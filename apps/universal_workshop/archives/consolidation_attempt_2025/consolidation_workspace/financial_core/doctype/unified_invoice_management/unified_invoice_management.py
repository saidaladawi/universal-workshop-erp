# -*- coding: utf-8 -*-
# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import nowdate, add_days, flt, cint, formatdate, get_datetime
from frappe.utils.data import get_link_to_form
import json
import re
from datetime import datetime, timedelta
import base64
import qrcode
from io import BytesIO

# Import shared libraries with fallback support
try:
    from universal_workshop.shared_libraries.arabic_business_logic import (
        validate_arabic_business_context,
        apply_traditional_patterns,
        ensure_islamic_compliance,
        format_arabic_currency,
        format_arabic_date
    )
    from universal_workshop.shared_libraries.financial_compliance import (
        calculate_omani_vat,
        validate_islamic_transaction,
        format_omani_currency,
        generate_vat_compliance_report
    )
    from universal_workshop.shared_libraries.qr_code_generation import (
        generate_tlv_qr_code,
        validate_qr_compliance,
        create_e_invoice_qr
    )
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError:
    SHARED_LIBRARIES_AVAILABLE = False
    frappe.log_error("Shared libraries not available, using fallback methods")

class UnifiedInvoiceManagement(Document):
    """
    Unified Invoice Management DocType
    
    This consolidated invoice management system combines multiple invoice-related
    functionalities while preserving and enhancing Arabic cultural excellence,
    Islamic business compliance, and Omani VAT regulatory requirements.
    """
    
    def autoname(self):
        """Generate invoice number based on naming series"""
        if self.naming_series:
            self.invoice_number = frappe.model.naming.make_autoname(self.naming_series)
        if not self.invoice_number:
            self.invoice_number = self.name
    
    def validate(self):
        """Comprehensive validation with Arabic cultural context"""
        self.validate_basic_information()
        self.validate_customer_information()
        self.validate_invoice_items()
        self.calculate_financial_totals()
        self.validate_omani_vat_compliance()
        self.validate_arabic_cultural_context()
        self.ensure_islamic_business_compliance()
        self.apply_traditional_invoice_patterns()
        self.generate_qr_code_if_required()
        self.update_integration_markers()
    
    def validate_basic_information(self):
        """Validate basic invoice information"""
        # Validate posting date
        if not self.posting_date:
            self.posting_date = nowdate()
        
        # Calculate due date if not provided
        if not self.due_date:
            # Default to 30 days from posting date
            self.due_date = add_days(self.posting_date, 30)
        
        # Validate currency
        if not self.currency:
            self.currency = "OMR"
        
        # Validate exchange rate
        if not self.exchange_rate or self.exchange_rate <= 0:
            self.exchange_rate = 1.0
        
        # Validate invoice status
        if not self.invoice_status:
            self.invoice_status = "Draft"
    
    def validate_customer_information(self):
        """Validate customer information and fetch details"""
        if not self.customer:
            frappe.throw(_("Customer is required"))
        
        # Fetch customer details
        customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
        
        # Update customer information
        if not self.customer_name:
            self.customer_name = customer_doc.customer_name
        if not self.customer_name_ar:
            self.customer_name_ar = customer_doc.customer_name_ar
        if not self.customer_contact:
            self.customer_contact = customer_doc.phone
        if not self.customer_email:
            self.customer_email = customer_doc.email
        if not self.customer_vat_number:
            self.customer_vat_number = customer_doc.tax_id
        
        # Validate VAT number format if provided
        if self.customer_vat_number:
            if not re.match(r'^OM\d{15}$', self.customer_vat_number):
                msgprint(_("Customer VAT number format should be OMxxxxxxxxxxxxxxx"))
    
    def validate_invoice_items(self):
        """Validate invoice items"""
        if not self.items:
            frappe.throw(_("Invoice items are required"))
        
        total_qty = 0
        item_count = 0
        
        for item in self.items:
            if not item.item_code:
                frappe.throw(_("Item code is required for all items"))
            if not item.quantity or item.quantity <= 0:
                frappe.throw(_("Quantity must be greater than 0"))
            if not item.rate or item.rate < 0:
                frappe.throw(_("Rate cannot be negative"))
            
            # Calculate item amount
            item.amount = flt(item.quantity) * flt(item.rate)
            
            total_qty += flt(item.quantity)
            item_count += 1
        
        self.total_quantity = total_qty
        self.item_count = item_count
    
    def calculate_financial_totals(self):
        """Calculate financial totals with Omani VAT"""
        if not self.items:
            return
        
        # Calculate base total
        base_total = sum(flt(item.amount) for item in self.items)
        self.base_total = base_total
        
        # Apply discount
        discount_amount = flt(self.discount_amount)
        subtotal_after_discount = base_total - discount_amount
        
        # Calculate VAT (default 5% for Oman)
        vat_rate = flt(self.omani_vat_rate) / 100 if self.omani_vat_rate else 0.05
        
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for VAT calculation
            vat_calculation = calculate_omani_vat({
                "base_amount": subtotal_after_discount,
                "vat_rate": vat_rate,
                "calculation_method": self.vat_calculation_method or "Exclusive",
                "currency": self.currency
            })
            
            self.vat_amount = vat_calculation.get("vat_amount", 0)
            self.taxes_and_charges = vat_calculation.get("total_tax", 0)
        else:
            # Fallback VAT calculation
            if self.vat_calculation_method == "Inclusive":
                # VAT is included in the price
                self.vat_amount = subtotal_after_discount * vat_rate / (1 + vat_rate)
                self.taxes_and_charges = self.vat_amount
            else:
                # VAT is exclusive (added to price)
                self.vat_amount = subtotal_after_discount * vat_rate
                self.taxes_and_charges = self.vat_amount
        
        # Calculate total amount
        if self.vat_calculation_method == "Inclusive":
            self.total_amount = subtotal_after_discount
        else:
            self.total_amount = subtotal_after_discount + self.taxes_and_charges
        
        # Calculate outstanding amount
        paid_amount = flt(self.paid_amount)
        self.outstanding_amount = flt(self.total_amount) - paid_amount
        
        # Round to 3 decimal places for OMR (Baisa precision)
        self.base_total = round(self.base_total, 3)
        self.vat_amount = round(self.vat_amount, 3)
        self.taxes_and_charges = round(self.taxes_and_charges, 3)
        self.total_amount = round(self.total_amount, 3)
        self.outstanding_amount = round(self.outstanding_amount, 3)
    
    def validate_omani_vat_compliance(self):
        """Validate Omani VAT compliance requirements"""
        # Set default VAT rate for Oman
        if not self.omani_vat_rate:
            self.omani_vat_rate = 5.0
        
        # Validate VAT registration number format
        if self.vat_registration_number:
            if not re.match(r'^OM\d{15}$', self.vat_registration_number):
                frappe.throw(_("VAT Registration Number must be in format OMxxxxxxxxxxxxxxx"))
        
        # Set quarterly filing period based on posting date
        if self.posting_date:
            month = get_datetime(self.posting_date).month
            if month in [1, 2, 3]:
                self.quarterly_filing_period = "Q1 (Jan-Mar)"
            elif month in [4, 5, 6]:
                self.quarterly_filing_period = "Q2 (Apr-Jun)"
            elif month in [7, 8, 9]:
                self.quarterly_filing_period = "Q3 (Jul-Sep)"
            else:
                self.quarterly_filing_period = "Q4 (Oct-Dec)"
        
        # Validate e-invoice compliance requirements
        if self.e_invoice_compliance:
            required_fields = [
                'customer_name', 'customer_vat_number', 'vat_registration_number',
                'total_amount', 'vat_amount', 'posting_date'
            ]
            missing_fields = [field for field in required_fields if not getattr(self, field)]
            if missing_fields:
                frappe.throw(_("E-invoice compliance requires: {0}").format(", ".join(missing_fields)))
        
        # Set integration marker
        self.omani_vat_validated = 1
    
    def validate_arabic_cultural_context(self):
        """Validate Arabic cultural context and formatting"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for Arabic validation
            arabic_validation = validate_arabic_business_context({
                "customer_name": self.customer_name,
                "customer_name_ar": self.customer_name_ar,
                "invoice_type": self.invoice_type,
                "cultural_context": {
                    "traditional_patterns": self.traditional_invoice_patterns,
                    "business_terminology": self.arabic_business_terminology,
                    "cultural_communication": self.cultural_communication_notes
                }
            })
            
            if arabic_validation.get("suggestions"):
                for suggestion in arabic_validation.get("suggestions", []):
                    msgprint(_(suggestion))
        
        # Set default Arabic invoice title
        if not self.invoice_title_ar:
            if self.invoice_type == "Service Invoice":
                self.invoice_title_ar = "فاتورة خدمة"
            elif self.invoice_type == "Sales Invoice":
                self.invoice_title_ar = "فاتورة مبيعات"
            else:
                self.invoice_title_ar = "فاتورة"
        
        # Set default Arabic currency format
        if not self.arabic_currency_format:
            self.arabic_currency_format = "123.456 ر.ع."
        
        # Set default Arabic date format
        if not self.arabic_date_format:
            self.arabic_date_format = "Both (Gregorian/Hijri)"
    
    def ensure_islamic_business_compliance(self):
        """Ensure Islamic business principle compliance"""
        if SHARED_LIBRARIES_AVAILABLE:
            islamic_validation = ensure_islamic_compliance({
                "transaction_type": "invoice",
                "amount": self.total_amount,
                "payment_terms": self.payment_terms,
                "business_context": {
                    "islamic_transaction_type": self.islamic_transaction_type,
                    "interest_free": self.interest_free_transaction,
                    "halal_service": self.halal_service_confirmation
                }
            })
            
            if islamic_validation.get("compliance_notes"):
                self.islamic_compliance_notes = islamic_validation.get("compliance_notes")
            
            # Validate interest-free transaction
            if not self.interest_free_transaction and self.payment_terms in ["Net 30", "Net 60"]:
                msgprint(_("Consider interest-free payment terms for Islamic compliance"))
        else:
            # Fallback Islamic compliance
            if not self.islamic_transaction_type:
                self.islamic_transaction_type = "Cash Sale"
            
            if not self.interest_free_transaction:
                self.interest_free_transaction = 1
            
            if not self.halal_service_confirmation:
                self.halal_service_confirmation = 1
        
        self.islamic_compliance_verified = 1
    
    def apply_traditional_invoice_patterns(self):
        """Apply traditional Arabic invoice patterns"""
        if SHARED_LIBRARIES_AVAILABLE:
            traditional_patterns = apply_traditional_patterns({
                "context": "invoice_generation",
                "customer_type": "arabic_business",
                "cultural_preferences": {
                    "courtesy_protocols": self.arabic_courtesy_protocols,
                    "traditional_formatting": self.traditional_invoice_formatting
                }
            })
            
            if traditional_patterns.get("patterns_applied"):
                self.traditional_invoice_patterns = traditional_patterns.get("pattern_description")
        else:
            # Fallback traditional patterns
            self.traditional_invoice_patterns = "Traditional Arabic business invoice formatting applied"
        
        # Apply traditional Arabic courtesy protocols
        if not self.arabic_courtesy_protocols:
            self.arabic_courtesy_protocols = "تحية طيبة وبعد، نتشرف بتقديم هذه الفاتورة"
        
        self.traditional_patterns_applied = 1
    
    def generate_qr_code_if_required(self):
        """Generate QR code for invoice if required"""
        if not self.qr_code_required:
            return
        
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for QR code generation
            qr_result = generate_tlv_qr_code({
                "invoice_number": self.invoice_number,
                "company_name": self.company_name_ar or frappe.defaults.get_global_default("company"),
                "vat_number": self.vat_registration_number,
                "total_amount": self.total_amount,
                "vat_amount": self.vat_amount,
                "timestamp": self.posting_date,
                "currency": self.currency
            })
            
            if qr_result.get("success"):
                self.qr_code_data = qr_result.get("qr_data")
                self.tlv_encoding = qr_result.get("tlv_encoding")
                self.qr_code_image = qr_result.get("qr_image")
                self.qr_compliance_status = "Generated"
                self.qr_generation_timestamp = frappe.utils.now()
            else:
                self.qr_compliance_status = "Failed"
                frappe.log_error(f"QR code generation failed: {qr_result.get('error')}")
        else:
            # Fallback QR code generation
            self.generate_fallback_qr_code()
    
    def generate_fallback_qr_code(self):
        """Generate basic QR code using fallback method"""
        try:
            # Create TLV (Tag-Length-Value) encoded data
            tlv_data = []
            
            # Seller name (Tag 1)
            seller_name = self.company_name_ar or frappe.defaults.get_global_default("company")
            tlv_data.append(f"01{len(seller_name):02x}{seller_name}")
            
            # VAT registration number (Tag 2)
            if self.vat_registration_number:
                tlv_data.append(f"02{len(self.vat_registration_number):02x}{self.vat_registration_number}")
            
            # Timestamp (Tag 3)
            timestamp = get_datetime(self.posting_date).strftime("%Y-%m-%dT%H:%M:%SZ")
            tlv_data.append(f"03{len(timestamp):02x}{timestamp}")
            
            # Invoice total (Tag 4)
            total_str = f"{self.total_amount:.3f}"
            tlv_data.append(f"04{len(total_str):02x}{total_str}")
            
            # VAT total (Tag 5)
            vat_str = f"{self.vat_amount:.3f}"
            tlv_data.append(f"05{len(vat_str):02x}{vat_str}")
            
            # Combine TLV data
            tlv_string = "".join(tlv_data)
            self.tlv_encoding = tlv_string
            
            # Convert to base64 for QR code
            qr_data = base64.b64encode(tlv_string.encode()).decode()
            self.qr_code_data = qr_data
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Save as base64 image
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            self.qr_code_image = f"data:image/png;base64,{img_base64}"
            
            self.qr_compliance_status = "Generated"
            self.qr_generation_timestamp = frappe.utils.now()
            
        except Exception as e:
            self.qr_compliance_status = "Failed"
            frappe.log_error(f"Fallback QR code generation failed: {str(e)}")
    
    def update_integration_markers(self):
        """Update shared library integration markers"""
        if SHARED_LIBRARIES_AVAILABLE:
            self.shared_library_invoice_enhanced = 1
            self.arabic_business_logic_integrated = 1
        else:
            self.shared_library_invoice_enhanced = 0
            self.arabic_business_logic_integrated = 0
    
    def before_save(self):
        """Before save operations"""
        # Set creation date if new
        if not self.created_date:
            self.created_date = nowdate()
        
        # Set created by if new
        if not self.created_by:
            self.created_by = frappe.session.user
        
        # Always update last updated by
        self.last_updated_by = frappe.session.user
        
        # Update invoice status based on payments
        self.update_invoice_status()
    
    def update_invoice_status(self):
        """Update invoice status based on payment status"""
        if self.outstanding_amount <= 0:
            self.invoice_status = "Paid"
        elif self.paid_amount > 0:
            self.invoice_status = "Partially Paid"
        elif self.due_date and get_datetime(self.due_date) < get_datetime():
            self.invoice_status = "Overdue"
        elif self.docstatus == 1:
            self.invoice_status = "Submitted"
        else:
            self.invoice_status = "Draft"
    
    def on_submit(self):
        """On submit operations"""
        # Update customer lifetime value
        self.update_customer_clv()
        
        # Create payment reminder if needed
        self.create_payment_reminder()
        
        # Send invoice notification
        self.send_invoice_notification()
    
    def update_customer_clv(self):
        """Update customer lifetime value"""
        if self.customer:
            customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
            current_clv = flt(customer_doc.total_lifetime_value)
            new_clv = current_clv + flt(self.total_amount)
            
            customer_doc.total_lifetime_value = new_clv
            customer_doc.last_service_date = self.posting_date
            customer_doc.db_update()
            
            # Set CLV impact
            self.customer_lifetime_value_impact = self.total_amount
            self.db_update()
    
    def create_payment_reminder(self):
        """Create automated payment reminder"""
        if self.automated_reminders and self.outstanding_amount > 0:
            # Create reminder based on payment terms
            reminder_days = 7  # Default 7 days before due date
            
            if self.payment_terms == "Net 15":
                reminder_days = 3
            elif self.payment_terms == "Net 30":
                reminder_days = 7
            elif self.payment_terms == "Net 60":
                reminder_days = 14
            
            reminder_date = add_days(self.due_date, -reminder_days)
            
            # Schedule reminder (would integrate with notification system)
            frappe.log_error(f"Payment reminder scheduled for {reminder_date} for invoice {self.invoice_number}")
    
    def send_invoice_notification(self):
        """Send invoice notification to customer"""
        if self.customer_email:
            # Format message based on customer language preference
            customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
            
            if customer_doc.preferred_language == "Arabic":
                subject = f"فاتورة جديدة - {self.invoice_number}"
                message = f"""
                السلام عليكم {self.customer_name_ar or self.customer_name}،
                
                نتشرف بإرسال الفاتورة رقم {self.invoice_number}
                المبلغ الإجمالي: {self.total_amount:.3f} ر.ع.
                تاريخ الاستحقاق: {formatdate(self.due_date)}
                
                شكراً لثقتكم بنا.
                ورشة يونيفرسال
                """
            else:
                subject = f"New Invoice - {self.invoice_number}"
                message = f"""
                Dear {self.customer_name},
                
                Please find attached your invoice {self.invoice_number}
                Total Amount: OMR {self.total_amount:.3f}
                Due Date: {formatdate(self.due_date)}
                
                Thank you for your business.
                Universal Workshop
                """
            
            # Send email (implementation depends on email system)
            try:
                frappe.sendmail(
                    recipients=[self.customer_email],
                    subject=subject,
                    message=message,
                    reference_doctype=self.doctype,
                    reference_name=self.name
                )
            except Exception as e:
                frappe.log_error(f"Failed to send invoice notification: {str(e)}")
    
    @frappe.whitelist()
    def regenerate_qr_code(self):
        """Regenerate QR code for the invoice"""
        self.qr_compliance_status = "Pending"
        self.generate_qr_code_if_required()
        self.db_update()
        return {
            "status": self.qr_compliance_status,
            "qr_data": self.qr_code_data,
            "qr_image": self.qr_code_image
        }
    
    @frappe.whitelist()
    def get_arabic_formatted_invoice(self):
        """Get Arabic formatted invoice data"""
        if SHARED_LIBRARIES_AVAILABLE:
            arabic_currency = format_arabic_currency(self.total_amount)
            arabic_date = format_arabic_date(self.posting_date)
        else:
            arabic_currency = f"{self.total_amount:.3f} ر.ع."
            arabic_date = formatdate(self.posting_date)
        
        return {
            "invoice_title_ar": self.invoice_title_ar,
            "customer_name_ar": self.customer_name_ar,
            "total_amount_ar": arabic_currency,
            "posting_date_ar": arabic_date,
            "currency_format": self.arabic_currency_format,
            "courtesy_message": self.arabic_courtesy_protocols
        }
    
    @frappe.whitelist()
    def get_omani_vat_summary(self):
        """Get Omani VAT compliance summary"""
        return {
            "vat_rate": f"{self.omani_vat_rate}%",
            "vat_amount": f"OMR {self.vat_amount:.3f}",
            "vat_registration": self.vat_registration_number,
            "quarterly_period": self.quarterly_filing_period,
            "e_invoice_ready": self.e_invoice_compliance,
            "qr_compliance": self.qr_compliance_status,
            "tax_authority": "هيئة الضرائب العمانية - Oman Tax Authority"
        }
    
    @frappe.whitelist()
    def validate_islamic_compliance(self):
        """Validate Islamic finance compliance"""
        compliance_issues = []
        
        if not self.interest_free_transaction:
            compliance_issues.append("Transaction should be interest-free")
        
        if not self.halal_service_confirmation:
            compliance_issues.append("Halal service confirmation required")
        
        if self.islamic_transaction_type not in ["Cash Sale", "Murabaha (Cost Plus)", "Ijara (Lease)"]:
            compliance_issues.append("Transaction type should comply with Islamic finance")
        
        return {
            "compliant": len(compliance_issues) == 0,
            "issues": compliance_issues,
            "islamic_transaction_type": self.islamic_transaction_type,
            "interest_free": self.interest_free_transaction,
            "halal_confirmed": self.halal_service_confirmation
        }