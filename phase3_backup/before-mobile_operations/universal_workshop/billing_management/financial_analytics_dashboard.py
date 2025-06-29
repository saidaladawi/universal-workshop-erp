# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Financial Analytics Dashboard for Universal Workshop ERP
Provides comprehensive real-time analytics, KPI tracking, and customizable dashboards
Integrates all financial modules: receivables, payables, cash flow, P&L, VAT, budgets
"""

import frappe
from frappe import _
from frappe.utils import (
    flt,
    cint,
    getdate,
    nowdate,
    add_months,
    add_days,
    get_first_day,
    get_last_day,
    formatdate,
    fmt_money,
)
import json
from datetime import datetime, timedelta
from collections import defaultdict
import math


class FinancialAnalyticsDashboard:
    """
    Comprehensive Financial Analytics Dashboard for Universal Workshop ERP

    Features:
    - Real-time KPI tracking and monitoring
    - Customizable dashboard configurations
    - Multi-dimensional financial analysis
    - Arabic/English bilingual reporting for Oman market
    - Workshop-specific operational metrics integration
    - Automated alerts and threshold monitoring
    """

    def __init__(self, company=None, date_range=None):
        self.company = company or frappe.defaults.get_user_default("Company")
        self.currency = frappe.get_cached_value("Company", self.company, "default_currency")
        self.date_range = date_range or self._get_default_date_range()
        self.language = frappe.local.lang or "en"

    def _get_default_date_range(self):
        """Get default date range for analytics (current fiscal year)"""
        today = getdate()
        fiscal_year = frappe.get_cached_value("Company", self.company, "fiscal_year")
        if fiscal_year:
            fy = frappe.get_doc("Fiscal Year", fiscal_year)
            return {"from_date": fy.year_start_date, "to_date": fy.year_end_date}
        else:
            # Fallback to calendar year
            return {
                "from_date": getdate(f"{today.year}-01-01"),
                "to_date": getdate(f"{today.year}-12-31"),
            }

    def get_comprehensive_dashboard_data(self):
        """
        Generate comprehensive dashboard data combining all financial modules
        Returns real-time analytics suitable for executive dashboards
        """
        try:
            dashboard_data = {
                "overview": self._get_financial_overview(),
                "revenue_analytics": self._get_revenue_analytics(),
                "cash_flow_summary": self._get_cash_flow_summary(),
                "receivables_analytics": self._get_receivables_analytics(),
                "budget_performance": self._get_budget_performance(),
                "vat_compliance": self._get_vat_compliance_summary(),
                "operational_kpis": self._get_operational_kpis(),
                "alerts_notifications": self._get_dashboard_alerts(),
                "trending_analysis": self._get_trending_analysis(),
                "metadata": {
                    "company": self.company,
                    "currency": self.currency,
                    "date_range": self.date_range,
                    "generated_at": frappe.utils.now(),
                    "language": self.language,
                },
            }

            return dashboard_data

        except Exception as e:
            frappe.log_error(f"Dashboard data generation error: {str(e)}")
            return {"error": str(e)}

    def _get_financial_overview(self):
        """Generate high-level financial overview KPIs"""
        try:
            # Revenue metrics
            total_revenue = self._get_total_revenue()
            revenue_growth = self._calculate_revenue_growth()

            # Profitability metrics
            gross_profit = self._calculate_gross_profit()
            net_profit = self._calculate_net_profit()

            # Cash position
            current_cash = self._get_current_cash_balance()
            cash_flow_trend = self._get_cash_flow_trend()

            # Receivables summary
            total_receivables = self._get_total_receivables()
            overdue_receivables = self._get_overdue_receivables()

            return {
                "revenue": {
                    "total": flt(total_revenue, 2),
                    "growth_rate": flt(revenue_growth, 2),
                    "formatted": self._format_currency(total_revenue),
                },
                "profitability": {
                    "gross_profit": flt(gross_profit, 2),
                    "net_profit": flt(net_profit, 2),
                    "gross_margin": flt(
                        (gross_profit / total_revenue * 100) if total_revenue else 0, 2
                    ),
                    "net_margin": flt(
                        (net_profit / total_revenue * 100) if total_revenue else 0, 2
                    ),
                },
                "cash_position": {
                    "current_balance": flt(current_cash, 2),
                    "trend": cash_flow_trend,
                    "formatted": self._format_currency(current_cash),
                },
                "receivables": {
                    "total": flt(total_receivables, 2),
                    "overdue": flt(overdue_receivables, 2),
                    "collection_efficiency": flt(
                        (
                            (1 - overdue_receivables / total_receivables) * 100
                            if total_receivables
                            else 100
                        ),
                        2,
                    ),
                },
            }

        except Exception as e:
            frappe.log_error(f"Financial overview error: {str(e)}")
            return {}

    def _get_revenue_analytics(self):
        """Generate detailed revenue analytics with breakdown"""
        try:
            # Service revenue by category
            service_revenue = self._get_service_revenue_breakdown()

            # Parts revenue
            parts_revenue = self._get_parts_revenue_breakdown()

            # Monthly revenue trend
            monthly_trend = self._get_monthly_revenue_trend()

            # Top customers by revenue
            top_customers = self._get_top_customers_by_revenue()

            return {
                "service_revenue": service_revenue,
                "parts_revenue": parts_revenue,
                "monthly_trend": monthly_trend,
                "top_customers": top_customers,
                "total_breakdown": {
                    "services": sum([cat["amount"] for cat in service_revenue]),
                    "parts": sum([cat["amount"] for cat in parts_revenue]),
                },
            }

        except Exception as e:
            frappe.log_error(f"Revenue analytics error: {str(e)}")
            return {}

    def _get_cash_flow_summary(self):
        """Generate cash flow summary for dashboard"""
        try:
            # Operating cash flow
            operating_cf = self._calculate_operating_cash_flow()

            # Investing cash flow
            investing_cf = self._calculate_investing_cash_flow()

            # Financing cash flow
            financing_cf = self._calculate_financing_cash_flow()

            # Forecast next 30 days
            forecast_30d = self._forecast_cash_flow_30_days()

            return {
                "operating": flt(operating_cf, 2),
                "investing": flt(investing_cf, 2),
                "financing": flt(financing_cf, 2),
                "net_flow": flt(operating_cf + investing_cf + financing_cf, 2),
                "forecast_30d": forecast_30d,
                "liquidity_ratio": self._calculate_liquidity_ratio(),
            }

        except Exception as e:
            frappe.log_error(f"Cash flow summary error: {str(e)}")
            return {}

    def _get_receivables_analytics(self):
        """Generate receivables analytics for dashboard"""
        try:
            # Aging analysis
            aging_buckets = self._get_aging_analysis()

            # Collection performance
            collection_stats = self._get_collection_performance()

            # Payment behavior analysis
            payment_behavior = self._get_payment_behavior_analysis()

            return {
                "aging_analysis": aging_buckets,
                "collection_performance": collection_stats,
                "payment_behavior": payment_behavior,
                "dso": self._calculate_days_sales_outstanding(),
            }

        except Exception as e:
            frappe.log_error(f"Receivables analytics error: {str(e)}")
            return {}

    def _get_budget_performance(self):
        """Generate budget vs actual performance analytics"""
        try:
            # Overall budget performance
            budget_summary = self._get_budget_vs_actual_summary()

            # Cost center performance
            cost_center_performance = self._get_cost_center_budget_performance()

            # Budget utilization rates
            utilization_rates = self._calculate_budget_utilization_rates()

            return {
                "summary": budget_summary,
                "cost_centers": cost_center_performance,
                "utilization": utilization_rates,
                "variance_alerts": self._get_budget_variance_alerts(),
            }

        except Exception as e:
            frappe.log_error(f"Budget performance error: {str(e)}")
            return {}

    def _get_vat_compliance_summary(self):
        """Generate VAT compliance summary for dashboard"""
        try:
            # Current period VAT summary
            vat_summary = self._get_current_vat_summary()

            # Compliance status
            compliance_status = self._check_vat_compliance_status()

            return {
                "current_period": vat_summary,
                "compliance_status": compliance_status,
                "next_filing_date": self._get_next_vat_filing_date(),
            }

        except Exception as e:
            frappe.log_error(f"VAT compliance summary error: {str(e)}")
            return {}

    def _get_operational_kpis(self):
        """Generate workshop-specific operational KPIs"""
        try:
            # Service bay utilization
            bay_utilization = self._calculate_service_bay_utilization()

            # Technician productivity
            technician_productivity = self._calculate_technician_productivity()

            # Average service time
            avg_service_time = self._calculate_average_service_time()

            # Customer satisfaction metrics
            customer_satisfaction = self._get_customer_satisfaction_metrics()

            return {
                "bay_utilization": bay_utilization,
                "technician_productivity": technician_productivity,
                "avg_service_time": avg_service_time,
                "customer_satisfaction": customer_satisfaction,
                "revenue_per_technician": self._calculate_revenue_per_technician(),
            }

        except Exception as e:
            frappe.log_error(f"Operational KPIs error: {str(e)}")
            return {}

    def _get_dashboard_alerts(self):
        """Generate real-time alerts and notifications for dashboard"""
        alerts = []

        try:
            # Cash flow alerts
            cash_balance = self._get_current_cash_balance()
            if cash_balance < 10000:  # Configurable threshold
                alerts.append(
                    {
                        "type": "warning",
                        "category": "cash_flow",
                        "message": _("Low cash balance: {0}").format(
                            self._format_currency(cash_balance)
                        ),
                        "priority": "high",
                    }
                )

            # Overdue receivables alerts
            overdue_amount = self._get_overdue_receivables()
            if overdue_amount > 5000:  # Configurable threshold
                alerts.append(
                    {
                        "type": "warning",
                        "category": "receivables",
                        "message": _("High overdue receivables: {0}").format(
                            self._format_currency(overdue_amount)
                        ),
                        "priority": "medium",
                    }
                )

            # Budget variance alerts
            budget_variances = self._get_significant_budget_variances()
            for variance in budget_variances:
                alerts.append(
                    {
                        "type": "info",
                        "category": "budget",
                        "message": _("Budget variance in {0}: {1}%").format(
                            variance["account"], variance["variance_pct"]
                        ),
                        "priority": "low",
                    }
                )

            return alerts

        except Exception as e:
            frappe.log_error(f"Dashboard alerts error: {str(e)}")
            return []

    def _get_trending_analysis(self):
        """Generate trending analysis for key metrics"""
        try:
            return {
                "revenue_trend": self._analyze_revenue_trend(),
                "profit_trend": self._analyze_profit_trend(),
                "cash_flow_trend": self._analyze_cash_flow_trend(),
                "customer_growth_trend": self._analyze_customer_growth_trend(),
            }

        except Exception as e:
            frappe.log_error(f"Trending analysis error: {str(e)}")
            return {}

    # Helper methods for calculations
    def _get_total_revenue(self):
        """Calculate total revenue for the period"""
        result = frappe.db.sql(
            """
            SELECT SUM(base_grand_total)
            FROM `tabSales Invoice`
            WHERE company = %s
            AND posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """,
            [self.company, self.date_range["from_date"], self.date_range["to_date"]],
        )

        return flt(result[0][0]) if result and result[0][0] else 0

    def _calculate_revenue_growth(self):
        """Calculate revenue growth compared to previous period"""
        # Implementation for revenue growth calculation
        return 0  # Placeholder

    def _calculate_gross_profit(self):
        """Calculate gross profit"""
        # Implementation for gross profit calculation
        return 0  # Placeholder

    def _calculate_net_profit(self):
        """Calculate net profit"""
        # Implementation for net profit calculation
        return 0  # Placeholder

    def _get_current_cash_balance(self):
        """Get current cash balance"""
        result = frappe.db.sql(
            """
            SELECT SUM(account_balance)
            FROM `tabAccount Balance`
            WHERE company = %s
            AND account IN (
                SELECT name FROM `tabAccount`
                WHERE account_type = 'Cash'
                AND company = %s
            )
        """,
            [self.company, self.company],
        )

        return flt(result[0][0]) if result and result[0][0] else 0

    def _get_total_receivables(self):
        """Get total outstanding receivables"""
        result = frappe.db.sql(
            """
            SELECT SUM(outstanding_amount)
            FROM `tabSales Invoice`
            WHERE company = %s
            AND docstatus = 1
            AND outstanding_amount > 0
        """,
            [self.company],
        )

        return flt(result[0][0]) if result and result[0][0] else 0

    def _get_overdue_receivables(self):
        """Get overdue receivables amount"""
        result = frappe.db.sql(
            """
            SELECT SUM(outstanding_amount)
            FROM `tabSales Invoice`
            WHERE company = %s
            AND docstatus = 1
            AND outstanding_amount > 0
            AND due_date < %s
        """,
            [self.company, nowdate()],
        )

        return flt(result[0][0]) if result and result[0][0] else 0

    def _format_currency(self, amount):
        """Format currency amount with proper localization"""
        if self.language == "ar":
            # Arabic format: ر.ع. ١٢٣.٤٥٦
            arabic_amount = self._convert_to_arabic_numerals(f"{amount:,.3f}")
            return f"ر.ع. {arabic_amount}"
        else:
            # English format: OMR 123.456
            return f"{self.currency} {amount:,.3f}"

    def _convert_to_arabic_numerals(self, text):
        """Convert Western numerals to Arabic-Indic numerals"""
        arabic_numerals = {
            "0": "٠",
            "1": "١",
            "2": "٢",
            "3": "٣",
            "4": "٤",
            "5": "٥",
            "6": "٦",
            "7": "٧",
            "8": "٨",
            "9": "٩",
        }

        for western, arabic in arabic_numerals.items():
            text = text.replace(western, arabic)
        return text

    # Placeholder implementations for complex calculations
    def _get_service_revenue_breakdown(self):
        return []

    def _get_parts_revenue_breakdown(self):
        return []

    def _get_monthly_revenue_trend(self):
        return []

    def _get_top_customers_by_revenue(self):
        return []

    def _calculate_operating_cash_flow(self):
        return 0

    def _calculate_investing_cash_flow(self):
        return 0

    def _calculate_financing_cash_flow(self):
        return 0

    def _forecast_cash_flow_30_days(self):
        return []

    def _calculate_liquidity_ratio(self):
        return 0

    def _get_aging_analysis(self):
        return {}

    def _get_collection_performance(self):
        return {}

    def _get_payment_behavior_analysis(self):
        return {}

    def _calculate_days_sales_outstanding(self):
        return 0

    def _get_budget_vs_actual_summary(self):
        return {}

    def _get_cost_center_budget_performance(self):
        return []

    def _calculate_budget_utilization_rates(self):
        return {}

    def _get_budget_variance_alerts(self):
        return []

    def _get_current_vat_summary(self):
        return {}

    def _check_vat_compliance_status(self):
        return {"status": "compliant"}

    def _get_next_vat_filing_date(self):
        return add_months(nowdate(), 1)

    def _calculate_service_bay_utilization(self):
        return 0

    def _calculate_technician_productivity(self):
        return 0

    def _calculate_average_service_time(self):
        return 0

    def _get_customer_satisfaction_metrics(self):
        return {}

    def _calculate_revenue_per_technician(self):
        return 0

    def _get_cash_flow_trend(self):
        return "stable"

    def _get_significant_budget_variances(self):
        return []

    def _analyze_revenue_trend(self):
        return {"trend": "stable", "slope": 0}

    def _analyze_profit_trend(self):
        return {"trend": "stable", "slope": 0}

    def _analyze_cash_flow_trend(self):
        return {"trend": "stable", "slope": 0}

    def _analyze_customer_growth_trend(self):
        return {"trend": "stable", "slope": 0}


class DashboardCustomization:
    """
    Dashboard customization and configuration management
    Allows users to create personalized financial dashboards
    """

    def __init__(self, user=None):
        self.user = user or frappe.session.user

    def save_dashboard_config(self, config_name, config_data):
        """Save custom dashboard configuration"""
        try:
            # Check if configuration exists
            existing = frappe.db.exists(
                "Dashboard Configuration", {"user": self.user, "config_name": config_name}
            )

            if existing:
                config = frappe.get_doc("Dashboard Configuration", existing)
                config.config_data = json.dumps(config_data)
                config.save()
            else:
                config = frappe.new_doc("Dashboard Configuration")
                config.user = self.user
                config.config_name = config_name
                config.config_data = json.dumps(config_data)
                config.insert()

            return config.name

        except Exception as e:
            frappe.log_error(f"Dashboard config save error: {str(e)}")
            return None

    def load_dashboard_config(self, config_name):
        """Load custom dashboard configuration"""
        try:
            config = frappe.db.get_value(
                "Dashboard Configuration",
                {"user": self.user, "config_name": config_name},
                "config_data",
            )

            return json.loads(config) if config else None

        except Exception as e:
            frappe.log_error(f"Dashboard config load error: {str(e)}")
            return None

    def get_user_dashboard_configs(self):
        """Get all dashboard configurations for user"""
        try:
            configs = frappe.get_list(
                "Dashboard Configuration", {"user": self.user}, ["config_name", "modified"]
            )

            return configs

        except Exception as e:
            frappe.log_error(f"Dashboard configs list error: {str(e)}")
            return []


# WhiteListed API Methods
@frappe.whitelist()
def get_financial_dashboard_data(company=None, date_range=None):
    """
    API endpoint to get comprehensive financial dashboard data

    Args:
        company (str): Company name
        date_range (dict): Date range with from_date and to_date

    Returns:
        dict: Complete dashboard data with all financial analytics
    """
    try:
        if date_range and isinstance(date_range, str):
            date_range = json.loads(date_range)

        dashboard = FinancialAnalyticsDashboard(company=company, date_range=date_range)
        return dashboard.get_comprehensive_dashboard_data()

    except Exception as e:
        frappe.log_error(f"Financial dashboard API error: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def save_dashboard_configuration(config_name, config_data):
    """
    Save custom dashboard configuration for current user

    Args:
        config_name (str): Name of the configuration
        config_data (str): JSON string of configuration data

    Returns:
        dict: Success/error response
    """
    try:
        if isinstance(config_data, str):
            config_data = json.loads(config_data)

        customization = DashboardCustomization()
        config_id = customization.save_dashboard_config(config_name, config_data)

        return {
            "success": True,
            "config_id": config_id,
            "message": _("Dashboard configuration saved successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Dashboard config save API error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_dashboard_kpi_summary(company=None):
    """
    Get high-level KPI summary for quick dashboard overview
    Optimized for real-time display with minimal data

    Args:
        company (str): Company name

    Returns:
        dict: Essential KPIs for dashboard header/summary
    """
    try:
        dashboard = FinancialAnalyticsDashboard(company=company)
        overview = dashboard._get_financial_overview()
        operational = dashboard._get_operational_kpis()

        return {
            "revenue": overview.get("revenue", {}),
            "cash_position": overview.get("cash_position", {}),
            "receivables": overview.get("receivables", {}),
            "profitability": overview.get("profitability", {}),
            "bay_utilization": operational.get("bay_utilization", 0),
            "last_updated": frappe.utils.now(),
        }

    except Exception as e:
        frappe.log_error(f"KPI summary API error: {str(e)}")
        return {"error": str(e)}
