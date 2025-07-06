frappe.ui.form.on('Payment Gateway Config', {
    refresh: function(frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
    },
    
    setup_custom_buttons: function(frm) {
        frm.add_custom_button(__('Test Connection'), function() {
            frm.trigger('test_connection');
        });
        
        frm.add_custom_button(__('Calculate Transaction Fee'), function() {
            frm.trigger('calculate_transaction_fee');
        });
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        ['gateway_name_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },
    
    environment: function(frm) {
        if (frm.doc.environment === 'Production') {
            frm.set_value('test_mode', 0);
            frm.set_df_property('test_mode', 'read_only', 1);
        } else {
            frm.set_df_property('test_mode', 'read_only', 0);
        }
    },
    
    enable_webhooks: function(frm) {
        if (frm.doc.enable_webhooks) {
            frm.set_df_property('webhook_url', 'reqd', 1);
            frm.set_df_property('webhook_secret', 'reqd', 1);
        } else {
            frm.set_df_property('webhook_url', 'reqd', 0);
            frm.set_df_property('webhook_secret', 'reqd', 0);
        }
    },
    
    test_connection: function(frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.doctype.payment_gateway_config.payment_gateway_config.test_connection',
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Connection Test'),
                        message: r.message.message,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Connection Test'),
                        message: r.message.message || __('Connection test failed'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    calculate_transaction_fee: function(frm) {
        let amount = frappe.prompt(__('Enter amount to calculate fee:'), {
            fieldtype: 'Float',
            label: __('Amount'),
            default: 100.0
        }, (values) => {
            if (values.amount) {
                frappe.call({
                    method: 'universal_workshop.billing_management.doctype.payment_gateway_config.payment_gateway_config.calculate_transaction_fee',
                    args: {
                        docname: frm.doc.name,
                        amount: values.amount
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __('Transaction Fee Calculation'),
                                message: __(`Amount: ${r.message.amount} OMR<br>
                                           Fee Percentage: ${r.message.fee_percentage}%<br>
                                           Fee: ${r.message.fee} OMR<br>
                                           Total: ${r.message.total} OMR`),
                                indicator: 'blue'
                            });
                        }
                    }
                });
            }
        });
    },
    
    gateway_type: function(frm) {
        // Update payment methods based on gateway type
        let payment_methods = [];
        
        switch(frm.doc.gateway_type) {
            case 'Credit Card':
                payment_methods = ['Visa', 'Mastercard', 'American Express', 'Discover'];
                break;
            case 'Bank Transfer':
                payment_methods = ['Bank Transfer', 'ACH', 'Wire Transfer'];
                break;
            case 'Digital Wallet':
                payment_methods = ['PayPal', 'Apple Pay', 'Google Pay', 'Samsung Pay'];
                break;
            case 'Local Payment':
                payment_methods = ['Cash', 'Cheque', 'Local Bank Transfer'];
                break;
        }
        
        frm.set_value('supported_payment_methods', payment_methods.join(', '));
    }
}); 