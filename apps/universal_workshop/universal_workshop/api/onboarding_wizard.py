"""
Onboarding Wizard API Endpoints
Handles the simplified 3-step onboarding process
"""

import frappe
from frappe import _
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def get_user_onboarding_progress():
    """
    Get current user's onboarding progress
    Returns existing progress or None if not started
    """
    try:
        user = frappe.session.user
        if user == "Guest":
            return {
                "exists": False,
                "current_step": 0,
                "completed_steps": [],
                "data": {},
                "progress_id": None
            }
        
        # Check for existing onboarding progress
        progress = frappe.db.get_value(
            "Onboarding Progress",
            {"user": user, "status": ["in", ["In Progress", "Completed"]]},
            ["name", "current_step", "completed_steps", "form_data", "status"],
            as_dict=True
        )
        
        if progress:
            return {
                "exists": True,
                "current_step": progress.current_step or 0,
                "completed_steps": json.loads(progress.completed_steps or "[]"),
                "data": json.loads(progress.form_data or "{}"),
                "progress_id": progress.name,
                "status": progress.status
            }
        
        return {
            "exists": False,
            "current_step": 0,
            "completed_steps": [],
            "data": {},
            "progress_id": None
        }
        
    except Exception as e:
        frappe.log_error(f"Get onboarding progress failed: {str(e)}")
        return {
            "exists": False,
            "current_step": 0,
            "completed_steps": [],
            "data": {},
            "progress_id": None
        }

@frappe.whitelist(allow_guest=True)
def start_onboarding_wizard():
    """
    Start new onboarding wizard session
    """
    try:
        user = frappe.session.user
        if user == "Guest":
            # For guest users, create temporary session
            progress_id = f"guest_{frappe.utils.random_string(10)}"
            return {
                "success": True,
                "progress_id": progress_id,
                "message": _("Guest onboarding session started")
            }
        
        # Create new onboarding progress record
        progress = frappe.get_doc({
            "doctype": "Onboarding Progress",
            "user": user,
            "current_step": 0,
            "completed_steps": "[]",
            "form_data": "{}",
            "status": "In Progress",
            "started_at": frappe.utils.now()
        })
        progress.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "progress_id": progress.name,
            "message": _("Onboarding wizard started successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Start onboarding wizard failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to start onboarding wizard"),
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def validate_step_data(step_name: str, data: str):
    """
    Validate step data before saving
    """
    try:
        step_data = json.loads(data) if isinstance(data, str) else data
        errors = []
        
        if step_name == "license_verification":
            errors.extend(_validate_license_step(step_data))
        elif step_name == "admin_account":
            errors.extend(_validate_admin_step(step_data))
        elif step_name == "workshop_config":
            errors.extend(_validate_workshop_step(step_data))
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Step validation failed: {str(e)}")
        return {
            "valid": False,
            "errors": [_("Validation failed: {0}").format(str(e))]
        }

def _validate_license_step(data: Dict[str, Any]) -> List[str]:
    """Validate license verification step"""
    errors = []
    
    # Validate business license
    license_number = data.get("business_license", "").strip()
    if not license_number:
        errors.append(_("Business license number is required"))
    elif len(license_number) != 7 or not license_number.isdigit():
        errors.append(_("Business license must be 7 digits"))
    else:
        # Check if license exists in system (mock validation for now)
        if license_number.startswith("0000"):
            errors.append(_("Invalid license number"))
    
    # Validate workshop names
    if not data.get("workshop_name", "").strip():
        errors.append(_("Workshop name in English is required"))
    
    if not data.get("workshop_name_ar", "").strip():
        errors.append(_("Workshop name in Arabic is required"))
    
    # Validate workshop type
    if not data.get("workshop_type", ""):
        errors.append(_("Workshop type is required"))
    
    # Validate governorate
    if not data.get("governorate", ""):
        errors.append(_("Governorate is required"))
    
    return errors

