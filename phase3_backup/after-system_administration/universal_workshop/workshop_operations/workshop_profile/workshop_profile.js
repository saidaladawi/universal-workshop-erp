// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Workshop Profile', {
    refresh: function (frm) {
        // Setup Arabic form enhancements
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_rtl_layout');
        frm.trigger('setup_oman_specific_features');

        // Setup logo optimization features
        frm.trigger('update_logo_preview');
        frm.trigger('update_optimization_status');

        // Add custom buttons
        if (frm.doc.status === 'Active') {
            frm.add_custom_button(__('View Services'), function () {
                frappe.route_options = { "workshop": frm.doc.name };
                frappe.set_route("List", "Workshop Service");
            });

            frm.add_custom_button(__('Create Service Order'), function () {
                frappe.new_doc("Service Order", { "workshop": frm.doc.name });
            });
        }

        // Add custom buttons for existing records
        frm.add_custom_buttons();
    },

    setup_arabic_fields: function (frm) {
        // Auto-direction for Arabic fields
        const arabic_fields = [
            'workshop_name_ar', 'owner_name_ar', 'address_ar',
            'specialization', 'equipment_list'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });
    },

    setup_rtl_layout: function (frm) {
        // RTL layout for Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');

            // Adjust form layout for RTL
            frm.layout.wrapper.find('.form-column').each(function () {
                $(this).css('text-align', 'right');
            });
        }
    },

    setup_oman_specific_features: function (frm) {
        // Auto-format phone numbers for Oman
        ['phone_number', 'mobile_number'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.on('blur', function () {
                    let phone = $(this).val();
                    if (phone && !phone.startsWith('+968')) {
                        if (phone.length === 8 && /^\d+$/.test(phone)) {
                            $(this).val('+968 ' + phone);
                        }
                    }
                });
            }
        });

        // Auto-format business license
        if (frm.fields_dict.business_license) {
            frm.fields_dict.business_license.$input.attr('maxlength', 7);
            frm.fields_dict.business_license.$input.attr('pattern', '[0-9]{7}');
        }

        // Auto-format VAT number
        if (frm.fields_dict.vat_number) {
            frm.fields_dict.vat_number.$input.on('input', function () {
                let value = $(this).val().toUpperCase();
                if (value && !value.startsWith('OM')) {
                    if (/^\d/.test(value)) {
                        $(this).val('OM' + value);
                    }
                }
            });
        }
    },

    workshop_name: function (frm) {
        // Auto-suggest Arabic transliteration
        if (frm.doc.workshop_name && !frm.doc.workshop_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },

    suggest_arabic_name: function (frm) {
        // This could integrate with a transliteration service
        // For now, just prompt the user
        if (frm.doc.workshop_name && !frm.doc.workshop_name_ar) {
            frappe.show_alert({
                message: __('Please provide Arabic name for the workshop'),
                indicator: 'orange'
            });
        }
    },

    owner_name: function (frm) {
        // Auto-suggest Arabic owner name
        if (frm.doc.owner_name && !frm.doc.owner_name_ar) {
            frappe.show_alert({
                message: __('Please provide Arabic name for the owner'),
                indicator: 'orange'
            });
        }
    },

    governorate: function (frm) {
        // Auto-suggest related settings based on governorate
        if (frm.doc.governorate) {
            frm.trigger('setup_governorate_defaults');
        }
    },

    setup_governorate_defaults: function (frm) {
        // Set default working hours based on governorate
        if (!frm.doc.working_hours_start) {
            frm.set_value('working_hours_start', '08:00:00');
        }
        if (!frm.doc.working_hours_end) {
            frm.set_value('working_hours_end', '17:00:00');
        }
        if (!frm.doc.weekend_days) {
            frm.set_value('weekend_days', 'Friday-Saturday');
        }
    },

    validate: function (frm) {
        // Client-side validation for Arabic content
        if (frm.doc.workshop_name_ar) {
            // Check if Arabic name contains Arabic characters
            const arabicRegex = /[\u0600-\u06FF]/;
            if (!arabicRegex.test(frm.doc.workshop_name_ar)) {
                frappe.msgprint({
                    title: __('Validation Error'),
                    message: __('Arabic workshop name must contain Arabic characters'),
                    indicator: 'red'
                });
                frappe.validated = false;
            }
        }

        // Validate working hours
        if (frm.doc.working_hours_start && frm.doc.working_hours_end) {
            if (frm.doc.working_hours_start >= frm.doc.working_hours_end) {
                frappe.msgprint({
                    title: __('Validation Error'),
                    message: __('Working hours end time must be after start time'),
                    indicator: 'red'
                });
                frappe.validated = false;
            }
        }
    },

    add_custom_buttons: function (frm) {
        if (frm.doc.name && !frm.is_new()) {
            // Add button to preview branding
            frm.add_custom_button(__('Preview Branding'), function () {
                frm.trigger('preview_branding');
            }, __('Actions'));

            // Add button to select theme
            frm.add_custom_button(__('Select Theme'), function () {
                frm.trigger('show_theme_selector');
            }, __('Actions'));

            // Add button to reset branding
            frm.add_custom_button(__('Reset Branding'), function () {
                frm.trigger('reset_branding');
            }, __('Actions'));

            // Add button to export branding settings
            frm.add_custom_button(__('Export Branding'), function () {
                frm.trigger('export_branding');
            }, __('Actions'));

            // Add button to apply system-wide
            frm.add_custom_button(__('Apply System-wide'), function () {
                frm.trigger('apply_system_wide_branding');
            }, __('Actions'));
        }
    },

    show_theme_selector: function (frm) {
        // Show theme selector dialog
        if (window.workshop_theme_manager) {
            window.workshop_theme_manager.show_theme_selector();
        } else {
            frappe.msgprint(__('Theme manager not available. Please refresh the page.'));
        }
    },

    workshop_logo: function (frm) {
        // Auto-optimize logo when uploaded
        if (frm.doc.workshop_logo && !frm.doc.__islocal) {
            frm.trigger('auto_optimize_logo');
        }
        frm.trigger('update_logo_preview');
        frm.trigger('update_optimization_status');
    },

    optimize_logo_button: function (frm) {
        // Manual logo optimization trigger
        if (frm.doc.workshop_logo) {
            frm.trigger('optimize_logo_manual');
        } else {
            frappe.msgprint(__('Please upload a logo first'));
        }
    },

    auto_optimize_logo: function (frm) {
        // Automatically optimize logo after upload
        if (!frm.doc.workshop_logo) return;

        frappe.show_alert({
            message: __('Optimizing logo...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'universal_workshop.utils.image_optimizer.optimize_workshop_logo',
            args: {
                workshop_profile_name: frm.doc.name,
                file_url: frm.doc.workshop_logo,
                generate_variants: true
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('handle_optimization_success', r.message);
                }
            },
            error: function (xhr) {
                frm.trigger('handle_optimization_error', xhr);
            }
        });
    },

    optimize_logo_manual: function (frm) {
        // Manual logo optimization with user confirmation
        frappe.confirm(
            __('This will optimize your logo and generate multiple size variants. Continue?'),
            function () {
                // Show progress dialog
                const progress_dialog = new frappe.ui.Dialog({
                    title: __('Optimizing Logo'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'progress_html',
                            options: `
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="sr-only">Loading...</span>
                                    </div>
                                    <p class="mt-3">${__('Processing logo optimization...')}</p>
                                    <p class="text-muted">${__('This may take a few moments')}</p>
                                </div>
                            `
                        }
                    ],
                    size: 'small'
                });
                progress_dialog.show();

                frappe.call({
                    method: 'universal_workshop.utils.image_optimizer.optimize_workshop_logo',
                    args: {
                        workshop_profile_name: frm.doc.name,
                        file_url: frm.doc.workshop_logo,
                        generate_variants: true
                    },
                    callback: function (r) {
                        progress_dialog.hide();
                        if (r.message) {
                            frm.trigger('handle_optimization_success', r.message);
                        }
                    },
                    error: function (xhr) {
                        progress_dialog.hide();
                        frm.trigger('handle_optimization_error', xhr);
                    }
                });
            }
        );
    },

    handle_optimization_success: function (frm, results) {
        // Handle successful logo optimization
        console.log('Logo optimization results:', results);

        // Update form with variant URLs
        if (results.variants) {
            Object.keys(results.variants).forEach(variant => {
                const field_name = `logo_${variant}`;
                if (frm.fields_dict[field_name]) {
                    frm.set_value(field_name, results.variants[variant].file_url);
                }
            });
        }

        // Update optimization data
        frm.set_value('logo_optimization_data', JSON.stringify(results));

        // Update status display
        frm.trigger('update_optimization_status');

        // Refresh branding if needed
        if (window.refresh_workshop_branding) {
            window.refresh_workshop_branding();
        }

        frappe.show_alert({
            message: __('Logo optimized successfully! Generated {0} variants with {1}% size reduction.',
                [Object.keys(results.variants || {}).length, Math.round(results.compression_ratio || 0)]),
            indicator: 'green'
        });
    },

    handle_optimization_error: function (frm, xhr) {
        // Handle optimization errors
        console.error('Logo optimization error:', xhr);

        frappe.msgprint({
            title: __('Optimization Failed'),
            message: __('Failed to optimize logo. Please check the file format and size.'),
            indicator: 'red'
        });
    },

    update_logo_preview: function (frm) {
        // Update logo preview display
        if (frm.fields_dict.logo_preview) {
            let preview_html = '';

            if (frm.doc.workshop_logo) {
                preview_html = `
                    <div class="logo-preview-container" style="text-align: center; padding: 15px;">
                        <img src="${frm.doc.workshop_logo}" 
                             alt="Workshop Logo" 
                             style="max-width: 200px; max-height: 100px; border: 1px solid #ddd; border-radius: 4px;">
                        <p class="text-muted mt-2">${__('Current Logo')}</p>
                    </div>
                `;
            } else {
                preview_html = `
                    <div class="logo-preview-placeholder" style="text-align: center; padding: 15px;">
                        <div style="border: 2px dashed #ddd; padding: 30px; border-radius: 4px;">
                            <i class="fa fa-image" style="font-size: 48px; color: #ccc;"></i>
                            <p class="text-muted mt-2">${__('No logo uploaded')}</p>
                        </div>
                    </div>
                `;
            }

            frm.fields_dict.logo_preview.$wrapper.html(preview_html);
        }
    },

    update_optimization_status: function (frm) {
        // Update optimization status display
        if (frm.fields_dict.logo_optimization_status) {
            let status_html = '';

            if (frm.doc.logo_optimization_data) {
                try {
                    const data = JSON.parse(frm.doc.logo_optimization_data);
                    const variant_count = Object.keys(data.variants || {}).length;
                    const compression = Math.round(data.compression_ratio || 0);
                    const is_vector = data.is_vector || false;

                    status_html = `
                        <div class="optimization-status" style="padding: 10px;">
                            <div class="alert alert-success" style="margin: 0;">
                                <h6><i class="fa fa-check-circle"></i> ${__('Logo Optimized')}</h6>
                                <ul class="mb-0">
                                    <li>${__('Generated {0} size variants', [variant_count])}</li>
                                    ${!is_vector ? `<li>${__('Size reduction: {0}%', [compression])}</li>` : ''}
                                    <li>${__('Format: {0}', [is_vector ? 'SVG (Vector)' : 'Raster'])}</li>
                                    <li>${__('Original size: {0}', [data.original_size === 'vector' ? 'Vector' : `${data.original_size[0]}x${data.original_size[1]}px`])}</li>
                                </ul>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    ${__('Variants: thumbnail, small, medium, large, print, favicon')}
                                </small>
                            </div>
                        </div>
                    `;
                } catch (e) {
                    status_html = `
                        <div class="alert alert-warning" style="margin: 0;">
                            <i class="fa fa-exclamation-triangle"></i> ${__('Invalid optimization data')}
                        </div>
                    `;
                }
            } else if (frm.doc.workshop_logo) {
                status_html = `
                    <div class="optimization-status" style="padding: 10px;">
                        <div class="alert alert-info" style="margin: 0;">
                            <h6><i class="fa fa-info-circle"></i> ${__('Logo Not Optimized')}</h6>
                            <p class="mb-2">${__('Click "Optimize Logo" to generate size variants and improve performance.')}</p>
                            <button class="btn btn-sm btn-primary" onclick="cur_frm.trigger('optimize_logo_manual')">
                                <i class="fa fa-magic"></i> ${__('Optimize Now')}
                            </button>
                        </div>
                    </div>
                `;
            } else {
                status_html = `
                    <div class="alert alert-secondary" style="margin: 0;">
                        <i class="fa fa-upload"></i> ${__('Upload a logo to enable optimization')}
                    </div>
                `;
            }

            frm.fields_dict.logo_optimization_status.$wrapper.html(status_html);
        }
    },

    cleanup_old_logos: function (frm) {
        // Clean up old logo variants
        if (!frm.doc.name) return;

        frappe.confirm(
            __('This will delete all old logo variants. Continue?'),
            function () {
                frappe.call({
                    method: 'universal_workshop.utils.image_optimizer.cleanup_logo_variants',
                    args: {
                        workshop_profile_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                        }
                    }
                });
            }
        );
    },

    theme_preference: function (frm) {
        if (frm.doc.theme_preference === 'Dark') {
            frm.set_value('dark_mode_enabled', 1);
        } else if (frm.doc.theme_preference === 'Light') {
            frm.set_value('dark_mode_enabled', 0);
        }

        // Apply theme immediately if theme manager is available
        if (window.workshop_theme_manager && frm.doc.theme_preference) {
            const theme_map = {
                'Light': 'classic',
                'Dark': 'classic', // Will be handled by dark mode
                'Classic': 'classic',
                'Automotive': 'automotive',
                'Luxury': 'luxury'
            };

            const theme_name = theme_map[frm.doc.theme_preference] || 'classic';
            window.workshop_theme_manager.apply_theme(theme_name, false);
        }

        frm.trigger('apply_form_branding');
    }
});

// Utility functions for Arabic support
function convert_to_arabic_numerals(englishNum) {
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return englishNum.toString().replace(/[0-9]/g, function (w) {
        return arabicNumbers[+w];
    });
}

function format_oman_phone(phone) {
    // Remove all non-digits
    const digits = phone.replace(/\D/g, '');

    // If it's 8 digits, add +968
    if (digits.length === 8) {
        return '+968 ' + digits;
    }

    // If it starts with 968, format it
    if (digits.length === 11 && digits.startsWith('968')) {
        return '+968 ' + digits.substring(3);
    }

    return phone;
}

// Auto-format numbers for Arabic locale
frappe.ready(() => {
    if (frappe.boot.lang === 'ar') {
        // Apply Arabic numerals to currency and number fields
        $(document).on('refresh', function () {
            $('.currency, .number').each(function () {
                let value = $(this).text();
                if (value && !isNaN(value)) {
                    $(this).text(convert_to_arabic_numerals(value));
                }
            });
        });
    }
}); 