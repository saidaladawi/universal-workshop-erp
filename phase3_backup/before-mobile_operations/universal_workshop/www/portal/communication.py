# -*- coding: utf-8 -*-
"""
Customer Portal Communication Preferences Page
"""

import frappe
from frappe import _
import json
from universal_workshop.customer_portal.auth import require_customer_auth


@require_customer_auth
def get_context(context):
    """Get context for communication preferences page"""
    customer_id = frappe.session.user

    try:
        # Get current communication preferences
        from universal_workshop.customer_portal.communication_integration import (
            get_communication_preferences,
        )

        prefs_result = get_communication_preferences(customer_id)

        if prefs_result.get("success"):
            preferences = prefs_result["preferences"]
        else:
            preferences = {
                "preferred_language": "ar",
                "sms_enabled": True,
                "whatsapp_enabled": True,
                "email_enabled": True,
            }

        # Get communication history
        from universal_workshop.customer_portal.communication_integration import (
            get_communication_history,
        )

        history_result = get_communication_history(customer_id, 10)

        if history_result.get("success"):
            communication_history = history_result["history"]
        else:
            communication_history = []

        context.update(
            {
                "title": _("Communication Preferences"),
                "preferences": preferences,
                "communication_history": communication_history,
                "languages": [
                    {"code": "ar", "name": _("Arabic")},
                    {"code": "en", "name": _("English")},
                ],
            }
        )

    except Exception as e:
        frappe.log_error(f"Error loading communication preferences: {str(e)}")
        context.update(
            {
                "title": _("Communication Preferences"),
                "error": _("Error loading preferences"),
                "preferences": {},
                "communication_history": [],
                "languages": [],
            }
        )

    return context


@frappe.whitelist()
@require_customer_auth
def update_preferences():
    """Update customer communication preferences"""
    try:
        customer_id = frappe.session.user

        # Get form data
        form_data = frappe.local.form_dict

        # Build preferences dictionary
        preferences = {
            "preferred_language": form_data.get("preferred_language", "ar"),
            "sms_enabled": bool(form_data.get("sms_enabled")),
            "whatsapp_enabled": bool(form_data.get("whatsapp_enabled")),
            "email_enabled": bool(form_data.get("email_enabled")),
        }

        # Update preferences
        from universal_workshop.customer_portal.communication_integration import (
            update_communication_preferences,
        )

        result = update_communication_preferences(customer_id, json.dumps(preferences))

        if result.get("success"):
            return {"success": True, "message": _("Communication preferences updated successfully")}
        else:
            return {
                "success": False,
                "message": result.get("error", _("Failed to update preferences")),
            }

    except Exception as e:
        frappe.log_error(f"Error updating communication preferences: {str(e)}")
        return {"success": False, "message": _("Error updating preferences")}
