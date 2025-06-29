# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months, today, get_first_day, get_last_day
from datetime import datetime, timedelta
import json
from collections import defaultdict
from .oman_vat_config import OmanVATConfig


class VATComplianceReportingManager:
    """
    Comprehensive VAT Compliance and Reporting Manager for Universal Workshop ERP
    Extends OmanVATConfig with advanced reporting and compliance features
    """

    def __init__(self):
        self.vat_config = OmanVATConfig()
        self.vat_rate = 5.0  # Oman VAT rate
        self.currency = "OMR"
        self.company = self.vat_config.company or self._get_default_company()

    def _get_default_company(self):
        """Get default company for VAT operations"""
        company = frappe.defaults.get_user_default("Company")
        if not company:
            companies = frappe.get_list("Company", limit=1)
            if companies:
                return companies[0].name
        return company

    def generate_vat_return_report(self, from_date, to_date, language="en"):
        """
        Generate comprehensive VAT return report for Oman Tax Authority

        Args:
            from_date (str): Start date for the reporting period
            to_date (str): End date for the reporting period
            language (str): Report language ('en' or 'ar')

        Returns:
            dict: Comprehensive VAT return data
        """
        try:
            # Convert dates to proper format
            from_date = getdate(from_date)
            to_date = getdate(to_date)

            # Get sales data (Output VAT)
            sales_data = self._get_sales_vat_data(from_date, to_date)

            # Get purchase data (Input VAT)
            purchase_data = self._get_purchase_vat_data(from_date, to_date)

            # Calculate VAT summary
            vat_summary = self._calculate_vat_summary(sales_data, purchase_data)

            # Prepare report structure
            report_data = {
                "company": self.company,
                "period": {
                    "from_date": from_date.strftime("%Y-%m-%d"),
                    "to_date": to_date.strftime("%Y-%m-%d"),
                    "quarter": self._get_quarter(from_date),
                    "year": from_date.year,
                },
                "sales_summary": sales_data,
                "purchase_summary": purchase_data,
                "vat_summary": vat_summary,
                "compliance_checks": self._run_compliance_checks(from_date, to_date),
                "generated_at": datetime.now().isoformat(),
                "language": language,
            }

            # Add Arabic translations if needed
            if language == "ar":
                report_data = self._add_arabic_translations(report_data)

            # Store report for audit trail
            self._store_vat_report(report_data)

            return report_data

        except Exception as e:
            frappe.log_error(f"VAT Return Report Error: {str(e)}")
            frappe.throw(_("Error generating VAT return report: {0}").format(str(e)))

    def _get_sales_vat_data(self, from_date, to_date):
        """Get detailed sales VAT data for the period"""
        sales_invoices = frappe.db.sql(
            """
            SELECT 
                si.name as invoice_no,
                si.customer,
                si.posting_date,
                si.net_total,
                si.total_taxes_and_charges as vat_amount,
                si.grand_total,
                si.tax_id as customer_vat_no,
                stc.rate as vat_rate,
                stc.tax_amount,
                si.currency
            FROM `tabSales Invoice` si
            LEFT JOIN `tabSales Taxes and Charges` stc ON stc.parent = si.name 
                AND stc.account_head LIKE '%Output VAT%'
            WHERE si.docstatus = 1 
                AND si.posting_date BETWEEN %s AND %s
                AND si.company = %s
            ORDER BY si.posting_date
        """,
            [from_date, to_date, self.company],
            as_dict=True,
        )

        # Categorize sales by VAT rate
        categorized_sales = {
            "standard_rate": [],  # 5% VAT
            "zero_rate": [],  # 0% VAT (exports)
            "exempt": [],  # Exempt supplies
            "out_of_scope": [],  # Out of scope
        }

        total_sales = {
            "standard_rate": {"net": 0, "vat": 0, "gross": 0},
            "zero_rate": {"net": 0, "vat": 0, "gross": 0},
            "exempt": {"net": 0, "vat": 0, "gross": 0},
            "out_of_scope": {"net": 0, "vat": 0, "gross": 0},
        }

        for invoice in sales_invoices:
            vat_rate = flt(invoice.vat_rate, 2)

            if vat_rate == 5.0:
                category = "standard_rate"
            elif vat_rate == 0.0:
                category = "zero_rate"
            else:
                category = "exempt"

            categorized_sales[category].append(invoice)
            total_sales[category]["net"] += flt(invoice.net_total, 3)
            total_sales[category]["vat"] += flt(invoice.vat_amount, 3)
            total_sales[category]["gross"] += flt(invoice.grand_total, 3)

        return {
            "details": categorized_sales,
            "totals": total_sales,
            "invoice_count": len(sales_invoices),
            "period_total_output_vat": sum([total_sales[cat]["vat"] for cat in total_sales]),
        }

    def _get_purchase_vat_data(self, from_date, to_date):
        """Get detailed purchase VAT data for the period"""
        purchase_invoices = frappe.db.sql(
            """
            SELECT 
                pi.name as invoice_no,
                pi.supplier,
                pi.posting_date,
                pi.net_total,
                pi.total_taxes_and_charges as vat_amount,
                pi.grand_total,
                pi.tax_id as supplier_vat_no,
                ptc.rate as vat_rate,
                ptc.tax_amount,
                pi.currency
            FROM `tabPurchase Invoice` pi
            LEFT JOIN `tabPurchase Taxes and Charges` ptc ON ptc.parent = pi.name 
                AND ptc.account_head LIKE '%Input VAT%'
            WHERE pi.docstatus = 1 
                AND pi.posting_date BETWEEN %s AND %s
                AND pi.company = %s
            ORDER BY pi.posting_date
        """,
            [from_date, to_date, self.company],
            as_dict=True,
        )

        # Categorize purchases
        categorized_purchases = {
            "recoverable": [],  # Recoverable input VAT
            "non_recoverable": [],  # Non-recoverable input VAT
        }

        total_purchases = {
            "recoverable": {"net": 0, "vat": 0, "gross": 0},
            "non_recoverable": {"net": 0, "vat": 0, "gross": 0},
        }

        for invoice in purchase_invoices:
            # Determine if VAT is recoverable
            is_recoverable = self._is_vat_recoverable(invoice)
            category = "recoverable" if is_recoverable else "non_recoverable"

            categorized_purchases[category].append(invoice)
            total_purchases[category]["net"] += flt(invoice.net_total, 3)
            total_purchases[category]["vat"] += flt(invoice.vat_amount, 3)
            total_purchases[category]["gross"] += flt(invoice.grand_total, 3)

        return {
            "details": categorized_purchases,
            "totals": total_purchases,
            "invoice_count": len(purchase_invoices),
            "period_total_input_vat": total_purchases["recoverable"]["vat"],
        }

    def _is_vat_recoverable(self, purchase_invoice):
        """
        Determine if purchase VAT is recoverable based on business rules

        Args:
            purchase_invoice (dict): Purchase invoice data

        Returns:
            bool: True if VAT is recoverable
        """
        # Business logic for VAT recoverability
        # In Oman, generally all business purchases are recoverable
        # unless specifically for exempt activities

        # Check if purchase is for business use
        # This could be enhanced with item-level categorization
        return True  # Default to recoverable for workshop operations

    def _calculate_vat_summary(self, sales_data, purchase_data):
        """Calculate VAT summary for the period"""
        output_vat = sales_data["period_total_output_vat"]
        input_vat = purchase_data["period_total_input_vat"]

        net_vat = output_vat - input_vat

        return {
            "total_output_vat": flt(output_vat, 3),
            "total_input_vat": flt(input_vat, 3),
            "net_vat_payable": flt(max(net_vat, 0), 3),
            "net_vat_refundable": flt(abs(min(net_vat, 0)), 3),
            "vat_rate_applied": self.vat_rate,
            "calculation_basis": "Invoice Method",
        }

    def _get_quarter(self, date):
        """Get quarter number for a given date"""
        month = date.month
        if month <= 3:
            return 1
        elif month <= 6:
            return 2
        elif month <= 9:
            return 3
        else:
            return 4

    def _run_compliance_checks(self, from_date, to_date):
        """Run comprehensive compliance checks"""
        checks = []

        # Check 1: VAT number validation
        invalid_vat_customers = self._check_customer_vat_numbers()
        if invalid_vat_customers:
            checks.append(
                {
                    "check": "customer_vat_validation",
                    "status": "warning",
                    "message": f"Found {len(invalid_vat_customers)} customers with invalid VAT numbers",
                    "details": invalid_vat_customers,
                }
            )
        else:
            checks.append(
                {
                    "check": "customer_vat_validation",
                    "status": "pass",
                    "message": "All customer VAT numbers are valid",
                }
            )

        # Check 2: Missing VAT on invoices
        missing_vat_invoices = self._check_missing_vat_invoices(from_date, to_date)
        if missing_vat_invoices:
            checks.append(
                {
                    "check": "vat_application",
                    "status": "error",
                    "message": f"Found {len(missing_vat_invoices)} invoices without VAT applied",
                    "details": missing_vat_invoices,
                }
            )
        else:
            checks.append(
                {
                    "check": "vat_application",
                    "status": "pass",
                    "message": "VAT properly applied on all invoices",
                }
            )

        # Check 3: Zero-rated sales documentation
        zero_rated_check = self._check_zero_rated_documentation(from_date, to_date)
        checks.append(zero_rated_check)

        # Check 4: Threshold monitoring
        threshold_check = self._check_vat_registration_threshold()
        checks.append(threshold_check)

        return checks

    def _check_customer_vat_numbers(self):
        """Check for invalid customer VAT numbers"""
        customers_with_vat = frappe.db.sql(
            """
            SELECT name, customer_name, tax_id
            FROM `tabCustomer`
            WHERE tax_id IS NOT NULL 
                AND tax_id != ''
                AND disabled = 0
        """,
            as_dict=True,
        )

        invalid_customers = []
        for customer in customers_with_vat:
            try:
                self.vat_config.validate_vat_number(customer.tax_id)
            except:
                invalid_customers.append(
                    {
                        "customer": customer.name,
                        "customer_name": customer.customer_name,
                        "invalid_vat_number": customer.tax_id,
                    }
                )

        return invalid_customers

    def _check_missing_vat_invoices(self, from_date, to_date):
        """Check for invoices missing VAT application"""
        invoices_without_vat = frappe.db.sql(
            """
            SELECT si.name, si.customer, si.posting_date, si.grand_total
            FROM `tabSales Invoice` si
            LEFT JOIN `tabSales Taxes and Charges` stc ON stc.parent = si.name 
                AND stc.account_head LIKE '%Output VAT%'
            WHERE si.docstatus = 1 
                AND si.posting_date BETWEEN %s AND %s
                AND si.company = %s
                AND stc.name IS NULL
                AND si.grand_total > 0
        """,
            [from_date, to_date, self.company],
            as_dict=True,
        )

        return invoices_without_vat

    def _check_zero_rated_documentation(self, from_date, to_date):
        """Check zero-rated sales have proper documentation"""
        zero_rated_sales = frappe.db.sql(
            """
            SELECT si.name, si.customer, si.posting_date, si.grand_total
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Taxes and Charges` stc ON stc.parent = si.name 
                AND stc.account_head LIKE '%Output VAT%'
                AND stc.rate = 0
            WHERE si.docstatus = 1 
                AND si.posting_date BETWEEN %s AND %s
                AND si.company = %s
        """,
            [from_date, to_date, self.company],
            as_dict=True,
        )

        if zero_rated_sales:
            return {
                "check": "zero_rated_documentation",
                "status": "warning",
                "message": f"Found {len(zero_rated_sales)} zero-rated sales transactions",
                "details": zero_rated_sales,
                "recommendation": "Ensure proper documentation for zero-rated sales (export certificates, etc.)",
            }
        else:
            return {
                "check": "zero_rated_documentation",
                "status": "pass",
                "message": "No zero-rated sales found",
            }

    def _check_vat_registration_threshold(self):
        """Check if business is approaching VAT registration threshold"""
        # Oman VAT registration threshold is OMR 38,500 annually
        threshold = 38500.0

        # Calculate revenue for last 12 months
        twelve_months_ago = add_months(today(), -12)
        annual_revenue = (
            frappe.db.sql(
                """
            SELECT SUM(net_total) as total_revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
                AND posting_date >= %s
                AND company = %s
        """,
                [twelve_months_ago, self.company],
            )[0][0]
            or 0
        )

        percentage_of_threshold = (annual_revenue / threshold) * 100

        if annual_revenue >= threshold:
            return {
                "check": "vat_threshold",
                "status": "info",
                "message": f"Annual revenue OMR {annual_revenue:,.3f} exceeds threshold",
                "details": {
                    "revenue": annual_revenue,
                    "threshold": threshold,
                    "percentage": percentage_of_threshold,
                },
            }
        elif percentage_of_threshold > 80:
            return {
                "check": "vat_threshold",
                "status": "warning",
                "message": f"Approaching VAT threshold: {percentage_of_threshold:.1f}% of limit",
                "details": {
                    "revenue": annual_revenue,
                    "threshold": threshold,
                    "percentage": percentage_of_threshold,
                },
            }
        else:
            return {
                "check": "vat_threshold",
                "status": "pass",
                "message": f"Revenue {percentage_of_threshold:.1f}% of VAT threshold",
                "details": {
                    "revenue": annual_revenue,
                    "threshold": threshold,
                    "percentage": percentage_of_threshold,
                },
            }

    def _add_arabic_translations(self, report_data):
        """Add Arabic translations to report data"""
        arabic_translations = {
            "company": "الشركة",
            "period": "فترة التقرير",
            "sales_summary": "ملخص المبيعات",
            "purchase_summary": "ملخص المشتريات",
            "vat_summary": "ملخص ضريبة القيمة المضافة",
            "total_output_vat": "إجمالي ضريبة المخرجات",
            "total_input_vat": "إجمالي ضريبة المدخلات",
            "net_vat_payable": "صافي الضريبة المستحقة",
            "net_vat_refundable": "صافي الضريبة القابلة للاسترداد",
        }

        report_data["arabic_labels"] = arabic_translations
        return report_data

    def _store_vat_report(self, report_data):
        """Store VAT report for audit trail"""
        try:
            # Create a log entry for the VAT report
            frappe.get_doc(
                {
                    "doctype": "Error Log",
                    "method": "VAT Compliance Report",
                    "error": json.dumps(report_data, indent=2, default=str),
                    "creation": datetime.now(),
                }
            ).insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to store VAT report: {str(e)}")

    def generate_periodic_vat_alerts(self):
        """Generate periodic VAT compliance alerts and reminders"""
        alerts = []

        # Monthly VAT filing reminder
        today_date = getdate(today())
        if today_date.day >= 15:  # Alert after 15th of each month
            last_month_start = get_first_day(add_months(today(), -1))
            last_month_end = get_last_day(add_months(today(), -1))

            alerts.append(
                {
                    "type": "monthly_filing",
                    "priority": "high",
                    "message": f"VAT return filing due for period {last_month_start} to {last_month_end}",
                    "action_required": "Generate and submit VAT return",
                    "due_date": get_last_day(today()).strftime("%Y-%m-%d"),
                }
            )

        # Quarterly review reminder
        quarter = self._get_quarter(today_date)
        if today_date.day >= 25 and today_date.month in [3, 6, 9, 12]:
            alerts.append(
                {
                    "type": "quarterly_review",
                    "priority": "medium",
                    "message": f"Quarterly VAT review due for Q{quarter}",
                    "action_required": "Review quarterly VAT compliance and reconcile accounts",
                    "due_date": get_last_day(today()).strftime("%Y-%m-%d"),
                }
            )

        return alerts

    def prepare_einvoicing_data(self, invoice_name):
        """
        Prepare invoice data for future e-invoicing compliance
        (When Oman implements e-invoicing in second half of 2025)

        Args:
            invoice_name (str): Sales Invoice name

        Returns:
            dict: E-invoicing ready data structure
        """
        try:
            invoice = frappe.get_doc("Sales Invoice", invoice_name)

            # Base invoice data structure for future e-invoicing
            einvoice_data = {
                "invoice_header": {
                    "invoice_number": invoice.name,
                    "invoice_date": invoice.posting_date.isoformat(),
                    "invoice_type": "Standard",
                    "currency": invoice.currency,
                    "supplier_info": self._get_supplier_info(),
                    "customer_info": self._get_customer_info(invoice.customer),
                },
                "invoice_lines": [],
                "tax_summary": {
                    "total_excluding_vat": flt(invoice.net_total, 3),
                    "total_vat_amount": flt(invoice.total_taxes_and_charges, 3),
                    "total_including_vat": flt(invoice.grand_total, 3),
                },
                "payment_terms": {
                    "payment_method": invoice.mode_of_payment or "Cash",
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                },
            }

            # Add invoice line items
            for item in invoice.items:
                line_data = {
                    "line_number": item.idx,
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "quantity": flt(item.qty, 2),
                    "unit_price": flt(item.rate, 3),
                    "line_total": flt(item.amount, 3),
                    "vat_rate": self._get_item_vat_rate(item),
                    "vat_amount": flt(item.amount * (self._get_item_vat_rate(item) / 100), 3),
                }
                einvoice_data["invoice_lines"].append(line_data)

            # Add future QR code placeholder
            einvoice_data["qr_code"] = self._generate_invoice_qr_code(invoice)

            return einvoice_data

        except Exception as e:
            frappe.log_error(f"E-invoicing data preparation error: {str(e)}")
            return None

    def _get_supplier_info(self):
        """Get supplier (company) information for e-invoicing"""
        company_doc = frappe.get_doc("Company", self.company)

        return {
            "name": company_doc.company_name,
            "vat_number": company_doc.tax_id,
            "address": self._format_company_address(company_doc),
            "business_license": getattr(company_doc, "registration_details", ""),
        }

    def _get_customer_info(self, customer_name):
        """Get customer information for e-invoicing"""
        customer = frappe.get_doc("Customer", customer_name)

        return {
            "name": customer.customer_name,
            "vat_number": customer.tax_id,
            "customer_group": customer.customer_group,
            "territory": customer.territory,
        }

    def _format_company_address(self, company_doc):
        """Format company address for e-invoicing"""
        # This would format the company address according to Oman standards
        return getattr(company_doc, "company_address", "")

    def _get_item_vat_rate(self, item):
        """Get VAT rate for an item"""
        # Default to standard VAT rate
        # This could be enhanced to check item-specific tax templates
        return self.vat_rate

    def _generate_invoice_qr_code(self, invoice):
        """
        Generate QR code data for invoice (placeholder for future implementation)

        Args:
            invoice: Sales Invoice document

        Returns:
            dict: QR code data structure
        """
        # Placeholder for future QR code implementation
        # When Oman implements e-invoicing, this will generate
        # the required QR code with invoice verification data

        qr_data = {
            "invoice_hash": f"HASH_{invoice.name}_{invoice.posting_date}",
            "digital_signature": f"SIG_{invoice.name}",
            "timestamp": datetime.now().isoformat(),
            "verification_url": f"https://verify.tax.gov.om/invoice/{invoice.name}",
            "qr_code_text": f"Invoice: {invoice.name}, Amount: {invoice.grand_total}, Date: {invoice.posting_date}",
        }

        return qr_data


