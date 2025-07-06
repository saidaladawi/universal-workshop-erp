frappe.ui.form.on('Exchange Request', {
    refresh: function (frm) {
        // Set up Arabic RTL fields
        frm.trigger('setup_arabic_fields');

        // Add custom buttons based on status
        frm.trigger('add_custom_buttons');

        // Set up field dependencies
        frm.trigger('setup_field_dependencies');

        // Auto-refresh customer data when customer changes
        if (frm.doc.customer) {
            frm.trigger('fetch_customer_data');
        }

        // Show compatibility score indicator
        frm.trigger('show_compatibility_indicator');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic text fields
        const arabic_fields = ['exchange_reason_details', 'customer_notes', 'admin_notes', 'internal_notes'];
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.attr('dir', 'auto');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });

        // Set Arabic font for better display
        frm.page.main.addClass('arabic-support');
    },

    add_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.page.clear_custom_buttons();

        if (frm.doc.docstatus === 1) {
            // Add buttons based on exchange status
            if (frm.doc.exchange_status === 'Pending Approval') {
                // Approve button
                frm.add_custom_button(__('Approve / موافقة'), function () {
                    frm.trigger('approve_request');
                }, __('Actions / الإجراءات'));

                // Reject button
                frm.add_custom_button(__('Reject / رفض'), function () {
                    frm.trigger('reject_request');
                }, __('Actions / الإجراءات'));
            }

            if (frm.doc.exchange_status === 'Approved') {
                // Process button
                frm.add_custom_button(__('Process Exchange / معالجة التبديل'), function () {
                    frm.trigger('process_exchange');
                }, __('Actions / الإجراءات'));
            }

            // Exchange preview button
            frm.add_custom_button(__('Exchange Preview / معاينة التبديل'), function () {
                frm.trigger('show_exchange_preview');
            }, __('View / عرض'));

            // Compatibility check button
            frm.add_custom_button(__('Compatibility Check / فحص التوافق'), function () {
                frm.trigger('show_compatibility_details');
            }, __('View / عرض'));

            // Related documents button
            frm.add_custom_button(__('Related Documents / المستندات المرتبطة'), function () {
                frm.trigger('show_related_documents');
            }, __('View / عرض'));
        }

        // Exchange suggestions button (always available)
        if (frm.doc.original_item_code && !frm.is_new()) {
            frm.add_custom_button(__('Item Suggestions / اقتراحات القطع'), function () {
                frm.trigger('show_item_suggestions');
            }, __('Tools / الأدوات'));
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on exchange type
        frm.toggle_display(['original_item_code', 'original_item_name', 'exchange_item_code', 'exchange_item_name', 'original_condition'],
            frm.doc.exchange_type === 'Parts' || frm.doc.exchange_type === 'Both');
        frm.toggle_display(['original_service_order', 'exchange_service_order'],
            frm.doc.exchange_type === 'Service' || frm.doc.exchange_type === 'Both');
    },

    exchange_type: function (frm) {
        // Clear related fields when exchange type changes
        if (frm.doc.exchange_type !== 'Parts' && frm.doc.exchange_type !== 'Both') {
            frm.set_value('original_item_code', '');
            frm.set_value('exchange_item_code', '');
            frm.set_value('original_condition', '');
        }
        if (frm.doc.exchange_type !== 'Service' && frm.doc.exchange_type !== 'Both') {
            frm.set_value('original_service_order', '');
            frm.set_value('exchange_service_order', '');
        }

        frm.trigger('setup_field_dependencies');
    },

    original_sales_invoice: function (frm) {
        if (frm.doc.original_sales_invoice) {
            // Fetch customer from original sales invoice
            frappe.db.get_value('Sales Invoice', frm.doc.original_sales_invoice, 'customer')
                .then(r => {
                    if (r.message && r.message.customer) {
                        frm.set_value('customer', r.message.customer);
                    }
                });
        }
    },

    original_item_code: function (frm) {
        if (frm.doc.original_item_code && frm.doc.original_sales_invoice) {
            // Get original rate from sales invoice
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Sales Invoice',
                    name: frm.doc.original_sales_invoice
                },
                callback: function (r) {
                    if (r.message && r.message.items) {
                        const item = r.message.items.find(i => i.item_code === frm.doc.original_item_code);
                        if (item) {
                            frm.set_value('original_rate', item.rate);
                            frm.set_value('original_warehouse', item.warehouse);
                            frm.trigger('calculate_exchange_values');
                        }
                    }
                }
            });

            // Show item suggestions button
            frm.trigger('add_custom_buttons');
        }
    },

    exchange_item_code: function (frm) {
        if (frm.doc.exchange_item_code) {
            // Get exchange item rate
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Item Price',
                    filters: {
                        item_code: frm.doc.exchange_item_code,
                        price_list: 'Standard Selling'
                    },
                    fields: ['price_list_rate'],
                    limit_page_length: 1
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frm.set_value('exchange_rate', r.message[0].price_list_rate);
                        frm.trigger('calculate_exchange_values');
                    }
                }
            });

            // Check inventory availability
            frm.trigger('check_inventory_availability');
        }
    },

    original_quantity: function (frm) {
        frm.trigger('calculate_exchange_values');
    },

    exchange_quantity: function (frm) {
        frm.trigger('calculate_exchange_values');
        frm.trigger('check_inventory_availability');
    },

    calculate_exchange_values: function (frm) {
        if (frm.doc.original_item_code && frm.doc.exchange_item_code &&
            frm.doc.original_quantity && frm.doc.exchange_quantity &&
            frm.doc.original_rate && frm.doc.exchange_rate) {

            // Calculate preview
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.exchange_request.exchange_request.calculate_exchange_preview',
                args: {
                    original_item_code: frm.doc.original_item_code,
                    exchange_item_code: frm.doc.exchange_item_code,
                    original_quantity: frm.doc.original_quantity,
                    exchange_quantity: frm.doc.exchange_quantity
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('original_total_value', r.message.original_total);
                        frm.set_value('exchange_total_value', r.message.exchange_total);
                        frm.set_value('price_difference', r.message.price_difference);
                        frm.set_value('handling_fee', r.message.handling_fee);

                        if (r.message.payment_type === 'additional_payment') {
                            frm.set_value('additional_payment', r.message.final_amount);
                            frm.set_value('refund_amount', 0);
                            frm.set_value('final_amount', r.message.final_amount);
                        } else {
                            frm.set_value('additional_payment', 0);
                            frm.set_value('refund_amount', r.message.final_amount);
                            frm.set_value('final_amount', -r.message.final_amount);
                        }

                        // Update payment summary in dashboard
                        frm.trigger('update_payment_summary');
                    }
                }
            });
        }
    },

    check_inventory_availability: function (frm) {
        if (frm.doc.exchange_item_code && frm.doc.exchange_quantity) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Bin',
                    filters: {
                        item_code: frm.doc.exchange_item_code
                    },
                    fields: ['warehouse', 'actual_qty', 'projected_qty'],
                    order_by: 'actual_qty desc'
                },
                callback: function (r) {
                    if (r.message) {
                        let total_qty = 0;
                        let best_warehouse = null;

                        r.message.forEach(bin => {
                            total_qty += bin.actual_qty;
                            if (!best_warehouse && bin.actual_qty >= frm.doc.exchange_quantity) {
                                best_warehouse = bin.warehouse;
                            }
                        });

                        frm.set_value('exchange_available_qty', total_qty);

                        if (total_qty >= frm.doc.exchange_quantity) {
                            frm.set_value('availability_status', 'Available');
                            if (best_warehouse) {
                                frm.set_value('exchange_warehouse', best_warehouse);
                            }
                        } else {
                            frm.set_value('availability_status', 'Out of Stock');
                        }

                        frm.trigger('update_availability_indicator');
                    }
                }
            });
        }
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            frm.trigger('fetch_customer_data');
        }
    },

    fetch_customer_data: function (frm) {
        if (frm.doc.customer) {
            // Get customer exchange history
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Exchange Request',
                    filters: {
                        customer: frm.doc.customer
                    },
                    fields: ['name', 'exchange_date', 'exchange_type', 'price_difference', 'exchange_status'],
                    order_by: 'exchange_date desc',
                    limit_page_length: 5
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let history_html = '<h5>' + __('Recent Exchanges / التبديلات الحديثة') + '</h5>';
                        history_html += '<table class="table table-condensed">';
                        history_html += '<tr><th>' + __('Date / التاريخ') + '</th><th>' + __('Type / النوع') + '</th><th>' + __('Price Diff / فرق السعر') + '</th><th>' + __('Status / الحالة') + '</th></tr>';

                        r.message.forEach(exchange => {
                            const price_color = exchange.price_difference > 0 ? 'text-success' : 'text-danger';
                            history_html += `<tr>
                                <td>${frappe.datetime.str_to_user(exchange.exchange_date)}</td>
                                <td>${exchange.exchange_type}</td>
                                <td class="${price_color}">${format_currency(exchange.price_difference, 'OMR')}</td>
                                <td><span class="indicator ${exchange.exchange_status === 'Processed' ? 'green' : 'orange'}">${exchange.exchange_status}</span></td>
                            </tr>`;
                        });

                        history_html += '</table>';
                        frm.dashboard.add_section(history_html, __('Customer Exchange History / تاريخ تبديل العميل'));
                    }
                }
            });
        }
    },

    show_compatibility_indicator: function (frm) {
        if (frm.doc.compatibility_score) {
            let color = 'green';
            let message = __('High Compatibility / توافق عالي');

            if (frm.doc.compatibility_score < 50) {
                color = 'red';
                message = __('Low Compatibility / توافق منخفض');
            } else if (frm.doc.compatibility_score < 80) {
                color = 'orange';
                message = __('Medium Compatibility / توافق متوسط');
            }

            frm.dashboard.add_indicator(__('Compatibility: {0}%', [frm.doc.compatibility_score]), color);

            if (frm.doc.risk_level) {
                const risk_colors = {
                    'Low': 'green',
                    'Medium': 'yellow',
                    'High': 'orange',
                    'Critical': 'red'
                };
                frm.dashboard.add_indicator(__('Risk Level: {0}', [frm.doc.risk_level]), risk_colors[frm.doc.risk_level]);
            }
        }
    },

    update_payment_summary: function (frm) {
        if (frm.doc.price_difference !== undefined) {
            let summary_html = '<div class="exchange-summary">';
            summary_html += '<h5>' + __('Exchange Summary / ملخص التبديل') + '</h5>';

            if (frm.doc.final_amount > 0) {
                summary_html += `<p class="text-warning"><strong>${__('Additional Payment Required / دفعة إضافية مطلوبة')}: ${format_currency(frm.doc.final_amount, 'OMR')}</strong></p>`;
            } else if (frm.doc.final_amount < 0) {
                summary_html += `<p class="text-success"><strong>${__('Refund Amount / مبلغ الاسترداد')}: ${format_currency(Math.abs(frm.doc.final_amount), 'OMR')}</strong></p>`;
            } else {
                summary_html += `<p class="text-info"><strong>${__('No Additional Payment / لا توجد دفعة إضافية')}</strong></p>`;
            }

            if (frm.doc.handling_fee > 0) {
                summary_html += `<p><small>${__('Handling Fee / رسوم المعالجة')}: ${format_currency(frm.doc.handling_fee, 'OMR')}</small></p>`;
            }

            summary_html += '</div>';
            frm.dashboard.add_section(summary_html, __('Payment Summary / ملخص الدفع'));
        }
    },

    update_availability_indicator: function (frm) {
        if (frm.doc.availability_status) {
            let color = frm.doc.availability_status === 'Available' ? 'green' : 'red';
            frm.dashboard.add_indicator(__('Availability: {0}', [frm.doc.availability_status]), color);

            if (frm.doc.exchange_available_qty !== undefined) {
                frm.dashboard.add_indicator(__('Available Qty: {0}', [frm.doc.exchange_available_qty]),
                    frm.doc.exchange_available_qty >= frm.doc.exchange_quantity ? 'green' : 'red');
            }
        }
    },

    show_item_suggestions: function (frm) {
        if (!frm.doc.original_item_code) {
            frappe.msgprint(__('Please select original item first / يرجى اختيار القطعة الأصلية أولاً'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.sales_service.doctype.exchange_request.exchange_request.get_item_exchange_suggestions',
            args: {
                original_item_code: frm.doc.original_item_code,
                customer: frm.doc.customer
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    const d = new frappe.ui.Dialog({
                        title: __('Exchange Suggestions / اقتراحات التبديل'),
                        fields: [
                            {
                                fieldname: 'suggestions',
                                fieldtype: 'HTML',
                                options: frm.trigger('get_suggestions_html', r.message)
                            }
                        ]
                    });
                    d.show();
                } else {
                    frappe.msgprint(__('No suitable exchange items found / لم يتم العثور على قطع مناسبة للتبديل'));
                }
            }
        });
    },

    get_suggestions_html: function (frm, suggestions) {
        let html = '<div class="exchange-suggestions">';
        html += '<table class="table table-striped">';
        html += '<tr><th>' + __('Item Code / كود القطعة') + '</th><th>' + __('Name / الاسم') + '</th><th>' + __('Brand / الماركة') + '</th><th>' + __('Rate / السعر') + '</th><th>' + __('Action / الإجراء') + '</th></tr>';

        suggestions.forEach(item => {
            html += `<tr>
                <td>${item.item_code}</td>
                <td>${item.item_name}</td>
                <td>${item.brand || ''}</td>
                <td>${item.current_rate ? format_currency(item.current_rate, 'OMR') : 'N/A'}</td>
                <td><button class="btn btn-xs btn-primary" onclick="cur_frm.set_value('exchange_item_code', '${item.item_code}')" data-dismiss="modal">${__('Select / اختيار')}</button></td>
            </tr>`;
        });

        html += '</table></div>';
        return html;
    },

    show_exchange_preview: function (frm) {
        if (!frm.doc.original_item_code || !frm.doc.exchange_item_code) {
            frappe.msgprint(__('Please select both original and exchange items / يرجى اختيار القطعة الأصلية والبديلة'));
            return;
        }

        let preview_html = '<div class="exchange-preview">';
        preview_html += '<h4>' + __('Exchange Preview / معاينة التبديل') + '</h4>';
        preview_html += '<table class="table">';
        preview_html += `<tr><td><strong>${__('Original Item / القطعة الأصلية')}</strong></td><td>${frm.doc.original_item_name} (${frm.doc.original_item_code})</td></tr>`;
        preview_html += `<tr><td><strong>${__('Exchange Item / القطعة البديلة')}</strong></td><td>${frm.doc.exchange_item_name} (${frm.doc.exchange_item_code})</td></tr>`;
        preview_html += `<tr><td><strong>${__('Quantity / الكمية')}</strong></td><td>${frm.doc.original_quantity} → ${frm.doc.exchange_quantity}</td></tr>`;
        preview_html += `<tr><td><strong>${__('Price Difference / فرق السعر')}</strong></td><td>${format_currency(frm.doc.price_difference, 'OMR')}</td></tr>`;
        preview_html += `<tr><td><strong>${__('Compatibility / التوافق')}</strong></td><td>${frm.doc.compatibility_score}%</td></tr>`;
        preview_html += `<tr><td><strong>${__('Availability / التوفر')}</strong></td><td>${frm.doc.availability_status}</td></tr>`;
        preview_html += '</table>';
        preview_html += '</div>';

        const d = new frappe.ui.Dialog({
            title: __('Exchange Preview / معاينة التبديل'),
            fields: [
                {
                    fieldname: 'preview',
                    fieldtype: 'HTML',
                    options: preview_html
                }
            ]
        });
        d.show();
    },

    show_compatibility_details: function (frm) {
        let details_html = '<div class="compatibility-details">';
        details_html += '<h4>' + __('Compatibility Analysis / تحليل التوافق') + '</h4>';
        details_html += '<table class="table">';
        details_html += `<tr><td><strong>${__('Compatibility Score / درجة التوافق')}</strong></td><td>${frm.doc.compatibility_score}%</td></tr>`;
        details_html += `<tr><td><strong>${__('Risk Level / مستوى المخاطر')}</strong></td><td>${frm.doc.risk_level}</td></tr>`;
        details_html += `<tr><td><strong>${__('Exchange Complexity / تعقيد التبديل')}</strong></td><td>${frm.doc.exchange_complexity}</td></tr>`;
        details_html += `<tr><td><strong>${__('Manager Approval Required / موافقة المدير مطلوبة')}</strong></td><td>${frm.doc.requires_manager_approval ? __('Yes / نعم') : __('No / لا')}</td></tr>`;
        details_html += `<tr><td><strong>${__('Auto Approved / موافقة تلقائية')}</strong></td><td>${frm.doc.auto_approved ? __('Yes / نعم') : __('No / لا')}</td></tr>`;
        details_html += '</table>';
        details_html += '</div>';

        const d = new frappe.ui.Dialog({
            title: __('Compatibility Details / تفاصيل التوافق'),
            fields: [
                {
                    fieldname: 'details',
                    fieldtype: 'HTML',
                    options: details_html
                }
            ]
        });
        d.show();
    },

    approve_request: function (frm) {
        frappe.confirm(
            __('Are you sure you want to approve this exchange request? / هل أنت متأكد من الموافقة على طلب التبديل؟'),
            function () {
                frappe.call({
                    method: 'universal_workshop.sales_service.doctype.exchange_request.exchange_request.approve_exchange_request',
                    args: {
                        exchange_request_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.msgprint(r.message.message);
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    reject_request: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('Reject Exchange Request / رفض طلب التبديل'),
            fields: [
                {
                    fieldname: 'rejection_reason',
                    fieldtype: 'Text',
                    label: __('Rejection Reason / سبب الرفض'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Reject / رفض'),
            primary_action: function (values) {
                frappe.call({
                    method: 'universal_workshop.sales_service.doctype.exchange_request.exchange_request.reject_exchange_request',
                    args: {
                        exchange_request_name: frm.doc.name,
                        rejection_reason: values.rejection_reason
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.msgprint(r.message.message);
                            frm.reload_doc();
                            d.hide();
                        }
                    }
                });
            }
        });
        d.show();
    },

    process_exchange: function (frm) {
        frappe.confirm(
            __('Are you sure you want to process this exchange? This will create stock entries and new invoice. / هل أنت متأكد من معالجة هذا التبديل؟ سيتم إنشاء قيود المخزون وفاتورة جديدة.'),
            function () {
                frappe.call({
                    method: 'frm.doc.process_exchange',
                    doc: frm.doc,
                    callback: function (r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    show_related_documents: function (frm) {
        const related_docs = [];

        if (frm.doc.original_sales_invoice) {
            related_docs.push({
                label: __('Original Sales Invoice / فاتورة البيع الأصلية'),
                doctype: 'Sales Invoice',
                docname: frm.doc.original_sales_invoice
            });
        }

        if (frm.doc.new_sales_invoice) {
            related_docs.push({
                label: __('New Sales Invoice / فاتورة البيع الجديدة'),
                doctype: 'Sales Invoice',
                docname: frm.doc.new_sales_invoice
            });
        }

        if (frm.doc.stock_entry) {
            related_docs.push({
                label: __('Stock Entry / قيد المخزون'),
                doctype: 'Stock Entry',
                docname: frm.doc.stock_entry
            });
        }

        let docs_html = '<div class="related-docs">';
        if (related_docs.length > 0) {
            related_docs.forEach(doc => {
                docs_html += `<p><a href="/app/${doc.doctype.toLowerCase().replace(' ', '-')}/${doc.docname}" target="_blank">
                    <i class="fa fa-external-link"></i> ${doc.label}: ${doc.docname}
                </a></p>`;
            });
        } else {
            docs_html += '<p>' + __('No related documents found / لا توجد مستندات مرتبطة') + '</p>';
        }
        docs_html += '</div>';

        const d = new frappe.ui.Dialog({
            title: __('Related Documents / المستندات المرتبطة'),
            fields: [
                {
                    fieldname: 'documents',
                    fieldtype: 'HTML',
                    options: docs_html
                }
            ]
        });
        d.show();
    },

    before_save: function (frm) {
        // Validate required fields before saving
        if (frm.doc.exchange_type === 'Parts' && (!frm.doc.original_item_code || !frm.doc.exchange_item_code)) {
            frappe.validated = false;
            frappe.msgprint(__('Please select both original and exchange items / يرجى اختيار القطعة الأصلية والبديلة'));
        }

        if (frm.doc.exchange_type === 'Service' && (!frm.doc.original_service_order || !frm.doc.exchange_service_order)) {
            frappe.validated = false;
            frappe.msgprint(__('Please select both original and exchange service orders / يرجى اختيار أمر الخدمة الأصلي والبديل'));
        }
    }
});

// List view customizations
frappe.listview_settings['Exchange Request'] = {
    add_fields: ["exchange_status", "risk_level", "auto_approved", "price_difference", "compatibility_score"],
    get_indicator: function (doc) {
        if (doc.exchange_status === "Processed") {
            return [__("Processed"), "green", "exchange_status,=,Processed"];
        } else if (doc.exchange_status === "Approved") {
            return [__("Approved"), "blue", "exchange_status,=,Approved"];
        } else if (doc.exchange_status === "Rejected") {
            return [__("Rejected"), "red", "exchange_status,=,Rejected"];
        } else if (doc.exchange_status === "Pending Approval") {
            return [__("Pending"), "orange", "exchange_status,=,Pending Approval"];
        } else {
            return [__("Draft"), "gray", "exchange_status,=,Draft"];
        }
    },

    onload: function (listview) {
        // Add filters for common views
        listview.page.add_menu_item(__("High Risk Exchanges / التبديلات عالية المخاطر"), function () {
            frappe.route_options = {
                'risk_level': 'High'
            };
            listview.refresh();
        });

        listview.page.add_menu_item(__("Low Compatibility / توافق منخفض"), function () {
            frappe.route_options = {
                'compatibility_score': ['<', 70]
            };
            listview.refresh();
        });

        listview.page.add_menu_item(__("Pending Approval / في انتظار الموافقة"), function () {
            frappe.route_options = {
                'exchange_status': 'Pending Approval'
            };
            listview.refresh();
        });
    }
};

// Add custom CSS for Exchange Request
frappe.dom.add_css(`
    .exchange-summary {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .exchange-preview table,
    .compatibility-details table {
        margin-top: 10px;
    }
    
    .exchange-suggestions table {
        font-size: 12px;
    }
    
    .exchange-request-risk-high {
        border-left: 4px solid #ff6b6b;
    }
    
    .exchange-request-risk-critical {
        border-left: 4px solid #ff3838;
        background-color: #fff5f5;
    }
    
    .related-docs a {
        display: inline-block;
        margin: 5px 0;
        color: #007bff;
        text-decoration: none;
    }
    
    .related-docs a:hover {
        text-decoration: underline;
    }
`); 