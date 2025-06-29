# pylint: disable=no-member
"""Dashboard Widget DocType Controller"""

import frappe
from frappe import _
from frappe.model.document import Document


class DashboardWidget(Document):
    """Controller for Dashboard Widget child table"""

    def validate(self):
        """Validate widget configuration"""
        if not self.widget_id:
            frappe.throw(_("Widget ID is required"))
        if not self.widget_title:
            frappe.throw(_("Widget Title is required"))
        if self.data_source == "KPI" and not self.kpi_code:
            frappe.throw(_("KPI Code is required for KPI widgets"))
        if self.widget_type == "Chart" and not self.chart_type:
            frappe.throw(_("Chart Type is required for Chart widgets"))
