# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_vat_custom_fields():
    """
    Install custom fields for VAT numbers on Customer and Supplier forms
    """

    custom_fields = {
        "Customer": [
            {
                "fieldname": "oman_vat_section",
                "fieldtype": "Section Break",
                "label": _("VAT Information"),
                "insert_after": "tax_id",
                "collapsible": 1,
            },
            {
                "fieldname": "oman_vat_number",
                "fieldtype": "Data",
                "label": _("Oman VAT Number"),
                "insert_after": "oman_vat_section",
                "description": _("Format: OMxxxxxxxxxxxxxxx (OM followed by 15 digits)"),
                "unique": 1,
                "translatable": 0,
            },
            {
                "fieldname": "oman_vat_number_ar",
                "fieldtype": "Data",
                "label": _("رقم ضريبة القيمة المضافة العمانية"),
                "insert_after": "oman_vat_number",
                "description": _("نفس الرقم بالعربية"),
                "translatable": 1,
                "depends_on": "oman_vat_number",
            },
            {
                "fieldname": "vat_exemption_reason",
                "fieldtype": "Select",
                "label": _("VAT Exemption Reason"),
                "insert_after": "oman_vat_number_ar",
                "options": "\nNot Registered\nExempt Entity\nZero Rated\nOut of Scope",
                "depends_on": "eval:!doc.oman_vat_number",
            },
            {
                "fieldname": "vat_column_break",
                "fieldtype": "Column Break",
                "insert_after": "vat_exemption_reason",
            },
            {
                "fieldname": "vat_registration_date",
                "fieldtype": "Date",
                "label": _("VAT Registration Date"),
                "insert_after": "vat_column_break",
                "depends_on": "oman_vat_number",
            },
            {
                "fieldname": "vat_certificate_attachment",
                "fieldtype": "Attach",
                "label": _("VAT Certificate"),
                "insert_after": "vat_registration_date",
                "depends_on": "oman_vat_number",
            },
        ],
        "Supplier": [
            {
                "fieldname": "oman_vat_section",
                "fieldtype": "Section Break",
                "label": _("VAT Information"),
                "insert_after": "tax_id",
                "collapsible": 1,
            },
            {
                "fieldname": "oman_vat_number",
                "fieldtype": "Data",
                "label": _("Oman VAT Number"),
                "insert_after": "oman_vat_section",
                "description": _("Format: OMxxxxxxxxxxxxxxx (OM followed by 15 digits)"),
                "unique": 1,
                "translatable": 0,
            },
            {
                "fieldname": "oman_vat_number_ar",
                "fieldtype": "Data",
                "label": _("رقم ضريبة القيمة المضافة العمانية"),
                "insert_after": "oman_vat_number",
                "description": _("نفس الرقم بالعربية"),
                "translatable": 1,
                "depends_on": "oman_vat_number",
            },
            {
                "fieldname": "vat_exemption_reason",
                "fieldtype": "Select",
                "label": _("VAT Exemption Reason"),
                "insert_after": "oman_vat_number_ar",
                "options": "\nNot Registered\nExempt Entity\nZero Rated\nOut of Scope",
                "depends_on": "eval:!doc.oman_vat_number",
            },
            {
                "fieldname": "vat_column_break",
                "fieldtype": "Column Break",
                "insert_after": "vat_exemption_reason",
            },
            {
                "fieldname": "vat_registration_date",
                "fieldtype": "Date",
                "label": _("VAT Registration Date"),
                "insert_after": "vat_column_break",
                "depends_on": "oman_vat_number",
            },
            {
                "fieldname": "vat_certificate_attachment",
                "fieldtype": "Attach",
                "label": _("VAT Certificate"),
                "insert_after": "vat_registration_date",
                "depends_on": "oman_vat_number",
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "oman_vat_section",
                "fieldtype": "Section Break",
                "label": _("Oman VAT Details"),
                "insert_after": "tax_id",
                "collapsible": 1,
            },
            {
                "fieldname": "customer_vat_number",
                "fieldtype": "Data",
                "label": _("Customer VAT Number"),
                "insert_after": "oman_vat_section",
                "fetch_from": "customer.oman_vat_number",
                "read_only": 1,
            },
            {
                "fieldname": "vat_compliance_status",
                "fieldtype": "Select",
                "label": _("VAT Compliance Status"),
                "insert_after": "customer_vat_number",
                "options": "Standard VAT\nZero Rated\nExempt\nOut of Scope",
                "default": "Standard VAT",
            },
            {
                "fieldname": "qr_code_section",
                "fieldtype": "Section Break",
                "label": _("E-Invoice QR Code"),
                "insert_after": "vat_compliance_status",
                "collapsible": 1,
            },
            {
                "fieldname": "qr_code_data",
                "fieldtype": "Long Text",
                "label": _("QR Code Data"),
                "insert_after": "qr_code_section",
                "read_only": 1,
                "description": _("TLV encoded data for Oman e-invoice QR code"),
            },
            {
                "fieldname": "qr_code_column_break",
                "fieldtype": "Column Break",
                "insert_after": "qr_code_data",
            },
            {
                "fieldname": "qr_code_image",
                "fieldtype": "Attach Image",
                "label": _("QR Code Image"),
                "insert_after": "qr_code_column_break",
                "read_only": 1,
            },
        ],
        "Purchase Invoice": [
            {
                "fieldname": "oman_vat_section",
                "fieldtype": "Section Break",
                "label": _("Oman VAT Details"),
                "insert_after": "tax_id",
                "collapsible": 1,
            },
            {
                "fieldname": "supplier_vat_number",
                "fieldtype": "Data",
                "label": _("Supplier VAT Number"),
                "insert_after": "oman_vat_section",
                "fetch_from": "supplier.oman_vat_number",
                "read_only": 1,
            },
            {
                "fieldname": "vat_compliance_status",
                "fieldtype": "Select",
                "label": _("VAT Compliance Status"),
                "insert_after": "supplier_vat_number",
                "options": "Standard VAT\nZero Rated\nExempt\nOut of Scope",
                "default": "Standard VAT",
            },
        ],
    }

    try:
        create_custom_fields(custom_fields, update=True)
        frappe.db.commit()
        frappe.logger().info("VAT custom fields installed successfully")

    except Exception as e:
        frappe.logger().error(f"Error installing VAT custom fields: {str(e)}")
        frappe.throw(_("Failed to install VAT custom fields: {0}").format(str(e)))


