# -*- coding: utf-8 -*-
"""
Redis Queue Manager for Universal Workshop Communication System
Implements RQ (Redis Queue) with retry mechanisms and dead letter queue
"""

import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import redis
import frappe
from frappe import _
from frappe.utils import get_site_name, now_datetime


class QueueType(Enum):
    """Queue types for different communication channels"""

    SMS = "sms_queue"
    WHATSAPP = "whatsapp_queue"
    EMAIL = "email_queue"
    BULK = "bulk_queue"


class Priority(Enum):
    """Message priority levels"""

    HIGH = 1  # Immediate processing
    MEDIUM = 2  # 5 minutes delay
    LOW = 3  # 15 minutes delay


class MessageStatus(Enum):
    """Message processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class RedisQueueManager:
    """
    Redis-based queue manager for Universal Workshop communication system.

    Features:
    - Multiple queue types (SMS, WhatsApp, Email, Bulk)
    - Priority-based processing
    - Retry mechanisms with exponential backoff
    - Dead letter queue for failed messages
    - Rate limiting for Oman compliance
    - Queue monitoring and statistics
    """

    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.site_name = get_site_name()
        self.max_retries = 3
        self.rate_limit_per_hour = 100  # Oman compliance

    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client connection"""
        try:
            redis_config = frappe.get_site_config().get("redis_queue") or {}
            return redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 2),
                decode_responses=True,
            )
        except Exception as e:
            frappe.log_error(f"Redis connection failed: {e}", "RedisQueueManager")
            raise

    def enqueue_message(
        self,
        queue_type: QueueType,
        message_data: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        delay_seconds: int = 0,
    ) -> str:
        """
        Enqueue a message for processing.

        Args:
            queue_type: Type of queue (SMS, WhatsApp, Email, Bulk)
            message_data: Message content and metadata
            priority: Message priority level
            delay_seconds: Delay before processing

        Returns:
            str: Message ID for tracking
        """
        try:
            # Generate unique message ID
            message_id = (
                f"{queue_type.value}_{int(time.time() * 1000)}_{frappe.generate_hash(length=8)}"
            )

            # Prepare message envelope
            message_envelope = {
                "id": message_id,
                "queue_type": queue_type.value,
                "priority": priority.value,
                "data": message_data,
                "created_at": now_datetime().isoformat(),
                "retry_count": 0,
                "status": MessageStatus.PENDING.value,
                "site_name": self.site_name,
            }

            # Calculate processing time based on priority
            process_at = datetime.now() + timedelta(seconds=delay_seconds)
            if priority == Priority.MEDIUM:
                process_at += timedelta(minutes=5)
            elif priority == Priority.LOW:
                process_at += timedelta(minutes=15)

            # Store message data
            self.redis_client.hset(
                f"messages:{self.site_name}", message_id, json.dumps(message_envelope)
            )

            # Add to priority queue
            score = process_at.timestamp()
            self.redis_client.zadd(
                f"queue:{queue_type.value}:{self.site_name}", {message_id: score}
            )

            # Update statistics
            self._update_queue_stats(queue_type, "enqueued")

            frappe.logger().info(f"Message {message_id} enqueued to {queue_type.value}")
            return message_id

        except Exception as e:
            frappe.log_error(f"Failed to enqueue message: {e}", "RedisQueueManager")
            raise

    def dequeue_message(self, queue_type: QueueType) -> Optional[Dict[str, Any]]:
        """
        Dequeue next available message for processing.

        Args:
            queue_type: Queue to process

        Returns:
            Dict containing message data or None if no messages available
        """
        try:
            current_time = time.time()
            queue_key = f"queue:{queue_type.value}:{self.site_name}"

            # Get next message that's ready for processing
            result = self.redis_client.zrangebyscore(
                queue_key, 0, current_time, start=0, num=1, withscores=True
            )

            if not result:
                return None

            message_id, score = result[0]

            # Remove from queue
            self.redis_client.zrem(queue_key, message_id)

            # Get message data
            message_data = self.redis_client.hget(f"messages:{self.site_name}", message_id)
            if not message_data:
                return None

            message_envelope = json.loads(message_data)
            message_envelope["status"] = MessageStatus.PROCESSING.value

            # Update message status
            self.redis_client.hset(
                f"messages:{self.site_name}", message_id, json.dumps(message_envelope)
            )

            # Update statistics
            self._update_queue_stats(queue_type, "dequeued")

            return message_envelope

        except Exception as e:
            frappe.log_error(f"Failed to dequeue message: {e}", "RedisQueueManager")
            return None

    def mark_message_completed(self, message_id: str) -> bool:
        """Mark message as successfully processed"""
        try:
            message_data = self.redis_client.hget(f"messages:{self.site_name}", message_id)
            if not message_data:
                return False

            message_envelope = json.loads(message_data)
            message_envelope["status"] = MessageStatus.COMPLETED.value
            message_envelope["completed_at"] = now_datetime().isoformat()

            # Update message
            self.redis_client.hset(
                f"messages:{self.site_name}", message_id, json.dumps(message_envelope)
            )

            # Update statistics
            queue_type = QueueType(message_envelope["queue_type"])
            self._update_queue_stats(queue_type, "completed")

            # Clean up completed messages after 24 hours
            self.redis_client.expire(f"messages:{self.site_name}", 86400)

            return True

        except Exception as e:
            frappe.log_error(f"Failed to mark message completed: {e}", "RedisQueueManager")
            return False

    def mark_message_failed(self, message_id: str, error: str) -> bool:
        """
        Mark message as failed and handle retry logic.

        Args:
            message_id: ID of the failed message
            error: Error description

        Returns:
            bool: True if message was processed, False if moved to dead letter queue
        """
        try:
            message_data = self.redis_client.hget(f"messages:{self.site_name}", message_id)
            if not message_data:
                return False

            message_envelope = json.loads(message_data)
            message_envelope["retry_count"] += 1
            message_envelope["last_error"] = error
            message_envelope["last_retry_at"] = now_datetime().isoformat()

            queue_type = QueueType(message_envelope["queue_type"])

            if message_envelope["retry_count"] >= self.max_retries:
                # Move to dead letter queue
                message_envelope["status"] = MessageStatus.DEAD_LETTER.value
                self.redis_client.lpush(
                    f"dead_letter:{self.site_name}", json.dumps(message_envelope)
                )
                self._update_queue_stats(queue_type, "dead_letter")
                return False
            else:
                # Retry with exponential backoff
                message_envelope["status"] = MessageStatus.PENDING.value
                backoff_seconds = (2 ** message_envelope["retry_count"]) * 60  # 2, 4, 8 minutes

                retry_at = datetime.now() + timedelta(seconds=backoff_seconds)
                score = retry_at.timestamp()

                # Re-enqueue with delay
                self.redis_client.zadd(
                    f"queue:{queue_type.value}:{self.site_name}", {message_id: score}
                )

                self._update_queue_stats(queue_type, "retried")

            # Update message
            self.redis_client.hset(
                f"messages:{self.site_name}", message_id, json.dumps(message_envelope)
            )

            return True

        except Exception as e:
            frappe.log_error(f"Failed to handle message failure: {e}", "RedisQueueManager")
            return False

    def check_rate_limit(self, customer_phone: str, queue_type: QueueType) -> bool:
        """
        Check if customer has exceeded rate limits (Oman compliance).

        Args:
            customer_phone: Customer phone number
            queue_type: Type of communication

        Returns:
            bool: True if within limits, False if exceeded
        """
        try:
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            rate_key = f"rate_limit:{queue_type.value}:{customer_phone}:{current_hour.isoformat()}"

            current_count = self.redis_client.get(rate_key) or 0
            current_count = int(current_count)

            if current_count >= self.rate_limit_per_hour:
                frappe.logger().warning(
                    f"Rate limit exceeded for {customer_phone} in {queue_type.value}: {current_count}"
                )
                return False

            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, 3600)  # Expire after 1 hour
            pipe.execute()

            return True

        except Exception as e:
            frappe.log_error(f"Rate limit check failed: {e}", "RedisQueueManager")
            return True  # Allow on error to avoid blocking legitimate messages

    def get_queue_stats(self, queue_type: Optional[QueueType] = None) -> Dict[str, Any]:
        """Get queue statistics for monitoring"""
        try:
            stats = {}

            if queue_type:
                queue_types = [queue_type]
            else:
                queue_types = list(QueueType)

            for qt in queue_types:
                queue_key = f"queue:{qt.value}:{self.site_name}"
                stats_key = f"stats:{qt.value}:{self.site_name}"

                # Current queue length
                queue_length = self.redis_client.zcard(queue_key)

                # Get statistics
                stats_data = self.redis_client.hgetall(stats_key)

                stats[qt.value] = {
                    "queue_length": queue_length,
                    "enqueued": int(stats_data.get("enqueued", 0)),
                    "dequeued": int(stats_data.get("dequeued", 0)),
                    "completed": int(stats_data.get("completed", 0)),
                    "retried": int(stats_data.get("retried", 0)),
                    "dead_letter": int(stats_data.get("dead_letter", 0)),
                }

            # Dead letter queue length
            dead_letter_length = self.redis_client.llen(f"dead_letter:{self.site_name}")
            stats["dead_letter_length"] = dead_letter_length

            return stats

        except Exception as e:
            frappe.log_error(f"Failed to get queue stats: {e}", "RedisQueueManager")
            return {}

    def get_dead_letter_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue for manual review"""
        try:
            dead_messages = self.redis_client.lrange(f"dead_letter:{self.site_name}", 0, limit - 1)
            return [json.loads(msg) for msg in dead_messages]
        except Exception as e:
            frappe.log_error(f"Failed to get dead letter messages: {e}", "RedisQueueManager")
            return []

    def requeue_dead_letter_message(self, index: int) -> bool:
        """Requeue a message from dead letter queue"""
        try:
            # Get message from dead letter queue
            message_data = self.redis_client.lindex(f"dead_letter:{self.site_name}", index)
            if not message_data:
                return False

            message_envelope = json.loads(message_data)

            # Reset retry count and status
            message_envelope["retry_count"] = 0
            message_envelope["status"] = MessageStatus.PENDING.value
            message_envelope["requeued_at"] = now_datetime().isoformat()

            queue_type = QueueType(message_envelope["queue_type"])

            # Remove from dead letter queue
            self.redis_client.lrem(f"dead_letter:{self.site_name}", 1, message_data)

            # Re-enqueue
            score = time.time()  # Process immediately
            self.redis_client.zadd(
                f"queue:{queue_type.value}:{self.site_name}", {message_envelope["id"]: score}
            )

            # Update message
            self.redis_client.hset(
                f"messages:{self.site_name}", message_envelope["id"], json.dumps(message_envelope)
            )

            return True

        except Exception as e:
            frappe.log_error(f"Failed to requeue dead letter message: {e}", "RedisQueueManager")
            return False

    def _update_queue_stats(self, queue_type: QueueType, operation: str):
        """Update queue statistics"""
        try:
            stats_key = f"stats:{queue_type.value}:{self.site_name}"
            self.redis_client.hincrby(stats_key, operation, 1)
            self.redis_client.expire(stats_key, 86400 * 7)  # Keep stats for 7 days
        except Exception as e:
            frappe.log_error(f"Failed to update queue stats: {e}", "RedisQueueManager")

    def cleanup_old_messages(self, days_old: int = 7):
        """Clean up old completed messages"""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days_old)).timestamp()

            # Get all message IDs
            message_keys = self.redis_client.hkeys(f"messages:{self.site_name}")

            for message_id in message_keys:
                message_data = self.redis_client.hget(f"messages:{self.site_name}", message_id)
                if message_data:
                    message_envelope = json.loads(message_data)
                    created_at = datetime.fromisoformat(message_envelope["created_at"]).timestamp()

                    if created_at < cutoff_time and message_envelope["status"] in [
                        MessageStatus.COMPLETED.value,
                        MessageStatus.FAILED.value,
                    ]:
                        self.redis_client.hdel(f"messages:{self.site_name}", message_id)

            frappe.logger().info(f"Cleaned up old messages older than {days_old} days")

        except Exception as e:
            frappe.log_error(f"Failed to cleanup old messages: {e}", "RedisQueueManager")


# Singleton instance
_queue_manager = None


def get_queue_manager() -> RedisQueueManager:
    """Get singleton queue manager instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = RedisQueueManager()
    return _queue_manager
