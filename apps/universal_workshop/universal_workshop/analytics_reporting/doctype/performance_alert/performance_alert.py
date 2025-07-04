# Copyright (c) 2024, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
from typing import Dict, List, Any, Optional
import json


class PerformanceAlert(Document):
    """Performance Alert for APM monitoring system"""

    def validate(self):
        """Validate alert data"""
        self.validate_severity()
        self.set_defaults()

    def validate_severity(self):
        """Ensure severity is valid"""
        valid_severities = ["Low", "Medium", "High", "Critical"]
        if self.severity not in valid_severities:
            frappe.throw(
                _("Invalid severity. Must be one of: {0}").format(", ".join(valid_severities))
            )

    def set_defaults(self):
        """Set default values"""
        if not self.creation:
            self.creation = now_datetime()

    def before_save(self):
        """Before save operations"""
        # Parse alert_data if it's a string
        if isinstance(self.alert_data, str):
            try:
                self.alert_data = json.loads(self.alert_data)
            except (json.JSONDecodeError, TypeError):
                pass

    def resolve_alert(self, resolved_by: str = None):
        """Mark alert as resolved"""
        self.resolved = 1
        self.resolved_by = resolved_by or frappe.session.user
        self.resolved_at = now_datetime()
        self.save(ignore_permissions=True)

        # Send notification about resolution
        self._send_resolution_notification()

    def _send_resolution_notification(self):
        """Send notification when alert is resolved"""
        try:
            # Create system notification
            frappe.publish_realtime(
                "alert_resolved",
                {
                    "alert_id": self.name,
                    "alert_type": self.alert_type,
                    "metric_name": self.metric_name,
                    "resolved_by": self.resolved_by,
                    "resolved_at": self.resolved_at,
                },
                user=self.resolved_by,
            )

            # Log resolution for audit trail
            frappe.logger().info(f"Performance alert {self.name} resolved by {self.resolved_by}")

        except Exception as e:
            frappe.log_error(
                f"Alert resolution notification error: {str(e)}", "Performance Alert Error"
            )

    @staticmethod
    def get_active_alerts(alert_type: str = None, severity: str = None) -> List[Dict]:
        """Get list of active (unresolved) alerts"""
        try:
            filters = {"resolved": 0}

            if alert_type:
                filters["alert_type"] = alert_type

            if severity:
                filters["severity"] = severity

            alerts = frappe.get_list(
                "Performance Alert",
                filters=filters,
                fields=[
                    "name",
                    "alert_type",
                    "metric_name",
                    "metric_value",
                    "threshold_value",
                    "severity",
                    "function_name",
                    "creation",
                ],
                order_by="creation desc",
            )

            return alerts

        except Exception as e:
            frappe.log_error(f"Get active alerts error: {str(e)}", "Performance Alert Error")
            return []

    @staticmethod
    def get_alert_statistics(hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        try:
            # Total alerts by severity
            severity_stats = frappe.db.sql(
                """
                SELECT 
                    severity,
                    COUNT(*) as count,
                    SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as active_count
                FROM `tabPerformance Alert`
                WHERE creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY severity
            """,
                [hours],
                as_dict=True,
            )

            # Total alerts by type
            type_stats = frappe.db.sql(
                """
                SELECT 
                    alert_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as active_count
                FROM `tabPerformance Alert`
                WHERE creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY alert_type
            """,
                [hours],
                as_dict=True,
            )

            # Alert trends over time
            hourly_trends = frappe.db.sql(
                """
                SELECT 
                    DATE_FORMAT(creation, '%%Y-%%m-%%d %%H:00:00') as hour,
                    COUNT(*) as total_alerts,
                    SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as active_alerts,
                    SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) as critical_alerts
                FROM `tabPerformance Alert`
                WHERE creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY DATE_FORMAT(creation, '%%Y-%%m-%%d %%H:00:00')
                ORDER BY hour
            """,
                [hours],
                as_dict=True,
            )

            # Resolution statistics
            resolution_stats = frappe.db.sql(
                """
                SELECT 
                    COUNT(*) as total_resolved,
                    AVG(TIMESTAMPDIFF(MINUTE, creation, resolved_at)) as avg_resolution_time_minutes,
                    COUNT(DISTINCT resolved_by) as unique_resolvers
                FROM `tabPerformance Alert`
                WHERE resolved = 1
                AND creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """,
                [hours],
                as_dict=True,
            )

            # Most frequent alerts
            frequent_alerts = frappe.db.sql(
                """
                SELECT 
                    metric_name,
                    alert_type,
                    COUNT(*) as occurrence_count,
                    AVG(metric_value) as avg_metric_value,
                    MAX(creation) as last_occurrence
                FROM `tabPerformance Alert`
                WHERE creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY metric_name, alert_type
                ORDER BY occurrence_count DESC
                LIMIT 10
            """,
                [hours],
                as_dict=True,
            )

            return {
                "period_hours": hours,
                "severity_breakdown": severity_stats,
                "type_breakdown": type_stats,
                "hourly_trends": hourly_trends,
                "resolution_stats": resolution_stats[0] if resolution_stats else {},
                "frequent_alerts": frequent_alerts,
                "generated_at": now_datetime().isoformat(),
            }

        except Exception as e:
            frappe.log_error(f"Alert statistics error: {str(e)}", "Performance Alert Error")
            return {"error": str(e)}

    @staticmethod
    def create_alert(
        alert_type: str,
        metric_name: str,
        metric_value: float,
        threshold_value: float,
        severity: str,
        function_name: str = None,
        alert_data: Dict = None,
    ) -> str:
        """Create a new performance alert"""
        try:
            # Check if similar alert exists in the last 10 minutes to avoid spam
            existing_alert = frappe.db.exists(
                "Performance Alert",
                {
                    "alert_type": alert_type,
                    "metric_name": metric_name,
                    "function_name": function_name,
                    "resolved": 0,
                    "creation": (">=", frappe.utils.add_to_date(now_datetime(), minutes=-10)),
                },
            )

            if existing_alert:
                # Update existing alert instead of creating new one
                alert_doc = frappe.get_doc("Performance Alert", existing_alert)
                alert_doc.metric_value = metric_value
                alert_doc.alert_data = alert_data or {}
                alert_doc.save(ignore_permissions=True)
                return existing_alert

            # Create new alert
            alert_doc = frappe.new_doc("Performance Alert")
            alert_doc.alert_type = alert_type
            alert_doc.metric_name = metric_name
            alert_doc.metric_value = metric_value
            alert_doc.threshold_value = threshold_value
            alert_doc.severity = severity
            alert_doc.function_name = function_name
            alert_doc.alert_data = alert_data or {}
            alert_doc.resolved = 0

            alert_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            # Send real-time notification for critical alerts
            if severity == "Critical":
                PerformanceAlert._send_critical_alert_notification(alert_doc)

            return alert_doc.name

        except Exception as e:
            frappe.log_error(f"Create alert error: {str(e)}", "Performance Alert Error")
            return None

    @staticmethod
    def _send_critical_alert_notification(alert_doc):
        """Send immediate notification for critical alerts"""
        try:
            # Real-time notification to all system managers
            system_managers = frappe.get_list(
                "Has Role", filters={"role": "System Manager"}, fields=["parent"], distinct=True
            )

            for manager in system_managers:
                frappe.publish_realtime(
                    "critical_performance_alert",
                    {
                        "alert_id": alert_doc.name,
                        "alert_type": alert_doc.alert_type,
                        "metric_name": alert_doc.metric_name,
                        "metric_value": alert_doc.metric_value,
                        "threshold_value": alert_doc.threshold_value,
                        "function_name": alert_doc.function_name,
                        "message": f"Critical performance alert: {alert_doc.metric_name} = {alert_doc.metric_value}",
                    },
                    user=manager["parent"],
                )

            # Create system notification
            notification = frappe.new_doc("Notification Log")
            notification.subject = f"Critical Performance Alert: {alert_doc.metric_name}"
            notification.email_content = f"""
            <p><strong>Critical performance alert triggered:</strong></p>
            <ul>
                <li><strong>Metric:</strong> {alert_doc.metric_name}</li>
                <li><strong>Value:</strong> {alert_doc.metric_value}</li>
                <li><strong>Threshold:</strong> {alert_doc.threshold_value}</li>
                <li><strong>Function:</strong> {alert_doc.function_name or 'System-wide'}</li>
                <li><strong>Alert Type:</strong> {alert_doc.alert_type}</li>
            </ul>
            <p>Please investigate immediately.</p>
            """
            notification.document_type = "Performance Alert"
            notification.document_name = alert_doc.name
            notification.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                f"Critical alert notification error: {str(e)}", "Performance Alert Error"
            )

    @staticmethod
    def bulk_resolve_alerts(alert_ids: List[str], resolved_by: str = None) -> Dict[str, Any]:
        """Resolve multiple alerts at once"""
        try:
            resolved_count = 0
            errors = []

            for alert_id in alert_ids:
                try:
                    alert_doc = frappe.get_doc("Performance Alert", alert_id)
                    if not alert_doc.resolved:
                        alert_doc.resolve_alert(resolved_by)
                        resolved_count += 1
                except Exception as e:
                    errors.append(f"Alert {alert_id}: {str(e)}")

            return {
                "status": "completed",
                "resolved_count": resolved_count,
                "total_requested": len(alert_ids),
                "errors": errors,
            }

        except Exception as e:
            frappe.log_error(f"Bulk resolve alerts error: {str(e)}", "Performance Alert Error")
            return {"status": "error", "error": str(e), "resolved_count": 0}


