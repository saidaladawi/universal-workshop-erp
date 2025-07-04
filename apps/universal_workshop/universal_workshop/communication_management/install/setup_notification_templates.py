# -*- coding: utf-8 -*-
"""
Notification Templates Installation Setup
Creates default templates for SMS, WhatsApp, and Email communications
Supports Arabic and English languages with Oman market localization
"""

import frappe
from frappe import _
import json


def setup_notification_templates():
    """Main function to set up all default notification templates"""

    try:
        frappe.flags.ignore_permissions = True

        print("Setting up notification templates...")

        # Create template categories first
        setup_template_categories()

        # Create SMS templates
        setup_sms_templates()

        # Create WhatsApp templates
        setup_whatsapp_templates()

        # Create Email templates
        setup_email_templates()

        # Set up template permissions
        setup_template_permissions()

        frappe.db.commit()
        print("Notification templates setup completed successfully!")

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Template setup failed: {str(e)}")
        print(f"Template setup failed: {str(e)}")
        raise
    finally:
        frappe.flags.ignore_permissions = False


def setup_template_categories():
    """Set up template categories if they don't exist"""

    # Categories are defined in DocType field options
    # This function can be used for future category management
    pass


def setup_sms_templates():
    """Create default SMS templates in Arabic and English"""

    sms_templates = [
        # Appointment Confirmation SMS
        {
            "template_name": "SMS_Appointment_Confirmation_EN",
            "channel_type": "SMS",
            "language": "English",
            "template_category": "Appointment Confirmation",
            "template_body": "Dear {{ doc.customer_name }}, your appointment at {{ doc.workshop_name }} is confirmed for {{ doc.appointment_date }} at {{ doc.appointment_time }} for {{ doc.service_type }}. Vehicle: {{ doc.vehicle_number }}. Call {{ doc.workshop_phone }} for changes.",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "workshop_name": "Gulf Universal Workshop",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 AM",
                "service_type": "Regular Maintenance",
                "vehicle_number": "AB-1234",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "SMS_Appointment_Confirmation_AR",
            "channel_type": "SMS",
            "language": "Arabic",
            "template_category": "Appointment Confirmation",
            "template_body": "عزيزي {{ doc.customer_name_ar }}، تم تأكيد موعدك في {{ doc.workshop_name }} بتاريخ {{ doc.appointment_date }} في {{ doc.appointment_time }} لخدمة {{ doc.service_type }}. المركبة: {{ doc.vehicle_number }}. للتغييرات اتصل {{ doc.workshop_phone }}",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name_ar": "أحمد السعدي",
                "workshop_name": "ورشة الخليج العالمية",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 صباحاً",
                "service_type": "صيانة دورية",
                "vehicle_number": "AB-1234",
                "workshop_phone": "+968 24123456",
            },
        },
        # Service Completion SMS
        {
            "template_name": "SMS_Service_Completion_EN",
            "channel_type": "SMS",
            "language": "English",
            "template_category": "Service Completion",
            "template_body": "Service completed for {{ doc.vehicle_number }}! {{ doc.service_type }} finished. Total: OMR {{ doc.total_amount }}. Invoice: {{ doc.invoice_number }}. Collect your vehicle at {{ doc.workshop_name }}. Thank you!",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "vehicle_number": "AB-1234",
                "service_type": "Oil Change",
                "total_amount": "25.500",
                "invoice_number": "INV-2025-001",
                "workshop_name": "Gulf Universal Workshop",
            },
        },
        {
            "template_name": "SMS_Service_Completion_AR",
            "channel_type": "SMS",
            "language": "Arabic",
            "template_category": "Service Completion",
            "template_body": "تم إنجاز الخدمة للمركبة {{ doc.vehicle_number }}! انتهت خدمة {{ doc.service_type }}. المجموع: {{ doc.total_amount }} ر.ع. الفاتورة: {{ doc.invoice_number }}. استلم مركبتك من {{ doc.workshop_name }}. شكراً!",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "vehicle_number": "AB-1234",
                "service_type": "تغيير الزيت",
                "total_amount": "25.500",
                "invoice_number": "INV-2025-001",
                "workshop_name": "ورشة الخليج العالمية",
            },
        },
        # Payment Reminder SMS
        {
            "template_name": "SMS_Payment_Reminder_EN",
            "channel_type": "SMS",
            "language": "English",
            "template_category": "Payment Reminder",
            "template_body": "Payment reminder: Invoice {{ doc.invoice_number }} for OMR {{ doc.total_amount }} is {{ doc.days_overdue }} days overdue. Please settle by {{ doc.due_date }}. Contact {{ doc.workshop_phone }}.",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "invoice_number": "INV-2025-001",
                "total_amount": "25.500",
                "days_overdue": "5",
                "due_date": "30/01/2025",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "SMS_Payment_Reminder_AR",
            "channel_type": "SMS",
            "language": "Arabic",
            "template_category": "Payment Reminder",
            "template_body": "تذكير دفع: الفاتورة {{ doc.invoice_number }} بمبلغ {{ doc.total_amount }} ر.ع متأخرة {{ doc.days_overdue }} أيام. الرجاء السداد قبل {{ doc.due_date }}. اتصل {{ doc.workshop_phone }}",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "invoice_number": "INV-2025-001",
                "total_amount": "25.500",
                "days_overdue": "5",
                "due_date": "30/01/2025",
                "workshop_phone": "+968 24123456",
            },
        },
        # Appointment Reminder SMS
        {
            "template_name": "SMS_Appointment_Reminder_EN",
            "channel_type": "SMS",
            "language": "English",
            "template_category": "Appointment Reminder",
            "template_body": "Reminder: Your appointment at {{ doc.workshop_name }} is tomorrow {{ doc.appointment_date }} at {{ doc.appointment_time }} for {{ doc.service_type }}. Vehicle: {{ doc.vehicle_number }}. Call {{ doc.workshop_phone }} to reschedule.",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "workshop_name": "Gulf Universal Workshop",
                "appointment_date": "16/01/2025",
                "appointment_time": "10:00 AM",
                "service_type": "Regular Maintenance",
                "vehicle_number": "AB-1234",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "SMS_Appointment_Reminder_AR",
            "channel_type": "SMS",
            "language": "Arabic",
            "template_category": "Appointment Reminder",
            "template_body": "تذكير: موعدك في {{ doc.workshop_name }} غداً {{ doc.appointment_date }} في {{ doc.appointment_time }} لخدمة {{ doc.service_type }}. المركبة: {{ doc.vehicle_number }}. اتصل {{ doc.workshop_phone }} لإعادة الجدولة.",
            "max_length": 160,
            "approval_status": "Approved",
            "preview_context": {
                "workshop_name": "ورشة الخليج العالمية",
                "appointment_date": "16/01/2025",
                "appointment_time": "10:00 صباحاً",
                "service_type": "صيانة دورية",
                "vehicle_number": "AB-1234",
                "workshop_phone": "+968 24123456",
            },
        },
    ]

    for template_data in sms_templates:
        create_template_if_not_exists(template_data)


