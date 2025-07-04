"""
API Performance Dashboard for Vehicle Make/Model System
Real-time monitoring and management interface
"""

import frappe
from frappe import _


def get_context(context):
    """Get dashboard context data"""
    context.no_cache = 1
    context.title = _("Vehicle API Performance Dashboard")

    # Get current user permissions
    if not frappe.has_permission("Vehicle", "read"):
        frappe.throw(_("Not permitted to access Vehicle API Dashboard"))

    # Dashboard data will be loaded via AJAX calls
    context.dashboard_data = {
        "page_title": _("Vehicle API Performance Dashboard"),
        "refresh_interval": 30000,  # 30 seconds
        "show_live_tests": frappe.has_permission("Vehicle", "write"),
    }

    return context
