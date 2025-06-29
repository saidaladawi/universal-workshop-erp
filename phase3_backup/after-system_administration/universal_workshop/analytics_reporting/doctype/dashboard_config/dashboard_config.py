# pylint: disable=no-member
"""Dashboard Config DocType Controller

This module provides dashboard configuration management for the Universal Workshop
ERP analytics dashboard system.
"""

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DashboardConfig(Document):
    """Controller for Dashboard Config DocType"""

    def validate(self):
        """Validate dashboard configuration before saving"""
        self.validate_dashboard_name()
        self.validate_widgets()
        self.ensure_unique_default()

    def before_save(self):
        """Set metadata before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        self.last_updated_by = frappe.session.user

    def validate_dashboard_name(self):
        """Validate dashboard name format"""
        if not self.dashboard_name:
            frappe.throw(_("Dashboard Name is required"))

        # Ensure lowercase and underscore format
        if not self.dashboard_name.replace("_", "").replace("-", "").isalnum():
            frappe.throw(
                _(
                    "Dashboard Name must contain only alphanumeric characters, underscores, and hyphens"
                )
            )

    def validate_widgets(self):
        """Validate widget configuration"""
        if not self.widgets:
            frappe.throw(_("At least one widget is required"))

        widget_ids = []
        for widget in self.widgets:
            # Check for duplicate widget IDs
            if widget.widget_id in widget_ids:
                frappe.throw(_("Duplicate widget ID: {0}").format(widget.widget_id))
            widget_ids.append(widget.widget_id)

            # Validate widget configuration
            if widget.data_source == "KPI" and not widget.kpi_code:
                frappe.throw(
                    _("KPI Code is required for KPI widgets: {0}").format(widget.widget_title)
                )

            if widget.widget_type == "Chart" and not widget.chart_type:
                frappe.throw(
                    _("Chart Type is required for Chart widgets: {0}").format(widget.widget_title)
                )

    def ensure_unique_default(self):
        """Ensure only one default dashboard per role"""
        if self.is_default and self.target_role:
            # Remove default flag from other dashboards for the same role
            existing_defaults = frappe.get_list(
                "Dashboard Config",
                filters={
                    "target_role": self.target_role,
                    "is_default": 1,
                    "name": ["!=", self.name],
                },
            )

            for default_dashboard in existing_defaults:
                dashboard = frappe.get_doc("Dashboard Config", default_dashboard.name)
                dashboard.is_default = 0
                dashboard.save()

    def get_dashboard_data(self, date_range=None):
        """Get complete dashboard data for rendering"""

        dashboard_data = {
            "config": {
                "dashboard_name": self.dashboard_name,
                "dashboard_title": self.dashboard_title,
                "dashboard_title_ar": self.dashboard_title_ar,
                "dashboard_type": self.dashboard_type,
                "grid_columns": cint(self.grid_columns),
                "refresh_interval": cint(self.refresh_interval),
                "auto_refresh": self.auto_refresh,
                "enable_filtering": self.enable_filtering,
                "default_date_range": self.default_date_range,
            },
            "widgets": [],
        }

        # Process each widget
        for widget in self.widgets:
            if not widget.is_visible:
                continue

            widget_data = self._get_widget_data(widget, date_range)
            dashboard_data["widgets"].append(widget_data)

        return dashboard_data

    def _get_widget_data(self, widget, date_range=None):
        """Get data for a specific widget"""

        widget_config = {
            "widget_id": widget.widget_id,
            "widget_title": widget.widget_title,
            "widget_title_ar": widget.widget_title_ar,
            "widget_type": widget.widget_type,
            "widget_size": widget.widget_size,
            "position_order": widget.position_order,
            "chart_type": widget.chart_type,
            "show_target": widget.show_target,
            "show_trend": widget.show_trend,
            "color_scheme": widget.color_scheme,
        }

        # Get widget data based on data source
        if widget.data_source == "KPI" and widget.kpi_code:
            kpi_data = self._get_kpi_widget_data(widget.kpi_code, widget, date_range)
            widget_config.update(kpi_data)
        elif widget.data_source == "Custom Query":
            # Handle custom queries if implemented
            widget_config["data"] = {"error": "Custom queries not yet implemented"}
        else:
            widget_config["data"] = {"value": 0, "trend": "stable"}

        return widget_config

    def _get_kpi_widget_data(self, kpi_code, widget, date_range=None):
        """Get KPI data for widget"""
        try:
            # Get KPI current value
            kpi = frappe.get_doc("Analytics KPI", kpi_code)

            # Get historical data for trends
            from universal_workshop.analytics_reporting.doctype.analytics_kpi_history.analytics_kpi_history import (
                get_kpi_trend_analysis,
            )

            trend_data = get_kpi_trend_analysis(
                kpi_code, widget.aggregation_period, widget.limit_records
            )

            # Format data based on widget type
            if widget.widget_type == "KPI Card":
                return {
                    "data": {
                        "current_value": kpi.current_value,
                        "target_value": kpi.target_value,
                        "percentage_change": kpi.percentage_change,
                        "trend_direction": kpi.trend_direction,
                        "status": kpi.status,
                        "last_updated": kpi.last_calculated,
                    }
                }
            elif widget.widget_type == "Chart":
                return {
                    "data": {
                        "chart_data": self._format_chart_data(trend_data, widget.chart_type),
                        "current_value": kpi.current_value,
                        "target_value": kpi.target_value,
                    }
                }
            elif widget.widget_type == "Gauge":
                return {
                    "data": {
                        "current_value": kpi.current_value,
                        "target_value": kpi.target_value,
                        "min_value": 0,
                        "max_value": kpi.target_value * 1.5 if kpi.target_value else 100,
                    }
                }
            else:
                return {"data": {"current_value": kpi.current_value}}

        except Exception as e:
            frappe.log_error(
                f"Error getting KPI widget data for {kpi_code}: {str(e)}", "Widget Data Error"
            )
            return {"data": {"error": str(e)}}

    def _format_chart_data(self, trend_data, chart_type):
        """Format trend data for different chart types"""

        if not trend_data or not trend_data.get("data"):
            return {"labels": [], "datasets": []}

        data_points = trend_data["data"]

        labels = [point["aggregation_period"] for point in data_points]
        values = [point["recorded_value"] for point in data_points]
        targets = [point["target_value"] for point in data_points if point.get("target_value")]

        chart_data = {
            "labels": labels,
            "datasets": [{"name": "Actual", "values": values, "chartType": chart_type.lower()}],
        }

        # Add target line for applicable chart types
        if targets and chart_type in ["Line", "Bar", "Area"]:
            chart_data["datasets"].append(
                {"name": "Target", "values": targets, "chartType": "line"}
            )

        return chart_data


@frappe.whitelist()
def get_dashboard_for_user(user=None, role=None):
    """Get appropriate dashboard for user or role"""

    if not user:
        user = frappe.session.user

    if not role:
        # Get user's primary role for dashboard selection
        user_roles = frappe.get_roles(user)
        role_priority = ["Workshop Manager", "System Manager", "Workshop User"]
        role = next(
            (r for r in role_priority if r in user_roles), user_roles[0] if user_roles else None
        )

    # Find default dashboard for role
    dashboard = frappe.db.get_value(
        "Dashboard Config", {"target_role": role, "is_default": 1, "is_active": 1}, "name"
    )

    # If no default found, get first active dashboard for role
    if not dashboard:
        dashboard = frappe.db.get_value(
            "Dashboard Config", {"target_role": role, "is_active": 1}, "name"
        )

    # If still no dashboard found, get first public dashboard
    if not dashboard:
        dashboard = frappe.db.get_value(
            "Dashboard Config", {"is_public": 1, "is_active": 1}, "name"
        )

    return dashboard


@frappe.whitelist()
def get_dashboard_data(dashboard_name):
    """Get dashboard data for rendering"""
    try:
        dashboard = frappe.get_doc("Dashboard Config", dashboard_name)
        return {
            "config": dashboard.as_dict(),
            "widgets": [w.as_dict() for w in dashboard.widgets if w.is_visible],
        }
    except Exception as e:
        frappe.log_error(f"Dashboard error: {str(e)}", "Dashboard Error")
        frappe.throw(_("Error loading dashboard"))


@frappe.whitelist()
def create_default_executive_dashboard():
    """Create default executive dashboard with standard widgets"""

    if frappe.db.exists("Dashboard Config", "executive_overview"):
        return "executive_overview"

    dashboard = frappe.new_doc("Dashboard Config")
    dashboard.dashboard_name = "executive_overview"
    dashboard.dashboard_title = "Executive Overview"
    dashboard.dashboard_title_ar = "نظرة عامة تنفيذية"
    dashboard.dashboard_type = "Executive"
    dashboard.target_role = "Workshop Manager"
    dashboard.is_default = 1
    dashboard.grid_columns = "4"
    dashboard.refresh_interval = 300
    dashboard.auto_refresh = 1
    dashboard.enable_filtering = 1
    dashboard.default_date_range = "This Month"
    dashboard.is_active = 1

    # Add default widgets
    widgets = [
        {
            "widget_id": "monthly_revenue_kpi",
            "widget_title": "Monthly Revenue",
            "widget_title_ar": "الإيرادات الشهرية",
            "widget_type": "KPI Card",
            "widget_size": "Medium (2x1)",
            "position_order": 1,
            "kpi_code": "MONTHLY_REVENUE",
            "data_source": "KPI",
            "aggregation_period": "Daily",
            "show_target": 1,
            "show_trend": 1,
            "color_scheme": "Green",
        },
        {
            "widget_id": "customer_satisfaction_gauge",
            "widget_title": "Customer Satisfaction",
            "widget_title_ar": "رضا العملاء",
            "widget_type": "Gauge",
            "widget_size": "Medium (2x1)",
            "position_order": 2,
            "kpi_code": "CUSTOMER_SATISFACTION",
            "data_source": "KPI",
            "aggregation_period": "Daily",
            "show_target": 1,
            "color_scheme": "Blue",
        },
        {
            "widget_id": "revenue_trend_chart",
            "widget_title": "Revenue Trend",
            "widget_title_ar": "اتجاه الإيرادات",
            "widget_type": "Chart",
            "widget_size": "Large (2x2)",
            "position_order": 3,
            "kpi_code": "MONTHLY_REVENUE",
            "chart_type": "Line",
            "data_source": "KPI",
            "aggregation_period": "Daily",
            "limit_records": 30,
            "show_target": 1,
            "show_trend": 1,
            "color_scheme": "Default",
        },
        {
            "widget_id": "technician_productivity",
            "widget_title": "Technician Productivity",
            "widget_title_ar": "إنتاجية الفنيين",
            "widget_type": "KPI Card",
            "widget_size": "Medium (2x1)",
            "position_order": 4,
            "kpi_code": "TECHNICIAN_PRODUCTIVITY",
            "data_source": "KPI",
            "aggregation_period": "Daily",
            "show_target": 1,
            "show_trend": 1,
            "color_scheme": "Orange",
        },
    ]

    for widget_data in widgets:
        dashboard.append("widgets", widget_data)

    dashboard.insert()

    return dashboard.name
