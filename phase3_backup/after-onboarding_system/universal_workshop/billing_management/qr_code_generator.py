# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, get_datetime, format_datetime
import qrcode
import io
import base64
import struct
from datetime import datetime
import json


class OmanEInvoiceQRGenerator:
    """
    QR Code generator for Oman e-invoice compliance following TLV encoding specification
    Based on Saudi ZATCA (FATOORAH) model until Oman specific requirements are published
    """

    def __init__(self):
        self.tlv_tags = {
            "seller_name": 1,
            "vat_number": 2,
            "invoice_timestamp": 3,
            "invoice_total": 4,
            "vat_amount": 5,
        }

    def generate_qr_code_for_invoice(self, sales_invoice_doc):
        """
        Generate QR code for a Sales Invoice document
        Returns QR code as base64 image and TLV data
        """
        try:
            # Extract invoice data
            invoice_data = self.extract_invoice_data(sales_invoice_doc)

            # Generate TLV encoded data
            tlv_data = self.encode_tlv_data(invoice_data)

            # Create base64 string from TLV data
            tlv_base64 = base64.b64encode(tlv_data).decode("utf-8")

            # Generate QR code
            qr_code_image = self.create_qr_code_image(tlv_base64)

            # Store QR data in invoice
            self.update_invoice_qr_fields(sales_invoice_doc, tlv_base64, qr_code_image)

            return {
                "success": True,
                "qr_code_image": qr_code_image,
                "tlv_data": tlv_base64,
                "invoice_data": invoice_data,
            }

        except Exception as e:
            frappe.log_error(f"QR code generation failed for {sales_invoice_doc.name}: {str(e)}")
            return {"success": False, "error": str(e)}

    def extract_invoice_data(self, sales_invoice_doc):
        """
        Extract required data from Sales Invoice for QR code generation
        """
        # Get company information
        company_doc = frappe.get_doc("Company", sales_invoice_doc.company)

        # Get seller name (Arabic if available, English fallback)
        seller_name = getattr(company_doc, "company_name_ar", None) or company_doc.company_name

        # Get VAT number
        vat_number = getattr(company_doc, "vat_number", "") or getattr(company_doc, "tax_id", "")
        if not vat_number:
            # Try to get from Sales Invoice custom fields
            vat_number = getattr(sales_invoice_doc, "company_vat_number", "")

        # Validate VAT number format for Oman
        if vat_number and not vat_number.startswith("OM"):
            vat_number = f"OM{vat_number}"

        # Get invoice timestamp
        if hasattr(sales_invoice_doc, "posting_date") and hasattr(
            sales_invoice_doc, "posting_time"
        ):
            timestamp_str = (
                f"{sales_invoice_doc.posting_date} {sales_invoice_doc.posting_time or '00:00:00'}"
            )
            timestamp = get_datetime(timestamp_str)
        else:
            timestamp = sales_invoice_doc.creation

        # Format timestamp as ISO 8601
        invoice_timestamp = format_datetime(timestamp, "yyyy-MM-ddTHH:mm:ssZ")

        # Get totals (format to 3 decimal places for OMR/Baisa)
        invoice_total = flt(sales_invoice_doc.grand_total, 3)
        vat_amount = flt(sales_invoice_doc.total_taxes_and_charges or 0, 3)

        return {
            "seller_name": seller_name,
            "vat_number": vat_number,
            "invoice_timestamp": invoice_timestamp,
            "invoice_total": f"{invoice_total:.3f}",
            "vat_amount": f"{vat_amount:.3f}",
        }

    def encode_tlv_data(self, invoice_data):
        """
        Encode invoice data using TLV (Tag-Length-Value) format
        Following Saudi ZATCA specification adapted for Oman
        """
        tlv_bytes = bytearray()

        # Encode each field
        for field, tag in self.tlv_tags.items():
            value = invoice_data.get(field, "")
            if value:
                value_bytes = value.encode("utf-8")
                length = len(value_bytes)

                # Add TLV entry: Tag (1 byte) + Length (1 byte) + Value (variable)
                tlv_bytes.append(tag)
                tlv_bytes.append(length)
                tlv_bytes.extend(value_bytes)

        return bytes(tlv_bytes)

    def create_qr_code_image(self, data):
        """
        Create QR code image from data and return as base64 string
        """
        # QR code settings for invoice compliance
        qr = qrcode.QRCode(
            version=1,  # Adjusts automatically
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
            box_size=10,  # Size of each box in pixels
            border=4,  # Minimum border requirement
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 string
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format="PNG")
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{img_base64}"

    def update_invoice_qr_fields(self, sales_invoice_doc, tlv_data, qr_image):
        """
        Update Sales Invoice with QR code data
        """
        try:
            # Update QR code fields if they exist
            if hasattr(sales_invoice_doc, "qr_code_data"):
                sales_invoice_doc.qr_code_data = tlv_data

            if hasattr(sales_invoice_doc, "qr_code_image"):
                sales_invoice_doc.qr_code_image = qr_image

            if hasattr(sales_invoice_doc, "qr_code_generated"):
                sales_invoice_doc.qr_code_generated = 1

            if hasattr(sales_invoice_doc, "qr_code_timestamp"):
                sales_invoice_doc.qr_code_timestamp = datetime.now()

            # Save without triggering validation hooks
            sales_invoice_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to update QR fields for {sales_invoice_doc.name}: {str(e)}")

    def decode_tlv_data(self, tlv_base64):
        """
        Decode TLV data back to invoice information (for testing/validation)
        """
        try:
            tlv_bytes = base64.b64decode(tlv_base64)
            decoded_data = {}

            i = 0
            while i < len(tlv_bytes):
                if i + 1 >= len(tlv_bytes):
                    break

                tag = tlv_bytes[i]
                length = tlv_bytes[i + 1]

                if i + 2 + length > len(tlv_bytes):
                    break

                value = tlv_bytes[i + 2 : i + 2 + length].decode("utf-8")

                # Map tag back to field name
                field_name = None
                for field, field_tag in self.tlv_tags.items():
                    if field_tag == tag:
                        field_name = field
                        break

                if field_name:
                    decoded_data[field_name] = value

                i += 2 + length

            return decoded_data

        except Exception as e:
            frappe.log_error(f"TLV decode error: {str(e)}")
            return {}

    def validate_qr_code_compliance(self, sales_invoice_doc):
        """
        Validate that the invoice meets QR code compliance requirements
        """
        validation_errors = []

        # Check company VAT number
        company_doc = frappe.get_doc("Company", sales_invoice_doc.company)
        vat_number = getattr(company_doc, "vat_number", "") or getattr(company_doc, "tax_id", "")

        if not vat_number:
            validation_errors.append(_("Company VAT number is required for QR code generation"))

        # Check invoice totals
        if not sales_invoice_doc.grand_total:
            validation_errors.append(_("Invoice grand total is required"))

        # Check invoice date
        if not sales_invoice_doc.posting_date:
            validation_errors.append(_("Invoice posting date is required"))

        # Validate Arabic company name for bilingual compliance
        if not getattr(company_doc, "company_name_ar", None):
            # This is a warning, not an error
            frappe.msgprint(_("Arabic company name not set. Using English name in QR code."))

        return validation_errors


