// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Channel', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_real_time_updates');
        frm.trigger('setup_financial_dashboard');
        frm.trigger('setup_integration_status');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        ['channel_name_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply Arabic formatting to currency fields in Arabic locale
        if (frappe.boot.lang === 'ar') {
            const currency_fields = ['total_sales_omr', 'commission_paid_omr', 'gross_profit_omr', 'net_profit_omr', 'average_order_value'];
            currency_fields.forEach(field => {
                if (frm.fields_dict[field] && frm.doc[field]) {
                    const value = frm.doc[field];
                    const formatted_value = format_omr_currency_arabic(value);
                    frm.fields_dict[field].$wrapper.find('.control-value').text(formatted_value);
                }
            });
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.name && !frm.is_new()) {
            // Test API Connection Button
            frm.add_custom_button(__('Test Connection'), function () {
                frm.trigger('test_api_connection');
            }, __('API'));

            // Sync Inventory Button
            frm.add_custom_button(__('Force Sync'), function () {
                frm.trigger('sync_inventory');
            }, __('Inventory'));

            // Get Pricing Recommendations
            frm.add_custom_button(__('Pricing Recommendations'), function () {
                frm.trigger('show_pricing_dialog');
            }, __('Pricing'));

            // Calculate ROI
            frm.add_custom_button(__('Calculate ROI'), function () {
                frm.trigger('calculate_roi');
            }, __('Analytics'));

            // View Channel Analytics
            frm.add_custom_button(__('View Analytics'), function () {
                frm.trigger('show_analytics_dashboard');
            }, __('Analytics'));

            // Export Sales Data
            frm.add_custom_button(__('Export Sales Data'), function () {
                frm.trigger('export_sales_data');
            }, __('Reports'));
        }
    },

    setup_real_time_updates: function (frm) {
        if (frm.doc.name && frm.doc.integration_status === 'Connected') {
            // Setup real-time status monitoring
            frm.realtime_update_interval = setInterval(() => {
                frm.trigger('update_sync_status');
            }, 30000); // Update every 30 seconds
        }

        // Clear interval when form is destroyed
        frm.$wrapper.on('remove', function () {
            if (frm.realtime_update_interval) {
                clearInterval(frm.realtime_update_interval);
            }
        });
    },

    setup_financial_dashboard: function (frm) {
        if (frm.doc.name && !frm.is_new()) {
            // Create financial metrics dashboard
            const dashboard_html = `
                <div class="row" style="margin: 15px 0;">
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #f8f9fa;">
                            <h5 style="color: #007bff;">${__('Total Sales')}</h5>
                            <h3 style="color: #28a745;">${format_omr_currency(frm.doc.total_sales_omr || 0)}</h3>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #f8f9fa;">
                            <h5 style="color: #007bff;">${__('Total Orders')}</h5>
                            <h3 style="color: #17a2b8;">${frm.doc.total_orders || 0}</h3>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #f8f9fa;">
                            <h5 style="color: #007bff;">${__('ROI Percentage')}</h5>
                            <h3 style="color: ${(frm.doc.roi_percentage || 0) > 0 ? '#28a745' : '#dc3545'};">${flt(frm.doc.roi_percentage || 0, 2)}%</h3>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #f8f9fa;">
                            <h5 style="color: #007bff;">${__('Net Profit')}</h5>
                            <h3 style="color: ${(frm.doc.net_profit_omr || 0) > 0 ? '#28a745' : '#dc3545'};">${format_omr_currency(frm.doc.net_profit_omr || 0)}</h3>
                        </div>
                    </div>
                </div>
            `;

            frm.get_field('financial_tracking_section').$wrapper.prepend(dashboard_html);
        }
    },

    setup_integration_status: function (frm) {
        if (frm.doc.integration_status) {
            const status_colors = {
                'Connected': 'green',
                'Disconnected': 'red',
                'Error': 'red',
                'Syncing': 'orange',
                'Testing': 'blue'
            };

            const color = status_colors[frm.doc.integration_status] || 'grey';
            const status_html = `<span style="color: ${color}; font-weight: bold;">● ${frm.doc.integration_status}</span>`;

            frm.get_field('integration_status').$wrapper.find('.control-value').html(status_html);
        }
    },

    test_api_connection: function (frm) {
        frappe.call({
            method: 'test_api_connection',
            doc: frm.doc,
            freeze: true,
            freeze_message: __('Testing API Connection...'),
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('API Connection Test Passed'),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('API Connection Test Failed'),
                        indicator: 'red'
                    });
                }
                frm.reload_doc();
            }
        });
    },

    sync_inventory: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.sales_channel.sales_channel.sync_channel_inventory',
            args: {
                channel_name: frm.doc.name,
                force_sync: true
            },
            freeze: true,
            freeze_message: __('Synchronizing Inventory...'),
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Inventory Sync Completed'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Sync Failed'),
                        message: r.message ? r.message.error : __('Unknown error occurred'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    show_pricing_dialog: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Pricing Recommendations'),
            fields: [
                {
                    label: __('Part Number'),
                    fieldname: 'part_number',
                    fieldtype: 'Link',
                    options: 'Item',
                    reqd: 1
                }
            ],
            primary_action_label: __('Get Recommendations'),
            primary_action(values) {
                frappe.call({
                    method: 'universal_workshop.scrap_management.doctype.sales_channel.sales_channel.get_pricing_recommendations',
                    args: {
                        channel_name: frm.doc.name,
                        part_number: values.part_number
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            const data = r.message;
                            const recommendations_html = `
                                <div style="padding: 15px;">
                                    <h4>${__('Pricing Recommendations for')} ${data.part_number}</h4>
                                    <table class="table table-bordered">
                                        <tr>
                                            <td><strong>${__('Cost Price')}</strong></td>
                                            <td>${format_omr_currency(data.cost_price)}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('Recommended Price')}</strong></td>
                                            <td style="color: green; font-weight: bold;">${format_omr_currency(data.recommended_price)}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('Markup Percentage')}</strong></td>
                                            <td>${flt(data.markup_percentage, 2)}%</td>
                                        </tr>
                                    </table>
                                </div>
                            `;

                            frappe.msgprint({
                                title: __('Pricing Recommendations'),
                                message: recommendations_html,
                                wide: true
                            });
                        }
                    }
                });
                dialog.hide();
            }
        });

        dialog.show();
    },

    calculate_roi: function (frm) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.sales_channel.sales_channel.calculate_channel_roi',
            args: {
                channel_name: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Calculating ROI...'),
            callback: function (r) {
                if (r.message && r.message.success) {
                    const metrics = r.message.metrics;
                    const roi_html = `
                        <div style="padding: 15px;">
                            <h4>${__('ROI Analysis for')} ${frm.doc.channel_name}</h4>
                            <div class="row">
                                <div class="col-md-6">
                                    <table class="table table-bordered">
                                        <tr>
                                            <td><strong>${__('Total Sales')}</strong></td>
                                            <td>${format_omr_currency(metrics.total_sales)}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('Total Orders')}</strong></td>
                                            <td>${metrics.total_orders}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('Average Order Value')}</strong></td>
                                            <td>${format_omr_currency(metrics.average_order_value)}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <table class="table table-bordered">
                                        <tr>
                                            <td><strong>${__('Gross Profit')}</strong></td>
                                            <td style="color: green;">${format_omr_currency(metrics.gross_profit)}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('Net Profit')}</strong></td>
                                            <td style="color: ${metrics.net_profit > 0 ? 'green' : 'red'};">${format_omr_currency(metrics.net_profit)}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>${__('ROI Percentage')}</strong></td>
                                            <td style="color: ${metrics.roi_percentage > 0 ? 'green' : 'red'}; font-weight: bold;">${flt(metrics.roi_percentage, 2)}%</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;

                    frappe.msgprint({
                        title: __('ROI Analysis'),
                        message: roi_html,
                        wide: true
                    });

                    frm.reload_doc();
                }
            }
        });
    },

    show_analytics_dashboard: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Channel Analytics Dashboard'),
            size: 'extra-large',
            fields: [
                {
                    label: __('Time Period'),
                    fieldname: 'period',
                    fieldtype: 'Select',
                    options: '7_days\n30_days\n90_days',
                    default: '30_days'
                },
                {
                    fieldname: 'analytics_content',
                    fieldtype: 'HTML'
                }
            ],
            primary_action_label: __('Refresh'),
            primary_action(values) {
                frm.trigger('load_analytics_data', values.period, dialog);
            }
        });

        dialog.show();
        frm.trigger('load_analytics_data', '30_days', dialog);
    },

    load_analytics_data: function (frm, period, dialog) {
        frappe.call({
            method: 'universal_workshop.scrap_management.doctype.sales_channel.sales_channel.get_channel_analytics',
            args: {
                channel_name: frm.doc.name,
                period: period || '30_days'
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    const analytics = r.message.analytics;
                    const analytics_html = frm.trigger('generate_analytics_html', analytics);
                    dialog.fields_dict.analytics_content.$wrapper.html(analytics_html);
                }
            }
        });
    },

    generate_analytics_html: function (frm, analytics) {
        // Generate comprehensive analytics HTML with charts
        return `
            <div style="padding: 20px;">
                <h4>${analytics.channel_name} (${analytics.channel_name_ar}) - ${__('Analytics')}</h4>
                
                <div class="row" style="margin: 20px 0;">
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #e3f2fd;">
                            <h6>${__('Total Sales')}</h6>
                            <h4 style="color: #1976d2;">${format_omr_currency(analytics.total_sales)}</h4>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #f3e5f5;">
                            <h6>${__('Total Orders')}</h6>
                            <h4 style="color: #7b1fa2;">${analytics.total_orders}</h4>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #e8f5e8;">
                            <h6>${__('Conversion Rate')}</h6>
                            <h4 style="color: #388e3c;">${flt(analytics.conversion_rate || 0, 2)}%</h4>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center" style="padding: 15px; background: #fff3e0;">
                            <h6>${__('ROI')}</h6>
                            <h4 style="color: #f57c00;">${flt(analytics.roi_percentage || 0, 2)}%</h4>
                        </div>
                    </div>
                </div>
                
                <div id="sales_chart" style="height: 300px; margin: 20px 0;"></div>
                
                <div class="row">
                    <div class="col-md-12">
                        <h5>${__('Recent Sales Data')}</h5>
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>${__('Date')}</th>
                                    <th>${__('Orders')}</th>
                                    <th>${__('Sales (OMR)')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${analytics.sales_data.map(row => `
                                    <tr>
                                        <td>${row.date}</td>
                                        <td>${row.orders}</td>
                                        <td>${format_omr_currency(row.sales)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },

    update_sync_status: function (frm) {
        if (frm.doc.name) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Sales Channel',
                    name: frm.doc.name,
                    fieldname: ['integration_status', 'last_inventory_sync', 'error_log']
                },
                callback: function (r) {
                    if (r.message) {
                        const current_status = frm.doc.integration_status;
                        const new_status = r.message.integration_status;

                        if (current_status !== new_status) {
                            frm.doc.integration_status = new_status;
                            frm.doc.last_inventory_sync = r.message.last_inventory_sync;
                            frm.doc.error_log = r.message.error_log;
                            frm.refresh_field('integration_status');
                            frm.refresh_field('last_inventory_sync');
                            frm.refresh_field('error_log');
                            frm.trigger('setup_integration_status');
                        }
                    }
                }
            });
        }
    },

    export_sales_data: function (frm) {
        const export_url = `/api/method/frappe.desk.reportview.export_query?doctype=Sales Order&file_format_type=Excel&filters=[["sales_channel","=","${frm.doc.name}"]]`;
        window.open(export_url, '_blank');
    },

    // Field event handlers
    platform: function (frm) {
        if (frm.doc.platform) {
            frm.trigger('set_platform_defaults');
        }
    },

    set_platform_defaults: function (frm) {
        const platform_defaults = {
            'eBay': {
                'commission_rate': 10,
                'api_endpoint': 'https://api.ebay.com/',
                'rate_limit_per_minute': 5000
            },
            'Amazon': {
                'commission_rate': 15,
                'api_endpoint': 'https://sellingpartnerapi-na.amazon.com/',
                'rate_limit_per_minute': 200
            },
            'OpenSooq': {
                'commission_rate': 5,
                'api_endpoint': 'https://api.opensooq.com/',
                'rate_limit_per_minute': 1000
            },
            'Shopify': {
                'commission_rate': 2.9,
                'api_endpoint': 'https://{shop}.myshopify.com/admin/api/2023-10/',
                'rate_limit_per_minute': 2000
            }
        };

        const defaults = platform_defaults[frm.doc.platform];
        if (defaults) {
            Object.keys(defaults).forEach(field => {
                if (!frm.doc[field]) {
                    frm.set_value(field, defaults[field]);
                }
            });
        }
    },

    channel_name: function (frm) {
        if (frm.doc.channel_name && !frm.doc.channel_name_ar) {
            // Auto-suggest Arabic name
            frm.trigger('suggest_arabic_name');
        }
    },

    suggest_arabic_name: function (frm) {
        const arabic_suggestions = {
            'eBay': 'إي باي',
            'Amazon': 'أمازون',
            'OpenSooq': 'أوبن سوق',
            'Dubizzle': 'دوبيزل',
            'Shopify': 'شوبيفاي',
            'Store': 'متجر',
            'Shop': 'متجر',
            'Market': 'سوق',
            'Auto Parts': 'قطع غيار السيارات',
            'Workshop': 'ورشة'
        };

        let suggested_name = frm.doc.channel_name;
        Object.keys(arabic_suggestions).forEach(english => {
            suggested_name = suggested_name.replace(new RegExp(english, 'gi'), arabic_suggestions[english]);
        });

        if (suggested_name !== frm.doc.channel_name) {
            frm.set_value('channel_name_ar', suggested_name);
        }
    }
});

// Utility functions
function format_omr_currency(amount) {
    if (!amount) return 'OMR 0.000';
    return `OMR ${parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 3,
        maximumFractionDigits: 3
    })}`;
}

function format_omr_currency_arabic(amount) {
    if (!amount) return 'ر.ع. ٠.٠٠٠';
    const arabic_numerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let formatted = parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 3,
        maximumFractionDigits: 3
    });

    // Convert to Arabic numerals
    for (let i = 0; i <= 9; i++) {
        formatted = formatted.replace(new RegExp(i.toString(), 'g'), arabic_numerals[i]);
    }

    return `ر.ع. ${formatted}`;
} 