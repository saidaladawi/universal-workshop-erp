# -*- coding: utf-8 -*-
"""
WhatsApp API Methods for Universal Workshop ERP
WhiteListed methods for sending WhatsApp messages with approved templates
"""

import frappe
from frappe import _
from typing import Dict, List, Optional
from ..oman_twilio_client import get_twilio_client


@frappe.whitelist()
def send_whatsapp_message(
    to: str,
    template_name: str,
    template_data: Dict = None,
    customer_id: str = None,
    language: str = "ar",
) -> Dict[str, any]:
    """
    Send WhatsApp message using approved templates

    Args:
        to (str): Phone number in Oman format
        template_name (str): Approved WhatsApp template name
        template_data (Dict): Data for template placeholders
        customer_id (str, optional): Customer reference
        language (str): Language preference ('ar' or 'en')

    Returns:
        Dict: Result with success status and details
    """
    try:
        # Get Twilio client
        client = get_twilio_client()

        # Send WhatsApp message
        result = client.send_whatsapp(
            to=to,
            template_name=template_name,
            template_data=template_data or {},
            customer_id=customer_id,
            language=language,
        )

        return result

    except Exception as e:
        frappe.log_error(f"WhatsApp API Error: {str(e)}", "WhatsApp Send API")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_service_quote_whatsapp(quotation_id: str, language: str = "ar") -> Dict[str, any]:
    """
    Send service quotation via WhatsApp (Workshop-specific)

    Args:
        quotation_id (str): Quotation document ID
        language (str): Language preference ('ar' or 'en')

    Returns:
        Dict: Send result
    """
    try:
        # Get quotation details
        quotation = frappe.get_doc("Quotation", quotation_id)
        customer = frappe.get_doc("Customer", quotation.party_name)

        # Get customer phone
        phone = customer.mobile_no or customer.phone
        if not phone:
            return {"success": False, "error": _("Customer phone number not found")}

        # Prepare template data
        template_data = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "quote_number": quotation.name,
            "vehicle_number": quotation.get("vehicle_plate_number", ""),
            "service_description": quotation.get("service_description", ""),
            "total_amount": f"{quotation.grand_total:.3f}",
            "currency": "OMR",
            "valid_until": quotation.valid_till,
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "workshop_phone": frappe.db.get_single_value("Workshop Settings", "phone"),
        }

        # Send WhatsApp message
        template_name = f"service_quotation_{language}"
        result = send_whatsapp_message(
            to=phone,
            template_name=template_name,
            template_data=template_data,
            customer_id=customer.name,
            language=language,
        )

        # Update quotation with notification sent flag
        if result.get("success"):
            quotation.whatsapp_sent = 1
            quotation.whatsapp_sent_at = frappe.utils.now()
            quotation.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"WhatsApp Quotation Error: {str(e)}", "WhatsApp Quotation")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_invoice_whatsapp(invoice_id: str, language: str = "ar") -> Dict[str, any]:
    """
    Send invoice with QR code via WhatsApp (Oman VAT compliant)

    Args:
        invoice_id (str): Sales Invoice document ID
        language (str): Language preference ('ar' or 'en')

    Returns:
        Dict: Send result
    """
    try:
        # Get invoice details
        invoice = frappe.get_doc("Sales Invoice", invoice_id)
        customer = frappe.get_doc("Customer", invoice.customer)

        # Get customer phone
        phone = customer.mobile_no or customer.phone
        if not phone:
            return {"success": False, "error": _("Customer phone number not found")}

        # Generate QR code for e-invoice (Oman compliance)
        qr_code_data = generate_oman_einvoice_qr(invoice)

        # Prepare template data
        template_data = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "invoice_number": invoice.name,
            "invoice_date": invoice.posting_date,
            "vehicle_number": invoice.get("vehicle_plate_number", ""),
            "service_description": invoice.get("service_description", ""),
            "net_amount": f"{invoice.net_total:.3f}",
            "vat_amount": f"{invoice.total_taxes_and_charges:.3f}",
            "total_amount": f"{invoice.grand_total:.3f}",
            "currency": "OMR",
            "qr_code": qr_code_data,
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "workshop_vat_number": frappe.db.get_single_value("Workshop Settings", "vat_number"),
        }

        # Send WhatsApp message
        template_name = f"invoice_with_qr_{language}"
        result = send_whatsapp_message(
            to=phone,
            template_name=template_name,
            template_data=template_data,
            customer_id=customer.name,
            language=language,
        )

        # Update invoice with notification sent flag
        if result.get("success"):
            invoice.whatsapp_sent = 1
            invoice.whatsapp_sent_at = frappe.utils.now()
            invoice.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"WhatsApp Invoice Error: {str(e)}", "WhatsApp Invoice")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_appointment_confirmation_whatsapp(
    appointment_id: str, language: str = "ar"
) -> Dict[str, any]:
    """
    Send appointment confirmation via WhatsApp

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

        # Prepare template data
        template_data = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "service_type": appointment.service_type,
            "vehicle_number": appointment.get("vehicle_plate_number", ""),
            "technician_name": appointment.get("technician_name", ""),
            "estimated_duration": appointment.get("estimated_duration", ""),
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "workshop_address": frappe.db.get_single_value(
                "Workshop Settings", "address_ar" if language == "ar" else "address"
            ),
            "workshop_phone": frappe.db.get_single_value("Workshop Settings", "phone"),
        }

        # Send WhatsApp message
        template_name = f"appointment_confirmation_{language}"
        result = send_whatsapp_message(
            to=phone,
            template_name=template_name,
            template_data=template_data,
            customer_id=customer.name,
            language=language,
        )

        # Update appointment with notification sent flag
        if result.get("success"):
            appointment.whatsapp_confirmation_sent = 1
            appointment.whatsapp_confirmation_sent_at = frappe.utils.now()
            appointment.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"WhatsApp Appointment Error: {str(e)}", "WhatsApp Appointment")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_vehicle_ready_whatsapp(service_order_id: str, language: str = "ar") -> Dict[str, any]:
    """
    Send vehicle ready for pickup notification via WhatsApp

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

        # Prepare template data
        template_data = {
            "customer_name": (
                customer.customer_name_ar if language == "ar" else customer.customer_name
            ),
            "vehicle_number": service_order.vehicle_plate_number,
            "service_completed": service_order.service_type,
            "pickup_time": service_order.get("estimated_pickup_time", ""),
            "final_amount": f"{service_order.total_amount:.3f}",
            "currency": "OMR",
            "workshop_name": frappe.db.get_single_value(
                "Workshop Settings", "workshop_name_ar" if language == "ar" else "workshop_name"
            ),
            "workshop_phone": frappe.db.get_single_value("Workshop Settings", "phone"),
            "workshop_hours": frappe.db.get_single_value("Workshop Settings", "working_hours"),
        }

        # Send WhatsApp message
        template_name = f"vehicle_ready_{language}"
        result = send_whatsapp_message(
            to=phone,
            template_name=template_name,
            template_data=template_data,
            customer_id=customer.name,
            language=language,
        )

        # Update service order with notification sent flag
        if result.get("success"):
            service_order.pickup_whatsapp_sent = 1
            service_order.pickup_whatsapp_sent_at = frappe.utils.now()
            service_order.save(ignore_permissions=True)

        return result

    except Exception as e:
        frappe.log_error(f"WhatsApp Vehicle Ready Error: {str(e)}", "WhatsApp Vehicle Ready")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_whatsapp_templates(language: str = "ar") -> List[Dict]:
    """
    Get available WhatsApp templates for the specified language

    Args:
        language (str): Language code ('ar' or 'en')

    Returns:
        List[Dict]: Available templates
    """
    try:
        if not frappe.db.exists("DocType", "WhatsApp Template"):
            return []

        templates = frappe.get_list(
            "WhatsApp Template",
            filters={"language": language, "is_approved": 1, "is_active": 1},
            fields=[
                "template_name",
                "template_type",
                "template_content",
                "description",
                "created_by",
                "creation",
            ],
            order_by="template_name",
        )

        return templates

    except Exception as e:
        frappe.log_error(f"Error fetching WhatsApp templates: {str(e)}")
        return []


