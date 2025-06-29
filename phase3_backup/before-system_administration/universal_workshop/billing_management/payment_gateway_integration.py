# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, get_datetime, format_datetime, now
import requests
import json
import hashlib
import hmac
import uuid
from datetime import datetime
import base64


class OmanPaymentGatewayManager:
    """
    Unified payment gateway manager for Oman-based payment processors
    Supports Thawani, MyFatoorah, PayTabs, and other CBO-approved gateways
    """

    def __init__(self):
        self.supported_gateways = {
            "thawani": ThawaniGateway,
            "myfatoorah": MyFatoorahGateway,
            "paytabs": PayTabsGateway,
            "sohar": SoharInternationalGateway,
        }
        self.supported_currencies = ["OMR", "USD", "EUR", "SAR", "AED"]
        self.default_currency = "OMR"

    def get_gateway(self, gateway_name):
        """Get gateway instance by name"""
        if gateway_name.lower() not in self.supported_gateways:
            frappe.throw(_("Unsupported payment gateway: {0}").format(gateway_name))

        gateway_class = self.supported_gateways[gateway_name.lower()]
        return gateway_class()

    def process_payment(self, payment_data):
        """Process payment through specified gateway"""
        gateway_name = payment_data.get("gateway")
        if not gateway_name:
            frappe.throw(_("Payment gateway not specified"))

        gateway = self.get_gateway(gateway_name)
        return gateway.process_payment(payment_data)

    def get_supported_currencies(self):
        """Get list of supported currencies"""
        return self.supported_currencies

    def convert_currency(self, amount, from_currency, to_currency):
        """Convert currency using latest exchange rates"""
        if from_currency == to_currency:
            return flt(amount, 3)

        # Get exchange rate from ERPNext Currency Exchange
        exchange_rate = self.get_exchange_rate(from_currency, to_currency)
        converted_amount = flt(amount) * flt(exchange_rate)

        return flt(converted_amount, 3)

    def get_exchange_rate(self, from_currency, to_currency):
        """Get exchange rate from ERPNext or external API"""
        try:
            # Try to get from ERPNext Currency Exchange doctype
            exchange_rate = frappe.db.get_value(
                "Currency Exchange",
                {"from_currency": from_currency, "to_currency": to_currency},
                "exchange_rate",
            )

            if exchange_rate:
                return flt(exchange_rate)

            # If not found, try to get latest rate from external API
            return self.fetch_live_exchange_rate(from_currency, to_currency)

        except Exception as e:
            frappe.log_error(f"Exchange rate fetch error: {str(e)}")
            return 1.0

    def fetch_live_exchange_rate(self, from_currency, to_currency):
        """Fetch live exchange rate from external API"""
        try:
            # Using a free exchange rate API (you can replace with preferred provider)
            api_url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get(to_currency)

                if rate:
                    # Store in ERPNext for caching
                    self.update_currency_exchange_rate(from_currency, to_currency, rate)
                    return flt(rate)

            return 1.0

        except Exception as e:
            frappe.log_error(f"Live exchange rate fetch error: {str(e)}")
            return 1.0

    def update_currency_exchange_rate(self, from_currency, to_currency, rate):
        """Update currency exchange rate in ERPNext"""
        try:
            existing = frappe.db.get_value(
                "Currency Exchange",
                {"from_currency": from_currency, "to_currency": to_currency},
                "name",
            )

            if existing:
                doc = frappe.get_doc("Currency Exchange", existing)
                doc.exchange_rate = flt(rate)
                doc.save()
            else:
                doc = frappe.new_doc("Currency Exchange")
                doc.from_currency = from_currency
                doc.to_currency = to_currency
                doc.exchange_rate = flt(rate)
                doc.insert()

            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Currency exchange rate update error: {str(e)}")


