"""
Advanced Application Performance Monitoring (APM) System
Comprehensive performance monitoring for Universal Workshop ERP with real-time alerting
"""

import time
import psutil
import frappe
import traceback
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class APMMonitor:
    """Advanced Application Performance Monitoring for Universal Workshop"""

    def __init__(self):
        self.redis_client = frappe.cache() if REDIS_AVAILABLE else None
        self.alert_thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 80,  # percentage
            "cpu_usage": 85,  # percentage
            "error_rate": 5,  # percentage
            "db_connection_time": 1.0,  # seconds
            "queue_length": 100,  # items
            "disk_usage": 85,  # percentage
        }

        # Performance metrics storage
        self.performance_history = []
        self.alert_history = []

        # Arabic translations for monitoring
        self.arabic_metrics = {
            "cpu_usage": "استخدام المعالج",
            "memory_usage": "استخدام الذاكرة",
            "disk_usage": "استخدام القرص الصلب",
            "response_time": "وقت الاستجابة",
            "error_rate": "معدل الأخطاء",
            "db_connection_time": "وقت الاتصال بقاعدة البيانات",
            "queue_length": "طول قائمة الانتظار",
        }

    def monitor_function(self, function_name: str = None, track_memory: bool = True):
        """Decorator for comprehensive function performance monitoring"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                function_name_actual = function_name or f"{func.__module__}.{func.__name__}"

                # Memory tracking
                process = psutil.Process() if track_memory else None
                memory_before = process.memory_info().rss / (1024 * 1024) if process else 0  # MB
                cpu_before = psutil.cpu_percent() if track_memory else 0

                error_occurred = None
                result = None

                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    error_occurred = str(e)
                    # Re-raise the exception after logging
                    raise
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time

                    # Memory and CPU after execution
                    memory_after = process.memory_info().rss / (1024 * 1024) if process else 0  # MB
                    cpu_after = psutil.cpu_percent() if track_memory else 0
                    memory_used = memory_after - memory_before
                    cpu_used = max(0, cpu_after - cpu_before)

                    # Record comprehensive metrics
                    self.record_function_metric(
                        function_name_actual,
                        execution_time,
                        success,
                        error_occurred,
                        memory_used,
                        cpu_used,
                        args,
                        kwargs,
                    )

                    # Check for performance alerts
                    self._check_performance_alerts(
                        function_name_actual,
                        {
                            "execution_time": execution_time,
                            "memory_used": memory_used,
                            "cpu_used": cpu_used,
                            "success": success,
                            "error": error_occurred,
                        },
                    )

                return result

            return wrapper

        return decorator

    def record_function_metric(
        self,
        function_name: str,
        execution_time: float,
        success: bool,
        error: str = None,
        memory_used: float = 0,
        cpu_used: float = 0,
        args: tuple = None,
        kwargs: dict = None,
    ):
        """Record comprehensive function performance metrics"""

        timestamp = frappe.utils.now()

        # Prepare metric data
        metric_data = {
            "timestamp": timestamp,
            "function_name": function_name,
            "execution_time": round(execution_time, 4),
            "success": success,
            "error": error,
            "memory_used_mb": round(memory_used, 2),
            "cpu_used_percent": round(cpu_used, 2),
            "system_memory_percent": psutil.virtual_memory().percent,
            "system_cpu_percent": psutil.cpu_percent(),
            "user": frappe.session.user,
            "session_id": frappe.session.sid,
            "request_id": getattr(frappe.local, "request_id", None),
        }

        # Store in database for long-term analysis
        try:
            performance_log = frappe.new_doc("Performance Log")
            performance_log.update(metric_data)
            performance_log.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to store performance log: {str(e)}", "APM Error")

        # Store in Redis for real-time monitoring (if available)
        if self.redis_client:
            try:
                metric_key = f"apm:function:{function_name}"

                # Store last 100 metrics per function
                self.redis_client.lpush(metric_key, frappe.as_json(metric_data))
                self.redis_client.ltrim(metric_key, 0, 99)  # Keep only last 100
                self.redis_client.expire(metric_key, 86400)  # 24 hours

                # Update real-time aggregated metrics
                self._update_realtime_metrics(function_name, metric_data)

            except Exception as e:
                frappe.log_error(f"Failed to store Redis metrics: {str(e)}", "APM Redis Error")

    def _update_realtime_metrics(self, function_name: str, metric_data: dict):
        """Update real-time aggregated metrics in Redis"""
        if not self.redis_client:
            return

        try:
            # Global system metrics
            global_key = "apm:system:global"
            current_hour = datetime.now().strftime("%Y%m%d%H")
            hourly_key = f"apm:system:hourly:{current_hour}"

            # Update global metrics
            self.redis_client.hincrby(global_key, "total_requests", 1)
            if not metric_data["success"]:
                self.redis_client.hincrby(global_key, "total_errors", 1)

            # Update hourly metrics
            self.redis_client.hincrby(hourly_key, "requests", 1)
            if not metric_data["success"]:
                self.redis_client.hincrby(hourly_key, "errors", 1)

            # Set expiry for hourly metrics (48 hours)
            self.redis_client.expire(hourly_key, 172800)

            # Update function-specific aggregated metrics
            func_key = f"apm:function:stats:{function_name}"
            self.redis_client.hset(
                func_key,
                {
                    "last_execution_time": metric_data["execution_time"],
                    "last_memory_used": metric_data["memory_used_mb"],
                    "last_cpu_used": metric_data["cpu_used_percent"],
                    "last_success": metric_data["success"],
                    "last_updated": metric_data["timestamp"],
                },
            )
            self.redis_client.expire(func_key, 86400)  # 24 hours

        except Exception as e:
            frappe.log_error(f"Redis real-time metrics update error: {str(e)}", "APM Redis Error")

    def _check_performance_alerts(self, function_name: str, metrics: dict):
        """Check metrics against thresholds and trigger alerts if needed"""
        alerts_triggered = []

        # Response time alert
        if metrics["execution_time"] > self.alert_thresholds["response_time"]:
            alerts_triggered.append(
                {
                    "type": "slow_function",
                    "metric": "response_time",
                    "value": metrics["execution_time"],
                    "threshold": self.alert_thresholds["response_time"],
                    "function": function_name,
                    "severity": "High" if metrics["execution_time"] > 5.0 else "Medium",
                }
            )

        # Memory usage alert
        current_memory = psutil.virtual_memory().percent
        if current_memory > self.alert_thresholds["memory_usage"]:
            alerts_triggered.append(
                {
                    "type": "high_memory_usage",
                    "metric": "memory_usage",
                    "value": current_memory,
                    "threshold": self.alert_thresholds["memory_usage"],
                    "function": function_name,
                    "severity": "Critical" if current_memory > 95 else "High",
                }
            )

        # CPU usage alert
        current_cpu = psutil.cpu_percent()
        if current_cpu > self.alert_thresholds["cpu_usage"]:
            alerts_triggered.append(
                {
                    "type": "high_cpu_usage",
                    "metric": "cpu_usage",
                    "value": current_cpu,
                    "threshold": self.alert_thresholds["cpu_usage"],
                    "function": function_name,
                    "severity": "Critical" if current_cpu > 95 else "High",
                }
            )

        # Function error alert
        if not metrics["success"]:
            alerts_triggered.append(
                {
                    "type": "function_error",
                    "metric": "error_rate",
                    "value": 100,  # 100% error for this specific call
                    "threshold": 0,
                    "function": function_name,
                    "error": metrics["error"],
                    "severity": "High",
                }
            )

        # Trigger alerts
        for alert in alerts_triggered:
            self.trigger_alert(alert)

    def trigger_alert(self, alert_data: dict):
        """Trigger comprehensive performance alert"""
        try:
            # Add timestamp and additional context
            alert_data.update(
                {
                    "timestamp": frappe.utils.now(),
                    "server_info": {
                        "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                        "cpu_count": psutil.cpu_count(),
                        "disk_usage_percent": psutil.disk_usage("/").percent,
                    },
                    "arabic_message": self._generate_arabic_alert_message(alert_data),
                }
            )

            # Store alert in database
            alert_doc = frappe.new_doc("Performance Alert")
            alert_doc.alert_type = alert_data["type"]
            alert_doc.metric_name = alert_data["metric"]
            alert_doc.metric_value = alert_data["value"]
            alert_doc.threshold_value = alert_data["threshold"]
            alert_doc.function_name = alert_data.get("function", "")
            alert_doc.severity = alert_data["severity"]
            alert_doc.alert_data = frappe.as_json(alert_data)
            alert_doc.resolved = 0
            alert_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            # Real-time notification via WebSocket
            frappe.publish_realtime(
                event="performance_alert", message=alert_data, room="system_administrators"
            )

            # Send email for critical alerts
            if alert_data["severity"] == "Critical":
                self._send_critical_alert_email(alert_data)

            # Log the alert
            frappe.logger().warning(
                f"Performance Alert: {alert_data['type']} - {alert_data['arabic_message']}"
            )

        except Exception as e:
            frappe.log_error(f"Alert triggering failed: {str(e)}", "APM Alert Error")

    def _generate_arabic_alert_message(self, alert_data: dict) -> str:
        """Generate Arabic alert message"""
        metric_ar = self.arabic_metrics.get(alert_data["metric"], alert_data["metric"])

        if alert_data["type"] == "slow_function":
            return f"تحذير: وظيفة بطيئة - {alert_data['function']} استغرقت {alert_data['value']:.2f} ثانية"
        elif alert_data["type"] == "high_memory_usage":
            return f"تحذير: {metric_ar} وصل إلى {alert_data['value']:.1f}%"
        elif alert_data["type"] == "high_cpu_usage":
            return f"تحذير: {metric_ar} وصل إلى {alert_data['value']:.1f}%"
        elif alert_data["type"] == "function_error":
            return f"خطأ في الوظيفة: {alert_data['function']} - {alert_data.get('error', 'خطأ غير محدد')}"
        else:
            return f"تحذير أداء: {metric_ar} = {alert_data['value']}"

    def _send_critical_alert_email(self, alert_data: dict):
        """Send email notification for critical alerts"""
        try:
            # Get system administrators
            admins = frappe.db.sql(
                """
                SELECT DISTINCT u.email, u.full_name
                FROM `tabUser` u
                JOIN `tabHas Role` hr ON hr.parent = u.name
                WHERE hr.role = 'System Manager'
                AND u.enabled = 1
                AND u.email IS NOT NULL
            """,
                as_dict=True,
            )

            subject = f"🚨 تحذير حرج - Universal Workshop ERP"

            message = f"""
            <div style="direction: rtl; font-family: 'Cairo', sans-serif;">
                <h2 style="color: #d32f2f;">تحذير أداء حرج</h2>
                <p><strong>نوع التحذير:</strong> {alert_data['arabic_message']}</p>
                <p><strong>مستوى الخطورة:</strong> {alert_data['severity']}</p>
                <p><strong>الوقت:</strong> {alert_data['timestamp']}</p>
                
                <h3>تفاصيل النظام:</h3>
                <ul>
                    <li>إجمالي الذاكرة: {alert_data['server_info']['total_memory_gb']} جيجابايت</li>
                    <li>عدد المعالجات: {alert_data['server_info']['cpu_count']}</li>
                    <li>استخدام القرص: {alert_data['server_info']['disk_usage_percent']:.1f}%</li>
                </ul>
                
                <p style="color: #d32f2f;">
                    <strong>يرجى فحص النظام فوراً والاتخاذ الإجراءات اللازمة.</strong>
                </p>
            </div>
            """

            for admin in admins:
                frappe.sendmail(
                    recipients=[admin["email"]], subject=subject, message=message, delayed=False
                )

        except Exception as e:
            frappe.log_error(f"Critical alert email failed: {str(e)}", "APM Email Error")

    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get comprehensive performance summary for last N hours"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            # Get performance data from database
            performance_data = frappe.db.sql(
                """
                SELECT 
                    function_name,
                    COUNT(*) as total_calls,
                    AVG(execution_time) as avg_execution_time,
                    MAX(execution_time) as max_execution_time,
                    MIN(execution_time) as min_execution_time,
                    AVG(memory_used_mb) as avg_memory_used,
                    AVG(cpu_used_percent) as avg_cpu_used,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count,
                    COUNT(DISTINCT user) as unique_users
                FROM `tabPerformance Log`
                WHERE timestamp >= %s AND timestamp <= %s
                GROUP BY function_name
                ORDER BY total_calls DESC
            """,
                [start_time, end_time],
                as_dict=True,
            )

            # System metrics
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            }

            # Calculate overall statistics
            total_calls = sum(item["total_calls"] for item in performance_data)
            total_errors = sum(item["error_count"] for item in performance_data)
            error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0

            # Get top slow functions
            slow_functions = sorted(
                performance_data, key=lambda x: x["avg_execution_time"], reverse=True
            )[:10]

            # Get most called functions
            popular_functions = sorted(
                performance_data, key=lambda x: x["total_calls"], reverse=True
            )[:10]

            return {
                "period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": hours,
                },
                "overview": {
                    "total_function_calls": total_calls,
                    "total_errors": total_errors,
                    "error_rate_percent": round(error_rate, 2),
                    "unique_functions": len(performance_data),
                    "avg_response_time": (
                        round(
                            sum(item["avg_execution_time"] for item in performance_data)
                            / len(performance_data),
                            4,
                        )
                        if performance_data
                        else 0
                    ),
                },
                "system_metrics": system_metrics,
                "top_slow_functions": slow_functions,
                "most_called_functions": popular_functions,
                "alert_status": self._get_current_alert_status(),
                "generated_at": frappe.utils.now(),
            }

        except Exception as e:
            frappe.log_error(
                f"Performance summary generation failed: {str(e)}", "APM Summary Error"
            )
            return {"error": str(e)}

    def _get_current_alert_status(self) -> Dict[str, Any]:
        """Get current alert status summary"""
        try:
            # Get unresolved alerts from last 24 hours
            alerts = frappe.db.sql(
                """
                SELECT 
                    severity,
                    COUNT(*) as count
                FROM `tabPerformance Alert`
                WHERE 
                    resolved = 0 
                    AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY severity
            """,
                as_dict=True,
            )

            alert_summary = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for alert in alerts:
                alert_summary[alert["severity"]] = alert["count"]

            return {
                "total_unresolved": sum(alert_summary.values()),
                "by_severity": alert_summary,
                "status": "healthy" if alert_summary["Critical"] == 0 else "critical",
            }

        except Exception:
            return {"error": "Failed to get alert status"}

    @frappe.whitelist()
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics for dashboard"""
        try:
            # Current system metrics
            current_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0,
                "timestamp": frappe.utils.now(),
            }

            # Redis metrics (if available)
            redis_metrics = {}
            if self.redis_client:
                try:
                    global_stats = self.redis_client.hgetall("apm:system:global")
                    redis_metrics = {
                        "total_requests": int(global_stats.get("total_requests", 0)),
                        "total_errors": int(global_stats.get("total_errors", 0)),
                        "error_rate": (
                            int(global_stats.get("total_errors", 0))
                            / max(1, int(global_stats.get("total_requests", 1)))
                        )
                        * 100,
                    }
                except Exception:
                    redis_metrics = {"error": "Redis unavailable"}

            # Database connection info
            db_metrics = self._get_database_metrics()

            return {
                "system": current_metrics,
                "redis": redis_metrics,
                "database": db_metrics,
                "status": self._determine_system_status(current_metrics, db_metrics),
            }

        except Exception as e:
            frappe.log_error(f"Real-time metrics collection failed: {str(e)}", "APM Metrics Error")
            return {"error": str(e)}

    def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Test database response time
            start_time = time.time()
            frappe.db.sql("SELECT 1")
            db_response_time = time.time() - start_time

            # Get connection count
            connections = frappe.db.sql("SHOW STATUS LIKE 'Threads_connected'")
            connection_count = int(connections[0][1]) if connections else 0

            # Get slow queries count
            slow_queries = frappe.db.sql("SHOW STATUS LIKE 'Slow_queries'")
            slow_query_count = int(slow_queries[0][1]) if slow_queries else 0

            return {
                "response_time": round(db_response_time, 4),
                "connection_count": connection_count,
                "slow_query_count": slow_query_count,
                "status": "healthy" if db_response_time < 1.0 else "slow",
            }

        except Exception as e:
            return {"error": str(e), "status": "error"}

    def _determine_system_status(self, system_metrics: dict, db_metrics: dict) -> str:
        """Determine overall system health status"""
        if (
            system_metrics["cpu_percent"] > 90
            or system_metrics["memory_percent"] > 90
            or system_metrics["disk_percent"] > 90
            or db_metrics.get("status") == "error"
        ):
            return "critical"
        elif (
            system_metrics["cpu_percent"] > 70
            or system_metrics["memory_percent"] > 70
            or system_metrics["disk_percent"] > 80
            or db_metrics.get("status") == "slow"
        ):
            return "warning"
        else:
            return "healthy"


