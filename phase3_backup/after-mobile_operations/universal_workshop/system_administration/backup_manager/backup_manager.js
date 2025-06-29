// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Backup Manager', {
    refresh: function (frm) {
        // Setup Arabic RTL support
        frm.trigger('setup_arabic_fields');

        // Setup custom buttons based on status
        frm.trigger('setup_custom_buttons');

        // Setup real-time status updates
        frm.trigger('setup_status_monitoring');
    },

    setup_arabic_fields: function (frm) {
        // Arabic RTL field handling
        const arabic_fields = [
            'backup_name_ar', 'description_ar', 'backup_log', 'error_log'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply RTL layout if Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.page.clear_menu();
        frm.page.clear_actions_menu();

        if (frm.doc.name) {
            // Manual Backup Button
            if (frm.doc.backup_type === 'Manual' && ['Pending', 'Failed'].includes(frm.doc.status)) {
                frm.add_custom_button(__('Start Backup'), function () {
                    frm.trigger('start_manual_backup');
                }, __('Actions'));
            }

            // Download Backup Button
            if (frm.doc.status === 'Completed' && frm.doc.file_path) {
                frm.add_custom_button(__('Download Backup'), function () {
                    frm.trigger('download_backup');
                }, __('Actions'));
            }

            // Verify Backup Button
            if (frm.doc.status === 'Completed' && !frm.doc.verification_status) {
                frm.add_custom_button(__('Verify Backup'), function () {
                    frm.trigger('verify_backup');
                }, __('Actions'));
            }

            // Delete Backup Button
            if (['Completed', 'Failed'].includes(frm.doc.status)) {
                frm.add_custom_button(__('Delete Backup'), function () {
                    frm.trigger('delete_backup');
                }, __('Actions'));
            }
        }
    },

    setup_status_monitoring: function (frm) {
        // Real-time status monitoring for in-progress backups
        if (frm.doc.status === 'In Progress') {
            frm.backup_monitor_interval = setInterval(function () {
                frm.reload_doc();
            }, 5000); // Check every 5 seconds
        } else {
            // Clear any existing intervals
            if (frm.backup_monitor_interval) {
                clearInterval(frm.backup_monitor_interval);
                frm.backup_monitor_interval = null;
            }
        }
    },

    start_manual_backup: function (frm) {
        frappe.confirm(__('Are you sure you want to start this backup?'), function () {
            frappe.call({
                method: 'create_backup',
                doc: frm.doc,
                btn: $('.primary-action'),
                callback: function (r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.msgprint({
                                title: __('Backup Started'),
                                message: r.message.message,
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __('Backup Failed'),
                                message: r.message.message,
                                indicator: 'red'
                            });
                        }
                    }
                }
            });
        });
    },

    download_backup: function (frm) {
        if (!frm.doc.file_path) {
            frappe.msgprint(__('No backup file available for download'));
            return;
        }

        // Create download link
        const filename = frm.doc.file_path.split('/').pop();
        const download_url = `/api/method/frappe.utils.file_manager.download_file?file_path=${encodeURIComponent(frm.doc.file_path)}&filename=${encodeURIComponent(filename)}`;

        window.open(download_url, '_blank');
    },

    verify_backup: function (frm) {
        frappe.call({
            method: 'verify_backup',
            doc: frm.doc,
            btn: $('.primary-action'),
            callback: function (r) {
                if (r.message) {
                    const result = r.message;
                    let message = __('Verification completed') + ':\n\n';

                    Object.keys(result).forEach(key => {
                        if (key !== 'overall_status') {
                            const check = result[key];
                            message += `${key}: ${check.status}\n`;
                        }
                    });

                    frappe.msgprint({
                        title: __('Backup Verification'),
                        message: message,
                        indicator: result.overall_status === 'Passed' ? 'green' : 'red'
                    });

                    frm.reload_doc();
                }
            }
        });
    },

    delete_backup: function (frm) {
        frappe.confirm(__('Are you sure you want to delete this backup? This action cannot be undone.'), function () {
            frappe.call({
                method: 'delete_backup',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('Backup Deleted'),
                            message: r.message.message,
                            indicator: 'green'
                        });
                        frappe.set_route('List', 'Backup Manager');
                    } else {
                        frappe.msgprint({
                            title: __('Deletion Failed'),
                            message: r.message.message,
                            indicator: 'red'
                        });
                    }
                }
            });
        });
    },

    // Field event handlers
    backup_type: function (frm) {
        // Show/hide fields based on backup type
        frm.toggle_display('scheduled_time', frm.doc.backup_type === 'Scheduled');
        frm.toggle_display('frequency', frm.doc.backup_type === 'Scheduled');
        frm.toggle_display('cron_expression', frm.doc.backup_type === 'Scheduled' && frm.doc.frequency === 'Custom');
    },

    frequency: function (frm) {
        // Show/hide cron expression field
        frm.toggle_display('cron_expression', frm.doc.frequency === 'Custom');
    },

    enable_encryption: function (frm) {
        // Show/hide encryption fields
        frm.toggle_display('encryption_password', frm.doc.enable_encryption);
    },

    cloud_upload: function (frm) {
        // Show/hide cloud upload fields
        frm.toggle_display(['cloud_provider', 'cloud_access_key', 'cloud_secret_key', 'cloud_bucket'], frm.doc.cloud_upload);
    },

    onload: function (frm) {
        // Set field visibility on load
        frm.trigger('backup_type');
        frm.trigger('frequency');
        frm.trigger('enable_encryption');
        frm.trigger('cloud_upload');
    }
});
