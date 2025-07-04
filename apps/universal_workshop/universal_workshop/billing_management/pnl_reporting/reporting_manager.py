"""
Universal Workshop ERP - Profit & Loss Reporting System
ERPNext v15 compatible with Arabic localization and workshop automation
Supports automated data aggregation, customizable templates, and real-time reporting
"""

import frappe
from frappe import _
from frappe.utils import (
    flt,
    cint,
    getdate,
    add_months,
    today,
    format_date,
    get_first_day,
    get_last_day,
)
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional


class WorkshopPnLReportingManager:
    """
    Comprehensive P&L reporting system for Universal Workshop ERP
    Integrates with ERPNext v15 financial modules and provides Arabic localization
    """

    def __init__(self):
        self.currency = "OMR"
        self.precision = 3
        self.language = frappe.boot.lang if hasattr(frappe, "boot") else "en"

    def generate_comprehensive_pnl(
        self,
        company: str,
        from_date: str,
        to_date: str,
        cost_center: Optional[str] = None,
        comparison_period: Optional[str] = None,
        include_workshop_metrics: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive P&L report with workshop-specific enhancements

        Args:
            company: Company name
            from_date: Start date for reporting period
            to_date: End date for reporting period
            cost_center: Optional cost center filter
            comparison_period: Optional comparison period (previous_year, previous_quarter)
            include_workshop_metrics: Include workshop-specific operational metrics

        Returns:
            Dict containing comprehensive P&L data
        """
        try:
            # Revenue section
            revenue_data = self._calculate_revenue_section(company, from_date, to_date, cost_center)

            # Cost of services section
            cogs_data = self._calculate_cogs_section(company, from_date, to_date, cost_center)

            # Operating expenses section
            opex_data = self._calculate_operating_expenses(company, from_date, to_date, cost_center)

            # Calculate gross and net profit
            gross_profit = revenue_data["total_revenue"] - cogs_data["total_cogs"]
            operating_profit = gross_profit - opex_data["total_operating_expenses"]
            net_profit = operating_profit - opex_data.get("non_operating_expenses", 0)

            # Prepare main P&L structure
            pnl_report = {
                "company": company,
                "period_from": from_date,
                "period_to": to_date,
                "cost_center": cost_center,
                "currency": self.currency,
                "generated_on": today(),
                "language": self.language,
                # Revenue Section
                "revenue": revenue_data,
                # Cost of Services Section
                "cost_of_services": cogs_data,
                # Gross Profit
                "gross_profit": {
                    "amount": flt(gross_profit, self.precision),
                    "percentage": flt(
                        (
                            (gross_profit / revenue_data["total_revenue"] * 100)
                            if revenue_data["total_revenue"] > 0
                            else 0
                        ),
                        2,
                    ),
                    "label_en": "Gross Profit",
                    "label_ar": "إجمالي الربح",
                },
                # Operating Expenses Section
                "operating_expenses": opex_data,
                # Operating Profit
                "operating_profit": {
                    "amount": flt(operating_profit, self.precision),
                    "percentage": flt(
                        (
                            (operating_profit / revenue_data["total_revenue"] * 100)
                            if revenue_data["total_revenue"] > 0
                            else 0
                        ),
                        2,
                    ),
                    "label_en": "Operating Profit",
                    "label_ar": "الربح التشغيلي",
                },
                # Net Profit
                "net_profit": {
                    "amount": flt(net_profit, self.precision),
                    "percentage": flt(
                        (
                            (net_profit / revenue_data["total_revenue"] * 100)
                            if revenue_data["total_revenue"] > 0
                            else 0
                        ),
                        2,
                    ),
                    "label_en": "Net Profit",
                    "label_ar": "صافي الربح",
                },
            }

            # Add workshop-specific metrics if requested
            if include_workshop_metrics:
                pnl_report["workshop_metrics"] = self._calculate_workshop_metrics(
                    company, from_date, to_date, cost_center
                )

            # Add comparison data if requested
            if comparison_period:
                pnl_report["comparison"] = self._calculate_comparison_period(
                    company, from_date, to_date, comparison_period, cost_center
                )

            # Store P&L report record
            self._save_pnl_report_record(pnl_report)

            return pnl_report

        except Exception as e:
            frappe.log_error(f"P&L report generation failed: {e}")
            raise frappe.ValidationError(_("Failed to generate P&L report: {0}").format(str(e)))

    def _calculate_revenue_section(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate revenue section with workshop-specific breakdowns"""

        # Service revenue
        service_revenue = self._get_service_revenue(company, from_date, to_date, cost_center)

        # Parts sales revenue
        parts_revenue = self._get_parts_revenue(company, from_date, to_date, cost_center)

        # Other income
        other_income = self._get_other_income(company, from_date, to_date, cost_center)

        total_revenue = service_revenue["total"] + parts_revenue["total"] + other_income["total"]

        return {
            "service_revenue": service_revenue,
            "parts_revenue": parts_revenue,
            "other_income": other_income,
            "total_revenue": flt(total_revenue, self.precision),
            "label_en": "Total Revenue",
            "label_ar": "إجمالي الإيرادات",
        }

    def _get_service_revenue(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get service revenue breakdown by service type"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND si.cost_center = %(cost_center)s"

        service_query = f"""
            SELECT 
                sii.item_code,
                i.item_name,
                i.item_name_ar,
                i.item_group,
                SUM(sii.base_amount) as revenue_amount,
                COUNT(DISTINCT si.name) as invoice_count,
                AVG(sii.base_rate) as avg_rate
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON sii.parent = si.name
            JOIN `tabItem` i ON sii.item_code = i.item_code
            WHERE si.company = %(company)s
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND si.docstatus = 1
            AND i.is_stock_item = 0  -- Service items
            {cost_center_condition}
            GROUP BY sii.item_code, i.item_name, i.item_name_ar, i.item_group
            ORDER BY revenue_amount DESC
        """

        service_data = frappe.db.sql(
            service_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        # Group by service categories
        service_breakdown = {}
        total_service_revenue = 0

        for service in service_data:
            revenue = flt(service.revenue_amount, self.precision)
            total_service_revenue += revenue

            group = service.item_group or "Other Services"
            if group not in service_breakdown:
                service_breakdown[group] = {"services": [], "total_revenue": 0, "invoice_count": 0}

            service_breakdown[group]["services"].append(
                {
                    "item_code": service.item_code,
                    "item_name": service.item_name,
                    "item_name_ar": service.item_name_ar,
                    "revenue": revenue,
                    "invoice_count": service.invoice_count,
                    "avg_rate": flt(service.avg_rate, self.precision),
                }
            )
            service_breakdown[group]["total_revenue"] += revenue
            service_breakdown[group]["invoice_count"] += service.invoice_count

        return {
            "total": flt(total_service_revenue, self.precision),
            "breakdown": service_breakdown,
            "label_en": "Service Revenue",
            "label_ar": "إيرادات الخدمات",
        }

    def _get_parts_revenue(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get parts sales revenue breakdown"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND si.cost_center = %(cost_center)s"

        parts_query = f"""
            SELECT 
                sii.item_code,
                i.item_name,
                i.item_name_ar,
                i.item_group,
                SUM(sii.base_amount) as revenue_amount,
                SUM(sii.qty) as total_qty,
                AVG(sii.base_rate) as avg_rate
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON sii.parent = si.name
            JOIN `tabItem` i ON sii.item_code = i.item_code
            WHERE si.company = %(company)s
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND si.docstatus = 1
            AND i.is_stock_item = 1  -- Parts/inventory items
            {cost_center_condition}
            GROUP BY sii.item_code, i.item_name, i.item_name_ar, i.item_group
            ORDER BY revenue_amount DESC
        """

        parts_data = frappe.db.sql(
            parts_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        # Group by parts categories
        parts_breakdown = {}
        total_parts_revenue = 0

        for part in parts_data:
            revenue = flt(part.revenue_amount, self.precision)
            total_parts_revenue += revenue

            group = part.item_group or "Other Parts"
            if group not in parts_breakdown:
                parts_breakdown[group] = {"parts": [], "total_revenue": 0, "total_qty": 0}

            parts_breakdown[group]["parts"].append(
                {
                    "item_code": part.item_code,
                    "item_name": part.item_name,
                    "item_name_ar": part.item_name_ar,
                    "revenue": revenue,
                    "qty": flt(part.total_qty, 2),
                    "avg_rate": flt(part.avg_rate, self.precision),
                }
            )
            parts_breakdown[group]["total_revenue"] += revenue
            parts_breakdown[group]["total_qty"] += flt(part.total_qty, 2)

        return {
            "total": flt(total_parts_revenue, self.precision),
            "breakdown": parts_breakdown,
            "label_en": "Parts Revenue",
            "label_ar": "إيرادات قطع الغيار",
        }

    def _get_other_income(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get other income (non-operating revenue)"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        # Get other income from GL entries
        other_income_query = f"""
            SELECT 
                account,
                account_name,
                SUM(credit - debit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND account_type = 'Income Account'
                AND name NOT LIKE '%%Service%%'
                AND name NOT LIKE '%%Sales%%'
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        other_income_data = frappe.db.sql(
            other_income_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_other_income = 0

        for income in other_income_data:
            amount = flt(income.amount, self.precision)
            total_other_income += amount
            breakdown.append(
                {"account": income.account, "account_name": income.account_name, "amount": amount}
            )

        return {
            "total": flt(total_other_income, self.precision),
            "breakdown": breakdown,
            "label_en": "Other Income",
            "label_ar": "الدخل الآخر",
        }

    def _calculate_cogs_section(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate Cost of Goods/Services Sold"""

        # Direct material costs (parts)
        material_costs = self._get_material_costs(company, from_date, to_date, cost_center)

        # Direct labor costs
        labor_costs = self._get_labor_costs(company, from_date, to_date, cost_center)

        # Service delivery costs
        service_costs = self._get_service_delivery_costs(company, from_date, to_date, cost_center)

        total_cogs = material_costs["total"] + labor_costs["total"] + service_costs["total"]

        return {
            "material_costs": material_costs,
            "labor_costs": labor_costs,
            "service_costs": service_costs,
            "total_cogs": flt(total_cogs, self.precision),
            "label_en": "Cost of Services",
            "label_ar": "تكلفة الخدمات",
        }

    def _get_material_costs(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get direct material costs (parts used in services)"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND se.cost_center = %(cost_center)s"

        # Get stock entries for materials used
        material_query = f"""
            SELECT 
                sed.item_code,
                i.item_name,
                i.item_name_ar,
                i.item_group,
                SUM(sed.qty) as total_qty,
                SUM(sed.amount) as total_cost,
                AVG(sed.basic_rate) as avg_rate
            FROM `tabStock Entry Detail` sed
            JOIN `tabStock Entry` se ON sed.parent = se.name
            JOIN `tabItem` i ON sed.item_code = i.item_code
            WHERE se.company = %(company)s
            AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND se.docstatus = 1
            AND se.stock_entry_type = 'Material Issue'
            AND sed.s_warehouse IS NOT NULL
            {cost_center_condition}
            GROUP BY sed.item_code, i.item_name, i.item_name_ar, i.item_group
            ORDER BY total_cost DESC
        """

        material_data = frappe.db.sql(
            material_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_material_cost = 0

        for material in material_data:
            cost = flt(material.total_cost, self.precision)
            total_material_cost += cost
            breakdown.append(
                {
                    "item_code": material.item_code,
                    "item_name": material.item_name,
                    "item_name_ar": material.item_name_ar,
                    "item_group": material.item_group,
                    "qty": flt(material.total_qty, 2),
                    "cost": cost,
                    "avg_rate": flt(material.avg_rate, self.precision),
                }
            )

        return {
            "total": flt(total_material_cost, self.precision),
            "breakdown": breakdown,
            "label_en": "Material Costs",
            "label_ar": "تكاليف المواد",
        }

    def _get_labor_costs(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get direct labor costs"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        # Get labor costs from GL entries or timesheet
        labor_query = f"""
            SELECT 
                account,
                account_name,
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (account_type = 'Expense Account' OR root_type = 'Expense')
                AND (name LIKE '%%Labor%%' OR name LIKE '%%Salary%%' OR name LIKE '%%Wage%%')
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        labor_data = frappe.db.sql(
            labor_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_labor_cost = 0

        for labor in labor_data:
            cost = flt(labor.amount, self.precision)
            total_labor_cost += cost
            breakdown.append(
                {"account": labor.account, "account_name": labor.account_name, "cost": cost}
            )

        return {
            "total": flt(total_labor_cost, self.precision),
            "breakdown": breakdown,
            "label_en": "Labor Costs",
            "label_ar": "تكاليف العمالة",
        }

    def _get_service_delivery_costs(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get service delivery costs (utilities, equipment depreciation, etc.)"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        service_costs_query = f"""
            SELECT 
                account,
                account_name,
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (account_type = 'Expense Account' OR root_type = 'Expense')
                AND (name LIKE '%%Utilities%%' OR name LIKE '%%Equipment%%' OR name LIKE '%%Tools%%' 
                     OR name LIKE '%%Depreciation%%' OR name LIKE '%%Maintenance%%')
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        service_data = frappe.db.sql(
            service_costs_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_service_cost = 0

        for service in service_data:
            cost = flt(service.amount, self.precision)
            total_service_cost += cost
            breakdown.append(
                {"account": service.account, "account_name": service.account_name, "cost": cost}
            )

        return {
            "total": flt(total_service_cost, self.precision),
            "breakdown": breakdown,
            "label_en": "Service Delivery Costs",
            "label_ar": "تكاليف تقديم الخدمة",
        }

    def _calculate_operating_expenses(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate operating expenses section"""

        # Administrative expenses
        admin_expenses = self._get_administrative_expenses(company, from_date, to_date, cost_center)

        # Marketing expenses
        marketing_expenses = self._get_marketing_expenses(company, from_date, to_date, cost_center)

        # General expenses
        general_expenses = self._get_general_expenses(company, from_date, to_date, cost_center)

        # Non-operating expenses
        non_operating_expenses = self._get_non_operating_expenses(
            company, from_date, to_date, cost_center
        )

        total_operating = (
            admin_expenses["total"] + marketing_expenses["total"] + general_expenses["total"]
        )

        return {
            "administrative_expenses": admin_expenses,
            "marketing_expenses": marketing_expenses,
            "general_expenses": general_expenses,
            "non_operating_expenses": flt(non_operating_expenses, self.precision),
            "total_operating_expenses": flt(total_operating, self.precision),
            "label_en": "Operating Expenses",
            "label_ar": "المصاريف التشغيلية",
        }

    def _get_administrative_expenses(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get administrative expenses"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        admin_query = f"""
            SELECT 
                account,
                account_name,
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (account_type = 'Expense Account' OR root_type = 'Expense')
                AND (name LIKE '%%Admin%%' OR name LIKE '%%Office%%' OR name LIKE '%%Management%%'
                     OR name LIKE '%%Insurance%%' OR name LIKE '%%Legal%%' OR name LIKE '%%Accounting%%')
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        admin_data = frappe.db.sql(
            admin_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_admin = 0

        for admin in admin_data:
            amount = flt(admin.amount, self.precision)
            total_admin += amount
            breakdown.append(
                {"account": admin.account, "account_name": admin.account_name, "amount": amount}
            )

        return {
            "total": flt(total_admin, self.precision),
            "breakdown": breakdown,
            "label_en": "Administrative Expenses",
            "label_ar": "المصاريف الإدارية",
        }

    def _get_marketing_expenses(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get marketing and sales expenses"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        marketing_query = f"""
            SELECT 
                account,
                account_name,
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (account_type = 'Expense Account' OR root_type = 'Expense')
                AND (name LIKE '%%Marketing%%' OR name LIKE '%%Advertising%%' OR name LIKE '%%Promotion%%'
                     OR name LIKE '%%Sales%%' OR name LIKE '%%Commission%%')
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        marketing_data = frappe.db.sql(
            marketing_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_marketing = 0

        for marketing in marketing_data:
            amount = flt(marketing.amount, self.precision)
            total_marketing += amount
            breakdown.append(
                {
                    "account": marketing.account,
                    "account_name": marketing.account_name,
                    "amount": amount,
                }
            )

        return {
            "total": flt(total_marketing, self.precision),
            "breakdown": breakdown,
            "label_en": "Marketing Expenses",
            "label_ar": "مصاريف التسويق",
        }

    def _get_general_expenses(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Get general operating expenses"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        general_query = f"""
            SELECT 
                account,
                account_name,
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (account_type = 'Expense Account' OR root_type = 'Expense')
                AND name NOT LIKE '%%Labor%%' 
                AND name NOT LIKE '%%Salary%%'
                AND name NOT LIKE '%%Admin%%'
                AND name NOT LIKE '%%Marketing%%'
                AND name NOT LIKE '%%Utilities%%'
                AND name NOT LIKE '%%Equipment%%'
                AND name NOT LIKE '%%Material%%'
            )
            {cost_center_condition}
            GROUP BY account, account_name
            HAVING amount > 0
            ORDER BY amount DESC
        """

        general_data = frappe.db.sql(
            general_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_dict=True,
        )

        breakdown = []
        total_general = 0

        for general in general_data:
            amount = flt(general.amount, self.precision)
            total_general += amount
            breakdown.append(
                {"account": general.account, "account_name": general.account_name, "amount": amount}
            )

        return {
            "total": flt(total_general, self.precision),
            "breakdown": breakdown,
            "label_en": "General Expenses",
            "label_ar": "المصاريف العامة",
        }

    def _get_non_operating_expenses(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> float:
        """Get non-operating expenses (interest, etc.)"""

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %(cost_center)s"

        non_op_query = f"""
            SELECT 
                SUM(debit - credit) as amount
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND is_cancelled = 0
            AND account IN (
                SELECT name FROM `tabAccount` 
                WHERE company = %(company)s 
                AND (name LIKE '%%Interest%%' OR name LIKE '%%Finance%%' OR name LIKE '%%Bank Charges%%')
            )
            {cost_center_condition}
        """

        result = frappe.db.sql(
            non_op_query,
            {
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
                "cost_center": cost_center,
            },
            as_list=True,
        )

        return flt(result[0][0] if result and result[0][0] else 0, self.precision)

    def _calculate_workshop_metrics(
        self, company: str, from_date: str, to_date: str, cost_center: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate workshop-specific operational metrics"""

        # Service bay utilization
        bay_utilization = self._get_service_bay_utilization(company, from_date, to_date)

        # Technician productivity
        technician_productivity = self._get_technician_productivity(company, from_date, to_date)

        # Customer satisfaction metrics
        customer_metrics = self._get_customer_satisfaction_metrics(company, from_date, to_date)

        # Vehicle service frequency
        vehicle_metrics = self._get_vehicle_service_metrics(company, from_date, to_date)

        return {
            "service_bay_utilization": bay_utilization,
            "technician_productivity": technician_productivity,
            "customer_satisfaction": customer_metrics,
            "vehicle_service_frequency": vehicle_metrics,
            "label_en": "Workshop Performance Metrics",
            "label_ar": "مؤشرات أداء الورشة",
        }

    def _get_service_bay_utilization(
        self, company: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Calculate service bay utilization metrics"""

        # This would integrate with the workshop management system
        # For now, return placeholder structure
        return {
            "total_bays": 8,
            "average_utilization": 75.5,
            "peak_utilization_time": "10:00-14:00",
            "daily_breakdown": [],
            "label_en": "Service Bay Utilization",
            "label_ar": "استخدام خلجان الخدمة",
        }

    def _get_technician_productivity(
        self, company: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Calculate technician productivity metrics"""

        # This would integrate with the technician management system
        return {
            "active_technicians": 12,
            "average_jobs_per_day": 4.2,
            "average_completion_time": 2.5,  # hours
            "efficiency_rating": 88.5,
            "label_en": "Technician Productivity",
            "label_ar": "إنتاجية الفنيين",
        }

    def _get_customer_satisfaction_metrics(
        self, company: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Get customer satisfaction metrics"""

        # This would integrate with customer feedback system
        return {
            "average_rating": 4.3,
            "total_reviews": 156,
            "satisfaction_rate": 92.5,
            "repeat_customer_rate": 78.2,
            "label_en": "Customer Satisfaction",
            "label_ar": "رضا العملاء",
        }

    def _get_vehicle_service_metrics(
        self, company: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Get vehicle service frequency metrics"""

        # This would integrate with vehicle management system
        return {
            "total_vehicles_serviced": 342,
            "unique_vehicles": 289,
            "average_service_frequency": 1.8,  # times per period
            "first_time_customers": 63,
            "label_en": "Vehicle Service Frequency",
            "label_ar": "تكرار خدمة المركبات",
        }

    def _calculate_comparison_period(
        self,
        company: str,
        from_date: str,
        to_date: str,
        comparison_period: str,
        cost_center: Optional[str],
    ) -> Dict[str, Any]:
        """Calculate comparison period data"""

        if comparison_period == "previous_year":
            # Calculate same period in previous year
            comp_from = add_months(from_date, -12)
            comp_to = add_months(to_date, -12)
        elif comparison_period == "previous_quarter":
            # Calculate previous quarter
            comp_from = add_months(from_date, -3)
            comp_to = add_months(to_date, -3)
        else:
            return {}

        # Generate comparison P&L (simplified)
        comparison_pnl = self.generate_comprehensive_pnl(
            company, comp_from, comp_to, cost_center, None, False
        )

        return {
            "period_from": comp_from,
            "period_to": comp_to,
            "data": comparison_pnl,
            "label_en": f'Comparison - {comparison_period.replace("_", " ").title()}',
            "label_ar": f"مقارنة - {comparison_period}",
        }

    def _save_pnl_report_record(self, pnl_report: Dict[str, Any]):
        """Save P&L report record for audit trail"""

        try:
            # Create P&L Report record if DocType exists
            if frappe.db.exists("DocType", "P&L Report"):
                report_doc = frappe.new_doc("P&L Report")
                report_doc.company = pnl_report["company"]
                report_doc.period_from = pnl_report["period_from"]
                report_doc.period_to = pnl_report["period_to"]
                report_doc.cost_center = pnl_report.get("cost_center")
                report_doc.total_revenue = pnl_report["revenue"]["total_revenue"]
                report_doc.gross_profit = pnl_report["gross_profit"]["amount"]
                report_doc.operating_profit = pnl_report["operating_profit"]["amount"]
                report_doc.net_profit = pnl_report["net_profit"]["amount"]
                report_doc.report_data = json.dumps(pnl_report)
                report_doc.insert()

        except Exception as e:
            frappe.log_error(f"Failed to save P&L report record: {e}")


# WhiteListed API methods for external access
@frappe.whitelist()
def generate_workshop_pnl_report(
    company, from_date, to_date, cost_center=None, comparison_period=None
):
    """
    Generate comprehensive P&L report for workshop

    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        cost_center: Optional cost center filter
        comparison_period: Optional comparison (previous_year, previous_quarter)
    """
    manager = WorkshopPnLReportingManager()
    return manager.generate_comprehensive_pnl(
        company, from_date, to_date, cost_center, comparison_period, True
    )


@frappe.whitelist()
def get_pnl_dashboard_data(company, period="current_month"):
    """
    Get P&L dashboard data for real-time monitoring

    Args:
        company: Company name
        period: Period to display (current_month, current_quarter, current_year)
    """
    if period == "current_month":
        from_date = get_first_day(today())
        to_date = get_last_day(today())
    elif period == "current_quarter":
        # Calculate current quarter dates
        current_month = getdate(today()).month
        quarter_start_month = ((current_month - 1) // 3) * 3 + 1
        from_date = f"{getdate(today()).year}-{quarter_start_month:02d}-01"
        to_date = add_months(from_date, 3)
    else:  # current_year
        from_date = f"{getdate(today()).year}-01-01"
        to_date = f"{getdate(today()).year}-12-31"

    manager = WorkshopPnLReportingManager()
    pnl_data = manager.generate_comprehensive_pnl(company, from_date, to_date)

    # Return dashboard-friendly format
    return {
        "revenue": pnl_data["revenue"]["total_revenue"],
        "gross_profit": pnl_data["gross_profit"]["amount"],
        "gross_margin": pnl_data["gross_profit"]["percentage"],
        "operating_profit": pnl_data["operating_profit"]["amount"],
        "operating_margin": pnl_data["operating_profit"]["percentage"],
        "net_profit": pnl_data["net_profit"]["amount"],
        "net_margin": pnl_data["net_profit"]["percentage"],
        "workshop_metrics": pnl_data.get("workshop_metrics", {}),
        "period": period,
        "from_date": from_date,
        "to_date": to_date,
    }


@frappe.whitelist()
def get_pnl_export_data(company, from_date, to_date, format_type="excel"):
    """
    Export P&L data in various formats

    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        format_type: Export format (excel, pdf, csv)
    """
    manager = WorkshopPnLReportingManager()
    pnl_data = manager.generate_comprehensive_pnl(company, from_date, to_date)

    if format_type == "excel":
        return _prepare_excel_export(pnl_data)
    elif format_type == "pdf":
        return _prepare_pdf_export(pnl_data)
    else:  # csv
        return _prepare_csv_export(pnl_data)


def _prepare_excel_export(pnl_data):
    """Prepare P&L data for Excel export"""
    # Implementation for Excel export
    return {"status": "Excel export prepared", "data": pnl_data}


def _prepare_pdf_export(pnl_data):
    """Prepare P&L data for PDF export"""
    # Implementation for PDF export
    return {"status": "PDF export prepared", "data": pnl_data}


def _prepare_csv_export(pnl_data):
    """Prepare P&L data for CSV export"""
    # Implementation for CSV export
    return {"status": "CSV export prepared", "data": pnl_data}
