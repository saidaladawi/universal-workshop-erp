# Copyright (c) 2024, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now_datetime, add_days
from typing import Dict, List, Any
from datetime import datetime, timedelta


class MLModelUsageLog(Document):
    """ML Model Usage Log for tracking model performance and usage statistics"""

    def validate(self):
        """Validate ML usage log data"""
        self.validate_prediction_time()
        self.validate_accuracy()
        self.set_defaults()

    def validate_prediction_time(self):
        """Ensure prediction time is reasonable"""
        if self.prediction_time and self.prediction_time < 0:
            frappe.throw(_("Prediction time cannot be negative"))

        if self.prediction_time and self.prediction_time > 300:  # 5 minutes
            frappe.throw(_("Prediction time seems unusually high (>5 minutes). Please verify."))

    def validate_accuracy(self):
        """Validate accuracy values"""
        if self.accuracy is not None:
            if self.accuracy < 0 or self.accuracy > 1:
                frappe.throw(_("Accuracy must be between 0 and 1"))

    def set_defaults(self):
        """Set default values"""
        if not self.timestamp:
            self.timestamp = now_datetime()

        if not self.user:
            self.user = frappe.session.user

    @staticmethod
    def get_model_performance_stats(model_type: str, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive performance statistics for a model type"""
        try:
            stats = frappe.db.sql(
                """
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(prediction_time) as avg_prediction_time,
                    MIN(prediction_time) as min_prediction_time,
                    MAX(prediction_time) as max_prediction_time,
                    AVG(accuracy) as avg_accuracy,
                    MIN(accuracy) as min_accuracy,
                    MAX(accuracy) as max_accuracy,
                    COUNT(DISTINCT user) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM `tabML Model Usage Log`
                WHERE model_type = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
                [model_type, days],
                as_dict=True,
            )

            if stats and stats[0]["total_predictions"]:
                result = stats[0]

                # Calculate performance trends
                trend_stats = frappe.db.sql(
                    """
                    SELECT 
                        DATE(timestamp) as date,
                        AVG(prediction_time) as daily_avg_time,
                        AVG(accuracy) as daily_avg_accuracy,
                        COUNT(*) as daily_predictions
                    FROM `tabML Model Usage Log`
                    WHERE model_type = %s
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """,
                    [model_type, days],
                    as_dict=True,
                )

                result["daily_trends"] = trend_stats
                result["performance_score"] = MLModelUsageLog._calculate_performance_score(result)

                return result
            else:
                return {"total_predictions": 0, "message": "No usage data found"}

        except Exception as e:
            frappe.log_error(f"Model performance stats error: {str(e)}", "ML Usage Log Error")
            return {"error": str(e)}

    @staticmethod
    def _calculate_performance_score(stats: Dict) -> float:
        """Calculate overall performance score (0-100)"""
        try:
            # Base score from accuracy (0-40 points)
            accuracy_score = (stats.get("avg_accuracy", 0) or 0) * 40

            # Speed score (0-30 points, better for faster predictions)
            avg_time = stats.get("avg_prediction_time", 5) or 5
            speed_score = max(0, 30 - (avg_time * 6))  # Penalize >5 second predictions

            # Consistency score (0-20 points)
            min_acc = stats.get("min_accuracy", 0) or 0
            max_acc = stats.get("max_accuracy", 1) or 1
            consistency_score = 20 * (1 - (max_acc - min_acc)) if max_acc > min_acc else 20

            # Usage score (0-10 points)
            usage_count = stats.get("total_predictions", 0) or 0
            usage_score = min(10, usage_count / 10)  # Full score at 100+ predictions

            return min(100, accuracy_score + speed_score + consistency_score + usage_score)

        except Exception:
            return 0.0

    @staticmethod
    def get_usage_trends(model_type: str = None, days: int = 30) -> List[Dict]:
        """Get usage trends over time"""
        try:
            where_clause = ""
            params = [days]

            if model_type:
                where_clause = "AND model_type = %s"
                params.append(model_type)

            trends = frappe.db.sql(
                f"""
                SELECT 
                    DATE(timestamp) as date,
                    model_type,
                    COUNT(*) as prediction_count,
                    AVG(prediction_time) as avg_prediction_time,
                    AVG(accuracy) as avg_accuracy
                FROM `tabML Model Usage Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                {where_clause}
                GROUP BY DATE(timestamp), model_type
                ORDER BY date DESC, model_type
            """,
                params,
                as_dict=True,
            )

            return trends

        except Exception as e:
            frappe.log_error(f"Usage trends error: {str(e)}", "ML Usage Log Error")
            return []

    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 90) -> int:
        """Clean up old usage logs to maintain database performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Delete logs older than specified days
            deleted_count = frappe.db.sql(
                """
                DELETE FROM `tabML Model Usage Log`
                WHERE timestamp < %s
            """,
                [cutoff_date],
            )

            frappe.db.commit()

            if deleted_count:
                frappe.logger().info(f"Cleaned up {deleted_count} old ML usage logs")

            return deleted_count[0][0] if deleted_count else 0

        except Exception as e:
            frappe.log_error(f"Usage log cleanup error: {str(e)}", "ML Usage Log Error")
            return 0

    @staticmethod
    def get_user_usage_summary(user: str = None, days: int = 7) -> Dict[str, Any]:
        """Get usage summary for a specific user or current user"""
        try:
            target_user = user or frappe.session.user

            summary = frappe.db.sql(
                """
                SELECT 
                    model_type,
                    COUNT(*) as usage_count,
                    AVG(prediction_time) as avg_time,
                    AVG(accuracy) as avg_accuracy,
                    MAX(timestamp) as last_used
                FROM `tabML Model Usage Log`
                WHERE user = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY model_type
                ORDER BY usage_count DESC
            """,
                [target_user, days],
                as_dict=True,
            )

            total_usage = sum(row["usage_count"] for row in summary)

            return {
                "user": target_user,
                "total_predictions": total_usage,
                "models_used": len(summary),
                "model_breakdown": summary,
                "period_days": days,
            }

        except Exception as e:
            frappe.log_error(f"User usage summary error: {str(e)}", "ML Usage Log Error")
            return {"error": str(e)}


# Whitelisted API methods
@frappe.whitelist()
def get_model_performance_dashboard(model_type: str = None, days: int = 7):
    """Get model performance data for dashboard display"""
    try:
        if model_type:
            return MLModelUsageLog.get_model_performance_stats(model_type, days)
        else:
            # Get summary for all models
            all_models = frappe.db.sql(
                """
                SELECT DISTINCT model_type 
                FROM `tabML Model Usage Log`
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
                [days],
                as_list=True,
            )

            dashboard_data = []
            for model in all_models:
                model_stats = MLModelUsageLog.get_model_performance_stats(model[0], days)
                model_stats["model_type"] = model[0]
                dashboard_data.append(model_stats)

            return sorted(dashboard_data, key=lambda x: x.get("total_predictions", 0), reverse=True)

    except Exception as e:
        frappe.log_error(f"Dashboard data error: {str(e)}", "ML Usage Log Error")
        return {"error": str(e)}


