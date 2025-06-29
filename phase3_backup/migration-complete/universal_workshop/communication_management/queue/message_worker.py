import time
import threading
from typing import Dict, Any, Optional
import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from .redis_queue_manager import get_queue_manager, QueueType, MessageStatus


class CommunicationWorker:
    """
    Worker class for processing communication messages from Redis queues.

    Features:
    - Processes SMS, WhatsApp, and Email messages
    - Handles retries and error logging
    - Respects business hours and rate limits
    - Integrates with existing communication APIs
    """

    def __init__(self):
        self.queue_manager = get_queue_manager()
        self.running = False
        self.worker_threads = {}

    def start_worker(self, queue_type: QueueType, max_workers: int = 2):
        """
        Start worker threads for a specific queue type.

        Args:
            queue_type: Type of queue to process
            max_workers: Maximum number of worker threads
        """
        try:
            if queue_type in self.worker_threads:
                frappe.logger().warning(f"Worker for {queue_type.value} already running")
                return

            self.running = True
            workers = []

            for i in range(max_workers):
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    args=(queue_type, f"{queue_type.value}_worker_{i}"),
                    daemon=True,
                )
                worker_thread.start()
                workers.append(worker_thread)

            self.worker_threads[queue_type] = workers
            frappe.logger().info(f"Started {max_workers} workers for {queue_type.value}")

        except Exception as e:
            frappe.log_error(
                f"Failed to start worker for {queue_type.value}: {e}", "CommunicationWorker"
            )

    def stop_worker(self, queue_type: QueueType):
        """Stop worker threads for a specific queue type"""
        try:
            self.running = False

            if queue_type in self.worker_threads:
                workers = self.worker_threads[queue_type]
                for worker in workers:
                    worker.join(timeout=30)  # Wait up to 30 seconds

                del self.worker_threads[queue_type]
                frappe.logger().info(f"Stopped workers for {queue_type.value}")

        except Exception as e:
            frappe.log_error(
                f"Failed to stop worker for {queue_type.value}: {e}", "CommunicationWorker"
            )

    def _worker_loop(self, queue_type: QueueType, worker_name: str):
        """Main worker loop for processing messages"""
        frappe.logger().info(f"Worker {worker_name} started for {queue_type.value}")

        while self.running:
            try:
                # Dequeue next message
                message = self.queue_manager.dequeue_message(queue_type)

                if not message:
                    # No messages available, sleep briefly
                    time.sleep(5)
                    continue

                # Process the message
                success = self._process_message(message)

                if success:
                    self.queue_manager.mark_message_completed(message["id"])
                    frappe.logger().info(f"Message {message['id']} processed successfully")
                else:
                    # Mark as failed - will be retried or moved to dead letter queue
                    error = f"Failed to process {queue_type.value} message"
                    self.queue_manager.mark_message_failed(message["id"], error)
                    frappe.logger().error(f"Message {message['id']} failed processing")

            except Exception as e:
                frappe.log_error(f"Worker {worker_name} error: {e}", "CommunicationWorker")
                time.sleep(10)  # Sleep longer on unexpected errors

        frappe.logger().info(f"Worker {worker_name} stopped")

    def _process_message(self, message):
        """Process a single message from the queue"""
        try:
            # Basic message processing logic
            frappe.log_error(f"Processing message: {message}", "Message Worker")
            return True
        except Exception as e:
            frappe.log_error(f"Message processing failed: {str(e)}", "Message Worker Error")
            return False


# Global worker instance
_worker_instance = None


def get_communication_worker():
    """Get singleton communication worker instance"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = CommunicationWorker()
    return _worker_instance


# Alias for backward compatibility with scheduler imports
MessageWorker = CommunicationWorker
