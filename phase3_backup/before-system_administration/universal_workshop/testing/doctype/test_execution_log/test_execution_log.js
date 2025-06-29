// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Execution Log', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('update_execution_dashboard');
        frm.trigger('setup_real_time_updates');
    },

    onload: function (frm) {
        frm.trigger('load_test_case_details');
        frm.trigger('setup_step_result_grid');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['execution_summary_ar', 'failure_details_ar', 'recommendations_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Generate Report button
            frm.add_custom_button(__('Generate Report'), function () {
                frm.trigger('generate_execution_report');
            }, __('Reports'));

            // Compare with Previous button
            frm.add_custom_button(__('Compare with Previous'), function () {
                frm.trigger('compare_with_previous');
            }, __('Analysis'));

            // View Test Case button
            if (frm.doc.test_case) {
                frm.add_custom_button(__('View Test Case'), function () {
                    frappe.set_route('Form', 'System Test Case', frm.doc.test_case);
                }, __('Navigation'));
            }

            // Export Results button
            frm.add_custom_button(__('Export Results'), function () {
                frm.trigger('export_execution_results');
            }, __('Export'));

            // Status-specific buttons
            if (frm.doc.execution_status === 'Failed') {
                frm.add_custom_button(__('Create Defect Report'), function () {
                    frm.trigger('create_defect_report');
                }, __('Actions'));

                frm.add_custom_button(__('Schedule Retest'), function () {
                    frm.trigger('schedule_retest');
                }, __('Actions'));
            }

            if (frm.doc.execution_status === 'In Progress') {
                frm.add_custom_button(__('Complete Execution'), function () {
                    frm.trigger('complete_execution');
                }, __('Actions')).addClass('btn-primary');

                frm.add_custom_button(__('Abort Execution'), function () {
                    frm.trigger('abort_execution');
                }, __('Actions')).addClass('btn-danger');
            }

            // Compliance buttons
            if (frm.doc.execution_status === 'Passed') {
                frm.add_custom_button(__('Mark Compliance Validated'), function () {
                    frm.trigger('mark_compliance_validated');
                }, __('Compliance'));
            }
        }
    },

    update_execution_dashboard: function (frm) {
        if (frm.doc.test_results && frm.doc.test_results.length > 0) {
            frm.trigger('show_execution_summary');
            frm.trigger('show_step_progress');
            frm.trigger('show_performance_metrics');
        }
    },

    setup_real_time_updates: function (frm) {
        if (frm.doc.execution_status === 'In Progress') {
            // Set up periodic refresh for in-progress executions
            frm.execution_timer = setInterval(function () {
                frm.reload_doc();
            }, 30000); // Refresh every 30 seconds

            // Clean up timer on form close
            $(window).on('beforeunload', function () {
                if (frm.execution_timer) {
                    clearInterval(frm.execution_timer);
                }
            });
        }
    },

    load_test_case_details: function (frm) {
        if (frm.doc.test_case && frm.doc.__islocal) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'System Test Case',
                    name: frm.doc.test_case
                },
                callback: function (r) {
                    if (r.message) {
                        frm.trigger('populate_from_test_case', r.message);
                    }
                }
            });
        }
    },

    setup_step_result_grid: function (frm) {
        // Customize the step results grid
        if (frm.fields_dict.test_results && frm.fields_dict.test_results.grid) {
            frm.fields_dict.test_results.grid.get_field('step_status').get_query = function () {
                return {
                    filters: {
                        'name': ['in', ['Passed', 'Failed', 'Blocked', 'Skipped', 'Not Executed']]
                    }
                };
            };
        }
    },

    // Field change handlers
    test_case: function (frm) {
        if (frm.doc.test_case) {
            frm.trigger('load_test_case_details');
        }
    },

    execution_status: function (frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('validate_status_change');

        if (frm.doc.execution_status === 'Failed') {
            frm.set_value('follow_up_required', 1);
        }
    },

    steps_passed: function (frm) {
        frm.trigger('calculate_success_rate');
    },

    steps_failed: function (frm) {
        frm.trigger('calculate_success_rate');
    },

    // Custom methods
    populate_from_test_case: function (frm, test_case) {
        // Populate execution log from test case details
        frm.set_value('test_case_title', test_case.test_case_title);
        frm.set_value('test_environment', test_case.test_environment || 'Testing');

        // Initialize step results from test case steps
        if (test_case.test_steps && test_case.test_steps.length > 0) {
            frm.clear_table('test_results');

            test_case.test_steps.forEach(function (step) {
                let row = frm.add_child('test_results');
                row.step_number = step.step_number;
                row.step_title = step.step_title;
                row.step_status = 'Not Executed';
                row.expected_result = step.expected_result;
                row.actual_result = '';
            });

            frm.refresh_field('test_results');
            frm.set_value('steps_executed', test_case.test_steps.length);
        }
    },

    generate_execution_report: function (frm) {
        frappe.call({
            method: 'generate_execution_report',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.trigger('show_execution_report_dialog', r.message);
                }
            }
        });
    },

    compare_with_previous: function (frm) {
        frappe.call({
            method: 'compare_with_previous_execution',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.trigger('show_comparison_dialog', r.message);
                }
            }
        });
    },

    export_execution_results: function (frm) {
        frappe.call({
            method: 'universal_workshop.testing.utils.export_execution_results',
            args: {
                execution_log: frm.doc.name
            },
            callback: function (r) {
                if (r.message && r.message.file_url) {
                    frappe.msgprint(__('Export completed. <a href="{0}" target="_blank">Download File</a>', [r.message.file_url]));
                }
            }
        });
    },

    create_defect_report: function (frm) {
        // Create defect reports for failed steps
        let failed_steps = frm.doc.test_results.filter(step => step.step_status === 'Failed');

        if (failed_steps.length === 0) {
            frappe.msgprint(__('No failed steps found to create defect reports'));
            return;
        }

        frappe.prompt([
            {
                label: __('Create defect for which steps?'),
                fieldname: 'step_numbers',
                fieldtype: 'MultiSelect',
                options: failed_steps.map(step => step.step_number).join('\n'),
                reqd: 1
            }
        ], function (values) {
            frm.trigger('create_defects_for_steps', values.step_numbers);
        }, __('Create Defect Reports'), __('Create'));
    },

    schedule_retest: function (frm) {
        frappe.prompt([
            {
                label: __('Retest Date'),
                fieldname: 'retest_date',
                fieldtype: 'Date',
                reqd: 1,
                default: frappe.datetime.add_days(frappe.datetime.get_today(), 3)
            },
            {
                label: __('Retest Notes'),
                fieldname: 'retest_notes',
                fieldtype: 'Text',
                description: __('Additional notes for the retest')
            }
        ], function (values) {
            frm.set_value('retesting_required', 1);
            frm.set_value('next_execution_scheduled', values.retest_date);
            frm.set_value('recommendations',
                (frm.doc.recommendations || '') + '\n\nRetest scheduled for: ' + values.retest_date +
                (values.retest_notes ? '\nNotes: ' + values.retest_notes : ''));
            frm.save();
        }, __('Schedule Retest'), __('Schedule'));
    },

    complete_execution: function (frm) {
        // Validate that all steps have been executed
        let unexecuted_steps = frm.doc.test_results.filter(step => step.step_status === 'Not Executed');

        if (unexecuted_steps.length > 0) {
            frappe.msgprint(__('Please complete all test steps before marking execution as complete'));
            return;
        }

        frappe.confirm(__('Mark this test execution as complete?'), function () {
            // Determine final status based on step results
            let failed_steps = frm.doc.test_results.filter(step => step.step_status === 'Failed');
            let blocked_steps = frm.doc.test_results.filter(step => step.step_status === 'Blocked');

            let final_status = 'Passed';
            if (blocked_steps.length > 0) {
                final_status = 'Blocked';
            } else if (failed_steps.length > 0) {
                final_status = 'Failed';
            }

            frm.set_value('execution_status', final_status);
            frm.save();
        });
    },

    abort_execution: function (frm) {
        frappe.confirm(__('Are you sure you want to abort this test execution?'), function () {
            frm.set_value('execution_status', 'Aborted');
            frm.set_value('execution_summary',
                (frm.doc.execution_summary || '') + '\n\nExecution aborted by user at: ' + frappe.datetime.now_datetime());
            frm.save();
        });
    },

    mark_compliance_validated: function (frm) {
        let compliance_dialog = new frappe.ui.Dialog({
            title: __('Mark Compliance Validated'),
            fields: [
                {
                    label: __('Arabic Localization'),
                    fieldname: 'arabic_localization_validated',
                    fieldtype: 'Check',
                    default: frm.doc.arabic_localization_validated
                },
                {
                    label: __('Oman VAT Compliance'),
                    fieldname: 'oman_vat_compliance_validated',
                    fieldtype: 'Check',
                    default: frm.doc.oman_vat_compliance_validated
                },
                {
                    label: __('Environmental Compliance'),
                    fieldname: 'environmental_compliance_validated',
                    fieldtype: 'Check',
                    default: frm.doc.environmental_compliance_validated
                },
                {
                    label: __('Security Validation'),
                    fieldname: 'security_validation_passed',
                    fieldtype: 'Check',
                    default: frm.doc.security_validation_passed
                },
                {
                    label: __('Performance Benchmarks'),
                    fieldname: 'performance_benchmarks_met',
                    fieldtype: 'Check',
                    default: frm.doc.performance_benchmarks_met
                },
                {
                    label: __('Integration Points'),
                    fieldname: 'integration_points_validated',
                    fieldtype: 'Check',
                    default: frm.doc.integration_points_validated
                },
                {
                    label: __('Audit Trail'),
                    fieldname: 'audit_trail_verified',
                    fieldtype: 'Check',
                    default: frm.doc.audit_trail_verified
                }
            ],
            primary_action_label: __('Update'),
            primary_action: function () {
                let values = compliance_dialog.get_values();

                Object.keys(values).forEach(function (key) {
                    frm.set_value(key, values[key]);
                });

                frm.save();
                compliance_dialog.hide();
            }
        });

        compliance_dialog.show();
    },

    // Helper methods
    calculate_success_rate: function (frm) {
        if (frm.doc.steps_executed > 0) {
            let success_rate = (frm.doc.steps_passed / frm.doc.steps_executed) * 100;

            // Update performance metrics
            if (frm.doc.performance_metrics) {
                try {
                    let metrics = JSON.parse(frm.doc.performance_metrics);
                    metrics.success_rate = success_rate.toFixed(2);
                    frm.set_value('performance_metrics', JSON.stringify(metrics, null, 2));
                } catch (e) {
                    console.log('Error updating performance metrics:', e);
                }
            }
        }
    },

    validate_status_change: function (frm) {
        // Validate status changes
        if (frm.doc.execution_status === 'Passed' && frm.doc.steps_failed > 0) {
            frappe.msgprint(__('Cannot mark as Passed when there are failed steps'), 'warning');
        }

        if (frm.doc.execution_status === 'Failed' && !frm.doc.failure_details) {
            frappe.msgprint(__('Please provide failure details for failed executions'), 'warning');
        }
    },

    show_execution_summary: function (frm) {
        let total_steps = frm.doc.steps_executed || 0;
        let passed_steps = frm.doc.steps_passed || 0;
        let failed_steps = frm.doc.steps_failed || 0;
        let success_rate = total_steps > 0 ? (passed_steps / total_steps * 100).toFixed(1) : 0;

        let status_color = frm.doc.execution_status === 'Passed' ? 'green' :
            frm.doc.execution_status === 'Failed' ? 'red' : 'orange';

        let summary_html = `
            <div class="execution-summary" style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <div class="row">
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="color: ${status_color}; margin: 0;">${frm.doc.execution_status}</h3>
                            <small>${__('Status')}</small>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="margin: 0;">${total_steps}</h3>
                            <small>${__('Total Steps')}</small>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="color: green; margin: 0;">${passed_steps}</h3>
                            <small>${__('Passed')}</small>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="color: red; margin: 0;">${failed_steps}</h3>
                            <small>${__('Failed')}</small>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="margin: 0;">${success_rate}%</h3>
                            <small>${__('Success Rate')}</small>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="text-center">
                            <h3 style="margin: 0;">${frm.doc.execution_duration || 0}m</h3>
                            <small>${__('Duration')}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        frm.get_field('execution_details_section').$wrapper.prepend(summary_html);
    },

    show_step_progress: function (frm) {
        if (frm.doc.test_results && frm.doc.test_results.length > 0) {
            let progress_html = '<div class="step-progress" style="margin: 10px 0;"><h5>' + __('Step Progress') + '</h5>';

            frm.doc.test_results.forEach(function (step) {
                let status_class = step.step_status === 'Passed' ? 'success' :
                    step.step_status === 'Failed' ? 'danger' :
                        step.step_status === 'Blocked' ? 'warning' : 'default';

                progress_html += `
                    <div style="margin: 5px 0;">
                        <span class="label label-${status_class}">${step.step_number}</span>
                        <span style="margin-left: 10px;">${step.step_title}</span>
                        <span class="pull-right">${step.execution_time || 0}s</span>
                    </div>
                `;
            });

            progress_html += '</div>';
            frm.get_field('results_section').$wrapper.prepend(progress_html);
        }
    },

    show_performance_metrics: function (frm) {
        if (frm.doc.performance_metrics) {
            try {
                let metrics = JSON.parse(frm.doc.performance_metrics);

                let metrics_html = `
                    <div class="performance-metrics" style="margin: 10px 0; padding: 10px; background: #f9f9f9;">
                        <h5>${__('Performance Metrics')}</h5>
                        <div class="row">
                            <div class="col-md-3">
                                <strong>${__('Avg Step Time')}:</strong> ${(metrics.average_step_time || 0).toFixed(1)}s
                            </div>
                            <div class="col-md-3">
                                <strong>${__('Screenshots')}:</strong> ${metrics.screenshots_count || 0}
                            </div>
                            <div class="col-md-3">
                                <strong>${__('Errors')}:</strong> ${metrics.errors_count || 0}
                            </div>
                            <div class="col-md-3">
                                <strong>${__('Success Rate')}:</strong> ${metrics.success_rate || 0}%
                            </div>
                        </div>
                `;

                if (metrics.average_api_response) {
                    metrics_html += `
                        <div class="row" style="margin-top: 10px;">
                            <div class="col-md-6">
                                <strong>${__('Avg API Response')}:</strong> ${metrics.average_api_response.toFixed(1)}ms
                            </div>
                            <div class="col-md-6">
                                <strong>${__('Max API Response')}:</strong> ${metrics.max_api_response || 0}ms
                            </div>
                        </div>
                    `;
                }

                metrics_html += '</div>';
                frm.get_field('technical_details_section').$wrapper.prepend(metrics_html);

            } catch (e) {
                console.log('Error parsing performance metrics:', e);
            }
        }
    },

    show_execution_report_dialog: function (frm, report_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Execution Report'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'report_html'
                }
            ]
        });

        let report_html = frm.trigger('format_execution_report', report_data);
        dialog.fields_dict.report_html.$wrapper.html(report_html);
        dialog.show();
    },

    show_comparison_dialog: function (frm, comparison_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Comparison with Previous Execution'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'comparison_html'
                }
            ]
        });

        let comparison_html = frm.trigger('format_comparison_report', comparison_data);
        dialog.fields_dict.comparison_html.$wrapper.html(comparison_html);
        dialog.show();
    },

    format_execution_report: function (frm, data) {
        return `
            <div class="execution-report">
                <h3>${data.execution_info.test_case_title}</h3>
                <p><strong>${__('Execution Date')}:</strong> ${data.execution_info.execution_date}</p>
                <p><strong>${__('Executed By')}:</strong> ${data.execution_info.executed_by}</p>
                <p><strong>${__('Status')}:</strong> <span class="label label-${data.execution_info.execution_status === 'Passed' ? 'success' : 'danger'}">${data.execution_info.execution_status}</span></p>
                
                <h4>${__('Results Summary')}</h4>
                <table class="table table-bordered">
                    <tr><td><strong>${__('Steps Executed')}:</strong></td><td>${data.results_summary.steps_executed}</td></tr>
                    <tr><td><strong>${__('Steps Passed')}:</strong></td><td>${data.results_summary.steps_passed}</td></tr>
                    <tr><td><strong>${__('Steps Failed')}:</strong></td><td>${data.results_summary.steps_failed}</td></tr>
                    <tr><td><strong>${__('Success Rate')}:</strong></td><td>${data.results_summary.success_rate}%</td></tr>
                    <tr><td><strong>${__('Defects Found')}:</strong></td><td>${data.results_summary.defects_found}</td></tr>
                </table>
                
                <h4>${__('Compliance Summary')}</h4>
                <ul>
                    ${Object.keys(data.compliance_summary).map(key =>
            `<li>${key.replace(/_/g, ' ')}: ${data.compliance_summary[key] ? '✓' : '✗'}</li>`
        ).join('')}
                </ul>
                
                ${data.defect_summary.length > 0 ? `
                    <h4>${__('Defects Found')}</h4>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>${__('Title')}</th>
                                <th>${__('Severity')}</th>
                                <th>${__('Type')}</th>
                                <th>${__('Module')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.defect_summary.map(defect => `
                                <tr>
                                    <td>${defect.title}</td>
                                    <td><span class="label label-${defect.severity === 'Critical' ? 'danger' : 'warning'}">${defect.severity}</span></td>
                                    <td>${defect.type}</td>
                                    <td>${defect.module}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                ` : ''}
            </div>
        `;
    },

    format_comparison_report: function (frm, data) {
        if (data.message) {
            return `<p>${data.message}</p>`;
        }

        return `
            <div class="comparison-report">
                <h4>${__('Comparison with Previous Execution')}</h4>
                <p><strong>${__('Previous Execution')}:</strong> ${data.previous_execution}</p>
                
                <table class="table table-bordered">
                    <tr>
                        <td><strong>${__('Status Change')}:</strong></td>
                        <td>${data.status_change.previous} → ${data.status_change.current} 
                            ${data.status_change.improved ? '<span class="label label-success">Improved</span>' : ''}
                        </td>
                    </tr>
                    <tr>
                        <td><strong>${__('Duration Change')}:</strong></td>
                        <td>${data.duration_change.previous}m → ${data.duration_change.current}m 
                            (${data.duration_change.difference > 0 ? '+' : ''}${data.duration_change.difference}m)
                        </td>
                    </tr>
                    <tr>
                        <td><strong>${__('Steps Passed Change')}:</strong></td>
                        <td>${data.steps_comparison.passed_change > 0 ? '+' : ''}${data.steps_comparison.passed_change}</td>
                    </tr>
                    <tr>
                        <td><strong>${__('Steps Failed Change')}:</strong></td>
                        <td>${data.steps_comparison.failed_change > 0 ? '+' : ''}${data.steps_comparison.failed_change}</td>
                    </tr>
                </table>
                
                ${data.performance_comparison ? `
                    <h5>${__('Performance Comparison')}</h5>
                    <p><strong>${__('Success Rate Change')}:</strong> ${data.performance_comparison.success_rate_change > 0 ? '+' : ''}${data.performance_comparison.success_rate_change}%</p>
                    ${data.performance_comparison.api_response_improvement ? `
                        <p><strong>${__('API Response Improvement')}:</strong> ${data.performance_comparison.api_response_improvement.improvement_percent}%</p>
                    ` : ''}
                ` : ''}
            </div>
        `;
    },

    create_defects_for_steps: function (frm, step_numbers) {
        let selected_steps = step_numbers.split(',').map(num => parseInt(num));
        let failed_steps = frm.doc.test_results.filter(step =>
            selected_steps.includes(step.step_number) && step.step_status === 'Failed');

        failed_steps.forEach(function (step) {
            // Create defect record for each failed step
            frappe.call({
                method: 'universal_workshop.testing.utils.create_defect_from_step',
                args: {
                    execution_log: frm.doc.name,
                    step_result: step
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Defect created for step {0}', [step.step_number]));
                    }
                }
            });
        });
    }
});

// Child table events for test step results
frappe.ui.form.on('Test Step Result', {
    step_status: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Auto-update parent counters
        frm.trigger('calculate_success_rate');

        // Require error message for failed steps
        if (row.step_status === 'Failed' && !row.error_message) {
            frappe.msgprint(__('Please provide an error message for failed steps'));
        }

        // Auto-set screenshot requirement for failed/blocked steps
        if (row.step_status === 'Failed' || row.step_status === 'Blocked') {
            frappe.model.set_value(cdt, cdn, 'screenshot_required', 1);
        }
    },

    execution_time: function (frm, cdt, cdn) {
        // Update total execution time
        let total_time = 0;
        frm.doc.test_results.forEach(function (step) {
            total_time += step.execution_time || 0;
        });

        if (total_time > 0) {
            frm.set_value('execution_duration', Math.max(1, Math.round(total_time / 60)));
        }
    }
}); 