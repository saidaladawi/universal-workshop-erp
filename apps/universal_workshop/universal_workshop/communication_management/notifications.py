# -*- coding: utf-8 -*-
"""
Communication Notifications Handler
Automatic SMS/WhatsApp notifications for Universal Workshop ERP events
"""

import frappe
from frappe import _
from typing import Dict, Optional


def send_invoice_notification(doc, method=None):
    """
    Send automatic notification when Sales Invoice is submitted

    Args:
        doc: Sales Invoice document
        method: Hook method (not used)
    """
    try:
        # Check if auto-send is enabled
        settings = frappe.get_single("Communication Settings")
        if not settings.get("auto_send_invoice_sms"):
            return

        # Get customer preferences
        from .api.communication_utils import get_customer_communication_preference

        preferences = get_customer_communication_preference(doc.customer)

        # Send notifications based on preferences
        if preferences.get("sms_enabled"):
            send_invoice_sms_notification(doc, preferences.get("preferred_language", "ar"))

        if preferences.get("whatsapp_enabled"):
            send_invoice_whatsapp_notification(doc, preferences.get("preferred_language", "ar"))

    except Exception as e:
        frappe.log_error(f"Error sending invoice notification: {str(e)}", "Invoice Notification")


def send_appointment_confirmation(doc, method=None):
    """
    Send automatic confirmation when Service Appointment is created

    Args:
        doc: Service Appointment document
        method: Hook method (not used)
    """
    try:
        # Check if auto-send is enabled
        settings = frappe.get_single("Communication Settings")
        if not settings.get("auto_send_appointment_confirmation"):
            return

        # Get customer preferences

        preferences = get_customer_communication_preference(doc.customer)

        # Send notifications based on preferences
        if preferences.get("whatsapp_enabled"):
            send_appointment_whatsapp_confirmation(doc, preferences.get("preferred_language", "ar"))
        elif preferences.get("sms_enabled"):
            send_appointment_sms_confirmation(doc, preferences.get("preferred_language", "ar"))

    except Exception as e:
        frappe.log_error(
            f"Error sending appointment confirmation: {str(e)}", "Appointment Confirmation"
        )


def send_appointment_reminder_check(doc, method=None):
    """
    Check if appointment reminder should be sent (before save)

    Args:
        doc: Service Appointment document
        method: Hook method (not used)
    """
    try:
        # This can be enhanced to send reminders based on appointment date
        # For now, we'll skip automatic reminders and let them be triggered manually
        pass

    except Exception as e:
        frappe.log_error(f"Error checking appointment reminder: {str(e)}", "Appointment Reminder")


def send_service_status_update(doc, method=None):
    """
    Send notification when Service Order status is updated

    Args:
        doc: Service Order document
        method: Hook method (not used)
    """
    try:
        # Check if status changed to 'In Progress' or 'Completed'
        if doc.has_value_changed("status") and doc.status in ["In Progress", "Completed"]:

            # Get customer preferences

            preferences = get_customer_communication_preference(doc.customer)

            # Send status update notification
            if preferences.get("sms_enabled"):
                send_service_status_sms(doc, preferences.get("preferred_language", "ar"))

    except Exception as e:
        frappe.log_error(f"Error sending service status update: {str(e)}", "Service Status Update")


def send_service_completion_notification(doc, method=None):
    """
    Send notification when Service Order is completed

    Args:
        doc: Service Order document
        method: Hook method (not used)
    """
    try:
        # Check if auto-send is enabled
        settings = frappe.get_single("Communication Settings")
        if not settings.get("auto_send_service_completion"):
            return

        # Get customer preferences

        preferences = get_customer_communication_preference(doc.customer)

        # Send completion notifications
        if preferences.get("whatsapp_enabled"):
            send_service_completion_whatsapp(doc, preferences.get("preferred_language", "ar"))
        elif preferences.get("sms_enabled"):
            send_service_completion_sms(doc, preferences.get("preferred_language", "ar"))

    except Exception as e:
        frappe.log_error(
            f"Error sending service completion notification: {str(e)}", "Service Completion"
        )


