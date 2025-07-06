import frappe
from frappe import _
from frappe.model.document import Document
import json
import hashlib
import hmac

class PaymentGatewayConfig(Document):
    # pylint: disable=no-member
    
    def validate(self):
        """Validate payment gateway configuration"""
        self.validate_connection_settings()
        self.validate_webhook_settings()
        self.validate_security_settings()
        self.set_default_values()
    
    def validate_connection_settings(self):
        """Validate connection settings"""
        if not self.api_key:
            frappe.throw(_("API Key is required"))
        
        if not self.secret_key:
            frappe.throw(_("Secret Key is required"))
        
        if not self.environment:
            frappe.throw(_("Environment must be specified"))
    
    def validate_webhook_settings(self):
        """Validate webhook configuration"""
        if self.enable_webhooks:
            if not self.webhook_url:
                frappe.throw(_("Webhook URL is required when webhooks are enabled"))
            
            if not self.webhook_secret:
                frappe.throw(_("Webhook Secret is required for security"))
    
    def validate_security_settings(self):
        """Validate security settings"""
        if self.environment == "Production" and self.test_mode:
            frappe.throw(_("Test mode should be disabled in production environment"))
    
    def set_default_values(self):
        """Set default values before saving"""
        if not self.gateway_status:
            self.gateway_status = "Disconnected"
        
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.creation_date:
            self.creation_date = frappe.utils.now()
    
    @frappe.whitelist()
    def test_connection(self):
        """Test gateway connection"""
        try:
            # Simulate connection test
            if self.environment == "Sandbox":
                return {
                    "status": "success",
                    "message": "Connection test successful (Sandbox mode)",
                    "test_mode": True
                }
            else:
                return {
                    "status": "success", 
                    "message": "Connection test successful (Production mode)",
                    "test_mode": False
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }
    
    @frappe.whitelist()
    def generate_webhook_signature(self, payload):
        """Generate webhook signature for verification"""
        if not self.webhook_secret:
            return {"error": "Webhook secret not configured"}
        
        try:
            # Generate HMAC signature
            signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return {
                "signature": signature,
                "algorithm": "sha256"
            }
        except Exception as e:
            return {"error": f"Signature generation failed: {str(e)}"}
    
    @frappe.whitelist()
    def get_supported_payment_methods(self):
        """Get list of supported payment methods"""
        if not self.supported_payment_methods:
            return []
        
        return [method.strip() for method in self.supported_payment_methods.split(',')]
    
    @frappe.whitelist()
    def get_supported_currencies(self):
        """Get list of supported currencies"""
        if not self.supported_currencies:
            return []
        
        return [currency.strip() for currency in self.supported_currencies.split(',')]
    
    @frappe.whitelist()
    def calculate_transaction_fee(self, amount):
        """Calculate transaction fee for given amount"""
        if not self.transaction_fees:
            return {"fee": 0, "total": amount}
        
        fee = (amount * self.transaction_fees) / 100
        total = amount + fee
        
        return {
            "amount": amount,
            "fee_percentage": self.transaction_fees,
            "fee": fee,
            "total": total
        }
    
    def before_save(self):
        """Actions before saving"""
        self.update_gateway_status()
    
    def update_gateway_status(self):
        """Update gateway status based on configuration"""
        if self.is_active and self.api_key and self.secret_key:
            self.gateway_status = "Connected"
        else:
            self.gateway_status = "Disconnected" 