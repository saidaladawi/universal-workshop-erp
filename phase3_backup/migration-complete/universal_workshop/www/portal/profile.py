# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Profile Page Controller
Handles profile management page routing and context
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer


def get_context(context):
    """
    Get context for profile management page

    Args:
        context: Frappe page context

    Returns:
        dict: Page context with customer profile data
    """
    # Check if customer is authenticated
    customer = get_current_customer()

    if not customer:
        # Redirect to login page if not authenticated
        frappe.local.flags.redirect_location = "/portal/login"
        raise frappe.Redirect

    # Get customer profile data
    from universal_workshop.customer_portal.profile import get_customer_profile

    profile_result = get_customer_profile()

    if not profile_result.get("success"):
        frappe.throw(_("Error loading profile data"))

    context.update(
        {
            "customer": customer,
            "profile_data": profile_result.get("profile", {}),
            "page_title": _("My Profile"),
            "page_title_ar": "ملفي الشخصي",
            "show_sidebar": True,
            "portal_language": frappe.local.lang,
            "is_rtl": frappe.local.lang == "ar",
            "active_page": "profile",
        }
    )

    return context
