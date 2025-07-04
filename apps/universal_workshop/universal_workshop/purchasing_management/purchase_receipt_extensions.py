"""
Purchase Receipt Extensions for Quality Inspection Integration
Universal Workshop ERP - Purchasing Management
"""

import frappe
from frappe import _
from frappe.utils import flt, cint


def setup_purchase_receipt_custom_fields():
    """Setup custom fields for Purchase Receipt integration with Quality Inspection"""

    # Custom fields for Purchase Receipt DocType
    purchase_receipt_fields = [
        {
            "dt": "Purchase Receipt",
            "properties": [
                {
                    "fieldname": "quality_inspection_required",
                    "fieldtype": "Check",
                    "label": "Quality Inspection Required",
                    "insert_after": "status",
                    "default": 0,
                    "description": "Check if any items in this receipt require quality inspection",
                },
                {
                    "fieldname": "quality_inspection_status",
                    "fieldtype": "Select",
                    "label": "Quality Inspection Status",
                    "options": "\nPending\nIn Progress\nCompleted\nFailed\nNot Required",
                    "insert_after": "quality_inspection_required",
                    "default": "Not Required",
                    "read_only": 1,
                },
                {
                    "fieldname": "quality_inspection_status_ar",
                    "fieldtype": "Data",
                    "label": "حالة فحص الجودة",
                    "insert_after": "quality_inspection_status",
                    "read_only": 1,
                    "translatable": 1,
                },
                {
                    "fieldname": "total_inspections_pending",
                    "fieldtype": "Int",
                    "label": "Total Inspections Pending",
                    "insert_after": "quality_inspection_status_ar",
                    "default": 0,
                    "read_only": 1,
                },
                {
                    "fieldname": "quality_inspection_notes",
                    "fieldtype": "Text Editor",
                    "label": "Quality Inspection Notes",
                    "insert_after": "total_inspections_pending",
                },
                {
                    "fieldname": "quality_inspection_notes_ar",
                    "fieldtype": "Text Editor",
                    "label": "ملاحظات فحص الجودة",
                    "insert_after": "quality_inspection_notes",
                    "translatable": 1,
                },
            ],
        }
    ]

    # Custom fields for Purchase Receipt Item child table
    purchase_receipt_item_fields = [
        {
            "dt": "Purchase Receipt Item",
            "properties": [
                {
                    "fieldname": "quality_inspection_required",
                    "fieldtype": "Check",
                    "label": "QI Required",
                    "insert_after": "quality_inspection",
                    "default": 0,
                    "in_list_view": 1,
                    "read_only": 1,
                },
                {
                    "fieldname": "inspection_status",
                    "fieldtype": "Select",
                    "label": "Inspection Status",
                    "options": "\nNot Required\nPending\nIn Progress\nPassed\nFailed",
                    "insert_after": "quality_inspection_required",
                    "default": "Not Required",
                    "in_list_view": 1,
                    "read_only": 1,
                },
                {
                    "fieldname": "inspections_completed",
                    "fieldtype": "Int",
                    "label": "Inspections Completed",
                    "insert_after": "inspection_status",
                    "default": 0,
                    "read_only": 1,
                },
                {
                    "fieldname": "quality_score",
                    "fieldtype": "Float",
                    "label": "Quality Score (%)",
                    "insert_after": "inspections_completed",
                    "precision": 2,
                    "read_only": 1,
                },
                {
                    "fieldname": "batch_inspections_required",
                    "fieldtype": "Int",
                    "label": "Batch Inspections Required",
                    "insert_after": "quality_score",
                    "default": 1,
                    "description": "Number of batch/serial inspections required for this item",
                },
                {
                    "fieldname": "mobile_inspection_link",
                    "fieldtype": "Data",
                    "label": "Mobile Inspection Link",
                    "insert_after": "batch_inspections_required",
                    "read_only": 1,
                    "hidden": 1,
                },
            ],
        }
    ]

    # Add all custom fields
    all_fields = purchase_receipt_fields + purchase_receipt_item_fields

    for field_group in all_fields:
        doctype = field_group["dt"]

        for field in field_group["properties"]:
            # Check if field already exists
            existing_field = frappe.db.get_value(
                "Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}, "name"
            )

            if not existing_field:
                # Create custom field
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = doctype
                custom_field.update(field)
                custom_field.insert()

                frappe.msgprint(
                    _("Added custom field '{0}' to {1}").format(field["fieldname"], doctype)
                )

    frappe.db.commit()


