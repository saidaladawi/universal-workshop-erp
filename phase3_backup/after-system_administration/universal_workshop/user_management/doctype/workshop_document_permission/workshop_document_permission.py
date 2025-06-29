# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopDocumentPermission(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate workshop document permission data"""
        self.validate_permission_level()
        self.validate_doctype_exists()

    def validate_permission_level(self):
        """Validate permission level is within acceptable range"""
        if self.permission_level and (self.permission_level < 0 or self.permission_level > 9):
            frappe.throw(_("Permission level must be between 0 and 9"))

    def validate_doctype_exists(self):
        """Validate that the specified DocType exists"""
        if self.doctype_name and not frappe.db.exists("DocType", self.doctype_name):
            frappe.throw(_("DocType '{0}' does not exist").format(self.doctype_name))