def setup_whatsapp_templates():
    """Create default WhatsApp templates in Arabic and English"""

    whatsapp_templates = [
        # Appointment Confirmation WhatsApp
        {
            "template_name": "WA_Appointment_Confirmation_EN",
            "channel_type": "WhatsApp",
            "language": "English",
            "template_category": "Appointment Confirmation",
            "template_body": "✅ *Appointment Confirmed*\n\nDear {{ doc.customer_name }},\n\nYour service appointment has been confirmed:\n\n📅 Date: {{ doc.appointment_date }}\n⏰ Time: {{ doc.appointment_time }}\n🔧 Service: {{ doc.service_type }}\n🚗 Vehicle: {{ doc.vehicle_number }}\n\n📍 Workshop: {{ doc.workshop_name }}\n📞 Contact: {{ doc.workshop_phone }}\n\nPlease arrive 15 minutes early. Thank you!",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 AM",
                "service_type": "Regular Maintenance",
                "vehicle_number": "AB-1234",
                "workshop_name": "Gulf Universal Workshop",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "WA_Appointment_Confirmation_AR",
            "channel_type": "WhatsApp",
            "language": "Arabic",
            "template_category": "Appointment Confirmation",
            "template_body": "✅ *تأكيد الموعد*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nتم تأكيد موعد الخدمة:\n\n📅 التاريخ: {{ doc.appointment_date }}\n⏰ الوقت: {{ doc.appointment_time }}\n🔧 الخدمة: {{ doc.service_type }}\n🚗 المركبة: {{ doc.vehicle_number }}\n\n📍 الورشة: {{ doc.workshop_name }}\n📞 الهاتف: {{ doc.workshop_phone }}\n\nالرجاء الحضور قبل 15 دقيقة. شكراً لك!",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name_ar": "أحمد السعدي",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 صباحاً",
                "service_type": "صيانة دورية",
                "vehicle_number": "AB-1234",
                "workshop_name": "ورشة الخليج العالمية",
                "workshop_phone": "+968 24123456",
            },
        },
        # Service Completion WhatsApp
        {
            "template_name": "WA_Service_Completion_EN",
            "channel_type": "WhatsApp",
            "language": "English",
            "template_category": "Service Completion",
            "template_body": "🎉 *Service Completed!*\n\nDear {{ doc.customer_name }},\n\nGreat news! Your vehicle service is complete:\n\n🚗 Vehicle: {{ doc.vehicle_number }}\n🔧 Service: {{ doc.service_type }}\n💰 Total Amount: OMR {{ doc.total_amount }}\n📄 Invoice: {{ doc.invoice_number }}\n\nYour vehicle is ready for collection at {{ doc.workshop_name }}.\n\nThank you for trusting us with your vehicle! 🚗✨",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "vehicle_number": "AB-1234",
                "service_type": "Oil Change",
                "total_amount": "25.500",
                "invoice_number": "INV-2025-001",
                "workshop_name": "Gulf Universal Workshop",
            },
        },
        {
            "template_name": "WA_Service_Completion_AR",
            "channel_type": "WhatsApp",
            "language": "Arabic",
            "template_category": "Service Completion",
            "template_body": "🎉 *تم إنجاز الخدمة!*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nأخبار رائعة! تم إنجاز خدمة مركبتك:\n\n🚗 المركبة: {{ doc.vehicle_number }}\n🔧 الخدمة: {{ doc.service_type }}\n💰 المبلغ الإجمالي: {{ doc.total_amount }} ر.ع\n📄 الفاتورة: {{ doc.invoice_number }}\n\nمركبتك جاهزة للاستلام من {{ doc.workshop_name }}.\n\nشكراً لثقتك بخدماتنا! 🚗✨",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name_ar": "أحمد السعدي",
                "vehicle_number": "AB-1234",
                "service_type": "تغيير الزيت",
                "total_amount": "25.500",
                "invoice_number": "INV-2025-001",
                "workshop_name": "ورشة الخليج العالمية",
            },
        },
        # Quotation WhatsApp
        {
            "template_name": "WA_Quotation_EN",
            "channel_type": "WhatsApp",
            "language": "English",
            "template_category": "Quotation",
            "template_body": "📋 *Service Quotation*\n\nDear {{ doc.customer_name }},\n\nQuotation for your vehicle {{ doc.vehicle_number }}:\n\n{{ doc.services_list }}\n\n💰 Total Amount: OMR {{ doc.total_amount }}\n📄 Quotation: {{ doc.quotation_number }}\n⏰ Valid Until: {{ doc.valid_until }}\n\nApprove to schedule your service!\n\n📞 {{ doc.workshop_phone }}",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "vehicle_number": "AB-1234",
                "services_list": "• Oil Change - OMR 15.000\n• Brake Inspection - OMR 10.500\n• Air Filter - OMR 8.250",
                "total_amount": "45.750",
                "quotation_number": "QTN-2025-001",
                "valid_until": "20/01/2025",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "WA_Quotation_AR",
            "channel_type": "WhatsApp",
            "language": "Arabic",
            "template_category": "Quotation",
            "template_body": "📋 *عرض أسعار الخدمة*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nعرض أسعار لمركبتك {{ doc.vehicle_number }}:\n\n{{ doc.services_list }}\n\n💰 المبلغ الإجمالي: {{ doc.total_amount }} ر.ع\n📄 العرض: {{ doc.quotation_number }}\n⏰ صالح حتى: {{ doc.valid_until }}\n\nوافق لجدولة خدمتك!\n\n📞 {{ doc.workshop_phone }}",
            "max_length": 4096,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name_ar": "أحمد السعدي",
                "vehicle_number": "AB-1234",
                "services_list": "• تغيير الزيت - 15.000 ر.ع\n• فحص الفرامل - 10.500 ر.ع\n• فلتر الهواء - 8.250 ر.ع",
                "total_amount": "45.750",
                "quotation_number": "QTN-2025-001",
                "valid_until": "20/01/2025",
                "workshop_phone": "+968 24123456",
            },
        },
    ]

    for template_data in whatsapp_templates:
        create_template_if_not_exists(template_data)


