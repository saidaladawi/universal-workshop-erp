# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate
import json
import re
from datetime import datetime


class OmanVATCalculationEngine:
    """
    Automatic VAT calculation engine for Oman compliance
    Implements item-based and customer-based tax logic per ERPNext v15 best practices
    """

    def __init__(self, company=None):
        self.company = company or frappe.defaults.get_user_default("Company")
        self.vat_rate_standard = 5.0  # Oman standard VAT rate
        self.vat_rate_zero = 0.0  # Zero-rated items
        self.currency_precision = 3  # OMR requires 3 decimal places

    def calculate_invoice_vat(self, invoice_doc):
        """
        Calculate VAT for an entire Sales Invoice based on items and customer settings
        """
        if not invoice_doc:
            return {"error": "No invoice document provided"}

        try:
            vat_calculation = {
                "net_total": 0.0,
                "total_vat": 0.0,
                "grand_total": 0.0,
                "vat_breakdown": [],
                "customer_vat_status": self.get_customer_vat_status(invoice_doc.customer),
                "is_export_invoice": self.is_export_invoice(invoice_doc),
                "compliance_status": "valid",
            }

            # Calculate VAT for each invoice item
            for item in invoice_doc.items:
                item_vat = self.calculate_item_vat(
                    item_code=item.item_code,
                    qty=item.qty,
                    rate=item.rate,
                    customer=invoice_doc.customer,
                    is_export=vat_calculation["is_export_invoice"],
                )

                vat_calculation["vat_breakdown"].append(
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "amount": item_vat["amount"],
                        "vat_rate": item_vat["vat_rate"],
                        "vat_amount": item_vat["vat_amount"],
                        "total_amount": item_vat["total_amount"],
                        "vat_category": item_vat["vat_category"],
                    }
                )

                vat_calculation["net_total"] += item_vat["amount"]
                vat_calculation["total_vat"] += item_vat["vat_amount"]

            vat_calculation["grand_total"] = (
                vat_calculation["net_total"] + vat_calculation["total_vat"]
            )

            # Round to currency precision
            vat_calculation["net_total"] = round(
                vat_calculation["net_total"], self.currency_precision
            )
            vat_calculation["total_vat"] = round(
                vat_calculation["total_vat"], self.currency_precision
            )
            vat_calculation["grand_total"] = round(
                vat_calculation["grand_total"], self.currency_precision
            )

            # Validate e-invoice compliance
            compliance_check = self.validate_e_invoice_compliance(invoice_doc, vat_calculation)
            vat_calculation["compliance_status"] = compliance_check["status"]
            vat_calculation["compliance_errors"] = compliance_check.get("errors", [])

            return vat_calculation

        except Exception as e:
            frappe.log_error(f"VAT calculation error: {str(e)}")
            return {"error": f"VAT calculation failed: {str(e)}"}

    def calculate_item_vat(self, item_code, qty, rate, customer=None, is_export=False):
        """
        Calculate VAT for a single item based on item settings and customer context
        """
        try:
            item_doc = frappe.get_doc("Item", item_code)
            amount = flt(qty) * flt(rate)

            # Determine VAT category and rate
            vat_category = self.determine_vat_category(item_doc, customer, is_export)
            vat_rate = self.get_vat_rate_for_category(vat_category)

            # Calculate VAT amount
            vat_amount = (amount * vat_rate) / 100
            total_amount = amount + vat_amount

            return {
                "amount": round(amount, self.currency_precision),
                "vat_rate": vat_rate,
                "vat_amount": round(vat_amount, self.currency_precision),
                "total_amount": round(total_amount, self.currency_precision),
                "vat_category": vat_category,
            }

        except Exception as e:
            frappe.log_error(f"Item VAT calculation error for {item_code}: {str(e)}")
            return {
                "amount": flt(qty) * flt(rate),
                "vat_rate": self.vat_rate_standard,
                "vat_amount": (flt(qty) * flt(rate) * self.vat_rate_standard) / 100,
                "total_amount": flt(qty) * flt(rate) * 1.05,
                "vat_category": "standard",
            }

    def determine_vat_category(self, item_doc, customer=None, is_export=False):
        """
        Determine VAT category based on item properties and context
        """
        # Priority 1: Export transactions are zero-rated
        if is_export:
            return "zero_rated_export"

        # Priority 2: Check item-specific VAT settings
        if hasattr(item_doc, "is_zero_rated_item") and item_doc.is_zero_rated_item:
            return "zero_rated_item"

        if hasattr(item_doc, "is_vat_exempt") and item_doc.is_vat_exempt:
            return "exempt"

        # Priority 3: Check item tax template
        if hasattr(item_doc, "item_tax_template") and item_doc.item_tax_template:
            tax_template = frappe.get_doc("Item Tax Template", item_doc.item_tax_template)
            for tax in tax_template.taxes:
                if "VAT" in tax.tax_type and tax.tax_rate == 0:
                    return "zero_rated_template"

        # Priority 4: Check customer VAT status
        if customer:
            customer_vat_status = self.get_customer_vat_status(customer)
            if customer_vat_status == "non_vat_registered":
                return "standard"  # Still charge VAT, customer just can't claim it back

        # Default: Standard VAT rate
        return "standard"

    def get_vat_rate_for_category(self, vat_category):
        """
        Get VAT rate based on category
        """
        vat_rates = {
            "standard": self.vat_rate_standard,
            "zero_rated_export": 0.0,
            "zero_rated_item": 0.0,
            "zero_rated_template": 0.0,
            "exempt": 0.0,
        }

        return vat_rates.get(vat_category, self.vat_rate_standard)

    def get_customer_vat_status(self, customer):
        """
        Determine customer VAT registration status
        """
        try:
            customer_doc = frappe.get_doc("Customer", customer)

            # Check if customer has VAT number
            vat_number = getattr(customer_doc, "vat_number", "") or getattr(
                customer_doc, "tax_id", ""
            )

            if vat_number and self.validate_oman_vat_number(vat_number):
                return "vat_registered"
            else:
                return "non_vat_registered"

        except Exception as e:
            frappe.log_error(f"Error getting customer VAT status: {str(e)}")
            return "unknown"

    def is_export_invoice(self, invoice_doc):
        """
        Determine if this is an export invoice (zero-rated for VAT)
        """
        try:
            # Check customer country
            if hasattr(invoice_doc, "customer_address"):
                address = frappe.get_doc("Address", invoice_doc.customer_address)
                if hasattr(address, "country") and address.country != "Oman":
                    return True

            # Check customer group for export designation
            customer_doc = frappe.get_doc("Customer", invoice_doc.customer)
            if hasattr(customer_doc, "customer_group"):
                if "export" in customer_doc.customer_group.lower():
                    return True

            # Check invoice-level export flag
            if hasattr(invoice_doc, "is_export_invoice") and invoice_doc.is_export_invoice:
                return True

            return False

        except Exception as e:
            frappe.log_error(f"Error checking export status: {str(e)}")
            return False

    def validate_oman_vat_number(self, vat_number):
        """
        Validate Oman VAT number format
        """
        if not vat_number:
            return False

        # Oman VAT format: OM followed by 15 digits
        return bool(re.match(r"^OM\d{15}$", vat_number))

    def validate_e_invoice_compliance(self, invoice_doc, vat_calculation):
        """
        Validate invoice against Oman e-invoice requirements
        """
        errors = []

        # Check required company VAT number
        if not getattr(invoice_doc, "company_tax_id", ""):
            errors.append(_("Company VAT registration number is required"))

        # Check customer VAT number for high-value invoices
        if vat_calculation["grand_total"] > 1000:
            customer_vat = getattr(invoice_doc, "customer_tax_id", "") or getattr(
                invoice_doc, "tax_id", ""
            )
            if not customer_vat:
                errors.append(_("Customer VAT number is required for invoices above OMR 1,000"))

        # Check tax invoice number format
        if hasattr(invoice_doc, "tax_invoice_number"):
            if not re.match(r"^TI-\d{4}-\d{6}$", invoice_doc.tax_invoice_number or ""):
                errors.append(_("Invalid tax invoice number format. Should be TI-YYYY-NNNNNN"))

        # Check e-invoice UUID
        if not getattr(invoice_doc, "e_invoice_uuid", ""):
            errors.append(_("E-invoice UUID is required for compliance"))

        # Validate VAT calculation totals
        if (
            abs(
                vat_calculation["total_vat"]
                - (vat_calculation["net_total"] * self.vat_rate_standard / 100)
            )
            > 0.01
        ):
            # Allow for rounding differences but flag significant discrepancies
            total_standard_vat = sum(
                [
                    item["vat_amount"]
                    for item in vat_calculation["vat_breakdown"]
                    if item["vat_category"] == "standard"
                ]
            )
            if abs(total_standard_vat - vat_calculation["total_vat"]) > 0.01:
                errors.append(_("VAT calculation discrepancy detected"))

        return {"status": "valid" if len(errors) == 0 else "invalid", "errors": errors}


