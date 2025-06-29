# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months, today, get_first_day, get_last_day, format_date
from datetime import datetime, timedelta
import json
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from .budget_planning import BudgetPlanningManager


class CostCenterAnalysisManager:
    """
    Advanced Cost Center Analysis Manager for Universal Workshop ERP
    Provides comprehensive departmental and project-based financial analysis
    """

    def __init__(self, company=None):
        self.company = company or frappe.defaults.get_global_default("company")
        self.budget_manager = BudgetPlanningManager()

        # Workshop department mapping
        self.department_mapping = {
            "Service Operations": {
                "name_ar": "عمليات الخدمة",
                "profit_centers": ["Service Bay 1", "Service Bay 2", "Diagnostic Center"],
                "revenue_accounts": ["Service Revenue", "Labor Charges"],
                "cost_accounts": ["Direct Labor", "Workshop Consumables", "Equipment Depreciation"],
            },
            "Parts Inventory": {
                "name_ar": "مخزون قطع الغيار",
                "profit_centers": ["Parts Warehouse", "Parts Counter", "Emergency Stock"],
                "revenue_accounts": ["Parts Sales", "Markup Revenue"],
                "cost_accounts": ["Cost of Goods Sold", "Inventory Shrinkage", "Storage Costs"],
            },
            "Customer Service": {
                "name_ar": "خدمة العملاء",
                "profit_centers": ["Reception", "Customer Relations", "Quality Assurance"],
                "revenue_accounts": ["Service Fees", "Extended Warranty"],
                "cost_accounts": [
                    "Customer Service Salaries",
                    "Communication Costs",
                    "Training Expenses",
                ],
            },
            "Administration": {
                "name_ar": "الإدارة",
                "profit_centers": ["Finance", "HR", "IT Support"],
                "revenue_accounts": [],  # Overhead department
                "cost_accounts": [
                    "Administrative Salaries",
                    "Office Expenses",
                    "Professional Fees",
                ],
            },
        }

    def generate_comprehensive_cost_center_report(
        self, from_date, to_date, cost_center=None, language="en"
    ):
        """
        Generate comprehensive cost center analysis report

        Args:
            from_date (str): Start date for analysis
            to_date (str): End date for analysis
            cost_center (str, optional): Specific cost center to analyze
            language (str): Report language ('en' or 'ar')

        Returns:
            dict: Comprehensive cost center analysis
        """
        try:
            from_date = getdate(from_date)
            to_date = getdate(to_date)

            # Get cost center performance data
            performance_data = self._get_cost_center_performance(from_date, to_date, cost_center)

            # Calculate departmental profitability
            departmental_analysis = self._analyze_departmental_profitability(from_date, to_date)

            # Get cost allocation analysis
            cost_allocation = self._analyze_cost_allocation(from_date, to_date)

            # Calculate efficiency metrics
            efficiency_metrics = self._calculate_efficiency_metrics(from_date, to_date)

            # Generate trending analysis
            trending_analysis = self._generate_trending_analysis(from_date, to_date)

            # Prepare report structure
            report_data = {
                "company": self.company,
                "period": {
                    "from_date": from_date.strftime("%Y-%m-%d"),
                    "to_date": to_date.strftime("%Y-%m-%d"),
                    "days": (to_date - from_date).days + 1,
                },
                "performance_summary": performance_data,
                "departmental_analysis": departmental_analysis,
                "cost_allocation": cost_allocation,
                "efficiency_metrics": efficiency_metrics,
                "trending_analysis": trending_analysis,
                "variance_analysis": self._calculate_variance_analysis(from_date, to_date),
                "generated_at": datetime.now().isoformat(),
                "language": language,
            }

            # Add Arabic translations if needed
            if language == "ar":
                report_data = self._add_arabic_translations(report_data)

            # Calculate insights and recommendations
            report_data["insights"] = self._generate_insights(report_data)

            return report_data

        except Exception as e:
            frappe.log_error(f"Cost Center Analysis Error: {str(e)}")
            frappe.throw(_("Error generating cost center analysis: {0}").format(str(e)))

    def _get_cost_center_performance(self, from_date, to_date, cost_center=None):
        """Get detailed cost center performance data"""

        # Base query for cost center transactions
        conditions = ["gle.posting_date BETWEEN %s AND %s", "gle.company = %s"]
        values = [from_date, to_date, self.company]

        if cost_center:
            conditions.append("gle.cost_center = %s")
            values.append(cost_center)

        # Get all general ledger entries with cost center allocation
        gl_entries = frappe.db.sql(
            f"""
            SELECT 
                gle.cost_center,
                cc.cost_center_name,
                gle.account,
                acc.account_name,
                acc.account_type,
                SUM(gle.debit) as total_debit,
                SUM(gle.credit) as total_credit,
                SUM(gle.debit - gle.credit) as net_amount,
                COUNT(*) as transaction_count
            FROM `tabGL Entry` gle
            LEFT JOIN `tabCost Center` cc ON cc.name = gle.cost_center
            LEFT JOIN `tabAccount` acc ON acc.name = gle.account
            WHERE {' AND '.join(conditions)}
                AND gle.is_cancelled = 0
                AND gle.cost_center IS NOT NULL
            GROUP BY gle.cost_center, gle.account
            ORDER BY cc.cost_center_name, acc.account_name
        """,
            values,
            as_dict=True,
        )

        # Organize data by cost center
        cost_center_data = defaultdict(
            lambda: {"revenue": 0, "expenses": 0, "profit": 0, "transactions": 0, "accounts": []}
        )

        for entry in gl_entries:
            cc_name = entry.cost_center
            account_type = entry.account_type or "Other"

            cost_center_data[cc_name]["transactions"] += entry.transaction_count
            cost_center_data[cc_name]["accounts"].append(
                {
                    "account": entry.account,
                    "account_name": entry.account_name,
                    "account_type": account_type,
                    "debit": flt(entry.total_debit, 3),
                    "credit": flt(entry.total_credit, 3),
                    "net_amount": flt(entry.net_amount, 3),
                }
            )

            # Categorize as revenue or expense
            if account_type in ["Income Account", "Income"]:
                cost_center_data[cc_name]["revenue"] += flt(entry.total_credit, 3)
            elif account_type in ["Expense Account", "Expense"]:
                cost_center_data[cc_name]["expenses"] += flt(entry.total_debit, 3)

        # Calculate profit for each cost center
        for cc_name in cost_center_data:
            cc_data = cost_center_data[cc_name]
            cc_data["profit"] = cc_data["revenue"] - cc_data["expenses"]
            cc_data["profit_margin"] = (
                (cc_data["profit"] / cc_data["revenue"] * 100) if cc_data["revenue"] > 0 else 0
            )

        return dict(cost_center_data)

    def _analyze_departmental_profitability(self, from_date, to_date):
        """Analyze profitability by workshop departments"""
        departmental_data = {}

        for dept_name, dept_info in self.department_mapping.items():
            dept_analysis = {
                "department": dept_name,
                "department_ar": dept_info["name_ar"],
                "total_revenue": 0,
                "total_expenses": 0,
                "net_profit": 0,
                "profit_centers": [],
            }

            # Analyze each profit center in the department
            for profit_center in dept_info["profit_centers"]:
                if frappe.db.exists("Cost Center", profit_center):
                    # Get revenue data
                    revenue = self._get_cost_center_revenue(profit_center, from_date, to_date)

                    # Get expense data
                    expenses = self._get_cost_center_expenses(profit_center, from_date, to_date)

                    # Calculate metrics
                    net_profit = revenue - expenses
                    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0

                    profit_center_data = {
                        "name": profit_center,
                        "revenue": flt(revenue, 3),
                        "expenses": flt(expenses, 3),
                        "net_profit": flt(net_profit, 3),
                        "profit_margin": flt(profit_margin, 2),
                        "efficiency_ratio": flt((revenue / expenses) if expenses > 0 else 0, 2),
                    }

                    dept_analysis["profit_centers"].append(profit_center_data)
                    dept_analysis["total_revenue"] += revenue
                    dept_analysis["total_expenses"] += expenses

            # Calculate department totals
            dept_analysis["net_profit"] = (
                dept_analysis["total_revenue"] - dept_analysis["total_expenses"]
            )
            dept_analysis["profit_margin"] = (
                (dept_analysis["net_profit"] / dept_analysis["total_revenue"] * 100)
                if dept_analysis["total_revenue"] > 0
                else 0
            )
            dept_analysis["roi"] = (
                (dept_analysis["net_profit"] / dept_analysis["total_expenses"] * 100)
                if dept_analysis["total_expenses"] > 0
                else 0
            )

            departmental_data[dept_name] = dept_analysis

        return departmental_data

    def _get_cost_center_revenue(self, cost_center, from_date, to_date):
        """Get revenue for a specific cost center"""
        revenue = (
            frappe.db.sql(
                """
            SELECT SUM(credit) as total_revenue
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON acc.name = gle.account
            WHERE gle.cost_center = %s
                AND gle.posting_date BETWEEN %s AND %s
                AND acc.account_type IN ('Income Account', 'Income')
                AND gle.is_cancelled = 0
        """,
                [cost_center, from_date, to_date],
            )[0][0]
            or 0
        )

        return flt(revenue, 3)

    def _get_cost_center_expenses(self, cost_center, from_date, to_date):
        """Get expenses for a specific cost center"""
        expenses = (
            frappe.db.sql(
                """
            SELECT SUM(debit) as total_expenses
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON acc.name = gle.account
            WHERE gle.cost_center = %s
                AND gle.posting_date BETWEEN %s AND %s
                AND acc.account_type IN ('Expense Account', 'Expense')
                AND gle.is_cancelled = 0
        """,
                [cost_center, from_date, to_date],
            )[0][0]
            or 0
        )

        return flt(expenses, 3)

    def _analyze_cost_allocation(self, from_date, to_date):
        """Analyze cost allocation across departments"""

        # Get shared costs that need allocation
        shared_costs = frappe.db.sql(
            """
            SELECT 
                gle.account,
                acc.account_name,
                SUM(gle.debit) as total_amount
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON acc.name = gle.account
            WHERE gle.posting_date BETWEEN %s AND %s
                AND gle.company = %s
                AND gle.cost_center IS NULL
                AND acc.account_type = 'Expense Account'
                AND gle.is_cancelled = 0
            GROUP BY gle.account
            ORDER BY total_amount DESC
        """,
            [from_date, to_date, self.company],
            as_dict=True,
        )

        # Calculate allocation percentages based on revenue
        department_revenues = {}
        total_revenue = 0

        for dept_name in self.department_mapping.keys():
            dept_revenue = 0
            for profit_center in self.department_mapping[dept_name]["profit_centers"]:
                if frappe.db.exists("Cost Center", profit_center):
                    dept_revenue += self._get_cost_center_revenue(profit_center, from_date, to_date)

            department_revenues[dept_name] = dept_revenue
            total_revenue += dept_revenue

        # Calculate allocation percentages
        allocation_percentages = {}
        for dept_name, revenue in department_revenues.items():
            allocation_percentages[dept_name] = (
                (revenue / total_revenue * 100) if total_revenue > 0 else 0
            )

        # Allocate shared costs
        allocated_costs = {}
        for dept_name in self.department_mapping.keys():
            allocated_costs[dept_name] = []
            allocation_pct = allocation_percentages[dept_name] / 100

            for cost in shared_costs:
                allocated_amount = flt(cost.total_amount * allocation_pct, 3)
                allocated_costs[dept_name].append(
                    {
                        "account": cost.account,
                        "account_name": cost.account_name,
                        "total_amount": flt(cost.total_amount, 3),
                        "allocated_amount": allocated_amount,
                        "allocation_percentage": allocation_percentages[dept_name],
                    }
                )

        return {
            "shared_costs": shared_costs,
            "allocation_percentages": allocation_percentages,
            "allocated_costs": allocated_costs,
            "total_shared_amount": sum([flt(cost.total_amount, 3) for cost in shared_costs]),
        }

    def _calculate_efficiency_metrics(self, from_date, to_date):
        """Calculate efficiency metrics for each department"""
        efficiency_metrics = {}

        for dept_name, dept_info in self.department_mapping.items():
            dept_metrics = {
                "department": dept_name,
                "department_ar": dept_info["name_ar"],
                "revenue_per_transaction": 0,
                "cost_per_transaction": 0,
                "asset_turnover": 0,
                "productivity_index": 0,
                "efficiency_trend": "stable",
            }

            # Calculate total department metrics
            total_revenue = 0
            total_expenses = 0
            total_transactions = 0

            for profit_center in dept_info["profit_centers"]:
                if frappe.db.exists("Cost Center", profit_center):
                    revenue = self._get_cost_center_revenue(profit_center, from_date, to_date)
                    expenses = self._get_cost_center_expenses(profit_center, from_date, to_date)

                    # Count transactions for this cost center
                    transactions = (
                        frappe.db.sql(
                            """
                        SELECT COUNT(*) as count
                        FROM `tabGL Entry`
                        WHERE cost_center = %s
                            AND posting_date BETWEEN %s AND %s
                            AND is_cancelled = 0
                    """,
                            [profit_center, from_date, to_date],
                        )[0][0]
                        or 0
                    )

                    total_revenue += revenue
                    total_expenses += expenses
                    total_transactions += transactions

            # Calculate efficiency metrics
            if total_transactions > 0:
                dept_metrics["revenue_per_transaction"] = flt(total_revenue / total_transactions, 3)
                dept_metrics["cost_per_transaction"] = flt(total_expenses / total_transactions, 3)

            if total_expenses > 0:
                dept_metrics["productivity_index"] = flt(total_revenue / total_expenses, 2)

            # Calculate asset turnover (simplified)
            dept_assets = self._get_department_assets(dept_name)
            if dept_assets > 0:
                dept_metrics["asset_turnover"] = flt(total_revenue / dept_assets, 2)

            # Determine efficiency trend (compared to previous period)
            prev_period_start = add_months(from_date, -1)
            prev_period_end = add_months(to_date, -1)
            prev_productivity = self._get_previous_productivity(
                dept_name, prev_period_start, prev_period_end
            )

            if dept_metrics["productivity_index"] > prev_productivity * 1.05:
                dept_metrics["efficiency_trend"] = "improving"
            elif dept_metrics["productivity_index"] < prev_productivity * 0.95:
                dept_metrics["efficiency_trend"] = "declining"

            efficiency_metrics[dept_name] = dept_metrics

        return efficiency_metrics

    def _get_department_assets(self, department):
        """Get assets allocated to a department (simplified calculation)"""
        # This is a simplified calculation - in practice, you'd have asset allocation logic
        asset_mapping = {
            "Service Operations": 150000,  # OMR - Service equipment and tools
            "Parts Inventory": 200000,  # OMR - Inventory value
            "Customer Service": 25000,  # OMR - Office equipment
            "Administration": 50000,  # OMR - IT equipment and furniture
        }

        return asset_mapping.get(department, 0)

    def _get_previous_productivity(self, department, from_date, to_date):
        """Get productivity index for previous period"""
        total_revenue = 0
        total_expenses = 0

        dept_info = self.department_mapping.get(department, {})
        for profit_center in dept_info.get("profit_centers", []):
            if frappe.db.exists("Cost Center", profit_center):
                revenue = self._get_cost_center_revenue(profit_center, from_date, to_date)
                expenses = self._get_cost_center_expenses(profit_center, from_date, to_date)

                total_revenue += revenue
                total_expenses += expenses

        return flt(total_revenue / total_expenses, 2) if total_expenses > 0 else 0

    def _generate_trending_analysis(self, from_date, to_date):
        """Generate trending analysis for the period"""

        # Calculate monthly trends
        monthly_trends = {}
        current_date = from_date

        while current_date <= to_date:
            month_start = get_first_day(current_date)
            month_end = get_last_day(current_date)

            # Ensure we don't go beyond the requested end date
            if month_end > to_date:
                month_end = to_date

            month_key = current_date.strftime("%Y-%m")
            monthly_data = {
                "period": month_key,
                "month_name": format_date(current_date, "MMMM yyyy"),
                "departments": {},
            }

            for dept_name in self.department_mapping.keys():
                dept_revenue = 0
                dept_expenses = 0

                for profit_center in self.department_mapping[dept_name]["profit_centers"]:
                    if frappe.db.exists("Cost Center", profit_center):
                        revenue = self._get_cost_center_revenue(
                            profit_center, month_start, month_end
                        )
                        expenses = self._get_cost_center_expenses(
                            profit_center, month_start, month_end
                        )

                        dept_revenue += revenue
                        dept_expenses += expenses

                monthly_data["departments"][dept_name] = {
                    "revenue": flt(dept_revenue, 3),
                    "expenses": flt(dept_expenses, 3),
                    "profit": flt(dept_revenue - dept_expenses, 3),
                    "profit_margin": (
                        flt((dept_revenue - dept_expenses) / dept_revenue * 100, 2)
                        if dept_revenue > 0
                        else 0
                    ),
                }

            monthly_trends[month_key] = monthly_data
            current_date = add_months(current_date, 1)

        return monthly_trends

    def _calculate_variance_analysis(self, from_date, to_date):
        """Calculate budget vs actual variance analysis"""
        variance_data = {}

        for dept_name in self.department_mapping.keys():
            # Get actual performance
            actual_revenue = 0
            actual_expenses = 0

            for profit_center in self.department_mapping[dept_name]["profit_centers"]:
                if frappe.db.exists("Cost Center", profit_center):
                    revenue = self._get_cost_center_revenue(profit_center, from_date, to_date)
                    expenses = self._get_cost_center_expenses(profit_center, from_date, to_date)

                    actual_revenue += revenue
                    actual_expenses += expenses

            # Get budget data (if exists)
            budget_revenue = self._get_budget_amount(dept_name, from_date, to_date, "Income")
            budget_expenses = self._get_budget_amount(dept_name, from_date, to_date, "Expense")

            # Calculate variances
            revenue_variance = actual_revenue - budget_revenue
            expense_variance = actual_expenses - budget_expenses

            variance_data[dept_name] = {
                "department": dept_name,
                "budget_revenue": flt(budget_revenue, 3),
                "actual_revenue": flt(actual_revenue, 3),
                "revenue_variance": flt(revenue_variance, 3),
                "revenue_variance_pct": flt(
                    (revenue_variance / budget_revenue * 100) if budget_revenue > 0 else 0, 2
                ),
                "budget_expenses": flt(budget_expenses, 3),
                "actual_expenses": flt(actual_expenses, 3),
                "expense_variance": flt(expense_variance, 3),
                "expense_variance_pct": flt(
                    (expense_variance / budget_expenses * 100) if budget_expenses > 0 else 0, 2
                ),
            }

        return variance_data

    def _get_budget_amount(self, department, from_date, to_date, account_type):
        """Get budget amount for department and period"""
        # This would integrate with ERPNext's budget system
        # For now, return 0 as placeholder
        return 0

    def _add_arabic_translations(self, report_data):
        """Add Arabic translations to report data"""
        arabic_translations = {
            "Cost Center Analysis": "تحليل مراكز التكلفة",
            "Department": "القسم",
            "Revenue": "الإيرادات",
            "Expenses": "المصروفات",
            "Profit": "الربح",
            "Profit Margin": "هامش الربح",
            "Efficiency": "الكفاءة",
            "Performance": "الأداء",
            "Budget vs Actual": "الميزانية مقابل الفعلي",
            "Variance": "الانحراف",
            "Trending Analysis": "تحليل الاتجاهات",
            "Service Operations": "عمليات الخدمة",
            "Parts Inventory": "مخزون قطع الغيار",
            "Customer Service": "خدمة العملاء",
            "Administration": "الإدارة",
        }

        report_data["arabic_labels"] = arabic_translations
        return report_data

    def _generate_insights(self, report_data):
        """Generate business insights and recommendations"""
        insights = []

        # Analyze departmental performance
        dept_analysis = report_data.get("departmental_analysis", {})

        # Find best and worst performing departments
        profit_margins = {}
        for dept_name, dept_data in dept_analysis.items():
            profit_margins[dept_name] = dept_data.get("profit_margin", 0)

        if profit_margins:
            best_dept = max(profit_margins, key=profit_margins.get)
            worst_dept = min(profit_margins, key=profit_margins.get)

            insights.append(
                {
                    "type": "performance",
                    "priority": "high",
                    "title": f"Best Performing Department: {best_dept}",
                    "description": f"Profit margin: {profit_margins[best_dept]:.1f}%",
                    "recommendation": f"Consider applying {best_dept} practices to other departments",
                }
            )

            if profit_margins[worst_dept] < 0:
                insights.append(
                    {
                        "type": "alert",
                        "priority": "urgent",
                        "title": f"Department at Loss: {worst_dept}",
                        "description": f"Negative profit margin: {profit_margins[worst_dept]:.1f}%",
                        "recommendation": "Immediate cost review and optimization required",
                    }
                )

        # Analyze efficiency trends
        efficiency_data = report_data.get("efficiency_metrics", {})
        declining_depts = [
            dept
            for dept, data in efficiency_data.items()
            if data.get("efficiency_trend") == "declining"
        ]

        if declining_depts:
            insights.append(
                {
                    "type": "warning",
                    "priority": "medium",
                    "title": "Declining Efficiency Detected",
                    "description": f"Departments with declining efficiency: {', '.join(declining_depts)}",
                    "recommendation": "Review operational processes and identify improvement opportunities",
                }
            )

        return insights


