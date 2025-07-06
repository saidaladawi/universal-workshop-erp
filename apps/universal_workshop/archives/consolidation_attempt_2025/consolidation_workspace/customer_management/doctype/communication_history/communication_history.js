// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Communication History', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_delivery_timeline');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_status_indicators');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic content
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Apply RTL to text fields that might contain Arabic
            ['message_content_ar', 'notes', 'error_message'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'auto');
                }
            });
        }

        // Auto-detect Arabic content in message fields
        if (frm.doc.message_content_ar) {
            frm.fields_dict.message_content_ar.$input.attr('dir', 'rtl');
        }
    },

    setup_custom_buttons: function (frm) {
        if (!frm.is_new()) {
            // View Customer Communications button
            if (frm.doc.customer) {
                frm.add_custom_button(__('View All Customer Communications'), function () {
                    frappe.set_route('List', 'Communication History', {
                        'customer': frm.doc.customer
                    });
                }, __('View'));
            }

            // Delivery Timeline button
            frm.add_custom_button(__('Delivery Timeline'), function () {
                frm.trigger('show_delivery_timeline_dialog');
            }, __('View'));

            // Analytics button
            frm.add_custom_button(__('Communication Analytics'), function () {
                frm.trigger('show_analytics_dialog');
            }, __('View'));

            // Resend button for failed messages
            if (frm.doc.delivery_status === 'Failed' && frm.doc.external_message_id) {
                frm.add_custom_button(__('Retry Delivery'), function () {
                    frm.trigger('retry_delivery');
                }, __('Actions'));
            }

            // View Template button
            if (frm.doc.template_used) {
                frm.add_custom_button(__('View Template'), function () {
                    frappe.set_route('Form', 'Notification Template', frm.doc.template_used);
                }, __('View'));
            }

            // View Consent Record button
            if (frm.doc.consent_record) {
                frm.add_custom_button(__('View Consent Record'), function () {
                    frappe.set_route('Form', 'Communication Consent', frm.doc.consent_record);
                }, __('View'));
            }
        }
    },

    setup_delivery_timeline: function (frm) {
        if (!frm.is_new() && frm.doc.sent_datetime) {
            // Create delivery timeline in the form
            frm.trigger('render_delivery_timeline');
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on communication status
        frm.trigger('toggle_delivery_fields');
        frm.trigger('toggle_error_fields');
        frm.trigger('toggle_consent_fields');
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            // Auto-fill customer details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('customer_name', r.message.customer_name);
                        if (r.message.email_id && !frm.doc.email) {
                            frm.set_value('email', r.message.email_id);
                        }
                        if (r.message.mobile_no && !frm.doc.phone_number) {
                            frm.set_value('phone_number', r.message.mobile_no);
                        }
                    }
                }
            });
        }
    },

    communication_status: function (frm) {
        frm.trigger('toggle_delivery_fields');
        frm.trigger('update_status_indicators');
    },

    delivery_status: function (frm) {
        frm.trigger('toggle_error_fields');
        frm.trigger('update_status_indicators');
    },

    template_used: function (frm) {
        if (frm.doc.template_used) {
            // Load template content for preview
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Notification Template',
                    name: frm.doc.template_used
                },
                callback: function (r) {
                    if (r.message) {
                        // Show template preview
                        frm.trigger('show_template_preview', r.message);
                    }
                }
            });
        }
    },

    toggle_delivery_fields: function (frm) {
        const is_sent = ['Sent', 'Delivered', 'Read'].includes(frm.doc.communication_status);
        const is_delivered = ['Delivered', 'Read'].includes(frm.doc.delivery_status);
        const is_read = frm.doc.delivery_status === 'Read';

        frm.toggle_display('sent_datetime', is_sent);
        frm.toggle_display('delivered_datetime', is_delivered);
        frm.toggle_display('read_datetime', is_read);
        frm.toggle_display('external_message_id', is_sent);
        frm.toggle_display('external_cost', is_sent);
    },

    toggle_error_fields: function (frm) {
        const has_error = ['Failed', 'Undelivered', 'Bounced'].includes(frm.doc.delivery_status);

        frm.toggle_display('error_message', has_error);
        frm.toggle_display('delivery_attempts', has_error);

        if (has_error) {
            frm.set_df_property('error_message', 'reqd', 1);
        } else {
            frm.set_df_property('error_message', 'reqd', 0);
        }
    },

    toggle_consent_fields: function (frm) {
        const show_consent = frm.doc.communication_type === 'Marketing' ||
            frm.doc.communication_type === 'Promotion';

        frm.toggle_display('consent_given', show_consent);
        frm.toggle_display('consent_record', show_consent);

        if (show_consent && !frm.doc.consent_given) {
            frm.dashboard.add_comment(
                __('⚠️ Marketing communication requires explicit customer consent'),
                'orange',
                true
            );
        }
    },

    update_status_indicators: function (frm) {
        // Clear existing indicators
        frm.page.clear_indicator();

        // Set status indicator based on delivery status
        if (frm.doc.delivery_status === 'Delivered') {
            frm.page.set_indicator(__('Delivered'), 'green');
        } else if (frm.doc.delivery_status === 'Read') {
            frm.page.set_indicator(__('Read'), 'blue');
        } else if (frm.doc.delivery_status === 'Sent') {
            frm.page.set_indicator(__('Sent'), 'orange');
        } else if (frm.doc.delivery_status === 'Failed') {
            frm.page.set_indicator(__('Failed'), 'red');
        } else if (frm.doc.delivery_status === 'Pending') {
            frm.page.set_indicator(__('Pending'), 'yellow');
        }
    },

    render_delivery_timeline: function (frm) {
        // Get delivery timeline data
        frappe.call({
            method: 'universal_workshop.communication_management.doctype.communication_history.communication_history.get_delivery_timeline',
            args: {
                communication_id: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_timeline', r.message);
                }
            }
        });
    },

    display_timeline: function (frm, timeline_data) {
        let timeline_html = '<div class="delivery-timeline">';
        timeline_html += '<h5>' + __('Delivery Timeline') + '</h5>';

        timeline_data.forEach(function (event, index) {
            const icon = event.status === 'completed' ? '✅' :
                event.status === 'failed' ? '❌' : '⏳';
            const time = moment(event.datetime).format('DD/MM/YYYY HH:mm');

            timeline_html += `
                <div class="timeline-item ${event.status}">
                    <span class="timeline-icon">${icon}</span>
                    <span class="timeline-event">${__(event.event)}</span>
                    <span class="timeline-time">${time}</span>
                    ${event.error ? `<div class="timeline-error">${event.error}</div>` : ''}
                </div>
            `;
        });

        timeline_html += '</div>';

        // Add custom CSS
        timeline_html += `
            <style>
                .delivery-timeline .timeline-item {
                    display: flex;
                    align-items: center;
                    margin: 10px 0;
                    padding: 8px;
                    border-left: 3px solid #ddd;
                }
                .delivery-timeline .timeline-item.completed {
                    border-left-color: #28a745;
                }
                .delivery-timeline .timeline-item.failed {
                    border-left-color: #dc3545;
                }
                .delivery-timeline .timeline-icon {
                    margin-right: 10px;
                    font-size: 16px;
                }
                .delivery-timeline .timeline-event {
                    flex: 1;
                    font-weight: bold;
                }
                .delivery-timeline .timeline-time {
                    color: #6c757d;
                    font-size: 12px;
                }
                .delivery-timeline .timeline-error {
                    width: 100%;
                    color: #dc3545;
                    font-size: 12px;
                    margin-top: 5px;
                }
            </style>
        `;

        frm.dashboard.add_comment(timeline_html, 'blue', true);
    },

    show_delivery_timeline_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Delivery Timeline for {0}', [frm.doc.name]),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'timeline_html',
                    options: '<div id="timeline-container">Loading...</div>'
                }
            ],
            size: 'large'
        });

        dialog.show();

        // Load timeline data
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Communication History',
                name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    const doc = r.message;
                    let timeline_html = '<div class="timeline-detail">';

                    // Add delivery metrics
                    timeline_html += '<h6>' + __('Delivery Metrics') + '</h6>';

                    if (doc.sent_datetime && doc.delivered_datetime) {
                        const delivery_time = moment(doc.delivered_datetime).diff(moment(doc.sent_datetime), 'seconds');
                        timeline_html += `<p><strong>${__('Delivery Time')}:</strong> ${delivery_time} ${__('seconds')}</p>`;
                    }

                    if (doc.delivered_datetime && doc.read_datetime) {
                        const read_time = moment(doc.read_datetime).diff(moment(doc.delivered_datetime), 'seconds');
                        timeline_html += `<p><strong>${__('Read Time')}:</strong> ${read_time} ${__('seconds')}</p>`;
                    }

                    if (doc.external_cost) {
                        timeline_html += `<p><strong>${__('Cost')}:</strong> ${doc.external_cost} OMR</p>`;
                    }

                    timeline_html += '</div>';

                    dialog.fields_dict.timeline_html.$wrapper.html(timeline_html);
                }
            }
        });
    },

    show_analytics_dialog: function (frm) {
        let dialog = new frappe.ui.Dialog({
            title: __('Communication Analytics'),
            fields: [
                {
                    fieldtype: 'Date',
                    fieldname: 'date_from',
                    label: __('From Date'),
                    default: moment().subtract(30, 'days').format('YYYY-MM-DD')
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'date_to',
                    label: __('To Date'),
                    default: moment().format('YYYY-MM-DD')
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'analytics_html',
                    options: '<div id="analytics-container">Click "Load Analytics" to view data</div>'
                }
            ],
            primary_action_label: __('Load Analytics'),
            primary_action: function (values) {
                frm.trigger('load_analytics_data', [dialog, values]);
            },
            size: 'extra-large'
        });

        dialog.show();
    },

    load_analytics_data: function (frm, dialog, values) {
        frappe.call({
            method: 'universal_workshop.communication_management.doctype.communication_history.communication_history.get_communication_analytics',
            args: {
                date_from: values.date_from,
                date_to: values.date_to
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frm.trigger('display_analytics', [dialog, r.message.analytics]);
                }
            }
        });
    },

    display_analytics: function (frm, dialog, analytics) {
        let html = '<div class="analytics-dashboard">';

        // Summary cards
        html += '<div class="row">';
        html += `
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <h5>${analytics.total_communications}</h5>
                        <p>${__('Total Communications')}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h5>${analytics.success_rate}%</h5>
                        <p>${__('Success Rate')}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h5>${analytics.total_cost_omr} OMR</h5>
                        <p>${__('Total Cost')}</p>
                    </div>
                </div>
            </div>
        </div>
        `;

        // Channel breakdown
        html += '<h6>' + __('Channel Breakdown') + '</h6>';
        html += '<table class="table table-striped">';
        html += '<thead><tr><th>' + __('Channel') + '</th><th>' + __('Count') + '</th><th>' + __('Avg Delivery Time') + '</th></tr></thead>';
        html += '<tbody>';

        analytics.channel_breakdown.forEach(function (channel) {
            const avg_time = channel.avg_delivery_time ?
                Math.round(channel.avg_delivery_time) + ' sec' : 'N/A';
            html += `<tr><td>${channel.communication_channel}</td><td>${channel.count}</td><td>${avg_time}</td></tr>`;
        });

        html += '</tbody></table>';

        // Top customers
        if (analytics.top_customers && analytics.top_customers.length > 0) {
            html += '<h6>' + __('Top Customers') + '</h6>';
            html += '<table class="table table-striped">';
            html += '<thead><tr><th>' + __('Customer') + '</th><th>' + __('Communications') + '</th></tr></thead>';
            html += '<tbody>';

            analytics.top_customers.forEach(function (customer) {
                html += `<tr><td>${customer.customer_name}</td><td>${customer.communication_count}</td></tr>`;
            });

            html += '</tbody></table>';
        }

        html += '</div>';

        dialog.fields_dict.analytics_html.$wrapper.html(html);
    },

    show_template_preview: function (frm, template_doc) {
        let preview_html = '<div class="template-preview">';
        preview_html += '<h6>' + __('Template Preview') + '</h6>';
        preview_html += '<p><strong>' + __('Template') + ':</strong> ' + template_doc.template_name + '</p>';
        preview_html += '<p><strong>' + __('Channel') + ':</strong> ' + template_doc.channel + '</p>';

        if (template_doc.template_content) {
            preview_html += '<div class="template-content">';
            preview_html += '<strong>' + __('Content') + ':</strong><br>';
            preview_html += template_doc.template_content.replace(/\n/g, '<br>');
            preview_html += '</div>';
        }

        if (template_doc.template_content_ar) {
            preview_html += '<div class="template-content-ar" dir="rtl">';
            preview_html += '<strong>' + __('Arabic Content') + ':</strong><br>';
            preview_html += template_doc.template_content_ar.replace(/\n/g, '<br>');
            preview_html += '</div>';
        }

        preview_html += '</div>';

        frm.dashboard.add_comment(preview_html, 'green', true);
    },

    retry_delivery: function (frm) {
        frappe.confirm(
            __('Retry delivery for this communication?'),
            function () {
                frappe.call({
                    method: 'universal_workshop.communication_management.queue.queue_api.retry_failed_message',
                    args: {
                        communication_id: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Message queued for retry'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to queue message for retry'));
                        }
                    }
                });
            }
        );
    }
});

