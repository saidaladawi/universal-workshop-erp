# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document


class DashboardWidgetConfiguration(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate widget configuration before saving"""
        self.validate_widget_config()
        self.validate_position()
        self.validate_refresh_settings()
        self.set_default_values()

    def validate_widget_config(self):
        """Validate widget configuration JSON"""
        if self.widget_config:
            try:
                config = json.loads(self.widget_config)
                self.validate_config_by_type(config)
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON in widget configuration"))

    def validate_config_by_type(self, config):
        """Validate configuration based on widget type"""
        required_fields = self.get_required_config_fields()

        for field in required_fields:
            if field not in config:
                frappe.throw(_("Missing required configuration field: {0}").format(field))

    def get_required_config_fields(self):
        """Get required configuration fields based on widget type"""
        config_map = {
            "Chart": ["chart_type", "x_axis", "y_axis"],
            "KPI Card": ["metric_field", "format_type"],
            "Table": ["columns", "page_size"],
            "Gauge": ["min_value", "max_value", "target_value"],
            "Calendar": ["date_field", "title_field"],
            "Map": ["latitude_field", "longitude_field"],
            "Text": ["text_content"],
            "Image": ["image_url"],
            "Iframe": ["iframe_url"],
            "Custom HTML": ["html_content"],
        }

        return config_map.get(self.widget_type, [])

    def validate_position(self):
        """Validate widget position and size"""
        if self.position_x < 0:
            frappe.throw(_("Position X cannot be negative"))
        if self.position_y < 0:
            frappe.throw(_("Position Y cannot be negative"))
        if self.width <= 0:
            frappe.throw(_("Width must be positive"))
        if self.height <= 0:
            frappe.throw(_("Height must be positive"))

    def validate_refresh_settings(self):
        """Validate refresh settings"""
        if self.auto_refresh and self.refresh_interval <= 0:
            frappe.throw(_("Refresh interval must be positive when auto refresh is enabled"))

    def set_default_values(self):
        """Set default values for widget"""
        if not self.widget_id:
            self.widget_id = self.generate_widget_id()

        if not self.widget_title_ar and self.widget_title:
            self.widget_title_ar = self.widget_title  # Placeholder for translation

        if not self.background_color:
            self.background_color = self.get_default_color()

        self.last_updated = frappe.utils.now()

    def generate_widget_id(self):
        """Generate unique widget ID"""
        import uuid

        return f"widget_{uuid.uuid4().hex[:8]}"

    def get_default_color(self):
        """Get default background color based on widget type"""
        color_map = {
            "Chart": "#ffffff",
            "KPI Card": "#f8f9fa",
            "Table": "#ffffff",
            "Gauge": "#f8f9fa",
            "Calendar": "#ffffff",
            "Map": "#ffffff",
            "Text": "#f8f9fa",
            "Image": "#ffffff",
            "Iframe": "#ffffff",
            "Custom HTML": "#ffffff",
        }

        return color_map.get(self.widget_type, "#ffffff")

    def get_widget_data(self):
        """Get widget data from data source"""
        if not self.data_source:
            return {}

        try:
            data_source_doc = frappe.get_doc("Data Source Mapping", self.data_source)
            return data_source_doc.get_data()
        except Exception as e:
            frappe.log_error(f"Error loading widget data: {str(e)}")
            return {}

    def render_widget(self):
        """Render widget HTML based on type and configuration"""
        widget_data = self.get_widget_data()
        config = json.loads(self.widget_config or "{}")

        render_methods = {
            "Chart": self.render_chart_widget,
            "KPI Card": self.render_kpi_widget,
            "Table": self.render_table_widget,
            "Gauge": self.render_gauge_widget,
            "Calendar": self.render_calendar_widget,
            "Map": self.render_map_widget,
            "Text": self.render_text_widget,
            "Image": self.render_image_widget,
            "Iframe": self.render_iframe_widget,
            "Custom HTML": self.render_html_widget,
        }

        render_method = render_methods.get(self.widget_type)
        if render_method:
            return render_method(widget_data, config)
        else:
            return f"<div>Unsupported widget type: {self.widget_type}</div>"

    def render_chart_widget(self, data, config):
        """Render chart widget"""
        return f"""
        <div class="chart-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <canvas id="chart_{self.widget_id}"></canvas>
        </div>
        """

    def render_kpi_widget(self, data, config):
        """Render KPI card widget"""
        value = data.get(config.get("metric_field", ""), 0)
        format_type = config.get("format_type", "number")

        return f"""
        <div class="kpi-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="kpi-value">{self.format_value(value, format_type)}</div>
        </div>
        """

    def render_table_widget(self, data, config):
        """Render table widget"""
        columns = config.get("columns", [])
        rows = data.get("rows", [])

        # Build table header
        header_cells = "".join([f"<th>{col}</th>" for col in columns])

        # Build table rows
        table_rows = []
        for row in rows:
            row_cells = "".join([f'<td>{row.get(col, "")}</td>' for col in columns])
            table_rows.append(f"<tr>{row_cells}</tr>")

        table_body = "".join(table_rows)

        table_html = f"""
        <div class="table-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <table class="table table-sm">
                <thead>
                    <tr>
                        {header_cells}
                    </tr>
                </thead>
                <tbody>
                    {table_body}
                </tbody>
            </table>
        </div>
        """

        return table_html

    def render_gauge_widget(self, data, config):
        """Render gauge widget"""
        return f"""
        <div class="gauge-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="gauge-container" id="gauge_{self.widget_id}"></div>
        </div>
        """

    def render_calendar_widget(self, data, config):
        """Render calendar widget"""
        return f"""
        <div class="calendar-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="calendar-container" id="calendar_{self.widget_id}"></div>
        </div>
        """

    def render_map_widget(self, data, config):
        """Render map widget"""
        return f"""
        <div class="map-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="map-container" id="map_{self.widget_id}" style="height: 300px;"></div>
        </div>
        """

    def render_text_widget(self, data, config):
        """Render text widget"""
        text_content = config.get("text_content", "")
        return f"""
        <div class="text-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="text-content">{text_content}</div>
        </div>
        """

    def render_image_widget(self, data, config):
        """Render image widget"""
        image_url = config.get("image_url", "")
        return f"""
        <div class="image-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <img src="{image_url}" alt="{self.widget_title}" class="img-fluid">
        </div>
        """

    def render_iframe_widget(self, data, config):
        """Render iframe widget"""
        iframe_url = config.get("iframe_url", "")
        return f"""
        <div class="iframe-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <iframe src="{iframe_url}" width="100%" height="300" frameborder="0"></iframe>
        </div>
        """

    def render_html_widget(self, data, config):
        """Render custom HTML widget"""
        html_content = config.get("html_content", "")
        return f"""
        <div class="html-widget" id="{self.widget_id}">
            <h6>{self.widget_title}</h6>
            <div class="html-content">{html_content}</div>
        </div>
        """

    def format_value(self, value, format_type):
        """Format value based on format type"""
        try:
            if format_type == "currency":
                return f"OMR {float(value):,.3f}"
            elif format_type == "percentage":
                return f"{float(value):.1f}%"
            elif format_type == "number":
                return f"{float(value):,.0f}"
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)


@frappe.whitelist()
def get_widget_preview(widget_config):
    """Get widget preview HTML"""
    try:
        doc = frappe.get_doc(json.loads(widget_config))
        return {"success": True, "html": doc.render_widget()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_widget_defaults(widget_type):
    """Get default configuration for widget type"""
    defaults = {
        "Chart": {
            "default_width": 6,
            "default_height": 4,
            "default_config": {"chart_type": "line", "x_axis": "date", "y_axis": "value"},
        },
        "KPI Card": {
            "default_width": 3,
            "default_height": 2,
            "default_config": {"metric_field": "value", "format_type": "number"},
        },
        "Table": {
            "default_width": 8,
            "default_height": 4,
            "default_config": {"columns": ["name", "value"], "page_size": 10},
        },
        "Gauge": {
            "default_width": 4,
            "default_height": 3,
            "default_config": {"min_value": 0, "max_value": 100, "target_value": 80},
        },
    }

    return defaults.get(
        widget_type, {"default_width": 4, "default_height": 3, "default_config": {}}
    )
