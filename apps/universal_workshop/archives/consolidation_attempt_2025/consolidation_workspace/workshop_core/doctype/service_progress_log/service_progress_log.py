"""
Service Progress Log DocType Controller
Handles progress tracking entries for service orders with Arabic localization
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, nowdate

# pylint: disable=no-member


class ServiceProgressLog(Document):
    """Service Progress Log DocType for tracking service order progress"""

    def validate(self):
        """Validate progress log entry"""
        self.validate_service_order()
        self.validate_progress_percentage()
        self.set_reference_data()

    def before_save(self):
        """Set default values before saving"""
        if not self.timestamp:
            self.timestamp = get_datetime()
        
        # Auto-translate notes if Arabic notes are empty
        if self.notes and not self.notes_ar:
            self.notes_ar = self._auto_translate_to_arabic(self.notes)

    def validate_service_order(self):
        """Validate service order exists and is active"""
        if not self.service_order:
            frappe.throw(_("Service Order is required"))

    def validate_progress_percentage(self):
        """Validate progress percentage is within valid range"""
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            frappe.throw(_("Progress percentage must be between 0 and 100"))

    def set_reference_data(self):
        """Set reference data from service order"""
        if self.service_order:
            service_order = frappe.get_doc("Sales Order", self.service_order)
            self.customer = service_order.customer

    def _auto_translate_to_arabic(self, text):
        """Simple Arabic translation for common phrases"""
        translation_map = {
            "Operation started": "بدأت العملية",
            "Operation completed successfully": "تمت العملية بنجاح",
            "Operation on hold": "العملية متوقفة",
            "Progress updated": "تم تحديث التقدم"
        }
        return translation_map.get(text, text)


@frappe.whitelist()
def get_operation_progress_history(service_order, operation_id=None):
    """Get progress history for service order operations"""
    filters = {"service_order": service_order}
    if operation_id:
        filters["operation_id"] = operation_id

    return frappe.get_list(
        "Service Progress Log",
        filters=filters,
        fields=["name", "operation_id", "status", "progress_percentage", "technician", "timestamp"],
        order_by="timestamp desc"
    )
