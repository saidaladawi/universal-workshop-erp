"""
Print Format Manager
Handles automatic injection of branding into print formats and template management
"""

import frappe
from frappe import _
from frappe.utils import get_url
import os
import json
from .branding_utils import PrintBrandingManager, get_print_branding_context


class PrintFormatManager:
    """Manages print format templates and branding integration"""

    def __init__(self):
        self.branding_manager = PrintBrandingManager()

    def get_branded_print_formats(self):
        """Get list of available branded print formats"""
        return [
            {
                "name": "Universal Workshop Invoice",
                "doctype": "Sales Invoice",
                "template": "workshop_invoice.html",
                "supports_arabic": True,
            },
            {
                "name": "Universal Workshop Quotation",
                "doctype": "Quotation",
                "template": "workshop_quotation.html",
                "supports_arabic": True,
            },
            {
                "name": "Universal Workshop Service Order",
                "doctype": "Service Order",
                "template": "workshop_service_order.html",
                "supports_arabic": True,
            },
            {
                "name": "Universal Workshop Receipt",
                "doctype": "Payment Entry",
                "template": "workshop_receipt.html",
                "supports_arabic": True,
            },
            {
                "name": "Universal Workshop Delivery Note",
                "doctype": "Delivery Note",
                "template": "workshop_delivery_note.html",
                "supports_arabic": True,
            },
            {
                "name": "Universal Workshop Purchase Order",
                "doctype": "Purchase Order",
                "template": "workshop_purchase_order.html",
                "supports_arabic": True,
            },
        ]

    def create_branded_print_format(
        self, doctype, format_name, template_content, supports_arabic=True
    ):
        """Create a new branded print format"""
        try:
            # Check if print format already exists
            if frappe.db.exists("Print Format", format_name):
                print_format = frappe.get_doc("Print Format", format_name)
            else:
                print_format = frappe.new_doc("Print Format")
                print_format.name = format_name
                print_format.doc_type = doctype

            # Update print format with branded template
            print_format.standard = "No"
            print_format.custom_format = 1
            print_format.html = self.inject_branding_into_template(
                template_content, supports_arabic
            )
            print_format.css = self.generate_print_format_css()

            # Set print format properties
            print_format.margin_top = 15
            print_format.margin_bottom = 15
            print_format.margin_left = 15
            print_format.margin_right = 15

            print_format.save()
            return print_format.name

        except Exception as e:
            frappe.log_error(f"Error creating branded print format: {e}")
            return None

    def inject_branding_into_template(self, template_content, supports_arabic=True):
        """Inject branding elements into print format template"""
        branding_context = get_print_branding_context()

        # Base template with branding injection
        branded_template = f"""
        {{% set branding_context = get_print_branding_context() %}}
        {{% set language = frappe.local.lang or 'en' %}}
        {{% set is_arabic = language == 'ar' %}}
        
        <!-- Workshop Branding CSS -->
        {{{{ branding_context.print_css | safe }}}}
        
        <!-- Document Container -->
        <div class="print-format" {{% if is_arabic %}}dir="rtl"{{% endif %}}>
            
            <!-- Workshop Header -->
            {{{{ branding_context.header_html | safe }}}}
            
            <!-- Document Content -->
            <div class="document-content">
                {template_content}
            </div>
            
            <!-- Workshop Footer -->
            {{{{ branding_context.footer_html | safe }}}}
            
        </div>
        
        <!-- JavaScript for dynamic branding -->
        <script>
        // Apply dynamic branding after page load
        document.addEventListener('DOMContentLoaded', function() {{
            // Update colors based on current theme
            var primaryColor = '{branding_context['branding']['primary_color']}';
            var secondaryColor = '{branding_context['branding']['secondary_color']}';
            
            // Apply colors to dynamic elements
            var style = document.createElement('style');
            style.textContent = `
                .dynamic-primary {{ color: ${{primaryColor}} !important; }}
                .dynamic-secondary {{ color: ${{secondaryColor}} !important; }}
                .dynamic-primary-bg {{ background-color: ${{primaryColor}} !important; }}
                .dynamic-secondary-bg {{ background-color: ${{secondaryColor}} !important; }}
            `;
            document.head.appendChild(style);
        }});
        </script>
        """

        return branded_template

    def generate_print_format_css(self):
        """Generate CSS for print formats"""
        return self.branding_manager.generate_print_css()

    def update_all_print_formats(self):
        """Update all existing print formats with current branding"""
        try:
            branded_formats = self.get_branded_print_formats()
            updated_count = 0

            for format_info in branded_formats:
                try:
                    # Load template content
                    template_path = f"apps/universal_workshop/universal_workshop/templates/print_formats/{format_info['template']}"
                    if os.path.exists(template_path):
                        with open(template_path, "r", encoding="utf-8") as f:
                            template_content = f.read()

                        # Update print format
                        format_name = self.create_branded_print_format(
                            format_info["doctype"],
                            format_info["name"],
                            template_content,
                            format_info["supports_arabic"],
                        )

                        if format_name:
                            updated_count += 1

                except Exception as e:
                    frappe.log_error(f"Error updating print format {format_info['name']}: {e}")

            return updated_count

        except Exception as e:
            frappe.log_error(f"Error updating print formats: {e}")
            return 0

    def install_default_print_formats(self):
        """Install default branded print formats"""
        try:
            installed_count = 0

            # Create default templates if they don't exist
            self.create_default_templates()

            # Install each print format
            branded_formats = self.get_branded_print_formats()

            for format_info in branded_formats:
                try:
                    template_content = self.get_default_template_content(format_info["doctype"])

                    format_name = self.create_branded_print_format(
                        format_info["doctype"],
                        format_info["name"],
                        template_content,
                        format_info["supports_arabic"],
                    )

                    if format_name:
                        installed_count += 1

                except Exception as e:
                    frappe.log_error(f"Error installing print format {format_info['name']}: {e}")

            return installed_count

        except Exception as e:
            frappe.log_error(f"Error installing default print formats: {e}")
            return 0

    def create_default_templates(self):
        """Create default print format templates"""
        templates_dir = "apps/universal_workshop/universal_workshop/templates/print_formats"

        # Ensure directory exists
        os.makedirs(templates_dir, exist_ok=True)

        # Default templates for each document type
        templates = {
            "workshop_invoice.html": self.get_invoice_template(),
            "workshop_quotation.html": self.get_quotation_template(),
            "workshop_service_order.html": self.get_service_order_template(),
            "workshop_receipt.html": self.get_receipt_template(),
            "workshop_delivery_note.html": self.get_delivery_note_template(),
            "workshop_purchase_order.html": self.get_purchase_order_template(),
        }

        for filename, content in templates.items():
            template_path = os.path.join(templates_dir, filename)
            if not os.path.exists(template_path):
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)

    def get_default_template_content(self, doctype):
        """Get default template content for a document type"""
        templates = {
            "Sales Invoice": self.get_invoice_template(),
            "Quotation": self.get_quotation_template(),
            "Service Order": self.get_service_order_template(),
            "Payment Entry": self.get_receipt_template(),
            "Delivery Note": self.get_delivery_note_template(),
            "Purchase Order": self.get_purchase_order_template(),
        }

        return templates.get(doctype, self.get_generic_template())

    def get_invoice_template(self):
        """Get invoice print template"""
        return """
        <!-- Invoice Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}فاتورة{% else %}INVOICE{% endif %}
        </h2>
        
        <!-- Invoice Details -->
        <div class="invoice-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}إلى:{% else %}To:{% endif %}</strong><br>
                        {{ doc.customer_name }}<br>
                        {% if doc.customer_address %}{{ doc.customer_address }}{% endif %}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم الفاتورة:{% else %}Invoice #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.posting_date }}<br>
                        {% if doc.due_date %}<strong>{% if is_arabic %}تاريخ الاستحقاق:{% else %}Due Date:{% endif %}</strong> {{ doc.due_date }}{% endif %}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Items Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الصنف{% else %}Item{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الكمية{% else %}Qty{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}السعر{% else %}Rate{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}المجموع{% else %}Amount{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.item_name }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{{ item.qty }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.rate }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.amount }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Totals Section -->
        <div class="total-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%;"></td>
                    <td style="width: 30%;">
                        <table style="width: 100%;">
                            <tr>
                                <td><strong>{% if is_arabic %}المجموع الفرعي:{% else %}Subtotal:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total }}</strong></td>
                            </tr>
                            {% if doc.total_taxes_and_charges %}
                            <tr>
                                <td><strong>{% if is_arabic %}الضريبة:{% else %}Tax:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total_taxes_and_charges }}</strong></td>
                            </tr>
                            {% endif %}
                            <tr style="border-top: 2px solid #333;">
                                <td><strong>{% if is_arabic %}المجموع الإجمالي:{% else %}Grand Total:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.grand_total }}</strong></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        """

    def get_quotation_template(self):
        """Get quotation print template"""
        return """
        <!-- Quotation Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}عرض أسعار{% else %}QUOTATION{% endif %}
        </h2>
        
        <!-- Quotation Details -->
        <div class="quotation-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}إلى:{% else %}To:{% endif %}</strong><br>
                        {{ doc.customer_name }}<br>
                        {% if doc.customer_address %}{{ doc.customer_address }}{% endif %}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم العرض:{% else %}Quotation #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.transaction_date }}<br>
                        {% if doc.valid_till %}<strong>{% if is_arabic %}صالح حتى:{% else %}Valid Till:{% endif %}</strong> {{ doc.valid_till }}{% endif %}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Items Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الخدمة/الصنف{% else %}Service/Item{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الوصف{% else %}Description{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الكمية{% else %}Qty{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}السعر{% else %}Rate{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}المجموع{% else %}Amount{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.item_name }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.description or '' }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{{ item.qty }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.rate }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.amount }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Terms and Conditions -->
        {% if doc.terms %}
        <div style="margin-top: 20px;">
            <h4>{% if is_arabic %}الشروط والأحكام:{% else %}Terms and Conditions:{% endif %}</h4>
            <div style="font-size: 12px;">{{ doc.terms }}</div>
        </div>
        {% endif %}
        
        <!-- Totals Section -->
        <div class="total-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%;"></td>
                    <td style="width: 30%;">
                        <table style="width: 100%;">
                            <tr>
                                <td><strong>{% if is_arabic %}المجموع الفرعي:{% else %}Subtotal:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total }}</strong></td>
                            </tr>
                            {% if doc.total_taxes_and_charges %}
                            <tr>
                                <td><strong>{% if is_arabic %}الضريبة:{% else %}Tax:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total_taxes_and_charges }}</strong></td>
                            </tr>
                            {% endif %}
                            <tr style="border-top: 2px solid #333;">
                                <td><strong>{% if is_arabic %}المجموع الإجمالي:{% else %}Grand Total:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.grand_total }}</strong></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        """

    def get_service_order_template(self):
        """Get service order print template"""
        return """
        <!-- Service Order Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}أمر خدمة{% else %}SERVICE ORDER{% endif %}
        </h2>
        
        <!-- Service Order Details -->
        <div class="service-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}العميل:{% else %}Customer:{% endif %}</strong><br>
                        {{ doc.customer_name }}<br>
                        {% if doc.vehicle_number %}<strong>{% if is_arabic %}رقم المركبة:{% else %}Vehicle:{% endif %}</strong> {{ doc.vehicle_number }}{% endif %}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم الأمر:{% else %}Order #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.posting_date }}<br>
                        <strong>{% if is_arabic %}الحالة:{% else %}Status:{% endif %}</strong> {{ doc.status }}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Services Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الخدمة{% else %}Service{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الوصف{% else %}Description{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الفني{% else %}Technician{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}التكلفة{% else %}Cost{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for service in doc.services %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ service.service_name }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ service.description or '' }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ service.technician or '' }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ service.cost or '' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Instructions -->
        {% if doc.instructions %}
        <div style="margin-top: 20px;">
            <h4>{% if is_arabic %}تعليمات خاصة:{% else %}Special Instructions:{% endif %}</h4>
            <div style="font-size: 12px; border: 1px solid #ddd; padding: 10px;">{{ doc.instructions }}</div>
        </div>
        {% endif %}
        """

    def get_receipt_template(self):
        """Get receipt print template"""
        return """
        <!-- Receipt Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}إيصال دفع{% else %}PAYMENT RECEIPT{% endif %}
        </h2>
        
        <!-- Receipt Details -->
        <div class="receipt-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}المستلم من:{% else %}Received From:{% endif %}</strong><br>
                        {{ doc.party_name }}<br>
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم الإيصال:{% else %}Receipt #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.posting_date }}<br>
                        <strong>{% if is_arabic %}طريقة الدفع:{% else %}Payment Method:{% endif %}</strong> {{ doc.mode_of_payment }}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Payment Details -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}البيان{% else %}Description{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}المبلغ{% else %}Amount{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for reference in doc.references %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        {% if is_arabic %}دفعة مقابل{% else %}Payment against{% endif %} {{ reference.reference_doctype }} {{ reference.reference_name }}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ reference.allocated_amount }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Total Amount -->
        <div class="total-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%;"></td>
                    <td style="width: 30%;">
                        <table style="width: 100%;">
                            <tr style="border-top: 2px solid #333;">
                                <td><strong>{% if is_arabic %}إجمالي المبلغ المستلم:{% else %}Total Amount Received:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.paid_amount }}</strong></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        """

    def get_delivery_note_template(self):
        """Get delivery note print template"""
        return """
        <!-- Delivery Note Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}إشعار تسليم{% else %}DELIVERY NOTE{% endif %}
        </h2>
        
        <!-- Delivery Details -->
        <div class="delivery-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}التسليم إلى:{% else %}Deliver To:{% endif %}</strong><br>
                        {{ doc.customer_name }}<br>
                        {% if doc.shipping_address_name %}{{ doc.shipping_address_name }}{% endif %}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم الإشعار:{% else %}Delivery Note #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.posting_date }}<br>
                        {% if doc.lr_no %}<strong>{% if is_arabic %}رقم النقل:{% else %}LR No:{% endif %}</strong> {{ doc.lr_no }}{% endif %}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Items Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الصنف{% else %}Item{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الوصف{% else %}Description{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الكمية{% else %}Qty{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الوحدة{% else %}UOM{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.item_name }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.description or '' }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{{ item.qty }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{{ item.uom }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Signature Section -->
        <div style="margin-top: 40px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 50%; text-align: center; border-top: 1px solid #333; padding-top: 10px;">
                        {% if is_arabic %}توقيع المستلم{% else %}Receiver's Signature{% endif %}
                    </td>
                    <td style="width: 50%; text-align: center; border-top: 1px solid #333; padding-top: 10px;">
                        {% if is_arabic %}توقيع المخول{% else %}Authorized Signature{% endif %}
                    </td>
                </tr>
            </table>
        </div>
        """

    def get_purchase_order_template(self):
        """Get purchase order print template"""
        return """
        <!-- Purchase Order Document Title -->
        <h2 class="document-title">
            {% if is_arabic %}أمر شراء{% else %}PURCHASE ORDER{% endif %}
        </h2>
        
        <!-- Purchase Order Details -->
        <div class="purchase-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}إلى:{% else %}To:{% endif %}</strong><br>
                        {{ doc.supplier_name }}<br>
                        {% if doc.supplier_address %}{{ doc.supplier_address }}{% endif %}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        <strong>{% if is_arabic %}رقم الأمر:{% else %}PO #:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.transaction_date }}<br>
                        {% if doc.schedule_date %}<strong>{% if is_arabic %}تاريخ التسليم:{% else %}Delivery Date:{% endif %}</strong> {{ doc.schedule_date }}{% endif %}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Items Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr class="table-header">
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الصنف{% else %}Item{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الوصف{% else %}Description{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}الكمية{% else %}Qty{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}السعر{% else %}Rate{% endif %}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{% if is_arabic %}المجموع{% else %}Amount{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr class="table-row">
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.item_name }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ item.description or '' }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{{ item.qty }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.rate }}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.amount }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <!-- Terms and Conditions -->
        {% if doc.terms %}
        <div style="margin-top: 20px;">
            <h4>{% if is_arabic %}الشروط والأحكام:{% else %}Terms and Conditions:{% endif %}</h4>
            <div style="font-size: 12px;">{{ doc.terms }}</div>
        </div>
        {% endif %}
        
        <!-- Totals Section -->
        <div class="total-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%;"></td>
                    <td style="width: 30%;">
                        <table style="width: 100%;">
                            <tr>
                                <td><strong>{% if is_arabic %}المجموع الفرعي:{% else %}Subtotal:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total }}</strong></td>
                            </tr>
                            {% if doc.total_taxes_and_charges %}
                            <tr>
                                <td><strong>{% if is_arabic %}الضريبة:{% else %}Tax:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.total_taxes_and_charges }}</strong></td>
                            </tr>
                            {% endif %}
                            <tr style="border-top: 2px solid #333;">
                                <td><strong>{% if is_arabic %}المجموع الإجمالي:{% else %}Grand Total:{% endif %}</strong></td>
                                <td style="text-align: right;"><strong>{{ doc.grand_total }}</strong></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        """

    def get_generic_template(self):
        """Get generic print template for unknown document types"""
        return """
        <!-- Generic Document Title -->
        <h2 class="document-title">
            {{ doc.doctype.upper() }}
        </h2>
        
        <!-- Document Details -->
        <div class="document-details" style="margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{% if is_arabic %}الوثيقة:{% else %}Document:{% endif %}</strong> {{ doc.name }}<br>
                        <strong>{% if is_arabic %}التاريخ:{% else %}Date:{% endif %}</strong> {{ doc.creation.date() if doc.creation else '' }}
                    </td>
                    <td style="width: 50%; vertical-align: top; text-align: {% if is_arabic %}left{% else %}right{% endif %};">
                        {% if doc.get('status') %}
                        <strong>{% if is_arabic %}الحالة:{% else %}Status:{% endif %}</strong> {{ doc.status }}
                        {% endif %}
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Document Content -->
        <div class="document-content">
            <!-- Add specific content based on document type -->
            {% if doc.get('description') %}
            <p><strong>{% if is_arabic %}الوصف:{% else %}Description:{% endif %}</strong></p>
            <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 20px;">
                {{ doc.description }}
            </div>
            {% endif %}
        </div>
        """


# API Functions
@frappe.whitelist()
def install_branded_print_formats():
    """Install all branded print formats"""
    try:
        manager = PrintFormatManager()
        installed_count = manager.install_default_print_formats()

        return {
            "success": True,
            "message": f"Successfully installed {installed_count} branded print formats",
            "installed_count": installed_count,
        }

    except Exception as e:
        frappe.log_error(f"Error installing branded print formats: {e}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def update_print_formats_branding():
    """Update all print formats with current branding"""
    try:
        manager = PrintFormatManager()
        updated_count = manager.update_all_print_formats()

        return {
            "success": True,
            "message": f"Successfully updated {updated_count} print formats with current branding",
            "updated_count": updated_count,
        }

    except Exception as e:
        frappe.log_error(f"Error updating print formats branding: {e}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_available_print_formats():
    """Get list of available branded print formats"""
    try:
        manager = PrintFormatManager()
        formats = manager.get_branded_print_formats()

        return {"success": True, "formats": formats}

    except Exception as e:
        frappe.log_error(f"Error getting available print formats: {e}")
        return {"success": False, "message": str(e)}
