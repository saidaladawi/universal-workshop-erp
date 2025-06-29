"""
Integration Manager DocType Controller for Universal Workshop ERP
Comprehensive third-party integration management with Arabic RTL support
"""

import hashlib
import hmac
import json
import re
import socket
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import frappe
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_to_date,
    cint,
    flt,
    get_datetime,
    now,
    now_datetime,
    today,
)


class IntegrationManager(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate integration configuration before saving"""
        self.validate_integration_name()
        self.validate_urls()
        self.validate_authentication()
        self.validate_webhook_configuration()
        self.validate_rate_limits()
        self.validate_notification_settings()
        self.validate_security_settings()

    def before_save(self):
        """Process data before saving"""
        self.set_default_values()
        self.update_metadata()
        self.log_activity("Integration configuration updated")

    def after_insert(self):
        """After integration creation"""
        self.setup_monitoring()
        self.send_creation_notification()
        self.log_activity("New integration created and configured")

    # ============ Validation Methods ============

    def validate_integration_name(self):
        """التحقق من اسم التكامل"""
        if not self.integration_name:
            frappe.throw(_("Integration name is required"))
        
        if not self.integration_name_ar:
            frappe.throw(_("Arabic integration name is required"))

        # التحقق من التفرد
        existing = frappe.db.exists("Integration Manager", {
            "integration_name": self.integration_name,
            "name": ["!=", self.name or ""]
        })
        if existing:
            frappe.throw(_("Integration name must be unique"))

    def validate_urls(self):
        """التحقق من صحة الروابط"""
        urls_to_validate = [
            ("base_url", self.base_url),
            ("provider_url", self.provider_url),
            ("webhook_url", self.webhook_url),
            ("health_check_url", self.health_check_url),
            ("slack_webhook_url", self.slack_webhook_url),
        ]

        for field_name, url in urls_to_validate:
            if url and not self.is_valid_url(url):
                frappe.throw(_("Invalid URL format in field: {0}").format(field_name))

    def is_valid_url(self, url: str) -> bool:
        """التحقق من صحة الرابط"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate_authentication(self):
        """التحقق من إعدادات المصادقة"""
        if not self.authentication_type:
            return

        auth_requirements = {
            "API Key / مفتاح API": ["api_key"],
            "Bearer Token / رمز الحامل": ["access_token"],
            "Basic Auth / المصادقة الأساسية": ["username", "password"],
            "OAuth 2.0 / OAuth 2.0": ["client_id", "client_secret"],
            "JWT / JWT": ["access_token"],
        }

        required_fields = auth_requirements.get(self.authentication_type, [])
        for field in required_fields:
            if not getattr(self, field, None):
                frappe.throw(_("Field {0} is required for authentication type {1}")
                           .format(field, self.authentication_type))

    def validate_webhook_configuration(self):
        """التحقق من إعدادات Webhook"""
        if not self.webhook_enabled:
            return

        if not self.webhook_url:
            frappe.throw(_("Webhook URL is required when webhooks are enabled"))

        if not self.webhook_method:
            self.webhook_method = "POST"

        # التحقق من قالب المحتوى
        if self.webhook_payload_template:
            try:
                json.loads(self.webhook_payload_template)
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in webhook payload template"))

        # التحقق من الرؤوس المخصصة
        if self.webhook_headers:
            try:
                json.loads(self.webhook_headers)
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in webhook headers"))

    def validate_rate_limits(self):
        """التحقق من حدود المعدل"""
        if self.rate_limit_requests and self.rate_limit_requests <= 0:
            frappe.throw(_("Rate limit requests must be greater than 0"))

    def validate_notification_settings(self):
        """التحقق من إعدادات الإشعارات"""
        if self.email_notifications and not self.notification_emails:
            frappe.throw(_("Notification emails are required when email notifications are enabled"))

        if self.sms_notifications and not self.notification_phones:
            frappe.throw(_("Notification phones are required when SMS notifications are enabled"))

        if self.slack_notifications and not self.slack_webhook_url:
            frappe.throw(_("Slack webhook URL is required when Slack notifications are enabled"))

    def validate_security_settings(self):
        """التحقق من إعدادات الأمان"""
        if self.ip_whitelist:
            ip_list = [ip.strip() for ip in self.ip_whitelist.split(",")]
            for ip in ip_list:
                if not self.is_valid_ip(ip):
                    frappe.throw(_("Invalid IP address in whitelist: {0}").format(ip))

    def is_valid_ip(self, ip: str) -> bool:
        """التحقق من صحة عنوان IP"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    # ============ Setup and Configuration Methods ============

    def set_default_values(self):
        """تعيين القيم الافتراضية"""
        if not self.integration_status:
            self.integration_status = "Inactive / غير نشط"

        if not self.priority_level:
            self.priority_level = "Medium / متوسط"

        if not self.request_timeout:
            self.request_timeout = 30

        if not self.webhook_retry_attempts:
            self.webhook_retry_attempts = 3

        if not self.webhook_retry_delay:
            self.webhook_retry_delay = 5

        if not self.health_check_timeout:
            self.health_check_timeout = 10

        if not self.alert_threshold:
            self.alert_threshold = 3

    def update_metadata(self):
        """تحديث البيانات الوصفية"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_on:
            self.created_on = now()

        self.modified_by = frappe.session.user
        self.modified_on = now()

    def setup_monitoring(self):
        """إعداد المراقبة"""
        if self.monitoring_enabled:
            self.schedule_health_checks()
            self.initialize_counters()

    def initialize_counters(self):
        """تهيئة العدادات"""
        self.success_count = 0
        self.failure_count = 0
        self.usage_count = 0
        self.average_response_time = 0.0

    # ============ API Request Methods ============

    @frappe.whitelist()
    def test_connection(self) -> Dict[str, Any]:
        """اختبار الاتصال مع التكامل"""
        try:
            if not self.base_url:
                return {"success": False, "error": "Base URL not configured"}

            start_time = time.time()
            response = self.make_api_request("GET", "/", timeout=self.health_check_timeout)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                self.update_success_metrics(response_time)
                self.log_activity(f"Connection test successful - {response_time:.2f}ms")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "message": "Connection test successful"
                }
            else:
                self.update_failure_metrics(f"HTTP {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            self.update_failure_metrics(str(e))
            self.log_error(f"Connection test failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def make_api_request(self, method: str, endpoint: str, data: Dict = None, 
                        timeout: int = None) -> requests.Response:
        """إجراء طلب API"""
        if not timeout:
            timeout = self.request_timeout

        url = f"{self.base_url.rstrip('/')}{endpoint}"
        headers = self.get_request_headers()

        # إضافة البيانات
        kwargs = {
            "headers": headers,
            "timeout": timeout,
            "verify": self.ssl_verification,
        }

        if data:
            if method.upper() in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = data
            else:
                kwargs["params"] = data

        # إضافة المصادقة
        auth = self.get_authentication()
        if auth:
            kwargs.update(auth)

        # تسجيل الطلب
        self.log_request(method, url, data)

        # إجراء الطلب
        response = requests.request(method, url, **kwargs)

        # تسجيل الاستجابة
        self.log_response(response)

        return response

    def get_request_headers(self) -> Dict[str, str]:
        """الحصول على رؤوس الطلب"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Universal Workshop ERP Integration Manager",
        }

        # إضافة الرؤوس المخصصة
        if self.custom_headers:
            try:
                custom = json.loads(self.custom_headers)
                headers.update(custom)
            except json.JSONDecodeError:
                pass

        return headers

    def get_authentication(self) -> Dict[str, Any]:
        """الحصول على إعدادات المصادقة"""
        if self.authentication_type == "API Key / مفتاح API":
            return {"headers": {"X-API-Key": self.api_key}}
        
        elif self.authentication_type == "Bearer Token / رمز الحامل":
            return {"headers": {"Authorization": f"Bearer {self.access_token}"}}
        
        elif self.authentication_type == "Basic Auth / المصادقة الأساسية":
            return {"auth": (self.username, self.password)}
        
        elif self.authentication_type == "JWT / JWT":
            return {"headers": {"Authorization": f"JWT {self.access_token}"}}

        return {}

    # ============ Webhook Methods ============

    @frappe.whitelist()
    def send_webhook(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """إرسال webhook"""
        if not self.webhook_enabled or not self.webhook_url:
            return {"success": False, "error": "Webhooks not configured"}

        try:
            payload = self.build_webhook_payload(event, data)
            headers = self.get_webhook_headers()

            response = requests.request(
                self.webhook_method,
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=self.request_timeout,
                verify=self.ssl_verification,
            )

            if response.status_code in [200, 201, 202]:
                self.log_webhook_success(event, payload, response)
                return {"success": True, "status_code": response.status_code}
            else:
                self.log_webhook_failure(event, payload, response)
                return {"success": False, "status_code": response.status_code}

        except Exception as e:
            self.log_webhook_error(event, str(e))
            return {"success": False, "error": str(e)}

    def build_webhook_payload(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """بناء محتوى webhook"""
        if self.webhook_payload_template:
            try:
                template = json.loads(self.webhook_payload_template)
                # يمكن إضافة منطق التخصيص هنا
                template.update({
                    "event": event,
                    "data": data,
                    "timestamp": now(),
                    "integration": self.integration_name,
                })
                return template
            except json.JSONDecodeError:
                pass

        # القالب الافتراضي
        return {
            "event": event,
            "data": data,
            "timestamp": now(),
            "integration": self.integration_name,
            "webhook_id": self.name,
        }

    def get_webhook_headers(self) -> Dict[str, str]:
        """الحصول على رؤوس webhook"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Universal Workshop ERP Webhook",
        }

        # إضافة التوقيع
        if self.webhook_secret:
            headers["X-Hub-Signature"] = self.generate_webhook_signature()

        # إضافة الرؤوس المخصصة
        if self.webhook_headers:
            try:
                custom = json.loads(self.webhook_headers)
                headers.update(custom)
            except json.JSONDecodeError:
                pass

        return headers

    def generate_webhook_signature(self, payload: str = "") -> str:
        """إنشاء توقيع webhook"""
        if not self.webhook_secret:
            return ""

        signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    # ============ Monitoring and Health Check Methods ============

    @frappe.whitelist()
    def run_health_check(self) -> Dict[str, Any]:
        """إجراء فحص الحالة الصحية"""
        if not self.monitoring_enabled:
            return {"success": False, "error": "Monitoring not enabled"}

        try:
            health_url = self.health_check_url or self.base_url
            if not health_url:
                return {"success": False, "error": "No health check URL configured"}

            start_time = time.time()
            response = requests.get(
                health_url,
                timeout=self.health_check_timeout,
                verify=self.ssl_verification,
            )
            response_time = (time.time() - start_time) * 1000

            self.last_health_check = now()

            if response.status_code == 200:
                self.update_success_metrics(response_time)
                self.log_activity(f"Health check passed - {response_time:.2f}ms")
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": response_time,
                    "status_code": response.status_code,
                }
            else:
                self.update_failure_metrics(f"Health check failed: HTTP {response.status_code}")
                self.check_alert_threshold()
                return {
                    "success": False,
                    "status": "unhealthy",
                    "status_code": response.status_code,
                }

        except Exception as e:
            self.update_failure_metrics(f"Health check error: {str(e)}")
            self.check_alert_threshold()
            self.log_error(f"Health check failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def schedule_health_checks(self):
        """جدولة فحوصات الحالة الصحية"""
        # يمكن إضافة منطق الجدولة هنا
        # باستخدام Frappe scheduler أو cron jobs
        pass

    def update_success_metrics(self, response_time: float):
        """تحديث مقاييس النجاح"""
        self.success_count = (self.success_count or 0) + 1
        self.last_used = now()

        # تحديث متوسط وقت الاستجابة
        if self.average_response_time:
            self.average_response_time = (
                (self.average_response_time + response_time) / 2
            )
        else:
            self.average_response_time = response_time

        # مسح رسائل الخطأ عند النجاح
        if self.last_error_message:
            self.last_error_message = ""
            self.last_error_time = None

    def update_failure_metrics(self, error_message: str):
        """تحديث مقاييس الفشل"""
        self.failure_count = (self.failure_count or 0) + 1
        self.last_error_message = error_message
        self.last_error_time = now()

    def check_alert_threshold(self):
        """فحص عتبة التنبيه"""
        if not self.alert_on_failure or not self.alert_threshold:
            return

        recent_failures = self.get_recent_failure_count()
        if recent_failures >= self.alert_threshold:
            self.send_failure_alert(recent_failures)

    def get_recent_failure_count(self) -> int:
        """الحصول على عدد الإخفاقات الأخيرة"""
        # يمكن تحسين هذا ليفحص الإخفاقات المتتالية الأخيرة
        return self.failure_count or 0

    # ============ Notification Methods ============

    def send_failure_alert(self, failure_count: int):
        """إرسال تنبيه الفشل"""
        subject = f"Integration Alert: {self.integration_name}"
        message = f"""
        Integration "{self.integration_name}" has failed {failure_count} times.
        
        Last Error: {self.last_error_message}
        Error Time: {self.last_error_time}
        
        Please check the integration configuration and connectivity.
        """

        self.send_notification(subject, message, "Critical")

    def send_creation_notification(self):
        """إرسال إشعار الإنشاء"""
        subject = f"New Integration Created: {self.integration_name}"
        message = f"""
        A new integration has been created:
        
        Name: {self.integration_name} ({self.integration_name_ar})
        Type: {self.integration_type}
        Status: {self.integration_status}
        Provider: {self.provider_name}
        """

        self.send_notification(subject, message, "Info")

    def send_notification(self, subject: str, message: str, priority: str = "Medium"):
        """إرسال إشعار"""
        try:
            # تسجيل الإشعار
            self.log_activity(f"Notification sent: {subject}")

            # إرسال بريد إلكتروني
            if self.email_notifications and self.notification_emails:
                self.send_email_notification(subject, message)

            # إرسال إشعار Slack
            if self.slack_notifications and self.slack_webhook_url:
                self.send_slack_notification(subject, message)

        except Exception as e:
            self.log_error(f"Notification error: {str(e)}")

    def send_email_notification(self, subject: str, message: str):
        """إرسال إشعار بالبريد الإلكتروني"""
        try:
            recipients = [email.strip() for email in self.notification_emails.split(",")]

            frappe.sendmail(
                recipients=recipients,
                subject=f"[Universal Workshop ERP] {subject}",
                message=f"""
                <div dir="auto">
                    <h3>{subject}</h3>
                    <p>{message}</p>
                    <hr>
                    <p><strong>Integration:</strong> {self.integration_name}</p>
                    <p><strong>Type:</strong> {self.integration_type}</p>
                    <p><strong>Time:</strong> {now()}</p>
                </div>
                """,
            )

        except Exception as e:
            self.log_error(f"Email notification error: {str(e)}")

    def send_slack_notification(self, subject: str, message: str):
        """إرسال إشعار Slack"""
        try:
            payload = {
                "text": f"*{subject}*",
                "attachments": [
                    {
                        "color": "warning" if "Error" in subject else "good",
                        "fields": [
                            {"title": "Integration", "value": self.integration_name, "short": True},
                            {"title": "Type", "value": self.integration_type, "short": True},
                            {"title": "Message", "value": message, "short": False},
                        ],
                        "ts": int(time.time()),
                    }
                ],
            }

            requests.post(self.slack_webhook_url, json=payload, timeout=10)

        except Exception as e:
            self.log_error(f"Slack notification error: {str(e)}")

    # ============ Data Synchronization Methods ============

    @frappe.whitelist()
    def sync_data(self, direction: str = None) -> Dict[str, Any]:
        """مزامنة البيانات"""
        if not direction:
            direction = self.sync_direction

        if not direction:
            return {"success": False, "error": "Sync direction not configured"}

        try:
            if direction == "Inbound Only / وارد فقط":
                result = self.sync_inbound_data()
            elif direction == "Outbound Only / صادر فقط":
                result = self.sync_outbound_data()
            elif direction == "Bidirectional / ثنائي الاتجاه":
                inbound_result = self.sync_inbound_data()
                outbound_result = self.sync_outbound_data()
                result = {
                    "success": inbound_result["success"] and outbound_result["success"],
                    "inbound": inbound_result,
                    "outbound": outbound_result,
                }

            self.last_sync = now()
            self.log_activity(f"Data sync completed: {direction}")
            return result

        except Exception as e:
            self.log_error(f"Data sync error: {str(e)}")
            return {"success": False, "error": str(e)}

    def sync_inbound_data(self) -> Dict[str, Any]:
        """مزامنة البيانات الواردة"""
        # يمكن تخصيص هذا حسب نوع التكامل
        return {"success": True, "records_processed": 0}

    def sync_outbound_data(self) -> Dict[str, Any]:
        """مزامنة البيانات الصادرة"""
        # يمكن تخصيص هذا حسب نوع التكامل
        return {"success": True, "records_processed": 0}

    # ============ Logging Methods ============

    def log_request(self, method: str, url: str, data: Dict = None):
        """تسجيل الطلب"""
        entry = f"[{now()}] {method} {url}"
        if data:
            entry += f" - Data: {json.dumps(data, ensure_ascii=False)[:200]}..."
        self.append_to_log("request_log", entry)

    def log_response(self, response: requests.Response):
        """تسجيل الاستجابة"""
        entry = f"[{now()}] Response: {response.status_code}"
        try:
            content = response.text[:200] + "..." if len(response.text) > 200 else response.text
            entry += f" - Content: {content}"
        except Exception:
            entry += " - Content: [Binary or non-text response]"
        
        self.append_to_log("response_log", entry)

    def log_webhook_success(self, event: str, payload: Dict, response: requests.Response):
        """تسجيل نجاح webhook"""
        entry = f"[{now()}] Webhook SUCCESS - Event: {event}, Status: {response.status_code}"
        self.append_to_log("activity_log", entry)

    def log_webhook_failure(self, event: str, payload: Dict, response: requests.Response):
        """تسجيل فشل webhook"""
        entry = f"[{now()}] Webhook FAILED - Event: {event}, Status: {response.status_code}"
        self.append_to_log("error_log", entry)

    def log_webhook_error(self, event: str, error: str):
        """تسجيل خطأ webhook"""
        entry = f"[{now()}] Webhook ERROR - Event: {event}, Error: {error}"
        self.append_to_log("error_log", entry)

    def append_to_log(self, log_field: str, entry: str):
        """إضافة إدخال إلى السجل"""
        try:
            current_log = getattr(self, log_field, "") or ""
            new_log = f"{current_log}\n{entry}" if current_log else entry
            
            # الاحتفاظ بآخر 1000 سطر فقط
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
        frappe.log_error(error, "Integration Manager")

    # ============ Utility Methods ============

    @frappe.whitelist()
    def get_integration_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التكامل"""
        return {
            "success_count": self.success_count or 0,
            "failure_count": self.failure_count or 0,
            "usage_count": self.usage_count or 0,
            "average_response_time": self.average_response_time or 0,
            "last_used": self.last_used,
            "last_health_check": self.last_health_check,
            "last_error": self.last_error_message,
            "success_rate": self.calculate_success_rate(),
        }

    def calculate_success_rate(self) -> float:
        """حساب معدل النجاح"""
        total = (self.success_count or 0) + (self.failure_count or 0)
        if total == 0:
            return 0.0
        return round((self.success_count or 0) / total * 100, 2)

    @frappe.whitelist()
    def reset_statistics(self):
        """إعادة تعيين الإحصائيات"""
        self.success_count = 0
        self.failure_count = 0
        self.usage_count = 0
        self.average_response_time = 0.0
        self.last_error_message = ""
        self.last_error_time = None
        
        self.log_activity("Statistics reset")
        self.save()

# ============ Global Integration Management Functions ============

@frappe.whitelist()
def get_active_integrations() -> List[Dict[str, Any]]:
    """الحصول على التكاملات النشطة"""
    return frappe.get_list(
        "Integration Manager",
        filters={"integration_status": "Active / نشط"},
        fields=["name", "integration_name", "integration_type", "provider_name"],
        order_by="integration_name",
    )

@frappe.whitelist()
def run_all_health_checks() -> Dict[str, Any]:
    """تشغيل فحوصات الحالة لجميع التكاملات"""
    integrations = frappe.get_list(
        "Integration Manager",
        filters={"integration_status": "Active / نشط", "monitoring_enabled": 1},
        fields=["name"],
    )

    results = []
    for integration in integrations:
        doc = frappe.get_doc("Integration Manager", integration.name)
        result = doc.run_health_check()
        results.append({
            "integration": integration.name,
            "result": result,
        })

    return {"total": len(results), "results": results}

@frappe.whitelist()
def get_integration_dashboard_data() -> Dict[str, Any]:
    """الحصول على بيانات لوحة التحكم"""
    total_integrations = frappe.db.count("Integration Manager")
    active_integrations = frappe.db.count("Integration Manager", 
                                         {"integration_status": "Active / نشط"})
    
    recent_errors = frappe.get_list(
        "Integration Manager",
        filters={"last_error_time": [">=", add_to_date(now(), days=-1)]},
        fields=["name", "integration_name", "last_error_message"],
        limit=10,
    )

    return {
        "total_integrations": total_integrations,
        "active_integrations": active_integrations,
        "inactive_integrations": total_integrations - active_integrations,
        "recent_errors": recent_errors,
        "health_check_summary": run_all_health_checks(),
    }
