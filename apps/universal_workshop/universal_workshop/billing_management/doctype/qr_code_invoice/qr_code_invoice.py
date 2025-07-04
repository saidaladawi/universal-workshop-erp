# -*- coding: utf-8 -*-
# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, flt
from universal_workshop.billing_management.qr_code_generator import OmanEInvoiceQRGenerator


class QRCodeInvoice(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields
    
    def before_insert(self):
        """Set defaults before inserting"""
        self.generated_by = frappe.session.user
        self.generated_on = now_datetime()
        self.invoice_status = "Draft"
        
    def before_save(self):
        """Validate and generate QR code before saving"""
        self.validate_sales_invoice()
        self.extract_invoice_data()
        
    def after_insert(self):
        """Generate QR code after successful insert"""
        if self.invoice_status == "Draft":
            self.generate_qr_code()
            
    def validate_sales_invoice(self):
        """Validate that Sales Invoice exists and is submitted"""
        if not self.sales_invoice:
            frappe.throw(_("Sales Invoice is required"))
            
        if not frappe.db.exists("Sales Invoice", self.sales_invoice):
            frappe.throw(_("Sales Invoice {0} does not exist").format(self.sales_invoice))
            
        sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
        if sales_invoice.docstatus != 1:
            frappe.throw(_("Sales Invoice must be submitted to generate QR code"))
            
        # Check if QR code already exists for this invoice
        existing_qr = frappe.db.exists("QR Code Invoice", {
            "sales_invoice": self.sales_invoice,
            "name": ["!=", self.name]
        })
        
        if existing_qr:
            frappe.throw(_("QR Code Invoice already exists for Sales Invoice {0}").format(self.sales_invoice))
    
    def extract_invoice_data(self):
        """Extract data from Sales Invoice for QR generation"""
        if not self.sales_invoice:
            return
            
        sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
        
        # Set basic information
        self.company = sales_invoice.company
        self.customer = sales_invoice.customer
        self.posting_date = sales_invoice.posting_date
        self.invoice_total = flt(sales_invoice.grand_total, 3)
        self.vat_amount = flt(sales_invoice.total_taxes_and_charges or 0, 3)
        
        # Get company information for seller name and VAT
        company_doc = frappe.get_doc("Company", sales_invoice.company)
        self.seller_name = getattr(company_doc, "company_name_ar", None) or company_doc.company_name
        self.vat_number = getattr(company_doc, "vat_number", "") or getattr(company_doc, "tax_id", "")
        
        # Format VAT number for Oman
        if self.vat_number and not self.vat_number.startswith("OM"):
            self.vat_number = f"OM{self.vat_number}"
            
        # Set compliance status
        self.oman_vat_compliance = 1 if self.vat_number else 0
    
    def generate_qr_code(self):
        """Generate QR code using the existing generator"""
        try:
            self.invoice_status = "Pending"
            self.save(ignore_permissions=True)
            
            # Get the Sales Invoice document
            sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
            
            # Use existing QR generator
            qr_generator = OmanEInvoiceQRGenerator()
            result = qr_generator.generate_qr_code_for_invoice(sales_invoice)
            
            if result.get("success"):
                # Update QR code fields
                self.qr_code_data = result.get("tlv_data")
                self.qr_code_image = result.get("qr_code_image")
                self.tlv_encoded = 1
                self.invoice_status = "Generated"
                self.compliance_status = "Compliant"
                self.error_log = ""
                
                # Update timestamp
                from frappe.utils import format_datetime, now_datetime
                invoice_data = result.get("invoice_data", {})
                self.invoice_timestamp = invoice_data.get("invoice_timestamp")
                
            else:
                # Handle errors
                self.invoice_status = "Error"
                self.compliance_status = "Non-Compliant"
                self.error_log = result.get("error", "Unknown error occurred")
                self.qr_code_data = ""
                self.qr_code_image = ""
                self.tlv_encoded = 0
                
            self.save(ignore_permissions=True)
            
        except Exception as e:
            self.invoice_status = "Error"
            self.compliance_status = "Non-Compliant"
            self.error_log = str(e)
            self.save(ignore_permissions=True)
            frappe.log_error(f"QR Code generation failed for {self.name}: {str(e)}")
    
    def regenerate_qr_code(self):
        """Regenerate QR code (for updates or corrections)"""
        self.invoice_status = "Draft"
        self.generate_qr_code()
        
    def validate_qr_compliance(self):
        """Validate QR code compliance with Oman regulations"""
        validation_results = {
            "valid": True,
            "issues": []
        }
        
        # Check required fields
        if not self.vat_number:
            validation_results["issues"].append("VAT Number is required")
            validation_results["valid"] = False
            
        if not self.seller_name:
            validation_results["issues"].append("Seller name is required")
            validation_results["valid"] = False
            
        if not self.invoice_total or self.invoice_total <= 0:
            validation_results["issues"].append("Invoice total must be greater than 0")
            validation_results["valid"] = False
            
        if not self.qr_code_data:
            validation_results["issues"].append("QR code data is missing")
            validation_results["valid"] = False
            
        # Update compliance status
        self.compliance_status = "Compliant" if validation_results["valid"] else "Non-Compliant"
        
        return validation_results


# Whitelisted API methods
@frappe.whitelist()
def create_qr_invoice_for_sales_invoice(sales_invoice):
    """Create QR Code Invoice for a Sales Invoice"""
    
    # Check if already exists
    existing = frappe.db.exists("QR Code Invoice", {"sales_invoice": sales_invoice})
    if existing:
        return {"success": False, "message": f"QR Code Invoice already exists: {existing}"}
    
    try:
        qr_invoice = frappe.new_doc("QR Code Invoice")
        qr_invoice.sales_invoice = sales_invoice
        qr_invoice.insert()
        
        return {
            "success": True,
            "qr_invoice": qr_invoice.name,
            "message": "QR Code Invoice created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to create QR Invoice for {sales_invoice}: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def regenerate_qr_code(qr_invoice_name):
    """Regenerate QR code for existing QR Code Invoice"""
    
    try:
        qr_invoice = frappe.get_doc("QR Code Invoice", qr_invoice_name)
        qr_invoice.regenerate_qr_code()
        
        return {
            "success": True,
            "message": "QR code regenerated successfully",
            "status": qr_invoice.invoice_status
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to regenerate QR code for {qr_invoice_name}: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_qr_invoice_for_sales_invoice(sales_invoice):
    """Get QR Code Invoice for a Sales Invoice"""
    
    qr_invoice = frappe.db.get_value("QR Code Invoice", 
                                   {"sales_invoice": sales_invoice}, 
                                   ["name", "invoice_status", "compliance_status", "qr_code_image"])
    
    if qr_invoice:
        return {
            "exists": True,
            "qr_invoice": qr_invoice[0],
            "status": qr_invoice[1],
            "compliance": qr_invoice[2],
            "qr_image": qr_invoice[3]
        }
    else:
        return {"exists": False}


@frappe.whitelist()
def validate_qr_compliance_bulk(company, start_date, end_date):
    """Validate QR compliance for multiple invoices in a date range"""
    
    # Get all Sales Invoices in the range
    invoices = frappe.db.sql("""
        SELECT si.name, si.posting_date, si.customer, si.grand_total,
               qr.name as qr_invoice, qr.compliance_status
        FROM `tabSales Invoice` si
        LEFT JOIN `tabQR Code Invoice` qr ON si.name = qr.sales_invoice
        WHERE si.company = %s
        AND si.posting_date BETWEEN %s AND %s
        AND si.docstatus = 1
        ORDER BY si.posting_date DESC
    """, [company, start_date, end_date], as_dict=True)
    
    compliance_summary = {
        "total_invoices": len(invoices),
        "with_qr": 0,
        "compliant": 0,
        "non_compliant": 0,
        "missing_qr": 0,
        "details": []
    }
    
    for invoice in invoices:
        if invoice.qr_invoice:
            compliance_summary["with_qr"] += 1
            if invoice.compliance_status == "Compliant":
                compliance_summary["compliant"] += 1
            else:
                compliance_summary["non_compliant"] += 1
        else:
            compliance_summary["missing_qr"] += 1
            
        compliance_summary["details"].append({
            "sales_invoice": invoice.name,
            "posting_date": invoice.posting_date,
            "customer": invoice.customer,
            "grand_total": invoice.grand_total,
            "has_qr": bool(invoice.qr_invoice),
            "qr_invoice": invoice.qr_invoice,
            "compliance_status": invoice.compliance_status or "Missing QR"
        })
    
    # Calculate compliance percentage
    if compliance_summary["total_invoices"] > 0:
        compliance_summary["compliance_percentage"] = (
            compliance_summary["compliant"] / compliance_summary["total_invoices"] * 100
        )
    else:
        compliance_summary["compliance_percentage"] = 0
        
    return compliance_summary 