def _validate_admin_step(data: Dict[str, Any]) -> List[str]:
    """Validate admin account step"""
    errors = []
    
    # Validate required fields
    required_fields = {
        "first_name": _("First name is required"),
        "last_name": _("Last name is required"),
        "email": _("Email address is required"),
        "mobile_number": _("Mobile number is required"),
        "username": _("Username is required"),
        "password": _("Password is required")
    }
    
    for field, error_msg in required_fields.items():
        if not data.get(field, "").strip():
            errors.append(error_msg)
    
    # Validate email format
    email = data.get("email", "").strip()
    if email and not frappe.utils.validate_email_address(email):
        errors.append(_("Invalid email format"))
    
    # Check if email already exists
    if email and frappe.db.exists("User", {"email": email}):
        errors.append(_("Email address already exists"))
    
    # Validate username
    username = data.get("username", "").strip()
    if username:
        if len(username) < 3:
            errors.append(_("Username must be at least 3 characters"))
        elif frappe.db.exists("User", {"username": username}):
            errors.append(_("Username already exists"))
    
    # Validate mobile number (Oman format)
    mobile = data.get("mobile_number", "").strip()
    if mobile and not _validate_oman_mobile(mobile):
        errors.append(_("Invalid Oman mobile number format"))
    
    # Validate password strength
    password = data.get("password", "")
    if password:
        password_errors = _validate_password_strength(password)
        errors.extend(password_errors)
    
    return errors

def _validate_workshop_step(data: Dict[str, Any]) -> List[str]:
    """Validate workshop configuration step"""
    errors = []
    
    # Validate working hours
    start_time = data.get("working_hours_start", "")
    end_time = data.get("working_hours_end", "")
    
    if not start_time:
        errors.append(_("Working hours start time is required"))
    if not end_time:
        errors.append(_("Working hours end time is required"))
    
    if start_time and end_time:
        try:
            from datetime import datetime
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")
            if start >= end:
                errors.append(_("End time must be after start time"))
        except ValueError:
            errors.append(_("Invalid time format"))
    
    # Validate capacity
    capacity = data.get("service_capacity_daily")
    if capacity and (not isinstance(capacity, (int, float)) or capacity <= 0):
        errors.append(_("Daily service capacity must be a positive number"))
    
    return errors

def _validate_oman_mobile(mobile: str) -> bool:
    """Validate Oman mobile number format"""
    import re
    # Oman mobile format: +968XXXXXXXX (8 digits after country code)
    pattern = r'^\+968\d{8}$'
    return bool(re.match(pattern, mobile))

def _validate_password_strength(password: str) -> List[str]:
    """Validate password strength"""
    import re
    errors = []
    
    if len(password) < 8:
        errors.append(_("Password must be at least 8 characters"))
    
    if not re.search(r'[A-Z]', password):
        errors.append(_("Password must contain at least one uppercase letter"))
    
    if not re.search(r'[a-z]', password):
        errors.append(_("Password must contain at least one lowercase letter"))
    
    if not re.search(r'\d', password):
        errors.append(_("Password must contain at least one number"))
    
    return errors

