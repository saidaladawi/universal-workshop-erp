# -*- coding: utf-8 -*-
"""
Template API Module
Provides endpoints for template management, testing, and integration
"""

import json
import frappe
from frappe import _
from typing import Dict, Any, List, Optional
from universal_workshop.communication_management.doctype.notification_template.notification_template import (
    NotificationTemplate,
)


@frappe.whitelist()
def get_default_template(
    category: str, channel_type: str, language: str = "English"
) -> Dict[str, Any]:
    """
    Get default template structure for a given category and channel

    Args:
        category: Template category (e.g., "Appointment Confirmation")
        channel_type: Communication channel (SMS/WhatsApp/Email)
        language: Template language (English/Arabic)

    Returns:
        Dictionary with template body, subject, and preview context
    """
    try:
        templates = get_default_templates()

        key = f"{category}_{channel_type}_{language}"
        if key in templates:
            template_data = templates[key].copy()

            # Add appropriate preview context
            template_data["preview_context"] = get_preview_context_for_category(category, language)

            return template_data

        # Fallback to basic template structure
        return {
            "template_body": get_basic_template_structure(category, channel_type, language),
            "template_subject": (
                get_default_subject(category, language) if channel_type == "Email" else None
            ),
            "preview_context": get_preview_context_for_category(category, language),
        }

    except Exception as e:
        frappe.log_error(f"Error getting default template: {str(e)}")
        return {"error": str(e)}


