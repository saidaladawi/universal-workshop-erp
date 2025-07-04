// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Customer Vehicle', {
    refresh: function(frm) {
        frm.add_custom_button(__('Service History'), function() {
            frm.trigger('view_service_history');
        });
        
        frm.add_custom_button(__('Maintenance Schedule'), function() {
            frm.trigger('view_maintenance_schedule');
        });
        
        frm.add_custom_button(__('Decode VIN'), function() {
            frm.trigger('decode_vin');
        });
    },
    
    view_service_history: function(frm) {
        if (!frm.doc.vehicle_id) {
            frappe.msgprint(__('Please enter a vehicle ID'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_vehicle.customer_vehicle.get_service_history',
            args: {
                vehicle_id: frm.doc.vehicle_id
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_service_history', r.message);
                }
            }
        });
    },
    
    display_service_history: function(frm, history) {
        const dialog = new frappe.ui.Dialog({
            title: __('Service History'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'history_table',
                options: frm.trigger('create_history_table', history)
            }]
        });
        
        dialog.show();
    },
    
    create_history_table: function(frm, history) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Service Date')}</th>
                        <th>${__('Service Type')}</th>
                        <th>${__('Technician')}</th>
                        <th>${__('Cost')}</th>
                        <th>${__('Status')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        history.forEach(service => {
            table_html += `
                <tr>
                    <td>${service.service_date}</td>
                    <td>${service.service_type}</td>
                    <td>${service.technician || '-'}</td>
                    <td>${service.cost || 0}</td>
                    <td>${service.status}</td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    view_maintenance_schedule: function(frm) {
        if (!frm.doc.vehicle_id) {
            frappe.msgprint(__('Please enter a vehicle ID'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_vehicle.customer_vehicle.get_maintenance_schedule',
            args: {
                vehicle_id: frm.doc.vehicle_id
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_maintenance_schedule', r.message);
                }
            }
        });
    },
    
    display_maintenance_schedule: function(frm, schedule) {
        const dialog = new frappe.ui.Dialog({
            title: __('Maintenance Schedule'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'schedule_table',
                options: frm.trigger('create_schedule_table', schedule)
            }]
        });
        
        dialog.show();
    },
    
    create_schedule_table: function(frm, schedule) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Service Type')}</th>
                        <th>${__('Due Date')}</th>
                        <th>${__('Mileage')}</th>
                        <th>${__('Status')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        schedule.forEach(item => {
            table_html += `
                <tr>
                    <td>${item.service_type}</td>
                    <td>${item.due_date}</td>
                    <td>${item.mileage || '-'}</td>
                    <td>${item.status}</td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    decode_vin: function(frm) {
        if (!frm.doc.vin_number) {
            frappe.msgprint(__('Please enter a VIN number'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_vehicle.customer_vehicle.decode_vin',
            args: {
                vin_number: frm.doc.vin_number
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_vin_info', r.message);
                }
            }
        });
    },
    
    display_vin_info: function(frm, vin_info) {
        const dialog = new frappe.ui.Dialog({
            title: __('VIN Decode Results'),
            fields: [{
                label: __('Make'),
                fieldname: 'make',
                fieldtype: 'Data',
                default: vin_info.make,
                read_only: 1
            }, {
                label: __('Model'),
                fieldname: 'model',
                fieldtype: 'Data',
                default: vin_info.model,
                read_only: 1
            }, {
                label: __('Year'),
                fieldname: 'year',
                fieldtype: 'Data',
                default: vin_info.year,
                read_only: 1
            }, {
                label: __('Engine'),
                fieldname: 'engine',
                fieldtype: 'Data',
                default: vin_info.engine,
                read_only: 1
            }, {
                label: __('Transmission'),
                fieldname: 'transmission',
                fieldtype: 'Data',
                default: vin_info.transmission,
                read_only: 1
            }],
            primary_action_label: __('Apply to Form'),
            primary_action: function() {
                frm.set_value('make', vin_info.make);
                frm.set_value('model', vin_info.model);
                frm.set_value('year', vin_info.year);
                frm.set_value('engine', vin_info.engine);
                frm.set_value('transmission', vin_info.transmission);
                dialog.hide();
            }
        });
        
        dialog.show();
    },
    
    validate: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Customer is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.vehicle_id) {
            frappe.msgprint(__('Vehicle ID is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.make || !frm.doc.model) {
            frappe.msgprint(__('Vehicle make and model are required'));
            frappe.validated = false;
        }
    }
}); 