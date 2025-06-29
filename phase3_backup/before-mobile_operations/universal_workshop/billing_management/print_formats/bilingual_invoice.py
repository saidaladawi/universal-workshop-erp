# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def install_bilingual_invoice_print_format():
    """
    Install bilingual (Arabic/English) invoice print format for Universal Workshop
    """

    # Check if print format already exists
    if frappe.db.exists("Print Format", "Universal Workshop - Bilingual Invoice"):
        frappe.msgprint(_("Bilingual Invoice print format already exists"))
        return

    # Create the print format
    print_format = frappe.new_doc("Print Format")
    print_format.name = "Universal Workshop - Bilingual Invoice"
    print_format.doc_type = "Sales Invoice"
    print_format.module = "Universal Workshop"
    print_format.standard = "Yes"
    print_format.disabled = 0
    print_format.print_format_builder = 0
    print_format.print_format_type = "Jinja"

    # Bilingual invoice HTML template
    print_format.html = get_bilingual_invoice_html()

    # CSS for Arabic RTL support
    print_format.css = get_bilingual_invoice_css()

    try:
        print_format.insert()
        frappe.db.commit()
        frappe.msgprint(_("Bilingual Invoice print format created successfully"))

    except Exception as e:
        frappe.log_error(f"Error creating bilingual invoice print format: {str(e)}")
        frappe.throw(_("Failed to create bilingual invoice print format: {0}").format(str(e)))


