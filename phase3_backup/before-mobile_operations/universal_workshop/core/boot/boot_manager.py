# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

"""
Unified Boot Manager for Universal Workshop
Consolidates boot logic from install.py, core/boot.py, and workshop_setup.py
"""

import frappe
from frappe import _
import json
import os


class BootManager:
    """Unified boot logic consolidating install.py, boot.py, and workshop_setup.py"""
    
    def __init__(self):
        self.setup_status = None
        self.license_info = None
        self.workshop_config = None
        self.session_info = None
    
    def get_boot_info(self, bootinfo):
        """Consolidated boot information gathering"""
        try:
            boot_info = {}
            
            # Check initial setup status
            setup_status = self.check_initial_setup_status()
            boot_info["setup_complete"] = setup_status.get("setup_complete", False)
            boot_info["setup_status"] = setup_status
            
            # Get workshop configuration if setup is complete
            if setup_status.get("setup_complete"):
                workshop_config = self.get_workshop_configuration()
                boot_info["workshop_config"] = workshop_config
                
                # Get license information
                license_info = self.get_license_information()
                boot_info["license_info"] = license_info
                
                # Get session management information
                session_info = self.get_session_boot_info()
                boot_info["session_info"] = session_info
            
            # Update the bootinfo with our data
            bootinfo.update(boot_info)
            return bootinfo
            
        except Exception as e:
            frappe.log_error(f"Error in BootManager.get_boot_info: {e}")
            bootinfo.update({"setup_complete": False, "error": str(e)})
            return bootinfo
    
    def check_initial_setup(self):
        """Check initial setup during startup"""
        try:
            setup_status = self.check_initial_setup_status()
            
            if not setup_status.get("setup_complete"):
                frappe.log_error("Initial setup not complete", "Setup Check")
            
            return setup_status
            
        except Exception as e:
            frappe.log_error(f"Error checking initial setup: {e}")
            return {"setup_complete": False, "error": str(e)}
    
    def check_initial_setup_status(self):
        """Unified setup status checking from multiple files"""
        try:
            # Check for existing verified license
            license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"
            
            # Check if any Workshop Profile exists
            workshop_exists = frappe.db.exists("Workshop Profile", {"status": "Active"})
            
            # Check if any admin users exist (excluding Administrator and Guest)
            admin_users = frappe.db.count(
                "User",
                {
                    "user_type": "System User",
                    "enabled": 1,
                    "name": ["not in", ["Administrator", "Guest"]],
                },
            )
            
            # Check if onboarding has been completed
            completed_onboarding = frappe.db.exists("Onboarding Progress", {"docstatus": 1})
            
            # If license has data and no admin user, only require admin creation
            if license_has_data and admin_users == 0:
                return {
                    "setup_complete": False,
                    "workshop_exists": False,
                    "admin_users_count": admin_users,
                    "license_has_workshop_data": True,
                    "setup_mode": "admin_only"
                }
            
            # If license has data and admin exists, setup is complete
            if license_has_data and admin_users > 0:
                return {
                    "setup_complete": True,
                    "workshop_exists": bool(workshop_exists),
                    "admin_users_count": admin_users,
                    "license_has_workshop_data": True,
                    "setup_mode": "complete"
                }
            
            setup_complete = bool(workshop_exists and admin_users > 0 and completed_onboarding)
            
            return {
                "setup_complete": setup_complete,
                "workshop_exists": bool(workshop_exists),
                "admin_users_count": admin_users,
                "onboarding_completed": bool(completed_onboarding),
                "license_has_workshop_data": license_has_data,
                "setup_mode": "full" if not license_has_data else "admin_only"
            }
            
        except Exception as e:
            frappe.log_error(f"Error checking setup status: {e}")
            return {"setup_complete": False, "error": str(e)}
    
    def get_workshop_configuration(self):
        """Get workshop configuration and branding"""
        try:
            # Get the first active workshop profile
            workshop = frappe.get_list(
                "Workshop Profile",
                filters={"status": "Active"},
                fields=[
                    "workshop_name",
                    "workshop_name_ar", 
                    "logo",
                    "primary_color",
                    "secondary_color",
                ],
                limit=1,
            )
            
            if workshop:
                workshop_data = workshop[0]
                return {
                    "name": workshop_data.get("workshop_name", "Universal Workshop"),
                    "name_ar": workshop_data.get("workshop_name_ar", "الورشة الشاملة"),
                    "logo": workshop_data.get("logo"),
                    "primary_color": workshop_data.get("primary_color", "#667eea"),
                    "secondary_color": workshop_data.get("secondary_color", "#764ba2"),
                    "has_branding": True,
                }
            else:
                return {
                    "name": "Universal Workshop",
                    "name_ar": "الورشة الشاملة",
                    "logo": None,
                    "primary_color": "#667eea",
                    "secondary_color": "#764ba2",
                    "has_branding": False,
                }
                
        except Exception as e:
            frappe.log_error(f"Error getting workshop config: {e}")
            return {
                "name": "Universal Workshop",
                "name_ar": "الورشة الشاملة",
                "logo": None,
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "has_branding": False,
                "error": str(e),
            }
    
    def get_license_information(self):
        """Get current license information"""
        try:
            # Get license file data
            license_data = self.get_license_file_data()
            
            if license_data:
                return {
                    "is_valid": True,
                    "license_type": license_data.get("license_type", "Trial"),
                    "expires_on": license_data.get("expiry_date"),
                    "workshop_name": license_data.get("workshop_name_en"),
                    "workshop_name_ar": license_data.get("workshop_name_ar"),
                    "business_name": license_data.get("workshop_name_en"),
                    "status_message": "License is valid",
                    "max_users": license_data.get("max_users", 5),
                    "features": license_data.get("features", []),
                    "license_id": license_data.get("license_id"),
                }
            else:
                return {
                    "is_valid": False,
                    "license_type": "Unknown",
                    "status_message": "License file not found",
                }
                
        except Exception as e:
            frappe.log_error(f"Error getting license info: {e}")
            return {
                "is_valid": False,
                "license_type": "Unknown",
                "status_message": "License check failed",
                "error": str(e),
            }
    
    def get_license_file_data(self):
        """Read license file data"""
        try:
            # Get bench path
            bench_path = frappe.utils.get_bench_path()
            license_file_path = os.path.join(bench_path, "licenses", "workshop_license.json")
            
            if os.path.exists(license_file_path):
                with open(license_file_path, 'r', encoding='utf-8') as f:
                    license_data = json.load(f)
                    return license_data
            
            return None
            
        except Exception as e:
            frappe.log_error(f"Error reading license file: {e}")
            return None
    
    def get_session_boot_info(self):
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
    
    @frappe.whitelist()
    def get_onboarding_data(self):
        """Get initial onboarding data from license file (from workshop_setup.py)"""
        try:
            # Get license data
            license_data = self.get_license_file_data()
            
            if not license_data:
                return {
                    "success": False,
                    "message": _("License file not found"),
                    "data": {}
                }
            
            # Prepare pre-filled onboarding data
            onboarding_data = {
                "workshop_name": license_data.get("workshop_name_en", ""),
                "workshop_name_ar": license_data.get("workshop_name_ar", ""),
                "license_id": license_data.get("license_id", ""),
                "license_type": license_data.get("license_type", "Trial"),
                "max_users": license_data.get("max_users", 5),
                "features": license_data.get("features", []),
                "expiry_date": license_data.get("expiry_date", ""),
                "is_prefilled": True
            }
            
            return {
                "success": True,
                "message": _("License data loaded successfully"),
                "data": onboarding_data
            }
            
        except Exception as e:
            frappe.log_error(f"Error in get_onboarding_data: {e}")
            return {
                "success": False,
                "message": str(e),
                "data": {}
            }
    
    @frappe.whitelist()
    def check_setup_status(self):
        """Check if initial setup is required (from workshop_setup.py)"""
        try:
            # Check setup completion
            setup_complete = frappe.db.get_default("setup_complete") == "1"
            
            # Check license data availability
            license_data = self.get_license_file_data()
            has_license = bool(license_data)
            
            # Check if Workshop Profile exists
            workshop_exists = frappe.db.exists("Workshop Profile", {"status": "Active"})
            
            # Check admin users (excluding Administrator and Guest)
            admin_users = frappe.db.count(
                "User",
                {
                    "user_type": "System User",
                    "enabled": 1,
                    "name": ["not in", ["Administrator", "Guest"]],
                },
            )
            
            needs_onboarding = not (setup_complete and workshop_exists and admin_users > 0)
            
            return {
                "needs_onboarding": needs_onboarding,
                "setup_complete": setup_complete,
                "has_license": has_license,
                "workshop_exists": bool(workshop_exists),
                "admin_users_count": admin_users,
                "license_data": license_data if has_license else None
            }
            
        except Exception as e:
            frappe.log_error(f"Error in check_setup_status: {e}")
            return {
                "needs_onboarding": True,
                "error": str(e)
            }
    
    @frappe.whitelist()
    def get_user_home_page(self, user):
        """Determine the appropriate home page for the user based on setup status"""
        try:
            # Check if setup is complete
            setup_status = self.check_setup_status()
            
            # If setup is not complete, redirect to onboarding
            if setup_status.get("needs_onboarding"):
                return "/onboarding"
            
            # If setup is complete, use the default role-based redirect
            # This will be handled by the existing role_home_page configuration
            return None
            
        except Exception as e:
            frappe.log_error(f"Error in get_user_home_page: {e}")
            # Fall back to onboarding if there's an error
            return "/onboarding"


# Global instance for backward compatibility
_boot_manager = None

def get_boot_manager():
    """Get singleton BootManager instance"""
    global _boot_manager
    if _boot_manager is None:
        _boot_manager = BootManager()
    return _boot_manager


# Legacy function wrappers for backward compatibility
def get_boot_info(bootinfo):
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().get_boot_info(bootinfo)

def check_initial_setup():
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().check_initial_setup()

def check_initial_setup_status():
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().check_initial_setup_status()

def get_workshop_configuration():
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().get_workshop_configuration()

def get_license_information():
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().get_license_information()

def get_session_boot_info():
    """Legacy wrapper for existing hooks"""
    return get_boot_manager().get_session_boot_info()


# Whitelisted functions from workshop_setup.py
@frappe.whitelist()
def get_onboarding_data():
    """Get initial onboarding data from license file"""
    return get_boot_manager().get_onboarding_data()

@frappe.whitelist()
def check_setup_status():
    """Check if initial setup is required"""
    return get_boot_manager().check_setup_status()

@frappe.whitelist()
def get_user_home_page(user):
    """Determine the appropriate home page for the user based on setup status"""
    return get_boot_manager().get_user_home_page(user)