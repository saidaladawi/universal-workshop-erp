/**
 * Workshop Appointment JavaScript Controller
 * Comprehensive appointment management interface with Arabic RTL support
 * Universal Workshop ERP - Customer Portal Module
 */

frappe.ui.form.on('Workshop Appointment', {
    refresh: function (frm) {
        // Setup Arabic interface if language is Arabic
        if (frappe.boot.lang === 'ar' || frm.doc.language_preference === 'Arabic') {
            frm.trigger('setup_arabic_interface');
        }

        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_status_indicators');
        frm.trigger('setup_real_time_updates');
        frm.trigger('setup_field_dependencies');
        frm.trigger('add_custom_styling');
    },

    onload: function (frm) {
        // Set default values for new appointments
        if (frm.doc.__islocal) {
            frm.trigger('set_default_values');
        }

        frm.trigger('setup_field_formatters');
        frm.trigger('setup_validation_helpers');
    },

    // === ARABIC INTERFACE SETUP ===

    setup_arabic_interface: function (frm) {
        // Apply RTL layout
        frm.page.main.addClass('rtl-layout');
        $('html').attr('dir', 'rtl');

        // Arabic-specific fields
        const arabic_fields = [
            'customer_name_ar', 'service_description_ar',
            'special_instructions_ar', 'customer_notes_ar', 'internal_notes_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                });
            }
        });

        // Format time display in Arabic
        if (frm.doc.appointment_time) {
            frm.trigger('format_arabic_time');
        }

        // Format Hijri date if applicable
        if (frm.doc.calendar_type === 'Hijri') {
            frm.trigger('display_hijri_date');
        }
    },

    format_arabic_time: function (frm) {
        if (frm.doc.appointment_time && frappe.boot.lang === 'ar') {
            const time = frm.doc.appointment_time;
            const arabic_time = convert_to_arabic_time(time);

            // Update display
            if (frm.fields_dict.appointment_time) {
                frm.fields_dict.appointment_time.$wrapper.find('.control-value').html(
                    `<span style="direction: rtl;">${arabic_time}</span>`
                );
            }
        }
    },

    display_hijri_date: function (frm) {
        if (frm.doc.hijri_date) {
            frm.add_custom_button(__('Show Hijri Calendar'), function () {
                frappe.msgprint({
                    title: __('Hijri Date'),
                    message: `<div style="text-align: center; font-size: 16px; direction: rtl;">
                        <p><strong>التاريخ الهجري:</strong></p>
                        <p style="font-size: 20px; color: #2e7d32;">${frm.doc.hijri_date}</p>
                    </div>`,
                    primary_action: {
                        'label': __('Close'),
                        'action': function () {
                            cur_dialog.hide();
                        }
                    }
                });
            }, __('Calendar'));
        }
    },

    // === CUSTOM BUTTONS ===

    setup_custom_buttons: function (frm) {
        frm.page.clear_inner_toolbar();

        // Status-specific buttons
        if (!frm.doc.__islocal) {
            if (frm.doc.appointment_status === 'Pending') {
                frm.trigger('add_confirmation_buttons');
            } else if (frm.doc.appointment_status === 'Confirmed') {
                frm.trigger('add_service_buttons');
            } else if (frm.doc.appointment_status === 'In Progress') {
                frm.trigger('add_completion_buttons');
            } else if (frm.doc.appointment_status === 'Completed') {
                frm.trigger('add_followup_buttons');
            }

            // Common buttons
            frm.trigger('add_communication_buttons');
            frm.trigger('add_utility_buttons');
        }

        // New appointment buttons
        if (frm.doc.__islocal) {
            frm.trigger('add_booking_helpers');
        }
    },

    add_confirmation_buttons: function (frm) {
        frm.add_custom_button(__('Confirm Appointment'), function () {
            frm.trigger('confirm_appointment');
        }, __('Actions')).addClass('btn-primary');

        frm.add_custom_button(__('Reschedule'), function () {
            frm.trigger('reschedule_appointment');
        }, __('Actions'));

        frm.add_custom_button(__('Cancel Appointment'), function () {
            frm.trigger('cancel_appointment');
        }, __('Actions')).addClass('btn-danger');
    },

    add_service_buttons: function (frm) {
        frm.add_custom_button(__('Start Service'), function () {
            frm.trigger('start_service');
        }, __('Service')).addClass('btn-success');

        frm.add_custom_button(__('Check In Customer'), function () {
            frm.trigger('check_in_customer');
        }, __('Service'));

        frm.add_custom_button(__('Assign Technician'), function () {
            frm.trigger('assign_technician');
        }, __('Service'));
    },

    add_completion_buttons: function (frm) {
        frm.add_custom_button(__('Complete Service'), function () {
            frm.trigger('complete_service');
        }, __('Service')).addClass('btn-success');

        frm.add_custom_button(__('Update Progress'), function () {
            frm.trigger('update_service_progress');
        }, __('Service'));

        frm.add_custom_button(__('Create Invoice'), function () {
            frm.trigger('create_service_invoice');
        }, __('Billing'));
    },

    add_followup_buttons: function (frm) {
        frm.add_custom_button(__('Send Feedback Request'), function () {
            frm.trigger('send_feedback_request');
        }, __('Follow-up'));

        frm.add_custom_button(__('Schedule Follow-up'), function () {
            frm.trigger('schedule_followup_appointment');
        }, __('Follow-up'));

        if (frm.doc.invoice_reference) {
            frm.add_custom_button(__('View Invoice'), function () {
                frappe.set_route('Form', 'Sales Invoice', frm.doc.invoice_reference);
            }, __('Billing'));
        }
    },

    add_communication_buttons: function (frm) {
        frm.add_custom_button(__('Send SMS'), function () {
            frm.trigger('send_sms_notification');
        }, __('Communication'));

        frm.add_custom_button(__('Send WhatsApp'), function () {
            frm.trigger('send_whatsapp_notification');
        }, __('Communication'));

        frm.add_custom_button(__('Send Email'), function () {
            frm.trigger('send_email_notification');
        }, __('Communication'));

        frm.add_custom_button(__('Communication Log'), function () {
            frm.trigger('show_communication_log');
        }, __('Communication'));
    },

    add_utility_buttons: function (frm) {
        frm.add_custom_button(__('Print Appointment'), function () {
            frm.trigger('print_appointment_slip');
        }, __('Print'));

        frm.add_custom_button(__('View Customer Profile'), function () {
            frappe.set_route('Form', 'Customer', frm.doc.customer);
        }, __('Related'));

        frm.add_custom_button(__('View Vehicle Profile'), function () {
            frappe.set_route('Form', 'Vehicle Profile', frm.doc.vehicle);
        }, __('Related'));

        frm.add_custom_button(__('Appointment History'), function () {
            frm.trigger('show_appointment_history');
        }, __('Reports'));
    },

    add_booking_helpers: function (frm) {
        frm.add_custom_button(__('Check Available Slots'), function () {
            frm.trigger('show_available_slots');
        }, __('Booking')).addClass('btn-primary');

        frm.add_custom_button(__('Load Customer Details'), function () {
            frm.trigger('load_customer_details');
        }, __('Booking'));

        frm.add_custom_button(__('Estimate Cost'), function () {
            frm.trigger('calculate_service_cost');
        }, __('Booking'));
    },

    // === STATUS INDICATORS ===

    setup_status_indicators: function (frm) {
        // Clear existing indicators
        frm.page.clear_indicators();

        if (frm.doc.appointment_status) {
            const status_colors = {
                'Pending': 'orange',
                'Confirmed': 'blue',
                'In Progress': 'yellow',
                'Completed': 'green',
                'Cancelled': 'red',
                'No Show': 'red',
                'Rescheduled': 'purple'
            };

            const status_arabic = {
                'Pending': 'في الانتظار',
                'Confirmed': 'مؤكد',
                'In Progress': 'قيد التنفيذ',
                'Completed': 'مكتمل',
                'Cancelled': 'ملغى',
                'No Show': 'لم يحضر',
                'Rescheduled': 'تم إعادة الجدولة'
            };

            const status_text = frappe.boot.lang === 'ar' ?
                status_arabic[frm.doc.appointment_status] : frm.doc.appointment_status;

            frm.page.set_indicator(status_text, status_colors[frm.doc.appointment_status]);
        }

        // Payment status indicator
        if (frm.doc.payment_status) {
            const payment_colors = {
                'Pending': 'orange',
                'Partial': 'yellow',
                'Paid': 'green',
                'Overdue': 'red',
                'Refunded': 'gray'
            };

            frm.page.add_indicator(__('Payment: {0}', [frm.doc.payment_status]),
                payment_colors[frm.doc.payment_status]);
        }

        // Priority indicator
        if (frm.doc.priority_level && frm.doc.priority_level !== 'Medium') {
            const priority_colors = {
                'Low': 'gray',
                'High': 'orange',
                'Urgent': 'red'
            };

            frm.page.add_indicator(__('Priority: {0}', [frm.doc.priority_level]),
                priority_colors[frm.doc.priority_level]);
        }
    },

    // === REAL-TIME UPDATES ===

    setup_real_time_updates: function (frm) {
        if (!frm.doc.__islocal) {
            // Setup real-time status monitoring
            frm.trigger('start_status_monitoring');

            // Setup workshop capacity monitoring
            if (frm.doc.workshop) {
                frm.trigger('monitor_workshop_capacity');
            }

            // Setup technician availability monitoring
            if (frm.doc.assigned_technician) {
                frm.trigger('monitor_technician_status');
            }
        }
    },

    start_status_monitoring: function (frm) {
        // Check for status updates every 30 seconds
        frm.status_interval = setInterval(function () {
            if (frm.doc.appointment_status === 'In Progress') {
                frm.trigger('update_service_duration');
            }

            frm.trigger('check_appointment_alerts');
        }, 30000);

        // Clear interval when form is closed
        $(window).on('beforeunload', function () {
            if (frm.status_interval) {
                clearInterval(frm.status_interval);
            }
        });
    },

    monitor_workshop_capacity: function (frm) {
        if (frm.doc.workshop && frm.doc.appointment_date) {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.workshop_appointment.workshop_appointment.get_workshop_capacity',
                args: {
                    workshop: frm.doc.workshop,
                    date: frm.doc.appointment_date
                },
                callback: function (r) {
                    if (r.message) {
                        frm.trigger('display_capacity_info', r.message);
                    }
                }
            });
        }
    },

    display_capacity_info: function (frm, capacity_info) {
        const capacity_percentage = capacity_info.capacity_percentage;
        let capacity_color = 'green';

        if (capacity_percentage > 80) {
            capacity_color = 'red';
        } else if (capacity_percentage > 60) {
            capacity_color = 'orange';
        }

        frm.dashboard.add_indicator(
            __('Workshop Capacity: {0}%', [Math.round(capacity_percentage)]),
            capacity_color
        );
    },

    // === FIELD DEPENDENCIES ===

    setup_field_dependencies: function (frm) {
        // Workshop-dependent fields
        frm.set_query('service_type', function () {
            return {
                filters: {
                    workshop: frm.doc.workshop
                }
            };
        });

        frm.set_query('assigned_technician', function () {
            return {
                filters: {
                    workshop: frm.doc.workshop,
                    status: 'Active'
                }
            };
        });

        frm.set_query('service_bay', function () {
            return {
                filters: {
                    workshop: frm.doc.workshop,
                    status: 'Available'
                }
            };
        });

        // Customer-dependent fields
        frm.set_query('vehicle', function () {
            return {
                filters: {
                    customer: frm.doc.customer
                }
            };
        });
    },

    // === FIELD EVENTS ===

    customer: function (frm) {
        if (frm.doc.customer) {
            frm.trigger('load_customer_data');
            frm.trigger('check_customer_history');
        }
    },

    load_customer_data: function (frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Customer',
                name: frm.doc.customer
            },
            callback: function (r) {
                if (r.message) {
                    const customer = r.message;
                    frm.set_value('customer_name', customer.customer_name);
                    frm.set_value('customer_name_ar', customer.customer_name_ar);
                    frm.set_value('customer_phone', customer.mobile_no);
                    frm.set_value('customer_email', customer.email_id);

                    // Check if repeat customer
                    frm.trigger('check_repeat_customer');
                }
            }
        });
    },

    check_repeat_customer: function (frm) {
        frappe.call({
            method: 'frappe.db.count',
            args: {
                doctype: 'Workshop Appointment',
                filters: {
                    customer: frm.doc.customer,
                    appointment_status: 'Completed'
                }
            },
            callback: function (r) {
                if (r.message > 0) {
                    frm.set_value('repeat_customer', 1);
                    frm.dashboard.add_indicator(__('Repeat Customer'), 'green');
                }
            }
        });
    },

    workshop: function (frm) {
        if (frm.doc.workshop) {
            frm.trigger('load_workshop_data');
            frm.trigger('refresh_available_slots');
        }
    },

    load_workshop_data: function (frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Workshop Profile',
                name: frm.doc.workshop
            },
            callback: function (r) {
                if (r.message) {
                    const workshop = r.message;
                    frm.set_value('workshop_name', workshop.workshop_name);

                    // Set currency based on workshop
                    if (workshop.default_currency) {
                        frm.set_value('currency', workshop.default_currency);
                    }
                }
            }
        });
    },

    appointment_date: function (frm) {
        if (frm.doc.appointment_date) {
            frm.trigger('validate_appointment_date');
            frm.trigger('refresh_available_slots');
            frm.trigger('set_hijri_date');
        }
    },

    validate_appointment_date: function (frm) {
        const selected_date = new Date(frm.doc.appointment_date);
        const today = new Date();

        // Check if date is in the past
        if (selected_date < today) {
            frappe.msgprint(__('Appointment date cannot be in the past'));
            frm.set_value('appointment_date', '');
            return;
        }

        // Check if date is a weekend (Friday/Saturday for Oman)
        const weekday = selected_date.getDay();
        if (weekday === 5 || weekday === 6) { // Friday or Saturday
            if (!frm.doc.emergency_appointment) {
                frappe.msgprint(__('Appointments are not available on weekends'));
                frm.set_value('appointment_date', '');
                return;
            }
        }

        // Check if date is too far in advance
        const diff_days = (selected_date - today) / (1000 * 60 * 60 * 24);
        if (diff_days > 90) {
            frappe.msgprint(__('Appointments cannot be scheduled more than 90 days in advance'));
            frm.set_value('appointment_date', '');
            return;
        }
    },

    service_type: function (frm) {
        if (frm.doc.service_type) {
            frm.trigger('load_service_details');
            frm.trigger('calculate_estimated_cost');
        }
    },

    load_service_details: function (frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Service Type',
                name: frm.doc.service_type
            },
            callback: function (r) {
                if (r.message) {
                    const service = r.message;
                    frm.set_value('service_description', service.description);
                    frm.set_value('service_description_ar', service.description_ar);
                    frm.set_value('estimated_duration', service.estimated_duration);
                    frm.set_value('service_complexity', service.complexity_level);

                    if (service.standard_rate) {
                        frm.set_value('estimated_cost', service.standard_rate);
                    }
                }
            }
        });
    },

    calendar_type: function (frm) {
        if (frm.doc.calendar_type === 'Hijri') {
            frm.trigger('set_hijri_date');
        }
    },

    set_hijri_date: function (frm) {
        if (frm.doc.appointment_date && frm.doc.calendar_type === 'Hijri') {
            frappe.call({
                method: 'universal_workshop.utils.date_utils.get_hijri_date',
                args: {
                    gregorian_date: frm.doc.appointment_date
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('hijri_date', r.message.formatted);
                    }
                }
            });
        }
    },

    // === ACTION METHODS ===

    confirm_appointment: function (frm) {
        frappe.confirm(
            __('Are you sure you want to confirm this appointment?'),
            function () {
                frm.set_value('appointment_status', 'Confirmed');
                frm.set_value('is_confirmed', 1);
                frm.set_value('confirmation_datetime', frappe.datetime.now_datetime());
                frm.set_value('confirmation_method', 'Manual');
                frm.save();

                frappe.show_alert({
                    message: __('Appointment confirmed successfully'),
                    indicator: 'green'
                });
            }
        );
    },

    start_service: function (frm) {
        frappe.confirm(
            __('Start service for this appointment?'),
            function () {
                frm.set_value('appointment_status', 'In Progress');
                frm.set_value('service_start_datetime', frappe.datetime.now_datetime());

                if (!frm.doc.check_in_datetime) {
                    frm.set_value('check_in_datetime', frappe.datetime.now_datetime());
                }

                frm.save();

                frappe.show_alert({
                    message: __('Service started'),
                    indicator: 'blue'
                });
            }
        );
    },

    complete_service: function (frm) {
        frappe.confirm(
            __('Mark service as completed?'),
            function () {
                frm.set_value('appointment_status', 'Completed');
                frm.set_value('service_end_datetime', frappe.datetime.now_datetime());
                frm.save();

                // Offer to create invoice
                frappe.confirm(
                    __('Would you like to create an invoice for this service?'),
                    function () {
                        frm.trigger('create_service_invoice');
                    }
                );

                frappe.show_alert({
                    message: __('Service completed'),
                    indicator: 'green'
                });
            }
        );
    },

    cancel_appointment: function (frm) {
        frappe.prompt([
            {
                label: __('Cancellation Reason'),
                fieldname: 'reason',
                fieldtype: 'Small Text',
                reqd: 1
            }
        ], function (values) {
            frm.set_value('appointment_status', 'Cancelled');

            // Add to internal notes
            const current_notes = frm.doc.internal_notes || '';
            const cancellation_note = `Cancelled: ${values.reason} (${frappe.datetime.now_datetime()})`;
            frm.set_value('internal_notes', current_notes + '\n' + cancellation_note);

            frm.save();

            frappe.show_alert({
                message: __('Appointment cancelled'),
                indicator: 'red'
            });
        }, __('Cancel Appointment'), __('Cancel'));
    },

    show_available_slots: function (frm) {
        if (!frm.doc.workshop || !frm.doc.appointment_date) {
            frappe.msgprint(__('Please select workshop and date first'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.workshop_appointment.workshop_appointment.get_available_time_slots',
            args: {
                workshop: frm.doc.workshop,
                date: frm.doc.appointment_date,
                service_type: frm.doc.service_type
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frm.trigger('display_time_slots', r.message);
                } else {
                    frappe.msgprint(__('No available slots for the selected date'));
                }
            }
        });
    },

    display_time_slots: function (frm, slots) {
        const dialog = new frappe.ui.Dialog({
            title: __('Available Time Slots'),
            fields: [
                {
                    label: __('Select Time Slot'),
                    fieldname: 'time_slot',
                    fieldtype: 'Select',
                    options: slots.join('\n'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Select'),
            primary_action: function (values) {
                frm.set_value('appointment_time', values.time_slot);
                dialog.hide();

                frappe.show_alert({
                    message: __('Time slot selected: {0}', [values.time_slot]),
                    indicator: 'green'
                });
            }
        });

        dialog.show();
    }
});

// === UTILITY FUNCTIONS ===

function convert_to_arabic_time(time) {
    if (!time) return '';

    const arabic_numbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let arabic_time = time.toString();

    for (let i = 0; i < 10; i++) {
        arabic_time = arabic_time.replace(new RegExp(i.toString(), 'g'), arabic_numbers[i]);
    }

    return arabic_time;
}

function format_arabic_currency(amount) {
    if (!amount) return '';

    const formatted = parseFloat(amount).toFixed(3);
    const arabic_amount = convert_to_arabic_numerals(formatted);

    return `${arabic_amount} ريال عماني`;
}

function convert_to_arabic_numerals(text) {
    const arabic_numbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let arabic_text = text.toString();

    for (let i = 0; i < 10; i++) {
        arabic_text = arabic_text.replace(new RegExp(i.toString(), 'g'), arabic_numbers[i]);
    }

    return arabic_text;
}

// === LIST VIEW CUSTOMIZATIONS ===

frappe.listview_settings['Workshop Appointment'] = {
    add_fields: ["appointment_status", "priority_level", "appointment_date", "customer_name_ar"],

    get_indicator: function (doc) {
        const status_colors = {
            'Pending': 'orange',
            'Confirmed': 'blue',
            'In Progress': 'yellow',
            'Completed': 'green',
            'Cancelled': 'red',
            'No Show': 'red',
            'Rescheduled': 'purple'
        };

        return [__(doc.appointment_status), status_colors[doc.appointment_status], "appointment_status,=," + doc.appointment_status];
    },

    onload: function (listview) {
        // Add custom filters
        listview.page.add_menu_item(__("Today's Appointments"), function () {
            listview.filter_area.add([[listview.doctype, "appointment_date", "=", frappe.datetime.get_today()]]);
        });

        listview.page.add_menu_item(__("This Week's Appointments"), function () {
            const today = new Date();
            const week_start = new Date(today.setDate(today.getDate() - today.getDay()));
            const week_end = new Date(today.setDate(today.getDate() - today.getDay() + 6));

            listview.filter_area.add([
                [listview.doctype, "appointment_date", ">=", frappe.datetime.obj_to_str(week_start)],
                [listview.doctype, "appointment_date", "<=", frappe.datetime.obj_to_str(week_end)]
            ]);
        });

        listview.page.add_menu_item(__("Pending Confirmations"), function () {
            listview.filter_area.add([[listview.doctype, "appointment_status", "=", "Pending"]]);
        });

        // Setup real-time refresh
        setInterval(function () {
            if (listview.current_view === 'List') {
                listview.refresh();
            }
        }, 60000); // Refresh every minute
    },

    formatters: {
        customer_name: function (value, field, doc) {
            // Show Arabic name if available and language is Arabic
            if (frappe.boot.lang === 'ar' && doc.customer_name_ar) {
                return doc.customer_name_ar;
            }
            return value;
        },

        appointment_date: function (value) {
            if (frappe.boot.lang === 'ar') {
                return frappe.datetime.str_to_user(value);
            }
            return value;
        }
    }
}; 