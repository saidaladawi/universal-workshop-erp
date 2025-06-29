import frappe
from frappe.model.document import Document
from frappe.utils import flt


class QualityInspectionCriteria(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate criteria values"""
        self.validate_value_ranges()
        self.auto_calculate_result()

    def validate_value_ranges(self):
        """Ensure min_value <= target_value <= max_value"""
        if self.min_value and self.max_value and flt(self.min_value) > flt(self.max_value):
            frappe.throw(_("Minimum value cannot be greater than maximum value"))

        if self.target_value and self.min_value and flt(self.target_value) < flt(self.min_value):
            frappe.throw(_("Target value cannot be less than minimum value"))

        if self.target_value and self.max_value and flt(self.target_value) > flt(self.max_value):
            frappe.throw(_("Target value cannot be greater than maximum value"))

    def auto_calculate_result(self):
        """Auto-calculate pass/fail based on actual value"""
        if not self.actual_value:
            return

        actual = flt(self.actual_value)

        # Check against min/max values
        if self.min_value and actual < flt(self.min_value):
            self.result = "Fail"
            return

        if self.max_value and actual > flt(self.max_value):
            self.result = "Fail"
            return

        # Check tolerance if target value is set
        if self.target_value and self.tolerance:
            target = flt(self.target_value)
            tolerance_value = (target * flt(self.tolerance)) / 100

            if abs(actual - target) > tolerance_value:
                self.result = "Fail"
                return

        # If all checks pass
        self.result = "Pass"
