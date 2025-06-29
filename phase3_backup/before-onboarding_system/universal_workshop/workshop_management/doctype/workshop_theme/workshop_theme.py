"""
Workshop Theme DocType Controller
Handles custom theme management and validation
"""

import frappe
from frappe import _
from frappe.model.document import Document
import json


class WorkshopTheme(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate theme data before saving"""
        self.validate_theme_data()
        self.validate_default_theme()
        self.set_metadata()

    def validate_theme_data(self):
        """Validate JSON theme data structure"""
        if self.theme_data:
            try:
                theme_data = json.loads(self.theme_data)

                # Validate required fields
                required_fields = ["name", "colors"]
                for field in required_fields:
                    if field not in theme_data:
                        frappe.throw(_("Theme data must contain '{0}' field").format(field))

                # Validate colors structure
                if "colors" in theme_data:
                    required_colors = ["primary", "secondary", "accent"]
                    for color in required_colors:
                        if color not in theme_data["colors"]:
                            frappe.throw(_("Theme colors must contain '{0}' color").format(color))

            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in theme data"))

    def validate_default_theme(self):
        """Ensure only one default theme exists"""
        if self.is_default:
            # Remove default flag from other themes
            existing_defaults = frappe.get_all(
                "Workshop Theme", filters={"is_default": 1, "name": ["!=", self.name]}
            )

            for theme in existing_defaults:
                frappe.db.set_value("Workshop Theme", theme.name, "is_default", 0)

    def set_metadata(self):
        """Set creation and modification metadata"""
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_date = frappe.utils.now()

        self.modified_by = frappe.session.user
        self.modified_date = frappe.utils.now()

    def before_save(self):
        """Actions before saving the theme"""
        # Generate preview if theme data is provided
        if self.theme_data and not self.preview_image:
            self.generate_preview_image()

    def generate_preview_image(self):
        """Generate a preview image for the theme"""
        # This could be enhanced to generate actual preview images
        # For now, we'll just set a placeholder
        pass

    def on_update(self):
        """Actions after updating the theme"""
        # Clear theme cache
        frappe.cache().delete_key("workshop_themes")

        # If this is the default theme, update workshop profile
        if self.is_default:
            self.update_workshop_profile_theme()

    def update_workshop_profile_theme(self):
        """Update workshop profile with default theme"""
        try:
            workshop_profile = frappe.get_single("Workshop Profile")
            if workshop_profile:
                workshop_profile.theme_preference = self.theme_name
                workshop_profile.save()
        except Exception as e:
            frappe.log_error(f"Error updating workshop profile theme: {str(e)}")

    def on_trash(self):
        """Actions before deleting the theme"""
        # Check if theme is in use
        users_using_theme = frappe.db.count("User", {"workshop_theme": self.theme_name})

        if users_using_theme > 0:
            frappe.throw(
                _("Cannot delete theme. {0} users are currently using this theme").format(
                    users_using_theme
                )
            )

        # Clear cache
        frappe.cache().delete_key("workshop_themes")


@frappe.whitelist()
def duplicate_theme(source_theme_name, new_theme_name):
    """Duplicate an existing theme"""
    try:
        # Get source theme
        source_theme = frappe.get_doc("Workshop Theme", source_theme_name)

        # Create new theme
        new_theme = frappe.new_doc("Workshop Theme")
        new_theme.theme_name = new_theme_name
        new_theme.theme_name_ar = source_theme.theme_name_ar
        new_theme.description = source_theme.description
        new_theme.description_ar = source_theme.description_ar
        new_theme.theme_data = source_theme.theme_data
        new_theme.is_active = 1
        new_theme.is_default = 0  # New theme should not be default

        new_theme.insert()

        return {
            "success": True,
            "message": _("Theme duplicated successfully"),
            "new_theme_name": new_theme_name,
        }

    except Exception as e:
        frappe.log_error(f"Error duplicating theme: {str(e)}")
        frappe.throw(_("Failed to duplicate theme: {0}").format(str(e)))


@frappe.whitelist()
def get_theme_usage_stats(theme_name):
    """Get usage statistics for a specific theme"""
    try:
        # Count users using this theme
        user_count = frappe.db.count("User", {"workshop_theme": theme_name})

        # Get recent usage
        recent_users = frappe.get_all(
            "User",
            filters={"workshop_theme": theme_name, "enabled": 1},
            fields=["name", "full_name", "last_login"],
            order_by="last_login desc",
            limit=10,
        )

        return {"user_count": user_count, "recent_users": recent_users}

    except Exception as e:
        frappe.log_error(f"Error getting theme usage stats: {str(e)}")
        return {"user_count": 0, "recent_users": []}
