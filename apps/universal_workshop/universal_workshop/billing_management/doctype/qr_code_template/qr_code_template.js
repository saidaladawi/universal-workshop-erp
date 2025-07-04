// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('QR Code Template', {
    validate: function (frm) {
        const required = ["{invoice_number}", "{vat_number}", "{amount}", "{date}"];
        let missing = required.filter(v => !frm.doc.template_content.includes(v));
        if (missing.length) {
            frappe.msgprint(__('يجب أن يحتوي القالب على المتغيرات التالية: ') + missing.join(', '));
            frappe.validated = false;
        }
    },
    refresh: function (frm) {
        frm.add_custom_button(__('معاينة القالب'), function () {
            frappe.msgprint(frm.doc.template_content || __('لا يوجد محتوى للمعاينة'));
        });
    }
}); 