def get_default_templates() -> Dict[str, Dict[str, str]]:
    """Get comprehensive collection of default templates"""

    return {
        # Appointment Confirmation Templates
        "Appointment Confirmation_SMS_English": {
            "template_body": "Dear {{ doc.customer_name }}, your appointment at {{ doc.workshop_name }} is confirmed for {{ doc.appointment_date }} at {{ doc.appointment_time }} for {{ doc.service_type }}. Vehicle: {{ doc.vehicle_number }}. Call {{ doc.workshop_phone }} for changes."
        },
        "Appointment Confirmation_SMS_Arabic": {
            "template_body": "عزيزي {{ doc.customer_name_ar }}، تم تأكيد موعدك في {{ doc.workshop_name }} بتاريخ {{ doc.appointment_date }} في {{ doc.appointment_time }} لخدمة {{ doc.service_type }}. المركبة: {{ doc.vehicle_number }}. للتغييرات اتصل {{ doc.workshop_phone }}"
        },
        "Appointment Confirmation_WhatsApp_English": {
            "template_body": "✅ *Appointment Confirmed*\n\nDear {{ doc.customer_name }},\n\nYour service appointment has been confirmed:\n\n📅 Date: {{ doc.appointment_date }}\n⏰ Time: {{ doc.appointment_time }}\n🔧 Service: {{ doc.service_type }}\n🚗 Vehicle: {{ doc.vehicle_number }}\n\n📍 Workshop: {{ doc.workshop_name }}\n📞 Contact: {{ doc.workshop_phone }}\n\nPlease arrive 15 minutes early. Thank you!"
        },
        "Appointment Confirmation_WhatsApp_Arabic": {
            "template_body": "✅ *تأكيد الموعد*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nتم تأكيد موعد الخدمة:\n\n📅 التاريخ: {{ doc.appointment_date }}\n⏰ الوقت: {{ doc.appointment_time }}\n🔧 الخدمة: {{ doc.service_type }}\n🚗 المركبة: {{ doc.vehicle_number }}\n\n📍 الورشة: {{ doc.workshop_name }}\n📞 الهاتف: {{ doc.workshop_phone }}\n\nالرجاء الحضور قبل 15 دقيقة. شكراً لك!"
        },
        "Appointment Confirmation_Email_English": {
            "template_subject": "Appointment Confirmed - {{ doc.service_type }}",
            "template_body": "<h2>Appointment Confirmation</h2><p>Dear {{ doc.customer_name }},</p><p>Your service appointment has been confirmed with the following details:</p><ul><li><strong>Date:</strong> {{ doc.appointment_date }}</li><li><strong>Time:</strong> {{ doc.appointment_time }}</li><li><strong>Service:</strong> {{ doc.service_type }}</li><li><strong>Vehicle:</strong> {{ doc.vehicle_number }}</li></ul><p><strong>Workshop Details:</strong><br/>{{ doc.workshop_name }}<br/>Phone: {{ doc.workshop_phone }}</p><p>Please arrive 15 minutes early for check-in.</p><p>Thank you for choosing our services!</p>",
        },
        # Service Completion Templates
        "Service Completion_SMS_English": {
            "template_body": "Service completed for {{ doc.vehicle_number }}! {{ doc.service_type }} finished. Total: OMR {{ doc.total_amount }}. Invoice: {{ doc.invoice_number }}. Collect your vehicle at {{ doc.workshop_name }}. Thank you!"
        },
        "Service Completion_SMS_Arabic": {
            "template_body": "تم إنجاز الخدمة للمركبة {{ doc.vehicle_number }}! انتهت خدمة {{ doc.service_type }}. المجموع: {{ doc.total_amount }} ر.ع. الفاتورة: {{ doc.invoice_number }}. استلم مركبتك من {{ doc.workshop_name }}. شكراً!"
        },
        "Service Completion_WhatsApp_English": {
            "template_body": "🎉 *Service Completed!*\n\nDear {{ doc.customer_name }},\n\nGreat news! Your vehicle service is complete:\n\n🚗 Vehicle: {{ doc.vehicle_number }}\n🔧 Service: {{ doc.service_type }}\n💰 Total Amount: OMR {{ doc.total_amount }}\n📄 Invoice: {{ doc.invoice_number }}\n\nYour vehicle is ready for collection at {{ doc.workshop_name }}.\n\nThank you for trusting us with your vehicle! 🚗✨"
        },
        "Service Completion_WhatsApp_Arabic": {
            "template_body": "🎉 *تم إنجاز الخدمة!*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nأخبار رائعة! تم إنجاز خدمة مركبتك:\n\n🚗 المركبة: {{ doc.vehicle_number }}\n🔧 الخدمة: {{ doc.service_type }}\n💰 المبلغ الإجمالي: {{ doc.total_amount }} ر.ع\n📄 الفاتورة: {{ doc.invoice_number }}\n\nمركبتك جاهزة للاستلام من {{ doc.workshop_name }}.\n\nشكراً لثقتك بخدماتنا! 🚗✨"
        },
        # Payment Reminder Templates
        "Payment Reminder_SMS_English": {
            "template_body": "Payment reminder: Invoice {{ doc.invoice_number }} for OMR {{ doc.total_amount }} is {{ doc.days_overdue }} days overdue. Please settle by {{ doc.due_date }}. Contact {{ doc.workshop_phone }}."
        },
        "Payment Reminder_SMS_Arabic": {
            "template_body": "تذكير دفع: الفاتورة {{ doc.invoice_number }} بمبلغ {{ doc.total_amount }} ر.ع متأخرة {{ doc.days_overdue }} أيام. الرجاء السداد قبل {{ doc.due_date }}. اتصل {{ doc.workshop_phone }}"
        },
        "Payment Reminder_WhatsApp_English": {
            "template_body": "💳 *Payment Reminder*\n\nDear {{ doc.customer_name }},\n\nThis is a friendly reminder about your outstanding invoice:\n\n📄 Invoice: {{ doc.invoice_number }}\n💰 Amount: OMR {{ doc.total_amount }}\n📅 Due Date: {{ doc.due_date }}\n⏰ Days Overdue: {{ doc.days_overdue }}\n\nPlease settle this amount at your earliest convenience.\n\n📞 Contact us: {{ doc.workshop_phone }}\n\nThank you for your cooperation!"
        },
        "Payment Reminder_WhatsApp_Arabic": {
            "template_body": "💳 *تذكير دفع*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nهذا تذكير ودي بشأن فاتورتك المستحقة:\n\n📄 الفاتورة: {{ doc.invoice_number }}\n💰 المبلغ: {{ doc.total_amount }} ر.ع\n📅 تاريخ الاستحقاق: {{ doc.due_date }}\n⏰ أيام التأخير: {{ doc.days_overdue }}\n\nالرجاء سداد هذا المبلغ في أقرب وقت ممكن.\n\n📞 اتصل بنا: {{ doc.workshop_phone }}\n\nشكراً لتعاونك!"
        },
        # Quotation Templates
        "Quotation_WhatsApp_English": {
            "template_body": "📋 *Service Quotation*\n\nDear {{ doc.customer_name }},\n\nQuotation for your vehicle {{ doc.vehicle_number }}:\n\n{{ doc.services_list }}\n\n💰 Total Amount: OMR {{ doc.total_amount }}\n📄 Quotation: {{ doc.quotation_number }}\n⏰ Valid Until: {{ doc.valid_until }}\n\nApprove to schedule your service!\n\n📞 {{ doc.workshop_phone }}"
        },
        "Quotation_WhatsApp_Arabic": {
            "template_body": "📋 *عرض أسعار الخدمة*\n\nعزيزي {{ doc.customer_name_ar }}،\n\nعرض أسعار لمركبتك {{ doc.vehicle_number }}:\n\n{{ doc.services_list }}\n\n💰 المبلغ الإجمالي: {{ doc.total_amount }} ر.ع\n📄 العرض: {{ doc.quotation_number }}\n⏰ صالح حتى: {{ doc.valid_until }}\n\nوافق لجدولة خدمتك!\n\n📞 {{ doc.workshop_phone }}"
        },
    }


