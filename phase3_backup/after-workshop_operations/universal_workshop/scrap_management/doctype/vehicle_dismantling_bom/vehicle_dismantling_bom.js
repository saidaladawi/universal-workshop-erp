// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle Dismantling BOM', {
    refresh: function (frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('calculate_totals');
        frm.trigger('setup_field_dependencies');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'bom_name_ar', 'vehicle_make_ar', 'vehicle_model_ar',
            'engine_type_ar', 'description_ar', 'notes_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal) {
            // Create Work Order Template button
            frm.add_custom_button(__('Create Work Order Template'), function () {
                frm.trigger('create_work_order_template');
            }, __('Actions'));

            // Generate Barcode Labels button
            frm.add_custom_button(__('Generate Barcode Labels'), function () {
                frm.trigger('generate_barcode_labels');
            }, __('Actions'));

            // ROI Projection button
            frm.add_custom_button(__('ROI Projection'), function () {
                frm.trigger('show_roi_projection');
            }, __('Reports'));

            // Parts by Priority button
            frm.add_custom_button(__('Parts by Priority'), function () {
                frm.trigger('show_parts_by_priority');
            }, __('Reports'));
        }
    },

    setup_field_dependencies: function (frm) {
        // Auto-generate BOM name when vehicle details change
        ['vehicle_make', 'vehicle_model', 'year_from', 'year_to'].forEach(field => {
            frm.fields_dict[field].$input.on('change', function () {
                if (frm.doc.vehicle_make && frm.doc.vehicle_model && frm.doc.year_from) {
                    frm.trigger('suggest_bom_name');
                }
            });
        });
    },

    suggest_bom_name: function (frm) {
        if (!frm.doc.bom_name && frm.doc.vehicle_make && frm.doc.vehicle_model) {
            const year_range = frm.doc.year_to ?
                `${frm.doc.year_from}-${frm.doc.year_to}` :
                frm.doc.year_from;
            const suggested_name = `${frm.doc.vehicle_make} ${frm.doc.vehicle_model} (${year_range}) Dismantling BOM`;
            frm.set_value('bom_name', suggested_name);
        }
    },

    calculate_totals: function (frm) {
        frm.trigger('calculate_operations_totals');
        frm.trigger('calculate_parts_totals');
        frm.trigger('calculate_financial_totals');
    },

    calculate_operations_totals: function (frm) {
        if (!frm.doc.dismantling_operations) return;

        let total_time = 0;
        let hazmat_operations = 0;

        frm.doc.dismantling_operations.forEach(operation => {
            total_time += parseFloat(operation.estimated_time || 0);
            if (operation.generates_hazmat) {
                hazmat_operations++;
            }
        });

        frm.set_value('total_estimated_time', total_time);
        frm.set_value('total_operations', frm.doc.dismantling_operations.length);
        frm.set_value('hazmat_operations_count', hazmat_operations);
    },

    calculate_parts_totals: function (frm) {
        if (!frm.doc.extractable_parts) return;

        let total_value = 0;
        let total_refurbishment = 0;
        let total_extraction_time = 0;
        let high_value_parts = 0;
        let high_priority_parts = 0;

        frm.doc.extractable_parts.forEach(part => {
            const value = parseFloat(part.estimated_value || 0);
            const refurb = parseFloat(part.estimated_refurbishment_cost || 0);
            const time = parseFloat(part.estimated_extraction_time || 0);

            total_value += value;
            total_refurbishment += refurb;
            total_extraction_time += time;

            if (value > 100) high_value_parts++; // 100 OMR threshold
            if (part.extraction_priority === 'High') high_priority_parts++;
        });

        frm.set_value('total_estimated_value', total_value);
        frm.set_value('total_refurbishment_cost', total_refurbishment);
        frm.set_value('total_extraction_time', total_extraction_time);
        frm.set_value('total_extractable_parts', frm.doc.extractable_parts.length);
        frm.set_value('high_value_parts_count', high_value_parts);
        frm.set_value('high_priority_parts_count', high_priority_parts);
    },

    calculate_financial_totals: function (frm) {
        const total_value = parseFloat(frm.doc.total_estimated_value || 0);
        const total_cost = parseFloat(frm.doc.total_refurbishment_cost || 0);
        const estimated_profit = total_value - total_cost;
        const profit_margin = total_value > 0 ? (estimated_profit / total_value) * 100 : 0;

        frm.set_value('estimated_profit', estimated_profit);
        frm.set_value('profit_margin_percent', profit_margin);
    },

    create_work_order_template: function (frm) {
        frappe.confirm(__('Create Work Order template from this BOM?'), function () {
            frappe.call({
                method: 'create_work_order_template',
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Work Order template created: {0}', [r.message]));
                        frappe.set_route('Form', 'Work Order', r.message);
                    }
                }
            });
        });
    },

    generate_barcode_labels: function (frm) {
        if (!frm.doc.extractable_parts || frm.doc.extractable_parts.length === 0) {
            frappe.msgprint(__('No extractable parts defined'));
            return;
        }

        frappe.call({
            method: 'generate_barcode_labels',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.refresh_field('extractable_parts');
                    frm.trigger('show_barcode_labels_dialog', r.message);
                }
            }
        });
    },

    show_barcode_labels_dialog: function (frm, labels) {
        const dialog = new frappe.ui.Dialog({
            title: __('Generated Barcode Labels'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'labels_html'
                }
            ]
        });

        let html = '<div class="barcode-labels">';
        labels.forEach(label => {
            html += `
                <div class="barcode-item" style="border: 1px solid #ccc; padding: 10px; margin: 5px; display: inline-block; width: 200px;">
                    <div style="text-align: center; font-weight: bold;">${label.barcode}</div>
                    <div>${label.part_name}</div>
                    ${label.part_name_ar ? `<div dir="rtl">${label.part_name_ar}</div>` : ''}
                    <div>Category: ${label.category}</div>
                    <div>Est. Value: ${label.estimated_value} OMR</div>
                </div>
            `;
        });
        html += '</div>';

        dialog.fields_dict.labels_html.$wrapper.html(html);
        dialog.show();
    },

    show_roi_projection: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('ROI Projection'),
            fields: [
                {
                    fieldtype: 'Currency',
                    fieldname: 'acquisition_cost',
                    label: __('Vehicle Acquisition Cost (OMR)'),
                    default: 0
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'projection_results'
                }
            ],
            primary_action_label: __('Calculate'),
            primary_action: function () {
                const acquisition_cost = dialog.get_value('acquisition_cost');

                frappe.call({
                    method: 'get_roi_projection',
                    doc: frm.doc,
                    args: {
                        acquisition_cost: acquisition_cost
                    },
                    callback: function (r) {
                        if (r.message) {
                            frm.trigger('display_roi_results', [dialog, r.message]);
                        }
                    }
                });
            }
        });

        dialog.show();
    },

    display_roi_results: function (frm, dialog, results) {
        const html = `
            <div class="roi-results">
                <h4>${__('ROI Projection Results')}</h4>
                <table class="table table-bordered">
                    <tr><td><strong>${__('Acquisition Cost')}</strong></td><td>${results.acquisition_cost.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Extraction Cost')}</strong></td><td>${results.extraction_cost.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Refurbishment Cost')}</strong></td><td>${results.refurbishment_cost.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Disposal Cost')}</strong></td><td>${results.disposal_cost.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Total Costs')}</strong></td><td>${results.total_costs.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Estimated Revenue')}</strong></td><td>${results.estimated_revenue.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('Net Profit')}</strong></td><td style="color: ${results.net_profit >= 0 ? 'green' : 'red'}">${results.net_profit.toFixed(3)} OMR</td></tr>
                    <tr><td><strong>${__('ROI Percentage')}</strong></td><td style="color: ${results.roi_percentage >= 0 ? 'green' : 'red'}">${results.roi_percentage.toFixed(1)}%</td></tr>
                    <tr><td><strong>${__('Break-even Acquisition Cost')}</strong></td><td>${results.break_even_acquisition_cost.toFixed(3)} OMR</td></tr>
                </table>
            </div>
        `;

        dialog.fields_dict.projection_results.$wrapper.html(html);
    },

    show_parts_by_priority: function (frm) {
        frappe.call({
            method: 'get_parts_by_priority',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.trigger('display_parts_by_priority', r.message);
                }
            }
        });
    },

    display_parts_by_priority: function (frm, priority_data) {
        const dialog = new frappe.ui.Dialog({
            title: __('Parts by Priority'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'priority_html'
                }
            ]
        });

        let html = '<div class="parts-by-priority">';

        ['high', 'medium', 'low'].forEach(priority => {
            const parts = priority_data[priority] || [];
            const priority_label = priority.charAt(0).toUpperCase() + priority.slice(1);

            html += `<h4>${__('Priority')}: ${__(priority_label)} (${parts.length})</h4>`;

            if (parts.length > 0) {
                html += '<table class="table table-striped table-bordered">';
                html += `<thead><tr>
                    <th>${__('Part Name')}</th>
                    <th>${__('Arabic Name')}</th>
                    <th>${__('Category')}</th>
                    <th>${__('Est. Value')}</th>
                    <th>${__('Extraction Time')}</th>
                </tr></thead><tbody>`;

                parts.forEach(part => {
                    html += `<tr>
                        <td>${part.part_name}</td>
                        <td dir="rtl">${part.part_name_ar || ''}</td>
                        <td>${part.category}</td>
                        <td>${part.estimated_value} OMR</td>
                        <td>${part.extraction_time} min</td>
                    </tr>`;
                });

                html += '</tbody></table>';
            } else {
                html += `<p>${__('No parts with {0} priority', [priority_label.toLowerCase()])}</p>`;
            }

            html += '<hr>';
        });

        html += '</div>';

        dialog.fields_dict.priority_html.$wrapper.html(html);
        dialog.show();
    },

    // Validation functions
    year_from: function (frm) {
        frm.trigger('validate_year_range');
        frm.trigger('suggest_bom_name');
    },

    year_to: function (frm) {
        frm.trigger('validate_year_range');
        frm.trigger('suggest_bom_name');
    },

    validate_year_range: function (frm) {
        if (frm.doc.year_from && frm.doc.year_to) {
            if (parseInt(frm.doc.year_from) > parseInt(frm.doc.year_to)) {
                frappe.msgprint(__('Year From cannot be greater than Year To'));
                frm.set_value('year_to', frm.doc.year_from);
            }
        }
    },

    vehicle_make: function (frm) {
        frm.trigger('suggest_bom_name');
    },

    vehicle_model: function (frm) {
        frm.trigger('suggest_bom_name');
    }
});

