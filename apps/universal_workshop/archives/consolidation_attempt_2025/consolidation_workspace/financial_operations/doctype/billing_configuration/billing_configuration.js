frappe.ui.form.on('Billing Configuration', {
    refresh: function (frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
    },

    setup_custom_buttons: function (frm) {
        frm.add_custom_button(__('Test VAT Calculation'), function () {
            frm.trigger('test_vat_calculation');
        });

        frm.add_custom_button(__('Validate QR Settings'), function () {
            frm.trigger('validate_qr_settings');
        });
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['configuration_name_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    enable_vat: function (frm) {
        if (frm.doc.enable_vat) {
            frm.set_df_property('vat_rate', 'reqd', 1);
            frm.set_df_property('vat_account', 'reqd', 1);
            frm.set_df_property('vat_registration_number', 'reqd', 1);
        } else {
            frm.set_df_property('vat_rate', 'reqd', 0);
            frm.set_df_property('vat_account', 'reqd', 0);
            frm.set_df_property('vat_registration_number', 'reqd', 0);
        }
    },

    enable_qr_codes: function (frm) {
        if (frm.doc.enable_qr_codes) {
            frm.set_df_property('qr_code_template', 'reqd', 1);
        } else {
            frm.set_df_property('qr_code_template', 'reqd', 0);
        }
    },

    require_approval: function (frm) {
        if (frm.doc.require_approval) {
            frm.set_df_property('approval_threshold', 'reqd', 1);
            frm.set_df_property('approver_role', 'reqd', 1);
        } else {
            frm.set_df_property('approval_threshold', 'reqd', 0);
            frm.set_df_property('approver_role', 'reqd', 0);
        }
    },

    test_vat_calculation: function (frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.doctype.billing_configuration.billing_configuration.test_vat_calculation',
            args: {
                docname: frm.doc.name,
                test_amount: 100.0
            },
            callback: function (r) {
                if (r.message && !r.message.error) {
                    frappe.msgprint({
                        title: __('VAT Calculation Test'),
                        message: __(`Base Amount: ${r.message.base_amount} ${r.message.currency}<br>
                                   VAT Rate: ${r.message.vat_rate}%<br>
                                   VAT Amount: ${r.message.vat_amount} ${r.message.currency}<br>
                                   Total Amount: ${r.message.total_amount} ${r.message.currency}`),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('VAT Calculation Test'),
                        message: r.message.error || __('Test failed'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    validate_qr_settings: function (frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.doctype.billing_configuration.billing_configuration.validate_qr_code_settings',
            args: {
                docname: frm.doc.name
            },
            callback: function (r) {
                if (r.message && r.message.status === 'valid') {
                    frappe.msgprint({
                        title: __('QR Code Settings'),
                        message: __('QR code settings are valid'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('QR Code Settings'),
                        message: r.message.error || __('QR code settings validation failed'),
                        indicator: 'red'
                    });
                }
            }
        });
    }
}); 