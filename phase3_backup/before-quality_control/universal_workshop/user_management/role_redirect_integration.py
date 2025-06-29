# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_role_redirect_with_session_validation(user):
    """Get role-based redirect URL with session validation"""
    try:
        from universal_workshop.user_management.session_manager import SessionManager
        
        session_manager = SessionManager()
        
        # Validate current session
        session_valid = session_manager.validate_current_session()
        if not session_valid:
            return "/login?session_expired=1"
        
        # Get user roles
        user_roles = frappe.get_roles(user)
        
        # Role-based redirect logic with session context
        role_redirects = {
            "Workshop Owner": "/universal-workshop-dashboard",
            "Workshop Manager": "/app/workspace/Workshop%20Management", 
            "Workshop Technician": "/technician",
            "System Manager": "/app/workspace/Workshop%20Management",
            "Administrator": "/app/workspace/Workshop%20Management"
        }
        
        # Find the highest priority role
        for role in ["Workshop Owner", "System Manager", "Administrator", "Workshop Manager", "Workshop Technician"]:
            if role in user_roles:
                redirect_url = role_redirects.get(role, "/app")
                
                # Log role-based redirect
                session_manager.log_session_activity(
                    activity_type="role_redirect",
                    details={"role": role, "redirect_url": redirect_url}
                )
                
                return redirect_url
        
        # Default redirect
        return "/app"
        
    except Exception as e:
        frappe.log_error(f"Role redirect with session validation error: {e}")
        return "/app"

