# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member,access-member-before-definition
# Frappe framework dynamically adds DocType fields to Document class

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class QualityControlPhoto(Document):
    def validate(self):
        """Validate quality control photo data"""
        self.validate_arabic_title()
        self.validate_photo_file()
        self.set_capture_details()

    def validate_arabic_title(self):
        """Ensure Arabic title is provided"""
        if not self.photo_title_ar:
            # Auto-translate common photo titles
            translations = {
                "Before Service": "قبل الخدمة",
                "During Service": "أثناء الخدمة",
                "After Service": "بعد الخدمة",
                "Defect Documentation": "توثيق العيوب",
                "Completion Evidence": "دليل الإكمال",
                "Customer Handover": "تسليم العميل",
            }

            if self.photo_title in translations:
                self.photo_title_ar = translations[self.photo_title]
            else:
                frappe.throw(_("Arabic photo title is required"))

    def validate_photo_file(self):
        """Validate photo file attachment"""
        if not self.photo_file:
            frappe.throw(_("Photo file is required"))

        # Check file extension
        if self.photo_file:
            allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
            file_ext = self.photo_file.lower().split(".")[-1]
            if f".{file_ext}" not in allowed_extensions:
                frappe.throw(_("Only JPG, PNG, and WebP images are allowed"))

    def set_capture_details(self):
        """Set default capture details"""
        if not self.captured_by:
            self.captured_by = frappe.session.user

        if not self.captured_date:
            self.captured_date = now_datetime()

    def before_save(self):
        """Set device info and GPS if available"""
        # Set device info from request headers
        if frappe.request and not self.device_info:
            user_agent = frappe.request.headers.get("User-Agent", "")
            self.device_info = user_agent[:200]  # Limit to 200 chars

    @staticmethod
    def get_photos_by_type(checkpoint_id, photo_type=None):
        """Get photos for a checkpoint, optionally filtered by type"""
        filters = {"parent": checkpoint_id}
        if photo_type:
            filters["photo_type"] = photo_type

        return frappe.get_all(
            "Quality Control Photo",
            filters=filters,
            fields=[
                "photo_title",
                "photo_title_ar",
                "photo_type",
                "photo_file",
                "captured_date",
                "captured_by",
            ],
            order_by="captured_date desc",
        )

    @staticmethod
    def add_photo_from_mobile(checkpoint_id, photo_data):
        """Add photo from mobile app with GPS and device info"""
        photo = frappe.new_doc("Quality Control Photo")
        photo.parent = checkpoint_id
        photo.parenttype = "Quality Control Checkpoint"
        photo.parentfield = "photos"

        photo.photo_title = photo_data.get("title", "Mobile Photo")
        photo.photo_type = photo_data.get("type", "During Service")
        photo.photo_file = photo_data.get("file_url")
        photo.photo_description = photo_data.get("description", "")
        photo.gps_location = photo_data.get("gps_location", "")
        photo.device_info = photo_data.get("device_info", "")

        photo.insert()
        return photo.name