class PurchaseReceiptQualityInspectionController:
    """Controller for Purchase Receipt Quality Inspection integration"""

    def __init__(self, doc):
        self.doc = doc

    def validate(self):
        """Validate Purchase Receipt with Quality Inspection requirements"""
        self.check_quality_inspection_requirements()
        self.update_inspection_status()
        self.validate_inspection_completion()

    def check_quality_inspection_requirements(self):
        """Check if any items require quality inspection"""
        inspection_required = False
        total_pending = 0

        for item in self.doc.items:
            # Check if item requires quality inspection
            item_qi_required = frappe.db.get_value(
                "Item", item.item_code, "inspection_required_before_delivery"
            )

            if item_qi_required:
                item.quality_inspection_required = 1
                inspection_required = True

                # Calculate required inspections based on batch/serial requirements
                if hasattr(item, "batch_inspections_required") and item.batch_inspections_required:
                    required_inspections = item.batch_inspections_required
                else:
                    required_inspections = 1

                # Check existing inspections
                existing_inspections = frappe.db.count(
                    "Quality Inspection",
                    {
                        "purchase_receipt": self.doc.name,
                        "purchase_receipt_item": item.name,
                        "docstatus": 1,
                    },
                )

                if hasattr(item, "inspections_completed"):
                    item.inspections_completed = existing_inspections

                if existing_inspections < required_inspections:
                    if hasattr(item, "inspection_status"):
                        item.inspection_status = "Pending"
                    total_pending += required_inspections - existing_inspections
                else:
                    if hasattr(item, "inspection_status"):
                        item.inspection_status = "Passed"

                    # Get quality score from latest inspection
                    latest_inspection = frappe.db.get_value(
                        "Quality Inspection",
                        {
                            "purchase_receipt": self.doc.name,
                            "purchase_receipt_item": item.name,
                            "docstatus": 1,
                        },
                        "quality_score",
                        order_by="creation desc",
                    )

                    if latest_inspection:
                        item.quality_score = flt(latest_inspection)
            else:
                item.quality_inspection_required = 0
                if hasattr(item, "inspection_status"):
                    item.inspection_status = "Not Required"

        # Update header fields
        self.doc.quality_inspection_required = int(inspection_required)
        if hasattr(self.doc, "total_inspections_pending"):
            self.doc.total_inspections_pending = total_pending

    def update_inspection_status(self):
        """Update overall inspection status"""
        if not self.doc.quality_inspection_required:
            if hasattr(self.doc, "quality_inspection_status"):
                self.doc.quality_inspection_status = "Not Required"
            if hasattr(self.doc, "quality_inspection_status_ar"):
                self.doc.quality_inspection_status_ar = "غير مطلوب"
            return

        pending_items = [item for item in self.doc.items if hasattr(item, "inspection_status") and item.inspection_status == "Pending"]
        failed_items = [item for item in self.doc.items if hasattr(item, "inspection_status") and item.inspection_status == "Failed"]

        if failed_items:
            if hasattr(self.doc, "quality_inspection_status"):
                self.doc.quality_inspection_status = "Failed"
            if hasattr(self.doc, "quality_inspection_status_ar"):
                self.doc.quality_inspection_status_ar = "فشل"
        elif pending_items:
            if any(hasattr(item, "inspection_status") and item.inspection_status == "In Progress" for item in self.doc.items):
                if hasattr(self.doc, "quality_inspection_status"):
                    self.doc.quality_inspection_status = "In Progress"
                if hasattr(self.doc, "quality_inspection_status_ar"):
                    self.doc.quality_inspection_status_ar = "قيد التنفيذ"
            else:
                if hasattr(self.doc, "quality_inspection_status"):
                    self.doc.quality_inspection_status = "Pending"
                if hasattr(self.doc, "quality_inspection_status_ar"):
                    self.doc.quality_inspection_status_ar = "في الانتظار"
        else:
            if hasattr(self.doc, "quality_inspection_status"):
                self.doc.quality_inspection_status = "Completed"
            if hasattr(self.doc, "quality_inspection_status_ar"):
                self.doc.quality_inspection_status_ar = "مكتمل"

    def validate_inspection_completion(self):
        """Validate that all required inspections are completed before submission"""
        if self.doc.docstatus == 1:  # On submission
            if (self.doc.quality_inspection_required and 
                hasattr(self.doc, "total_inspections_pending") and 
                self.doc.total_inspections_pending > 0):
                frappe.throw(
                    _("Cannot submit Purchase Receipt. {0} quality inspections are still pending.").format(
                        self.doc.total_inspections_pending
                    )
                )

    def on_submit(self):
        """Actions after Purchase Receipt submission"""
        if self.doc.quality_inspection_required:
            self.create_pending_inspection_notifications()

    def create_pending_inspection_notifications(self):
        """Create notifications for pending inspections"""
        pending_items = [item for item in self.doc.items if item.inspection_status == "Pending"]

        if pending_items:
            # Create notification for quality team
            notification_doc = frappe.new_doc("Notification Log")
            notification_doc.subject = _(
                "Quality Inspection Required for Purchase Receipt {0}"
            ).format(self.doc.name)
            notification_doc.email_content = self.get_inspection_notification_content(pending_items)
            notification_doc.document_type = "Purchase Receipt"
            notification_doc.document_name = self.doc.name
            notification_doc.for_user = frappe.db.get_value(
                "User", {"role": "Quality Inspector"}, "name"
            )
            notification_doc.insert()


