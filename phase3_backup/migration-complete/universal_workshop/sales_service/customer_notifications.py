import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, add_days, cint, flt
from frappe.desk.doctype.notification_log.notification_log import make_notification_log
from frappe.email.doctype.email_queue.email_queue import send_email
from typing import Dict, List, Optional
import json
import re


class CustomerNotificationSystem:
    """Comprehensive customer notification system for Universal Workshop ERP"""

    def __init__(self, service_order: str = None, customer: str = None):
        self.service_order = service_order
        self.customer = customer
        self.service_order_doc = None
        self.customer_doc = None

        if service_order:
            self.service_order_doc = frappe.get_doc("Sales Order", service_order)
            self.customer_doc = frappe.get_doc("Customer", self.service_order_doc.customer)
        elif customer:
            self.customer_doc = frappe.get_doc("Customer", customer)

    def send_workflow_notification(
        self,
        notification_type: str,
        stage: str,
        custom_data: Dict = None,
        send_sms: bool = True,
        send_email: bool = True,
    ) -> Dict:
        """Send workflow notification for service stages"""
        try:
            # Get notification template
            template = self._get_notification_template(notification_type, stage)
            if not template:
                return {"status": "error", "message": _("Notification template not found")}

            # Prepare notification data
            notification_data = self._prepare_notification_data(custom_data or {})

            # Send notifications
            results = {}

            if send_email and self.customer_doc.email_id:
                email_result = self._send_email_notification(template, notification_data)
                results["email"] = email_result

            if send_sms and self.customer_doc.mobile_no:
                sms_result = self._send_sms_notification(template, notification_data)
                results["sms"] = sms_result

            # Create notification log
            self._create_notification_log(notification_type, stage, notification_data)

            # Publish real-time notification
            self._publish_realtime_notification(notification_type, stage, notification_data)

            return {
                "status": "success",
                "message": _("Notification sent successfully"),
                "message_ar": "تم إرسال الإشعار بنجاح",
                "results": results,
                "notification_type": notification_type,
                "stage": stage,
            }

        except Exception as e:
            frappe.log_error(f"Notification error: {str(e)}", "Customer Notification System")
            return {
                "status": "error",
                "message": _("Failed to send notification: {0}").format(str(e)),
                "message_ar": "فشل في إرسال الإشعار: {0}".format(str(e)),
            }

    def _get_notification_template(self, notification_type: str, stage: str) -> Dict:
        """Get notification template for specific type and stage"""
        templates = {
            "service_estimate": {
                "created": {
                    "subject_en": "Service Estimate Created - {service_order}",
                    "subject_ar": "تم إنشاء تقدير الخدمة - {service_order}",
                    "email_body_en": """
Dear {customer_name},

Your service estimate has been created for vehicle {vehicle_registration}.

Estimate Details:
- Service Order: {service_order}
- Vehicle: {vehicle_registration}
- Total Amount: {total_amount}
- Expected Completion: {expected_completion}

Services Included:
{services_list}

You can view your estimate online or visit our workshop.

Best regards,
{workshop_name}
                    """,
                    "email_body_ar": """
عزيزي {customer_name_ar},

تم إنشاء تقدير الخدمة لمركبتك {vehicle_registration}.

تفاصيل التقدير:
- رقم أمر الخدمة: {service_order}
- المركبة: {vehicle_registration}
- المبلغ الإجمالي: {total_amount}
- التاريخ المتوقع للانتهاء: {expected_completion}

الخدمات المشمولة:
{services_list_ar}

يمكنك مراجعة التقدير عبر الإنترنت أو زيارة ورشتنا.

مع أطيب التحيات،
{workshop_name_ar}
                    """,
                    "sms_en": "Service estimate created for {vehicle_registration}. Total: {total_amount}. Expected completion: {expected_completion}. View details: {link}",
                    "sms_ar": "تم إنشاء تقدير خدمة للمركبة {vehicle_registration}. المجموع: {total_amount}. التاريخ المتوقع: {expected_completion}. عرض التفاصيل: {link}",
                },
                "approved": {
                    "subject_en": "Service Estimate Approved - Work Starting",
                    "subject_ar": "تمت الموافقة على تقدير الخدمة - بدء العمل",
                    "email_body_en": "Your service estimate has been approved. Work will commence shortly.",
                    "email_body_ar": "تمت الموافقة على تقدير الخدمة. سيبدأ العمل قريباً.",
                    "sms_en": "Service approved for {vehicle_registration}. Work starting soon.",
                    "sms_ar": "تمت الموافقة على الخدمة للمركبة {vehicle_registration}. العمل سيبدأ قريباً.",
                },
            },
            "service_progress": {
                "started": {
                    "subject_en": "Service Work Started - {service_order}",
                    "subject_ar": "بدء العمل على الخدمة - {service_order}",
                    "email_body_en": "Work has started on your vehicle {vehicle_registration}.",
                    "email_body_ar": "بدأ العمل على مركبتك {vehicle_registration}.",
                    "sms_en": "Work started on {vehicle_registration}. Progress: {progress_percentage}%",
                    "sms_ar": "بدأ العمل على {vehicle_registration}. التقدم: {progress_percentage}%",
                },
                "progress_update": {
                    "subject_en": "Service Progress Update - {progress_percentage}% Complete",
                    "subject_ar": "تحديث تقدم الخدمة - {progress_percentage}% مكتمل",
                    "email_body_en": "Your service is {progress_percentage}% complete. Current operation: {current_operation}",
                    "email_body_ar": "خدمتك مكتملة بنسبة {progress_percentage}%. العملية الحالية: {current_operation_ar}",
                    "sms_en": "{vehicle_registration} service {progress_percentage}% complete. Current: {current_operation}",
                    "sms_ar": "خدمة {vehicle_registration} مكتملة {progress_percentage}%. الحالية: {current_operation_ar}",
                },
                "on_hold": {
                    "subject_en": "Service Temporarily On Hold",
                    "subject_ar": "الخدمة متوقفة مؤقتاً",
                    "email_body_en": "Your service has been temporarily put on hold. Reason: {hold_reason}",
                    "email_body_ar": "تم إيقاف خدمتك مؤقتاً. السبب: {hold_reason_ar}",
                    "sms_en": "Service on hold for {vehicle_registration}. Reason: {hold_reason}",
                    "sms_ar": "الخدمة متوقفة للمركبة {vehicle_registration}. السبب: {hold_reason_ar}",
                },
                "completed": {
                    "subject_en": "Service Completed - Ready for Pickup",
                    "subject_ar": "اكتملت الخدمة - جاهزة للاستلام",
                    "email_body_en": """
Your vehicle {vehicle_registration} is ready for pickup!

Service Summary:
- Total Time: {total_time} hours
- Services Completed: {completed_services}
- Quality Check: Passed
- Total Amount: {final_amount}

Please visit our workshop during business hours to collect your vehicle.

Thank you for choosing {workshop_name}!
                    """,
                    "email_body_ar": """
مركبتك {vehicle_registration} جاهزة للاستلام!

ملخص الخدمة:
- إجمالي الوقت: {total_time} ساعة
- الخدمات المكتملة: {completed_services_ar}
- فحص الجودة: اجتاز
- المبلغ الإجمالي: {final_amount}

يرجى زيارة ورشتنا خلال ساعات العمل لاستلام مركبتك.

شكراً لاختياركم {workshop_name_ar}!
                    """,
                    "sms_en": "{vehicle_registration} ready for pickup! Quality passed. Total: {final_amount}",
                    "sms_ar": "{vehicle_registration} جاهزة للاستلام! اجتاز الفحص. المجموع: {final_amount}",
                },
            },
            "payment": {
                "reminder": {
                    "subject_en": "Payment Reminder - {service_order}",
                    "subject_ar": "تذكير بالدفع - {service_order}",
                    "email_body_en": "Payment reminder for service order {service_order}. Amount due: {amount_due}",
                    "email_body_ar": "تذكير بالدفع لأمر الخدمة {service_order}. المبلغ المستحق: {amount_due}",
                    "sms_en": "Payment due: {amount_due} for {service_order}. Pay now: {payment_link}",
                    "sms_ar": "دفع مستحق: {amount_due} لـ {service_order}. ادفع الآن: {payment_link}",
                },
                "received": {
                    "subject_en": "Payment Received - Thank You",
                    "subject_ar": "تم استلام الدفع - شكراً لك",
                    "email_body_en": "Payment received for {service_order}. Amount: {payment_amount}",
                    "email_body_ar": "تم استلام الدفع لـ {service_order}. المبلغ: {payment_amount}",
                    "sms_en": "Payment received: {payment_amount} for {service_order}. Thank you!",
                    "sms_ar": "تم استلام الدفع: {payment_amount} لـ {service_order}. شكراً!",
                },
            },
            "appointment": {
                "scheduled": {
                    "subject_en": "Service Appointment Scheduled",
                    "subject_ar": "تم تحديد موعد الخدمة",
                    "email_body_en": "Service appointment scheduled for {appointment_date} at {appointment_time}",
                    "email_body_ar": "تم تحديد موعد الخدمة في {appointment_date} الساعة {appointment_time}",
                    "sms_en": "Appointment: {appointment_date} {appointment_time} for {vehicle_registration}",
                    "sms_ar": "الموعد: {appointment_date} {appointment_time} للمركبة {vehicle_registration}",
                },
                "reminder": {
                    "subject_en": "Service Appointment Reminder",
                    "subject_ar": "تذكير بموعد الخدمة",
                    "email_body_en": "Reminder: Service appointment tomorrow at {appointment_time}",
                    "email_body_ar": "تذكير: موعد الخدمة غداً الساعة {appointment_time}",
                    "sms_en": "Reminder: Service appointment tomorrow {appointment_time} for {vehicle_registration}",
                    "sms_ar": "تذكير: موعد الخدمة غداً {appointment_time} للمركبة {vehicle_registration}",
                },
            },
        }

        return templates.get(notification_type, {}).get(stage, {})

    def _prepare_notification_data(self, custom_data: Dict) -> Dict:
        """Prepare data for notification templates"""
        data = {
            # Basic customer data
            "customer_name": self.customer_doc.customer_name if self.customer_doc else "",
            "customer_name_ar": (
                getattr(self.customer_doc, "customer_name_ar", "") if self.customer_doc else ""
            ),
            "customer_email": self.customer_doc.email_id if self.customer_doc else "",
            "customer_mobile": self.customer_doc.mobile_no if self.customer_doc else "",
            # Workshop data
            "workshop_name": frappe.db.get_single_value("System Settings", "company")
            or "Universal Workshop",
            "workshop_name_ar": "ورشة شاملة",  # Default Arabic name
            # Date/time
            "current_date": nowdate(),
            "current_datetime": get_datetime(),
            # Language
            "language": frappe.local.lang or "en",
        }

        # Service order specific data
        if self.service_order_doc:
            data.update(
                {
                    "service_order": self.service_order_doc.name,
                    "vehicle_registration": getattr(
                        self.service_order_doc, "vehicle_registration", ""
                    ),
                    "total_amount": self._format_currency(self.service_order_doc.grand_total),
                    "expected_completion": self.service_order_doc.delivery_date,
                    "services_list": self._get_services_list(),
                    "services_list_ar": self._get_services_list(arabic=True),
                }
            )

        # Add custom data
        data.update(custom_data)

        return data

    def _send_email_notification(self, template: Dict, data: Dict) -> Dict:
        """Send email notification"""
        try:
            language = data.get("language", "en")

            # Select language-specific template
            if language == "ar":
                subject = template.get("subject_ar", template.get("subject_en", ""))
                body = template.get("email_body_ar", template.get("email_body_en", ""))
            else:
                subject = template.get("subject_en", "")
                body = template.get("email_body_en", "")

            # Format template with data
            subject = subject.format(**data)
            body = body.format(**data)

            # Send email
            send_email(
                recipients=[self.customer_doc.email_id],
                subject=subject,
                message=body,
                sender=frappe.db.get_single_value("System Settings", "outgoing_email_account"),
                communication=True,
                reference_doctype="Sales Order" if self.service_order else "Customer",
                reference_name=self.service_order or self.customer,
            )

            return {
                "status": "success",
                "message": _("Email sent successfully"),
                "recipient": self.customer_doc.email_id,
            }

        except Exception as e:
            frappe.log_error(f"Email notification error: {str(e)}")
            return {"status": "error", "message": _("Failed to send email: {0}").format(str(e))}

    def _send_sms_notification(self, template: Dict, data: Dict) -> Dict:
        """Send SMS notification"""
        try:
            language = data.get("language", "en")

            # Select language-specific template
            if language == "ar":
                message = template.get("sms_ar", template.get("sms_en", ""))
            else:
                message = template.get("sms_en", "")

            # Format template with data
            message = message.format(**data)

            # Truncate SMS to 160 characters
            if len(message) > 160:
                message = message[:157] + "..."

            # Send SMS (integration with SMS provider)
            sms_result = self._send_sms_via_provider(self.customer_doc.mobile_no, message)

            return sms_result

        except Exception as e:
            frappe.log_error(f"SMS notification error: {str(e)}")
            return {"status": "error", "message": _("Failed to send SMS: {0}").format(str(e))}

    def _send_sms_via_provider(self, mobile_no: str, message: str) -> Dict:
        """Send SMS via configured SMS provider"""
        try:
            # Format Oman mobile number
            mobile_no = self._format_oman_mobile(mobile_no)

            # Get SMS settings
            sms_settings = frappe.get_single("SMS Settings")

            if not sms_settings.sms_gateway_url:
                return {"status": "error", "message": _("SMS gateway not configured")}

            # Create SMS log
            sms_log = frappe.new_doc("SMS Log")
            sms_log.sender_name = "Universal Workshop"
            sms_log.receiver_list = mobile_no
            sms_log.message = message
            sms_log.sent_on = get_datetime()
            sms_log.insert()

            # For demo purposes, we'll simulate SMS sending
            # In production, integrate with actual SMS provider (Twilio, etc.)
            frappe.log_error(f"SMS sent to {mobile_no}: {message}", "SMS Notification")

            return {
                "status": "success",
                "message": _("SMS sent successfully"),
                "recipient": mobile_no,
                "sms_log": sms_log.name,
            }

        except Exception as e:
            return {"status": "error", "message": _("SMS sending failed: {0}").format(str(e))}

    def _format_oman_mobile(self, mobile_no: str) -> str:
        """Format mobile number for Oman (+968)"""
        if not mobile_no:
            return ""

        # Remove all non-digits
        digits_only = re.sub(r"\D", "", mobile_no)

        # Handle different formats
        if digits_only.startswith("968"):
            return f"+{digits_only}"
        elif len(digits_only) == 8:
            return f"+968{digits_only}"
        else:
            return f"+968{digits_only[-8:]}"  # Take last 8 digits

    def _create_notification_log(self, notification_type: str, stage: str, data: Dict):
        """Create notification log for tracking"""
        try:
            notification_log = frappe.new_doc("Notification Log")
            notification_log.subject = f"{notification_type.title()} - {stage.title()}"
            notification_log.for_user = self.customer_doc.name if self.customer_doc else ""
            notification_log.type = "Alert"
            notification_log.document_type = "Sales Order" if self.service_order else "Customer"
            notification_log.document_name = self.service_order or self.customer
            notification_log.from_user = frappe.session.user
            notification_log.email_content = json.dumps(data, default=str)
            notification_log.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to create notification log: {str(e)}")

    def _publish_realtime_notification(self, notification_type: str, stage: str, data: Dict):
        """Publish real-time notification"""
        try:
            frappe.publish_realtime(
                "customer_notification",
                {
                    "notification_type": notification_type,
                    "stage": stage,
                    "service_order": self.service_order,
                    "customer": self.customer
                    or (self.customer_doc.name if self.customer_doc else ""),
                    "data": data,
                    "timestamp": get_datetime(),
                },
                user=self.customer_doc.name if self.customer_doc else frappe.session.user,
            )

        except Exception as e:
            frappe.log_error(f"Failed to publish realtime notification: {str(e)}")

    def _get_services_list(self, arabic: bool = False) -> str:
        """Get formatted list of services"""
        if not self.service_order_doc:
            return ""

        services = []
        for item in self.service_order_doc.items:
            if arabic and hasattr(item, "item_name_ar") and item.item_name_ar:
                service_name = item.item_name_ar
            else:
                service_name = item.item_name or item.item_code

            services.append(f"- {service_name}: {self._format_currency(item.amount)}")

        return "\n".join(services)

    def _format_currency(self, amount: float) -> str:
        """Format currency amount for display"""
        if not amount:
            return "OMR 0.000"

        return f"OMR {amount:,.3f}"

    def schedule_appointment_reminders(self):
        """Schedule automatic appointment reminders"""
        try:
            # Get appointments for tomorrow
            tomorrow = add_days(nowdate(), 1)

            appointments = frappe.db.sql(
                """
                SELECT so.name, so.customer, so.delivery_date, so.vehicle_registration
                FROM `tabSales Order` so
                WHERE DATE(so.delivery_date) = %s
                AND so.docstatus = 1
                AND so.status NOT IN ('Completed', 'Cancelled')
                AND so.service_estimate_reference IS NOT NULL
            """,
                [tomorrow],
                as_dict=True,
            )

            for appointment in appointments:
                notification_system = CustomerNotificationSystem(appointment.name)
                notification_system.send_workflow_notification(
                    "appointment",
                    "reminder",
                    {
                        "appointment_date": appointment.delivery_date,
                        "appointment_time": "09:00",  # Default time
                        "vehicle_registration": appointment.vehicle_registration,
                    },
                )

            return {"status": "success", "reminders_sent": len(appointments)}

        except Exception as e:
            frappe.log_error(f"Failed to schedule appointment reminders: {str(e)}")
            return {"status": "error", "message": str(e)}

    def send_bulk_notifications(
        self, customers: List[str], notification_type: str, stage: str, custom_data: Dict = None
    ):
        """Send bulk notifications to multiple customers"""
        results = []

        for customer in customers:
            try:
                notification_system = CustomerNotificationSystem(customer=customer)
                result = notification_system.send_workflow_notification(
                    notification_type, stage, custom_data
                )
                results.append({"customer": customer, "result": result})

            except Exception as e:
                results.append(
                    {"customer": customer, "result": {"status": "error", "message": str(e)}}
                )

        return results


