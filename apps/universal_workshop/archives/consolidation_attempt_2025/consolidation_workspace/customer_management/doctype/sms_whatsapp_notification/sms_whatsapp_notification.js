// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('SMS WhatsApp Notification', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_interface');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_realtime_monitoring');
        frm.trigger('setup_template_helpers');
    },
    
    onload: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('load_twilio_config');
        frm.trigger('setup_cost_calculation');
    },
    
    setup_arabic_interface: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'notification_title_ar', 'notification_description_ar', 'customer_name_ar',
            'message_body_ar', 'follow_up_notes_ar', 'compliance_notes_ar',
            'response_content_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': '"Noto Sans Arabic", Tahoma, Arial, sans-serif'
                });
            }
        });
        
        // Setup translation helpers
        frm.trigger('setup_translation_helpers');
    },
    
    setup_translation_helpers: function(frm) {
        // Add Arabic translation suggestion buttons
        if (frm.fields_dict.notification_title_ar) {
            const $title_field = frm.fields_dict.notification_title_ar.$wrapper;
            
            if (!$title_field.find('.arabic-translate-btn').length) {
                const $translate_btn = $('<button class="btn btn-xs btn-default arabic-translate-btn" style="margin-top: 5px;">')
                    .text('ترجمة تلقائية / Auto Translate')
                    .click(() => frm.trigger('auto_translate_arabic'));
                    
                $title_field.append($translate_btn);
            }
        }
        
        // Add template loading buttons
        if (frm.fields_dict.message_body) {
            const $message_field = frm.fields_dict.message_body.$wrapper;
            
            if (!$message_field.find('.template-load-btn').length) {
                const $template_btn = $('<button class="btn btn-xs btn-primary template-load-btn" style="margin-top: 5px;">')
                    .text('📋 Load Template')
                    .click(() => frm.trigger('show_template_selector'));
                    
                $message_field.append($template_btn);
            }
        }
    },
    
    auto_translate_arabic: function(frm) {
        if (!frm.doc.notification_title) {
            frappe.msgprint(__('Please enter English title first'));
            return;
        }
        
        // Simple auto-translation based on notification type
        const translations = {
            'Appointment Reminder': 'تذكير بالموعد',
            'Service Update': 'تحديث الخدمة',
            'Payment Confirmation': 'تأكيد الدفع',
            'Payment Reminder': 'تذكير بالدفع',
            'Feedback Request': 'طلب تقييم',
            'Promotion': 'عرض ترويجي',
            'Emergency Alert': 'تنبيه طارئ',
            'General Information': 'معلومات عامة'
        };
        
        const arabic_title = translations[frm.doc.notification_type] || 'إشعار من الورشة';
        frm.set_value('notification_title_ar', arabic_title);
        
        // Auto-translate message body based on type
        if (frm.doc.notification_type && !frm.doc.message_body_ar) {
            frm.trigger('load_arabic_template');
        }
        
        frappe.show_alert({
            message: __('Arabic translation applied'),
            indicator: 'green'
        });
    },
    
    load_arabic_template: function(frm) {
        if (!frm.doc.notification_type) return;
        
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.get_notification_templates',
            args: {
                notification_type: frm.doc.notification_type,
                language: 'ar'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('message_body_ar', r.message);
                }
            }
        });
    },
    
    show_template_selector: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Select Message Template'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'template_type',
                    label: __('Template Type'),
                    options: [
                        'Appointment Reminder',
                        'Service Update',
                        'Payment Confirmation',
                        'Payment Reminder',
                        'Feedback Request',
                        'Promotion',
                        'Emergency Alert',
                        'General Information'
                    ],
                    reqd: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'language',
                    label: __('Language'),
                    options: ['English', 'Arabic', 'Both'],
                    default: 'Both',
                    reqd: 1
                }
            ],
            primary_action_label: __('Load Template'),
            primary_action: function(values) {
                frm.trigger('load_selected_template', values);
                dialog.hide();
            }
        });
        
        dialog.show();
    },
    
    load_selected_template: function(frm, values) {
        frm.set_value('notification_type', values.template_type);
        
        // Load English template
        if (['English', 'Both'].includes(values.language)) {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.get_notification_templates',
                args: {
                    notification_type: values.template_type,
                    language: 'en'
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('message_body', r.message);
                    }
                }
            });
        }
        
        // Load Arabic template
        if (['Arabic', 'Both'].includes(values.language)) {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.get_notification_templates',
                args: {
                    notification_type: values.template_type,
                    language: 'ar'
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('message_body_ar', r.message);
                    }
                }
            });
        }
        
        frappe.show_alert({
            message: __('Template loaded successfully'),
            indicator: 'green'
        });
    },
    
    setup_custom_buttons: function(frm) {
        // Status-specific buttons
        if (frm.doc.status === 'Draft') {
            frm.add_custom_button(__('Send Now'), function() {
                frm.trigger('send_notification_now');
            }).addClass('btn-primary');
            
            frm.add_custom_button(__('Preview Message'), function() {
                frm.trigger('preview_message');
            }).addClass('btn-info');
            
            frm.add_custom_button(__('Test Send'), function() {
                frm.trigger('test_send');
            }).addClass('btn-default');
        }
        
        if (['Sent', 'Delivered'].includes(frm.doc.status)) {
            frm.add_custom_button(__('View Analytics'), function() {
                frm.trigger('show_analytics');
            }).addClass('btn-info');
            
            frm.add_custom_button(__('Resend'), function() {
                frm.trigger('resend_notification');
            }).addClass('btn-warning');
        }
        
        if (frm.doc.status === 'Failed') {
            frm.add_custom_button(__('Retry'), function() {
                frm.trigger('retry_notification');
            }).addClass('btn-primary');
        }
        
        // Utility buttons
        frm.add_custom_button(__('Check Status'), function() {
            frm.trigger('check_delivery_status');
        }).addClass('btn-default');
        
        if (frm.doc.customer) {
            frm.add_custom_button(__('Customer History'), function() {
                frm.trigger('show_customer_notification_history');
            }).addClass('btn-default');
        }
        
        // Add status indicators
        frm.trigger('add_status_indicators');
    },
    
    add_status_indicators: function(frm) {
        // Clear existing indicators
        frm.dashboard.clear_indicator();
        
        // Status indicator
        const status_colors = {
            'Draft': 'orange',
            'Scheduled': 'blue',
            'Sending': 'yellow',
            'Sent': 'green',
            'Delivered': 'green',
            'Read': 'green',
            'Failed': 'red',
            'Cancelled': 'gray'
        };
        
        frm.dashboard.add_indicator(
            __('Status: {0}', [frm.doc.status]),
            status_colors[frm.doc.status] || 'gray'
        );
        
        // Delivery status indicator
        if (frm.doc.delivery_status && frm.doc.delivery_status !== frm.doc.status) {
            frm.dashboard.add_indicator(
                __('Delivery: {0}', [frm.doc.delivery_status]),
                status_colors[frm.doc.delivery_status] || 'gray'
            );
        }
        
        // Cost indicator
        if (frm.doc.actual_cost) {
            frm.dashboard.add_indicator(
                __('Cost: {0} OMR', [frm.doc.actual_cost]),
                'blue'
            );
        }
        
        // Priority indicator
        if (frm.doc.priority_level === 'Urgent' || frm.doc.priority_level === 'Critical') {
            frm.dashboard.add_indicator(
                __('Priority: {0}', [frm.doc.priority_level]),
                'red'
            );
        }
    },
    
    send_notification_now: function(frm) {
        frappe.confirm(
            __('Are you sure you want to send this notification immediately?'),
            () => {
                frm.set_value('send_immediately', 1);
                frm.save().then(() => {
                    frappe.show_alert({
                        message: __('Notification sent successfully'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                });
            }
        );
    },
    
    preview_message: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Message Preview'),
            size: 'large'
        });
        
        const preview_html = `
            <div class="message-preview" style="padding: 20px;">
                <div class="row">
                    <div class="col-md-6">
                        <h5>English Message:</h5>
                        <div class="message-content" style="
                            background: #f8f9fa; 
                            padding: 15px; 
                            border-radius: 5px; 
                            border-left: 4px solid #007bff;
                            margin-bottom: 20px;
                        ">
                            ${frm.doc.message_body || 'No English message'}
                        </div>
                        
                        <div class="message-info">
                            <p><strong>Characters:</strong> ${(frm.doc.message_body || '').length}</p>
                            <p><strong>Channel:</strong> ${frm.doc.channel_type}</p>
                            <p><strong>Recipient:</strong> ${frm.doc.customer_name || frm.doc.phone_number}</p>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <h5>Arabic Message | الرسالة العربية:</h5>
                        <div class="message-content arabic-message" style="
                            background: #f8f9fa; 
                            padding: 15px; 
                            border-radius: 5px; 
                            border-right: 4px solid #28a745;
                            margin-bottom: 20px;
                            direction: rtl;
                            text-align: right;
                            font-family: 'Noto Sans Arabic', Tahoma, Arial, sans-serif;
                        ">
                            ${frm.doc.message_body_ar || 'لا توجد رسالة عربية'}
                        </div>
                        
                        <div class="message-info arabic-info" style="direction: rtl; text-align: right;">
                            <p><strong>الأحرف:</strong> ${(frm.doc.message_body_ar || '').length}</p>
                            <p><strong>القناة:</strong> ${frm.doc.channel_type}</p>
                            <p><strong>المستقبل:</strong> ${frm.doc.customer_name_ar || frm.doc.whatsapp_number}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        dialog.$body.html(preview_html);
        dialog.show();
    },
    
    test_send: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Test Send Notification'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'test_phone',
                    label: __('Test Phone Number (+968)'),
                    reqd: 1,
                    description: __('Enter a test phone number to send the notification')
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'send_sms',
                    label: __('Send SMS'),
                    default: 1
                },
                {
                    fieldtype: 'Check',
                    fieldname: 'send_whatsapp',
                    label: __('Send WhatsApp'),
                    default: 1
                }
            ],
            primary_action_label: __('Send Test'),
            primary_action: function(values) {
                frm.trigger('execute_test_send', values);
                dialog.hide();
            }
        });
        
        dialog.show();
    },
    
    execute_test_send: function(frm, values) {
        frappe.call({
            method: 'universal_workshop.api.test_notification_send',
            args: {
                notification_id: frm.doc.name,
                test_phone: values.test_phone,
                send_sms: values.send_sms,
                send_whatsapp: values.send_whatsapp
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('Test notification sent successfully'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint(__('Test send failed: {0}', [r.message.error || 'Unknown error']));
                }
            }
        });
    },
    
    show_analytics: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.get_notification_analytics',
            args: {
                date_range: '30'
            },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    frm.trigger('display_analytics', r.message);
                } else {
                    frappe.msgprint(__('Failed to load analytics data'));
                }
            }
        });
    },
    
    display_analytics: function(frm, analytics) {
        const dialog = new frappe.ui.Dialog({
            title: __('Notification Analytics (Last 30 Days)'),
            size: 'extra-large'
        });
        
        const analytics_html = `
            <div class="notification-analytics" style="padding: 20px;">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>Summary | الملخص</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Total Notifications:</strong> ${analytics.summary.total_notifications}</p>
                                <p><strong>Sent:</strong> ${analytics.summary.sent_notifications}</p>
                                <p><strong>Delivered:</strong> ${analytics.summary.delivered_notifications}</p>
                                <p><strong>Delivery Rate:</strong> ${analytics.summary.delivery_rate}%</p>
                                <p><strong>Total Cost:</strong> ${analytics.summary.total_cost} OMR</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>Channel Breakdown | توزيع القنوات</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>SMS:</strong> ${analytics.channel_breakdown.sms}</p>
                                <p><strong>WhatsApp:</strong> ${analytics.channel_breakdown.whatsapp}</p>
                                <div class="progress" style="margin-top: 10px;">
                                    <div class="progress-bar bg-info" style="width: ${analytics.channel_breakdown.sms / (analytics.channel_breakdown.sms + analytics.channel_breakdown.whatsapp) * 100}%">
                                        SMS ${Math.round(analytics.channel_breakdown.sms / (analytics.channel_breakdown.sms + analytics.channel_breakdown.whatsapp) * 100)}%
                                    </div>
                                    <div class="progress-bar bg-success" style="width: ${analytics.channel_breakdown.whatsapp / (analytics.channel_breakdown.sms + analytics.channel_breakdown.whatsapp) * 100}%">
                                        WhatsApp ${Math.round(analytics.channel_breakdown.whatsapp / (analytics.channel_breakdown.sms + analytics.channel_breakdown.whatsapp) * 100)}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>Type Breakdown | توزيع الأنواع</h5>
                            </div>
                            <div class="card-body">
                                ${Object.keys(analytics.type_breakdown).map(type => 
                                    `<p><strong>${type}:</strong> ${analytics.type_breakdown[type]}</p>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row" style="margin-top: 20px;">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>Recent Notifications | الإشعارات الحديثة</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Type</th>
                                            <th>Channel</th>
                                            <th>Status</th>
                                            <th>Cost (OMR)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${analytics.recent_notifications.map(notification => `
                                            <tr>
                                                <td>${notification.created_date}</td>
                                                <td>${notification.notification_type}</td>
                                                <td>${notification.channel_type}</td>
                                                <td><span class="badge badge-info">${notification.status}</span></td>
                                                <td>${notification.actual_cost || 0}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        dialog.$body.html(analytics_html);
        dialog.show();
    },
    
    setup_realtime_monitoring: function(frm) {
        // Real-time status monitoring for sent notifications
        if (['Sent', 'Delivered'].includes(frm.doc.status)) {
            setInterval(() => {
                frm.trigger('check_delivery_status');
            }, 30000); // Check every 30 seconds
        }
        
        // Auto-save draft every 60 seconds
        if (frm.doc.status === 'Draft') {
            setInterval(() => {
                if (frm.is_dirty() && !frm.is_new()) {
                    frm.save();
                }
            }, 60000);
        }
        
        // Update character count in real-time
        frm.trigger('setup_character_counter');
    },
    
    setup_character_counter: function(frm) {
        // Real-time character counting for message fields
        ['message_body', 'message_body_ar'].forEach(fieldname => {
            if (frm.fields_dict[fieldname]) {
                frm.fields_dict[fieldname].$input.on('input', function() {
                    const text = $(this).val();
                    const count = text.length;
                    const is_arabic = fieldname.includes('_ar');
                    
                    // Create or update character counter
                    let $counter = $(this).siblings('.char-counter');
                    if (!$counter.length) {
                        $counter = $('<div class="char-counter" style="font-size: 11px; color: #666; margin-top: 3px;"></div>');
                        $(this).after($counter);
                    }
                    
                    // SMS limits: 160 for English, 70 for Arabic
                    const limit = is_arabic ? 70 : 160;
                    const color = count > limit ? 'red' : (count > limit * 0.8 ? 'orange' : 'green');
                    
                    $counter.html(`
                        <span style="color: ${color};">
                            ${count} characters ${is_arabic ? '| حرف' : ''}
                            ${frm.doc.channel_type === 'SMS' ? `(SMS limit: ${limit})` : ''}
                        </span>
                    `);
                });
            }
        });
    },
    
    check_delivery_status: function(frm) {
        if (frm.doc.twilio_message_sid) {
            frappe.call({
                method: 'universal_workshop.api.check_twilio_message_status',
                args: {
                    message_sid: frm.doc.twilio_message_sid
                },
                callback: function(r) {
                    if (r.message && r.message.status !== frm.doc.delivery_status) {
                        frm.reload_doc();
                    }
                }
            });
        }
    },
    
    setup_field_dependencies: function(frm) {
        // Show/hide fields based on channel type
        frm.toggle_display('phone_number', ['SMS', 'Both'].includes(frm.doc.channel_type));
        frm.toggle_display('whatsapp_number', ['WhatsApp', 'Both'].includes(frm.doc.channel_type));
        
        // Show/hide scheduling fields
        frm.toggle_display('scheduled_datetime', !frm.doc.send_immediately);
        frm.toggle_display(['delivery_window_start', 'delivery_window_end'], !frm.doc.send_immediately);
        
        // Show/hide recurring fields
        frm.toggle_display('recurrence_pattern', frm.doc.recurring_notification);
        
        // Show/hide delivery tracking fields based on status
        frm.toggle_display(['sent_datetime', 'delivered_datetime'], frm.doc.status !== 'Draft');
        frm.toggle_display('error_message', frm.doc.status === 'Failed');
        
        // Required fields based on recipient type
        frm.toggle_reqd('customer', frm.doc.recipient_type === 'Individual');
    },
    
    load_twilio_config: function(frm) {
        // Load Twilio configuration from Universal Workshop Settings
        frappe.db.get_single_value('Universal Workshop Settings', 'twilio_account_sid')
            .then(sid => {
                if (sid) {
                    frm.set_value('twilio_account_sid', sid);
                }
            });
    },
    
    setup_cost_calculation: function(frm) {
        // Auto-calculate estimated costs
        frm.trigger('calculate_estimated_cost');
    },
    
    calculate_estimated_cost: function(frm) {
        let total_cost = 0;
        
        // SMS cost calculation
        if (['SMS', 'Both'].includes(frm.doc.channel_type)) {
            const sms_cost = 0.0029; // Approximate OMR cost per SMS
            total_cost += sms_cost;
        }
        
        // WhatsApp cost calculation
        if (['WhatsApp', 'Both'].includes(frm.doc.channel_type)) {
            const whatsapp_cost = 0.0016; // Approximate OMR cost per WhatsApp
            total_cost += whatsapp_cost;
        }
        
        // Update recipient count for group notifications
        if (frm.doc.recipient_type === 'Group' && frm.doc.total_recipients) {
            total_cost *= frm.doc.total_recipients;
        }
        
        frm.set_value('estimated_cost', total_cost);
    },
    
    // Field change handlers
    notification_type: function(frm) {
        frm.trigger('auto_translate_arabic');
        frm.trigger('load_arabic_template');
    },
    
    channel_type: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('calculate_estimated_cost');
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value('Customer', frm.doc.customer, ['customer_name', 'mobile_no', 'email_id'])
                .then(r => {
                    if (r.message) {
                        frm.set_value('customer_name', r.message.customer_name);
                        if (!frm.doc.phone_number && r.message.mobile_no) {
                            frm.set_value('phone_number', r.message.mobile_no);
                        }
                        if (!frm.doc.whatsapp_number && r.message.mobile_no) {
                            frm.set_value('whatsapp_number', r.message.mobile_no);
                        }
                        if (!frm.doc.email_address && r.message.email_id) {
                            frm.set_value('email_address', r.message.email_id);
                        }
                    }
                });
        }
    },
    
    send_immediately: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    recurring_notification: function(frm) {
        frm.trigger('setup_field_dependencies');
    },
    
    recipient_type: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('calculate_estimated_cost');
    },
    
    total_recipients: function(frm) {
        frm.trigger('calculate_estimated_cost');
    },
    
    message_body: function(frm) {
        // Auto-calculate character count
        if (frm.doc.message_body) {
            frm.set_value('character_count', frm.doc.message_body.length);
        }
    }
});