# WhiteListed API Methods for VAT Compliance


@frappe.whitelist()
def generate_vat_return_report(from_date, to_date, language="en"):
    """
    Generate VAT return report for specified period

    Args:
        from_date (str): Start date
        to_date (str): End date
        language (str): Report language ('en' or 'ar')

    Returns:
        dict: Comprehensive VAT return report
    """
    manager = VATComplianceReportingManager()
    return manager.generate_vat_return_report(from_date, to_date, language)


@frappe.whitelist()
def get_vat_compliance_dashboard():
    """
    Get VAT compliance dashboard data

    Returns:
        dict: Dashboard data with alerts and status
    """
    manager = VATComplianceReportingManager()

    # Get current month data
    current_month_start = get_first_day(today())
    current_month_end = get_last_day(today())

    # Generate basic report for current month
    current_report = manager.generate_vat_return_report(
        current_month_start, current_month_end, "en"
    )

    # Get alerts
    alerts = manager.generate_periodic_vat_alerts()

    return {
        "current_month_summary": current_report["vat_summary"],
        "compliance_status": current_report["compliance_checks"],
        "alerts": alerts,
        "last_updated": datetime.now().isoformat(),
    }


@frappe.whitelist()
def prepare_invoice_einvoicing_data(invoice_name):
    """
    Prepare invoice data for future e-invoicing compliance

    Args:
        invoice_name (str): Sales Invoice name

    Returns:
        dict: E-invoicing ready data structure
    """
    manager = VATComplianceReportingManager()
    return manager.prepare_einvoicing_data(invoice_name)


