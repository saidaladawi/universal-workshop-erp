// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Benchmark Analysis', {
    refresh: function (frm) {
        // Setup form enhancements
        frm.trigger('setup_arabic_support');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_dashboard_indicators');
    },

    setup_arabic_support: function (frm) {
        // Configure RTL layout if enabled
        if (frm.doc.rtl_display) {
            frm.page.main.addClass('rtl-layout');

            // Set RTL direction for Arabic fields
            ['benchmark_name_ar', 'performance_summary', 'gap_analysis',
                'recommendations', 'action_items'].forEach(function (field) {
                    if (frm.fields_dict[field]) {
                        frm.fields_dict[field].$wrapper.attr('dir', 'rtl');
                        if (frm.fields_dict[field].$input) {
                            frm.fields_dict[field].$input.attr('dir', 'rtl');
                        }
                    }
                });
        }

        // Auto-suggest Arabic name when English name is entered
        if (frm.doc.benchmark_name && !frm.doc.benchmark_name_ar && frappe.boot.lang === 'ar') {
            frm.set_value('benchmark_name_ar', 'مقارنة معيارية - ' + frm.doc.benchmark_name);
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.name && frm.doc.docstatus !== 2) {
            // Add custom buttons for various actions
            frm.add_custom_button(__('Calculate Scores'), function () {
                frm.trigger('calculate_performance_scores');
            }, __('Actions'));

            frm.add_custom_button(__('Generate Insights'), function () {
                frm.trigger('generate_automatic_insights');
            }, __('Actions'));

            frm.add_custom_button(__('View Trends'), function () {
                frm.trigger('show_trend_analysis');
            }, __('Analysis'));

            frm.add_custom_button(__('Export Report'), function () {
                frm.trigger('export_benchmark_report');
            }, __('Reports'));

            frm.add_custom_button(__('Compare with Industry'), function () {
                frm.trigger('compare_with_industry');
            }, __('Comparison'));

            frm.add_custom_button(__('Setup Alerts'), function () {
                frm.trigger('setup_alert_thresholds');
            }, __('Configuration'));

            // Dashboard button
            if (frm.doc.dashboard_display) {
                frm.add_custom_button(__('View Dashboard'), function () {
                    frappe.route_options = { 'benchmark': frm.doc.name };
                    frappe.set_route('benchmark-dashboard');
                }, __('Dashboard'));
            }
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on configuration
        frm.trigger('toggle_automation_fields');
        frm.trigger('toggle_arabic_fields');
        frm.trigger('toggle_calculation_fields');
    },

    update_dashboard_indicators: function (frm) {
        if (frm.doc.performance_score !== undefined) {
            frm.dashboard.add_indicator(__('Performance Score'),
                frm.doc.performance_score >= 80 ? 'green' :
                    frm.doc.performance_score >= 60 ? 'orange' : 'red',
                frm.doc.performance_score + '%');
        }

        if (frm.doc.trend_direction) {
            let color = frm.doc.trend_direction === 'Improving' ? 'green' :
                frm.doc.trend_direction === 'Declining' ? 'red' : 'blue';
            frm.dashboard.add_indicator(__('Trend'), color, frm.doc.trend_direction);
        }

        if (frm.doc.variance !== undefined) {
            let color = Math.abs(frm.doc.variance) <= 5 ? 'green' :
                Math.abs(frm.doc.variance) <= 15 ? 'orange' : 'red';
            frm.dashboard.add_indicator(__('Variance'), color,
                (frm.doc.variance > 0 ? '+' : '') + frm.doc.variance.toFixed(1) + '%');
        }
    },

    // Field event handlers
    benchmark_name: function (frm) {
        if (frm.doc.benchmark_name && !frm.doc.benchmark_name_ar && frm.doc.rtl_display) {
            frm.set_value('benchmark_name_ar', 'مقارنة معيارية - ' + frm.doc.benchmark_name);
        }
    },

    primary_kpi: function (frm) {
        if (frm.doc.primary_kpi) {
            frm.trigger('fetch_kpi_data');
        }
    },

    current_value: function (frm) {
        frm.trigger('calculate_variance_and_scores');
    },

    target_value: function (frm) {
        frm.trigger('calculate_variance_and_scores');
    },

    benchmark_type: function (frm) {
        frm.trigger('update_type_specific_fields');
    },

    business_area: function (frm) {
        if (frm.doc.business_area) {
            frm.trigger('fetch_industry_benchmarks');
        }
    },

    rtl_display: function (frm) {
        frm.trigger('setup_arabic_support');
    },

    auto_update_frequency: function (frm) {
        frm.trigger('toggle_automation_fields');
    },

    // Custom trigger functions
    fetch_kpi_data: function (frm) {
        if (frm.doc.primary_kpi) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Analytics KPI',
                    name: frm.doc.primary_kpi
                },
                callback: function (r) {
                    if (r.message) {
                        let kpi = r.message;

                        if (!frm.doc.current_value) {
                            frm.set_value('current_value', kpi.current_value);
                        }

                        if (!frm.doc.target_value && kpi.target_value) {
                            frm.set_value('target_value', kpi.target_value);
                        }

                        if (!frm.doc.business_area && kpi.kpi_category) {
                            frm.set_value('business_area', kpi.kpi_category);
                        }

                        frm.trigger('calculate_variance_and_scores');
                    }
                }
            });
        }
    },

    calculate_variance_and_scores: function (frm) {
        if (frm.doc.current_value && frm.doc.target_value) {
            let variance = ((frm.doc.current_value - frm.doc.target_value) / frm.doc.target_value) * 100;
            frm.set_value('variance', variance);
        }

        // Trigger performance score calculation
        frm.trigger('calculate_performance_scores');
    },

    calculate_performance_scores: function (frm) {
        if (!frm.doc.current_value) {
            frappe.msgprint(__('Current value is required to calculate performance scores'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.benchmark_analysis.benchmark_analysis.calculate_benchmark_score',
            args: {
                current_value: frm.doc.current_value,
                target_values: {
                    'internal_target': frm.doc.internal_target || 0,
                    'industry_standard': frm.doc.industry_standard || 0,
                    'peer_average': frm.doc.peer_average || 0,
                    'best_in_class': frm.doc.best_in_class || 0,
                    'historical_baseline': frm.doc.historical_baseline || 0
                }
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('performance_score', r.message);
                    frm.trigger('update_dashboard_indicators');

                    frappe.show_alert({
                        message: __('Performance score calculated: {0}%', [r.message.toFixed(1)]),
                        indicator: r.message >= 80 ? 'green' : r.message >= 60 ? 'orange' : 'red'
                    });
                }
            }
        });
    },

    generate_automatic_insights: function (frm) {
        frappe.call({
            method: 'frappe.client.save',
            args: {
                doc: frm.doc
            },
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Insights generated successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    show_trend_analysis: function (frm) {
        if (!frm.doc.name) {
            frappe.msgprint(__('Please save the document first'));
            return;
        }

        let dialog = new frappe.ui.Dialog({
            title: __('Trend Analysis'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'Select',
                    label: __('Period'),
                    fieldname: 'period_days',
                    options: '30\n60\n90\n180\n365',
                    default: '90'
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'trend_chart'
                }
            ],
            primary_action_label: __('Generate Chart'),
            primary_action: function () {
                let period_days = dialog.get_value('period_days');

                frappe.call({
                    method: 'universal_workshop.analytics_reporting.doctype.benchmark_analysis.benchmark_analysis.get_benchmark_trends',
                    args: {
                        benchmark_name: frm.doc.name,
                        period_days: period_days
                    },
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            frm.trigger('render_trend_chart', [dialog, r.message]);
                        } else {
                            frappe.msgprint(__('No trend data available for the selected period'));
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    export_benchmark_report: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Export Benchmark Report'),
            fields: [
                {
                    fieldtype: 'Select',
                    label: __('Format'),
                    fieldname: 'format_type',
                    options: 'PDF\nExcel\nCSV\nPowerPoint',
                    default: 'PDF',
                    reqd: 1
                },
                {
                    fieldtype: 'Check',
                    label: __('Include Charts'),
                    fieldname: 'include_charts',
                    default: 1
                },
                {
                    fieldtype: 'Check',
                    label: __('Include Trend Analysis'),
                    fieldname: 'include_trends',
                    default: 1
                },
                {
                    fieldtype: 'Select',
                    label: __('Language'),
                    fieldname: 'language',
                    options: 'English\nArabic\nBilingual',
                    default: frappe.boot.lang === 'ar' ? 'Arabic' : 'English'
                }
            ],
            primary_action_label: __('Export'),
            primary_action: function () {
                let values = dialog.get_values();

                frappe.call({
                    method: 'universal_workshop.analytics_reporting.doctype.benchmark_analysis.benchmark_analysis.export_benchmark_report',
                    args: {
                        benchmark_name: frm.doc.name,
                        format_type: values.format_type
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Report exported successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    compare_with_industry: function (frm) {
        if (!frm.doc.business_area) {
            frappe.msgprint(__('Please select a business area first'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.benchmark_analysis.benchmark_analysis.get_industry_benchmarks',
            args: {
                business_area: frm.doc.business_area
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('show_industry_comparison', [r.message]);
                }
            }
        });
    },

    show_industry_comparison: function (frm, industry_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Industry Benchmark Comparison'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'comparison_table'
                }
            ]
        });

        let html = '<table class="table table-striped"><thead><tr>';
        html += '<th>' + __('Metric') + '</th>';
        html += '<th>' + __('Your Value') + '</th>';
        html += '<th>' + __('Industry Standard') + '</th>';
        html += '<th>' + __('Gap') + '</th>';
        html += '<th>' + __('Performance') + '</th>';
        html += '</tr></thead><tbody>';

        for (let metric in industry_data) {
            let industry_value = industry_data[metric];
            let your_value = frm.doc.current_value || 0;
            let gap = your_value - industry_value;
            let performance = (your_value / industry_value) * 100;

            html += '<tr>';
            html += '<td>' + metric + '</td>';
            html += '<td>' + your_value.toFixed(2) + '</td>';
            html += '<td>' + industry_value.toFixed(2) + '</td>';
            html += '<td class="' + (gap >= 0 ? 'text-success' : 'text-danger') + '">';
            html += (gap >= 0 ? '+' : '') + gap.toFixed(2) + '</td>';
            html += '<td>';
            html += '<span class="badge badge-' + (performance >= 100 ? 'success' : performance >= 80 ? 'warning' : 'danger') + '">';
            html += performance.toFixed(1) + '%</span></td>';
            html += '</tr>';
        }

        html += '</tbody></table>';

        dialog.fields_dict.comparison_table.$wrapper.html(html);
        dialog.show();
    },

    setup_alert_thresholds: function (frm) {
        let current_thresholds = {};
        if (frm.doc.alert_thresholds) {
            try {
                current_thresholds = JSON.parse(frm.doc.alert_thresholds);
            } catch (e) {
                current_thresholds = {};
            }
        }

        let dialog = new frappe.ui.Dialog({
            title: __('Setup Alert Thresholds'),
            fields: [
                {
                    fieldtype: 'Float',
                    label: __('Critical Threshold'),
                    fieldname: 'critical',
                    default: current_thresholds.critical || 0
                },
                {
                    fieldtype: 'Float',
                    label: __('Warning Threshold'),
                    fieldname: 'warning',
                    default: current_thresholds.warning || 0
                },
                {
                    fieldtype: 'Float',
                    label: __('Target Threshold'),
                    fieldname: 'target',
                    default: current_thresholds.target || 0
                },
                {
                    fieldtype: 'Small Text',
                    label: __('Notification Recipients'),
                    fieldname: 'recipients',
                    default: frm.doc.notification_recipients || ''
                }
            ],
            primary_action_label: __('Save'),
            primary_action: function () {
                let values = dialog.get_values();

                let thresholds = {
                    critical: values.critical,
                    warning: values.warning,
                    target: values.target
                };

                frm.set_value('alert_thresholds', JSON.stringify(thresholds));
                frm.set_value('notification_recipients', values.recipients);

                frappe.show_alert({
                    message: __('Alert thresholds saved successfully'),
                    indicator: 'green'
                });

                dialog.hide();
                frm.save();
            }
        });

        dialog.show();
    },

    toggle_automation_fields: function (frm) {
        let show_automation = frm.doc.auto_update_frequency && frm.doc.auto_update_frequency !== '';

        frm.toggle_display(['alert_thresholds', 'notification_recipients',
            'escalation_rules', 'reporting_schedule'], show_automation);
    },

    toggle_arabic_fields: function (frm) {
        let show_arabic = frm.doc.rtl_display;

        frm.toggle_display(['benchmark_name_ar', 'arabic_charts',
            'bilingual_reports', 'arabic_fonts'], show_arabic);
    },

    toggle_calculation_fields: function (frm) {
        let show_calculation = frm.doc.comparison_method && frm.doc.comparison_method !== '';

        frm.toggle_display(['calculation_formula', 'weights_json',
            'normalization_method', 'statistical_method'], show_calculation);
    },

    update_type_specific_fields: function (frm) {
        if (frm.doc.benchmark_type) {
            // Show relevant fields based on benchmark type
            switch (frm.doc.benchmark_type) {
                case 'Industry Standard':
                    frm.set_df_property('industry_standard', 'reqd', 1);
                    frm.set_df_property('external_benchmarks', 'hidden', 0);
                    break;
                case 'Peer Comparison':
                    frm.set_df_property('peer_average', 'reqd', 1);
                    frm.set_df_property('external_benchmarks', 'hidden', 0);
                    break;
                case 'Historical Trend':
                    frm.set_df_property('historical_baseline', 'reqd', 1);
                    frm.set_df_property('period_comparison', 'hidden', 0);
                    break;
                case 'Internal Target':
                    frm.set_df_property('internal_target', 'reqd', 1);
                    frm.set_df_property('external_benchmarks', 'hidden', 1);
                    break;
            }
        }
    },

    render_trend_chart: function (frm, dialog, trend_data) {
        let chart_data = {
            labels: trend_data.map(d => d.date),
            datasets: [{
                name: __('Current Value'),
                values: trend_data.map(d => d.value),
                chartType: 'line'
            }, {
                name: __('Target'),
                values: trend_data.map(d => d.target),
                chartType: 'line'
            }, {
                name: __('Industry Standard'),
                values: trend_data.map(d => d.industry_standard),
                chartType: 'line'
            }]
        };

        let chart = new frappe.Chart(dialog.fields_dict.trend_chart.$wrapper[0], {
            title: __('Performance Trend'),
            data: chart_data,
            type: 'line',
            height: 300,
            colors: ['#007bff', '#28a745', '#ffc107']
        });
    },

    fetch_industry_benchmarks: function (frm) {
        if (frm.doc.business_area) {
            frappe.call({
                method: 'universal_workshop.analytics_reporting.doctype.benchmark_analysis.benchmark_analysis.get_industry_benchmarks',
                args: {
                    business_area: frm.doc.business_area
                },
                callback: function (r) {
                    if (r.message && Object.keys(r.message).length > 0) {
                        // Update industry standard if available
                        if (r.message.industry_average && !frm.doc.industry_standard) {
                            frm.set_value('industry_standard', r.message.industry_average);
                        }

                        // Update peer average if available
                        if (r.message.peer_average && !frm.doc.peer_average) {
                            frm.set_value('peer_average', r.message.peer_average);
                        }

                        // Update best in class if available
                        if (r.message.best_in_class && !frm.doc.best_in_class) {
                            frm.set_value('best_in_class', r.message.best_in_class);
                        }
                    }
                }
            });
        }
    }
});

// Child table events for any future extensions
frappe.ui.form.on('Benchmark Analysis', {
    // Add any child table specific events here if needed
});

// Additional utility functions
function format_arabic_number(number) {
    if (!number) return '';

    let arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let formattedNumber = number.toString();

    for (let i = 0; i < 10; i++) {
        formattedNumber = formattedNumber.replace(new RegExp(i.toString(), 'g'), arabicNumerals[i]);
    }

    return formattedNumber;
}

function get_benchmark_color(score) {
    if (score >= 90) return 'green';
    if (score >= 75) return 'blue';
    if (score >= 60) return 'orange';
    if (score >= 40) return 'yellow';
    return 'red';
}

function format_variance_display(variance) {
    let color = Math.abs(variance) <= 5 ? 'success' :
        Math.abs(variance) <= 15 ? 'warning' : 'danger';
    let icon = variance > 0 ? '↗' : variance < 0 ? '↘' : '→';

    return `<span class="text-${color}">${icon} ${variance.toFixed(1)}%</span>`;
}
