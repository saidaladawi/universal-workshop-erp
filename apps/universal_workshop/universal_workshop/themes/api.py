"""
Universal Workshop Themes API
Handles custom theme management and persistence
"""

import frappe
from frappe import _
import json


@frappe.whitelist()
def get_custom_themes():
    """Get all custom themes created by users"""
    try:
        # Get custom themes from database
        custom_themes = frappe.get_all(
            "Workshop Theme",
            fields=["name", "theme_name", "theme_data", "is_active", "created_by"],
            filters={"is_active": 1},
        )

        themes_dict = {}
        for theme in custom_themes:
            if theme.theme_data:
                theme_data = json.loads(theme.theme_data)
                themes_dict[theme.name] = theme_data

        return themes_dict

    except Exception as e:
        frappe.log_error(f"Error loading custom themes: {str(e)}")
        return {}


@frappe.whitelist()
def save_custom_theme(theme_name, theme_data):
    """Save a custom theme"""
    try:
        # Validate theme data
        if not theme_name or not theme_data:
            frappe.throw(_("Theme name and data are required"))

        # Check if theme already exists
        existing_theme = frappe.db.exists("Workshop Theme", {"theme_name": theme_name})

        if existing_theme:
            # Update existing theme
            theme_doc = frappe.get_doc("Workshop Theme", existing_theme)
            theme_doc.theme_data = json.dumps(theme_data)
            theme_doc.modified_by = frappe.session.user
            theme_doc.save()
        else:
            # Create new theme
            theme_doc = frappe.new_doc("Workshop Theme")
            theme_doc.theme_name = theme_name
            theme_doc.theme_data = json.dumps(theme_data)
            theme_doc.is_active = 1
            theme_doc.created_by = frappe.session.user
            theme_doc.insert()

        return {"success": True, "message": _("Theme saved successfully")}

    except Exception as e:
        frappe.log_error(f"Error saving custom theme: {str(e)}")
        frappe.throw(_("Failed to save theme: {0}").format(str(e)))


@frappe.whitelist()
def delete_custom_theme(theme_name):
    """Delete a custom theme"""
    try:
        theme_doc = frappe.get_doc("Workshop Theme", {"theme_name": theme_name})

        # Check permissions
        if theme_doc.created_by != frappe.session.user and not frappe.has_permission(
            "Workshop Theme", "delete"
        ):
            frappe.throw(_("You don't have permission to delete this theme"))

        theme_doc.delete()
        return {"success": True, "message": _("Theme deleted successfully")}

    except Exception as e:
        frappe.log_error(f"Error deleting custom theme: {str(e)}")
        frappe.throw(_("Failed to delete theme: {0}").format(str(e)))


@frappe.whitelist()
def get_user_theme_preference():
    """Get current user's theme preference"""
    try:
        user_theme = frappe.db.get_value("User", frappe.session.user, "workshop_theme")

        # Fallback to workshop branding theme
        if not user_theme:
            workshop_profile = frappe.get_single("Workshop Profile")
            if workshop_profile and workshop_profile.theme_preference:
                user_theme = workshop_profile.theme_preference

        return user_theme or "classic"

    except Exception as e:
        frappe.log_error(f"Error getting user theme preference: {str(e)}")
        return "classic"


@frappe.whitelist()
def set_user_theme_preference(theme_name):
    """Set current user's theme preference"""
    try:
        # Validate theme exists
        if not is_valid_theme(theme_name):
            frappe.throw(_("Invalid theme selected"))

        # Update user preference
        frappe.db.set_value("User", frappe.session.user, "workshop_theme", theme_name)

        return {"success": True, "message": _("Theme preference updated")}

    except Exception as e:
        frappe.log_error(f"Error setting user theme preference: {str(e)}")
        frappe.throw(_("Failed to update theme preference: {0}").format(str(e)))


@frappe.whitelist()
def export_theme(theme_name):
    """Export a theme for sharing"""
    try:
        # Get theme data
        theme_doc = frappe.get_doc("Workshop Theme", {"theme_name": theme_name})

        if not theme_doc:
            frappe.throw(_("Theme not found"))

        # Prepare export data
        export_data = {
            "theme_name": theme_doc.theme_name,
            "theme_data": json.loads(theme_doc.theme_data),
            "version": "1.0",
            "exported_by": frappe.session.user,
            "exported_at": frappe.utils.now(),
        }

        return export_data

    except Exception as e:
        frappe.log_error(f"Error exporting theme: {str(e)}")
        frappe.throw(_("Failed to export theme: {0}").format(str(e)))