def send_quotation_notification(doc, method=None):
    """
    Send notification when Quotation is submitted

    Args:
        doc: Quotation document
        method: Hook method (not used)
    """
    try:
        # Get customer preferences

        preferences = get_customer_communication_preference(doc.party_name)

        # Send quotation via WhatsApp if enabled
        if preferences.get("whatsapp_enabled"):
            send_quotation_whatsapp(doc, preferences.get("preferred_language", "ar"))
        elif preferences.get("sms_enabled"):
            send_quotation_sms(doc, preferences.get("preferred_language", "ar"))

    except Exception as e:
        frappe.log_error(
            f"Error sending quotation notification: {str(e)}", "Quotation Notification"
        )


# Individual notification functions


def send_invoice_sms_notification(invoice_doc, language="ar"):
    """Send SMS notification for invoice"""
    try:
        from .api.sms_api import send_sms_message

        customer = frappe.get_doc("Customer", invoice_doc.customer)
        phone = customer.mobile_no or customer.phone

        if not phone:
            return

        # Prepare message
        if language == "ar":
            message = _(
                "عزيزنا {0}، تم إصدار فاتورة رقم {1} بمبلغ {2:.3f} ريال عماني. شكراً لثقتكم."
            ).format(
                customer.customer_name_ar or customer.customer_name,
                invoice_doc.name,
                invoice_doc.grand_total,
            )
        else:
            message = _(
                "Dear {0}, invoice {1} has been generated for {2:.3f} OMR. Thank you."
            ).format(customer.customer_name, invoice_doc.name, invoice_doc.grand_total)

        # Send SMS
        result = send_sms_message(
            to=phone,
            message=message,
            customer_id=customer.name,
            template_name=f"invoice_notification_{language}",
        )

        # Update invoice with SMS sent flag
        if result.get("success"):
            invoice_doc.db_set("sms_sent", 1)
            invoice_doc.db_set("sms_sent_at", frappe.utils.now())

    except Exception as e:
        frappe.log_error(f"Error sending invoice SMS: {str(e)}", "Invoice SMS")


def send_invoice_whatsapp_notification(invoice_doc, language="ar"):
    """Send WhatsApp notification for invoice"""
    try:
        from .api.whatsapp_api import send_invoice_whatsapp

        result = send_invoice_whatsapp(invoice_doc.name, language)

        if result.get("success"):
            frappe.logger().info(f"WhatsApp invoice notification sent for {invoice_doc.name}")
        else:
            frappe.logger().error(
                f"Failed to send WhatsApp invoice notification: {result.get('error')}"
            )

    except Exception as e:
        frappe.log_error(f"Error sending invoice WhatsApp: {str(e)}", "Invoice WhatsApp")


def send_appointment_sms_confirmation(appointment_doc, language="ar"):
    """Send SMS confirmation for appointment"""
    try:
        from .api.sms_api import send_appointment_reminder_sms

        result = send_appointment_reminder_sms(appointment_doc.name, language)

        if result.get("success"):
            frappe.logger().info(f"SMS appointment confirmation sent for {appointment_doc.name}")
        else:
            frappe.logger().error(
                f"Failed to send SMS appointment confirmation: {result.get('error')}"
            )

    except Exception as e:
        frappe.log_error(f"Error sending appointment SMS: {str(e)}", "Appointment SMS")


def send_appointment_whatsapp_confirmation(appointment_doc, language="ar"):
    """Send WhatsApp confirmation for appointment"""
    try:
        from .api.whatsapp_api import send_appointment_confirmation_whatsapp

        result = send_appointment_confirmation_whatsapp(appointment_doc.name, language)

        if result.get("success"):
            frappe.logger().info(
                f"WhatsApp appointment confirmation sent for {appointment_doc.name}"
            )
        else:
            frappe.logger().error(
                f"Failed to send WhatsApp appointment confirmation: {result.get('error')}"
            )

    except Exception as e:
        frappe.log_error(f"Error sending appointment WhatsApp: {str(e)}", "Appointment WhatsApp")


