#!/usr/bin/env python3
"""
Universal Workshop ERP License Manager
Manages software licensing and hardware binding for workshop installations
"""
import frappe
import hashlib
import platform
import psutil
import uuid
from datetime import datetime, timedelta
from frappe import _
from frappe.utils import now_datetime, add_days


class LicenseManager:
    """
    License management system for Universal Workshop ERP
    Handles hardware fingerprinting, license validation, and business binding
    """

    def __init__(self):
        self.hardware_id = self._generate_hardware_id()
        self.installation_id = self._get_installation_id()

    def _generate_hardware_id(self):
        """Generate unique hardware fingerprint for this machine"""
        try:
            # Get system identifiers
            machine_id = platform.machine()
            processor = platform.processor()

            # Get MAC address
            mac = ":".join(
                ["{:02x}".format((uuid.getnode() >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][
                    ::-1
                ]
            )

            # Get system info
            system_info = f"{platform.system()}-{platform.release()}"

            # Create fingerprint
            fingerprint_data = f"{machine_id}|{processor}|{mac}|{system_info}"
            hardware_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

            return hardware_id

        except Exception as e:
            frappe.log_error(f"Hardware ID generation failed: {e}")
            return "default-hardware-id"

    def _get_installation_id(self):
        """Get or create installation ID"""
        try:
            # Check if installation ID exists in System Settings
            installation_id = frappe.db.get_single_value("System Settings", "installation_id")

            if not installation_id:
                # Generate new installation ID
                installation_id = f"UW-{uuid.uuid4().hex[:8].upper()}"

                # Save to System Settings
                frappe.db.set_single_value("System Settings", "installation_id", installation_id)
                frappe.db.commit()

            return installation_id

        except Exception as e:
            frappe.log_error(f"Installation ID retrieval failed: {e}")
            return "UW-DEFAULT"

    def validate_license(self, business_name=None, license_key=None):
        """
        Validate software license

        Args:
            business_name (str): Registered business name
            license_key (str): License key (optional for demo)

        Returns:
            dict: Validation result
        """
        try:
            # For demo/development purposes, allow basic validation
            if not business_name:
                return {
                    "is_valid": False,
                    "message": _("Business name is required for license validation"),
                    "days_remaining": 0,
                }

            # Check if this is demo mode
            if license_key == "DEMO" or not license_key:
                return self._validate_demo_license(business_name)

            # Production license validation would go here
            return self._validate_production_license(business_name, license_key)

        except Exception as e:
            frappe.log_error(f"License validation failed: {e}")
            return {
                "is_valid": False,
                "message": _("License validation error occurred"),
                "days_remaining": 0,
            }

    def _validate_demo_license(self, business_name):
        """Validate demo license (30 days trial)"""
        try:
            # Check installation date
            installation_date = frappe.db.get_single_value("System Settings", "installation_date")

            if not installation_date:
                # First time setup
                installation_date = now_datetime()
                frappe.db.set_single_value(
                    "System Settings", "installation_date", installation_date
                )
                frappe.db.commit()

            # Calculate days remaining
            expiry_date = add_days(installation_date, 30)
            current_date = now_datetime()
            days_remaining = (expiry_date - current_date).days

            if days_remaining > 0:
                return {
                    "is_valid": True,
                    "license_type": "demo",
                    "message": _("Demo license active"),
                    "days_remaining": days_remaining,
                    "business_name": business_name,
                    "hardware_id": self.hardware_id,
                }
            else:
                return {
                    "is_valid": False,
                    "license_type": "expired",
                    "message": _("Demo license has expired"),
                    "days_remaining": 0,
                }

        except Exception as e:
            frappe.log_error(f"Demo license validation failed: {e}")
            return {
                "is_valid": False,
                "message": _("Demo license validation error"),
                "days_remaining": 0,
            }

    def _validate_production_license(self, business_name, license_key):
        """Validate production license"""
        # This would implement real license validation
        # For now, return a basic validation
        return {
            "is_valid": True,
            "license_type": "production",
            "message": _("Production license active"),
            "days_remaining": 365,
            "business_name": business_name,
            "hardware_id": self.hardware_id,
        }

    def get_license_status(self):
        """Get current license status"""
        try:
            # Get business registration
            business_registrations = frappe.get_list("Business Registration", limit=1)

            if business_registrations:
                business = frappe.get_doc("Business Registration", business_registrations[0].name)
                return self.validate_license(business.business_name_en, business.license_key)
            else:
                return {
                    "is_valid": False,
                    "message": _("No business registration found"),
                    "days_remaining": 0,
                }

        except Exception as e:
            frappe.log_error(f"License status check failed: {e}")
            return {
                "is_valid": False,
                "message": _("Unable to check license status"),
                "days_remaining": 0,
            }

    def bind_to_business(self, business_name, contact_email):
        """Bind license to specific business"""
        try:
            binding_data = {
                "business_name": business_name,
                "contact_email": contact_email,
                "hardware_id": self.hardware_id,
                "installation_id": self.installation_id,
                "binding_date": now_datetime(),
                "system_info": {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "machine_type": platform.machine(),
                },
            }

            # Store binding information
            frappe.db.set_single_value(
                "System Settings", "license_binding", frappe.as_json(binding_data)
            )
            frappe.db.commit()

            return {
                "success": True,
                "message": _("License successfully bound to business"),
                "binding_data": binding_data,
            }

        except Exception as e:
            frappe.log_error(f"Business binding failed: {e}")
            return {"success": False, "message": _("Failed to bind license to business")}


# Utility functions
def get_license_manager():
    """Get LicenseManager instance"""
    return LicenseManager()


@frappe.whitelist()
def check_license_status():
    """API endpoint to check license status"""
    license_manager = get_license_manager()
    return license_manager.get_license_status()


@frappe.whitelist()
def validate_business_license(business_name, license_key=None):
    """API endpoint to validate business license"""
    license_manager = get_license_manager()
    return license_manager.validate_license(business_name, license_key)


def is_license_valid():
    """Quick check if license is valid"""
    try:
        license_manager = get_license_manager()
        status = license_manager.get_license_status()
        return status.get("is_valid", False)
    except:
        return False


def get_trial_days_remaining():
    """Get remaining trial days"""
    try:
        license_manager = get_license_manager()
        status = license_manager.get_license_status()
        return status.get("days_remaining", 0)
    except:
        return 0
