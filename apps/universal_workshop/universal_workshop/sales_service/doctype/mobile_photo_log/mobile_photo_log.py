import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, get_datetime, file_manager
import json
import os
from PIL import Image


class MobilePhotoLog(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate mobile photo log"""
        self.validate_service_order()
        self.validate_file_url()
        self.set_default_values()
        self.process_image_info()

    def validate_service_order(self):
        """Validate service order exists and user has access"""
        if not self.service_order:
            frappe.throw(_("Service Order is required"))

        # Check if service order exists
        if not frappe.db.exists("Sales Order", self.service_order):
            frappe.throw(_("Service Order {0} does not exist").format(self.service_order))

        # Check user permissions
        if not self.uploaded_by:
            self.uploaded_by = frappe.session.user

        # Validate technician access
        service_order = frappe.get_doc("Sales Order", self.service_order)
        user_roles = frappe.get_roles(self.uploaded_by)

        if (
            "Workshop Manager" not in user_roles
            and "Workshop Technician" not in user_roles
            and service_order.get("technician") != self.uploaded_by
        ):
            frappe.throw(
                _("User {0} does not have access to this service order").format(self.uploaded_by)
            )

    def validate_file_url(self):
        """Validate file URL and accessibility"""
        if not self.file_url:
            frappe.throw(_("File URL is required"))

        # Check if file exists
        try:
            file_doc = frappe.get_doc("File", {"file_url": self.file_url})
            if not file_doc:
                frappe.throw(_("File not found: {0}").format(self.file_url))

            # Update file size if not set
            if not self.file_size and file_doc.file_size:
                self.file_size = file_doc.file_size

        except Exception as e:
            frappe.log_error(f"File validation error: {str(e)}")
            frappe.throw(_("Invalid file URL: {0}").format(self.file_url))

    def set_default_values(self):
        """Set default values for new documents"""
        if not self.upload_timestamp:
            self.upload_timestamp = get_datetime()

        if not self.photo_type:
            self.photo_type = "general"

        if not self.uploaded_by:
            self.uploaded_by = frappe.session.user

    def process_image_info(self):
        """Process and extract image information"""
        if not self.file_url or self.image_dimensions:
            return

        try:
            # Get file path from URL
            file_path = frappe.get_site_path() + self.file_url

            if os.path.exists(file_path):
                # Open image and get dimensions
                with Image.open(file_path) as img:
                    width, height = img.size
                    self.image_dimensions = f"{width}x{height}"

                    # Update file size if not set
                    if not self.file_size:
                        self.file_size = os.path.getsize(file_path)

        except Exception as e:
            frappe.log_error(f"Image processing error: {str(e)}")
            # Don't throw error, just log it

    def before_save(self):
        """Actions before saving the document"""
        # Auto-translate description if Arabic not provided
        if self.description and not self.description_ar:
            self.description_ar = self._translate_to_arabic(self.description)

    def on_update(self):
        """Actions after updating the document"""
        # Send real-time notification
        self.publish_photo_update()

        # Update service order with photo count
        self.update_service_order_photo_count()

    def publish_photo_update(self):
        """Publish real-time photo update"""
        try:
            frappe.publish_realtime(
                "mobile_photo_uploaded",
                {
                    "photo_id": self.name,
                    "service_order": self.service_order,
                    "photo_type": self.photo_type,
                    "uploaded_by": self.uploaded_by,
                    "file_url": self.file_url,
                    "description": self.description,
                    "timestamp": self.upload_timestamp,
                },
                doctype="Mobile Photo Log",
                docname=self.name,
            )
        except Exception as e:
            frappe.log_error(f"Failed to publish photo update: {str(e)}")

    def update_service_order_photo_count(self):
        """Update photo count in service order"""
        try:
            photo_count = frappe.db.count("Mobile Photo Log", {"service_order": self.service_order})

            frappe.db.set_value(
                "Sales Order", self.service_order, "mobile_photo_count", photo_count
            )

        except Exception as e:
            frappe.log_error(f"Failed to update photo count: {str(e)}")

    def approve_photo(self, approval_notes=""):
        """Approve the uploaded photo"""
        self.is_processed = True
        self.approved_by = frappe.session.user
        self.approval_date = nowdate()
        self.processing_notes = approval_notes
        self.save()

        # Send notification
        frappe.publish_realtime(
            "photo_approved",
            {
                "photo_id": self.name,
                "service_order": self.service_order,
                "approved_by": self.approved_by,
            },
        )

        return {"status": "success", "message": _("Photo approved successfully")}

    def reject_photo(self, rejection_reason=""):
        """Reject the uploaded photo"""
        self.is_processed = True
        self.processing_notes = f"REJECTED: {rejection_reason}"
        self.save()

        # Send notification
        frappe.publish_realtime(
            "photo_rejected",
            {
                "photo_id": self.name,
                "service_order": self.service_order,
                "rejection_reason": rejection_reason,
            },
        )

        return {"status": "success", "message": _("Photo rejected successfully")}

    def get_photo_metadata(self):
        """Get comprehensive photo metadata"""
        metadata = {
            "photo_id": self.name,
            "service_order": self.service_order,
            "uploaded_by": self.uploaded_by,
            "upload_timestamp": self.upload_timestamp,
            "photo_type": self.photo_type,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "image_dimensions": self.image_dimensions,
            "description": self.description,
            "description_ar": self.description_ar,
            "is_processed": self.is_processed,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date,
        }

        # Add device info if available
        if self.device_info:
            try:
                metadata["device_info"] = json.loads(self.device_info)
            except:
                metadata["device_info"] = self.device_info

        # Add location data if available
        if self.location_data:
            try:
                metadata["location_data"] = json.loads(self.location_data)
            except:
                metadata["location_data"] = self.location_data

        return metadata

    def _translate_to_arabic(self, text):
        """Simple Arabic translation for common terms"""
        if not text:
            return ""

        translation_map = {
            "Before service": "قبل الخدمة",
            "After service": "بعد الخدمة",
            "Parts identification": "تحديد القطع",
            "Issue documentation": "توثيق المشكلة",
            "Quality check": "فحص الجودة",
            "General": "عام",
            "Engine compartment": "مقصورة المحرك",
            "Interior view": "المنظر الداخلي",
            "Exterior damage": "الضرر الخارجي",
            "Part replacement": "استبدال القطعة",
            "Work completed": "العمل مكتمل",
            "Issue found": "مشكلة موجودة",
            "Repair needed": "إصلاح مطلوب",
            "Good condition": "حالة جيدة",
        }

        # Simple word replacement
        result = text
        for english, arabic in translation_map.items():
            result = result.replace(english, arabic)

        return result


# Document Event Hooks
def on_doctype_update():
    """Called when the DocType is updated"""
    frappe.db.add_index("Mobile Photo Log", ["service_order", "upload_timestamp"])
    frappe.db.add_index("Mobile Photo Log", ["uploaded_by", "photo_type"])
    frappe.db.add_index("Mobile Photo Log", ["is_processed", "approval_date"])


def validate_mobile_photo_permissions(doc, method):
    """Validate mobile photo upload permissions"""
    if doc.doctype != "Mobile Photo Log":
        return

    user_roles = frappe.get_roles(frappe.session.user)

    # Check if user has permission to upload photos
    if not any(
        role in user_roles for role in ["Workshop Manager", "Workshop Technician", "System Manager"]
    ):
        frappe.throw(_("You do not have permission to upload photos"))

    # Check service order access
    if doc.service_order:
        service_order = frappe.get_doc("Sales Order", doc.service_order)

        # Technicians can only upload photos for their assigned orders
        if (
            "Workshop Technician" in user_roles
            and "Workshop Manager" not in user_roles
            and service_order.get("technician") != frappe.session.user
        ):
            frappe.throw(_("You can only upload photos for your assigned service orders"))


def cleanup_old_photos():
    """Cleanup old unprocessed photos (called via scheduled job)"""
    from frappe.utils import add_days

    # Delete photos older than 30 days that are not approved
    cutoff_date = add_days(nowdate(), -30)

    old_photos = frappe.get_list(
        "Mobile Photo Log",
        filters={"upload_timestamp": ["<", cutoff_date], "is_processed": 0},
        fields=["name", "file_url"],
    )

    for photo in old_photos:
        try:
            # Delete the file
            if photo.file_url:
                file_doc = frappe.get_doc("File", {"file_url": photo.file_url})
                if file_doc:
                    file_doc.delete()

            # Delete the photo log
            frappe.delete_doc("Mobile Photo Log", photo.name)

        except Exception as e:
            frappe.log_error(f"Failed to cleanup photo {photo.name}: {str(e)}")

    if old_photos:
        frappe.log_error(f"Cleaned up {len(old_photos)} old mobile photos")


def get_photo_statistics(service_order=None):
    """Get photo upload statistics"""
    filters = {}
    if service_order:
        filters["service_order"] = service_order

    total_photos = frappe.db.count("Mobile Photo Log", filters)

    # Photos by type
    photo_types = frappe.db.sql(
        """
        SELECT photo_type, COUNT(*) as count
        FROM `tabMobile Photo Log`
        WHERE service_order = %s OR %s IS NULL
        GROUP BY photo_type
        ORDER BY count DESC
    """,
        [service_order, service_order],
        as_dict=True,
    )

    # Photos by status
    processed_photos = frappe.db.count("Mobile Photo Log", dict(filters, is_processed=1))

    approved_photos = frappe.db.count(
        "Mobile Photo Log", dict(filters, is_processed=1, approved_by=["!=", ""])
    )

    return {
        "total_photos": total_photos,
        "processed_photos": processed_photos,
        "approved_photos": approved_photos,
        "pending_photos": total_photos - processed_photos,
        "photo_types": photo_types,
    }
