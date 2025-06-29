// -*- coding: utf-8 -*-
/**
 * Notification Template Form Controller
 * Handles template editing, preview, validation, and Arabic RTL support
 */

frappe.ui.form.on('Notification Template', {
    refresh: function (frm) {
        frm.trigger('setup_form_layout');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
        frm.trigger('update_variable_help');
    },

    setup_form_layout: function (frm) {
        // Hide fields based on channel type
        frm.trigger('toggle_channel_specific_fields');

        // Set up live preview
        frm.trigger('setup_live_preview');

        // Add RTL support for Arabic templates
        if (frm.doc.language === 'Arabic') {
            frm.trigger('enable_rtl_mode');
        }
    },

    setup_custom_buttons: function (frm) {
        // Template Preview Button
        frm.add_custom_button(__('Generate Preview'), function () {
            frm.trigger('generate_template_preview');
        }, __('Actions'));

        // Template Testing Button
        if (frm.doc.approval_status === 'Approved') {
            frm.add_custom_button(__('Test Template'), function () {
                frm.trigger('test_template');
            }, __('Actions'));
        }

        // Approval Actions
        if (frm.doc.approval_status === 'Pending Approval' && frappe.user.has_role('System Manager')) {
            frm.add_custom_button(__('Approve'), function () {
                frm.trigger('approve_template');
            }, __('Approval'));

            frm.add_custom_button(__('Reject'), function () {
                frm.trigger('reject_template');
            }, __('Approval'));
        }

        // Variable Helper Button
        frm.add_custom_button(__('Insert Variable'), function () {
            frm.trigger('show_variable_picker');
        }, __('Template'));

        // Quick Templates
        if (frm.is_new()) {
            frm.add_custom_button(__('Load Template'), function () {
                frm.trigger('show_template_picker');
            }, __('Template'));
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic language templates
        if (frm.doc.language === 'Arabic') {
            frm.fields_dict.template_body.$wrapper.find('textarea, .ql-editor').attr('dir', 'rtl');
            frm.fields_dict.template_subject.$input.attr('dir', 'rtl');
        } else {
            frm.fields_dict.template_body.$wrapper.find('textarea, .ql-editor').attr('dir', 'ltr');
            frm.fields_dict.template_subject.$input.attr('dir', 'ltr');
        }
    },

    language: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('update_variable_help');
        frm.trigger('load_default_template');
    },

    channel_type: function (frm) {
        frm.trigger('toggle_channel_specific_fields');
        frm.trigger('update_max_length');
        frm.trigger('update_variable_help');
    },

    template_category: function (frm) {
        frm.trigger('update_variable_help');
        if (frm.is_new()) {
            frm.trigger('load_default_template');
        }
    },

    toggle_channel_specific_fields: function (frm) {
        // Show/hide fields based on channel type
        frm.toggle_display('template_subject', frm.doc.channel_type === 'Email');
        frm.toggle_display(['whatsapp_template_id', 'whatsapp_template_status'],
            frm.doc.channel_type === 'WhatsApp');
        frm.toggle_display('estimated_segments', frm.doc.channel_type === 'SMS');
    },

    update_max_length: function (frm) {
        // Set default max length based on channel
        if (!frm.doc.max_length) {
            let defaults = {
                'SMS': 160,
                'WhatsApp': 4096,
                'Email': 10000
            };
            frm.set_value('max_length', defaults[frm.doc.channel_type] || 160);
        }
    },

    template_body: function (frm) {
        // Live preview update
        clearTimeout(frm._preview_timeout);
        frm._preview_timeout = setTimeout(() => {
            frm.trigger('generate_template_preview');
        }, 1000);

        // Character count validation
        frm.trigger('validate_character_count');
    },

    validate_character_count: function (frm) {
        if (frm.doc.template_body && frm.doc.max_length) {
            let length = frm.doc.template_body.length;
            let max = frm.doc.max_length;

            if (length > max) {
                frm.set_intro(__('Warning: Template exceeds maximum length of {0} characters', [max]), 'orange');
            } else {
                frm.clear_intro();
            }
        }
    },

    setup_live_preview: function (frm) {
        // Add preview refresh on context change
        if (frm.fields_dict.preview_context_json) {
            frm.fields_dict.preview_context_json.$input.on('input', function () {
                clearTimeout(frm._context_timeout);
                frm._context_timeout = setTimeout(() => {
                    frm.trigger('generate_template_preview');
                }, 1500);
            });
        }
    },

    generate_template_preview: function (frm) {
        if (!frm.doc.template_body) return;

        frappe.call({
            method: 'preview_template',
            doc: frm.doc,
            args: {
                context_json: frm.doc.preview_context_json || '{}'
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frm.set_value('rendered_preview', r.message.rendered_template);

                    // Show character count and segment info
                    let info = r.message.info;
                    if (info) {
                        let message = __('Characters: {0}', [info.character_count]);
                        if (info.estimated_segments) {
                            message += __(', SMS Segments: {0}', [info.estimated_segments]);
                        }
                        frm.set_df_property('rendered_preview', 'description', message);
                    }
                } else if (r.message && r.message.error) {
                    frm.set_value('rendered_preview', __('Preview Error: {0}', [r.message.error]));
                }
            }
        });
    },

    update_variable_help: function (frm) {
        // Update variable help based on category and language
        let variables = frm.trigger('get_category_variables');
        let help_html = frm.trigger('build_variable_help_html', variables);
        frm.set_df_property('template_variables_help', 'options', help_html);
    },

    get_category_variables: function (frm) {
        let base_vars = [
            'customer_name', 'customer_name_ar', 'workshop_name', 'workshop_phone',
            'current_date', 'current_time'
        ];

        let category_vars = {
            'Appointment Confirmation': ['appointment_date', 'appointment_time', 'service_type', 'vehicle_number'],
            'Appointment Reminder': ['appointment_date', 'appointment_time', 'service_type', 'vehicle_number'],
            'Service Update': ['vehicle_number', 'service_type', 'progress_status', 'estimated_completion'],
            'Service Completion': ['vehicle_number', 'service_type', 'total_amount', 'invoice_number'],
            'Invoice Notification': ['invoice_number', 'total_amount', 'due_date', 'payment_link'],
            'Payment Reminder': ['invoice_number', 'total_amount', 'days_overdue', 'due_date'],
            'Quotation': ['quotation_number', 'vehicle_number', 'services_list', 'total_amount', 'valid_until']
        };

        let category = frm.doc.template_category;
        return base_vars.concat(category_vars[category] || []);
    },

    build_variable_help_html: function (frm, variables) {
        let lang = frm.doc.language === 'Arabic' ? 'ar' : 'en';
        let var_examples = variables.map(v => `{{ doc.${v} }}`).join('<br/>');

        return `
            <div class="text-muted" style="direction: ${lang === 'ar' ? 'rtl' : 'ltr'}">
                <strong>${__('Available Variables')}:</strong><br/>
                ${var_examples}<br/><br/>
                <strong>${__('Conditional Logic')}:</strong><br/>
                {% if doc.language == "ar" %}${__('Arabic text')}{% else %}${__('English text')}{% endif %}<br/>
                {{ doc.customer_name or "${__('Valued Customer')}" }}<br/><br/>
                <strong>${__('Formatting Functions')}:</strong><br/>
                {{ format_currency(doc.total_amount) }}<br/>
                {{ format_date(doc.appointment_date) }}
            </div>
        `;
    },

    show_variable_picker: function (frm) {
        let variables = frm.trigger('get_category_variables');

        let d = new frappe.ui.Dialog({
            title: __('Insert Variable'),
            fields: [
                {
                    label: __('Variable'),
                    fieldname: 'variable',
                    fieldtype: 'Select',
                    options: variables.map(v => ({ label: v, value: `{{ doc.${v} }}` })),
                    reqd: 1
                },
                {
                    label: __('With Fallback'),
                    fieldname: 'with_fallback',
                    fieldtype: 'Check'
                },
                {
                    label: __('Fallback Text'),
                    fieldname: 'fallback_text',
                    fieldtype: 'Data',
                    depends_on: 'with_fallback'
                }
            ],
            primary_action_label: __('Insert'),
            primary_action: function (values) {
                let variable_text = values.variable;
                if (values.with_fallback && values.fallback_text) {
                    variable_text = variable_text.replace('}}', ` or "${values.fallback_text}"}}`);
                }

                // Insert at cursor position in template_body
                frm.trigger('insert_text_at_cursor', 'template_body', variable_text);
                d.hide();
            }
        });
        d.show();
    },

    insert_text_at_cursor: function (frm, fieldname, text) {
        let field = frm.fields_dict[fieldname];
        if (field && field.$input) {
            let input = field.$input[0];
            let start = input.selectionStart;
            let end = input.selectionEnd;
            let current_value = frm.doc[fieldname] || '';

            let new_value = current_value.substring(0, start) + text + current_value.substring(end);
            frm.set_value(fieldname, new_value);

            // Set cursor position after inserted text
            setTimeout(() => {
                input.setSelectionRange(start + text.length, start + text.length);
                input.focus();
            }, 100);
        }
    },

    load_default_template: function (frm) {
        if (!frm.is_new() || !frm.doc.template_category) return;

        frappe.call({
            method: 'universal_workshop.communication_management.api.template_api.get_default_template',
            args: {
                category: frm.doc.template_category,
                channel_type: frm.doc.channel_type,
                language: frm.doc.language
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('template_body', r.message.template_body);
                    if (r.message.template_subject) {
                        frm.set_value('template_subject', r.message.template_subject);
                    }
                    if (r.message.preview_context) {
                        frm.set_value('preview_context_json', JSON.stringify(r.message.preview_context, null, 2));
                    }
                }
            }
        });
    },

    approve_template: function (frm) {
        frappe.call({
            method: 'approve_template',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.msgprint(__('Template approved successfully'));
                    frm.reload_doc();
                }
            }
        });
    },

    reject_template: function (frm) {
        frappe.prompt([
            {
                label: __('Rejection Reason'),
                fieldname: 'reason',
                fieldtype: 'Text',
                reqd: 1
            }
        ], function (values) {
            frappe.call({
                method: 'reject_template',
                doc: frm.doc,
                args: { reason: values.reason },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__('Template rejected'));
                        frm.reload_doc();
                    }
                }
            });
        }, __('Reject Template'));
    },

    test_template: function (frm) {
        frappe.prompt([
            {
                label: __('Test Phone Number'),
                fieldname: 'phone_number',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Enter +968 phone number for testing')
            },
            {
                label: __('Test Context (JSON)'),
                fieldname: 'test_context',
                fieldtype: 'JSON',
                default: frm.doc.preview_context_json
            }
        ], function (values) {
            frappe.call({
                method: 'universal_workshop.communication_management.api.template_api.test_template',
                args: {
                    template_name: frm.doc.name,
                    phone_number: values.phone_number,
                    context_data: values.test_context || '{}'
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__('Test message sent successfully. Message ID: {0}', [r.message.message_id]));
                    } else {
                        frappe.msgprint(__('Test failed: {0}', [r.message.error || 'Unknown error']));
                    }
                }
            });
        }, __('Test Template'));
    },

    enable_rtl_mode: function (frm) {
        // Add RTL CSS class to form
        frm.page.main.addClass('rtl-template-form');

        // Apply RTL to specific fields
        setTimeout(() => {
            frm.$wrapper.find('.ql-editor, textarea').each(function () {
                $(this).css({
                    'direction': 'rtl',
                    'text-align': 'right'
                });
            });
        }, 500);
    }
});

// Auto-save draft on template body changes
frappe.ui.form.on('Notification Template', 'template_body', frappe.utils.debounce(function (frm) {
    if (!frm.is_dirty() || frm.is_new()) return;

    frappe.call({
        method: 'frappe.desk.form.save.savedocs',
        args: {
            doc: frm.doc,
            action: 'Save'
        },
        callback: function () {
            frappe.show_alert(__('Template auto-saved'), 2);
        }
    });
}, 3000)); 