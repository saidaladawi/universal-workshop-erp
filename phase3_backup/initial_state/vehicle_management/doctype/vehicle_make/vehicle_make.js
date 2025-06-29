// -*- coding: utf-8 -*-
// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle Make', {
    refresh: function (frm) {
        // Add custom buttons for API operations
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Update from API'), function () {
                update_make_from_api(frm);
            }, __('API Actions'));
        }

        // Add bulk sync button for users with permissions
        if (frappe.user.has_role(['Workshop Manager', 'System Manager'])) {
            frm.add_custom_button(__('Sync All Makes'), function () {
                sync_all_makes_from_api();
            }, __('API Actions'));

            frm.add_custom_button(__('API Status'), function () {
                show_api_sync_status();
            }, __('API Actions'));
        }

        // Setup Arabic RTL support
        setup_arabic_fields(frm);

        // Show API source indicator
        show_api_source_indicator(frm);
    },

    make_name: function (frm) {
        // Auto-suggest Arabic translation when English name is entered
        if (frm.doc.make_name && !frm.doc.make_name_ar && !frm.doc.is_manual_entry) {
            suggest_arabic_translation(frm);
        }
    },

    is_manual_entry: function (frm) {
        // Toggle API-related fields based on manual entry setting
        toggle_api_fields(frm);
    }
});

function setup_arabic_fields(frm) {
    // Set RTL direction for Arabic fields
    if (frm.fields_dict.make_name_ar) {
        frm.fields_dict.make_name_ar.$input.attr('dir', 'rtl');
        frm.fields_dict.make_name_ar.$input.addClass('arabic-text');
    }
}

function show_api_source_indicator(frm) {
    // Show visual indicator for API source
    if (frm.doc.api_source && frm.doc.api_source !== 'Local Database') {
        frm.dashboard.add_indicator(__('API Source: {0}', [frm.doc.api_source]), 'blue');

        if (frm.doc.last_api_update) {
            const last_update = moment(frm.doc.last_api_update).fromNow();
            frm.dashboard.add_indicator(__('Last Updated: {0}', [last_update]), 'grey');
        }
    } else if (frm.doc.is_manual_entry) {
        frm.dashboard.add_indicator(__('Manual Entry'), 'orange');
    }
}

function toggle_api_fields(frm) {
    // Hide/show API fields based on manual entry setting
    const api_fields = ['api_source', 'last_api_update', 'api_id'];

    api_fields.forEach(field => {
        frm.toggle_display(field, !frm.doc.is_manual_entry);
    });
}

function update_make_from_api(frm) {
    frappe.call({
        method: 'universal_workshop.vehicle_management.api.get_vehicle_makes_from_api',
        args: {
            force_refresh: true
        },
        callback: function (r) {
            if (r.message) {
                // Find current make in API results
                const api_make = r.message.find(make =>
                    make.make_name.toLowerCase() === frm.doc.make_name.toLowerCase()
                );

                if (api_make && api_make.source !== 'Local Database') {
                    // Update fields with API data
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, {
                        'make_name_ar': api_make.make_name_ar,
                        'api_source': api_make.source,
                        'last_api_update': frappe.datetime.now_datetime()
                    });

                    frappe.show_alert({
                        message: __('Updated from {0}', [api_make.source]),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint(__('No API data found for this make'));
                }
            }
        },
        error: function () {
            frappe.msgprint(__('Failed to fetch data from API'));
        }
    });
}

function sync_all_makes_from_api() {
    frappe.confirm(
        __('This will sync all vehicle makes from external APIs. Continue?'),
        function () {
            frappe.call({
                method: 'universal_workshop.vehicle_management.api.sync_vehicle_data_from_apis',
                callback: function (r) {
                    if (r.message) {
                        if (r.message.status === 'success') {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });

                            // Refresh current form if it was updated
                            if (r.message.updated_count > 0) {
                                frm.reload_doc();
                            }
                        } else {
                            frappe.msgprint(__('Sync failed: {0}', [r.message.message]));
                        }
                    }
                },
                error: function () {
                    frappe.msgprint(__('Failed to sync data from APIs'));
                }
            });
        }
    );
}

