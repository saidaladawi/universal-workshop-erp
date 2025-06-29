/**
 * License Manager JavaScript Controller
 * Comprehensive license management interface with Arabic RTL support
 */

frappe.ui.form.on('License Manager', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_license_monitoring');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_status_display');
    },

    onload: function(frm) {
        // Load license data on form load
        frm.trigger('load_license_info');
    },

    setup_arabic_fields: function(frm) {
        // Configure Arabic RTL fields
        const arabic_fields = [
            'business_name_ar', 'license_owner_ar', 'contact_person_ar',
            'admin_email_ar', 'violation_details_ar', 'compliance_notes_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                });
            }
        });

        // Apply RTL layout if Arabic is selected
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function(frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        if (frm.doc.name) {
            // Activation buttons
            if (frm.doc.activation_status !== "Activated / مفعل") {
                frm.add_custom_button(__('Activate License'), () => {
                    frm.trigger('show_activation_dialog');
                }, __('License Actions'));
            }

            // Validation button
            frm.add_custom_button(__('Validate License'), () => {
                frm.trigger('validate_license');
            }, __('License Actions'));

            // Hardware info refresh
            frm.add_custom_button(__('Refresh Hardware Info'), () => {
                frm.trigger('refresh_hardware_info');
            }, __('System Actions'));

            // License reset (Admin only)
            if (frappe.user.has_role('System Manager')) {
                frm.add_custom_button(__('Reset License'), () => {
                    frm.trigger('reset_license');
                }, __('Admin Actions'));
            }

            // Test server connection
            frm.add_custom_button(__('Test Server Connection'), () => {
                frm.trigger('test_server_connection');
            }, __('System Actions'));

            // Export license info
            frm.add_custom_button(__('Export License Info'), () => {
                frm.trigger('export_license_info');
            }, __('Utilities'));

            // View logs
            frm.add_custom_button(__('View Activity Logs'), () => {
                frm.trigger('show_activity_logs');
            }, __('Logs'));
        }
    },

    setup_license_monitoring: function(frm) {
        // Setup real-time license monitoring
        if (frm.doc.name && frm.doc.license_status === "Active / نشط") {
            // Update license status every 60 seconds
            frm.license_monitor = setInterval(() => {
                frm.trigger('check_license_status');
            }, 60000);
        }
    },

    setup_field_dependencies: function(frm) {
        // Show/hide fields based on license type and status
        frm.trigger('toggle_field_visibility');

        // Set field dependencies
        const conditional_fields = {
            'strict_validation': ['offline_grace_period'],
            'tamper_detection': ['signature_hash'],
            'email_notifications': ['admin_email', 'alert_recipients'],
            'compliance_mode': ['enforcement_level'],
            'api_access': ['api_rate_limit'],
            'custom_branding': ['white_label_mode']
        };

        Object.keys(conditional_fields).forEach(trigger_field => {
            if (frm.fields_dict[trigger_field]) {
                conditional_fields[trigger_field].forEach(dependent_field => {
                    frm.toggle_reqd(dependent_field, frm.doc[trigger_field]);
                    frm.toggle_display(dependent_field, frm.doc[trigger_field]);
                });
            }
        });
    },

    toggle_field_visibility: function(frm) {
        // Toggle fields based on license status
        const is_activated = frm.doc.activation_status === "Activated / مفعل";
        const is_trial = frm.doc.license_type === "Trial / تجريبي";

        // Show activation fields only if not activated
        frm.toggle_display('activation_code', !is_activated);
        frm.toggle_display('activation_attempts', !is_activated);

        // Show enterprise features only for appropriate licenses
        const enterprise_fields = [
            'api_access', 'mobile_app_access', 'custom_reports', 
            'advanced_analytics', 'third_party_integrations'
        ];

        enterprise_fields.forEach(field => {
            frm.toggle_display(field, !is_trial);
        });
    },

    update_status_display: function(frm) {
        // Update status indicators
        if (frm.doc.name) {
            const status_color = frm.trigger('get_status_color');
            
            // Update form title with status
            frm.set_df_property('license_status', 'description', 
                `<span style="color: ${status_color}; font-weight: bold;">
                    ${frm.doc.license_status}
                </span>`);

            // Show expiry warning
            if (frm.doc.expiry_date) {
                const days_to_expiry = frappe.datetime.get_diff(frm.doc.expiry_date, frappe.datetime.now_date());
                if (days_to_expiry <= 30 && days_to_expiry > 0) {
                    frm.dashboard.add_indicator(__('Expires in {0} days', [days_to_expiry]), 'orange');
                } else if (days_to_expiry <= 0) {
                    frm.dashboard.add_indicator(__('License Expired'), 'red');
                }
            }

            // Show usage information
            if (frm.doc.current_users && frm.doc.max_users) {
                const usage_percent = (frm.doc.current_users / frm.doc.max_users) * 100;
                const usage_color = usage_percent > 90 ? 'red' : usage_percent > 75 ? 'orange' : 'green';
                frm.dashboard.add_indicator(
                    __('Users: {0}/{1} ({2}%)', [frm.doc.current_users, frm.doc.max_users, Math.round(usage_percent)]), 
                    usage_color
                );
            }
        }
    },

    get_status_color: function(frm) {
        const status_colors = {
            'Active / نشط': '#28a745',
            'Expired / منتهي الصلاحية': '#dc3545',
            'Suspended / معلق': '#fd7e14',
            'Pending / في الانتظار': '#6c757d',
            'Trial / تجريبي': '#17a2b8'
        };
        return status_colors[frm.doc.license_status] || '#6c757d';
    },

    // ============ License Actions ============

    show_activation_dialog: function(frm) {
        // Show license activation dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Activate License'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'activation_code',
                    label: __('Activation Code'),
                    reqd: 1,
                    description: __('Enter the activation code provided by Universal Workshop')
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'accept_terms',
                    label: __('I accept the terms and conditions'),
                    reqd: 1
                }
            ],
            primary_action: function(data) {
                if (!data.accept_terms) {
                    frappe.msgprint(__('You must accept the terms and conditions'));
                    return;
                }

                dialog.hide();
                frm.trigger('activate_license', data.activation_code);
            },
            primary_action_label: __('Activate')
        });

        dialog.show();
    },

    activate_license: function(frm, activation_code) {
        frappe.show_progress(__('Activating License'), 60, 100);
        
        frappe.call({
            method: 'activate_license',
            doc: frm.doc,
            args: {
                activation_code: activation_code
            },
            callback: function(response) {
                frappe.hide_progress();
                
                if (response.message && response.message.success) {
                    frappe.show_alert({
                        message: __('License activated successfully'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.show_alert({
                        message: __('License activation failed'),
                        indicator: 'red'
                    });
                }
            },
            error: function(err) {
                frappe.hide_progress();
                frappe.show_alert({
                    message: __('Activation failed: {0}', [err.message || 'Unknown error']),
                    indicator: 'red'
                });
            }
        });
    },

    validate_license: function(frm) {
        frappe.show_progress(__('Validating License'), 50, 100);
        
        frappe.call({
            method: 'validate_license',
            doc: frm.doc,
            callback: function(response) {
                frappe.hide_progress();
                
                if (response.message) {
                    const result = response.message;
                    frm.trigger('show_validation_results', result);
                }
            }
        });
    },

    show_validation_results: function(frm, result) {
        const status_color = result.valid ? 'green' : 'red';
        const status_text = result.valid ? __('Valid') : __('Invalid');
        
        let message = `<div style="color: ${status_color}; font-weight: bold;">
            ${__('License Status')}: ${status_text}
        </div><br>`;

        if (result.expires_in_days > 0) {
            message += `${__('Expires in')}: ${result.expires_in_days} ${__('days')}<br>`;
        }

        if (result.messages.length > 0) {
            message += `<strong>${__('Issues')}:</strong><br>`;
            result.messages.forEach(msg => {
                message += `• ${msg}<br>`;
            });
        }

        if (result.warnings.length > 0) {
            message += `<br><strong>${__('Warnings')}:</strong><br>`;
            result.warnings.forEach(warning => {
                message += `• ${warning}<br>`;
            });
        }

        frappe.msgprint({
            title: __('License Validation Results'),
            message: message,
            indicator: result.valid ? 'green' : 'red'
        });
    },

    check_license_status: function(frm) {
        // Silent license status check
        if (frm.doc.name) {
            frappe.call({
                method: 'validate_license',
                doc: frm.doc,
                callback: function(response) {
                    if (response.message && !response.message.valid) {
                        // License became invalid
                        frm.trigger('handle_license_invalid');
                    }
                }
            });
        }
    },

    handle_license_invalid: function(frm) {
        // Handle license becoming invalid
        frappe.show_alert({
            message: __('License validation failed. Please check license status.'),
            indicator: 'red'
        });
        
        frm.reload_doc();
    },

    // ============ System Actions ============

    refresh_hardware_info: function(frm) {
        frappe.call({
            method: 'frappe.client.save',
            args: {
                doc: frm.doc
            },
            callback: function() {
                frappe.show_alert({
                    message: __('Hardware information updated'),
                    indicator: 'green'
                });
                frm.reload_doc();
            }
        });
    },

    reset_license: function(frm) {
        frappe.confirm(
            __('Are you sure you want to reset this license? This will deactivate the license and require reactivation.'),
            function() {
                frappe.call({
                    method: 'reset_license',
                    doc: frm.doc,
                    callback: function(response) {
                        if (response.message && response.message.status === 'success') {
                            frappe.show_alert({
                                message: __('License reset successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    test_server_connection: function(frm) {
        frappe.show_progress(__('Testing Connection'), 30, 100);
        
        frappe.call({
            method: 'frappe.utils.ping_url',
            args: {
                url: 'https://license.universal-workshop.com/api/ping'
            },
            callback: function(response) {
                frappe.hide_progress();
                
                const is_connected = response.message;
                frappe.show_alert({
                    message: is_connected ? 
                        __('Server connection successful') : 
                        __('Server connection failed'),
                    indicator: is_connected ? 'green' : 'red'
                });
            }
        });
    },

    // ============ Utilities ============

    export_license_info: function(frm) {
        const license_data = {
            license_code: frm.doc.license_code,
            business_name: frm.doc.business_name,
            business_name_ar: frm.doc.business_name_ar,
            license_type: frm.doc.license_type,
            edition: frm.doc.edition,
            status: frm.doc.license_status,
            activation_status: frm.doc.activation_status,
            expiry_date: frm.doc.expiry_date,
            max_users: frm.doc.max_users,
            max_devices: frm.doc.max_devices,
            max_workshops: frm.doc.max_workshops,
            hardware_fingerprint: frm.doc.hardware_fingerprint,
            exported_on: frappe.datetime.now_datetime()
        };

        const json_data = JSON.stringify(license_data, null, 2);
        const blob = new Blob([json_data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `license_${frm.doc.license_code}_${frappe.datetime.now_date()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        
        frappe.show_alert({
            message: __('License information exported'),
            indicator: 'green'
        });
    },

    show_activity_logs: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Activity Logs'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'Tab Break',
                    fieldname: 'activity_tab',
                    label: __('Activity Log')
                },
                {
                    fieldtype: 'Code',
                    fieldname: 'activity_log',
                    label: __('Activity Log'),
                    options: 'Text',
                    read_only: 1,
                    default: frm.doc.activity_log || __('No activity recorded')
                },
                {
                    fieldtype: 'Tab Break',
                    fieldname: 'error_tab',
                    label: __('Error Log')
                },
                {
                    fieldtype: 'Code',
                    fieldname: 'error_log',
                    label: __('Error Log'),
                    options: 'Text',
                    read_only: 1,
                    default: frm.doc.error_log || __('No errors recorded')
                },
                {
                    fieldtype: 'Tab Break',
                    fieldname: 'compliance_tab',
                    label: __('Compliance Log')
                },
                {
                    fieldtype: 'Code',
                    fieldname: 'compliance_log',
                    label: __('Compliance Log'),
                    options: 'Text',
                    read_only: 1,
                    default: frm.doc.compliance_log || __('No compliance issues recorded')
                }
            ]
        });

        dialog.show();
    },

    load_license_info: function(frm) {
        // Load additional license information
        if (frm.doc.name) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'License Manager',
                    filters: { name: frm.doc.name },
                    fieldname: ['current_users', 'last_validation', 'violation_count']
                },
                callback: function(response) {
                    if (response.message) {
                        // Update form with current data
                        frm.trigger('update_status_display');
                    }
                }
            });
        }
    },

    // ============ Field Change Events ============

    license_type: function(frm) {
        frm.trigger('toggle_field_visibility');
        frm.trigger('set_default_limits');
    },

    edition: function(frm) {
        frm.trigger('set_default_limits');
    },

    set_default_limits: function(frm) {
        // Set default limits based on license type and edition
        const limits = {
            'Trial / تجريبي': { users: 3, devices: 2, workshops: 1, storage: 1 },
            'Community / مجتمعي': { users: 5, devices: 3, workshops: 2, storage: 5 },
            'Professional / احترافي': { users: 25, devices: 15, workshops: 5, storage: 50 },
            'Enterprise / مؤسسي': { users: 100, devices: 50, workshops: 20, storage: 500 },
            'Unlimited / غير محدود': { users: 0, devices: 0, workshops: 0, storage: 0 }
        };

        const license_limits = limits[frm.doc.license_type];
        if (license_limits && !frm.doc.max_users) {
            frm.set_value('max_users', license_limits.users);
            frm.set_value('max_devices', license_limits.devices);
            frm.set_value('max_workshops', license_limits.workshops);
            frm.set_value('storage_limit_gb', license_limits.storage);
        }
    },

    strict_validation: function(frm) {
        frm.trigger('setup_field_dependencies');
    },

    tamper_detection: function(frm) {
        frm.trigger('setup_field_dependencies');
    },

    email_notifications: function(frm) {
        frm.trigger('setup_field_dependencies');
    },

    compliance_mode: function(frm) {
        frm.trigger('setup_field_dependencies');
    }
});

// ============ Global License Manager Functions ============

frappe.license_manager = {
    check_license_status: function() {
        // Global function to check license status
        return frappe.call({
            method: 'universal_workshop.workshop_management.doctype.license_manager.license_manager.validate_current_license',
            callback: function(response) {
                if (response.message && !response.message.valid) {
                    frappe.show_alert({
                        message: __('License validation failed. Please contact administrator.'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    get_active_license: function() {
        // Get the active license
        return frappe.call({
            method: 'universal_workshop.workshop_management.doctype.license_manager.license_manager.get_active_license'
        });
    }
};

// Initialize license check on page load
$(document).ready(function() {
    // Check license status every 5 minutes
    setInterval(function() {
        frappe.license_manager.check_license_status();
    }, 300000); // 5 minutes
});
