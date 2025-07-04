// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Part Cross Reference', {
    refresh: function(frm) {
        frm.add_custom_button(__('Search Cross References'), function() {
            frm.trigger('search_cross_references');
        });
        
        frm.add_custom_button(__('Import Cross References'), function() {
            frm.trigger('import_cross_references');
        });
    },
    
    search_cross_references: function(frm) {
        if (!frm.doc.part_number) {
            frappe.msgprint(__('Please enter a part number to search'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.part_cross_reference.part_cross_reference.search_cross_references',
            args: {
                part_number: frm.doc.part_number
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_search_results', r.message);
                }
            }
        });
    },
    
    display_search_results: function(frm, results) {
        const dialog = new frappe.ui.Dialog({
            title: __('Cross Reference Search Results'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'results_table',
                options: frm.trigger('create_results_table', results)
            }]
        });
        
        dialog.show();
    },
    
    create_results_table: function(frm, results) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Part Number')}</th>
                        <th>${__('Manufacturer')}</th>
                        <th>${__('Description')}</th>
                        <th>${__('Compatibility')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        results.forEach(result => {
            table_html += `
                <tr>
                    <td>${result.part_number}</td>
                    <td>${result.manufacturer || '-'}</td>
                    <td>${result.description || '-'}</td>
                    <td>${result.compatibility || '-'}</td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    import_cross_references: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Import Cross References'),
            fields: [{
                label: __('File'),
                fieldname: 'file',
                fieldtype: 'Attach',
                reqd: 1
            }, {
                label: __('File Type'),
                fieldname: 'file_type',
                fieldtype: 'Select',
                options: 'CSV\nExcel',
                default: 'CSV',
                reqd: 1
            }],
            primary_action_label: __('Import'),
            primary_action: function() {
                const values = dialog.get_values();
                if (values) {
                    frm.trigger('process_import', values);
                    dialog.hide();
                }
            }
        });
        
        dialog.show();
    },
    
    process_import: function(frm, values) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.part_cross_reference.part_cross_reference.import_cross_references',
            args: {
                file_url: values.file,
                file_type: values.file_type
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Import completed successfully'));
                    frm.reload_doc();
                }
            }
        });
    },
    
    validate: function(frm) {
        if (!frm.doc.part_number) {
            frappe.msgprint(__('Part number is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.manufacturer) {
            frappe.msgprint(__('Manufacturer is required'));
            frappe.validated = false;
        }
    }
}); 