import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now
import json


class QualityInspection(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate quality inspection data"""
        self.validate_inspection_date()
        self.validate_sample_size()
        self.calculate_quality_metrics()

    def before_save(self):
        """Set default values and fetch related data"""
        self.set_item_details()
        self.set_supplier_details()
        self.set_inspector_details()
        self.set_audit_trail()

    def on_submit(self):
        """Update supplier scorecard and create follow-up actions"""
        self.update_supplier_scorecard()
        self.create_corrective_actions()
        self.notify_quality_team()

    def validate_inspection_date(self):
        """Ensure inspection date is not in future"""
        if self.inspection_date and getdate(self.inspection_date) > getdate():
            frappe.throw(_("Inspection date cannot be in the future"))

    def validate_sample_size(self):
        """Validate sample size is reasonable"""
        if self.sample_size and self.sample_size <= 0:
            frappe.throw(_("Sample size must be greater than 0"))

    def set_item_details(self):
        """Fetch and set item details"""
        if self.item_code:
            item = frappe.get_doc("Item", self.item_code)
            self.item_name = item.item_name
            # Set Arabic name if available
            if hasattr(item, "item_name_ar") and item.item_name_ar:
                self.item_name_ar = item.item_name_ar

    def set_supplier_details(self):
        """Fetch and set supplier details"""
        if self.supplier:
            supplier = frappe.get_doc("Supplier", self.supplier)
            self.supplier_name = supplier.supplier_name
            # Set Arabic name if available
            if hasattr(supplier, "supplier_name_ar") and supplier.supplier_name_ar:
                self.supplier_name_ar = supplier.supplier_name_ar

    def set_inspector_details(self):
        """Fetch and set inspector details"""
        if self.inspected_by:
            employee = frappe.get_doc("Employee", self.inspected_by)
            self.inspector_name = employee.employee_name
            # Set Arabic name if available
            if hasattr(employee, "employee_name_ar") and employee.employee_name_ar:
                self.inspector_name_ar = employee.employee_name_ar

        if self.approved_by:
            approver = frappe.get_doc("Employee", self.approved_by)
            self.approved_by_name = approver.employee_name

    def set_audit_trail(self):
        """Set audit trail information"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = now()

        self.modified_by = frappe.session.user
        self.modified_date = now()

    def calculate_quality_metrics(self):
        """Calculate quality score and pass percentage"""
        if not self.inspection_criteria:
            return

        total_criteria = len(self.inspection_criteria)
        passed_criteria = 0
        total_score = 0
        max_score = 0

        for criterion in self.inspection_criteria:
            max_score += flt(criterion.max_value, 2)
            total_score += flt(criterion.actual_value, 2)

            if criterion.result == "Pass":
                passed_criteria += 1

        # Calculate pass percentage
        self.pass_percentage = (passed_criteria / total_criteria) * 100 if total_criteria > 0 else 0

        # Calculate quality score (0-100)
        self.quality_score = (total_score / max_score) * 100 if max_score > 0 else 0

        # Determine overall result
        if self.pass_percentage >= 95:
            self.overall_result = "Pass"
        elif self.pass_percentage >= 70:
            self.overall_result = "Partial Pass"
            self.corrective_action_required = 1
        else:
            self.overall_result = "Fail"
            self.corrective_action_required = 1

        # Update inspection status
        if self.overall_result == "Fail":
            self.inspection_status = "Rejected"
        else:
            self.inspection_status = "Completed"

    def update_supplier_scorecard(self):
        """Update supplier performance metrics"""
        if not self.supplier:
            return

        # Get or create supplier scorecard
        scorecard_name = f"{self.supplier}-{getdate().year}"

        if not frappe.db.exists("Supplier Scorecard", scorecard_name):
            scorecard = frappe.new_doc("Supplier Scorecard")
            scorecard.supplier = self.supplier
            scorecard.year = getdate().year
            scorecard.total_inspections = 0
            scorecard.passed_inspections = 0
            scorecard.failed_inspections = 0
            scorecard.total_quality_score = 0
            scorecard.insert()
        else:
            scorecard = frappe.get_doc("Supplier Scorecard", scorecard_name)

        # Update metrics
        scorecard.total_inspections += 1
        scorecard.total_quality_score += flt(self.quality_score, 2)

        if self.overall_result == "Pass":
            scorecard.passed_inspections += 1
        else:
            scorecard.failed_inspections += 1

        # Calculate averages
        scorecard.average_quality_score = (
            scorecard.total_quality_score / scorecard.total_inspections
        )
        scorecard.pass_rate = (scorecard.passed_inspections / scorecard.total_inspections) * 100

        # Update performance rating
        if scorecard.pass_rate >= 95 and scorecard.average_quality_score >= 90:
            scorecard.performance_rating = "Excellent"
        elif scorecard.pass_rate >= 85 and scorecard.average_quality_score >= 80:
            scorecard.performance_rating = "Good"
        elif scorecard.pass_rate >= 70 and scorecard.average_quality_score >= 70:
            scorecard.performance_rating = "Satisfactory"
        else:
            scorecard.performance_rating = "Needs Improvement"

        scorecard.last_updated = now()
        scorecard.save()

    def create_corrective_actions(self):
        """Create corrective action items if required"""
        if not self.corrective_action_required:
            return

        # Create corrective action document
        corrective_action = frappe.new_doc("Corrective Action")
        corrective_action.quality_inspection = self.name
        corrective_action.supplier = self.supplier
        corrective_action.item_code = self.item_code
        corrective_action.issue_description = f"Quality inspection failed for {self.item_name}"
        corrective_action.issue_description_ar = (
            f"فشل فحص الجودة لـ {self.item_name_ar or self.item_name}"
        )
        corrective_action.priority = "High" if self.overall_result == "Fail" else "Medium"
        corrective_action.status = "Open"
        corrective_action.assigned_to = self.inspected_by
        corrective_action.due_date = frappe.utils.add_days(getdate(), 7)
        corrective_action.insert()

    def notify_quality_team(self):
        """Send notifications to quality team"""
        if self.overall_result == "Fail":
            # Send notification to quality manager
            frappe.sendmail(
                recipients=["quality@universal-workshop.com"],
                subject=_("Quality Inspection Failed: {0}").format(self.item_name),
                message=self.get_notification_message(),
                reference_doctype=self.doctype,
                reference_name=self.name,
            )

    def get_notification_message(self):
        """Get notification message content"""
        message = f"""
        Quality Inspection Failed
        
        Item: {self.item_name} ({self.item_code})
        Supplier: {self.supplier_name} ({self.supplier})
        Quality Score: {self.quality_score}%
        Pass Rate: {self.pass_percentage}%
        Defects Found: {self.defects_found}
        
        Inspector: {self.inspector_name}
        Inspection Date: {self.inspection_date}
        
        Remarks: {self.inspection_remarks or 'None'}
        
        Please review and take necessary action.
        """
        return message


@frappe.whitelist()
def get_quality_inspection_template(item_code):
    """Get quality inspection template for item"""
    templates = frappe.get_list(
        "Quality Inspection Template",
        filters={"item_code": item_code},
        fields=["name", "template_name", "inspection_criteria"],
    )

    if templates:
        template = frappe.get_doc("Quality Inspection Template", templates[0].name)
        return {"template_name": template.name, "criteria": template.inspection_criteria}
    return None


@frappe.whitelist()
def get_supplier_quality_metrics(supplier, from_date=None, to_date=None):
    """Get supplier quality metrics for dashboard"""
    filters = {"supplier": supplier}

    if from_date:
        filters["inspection_date"] = [">=", from_date]
    if to_date:
        filters["inspection_date"] = ["<=", to_date]

    inspections = frappe.get_list(
        "Quality Inspection",
        filters=filters,
        fields=[
            "name",
            "inspection_date",
            "item_code",
            "item_name",
            "quality_score",
            "pass_percentage",
            "overall_result",
            "defects_found",
            "corrective_action_required",
        ],
    )

    # Calculate summary metrics
    total_inspections = len(inspections)
    passed_inspections = len([i for i in inspections if i.overall_result == "Pass"])
    failed_inspections = len([i for i in inspections if i.overall_result == "Fail"])

    avg_quality_score = (
        sum([flt(i.quality_score) for i in inspections]) / total_inspections
        if total_inspections > 0
        else 0
    )
    pass_rate = (passed_inspections / total_inspections) * 100 if total_inspections > 0 else 0

    return {
        "summary": {
            "total_inspections": total_inspections,
            "passed_inspections": passed_inspections,
            "failed_inspections": failed_inspections,
            "pass_rate": round(pass_rate, 2),
            "average_quality_score": round(avg_quality_score, 2),
        },
        "inspections": inspections,
    }


@frappe.whitelist()
def create_inspection_from_purchase_receipt(purchase_receipt, item_code):
    """Create quality inspection from purchase receipt"""
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)

    # Find the item in purchase receipt
    pr_item = None
    for item in pr.items:
        if item.item_code == item_code:
            pr_item = item
            break

    if not pr_item:
        frappe.throw(
            _("Item {0} not found in Purchase Receipt {1}").format(item_code, purchase_receipt)
        )

    # Create quality inspection
    qi = frappe.new_doc("Quality Inspection")
    qi.purchase_receipt = purchase_receipt
    qi.purchase_receipt_item = pr_item.name
    qi.item_code = item_code
    qi.supplier = pr.supplier
    qi.sample_size = 1
    qi.inspection_date = getdate()
    qi.inspection_status = "Pending"

    # Get quality inspection template if available
    template = get_quality_inspection_template(item_code)
    if template:
        qi.quality_inspection_template = template["template_name"]
        qi.inspection_criteria = template["criteria"]

    qi.insert()
    return qi.name
