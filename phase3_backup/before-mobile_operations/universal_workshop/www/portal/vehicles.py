# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Vehicles Page Controller
Handles vehicle management page routing and context
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer


def get_context(context):
    """
    Get context for vehicles management page

    Args:
        context: Frappe page context

    Returns:
        dict: Page context with customer vehicles data
    """
    # Check if customer is authenticated
    customer = get_current_customer()

    if not customer:
        # Redirect to login page if not authenticated
        frappe.local.flags.redirect_location = "/portal/login"
        raise frappe.Redirect

    # Get customer vehicles data
    from universal_workshop.customer_portal.profile import get_customer_vehicles

    vehicles_result = get_customer_vehicles()

    if not vehicles_result.get("success"):
        frappe.throw(_("Error loading vehicles data"))

    context.update(
        {
            "customer": customer,
            "vehicles": vehicles_result.get("vehicles", []),
            "total_vehicles": vehicles_result.get("total_vehicles", 0),
            "page_title": _("My Vehicles"),
            "page_title_ar": "مركباتي",
            "show_sidebar": True,
            "portal_language": frappe.local.lang,
            "is_rtl": frappe.local.lang == "ar",
            "active_page": "vehicles",
        }
    )

    return context
