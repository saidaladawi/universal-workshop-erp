# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SecurityThreatIndicator(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate security threat indicator"""
        self.validate_indicator_type()
        self.validate_risk_weight()
        self.validate_severity()

    def validate_indicator_type(self):
        """Validate indicator type selection"""
        if not self.indicator_type:
            frappe.throw(_("Indicator Type is required"))

    def validate_risk_weight(self):
        """Validate risk weight is within range"""
        if self.risk_weight and (self.risk_weight < 1 or self.risk_weight > 10):
            frappe.throw(_("Risk Weight must be between 1 and 10"))

    def validate_severity(self):
        """Validate severity selection"""
        valid_severities = ["Low", "Medium", "High", "Critical"]
        if self.severity and self.severity not in valid_severities:
            frappe.throw(_("Invalid severity level"))

    def before_save(self):
        """Actions before saving"""
        if not self.detection_date:
            self.detection_date = frappe.utils.today()

        # Set default severity based on risk weight
        if not self.severity and self.risk_weight:
            if self.risk_weight <= 3:
                self.severity = "Low"
            elif self.risk_weight <= 6:
                self.severity = "Medium"
            elif self.risk_weight <= 8:
                self.severity = "High"
            else:
                self.severity = "Critical"
