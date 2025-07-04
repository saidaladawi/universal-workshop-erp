# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

"""
Delivery Alert DocType for monitoring SLA breaches and system alerts
Part of Universal Workshop ERP Communication Management System
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, time_diff_in_seconds
import json
from typing import Dict, Any, List


class DeliveryAlert(Document):
    """Controller for Delivery Alert DocType"""

    def validate(self):
        """Validate delivery alert data"""
        self.validate_alert_type()
        self.validate_severity()
        self.set_defaults()

    def validate_alert_type(self):
        """Validate alert type and required fields"""
        if not self.alert_type:
            frappe.throw(_("Alert Type is required"))

        # Validate required fields based on alert type
        if self.alert_type == "SLA Breach":
            if not self.current_success_rate or not self.threshold:
                frappe.throw(_("Success rate and threshold are required for SLA Breach alerts"))

        elif self.alert_type == "Critical Error":
            if not self.error_code:
                frappe.throw(_("Error code is required for Critical Error alerts"))

        elif self.alert_type == "Failure Pattern":
            if not self.failure_count:
                frappe.throw(_("Failure count is required for Failure Pattern alerts"))

    def validate_severity(self):
        """Validate severity level"""
        if not self.severity:
            frappe.throw(_("Severity is required"))

        # Auto-assign severity based on alert type if not set
        if self.alert_type == "SLA Breach" and self.current_success_rate:
            if self.current_success_rate < 90:
                self.severity = "Critical"
            elif self.current_success_rate < 95:
                self.severity = "High"
            elif self.current_success_rate < 98:
                self.severity = "Medium"
            else:
                self.severity = "Low"

        elif self.alert_type == "Critical Error":
            self.severity = "Critical"

    def set_defaults(self):
        """Set default values"""
        if not self.triggered_at:
            self.triggered_at = now_datetime()

        if not self.status:
            self.status = "Open"

        if not self.created_by_user:
            self.created_by_user = frappe.session.user

        if not self.created_date:
            self.created_date = now_datetime()

    def before_save(self):
        """Actions before saving"""
        self.modified_by_user = frappe.session.user
        self.modified_date = now_datetime()

        # Set acknowledgment timestamp when status changes to Acknowledged
        if self.status == "Acknowledged" and not self.acknowledged_at:
            self.acknowledged_at = now_datetime()

        # Set resolution timestamp when status changes to Resolved
        if self.status in ["Resolved", "Closed"] and not self.resolved_at:
            self.resolved_at = now_datetime()

    def after_insert(self):
        """Actions after inserting new alert"""
        # Send immediate notification for critical alerts
        if self.severity in ["Critical", "High"]:
            self.send_immediate_notification()

        # Auto-assign to system administrators
        self.auto_assign_alert()

        # Create alert timeline entry
        self.create_timeline_entry("Alert Created", f"Alert triggered: {self.description}")

    def send_immediate_notification(self):
        """Send immediate notification for critical alerts"""
        try:
            # Get system administrators
            admins = frappe.get_all(
                "User",
                filters={
                    "role_profile_name": ["in", ["System Manager", "Workshop Manager"]],
                    "enabled": 1,
                },
                fields=["email", "full_name", "mobile_no"],
            )

            subject = f"[{self.severity}] {self.alert_type}: {self.description[:50]}..."

            # Email notification
            for admin in admins:
                try:
                    frappe.sendmail(
                        recipients=[admin.email],
                        subject=subject,
                        template="delivery_alert_notification",
                        args={
                            "alert": self,
                            "admin_name": admin.full_name,
                            "dashboard_url": f"{frappe.utils.get_url()}/app/delivery-dashboard",
                        },
                    )
                except Exception as e:
                    frappe.log_error(f"Email notification failed for {admin.email}: {e}")

            # SMS notification for critical alerts
            if self.severity == "Critical":
                self.send_sms_alerts(admins)

        except Exception as e:
            frappe.log_error(f"Immediate notification failed: {e}", "DeliveryAlert")

    def send_sms_alerts(self, admins: List[Dict]):
        """Send SMS alerts for critical issues"""
        try:
            from universal_workshop.communication_management.sms_api import queue_sms_message

            message = f"CRITICAL ALERT: {self.alert_type} - {self.description[:100]}... Check delivery dashboard immediately."

            for admin in admins:
                if admin.mobile_no:
                    try:
                        queue_sms_message(
                            phone_number=admin.mobile_no,
                            message=message,
                            customer=None,
                            message_type="Alert",
                            priority="High",
                        )
                    except Exception as e:
                        frappe.log_error(f"SMS alert failed for {admin.mobile_no}: {e}")

        except Exception as e:
            frappe.log_error(f"SMS alert sending failed: {e}", "DeliveryAlert")

    def auto_assign_alert(self):
        """Auto-assign alert to appropriate user"""
        try:
            # Find the most appropriate user to assign based on alert type
            assignment_rules = {
                "SLA Breach": "System Manager",
                "Critical Error": "System Manager",
                "Failure Pattern": "Workshop Manager",
                "Rate Limit": "System Manager",
                "System Health": "System Manager",
            }

            target_role = assignment_rules.get(self.alert_type, "System Manager")

            # Get users with target role
            users = frappe.get_all(
                "User",
                filters={"role_profile_name": target_role, "enabled": 1},
                fields=["name", "full_name"],
                limit=1,
            )

            if users:
                self.assigned_to = users[0].name
                self.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Auto-assignment failed: {e}", "DeliveryAlert")

    def create_timeline_entry(self, action: str, details: str):
        """Create timeline entry for alert tracking"""
        try:
            timeline_entry = frappe.new_doc("Alert Timeline")
            timeline_entry.alert = self.name
            timeline_entry.action = action
            timeline_entry.details = details
            timeline_entry.user = frappe.session.user
            timeline_entry.timestamp = now_datetime()
            timeline_entry.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Timeline entry creation failed: {e}")

    @frappe.whitelist()
    def acknowledge_alert(self, notes=""):
        """Acknowledge the alert"""
        if self.status == "Open":
            self.status = "Acknowledged"
            self.acknowledged_at = now_datetime()
            if notes:
                self.response_notes = notes
            self.save(ignore_permissions=True)

            self.create_timeline_entry(
                "Acknowledged", f"Alert acknowledged by {frappe.session.user}"
            )
            frappe.msgprint(_("Alert acknowledged successfully"))
        else:
            frappe.throw(_("Only open alerts can be acknowledged"))

    @frappe.whitelist()
    def start_investigation(self, notes=""):
        """Start investigation on the alert"""
        if self.status in ["Open", "Acknowledged"]:
            self.status = "In Progress"
            if notes:
                self.response_notes = (self.response_notes or "") + f"\n\n{notes}"
            self.save(ignore_permissions=True)

            self.create_timeline_entry(
                "Investigation Started", f"Investigation started by {frappe.session.user}"
            )
            frappe.msgprint(_("Investigation started"))
        else:
            frappe.throw(_("Cannot start investigation on {0} alert").format(self.status.lower()))

    @frappe.whitelist()
    def resolve_alert(self, resolution_notes="", auto_resolved=False):
        """Resolve the alert"""
        if self.status != "Resolved":
            self.status = "Resolved"
            self.resolved_at = now_datetime()
            self.resolution_notes = resolution_notes
            self.auto_resolved = 1 if auto_resolved else 0
            self.save(ignore_permissions=True)

            action = "Auto-Resolved" if auto_resolved else "Resolved"
            self.create_timeline_entry(action, f"Alert resolved: {resolution_notes}")

            if not auto_resolved:
                frappe.msgprint(_("Alert resolved successfully"))
        else:
            frappe.throw(_("Alert is already resolved"))

    @frappe.whitelist()
    def close_alert(self, notes=""):
        """Close the alert"""
        if self.status == "Resolved":
            self.status = "Closed"
            if notes:
                self.resolution_notes = (
                    self.resolution_notes or ""
                ) + f"\n\nClosure notes: {notes}"
            self.save(ignore_permissions=True)

            self.create_timeline_entry("Closed", f"Alert closed by {frappe.session.user}")
            frappe.msgprint(_("Alert closed successfully"))
        else:
            frappe.throw(_("Only resolved alerts can be closed"))

    @frappe.whitelist()
    def get_alert_timeline(self):
        """Get complete timeline for this alert"""
        timeline = frappe.get_all(
            "Alert Timeline",
            filters={"alert": self.name},
            fields=["action", "details", "user", "timestamp"],
            order_by="timestamp asc",
        )

        return timeline

    def get_resolution_time(self):
        """Calculate resolution time in hours"""
        if self.triggered_at and self.resolved_at:
            return time_diff_in_seconds(self.resolved_at, self.triggered_at) / 3600
        return None

    def get_acknowledgment_time(self):
        """Calculate acknowledgment time in minutes"""
        if self.triggered_at and self.acknowledged_at:
            return time_diff_in_seconds(self.acknowledged_at, self.triggered_at) / 60
        return None


# WhiteListed methods for API access
@frappe.whitelist()
def get_active_alerts(filters=None):
    """Get list of active alerts with optional filters"""
    try:
        base_filters = {"status": ["in", ["Open", "Acknowledged", "In Progress"]]}

        if filters:
            if filters.get("severity"):
                base_filters["severity"] = filters["severity"]
            if filters.get("alert_type"):
                base_filters["alert_type"] = filters["alert_type"]
            if filters.get("assigned_to"):
                base_filters["assigned_to"] = filters["assigned_to"]

        alerts = frappe.get_all(
            "Delivery Alert",
            filters=base_filters,
            fields=["*"],
            order_by="severity desc, triggered_at desc",
        )

        return alerts

    except Exception as e:
        frappe.log_error(f"Active alerts query failed: {e}", "DeliveryAlert")
        return {"error": str(e)}


@frappe.whitelist()
def get_alert_statistics(days=7):
    """Get alert statistics for dashboard"""
    try:
        from_date = get_datetime() - frappe.utils.timedelta(days=int(days))

        # Get alert counts by type
        type_stats = frappe.db.sql(
            """
            SELECT alert_type, COUNT(*) as count
            FROM `tabDelivery Alert`
            WHERE triggered_at >= %s
            GROUP BY alert_type
        """,
            [from_date],
            as_dict=True,
        )

        # Get alert counts by severity
        severity_stats = frappe.db.sql(
            """
            SELECT severity, COUNT(*) as count
            FROM `tabDelivery Alert`
            WHERE triggered_at >= %s
            GROUP BY severity
        """,
            [from_date],
            as_dict=True,
        )

        # Get resolution metrics
        resolution_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_alerts,
                AVG(CASE WHEN resolved_at IS NOT NULL THEN 
                    TIMESTAMPDIFF(MINUTE, triggered_at, resolved_at) ELSE NULL END) as avg_resolution_time_minutes
            FROM `tabDelivery Alert`
            WHERE triggered_at >= %s
        """,
            [from_date],
            as_dict=True,
        )

        total_alerts = resolution_stats[0]["total_alerts"] if resolution_stats else 0
        resolved_alerts = resolution_stats[0]["resolved_alerts"] if resolution_stats else 0
        resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 100.0

        return {
            "total_alerts": total_alerts,
            "resolved_alerts": resolved_alerts,
            "resolution_rate": round(resolution_rate, 2),
            "avg_resolution_time_minutes": (
                resolution_stats[0]["avg_resolution_time_minutes"] if resolution_stats else 0
            ),
            "alerts_by_type": type_stats,
            "alerts_by_severity": severity_stats,
        }

    except Exception as e:
        frappe.log_error(f"Alert statistics error: {e}", "DeliveryAlert")
        return {"error": str(e)}


