# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopPermissionRole(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate workshop permission role data"""
        self.validate_role_exists()

    def validate_role_exists(self):
        """Validate that the specified workshop role exists"""
        if self.role_name and not frappe.db.exists("Workshop Role", self.role_name):
            frappe.throw(_("Workshop Role '{0}' does not exist").format(self.role_name))
