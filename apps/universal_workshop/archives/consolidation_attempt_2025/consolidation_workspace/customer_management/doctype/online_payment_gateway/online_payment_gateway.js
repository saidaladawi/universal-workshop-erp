// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Online Payment Gateway', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_interface');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_real_time_monitoring');
        frm.trigger('setup_conditional_fields');
        frm.trigger('load_transaction_statistics');
    },

    setup_arabic_interface: function (frm) {
        // Apply RTL layout for Arabic interface
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Set RTL direction for Arabic fields
            const arabic_fields = [
                'gateway_name_ar', 'description_ar', 'notes_ar',
                'customer_notification_template_ar', 'failure_notification_template_ar'
            ];

            arabic_fields.forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                }
            });
        }

        // Auto-translate gateway name
        if (frm.doc.gateway_name && !frm.doc.gateway_name_ar) {
            frm.trigger('suggest_arabic_translation');
        }
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        if (frm.doc.name && !frm.is_new()) {
            // Test Connection button
            frm.add_custom_button(__('Test Connection'), function () {
                frm.trigger('test_gateway_connection');
            }, __('Actions'));

            // View Transaction Log button
            frm.add_custom_button(__('Transaction Log'), function () {
                frm.trigger('view_transaction_log');
            }, __('Reports'));

            // Payment Statistics button
            frm.add_custom_button(__('Payment Statistics'), function () {
                frm.trigger('show_payment_statistics');
            }, __('Reports'));

            // Create Test Payment button
            if (frm.doc.is_test_mode) {
                frm.add_custom_button(__('Create Test Payment'), function () {
                    frm.trigger('create_test_payment');
                }, __('Test'));
            }

            // Sync with ERPNext button
            if (frm.doc.erpnext_integration) {
                frm.add_custom_button(__('Sync with ERPNext'), function () {
                    frm.trigger('sync_with_erpnext');
                }, __('Integration'));
            }

            // Arabic Interface Test button
            frm.add_custom_button(__('Test Arabic Interface'), function () {
                frm.trigger('test_arabic_interface');
            }, __('Test'));
        }
    },

    setup_real_time_monitoring: function (frm) {
        if (frm.doc.name && frm.doc.is_active && !frm.is_new()) {
            // Start real-time monitoring for active gateways
            frm.realtime_monitoring = setInterval(function () {
                frm.trigger('update_gateway_status');
            }, 60000); // Update every minute

            // Initial status update
            frm.trigger('update_gateway_status');
        }
    },

    setup_conditional_fields: function (frm) {
        // Show/hide fields based on provider selection
        frm.trigger('toggle_provider_fields');

        // Show/hide test mode fields
        frm.toggle_display(['test_api_key', 'test_secret_key'], frm.doc.is_test_mode);

        // Show/hide Arabic fields
        frm.toggle_display(['gateway_name_ar', 'description_ar', 'notes_ar'], frm.doc.arabic_interface);

        // Show/hide OMR specific fields
        frm.toggle_display(['vat_handling', 'receipt_format'], frm.doc.omr_support);

        // Show/hide advanced security fields
        frm.toggle_display(['fraud_detection', 'risk_assessment', 'encryption_type'], frm.doc.advanced_security);

        // Show/hide webhook fields
        frm.toggle_display(['webhook_url', 'webhook_secret'], frm.doc.webhook_enabled);
    },

    load_transaction_statistics: function (frm) {
        if (frm.doc.name && !frm.is_new()) {
            frappe.call({
                method: 'universal_workshop.customer_portal.api.get_gateway_statistics',
                args: {
                    gateway_name: frm.doc.name,
                    period: '30_days'
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frm.trigger('display_statistics', [r.message.data]);
                    }
                }
            });
        }
    },

    display_statistics: function (frm, stats) {
        const dashboard = frm.dashboard;
        dashboard.clear_headlines();

        if (stats && stats.length > 0) {
            const data = stats[0];

            // Add statistics cards
            dashboard.add_indicator(__('Success Rate'), data.success_rate + '%',
                data.success_rate > 95 ? 'green' : data.success_rate > 85 ? 'orange' : 'red');

            dashboard.add_indicator(__('Total Transactions'), data.total_transactions, 'blue');

            dashboard.add_indicator(__('Average Response Time'), data.avg_response_time + 'ms',
                data.avg_response_time < 2000 ? 'green' : 'orange');

            dashboard.add_indicator(__('Uptime'), data.uptime + '%',
                data.uptime > 99 ? 'green' : 'orange');
        }
    },

    gateway_provider: function (frm) {
        frm.trigger('toggle_provider_fields');
        frm.trigger('set_default_endpoints');
    },

    toggle_provider_fields: function (frm) {
        const provider = frm.doc.gateway_provider;

        // Show/hide provider-specific fields
        const stripe_fields = ['stripe_webhook_endpoint', 'stripe_public_key'];
        const paytabs_fields = ['paytabs_profile_id', 'paytabs_server_key'];
        const payfort_fields = ['payfort_merchant_identifier', 'payfort_access_code'];
        const omannet_fields = ['omannet_merchant_code', 'omannet_terminal_id'];

        // Hide all provider-specific fields first
        [].concat(stripe_fields, paytabs_fields, payfort_fields, omannet_fields).forEach(field => {
            frm.toggle_display([field], false);
        });

        // Show relevant fields based on provider
        switch (provider) {
            case 'Stripe':
                stripe_fields.forEach(field => frm.toggle_display([field], true));
                break;
            case 'PayTabs':
                paytabs_fields.forEach(field => frm.toggle_display([field], true));
                break;
            case 'PayFort':
                payfort_fields.forEach(field => frm.toggle_display([field], true));
                break;
            case 'OmanNet':
                omannet_fields.forEach(field => frm.toggle_display([field], true));
                break;
        }
    },

    set_default_endpoints: function (frm) {
        const provider = frm.doc.gateway_provider;
        const mode = frm.doc.is_test_mode ? 'test' : 'live';

        const endpoints = {
            'Stripe': {
                'live': 'https://api.stripe.com/v1',
                'test': 'https://api.stripe.com/v1'
            },
            'PayTabs': {
                'live': 'https://secure.paytabs.com/payment/request',
                'test': 'https://secure-egypt.paytabs.com/payment/request'
            },
            'PayFort': {
                'live': 'https://paymentservices.amazon.com/payment',
                'test': 'https://sbpaymentservices.payfort.com/FortAPI'
            },
            'OmanNet': {
                'live': 'https://gateway.omannet.om/api/v1',
                'test': 'https://test.omannet.om/api/v1'
            }
        };

        if (endpoints[provider] && endpoints[provider][mode] && !frm.doc.api_endpoint) {
            frm.set_value('api_endpoint', endpoints[provider][mode]);
        }
    },

    is_test_mode: function (frm) {
        frm.trigger('set_default_endpoints');
        frm.toggle_display(['test_api_key', 'test_secret_key'], frm.doc.is_test_mode);
    },

    arabic_interface: function (frm) {
        frm.toggle_display(['gateway_name_ar', 'description_ar', 'notes_ar'], frm.doc.arabic_interface);

        if (frm.doc.arabic_interface && !frm.doc.gateway_name_ar) {
            frm.trigger('suggest_arabic_translation');
        }
    },

    omr_support: function (frm) {
        frm.toggle_display(['vat_handling', 'receipt_format'], frm.doc.omr_support);

        if (frm.doc.omr_support && frm.doc.default_currency !== 'OMR') {
            frappe.msgprint(__('Consider setting default currency to OMR when OMR support is enabled'));
        }
    },

    webhook_enabled: function (frm) {
        frm.toggle_display(['webhook_url', 'webhook_secret'], frm.doc.webhook_enabled);
    },

    test_gateway_connection: function (frm) {
        frappe.show_alert({
            message: __('Testing gateway connection...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'test_connection',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    const result = JSON.parse(r.message);

                    if (result.success) {
                        frappe.show_alert({
                            message: __('Connection test successful'),
                            indicator: 'green'
                        });

                        frm.set_value('test_status', 'Passed');
                        frm.set_value('last_tested', frappe.datetime.now_datetime());

                    } else {
                        frappe.show_alert({
                            message: __('Connection test failed'),
                            indicator: 'red'
                        });

                        frm.set_value('test_status', 'Failed');
                    }

                    frm.set_value('test_results', JSON.stringify(result, null, 2));
                    frm.refresh_field('test_results');
                }
            }
        });
    },

    view_transaction_log: function (frm) {
        frappe.route_options = {
            'gateway': frm.doc.name
        };
        frappe.set_route('List', 'Payment Transaction Log');
    },

    show_payment_statistics: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Payment Gateway Statistics'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'statistics_html'
                }
            ]
        });

        frappe.call({
            method: 'universal_workshop.customer_portal.api.get_detailed_gateway_statistics',
            args: {
                gateway_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    const stats = r.message.data;
                    const html = frm.trigger('build_statistics_html', [stats]);
                    dialog.fields_dict.statistics_html.$wrapper.html(html);
                }
            }
        });

        dialog.show();
    },

    build_statistics_html: function (frm, stats) {
        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header"><strong>${__('Transaction Summary')}</strong></div>
                        <div class="card-body">
                            <p>${__('Total Transactions')}: ${stats.total_transactions || 0}</p>
                            <p>${__('Successful')}: ${stats.successful_transactions || 0}</p>
                            <p>${__('Failed')}: ${stats.failed_transactions || 0}</p>
                            <p>${__('Success Rate')}: ${stats.success_rate || 0}%</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header"><strong>${__('Performance Metrics')}</strong></div>
                        <div class="card-body">
                            <p>${__('Average Response Time')}: ${stats.avg_response_time || 0}ms</p>
                            <p>${__('Uptime')}: ${stats.uptime || 0}%</p>
                            <p>${__('Last Health Check')}: ${stats.last_health_check || 'Never'}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header"><strong>${__('Recent Activity')}</strong></div>
                        <div class="card-body">
                            <canvas id="transaction-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    create_test_payment: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Create Test Payment'),
            fields: [
                {
                    fieldtype: 'Currency',
                    fieldname: 'amount',
                    label: __('Amount'),
                    reqd: 1,
                    default: 10.000
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'currency',
                    label: __('Currency'),
                    options: 'OMR\nUSD\nEUR\nAED',
                    default: 'OMR',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'customer_email',
                    label: __('Customer Email'),
                    default: 'test@example.com'
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'description',
                    label: __('Description'),
                    default: 'Test Payment'
                }
            ],
            primary_action_label: __('Create Payment'),
            primary_action: function () {
                const values = dialog.get_values();

                frappe.call({
                    method: 'create_payment_request',
                    doc: frm.doc,
                    args: values,
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Test payment created successfully'),
                                indicator: 'green'
                            });

                            if (r.message.payment_url) {
                                window.open(r.message.payment_url, '_blank');
                            }

                        } else {
                            frappe.show_alert({
                                message: __('Failed to create test payment'),
                                indicator: 'red'
                            });
                        }

                        dialog.hide();
                    }
                });
            }
        });

        dialog.show();
    },

    sync_with_erpnext: function (frm) {
        frappe.call({
            method: 'sync_with_erpnext',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Sync completed successfully'),
                        indicator: 'green'
                    });

                    frm.reload_doc();
                }
            }
        });
    },

    test_arabic_interface: function (frm) {
        if (!frm.doc.arabic_interface) {
            frappe.msgprint(__('Arabic interface is not enabled for this gateway'));
            return;
        }

        // Create a test dialog with Arabic interface
        const dialog = new frappe.ui.Dialog({
            title: 'واجهة الدفع العربية - اختبار',
            fields: [
                {
                    fieldtype: 'Currency',
                    fieldname: 'amount',
                    label: 'المبلغ',
                    reqd: 1,
                    default: 10.000
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'customer_name',
                    label: 'اسم العميل',
                    default: 'أحمد محمد'
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'description',
                    label: 'وصف الدفعة',
                    default: 'دفعة تجريبية'
                }
            ],
            primary_action_label: 'إنشاء دفعة تجريبية',
            primary_action: function () {
                frappe.show_alert({
                    message: 'تم اختبار الواجهة العربية بنجاح',
                    indicator: 'green'
                });
                dialog.hide();
            }
        });

        // Apply RTL to dialog
        dialog.$wrapper.addClass('rtl-layout');
        dialog.$wrapper.find('input, textarea').attr('dir', 'rtl').css('text-align', 'right');

        dialog.show();
    },

    suggest_arabic_translation: function (frm) {
        if (!frm.doc.gateway_name) return;

        const translations = {
            'Stripe': 'سترايب',
            'PayTabs': 'بي تابس',
            'PayPal': 'باي بال',
            'PayFort': 'بي فورت',
            'OmanNet': 'عمان نت',
            'Credit Card': 'بطاقة ائتمان',
            'Debit Card': 'بطاقة خصم',
            'Bank Transfer': 'تحويل بنكي',
            'Mobile Payment': 'دفع بالهاتف المحمول'
        };

        const arabic_name = translations[frm.doc.gateway_name];
        if (arabic_name) {
            frm.set_value('gateway_name_ar', arabic_name);
        }
    },

    update_gateway_status: function (frm) {
        if (!frm.doc.name || frm.is_new()) return;

        frappe.call({
            method: 'universal_workshop.customer_portal.api.get_gateway_status',
            args: {
                gateway_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    const status = r.message.status;

                    // Update status indicator
                    frm.dashboard.set_headline_alert(
                        status.is_online ?
                            `<div class="indicator green">${__('Online')}</div>` :
                            `<div class="indicator red">${__('Offline')}</div>`
                    );

                    // Update response time
                    if (status.response_time) {
                        frm.set_value('average_response_time', status.response_time);
                    }

                    // Update last health check
                    frm.set_value('last_health_check', frappe.datetime.now_datetime());
                }
            }
        });
    },

    on_submit: function (frm) {
        frappe.show_alert({
            message: __('Payment Gateway activated successfully'),
            indicator: 'green'
        });
    },

    before_load: function (frm) {
        // Clear any existing intervals
        if (frm.realtime_monitoring) {
            clearInterval(frm.realtime_monitoring);
        }
    }
});