@frappe.whitelist()
def run_vat_compliance_check(from_date=None, to_date=None):
    """
    Run comprehensive VAT compliance check

    Args:
        from_date (str, optional): Start date (defaults to current month)
        to_date (str, optional): End date (defaults to current month)

    Returns:
        dict: Compliance check results
    """
    if not from_date:
        from_date = get_first_day(today())
    if not to_date:
        to_date = get_last_day(today())

    manager = VATComplianceReportingManager()

    # Get basic data for compliance check
    sales_data = manager._get_sales_vat_data(getdate(from_date), getdate(to_date))
    purchase_data = manager._get_purchase_vat_data(getdate(from_date), getdate(to_date))

    # Run compliance checks
    compliance_results = manager._run_compliance_checks(getdate(from_date), getdate(to_date))

    return {
        "period": {"from_date": from_date, "to_date": to_date},
        "summary": {
            "total_sales_invoices": sales_data["invoice_count"],
            "total_purchase_invoices": purchase_data["invoice_count"],
            "total_output_vat": sales_data["period_total_output_vat"],
            "total_input_vat": purchase_data["period_total_input_vat"],
        },
        "compliance_checks": compliance_results,
        "overall_status": (
            "compliant"
            if all(check["status"] in ["pass", "info"] for check in compliance_results)
            else "issues_found"
        ),
    }
