# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
from datetime import datetime, time

import frappe
from frappe import _
from frappe.utils import validate_email_address, validate_url


class OnboardingWizard:
    """Workshop Onboarding Wizard Backend Logic"""

    def __init__(self):
        # Check license mode
        license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"
        
        if license_has_data:
            # Admin-only mode for license-based setup
            self.steps = ["admin_account"]
        else:
            # Full onboarding mode
            self.steps = [
                "basic_info",
                "admin_account",
                "business_info",
                "contact_info",
                "operational_details",
                "financial_info",
            ]
        self.current_step = 0
        self.validation_errors = []
        self.license_mode = license_has_data

    def get_wizard_progress(self, user_id=None):
        """Get current onboarding progress for user"""
        if not user_id:
            user_id = frappe.session.user

        progress = frappe.db.get_value(
            "Onboarding Progress",
            {"user": user_id, "docstatus": 0},
            ["current_step", "completed_steps", "data", "name"],
        )

        if progress:
            return {
                "exists": True,
                "current_step": progress[0] or 0,
                "completed_steps": frappe.parse_json(progress[1]) if progress[1] else [],
                "data": frappe.parse_json(progress[2]) if progress[2] else {},
                "progress_id": progress[3],
            }
        else:
            return {
                "exists": False,
                "current_step": 0,
                "completed_steps": [],
                "data": {},
                "progress_id": None,
            }


@frappe.whitelist()
def start_onboarding_wizard():
    """Initialize new onboarding wizard session"""
    user_id = frappe.session.user

    # Check if user already has an active onboarding session
    existing = frappe.db.exists("Onboarding Progress", {"user": user_id, "docstatus": 0})

    if existing:
        return {
            "success": True,
            "message": _("Resuming existing onboarding session"),
            "progress_id": existing,
        }

    # Create new onboarding progress record
    progress = frappe.new_doc("Onboarding Progress")
    progress.user = user_id
    progress.current_step = 0
    progress.completed_steps = "[]"
    progress.data = "{}"
    progress.started_on = datetime.now()
    progress.insert()

    return {
        "success": True,
        "message": _("Onboarding wizard started successfully"),
        "progress_id": progress.name,
    }


@frappe.whitelist()
def validate_step_data(step_name, data):
    """Validate data for specific onboarding step"""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    validator = OnboardingStepValidator()

    if step_name == "basic_info":
        return validator.validate_basic_info(data)
    elif step_name == "admin_account":
        return validator.validate_admin_account(data)
    elif step_name == "business_info":
        return validator.validate_business_info(data)
    elif step_name == "contact_info":
        return validator.validate_contact_info(data)
    elif step_name == "operational_details":
        return validator.validate_operational_details(data)
    elif step_name == "financial_info":
        return validator.validate_financial_info(data)
    else:
        return {"valid": False, "errors": [_("Invalid step name: {0}").format(step_name)]}


@frappe.whitelist()
def save_step_data(progress_id, step_name, data):
    """Save validated step data to onboarding progress"""
    data = frappe.parse_json(data) if isinstance(data, str) else data

    # Validate step data first
    validation_result = validate_step_data(step_name, data)

    if not validation_result.get("valid"):
        return {"success": False, "errors": validation_result.get("errors", [])}

    try:
        # Get onboarding progress record
        progress = frappe.get_doc("Onboarding Progress", progress_id)

        # Update progress data
        current_data = frappe.parse_json(progress.data) if progress.data else {}
        current_data[step_name] = data
        progress.data = frappe.as_json(current_data)

        # Update completed steps
        completed_steps = (
            frappe.parse_json(progress.completed_steps) if progress.completed_steps else []
        )
        if step_name not in completed_steps:
            completed_steps.append(step_name)
        progress.completed_steps = frappe.as_json(completed_steps)

        # Update current step to next step
        license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"
        
        if license_has_data:
            # Admin-only mode
            steps = ["admin_account"]
        else:
            # Full onboarding mode
            steps = [
                "basic_info",
                "admin_account",
                "business_info",
                "contact_info",
                "operational_details",
                "financial_info",
            ]
        current_step_index = steps.index(step_name)
        if current_step_index < len(steps) - 1:
            progress.current_step = current_step_index + 1
        else:
            progress.current_step = len(steps)  # All steps completed

        progress.modified = datetime.now()
        progress.save()

        return {
            "success": True,
            "message": _("Step data saved successfully"),
            "next_step": (
                steps[current_step_index + 1] if current_step_index < len(steps) - 1 else None
            ),
            "progress_percentage": (len(completed_steps) / len(steps)) * 100,
        }

    except Exception as e:
        frappe.log_error(f"Error saving step data: {e!s}")
        return {"success": False, "errors": [_("Failed to save step data: {0}").format(str(e))]}


