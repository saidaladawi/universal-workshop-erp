"""
Session Management Custom Fields and DocType Setup
Universal Workshop ERP - User Management

Creates custom DocType for session tracking and adds session-related fields to User DocType.
"""

import frappe
from frappe import _


def create_workshop_user_session_doctype():
    """Create custom DocType for enhanced session tracking"""

    # Check if DocType already exists
    if frappe.db.exists("DocType", "Workshop User Session"):
        print("Workshop User Session DocType already exists")
        return

    try:
        session_doctype = frappe.new_doc("DocType")
        session_doctype.name = "Workshop User Session"
        session_doctype.module = "User Management"
        session_doctype.custom = 1
        session_doctype.is_submittable = 0
        session_doctype.track_changes = 1
        session_doctype.autoname = "hash"
        session_doctype.title_field = "user_email"
        session_doctype.sort_field = "login_time"
        session_doctype.sort_order = "DESC"

        # Add fields for session tracking
        fields = [
            {
                "fieldname": "user_email",
                "fieldtype": "Link",
                "options": "User",
                "label": "User",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "session_id",
                "fieldtype": "Data",
                "label": "Session ID",
                "unique": 1,
                "reqd": 1,
                "read_only": 1,
            },
            {
                "fieldname": "device_info",
                "fieldtype": "JSON",
                "label": "Device Information",
                "description": "Browser, OS, and device details",
            },
            {
                "fieldname": "ip_address",
                "fieldtype": "Data",
                "label": "IP Address",
                "in_list_view": 1,
            },
            {
                "fieldname": "user_agent",
                "fieldtype": "Text",
                "label": "User Agent",
                "description": "Full user agent string from browser",
            },
            {
                "fieldname": "login_time",
                "fieldtype": "Datetime",
                "label": "Login Time",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "last_activity",
                "fieldtype": "Datetime",
                "label": "Last Activity",
                "in_list_view": 1,
            },
            {
                "fieldname": "expiry_time",
                "fieldtype": "Datetime",
                "label": "Expiry Time",
                "description": "When this session will expire",
            },
            {
                "fieldname": "is_active",
                "fieldtype": "Check",
                "label": "Is Active",
                "default": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "revoked_by",
                "fieldtype": "Link",
                "options": "User",
                "label": "Revoked By",
                "description": "User who revoked this session",
            },
            {
                "fieldname": "revocation_reason",
                "fieldtype": "Text",
                "label": "Revocation Reason",
                "description": "Reason for session revocation",
            },
            {
                "fieldname": "session_policy",
                "fieldtype": "JSON",
                "label": "Session Policy",
                "description": "Policy settings active for this session",
            },
        ]

        for field in fields:
            field["parent"] = "Workshop User Session"
            field["parenttype"] = "DocType"
            field["parentfield"] = "fields"
            session_doctype.append("fields", field)

        session_doctype.insert(ignore_permissions=True)
        frappe.db.commit()

        print("Workshop User Session DocType created successfully")

    except Exception as e:
        frappe.log_error(f"Error creating Workshop User Session DocType: {e}")
        print(f"Error: {e}")


def add_session_fields_to_user():
    """Add session management related fields to User DocType"""

    try:
        # Session Policy field
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "session_policy"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "session_policy"
            custom_field.fieldtype = "JSON"
            custom_field.label = "Session Policy"
            custom_field.description = "Custom session management policy for this user"
            custom_field.insert_after = "user_type"
            custom_field.permlevel = 1  # Restrict to System Manager
            custom_field.insert(ignore_permissions=True)

        # Session Timeout Minutes field
        if not frappe.db.exists(
            "Custom Field", {"dt": "User", "fieldname": "session_timeout_minutes"}
        ):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "session_timeout_minutes"
            custom_field.fieldtype = "Int"
            custom_field.label = "Session Timeout (Minutes)"
            custom_field.description = "Custom idle timeout in minutes (0 = use role default)"
            custom_field.insert_after = "session_policy"
            custom_field.default = "0"
            custom_field.permlevel = 1
            custom_field.insert(ignore_permissions=True)

        # Max Concurrent Sessions field
        if not frappe.db.exists(
            "Custom Field", {"dt": "User", "fieldname": "max_concurrent_sessions"}
        ):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "max_concurrent_sessions"
            custom_field.fieldtype = "Int"
            custom_field.label = "Max Concurrent Sessions"
            custom_field.description = "Maximum allowed concurrent sessions (0 = use role default)"
            custom_field.insert_after = "session_timeout_minutes"
            custom_field.default = "0"
            custom_field.permlevel = 1
            custom_field.insert(ignore_permissions=True)

        # Force Single Session field
        if not frappe.db.exists(
            "Custom Field", {"dt": "User", "fieldname": "force_single_session"}
        ):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "force_single_session"
            custom_field.fieldtype = "Check"
            custom_field.label = "Force Single Session"
            custom_field.description = "Allow only one active session at a time"
            custom_field.insert_after = "max_concurrent_sessions"
            custom_field.default = "0"
            custom_field.permlevel = 1
            custom_field.insert(ignore_permissions=True)

        frappe.db.commit()
        print("Session management fields added to User DocType successfully")

    except Exception as e:
        frappe.log_error(f"Error adding session fields to User: {e}")
        print(f"Error: {e}")


def setup_session_management():
    """Complete setup for session management"""
    print("Setting up session management...")

    # Create custom DocType
    create_workshop_user_session_doctype()

    # Add custom fields to User
    add_session_fields_to_user()

    # Clear cache to reload changes
    frappe.clear_cache()

    print("Session management setup completed successfully!")


if __name__ == "__main__":
    setup_session_management()
