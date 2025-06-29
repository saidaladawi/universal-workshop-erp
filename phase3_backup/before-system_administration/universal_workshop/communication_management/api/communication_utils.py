# -*- coding: utf-8 -*-
"""
Communication Utilities for Universal Workshop ERP
Helper functions for Arabic RTL support and Oman-specific features
"""

import frappe
from frappe import _
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime, time


@frappe.whitelist()
def get_customer_communication_preference(customer_id: str) -> Dict[str, any]:
    """
    Get customer's communication preferences (language, channels, timing)

    Args:
        customer_id (str): Customer document ID

    Returns:
        Dict: Communication preferences
    """
    try:
        customer = frappe.get_doc("Customer", customer_id)

        # Default preferences for Oman market
        preferences = {
            "preferred_language": "ar",  # Default to Arabic
            "sms_enabled": True,
            "whatsapp_enabled": True,
            "email_enabled": True,
            "preferred_time_start": "09:00",
            "preferred_time_end": "20:00",
            "timezone": "Asia/Muscat",
        }

        # Override with customer-specific preferences if available
        if hasattr(customer, "preferred_language"):
            preferences["preferred_language"] = customer.preferred_language or "ar"
        if hasattr(customer, "sms_notifications"):
            preferences["sms_enabled"] = customer.sms_notifications
        if hasattr(customer, "whatsapp_notifications"):
            preferences["whatsapp_enabled"] = customer.whatsapp_notifications
        if hasattr(customer, "email_notifications"):
            preferences["email_enabled"] = customer.email_notifications

        # Add contact information
        preferences["mobile_no"] = customer.mobile_no
        preferences["phone"] = customer.phone
        preferences["email_id"] = customer.email_id

        return preferences

    except Exception as e:
        frappe.log_error(f"Error getting communication preferences: {str(e)}")
        return {
            "preferred_language": "ar",
            "sms_enabled": True,
            "whatsapp_enabled": True,
            "email_enabled": True,
        }


@frappe.whitelist()
def format_arabic_message(message: str, customer_name: str = None) -> str:
    """
    Format message with proper Arabic RTL formatting and polite Omani greetings

    Args:
        message (str): Base message content
        customer_name (str): Customer name for personalization

    Returns:
        str: Formatted Arabic message
    """
    try:
        # Arabic greeting patterns
        if customer_name:
            # Polite Arabic greeting
            if detect_arabic_text(customer_name):
                greeting = f"السلام عليكم {customer_name}،"
            else:
                greeting = f"السلام عليكم أستاذ {customer_name}،"
        else:
            greeting = "السلام عليكم،"

        # Add proper RTL formatting
        formatted_message = f"{greeting}\n\n{message}\n\nمع أطيب التحيات،\nورشة الخليج للسيارات"

        return formatted_message

    except Exception as e:
        frappe.log_error(f"Error formatting Arabic message: {str(e)}")
        return message


@frappe.whitelist()
def format_english_message(message: str, customer_name: str = None) -> str:
    """
    Format message with proper English formatting and Omani business etiquette

    Args:
        message (str): Base message content
        customer_name (str): Customer name for personalization

    Returns:
        str: Formatted English message
    """
    try:
        # English greeting patterns
        if customer_name:
            greeting = f"Dear Mr./Ms. {customer_name},"
        else:
            greeting = "Dear Valued Customer,"

        # Add proper business formatting
        formatted_message = f"{greeting}\n\n{message}\n\nBest regards,\nAl Khaleej Auto Workshop"

        return formatted_message

    except Exception as e:
        frappe.log_error(f"Error formatting English message: {str(e)}")
        return message


def detect_arabic_text(text: str) -> bool:
    """
    Detect if text contains Arabic characters

    Args:
        text (str): Text to analyze

    Returns:
        bool: True if Arabic characters detected
    """
    if not text:
        return False

    arabic_pattern = re.compile(
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
    )
    return bool(arabic_pattern.search(text))


