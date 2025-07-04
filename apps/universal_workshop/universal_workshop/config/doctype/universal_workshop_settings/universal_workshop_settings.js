// Universal Workshop Settings - Client-side JavaScript
// Enhanced UI for comprehensive system administration

frappe.ui.form.on('Universal Workshop Settings', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_real_time_monitoring');
        frm.trigger('setup_field_dependencies');
        frm.trigger('load_system_status');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'company_name_ar', 'description_ar', 'backup_location',
            'license_key', 'performance_alert_email'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'auto');
                frm.fields_dict[field].$input.css('text-align', 'start');
            }
        });

        // Apply RTL layout if Arabic is selected
        if (frm.doc.language === 'ar') {
            frm.page.main.addClass('rtl-layout');
            $('body').attr('dir', 'rtl');
        }
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        // Backup Management Buttons
        if (frm.doc.enable_automated_backup) {
            frm.add_custom_button(__('Create Manual Backup'), function () {
                frm.trigger('create_manual_backup');
            }, __('Backup Management'));

            frm.add_custom_button(__('View Backup History'), function () {
                frm.trigger('view_backup_history');
            }, __('Backup Management'));
        }

        // Performance Monitoring Buttons
        if (frm.doc.enable_performance_monitoring) {
            frm.add_custom_button(__('View Performance Dashboard'), function () {
                frm.trigger('show_performance_dashboard');
            }, __('Performance'));

            frm.add_custom_button(__('System Health Check'), function () {
                frm.trigger('run_system_health_check');
            }, __('Performance'));
        }

        // License Management Buttons
        if (frm.doc.license_key) {
            frm.add_custom_button(__('Refresh License Status'), function () {
                frm.trigger('refresh_license_status');
            }, __('License'));

            frm.add_custom_button(__('View License Details'), function () {
                frm.trigger('show_license_details');
            }, __('License'));
        }

        // Integration Management Buttons
        frm.add_custom_button(__('Test API Endpoints'), function () {
            frm.trigger('test_api_endpoints');
        }, __('Integration'));

        frm.add_custom_button(__('API Usage Statistics'), function () {
            frm.trigger('show_api_stats');
        }, __('Integration'));

        // Mobile Device Management Buttons
        if (frm.doc.enable_mobile_device_management) {
            frm.add_custom_button(__('View Registered Devices'), function () {
                frm.trigger('show_registered_devices');
            }, __('Mobile'));

            frm.add_custom_button(__('Device Policies'), function () {
                frm.trigger('manage_device_policies');
            }, __('Mobile'));
        }

        // System Utilities
        frm.add_custom_button(__('Reset to Defaults'), function () {
            frm.trigger('reset_to_defaults');
        }, __('System'));

        frm.add_custom_button(__('Export Settings'), function () {
            frm.trigger('export_settings');
        }, __('System'));

        frm.add_custom_button(__('Import Settings'), function () {
            frm.trigger('import_settings');
        }, __('System'));
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on checkbox states
        frm.trigger('toggle_backup_fields');
        frm.trigger('toggle_performance_fields');
        frm.trigger('toggle_license_fields');
        frm.trigger('toggle_integration_fields');
        frm.trigger('toggle_mobile_fields');
    },

    setup_real_time_monitoring: function (frm) {
        // Set up real-time performance monitoring
        if (frm.doc.enable_performance_monitoring && frm.doc.enable_real_time_monitoring) {
            frm.performance_interval = setInterval(function () {
                frm.trigger('update_performance_indicators');
            }, 30000); // Update every 30 seconds
        }
    },

    onload: function (frm) {
        // Load initial data and setup form
        frm.trigger('load_system_info');
        frm.trigger('setup_theme_preview');
    },

    load_system_status: function (frm) {
        // Load current system status indicators
        frappe.call({
            method: 'get_system_performance',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && !r.message.error) {
                    frm.trigger('display_performance_indicators', r.message);
                }
            }
        });
    },

    // ======== Theme and Appearance ========
    primary_color: function (frm) {
        frm.trigger('preview_theme_changes');
    },

    secondary_color: function (frm) {
        frm.trigger('preview_theme_changes');
    },

    theme_style: function (frm) {
        frm.trigger('preview_theme_changes');
    },

    preview_theme_changes: function (frm) {
        // Live preview of theme changes
        if (frm.doc.primary_color) {
            $(':root').css('--uw-primary-color', frm.doc.primary_color);
        }
        if (frm.doc.secondary_color) {
            $(':root').css('--uw-secondary-color', frm.doc.secondary_color);
        }
    },

    setup_theme_preview: function (frm) {
        // Add theme preview functionality
        $('.form-section[data-fieldname="theme_section"]').append(`
            <div class="theme-preview" style="margin-top: 15px;">
                <div class="card" style="padding: 15px; background: linear-gradient(135deg, var(--uw-primary-color, #1976d2), var(--uw-secondary-color, #424242)); color: white; border-radius: 8px;">
                    <h5>${__('Theme Preview')}</h5>
                    <p>${__('This is how your theme will look')}</p>
                    <button class="btn btn-light btn-sm">${__('Sample Button')}</button>
                </div>
            </div>
        `);
    },

    // ======== Backup Management ========
    enable_automated_backup: function (frm) {
        frm.trigger('toggle_backup_fields');
    },

    toggle_backup_fields: function (frm) {
        const show_backup_fields = frm.doc.enable_automated_backup;
        frm.toggle_display(['backup_frequency', 'backup_retention_days', 'backup_location',
            'enable_backup_verification', 'backup_notification_email'], show_backup_fields);
    },

    create_manual_backup: function (frm) {
        frappe.confirm(__('Create a manual backup now? This may take a few minutes.'), function () {
            frappe.show_progress(__('Creating Backup...'), 0, 100, __('Please wait...'));

            frappe.call({
                method: 'create_manual_backup',
                doc: frm.doc,
                callback: function (r) {
                    frappe.hide_progress();
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message + '<br><small>Path: ' + r.message.path + '</small>',
                            indicator: 'green'
                        });
                    }
                },
                error: function () {
                    frappe.hide_progress();
                }
            });
        });
    },

    view_backup_history: function (frm) {
        frappe.route_options = { "reference_doctype": "Universal Workshop Settings" };
        frappe.set_route("List", "File", "List");
    },

    // ======== Performance Monitoring ========
    enable_performance_monitoring: function (frm) {
        frm.trigger('toggle_performance_fields');
        if (frm.doc.enable_performance_monitoring) {
            frm.trigger('setup_real_time_monitoring');
        } else if (frm.performance_interval) {
            clearInterval(frm.performance_interval);
        }
    },

    toggle_performance_fields: function (frm) {
        const show_performance_fields = frm.doc.enable_performance_monitoring;
        frm.toggle_display(['cpu_threshold', 'memory_threshold', 'disk_threshold',
            'enable_performance_alerts', 'performance_alert_email',
            'enable_real_time_monitoring'], show_performance_fields);
    },

    show_performance_dashboard: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('Performance Dashboard'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'performance_html',
                    options: '<div id="performance-dashboard" style="min-height: 400px;">Loading...</div>'
                }
            ]
        });

        d.show();
        frm.trigger('load_performance_dashboard_data', d);
    },

    load_performance_dashboard_data: function (frm, dialog) {
        frappe.call({
            method: 'get_system_performance',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && !r.message.error) {
                    const data = r.message;
                    const dashboard_html = frm.trigger('build_performance_dashboard_html', data);
                    dialog.fields_dict.performance_html.$wrapper.html(dashboard_html);
                }
            }
        });
    },

    build_performance_dashboard_html: function (frm, data) {
        return `
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('CPU Usage')}</h5>
                            <div class="progress mb-2">
                                <div class="progress-bar ${data.cpu_usage > 80 ? 'bg-danger' : data.cpu_usage > 60 ? 'bg-warning' : 'bg-success'}" 
                                     style="width: ${data.cpu_usage}%"></div>
                            </div>
                            <p class="card-text">${data.cpu_usage}%</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('Memory Usage')}</h5>
                            <div class="progress mb-2">
                                <div class="progress-bar ${data.memory_usage > 80 ? 'bg-danger' : data.memory_usage > 60 ? 'bg-warning' : 'bg-success'}" 
                                     style="width: ${data.memory_usage}%"></div>
                            </div>
                            <p class="card-text">${data.memory_usage}% (${data.memory_available}GB free)</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('Disk Usage')}</h5>
                            <div class="progress mb-2">
                                <div class="progress-bar ${data.disk_usage > 80 ? 'bg-danger' : data.disk_usage > 60 ? 'bg-warning' : 'bg-success'}" 
                                     style="width: ${data.disk_usage}%"></div>
                            </div>
                            <p class="card-text">${data.disk_usage}% (${data.disk_free}GB free)</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">${__('DB Connections')}</h5>
                            <h2>${data.db_connections}</h2>
                            <p class="card-text">${__('Active connections')}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">${__('Network I/O')}</h5>
                            <p><strong>${__('Sent')}:</strong> ${data.network_sent} MB</p>
                            <p><strong>${__('Received')}:</strong> ${data.network_received} MB</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">${__('Last Updated')}</h5>
                            <p>${data.timestamp}</p>
                            <button class="btn btn-primary btn-sm" onclick="cur_frm.trigger('load_performance_dashboard_data')">${__('Refresh')}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    update_performance_indicators: function (frm) {
        frappe.call({
            method: 'get_system_performance',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && !r.message.error) {
                    frm.trigger('display_performance_indicators', r.message);
                }
            }
        });
    },

    display_performance_indicators: function (frm, data) {
        // Update performance indicators in the form
        const indicator_html = `
            <div class="performance-indicators" style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                <div class="row text-center">
                    <div class="col-md-3">
                        <small>${__('CPU')}</small><br>
                        <span class="badge badge-${data.cpu_usage > 80 ? 'danger' : data.cpu_usage > 60 ? 'warning' : 'success'}">${data.cpu_usage}%</span>
                    </div>
                    <div class="col-md-3">
                        <small>${__('Memory')}</small><br>
                        <span class="badge badge-${data.memory_usage > 80 ? 'danger' : data.memory_usage > 60 ? 'warning' : 'success'}">${data.memory_usage}%</span>
                    </div>
                    <div class="col-md-3">
                        <small>${__('Disk')}</small><br>
                        <span class="badge badge-${data.disk_usage > 80 ? 'danger' : data.disk_usage > 60 ? 'warning' : 'success'}">${data.disk_usage}%</span>
                    </div>
                    <div class="col-md-3">
                        <small>${__('DB Connections')}</small><br>
                        <span class="badge badge-info">${data.db_connections}</span>
                    </div>
                </div>
            </div>
        `;

        // Insert or update performance indicators
        if ($('.performance-indicators').length > 0) {
            $('.performance-indicators').replaceWith(indicator_html);
        } else {
            $('.form-section[data-fieldname="performance_section"]').append(indicator_html);
        }
    },

    run_system_health_check: function (frm) {
        frappe.show_progress(__('Running Health Check...'), 0, 100, __('Please wait...'));

        frappe.call({
            method: 'run_health_check',
            doc: frm.doc,
            callback: function (r) {
                frappe.hide_progress();
                if (r.message) {
                    frm.trigger('show_health_check_results', r.message);
                }
            },
            error: function () {
                frappe.hide_progress();
            }
        });
    },

    show_health_check_results: function (frm, results) {
        const d = new frappe.ui.Dialog({
            title: __('System Health Check Results'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'health_results',
                    options: frm.trigger('build_health_results_html', results)
                }
            ]
        });
        d.show();
    },

    build_health_results_html: function (frm, results) {
        let html = `
            <div class="health-check-results">
                <div class="alert alert-${results.overall_status === 'Healthy' ? 'success' : results.overall_status === 'Warning' ? 'warning' : 'danger'}">
                    <h5>${__('Overall Status')}: ${results.overall_status}</h5>
                    <small>${__('Last checked')}: ${results.timestamp}</small>
                </div>
        `;

        results.checks.forEach(check => {
            const status_class = check.status === 'Healthy' ? 'success' : check.status === 'Warning' ? 'warning' : 'danger';
            html += `
                <div class="card mb-2">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${check.component}</h6>
                            <span class="badge badge-${status_class}">${check.status}</span>
                        </div>
                        <small class="text-muted">${check.details}</small>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    },

    // ======== License Management ========
    license_key: function (frm) {
        frm.trigger('toggle_license_fields');
        if (frm.doc.license_key && frm.doc.license_compliance_mode) {
            frm.trigger('validate_license_format');
        }
    },

    license_compliance_mode: function (frm) {
        frm.trigger('toggle_license_fields');
    },

    toggle_license_fields: function (frm) {
        const show_license_fields = frm.doc.license_key;
        frm.toggle_display(['license_status', 'license_user_count', 'license_expiry_date',
            'license_compliance_mode'], show_license_fields);
    },

    validate_license_format: function (frm) {
        if (frm.doc.license_key) {
            const pattern = /^UW-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;
            if (!pattern.test(frm.doc.license_key)) {
                frappe.msgprint({
                    message: __('Invalid license key format. Expected format: UW-XXXX-XXXX-XXXX-XXXX'),
                    indicator: 'orange'
                });
            }
        }
    },

    refresh_license_status: function (frm) {
        frappe.show_progress(__('Validating License...'), 0, 100, __('Please wait...'));

        frappe.call({
            method: 'refresh_license_status',
            doc: frm.doc,
            callback: function (r) {
                frappe.hide_progress();
                if (r.message) {
                    if (r.message.valid) {
                        frappe.show_alert({
                            message: __('License validated successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            message: __('License validation failed: ') + r.message.error,
                            indicator: 'red'
                        });
                    }
                }
            },
            error: function () {
                frappe.hide_progress();
            }
        });
    },

    show_license_details: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('License Details'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'license_key',
                    label: __('License Key'),
                    default: frm.doc.license_key,
                    read_only: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'license_status',
                    label: __('Status'),
                    default: frm.doc.license_status,
                    read_only: 1
                },
                {
                    fieldtype: 'Int',
                    fieldname: 'license_user_count',
                    label: __('Licensed Users'),
                    default: frm.doc.license_user_count,
                    read_only: 1
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'license_expiry_date',
                    label: __('Expiry Date'),
                    default: frm.doc.license_expiry_date,
                    read_only: 1
                }
            ]
        });
        d.show();
    },

    // ======== Integration Management ========
    test_api_endpoints: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('Test API Endpoints'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'endpoint_url',
                    label: __('Endpoint URL'),
                    reqd: 1,
                    default: 'https://httpbin.org/get'
                }
            ],
            primary_action_label: __('Test'),
            primary_action: function () {
                const values = d.get_values();
                frappe.call({
                    method: 'test_api_endpoint',
                    doc: frm.doc,
                    args: {
                        endpoint_url: values.endpoint_url
                    },
                    callback: function (r) {
                        if (r.message) {
                            const status_color = r.message.status === 'success' ? 'green' : 'red';
                            frappe.msgprint({
                                message: `<strong>Status:</strong> ${r.message.status}<br>
                                         <strong>Response Time:</strong> ${r.message.response_time}s<br>
                                         <strong>Message:</strong> ${r.message.message}`,
                                indicator: status_color
                            });
                        }
                    }
                });
                d.hide();
            }
        });
        d.show();
    },

    show_api_stats: function (frm) {
        frappe.call({
            method: 'get_api_usage_stats',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && !r.message.error) {
                    const stats = r.message;
                    frappe.msgprint({
                        title: __('API Usage Statistics'),
                        message: `
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>${__('Total Requests')}:</strong> ${stats.total_requests}</p>
                                    <p><strong>${__('Requests Today')}:</strong> ${stats.requests_today}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>${__('Average Response Time')}:</strong> ${stats.avg_response_time}</p>
                                    <p><strong>${__('Success Rate')}:</strong> ${stats.success_rate}</p>
                                </div>
                            </div>
                            <p><strong>${__('Rate Limit Status')}:</strong> <span class="badge badge-success">${stats.rate_limit_status}</span></p>
                        `,
                        indicator: 'blue'
                    });
                }
            }
        });
    },

    // ======== Mobile Device Management ========
    enable_mobile_device_management: function (frm) {
        frm.trigger('toggle_mobile_fields');
    },

    toggle_mobile_fields: function (frm) {
        const show_mobile_fields = frm.doc.enable_mobile_device_management;
        frm.toggle_display(['mobile_policy_enforcement', 'mobile_remote_wipe',
            'mobile_app_restrictions'], show_mobile_fields);
    },

    show_registered_devices: function (frm) {
        frappe.call({
            method: 'get_registered_devices',
            doc: frm.doc,
            callback: function (r) {
                if (r.message && r.message.devices) {
                    frm.trigger('display_devices_list', r.message.devices);
                }
            }
        });
    },

    display_devices_list: function (frm, devices) {
        const d = new frappe.ui.Dialog({
            title: __('Registered Mobile Devices'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'devices_html',
                    options: frm.trigger('build_devices_list_html', devices)
                }
            ]
        });
        d.show();
    },

    build_devices_list_html: function (frm, devices) {
        if (!devices || devices.length === 0) {
            return '<p class="text-muted">' + __('No devices registered') + '</p>';
        }

        let html = '<div class="table-responsive"><table class="table table-striped">';
        html += `<thead><tr>
            <th>${__('Device Name')}</th>
            <th>${__('Platform')}</th>
            <th>${__('User')}</th>
            <th>${__('Registration Date')}</th>
            <th>${__('Status')}</th>
        </tr></thead><tbody>`;

        devices.forEach(device => {
            const status_class = device.status === 'Active' ? 'success' : 'secondary';
            html += `<tr>
                <td>${device.device_name}</td>
                <td>${device.platform}</td>
                <td>${device.user}</td>
                <td>${device.registration_date}</td>
                <td><span class="badge badge-${status_class}">${device.status}</span></td>
            </tr>`;
        });

        html += '</tbody></table></div>';
        return html;
    },

    manage_device_policies: function (frm) {
        frappe.msgprint({
            title: __('Device Policies'),
            message: __('Device policy management will be available in the next version'),
            indicator: 'blue'
        });
    },

    // ======== System Utilities ========
    reset_to_defaults: function (frm) {
        frappe.confirm(__('Reset all settings to default values? This action cannot be undone.'), function () {
            frappe.call({
                method: 'reset_to_defaults',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        });
    },

    export_settings: function (frm) {
        frappe.call({
            method: 'export_settings',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    // Create download link
                    const element = document.createElement('a');
                    element.setAttribute('href', 'data:application/json;charset=utf-8,' +
                        encodeURIComponent(r.message.content));
                    element.setAttribute('download', r.message.file_name);
                    element.style.display = 'none';
                    document.body.appendChild(element);
                    element.click();
                    document.body.removeChild(element);

                    frappe.show_alert({
                        message: __('Settings exported successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    import_settings: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('Import Settings'),
            fields: [
                {
                    fieldtype: 'Attach',
                    fieldname: 'settings_file',
                    label: __('Settings File'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Import'),
            primary_action: function () {
                const values = d.get_values();
                if (values.settings_file) {
                    // Read the file and import settings
                    frappe.call({
                        method: 'frappe.client.get_file',
                        args: {
                            'file_url': values.settings_file
                        },
                        callback: function (r) {
                            if (r.message) {
                                frappe.call({
                                    method: 'import_settings',
                                    doc: frm.doc,
                                    args: {
                                        settings_json: r.message
                                    },
                                    callback: function (response) {
                                        if (response.message && response.message.status === 'success') {
                                            frappe.show_alert({
                                                message: response.message.message,
                                                indicator: 'green'
                                            });
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        }
                    });
                }
                d.hide();
            }
        });
        d.show();
    },

    load_system_info: function (frm) {
        // Load basic system information
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'System Settings',
                fields: ['language', 'time_zone', 'country']
            },
            callback: function (r) {
                if (r.message && r.message[0]) {
                    const system_settings = r.message[0];
                    if (!frm.doc.language) {
                        frm.set_value('language', system_settings.language);
                    }
                    if (!frm.doc.time_zone) {
                        frm.set_value('time_zone', system_settings.time_zone);
                    }
                }
            }
        });
    }
});

// Clean up intervals when form is closed
$(document).on('page-change', function () {
    if (cur_frm && cur_frm.performance_interval) {
        clearInterval(cur_frm.performance_interval);
    }
}); 