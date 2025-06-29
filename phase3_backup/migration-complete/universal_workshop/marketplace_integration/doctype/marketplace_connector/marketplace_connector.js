// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Marketplace Connector', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_status_indicators');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_connection_status');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['connector_name_ar'];
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply RTL to text areas if Arabic content detected
        ['warranty_terms_template', 'return_policy_template', 'regulatory_notes'].forEach(field => {
            if (frm.fields_dict[field] && frm.doc[field]) {
                const text = frm.doc[field];
                if (has_arabic_content(text)) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                }
            }
        });
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        if (!frm.doc.__islocal) {
            // Test Connection button
            frm.add_custom_button(__('Test Connection'), function () {
                frm.trigger('test_connection');
            }, __('Actions'));

            // Sync buttons based on connector status
            if (frm.doc.status === 'Connected' && frm.doc.is_active) {
                // Manual sync buttons
                frm.add_custom_button(__('Sync Products'), function () {
                    frm.trigger('sync_data', 'products');
                }, __('Sync'));

                frm.add_custom_button(__('Sync Inventory'), function () {
                    frm.trigger('sync_data', 'inventory');
                }, __('Sync'));

                frm.add_custom_button(__('Sync Orders'), function () {
                    frm.trigger('sync_data', 'orders');
                }, __('Sync'));

                frm.add_custom_button(__('Sync All'), function () {
                    frm.trigger('sync_data', 'all');
                }, __('Sync'));

                // OAuth token refresh for OAuth 2.0
                if (frm.doc.auth_method === 'OAuth 2.0') {
                    frm.add_custom_button(__('Refresh Token'), function () {
                        frm.trigger('refresh_oauth_token');
                    }, __('OAuth'));
                }
            }

            // Configuration buttons
            frm.add_custom_button(__('View Sync Logs'), function () {
                frm.trigger('view_sync_logs');
            }, __('Reports'));

            frm.add_custom_button(__('Export Configuration'), function () {
                frm.trigger('export_configuration');
            }, __('Tools'));

            // Dashboard button
            frm.add_custom_button(__('Connector Dashboard'), function () {
                frm.trigger('open_dashboard');
            }, __('Reports'));
        }
    },

    setup_status_indicators: function (frm) {
        // Add status indicators to the form
        if (frm.doc.status) {
            let color = 'grey';
            let icon = 'fa fa-circle';

            switch (frm.doc.status) {
                case 'Connected':
                    color = 'green';
                    icon = 'fa fa-check-circle';
                    break;
                case 'Error':
                    color = 'red';
                    icon = 'fa fa-times-circle';
                    break;
                case 'Disconnected':
                    color = 'orange';
                    icon = 'fa fa-exclamation-circle';
                    break;
                case 'Suspended':
                    color = 'darkred';
                    icon = 'fa fa-ban';
                    break;
            }

            frm.dashboard.add_indicator(__('Status: {0}', [frm.doc.status]), color, icon);
        }

        // Add sync statistics indicators
        if (frm.doc.total_products_synced) {
            frm.dashboard.add_indicator(__('Products Synced: {0}', [frm.doc.total_products_synced]), 'blue');
        }

        if (frm.doc.sync_success_rate) {
            let rate_color = frm.doc.sync_success_rate >= 90 ? 'green' :
                frm.doc.sync_success_rate >= 70 ? 'orange' : 'red';
            frm.dashboard.add_indicator(__('Success Rate: {0}%', [frm.doc.sync_success_rate.toFixed(1)]), rate_color);
        }

        // Token expiry warning for OAuth
        if (frm.doc.auth_method === 'OAuth 2.0' && frm.doc.token_expires_at) {
            const expiry = new Date(frm.doc.token_expires_at);
            const now = new Date();
            const hours_until_expiry = (expiry - now) / (1000 * 60 * 60);

            if (hours_until_expiry < 24 && hours_until_expiry > 0) {
                frm.dashboard.add_indicator(__('Token Expires Soon'), 'orange', 'fa fa-clock-o');
            } else if (hours_until_expiry <= 0) {
                frm.dashboard.add_indicator(__('Token Expired'), 'red', 'fa fa-times');
            }
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on authentication method
        frm.trigger('toggle_auth_fields');

        // Show/hide OAuth fields
        frm.toggle_display(['oauth_section'], frm.doc.auth_method === 'OAuth 2.0');

        // Show/hide sync settings based on auto sync
        frm.toggle_reqd('sync_frequency', frm.doc.auto_sync_enabled);
    },

    auth_method: function (frm) {
        frm.trigger('toggle_auth_fields');
        frm.trigger('setup_field_dependencies');
    },

    toggle_auth_fields: function (frm) {
        // Reset all auth fields
        frm.toggle_reqd(['api_key', 'api_secret', 'access_token', 'oauth_client_id', 'oauth_client_secret'], false);

        switch (frm.doc.auth_method) {
            case 'API Key':
                frm.toggle_reqd('api_key', true);
                break;
            case 'OAuth 2.0':
                frm.toggle_reqd(['oauth_client_id', 'oauth_client_secret'], true);
                break;
            case 'Bearer Token':
                frm.toggle_reqd('access_token', true);
                break;
            case 'Basic Auth':
                frm.toggle_reqd(['api_key', 'api_secret'], true);
                break;
        }
    },

    auto_sync_enabled: function (frm) {
        frm.trigger('setup_field_dependencies');
    },

    marketplace_platform: function (frm) {
        // Auto-fill platform-specific settings
        if (frm.doc.marketplace_platform) {
            frm.trigger('setup_platform_defaults');
        }
    },

    setup_platform_defaults: function (frm) {
        const platform_defaults = {
            'Dubizzle Motors': {
                marketplace_url: 'https://dubai.dubizzle.com/motors/',
                platform_region: 'UAE',
                default_currency: 'AED',
                supported_languages: 'en,ar',
                max_images_per_listing: 10,
                rate_limit_per_minute: 60
            },
            'OpenSooq': {
                marketplace_url: 'https://om.opensooq.com/cars',
                platform_region: 'Oman',
                default_currency: 'OMR',
                supported_languages: 'ar,en',
                max_images_per_listing: 8,
                rate_limit_per_minute: 30
            },
            'YallaMotor': {
                marketplace_url: 'https://www.yallamotor.com/',
                platform_region: 'UAE',
                default_currency: 'AED',
                supported_languages: 'en,ar',
                max_images_per_listing: 12,
                rate_limit_per_minute: 100
            },
            'Amazon Automotive': {
                marketplace_url: 'https://www.amazon.ae/automotive',
                platform_region: 'UAE',
                default_currency: 'AED',
                supported_languages: 'en,ar',
                max_images_per_listing: 9,
                rate_limit_per_minute: 200
            }
        };

        const defaults = platform_defaults[frm.doc.marketplace_platform];
        if (defaults) {
            Object.keys(defaults).forEach(field => {
                if (!frm.doc[field]) {
                    frm.set_value(field, defaults[field]);
                }
            });
        }
    },

    test_connection: function (frm) {
        if (!frm.doc.api_endpoint) {
            frappe.msgprint(__('Please set API endpoint before testing connection'));
            return;
        }

        frm.call({
            method: 'test_connection',
            doc: frm.doc,
            btn: $('.btn-test-connection'),
            callback: function (r) {
                if (r.message) {
                    if (r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frm.refresh();
                    } else {
                        frappe.msgprint({
                            title: __('Connection Failed'),
                            message: r.message.message,
                            indicator: 'red'
                        });
                    }
                }
            }
        });
    },

    refresh_oauth_token: function (frm) {
        frm.call({
            method: 'refresh_oauth_token',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    if (r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frm.refresh();
                    } else {
                        frappe.msgprint({
                            title: __('Token Refresh Failed'),
                            message: r.message.message,
                            indicator: 'red'
                        });
                    }
                }
            }
        });
    },

    sync_data: function (frm, sync_type) {
        frappe.confirm(__('Are you sure you want to sync {0} data to {1}?',
            [sync_type, frm.doc.marketplace_platform]), function () {

                const sync_dialog = frappe.msgprint({
                    title: __('Syncing Data'),
                    message: __('Synchronization in progress. Please wait...'),
                    indicator: 'blue'
                });

                frm.call({
                    method: 'sync_to_marketplace',
                    doc: frm.doc,
                    args: {
                        sync_type: sync_type
                    },
                    callback: function (r) {
                        sync_dialog.hide();

                        if (r.message) {
                            if (r.message.status === 'success') {
                                frm.trigger('show_sync_results', r.message.results);
                                frm.refresh();
                            } else {
                                frappe.msgprint({
                                    title: __('Sync Failed'),
                                    message: r.message.message,
                                    indicator: 'red'
                                });
                            }
                        }
                    }
                });
            });
    },

    show_sync_results: function (frm, results) {
        let message = __('Synchronization completed successfully:') + '<br><br>';

        Object.keys(results).forEach(sync_type => {
            const result = results[sync_type];
            if (typeof result === 'object' && result.total_processed !== undefined) {
                message += `<strong>${__(sync_type.toUpperCase())}:</strong><br>`;
                message += `${__('Total Processed')}: ${result.total_processed}<br>`;
                message += `${__('Successful')}: ${result.successful}<br>`;
                message += `${__('Failed')}: ${result.failed}<br><br>`;
            }
        });

        frappe.msgprint({
            title: __('Sync Results'),
            message: message,
            indicator: 'green'
        });
    },

    view_sync_logs: function (frm) {
        frappe.route_options = {
            "connector": frm.doc.name
        };
        frappe.set_route("List", "Marketplace Sync Log");
    },

    export_configuration: function (frm) {
        const config_data = {
            connector_name: frm.doc.connector_name,
            marketplace_platform: frm.doc.marketplace_platform,
            platform_region: frm.doc.platform_region,
            api_endpoint: frm.doc.api_endpoint,
            auth_method: frm.doc.auth_method,
            sync_settings: {
                auto_sync_enabled: frm.doc.auto_sync_enabled,
                sync_frequency: frm.doc.sync_frequency,
                sync_products: frm.doc.sync_products,
                sync_inventory: frm.doc.sync_inventory,
                sync_orders: frm.doc.sync_orders,
                sync_pricing: frm.doc.sync_pricing
            },
            mappings: {
                category_mapping: frm.doc.category_mapping,
                attribute_mapping: frm.doc.attribute_mapping,
                condition_grade_mapping: frm.doc.condition_grade_mapping
            }
        };

        const config_json = JSON.stringify(config_data, null, 2);

        // Create download link
        const blob = new Blob([config_json], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${frm.doc.connector_name}_config.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        frappe.show_alert({
            message: __('Configuration exported successfully'),
            indicator: 'green'
        });
    },

    open_dashboard: function (frm) {
        // Open marketplace connector dashboard
        const dashboard_url = `/app/marketplace-connector-dashboard/${frm.doc.name}`;
        window.open(dashboard_url, '_blank');
    },

    update_connection_status: function (frm) {
        // Auto-update connection status every 30 seconds if form is open
        if (!frm.doc.__islocal && frm.doc.is_active) {
            setTimeout(function () {
                if (frm.is_dirty() === false) { // Only if form is not being edited
                    frm.refresh_field('last_sync_datetime');
                    frm.refresh_field('total_api_calls_today');
                }
                frm.trigger('update_connection_status');
            }, 30000);
        }
    },

    // Field validation functions
    api_endpoint: function (frm) {
        if (frm.doc.api_endpoint && !is_valid_url(frm.doc.api_endpoint)) {
            frappe.msgprint(__('Please enter a valid API endpoint URL'));
            frm.set_value('api_endpoint', '');
        }
    },

    marketplace_url: function (frm) {
        if (frm.doc.marketplace_url && !is_valid_url(frm.doc.marketplace_url)) {
            frappe.msgprint(__('Please enter a valid marketplace URL'));
            frm.set_value('marketplace_url', '');
        }
    },

    error_notification_email: function (frm) {
        if (frm.doc.error_notification_email && !is_valid_email(frm.doc.error_notification_email)) {
            frappe.msgprint(__('Please enter a valid email address'));
            frm.set_value('error_notification_email', '');
        }
    },

    rate_limit_per_minute: function (frm) {
        if (frm.doc.rate_limit_per_minute && (frm.doc.rate_limit_per_minute < 1 || frm.doc.rate_limit_per_minute > 1000)) {
            frappe.msgprint(__('Rate limit should be between 1 and 1000 requests per minute'));
        }
    },

    retry_attempts: function (frm) {
        if (frm.doc.retry_attempts && (frm.doc.retry_attempts < 1 || frm.doc.retry_attempts > 10)) {
            frappe.msgprint(__('Retry attempts should be between 1 and 10'));
            frm.set_value('retry_attempts', 3);
        }
    },

    max_log_retention_days: function (frm) {
        if (frm.doc.max_log_retention_days && (frm.doc.max_log_retention_days < 1 || frm.doc.max_log_retention_days > 365)) {
            frappe.msgprint(__('Log retention should be between 1 and 365 days'));
            frm.set_value('max_log_retention_days', 30);
        }
    }
});

// Utility functions
function has_arabic_content(text) {
    const arabic_pattern = /[\u0600-\u06FF]/;
    return arabic_pattern.test(text);
}

function is_valid_url(url) {
    const url_pattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return url_pattern.test(url);
}

function is_valid_email(email) {
    const email_pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return email_pattern.test(email);
}

// Auto-refresh form data every minute for active connectors
frappe.realtime.on("marketplace_connector_update", function (data) {
    if (cur_frm && cur_frm.doc.name === data.connector_name) {
        cur_frm.refresh_fields(['total_products_synced', 'total_orders_received',
            'last_successful_sync', 'sync_success_rate']);
    }
}); 