@frappe.whitelist()
def complete_onboarding(progress_id):
    """Complete onboarding and create Workshop Profile"""
    try:
        progress = frappe.get_doc("Onboarding Progress", progress_id)
        onboarding_data = frappe.parse_json(progress.data)
        
        # Check if this is license-based setup
        license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"

        if license_has_data:
            # License-based setup - only admin account required
            required_steps = ["admin_account"]
            completed_steps = frappe.parse_json(progress.completed_steps)

            missing_steps = [step for step in required_steps if step not in completed_steps]
            if missing_steps:
                return {
                    "success": False,
                    "errors": [
                        _("Please complete admin account creation")
                    ],
                }

            # Create Workshop Profile from existing license data
            workshop_profile = create_workshop_from_license(onboarding_data.get("admin_account", {}))
        else:
            # Full onboarding mode
            required_steps = [
                "basic_info",
                "admin_account",
                "business_info",
                "contact_info",
                "operational_details",
                "financial_info",
            ]
            completed_steps = frappe.parse_json(progress.completed_steps)

            missing_steps = [step for step in required_steps if step not in completed_steps]
            if missing_steps:
                return {
                    "success": False,
                    "errors": [
                        _("Please complete all required steps: {0}").format(", ".join(missing_steps))
                    ],
                }

            # Create Workshop Profile from onboarding data
            workshop_profile = create_workshop_profile_from_onboarding(onboarding_data)

        # Create administrator user account
        admin_data = onboarding_data.get("admin_account", {})
        admin_result = create_admin_user(admin_data, workshop_profile)

        if not admin_result.get("success"):
            return admin_result

        # Mark onboarding as completed
        progress.docstatus = 1
        progress.completed_on = datetime.now()
        progress.workshop_profile = workshop_profile.name
        progress.save()

        return {
            "success": True,
            "message": _("Workshop onboarding completed successfully"),
            "workshop_profile": workshop_profile.name,
            "workshop_code": workshop_profile.workshop_code,
            "license_mode": license_has_data
        }

    except Exception as e:
        frappe.log_error(f"Error completing onboarding: {e!s}")
        return {
            "success": False,
            "errors": [_("Failed to complete onboarding: {0}").format(str(e))],
        }


def create_workshop_from_license(admin_data):
    """Create Workshop Profile from existing Business Registration license"""
    try:
        # Get the first verified business registration
        business_regs = frappe.get_list(
            "Business Registration", 
            filters={"verification_status": "Verified"},
            fields=["*"],
            limit=1
        )
        
        if not business_regs:
            frappe.throw(_("No verified business registration found"))
            
        business_reg = frappe.get_doc("Business Registration", business_regs[0].name)
        
        # Create workshop profile from license data
        workshop = frappe.new_doc("Workshop Profile")
        
        # Map license data to workshop profile
        workshop.workshop_name = business_reg.business_name_en
        workshop.workshop_name_ar = business_reg.business_name_ar
        workshop.business_license = business_reg.business_license_number
        workshop.owner_name = business_reg.owner_name_en
        workshop.owner_name_ar = business_reg.owner_name_ar
        
        # Contact information from license
        workshop.phone_number = business_reg.phone_number
        workshop.email = business_reg.email
        workshop.address = business_reg.address
        workshop.address_ar = business_reg.address_ar
        workshop.city = business_reg.city
        workshop.governorate = business_reg.governorate
        
        # Set defaults for missing data
        workshop.workshop_type = "General Repair"
        workshop.status = "Active"
        workshop.currency = "OMR"
        workshop.establishment_date = business_reg.registration_date
        workshop.total_staff = 5  # Default value
        
        # Working hours defaults
        workshop.working_hours_start = time(8, 0)
        workshop.working_hours_end = time(18, 0)
        workshop.weekend_days = "Friday-Saturday"
        
        workshop.insert()
        
        return workshop
        
    except Exception as e:
        frappe.log_error(f"Error creating workshop from license: {e}")
        raise