def uninstall_vat_custom_fields():
    """
    Remove VAT custom fields
    """
    field_names = [
        "oman_vat_section",
        "oman_vat_number",
        "oman_vat_number_ar",
        "vat_exemption_reason",
        "vat_column_break",
        "vat_registration_date",
        "vat_certificate_attachment",
        "customer_vat_number",
        "supplier_vat_number",
        "vat_compliance_status",
        "qr_code_section",
        "qr_code_data",
        "qr_code_column_break",
        "qr_code_image",
    ]

    doctypes = ["Customer", "Supplier", "Sales Invoice", "Purchase Invoice"]

    try:
        for doctype in doctypes:
            for field_name in field_names:
                if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
                    frappe.delete_doc(
                        "Custom Field",
                        frappe.db.get_value(
                            "Custom Field", {"dt": doctype, "fieldname": field_name}, "name"
                        ),
                    )

        frappe.db.commit()
        frappe.logger().info("VAT custom fields uninstalled successfully")

    except Exception as e:
        frappe.logger().error(f"Error uninstalling VAT custom fields: {str(e)}")


@frappe.whitelist()
def setup_vat_fields():
    """
    Whitelist method to setup VAT custom fields
    """
    install_vat_custom_fields()
    return {"status": "success", "message": _("VAT custom fields installed successfully")}
