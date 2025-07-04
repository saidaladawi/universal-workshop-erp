// Universal Workshop Sales Invoice Customizations
// Copyright (c) 2024, Said Al-Adowi and contributors

frappe.ui.form.on('Sales Invoice', {
    refresh: function (frm) {
        // Setup Arabic field enhancements
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_language_selection');
        frm.trigger('setup_print_format_button');
    },

    customer: function (frm) {
        // Auto-populate Arabic customer name when customer is selected
        if (frm.doc.customer) {
            frm.trigger('fetch_arabic_customer_details');
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['customer_name_arabic'];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].$input) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                });
            }
        });
    },

    setup_language_selection: function (frm) {
        // Set default invoice language based on customer or system preference
        if (!frm.doc.invoice_language) {
            // Default to bilingual if not set
            frm.set_value('invoice_language', 'Bilingual');
        }
    },

    setup_print_format_button: function (frm) {
        // Add custom print button for bilingual invoice
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print Bilingual Invoice'), function () {
                frm.trigger('print_bilingual_invoice');
            }, __('Print'));
        }
    },

    fetch_arabic_customer_details: function (frm) {
        // Fetch Arabic customer name and populate the field
        if (frm.doc.customer && !frm.doc.customer_name_arabic) {
            frappe.call({
                method: 'universal_workshop.billing_management.fixtures.invoice_custom_fields.get_arabic_customer_name',
                args: {
                    customer: frm.doc.customer
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('customer_name_arabic', r.message);
                    }
                }
            });
        }
    },

    print_bilingual_invoice: function (frm) {
        // Print using the bilingual invoice format
        const print_format = "Universal Workshop - Bilingual Invoice";
        const language = frm.doc.invoice_language === 'Arabic' ? 'ar' : 'en';

        frappe.route_options = {
            "doctype": frm.doc.doctype,
            "name": frm.doc.name,
            "print_format": print_format,
            "language": language
        };

        frappe.set_route("print", frm.doc.doctype, frm.doc.name);
    },

    invoice_language: function (frm) {
        // Handle language selection change
        if (frm.doc.invoice_language) {
            frappe.show_alert({
                message: __('Invoice language set to {0}', [frm.doc.invoice_language]),
                indicator: 'green'
            });
        }
    },

    before_save: function (frm) {
        // Generate e-invoice UUID if not exists
        if (!frm.doc.e_invoice_uuid && frm.doc.docstatus === 0) {
            frm.set_value('e_invoice_uuid', frappe.utils.get_random_string(32));
        }

        // Generate tax invoice number sequence
        if (!frm.doc.tax_invoice_number && frm.doc.docstatus === 0) {
            frm.trigger('generate_tax_invoice_number');
        }
    },

    generate_tax_invoice_number: function (frm) {
        // Generate sequential tax invoice number for VAT compliance
        frappe.call({
            method: 'universal_workshop.billing_management.utils.generate_tax_invoice_number',
            args: {
                company: frm.doc.company,
                posting_date: frm.doc.posting_date
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('tax_invoice_number', r.message);
                }
            }
        });
    }
});

// Sales Invoice Item customizations
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function (frm, cdt, cdn) {
        // Auto-populate Arabic item details when item is selected
        const row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.call({
                method: 'universal_workshop.billing_management.fixtures.invoice_custom_fields.get_arabic_item_details',
                args: {
                    item_code: row.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'item_name_arabic', r.message.item_name_arabic);
                        frappe.model.set_value(cdt, cdn, 'description_arabic', r.message.description_arabic);
                        frm.refresh_field('items');
                    }
                }
            });
        }
    },

    items_add: function (frm, cdt, cdn) {
        // Setup Arabic fields for new item rows
        setTimeout(() => {
            const row = locals[cdt][cdn];
            const row_doc = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];

            if (row_doc) {
                // Set RTL direction for Arabic fields in the row
                const arabic_fields = ['item_name_arabic', 'description_arabic'];
                arabic_fields.forEach(field => {
                    const field_input = row_doc.columns[field];
                    if (field_input && field_input.$input) {
                        field_input.$input.attr('dir', 'rtl');
                        field_input.$input.css({
                            'text-align': 'right',
                            'font-family': 'Tahoma, Arial Unicode MS, sans-serif'
                        });
                    }
                });
            }
        }, 500);
    }
});

// Custom functions for language detection and formatting
function detect_text_language(text) {
    // Simple Arabic text detection
    const arabic_pattern = /[\u0600-\u06FF]/;
    return arabic_pattern.test(text) ? 'ar' : 'en';
}

function format_currency_bilingual(amount, currency) {
    // Format currency for bilingual display
    if (currency === 'OMR') {
        return `${amount.toFixed(3)} ${currency} (${(amount * 1000).toFixed(0)} بيسة)`;
    }
    return `${amount.toFixed(2)} ${currency}`;
}

// Override print preview to use bilingual format
frappe.ui.form.PrintView = class extends frappe.ui.form.PrintView {
    constructor(opts) {
        super(opts);

        // Set default print format to bilingual if available
        if (opts.doctype === 'Sales Invoice' &&
            frappe.boot.print_formats['Sales Invoice'] &&
            frappe.boot.print_formats['Sales Invoice'].includes('Universal Workshop - Bilingual Invoice')) {
            this.print_format = 'Universal Workshop - Bilingual Invoice';
        }
    }
};

// Arabic number conversion utility
function convert_to_arabic_numerals(text) {
    const arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    };

    return text.replace(/[0-9]/g, function (match) {
        return arabic_numerals[match];
    });
}

// Utility to format amounts in Arabic text
function amount_in_words_arabic(amount) {
    // Basic implementation - would need full Arabic number-to-words conversion
    const currency_text = frappe.boot.sysdefaults.currency === 'OMR' ? 'ريال عماني' : 'ريال';
    return `${convert_to_arabic_numerals(amount.toString())} ${currency_text}`;
} 