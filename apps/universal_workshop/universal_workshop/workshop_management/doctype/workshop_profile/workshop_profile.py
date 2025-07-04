# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
import os
from datetime import datetime
from PIL import Image

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path


class WorkshopProfile(Document):
    def autoname(self):
        """Auto-generate workshop code: WS-YYYY-0001"""
        self.name = self.generate_workshop_code()

    def validate(self):
        """Validate workshop data according to Oman regulations"""
        self.validate_business_license()
        self.validate_arabic_name()
        self.validate_oman_phone_numbers()
        self.validate_vat_number()
        self.validate_working_hours()
        self.validate_branding_fields()

    def validate_branding_fields(self):
        """Validate branding and logo fields"""
        if self.workshop_logo:
            self.validate_logo_file_size_and_format()

        if self.primary_color:
            self.validate_color_format(self.primary_color, "Primary Color")

        if self.secondary_color:
            self.validate_color_format(self.secondary_color, "Secondary Color")

    def validate_logo_file_size_and_format(self):
        """Validate uploaded logo file"""
        if not self.workshop_logo:
            return

        try:
            # Get file path
            file_path = get_file_path(self.workshop_logo)

            if not file_path or not os.path.exists(file_path):
                frappe.throw(_("Logo file not found"))

            # Check file size (max 2MB)
            file_size = os.path.getsize(file_path)
            max_size = 2 * 1024 * 1024  # 2MB in bytes

            if file_size > max_size:
                frappe.throw(_("Logo file size must be less than 2MB"))

            # Check file format using PIL
            try:
                with Image.open(file_path) as img:
                    # Allowed formats
                    allowed_formats = ["PNG", "JPEG", "JPG", "SVG"]
                    if img.format not in allowed_formats and not file_path.lower().endswith(".svg"):
                        frappe.throw(_("Logo must be in PNG, JPG, or SVG format"))

                    # Check dimensions (reasonable limits)
                    if img.size[0] > 2000 or img.size[1] > 2000:
                        frappe.throw(_("Logo dimensions should not exceed 2000x2000 pixels"))

            except Exception as e:
                # Handle SVG files (PIL can't read them)
                if not file_path.lower().endswith(".svg"):
                    frappe.throw(_("Invalid image file format"))

        except Exception as e:
            frappe.log_error(f"Logo validation error: {str(e)}")
            frappe.throw(_("Error validating logo file: {0}").format(str(e)))

    def validate_color_format(self, color_value, field_name):
        """Validate hex color format"""
        if color_value and not re.match(r"^#[0-9A-Fa-f]{6}$", color_value):
            frappe.throw(_("{0} must be a valid hex color (e.g., #1f4e79)").format(field_name))

    def validate_business_license(self):
        """Validate Oman business license format (7 digits)"""
        if self.business_license and not re.match(r"^\d{7}$", self.business_license):
            frappe.throw(_("Business License must be exactly 7 digits (Oman format)"))

    def validate_arabic_name(self):
        """Ensure Arabic workshop name is provided and contains Arabic characters"""
        if not self.workshop_name_ar:
            frappe.throw(_("Arabic workshop name is required"))

        # Check if Arabic name contains actual Arabic characters
        if not re.search(r"[\u0600-\u06FF]", self.workshop_name_ar):
            frappe.throw(_("Arabic name must contain Arabic characters"))

    def validate_oman_phone_numbers(self):
        """Validate Oman phone number formats (+968 XXXXXXXX)"""
        for field in ["phone_number", "mobile_number"]:
            phone = getattr(self, field, None)
            if phone:
                # Remove spaces and formatting
                clean_phone = re.sub(r"\s+", "", phone)

                # Check Oman phone format: +968 followed by 8 digits
                if not re.match(r"^\+968\d{8}$", clean_phone):
                    frappe.throw(
                        _("{0} must be in Oman format: +968 XXXXXXXX").format(
                            _(field.replace("_", " ").title())
                        )
                    )

    def validate_vat_number(self):
        """Validate Oman VAT registration number format"""
        if self.vat_number:
            # Oman VAT format: OM followed by 15 digits
            if not re.match(r"^OM\d{15}$", self.vat_number):
                frappe.throw(_("VAT number must be in Oman format: OMxxxxxxxxxxxxxxx"))

    def validate_working_hours(self):
        """Validate working hours logic"""
        if self.working_hours_start and self.working_hours_end:
            # Convert time strings to datetime objects for comparison
            start_time = datetime.strptime(str(self.working_hours_start), "%H:%M:%S").time()
            end_time = datetime.strptime(str(self.working_hours_end), "%H:%M:%S").time()

            if start_time >= end_time:
                frappe.throw(_("Working hours end time must be after start time"))

    def generate_workshop_code(self):
        """Generate unique workshop code: WS-YYYY-0001"""
        year = datetime.now().year

        # Get the last workshop number for current year
        last_workshop = frappe.db.sql(
            """
            SELECT workshop_code FROM `tabWorkshop Profile`
            WHERE workshop_code LIKE 'WS-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(
                year
            )
        )

        if last_workshop and last_workshop[0][0]:
            # Extract number from last code and increment
            last_num = int(last_workshop[0][0].split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"WS-{year}-{new_num:04d}"

    def get_branding_settings(self):
        """Get workshop branding settings for UI"""
        return {
            "logo": self.workshop_logo,
            "primary_color": self.primary_color or "#1f4e79",
            "secondary_color": self.secondary_color or "#e8f4fd",
            "dark_mode": self.dark_mode_enabled,
            "theme": self.theme_preference or "Light",
        }

    def get_arabic_display_name(self):
        """Get Arabic display name for UI"""
        return self.workshop_name_ar if self.workshop_name_ar else self.workshop_name

    def get_full_address(self, language="en"):
        """Get formatted address in specified language"""
        if language == "ar" and self.address_ar:
            address_parts = [self.address_ar, self.city, self.governorate]
        else:
            address_parts = [self.address, self.city, self.governorate]

        # Filter out empty parts and join
        return ", ".join([part for part in address_parts if part])

    def after_insert(self):
        """Actions to perform after inserting new Workshop Profile"""
        try:
            # Initialize system settings for the new workshop
            from universal_workshop.setup.system_initialization import initialize_system_settings
            
            init_result = initialize_system_settings(self.name)
            
            if init_result.get("status") == "success":
                # Mark setup as complete when first workshop profile is created
                frappe.db.set_default("setup_complete", "1")
                frappe.db.commit()

                # Log successful setup completion
                frappe.logger().info(
                    f"Workshop Profile {self.name} created successfully. Setup marked as complete."
                )

                # Show success message
                frappe.msgprint(
                    _("Workshop setup completed successfully! Welcome to Universal Workshop ERP."),
                    title=_("Setup Complete"),
                    indicator="green",
                )
            else:
                # Log warning if system initialization failed
                frappe.logger().warning(
                    f"Workshop Profile {self.name} created but system initialization failed: {init_result.get('message')}"
                )

        except Exception as e:
            frappe.log_error(f"Error in Workshop Profile after_insert: {str(e)}")
            # Don't fail the workshop profile creation if initialization fails
            frappe.msgprint(
                _("Workshop profile created but some system initialization steps failed. Please check System Settings."),
                title=_("Partial Setup"),
                indicator="orange",
            )

    def is_active(self):
        """Check if workshop is currently active"""
        return self.status == "Active"

    def can_provide_service(self):
        """Check if workshop can currently provide service"""
        return (
            self.status == "Active"
            and self.service_capacity_daily
            and self.service_capacity_daily > 0
        )


@frappe.whitelist()
def validate_logo_file(file_url):
    """Validate logo file via API call"""
    try:
        if not file_url:
            return {"valid": False, "error": _("No file provided")}

        # Get file path
        file_path = get_file_path(file_url)

        if not file_path or not os.path.exists(file_path):
            return {"valid": False, "error": _("File not found")}

        # Check file size (max 2MB)
        file_size = os.path.getsize(file_path)
        max_size = 2 * 1024 * 1024  # 2MB in bytes

        if file_size > max_size:
            return {"valid": False, "error": _("File size must be less than 2MB")}

        # Check file format
        try:
            with Image.open(file_path) as img:
                allowed_formats = ["PNG", "JPEG", "JPG"]
                if img.format not in allowed_formats:
                    return {"valid": False, "error": _("File must be PNG, JPG, or JPEG format")}

                # Check dimensions
                if img.size[0] > 2000 or img.size[1] > 2000:
                    return {
                        "valid": False,
                        "error": _("Image dimensions should not exceed 2000x2000 pixels"),
                    }

        except Exception:
            # Check if it's SVG
            if not file_path.lower().endswith(".svg"):
                return {"valid": False, "error": _("Invalid image format")}

        return {"valid": True, "message": _("Logo file is valid")}

    except Exception as e:
        frappe.log_error(f"Logo validation API error: {str(e)}")
        return {"valid": False, "error": _("Error validating file")}


@frappe.whitelist()
def get_workshop_branding(workshop_name=None):
    """Get workshop branding settings"""
    if not workshop_name:
        # Get the first active workshop
        workshop = frappe.get_list(
            "Workshop Profile",
            filters={"status": "Active"},
            fields=[
                "name",
                "workshop_logo",
                "primary_color",
                "secondary_color",
                "dark_mode_enabled",
                "theme_preference",
            ],
            limit=1,
        )

        if workshop:
            workshop_data = workshop[0]
        else:
            # Return default branding
            return {
                "logo": None,
                "primary_color": "#1f4e79",
                "secondary_color": "#e8f4fd",
                "dark_mode": False,
                "theme": "Light",
            }
    else:
        workshop_data = frappe.get_doc("Workshop Profile", workshop_name)

    return {
        "logo": workshop_data.get("workshop_logo"),
        "primary_color": workshop_data.get("primary_color") or "#1f4e79",
        "secondary_color": workshop_data.get("secondary_color") or "#e8f4fd",
        "dark_mode": workshop_data.get("dark_mode_enabled") or False,
        "theme": workshop_data.get("theme_preference") or "Light",
    }


@frappe.whitelist()
def get_workshop_by_license(business_license):
    """Get workshop by business license number"""
    return frappe.get_list(
        "Workshop Profile",
        filters={"business_license": business_license},
        fields=["name", "workshop_name", "workshop_name_ar", "status"],
    )


@frappe.whitelist()
def search_workshops(txt, language="en"):
    """Search workshops by name (supports Arabic and English)"""
    conditions = []

    if language == "ar":
        conditions.append("workshop_name_ar LIKE %(txt)s")
        conditions.append("owner_name_ar LIKE %(txt)s")
    else:
        conditions.append("workshop_name LIKE %(txt)s")
        conditions.append("owner_name LIKE %(txt)s")

    # Also search by workshop code and business license
    conditions.extend(["workshop_code LIKE %(txt)s", "business_license LIKE %(txt)s"])

    return frappe.db.sql(
        f"""
        SELECT name, workshop_code, workshop_name, workshop_name_ar,
               status, governorate, workshop_type
        FROM `tabWorkshop Profile`
        WHERE ({" OR ".join(conditions)}) AND status = 'Active'
        ORDER BY workshop_name
        LIMIT 20
    """,
        {"txt": f"%{txt}%"},
        as_dict=True,
    )