def get_bilingual_invoice_html():
    """
    Get the HTML template for bilingual invoice
    """
    return """
<!-- Universal Workshop Bilingual Invoice Template -->
{% set lang = frappe.local.lang or "en" %}
{% set is_arabic = lang == "ar" %}
{% set direction = "rtl" if is_arabic else "ltr" %}
{% set text_align = "right" if is_arabic else "left" %}

<div class="invoice-container" dir="{{ direction }}" style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif;">
    <!-- Header Section -->
    <div class="invoice-header">
        <div class="company-section">
            <div class="company-logo">
                {% if doc.company_logo %}
                    <img src="{{ doc.company_logo }}" alt="Company Logo" style="max-height: 80px;">
                {% endif %}
            </div>
            
            <div class="company-details" style="text-align: {{ text_align }};">
                <h2 class="company-name">
                    {% if is_arabic and doc.company_arabic %}
                        {{ doc.company_arabic }}
                    {% else %}
                        {{ doc.company }}
                    {% endif %}
                </h2>
                
                <!-- Company Address -->
                <div class="company-address">
                    {% if is_arabic and doc.company_address_arabic %}
                        {{ doc.company_address_arabic | nl2br }}
                    {% else %}
                        {% if doc.company_address %}
                            {{ frappe.db.get_value("Address", doc.company_address, "address_line1") | default("") }}
                            {% if frappe.db.get_value("Address", doc.company_address, "address_line2") %}
                                <br>{{ frappe.db.get_value("Address", doc.company_address, "address_line2") }}
                            {% endif %}
                            <br>{{ frappe.db.get_value("Address", doc.company_address, "city") }}, {{ frappe.db.get_value("Address", doc.company_address, "country") }}
                        {% endif %}
                    {% endif %}
                </div>
                
                <!-- Company Contact Info -->
                <div class="company-contact">
                    {% if doc.company_phone %}
                        <div>{{ _("Phone") }}: {{ doc.company_phone }}</div>
                    {% endif %}
                    {% if doc.company_email %}
                        <div>{{ _("Email") }}: {{ doc.company_email }}</div>
                    {% endif %}
                    {% if doc.company_website %}
                        <div>{{ _("Website") }}: {{ doc.company_website }}</div>
                    {% endif %}
                </div>
                
                <!-- VAT Registration Number -->
                {% if doc.tax_id %}
                    <div class="tax-id">
                        <strong>{{ _("VAT Registration No") }}</strong>: {{ doc.tax_id }}
                    </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Invoice Title -->
        <div class="invoice-title" style="text-align: center; margin: 20px 0;">
            <h1>
                {% if is_arabic %}
                    فاتورة ضريبية<br>
                    <small style="font-size: 14px;">Tax Invoice</small>
                {% else %}
                    Tax Invoice<br>
                    <small style="font-size: 14px;">فاتورة ضريبية</small>
                {% endif %}
            </h1>
        </div>
    </div>
    
    <!-- Invoice Info Section -->
    <div class="invoice-info" style="margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding: 10px;">
                    <!-- Customer Details -->
                    <div class="customer-details">
                        <h3>{{ _("Bill To") }}{% if is_arabic %} - إرسال الفاتورة إلى{% endif %}</h3>
                        <div class="customer-name">
                            <strong>
                                {% if is_arabic and doc.customer_name_arabic %}
                                    {{ doc.customer_name_arabic }}
                                {% else %}
                                    {{ doc.customer_name }}
                                {% endif %}
                            </strong>
                        </div>
                        
                        <!-- Customer Address -->
                        {% if doc.customer_address %}
                            <div class="customer-address">
                                {% set cust_address = frappe.get_doc("Address", doc.customer_address) %}
                                {% if is_arabic and cust_address.address_line1_arabic %}
                                    {{ cust_address.address_line1_arabic }}<br>
                                    {% if cust_address.address_line2_arabic %}
                                        {{ cust_address.address_line2_arabic }}<br>
                                    {% endif %}
                                    {{ cust_address.city_arabic or cust_address.city }}
                                {% else %}
                                    {{ cust_address.address_line1 }}<br>
                                    {% if cust_address.address_line2 %}
                                        {{ cust_address.address_line2 }}<br>
                                    {% endif %}
                                    {{ cust_address.city }}, {{ cust_address.country }}
                                {% endif %}
                            </div>
                        {% endif %}
                        
                        <!-- Customer VAT Number -->
                        {% if doc.tax_id %}
                            <div class="customer-tax-id">
                                <strong>{{ _("VAT No") }}</strong>: {{ doc.tax_id }}
                            </div>
                        {% endif %}
                    </div>
                </td>
                
                <td style="width: 50%; vertical-align: top; padding: 10px; text-align: {{ text_align }};">
                    <!-- Invoice Details -->
                    <div class="invoice-details">
                        <table style="width: 100%;">
                            <tr>
                                <td style="padding: 5px;"><strong>{{ _("Invoice No") }}</strong></td>
                                <td style="padding: 5px;">{{ doc.name }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px;"><strong>{{ _("Invoice Date") }}</strong></td>
                                <td style="padding: 5px;">{{ frappe.utils.formatdate(doc.posting_date, "dd/MM/yyyy") }}</td>
                            </tr>
                            {% if doc.due_date %}
                            <tr>
                                <td style="padding: 5px;"><strong>{{ _("Due Date") }}</strong></td>
                                <td style="padding: 5px;">{{ frappe.utils.formatdate(doc.due_date, "dd/MM/yyyy") }}</td>
                            </tr>
                            {% endif %}
                            {% if doc.po_no %}
                            <tr>
                                <td style="padding: 5px;"><strong>{{ _("PO No") }}</strong></td>
                                <td style="padding: 5px;">{{ doc.po_no }}</td>
                            </tr>
                            {% endif %}
                            <tr>
                                <td style="padding: 5px;"><strong>{{ _("Currency") }}</strong></td>
                                <td style="padding: 5px;">{{ doc.currency }}</td>
                            </tr>
                        </table>
                    </div>
                </td>
            </tr>
        </table>
    </div>
    
    <!-- Items Table -->
    <div class="items-section" style="margin: 20px 0;">
        <table class="items-table" style="width: 100%; border-collapse: collapse; border: 1px solid #000;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                        {{ _("Item") }}{% if is_arabic %}<br>الصنف{% endif %}
                    </th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                        {{ _("Description") }}{% if is_arabic %}<br>الوصف{% endif %}
                    </th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ _("Qty") }}{% if is_arabic %}<br>الكمية{% endif %}
                    </th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ _("Unit Price") }}{% if is_arabic %}<br>سعر الوحدة{% endif %}
                    </th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ _("Total") }}{% if is_arabic %}<br>الإجمالي{% endif %}
                    </th>
                </tr>
            </thead>
            <tbody>
                {% for row in doc.items %}
                <tr>
                    <td style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                        {% if is_arabic and row.item_name_arabic %}
                            {{ row.item_name_arabic }}<br>
                            <small style="color: #666;">{{ row.item_name }}</small>
                        {% else %}
                            {{ row.item_name }}
                            {% if row.item_name_arabic %}
                                <br><small style="color: #666;">{{ row.item_name_arabic }}</small>
                            {% endif %}
                        {% endif %}
                    </td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                        {% if is_arabic and row.description_arabic %}
                            {{ row.description_arabic }}
                        {% else %}
                            {{ row.description or "" }}
                        {% endif %}
                    </td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ "%.0f"|format(row.qty) }}
                    </td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ "%.3f"|format(row.rate) }} {{ doc.currency }}
                    </td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                        {{ "%.3f"|format(row.amount) }} {{ doc.currency }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Totals Section -->
    <div class="totals-section" style="margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 60%;"></td>
                <td style="width: 40%;">
                    <table style="width: 100%; border: 1px solid #000;">
                        <tr>
                            <td style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                                <strong>{{ _("Subtotal") }}{% if is_arabic %} - المجموع الفرعي{% endif %}</strong>
                            </td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                                <strong>{{ "%.3f"|format(doc.net_total) }} {{ doc.currency }}</strong>
                            </td>
                        </tr>
                        
                        <!-- Tax Details -->
                        {% for tax in doc.taxes %}
                        <tr>
                            <td style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                                {{ tax.description }}
                                {% if tax.rate %}
                                    ({{ "%.1f"|format(tax.rate) }}%)
                                {% endif %}
                            </td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                                {{ "%.3f"|format(tax.tax_amount) }} {{ doc.currency }}
                            </td>
                        </tr>
                        {% endfor %}
                        
                        <tr style="background-color: #f5f5f5;">
                            <td style="border: 1px solid #000; padding: 8px; text-align: {{ text_align }};">
                                <strong>{{ _("Grand Total") }}{% if is_arabic %} - المجموع الإجمالي{% endif %}</strong>
                            </td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center;">
                                <strong>{{ "%.3f"|format(doc.grand_total) }} {{ doc.currency }}</strong>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
    
    <!-- QR Code Section (Placeholder for e-invoice compliance) -->
    {% if doc.qr_code %}
    <div class="qr-code-section" style="margin: 20px 0; text-align: center;">
        <h4>{{ _("E-Invoice QR Code") }}{% if is_arabic %} - رمز الاستجابة السريعة{% endif %}</h4>
        <div class="qr-code-placeholder" style="border: 1px dashed #ccc; padding: 20px; display: inline-block;">
            <!-- QR Code will be generated here -->
            <p>{{ _("QR Code") }}: {{ doc.qr_code }}</p>
        </div>
    </div>
    {% endif %}
    
    <!-- Footer -->
    <div class="invoice-footer" style="margin-top: 30px; border-top: 1px solid #000; padding-top: 10px;">
        <div style="text-align: center; font-size: 12px;">
            {% if is_arabic %}
                <p>شكراً لتعاملكم معنا - Thank you for your business</p>
                <p>تم إنشاء هذه الفاتورة إلكترونياً ولا تتطلب توقيعاً</p>
            {% else %}
                <p>Thank you for your business - شكراً لتعاملكم معنا</p>
                <p>This is an electronically generated invoice and does not require a signature</p>
            {% endif %}
        </div>
        
        <!-- Terms and Conditions -->
        {% if doc.terms %}
        <div class="terms-section" style="margin-top: 15px; font-size: 11px;">
            <h4>{{ _("Terms and Conditions") }}{% if is_arabic %} - الشروط والأحكام{% endif %}</h4>
            <p>{{ doc.terms }}</p>
        </div>
        {% endif %}
    </div>
</div>
"""


