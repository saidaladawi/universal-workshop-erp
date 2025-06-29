"""
Delivery Status Tracking and Monitoring System for Twilio WhatsApp/SMS
2025 Oman/UAE compliant implementation with 98% success rate monitoring
"""

import json
import time
import hashlib
import hmac
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, get_datetime
import logging

logger = logging.getLogger(__name__)


class DeliveryStatusTracker:
    """Main delivery status tracking and monitoring system"""

    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.webhook_secret = frappe.conf.get("twilio_webhook_secret")

    def _get_redis_client(self):
        """Get Redis client with proper configuration"""
        try:
            return redis.Redis(
                host=frappe.conf.get("redis_host", "localhost"),
                port=frappe.conf.get("redis_port", 6379),
                db=frappe.conf.get("redis_db", 1),
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        except Exception as e:
            frappe.log_error(f"Redis connection failed: {e}", "DeliveryTracking")
            return None


class WebhookHandler:
    """Secure Twilio webhook processing with signature validation"""

    def __init__(self):
        self.tracker = DeliveryStatusTracker()
        self.webhook_secret = frappe.conf.get("twilio_webhook_secret")

    def validate_webhook_signature(self, payload: str, signature: str, url: str) -> bool:
        """Validate Twilio webhook signature for security"""
        if not self.webhook_secret:
            frappe.log_error("Twilio webhook secret not configured", "WebhookSecurity")
            return False

        try:
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"), f"{url}{payload}".encode("utf-8"), hashlib.sha1
            ).digest()

            # Convert to base64
            import base64

            expected_b64 = base64.b64encode(expected_signature).decode()

            # Remove 'sha1=' prefix from Twilio signature
            provided_signature = (
                signature.replace("sha1=", "") if signature.startswith("sha1=") else signature
            )

            return hmac.compare_digest(expected_b64, provided_signature)

        except Exception as e:
            frappe.log_error(f"Webhook signature validation failed: {e}", "WebhookSecurity")
            return False

    def process_delivery_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Twilio delivery status webhook with idempotent handling"""
        try:
            message_sid = payload.get("MessageSid")
            if not message_sid:
                raise ValueError("MessageSid required in webhook payload")

            status = payload.get("MessageStatus", "unknown")
            error_code = payload.get("ErrorCode")
            error_message = payload.get("ErrorMessage")
            timestamp = now_datetime()

            # Store in Redis for real-time metrics
            self._update_redis_metrics(message_sid, status, payload)

            # Update database record
            self._update_database_status(message_sid, status, error_code, error_message, timestamp)

            # Check for alerting conditions
            self._check_alert_conditions(status, error_code)

            # Update Communication History record
            self._update_communication_history(message_sid, status, payload)

            return {
                "status": "success",
                "message_sid": message_sid,
                "processed_status": status,
                "timestamp": timestamp,
            }

        except Exception as e:
            frappe.log_error(f"Webhook processing error: {e}", "DeliveryTracking")
            raise

    def _update_redis_metrics(self, message_sid: str, status: str, payload: Dict[str, Any]):
        """Update Redis metrics for real-time monitoring"""
        if not self.tracker.redis_client:
            return

        try:
            redis_key = f"delivery:message:{message_sid}"
            current_time = int(time.time())

            # Store complete payload with timestamp
            self.tracker.redis_client.hset(
                redis_key,
                mapping={
                    "status": status,
                    "updated_at": current_time,
                    "payload": json.dumps(payload),
                },
            )

            # Set expiration (30 days)
            self.tracker.redis_client.expire(redis_key, 2592000)

            # Update hourly counters
            hour_key = f"metrics:hourly:{datetime.now().strftime('%Y%m%d%H')}"
            self.tracker.redis_client.hincrby(hour_key, f"total_{status}", 1)
            self.tracker.redis_client.expire(hour_key, 86400 * 7)  # 7 days

            # Update daily counters
            day_key = f"metrics:daily:{datetime.now().strftime('%Y%m%d')}"
            self.tracker.redis_client.hincrby(day_key, f"total_{status}", 1)
            self.tracker.redis_client.expire(day_key, 86400 * 30)  # 30 days

            # Update rolling window metrics (last 1 hour)
            rolling_key = "metrics:rolling:1h"
            self.tracker.redis_client.lpush(f"{rolling_key}:{status}", current_time)
            self.tracker.redis_client.ltrim(
                f"{rolling_key}:{status}", 0, 10000
            )  # Keep last 10k entries

        except Exception as e:
            frappe.log_error(f"Redis metrics update failed: {e}", "DeliveryTracking")

    def _update_database_status(
        self,
        message_sid: str,
        status: str,
        error_code: Optional[str],
        error_message: Optional[str],
        timestamp: datetime,
    ):
        """Update database with delivery status (idempotent)"""
        try:
            # Check if status update already processed
            existing = frappe.db.get_value(
                "Delivery Status Log", {"message_sid": message_sid, "status": status}, "name"
            )

            if existing:
                # Already processed - idempotent behavior
                return existing

            # Create new status log entry
            status_log = frappe.new_doc("Delivery Status Log")
            status_log.message_sid = message_sid
            status_log.status = status
            status_log.error_code = error_code or ""
            status_log.error_message = error_message or ""
            status_log.received_at = timestamp
            status_log.processed_at = now_datetime()
            status_log.insert(ignore_permissions=True)

            return status_log.name

        except Exception as e:
            frappe.log_error(f"Database status update failed: {e}", "DeliveryTracking")

    def _update_communication_history(self, message_sid: str, status: str, payload: Dict[str, Any]):
        """Update Communication History record with delivery status"""
        try:
            # Find communication history record by external_id (message_sid)
            history = frappe.db.get_value(
                "Communication History", {"external_id": message_sid}, ["name", "delivery_status"]
            )

            if history:
                doc = frappe.get_doc("Communication History", history[0])

                # Update delivery status based on Twilio status mapping
                status_mapping = {
                    "queued": "Queued",
                    "sent": "Sent",
                    "delivered": "Delivered",
                    "read": "Read",
                    "failed": "Failed",
                    "undelivered": "Failed",
                }

                new_status = status_mapping.get(status, "Unknown")

                # Only update if status has changed
                if doc.delivery_status != new_status:
                    doc.delivery_status = new_status
                    doc.delivery_timestamp = now_datetime()

                    # Update cost if available
                    if "Price" in payload:
                        doc.cost_omr = flt(payload["Price"], 3)

                    # Add delivery timeline entry
                    if hasattr(doc, "delivery_timeline"):
                        timeline_entry = {
                            "timestamp": now_datetime(),
                            "status": new_status,
                            "details": f"Twilio status: {status}",
                        }

                        existing_timeline = json.loads(doc.delivery_timeline or "[]")
                        existing_timeline.append(timeline_entry)
                        doc.delivery_timeline = json.dumps(existing_timeline)

                    doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Communication history update failed: {e}", "DeliveryTracking")

    def _check_alert_conditions(self, status: str, error_code: Optional[str]):
        """Check if alert conditions are met and trigger notifications"""
        try:
            # Get current delivery success rate
            success_rate = self._calculate_success_rate()

            # Check SLA threshold (98%)
            if success_rate < 98.0:
                self._trigger_sla_alert(success_rate)

            # Check for specific error patterns
            if error_code:
                self._check_error_pattern_alerts(error_code)

        except Exception as e:
            frappe.log_error(f"Alert checking failed: {e}", "DeliveryTracking")

    def _calculate_success_rate(self, window_hours: int = 1) -> float:
        """Calculate delivery success rate for specified time window"""
        if not self.tracker.redis_client:
            return 100.0  # Default to 100% if Redis unavailable

        try:
            current_time = int(time.time())
            window_start = current_time - (window_hours * 3600)

            # Get counts from Redis rolling metrics
            delivered_count = 0
            failed_count = 0

            # Count delivered messages in time window
            delivered_times = self.tracker.redis_client.lrange(
                "metrics:rolling:1h:delivered", 0, -1
            )
            delivered_count = sum(1 for t in delivered_times if int(t) >= window_start)

            # Count failed messages in time window
            failed_times = self.tracker.redis_client.lrange("metrics:rolling:1h:failed", 0, -1)
            failed_count = sum(1 for t in failed_times if int(t) >= window_start)

            undelivered_times = self.tracker.redis_client.lrange(
                "metrics:rolling:1h:undelivered", 0, -1
            )
            failed_count += sum(1 for t in undelivered_times if int(t) >= window_start)

            total_count = delivered_count + failed_count

            if total_count == 0:
                return 100.0

            success_rate = (delivered_count / total_count) * 100
            return round(success_rate, 2)

        except Exception as e:
            frappe.log_error(f"Success rate calculation failed: {e}", "DeliveryTracking")
            return 100.0

    def _trigger_sla_alert(self, current_rate: float):
        """Trigger SLA breach alert"""
        try:
            alert_doc = frappe.new_doc("Delivery Alert")
            alert_doc.alert_type = "SLA Breach"
            alert_doc.severity = "High"
            alert_doc.description = (
                f"Delivery success rate dropped to {current_rate}% (below 98% SLA)"
            )
            alert_doc.current_success_rate = current_rate
            alert_doc.threshold = 98.0
            alert_doc.triggered_at = now_datetime()
            alert_doc.insert(ignore_permissions=True)

            # Send notification to administrators
            self._send_alert_notification(alert_doc)

        except Exception as e:
            frappe.log_error(f"SLA alert trigger failed: {e}", "DeliveryTracking")

    def _check_error_pattern_alerts(self, error_code: str):
        """Check for error patterns that require immediate attention"""
        critical_errors = ["30008", "30004", "30006"]  # Twilio critical error codes

        if error_code in critical_errors:
            try:
                alert_doc = frappe.new_doc("Delivery Alert")
                alert_doc.alert_type = "Critical Error"
                alert_doc.severity = "Critical"
                alert_doc.description = f"Critical Twilio error code {error_code} detected"
                alert_doc.error_code = error_code
                alert_doc.triggered_at = now_datetime()
                alert_doc.insert(ignore_permissions=True)

                self._send_alert_notification(alert_doc)

            except Exception as e:
                frappe.log_error(f"Error pattern alert failed: {e}", "DeliveryTracking")

    def _send_alert_notification(self, alert_doc):
        """Send alert notification to system administrators"""
        try:
            # Get admin users
            admins = frappe.get_all(
                "User",
                filters={"role_profile_name": "System Manager", "enabled": 1},
                fields=["email", "full_name"],
            )

            for admin in admins:
                frappe.sendmail(
                    recipients=[admin.email],
                    subject=f"[ALERT] {alert_doc.alert_type}: {alert_doc.severity}",
                    message=f"""
                    <h3>Delivery Monitoring Alert</h3>
                    <p><strong>Type:</strong> {alert_doc.alert_type}</p>
                    <p><strong>Severity:</strong> {alert_doc.severity}</p>
                    <p><strong>Description:</strong> {alert_doc.description}</p>
                    <p><strong>Time:</strong> {alert_doc.triggered_at}</p>
                    <p>Please check the delivery monitoring dashboard for more details.</p>
                    """,
                )

        except Exception as e:
            frappe.log_error(f"Alert notification failed: {e}", "DeliveryTracking")

    def _get_success_rate_trend(self):
        """Get success rate trend for dashboard"""
        try:
            # Get hourly success rates for last 24 hours
            trend_data = []
            current_time = frappe.utils.now_datetime()

            for i in range(24):
                hour_start = current_time - timedelta(hours=i + 1)
                hour_end = current_time - timedelta(hours=i)

                # Get metrics for this hour from Redis
                hour_key = f"delivery_metrics:hour:{hour_start.strftime('%Y%m%d%H')}"
                hour_data = self.tracker.redis_client.hgetall(hour_key)

                if hour_data:
                    total = int(hour_data.get("total_sent", 0))
                    delivered = int(hour_data.get("delivered", 0))
                    success_rate = (delivered / total * 100) if total > 0 else 0
                else:
                    success_rate = 0

                trend_data.append(
                    {"hour": hour_start.strftime("%H:00"), "success_rate": round(success_rate, 2)}
                )

            return list(reversed(trend_data))  # Chronological order

        except Exception as e:
            frappe.log_error(f"Error getting success rate trend: {str(e)}")
            return []


class DeliveryMetricsCollector:
    """Collect and aggregate delivery metrics for dashboard reporting"""

    def __init__(self):
        self.tracker = DeliveryStatusTracker()

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time delivery metrics from Redis"""
        if not self.tracker.redis_client:
            return self._get_fallback_metrics()

        try:
            current_hour = datetime.now().strftime("%Y%m%d%H")
            hour_key = f"metrics:hourly:{current_hour}"

            metrics = self.tracker.redis_client.hgetall(hour_key)

            total_delivered = int(metrics.get("total_delivered", 0))
            total_failed = int(metrics.get("total_failed", 0)) + int(
                metrics.get("total_undelivered", 0)
            )
            total_sent = int(metrics.get("total_sent", 0))
            total_queued = int(metrics.get("total_queued", 0))

            total_messages = total_delivered + total_failed + total_sent + total_queued
            success_rate = (total_delivered / total_messages * 100) if total_messages > 0 else 100.0

            return {
                "total_messages": total_messages,
                "delivered": total_delivered,
                "failed": total_failed,
                "sent": total_sent,
                "queued": total_queued,
                "success_rate": round(success_rate, 2),
                "last_updated": now_datetime(),
                "sla_compliance": success_rate >= 98.0,
            }

        except Exception as e:
            frappe.log_error(f"Real-time metrics collection failed: {e}", "DeliveryTracking")
            return self._get_fallback_metrics()

    def get_historical_metrics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get historical delivery metrics for trend analysis"""
        try:
            metrics = []

            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                day_key = f"metrics:daily:{date}"

                if self.tracker.redis_client:
                    day_metrics = self.tracker.redis_client.hgetall(day_key)
                else:
                    day_metrics = {}

                delivered = int(day_metrics.get("total_delivered", 0))
                failed = int(day_metrics.get("total_failed", 0)) + int(
                    day_metrics.get("total_undelivered", 0)
                )
                total = delivered + failed

                success_rate = (delivered / total * 100) if total > 0 else 100.0

                metrics.append(
                    {
                        "date": date,
                        "total_messages": total,
                        "delivered": delivered,
                        "failed": failed,
                        "success_rate": round(success_rate, 2),
                    }
                )

            return sorted(metrics, key=lambda x: x["date"])

        except Exception as e:
            frappe.log_error(f"Historical metrics collection failed: {e}", "DeliveryTracking")
            return []

    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Fallback metrics when Redis is unavailable"""
        return {
            "total_messages": 0,
            "delivered": 0,
            "failed": 0,
            "sent": 0,
            "queued": 0,
            "success_rate": 100.0,
            "last_updated": now_datetime(),
            "sla_compliance": True,
            "fallback_mode": True,
        }


