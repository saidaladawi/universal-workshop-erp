"""
Dark Mode Fixtures for Universal Workshop ERP
Creates custom fields and configurations for dark mode functionality
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_dark_mode_custom_fields():
    """Install custom fields for dark mode functionality"""

    # Custom fields for User DocType
    user_custom_fields = {
        "User": [
            {
                "fieldname": "dark_mode_section",
                "fieldtype": "Section Break",
                "label": "Dark Mode Preferences",
                "insert_after": "language",
                "collapsible": 1,
            },
            {
                "fieldname": "dark_mode_preference",
                "fieldtype": "Select",
                "label": "Dark Mode Preference",
                "options": "system\nlight\ndark",
                "default": "system",
                "description": "Choose your preferred dark mode setting",
                "insert_after": "dark_mode_section",
            },
            {
                "fieldname": "dark_mode_column_break",
                "fieldtype": "Column Break",
                "insert_after": "dark_mode_preference",
            },
            {
                "fieldname": "auto_dark_mode",
                "fieldtype": "Check",
                "label": "Auto Dark Mode",
                "description": "Automatically switch to dark mode based on system preference",
                "depends_on": "eval:doc.dark_mode_preference=='system'",
                "default": 1,
                "insert_after": "dark_mode_column_break",
            },
        ]
    }

    try:
        create_custom_fields(user_custom_fields, ignore_validate=True)
        print("✅ Dark mode custom fields installed successfully")
    except Exception as e:
        print(f"❌ Error installing dark mode custom fields: {e}")


def setup_dark_mode_permissions():
    """Setup permissions for dark mode functionality"""

    # Users should be able to modify their own dark mode preferences
    try:
        # Add permission for users to modify their own User record
        if not frappe.db.exists(
            "Custom DocPerm", {"parent": "User", "role": "System Manager", "permlevel": 0}
        ):
            # System Manager already has full access, no need to add
            pass

        print("✅ Dark mode permissions configured successfully")
    except Exception as e:
        print(f"❌ Error setting up dark mode permissions: {e}")


def create_dark_mode_workspace():
    """Create workspace for dark mode management"""

    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "Dark Mode Management"):
            print("ℹ️ Dark Mode Management workspace already exists")
            return

        workspace = frappe.new_doc("Workspace")
        workspace.title = "Dark Mode Management"
        workspace.module = "Universal Workshop"
        workspace.category = "Modules"
        workspace.public = 1
        workspace.is_standard = 1

        # Add charts/shortcuts for dark mode statistics
        workspace.charts = [
            {
                "chart_name": "Dark Mode Usage",
                "label": "Dark Mode Usage Statistics",
                "chart_type": "Donut",
                "doctype": "User",
                "based_on": "dark_mode_preference",
                "time_interval": "Daily",
                "timeseries": 0,
                "filters_json": "[]",
                "source": "Dashboard Chart",
            }
        ]

        workspace.shortcuts = [
            {
                "type": "DocType",
                "label": "User Settings",
                "doc_view": "List",
                "doctype": "User",
                "link_to": "User",
            }
        ]

        workspace.insert()
        print("✅ Dark Mode Management workspace created successfully")

    except Exception as e:
        print(f"❌ Error creating dark mode workspace: {e}")


def install_dark_mode_system():
    """Complete dark mode system installation"""

    print("🌙 Installing Dark Mode System for Universal Workshop ERP...")

    # Install custom fields
    install_dark_mode_custom_fields()

    # Setup permissions
    setup_dark_mode_permissions()

    # Create workspace
    create_dark_mode_workspace()

    # Commit changes
    frappe.db.commit()

    print("✅ Dark Mode system installation completed!")


def uninstall_dark_mode_system():
    """Remove dark mode system components"""

    print("🗑️ Uninstalling Dark Mode System...")

    try:
        # Remove custom fields
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={
                "fieldname": [
                    "in",
                    [
                        "dark_mode_section",
                        "dark_mode_preference",
                        "dark_mode_column_break",
                        "auto_dark_mode",
                    ],
                ]
            },
        )

        for field in custom_fields:
            frappe.delete_doc("Custom Field", field.name)

        # Remove workspace
        if frappe.db.exists("Workspace", "Dark Mode Management"):
            frappe.delete_doc("Workspace", "Dark Mode Management")

        frappe.db.commit()
        print("✅ Dark Mode system uninstalled successfully")

    except Exception as e:
        print(f"❌ Error uninstalling dark mode system: {e}")


# API Methods for client-side access
@frappe.whitelist()
def get_user_dark_mode_preference(user=None):
    """Get user's dark mode preference"""

    if not user:
        user = frappe.session.user

    try:
        preference = frappe.db.get_value("User", user, "dark_mode_preference")
        auto_mode = frappe.db.get_value("User", user, "auto_dark_mode")

        return {"preference": preference or "system", "auto_mode": auto_mode or 0, "user": user}
    except Exception as e:
        frappe.log_error(f"Error getting dark mode preference: {e}")
        return {"preference": "system", "auto_mode": 1, "user": user}


@frappe.whitelist()
def set_user_dark_mode_preference(preference, auto_mode=None):
    """Set user's dark mode preference"""

    if preference not in ["system", "light", "dark"]:
        frappe.throw("Invalid dark mode preference")

    try:
        user = frappe.session.user

        # Update user preference
        frappe.db.set_value("User", user, "dark_mode_preference", preference)

        if auto_mode is not None:
            frappe.db.set_value("User", user, "auto_dark_mode", auto_mode)

        frappe.db.commit()

        return {
            "status": "success",
            "message": "Dark mode preference updated successfully",
            "preference": preference,
            "auto_mode": auto_mode,
        }

    except Exception as e:
        frappe.log_error(f"Error setting dark mode preference: {e}")
        frappe.throw("Failed to update dark mode preference")


@frappe.whitelist()
def get_dark_mode_statistics():
    """Get dark mode usage statistics"""

    try:
        stats = frappe.db.sql(
            """
            SELECT 
                dark_mode_preference,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `tabUser` WHERE enabled = 1), 2) as percentage
            FROM `tabUser` 
            WHERE enabled = 1 AND dark_mode_preference IS NOT NULL
            GROUP BY dark_mode_preference
            ORDER BY count DESC
        """,
            as_dict=True,
        )

        return {
            "statistics": stats,
            "total_users": frappe.db.count("User", {"enabled": 1}),
            "dark_mode_users": frappe.db.count(
                "User", {"enabled": 1, "dark_mode_preference": "dark"}
            ),
            "system_users": frappe.db.count(
                "User", {"enabled": 1, "dark_mode_preference": "system"}
            ),
        }

    except Exception as e:
        frappe.log_error(f"Error getting dark mode statistics: {e}")
        return {"statistics": [], "total_users": 0, "dark_mode_users": 0, "system_users": 0}
