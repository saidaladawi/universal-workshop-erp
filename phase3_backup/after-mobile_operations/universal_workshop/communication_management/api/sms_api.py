# -*- coding: utf-8 -*-
"""
SMS API Methods for Universal Workshop ERP
WhiteListed methods for sending SMS with Oman regulatory compliance
"""

import frappe
from frappe import _
from typing import Dict, List, Optional
from ..oman_twilio_client import get_twilio_client


@frappe.whitelist()
def send_sms_message(
    to: str, message: str, customer_id: str = None, template_name: str = None
) -> Dict[str, any]:
    """
    Send SMS message with Oman compliance validation

    Args:
        to (str): Phone number in Oman format
        message (str): SMS content (Arabic/English supported)
        customer_id (str, optional): Customer reference
        template_name (str, optional): Template used for tracking

    Returns:
        Dict: Result with success status and details
    """
    try:
        # Get Twilio client
        client = get_twilio_client()

        # Send SMS
        result = client.send_sms(
            to=to, message=message, customer_id=customer_id, template_name=template_name
        )

        return result

    except Exception as e:
        frappe.log_error(f"SMS API Error: {str(e)}", "SMS Send API")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_bulk_sms(recipients_json: str, message: str, template_name: str = None) -> Dict[str, any]:
    """
    Send bulk SMS messages with rate limiting

    Args:
        recipients_json (str): JSON string of recipients list
        message (str): SMS content
        template_name (str, optional): Template name for tracking

    Returns:
        Dict: Bulk send results
    """
    try:
        import json

        # Parse recipients
        recipients = json.loads(recipients_json)

        # Prepare bulk data
        bulk_data = []
        for recipient in recipients:
            bulk_data.append(
                {
                    "phone": recipient.get("phone"),
                    "message": message,
                    "customer_id": recipient.get("customer_id"),
                    "context": recipient.get("context", {}),
                }
            )

        # Get Twilio client
        client = get_twilio_client()

        # Send bulk SMS
        result = client.bulk_send_sms(bulk_data, template_name)

        return result

    except Exception as e:
        frappe.log_error(f"Bulk SMS API Error: {str(e)}", "Bulk SMS Send API")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_phone_number(phone: str) -> Dict[str, any]:
    """
    Validate Oman phone number format

    Args:
        phone (str): Phone number to validate

    Returns:
        Dict: Validation result with formatted number
    """
    try:
        client = get_twilio_client()
        is_valid, formatted_phone = client.validate_oman_phone_number(phone)

        return {"is_valid": is_valid, "formatted_phone": formatted_phone, "original_phone": phone}

    except Exception as e:
        return {"is_valid": False, "error": str(e)}


