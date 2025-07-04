# -*- coding: utf-8 -*-
"""
Oman-Compliant Twilio Client for SMS and WhatsApp Integration (2025)
Implements strict regulatory compliance for Oman/UAE market with Arabic RTL support
"""

import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Tuple
import requests
import frappe
from frappe import _
from frappe.utils import cstr, get_datetime, now_datetime, get_time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class OmanTwilioClient:
    """
    Oman-compliant Twilio client for SMS and WhatsApp messaging
    Implements 2025 regulatory requirements and Arabic RTL support
    """

    def __init__(self):
        """Initialize Twilio client with Oman compliance settings"""
        self.account_sid = self._get_secure_config("twilio_account_sid")
        self.auth_token = self._get_secure_config("twilio_auth_token")
        self.from_phone = self._get_secure_config("twilio_from_phone")
        self.whatsapp_from = self._get_secure_config(
            "twilio_whatsapp_from", "whatsapp:+14155238886"
        )

        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)

        # Oman regulatory settings
        self.country_code = "+968"
        self.business_hours = {"start": "07:00", "end": "21:00"}
        self.max_sms_length_arabic = 70  # UCS-2 encoding limitation
        self.max_sms_length_english = 160

        # Content filtering patterns for Oman/UAE compliance
        self.prohibited_content_patterns = [
            r"(?i)(gambling|casino|bet)",
            r"(?i)(alcohol|beer|wine|liquor)",
            r"(?i)(adult|porn|sex)",
            r"(?i)(political|election)",
            r"(?i)(religious|islam|christian)",
            r"(?i)(controlled substances|drugs)",
            r"https?://[^\s]+",  # URLs not allowed in UAE
            r"whatsapp\.com",  # WhatsApp links not allowed in UAE
            r"\+\d{10,15}",  # Phone numbers in body not allowed in UAE
        ]

    def _get_secure_config(self, key: str, default: str = None) -> str:
        """Get configuration from secure Frappe settings"""
        try:
            # Try getting from site_config first
            value = frappe.conf.get(key)
            if value:
                return value

            # Try getting from System Settings
            system_settings = frappe.get_single("System Settings")
            if hasattr(system_settings, key):
                return getattr(system_settings, key)

            # Try getting from Communication Settings (custom DocType)
            if frappe.db.exists("DocType", "Communication Settings"):
                comm_settings = frappe.get_single("Communication Settings")
                if hasattr(comm_settings, key):
                    return getattr(comm_settings, key)

            if default:
                return default

            frappe.throw(_("Configuration {0} not found").format(key))

        except Exception as e:
            frappe.log_error(f"Error getting config {key}: {str(e)}")
            if default:
                return default
            raise

    def validate_oman_phone_number(self, phone: str) -> Tuple[bool, str]:
        """
        Validate Oman phone number format
        Returns: (is_valid, formatted_number)
        """
        # Remove all non-digit characters except +
        clean_phone = re.sub(r"[^\d+]", "", phone)

        # Oman phone number patterns
        patterns = [
            r"^\+968\d{8}$",  # +968XXXXXXXX
            r"^968\d{8}$",  # 968XXXXXXXX
            r"^00968\d{8}$",  # 00968XXXXXXXX
            r"^\d{8}$",  # XXXXXXXX (local)
        ]

        for pattern in patterns:
            if re.match(pattern, clean_phone):
                # Format to international standard
                if clean_phone.startswith("+968"):
                    return True, clean_phone
                elif clean_phone.startswith("968"):
                    return True, f"+{clean_phone}"
                elif clean_phone.startswith("00968"):
                    return True, f"+{clean_phone[2:]}"
                else:  # Local 8-digit number
                    return True, f"+968{clean_phone}"

        return False, phone

    def validate_content_compliance(
        self, message: str, target_country: str = "OM"
    ) -> Tuple[bool, List[str]]:
        """
        Validate message content for Oman/UAE regulatory compliance
        Returns: (is_compliant, list_of_violations)
        """
        violations = []

        # Check for prohibited content patterns
        for pattern in self.prohibited_content_patterns:
            if re.search(pattern, message):
                violations.append(f"Prohibited content detected: {pattern}")

        # UAE-specific restrictions
        if target_country in ["AE", "UAE"]:
            # Check message timing for promotional content
            current_time = get_time()
            business_start = get_time(self.business_hours["start"])
            business_end = get_time(self.business_hours["end"])

            if not (business_start <= current_time <= business_end):
                # This is outside business hours - mark as potential violation
                violations.append("Message sent outside permitted hours (7:00am-9:00pm)")

        return len(violations) == 0, violations

    def detect_arabic_content(self, text: str) -> bool:
        """Detect if text contains Arabic characters"""
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return bool(arabic_pattern.search(text))

    def calculate_sms_segments(self, message: str) -> Dict[str, int]:
        """
        Calculate SMS segments for Arabic and English content
        Arabic uses UCS-2 encoding (70 chars per segment)
        English uses GSM 7-bit (160 chars per segment)
        """
        is_arabic = self.detect_arabic_content(message)

        if is_arabic:
            segment_length = self.max_sms_length_arabic
            # For multi-segment, each segment is reduced (67 chars for Arabic)
            if len(message) > segment_length:
                segment_length = 67
        else:
            segment_length = self.max_sms_length_english
            # For multi-segment, each segment is reduced (153 chars for English)
            if len(message) > segment_length:
                segment_length = 153

        segments = (len(message) + segment_length - 1) // segment_length

        return {
            "message_length": len(message),
            "segment_length": segment_length,
            "total_segments": segments,
            "is_arabic": is_arabic,
            "encoding": "UCS-2" if is_arabic else "GSM 7-bit",
        }

    def send_sms(
        self,
        to: str,
        message: str,
        customer_id: str = None,
        template_name: str = None,
        context: Dict = None,
    ) -> Dict[str, any]:
        """
        Send SMS with Oman regulatory compliance
        """
        try:
            # Validate phone number
            is_valid, formatted_phone = self.validate_oman_phone_number(to)
            if not is_valid:
                raise ValueError(f"Invalid Oman phone number: {to}")

            # Detect target country from phone number
            target_country = "OM"  # Default to Oman
            if formatted_phone.startswith("+971"):
                target_country = "AE"  # UAE

            # Validate content compliance
            is_compliant, violations = self.validate_content_compliance(message, target_country)
            if not is_compliant:
                raise ValueError(f"Content compliance violations: {', '.join(violations)}")

            # Calculate segments and cost estimation
            segment_info = self.calculate_sms_segments(message)

            # Send SMS via Twilio
            twilio_message = self.client.messages.create(
                body=message, from_=self.from_phone, to=formatted_phone
            )

            # Log communication in ERPNext
            self._log_communication(
                communication_type="SMS",
                phone_number=formatted_phone,
                message=message,
                status="Sent",
                provider_message_id=twilio_message.sid,
                customer_id=customer_id,
                template_name=template_name,
                segment_info=segment_info,
                target_country=target_country,
            )

            return {
                "success": True,
                "message_id": twilio_message.sid,
                "status": twilio_message.status,
                "formatted_phone": formatted_phone,
                "segment_info": segment_info,
                "compliance_checked": True,
            }

        except TwilioRestException as e:
            error_msg = f"Twilio SMS error: {e.msg}"
            frappe.log_error(error_msg, "SMS Send Error")

            self._log_communication(
                communication_type="SMS",
                phone_number=to,
                message=message,
                status="Failed",
                error_message=error_msg,
                customer_id=customer_id,
                template_name=template_name,
            )

            return {"success": False, "error": error_msg, "error_code": e.code}

        except Exception as e:
            error_msg = f"SMS send error: {str(e)}"
            frappe.log_error(error_msg, "SMS Send Error")

            return {"success": False, "error": error_msg}

    def send_whatsapp(
        self,
        to: str,
        template_name: str,
        template_data: Dict = None,
        customer_id: str = None,
        language: str = "ar",
    ) -> Dict[str, any]:
        """
        Send WhatsApp message using approved templates with Oman compliance
        """
        try:
            # Validate phone number
            is_valid, formatted_phone = self.validate_oman_phone_number(to)
            if not is_valid:
                raise ValueError(f"Invalid Oman phone number: {to}")

            # Format for WhatsApp
            whatsapp_phone = f"whatsapp:{formatted_phone}"

            # Get approved template from ERPNext
            template_doc = self._get_whatsapp_template(template_name, language)
            if not template_doc:
                raise ValueError(
                    f"WhatsApp template '{template_name}' not found for language '{language}'"
                )

            # Validate template approval status
            if not template_doc.get("is_approved"):
                raise ValueError(f"WhatsApp template '{template_name}' is not approved")

            # Render template with data
            rendered_message = self._render_template(
                template_doc.get("template_content"), template_data or {}
            )

            # Validate content compliance
            is_compliant, violations = self.validate_content_compliance(rendered_message)
            if not is_compliant:
                raise ValueError(f"Content compliance violations: {', '.join(violations)}")

            # Send WhatsApp message via Twilio
            twilio_message = self.client.messages.create(
                body=rendered_message, from_=self.whatsapp_from, to=whatsapp_phone
            )

            # Log communication in ERPNext
            self._log_communication(
                communication_type="WhatsApp",
                phone_number=formatted_phone,
                message=rendered_message,
                status="Sent",
                provider_message_id=twilio_message.sid,
                customer_id=customer_id,
                template_name=template_name,
                language=language,
            )

            return {
                "success": True,
                "message_id": twilio_message.sid,
                "status": twilio_message.status,
                "formatted_phone": formatted_phone,
                "template_used": template_name,
                "language": language,
                "compliance_checked": True,
            }

        except TwilioRestException as e:
            error_msg = f"Twilio WhatsApp error: {e.msg}"
            frappe.log_error(error_msg, "WhatsApp Send Error")

            self._log_communication(
                communication_type="WhatsApp",
                phone_number=to,
                message=template_name,
                status="Failed",
                error_message=error_msg,
                customer_id=customer_id,
                template_name=template_name,
            )

            return {"success": False, "error": error_msg, "error_code": e.code}

        except Exception as e:
            error_msg = f"WhatsApp send error: {str(e)}"
            frappe.log_error(error_msg, "WhatsApp Send Error")

            return {"success": False, "error": error_msg}

    def _get_whatsapp_template(self, template_name: str, language: str = "ar") -> Dict:
        """Get WhatsApp template from ERPNext DocType"""
        try:
            if not frappe.db.exists("DocType", "WhatsApp Template"):
                return None

            template = frappe.db.get_value(
                "WhatsApp Template",
                {"template_name": template_name, "language": language},
                ["template_content", "is_approved", "template_type"],
                as_dict=True,
            )

            return template

        except Exception as e:
            frappe.log_error(f"Error getting WhatsApp template: {str(e)}")
            return None

    def _render_template(self, template: str, context: Dict) -> str:
        """Render template with context data"""
        try:
            # Simple template rendering - can be enhanced with Jinja2
            rendered = template
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))

            return rendered

        except Exception as e:
            frappe.log_error(f"Error rendering template: {str(e)}")
            return template

    def _log_communication(
        self, communication_type: str, phone_number: str, message: str, status: str, **kwargs
    ) -> str:
        """Log communication in ERPNext Communication DocType"""
        try:
            # Create Communication log
            communication = frappe.new_doc("Communication")
            communication.communication_type = "Automated Message"
            communication.communication_medium = communication_type
            communication.sender = frappe.session.user
            communication.recipients = phone_number
            communication.subject = (
                f"{communication_type} - {kwargs.get('template_name', 'Manual')}"
            )
            communication.content = message
            communication.status = status

            # Link to customer if provided
            if kwargs.get("customer_id"):
                communication.reference_doctype = "Customer"
                communication.reference_name = kwargs.get("customer_id")

            # Add custom fields for our tracking
            if hasattr(communication, "provider_message_id"):
                communication.provider_message_id = kwargs.get("provider_message_id")
            if hasattr(communication, "template_name"):
                communication.template_name = kwargs.get("template_name")
            if hasattr(communication, "segment_info"):
                communication.segment_info = json.dumps(kwargs.get("segment_info", {}))
            if hasattr(communication, "compliance_status"):
                communication.compliance_status = (
                    "Compliant" if kwargs.get("compliance_checked") else "Not Checked"
                )
            if hasattr(communication, "error_message"):
                communication.error_message = kwargs.get("error_message")

            communication.insert(ignore_permissions=True)

            return communication.name

        except Exception as e:
            frappe.log_error(f"Error logging communication: {str(e)}")
            return None

    def get_delivery_status(self, message_id: str) -> Dict[str, any]:
        """Get delivery status from Twilio"""
        try:
            message = self.client.messages(message_id).fetch()

            return {
                "message_id": message_id,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent,
                "date_updated": message.date_updated,
                "price": message.price,
                "price_unit": message.price_unit,
            }

        except TwilioRestException as e:
            return {
                "message_id": message_id,
                "status": "unknown",
                "error": f"Error fetching status: {e.msg}",
            }

    def bulk_send_sms(self, recipients: List[Dict], template_name: str = None) -> Dict[str, any]:
        """
        Send bulk SMS with rate limiting for Oman compliance
        recipients: [{"phone": "+968xxxxxxxx", "customer_id": "CUST-001", "context": {...}}]
        """
        results = {"total": len(recipients), "sent": 0, "failed": 0, "details": []}

        for recipient in recipients:
            try:
                # Rate limiting - respect Twilio limits
                time.sleep(0.1)  # 10 requests per second

                result = self.send_sms(
                    to=recipient.get("phone"),
                    message=recipient.get("message"),
                    customer_id=recipient.get("customer_id"),
                    template_name=template_name,
                    context=recipient.get("context"),
                )

                if result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1

                results["details"].append(
                    {
                        "phone": recipient.get("phone"),
                        "success": result.get("success"),
                        "message_id": result.get("message_id"),
                        "error": result.get("error"),
                    }
                )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    {"phone": recipient.get("phone"), "success": False, "error": str(e)}
                )

        return results


# Singleton instance for module use
_twilio_client = None


def get_twilio_client() -> OmanTwilioClient:
    """Get singleton Twilio client instance"""
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = OmanTwilioClient()
    return _twilio_client