# WhiteListed API methods for external access
@frappe.whitelist(allow_guest=True)
def handle_twilio_webhook():
    """Handle incoming Twilio delivery status webhook"""
    try:
        # Get webhook payload
        payload = frappe.local.form_dict
        signature = frappe.get_request_header("X-Twilio-Signature", "")

        # Validate webhook signature
        handler = WebhookHandler()

        # For development, skip signature validation if secret not configured
        if handler.webhook_secret:
            url = frappe.request.url
            raw_payload = frappe.request.get_data(as_text=True)

            if not handler.validate_webhook_signature(raw_payload, signature, url):
                frappe.throw(_("Invalid webhook signature"), frappe.AuthenticationError)

        # Process webhook
        result = handler.process_delivery_webhook(payload)

        return {"status": "success", "message": "Webhook processed successfully", "data": result}

    except Exception as e:
        frappe.log_error(f"Webhook handling error: {e}", "DeliveryTracking")
        frappe.local.response.http_status_code = 500
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_delivery_metrics():
    """Get current delivery metrics for dashboard"""
    try:
        tracker = DeliveryStatusTracker()
        if not tracker.redis_client:
            return {
                "total_messages": 0,
                "delivered": 0,
                "failed": 0,
                "success_rate": 100.0,
                "fallback_mode": True,
            }

        current_hour = datetime.now().strftime("%Y%m%d%H")
        hour_key = f"metrics:hourly:{current_hour}"

        metrics = tracker.redis_client.hgetall(hour_key)

        total_delivered = int(metrics.get("total_delivered", 0))
        total_failed = int(metrics.get("total_failed", 0)) + int(
            metrics.get("total_undelivered", 0)
        )
        total_messages = total_delivered + total_failed
        success_rate = (total_delivered / total_messages * 100) if total_messages > 0 else 100.0

        return {
            "total_messages": total_messages,
            "delivered": total_delivered,
            "failed": total_failed,
            "success_rate": round(success_rate, 2),
            "sla_compliance": success_rate >= 98.0,
        }

    except Exception as e:
        frappe.log_error(f"Delivery metrics error: {e}", "DeliveryTracking")
        return {"error": str(e)}


