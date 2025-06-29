// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle', {
    refresh: function(frm) {
        // Add VIN Decoder button
        if (frm.doc.vin && !frm.is_new()) {
            frm.add_custom_button(__('Decode VIN'), function() {
                decode_vin_data(frm);
            }, __('Tools'));
        }

        // Add maintenance alerts if vehicle has data
        if (frm.doc.name && !frm.is_new()) {
            frm.add_custom_button(__('Check Maintenance Alerts'), function() {
                check_maintenance_alerts(frm);
            }, __('Tools'));
        }

        // Set up Arabic field handling
        setup_arabic_fields(frm);
        
        // Set up VIN field validation
        setup_vin_field(frm);
    },

    vin: function(frm) {
        // Auto-validate VIN when entered
        if (frm.doc.vin) {
            validate_vin_format(frm);
            
            // Show decode button if VIN is valid
            if (frm.doc.vin.length === 17) {
                frm.add_custom_button(__('Decode VIN'), function() {
                    decode_vin_data(frm);
                }, __('Tools'));
            }
        }
    },

    year: function(frm) {
        // Update vehicle display name when year changes
        update_vehicle_display_name(frm);
    },

    make: function(frm) {
        // Update vehicle display name when make changes
        update_vehicle_display_name(frm);
        
        // Auto-suggest Arabic translation if available
        suggest_arabic_make(frm);
    },

    model: function(frm) {
        // Update vehicle display name when model changes
        update_vehicle_display_name(frm);
        
        // Auto-suggest Arabic translation if available
        suggest_arabic_model(frm);
    },

    license_plate: function(frm) {
        // Update vehicle display name when license plate changes
        update_vehicle_display_name(frm);
    },

    last_service_date: function(frm) {
        // Calculate next service due date
        calculate_next_service_date(frm);
    },

    service_interval_km: function(frm) {
        // Recalculate next service due date
        calculate_next_service_date(frm);
    }
});

function decode_vin_data(frm) {
    if (!frm.doc.vin) {
        frappe.msgprint(__('Please enter a VIN number first'));
        return;
    }

    // Show loading indicator
    frappe.show_alert({
        message: __('Decoding VIN, please wait...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'decode_vin',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                
                if (r.message.updated_fields.length > 0) {
                    frappe.show_alert({
                        message: __('VIN decoded successfully! Updated: {0}', [r.message.updated_fields.join(', ')]),
                        indicator: 'green'
                    });
                    
                    // Refresh the form to show updated values
                    frm.refresh_fields();
                } else {
                    frappe.show_alert({
                        message: __('VIN decoded but no new data was populated'),
                        indicator: 'orange'
                    });
                }
            }
        },
        error: function(r) {
            frappe.show_alert({
                message: __('Failed to decode VIN. Please try again.'),
                indicator: 'red'
            });
        }
    });
}

function check_maintenance_alerts(frm) {
    frappe.call({
        method: 'get_maintenance_alerts',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let alerts_html = '<div class="maintenance-alerts">';
                alerts_html += '<h5>' + __('Maintenance Alerts') + '</h5>';
                
                r.message.forEach(function(alert) {
                    let badge_color = alert.priority === 'high' ? 'red' : 
                                     alert.priority === 'medium' ? 'orange' : 'blue';
                    alerts_html += `<div class="alert-item">
                        <span class="badge badge-${badge_color}">${__(alert.priority.toUpperCase())}</span>
                        ${alert.message}
                    </div>`;
                });
                
                alerts_html += '</div>';
                
                frappe.msgprint({
                    title: __('Vehicle Maintenance Alerts'),
                    message: alerts_html,
                    primary_action_label: __('OK')
                });
            } else {
                frappe.msgprint(__('No maintenance alerts for this vehicle'));
            }
        }
    });
}

