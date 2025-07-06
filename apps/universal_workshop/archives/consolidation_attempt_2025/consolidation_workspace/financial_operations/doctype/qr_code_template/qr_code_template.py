# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import re

REQUIRED_VARIABLES = ["{invoice_number}", "{vat_number}", "{amount}", "{date}"]

class QRCodeTemplate(Document):
    def validate(self):
        missing = [v for v in REQUIRED_VARIABLES if v not in self.template_content]
        if missing:
            frappe.throw(_("يجب أن يحتوي القالب على المتغيرات التالية: {0}").format(", ".join(missing)))

    def generate_qr(self, data):
        """Stub: Generate QR code for given data (implement with qrcode lib if needed)"""
        # Example: import qrcode; img = qrcode.make(data)
        pass 