// Field-specific events
frappe.ui.form.on('Online Payment Gateway', 'minimum_amount', function (frm) {
    if (frm.doc.minimum_amount && frm.doc.maximum_amount) {
        if (parseFloat(frm.doc.minimum_amount) >= parseFloat(frm.doc.maximum_amount)) {
            frappe.msgprint(__('Minimum amount should be less than maximum amount'));
            frm.set_value('minimum_amount', 0);
        }
    }
});

frappe.ui.form.on('Online Payment Gateway', 'maximum_amount', function (frm) {
    if (frm.doc.minimum_amount && frm.doc.maximum_amount) {
        if (parseFloat(frm.doc.maximum_amount) <= parseFloat(frm.doc.minimum_amount)) {
            frappe.msgprint(__('Maximum amount should be greater than minimum amount'));
            frm.set_value('maximum_amount', '');
        }
    }
});

// Auto-format OMR amounts
frappe.ui.form.on('Online Payment Gateway', 'minimum_amount', function (frm) {
    if (frm.doc.default_currency === 'OMR' && frm.doc.minimum_amount) {
        frm.set_value('minimum_amount', parseFloat(frm.doc.minimum_amount).toFixed(3));
    }
});

frappe.ui.form.on('Online Payment Gateway', 'maximum_amount', function (frm) {
    if (frm.doc.default_currency === 'OMR' && frm.doc.maximum_amount) {
        frm.set_value('maximum_amount', parseFloat(frm.doc.maximum_amount).toFixed(3));
    }
});

