# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import os
import re
import json
import time
import socket
import psutil
import platform
import subprocess
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, flt, cint, get_datetime


class SystemHealthMonitor(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate system health monitor configuration"""
        self.validate_thresholds()
        self.validate_notification_settings()
        self.validate_maintenance_window()

    def before_save(self):
        """Prepare data before saving"""
        if not self.created_by_system:
            self.created_by_system = frappe.session.user
        if not self.created_date:
            self.created_date = now_datetime()

        self.modified_by_system = frappe.session.user
        self.modified_date = now_datetime()

        # Set Arabic names if missing
        if not self.monitor_name_ar and self.monitor_name:
            self.monitor_name_ar = self.get_arabic_name(self.monitor_name)

    def validate_thresholds(self):
        """Validate monitoring thresholds"""
        # CPU thresholds
        if self.cpu_threshold_warning >= self.cpu_threshold_critical:
            frappe.throw(_("CPU warning threshold must be less than critical threshold"))

        # Memory thresholds
        if self.memory_threshold_warning >= self.memory_threshold_critical:
            frappe.throw(_("Memory warning threshold must be less than critical threshold"))

        # Disk thresholds
        if self.disk_threshold_warning >= self.disk_threshold_critical:
            frappe.throw(_("Disk warning threshold must be less than critical threshold"))

    def validate_notification_settings(self):
        """Validate notification configuration"""
        if self.send_notifications and not self.notification_recipients:
            frappe.throw(_("Notification recipients are required when notifications are enabled"))

        if self.escalation_recipients and not self.notification_recipients:
            frappe.throw(
                _("Regular notification recipients must be set before escalation recipients")
            )

    def validate_maintenance_window(self):
        """Validate scheduled maintenance window"""
        if self.scheduled_maintenance:
            if not self.maintenance_window_start or not self.maintenance_window_end:
                frappe.throw(_("Maintenance window start and end times are required"))

            if get_datetime(self.maintenance_window_start) >= get_datetime(
                self.maintenance_window_end
            ):
                frappe.throw(_("Maintenance window end must be after start time"))

    @frappe.whitelist()
    def run_health_check(self):
        """Run comprehensive system health check"""
        try:
            self.log_health_check("Starting comprehensive health check...")

            # Check hardware metrics
            if self.hardware_monitoring_enabled:
                self.check_hardware_health()

            # Check software status
            if self.software_monitoring_enabled:
                self.check_software_health()

            # Check network connectivity
            if self.network_monitoring_enabled:
                self.check_network_health()

            # Calculate overall health score
            self.calculate_overall_health_score()

            # Check for alerts
            if self.alerting_enabled:
                self.check_and_send_alerts()

            # Update check times
            self.last_check_time = now_datetime()
            self.next_check_time = self.calculate_next_check_time()

            # Save without validation to avoid recursion
            self.db_set("last_check_time", self.last_check_time)
            self.db_set("next_check_time", self.next_check_time)
            self.db_set("health_status", self.health_status)
            self.db_set("overall_score", self.overall_score)

            self.log_health_check("Health check completed successfully")
            return True

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            self.log_health_check(error_msg)
            frappe.log_error(error_msg, "System Health Monitor Error")
            return False

    def check_hardware_health(self):
        """Monitor hardware metrics"""
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_percent = flt(cpu_percent, 2)

            # Memory Usage
            memory = psutil.virtual_memory()
            self.memory_total_gb = flt(memory.total / (1024**3), 2)
            self.memory_used_gb = flt(memory.used / (1024**3), 2)
            self.memory_usage_percent = flt(memory.percent, 2)

            # Disk Usage
            disk = psutil.disk_usage("/")
            self.disk_total_gb = flt(disk.total / (1024**3), 2)
            self.disk_used_gb = flt(disk.used / (1024**3), 2)
            self.disk_usage_percent = flt((disk.used / disk.total) * 100, 2)

            # System Load (Linux/Unix only)
            try:
                load_avg = os.getloadavg()
                self.system_load_1min = flt(load_avg[0], 2)
                self.system_load_5min = flt(load_avg[1], 2)
                self.system_load_15min = flt(load_avg[2], 2)
            except (OSError, AttributeError):
                # Not available on Windows
                pass

            # CPU Temperature (Linux only)
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Get first available temperature
                        for name, entries in temps.items():
                            if entries:
                                self.cpu_temperature = flt(entries[0].current, 1)
                                break
            except Exception:
                pass

            self.log_health_check(
                f"Hardware check: CPU {self.cpu_usage_percent}%, Memory {self.memory_usage_percent}%, Disk {self.disk_usage_percent}%"
            )

        except Exception as e:
            frappe.log_error(f"Hardware monitoring error: {str(e)}", "System Health Monitor")

    def check_software_health(self):
        """Monitor software services and applications"""
        try:
            # Check Frappe processes
            self.frappe_process_status = self.check_service_status("frappe")

            # Check database status
            self.database_status = self.check_database_health()

            # Check Redis status
            self.redis_status = self.check_service_status("redis")

            # Check Nginx status
            self.nginx_status = self.check_service_status("nginx")

            # Check Supervisor status
            self.supervisor_status = self.check_service_status("supervisor")

            # Get version information
            self.python_version = platform.python_version()

            try:
                import frappe as frappe_module

                self.frappe_version = getattr(frappe_module, "__version__", "Unknown")
            except Exception:
                self.frappe_version = "Unknown"

            try:
                import erpnext

                self.erpnext_version = getattr(erpnext, "__version__", "Unknown")
            except Exception:
                self.erpnext_version = "Unknown"

            try:
                import universal_workshop

                self.universal_workshop_version = getattr(
                    universal_workshop, "__version__", "1.0.0"
                )
            except Exception:
                self.universal_workshop_version = "1.0.0"

            # Check background jobs
            self.check_background_jobs()

            # Check last backup time
            self.check_last_backup()

            self.log_health_check(
                f"Software check: Frappe {self.frappe_process_status}, DB {self.database_status}, Redis {self.redis_status}"
            )

        except Exception as e:
            frappe.log_error(f"Software monitoring error: {str(e)}", "System Health Monitor")

    def check_network_health(self):
        """Monitor network connectivity and external services"""
        try:
            # Check internet connectivity
            self.internet_connectivity = self.check_internet_connection()

            # Check DNS resolution
            self.dns_resolution_time = self.check_dns_resolution()

            # Check external services
            self.check_external_services()

            # Check network performance
            self.check_network_performance()

            self.log_health_check(
                f"Network check: Internet {self.internet_connectivity}, DNS {self.dns_resolution_time}ms"
            )

        except Exception as e:
            frappe.log_error(f"Network monitoring error: {str(e)}", "System Health Monitor")

    def check_service_status(self, service_name):
        """Check status of system service"""
        try:
            # Try systemctl first
            result = subprocess.run(
                ["systemctl", "is-active", service_name], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "Running / يعمل"
            else:
                return "Stopped / متوقف"
        except Exception:
            try:
                # Fallback to service command
                result = subprocess.run(
                    ["service", service_name, "status"], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return "Running / يعمل"
                else:
                    return "Stopped / متوقف"
            except Exception:
                return "Unknown / غير معروف"

    def check_database_health(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()

            # Test database connection
            frappe.db.sql("SELECT 1")

            response_time = (time.time() - start_time) * 1000

            # Check connection count
            try:
                connections = frappe.db.sql("SHOW STATUS LIKE 'Threads_connected'", as_dict=True)
                if connections:
                    self.database_connection_count = cint(connections[0].get("Value", 0))
            except Exception:
                pass

            # Check slow queries
            try:
                slow_queries = frappe.db.sql("SHOW STATUS LIKE 'Slow_queries'", as_dict=True)
                if slow_queries:
                    self.database_slow_queries = cint(slow_queries[0].get("Value", 0))
            except Exception:
                pass

            if response_time > 1000:  # More than 1 second
                return "Slow / بطيء"
            else:
                return "Online / متصل"

        except Exception as e:
            frappe.log_error(f"Database health check error: {str(e)}", "System Health Monitor")
            return "Error / خطأ"

    def check_background_jobs(self):
        """Check background job status"""
        try:
            # Get job statistics from RQ or Frappe queue
            from frappe.utils.background_jobs import get_jobs

            jobs = get_jobs()

            running = len([j for j in jobs if j.get("status") == "running"])
            pending = len([j for j in jobs if j.get("status") == "queued"])
            failed = len([j for j in jobs if j.get("status") == "failed"])

            self.background_jobs_running = running
            self.background_jobs_pending = pending
            self.background_jobs_failed = failed

        except Exception:
            # Fallback values
            self.background_jobs_running = 0
            self.background_jobs_pending = 0
            self.background_jobs_failed = 0

    def check_last_backup(self):
        """Check when last backup was created"""
        try:
            backup_files = frappe.get_list(
                "Backup Manager",
                filters={"status": "Completed / مكتمل"},
                fields=["creation"],
                order_by="creation desc",
                limit=1,
            )

            if backup_files:
                self.last_backup_time = backup_files[0].creation

        except Exception:
            pass

    def check_internet_connection(self):
        """Check internet connectivity"""
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return "Connected / متصل"
        except Exception:
            return "Disconnected / منقطع"

    def check_dns_resolution(self):
        """Check DNS resolution time"""
        try:
            start_time = time.time()
            socket.gethostbyname("google.com")
            resolution_time = (time.time() - start_time) * 1000
            return flt(resolution_time, 2)
        except Exception:
            return 0.0

    def check_external_services(self):
        """Check status of external services"""
        try:
            # Email service check
            self.email_service_status = self.check_service_endpoint("smtp")

            # License server check
            self.license_server_status = self.check_service_endpoint("license")

            # VIN decoder check
            self.vin_decoder_status = self.check_service_endpoint("vin")

            # Payment gateway check
            self.payment_gateway_status = self.check_service_endpoint("payment")

        except Exception as e:
            frappe.log_error(f"External services check error: {str(e)}", "System Health Monitor")

    def check_service_endpoint(self, service_type):
        """Check specific service endpoint"""
        try:
            # This would check actual service endpoints
            # For now, return default status
            return "Online / متصل"
        except Exception:
            return "Unknown / غير معروف"

    def check_network_performance(self):
        """Check network performance metrics"""
        try:
            # Basic network latency check
            start_time = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            latency = (time.time() - start_time) * 1000
            self.network_latency_ms = flt(latency, 2)

            # Packet loss would require more complex testing
            self.packet_loss_percent = 0.0

        except Exception:
            self.network_latency_ms = 0.0
            self.packet_loss_percent = 100.0

    def calculate_overall_health_score(self):
        """Calculate overall system health score"""
        try:
            scores = []

            # Hardware health (40% weight)
            if self.hardware_monitoring_enabled:
                hardware_score = 100

                # CPU score
                if self.cpu_usage_percent > self.cpu_threshold_critical:
                    hardware_score -= 30
                elif self.cpu_usage_percent > self.cpu_threshold_warning:
                    hardware_score -= 15

                # Memory score
                if self.memory_usage_percent > self.memory_threshold_critical:
                    hardware_score -= 30
                elif self.memory_usage_percent > self.memory_threshold_warning:
                    hardware_score -= 15

                # Disk score
                if self.disk_usage_percent > self.disk_threshold_critical:
                    hardware_score -= 20
                elif self.disk_usage_percent > self.disk_threshold_warning:
                    hardware_score -= 10

                scores.append(("hardware", max(0, hardware_score), 0.4))

            # Software health (35% weight)
            if self.software_monitoring_enabled:
                software_score = 100

                # Critical services
                critical_services = [
                    self.frappe_process_status,
                    self.database_status,
                    self.redis_status,
                ]

                for service in critical_services:
                    if "Error" in service or "Stopped" in service or "Offline" in service:
                        software_score -= 25

                scores.append(("software", max(0, software_score), 0.35))

            # Network health (25% weight)
            if self.network_monitoring_enabled:
                network_score = 100

                if "Disconnected" in self.internet_connectivity:
                    network_score -= 50

                if self.network_latency_ms > 1000:
                    network_score -= 25
                elif self.network_latency_ms > 500:
                    network_score -= 15

                scores.append(("network", max(0, network_score), 0.25))

            # Calculate weighted average
            if scores:
                total_score = sum(score * weight for _, score, weight in scores)
                total_weight = sum(weight for _, _, weight in scores)
                overall_score = total_score / total_weight if total_weight > 0 else 0
            else:
                overall_score = 0

            self.overall_score = flt(overall_score, 2)

            # Set health status based on score
            if overall_score >= 90:
                self.health_status = "Healthy / سليم"
            elif overall_score >= 70:
                self.health_status = "Warning / تحذير"
            elif overall_score >= 50:
                self.health_status = "Critical / حرج"
            else:
                self.health_status = "Down / متوقف"

        except Exception as e:
            frappe.log_error(f"Health score calculation error: {str(e)}", "System Health Monitor")
            self.overall_score = 0
            self.health_status = "Unknown / غير معروف"

    def check_and_send_alerts(self):
        """Check conditions and send alerts if needed"""
        try:
            alert_messages = []
            alert_level = "None / لا شيء"

            # Check CPU threshold
            if self.cpu_usage_percent > self.cpu_threshold_critical:
                alert_messages.append(f"Critical CPU usage: {self.cpu_usage_percent}%")
                alert_level = "Critical / حرج"
            elif self.cpu_usage_percent > self.cpu_threshold_warning:
                alert_messages.append(f"High CPU usage: {self.cpu_usage_percent}%")
                if alert_level == "None / لا شيء":
                    alert_level = "Warning / تحذير"

            # Check memory threshold
            if self.memory_usage_percent > self.memory_threshold_critical:
                alert_messages.append(f"Critical memory usage: {self.memory_usage_percent}%")
                alert_level = "Critical / حرج"
            elif self.memory_usage_percent > self.memory_threshold_warning:
                alert_messages.append(f"High memory usage: {self.memory_usage_percent}%")
                if alert_level == "None / لا شيء":
                    alert_level = "Warning / تحذير"

            # Check disk threshold
            if self.disk_usage_percent > self.disk_threshold_critical:
                alert_messages.append(f"Critical disk usage: {self.disk_usage_percent}%")
                alert_level = "Critical / حرج"
            elif self.disk_usage_percent > self.disk_threshold_warning:
                alert_messages.append(f"High disk usage: {self.disk_usage_percent}%")
                if alert_level == "None / لا شيء":
                    alert_level = "Warning / تحذير"

            # Check service status
            if "Error" in self.database_status or "Offline" in self.database_status:
                alert_messages.append("Database service is down")
                alert_level = "Critical / حرج"

            if "Stopped" in self.frappe_process_status:
                alert_messages.append("Frappe process is stopped")
                alert_level = "Critical / حرج"

            # Send alerts if any
            if alert_messages:
                self.alert_level = alert_level
                self.alert_message = "; ".join(alert_messages)
                self.alert_message_ar = self.translate_alert_message(self.alert_message)

                # Check if we should send notification (frequency limiting)
                should_send = self.should_send_alert_notification()

                if should_send:
                    self.send_alert_notifications()
                    self.update_alert_counters()
            else:
                self.alert_level = "None / لا شيء"
                self.alert_message = ""
                self.alert_message_ar = ""

        except Exception as e:
            frappe.log_error(f"Alert checking error: {str(e)}", "System Health Monitor")

    def should_send_alert_notification(self):
        """Check if alert notification should be sent (frequency limiting)"""
        try:
            if not self.last_alert_time:
                return True

            time_since_last = now_datetime() - get_datetime(self.last_alert_time)
            minutes_since_last = time_since_last.total_seconds() / 60

            return minutes_since_last >= (self.alert_frequency_limit or 30)

        except Exception:
            return True

    def send_alert_notifications(self):
        """Send alert notifications via various channels"""
        try:
            if not self.send_notifications:
                return

            alert_title = f"System Health Alert - {self.monitor_name}"
            alert_content = f"""
            Monitor: {self.monitor_name}
            Status: {self.health_status}
            Score: {self.overall_score}%
            Alert Level: {self.alert_level}
            Message: {self.alert_message}
            
            Time: {now_datetime()}
            """

            # Email notifications
            if self.email_alerts and self.notification_recipients:
                self.send_email_notification(alert_title, alert_content)

            # SMS notifications
            if self.sms_alerts and self.notification_recipients:
                self.send_sms_notification(alert_title, alert_content)

            # Webhook notifications
            if self.webhook_url:
                self.send_webhook_notification(alert_title, alert_content)

        except Exception as e:
            frappe.log_error(f"Alert notification error: {str(e)}", "System Health Monitor")

    def send_email_notification(self, title, content):
        """Send email notification"""
        try:
            recipients = [email.strip() for email in self.notification_recipients.split(",")]

            frappe.sendmail(recipients=recipients, subject=title, message=content, delayed=False)

        except Exception as e:
            frappe.log_error(f"Email notification error: {str(e)}", "System Health Monitor")

    def send_sms_notification(self, title, content):
        """Send SMS notification"""
        try:
            # SMS implementation would go here
            # For now, just log
            frappe.logger().info(f"SMS Alert: {title}")

        except Exception as e:
            frappe.log_error(f"SMS notification error: {str(e)}", "System Health Monitor")

    def send_webhook_notification(self, title, content):
        """Send webhook notification"""
        try:
            import requests

            payload = {
                "monitor_name": self.monitor_name,
                "health_status": self.health_status,
                "overall_score": self.overall_score,
                "alert_level": self.alert_level,
                "alert_message": self.alert_message,
                "timestamp": str(now_datetime()),
            }

            requests.post(self.webhook_url, json=payload, timeout=10)

        except Exception as e:
            frappe.log_error(f"Webhook notification error: {str(e)}", "System Health Monitor")

    def update_alert_counters(self):
        """Update alert counters and timestamps"""
        try:
            self.last_alert_time = now_datetime()

            # Increment daily counter
            today = now_datetime().date()
            if hasattr(self, "_last_alert_date") and self._last_alert_date == today:
                self.alert_count_today = (self.alert_count_today or 0) + 1
            else:
                self.alert_count_today = 1
                self._last_alert_date = today

        except Exception as e:
            frappe.log_error(f"Alert counter update error: {str(e)}", "System Health Monitor")

    def calculate_next_check_time(self):
        """Calculate next health check time"""
        try:
            interval_minutes = self.check_interval_minutes or 5
            return now_datetime() + timedelta(minutes=interval_minutes)
        except Exception:
            return now_datetime() + timedelta(minutes=5)

    def log_health_check(self, message):
        """Log health check activities"""
        try:
            timestamp = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            # Append to health check log
            current_log = self.health_check_log or ""

            # Keep only last 50 entries
            log_lines = current_log.split("\n")
            if len(log_lines) > 50:
                log_lines = log_lines[-49:]  # Keep last 49 + new entry = 50

            log_lines.append(log_entry.strip())
            self.health_check_log = "\n".join(log_lines)

        except Exception:
            pass

    def get_arabic_name(self, english_name):
        """Get Arabic translation for monitor name"""
        arabic_translations = {
            "Main System Monitor": "مراقب النظام الرئيسي",
            "Hardware Monitor": "مراقب الأجهزة",
            "Software Monitor": "مراقب البرمجيات",
            "Network Monitor": "مراقب الشبكة",
            "Database Monitor": "مراقب قاعدة البيانات",
            "Application Monitor": "مراقب التطبيق",
        }

        return arabic_translations.get(english_name, english_name)

    def translate_alert_message(self, english_message):
        """Translate alert message to Arabic"""
        translations = {
            "Critical CPU usage": "استخدام حرج للمعالج",
            "High CPU usage": "استخدام عالي للمعالج",
            "Critical memory usage": "استخدام حرج للذاكرة",
            "High memory usage": "استخدام عالي للذاكرة",
            "Critical disk usage": "استخدام حرج للقرص",
            "High disk usage": "استخدام عالي للقرص",
            "Database service is down": "خدمة قاعدة البيانات متوقفة",
            "Frappe process is stopped": "عملية Frappe متوقفة",
        }

        arabic_message = english_message
        for en, ar in translations.items():
            arabic_message = arabic_message.replace(en, ar)

        return arabic_message

    @frappe.whitelist()
    def restart_service(self, service_name):
        """Restart a system service"""
        try:
            if not frappe.has_permission(self.doctype, "write"):
                frappe.throw(_("Insufficient permissions to restart services"))

            # Only allow restarting specific services
            allowed_services = ["frappe", "redis", "nginx", "supervisor"]
            if service_name not in allowed_services:
                frappe.throw(_("Service restart not allowed for {0}").format(service_name))

            # Restart service
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.log_health_check(f"Successfully restarted {service_name}")
                return {
                    "success": True,
                    "message": f"Service {service_name} restarted successfully",
                }
            else:
                error_msg = f"Failed to restart {service_name}: {result.stderr}"
                self.log_health_check(error_msg)
                return {"success": False, "message": error_msg}

        except Exception as e:
            error_msg = f"Service restart error: {str(e)}"
            frappe.log_error(error_msg, "System Health Monitor")
            return {"success": False, "message": error_msg}

    @frappe.whitelist()
    def get_real_time_metrics(self):
        """Get real-time system metrics"""
        try:
            metrics = {
                "timestamp": now_datetime().isoformat(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "network_io": psutil.net_io_counters()._asdict(),
                "process_count": len(psutil.pids()),
                "uptime": time.time() - psutil.boot_time(),
            }

            return metrics

        except Exception as e:
            frappe.log_error(f"Real-time metrics error: {str(e)}", "System Health Monitor")
            return {}

    @frappe.whitelist()
    def export_health_report(self):
        """Export comprehensive health report"""
        try:
            report_data = {
                "monitor_info": {
                    "name": self.monitor_name,
                    "name_ar": self.monitor_name_ar,
                    "type": self.monitor_type,
                    "overall_score": self.overall_score,
                    "health_status": self.health_status,
                },
                "hardware_metrics": {
                    "cpu_usage": self.cpu_usage_percent,
                    "memory_usage": self.memory_usage_percent,
                    "memory_total": self.memory_total_gb,
                    "disk_usage": self.disk_usage_percent,
                    "disk_total": self.disk_total_gb,
                    "cpu_temperature": self.cpu_temperature,
                },
                "software_status": {
                    "frappe": self.frappe_process_status,
                    "database": self.database_status,
                    "redis": self.redis_status,
                    "nginx": self.nginx_status,
                    "background_jobs_running": self.background_jobs_running,
                    "background_jobs_pending": self.background_jobs_pending,
                    "background_jobs_failed": self.background_jobs_failed,
                },
                "network_status": {
                    "internet_connectivity": self.internet_connectivity,
                    "dns_resolution_time": self.dns_resolution_time,
                    "network_latency": self.network_latency_ms,
                    "email_service": self.email_service_status,
                    "license_server": self.license_server_status,
                },
                "alerts": {
                    "current_level": self.alert_level,
                    "current_message": self.alert_message,
                    "alert_count_today": self.alert_count_today,
                    "last_alert_time": self.last_alert_time,
                },
                "uptime_stats": {
                    "uptime_24h": self.uptime_percentage_24h,
                    "uptime_7d": self.uptime_percentage_7d,
                    "uptime_30d": self.uptime_percentage_30d,
                    "average_response_time": self.average_response_time,
                },
                "generated_at": now_datetime().isoformat(),
            }

            return report_data

        except Exception as e:
            frappe.log_error(f"Health report export error: {str(e)}", "System Health Monitor")
            return {}


@frappe.whitelist()
def get_system_health_dashboard():
    """Get dashboard data for system health monitoring"""
    try:
        # Get all active monitors
        monitors = frappe.get_list(
            "System Health Monitor",
            filters={"monitoring_enabled": 1},
            fields=[
                "name",
                "monitor_name",
                "monitor_name_ar",
                "health_status",
                "overall_score",
                "last_check_time",
                "alert_level",
            ],
        )

        # Get system overview
        total_monitors = len(monitors)
        healthy_monitors = len([m for m in monitors if "Healthy" in m.health_status])
        warning_monitors = len([m for m in monitors if "Warning" in m.health_status])
        critical_monitors = len([m for m in monitors if "Critical" in m.health_status])

        # Calculate average health score
        if monitors:
            avg_score = sum(m.overall_score or 0 for m in monitors) / total_monitors
        else:
            avg_score = 0

        return {
            "monitors": monitors,
            "summary": {
                "total_monitors": total_monitors,
                "healthy_monitors": healthy_monitors,
                "warning_monitors": warning_monitors,
                "critical_monitors": critical_monitors,
                "average_health_score": round(avg_score, 2),
            },
            "last_updated": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"System health dashboard error: {str(e)}", "System Health Monitor")
        return {"error": str(e)}


@frappe.whitelist()
def run_all_health_checks():
    """Run health checks for all active monitors"""
    try:
        monitors = frappe.get_list(
            "System Health Monitor", filters={"monitoring_enabled": 1}, fields=["name"]
        )

        results = []
        for monitor in monitors:
            doc = frappe.get_doc("System Health Monitor", monitor.name)
            success = doc.run_health_check()
            results.append({"monitor": monitor.name, "success": success})

        return {
            "total_monitors": len(monitors),
            "results": results,
            "completed_at": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Batch health check error: {str(e)}", "System Health Monitor")
        return {"error": str(e)}


@frappe.whitelist()
def create_default_system_monitor():
    """Create default system health monitor"""
    try:
        # Check if default monitor already exists
        if frappe.db.exists("System Health Monitor", {"monitor_name": "Main System Monitor"}):
            return {"message": "Default monitor already exists"}

        # Create default monitor
        monitor = frappe.new_doc("System Health Monitor")
        monitor.monitor_name = "Main System Monitor"
        monitor.monitor_name_ar = "مراقب النظام الرئيسي"
        monitor.monitor_type = "Full System / النظام الكامل"
        monitor.monitoring_enabled = 1
        monitor.hardware_monitoring_enabled = 1
        monitor.software_monitoring_enabled = 1
        monitor.network_monitoring_enabled = 1
        monitor.alerting_enabled = 1
        monitor.send_notifications = 1
        monitor.email_alerts = 1
        monitor.check_interval_minutes = 5
        monitor.cpu_threshold_warning = 80
        monitor.cpu_threshold_critical = 95
        monitor.memory_threshold_warning = 80
        monitor.memory_threshold_critical = 95
        monitor.disk_threshold_warning = 80
        monitor.disk_threshold_critical = 95
        monitor.alert_frequency_limit = 30

        monitor.insert()

        return {
            "message": "Default system monitor created successfully",
            "monitor_name": monitor.name,
        }

    except Exception as e:
        frappe.log_error(f"Default monitor creation error: {str(e)}", "System Health Monitor")
        return {"error": str(e)}