// Operations table events
frappe.ui.form.on('Vehicle Dismantling Operation', {
    estimated_time: function (frm) {
        frm.trigger('calculate_operations_totals');
    },

    generates_hazmat: function (frm) {
        frm.trigger('calculate_operations_totals');
    },

    dismantling_operations_add: function (frm) {
        frm.trigger('calculate_operations_totals');
    },

    dismantling_operations_remove: function (frm) {
        frm.trigger('calculate_operations_totals');
    }
});

// Extractable parts table events
frappe.ui.form.on('Vehicle Dismantling Extractable Part', {
    estimated_value: function (frm) {
        frm.trigger('calculate_parts_totals');
        frm.trigger('calculate_financial_totals');
    },

    estimated_refurbishment_cost: function (frm) {
        frm.trigger('calculate_parts_totals');
        frm.trigger('calculate_financial_totals');
    },

    estimated_extraction_time: function (frm) {
        frm.trigger('calculate_parts_totals');
    },

    extraction_priority: function (frm) {
        frm.trigger('calculate_parts_totals');
    },

    extractable_parts_add: function (frm) {
        frm.trigger('calculate_parts_totals');
        frm.trigger('calculate_financial_totals');
    },

    extractable_parts_remove: function (frm) {
        frm.trigger('calculate_parts_totals');
        frm.trigger('calculate_financial_totals');
    }
}); 