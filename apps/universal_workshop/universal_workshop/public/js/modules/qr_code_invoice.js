// QR Code Invoice Enhancement for Universal Workshop ERP
// Copyright (c) 2024, Said Al-Adowi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    refresh: function (frm) {
        // Add QR code generation button
        frm.trigger('add_qr_code_button');

        // Show QR code if generated
        frm.trigger('display_qr_code');

        // Setup Arabic field directions
        frm.trigger('setup_arabic_qr_fields');
    },

    add_qr_code_button: function (frm) {
        if (frm.doc.docstatus === 1) { // Only for submitted invoices
            // Generate QR Code button
            frm.add_custom_button(__('Generate QR Code'), function () {
                frm.trigger('generate_qr_code');
            }, __('E-Invoice'));

            // Validate QR Code button (if QR exists)
            if (frm.doc.qr_code_data) {
                frm.add_custom_button(__('Validate QR Code'), function () {
                    frm.trigger('validate_qr_code');
                }, __('E-Invoice'));
            }

            // Download QR Code button (if QR exists)
            if (frm.doc.qr_code_image) {
                frm.add_custom_button(__('Download QR Image'), function () {
                    frm.trigger('download_qr_image');
                }, __('E-Invoice'));
            }
        }
    },

    generate_qr_code: function (frm) {
        frappe.call({
            method: 'universal_workshop.billing_management.qr_code_generator.generate_qr_code_for_sales_invoice',
            args: {
                sales_invoice_name: frm.doc.name
            },
            btn: frm.page.btn_primary,
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('QR Code generated successfully'),
                        indicator: 'green'
                    });

                    // Refresh the form to show new QR data
                    frm.reload_doc();

                    // Show QR code details
                    frm.trigger('show_qr_generation_details', r.message);

                } else {
                    let error_msg = r.message ? r.message.error : __('QR Code generation failed');
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: error_msg
                    });
                }
            }
        });
    },

    validate_qr_code: function (frm) {
        if (!frm.doc.qr_code_data) {
            frappe.msgprint(__('No QR code data found. Please generate QR code first.'));
            return;
        }

        frappe.call({
            method: 'universal_workshop.billing_management.qr_code_generator.validate_qr_code_data',
            args: {
                tlv_base64: frm.doc.qr_code_data
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    let decoded_data = r.message.decoded_data;

                    // Format decoded data for display
                    let html = '<div class="qr-validation-result">';
                    html += '<h5>' + __('QR Code Validation Results') + '</h5>';
                    html += '<table class="table table-bordered">';

                    const field_labels = {
                        'seller_name': __('Seller Name'),
                        'vat_number': __('VAT Number'),
                        'invoice_timestamp': __('Invoice Timestamp'),
                        'invoice_total': __('Invoice Total'),
                        'vat_amount': __('VAT Amount')
                    };

                    for (let field in decoded_data) {
                        let label = field_labels[field] || field;
                        let value = decoded_data[field];

                        // Add currency formatting for amounts
                        if (field.includes('amount') || field.includes('total')) {
                            value = format_currency(value, 'OMR');
                        }

                        html += `<tr><td><strong>${label}:</strong></td><td>${value}</td></tr>`;
                    }

                    html += '</table></div>';

                    frappe.msgprint({
                        title: __('QR Code Validation'),
                        message: html,
                        wide: true
                    });

                } else {
                    frappe.msgprint({
                        title: __('Validation Error'),
                        indicator: 'red',
                        message: r.message ? r.message.error : __('QR code validation failed')
                    });
                }
            }
        });
    },

    download_qr_image: function (frm) {
        if (!frm.doc.qr_code_image) {
            frappe.msgprint(__('No QR code image found. Please generate QR code first.'));
            return;
        }

        // Create download link
        let filename = `qr_code_${frm.doc.name}.png`;
        let link = document.createElement('a');
        link.href = frm.doc.qr_code_image;
        link.download = filename;
        link.click();

        frappe.show_alert({
            message: __('QR Code image downloaded'),
            indicator: 'green'
        });
    },

    display_qr_code: function (frm) {
        if (frm.doc.qr_code_image && frm.doc.qr_code_generated) {
            // Create QR code display section
            let qr_html = `
                <div class="qr-code-display">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>${__('E-Invoice QR Code')}</h5>
                            <img src="${frm.doc.qr_code_image}" 
                                 alt="QR Code" 
                                 style="max-width: 200px; border: 1px solid #ddd; padding: 10px;">
                        </div>
                        <div class="col-md-6">
                            <h6>${__('QR Code Information')}</h6>
                            <p><strong>${__('Generated On')}:</strong> ${frm.doc.qr_code_timestamp ? frappe.datetime.str_to_user(frm.doc.qr_code_timestamp) : 'N/A'}</p>
                            <p><strong>${__('Compliance Status')}:</strong> 
                               <span class="label label-${frm.doc.e_invoice_compliance_status === 'Compliant' ? 'success' : 'default'}">
                                   ${frm.doc.e_invoice_compliance_status || 'Pending'}
                               </span>
                            </p>
                            <p><strong>${__('E-Invoice UUID')}:</strong> ${frm.doc.e_invoice_uuid || 'Not assigned'}</p>
                        </div>
                    </div>
                </div>
            `;

            // Add to form
            if (!frm.qr_code_wrapper) {
                frm.qr_code_wrapper = $('<div>').appendTo(frm.layout.wrapper.find('.form-layout'));
            }
            frm.qr_code_wrapper.html(qr_html);
        }
    },

    show_qr_generation_details: function (frm, qr_result) {
        if (qr_result && qr_result.invoice_data) {
            let data = qr_result.invoice_data;

            let html = '<div class="qr-generation-details">';
            html += '<h5>' + __('QR Code Generated Successfully') + '</h5>';
            html += '<p>' + __('The following data has been encoded in the QR code:') + '</p>';
            html += '<table class="table table-bordered">';
            html += `<tr><td><strong>${__('Seller Name')}:</strong></td><td>${data.seller_name}</td></tr>`;
            html += `<tr><td><strong>${__('VAT Number')}:</strong></td><td>${data.vat_number}</td></tr>`;
            html += `<tr><td><strong>${__('Invoice Total')}:</strong></td><td>${format_currency(data.invoice_total, 'OMR')}</td></tr>`;
            html += `<tr><td><strong>${__('VAT Amount')}:</strong></td><td>${format_currency(data.vat_amount, 'OMR')}</td></tr>`;
            html += `<tr><td><strong>${__('Timestamp')}:</strong></td><td>${data.invoice_timestamp}</td></tr>`;
            html += '</table></div>';

            frappe.msgprint({
                title: __('QR Code Details'),
                message: html,
                wide: true
            });
        }
    },

    setup_arabic_qr_fields: function (frm) {
        // Set RTL direction for Arabic fields if they exist
        if (frappe.boot.lang === 'ar') {
            ['company_name_ar'].forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.fields_dict[field].$input.attr('dir', 'rtl');
                    frm.fields_dict[field].$input.css('text-align', 'right');
                }
            });
        }
    },

    before_submit: function (frm) {
        // Show warning if QR code is not generated
        if (!frm.doc.qr_code_generated) {
            frappe.msgprint({
                title: __('QR Code Notice'),
                message: __('QR code will be automatically generated after submission for e-invoice compliance.'),
                indicator: 'blue'
            });
        }
    }
});