// Real-time delivery status updates
if (frappe.realtime) {
    frappe.realtime.on('communication_status_update', function (data) {
        if (cur_frm && cur_frm.doctype === 'Communication History' &&
            cur_frm.doc.name === data.communication_id) {

            // Update form fields
            cur_frm.set_value('delivery_status', data.status);
            cur_frm.set_value('communication_status', data.status);

            if (data.delivered_datetime) {
                cur_frm.set_value('delivered_datetime', data.delivered_datetime);
            }

            if (data.read_datetime) {
                cur_frm.set_value('read_datetime', data.read_datetime);
            }

            if (data.error_message) {
                cur_frm.set_value('error_message', data.error_message);
            }

            // Refresh timeline
            cur_frm.trigger('render_delivery_timeline');

            // Show notification
            frappe.show_alert({
                message: __('Delivery status updated to {0}', [data.status]),
                indicator: data.status === 'Delivered' ? 'green' :
                    data.status === 'Failed' ? 'red' : 'blue'
            });
        }
    });
}

// Auto-refresh for pending deliveries
setInterval(function () {
    if (cur_frm && cur_frm.doctype === 'Communication History' &&
        cur_frm.doc.delivery_status === 'Pending' && cur_frm.doc.sent_datetime) {

        const sent_time = moment(cur_frm.doc.sent_datetime);
        const now = moment();
        const minutes_since_sent = now.diff(sent_time, 'minutes');

        // Auto-refresh if message was sent more than 5 minutes ago
        if (minutes_since_sent > 5) {
            cur_frm.reload_doc();
        }
    }
}, 30000); // Check every 30 seconds 