/**
 * MFA Frontend Integration
 * Universal Workshop ERP - Arabic/English Support
 */

frappe.ui.form.on('User', {
    refresh: function(frm) {
        if (frm.doc.name !== frappe.session.user && !frappe.user.has_role('System Manager')) {
            return;
        }
        
        frm.trigger('setup_mfa_buttons');
        frm.trigger('show_mfa_status');
    },
    
    setup_mfa_buttons: function(frm) {
        frm.add_custom_button(__('MFA Settings'), function() {
            frm.trigger('open_mfa_dialog');
        }, __('Security'));
    },
    
    show_mfa_status: function(frm) {
        frappe.call({
            method: 'universal_workshop.user_management.mfa_manager.get_mfa_status',
            callback: function(r) {
                if (r.message && r.message.success) {
                    const status = r.message;
                    let indicator = status.enabled ? 'green' : 'orange';
                    let status_text = status.enabled ? __('Enabled') : __('Not Set');
                    
                    frm.dashboard.add_indicator(__('MFA Status: {0}', [status_text]), indicator);
                }
            }
        });
    },
    
    open_mfa_dialog: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Multi-Factor Authentication Settings'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'mfa_status'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'mfa_method',
                    label: __('MFA Method'),
                    options: 'TOTP\nSMS\nWhatsApp\nEmail',
                    default: 'TOTP'
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'enable_mfa_btn',
                    label: __('Enable MFA')
                },
                {
                    fieldtype: 'Button', 
                    fieldname: 'disable_mfa_btn',
                    label: __('Disable MFA')
                }
            ],
            primary_action_label: __('Close'),
            primary_action: function() {
                dialog.hide();
            }
        });
        
        // Load MFA status
        frappe.call({
            method: 'universal_workshop.user_management.mfa_manager.get_mfa_status',
            callback: function(r) {
                if (r.message && r.message.success) {
                    const status = r.message;
                    let status_html = status.enabled ? 
                        '<div class="alert alert-success">MFA Enabled</div>' :
                        '<div class="alert alert-warning">MFA Not Enabled</div>';
                    
                    dialog.set_value('mfa_status', status_html);
                }
            }
        });
        
        dialog.show();
    }
});
