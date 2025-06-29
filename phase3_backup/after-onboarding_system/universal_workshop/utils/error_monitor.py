"""
Error Monitoring Utility for Universal Workshop ERP
Provides real-time error monitoring and alerting capabilities
"""

import frappe
import json
from datetime import datetime, timedelta
from frappe.utils import now, cint, flt


class ErrorMonitor:
    """Real-time error monitoring and alerting system"""

    def __init__(self):
        self.config = self.get_monitoring_config()

    def get_monitoring_config(self):
        """Get error monitoring configuration"""
        try:
            config_str = frappe.db.get_single_value("System Settings", "error_monitoring_config")
            if config_str:
                return json.loads(config_str)
            else:
                # Default configuration
                return {
                    "critical_error_threshold": 10,
                    "warning_error_threshold": 5,
                    "monitoring_interval": 300,
                    "alert_recipients": ["admin@workshop.local"],
                    "error_categories": {
                        "database": ["1054", "1146", "1062"],
                        "scheduler": ["scheduler", "cron", "background"],
                        "api": ["api", "whitelist", "authentication"],
                        "doctype": ["DocType", "not found", "missing"],
                        "validation": ["ValidationError", "MandatoryError"],
                    },
                }
        except Exception as e:
            frappe.log_error(f"Failed to get monitoring config: {str(e)}", "Error Monitor")
            return {}

    def check_error_threshold(self, hours=1):
        """Check if error threshold has been exceeded"""
        try:
            # Get error count for the specified time period
            error_count = frappe.db.sql(
                """
				SELECT COUNT(*) as count
				FROM `tabError Log`
				WHERE creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
			""",
                (hours,),
                as_dict=True,
            )[0]["count"]

            threshold = self.config.get("critical_error_threshold", 10)

            if error_count >= threshold:
                return {
                    "status": "critical",
                    "count": error_count,
                    "threshold": threshold,
                    "period_hours": hours,
                }
            elif error_count >= self.config.get("warning_error_threshold", 5):
                return {
                    "status": "warning",
                    "count": error_count,
                    "threshold": self.config.get("warning_error_threshold", 5),
                    "period_hours": hours,
                }
            else:
                return {"status": "normal", "count": error_count, "period_hours": hours}

        except Exception as e:
            frappe.log_error(f"Failed to check error threshold: {str(e)}", "Error Monitor")
            return {"status": "unknown", "error": str(e)}

    def get_error_summary(self, days=7):
        """Get comprehensive error summary"""
        try:
            # Daily error statistics
            daily_stats = frappe.db.sql(
                """
				SELECT 
					DATE(creation) as error_date,
					COUNT(*) as error_count,
					COUNT(DISTINCT method) as unique_methods
				FROM `tabError Log` 
				WHERE creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
				GROUP BY DATE(creation)
				ORDER BY error_date DESC
			""",
                (days,),
                as_dict=True,
            )

            # Top error types
            top_errors = frappe.db.sql(
                """
				SELECT 
					SUBSTRING(error, 1, 100) as error_type,
					COUNT(*) as frequency,
					MAX(creation) as last_occurrence
				FROM `tabError Log`
				WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
				GROUP BY SUBSTRING(error, 1, 100)
				ORDER BY frequency DESC
				LIMIT 10
			""",
                as_dict=True,
            )

            # Error categories
            error_categories = self.categorize_errors()

            return {
                "daily_stats": daily_stats,
                "top_errors": top_errors,
                "error_categories": error_categories,
                "total_errors_24h": sum(
                    [
                        stat["error_count"]
                        for stat in daily_stats
                        if stat["error_date"] >= (datetime.now() - timedelta(days=1)).date()
                    ]
                ),
                "summary_generated": now(),
            }

        except Exception as e:
            frappe.log_error(f"Failed to get error summary: {str(e)}", "Error Monitor")
            return {"error": str(e)}

    def categorize_errors(self):
        """Categorize recent errors by type"""
        try:
            categories = {}
            error_categories = self.config.get("error_categories", {})

            # Get recent errors
            recent_errors = frappe.db.sql(
                """
				SELECT error, method, creation
				FROM `tabError Log`
				WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
			""",
                as_dict=True,
            )

            for error in recent_errors:
                error_text = error["error"].lower()
                categorized = False

                for category, keywords in error_categories.items():
                    if any(keyword.lower() in error_text for keyword in keywords):
                        if category not in categories:
                            categories[category] = {"count": 0, "examples": []}
                        categories[category]["count"] += 1
                        if len(categories[category]["examples"]) < 3:
                            categories[category]["examples"].append(
                                {
                                    "error": (
                                        error["error"][:100] + "..."
                                        if len(error["error"]) > 100
                                        else error["error"]
                                    ),
                                    "method": error["method"],
                                    "time": error["creation"],
                                }
                            )
                        categorized = True
                        break

                if not categorized:
                    if "uncategorized" not in categories:
                        categories["uncategorized"] = {"count": 0, "examples": []}
                    categories["uncategorized"]["count"] += 1

            return categories

        except Exception as e:
            frappe.log_error(f"Failed to categorize errors: {str(e)}", "Error Monitor")
            return {}

    def send_error_alert(self, alert_data):
        """Send error alert to configured recipients"""
        try:
            alert_config = self.get_alert_config()

            if alert_config.get("email_alerts", False):
                recipients = alert_config.get("alert_recipients", [])

                subject = f"Universal Workshop ERP Error Alert - {alert_data['status'].upper()}"
                message = f"""
				Error Alert Triggered:
				
				Status: {alert_data['status']}
				Error Count: {alert_data['count']} errors in {alert_data['period_hours']} hour(s)
				Threshold: {alert_data['threshold']}
				
				Please check the error logs in the system for detailed information.
				
				Time: {now()}
				"""

                for recipient in recipients:
                    try:
                        frappe.sendmail(recipients=[recipient], subject=subject, message=message)
                    except Exception as e:
                        frappe.log_error(
                            f"Failed to send alert to {recipient}: {str(e)}", "Error Alert"
                        )

        except Exception as e:
            frappe.log_error(f"Failed to send error alert: {str(e)}", "Error Alert")

    def get_alert_config(self):
        """Get error alert configuration"""
        try:
            config_str = frappe.db.get_single_value("System Settings", "error_alert_config")
            if config_str:
                return json.loads(config_str)
            else:
                return {"email_alerts": True, "alert_recipients": ["admin@workshop.local"]}
        except Exception:
            return {}

    def cleanup_old_errors(self, days=30):
        """Clean up old error logs"""
        try:
            deleted_count = frappe.db.sql(
                """
				DELETE FROM `tabError Log` 
				WHERE creation < DATE_SUB(NOW(), INTERVAL %s DAY)
			""",
                (days,),
            )

            frappe.log_error(f"Cleaned up {deleted_count} old error logs", "Error Cleanup")
            return deleted_count

        except Exception as e:
            frappe.log_error(f"Failed to cleanup old errors: {str(e)}", "Error Cleanup")
            return 0