@frappe.whitelist(allow_guest=True)
def save_step_data(progress_id: str, step_name: str, data: str):
    """
    Save step data to database
    """
    try:
        step_data = json.loads(data) if isinstance(data, str) else data
        
        if progress_id.startswith("guest_"):
            # For guest users, store in session/cache temporarily
            frappe.cache().set_value(f"onboarding_{progress_id}", {
                "step_name": step_name,
                "data": step_data,
                "timestamp": frappe.utils.now()
            }, expires_in_sec=3600)  # 1 hour
            
            return {
                "success": True,
                "message": _("Step data saved temporarily")
            }
        
        # For authenticated users, save to database
        progress = frappe.get_doc("Onboarding Progress", progress_id)
        
        # Update form data
        existing_data = json.loads(progress.form_data or "{}")
        existing_data[step_name] = step_data
        progress.form_data = json.dumps(existing_data)
        
        # Update completed steps
        completed_steps = json.loads(progress.completed_steps or "[]")
        if step_name not in completed_steps:
            completed_steps.append(step_name)
        progress.completed_steps = json.dumps(completed_steps)
        
        # Update current step
        step_order = ["license_verification", "admin_account", "workshop_config"]
        if step_name in step_order:
            current_step_index = step_order.index(step_name) + 1
            progress.current_step = min(current_step_index, len(step_order) - 1)
        
        progress.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": _("Step data saved successfully"),
            "next_step": step_order[current_step_index] if current_step_index < len(step_order) else None,
            "progress_percentage": (len(completed_steps) / len(step_order)) * 100
        }
        
    except Exception as e:
        frappe.log_error(f"Save step data failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to save step data"),
            "errors": [str(e)]
        }

@frappe.whitelist(allow_guest=True)
def complete_onboarding(progress_id: str):
    """
    Complete the onboarding process and create workshop
    """
    try:
        if progress_id.startswith("guest_"):
            # Handle guest completion
            cached_data = frappe.cache().get_value(f"onboarding_{progress_id}")
            if not cached_data:
                return {
                    "success": False,
                    "errors": [_("Session expired. Please start over.")]
                }
            
            return {
                "success": True,
                "message": _("Guest onboarding completed. Please sign up to continue."),
                "workshop_profile": None,
                "workshop_code": f"DEMO_{frappe.utils.random_string(6)}",
                "license_mode": False
            }
        
        # Get onboarding progress
        progress = frappe.get_doc("Onboarding Progress", progress_id)
        form_data = json.loads(progress.form_data or "{}")
        
        # Create workshop profile
        workshop_result = _create_workshop_profile(form_data)
        if not workshop_result["success"]:
            return workshop_result
        
        # Create admin user
        user_result = _create_admin_user(form_data, workshop_result["workshop_code"])
        if not user_result["success"]:
            return user_result
        
        # Configure system settings
        _configure_system_settings(form_data)
        
        # Configure selected modules
        _configure_selected_modules(form_data.get("workshop_config", {}).get("selected_modules", []))
        
        # Mark progress as completed
        progress.status = "Completed"
        progress.completed_at = frappe.utils.now()
        progress.save(ignore_permissions=True)
        
        # Handle post-completion redirect
        from universal_workshop.utils.browser_launcher import InstallationRedirectManager
        redirect_result = InstallationRedirectManager.handle_onboarding_completion(workshop_result["workshop_code"])
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Workshop setup completed successfully!"),
            "workshop_profile": workshop_result["workshop_profile"],
            "workshop_code": workshop_result["workshop_code"],
            "admin_username": user_result["username"],
            "license_mode": frappe.db.get_single_value("System Settings", "license_has_workshop_data") == 1,
            "redirect_url": redirect_result.get("redirect_url", "/app/workspace/Workshop%20Management")
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Complete onboarding failed: {str(e)}")
        return {
            "success": False,
            "errors": [_("Failed to complete onboarding: {0}").format(str(e))]
        }

