# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopFieldPermission(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate workshop field permission data"""
        self.validate_permission_level()
        self.validate_doctype_and_field()

    def validate_permission_level(self):
        """Validate permission level is within acceptable range"""
        if self.permission_level and (self.permission_level < 0 or self.permission_level > 9):
            frappe.throw(_("Permission level must be between 0 and 9"))

    def validate_doctype_and_field(self):
        """Validate that the specified DocType and field exist"""
        if self.doctype_name and not frappe.db.exists("DocType", self.doctype_name):
            frappe.throw(_("DocType '{0}' does not exist").format(self.doctype_name))

        if self.doctype_name and self.field_name:
            # Get DocType meta to check if field exists
            try:
                meta = frappe.get_meta(self.doctype_name)
                if not meta.has_field(self.field_name):
                    frappe.throw(
                        _("Field '{0}' does not exist in DocType '{1}'").format(
                            self.field_name, self.doctype_name
                        )
                    )
            except Exception:
                # If meta is not available, skip validation
                pass
