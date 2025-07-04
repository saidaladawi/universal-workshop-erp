import frappe
from frappe import _


def get_context(context):
    """Get context for mobile receiving page"""

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to access mobile receiving interface"), frappe.PermissionError)

    # Check user permissions
    if not frappe.has_permission("Purchase Receipt", "create"):
        frappe.throw(
            _("You don't have permission to create Purchase Receipts"), frappe.PermissionError
        )

    # Set page context
    context.update(
        {
            "title": _("Mobile Receiving Interface"),
            "no_cache": 1,
            "show_sidebar": False,
            "no_breadcrumbs": True,
        }
    )

    # Get user's default company and warehouse
    user_defaults = frappe.defaults.get_user_defaults(frappe.session.user)

    context.update(
        {
            "user_company": user_defaults.get("Company")
            or frappe.defaults.get_global_default("company"),
            "user_warehouse": user_defaults.get("Warehouse"),
            "user_name": frappe.get_value("User", frappe.session.user, "full_name")
            or frappe.session.user,
            "current_user": frappe.session.user,
        }
    )

    return context
