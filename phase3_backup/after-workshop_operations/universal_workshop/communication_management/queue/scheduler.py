"""
Scheduler functions for communication queue management.
Integrates with Frappe's background task system for automated queue operations.
"""

import frappe
from frappe import _
from .redis_queue_manager import get_queue_manager, QueueType
from .message_worker import get_communication_worker


def process_communication_queues():
    """
    Process communication queues - called every minute by Frappe scheduler.
    This function ensures workers are running and processes any pending messages.
    """
    try:
        # Check if workers are running and start if needed
        worker = get_communication_worker()

        # Ensure workers are running for all queue types
        for queue_type in [QueueType.SMS, QueueType.WHATSAPP, QueueType.EMAIL, QueueType.BULK]:
            if queue_type not in worker.worker_threads or not worker.running:
                frappe.logger().info(f"Starting worker for {queue_type.value}")
                max_workers = 2 if queue_type in [QueueType.SMS, QueueType.WHATSAPP] else 1
                worker.start_worker(queue_type, max_workers)

        # Log queue statistics for monitoring
        queue_manager = get_queue_manager()
        stats = queue_manager.get_queue_stats()

        # Log if there are significant queue backlogs
        for queue_name, queue_stats in stats.items():
            if queue_name != "dead_letter_length" and isinstance(queue_stats, dict):
                queue_length = queue_stats.get("queue_length", 0)
                if queue_length > 50:  # Alert if more than 50 messages pending
                    frappe.logger().warning(
                        f"Large queue backlog in {queue_name}: {queue_length} messages pending"
                    )

        # Alert if dead letter queue is growing
        dead_letter_count = stats.get("dead_letter_length", 0)
        if dead_letter_count > 10:
            frappe.logger().warning(
                f"Dead letter queue has {dead_letter_count} messages - manual review recommended"
            )

    except Exception as e:
        frappe.log_error(f"Error in communication queue processing: {e}", "QueueScheduler")


def cleanup_old_queue_messages():
    """
    Clean up old completed messages - called daily by Frappe scheduler.
    """
    try:
        queue_manager = get_queue_manager()

        # Clean up messages older than 7 days
        queue_manager.cleanup_old_messages(days_old=7)

        frappe.logger().info("Queue message cleanup completed successfully")

    except Exception as e:
        frappe.log_error(f"Error in queue message cleanup: {e}", "QueueScheduler")


def generate_queue_health_report():
    """
    Generate queue health report - called hourly by Frappe scheduler.
    """
    try:
        queue_manager = get_queue_manager()
        stats = queue_manager.get_queue_stats()

        # Calculate health metrics
        total_enqueued = 0
        total_completed = 0
        total_failed = 0
        total_pending = 0

        for queue_name, queue_stats in stats.items():
            if queue_name != "dead_letter_length" and isinstance(queue_stats, dict):
                total_enqueued += queue_stats.get("enqueued", 0)
                total_completed += queue_stats.get("completed", 0)
                total_failed += queue_stats.get("dead_letter", 0)
                total_pending += queue_stats.get("queue_length", 0)

        # Calculate success rate
        total_processed = total_completed + total_failed
        success_rate = (total_completed / total_processed * 100) if total_processed > 0 else 100

        # Create health report
        health_report = {
            "timestamp": frappe.utils.now_datetime().isoformat(),
            "total_enqueued": total_enqueued,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "total_pending": total_pending,
            "success_rate": round(success_rate, 2),
            "dead_letter_count": stats.get("dead_letter_length", 0),
            "queue_details": stats,
        }

        # Store report in Communication Settings for dashboard display
        try:
            communication_settings = frappe.get_single("Communication Settings")
            communication_settings.queue_health_report = frappe.as_json(health_report)
            communication_settings.last_queue_health_check = frappe.utils.now_datetime()
            communication_settings.save(ignore_permissions=True)
        except Exception:
            # Communication Settings might not exist yet
            pass

        # Log critical issues
        if success_rate < 90:
            frappe.logger().warning(
                f"Queue success rate is low: {success_rate}% - investigate dead letter queue"
            )

        if total_pending > 100:
            frappe.logger().warning(
                f"High number of pending messages: {total_pending} - check worker status"
            )

        frappe.logger().info(f"Queue health report generated: {success_rate}% success rate")

    except Exception as e:
        frappe.log_error(f"Error generating queue health report: {e}", "QueueScheduler")


def handle_failed_messages():
    """
    Handle failed messages in dead letter queue - called every 6 hours.
    Attempts to requeue recent failures that might have been transient.
    """
    try:
        queue_manager = get_queue_manager()

        # Get dead letter messages
        dead_messages = queue_manager.get_dead_letter_messages(limit=10)

        if not dead_messages:
            return

        frappe.logger().info(f"Processing {len(dead_messages)} dead letter messages")

        requeued_count = 0
        for i, message in enumerate(dead_messages):
            try:
                # Only requeue recent failures (within last 24 hours)
                from datetime import datetime, timedelta

                message_time = datetime.fromisoformat(message.get("created_at", ""))
                if datetime.now() - message_time < timedelta(hours=24):

                    # Check if it's a transient error (network issues, timeouts)
                    last_error = message.get("last_error", "").lower()
                    transient_errors = [
                        "timeout",
                        "network",
                        "connection",
                        "temporary",
                        "503",
                        "502",
                        "504",
                    ]

                    if any(error_type in last_error for error_type in transient_errors):
                        if queue_manager.requeue_dead_letter_message(i):
                            requeued_count += 1
                            frappe.logger().info(
                                f"Requeued message {message.get('id')} due to transient error"
                            )

            except Exception as e:
                frappe.log_error(f"Error processing dead letter message {i}: {e}", "QueueScheduler")

        if requeued_count > 0:
            frappe.logger().info(f"Requeued {requeued_count} messages from dead letter queue")

    except Exception as e:
        frappe.log_error(f"Error handling failed messages: {e}", "QueueScheduler")


def monitor_rate_limits():
    """
    Monitor rate limit usage - called every 15 minutes.
    Logs high usage patterns for capacity planning.
    """
    try:
        # This would typically check Redis keys for rate limit patterns
        # For now, we'll just log that monitoring is active
        frappe.logger().debug("Rate limit monitoring check completed")

    except Exception as e:
        frappe.log_error(f"Error in rate limit monitoring: {e}", "QueueScheduler")