function setup_arabic_fields(frm) {
    // Set RTL direction for Arabic fields
    ['license_plate_ar', 'make_ar', 'model_ar', 'color_ar', 'body_class_ar'].forEach(function(field) {
        if (frm.fields_dict[field]) {
            frm.fields_dict[field].$input.attr('dir', 'rtl');
            frm.fields_dict[field].$input.css('text-align', 'right');
        }
    });

    // Apply Arabic font if language is Arabic
    if (frappe.boot.lang === 'ar') {
        frm.$wrapper.addClass('arabic-form');
    }
}

function setup_vin_field(frm) {
    // Add VIN validation styling
    if (frm.fields_dict.vin) {
        frm.fields_dict.vin.$input.on('input', function() {
            let vin = $(this).val().replace(/\s/g, '').toUpperCase();
            let $input = $(this);
            
            // Remove previous validation classes
            $input.removeClass('vin-valid vin-invalid vin-partial');
            
            if (vin.length === 0) {
                // Empty - no styling
                return;
            } else if (vin.length === 17) {
                // Check if VIN format is valid
                if (/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) {
                    $input.addClass('vin-valid');
                } else {
                    $input.addClass('vin-invalid');
                }
            } else {
                // Partial VIN
                $input.addClass('vin-partial');
            }
        });
    }
}

function validate_vin_format(frm) {
    if (frm.doc.vin) {
        let vin = frm.doc.vin.replace(/\s/g, '').toUpperCase();
        
        if (vin.length !== 17) {
            frappe.show_alert({
                message: __('VIN must be exactly 17 characters'),
                indicator: 'red'
            });
            return false;
        }
        
        if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) {
            frappe.show_alert({
                message: __('VIN contains invalid characters (cannot contain I, O, or Q)'),
                indicator: 'red'
            });
            return false;
        }
        
        return true;
    }
    return false;
}

function update_vehicle_display_name(frm) {
    // Auto-generate vehicle display name
    if (frm.doc.year && frm.doc.make && frm.doc.model) {
        let display_name = frm.doc.year + ' ' + frm.doc.make + ' ' + frm.doc.model;
        if (frm.doc.license_plate) {
            display_name += ' (' + frm.doc.license_plate + ')';
        }
        frm.set_value('vehicle_display_name', display_name);
    }
}

function suggest_arabic_make(frm) {
    // Simple Arabic suggestions for common makes
    const make_translations = {
        'TOYOTA': 'تويوتا',
        'HONDA': 'هوندا',
        'NISSAN': 'نيسان',
        'FORD': 'فورد',
        'CHEVROLET': 'شيفرولت',
        'BMW': 'بي إم دبليو',
        'MERCEDES-BENZ': 'مرسيدس بنز',
        'AUDI': 'أودي',
        'VOLKSWAGEN': 'فولكس فاغن',
        'HYUNDAI': 'هيونداي',
        'KIA': 'كيا',
        'MAZDA': 'مازدا',
        'SUBARU': 'سوبارو',
        'LEXUS': 'لكزس'
    };
    
    if (frm.doc.make && !frm.doc.make_ar) {
        let arabic_make = make_translations[frm.doc.make.toUpperCase()];
        if (arabic_make) {
            frm.set_value('make_ar', arabic_make);
        }
    }
}

function suggest_arabic_model(frm) {
    // For now, just suggest user to fill manually
    // In future, this could integrate with a translation API
    if (frm.doc.model && !frm.doc.model_ar) {
        // Could implement model translation logic here
    }
}

function calculate_next_service_date(frm) {
    if (frm.doc.last_service_date && frm.doc.service_interval_km) {
        // Simple calculation - estimate 3-6 months based on interval
        let months_to_add = Math.max(3, Math.min(6, frm.doc.service_interval_km / 2000));
        
        let last_service = frappe.datetime.str_to_obj(frm.doc.last_service_date);
        let next_service = frappe.datetime.add_months(last_service, months_to_add);
        
        frm.set_value('next_service_due', frappe.datetime.obj_to_str(next_service));
        
        frappe.show_alert({
            message: __('Next service date calculated based on interval'),
            indicator: 'blue'
        });
    }
} 