@frappe.whitelist()
def get_error_dashboard_data():
    """API endpoint to get error dashboard data"""
    try:
        monitor = ErrorMonitor()

        # Get error summary
        summary = monitor.get_error_summary()

        # Check current status
        status = monitor.check_error_threshold()

        return {"status": status, "summary": summary, "timestamp": now()}

    except Exception as e:
        frappe.log_error(f"Failed to get dashboard data: {str(e)}", "Error Dashboard API")
        return {"error": str(e)}


@frappe.whitelist()
def trigger_error_check():
    """Manual trigger for error threshold check"""
    try:
        monitor = ErrorMonitor()
        status = monitor.check_error_threshold()

        if status["status"] in ["critical", "warning"]:
            monitor.send_error_alert(status)

        return status

    except Exception as e:
        frappe.log_error(f"Failed to trigger error check: {str(e)}", "Error Check")
        return {"error": str(e)}


def scheduled_error_monitoring():
    """Scheduled function for regular error monitoring"""
    try:
        monitor = ErrorMonitor()

        # Check error threshold
        status = monitor.check_error_threshold()

        # Send alert if needed
        if status["status"] in ["critical", "warning"]:
            monitor.send_error_alert(status)

        # Cleanup old errors weekly
        if datetime.now().weekday() == 0:  # Monday
            monitor.cleanup_old_errors()

        frappe.log_error(
            f"Scheduled error monitoring completed: {status['status']}", "Error Monitoring"
        )

    except Exception as e:
        frappe.log_error(f"Scheduled error monitoring failed: {str(e)}", "Error Monitoring")
