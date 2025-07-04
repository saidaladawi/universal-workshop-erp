# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, flt, cint
from typing import Dict, List, Any, Optional
import json


class DashboardConfig(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate dashboard configuration"""
        self.validate_configuration()
        self.validate_user_permissions()
        self.validate_widget_configuration()
        self.set_default_values()

    def before_save(self):
        """Set metadata before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_at:
            self.created_at = now_datetime()

        self.modified_by = frappe.session.user
        self.last_modified = now_datetime()

        # Update widget count
        if self.config:
            config_data = (
                frappe.parse_json(self.config) if isinstance(self.config, str) else self.config
            )
            widgets = config_data.get("widgets", [])
            self.widget_count = len(widgets)

    def after_save(self):
        """Clear cache after saving"""
        self.clear_dashboard_cache()

    def validate_configuration(self):
        """Validate dashboard configuration JSON"""
        if not self.config:
            frappe.throw(_("Dashboard configuration is required"))

        try:
            if isinstance(self.config, str):
                config_data = frappe.parse_json(self.config)
            else:
                config_data = self.config

            # Validate required configuration fields
            required_fields = ["layout", "widgets"]
            for field in required_fields:
                if field not in config_data:
                    frappe.throw(_("Configuration field '{0}' is required").format(field))

            # Validate layout configuration
            layout = config_data.get("layout", {})
            if not isinstance(layout, dict):
                frappe.throw(_("Layout configuration must be an object"))

            # Validate widgets configuration
            widgets = config_data.get("widgets", [])
            if not isinstance(widgets, list):
                frappe.throw(_("Widgets configuration must be an array"))

            # Validate each widget
            for i, widget in enumerate(widgets):
                self.validate_widget(widget, i)

        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.throw(_("Invalid configuration format: {0}").format(str(e)))

    def validate_widget(self, widget: Dict[str, Any], index: int):
        """Validate individual widget configuration"""
        if not isinstance(widget, dict):
            frappe.throw(_("Widget {0}: Widget must be an object").format(index + 1))

        # Required widget fields
        required_fields = ["id", "type"]
        for field in required_fields:
            if field not in widget:
                frappe.throw(_("Widget {0}: Field '{1}' is required").format(index + 1, field))

        # Validate widget type
        valid_types = ["chart", "kpi", "table", "gauge", "alert", "timeline"]
        if widget["type"] not in valid_types:
            frappe.throw(
                _("Widget {0}: Invalid widget type '{1}'").format(index + 1, widget["type"])
            )

        # Validate widget ID uniqueness
        widget_id = widget["id"]
        if isinstance(self.config, str):
            config_data = frappe.parse_json(self.config)
        else:
            config_data = self.config

        widgets = config_data.get("widgets", [])
        widget_ids = [w.get("id") for w in widgets if w.get("id")]

        if widget_ids.count(widget_id) > 1:
            frappe.throw(_("Widget ID '{0}' must be unique").format(widget_id))

    def validate_user_permissions(self):
        """Validate user permissions for dashboard"""
        # Check if user exists
        if not frappe.db.exists("User", self.user_id):
            frappe.throw(_("User '{0}' does not exist").format(self.user_id))

        # Check if user is enabled
        user_enabled = frappe.db.get_value("User", self.user_id, "enabled")
        if not user_enabled:
            frappe.throw(_("User '{0}' is disabled").format(self.user_id))

        # Validate shared users if specified
        if self.shared_with_users:
            try:
                shared_users = (
                    frappe.parse_json(self.shared_with_users)
                    if isinstance(self.shared_with_users, str)
                    else self.shared_with_users
                )

                if isinstance(shared_users, list):
                    for user_id in shared_users:
                        if not frappe.db.exists("User", user_id):
                            frappe.throw(_("Shared user '{0}' does not exist").format(user_id))

            except Exception as e:
                frappe.throw(_("Invalid shared users format: {0}").format(str(e)))

    def validate_widget_configuration(self):
        """Validate widget-specific configurations"""
        if not self.config:
            return

        try:
            config_data = (
                frappe.parse_json(self.config) if isinstance(self.config, str) else self.config
            )
            widgets = config_data.get("widgets", [])

            for widget in widgets:
                widget_type = widget.get("type")

                # Validate chart widgets
                if widget_type == "chart" and "chart_config" in widget:
                    self.validate_chart_widget(widget["chart_config"])

                # Validate KPI widgets
                elif widget_type == "kpi" and "data_source" in widget:
                    self.validate_kpi_widget(widget["data_source"])

                # Validate table widgets
                elif widget_type == "table" and "data_source" in widget:
                    self.validate_table_widget(widget["data_source"])

        except Exception as e:
            frappe.throw(_("Widget configuration validation error: {0}").format(str(e)))

    def validate_chart_widget(self, chart_config: Dict[str, Any]):
        """Validate chart widget configuration"""
        required_fields = ["type", "data_source"]
        for field in required_fields:
            if field not in chart_config:
                frappe.throw(_("Chart widget: Field '{0}' is required").format(field))

    def validate_kpi_widget(self, data_source: Dict[str, Any]):
        """Validate KPI widget data source"""
        if "type" not in data_source:
            frappe.throw(_("KPI widget: Data source type is required"))

        if data_source["type"] == "sql" and "query" not in data_source:
            frappe.throw(_("KPI widget: SQL query is required"))

    def validate_table_widget(self, data_source: Dict[str, Any]):
        """Validate table widget data source"""
        if "type" not in data_source:
            frappe.throw(_("Table widget: Data source type is required"))

        if data_source["type"] == "doctype" and "doctype" not in data_source:
            frappe.throw(_("Table widget: DocType is required"))

    def set_default_values(self):
        """Set default values for dashboard configuration"""
        if not self.dashboard_name_ar and self.dashboard_name:
            # Set default Arabic name
            self.dashboard_name_ar = self.dashboard_name

        if not self.theme:
            self.theme = "workshop"

        if self.refresh_interval is None:
            self.refresh_interval = 30000

        if self.auto_refresh is None:
            self.auto_refresh = 1

    def clear_dashboard_cache(self):
        """Clear dashboard cache for this configuration"""
        try:
            # Clear Redis cache if available
            redis_client = frappe.cache()
            if redis_client:
                cache_patterns = [
                    f"dashboard:config:{self.user_id}:{self.dashboard_name}",
                    f"dashboard:config:{self.user_id}:*",
                    f"widget:data:*",
                ]

                for pattern in cache_patterns:
                    keys = redis_client.keys(pattern)
                    if keys:
                        redis_client.delete(*keys)

        except Exception as e:
            frappe.log_error(
                f"Dashboard cache clear error: {str(e)}", "Dashboard Config Cache Error"
            )

    def get_dashboard_performance(self) -> Dict[str, Any]:
        """Get dashboard performance metrics"""
        try:
            config_data = (
                frappe.parse_json(self.config) if isinstance(self.config, str) else self.config
            )
            widgets = config_data.get("widgets", [])

            # Calculate performance metrics
            total_widgets = len(widgets)
            estimated_load_time = total_widgets * 200  # Estimate 200ms per widget

            # Performance score calculation (0-100)
            score = 100
            if total_widgets > 10:
                score -= (total_widgets - 10) * 5  # Penalty for too many widgets
            if self.refresh_interval < 10000:
                score -= 10  # Penalty for too frequent refresh
            if self.error_count > 5:
                score -= self.error_count * 2  # Penalty for errors

            score = max(0, min(100, score))  # Clamp between 0-100

            return {
                "total_widgets": total_widgets,
                "estimated_load_time": estimated_load_time,
                "performance_score": score,
                "refresh_interval": self.refresh_interval,
                "error_count": self.error_count,
                "last_accessed": self.last_accessed,
                "recommendations": self.get_performance_recommendations(score, total_widgets),
            }

        except Exception as e:
            frappe.log_error(
                f"Dashboard performance calculation error: {str(e)}", "Dashboard Performance Error"
            )
            return {"error": str(e)}

    def get_performance_recommendations(self, score: float, widget_count: int) -> List[str]:
        """Get performance improvement recommendations"""
        recommendations = []

        if score < 70:
            recommendations.append(_("Consider reducing the number of widgets"))
            recommendations.append(_("Increase refresh intervals for better performance"))

        if widget_count > 8:
            recommendations.append(_("Too many widgets may slow down the dashboard"))

        if self.refresh_interval < 15000:
            recommendations.append(_("Consider increasing refresh interval to reduce server load"))

        if self.error_count > 3:
            recommendations.append(_("Fix widget configuration errors to improve reliability"))

        return recommendations

    @frappe.whitelist()
    def update_performance_metrics(self, load_time: int, error_count: Optional[int] = None):
        """Update dashboard performance metrics"""
        try:
            self.load_time_ms = load_time
            if error_count is not None:
                self.error_count = error_count

            # Recalculate performance score
            performance_data = self.get_dashboard_performance()
            self.performance_score = performance_data.get("performance_score", 0)

            self.save()

            return {
                "status": "success",
                "performance_score": self.performance_score,
                "load_time_ms": self.load_time_ms,
            }

        except Exception as e:
            frappe.log_error(
                f"Performance metrics update error: {str(e)}", "Dashboard Performance Error"
            )
            return {"status": "error", "error": str(e)}

    @frappe.whitelist()
    def clone_dashboard(self, new_name: str, new_user: Optional[str] = None):
        """Clone dashboard configuration for another user or with new name"""
        try:
            new_dashboard = frappe.copy_doc(self)
            new_dashboard.dashboard_name = new_name
            new_dashboard.user_id = new_user or self.user_id
            new_dashboard.is_default = 0
            new_dashboard.created_at = now_datetime()
            new_dashboard.created_by = frappe.session.user

            # Clear performance metrics for new dashboard
            new_dashboard.performance_score = 0
            new_dashboard.load_time_ms = 0
            new_dashboard.error_count = 0
            new_dashboard.last_accessed = None

            new_dashboard.insert()

            return {
                "status": "success",
                "new_dashboard_id": new_dashboard.name,
                "message": _("Dashboard cloned successfully"),
            }

        except Exception as e:
            frappe.log_error(f"Dashboard clone error: {str(e)}", "Dashboard Clone Error")
            return {"status": "error", "error": str(e)}


# Whitelisted API methods
@frappe.whitelist()
def get_user_dashboards(user_id=None):
    """Get all dashboards for a user"""
    if not user_id:
        user_id = frappe.session.user

    try:
        dashboards = frappe.get_list(
            "Dashboard Config",
            filters={"user_id": user_id, "is_active": 1},
            fields=[
                "name",
                "dashboard_name",
                "dashboard_name_ar",
                "theme",
                "is_default",
                "last_accessed",
                "widget_count",
                "performance_score",
            ],
            order_by="is_default desc, last_accessed desc",
        )

        return {"status": "success", "dashboards": dashboards, "total_dashboards": len(dashboards)}

    except Exception as e:
        frappe.log_error(f"Get user dashboards error: {str(e)}", "Dashboard API Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def set_default_dashboard(dashboard_id, user_id=None):
    """Set a dashboard as default for user"""
    if not user_id:
        user_id = frappe.session.user

    try:
        # Clear existing default
        frappe.db.sql(
            """
            UPDATE `tabDashboard Config` 
            SET is_default = 0 
            WHERE user_id = %s
        """,
            [user_id],
        )

        # Set new default
        dashboard = frappe.get_doc("Dashboard Config", dashboard_id)
        if dashboard.user_id == user_id:
            dashboard.is_default = 1
            dashboard.save()

            return {"status": "success", "message": _("Default dashboard updated successfully")}
        else:
            return {
                "status": "error",
                "error": _("You don't have permission to modify this dashboard"),
            }

    except Exception as e:
        frappe.log_error(f"Set default dashboard error: {str(e)}", "Dashboard API Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def get_dashboard_analytics(dashboard_id):
    """Get analytics for a specific dashboard"""
    try:
        dashboard = frappe.get_doc("Dashboard Config", dashboard_id)

        # Check permissions
        if dashboard.user_id != frappe.session.user and not frappe.has_permission(
            "Dashboard Config", "read"
        ):
            return {"status": "error", "error": _("Permission denied")}

        analytics = dashboard.get_dashboard_performance()

        # Add usage statistics
        usage_stats = {
            "total_views": 0,  # Would be tracked in a separate table
            "avg_session_duration": "N/A",
            "last_30_days_usage": [],
            "most_used_widgets": [],
        }

        return {
            "status": "success",
            "analytics": analytics,
            "usage_stats": usage_stats,
            "dashboard_info": {
                "name": dashboard.dashboard_name,
                "name_ar": dashboard.dashboard_name_ar,
                "created_at": dashboard.created_at,
                "widget_count": dashboard.widget_count,
            },
        }

    except Exception as e:
        frappe.log_error(f"Dashboard analytics error: {str(e)}", "Dashboard Analytics Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def export_dashboard_config(dashboard_id):
    """Export dashboard configuration as JSON"""
    try:
        dashboard = frappe.get_doc("Dashboard Config", dashboard_id)

        # Check permissions
        if dashboard.user_id != frappe.session.user and not frappe.has_permission(
            "Dashboard Config", "read"
        ):
            return {"status": "error", "error": _("Permission denied")}

        export_data = {
            "dashboard_name": dashboard.dashboard_name,
            "dashboard_name_ar": dashboard.dashboard_name_ar,
            "theme": dashboard.theme,
            "auto_refresh": dashboard.auto_refresh,
            "refresh_interval": dashboard.refresh_interval,
            "config": dashboard.config,
            "layout_config": dashboard.layout_config,
            "exported_at": now_datetime().isoformat(),
            "exported_by": frappe.session.user,
        }

        return {
            "status": "success",
            "export_data": export_data,
            "filename": f"dashboard_config_{dashboard.dashboard_name}.json",
        }

    except Exception as e:
        frappe.log_error(f"Dashboard export error: {str(e)}", "Dashboard Export Error")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def import_dashboard_config(config_data, dashboard_name=None):
    """Import dashboard configuration from JSON"""
    try:
        if isinstance(config_data, str):
            config_data = frappe.parse_json(config_data)

        # Create new dashboard
        dashboard = frappe.new_doc("Dashboard Config")
        dashboard.user_id = frappe.session.user
        dashboard.dashboard_name = dashboard_name or config_data.get(
            "dashboard_name", "Imported Dashboard"
        )
        dashboard.dashboard_name_ar = config_data.get("dashboard_name_ar", dashboard.dashboard_name)
        dashboard.theme = config_data.get("theme", "workshop")
        dashboard.auto_refresh = config_data.get("auto_refresh", 1)
        dashboard.refresh_interval = config_data.get("refresh_interval", 30000)
        dashboard.config = config_data.get("config", {})
        dashboard.layout_config = config_data.get("layout_config", {})

        dashboard.insert()

        return {
            "status": "success",
            "dashboard_id": dashboard.name,
            "message": _("Dashboard imported successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Dashboard import error: {str(e)}", "Dashboard Import Error")
        return {"status": "error", "error": str(e)}
