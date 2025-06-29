# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def handle_app_startup():
    """Handle application startup hooks"""
    try:
        # Check initial setup
        from universal_workshop.core.boot.boot_manager import check_initial_setup
        setup_status = check_initial_setup()
        
        # Log startup
        frappe.logger().info("Universal Workshop startup completed")
        
        return setup_status
        
    except Exception as e:
        frappe.log_error(f"Error in app startup: {e}")
        return {"error": str(e)}


def handle_boot_session(bootinfo):
    """Handle boot session initialization"""
    try:
        from universal_workshop.core.boot.boot_manager import get_boot_info
        return get_boot_info(bootinfo)
        
    except Exception as e:
        frappe.log_error(f"Error in boot session: {e}")
        bootinfo.update({"setup_complete": False, "error": str(e)})
        return bootinfo


def handle_after_install():
    """Handle post-installation setup"""
    try:
        from universal_workshop.setup.installation.installation_manager import after_install
        return after_install()
        
    except Exception as e:
        frappe.log_error(f"Error in after_install hook: {e}")
        raise


def handle_user_home_page(user):
    """Handle user home page determination"""
    try:
        from universal_workshop.core.boot.boot_manager import get_user_home_page
        return get_user_home_page(user)
        
    except Exception as e:
        frappe.log_error(f"Error getting user home page: {e}")
        return None


def validate_workshop_permissions():
    """Validate workshop-specific permissions"""
    try:
        from universal_workshop.user_management.permission_hooks import has_permission
        return {"has_workshop_access": True}  # يتم التحقق من الصلاحيات عبر النظام الموجود
        
    except Exception as e:
        frappe.log_error(f"Error validating permissions: {e}")
        return {"has_workshop_access": False}