# Utility functions for ERPNext integration


@frappe.whitelist()
def calculate_sales_invoice_vat(sales_invoice_name):
    """
    API method to calculate VAT for a Sales Invoice
    """
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
        vat_engine = OmanVATCalculationEngine(invoice_doc.company)

        result = vat_engine.calculate_invoice_vat(invoice_doc)

        return result

    except Exception as e:
        frappe.log_error(f"Error calculating invoice VAT: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def validate_invoice_e_compliance(sales_invoice_name):
    """
    API method to validate e-invoice compliance
    """
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
        vat_engine = OmanVATCalculationEngine(invoice_doc.company)

        # Get VAT calculation first
        vat_calculation = vat_engine.calculate_invoice_vat(invoice_doc)

        if "error" in vat_calculation:
            return vat_calculation

        compliance_result = vat_engine.validate_e_invoice_compliance(invoice_doc, vat_calculation)

        return {
            "is_compliant": compliance_result["status"] == "valid",
            "compliance_status": compliance_result["status"],
            "errors": compliance_result.get("errors", []),
            "vat_summary": {
                "net_total": vat_calculation["net_total"],
                "vat_total": vat_calculation["total_vat"],
                "grand_total": vat_calculation["grand_total"],
            },
        }

    except Exception as e:
        frappe.log_error(f"Error validating e-invoice compliance: {str(e)}")
        return {"error": str(e), "is_compliant": False}


@frappe.whitelist()
def apply_automatic_vat_to_invoice(sales_invoice_name):
    """
    Automatically apply VAT calculation to a Sales Invoice
    """
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
        vat_engine = OmanVATCalculationEngine(invoice_doc.company)

        vat_result = vat_engine.calculate_invoice_vat(invoice_doc)

        if "error" in vat_result:
            return {"success": False, "message": vat_result["error"]}

        # Apply calculated VAT to invoice
        invoice_doc.total = vat_result["net_total"]
        invoice_doc.total_taxes_and_charges = vat_result["total_vat"]
        invoice_doc.grand_total = vat_result["grand_total"]

        # Clear existing taxes and add calculated VAT
        invoice_doc.taxes = []

        if vat_result["total_vat"] > 0:
            vat_row = invoice_doc.append("taxes", {})
            vat_row.charge_type = "On Net Total"
            vat_row.account_head = get_vat_account_for_company(invoice_doc.company)
            vat_row.description = f"VAT @ {vat_engine.vat_rate_standard}%"
            vat_row.rate = vat_engine.vat_rate_standard
            vat_row.tax_amount = vat_result["total_vat"]
            vat_row.total = vat_result["grand_total"]

        # Save the invoice
        invoice_doc.save()

        return {
            "success": True,
            "message": _("VAT calculation applied successfully"),
            "vat_details": vat_result,
        }

    except Exception as e:
        frappe.log_error(f"Error applying automatic VAT: {str(e)}")
        return {"success": False, "message": str(e)}


def get_vat_account_for_company(company):
    """
    Get the Output VAT account for a company
    """
    try:
        vat_account = frappe.db.get_value(
            "Account",
            {"company": company, "account_name": "Output VAT 5%", "account_type": "Tax"},
            "name",
        )

        if vat_account:
            return vat_account

        # Fallback: look for any VAT account
        vat_account = frappe.db.sql(
            """
            SELECT name FROM `tabAccount`
            WHERE company = %s 
            AND (account_name LIKE '%VAT%' OR account_name LIKE '%Tax%')
            AND account_type = 'Tax'
            LIMIT 1
        """,
            [company],
        )

        if vat_account:
            return vat_account[0][0]

        return None

    except Exception as e:
        frappe.log_error(f"Error getting VAT account: {str(e)}")
        return None


# Validation hook for Sales Invoice
def validate_sales_invoice_vat(doc, method):
    """
    Validate VAT calculation when Sales Invoice is saved
    Called via hooks
    """
    if doc.doctype != "Sales Invoice":
        return

    try:
        vat_engine = OmanVATCalculationEngine(doc.company)
        vat_calculation = vat_engine.calculate_invoice_vat(doc)

        if "error" in vat_calculation:
            frappe.throw(_("VAT calculation error: {0}").format(vat_calculation["error"]))

        # Check compliance
        if vat_calculation["compliance_status"] != "valid":
            error_msg = "\n".join(vat_calculation.get("compliance_errors", []))
            frappe.throw(_("E-invoice compliance errors:\n{0}").format(error_msg))

        # Auto-generate required fields if missing
        if not doc.tax_invoice_number:
            from universal_workshop.billing_management.utils import generate_tax_invoice_number

            doc.tax_invoice_number = generate_tax_invoice_number(doc.company, doc.posting_date)

        if not doc.e_invoice_uuid:
            from universal_workshop.billing_management.utils import generate_e_invoice_uuid

            doc.e_invoice_uuid = generate_e_invoice_uuid()

    except Exception as e:
        frappe.log_error(f"Sales Invoice VAT validation error: {str(e)}")
        frappe.throw(_("VAT validation failed: {0}").format(str(e)))