def get_basic_template_structure(category: str, channel_type: str, language: str) -> str:
    """Generate basic template structure for custom categories"""

    if language == "Arabic":
        base_greeting = "عزيزي {{ doc.customer_name_ar }}،"
        workshop_signature = "\n\n{{ doc.workshop_name }}\n{{ doc.workshop_phone }}"
    else:
        base_greeting = "Dear {{ doc.customer_name }},"
        workshop_signature = "\n\nBest regards,\n{{ doc.workshop_name }}\n{{ doc.workshop_phone }}"

    if channel_type == "SMS":
        return f"{base_greeting} [Your message here]{workshop_signature}"
    elif channel_type == "WhatsApp":
        return f"{base_greeting}\n\n[Your message content here]{workshop_signature}"
    else:  # Email
        return (
            f"<p>{base_greeting}</p><p>[Your message content here]</p><p>{workshop_signature}</p>"
        )


def get_default_subject(category: str, language: str) -> str:
    """Get default email subject for category"""

    subjects = {
        "English": {
            "Appointment Confirmation": "Service Appointment Confirmed",
            "Appointment Reminder": "Service Appointment Reminder",
            "Service Update": "Service Update for Your Vehicle",
            "Service Completion": "Service Completed - Vehicle Ready",
            "Invoice Notification": "Invoice for Service",
            "Payment Reminder": "Payment Reminder",
            "Quotation": "Service Quotation",
        },
        "Arabic": {
            "Appointment Confirmation": "تأكيد موعد الخدمة",
            "Appointment Reminder": "تذكير موعد الخدمة",
            "Service Update": "تحديث حالة الخدمة",
            "Service Completion": "انتهاء الخدمة - المركبة جاهزة",
            "Invoice Notification": "فاتورة الخدمة",
            "Payment Reminder": "تذكير دفع",
            "Quotation": "عرض أسعار الخدمة",
        },
    }

    return subjects.get(language, {}).get(category, f"Notification - {category}")


