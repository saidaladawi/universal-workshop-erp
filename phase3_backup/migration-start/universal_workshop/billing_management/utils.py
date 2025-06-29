# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, formatdate, get_datetime, now
import uuid
import re
from datetime import datetime


@frappe.whitelist()
def generate_tax_invoice_number(company, posting_date):
    """
    Generate sequential tax invoice number for VAT compliance
    Format: TI-YYYY-NNNNNN (e.g., TI-2024-000001)
    """
    try:
        posting_year = getdate(posting_date).year

        # Get the last tax invoice number for the year
        last_invoice = frappe.db.sql(
            """
            SELECT tax_invoice_number 
            FROM `tabSales Invoice` 
            WHERE company = %s 
            AND YEAR(posting_date) = %s 
            AND tax_invoice_number IS NOT NULL 
            AND tax_invoice_number != ''
            ORDER BY tax_invoice_number DESC 
            LIMIT 1
        """,
            [company, posting_year],
        )

        if last_invoice and last_invoice[0][0]:
            # Extract number from format TI-YYYY-NNNNNN
            last_number = last_invoice[0][0]
            match = re.search(r"TI-\d{4}-(\d{6})", last_number)
            if match:
                next_number = int(match.group(1)) + 1
            else:
                next_number = 1
        else:
            next_number = 1

        # Format: TI-YYYY-NNNNNN
        tax_invoice_number = f"TI-{posting_year}-{next_number:06d}"

        return tax_invoice_number

    except Exception as e:
        frappe.log_error(f"Error generating tax invoice number: {str(e)}")
        return f"TI-{getdate(posting_date).year}-{frappe.utils.random_string(6).upper()}"


@frappe.whitelist()
def generate_e_invoice_uuid():
    """
    Generate unique UUID for e-invoice compliance
    """
    return str(uuid.uuid4()).replace("-", "").upper()


@frappe.whitelist()
def validate_oman_vat_invoice(doc_name):
    """
    Validate invoice against Oman VAT requirements
    """
    doc = frappe.get_doc("Sales Invoice", doc_name)
    errors = []

    # Check required fields for VAT compliance
    if not doc.tax_id and not doc.company_tax_id:
        errors.append(_("Company VAT registration number is required"))

    if not doc.customer_tax_id and doc.grand_total > 1000:
        errors.append(_("Customer VAT number is required for invoices above OMR 1,000"))

    # Validate tax calculation
    if doc.taxes:
        for tax in doc.taxes:
            if "VAT" in tax.description and tax.rate != 5.0:
                errors.append(_("VAT rate should be 5% for Oman"))

    # Check currency precision (Oman requires 3 decimal places for OMR)
    if doc.currency == "OMR":
        if len(str(doc.grand_total).split(".")[-1]) > 3:
            errors.append(_("OMR amounts should have maximum 3 decimal places"))

    return {"is_valid": len(errors) == 0, "errors": errors}


@frappe.whitelist()
def format_amount_in_words_arabic(amount, currency="OMR"):
    """
    Convert amount to words in Arabic
    Basic implementation - would need comprehensive Arabic number conversion
    """
    try:
        amount = float(amount)

        if currency == "OMR":
            omr_amount = int(amount)
            baisa_amount = int((amount - omr_amount) * 1000)

            # Basic Arabic number words (simplified)
            arabic_numbers = {
                0: "صفر",
                1: "واحد",
                2: "اثنان",
                3: "ثلاثة",
                4: "أربعة",
                5: "خمسة",
                6: "ستة",
                7: "سبعة",
                8: "ثمانية",
                9: "تسعة",
                10: "عشرة",
            }

            if omr_amount <= 10:
                omr_words = arabic_numbers.get(omr_amount, str(omr_amount))
            else:
                omr_words = str(omr_amount)  # Fallback to number

            result = f"{omr_words} ريال عماني"

            if baisa_amount > 0:
                if baisa_amount <= 10:
                    baisa_words = arabic_numbers.get(baisa_amount, str(baisa_amount))
                else:
                    baisa_words = str(baisa_amount)
                result += f" و {baisa_words} بيسة"

            return result
        else:
            return f"{amount} {currency}"

    except Exception as e:
        frappe.log_error(f"Error formatting amount in Arabic words: {str(e)}")
        return f"{amount} {currency}"