def get_bilingual_invoice_css():
    """
    Get the CSS styles for bilingual invoice
    """
    return """
/* Universal Workshop Bilingual Invoice CSS */
.invoice-container {
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20px;
    color: #333;
    line-height: 1.4;
}

/* Arabic Font Support */
.invoice-container[dir="rtl"] {
    font-family: 'Tahoma', 'Arial Unicode MS', 'Segoe UI', sans-serif;
    text-align: right;
}

/* Header Styles */
.invoice-header {
    margin-bottom: 20px;
}

.company-section {
    border-bottom: 2px solid #000;
    padding-bottom: 15px;
    margin-bottom: 15px;
}

.company-name {
    font-size: 24px;
    font-weight: bold;
    margin: 0 0 10px 0;
    color: #1a73e8;
}

.company-address,
.company-contact {
    font-size: 12px;
    margin: 5px 0;
}

.tax-id {
    font-size: 14px;
    margin-top: 10px;
    padding: 5px;
    background-color: #f0f0f0;
    border-left: 3px solid #1a73e8;
}

.invoice-container[dir="rtl"] .tax-id {
    border-left: none;
    border-right: 3px solid #1a73e8;
}

/* Invoice Title */
.invoice-title h1 {
    font-size: 28px;
    font-weight: bold;
    margin: 0;
    color: #d32f2f;
}

/* Customer and Invoice Details */
.customer-details h3,
.invoice-details h3 {
    font-size: 16px;
    font-weight: bold;
    margin: 0 0 10px 0;
    color: #1a73e8;
    border-bottom: 1px solid #ddd;
    padding-bottom: 5px;
}

.customer-name {
    font-size: 16px;
    margin: 10px 0;
}

.customer-address,
.customer-tax-id {
    font-size: 12px;
    margin: 5px 0;
}

/* Items Table */
.items-table {
    font-size: 12px;
}

.items-table th {
    background-color: #1a73e8;
    color: white;
    font-weight: bold;
}

.items-table td,
.items-table th {
    border: 1px solid #000;
    padding: 8px;
}

.items-table tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* Totals Section */
.totals-section table {
    font-size: 14px;
}

.totals-section td:last-child {
    font-weight: bold;
}

/* QR Code Section */
.qr-code-section h4 {
    font-size: 14px;
    margin: 10px 0;
}

.qr-code-placeholder {
    min-height: 100px;
    background-color: #f9f9f9;
}

/* Footer */
.invoice-footer {
    font-size: 11px;
    color: #666;
}

.terms-section {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
}

/* Print Styles */
@media print {
    .invoice-container {
        max-width: none;
        padding: 10px;
    }
    
    .invoice-header,
    .items-section,
    .totals-section {
        break-inside: avoid;
    }
}

/* Mobile Responsive */
@media (max-width: 600px) {
    .invoice-container {
        padding: 10px;
        font-size: 12px;
    }
    
    .company-name {
        font-size: 18px;
    }
    
    .invoice-title h1 {
        font-size: 20px;
    }
    
    .items-table {
        font-size: 10px;
    }
}
"""
