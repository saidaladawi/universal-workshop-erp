# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

"""
Delivery Status Log DocType for tracking individual message delivery events
Part of Universal Workshop ERP Communication Management System
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
import json
from typing import Dict, Any


class DeliveryStatusLog(Document):
    """Controller for Delivery Status Log DocType"""

    def validate(self):
        """Validate delivery status log data"""
        self.validate_message_sid()
        self.validate_status_transition()
        self.set_defaults()

    def validate_message_sid(self):
        """Validate message SID format"""
        if not self.message_sid:
            frappe.throw(_("Message SID is required"))

        # Twilio Message SID format validation (starts with SM for SMS, WA for WhatsApp)
        if not (
            self.message_sid.startswith("SM")
            or self.message_sid.startswith("WA")
            or self.message_sid.startswith("MM")
        ):
            frappe.throw(_("Invalid Message SID format. Must start with SM, WA, or MM"))

    def validate_status_transition(self):
        """Validate status transition logic"""
        valid_transitions = {
            "queued": ["sent", "failed"],
            "sent": ["delivered", "undelivered", "failed"],
            "delivered": ["read", "failed"],
            "read": [],  # Final status
            "failed": [],  # Final status
            "undelivered": ["delivered", "failed"],  # Can retry
            "unknown": ["queued", "sent", "delivered", "failed"],
        }

        # Get previous status for this message
        if not self.is_new():
            return  # Skip validation for updates

        previous_logs = frappe.get_all(
            "Delivery Status Log",
            filters={"message_sid": self.message_sid, "name": ["!=", self.name or ""]},
            fields=["status", "received_at"],
            order_by="received_at desc",
            limit=1,
        )

        if previous_logs:
            previous_status = previous_logs[0].status
            current_status = self.status

            allowed_statuses = valid_transitions.get(previous_status, [])
            if allowed_statuses and current_status not in allowed_statuses:
                frappe.throw(
                    _("Invalid status transition from {0} to {1}").format(
                        previous_status, current_status
                    )
                )

    def set_defaults(self):
        """Set default values"""
        if not self.received_at:
            self.received_at = now_datetime()

        if not self.processed_at:
            self.processed_at = now_datetime()

        if not self.created_by_user:
            self.created_by_user = frappe.session.user

        if not self.created_date:
            self.created_date = now_datetime()

        # Determine if this is a final status
        final_statuses = ["delivered", "read", "failed"]
        self.final_status = 1 if self.status in final_statuses else 0

    def before_save(self):
        """Actions before saving"""
        self.modified_by_user = frappe.session.user
        self.modified_date = now_datetime()

        # Link to Communication History if available
        if not self.communication_history and self.message_sid:
            history = frappe.db.get_value(
                "Communication History", {"external_id": self.message_sid}, "name"
            )
            if history:
                self.communication_history = history

    def after_insert(self):
        """Actions after inserting new delivery status log"""
        # Update Redis metrics if available
        self.update_redis_metrics()

        # Update Communication History record
        self.update_communication_history()

        # Check for alerting conditions
        self.check_alert_conditions()

    def update_redis_metrics(self):
        """Update Redis metrics for real-time monitoring"""
        try:
            from universal_workshop.communication_management.delivery_tracking import (
                DeliveryStatusTracker,
            )

            tracker = DeliveryStatusTracker()
            if tracker.redis_client:
                # Update status counters
                current_hour = now_datetime().strftime("%Y%m%d%H")
                hour_key = f"metrics:hourly:{current_hour}"
                tracker.redis_client.hincrby(hour_key, f"total_{self.status}", 1)

                # Update daily counters
                current_day = now_datetime().strftime("%Y%m%d")
                day_key = f"metrics:daily:{current_day}"
                tracker.redis_client.hincrby(day_key, f"total_{self.status}", 1)

        except Exception as e:
            frappe.log_error(f"Redis metrics update failed: {e}", "DeliveryStatusLog")

    def update_communication_history(self):
        """Update linked Communication History record"""
        if not self.communication_history:
            return

        try:
            history_doc = frappe.get_doc("Communication History", self.communication_history)

            # Update delivery status
            status_mapping = {
                "queued": "Queued",
                "sent": "Sent",
                "delivered": "Delivered",
                "read": "Read",
                "failed": "Failed",
                "undelivered": "Failed",
                "unknown": "Unknown",
            }

            new_status = status_mapping.get(self.status, "Unknown")

            if history_doc.delivery_status != new_status:
                history_doc.delivery_status = new_status
                history_doc.delivery_timestamp = self.received_at

                # Update cost if available
                if self.cost_omr:
                    history_doc.cost_omr = self.cost_omr

                # Add to delivery timeline
                if hasattr(history_doc, "delivery_timeline"):
                    timeline_entry = {
                        "timestamp": self.received_at,
                        "status": new_status,
                        "details": f"Provider status: {self.status}",
                    }

                    existing_timeline = json.loads(history_doc.delivery_timeline or "[]")
                    existing_timeline.append(timeline_entry)
                    history_doc.delivery_timeline = json.dumps(existing_timeline)

                history_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Communication history update failed: {e}", "DeliveryStatusLog")

    def check_alert_conditions(self):
        """Check if this status log triggers any alerts"""
        try:
            # Check for critical error codes
            critical_errors = ["30008", "30004", "30006", "21610"]  # Twilio critical errors

            if self.error_code in critical_errors:
                self.create_error_alert()

            # Check delivery failure patterns
            if self.status in ["failed", "undelivered"]:
                self.check_failure_patterns()

        except Exception as e:
            frappe.log_error(f"Alert condition check failed: {e}", "DeliveryStatusLog")

    def create_error_alert(self):
        """Create alert for critical error"""
        try:
            alert_doc = frappe.new_doc("Delivery Alert")
            alert_doc.alert_type = "Critical Error"
            alert_doc.severity = "Critical"
            alert_doc.description = f"Critical error {self.error_code}: {self.error_message}"
            alert_doc.message_sid = self.message_sid
            alert_doc.error_code = self.error_code
            alert_doc.customer = self.customer
            alert_doc.channel = self.channel
            alert_doc.triggered_at = now_datetime()
            alert_doc.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Error alert creation failed: {e}", "DeliveryStatusLog")

    def check_failure_patterns(self):
        """Check for failure patterns that might indicate system issues"""
        try:
            # Count recent failures for this customer/channel
            recent_failures = frappe.db.count(
                "Delivery Status Log",
                filters={
                    "customer": self.customer,
                    "channel": self.channel,
                    "status": ["in", ["failed", "undelivered"]],
                    "received_at": [">=", get_datetime() - frappe.utils.timedelta(hours=1)],
                },
            )

            # Alert if more than 3 failures in 1 hour for same customer/channel
            if recent_failures >= 3:
                alert_doc = frappe.new_doc("Delivery Alert")
                alert_doc.alert_type = "Failure Pattern"
                alert_doc.severity = "High"
                alert_doc.description = (
                    f"Multiple delivery failures for customer {self.customer} on {self.channel}"
                )
                alert_doc.customer = self.customer
                alert_doc.channel = self.channel
                alert_doc.failure_count = recent_failures
                alert_doc.triggered_at = now_datetime()
                alert_doc.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failure pattern check failed: {e}", "DeliveryStatusLog")

    @frappe.whitelist()
    def get_delivery_timeline(self):
        """Get complete delivery timeline for this message"""
        timeline = frappe.get_all(
            "Delivery Status Log",
            filters={"message_sid": self.message_sid},
            fields=["status", "received_at", "error_code", "error_message", "retry_count"],
            order_by="received_at asc",
        )

        return timeline

    @frappe.whitelist()
    def retry_delivery(self):
        """Mark message for retry (if applicable)"""
        if self.status not in ["failed", "undelivered"]:
            frappe.throw(_("Can only retry failed or undelivered messages"))

        try:
            # Create new queued status entry
            retry_log = frappe.new_doc("Delivery Status Log")
            retry_log.message_sid = self.message_sid
            retry_log.communication_history = self.communication_history
            retry_log.status = "queued"
            retry_log.channel = self.channel
            retry_log.customer = self.customer
            retry_log.phone_number = self.phone_number
            retry_log.message_content = self.message_content
            retry_log.retry_count = (self.retry_count or 0) + 1
            retry_log.received_at = now_datetime()
            retry_log.processed_at = now_datetime()
            retry_log.insert(ignore_permissions=True)

            frappe.msgprint(_("Message marked for retry"))
            return retry_log.name

        except Exception as e:
            frappe.log_error(f"Delivery retry failed: {e}", "DeliveryStatusLog")
            frappe.throw(_("Failed to mark message for retry: {0}").format(str(e)))


# WhiteListed methods for API access
@frappe.whitelist()
def get_delivery_statistics(filters=None):
    """Get delivery statistics with optional filters"""
    try:
        conditions = "1=1"
        values = []

        if filters:
            if filters.get("customer"):
                conditions += " AND customer = %s"
                values.append(filters["customer"])

            if filters.get("channel"):
                conditions += " AND channel = %s"
                values.append(filters["channel"])

            if filters.get("from_date"):
                conditions += " AND received_at >= %s"
                values.append(filters["from_date"])

            if filters.get("to_date"):
                conditions += " AND received_at <= %s"
                values.append(filters["to_date"])

        # Get status counts
        status_counts = frappe.db.sql(
            f"""
            SELECT status, COUNT(*) as count
            FROM `tabDelivery Status Log`
            WHERE {conditions}
            GROUP BY status
        """,
            values,
            as_dict=True,
        )

        # Calculate totals
        total_messages = sum(item["count"] for item in status_counts)
        delivered_count = sum(
            item["count"] for item in status_counts if item["status"] in ["delivered", "read"]
        )
        failed_count = sum(
            item["count"] for item in status_counts if item["status"] in ["failed", "undelivered"]
        )

        success_rate = (delivered_count / total_messages * 100) if total_messages > 0 else 100.0

        return {
            "total_messages": total_messages,
            "delivered": delivered_count,
            "failed": failed_count,
            "success_rate": round(success_rate, 2),
            "status_breakdown": status_counts,
        }

    except Exception as e:
        frappe.log_error(f"Delivery statistics error: {e}", "DeliveryStatusLog")
        return {"error": str(e)}


@frappe.whitelist()
def get_message_timeline(message_sid):
    """Get complete timeline for a specific message"""
    try:
        timeline = frappe.get_all(
            "Delivery Status Log",
            filters={"message_sid": message_sid},
            fields=["*"],
            order_by="received_at asc",
        )

        return timeline

    except Exception as e:
        frappe.log_error(f"Message timeline error: {e}", "DeliveryStatusLog")
        return {"error": str(e)}


@frappe.whitelist()
def bulk_retry_failed_messages(filters=None):
    """Bulk retry failed messages with optional filters"""
    try:
        conditions = "status IN ('failed', 'undelivered')"
        values = []

        if filters:
            if filters.get("customer"):
                conditions += " AND customer = %s"
                values.append(filters["customer"])

            if filters.get("channel"):
                conditions += " AND channel = %s"
                values.append(filters["channel"])

        failed_messages = frappe.db.sql(
            f"""
            SELECT DISTINCT message_sid, MAX(name) as latest_log
            FROM `tabDelivery Status Log`
            WHERE {conditions}
            GROUP BY message_sid
        """,
            values,
            as_dict=True,
        )

        retry_count = 0
        for message in failed_messages:
            try:
                log_doc = frappe.get_doc("Delivery Status Log", message["latest_log"])
                log_doc.retry_delivery()
                retry_count += 1
            except Exception as e:
                frappe.log_error(f"Bulk retry error for {message['message_sid']}: {e}")
                continue

        return {
            "status": "success",
            "retried_count": retry_count,
            "total_failed": len(failed_messages),
        }

    except Exception as e:
        frappe.log_error(f"Bulk retry error: {e}", "DeliveryStatusLog")
        return {"error": str(e)}