@frappe.whitelist()
def get_usage_analytics(days: int = 30):
    """Get comprehensive usage analytics for all models"""
    try:
        analytics = frappe.db.sql(
            """
            SELECT 
                model_type,
                model_version,
                COUNT(*) as total_predictions,
                COUNT(DISTINCT user) as unique_users,
                AVG(prediction_time) as avg_prediction_time,
                AVG(accuracy) as avg_accuracy,
                DATE(MIN(timestamp)) as first_used,
                DATE(MAX(timestamp)) as last_used
            FROM `tabML Model Usage Log`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY model_type, model_version
            ORDER BY total_predictions DESC
        """,
            [days],
            as_dict=True,
        )

        # Calculate totals
        total_predictions = sum(row["total_predictions"] for row in analytics)
        unique_models = len(set(row["model_type"] for row in analytics))

        return {
            "summary": {
                "total_predictions": total_predictions,
                "unique_models": unique_models,
                "period_days": days,
            },
            "model_analytics": analytics,
            "trends": MLModelUsageLog.get_usage_trends(days=days),
        }

    except Exception as e:
        frappe.log_error(f"Usage analytics error: {str(e)}", "ML Usage Log Error")
        return {"error": str(e)}


@frappe.whitelist()
def cleanup_usage_logs(days_to_keep: int = 90):
    """Clean up old usage logs (admin only)"""
    if not frappe.has_permission("ML Model Usage Log", "delete"):
        frappe.throw(_("Insufficient permissions to cleanup logs"))

    deleted_count = MLModelUsageLog.cleanup_old_logs(days_to_keep)

    return {
        "message": f"Successfully cleaned up {deleted_count} old usage logs",
        "deleted_count": deleted_count,
    }


@frappe.whitelist()
def get_my_usage_summary(days: int = 7):
    """Get usage summary for current user"""
    return MLModelUsageLog.get_user_usage_summary(frappe.session.user, days)


def cleanup_old_logs():
    """Clean up old ML model usage logs (older than 30 days)"""
    try:
        cutoff_date = datetime.now() - timedelta(days=30)

        # Delete old ML model usage logs
        deleted_count = frappe.db.sql(
            """
            DELETE FROM `tabML Model Usage Log`
            WHERE creation < %s
        """,
            [cutoff_date],
        )

        frappe.logger().info(f"Cleaned up {deleted_count} old ML model usage logs")

    except Exception as e:
        frappe.logger().error(f"Error cleaning up ML model usage logs: {str(e)}")