def get_preview_context_for_category(category: str, language: str) -> Dict[str, Any]:
    """Get appropriate preview context for template category"""

    base_context = {
        "customer_name": "أحمد محمد السعدي" if language == "Arabic" else "Ahmed Mohammed Al-Saadi",
        "customer_name_ar": "أحمد محمد السعدي",
        "workshop_name": (
            "ورشة الخليج العالمية" if language == "Arabic" else "Gulf Universal Workshop"
        ),
        "workshop_phone": "+968 24 123456",
        "current_date": frappe.utils.format_date(frappe.utils.today(), "dd/MM/yyyy"),
        "current_time": frappe.utils.format_time(frappe.utils.nowtime()),
    }

    category_contexts = {
        "Appointment Confirmation": {
            "appointment_date": "15/01/2025",
            "appointment_time": "10:00 صباحاً" if language == "Arabic" else "10:00 AM",
            "service_type": "صيانة دورية" if language == "Arabic" else "Regular Maintenance",
            "vehicle_number": "AB-1234",
        },
        "Service Completion": {
            "vehicle_number": "AB-1234",
            "service_type": "تغيير الزيت" if language == "Arabic" else "Oil Change",
            "total_amount": "25.500",
            "invoice_number": "INV-2025-001",
        },
        "Payment Reminder": {
            "invoice_number": "INV-2025-001",
            "total_amount": "25.500",
            "days_overdue": "5",
            "due_date": "30/01/2025",
        },
        "Quotation": {
            "quotation_number": "QTN-2025-001",
            "vehicle_number": "AB-1234",
            "services_list": (
                "• تغيير الزيت\n• فحص الفرامل"
                if language == "Arabic"
                else "• Oil Change\n• Brake Inspection"
            ),
            "total_amount": "45.750",
            "valid_until": "20/01/2025",
        },
    }

    context = base_context.copy()
    context.update(category_contexts.get(category, {}))
    return context


