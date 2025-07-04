// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Stock Transfer Log', {
    refresh: function(frm) {
        frm.add_custom_button(__('View Transfer History'), function() {
            frm.trigger('show_transfer_history');
        });
        
        frm.add_custom_button(__('Export Transfer Log'), function() {
            frm.trigger('export_transfer_log');
        });
    },
    
    show_transfer_history: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.stock_transfer_log.stock_transfer_log.get_transfer_history',
            args: {
                item_code: frm.doc.item_code,
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('display_transfer_history', r.message);
                }
            }
        });
    },
    
    display_transfer_history: function(frm, history_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Transfer History'),
            size: 'large',
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'history_table',
                options: frm.trigger('create_history_table', history_data)
            }]
        });
        
        dialog.show();
    },
    
    create_history_table: function(frm, history_data) {
        let table_html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Date')}</th>
                        <th>${__('From')}</th>
                        <th>${__('To')}</th>
                        <th>${__('Quantity')}</th>
                        <th>${__('Reference')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        history_data.forEach(transfer => {
            table_html += `
                <tr>
                    <td>${transfer.posting_date}</td>
                    <td>${transfer.from_warehouse || '-'}</td>
                    <td>${transfer.to_warehouse || '-'}</td>
                    <td>${transfer.qty}</td>
                    <td>${transfer.reference}</td>
                </tr>
            `;
        });
        
        table_html += '</tbody></table>';
        return table_html;
    },
    
    export_transfer_log: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.stock_transfer_log.stock_transfer_log.export_log',
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
        if (frm.doc.from_date && frm.doc.to_date) {
            if (frm.doc.from_date > frm.doc.to_date) {
                frappe.msgprint(__('From date cannot be after to date'));
                frappe.validated = false;
            }
        }
    }
}); 