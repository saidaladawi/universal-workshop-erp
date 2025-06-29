// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Report Export Utility', {
    refresh: function (frm) {
        // Setup form enhancements
        frm.trigger('setup_mobile_responsive_ui');
        frm.trigger('setup_arabic_support');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_dashboard_indicators');
    },

    setup_mobile_responsive_ui: function (frm) {
        // Add mobile-responsive CSS classes
        if (frm.is_new()) {
            frm.set_value('mobile_friendly', 1);
            frm.set_value('responsive_layout', 1);
            frm.set_value('touch_optimized', 1);
        }

        // Detect mobile device and adjust UI
        if (frappe.utils.is_mobile()) {
            frm.page.wrapper.addClass('mobile-export-form');

            // Mobile-specific styles
            $('<style>')
                .prop('type', 'text/css')
                .html(`
                    .mobile-export-form .form-section {
                        margin-bottom: 15px;
                    }
                    .mobile-export-form .control-input {
                        font-size: 16px;
                        padding: 12px;
                    }
                    .mobile-export-form .btn {
                        min-height: 44px;
                        font-size: 16px;
                    }
                    .mobile-export-form .section-head {
                        background: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 10px;
                    }
                `)
                .appendTo('head');
        }
    },

    setup_arabic_support: function (frm) {
        // Configure RTL layout if enabled
        if (frm.doc.rtl_layout) {
            frm.page.main.addClass('rtl-layout');

            // Set RTL direction for Arabic fields
            ['export_name_ar', 'email_recipients', 'access_permissions'].forEach(function (field) {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$wrapper.attr('dir', 'rtl');
                    if (frm.fields_dict[field].$input) {
                        frm.fields_dict[field].$input.attr('dir', 'rtl');
                    }
                }
            });
        }

        // Auto-suggest Arabic name when English name is entered
        if (frm.doc.export_name && !frm.doc.export_name_ar && frappe.boot.lang === 'ar') {
            frm.set_value('export_name_ar', 'تصدير - ' + frm.doc.export_name);
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.name && frm.doc.docstatus !== 2) {
            // Generate Export button
            frm.add_custom_button(__('Generate Export'), function () {
                frm.trigger('generate_export');
            }, __('Actions')).addClass('btn-primary');

            // Quick Export buttons for different formats
            frm.add_custom_button(__('Quick PDF'), function () {
                frm.trigger('quick_export', ['PDF']);
            }, __('Quick Export'));

            frm.add_custom_button(__('Quick Excel'), function () {
                frm.trigger('quick_export', ['Excel (XLSX)']);
            }, __('Quick Export'));

            frm.add_custom_button(__('Quick CSV'), function () {
                frm.trigger('quick_export', ['CSV']);
            }, __('Quick Export'));

            // Download button if export is completed
            if (frm.doc.status === 'Completed' && frm.doc.download_url) {
                frm.add_custom_button(__('Download'), function () {
                    frm.trigger('download_export');
                }, __('File')).addClass('btn-success');
            }

            // Preview button for HTML exports
            if (frm.doc.status === 'Completed' && frm.doc.output_format === 'HTML') {
                frm.add_custom_button(__('Preview'), function () {
                    frm.trigger('preview_export');
                }, __('File'));
            }

            // Test Export Configuration button
            if (frm.doc.source_report) {
                frm.add_custom_button(__('Test Configuration'), function () {
                    frm.trigger('test_export_configuration');
                }, __('Actions'));
            }

            // Email Test button
            if (frm.doc.email_delivery && frm.doc.email_recipients) {
                frm.add_custom_button(__('Send Test Email'), function () {
                    frm.trigger('send_test_email');
                }, __('Actions'));
            }
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on configuration
        frm.trigger('toggle_format_specific_fields');
        frm.trigger('toggle_mobile_fields');
        frm.trigger('toggle_arabic_fields');
        frm.trigger('toggle_delivery_fields');
    },

    update_dashboard_indicators: function (frm) {
        if (frm.doc.status) {
            let color = frm.doc.status === 'Completed' ? 'green' :
                frm.doc.status === 'Failed' ? 'red' :
                    frm.doc.status === 'Generating' ? 'orange' : 'blue';
            frm.dashboard.add_indicator(__('Status'), color, frm.doc.status);
        }

        if (frm.doc.file_size) {
            frm.dashboard.add_indicator(__('File Size'), 'blue', frm.doc.file_size);
        }

        if (frm.doc.export_rows) {
            frm.dashboard.add_indicator(__('Rows'), 'green', frm.doc.export_rows.toString());
        }

        if (frm.doc.download_count) {
            frm.dashboard.add_indicator(__('Downloads'), 'orange', frm.doc.download_count.toString());
        }
    },

    // Field event handlers
    export_name: function (frm) {
        if (frm.doc.export_name && !frm.doc.export_name_ar && frm.doc.rtl_layout) {
            frm.set_value('export_name_ar', 'تصدير - ' + frm.doc.export_name);
        }
    },

    source_report: function (frm) {
        if (frm.doc.source_report) {
            frm.trigger('load_report_configuration');
        }
    },

    output_format: function (frm) {
        frm.trigger('toggle_format_specific_fields');
        frm.trigger('update_format_recommendations');
    },

    rtl_layout: function (frm) {
        frm.trigger('setup_arabic_support');
        frm.trigger('toggle_arabic_fields');
    },

    mobile_friendly: function (frm) {
        frm.trigger('toggle_mobile_fields');
        frm.trigger('update_mobile_recommendations');
    },

    email_delivery: function (frm) {
        frm.trigger('toggle_delivery_fields');
    },

    cloud_storage: function (frm) {
        frm.trigger('toggle_delivery_fields');
    },

    // Custom trigger functions
    load_report_configuration: function (frm) {
        if (frm.doc.source_report) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Custom Report Builder',
                    name: frm.doc.source_report
                },
                callback: function (r) {
                    if (r.message) {
                        let report = r.message;

                        // Auto-fill export name if empty
                        if (!frm.doc.export_name) {
                            frm.set_value('export_name', report.report_name + ' Export');
                        }

                        // Set Arabic name if available
                        if (report.report_name_ar && !frm.doc.export_name_ar) {
                            frm.set_value('export_name_ar', 'تصدير ' + report.report_name_ar);
                        }

                        frm.trigger('update_format_recommendations');
                    }
                }
            });
        }
    },

    generate_export: function (frm) {
        if (!frm.doc.source_report) {
            frappe.msgprint(__('Please select a source report first'));
            return;
        }

        // Show progress indicator
        let progress_dialog = frappe.show_progress(__('Generating Export'), 0, __('Initializing...'));

        frappe.call({
            method: 'generate_export',
            doc: frm.doc,
            callback: function (r) {
                progress_dialog.hide();

                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Export generated successfully'),
                        indicator: 'green'
                    });

                    frm.reload_doc();

                    // Auto-download if configured
                    if (frm.doc.auto_download && r.message.download_url) {
                        setTimeout(function () {
                            frm.trigger('download_export');
                        }, 1000);
                    }
                } else {
                    frappe.msgprint({
                        title: __('Export Failed'),
                        message: r.message ? r.message.message : __('Unknown error occurred'),
                        indicator: 'red'
                    });
                }
            },
            error: function (r) {
                progress_dialog.hide();
                frappe.msgprint({
                    title: __('Export Error'),
                    message: __('Failed to generate export. Please try again.'),
                    indicator: 'red'
                });
            }
        });
    },

    quick_export: function (frm, format) {
        if (!frm.doc.source_report) {
            frappe.msgprint(__('Please select a source report first'));
            return;
        }

        // Create quick export with minimal configuration
        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.report_export_utility.report_export_utility.create_quick_export',
            args: {
                source_report: frm.doc.source_report,
                output_format: format,
                mobile_friendly: 1,
                rtl_layout: frappe.boot.lang === 'ar' ? 1 : 0
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Quick export generated successfully'),
                        indicator: 'green'
                    });

                    // Auto-download
                    if (r.message.download_url) {
                        window.open(r.message.download_url, '_blank');
                    }
                } else {
                    frappe.msgprint(__('Quick export failed: {0}', [r.message.message || 'Unknown error']));
                }
            }
        });
    },

    download_export: function (frm) {
        if (!frm.doc.download_url) {
            frappe.msgprint(__('No download URL available'));
            return;
        }

        // For mobile devices, handle download differently
        if (frappe.utils.is_mobile()) {
            // Create a temporary link for mobile download
            let link = document.createElement('a');
            link.href = frm.doc.download_url;
            link.download = frm.doc.export_name || 'export';
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            window.open(frm.doc.download_url, '_blank');
        }
    },

    preview_export: function (frm) {
        if (frm.doc.output_format !== 'HTML') {
            frappe.msgprint(__('Preview is only available for HTML exports'));
            return;
        }

        if (!frm.doc.download_url) {
            frappe.msgprint(__('No preview available'));
            return;
        }

        // Open preview in modal for mobile, new tab for desktop
        if (frappe.utils.is_mobile()) {
            let preview_dialog = new frappe.ui.Dialog({
                title: __('Export Preview'),
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'preview_content'
                    }
                ]
            });

            // Load content via iframe
            let iframe = `<iframe src="${frm.doc.download_url}" width="100%" height="500px" frameborder="0"></iframe>`;
            preview_dialog.fields_dict.preview_content.$wrapper.html(iframe);
            preview_dialog.show();
        } else {
            window.open(frm.doc.download_url, '_blank');
        }
    },

    test_export_configuration: function (frm) {
        frappe.call({
            method: 'universal_workshop.analytics_reporting.doctype.report_export_utility.report_export_utility.create_quick_export',
            args: {
                source_report: frm.doc.source_report,
                output_format: 'HTML',
                mobile_friendly: frm.doc.mobile_friendly,
                rtl_layout: frm.doc.rtl_layout,
                include_filters: frm.doc.include_filters,
                include_charts: frm.doc.include_charts,
                include_summary: frm.doc.include_summary
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Test export successful'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint(__('Test export failed: {0}', [r.message.message || 'Configuration error']));
                }
            }
        });
    },

    send_test_email: function (frm) {
        if (!frm.doc.email_recipients) {
            frappe.msgprint(__('Please enter email recipients first'));
            return;
        }

        let test_message = `
            <p>${__("This is a test email for export delivery configuration.")}</p>
            <p><strong>${__("Export Name")}:</strong> ${frm.doc.export_name}</p>
            <p><strong>${__("Output Format")}:</strong> ${frm.doc.output_format}</p>
            <p><strong>${__("Configuration Test")}:</strong> ${__("Successful")}</p>
        `;

        frappe.call({
            method: 'frappe.core.doctype.communication.email.make',
            args: {
                recipients: frm.doc.email_recipients,
                subject: __('Export Configuration Test - {0}', [frm.doc.export_name]),
                content: test_message,
                send_email: 1
            },
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Test email sent successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    toggle_format_specific_fields: function (frm) {
        let is_pdf = frm.doc.output_format === 'PDF';

        frm.toggle_display(['page_orientation', 'paper_size', 'margin_settings'], is_pdf);

        // Show different options based on format
        if (frm.doc.output_format) {
            frm.trigger('update_format_recommendations');
        }
    },

    toggle_mobile_fields: function (frm) {
        let show_mobile = frm.doc.mobile_friendly;

        frm.toggle_display(['responsive_layout', 'touch_optimized', 'compress_images',
            'optimize_fonts', 'reduce_file_size'], show_mobile);
    },

    toggle_arabic_fields: function (frm) {
        let show_arabic = frm.doc.rtl_layout;

        frm.toggle_display(['arabic_fonts', 'bilingual_export', 'arabic_numbers',
            'date_format_arabic', 'currency_format_arabic'], show_arabic);
    },

    toggle_delivery_fields: function (frm) {
        frm.toggle_display(['email_recipients'], frm.doc.email_delivery);
        frm.toggle_display(['storage_path'], frm.doc.cloud_storage);
    },

    update_format_recommendations: function (frm) {
        if (!frm.doc.output_format) return;

        let recommendations = {
            'PDF': __('Best for printing and official documents. Supports Arabic RTL layout.'),
            'Excel (XLSX)': __('Ideal for data analysis and spreadsheet manipulation.'),
            'CSV': __('Universal format for data exchange and import/export.'),
            'HTML': __('Perfect for web viewing and mobile devices.'),
            'JSON': __('Suitable for API integration and data processing.'),
            'XML': __('Structured format for system integration.')
        };

        let recommendation = recommendations[frm.doc.output_format];
        if (recommendation) {
            frm.set_df_property('output_format', 'description', recommendation);
        }
    },

    update_mobile_recommendations: function (frm) {
        if (frm.doc.mobile_friendly) {
            // Auto-enable mobile optimizations
            if (!frm.doc.responsive_layout) frm.set_value('responsive_layout', 1);
            if (!frm.doc.touch_optimized) frm.set_value('touch_optimized', 1);
            if (!frm.doc.compress_images) frm.set_value('compress_images', 1);

            // Show mobile-specific recommendations
            frappe.show_alert({
                message: __('Mobile optimizations enabled. File size will be reduced for faster downloads.'),
                indicator: 'blue'
            });
        }
    }
});

// Utility functions for mobile detection and responsive behavior
frappe.utils.is_mobile = function () {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

// Enhanced progress dialog for mobile
frappe.show_progress = function (title, percent, message) {
    if (!frappe.progress_dialog) {
        frappe.progress_dialog = new frappe.ui.Dialog({
            title: title,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'progress_area'
                }
            ]
        });
    }

    let progress_html = `
        <div class="progress" style="height: 20px; margin: 20px 0;">
            <div class="progress-bar" role="progressbar" style="width: ${percent}%;" 
                 aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100">
                ${percent}%
            </div>
        </div>
        <p class="text-muted">${message}</p>
    `;

    frappe.progress_dialog.fields_dict.progress_area.$wrapper.html(progress_html);
    frappe.progress_dialog.show();

    return {
        hide: function () {
            if (frappe.progress_dialog) {
                frappe.progress_dialog.hide();
            }
        },
        update: function (new_percent, new_message) {
            if (frappe.progress_dialog) {
                let new_html = `
                    <div class="progress" style="height: 20px; margin: 20px 0;">
                        <div class="progress-bar" role="progressbar" style="width: ${new_percent}%;" 
                             aria-valuenow="${new_percent}" aria-valuemin="0" aria-valuemax="100">
                            ${new_percent}%
                        </div>
                    </div>
                    <p class="text-muted">${new_message}</p>
                `;
                frappe.progress_dialog.fields_dict.progress_area.$wrapper.html(new_html);
            }
        }
    };
};

// Mobile-friendly alert system
frappe.show_mobile_alert = function (message, indicator) {
    if (frappe.utils.is_mobile()) {
        // Use native mobile toast for better UX
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Universal Workshop ERP', {
                body: message,
                icon: '/assets/universal_workshop/images/logo.png'
            });
        } else {
            frappe.show_alert({ message: message, indicator: indicator });
        }
    } else {
        frappe.show_alert({ message: message, indicator: indicator });
    }
}; 