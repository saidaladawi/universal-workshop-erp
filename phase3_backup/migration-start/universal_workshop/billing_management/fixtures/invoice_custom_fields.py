# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_invoice_custom_fields():
    """
    Install custom fields for bilingual invoice support
    """

    custom_fields = {
        "Company": [
            {
                "fieldname": "company_arabic_section",
                "fieldtype": "Section Break",
                "label": _("Arabic Information"),
                "insert_after": "website",
                "collapsible": 1,
            },
            {
                "fieldname": "company_arabic",
                "fieldtype": "Data",
                "label": _("Company Name (Arabic)"),
                "insert_after": "company_arabic_section",
                "translatable": 1,
            },
            {
                "fieldname": "company_address_arabic",
                "fieldtype": "Small Text",
                "label": _("Company Address (Arabic)"),
                "insert_after": "company_arabic",
                "translatable": 1,
            },
            {
                "fieldname": "company_phone",
                "fieldtype": "Data",
                "label": _("Company Phone"),
                "insert_after": "company_address_arabic",
                "options": "Phone",
            },
            {
                "fieldname": "company_website",
                "fieldtype": "Data",
                "label": _("Company Website"),
                "insert_after": "company_phone",
                "options": "URL",
            },
        ],
        "Customer": [
            {
                "fieldname": "customer_name_arabic",
                "fieldtype": "Data",
                "label": _("Customer Name (Arabic)"),
                "insert_after": "customer_name",
                "translatable": 1,
                "in_list_view": 1,
            }
        ],
        "Address": [
            {
                "fieldname": "address_arabic_section",
                "fieldtype": "Section Break",
                "label": _("Arabic Address"),
                "insert_after": "country",
                "collapsible": 1,
            },
            {
                "fieldname": "address_line1_arabic",
                "fieldtype": "Data",
                "label": _("Address Line 1 (Arabic)"),
                "insert_after": "address_arabic_section",
                "translatable": 1,
            },
            {
                "fieldname": "address_line2_arabic",
                "fieldtype": "Data",
                "label": _("Address Line 2 (Arabic)"),
                "insert_after": "address_line1_arabic",
                "translatable": 1,
            },
            {
                "fieldname": "city_arabic",
                "fieldtype": "Data",
                "label": _("City (Arabic)"),
                "insert_after": "address_line2_arabic",
                "translatable": 1,
            },
        ],
        "Item": [
            {
                "fieldname": "item_arabic_section",
                "fieldtype": "Section Break",
                "label": _("Arabic Information"),
                "insert_after": "description",
                "collapsible": 1,
            },
            {
                "fieldname": "item_name_arabic",
                "fieldtype": "Data",
                "label": _("Item Name (Arabic)"),
                "insert_after": "item_arabic_section",
                "translatable": 1,
            },
            {
                "fieldname": "description_arabic",
                "fieldtype": "Small Text",
                "label": _("Description (Arabic)"),
                "insert_after": "item_name_arabic",
                "translatable": 1,
            },
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "item_name_arabic",
                "fieldtype": "Data",
                "label": _("Item Name (Arabic)"),
                "insert_after": "item_name",
                "read_only": 1,
                "fetch_from": "item_code.item_name_arabic",
            },
            {
                "fieldname": "description_arabic",
                "fieldtype": "Small Text",
                "label": _("Description (Arabic)"),
                "insert_after": "description",
                "fetch_from": "item_code.description_arabic",
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "customer_name_arabic",
                "fieldtype": "Data",
                "label": _("Customer Name (Arabic)"),
                "insert_after": "customer_name",
                "read_only": 1,
                "fetch_from": "customer.customer_name_arabic",
            },
            {
                "fieldname": "invoice_language_section",
                "fieldtype": "Section Break",
                "label": _("Invoice Language & Compliance"),
                "insert_after": "customer_name_arabic",
                "collapsible": 1,
            },
            {
                "fieldname": "invoice_language",
                "fieldtype": "Select",
                "label": _("Invoice Language"),
                "insert_after": "invoice_language_section",
                "options": "English\nArabic\nBilingual",
                "default": "Bilingual",
            },
            {
                "fieldname": "qr_code",
                "fieldtype": "Data",
                "label": _("QR Code"),
                "insert_after": "invoice_language",
                "read_only": 1,
                "description": _("E-invoice QR code for Oman compliance"),
            },
            {
                "fieldname": "e_invoice_uuid",
                "fieldtype": "Data",
                "label": _("E-Invoice UUID"),
                "insert_after": "qr_code",
                "read_only": 1,
                "unique": 1,
                "description": _("Unique identifier for e-invoice"),
            },
            {
                "fieldname": "tax_invoice_number",
                "fieldtype": "Data",
                "label": _("Tax Invoice Number"),
                "insert_after": "e_invoice_uuid",
                "read_only": 1,
                "description": _("Sequential tax invoice number for VAT compliance"),
            },
        ],
    }

    try:
        create_custom_fields(custom_fields)
        frappe.db.commit()
        frappe.msgprint(_("Invoice custom fields installed successfully"))

    except Exception as e:
        frappe.log_error(f"Error installing invoice custom fields: {str(e)}")
        frappe.throw(_("Failed to install invoice custom fields: {0}").format(str(e)))


@frappe.whitelist()
def get_arabic_customer_name(customer):
    """
    Get Arabic customer name for invoice
    """
    if not customer:
        return ""

    return frappe.db.get_value("Customer", customer, "customer_name_arabic") or ""


@frappe.whitelist()
def get_arabic_item_details(item_code):
    """
    Get Arabic item details for invoice line items
    """
    if not item_code:
        return {}

    item_details = (
        frappe.db.get_value(
            "Item", item_code, ["item_name_arabic", "description_arabic"], as_dict=True
        )
        or {}
    )

    return {
        "item_name_arabic": item_details.get("item_name_arabic", ""),
        "description_arabic": item_details.get("description_arabic", ""),
    }
