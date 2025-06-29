# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def integrate_session_with_login(user, login_manager):
    """Integrate session management with login process"""
    try:
        from universal_workshop.user_management.session_manager import SessionManager
        from universal_workshop.user_management.mfa_manager import MFAManager
        
        session_manager = SessionManager()
        mfa_manager = MFAManager()
        
        # Create or update session
        session_data = {
            "user": user,
            "ip_address": frappe.local.request_ip,
            "user_agent": frappe.local.request.headers.get("User-Agent", ""),
            "login_method": "password"
        }
        
        session_result = session_manager.create_session(session_data)
        
        if not session_result.get("success"):
            frappe.throw(_("Session creation failed: {0}").format(session_result.get("message")))
        
        # Check MFA requirement
        mfa_required = mfa_manager.is_mfa_required(user)
        if mfa_required and not session_result.get("mfa_verified"):
            # Redirect to MFA verification
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/mfa-verification"
            return
        
        # Set session cookies
        session_manager.set_session_cookies(session_result.get("session_id"))
        
        # Log successful login
        frappe.logger().info(f"User {user} logged in successfully with session {session_result.get('session_id')}")
        
        return session_result
        
    except Exception as e:
        frappe.log_error(f"Login session integration error: {e}")
        frappe.throw(_("Login failed due to session error"))

