import frappe
from frappe.model.document import Document
from frappe import _
import json
import os
import psutil
import datetime
from pathlib import Path
import hashlib
import requests
from typing import Dict, List, Any


class UniversalWorkshopSettings(Document):
    """إعدادات النظام الشاملة لإدارة الورش"""

    def validate(self):
        """التحقق من صحة البيانات"""
        self.apply_theme_changes()
        self.update_system_settings()
        self.validate_license_settings()
        self.validate_backup_settings()
        self.validate_performance_settings()

    def validate_license_settings(self):
        """التحقق من صحة إعدادات الترخيص"""
        if self.license_key:
            if not self.is_valid_license_format(self.license_key):
                frappe.throw(_("Invalid license key format"))

            # التحقق من صحة الترخيص مع الخادم
            if self.license_compliance_mode:
                license_status = self.validate_license_with_server()
                if not license_status.get("valid"):
                    frappe.throw(
                        _("License validation failed: {0}").format(
                            license_status.get("error", "Unknown error")
                        )
                    )

    def validate_backup_settings(self):
        """التحقق من صحة إعدادات النسخ الاحتياطي"""
        if self.enable_automated_backup:
            if not self.backup_frequency:
                frappe.throw(_("Backup frequency is required when automated backup is enabled"))

            if self.backup_location:
                backup_path = Path(self.backup_location)
                if not backup_path.exists():
                    try:
                        backup_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        frappe.throw(_("Cannot create backup directory: {0}").format(str(e)))

    def validate_performance_settings(self):
        """التحقق من صحة إعدادات الأداء"""
        if self.enable_performance_monitoring:
            # التحقق من عتبات الأداء
            if self.cpu_threshold and (self.cpu_threshold < 10 or self.cpu_threshold > 95):
                frappe.throw(_("CPU threshold must be between 10% and 95%"))

            if self.memory_threshold and (self.memory_threshold < 10 or self.memory_threshold > 95):
                frappe.throw(_("Memory threshold must be between 10% and 95%"))

            if self.disk_threshold and (self.disk_threshold < 10 or self.disk_threshold > 95):
                frappe.throw(_("Disk threshold must be between 10% and 95%"))

    def apply_theme_changes(self):
        """تطبيق تغييرات الثيم والألوان"""
        if self.primary_color or self.secondary_color or self.theme_style:
            # إنشاء/تحديث CSS مُخصص
            custom_css = self.generate_custom_css()
            # حفظ CSS في ملف أو قاعدة البيانات
            self.save_custom_css(custom_css)

    def generate_custom_css(self):
        """إنشاء CSS مُخصص حسب الإعدادات"""
        theme_styles = {
            "Modern": {
                "border_radius": "8px",
                "shadow": "0 2px 8px rgba(0,0,0,0.1)",
                "font_family": "'Inter', 'Arial', sans-serif",
            },
            "Classic": {
                "border_radius": "4px",
                "shadow": "0 1px 3px rgba(0,0,0,0.2)",
                "font_family": "'Times New Roman', serif",
            },
            "Minimalist": {
                "border_radius": "2px",
                "shadow": "none",
                "font_family": "'Helvetica Neue', sans-serif",
            },
            "Industrial": {
                "border_radius": "0px",
                "shadow": "0 4px 12px rgba(0,0,0,0.15)",
                "font_family": "'Roboto Mono', monospace",
            },
        }

        style = theme_styles.get(self.theme_style, theme_styles["Modern"])

        css = f"""
        /* Universal Workshop Custom Theme - {self.theme_style} */
        :root {{
            --uw-primary-color: {self.primary_color or '#1976d2'};
            --uw-secondary-color: {self.secondary_color or '#424242'};
            --uw-accent-color: {self.primary_color or '#1976d2'}22;
            --uw-border-radius: {style['border_radius']};
            --uw-shadow: {style['shadow']};
            --uw-font-family: {style['font_family']};
        }}

        /* Global Styling */
        body {{
            font-family: var(--uw-font-family) !important;
        }}

        /* Header & Navigation */
        .navbar {{
            background: linear-gradient(135deg, var(--uw-primary-color), var(--uw-secondary-color)) !important;
            box-shadow: var(--uw-shadow);
        }}

        .navbar-brand {{
            display: flex;
            align-items: center;
        }}

        .navbar-brand img {{
            max-height: 40px;
            width: auto;
            margin-right: 10px;
        }}

        /* Sidebar */
        .sidebar {{
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%) !important;
        }}

        .sidebar .module-link {{
            border-radius: var(--uw-border-radius);
            margin: 2px 8px;
            transition: all 0.3s ease;
        }}

        .sidebar .module-link:hover {{
            background: var(--uw-accent-color) !important;
            transform: translateX(4px);
        }}

        /* Cards & Modules */
        .frappe-card, .card {{
            border-radius: var(--uw-border-radius) !important;
            box-shadow: var(--uw-shadow) !important;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }}

        .frappe-card:hover, .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
        }}

        /* Buttons */
        .btn-primary {{
            background: var(--uw-primary-color) !important;
            border-color: var(--uw-primary-color) !important;
            border-radius: var(--uw-border-radius) !important;
        }}

        .btn-secondary {{
            background: var(--uw-secondary-color) !important;
            border-color: var(--uw-secondary-color) !important;
            border-radius: var(--uw-border-radius) !important;
        }}

        /* Automotive Theme Elements */
        .automotive-card {{
            background: linear-gradient(135deg, var(--uw-accent-color), white);
            border-left: 4px solid var(--uw-primary-color);
            padding: 20px;
            margin: 10px 0;
            border-radius: var(--uw-border-radius);
        }}

        .automotive-icon {{
            background: var(--uw-primary-color);
            color: white;
            border-radius: 50%;
            padding: 12px;
            margin-right: 15px;
            font-size: 18px;
        }}

        /* Workshop Status Indicators */
        .status-available {{ background: #28a745; }}
        .status-busy {{ background: #dc3545; }}
        .status-maintenance {{ background: #ffc107; }}
        .status-closed {{ background: #6c757d; }}

        /* Forms */
        .form-control {{
            border-radius: var(--uw-border-radius) !important;
            border: 1px solid #e0e0e0;
        }}

        .form-control:focus {{
            border-color: var(--uw-primary-color) !important;
            box-shadow: 0 0 0 0.2rem {self.primary_color or '#1976d2'}33 !important;
        }}
        """

        return css

    def save_custom_css(self, css):
        """حفظ CSS المُخصص"""
        # حذف CSS القديم إن وجد
        if frappe.db.exists("Custom HTML Block", "Universal Workshop Theme"):
            frappe.delete_doc("Custom HTML Block", "Universal Workshop Theme")

        # إنشاء CSS جديد
        css_block = frappe.get_doc(
            {
                "doctype": "Custom HTML Block",
                "name": "Universal Workshop Theme",
                "html": f"<style>{css}</style>",
                "script": f"""
            // تطبيق الشعار والثيم
            $(document).ready(function() {{
                // إضافة الشعار
                if ('{self.workshop_logo}' && $('.navbar-brand img').length === 0) {{
                    $('.navbar-brand').prepend('<img src="{self.workshop_logo}" alt="Workshop Logo">');
                }}

                // إضافة class للثيم
                $('body').addClass('uw-theme-{self.theme_style.lower() if self.theme_style else "modern"}');

                // تطبيق الخط العربي
                if ('{self.language}' === 'ar') {{
                    $('body').css('font-family', '"Cairo", "Tahoma", sans-serif');
                    $('body').attr('dir', 'rtl');
                }}
            }});
            """,
            }
        )
        css_block.insert(ignore_permissions=True)
        frappe.db.commit()

    def update_system_settings(self):
        """تحديث إعدادات النظام الأساسية"""
        # تحديث إعدادات النظام
        if self.language or self.time_zone:
            system_settings = frappe.get_single("System Settings")

            if self.language:
                system_settings.language = self.language
            if self.time_zone:
                system_settings.time_zone = self.time_zone

            system_settings.save(ignore_permissions=True)

        # تحديث العملة الافتراضية
        if self.currency:
            frappe.db.set_default("currency", self.currency)

        # تحديث اسم الشركة
        if self.company_name:
            frappe.db.set_default("company", self.company_name)

    # ======== Backup Management Methods ========

    @frappe.whitelist()
    def create_manual_backup(self):
        """إنشاء نسخة احتياطية يدوياً"""
        try:
            backup_result = frappe.utils.backups.new_backup(
                ignore_files=False,
                backup_path_db=self.backup_location or None,
                backup_path_files=self.backup_location or None,
                backup_path_private_files=self.backup_location or None,
                force=True,
            )

            if self.enable_backup_verification:
                verification_result = self.verify_backup(backup_result.get("backup_path"))
                if not verification_result.get("valid"):
                    frappe.throw(_("Backup verification failed"))

            self.log_backup_event("Manual backup created successfully", "Success")
            return {
                "status": "success",
                "message": _("Backup created successfully"),
                "path": backup_result.get("backup_path"),
            }

        except Exception as e:
            self.log_backup_event(f"Manual backup failed: {str(e)}", "Error")
            frappe.throw(_("Backup creation failed: {0}").format(str(e)))

    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """التحقق من صحة النسخة الاحتياطية"""
        try:
            if not os.path.exists(backup_path):
                return {"valid": False, "error": "Backup file not found"}

            # التحقق من حجم الملف
            file_size = os.path.getsize(backup_path)
            if file_size < 1024:  # أقل من 1KB
                return {"valid": False, "error": "Backup file too small"}

            # التحقق من إمكانية قراءة الملف
            with open(backup_path, "rb") as f:
                f.read(1024)  # قراءة أول 1KB

            return {"valid": True, "size": file_size}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def log_backup_event(self, message: str, status: str):
        """تسجيل أحداث النسخ الاحتياطي"""
        frappe.get_doc(
            {
                "doctype": "Error Log",
                "method": "Backup Management",
                "error": f"[{status}] {message}",
                "creation": frappe.utils.now(),
            }
        ).insert(ignore_permissions=True)

    # ======== Performance Monitoring Methods ========

    @frappe.whitelist()
    def get_system_performance(self):
        """الحصول على بيانات أداء النظام الحالية"""
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk Usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # Network I/O
            network = psutil.net_io_counters()

            # Database Connections
            db_connections = self.get_database_connections()

            performance_data = {
                "cpu_usage": round(cpu_percent, 2),
                "memory_usage": round(memory_percent, 2),
                "disk_usage": round(disk_percent, 2),
                "memory_total": round(memory.total / (1024**3), 2),  # GB
                "memory_available": round(memory.available / (1024**3), 2),  # GB
                "disk_total": round(disk.total / (1024**3), 2),  # GB
                "disk_free": round(disk.free / (1024**3), 2),  # GB
                "network_sent": round(network.bytes_sent / (1024**2), 2),  # MB
                "network_received": round(network.bytes_recv / (1024**2), 2),  # MB
                "db_connections": db_connections,
                "timestamp": frappe.utils.now(),
            }

            # التحقق من العتبات وإرسال تنبيهات
            self.check_performance_thresholds(performance_data)

            return performance_data

        except Exception as e:
            frappe.log_error(f"Performance monitoring error: {str(e)}")
            return {"error": str(e)}

    def get_database_connections(self):
        """الحصول على عدد اتصالات قاعدة البيانات"""
        try:
            result = frappe.db.sql("SHOW STATUS LIKE 'Threads_connected'", as_dict=True)
            return int(result[0].get("Value", 0)) if result else 0
        except Exception:
            return 0

    def check_performance_thresholds(self, performance_data: Dict[str, Any]):
        """التحقق من عتبات الأداء وإرسال التنبيهات"""
        alerts = []

        if self.cpu_threshold and performance_data["cpu_usage"] > self.cpu_threshold:
            alerts.append(
                f"CPU usage ({performance_data['cpu_usage']}%) exceeds threshold ({self.cpu_threshold}%)"
            )

        if self.memory_threshold and performance_data["memory_usage"] > self.memory_threshold:
            alerts.append(
                f"Memory usage ({performance_data['memory_usage']}%) exceeds threshold ({self.memory_threshold}%)"
            )

        if self.disk_threshold and performance_data["disk_usage"] > self.disk_threshold:
            alerts.append(
                f"Disk usage ({performance_data['disk_usage']}%) exceeds threshold ({self.disk_threshold}%)"
            )

        if alerts and self.enable_performance_alerts:
            self.send_performance_alerts(alerts)

    def send_performance_alerts(self, alerts: List[str]):
        """إرسال تنبيهات الأداء"""
        alert_message = "\n".join(alerts)

        # إرسال إشعار داخلي
        frappe.get_doc(
            {
                "doctype": "Notification Log",
                "subject": _("Performance Alert"),
                "email_content": alert_message,
                "for_user": frappe.session.user,
                "type": "Alert",
            }
        ).insert(ignore_permissions=True)

        # إرسال بريد إلكتروني إذا كان مُفعل
        if self.performance_alert_email:
            frappe.sendmail(
                recipients=[self.performance_alert_email],
                subject=_("Universal Workshop - Performance Alert"),
                message=alert_message,
            )

    # ======== License Management Methods ========

    def is_valid_license_format(self, license_key: str) -> bool:
        """التحقق من تنسيق مفتاح الترخيص"""
        # تنسيق الترخيص: UW-XXXX-XXXX-XXXX-XXXX
        import re

        pattern = r"^UW-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
        return bool(re.match(pattern, license_key))

    def validate_license_with_server(self) -> Dict[str, Any]:
        """التحقق من صحة الترخيص مع الخادم"""
        try:
            hardware_fingerprint = self.get_hardware_fingerprint()

            response = requests.post(
                "https://license.universal-workshop.com/api/validate",
                json={
                    "license_key": self.license_key,
                    "hardware_fingerprint": hardware_fingerprint,
                    "product": "Universal Workshop ERP",
                },
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                # تحديث معلومات الترخيص
                self.license_status = result.get("status", "Unknown")
                self.license_user_count = result.get("user_count", 0)
                if result.get("expiry_date"):
                    self.license_expiry_date = result.get("expiry_date")

                return {"valid": result.get("valid", False), "data": result}
            else:
                return {"valid": False, "error": f"Server returned {response.status_code}"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def get_hardware_fingerprint(self) -> str:
        """الحصول على بصمة الجهاز"""
        try:
            # جمع معلومات الجهاز
            import platform
            import uuid

            system_info = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "machine": platform.machine(),
                "mac_address": str(uuid.getnode()),
                "hostname": platform.node(),
            }

            # إنشاء hash من المعلومات
            info_string = "|".join(system_info.values())
            fingerprint = hashlib.sha256(info_string.encode()).hexdigest()[:32]

            return fingerprint

        except Exception:
            return "UNKNOWN_HARDWARE"

    @frappe.whitelist()
    def refresh_license_status(self):
        """تحديث حالة الترخيص"""
        if self.license_key and self.license_compliance_mode:
            result = self.validate_license_with_server()
            self.save()
            return result
        return {"valid": False, "error": "License key not set or compliance mode disabled"}

    # ======== Integration Management Methods ========

    @frappe.whitelist()
    def test_api_endpoint(self, endpoint_url: str):
        """اختبار نقطة API خارجية"""
        try:
            response = requests.get(endpoint_url, timeout=10)
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "message": (
                    "API endpoint is accessible"
                    if response.status_code == 200
                    else f"HTTP {response.status_code}"
                ),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @frappe.whitelist()
    def get_api_usage_stats(self):
        """الحصول على إحصائيات استخدام API"""
        try:
            # هذا مثال - يجب ربطه بنظام تتبع API حقيقي
            stats = {
                "total_requests": frappe.db.count("API Request Log"),
                "requests_today": frappe.db.count(
                    "API Request Log", {"creation": [">=", frappe.utils.today()]}
                ),
                "avg_response_time": "145ms",  # يجب حسابه من البيانات الفعلية
                "success_rate": "98.5%",  # يجب حسابه من البيانات الفعلية
                "rate_limit_status": "Normal",
            }
            return stats
        except Exception as e:
            return {"error": str(e)}

    # ======== System Health Methods ========

    @frappe.whitelist()
    def run_health_check(self):
        """تشغيل فحص شامل لصحة النظام"""
        health_results = {
            "timestamp": frappe.utils.now(),
            "overall_status": "Healthy",
            "checks": [],
        }

        try:
            # فحص قاعدة البيانات
            db_check = self.check_database_health()
            health_results["checks"].append(db_check)

            # فحص الخدمات
            services_check = self.check_services_health()
            health_results["checks"].append(services_check)

            # فحص المساحة التخزينية
            storage_check = self.check_storage_health()
            health_results["checks"].append(storage_check)

            # فحص الاتصال بالإنترنت
            network_check = self.check_network_health()
            health_results["checks"].append(network_check)

            # تحديد الحالة العامة
            failed_checks = [
                check for check in health_results["checks"] if check["status"] != "Healthy"
            ]
            if failed_checks:
                health_results["overall_status"] = (
                    "Warning" if len(failed_checks) == 1 else "Critical"
                )

            return health_results

        except Exception as e:
            health_results["overall_status"] = "Error"
            health_results["error"] = str(e)
            return health_results

    def check_database_health(self):
        """فحص صحة قاعدة البيانات"""
        try:
            # اختبار الاتصال
            frappe.db.sql("SELECT 1")

            # فحص أداء قاعدة البيانات
            start_time = datetime.datetime.now()
            frappe.db.sql("SELECT COUNT(*) FROM tabUser")
            query_time = (datetime.datetime.now() - start_time).total_seconds()

            status = "Healthy" if query_time < 1.0 else "Warning"

            return {
                "component": "Database",
                "status": status,
                "details": f"Query time: {query_time:.3f}s",
                "response_time": query_time,
            }
        except Exception as e:
            return {
                "component": "Database",
                "status": "Critical",
                "details": f"Database error: {str(e)}",
            }

    def check_services_health(self):
        """فحص صحة الخدمات"""
        try:
            # فحص خدمة الويب
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", 8000))
            sock.close()

            if result == 0:
                return {
                    "component": "Web Service",
                    "status": "Healthy",
                    "details": "Web server is responding",
                }
            else:
                return {
                    "component": "Web Service",
                    "status": "Critical",
                    "details": "Web server is not responding",
                }
        except Exception as e:
            return {
                "component": "Web Service",
                "status": "Critical",
                "details": f"Service check error: {str(e)}",
            }

    def check_storage_health(self):
        """فحص صحة التخزين"""
        try:
            disk = psutil.disk_usage("/")
            free_percent = (disk.free / disk.total) * 100

            if free_percent > 20:
                status = "Healthy"
            elif free_percent > 10:
                status = "Warning"
            else:
                status = "Critical"

            return {
                "component": "Storage",
                "status": status,
                "details": f"Free space: {free_percent:.1f}% ({disk.free / (1024**3):.1f} GB)",
            }
        except Exception as e:
            return {
                "component": "Storage",
                "status": "Critical",
                "details": f"Storage check error: {str(e)}",
            }

    def check_network_health(self):
        """فحص صحة الشبكة"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            if response.status_code == 200:
                return {
                    "component": "Network",
                    "status": "Healthy",
                    "details": "Internet connectivity OK",
                }
            else:
                return {
                    "component": "Network",
                    "status": "Warning",
                    "details": f"Internet check returned {response.status_code}",
                }
        except Exception as e:
            return {
                "component": "Network",
                "status": "Warning",
                "details": f"Network check error: {str(e)}",
            }

    # ======== Mobile Device Management Methods ========

    @frappe.whitelist()
    def register_mobile_device(self, device_info: str):
        """تسجيل جهاز محمول جديد"""
        try:
            device_data = json.loads(device_info)

            # التحقق من وجود الجهاز مسبقاً
            existing_device = frappe.db.exists(
                "Mobile Device", {"device_id": device_data.get("device_id")}
            )

            if existing_device:
                return {"status": "exists", "message": _("Device already registered")}

            # إنشاء سجل جهاز جديد
            device_doc = frappe.get_doc(
                {
                    "doctype": "Mobile Device",
                    "device_id": device_data.get("device_id"),
                    "device_name": device_data.get("device_name"),
                    "platform": device_data.get("platform"),
                    "user": frappe.session.user,
                    "registration_date": frappe.utils.now(),
                    "status": "Active",
                }
            )
            device_doc.insert()

            return {"status": "success", "message": _("Device registered successfully")}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @frappe.whitelist()
    def get_registered_devices(self):
        """الحصول على قائمة الأجهزة المسجلة"""
        try:
            devices = frappe.get_all(
                "Mobile Device",
                fields=[
                    "name",
                    "device_name",
                    "platform",
                    "user",
                    "registration_date",
                    "last_sync",
                    "status",
                ],
                order_by="registration_date desc",
            )
            return {"devices": devices}
        except Exception as e:
            return {"error": str(e)}

    # ======== Utility Methods ========

    @frappe.whitelist()
    def reset_to_defaults(self):
        """إعادة تعيين الإعدادات للوضع الافتراضي"""
        self.primary_color = "#1976d2"
        self.secondary_color = "#424242"
        self.theme_style = "Modern"
        self.language = "ar"
        self.currency = "OMR"
        self.time_zone = "Asia/Muscat"

        # إعادة تعيين جميع الميزات
        for field in [
            "enable_notifications",
            "enable_sms",
            "enable_email",
            "enable_reports",
            "enable_analytics",
            "enable_backup",
            "enable_inventory",
            "enable_billing",
            "enable_scheduling",
            "enable_crm",
            "enable_pos",
        ]:
            setattr(self, field, 1)

        setattr(self, "enable_mobile", 0)

        self.save()

        return {"message": _("Settings reset successfully")}

    @frappe.whitelist()
    def export_settings(self):
        """تصدير الإعدادات كملف JSON"""
        settings_data = self.as_dict()

        # إزالة البيانات غير المطلوبة
        excluded_fields = ["name", "owner", "creation", "modified", "modified_by", "docstatus"]
        for field in excluded_fields:
            settings_data.pop(field, None)

        return {
            "file_name": f"workshop_settings_{frappe.utils.today()}.json",
            "content": json.dumps(settings_data, indent=2, ensure_ascii=False),
        }

    @frappe.whitelist()
    def import_settings(self, settings_json: str):
        """استيراد الإعدادات من ملف JSON"""
        try:
            settings_data = json.loads(settings_json)

            # تطبيق الإعدادات
            for key, value in settings_data.items():
                if hasattr(self, key) and key not in ["name", "doctype"]:
                    setattr(self, key, value)

            self.save()
            return {"status": "success", "message": _("Settings imported successfully")}

        except Exception as e:
            return {"status": "error", "message": str(e)}