@frappe.whitelist()
def check_oman_business_hours() -> Dict[str, any]:
    """
    Check if current time is within Oman business hours for communication

    Returns:
        Dict: Business hours status and information
    """
    try:
        from frappe.utils import now_datetime, get_time
        import pytz

        # Oman timezone
        oman_tz = pytz.timezone("Asia/Muscat")
        current_time = now_datetime().astimezone(oman_tz)
        current_hour = current_time.hour

        # Business hours (7 AM to 9 PM for promotional messages)
        business_start = 7
        business_end = 21

        is_business_hours = business_start <= current_hour < business_end

        # Check if it's a working day (Sunday to Thursday in Oman)
        weekday = current_time.weekday()  # Monday = 0, Sunday = 6
        is_working_day = weekday in [6, 0, 1, 2, 3]  # Sunday(6) to Thursday(3)

        return {
            "is_business_hours": is_business_hours,
            "is_working_day": is_working_day,
            "current_time": current_time.strftime("%H:%M"),
            "current_day": current_time.strftime("%A"),
            "business_hours": f"{business_start:02d}:00 - {business_end:02d}:00",
            "working_days": "Sunday to Thursday",
            "can_send_promotional": is_business_hours and is_working_day,
            "can_send_transactional": True,  # Transactional messages allowed anytime
        }

    except Exception as e:
        frappe.log_error(f"Error checking business hours: {str(e)}")
        return {
            "is_business_hours": True,
            "is_working_day": True,
            "can_send_promotional": True,
            "can_send_transactional": True,
        }


@frappe.whitelist()
def get_communication_history(customer_id: str, limit: int = 50) -> List[Dict]:
    """
    Get communication history for a customer

    Args:
        customer_id (str): Customer ID
        limit (int): Number of records to retrieve

    Returns:
        List[Dict]: Communication history
    """
    try:
        communications = frappe.get_list(
            "Communication",
            filters={"reference_doctype": "Customer", "reference_name": customer_id},
            fields=[
                "name",
                "communication_medium",
                "sender",
                "recipients",
                "subject",
                "content",
                "status",
                "creation",
                "communication_date",
            ],
            order_by="creation desc",
            limit=limit,
        )

        return communications

    except Exception as e:
        frappe.log_error(f"Error getting communication history: {str(e)}")
        return []


@frappe.whitelist()
def send_multilingual_notification(
    customer_id: str, template_type: str, context_data: Dict, channels: List[str] = None
) -> Dict[str, any]:
    """
    Send notification in customer's preferred language across multiple channels

    Args:
        customer_id (str): Customer ID
        template_type (str): Type of notification (appointment, invoice, etc.)
        context_data (Dict): Data for template rendering
        channels (List[str]): Communication channels to use

    Returns:
        Dict: Send results across all channels
    """
    try:
        # Get customer preferences
        preferences = get_customer_communication_preference(customer_id)
        language = preferences.get("preferred_language", "ar")

        # Default channels if not specified
        if not channels:
            channels = []
            if preferences.get("sms_enabled"):
                channels.append("sms")
            if preferences.get("whatsapp_enabled"):
                channels.append("whatsapp")
            if preferences.get("email_enabled"):
                channels.append("email")

        results = {
            "customer_id": customer_id,
            "language": language,
            "channels_attempted": channels,
            "results": {},
        }

        # Send via each channel
        for channel in channels:
            try:
                if channel == "sms":
                    result = send_template_sms(customer_id, template_type, context_data, language)
                elif channel == "whatsapp":
                    result = send_template_whatsapp(
                        customer_id, template_type, context_data, language
                    )
                elif channel == "email":
                    result = send_template_email(customer_id, template_type, context_data, language)
                else:
                    result = {"success": False, "error": f"Unknown channel: {channel}"}

                results["results"][channel] = result

            except Exception as e:
                results["results"][channel] = {"success": False, "error": str(e)}

        return results

    except Exception as e:
        frappe.log_error(f"Error sending multilingual notification: {str(e)}")
        return {"success": False, "error": str(e)}