@frappe.whitelist()
def test_template(
    template_name: str, phone_number: str, context_data: str = "{}"
) -> Dict[str, Any]:
    """
    Test a template by sending actual message

    Args:
        template_name: Name of the notification template
        phone_number: Test phone number
        context_data: JSON string with context data

    Returns:
        Dictionary with success status and message ID or error
    """
    try:
        # Get template
        template = frappe.get_doc("Notification Template", template_name)
        if not template:
            return {"success": False, "error": "Template not found"}

        if template.approval_status != "Approved":
            return {"success": False, "error": "Template not approved for testing"}

        # Parse context
        try:
            context = json.loads(context_data)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid context data JSON"}

        # Render template
        rendered_message = template.render_template_with_context(context)

        # Send test message based on channel type
        if template.channel_type == "SMS":
            from universal_workshop.communication_management.api.sms_api import send_sms_message

            result = send_sms_message(
                phone_number=phone_number, message=rendered_message, message_type="test"
            )
        elif template.channel_type == "WhatsApp":
            from universal_workshop.communication_management.api.whatsapp_api import (
                send_whatsapp_message,
            )

            result = send_whatsapp_message(
                phone_number=phone_number, message=rendered_message, message_type="test"
            )
        else:
            return {"success": False, "error": "Email testing not supported via this endpoint"}

        if result.get("success"):
            # Log test usage
            template.increment_usage_count()
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "rendered_message": rendered_message,
            }
        else:
            return {"success": False, "error": result.get("error", "Failed to send test message")}

    except Exception as e:
        frappe.log_error(f"Template test error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_template_usage_stats(template_name: str = None) -> Dict[str, Any]:
    """
    Get usage statistics for templates

    Args:
        template_name: Optional specific template name

    Returns:
        Dictionary with usage statistics
    """
    try:
        if template_name:
            # Get stats for specific template
            template = frappe.get_doc("Notification Template", template_name)
            return {
                "template_name": template.template_name,
                "usage_count": template.usage_count or 0,
                "error_count": template.error_count or 0,
                "last_used": template.last_used,
                "success_rate": calculate_success_rate(template.usage_count, template.error_count),
            }
        else:
            # Get summary stats for all templates
            templates = frappe.get_all(
                "Notification Template",
                fields=[
                    "name",
                    "template_name",
                    "channel_type",
                    "language",
                    "usage_count",
                    "error_count",
                    "last_used",
                    "approval_status",
                ],
                filters={"is_active": 1},
            )

            total_usage = sum(t.get("usage_count", 0) for t in templates)
            total_errors = sum(t.get("error_count", 0) for t in templates)

            return {
                "total_templates": len(templates),
                "total_usage": total_usage,
                "total_errors": total_errors,
                "overall_success_rate": calculate_success_rate(total_usage, total_errors),
                "templates": [
                    {
                        **t,
                        "success_rate": calculate_success_rate(
                            t.get("usage_count", 0), t.get("error_count", 0)
                        ),
                    }
                    for t in templates
                ],
            }

    except Exception as e:
        frappe.log_error(f"Template stats error: {str(e)}")
        return {"error": str(e)}


def calculate_success_rate(usage_count: int, error_count: int) -> float:
    """Calculate success rate percentage"""
    if not usage_count:
        return 0.0
    return round(((usage_count - error_count) / usage_count) * 100, 2)


@frappe.whitelist()
def search_templates(
    search_term: str, channel_type: str = None, language: str = None
) -> List[Dict[str, Any]]:
    """
    Search templates by name, category, or content

    Args:
        search_term: Search term
        channel_type: Optional channel filter
        language: Optional language filter

    Returns:
        List of matching templates
    """
    try:
        filters = {"is_active": 1}

        if channel_type:
            filters["channel_type"] = channel_type
        if language:
            filters["language"] = language

        # Search in multiple fields
        or_filters = [
            {"template_name": ["like", f"%{search_term}%"]},
            {"template_category": ["like", f"%{search_term}%"]},
            {"template_body": ["like", f"%{search_term}%"]},
        ]

        templates = frappe.get_all(
            "Notification Template",
            fields=[
                "name",
                "template_name",
                "template_category",
                "channel_type",
                "language",
                "approval_status",
                "usage_count",
                "last_used",
            ],
            filters=filters,
            or_filters=or_filters,
            limit=20,
        )

        return templates

    except Exception as e:
        frappe.log_error(f"Template search error: {str(e)}")
        return []


@frappe.whitelist()
def duplicate_template(
    source_template: str, new_name: str, new_language: str = None
) -> Dict[str, Any]:
    """
    Duplicate an existing template with optional language change

    Args:
        source_template: Name of template to duplicate
        new_name: Name for new template
        new_language: Optional new language

    Returns:
        Dictionary with new template details or error
    """
    try:
        # Get source template
        source = frappe.get_doc("Notification Template", source_template)

        # Create new template
        new_template = frappe.new_doc("Notification Template")

        # Copy fields
        copy_fields = [
            "channel_type",
            "language",
            "template_category",
            "template_subject",
            "template_body",
            "conditional_logic",
            "max_length",
        ]

        for field in copy_fields:
            new_template.set(field, source.get(field))

        # Set new values
        new_template.template_name = new_name
        if new_language:
            new_template.language = new_language

        # Reset status fields
        new_template.approval_status = "Draft"
        new_template.version = 1
        new_template.usage_count = 0
        new_template.error_count = 0

        new_template.insert()

        return {
            "success": True,
            "new_template": new_template.name,
            "message": f"Template duplicated successfully as '{new_name}'",
        }

    except Exception as e:
        frappe.log_error(f"Template duplication error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_template_categories() -> List[str]:
    """Get list of available template categories"""
    try:
        # Get categories from DocType options
        meta = frappe.get_meta("Notification Template")
        category_field = next((f for f in meta.fields if f.fieldname == "template_category"), None)

        if category_field and category_field.options:
            return [cat.strip() for cat in category_field.options.split("\n") if cat.strip()]

        # Fallback categories
        return [
            "Appointment Confirmation",
            "Appointment Reminder",
            "Service Update",
            "Service Completion",
            "Invoice Notification",
            "Payment Reminder",
            "Quotation",
            "Promotion",
            "General",
        ]

    except Exception as e:
        frappe.log_error(f"Error getting categories: {str(e)}")
        return []