@frappe.whitelist()
def get_company_arabic_details(company):
    """
    Get company details in Arabic for invoice
    """
    try:
        company_doc = frappe.get_doc("Company", company)

        return {
            "company_arabic": getattr(company_doc, "company_arabic", ""),
            "company_address_arabic": getattr(company_doc, "company_address_arabic", ""),
            "company_phone": getattr(company_doc, "company_phone", ""),
            "company_email": getattr(company_doc, "email", ""),
            "company_website": getattr(company_doc, "company_website", ""),
            "tax_id": getattr(company_doc, "tax_id", ""),
        }
    except Exception as e:
        frappe.log_error(f"Error getting company Arabic details: {str(e)}")
        return {}


@frappe.whitelist()
def calculate_invoice_totals_with_vat(items, tax_template=None):
    """
    Calculate invoice totals with Oman VAT (5%)
    """
    try:
        subtotal = 0
        for item in items:
            item_amount = float(item.get("qty", 1)) * float(item.get("rate", 0))
            subtotal += item_amount

        vat_rate = 5.0  # Oman VAT rate
        vat_amount = (subtotal * vat_rate) / 100
        grand_total = subtotal + vat_amount

        return {
            "net_total": round(subtotal, 3),
            "total_taxes_and_charges": round(vat_amount, 3),
            "grand_total": round(grand_total, 3),
            "vat_rate": vat_rate,
            "in_words": format_amount_in_words_arabic(grand_total),
        }

    except Exception as e:
        frappe.log_error(f"Error calculating invoice totals: {str(e)}")
        return {}


def validate_oman_business_requirements(doc, method):
    """
    Validate invoice against Oman business requirements
    Called as a hook on Sales Invoice validation
    """
    if doc.doctype != "Sales Invoice":
        return

    # Generate tax invoice number if not exists
    if not doc.tax_invoice_number:
        doc.tax_invoice_number = generate_tax_invoice_number(doc.company, doc.posting_date)

    # Generate e-invoice UUID if not exists
    if not doc.e_invoice_uuid:
        doc.e_invoice_uuid = generate_e_invoice_uuid()

    # Validate VAT compliance
    validation_result = validate_oman_vat_invoice(doc.name if doc.name else "New Invoice")
    if not validation_result["is_valid"]:
        error_msg = "\n".join(validation_result["errors"])
        frappe.throw(_("VAT Compliance Errors:\n{0}").format(error_msg))


@frappe.whitelist()
def get_invoice_print_languages():
    """
    Get available print languages for invoices
    """
    return [
        {"value": "English", "label": _("English")},
        {"value": "Arabic", "label": _("Arabic")},
        {"value": "Bilingual", "label": _("Bilingual (Arabic/English)")},
    ]


@frappe.whitelist()
def format_date_arabic(date_str):
    """
    Format date in Arabic locale
    """
    try:
        date_obj = getdate(date_str)

        # Arabic month names
        arabic_months = [
            "يناير",
            "فبراير",
            "مارس",
            "أبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
        ]

        # Convert to Arabic numerals
        day = convert_to_arabic_numerals(str(date_obj.day))
        month = arabic_months[date_obj.month - 1]
        year = convert_to_arabic_numerals(str(date_obj.year))

        return f"{day} {month} {year}"

    except Exception as e:
        try:
            return formatdate(date_str, "dd/MM/yyyy")
        except:
            return str(date_str)


def convert_to_arabic_numerals(text):
    """
    Convert Western numerals to Arabic-Indic numerals
    """
    arabic_numerals = {
        "0": "٠",
        "1": "١",
        "2": "٢",
        "3": "٣",
        "4": "٤",
        "5": "٥",
        "6": "٦",
        "7": "٧",
        "8": "٨",
        "9": "٩",
    }

    for western, arabic in arabic_numerals.items():
        text = text.replace(western, arabic)
    return text


@frappe.whitelist()
def generate_invoice_qr_code_data(doc_name):
    """
    Generate QR code data for e-invoice compliance (placeholder)
    Will be expanded in the QR code implementation subtask
    """
    try:
        doc = frappe.get_doc("Sales Invoice", doc_name)

        # Basic QR code data structure for Oman e-invoice
        qr_data = {
            "seller_name": doc.company,
            "vat_number": doc.company_tax_id or "",
            "timestamp": get_datetime().isoformat(),
            "invoice_total": str(doc.grand_total),
            "vat_amount": str(doc.total_taxes_and_charges or 0),
            "uuid": doc.e_invoice_uuid or generate_e_invoice_uuid(),
        }

        # Convert to string format (will be used for QR code generation)
        qr_string = f"1:{qr_data['seller_name']}|2:{qr_data['vat_number']}|3:{qr_data['timestamp']}|4:{qr_data['invoice_total']}|5:{qr_data['vat_amount']}|6:{qr_data['uuid']}"

        return qr_string

    except Exception as e:
        frappe.log_error(f"Error generating QR code data: {str(e)}")
        return ""