@frappe.whitelist()
def import_theme(theme_data):
    """Import a theme from export data"""
    try:
        # Validate import data
        if not theme_data or "theme_name" not in theme_data or "theme_data" not in theme_data:
            frappe.throw(_("Invalid theme import data"))

        theme_name = theme_data["theme_name"]

        # Check if theme already exists
        if frappe.db.exists("Workshop Theme", {"theme_name": theme_name}):
            # Add suffix to avoid conflicts
            import time

            theme_name = f"{theme_name}_imported_{int(time.time())}"

        # Create imported theme
        theme_doc = frappe.new_doc("Workshop Theme")
        theme_doc.theme_name = theme_name
        theme_doc.theme_data = json.dumps(theme_data["theme_data"])
        theme_doc.is_active = 1
        theme_doc.created_by = frappe.session.user
        theme_doc.insert()

        return {
            "success": True,
            "message": _("Theme imported successfully as {0}").format(theme_name),
            "theme_name": theme_name,
        }

    except Exception as e:
        frappe.log_error(f"Error importing theme: {str(e)}")
        frappe.throw(_("Failed to import theme: {0}").format(str(e)))


def is_valid_theme(theme_name):
    """Check if a theme name is valid (exists in default or custom themes)"""
    default_themes = ["classic", "automotive", "luxury"]

    if theme_name in default_themes:
        return True

    # Check custom themes
    return frappe.db.exists("Workshop Theme", {"theme_name": theme_name, "is_active": 1})


@frappe.whitelist()
def get_theme_analytics():
    """Get analytics about theme usage"""
    try:
        # Get theme usage statistics
        theme_stats = frappe.db.sql(
            """
            SELECT workshop_theme as theme, COUNT(*) as usage_count
            FROM tabUser
            WHERE workshop_theme IS NOT NULL
            GROUP BY workshop_theme
        """,
            as_dict=True,
        )

        # Get custom themes count
        custom_themes_count = frappe.db.count("Workshop Theme", {"is_active": 1})

        return {
            "theme_usage": theme_stats,
            "custom_themes_count": custom_themes_count,
            "total_users": frappe.db.count("User", {"enabled": 1}),
        }

    except Exception as e:
        frappe.log_error(f"Error getting theme analytics: {str(e)}")
        return {}


@frappe.whitelist()
def get_workshop_theme():
    """Get the current workshop theme for the user"""
    try:
        # Get user's preferred theme
        user = frappe.get_doc("User", frappe.session.user)
        workshop_theme = getattr(user, 'workshop_theme', None)

        if workshop_theme:
            # Get theme details
            theme_doc = frappe.get_doc("Workshop Theme", workshop_theme)
            return {
                "theme_name": theme_doc.theme_name,
                "theme_data": json.loads(theme_doc.theme_data) if theme_doc.theme_data else {},
                "is_active": theme_doc.is_active
            }

        # Return default theme if no custom theme is set
        return {
            "theme_name": "Default Workshop Theme",
            "theme_data": {
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "background_color": "#ffffff",
                "text_color": "#333333",
                "rtl_support": True,
                "arabic_font": "Noto Sans Arabic"
            },
            "is_active": True
        }

    except Exception as e:
        frappe.log_error(f"Error getting workshop theme: {str(e)}")
        return {
            "theme_name": "Default Workshop Theme",
            "theme_data": {
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "background_color": "#ffffff",
                "text_color": "#333333",
                "rtl_support": True,
                "arabic_font": "Noto Sans Arabic"
            },
            "is_active": True
        }


@frappe.whitelist()
def get_theme_colors():
    """Get theme color configuration for the current user"""
    try:
        # Get user's current theme
        theme_data = get_workshop_theme()

        if theme_data and theme_data.get('theme_data'):
            colors = theme_data['theme_data']
            return {
                "primary_color": colors.get("primary_color", "#007bff"),
                "secondary_color": colors.get("secondary_color", "#6c757d"),
                "background_color": colors.get("background_color", "#ffffff"),
                "text_color": colors.get("text_color", "#333333"),
                "accent_color": colors.get("accent_color", "#28a745"),
                "warning_color": colors.get("warning_color", "#ffc107"),
                "danger_color": colors.get("danger_color", "#dc3545"),
                "success_color": colors.get("success_color", "#28a745"),
                "info_color": colors.get("info_color", "#17a2b8"),
                "rtl_support": colors.get("rtl_support", True),
                "arabic_font": colors.get("arabic_font", "Noto Sans Arabic")
            }

        # Return default color scheme
        return {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "background_color": "#ffffff",
            "text_color": "#333333",
            "accent_color": "#28a745",
            "warning_color": "#ffc107",
            "danger_color": "#dc3545",
            "success_color": "#28a745",
            "info_color": "#17a2b8",
            "rtl_support": True,
            "arabic_font": "Noto Sans Arabic"
        }

    except Exception as e:
        frappe.log_error(f"Error getting theme colors: {str(e)}")
        # Return safe defaults on error
        return {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "background_color": "#ffffff",
            "text_color": "#333333",
            "accent_color": "#28a745",
            "warning_color": "#ffc107",
            "danger_color": "#dc3545",
            "success_color": "#28a745",
            "info_color": "#17a2b8",
            "rtl_support": True,
            "arabic_font": "Noto Sans Arabic"
        }
