// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Record', {
    refresh: function(frm) {
        // Add custom buttons for completed records
        if (!frm.is_new() && frm.doc.status === 'Completed') {
            frm.add_custom_button(__('View Service History'), function() {
                show_service_history(frm);
            });
        }
        
        // Set up Arabic form handling
        setup_arabic_form(frm);
        
        // Load vehicle information
        if (frm.doc.vehicle) {
            load_vehicle_info(frm);
        }
        
        // Set up real-time cost calculation
        setup_cost_calculation(frm);
        
        // Add service history section
        if (frm.doc.vehicle && !frm.is_new()) {
            load_service_history(frm);
        }
    },
    
    vehicle: function(frm) {
        if (frm.doc.vehicle) {
            load_vehicle_info(frm);
            load_service_history(frm);
        }
    },
    
    service_type: function(frm) {
        // Auto-populate Arabic translation
        if (frm.doc.service_type && !frm.doc.service_type_ar) {
            const translations = {
                "Oil Change": "تغيير الزيت",
                "Brake Service": "خدمة الفرامل",
                "Engine Repair": "إصلاح المحرك",
                "Transmission Service": "خدمة ناقل الحركة",
                "Tire Replacement": "استبدال الإطارات",
                "Battery Replacement": "استبدال البطارية",
                "Air Filter Replacement": "استبدال فلتر الهواء",
                "Spark Plug Replacement": "استبدال شمعات الإشعال",
                "Cooling System Service": "خدمة نظام التبريد",
                "Electrical Repair": "إصلاح كهربائي",
                "General Maintenance": "صيانة عامة",
                "Inspection": "فحص",
                "Other": "أخرى"
            };
            
            frm.set_value('service_type_ar', translations[frm.doc.service_type] || '');
        }
    },
    
    labor_hours: function(frm) {
        calculate_totals(frm);
    },
    
    labor_cost: function(frm) {
        calculate_totals(frm);
    },
    
    mileage_at_service: function(frm) {
        // Auto-calculate next service due
        if (frm.doc.mileage_at_service && frm.doc.vehicle) {
            frappe.db.get_value('Vehicle', frm.doc.vehicle, 'service_interval_km').then(r => {
                if (r.message && r.message.service_interval_km) {
                    const interval = r.message.service_interval_km || 10000;
                    frm.set_value('next_service_due_km', frm.doc.mileage_at_service + interval);
                }
            });
        }
    }
});

// Child table events for Parts Used
frappe.ui.form.on('Service Record Parts', {
    quantity: function(frm, cdt, cdn) {
        calculate_part_total(frm, cdt, cdn);
        calculate_totals(frm);
    },
    
    unit_cost: function(frm, cdt, cdn) {
        calculate_part_total(frm, cdt, cdn);
        calculate_totals(frm);
    },
    
    part_name: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        // Auto-populate Arabic translation for common parts
        if (row.part_name && !row.part_name_ar) {
            const translations = {
                "Engine Oil": "زيت المحرك",
                "Oil Filter": "فلتر الزيت",
                "Air Filter": "فلتر الهواء",
                "Fuel Filter": "فلتر الوقود",
                "Brake Pads": "تيل الفرامل",
                "Brake Fluid": "زيت الفرامل",
                "Spark Plugs": "شمعات الإشعال",
                "Battery": "بطارية",
                "Tire": "إطار",
                "Transmission Oil": "زيت ناقل الحركة",
                "Coolant": "سائل التبريد",
                "Radiator": "مشع",
                "Alternator": "دينامو",
                "Starter": "سلف",
                "Clutch": "كلتش",
                "Timing Belt": "سير التوقيت",
                "Water Pump": "طلمبة الماء",
                "Thermostat": "ثرموستات",
                "Shock Absorber": "ماص الصدمات"
            };
            
            frappe.model.set_value(cdt, cdn, 'part_name_ar', translations[row.part_name] || '');
        }
    },
    
    parts_used_remove: function(frm) {
        calculate_totals(frm);
    }
});