class BasePaymentGateway:
    """Base class for all payment gateways"""

    def __init__(self):
        self.gateway_name = ""
        self.api_base_url = ""
        self.test_mode = frappe.conf.get("developer_mode", False)
        self.supported_currencies = ["OMR"]

    def get_gateway_settings(self):
        """Get gateway settings from ERPNext"""
        settings_doctype = f"{self.gateway_name.title()} Gateway Settings"
        try:
            return frappe.get_single(settings_doctype)
        except:
            frappe.throw(_("Gateway settings not configured for {0}").format(self.gateway_name))

    def process_payment(self, payment_data):
        """Process payment - to be implemented by child classes"""
        raise NotImplementedError("Subclasses must implement process_payment method")

    def validate_payment_data(self, payment_data):
        """Validate payment data"""
        required_fields = ["amount", "currency", "customer_name", "customer_email"]
        for field in required_fields:
            if not payment_data.get(field):
                frappe.throw(_("Missing required field: {0}").format(field))

    def generate_payment_reference(self):
        """Generate unique payment reference"""
        return f"UW-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def log_payment_transaction(self, payment_data, response_data, status):
        """Log payment transaction for audit trail"""
        try:
            transaction_log = frappe.new_doc("Payment Transaction Log")
            transaction_log.gateway = self.gateway_name
            transaction_log.reference_number = payment_data.get("reference")
            transaction_log.amount = payment_data.get("amount")
            transaction_log.currency = payment_data.get("currency")
            transaction_log.customer_name = payment_data.get("customer_name")
            transaction_log.status = status
            transaction_log.request_data = json.dumps(payment_data)
            transaction_log.response_data = json.dumps(response_data)
            transaction_log.transaction_date = now()
            transaction_log.insert()
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Payment transaction logging error: {str(e)}")


class ThawaniGateway(BasePaymentGateway):
    """Thawani Payment Gateway Integration (CBO-approved)"""

    def __init__(self):
        super().__init__()
        self.gateway_name = "thawani"
        self.api_base_url = "https://uatcheckout.thawani.om/api/v1"  # Test URL
        self.production_url = "https://checkout.thawani.om/api/v1"
        self.supported_currencies = ["OMR", "USD", "EUR"]

    def process_payment(self, payment_data):
        """Process payment through Thawani gateway"""
        self.validate_payment_data(payment_data)

        settings = self.get_gateway_settings()

        # Convert amount to Baisa (OMR smallest unit)
        amount_in_baisa = int(flt(payment_data["amount"]) * 1000)

        # Prepare payment request
        payment_request = {
            "client_reference_id": payment_data.get("reference", self.generate_payment_reference()),
            "mode": "payment",
            "products": [
                {
                    "name": payment_data.get("description", "Workshop Service Payment"),
                    "unit_amount": amount_in_baisa,
                    "quantity": 1,
                }
            ],
            "success_url": payment_data.get(
                "success_url", f"{frappe.utils.get_url()}/payment-success"
            ),
            "cancel_url": payment_data.get(
                "cancel_url", f"{frappe.utils.get_url()}/payment-cancel"
            ),
            "metadata": {
                "customer_name": payment_data["customer_name"],
                "customer_email": payment_data["customer_email"],
                "invoice_number": payment_data.get("invoice_number", ""),
            },
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "thawani-api-key": settings.get_password("api_key"),
        }

        try:
            api_url = self.production_url if not self.test_mode else self.api_base_url
            response = requests.post(
                f"{api_url}/checkout/session", headers=headers, json=payment_request, timeout=30
            )

            response_data = response.json()

            if response.status_code == 201 and response_data.get("success"):
                # Success response
                result = {
                    "success": True,
                    "gateway": self.gateway_name,
                    "session_id": response_data.get("data", {}).get("session_id"),
                    "payment_url": response_data.get("data", {}).get("payment_url"),
                    "reference": payment_request["client_reference_id"],
                    "message": "Payment session created successfully",
                }

                self.log_payment_transaction(payment_data, response_data, "initiated")
                return result
            else:
                # Error response
                error_message = response_data.get("description", "Payment initiation failed")
                self.log_payment_transaction(payment_data, response_data, "failed")

                return {
                    "success": False,
                    "gateway": self.gateway_name,
                    "error": error_message,
                    "reference": payment_request["client_reference_id"],
                }

        except Exception as e:
            error_msg = f"Thawani payment processing error: {str(e)}"
            frappe.log_error(error_msg)

            return {
                "success": False,
                "gateway": self.gateway_name,
                "error": error_msg,
                "reference": payment_request["client_reference_id"],
            }