def create_workshop_profile_from_onboarding(data):
    """Transform onboarding data into Workshop Profile DocType"""

    workshop = frappe.new_doc("Workshop Profile")

    # Basic Information
    basic_info = data.get("basic_info", {})
    workshop.workshop_name = basic_info.get("workshop_name")
    workshop.workshop_name_ar = basic_info.get("workshop_name_ar")
    workshop.workshop_type = basic_info.get("workshop_type")
    workshop.owner_name = basic_info.get("owner_name")
    workshop.owner_name_ar = basic_info.get("owner_name_ar")
    workshop.establishment_date = basic_info.get("establishment_date")
    workshop.total_staff = basic_info.get("total_staff")

    # Business Information
    business_info = data.get("business_info", {})
    workshop.business_license = business_info.get("business_license")
    workshop.license_expiry_date = business_info.get("license_expiry_date")
    workshop.vat_number = business_info.get("vat_number")
    workshop.commercial_registration = business_info.get("commercial_registration")
    workshop.ministry_approval = business_info.get("ministry_approval")
    workshop.insurance_certificate = business_info.get("insurance_certificate")
    workshop.municipality_license = business_info.get("municipality_license")

    # Contact Information
    contact_info = data.get("contact_info", {})
    workshop.phone_number = contact_info.get("phone_number")
    workshop.mobile_number = contact_info.get("mobile_number")
    workshop.email = contact_info.get("email")
    workshop.website = contact_info.get("website")
    workshop.address = contact_info.get("address")
    workshop.address_ar = contact_info.get("address_ar")
    workshop.city = contact_info.get("city")
    workshop.governorate = contact_info.get("governorate")
    workshop.postal_code = contact_info.get("postal_code")

    # Operational Details
    operational_details = data.get("operational_details", {})
    workshop.working_hours_start = operational_details.get("working_hours_start")
    workshop.working_hours_end = operational_details.get("working_hours_end")
    workshop.weekend_days = operational_details.get("weekend_days")
    workshop.service_capacity_daily = operational_details.get("service_capacity_daily")
    workshop.specialization = operational_details.get("specialization")
    workshop.equipment_list = operational_details.get("equipment_list")
    workshop.certification_level = operational_details.get("certification_level")

    # Financial Information
    financial_info = data.get("financial_info", {})
    workshop.bank_name = financial_info.get("bank_name")
    workshop.bank_account = financial_info.get("bank_account")
    workshop.iban = financial_info.get("iban")
    workshop.currency = financial_info.get("currency", "OMR")

    # Set default status
    workshop.status = "Active"

    # Insert and return the workshop profile
    workshop.insert()

    return workshop


def create_admin_user(admin_data, workshop_profile):
    """Create administrator user account"""
    try:
        # Create new user
        user = frappe.new_doc("User")
        user.email = admin_data.get("admin_email")
        user.username = admin_data.get("admin_username")
        user.first_name = admin_data.get("admin_full_name")
        user.full_name = admin_data.get("admin_full_name")
        user.phone = admin_data.get("admin_phone")
        user.enabled = 1
        user.user_type = "System User"
        user.send_welcome_email = 0  # Don't send welcome email during setup

        # Set password
        user.new_password = admin_data.get("admin_password")

        # Arabic name if provided
        if admin_data.get("admin_full_name_ar"):
            user.bio = admin_data.get("admin_full_name_ar")  # Store Arabic name in bio for now

        # Insert user
        user.insert()

        # Assign roles to the admin user
        admin_roles = [
            "System Manager",
            "Administrator",
            "Workshop Manager",
            "Workshop Owner",
            "Accounts Manager",
            "Item Manager",
            "Stock Manager",
            "Sales Manager",
            "Purchase Manager",
        ]

        for role in admin_roles:
            if frappe.db.exists("Role", role):
                user.add_roles(role)

        # Create employee record for the admin
        employee = frappe.new_doc("Employee")
        employee.employee_name = admin_data.get("admin_full_name")
        employee.user_id = user.name
        employee.company = workshop_profile.workshop_name
        employee.designation = "Workshop Manager"
        employee.cell_number = admin_data.get("admin_phone")
        employee.personal_email = admin_data.get("admin_email")
        employee.status = "Active"

        if admin_data.get("admin_full_name_ar"):
            employee.employee_name_ar = admin_data.get("admin_full_name_ar")

        employee.insert()

        # Link admin user to workshop profile
        workshop_profile.admin_user = user.name
        workshop_profile.admin_employee = employee.name
        workshop_profile.save()

        return {
            "success": True,
            "user_id": user.name,
            "employee_id": employee.name,
            "message": _("Administrator account created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating admin user: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to create administrator account: {0}").format(str(e)),
        }