function show_api_sync_status() {
    frappe.call({
        method: 'universal_workshop.vehicle_management.api.get_api_sync_status',
        callback: function (r) {
            if (r.message && !r.message.error) {
                const status = r.message;

                let message = __('API Sync Status') + ':<br><br>';
                message += __('Total Makes: {0}', [status.total_makes]) + '<br>';
                message += __('API Sourced: {0}', [status.api_makes_count]) + '<br>';
                message += __('Manual Entries: {0}', [status.manual_makes_count]) + '<br><br>';

                if (status.last_sync && status.last_sync.last_sync_time) {
                    const last_sync = moment(status.last_sync.last_sync_time).fromNow();
                    message += __('Last Sync: {0}', [last_sync]) + '<br>';
                    message += __('Status: {0}', [status.last_sync.status]);
                } else {
                    message += __('Status: Never synced');
                }

                frappe.msgprint({
                    title: __('API Sync Status'),
                    message: message,
                    indicator: 'blue'
                });
            } else {
                frappe.msgprint(__('Failed to get sync status'));
            }
        }
    });
}

function suggest_arabic_translation(frm) {
    // Arabic translations for common vehicle makes
    const translation_map = {
        'Toyota': 'تويوتا',
        'Honda': 'هوندا',
        'Ford': 'فورد',
        'Chevrolet': 'شيفروليه',
        'BMW': 'بي إم دبليو',
        'Mercedes-Benz': 'مرسيدس بنز',
        'Mercedes': 'مرسيدس',
        'Audi': 'أودي',
        'Lexus': 'لكزس',
        'Infiniti': 'إنفينيتي',
        'Cadillac': 'كاديلاك',
        'Volkswagen': 'فولكس فاجن',
        'Porsche': 'بورشه',
        'Jaguar': 'جاجوار',
        'Land Rover': 'لاند روفر',
        'Range Rover': 'رينج روفر',
        'Bentley': 'بنتلي',
        'Rolls-Royce': 'رولز رويس',
        'Ferrari': 'فيراري',
        'Lamborghini': 'لامبورغيني',
        'Maserati': 'مازيراتي',
        'Alfa Romeo': 'ألفا روميو',
        'Fiat': 'فيات',
        'Peugeot': 'بيجو',
        'Renault': 'رينو',
        'Citroen': 'ستروين',
        'Volvo': 'فولفو',
        'Saab': 'ساب',
        'Subaru': 'سوبارو',
        'Mazda': 'مازدا',
        'Mitsubishi': 'ميتسوبيشي',
        'Suzuki': 'سوزوكي',
        'Isuzu': 'إيسوزو',
        'Daihatsu': 'دايهاتسو',
        'Hyundai': 'هيونداي',
        'Kia': 'كيا',
        'Daewoo': 'دايو',
        'SsangYong': 'سانغ يونغ'
    };

    const arabic_name = translation_map[frm.doc.make_name];
    if (arabic_name) {
        frm.set_value('make_name_ar', arabic_name);
    }
}

// Custom search for make selection in other forms
frappe.ui.form.on('Vehicle', {
    make: function (frm) {
        // Auto-populate model options when make is selected
        if (frm.doc.make) {
            get_models_for_make(frm, frm.doc.make);
        }
    }
});

function get_models_for_make(frm, make_name) {
    frappe.call({
        method: 'universal_workshop.vehicle_management.api.get_vehicle_models_from_api',
        args: {
            make_name: make_name,
            year: frm.doc.year || null
        },
        callback: function (r) {
            if (r.message) {
                // Update model field options
                const model_options = r.message.map(model => model.model_name);
                frm.set_df_property('model', 'options', model_options.join('\n'));
                frm.refresh_field('model');

                // Show API source info
                if (r.message.length > 0 && r.message[0].source !== 'Local Database') {
                    frappe.show_alert({
                        message: __('Models loaded from {0}', [r.message[0].source]),
                        indicator: 'blue'
                    });
                }
            }
        }
    });
} 