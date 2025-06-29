// Auto Reorder Rules JavaScript
// Universal Workshop ERP - Arabic-first automotive workshop management system

frappe.ui.form.on('Auto Reorder Rules', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_field_dependencies');
        frm.trigger('update_stock_status_indicator');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        if (frappe.boot.lang === 'ar') {
            ['item_name_ar', 'notes_ar'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                }
            });
        }
    },

    setup_custom_buttons: function (frm) {
        if (frm.doc.name && !frm.is_new()) {
            // Update Forecast button
            frm.add_custom_button(__('Update Forecast'), function () {
                frm.trigger('update_forecast');
            }, __('Actions'));

            // Check Reorder Status button
            frm.add_custom_button(__('Check Reorder Status'), function () {
                frm.trigger('check_reorder_status');
            }, __('Actions'));

            // Create Material Request button
            if (frm.doc.auto_create_material_request && frm.doc.enabled) {
                frm.add_custom_button(__('Create Material Request'), function () {
                    frm.trigger('create_material_request');
                }, __('Create'));
            }

            // Create Purchase Order button
            if (frm.doc.auto_create_purchase_order && frm.doc.enabled && frm.doc.preferred_supplier) {
                frm.add_custom_button(__('Create Purchase Order'), function () {
                    frm.trigger('create_purchase_order');
                }, __('Create'));
            }

            // Analytics button
            frm.add_custom_button(__('View Analytics'), function () {
                frm.trigger('view_analytics');
            }, __('Reports'));
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on forecasting method
        frm.toggle_display('smoothing_alpha', frm.doc.forecasting_method === 'Exponential Smoothing');

        // Show/hide supplier fields based on auto creation settings
        frm.toggle_reqd('preferred_supplier', frm.doc.auto_create_purchase_order);

        // Update field labels with Arabic if needed
        if (frappe.boot.lang === 'ar') {
            frm.set_df_property('reorder_level', 'description', 'مستوى إعادة الطلب - النقطة التي يجب فيها إعادة طلب المواد');
            frm.set_df_property('safety_stock', 'description', 'المخزون الآمن - كمية إضافية للحماية من النفاد');
        }
    },

    update_stock_status_indicator: function (frm) {
        if (frm.doc.current_stock !== undefined && frm.doc.reorder_level) {
            let status_color = 'green';
            let status_text = __('Normal');

            if (frm.doc.current_stock <= frm.doc.reorder_level) {
                status_color = 'red';
                status_text = __('Reorder Required');
            } else if (frm.doc.current_stock <= (frm.doc.reorder_level * 1.2)) {
                status_color = 'orange';
                status_text = __('Low Stock');
            }

            frm.dashboard.add_indicator(status_text, status_color);
        }
    },

    item_code: function (frm) {
        if (frm.doc.item_code) {
            // Fetch item details
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: { 'name': frm.doc.item_code },
                    fieldname: ['item_name', 'item_group', 'stock_uom']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('item_name', r.message.item_name);
                        frm.refresh_field('item_name');
                    }
                }
            });
        }
    },

    warehouse: function (frm) {
        if (frm.doc.item_code && frm.doc.warehouse) {
            frm.trigger('update_current_stock');
        }
    },

    forecasting_method: function (frm) {
        frm.trigger('setup_field_dependencies');

        // Update description based on method
        let descriptions = {
            'Simple Average': __('Uses historical average consumption for forecasting'),
            'Moving Average': __('Uses moving average of last 30 days'),
            'Exponential Smoothing': __('Uses exponential smoothing with configurable alpha'),
            'Linear Regression': __('Uses trend analysis for forecasting')
        };

        if (descriptions[frm.doc.forecasting_method]) {
            frm.set_df_property('forecasting_method', 'description', descriptions[frm.doc.forecasting_method]);
        }
    },

    auto_create_purchase_order: function (frm) {
        frm.trigger('setup_field_dependencies');
    },

    reorder_level: function (frm) {
        frm.trigger('validate_reorder_levels');
        frm.trigger('update_stock_status_indicator');
    },

    reorder_quantity: function (frm) {
        frm.trigger('validate_reorder_levels');
    },

    maximum_stock: function (frm) {
        frm.trigger('validate_reorder_levels');
    },

    validate_reorder_levels: function (frm) {
        if (frm.doc.maximum_stock && frm.doc.reorder_level &&
            frm.doc.maximum_stock <= frm.doc.reorder_level) {
            frappe.msgprint(__('Maximum Stock should be greater than Reorder Level'));
        }
    },

    update_current_stock: function (frm) {
        if (frm.doc.item_code && frm.doc.warehouse) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Bin',
                    filters: {
                        'item_code': frm.doc.item_code,
                        'warehouse': frm.doc.warehouse
                    },
                    fieldname: ['actual_qty', 'projected_qty']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('current_stock', r.message.actual_qty || 0);
                        frm.refresh_field('current_stock');
                        frm.trigger('update_stock_status_indicator');
                    }
                }
            });
        }
    },

    update_forecast: function (frm) {
        frappe.call({
            method: 'universal_workshop.purchasing_management.doctype.auto_reorder_rules.auto_reorder_rules.update_forecast',
            args: {
                'name': frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(__('Forecast updated successfully'));
                    frm.reload_doc();
                } else {
                    frappe.msgprint(__('Error updating forecast'));
                }
            }
        });
    },

    check_reorder_status: function (frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Auto Reorder Rules',
                name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    let doc = r.message;
                    let message = '';

                    if (doc.current_stock <= doc.reorder_level) {
                        message = __('Reorder Required: Current stock ({0}) is below reorder level ({1})',
                            [doc.current_stock, doc.reorder_level]);
                    } else {
                        let days_to_reorder = doc.average_consumption > 0 ?
                            (doc.current_stock - doc.reorder_level) / doc.average_consumption : 0;
                        message = __('Stock Status: Normal. Estimated {0} days until reorder needed',
                            [Math.round(days_to_reorder)]);
                    }

                    frappe.msgprint({
                        title: __('Reorder Status'),
                        message: message,
                        indicator: doc.current_stock <= doc.reorder_level ? 'red' : 'green'
                    });
                }
            }
        });
    }
});
