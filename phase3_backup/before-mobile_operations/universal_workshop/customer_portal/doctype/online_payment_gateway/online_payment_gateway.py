# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json
import requests
import hashlib
import hmac
import time
from datetime import datetime, timedelta
import re

class OnlinePaymentGateway(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate payment gateway configuration before saving"""
        self.validate_arabic_fields()
        self.validate_api_configuration()
        self.validate_currency_settings()
        self.validate_amount_limits()
        self.validate_security_settings()
        self.validate_oman_compliance()
        
    def before_save(self):
        """Set default values and update configuration before saving"""
        self.set_metadata()
        self.update_api_endpoints()
        self.configure_webhooks()
        self.setup_default_settings()
        
    def after_save(self):
        """Post-save operations"""
        self.test_connection()
        self.update_integration_status()
        self.sync_with_erpnext()
        
    def validate_arabic_fields(self):
        """Ensure Arabic fields are properly filled"""
        if not self.gateway_name_ar and self.gateway_name:
            frappe.throw(_("Arabic gateway name is required"))
            
        # Validate Arabic text in notes
        if self.notes_ar:
            self.validate_arabic_text(self.notes_ar, 'notes_ar')
            
    def validate_arabic_text(self, text, field_name):
        """Validate Arabic text contains proper Arabic characters"""
        import re
        if text and not re.search(r'[\u0600-\u06FF]', text):
            frappe.msgprint(_("Field {0} should contain Arabic text").format(_(field_name)))
            
    def validate_api_configuration(self):
        """Validate API configuration settings"""
        if self.is_active and not self.is_test_mode:
            required_fields = ['api_endpoint', 'api_key', 'merchant_id']
            
            for field in required_fields:
                if not getattr(self, field, None):
                    frappe.throw(_("Field {0} is required for active payment gateway").format(_(field)))
                    
        # Validate URL formats
        url_fields = ['api_endpoint', 'webhook_url', 'success_url', 'cancel_url', 'callback_url']
        for field in url_fields:
            value = getattr(self, field, None)
            if value and not self.is_valid_url(value):
                frappe.throw(_("Invalid URL format in field {0}").format(_(field)))
                
    def is_valid_url(self, url):
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
        
    def validate_currency_settings(self):
        """Validate currency configuration"""
        if self.omr_support and self.default_currency != 'OMR':
            frappe.msgprint(_("Default currency should be OMR when OMR support is enabled"))
            
        # Validate supported currency against provider capabilities
        provider_currencies = self.get_provider_supported_currencies()
        if self.supported_currency not in provider_currencies:
            frappe.throw(_("Currency {0} is not supported by {1}").format(
                self.supported_currency, self.gateway_provider))
                
    def get_provider_supported_currencies(self):
        """Get supported currencies for the payment provider"""
        provider_currencies = {
            'Stripe': ['OMR', 'USD', 'EUR', 'GBP', 'AED', 'SAR'],
            'PayTabs': ['OMR', 'USD', 'EUR', 'AED', 'SAR', 'KWD'],
            'PayFort': ['OMR', 'USD', 'EUR', 'AED', 'SAR', 'KWD', 'QAR'],
            'OmanNet': ['OMR'],
            'Custom': ['Multiple']
        }
        return provider_currencies.get(self.gateway_provider, ['OMR', 'USD'])
        
    def validate_amount_limits(self):
        """Validate amount limits configuration"""
        if self.minimum_amount and self.maximum_amount:
            if float(self.minimum_amount) >= float(self.maximum_amount):
                frappe.throw(_("Minimum amount must be less than maximum amount"))
                
        # Validate against Oman regulations
        if self.omr_support:
            max_omr_limit = 10000  # Example: 10,000 OMR daily limit
            if self.maximum_amount and float(self.maximum_amount) > max_omr_limit:
                frappe.msgprint(_("Maximum amount exceeds recommended OMR limit of {0}").format(max_omr_limit))
                
    def validate_security_settings(self):
        """Validate security configuration"""
        if self.is_active and not self.ssl_certificate:
            frappe.msgprint(_("SSL certificate is recommended for active payment gateways"))
            
        if self.fraud_detection and not self.risk_assessment:
            self.risk_assessment = 'Medium'
            
        # Validate encryption type
        recommended_encryption = ['TLS 1.2', 'TLS 1.3']
        if self.encryption_type not in recommended_encryption:
            frappe.msgprint(_("Consider using TLS 1.2 or TLS 1.3 for better security"))
            
    def validate_oman_compliance(self):
        """Validate Oman market compliance settings"""
        if self.omr_support:
            # Ensure VAT handling is enabled for Oman (5% VAT)
            if not self.vat_handling:
                frappe.msgprint(_("VAT handling should be enabled for Oman market (5% VAT)"))
                
            # Validate receipt format for Oman regulations
            if self.receipt_format not in ['Oman Tax Authority', 'Custom']:
                frappe.msgprint(_("Receipt format should comply with Oman Tax Authority requirements"))
                
            # Ensure Arabic interface is enabled
            if not self.arabic_interface:
                frappe.msgprint(_("Arabic interface is recommended for Oman market"))
                
    def set_metadata(self):
        """Set metadata fields"""
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_date = frappe.utils.today()
            
        self.last_modified_by = frappe.session.user
        self.last_modified_date = frappe.utils.now()
        
    def update_api_endpoints(self):
        """Update API endpoints based on provider and mode"""
        if not self.api_endpoint:
            endpoint_map = {
                'Stripe': {
                    'live': 'https://api.stripe.com/v1',
                    'test': 'https://api.stripe.com/v1'
                },
                'PayTabs': {
                    'live': 'https://secure.paytabs.com/payment/request',
                    'test': 'https://secure-egypt.paytabs.com/payment/request'
                },
                'PayFort': {
                    'live': 'https://paymentservices.amazon.com/payment',
                    'test': 'https://sbpaymentservices.payfort.com/FortAPI'
                },
                'OmanNet': {
                    'live': 'https://gateway.omannet.om/api/v1',
                    'test': 'https://test.omannet.om/api/v1'
                }
            }
            
            provider_endpoints = endpoint_map.get(self.gateway_provider)
            if provider_endpoints:
                mode = 'test' if self.is_test_mode else 'live'
                self.api_endpoint = provider_endpoints.get(mode)
                
    def configure_webhooks(self):
        """Configure webhook URLs"""
        if not self.webhook_url:
            site_url = frappe.utils.get_url()
            self.webhook_url = f"{site_url}/api/method/universal_workshop.customer_portal.api.payment_webhook"
            
        if not self.success_url:
            self.success_url = f"{frappe.utils.get_url()}/payment-success"
            
        if not self.cancel_url:
            self.cancel_url = f"{frappe.utils.get_url()}/payment-cancelled"
            
        if not self.callback_url:
            self.callback_url = f"{frappe.utils.get_url()}/payment-callback"
            
    def setup_default_settings(self):
        """Set up default configuration settings"""
        if not self.timeout_duration:
            self.timeout_duration = 300  # 5 minutes default
            
        if not self.retry_attempts:
            self.retry_attempts = 3
            
        if not self.settlement_period:
            self.settlement_period = 1  # Next business day
            
        # Set default notification language for Oman
        if self.omr_support and not self.notification_language:
            self.notification_language = 'Both'
            
    def test_connection(self):
        """Test connection to payment gateway"""
        if not self.is_active or not self.api_endpoint:
            return
            
        try:
            test_result = self.perform_health_check()
            
            self.test_status = 'Passed' if test_result['success'] else 'Failed'
            self.last_tested = frappe.utils.now()
            self.test_results = json.dumps(test_result, indent=2)
            self.last_health_check = frappe.utils.now()
            
            if test_result['success']:
                self.average_response_time = test_result.get('response_time', 0)
                
        except Exception as e:
            self.test_status = 'Failed'
            self.test_results = f"Connection test failed: {str(e)}"
            frappe.log_error(f"Payment gateway test failed: {str(e)}")
            
    def perform_health_check(self):
        """Perform health check on payment gateway"""
        start_time = time.time()
        
        try:
            headers = self.get_api_headers()
            response = requests.get(
                f"{self.api_endpoint}/health", 
                headers=headers, 
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response_time,
                'message': 'Health check successful' if response.status_code == 200 else 'Health check failed'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Connection failed'
            }
            
    def get_api_headers(self):
        """Get API headers for requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Universal-Workshop-ERP/1.0'
        }
        
        if self.gateway_provider == 'Stripe':
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.gateway_provider in ['PayTabs', 'PayFort']:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.gateway_provider == 'OmanNet':
            headers['X-API-Key'] = self.api_key
            
        return headers
        
    def update_integration_status(self):
        """Update integration status with ERPNext"""
        if self.erpnext_integration:
            # Enable payment gateway in ERPNext settings
            self.setup_erpnext_payment_gateway()
            
    def setup_erpnext_payment_gateway(self):
        """Set up payment gateway in ERPNext"""
        try:
            # Create or update ERPNext Payment Gateway
            gateway_exists = frappe.db.exists('Payment Gateway', self.gateway_name)
            
            if gateway_exists:
                gateway_doc = frappe.get_doc('Payment Gateway', self.gateway_name)
            else:
                gateway_doc = frappe.new_doc('Payment Gateway')
                gateway_doc.gateway = self.gateway_name
                
            gateway_doc.gateway_settings = json.dumps({
                'api_endpoint': self.api_endpoint,
                'merchant_id': self.merchant_id,
                'is_test_mode': self.is_test_mode,
                'default_currency': self.default_currency
            })
            
            gateway_doc.save()
            
        except Exception as e:
            frappe.log_error(f"Failed to setup ERPNext payment gateway: {str(e)}")
            
    def sync_with_erpnext(self):
        """Sync payment gateway settings with ERPNext"""
        if self.erpnext_integration:
            # Update ERPNext system settings for payment gateway
            self.update_system_settings()
            
    def update_system_settings(self):
        """Update system settings for payment integration"""
        # This would update relevant system settings
        # Such as default payment gateway, currency settings, etc.
        pass
        
    @frappe.whitelist()
    def create_payment_request(self, amount, currency='OMR', customer_email='', description='', invoice_id=''):
        """Create a payment request"""
        try:
            # Validate amount
            if not amount or float(amount) <= 0:
                return {
                    'success': False,
                    'error': _('Invalid amount')
                }
                
            # Check amount limits
            if self.minimum_amount and float(amount) < float(self.minimum_amount):
                return {
                    'success': False,
                    'error': _('Amount below minimum limit')
                }
                
            if self.maximum_amount and float(amount) > float(self.maximum_amount):
                return {
                    'success': False,
                    'error': _('Amount exceeds maximum limit')
                }
                
            # Prepare payment request data
            payment_data = {
                'amount': float(amount),
                'currency': currency or self.default_currency,
                'customer_email': customer_email,
                'description': description,
                'invoice_id': invoice_id,
                'gateway_name': self.name,
                'success_url': self.success_url,
                'cancel_url': self.cancel_url,
                'webhook_url': self.webhook_url
            }
            
            # Create payment request based on provider
            if self.gateway_provider == 'Stripe':
                return self.create_stripe_payment(payment_data)
            elif self.gateway_provider == 'PayTabs':
                return self.create_paytabs_payment(payment_data)
            elif self.gateway_provider == 'PayFort':
                return self.create_payfort_payment(payment_data)
            elif self.gateway_provider == 'OmanNet':
                return self.create_omannet_payment(payment_data)
            else:
                return {
                    'success': False,
                    'error': _('Payment provider not supported')
                }
                
        except Exception as e:
            frappe.log_error(f"Payment request creation failed: {str(e)}")
            return {
                'success': False,
                'error': _('Payment request creation failed')
            }
            
    def create_stripe_payment(self, payment_data):
        """Create Stripe payment intent"""
        try:
            import stripe
            stripe.api_key = self.secret_key
            
            intent = stripe.PaymentIntent.create(
                amount=int(payment_data['amount'] * 100),  # Stripe uses cents
                currency=payment_data['currency'].lower(),
                metadata={
                    'invoice_id': payment_data['invoice_id'],
                    'customer_email': payment_data['customer_email']
                }
            )
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'payment_url': f"https://checkout.stripe.com/pay/{intent.id}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def create_paytabs_payment(self, payment_data):
        """Create PayTabs payment"""
        try:
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'profile_id': self.merchant_id,
                'tran_type': 'sale',
                'tran_class': 'ecom',
                'cart_currency': payment_data['currency'],
                'cart_amount': payment_data['amount'],
                'cart_description': payment_data['description'],
                'paypage_lang': 'ar' if self.arabic_interface else 'en',
                'return_url': self.success_url,
                'callback_url': self.webhook_url
            }
            
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'payment_url': result.get('redirect_url'),
                    'transaction_id': result.get('tran_ref')
                }
            else:
                return {
                    'success': False,
                    'error': 'PayTabs payment creation failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def create_payfort_payment(self, payment_data):
        """Create PayFort payment"""
        # PayFort implementation would go here
        return {
            'success': False,
            'error': 'PayFort integration not yet implemented'
        }
        
    def create_omannet_payment(self, payment_data):
        """Create OmanNet payment"""
        # OmanNet implementation would go here
        return {
            'success': False,
            'error': 'OmanNet integration not yet implemented'
        }
        
    @frappe.whitelist()
    def process_webhook(self, webhook_data):
        """Process webhook notification from payment gateway"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(webhook_data):
                return {
                    'success': False,
                    'error': 'Invalid webhook signature'
                }
                
            # Process webhook based on provider
            if self.gateway_provider == 'Stripe':
                return self.process_stripe_webhook(webhook_data)
            elif self.gateway_provider == 'PayTabs':
                return self.process_paytabs_webhook(webhook_data)
            else:
                return {
                    'success': False,
                    'error': 'Webhook processing not implemented for this provider'
                }
                
        except Exception as e:
            frappe.log_error(f"Webhook processing failed: {str(e)}")
            return {
                'success': False,
                'error': 'Webhook processing failed'
            }
            
    def verify_webhook_signature(self, webhook_data):
        """Verify webhook signature"""
        # Implementation depends on payment provider
        return True  # Placeholder
        
    def process_stripe_webhook(self, webhook_data):
        """Process Stripe webhook"""
        event_type = webhook_data.get('type')
        
        if event_type == 'payment_intent.succeeded':
            return self.handle_payment_success(webhook_data)
        elif event_type == 'payment_intent.payment_failed':
            return self.handle_payment_failure(webhook_data)
        else:
            return {'success': True, 'message': 'Event processed'}
            
    def process_paytabs_webhook(self, webhook_data):
        """Process PayTabs webhook"""
        payment_result = webhook_data.get('payment_result')
        
        if payment_result and payment_result.get('response_status') == 'A':
            return self.handle_payment_success(webhook_data)
        else:
            return self.handle_payment_failure(webhook_data)
            
    def handle_payment_success(self, webhook_data):
        """Handle successful payment"""
        try:
            # Update transaction statistics
            self.successful_transactions = (self.successful_transactions or 0) + 1
            self.total_transactions = (self.total_transactions or 0) + 1
            self.success_rate = (self.successful_transactions / self.total_transactions) * 100
            
            # Send success notification
            self.send_payment_notification(webhook_data, 'success')
            
            return {'success': True, 'message': 'Payment processed successfully'}
            
        except Exception as e:
            frappe.log_error(f"Payment success handling failed: {str(e)}")
            return {'success': False, 'error': 'Failed to process payment success'}
            
    def handle_payment_failure(self, webhook_data):
        """Handle failed payment"""
        try:
            # Update transaction statistics
            self.failed_transactions = (self.failed_transactions or 0) + 1
            self.total_transactions = (self.total_transactions or 0) + 1
            self.success_rate = (self.successful_transactions or 0) / self.total_transactions * 100
            
            # Send failure notification
            self.send_payment_notification(webhook_data, 'failure')
            
            return {'success': True, 'message': 'Payment failure processed'}
            
        except Exception as e:
            frappe.log_error(f"Payment failure handling failed: {str(e)}")
            return {'success': False, 'error': 'Failed to process payment failure'}
            
    def send_payment_notification(self, payment_data, status):
        """Send payment notification"""
        try:
            if status == 'success' and self.customer_notification_template:
                template = frappe.get_doc('Email Template', self.customer_notification_template)
            elif status == 'failure' and self.failure_notification_template:
                template = frappe.get_doc('Email Template', self.failure_notification_template)
            else:
                return
                
            # Send notification using template
            # Implementation would depend on specific requirements
            
        except Exception as e:
            frappe.log_error(f"Payment notification failed: {str(e)}")

@frappe.whitelist()
def get_active_payment_gateways(currency='OMR'):
    """Get list of active payment gateways for a currency"""
    try:
        filters = {
            'is_active': 1,
            'maintenance_mode': 0
        }
        
        if currency != 'Multiple':
            filters['supported_currency'] = ['in', [currency, 'Multiple']]
            
        gateways = frappe.get_list(
            'Online Payment Gateway',
            filters=filters,
            fields=[
                'name', 'gateway_name', 'gateway_name_ar', 'gateway_provider',
                'supported_currency', 'minimum_amount', 'maximum_amount',
                'transaction_fee_percentage', 'arabic_interface', 'success_rate'
            ],
            order_by='success_rate desc'
        )
        
        return {
            'success': True,
            'gateways': gateways
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching payment gateways: {str(e)}")
        return {
            'success': False,
            'error': _('Failed to fetch payment gateways')
        }

@frappe.whitelist()
def create_payment_link(gateway_name, amount, currency='OMR', customer_email='', description='', invoice_id=''):
    """Create payment link for customer"""
    try:
        gateway = frappe.get_doc('Online Payment Gateway', gateway_name)
        
        # Create payment request
        result = gateway.create_payment_request(
            amount=amount,
            currency=currency,
            customer_email=customer_email,
            description=description,
            invoice_id=invoice_id
        )
        
        if result['success']:
            # Log payment request
            payment_log = frappe.new_doc('Payment Request Log')
            payment_log.gateway = gateway_name
            payment_log.amount = amount
            payment_log.currency = currency
            payment_log.customer_email = customer_email
            payment_log.description = description
            payment_log.invoice_id = invoice_id
            payment_log.payment_url = result.get('payment_url')
            payment_log.status = 'Created'
            payment_log.insert()
            
        return result
        
    except Exception as e:
        frappe.log_error(f"Payment link creation failed: {str(e)}")
        return {
            'success': False,
            'error': _('Failed to create payment link')
        } 