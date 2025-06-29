# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ServiceEstimateItem(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate service estimate item"""
        self.calculate_amount()
        self.validate_technician_assignment()

    def calculate_amount(self):
        """Calculate amount based on quantity and rate"""
        if self.qty and self.rate:
            self.amount = self.qty * self.rate

    def validate_technician_assignment(self):
        """Validate technician assignment for labor items"""
        if self.estimated_hours and not self.technician:
            frappe.msgprint(
                frappe._("Technician assignment recommended for items with estimated hours"),
                indicator="orange",
            )