@frappe.whitelist()
def get_delivery_trends(days=7):
    """Get delivery trend data for specified number of days"""
    collector = DeliveryMetricsCollector()
    return collector.get_historical_metrics(cint(days))


@frappe.whitelist()
def get_delivery_success_rate():
    """Get current delivery success rate"""
    handler = WebhookHandler()
    return {
        "success_rate": handler._calculate_success_rate(),
        "sla_compliance": handler._calculate_success_rate() >= 98.0,
        "timestamp": now_datetime(),
    }


@frappe.whitelist()
def trigger_test_alert():
    """Trigger test alert for testing alerting system"""
    try:
        handler = WebhookHandler()
        handler._trigger_sla_alert(95.5)  # Test with low success rate

        return {"status": "success", "message": "Test alert triggered successfully"}

    except Exception as e:
        frappe.log_error(f"Test alert failed: {e}", "DeliveryTracking")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cleanup_old_metrics(days_to_keep=30):
    """Cleanup old metrics data from Redis"""
    try:
        tracker = DeliveryStatusTracker()
        if not tracker.redis_client:
            return {"status": "error", "message": "Redis not available"}

        # Get all metric keys older than retention period
        cutoff_date = (datetime.now() - timedelta(days=cint(days_to_keep))).strftime("%Y%m%d")

        # Delete old daily metrics
        for key in tracker.redis_client.scan_iter(match="metrics:daily:*"):
            date_part = key.split(":")[-1]
            if date_part < cutoff_date:
                tracker.redis_client.delete(key)

        # Delete old hourly metrics (keep only last 7 days)
        cutoff_hour = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d%H")
        for key in tracker.redis_client.scan_iter(match="metrics:hourly:*"):
            hour_part = key.split(":")[-1]
            if hour_part < cutoff_hour:
                tracker.redis_client.delete(key)

        return {
            "status": "success",
            "message": f"Cleaned up metrics older than {days_to_keep} days",
        }

    except Exception as e:
        frappe.log_error(f"Metrics cleanup failed: {e}", "DeliveryTracking")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def twilio_webhook_handler():
    """
    Handle Twilio delivery status webhooks
    Public endpoint that Twilio calls with delivery updates
    """
    try:
        # Get request data
        payload = frappe.request.get_data(as_text=True)
        signature = frappe.request.headers.get("X-Twilio-Signature", "")

        # Initialize webhook handler
        webhook = WebhookHandler()

        # Process the webhook
        result = webhook.process_twilio_webhook(payload, signature)

        # Return success response (Twilio expects 200 OK)
        return {"status": "success", "message": "Webhook processed"}

    except Exception as e:
        frappe.log_error(f"Webhook processing failed: {str(e)}", "Twilio Webhook Error")
        # Still return 200 to prevent Twilio retries for invalid webhooks
        return {"status": "error", "message": "Processing failed"}