class OnboardingStepValidator:
    """Validation logic for each onboarding step"""

    def validate_basic_info(self, data):
        """Validate basic workshop information"""
        errors = []

        # Required fields validation
        required_fields = [
            "workshop_name",
            "workshop_name_ar",
            "workshop_type",
            "owner_name",
            "owner_name_ar",
        ]
        for field in required_fields:
            if not data.get(field):
                errors.append(_("{0} is required").format(field.replace("_", " ").title()))

        # Arabic name validation
        if data.get("workshop_name_ar") and not re.search(
            r"[\u0600-\u06FF]", data.get("workshop_name_ar")
        ):
            errors.append(_("Arabic workshop name must contain Arabic characters"))

        if data.get("owner_name_ar") and not re.search(
            r"[\u0600-\u06FF]", data.get("owner_name_ar")
        ):
            errors.append(_("Arabic owner name must contain Arabic characters"))

        # Total staff validation
        if data.get("total_staff") and (
            not isinstance(data.get("total_staff"), int) or data.get("total_staff") < 1
        ):
            errors.append(_("Total staff must be a positive number"))

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_admin_account(self, data):
        """Validate administrator account information"""
        errors = []

        # Required fields validation
        required_fields = [
            "admin_username",
            "admin_email",
            "admin_password",
            "admin_password_confirm",
            "admin_full_name",
        ]
        for field in required_fields:
            if not data.get(field):
                errors.append(_("{0} is required").format(field.replace("_", " ").title()))

        # Username validation
        if data.get("admin_username"):
            username = data.get("admin_username")
            if len(username) < 3:
                errors.append(_("Username must be at least 3 characters long"))
            if not re.match(r"^[a-zA-Z0-9_]+$", username):
                errors.append(_("Username can only contain letters, numbers and underscores"))
            # Check if username already exists
            if frappe.db.exists("User", username):
                errors.append(_("Username '{0}' already exists").format(username))

        # Email validation
        if data.get("admin_email"):
            try:
                validate_email_address(data.get("admin_email"))
            except frappe.ValidationError:
                errors.append(_("Invalid email address"))
            # Check if email already exists
            if frappe.db.exists("User", data.get("admin_email")):
                errors.append(_("Email '{0}' already exists").format(data.get("admin_email")))

        # Password validation
        if data.get("admin_password"):
            password = data.get("admin_password")
            if len(password) < 8:
                errors.append(_("Password must be at least 8 characters long"))
            if not re.search(r"[A-Z]", password):
                errors.append(_("Password must contain at least one uppercase letter"))
            if not re.search(r"[a-z]", password):
                errors.append(_("Password must contain at least one lowercase letter"))
            if not re.search(r"\d", password):
                errors.append(_("Password must contain at least one number"))

        # Password confirmation
        if data.get("admin_password") != data.get("admin_password_confirm"):
            errors.append(_("Password and confirmation password do not match"))

        # Full name validation
        if data.get("admin_full_name") and len(data.get("admin_full_name")) < 2:
            errors.append(_("Full name must be at least 2 characters long"))

        # Arabic full name validation (optional)
        if data.get("admin_full_name_ar") and not re.search(
            r"[\u0600-\u06FF]", data.get("admin_full_name_ar")
        ):
            errors.append(_("Arabic full name must contain Arabic characters"))

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_business_info(self, data):
        """Validate business license and registration information"""
        errors = []

        # Business license (required)
        if not data.get("business_license"):
            errors.append(_("Business license is required"))
        elif not re.match(r"^\d{7}$", data.get("business_license")):
            errors.append(_("Business license must be exactly 7 digits (Oman format)"))

        # VAT number validation (optional but if provided, must be valid)
        if data.get("vat_number") and not re.match(r"^OM\d{15}$", data.get("vat_number")):
            errors.append(_("VAT number must be in Oman format: OMxxxxxxxxxxxxxxx"))

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_contact_info(self, data):
        """Validate contact information"""
        errors = []

        # Phone number validation
        for field in ["phone_number", "mobile_number"]:
            phone = data.get(field)
            if phone:
                clean_phone = re.sub(r"\s+", "", phone)
                if not re.match(r"^\+968\d{8}$", clean_phone):
                    errors.append(
                        _("{0} must be in Oman format: +968 XXXXXXXX").format(
                            field.replace("_", " ").title()
                        )
                    )

        # Email validation
        if data.get("email"):
            try:
                validate_email_address(data.get("email"))
            except Exception:
                errors.append(_("Invalid email address"))

        # Website validation
        if data.get("website"):
            try:
                validate_url(data.get("website"))
            except Exception:
                errors.append(_("Invalid website URL"))

        # Required fields
        if not data.get("address") and not data.get("address_ar"):
            errors.append(_("Address is required (Arabic or English)"))

        if not data.get("city"):
            errors.append(_("City is required"))

        if not data.get("governorate"):
            errors.append(_("Governorate is required"))

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_operational_details(self, data):
        """Validate operational configuration"""
        errors = []

        # Working hours validation
        if data.get("working_hours_start") and data.get("working_hours_end"):
            try:
                start_time = datetime.strptime(
                    str(data.get("working_hours_start")), "%H:%M:%S"
                ).time()
                end_time = datetime.strptime(str(data.get("working_hours_end")), "%H:%M:%S").time()

                if start_time >= end_time:
                    errors.append(_("Working hours end time must be after start time"))
            except Exception:
                errors.append(_("Invalid working hours format"))

        # Service capacity validation
        if data.get("service_capacity_daily"):
            try:
                capacity = int(data.get("service_capacity_daily"))
                if capacity < 1:
                    errors.append(_("Daily service capacity must be at least 1"))
            except Exception:
                errors.append(_("Daily service capacity must be a valid number"))

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_financial_info(self, data):
        """Validate financial information"""
        errors = []

        # IBAN validation (optional but if provided, must be valid format)
        if data.get("iban"):
            iban = data.get("iban").replace(" ", "").upper()
            if not re.match(r"^OM\d{21}$", iban):
                errors.append(
                    _("IBAN must be in Oman format: OMxxxxxxxxxxxxxxxxx (23 characters total)")
                )

        return {"valid": len(errors) == 0, "errors": errors}


