// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('ABC Analysis', {
    refresh: function (frm) {
        frm.add_custom_button(__('Run Analysis'), function () {
            frm.trigger('run_analysis');
        });

        frm.add_custom_button(__('View Chart'), function () {
            frm.trigger('show_analysis_chart');
        });

        frm.add_custom_button(__('Export Results'), function () {
            frm.trigger('export_analysis_results');
        });

        // Setup percentage validation
        frm.trigger('setup_percentage_validation');
    },

    setup_percentage_validation: function (frm) {
        ['category_a_percentage', 'category_b_percentage', 'category_c_percentage'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('change', function () {
                    frm.trigger('validate_percentages');
                });
            }
        });
    },

    validate_percentages: function (frm) {
        const a = parseFloat(frm.doc.category_a_percentage || 0);
        const b = parseFloat(frm.doc.category_b_percentage || 0);
        const c = parseFloat(frm.doc.category_c_percentage || 0);
        const total = a + b + c;

        if (Math.abs(total - 100) > 0.01) {
            frappe.msgprint(__('Category percentages must sum to 100%. Current total: ') + total + '%');
            frappe.validated = false;
        }
    },

    run_analysis: function (frm) {
        if (!frm.doc.analysis_name) {
            frappe.msgprint(__('Please enter analysis name'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.abc_analysis.abc_analysis.run_abc_analysis',
            args: {
                docname: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(__('ABC Analysis completed successfully'));
                    frm.reload_doc();
                }
            }
        });
    },

    show_analysis_chart: function (frm) {
        if (!frm.doc.total_items_analyzed || frm.doc.total_items_analyzed === 0) {
            frappe.msgprint(__('No analysis data available. Please run analysis first.'));
            return;
        }

        // Create chart data
        const chartData = {
            labels: ['Category A', 'Category B', 'Category C'],
            datasets: [{
                label: 'Items Count',
                data: [
                    frm.doc.category_a_items || 0,
                    frm.doc.category_b_items || 0,
                    frm.doc.category_c_items || 0
                ],
                backgroundColor: ['#ff6384', '#36a2eb', '#cc65fe']
            }, {
                label: 'Value (OMR)',
                data: [
                    frm.doc.category_a_value || 0,
                    frm.doc.category_b_value || 0,
                    frm.doc.category_c_value || 0
                ],
                backgroundColor: ['#ff9f40', '#4bc0c0', '#9966ff']
            }]
        };

        // Show chart in dialog
        const dialog = new frappe.ui.Dialog({
            title: __('ABC Analysis Chart'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'chart_container',
                options: '<canvas id="abc-chart" width="400" height="200"></canvas>'
            }]
        });

        dialog.show();

        // Initialize chart after dialog is shown
        setTimeout(() => {
            const ctx = document.getElementById('abc-chart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: chartData,
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }, 100);
    },

    export_analysis_results: function (frm) {
        if (!frm.doc.total_items_analyzed || frm.doc.total_items_analyzed === 0) {
            frappe.msgprint(__('No analysis data available to export.'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.abc_analysis.abc_analysis.export_results',
            args: {
                docname: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    // Download the exported file
                    const link = document.createElement('a');
                    link.href = r.message.file_url;
                    link.download = r.message.filename;
                    link.click();
                }
            }
        });
    },

    analysis_period: function (frm) {
        // Update UI based on analysis period
        if (frm.doc.analysis_period === 'Custom Period') {
            frm.add_custom_button(__('Set Custom Dates'), function () {
                frm.trigger('show_custom_date_selector');
            });
        }
    },

    show_custom_date_selector: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Set Custom Analysis Period'),
            fields: [{
                label: __('Start Date'),
                fieldname: 'custom_start_date',
                fieldtype: 'Date',
                reqd: 1
            }, {
                label: __('End Date'),
                fieldname: 'custom_end_date',
                fieldtype: 'Date',
                reqd: 1
            }],
            primary_action_label: __('Apply'),
            primary_action: function () {
                const values = dialog.get_values();
                if (values) {
                    frm.set_value('custom_start_date', values.custom_start_date);
                    frm.set_value('custom_end_date', values.custom_end_date);
                    dialog.hide();
                }
            }
        });

        dialog.show();
    },

    calculation_method: function (frm) {
        // Update description based on calculation method
        const descriptions = {
            'Value Based': __('Analysis based on current stock value'),
            'Usage Based': __('Analysis based on item usage over time'),
            'Combined Value+Usage': __('Analysis based on both stock value and usage')
        };

        const description = descriptions[frm.doc.calculation_method] || '';
        if (description) {
            frappe.msgprint(description);
        }
    },

    validate: function (frm) {
        // Validate analysis configuration
        if (!frm.doc.analysis_name) {
            frappe.msgprint(__('Analysis name is required'));
            frappe.validated = false;
        }

        if (!frm.doc.analysis_period) {
            frappe.msgprint(__('Analysis period is required'));
            frappe.validated = false;
        }

        if (!frm.doc.calculation_method) {
            frappe.msgprint(__('Calculation method is required'));
            frappe.validated = false;
        }

        // Validate percentages
        frm.trigger('validate_percentages');
    }
});

// Global ABC Analysis functions
window.abcAnalysis = {
    getAnalysisSummary: function (docname) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'universal_workshop.parts_inventory.doctype.abc_analysis.abc_analysis.get_analysis_summary',
                args: { docname: docname },
                callback: function (r) {
                    if (r.message) {
                        resolve(r.message);
                    } else {
                        reject('Failed to get analysis summary');
                    }
                }
            });
        });
    },

    createDashboardWidget: function (container, analysisData) {
        // Create dashboard widget for ABC analysis
        const widget = $(`
            <div class="abc-dashboard-widget">
                <h4>${__('ABC Analysis Summary')}</h4>
                <div class="abc-stats">
                    <div class="stat-item">
                        <span class="stat-label">${__('Total Items')}</span>
                        <span class="stat-value">${analysisData.total_items}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">${__('Total Value')}</span>
                        <span class="stat-value">${format_currency(analysisData.total_value)}</span>
                    </div>
                </div>
                <div class="abc-categories">
                    <div class="category-a">
                        <h5>${__('Category A')}</h5>
                        <p>${__('Items')}: ${analysisData.category_a.items}</p>
                        <p>${__('Value')}: ${format_currency(analysisData.category_a.value)}</p>
                    </div>
                    <div class="category-b">
                        <h5>${__('Category B')}</h5>
                        <p>${__('Items')}: ${analysisData.category_b.items}</p>
                        <p>${__('Value')}: ${format_currency(analysisData.category_b.value)}</p>
                    </div>
                    <div class="category-c">
                        <h5>${__('Category C')}</h5>
                        <p>${__('Items')}: ${analysisData.category_c.items}</p>
                        <p>${__('Value')}: ${format_currency(analysisData.category_c.value)}</p>
                    </div>
                </div>
            </div>
        `);

        container.append(widget);
    }
};

function format_currency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'OMR'
    }).format(amount);
} 