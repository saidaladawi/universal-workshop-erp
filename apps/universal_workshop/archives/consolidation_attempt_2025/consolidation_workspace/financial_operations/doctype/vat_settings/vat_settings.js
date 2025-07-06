// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('VAT Settings', {
    validate: function(frm) {
        if (frm.doc.vat_rate <= 0 || frm.doc.vat_rate > 100) {
            frappe.msgprint(__('نسبة الضريبة يجب أن تكون بين 0 و 100'));
            frappe.validated = false;
        }
        if (frm.doc.vat_number && !/^OM\d{15}$/.test(frm.doc.vat_number)) {
            frappe.msgprint(__('رقم ضريبة القيمة المضافة غير صحيح. يجب أن يكون بالشكل: OMxxxxxxxxxxxxxxx'));
            frappe.validated = false;
        }
    }
}); 