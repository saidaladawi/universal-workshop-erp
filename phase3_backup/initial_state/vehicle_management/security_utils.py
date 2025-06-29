"""
Security Utilities for Vehicle Management Module
Provides input validation, sanitization, and security checks
"""

import re
import time
from typing import Dict, List, Pattern, Optional, ClassVar

import frappe
from frappe import _


class VehicleSecurityValidator:
    """Security validation for vehicle management operations"""

    # Validation patterns
    VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
    LICENSE_PLATE_PATTERNS: ClassVar[Dict[str, Pattern]] = {
        "oman": re.compile(r"^\d{1,6}\s?[A-Z]{1,3}$", re.IGNORECASE),
        "general": re.compile(r"^[A-Z0-9\s\-]{1,12}$", re.IGNORECASE),
    }

    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS: ClassVar[List[str]] = [
        r"('|(\\')|(;)|(\\)|(--)|(\s*(select|insert|update|delete|drop|create|alter|exec|execute)\s)",
        r"(\bunion\b)|(\bor\b\s+\d+\s*=\s*\d+)|(\band\b\s+\d+\s*=\s*\d+)",
        r"(\bxp_cmdshell\b)|(\bsp_executesql\b)|(\bschema\b)",
    ]

    @classmethod
    def validate_vin(cls, vin):
        """
        Validate VIN format and check digit

        Args:
            vin (str): Vehicle Identification Number

        Returns:
            dict: Validation result with status and message
        """
        if not vin:
            return {"valid": False, "message": _("VIN is required")}

        vin = vin.strip().upper()

        # Check length
        if len(vin) != 17:
            return {"valid": False, "message": _("VIN must be exactly 17 characters")}

        # Check pattern (no I, O, Q allowed)
        if not cls.VIN_PATTERN.match(vin):
            return {
                "valid": False,
                "message": _("VIN contains invalid characters (I, O, Q not allowed)"),
            }

        # Check for duplicate
        if frappe.db.exists("Vehicle", {"vin": vin}):
            return {"valid": False, "message": _("Vehicle with this VIN already exists")}

        return {"valid": True, "formatted_vin": vin}

    @classmethod
    def validate_license_plate(cls, license_plate, country="oman"):
        """
        Validate license plate format based on country

        Args:
            license_plate (str): License plate number
            country (str): Country code for validation pattern

        Returns:
            dict: Validation result
        """
        if not license_plate:
            return {"valid": False, "message": _("License plate is required")}

        license_plate = license_plate.strip()
        pattern = cls.LICENSE_PLATE_PATTERNS.get(country, cls.LICENSE_PLATE_PATTERNS["general"])

        if not pattern.match(license_plate):
            return {"valid": False, "message": _("Invalid license plate format")}

        return {"valid": True, "formatted_plate": license_plate.upper()}

    @classmethod
    def sanitize_search_query(cls, query):
        """
        Sanitize search query to prevent SQL injection

        Args:
            query (str): Search query string

        Returns:
            str: Sanitized query or raises exception if malicious
        """
        if not query:
            return ""

        query = query.strip()

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                frappe.throw(_("Invalid search query detected"))

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', "", query)

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized

    @classmethod
    def validate_year(cls, year):
        """
        Validate vehicle year

        Args:
            year (int): Vehicle year

        Returns:
            dict: Validation result
        """
        if not year:
            return {"valid": False, "message": _("Vehicle year is required")}

        current_year = frappe.utils.now_datetime().year

        if year < 1900 or year > current_year + 2:
            return {
                "valid": False,
                "message": _("Vehicle year must be between 1900 and {0}").format(current_year + 2),
            }

        return {"valid": True}

    @classmethod
    def validate_mileage(cls, mileage, previous_mileage=None):
        """
        Validate vehicle mileage

        Args:
            mileage (float): Current mileage
            previous_mileage (float): Previous recorded mileage

        Returns:
            dict: Validation result
        """
        if mileage is None:
            return {"valid": True}  # Mileage is optional

        if mileage < 0:
            return {"valid": False, "message": _("Mileage cannot be negative")}

        if mileage > 9999999:  # 9.9M km reasonable max
            return {"valid": False, "message": _("Mileage seems unreasonably high")}

        if previous_mileage and mileage < previous_mileage:
            return {"valid": False, "message": _("Mileage cannot be less than previous reading")}

        return {"valid": True}

    @classmethod
    def check_user_vehicle_access(cls, vehicle_name, user=None):
        """
        Check if user has access to specific vehicle

        Args:
            vehicle_name (str): Vehicle document name
            user (str): User ID (optional, defaults to current user)

        Returns:
            bool: True if user has access
        """
        if not user:
            user = frappe.session.user

        # System users have full access
        if user in ["Administrator", "system"]:
            return True

        # Check if user is linked to vehicle's customer
        vehicle = frappe.get_doc("Vehicle", vehicle_name)

        # Workshop managers have access to all vehicles
        if frappe.db.exists("Has Role", {"parent": user, "role": "Workshop Manager"}):
            return True

        # Customer users only access their own vehicles
        if frappe.db.exists("Has Role", {"parent": user, "role": "Customer"}):
            customer_link = frappe.db.get_value("Customer", {"email_id": user}, "name")
            return customer_link == vehicle.customer

        return False

    @classmethod
    def validate_api_request_limit(cls, user=None, endpoint=None):
        """
        Check API request rate limiting

        Args:
            user (str): User making the request
            endpoint (str): API endpoint being called

        Returns:
            bool: True if request is allowed
        """
        if not user:
            user = frappe.session.user

        # Skip for system users
        if user in ["Administrator", "system"]:
            return True

        # Check rate limiting (example: 100 requests per hour for VIN decoder)
        if endpoint == "decode_vin":
            cache_key = f"vin_decode_requests_{user}"
            request_count = frappe.cache().get(cache_key) or 0

            if request_count >= 100:  # 100 requests per hour limit
                frappe.throw(_("Rate limit exceeded. Please try again later."))

            # Increment counter
            frappe.cache().set(cache_key, request_count + 1, expires_in_sec=3600)

        return True