def setup_email_templates():
    """Create default Email templates in Arabic and English"""

    email_templates = [
        # Appointment Confirmation Email
        {
            "template_name": "Email_Appointment_Confirmation_EN",
            "channel_type": "Email",
            "language": "English",
            "template_category": "Appointment Confirmation",
            "template_subject": "Appointment Confirmed - {{ doc.service_type }}",
            "template_body": "<div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'><h2 style='color: #2E86AB;'>Appointment Confirmation</h2><p>Dear {{ doc.customer_name }},</p><p>Your service appointment has been confirmed with the following details:</p><div style='background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'><h3 style='margin-top: 0;'>Appointment Details</h3><ul style='list-style: none; padding: 0;'><li style='padding: 5px 0;'><strong>📅 Date:</strong> {{ doc.appointment_date }}</li><li style='padding: 5px 0;'><strong>⏰ Time:</strong> {{ doc.appointment_time }}</li><li style='padding: 5px 0;'><strong>🔧 Service:</strong> {{ doc.service_type }}</li><li style='padding: 5px 0;'><strong>🚗 Vehicle:</strong> {{ doc.vehicle_number }}</li></ul></div><div style='background: #e3f2fd; padding: 15px; border-radius: 8px;'><h4 style='margin-top: 0;'>Workshop Details</h4><p><strong>{{ doc.workshop_name }}</strong><br/>📞 Phone: {{ doc.workshop_phone }}</p></div><p><strong>Important:</strong> Please arrive 15 minutes early for check-in.</p><p>Thank you for choosing our services!</p><hr style='margin: 30px 0;'/><p style='color: #666; font-size: 12px;'>This is an automated message. Please do not reply to this email.</p></div>",
            "max_length": 10000,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 AM",
                "service_type": "Regular Maintenance",
                "vehicle_number": "AB-1234",
                "workshop_name": "Gulf Universal Workshop",
                "workshop_phone": "+968 24123456",
            },
        },
        {
            "template_name": "Email_Appointment_Confirmation_AR",
            "channel_type": "Email",
            "language": "Arabic",
            "template_category": "Appointment Confirmation",
            "template_subject": "تأكيد الموعد - {{ doc.service_type }}",
            "template_body": "<div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl; text-align: right;'><h2 style='color: #2E86AB;'>تأكيد الموعد</h2><p>عزيزي {{ doc.customer_name_ar }}،</p><p>تم تأكيد موعد الخدمة مع التفاصيل التالية:</p><div style='background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'><h3 style='margin-top: 0;'>تفاصيل الموعد</h3><ul style='list-style: none; padding: 0;'><li style='padding: 5px 0;'><strong>📅 التاريخ:</strong> {{ doc.appointment_date }}</li><li style='padding: 5px 0;'><strong>⏰ الوقت:</strong> {{ doc.appointment_time }}</li><li style='padding: 5px 0;'><strong>🔧 الخدمة:</strong> {{ doc.service_type }}</li><li style='padding: 5px 0;'><strong>🚗 المركبة:</strong> {{ doc.vehicle_number }}</li></ul></div><div style='background: #e3f2fd; padding: 15px; border-radius: 8px;'><h4 style='margin-top: 0;'>تفاصيل الورشة</h4><p><strong>{{ doc.workshop_name }}</strong><br/>📞 الهاتف: {{ doc.workshop_phone }}</p></div><p><strong>مهم:</strong> الرجاء الحضور قبل 15 دقيقة من الموعد.</p><p>شكراً لك لاختيار خدماتنا!</p><hr style='margin: 30px 0;'/><p style='color: #666; font-size: 12px;'>هذه رسالة تلقائية. الرجاء عدم الرد على هذا البريد الإلكتروني.</p></div>",
            "max_length": 10000,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name_ar": "أحمد السعدي",
                "appointment_date": "15/01/2025",
                "appointment_time": "10:00 صباحاً",
                "service_type": "صيانة دورية",
                "vehicle_number": "AB-1234",
                "workshop_name": "ورشة الخليج العالمية",
                "workshop_phone": "+968 24123456",
            },
        },
        # Invoice Notification Email
        {
            "template_name": "Email_Invoice_Notification_EN",
            "channel_type": "Email",
            "language": "English",
            "template_category": "Invoice Notification",
            "template_subject": "Invoice {{ doc.invoice_number }} - OMR {{ doc.total_amount }}",
            "template_body": "<div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'><h2 style='color: #2E86AB;'>Service Invoice</h2><p>Dear {{ doc.customer_name }},</p><p>Thank you for choosing our services. Please find your invoice details below:</p><div style='background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'><h3 style='margin-top: 0;'>Invoice Details</h3><ul style='list-style: none; padding: 0;'><li style='padding: 5px 0;'><strong>📄 Invoice Number:</strong> {{ doc.invoice_number }}</li><li style='padding: 5px 0;'><strong>🚗 Vehicle:</strong> {{ doc.vehicle_number }}</li><li style='padding: 5px 0;'><strong>🔧 Service:</strong> {{ doc.service_type }}</li><li style='padding: 5px 0; font-size: 18px; color: #2E86AB;'><strong>💰 Total Amount:</strong> OMR {{ doc.total_amount }}</li><li style='padding: 5px 0;'><strong>📅 Due Date:</strong> {{ doc.due_date }}</li></ul></div>{% if doc.payment_link %}<div style='text-align: center; margin: 30px 0;'><a href='{{ doc.payment_link }}' style='background: #2E86AB; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;'>Pay Online</a></div>{% endif %}<p>For any questions, please contact us at {{ doc.workshop_phone }}.</p><p>Thank you for your business!</p><hr style='margin: 30px 0;'/><p style='color: #666; font-size: 12px;'>{{ doc.workshop_name }}<br/>This is an automated message.</p></div>",
            "max_length": 10000,
            "approval_status": "Approved",
            "preview_context": {
                "customer_name": "Ahmed Al-Saadi",
                "invoice_number": "INV-2025-001",
                "vehicle_number": "AB-1234",
                "service_type": "Oil Change",
                "total_amount": "25.500",
                "due_date": "30/01/2025",
                "payment_link": "https://workshop.om/pay/INV-2025-001",
                "workshop_phone": "+968 24123456",
                "workshop_name": "Gulf Universal Workshop",
            },
        },
    ]

    for template_data in email_templates:
        create_template_if_not_exists(template_data)


