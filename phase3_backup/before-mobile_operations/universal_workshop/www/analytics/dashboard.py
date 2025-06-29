"""Analytics Dashboard Web Page Backend"""

import frappe
from frappe import _


def get_context(context):
    """Get context for dashboard page"""

    # Check permissions
    if not frappe.has_permission("Dashboard Config", "read"):
        frappe.throw(_("Not permitted to access analytics dashboard"), frappe.PermissionError)

    # Get user's default dashboard
    user_roles = frappe.get_roles(frappe.session.user)

    # Determine primary role for dashboard selection
    role_priority = ["Workshop Manager", "System Manager", "Workshop User"]
    primary_role = next(
        (role for role in role_priority if role in user_roles),
        user_roles[0] if user_roles else "Guest",
    )

    # Get default dashboard for user's role
    dashboard_name = frappe.db.get_value(
        "Dashboard Config", {"target_role": primary_role, "is_default": 1, "is_active": 1}, "name"
    )

    # Get available dashboards for dropdown
    available_dashboards = frappe.get_list(
        "Dashboard Config",
        filters={"is_active": 1},
        fields=["name", "dashboard_title", "dashboard_title_ar"],
        order_by="dashboard_title",
    )

    context.update(
        {
            "current_dashboard": dashboard_name or "executive_overview",
            "available_dashboards": available_dashboards,
            "user_role": primary_role,
            "page_title": _("Analytics Dashboard"),
            "page_title_ar": "لوحة التحليلات",
        }
    )

    return context
