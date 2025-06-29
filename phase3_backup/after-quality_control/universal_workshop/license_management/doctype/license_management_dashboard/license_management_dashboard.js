// License Management Dashboard JavaScript Controller
// Provides interactive administrative interface for license management
// Supports Arabic RTL layout and dual language functionality

frappe.ui.form.on('License Management Dashboard', {
    refresh: function (frm) {
        // Setup dashboard interface
        frm.trigger('setup_dashboard_interface');
        frm.trigger('setup_arabic_support');
        frm.trigger('setup_action_buttons');
        frm.trigger('auto_refresh_dashboard');
    },

    setup_dashboard_interface: function (frm) {
        // Configure dashboard layout and styling
        frm.page.main.addClass('license-management-dashboard');

        // Add custom CSS for dashboard styling
        if (!$('.dashboard-custom-styles').length) {
            $('<style class="dashboard-custom-styles">')
                .text(`
                    .license-management-dashboard .form-section {
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 15px;
                        margin-bottom: 20px;
                    }
                    .license-management-dashboard .form-section .section-head {
                        background: #007bff;
                        color: white;
                        padding: 10px 15px;
                        margin: -15px -15px 15px -15px;
                        border-radius: 8px 8px 0 0;
                        font-weight: bold;
                    }
                    .dashboard-stat-card {
                        background: white;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                        padding: 15px;
                        text-align: center;
                        margin-bottom: 10px;
                    }
                    .dashboard-stat-number {
                        font-size: 2em;
                        font-weight: bold;
                        color: #007bff;
                    }
                    .dashboard-stat-label {
                        color: #6c757d;
                        font-size: 0.9em;
                    }
                    .system-status-healthy { color: #28a745; }
                    .system-status-warning { color: #ffc107; }
                    .system-status-critical { color: #dc3545; }
                    .system-status-maintenance { color: #6c757d; }
                `)
                .appendTo('head');
        }
    },

    setup_arabic_support: function (frm) {
        // Configure Arabic RTL support
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Set RTL direction for Arabic fields
            ['dashboard_title_ar'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                }
            });
        }
    },

    setup_action_buttons: function (frm) {
        // Clear existing custom buttons
        frm.page.clear_inner_toolbar();

        // Refresh Dashboard Button
        frm.add_custom_button(__('Refresh Dashboard'), function () {
            frm.trigger('refresh_dashboard_data');
        }, __('Actions'));

        // Issue New License Button
        frm.add_custom_button(__('Issue New License'), function () {
            frm.trigger('show_license_issuance_dialog');
        }, __('License Management'));

        // Bulk Operations Button
        frm.add_custom_button(__('Bulk Renewal'), function () {
            frm.trigger('show_bulk_renewal_dialog');
        }, __('License Management'));

        // Export Audit Logs Button
        frm.add_custom_button(__('Export Audit Logs'), function () {
            frm.trigger('show_export_dialog');
        }, __('Reports'));

        // System Maintenance Button
        frm.add_custom_button(__('System Maintenance'), function () {
            frm.trigger('show_maintenance_dialog');
        }, __('System'));

        // Auto-refresh toggle
        frm.add_custom_button(__('Auto-refresh: ON'), function () {
            frm.trigger('toggle_auto_refresh');
        }, __('Settings'));
    },

    auto_refresh_dashboard: function (frm) {
        // Setup automatic dashboard refresh every 5 minutes
        if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
        }

        frm.auto_refresh_enabled = true;
        frm.auto_refresh_interval = setInterval(function () {
            if (frm.auto_refresh_enabled && !frm.is_dirty()) {
                frm.trigger('refresh_dashboard_data');
            }
        }, 300000); // 5 minutes
    },

    refresh_dashboard_data: function (frm) {
        // Refresh dashboard data from server
        frappe.show_alert({
            message: __('Refreshing dashboard data...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'universal_workshop.license_management.doctype.license_management_dashboard.license_management_dashboard.get_dashboard_data',
            callback: function (r) {
                if (r.message && r.message.success) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Dashboard refreshed successfully'),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('Failed to refresh dashboard'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    show_license_issuance_dialog: function (frm) {
        // Show license issuance dialog
        let dialog = new frappe.ui.Dialog({
            title: __('Issue New License'),
            fields: [
                {
                    label: __('Business Name'),
                    fieldname: 'business_name',
                    fieldtype: 'Data',
                    reqd: 1
                },
                {
                    label: __('Arabic Business Name'),
                    fieldname: 'business_name_ar',
                    fieldtype: 'Data',
                    reqd: 1
                },
                {
                    label: __('License Type'),
                    fieldname: 'license_type',
                    fieldtype: 'Select',
                    options: 'Demo\nTrial\nStandard\nProfessional\nEnterprise',
                    default: 'Demo',
                    reqd: 1
                },
                {
                    label: __('Contact Email'),
                    fieldname: 'contact_email',
                    fieldtype: 'Data',
                    reqd: 1
                },
                {
                    label: __('Business License Number'),
                    fieldname: 'business_license',
                    fieldtype: 'Data',
                    reqd: 1,
                    description: __('7-digit Oman business license number')
                },
                {
                    label: __('Duration (Days)'),
                    fieldname: 'duration_days',
                    fieldtype: 'Int',
                    default: 30,
                    reqd: 1
                }
            ],
            primary_action_label: __('Issue License'),
            primary_action(values) {
                frappe.call({
                    method: 'universal_workshop.license_management.doctype.license_management_dashboard.license_management_dashboard.issue_new_license_from_dashboard',
                    args: {
                        license_request: values
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('License issued successfully: {0}', [r.message.license_id]),
                                indicator: 'green'
                            });
                            dialog.hide();
                            frm.trigger('refresh_dashboard_data');
                        } else {
                            frappe.msgprint({
                                title: __('License Issuance Failed'),
                                message: r.message.error || __('Unknown error occurred'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        });

        // Setup Arabic field direction
        dialog.show();
        if (frappe.boot.lang === 'ar') {
            dialog.$wrapper.find('[data-fieldname="business_name_ar"] input').attr('dir', 'rtl');
        }
    },

    show_bulk_renewal_dialog: function (frm) {
        // Show bulk renewal dialog
        let dialog = new frappe.ui.Dialog({
            title: __('Bulk License Renewal'),
            fields: [
                {
                    label: __('Renewal Criteria'),
                    fieldname: 'criteria_section',
                    fieldtype: 'Section Break'
                },
                {
                    label: __('License Status'),
                    fieldname: 'license_status',
                    fieldtype: 'Select',
                    options: 'Active\nExpiring Soon\nExpired',
                    default: 'Expiring Soon'
                },
                {
                    label: __('Extension Duration (Days)'),
                    fieldname: 'duration_days',
                    fieldtype: 'Int',
                    default: 90,
                    reqd: 1
                },
                {
                    label: __('Renewal Reason'),
                    fieldname: 'renewal_reason',
                    fieldtype: 'Text',
                    default: 'Bulk renewal operation'
                }
            ],
            primary_action_label: __('Start Bulk Renewal'),
            primary_action(values) {
                frappe.call({
                    method: 'universal_workshop.license_management.doctype.license_management_dashboard.license_management_dashboard.bulk_license_renewal',
                    args: {
                        renewal_criteria: values
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Bulk renewal completed: {0} licenses processed', [r.message.total_processed]),
                                indicator: 'green'
                            });
                            dialog.hide();
                            frm.trigger('refresh_dashboard_data');
                        } else {
                            frappe.msgprint({
                                title: __('Bulk Renewal Failed'),
                                message: r.message.error || __('Unknown error occurred'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    show_export_dialog: function (frm) {
        // Show audit log export dialog
        let dialog = new frappe.ui.Dialog({
            title: __('Export Audit Logs'),
            fields: [
                {
                    label: __('Export Criteria'),
                    fieldname: 'criteria_section',
                    fieldtype: 'Section Break'
                },
                {
                    label: __('Start Date'),
                    fieldname: 'start_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.add_days(frappe.datetime.get_today(), -30)
                },
                {
                    label: __('End Date'),
                    fieldname: 'end_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.get_today()
                },
                {
                    label: __('Severity Filter'),
                    fieldname: 'severity',
                    fieldtype: 'Select',
                    options: '\nLow\nMedium\nHigh\nCritical'
                },
                {
                    label: __('Maximum Records'),
                    fieldname: 'limit',
                    fieldtype: 'Int',
                    default: 1000
                }
            ],
            primary_action_label: __('Export Logs'),
            primary_action(values) {
                frappe.call({
                    method: 'universal_workshop.license_management.doctype.license_management_dashboard.license_management_dashboard.export_audit_logs',
                    args: {
                        export_criteria: values
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            // Create downloadable file
                            let data = r.message.audit_logs;
                            let csv_content = "data:text/csv;charset=utf-8,";

                            // Add headers
                            csv_content += "Event Type,Workshop,Timestamp,Severity,Description\n";

                            // Add data rows
                            data.forEach(function (row) {
                                csv_content += `"${row.event_type}","${row.workshop_id || ''}","${row.timestamp}","${row.severity}","${row.description || ''}"\n`;
                            });

                            // Create download link
                            let encoded_uri = encodeURI(csv_content);
                            let link = document.createElement("a");
                            link.setAttribute("href", encoded_uri);
                            link.setAttribute("download", `audit_logs_${frappe.datetime.get_today()}.csv`);
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);

                            frappe.show_alert({
                                message: __('Audit logs exported: {0} records', [r.message.total_records]),
                                indicator: 'green'
                            });
                            dialog.hide();
                        } else {
                            frappe.msgprint({
                                title: __('Export Failed'),
                                message: r.message.error || __('Unknown error occurred'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    show_maintenance_dialog: function (frm) {
        // Show system maintenance dialog
        let dialog = new frappe.ui.Dialog({
            title: __('System Maintenance'),
            fields: [
                {
                    label: __('Maintenance Operations'),
                    fieldname: 'operations_section',
                    fieldtype: 'Section Break'
                },
                {
                    label: __('Operation Type'),
                    fieldname: 'operation_type',
                    fieldtype: 'Select',
                    options: 'cleanup_expired_tokens\nrefresh_hardware_fingerprints\nvalidate_all_licenses',
                    reqd: 1
                },
                {
                    label: __('Confirm Operation'),
                    fieldname: 'confirm',
                    fieldtype: 'Check',
                    description: __('I understand this operation may affect system performance')
                }
            ],
            primary_action_label: __('Execute Maintenance'),
            primary_action(values) {
                if (!values.confirm) {
                    frappe.msgprint(__('Please confirm the operation before proceeding'));
                    return;
                }

                frappe.call({
                    method: 'universal_workshop.license_management.doctype.license_management_dashboard.license_management_dashboard.system_maintenance_operations',
                    args: {
                        operation_type: values.operation_type
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Maintenance operation completed successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                            frm.trigger('refresh_dashboard_data');
                        } else {
                            frappe.msgprint({
                                title: __('Maintenance Failed'),
                                message: r.message.error || __('Unknown error occurred'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    toggle_auto_refresh: function (frm) {
        // Toggle auto-refresh functionality
        frm.auto_refresh_enabled = !frm.auto_refresh_enabled;

        let button_text = frm.auto_refresh_enabled ?
            __('Auto-refresh: ON') : __('Auto-refresh: OFF');

        // Update button text
        frm.page.inner_toolbar.find('[data-label="Auto-refresh: ON"], [data-label="Auto-refresh: OFF"]')
            .attr('data-label', button_text)
            .text(button_text);

        frappe.show_alert({
            message: frm.auto_refresh_enabled ?
                __('Auto-refresh enabled') : __('Auto-refresh disabled'),
            indicator: frm.auto_refresh_enabled ? 'green' : 'orange'
        });
    }
});

// Custom field events for enhanced interactivity

frappe.ui.form.on('License Management Dashboard', 'issue_new_license', function (frm) {
    frm.trigger('show_license_issuance_dialog');
});

frappe.ui.form.on('License Management Dashboard', 'bulk_renewal', function (frm) {
    frm.trigger('show_bulk_renewal_dialog');
});

frappe.ui.form.on('License Management Dashboard', 'export_audit_logs', function (frm) {
    frm.trigger('show_export_dialog');
});

frappe.ui.form.on('License Management Dashboard', 'system_maintenance', function (frm) {
    frm.trigger('show_maintenance_dialog');
});

// Cleanup on form destroy
frappe.ui.form.on('License Management Dashboard', 'onload', function (frm) {
    // Cleanup interval on page unload
    $(window).on('beforeunload', function () {
        if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
        }
    });
}); 