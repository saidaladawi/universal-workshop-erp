// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Profit Analysis', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_rtl_layout');
        frm.trigger('update_dashboard_display');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['analysis_name_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });

        // Format OMR currency fields with Arabic numerals if Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.trigger('format_currency_arabic');
        }
    },

    setup_rtl_layout: function (frm) {
        // Apply RTL layout for Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
            $('.form-section').addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.docstatus === 1) {
            // Dashboard button
            frm.add_custom_button(__('View Dashboard'), function () {
                frm.trigger('show_dashboard');
            }, __('Actions'));

            // Export Report button
            frm.add_custom_button(__('Export Report'), function () {
                frm.trigger('export_analysis_report');
            }, __('Actions'));

            // Generate Next Analysis button
            frm.add_custom_button(__('Generate Next Analysis'), function () {
                frm.trigger('generate_next_analysis');
            }, __('Actions'));
        }

        if (frm.doc.docstatus === 0) {
            // Recalculate button
            frm.add_custom_button(__('Recalculate All Metrics'), function () {
                frm.trigger('recalculate_metrics');
            }, __('Calculate'));

            // Auto-fill recommendations button
            frm.add_custom_button(__('Generate AI Recommendations'), function () {
                frm.trigger('generate_ai_recommendations');
            }, __('AI Tools'));
        }
    },

    update_dashboard_display: function (frm) {
        if (frm.doc.analysis_status === 'Completed' && frm.doc.total_revenue_omr) {
            frm.trigger('render_summary_cards');
        }
    },

    render_summary_cards: function (frm) {
        // Create summary dashboard cards
        let dashboard_html = `
            <div class="profit-analysis-dashboard" style="margin: 15px 0;">
                <div class="row">
                    <div class="col-md-3">
                        <div class="card metric-card revenue-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">${__('Total Revenue')}</h5>
                                <h3 class="metric-value">${format_currency(frm.doc.total_revenue_omr || 0, 'OMR')}</h3>
                                <small class="text-muted">${__('إجمالي الإيرادات')}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card profit-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">${__('Net Profit')}</h5>
                                <h3 class="metric-value">${format_currency(frm.doc.net_profit_omr || 0, 'OMR')}</h3>
                                <small class="text-muted">${__('صافي الربح')} (${frm.doc.net_profit_margin_percentage || 0}%)</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card orders-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">${__('Total Orders')}</h5>
                                <h3 class="metric-value">${frm.doc.total_orders || 0}</h3>
                                <small class="text-muted">${__('إجمالي الطلبات')}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card roi-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">${__('ROI')}</h5>
                                <h3 class="metric-value">${frm.doc.roi_percentage || 0}%</h3>
                                <small class="text-muted">${__('العائد على الاستثمار')}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <style>
                .profit-analysis-dashboard .metric-card {
                    border: none;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin-bottom: 15px;
                    transition: transform 0.2s;
                }
                .profit-analysis-dashboard .metric-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .profit-analysis-dashboard .revenue-card { border-left: 4px solid #28a745; }
                .profit-analysis-dashboard .profit-card { border-left: 4px solid #007bff; }
                .profit-analysis-dashboard .orders-card { border-left: 4px solid #ffc107; }
                .profit-analysis-dashboard .roi-card { border-left: 4px solid #dc3545; }
                .profit-analysis-dashboard .metric-value {
                    color: #2e8b57;
                    font-weight: bold;
                    margin: 10px 0;
                }
                .rtl-layout .profit-analysis-dashboard .metric-card {
                    text-align: right;
                }
                .arabic-text {
                    font-family: 'Noto Sans Arabic', 'Tahoma', sans-serif;
                }
            </style>
        `;

        // Insert dashboard before form sections
        if (!frm.fields_dict.dashboard_section) {
            $(dashboard_html).insertBefore(frm.fields_dict.basic_information_section.$wrapper);
        }
    },

    format_currency_arabic: function (frm) {
        // Format currency fields with Arabic numerals
        let currency_fields = [
            'total_revenue_omr', 'marketplace_sales_omr', 'direct_sales_omr', 'b2b_sales_omr',
            'acquisition_costs_omr', 'labor_costs_omr', 'storage_costs_omr', 'overhead_costs_omr',
            'shipping_costs_omr', 'marketing_costs_omr', 'platform_fees_omr', 'total_costs_omr',
            'gross_profit_omr', 'net_profit_omr', 'profit_per_part_omr', 'average_order_value_omr'
        ];

        currency_fields.forEach(field => {
            if (frm.fields_dict[field] && frm.doc[field]) {
                let formatted_value = format_currency_arabic(frm.doc[field]);
                frm.fields_dict[field].$wrapper.find('.control-value').text(formatted_value);
            }
        });
    },

    show_dashboard: function (frm) {
        // Show comprehensive dashboard in dialog
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.profit_analysis.profit_analysis.get_profit_analysis_dashboard',
            args: {
                analysis_id: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('render_dashboard_dialog', [r.message]);
                }
            }
        });
    },

    render_dashboard_dialog: function (frm, dashboard_data) {
        let dialog = new frappe.ui.Dialog({
            title: __('Profit Analysis Dashboard') + ' - ' + frm.doc.analysis_name,
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'dashboard_html'
                }
            ]
        });

        let html = frm.trigger('generate_dashboard_html', [dashboard_data]);
        dialog.fields_dict.dashboard_html.$wrapper.html(html);
        dialog.show();
    },

    generate_dashboard_html: function (frm, data) {
        return `
            <div class="comprehensive-dashboard" dir="${frappe.boot.lang === 'ar' ? 'rtl' : 'ltr'}">
                <!-- Revenue Section -->
                <div class="dashboard-section">
                    <h4>${__('Revenue Analysis')} | ${__('تحليل الإيرادات')}</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="metric-box">
                                <span class="metric-label">${__('Total Revenue')}</span>
                                <span class="metric-value">${format_currency(data.revenue_metrics.total_revenue || 0, 'OMR')}</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-box">
                                <span class="metric-label">${__('Marketplace Sales')}</span>
                                <span class="metric-value">${format_currency(data.revenue_metrics.marketplace_sales || 0, 'OMR')}</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-box">
                                <span class="metric-label">${__('Direct Sales')}</span>
                                <span class="metric-value">${format_currency(data.revenue_metrics.direct_sales || 0, 'OMR')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Profitability Section -->
                <div class="dashboard-section">
                    <h4>${__('Profitability Analysis')} | ${__('تحليل الربحية')}</h4>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="metric-box profit-box">
                                <span class="metric-label">${__('Gross Profit')}</span>
                                <span class="metric-value">${format_currency(data.profitability_metrics.gross_profit || 0, 'OMR')}</span>
                                <span class="metric-percentage">${data.profitability_metrics.gross_margin || 0}%</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box profit-box">
                                <span class="metric-label">${__('Net Profit')}</span>
                                <span class="metric-value">${format_currency(data.profitability_metrics.net_profit || 0, 'OMR')}</span>
                                <span class="metric-percentage">${data.profitability_metrics.net_margin || 0}%</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box roi-box">
                                <span class="metric-label">${__('ROI')}</span>
                                <span class="metric-value">${data.profitability_metrics.roi || 0}%</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-box">
                                <span class="metric-label">${__('Profit per Part')}</span>
                                <span class="metric-value">${format_currency(data.profitability_metrics.profit_per_part || 0, 'OMR')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Cost Breakdown Chart -->
                <div class="dashboard-section">
                    <h4>${__('Cost Breakdown')} | ${__('تفصيل التكاليف')}</h4>
                    <div class="cost-breakdown-chart">
                        <canvas id="costBreakdownChart" width="400" height="200"></canvas>
                    </div>
                </div>

                <!-- Performance Data -->
                <div class="dashboard-section">
                    <h4>${__('Performance Insights')} | ${__('رؤى الأداء')}</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <h5>${__('Best Performing Parts')}</h5>
                            <div class="performance-list">
                                ${data.performance_data.best_parts.map(part => `
                                    <div class="performance-item">
                                        <strong>${part.item_name}</strong>
                                        <span class="float-right">${format_currency(part.total_sales, 'OMR')}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h5>${__('Recommendations')}</h5>
                            <div class="recommendations-list">
                                ${data.performance_data.recommendations.map(rec => `
                                    <div class="recommendation-item">
                                        <i class="fa fa-lightbulb-o"></i> ${rec}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style>
                .comprehensive-dashboard {
                    padding: 20px;
                }
                .dashboard-section {
                    margin-bottom: 30px;
                    padding: 20px;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    background: #fff;
                }
                .metric-box {
                    padding: 15px;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    text-align: center;
                    margin-bottom: 15px;
                }
                .metric-label {
                    display: block;
                    font-size: 12px;
                    color: #6c757d;
                    margin-bottom: 5px;
                }
                .metric-value {
                    display: block;
                    font-size: 18px;
                    font-weight: bold;
                    color: #2e8b57;
                }
                .metric-percentage {
                    display: block;
                    font-size: 14px;
                    color: #28a745;
                }
                .profit-box { border-left: 4px solid #007bff; }
                .roi-box { border-left: 4px solid #dc3545; }
                .performance-item, .recommendation-item {
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }
                .rtl-layout .float-right { float: left !important; }
                .rtl-layout .metric-box { text-align: right; }
            </style>
        `;
    },

    recalculate_metrics: function (frm) {
        frappe.confirm(
            __('This will recalculate all metrics based on current data. Continue?'),
            function () {
                frappe.call({
                    method: 'frappe.client.save',
                    args: {
                        doc: frm.doc
                    },
                    callback: function (r) {
                        if (r.message) {
                            frm.reload_doc();
                            frappe.show_alert({
                                message: __('Metrics recalculated successfully'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            }
        );
    },

    generate_ai_recommendations: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.profit_analysis.profit_analysis.generate_ai_recommendations',
            args: {
                analysis_id: frm.doc.name,
                analysis_data: {
                    revenue: frm.doc.total_revenue_omr,
                    profit_margin: frm.doc.net_profit_margin_percentage,
                    roi: frm.doc.roi_percentage,
                    inventory_turnover: frm.doc.inventory_turnover_ratio
                }
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('recommendations', JSON.stringify(r.message, null, 2));
                    frappe.show_alert({
                        message: __('AI recommendations generated'),
                        indicator: 'blue'
                    });
                }
            }
        });
    },

    export_analysis_report: function (frm) {
        // Export comprehensive analysis report
        window.open(
            `/api/method/universal_workshop.scrap_management.doctype.profit_analysis.profit_analysis.export_analysis_pdf?analysis_id=${frm.doc.name}`,
            '_blank'
        );
    },

    generate_next_analysis: function (frm) {
        // Generate next period analysis
        let next_from = frappe.datetime.add_days(frm.doc.analysis_period_to, 1);
        let period_days = frappe.datetime.get_diff(frm.doc.analysis_period_to, frm.doc.analysis_period_from);
        let next_to = frappe.datetime.add_days(next_from, period_days);

        frappe.new_doc('Profit Analysis', {
            analysis_name: frm.doc.analysis_name + ' - Next Period',
            analysis_name_ar: frm.doc.analysis_name_ar + ' - الفترة التالية',
            analysis_period_from: next_from,
            analysis_period_to: next_to,
            sales_channel: frm.doc.sales_channel,
            vehicle_category: frm.doc.vehicle_category,
            part_category: frm.doc.part_category
        });
    },

    analysis_period_from: function (frm) {
        // Auto-suggest period end date (30 days later)
        if (frm.doc.analysis_period_from && !frm.doc.analysis_period_to) {
            let suggested_to = frappe.datetime.add_days(frm.doc.analysis_period_from, 30);
            frm.set_value('analysis_period_to', suggested_to);
        }
    },

    analysis_name: function (frm) {
        // Auto-suggest Arabic name based on English name
        if (frm.doc.analysis_name && !frm.doc.analysis_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },

    suggest_arabic_name: function (frm) {
        // Simple mapping for common analysis types
        let arabic_suggestions = {
            'Monthly Analysis': 'التحليل الشهري',
            'Quarterly Analysis': 'التحليل الربع سنوي',
            'Annual Analysis': 'التحليل السنوي',
            'Sales Performance': 'أداء المبيعات',
            'Profit Review': 'مراجعة الأرباح',
            'Market Analysis': 'تحليل السوق'
        };

        let suggested = arabic_suggestions[frm.doc.analysis_name];
        if (suggested) {
            frm.set_value('analysis_name_ar', suggested);
        } else {
            // Generic suggestion
            frm.set_value('analysis_name_ar', 'تحليل الأرباح - ' + frm.doc.analysis_name);
        }
    }
});

// Utility functions for Arabic number formatting
function format_currency_arabic(amount) {
    if (!amount) return 'ر.ع. ٠.٠٠٠';

    let formatted = format_currency(amount, 'OMR');

    if (frappe.boot.lang === 'ar') {
        // Convert Western numerals to Arabic-Indic numerals
        const arabic_numerals = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
        };

        formatted = formatted.replace(/[0-9]/g, function (match) {
            return arabic_numerals[match];
        });

        // Replace 'OMR' with Arabic
        formatted = formatted.replace('OMR', 'ر.ع.');
    }

    return formatted;
}

function get_text_direction(text) {
    // Detect text direction for mixed content
    let arabic_chars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    let total_chars = text.replace(/\s/g, '').length;

    return (arabic_chars / total_chars > 0.3) ? 'rtl' : 'ltr';
} 