// Utility function for QR code operations
frappe.qr_code_utils = {

    bulk_generate_qr_codes: function (invoice_names) {
        frappe.call({
            method: 'universal_workshop.billing_management.qr_code_generator.bulk_generate_qr_codes',
            args: {
                invoice_list: invoice_names
            },
            callback: function (r) {
                if (r.message) {
                    let results = r.message;
                    let success_count = results.filter(result => result.success).length;
                    let error_count = results.length - success_count;

                    frappe.msgprint({
                        title: __('Bulk QR Generation Results'),
                        message: __('Generated QR codes for {0} invoices. {1} errors.', [success_count, error_count]),
                        indicator: error_count > 0 ? 'orange' : 'green'
                    });
                }
            }
        });
    },

    check_qr_compliance: function (frm) {
        // Check if all required fields for QR generation are available
        let missing_fields = [];

        // Check company VAT number
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Company',
                name: frm.doc.company
            },
            callback: function (r) {
                if (r.message) {
                    let company = r.message;
                    if (!company.vat_number && !company.tax_id) {
                        missing_fields.push(__('Company VAT Number'));
                    }
                    if (!company.company_name_ar) {
                        missing_fields.push(__('Company Arabic Name'));
                    }

                    if (missing_fields.length > 0) {
                        frappe.msgprint({
                            title: __('QR Code Compliance Check'),
                            message: __('Missing required fields for QR generation: {0}', [missing_fields.join(', ')]),
                            indicator: 'orange'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('All required fields available for QR generation'),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    }
};

// List view enhancements for bulk operations
frappe.listview_settings['Sales Invoice'] = {
    add_fields: ['qr_code_generated', 'e_invoice_compliance_status'],

    onload: function (listview) {
        // Add bulk QR generation button
        listview.page.add_action_item(__('Generate QR Codes'), function () {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select invoices to generate QR codes.'));
                return;
            }

            let invoice_names = selected_docs.map(doc => doc.name);
            frappe.qr_code_utils.bulk_generate_qr_codes(invoice_names);
        });
    },

    formatters: {
        qr_code_generated: function (value) {
            if (value) {
                return '<span class="label label-success">QR Generated</span>';
            } else {
                return '<span class="label label-default">No QR</span>';
            }
        },

        e_invoice_compliance_status: function (value) {
            let color = 'default';
            if (value === 'Compliant') color = 'success';
            else if (value === 'Non-Compliant') color = 'danger';
            else if (value === 'Error') color = 'warning';

            return `<span class="label label-${color}">${value || 'Pending'}</span>`;
        }
    }
}; 