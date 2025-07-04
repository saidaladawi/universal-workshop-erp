import frappe
from frappe import _
from frappe.model.document import Document

class BillingConfiguration(Document):
    # pylint: disable=no-member
    
    def validate(self):
        """Validate billing configuration settings"""
        self.validate_vat_settings()
        self.validate_payment_terms()
        self.validate_approval_threshold()
        self.set_default_values()
    
    def validate_vat_settings(self):
        """Validate VAT configuration"""
        if self.enable_vat:
            if not self.vat_rate or self.vat_rate <= 0:
                frappe.throw(_("VAT rate must be greater than 0 when VAT is enabled"))
            
            if not self.vat_account:
                frappe.throw(_("VAT account is required when VAT is enabled"))
            
            if not self.vat_registration_number:
                frappe.throw(_("VAT registration number is required for Oman compliance"))
    
    def validate_payment_terms(self):
        """Validate payment terms configuration"""
        if self.late_payment_penalty and self.late_payment_penalty < 0:
            frappe.throw(_("Late payment penalty cannot be negative"))
    
    def validate_approval_threshold(self):
        """Validate approval threshold settings"""
        if self.require_approval and not self.approval_threshold:
            frappe.throw(_("Approval threshold is required when approval is mandatory"))
        
        if self.approval_threshold and self.approval_threshold < 0:
            frappe.throw(_("Approval threshold cannot be negative"))
    
    def set_default_values(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.creation_date:
            self.creation_date = frappe.utils.now()
        
        if not self.configuration_status:
            self.configuration_status = "Draft"
    
    def before_save(self):
        """Actions before saving"""
        self.update_configuration_status()
    
    def update_configuration_status(self):
        """Update configuration status based on settings"""
        if self.is_active:
            if self.configuration_status == "Draft":
                self.configuration_status = "Active"
        else:
            self.configuration_status = "Inactive"
    
    @frappe.whitelist()
    def test_vat_calculation(self, test_amount=100.0):
        """Test VAT calculation with sample amount"""
        if not self.enable_vat:
            return {"error": "VAT is not enabled in this configuration"}
        
        vat_amount = (test_amount * self.vat_rate) / 100
        total_amount = test_amount + vat_amount
        
        return {
            "base_amount": test_amount,
            "vat_rate": self.vat_rate,
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "currency": self.currency_settings or "OMR"
        }
    
    @frappe.whitelist()
    def get_payment_methods_list(self):
        """Get list of configured payment methods"""
        if not self.payment_methods:
            return []
        
        return [method.strip() for method in self.payment_methods.split(',')]
    
    @frappe.whitelist()
    def validate_qr_code_settings(self):
        """Validate QR code configuration"""
        if self.enable_qr_codes and not self.qr_code_template:
            return {"error": "QR code template is required when QR codes are enabled"}
        
        return {"status": "valid"} 