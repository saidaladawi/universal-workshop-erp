import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta

class FinancialDashboardConfig(Document):
    # pylint: disable=no-member
    
    def validate(self):
        """Validate financial dashboard configuration"""
        self.validate_widget_settings()
        self.validate_chart_settings()
        self.validate_access_control()
        self.set_default_values()
    
    def validate_widget_settings(self):
        """Validate widget configuration"""
        if not any([
            self.revenue_widget, self.expense_widget, self.profit_widget,
            self.cash_flow_widget, self.vat_widget, self.receivables_widget,
            self.payables_widget, self.inventory_widget
        ]):
            frappe.throw(_("At least one widget must be enabled"))
    
    def validate_chart_settings(self):
        """Validate chart configuration"""
        chart_types = ["Line Chart", "Bar Chart", "Area Chart", "Pie Chart", "Waterfall Chart"]
        
        if self.revenue_chart_type and self.revenue_chart_type not in chart_types:
            frappe.throw(_("Invalid revenue chart type"))
        
        if self.expense_chart_type and self.expense_chart_type not in chart_types:
            frappe.throw(_("Invalid expense chart type"))
        
        if self.profit_chart_type and self.profit_chart_type not in chart_types:
            frappe.throw(_("Invalid profit chart type"))
        
        if self.cash_flow_chart_type and self.cash_flow_chart_type not in chart_types:
            frappe.throw(_("Invalid cash flow chart type"))
    
    def validate_access_control(self):
        """Validate access control settings"""
        if self.restrict_access and not self.visible_to_roles:
            frappe.throw(_("Visible roles must be specified when access is restricted"))
    
    def set_default_values(self):
        """Set default values before saving"""
        if not self.dashboard_status:
            self.dashboard_status = "Draft"
        
        if not self.refresh_interval:
            self.refresh_interval = "15 minutes"
        
        if not self.default_period:
            self.default_period = "This Month"
        
        if not self.currency_display:
            self.currency_display = "OMR"
        
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.creation_date:
            self.creation_date = frappe.utils.now()
    
    @frappe.whitelist()
    def get_dashboard_data(self, period=None):
        """Get dashboard data for specified period"""
        if not period:
            period = self.default_period
        
        try:
            data = {
                "period": period,
                "currency": self.currency_display,
                "widgets": {},
                "charts": {}
            }
            
            # Get widget data
            if self.revenue_widget:
                data["widgets"]["revenue"] = self.get_revenue_data(period)
            
            if self.expense_widget:
                data["widgets"]["expense"] = self.get_expense_data(period)
            
            if self.profit_widget:
                data["widgets"]["profit"] = self.get_profit_data(period)
            
            if self.vat_widget:
                data["widgets"]["vat"] = self.get_vat_data(period)
            
            # Get chart data
            if self.revenue_chart_type:
                data["charts"]["revenue"] = self.get_revenue_chart_data(period)
            
            if self.expense_chart_type:
                data["charts"]["expense"] = self.get_expense_chart_data(period)
            
            return data
            
        except Exception as e:
            return {"error": f"Failed to get dashboard data: {str(e)}"}
    
    def get_revenue_data(self, period):
        """Get revenue data for widget"""
        # Placeholder implementation
        return {
            "current": 15000.0,
            "previous": 12000.0,
            "change_percentage": 25.0,
            "trend": "up"
        }
    
    def get_expense_data(self, period):
        """Get expense data for widget"""
        # Placeholder implementation
        return {
            "current": 8000.0,
            "previous": 7500.0,
            "change_percentage": 6.67,
            "trend": "up"
        }
    
    def get_profit_data(self, period):
        """Get profit data for widget"""
        # Placeholder implementation
        return {
            "current": 7000.0,
            "previous": 4500.0,
            "change_percentage": 55.56,
            "trend": "up"
        }
    
    def get_vat_data(self, period):
        """Get VAT data for widget"""
        # Placeholder implementation
        return {
            "collected": 750.0,
            "paid": 400.0,
            "outstanding": 350.0,
            "compliance_status": "compliant"
        }
    
    def get_revenue_chart_data(self, period):
        """Get revenue chart data"""
        # Placeholder implementation
        return {
            "chart_type": self.revenue_chart_type,
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [12000, 13500, 14200, 15800, 16500, 15000]
        }
    
    def get_expense_chart_data(self, period):
        """Get expense chart data"""
        # Placeholder implementation
        return {
            "chart_type": self.expense_chart_type,
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [7000, 7200, 7800, 8200, 7900, 8000]
        }
    
    @frappe.whitelist()
    def test_dashboard_access(self, user=None):
        """Test dashboard access for user"""
        if not user:
            user = frappe.session.user
        
        if not self.restrict_access:
            return {"access": "allowed", "reason": "No access restrictions"}
        
        user_roles = frappe.get_roles(user)
        visible_roles = [role.strip() for role in self.visible_to_roles.split(',')]
        
        has_access = any(role in user_roles for role in visible_roles)
        
        return {
            "access": "allowed" if has_access else "denied",
            "user_roles": user_roles,
            "visible_roles": visible_roles,
            "reason": "User has required role" if has_access else "User lacks required role"
        }
    
    def before_save(self):
        """Actions before saving"""
        self.update_dashboard_status()
    
    def update_dashboard_status(self):
        """Update dashboard status based on configuration"""
        if self.is_active and self.dashboard_status == "Draft":
            self.dashboard_status = "Published" 