def validate_vehicle_data(vehicle_doc):
    """
    Comprehensive validation for vehicle document

    Args:
        vehicle_doc: Vehicle document instance

    Raises:
        ValidationError: If validation fails
    """
    validator = VehicleSecurityValidator()

    # Validate VIN
    vin_result = validator.validate_vin(vehicle_doc.vin)
    if not vin_result["valid"]:
        frappe.throw(vin_result["message"])

    # Validate license plate
    plate_result = validator.validate_license_plate(vehicle_doc.license_plate)
    if not plate_result["valid"]:
        frappe.throw(plate_result["message"])

    # Validate year
    year_result = validator.validate_year(vehicle_doc.year)
    if not year_result["valid"]:
        frappe.throw(year_result["message"])

    # Validate mileage
    mileage_result = validator.validate_mileage(vehicle_doc.current_mileage)
    if not mileage_result["valid"]:
        frappe.throw(mileage_result["message"])


# Security decorators
def require_vehicle_access(vehicle_field="vehicle"):
    """
    Decorator to check vehicle access permissions

    Args:
        vehicle_field (str): Field name containing vehicle reference
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            vehicle_name = kwargs.get(vehicle_field)
            if vehicle_name and not VehicleSecurityValidator.check_user_vehicle_access(
                vehicle_name
            ):
                frappe.throw(_("Insufficient permissions for this vehicle"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit(endpoint):
    """
    Decorator for API rate limiting

    Args:
        endpoint (str): Endpoint identifier for rate limiting
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            VehicleSecurityValidator.validate_api_request_limit(endpoint=endpoint)
            return func(*args, **kwargs)

        return wrapper

    return decorator
