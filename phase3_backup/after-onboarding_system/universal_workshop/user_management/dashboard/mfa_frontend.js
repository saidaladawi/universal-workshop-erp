/**
 * Multi-Factor Authentication (MFA) Frontend Integration
 * Universal Workshop ERP - Arabic/English Support
 * 
 * Provides frontend interface for MFA setup, verification, and management
 * with full RTL and Arabic localization support.
 */

// =============================================================================
// User Form Integration
// =============================================================================

frappe.ui.form.on('User', {
    refresh: function (frm) {
        if (frm.doc.name !== frappe.session.user && !frappe.user.has_role('System Manager')) {
            return; // Only allow self-service or admin access
        }

        frm.trigger('setup_mfa_buttons');
        frm.trigger('show_mfa_status');
    },

    setup_mfa_buttons: function (frm) {
        // Clear existing custom buttons
        frm.custom_buttons = {};

        // Add MFA management buttons
        frm.add_custom_button(__('MFA Settings'), function () {
            frm.trigger('open_mfa_dialog');
        }, __('Security'));

        frm.add_custom_button(__('Security Dashboard'), function () {
            frappe.set_route('security-dashboard');
        }, __('Security'));

        // Add admin-only buttons
        if (frappe.user.has_role('System Manager')) {
            frm.add_custom_button(__('Admin MFA Controls'), function () {
                frm.trigger('open_admin_mfa_dialog');
            }, __('Security'));
        }
    },

    show_mfa_status: function (frm) {
        // Get current MFA status
        frappe.call({
            method: 'universal_workshop.user_management.mfa_manager.get_mfa_status',
            callback: function (r) {
                if (r.message && r.message.success) {
                    const status = r.message;
                    let indicator = 'orange';
                    let status_text = __('Not Set');

                    if (status.enabled) {
                        indicator = 'green';
                        status_text = __('Enabled') + ` (${status.method.toUpperCase()})`;
                    }

                    frm.dashboard.add_indicator(__('MFA Status: {0}', [status_text]), indicator);

                    if (status.enabled && status.backup_codes_remaining !== undefined) {
                        frm.dashboard.add_indicator(
                            __('Backup Codes: {0}', [status.backup_codes_remaining]),
                            status.backup_codes_remaining > 5 ? 'blue' : 'red'
                        );
                    }
                }
            }
        });
    },

    open_mfa_dialog: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Multi-Factor Authentication Settings'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'mfa_status',
                    label: __('Current Status')
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'mfa_method',
                    label: __('MFA Method'),
                    options: [
                        { value: 'totp', label: __('Authenticator App (TOTP)') },
                        { value: 'sms', label: __('SMS') },
                        { value: 'whatsapp', label: __('WhatsApp') },
                        { value: 'email', label: __('Email') }
                    ],
                    default: 'totp',
                    description: __('Choose your preferred multi-factor authentication method')
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'enable_mfa_btn',
                    label: __('Enable MFA'),
                    depends_on: 'eval:!doc.mfa_enabled'
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'disable_mfa_btn',
                    label: __('Disable MFA'),
                    depends_on: 'eval:doc.mfa_enabled'
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'generate_backup_codes_btn',
                    label: __('Generate New Backup Codes'),
                    depends_on: 'eval:doc.mfa_enabled'
                },
                {
                    fieldtype: 'Button',
                    fieldname: 'test_mfa_btn',
                    label: __('Test MFA'),
                    depends_on: 'eval:doc.mfa_enabled'
                }
            ],
            size: 'large',
            primary_action_label: __('Close'),
            primary_action: function () {
                dialog.hide();
            }
        });

        // Load current MFA status
        dialog.set_value('mfa_status', '<div class="text-muted">' + __('Loading...') + '</div>');

        frappe.call({
            method: 'universal_workshop.user_management.mfa_manager.get_mfa_status',
            callback: function (r) {
                if (r.message && r.message.success) {
                    const status = r.message;
                    let status_html = '';

                    if (status.enabled) {
                        status_html = `
                            <div class="alert alert-success">
                                <strong>${__('MFA Enabled')}</strong><br>
                                ${__('Method')}: ${status.method.toUpperCase()}<br>
                                ${__('Setup Date')}: ${status.setup_date}<br>
                                ${__('Backup Codes Remaining')}: ${status.backup_codes_remaining || 0}
                            </div>
                        `;
                        dialog.doc.mfa_enabled = true;
                    } else {
                        status_html = `
                            <div class="alert alert-warning">
                                <strong>${__('MFA Not Enabled')}</strong><br>
                                ${__('Your account is not protected by multi-factor authentication.')}
                            </div>
                        `;
                        dialog.doc.mfa_enabled = false;
                    }

                    dialog.set_value('mfa_status', status_html);
                    dialog.refresh();
                }
            }
        });

        // Button event handlers
        dialog.$wrapper.on('click', '[data-fieldname="enable_mfa_btn"]', function () {
            frm.trigger('enable_mfa_workflow', dialog);
        });

        dialog.$wrapper.on('click', '[data-fieldname="disable_mfa_btn"]', function () {
            frm.trigger('disable_mfa_workflow', dialog);
        });

        dialog.$wrapper.on('click', '[data-fieldname="generate_backup_codes_btn"]', function () {
            frm.trigger('generate_backup_codes_workflow', dialog);
        });

        dialog.$wrapper.on('click', '[data-fieldname="test_mfa_btn"]', function () {
            frm.trigger('test_mfa_workflow', dialog);
        });

        dialog.show();
    },

    enable_mfa_workflow: function (frm, dialog) {
        const method = dialog.get_value('mfa_method');

        frappe.confirm(
            __('Are you sure you want to enable MFA using {0}?', [method.toUpperCase()]),
            function () {
                frappe.call({
                    method: 'universal_workshop.user_management.mfa_manager.enable_mfa',
                    args: { mfa_method: method },
                    btn: dialog.$wrapper.find('[data-fieldname="enable_mfa_btn"]'),
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frm.trigger('show_mfa_setup_result', r.message, dialog);
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                message: r.message ? r.message.error : __('Failed to enable MFA'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        );
    },

    show_mfa_setup_result: function (frm, result, dialog) {
        dialog.hide();

        const setup_dialog = new frappe.ui.Dialog({
            title: __('MFA Setup Complete'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'setup_instructions'
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Code',
                    fieldname: 'backup_codes',
                    label: __('Backup Codes'),
                    description: __('Save these codes in a safe place. You can use them to access your account if you lose your device.'),
                    read_only: 1
                }
            ],
            size: 'large',
            primary_action_label: __('I have saved the backup codes'),
            primary_action: function () {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('MFA has been enabled successfully'),
                    indicator: 'green'
                });
                setup_dialog.hide();
                frm.reload_doc();
            }
        });

        let instructions_html = '';

        if (result.method === 'totp') {
            instructions_html = `
                <div class="alert alert-info">
                    <h5>${__('Setup Your Authenticator App')}</h5>
                    <p>${__('Scan the QR code below with your authenticator app (Google Authenticator, Authy, etc.):')}</p>
                    <div class="text-center mb-3">
                        <img src="data:image/png;base64,${result.qr_code}" style="max-width: 200px;">
                    </div>
                    <p><strong>${__('Manual Entry Key')}:</strong> <code>${result.secret}</code></p>
                    <p class="text-muted">${__('If you cannot scan the QR code, enter the key above manually in your authenticator app.')}</p>
                </div>
            `;
        } else {
            instructions_html = `
                <div class="alert alert-success">
                    <h5>${__('MFA Setup Complete')}</h5>
                    <p>${__('You will receive verification codes via {0} when logging in.', [result.method.toUpperCase()])}</p>
                </div>
            `;
        }

        setup_dialog.set_value('setup_instructions', instructions_html);
        setup_dialog.set_value('backup_codes', result.backup_codes.join('\n'));
        setup_dialog.show();
    }
});

