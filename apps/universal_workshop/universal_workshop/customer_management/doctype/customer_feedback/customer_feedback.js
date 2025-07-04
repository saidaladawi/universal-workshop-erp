// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Customer Feedback', {
    refresh: function(frm) {
        frm.add_custom_button(__('Send Response'), function() {
            frm.trigger('send_response');
        });
        
        frm.add_custom_button(__('Escalate Feedback'), function() {
            frm.trigger('escalate_feedback');
        });
    },
    
    send_response: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Please select a customer'));
            return;
        }
        
        const dialog = new frappe.ui.Dialog({
            title: __('Send Response'),
            fields: [{
                label: __('Response Message'),
                fieldname: 'response_message',
                fieldtype: 'Text Editor',
                reqd: 1
            }, {
                label: __('Send via'),
                fieldname: 'send_via',
                fieldtype: 'Select',
                options: 'Email\nSMS\nBoth',
                default: 'Email',
                reqd: 1
            }],
            primary_action_label: __('Send'),
            primary_action: function() {
                const values = dialog.get_values();
                if (values) {
                    frm.trigger('process_response', values);
                    dialog.hide();
                }
            }
        });
        
        dialog.show();
    },
    
    process_response: function(frm, values) {
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_feedback.customer_feedback.send_response',
            args: {
                docname: frm.doc.name,
                response_message: values.response_message,
                send_via: values.send_via
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Response sent successfully'));
                    frm.set_value('status', 'Responded');
                    frm.set_value('response_date', frappe.datetime.nowdate());
                }
            }
        });
    },
    
    escalate_feedback: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Please select a customer'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_feedback.customer_feedback.escalate_feedback',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Feedback escalated successfully'));
                    frm.set_value('status', 'Escalated');
                    frm.set_value('escalation_date', frappe.datetime.nowdate());
                }
            }
        });
    },
    
    validate: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Customer is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.feedback_type) {
            frappe.msgprint(__('Feedback type is required'));
            frappe.validated = false;
        }
        
        if (!frm.doc.feedback_message) {
            frappe.msgprint(__('Feedback message is required'));
            frappe.validated = false;
        }
        
        if (frm.doc.rating && (frm.doc.rating < 1 || frm.doc.rating > 5)) {
            frappe.msgprint(__('Rating must be between 1 and 5'));
            frappe.validated = false;
        }
    }
}); 