# API Methods for external usage


@frappe.whitelist()
def generate_qr_code_for_sales_invoice(sales_invoice_name):
    """
    Generate QR code for a specific Sales Invoice
    """
    try:
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

        qr_generator = OmanEInvoiceQRGenerator()

        # Validate compliance first
        validation_errors = qr_generator.validate_qr_code_compliance(sales_invoice)
        if validation_errors:
            return {"success": False, "errors": validation_errors}

        # Generate QR code
        result = qr_generator.generate_qr_code_for_invoice(sales_invoice)

        return result

    except Exception as e:
        frappe.log_error(f"QR code generation API error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_qr_code_data(tlv_base64):
    """
    Validate and decode QR code TLV data
    """
    try:
        qr_generator = OmanEInvoiceQRGenerator()
        decoded_data = qr_generator.decode_tlv_data(tlv_base64)

        return {"success": True, "decoded_data": decoded_data}

    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def bulk_generate_qr_codes(invoice_list):
    """
    Generate QR codes for multiple invoices
    """
    results = []
    qr_generator = OmanEInvoiceQRGenerator()

    for invoice_name in invoice_list:
        try:
            sales_invoice = frappe.get_doc("Sales Invoice", invoice_name)
            result = qr_generator.generate_qr_code_for_invoice(sales_invoice)
            result["invoice_name"] = invoice_name
            results.append(result)

        except Exception as e:
            results.append({"invoice_name": invoice_name, "success": False, "error": str(e)})

    return results


# Hook functions for automatic QR code generation


def generate_qr_on_invoice_submit(doc, method):
    """
    Automatically generate QR code when Sales Invoice is submitted
    """
    if doc.doctype == "Sales Invoice" and doc.docstatus == 1:
        try:
            qr_generator = OmanEInvoiceQRGenerator()

            # Check if QR already generated
            if hasattr(doc, "qr_code_generated") and doc.qr_code_generated:
                return

            # Generate QR code
            result = qr_generator.generate_qr_code_for_invoice(doc)

            if result.get("success"):
                frappe.msgprint(
                    _("QR code generated successfully for invoice {0}").format(doc.name)
                )
            else:
                frappe.log_error(f"Auto QR generation failed for {doc.name}: {result.get('error')}")

        except Exception as e:
            frappe.log_error(f"Auto QR generation hook error for {doc.name}: {str(e)}")


def validate_invoice_for_qr(doc, method):
    """
    Validate invoice data before submission to ensure QR code compliance
    """
    if doc.doctype == "Sales Invoice":
        qr_generator = OmanEInvoiceQRGenerator()
        validation_errors = qr_generator.validate_qr_code_compliance(doc)

        if validation_errors:
            error_msg = _("QR Code compliance errors:\n") + "\n".join(validation_errors)
            frappe.throw(error_msg)
