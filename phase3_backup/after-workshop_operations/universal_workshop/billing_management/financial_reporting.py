"""
Financial Reporting System for Universal Workshop ERP
Implements Oman VAT compliance and government reporting requirements
Supports quarterly VAT returns, aging analysis, and audit trails
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_months, today, format_date
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple


class OmanFinancialReportingManager:
    """
    Comprehensive financial reporting system for Oman VAT compliance
    Handles quarterly VAT returns, aging analysis, and government reporting
    """

    def __init__(self):
        self.vat_rate = 5.0  # Oman VAT rate
        self.currency = "OMR"
        self.precision = 3

    def generate_quarterly_vat_return(
        self, company: str, quarter: int, year: int
    ) -> Dict[str, Any]:
        """
        Generate quarterly VAT return for Oman Tax Authority (OTA)

        Args:
            company: Company name
            quarter: Quarter number (1-4)
            year: Year

        Returns:
            Dict containing VAT return data
        """
        try:
            # Calculate quarter date range
            start_month = (quarter - 1) * 3 + 1
            start_date = f"{year}-{start_month:02d}-01"
            end_date = add_months(start_date, 3)

            # Get sales data
            sales_data = self._get_sales_vat_data(company, start_date, end_date)

            # Get purchase data
            purchase_data = self._get_purchase_vat_data(company, start_date, end_date)

            # Calculate net VAT liability
            net_vat = sales_data["total_vat"] - purchase_data["total_vat"]

            vat_return = {
                "company": company,
                "quarter": quarter,
                "year": year,
                "period_start": start_date,
                "period_end": end_date,
                "generated_on": today(),
                "currency": self.currency,
                # Sales information
                "total_sales_value": sales_data["total_value"],
                "vat_on_sales": sales_data["total_vat"],
                "zero_rated_sales": sales_data["zero_rated"],
                "exempt_sales": sales_data["exempt"],
                # Purchase information
                "total_purchase_value": purchase_data["total_value"],
                "vat_on_purchases": purchase_data["total_vat"],
                "zero_rated_purchases": purchase_data["zero_rated"],
                "exempt_purchases": purchase_data["exempt"],
                # VAT calculation
                "net_vat_liability": net_vat,
                "vat_refund_due": abs(net_vat) if net_vat < 0 else 0,
                "vat_payment_due": net_vat if net_vat > 0 else 0,
                # Additional information
                "sales_breakdown": sales_data["breakdown"],
                "purchase_breakdown": purchase_data["breakdown"],
                "customer_vat_breakdown": self._get_customer_vat_breakdown(
                    company, start_date, end_date
                ),
                "supplier_vat_breakdown": self._get_supplier_vat_breakdown(
                    company, start_date, end_date
                ),
            }

            # Store VAT return record
            self._save_vat_return_record(vat_return)

            return vat_return

        except Exception as e:
            frappe.log_error(f"VAT return generation failed: {e}")
            raise frappe.ValidationError(_("Failed to generate VAT return: {0}").format(str(e)))

    def _get_sales_vat_data(self, company: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get sales VAT data for the period"""

        sales_query = """
            SELECT 
                si.base_total as total_value,
                si.base_total_taxes_and_charges as tax_amount,
                si.customer,
                c.customer_name,
                c.customer_name_ar,
                c.tax_category,
                si.taxes_and_charges_template,
                COALESCE(si.custom_is_zero_rated, 0) as is_zero_rated,
                COALESCE(si.custom_is_exempt, 0) as is_exempt
            FROM `tabSales Invoice` si
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            WHERE si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
        """

        sales_data = frappe.db.sql(sales_query, [company, start_date, end_date], as_dict=True)

        total_value = 0
        total_vat = 0
        zero_rated = 0
        exempt = 0
        breakdown = []

        for sale in sales_data:
            total_value += flt(sale.total_value, self.precision)

            if sale.is_zero_rated:
                zero_rated += flt(sale.total_value, self.precision)
            elif sale.is_exempt:
                exempt += flt(sale.total_value, self.precision)
            else:
                vat_amount = flt(sale.tax_amount, self.precision)
                total_vat += vat_amount

            breakdown.append(
                {
                    "customer": sale.customer,
                    "customer_name": sale.customer_name,
                    "customer_name_ar": sale.customer_name_ar,
                    "value": flt(sale.total_value, self.precision),
                    "vat": flt(sale.tax_amount, self.precision),
                    "category": (
                        "Zero Rated"
                        if sale.is_zero_rated
                        else "Exempt" if sale.is_exempt else "Standard"
                    ),
                }
            )

        return {
            "total_value": total_value,
            "total_vat": total_vat,
            "zero_rated": zero_rated,
            "exempt": exempt,
            "breakdown": breakdown,
        }

    def _get_purchase_vat_data(
        self, company: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Get purchase VAT data for the period"""

        purchase_query = """
            SELECT 
                pi.base_total as total_value,
                pi.base_total_taxes_and_charges as tax_amount,
                pi.supplier,
                s.supplier_name,
                s.supplier_name_ar,
                s.tax_category,
                pi.taxes_and_charges_template,
                COALESCE(pi.custom_is_zero_rated, 0) as is_zero_rated,
                COALESCE(pi.custom_is_exempt, 0) as is_exempt
            FROM `tabPurchase Invoice` pi
            LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
            WHERE pi.company = %s
            AND pi.posting_date BETWEEN %s AND %s
            AND pi.docstatus = 1
        """

        purchase_data = frappe.db.sql(purchase_query, [company, start_date, end_date], as_dict=True)

        total_value = 0
        total_vat = 0
        zero_rated = 0
        exempt = 0
        breakdown = []

        for purchase in purchase_data:
            total_value += flt(purchase.total_value, self.precision)

            if purchase.is_zero_rated:
                zero_rated += flt(purchase.total_value, self.precision)
            elif purchase.is_exempt:
                exempt += flt(purchase.total_value, self.precision)
            else:
                vat_amount = flt(purchase.tax_amount, self.precision)
                total_vat += vat_amount

            breakdown.append(
                {
                    "supplier": purchase.supplier,
                    "supplier_name": purchase.supplier_name,
                    "supplier_name_ar": purchase.supplier_name_ar,
                    "value": flt(purchase.total_value, self.precision),
                    "vat": flt(purchase.tax_amount, self.precision),
                    "category": (
                        "Zero Rated"
                        if purchase.is_zero_rated
                        else "Exempt" if purchase.is_exempt else "Standard"
                    ),
                }
            )

        return {
            "total_value": total_value,
            "total_vat": total_vat,
            "zero_rated": zero_rated,
            "exempt": exempt,
            "breakdown": breakdown,
        }

    def _get_customer_vat_breakdown(
        self, company: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """Get VAT breakdown by customer for detailed reporting"""

        query = """
            SELECT 
                si.customer,
                c.customer_name,
                c.customer_name_ar,
                c.tax_id,
                COUNT(si.name) as invoice_count,
                SUM(si.base_total) as total_sales,
                SUM(si.base_total_taxes_and_charges) as total_vat,
                c.customer_type
            FROM `tabSales Invoice` si
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            WHERE si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
            GROUP BY si.customer
            ORDER BY total_sales DESC
        """

        results = frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

        breakdown = []
        for row in results:
            breakdown.append(
                {
                    "customer_code": row.customer,
                    "customer_name": row.customer_name,
                    "customer_name_ar": row.customer_name_ar or "",
                    "tax_id": row.tax_id or "",
                    "customer_type": row.customer_type or "Individual",
                    "invoice_count": cint(row.invoice_count),
                    "total_sales": flt(row.total_sales, self.precision),
                    "total_vat": flt(row.total_vat, self.precision),
                    "average_invoice": flt(row.total_sales / row.invoice_count, self.precision),
                }
            )

        return breakdown

    def _get_supplier_vat_breakdown(
        self, company: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """Get VAT breakdown by supplier for detailed reporting"""

        query = """
            SELECT 
                pi.supplier,
                s.supplier_name,
                s.supplier_name_ar,
                s.tax_id,
                COUNT(pi.name) as invoice_count,
                SUM(pi.base_total) as total_purchases,
                SUM(pi.base_total_taxes_and_charges) as total_vat,
                s.supplier_type
            FROM `tabPurchase Invoice` pi
            LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
            WHERE pi.company = %s
            AND pi.posting_date BETWEEN %s AND %s
            AND pi.docstatus = 1
            GROUP BY pi.supplier
            ORDER BY total_purchases DESC
        """

        results = frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

        breakdown = []
        for row in results:
            breakdown.append(
                {
                    "supplier_code": row.supplier,
                    "supplier_name": row.supplier_name,
                    "supplier_name_ar": row.supplier_name_ar or "",
                    "tax_id": row.tax_id or "",
                    "supplier_type": row.supplier_type or "Company",
                    "invoice_count": cint(row.invoice_count),
                    "total_purchases": flt(row.total_purchases, self.precision),
                    "total_vat": flt(row.total_vat, self.precision),
                    "average_invoice": flt(row.total_purchases / row.invoice_count, self.precision),
                }
            )

        return breakdown

    def _save_vat_return_record(self, vat_return: Dict[str, Any]):
        """Save VAT return record for audit trail"""

        if not frappe.db.exists("DocType", "VAT Return Record"):
            self._create_vat_return_doctype()

        doc = frappe.new_doc("VAT Return Record")
        doc.update(
            {
                "company": vat_return["company"],
                "quarter": vat_return["quarter"],
                "year": vat_return["year"],
                "period_start": vat_return["period_start"],
                "period_end": vat_return["period_end"],
                "total_sales_value": vat_return["total_sales_value"],
                "vat_on_sales": vat_return["vat_on_sales"],
                "total_purchase_value": vat_return["total_purchase_value"],
                "vat_on_purchases": vat_return["vat_on_purchases"],
                "net_vat_liability": vat_return["net_vat_liability"],
                "status": "Generated",
                "generated_by": frappe.session.user,
                "vat_return_data": json.dumps(vat_return, default=str),
            }
        )
        doc.insert()
        doc.submit()

    def _create_vat_return_doctype(self):
        """Create VAT Return Record DocType if it doesn't exist"""

        doctype_dict = {
            "doctype": "DocType",
            "name": "VAT Return Record",
            "module": "Universal Workshop",
            "custom": 1,
            "is_submittable": 1,
            "track_changes": 1,
            "autoname": "naming_series:",
            "naming_series": "VAT-RTN-.YYYY.-.#####",
            "fields": [
                {
                    "fieldname": "naming_series",
                    "fieldtype": "Select",
                    "label": "Series",
                    "options": "VAT-RTN-.YYYY.-.#####",
                    "reqd": 1,
                },
                {
                    "fieldname": "company",
                    "fieldtype": "Link",
                    "label": "Company",
                    "options": "Company",
                    "reqd": 1,
                },
                {"fieldname": "quarter", "fieldtype": "Int", "label": "Quarter", "reqd": 1},
                {"fieldname": "year", "fieldtype": "Int", "label": "Year", "reqd": 1},
                {
                    "fieldname": "period_start",
                    "fieldtype": "Date",
                    "label": "Period Start",
                    "reqd": 1,
                },
                {"fieldname": "period_end", "fieldtype": "Date", "label": "Period End", "reqd": 1},
                {
                    "fieldname": "total_sales_value",
                    "fieldtype": "Currency",
                    "label": "Total Sales Value",
                    "options": "OMR",
                    "precision": 3,
                },
                {
                    "fieldname": "vat_on_sales",
                    "fieldtype": "Currency",
                    "label": "VAT on Sales",
                    "options": "OMR",
                    "precision": 3,
                },
                {
                    "fieldname": "total_purchase_value",
                    "fieldtype": "Currency",
                    "label": "Total Purchase Value",
                    "options": "OMR",
                    "precision": 3,
                },
                {
                    "fieldname": "vat_on_purchases",
                    "fieldtype": "Currency",
                    "label": "VAT on Purchases",
                    "options": "OMR",
                    "precision": 3,
                },
                {
                    "fieldname": "net_vat_liability",
                    "fieldtype": "Currency",
                    "label": "Net VAT Liability",
                    "options": "OMR",
                    "precision": 3,
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "label": "Status",
                    "options": "Generated\nSubmitted to OTA\nAccepted\nRejected",
                    "default": "Generated",
                },
                {
                    "fieldname": "generated_by",
                    "fieldtype": "Link",
                    "label": "Generated By",
                    "options": "User",
                },
                {
                    "fieldname": "vat_return_data",
                    "fieldtype": "Long Text",
                    "label": "VAT Return Data",
                },
            ],
        }

        doc = frappe.get_doc(doctype_dict)
        doc.insert()

    def generate_vat_audit_trail(
        self, company: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive VAT audit trail with drill-down capability
        Required for Oman VAT compliance
        """

        audit_trail = {
            "company": company,
            "period_start": start_date,
            "period_end": end_date,
            "generated_on": today(),
            "generated_by": frappe.session.user,
            "sales_register": self._generate_sales_register(company, start_date, end_date),
            "purchase_register": self._generate_purchase_register(company, start_date, end_date),
            "vat_rate_analysis": self._analyze_vat_rates(company, start_date, end_date),
            "customer_analysis": self._analyze_customer_vat(company, start_date, end_date),
            "supplier_analysis": self._analyze_supplier_vat(company, start_date, end_date),
            "payment_analysis": self._analyze_payment_vat_impact(company, start_date, end_date),
        }

        return audit_trail

    def _generate_sales_register(self, company: str, start_date: str, end_date: str) -> List[Dict]:
        """Generate detailed sales register for audit"""

        query = """
            SELECT 
                si.name as invoice_number,
                si.posting_date,
                si.customer,
                c.customer_name,
                c.customer_name_ar,
                c.tax_id as customer_tax_id,
                si.base_net_total,
                si.base_total_taxes_and_charges as vat_amount,
                si.base_grand_total,
                si.taxes_and_charges_template,
                COALESCE(si.custom_vat_number, '') as invoice_vat_number,
                COALESCE(si.custom_qr_code, '') as qr_code,
                si.workflow_state,
                si.modified,
                si.modified_by
            FROM `tabSales Invoice` si
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            WHERE si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
            ORDER BY si.posting_date, si.name
        """

        return frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

    def _generate_purchase_register(
        self, company: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """Generate detailed purchase register for audit"""

        query = """
            SELECT 
                pi.name as invoice_number,
                pi.posting_date,
                pi.supplier,
                s.supplier_name,
                s.supplier_name_ar,
                s.tax_id as supplier_tax_id,
                pi.base_net_total,
                pi.base_total_taxes_and_charges as vat_amount,
                pi.base_grand_total,
                pi.taxes_and_charges_template,
                pi.bill_no as supplier_invoice_number,
                pi.bill_date as supplier_invoice_date,
                pi.workflow_state,
                pi.modified,
                pi.modified_by
            FROM `tabPurchase Invoice` pi
            LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
            WHERE pi.company = %s
            AND pi.posting_date BETWEEN %s AND %s
            AND pi.docstatus = 1
            ORDER BY pi.posting_date, pi.name
        """

        return frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

    def _analyze_vat_rates(self, company: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Analyze VAT rates used during the period"""

        sales_vat_rates = frappe.db.sql(
            """
            SELECT 
                taxes_and_charges_template,
                COUNT(*) as transaction_count,
                SUM(base_net_total) as net_total,
                SUM(base_total_taxes_and_charges) as vat_total,
                AVG(base_total_taxes_and_charges / NULLIF(base_net_total, 0) * 100) as avg_vat_rate
            FROM `tabSales Invoice`
            WHERE company = %s
            AND posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY taxes_and_charges_template
        """,
            [company, start_date, end_date],
            as_dict=True,
        )

        purchase_vat_rates = frappe.db.sql(
            """
            SELECT 
                taxes_and_charges_template,
                COUNT(*) as transaction_count,
                SUM(base_net_total) as net_total,
                SUM(base_total_taxes_and_charges) as vat_total,
                AVG(base_total_taxes_and_charges / NULLIF(base_net_total, 0) * 100) as avg_vat_rate
            FROM `tabPurchase Invoice`
            WHERE company = %s
            AND posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY taxes_and_charges_template
        """,
            [company, start_date, end_date],
            as_dict=True,
        )

        return {"sales_vat_rates": sales_vat_rates, "purchase_vat_rates": purchase_vat_rates}

    def _analyze_customer_vat(self, company: str, start_date: str, end_date: str) -> List[Dict]:
        """Analyze VAT by customer for compliance checking"""

        query = """
            SELECT 
                si.customer,
                c.customer_name,
                c.customer_name_ar,
                c.tax_id,
                c.customer_type,
                COUNT(si.name) as invoice_count,
                MIN(si.posting_date) as first_invoice_date,
                MAX(si.posting_date) as last_invoice_date,
                SUM(si.base_net_total) as total_net,
                SUM(si.base_total_taxes_and_charges) as total_vat,
                SUM(si.base_grand_total) as total_gross,
                AVG(si.base_total_taxes_and_charges / NULLIF(si.base_net_total, 0) * 100) as avg_vat_rate
            FROM `tabSales Invoice` si
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            WHERE si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
            GROUP BY si.customer
            HAVING total_gross > 1000  -- Focus on significant customers
            ORDER BY total_gross DESC
        """

        return frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

    def _analyze_supplier_vat(self, company: str, start_date: str, end_date: str) -> List[Dict]:
        """Analyze VAT by supplier for compliance checking"""

        query = """
            SELECT 
                pi.supplier,
                s.supplier_name,
                s.supplier_name_ar,
                s.tax_id,
                s.supplier_type,
                COUNT(pi.name) as invoice_count,
                MIN(pi.posting_date) as first_invoice_date,
                MAX(pi.posting_date) as last_invoice_date,
                SUM(pi.base_net_total) as total_net,
                SUM(pi.base_total_taxes_and_charges) as total_vat,
                SUM(pi.base_grand_total) as total_gross,
                AVG(pi.base_total_taxes_and_charges / NULLIF(pi.base_net_total, 0) * 100) as avg_vat_rate
            FROM `tabPurchase Invoice` pi
            LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
            WHERE pi.company = %s
            AND pi.posting_date BETWEEN %s AND %s
            AND pi.docstatus = 1
            GROUP BY pi.supplier
            HAVING total_gross > 500  -- Focus on significant suppliers
            ORDER BY total_gross DESC
        """

        return frappe.db.sql(query, [company, start_date, end_date], as_dict=True)

    def _analyze_payment_vat_impact(
        self, company: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Analyze payment impact on VAT for cash accounting if applicable"""

        # Get payment entries linked to invoices
        payment_query = """
            SELECT 
                pe.name as payment_entry,
                pe.posting_date as payment_date,
                pe.paid_amount,
                pe.received_amount,
                per.reference_doctype,
                per.reference_name,
                per.allocated_amount,
                CASE 
                    WHEN per.reference_doctype = 'Sales Invoice' THEN 'Sales'
                    WHEN per.reference_doctype = 'Purchase Invoice' THEN 'Purchase'
                    ELSE 'Other'
                END as transaction_type
            FROM `tabPayment Entry` pe
            INNER JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
            WHERE pe.company = %s
            AND pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            AND per.reference_doctype IN ('Sales Invoice', 'Purchase Invoice')
        """

        payments = frappe.db.sql(payment_query, [company, start_date, end_date], as_dict=True)

        sales_payments = [p for p in payments if p.transaction_type == "Sales"]
        purchase_payments = [p for p in payments if p.transaction_type == "Purchase"]

        return {
            "total_sales_payments": sum(p.allocated_amount for p in sales_payments),
            "total_purchase_payments": sum(p.allocated_amount for p in purchase_payments),
            "sales_payment_count": len(sales_payments),
            "purchase_payment_count": len(purchase_payments),
            "payment_details": payments,
        }


# API methods for external access
@frappe.whitelist()
def generate_quarterly_vat_return(company, quarter, year):
    """Generate quarterly VAT return (API endpoint)"""
    manager = OmanFinancialReportingManager()
    return manager.generate_quarterly_vat_return(company, cint(quarter), cint(year))


@frappe.whitelist()
def generate_vat_audit_trail(company, start_date, end_date):
    """Generate VAT audit trail (API endpoint)"""
    manager = OmanFinancialReportingManager()
    return manager.generate_vat_audit_trail(company, start_date, end_date)


@frappe.whitelist()
def get_company_vat_info(company):
    """Get company VAT registration information"""
    return frappe.db.get_value(
        "Company",
        company,
        [
            "custom_vat_registered",
            "custom_vat_registration_date",
            "custom_business_activity",
            "custom_quarterly_filing_day",
            "tax_id",
        ],
        as_dict=True,
    )


@frappe.whitelist()
def validate_vat_compliance(company, start_date, end_date):
    """Validate VAT compliance for the period"""

    # Check for missing VAT numbers on invoices
    missing_vat_invoices = frappe.db.sql(
        """
        SELECT name, posting_date, customer, base_grand_total
        FROM `tabSales Invoice`
        WHERE company = %s
        AND posting_date BETWEEN %s AND %s
        AND docstatus = 1
        AND (custom_vat_number IS NULL OR custom_vat_number = '')
        AND base_grand_total > 100
    """,
        [company, start_date, end_date],
        as_dict=True,
    )

    # Check for missing QR codes
    missing_qr_invoices = frappe.db.sql(
        """
        SELECT name, posting_date, customer, base_grand_total
        FROM `tabSales Invoice`
        WHERE company = %s
        AND posting_date BETWEEN %s AND %s
        AND docstatus = 1
        AND (custom_qr_code IS NULL OR custom_qr_code = '')
        AND base_grand_total > 100
    """,
        [company, start_date, end_date],
        as_dict=True,
    )

    return {
        "missing_vat_numbers": missing_vat_invoices,
        "missing_qr_codes": missing_qr_invoices,
        "compliance_score": 100 - (len(missing_vat_invoices) + len(missing_qr_invoices)) * 2,
        "recommendations": [
            "Ensure all invoices above OMR 100 have VAT numbers",
            "Generate QR codes for all tax invoices",
            "Maintain proper VAT rate consistency",
            "Keep detailed audit trails for 10 years",
        ],
    }
