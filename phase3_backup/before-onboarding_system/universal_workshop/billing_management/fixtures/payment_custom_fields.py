# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def create_payment_custom_fields():
    """
    Create custom fields for payment gateway integration and multi-currency support
    """

    # Sales Invoice Payment Fields
    sales_invoice_payment_fields = [
        {
            "fieldname": "payment_gateway_section",
            "fieldtype": "Section Break",
            "label": _("Payment Gateway"),
            "insert_after": "payment_schedule",
            "collapsible": 1,
            "collapsible_depends_on": "enable_online_payment",
        },
        {
            "fieldname": "enable_online_payment",
            "fieldtype": "Check",
            "label": _("Enable Online Payment"),
            "insert_after": "payment_gateway_section",
            "default": 0,
            "description": _("Allow customers to pay online through payment gateways"),
        },
        {
            "fieldname": "preferred_payment_gateway",
            "fieldtype": "Select",
            "label": _("Preferred Payment Gateway"),
            "insert_after": "enable_online_payment",
            "options": "\nThawani\nMyFatoorah\nPayTabs\nSohar International",
            "depends_on": "enable_online_payment",
            "description": _("Select preferred payment gateway for this invoice"),
        },
        {
            "fieldname": "payment_gateway_column_break",
            "fieldtype": "Column Break",
            "insert_after": "preferred_payment_gateway",
        },
        {
            "fieldname": "payment_reference_number",
            "fieldtype": "Data",
            "label": _("Payment Reference Number"),
            "insert_after": "payment_gateway_column_break",
            "read_only": 1,
            "description": _("Unique reference number for payment tracking"),
        },
        {
            "fieldname": "payment_status",
            "fieldtype": "Select",
            "label": _("Payment Status"),
            "insert_after": "payment_reference_number",
            "options": "\nPending\nInitiated\nProcessing\nCompleted\nFailed\nCancelled\nRefunded",
            "default": "Pending",
            "read_only": 1,
        },
        {
            "fieldname": "payment_gateway_response",
            "fieldtype": "Long Text",
            "label": _("Payment Gateway Response"),
            "insert_after": "payment_status",
            "read_only": 1,
            "hidden": 1,
            "description": _("Gateway response data for debugging"),
        },
        {
            "fieldname": "payment_url",
            "fieldtype": "Data",
            "label": _("Payment URL"),
            "insert_after": "payment_gateway_response",
            "read_only": 1,
            "description": _("URL for customer to complete payment"),
        },
        {
            "fieldname": "multi_currency_section",
            "fieldtype": "Section Break",
            "label": _("Multi-Currency Details"),
            "insert_after": "payment_url",
            "collapsible": 1,
            "depends_on": 'eval:doc.currency != "OMR"',
        },
        {
            "fieldname": "original_currency",
            "fieldtype": "Link",
            "label": _("Original Currency"),
            "insert_after": "multi_currency_section",
            "options": "Currency",
            "read_only": 1,
            "description": _("Original invoice currency before conversion"),
        },
        {
            "fieldname": "original_amount",
            "fieldtype": "Currency",
            "label": _("Original Amount"),
            "insert_after": "original_currency",
            "read_only": 1,
            "precision": 3,
            "description": _("Original invoice amount before currency conversion"),
        },
        {
            "fieldname": "currency_conversion_rate",
            "fieldtype": "Float",
            "label": _("Currency Conversion Rate"),
            "insert_after": "original_amount",
            "read_only": 1,
            "precision": 6,
            "description": _("Exchange rate used for currency conversion"),
        },
        {
            "fieldname": "conversion_date",
            "fieldtype": "Date",
            "label": _("Conversion Date"),
            "insert_after": "currency_conversion_rate",
            "read_only": 1,
            "description": _("Date when currency conversion was applied"),
        },
    ]

    # Customer Payment Preferences
    customer_payment_fields = [
        {
            "fieldname": "payment_preferences_section",
            "fieldtype": "Section Break",
            "label": _("Payment Preferences"),
            "insert_after": "qr_preferences_section",
            "collapsible": 1,
        },
        {
            "fieldname": "preferred_payment_method",
            "fieldtype": "Select",
            "label": _("Preferred Payment Method"),
            "insert_after": "payment_preferences_section",
            "options": "\nCash\nCard\nBank Transfer\nOnline Payment\nCheque",
            "default": "Cash",
        },
        {
            "fieldname": "preferred_currency",
            "fieldtype": "Link",
            "label": _("Preferred Currency"),
            "insert_after": "preferred_payment_method",
            "options": "Currency",
            "default": "OMR",
            "description": _("Customer preferred currency for invoicing"),
        },
        {
            "fieldname": "payment_preferences_column_break",
            "fieldtype": "Column Break",
            "insert_after": "preferred_currency",
        },
        {
            "fieldname": "auto_send_payment_link",
            "fieldtype": "Check",
            "label": _("Auto Send Payment Link"),
            "insert_after": "payment_preferences_column_break",
            "default": 1,
            "description": _("Automatically send payment link when invoice is submitted"),
        },
        {
            "fieldname": "payment_terms_accepted",
            "fieldtype": "Check",
            "label": _("Payment Terms Accepted"),
            "insert_after": "auto_send_payment_link",
            "default": 0,
            "description": _("Customer has accepted payment terms and conditions"),
        },
    ]

    # Company Payment Gateway Settings
    company_payment_fields = [
        {
            "fieldname": "payment_gateway_config_section",
            "fieldtype": "Section Break",
            "label": _("Payment Gateway Configuration"),
            "insert_after": "e_invoice_ota_endpoint",
            "collapsible": 1,
        },
        {
            "fieldname": "enable_payment_gateways",
            "fieldtype": "Check",
            "label": _("Enable Payment Gateways"),
            "insert_after": "payment_gateway_config_section",
            "default": 1,
            "description": _("Enable online payment processing for this company"),
        },
        {
            "fieldname": "default_payment_gateway",
            "fieldtype": "Select",
            "label": _("Default Payment Gateway"),
            "insert_after": "enable_payment_gateways",
            "options": "\nThawani\nMyFatoorah\nPayTabs\nSohar International",
            "default": "Thawani",
            "depends_on": "enable_payment_gateways",
        },
        {
            "fieldname": "payment_config_column_break",
            "fieldtype": "Column Break",
            "insert_after": "default_payment_gateway",
        },
        {
            "fieldname": "payment_success_url",
            "fieldtype": "Data",
            "label": _("Payment Success URL"),
            "insert_after": "payment_config_column_break",
            "description": _("URL to redirect customers after successful payment"),
        },
        {
            "fieldname": "payment_cancel_url",
            "fieldtype": "Data",
            "label": _("Payment Cancel URL"),
            "insert_after": "payment_success_url",
            "description": _("URL to redirect customers after cancelled payment"),
        },
        {
            "fieldname": "payment_callback_url",
            "fieldtype": "Data",
            "label": _("Payment Callback URL"),
            "insert_after": "payment_cancel_url",
            "description": _("URL for payment gateway to send status updates"),
        },
    ]

    # Payment Entry Enhancement Fields
    payment_entry_fields = [
        {
            "fieldname": "gateway_details_section",
            "fieldtype": "Section Break",
            "label": _("Gateway Transaction Details"),
            "insert_after": "difference_amount",
            "collapsible": 1,
            "depends_on": 'eval:doc.mode_of_payment && doc.mode_of_payment.includes("Gateway")',
        },
        {
            "fieldname": "payment_gateway_used",
            "fieldtype": "Select",
            "label": _("Payment Gateway Used"),
            "insert_after": "gateway_details_section",
            "options": "\nThawani\nMyFatoorah\nPayTabs\nSohar International",
            "read_only": 1,
        },
        {
            "fieldname": "gateway_transaction_id",
            "fieldtype": "Data",
            "label": _("Gateway Transaction ID"),
            "insert_after": "payment_gateway_used",
            "read_only": 1,
            "description": _("Transaction ID from payment gateway"),
        },
        {
            "fieldname": "gateway_column_break",
            "fieldtype": "Column Break",
            "insert_after": "gateway_transaction_id",
        },
        {
            "fieldname": "gateway_fee_amount",
            "fieldtype": "Currency",
            "label": _("Gateway Fee Amount"),
            "insert_after": "gateway_column_break",
            "read_only": 1,
            "precision": 3,
            "description": _("Fee charged by payment gateway"),
        },
        {
            "fieldname": "net_amount_received",
            "fieldtype": "Currency",
            "label": _("Net Amount Received"),
            "insert_after": "gateway_fee_amount",
            "read_only": 1,
            "precision": 3,
            "description": _("Amount received after gateway fees"),
        },
    ]

    # Create all custom fields
    field_groups = [
        ("Sales Invoice", sales_invoice_payment_fields),
        ("Customer", customer_payment_fields),
        ("Company", company_payment_fields),
        ("Payment Entry", payment_entry_fields),
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
            frappe.log_error(f"Payment field creation error: {str(e)}")


def create_payment_modes():
    """
    Create payment modes for different gateways
    """
    payment_modes = [
        {"mode_of_payment": "Thawani Gateway", "type": "Electronic"},
        {"mode_of_payment": "MyFatoorah Gateway", "type": "Electronic"},
        {"mode_of_payment": "PayTabs Gateway", "type": "Electronic"},
        {"mode_of_payment": "Sohar International Gateway", "type": "Electronic"},
        {"mode_of_payment": "Online Payment", "type": "Electronic"},
    ]

    for mode_data in payment_modes:
        try:
            if not frappe.db.exists("Mode of Payment", mode_data["mode_of_payment"]):
                mode_doc = frappe.new_doc("Mode of Payment")
                mode_doc.mode_of_payment = mode_data["mode_of_payment"]
                mode_doc.type = mode_data["type"]
                mode_doc.enabled = 1
                mode_doc.insert()
                print(f"Created payment mode: {mode_data['mode_of_payment']}")
        except Exception as e:
            print(f"Error creating payment mode {mode_data['mode_of_payment']}: {str(e)}")


def create_payment_gateway_settings_doctypes():
    """
    Create custom DocTypes for payment gateway settings
    """
    gateway_settings = [
        {
            "name": "Thawani Gateway Settings",
            "fields": [
                {"fieldname": "api_key", "fieldtype": "Password", "label": "API Key"},
                {"fieldname": "test_mode", "fieldtype": "Check", "label": "Test Mode"},
                {"fieldname": "webhook_secret", "fieldtype": "Password", "label": "Webhook Secret"},
            ],
        },
        {
            "name": "MyFatoorah Gateway Settings",
            "fields": [
                {"fieldname": "api_token", "fieldtype": "Password", "label": "API Token"},
                {"fieldname": "test_mode", "fieldtype": "Check", "label": "Test Mode"},
                {"fieldname": "webhook_secret", "fieldtype": "Password", "label": "Webhook Secret"},
            ],
        },
        {
            "name": "PayTabs Gateway Settings",
            "fields": [
                {"fieldname": "profile_id", "fieldtype": "Data", "label": "Profile ID"},
                {"fieldname": "server_key", "fieldtype": "Password", "label": "Server Key"},
                {"fieldname": "client_key", "fieldtype": "Password", "label": "Client Key"},
                {"fieldname": "test_mode", "fieldtype": "Check", "label": "Test Mode"},
            ],
        },
        {
            "name": "Sohar Gateway Settings",
            "fields": [
                {"fieldname": "merchant_id", "fieldtype": "Data", "label": "Merchant ID"},
                {"fieldname": "api_key", "fieldtype": "Password", "label": "API Key"},
                {"fieldname": "test_mode", "fieldtype": "Check", "label": "Test Mode"},
            ],
        },
    ]

    for gateway in gateway_settings:
        create_gateway_settings_doctype(gateway["name"], gateway["fields"])


def create_gateway_settings_doctype(doctype_name, fields):
    """
    Create a gateway settings DocType programmatically
    """
    try:
        if frappe.db.exists("DocType", doctype_name):
            return  # DocType already exists

        # Create the DocType
        doctype_doc = frappe.new_doc("DocType")
        doctype_doc.module = "Universal Workshop"
        doctype_doc.name = doctype_name
        doctype_doc.custom = 1
        doctype_doc.istable = 0
        doctype_doc.issingle = 1  # Single DocType for settings
        doctype_doc.track_changes = 1

        # Add fields
        for i, field in enumerate(fields):
            field_doc = doctype_doc.append("fields")
            field_doc.fieldname = field["fieldname"]
            field_doc.fieldtype = field["fieldtype"]
            field_doc.label = field["label"]
            field_doc.idx = i + 1

            if field["fieldtype"] == "Password":
                field_doc.hidden = 1

        doctype_doc.insert()
        print(f"Created DocType: {doctype_name}")

    except Exception as e:
        print(f"Error creating DocType {doctype_name}: {str(e)}")
        frappe.log_error(f"DocType creation error: {str(e)}")


def remove_payment_custom_fields():
    """
    Remove payment custom fields (for uninstallation)
    """
    payment_fields = [
        # Sales Invoice fields
        "payment_gateway_section",
        "enable_online_payment",
        "preferred_payment_gateway",
        "payment_gateway_column_break",
        "payment_reference_number",
        "payment_status",
        "payment_gateway_response",
        "payment_url",
        "multi_currency_section",
        "original_currency",
        "original_amount",
        "currency_conversion_rate",
        "conversion_date",
        # Customer fields
        "payment_preferences_section",
        "preferred_payment_method",
        "preferred_currency",
        "payment_preferences_column_break",
        "auto_send_payment_link",
        "payment_terms_accepted",
        # Company fields
        "payment_gateway_config_section",
        "enable_payment_gateways",
        "default_payment_gateway",
        "payment_config_column_break",
        "payment_success_url",
        "payment_cancel_url",
        "payment_callback_url",
        # Payment Entry fields
        "gateway_details_section",
        "payment_gateway_used",
        "gateway_transaction_id",
        "gateway_column_break",
        "gateway_fee_amount",
        "net_amount_received",
    ]

    doctypes = ["Sales Invoice", "Customer", "Company", "Payment Entry"]

    for doctype in doctypes:
        for fieldname in payment_fields:
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
def install_payment_custom_fields():
    """
    Install payment custom fields during app installation
    """
    print("Installing Payment custom fields...")
    create_payment_custom_fields()
    create_payment_modes()
    create_payment_gateway_settings_doctypes()
    print("Payment custom fields installation completed!")


# Uninstallation function
def uninstall_payment_custom_fields():
    """
    Uninstall payment custom fields during app removal
    """
    print("Removing Payment custom fields...")
    remove_payment_custom_fields()
    print("Payment custom fields removal completed!")