function add_custom_buttons(frm) {
    // Add buttons only for saved documents
    if (!frm.is_new()) {
        // View Service History button
        frm.add_custom_button(__('Service History'), function() {
            show_service_history_dialog(frm);
        }, __('View'));
        
        // Cost Breakdown button
        frm.add_custom_button(__('Cost Breakdown'), function() {
            show_cost_breakdown_dialog(frm);
        }, __('View'));
        
        // Print Service Report button
        frm.add_custom_button(__('Print Report'), function() {
            frappe.utils.print(
                frm.doc.doctype,
                frm.doc.name,
                'Service Record Print Format'
            );
        }, __('Print'));
    }
    
    // Quick Action buttons
    if (frm.doc.status === 'Draft') {
        frm.add_custom_button(__('Start Service'), function() {
            frm.set_value('status', 'In Progress');
            frm.save();
        }, __('Actions'));
    }
    
    if (frm.doc.status === 'In Progress') {
        frm.add_custom_button(__('Complete Service'), function() {
            frm.set_value('status', 'Completed');
            frm.set_value('completion_date', frappe.datetime.now_datetime());
            frm.save();
        }, __('Actions'));
    }
}

function setup_arabic_form(frm) {
    // Apply RTL styling for Arabic fields
    if (frappe.boot.lang === 'ar') {
        frm.page.main.addClass('arabic-form');
        
        // Set RTL direction for Arabic fields
        ['service_type_ar', 'description_ar', 'notes_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    }
}

function load_vehicle_info(frm) {
    if (!frm.doc.vehicle) return;
    
    frappe.call({
        method: 'get_vehicle_info',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                const info = r.message;
                // Simple vehicle info display
                frm.set_intro(`Vehicle: ${info.vehicle_display_name} | License: ${info.license_plate || 'N/A'} | Current Mileage: ${info.current_mileage || 'N/A'} KM`);
            }
        }
    });
}

function load_service_history(frm) {
    if (!frm.doc.vehicle) return;
    
    frappe.call({
        method: 'get_service_history',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                const history = r.message;
                
                // Create service history HTML
                let history_html = '<div class="service-history" style="margin-top: 15px;"><h6>Recent Service History:</h6>';
                
                history.slice(0, 3).forEach(service => {
                    const status_color = {
                        'Completed': 'green',
                        'In Progress': 'orange',
                        'Draft': 'blue',
                        'Cancelled': 'red'
                    }[service.status] || 'gray';
                    
                    history_html += `
                        <div style="
                            border-left: 3px solid ${status_color}; 
                            padding-left: 10px; 
                            margin: 8px 0; 
                            background: #f9f9f9; 
                            padding: 8px;
                        ">
                            <strong>${service.service_type}</strong> - ${service.service_date}<br>
                            <small>
                                ${service.mileage_at_service} KM | 
                                OMR ${service.total_cost || 0} | 
                                <span style="color: ${status_color};">${service.status}</span>
                            </small>
                        </div>
                    `;
                });
                
                history_html += '</div>';
                
                // Add to form if not already present
                if (frm.fields_dict.vehicle.$wrapper.find('.service-history').length === 0) {
                    frm.fields_dict.vehicle.$wrapper.append(history_html);
                }
            }
        }
    });
}

function calculate_part_total(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    
    if (row.quantity && row.unit_cost) {
        const total = row.quantity * row.unit_cost;
        frappe.model.set_value(cdt, cdn, 'total_cost', total);
    }
}

function calculate_totals(frm) {
    let parts_total = 0;
    
    // Calculate parts total
    if (frm.doc.parts_used) {
        frm.doc.parts_used.forEach(part => {
            if (part.total_cost) {
                parts_total += part.total_cost;
            }
        });
    }
    
    // Set parts total
    frm.set_value('parts_total_cost', parts_total);
    
    // Calculate overall total
    const labor_cost = frm.doc.labor_cost || 0;
    const total_cost = parts_total + labor_cost;
    frm.set_value('total_cost', total_cost);
}

