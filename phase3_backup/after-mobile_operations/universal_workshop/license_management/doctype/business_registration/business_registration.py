"""
Business Registration DocType Controller
Handles business name binding, owner verification, and government integration
for Universal Workshop ERP license management system.
"""

import hashlib
import json
import re
from datetime import datetime, timedelta

import frappe
from frappe import ValidationError, _
from frappe.model.document import Document
from universal_workshop.license_management.utils.government_api import GovernmentVerificationService
from universal_workshop.license_management.utils.license_manager import LicenseManager


class BusinessRegistration(Document):
    """Business Registration controller for license management"""

    def before_insert(self):
        """Pre-insertion validation and setup"""
        self.validate_required_fields()
        self.validate_business_license_format()
        self.validate_civil_id_format()
        self.validate_arabic_text()
        self.generate_verification_hash()

    def before_save(self):
        """Pre-save validation and processing"""
        self.validate_phone_numbers()
        self.validate_ownership_percentage()
        self.update_verification_status()

    def after_insert(self):
        """Post-insertion processing"""
        self.log_business_registration()
        self.initiate_government_verification()

    def validate_required_fields(self):
        """Validate required fields with Arabic support"""
        required_fields = [
            "business_name_en",
            "business_name_ar",
            "registration_date",
            "business_type",
            "owner_name_en",
            "owner_name_ar",
            "owner_civil_id",
        ]

        for field in required_fields:
            if not self.get(field):
                field_label = self.meta.get_field(field).label
                frappe.throw(_("Field {0} is required").format(field_label))

    def validate_business_license_format(self):
        """Validate Oman business license number format (optional field)"""
        if not self.business_license_number:
            # Business license is now optional
            return

        # Remove any spaces or formatting
        clean_license = re.sub(r"[\s\-]", "", self.business_license_number)
        self.business_license_number = clean_license

        # Oman business license: 7 digits
        if not re.match(r"^\d{7}$", clean_license):
            frappe.throw(_("Business License Number must be 7 digits (Oman format) if provided"))

        # Check for existing license
        existing = frappe.db.exists(
            "Business Registration",
            {"business_license_number": clean_license, "name": ["!=", self.name]},
        )

        if existing:
            frappe.throw(_("Business License Number {0} already exists").format(clean_license))

    def validate_civil_id_format(self):
        """Validate Oman Civil ID format"""
        if not self.owner_civil_id:
            return

        # Oman Civil ID: 8 digits
        if not re.match(r"^\d{8}$", self.owner_civil_id):
            frappe.throw(_("Civil ID must be 8 digits (Oman format)"))

        # Check for existing Civil ID
        existing = frappe.db.exists(
            "Business Registration",
            {"owner_civil_id": self.owner_civil_id, "name": ["!=", self.name]},
        )

        if existing:
            frappe.throw(
                _("Civil ID {0} already registered for another business").format(
                    self.owner_civil_id
                )
            )

    def validate_arabic_text(self):
        """Validate Arabic text fields"""
        arabic_fields = [
            "business_name_ar",
            "owner_name_ar",
            "primary_contact_name_ar",
            "address_ar",
        ]

        for field in arabic_fields:
            text = self.get(field)
            if text and not self.is_arabic_text(text):
                field_label = self.meta.get_field(field).label
                frappe.throw(_("Field {0} must contain Arabic text").format(field_label))

    def is_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return arabic_pattern.search(text) is not None

    def validate_phone_numbers(self):
        """Validate Oman phone number formats"""
        phone_fields = ["phone_number", "owner_phone"]

        for field in phone_fields:
            phone = self.get(field)
            if phone and not self.is_valid_oman_phone(phone):
                field_label = self.meta.get_field(field).label
                frappe.throw(
                    _("Invalid Oman phone number format for {0}. Use +968 XXXXXXXX").format(
                        field_label
                    )
                )

    def is_valid_oman_phone(self, phone):
        """Validate Oman phone number format"""
        # Remove spaces and formatting
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)

        # Check Oman format: +968XXXXXXXX (8 digits after country code)
        return re.match(r"^\+968\d{8}$", clean_phone) is not None

    def validate_ownership_percentage(self):
        """Validate ownership percentage"""
        if (
            self.ownership_percentage and self.ownership_percentage < 0
        ) or self.ownership_percentage > 100:
            frappe.throw(_("Ownership percentage must be between 0 and 100"))

    def generate_verification_hash(self):
        """Generate hash for business verification"""
        hash_data = {
            "business_license": self.business_license_number or "",
            "owner_civil_id": self.owner_civil_id,
            "business_name_en": self.business_name_en,
            "business_name_ar": self.business_name_ar,
            "owner_name_en": self.owner_name_en,
            "owner_name_ar": self.owner_name_ar,
        }

        hash_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
        self.verification_hash = hashlib.sha256(hash_string.encode("utf-8")).hexdigest()

    def update_verification_status(self):
        """Update verification status based on government verification"""
        if self.government_verification_status == "Verified":
            self.verification_status = "Verified"
            if not self.verification_expiry_date:
                # Set verification to expire in 1 year
                self.verification_expiry_date = datetime.now().date() + timedelta(days=365)
        elif self.government_verification_status == "Failed":
            self.verification_status = "Rejected"
        elif self.government_verification_status in ["In Progress"]:
            self.verification_status = "In Progress"

    def log_business_registration(self):
        """Log business registration in audit system"""
        try:
            frappe.get_doc(
                {
                    "doctype": "License Audit Log",
                    "event_type": "Business Registration",
                    "event_description": f"New business registered: {self.business_name_en}",
                    "severity": "Info",
                    "workshop_code": None,  # Not bound yet
                    "business_license": self.business_license_number,
                    "details": json.dumps(
                        {
                            "business_name_en": self.business_name_en,
                            "business_name_ar": self.business_name_ar,
                            "owner_name_en": self.owner_name_en,
                            "business_type": self.business_type,
                            "verification_hash": self.verification_hash,
                        },
                        ensure_ascii=False,
                    ),
                }
            ).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log business registration: {e}")

    def initiate_government_verification(self):
        """Initiate government verification process"""
        try:
            verification_service = GovernmentVerificationService()

            # Start MCI verification
            if self.business_license_number:
                mci_result = verification_service.verify_business_license(
                    self.business_license_number, self.business_name_en, self.business_name_ar
                )

                if mci_result.get("success"):
                    self.mci_registration_number = mci_result.get("mci_number")
                    self.government_verification_status = "In Progress"
                    self.verification_attempts += 1
                    self.last_verification_date = datetime.now()

            # Start civil ID verification
            if self.owner_civil_id:
                civil_result = verification_service.verify_civil_id(
                    self.owner_civil_id, self.owner_name_en, self.owner_name_ar
                )

                if civil_result.get("success"):
                    self.government_verification_status = "Verified"
                    self.verification_status = "Verified"

            self.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Government verification failed: {e}")
            self.government_verification_status = "Failed"
            self.verification_status = "Rejected"
            self.save(ignore_permissions=True)

    @frappe.whitelist()
    def bind_to_workshop(self, workshop_code, license_key_hash, hardware_fingerprint_hash):
        """Bind business registration to workshop license"""
        try:
            # Validate business is verified
            if self.verification_status != "Verified":
                frappe.throw(_("Business must be verified before binding to workshop"))

            # Check if workshop already bound
            existing_binding = next(
                (row for row in self.workshop_codes if row.workshop_code == workshop_code), None
            )

            if existing_binding:
                frappe.throw(_("Workshop {0} already bound to this business").format(workshop_code))

            # Add workshop binding
            self.append(
                "workshop_codes",
                {
                    "workshop_code": workshop_code,
                    "binding_date": datetime.now(),
                    "binding_status": "Active",
                    "license_key_hash": license_key_hash,
                    "hardware_fingerprint_hash": hardware_fingerprint_hash,
                },
            )

            # Update main binding status
            self.binding_status = "Bound"
            self.binding_date = datetime.now()
            self.license_key_hash = license_key_hash
            self.hardware_fingerprint_hash = hardware_fingerprint_hash
            self.last_validation_date = datetime.now()

            self.save(ignore_permissions=True)

            # Log binding event
            self.log_workshop_binding(workshop_code, "Bound")

            return {
                "success": True,
                "message": _("Workshop {0} successfully bound to business").format(workshop_code),
            }

        except Exception as e:
            frappe.log_error(f"Workshop binding failed: {e}")
            return {"success": False, "message": str(e)}

    @frappe.whitelist()
    def unbind_from_workshop(self, workshop_code):
        """Unbind workshop from business registration"""
        try:
            # Find and remove workshop binding
            for i, row in enumerate(self.workshop_codes):
                if row.workshop_code == workshop_code:
                    self.remove(self.workshop_codes[i])
                    break
            else:
                frappe.throw(_("Workshop {0} not found in bindings").format(workshop_code))

            # Update binding status if no workshops remain
            if not self.workshop_codes:
                self.binding_status = "Unbound"
                self.binding_date = None
                self.license_key_hash = None
                self.hardware_fingerprint_hash = None

            self.save(ignore_permissions=True)

            # Log unbinding event
            self.log_workshop_binding(workshop_code, "Unbound")

            return {
                "success": True,
                "message": _("Workshop {0} successfully unbound from business").format(
                    workshop_code
                ),
            }

        except Exception as e:
            frappe.log_error(f"Workshop unbinding failed: {e}")
            return {"success": False, "message": str(e)}

    def log_workshop_binding(self, workshop_code, action):
        """Log workshop binding/unbinding events"""
        try:
            frappe.get_doc(
                {
                    "doctype": "License Audit Log",
                    "event_type": "Workshop Binding",
                    "event_description": f"Workshop {workshop_code} {action.lower()} to business {self.business_name_en}",
                    "severity": "Info",
                    "workshop_code": workshop_code,
                    "business_license": self.business_license_number,
                    "details": json.dumps(
                        {
                            "action": action,
                            "business_name_en": self.business_name_en,
                            "business_name_ar": self.business_name_ar,
                            "binding_date": str(datetime.now()),
                            "verification_hash": self.verification_hash,
                        },
                        ensure_ascii=False,
                    ),
                }
            ).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log workshop binding: {e}")

    @frappe.whitelist()
    def validate_business_integrity(self):
        """Validate business registration integrity"""
        try:
            results = {"valid": True, "errors": [], "warnings": []}

            # Check verification hash integrity
            current_hash = self.generate_verification_hash()
            if current_hash != self.verification_hash:
                results["valid"] = False
                results["errors"].append(_("Business data integrity compromised"))

            # Check verification expiry
            if (
                self.verification_expiry_date
                and self.verification_expiry_date < datetime.now().date()
            ):
                results["valid"] = False
                results["errors"].append(_("Business verification expired"))

            # Check government verification status
            if self.government_verification_status not in ["Verified"]:
                results["warnings"].append(_("Government verification not complete"))

            # Validate workshop bindings
            for binding in self.workshop_codes:
                if binding.binding_status != "Active":
                    results["warnings"].append(
                        _("Workshop {0} binding inactive").format(binding.workshop_code)
                    )

            return results

        except Exception as e:
            frappe.log_error(f"Business integrity validation failed: {e}")
            return {"valid": False, "errors": [str(e)], "warnings": []}

    @frappe.whitelist()
    def refresh_government_verification(self):
        """Refresh government verification status"""
        try:
            if self.verification_attempts >= 5:
                frappe.throw(_("Maximum verification attempts exceeded"))

            self.initiate_government_verification()

            return {
                "success": True,
                "message": _("Government verification refresh initiated"),
                "status": self.government_verification_status,
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


# Helper functions for Business Registration management


@frappe.whitelist()
def get_business_by_license(business_license_number):
    """Get business registration by license number"""
    try:
        business = frappe.get_doc(
            "Business Registration", {"business_license_number": business_license_number}
        )

        if business:
            return {"success": True, "business": business.as_dict()}
        else:
            return {"success": False, "message": _("Business license not found")}

    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def search_businesses(query, filters=None):
    """Search businesses with Arabic support"""
    try:
        conditions = []
        values = {}

        if query:
            conditions.append(
                """
                (business_name_en LIKE %(query)s OR
                 business_name_ar LIKE %(query)s OR
                 business_license_number LIKE %(query)s OR
                 owner_name_en LIKE %(query)s OR
                 owner_name_ar LIKE %(query)s)
            """
            )
            values["query"] = f"%{query}%"

        if filters:
            for field, value in filters.items():
                conditions.append(f"{field} = %({field})s")
                values[field] = value

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT name, business_name_en, business_name_ar,
                   business_license_number, verification_status,
                   binding_status, owner_name_en, owner_name_ar
            FROM `tabBusiness Registration`
            WHERE {where_clause}
            ORDER BY business_name_en
            LIMIT 50
        """

        results = frappe.db.sql(sql, values, as_dict=True)

        return {"success": True, "businesses": results}

    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def validate_license_binding(workshop_code, business_license_number):
    """Validate workshop-business binding"""
    try:
        business = frappe.get_doc(
            "Business Registration", {"business_license_number": business_license_number}
        )

        if not business:
            return {"valid": False, "message": _("Business license not found")}

        # Check if workshop is bound
        workshop_bound = any(
            row.workshop_code == workshop_code
            for row in business.workshop_codes
            if row.binding_status == "Active"
        )

        if not workshop_bound:
            return {"valid": False, "message": _("Workshop not bound to this business")}

        # Validate business integrity
        integrity_check = business.validate_business_integrity()

        return {
            "valid": integrity_check["valid"] and workshop_bound,
            "business_name": business.business_name_en,
            "business_name_ar": business.business_name_ar,
            "verification_status": business.verification_status,
            "integrity_check": integrity_check,
        }

    except Exception as e:
        return {"valid": False, "message": str(e)}
