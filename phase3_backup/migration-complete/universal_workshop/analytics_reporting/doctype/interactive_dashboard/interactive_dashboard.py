"""
Universal Workshop ERP - Interactive Dashboard
Advanced dashboard builder with real-time data, drill-down capabilities, and customizable widgets
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, get_datetime, flt, cint, cstr
from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime, timedelta


class InteractiveDashboard(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate dashboard configuration"""
        self.validate_dashboard_names()
        self.validate_layout_configuration()
        self.validate_widget_configuration()
        self.validate_data_sources()
        self.validate_performance_settings()
        
    def before_save(self):
        """Set default values and calculate performance metrics"""
        self.set_default_values()
        self.calculate_performance_metrics()
        self.update_metadata()
        
    def validate_dashboard_names(self):
        """Validate dashboard name requirements"""
        if not self.dashboard_name:
            frappe.throw(_("Dashboard name (English) is required"))
            
        if not self.dashboard_name_ar:
            frappe.throw(_("Dashboard name (Arabic) is required"))
            
        # Check for duplicates
        existing = frappe.db.exists("Interactive Dashboard", {
            "dashboard_name": self.dashboard_name,
            "name": ["!=", self.name]
        })
        if existing:
            frappe.throw(_("Dashboard with this name already exists"))
            
    def validate_layout_configuration(self):
        """Validate layout settings"""
        if self.grid_columns and (self.grid_columns < 1 or self.grid_columns > 24):
            frappe.throw(_("Grid columns must be between 1 and 24"))
            
        if self.grid_rows and (self.grid_rows < 1 or self.grid_rows > 20):
            frappe.throw(_("Grid rows must be between 1 and 20"))
            
        if self.responsive_breakpoints:
            try:
                breakpoints = json.loads(self.responsive_breakpoints)
                required_keys = ['xs', 'sm', 'md', 'lg', 'xl']
                for key in required_keys:
                    if key not in breakpoints:
                        frappe.throw(_("Missing breakpoint: {0}").format(key))
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format for responsive breakpoints"))
                
    def validate_widget_configuration(self):
        """Validate widget settings"""
        if self.refresh_interval and self.refresh_interval < 5:
            frappe.throw(_("Refresh interval must be at least 5 seconds"))
            
        if self.cache_duration and self.cache_duration < 10:
            frappe.throw(_("Cache duration must be at least 10 seconds"))
            
    def validate_data_sources(self):
        """Validate data source configuration"""
        if self.primary_data_source:
            if not frappe.db.exists("Data Source Mapping", self.primary_data_source):
                frappe.throw(_("Primary data source does not exist"))
                
    def validate_performance_settings(self):
        """Validate performance-related settings"""
        if self.real_time_updates and not self.refresh_interval:
            self.refresh_interval = 30  # Default 30 seconds
            
    def set_default_values(self):
        """Set default values for new dashboards"""
        if not self.created_by:
            self.created_by = frappe.session.user
            
        if not self.created_date:
            self.created_date = get_datetime()
            
        if not self.version:
            self.version = "1.0.0"
            
        if not self.grid_columns:
            self.grid_columns = 12
            
        if not self.grid_rows:
            self.grid_rows = 6
            
        if not self.refresh_interval:
            self.refresh_interval = 30
            
        if not self.cache_duration:
            self.cache_duration = 300
            
        # Set RTL mode based on current language
        if frappe.local.lang == 'ar' and not self.rtl_mode:
            self.rtl_mode = 1
            
        if not self.arabic_font_family and self.rtl_mode:
            self.arabic_font_family = "Noto Sans Arabic"
            
    def calculate_performance_metrics(self):
        """Calculate dashboard performance metrics"""
        # Calculate complexity score based on widgets and data sources
        widget_count = len(self.widgets) if self.widgets else 0
        data_source_count = len(self.secondary_data_sources) if self.secondary_data_sources else 0
        
        # Performance score calculation (1-10 scale)
        base_score = 10.0
        
        # Deduct points for complexity
        if widget_count > 10:
            base_score -= (widget_count - 10) * 0.2
        if data_source_count > 5:
            base_score -= (data_source_count - 5) * 0.3
        if self.real_time_updates:
            base_score -= 1.0
        if self.refresh_interval < 30:
            base_score -= 1.5
            
        self.performance_score = max(1.0, min(10.0, base_score))
        
        # Estimate load time
        estimated_load_time = 1.0  # Base load time
        estimated_load_time += widget_count * 0.2
        estimated_load_time += data_source_count * 0.5
        if self.chart_library in ['D3.js', 'Plotly.js']:
            estimated_load_time += 0.5
            
        self.load_time = flt(estimated_load_time, 3)
        
        # Estimate memory usage
        estimated_memory = 10.0  # Base memory in MB
        estimated_memory += widget_count * 2.0
        estimated_memory += data_source_count * 1.5
        if self.real_time_updates:
            estimated_memory += 5.0
            
        self.memory_usage = flt(estimated_memory, 2)
        
        # Generate optimization suggestions
        suggestions = []
        if widget_count > 12:
            suggestions.append("Consider reducing the number of widgets")
        if self.refresh_interval < 30:
            suggestions.append("Increase refresh interval for better performance")
        if not self.caching_strategy or self.caching_strategy == "None":
            suggestions.append("Enable caching for better performance")
        if self.performance_score < 7:
            suggestions.append("Dashboard complexity is high - consider optimization")
            
        self.optimization_suggestions = "; ".join(suggestions) if suggestions else "Dashboard is well optimized"
        
    def update_metadata(self):
        """Update metadata fields"""
        self.modified_by = frappe.session.user
        self.modified_date = get_datetime()
        
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get complete dashboard configuration for frontend"""
        return {
            'basic_info': {
                'name': self.name,
                'dashboard_name': self.dashboard_name,
                'dashboard_name_ar': self.dashboard_name_ar,
                'category': self.dashboard_category,
                'business_area': self.business_area,
                'description': self.description,
                'description_ar': self.description_ar
            },
            'layout': {
                'layout_type': self.layout_type,
                'grid_columns': self.grid_columns,
                'grid_rows': self.grid_rows,
                'responsive_breakpoints': json.loads(self.responsive_breakpoints) if self.responsive_breakpoints else {},
                'mobile_layout': self.mobile_layout,
                'rtl_mode': self.rtl_mode,
                'arabic_font_family': self.arabic_font_family
            },
            'widgets': [widget.as_dict() for widget in self.widgets] if self.widgets else [],
            'interactivity': {
                'drill_down_enabled': self.drill_down_enabled,
                'real_time_updates': self.real_time_updates,
                'refresh_interval': self.refresh_interval,
                'hover_effects': self.hover_effects,
                'filter_sync': self.filter_sync
            },
            'data_sources': {
                'primary': self.primary_data_source,
                'secondary': [ds.as_dict() for ds in self.secondary_data_sources] if self.secondary_data_sources else [],
                'refresh_mode': self.data_refresh_mode,
                'cache_duration': self.cache_duration
            },
            'visualization': {
                'chart_library': self.chart_library,
                'color_scheme': self.color_scheme,
                'theme': self.theme,
                'animation_enabled': self.animation_enabled,
                'transition_effects': self.transition_effects,
                'chart_tooltips': self.chart_tooltips
            },
            'performance': {
                'performance_score': self.performance_score,
                'load_time': self.load_time,
                'memory_usage': self.memory_usage,
                'caching_strategy': self.caching_strategy,
                'background_processing': self.background_processing
            },
            'permissions': {
                'public_access': self.public_access,
                'embed_enabled': self.embed_enabled,
                'api_access': self.api_access
            }
        }
        
    def get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        if not self.widgets:
            return {}
            
        widget = None
        for w in self.widgets:
            if w.widget_id == widget_id:
                widget = w
                break
                
        if not widget:
            frappe.throw(_("Widget not found: {0}").format(widget_id))
            
        # Get data based on widget type and data source
        data = {}
        
        if widget.widget_type == "Chart":
            data = self._get_chart_data(widget)
        elif widget.widget_type == "KPI":
            data = self._get_kpi_data(widget)
        elif widget.widget_type == "Table":
            data = self._get_table_data(widget)
        elif widget.widget_type == "Gauge":
            data = self._get_gauge_data(widget)
        elif widget.widget_type == "Timeline":
            data = self._get_timeline_data(widget)
            
        return data
        
    def _get_chart_data(self, widget) -> Dict[str, Any]:
        """Get chart data for widget"""
        # Implementation would fetch data from configured data source
        # and format it for the specified chart type
        return {
            'type': widget.chart_type,
            'data': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                'datasets': [{
                    'label': widget.widget_title,
                    'data': [10, 20, 30, 40, 50],
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)'
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': widget.widget_title_ar if frappe.local.lang == 'ar' else widget.widget_title
                    }
                }
            }
        }
        
    def _get_kpi_data(self, widget) -> Dict[str, Any]:
        """Get KPI data for widget"""
        return {
            'value': 1250.75,
            'format': 'currency',
            'currency': 'OMR',
            'trend': {
                'direction': 'up',
                'percentage': 12.5,
                'color': 'success'
            },
            'target': 1500,
            'achievement': 83.4
        }
        
    def _get_table_data(self, widget) -> Dict[str, Any]:
        """Get table data for widget"""
        return {
            'columns': ['Service', 'Count', 'Revenue'],
            'rows': [
                ['Oil Change', 25, 375.00],
                ['Brake Repair', 12, 1200.00],
                ['Engine Tune-up', 8, 1600.00]
            ]
        }
        
    def _get_gauge_data(self, widget) -> Dict[str, Any]:
        """Get gauge data for widget"""
        return {
            'value': 75,
            'min': 0,
            'max': 100,
            'unit': '%',
            'ranges': [
                {'from': 0, 'to': 50, 'color': 'red'},
                {'from': 50, 'to': 80, 'color': 'yellow'},
                {'from': 80, 'to': 100, 'color': 'green'}
            ]
        }
        
    def _get_timeline_data(self, widget) -> Dict[str, Any]:
        """Get timeline data for widget"""
        return {
            'events': [
                {
                    'time': get_datetime(),
                    'title': 'Service Order Completed',
                    'description': 'SO-2024-001 completed by Ahmed Al-Rashid',
                    'type': 'success'
                },
                {
                    'time': get_datetime() - timedelta(minutes=30),
                    'title': 'New Customer Registration',
                    'description': 'Customer CU-2024-015 registered',
                    'type': 'info'
                }
            ]
        }
        
    def export_dashboard(self, format_type: str = "json") -> Dict[str, Any]:
        """Export dashboard configuration"""
        config = self.get_dashboard_config()
        
        if format_type == "json":
            return config
        elif format_type == "yaml":
            import yaml
            return yaml.dump(config, default_flow_style=False)
        else:
            frappe.throw(_("Unsupported export format: {0}").format(format_type))
            
    def clone_dashboard(self, new_name: str) -> str:
        """Clone dashboard with new name"""
        new_dashboard = frappe.copy_doc(self)
        new_dashboard.dashboard_name = new_name
        new_dashboard.dashboard_name_ar = f"{self.dashboard_name_ar} (نسخة)"
        new_dashboard.status = "Draft"
        new_dashboard.is_default = 0
        new_dashboard.insert()
        
        return new_dashboard.name


# WhiteListed API Methods
@frappe.whitelist()
def get_dashboard_config(dashboard_name: str):
    """Get dashboard configuration for frontend"""
    dashboard = frappe.get_doc("Interactive Dashboard", dashboard_name)
    return dashboard.get_dashboard_config()


@frappe.whitelist()
def get_widget_data(dashboard_name: str, widget_id: str):
    """Get data for specific widget"""
    dashboard = frappe.get_doc("Interactive Dashboard", dashboard_name)
    return dashboard.get_widget_data(widget_id)


@frappe.whitelist()
def refresh_dashboard_data(dashboard_name: str):
    """Refresh all dashboard data"""
    dashboard = frappe.get_doc("Interactive Dashboard", dashboard_name)
    
    # Clear cache for this dashboard
    cache_key = f"dashboard_data_{dashboard_name}"
    frappe.cache().delete_value(cache_key)
    
    return {"status": "refreshed", "timestamp": get_datetime()}


@frappe.whitelist()
def get_dashboard_list(category: str = None, business_area: str = None):
    """Get list of available dashboards"""
    filters = {"is_active": 1, "status": "Active"}
    
    if category:
        filters["dashboard_category"] = category
    if business_area:
        filters["business_area"] = business_area
        
    dashboards = frappe.get_list(
        "Interactive Dashboard",
        filters=filters,
        fields=["name", "dashboard_name", "dashboard_name_ar", "dashboard_category", 
                "business_area", "performance_score", "is_default"],
        order_by="dashboard_name"
    )
    
    return dashboards


@frappe.whitelist()
def export_dashboard(dashboard_name: str, format_type: str = "json"):
    """Export dashboard configuration"""
    dashboard = frappe.get_doc("Interactive Dashboard", dashboard_name)
    return dashboard.export_dashboard(format_type)


@frappe.whitelist()
def clone_dashboard(dashboard_name: str, new_name: str):
    """Clone existing dashboard"""
    dashboard = frappe.get_doc("Interactive Dashboard", dashboard_name)
    return dashboard.clone_dashboard(new_name)


@frappe.whitelist()
def get_dashboard_templates():
    """Get available dashboard templates"""
    templates = [
        {
            "name": "executive_template",
            "title": "Executive Dashboard",
            "title_ar": "لوحة تحكم تنفيذية",
            "category": "Executive",
            "description": "High-level KPIs and business metrics",
            "widgets": ["revenue_chart", "profit_margin", "customer_satisfaction", "market_share"]
        },
        {
            "name": "operational_template",
            "title": "Operational Dashboard",
            "title_ar": "لوحة تحكم تشغيلية",
            "category": "Operational",
            "description": "Service operations and technician performance",
            "widgets": ["service_orders", "technician_utilization", "equipment_status", "queue_management"]
        },
        {
            "name": "financial_template",
            "title": "Financial Dashboard",
            "title_ar": "لوحة تحكم مالية",
            "category": "Financial",
            "description": "Revenue, costs, and financial analysis",
            "widgets": ["revenue_trend", "cost_analysis", "profit_loss", "cash_flow"]
        }
    ]
    
    return templates


@frappe.whitelist()
def create_from_template(template_name: str, dashboard_name: str):
    """Create dashboard from template"""
    templates = get_dashboard_templates()
    template = next((t for t in templates if t["name"] == template_name), None)
    
    if not template:
        frappe.throw(_("Template not found: {0}").format(template_name))
        
    # Create new dashboard from template
    dashboard = frappe.new_doc("Interactive Dashboard")
    dashboard.dashboard_name = dashboard_name
    dashboard.dashboard_name_ar = f"{dashboard_name} (عربي)"
    dashboard.dashboard_category = template["category"]
    dashboard.description = template["description"]
    dashboard.status = "Draft"
    
    # Add template-specific configuration
    # This would be expanded based on actual template requirements
    
    dashboard.insert()
    return dashboard.name 