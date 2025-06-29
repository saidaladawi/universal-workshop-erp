import frappe
from frappe import _


def get_context(context):
    """Get context for onboarding page"""

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # Check if setup is already complete
    try:
        from universal_workshop.core.boot.boot_manager import check_setup_status
        setup_status = check_setup_status()

        if not setup_status.get("needs_onboarding"):
            frappe.local.flags.redirect_location = "/app"
            raise frappe.Redirect

        # Prepare context
        context.update({
            "title": _("Workshop Setup"),
            "setup_status": setup_status,
            "has_license_data": setup_status.get("has_license"),
            "license_data": setup_status.get("license_data", {}),
            "show_license_info": True if setup_status.get("license_data") else False
        })

    except Exception as e:
        frappe.log_error(f"Error in onboarding context: {e}")
        context.update({
            "title": _("Workshop Setup"),
            "error": str(e),
            "setup_status": {"needs_onboarding": True}
        })
