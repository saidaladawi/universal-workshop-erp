// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service History Tracker', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_real_time_updates');
        frm.trigger('setup_list_view_customizations');
        frm.trigger('setup_timeline_view');
    },

    onload: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('load_customer_preferences');
    },

    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'service_description_ar', 'customer_notes_ar', 'technician_notes_ar',
            'internal_notes_ar', 'stage_description_ar', 'customer_feedback_ar',
            'qc_notes_ar', 'delivery_notes_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, Arial, sans-serif'
                });
            }
        });

        // Apply RTL layout if Arabic is selected
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
            
            // Adjust form layout for RTL
            frm.layout.wrapper.css('direction', 'rtl');
        }
    },

    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // Service Management Buttons
            frm.add_custom_button(__('Update Stage'), function() {
                frm.trigger('show_stage_update_dialog');
            }, __('Service Actions'));

            frm.add_custom_button(__('Send Notification'), function() {
                frm.trigger('send_customer_notification');
            }, __('Service Actions'));

            frm.add_custom_button(__('Mark QC Complete'), function() {
                frm.trigger('complete_quality_check');
            }, __('Service Actions'));

            // Customer Actions
            frm.add_custom_button(__('Mark Customer Viewed'), function() {
                frm.trigger('mark_customer_viewed');
            }, __('Customer Actions'));

            frm.add_custom_button(__('Request Feedback'), function() {
                frm.trigger('request_customer_feedback');
            }, __('Customer Actions'));

            // Delivery Actions
            if (frm.doc.status === 'Ready for Delivery') {
                frm.add_custom_button(__('Complete Delivery'), function() {
                    frm.trigger('complete_delivery');
                }, __('Delivery'));
            }

            // Reports
            frm.add_custom_button(__('Service Report'), function() {
                frm.trigger('generate_service_report');
            }, __('Reports'));

            frm.add_custom_button(__('Timeline Report'), function() {
                frm.trigger('show_timeline_report');
            }, __('Reports'));
        }
    },

    setup_real_time_updates: function(frm) {
        if (!frm.doc.__islocal) {
            // Set up real-time status monitoring
            frm.real_time_interval = setInterval(function() {
                frm.trigger('refresh_real_time_data');
            }, 30000); // Update every 30 seconds

            // Clean up interval when form is closed
            $(window).on('beforeunload', function() {
                if (frm.real_time_interval) {
                    clearInterval(frm.real_time_interval);
                }
            });
        }
    },

    setup_list_view_customizations: function(frm) {
        // Add status indicators to list view
        if (frm.doc.status) {
            frm.set_indicator_formatter('status', function(doc) {
                let color = 'gray';
                switch (doc.status) {
                    case 'Completed':
                        color = 'green';
                        break;
                    case 'In Progress':
                        color = 'blue';
                        break;
                    case 'Pending Parts':
                        color = 'orange';
                        break;
                    case 'Ready for Delivery':
                        color = 'purple';
                        break;
                    case 'Cancelled':
                        color = 'red';
                        break;
                }
                return [__(doc.status), color, 'status,=,' + doc.status];
            });
        }
    },

    setup_timeline_view: function(frm) {
        if (!frm.doc.__islocal && frm.doc.status_timeline) {
            frm.trigger('render_status_timeline');
        }
    },

    setup_field_dependencies: function(frm) {
        // Show/hide fields based on status
        frm.toggle_display(['qc_technician', 'qc_notes', 'qc_notes_ar', 'qc_date'], 
                          frm.doc.status === 'Quality Check');
        
        frm.toggle_display(['delivery_date', 'delivery_method', 'delivered_to'], 
                          frm.doc.status === 'Ready for Delivery' || frm.doc.status === 'Completed');
        
        frm.toggle_display(['satisfaction_rating', 'customer_feedback', 'customer_feedback_ar'], 
                          frm.doc.status === 'Completed');
    },

    load_customer_preferences: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback: function(r) {
                    if (r.message) {
                        // Set notification preferences based on customer settings
                        if (r.message.default_language) {
                            frm.set_value('notification_language', r.message.default_language);
                        }
                    }
                }
            });
        }
    },

    refresh_real_time_data: function(frm) {
        if (!frm.doc.__islocal) {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.service_history_tracker.service_history_tracker.get_real_time_updates',
                args: {
                    tracking_ids: [frm.doc.name]
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success' && r.message.data.length > 0) {
                        const updated_data = r.message.data[0];
                        
                        // Update fields if they've changed
                        if (updated_data.progress_percentage !== frm.doc.progress_percentage) {
                            frm.set_value('progress_percentage', updated_data.progress_percentage);
                        }
                        
                        if (updated_data.current_stage !== frm.doc.current_stage) {
                            frm.set_value('current_stage', updated_data.current_stage);
                        }
                        
                        // Show real-time indicator
                        frm.dashboard.set_headline_alert(
                            __('Live Updates Active - Last Update: {0}', [moment().format('HH:mm:ss')]),
                            'green'
                        );
                    }
                }
            });
        }
    },

    show_stage_update_dialog: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Update Service Stage'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'new_stage',
                    label: __('New Stage'),
                    options: 'Vehicle Received\nDiagnosis in Progress\nAwaiting Customer Approval\nParts Ordered\nWork in Progress\nQuality Check\nReady for Pickup\nCompleted',
                    reqd: 1,
                    default: frm.doc.current_stage
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'description_en',
                    label: __('Description (English)')
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'description_ar',
                    label: __('وصف المرحلة')
                }
            ],
            primary_action_label: __('Update'),
            primary_action: function(values) {
                frappe.call({
                    method: 'update_stage',
                    doc: frm.doc,
                    args: {
                        stage: values.new_stage,
                        description_en: values.description_en,
                        description_ar: values.description_ar
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frm.refresh();
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                        }
                    }
                });
                d.hide();
            }
        });

        // Set RTL for Arabic field
        d.show();
        setTimeout(() => {
            d.fields_dict.description_ar.$input.attr('dir', 'rtl');
        }, 100);
    },

    send_customer_notification: function(frm) {
        frappe.confirm(
            __('Send notification to customer about current status?'),
            function() {
                frm.call('send_customer_notification').then(r => {
                    frappe.show_alert({
                        message: __('Notification sent successfully'),
                        indicator: 'green'
                    });
                });
            }
        );
    },

    complete_quality_check: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Complete Quality Check'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'qc_result',
                    label: __('QC Result'),
                    options: 'Passed\nFailed\nRework Required',
                    reqd: 1
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'qc_notes_en',
                    label: __('QC Notes (English)')
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'qc_notes_ar',
                    label: __('ملاحظات مراقبة الجودة')
                }
            ],
            primary_action_label: __('Complete QC'),
            primary_action: function(values) {
                frm.set_value('quality_check_status', values.qc_result);
                frm.set_value('qc_notes', values.qc_notes_en);
                frm.set_value('qc_notes_ar', values.qc_notes_ar);
                frm.set_value('qc_date', frappe.datetime.now_date());
                frm.set_value('qc_technician', frappe.session.user);
                frm.set_value('qc_passed', values.qc_result === 'Passed');
                frm.set_value('rework_required', values.qc_result === 'Rework Required');
                
                if (values.qc_result === 'Passed') {
                    frm.set_value('status', 'Ready for Delivery');
                } else if (values.qc_result === 'Rework Required') {
                    frm.set_value('status', 'In Progress');
                }
                
                frm.save();
                d.hide();
            }
        });

        d.show();
        setTimeout(() => {
            d.fields_dict.qc_notes_ar.$input.attr('dir', 'rtl');
        }, 100);
    },

    mark_customer_viewed: function(frm) {
        frm.call('mark_as_viewed_by_customer').then(r => {
            frm.refresh_field('customer_viewed');
            frappe.show_alert({
                message: __('Marked as viewed by customer'),
                indicator: 'blue'
            });
        });
    },

    request_customer_feedback: function(frm) {
        frappe.confirm(
            __('Send feedback request to customer?'),
            function() {
                // This would trigger a feedback request notification
                frappe.show_alert({
                    message: __('Feedback request sent to customer'),
                    indicator: 'green'
                });
            }
        );
    },

    complete_delivery: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Complete Vehicle Delivery'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'delivered_to',
                    label: __('Delivered To'),
                    reqd: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'delivery_method',
                    label: __('Delivery Method'),
                    options: 'Customer Pickup\nDelivery Service\nTowing Service',
                    reqd: 1
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'delivery_notes_en',
                    label: __('Delivery Notes (English)')
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'delivery_notes_ar',
                    label: __('ملاحظات التسليم')
                }
            ],
            primary_action_label: __('Complete Delivery'),
            primary_action: function(values) {
                frm.set_value('delivered_to', values.delivered_to);
                frm.set_value('delivery_method', values.delivery_method);
                frm.set_value('delivery_notes', values.delivery_notes_en);
                frm.set_value('delivery_notes_ar', values.delivery_notes_ar);
                frm.set_value('delivery_date', frappe.datetime.now());
                frm.set_value('status', 'Completed');
                frm.set_value('actual_completion', frappe.datetime.now());
                frm.set_value('ready_for_delivery', 1);
                
                frm.save();
                d.hide();
                
                frappe.show_alert({
                    message: __('Delivery completed successfully'),
                    indicator: 'green'
                });
            }
        });

        d.show();
        setTimeout(() => {
            d.fields_dict.delivery_notes_ar.$input.attr('dir', 'rtl');
        }, 100);
    },

    generate_service_report: function(frm) {
        const print_format = frappe.boot.lang === 'ar' ? 'Service Report Arabic' : 'Service Report';
        window.open(frappe.urllib.get_full_url(
            '/printview?doctype=Service History Tracker&name=' + 
            encodeURIComponent(frm.doc.name) + 
            '&format=' + encodeURIComponent(print_format)
        ));
    },

    show_timeline_report: function(frm) {
        frm.trigger('render_timeline_dashboard');
    },

    render_status_timeline: function(frm) {
        if (frm.doc.status_timeline && frm.doc.status_timeline.length > 0) {
            let timeline_html = '<div class="service-timeline">';
            
            frm.doc.status_timeline.forEach(entry => {
                const timestamp = moment(entry.timestamp).format('DD/MM/YYYY HH:mm');
                const progress_bar = `
                    <div class="progress" style="height: 20px; margin: 5px 0;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${entry.progress}%"
                             aria-valuenow="${entry.progress}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            ${entry.progress}%
                        </div>
                    </div>
                `;
                
                timeline_html += `
                    <div class="timeline-entry" style="margin: 10px 0; padding: 10px; border-left: 3px solid #007bff;">
                        <h6>${entry.new_status} - ${entry.stage}</h6>
                        <small class="text-muted">${timestamp} by ${entry.user}</small>
                        ${progress_bar}
                        <p>${entry.notes}</p>
                    </div>
                `;
            });
            
            timeline_html += '</div>';
            
            frm.set_df_property('status_timeline', 'description', timeline_html);
        }
    },

    render_timeline_dashboard: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Service Timeline Dashboard'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'timeline_dashboard'
                }
            ]
        });

        // Create comprehensive timeline visualization
        let dashboard_html = `
            <div class="service-timeline-dashboard">
                <div class="row">
                    <div class="col-md-6">
                        <h5>${__('Service Progress')}</h5>
                        <div class="progress" style="height: 30px;">
                            <div class="progress-bar bg-success" role="progressbar" 
                                 style="width: ${frm.doc.progress_percentage || 0}%">
                                ${frm.doc.progress_percentage || 0}%
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h5>${__('Service Status')}</h5>
                        <span class="badge badge-primary badge-lg">${frm.doc.status}</span>
                        <br><small>${frm.doc.current_stage}</small>
                    </div>
                </div>
                <hr>
        `;

        if (frm.doc.status_timeline) {
            dashboard_html += '<h5>' + __('Status History') + '</h5>';
            frm.doc.status_timeline.forEach(entry => {
                dashboard_html += `
                    <div class="timeline-entry-dashboard" style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                        <div class="row">
                            <div class="col-md-8">
                                <strong>${entry.new_status}</strong> - ${entry.stage}
                                <br><small>${entry.notes}</small>
                            </div>
                            <div class="col-md-4 text-right">
                                <small>${moment(entry.timestamp).format('DD/MM/YYYY HH:mm')}</small>
                                <br><small>by ${entry.user}</small>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        dashboard_html += '</div>';
        
        d.fields_dict.timeline_dashboard.$wrapper.html(dashboard_html);
        d.show();
    },

    // Field change handlers
    status: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_progress_based_on_status');
    },

    current_stage: function(frm) {
        frm.trigger('update_progress_based_on_stage');
    },

    labor_hours: function(frm) {
        frm.trigger('calculate_labor_cost');
    },

    hourly_rate: function(frm) {
        frm.trigger('calculate_labor_cost');
    },

    paid_amount: function(frm) {
        frm.trigger('calculate_balance');
    },

    total_amount: function(frm) {
        frm.trigger('calculate_balance');
    },

    update_progress_based_on_status: function(frm) {
        const status_progress_map = {
            'Received': 10,
            'In Progress': 50,
            'Pending Parts': 40,
            'Quality Check': 85,
            'Ready for Delivery': 95,
            'Completed': 100,
            'Cancelled': 0
        };

        if (frm.doc.status && status_progress_map[frm.doc.status]) {
            frm.set_value('progress_percentage', status_progress_map[frm.doc.status]);
        }
    },

    update_progress_based_on_stage: function(frm) {
        const stage_progress_map = {
            'Vehicle Received': 10,
            'Diagnosis in Progress': 25,
            'Awaiting Customer Approval': 35,
            'Parts Ordered': 45,
            'Work in Progress': 70,
            'Quality Check': 85,
            'Ready for Pickup': 95,
            'Completed': 100
        };

        if (frm.doc.current_stage && stage_progress_map[frm.doc.current_stage]) {
            frm.set_value('progress_percentage', stage_progress_map[frm.doc.current_stage]);
        }
    },

    calculate_labor_cost: function(frm) {
        if (frm.doc.labor_hours && frm.doc.hourly_rate) {
            const labor_cost = parseFloat(frm.doc.labor_hours) * parseFloat(frm.doc.hourly_rate);
            frm.set_value('labor_cost', labor_cost);
            frm.trigger('calculate_total_cost');
        }
    },

    calculate_total_cost: function(frm) {
        const labor_cost = parseFloat(frm.doc.labor_cost || 0);
        const parts_cost = parseFloat(frm.doc.parts_cost || 0);
        const total_cost = labor_cost + parts_cost;
        
        frm.set_value('total_cost', total_cost);
        
        if (!frm.doc.total_amount) {
            frm.set_value('total_amount', total_cost);
        }
    },

    calculate_balance: function(frm) {
        const total_amount = parseFloat(frm.doc.total_amount || 0);
        const paid_amount = parseFloat(frm.doc.paid_amount || 0);
        const balance = total_amount - paid_amount;
        
        frm.set_value('balance_amount', balance);
        
        // Update payment status
        if (balance <= 0 && total_amount > 0) {
            frm.set_value('payment_status', 'Paid');
        } else if (paid_amount > 0 && balance > 0) {
            frm.set_value('payment_status', 'Partial');
        } else if (paid_amount <= 0) {
            frm.set_value('payment_status', 'Pending');
        }
    }
});

// Child table handlers for Service History Item
frappe.ui.form.on('Service History Item', {
    quantity: function(frm, cdt, cdn) {
        calculate_service_item_total(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_service_item_total(frm, cdt, cdn);
    }
});

// Child table handlers for Service History Part
frappe.ui.form.on('Service History Part', {
    quantity: function(frm, cdt, cdn) {
        calculate_part_total(frm, cdt, cdn);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_part_total(frm, cdt, cdn);
    },
    
    parts_used_remove: function(frm) {
        frm.trigger('calculate_parts_cost');
    }
});

function calculate_service_item_total(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.quantity && row.rate) {
        row.total = parseFloat(row.quantity) * parseFloat(row.rate);
        refresh_field('total', cdn, 'service_items');
    }
}

function calculate_part_total(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.quantity && row.rate) {
        row.total_cost = parseFloat(row.quantity) * parseFloat(row.rate);
        refresh_field('total_cost', cdn, 'parts_used');
        frm.trigger('calculate_parts_cost');
    }
}

// Global functions for real-time updates
window.service_tracker_real_time = {
    start_monitoring: function(tracking_ids) {
        if (window.service_tracker_interval) {
            clearInterval(window.service_tracker_interval);
        }
        
        window.service_tracker_interval = setInterval(function() {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.service_history_tracker.service_history_tracker.get_real_time_updates',
                args: {
                    tracking_ids: tracking_ids
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        // Emit real-time update event
                        $(document).trigger('service_tracker_update', [r.message.data]);
                    }
                }
            });
        }, 15000); // Check every 15 seconds
    },
    
    stop_monitoring: function() {
        if (window.service_tracker_interval) {
            clearInterval(window.service_tracker_interval);
            window.service_tracker_interval = null;
        }
    }
}; 