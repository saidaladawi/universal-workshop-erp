"""
Theme-related fixtures for Universal Workshop
Creates custom fields and configurations for theme management
"""

import frappe
from frappe import _


def create_theme_custom_fields():
    """Create custom fields for theme management"""

    # Add workshop_theme field to User DocType
    user_theme_field = {
        "doctype": "Custom Field",
        "dt": "User",
        "fieldname": "workshop_theme",
        "fieldtype": "Select",
        "label": "Workshop Theme",
        "options": "\nclassic\nautomotive\nluxury",
        "default": "classic",
        "insert_after": "language",
        "description": "Select your preferred workshop theme",
    }

    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "workshop_theme"}):
        frappe.get_doc(user_theme_field).insert()

    # Add theme_preference field to Workshop Profile (if not already exists)
    workshop_theme_field = {
        "doctype": "Custom Field",
        "dt": "Workshop Profile",
        "fieldname": "default_theme",
        "fieldtype": "Select",
        "label": "Default Theme",
        "options": "\nclassic\nautomotive\nluxury",
        "default": "classic",
        "insert_after": "theme_preference",
        "description": "Default theme for new users",
    }

    if not frappe.db.exists(
        "Custom Field", {"dt": "Workshop Profile", "fieldname": "default_theme"}
    ):
        frappe.get_doc(workshop_theme_field).insert()


def create_default_themes():
    """Create default workshop themes"""

    default_themes = [
        {
            "theme_name": "classic",
            "theme_name_ar": "الكلاسيكي",
            "description": "Traditional ERPNext blue theme with workshop enhancements",
            "description_ar": "المظهر الأزرق التقليدي مع تحسينات الورشة",
            "is_active": 1,
            "is_default": 1,
            "theme_data": """{
                "name": "Classic Blue",
                "name_ar": "الأزرق الكلاسيكي",
                "colors": {
                    "primary": "#1f4e79",
                    "secondary": "#e8f4fd",
                    "accent": "#2490ef",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "danger": "#dc3545",
                    "info": "#17a2b8",
                    "light": "#f8f9fa",
                    "dark": "#343a40"
                },
                "fonts": {
                    "primary": "\\"Noto Sans\\", \\"Helvetica Neue\\", Arial, sans-serif",
                    "arabic": "\\"Noto Sans Arabic\\", \\"Tahoma\\", \\"Arial Unicode MS\\", sans-serif"
                },
                "properties": {
                    "borderRadius": "4px",
                    "shadowLevel": "medium"
                }
            }""",
        },
        {
            "theme_name": "automotive",
            "theme_name_ar": "السيارات",
            "description": "Professional green theme inspired by automotive industry",
            "description_ar": "مظهر أخضر مهني مستوحى من صناعة السيارات",
            "is_active": 1,
            "is_default": 0,
            "theme_data": """{
                "name": "Automotive Green",
                "name_ar": "الأخضر السيارات",
                "colors": {
                    "primary": "#2c5f41",
                    "secondary": "#e8f5e8",
                    "accent": "#4caf50",
                    "success": "#388e3c",
                    "warning": "#ff9800",
                    "danger": "#f44336",
                    "info": "#2196f3",
                    "light": "#f1f8e9",
                    "dark": "#1b5e20"
                },
                "fonts": {
                    "primary": "\\"Roboto\\", \\"Segoe UI\\", Tahoma, Geneva, Verdana, sans-serif",
                    "arabic": "\\"Noto Sans Arabic\\", \\"Tahoma\\", \\"Arial Unicode MS\\", sans-serif"
                },
                "properties": {
                    "borderRadius": "6px",
                    "shadowLevel": "high"
                }
            }""",
        },
        {
            "theme_name": "luxury",
            "theme_name_ar": "الفاخر",
            "description": "Premium gold and black theme for luxury workshops",
            "description_ar": "مظهر ذهبي وأسود راقي للورش الفاخرة",
            "is_active": 1,
            "is_default": 0,
            "theme_data": """{
                "name": "Luxury Gold",
                "name_ar": "الذهبي الفاخر",
                "colors": {
                    "primary": "#b8860b",
                    "secondary": "#fffef7",
                    "accent": "#ffd700",
                    "success": "#6a994e",
                    "warning": "#f77f00",
                    "danger": "#d62828",
                    "info": "#457b9d",
                    "light": "#fefcf3",
                    "dark": "#2f3e46"
                },
                "fonts": {
                    "primary": "\\"Playfair Display\\", Georgia, \\"Times New Roman\\", serif",
                    "arabic": "\\"Amiri\\", \\"Noto Sans Arabic\\", \\"Times New Roman\\", serif"
                },
                "properties": {
                    "borderRadius": "8px",
                    "shadowLevel": "high"
                }
            }""",
        },
    ]

    for theme_data in default_themes:
        if not frappe.db.exists("Workshop Theme", theme_data["theme_name"]):
            theme_doc = frappe.new_doc("Workshop Theme")
            theme_doc.update(theme_data)
            theme_doc.insert()


def setup_theme_permissions():
    """Setup permissions for theme management"""

    # Workshop Theme permissions
    theme_permissions = [
        {
            "role": "Workshop Manager",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
        {
            "role": "Workshop User",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
        {
            "role": "All",
            "permlevel": 0,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
        },
    ]

    for perm in theme_permissions:
        if not frappe.db.exists(
            "Custom DocPerm", {"parent": "Workshop Theme", "role": perm["role"]}
        ):
            doc_perm = frappe.new_doc("Custom DocPerm")
            doc_perm.parent = "Workshop Theme"
            doc_perm.parenttype = "DocType"
            doc_perm.parentfield = "permissions"
            doc_perm.update(perm)
            doc_perm.insert()


def install_theme_system():
    """Install complete theme management system"""
    try:
        # Create custom fields
        create_theme_custom_fields()

        # Create default themes
        create_default_themes()

        # Setup permissions
        setup_theme_permissions()

        frappe.db.commit()

        return {"success": True, "message": _("Theme system installed successfully")}

    except Exception as e:
        frappe.log_error(f"Error installing theme system: {str(e)}")
        frappe.db.rollback()
        return {
            "success": False,
            "message": _("Failed to install theme system: {0}").format(str(e)),
        }
