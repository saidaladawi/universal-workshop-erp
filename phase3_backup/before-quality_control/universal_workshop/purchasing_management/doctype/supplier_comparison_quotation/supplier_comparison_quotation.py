# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SupplierComparisonQuotation(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate supplier comparison quotation data"""
        self.validate_rates()
        self.validate_dates()
        self.calculate_amount()
        self.set_supplier_name()
        self.set_item_name()

    def validate_rates(self):
        """Validate quoted rates are positive"""
        if self.quoted_rate and self.quoted_rate <= 0:
            frappe.throw(_("Quoted rate must be greater than zero"))

        if self.qty and self.qty <= 0:
            frappe.throw(_("Quantity must be greater than zero"))

    def validate_dates(self):
        """Validate quotation dates"""
        if self.quotation_date and self.valid_till:
            if getdate(self.valid_till) < getdate(self.quotation_date):
                frappe.throw(_("Valid Till date cannot be before Quotation Date"))

    def calculate_amount(self):
        """Calculate total amount"""
        if self.quoted_rate and self.qty:
            self.amount = flt(self.quoted_rate) * flt(self.qty)

    def set_supplier_name(self):
        """Set supplier name from Supplier master"""
        if self.supplier and not self.supplier_name:
            supplier = frappe.get_doc("Supplier", self.supplier)
            self.supplier_name = supplier.supplier_name

    def set_item_name(self):
        """Set item name from Item master"""
        if self.item_code and not self.item_name:
            item = frappe.get_doc("Item", self.item_code)
            self.item_name = item.item_name
