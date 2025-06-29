# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def create_qr_code_custom_fields():
    """
    Create custom fields for QR code storage and e-invoice compliance
    """

    # Sales Invoice QR Code Fields
    sales_invoice_qr_fields = [
        {
            "fieldname": "qr_code_section",
            "fieldtype": "Section Break",
            "label": _("E-Invoice QR Code"),
            "insert_after": "taxes_and_charges",
            "collapsible": 1,
            "collapsible_depends_on": "qr_code_generated",
        },
        {
            "fieldname": "qr_code_data",
            "fieldtype": "Long Text",
            "label": _("QR Code Data (TLV Base64)"),
            "insert_after": "qr_code_section",
            "read_only": 1,
            "description": _("TLV encoded QR code data for Oman e-invoice compliance"),
        },
        {
            "fieldname": "qr_code_image",
            "fieldtype": "Attach Image",
            "label": _("QR Code Image"),
            "insert_after": "qr_code_data",
            "read_only": 1,
            "description": _("Generated QR code image for printing on invoice"),
        },
        {
            "fieldname": "qr_code_column_break",
            "fieldtype": "Column Break",
            "insert_after": "qr_code_image",
        },
        {
            "fieldname": "qr_code_generated",
            "fieldtype": "Check",
            "label": _("QR Code Generated"),
            "insert_after": "qr_code_column_break",
            "default": 0,
            "read_only": 1,
        },
        {
            "fieldname": "qr_code_timestamp",
            "fieldtype": "Datetime",
            "label": _("QR Code Generated On"),
            "insert_after": "qr_code_generated",
            "read_only": 1,
        },
        {
            "fieldname": "e_invoice_compliance_status",
            "fieldtype": "Select",
            "label": _("E-Invoice Compliance Status"),
            "insert_after": "qr_code_timestamp",
            "options": "\nPending\nCompliant\nNon-Compliant\nError",
            "default": "Pending",
            "read_only": 1,
        },
        {
            "fieldname": "e_invoice_uuid",
            "fieldtype": "Data",
            "label": _("E-Invoice UUID"),
            "insert_after": "e_invoice_compliance_status",
            "read_only": 1,
            "unique": 1,
            "description": _("Unique identifier for e-invoice submission to OTA"),
        },
    ]

    # Company QR Configuration Fields
    company_qr_fields = [
        {
            "fieldname": "qr_config_section",
            "fieldtype": "Section Break",
            "label": _("QR Code Configuration"),
            "insert_after": "default_currency",
            "collapsible": 1,
        },
        {
            "fieldname": "qr_code_enabled",
            "fieldtype": "Check",
            "label": _("Enable QR Code Generation"),
            "insert_after": "qr_config_section",
            "default": 1,
            "description": _("Automatically generate QR codes for invoices"),
        },
        {
            "fieldname": "vat_number",
            "fieldtype": "Data",
            "label": _("VAT Registration Number"),
            "insert_after": "qr_code_enabled",
            "description": _("Enter Oman VAT number (format: OMxxxxxxxxxxxxxxx)"),
        },
        {
            "fieldname": "qr_config_column_break",
            "fieldtype": "Column Break",
            "insert_after": "vat_number",
        },
        {
            "fieldname": "company_name_ar",
            "fieldtype": "Data",
            "label": _("Company Name (Arabic)"),
            "insert_after": "qr_config_column_break",
            "description": _("Arabic company name for bilingual QR codes"),
        },
        {
            "fieldname": "e_invoice_ota_endpoint",
            "fieldtype": "Data",
            "label": _("OTA E-Invoice Endpoint"),
            "insert_after": "company_name_ar",
            "description": _("Oman Tax Authority e-invoice submission endpoint"),
        },
    ]

    # Customer QR Related Fields
    customer_qr_fields = [
        {
            "fieldname": "qr_preferences_section",
            "fieldtype": "Section Break",
            "label": _("E-Invoice Preferences"),
            "insert_after": "customer_primary_contact",
            "collapsible": 1,
        },
        {
            "fieldname": "prefer_arabic_invoice",
            "fieldtype": "Check",
            "label": _("Prefer Arabic Invoice"),
            "insert_after": "qr_preferences_section",
            "default": 0,
            "description": _("Generate invoices with Arabic as primary language"),
        },
        {
            "fieldname": "email_qr_invoice",
            "fieldtype": "Check",
            "label": _("Email QR Invoice"),
            "insert_after": "prefer_arabic_invoice",
            "default": 1,
            "description": _("Email invoice with QR code for validation"),
        },
    ]

    # Create all custom fields
    field_groups = [
        ("Sales Invoice", sales_invoice_qr_fields),
        ("Company", company_qr_fields),
        ("Customer", customer_qr_fields),
    ]

    for doctype, fields in field_groups:
        create_custom_fields_for_doctype(doctype, fields)


def create_custom_fields_for_doctype(doctype, fields):
    """
    Create custom fields for a specific DocType
    """
    for field in fields:
        try:
            # Check if field already exists
            existing_field = frappe.db.get_value(
                "Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}, "name"
            )

            if existing_field:
                # Update existing field
                custom_field = frappe.get_doc("Custom Field", existing_field)
                for key, value in field.items():
                    if key != "fieldname":  # Don't update fieldname
                        setattr(custom_field, key, value)
                custom_field.save()
                print(f"Updated custom field {field['fieldname']} in {doctype}")
            else:
                # Create new field
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = doctype
                for key, value in field.items():
                    setattr(custom_field, key, value)
                custom_field.insert()
                print(f"Created custom field {field['fieldname']} in {doctype}")

        except Exception as e:
            print(f"Error creating field {field['fieldname']} in {doctype}: {str(e)}")
            frappe.log_error(f"QR Code field creation error: {str(e)}")


def remove_qr_code_custom_fields():
    """
    Remove QR code custom fields (for uninstallation)
    """
    qr_fields = [
        # Sales Invoice fields
        "qr_code_section",
        "qr_code_data",
        "qr_code_image",
        "qr_code_column_break",
        "qr_code_generated",
        "qr_code_timestamp",
        "e_invoice_compliance_status",
        "e_invoice_uuid",
        # Company fields
        "qr_config_section",
        "qr_code_enabled",
        "vat_number",
        "qr_config_column_break",
        "company_name_ar",
        "e_invoice_ota_endpoint",
        # Customer fields
        "qr_preferences_section",
        "prefer_arabic_invoice",
        "email_qr_invoice",
    ]

    doctypes = ["Sales Invoice", "Company", "Customer"]

    for doctype in doctypes:
        for fieldname in qr_fields:
            try:
                existing_field = frappe.db.get_value(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}, "name"
                )

                if existing_field:
                    frappe.delete_doc("Custom Field", existing_field)
                    print(f"Deleted custom field {fieldname} from {doctype}")

            except Exception as e:
                print(f"Error removing field {fieldname} from {doctype}: {str(e)}")


# Installation function
def install_qr_code_fields():
    """
    Install QR code custom fields during app installation
    """
    print("Installing QR Code custom fields...")
    create_qr_code_custom_fields()
    print("QR Code custom fields installation completed!")


# Uninstallation function
def uninstall_qr_code_fields():
    """
    Uninstall QR code custom fields during app removal
    """
    print("Removing QR Code custom fields...")
    remove_qr_code_custom_fields()
    print("QR Code custom fields removal completed!")
