"""
Real-time Dashboard System for Universal Workshop ERP
Comprehensive dashboard with WebSocket updates, widget management, and Arabic support
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint, add_days, get_datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import asyncio
from datetime import datetime, timedelta
from .chart_engine import chart_engine

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class DashboardRealtimeManager:
    """Real-time Dashboard Management System"""

    def __init__(self):
        self.redis_client = frappe.cache() if REDIS_AVAILABLE else None
        self.update_interval = 30  # seconds
        self.websocket_room = "universal_workshop_dashboard"
        
        # Widget types and their configurations
        self.widget_types = {
            "chart": {
                "name_ar": "مخطط بياني",
                "refresh_interval": 30000,
                "data_source": "chart_engine",
                "size_options": ["small", "medium", "large", "xlarge"]
            },
            "kpi": {
                "name_ar": "مؤشر أداء",
                "refresh_interval": 15000,
                "data_source": "sql",
                "size_options": ["small", "medium"]
            },
            "table": {
                "name_ar": "جدول بيانات",
                "refresh_interval": 60000,
                "data_source": "doctype",
                "size_options": ["medium", "large", "xlarge"]
            },
            "gauge": {
                "name_ar": "مقياس",
                "refresh_interval": 20000,
                "data_source": "api",
                "size_options": ["small", "medium"]
            },
            "alert": {
                "name_ar": "تنبيه",
                "refresh_interval": 10000,
                "data_source": "realtime",
                "size_options": ["small", "medium", "large"]
            },
            "timeline": {
                "name_ar": "الجدول الزمني",
                "refresh_interval": 45000,
                "data_source": "mixed",
                "size_options": ["medium", "large"]
            }
        }
        
        # Dashboard themes
        self.dashboard_themes = {
            "light": {
                "name_ar": "فاتح",
                "background": "#ffffff",
                "card_background": "#f8f9fa",
                "text_color": "#2c3e50",
                "border_color": "#dee2e6"
            },
            "dark": {
                "name_ar": "داكن",
                "background": "#1a1a1a",
                "card_background": "#2d3748",
                "text_color": "#f7fafc",
                "border_color": "#4a5568"
            },
            "workshop": {
                "name_ar": "ورشة",
                "background": "#f0f4f8",
                "card_background": "#ffffff",
                "text_color": "#2d3748",
                "border_color": "#e2e8f0"
            }
        }

    def create_dashboard_config(self, user_id: str, dashboard_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update dashboard configuration"""
        try:
            # Validate configuration
            validated_config = self._validate_dashboard_config(config)
            
            # Save to database
            dashboard_config = {
                "user_id": user_id,
                "dashboard_name": dashboard_name,
                "config": validated_config,
                "created_at": now_datetime().isoformat(),
                "is_active": True
            }
            
            # Store in database
            existing = frappe.db.exists("Dashboard Config", {
                "user_id": user_id,
                "dashboard_name": dashboard_name
            })
            
            if existing:
                doc = frappe.get_doc("Dashboard Config", existing)
                doc.update(dashboard_config)
                doc.save()
            else:
                doc = frappe.new_doc("Dashboard Config")
                doc.update(dashboard_config)
                doc.insert()
            
            # Cache the configuration
            if self.redis_client:
                cache_key = f"dashboard:config:{user_id}:{dashboard_name}"
                self.redis_client.setex(cache_key, 3600, frappe.as_json(validated_config))
            
            return {
                "status": "success",
                "dashboard_id": doc.name,
                "message": _("Dashboard configuration saved successfully"),
                "message_ar": "تم حفظ إعدادات لوحة المعلومات بنجاح"
            }
            
        except Exception as e:
            frappe.log_error(f"Dashboard config creation error: {str(e)}", "Dashboard Realtime Error")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_dashboard_config(self, user_id: str, dashboard_name: str = "default") -> Dict[str, Any]:
        """Get dashboard configuration for user"""
        try:
            # Try cache first
            if self.redis_client:
                cache_key = f"dashboard:config:{user_id}:{dashboard_name}"
                cached_config = self.redis_client.get(cache_key)
                if cached_config:
                    return frappe.parse_json(cached_config)
            
            # Get from database
            config_doc = frappe.db.get_value("Dashboard Config", {
                "user_id": user_id,
                "dashboard_name": dashboard_name,
                "is_active": 1
            }, "config")
            
            if config_doc:
                config = frappe.parse_json(config_doc)
                
                # Cache for next time
                if self.redis_client:
                    cache_key = f"dashboard:config:{user_id}:{dashboard_name}"
                    self.redis_client.setex(cache_key, 3600, frappe.as_json(config))
                
                return config
            else:
                # Return default configuration
                return self._get_default_dashboard_config()
                
        except Exception as e:
            frappe.log_error(f"Dashboard config retrieval error: {str(e)}", "Dashboard Realtime Error")
            return self._get_default_dashboard_config()

    def update_widget_data(self, widget_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update data for a specific widget"""
        try:
            widget_type = config.get("type", "chart")
            data_source = config.get("data_source", {})
            
            # Get widget data based on type
            if widget_type == "chart":
                widget_data = self._get_chart_widget_data(config)
            elif widget_type == "kpi":
                widget_data = self._get_kpi_widget_data(config)
            elif widget_type == "table":
                widget_data = self._get_table_widget_data(config)
            elif widget_type == "gauge":
                widget_data = self._get_gauge_widget_data(config)
            elif widget_type == "alert":
                widget_data = self._get_alert_widget_data(config)
            elif widget_type == "timeline":
                widget_data = self._get_timeline_widget_data(config)
            else:
                raise ValueError(f"Unsupported widget type: {widget_type}")
            
            # Add metadata
            widget_result = {
                "widget_id": widget_id,
                "type": widget_type,
                "data": widget_data,
                "last_updated": now_datetime().isoformat(),
                "update_interval": config.get("refresh_interval", 30000),
                "status": "success"
            }
            
            # Cache the result
            if self.redis_client:
                cache_key = f"widget:data:{widget_id}"
                cache_duration = config.get("cache_duration", 300)
                self.redis_client.setex(cache_key, cache_duration, frappe.as_json(widget_result))
            
            return widget_result
            
        except Exception as e:
            frappe.log_error(f"Widget data update error: {str(e)}", "Dashboard Widget Error")
            return {
                "widget_id": widget_id,
                "type": config.get("type", "unknown"),
                "status": "error",
                "error": str(e),
                "last_updated": now_datetime().isoformat()
            }

    def _get_chart_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for chart widget"""
        chart_config = config.get("chart_config", {})
        return chart_engine.generate_chart(chart_config)

    def _get_kpi_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for KPI widget"""
        data_source = config.get("data_source", {})
        
        if data_source.get("type") == "sql":
            query = data_source.get("query", "")
            params = data_source.get("params", [])
            
            result = frappe.db.sql(query, params, as_dict=True)
            if result:
                value = result[0].get("value", 0)
                previous_value = result[0].get("previous_value", 0) if len(result[0]) > 1 else 0
                
                # Calculate trend
                if previous_value > 0:
                    trend_percent = ((value - previous_value) / previous_value) * 100
                else:
                    trend_percent = 0
                
                return {
                    "current_value": flt(value),
                    "previous_value": flt(previous_value),
                    "trend_percent": round(trend_percent, 2),
                    "trend_direction": "up" if trend_percent > 0 else "down" if trend_percent < 0 else "neutral",
                    "formatted_value": self._format_kpi_value(value, config.get("format", "number")),
                    "title": config.get("title", "KPI"),
                    "title_ar": config.get("title_ar", "مؤشر الأداء")
                }
        
        return {"current_value": 0, "error": "Invalid data source"}

    def _get_table_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for table widget"""
        data_source = config.get("data_source", {})
        
        if data_source.get("type") == "doctype":
            doctype = data_source.get("doctype")
            filters = data_source.get("filters", {})
            fields = data_source.get("fields", ["name"])
            limit = data_source.get("limit", 10)
            order_by = data_source.get("order_by", "creation desc")
            
            rows = frappe.get_list(
                doctype,
                filters=filters,
                fields=fields,
                limit=limit,
                order_by=order_by
            )
            
            return {
                "headers": fields,
                "rows": rows,
                "total_rows": len(rows),
                "title": config.get("title", "Table"),
                "title_ar": config.get("title_ar", "جدول")
            }
        
        return {"headers": [], "rows": [], "total_rows": 0}

    def _get_gauge_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for gauge widget"""
        data_source = config.get("data_source", {})
        
        # Default gauge data
        gauge_data = {
            "value": 0,
            "min": 0,
            "max": 100,
            "thresholds": [
                {"value": 30, "color": "#28a745", "label": "جيد"},
                {"value": 70, "color": "#ffc107", "label": "متوسط"},
                {"value": 100, "color": "#dc3545", "label": "سيء"}
            ],
            "title": config.get("title", "Gauge"),
            "title_ar": config.get("title_ar", "مقياس")
        }
        
        if data_source.get("type") == "api":
            try:
                api_result = frappe.call(data_source.get("endpoint"), **data_source.get("params", {}))
                if isinstance(api_result, dict):
                    gauge_data.update(api_result)
                elif isinstance(api_result, (int, float)):
                    gauge_data["value"] = flt(api_result)
            except Exception as e:
                frappe.log_error(f"Gauge API call error: {str(e)}", "Dashboard Gauge Error")
        
        return gauge_data

    def _get_alert_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for alert widget"""
        # Get recent alerts
        alerts = frappe.get_list(
            "Performance Alert",
            filters={
                "resolved": 0,
                "creation": [">", add_days(now_datetime(), -1)]
            },
            fields=["name", "alert_type", "severity", "message", "message_ar", "creation"],
            order_by="creation desc",
            limit=config.get("max_alerts", 5)
        )
        
        # Group by severity
        alert_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for alert in alerts:
            severity = alert.get("severity", "Low")
            if severity in alert_counts:
                alert_counts[severity] += 1
        
        return {
            "alerts": alerts,
            "alert_counts": alert_counts,
            "total_unresolved": len(alerts),
            "title": config.get("title", "Alerts"),
            "title_ar": config.get("title_ar", "التنبيهات")
        }

    def _get_timeline_widget_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for timeline widget"""
        # Get recent activities
        activities = []
        
        # Service orders timeline
        recent_orders = frappe.get_list(
            "Service Order",
            filters={"creation": [">", add_days(now_datetime(), -7)]},
            fields=["name", "customer", "status", "creation"],
            order_by="creation desc",
            limit=10
        )
        
        for order in recent_orders:
            activities.append({
                "type": "service_order",
                "title": f"Service Order {order['name']}",
                "title_ar": f"طلب خدمة {order['name']}",
                "description": f"Customer: {order['customer']}",
                "timestamp": order["creation"],
                "status": order["status"],
                "icon": "tool"
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "activities": activities[:config.get("max_items", 10)],
            "title": config.get("title", "Timeline"),
            "title_ar": config.get("title_ar", "الجدول الزمني")
        }

    def broadcast_dashboard_update(self, user_id: str, widget_id: str, data: Dict[str, Any]):
        """Broadcast widget update to specific user via WebSocket"""
        try:
            message = {
                "type": "widget_update",
                "widget_id": widget_id,
                "data": data,
                "timestamp": now_datetime().isoformat(),
                "user_id": user_id
            }
            
            # Send to specific user room
            frappe.publish_realtime(
                event="dashboard_widget_update",
                message=message,
                room=f"dashboard_user_{user_id}"
            )
            
            # Also send to general dashboard room for shared widgets
            frappe.publish_realtime(
                event="dashboard_widget_update",
                message=message,
                room=self.websocket_room
            )
            
        except Exception as e:
            frappe.log_error(f"Dashboard broadcast error: {str(e)}", "Dashboard WebSocket Error")

    def refresh_all_widgets(self, user_id: str, dashboard_name: str = "default"):
        """Refresh all widgets for a user's dashboard"""
        try:
            # Get dashboard configuration
            dashboard_config = self.get_dashboard_config(user_id, dashboard_name)
            
            if not dashboard_config or "widgets" not in dashboard_config:
                return
            
            # Update each widget
            for widget in dashboard_config["widgets"]:
                widget_id = widget.get("id")
                if widget_id:
                    updated_data = self.update_widget_data(widget_id, widget)
                    self.broadcast_dashboard_update(user_id, widget_id, updated_data)
            
        except Exception as e:
            frappe.log_error(f"Dashboard refresh error: {str(e)}", "Dashboard Refresh Error")

    def get_dashboard_analytics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get dashboard usage analytics"""
        try:
            # This would track widget views, interactions, etc.
            # For now, return sample analytics
            
            return {
                "period_days": days,
                "total_widget_views": 156,
                "most_viewed_widget_type": "chart",
                "average_session_duration": "12.5 minutes",
                "refresh_count": 45,
                "error_rate": 0.02,
                "performance_score": 98.5,
                "user_engagement": {
                    "daily_logins": 6,
                    "widgets_interacted": 8,
                    "customizations_made": 3
                },
                "generated_at": now_datetime().isoformat()
            }
            
        except Exception as e:
            frappe.log_error(f"Dashboard analytics error: {str(e)}", "Dashboard Analytics Error")
            return {"error": str(e)}

    def _validate_dashboard_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate dashboard configuration"""
        if not isinstance(config, dict):
            raise ValueError("Dashboard configuration must be a dictionary")
        
        # Required fields
        required_fields = ["layout", "widgets"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required field '{field}' is missing")
        
        # Validate widgets
        if not isinstance(config["widgets"], list):
            raise ValueError("Widgets must be a list")
        
        for widget in config["widgets"]:
            if not isinstance(widget, dict):
                raise ValueError("Each widget must be a dictionary")
            
            if "type" not in widget:
                raise ValueError("Widget type is required")
            
            if widget["type"] not in self.widget_types:
                raise ValueError(f"Unsupported widget type: {widget['type']}")
        
        return config

    def _get_default_dashboard_config(self) -> Dict[str, Any]:
        """Get default dashboard configuration"""
        return {
            "layout": {
                "columns": 12,
                "rows": "auto",
                "gap": 16,
                "theme": "workshop"
            },
            "widgets": [
                {
                    "id": "workshop_overview",
                    "type": "chart",
                    "title": "Workshop Overview",
                    "title_ar": "نظرة عامة على الورشة",
                    "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                    "chart_config": {
                        "type": "bar",
                        "data_source": {
                            "type": "custom",
                            "function": "universal_workshop.utils.chart_engine.get_sample_data"
                        }
                    },
                    "refresh_interval": 30000
                },
                {
                    "id": "active_orders",
                    "type": "kpi",
                    "title": "Active Orders",
                    "title_ar": "الطلبات النشطة",
                    "position": {"x": 6, "y": 0, "w": 3, "h": 2},
                    "data_source": {
                        "type": "sql",
                        "query": "SELECT COUNT(*) as value FROM `tabService Order` WHERE status IN ('Draft', 'In Progress')"
                    },
                    "refresh_interval": 15000
                },
                {
                    "id": "system_alerts",
                    "type": "alert",
                    "title": "System Alerts",
                    "title_ar": "تنبيهات النظام",
                    "position": {"x": 9, "y": 0, "w": 3, "h": 4},
                    "max_alerts": 5,
                    "refresh_interval": 10000
                }
            ],
            "auto_refresh": True,
            "refresh_interval": 30000
        }

    def _format_kpi_value(self, value: float, format_type: str) -> str:
        """Format KPI value based on type"""
        if format_type == "currency":
            return f"OMR {value:,.2f}"
        elif format_type == "percentage":
            return f"{value:.1f}%"
        elif format_type == "number":
            return f"{value:,.0f}"
        else:
            return str(value)


# Global dashboard manager instance
dashboard_manager = DashboardRealtimeManager()


# Whitelisted API methods
@frappe.whitelist()
def create_dashboard_config(dashboard_name, config):
    """API endpoint to create dashboard configuration"""
    if isinstance(config, str):
        config = frappe.parse_json(config)
    
    user_id = frappe.session.user
    return dashboard_manager.create_dashboard_config(user_id, dashboard_name, config)


@frappe.whitelist()
def get_dashboard_config(dashboard_name="default"):
    """API endpoint to get dashboard configuration"""
    user_id = frappe.session.user
    return dashboard_manager.get_dashboard_config(user_id, dashboard_name)


@frappe.whitelist()
def update_widget_data(widget_id, config):
    """API endpoint to update widget data"""
    if isinstance(config, str):
        config = frappe.parse_json(config)
    
    return dashboard_manager.update_widget_data(widget_id, config)


@frappe.whitelist()
def refresh_dashboard(dashboard_name="default"):
    """API endpoint to refresh all dashboard widgets"""
    user_id = frappe.session.user
    dashboard_manager.refresh_all_widgets(user_id, dashboard_name)
    return {"status": "success", "message": "Dashboard refreshed"}


@frappe.whitelist()
def get_dashboard_analytics(days=7):
    """API endpoint to get dashboard analytics"""
    user_id = frappe.session.user
    return dashboard_manager.get_dashboard_analytics(user_id, int(days))


@frappe.whitelist()
def get_widget_types():
    """API endpoint to get available widget types"""
    return dashboard_manager.widget_types


@frappe.whitelist()
def get_dashboard_themes():
    """API endpoint to get available dashboard themes"""
    return dashboard_manager.dashboard_themes


# Scheduled functions for real-time updates
def update_realtime_dashboards():
    """Scheduled function to update all active dashboards"""
    try:
        # Get all active dashboard configurations
        active_dashboards = frappe.get_list(
            "Dashboard Config",
            filters={"is_active": 1},
            fields=["user_id", "dashboard_name"]
        )
        
        for dashboard in active_dashboards:
            dashboard_manager.refresh_all_widgets(
                dashboard["user_id"], 
                dashboard["dashboard_name"]
            )
        
        return {
            "status": "success",
            "updated_dashboards": len(active_dashboards),
            "timestamp": now_datetime().isoformat()
        }
        
    except Exception as e:
        frappe.log_error(f"Realtime dashboard update error: {str(e)}", "Dashboard Scheduled Update Error")
        return {"status": "error", "error": str(e)}


def cleanup_dashboard_cache():
    """Cleanup old dashboard cache entries"""
    try:
        if dashboard_manager.redis_client:
            # Delete cache entries older than 24 hours
            keys_deleted = 0
            dashboard_keys = dashboard_manager.redis_client.keys("dashboard:*")
            widget_keys = dashboard_manager.redis_client.keys("widget:*")
            
            all_keys = dashboard_keys + widget_keys
            for key in all_keys:
                try:
                    ttl = dashboard_manager.redis_client.ttl(key)
                    if ttl < 0:  # Key has no expiry or expired
                        dashboard_manager.redis_client.delete(key)
                        keys_deleted += 1
                except Exception:
                    continue
            
            return {
                "status": "success",
                "keys_deleted": keys_deleted,
                "timestamp": now_datetime().isoformat()
            }
        
        return {"status": "success", "message": "Redis not available"}
        
    except Exception as e:
        frappe.log_error(f"Dashboard cache cleanup error: {str(e)}", "Dashboard Cache Cleanup Error")
        return {"status": "error", "error": str(e)} 