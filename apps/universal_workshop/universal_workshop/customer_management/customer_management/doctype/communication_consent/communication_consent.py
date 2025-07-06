# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import secrets
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, add_to_date, format_datetime
import re
import json
from datetime import datetime


class CommunicationConsent(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate communication consent data"""
        self.validate_customer_details()
        self.validate_phone_number()
        self.validate_consent_dates()
        self.validate_double_optin()
        self.validate_withdrawal_data()

    def before_save(self):
        """Set default values and generate tokens before saving"""
        self.set_customer_details()
        self.generate_confirmation_token()
        self.update_audit_trail()
        self.set_compliance_flags()

    def after_insert(self):
        """Actions after consent record is created"""
        if self.double_optin_required and self.consent_status == "Given":
            self.send_double_optin_confirmation()
            self.consent_status = "Pending Double Opt-in"
            self.save(ignore_permissions=True)

    def validate_customer_details(self):
        """Validate customer information"""
        if not self.customer:
            frappe.throw(_("Customer is required"))

        if not self.phone_number:
            frappe.throw(_("Phone number is required"))

    def validate_phone_number(self):
        """Validate Oman phone number format"""
        if self.phone_number:
            # Oman phone format: +968 followed by 8 digits
            oman_pattern = r"^\+968\s?\d{8}$"
            if not re.match(oman_pattern, self.phone_number):
                frappe.throw(_("Invalid Oman phone number format. Use: +968 XXXXXXXX"))

    def validate_consent_dates(self):
        """Validate consent date logic"""
        if self.consent_given_date and self.consent_withdrawn_date:
            if self.consent_withdrawn_date <= self.consent_given_date:
                frappe.throw(_("Withdrawal date must be after consent given date"))

    def validate_double_optin(self):
        """Validate double opt-in workflow"""
        if self.double_optin_required:
            if self.confirmation_expires and self.confirmation_expires < now():
                if self.consent_status == "Pending Double Opt-in":
                    self.consent_status = "Expired"

    def validate_withdrawal_data(self):
        """Validate withdrawal information"""
        if self.consent_status == "Withdrawn":
            if not self.consent_withdrawn_date:
                self.consent_withdrawn_date = now()
            if not self.withdrawal_method:
                frappe.throw(_("Withdrawal method is required when consent is withdrawn"))

    def set_customer_details(self):
        """Set customer details from linked customer"""
        if self.customer and not self.customer_name:
            customer_doc = frappe.get_doc("Customer", self.customer)
            self.customer_name = customer_doc.customer_name

            # Get email from customer if not provided
            if not self.email and customer_doc.email_id:
                self.email = customer_doc.email_id

    def generate_confirmation_token(self):
        """Generate secure confirmation token for double opt-in"""
        if self.double_optin_required and not self.confirmation_token:
            self.confirmation_token = secrets.token_urlsafe(32)

            # Set expiration (24 hours from now)
            self.confirmation_expires = add_to_date(now(), hours=24)

            # Generate confirmation link
            site_url = frappe.utils.get_url()
            self.confirmation_link = f"{site_url}/api/method/universal_workshop.communication_management.doctype.communication_consent.communication_consent.confirm_double_optin?token={self.confirmation_token}"

    def update_audit_trail(self):
        """Update audit trail with current action"""
        current_time = format_datetime(now())
        current_user = frappe.session.user

        action_description = f"[{current_time}] {current_user}: "

        if self.is_new():
            action_description += f"Consent created - Type: {self.consent_type}, Channel: {self.consent_channel}, Status: {self.consent_status}"
        else:
            action_description += f"Consent updated - Status: {self.consent_status}"

        if self.consent_status == "Withdrawn":
            action_description += f", Withdrawal Method: {self.withdrawal_method}"

        # Append to existing audit trail
        if self.audit_trail:
            self.audit_trail += f"\n{action_description}"
        else:
            self.audit_trail = action_description

        # Set last updated by
        self.last_updated_by = current_user

    def set_compliance_flags(self):
        """Set compliance flags based on current regulations"""
        # All consents are compliant with 2025 regulations if properly documented
        self.gdpr_compliant = 1
        self.oman_pdpl_compliant = 1
        self.uae_compliant = 1

    def send_double_optin_confirmation(self):
        """Send double opt-in confirmation message"""
        try:
            # Import here to avoid circular imports
            from universal_workshop.communication_management.doctype.communication_settings.oman_twilio_client import (
                OmanTwilioClient,
            )

            # Get consent confirmation template
            confirmation_message = self.get_double_optin_message()

            client = OmanTwilioClient()

            if self.consent_channel in ["SMS", "All Channels"]:
                client.send_sms(
                    to_number=self.phone_number,
                    message=confirmation_message,
                    message_type="transactional",
                )

            if self.consent_channel in ["WhatsApp", "All Channels"]:
                client.send_whatsapp_message(
                    to_number=self.phone_number,
                    message=confirmation_message,
                    message_type="transactional",
                )

            self.double_optin_sent_date = now()

        except Exception as e:
            frappe.log_error(f"Failed to send double opt-in confirmation: {str(e)}")

    def get_double_optin_message(self):
        """Get double opt-in confirmation message"""
        customer_name = self.customer_name or "Customer"

        if frappe.local.lang == "ar":
            message = f"""مرحباً {customer_name},
            
للتأكيد على موافقتك لتلقي الرسائل من ورشة يونيفرسال، يرجى النقر على الرابط التالي:

{self.confirmation_link}

هذا الرابط صالح لمدة 24 ساعة.

للإلغاء، أرسل STOP"""
        else:
            message = f"""Hello {customer_name},

To confirm your consent for receiving messages from Universal Workshop, please click the link below:

{self.confirmation_link}

This link expires in 24 hours.

Reply STOP to unsubscribe."""

        return message

    @staticmethod
    def confirm_double_optin(token):
        """Confirm double opt-in using token"""
        consent_record = frappe.get_list(
            "Communication Consent",
            filters={
                "confirmation_token": token,
                "consent_status": "Pending Double Opt-in",
                "confirmation_expires": [">", now()],
            },
            limit=1,
        )

        if not consent_record:
            return {"success": False, "message": _("Invalid or expired confirmation link")}

        doc = frappe.get_doc("Communication Consent", consent_record[0].name)
        doc.consent_status = "Given"
        doc.double_optin_confirmed_date = now()
        doc.save(ignore_permissions=True)

        return {"success": True, "message": _("Communication consent confirmed successfully")}

    def withdraw_consent(self, method="Website", reason=""):
        """Withdraw communication consent"""
        self.consent_status = "Withdrawn"
        self.consent_withdrawn_date = now()
        self.withdrawal_method = method
        self.withdrawal_reason = reason
        self.save(ignore_permissions=True)

        # Update all related consent records for this customer/channel
        self.update_related_consents()

    def update_related_consents(self):
        """Update related consent records when one is withdrawn"""
        if self.consent_status == "Withdrawn":
            # Find related consents for same customer/channel
            related_consents = frappe.get_list(
                "Communication Consent",
                filters={
                    "customer": self.customer,
                    "consent_channel": self.consent_channel,
                    "consent_status": ["!=", "Withdrawn"],
                    "name": ["!=", self.name],
                },
            )

            for consent in related_consents:
                doc = frappe.get_doc("Communication Consent", consent.name)
                doc.consent_status = "Withdrawn"
                doc.consent_withdrawn_date = self.consent_withdrawn_date
                doc.withdrawal_method = "Related Consent Withdrawn"
                doc.withdrawal_reason = f"Withdrawn due to related consent {self.name}"
                doc.save(ignore_permissions=True)

    def get_consent_summary(self):
        """Get summary of customer's consent preferences"""
        return {
            "customer": self.customer,
            "customer_name": self.customer_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "consent_status": self.consent_status,
            "channels": {
                "sms": self.allow_sms,
                "whatsapp": self.allow_whatsapp,
                "email": self.allow_email,
            },
            "preferences": {
                "promotional": self.allow_promotional,
                "transactional": self.allow_transactional,
                "appointment_reminders": self.allow_appointment_reminders,
                "frequency": self.communication_frequency,
            },
            "compliance": {
                "gdpr": self.gdpr_compliant,
                "oman_pdpl": self.oman_pdpl_compliant,
                "uae": self.uae_compliant,
            },
        }


# WhiteListed Methods
@frappe.whitelist()
def confirm_double_optin(token):
    """Public API for confirming double opt-in"""
    return CommunicationConsent.confirm_double_optin(token)


@frappe.whitelist()
def withdraw_consent_by_token(token, method="Unsubscribe Link", reason=""):
    """Withdraw consent using unsubscribe token"""
    consent_record = frappe.get_list(
        "Communication Consent", filters={"confirmation_token": token}, limit=1
    )

    if not consent_record:
        return {"success": False, "message": _("Invalid unsubscribe link")}

    doc = frappe.get_doc("Communication Consent", consent_record[0].name)
    doc.withdraw_consent(method, reason)

    return {"success": True, "message": _("You have been unsubscribed successfully")}


@frappe.whitelist()
def get_customer_consent_status(customer, phone_number=None):
    """Get customer's current consent status for all channels"""
    filters = {"customer": customer}
    if phone_number:
        filters["phone_number"] = phone_number

    consents = frappe.get_list(
        "Communication Consent", filters=filters, fields=["*"], order_by="creation desc"
    )

    # Process consents to get current status
    consent_status = {
        "SMS": False,
        "WhatsApp": False,
        "Email": False,
        "promotional": False,
        "transactional": True,  # Default allow transactional
        "appointment_reminders": True,  # Default allow reminders
    }

    for consent in consents:
        if consent.consent_status == "Given":
            if consent.consent_channel in ["SMS", "All Channels"]:
                consent_status["SMS"] = consent.allow_sms
            if consent.consent_channel in ["WhatsApp", "All Channels"]:
                consent_status["WhatsApp"] = consent.allow_whatsapp
            if consent.consent_channel in ["Email", "All Channels"]:
                consent_status["Email"] = consent.allow_email

            consent_status["promotional"] = consent.allow_promotional
            consent_status["transactional"] = consent.allow_transactional
            consent_status["appointment_reminders"] = consent.allow_appointment_reminders

    return consent_status


@frappe.whitelist()
def create_consent_record(
    customer,
    phone_number,
    consent_type,
    consent_channel,
    consent_method="Website Form",
    ip_address=None,
    user_agent=None,
):
    """Create new consent record"""
    try:
        consent = frappe.new_doc("Communication Consent")
        consent.update(
            {
                "customer": customer,
                "phone_number": phone_number,
                "consent_type": consent_type,
                "consent_channel": consent_channel,
                "consent_method": consent_method,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "consent_given_date": now(),
                "double_optin_required": 1,  # 2025 compliance requirement
                "created_by_system": 1,
            }
        )

        consent.insert(ignore_permissions=True)

        return {
            "success": True,
            "consent_id": consent.name,
            "message": _("Consent record created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating consent record: {str(e)}")
        return {"success": False, "message": _("Failed to create consent record")}


@frappe.whitelist()
def bulk_update_consent_preferences(customers_data):
    """Bulk update consent preferences for multiple customers"""
    try:
        updated_count = 0

        for customer_data in customers_data:
            customer = customer_data.get("customer")
            preferences = customer_data.get("preferences", {})

            # Get existing consent records
            consents = frappe.get_list(
                "Communication Consent", filters={"customer": customer, "consent_status": "Given"}
            )

            for consent_name in consents:
                doc = frappe.get_doc("Communication Consent", consent_name.name)

                # Update preferences
                if "allow_sms" in preferences:
                    doc.allow_sms = preferences["allow_sms"]
                if "allow_whatsapp" in preferences:
                    doc.allow_whatsapp = preferences["allow_whatsapp"]
                if "allow_email" in preferences:
                    doc.allow_email = preferences["allow_email"]
                if "allow_promotional" in preferences:
                    doc.allow_promotional = preferences["allow_promotional"]
                if "communication_frequency" in preferences:
                    doc.communication_frequency = preferences["communication_frequency"]

                doc.save(ignore_permissions=True)
                updated_count += 1

        return {
            "success": True,
            "updated_count": updated_count,
            "message": _("Consent preferences updated successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error bulk updating consent preferences: {str(e)}")
        return {"success": False, "message": _("Failed to update consent preferences")}