// List view customizations
frappe.listview_settings['SMS WhatsApp Notification'] = {
    get_indicator: function(doc) {
        const status_colors = {
            'Draft': 'orange',
            'Scheduled': 'blue',
            'Sending': 'yellow',
            'Sent': 'green',
            'Delivered': 'green',
            'Read': 'green',
            'Failed': 'red',
            'Cancelled': 'gray'
        };
        
        return [doc.status, status_colors[doc.status] || 'gray', 'status,=,' + doc.status];
    },
    
    onload: function(listview) {
        // Add custom filters for quick access
        listview.page.add_menu_item(__('Failed Notifications'), function() {
            listview.filter_area.add([[listview.doctype, 'status', '=', 'Failed']]);
        });
        
        listview.page.add_menu_item(__('Urgent Priority'), function() {
            listview.filter_area.add([[listview.doctype, 'priority_level', 'in', ['Urgent', 'Critical']]]);
        });
        
        listview.page.add_menu_item(__('Today\'s Notifications'), function() {
            listview.filter_area.add([[listview.doctype, 'created_date', '>=', frappe.datetime.get_today()]]);
        });
        
        listview.page.add_menu_item(__('WhatsApp Only'), function() {
            listview.filter_area.add([[listview.doctype, 'channel_type', '=', 'WhatsApp']]);
        });
        
        // Add bulk actions
        listview.page.add_action_item(__('Send Bulk'), function() {
            frappe.set_route('Form', 'Bulk Notification Sender');
        });
    }
};
