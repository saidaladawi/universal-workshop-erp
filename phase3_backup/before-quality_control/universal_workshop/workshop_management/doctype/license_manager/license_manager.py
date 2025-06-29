"""
License Manager DocType Controller for Universal Workshop ERP
Comprehensive license management, validation, and compliance enforcement
"""

import hashlib
import json
import platform
import re
import socket
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import frappe
import psutil
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    add_to_date,
    cint,
    flt,
    get_datetime,
    now,
    now_datetime,
    today,
)


class LicenseManager(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate license data before saving"""
        self.validate_license_format()
        self.validate_business_information()
        self.validate_limits()
        self.validate_dates()
        self.update_hardware_info()
        self.calculate_next_validation()

    def before_save(self):
        """Process data before saving"""
        self.generate_hardware_fingerprint()
        self.update_security_info()
        self.log_activity("License information updated")

    def after_insert(self):
        """After license creation"""
        self.register_with_server()
        self.send_activation_notification()
        self.log_activity("New license created and registered")

    # ============ Validation Methods ============

    def validate_license_format(self):
        """التحقق من تنسيق رمز الترخيص"""
        if not self.license_code:
            frappe.throw(_("License code is required"))

        # تنسيق الترخيص: UW-XXXX-XXXX-XXXX-XXXX
        pattern = r"^UW-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
        if not re.match(pattern, self.license_code):
            frappe.throw(_("Invalid license code format. Expected: UW-XXXX-XXXX-XXXX-XXXX"))

    def validate_business_information(self):
        """التحقق من معلومات الشركة"""
        if not self.business_name or not self.business_name_ar:
            frappe.throw(_("Both English and Arabic business names are required"))

        if not self.license_owner:
            frappe.throw(_("License owner information is required"))

    def validate_limits(self):
        """التحقق من حدود الترخيص"""
        if self.max_users and self.max_users < 1:
            frappe.throw(_("Maximum users must be at least 1"))

        if self.max_devices and self.max_devices < 1:
            frappe.throw(_("Maximum devices must be at least 1"))

        if self.storage_limit_gb and self.storage_limit_gb < 0:
            frappe.throw(_("Storage limit cannot be negative"))

    def validate_dates(self):
        """التحقق من صحة التواريخ"""
        if self.expiry_date and self.issue_date:
            if get_datetime(self.expiry_date) <= get_datetime(self.issue_date):
                frappe.throw(_("Expiry date must be after issue date"))

    def calculate_next_validation(self):
        """حساب موعد التحقق التالي"""
        if not self.validation_interval:
            self.validation_interval = "24 Hours / 24 ساعة"

        interval_hours = self.get_validation_interval_hours()
        self.next_validation = add_to_date(
            now_datetime(), hours=interval_hours, as_datetime=True
        )

    def get_validation_interval_hours(self) -> int:
        """الحصول على فترة التحقق بالساعات"""
        interval_map = {
            "1 Hour / ساعة واحدة": 1,
            "6 Hours / 6 ساعات": 6,
            "12 Hours / 12 ساعة": 12,
            "24 Hours / 24 ساعة": 24,
            "48 Hours / 48 ساعة": 48,
            "Weekly / أسبوعياً": 168,
        }
        return interval_map.get(self.validation_interval, 24)

    # ============ Hardware Information Methods ============

    def update_hardware_info(self):
        """تحديث معلومات الجهاز"""
        try:
            self.server_hostname = platform.node()
            self.os_platform = platform.platform()
            self.cpu_info = platform.processor() or "Unknown"

            # معلومات الذاكرة
            memory = psutil.virtual_memory()
            self.total_memory_gb = round(memory.total / (1024**3), 2)

            # عنوان IP
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect(("8.8.8.8", 80))
                self.ip_address = sock.getsockname()[0]
                sock.close()
            except Exception:
                self.ip_address = "127.0.0.1"

            # عنوان MAC
            self.mac_address = ":".join(
                ["{:02x}".format((uuid.getnode() >> elements) & 0xFF) for elements in range(0, 2 * 6, 2)][::-1]
            )

            if not self.registration_date:
                self.registration_date = now()

        except Exception as e:
            self.log_error(f"Failed to update hardware info: {str(e)}")

    def generate_hardware_fingerprint(self):
        """إنشاء بصمة فريدة للجهاز"""
        try:
            # جمع المعلومات الفريدة للجهاز
            system_info = {
                "hostname": self.server_hostname or platform.node(),
                "platform": self.os_platform or platform.platform(),
                "processor": self.cpu_info or platform.processor(),
                "mac_address": self.mac_address or str(uuid.getnode()),
                "total_memory": str(self.total_memory_gb or 0),
            }

            # إنشاء hash من المعلومات
            info_string = "|".join(system_info.values())
            fingerprint = hashlib.sha256(info_string.encode()).hexdigest()[:32]
            self.hardware_fingerprint = fingerprint

        except Exception as e:
            self.hardware_fingerprint = "UNKNOWN_HARDWARE"
            self.log_error(f"Failed to generate hardware fingerprint: {str(e)}")

    # ============ License Activation Methods ============

    @frappe.whitelist()
    def activate_license(self, activation_code: str = None):
        """تفعيل الترخيص"""
        try:
            if self.activation_locked:
                frappe.throw(_("License activation is locked due to too many failed attempts"))

            if not activation_code and not self.activation_code:
                frappe.throw(_("Activation code is required"))

            if activation_code:
                self.activation_code = activation_code

            # التحقق من رمز التفعيل
            if not self.is_valid_activation_code(self.activation_code):
                self.increment_activation_attempts()
                frappe.throw(_("Invalid activation code"))

            # محاولة التفعيل مع الخادم
            result = self.activate_with_server()
            
            if result.get("success"):
                self.activation_status = "Activated / مفعل"
                self.activation_date = now()
                self.activated_by = frappe.session.user
                self.activation_method = "Online / عبر الإنترنت"
                self.license_status = "Active / نشط"
                self.activation_attempts = 0  # Reset attempts
                
                self.log_activity("License activated successfully")
                self.send_notification("License Activation Successful", 
                                     f"License {self.license_code} has been successfully activated.")
                
                self.save()
                return {"success": True, "message": _("License activated successfully")}
            else:
                self.increment_activation_attempts()
                error_msg = result.get("error", "Unknown activation error")
                self.log_error(f"Activation failed: {error_msg}")
                frappe.throw(_(f"Activation failed: {error_msg}"))

        except Exception as e:
            self.increment_activation_attempts()
            self.log_error(f"Activation error: {str(e)}")
            frappe.throw(_("Activation failed: {0}").format(str(e)))

    def is_valid_activation_code(self, code: str) -> bool:
        """التحقق من صحة رمز التفعيل"""
        if not code or len(code) < 16:
            return False
        
        # يمكن إضافة منطق تحقق أكثر تعقيداً هنا
        return True

    def increment_activation_attempts(self):
        """زيادة عداد محاولات التفعيل"""
        self.activation_attempts = (self.activation_attempts or 0) + 1
        
        if self.activation_attempts >= (self.max_activation_attempts or 5):
            self.activation_locked = 1
            self.log_activity(f"License activation locked after {self.activation_attempts} failed attempts")
            self.send_notification("License Activation Locked", 
                                 f"License {self.license_code} activation has been locked due to too many failed attempts.")

    def activate_with_server(self) -> Dict[str, Any]:
        """تفعيل الترخيص مع خادم الترخيص"""
        try:
            response = requests.post(
                "https://license.universal-workshop.com/api/activate",
                json={
                    "license_code": self.license_code,
                    "activation_code": self.activation_code,
                    "hardware_fingerprint": self.hardware_fingerprint,
                    "business_name": self.business_name,
                    "business_name_ar": self.business_name_ar,
                    "license_owner": self.license_owner,
                },
                timeout=30,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # تحديث معلومات الترخيص من الخادم
                    self.update_from_server_response(result.get("license_data", {}))
                    return {"success": True}
                else:
                    return {"success": False, "error": result.get("error", "Server validation failed")}
            else:
                return {"success": False, "error": f"Server returned {response.status_code}"}

        except requests.RequestException as e:
            # في حالة عدم توفر الاتصال، يمكن السماح بالتفعيل المؤقت
            if self.allow_offline_activation():
                return {"success": True, "offline": True}
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def allow_offline_activation(self) -> bool:
        """السماح بالتفعيل دون اتصال في حالات معينة"""
        # يمكن تعديل هذا المنطق حسب متطلبات العمل
        return self.edition in ["Trial / تجريبي", "Community / مجتمعي"]

    def update_from_server_response(self, license_data: Dict[str, Any]):
        """تحديث بيانات الترخيص من استجابة الخادم"""
        if license_data:
            self.license_type = license_data.get("license_type", self.license_type)
            self.edition = license_data.get("edition", self.edition)
            self.max_users = license_data.get("max_users", self.max_users)
            self.max_devices = license_data.get("max_devices", self.max_devices)
            self.max_workshops = license_data.get("max_workshops", self.max_workshops)
            self.expiry_date = license_data.get("expiry_date", self.expiry_date)
            
            # تحديث الميزات
            features = license_data.get("features", {})
            for feature, enabled in features.items():
                if hasattr(self, feature):
                    setattr(self, feature, enabled)

    # ============ License Validation Methods ============

    @frappe.whitelist()
    def validate_license(self) -> Dict[str, Any]:
        """التحقق من صحة الترخيص"""
        try:
            validation_result = {
                "valid": False,
                "status": self.license_status,
                "messages": [],
                "warnings": [],
                "expires_in_days": 0,
            }

            # التحقق من حالة التفعيل
            if self.activation_status != "Activated / مفعل":
                validation_result["messages"].append("License is not activated")
                return validation_result

            # التحقق من تاريخ الانتهاء
            if self.expiry_date:
                expiry = get_datetime(self.expiry_date)
                now_dt = now_datetime()
                
                if expiry <= now_dt:
                    self.license_status = "Expired / منتهي الصلاحية"
                    validation_result["messages"].append("License has expired")
                    self.log_compliance_violation("License expired")
                    return validation_result
                
                days_to_expiry = (expiry - now_dt).days
                validation_result["expires_in_days"] = days_to_expiry
                
                if days_to_expiry <= 30:
                    validation_result["warnings"].append(f"License expires in {days_to_expiry} days")

            # التحقق من الحدود
            usage_check = self.check_usage_limits()
            if not usage_check["within_limits"]:
                validation_result["warnings"].extend(usage_check["violations"])

            # التحقق مع الخادم (إذا كان التحقق الصارم مفعلاً)
            if self.strict_validation:
                server_check = self.validate_with_server()
                if not server_check.get("valid"):
                    validation_result["messages"].append("Server validation failed")
                    return validation_result

            # التحقق من بصمة الجهاز
            if not self.verify_hardware_fingerprint():
                validation_result["messages"].append("Hardware fingerprint mismatch")
                self.log_compliance_violation("Hardware fingerprint mismatch")
                return validation_result

            # الترخيص صالح
            validation_result["valid"] = True
            self.last_validation = now()
            self.license_status = "Active / نشط"
            
            self.log_activity("License validation successful")
            return validation_result

        except Exception as e:
            self.log_error(f"License validation error: {str(e)}")
            return {
                "valid": False,
                "status": "Error",
                "messages": [f"Validation error: {str(e)}"],
                "warnings": [],
                "expires_in_days": 0,
            }

    def check_usage_limits(self) -> Dict[str, Any]:
        """التحقق من حدود الاستخدام"""
        result = {"within_limits": True, "violations": [], "usage": {}}

        try:
            # عدد المستخدمين النشطين
            active_users = frappe.db.count("User", {"enabled": 1, "user_type": "System User"})
            result["usage"]["active_users"] = active_users
            
            if self.max_users and active_users > self.max_users:
                result["within_limits"] = False
                result["violations"].append(f"Active users ({active_users}) exceeds limit ({self.max_users})")

            # عدد الورش
            workshop_count = frappe.db.count("Workshop Profile")
            result["usage"]["workshops"] = workshop_count
            
            if self.max_workshops and workshop_count > self.max_workshops:
                result["within_limits"] = False
                result["violations"].append(f"Workshops ({workshop_count}) exceeds limit ({self.max_workshops})")

            # تحديث العدادات الحالية
            self.current_users = active_users
            
        except Exception as e:
            result["within_limits"] = False
            result["violations"].append(f"Error checking usage limits: {str(e)}")

        return result

    def validate_with_server(self) -> Dict[str, Any]:
        """التحقق من الترخيص مع الخادم"""
        try:
            response = requests.post(
                "https://license.universal-workshop.com/api/validate",
                json={
                    "license_code": self.license_code,
                    "hardware_fingerprint": self.hardware_fingerprint,
                    "business_name": self.business_name,
                },
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                self.last_sync = now()
                return result
            else:
                return {"valid": False, "error": f"Server returned {response.status_code}"}

        except requests.RequestException as e:
            # في حالة عدم توفر الاتصال، التحقق من فترة السماح
            if self.is_within_grace_period():
                return {"valid": True, "offline": True}
            return {"valid": False, "error": f"Connection error: {str(e)}"}

    def is_within_grace_period(self) -> bool:
        """التحقق من وجود فترة سماح للعمل دون اتصال"""
        if not self.last_sync or not self.offline_grace_period:
            return False

        last_sync_dt = get_datetime(self.last_sync)
        grace_period_end = last_sync_dt + timedelta(hours=self.offline_grace_period)
        
        if now_datetime() <= grace_period_end:
            # حساب الساعات المستخدمة من فترة السماح
            hours_used = (now_datetime() - last_sync_dt).total_seconds() / 3600
            self.grace_period_used = int(hours_used)
            return True
        
        return False

    def verify_hardware_fingerprint(self) -> bool:
        """التحقق من مطابقة بصمة الجهاز"""
        if not self.hardware_fingerprint:
            return True  # لا يوجد بصمة محفوظة للمقارنة

        current_fingerprint = self.generate_current_fingerprint()
        return current_fingerprint == self.hardware_fingerprint

    def generate_current_fingerprint(self) -> str:
        """إنشاء بصمة الجهاز الحالية للمقارنة"""
        try:
            system_info = {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "mac_address": str(uuid.getnode()),
                "total_memory": str(round(psutil.virtual_memory().total / (1024**3), 2)),
            }

            info_string = "|".join(system_info.values())
            return hashlib.sha256(info_string.encode()).hexdigest()[:32]

        except Exception:
            return "UNKNOWN_HARDWARE"

    # ============ Compliance and Monitoring Methods ============

    def log_compliance_violation(self, violation_type: str, details: str = ""):
        """تسجيل مخالفة الامتثال"""
        self.violation_count = (self.violation_count or 0) + 1
        self.last_violation_date = now()
        self.violation_details = f"{violation_type}: {details}"

        # تسجيل في سجل الامتثال
        compliance_entry = f"[{now()}] VIOLATION: {violation_type}"
        if details:
            compliance_entry += f" - {details}"
        
        self.append_to_log("compliance_log", compliance_entry)

        # تطبيق إجراءات الإنفاذ
        self.apply_enforcement_actions()

        # إرسال تنبيه
        self.send_notification("Compliance Violation", 
                             f"Violation detected: {violation_type}")

    def apply_enforcement_actions(self):
        """تطبيق إجراءات الإنفاذ عند المخالفة"""
        if self.enforcement_level == "Warning / تحذير":
            # تحذير فقط، لا إجراءات
            pass
        elif self.enforcement_level == "Restricted / مقيد":
            # تقييد بعض الميزات
            self.restrict_features()
        elif self.enforcement_level == "Blocked / محظور":
            # حظر النظام
            self.block_system()

    def restrict_features(self):
        """تقييد الميزات عند المخالفة"""
        # تعطيل الميزات المتقدمة
        self.api_access = 0
        self.mobile_app_access = 0
        self.custom_reports = 0
        
        self.log_activity("Features restricted due to compliance violation")

    def block_system(self):
        """حظر النظام عند المخالفة الجسيمة"""
        self.license_status = "Suspended / معلق"
        self.log_activity("System blocked due to serious compliance violation")

    # ============ Security Methods ============

    def update_security_info(self):
        """تحديث معلومات الأمان"""
        try:
            # إنشاء رمز التوقيع
            signature_data = f"{self.license_code}|{self.hardware_fingerprint}|{self.business_name}"
            self.signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

            # التحقق من اكتشاف التلاعب
            if self.tamper_detection:
                self.check_for_tampering()

        except Exception as e:
            self.log_error(f"Security update error: {str(e)}")

    def check_for_tampering(self):
        """التحقق من التلاعب بالنظام"""
        try:
            # فحص ملفات النظام المهمة
            critical_files = [
                "apps/universal_workshop/universal_workshop/hooks.py",
                "apps/universal_workshop/universal_workshop/config/desktop.py",
            ]

            tampering_detected = False
            for file_path in critical_files:
                if not self.verify_file_integrity(file_path):
                    tampering_detected = True
                    break

            if tampering_detected:
                self.log_compliance_violation("System tampering detected")
                self.append_to_log("security_log", f"[{now()}] TAMPERING: Critical file modification detected")

        except Exception as e:
            self.log_error(f"Tampering check error: {str(e)}")

    def verify_file_integrity(self, file_path: str) -> bool:
        """التحقق من سلامة الملف"""
        try:
            import os
            if os.path.exists(file_path):
                # يمكن إضافة فحص checksum هنا
                return True
            return False
        except Exception:
            return False

    # ============ Notification Methods ============

    def send_notification(self, subject: str, message: str, priority: str = "Medium"):
        """إرسال إشعار"""
        try:
            if not self.email_notifications and not self.sms_notifications:
                return

            # تسجيل الإشعار
            notification_entry = f"[{now()}] {priority}: {subject} - {message}"
            self.append_to_log("notification_log", notification_entry)
            self.last_notification = now()

            # إرسال بريد إلكتروني
            if self.email_notifications and self.admin_email:
                self.send_email_notification(subject, message)

        except Exception as e:
            self.log_error(f"Notification error: {str(e)}")

    def send_email_notification(self, subject: str, message: str):
        """إرسال إشعار بالبريد الإلكتروني"""
        try:
            recipients = [self.admin_email]
            if self.alert_recipients:
                recipients.extend([email.strip() for email in self.alert_recipients.split(",")])

            frappe.sendmail(
                recipients=recipients,
                subject=f"[Universal Workshop ERP] {subject}",
                message=f"""
                <div dir="auto">
                    <h3>{subject}</h3>
                    <p>{message}</p>
                    <hr>
                    <p><strong>License Code:</strong> {self.license_code}</p>
                    <p><strong>Business:</strong> {self.business_name} ({self.business_name_ar})</p>
                    <p><strong>Time:</strong> {now()}</p>
                </div>
                """,
            )

        except Exception as e:
            self.log_error(f"Email notification error: {str(e)}")

    # ============ Registration and Server Communication ============

    def register_with_server(self):
        """تسجيل الترخيص مع الخادم"""
        try:
            registration_data = {
                "license_code": self.license_code,
                "business_name": self.business_name,
                "business_name_ar": self.business_name_ar,
                "license_owner": self.license_owner,
                "hardware_fingerprint": self.hardware_fingerprint,
                "server_hostname": self.server_hostname,
                "ip_address": self.ip_address,
                "os_platform": self.os_platform,
                "product_version": self.product_version,
            }

            response = requests.post(
                "https://license.universal-workshop.com/api/register",
                json=registration_data,
                timeout=15,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.log_activity("Successfully registered with license server")
                    return True
                else:
                    self.log_error(f"Server registration failed: {result.get('error')}")
            else:
                self.log_error(f"Server registration failed: HTTP {response.status_code}")

        except Exception as e:
            self.log_error(f"Registration error: {str(e)}")

        return False

    def send_activation_notification(self):
        """إرسال إشعار عند إنشاء ترخيص جديد"""
        try:
            subject = "New License Created"
            message = f"""
            A new license has been created for {self.business_name}.
            License Code: {self.license_code}
            License Type: {self.license_type}
            Please activate the license using the provided activation code.
            """
            self.send_notification(subject, message, "High")
        except Exception as e:
            self.log_error(f"Activation notification error: {str(e)}")

    # ============ Utility Methods ============

    def append_to_log(self, log_field: str, entry: str):
        """إضافة إدخال إلى السجل"""
        try:
            current_log = getattr(self, log_field, "") or ""
            new_log = f"{current_log}\n{entry}" if current_log else entry
            
            # الاحتفاظ بآخر 1000 سطر فقط لتجنب نمو السجل بشكل مفرط
            lines = new_log.split("\n")
            if len(lines) > 1000:
                lines = lines[-1000:]
                new_log = "\n".join(lines)
            
            setattr(self, log_field, new_log)
        except Exception as e:
            frappe.log_error(f"Error appending to log {log_field}: {str(e)}")

    def log_activity(self, activity: str):
        """تسجيل نشاط"""
        self.append_to_log("activity_log", f"[{now()}] {activity}")

    def log_error(self, error: str):
        """تسجيل خطأ"""
        self.append_to_log("error_log", f"[{now()}] ERROR: {error}")
        frappe.log_error(error, "License Manager")

    @frappe.whitelist()
    def reset_license(self):
        """إعادة تعيين الترخيص"""
        try:
            if frappe.session.user != "Administrator":
                frappe.throw(_("Only Administrator can reset license"))

            self.activation_status = "Not Activated / غير مفعل"
            self.activation_date = None
            self.activated_by = None
            self.activation_attempts = 0
            self.activation_locked = 0
            self.violation_count = 0
            self.grace_period_used = 0
            self.license_status = "Pending / في الانتظار"

            self.log_activity("License reset by Administrator")
            self.save()

            return {"status": "success", "message": _("License reset successfully")}

        except Exception as e:
            self.log_error(f"License reset error: {str(e)}")
            frappe.throw(_("License reset failed: {0}").format(str(e)))

# ============ Global License Management Functions ============

@frappe.whitelist()
def get_active_license() -> Optional[str]:
    """الحصول على الترخيص النشط"""
    try:
        active_licenses = frappe.get_list(
            "License Manager",
            filters={"license_status": "Active / نشط", "activation_status": "Activated / مفعل"},
            fields=["name"],
            limit=1,
        )
        return active_licenses[0].name if active_licenses else None
    except Exception:
        return None

@frappe.whitelist()
def validate_current_license() -> Dict[str, Any]:
    """التحقق من الترخيص الحالي"""
    try:
        license_name = get_active_license()
        if not license_name:
            return {"valid": False, "error": "No active license found"}

        license_doc = frappe.get_doc("License Manager", license_name)
        return license_doc.validate_license()

    except Exception as e:
        return {"valid": False, "error": str(e)}