# Global APM instance
apm_monitor = APMMonitor()


# Whitelisted API methods
@frappe.whitelist()
def get_performance_summary(hours: int = 1):
    """API endpoint for performance summary"""
    return apm_monitor.get_performance_summary(int(hours))


@frappe.whitelist()
def get_realtime_metrics():
    """API endpoint for real-time metrics"""
    return apm_monitor.get_realtime_metrics()


@frappe.whitelist()
def resolve_alert(alert_id: str):
    """API endpoint to mark alert as resolved"""
    try:
        alert_doc = frappe.get_doc("Performance Alert", alert_id)
        alert_doc.resolved = 1
        alert_doc.resolved_by = frappe.session.user
        alert_doc.resolved_at = frappe.utils.now()
        alert_doc.save()

        return {"success": True, "message": "Alert resolved successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# Decorator for easy function monitoring
def monitor_performance(function_name: str = None, track_memory: bool = True):
    """Easy-to-use decorator for function performance monitoring"""
    return apm_monitor.monitor_function(function_name, track_memory)


# ✅ ADD: Scheduler functions at the end of the file


def monitor_system_performance_job():
    """Scheduled job for comprehensive APM monitoring"""
    try:
        apm = APMMonitor()

        # Get current system metrics
        metrics = apm.get_realtime_metrics()

        # Log the monitoring completion
        frappe.logger().info(f"APM monitoring completed at {metrics.get('timestamp')}")

        return {
            "status": "success",
            "timestamp": metrics.get("timestamp"),
            "metrics_collected": len(metrics.get("system_metrics", {})),
        }

    except Exception as e:
        frappe.log_error(f"APM monitoring job error: {str(e)}", "APM Monitor Job Error")
        return {"status": "error", "error": str(e)}


def collect_realtime_metrics():
    """Collect real-time metrics every 10 minutes"""
    try:
        apm = APMMonitor()

        # Collect current performance data
        performance_data = {
            "timestamp": frappe.utils.now(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "active_users": len(frappe.get_all("Sessions", filters={"status": "Active"})),
        }

        # Store in Redis for real-time dashboard access
        if apm.redis_client:
            try:
                # Store current metrics
                metric_key = f"apm:realtime:{frappe.utils.now().strftime('%Y%m%d%H%M')}"
                apm.redis_client.setex(
                    metric_key, 3600, frappe.as_json(performance_data)
                )  # 1 hour expiry

                # Update system status
                apm.redis_client.setex(
                    "apm:current_status", 300, frappe.as_json(performance_data)
                )  # 5 min expiry

            except Exception as e:
                frappe.log_error(f"Redis metrics storage error: {str(e)}", "APM Redis Error")

        frappe.logger().info(f"Real-time APM metrics collected: {performance_data['timestamp']}")

        return {"status": "success", "metrics": performance_data}

    except Exception as e:
        frappe.log_error(f"Real-time metrics collection error: {str(e)}", "APM Metrics Error")
        return {"status": "error", "error": str(e)}