@frappe.whitelist()
def get_delivery_dashboard_data():
    """
    Get delivery dashboard data for monitoring
    """
    tracker = DeliveryStatusTracker()

    # Get basic metrics from Redis
    metrics = tracker.get_delivery_metrics()

    # Get recent alerts
    recent_alerts = frappe.get_list(
        "Delivery Alert",
        filters={"status": ["in", ["Open", "In Progress"]]},
        fields=["name", "alert_type", "severity", "title", "creation"],
        order_by="creation desc",
        limit=10,
    )

    # Get success rate trend (last 24 hours)
    success_rate_trend = tracker._get_success_rate_trend()

    return {
        "metrics": metrics,
        "recent_alerts": recent_alerts,
        "success_rate_trend": success_rate_trend,
    }


@frappe.whitelist()
def retry_failed_messages(status_log_ids=None):
    """
    Retry failed message deliveries

    Args:
        status_log_ids (list): Specific delivery status log IDs to retry
    """
    tracker = DeliveryStatusTracker()

    if status_log_ids:
        # Retry specific messages
        if isinstance(status_log_ids, str):
            status_log_ids = [status_log_ids]

        results = []
        for log_id in status_log_ids:
            try:
                result = tracker.retry_failed_delivery(log_id)
                results.append({"log_id": log_id, "status": "queued", "result": result})
            except Exception as e:
                results.append({"log_id": log_id, "status": "error", "error": str(e)})

        return {"results": results}
    else:
        # Retry all failed messages from last 24 hours
        failed_logs = frappe.get_list(
            "Delivery Status Log",
            filters={
                "status": "failed",
                "creation": [">", frappe.utils.add_days(frappe.utils.now(), -1)],
            },
            fields=["name"],
        )

        retry_count = 0
        for log in failed_logs:
            try:
                tracker.retry_failed_delivery(log.name)
                retry_count += 1
            except Exception as e:
                frappe.log_error(f"Failed to retry message {log.name}: {str(e)}")

        return {"retried_count": retry_count, "total_failed": len(failed_logs)}