// Arabic text validation
frappe.ui.form.on('Online Payment Gateway', 'gateway_name_ar', function (frm) {
    if (frm.doc.gateway_name_ar) {
        const arabic_pattern = /[\u0600-\u06FF]/;
        if (!arabic_pattern.test(frm.doc.gateway_name_ar)) {
            frappe.msgprint(__('Arabic gateway name should contain Arabic characters'));
        }
    }
});

// Real-time form validation
frappe.ui.form.on('Online Payment Gateway', {
    validate: function (frm) {
        // Validate API endpoint URL format
        if (frm.doc.api_endpoint && !frm.trigger('is_valid_url', [frm.doc.api_endpoint])) {
            frappe.validated = false;
            frappe.msgprint(__('Please enter a valid API endpoint URL'));
        }

        // Validate webhook URL format
        if (frm.doc.webhook_url && !frm.trigger('is_valid_url', [frm.doc.webhook_url])) {
            frappe.validated = false;
            frappe.msgprint(__('Please enter a valid webhook URL'));
        }

        // Validate required fields for active gateway
        if (frm.doc.is_active && !frm.doc.is_test_mode) {
            const required_fields = ['api_key', 'merchant_id'];
            let missing_fields = [];

            required_fields.forEach(field => {
                if (!frm.doc[field]) {
                    missing_fields.push(__(frappe.meta.get_label('Online Payment Gateway', field)));
                }
            });

            if (missing_fields.length > 0) {
                frappe.validated = false;
                frappe.msgprint(__('Please fill required fields: {0}', [missing_fields.join(', ')]));
            }
        }
    },

    is_valid_url: function (frm, url) {
        const url_pattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
        return url_pattern.test(url);
    }
}); 