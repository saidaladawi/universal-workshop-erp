# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BusinessRegistrationDocument(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate business registration document"""
        self.validate_document_type()
        self.validate_upload_date()

    def validate_document_type(self):
        """Validate document type selection"""
        if not self.document_type:
            frappe.throw(_("Document Type is required"))

    def validate_upload_date(self):
        """Validate upload date"""
        if not self.upload_date:
            self.upload_date = frappe.utils.today()

    def before_save(self):
        """Actions before saving"""
        if not self.upload_date:
            self.upload_date = frappe.utils.today()

        # Set default verification status if not set
        if not self.verification_status:
            self.verification_status = "Pending"
