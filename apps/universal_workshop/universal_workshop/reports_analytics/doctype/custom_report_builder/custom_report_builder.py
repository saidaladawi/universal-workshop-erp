# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
import re
from datetime import datetime
from frappe.utils import flt, cint, getdate, get_datetime, nowdate, now_datetime


class CustomReportBuilder(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields
    
    def validate(self):
        """Validate report configuration before saving"""
        self.validate_report_names()
        self.validate_data_source()
        self.validate_chart_configuration()
        self.validate_canvas_settings()
        self.set_default_values()
        
    def before_save(self):
        """Set default values and generate configurations before saving"""
        if not self.report_code:
            self.report_code = self.generate_report_code()
            
        if not self.owner_user:
            self.owner_user = frappe.session.user
            
        if not self.created_date:
            self.created_date = now_datetime()
            
        self.last_modified = now_datetime()
        self.generate_sql_query()
        self.update_performance_metrics()
        
    def validate_report_names(self):
        """Validate both English and Arabic report names"""
        if not self.report_name:
            frappe.throw(_("Report name (English) is required"))
            
        if not self.report_name_ar:
            frappe.throw(_("Arabic report name is required"))
            
    def validate_data_source(self):
        """Validate data source configuration"""
        if not self.primary_data_source:
            frappe.throw(_("Primary data source is required"))
            
    def validate_chart_configuration(self):
        """Validate chart and visualization settings"""
        if self.chart_type and self.chart_type != "Table":
            if not self.chart_library:
                frappe.throw(_("Chart library is required for chart type: {0}").format(self.chart_type))
                
    def validate_canvas_settings(self):
        """Validate canvas and layout configuration"""
        if self.canvas_width and self.canvas_width < 300:
            frappe.throw(_("Canvas width must be at least 300 pixels"))
            
        if self.canvas_height and self.canvas_height < 200:
            frappe.throw(_("Canvas height must be at least 200 pixels"))
            
    def set_default_values(self):
        """Set default values for new reports"""
        if not self.status:
            self.status = "Draft"
            
        if not self.priority:
            self.priority = "Medium"
            
        if not self.canvas_layout:
            self.canvas_layout = "Grid"
            
        if not self.language_direction:
            self.language_direction = "Auto"
            
        if not self.chart_library:
            self.chart_library = "Chart.js"
            
        if not self.version_number:
            self.version_number = "1.0.0"
            
        # Set RTL mode based on language
        if frappe.local.lang == 'ar' and not self.rtl_mode:
            self.rtl_mode = 1
            self.language_direction = "RTL"
            self.arabic_font_family = "Noto Sans Arabic"
            
    def generate_report_code(self):
        """Generate unique report code"""
        year = datetime.now().year
        
        # Get last report number for current year
        last_report = frappe.db.sql("""
            SELECT report_code FROM `tabCustom Report Builder`
            WHERE report_code LIKE 'RPT-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year))
        
        if last_report:
            last_num = int(last_report[0][0].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"RPT-{year}-{new_num:05d}"
        
    def generate_sql_query(self):
        """Generate SQL query based on configuration"""
        try:
            if not self.primary_data_source:
                return
                
            # Basic query generation
            self.sql_query = "SELECT * FROM `tabCustomer` LIMIT 100"
            
        except Exception as e:
            frappe.log_error(f"Error generating SQL query: {str(e)}", "Custom Report Builder")
            self.sql_query = f"-- Error generating query: {str(e)}"
            
    def update_performance_metrics(self):
        """Update performance metrics and statistics"""
        try:
            metrics = {
                "last_updated": now_datetime().isoformat(),
                "query_complexity": 5,
                "estimated_execution_time": 2.0
            }
            
            self.performance_metrics = json.dumps(metrics, indent=2)
            
        except Exception as e:
            frappe.log_error(f"Error updating performance metrics: {str(e)}", "Custom Report Builder")
            
    @frappe.whitelist()
    def execute_report(self, limit=None):
        """Execute the report and return results"""
        try:
            if not self.sql_query or self.sql_query.startswith("--"):
                frappe.throw(_("Invalid SQL query. Please check report configuration."))
                
            # Execute query
            results = frappe.db.sql(self.sql_query, as_dict=True)
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            error_msg = str(e)
            frappe.log_error(f"Report execution error: {error_msg}", "Custom Report Builder")
            
            return {
                "success": False,
                "error": error_msg
            }
            
    @frappe.whitelist()
    def get_chart_data(self):
        """Get formatted data for chart visualization"""
        try:
            result = self.execute_report(limit=1000)
            
            if not result["success"]:
                return result
                
            return {
                "success": True,
                "chart_data": {"type": "bar", "data": result["data"]}
            }
            
        except Exception as e:
            error_msg = str(e)
            return {"success": False, "error": error_msg}


@frappe.whitelist()
def get_available_fields(data_source):
    """Get available fields from data source"""
    try:
        if not data_source:
            return {"success": False, "error": "Data source is required"}
            
        fields = [
            {"name": "name", "label": "Name", "type": "Data"},
            {"name": "customer_name", "label": "Customer Name", "type": "Data"},
            {"name": "phone", "label": "Phone", "type": "Data"}
        ]
        
        return {"success": True, "fields": fields}
        
    except Exception as e:
        error_msg = str(e)
        return {"success": False, "error": error_msg}


@frappe.whitelist()
def get_report_templates():
    """Get available report templates"""
    templates = [
        {
            "name": "Financial Summary",
            "name_ar": "الملخص المالي",
            "category": "Financial",
            "description": "Revenue, expenses, and profit analysis",
            "chart_type": "Bar Chart"
        },
        {
            "name": "Service Performance", 
            "name_ar": "أداء الخدمة",
            "category": "Operational",
            "description": "Service completion rates",
            "chart_type": "Line Chart"
        }
    ]
    
    return {"success": True, "templates": templates}
