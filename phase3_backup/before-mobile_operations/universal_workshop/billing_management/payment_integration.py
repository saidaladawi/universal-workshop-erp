"""
Payment Integration Module for Universal Workshop ERP
Integrates payment gateways and multi-currency support with ERPNext billing
"""

import frappe
from frappe import _
import json
from datetime import datetime
from .payment_gateway_integration import OmanPaymentGatewayManager
from .multi_currency_config import OmanMultiCurrencyManager


class OmanPaymentIntegrator:
    """Main class for payment integration in Universal Workshop ERP"""

    def __init__(self):
        self.gateway_manager = OmanPaymentGatewayManager()
        self.currency_manager = OmanMultiCurrencyManager()

    def process_invoice_payment(self, sales_invoice_name, payment_method, gateway_type=None):
        """Process payment for a sales invoice with multi-currency support"""
        try:
            invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

            # Get currency information
            currency_info = self.currency_manager.get_currency_info(invoice.currency)

            payment_data = {
                "invoice_name": sales_invoice_name,
                "amount": invoice.grand_total,
                "currency": invoice.currency,
                "customer": invoice.customer,
                "payment_method": payment_method,
                "gateway_type": gateway_type,
                "currency_info": currency_info,
            }

            if payment_method == "Online Payment" and gateway_type:
                return self._process_online_payment(payment_data)
            else:
                return self._process_offline_payment(payment_data)

        except Exception as e:
            frappe.log_error(f"Payment processing error: {e}")
            return {"status": "error", "message": str(e)}

    def _process_online_payment(self, payment_data):
        """Process online payment through gateway"""
        try:
            gateway = self.gateway_manager.get_gateway(payment_data["gateway_type"])

            # Convert amount to OMR if needed
            if payment_data["currency"] != "OMR":
                omr_amount = self.currency_manager.convert_currency(
                    payment_data["amount"], payment_data["currency"], "OMR"
                )
            else:
                omr_amount = payment_data["amount"]

            # Create payment request
            payment_request = gateway.create_payment_session(
                {
                    "amount": omr_amount,
                    "currency": "OMR",
                    "customer_email": frappe.db.get_value(
                        "Customer", payment_data["customer"], "email_id"
                    ),
                    "invoice_reference": payment_data["invoice_name"],
                    "success_url": f"/api/payment/success/{payment_data['invoice_name']}",
                    "cancel_url": f"/api/payment/cancel/{payment_data['invoice_name']}",
                }
            )

            if payment_request.get("status") == "success":
                # Update invoice with payment details
                self._update_invoice_payment_status(
                    payment_data["invoice_name"],
                    "Processing",
                    payment_request.get("session_id"),
                    payment_data["gateway_type"],
                )

                return {
                    "status": "success",
                    "payment_url": payment_request.get("payment_url"),
                    "session_id": payment_request.get("session_id"),
                }
            else:
                return {
                    "status": "error",
                    "message": payment_request.get("message", "Payment session creation failed"),
                }

        except Exception as e:
            frappe.log_error(f"Online payment processing error: {e}")
            return {"status": "error", "message": str(e)}

    def _process_offline_payment(self, payment_data):
        """Process offline payment (cash, bank transfer, etc.)"""
        try:
            # Create payment entry
            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = payment_data["customer"]
            payment_entry.paid_amount = payment_data["amount"]
            payment_entry.received_amount = payment_data["amount"]
            payment_entry.paid_from = self._get_default_receivable_account()
            payment_entry.paid_to = self._get_default_cash_account()
            payment_entry.reference_no = payment_data["invoice_name"]
            payment_entry.reference_date = frappe.utils.today()

            # Add invoice reference
            payment_entry.append(
                "references",
                {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": payment_data["invoice_name"],
                    "allocated_amount": payment_data["amount"],
                },
            )

            payment_entry.insert()
            payment_entry.submit()

            # Update invoice payment status
            self._update_invoice_payment_status(
                payment_data["invoice_name"],
                "Paid",
                payment_entry.name,
                payment_data["payment_method"],
            )

            return {
                "status": "success",
                "payment_entry": payment_entry.name,
                "message": _("Payment recorded successfully"),
            }

        except Exception as e:
            frappe.log_error(f"Offline payment processing error: {e}")
            return {"status": "error", "message": str(e)}

    def _update_invoice_payment_status(self, invoice_name, status, reference, gateway_type):
        """Update invoice with payment status and details"""
        frappe.db.set_value(
            "Sales Invoice",
            invoice_name,
            {
                "custom_payment_status": status,
                "custom_payment_reference": reference,
                "custom_payment_gateway": gateway_type,
                "custom_payment_timestamp": frappe.utils.now(),
            },
        )
        frappe.db.commit()

    def _get_default_receivable_account(self):
        """Get default accounts receivable account"""
        company = frappe.defaults.get_defaults().company
        return frappe.db.get_value("Company", company, "default_receivable_account")

    def _get_default_cash_account(self):
        """Get default cash account"""
        company = frappe.defaults.get_defaults().company
        return frappe.db.get_value("Company", company, "default_cash_account")


