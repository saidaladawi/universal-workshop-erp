// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Report Schedule', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_status_indicator');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['schedule_name_ar', 'email_subject_ar', 'email_body_ar'].forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    setup_custom_buttons: function (frm) {
        // Add custom buttons based on status
        if (frm.doc.name && !frm.is_new()) {
            // Test Report button
            frm.add_custom_button(__('Test Report'), function () {
                frm.trigger('test_report_execution');
            }, __('Actions'));

            // View Execution History button
            frm.add_custom_button(__('Execution History'), function () {
                frm.trigger('show_execution_history');
            }, __('View'));

            // View Statistics button
            frm.add_custom_button(__('Statistics'), function () {
                frm.trigger('show_statistics');
            }, __('View'));

            if (frm.doc.status === 'Active') {
                // Execute Now button
                frm.add_custom_button(__('Execute Now'), function () {
                    frm.trigger('execute_now');
                }, __('Actions'));

                // Pause Schedule button
                frm.add_custom_button(__('Pause Schedule'), function () {
                    frm.trigger('pause_schedule');
                }, __('Actions'));
            }

            if (frm.doc.status === 'Paused') {
                // Resume Schedule button
                frm.add_custom_button(__('Resume Schedule'), function () {
                    frm.trigger('resume_schedule');
                }, __('Actions'));
            }
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on selections
        frm.trigger('toggle_frequency_fields');
        frm.trigger('toggle_delivery_fields');
        frm.trigger('toggle_email_fields');
    },

    update_status_indicator: function (frm) {
        if (frm.doc.status) {
            let color_map = {
                'Active': 'green',
                'Inactive': 'grey',
                'Paused': 'orange',
                'Expired': 'red',
                'Error': 'red'
            };
            frm.dashboard.set_headline_alert(
                `Status: ${frm.doc.status}`,
                color_map[frm.doc.status] || 'blue'
            );
        }

        // Show next execution time
        if (frm.doc.next_execution_time && frm.doc.status === 'Active') {
            let next_exec = moment(frm.doc.next_execution_time).format('DD-MM-YYYY HH:mm');
            frm.dashboard.add_comment(__('Next Execution: {0}', [next_exec]), 'blue', true);
        }
    },

    // Field change handlers
    frequency: function (frm) {
        frm.trigger('toggle_frequency_fields');
        frm.trigger('calculate_next_execution');
    },

    delivery_method: function (frm) {
        frm.trigger('toggle_delivery_fields');
    },

    report_name: function (frm) {
        if (frm.doc.report_name) {
            frm.trigger('load_report_details');
        }
    },

    status: function (frm) {
        frm.trigger('update_status_indicator');
    },

    execution_time: function (frm) {
        frm.trigger('calculate_next_execution');
    },

    day_of_week: function (frm) {
        if (frm.doc.frequency === 'Weekly') {
            frm.trigger('calculate_next_execution');
        }
    },

    day_of_month: function (frm) {
        if (frm.doc.frequency === 'Monthly') {
            frm.trigger('calculate_next_execution');
        }
    },

    // Custom functions
    toggle_frequency_fields: function (frm) {
        // Show/hide frequency-specific fields
        frm.toggle_display('day_of_week', frm.doc.frequency === 'Weekly');
        frm.toggle_display('day_of_month', frm.doc.frequency === 'Monthly');
        frm.toggle_display('cron_expression', frm.doc.frequency === 'Custom Cron');

        // Set field requirements
        frm.toggle_reqd('day_of_week', frm.doc.frequency === 'Weekly');
        frm.toggle_reqd('day_of_month', frm.doc.frequency === 'Monthly');
        frm.toggle_reqd('cron_expression', frm.doc.frequency === 'Custom Cron');
    },

    toggle_delivery_fields: function (frm) {
        let is_email = frm.doc.delivery_method === 'Email';

        // Email-specific fields
        frm.toggle_display('email_recipients', is_email);
        frm.toggle_display('email_subject', is_email);
        frm.toggle_display('email_body', is_email);
        frm.toggle_display('sender_email_account', is_email);

        // Arabic email fields
        frm.toggle_display('email_subject_ar', is_email);
        frm.toggle_display('email_body_ar', is_email);

        // Set requirements
        frm.toggle_reqd('email_recipients', is_email);
    },

    toggle_email_fields: function (frm) {
        // Show Arabic email fields if Arabic language is selected
        let show_arabic = frappe.boot.lang === 'ar' || frm.doc.include_arabic_content;
        frm.toggle_display('email_subject_ar', show_arabic && frm.doc.delivery_method === 'Email');
        frm.toggle_display('email_body_ar', show_arabic && frm.doc.delivery_method === 'Email');
    },

    load_report_details: function (frm) {
        if (!frm.doc.report_name) return;

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Report',
                name: frm.doc.report_name
            },
            callback: function (r) {
                if (r.message) {
                    let report = r.message;

                    // Update report type info
                    frm.dashboard.add_comment(
                        __('Report Type: {0}', [report.report_type]),
                        'blue',
                        true
                    );

                    // Load available filters for this report
                    frm.trigger('load_report_filters');
                }
            }
        });
    },

    load_report_filters: function (frm) {
        if (!frm.doc.report_name) return;

        frappe.call({
            method: 'frappe.desk.query_report.get_script',
            args: {
                report_name: frm.doc.report_name
            },
            callback: function (r) {
                if (r.message && r.message.filters) {
                    // Show available filters in help text
                    let filter_names = r.message.filters.map(f => f.fieldname || f.label).join(', ');
                    frm.set_df_property('report_filters', 'description',
                        __('Available filters: {0}', [filter_names]));
                }
            }
        });
    },

    calculate_next_execution: function (frm) {
        if (!frm.doc.frequency || !frm.doc.execution_time) return;

        // This is a simplified calculation - the actual calculation is done server-side
        let now = frappe.datetime.now_datetime();
        let next_exec = __('Will be calculated on save');

        frm.set_value('next_execution_time', null);
        frm.dashboard.add_comment(__('Next execution time will be calculated when saved'), 'blue', true);
    },

    test_report_execution: function (frm) {
        if (!frm.doc.name) {
            frappe.msgprint(__('Please save the schedule first'));
            return;
        }

        frappe.show_alert({
            message: __('Testing report execution...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.report_schedule.report_schedule.test_report_execution',
            args: {
                report_schedule_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __('Test execution completed successfully'),
                            indicator: 'green'
                        });

                        // Show execution details
                        frappe.msgprint({
                            title: __('Test Execution Result'),
                            message: `
                                <div class="test-execution-result">
                                    <p><strong>${__('Execution ID')}:</strong> ${r.message.execution_id}</p>
                                    <p><strong>${__('File Generated')}:</strong> ${r.message.file_path ? __('Yes') : __('No')}</p>
                                    <p><strong>${__('Delivery Status')}:</strong> ${r.message.delivery_result ? r.message.delivery_result.message : __('N/A')}</p>
                                </div>
                            `,
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Test execution failed: {0}', [r.message.error]),
                            indicator: 'red'
                        });
                    }
                }
            },
            error: function (xhr) {
                frappe.show_alert({
                    message: __('Test execution failed'),
                    indicator: 'red'
                });
            }
        });
    },

    execute_now: function (frm) {
        frappe.confirm(
            __('Are you sure you want to execute this report now?'),
            function () {
                frappe.show_alert({
                    message: __('Executing report...'),
                    indicator: 'blue'
                });

                frappe.call({
                    method: 'universal_workshop.reports_analytics.doctype.report_schedule.report_schedule.execute_scheduled_report',
                    args: {
                        report_schedule_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Report executed successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        } else {
                            frappe.show_alert({
                                message: __('Report execution failed'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        );
    },

    pause_schedule: function (frm) {
        frappe.confirm(
            __('Are you sure you want to pause this schedule?'),
            function () {
                frm.set_value('status', 'Paused');
                frm.save();
            }
        );
    },

    resume_schedule: function (frm) {
        frappe.confirm(
            __('Are you sure you want to resume this schedule?'),
            function () {
                frm.set_value('status', 'Active');
                frm.save();
            }
        );
    },

    show_execution_history: function (frm) {
        frappe.route_options = {
            "parent": frm.doc.name
        };
        frappe.set_route("List", "Report Schedule Execution");
    },

    show_statistics: function (frm) {
        frappe.call({
            method: 'universal_workshop.reports_analytics.doctype.report_schedule_execution.report_schedule_execution.get_execution_statistics',
            args: {
                report_schedule: frm.doc.name,
                days: 30
            },
            callback: function (r) {
                if (r.message) {
                    let stats = r.message;
                    let html = `
                        <div class="execution-statistics">
                            <h4>${__('Execution Statistics (Last 30 Days)')}</h4>
                            <table class="table table-bordered">
                                <tr>
                                    <td><strong>${__('Total Executions')}</strong></td>
                                    <td>${stats.total_executions}</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Successful Executions')}</strong></td>
                                    <td>${stats.successful_executions}</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Failed Executions')}</strong></td>
                                    <td>${stats.failed_executions}</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Success Rate')}</strong></td>
                                    <td>${stats.success_rate.toFixed(2)}%</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Average Duration')}</strong></td>
                                    <td>${stats.average_duration.toFixed(2)} seconds</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Total Rows Generated')}</strong></td>
                                    <td>${stats.total_rows_generated}</td>
                                </tr>
                                <tr>
                                    <td><strong>${__('Delivery Success Rate')}</strong></td>
                                    <td>${stats.delivery_success_rate.toFixed(2)}%</td>
                                </tr>
                            </table>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('Execution Statistics'),
                        message: html,
                        wide: true
                    });
                }
            }
        });
    }
});

// Child table handlers
frappe.ui.form.on('Report Schedule Execution', {
    // Handle child table events if needed
});

// Custom validation functions
frappe.ui.form.on('Report Schedule', {
    validate: function (frm) {
        // Validate cron expression if Custom Cron is selected
        if (frm.doc.frequency === 'Custom Cron' && frm.doc.cron_expression) {
            frm.trigger('validate_cron_expression');
        }

        // Validate email addresses
        if (frm.doc.delivery_method === 'Email' && frm.doc.email_recipients) {
            frm.trigger('validate_email_addresses');
        }

        // Validate date ranges
        if (frm.doc.schedule_start_date && frm.doc.schedule_end_date) {
            if (frappe.datetime.get_diff(frm.doc.schedule_end_date, frm.doc.schedule_start_date) < 0) {
                frappe.validated = false;
                frappe.msgprint(__('End date cannot be before start date'));
            }
        }
    },

    validate_cron_expression: function (frm) {
        // Basic cron expression validation (5 parts separated by spaces)
        let cron_parts = frm.doc.cron_expression.trim().split(/\s+/);
        if (cron_parts.length !== 5) {
            frappe.validated = false;
            frappe.msgprint(__('Cron expression must have 5 parts: minute hour day month weekday'));
        }
    },

    validate_email_addresses: function (frm) {
        let emails = frm.doc.email_recipients.split(',');
        let email_regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        for (let email of emails) {
            email = email.trim();
            if (email && !email_regex.test(email)) {
                frappe.validated = false;
                frappe.msgprint(__('Invalid email address: {0}', [email]));
                break;
            }
        }
    }
});

// Utility functions
function format_execution_time(execution_time) {
    if (!execution_time) return '';
    return moment(execution_time).format('DD-MM-YYYY HH:mm:ss');
}

function get_status_color(status) {
    const color_map = {
        'Queued': 'blue',
        'Running': 'orange',
        'Completed': 'green',
        'Failed': 'red',
        'Cancelled': 'grey',
        'Retrying': 'yellow'
    };
    return color_map[status] || 'blue';
} 