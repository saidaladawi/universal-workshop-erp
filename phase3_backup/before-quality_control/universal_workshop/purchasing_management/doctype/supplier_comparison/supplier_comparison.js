// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Comparison', {
    refresh: function (frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_currency_formatting');

        if (frm.doc.docstatus === 1 && frm.doc.status === 'Supplier Selected') {
            frm.add_custom_button(__('Create Purchase Order'), function () {
                frm.trigger('create_purchase_order');
            });
        }
    },

    setup_custom_buttons: function (frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Load Quotations'), function () {
                frm.trigger('load_supplier_quotations');
            });

            frm.add_custom_button(__('Comparison Analytics'), function () {
                frm.trigger('show_comparison_analytics');
            });

            frm.add_custom_button(__('Send RFQ'), function () {
                frm.trigger('send_rfq_to_suppliers');
            });
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        if (frappe.boot.lang === 'ar') {
            ['title_ar', 'notes_ar'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                }
            });

            // Apply RTL to form layout
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_currency_formatting: function (frm) {
        // Format currency fields for OMR (3 decimal places)
        if (frm.doc.currency === 'OMR') {
            frm.set_currency_labels(['total_amount'], 'OMR', 3);
        }
    },

    material_request: function (frm) {
        if (frm.doc.material_request) {
            frm.trigger('populate_items_from_material_request');
        }
    },

    populate_items_from_material_request: function (frm) {
        if (!frm.doc.material_request) return;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Material Request Item',
                filters: {
                    parent: frm.doc.material_request
                },
                fields: ['item_code', 'item_name', 'description', 'qty', 'uom', 'warehouse']
            },
            callback: function (r) {
                if (r.message) {
                    frm.clear_table('comparison_items');

                    r.message.forEach(function (item) {
                        let row = frm.add_child('comparison_items');
                        row.item_code = item.item_code;
                        row.item_name = item.item_name;
                        row.description = item.description;
                        row.qty = item.qty;
                        row.uom = item.uom;
                        row.warehouse = item.warehouse;
                    });

                    frm.refresh_field('comparison_items');
                }
            }
        });
    },

    load_supplier_quotations: function (frm) {
        if (!frm.doc.material_request) {
            frappe.msgprint(__('Please select a Material Request first'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.purchasing_management.doctype.supplier_comparison.supplier_comparison.get_supplier_quotations',
            args: {
                material_request: frm.doc.material_request
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frm.clear_table('supplier_quotations');

                    r.message.forEach(function (quote) {
                        let row = frm.add_child('supplier_quotations');
                        row.supplier = quote.supplier;
                        row.supplier_name = quote.supplier_name;
                        row.item_code = quote.item_code;
                        row.qty = quote.qty;
                        row.quoted_rate = quote.quoted_rate;
                        row.amount = quote.amount;
                        row.quotation_date = quote.quotation_date;
                        row.lead_time_days = quote.lead_time_days;
                        row.warehouse = quote.warehouse;
                        row.currency = frm.doc.currency || 'OMR';
                    });

                    frm.refresh_field('supplier_quotations');
                    frappe.msgprint(__('Loaded {0} supplier quotations').format(r.message.length));
                } else {
                    frappe.msgprint(__('No supplier quotations found for this Material Request'));
                }
            }
        });
    },

    show_comparison_analytics: function (frm) {
        if (!frm.doc.name) return;

        frappe.call({
            method: 'universal_workshop.purchasing_management.doctype.supplier_comparison.supplier_comparison.get_supplier_comparison_analytics',
            args: {
                comparison_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    let analytics = r.message;
                    let html = frm.trigger('format_analytics_html', analytics);

                    frappe.msgprint({
                        title: __('Comparison Analytics'),
                        message: html,
                        indicator: 'blue'
                    });
                }
            }
        });
    },

    format_analytics_html: function (frm, analytics) {
        let html = `
            <div class="comparison-analytics">
                <h4>${__('Supplier Comparison Analytics')}</h4>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>${__('Total Suppliers')}: </strong>${analytics.total_suppliers}</p>
                        <p><strong>${__('Total Items')}: </strong>${analytics.total_items}</p>
                    </div>
                </div>
        `;

        if (analytics.price_analysis && Object.keys(analytics.price_analysis).length > 0) {
            html += '<h5>' + __('Price Analysis') + '</h5>';
            html += '<table class="table table-bordered">';
            html += '<thead><tr><th>' + __('Item') + '</th><th>' + __('Min Price') + '</th><th>' + __('Max Price') + '</th><th>' + __('Avg Price') + '</th><th>' + __('Variance') + '</th></tr></thead>';
            html += '<tbody>';

            Object.keys(analytics.price_analysis).forEach(function (item_code) {
                let analysis = analytics.price_analysis[item_code];
                html += `<tr>
                    <td>${item_code}</td>
                    <td>${format_currency(analysis.min_price, frm.doc.currency)}</td>
                    <td>${format_currency(analysis.max_price, frm.doc.currency)}</td>
                    <td>${format_currency(analysis.avg_price, frm.doc.currency)}</td>
                    <td>${format_currency(analysis.price_variance, frm.doc.currency)}</td>
                </tr>`;
            });

            html += '</tbody></table>';
        }

        html += '</div>';
        return html;
    },

    send_rfq_to_suppliers: function (frm) {
        let suppliers = [];
        if (frm.doc.supplier_quotations) {
            suppliers = [...new Set(frm.doc.supplier_quotations.map(q => q.supplier))];
        }

        if (suppliers.length === 0) {
            frappe.msgprint(__('No suppliers found in quotations'));
            return;
        }

        frappe.prompt([
            {
                fieldtype: 'MultiSelect',
                label: __('Select Suppliers'),
                fieldname: 'suppliers',
                options: suppliers.join('\n'),
                reqd: 1
            },
            {
                fieldtype: 'Text',
                label: __('Message'),
                fieldname: 'message',
                default: __('Please provide your quotation for the following items')
            },
            {
                fieldtype: 'Text',
                label: __('Message (Arabic)'),
                fieldname: 'message_ar',
                default: 'يرجى تقديم عرض أسعار للعناصر التالية'
            }
        ], function (values) {
            frappe.call({
                method: 'universal_workshop.purchasing_management.api.send_rfq_to_suppliers',
                args: {
                    comparison_name: frm.doc.name,
                    suppliers: values.suppliers.split(','),
                    message: values.message,
                    message_ar: values.message_ar
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('RFQ sent to selected suppliers'));
                        frm.set_value('status', 'Request Sent');
                    }
                }
            });
        }, __('Send RFQ'));
    },

    create_purchase_order: function (frm) {
        if (!frm.doc.selected_supplier) {
            frappe.msgprint(__('Please select a supplier first'));
            return;
        }

        frappe.confirm(__('Create Purchase Order for selected supplier?'), function () {
            frappe.call({
                method: 'universal_workshop.purchasing_management.doctype.supplier_comparison.supplier_comparison.create_purchase_order',
                args: {
                    comparison_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Purchase Order {0} created successfully').format(r.message));
                        frm.reload_doc();
                    }
                }
            });
        });
    }
});