@frappe.whitelist()
def create_quality_inspection_from_purchase_receipt(purchase_receipt, item_code, item_row=None):
    """Create Quality Inspection record from Purchase Receipt"""

    pr_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)

    # Find the item
    pr_item = None
    for item in pr_doc.items:
        if item.item_code == item_code and (not item_row or item.name == item_row):
            pr_item = item
            break

    if not pr_item:
        frappe.throw(
            _("Item {0} not found in Purchase Receipt {1}").format(item_code, purchase_receipt)
        )

    # Create Quality Inspection
    qi_doc = frappe.new_doc("Quality Inspection")
    qi_doc.purchase_receipt = purchase_receipt
    qi_doc.purchase_receipt_item = pr_item.name
    qi_doc.item_code = item_code
    qi_doc.supplier = pr_doc.supplier
    if hasattr(pr_item, "batch_no"):
        qi_doc.batch_no = pr_item.batch_no
    qi_doc.sample_size = 1

    # Get inspection template if available
    inspection_template = frappe.db.get_value("Item", item_code, "quality_inspection_template")
    if inspection_template:
        qi_doc.quality_inspection_template = inspection_template

    # Set default inspector
    default_inspector = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if default_inspector:
        qi_doc.inspected_by = default_inspector

    qi_doc.insert()

    return qi_doc.name


@frappe.whitelist()
def get_mobile_inspection_url(purchase_receipt, item_code, item_row):
    """Generate mobile inspection URL for technicians"""

    # Create mobile-friendly URL with parameters
    base_url = frappe.utils.get_url()
    mobile_url = f"{base_url}/app/quality-inspection/new"

    # Add URL parameters for auto-population
    params = {
        "purchase_receipt": purchase_receipt,
        "item_code": item_code,
        "purchase_receipt_item": item_row,
    }

    import urllib.parse

    query_string = urllib.parse.urlencode(params)
    full_url = f"{mobile_url}?{query_string}"

    return full_url


@frappe.whitelist()
def update_purchase_receipt_inspection_status(purchase_receipt):
    """Update Purchase Receipt inspection status after QI submission"""

    pr_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)
    controller = PurchaseReceiptQualityInspectionController(pr_doc)
    controller.validate()

    pr_doc.save()

    return {
        "status": getattr(pr_doc, "quality_inspection_status", "Not Required"),
        "pending_inspections": getattr(pr_doc, "total_inspections_pending", 0),
    }


@frappe.whitelist()
def get_inspection_summary(purchase_receipt):
    """Get inspection summary for Purchase Receipt"""

    pr_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)

    summary = {
        "total_items": len(pr_doc.items),
        "items_requiring_inspection": len(
            [item for item in pr_doc.items if getattr(item, "quality_inspection_required", 0)]
        ),
        "inspections_completed": sum([getattr(item, "inspections_completed", 0) for item in pr_doc.items]),
        "inspections_pending": getattr(pr_doc, "total_inspections_pending", 0),
        "overall_status": getattr(pr_doc, "quality_inspection_status", "Not Required"),
        "items_detail": [],
    }

    for item in pr_doc.items:
        if getattr(item, "quality_inspection_required", 0):
            summary["items_detail"].append(
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "item_name_ar": getattr(item, "item_name_ar", ""),
                    "inspection_status": getattr(item, "inspection_status", "Not Required"),
                    "inspections_completed": getattr(item, "inspections_completed", 0),
                    "batch_inspections_required": getattr(item, "batch_inspections_required", 1),
                    "quality_score": getattr(item, "quality_score", 0),
                    "mobile_url": get_mobile_inspection_url(
                        purchase_receipt, item.item_code, item.name
                    ),
                }
            )

    return summary
