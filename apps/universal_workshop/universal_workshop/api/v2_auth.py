"""
V2 Authentication API - Universal Workshop ERP
Provides REST-style authentication endpoints for Frontend V2
"""

import frappe
from frappe import _
from frappe.auth import validate_auth_via_api_keys, get_api_key
from frappe.utils import cint, get_datetime, add_to_date
import json
from typing import Dict, Any, Optional


@frappe.whitelist(allow_guest=True)
def login(email: str, password: str) -> Dict[str, Any]:
    """
    REST API login endpoint for Frontend V2
    Returns user data and session information
    """
    try:
        # Authenticate user
        frappe.local.login_manager.authenticate(email, password)
        frappe.local.login_manager.post_login()
        
        # Get user data
        user = frappe.get_doc("User", email)
        
        # Get frontend preference
        frontend_preference = getattr(user, 'frontend_preference', 'traditional')
        
        # Create session data
        session_data = {
            "success": True,
            "user": {
                "name": user.name,
                "email": user.email,
                "full_name": user.full_name or user.first_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_image": user.user_image,
                "frontend_preference": frontend_preference,
                "language": user.language or frappe.local.lang,
                "time_zone": user.time_zone or frappe.utils.get_system_timezone(),
                "user_type": user.user_type,
                "enabled": user.enabled
            },
            "session": {
                "session_id": frappe.session.sid,
                "expires_at": get_session_expiry().isoformat(),
                "csrf_token": frappe.sessions.get_csrf_token()
            },
            "permissions": get_user_permissions(user.name),
            "workshop_settings": get_workshop_context()
        }
        
        # Log successful login
        frappe.logger().info(f"Frontend V2 login successful for user: {email}")
        
        return session_data
        
    except frappe.exceptions.AuthenticationError:
        frappe.throw(_("Invalid email or password"), frappe.AuthenticationError)
    except Exception as e:
        frappe.logger().error(f"Frontend V2 login error: {str(e)}")
        frappe.throw(_("Login failed. Please try again."))


@frappe.whitelist(allow_guest=False)
def logout() -> Dict[str, Any]:
    """
    REST API logout endpoint for Frontend V2
    Clears session and logs out user
    """
    try:
        user = frappe.session.user
        
        # Clear session
        frappe.local.login_manager.logout()
        
        # Clear any cached data
        frappe.cache().delete_value("user_permissions:" + user)
        
        frappe.logger().info(f"Frontend V2 logout successful for user: {user}")
        
        return {
            "success": True,
            "message": _("Logged out successfully")
        }
        
    except Exception as e:
        frappe.logger().error(f"Frontend V2 logout error: {str(e)}")
        return {
            "success": False,
            "message": _("Logout failed")
        }


@frappe.whitelist(allow_guest=False)
def refresh_token() -> Dict[str, Any]:
    """
    Refresh authentication token/session
    Extends current session and returns updated data
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            frappe.throw(_("No active session found"), frappe.AuthenticationError)
        
        # Extend session
        frappe.local.login_manager.extend_session()
        
        # Get updated user data
        user_doc = frappe.get_doc("User", user)
        
        return {
            "success": True,
            "session": {
                "session_id": frappe.session.sid,
                "expires_at": get_session_expiry().isoformat(),
                "csrf_token": frappe.sessions.get_csrf_token()
            },
            "user": {
                "name": user_doc.name,
                "email": user_doc.email,
                "full_name": user_doc.full_name or user_doc.first_name,
                "frontend_preference": getattr(user_doc, 'frontend_preference', 'traditional')
            },
            "permissions": get_user_permissions(user)
        }
        
    except Exception as e:
        frappe.logger().error(f"Token refresh error: {str(e)}")
        frappe.throw(_("Token refresh failed"))


@frappe.whitelist(allow_guest=False)
def get_session_status() -> Dict[str, Any]:
    """
    Check current session status
    Returns session validity and user information
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return {
                "authenticated": False,
                "session_valid": False
            }
        
        # Check if session is still valid
        session_valid = frappe.local.session_obj and frappe.local.session_obj.data
        
        return {
            "authenticated": True,
            "session_valid": session_valid,
            "user": user,
            "session_id": frappe.session.sid,
            "expires_at": get_session_expiry().isoformat() if session_valid else None
        }
        
    except Exception as e:
        frappe.logger().error(f"Session status check error: {str(e)}")
        return {
            "authenticated": False,
            "session_valid": False,
            "error": str(e)
        }


def get_session_expiry():
    """Get session expiry datetime"""
    try:
        # Default session expiry (24 hours from now)
        expiry_hours = cint(frappe.db.get_single_value("System Settings", "session_expiry")) or 24
        return add_to_date(get_datetime(), hours=expiry_hours)
    except:
        # Fallback to 24 hours
        return add_to_date(get_datetime(), hours=24)


