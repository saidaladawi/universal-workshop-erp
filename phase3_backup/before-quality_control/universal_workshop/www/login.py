import frappe
from frappe import _
from frappe.utils import get_url
import json
import os


def get_context(context):
    """Build context for custom workshop login page"""

    # Check if initial setup is required
    setup_status = check_initial_setup_status()
    if not setup_status.get("setup_complete"):
        frappe.local.flags.redirect_location = "/workshop-onboarding"
        raise frappe.Redirect

    # Redirect if user is already logged in
    if frappe.session.user != "Guest":
        # Check for requested redirect parameter
        requested_redirect = frappe.form_dict.get("redirect") or frappe.local.request.args.get(
            "redirect"
        )
        frappe.local.flags.redirect_location = get_post_login_redirect(
            requested_redirect=requested_redirect
        )
        raise frappe.Redirect

    # Get workshop branding and configuration
    context.workshop_config = get_workshop_config()
    context.license_status = check_license_status()
    context.system_status = get_system_status()

    # Language and RTL support
    context.is_arabic = frappe.local.lang == "ar"
    context.text_direction = "rtl" if context.is_arabic else "ltr"

    # Login form configuration
    context.disable_signup = True  # Workshop users are created by admin
    context.show_forgot_password = True
    context.login_required_message = _("Please log in to access Universal Workshop")

    # Custom branding
    context.page_title = _("Universal Workshop Login")
    context.login_title = _("Welcome to Universal Workshop")
    context.login_subtitle = _("Professional Automotive Workshop Management")

    # Error handling
    context.license_error = None
    context.system_error = None

    if not context.license_status.get("is_valid"):
        context.license_error = context.license_status.get("error_message")

    if not context.system_status.get("is_healthy"):
        context.system_error = context.system_status.get("error_message")

    return context


def check_initial_setup_status():
    """Check if initial workshop setup has been completed"""
    try:
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

        setup_complete = bool(workshop_exists and admin_users > 0 and completed_onboarding)

        return {
            "setup_complete": setup_complete,
            "workshop_exists": bool(workshop_exists),
            "admin_users_count": admin_users,
            "onboarding_completed": bool(completed_onboarding),
        }

    except Exception as e:
        frappe.log_error(f"Error checking setup status: {e}")
        return {"setup_complete": False, "error": str(e)}


def get_workshop_config():
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


def check_license_status():
    """Check current license status"""
    try:
        # Import license validation function
        from universal_workshop.license_management.license_validator import validate_current_license

        license_result = validate_current_license()
        return {
            "is_valid": license_result.get("is_valid", False),
            "license_type": license_result.get("license_type", "Trial"),
            "expires_on": license_result.get("expires_on"),
            "days_remaining": license_result.get("days_remaining", 0),
            "business_name": license_result.get("business_name"),
            "status_message": license_result.get("message", "License validation failed"),
        }

    except Exception as e:
        frappe.log_error(f"Error checking license status: {e}")
        return {
            "is_valid": False,
            "license_type": "Unknown",
            "status_message": "License check failed",
            "error": str(e),
        }


def get_system_status():
    """Get overall system health status"""
    try:
        # Basic system checks
        database_status = "OK" if frappe.db else "Error"

        # Check if essential DocTypes exist
        essential_doctypes = ["Workshop Profile", "Customer", "Vehicle", "Service Order"]
        doctype_status = "OK"

        for doctype in essential_doctypes:
            if not frappe.db.exists("DocType", doctype):
                doctype_status = "Missing DocTypes"
                break

        return {
            "overall_status": (
                "OK" if database_status == "OK" and doctype_status == "OK" else "Error"
            ),
            "database_status": database_status,
            "doctype_status": doctype_status,
            "server_time": frappe.utils.now(),
            "version": frappe.get_version(),
        }

    except Exception as e:
        frappe.log_error(f"Error getting system status: {e}")
        return {"overall_status": "Error", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def authenticate_user(usr, pwd):
    """Custom authentication with workshop-specific logic"""
    try:
        # Check if initial setup is still required
        setup_status = check_initial_setup_status()
        if not setup_status.get("setup_complete"):
            return {
                "status": "error",
                "message": _("System setup not complete. Please complete initial setup first."),
                "redirect_to": "/workshop-onboarding",
            }

        # Validate license before allowing login
        license_status = check_license_status()
        if not license_status.get("is_valid"):
            # Allow login during grace period but show warning
            frappe.log_error(f"Login attempted with invalid license: {license_status}")

        # Attempt authentication
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        # Get user roles and determine redirect
        user_roles = frappe.get_roles(usr)

        # Check for requested redirect parameter
        requested_redirect = frappe.form_dict.get("redirect") or frappe.local.request.args.get(
            "redirect"
        )
        redirect_url = get_post_login_redirect(usr, requested_redirect)

        # Log successful login with redirect info
        log_login_attempt(usr, True)
        frappe.logger().info(
            f"Successful login for user: {usr} with roles: {user_roles}, redirecting to: {redirect_url}"
        )

        return {
            "status": "success",
            "message": _("Login successful. Welcome to Universal Workshop!"),
            "redirect_to": redirect_url,
            "user_roles": user_roles,
        }

    except frappe.exceptions.AuthenticationError:
        log_login_attempt(usr, False, "Invalid username or password")
        return {"status": "error", "message": _("Invalid username or password. Please try again.")}
    except frappe.exceptions.ValidationError as e:
        log_login_attempt(usr, False, str(e))
        return {"status": "error", "message": str(e)}
    except Exception as e:
        frappe.log_error(f"Login error: {e}")
        log_login_attempt(usr, False, str(e))
        return {
            "status": "error",
            "message": _("Login failed due to system error. Please contact administrator."),
        }


def has_workshop_access(user):
    """Check if user has workshop access permissions"""
    try:
        user_roles = frappe.get_roles(user)
        workshop_roles = [
            "Workshop Manager",
            "Workshop Technician",
            "Workshop Owner",
            "System Manager",
            "Administrator",
        ]

        return any(role in workshop_roles for role in user_roles)
    except Exception:
        return False


def get_post_login_redirect(user=None, requested_redirect=None):
    """Determine where to redirect user after login based on their role and requested URL"""
    try:
        # Import secure redirect manager
        from universal_workshop.user_management.secure_redirect import get_redirect_manager

        redirect_manager = get_redirect_manager()
        user_roles = frappe.get_roles(user or frappe.session.user)

        # If a specific redirect was requested (e.g., from ?redirect= parameter)
        if requested_redirect:
            # Use secure redirect manager to validate and get safe URL
            safe_redirect = redirect_manager.get_safe_redirect_url(requested_redirect, user_roles)
            return safe_redirect

        # Default role-based redirect logic using secure redirect manager
        return redirect_manager._get_role_based_redirect(user_roles)

    except Exception as e:
        frappe.log_error(f"Error determining post-login redirect: {e}")
        return "/app"


def log_login_attempt(user, success, error_message=None):
    """Log login attempts for security audit"""
    try:
        from universal_workshop.user_management.audit_logger import log_security_event

        event_data = {
            "user": user,
            "ip_address": frappe.local.request_ip,
            "user_agent": frappe.get_request_header("User-Agent"),
            "success": success,
            "error_message": error_message,
        }

        log_security_event("login_attempt", event_data)
    except Exception as e:
        frappe.log_error(f"Error logging login attempt: {e}")
