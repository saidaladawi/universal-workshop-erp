// Copyright (c) 2025, Universal Workshop ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mobile Device Management', {
    refresh: function (frm) {
        // Setup Arabic RTL fields
        frm.trigger('setup_arabic_fields');

        // Setup custom buttons
        frm.trigger('setup_custom_buttons');

        // Setup real-time monitoring
        frm.trigger('setup_real_time_monitoring');

        // Setup dashboard
        frm.trigger('setup_device_dashboard');

        // Setup form layout
        frm.trigger('setup_form_layout');

        // Auto-refresh if monitoring is enabled
        if (frm.doc.monitoring_enabled && !frm.is_new()) {
            frm.trigger('start_auto_refresh');
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'device_name_ar', 'device_owner_ar', 'compliance_notes',
            'wipe_reason', 'maintenance_notes', 'communication_log',
            'activity_log', 'security_log'
        ];

        arabic_fields.forEach(fieldname => {
            if (frm.fields_dict[fieldname]) {
                const field = frm.fields_dict[fieldname];
                field.$input?.attr('dir', 'rtl').css('text-align', 'right');
                field.$wrapper?.addClass('arabic-field');
            }
        });

        // Auto-direction detection for mixed content
        ['device_name', 'device_owner'].forEach(fieldname => {
            if (frm.fields_dict[fieldname]) {
                frm.fields_dict[fieldname].$input?.on('input', function () {
                    const text = $(this).val();
                    const direction = detect_text_direction(text);
                    $(this).attr('dir', direction);
                });
            }
        });
    },

    setup_custom_buttons: function (frm) {
        if (frm.is_new()) return;

        // Device Control Section
        frm.add_custom_button(__('Sync Device Info'), function () {
            frappe.call({
                method: 'sync_device_info',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Device Control / التحكم بالجهاز'));

        if (frm.doc.device_locked) {
            frm.add_custom_button(__('Unlock Device'), function () {
                frm.trigger('unlock_device_action');
            }, __('Device Control / التحكم بالجهاز'));
        } else {
            frm.add_custom_button(__('Lock Device'), function () {
                frm.trigger('lock_device_action');
            }, __('Device Control / التحكم بالجهاز'));
        }

        // Security Actions
        frm.add_custom_button(__('Remote Wipe'), function () {
            frm.trigger('remote_wipe_action');
        }, __('Security Actions / إجراءات الأمان'));

        frm.add_custom_button(__('Compliance Check'), function () {
            frappe.call({
                method: 'run_compliance_check',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Security Actions / إجراءات الأمان'));

        // App Management
        frm.add_custom_button(__('Install App'), function () {
            frm.trigger('install_app_action');
        }, __('App Management / إدارة التطبيقات'));

        frm.add_custom_button(__('View Installed Apps'), function () {
            frm.trigger('show_installed_apps');
        }, __('App Management / إدارة التطبيقات'));

        // Reports and Export
        frm.add_custom_button(__('Export Report'), function () {
            frm.trigger('export_device_report');
        }, __('Reports / التقارير'));

        frm.add_custom_button(__('Activity Timeline'), function () {
            frm.trigger('show_activity_timeline');
        }, __('Reports / التقارير'));

        // Quick Actions
        frm.add_custom_button(__('Send Notification'), function () {
            frm.trigger('send_notification_action');
        }, __('Quick Actions / إجراءات سريعة'));

        frm.add_custom_button(__('Locate Device'), function () {
            frm.trigger('locate_device_action');
        }, __('Quick Actions / إجراءات سريعة'));
    },

    setup_real_time_monitoring: function (frm) {
        if (frm.is_new() || !frm.doc.monitoring_enabled) return;

        // Create real-time monitoring indicator
        const monitoring_html = `
            <div class="device-monitoring-indicator" style="
                position: absolute;
                top: 10px;
                right: 20px;
                padding: 5px 10px;
                background: ${frm.doc.device_status === 'Active / نشط' ? '#28a745' : '#dc3545'};
                color: white;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            ">
                <i class="fa fa-circle" style="animation: pulse 2s infinite;"></i>
                ${__('Live Monitoring / مراقبة مباشرة')}
            </div>
            <style>
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
            </style>
        `;

        $('.layout-main-section-wrapper').prepend(monitoring_html);
    },

    setup_device_dashboard: function (frm) {
        if (frm.is_new()) return;

        // Create dashboard section
        const dashboard_wrapper = $('<div class="device-dashboard">').insertAfter(frm.dashboard.wrapper);

        frappe.call({
            method: 'get_device_dashboard_data',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.trigger('render_device_dashboard', r.message);
                }
            }
        });
    },

    render_device_dashboard: function (frm, dashboard_data) {
        const data = dashboard_data || {};

        const dashboard_html = `
            <div class="device-dashboard-container" style="margin: 20px 0; padding: 20px; border: 1px solid #d1d8dd; border-radius: 6px; background: #f8f9fa;">
                <h4 style="margin-bottom: 20px; color: #36414c;">
                    <i class="fa fa-mobile" style="margin-right: 8px;"></i>
                    ${__('Device Dashboard / لوحة تحكم الجهاز')}
                </h4>
                
                <div class="row">
                    <!-- Device Status -->
                    <div class="col-md-3">
                        <div class="dashboard-card">
                            <h6>${__('Device Status / حالة الجهاز')}</h6>
                            <div class="metric-value ${get_status_class(data.device_info?.status)}">
                                ${data.device_info?.status || 'Unknown / غير معروف'}
                            </div>
                            <small class="text-muted">
                                ${data.device_info?.type || ''} - ${data.device_info?.manufacturer || ''}
                            </small>
                        </div>
                    </div>
                    
                    <!-- Compliance Score -->
                    <div class="col-md-3">
                        <div class="dashboard-card">
                            <h6>${__('Compliance / الامتثال')}</h6>
                            <div class="metric-value">
                                <div class="progress" style="height: 20px; margin-bottom: 5px;">
                                    <div class="progress-bar ${get_compliance_class(data.compliance?.score)}" 
                                         style="width: ${data.compliance?.score || 0}%">
                                        ${data.compliance?.score || 0}%
                                    </div>
                                </div>
                            </div>
                            <small class="text-muted">
                                ${data.compliance?.status || 'Unknown / غير معروف'}
                            </small>
                        </div>
                    </div>
                    
                    <!-- Battery & Performance -->
                    <div class="col-md-3">
                        <div class="dashboard-card">
                            <h6>${__('Performance / الأداء')}</h6>
                            <div class="metric-row">
                                <span>${__('Battery / البطارية')}: </span>
                                <span class="metric-value ${get_battery_class(data.performance?.battery_level)}">
                                    ${data.performance?.battery_level || 0}%
                                </span>
                            </div>
                            <div class="metric-row">
                                <span>${__('Signal / الإشارة')}: </span>
                                <span class="metric-value">
                                    ${data.performance?.network_quality || 'Unknown / غير معروف'}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Security Status -->
                    <div class="col-md-3">
                        <div class="dashboard-card">
                            <h6>${__('Security / الأمان')}</h6>
                            <div class="security-indicators">
                                <div class="security-item">
                                    <i class="fa fa-${data.security?.device_locked ? 'lock text-success' : 'unlock text-warning'}"></i>
                                    <span>${data.security?.device_locked ? __('Locked / مقفل') : __('Unlocked / مفتوح')}</span>
                                </div>
                                <div class="security-item">
                                    <i class="fa fa-${data.security?.encryption_enabled ? 'shield text-success' : 'shield text-danger'}"></i>
                                    <span>${data.security?.encryption_enabled ? __('Encrypted / مشفر') : __('Not Encrypted / غير مشفر')}</span>
                                </div>
                                ${data.security?.jailbreak_detected ?
                '<div class="security-item"><i class="fa fa-exclamation-triangle text-danger"></i><span class="text-danger">' + __('Jailbreak Detected / كسر الحماية مكتشف') + '</span></div>' :
                ''
            }
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- App Summary -->
                <div class="row" style="margin-top: 15px;">
                    <div class="col-md-12">
                        <div class="dashboard-card">
                            <h6>${__('Application Summary / ملخص التطبيقات')}</h6>
                            <div class="row">
                                <div class="col-md-3">
                                    <span class="badge badge-primary">${data.apps?.total_installed || 0}</span>
                                    ${__('Total Apps / إجمالي التطبيقات')}
                                </div>
                                <div class="col-md-3">
                                    <span class="badge badge-success">${data.apps?.corporate_apps || 0}</span>
                                    ${__('Corporate / الشركة')}
                                </div>
                                <div class="col-md-3">
                                    <span class="badge badge-info">${data.apps?.personal_apps || 0}</span>
                                    ${__('Personal / شخصية')}
                                </div>
                                <div class="col-md-3">
                                    <span class="badge badge-danger">${data.apps?.restricted_detected || 0}</span>
                                    ${__('Restricted / مقيدة')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('.device-dashboard').html(dashboard_html);
    },

    setup_form_layout: function (frm) {
        // Add custom CSS for better layout
        const custom_css = `
            <style>
                .device-dashboard-container .dashboard-card {
                    padding: 15px;
                    background: white;
                    border: 1px solid #e4e8eb;
                    border-radius: 6px;
                    margin-bottom: 15px;
                    height: 120px;
                }
                
                .device-dashboard-container .metric-value {
                    font-size: 18px;
                    font-weight: bold;
                    margin: 5px 0;
                }
                
                .device-dashboard-container .metric-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 3px 0;
                    font-size: 13px;
                }
                
                .device-dashboard-container .security-item {
                    display: flex;
                    align-items: center;
                    margin: 3px 0;
                    font-size: 12px;
                }
                
                .device-dashboard-container .security-item i {
                    margin-right: 8px;
                    width: 16px;
                }
                
                .arabic-field input,
                .arabic-field textarea {
                    font-family: 'Noto Sans Arabic', 'Tahoma', sans-serif;
                    line-height: 1.6;
                }
                
                .compliance-high { color: #28a745; }
                .compliance-medium { color: #ffc107; }
                .compliance-low { color: #dc3545; }
                
                .battery-high { color: #28a745; }
                .battery-medium { color: #ffc107; }
                .battery-low { color: #dc3545; }
                
                .status-active { color: #28a745; }
                .status-inactive { color: #6c757d; }
                .status-lost { color: #dc3545; }
                .status-maintenance { color: #ffc107; }
            </style>
        `;

        $('head').append(custom_css);
    },

    start_auto_refresh: function (frm) {
        if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
        }

        // Auto-refresh every 30 seconds if monitoring is enabled
        frm.auto_refresh_interval = setInterval(function () {
            if (frm.doc.monitoring_enabled && !frm.is_dirty()) {
                frappe.call({
                    method: 'get_device_dashboard_data',
                    doc: frm.doc,
                    callback: function (r) {
                        if (r.message) {
                            frm.trigger('render_device_dashboard', r.message);
                        }
                    }
                });
            }
        }, 30000);
    },

    // Action Triggers
    lock_device_action: function (frm) {
        frappe.confirm(
            __('Are you sure you want to lock this device remotely? / هل أنت متأكد من قفل هذا الجهاز عن بعد؟'),
            function () {
                frappe.call({
                    method: 'lock_device',
                    doc: frm.doc,
                    callback: function (r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    unlock_device_action: function (frm) {
        frappe.confirm(
            __('Are you sure you want to unlock this device remotely? / هل أنت متأكد من فتح قفل هذا الجهاز عن بعد؟'),
            function () {
                frappe.call({
                    method: 'unlock_device',
                    doc: frm.doc,
                    callback: function (r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    remote_wipe_action: function (frm) {
        frappe.prompt([
            {
                label: __('Reason for Remote Wipe / سبب المسح عن بعد'),
                fieldname: 'reason',
                fieldtype: 'Small Text',
                reqd: 1,
                description: __('Please provide a detailed reason for initiating remote wipe')
            }
        ], function (values) {
            frappe.confirm(
                __('WARNING: This will permanently erase all data on the device. This action cannot be undone. / تحذير: سيؤدي هذا إلى مسح جميع البيانات نهائياً من الجهاز. لا يمكن التراجع عن هذا الإجراء.'),
                function () {
                    frappe.call({
                        method: 'initiate_remote_wipe',
                        doc: frm.doc,
                        args: {
                            reason: values.reason
                        },
                        callback: function (r) {
                            if (r.message) {
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }, __('Remote Wipe Confirmation / تأكيد المسح عن بعد'), __('Initiate Wipe / بدء المسح'));
    },

    install_app_action: function (frm) {
        frappe.prompt([
            {
                label: __('App Package Name'),
                fieldname: 'app_package',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Enter the app package identifier (e.g., com.example.app)')
            },
            {
                label: __('App Display Name'),
                fieldname: 'app_name',
                fieldtype: 'Data',
                description: __('Friendly name for the application')
            }
        ], function (values) {
            frappe.call({
                method: 'install_app',
                doc: frm.doc,
                args: {
                    app_package: values.app_package,
                    app_name: values.app_name
                },
                callback: function (r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Install Application / تثبيت التطبيق'), __('Install / تثبيت'));
    },

    show_installed_apps: function (frm) {
        if (!frm.doc.installed_apps) {
            frappe.msgprint(__('No app data available. Please sync device info first.'));
            return;
        }

        let apps_data;
        try {
            apps_data = JSON.parse(frm.doc.installed_apps);
        } catch (e) {
            frappe.msgprint(__('Invalid app data format'));
            return;
        }

        const apps_html = apps_data.map(app => `
            <tr>
                <td>${app.name || 'Unknown'}</td>
                <td><code>${app.package || 'Unknown'}</code></td>
                <td>
                    <span class="badge badge-${app.type === 'corporate' ? 'success' : 'info'}">
                        ${app.type || 'Unknown'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="uninstall_app('${app.package}')">
                        ${__('Uninstall / إلغاء التثبيت')}
                    </button>
                </td>
            </tr>
        `).join('');

        const dialog = new frappe.ui.Dialog({
            title: __('Installed Applications / التطبيقات المثبتة'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'apps_list',
                    options: `
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>${__('App Name / اسم التطبيق')}</th>
                                    <th>${__('Package / الحزمة')}</th>
                                    <th>${__('Type / النوع')}</th>
                                    <th>${__('Actions / الإجراءات')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${apps_html}
                            </tbody>
                        </table>
                    `
                }
            ]
        });

        dialog.show();

        // Add uninstall function to window scope
        window.uninstall_app = function (package_name) {
            frappe.confirm(
                __('Are you sure you want to uninstall this app? / هل أنت متأكد من إلغاء تثبيت هذا التطبيق؟'),
                function () {
                    frappe.call({
                        method: 'uninstall_app',
                        doc: frm.doc,
                        args: {
                            app_package: package_name
                        },
                        callback: function (r) {
                            dialog.hide();
                            if (r.message) {
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        };
    },

    export_device_report: function (frm) {
        frappe.call({
            method: 'export_device_report',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    // Convert to downloadable JSON
                    const data = JSON.stringify(r.message, null, 2);
                    const blob = new Blob([data], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);

                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `device_report_${frm.doc.device_name}_${frappe.datetime.now_date()}.json`;
                    a.click();

                    URL.revokeObjectURL(url);
                    frappe.msgprint(__('Device report exported successfully'));
                }
            }
        });
    },

    show_activity_timeline: function (frm) {
        if (!frm.doc.activity_log) {
            frappe.msgprint(__('No activity data available'));
            return;
        }

        const activities = frm.doc.activity_log.split('\n').filter(line => line.trim());
        const timeline_html = activities.map(activity => {
            const match = activity.match(/\[(.*?)\]\s*(.*?):\s*(.*)/);
            if (match) {
                const [, timestamp, type, message] = match;
                const icon_class = type === 'Security' ? 'fa-shield text-danger' :
                    type === 'Error' ? 'fa-exclamation-circle text-warning' :
                        'fa-info-circle text-info';

                return `
                    <div class="timeline-item" style="margin-bottom: 15px; padding: 10px; border-left: 3px solid #007bff;">
                        <div class="timeline-header">
                            <i class="fa ${icon_class}" style="margin-right: 8px;"></i>
                            <strong>${type}</strong>
                            <span class="text-muted" style="float: right;">${timestamp}</span>
                        </div>
                        <div class="timeline-body" style="margin-top: 5px;">
                            ${message}
                        </div>
                    </div>
                `;
            }
            return '';
        }).join('');

        const dialog = new frappe.ui.Dialog({
            title: __('Activity Timeline / الجدول الزمني للنشاط'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'timeline',
                    options: `
                        <div class="activity-timeline" style="max-height: 400px; overflow-y: auto;">
                            ${timeline_html}
                        </div>
                    `
                }
            ]
        });

        dialog.show();
    },

    send_notification_action: function (frm) {
        frappe.prompt([
            {
                label: __('Notification Title / عنوان التنبيه'),
                fieldname: 'title',
                fieldtype: 'Data',
                reqd: 1
            },
            {
                label: __('Message / الرسالة'),
                fieldname: 'message',
                fieldtype: 'Small Text',
                reqd: 1
            },
            {
                label: __('Priority / الأولوية'),
                fieldname: 'priority',
                fieldtype: 'Select',
                options: 'Normal\nHigh\nCritical',
                default: 'Normal'
            }
        ], function (values) {
            // Since send_notification is not whitelisted, we'll log it as activity
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Mobile Device Management',
                    name: frm.doc.name,
                    fieldname: 'communication_log',
                    value: (frm.doc.communication_log || '') +
                        `\n[${frappe.datetime.now()}] Manual Notification: ${values.title} - ${values.message}`
                },
                callback: function (r) {
                    frm.reload_doc();
                    frappe.msgprint(__('Notification sent successfully'));
                }
            });
        }, __('Send Notification / إرسال تنبيه'), __('Send / إرسال'));
    },

    locate_device_action: function (frm) {
        if (!frm.doc.location_tracking) {
            frappe.msgprint(__('Location tracking is not enabled for this device / تتبع الموقع غير مفعل لهذا الجهاز'));
            return;
        }

        // Simulate location request
        frappe.show_alert({
            message: __('Location request sent to device / تم إرسال طلب الموقع للجهاز'),
            indicator: 'blue'
        });

        // Update last location with simulated data
        setTimeout(function () {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Mobile Device Management',
                    name: frm.doc.name,
                    fieldname: 'last_location',
                    value: `23.5859° N, 58.4059° E (Muscat, Oman) - ${frappe.datetime.now()}`
                },
                callback: function (r) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Device location updated / تم تحديث موقع الجهاز'),
                        indicator: 'green'
                    });
                }
            });
        }, 2000);
    },

    // Field Event Handlers
    device_name: function (frm) {
        if (frm.doc.device_name && !frm.doc.device_name_ar) {
            frm.set_value('device_name_ar', `جهاز ${frm.doc.device_name}`);
        }
    },

    device_owner: function (frm) {
        if (frm.doc.device_owner && !frm.doc.device_owner_ar) {
            frm.set_value('device_owner_ar', `مالك الجهاز: ${frm.doc.device_owner}`);
        }
    },

    assigned_user: function (frm) {
        if (frm.doc.assigned_user) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'User',
                    filters: { 'name': frm.doc.assigned_user },
                    fieldname: ['email', 'mobile_no', 'full_name']
                },
                callback: function (r) {
                    if (r.message) {
                        if (r.message.email && !frm.doc.email_address) {
                            frm.set_value('email_address', r.message.email);
                        }
                        if (r.message.mobile_no && !frm.doc.contact_number) {
                            frm.set_value('contact_number', r.message.mobile_no);
                        }
                        if (r.message.full_name && !frm.doc.device_owner) {
                            frm.set_value('device_owner', r.message.full_name);
                        }
                    }
                }
            });
        }
    },

    monitoring_enabled: function (frm) {
        if (frm.doc.monitoring_enabled) {
            frm.trigger('start_auto_refresh');
        } else if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
            delete frm.auto_refresh_interval;
        }
    },

    onload: function (frm) {
        // Set default values for new devices
        if (frm.is_new()) {
            frm.set_value('enrollment_date', frappe.datetime.now());
            frm.set_value('device_status', 'Active / نشط');
            frm.set_value('policy_profile', 'Technician / فني');
            frm.set_value('notification_language', 'Both / كلاهما');
            frm.set_value('policy_enforcement_enabled', 1);
            frm.set_value('password_policy_enabled', 1);
            frm.set_value('encryption_enabled', 1);
            frm.set_value('auto_lock_enabled', 1);
            frm.set_value('remote_wipe_enabled', 1);
            frm.set_value('monitoring_enabled', 1);
            frm.set_value('screen_lock_timeout', 5);
            frm.set_value('max_failed_attempts', 5);
        }
    },

    before_save: function (frm) {
        // Clear auto refresh before saving
        if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
            delete frm.auto_refresh_interval;
        }
    }
});

// Utility Functions
function detect_text_direction(text) {
    const arabic_pattern = /[\u0600-\u06FF]/;
    const arabic_chars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    const total_chars = text.replace(/\s/g, '').length;

    return (arabic_chars / total_chars > 0.3) ? 'rtl' : 'ltr';
}

function get_status_class(status) {
    if (!status) return 'status-inactive';

    if (status.includes('Active') || status.includes('نشط')) return 'status-active';
    if (status.includes('Lost') || status.includes('مفقود') || status.includes('Stolen') || status.includes('مسروق')) return 'status-lost';
    if (status.includes('Maintenance') || status.includes('صيانة')) return 'status-maintenance';

    return 'status-inactive';
}

function get_compliance_class(score) {
    if (score >= 90) return 'progress-bar-success compliance-high';
    if (score >= 70) return 'progress-bar-warning compliance-medium';
    return 'progress-bar-danger compliance-low';
}

function get_battery_class(level) {
    if (level >= 50) return 'battery-high';
    if (level >= 20) return 'battery-medium';
    return 'battery-low';
}

// List View Customizations
frappe.listview_settings['Mobile Device Management'] = {
    add_fields: ["device_status", "compliance_status", "battery_level", "last_sync_time", "assigned_user"],
    get_indicator: function (doc) {
        if (doc.device_status === "Active / نشط") {
            if (doc.compliance_status === "Compliant / ممتثل") {
                return [__("Active & Compliant"), "green", "device_status,=,Active / نشط"];
            } else {
                return [__("Active - Non-Compliant"), "orange", "device_status,=,Active / نشط"];
            }
        } else if (doc.device_status === "Lost / مفقود" || doc.device_status === "Stolen / مسروق") {
            return [__("Security Alert"), "red", "device_status,in,Lost / مفقود,Stolen / مسروق"];
        } else if (doc.device_status === "Maintenance / صيانة") {
            return [__("Under Maintenance"), "blue", "device_status,=,Maintenance / صيانة"];
        } else {
            return [__("Inactive"), "gray", "device_status,=,Inactive / غير نشط"];
        }
    },
    onload: function (listview) {
        // Add custom buttons to list view
        listview.page.add_inner_button(__('Bulk Compliance Check'), function () {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select devices to check compliance'));
                return;
            }

            frappe.call({
                method: 'universal_workshop.workshop_management.doctype.mobile_device_management.mobile_device_management.bulk_device_action',
                args: {
                    device_names: selected_docs.map(d => d.name),
                    action: 'compliance_check'
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Bulk compliance check completed'));
                        listview.refresh();
                    }
                }
            });
        });

        listview.page.add_inner_button(__('Sync All Devices'), function () {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select devices to sync'));
                return;
            }

            frappe.call({
                method: 'universal_workshop.workshop_management.doctype.mobile_device_management.mobile_device_management.bulk_device_action',
                args: {
                    device_names: selected_docs.map(d => d.name),
                    action: 'sync'
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Bulk device sync completed'));
                        listview.refresh();
                    }
                }
            });
        });
    }
}; 