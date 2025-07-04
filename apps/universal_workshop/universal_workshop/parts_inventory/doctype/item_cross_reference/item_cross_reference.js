// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Item Cross Reference', {
    refresh: function(frm) {
        frm.add_custom_button(__('Find Cross References'), function() {
            frm.trigger('find_cross_references');
        });
        
        frm.add_custom_button(__('Validate Cross Reference'), function() {
            frm.trigger('validate_cross_reference');
        });
    },
    
    find_cross_references: function(frm) {
        if (!frm.doc.item_code) {
            frappe.msgprint(__('Please enter an item code to search'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.item_cross_reference.item_cross_reference.find_cross_references',
            args: {
                item_code: frm.doc.item_code
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_cross_references', r.message);
                }
            }
        });
    },
    
    display_cross_references: function(frm, references) {
        const dialog = new frappe.ui.Dialog({
            title: __('Cross References Found'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'references_table',
                options: frm.trigger('create_references_table', references)
            }]
        });
        
        dialog.show();
    },
    
    create_references_table: function(frm, references) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Cross Reference Item')}</th>
                        <th>${__('Manufacturer')}</th>
                        <th>${__('Part Number')}</th>
                        <th>${__('Compatibility Score')}</th>
                        <th>${__('Action')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        references.forEach(ref => {
            table_html += `
                <tr>
                    <td>${ref.cross_reference_item}</td>
                    <td>${ref.manufacturer || '-'}</td>
                    <td>${ref.part_number || '-'}</td>
                    <td>${ref.compatibility_score || 'N/A'}</td>
                    <td>
                        <button class="btn btn-xs btn-primary" onclick="select_cross_reference('${ref.cross_reference_item}')">
                            ${__('Select')}
                        </button>
                    </td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    validate_cross_reference: function(frm) {
        if (!frm.doc.item_code || !frm.doc.cross_reference_item) {
            frappe.msgprint(__('Both item code and cross reference item are required'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.item_cross_reference.item_cross_reference.validate_cross_reference',
            args: {
                item_code: frm.doc.item_code,
                cross_reference_item: frm.doc.cross_reference_item
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Cross reference validation completed'));
                    frm.set_value('validation_status', r.message.status);
                    frm.set_value('validation_date', r.message.date);
                }
            }
        });
    },
    
    validate: function(frm) {
        if (!frm.doc.item_code) {
            frappe.msgprint(__('Item code is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.cross_reference_item) {
            frappe.msgprint(__('Cross reference item is required'));
            frappe.validated = false;
        }
        
        if (frm.doc.item_code === frm.doc.cross_reference_item) {
            frappe.msgprint(__('Item code and cross reference item cannot be the same'));
            frappe.validated = false;
        }
    }
});

// Global function for cross reference selection
window.select_cross_reference = function(cross_reference_item) {
    const frm = cur_frm;
    if (frm) {
        frm.set_value('cross_reference_item', cross_reference_item);
        frm.trigger('validate_cross_reference');
    }
}; 