class MyFatoorahGateway(BasePaymentGateway):
    """MyFatoorah Payment Gateway Integration"""

    def __init__(self):
        super().__init__()
        self.gateway_name = "myfatoorah"
        self.api_base_url = "https://apitest.myfatoorah.com"  # Test URL
        self.production_url = "https://api.myfatoorah.com"
        self.supported_currencies = ["OMR", "USD", "EUR", "SAR", "AED"]

    def process_payment(self, payment_data):
        """Process payment through MyFatoorah gateway"""
        self.validate_payment_data(payment_data)

        settings = self.get_gateway_settings()

        # Prepare payment request
        payment_request = {
            "CustomerName": payment_data["customer_name"],
            "CustomerEmail": payment_data["customer_email"],
            "InvoiceValue": flt(payment_data["amount"], 3),
            "DisplayCurrencyIso": payment_data.get("currency", "OMR"),
            "MobileCountryCode": "+968",
            "CustomerMobile": payment_data.get("customer_phone", ""),
            "CustomerReference": payment_data.get("reference", self.generate_payment_reference()),
            "Language": "ar" if frappe.local.lang == "ar" else "en",
            "CallBackUrl": payment_data.get(
                "callback_url", f"{frappe.utils.get_url()}/payment-callback"
            ),
            "ErrorUrl": payment_data.get("error_url", f"{frappe.utils.get_url()}/payment-error"),
            "NotificationOption": "EML",
            "InvoiceItems": [
                {
                    "ItemName": payment_data.get("description", "Workshop Service Payment"),
                    "Quantity": 1,
                    "UnitPrice": flt(payment_data["amount"], 3),
                }
            ],
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.get_password('api_token')}",
        }

        try:
            api_url = self.production_url if not self.test_mode else self.api_base_url
            response = requests.post(
                f"{api_url}/v2/SendPayment", headers=headers, json=payment_request, timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get("IsSuccess"):
                # Success response
                data = response_data.get("Data", {})
                result = {
                    "success": True,
                    "gateway": self.gateway_name,
                    "invoice_id": data.get("InvoiceId"),
                    "payment_url": data.get("InvoiceURL"),
                    "reference": payment_request["CustomerReference"],
                    "message": "Payment invoice created successfully",
                }

                self.log_payment_transaction(payment_data, response_data, "initiated")
                return result
            else:
                # Error response
                error_message = response_data.get("Message", "Payment initiation failed")
                self.log_payment_transaction(payment_data, response_data, "failed")

                return {
                    "success": False,
                    "gateway": self.gateway_name,
                    "error": error_message,
                    "reference": payment_request["CustomerReference"],
                }

        except Exception as e:
            error_msg = f"MyFatoorah payment processing error: {str(e)}"
            frappe.log_error(error_msg)

            return {
                "success": False,
                "gateway": self.gateway_name,
                "error": error_msg,
                "reference": payment_request["CustomerReference"],
            }


class PayTabsGateway(BasePaymentGateway):
    """PayTabs Payment Gateway Integration"""

    def __init__(self):
        super().__init__()
        self.gateway_name = "paytabs"
        self.api_base_url = "https://secure.paytabs.com"
        self.supported_currencies = ["OMR", "USD", "EUR", "SAR", "AED"]

    def process_payment(self, payment_data):
        """Process payment through PayTabs gateway"""
        self.validate_payment_data(payment_data)

        settings = self.get_gateway_settings()

        # Prepare payment request
        payment_request = {
            "profile_id": settings.profile_id,
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_id": payment_data.get("reference", self.generate_payment_reference()),
            "cart_description": payment_data.get("description", "Workshop Service Payment"),
            "cart_currency": payment_data.get("currency", "OMR"),
            "cart_amount": flt(payment_data["amount"], 3),
            "callback": payment_data.get(
                "callback_url", f"{frappe.utils.get_url()}/payment-callback"
            ),
            "return": payment_data.get("return_url", f"{frappe.utils.get_url()}/payment-return"),
            "customer_details": {
                "name": payment_data["customer_name"],
                "email": payment_data["customer_email"],
                "phone": payment_data.get("customer_phone", ""),
                "street1": payment_data.get("customer_address", ""),
                "city": payment_data.get("customer_city", "Muscat"),
                "state": payment_data.get("customer_state", "Muscat"),
                "country": "OM",
                "zip": payment_data.get("customer_zip", "100"),
            },
        }

        # Make API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": settings.get_password("server_key"),
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/payment/request",
                headers=headers,
                json=payment_request,
                timeout=30,
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get("redirect_url"):
                # Success response
                result = {
                    "success": True,
                    "gateway": self.gateway_name,
                    "transaction_ref": response_data.get("tran_ref"),
                    "payment_url": response_data.get("redirect_url"),
                    "reference": payment_request["cart_id"],
                    "message": "Payment request created successfully",
                }

                self.log_payment_transaction(payment_data, response_data, "initiated")
                return result
            else:
                # Error response
                error_message = response_data.get("message", "Payment initiation failed")
                self.log_payment_transaction(payment_data, response_data, "failed")

                return {
                    "success": False,
                    "gateway": self.gateway_name,
                    "error": error_message,
                    "reference": payment_request["cart_id"],
                }

        except Exception as e:
            error_msg = f"PayTabs payment processing error: {str(e)}"
            frappe.log_error(error_msg)

            return {
                "success": False,
                "gateway": self.gateway_name,
                "error": error_msg,
                "reference": payment_request["cart_id"],
            }


class SoharInternationalGateway(BasePaymentGateway):
    """Sohar International Bank Payment Gateway Integration"""

    def __init__(self):
        super().__init__()
        self.gateway_name = "sohar"
        self.api_base_url = "https://payments.soharbank.om/api/v1"  # Placeholder URL
        self.supported_currencies = ["OMR", "USD", "EUR"]

    def process_payment(self, payment_data):
        """Process payment through Sohar International gateway"""
        # Note: This is a placeholder implementation
        # Actual API details should be obtained from Sohar International Bank

        self.validate_payment_data(payment_data)

        # For now, return a placeholder response
        return {
            "success": False,
            "gateway": self.gateway_name,
            "error": "Sohar International Gateway integration pending bank API documentation",
            "reference": self.generate_payment_reference(),
        }


# API Methods for Frappe/ERPNext integration


@frappe.whitelist()
def initiate_payment(payment_data):
    """
    Initiate payment through selected gateway
    """
    try:
        # Parse payment data if it's a string
        if isinstance(payment_data, str):
            payment_data = json.loads(payment_data)

        # Initialize payment manager
        payment_manager = OmanPaymentGatewayManager()

        # Process payment
        result = payment_manager.process_payment(payment_data)

        return result

    except Exception as e:
        frappe.log_error(f"Payment initiation error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_supported_gateways():
    """
    Get list of supported payment gateways
    """
    try:
        payment_manager = OmanPaymentGatewayManager()

        gateways = []
        for gateway_name in payment_manager.supported_gateways.keys():
            gateway = payment_manager.get_gateway(gateway_name)
            gateways.append(
                {
                    "name": gateway_name,
                    "display_name": gateway_name.title(),
                    "supported_currencies": gateway.supported_currencies,
                }
            )

        return {
            "success": True,
            "gateways": gateways,
            "default_currency": payment_manager.default_currency,
        }

    except Exception as e:
        frappe.log_error(f"Get gateways error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def convert_currency(amount, from_currency, to_currency):
    """
    Convert currency using latest exchange rates
    """
    try:
        payment_manager = OmanPaymentGatewayManager()
        converted_amount = payment_manager.convert_currency(amount, from_currency, to_currency)

        return {
            "success": True,
            "original_amount": flt(amount, 3),
            "converted_amount": converted_amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        }

    except Exception as e:
        frappe.log_error(f"Currency conversion error: {str(e)}")
        return {"success": False, "error": str(e)}


def setup_payment_gateway_settings():
    """
    Setup default payment gateway settings during installation
    """
    try:
        # Create gateway settings doctypes if they don't exist
        gateway_settings = [
            "Thawani Gateway Settings",
            "MyFatoorah Gateway Settings",
            "PayTabs Gateway Settings",
            "Sohar Gateway Settings",
        ]

        for setting_name in gateway_settings:
            if not frappe.db.exists("DocType", setting_name):
                # Create the doctype programmatically
                create_gateway_settings_doctype(setting_name)

    except Exception as e:
        frappe.log_error(f"Payment gateway settings setup error: {str(e)}")


def create_gateway_settings_doctype(doctype_name):
    """
    Create gateway settings doctype programmatically
    """
    # This would create the DocType with necessary fields
    # Implementation depends on specific gateway requirements
    pass