@frappe.whitelist()
def calculate_sms_cost(message: str) -> Dict[str, any]:
    """
    Calculate SMS segments and estimated cost

    Args:
        message (str): SMS content

    Returns:
        Dict: Segment information and cost estimation
    """
    try:
        client = get_twilio_client()
        segment_info = client.calculate_sms_segments(message)

        # Add cost estimation (example rates)
        cost_per_segment = 0.05  # OMR per segment - adjust based on actual rates
        estimated_cost = segment_info["total_segments"] * cost_per_segment

        segment_info["estimated_cost_omr"] = estimated_cost
        segment_info["cost_per_segment"] = cost_per_segment

        return segment_info

    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_sms_delivery_status(message_id: str) -> Dict[str, any]:
    """
    Get delivery status for sent SMS

    Args:
        message_id (str): Twilio message ID

    Returns:
        Dict: Delivery status information
    """
    try:
        client = get_twilio_client()
        status_info = client.get_delivery_status(message_id)

        return status_info

    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def send_appointment_reminder_sms(appointment_id: str, language: str = "ar") -> Dict[str, any]:
    """
    Send appointment reminder SMS (Workshop-specific)

    Args:
        appointment_id (str): Service Appointment ID
        language (str): Language preference ('ar' or 'en')

    Returns:
        Dict: Send result
    """
    try:
        # Get appointment details
        appointment = frappe.get_doc("Service Appointment", appointment_id)
        customer = frappe.get_doc("Customer", appointment.customer)

        # Get customer phone
        phone = customer.mobile_no or customer.phone
        if not phone:
            return {"success": False, "error": _("Customer phone number not found")}

        # Prepare message context
        context = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "service_type": appointment.service_type,
        }

        # Get message template
        template_name = f"appointment_reminder_{language}"
        template = get_sms_template(template_name)

        if not template:
            # Fallback message
            if language == "ar":
                message = _(
                    "مرحباً {customer_name}، نذكركم بموعد الخدمة في {appointment_date} الساعة {appointment_time}. ورشة {workshop_name}"
                ).format(**context)
            else:
                message = _(
                    "Hello {customer_name}, reminder for your service appointment on {appointment_date} at {appointment_time}. {workshop_name}"
                ).format(**context)
        else:
            message = render_sms_template(template, context)

        # Send SMS
        result = send_sms_message(
            to=phone, message=message, customer_id=customer.name, template_name=template_name
        )

        # Update appointment with notification sent flag
        if result.get("success"):
            appointment.reminder_sent = 1
            appointment.reminder_sent_at = frappe.utils.now()
            appointment.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"Appointment Reminder SMS Error: {str(e)}", "Appointment SMS")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_service_completion_sms(service_order_id: str, language: str = "ar") -> Dict[str, any]:
    """
    Send service completion notification SMS (Workshop-specific)

    Args:
        service_order_id (str): Service Order ID
        language (str): Language preference ('ar' or 'en')

    Returns:
        Dict: Send result
    """
    try:
        # Get service order details
        service_order = frappe.get_doc("Service Order", service_order_id)
        customer = frappe.get_doc("Customer", service_order.customer)

        # Get customer phone
        phone = customer.mobile_no or customer.phone
        if not phone:
            return {"success": False, "error": _("Customer phone number not found")}

        # Prepare message context
        context = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "vehicle_number": service_order.vehicle_plate_number,
            "service_type": service_order.service_type,
            "total_amount": service_order.total_amount,
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "workshop_phone": frappe.db.get_single_value("Workshop Settings", "phone"),
        }

        # Get message template
        template_name = f"service_completion_{language}"
        template = get_sms_template(template_name)

        if not template:
            # Fallback message
            if language == "ar":
                message = _(
                    "مرحباً {customer_name}، تم إنجاز خدمة {service_type} للمركبة {vehicle_number}. المبلغ الإجمالي: {total_amount} ر.ع. ورشة {workshop_name}"
                ).format(**context)
            else:
                message = _(
                    "Hello {customer_name}, service {service_type} completed for vehicle {vehicle_number}. Total amount: {total_amount} OMR. {workshop_name}"
                ).format(**context)
        else:
            message = render_sms_template(template, context)

        # Send SMS
        result = send_sms_message(
            to=phone, message=message, customer_id=customer.name, template_name=template_name
        )

        # Update service order with notification sent flag
        if result.get("success"):
            service_order.completion_sms_sent = 1
            service_order.completion_sms_sent_at = frappe.utils.now()
            service_order.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"Service Completion SMS Error: {str(e)}", "Service SMS")
        return {"success": False, "error": str(e)}


def get_sms_template(template_name: str) -> str:
    """Get SMS template content from database"""
    try:
        if frappe.db.exists("DocType", "SMS Template"):
            template = frappe.db.get_value("SMS Template", template_name, "template_content")
            return template
        return None
    except Exception:
        return None


def render_sms_template(template: str, context: Dict) -> str:
    """Render SMS template with context"""
    try:
        # Simple template rendering
        rendered = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    except Exception:
        return template


@frappe.whitelist()
def send_sms_with_validation(to_number: str, message: str, language: str = "en") -> Dict[str, any]:
    """
    Send SMS with validation - used by queue workers

    Args:
        to_number: Recipient phone number
        message: SMS message content
        language: Message language

    Returns:
        Dict: Send result with success status
    """
    try:
        # Validate phone number format
        validation_result = validate_phone_number(to_number)
        if not validation_result.get("is_valid"):
            return {"success": False, "error": f"Invalid phone number: {to_number}"}

        # Use validated/formatted number
        formatted_number = validation_result.get("formatted_phone", to_number)

        # Send SMS using existing function
        result = send_sms_message(formatted_number, message)

        return result

    except Exception as e:
        frappe.log_error(f"SMS validation error: {e}", "SMS Send Validation")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def queue_sms_message(
    to_number: str,
    message: str,
    customer_id: str = None,
    language: str = "en",
    priority: str = "medium",
) -> Dict[str, any]:
    """
    Queue SMS message for asynchronous processing

    Args:
        to_number: Recipient phone number
        message: SMS message content
        customer_id: Optional customer ID
        language: Message language
        priority: Message priority (high/medium/low)

    Returns:
        Dict: Queue result with message ID
    """
    try:
        from ..queue.redis_queue_manager import get_queue_manager, QueueType, Priority

        queue_manager = get_queue_manager()

        # Prepare message data
        message_data = {
            "to_number": to_number,
            "message": message,
            "customer_id": customer_id,
            "language": language,
        }

        # Convert priority string to enum
        priority_map = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}
        priority_enum = priority_map.get(priority.lower(), Priority.MEDIUM)

        # Enqueue message
        message_id = queue_manager.enqueue_message(
            queue_type=QueueType.SMS, message_data=message_data, priority=priority_enum
        )

        return {
            "success": True,
            "message_id": message_id,
            "message": _("SMS message queued successfully"),
        }

    except Exception as e:
        frappe.log_error(f"SMS queue error: {e}", "SMS Queue")
        return {"success": False, "error": str(e)}