@frappe.whitelist()
def validate_whatsapp_template(
    template_name: str, template_data: Dict, language: str = "ar"
) -> Dict[str, any]:
    """
    Validate WhatsApp template and render preview

    Args:
        template_name (str): Template name
        template_data (Dict): Template data for rendering
        language (str): Language code

    Returns:
        Dict: Validation result with preview
    """
    try:
        # Get template
        if not frappe.db.exists("DocType", "WhatsApp Template"):
            return {"valid": False, "error": "WhatsApp Template DocType not found"}

        template = frappe.db.get_value(
            "WhatsApp Template",
            {"template_name": template_name, "language": language},
            ["template_content", "is_approved"],
            as_dict=True,
        )

        if not template:
            return {
                "valid": False,
                "error": f"Template {template_name} not found for language {language}",
            }

        if not template.get("is_approved"):
            return {"valid": False, "error": f"Template {template_name} is not approved"}

        # Render preview
        preview = render_whatsapp_template(template.get("template_content"), template_data)

        return {
            "valid": True,
            "template_name": template_name,
            "language": language,
            "preview": preview,
            "character_count": len(preview),
        }

    except Exception as e:
        return {"valid": False, "error": str(e)}


def generate_oman_einvoice_qr(invoice_doc) -> str:
    """
    Generate QR code data for Oman e-invoice compliance
    This should integrate with the billing system's QR code generation
    """
    try:
        # This should use the QR code generator from billing_management module
        from ..billing_management.qr_code_generator import generate_vat_qr_code

        qr_data = generate_vat_qr_code(invoice_doc)
        return qr_data

    except ImportError:
        # Fallback if billing module not available
        frappe.log_error("Billing QR code generator not found", "WhatsApp Invoice QR")
        return f"Invoice: {invoice_doc.name}, Total: {invoice_doc.grand_total} OMR"
    except Exception as e:
        frappe.log_error(f"Error generating QR code: {str(e)}", "WhatsApp Invoice QR")
        return ""


def render_whatsapp_template(template: str, context: Dict) -> str:
    """Render WhatsApp template with context data"""
    try:
        # Simple template rendering - can be enhanced with Jinja2
        rendered = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    except Exception as e:
        frappe.log_error(f"Error rendering WhatsApp template: {str(e)}")
        return template
