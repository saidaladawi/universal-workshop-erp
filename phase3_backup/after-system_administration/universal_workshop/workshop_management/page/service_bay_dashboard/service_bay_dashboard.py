# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
    """Get context for service bay dashboard page"""

    # Check permissions
    if not frappe.has_permission("Service Bay", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    context.title = "Service Bay Dashboard - لوحة مراقبة أقسام الخدمة"
    context.show_sidebar = False

    # Get initial dashboard data
    from universal_workshop.workshop_management.utils.bay_monitoring import (
        get_service_bay_dashboard,
    )

    context.dashboard_data = get_service_bay_dashboard()

    return context