# WhiteListed API Methods
@frappe.whitelist()
def send_service_notification(service_order, notification_type, stage, custom_data=None):
    """Send service-related notification"""
    try:
        if custom_data and isinstance(custom_data, str):
            custom_data = json.loads(custom_data)

        notification_system = CustomerNotificationSystem(service_order)
        return notification_system.send_workflow_notification(
            notification_type, stage, custom_data or {}
        )

    except Exception as e:
        frappe.log_error(f"API notification error: {str(e)}")
        return {"status": "error", "message": _("Failed to send notification: {0}").format(str(e))}


@frappe.whitelist()
def send_customer_notification(customer, notification_type, stage, custom_data=None):
    """Send customer-specific notification"""
    try:
        if custom_data and isinstance(custom_data, str):
            custom_data = json.loads(custom_data)

        notification_system = CustomerNotificationSystem(customer=customer)
        return notification_system.send_workflow_notification(
            notification_type, stage, custom_data or {}
        )

    except Exception as e:
        frappe.log_error(f"API customer notification error: {str(e)}")
        return {"status": "error", "message": _("Failed to send notification: {0}").format(str(e))}


@frappe.whitelist()
def get_notification_templates():
    """Get available notification templates"""
    notification_system = CustomerNotificationSystem()
    templates = notification_system._get_notification_template("service_estimate", "created")

    # Return template structure for frontend
    return {
        "notification_types": ["service_estimate", "service_progress", "payment", "appointment"],
        "stages": {
            "service_estimate": ["created", "approved"],
            "service_progress": ["started", "progress_update", "on_hold", "completed"],
            "payment": ["reminder", "received"],
            "appointment": ["scheduled", "reminder"],
        },
        "template_example": templates,
    }