def create_template_if_not_exists(template_data):
    """Create template if it doesn't already exist"""

    template_name = template_data["template_name"]

    if frappe.db.exists("Notification Template", template_name):
        print(f"Template {template_name} already exists, skipping...")
        return

    try:
        # Create new template document
        template = frappe.new_doc("Notification Template")

        # Set basic fields
        template.template_name = template_name
        template.channel_type = template_data["channel_type"]
        template.language = template_data["language"]
        template.template_category = template_data["template_category"]
        template.template_body = template_data["template_body"]
        template.max_length = template_data["max_length"]
        template.approval_status = template_data["approval_status"]
        template.is_active = 1
        template.version = 1

        # Set optional fields
        if "template_subject" in template_data:
            template.template_subject = template_data["template_subject"]

        if "preview_context" in template_data:
            template.preview_context_json = json.dumps(template_data["preview_context"], indent=2)

        # Set creator
        template.created_by = "Administrator"
        template.approved_by = "Administrator"
        template.approved_on = frappe.utils.now()

        # Insert template
        template.insert(ignore_permissions=True)

        print(f"Created template: {template_name}")

    except Exception as e:
        frappe.log_error(f"Failed to create template {template_name}: {str(e)}")
        print(f"Failed to create template {template_name}: {str(e)}")


def setup_template_permissions():
    """Set up role permissions for notification templates"""

    roles_permissions = [
        {
            "role": "Workshop Manager",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
        {
            "role": "System Manager",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
        {
            "role": "Workshop Staff",
            "permlevel": 0,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
    ]

    for perm in roles_permissions:
        if not frappe.db.exists(
            "Custom DocPerm",
            {
                "parent": "Notification Template",
                "role": perm["role"],
                "permlevel": perm["permlevel"],
            },
        ):
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "Notification Template",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    **perm,
                }
            ).insert(ignore_permissions=True)


if __name__ == "__main__":
    setup_notification_templates()
