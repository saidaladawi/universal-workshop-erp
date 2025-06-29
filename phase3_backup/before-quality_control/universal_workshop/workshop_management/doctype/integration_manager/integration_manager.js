/**
 * Integration Manager JavaScript Controller
 * Universal Workshop ERP - Arabic RTL Integration Management
 */

frappe.ui.form.on('Integration Manager', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('setup_real_time_monitoring');
        frm.trigger('setup_dashboard');
    },

    setup_arabic_fields: function(frm) {
        // إعداد الحقول العربية مع اتجاه RTL
        const arabic_fields = [
            'integration_name_ar', 'provider_name_ar', 'description_ar',
            'notification_message_ar', 'error_message_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': '"Noto Sans Arabic", Tahoma, Arial'
                });
            }
        });

        // إعداد الحقول المختلطة (عربي/إنجليزي)
        const mixed_fields = ['activity_log', 'error_log', 'request_log', 'response_log'];
        mixed_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'auto');
                frm.fields_dict[field].$input.css({
                    'font-family': '"Noto Sans Arabic", Courier, monospace',
                    'direction': 'ltr'
                });
            }
        });
    },

    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // أزرار الاختبار والمراقبة
            frm.add_custom_button(__('Test Connection'), function() {
                frm.trigger('test_connection');
            }, __('Testing'));

            frm.add_custom_button(__('Run Health Check'), function() {
                frm.trigger('run_health_check');
            }, __('Testing'));

            frm.add_custom_button(__('Send Test Webhook'), function() {
                frm.trigger('send_test_webhook');
            }, __('Testing'));

            // أزرار إدارة البيانات
            frm.add_custom_button(__('Sync Data'), function() {
                frm.trigger('sync_data');
            }, __('Data Management'));

            frm.add_custom_button(__('View Statistics'), function() {
                frm.trigger('view_statistics');
            }, __('Data Management'));

            frm.add_custom_button(__('Reset Statistics'), function() {
                frm.trigger('reset_statistics');
            }, __('Data Management'));

            // أزرار المراقبة
            frm.add_custom_button(__('Real-time Monitor'), function() {
                frm.trigger('toggle_monitoring');
            }, __('Monitoring'));

            frm.add_custom_button(__('Export Logs'), function() {
                frm.trigger('export_logs');
            }, __('Monitoring'));

            frm.add_custom_button(__('Clear Logs'), function() {
                frm.trigger('clear_logs');
            }, __('Monitoring'));

            // أزرار الإعدادات
            frm.add_custom_button(__('Duplicate Integration'), function() {
                frm.trigger('duplicate_integration');
            }, __('Settings'));

            frm.add_custom_button(__('Export Configuration'), function() {
                frm.trigger('export_configuration');
            }, __('Settings'));
        }
    },

    setup_field_dependencies: function(frm) {
        // إظهار/إخفاء الحقول حسب النوع
        frm.trigger('toggle_authentication_fields');
        frm.trigger('toggle_webhook_fields');
        frm.trigger('toggle_sync_fields');
        frm.trigger('toggle_monitoring_fields');
        frm.trigger('toggle_notification_fields');
    },

    setup_real_time_monitoring: function(frm) {
        if (frm.doc.monitoring_enabled && !frm.doc.__islocal) {
            // بدء المراقبة في الوقت الفعلي
            frm.monitoring_interval = setInterval(() => {
                frm.trigger('update_real_time_stats');
            }, 30000); // كل 30 ثانية
        }
    },

    setup_dashboard: function(frm) {
        if (!frm.doc.__islocal) {
            frm.trigger('render_dashboard');
        }
    },

    // ============ Field Event Handlers ============

    integration_type: function(frm) {
        frm.trigger('toggle_authentication_fields');
        frm.trigger('set_default_endpoints');
    },

    authentication_type: function(frm) {
        frm.trigger('toggle_authentication_fields');
    },

    webhook_enabled: function(frm) {
        frm.trigger('toggle_webhook_fields');
    },

    sync_enabled: function(frm) {
        frm.trigger('toggle_sync_fields');
    },

    monitoring_enabled: function(frm) {
        frm.trigger('toggle_monitoring_fields');
        if (frm.doc.monitoring_enabled) {
            frm.trigger('setup_real_time_monitoring');
        } else if (frm.monitoring_interval) {
            clearInterval(frm.monitoring_interval);
            frm.monitoring_interval = null;
        }
    },

    email_notifications: function(frm) {
        frm.toggle_reqd('notification_emails', frm.doc.email_notifications);
    },

    sms_notifications: function(frm) {
        frm.toggle_reqd('notification_phones', frm.doc.sms_notifications);
    },

    slack_notifications: function(frm) {
        frm.toggle_reqd('slack_webhook_url', frm.doc.slack_notifications);
    },

    base_url: function(frm) {
        if (frm.doc.base_url && !frm.doc.health_check_url) {
            frm.set_value('health_check_url', frm.doc.base_url + '/health');
        }
    },

    // ============ Testing Functions ============

    test_connection: function(frm) {
        if (!frm.doc.base_url) {
            frappe.msgprint(__('Please set Base URL first'));
            return;
        }

        frappe.show_alert({
            message: __('Testing connection...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'test_connection',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __('Connection successful! Response time: {0}ms', [r.message.response_time.toFixed(2)]),
                            indicator: 'green'
                        });
                        frm.trigger('refresh_logs');
                    } else {
                        frappe.show_alert({
                            message: __('Connection failed: {0}', [r.message.error]),
                            indicator: 'red'
                        });
                    }
                }
            },
            error: function(xhr) {
                frappe.show_alert({
                    message: __('Connection test failed'),
                    indicator: 'red'
                });
            }
        });
    },

    run_health_check: function(frm) {
        frappe.show_alert({
            message: __('Running health check...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'run_health_check',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __('Health check passed! Status: {0}', [r.message.status]),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Health check failed: {0}', [r.message.error || 'Unknown error']),
                            indicator: 'red'
                        });
                    }
                    frm.refresh();
                }
            }
        });
    },

    send_test_webhook: function(frm) {
        if (!frm.doc.webhook_enabled || !frm.doc.webhook_url) {
            frappe.msgprint(__('Webhooks not configured'));
            return;
        }

        const test_data = {
            test: true,
            timestamp: new Date().toISOString(),
            integration: frm.doc.integration_name,
            message: 'Test webhook from Universal Workshop ERP'
        };

        frappe.show_alert({
            message: __('Sending test webhook...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'send_webhook',
            doc: frm.doc,
            args: {
                event: 'test',
                data: test_data
            },
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __('Test webhook sent successfully!'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Webhook failed: {0}', [r.message.error]),
                            indicator: 'red'
                        });
                    }
                    frm.trigger('refresh_logs');
                }
            }
        });
    },

    // ============ Data Management Functions ============

    sync_data: function(frm) {
        if (!frm.doc.sync_enabled) {
            frappe.msgprint(__('Data synchronization not enabled'));
            return;
        }

        const d = new frappe.ui.Dialog({
            title: __('Data Synchronization'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'direction',
                    label: __('Sync Direction'),
                    options: [
                        'Inbound Only / وارد فقط',
                        'Outbound Only / صادر فقط',
                        'Bidirectional / ثنائي الاتجاه'
                    ],
                    default: frm.doc.sync_direction
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'force_sync',
                    label: __('Force Sync (ignore last sync time)')
                }
            ],
            primary_action_label: __('Start Sync'),
            primary_action: function(values) {
                frappe.show_alert({
                    message: __('Starting data synchronization...'),
                    indicator: 'blue'
                });

                frappe.call({
                    method: 'sync_data',
                    doc: frm.doc,
                    args: {
                        direction: values.direction
                    },
                    callback: function(r) {
                        if (r.message) {
                            if (r.message.success) {
                                frappe.show_alert({
                                    message: __('Data synchronization completed successfully!'),
                                    indicator: 'green'
                                });
                            } else {
                                frappe.show_alert({
                                    message: __('Sync failed: {0}', [r.message.error]),
                                    indicator: 'red'
                                });
                            }
                            frm.refresh();
                        }
                        d.hide();
                    }
                });
            }
        });

        d.show();
    },

    view_statistics: function(frm) {
        frappe.call({
            method: 'get_integration_stats',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    const stats = r.message;
                    
                    const d = new frappe.ui.Dialog({
                        title: __('Integration Statistics'),
                        size: 'large',
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'stats_html'
                            }
                        ]
                    });

                    const stats_html = `
                        <div style="padding: 20px; font-family: Arial, sans-serif;">
                            <div class="row">
                                <div class="col-sm-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5>${__('Usage Statistics')}</h5>
                                        </div>
                                        <div class="card-body">
                                            <p><strong>${__('Success Count')}:</strong> ${stats.success_count}</p>
                                            <p><strong>${__('Failure Count')}:</strong> ${stats.failure_count}</p>
                                            <p><strong>${__('Total Usage')}:</strong> ${stats.usage_count}</p>
                                            <p><strong>${__('Success Rate')}:</strong> ${stats.success_rate}%</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5>${__('Performance Metrics')}</h5>
                                        </div>
                                        <div class="card-body">
                                            <p><strong>${__('Average Response Time')}:</strong> ${stats.average_response_time.toFixed(2)}ms</p>
                                            <p><strong>${__('Last Used')}:</strong> ${stats.last_used || 'Never'}</p>
                                            <p><strong>${__('Last Health Check')}:</strong> ${stats.last_health_check || 'Never'}</p>
                                            <p><strong>${__('Last Error')}:</strong> ${stats.last_error || 'None'}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    d.fields_dict.stats_html.$wrapper.html(stats_html);
                    d.show();
                }
            }
        });
    },

    reset_statistics: function(frm) {
        frappe.confirm(
            __('Are you sure you want to reset all statistics? This action cannot be undone.'),
            function() {
                frappe.call({
                    method: 'reset_statistics',
                    doc: frm.doc,
                    callback: function(r) {
                        frappe.show_alert({
                            message: __('Statistics reset successfully'),
                            indicator: 'green'
                        });
                        frm.refresh();
                    }
                });
            }
        );
    },

    // ============ Field Toggle Functions ============

    toggle_authentication_fields: function(frm) {
        const auth_type = frm.doc.authentication_type;
        
        // إخفاء جميع حقول المصادقة أولاً
        frm.toggle_display('api_key', false);
        frm.toggle_display('access_token', false);
        frm.toggle_display('username', false);
        frm.toggle_display('password', false);
        frm.toggle_display('client_id', false);
        frm.toggle_display('client_secret', false);
        frm.toggle_display('token_endpoint', false);
        frm.toggle_display('refresh_token', false);

        // إظهار الحقول المطلوبة حسب نوع المصادقة
        if (auth_type === 'API Key / مفتاح API') {
            frm.toggle_display('api_key', true);
            frm.toggle_reqd('api_key', true);
        } else if (auth_type === 'Bearer Token / رمز الحامل') {
            frm.toggle_display('access_token', true);
            frm.toggle_reqd('access_token', true);
        } else if (auth_type === 'Basic Auth / المصادقة الأساسية') {
            frm.toggle_display('username', true);
            frm.toggle_display('password', true);
            frm.toggle_reqd('username', true);
            frm.toggle_reqd('password', true);
        } else if (auth_type === 'OAuth 2.0 / OAuth 2.0') {
            frm.toggle_display('client_id', true);
            frm.toggle_display('client_secret', true);
            frm.toggle_display('token_endpoint', true);
            frm.toggle_display('access_token', true);
            frm.toggle_display('refresh_token', true);
            frm.toggle_reqd('client_id', true);
            frm.toggle_reqd('client_secret', true);
        } else if (auth_type === 'JWT / JWT') {
            frm.toggle_display('access_token', true);
            frm.toggle_reqd('access_token', true);
        }
    },

    toggle_webhook_fields: function(frm) {
        const enabled = frm.doc.webhook_enabled;
        
        frm.toggle_display('webhook_url', enabled);
        frm.toggle_display('webhook_method', enabled);
        frm.toggle_display('webhook_secret', enabled);
        frm.toggle_display('webhook_headers', enabled);
        frm.toggle_display('webhook_payload_template', enabled);
        frm.toggle_display('webhook_retry_attempts', enabled);
        frm.toggle_display('webhook_retry_delay', enabled);
        
        frm.toggle_reqd('webhook_url', enabled);
    },

    toggle_sync_fields: function(frm) {
        const enabled = frm.doc.sync_enabled;
        
        frm.toggle_display('sync_direction', enabled);
        frm.toggle_display('sync_frequency', enabled);
        frm.toggle_display('last_sync', enabled);
        frm.toggle_display('auto_sync', enabled);
    },

    toggle_monitoring_fields: function(frm) {
        const enabled = frm.doc.monitoring_enabled;
        
        frm.toggle_display('health_check_url', enabled);
        frm.toggle_display('health_check_timeout', enabled);
        frm.toggle_display('last_health_check', enabled);
        frm.toggle_display('alert_on_failure', enabled);
        frm.toggle_display('alert_threshold', enabled);
    },

    toggle_notification_fields: function(frm) {
        frm.toggle_reqd('notification_emails', frm.doc.email_notifications);
        frm.toggle_reqd('notification_phones', frm.doc.sms_notifications);
        frm.toggle_reqd('slack_webhook_url', frm.doc.slack_notifications);
    },

    // ============ Real-time Monitoring ============

    toggle_monitoring: function(frm) {
        if (frm.monitoring_active) {
            // إيقاف المراقبة
            if (frm.monitoring_interval) {
                clearInterval(frm.monitoring_interval);
                frm.monitoring_interval = null;
            }
            frm.monitoring_active = false;
            frappe.show_alert({
                message: __('Real-time monitoring stopped'),
                indicator: 'orange'
            });
        } else {
            // بدء المراقبة
            frm.trigger('setup_real_time_monitoring');
            frm.monitoring_active = true;
            frappe.show_alert({
                message: __('Real-time monitoring started'),
                indicator: 'green'
            });
        }
    },

    update_real_time_stats: function(frm) {
        if (!frm.monitoring_active) return;

        frappe.call({
            method: 'get_integration_stats',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.trigger('update_dashboard_stats', r.message);
                }
            }
        });
    },

    // ============ Dashboard Functions ============

    render_dashboard: function(frm) {
        const dashboard_html = `
            <div class="integration-dashboard" style="margin: 20px 0;">
                <div class="row">
                    <div class="col-sm-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 id="success-count" class="text-success">-</h3>
                                <p class="card-text">${__('Successful Requests')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 id="failure-count" class="text-danger">-</h3>
                                <p class="card-text">${__('Failed Requests')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 id="success-rate" class="text-info">-</h3>
                                <p class="card-text">${__('Success Rate')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 id="avg-response" class="text-primary">-</h3>
                                <p class="card-text">${__('Avg Response (ms)')}</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-sm-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>${__('Integration Status')}</h5>
                            </div>
                            <div class="card-body">
                                <div id="status-indicator" class="text-center">
                                    <span class="indicator-dot" style="background-color: #ccc;"></span>
                                    <span id="status-text">${__('Checking...')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // إضافة لوحة التحكم إلى النموذج
        if (!frm.dashboard_wrapper) {
            frm.dashboard_wrapper = $('<div>').appendTo(frm.layout.wrapper.find('.form-layout'));
        }
        frm.dashboard_wrapper.html(dashboard_html);

        // تحديث البيانات الأولية
        frm.trigger('update_dashboard_initial');
    },

    update_dashboard_initial: function(frm) {
        frappe.call({
            method: 'get_integration_stats',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.trigger('update_dashboard_stats', r.message);
                }
            }
        });
    },

    update_dashboard_stats: function(frm, stats) {
        if (!stats) return;

        $('#success-count').text(stats.success_count || 0);
        $('#failure-count').text(stats.failure_count || 0);
        $('#success-rate').text((stats.success_rate || 0) + '%');
        $('#avg-response').text((stats.average_response_time || 0).toFixed(2));

        // تحديث مؤشر الحالة
        const status_colors = {
            'Active / نشط': '#28a745',
            'Inactive / غير نشط': '#6c757d',
            'Error / خطأ': '#dc3545',
            'Testing / اختبار': '#ffc107'
        };

        const color = status_colors[frm.doc.integration_status] || '#6c757d';
        $('.indicator-dot').css('background-color', color);
        $('#status-text').text(frm.doc.integration_status || __('Unknown'));
    },

    // ============ Utility Functions ============

    set_default_endpoints: function(frm) {
        const type = frm.doc.integration_type;
        
        // تعيين نقاط النهاية الافتراضية حسب النوع
        const default_endpoints = {
            'REST API / واجهة برمجة التطبيقات REST': {
                health_check_url: '/health'
            },
            'GraphQL API / واجهة GraphQL': {
                health_check_url: '/health'
            },
            'SOAP Web Service / خدمة ويب SOAP': {
                health_check_url: '?wsdl'
            }
        };

        const defaults = default_endpoints[type];
        if (defaults && frm.doc.base_url) {
            Object.keys(defaults).forEach(field => {
                if (!frm.doc[field]) {
                    frm.set_value(field, frm.doc.base_url + defaults[field]);
                }
            });
        }
    },

    refresh_logs: function(frm) {
        frm.refresh_field('activity_log');
        frm.refresh_field('error_log');
        frm.refresh_field('request_log');
        frm.refresh_field('response_log');
    },

    export_logs: function(frm) {
        const logs_data = {
            integration_name: frm.doc.integration_name,
            export_time: new Date().toISOString(),
            activity_log: frm.doc.activity_log,
            error_log: frm.doc.error_log,
            request_log: frm.doc.request_log,
            response_log: frm.doc.response_log
        };

        const blob = new Blob([JSON.stringify(logs_data, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `integration_logs_${frm.doc.name}_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);

        frappe.show_alert({
            message: __('Logs exported successfully'),
            indicator: 'green'
        });
    },

    clear_logs: function(frm) {
        frappe.confirm(
            __('Are you sure you want to clear all logs? This action cannot be undone.'),
            function() {
                frm.set_value('activity_log', '');
                frm.set_value('error_log', '');
                frm.set_value('request_log', '');
                frm.set_value('response_log', '');
                
                frappe.show_alert({
                    message: __('Logs cleared successfully'),
                    indicator: 'green'
                });
            }
        );
    },

    duplicate_integration: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Duplicate Integration'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'new_name',
                    label: __('New Integration Name'),
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'new_name_ar',
                    label: __('New Integration Name (Arabic)'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Create Duplicate'),
            primary_action: function(values) {
                frappe.call({
                    method: 'frappe.client.copy_doc',
                    args: {
                        doc: frm.doc
                    },
                    callback: function(r) {
                        if (r.message) {
                            const new_doc = r.message;
                            new_doc.integration_name = values.new_name;
                            new_doc.integration_name_ar = values.new_name_ar;
                            new_doc.integration_status = 'Inactive / غير نشط';
                            
                            // مسح السجلات والإحصائيات
                            new_doc.activity_log = '';
                            new_doc.error_log = '';
                            new_doc.request_log = '';
                            new_doc.response_log = '';
                            new_doc.success_count = 0;
                            new_doc.failure_count = 0;
                            new_doc.usage_count = 0;
                            new_doc.average_response_time = 0;

                            frappe.set_route('Form', 'Integration Manager', new_doc.name);
                        }
                        d.hide();
                    }
                });
            }
        });

        d.show();
    },

    export_configuration: function(frm) {
        const config_data = {
            integration_name: frm.doc.integration_name,
            integration_type: frm.doc.integration_type,
            provider_name: frm.doc.provider_name,
            base_url: frm.doc.base_url,
            authentication_type: frm.doc.authentication_type,
            webhook_enabled: frm.doc.webhook_enabled,
            webhook_url: frm.doc.webhook_url,
            webhook_method: frm.doc.webhook_method,
            sync_enabled: frm.doc.sync_enabled,
            sync_direction: frm.doc.sync_direction,
            monitoring_enabled: frm.doc.monitoring_enabled,
            export_time: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(config_data, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `integration_config_${frm.doc.name}.json`;
        a.click();
        URL.revokeObjectURL(url);

        frappe.show_alert({
            message: __('Configuration exported successfully'),
            indicator: 'green'
        });
    }
});

// تنظيف المراقبة عند الخروج
$(window).on('beforeunload', function() {
    if (cur_frm && cur_frm.monitoring_interval) {
        clearInterval(cur_frm.monitoring_interval);
    }
});