@frappe.whitelist()
def create_payment_request(sales_invoice, payment_method, gateway_type=None):
    """API endpoint to create payment request"""
    integrator = OmanPaymentIntegrator()
    return integrator.process_invoice_payment(sales_invoice, payment_method, gateway_type)


@frappe.whitelist()
def handle_payment_callback(session_id, status, transaction_id=None):
    """Handle payment gateway callback"""
    try:
        # Find invoice by session ID
        invoice_name = frappe.db.get_value(
            "Sales Invoice", {"custom_payment_reference": session_id}, "name"
        )

        if not invoice_name:
            return {"status": "error", "message": "Invoice not found"}

        integrator = OmanPaymentIntegrator()

        if status == "success":
            # Create payment entry for successful payment
            invoice = frappe.get_doc("Sales Invoice", invoice_name)

            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = invoice.customer
            payment_entry.paid_amount = invoice.grand_total
            payment_entry.received_amount = invoice.grand_total
            payment_entry.paid_from = integrator._get_default_receivable_account()
            payment_entry.paid_to = integrator._get_default_cash_account()
            payment_entry.reference_no = transaction_id or session_id
            payment_entry.reference_date = frappe.utils.today()

            payment_entry.append(
                "references",
                {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": invoice_name,
                    "allocated_amount": invoice.grand_total,
                },
            )

            payment_entry.insert()
            payment_entry.submit()

            # Update invoice status
            integrator._update_invoice_payment_status(
                invoice_name, "Paid", payment_entry.name, "Online Payment"
            )

            return {"status": "success", "payment_entry": payment_entry.name}

        else:
            # Handle failed payment
            integrator._update_invoice_payment_status(
                invoice_name, "Failed", session_id, "Online Payment"
            )

            return {"status": "failed", "message": "Payment failed"}

    except Exception as e:
        frappe.log_error(f"Payment callback error: {e}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_available_payment_methods(customer=None):
    """Get available payment methods for customer"""
    methods = [
        {"value": "Cash", "label": _("Cash Payment")},
        {"value": "Bank Transfer", "label": _("Bank Transfer")},
        {"value": "Cheque", "label": _("Cheque Payment")},
        {"value": "Online Payment", "label": _("Online Payment")},
    ]

    return methods


@frappe.whitelist()
def get_available_payment_gateways():
    """Get available payment gateways"""
    gateways = [
        {"value": "thawani", "label": _("Thawani Payment Gateway")},
        {"value": "myfatoorah", "label": _("MyFatoorah")},
        {"value": "paytabs", "label": _("PayTabs")},
        {"value": "sohar", "label": _("Sohar International Gateway")},
        {"value": "quadrapay", "label": _("QuadraPay")},
        {"value": "fibonatix", "label": _("Fibonatix")},
    ]

    return gateways


@frappe.whitelist()
def get_currency_conversion_rate(from_currency, to_currency):
    """Get current currency conversion rate"""
    manager = OmanMultiCurrencyManager()
    return manager.get_exchange_rate(from_currency, to_currency)


@frappe.whitelist()
def convert_amount(amount, from_currency, to_currency):
    """Convert amount between currencies"""
    manager = OmanMultiCurrencyManager()
    return manager.convert_currency(float(amount), from_currency, to_currency)


class PaymentValidator:
    """Validator for payment transactions"""

    @staticmethod
    def validate_payment_amount(amount, currency):
        """Validate payment amount"""
        if amount <= 0:
            frappe.throw(_("Payment amount must be greater than zero"))

        # Check minimum amounts for different currencies
        min_amounts = {
            "OMR": 0.100,  # 100 Baisa minimum
            "USD": 1.00,
            "EUR": 1.00,
            "GBP": 1.00,
            "AED": 5.00,
            "SAR": 5.00,
        }

        min_amount = min_amounts.get(currency, 1.00)
        if amount < min_amount:
            frappe.throw(_("Minimum payment amount for {0} is {1}").format(currency, min_amount))

    @staticmethod
    def validate_customer_payment_limits(customer, amount, currency):
        """Validate customer payment limits"""
        # Convert to OMR for limit checking
        manager = OmanMultiCurrencyManager()
        omr_amount = manager.convert_currency(amount, currency, "OMR")

        # Check daily limit (example: 10,000 OMR)
        daily_limit = 10000.0

        today_payments = (
            frappe.db.sql(
                """
            SELECT SUM(grand_total)
            FROM `tabSales Invoice`
            WHERE customer = %s 
            AND DATE(creation) = CURDATE()
            AND custom_payment_status = 'Paid'
        """,
                [customer],
            )[0][0]
            or 0
        )

        if (today_payments + omr_amount) > daily_limit:
            frappe.throw(_("Daily payment limit exceeded. Limit: {0} OMR").format(daily_limit))


def setup_payment_integration():
    """Setup payment integration system"""
    try:
        # Initialize currency manager
        currency_manager = OmanMultiCurrencyManager()
        currency_manager.setup_currencies()

        # Setup payment modes
        payment_modes = [
            "Cash",
            "Bank Transfer",
            "Cheque",
            "Credit Card",
            "Thawani Gateway",
            "MyFatoorah",
            "PayTabs",
            "Sohar International",
            "QuadraPay",
            "Fibonatix",
        ]

        for mode in payment_modes:
            if not frappe.db.exists("Mode of Payment", mode):
                payment_mode = frappe.new_doc("Mode of Payment")
                payment_mode.mode_of_payment = mode
                if "Gateway" in mode or mode in ["MyFatoorah", "PayTabs", "QuadraPay", "Fibonatix"]:
                    payment_mode.type = "Electronic"
                else:
                    payment_mode.type = "Cash" if mode == "Cash" else "Bank"
                payment_mode.insert()

        frappe.db.commit()
        return True

    except Exception as e:
        frappe.log_error(f"Payment integration setup error: {e}")
        return False


# Hooks integration
def validate_payment_entry(doc, method):
    """Validate payment entry before submission"""
    if doc.payment_type == "Receive" and doc.party_type == "Customer":
        PaymentValidator.validate_payment_amount(doc.paid_amount, doc.paid_from_account_currency)
        PaymentValidator.validate_customer_payment_limits(
            doc.party, doc.paid_amount, doc.paid_from_account_currency
        )


def update_payment_status_on_submit(doc, method):
    """Update payment status when payment entry is submitted"""
    for ref in doc.references:
        if ref.reference_doctype == "Sales Invoice":
            frappe.db.set_value(
                "Sales Invoice",
                ref.reference_name,
                {
                    "custom_payment_status": "Paid",
                    "custom_payment_reference": doc.name,
                    "custom_payment_timestamp": frappe.utils.now(),
                },
            )
    frappe.db.commit()