# Add scheduler functions at the end of the file


def check_delivery_alerts():
    """
    Scheduler function: Check and trigger delivery alerts
    Called every 5 minutes via hooks.py
    """
    try:
        tracker = DeliveryStatusTracker()

        # Check for delivery SLA breaches
        current_time = frappe.utils.now_datetime()
        sla_threshold = current_time - timedelta(minutes=30)  # 30 min SLA

        # Find pending deliveries beyond SLA
        overdue_logs = frappe.get_list(
            "Delivery Status Log",
            filters={"status": ["in", ["sent", "queued"]], "creation": ["<", sla_threshold]},
            fields=["name", "message_sid", "channel", "customer"],
        )

        for log in overdue_logs:
            try:
                tracker._create_alert(
                    alert_type="sla_breach",
                    severity="Medium",
                    title=f"Delivery SLA Breach - {log.message_sid}",
                    description=f"{log.channel} message pending delivery for >30 minutes",
                    related_record=log.name,
                )
            except Exception as e:
                frappe.log_error(f"Failed to create SLA alert for {log.name}: {str(e)}")

        # Check overall success rate
        metrics = tracker.get_delivery_metrics()
        success_rate = metrics.get("success_rate", 100)

        if success_rate < 98:  # Below 98% threshold
            tracker._create_alert(
                alert_type="low_success_rate",
                severity="High" if success_rate < 95 else "Medium",
                title=f"Low Delivery Success Rate: {success_rate:.1f}%",
                description=f"Current delivery success rate ({success_rate:.1f}%) is below acceptable threshold (98%)",
                related_record=None,
            )

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Delivery alert check failed: {str(e)}", "DeliveryTracking")


