"""
V2 User Management API - Universal Workshop ERP
Provides user profile and preference management for Frontend V2
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, cint
import json
from typing import Dict, Any, Optional, List


@frappe.whitelist(allow_guest=False)
def get_profile() -> Dict[str, Any]:
    """
    Get complete user profile for Frontend V2
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        
        # Get user roles
        user_roles = frappe.get_roles(user)
        
        # Get user permissions summary
        permissions = get_user_permission_summary(user)
        
        # Get recent activity
        recent_activity = get_recent_user_activity(user, limit=5)
        
        profile_data = {
            "user": {
                "name": user_doc.name,
                "email": user_doc.email,
                "full_name": user_doc.full_name or f"{user_doc.first_name} {user_doc.last_name or ''}".strip(),
                "first_name": user_doc.first_name,
                "last_name": user_doc.last_name,
                "user_image": user_doc.user_image,
                "phone": user_doc.phone,
                "mobile_no": user_doc.mobile_no,
                "language": user_doc.language or frappe.local.lang,
                "time_zone": user_doc.time_zone or frappe.utils.get_system_timezone(),
                "user_type": user_doc.user_type,
                "enabled": user_doc.enabled,
                "creation": user_doc.creation,
                "last_login": user_doc.last_login,
                "frontend_preference": getattr(user_doc, 'frontend_preference', 'traditional')
            },
            "roles": user_roles,
            "permissions": permissions,
            "settings": get_user_settings(user),
            "recent_activity": recent_activity,
            "statistics": get_user_statistics(user)
        }
        
        return profile_data
        
    except Exception as e:
        frappe.logger().error(f"Error getting user profile: {str(e)}")
        frappe.throw(_("Failed to load user profile"))


@frappe.whitelist(allow_guest=False)
def update_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user profile information
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        
        # Allowed fields for user update
        allowed_fields = [
            "first_name", "last_name", "user_image", "phone", "mobile_no",
            "language", "time_zone", "frontend_preference"
        ]
        
        updated_fields = []
        for field in allowed_fields:
            if field in profile_data and profile_data[field] is not None:
                old_value = getattr(user_doc, field, None)
                new_value = profile_data[field]
                if old_value != new_value:
                    setattr(user_doc, field, new_value)
                    updated_fields.append(field)
        
        if updated_fields:
            user_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Log the update
            frappe.logger().info(f"User profile updated for {user}: {updated_fields}")
        
        return {
            "success": True,
            "message": _("Profile updated successfully"),
            "updated_fields": updated_fields
        }
        
    except Exception as e:
        frappe.logger().error(f"Error updating user profile: {str(e)}")
        frappe.throw(_("Failed to update profile"))


@frappe.whitelist(allow_guest=False)
def get_preferences() -> Dict[str, Any]:
    """
    Get user preferences for Frontend V2
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        
        preferences = {
            "frontend_preference": getattr(user_doc, 'frontend_preference', 'traditional'),
            "language": user_doc.language or "ar",
            "time_zone": user_doc.time_zone or "Asia/Muscat",
            "date_format": get_user_date_format(user),
            "number_format": get_user_number_format(user),
            "theme": get_user_theme_preference(user),
            "dashboard_settings": get_user_dashboard_settings(user),
            "notification_settings": get_user_notification_settings(user)
        }
        
        return {
            "preferences": preferences,
            "available_options": get_preference_options()
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting user preferences: {str(e)}")
        return {"preferences": {}, "available_options": {}}


@frappe.whitelist(allow_guest=False)
def update_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user preferences
    """
    try:
        user = frappe.session.user
        
        # Update user document fields
        user_fields = ["frontend_preference", "language", "time_zone"]
        user_doc = frappe.get_doc("User", user)
        user_updated = False
        
        for field in user_fields:
            if field in preferences:
                if getattr(user_doc, field, None) != preferences[field]:
                    setattr(user_doc, field, preferences[field])
                    user_updated = True
        
        if user_updated:
            user_doc.save(ignore_permissions=True)
        
        # Update other preference settings
        for key, value in preferences.items():
            if key not in user_fields:
                set_user_preference(user, key, value)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Preferences updated successfully"),
            "updated_preferences": preferences
        }
        
    except Exception as e:
        frappe.logger().error(f"Error updating preferences: {str(e)}")
        frappe.throw(_("Failed to update preferences"))


