# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Booking Page Controller
Handles appointment booking page routing and context
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer


def get_context(context):
    """
    Get context for appointment booking page

    Args:
        context: Frappe page context

    Returns:
        dict: Page context with booking data
    """
    # Check if customer is authenticated
    customer = get_current_customer()

    if not customer:
        # Redirect to login page if not authenticated
        frappe.local.flags.redirect_location = "/portal/login"
        raise frappe.Redirect

    # Get customer vehicles for booking
    from universal_workshop.customer_portal.profile import get_customer_vehicles

    vehicles_result = get_customer_vehicles()

    # Get available services for booking
    from universal_workshop.customer_portal.booking import get_available_services

    services_result = get_available_services()

    context.update(
        {
            "customer": customer,
            "vehicles": (
                vehicles_result.get("vehicles", []) if vehicles_result.get("success") else []
            ),
            "services": (
                services_result.get("grouped_services", {})
                if services_result.get("success")
                else {}
            ),
            "page_title": _("Book Appointment"),
            "page_title_ar": "حجز موعد",
            "show_sidebar": True,
            "portal_language": frappe.local.lang,
            "is_rtl": frappe.local.lang == "ar",
            "active_page": "booking",
        }
    )

    return context
