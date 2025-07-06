# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SupplierComparisonItem(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate supplier comparison item data"""
        self.validate_quantity()
        self.set_item_details()

    def validate_quantity(self):
        """Validate quantity is positive"""
        if self.qty and self.qty <= 0:
            frappe.throw(_("Quantity must be greater than zero"))

    def set_item_details(self):
        """Set item name and description from Item master"""
        if self.item_code and not self.item_name:
            item = frappe.get_doc("Item", self.item_code)
            self.item_name = item.item_name
            if not self.description:
                self.description = item.description or item.item_name
