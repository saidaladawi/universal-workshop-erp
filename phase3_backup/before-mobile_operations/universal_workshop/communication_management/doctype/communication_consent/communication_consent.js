// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Communication Consent', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_compliance_display');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields and notes
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Apply RTL to text fields that might contain Arabic
            ['notes', 'compliance_notes', 'withdrawal_reason', 'audit_trail'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'auto');
                }
            });
        }
    },

    setup_custom_buttons: function (frm) {
        // Add custom buttons based on consent status
        if (frm.doc.consent_status === "Given" && !frm.is_new()) {
            frm.add_custom_button(__('Withdraw Consent'), function () {
                frm.trigger('withdraw_consent_dialog');
            }, __('Actions'));
        }

        if (frm.doc.consent_status === "Pending Double Opt-in" && !frm.is_new()) {
            frm.add_custom_button(__('Resend Confirmation'), function () {
                frm.trigger('resend_double_optin');
            }, __('Actions'));
        }

        if (frm.doc.confirmation_token && !frm.is_new()) {
            frm.add_custom_button(__('Test Confirmation Link'), function () {
                frm.trigger('test_confirmation_link');
            }, __('Actions'));
        }

        // Add button to view all customer consents
        if (frm.doc.customer && !frm.is_new()) {
            frm.add_custom_button(__('View All Customer Consents'), function () {
                frappe.set_route('List', 'Communication Consent', {
                    'customer': frm.doc.customer
                });
            }, __('View'));
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on consent status
        frm.trigger('toggle_withdrawal_fields');
        frm.trigger('toggle_double_optin_fields');
        frm.trigger('update_channel_preferences');
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            // Auto-fill customer details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('customer_name', r.message.customer_name);
                        if (r.message.email_id && !frm.doc.email) {
                            frm.set_value('email', r.message.email_id);
                        }
                        // Try to get phone from customer if not set
                        if (r.message.mobile_no && !frm.doc.phone_number) {
                            frm.set_value('phone_number', r.message.mobile_no);
                        }
                    }
                }
            });

            // Check for existing consents
            frm.trigger('check_existing_consents');
        }
    },

    phone_number: function (frm) {
        if (frm.doc.phone_number) {
            frm.trigger('validate_oman_phone');
        }
    },

    consent_status: function (frm) {
        frm.trigger('toggle_withdrawal_fields');
        frm.trigger('toggle_double_optin_fields');
        frm.trigger('update_status_indicators');
    },

    consent_channel: function (frm) {
        frm.trigger('update_channel_preferences');
    },

    double_optin_required: function (frm) {
        frm.trigger('toggle_double_optin_fields');
    },

    validate_oman_phone: function (frm) {
        if (frm.doc.phone_number) {
            // Validate Oman phone format
            const omanPattern = /^\+968\s?\d{8}$/;
            if (!omanPattern.test(frm.doc.phone_number)) {
                frappe.msgprint({
                    title: __('Invalid Phone Format'),
                    message: __('Phone number must be in Oman format: +968 XXXXXXXX'),
                    indicator: 'orange'
                });
            }
        }
    },

    check_existing_consents: function (frm) {
        if (frm.doc.customer && frm.doc.phone_number) {
            frappe.call({
                method: 'universal_workshop.communication_management.doctype.communication_consent.communication_consent.get_customer_consent_status',
                args: {
                    customer: frm.doc.customer,
                    phone_number: frm.doc.phone_number
                },
                callback: function (r) {
                    if (r.message) {
                        frm.trigger('display_existing_consent_info', r.message);
                    }
                }
            });
        }
    },

    display_existing_consent_info: function (frm, consent_status) {
        let message = __('Existing Consent Status:') + '<br>';
        message += __('SMS: {0}', [consent_status.SMS ? '✅' : '❌']) + '<br>';
        message += __('WhatsApp: {0}', [consent_status.WhatsApp ? '✅' : '❌']) + '<br>';
        message += __('Email: {0}', [consent_status.Email ? '✅' : '❌']) + '<br>';
        message += __('Promotional: {0}', [consent_status.promotional ? '✅' : '❌']);

        frm.dashboard.add_comment(message, 'blue', true);
    },

    toggle_withdrawal_fields: function (frm) {
        const is_withdrawn = frm.doc.consent_status === "Withdrawn";

        frm.toggle_display('consent_withdrawn_date', is_withdrawn);
        frm.toggle_display('withdrawal_method', is_withdrawn);
        frm.toggle_display('withdrawal_reason', is_withdrawn);

        if (is_withdrawn) {
            frm.set_df_property('withdrawal_method', 'reqd', 1);
        } else {
            frm.set_df_property('withdrawal_method', 'reqd', 0);
        }
    },

    toggle_double_optin_fields: function (frm) {
        const is_double_optin = frm.doc.double_optin_required;
        const is_pending = frm.doc.consent_status === "Pending Double Opt-in";

        frm.toggle_display('double_optin_sent_date', is_double_optin);
        frm.toggle_display('double_optin_confirmed_date', is_double_optin);
        frm.toggle_display('confirmation_token', is_double_optin);
        frm.toggle_display('confirmation_link', is_double_optin);
        frm.toggle_display('confirmation_expires', is_double_optin);

        // Show expiration warning if pending and near expiry
        if (is_pending && frm.doc.confirmation_expires) {
            const expires = moment(frm.doc.confirmation_expires);
            const now = moment();
            const hours_left = expires.diff(now, 'hours');

            if (hours_left < 6) {
                frm.dashboard.clear_comment();
                frm.dashboard.add_comment(
                    __('⚠️ Double opt-in confirmation expires in {0} hours', [hours_left]),
                    'orange',
                    true
                );
            }
        }
    },

    update_channel_preferences: function (frm) {
        // Enable/disable channel preferences based on selected channel
        const channel = frm.doc.consent_channel;

        if (channel === "SMS") {
            frm.set_value('allow_sms', 1);
            frm.set_value('allow_whatsapp', 0);
            frm.set_df_property('allow_sms', 'read_only', 1);
            frm.set_df_property('allow_whatsapp', 'read_only', 1);
        } else if (channel === "WhatsApp") {
            frm.set_value('allow_whatsapp', 1);
            frm.set_value('allow_sms', 0);
            frm.set_df_property('allow_whatsapp', 'read_only', 1);
            frm.set_df_property('allow_sms', 'read_only', 1);
        } else if (channel === "Email") {
            frm.set_value('allow_email', 1);
            frm.set_df_property('allow_email', 'read_only', 1);
        } else if (channel === "All Channels") {
            frm.set_df_property('allow_sms', 'read_only', 0);
            frm.set_df_property('allow_whatsapp', 'read_only', 0);
            frm.set_df_property('allow_email', 'read_only', 0);
        }
    },

    update_status_indicators: function (frm) {
        // Add visual indicators for consent status
        frm.page.clear_indicator();

        if (frm.doc.consent_status === "Given") {
            frm.page.set_indicator(__('Active Consent'), 'green');
        } else if (frm.doc.consent_status === "Withdrawn") {
            frm.page.set_indicator(__('Consent Withdrawn'), 'red');
        } else if (frm.doc.consent_status === "Pending Double Opt-in") {
            frm.page.set_indicator(__('Pending Confirmation'), 'orange');
        } else if (frm.doc.consent_status === "Expired") {
            frm.page.set_indicator(__('Consent Expired'), 'red');
        }
    },

    update_compliance_display: function (frm) {
        // Show compliance status
        if (!frm.is_new()) {
            let compliance_html = '<div class="compliance-status">';

            const compliance_items = [
                { label: 'GDPR', field: 'gdpr_compliant' },
                { label: 'Oman PDPL', field: 'oman_pdpl_compliant' },
                { label: 'UAE DP', field: 'uae_compliant' }
            ];

            compliance_items.forEach(item => {
                const status = frm.doc[item.field] ? '✅' : '❌';
                compliance_html += `<span class="compliance-item">${item.label}: ${status}</span> `;
            });

            compliance_html += '</div>';

            frm.dashboard.add_comment(compliance_html, 'blue', true);
        }
    },

    withdraw_consent_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Withdraw Communication Consent'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'withdrawal_method',
                    label: __('Withdrawal Method'),
                    options: [
                        'Unsubscribe Link',
                        'SMS STOP',
                        'WhatsApp Request',
                        'Phone Call',
                        'Email Request',
                        'In-Person',
                        'Website',
                        'Mobile App'
                    ],
                    reqd: 1
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'withdrawal_reason',
                    label: __('Reason for Withdrawal (Optional)')
                }
            ],
            primary_action_label: __('Withdraw Consent'),
            primary_action: function (values) {
                frappe.call({
                    method: 'universal_workshop.communication_management.doctype.communication_consent.communication_consent.withdraw_consent_by_token',
                    args: {
                        token: frm.doc.confirmation_token,
                        method: values.withdrawal_method,
                        reason: values.withdrawal_reason || ''
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Consent withdrawn successfully'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to withdraw consent'));
                        }
                    }
                });
                dialog.hide();
            }
        });

        dialog.show();
    },

    resend_double_optin: function (frm) {
        frappe.confirm(
            __('Resend double opt-in confirmation to {0}?', [frm.doc.phone_number]),
            function () {
                frappe.call({
                    method: 'universal_workshop.communication_management.doctype.communication_consent.communication_consent.resend_double_optin',
                    args: {
                        consent_id: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Double opt-in confirmation sent successfully'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to send confirmation'));
                        }
                    }
                });
            }
        );
    },

    test_confirmation_link: function (frm) {
        if (frm.doc.confirmation_link) {
            // Open confirmation link in new tab for testing
            window.open(frm.doc.confirmation_link, '_blank');
        } else {
            frappe.msgprint(__('No confirmation link available'));
        }
    }
});

// Helper function to format Arabic text
function format_arabic_display(text) {
    if (!text) return text;

    // Add RTL mark for proper Arabic display
    return '\u202E' + text + '\u202C';
}

// Auto-format phone numbers
frappe.ui.form.on('Communication Consent', 'phone_number', function (frm) {
    if (frm.doc.phone_number && !frm.doc.phone_number.startsWith('+968')) {
        // Auto-add Oman country code if missing
        let phone = frm.doc.phone_number.replace(/\D/g, ''); // Remove non-digits
        if (phone.length === 8) {
            frm.set_value('phone_number', '+968 ' + phone);
        }
    }
});

// Real-time consent status monitoring
setInterval(function () {
    if (cur_frm && cur_frm.doctype === 'Communication Consent' && cur_frm.doc.name) {
        // Check if double opt-in has expired
        if (cur_frm.doc.consent_status === "Pending Double Opt-in" &&
            cur_frm.doc.confirmation_expires) {

            const expires = moment(cur_frm.doc.confirmation_expires);
            const now = moment();

            if (now.isAfter(expires)) {
                cur_frm.set_value('consent_status', 'Expired');
                cur_frm.save();
            }
        }
    }
}, 60000); // Check every minute 