// =============================================================================
// Login Form Integration
// =============================================================================

$(document).ready(function () {
    // Enhance login form with MFA support
    if (window.location.pathname === '/login') {
        setTimeout(function () {
            enhanceLoginFormWithMFA();
        }, 1000);
    }
});

function enhanceLoginFormWithMFA() {
    const login_form = $('.login-content form');
    if (login_form.length === 0) return;

    // Add MFA code field (initially hidden)
    const mfa_field = $(`
        <div class="form-group mfa-field" style="display: none;">
            <input type="text" 
                   class="form-control" 
                   id="mfa_code" 
                   name="mfa_code"
                   placeholder="${__('Enter verification code')}"
                   maxlength="10"
                   autocomplete="one-time-code">
            <div class="help-text text-muted">
                ${__('Enter the code from your authenticator app or received via SMS/WhatsApp')}
            </div>
            <div class="mt-2">
                <a href="#" class="text-muted small" id="send-otp-link">${__('Send new code')}</a>
                <span class="mx-2">|</span>
                <a href="#" class="text-muted small" id="use-backup-code-link">${__('Use backup code')}</a>
            </div>
        </div>
    `);

    // Insert MFA field before the login button
    const login_btn = login_form.find('[type="submit"]');
    mfa_field.insertBefore(login_btn.parent());
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Arabic/RTL support for MFA dialogs
 */
function apply_rtl_to_mfa_dialogs() {
    if (frappe.boot.lang === 'ar') {
        $('.modal-dialog').addClass('rtl-layout');
        $('.form-control').attr('dir', 'auto');
    }
}

// Apply RTL when document is ready
$(document).ready(function () {
    apply_rtl_to_mfa_dialogs();
}); 