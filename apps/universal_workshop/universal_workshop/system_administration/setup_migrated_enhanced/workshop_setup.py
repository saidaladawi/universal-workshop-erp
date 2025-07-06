# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
import os


@frappe.whitelist()
def get_onboarding_data():
    """Get initial onboarding data from license file"""
    try:
        # Get license data
        license_data = get_license_file_data()

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
def complete_onboarding_with_license(data):
    """Complete onboarding process using license and user data"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data

        # Get license data first
        license_data = get_license_file_data()
        if not license_data:
            frappe.throw(_("License file not found"))

        # Create Workshop Profile with license data
        workshop_profile = create_workshop_profile(license_data, data)

        # Create admin user if specified
        if data.get("create_admin_user"):
            admin_user = create_admin_user(data.get("admin_user_data", {}))

        # Mark setup as complete
        frappe.db.set_default("setup_complete", "1")
        frappe.db.set_default("license_has_workshop_data", "1")

        # Create onboarding progress record
        onboarding_progress = frappe.get_doc({
            "doctype": "Onboarding Progress",
            "workshop_profile": workshop_profile.name,
            "completed_on": frappe.utils.now(),
            "completed_by": frappe.session.user,
            "docstatus": 1
        })
        onboarding_progress.insert()

        frappe.db.commit()

        return {
            "success": True,
            "message": _("Onboarding completed successfully"),
            "workshop_profile": workshop_profile.name,
            "redirect_to": "/app/workspace/Workshop%20Management"
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in complete_onboarding_with_license: {e}")
        frappe.throw(str(e))


def create_workshop_profile(license_data, user_data):
    """Create Workshop Profile using license and user data"""

    # Check if workshop profile already exists
    existing_profile = frappe.db.exists("Workshop Profile",
                                       {"workshop_name": license_data.get("workshop_name_en")})

    if existing_profile:
        return frappe.get_doc("Workshop Profile", existing_profile)

    workshop_profile = frappe.get_doc({
        "doctype": "Workshop Profile",
        "workshop_name": license_data.get("workshop_name_en"),
        "workshop_name_ar": license_data.get("workshop_name_ar"),
        "license_id": license_data.get("license_id"),
        "license_type": license_data.get("license_type"),
        "max_users": license_data.get("max_users", 5),
        "status": "Active",

        # User provided data
        "owner_name": user_data.get("owner_name", ""),
        "contact_email": user_data.get("contact_email", ""),
        "contact_phone": user_data.get("contact_phone", ""),
        "address": user_data.get("address", ""),
        "city": user_data.get("city", ""),
        "country": "Oman",

        # Default settings
        "default_currency": "OMR",
        "language": "ar",
        "time_zone": "Asia/Muscat"
    })

    workshop_profile.insert()
    return workshop_profile


def create_admin_user(admin_data):
    """Create admin user for the workshop"""
    try:
        email = admin_data.get("email")
        if not email:
            return None

        # Check if user already exists
        if frappe.db.exists("User", email):
            return frappe.get_doc("User", email)

        admin_user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": admin_data.get("first_name", "Workshop"),
            "last_name": admin_data.get("last_name", "Manager"),
            "enabled": 1,
            "user_type": "System User",
            "language": "ar",
            "time_zone": "Asia/Muscat",
            "send_welcome_email": 0,
            "roles": [
                {"role": "Workshop Manager"},
                {"role": "Workshop Owner"},
                {"role": "System Manager"}
            ]
        })

        admin_user.insert()

        # Set password if provided
        if admin_data.get("password"):
            admin_user.new_password = admin_data.get("password")
            admin_user.save()

        return admin_user

    except Exception as e:
        frappe.log_error(f"Error creating admin user: {e}")
        return None


def get_license_file_data():
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


@frappe.whitelist()
def check_setup_status():
    """Check if initial setup is required"""
    try:
        # Check setup completion
        setup_complete = frappe.db.get_default("setup_complete") == "1"

        # Check license data availability
        license_data = get_license_file_data()
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
def get_user_home_page(user):
    """Determine the appropriate home page for the user based on setup status"""
    try:
        # Check if setup is complete
        setup_status = check_setup_status()

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