def send_template_sms(
    customer_id: str, template_type: str, context_data: Dict, language: str
) -> Dict:
    """Send SMS using template"""
    try:
        from .sms_api import send_sms_message

        # Get customer phone
        customer = frappe.get_doc("Customer", customer_id)
        phone = customer.mobile_no or customer.phone

        if not phone:
            return {"success": False, "error": "No phone number"}

        # Get template and render message
        template_name = f"{template_type}_sms_{language}"
        message = render_message_template(template_name, context_data, language)

        # Send SMS
        return send_sms_message(phone, message, customer_id, template_name)

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_template_whatsapp(
    customer_id: str, template_type: str, context_data: Dict, language: str
) -> Dict:
    """Send WhatsApp using template"""
    try:
        from .whatsapp_api import send_whatsapp_message

        # Get customer phone
        customer = frappe.get_doc("Customer", customer_id)
        phone = customer.mobile_no or customer.phone

        if not phone:
            return {"success": False, "error": "No phone number"}

        # Send WhatsApp
        template_name = f"{template_type}_{language}"
        return send_whatsapp_message(phone, template_name, context_data, customer_id, language)

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_template_email(
    customer_id: str, template_type: str, context_data: Dict, language: str
) -> Dict:
    """Send Email using template"""
    try:
        # Get customer email
        customer = frappe.get_doc("Customer", customer_id)
        email = customer.email_id

        if not email:
            return {"success": False, "error": "No email address"}

        # This would integrate with Frappe's email system
        # For now, return success placeholder
        return {"success": True, "message": "Email sent (placeholder)"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def render_message_template(template_name: str, context_data: Dict, language: str) -> str:
    """Render message template with context data"""
    try:
        # Get template content
        template_content = get_message_template(template_name, language)

        if not template_content:
            # Fallback to default template
            return get_default_message(template_name, context_data, language)

        # Simple template rendering
        rendered = template_content
        for key, value in context_data.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

        # Format based on language
        customer_name = context_data.get("customer_name", "")
        if language == "ar":
            return format_arabic_message(rendered, customer_name)
        else:
            return format_english_message(rendered, customer_name)

    except Exception as e:
        frappe.log_error(f"Error rendering template: {str(e)}")
        return get_default_message(template_name, context_data, language)


def get_message_template(template_name: str, language: str) -> str:
    """Get message template from database"""
    try:
        # Try to get from Message Template DocType
        if frappe.db.exists("DocType", "Message Template"):
            template = frappe.db.get_value(
                "Message Template",
                {"template_name": template_name, "language": language},
                "template_content",
            )
            return template

        return None

    except Exception:
        return None


def get_default_message(template_name: str, context_data: Dict, language: str) -> str:
    """Get default fallback message"""
    customer_name = context_data.get("customer_name", "")

    if language == "ar":
        if "appointment" in template_name:
            return f"عزيزنا {customer_name}، تذكير بموعد الخدمة. شكراً لك."
        elif "invoice" in template_name:
            return f"عزيزنا {customer_name}، تم إرسال الفاتورة. شكراً لك."
        else:
            return f"عزيزنا {customer_name}، شكراً لتعاملكم معنا."
    else:
        if "appointment" in template_name:
            return f"Dear {customer_name}, appointment reminder. Thank you."
        elif "invoice" in template_name:
            return f"Dear {customer_name}, invoice has been sent. Thank you."
        else:
            return f"Dear {customer_name}, thank you for your business."


@frappe.whitelist()
def validate_oman_communication_compliance(
    message_type: str, content: str, recipient_phone: str = None
) -> Dict[str, any]:
    """
    Validate communication compliance for Oman/UAE regulations

    Args:
        message_type (str): Type of message (promotional, transactional)
        content (str): Message content
        recipient_phone (str): Recipient phone number

    Returns:
        Dict: Compliance validation result
    """
    try:
        from ..oman_twilio_client import get_twilio_client

        client = get_twilio_client()

        # Determine target country
        target_country = "OM"  # Default to Oman
        if recipient_phone and recipient_phone.startswith("+971"):
            target_country = "AE"  # UAE

        # Validate content compliance
        is_compliant, violations = client.validate_content_compliance(content, target_country)

        # Check business hours for promotional messages
        business_hours_check = check_oman_business_hours()
        can_send_now = (
            business_hours_check.get("can_send_promotional")
            if message_type == "promotional"
            else True
        )

        result = {
            "is_compliant": is_compliant and can_send_now,
            "content_violations": violations,
            "business_hours_compliant": can_send_now,
            "target_country": target_country,
            "message_type": message_type,
            "current_time_info": business_hours_check,
        }

        if not can_send_now and message_type == "promotional":
            result["timing_violation"] = "Promotional messages not allowed outside business hours"

        return result

    except Exception as e:
        frappe.log_error(f"Error validating compliance: {str(e)}")
        return {"is_compliant": False, "error": str(e)}
