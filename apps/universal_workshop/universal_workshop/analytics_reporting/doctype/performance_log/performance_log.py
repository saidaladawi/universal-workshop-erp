# Copyright (c) 2024, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now_datetime, add_days
from typing import Dict, List, Any, Optional
import statistics
from datetime import datetime, timedelta


class PerformanceLog(Document):
    """Performance Log for APM monitoring system"""

    def validate(self):
        """Validate performance log data"""
        self.validate_execution_time()
        self.set_defaults()
        if self.response_time and self.response_time < 0:
            frappe.throw(_("Response time cannot be negative"))

        if self.memory_usage and self.memory_usage < 0:
            frappe.throw(_("Memory usage cannot be negative"))

    def validate_execution_time(self):
        """Ensure execution time is reasonable"""
        if self.execution_time and self.execution_time < 0:
            frappe.throw(_("Execution time cannot be negative"))

        if self.execution_time and self.execution_time > 300:  # 5 minutes
            frappe.throw(_("Execution time seems unusually high (>5 minutes). Please verify."))

    def set_defaults(self):
        """Set default values"""
        if not self.timestamp:
            self.timestamp = now_datetime()

        if not self.user:
            self.user = frappe.session.user

    @staticmethod
    def get_function_performance_stats(function_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for a specific function"""
        try:
            stats = frappe.db.sql(
                """
                SELECT 
                    COUNT(*) as total_calls,
                    AVG(execution_time) as avg_execution_time,
                    MIN(execution_time) as min_execution_time,
                    MAX(execution_time) as max_execution_time,
                    AVG(memory_used_mb) as avg_memory_used,
                    AVG(cpu_used_percent) as avg_cpu_used,
                    COUNT(DISTINCT user) as unique_users,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
                FROM `tabPerformance Log`
                WHERE function_name = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """,
                [function_name, hours],
                as_dict=True,
            )

            if stats and stats[0]["total_calls"]:
                result = stats[0]

                # Calculate performance trends
                trend_stats = frappe.db.sql(
                    """
                    SELECT 
                        DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as hour,
                        AVG(execution_time) as hourly_avg_time,
                        COUNT(*) as hourly_calls,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as hourly_errors
                    FROM `tabPerformance Log`
                    WHERE function_name = %s
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    GROUP BY DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00')
                    ORDER BY hour
                """,
                    [function_name, hours],
                    as_dict=True,
                )

                result["hourly_trends"] = trend_stats
                result["error_rate"] = (result["error_count"] / result["total_calls"]) * 100
                result["performance_score"] = PerformanceLog._calculate_performance_score(result)

                return result
            else:
                return {"total_calls": 0, "message": "No performance data found"}

        except Exception as e:
            frappe.log_error(f"Function performance stats error: {str(e)}", "Performance Log Error")
            return {"error": str(e)}

    @staticmethod
    def _calculate_performance_score(stats: Dict) -> float:
        """Calculate overall performance score (0-100)"""
        try:
            # Speed score (0-40 points, better for faster functions)
            avg_time = stats.get("avg_execution_time", 5) or 5
            speed_score = max(0, 40 - (avg_time * 8))  # Penalize >5 second functions

            # Reliability score (0-30 points)
            error_rate = stats.get("error_rate", 100) or 0
            reliability_score = max(0, 30 - error_rate)

            # Consistency score (0-20 points)
            min_time = stats.get("min_execution_time", 0) or 0
            max_time = stats.get("max_execution_time", 1) or 1
            consistency_score = 20 * (1 - (max_time - min_time) / max_time) if max_time > 0 else 20

            # Usage score (0-10 points)
            usage_count = stats.get("total_calls", 0) or 0
            usage_score = min(10, usage_count / 100)  # Full score at 1000+ calls

            return min(100, speed_score + reliability_score + consistency_score + usage_score)

        except Exception:
            return 0.0

    @staticmethod
    def get_system_performance_overview(hours: int = 24) -> Dict[str, Any]:
        """Get system-wide performance overview"""
        try:
            # Overall statistics
            overall_stats = frappe.db.sql(
                """
                SELECT 
                    COUNT(*) as total_function_calls,
                    COUNT(DISTINCT function_name) as unique_functions,
                    COUNT(DISTINCT user) as active_users,
                    AVG(execution_time) as avg_response_time,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as total_errors,
                    AVG(memory_used_mb) as avg_memory_usage,
                    AVG(cpu_used_percent) as avg_cpu_usage
                FROM `tabPerformance Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """,
                [hours],
                as_dict=True,
            )

            # Top slowest functions
            slow_functions = frappe.db.sql(
                """
                SELECT 
                    function_name,
                    AVG(execution_time) as avg_time,
                    COUNT(*) as call_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
                FROM `tabPerformance Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY function_name
                ORDER BY avg_time DESC
                LIMIT 10
            """,
                [hours],
                as_dict=True,
            )

            # Most called functions
            popular_functions = frappe.db.sql(
                """
                SELECT 
                    function_name,
                    COUNT(*) as call_count,
                    AVG(execution_time) as avg_time,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
                FROM `tabPerformance Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY function_name
                ORDER BY call_count DESC
                LIMIT 10
            """,
                [hours],
                as_dict=True,
            )

            # Hourly trends
            hourly_trends = frappe.db.sql(
                """
                SELECT 
                    DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as hour,
                    COUNT(*) as calls,
                    AVG(execution_time) as avg_time,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors,
                    AVG(memory_used_mb) as avg_memory,
                    AVG(cpu_used_percent) as avg_cpu
                FROM `tabPerformance Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00')
                ORDER BY hour
            """,
                [hours],
                as_dict=True,
            )

            stats = overall_stats[0] if overall_stats else {}
            error_rate = (
                stats.get("total_errors", 0) / max(1, stats.get("total_function_calls", 1))
            ) * 100

            return {
                "period_hours": hours,
                "overview": {**stats, "error_rate_percent": round(error_rate, 2)},
                "top_slow_functions": slow_functions,
                "most_called_functions": popular_functions,
                "hourly_trends": hourly_trends,
                "generated_at": now_datetime().isoformat(),
            }

        except Exception as e:
            frappe.log_error(
                f"System performance overview error: {str(e)}", "Performance Log Error"
            )
            return {"error": str(e)}

    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 30) -> int:
        """Clean up old performance logs to maintain database performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Delete old performance logs
            deleted_count = frappe.db.sql(
                """
                DELETE FROM `tabPerformance Log`
                WHERE creation < %s
            """,
                [cutoff_date],
            )

            frappe.logger().info(f"Cleaned up {deleted_count} old performance logs")

            return deleted_count[0][0] if deleted_count else 0

        except Exception as e:
            frappe.log_error(f"Performance log cleanup error: {str(e)}", "Performance Log Error")
            return 0

    @staticmethod
    def get_function_error_analysis(function_name: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze errors for a specific function"""
        try:
            # Get error details
            errors = frappe.db.sql(
                """
                SELECT 
                    error,
                    COUNT(*) as error_count,
                    MAX(timestamp) as last_occurrence,
                    AVG(execution_time) as avg_execution_time
                FROM `tabPerformance Log`
                WHERE function_name = %s
                AND success = 0
                AND error IS NOT NULL
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY error
                ORDER BY error_count DESC
            """,
                [function_name, hours],
                as_dict=True,
            )

            # Get error frequency over time
            error_trends = frappe.db.sql(
                """
                SELECT 
                    DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00') as hour,
                    COUNT(*) as error_count
                FROM `tabPerformance Log`
                WHERE function_name = %s
                AND success = 0
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:00:00')
                ORDER BY hour
            """,
                [function_name, hours],
                as_dict=True,
            )

            return {
                "function_name": function_name,
                "error_details": errors,
                "error_trends": error_trends,
                "total_errors": sum(error["error_count"] for error in errors),
                "unique_error_types": len(errors),
                "generated_at": now_datetime().isoformat(),
            }

        except Exception as e:
            frappe.log_error(f"Function error analysis error: {str(e)}", "Performance Log Error")
            return {"error": str(e)}


# Whitelisted API methods
@frappe.whitelist()
def get_function_performance(function_name: str, hours: int = 24):
    """API endpoint for function performance statistics"""
    return PerformanceLog.get_function_performance_stats(function_name, int(hours))


@frappe.whitelist()
def get_system_overview(hours: int = 24):
    """API endpoint for system performance overview"""
    return PerformanceLog.get_system_performance_overview(int(hours))


@frappe.whitelist()
def get_error_analysis(function_name: str, hours: int = 24):
    """API endpoint for function error analysis"""
    return PerformanceLog.get_function_error_analysis(function_name, int(hours))


@frappe.whitelist()
def cleanup_performance_logs(days_to_keep: int = 30):
    """API endpoint to cleanup old performance logs"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions"))

    deleted_count = PerformanceLog.cleanup_old_logs(int(days_to_keep))

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": _("Cleaned up {0} old performance logs").format(deleted_count),
    }