# WhiteListed API Methods for Cost Center Analysis


@frappe.whitelist()
def generate_cost_center_analysis_report(from_date, to_date, cost_center=None, language="en"):
    """
    Generate comprehensive cost center analysis report

    Args:
        from_date (str): Start date for analysis
        to_date (str): End date for analysis
        cost_center (str, optional): Specific cost center to analyze
        language (str): Report language ('en' or 'ar')

    Returns:
        dict: Comprehensive cost center analysis report
    """
    manager = CostCenterAnalysisManager()
    return manager.generate_comprehensive_cost_center_report(
        from_date, to_date, cost_center, language
    )


@frappe.whitelist()
def get_departmental_profitability_analysis(from_date, to_date):
    """
    Get departmental profitability analysis

    Args:
        from_date (str): Start date
        to_date (str): End date

    Returns:
        dict: Departmental profitability data
    """
    manager = CostCenterAnalysisManager()
    return manager._analyze_departmental_profitability(getdate(from_date), getdate(to_date))


@frappe.whitelist()
def get_cost_center_efficiency_metrics(from_date, to_date):
    """
    Get cost center efficiency metrics

    Args:
        from_date (str): Start date
        to_date (str): End date

    Returns:
        dict: Efficiency metrics for all departments
    """
    manager = CostCenterAnalysisManager()
    return manager._calculate_efficiency_metrics(getdate(from_date), getdate(to_date))


