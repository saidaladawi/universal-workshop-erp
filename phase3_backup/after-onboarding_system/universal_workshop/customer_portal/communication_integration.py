# -*- coding: utf-8 -*-
"""
Customer Portal Communication Integration
Connects customer portal events with SMS/WhatsApp communication system
"""

import frappe
from frappe import _
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class CustomerPortalCommunication:
    """Main class for customer portal communication integration"""

    def __init__(self):
        self.communication_settings = self._get_communication_settings()

    def _get_communication_settings(self) -> Dict:
        """Get communication system settings"""
        try:
            settings = frappe.get_single("Communication Settings")
            return {
                "auto_send_booking_confirmation": getattr(
                    settings, "auto_send_booking_confirmation", True
                ),
                "auto_send_cancellation_notice": getattr(
                    settings, "auto_send_cancellation_notice", True
                ),
                "auto_send_reschedule_notice": getattr(
                    settings, "auto_send_reschedule_notice", True
                ),
                "auto_send_status_updates": getattr(settings, "auto_send_status_updates", True),
                "auto_send_feedback_request": getattr(settings, "auto_send_feedback_request", True),
                "default_notification_channels": ["whatsapp", "sms"],
            }
        except Exception as e:
            frappe.log_error(f"Error getting communication settings: {str(e)}")
            return {
                "auto_send_booking_confirmation": True,
                "auto_send_cancellation_notice": True,
                "auto_send_reschedule_notice": True,
                "auto_send_status_updates": True,
                "auto_send_feedback_request": True,
                "default_notification_channels": ["whatsapp", "sms"],
            }


# Booking Related Notifications