def _create_workshop_profile(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create workshop profile from onboarding data"""
    try:
        license_data = form_data.get("license_verification", {})
        config_data = form_data.get("workshop_config", {})
        
        # Generate unique workshop code
        workshop_code = f"WS{frappe.utils.random_string(6).upper()}"
        
        workshop_profile = frappe.get_doc({
            "doctype": "Workshop Profile",
            "workshop_code": workshop_code,
            "workshop_name": license_data.get("workshop_name"),
            "workshop_name_ar": license_data.get("workshop_name_ar"),
            "workshop_type": license_data.get("workshop_type"),
            "status": "Active",
            "governorate": license_data.get("governorate"),
            "business_license": license_data.get("business_license"),
            "working_hours_start": config_data.get("working_hours_start", "08:00"),
            "working_hours_end": config_data.get("working_hours_end", "18:00"),
            "weekend_days": config_data.get("weekend_days", "Friday-Saturday"),
            "service_capacity_daily": config_data.get("service_capacity_daily", 20),
            "currency": config_data.get("currency", "OMR"),
            "default_language": config_data.get("default_language", "en"),
            "timezone": config_data.get("timezone", "Asia/Muscat")
        })
        
        workshop_profile.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "workshop_profile": workshop_profile.name,
            "workshop_code": workshop_code
        }
        
    except Exception as e:
        return {
            "success": False,
            "errors": [_("Failed to create workshop profile: {0}").format(str(e))]
        }

def _create_admin_user(form_data: Dict[str, Any], workshop_code: str) -> Dict[str, Any]:
    """Create administrator user"""
    try:
        admin_data = form_data.get("admin_account", {})
        
        # Create user
        user = frappe.get_doc({
            "doctype": "User",
            "email": admin_data.get("email"),
            "username": admin_data.get("username"),
            "first_name": admin_data.get("first_name"),
            "last_name": admin_data.get("last_name"),
            "mobile_no": admin_data.get("mobile_number"),
            "language": admin_data.get("default_language", "en"),
            "time_zone": admin_data.get("timezone", "Asia/Muscat"),
            "send_welcome_email": 0,
            "enabled": 1,
            "user_type": "System User"
        })
        
        # Set password
        user.new_password = admin_data.get("password")
        user.insert(ignore_permissions=True)
        
        # Assign roles
        user.add_roles("System Manager", "Workshop Manager")
        
        # Set user preferences
        user_prefs = {
            "workshop_code": workshop_code,
            "enable_two_factor": admin_data.get("enable_two_factor", False),
            "onboarding_completed": True
        }
        
        for key, value in user_prefs.items():
            frappe.db.set_value("User", user.name, key, value)
        
        return {
            "success": True,
            "username": user.username,
            "user_id": user.name
        }
        
    except Exception as e:
        return {
            "success": False,
            "errors": [_("Failed to create admin user: {0}").format(str(e))]
        }

def _configure_system_settings(form_data: Dict[str, Any]):
    """Configure system settings based on onboarding data"""
    config_data = form_data.get("workshop_config", {})
    
    # Update system settings
    settings = {
        "country": "Oman",
        "currency": config_data.get("currency", "OMR"),
        "time_zone": config_data.get("timezone", "Asia/Muscat"),
        "language": config_data.get("default_language", "en"),
        "date_format": "dd-mm-yyyy",
        "number_format": "#,###.##",
        "onboarding_completed": 1
    }
    
    for key, value in settings.items():
        frappe.db.set_single_value("System Settings", key, value)

def _configure_selected_modules(selected_modules: List[str]):
    """Configure selected modules"""
    try:
        from universal_workshop.setup.module_configuration import configure_modules_for_license
        
        # Get license type (mock for now)
        license_type = "basic"  # This would come from actual license validation
        
        configure_modules_for_license(license_type, selected_modules)
        
    except Exception as e:
        frappe.log_error(f"Module configuration failed: {str(e)}")

@frappe.whitelist(allow_guest=True)
def rollback_onboarding(progress_id: str, reason: str = "User cancelled"):
    """
    Rollback/cancel onboarding process
    """
    try:
        if progress_id.startswith("guest_"):
            # Clear guest cache
            frappe.cache().delete_value(f"onboarding_{progress_id}")
            return {
                "success": True,
                "message": _("Guest session cleared")
            }
        
        # Mark progress as cancelled
        progress = frappe.get_doc("Onboarding Progress", progress_id)
        progress.status = "Cancelled"
        progress.cancellation_reason = reason
        progress.cancelled_at = frappe.utils.now()
        progress.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": _("Onboarding cancelled successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Rollback onboarding failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to cancel onboarding")
        }