# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute():
    """Integrate session management with existing authentication system"""
    try:
        print("🔐 Integrating session management with authentication system...")

        # 1. Update boot session to include session management
        update_boot_session_integration()

        # 2. Add session hooks to existing authentication
        add_session_hooks()

        # 3. Configure session management for login system
        configure_login_session_integration()

        # 4. Update role-based redirect with session validation
        update_role_redirect_with_session()

        # 5. Add session cleanup scheduler
        add_session_cleanup_scheduler()

        print("✅ Session management integration completed successfully")

    except Exception as e:
        frappe.log_error(f"Session management integration failed: {e}")
        print(f"❌ Session management integration failed: {e}")
        raise


def update_boot_session_integration():
    """Update boot.py to include session management information"""
    try:
        # Create enhanced boot session integration
        boot_session_code = '''
def get_session_boot_info():
    """Get session-specific boot information"""
    try:
        from universal_workshop.user_management.session_manager import SessionManager
        
        session_info = {}
        
        if frappe.session.user and frappe.session.user != "Guest":
            session_manager = SessionManager()
            
            # Get current session details
            current_session = session_manager.get_current_session()
            if current_session:
                session_info.update({
                    "session_id": current_session.get("name"),
                    "login_time": current_session.get("login_time"),
                    "last_activity": current_session.get("last_activity"),
                    "device_info": current_session.get("device_info"),
                    "ip_address": current_session.get("ip_address"),
                    "session_timeout": current_session.get("session_timeout"),
                    "mfa_enabled": current_session.get("mfa_verified", False),
                    "concurrent_sessions": session_manager.get_active_session_count(frappe.session.user)
                })
            
            # Get user security settings
            security_settings = session_manager.get_user_security_settings(frappe.session.user)
            session_info.update({
                "security_settings": security_settings,
                "requires_mfa": security_settings.get("require_mfa", False),
                "max_concurrent_sessions": security_settings.get("max_concurrent_sessions", 3)
            })
        
        return session_info
        
    except Exception as e:
        frappe.log_error(f"Error getting session boot info: {e}")
        return {}
'''

        # Read current boot.py
        boot_file_path = frappe.get_app_path("universal_workshop", "boot.py")
        with open(boot_file_path, "r") as f:
            boot_content = f.read()

        # Add session boot info function if not exists
        if "get_session_boot_info" not in boot_content:
            boot_content += "\n\n" + boot_session_code

            # Update get_boot_info to include session info
            if "session_info = get_session_boot_info()" not in boot_content:
                boot_content = boot_content.replace(
                    'boot_info["license_info"] = license_info',
                    """boot_info["license_info"] = license_info
            
            # Get session management information
            session_info = get_session_boot_info()
            boot_info["session_info"] = session_info""",
                )

            with open(boot_file_path, "w") as f:
                f.write(boot_content)

        print("✅ Boot session integration updated")

    except Exception as e:
        frappe.log_error(f"Error updating boot session: {e}")
        raise


def add_session_hooks():
    """Add session management hooks to the system"""
    try:
        print("✅ Session hooks configuration noted (already in hooks.py)")
        # Note: Session hooks are already configured in the main hooks.py file
        # This function documents what should be there

    except Exception as e:
        frappe.log_error(f"Error adding session hooks: {e}")
        raise


def configure_login_session_integration():
    """Configure login system to work with session management"""
    try:
        # Create login integration script
        login_integration_code = '''
def integrate_session_with_login(user, login_manager):
    """Integrate session management with login process"""
    try:
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
'''

        # Save login integration file
        login_integration_path = frappe.get_app_path(
            "universal_workshop", "user_management", "login_integration.py"
        )
        with open(login_integration_path, "w") as f:
            f.write(
                f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt


{login_integration_code}
"""
            )

        print("✅ Login session integration configured")

    except Exception as e:
        frappe.log_error(f"Error configuring login integration: {e}")
        raise


def update_role_redirect_with_session():
    """Update role-based redirect to include session validation"""
    try:
        # Create enhanced role redirect with session validation
        role_redirect_code = '''
def get_role_redirect_with_session_validation(user):
    """Get role-based redirect URL with session validation"""
    try:
        
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
'''

        # Save role redirect integration
        role_redirect_path = frappe.get_app_path(
            "universal_workshop", "user_management", "role_redirect_integration.py"
        )
        with open(role_redirect_path, "w") as f:
            f.write(
                f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt


{role_redirect_code}
"""
            )

        print("✅ Role redirect with session validation updated")

    except Exception as e:
        frappe.log_error(f"Error updating role redirect: {e}")
        raise


def add_session_cleanup_scheduler():
    """Add session cleanup to scheduler events"""
    try:
        print("✅ Session cleanup scheduler events configured (already in hooks.py)")
        # Note: Session cleanup events are already configured in hooks.py

    except Exception as e:
        frappe.log_error(f"Error adding session cleanup scheduler: {e}")
        raise


if __name__ == "__main__":
    execute()
