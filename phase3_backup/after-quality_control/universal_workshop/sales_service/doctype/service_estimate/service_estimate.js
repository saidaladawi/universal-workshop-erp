// Service Estimate Form JavaScript Controller
// Integrates with Parts Auto-Suggestion Engine

frappe.ui.form.on('Service Estimate', {
    refresh: function (frm) {
        // Setup form enhancements
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_parts_suggestions');

        // Show workflow buttons based on status
        if (frm.doc.status === "Pending Approval") {
            frm.add_custom_button(__('Approve'), function () {
                frm.trigger('approve_estimate');
            }, __('Actions')).addClass('btn-success');

            frm.add_custom_button(__('Reject'), function () {
                frm.trigger('reject_estimate');
            }, __('Actions')).addClass('btn-danger');
        }

        if (frm.doc.status === "Approved" && !frm.doc.converted_to_service_order) {
            frm.add_custom_button(__('Convert to Service Order'), function () {
                frm.trigger('convert_to_service_order');
            }, __('Actions')).addClass('btn-primary');
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'customer_name_ar', 'service_description_ar',
            'terms_and_conditions_ar', 'rejection_reason_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Apply Arabic styling if current language is Arabic
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_custom_buttons: function (frm) {
        // Add custom button for parts suggestions
        if (!frm.is_new()) {
            frm.add_custom_button(__('Suggest Parts'), function () {
                frm.trigger('show_parts_suggestions');
            }, __('Tools')).addClass('btn-info');
        }

        // Add button to clear suggestions
        frm.add_custom_button(__('Clear Suggestions'), function () {
            frm.trigger('clear_suggestions_display');
        }, __('Tools'));
    },

    setup_parts_suggestions: function (frm) {
        // Create suggestions display area
        if (!frm.suggestions_wrapper) {
            frm.suggestions_wrapper = $('<div class="parts-suggestions-wrapper" style="margin: 15px 0; display: none;"></div>');
            frm.fields_dict.parts_items.wrapper.after(frm.suggestions_wrapper);
        }
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            // Fetch customer name and Arabic name
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.customer
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('customer_name', r.message.customer_name);
                        if (r.message.customer_name_ar) {
                            frm.set_value('customer_name_ar', r.message.customer_name_ar);
                        }
                    }
                }
            });

            // Get customer vehicles
            frm.trigger('load_customer_vehicles');
        }
    },

    load_customer_vehicles: function (frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.service_estimate.service_estimate.get_customer_vehicles',
                args: {
                    customer: frm.doc.customer
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        // Update vehicle field options
                        frm.set_query('vehicle', function () {
                            return {
                                filters: {
                                    customer: frm.doc.customer
                                }
                            };
                        });
                    }
                }
            });
        }
    },

    vehicle: function (frm) {
        if (frm.doc.vehicle) {
            // Fetch vehicle details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Vehicle',
                    name: frm.doc.vehicle
                },
                callback: function (r) {
                    if (r.message) {
                        const vehicle = r.message;
                        const vehicle_details = `${vehicle.make} ${vehicle.model} ${vehicle.year} - ${vehicle.license_plate}`;
                        frm.set_value('vehicle_details', vehicle_details);
                    }
                }
            });

            // Auto-trigger parts suggestions if service type is selected
            if (frm.doc.service_type) {
                frm.trigger('auto_suggest_parts');
            }
        }
    },

    service_type: function (frm) {
        // Auto-trigger parts suggestions when service type changes
        if (frm.doc.service_type && frm.doc.vehicle) {
            frm.trigger('auto_suggest_parts');
        }
    },

    service_description: function (frm) {
        // Auto-trigger parts suggestions when description changes
        if (frm.doc.service_description && frm.doc.vehicle) {
            frm.trigger('auto_suggest_parts');
        }
    },

    auto_suggest_parts: function (frm) {
        // Automatically get parts suggestions based on form data
        if (frm.doc.service_type || frm.doc.service_description) {
            setTimeout(() => {
                frm.trigger('get_parts_suggestions');
            }, 1000); // Delay to avoid too many API calls
        }
    },

    show_parts_suggestions: function (frm) {
        // Manually trigger parts suggestions display
        frm.trigger('get_parts_suggestions');
    },

    get_parts_suggestions: function (frm) {
        if (!frm.doc.customer && !frm.doc.vehicle && !frm.doc.service_type) {
            frappe.msgprint(__('Please select customer, vehicle, or service type first'));
            return;
        }

        frappe.show_alert({
            message: __('Getting parts suggestions...'),
            indicator: 'blue'
        });

        frappe.call({
            method: 'universal_workshop.sales_service.parts_auto_suggestion.get_parts_suggestions',
            args: {
                service_type: frm.doc.service_type,
                vehicle: frm.doc.vehicle,
                customer: frm.doc.customer,
                description: frm.doc.service_description,
                max_suggestions: 8
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frm.trigger('display_parts_suggestions', [r.message]);
                    frappe.show_alert({
                        message: __('Found {0} parts suggestions', [r.message.length]),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('No parts suggestions found'),
                        indicator: 'orange'
                    });
                }
            },
            error: function () {
                frappe.show_alert({
                    message: __('Error getting parts suggestions'),
                    indicator: 'red'
                });
            }
        });
    },

    display_parts_suggestions: function (frm, suggestions) {
        const wrapper = frm.suggestions_wrapper;
        wrapper.empty();

        if (!suggestions || suggestions.length === 0) {
            wrapper.hide();
            return;
        }

        // Create suggestions container
        const container = $(`
            <div class="suggestions-container">
                <div class="suggestions-header">
                    <h5><i class="fa fa-lightbulb-o"></i> ${__('Suggested Parts')}</h5>
                    <small class="text-muted">${__('Based on service type, vehicle, and history')}</small>
                </div>
                <div class="suggestions-grid"></div>
            </div>
        `);

        const grid = container.find('.suggestions-grid');

        // Create suggestion cards
        suggestions.forEach(suggestion => {
            const confidence_color = suggestion.confidence > 0.8 ? 'success' :
                suggestion.confidence > 0.6 ? 'warning' : 'info';

            const stock_indicator = suggestion.current_stock > 0 ?
                `<span class="label label-success">${__('In Stock')} (${suggestion.current_stock})</span>` :
                `<span class="label label-danger">${__('Out of Stock')}</span>`;

            const arabic_name = suggestion.item_name_ar ?
                `<div class="arabic-name" dir="rtl">${suggestion.item_name_ar}</div>` : '';

            const card = $(`
                <div class="suggestion-card" data-item-code="${suggestion.item_code}">
                    <div class="card-header">
                        <strong>${suggestion.item_name}</strong>
                        ${arabic_name}
                        <div class="confidence-badge">
                            <span class="label label-${confidence_color}">${Math.round(suggestion.confidence * 100)}% ${__('Match')}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="item-details">
                            <div><strong>${__('Code')}:</strong> ${suggestion.item_code}</div>
                            <div><strong>${__('Rate')}:</strong> ${suggestion.rate} OMR</div>
                            <div><strong>${__('Source')}:</strong> ${__(suggestion.source)}</div>
                            <div class="stock-info">${stock_indicator}</div>
                        </div>
                        <div class="card-actions">
                            <button class="btn btn-sm btn-primary add-part-btn" data-item-code="${suggestion.item_code}">
                                <i class="fa fa-plus"></i> ${__('Add to Estimate')}
                            </button>
                        </div>
                    </div>
                </div>
            `);

            grid.append(card);
        });

        // Add event handlers
        container.find('.add-part-btn').on('click', function () {
            const item_code = $(this).data('item-code');
            frm.trigger('add_suggested_part', [item_code]);
        });

        // Add styling
        container.find('.suggestions-grid').css({
            'display': 'grid',
            'grid-template-columns': 'repeat(auto-fill, minmax(300px, 1fr))',
            'gap': '15px',
            'margin-top': '10px'
        });

        container.find('.suggestion-card').css({
            'border': '1px solid #e0e6ed',
            'border-radius': '8px',
            'padding': '15px',
            'background': '#f9f9f9',
            'transition': 'all 0.3s ease'
        });

        container.find('.suggestion-card:hover').css({
            'transform': 'translateY(-2px)',
            'box-shadow': '0 4px 8px rgba(0,0,0,0.1)'
        });

        wrapper.html(container);
        wrapper.show();
    },

    add_suggested_part: function (frm, item_code) {
        frappe.call({
            method: 'universal_workshop.sales_service.parts_auto_suggestion.add_suggested_part_to_estimate',
            args: {
                estimate_id: frm.doc.name,
                part_code: item_code,
                quantity: 1
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Part added successfully'),
                        indicator: 'green'
                    });

                    // Log feedback for learning
                    frm.trigger('log_suggestion_feedback', [item_code, 'selected']);
                } else {
                    frappe.msgprint(__('Error adding part: {0}', [r.message.message]));
                }
            }
        });
    },

    log_suggestion_feedback: function (frm, item_code, action, feedback) {
        frappe.call({
            method: 'universal_workshop.sales_service.parts_auto_suggestion.log_suggestion_feedback',
            args: {
                estimate_id: frm.doc.name,
                part_code: item_code,
                action: action,
                feedback: feedback
            }
        });
    },

    clear_suggestions_display: function (frm) {
        if (frm.suggestions_wrapper) {
            frm.suggestions_wrapper.hide();
        }
    },

    approve_estimate: function (frm) {
        frappe.call({
            method: 'universal_workshop.sales_service.doctype.service_estimate.service_estimate.approve_estimate',
            args: {
                estimate_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                }
            }
        });
    },

    reject_estimate: function (frm) {
        frappe.prompt([
            {
                fieldname: 'reason',
                label: __('Rejection Reason'),
                fieldtype: 'Text',
                reqd: 1
            },
            {
                fieldname: 'reason_ar',
                label: __('Rejection Reason (Arabic)'),
                fieldtype: 'Text'
            }
        ], function (data) {
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.service_estimate.service_estimate.reject_estimate',
                args: {
                    estimate_name: frm.doc.name,
                    reason: data.reason,
                    reason_ar: data.reason_ar
                },
                callback: function (r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }, __('Reject Estimate'), __('Reject'));
    },

    convert_to_service_order: function (frm) {
        frappe.confirm(__('Convert this estimate to a service order?'), function () {
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.service_estimate.service_estimate.convert_to_service_order',
                args: {
                    estimate_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frm.reload_doc();
                        frappe.set_route('Form', 'Sales Order', r.message);
                    }
                }
            });
        });
    }
});

