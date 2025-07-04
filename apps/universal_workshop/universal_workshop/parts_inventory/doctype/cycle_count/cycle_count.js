frappe.ui.form.on('Cycle Count', {
    refresh: function(frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
    },
    
    setup_custom_buttons: function(frm) {
        if (frm.doc.cycle_count_status === 'Draft') {
            frm.add_custom_button(__('Start Count'), function() {
                frm.trigger('start_count');
            }, __('Actions'));
        }
        
        if (frm.doc.cycle_count_status === 'In Progress') {
            frm.add_custom_button(__('Complete Count'), function() {
                frm.trigger('complete_count');
            }, __('Actions'));
        }
        
        if (frm.doc.cycle_count_status === 'Completed') {
            frm.add_custom_button(__('Approve Count'), function() {
                frm.trigger('approve_count');
            }, __('Actions'));
        }
        
        frm.add_custom_button(__('Get Progress'), function() {
            frm.trigger('get_count_progress');
        });
        
        frm.add_custom_button(__('Generate Report'), function() {
            frm.trigger('generate_count_report');
        });
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        ['cycle_count_name_ar', 'count_notes_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },
    
    count_type: function(frm) {
        // Update count method based on count type
        let count_method = 'Manual Count';
        
        switch(frm.doc.count_type) {
            case 'Full Count':
                count_method = 'Manual Count';
                break;
            case 'Partial Count':
                count_method = 'Barcode Scanner';
                break;
            case 'ABC Count':
                count_method = 'Mobile App';
                break;
            case 'Random Count':
                count_method = 'Manual Count';
                break;
        }
        
        frm.set_value('count_method', count_method);
    },
    
    start_count: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.cycle_count.cycle_count.start_count',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Cycle Count Started'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to start cycle count'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    complete_count: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.cycle_count.cycle_count.complete_count',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Cycle Count Completed'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to complete cycle count'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    approve_count: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.cycle_count.cycle_count.approve_count',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Cycle Count Approved'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.message.message || __('Failed to approve cycle count'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    get_count_progress: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.cycle_count.cycle_count.get_count_progress',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    let message = __(`Total Items: ${r.message.total_items}<br>
                                    Counted Items: ${r.message.counted_items}<br>
                                    Pending Items: ${r.message.pending_items}<br>
                                    Completion: ${r.message.completion_percentage.toFixed(1)}%<br>
                                    Status: ${r.message.status}`);
                    
                    frappe.msgprint({
                        title: __('Count Progress'),
                        message: message,
                        indicator: 'blue'
                    });
                }
            }
        });
    },
    
    generate_count_report: function(frm) {
        frappe.call({
            method: 'universal_workshop.parts_inventory.doctype.cycle_count.cycle_count.generate_count_report',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    let message = __(`Count Name: ${r.message.cycle_count_name}<br>
                                    Date: ${r.message.count_date}<br>
                                    Warehouse: ${r.message.warehouse}<br>
                                    Total Items: ${r.message.total_items}<br>
                                    Items with Variance: ${r.message.items_with_variance}<br>
                                    Variance Percentage: ${r.message.variance_percentage.toFixed(1)}%<br>
                                    Duration: ${r.message.duration}<br>
                                    Status: ${r.message.status}`);
                    
                    frappe.msgprint({
                        title: __('Cycle Count Report'),
                        message: message,
                        indicator: 'blue'
                    });
                }
            }
        });
    },
    
    requires_approval: function(frm) {
        if (frm.doc.requires_approval) {
            frm.set_df_property('approval_threshold', 'reqd', 1);
        } else {
            frm.set_df_property('approval_threshold', 'reqd', 0);
        }
    }
}); 