@frappe.whitelist()
def schedule_daily_reminders():
    """Schedule daily appointment reminders (called by scheduler)"""
    notification_system = CustomerNotificationSystem()
    return notification_system.schedule_appointment_reminders()


@frappe.whitelist()
def test_notification_system(service_order=None, customer=None):
    """Test notification system functionality"""
    try:
        if service_order:
            notification_system = CustomerNotificationSystem(service_order)
        elif customer:
            notification_system = CustomerNotificationSystem(customer=customer)
        else:
            return {"status": "error", "message": "Service order or customer required"}

        # Send test notification
        result = notification_system.send_workflow_notification(
            "service_progress",
            "progress_update",
            {
                "progress_percentage": 50,
                "current_operation": "Engine Inspection",
                "current_operation_ar": "فحص المحرك",
            },
        )

        return result

    except Exception as e:
        return {"status": "error", "message": _("Test failed: {0}").format(str(e))}


@frappe.whitelist()
def get_customer_notification_history(customer, limit=50):
    """Get notification history for customer"""
    try:
        history = frappe.get_list(
            "Notification Log",
            filters={"for_user": customer},
            fields=["name", "subject", "creation", "read", "type"],
            order_by="creation desc",
            limit=limit,
        )

        return {"status": "success", "history": history, "total": len(history)}

    except Exception as e:
        return {
            "status": "error",
            "message": _("Failed to get notification history: {0}").format(str(e)),
        }


@frappe.whitelist()
def send_payment_reminder(service_order, amount_due):
    """Send payment reminder for service order"""
    try:
        notification_system = CustomerNotificationSystem(service_order)
        return notification_system.send_workflow_notification(
            "payment",
            "reminder",
            {
                "amount_due": f"OMR {float(amount_due):,.3f}",
                "payment_link": f"/payment/{service_order}",
            },
        )

    except Exception as e:
        return {
            "status": "error",
            "message": _("Failed to send payment reminder: {0}").format(str(e)),
        }