@frappe.whitelist(allow_guest=False)
def get_dashboard_config() -> Dict[str, Any]:
    """
    Get user dashboard configuration for Frontend V2
    """
    try:
        user = frappe.session.user
        
        # Get default dashboard configuration
        default_config = get_default_dashboard_config()
        
        # Get user customizations
        user_config = get_user_dashboard_settings(user)
        
        # Merge configurations
        dashboard_config = {**default_config, **user_config}
        
        return {
            "dashboard_config": dashboard_config,
            "widgets_available": get_available_dashboard_widgets(),
            "layout_options": get_dashboard_layout_options()
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting dashboard config: {str(e)}")
        return {"dashboard_config": {}, "widgets_available": [], "layout_options": []}


@frappe.whitelist(allow_guest=False)
def save_dashboard_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save user dashboard configuration
    """
    try:
        user = frappe.session.user
        
        # Validate configuration
        if not validate_dashboard_config(config):
            frappe.throw(_("Invalid dashboard configuration"))
        
        # Save configuration
        set_user_preference(user, "dashboard_config", json.dumps(config))
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Dashboard configuration saved successfully")
        }
        
    except Exception as e:
        frappe.logger().error(f"Error saving dashboard config: {str(e)}")
        frappe.throw(_("Failed to save dashboard configuration"))


def get_user_permission_summary(user: str) -> Dict[str, Any]:
    """Get summary of user permissions"""
    try:
        return {
            "service_orders": {
                "create": frappe.has_permission("Service Order", "create", user=user),
                "read": frappe.has_permission("Service Order", "read", user=user),
                "write": frappe.has_permission("Service Order", "write", user=user),
                "cancel": frappe.has_permission("Service Order", "cancel", user=user)
            },
            "customers": {
                "create": frappe.has_permission("Customer", "create", user=user),
                "read": frappe.has_permission("Customer", "read", user=user),
                "write": frappe.has_permission("Customer", "write", user=user)
            },
            "vehicles": {
                "create": frappe.has_permission("Vehicle", "create", user=user),
                "read": frappe.has_permission("Vehicle", "read", user=user),
                "write": frappe.has_permission("Vehicle", "write", user=user)
            },
            "inventory": {
                "read": frappe.has_permission("Item", "read", user=user),
                "write": frappe.has_permission("Item", "write", user=user),
                "stock_entry": frappe.has_permission("Stock Entry", "create", user=user)
            },
            "reports": {
                "view": frappe.has_permission("Report", "read", user=user),
                "export": frappe.has_permission("Report", "export", user=user)
            },
            "system": {
                "settings": frappe.has_permission("Workshop Settings", "write", user=user),
                "system_manager": "System Manager" in frappe.get_roles(user)
            }
        }
    except Exception:
        return {}


def get_recent_user_activity(user: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent user activity"""
    try:
        activities = frappe.get_all(
            "Activity Log",
            filters={"user": user},
            fields=["subject", "content", "creation", "reference_doctype", "reference_name"],
            order_by="creation desc",
            limit=limit
        )
        return activities
    except Exception:
        return []


def get_user_statistics(user: str) -> Dict[str, Any]:
    """Get user statistics for profile"""
    try:
        # Get various counts for user statistics
        stats = {
            "service_orders_created": frappe.db.count("Service Order", {"owner": user}),
            "customers_created": frappe.db.count("Customer", {"owner": user}),
            "total_logins": frappe.db.count("Activity Log", {"user": user, "subject": ("like", "%login%")}),
            "last_30_days_activity": frappe.db.count(
                "Activity Log", 
                {
                    "user": user, 
                    "creation": (">=", frappe.utils.add_days(frappe.utils.nowdate(), -30))
                }
            )
        }
        return stats
    except Exception:
        return {}


def get_user_settings(user: str) -> Dict[str, Any]:
    """Get user-specific settings"""
    try:
        settings = {
            "date_format": get_user_date_format(user),
            "number_format": get_user_number_format(user),
            "theme": get_user_theme_preference(user),
            "notifications_enabled": get_user_preference(user, "notifications_enabled", True),
            "email_notifications": get_user_preference(user, "email_notifications", True),
            "sms_notifications": get_user_preference(user, "sms_notifications", False)
        }
        return settings
    except Exception:
        return {}


def get_user_date_format(user: str) -> str:
    """Get user date format preference"""
    user_format = get_user_preference(user, "date_format")
    return user_format or frappe.db.get_single_value("System Settings", "date_format") or "dd-mm-yyyy"


def get_user_number_format(user: str) -> str:
    """Get user number format preference"""
    user_format = get_user_preference(user, "number_format")
    return user_format or frappe.db.get_single_value("System Settings", "number_format") or "#,###.##"


def get_user_theme_preference(user: str) -> str:
    """Get user theme preference"""
    return get_user_preference(user, "theme", "modern")


def get_user_dashboard_settings(user: str) -> Dict[str, Any]:
    """Get user dashboard settings"""
    settings_json = get_user_preference(user, "dashboard_config", "{}")
    try:
        return json.loads(settings_json) if isinstance(settings_json, str) else settings_json
    except:
        return {}


def get_user_notification_settings(user: str) -> Dict[str, Any]:
    """Get user notification settings"""
    return {
        "email_enabled": get_user_preference(user, "email_notifications", True),
        "sms_enabled": get_user_preference(user, "sms_notifications", False),
        "browser_enabled": get_user_preference(user, "browser_notifications", True),
        "service_order_updates": get_user_preference(user, "notify_service_orders", True),
        "customer_updates": get_user_preference(user, "notify_customers", True),
        "system_alerts": get_user_preference(user, "notify_system", True)
    }


def get_user_preference(user: str, key: str, default: Any = None) -> Any:
    """Get user preference value"""
    try:
        value = frappe.db.get_value("User Permission", {"user": user, "key": key}, "value")
        return value if value is not None else default
    except:
        return default


def set_user_preference(user: str, key: str, value: Any) -> None:
    """Set user preference value"""
    try:
        existing = frappe.db.get_value("User Permission", {"user": user, "key": key}, "name")
        if existing:
            frappe.db.set_value("User Permission", existing, "value", str(value))
        else:
            # Create new preference record if User Permission doctype exists
            # Otherwise, use a simple key-value store approach
            frappe.db.set_value("User", user, f"preference_{key}", str(value))
    except Exception as e:
        frappe.logger().error(f"Error setting user preference {key}: {str(e)}")


def get_preference_options() -> Dict[str, Any]:
    """Get available preference options"""
    return {
        "languages": [
            {"value": "ar", "label": "العربية"},
            {"value": "en", "label": "English"}
        ],
        "time_zones": [
            {"value": "Asia/Muscat", "label": "Muscat (UTC+4)"},
            {"value": "Asia/Dubai", "label": "Dubai (UTC+4)"},
            {"value": "Asia/Riyadh", "label": "Riyadh (UTC+3)"},
            {"value": "Asia/Kuwait", "label": "Kuwait (UTC+3)"}
        ],
        "date_formats": [
            {"value": "dd-mm-yyyy", "label": "DD-MM-YYYY"},
            {"value": "mm-dd-yyyy", "label": "MM-DD-YYYY"},
            {"value": "yyyy-mm-dd", "label": "YYYY-MM-DD"}
        ],
        "themes": [
            {"value": "modern", "label": "Modern"},
            {"value": "classic", "label": "Classic"},
            {"value": "dark", "label": "Dark"},
            {"value": "automotive", "label": "Automotive"}
        ],
        "frontend_options": [
            {"value": "traditional", "label": "Traditional Frappe"},
            {"value": "v2", "label": "Modern Frontend V2"}
        ]
    }


def get_default_dashboard_config() -> Dict[str, Any]:
    """Get default dashboard configuration"""
    return {
        "layout": "grid",
        "widgets": [
            {"type": "service_orders", "position": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"type": "revenue", "position": {"x": 6, "y": 0, "w": 6, "h": 4}},
            {"type": "customers", "position": {"x": 0, "y": 4, "w": 4, "h": 3}},
            {"type": "vehicles", "position": {"x": 4, "y": 4, "w": 4, "h": 3}},
            {"type": "inventory", "position": {"x": 8, "y": 4, "w": 4, "h": 3}}
        ],
        "refresh_interval": 300,
        "auto_refresh": True
    }


def get_available_dashboard_widgets() -> List[Dict[str, Any]]:
    """Get available dashboard widgets"""
    return [
        {"type": "service_orders", "name": "Service Orders", "category": "Operations"},
        {"type": "revenue", "name": "Revenue", "category": "Financial"},
        {"type": "customers", "name": "Customers", "category": "CRM"},
        {"type": "vehicles", "name": "Vehicles", "category": "Operations"},
        {"type": "inventory", "name": "Inventory", "category": "Inventory"},
        {"type": "technicians", "name": "Technicians", "category": "Resources"},
        {"type": "appointments", "name": "Appointments", "category": "Scheduling"},
        {"type": "alerts", "name": "Alerts", "category": "System"}
    ]


def get_dashboard_layout_options() -> List[Dict[str, Any]]:
    """Get dashboard layout options"""
    return [
        {"value": "grid", "label": "Grid Layout", "description": "Flexible grid-based layout"},
        {"value": "list", "label": "List Layout", "description": "Vertical list layout"},
        {"value": "cards", "label": "Card Layout", "description": "Card-based layout"}
    ]


def validate_dashboard_config(config: Dict[str, Any]) -> bool:
    """Validate dashboard configuration"""
    try:
        required_fields = ["layout", "widgets"]
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate widgets structure
        if not isinstance(config["widgets"], list):
            return False
        
        for widget in config["widgets"]:
            if not isinstance(widget, dict) or "type" not in widget:
                return False
        
        return True
    except:
        return False