@frappe.whitelist()
def send_booking_confirmation(appointment_id: str) -> Dict[str, Any]:
    """
    Send booking confirmation via SMS/WhatsApp after appointment creation

    Args:
        appointment_id (str): Service Appointment document ID

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get appointment details
        appointment = frappe.get_doc("Service Appointment", appointment_id)

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare context data for templates
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "appointment_date": frappe.format_date(appointment.appointment_date, "dd/MM/yyyy"),
            "appointment_time": frappe.format_time(appointment.appointment_time),
            "service_type": appointment.service_type,
            "vehicle_number": appointment.vehicle_number or "N/A",
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
            "appointment_id": appointment.name,
        }

        results = {
            "appointment_id": appointment_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Send WhatsApp notification if enabled
        if preferences.get("whatsapp_enabled"):
            try:
                whatsapp_result = _send_template_notification(
                    customer_id=appointment.customer,
                    template_type="Appointment Confirmation",
                    channel="WhatsApp",
                    context_data=context_data,
                    language=preferences.get("preferred_language", "ar"),
                )
                results["notifications_sent"].append(
                    {
                        "channel": "WhatsApp",
                        "status": whatsapp_result.get("status"),
                        "message_id": whatsapp_result.get("message_id"),
                    }
                )
            except Exception as e:
                error_msg = f"WhatsApp notification failed: {str(e)}"
                results["errors"].append(error_msg)
                frappe.log_error(error_msg, "Booking Confirmation WhatsApp")

        # Send SMS notification if enabled (fallback or primary)
        if preferences.get("sms_enabled"):
            try:
                sms_result = _send_template_notification(
                    customer_id=appointment.customer,
                    template_type="Appointment Confirmation",
                    channel="SMS",
                    context_data=context_data,
                    language=preferences.get("preferred_language", "ar"),
                )
                results["notifications_sent"].append(
                    {
                        "channel": "SMS",
                        "status": sms_result.get("status"),
                        "message_id": sms_result.get("message_id"),
                    }
                )
            except Exception as e:
                error_msg = f"SMS notification failed: {str(e)}"
                results["errors"].append(error_msg)
                frappe.log_error(error_msg, "Booking Confirmation SMS")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Booking Confirmation",
            reference_document="Service Appointment",
            reference_id=appointment_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending booking confirmation: {str(e)}"
        frappe.log_error(error_msg, "Booking Confirmation")
        return {"error": error_msg, "appointment_id": appointment_id}


@frappe.whitelist()
def send_cancellation_notice(
    appointment_id: str, cancellation_reason: str = None
) -> Dict[str, Any]:
    """
    Send appointment cancellation notice via SMS/WhatsApp

    Args:
        appointment_id (str): Service Appointment document ID
        cancellation_reason (str): Reason for cancellation

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get appointment details
        appointment = frappe.get_doc("Service Appointment", appointment_id)

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare context data
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "appointment_date": frappe.format_date(appointment.appointment_date, "dd/MM/yyyy"),
            "appointment_time": frappe.format_time(appointment.appointment_time),
            "service_type": appointment.service_type,
            "vehicle_number": appointment.vehicle_number or "N/A",
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
            "cancellation_reason": cancellation_reason or _("Customer Request"),
            "appointment_id": appointment.name,
        }

        results = {
            "appointment_id": appointment_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Create cancellation message templates if not exist
        cancellation_templates = _get_cancellation_templates()

        # Send notifications based on preferences
        for channel in ["WhatsApp", "SMS"]:
            channel_key = f"{channel.lower()}_enabled"
            if preferences.get(channel_key):
                try:
                    result = _send_custom_notification(
                        customer_id=appointment.customer,
                        channel=channel,
                        message_template=cancellation_templates[channel][
                            preferences.get("preferred_language", "ar")
                        ],
                        context_data=context_data,
                    )
                    results["notifications_sent"].append(
                        {
                            "channel": channel,
                            "status": result.get("status"),
                            "message_id": result.get("message_id"),
                        }
                    )
                except Exception as e:
                    error_msg = f"{channel} cancellation notice failed: {str(e)}"
                    results["errors"].append(error_msg)
                    frappe.log_error(error_msg, "Cancellation Notice")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Appointment Cancellation",
            reference_document="Service Appointment",
            reference_id=appointment_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending cancellation notice: {str(e)}"
        frappe.log_error(error_msg, "Cancellation Notice")
        return {"error": error_msg, "appointment_id": appointment_id}


@frappe.whitelist()
def send_reschedule_notice(appointment_id: str, old_date: str, old_time: str) -> Dict[str, Any]:
    """
    Send appointment reschedule notice via SMS/WhatsApp

    Args:
        appointment_id (str): Service Appointment document ID
        old_date (str): Previous appointment date
        old_time (str): Previous appointment time

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get appointment details
        appointment = frappe.get_doc("Service Appointment", appointment_id)

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare context data
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "old_date": frappe.format_date(old_date, "dd/MM/yyyy"),
            "old_time": old_time,
            "new_date": frappe.format_date(appointment.appointment_date, "dd/MM/yyyy"),
            "new_time": frappe.format_time(appointment.appointment_time),
            "service_type": appointment.service_type,
            "vehicle_number": appointment.vehicle_number or "N/A",
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
            "appointment_id": appointment.name,
        }

        results = {
            "appointment_id": appointment_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Create reschedule message templates if not exist
        reschedule_templates = _get_reschedule_templates()

        # Send notifications based on preferences
        for channel in ["WhatsApp", "SMS"]:
            channel_key = f"{channel.lower()}_enabled"
            if preferences.get(channel_key):
                try:
                    result = _send_custom_notification(
                        customer_id=appointment.customer,
                        channel=channel,
                        message_template=reschedule_templates[channel][
                            preferences.get("preferred_language", "ar")
                        ],
                        context_data=context_data,
                    )
                    results["notifications_sent"].append(
                        {
                            "channel": channel,
                            "status": result.get("status"),
                            "message_id": result.get("message_id"),
                        }
                    )
                except Exception as e:
                    error_msg = f"{channel} reschedule notice failed: {str(e)}"
                    results["errors"].append(error_msg)
                    frappe.log_error(error_msg, "Reschedule Notice")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Appointment Reschedule",
            reference_document="Service Appointment",
            reference_id=appointment_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending reschedule notice: {str(e)}"
        frappe.log_error(error_msg, "Reschedule Notice")
        return {"error": error_msg, "appointment_id": appointment_id}


# Service Status Update Notifications


@frappe.whitelist()
def send_service_status_update(work_order_id: str, new_status: str) -> Dict[str, Any]:
    """
    Send service status update notification

    Args:
        work_order_id (str): Work Order document ID
        new_status (str): New work order status

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get work order and related appointment
        work_order = frappe.get_doc("Work Order", work_order_id)

        # Find related service appointment
        appointment = None
        if hasattr(work_order, "service_appointment"):
            appointment = frappe.get_doc("Service Appointment", work_order.service_appointment)

        if not appointment:
            # Try to find by work order reference
            appointments = frappe.get_list(
                "Service Appointment", filters={"work_order": work_order_id}, limit=1
            )
            if appointments:
                appointment = frappe.get_doc("Service Appointment", appointments[0].name)

        if not appointment:
            return {"error": "No associated appointment found for work order"}

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare context data
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "vehicle_number": appointment.vehicle_number or "N/A",
            "service_type": appointment.service_type,
            "new_status": new_status,
            "work_order_id": work_order_id,
            "estimated_completion": _get_estimated_completion_time(work_order),
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
        }

        results = {
            "work_order_id": work_order_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Create status update message templates
        status_templates = _get_status_update_templates()

        # Send notifications for significant status changes
        significant_statuses = [
            "In Progress",
            "Waiting for Parts",
            "Completed",
            "Ready for Collection",
        ]

        if new_status in significant_statuses:
            # Send notifications based on preferences
            for channel in ["WhatsApp", "SMS"]:
                channel_key = f"{channel.lower()}_enabled"
                if preferences.get(channel_key):
                    try:
                        result = _send_custom_notification(
                            customer_id=appointment.customer,
                            channel=channel,
                            message_template=status_templates[channel][
                                preferences.get("preferred_language", "ar")
                            ],
                            context_data=context_data,
                        )
                        results["notifications_sent"].append(
                            {
                                "channel": channel,
                                "status": result.get("status"),
                                "message_id": result.get("message_id"),
                            }
                        )
                    except Exception as e:
                        error_msg = f"{channel} status update failed: {str(e)}"
                        results["errors"].append(error_msg)
                        frappe.log_error(error_msg, "Service Status Update")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Service Status Update",
            reference_document="Work Order",
            reference_id=work_order_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending service status update: {str(e)}"
        frappe.log_error(error_msg, "Service Status Update")
        return {"error": error_msg, "work_order_id": work_order_id}


@frappe.whitelist()
def send_parts_approval_request(parts_usage_id: str) -> Dict[str, Any]:
    """
    Send parts approval request to customer

    Args:
        parts_usage_id (str): Parts Usage document ID

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get parts usage details
        parts_usage = frappe.get_doc("Parts Usage", parts_usage_id)

        # Find related appointment/work order
        work_order = frappe.get_doc("Work Order", parts_usage.work_order)
        appointment = None

        if hasattr(work_order, "service_appointment"):
            appointment = frappe.get_doc("Service Appointment", work_order.service_appointment)

        if not appointment:
            return {"error": "No associated appointment found"}

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare parts list
        parts_list = []
        total_cost = 0

        for item in parts_usage.items:
            parts_list.append(
                {
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "rate": item.rate,
                    "amount": item.amount,
                }
            )
            total_cost += item.amount

        # Prepare context data
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "vehicle_number": appointment.vehicle_number or "N/A",
            "service_type": appointment.service_type,
            "parts_list": parts_list,
            "total_cost": f"{total_cost:.3f}",
            "parts_usage_id": parts_usage_id,
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
            "approval_deadline": frappe.format_date(
                frappe.utils.add_days(frappe.utils.today(), 1), "dd/MM/yyyy"
            ),
        }

        results = {
            "parts_usage_id": parts_usage_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Create parts approval message templates
        approval_templates = _get_parts_approval_templates()

        # Send notifications based on preferences (prioritize WhatsApp for rich content)
        for channel in ["WhatsApp", "SMS"]:
            channel_key = f"{channel.lower()}_enabled"
            if preferences.get(channel_key):
                try:
                    result = _send_custom_notification(
                        customer_id=appointment.customer,
                        channel=channel,
                        message_template=approval_templates[channel][
                            preferences.get("preferred_language", "ar")
                        ],
                        context_data=context_data,
                    )
                    results["notifications_sent"].append(
                        {
                            "channel": channel,
                            "status": result.get("status"),
                            "message_id": result.get("message_id"),
                        }
                    )
                except Exception as e:
                    error_msg = f"{channel} parts approval request failed: {str(e)}"
                    results["errors"].append(error_msg)
                    frappe.log_error(error_msg, "Parts Approval Request")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Parts Approval Request",
            reference_document="Parts Usage",
            reference_id=parts_usage_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending parts approval request: {str(e)}"
        frappe.log_error(error_msg, "Parts Approval Request")
        return {"error": error_msg, "parts_usage_id": parts_usage_id}


@frappe.whitelist()
def send_feedback_request(appointment_id: str) -> Dict[str, Any]:
    """
    Send service feedback request after service completion

    Args:
        appointment_id (str): Service Appointment document ID

    Returns:
        Dict: Notification sending results
    """
    try:
        # Get appointment details
        appointment = frappe.get_doc("Service Appointment", appointment_id)

        # Check if service is completed
        if appointment.status != "Completed":
            return {"error": "Service not completed yet"}

        # Get customer communication preferences
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(appointment.customer)

        # Prepare context data
        context_data = {
            "customer_name": appointment.customer_name,
            "customer_name_ar": getattr(appointment, "customer_name_ar", appointment.customer_name),
            "vehicle_number": appointment.vehicle_number or "N/A",
            "service_type": appointment.service_type,
            "completion_date": frappe.format_date(
                appointment.completion_date or frappe.utils.today(), "dd/MM/yyyy"
            ),
            "appointment_id": appointment_id,
            "feedback_url": f"{frappe.utils.get_url()}/portal/feedback/{appointment_id}",
            "workshop_name": appointment.workshop_name,
            "workshop_phone": appointment.workshop_phone or "+968 24 123456",
        }

        results = {
            "appointment_id": appointment_id,
            "customer": appointment.customer,
            "notifications_sent": [],
            "errors": [],
        }

        # Create feedback request message templates
        feedback_templates = _get_feedback_request_templates()

        # Send notifications based on preferences
        for channel in ["WhatsApp", "SMS"]:
            channel_key = f"{channel.lower()}_enabled"
            if preferences.get(channel_key):
                try:
                    result = _send_custom_notification(
                        customer_id=appointment.customer,
                        channel=channel,
                        message_template=feedback_templates[channel][
                            preferences.get("preferred_language", "ar")
                        ],
                        context_data=context_data,
                    )
                    results["notifications_sent"].append(
                        {
                            "channel": channel,
                            "status": result.get("status"),
                            "message_id": result.get("message_id"),
                        }
                    )
                except Exception as e:
                    error_msg = f"{channel} feedback request failed: {str(e)}"
                    results["errors"].append(error_msg)
                    frappe.log_error(error_msg, "Feedback Request")

        # Log communication history
        _log_portal_communication(
            customer=appointment.customer,
            communication_type="Feedback Request",
            reference_document="Service Appointment",
            reference_id=appointment_id,
            results=results,
        )

        return results

    except Exception as e:
        error_msg = f"Error sending feedback request: {str(e)}"
        frappe.log_error(error_msg, "Feedback Request")
        return {"error": error_msg, "appointment_id": appointment_id}


# Helper Functions


def _send_template_notification(
    customer_id: str, template_type: str, channel: str, context_data: Dict, language: str
) -> Dict[str, Any]:
    """Send notification using existing communication management templates"""
    try:
        from universal_workshop.communication_management.api.communication_utils import (
            send_multilingual_notification,
        )

        # Map channel names to communication system format
        channel_mapping = {"SMS": ["sms"], "WhatsApp": ["whatsapp"], "Email": ["email"]}

        channels = channel_mapping.get(channel, [channel.lower()])

        result = send_multilingual_notification(
            customer_id=customer_id,
            template_type=template_type,
            context_data=context_data,
            channels=channels,
        )

        return {
            "status": "success" if not result.get("error") else "failed",
            "message_id": result.get("message_id"),
            "details": result,
        }

    except Exception as e:
        frappe.log_error(f"Template notification error: {str(e)}")
        return {"status": "failed", "error": str(e)}


def _send_custom_notification(
    customer_id: str, channel: str, message_template: str, context_data: Dict
) -> Dict[str, Any]:
    """Send custom notification using communication APIs"""
    try:
        # Render message template with context data
        from frappe.utils.jinja import render_template

        rendered_message = render_template(message_template, context_data)

        # Get customer phone/contact info
        customer = frappe.get_doc("Customer", customer_id)

        if channel == "SMS":
            from universal_workshop.communication_management.api.sms_api import send_sms_message

            phone = customer.mobile_no or customer.phone
            if phone:
                result = send_sms_message(phone, rendered_message)
                return {
                    "status": "success" if result.get("success") else "failed",
                    "message_id": result.get("message_id"),
                    "details": result,
                }
            else:
                return {"status": "failed", "error": "No phone number found"}

        elif channel == "WhatsApp":
            from universal_workshop.communication_management.api.whatsapp_api import (
                send_whatsapp_message,
            )

            phone = customer.mobile_no or customer.phone
            if phone:
                result = send_whatsapp_message(phone, rendered_message)
                return {
                    "status": "success" if result.get("success") else "failed",
                    "message_id": result.get("message_id"),
                    "details": result,
                }
            else:
                return {"status": "failed", "error": "No phone number found"}

        return {"status": "failed", "error": f"Unsupported channel: {channel}"}

    except Exception as e:
        frappe.log_error(f"Custom notification error: {str(e)}")
        return {"status": "failed", "error": str(e)}


def _log_portal_communication(
    customer: str,
    communication_type: str,
    reference_document: str,
    reference_id: str,
    results: Dict,
) -> None:
    """Log customer portal communication history"""
    try:
        # Create communication history entry
        comm_history = frappe.new_doc("Communication History")
        comm_history.customer = customer
        comm_history.communication_type = communication_type
        comm_history.reference_doctype = reference_document
        comm_history.reference_name = reference_id
        comm_history.sent_on = frappe.utils.now()
        comm_history.source = "Customer Portal"

        # Add notification results
        comm_history.notifications_sent = json.dumps(results.get("notifications_sent", []))
        comm_history.errors = json.dumps(results.get("errors", []))
        comm_history.success_count = len(results.get("notifications_sent", []))
        comm_history.error_count = len(results.get("errors", []))

        comm_history.insert(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(f"Error logging portal communication: {str(e)}")


def _get_estimated_completion_time(work_order) -> str:
    """Get estimated completion time for work order"""
    try:
        if hasattr(work_order, "expected_end_date") and work_order.expected_end_date:
            return frappe.format_datetime(work_order.expected_end_date, "dd/MM/yyyy HH:mm")
        else:
            # Default to 24 hours from now
            estimated = frappe.utils.add_to_date(frappe.utils.now(), hours=24)
            return frappe.format_datetime(estimated, "dd/MM/yyyy HH:mm")
    except Exception:
        return _("Not available")


# Message Template Functions


def _get_cancellation_templates() -> Dict[str, Dict[str, str]]:
    """Get cancellation notice message templates"""
    return {
        "SMS": {
            "ar": "عزيزي {{ customer_name_ar }}، تم إلغاء موعدك بتاريخ {{ appointment_date }} في {{ appointment_time }} لخدمة {{ service_type }} للمركبة {{ vehicle_number }}. السبب: {{ cancellation_reason }}. للاستفسار: {{ workshop_phone }}",
            "en": "Dear {{ customer_name }}, your appointment on {{ appointment_date }} at {{ appointment_time }} for {{ service_type }} (Vehicle: {{ vehicle_number }}) has been cancelled. Reason: {{ cancellation_reason }}. Contact: {{ workshop_phone }}",
        },
        "WhatsApp": {
            "ar": "❌ *إلغاء الموعد*\n\nعزيزي {{ customer_name_ar }}،\n\nتم إلغاء موعدك:\n\n📅 التاريخ: {{ appointment_date }}\n⏰ الوقت: {{ appointment_time }}\n🔧 الخدمة: {{ service_type }}\n🚗 المركبة: {{ vehicle_number }}\n\n❓ السبب: {{ cancellation_reason }}\n\n📞 للاستفسار: {{ workshop_phone }}\n\n{{ workshop_name }}",
            "en": "❌ *Appointment Cancelled*\n\nDear {{ customer_name }},\n\nYour appointment has been cancelled:\n\n📅 Date: {{ appointment_date }}\n⏰ Time: {{ appointment_time }}\n🔧 Service: {{ service_type }}\n🚗 Vehicle: {{ vehicle_number }}\n\n❓ Reason: {{ cancellation_reason }}\n\n📞 Contact: {{ workshop_phone }}\n\n{{ workshop_name }}",
        },
    }


def _get_reschedule_templates() -> Dict[str, Dict[str, str]]:
    """Get reschedule notice message templates"""
    return {
        "SMS": {
            "ar": "عزيزي {{ customer_name_ar }}، تم تعديل موعدك من {{ old_date }} {{ old_time }} إلى {{ new_date }} {{ new_time }} لخدمة {{ service_type }}. المركبة: {{ vehicle_number }}. {{ workshop_phone }}",
            "en": "Dear {{ customer_name }}, your appointment has been rescheduled from {{ old_date }} {{ old_time }} to {{ new_date }} {{ new_time }} for {{ service_type }}. Vehicle: {{ vehicle_number }}. {{ workshop_phone }}",
        },
        "WhatsApp": {
            "ar": "🔄 *تعديل الموعد*\n\nعزيزي {{ customer_name_ar }}،\n\nتم تعديل موعدك:\n\n❌ الموعد السابق:\n📅 {{ old_date }} في {{ old_time }}\n\n✅ الموعد الجديد:\n📅 {{ new_date }} في {{ new_time }}\n\n🔧 الخدمة: {{ service_type }}\n🚗 المركبة: {{ vehicle_number }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
            "en": "🔄 *Appointment Rescheduled*\n\nDear {{ customer_name }},\n\nYour appointment has been rescheduled:\n\n❌ Previous:\n📅 {{ old_date }} at {{ old_time }}\n\n✅ New:\n📅 {{ new_date }} at {{ new_time }}\n\n🔧 Service: {{ service_type }}\n🚗 Vehicle: {{ vehicle_number }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
        },
    }


def _get_status_update_templates() -> Dict[str, Dict[str, str]]:
    """Get service status update message templates"""
    return {
        "SMS": {
            "ar": "تحديث حالة الخدمة: {{ service_type }} للمركبة {{ vehicle_number }} - الحالة: {{ new_status }}. الانتهاء المتوقع: {{ estimated_completion }}. {{ workshop_phone }}",
            "en": "Service Update: {{ service_type }} for {{ vehicle_number }} - Status: {{ new_status }}. Est. completion: {{ estimated_completion }}. {{ workshop_phone }}",
        },
        "WhatsApp": {
            "ar": "🔄 *تحديث حالة الخدمة*\n\nعزيزي {{ customer_name_ar }}،\n\n🚗 المركبة: {{ vehicle_number }}\n🔧 الخدمة: {{ service_type }}\n📊 الحالة الجديدة: {{ new_status }}\n⏰ الانتهاء المتوقع: {{ estimated_completion }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
            "en": "🔄 *Service Status Update*\n\nDear {{ customer_name }},\n\n🚗 Vehicle: {{ vehicle_number }}\n🔧 Service: {{ service_type }}\n📊 New Status: {{ new_status }}\n⏰ Est. Completion: {{ estimated_completion }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
        },
    }


def _get_parts_approval_templates() -> Dict[str, Dict[str, str]]:
    """Get parts approval request message templates"""
    return {
        "SMS": {
            "ar": "مطلوب موافقة: قطع غيار للمركبة {{ vehicle_number }} بمبلغ {{ total_cost }} ر.ع. للموافقة اتصل {{ workshop_phone }} أو زر البوابة الإلكترونية.",
            "en": "Approval Required: Parts for {{ vehicle_number }} costing OMR {{ total_cost }}. To approve call {{ workshop_phone }} or visit portal.",
        },
        "WhatsApp": {
            "ar": "⚠️ *مطلوب موافقة على قطع الغيار*\n\nعزيزي {{ customer_name_ar }}،\n\n🚗 المركبة: {{ vehicle_number }}\n🔧 الخدمة: {{ service_type }}\n\n💰 إجمالي التكلفة: {{ total_cost }} ر.ع\n\n⏰ الموافقة مطلوبة قبل: {{ approval_deadline }}\n\nللموافقة:\n📞 اتصل: {{ workshop_phone }}\n🌐 أو زر البوابة الإلكترونية\n\n{{ workshop_name }}",
            "en": "⚠️ *Parts Approval Required*\n\nDear {{ customer_name }},\n\n🚗 Vehicle: {{ vehicle_number }}\n🔧 Service: {{ service_type }}\n\n💰 Total Cost: OMR {{ total_cost }}\n\n⏰ Approval needed by: {{ approval_deadline }}\n\nTo approve:\n📞 Call: {{ workshop_phone }}\n🌐 Or visit portal\n\n{{ workshop_name }}",
        },
    }


def _get_feedback_request_templates() -> Dict[str, Dict[str, str]]:
    """Get feedback request message templates"""
    return {
        "SMS": {
            "ar": "شكراً لثقتك {{ customer_name_ar }}! تم إنجاز خدمة {{ service_type }} للمركبة {{ vehicle_number }}. نقدر تقييمك عبر البوابة الإلكترونية. {{ workshop_phone }}",
            "en": "Thank you {{ customer_name }}! {{ service_type }} for {{ vehicle_number }} completed. We appreciate your feedback via portal. {{ workshop_phone }}",
        },
        "WhatsApp": {
            "ar": "🌟 *طلب تقييم الخدمة*\n\nعزيزي {{ customer_name_ar }}،\n\nشكراً لثقتك بخدماتنا!\n\n✅ تم إنجاز:\n🔧 الخدمة: {{ service_type }}\n🚗 المركبة: {{ vehicle_number }}\n📅 تاريخ الإنجاز: {{ completion_date }}\n\n⭐ نقدر تقييمك وملاحظاتك:\n🌐 {{ feedback_url }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
            "en": "🌟 *Service Feedback Request*\n\nDear {{ customer_name }},\n\nThank you for trusting us!\n\n✅ Completed:\n🔧 Service: {{ service_type }}\n🚗 Vehicle: {{ vehicle_number }}\n📅 Completion: {{ completion_date }}\n\n⭐ We value your feedback:\n🌐 {{ feedback_url }}\n\n📞 {{ workshop_phone }}\n{{ workshop_name }}",
        },
    }


# API Endpoints for Customer Portal Integration


@frappe.whitelist()
def get_communication_preferences(customer_id: str) -> Dict[str, Any]:
    """Get customer communication preferences for portal"""
    try:
        from universal_workshop.communication_management.api.communication_utils import (
            get_customer_communication_preference,
        )

        preferences = get_customer_communication_preference(customer_id)
        return {"success": True, "preferences": preferences}

    except Exception as e:
        frappe.log_error(f"Error getting communication preferences: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_communication_preferences(customer_id: str, preferences: str) -> Dict[str, Any]:
    """Update customer communication preferences from portal"""
    try:
        preferences_dict = json.loads(preferences) if isinstance(preferences, str) else preferences

        # Update customer document with new preferences
        customer = frappe.get_doc("Customer", customer_id)

        # Update fields if they exist
        if hasattr(customer, "preferred_language"):
            customer.preferred_language = preferences_dict.get("preferred_language", "ar")
        if hasattr(customer, "sms_notifications"):
            customer.sms_notifications = preferences_dict.get("sms_enabled", True)
        if hasattr(customer, "whatsapp_notifications"):
            customer.whatsapp_notifications = preferences_dict.get("whatsapp_enabled", True)
        if hasattr(customer, "email_notifications"):
            customer.email_notifications = preferences_dict.get("email_enabled", True)

        customer.save(ignore_permissions=True)

        return {"success": True, "message": _("Communication preferences updated successfully")}

    except Exception as e:
        frappe.log_error(f"Error updating communication preferences: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_communication_history(customer_id: str, limit: int = 20) -> Dict[str, Any]:
    """Get customer communication history for portal"""
    try:
        # Get communication history
        history = frappe.get_list(
            "Communication History",
            filters={"customer": customer_id},
            fields=[
                "name",
                "communication_type",
                "sent_on",
                "success_count",
                "error_count",
                "reference_doctype",
                "reference_name",
            ],
            order_by="sent_on desc",
            limit=limit,
        )

        return {"success": True, "history": history, "total_count": len(history)}

    except Exception as e:
        frappe.log_error(f"Error getting communication history: {str(e)}")
        return {"success": False, "error": str(e)}
