"""
Error Logger DocType Controller for Universal Workshop ERP
Comprehensive error logging, reporting, and notification system with Arabic RTL support
"""

import hashlib
import json
import re
import socket
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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


class ErrorLogger(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate error log entry before saving"""
        self.validate_required_fields()
        self.validate_severity_priority_consistency()
        self.validate_resolution_fields()
        self.validate_notification_settings()
        self.calculate_resolution_time()
        self.check_for_duplicates()

    def before_save(self):
        """Process data before saving"""
        self.set_default_values()
        self.generate_hash_signature()
        self.update_occurrence_count()
        self.extract_system_information()
        self.categorize_error_automatically()
        self.update_metadata()

    def after_insert(self):
        """After error log creation"""
        self.send_notifications()
        self.check_escalation_rules()
        self.update_error_trends()
        self.log_system_activity("New error logged in system")

    def on_update(self):
        """After error log update"""
        if self.has_value_changed("error_status"):
            self.handle_status_change()
        if self.has_value_changed("severity_level"):
            self.handle_severity_change()

    # ============ Validation Methods ============

    def validate_required_fields(self):
        """التحقق من الحقول المطلوبة"""
        if not self.error_title:
            frappe.throw(_("Error title is required"))

        if not self.error_category:
            frappe.throw(_("Error category is required"))

        if not self.severity_level:
            frappe.throw(_("Severity level is required"))

        # تحديد حقول مطلوبة حسب فئة الخطأ
        if self.error_category == "API Error / خطأ واجهة برمجة التطبيقات":
            if not self.request_url:
                frappe.throw(_("Request URL is required for API errors"))

    def validate_severity_priority_consistency(self):
        """التحقق من تناسق الخطورة والأولوية"""
        severity_priority_map = {
            "Critical / حرج": ["Immediate / فوري", "Urgent / عاجل"],
            "High / عالي": ["Urgent / عاجل", "High / عالي"],
            "Medium / متوسط": ["Medium / متوسط", "High / عالي"],
            "Low / منخفض": ["Low / منخفض", "Medium / متوسط"],
            "Info / معلوماتي": ["Low / منخفض", "Backlog / قائمة الانتظار"],
        }

        if self.resolution_priority:
            valid_priorities = severity_priority_map.get(self.severity_level, [])
            if valid_priorities and self.resolution_priority not in valid_priorities:
                frappe.msgprint(
                    _(
                        "Warning: Resolution priority '{0}' may not be appropriate for severity level '{1}'"
                    ).format(self.resolution_priority, self.severity_level),
                    alert=True,
                )

    def validate_resolution_fields(self):
        """التحقق من حقول الحل"""
        if self.resolution_status == "Resolved / محلول":
            if not self.resolution_date:
                self.resolution_date = now()
            if not self.resolved_by:
                self.resolved_by = frappe.session.user
            if not self.resolution_notes:
                frappe.throw(_("Resolution notes are required when marking error as resolved"))

    def validate_notification_settings(self):
        """التحقق من إعدادات الإشعارات"""
        if self.notification_channels:
            if (
                "Email / البريد الإلكتروني" in self.notification_channels
                and not self.email_recipients
            ):
                frappe.throw(_("Email recipients required for email notifications"))
            if "SMS / رسائل نصية" in self.notification_channels and not self.sms_recipients:
                frappe.throw(_("SMS recipients required for SMS notifications"))
            if "Slack / سلاك" in self.notification_channels and not self.slack_channel:
                frappe.throw(_("Slack channel required for Slack notifications"))

    def calculate_resolution_time(self):
        """حساب وقت الحل"""
        if self.resolution_date and self.first_occurrence:
            resolution_datetime = get_datetime(self.resolution_date)
            occurrence_datetime = get_datetime(self.first_occurrence)
            diff = resolution_datetime - occurrence_datetime
            self.resolution_time_minutes = int(diff.total_seconds() / 60)

    def check_for_duplicates(self):
        """فحص الأخطاء المكررة"""
        if self.error_message and self.function_name:
            duplicate_hash = self.generate_duplicate_hash()
            existing = frappe.db.get_list(
                "Error Logger",
                filters={"duplicate_hash": duplicate_hash, "name": ["!=", self.name or ""]},
                fields=["name", "occurrence_count"],
                limit=1,
            )

            if existing:
                self.duplicate_hash = duplicate_hash
                self.related_errors = f"Duplicate of: {existing[0]['name']}"
                self.similar_errors_count = existing[0]["occurrence_count"] + 1

    # ============ Setup and Default Values ============

    def set_default_values(self):
        """تعيين القيم الافتراضية"""
        if not self.error_status:
            self.error_status = "New / جديد"

        if not self.created_by_system:
            self.created_by_system = frappe.session.user

        if not self.created_date:
            self.created_date = now()

        if not self.first_occurrence:
            self.first_occurrence = now()

        self.last_occurrence = now()

        if not self.occurrence_count:
            self.occurrence_count = 1

        # تعيين الأولوية الافتراضية حسب الخطورة
        if not self.resolution_priority:
            priority_defaults = {
                "Critical / حرج": "Immediate / فوري",
                "High / عالي": "Urgent / عاجل",
                "Medium / متوسط": "Medium / متوسط",
                "Low / منخفض": "Low / منخفض",
                "Info / معلوماتي": "Backlog / قائمة الانتظار",
            }
            self.resolution_priority = priority_defaults.get(self.severity_level, "Medium / متوسط")

    def generate_hash_signature(self):
        """إنشاء توقيع تجزئة للخطأ"""
        signature_data = {
            "error_title": self.error_title,
            "error_category": self.error_category,
            "file_path": self.file_path,
            "function_name": self.function_name,
            "line_number": self.line_number,
        }

        signature_string = json.dumps(signature_data, sort_keys=True, ensure_ascii=False)
        self.hash_signature = hashlib.sha256(signature_string.encode()).hexdigest()[:16]

    def generate_duplicate_hash(self) -> str:
        """إنشاء تجزئة للكشف عن المكررات"""
        duplicate_data = {
            "error_message": self.error_message[:100] if self.error_message else "",
            "function_name": self.function_name,
            "line_number": self.line_number,
            "file_path": self.file_path,
        }

        duplicate_string = json.dumps(duplicate_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(duplicate_string.encode(), usedforsecurity=False).hexdigest()[:12]

    def update_occurrence_count(self):
        """تحديث عدد مرات الحدوث"""
        if self.duplicate_hash:
            # البحث عن أخطاء مشابهة
            similar_errors = frappe.db.count(
                "Error Logger", filters={"duplicate_hash": self.duplicate_hash}
            )
            self.occurrence_count = similar_errors + 1

    def extract_system_information(self):
        """استخراج معلومات النظام"""
        if not self.frappe_version:
            self.frappe_version = frappe.__version__

        if not self.python_version:
            self.python_version = (
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            )

        if not self.server_name:
            try:
                self.server_name = socket.gethostname()
            except Exception:
                self.server_name = "Unknown"

        if not self.database_name:
            self.database_name = frappe.conf.db_name

        if not self.app_version:
            try:
                from universal_workshop import __version__

                self.app_version = __version__
            except ImportError:
                self.app_version = "Unknown"

    def categorize_error_automatically(self):
        """تصنيف الخطأ تلقائياً"""
        if not self.error_category and self.error_message:
            error_message_lower = self.error_message.lower()

            # تصنيف تلقائي بناءً على رسالة الخطأ
            if any(
                word in error_message_lower
                for word in ["permission", "access", "unauthorized", "forbidden"]
            ):
                self.error_category = "Permission Error / خطأ الصلاحية"
            elif any(
                word in error_message_lower for word in ["database", "sql", "mysql", "mariadb"]
            ):
                self.error_category = "Database Error / خطأ قاعدة البيانات"
            elif any(
                word in error_message_lower for word in ["api", "request", "response", "http"]
            ):
                self.error_category = "API Error / خطأ واجهة برمجة التطبيقات"
            elif any(word in error_message_lower for word in ["validation", "invalid", "required"]):
                self.error_category = "Validation Error / خطأ التحقق"
            elif any(word in error_message_lower for word in ["network", "connection", "timeout"]):
                self.error_category = "Network Error / خطأ الشبكة"
            else:
                self.error_category = "System Error / خطأ النظام"

    def update_metadata(self):
        """تحديث البيانات الوصفية"""
        self.modified_by_system = frappe.session.user
        self.modified_date = now()

        if not self.version_number:
            self.version_number = 1
        else:
            self.version_number += 1

    # ============ Status and Lifecycle Management ============

    def handle_status_change(self):
        """التعامل مع تغيير الحالة"""
        old_status = self.get_doc_before_save().error_status if self.get_doc_before_save() else None
        new_status = self.error_status

        self.log_activity(f"Status changed from '{old_status}' to '{new_status}'")

        # إجراءات خاصة حسب الحالة الجديدة
        if new_status == "Resolved / محلول":
            self.handle_resolution()
        elif new_status == "Closed / مغلق":
            self.handle_closure()
        elif new_status == "Reopened / أعيد فتحه":
            self.handle_reopening()

    def handle_severity_change(self):
        """التعامل مع تغيير مستوى الخطورة"""
        old_severity = (
            self.get_doc_before_save().severity_level if self.get_doc_before_save() else None
        )
        new_severity = self.severity_level

        self.log_activity(f"Severity changed from '{old_severity}' to '{new_severity}'")

        # إعادة تقييم الأولوية والتصعيد
        if new_severity in ["Critical / حرج", "High / عالي"]:
            self.check_escalation_rules()
            self.send_severity_change_notification()

    def handle_resolution(self):
        """التعامل مع حل الخطأ"""
        if not self.resolution_date:
            self.resolution_date = now()
        if not self.resolved_by:
            self.resolved_by = frappe.session.user

        self.log_activity("Error marked as resolved")
        self.send_resolution_notification()

    def handle_closure(self):
        """التعامل مع إغلاق الخطأ"""
        self.log_activity("Error closed")
        self.update_error_trends()

    def handle_reopening(self):
        """التعامل مع إعادة فتح الخطأ"""
        self.resolution_date = None
        self.resolved_by = None
        self.occurrence_count = (self.occurrence_count or 1) + 1
        self.last_occurrence = now()

        self.log_activity("Error reopened")
        self.send_reopening_notification()

    # ============ Notification Methods ============

    def send_notifications(self):
        """إرسال الإشعارات"""
        if not self.notification_channels:
            return

        try:
            # تحديد قالب الإشعار
            template = self.get_notification_template()

            # إرسال حسب القنوات المحددة
            if "Email / البريد الإلكتروني" in self.notification_channels:
                self.send_email_notification(template)

            if "SMS / رسائل نصية" in self.notification_channels:
                self.send_sms_notification(template)

            if "Slack / سلاك" in self.notification_channels:
                self.send_slack_notification(template)

            self.notification_sent = True
            self.log_activity("Notifications sent successfully")

        except Exception as e:
            self.log_activity(f"Notification error: {str(e)}")
            frappe.log_error(f"Error sending notifications: {str(e)}", "Error Logger Notifications")

    def get_notification_template(self) -> Dict[str, str]:
        """الحصول على قالب الإشعار"""
        templates = {
            "Critical Error / خطأ حرج": {
                "subject": f"🚨 Critical Error: {self.error_title}",
                "subject_ar": f"🚨 خطأ حرج: {self.error_title_ar or self.error_title}",
                "priority": "critical",
            },
            "High Priority / أولوية عالية": {
                "subject": f"⚠️ High Priority Error: {self.error_title}",
                "subject_ar": f"⚠️ خطأ عالي الأولوية: {self.error_title_ar or self.error_title}",
                "priority": "high",
            },
            "System Down / توقف النظام": {
                "subject": f"🔴 System Down: {self.error_title}",
                "subject_ar": f"🔴 توقف النظام: {self.error_title_ar or self.error_title}",
                "priority": "critical",
            },
            "Security Alert / تنبيه أمني": {
                "subject": f"🔒 Security Alert: {self.error_title}",
                "subject_ar": f"🔒 تنبيه أمني: {self.error_title_ar or self.error_title}",
                "priority": "critical",
            },
        }

        default_template = {
            "subject": f"Error Report: {self.error_title}",
            "subject_ar": f"تقرير خطأ: {self.error_title_ar or self.error_title}",
            "priority": "medium",
        }

        return templates.get(self.notification_template, default_template)

    def send_email_notification(self, template: Dict[str, str]):
        """إرسال إشعار بالبريد الإلكتروني"""
        if not self.email_recipients:
            return

        recipients = [email.strip() for email in self.email_recipients.split(",")]

        # تحديد اللغة المفضلة للمستخدم
        user_language = frappe.db.get_value("User", frappe.session.user, "language") or "en"
        subject = template.get(
            "subject_ar" if user_language == "ar" else "subject", template["subject"]
        )

        message = self.build_email_message(template, user_language)

        frappe.sendmail(
            recipients=recipients,
            subject=f"[Universal Workshop ERP] {subject}",
            message=message,
            delayed=False,
        )

    def build_email_message(self, template: Dict[str, str], language: str = "en") -> str:
        """بناء رسالة البريد الإلكتروني"""
        if language == "ar":
            return f"""
            <div dir="rtl" style="font-family: 'Noto Sans Arabic', Tahoma, Arial; text-align: right;">
                <h2 style="color: #dc3545;">تقرير خطأ في النظام</h2>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3>{self.error_title_ar or self.error_title}</h3>
                    <p><strong>الفئة:</strong> {self.error_category}</p>
                    <p><strong>مستوى الخطورة:</strong> {self.severity_level}</p>
                    <p><strong>الحالة:</strong> {self.error_status}</p>
                    <p><strong>تاريخ الحدوث:</strong> {self.first_occurrence}</p>
                </div>
                
                <div style="margin: 15px 0;">
                    <h4>تفاصيل الخطأ:</h4>
                    <p>{self.error_message_ar or self.error_message or 'غير متوفر'}</p>
                </div>
                
                <div style="margin: 15px 0;">
                    <h4>معلومات النظام:</h4>
                    <p><strong>الوحدة:</strong> {self.system_module or 'غير محدد'}</p>
                    <p><strong>المستخدم:</strong> {self.user_full_name or self.user_name or 'غير محدد'}</p>
                    <p><strong>الورشة:</strong> {self.workshop_name or 'غير محدد'}</p>
                </div>
                
                <hr>
                <p style="font-size: 12px; color: #6c757d;">
                    هذا إشعار تلقائي من نظام إدارة الورش العالمية
                </p>
            </div>
            """
        else:
            return f"""
            <div style="font-family: Arial, sans-serif;">
                <h2 style="color: #dc3545;">System Error Report</h2>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3>{self.error_title}</h3>
                    <p><strong>Category:</strong> {self.error_category}</p>
                    <p><strong>Severity:</strong> {self.severity_level}</p>
                    <p><strong>Status:</strong> {self.error_status}</p>
                    <p><strong>Occurrence:</strong> {self.first_occurrence}</p>
                </div>
                
                <div style="margin: 15px 0;">
                    <h4>Error Details:</h4>
                    <p>{self.error_message or 'Not available'}</p>
                </div>
                
                <div style="margin: 15px 0;">
                    <h4>System Information:</h4>
                    <p><strong>Module:</strong> {self.system_module or 'Not specified'}</p>
                    <p><strong>User:</strong> {self.user_full_name or self.user_name or 'Not specified'}</p>
                    <p><strong>Workshop:</strong> {self.workshop_name or 'Not specified'}</p>
                </div>
                
                <hr>
                <p style="font-size: 12px; color: #6c757d;">
                    This is an automated notification from Universal Workshop ERP
                </p>
            </div>
            """

    def send_sms_notification(self, template: Dict[str, str]):
        """إرسال إشعار نصي"""
        if not self.sms_recipients:
            return

        recipients = [phone.strip() for phone in self.sms_recipients.split(",")]

        message = f"Error Alert: {self.error_title[:50]}... Severity: {self.severity_level} - Universal Workshop ERP"

        # يمكن تخصيص هذا لاستخدام خدمة SMS فعلية
        self.log_activity(f"SMS notification sent to {len(recipients)} recipients")

    def send_slack_notification(self, template: Dict[str, str]):
        """إرسال إشعار Slack"""
        if not self.slack_channel:
            return

        # يمكن تخصيص هذا للتكامل مع Slack API
        payload = {
            "channel": self.slack_channel,
            "text": f"*{template['subject']}*",
            "attachments": [
                {
                    "color": self.get_slack_color(),
                    "fields": [
                        {"title": "Category", "value": self.error_category, "short": True},
                        {"title": "Severity", "value": self.severity_level, "short": True},
                        {"title": "Status", "value": self.error_status, "short": True},
                        {"title": "User", "value": self.user_name or "System", "short": True},
                    ],
                    "footer": "Universal Workshop ERP",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        self.log_activity("Slack notification prepared")

    def get_slack_color(self) -> str:
        """الحصول على لون إشعار Slack"""
        colors = {
            "Critical / حرج": "danger",
            "High / عالي": "warning",
            "Medium / متوسط": "#ff9500",
            "Low / منخفض": "good",
            "Info / معلوماتي": "#36a64f",
        }
        return colors.get(self.severity_level, "#cccccc")

    def send_resolution_notification(self):
        """إرسال إشعار الحل"""
        if self.email_recipients:
            subject = f"✅ Error Resolved: {self.error_title}"
            message = f"""
            <h3>Error Resolution Notification</h3>
            <p>The following error has been resolved:</p>
            <p><strong>Title:</strong> {self.error_title}</p>
            <p><strong>Resolved By:</strong> {self.resolved_by}</p>
            <p><strong>Resolution Date:</strong> {self.resolution_date}</p>
            <p><strong>Resolution Time:</strong> {self.resolution_time_minutes} minutes</p>
            <p><strong>Notes:</strong> {self.resolution_notes or 'No notes provided'}</p>
            """

            recipients = [email.strip() for email in self.email_recipients.split(",")]
            frappe.sendmail(recipients=recipients, subject=subject, message=message)

    def send_severity_change_notification(self):
        """إرسال إشعار تغيير الخطورة"""
        self.log_activity(f"Severity escalated to {self.severity_level}")

    def send_reopening_notification(self):
        """إرسال إشعار إعادة الفتح"""
        self.log_activity("Error reopened - notifications sent to stakeholders")

    # ============ Escalation Management ============

    def check_escalation_rules(self):
        """فحص قواعد التصعيد"""
        if not self.auto_escalate:
            return

        # قواعد التصعيد حسب الخطورة والوقت
        escalation_rules = {
            "Critical / حرج": 30,  # 30 دقيقة
            "High / عالي": 120,  # ساعتان
            "Medium / متوسط": 480,  # 8 ساعات
        }

        time_limit = escalation_rules.get(self.severity_level)
        if not time_limit:
            return

        if self.first_occurrence:
            elapsed_minutes = (
                datetime.now() - get_datetime(self.first_occurrence)
            ).total_seconds() / 60

            if elapsed_minutes > time_limit and not self.escalation_time:
                self.escalate_error()

    def escalate_error(self):
        """تصعيد الخطأ"""
        self.escalation_level = (self.escalation_level or 0) + 1
        self.escalation_time = now()

        # إرسال إشعار التصعيد
        if self.escalation_recipients:
            self.send_escalation_notification()

        self.log_activity(f"Error escalated to level {self.escalation_level}")

    def send_escalation_notification(self):
        """إرسال إشعار التصعيد"""
        if not self.escalation_recipients:
            return

        recipients = [email.strip() for email in self.escalation_recipients.split(",")]
        subject = f"🚨 ESCALATED - {self.error_title}"

        message = f"""
        <h2 style="color: #dc3545;">Error Escalation Notice</h2>
        <p>The following error has been escalated due to time limits:</p>
        <p><strong>Error:</strong> {self.error_title}</p>
        <p><strong>Severity:</strong> {self.severity_level}</p>
        <p><strong>Escalation Level:</strong> {self.escalation_level}</p>
        <p><strong>First Occurrence:</strong> {self.first_occurrence}</p>
        <p><strong>Assigned To:</strong> {self.assigned_to or 'Unassigned'}</p>
        <p>Please take immediate action to resolve this issue.</p>
        """

        frappe.sendmail(recipients=recipients, subject=subject, message=message)

    # ============ Trend Analysis and Reporting ============

    def update_error_trends(self):
        """تحديث اتجاهات الأخطاء"""
        try:
            # تحليل الاتجاه للأخطاء المشابهة
            similar_errors = frappe.db.count(
                "Error Logger",
                filters={
                    "error_category": self.error_category,
                    "creation": [">=", add_to_date(now(), days=-7)],
                },
            )

            if similar_errors > 10:
                self.trending_status = "Increasing / متزايد"
            elif similar_errors > 5:
                self.trending_status = "Stable / مستقر"
            else:
                self.trending_status = "Decreasing / متناقص"

            # تحديث تكرار الحدوث
            if self.occurrence_count > 10:
                self.recurrence_frequency = "Frequent / متكرر"
            elif self.occurrence_count > 5:
                self.recurrence_frequency = "Occasional / أحياناً"
            elif self.occurrence_count > 1:
                self.recurrence_frequency = "Rare / نادر"
            else:
                self.recurrence_frequency = "Never / لا يتكرر"

        except Exception as e:
            self.log_activity(f"Error updating trends: {str(e)}")

    def calculate_business_impact(self):
        """حساب التأثير على الأعمال"""
        # يمكن تخصيص هذا حسب منطق الأعمال
        impact_factors = {
            "Critical / حرج": 100,
            "High / عالي": 50,
            "Medium / متوسط": 20,
            "Low / منخفض": 5,
            "Info / معلوماتي": 1,
        }

        base_impact = impact_factors.get(self.severity_level, 10)

        # مضاعفات حسب عدد المستخدمين المتأثرين
        if self.affected_users_count:
            base_impact *= min(self.affected_users_count, 10)

        # تقدير التأثير المالي (بالريال العماني)
        if not self.financial_impact:
            self.financial_impact = base_impact * 0.5  # تقدير أولي

    # ============ Utility Methods ============

    def log_activity(self, activity: str):
        """تسجيل نشاط"""
        timestamp = now()
        entry = f"[{timestamp}] {activity}"

        current_log = self.activity_log or ""
        self.activity_log = f"{current_log}\n{entry}" if current_log else entry

        # الاحتفاظ بآخر 100 إدخال فقط
        lines = self.activity_log.split("\n")
        if len(lines) > 100:
            self.activity_log = "\n".join(lines[-100:])

    def log_system_activity(self, activity: str):
        """تسجيل نشاط النظام"""
        frappe.logger().info(f"Error Logger: {activity} - Error ID: {self.name}")

    @frappe.whitelist()
    def mark_as_seen(self):
        """تمييز كمشاهد"""
        self.seen_status = True
        self.log_activity("Marked as seen")
        self.save()

    @frappe.whitelist()
    def archive_error(self):
        """أرشفة الخطأ"""
        self.archived_status = True
        self.retention_date = add_to_date(today(), years=1)
        self.log_activity("Error archived")
        self.save()

    @frappe.whitelist()
    def assign_to_user(self, user: str):
        """تكليف مستخدم"""
        self.assigned_to = user
        self.error_status = "In Progress / قيد التقدم"
        self.log_activity(f"Assigned to {user}")
        self.save()

        # إرسال إشعار للمستخدم المكلف
        self.send_assignment_notification(user)

    def send_assignment_notification(self, user: str):
        """إرسال إشعار التكليف"""
        user_email = frappe.db.get_value("User", user, "email")
        if user_email:
            subject = f"Error Assignment: {self.error_title}"
            message = f"""
            <h3>Error Assignment</h3>
            <p>You have been assigned to resolve the following error:</p>
            <p><strong>Title:</strong> {self.error_title}</p>
            <p><strong>Category:</strong> {self.error_category}</p>
            <p><strong>Severity:</strong> {self.severity_level}</p>
            <p><strong>Priority:</strong> {self.resolution_priority}</p>
            <p>Please review and take appropriate action.</p>
            """

            frappe.sendmail(recipients=[user_email], subject=subject, message=message)


# ============ Global Error Logging Functions ============


@frappe.whitelist()
def log_system_error(
    error_title: str,
    error_message: str,
    severity_level: str = "Medium / متوسط",
    error_category: str = "System Error / خطأ النظام",
    **kwargs,
) -> str:
    """تسجيل خطأ النظام"""
    try:
        error_log = frappe.new_doc("Error Logger")
        error_log.error_title = error_title
        error_log.error_message = error_message
        error_log.severity_level = severity_level
        error_log.error_category = error_category

        # إضافة معلومات إضافية
        for key, value in kwargs.items():
            if hasattr(error_log, key):
                setattr(error_log, key, value)

        # استخراج معلومات Stack Trace تلقائياً
        if not error_log.stack_trace:
            error_log.stack_trace = traceback.format_exc()

        error_log.insert()
        return error_log.name

    except Exception as e:
        frappe.log_error(f"Failed to log error: {str(e)}", "Error Logger")
        return None


@frappe.whitelist()
def get_error_dashboard_data() -> Dict[str, Any]:
    """الحصول على بيانات لوحة تحكم الأخطاء"""
    today_date = today()
    week_ago = add_to_date(today_date, days=-7)

    # إحصائيات عامة
    total_errors = frappe.db.count("Error Logger")
    new_errors = frappe.db.count("Error Logger", {"error_status": "New / جديد"})
    critical_errors = frappe.db.count("Error Logger", {"severity_level": "Critical / حرج"})

    # أخطاء الأسبوع الماضي
    recent_errors = frappe.db.count("Error Logger", {"creation": [">=", week_ago]})

    # أخطاء حسب الفئة
    category_stats = frappe.db.sql(
        """
        SELECT error_category, COUNT(*) as count
        FROM `tabError Logger`
        WHERE creation >= %s
        GROUP BY error_category
        ORDER BY count DESC
        LIMIT 5
    """,
        [week_ago],
        as_dict=True,
    )

    # أخطاء حسب الخطورة
    severity_stats = frappe.db.sql(
        """
        SELECT severity_level, COUNT(*) as count
        FROM `tabError Logger`
        WHERE creation >= %s
        GROUP BY severity_level
        ORDER BY count DESC
    """,
        [week_ago],
        as_dict=True,
    )

    # أحدث الأخطاء الحرجة
    latest_critical = frappe.get_list(
        "Error Logger",
        filters={"severity_level": "Critical / حرج"},
        fields=["name", "error_title", "creation", "error_status"],
        order_by="creation desc",
        limit=5,
    )

    return {
        "summary": {
            "total_errors": total_errors,
            "new_errors": new_errors,
            "critical_errors": critical_errors,
            "recent_errors": recent_errors,
        },
        "category_breakdown": category_stats,
        "severity_breakdown": severity_stats,
        "latest_critical_errors": latest_critical,
        "trends": {
            "weekly_growth": calculate_error_growth_rate(week_ago),
            "resolution_rate": calculate_resolution_rate(),
            "average_resolution_time": calculate_avg_resolution_time(),
        },
    }


def calculate_error_growth_rate(since_date: str) -> float:
    """حساب معدل نمو الأخطاء"""
    current_week = frappe.db.count("Error Logger", {"creation": [">=", since_date]})
    previous_week = frappe.db.count(
        "Error Logger", {"creation": ["between", [add_to_date(since_date, days=-7), since_date]]}
    )

    if previous_week == 0:
        return 100.0 if current_week > 0 else 0.0

    return ((current_week - previous_week) / previous_week) * 100


def calculate_resolution_rate() -> float:
    """حساب معدل الحل"""
    total_errors = frappe.db.count("Error Logger")
    resolved_errors = frappe.db.count(
        "Error Logger",
        {
            "resolution_status": [
                "in",
                ["Resolved / محلول", "Verified / تم التحقق", "Closed / مغلق"],
            ]
        },
    )

    return (resolved_errors / total_errors * 100) if total_errors > 0 else 0.0


def calculate_avg_resolution_time() -> float:
    """حساب متوسط وقت الحل"""
    avg_time = frappe.db.sql(
        """
        SELECT AVG(resolution_time_minutes)
        FROM `tabError Logger`
        WHERE resolution_time_minutes IS NOT NULL
        AND resolution_time_minutes > 0
    """
    )[0][0]

    return float(avg_time) if avg_time else 0.0


@frappe.whitelist()
def cleanup_old_errors(days: int = 90):
    """تنظيف الأخطاء القديمة"""
    cutoff_date = add_to_date(today(), days=-days)

    # أرشفة الأخطاء القديمة المحلولة
    old_resolved_errors = frappe.get_list(
        "Error Logger",
        filters={
            "creation": ["<", cutoff_date],
            "resolution_status": [
                "in",
                ["Resolved / محلول", "Verified / تم التحقق", "Closed / مغلق"],
            ],
            "archived_status": 0,
        },
        fields=["name"],
    )

    for error in old_resolved_errors:
        doc = frappe.get_doc("Error Logger", error.name)
        doc.archive_error()

    return len(old_resolved_errors)


@frappe.whitelist()
def generate_error_report(
    start_date: str, end_date: str, format_type: str = "summary"
) -> Dict[str, Any]:
    """إنشاء تقرير الأخطاء"""
    errors = frappe.get_list(
        "Error Logger", filters={"creation": ["between", [start_date, end_date]]}, fields=["*"]
    )

    if format_type == "detailed":
        return {"errors": errors, "total": len(errors)}

    # تقرير موجز
    summary = {
        "period": {"start": start_date, "end": end_date},
        "total_errors": len(errors),
        "by_category": {},
        "by_severity": {},
        "by_status": {},
        "top_error_sources": {},
    }

    for error in errors:
        # تجميع حسب الفئة
        category = error.get("error_category", "Unknown")
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1

        # تجميع حسب الخطورة
        severity = error.get("severity_level", "Unknown")
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

        # تجميع حسب الحالة
        status = error.get("error_status", "Unknown")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

    return summary