def get_user_permissions(user: str) -> Dict[str, Any]:
    """
    Get user permissions for Frontend V2
    Returns structured permissions data
    """
    try:
        permissions = {
            "workshop_management": {
                "can_create_service_orders": frappe.has_permission("Service Order", "create", user=user),
                "can_view_service_orders": frappe.has_permission("Service Order", "read", user=user),
                "can_update_service_orders": frappe.has_permission("Service Order", "write", user=user),
                "can_cancel_service_orders": frappe.has_permission("Service Order", "cancel", user=user)
            },
            "customer_management": {
                "can_create_customers": frappe.has_permission("Customer", "create", user=user),
                "can_view_customers": frappe.has_permission("Customer", "read", user=user),
                "can_update_customers": frappe.has_permission("Customer", "write", user=user)
            },
            "vehicle_management": {
                "can_create_vehicles": frappe.has_permission("Vehicle", "create", user=user),
                "can_view_vehicles": frappe.has_permission("Vehicle", "read", user=user),
                "can_update_vehicles": frappe.has_permission("Vehicle", "write", user=user)
            },
            "inventory_management": {
                "can_view_inventory": frappe.has_permission("Item", "read", user=user),
                "can_update_inventory": frappe.has_permission("Stock Entry", "create", user=user),
                "can_manage_parts": frappe.has_permission("Item", "write", user=user)
            },
            "analytics": {
                "can_view_analytics": frappe.has_permission("Dashboard", "read", user=user),
                "can_view_reports": frappe.has_permission("Report", "read", user=user)
            },
            "system": {
                "is_system_manager": "System Manager" in frappe.get_roles(user),
                "can_manage_settings": frappe.has_permission("Workshop Settings", "write", user=user)
            }
        }
        
        return permissions
        
    except Exception as e:
        frappe.logger().error(f"Error getting user permissions: {str(e)}")
        return {}


def get_workshop_context() -> Dict[str, Any]:
    """
    Get workshop settings context for Frontend V2
    """
    try:
        workshop_settings = frappe.get_single("Workshop Settings")
        
        return {
            "workshop_name": workshop_settings.workshop_name,
            "primary_color": workshop_settings.primary_color,
            "secondary_color": workshop_settings.secondary_color,
            "theme_style": workshop_settings.theme_style,
            "language": workshop_settings.language,
            "time_zone": workshop_settings.time_zone,
            "currency": workshop_settings.default_currency,
            "enable_frontend_v2": workshop_settings.enable_frontend_v2,
            "frontend_v2_default": getattr(workshop_settings, 'frontend_v2_default', False)
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting workshop context: {str(e)}")
        return {
            "workshop_name": "Universal Workshop",
            "primary_color": "#1976d2",
            "language": "ar",
            "enable_frontend_v2": True
        }


@frappe.whitelist(allow_guest=False)
def update_user_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user preferences for Frontend V2
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        
        # Update frontend preference
        if "frontend_preference" in preferences:
            user_doc.frontend_preference = preferences["frontend_preference"]
        
        # Update other preferences
        allowed_fields = ["language", "time_zone", "user_image"]
        for field in allowed_fields:
            if field in preferences:
                setattr(user_doc, field, preferences[field])
        
        user_doc.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": _("Preferences updated successfully"),
            "updated_preferences": preferences
        }
        
    except Exception as e:
        frappe.logger().error(f"Error updating user preferences: {str(e)}")
        frappe.throw(_("Failed to update preferences"))


@frappe.whitelist(allow_guest=False)
def get_user_activities(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent user activities for dashboard
    """
    try:
        user = frappe.session.user
        
        # Get recent activities
        activities = frappe.get_all(
            "Activity Log",
            filters={"user": user},
            fields=["subject", "content", "creation", "reference_doctype", "reference_name"],
            order_by="creation desc",
            limit=limit
        )
        
        return {
            "activities": activities,
            "count": len(activities)
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting user activities: {str(e)}")
        return {"activities": [], "count": 0}


@frappe.whitelist(allow_guest=False)  
def get_user_notifications(limit: int = 20, unread_only: bool = False) -> Dict[str, Any]:
    """
    Get user notifications for Frontend V2
    """
    try:
        user = frappe.session.user
        
        filters = {"for_user": user}
        if unread_only:
            filters["read"] = 0
        
        notifications = frappe.get_all(
            "Notification Log",
            filters=filters,
            fields=["subject", "email_content", "creation", "read", "type", "document_type", "document_name"],
            order_by="creation desc",
            limit=limit
        )
        
        unread_count = frappe.db.count("Notification Log", {"for_user": user, "read": 0})
        
        return {
            "notifications": notifications,
            "unread_count": unread_count,
            "total": len(notifications)
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting user notifications: {str(e)}")
        return {"notifications": [], "unread_count": 0, "total": 0}