// Child table events
frappe.ui.form.on('Supplier Comparison Quotation', {
    quoted_rate: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.quoted_rate && row.qty) {
            frappe.model.set_value(cdt, cdn, 'amount', row.quoted_rate * row.qty);
        }
        frm.trigger('calculate_totals');
    },

    qty: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.quoted_rate && row.qty) {
            frappe.model.set_value(cdt, cdn, 'amount', row.quoted_rate * row.qty);
        }
        frm.trigger('calculate_totals');
    },

    is_selected: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_selected) {
            // Uncheck other selections for the same item
            frm.doc.supplier_quotations.forEach(function (quote) {
                if (quote.item_code === row.item_code && quote.name !== row.name) {
                    frappe.model.set_value('Supplier Comparison Quotation', quote.name, 'is_selected', 0);
                }
            });

            frm.set_value('selected_supplier', row.supplier);
        }
        frm.trigger('calculate_totals');
    },

    supplier: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.supplier) {
            frappe.db.get_value('Supplier', row.supplier, 'supplier_name', function (r) {
                if (r.supplier_name) {
                    frappe.model.set_value(cdt, cdn, 'supplier_name', r.supplier_name);
                }
            });
        }
    },

    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, 'item_name', function (r) {
                if (r.item_name) {
                    frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
                }
            });
        }
    }
});

frappe.ui.form.on('Supplier Comparison Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.db.get_value('Item', row.item_code, ['item_name', 'description'], function (r) {
                if (r.item_name) {
                    frappe.model.set_value(cdt, cdn, 'item_name', r.item_name);
                }
                if (r.description) {
                    frappe.model.set_value(cdt, cdn, 'description', r.description);
                }
            });
        }
    }
});

// Calculate totals
frappe.ui.form.on('Supplier Comparison', {
    calculate_totals: function (frm) {
        let total = 0;
        if (frm.doc.supplier_quotations) {
            frm.doc.supplier_quotations.forEach(function (quotation) {
                if (quotation.is_selected && quotation.amount) {
                    total += flt(quotation.amount);
                }
            });
        }
        frm.set_value('total_amount', total);
    }
}); 