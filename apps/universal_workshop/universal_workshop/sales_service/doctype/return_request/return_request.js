frappe.ui.form.on('Return Request', {
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
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic text fields
        const arabic_fields = ['reason', 'condition_notes', 'customer_notes', 'admin_notes', 'internal_notes'];
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
            // Add buttons based on request status
            if (frm.doc.request_status === 'Pending Approval') {
                // Approve button
                frm.add_custom_button(__('Approve / موافقة'), function () {
                    frm.trigger('approve_request');
                }, __('Actions / الإجراءات'));

                // Reject button
                frm.add_custom_button(__('Reject / رفض'), function () {
                    frm.trigger('reject_request');
                }, __('Actions / الإجراءات'));
            }

            if (frm.doc.request_status === 'Approved') {
                // Process button
                frm.add_custom_button(__('Process Return / معالجة الاسترجاع'), function () {
                    frm.trigger('process_return');
                }, __('Actions / الإجراءات'));
            }

            // Customer history button
            frm.add_custom_button(__('Customer History / تاريخ العميل'), function () {
                frm.trigger('show_customer_history');
            }, __('View / عرض'));

            // Related documents button
            frm.add_custom_button(__('Related Documents / المستندات المرتبطة'), function () {
                frm.trigger('show_related_documents');
            }, __('View / عرض'));
        }
    },

    setup_field_dependencies: function (frm) {
        // Show/hide fields based on request type
        frm.toggle_display(['item_code', 'item_name', 'part_status'],
            frm.doc.request_type === 'Parts' || frm.doc.request_type === 'Both');
        frm.toggle_display(['service_order'],
            frm.doc.request_type === 'Service' || frm.doc.request_type === 'Both');
    },

    request_type: function (frm) {
        // Clear related fields when request type changes
        if (frm.doc.request_type !== 'Parts' && frm.doc.request_type !== 'Both') {
            frm.set_value('item_code', '');
            frm.set_value('part_status', '');
        }
        if (frm.doc.request_type !== 'Service' && frm.doc.request_type !== 'Both') {
            frm.set_value('service_order', '');
        }

        frm.trigger('setup_field_dependencies');
    },

    sales_invoice: function (frm) {
        if (frm.doc.sales_invoice) {
            // Fetch customer from sales invoice
            frappe.db.get_value('Sales Invoice', frm.doc.sales_invoice, 'customer')
                .then(r => {
                    if (r.message && r.message.customer) {
                        frm.set_value('customer', r.message.customer);
                    }
                });

            // Fetch delivery note if exists
            frappe.db.get_value('Delivery Note', { 'against_sales_invoice': frm.doc.sales_invoice }, 'name')
                .then(r => {
                    if (r.message && r.message.name) {
                        frm.set_value('delivery_note', r.message.name);
                    }
                });
        }
    },

    item_code: function (frm) {
        if (frm.doc.item_code && frm.doc.sales_invoice) {
            // Get original rate from sales invoice
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Sales Invoice',
                    name: frm.doc.sales_invoice
                },
                callback: function (r) {
                    if (r.message && r.message.items) {
                        const item = r.message.items.find(i => i.item_code === frm.doc.item_code);
                        if (item) {
                            frm.set_value('original_rate', item.rate);
                            frm.trigger('calculate_return_value');
                        }
                    }
                }
            });
        }
    },

    return_quantity: function (frm) {
        frm.trigger('calculate_return_value');
    },

    part_status: function (frm) {
        frm.trigger('calculate_return_value');
    },

    calculate_return_value: function (frm) {
        if (frm.doc.return_quantity && frm.doc.original_rate) {
            const base_value = frm.doc.return_quantity * frm.doc.original_rate;

            // Apply condition deductions
            const deduction_map = {
                'New': 0,
                'Unopened': 0,
                'Opened': 5,
                'Used': 15,
                'Defective': 0,
                'Damaged': 25,
                'Other': 10
            };

            const deduction = deduction_map[frm.doc.part_status] || 10;
            const return_value = base_value * (1 - deduction / 100);

            frm.set_value('return_value', return_value);

            // Estimate refund amount (simplified calculation)
            frm.set_value('refund_amount', return_value * 1.05); // Assume 5% tax
        }
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            frm.trigger('fetch_customer_data');
        }
    },

    fetch_customer_data: function (frm) {
        if (frm.doc.customer) {
            // Get customer return history for fraud assessment
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.return_request.return_request.get_customer_return_history',
                args: {
                    customer: frm.doc.customer,
                    limit: 5
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let history_html = '<h5>' + __('Recent Returns / الاسترجاعات الحديثة') + '</h5>';
                        history_html += '<table class="table table-condensed">';
                        history_html += '<tr><th>' + __('Date / التاريخ') + '</th><th>' + __('Type / النوع') + '</th><th>' + __('Value / القيمة') + '</th><th>' + __('Status / الحالة') + '</th></tr>';

                        r.message.forEach(return_req => {
                            history_html += `<tr>
                                <td>${frappe.datetime.str_to_user(return_req.request_date)}</td>
                                <td>${return_req.request_type}</td>
                                <td>${format_currency(return_req.return_value, 'OMR')}</td>
                                <td><span class="indicator ${return_req.request_status === 'Processed' ? 'green' : 'orange'}">${return_req.request_status}</span></td>
                            </tr>`;
                        });

                        history_html += '</table>';
                        frm.dashboard.add_section(history_html, __('Customer Return History / تاريخ استرجاع العميل'));
                    }
                }
            });
        }
    },

    approve_request: function (frm) {
        frappe.confirm(
            __('Are you sure you want to approve this return request? / هل أنت متأكد من الموافقة على طلب الاسترجاع؟'),
            function () {
                frappe.call({
                    method: 'universal_workshop.sales_service.doctype.return_request.return_request.approve_return_request',
                    args: {
                        return_request_name: frm.doc.name
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
            title: __('Reject Return Request / رفض طلب الاسترجاع'),
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
                    method: 'universal_workshop.sales_service.doctype.return_request.return_request.reject_return_request',
                    args: {
                        return_request_name: frm.doc.name,
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

    process_return: function (frm) {
        frappe.confirm(
            __('Are you sure you want to process this return? This will create stock entries and credit notes. / هل أنت متأكد من معالجة هذا الاسترجاع؟ سيتم إنشاء قيود المخزون وإشعارات الدائن.'),
            function () {
                frappe.call({
                    method: 'frm.doc.process_return',
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

    show_customer_history: function (frm) {
        frappe.route_options = {
            'customer': frm.doc.customer
        };
        frappe.set_route('List', 'Return Request');
    },

    show_related_documents: function (frm) {
        const related_docs = [];

        if (frm.doc.sales_invoice) {
            related_docs.push({
                label: __('Sales Invoice / فاتورة البيع'),
                doctype: 'Sales Invoice',
                docname: frm.doc.sales_invoice
            });
        }

        if (frm.doc.delivery_note) {
            related_docs.push({
                label: __('Delivery Note / إشعار التسليم'),
                doctype: 'Delivery Note',
                docname: frm.doc.delivery_note
            });
        }

        if (frm.doc.stock_entry) {
            related_docs.push({
                label: __('Stock Entry / قيد المخزون'),
                doctype: 'Stock Entry',
                docname: frm.doc.stock_entry
            });
        }

        if (frm.doc.credit_note) {
            related_docs.push({
                label: __('Credit Note / إشعار دائن'),
                doctype: 'Sales Invoice',
                docname: frm.doc.credit_note
            });
        }

        const d = new frappe.ui.Dialog({
            title: __('Related Documents / المستندات المرتبطة'),
            fields: [
                {
                    fieldname: 'documents',
                    fieldtype: 'HTML',
                    options: frm.trigger('get_related_docs_html', related_docs)
                }
            ]
        });
        d.show();
    },

    get_related_docs_html: function (frm, docs) {
        let html = '<div class="related-docs">';

        if (docs && docs.length > 0) {
            docs.forEach(doc => {
                html += `<p><a href="/app/${doc.doctype.toLowerCase().replace(' ', '-')}/${doc.docname}" target="_blank">
                    <i class="fa fa-external-link"></i> ${doc.label}: ${doc.docname}
                </a></p>`;
            });
        } else {
            html += '<p>' + __('No related documents found / لا توجد مستندات مرتبطة') + '</p>';
        }

        html += '</div>';
        return html;
    },

    before_save: function (frm) {
        // Validate required fields before saving
        if (frm.doc.request_type === 'Parts' && !frm.doc.item_code) {
            frappe.validated = false;
            frappe.msgprint(__('Please select an item code for parts return / يرجى اختيار كود القطعة لاسترجاع القطع'));
        }

        if (frm.doc.request_type === 'Service' && !frm.doc.service_order) {
            frappe.validated = false;
            frappe.msgprint(__('Please select a service order for service return / يرجى اختيار أمر الخدمة لاسترجاع الخدمات'));
        }
    }
});

// List view customizations
frappe.listview_settings['Return Request'] = {
    add_fields: ["request_status", "risk_level", "auto_approved", "return_value"],
    get_indicator: function (doc) {
        if (doc.request_status === "Processed") {
            return [__("Processed"), "green", "request_status,=,Processed"];
        } else if (doc.request_status === "Approved") {
            return [__("Approved"), "blue", "request_status,=,Approved"];
        } else if (doc.request_status === "Rejected") {
            return [__("Rejected"), "red", "request_status,=,Rejected"];
        } else if (doc.request_status === "Pending Approval") {
            return [__("Pending"), "orange", "request_status,=,Pending Approval"];
        } else {
            return [__("Draft"), "gray", "request_status,=,Draft"];
        }
    },

    onload: function (listview) {
        // Add bulk actions
        listview.page.add_menu_item(__("Process Approved Returns / معالجة الاسترجاعات الموافق عليها"), function () {
            frappe.call({
                method: 'universal_workshop.sales_service.doctype.return_request.return_request.process_approved_returns',
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(r.message.message);
                        listview.refresh();
                    }
                }
            });
        });

        // Add filters for common views
        listview.page.add_menu_item(__("High Risk Returns / الاسترجاعات عالية المخاطر"), function () {
            frappe.route_options = {
                'risk_level': 'High'
            };
            listview.refresh();
        });

        listview.page.add_menu_item(__("Pending Approval / في انتظار الموافقة"), function () {
            frappe.route_options = {
                'request_status': 'Pending Approval'
            };
            listview.refresh();
        });
    }
};

// Add custom CSS for Arabic support
frappe.dom.add_css(`
    .arabic-support .form-control[dir="auto"] {
        text-align: right;
        font-family: 'Tahoma', 'Arial Unicode MS', sans-serif;
    }
    
    .return-request-risk-high {
        border-left: 4px solid #ff6b6b;
    }
    
    .return-request-risk-critical {
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
