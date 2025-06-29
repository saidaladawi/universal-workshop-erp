/**
 * Error Logger JavaScript Controller
 * Universal Workshop ERP - Error Logging and Monitoring System
 * Arabic RTL Support with Real-time Error Management
 */

frappe.ui.form.on('Error Logger', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('setup_realtime_monitoring');
        frm.trigger('setup_dashboard_view');
        frm.trigger('load_error_statistics');
    },

    onload: function (frm) {
        frm.trigger('setup_field_formatting');
        frm.trigger('setup_notification_channels');

        // Load dashboard data for new errors
        if (frm.is_new()) {
            frm.trigger('setup_new_error_defaults');
        }
    },

    // ============ Arabic RTL Setup ============

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic text fields
        const arabic_fields = [
            'error_title_ar', 'error_message_ar', 'error_description_ar',
            'resolution_notes_ar', 'business_impact_description_ar',
            'stakeholder_feedback_ar', 'prevention_measures_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': "'Noto Sans Arabic', Tahoma, Arial"
                });
            }
        });

        // Apply RTL to the entire form if Arabic is primary language
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Adjust form layout for Arabic
            $('.form-column').css('direction', 'rtl');
            $('.control-label').css('text-align', 'right');
        }
    },

    setup_field_formatting: function (frm) {
        // Format datetime fields for Arabic locale
        if (frappe.boot.lang === 'ar') {
            const datetime_fields = [
                'first_occurrence', 'last_occurrence', 'resolution_date',
                'escalation_time', 'created_date', 'modified_date'
            ];

            datetime_fields.forEach(field => {
                if (frm.fields_dict[field] && frm.doc[field]) {
                    // Format for Arabic display
                    frm.fields_dict[field].$input.attr('lang', 'ar');
                }
            });
        }

        // Format number fields
        const number_fields = [
            'occurrence_count', 'resolution_time_minutes', 'affected_users_count',
            'financial_impact', 'escalation_level', 'similar_errors_count'
        ];

        number_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('input', function () {
                    let value = $(this).val();
                    if (frappe.boot.lang === 'ar') {
                        // Convert to Arabic-Indic numerals for display
                        $(this).val(convert_to_arabic_numerals(value));
                    }
                });
            }
        });
    },

    // ============ Custom Buttons Setup ============

    setup_custom_buttons: function (frm) {
        // Clear existing buttons
        frm.page.clear_menu();
        frm.page.clear_inner_toolbar();

        // Error Management Buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Mark as Seen'), () => {
                frm.trigger('mark_error_as_seen');
            }, __('Actions'));

            frm.add_custom_button(__('Archive Error'), () => {
                frm.trigger('archive_error');
            }, __('Actions'));

            frm.add_custom_button(__('Assign to User'), () => {
                frm.trigger('assign_error_to_user');
            }, __('Actions'));

            // Resolution buttons
            if (frm.doc.error_status !== 'Resolved / محلول') {
                frm.add_custom_button(__('Mark as Resolved'), () => {
                    frm.trigger('mark_as_resolved');
                }, __('Resolution'));
            }

            if (frm.doc.error_status === 'Resolved / محلول') {
                frm.add_custom_button(__('Reopen Error'), () => {
                    frm.trigger('reopen_error');
                }, __('Resolution'));
            }

            // Notification buttons
            frm.add_custom_button(__('Send Notification'), () => {
                frm.trigger('send_manual_notification');
            }, __('Notifications'));

            frm.add_custom_button(__('Test Notifications'), () => {
                frm.trigger('test_notification_channels');
            }, __('Notifications'));

            // Analysis buttons
            frm.add_custom_button(__('View Similar Errors'), () => {
                frm.trigger('view_similar_errors');
            }, __('Analysis'));

            frm.add_custom_button(__('Generate Report'), () => {
                frm.trigger('generate_error_report');
            }, __('Analysis'));

            frm.add_custom_button(__('Error Trends'), () => {
                frm.trigger('show_error_trends');
            }, __('Analysis'));
        }

        // Dashboard button for all errors
        frm.add_custom_button(__('Error Dashboard'), () => {
            frm.trigger('open_error_dashboard');
        }, __('Dashboard'));

        frm.add_custom_button(__('System Health'), () => {
            frm.trigger('check_system_health');
        }, __('Dashboard'));
    },

    // ============ Field Dependencies ============

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on error category
        frm.trigger('toggle_category_fields');

        // Show/hide notification fields based on channels
        frm.trigger('toggle_notification_fields');

        // Show/hide resolution fields based on status
        frm.trigger('toggle_resolution_fields');

        // Show/hide escalation fields
        frm.trigger('toggle_escalation_fields');
    },

    toggle_category_fields: function (frm) {
        const category = frm.doc.error_category;

        // API Error specific fields
        frm.toggle_display(['request_url', 'request_method', 'response_code', 'response_body'],
            category === 'API Error / خطأ واجهة برمجة التطبيقات');

        // Database Error specific fields
        frm.toggle_display(['database_query', 'table_name', 'database_connection'],
            category === 'Database Error / خطأ قاعدة البيانات');

        // Permission Error specific fields
        frm.toggle_display(['user_role', 'required_permission', 'permission_level'],
            category === 'Permission Error / خطأ الصلاحية');
    },

    toggle_notification_fields: function (frm) {
        const channels = frm.doc.notification_channels || [];

        frm.toggle_display('email_recipients',
            channels.includes('Email / البريد الإلكتروني'));

        frm.toggle_display('sms_recipients',
            channels.includes('SMS / رسائل نصية'));

        frm.toggle_display('slack_channel',
            channels.includes('Slack / سلاك'));

        frm.toggle_display('teams_channel',
            channels.includes('Microsoft Teams / مايكروسوفت تيمز'));
    },

    toggle_resolution_fields: function (frm) {
        const status = frm.doc.error_status;
        const is_resolved = ['Resolved / محلول', 'Verified / تم التحقق', 'Closed / مغلق'].includes(status);

        frm.toggle_display(['resolution_date', 'resolved_by', 'resolution_notes',
            'resolution_notes_ar', 'verification_status'], is_resolved);
    },

    toggle_escalation_fields: function (frm) {
        frm.toggle_display(['escalation_level', 'escalation_time', 'escalation_recipients'],
            frm.doc.auto_escalate);
    },

    // ============ Real-time Monitoring ============

    setup_realtime_monitoring: function (frm) {
        if (!frm.is_new()) {
            // Set up real-time updates for error status
            frappe.realtime.on('error_logger_update', (data) => {
                if (data.error_id === frm.doc.name) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Error status updated in real-time'),
                        indicator: 'blue'
                    });
                }
            });

            // Monitor similar errors
            if (frm.doc.hash_signature) {
                setInterval(() => {
                    frm.trigger('check_similar_errors');
                }, 60000); // Check every minute
            }
        }

        // Set up error statistics refresh
        setInterval(() => {
            frm.trigger('refresh_error_statistics');
        }, 30000); // Refresh every 30 seconds
    },

    check_similar_errors: function (frm) {
        if (!frm.doc.hash_signature) return;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Error Logger',
                filters: {
                    hash_signature: frm.doc.hash_signature,
                    name: ['!=', frm.doc.name]
                },
                fields: ['name', 'occurrence_count', 'last_occurrence']
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    const count = r.message.length;
                    frm.dashboard.add_indicator(__('Similar Errors: {0}', [count]), 'orange');

                    if (count > frm.doc.similar_errors_count) {
                        frappe.show_alert({
                            message: __('New similar errors detected'),
                            indicator: 'orange'
                        });
                    }
                }
            }
        });
    },

    // ============ Dashboard and Statistics ============

    setup_dashboard_view: function (frm) {
        // Create dashboard section
        frm.dashboard.reset();

        if (!frm.is_new()) {
            // Error status indicator
            let status_color = 'blue';
            if (frm.doc.severity_level === 'Critical / حرج') status_color = 'red';
            else if (frm.doc.severity_level === 'High / عالي') status_color = 'orange';
            else if (frm.doc.severity_level === 'Medium / متوسط') status_color = 'yellow';
            else if (frm.doc.severity_level === 'Low / منخفض') status_color = 'green';

            frm.dashboard.add_indicator(__('Severity: {0}', [frm.doc.severity_level]), status_color);

            // Occurrence count
            if (frm.doc.occurrence_count > 1) {
                frm.dashboard.add_indicator(__('Occurrences: {0}', [frm.doc.occurrence_count]), 'blue');
            }

            // Resolution time
            if (frm.doc.resolution_time_minutes) {
                const hours = Math.floor(frm.doc.resolution_time_minutes / 60);
                const minutes = frm.doc.resolution_time_minutes % 60;
                frm.dashboard.add_indicator(__('Resolution Time: {0}h {1}m', [hours, minutes]), 'green');
            }

            // Escalation status
            if (frm.doc.escalation_level > 0) {
                frm.dashboard.add_indicator(__('Escalation Level: {0}', [frm.doc.escalation_level]), 'red');
            }
        }
    },

    load_error_statistics: function (frm) {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.get_error_dashboard_data',
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_error_statistics', r.message);
                }
            }
        });
    },

    display_error_statistics: function (frm, data) {
        if (!data) return;

        // Create statistics HTML
        let stats_html = `
            <div class="error-statistics" style="margin: 15px 0;">
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 5px;">
                            <h4 style="color: #495057; margin: 0;">${data.summary.total_errors}</h4>
                            <p style="margin: 5px 0 0 0; color: #6c757d;">${__('Total Errors')}</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 5px;">
                            <h4 style="color: #856404; margin: 0;">${data.summary.new_errors}</h4>
                            <p style="margin: 5px 0 0 0; color: #856404;">${__('New Errors')}</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 5px;">
                            <h4 style="color: #721c24; margin: 0;">${data.summary.critical_errors}</h4>
                            <p style="margin: 5px 0 0 0; color: #721c24;">${__('Critical Errors')}</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="background: #d1ecf1; padding: 15px; border-radius: 8px; margin: 5px;">
                            <h4 style="color: #0c5460; margin: 0;">${data.summary.recent_errors}</h4>
                            <p style="margin: 5px 0 0 0; color: #0c5460;">${__('This Week')}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to form dashboard
        if (!frm.dashboard.stats_wrapper) {
            frm.dashboard.stats_wrapper = $('<div class="form-dashboard-section">').appendTo(frm.dashboard.wrapper);
        }
        frm.dashboard.stats_wrapper.html(stats_html);
    },

    refresh_error_statistics: function (frm) {
        frm.trigger('load_error_statistics');
    },

    // ============ Error Actions ============

    mark_error_as_seen: function (frm) {
        frappe.call({
            method: 'mark_as_seen',
            doc: frm.doc,
            callback: function (r) {
                if (!r.exc) {
                    frappe.show_alert({
                        message: __('Error marked as seen'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                }
            }
        });
    },

    archive_error: function (frm) {
        frappe.confirm(
            __('Are you sure you want to archive this error? This action cannot be undone.'),
            () => {
                frappe.call({
                    method: 'archive_error',
                    doc: frm.doc,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Error archived successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    assign_error_to_user: function (frm) {
        let d = new frappe.ui.Dialog({
            title: __('Assign Error to User'),
            fields: [
                {
                    label: __('User'),
                    fieldname: 'user',
                    fieldtype: 'Link',
                    options: 'User',
                    reqd: 1,
                    filters: {
                        enabled: 1
                    }
                },
                {
                    label: __('Comments'),
                    fieldname: 'comments',
                    fieldtype: 'Small Text'
                }
            ],
            primary_action_label: __('Assign'),
            primary_action: function (values) {
                frappe.call({
                    method: 'assign_to_user',
                    doc: frm.doc,
                    args: {
                        user: values.user
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Error assigned to {0}', [values.user]),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                            d.hide();
                        }
                    }
                });
            }
        });
        d.show();
    },

    mark_as_resolved: function (frm) {
        let d = new frappe.ui.Dialog({
            title: __('Mark Error as Resolved'),
            fields: [
                {
                    label: __('Resolution Notes'),
                    fieldname: 'resolution_notes',
                    fieldtype: 'Text',
                    reqd: 1
                },
                {
                    label: __('Resolution Notes (Arabic)'),
                    fieldname: 'resolution_notes_ar',
                    fieldtype: 'Text'
                },
                {
                    label: __('Prevention Measures'),
                    fieldname: 'prevention_measures',
                    fieldtype: 'Text'
                }
            ],
            primary_action_label: __('Mark as Resolved'),
            primary_action: function (values) {
                frm.set_value('error_status', 'Resolved / محلول');
                frm.set_value('resolution_status', 'Resolved / محلول');
                frm.set_value('resolution_notes', values.resolution_notes);
                frm.set_value('resolution_notes_ar', values.resolution_notes_ar);
                frm.set_value('prevention_measures', values.prevention_measures);
                frm.set_value('resolution_date', frappe.datetime.now_datetime());
                frm.set_value('resolved_by', frappe.session.user);

                frm.save().then(() => {
                    frappe.show_alert({
                        message: __('Error marked as resolved'),
                        indicator: 'green'
                    });
                    d.hide();
                });
            }
        });
        d.show();
    },

    reopen_error: function (frm) {
        frappe.confirm(
            __('Are you sure you want to reopen this error?'),
            () => {
                frm.set_value('error_status', 'Reopened / أعيد فتحه');
                frm.set_value('resolution_status', 'Pending / معلق');
                frm.set_value('resolution_date', '');
                frm.set_value('resolved_by', '');

                frm.save().then(() => {
                    frappe.show_alert({
                        message: __('Error reopened'),
                        indicator: 'orange'
                    });
                });
            }
        );
    },

    // ============ Notification Management ============

    send_manual_notification: function (frm) {
        let d = new frappe.ui.Dialog({
            title: __('Send Manual Notification'),
            fields: [
                {
                    label: __('Notification Template'),
                    fieldname: 'template',
                    fieldtype: 'Select',
                    options: ['Critical Error / خطأ حرج', 'High Priority / أولوية عالية',
                        'System Down / توقف النظام', 'Security Alert / تنبيه أمني'],
                    default: frm.doc.notification_template
                },
                {
                    label: __('Additional Message'),
                    fieldname: 'additional_message',
                    fieldtype: 'Text'
                },
                {
                    label: __('Recipients'),
                    fieldname: 'recipients',
                    fieldtype: 'Small Text',
                    default: frm.doc.email_recipients
                }
            ],
            primary_action_label: __('Send Notification'),
            primary_action: function (values) {
                frappe.call({
                    method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.send_manual_notification',
                    args: {
                        error_id: frm.doc.name,
                        template: values.template,
                        additional_message: values.additional_message,
                        recipients: values.recipients
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Notification sent successfully'),
                                indicator: 'green'
                            });
                            d.hide();
                        }
                    }
                });
            }
        });
        d.show();
    },

    test_notification_channels: function (frm) {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.test_notification_channels',
            args: {
                error_id: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    let results = r.message;
                    let message = __('Notification Test Results:') + '<br>';

                    for (let channel in results) {
                        let status = results[channel] ? '✅' : '❌';
                        message += `${status} ${channel}<br>`;
                    }

                    frappe.msgprint({
                        title: __('Test Results'),
                        message: message,
                        indicator: 'blue'
                    });
                }
            }
        });
    },

    // ============ Analysis and Reporting ============

    view_similar_errors: function (frm) {
        if (!frm.doc.hash_signature) {
            frappe.msgprint(__('No signature available for similarity analysis'));
            return;
        }

        frappe.route_options = {
            hash_signature: frm.doc.hash_signature
        };
        frappe.set_route('List', 'Error Logger');
    },

    generate_error_report: function (frm) {
        let d = new frappe.ui.Dialog({
            title: __('Generate Error Report'),
            fields: [
                {
                    label: __('Start Date'),
                    fieldname: 'start_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
                    reqd: 1
                },
                {
                    label: __('End Date'),
                    fieldname: 'end_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.nowdate(),
                    reqd: 1
                },
                {
                    label: __('Report Type'),
                    fieldname: 'report_type',
                    fieldtype: 'Select',
                    options: ['Summary / موجز', 'Detailed / تفصيلي'],
                    default: 'Summary / موجز'
                },
                {
                    label: __('Include Categories'),
                    fieldname: 'categories',
                    fieldtype: 'MultiSelectPills',
                    options: ['System Error / خطأ النظام', 'Database Error / خطأ قاعدة البيانات',
                        'API Error / خطأ واجهة برمجة التطبيقات', 'Permission Error / خطأ الصلاحية',
                        'Validation Error / خطأ التحقق', 'Network Error / خطأ الشبكة']
                }
            ],
            primary_action_label: __('Generate Report'),
            primary_action: function (values) {
                window.open(
                    `/api/method/universal_workshop.workshop_management.doctype.error_logger.error_logger.generate_error_report?start_date=${values.start_date}&end_date=${values.end_date}&format_type=${values.report_type}`,
                    '_blank'
                );
                d.hide();
            }
        });
        d.show();
    },

    show_error_trends: function (frm) {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.get_error_trends',
            args: {
                category: frm.doc.error_category,
                days: 30
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_error_trends', r.message);
                }
            }
        });
    },

    display_error_trends: function (frm, trends_data) {
        let d = new frappe.ui.Dialog({
            title: __('Error Trends Analysis'),
            fields: [
                {
                    fieldname: 'trends_chart',
                    fieldtype: 'HTML'
                }
            ]
        });

        // Create trends chart HTML
        let chart_html = `
            <div class="trends-analysis">
                <h4>${__('Error Trends for Category: {0}', [frm.doc.error_category])}</h4>
                <div class="trend-metrics">
                    <p><strong>${__('Weekly Growth Rate')}:</strong> ${trends_data.growth_rate}%</p>
                    <p><strong>${__('Resolution Rate')}:</strong> ${trends_data.resolution_rate}%</p>
                    <p><strong>${__('Average Resolution Time')}:</strong> ${trends_data.avg_resolution_time} minutes</p>
                </div>
            </div>
        `;

        d.fields_dict.trends_chart.$wrapper.html(chart_html);
        d.show();
    },

    // ============ Dashboard Functions ============

    open_error_dashboard: function (frm) {
        frappe.set_route('query-report', 'Error Logger Dashboard');
    },

    check_system_health: function (frm) {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.check_system_health',
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_system_health', r.message);
                }
            }
        });
    },

    display_system_health: function (frm, health_data) {
        let d = new frappe.ui.Dialog({
            title: __('System Health Check'),
            fields: [
                {
                    fieldname: 'health_status',
                    fieldtype: 'HTML'
                }
            ]
        });

        let health_html = `
            <div class="system-health">
                <h4>${__('System Health Status')}</h4>
                <div class="health-metrics">
                    <p><strong>${__('Overall Status')}:</strong> 
                        <span class="indicator ${health_data.overall_status === 'Healthy' ? 'green' : 'red'}">
                            ${health_data.overall_status}
                        </span>
                    </p>
                    <p><strong>${__('Error Rate (24h)')}:</strong> ${health_data.error_rate_24h}</p>
                    <p><strong>${__('Critical Errors')}:</strong> ${health_data.critical_errors}</p>
                    <p><strong>${__('System Uptime')}:</strong> ${health_data.uptime}</p>
                </div>
            </div>
        `;

        d.fields_dict.health_status.$wrapper.html(health_html);
        d.show();
    },

    // ============ New Error Setup ============

    setup_new_error_defaults: function (frm) {
        // Set default values for new errors
        frm.set_value('created_by_system', frappe.session.user);
        frm.set_value('created_date', frappe.datetime.now_datetime());
        frm.set_value('first_occurrence', frappe.datetime.now_datetime());
        frm.set_value('error_status', 'New / جديد');
        frm.set_value('occurrence_count', 1);

        // Auto-detect user information
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'User',
                name: frappe.session.user
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('user_name', r.message.name);
                    frm.set_value('user_full_name', r.message.full_name);
                    frm.set_value('user_email', r.message.email);
                }
            }
        });
    },

    setup_notification_channels: function (frm) {
        // Setup default notification channels based on severity
        if (frm.is_new()) {
            frm.set_value('notification_channels', ['Email / البريد الإلكتروني']);
        }
    },

    // ============ Field Event Handlers ============

    error_category: function (frm) {
        frm.trigger('toggle_category_fields');
        frm.trigger('auto_categorize_error');
    },

    severity_level: function (frm) {
        frm.trigger('update_priority_based_on_severity');
        frm.trigger('setup_notification_channels');
    },

    notification_channels: function (frm) {
        frm.trigger('toggle_notification_fields');
    },

    error_status: function (frm) {
        frm.trigger('toggle_resolution_fields');
    },

    auto_escalate: function (frm) {
        frm.trigger('toggle_escalation_fields');
    },

    update_priority_based_on_severity: function (frm) {
        const severity_priority_map = {
            'Critical / حرج': 'Immediate / فوري',
            'High / عالي': 'Urgent / عاجل',
            'Medium / متوسط': 'Medium / متوسط',
            'Low / منخفض': 'Low / منخفض',
            'Info / معلوماتي': 'Backlog / قائمة الانتظار'
        };

        if (frm.doc.severity_level && !frm.doc.resolution_priority) {
            frm.set_value('resolution_priority', severity_priority_map[frm.doc.severity_level]);
        }
    },

    auto_categorize_error: function (frm) {
        if (frm.doc.error_message && !frm.doc.error_category) {
            const message = frm.doc.error_message.toLowerCase();

            if (message.includes('permission') || message.includes('access')) {
                frm.set_value('error_category', 'Permission Error / خطأ الصلاحية');
            } else if (message.includes('database') || message.includes('sql')) {
                frm.set_value('error_category', 'Database Error / خطأ قاعدة البيانات');
            } else if (message.includes('api') || message.includes('http')) {
                frm.set_value('error_category', 'API Error / خطأ واجهة برمجة التطبيقات');
            } else if (message.includes('validation') || message.includes('required')) {
                frm.set_value('error_category', 'Validation Error / خطأ التحقق');
            }
        }
    }
});

// ============ Utility Functions ============

function convert_to_arabic_numerals(englishNum) {
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return englishNum.toString().replace(/[0-9]/g, function (w) {
        return arabicNumbers[+w];
    });
}

// ============ List View Customizations ============

frappe.listview_settings['Error Logger'] = {
    add_fields: ['error_status', 'severity_level', 'error_category', 'occurrence_count'],
    get_indicator: function (doc) {
        const status_colors = {
            'New / جديد': 'blue',
            'In Progress / قيد التقدم': 'orange',
            'Resolved / محلول': 'green',
            'Closed / مغلق': 'gray',
            'Reopened / أعيد فتحه': 'red'
        };

        return [__(doc.error_status), status_colors[doc.error_status] || 'gray', 'error_status,=,' + doc.error_status];
    },

    onload: function (listview) {
        // Add custom buttons to list view
        listview.page.add_inner_button(__('Error Dashboard'), function () {
            frappe.set_route('query-report', 'Error Logger Dashboard');
        });

        listview.page.add_inner_button(__('Cleanup Old Errors'), function () {
            frappe.confirm(
                __('This will archive errors older than 90 days. Continue?'),
                function () {
                    frappe.call({
                        method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.cleanup_old_errors',
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Cleaned up {0} old errors', [r.message]),
                                    indicator: 'green'
                                });
                                listview.refresh();
                            }
                        }
                    });
                }
            );
        });
    }
};

// ============ Global Error Handling ============

$(document).ready(function () {
    // Set up global error handler for automatic error logging
    window.addEventListener('error', function (event) {
        // Log JavaScript errors automatically
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.error_logger.error_logger.log_system_error',
            args: {
                error_title: 'JavaScript Error: ' + event.error.name,
                error_message: event.error.message,
                severity_level: 'Medium / متوسط',
                error_category: 'Frontend Error / خطأ الواجهة الأمامية',
                file_path: event.filename,
                line_number: event.lineno,
                stack_trace: event.error.stack
            },
            callback: function (r) {
                if (r.message) {
                    console.log('Error logged with ID:', r.message);
                }
            }
        });
    });
});