@frappe.whitelist()
def get_onboarding_step_fields(step_name):
    """Get field configuration for specific onboarding step"""

    field_configs = {
        "basic_info": [
            {
                "fieldname": "workshop_name",
                "label": _("Workshop Name (English)"),
                "fieldtype": "Data",
                "reqd": 1,
            },
            {
                "fieldname": "workshop_name_ar",
                "label": _("اسم الورشة"),
                "fieldtype": "Data",
                "reqd": 1,
            },
            {
                "fieldname": "workshop_type",
                "label": _("Workshop Type"),
                "fieldtype": "Select",
                "options": "General Repair\nBody Work\nElectrical\nEngine Specialist\nTire Services\nPainting\nAir Conditioning",
                "reqd": 1,
            },
            {
                "fieldname": "owner_name",
                "label": _("Owner Name (English)"),
                "fieldtype": "Data",
                "reqd": 1,
            },
            {
                "fieldname": "owner_name_ar",
                "label": _("اسم المالك"),
                "fieldtype": "Data",
                "reqd": 1,
            },
            {
                "fieldname": "establishment_date",
                "label": _("Establishment Date"),
                "fieldtype": "Date",
            },
            {"fieldname": "total_staff", "label": _("Total Staff"), "fieldtype": "Int"},
        ],
        "admin_account": [
            {
                "fieldname": "admin_username",
                "label": _("Administrator Username"),
                "fieldtype": "Data",
                "reqd": 1,
                "description": _(
                    "Username for system administrator (minimum 3 characters, letters, numbers and underscores only)"
                ),
            },
            {
                "fieldname": "admin_email",
                "label": _("Administrator Email"),
                "fieldtype": "Data",
                "reqd": 1,
                "description": _("Email address for system administrator"),
            },
            {
                "fieldname": "admin_full_name",
                "label": _("Administrator Full Name (English)"),
                "fieldtype": "Data",
                "reqd": 1,
                "description": _("Full name of the system administrator"),
            },
            {
                "fieldname": "admin_full_name_ar",
                "label": _("اسم المدير الكامل"),
                "fieldtype": "Data",
                "description": _("الاسم الكامل لمدير النظام باللغة العربية"),
            },
            {
                "fieldname": "admin_password",
                "label": _("Administrator Password"),
                "fieldtype": "Password",
                "reqd": 1,
                "description": _(
                    "Password must be at least 8 characters with uppercase, lowercase and numbers"
                ),
            },
            {
                "fieldname": "admin_password_confirm",
                "label": _("Confirm Password"),
                "fieldtype": "Password",
                "reqd": 1,
                "description": _("Re-enter the password to confirm"),
            },
            {
                "fieldname": "admin_phone",
                "label": _("Administrator Phone"),
                "fieldtype": "Data",
                "description": _("Phone number for administrator (Oman format: +968 XXXXXXXX)"),
            },
        ],
        "business_info": [
            {
                "fieldname": "business_license",
                "label": _("Business License (7 digits)"),
                "fieldtype": "Data",
                "reqd": 1,
            },
            {
                "fieldname": "license_expiry_date",
                "label": _("License Expiry Date"),
                "fieldtype": "Date",
            },
            {"fieldname": "vat_number", "label": _("VAT Registration Number"), "fieldtype": "Data"},
            {
                "fieldname": "commercial_registration",
                "label": _("Commercial Registration"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "ministry_approval",
                "label": _("Ministry Approval Number"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "insurance_certificate",
                "label": _("Insurance Certificate"),
                "fieldtype": "Data",
            },
            {
                "fieldname": "municipality_license",
                "label": _("Municipality License"),
                "fieldtype": "Data",
            },
        ],
        "contact_info": [
            {"fieldname": "phone_number", "label": _("Phone Number (+968)"), "fieldtype": "Data"},
            {"fieldname": "mobile_number", "label": _("Mobile Number (+968)"), "fieldtype": "Data"},
            {"fieldname": "email", "label": _("Email"), "fieldtype": "Data"},
            {"fieldname": "website", "label": _("Website"), "fieldtype": "Data"},
            {"fieldname": "address", "label": _("Address (English)"), "fieldtype": "Small Text"},
            {"fieldname": "address_ar", "label": _("العنوان"), "fieldtype": "Small Text"},
            {"fieldname": "city", "label": _("City"), "fieldtype": "Data", "reqd": 1},
            {
                "fieldname": "governorate",
                "label": _("Governorate"),
                "fieldtype": "Select",
                "options": "Muscat\nDhofar\nAl Batinah North\nAl Batinah South\nAl Buraimi\nAl Dakhiliyah\nAl Dhahirah\nAl Sharqiyah North\nAl Sharqiyah South\nAl Wusta\nMusandam",
                "reqd": 1,
            },
            {"fieldname": "postal_code", "label": _("Postal Code"), "fieldtype": "Data"},
        ],
        "operational_details": [
            {
                "fieldname": "working_hours_start",
                "label": _("Working Hours Start"),
                "fieldtype": "Time",
            },
            {
                "fieldname": "working_hours_end",
                "label": _("Working Hours End"),
                "fieldtype": "Time",
            },
            {
                "fieldname": "weekend_days",
                "label": _("Weekend Days"),
                "fieldtype": "Select",
                "options": "Friday-Saturday\nSaturday-Sunday\nSunday-Monday",
                "default": "Friday-Saturday",
            },
            {
                "fieldname": "service_capacity_daily",
                "label": _("Daily Service Capacity"),
                "fieldtype": "Int",
            },
            {
                "fieldname": "specialization",
                "label": _("Main Specialization"),
                "fieldtype": "Small Text",
            },
            {"fieldname": "equipment_list", "label": _("Equipment List"), "fieldtype": "Long Text"},
            {
                "fieldname": "certification_level",
                "label": _("Certification Level"),
                "fieldtype": "Select",
                "options": "Basic\nIntermediate\nAdvanced\nProfessional",
            },
        ],
        "financial_info": [
            {"fieldname": "bank_name", "label": _("Bank Name"), "fieldtype": "Data"},
            {"fieldname": "bank_account", "label": _("Bank Account Number"), "fieldtype": "Data"},
            {"fieldname": "iban", "label": _("IBAN"), "fieldtype": "Data"},
            {
                "fieldname": "currency",
                "label": _("Currency"),
                "fieldtype": "Select",
                "options": "OMR\nUSD\nEUR",
                "default": "OMR",
            },
        ],
    }

    return field_configs.get(step_name, [])


@frappe.whitelist()
def rollback_onboarding(progress_id, reason="User cancelled"):
    """Rollback/cancel onboarding process"""
    try:
        progress = frappe.get_doc("Onboarding Progress", progress_id)
        progress.add_comment("Info", f"Onboarding cancelled: {reason}")
        frappe.delete_doc("Onboarding Progress", progress_id)

        return {"success": True, "message": _("Onboarding process cancelled successfully")}
    except Exception as e:
        return {"success": False, "errors": [_("Failed to cancel onboarding: {0}").format(str(e))]}