@frappe.whitelist()
def bulk_acknowledge_alerts(alert_ids, notes=""):
    """Bulk acknowledge multiple alerts"""
    try:
        acknowledged_count = 0

        for alert_id in alert_ids:
            try:
                alert_doc = frappe.get_doc("Delivery Alert", alert_id)
                if alert_doc.status == "Open":
                    alert_doc.acknowledge_alert(notes)
                    acknowledged_count += 1
            except Exception as e:
                frappe.log_error(f"Bulk acknowledge error for {alert_id}: {e}")
                continue

        return {
            "status": "success",
            "acknowledged_count": acknowledged_count,
            "total_alerts": len(alert_ids),
        }

    except Exception as e:
        frappe.log_error(f"Bulk acknowledge error: {e}", "DeliveryAlert")
        return {"error": str(e)}


@frappe.whitelist()
def create_custom_alert(alert_type, severity, description, **kwargs):
    """Create custom alert programmatically"""
    try:
        alert_doc = frappe.new_doc("Delivery Alert")
        alert_doc.alert_type = alert_type
        alert_doc.severity = severity
        alert_doc.description = description
        alert_doc.triggered_at = now_datetime()

        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(alert_doc, key):
                setattr(alert_doc, key, value)

        alert_doc.insert(ignore_permissions=True)

        return {
            "status": "success",
            "alert_id": alert_doc.name,
            "message": "Custom alert created successfully",
        }

    except Exception as e:
        frappe.log_error(f"Custom alert creation failed: {e}", "DeliveryAlert")
        return {"error": str(e)}


@frappe.whitelist()
def auto_resolve_outdated_alerts(hours=24):
    """Auto-resolve alerts that are older than specified hours"""
    try:
        cutoff_time = get_datetime() - frappe.utils.timedelta(hours=int(hours))

        outdated_alerts = frappe.get_all(
            "Delivery Alert",
            filters={
                "status": ["in", ["Open", "Acknowledged"]],
                "triggered_at": ["<=", cutoff_time],
                "severity": ["in", ["Low", "Medium"]],  # Only auto-resolve low/medium severity
            },
            fields=["name"],
        )

        resolved_count = 0
        for alert in outdated_alerts:
            try:
                alert_doc = frappe.get_doc("Delivery Alert", alert.name)
                alert_doc.resolve_alert(
                    resolution_notes=f"Auto-resolved after {hours} hours of inactivity",
                    auto_resolved=True,
                )
                resolved_count += 1
            except Exception as e:
                frappe.log_error(f"Auto-resolve error for {alert.name}: {e}")
                continue

        return {
            "status": "success",
            "resolved_count": resolved_count,
            "total_outdated": len(outdated_alerts),
        }

    except Exception as e:
        frappe.log_error(f"Auto-resolve error: {e}", "DeliveryAlert")
        return {"error": str(e)}