// Child table events for parts
frappe.ui.form.on('Service Estimate Parts', {
    part_code: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.part_code) {
            // Fetch part details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Item',
                    name: row.part_code
                },
                callback: function (r) {
                    if (r.message) {
                        const item = r.message;
                        frappe.model.set_value(cdt, cdn, 'part_name', item.item_name);
                        if (item.item_name_ar) {
                            frappe.model.set_value(cdt, cdn, 'part_name_ar', item.item_name_ar);
                        }
                        if (item.description) {
                            frappe.model.set_value(cdt, cdn, 'description', item.description);
                        }
                        if (item.standard_rate) {
                            frappe.model.set_value(cdt, cdn, 'rate', item.standard_rate);
                        }
                    }
                }
            });
        }
    },

    qty: function (frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
    },

    rate: function (frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
    }
});

function calculate_part_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.qty && row.rate) {
        const amount = flt(row.qty) * flt(row.rate);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    }
}

// Apply Arabic styling
frappe.ready(function () {
    if (frappe.boot.lang === 'ar') {
        // Add Arabic-specific CSS
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .rtl-layout .form-control { text-align: right; direction: rtl; }
                .arabic-name { font-size: 12px; color: #888; margin-top: 2px; }
                .suggestions-container { direction: ltr; }
                .suggestions-container .arabic-name { direction: rtl; text-align: right; }
            `)
            .appendTo('head');
    }
}); 