# Whitelisted API methods
@frappe.whitelist()
def get_active_alerts(alert_type=None, severity=None):
    """API endpoint for active alerts"""
    return PerformanceAlert.get_active_alerts(alert_type, severity)


@frappe.whitelist()
def get_alert_statistics(hours=24):
    """API endpoint for alert statistics"""
    return PerformanceAlert.get_alert_statistics(int(hours))


@frappe.whitelist()
def resolve_alert(alert_id: str):
    """API endpoint to resolve a single alert"""
    try:
        alert_doc = frappe.get_doc("Performance Alert", alert_id)
        alert_doc.resolve_alert()

        return {"status": "success", "message": _("Alert {0} has been resolved").format(alert_id)}

    except Exception as e:
        frappe.log_error(f"Resolve alert API error: {str(e)}", "Performance Alert Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def bulk_resolve_alerts(alert_ids):
    """API endpoint to resolve multiple alerts"""
    if isinstance(alert_ids, str):
        alert_ids = json.loads(alert_ids)

    return PerformanceAlert.bulk_resolve_alerts(alert_ids)


@frappe.whitelist()
def create_manual_alert(
    alert_type,
    metric_name,
    metric_value,
    threshold_value,
    severity,
    function_name=None,
    alert_data=None,
):
    """API endpoint to manually create an alert"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions"))

    alert_data_dict = {}
    if alert_data and isinstance(alert_data, str):
        try:
            alert_data_dict = json.loads(alert_data)
        except json.JSONDecodeError:
            pass

    alert_id = PerformanceAlert.create_alert(
        alert_type,
        metric_name,
        float(metric_value),
        float(threshold_value),
        severity,
        function_name,
        alert_data_dict,
    )

    if alert_id:
        return {
            "status": "success",
            "alert_id": alert_id,
            "message": _("Alert created successfully"),
        }
    else:
        return {"status": "error", "error": "Failed to create alert"}


# ✅ ADD: Scheduler function for critical alert monitoring
def check_critical_alerts():
    """Scheduled function to check for critical alerts and escalate if needed"""
    try:
        # Get unresolved critical alerts older than 15 minutes
        critical_alerts = frappe.get_list(
            "Performance Alert",
            filters={
                "severity": "Critical",
                "resolved": 0,
                "creation": ("<=", frappe.utils.add_to_date(frappe.utils.now(), minutes=-15))
            },
            fields=["name", "alert_type", "metric_name", "metric_value", "creation"],
            order_by="creation asc"
        )

        escalated_count = 0
        
        for alert in critical_alerts:
            try:
                # Escalate alert - send additional notifications
                alert_doc = frappe.get_doc("Performance Alert", alert["name"])
                
                # Send escalation notification
                frappe.publish_realtime(
                    "critical_alert_escalation",
                    {
                        "alert_id": alert["name"],
                        "alert_type": alert["alert_type"],
                        "metric_name": alert["metric_name"],
                        "unresolved_duration": frappe.utils.time_diff_in_hours(frappe.utils.now(), alert["creation"]),
                        "message": f"Critical alert {alert['name']} has been unresolved for over 15 minutes"
                    },
                    room="system_managers"
                )
                
                # Create escalation notification
                notification = frappe.new_doc("Notification Log")
                notification.subject = f"ESCALATION: Critical Performance Alert {alert['name']}"
                notification.email_content = f"""
                <p><strong style="color: red;">CRITICAL ALERT ESCALATION</strong></p>
                <p>The following critical performance alert has been unresolved for over 15 minutes:</p>
                <ul>
                    <li><strong>Alert ID:</strong> {alert['name']}</li>
                    <li><strong>Type:</strong> {alert['alert_type']}</li>
                    <li><strong>Metric:</strong> {alert['metric_name']}</li>
                    <li><strong>Value:</strong> {alert['metric_value']}</li>
                    <li><strong>Created:</strong> {alert['creation']}</li>
                </ul>
                <p><strong>Immediate action required!</strong></p>
                """
                notification.document_type = "Performance Alert"
                notification.document_name = alert["name"]
                notification.insert(ignore_permissions=True)
                
                escalated_count += 1
                
            except Exception as e:
                frappe.log_error(f"Alert escalation error for {alert['name']}: {str(e)}", "Performance Alert Escalation Error")

        # Check for system-wide critical status
        system_critical_count = len(frappe.get_list(
            "Performance Alert",
            filters={"severity": "Critical", "resolved": 0}
        ))

        if system_critical_count >= 5:  # 5 or more unresolved critical alerts
            # System-wide critical alert
            frappe.publish_realtime(
                "system_critical_status",
                {
                    "critical_alert_count": system_critical_count,
                    "message": f"SYSTEM CRITICAL: {system_critical_count} unresolved critical alerts",
                    "timestamp": frappe.utils.now()
                },
                room="system_managers"
            )

        frappe.logger().info(f"Critical alert check completed: {escalated_count} alerts escalated, {system_critical_count} total critical")
        
        return {
            "status": "success",
            "escalated_alerts": escalated_count,
            "total_critical_alerts": system_critical_count,
            "timestamp": frappe.utils.now()
        }

    except Exception as e:
        frappe.log_error(f"Critical alert checking error: {str(e)}", "Performance Alert Check Error")
        return {"status": "error", "error": str(e)}
