// Copyright (c) 2025, Universal Workshop ERP
// For license information, see license.txt

frappe.ui.form.on('Customer Preference', {
    refresh: function(frm) {
        frm.add_custom_button(__('Apply Preferences'), function() {
            frm.trigger('apply_preferences');
        });
        
        frm.add_custom_button(__('Reset to Defaults'), function() {
            frm.trigger('reset_to_defaults');
        });
    },
    
    apply_preferences: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Please select a customer'));
            return;
        }
        
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_preference.customer_preference.apply_preferences',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Preferences applied successfully'));
                }
            }
        });
    },
    
    reset_to_defaults: function(frm) {
        frappe.confirm(__('Are you sure you want to reset all preferences to defaults?'), function() {
            frm.trigger('perform_reset');
        });
    },
    
    perform_reset: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_preference.customer_preference.reset_to_defaults',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Preferences reset to defaults'));
                    frm.reload_doc();
                }
            }
        });
    },
    
    validate: function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__('Customer is required'));
            frappe.validated = false;
        }
        
        // Validate communication preferences
        if (frm.doc.communication_language && !['ar', 'en'].includes(frm.doc.communication_language)) {
            frappe.msgprint(__('Communication language must be Arabic or English'));
            frappe.validated = false;
        }
        
        // Validate notification preferences
        if (frm.doc.sms_notifications && !frm.doc.phone_number) {
            frappe.msgprint(__('Phone number is required for SMS notifications'));
            frappe.validated = false;
        }
        
        if (frm.doc.email_notifications && !frm.doc.email) {
            frappe.msgprint(__('Email is required for email notifications'));
            frappe.validated = false;
        }
    }
}); 