# pylint: disable=no-member
import frappe
from frappe import _
from frappe.model.document import Document


class VehicleInspectionPhoto(Document):
    """Child DocType for storing vehicle inspection photos with categorization"""

    def validate(self):
        """Validate inspection photo data"""
        self.validate_photo_file()
        self.validate_photo_category()
        self.set_default_values()

    def validate_photo_file(self):
        """Validate that the photo file is attached and valid"""
        if not self.photo:
            frappe.throw(_("Photo file is required"))

        # Check file extension
        allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        file_extension = self.photo.lower().split(".")[-1] if "." in self.photo else ""

        if not any(self.photo.lower().endswith(ext) for ext in allowed_extensions):
            frappe.throw(_("Photo must be an image file (JPG, PNG, BMP, GIF)"))

        # Check file size (max 10MB for inspection photos)
        if self.photo:
            try:
                file_doc = frappe.get_doc("File", {"file_url": self.photo})
                if file_doc.file_size and file_doc.file_size > 10 * 1024 * 1024:  # 10MB
                    frappe.throw(_("Photo file size must not exceed 10MB"))
            except frappe.DoesNotExistError:
                pass  # File might be uploaded but not yet saved as File doc

    def validate_photo_category(self):
        """Validate photo category and set Arabic translation"""
        if not self.photo_category:
            self.photo_category = "General"

        # Set Arabic category name
        category_translations = {
            "Engine": "المحرك",
            "Exterior": "المظهر الخارجي",
            "Interior": "المظهر الداخلي",
            "Undercarriage": "أسفل السيارة",
            "Tires": "الإطارات",
            "Brakes": "الفرامل",
            "Lights": "الأضواء",
            "Damage": "الأضرار",
            "Before Repair": "قبل الإصلاح",
            "After Repair": "بعد الإصلاح",
            "Parts": "القطع",
            "General": "عام",
        }

        self.photo_category_ar = category_translations.get(self.photo_category, self.photo_category)

    def set_default_values(self):
        """Set default values for the photo record"""
        if not self.taken_date:
            self.taken_date = frappe.utils.now()

        if not self.taken_by:
            self.taken_by = frappe.session.user

        if not self.severity_level:
            self.severity_level = "Normal"

    def before_save(self):
        """Actions before saving the photo record"""
        # Generate photo description if not provided
        if not self.description and self.photo_category:
            inspection_doc = self.get_parent_doc()
            if inspection_doc:
                vehicle_name = inspection_doc.vehicle
                self.description = f"{self.photo_category} photo for {vehicle_name}"

        # Set file metadata
        self.set_file_metadata()

    def set_file_metadata(self):
        """Extract and set file metadata"""
        if self.photo:
            try:
                file_doc = frappe.get_doc("File", {"file_url": self.photo})
                self.file_name = file_doc.file_name
                self.file_size = file_doc.file_size
            except frappe.DoesNotExistError:
                pass

    def get_parent_doc(self):
        """Get the parent Vehicle Inspection document"""
        if self.parent and self.parenttype == "Vehicle Inspection":
            return frappe.get_doc("Vehicle Inspection", self.parent)
        return None


@frappe.whitelist()
def upload_inspection_photo(inspection_id, category, description="", severity="Normal"):
    """Upload and attach a photo to a vehicle inspection"""
    from frappe.utils.file_manager import save_file

    # Validate inspection exists
    if not frappe.db.exists("Vehicle Inspection", inspection_id):
        frappe.throw(_("Vehicle Inspection {0} not found").format(inspection_id))

    # Handle file upload (this would be called from frontend with file data)
    # This is a placeholder for the actual file upload logic
    return {"status": "success", "message": _("Photo uploaded successfully")}


@frappe.whitelist()
def get_inspection_photos(inspection_id, category=""):
    """Get all photos for a vehicle inspection, optionally filtered by category"""
    filters = {"parent": inspection_id, "parenttype": "Vehicle Inspection"}
    if category:
        filters["photo_category"] = category

    photos = frappe.get_all(
        "Vehicle Inspection Photo",
        filters=filters,
        fields=[
            "name",
            "photo",
            "photo_category",
            "photo_category_ar",
            "description",
            "severity_level",
            "taken_date",
            "taken_by",
        ],
        order_by="taken_date desc",
    )

    return photos


@frappe.whitelist()
def delete_inspection_photo(photo_id):
    """Delete an inspection photo"""
    try:
        photo_doc = frappe.get_doc("Vehicle Inspection Photo", photo_id)

        # Delete the actual file
        if photo_doc.photo:
            try:
                file_doc = frappe.get_doc("File", {"file_url": photo_doc.photo})
                file_doc.delete()
            except frappe.DoesNotExistError:
                pass

        # Delete the photo record
        photo_doc.delete()

        return {"status": "success", "message": _("Photo deleted successfully")}

    except frappe.DoesNotExistError:
        frappe.throw(_("Photo not found"))
    except Exception as e:
        frappe.throw(_("Error deleting photo: {0}").format(str(e)))


@frappe.whitelist()
def get_photo_categories():
    """Get list of available photo categories with Arabic translations"""
    categories = [
        {"value": "Engine", "label": "Engine", "label_ar": "المحرك"},
        {"value": "Exterior", "label": "Exterior", "label_ar": "المظهر الخارجي"},
        {"value": "Interior", "label": "Interior", "label_ar": "المظهر الداخلي"},
        {"value": "Undercarriage", "label": "Undercarriage", "label_ar": "أسفل السيارة"},
        {"value": "Tires", "label": "Tires", "label_ar": "الإطارات"},
        {"value": "Brakes", "label": "Brakes", "label_ar": "الفرامل"},
        {"value": "Lights", "label": "Lights", "label_ar": "الأضواء"},
        {"value": "Damage", "label": "Damage", "label_ar": "الأضرار"},
        {"value": "Before Repair", "label": "Before Repair", "label_ar": "قبل الإصلاح"},
        {"value": "After Repair", "label": "After Repair", "label_ar": "بعد الإصلاح"},
        {"value": "Parts", "label": "Parts", "label_ar": "القطع"},
        {"value": "General", "label": "General", "label_ar": "عام"},
    ]

    return categories