def update_delivery_metrics():
    """
    Scheduler function: Update delivery metrics in Redis
    Called every 5 minutes via hooks.py
    """
    try:
        collector = DeliveryMetricsCollector()
        result = collector.update_redis_metrics()

        if result.get("status") == "error":
            frappe.log_error(f"Metrics update failed: {result.get('message')}", "DeliveryTracking")

    except Exception as e:
        frappe.log_error(f"Metrics update scheduler failed: {str(e)}", "DeliveryTracking")


def scheduled_cleanup_old_metrics():
    """
    Scheduler function: Cleanup old Redis metrics
    Called hourly via hooks.py
    """
    try:
        collector = DeliveryMetricsCollector()
        result = collector.cleanup_old_metrics(days_to_keep=7)

        if result.get("status") == "success":
            frappe.logger().info(
                f"Cleaned up old metrics: {result.get('cleaned_keys', 0)} keys removed"
            )
        else:
            frappe.log_error(f"Metrics cleanup failed: {result.get('message')}", "DeliveryTracking")

    except Exception as e:
        frappe.log_error(f"Metrics cleanup scheduler failed: {str(e)}", "DeliveryTracking")


def generate_delivery_reports():
    """
    Scheduler function: Generate daily delivery reports
    Called daily via hooks.py
    """
    try:
        tracker = DeliveryStatusTracker()
        yesterday = frappe.utils.add_days(frappe.utils.today(), -1)

        # Get yesterday's delivery statistics
        stats = frappe.db.sql(
            """
            SELECT 
                channel,
                status,
                COUNT(*) as count,
                AVG(CASE 
                    WHEN status = 'delivered' AND delivered_at IS NOT NULL 
                    THEN TIMESTAMPDIFF(SECOND, creation, delivered_at) 
                    ELSE NULL 
                END) as avg_delivery_time_seconds
            FROM `tabDelivery Status Log`
            WHERE DATE(creation) = %s
            GROUP BY channel, status
            ORDER BY channel, status
        """,
            [yesterday],
            as_dict=True,
        )

        # Calculate totals and success rates
        report_data = {
            "date": yesterday,
            "total_sent": 0,
            "total_delivered": 0,
            "channels": {},
            "overall_success_rate": 0,
            "avg_delivery_time_minutes": 0,
        }

        total_delivery_time = 0
        delivered_count = 0

        for stat in stats:
            channel = stat.channel
            if channel not in report_data["channels"]:
                report_data["channels"][channel] = {
                    "sent": 0,
                    "delivered": 0,
                    "failed": 0,
                    "success_rate": 0,
                    "avg_delivery_time_minutes": 0,
                }

            count = stat.count
            status = stat.status

            if status in ["sent", "delivered"]:
                report_data["total_sent"] += count
                report_data["channels"][channel]["sent"] += count

            if status == "delivered":
                report_data["total_delivered"] += count
                report_data["channels"][channel]["delivered"] += count

                # Track delivery time
                if stat.avg_delivery_time_seconds:
                    total_delivery_time += stat.avg_delivery_time_seconds * count
                    delivered_count += count

            elif status == "failed":
                report_data["channels"][channel]["failed"] += count

        # Calculate success rates and averages
        if report_data["total_sent"] > 0:
            report_data["overall_success_rate"] = round(
                (report_data["total_delivered"] / report_data["total_sent"]) * 100, 2
            )

        if delivered_count > 0:
            report_data["avg_delivery_time_minutes"] = round(
                (total_delivery_time / delivered_count) / 60, 2
            )

        # Calculate per-channel success rates
        for channel_data in report_data["channels"].values():
            if channel_data["sent"] > 0:
                channel_data["success_rate"] = round(
                    (channel_data["delivered"] / channel_data["sent"]) * 100, 2
                )

        # Create alert if success rate is low
        if report_data["overall_success_rate"] < 95:
            tracker._create_alert(
                alert_type="daily_report_low_success",
                severity="High",
                title=f'Daily Report: Low Success Rate ({report_data["overall_success_rate"]}%)',
                description=f'Yesterday\'s delivery success rate was {report_data["overall_success_rate"]}%, below 95% threshold',
                related_record=None,
            )

        # Log the report for monitoring
        frappe.logger().info(f"Daily delivery report generated: {report_data}")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Daily report generation failed: {str(e)}", "DeliveryTracking")
