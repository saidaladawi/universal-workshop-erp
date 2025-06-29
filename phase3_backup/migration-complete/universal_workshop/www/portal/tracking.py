# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Service Tracking Page Controller
Handles service tracking page routing and context
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer


def get_context(context):
    """
    Get context for service tracking page

    Args:
        context: Frappe page context

    Returns:
        dict: Page context with tracking data
    """
    # Check if customer is authenticated
    customer = get_current_customer()

    if not customer:
        # Redirect to login page if not authenticated
        frappe.local.flags.redirect_location = "/portal/login"
        raise frappe.Redirect

    # Get active service requests
    from universal_workshop.customer_portal.tracking import get_active_service_requests

    active_requests_result = get_active_service_requests()

    # Get service history with feedback
    from universal_workshop.customer_portal.tracking import get_service_history_with_feedback

    history_result = get_service_history_with_feedback()

    context.update(
        {
            "customer": customer,
            "active_requests": (
                active_requests_result.get("active_requests", [])
                if active_requests_result.get("success")
                else []
            ),
            "service_history": (
                history_result.get("service_history", []) if history_result.get("success") else []
            ),
            "total_active": (
                active_requests_result.get("total_active", 0)
                if active_requests_result.get("success")
                else 0
            ),
            "total_history": (
                history_result.get("total_services", 0) if history_result.get("success") else 0
            ),
            "page_title": _("Service Tracking"),
            "page_title_ar": "تتبع الخدمة",
            "show_sidebar": True,
            "portal_language": frappe.local.lang,
            "is_rtl": frappe.local.lang == "ar",
            "active_page": "tracking",
        }
    )

    return context
