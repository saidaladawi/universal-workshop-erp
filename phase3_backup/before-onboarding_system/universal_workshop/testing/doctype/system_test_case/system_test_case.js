// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('System Test Case', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_status_indicators');
        frm.trigger('load_execution_metrics');
    },

    onload: function (frm) {
        frm.trigger('setup_filters');
        frm.trigger('load_test_templates');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['test_case_title_ar', 'test_description_ar', 'test_objective_ar',
            'prerequisites_ar', 'expected_results_ar', 'arabic_localization_checks'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css({
                        'text-align': 'right',
                        'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                    });
                }
            });

        // Auto-detect text direction for mixed content
        ['test_description', 'test_objective', 'prerequisites', 'expected_results'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('input', function () {
                    let text = $(this).val();
                    let direction = frm.trigger('detect_text_direction', text);
                    $(this).attr('dir', direction);
                });
            }
        });
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Execute Test button
            if (frm.doc.test_status === 'Ready for Testing') {
                frm.add_custom_button(__('Execute Test'), function () {
                    frm.trigger('execute_test_case');
                }, __('Testing'));
            }

            // Clone Test Case button
            frm.add_custom_button(__('Clone Test Case'), function () {
                frm.trigger('clone_test_case');
            }, __('Actions'));

            // Generate Report button
            frm.add_custom_button(__('Generate Report'), function () {
                frm.trigger('generate_test_report');
            }, __('Reports'));

            // View Execution History button
            frm.add_custom_button(__('Execution History'), function () {
                frm.trigger('show_execution_history');
            }, __('Testing'));

            // Automation buttons
            if (frm.doc.test_type === 'Automated' || frm.doc.test_type === 'Semi-Automated') {
                frm.add_custom_button(__('Generate Script'), function () {
                    frm.trigger('generate_automation_script');
                }, __('Automation'));

                if (frm.doc.automation_script_path) {
                    frm.add_custom_button(__('Run Automated Test'), function () {
                        frm.trigger('run_automated_test');
                    }, __('Automation'));
                }
            }

            // Compliance buttons
            if (frm.doc.oman_vat_compliance || frm.doc.environmental_compliance ||
                frm.doc.arabic_localization_checks) {
                frm.add_custom_button(__('Compliance Checklist'), function () {
                    frm.trigger('show_compliance_checklist');
                }, __('Compliance'));
            }
        }

        // Quick action buttons in list view
        if (frm.doc.test_status === 'Draft') {
            frm.add_custom_button(__('Mark Ready'), function () {
                frm.set_value('test_status', 'Ready for Testing');
                frm.save();
            }).addClass('btn-primary');
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on test type
        frm.toggle_display(['automation_script_path'],
            frm.doc.test_type === 'Automated' || frm.doc.test_type === 'Semi-Automated');

        // Show/hide compliance fields based on checkboxes
        frm.toggle_display(['arabic_localization_checks'], frm.doc.arabic_report_validation);
        frm.toggle_display(['compliance_checks'],
            frm.doc.oman_vat_compliance || frm.doc.environmental_compliance);

        // Performance fields visibility
        frm.toggle_display(['performance_benchmarks'],
            frm.doc.test_category === 'Performance Testing');

        // API testing fields
        frm.toggle_display(['api_endpoints'],
            frm.doc.test_type === 'API Testing' || frm.doc.api_integrations);
    },

    update_status_indicators: function (frm) {
        // Add status indicators and progress bars
        if (!frm.doc.__islocal) {
            frm.trigger('show_execution_metrics');
            frm.trigger('show_compliance_status');
            frm.trigger('show_test_progress');
        }
    },

    setup_filters: function (frm) {
        // Set filters for linked fields
        frm.set_query('reviewer', function () {
            return {
                filters: {
                    'enabled': 1,
                    'user_type': 'System User'
                }
            };
        });

        frm.set_query('approved_by', function () {
            return {
                filters: {
                    'enabled': 1,
                    'user_type': 'System User'
                }
            };
        });
    },

    load_test_templates: function (frm) {
        // Load test case templates based on module and category
        if (frm.doc.__islocal && frm.doc.test_module && frm.doc.test_category) {
            frappe.call({
                method: 'universal_workshop.testing.utils.get_test_templates',
                args: {
                    module: frm.doc.test_module,
                    category: frm.doc.test_category
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frm.trigger('show_template_selection', r.message);
                    }
                }
            });
        }
    },

    // Field change handlers
    test_module: function (frm) {
        frm.trigger('load_test_templates');
        frm.trigger('update_module_specific_fields');
    },

    test_category: function (frm) {
        frm.trigger('load_test_templates');
        frm.trigger('setup_field_dependencies');
        frm.trigger('set_category_defaults');
    },

    test_type: function (frm) {
        frm.trigger('setup_field_dependencies');
        if (frm.doc.test_type === 'Automated') {
            frm.set_value('automated_test_available', 1);
        }
    },

    test_priority: function (frm) {
        frm.trigger('validate_priority_category_combination');
        frm.trigger('set_priority_defaults');
    },

    // Custom methods
    execute_test_case: function (frm) {
        frappe.prompt([
            {
                label: __('Execution Notes'),
                fieldname: 'execution_notes',
                fieldtype: 'Text',
                reqd: 0
            },
            {
                label: __('Test Environment'),
                fieldname: 'test_environment',
                fieldtype: 'Select',
                options: 'Development\nTesting\nStaging\nProduction',
                default: 'Development',
                reqd: 1
            }
        ], function (data) {
            frappe.call({
                method: 'execute_test_case',
                doc: frm.doc,
                args: {
                    execution_notes: data.execution_notes,
                    test_environment: data.test_environment
                },
                callback: function (r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint(__('Test execution started successfully'));
                        frm.trigger('load_execution_metrics');

                        // Open the execution log
                        if (r.message.execution_log) {
                            frappe.set_route('Form', 'Test Execution Log', r.message.execution_log);
                        }
                    } else {
                        frappe.msgprint(__('Failed to start test execution: {0}', [r.message.message || 'Unknown error']));
                    }
                }
            });
        }, __('Execute Test Case'), __('Execute'));
    },

    clone_test_case: function (frm) {
        frappe.prompt([
            {
                label: __('New Test Case Title'),
                fieldname: 'new_title',
                fieldtype: 'Data',
                reqd: 1,
                default: frm.doc.test_case_title + ' - Copy'
            }
        ], function (values) {
            frappe.call({
                method: 'clone_test_case',
                doc: frm.doc,
                args: {
                    new_title: values.new_title
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Test case cloned successfully'));
                        frappe.set_route('Form', 'System Test Case', r.message);
                    }
                }
            });
        }, __('Clone Test Case'), __('Clone'));
    },

    generate_test_report: function (frm) {
        frappe.call({
            method: 'generate_test_report',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_test_report', r.message);
                }
            }
        });
    },

    view_execution_history: function (frm) {
        frappe.route_options = {
            'test_case': frm.doc.name
        };
        frappe.set_route('List', 'Test Execution Log');
    },

    generate_automation_script: function (frm) {
        frappe.confirm(__('Generate automation script template for this test case?'), function () {
            frappe.call({
                method: 'universal_workshop.testing.utils.generate_automation_script',
                args: {
                    test_case: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frm.trigger('show_script_dialog', r.message);
                    }
                }
            });
        });
    },

    run_automated_test: function (frm) {
        if (!frm.doc.automation_script_path) {
            frappe.msgprint(__('No automation script path specified'));
            return;
        }

        frappe.confirm(__('Run automated test for this test case?'), function () {
            frappe.call({
                method: 'universal_workshop.testing.utils.run_automated_test',
                args: {
                    test_case: frm.doc.name,
                    script_path: frm.doc.automation_script_path
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Automated test execution completed. Check execution log for results.'));
                        frm.reload_doc();
                    }
                }
            });
        });
    },

    show_compliance_checklist: function (frm) {
        let compliance_items = [];

        if (frm.doc.oman_vat_compliance) {
            compliance_items.push({
                label: __('Oman VAT Compliance (5%)'),
                items: [
                    __('VAT calculation accuracy'),
                    __('Invoice QR code generation'),
                    __('Tax authority reporting format'),
                    __('Multi-currency support')
                ]
            });
        }

        if (frm.doc.environmental_compliance) {
            compliance_items.push({
                label: __('Environmental Compliance'),
                items: [
                    __('Waste documentation tracking'),
                    __('Regulatory report generation'),
                    __('GPS coordinate validation'),
                    __('Compliance percentage calculation')
                ]
            });
        }

        if (frm.doc.arabic_localization_checks) {
            compliance_items.push({
                label: __('Arabic Localization'),
                items: [
                    __('RTL text display'),
                    __('Arabic character encoding'),
                    __('Dual language support'),
                    __('Arabic number formatting')
                ]
            });
        }

        frm.trigger('show_compliance_dialog', compliance_items);
    },

    // Helper methods
    detect_text_direction: function (frm, text) {
        if (!text) return 'ltr';

        // Simple Arabic text detection
        let arabicPattern = /[\u0600-\u06FF]/;
        let arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
        let totalChars = text.replace(/\s/g, '').length;

        return (arabicChars / totalChars > 0.3) ? 'rtl' : 'ltr';
    },

    update_module_specific_fields: function (frm) {
        // Update fields based on selected module
        if (frm.doc.test_module === 'Scrap Vehicle Processing') {
            frm.set_value('scrap_vehicle_components', 'Vehicle Assessment, Dismantling, Parts Grading');
        } else if (frm.doc.test_module === 'Marketplace Integration') {
            frm.set_value('marketplace_integrations', 'Online Parts Listing, Inventory Sync, Sales Channel Integration');
        } else if (frm.doc.test_module === 'Environmental Compliance') {
            frm.set_value('environmental_compliance', 1);
            frm.set_value('regulatory_documentation', 1);
        }
    },

    set_category_defaults: function (frm) {
        // Set default values based on test category
        switch (frm.doc.test_category) {
            case 'Performance Testing':
                frm.set_value('performance_benchmarks', 'Response time < 3 seconds, Load capacity > 100 users');
                break;
            case 'Security Testing':
                frm.set_value('security_validation', 1);
                break;
            case 'Compliance Testing':
                frm.set_value('audit_trail_validation', 1);
                break;
            case 'Arabic Localization Testing':
                frm.set_value('arabic_localization_checks', 'RTL display, Arabic text input, Number formatting');
                frm.set_value('arabic_report_validation', 1);
                break;
        }
    },

    set_priority_defaults: function (frm) {
        // Set defaults based on priority
        if (frm.doc.test_priority === 'Critical') {
            frm.set_value('approval_required', 1);
            if (!frm.doc.estimated_duration) {
                frm.set_value('estimated_duration', 60); // 1 hour for critical tests
            }
        }
    },

    validate_priority_category_combination: function (frm) {
        // Validate priority and category combinations
        let criticalCategories = ['Functional Testing', 'Security Testing', 'Compliance Testing'];

        if (frm.doc.test_priority === 'Critical' &&
            !criticalCategories.includes(frm.doc.test_category)) {
            frappe.msgprint(__('Critical priority is typically used for Functional, Security, or Compliance tests'), 'warning');
        }
    },

    show_execution_metrics: function (frm) {
        if (frm.doc.execution_count > 0) {
            let success_rate = frm.doc.success_rate || 0;
            let status_color = success_rate >= 80 ? 'green' : success_rate >= 60 ? 'orange' : 'red';

            let metrics_html = `
                <div class="test-metrics" style="margin: 10px 0;">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="metric-box">
                                <h4>${frm.doc.execution_count}</h4>
                                <p>${__('Total Executions')}</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box">
                                <h4 style="color: ${status_color}">${success_rate.toFixed(1)}%</h4>
                                <p>${__('Success Rate')}</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box">
                                <h4>${frm.doc.total_failures || 0}</h4>
                                <p>${__('Total Failures')}</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box">
                                <h4>${frm.doc.last_execution_duration || 0}m</h4>
                                <p>${__('Last Duration')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            frm.get_field('execution_tracking_section').$wrapper.append(metrics_html);
        }
    },

    show_compliance_status: function (frm) {
        let compliance_checks = [
            { field: 'oman_vat_compliance', label: __('VAT Compliance') },
            { field: 'environmental_compliance', label: __('Environmental') },
            { field: 'arabic_localization_checks', label: __('Arabic Localization') },
            { field: 'security_validation', label: __('Security') },
            { field: 'audit_trail_validation', label: __('Audit Trail') }
        ];

        let active_checks = compliance_checks.filter(check => frm.doc[check.field]);

        if (active_checks.length > 0) {
            let compliance_html = '<div class="compliance-status" style="margin: 10px 0;"><h5>' + __('Compliance Requirements') + '</h5>';

            active_checks.forEach(check => {
                compliance_html += `<span class="label label-info" style="margin-right: 5px;">${check.label}</span>`;
            });

            compliance_html += '</div>';
            frm.get_field('compliance_testing_section').$wrapper.append(compliance_html);
        }
    },

    show_test_progress: function (frm) {
        if (frm.doc.test_steps && frm.doc.test_steps.length > 0) {
            let total_steps = frm.doc.test_steps.length;
            let critical_steps = frm.doc.test_steps.filter(step => step.is_critical).length;

            let progress_html = `
                <div class="test-progress" style="margin: 10px 0;">
                    <p><strong>${__('Test Steps Overview')}</strong></p>
                    <p>${__('Total Steps')}: ${total_steps} | ${__('Critical Steps')}: ${critical_steps}</p>
                    <div class="progress">
                        <div class="progress-bar progress-bar-info" style="width: 100%">
                            ${total_steps} ${__('Steps Defined')}
                        </div>
                    </div>
                </div>
            `;

            frm.get_field('test_steps_section').$wrapper.append(progress_html);
        }
    },

    show_template_selection: function (frm, templates) {
        let template_options = templates.map(t => ({ label: t.name, value: t.name }));

        frappe.prompt([
            {
                label: __('Select Template'),
                fieldname: 'template',
                fieldtype: 'Select',
                options: template_options,
                description: __('Choose a template to pre-populate test case fields')
            }
        ], function (values) {
            frm.trigger('apply_template', values.template);
        }, __('Test Case Templates'), __('Apply Template'));
    },

    apply_template: function (frm, template_name) {
        frappe.call({
            method: 'universal_workshop.testing.utils.apply_test_template',
            args: {
                template_name: template_name,
                test_case: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.msgprint(__('Template applied successfully'));
                }
            }
        });
    },

    show_test_report_dialog: function (frm, report_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Test Case Report'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'report_html'
                }
            ]
        });

        let report_html = frm.trigger('format_test_report', report_data);
        dialog.fields_dict.report_html.$wrapper.html(report_html);
        dialog.show();
    },

    format_test_report: function (frm, data) {
        return `
            <div class="test-report">
                <h3>${data.test_case.test_case_title}</h3>
                <p><strong>${__('Total Executions')}:</strong> ${data.summary.total_executions}</p>
                <p><strong>${__('Success Rate')}:</strong> ${data.summary.success_rate}%</p>
                <p><strong>${__('Average Duration')}:</strong> ${data.summary.average_duration} minutes</p>
                
                <h4>${__('Recent Executions')}</h4>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>${__('Date')}</th>
                            <th>${__('Status')}</th>
                            <th>${__('Duration')}</th>
                            <th>${__('Steps Passed')}</th>
                            <th>${__('Steps Failed')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.execution_history.map(exec => `
                            <tr>
                                <td>${exec.execution_date}</td>
                                <td><span class="label label-${exec.execution_status === 'Passed' ? 'success' : 'danger'}">${exec.execution_status}</span></td>
                                <td>${exec.execution_duration || 0}m</td>
                                <td>${exec.steps_passed || 0}</td>
                                <td>${exec.steps_failed || 0}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    show_compliance_dialog: function (frm, compliance_items) {
        let dialog = new frappe.ui.Dialog({
            title: __('Compliance Checklist'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'compliance_html'
                }
            ]
        });

        let compliance_html = '<div class="compliance-checklist">';

        compliance_items.forEach(section => {
            compliance_html += `<h4>${section.label}</h4><ul>`;
            section.items.forEach(item => {
                compliance_html += `<li>${item}</li>`;
            });
            compliance_html += '</ul>';
        });

        compliance_html += '</div>';
        dialog.fields_dict.compliance_html.$wrapper.html(compliance_html);
        dialog.show();
    },

    show_script_dialog: function (frm, script_content) {
        let dialog = new frappe.ui.Dialog({
            title: __('Automation Script Template'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'Code',
                    fieldname: 'script_content',
                    label: __('Script Content'),
                    options: 'Python',
                    value: script_content,
                    read_only: 1
                }
            ]
        });

        dialog.show();
    },

    load_execution_metrics: function (frm) {
        if (frm.doc.execution_count > 0) {
            frm.trigger('display_execution_metrics');
        }
    },

    display_execution_metrics: function (frm) {
        const success_rate = frm.doc.total_failures ?
            ((frm.doc.execution_count - frm.doc.total_failures) / frm.doc.execution_count * 100).toFixed(1) :
            (frm.doc.execution_count > 0 ? 100 : 0);

        let html = '<div class="alert alert-info">';
        html += '<strong>' + __('Execution Metrics') + '</strong><br>';
        html += __('Total Executions') + ': ' + (frm.doc.execution_count || 0) + '<br>';
        html += __('Success Rate') + ': ' + success_rate + '%<br>';
        if (frm.doc.last_executed) {
            html += __('Last Executed') + ': ' + frappe.datetime.str_to_user(frm.doc.last_executed);
        }
        html += '</div>';

        frm.get_field('execution_tracking_section').$wrapper.find('.execution-metrics').remove();
        $(html).addClass('execution-metrics').appendTo(frm.get_field('execution_tracking_section').$wrapper);
    },

    display_test_report: function (frm, report_data) {
        let html = '<div class="test-report">';

        // Test Case Summary
        html += '<h4>' + __('Test Case Summary') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>' + __('Title') + '</strong></td><td>' + report_data.test_case.test_case_title + '</td></tr>';
        html += '<tr><td><strong>' + __('Module') + '</strong></td><td>' + report_data.test_case.test_module + '</td></tr>';
        html += '<tr><td><strong>' + __('Priority') + '</strong></td><td>' + report_data.test_case.test_priority + '</td></tr>';
        html += '<tr><td><strong>' + __('Success Rate') + '</strong></td><td>' + report_data.success_rate.toFixed(1) + '%</td></tr>';
        html += '</table>';

        // Performance Analysis
        if (report_data.performance_analysis.status !== 'No data') {
            html += '<h4>' + __('Performance Analysis') + '</h4>';
            html += '<table class="table table-bordered">';
            html += '<tr><td><strong>' + __('Trend') + '</strong></td><td>' + report_data.performance_analysis.trend + '</td></tr>';
            html += '<tr><td><strong>' + __('Average Duration') + '</strong></td><td>' + (report_data.performance_analysis.avg_duration || 0) + ' min</td></tr>';
            html += '</table>';
        }

        // Recommendations
        if (report_data.recommendations && report_data.recommendations.length > 0) {
            html += '<h4>' + __('Recommendations') + '</h4>';
            html += '<ul>';
            report_data.recommendations.forEach(function (rec) {
                html += '<li>' + rec + '</li>';
            });
            html += '</ul>';
        }

        html += '</div>';

        frappe.msgprint({
            title: __('Test Case Report'),
            message: html,
            wide: true
        });
    }
});

// Child table events for test steps
frappe.ui.form.on('System Test Step', {
    step_type: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Set default values based on step type
        if (row.step_type === 'API Call' && !row.api_endpoint) {
            frappe.model.set_value(cdt, cdn, 'api_endpoint', '/api/method/');
        } else if (row.step_type === 'Database Query' && !row.sql_query) {
            frappe.model.set_value(cdt, cdn, 'sql_query', 'SELECT * FROM tab');
        }
    },

    is_critical: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.is_critical) {
            frappe.model.set_value(cdt, cdn, 'screenshot_required', 1);
        }
    },

    step_description: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Auto-detect and set text direction for Arabic content
        if (row.step_description) {
            let direction = frm.trigger('detect_text_direction', row.step_description);
            // Note: Setting direction for child table fields requires different approach
        }
    }
});

// Utility functions for testing
frappe.provide('universal_workshop.testing');

universal_workshop.testing = {
    execute_test_suite: function (filters) {
        frappe.call({
            method: 'universal_workshop.testing.doctype.system_test_case.system_test_case.execute_test_suite',
            args: filters,
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Test Suite Execution'),
                        message: __('Executed {0} test cases. Check execution logs for details.', [r.message.total_tests]),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    bulk_create_test_cases: function (test_data_file) {
        frappe.call({
            method: 'universal_workshop.testing.doctype.system_test_case.system_test_case.bulk_create_test_cases',
            args: {
                test_cases_data: test_data_file
            },
            callback: function (r) {
                if (r.message) {
                    const result = r.message;
                    let message = result.summary;

                    if (result.errors.length > 0) {
                        message += '<br><br><strong>' + __('Errors') + ':</strong><ul>';
                        result.errors.forEach(error => {
                            message += '<li>' + error.test_title + ': ' + error.error + '</li>';
                        });
                        message += '</ul>';
                    }

                    frappe.msgprint({
                        title: __('Bulk Test Case Creation'),
                        message: message,
                        indicator: result.errors.length === 0 ? 'green' : 'orange'
                    });
                }
            }
        });
    },

    get_testing_dashboard: function () {
        frappe.call({
            method: 'universal_workshop.testing.doctype.system_test_case.system_test_case.get_testing_dashboard_data',
            callback: function (r) {
                if (r.message) {
                    universal_workshop.testing.display_dashboard(r.message);
                }
            }
        });
    },

    display_dashboard: function (data) {
        let html = '<div class="testing-dashboard">';

        // Test Case Statistics
        html += '<div class="row">';
        html += '<div class="col-md-6">';
        html += '<h4>' + __('Test Case Statistics') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td>' + __('Total Test Cases') + '</td><td>' + data.test_case_stats.total + '</td></tr>';
        html += '<tr><td>' + __('Ready for Testing') + '</td><td>' + data.test_case_stats.ready + '</td></tr>';
        html += '<tr><td>' + __('Passed') + '</td><td>' + data.test_case_stats.passed + '</td></tr>';
        html += '<tr><td>' + __('Failed') + '</td><td>' + data.test_case_stats.failed + '</td></tr>';
        html += '<tr><td>' + __('Success Rate') + '</td><td>' + data.test_case_stats.success_rate.toFixed(1) + '%</td></tr>';
        html += '</table></div>';

        // Execution Statistics
        html += '<div class="col-md-6">';
        html += '<h4>' + __('Execution Statistics') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td>' + __('Total Executions') + '</td><td>' + data.execution_stats.total + '</td></tr>';
        html += '<tr><td>' + __('Passed Executions') + '</td><td>' + data.execution_stats.passed + '</td></tr>';
        html += '<tr><td>' + __('Failed Executions') + '</td><td>' + data.execution_stats.failed + '</td></tr>';
        html += '<tr><td>' + __('Execution Success Rate') + '</td><td>' + data.execution_stats.success_rate.toFixed(1) + '%</td></tr>';
        html += '</table></div></div>';

        html += '</div>';

        frappe.msgprint({
            title: __('Testing Dashboard'),
            message: html,
            wide: true
        });
    }
}; 