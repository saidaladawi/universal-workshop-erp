# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_context(context):
    """Get context for migration dashboard page"""

    # Check user permissions
    if not has_dashboard_access():
        frappe.throw(_("Access Denied"), frappe.PermissionError)

    # Get user's role and default dashboard
    user_roles = frappe.get_roles()
    default_dashboard = get_user_default_dashboard(user_roles)

    # Get list of accessible dashboards
    accessible_dashboards = get_accessible_dashboards(user_roles)

    # Get current language for Arabic support
    current_language = frappe.local.lang or "en"

    context.update(
        {
            "title": _("Migration Dashboard"),
            "default_dashboard": default_dashboard,
            "dashboards": accessible_dashboards,
            "user_roles": user_roles,
            "language": current_language,
            "is_arabic": current_language == "ar",
            "csrf_token": frappe.sessions.get_csrf_token(),
            "user": frappe.session.user,
            "has_system_manager": "System Manager" in user_roles,
            "has_workshop_manager": "Workshop Manager" in user_roles,
        }
    )

    return context


def has_dashboard_access():
    """Check if user has access to migration dashboard"""

    required_roles = ["System Manager", "Workshop Manager", "Workshop User"]
    user_roles = frappe.get_roles()

    return any(role in user_roles for role in required_roles)


def get_user_default_dashboard(user_roles):
    """Get default dashboard based on user role"""

    # Check for role-specific default dashboards
    if "System Manager" in user_roles:
        dashboard = frappe.db.get_value(
            "Migration Dashboard",
            {"is_active": 1, "role_permissions": ["like", "%System Manager%"]},
            "name",
        )
        if dashboard:
            return dashboard

    if "Workshop Manager" in user_roles:
        dashboard = frappe.db.get_value(
            "Migration Dashboard",
            {"is_active": 1, "role_permissions": ["like", "%Workshop Manager%"]},
            "name",
        )
        if dashboard:
            return dashboard

    # Fallback to first active dashboard or create default
    dashboard = frappe.db.get_value("Migration Dashboard", {"is_active": 1}, "name")

    if not dashboard:
        # Create default dashboard if none exists
        try:
            from universal_workshop.analytics_reporting.doctype.migration_dashboard.migration_dashboard import (
                create_default_dashboard,
            )

            default_dash = create_default_dashboard()
            return default_dash.get("name")
        except Exception:
            return None

    return dashboard


def get_accessible_dashboards(user_roles):
    """Get list of dashboards accessible to user"""

    # Build role filter condition
    role_conditions = []
    for role in user_roles:
        role_conditions.append(f"role_permissions LIKE '%{role}%'")

    role_filter = f"({' OR '.join(role_conditions)})" if role_conditions else "1=1"

    dashboards = frappe.db.sql(
        f"""
        SELECT 
            name,
            dashboard_name,
            dashboard_name_ar,
            created_by,
            created_date,
            theme_variant
        FROM `tabMigration Dashboard`
        WHERE is_active = 1
        AND ({role_filter} OR created_by = %s)
        ORDER BY dashboard_name
    """,
        [frappe.session.user],
        as_dict=True,
    )

    return dashboards
