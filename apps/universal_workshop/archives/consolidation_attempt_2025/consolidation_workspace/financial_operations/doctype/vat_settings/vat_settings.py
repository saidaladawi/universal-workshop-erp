# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import re

class VATSettings(Document):
    def validate(self):
        if not (0 < self.vat_rate <= 100):
            frappe.throw(_("نسبة الضريبة يجب أن تكون بين 0 و 100"))
        if not self.vat_number or not re.match(r'^OM\d{15}$', self.vat_number):
            frappe.throw(_("رقم ضريبة القيمة المضافة غير صحيح. يجب أن يكون بالشكل: OMxxxxxxxxxxxxxxx"))
        # تحقق من نوع الحساب (اختياري)
        if self.vat_account:
            acc_type = frappe.db.get_value("Account", self.vat_account, "account_type")
            if acc_type and acc_type.lower() != "tax":
                frappe.throw(_("الحساب المختار يجب أن يكون من نوع 'Tax'")) 