function setup_cost_calculation(frm) {
    // Auto-calculate when form loads
    calculate_totals(frm);
    
    // Real-time calculation indicator
    const cost_indicator = $(`
        <div class="cost-indicator" style="
            position: fixed; 
            top: 70px; 
            right: 20px; 
            background: #007bff; 
            color: white; 
            padding: 10px; 
            border-radius: 5px; 
            z-index: 1000;
            display: none;
        ">
            💰 Total: OMR <span class="total-amount">${frm.doc.total_cost || 0}</span>
        </div>
    `);
    
    $('body').append(cost_indicator);
    
    // Show/hide indicator based on form focus
    frm.wrapper.on('focusin', function() {
        cost_indicator.show();
    }).on('focusout', function() {
        setTimeout(() => cost_indicator.hide(), 2000);
    });
    
    // Update indicator when total changes
    frm.doc.__onchange = function() {
        cost_indicator.find('.total-amount').text(frm.doc.total_cost || 0);
    };
}

function show_service_history_dialog(frm) {
    frappe.call({
        method: 'get_service_history',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                const history = r.message;
                
                let dialog_html = '<div class="service-history-dialog">';
                
                if (history.length === 0) {
                    dialog_html += '<p>No previous service records found for this vehicle.</p>';
                } else {
                    history.forEach(service => {
                        dialog_html += `
                            <div class="service-item" style="
                                border: 1px solid #dee2e6; 
                                margin: 10px 0; 
                                padding: 15px; 
                                border-radius: 5px;
                            ">
                                <h6>${service.service_type} - ${service.service_date}</h6>
                                <p><strong>Mileage:</strong> ${service.mileage_at_service} KM</p>
                                <p><strong>Cost:</strong> OMR ${service.total_cost || 0}</p>
                                <p><strong>Status:</strong> ${service.status}</p>
                                <a href="/app/service-record/${service.name}" target="_blank">View Details →</a>
                            </div>
                        `;
                    });
                }
                
                dialog_html += '</div>';
                
                const dialog = new frappe.ui.Dialog({
                    title: 'Service History',
                    fields: [{
                        fieldtype: 'HTML',
                        fieldname: 'history_html',
                        options: dialog_html
                    }]
                });
                
                dialog.show();
            }
        }
    });
}

function show_cost_breakdown_dialog(frm) {
    frappe.call({
        method: 'get_cost_breakdown',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                const breakdown = r.message;
                
                let dialog_html = `
                    <div class="cost-breakdown">
                        <h6>Cost Summary</h6>
                        <table class="table table-bordered">
                            <tr><td><strong>Labor Cost:</strong></td><td>OMR ${breakdown.labor_cost}</td></tr>
                            <tr><td><strong>Parts Cost:</strong></td><td>OMR ${breakdown.parts_cost}</td></tr>
                            <tr class="table-primary"><td><strong>Total Cost:</strong></td><td><strong>OMR ${breakdown.total_cost}</strong></td></tr>
                        </table>
                `;
                
                if (breakdown.parts_details && breakdown.parts_details.length > 0) {
                    dialog_html += `
                        <h6 style="margin-top: 20px;">Parts Breakdown</h6>
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Part Name</th>
                                    <th>Quantity</th>
                                    <th>Unit Cost</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    breakdown.parts_details.forEach(part => {
                        dialog_html += `
                            <tr>
                                <td>${part.part_name}</td>
                                <td>${part.quantity}</td>
                                <td>OMR ${part.unit_cost}</td>
                                <td>OMR ${part.total_cost}</td>
                            </tr>
                        `;
                    });
                    
                    dialog_html += '</tbody></table>';
                }
                
                dialog_html += '</div>';
                
                const dialog = new frappe.ui.Dialog({
                    title: 'Cost Breakdown',
                    size: 'large',
                    fields: [{
                        fieldtype: 'HTML',
                        fieldname: 'breakdown_html',
                        options: dialog_html
                    }]
                });
                
                dialog.show();
            }
        }
    });
}

function show_service_history(frm) {
    frappe.call({
        method: 'get_service_history',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: 'Service History',
                    message: `Found ${r.message.length} previous service records for this vehicle.`,
                    indicator: 'blue'
                });
            }
        }
    });
} 