@frappe.whitelist()
def get_cost_allocation_analysis(from_date, to_date):
    """
    Get cost allocation analysis across departments

    Args:
        from_date (str): Start date
        to_date (str): End date

    Returns:
        dict: Cost allocation analysis with shared cost distribution
    """
    manager = CostCenterAnalysisManager()
    return manager._analyze_cost_allocation(getdate(from_date), getdate(to_date))


@frappe.whitelist()
def get_cost_center_dashboard_data(period="current_month"):
    """
    Get cost center dashboard data for quick overview

    Args:
        period (str): Analysis period ('current_month', 'current_quarter', 'current_year')

    Returns:
        dict: Dashboard data with key metrics and alerts
    """
    manager = CostCenterAnalysisManager()

    # Define date ranges based on period
    if period == "current_month":
        from_date = get_first_day(today())
        to_date = get_last_day(today())
    elif period == "current_quarter":
        from_date = get_first_day(today())
        # Get start of quarter
        month = getdate(today()).month
        quarter_start_month = ((month - 1) // 3) * 3 + 1
        from_date = getdate(f"{getdate(today()).year}-{quarter_start_month:02d}-01")
        to_date = getdate(today())
    else:  # current_year
        from_date = getdate(f"{getdate(today()).year}-01-01")
        to_date = getdate(today())

    # Get analysis data
    analysis_data = manager.generate_comprehensive_cost_center_report(
        from_date, to_date, language="en"
    )

    # Extract key dashboard metrics
    dashboard_data = {
        "period": {
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d"),
            "period_name": period.replace("_", " ").title(),
        },
        "summary": {
            "total_departments": len(analysis_data.get("departmental_analysis", {})),
            "profitable_departments": sum(
                1
                for dept in analysis_data.get("departmental_analysis", {}).values()
                if dept.get("net_profit", 0) > 0
            ),
            "total_revenue": sum(
                dept.get("total_revenue", 0)
                for dept in analysis_data.get("departmental_analysis", {}).values()
            ),
            "total_expenses": sum(
                dept.get("total_expenses", 0)
                for dept in analysis_data.get("departmental_analysis", {}).values()
            ),
            "overall_profit_margin": 0,
        },
        "top_performers": [],
        "alerts": analysis_data.get("insights", []),
        "efficiency_summary": analysis_data.get("efficiency_metrics", {}),
        "last_updated": datetime.now().isoformat(),
    }

    # Calculate overall profit margin
    if dashboard_data["summary"]["total_revenue"] > 0:
        net_profit = (
            dashboard_data["summary"]["total_revenue"] - dashboard_data["summary"]["total_expenses"]
        )
        dashboard_data["summary"]["overall_profit_margin"] = flt(
            (net_profit / dashboard_data["summary"]["total_revenue"] * 100), 2
        )

    # Get top performing departments
    dept_analysis = analysis_data.get("departmental_analysis", {})
    sorted_depts = sorted(
        dept_analysis.items(), key=lambda x: x[1].get("profit_margin", 0), reverse=True
    )
    dashboard_data["top_performers"] = [
        {
            "department": dept_name,
            "profit_margin": dept_data.get("profit_margin", 0),
            "net_profit": dept_data.get("net_profit", 0),
        }
        for dept_name, dept_data in sorted_depts[:3]
    ]

    return dashboard_data
