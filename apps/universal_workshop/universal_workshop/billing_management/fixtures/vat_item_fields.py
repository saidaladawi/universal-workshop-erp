# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_vat_item_fields():
    """
    Install custom fields for VAT settings on items
    """

    custom_fields = {
        "Item": [
            {
                "fieldname": "vat_settings_section",
                "fieldtype": "Section Break",
                "label": _("VAT Settings"),
                "insert_after": "item_tax_template",
                "collapsible": 1,
            },
            {
                "fieldname": "is_zero_rated_item",
                "fieldtype": "Check",
                "label": _("Zero Rated Item"),
                "insert_after": "vat_settings_section",
                "default": 0,
                "description": _(
                    "Check if this item is zero-rated for VAT (e.g., basic food items, medicines)"
                ),
            },
            {
                "fieldname": "is_vat_exempt",
                "fieldtype": "Check",
                "label": _("VAT Exempt"),
                "insert_after": "is_zero_rated_item",
                "default": 0,
                "description": _("Check if this item is completely exempt from VAT"),
            },
            {
                "fieldname": "vat_exemption_reason",
                "fieldtype": "Select",
                "label": _("VAT Exemption Reason"),
                "insert_after": "is_vat_exempt",
                "options": "\nBasic Food Items\nMedicines\nEducational Materials\nFinancial Services\nInsurance Services\nReal Estate\nOther",
                "depends_on": "eval:doc.is_vat_exempt || doc.is_zero_rated_item",
                "description": _("Specify the reason for VAT exemption/zero-rating"),
            },
            {
                "fieldname": "vat_category_override",
                "fieldtype": "Select",
                "label": _("VAT Category Override"),
                "insert_after": "vat_exemption_reason",
                "options": "\nStandard (5%)\nZero Rated (0%)\nExempt (No VAT)\nReduced Rate",
                "description": _("Override automatic VAT category determination"),
            },
        ],
        "Customer": [
            {
                "fieldname": "customer_type_vat",
                "fieldtype": "Select",
                "label": _("Customer Type (VAT)"),
                "insert_after": "customer_type",
                "options": "\nDomestic B2B\nDomestic B2C\nGCC Export\nInternational Export\nGovernment Entity\nVAT Exempt Entity",
                "description": _("Customer type for VAT calculation purposes"),
            },
            {
                "fieldname": "is_export_customer",
                "fieldtype": "Check",
                "label": _("Export Customer"),
                "insert_after": "customer_type_vat",
                "default": 0,
                "description": _("Check if this customer is for export transactions (zero-rated)"),
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "vat_calculation_section",
                "fieldtype": "Section Break",
                "label": _("VAT Calculation Details"),
                "insert_after": "e_invoice_uuid",
                "collapsible": 1,
            },
            {
                "fieldname": "is_export_invoice",
                "fieldtype": "Check",
                "label": _("Export Invoice"),
                "insert_after": "vat_calculation_section",
                "default": 0,
                "description": _("Check if this is an export invoice (zero-rated for VAT)"),
            },
            {
                "fieldname": "vat_calculation_method",
                "fieldtype": "Select",
                "label": _("VAT Calculation Method"),
                "insert_after": "is_export_invoice",
                "options": "Automatic\nManual\nTemplate Based",
                "default": "Automatic",
                "description": _("Method used for VAT calculation"),
            },
            {
                "fieldname": "automatic_vat_details",
                "fieldtype": "Long Text",
                "label": _("Automatic VAT Calculation Details"),
                "insert_after": "vat_calculation_method",
                "read_only": 1,
                "description": _("Details of automatic VAT calculation breakdown"),
            },
            {
                "fieldname": "vat_compliance_status",
                "fieldtype": "Select",
                "label": _("VAT Compliance Status"),
                "insert_after": "automatic_vat_details",
                "options": "\nValid\nInvalid\nPending Validation\nRequires Review",
                "read_only": 1,
                "description": _("E-invoice compliance validation status"),
            },
            {
                "fieldname": "vat_compliance_errors",
                "fieldtype": "Small Text",
                "label": _("VAT Compliance Errors"),
                "insert_after": "vat_compliance_status",
                "read_only": 1,
                "description": _("List of VAT compliance validation errors"),
            },
        ],
    }

    try:
        create_custom_fields(custom_fields)
        frappe.db.commit()
        frappe.msgprint(_("VAT item fields installed successfully"))

    except Exception as e:
        frappe.log_error(f"Error installing VAT item fields: {str(e)}")
        frappe.throw(_("Failed to install VAT item fields: {0}").format(str(e)))


@frappe.whitelist()
def update_item_vat_settings(item_code, is_zero_rated=0, is_exempt=0, exemption_reason=""):
    """
    Update VAT settings for an item
    """
    try:
        item_doc = frappe.get_doc("Item", item_code)

        if hasattr(item_doc, "is_zero_rated_item"):
            item_doc.is_zero_rated_item = int(is_zero_rated)

        if hasattr(item_doc, "is_vat_exempt"):
            item_doc.is_vat_exempt = int(is_exempt)

        if hasattr(item_doc, "vat_exemption_reason") and exemption_reason:
            item_doc.vat_exemption_reason = exemption_reason

        item_doc.save()
        frappe.db.commit()

        return {"success": True, "message": _("Item VAT settings updated successfully")}

    except Exception as e:
        frappe.log_error(f"Error updating item VAT settings: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_item_vat_category(item_code):
    """
    Get VAT category for an item
    """
    try:
        item_doc = frappe.get_doc("Item", item_code)

        if getattr(item_doc, "is_vat_exempt", 0):
            return "exempt"
        elif getattr(item_doc, "is_zero_rated_item", 0):
            return "zero_rated"
        else:
            return "standard"

    except Exception as e:
        frappe.log_error(f"Error getting item VAT category: {str(e)}")
        return "standard"


@frappe.whitelist()
def bulk_update_item_vat_categories(items_data):
    """
    Bulk update VAT categories for multiple items
    items_data should be a JSON string with format:
    [{"item_code": "ITEM001", "vat_category": "zero_rated", "reason": "Basic Food Items"}, ...]
    """
    try:
        import json

        items = json.loads(items_data) if isinstance(items_data, str) else items_data

        updated_count = 0
        errors = []

        for item_data in items:
            try:
                item_code = item_data.get("item_code")
                vat_category = item_data.get("vat_category", "standard")
                reason = item_data.get("reason", "")

                item_doc = frappe.get_doc("Item", item_code)

                # Reset all VAT flags first
                if hasattr(item_doc, "is_zero_rated_item"):
                    item_doc.is_zero_rated_item = 0
                if hasattr(item_doc, "is_vat_exempt"):
                    item_doc.is_vat_exempt = 0

                # Set appropriate flag based on category
                if vat_category == "zero_rated":
                    item_doc.is_zero_rated_item = 1
                elif vat_category == "exempt":
                    item_doc.is_vat_exempt = 1

                if hasattr(item_doc, "vat_exemption_reason") and reason:
                    item_doc.vat_exemption_reason = reason

                item_doc.save()
                updated_count += 1

            except Exception as e:
                errors.append(f"{item_code}: {str(e)}")

        frappe.db.commit()

        return {
            "success": True,
            "updated_count": updated_count,
            "errors": errors,
            "message": _("Bulk update completed. {0} items updated.").format(updated_count),
        }

    except Exception as e:
        frappe.log_error(f"Error in bulk VAT category update: {str(e)}")
        return {"success": False, "message": str(e)}
