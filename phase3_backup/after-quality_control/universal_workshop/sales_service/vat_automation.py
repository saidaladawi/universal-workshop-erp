# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
"""
Automated VAT Calculation System for Universal Workshop ERP (Oman)
Complies with Oman Tax Authority (OTA) requirements and ERPNext v15 standards
"""

import frappe
from frappe import _
from frappe.utils import flt, cstr
from frappe.model.document import Document
import json
from datetime import datetime


class OmanVATController:
    """
    Main controller for automated VAT calculation in Universal Workshop ERP
    Handles Oman-specific VAT requirements (5% standard rate)
    """

    def __init__(self):
        self.standard_vat_rate = 5.0  # Oman standard VAT rate
        self.exempted_items = []
        self.zero_rated_items = []

    def setup_vat_configuration(self):
        """Initialize VAT configuration for Oman compliance"""
        self.create_vat_settings()
        self.create_tax_templates()
        self.setup_item_tax_categories()
        self.configure_customer_vat_types()

    def create_vat_settings(self):
        """Create Oman VAT settings document"""
        try:
            # Check if Oman VAT Settings already exists
            if frappe.db.exists("Oman VAT Settings", "Oman VAT Settings"):
                settings = frappe.get_doc("Oman VAT Settings", "Oman VAT Settings")
            else:
                settings = frappe.new_doc("Oman VAT Settings")
                settings.name = "Oman VAT Settings"

            # Configure Oman-specific VAT settings
            settings.company = frappe.defaults.get_user_default("Company")
            settings.vat_rate = self.standard_vat_rate
            settings.currency = "OMR"
            settings.fiscal_year_start = "01-01"
            settings.fiscal_year_end = "12-31"
            settings.vat_registration_threshold = 38500.000  # OMR 38,500
            settings.voluntary_threshold = 19250.000  # OMR 19,250
            settings.quarterly_filing = 1
            settings.e_invoicing_mandatory = 0  # Will be 1 from 2026

            settings.save()
            frappe.db.commit()

            return {"success": True, "message": _("Oman VAT settings configured successfully")}

        except Exception as e:
            frappe.log_error(f"VAT Settings Error: {str(e)}")
            return {"success": False, "message": str(e)}

    def create_tax_templates(self):
        """Create VAT tax templates for different scenarios"""
        templates = [
            {
                "title": "Oman VAT 5% (Standard)",
                "title_ar": "ضريبة القيمة المضافة عمان ٥٪ (عادي)",
                "company": frappe.defaults.get_user_default("Company"),
                "taxes": [
                    {
                        "charge_type": "On Net Total",
                        "account_head": self.get_or_create_vat_account("Output VAT 5%"),
                        "description": "VAT @ 5%",
                        "description_ar": "ضريبة القيمة المضافة ٥٪",
                        "rate": 5.0,
                    }
                ],
            },
            {
                "title": "Oman VAT 0% (Zero Rated)",
                "title_ar": "ضريبة القيمة المضافة عمان ٠٪ (معدل صفر)",
                "company": frappe.defaults.get_user_default("Company"),
                "taxes": [
                    {
                        "charge_type": "On Net Total",
                        "account_head": self.get_or_create_vat_account("Output VAT 0%"),
                        "description": "VAT @ 0%",
                        "description_ar": "ضريبة القيمة المضافة ٠٪",
                        "rate": 0.0,
                    }
                ],
            },
            {
                "title": "Oman VAT Exempt",
                "title_ar": "ضريبة القيمة المضافة عمان معفاة",
                "company": frappe.defaults.get_user_default("Company"),
                "taxes": [],  # No VAT for exempt items
            },
        ]

        for template_data in templates:
            try:
                if not frappe.db.exists("Sales Taxes and Charges Template", template_data["title"]):
                    template = frappe.new_doc("Sales Taxes and Charges Template")
                    template.title = template_data["title"]
                    template.company = template_data["company"]

                    # Add custom field for Arabic title
                    if hasattr(template, "title_ar"):
                        template.title_ar = template_data["title_ar"]

                    # Add tax charges
                    for tax in template_data["taxes"]:
                        template.append("taxes", tax)

                    template.insert()
                    frappe.db.commit()

            except Exception as e:
                frappe.log_error(f"Tax Template Error: {str(e)}")

    def get_or_create_vat_account(self, account_name):
        """Get or create VAT account heads"""
        company = frappe.defaults.get_user_default("Company")
        account_name_full = (
            f"{account_name} - {frappe.get_cached_value('Company', company, 'abbr')}"
        )

        if not frappe.db.exists("Account", account_name_full):
            try:
                account = frappe.new_doc("Account")
                account.account_name = account_name
                account.company = company
                account.account_type = "Tax"
                account.account_currency = "OMR"
                account.is_group = 0

                # Find parent account
                parent_account = frappe.db.get_value(
                    "Account", {"company": company, "account_name": "Duties and Taxes"}, "name"
                )
                if not parent_account:
                    parent_account = frappe.db.get_value(
                        "Account",
                        {"company": company, "is_group": 1, "account_type": "Tax"},
                        "name",
                    )

                account.parent_account = parent_account
                account.insert()
                frappe.db.commit()

                return account.name
            except Exception as e:
                frappe.log_error(f"VAT Account Creation Error: {str(e)}")
                return None

        return account_name_full

    def setup_item_tax_categories(self):
        """Setup item tax categories for different VAT treatments"""
        categories = [
            {
                "name": "Standard VAT",
                "name_ar": "ضريبة قيمة مضافة عادية",
                "vat_rate": 5.0,
                "description": "Items subject to 5% VAT",
            },
            {
                "name": "Zero Rated VAT",
                "name_ar": "ضريبة قيمة مضافة معدل صفر",
                "vat_rate": 0.0,
                "description": "Items with 0% VAT (exported goods, etc.)",
            },
            {
                "name": "VAT Exempt",
                "name_ar": "معفاة من ضريبة القيمة المضافة",
                "vat_rate": 0.0,
                "description": "Items exempt from VAT (education, healthcare, etc.)",
            },
        ]

        for category in categories:
            try:
                if not frappe.db.exists("Item Tax Template", category["name"]):
                    template = frappe.new_doc("Item Tax Template")
                    template.title = category["name"]
                    template.company = frappe.defaults.get_user_default("Company")

                    # Add VAT account and rate
                    if category["vat_rate"] > 0:
                        account_head = self.get_or_create_vat_account("Output VAT 5%")
                        template.append(
                            "taxes", {"tax_type": account_head, "tax_rate": category["vat_rate"]}
                        )

                    template.insert()
                    frappe.db.commit()

            except Exception as e:
                frappe.log_error(f"Item Tax Category Error: {str(e)}")

    def configure_customer_vat_types(self):
        """Configure customer VAT types and TRN validation"""
        # Add custom fields to Customer DocType if not exists
        custom_fields = [
            {
                "dt": "Customer",
                "fieldname": "oman_trn",
                "label": "Oman Tax Registration Number",
                "fieldtype": "Data",
                "insert_after": "tax_id",
                "description": "15-digit TRN for VAT registered customers",
            },
            {
                "dt": "Customer",
                "fieldname": "oman_trn_ar",
                "label": "رقم التسجيل الضريبي العماني",
                "fieldtype": "Data",
                "insert_after": "oman_trn",
            },
            {
                "dt": "Customer",
                "fieldname": "vat_type",
                "label": "VAT Type",
                "fieldtype": "Select",
                "options": "Registered\nNon-Registered\nExempt\nZero-Rated",
                "default": "Non-Registered",
                "insert_after": "oman_trn_ar",
            },
        ]

        for field in custom_fields:
            try:
                if not frappe.db.exists(
                    "Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}
                ):
                    custom_field = frappe.new_doc("Custom Field")
                    custom_field.update(field)
                    custom_field.insert()
                    frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Custom Field Error: {str(e)}")

    @frappe.whitelist()
    def calculate_vat_for_transaction(self, doc_dict):
        """
        Calculate VAT for any transaction (Service Estimate, Sales Order, Sales Invoice)

        Args:
            doc_dict: Dictionary containing transaction data

        Returns:
            dict: Updated transaction with VAT calculations
        """
        try:
            if isinstance(doc_dict, str):
                doc_dict = json.loads(doc_dict)

            # Get customer VAT information
            customer_vat_info = self.get_customer_vat_info(doc_dict.get("customer"))

            # Calculate VAT for each item
            total_vat_amount = 0
            net_total = 0

            for item in doc_dict.get("items", []):
                item_vat = self.calculate_item_vat(item, customer_vat_info)
                item.update(item_vat)

                net_total += flt(item.get("amount", 0))
                total_vat_amount += flt(item.get("vat_amount", 0))

            # Update totals
            doc_dict["net_total"] = flt(net_total, 3)
            doc_dict["total_taxes_and_charges"] = flt(total_vat_amount, 3)
            doc_dict["grand_total"] = flt(net_total + total_vat_amount, 3)

            # Add VAT breakdown
            doc_dict["vat_breakdown"] = self.generate_vat_breakdown(doc_dict["items"])

            return {"success": True, "data": doc_dict, "message": _("VAT calculated successfully")}

        except Exception as e:
            frappe.log_error(f"VAT Calculation Error: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_customer_vat_info(self, customer_id):
        """Get customer VAT registration information"""
        if not customer_id:
            return {"vat_type": "Non-Registered", "trn": None}

        try:
            customer = frappe.get_doc("Customer", customer_id)
            return {
                "vat_type": getattr(customer, "vat_type", "Non-Registered"),
                "trn": getattr(customer, "oman_trn", None),
                "trn_ar": getattr(customer, "oman_trn_ar", None),
            }
        except:
            return {"vat_type": "Non-Registered", "trn": None}

    def calculate_item_vat(self, item, customer_vat_info):
        """Calculate VAT for individual item based on item type and customer VAT status"""
        try:
            item_code = item.get("item_code")
            amount = flt(item.get("amount", 0))

            # Get item VAT category
            item_vat_category = self.get_item_vat_category(item_code)

            # Determine VAT rate based on item and customer
            vat_rate = self.determine_vat_rate(item_vat_category, customer_vat_info)

            # Calculate VAT amount
            vat_amount = (amount * vat_rate) / 100

            return {
                "vat_rate": vat_rate,
                "vat_amount": flt(vat_amount, 3),
                "amount_with_vat": flt(amount + vat_amount, 3),
                "vat_category": item_vat_category,
            }

        except Exception as e:
            frappe.log_error(f"Item VAT Calculation Error: {str(e)}")
            return {
                "vat_rate": 0,
                "vat_amount": 0,
                "amount_with_vat": flt(item.get("amount", 0)),
                "vat_category": "Error",
            }

    def get_item_vat_category(self, item_code):
        """Get VAT category for specific item"""
        if not item_code:
            return "Standard VAT"

        try:
            # Check if item has specific VAT template
            item_tax_template = frappe.db.get_value("Item", item_code, "item_tax_template")
            if item_tax_template:
                return item_tax_template

            # Check item group VAT settings
            item_group = frappe.db.get_value("Item", item_code, "item_group")
            if item_group:
                # Define VAT categories for different item groups
                vat_categories = {
                    "Services": "Standard VAT",
                    "Automotive Parts": "Standard VAT",
                    "Labor": "Standard VAT",
                    "Lubricants": "Standard VAT",
                    "Tires": "Standard VAT",
                    "Batteries": "Standard VAT",
                    "Educational Services": "VAT Exempt",
                    "Healthcare Services": "VAT Exempt",
                }
                return vat_categories.get(item_group, "Standard VAT")

            return "Standard VAT"

        except:
            return "Standard VAT"

    def determine_vat_rate(self, vat_category, customer_vat_info):
        """Determine final VAT rate based on item category and customer status"""
        # VAT exempt items
        if "Exempt" in vat_category:
            return 0

        # Zero-rated items
        if "Zero" in vat_category:
            return 0

        # Standard VAT items
        if customer_vat_info.get("vat_type") == "Exempt":
            return 0

        return self.standard_vat_rate

    def generate_vat_breakdown(self, items):
        """Generate detailed VAT breakdown for reporting"""
        breakdown = {
            "standard_vat": {"net_amount": 0, "vat_amount": 0, "rate": 5.0},
            "zero_rated": {"net_amount": 0, "vat_amount": 0, "rate": 0.0},
            "exempt": {"net_amount": 0, "vat_amount": 0, "rate": 0.0},
        }

        for item in items:
            vat_rate = flt(item.get("vat_rate", 0))
            amount = flt(item.get("amount", 0))
            vat_amount = flt(item.get("vat_amount", 0))

            if vat_rate == 5.0:
                breakdown["standard_vat"]["net_amount"] += amount
                breakdown["standard_vat"]["vat_amount"] += vat_amount
            elif vat_rate == 0 and "Zero" in item.get("vat_category", ""):
                breakdown["zero_rated"]["net_amount"] += amount
                breakdown["zero_rated"]["vat_amount"] += vat_amount
            else:
                breakdown["exempt"]["net_amount"] += amount
                breakdown["exempt"]["vat_amount"] += vat_amount

        # Round all amounts to 3 decimal places (OMR standard)
        for category in breakdown.values():
            category["net_amount"] = flt(category["net_amount"], 3)
            category["vat_amount"] = flt(category["vat_amount"], 3)

        return breakdown

    @frappe.whitelist()
    def validate_oman_trn(self, trn):
        """Validate Oman Tax Registration Number format"""
        if not trn:
            return {"valid": True, "message": ""}

        # Oman TRN format: 15 digits
        if not trn.isdigit() or len(trn) != 15:
            return {"valid": False, "message": _("Oman TRN must be exactly 15 digits")}

        return {"valid": True, "message": _("Valid TRN format")}

    @frappe.whitelist()
    def get_quarterly_vat_report(self, from_date, to_date):
        """Generate quarterly VAT report for OTA filing"""
        try:
            # Get all sales transactions in period
            sales_data = frappe.db.sql(
                """
                SELECT 
                    si.name, si.posting_date, si.customer, si.net_total,
                    si.total_taxes_and_charges, si.grand_total,
                    c.oman_trn, c.vat_type
                FROM `tabSales Invoice` si
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                WHERE si.posting_date BETWEEN %s AND %s
                AND si.docstatus = 1
                ORDER BY si.posting_date
            """,
                [from_date, to_date],
                as_dict=True,
            )

            # Calculate VAT totals
            total_output_vat = sum(flt(row.total_taxes_and_charges) for row in sales_data)
            total_net_sales = sum(flt(row.net_total) for row in sales_data)

            # Get purchase VAT (input VAT)
            purchase_data = frappe.db.sql(
                """
                SELECT SUM(total_taxes_and_charges) as input_vat
                FROM `tabPurchase Invoice`
                WHERE posting_date BETWEEN %s AND %s
                AND docstatus = 1
            """,
                [from_date, to_date],
                as_dict=True,
            )

            total_input_vat = flt(purchase_data[0].input_vat if purchase_data else 0)

            # Net VAT payable
            net_vat_payable = total_output_vat - total_input_vat

            return {
                "success": True,
                "data": {
                    "period": {"from": from_date, "to": to_date},
                    "sales_summary": {
                        "total_sales": flt(total_net_sales, 3),
                        "output_vat": flt(total_output_vat, 3),
                        "total_with_vat": flt(total_net_sales + total_output_vat, 3),
                    },
                    "purchase_summary": {"input_vat": flt(total_input_vat, 3)},
                    "vat_liability": {
                        "output_vat": flt(total_output_vat, 3),
                        "input_vat": flt(total_input_vat, 3),
                        "net_payable": flt(net_vat_payable, 3),
                    },
                    "transactions": sales_data,
                },
            }

        except Exception as e:
            frappe.log_error(f"VAT Report Error: {str(e)}")
            return {"success": False, "message": str(e)}

    def calculate_vat(self, amount):
        vat_amount = (amount * self.standard_vat_rate) / 100
        return flt(vat_amount, 3)


# Utility functions for VAT automation


@frappe.whitelist()
def setup_oman_vat():
    """Initialize Oman VAT configuration"""
    controller = OmanVATController()
    return controller.setup_vat_configuration()


@frappe.whitelist()
def calculate_transaction_vat(doc_json):
    """Calculate VAT for any transaction document"""
    controller = OmanVATController()
    return controller.calculate_vat_for_transaction(doc_json)


@frappe.whitelist()
def validate_trn(trn):
    """Validate Oman TRN number"""
    controller = OmanVATController()
    return controller.validate_oman_trn(trn)


@frappe.whitelist()
def get_vat_report(from_date, to_date):
    """Get quarterly VAT report"""
    controller = OmanVATController()
    return controller.get_quarterly_vat_report(from_date, to_date)


@frappe.whitelist()
def auto_apply_vat_to_service_estimate(service_estimate_id):
    """Automatically apply VAT to Service Estimate"""
    try:
        estimate = frappe.get_doc("Service Estimate", service_estimate_id)
        
        # Calculate VAT for the estimate
        estimate_dict = estimate.as_dict()
        controller = OmanVATController()
        result = controller.calculate_vat_for_transaction(estimate_dict)
        
        if result["success"]:
            updated_data = result["data"]
            
            # Update estimate with VAT calculations
            estimate.net_total = updated_data['net_total']
            estimate.total_taxes_and_charges = updated_data['total_taxes_and_charges']
            estimate.grand_total = updated_data['grand_total']
            
            # Update items with VAT details
            for idx, item_data in enumerate(updated_data['items']):
                if idx < len(estimate.items):
                    estimate.items[idx].vat_rate = item_data.get('vat_rate', 0)
                    estimate.items[idx].vat_amount = item_data.get('vat_amount', 0)
            
            estimate.save()
            
            return {
                "success": True,
                "message": _("VAT applied successfully to Service Estimate"),
                "vat_amount": updated_data['total_taxes_and_charges'],
                "grand_total": updated_data['grand_total']
            }
        else:
            return result
            
    except Exception as e:
        frappe.log_error(f"Service Estimate VAT Error: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_vat_summary_for_period(from_date, to_date):
    """Get VAT summary for reporting period"""
    try:
        # Get all sales transactions in period
        sales_data = frappe.db.sql("""
            SELECT 
                COUNT(*) as transaction_count,
                SUM(net_total) as total_net_sales,
                SUM(total_taxes_and_charges) as total_output_vat,
                SUM(grand_total) as total_with_vat
            FROM `tabSales Invoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """, [from_date, to_date], as_dict=True)
        
        summary = sales_data[0] if sales_data else {}
        
        return {
            "success": True,
            "data": {
                "period": {"from": from_date, "to": to_date},
                "transaction_count": summary.get("transaction_count", 0),
                "net_sales": flt(summary.get("total_net_sales", 0), 3),
                "vat_collected": flt(summary.get("total_output_vat", 0), 3),
                "total_with_vat": flt(summary.get("total_with_vat", 0), 3)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"VAT Summary Error: {str(e)}")
        return {"success": False, "message": str(e)}
