import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, get_datetime, add_days, cint, flt
import json


class QualityInspectionChecklist(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate quality inspection checklist"""
        self.validate_service_order()
        self.validate_inspection_items()
        self.update_summary_fields()
        self.set_default_values()

    def validate_service_order(self):
        """Validate service order exists and is valid"""
        if not self.service_order:
            frappe.throw(_("Service Order is required"))

        # Check if service order exists
        if not frappe.db.exists("Sales Order", self.service_order):
            frappe.throw(_("Service Order {0} does not exist").format(self.service_order))

        # Get service order details
        service_order = frappe.get_doc("Sales Order", self.service_order)

        # Auto-populate customer and vehicle details
        if not self.customer:
            self.customer = service_order.customer

        if not self.vehicle_registration and hasattr(service_order, "vehicle_registration"):
            self.vehicle_registration = service_order.vehicle_registration

    def validate_inspection_items(self):
        """Validate inspection items configuration"""
        if not self.inspection_items:
            frappe.throw(_("At least one inspection item is required"))

        # Check for duplicate item codes
        item_codes = []
        for item in self.inspection_items:
            if item.item_code in item_codes:
                frappe.throw(_("Duplicate inspection item code: {0}").format(item.item_code))
            item_codes.append(item.item_code)

            # Validate item details
            if not item.item_name:
                frappe.throw(_("Item name is required for item code: {0}").format(item.item_code))

            if not item.category:
                frappe.throw(_("Category is required for item: {0}").format(item.item_name))

    def update_summary_fields(self):
        """Update summary fields based on inspection items"""
        if not self.inspection_items:
            return

        total = len(self.inspection_items)
        passed = sum(1 for item in self.inspection_items if item.status == "pass")
        failed = sum(1 for item in self.inspection_items if item.status == "fail")
        completed = passed + failed

        self.total_items = total
        self.passed_items = passed
        self.failed_items = failed
        self.completion_percentage = (completed / total) * 100 if total > 0 else 0

        # Update overall status based on completion
        if completed == 0:
            if self.status not in ["draft", "approved", "rejected"]:
                self.status = "draft"
        elif completed < total:
            if self.status not in ["approved", "rejected"]:
                self.status = "in_progress"
        elif failed > 0:
            if self.status not in ["approved", "rejected"]:
                self.status = "failed"
        else:
            if self.status not in ["approved", "rejected"]:
                self.status = "passed"

    def set_default_values(self):
        """Set default values for new documents"""
        if not self.inspection_date:
            self.inspection_date = get_datetime()

        if not self.status:
            self.status = "draft"

        self.last_updated = get_datetime()

    def before_save(self):
        """Actions before saving the document"""
        self.last_updated = get_datetime()

    def on_update(self):
        """Actions after updating the document"""
        # Update service order QC status
        self.update_service_order_qc_status()

        # Send real-time updates
        self.publish_inspection_update()

    def update_service_order_qc_status(self):
        """Update QC status in the linked service order"""
        if not self.service_order:
            return

        try:
            service_order = frappe.get_doc("Sales Order", self.service_order)

            # Determine QC status based on checklist status
            qc_status = "Pending"
            if self.status == "approved":
                qc_status = "Passed"
            elif self.status == "rejected" or self.status == "failed":
                qc_status = "Failed"
            elif self.status == "in_progress":
                qc_status = "In Progress"

            # Update service order
            service_order.db_set("qc_status", qc_status)

            if self.status in ["approved", "rejected"]:
                service_order.db_set("qc_completion_date", self.last_updated)

            # Add comment to service order timeline
            service_order.add_comment("Info", _("Quality Control Status: {0}").format(qc_status))

        except Exception as e:
            frappe.log_error(f"Failed to update service order QC status: {str(e)}")

    def publish_inspection_update(self):
        """Publish real-time inspection updates"""
        try:
            frappe.publish_realtime(
                "quality_inspection_update",
                {
                    "checklist_id": self.name,
                    "service_order": self.service_order,
                    "status": self.status,
                    "completion_percentage": self.completion_percentage,
                    "passed_items": self.passed_items,
                    "failed_items": self.failed_items,
                    "total_items": self.total_items,
                    "timestamp": self.last_updated,
                },
                doctype="Quality Inspection Checklist",
                docname=self.name,
            )
        except Exception as e:
            frappe.log_error(f"Failed to publish inspection update: {str(e)}")

    def approve_checklist(self, approval_notes=""):
        """Approve the inspection checklist"""
        # Validate all mandatory items are completed
        incomplete_mandatory = []
        for item in self.inspection_items:
            if item.is_mandatory and item.status not in ["pass", "fail"]:
                incomplete_mandatory.append(item.item_name)

        if incomplete_mandatory:
            frappe.throw(
                _("Mandatory items not completed: {0}").format(", ".join(incomplete_mandatory))
            )

        # Check if any mandatory items failed
        failed_mandatory = []
        for item in self.inspection_items:
            if item.is_mandatory and item.status == "fail":
                failed_mandatory.append(item.item_name)

        if failed_mandatory:
            self.status = "rejected"
            self.rejection_reason = f"Failed mandatory items: {', '.join(failed_mandatory)}"
            self.rejection_reason_ar = f"عناصر إجبارية فاشلة: {', '.join(failed_mandatory)}"
        else:
            self.status = "approved"

        self.approved_by = frappe.session.user
        self.approval_date = get_datetime()
        self.approval_notes = approval_notes
        self.approval_notes_ar = self._translate_to_arabic(approval_notes)

        self.save()

        # Send notifications
        self.send_approval_notifications()

        return {
            "status": "success",
            "checklist_status": self.status,
            "message": _("Inspection {0} successfully").format(self.status),
        }

    def reject_checklist(self, rejection_reason=""):
        """Reject the inspection checklist"""
        self.status = "rejected"
        self.rejected_by = frappe.session.user
        self.rejection_date = get_datetime()
        self.rejection_reason = rejection_reason
        self.rejection_reason_ar = self._translate_to_arabic(rejection_reason)

        self.save()

        # Send notifications
        self.send_rejection_notifications()

        return {"status": "success", "message": _("Inspection rejected successfully")}

    def send_approval_notifications(self):
        """Send notifications for inspection approval"""
        try:
            # Import here to avoid circular imports
            from universal_workshop.sales_service.customer_notifications import (
                CustomerNotificationSystem,
            )

            if self.service_order:
                notification_system = CustomerNotificationSystem(self.service_order)

                if self.status == "approved":
                    notification_system.send_workflow_notification(
                        "service_progress",
                        "completed",
                        {
                            "qc_status": "passed",
                            "completion_date": self.approval_date,
                            "checklist_id": self.name,
                        },
                    )

        except Exception as e:
            frappe.log_error(f"Failed to send approval notifications: {str(e)}")

    def send_rejection_notifications(self):
        """Send notifications for inspection rejection"""
        try:
                CustomerNotificationSystem,
            )

            if self.service_order:
                notification_system = CustomerNotificationSystem(self.service_order)

                notification_system.send_workflow_notification(
                    "service_progress",
                    "on_hold",
                    {
                        "hold_reason": "Quality control failed",
                        "hold_reason_ar": "فشل في مراقبة الجودة",
                        "rejection_reason": self.rejection_reason,
                        "checklist_id": self.name,
                    },
                )

        except Exception as e:
            frappe.log_error(f"Failed to send rejection notifications: {str(e)}")

    def get_inspection_summary(self):
        """Get inspection summary data"""
        summary = {
            "checklist_id": self.name,
            "service_order": self.service_order,
            "customer": self.customer,
            "vehicle_registration": self.vehicle_registration,
            "status": self.status,
            "completion_percentage": self.completion_percentage,
            "total_items": self.total_items,
            "passed_items": self.passed_items,
            "failed_items": self.failed_items,
            "pending_items": self.total_items - self.passed_items - self.failed_items,
            "creation_date": self.creation,
            "completion_date": self.approval_date,
            "approved_by": self.approved_by,
        }

        # Group items by category
        categories = {}
        for item in self.inspection_items:
            category = item.category
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "pending": 0}

            categories[category]["total"] += 1
            if item.status == "pass":
                categories[category]["passed"] += 1
            elif item.status == "fail":
                categories[category]["failed"] += 1
            else:
                categories[category]["pending"] += 1

        summary["categories"] = categories

        return summary

    def _translate_to_arabic(self, text):
        """Simple Arabic translation for common terms"""
        if not text:
            return ""

        translation_map = {
            "Approved": "موافق عليه",
            "Rejected": "مرفوض",
            "Good condition": "حالة جيدة",
            "Needs attention": "يحتاج انتباه",
            "Replace immediately": "استبدل فوراً",
            "Check required": "فحص مطلوب",
            "Excellent": "ممتاز",
            "Satisfactory": "مرضي",
            "Poor": "ضعيف",
            "Quality control passed": "مراقبة الجودة نجحت",
            "Quality control failed": "مراقبة الجودة فشلت",
        }

        # Simple word replacement
        result = text
        for english, arabic in translation_map.items():
            result = result.replace(english, arabic)

        return result


# Document Event Hooks
def on_doctype_update():
    """Called when the DocType is updated"""
    frappe.db.add_index("Quality Inspection Checklist", ["service_order", "status"])
    frappe.db.add_index("Quality Inspection Checklist", ["customer"])
    frappe.db.add_index("Quality Inspection Checklist", ["checklist_type", "vehicle_type"])


def validate_inspection_workflow(doc, method):
    """Validate inspection workflow transitions"""
    if doc.doctype != "Quality Inspection Checklist":
        return

    # Get previous status if document exists
    if not doc.is_new():
        old_doc = frappe.get_doc("Quality Inspection Checklist", doc.name)
        old_status = old_doc.status
        new_status = doc.status

        # Define valid status transitions
        valid_transitions = {
            "draft": ["in_progress", "approved", "rejected"],
            "in_progress": ["passed", "failed", "approved", "rejected"],
            "passed": ["approved", "rejected"],
            "failed": ["rejected", "in_progress"],  # Allow retry
            "approved": [],  # Final state
            "rejected": ["in_progress"],  # Allow retry
        }

        if old_status != new_status:
            if new_status not in valid_transitions.get(old_status, []):
                frappe.throw(
                    _("Invalid status transition from {0} to {1}").format(old_status, new_status)
                )
