// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Supplier Parts Category', {
    refresh: function(frm) {
        frm.add_custom_button(__('View Category Parts'), function() {
            frm.trigger('view_category_parts');
        });
        
        frm.add_custom_button(__('Export Category'), function() {
            frm.trigger('export_category');
        });
    },
    
    view_category_parts: function(frm) {
        if (!frm.doc.category_name) {
            frappe.msgprint(__('Please enter a category name'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.supplier_parts_category.supplier_parts_category.get_category_parts',
            args: {
                category_name: frm.doc.category_name,
                supplier: frm.doc.supplier
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_category_parts', r.message);
                }
            }
        });
    },
    
    display_category_parts: function(frm, parts) {
        const dialog = new frappe.ui.Dialog({
            title: __('Category Parts'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'parts_table',
                options: frm.trigger('create_parts_table', parts)
            }]
        });
        
        dialog.show();
    },
    
    create_parts_table: function(frm, parts) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Item Code')}</th>
                        <th>${__('Item Name')}</th>
                        <th>${__('Part Number')}</th>
                        <th>${__('Current Stock')}</th>
                        <th>${__('Reorder Level')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        parts.forEach(part => {
            table_html += `
                <tr>
                    <td>${part.item_code}</td>
                    <td>${part.item_name}</td>
                    <td>${part.part_number || '-'}</td>
                    <td>${part.current_stock || 0}</td>
                    <td>${part.reorder_level || 0}</td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    export_category: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.supplier_parts_category.supplier_parts_category.export_category',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    const link = document.createElement('a');
                    link.href = r.message.file_url;
                    link.download = r.message.filename;
                    link.click();
                }
            }
        });
    },
    
    validate: function(frm) {
        if (!frm.doc.category_name) {
            frappe.msgprint(__('Category name is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.supplier) {
            frappe.msgprint(__('Supplier is required'));
            frappe.validated = false;
        }
    }
}); 