def send_service_status_sms(service_order_doc, language="ar"):
    """Send SMS for service status update"""
    try:

        customer = frappe.get_doc("Customer", service_order_doc.customer)
        phone = customer.mobile_no or customer.phone

        if not phone:
            return

        # Prepare status message
        if language == "ar":
            message = _(
                "عزيزنا {0}، تحديث حالة الخدمة للمركبة {1}: {2}. ورشة الخليج للسيارات"
            ).format(
                customer.customer_name_ar or customer.customer_name,
                service_order_doc.get("vehicle_plate_number", ""),
                service_order_doc.status,
            )
        else:
            message = _(
                "Dear {0}, service status update for vehicle {1}: {2}. Al Khaleej Auto Workshop"
            ).format(
                customer.customer_name,
                service_order_doc.get("vehicle_plate_number", ""),
                service_order_doc.status,
            )

        # Send SMS
        result = send_sms_message(
            to=phone,
            message=message,
            customer_id=customer.name,
            template_name=f"service_status_{language}",
        )

        if result.get("success"):
            frappe.logger().info(f"Service status SMS sent for {service_order_doc.name}")

    except Exception as e:
        frappe.log_error(f"Error sending service status SMS: {str(e)}", "Service Status SMS")


def send_service_completion_sms(service_order_doc, language="ar"):
    """Send SMS for service completion"""
    try:
        from .api.sms_api import send_service_completion_sms

        result = send_service_completion_sms(service_order_doc.name, language)

        if result.get("success"):
            frappe.logger().info(f"Service completion SMS sent for {service_order_doc.name}")
        else:
            frappe.logger().error(f"Failed to send service completion SMS: {result.get('error')}")

    except Exception as e:
        frappe.log_error(
            f"Error sending service completion SMS: {str(e)}", "Service Completion SMS"
        )


def send_service_completion_whatsapp(service_order_doc, language="ar"):
    """Send WhatsApp for service completion"""
    try:
        from .api.whatsapp_api import send_vehicle_ready_whatsapp

        result = send_vehicle_ready_whatsapp(service_order_doc.name, language)

        if result.get("success"):
            frappe.logger().info(f"Service completion WhatsApp sent for {service_order_doc.name}")
        else:
            frappe.logger().error(
                f"Failed to send service completion WhatsApp: {result.get('error')}"
            )

    except Exception as e:
        frappe.log_error(
            f"Error sending service completion WhatsApp: {str(e)}", "Service Completion WhatsApp"
        )


def send_quotation_sms(quotation_doc, language="ar"):
    """Send SMS for quotation"""
    try:

        customer = frappe.get_doc("Customer", quotation_doc.party_name)
        phone = customer.mobile_no or customer.phone

        if not phone:
            return

        # Prepare quotation message
        if language == "ar":
            message = _(
                "عزيزنا {0}، تم إرسال عرض أسعار رقم {1} بمبلغ {2:.3f} ريال عماني. صالح حتى {3}. ورشة الخليج"
            ).format(
                customer.customer_name_ar or customer.customer_name,
                quotation_doc.name,
                quotation_doc.grand_total,
                quotation_doc.valid_till,
            )
        else:
            message = _(
                "Dear {0}, quotation {1} sent for {2:.3f} OMR. Valid until {3}. Al Khaleej Workshop"
            ).format(
                customer.customer_name,
                quotation_doc.name,
                quotation_doc.grand_total,
                quotation_doc.valid_till,
            )

        # Send SMS
        result = send_sms_message(
            to=phone,
            message=message,
            customer_id=customer.name,
            template_name=f"quotation_{language}",
        )

        if result.get("success"):
            frappe.logger().info(f"Quotation SMS sent for {quotation_doc.name}")

    except Exception as e:
        frappe.log_error(f"Error sending quotation SMS: {str(e)}", "Quotation SMS")


def send_quotation_whatsapp(quotation_doc, language="ar"):
    """Send WhatsApp for quotation"""
    try:
        from .api.whatsapp_api import send_service_quote_whatsapp

        result = send_service_quote_whatsapp(quotation_doc.name, language)

        if result.get("success"):
            frappe.logger().info(f"Quotation WhatsApp sent for {quotation_doc.name}")
        else:
            frappe.logger().error(f"Failed to send quotation WhatsApp: {result.get('error')}")

    except Exception as e:
        frappe.log_error(f"Error sending quotation WhatsApp: {str(e)}", "Quotation WhatsApp")
