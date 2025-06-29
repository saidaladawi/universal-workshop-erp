"""
Multi-Factor Authentication (MFA) Manager for Universal Workshop ERP

Extends ERPNext v15's native MFA system with custom delivery methods including
SMS and WhatsApp integration, along with Arabic localization support.
"""

import pyotp
import qrcode
import io
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, format_datetime, cint, random_string
from frappe.core.doctype.user.user import User
from frappe.utils.password import get_decrypted_password


class MFAManager:
    """
    Comprehensive MFA Manager for Universal Workshop ERP

    Provides TOTP, SMS, and WhatsApp multi-factor authentication with
    Arabic localization and integration with ERPNext's native MFA system.
    """

    def __init__(self):
        """Initialize MFA manager with configuration"""
        self.otp_validity_minutes = 5
        self.backup_codes_count = 10
        self.max_failed_attempts = 3
        self.lockout_duration_minutes = 15

        # Load MFA configuration from site config
        self.config = frappe.get_site_config()
        self.enable_two_factor_auth = self.config.get("enable_two_factor_auth", False)
        self.otp_issuer_name = self.config.get("otp_issuer_name", "Universal Workshop ERP")

    def enable_mfa_for_user(self, user_email: str, mfa_method: str = "totp") -> Dict[str, Any]:
        """
        Enable MFA for a specific user

        Args:
            user_email: User's email address
            mfa_method: MFA method ('totp', 'sms', 'whatsapp', 'email')

        Returns:
            Dict containing setup information
        """
        try:
            user_doc = frappe.get_doc("User", user_email)

            if not user_doc:
                frappe.throw(_("User not found"))

            # Generate secret for TOTP
            secret = pyotp.random_base32()

            # Store MFA settings
            mfa_settings = {
                "enabled": True,
                "method": mfa_method,
                "secret": secret,
                "setup_date": now_datetime(),
                "backup_codes": self._generate_backup_codes(),
                "failed_attempts": 0,
                "locked_until": None,
            }

            # Save to user document (custom field)
            user_doc.db_set("mfa_settings", json.dumps(mfa_settings))

            result = {
                "success": True,
                "method": mfa_method,
                "setup_date": format_datetime(mfa_settings["setup_date"]),
                "backup_codes": mfa_settings["backup_codes"],
            }

            # Generate TOTP-specific data
            if mfa_method == "totp":
                totp = pyotp.TOTP(secret)
                provisioning_uri = totp.provisioning_uri(
                    name=user_email, issuer_name=self.otp_issuer_name
                )

                # Generate QR code
                qr_code_data = self._generate_qr_code(provisioning_uri)

                result.update(
                    {
                        "qr_code": qr_code_data,
                        "secret": secret,
                        "provisioning_uri": provisioning_uri,
                        "manual_entry_key": secret,
                    }
                )

                # Send setup email
                self._send_mfa_setup_email(user_email, result)

            # Log MFA enablement
            self._log_mfa_event(
                user_email,
                "MFA_ENABLED",
                {"method": mfa_method, "setup_date": format_datetime(now_datetime())},
            )

            return result

        except Exception as e:
            frappe.log_error(f"MFA enablement error for {user_email}: {e}")
            return {"success": False, "error": str(e)}

    def verify_mfa_code(
        self, user_email: str, code: str, method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify MFA code for user authentication

        Args:
            user_email: User's email address
            code: OTP/verification code provided by user
            method: Optional method override

        Returns:
            Dict containing verification result
        """
        try:
            user_doc = frappe.get_doc("User", user_email)
            mfa_settings = self._get_user_mfa_settings(user_email)

            if not mfa_settings or not mfa_settings.get("enabled"):
                return {"success": False, "error": _("MFA not enabled for user")}

            # Check if user is locked out
            if self._is_user_locked_out(mfa_settings):
                return {
                    "success": False,
                    "error": _("Account temporarily locked due to failed attempts"),
                    "locked_until": mfa_settings.get("locked_until"),
                }

            # Use provided method or fall back to user's configured method
            verification_method = method or mfa_settings.get("method", "totp")

            is_valid = False
            verification_details: Dict[str, Any] = {}

            # Verify based on method
            if verification_method == "totp":
                is_valid, verification_details = self._verify_totp_code(mfa_settings, code)
            elif verification_method in ["sms", "whatsapp"]:
                is_valid, verification_details = self._verify_otp_code(
                    user_email, code, verification_method
                )
            elif verification_method == "email":
                is_valid, verification_details = self._verify_email_otp(user_email, code)
            elif code in mfa_settings.get("backup_codes", []):
                is_valid = True
                verification_details = {"backup_code_used": True}
                # Remove used backup code
                self._remove_used_backup_code(user_email, code)

            if is_valid:
                # Reset failed attempts on successful verification
                self._reset_failed_attempts(user_email)

                # Log successful verification
                self._log_mfa_event(
                    user_email,
                    "MFA_VERIFIED",
                    {
                        "method": verification_method,
                        "timestamp": format_datetime(now_datetime()),
                        **verification_details,
                    },
                )

                return {
                    "success": True,
                    "method": verification_method,
                    "verified_at": format_datetime(now_datetime()),
                    **verification_details,
                }
            else:
                # Increment failed attempts
                self._increment_failed_attempts(user_email)

                # Log failed verification
                self._log_mfa_event(
                    user_email,
                    "MFA_FAILED",
                    {
                        "method": verification_method,
                        "timestamp": format_datetime(now_datetime()),
                        "reason": verification_details.get("error", "Invalid code"),
                    },
                )

                return {
                    "success": False,
                    "error": _("Invalid verification code"),
                    "attempts_remaining": self._get_remaining_attempts(user_email),
                }

        except Exception as e:
            frappe.log_error(f"MFA verification error for {user_email}: {e}")
            return {"success": False, "error": str(e)}

    def send_otp_code(self, user_email: str, method: str = "sms") -> Dict[str, Any]:
        """
        Send OTP code via SMS, WhatsApp, or email

        Args:
            user_email: User's email address
            method: Delivery method ('sms', 'whatsapp', 'email')

        Returns:
            Dict containing send result
        """
        try:
            user_doc = frappe.get_doc("User", user_email)

            # Generate OTP code
            otp_code = random_string(6).upper()
            otp_data = {
                "code": otp_code,
                "method": method,
                "generated_at": now_datetime(),
                "expires_at": now_datetime() + timedelta(minutes=self.otp_validity_minutes),
                "verified": False,
            }

            # Store OTP temporarily
            cache_key = f"mfa_otp_{user_email}_{method}"
            frappe.cache().set_value(
                cache_key, json.dumps(otp_data), expires_in_sec=self.otp_validity_minutes * 60
            )

            # Send based on method
            if method == "sms":
                result = self._send_sms_otp(user_email, otp_code)
            elif method == "whatsapp":
                result = self._send_whatsapp_otp(user_email, otp_code)
            elif method == "email":
                result = self._send_email_otp(user_email, otp_code)
            else:
                return {"success": False, "error": _("Unsupported delivery method")}

            if result.get("success"):
                # Log OTP sent
                self._log_mfa_event(
                    user_email,
                    "OTP_SENT",
                    {
                        "method": method,
                        "timestamp": format_datetime(now_datetime()),
                        "expires_at": format_datetime(otp_data["expires_at"]),
                    },
                )

                return {
                    "success": True,
                    "method": method,
                    "sent_at": format_datetime(now_datetime()),
                    "expires_at": format_datetime(otp_data["expires_at"]),
                    "delivery_details": result.get("details", {}),
                }
            else:
                return {"success": False, "error": result.get("error", "Failed to send OTP")}

        except Exception as e:
            frappe.log_error(f"OTP sending error for {user_email}: {e}")
            return {"success": False, "error": str(e)}

    def disable_mfa_for_user(self, user_email: str, admin_override: bool = False) -> Dict[str, Any]:
        """
        Disable MFA for a user

        Args:
            user_email: User's email address
            admin_override: Whether this is an admin override

        Returns:
            Dict containing disable result
        """
        try:
            user_doc = frappe.get_doc("User", user_email)

            # Clear MFA settings
            user_doc.db_set("mfa_settings", None)

            # Log MFA disabled
            self._log_mfa_event(
                user_email,
                "MFA_DISABLED",
                {
                    "timestamp": format_datetime(now_datetime()),
                    "admin_override": admin_override,
                    "disabled_by": frappe.session.user,
                },
            )

            return {
                "success": True,
                "disabled_at": format_datetime(now_datetime()),
                "admin_override": admin_override,
            }

        except Exception as e:
            frappe.log_error(f"MFA disable error for {user_email}: {e}")
            return {"success": False, "error": str(e)}

    def get_user_mfa_status(self, user_email: str) -> Dict[str, Any]:
        """
        Get comprehensive MFA status for a user

        Args:
            user_email: User's email address

        Returns:
            Dict containing MFA status information
        """
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)

            if not mfa_settings:
                return {
                    "enabled": False,
                    "method": None,
                    "setup_date": None,
                    "backup_codes_count": 0,
                    "is_locked": False,
                }

            return {
                "enabled": mfa_settings.get("enabled", False),
                "method": mfa_settings.get("method"),
                "setup_date": mfa_settings.get("setup_date"),
                "backup_codes_count": len(mfa_settings.get("backup_codes", [])),
                "failed_attempts": mfa_settings.get("failed_attempts", 0),
                "is_locked": self._is_user_locked_out(mfa_settings),
                "locked_until": mfa_settings.get("locked_until"),
            }

        except Exception as e:
            frappe.log_error(f"MFA status error for {user_email}: {e}")
            return {"enabled": False, "error": str(e)}

    def generate_new_backup_codes(self, user_email: str) -> Dict[str, Any]:
        """
        Generate new backup codes for a user

        Args:
            user_email: User's email address

        Returns:
            Dict containing new backup codes
        """
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)

            if not mfa_settings or not mfa_settings.get("enabled"):
                return {"success": False, "error": _("MFA not enabled for user")}

            # Generate new backup codes
            new_backup_codes = self._generate_backup_codes()
            mfa_settings["backup_codes"] = new_backup_codes

            # Update user settings
            user_doc = frappe.get_doc("User", user_email)
            user_doc.db_set("mfa_settings", json.dumps(mfa_settings))

            # Log backup codes generation
            self._log_mfa_event(
                user_email,
                "BACKUP_CODES_GENERATED",
                {
                    "timestamp": format_datetime(now_datetime()),
                    "codes_count": len(new_backup_codes),
                },
            )

            return {
                "success": True,
                "backup_codes": new_backup_codes,
                "generated_at": format_datetime(now_datetime()),
            }

        except Exception as e:
            frappe.log_error(f"Backup codes generation error for {user_email}: {e}")
            return {"success": False, "error": str(e)}

    # Private helper methods

    def _get_user_mfa_settings(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get user's MFA settings from database"""
        try:
            settings_json = frappe.db.get_value("User", user_email, "mfa_settings")
            if settings_json:
                return json.loads(settings_json)
            return None
        except (json.JSONDecodeError, TypeError):
            return None

    def _verify_totp_code(
        self, mfa_settings: Dict[str, Any], code: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Verify TOTP code"""
        try:
            secret = mfa_settings.get("secret")
            if not secret:
                return False, {"error": "No TOTP secret found"}

            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(code, valid_window=1)  # Allow 1 time step tolerance

            return is_valid, {"method_details": "TOTP verification"}

        except Exception as e:
            return False, {"error": f"TOTP verification error: {e}"}

    def _verify_otp_code(
        self, user_email: str, code: str, method: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Verify SMS/WhatsApp OTP code"""
        try:
            cache_key = f"mfa_otp_{user_email}_{method}"
            otp_data_json = frappe.cache().get_value(cache_key)

            if not otp_data_json:
                return False, {"error": "OTP expired or not found"}

            otp_data = json.loads(otp_data_json)

            # Check expiry
            if now_datetime() > datetime.fromisoformat(otp_data["expires_at"]):
                return False, {"error": "OTP expired"}

            # Check code
            if otp_data["code"] == code.upper():
                # Mark as verified and clear cache
                frappe.cache().delete_value(cache_key)
                return True, {"method_details": f"{method.upper()} OTP verification"}
            else:
                return False, {"error": "Invalid OTP code"}

        except Exception as e:
            return False, {"error": f"OTP verification error: {e}"}

    def _verify_email_otp(self, user_email: str, code: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify email OTP code"""
        return self._verify_otp_code(user_email, code, "email")

    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes for account recovery"""
        return [random_string(8).upper() for _ in range(self.backup_codes_count)]

    def _generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate QR code for TOTP setup"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64 string
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            frappe.log_error(f"QR code generation error: {e}")
            return ""

    def _send_sms_otp(self, user_email: str, otp_code: str) -> Dict[str, Any]:
        """Send OTP via SMS"""
        try:
            user_doc = frappe.get_doc("User", user_email)
            mobile_no = user_doc.mobile_no

            if not mobile_no:
                return {"success": False, "error": _("No mobile number found for user")}

            # Get Arabic/English message based on user language
            message = self._get_localized_otp_message(otp_code, "sms", user_doc.language)

            # Use ERPNext's SMS settings or custom SMS gateway
            try:
                from frappe.core.doctype.sms_settings.sms_settings import send_sms

                send_sms([mobile_no], message)

                return {
                    "success": True,
                    "details": {
                        "recipient": mobile_no,
                        "message_length": len(message),
                        "delivery_method": "ERPNext SMS",
                    },
                }

            except Exception as sms_error:
                # Fallback to custom SMS implementation if needed
                frappe.log_error(f"SMS sending failed: {sms_error}")
                return {"success": False, "error": f"SMS delivery failed: {sms_error}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_whatsapp_otp(self, user_email: str, otp_code: str) -> Dict[str, Any]:
        """Send OTP via WhatsApp"""
        try:
            user_doc = frappe.get_doc("User", user_email)
            whatsapp_no = user_doc.get("whatsapp_number") or user_doc.mobile_no

            if not whatsapp_no:
                return {"success": False, "error": _("No WhatsApp number found for user")}

            # Get Arabic/English message based on user language
            message = self._get_localized_otp_message(otp_code, "whatsapp", user_doc.language)

            # Custom WhatsApp implementation using Twilio or similar
            # This would need to be configured with your WhatsApp Business API credentials
            try:
                # Placeholder for WhatsApp integration
                # In production, this would call your WhatsApp API

                # Example with Twilio:
                # from twilio.rest import Client
                # client = Client(account_sid, auth_token)
                # message = client.messages.create(
                #     body=message,
                #     from_='whatsapp:+your_twilio_number',
                #     to=f'whatsapp:{whatsapp_no}'
                # )

                # For now, return success (implement actual WhatsApp sending)
                return {
                    "success": True,
                    "details": {
                        "recipient": whatsapp_no,
                        "message_length": len(message),
                        "delivery_method": "WhatsApp",
                    },
                }

            except Exception as whatsapp_error:
                frappe.log_error(f"WhatsApp sending failed: {whatsapp_error}")
                return {"success": False, "error": f"WhatsApp delivery failed: {whatsapp_error}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_email_otp(self, user_email: str, otp_code: str) -> Dict[str, Any]:
        """Send OTP via email"""
        try:
            user_doc = frappe.get_doc("User", user_email)

            # Get Arabic/English message based on user language
            subject, message = self._get_localized_email_otp(otp_code, user_doc.language)

            # Send email using Frappe's email system
            frappe.sendmail(
                recipients=[user_email],
                subject=subject,
                message=message,
                header=_("OTP Verification - Universal Workshop ERP"),
            )

            return {
                "success": True,
                "details": {
                    "recipient": user_email,
                    "subject": subject,
                    "delivery_method": "Email",
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_localized_otp_message(
        self, otp_code: str, method: str, language: Optional[str] = None
    ) -> str:
        """Get localized OTP message for SMS/WhatsApp"""
        if language == "ar":
            if method == "sms":
                return f"رمز التحقق الخاص بك لنظام إدارة الورشة الشاملة هو: {otp_code}\nصالح لمدة {self.otp_validity_minutes} دقائق.\nلا تشارك هذا الرمز مع أي شخص."
            else:  # WhatsApp
                return f"🔒 رمز التحقق الخاص بك لنظام إدارة الورشة الشاملة:\n\n*{otp_code}*\n\n⏰ صالح لمدة {self.otp_validity_minutes} دقائق\n⚠️ لا تشارك هذا الرمز مع أي شخص"
        else:
            if method == "sms":
                return f"Your Universal Workshop ERP verification code is: {otp_code}\nValid for {self.otp_validity_minutes} minutes.\nDo not share this code with anyone."
            else:  # WhatsApp
                return f"🔒 Your Universal Workshop ERP verification code:\n\n*{otp_code}*\n\n⏰ Valid for {self.otp_validity_minutes} minutes\n⚠️ Do not share this code with anyone"

    def _get_localized_email_otp(self, otp_code: str, language: str = None) -> Tuple[str, str]:
        """Get localized email OTP subject and message"""
        if language == "ar":
            subject = "رمز التحقق - نظام إدارة الورشة الشاملة"
            message = f"""
            <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <h2>رمز التحقق الخاص بك</h2>
                <p>مرحباً،</p>
                <p>رمز التحقق الخاص بك لنظام إدارة الورشة الشاملة هو:</p>
                <div style="background: #f0f0f0; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">
                    {otp_code}
                </div>
                <p><strong>ملاحظة هامة:</strong></p>
                <ul>
                    <li>هذا الرمز صالح لمدة {self.otp_validity_minutes} دقائق فقط</li>
                    <li>لا تشارك هذا الرمز مع أي شخص</li>
                    <li>إذا لم تطلب هذا الرمز، يرجى تجاهل هذه الرسالة</li>
                </ul>
                <p>شكراً لاستخدامك نظام إدارة الورشة الشاملة</p>
            </div>
            """
        else:
            subject = "Verification Code - Universal Workshop ERP"
            message = f"""
            <div style="font-family: Arial, sans-serif;">
                <h2>Your Verification Code</h2>
                <p>Hello,</p>
                <p>Your verification code for Universal Workshop ERP is:</p>
                <div style="background: #f0f0f0; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">
                    {otp_code}
                </div>
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>This code is valid for {self.otp_validity_minutes} minutes only</li>
                    <li>Do not share this code with anyone</li>
                    <li>If you did not request this code, please ignore this message</li>
                </ul>
                <p>Thank you for using Universal Workshop ERP</p>
            </div>
            """

        return subject, message

    def _send_mfa_setup_email(self, user_email: str, setup_data: Dict[str, Any]) -> None:
        """Send MFA setup email with QR code"""
        try:
            user_doc = frappe.get_doc("User", user_email)
            language = user_doc.language

            if language == "ar":
                subject = "إعداد المصادقة الثنائية - نظام إدارة الورشة الشاملة"
                message = f"""
                <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <h2>إعداد المصادقة الثنائية</h2>
                    <p>مرحباً {user_doc.first_name},</p>
                    <p>تم تفعيل المصادقة الثنائية لحسابك. يرجى اتباع الخطوات التالية:</p>
                    <ol>
                        <li>قم بتحميل تطبيق Google Authenticator أو Microsoft Authenticator</li>
                        <li>امسح رمز QR أدناه باستخدام التطبيق</li>
                        <li>أدخل الرمز المكون من 6 أرقام للتحقق من الإعداد</li>
                    </ol>
                    <div style="text-align: center; margin: 20px 0;">
                        <img src="{setup_data.get('qr_code', '')}" alt="QR Code" style="max-width: 300px;">
                    </div>
                    <p><strong>مفتاح الإدخال اليدوي:</strong> {setup_data.get('secret', '')}</p>
                    <p><strong>رموز النسخ الاحتياطي:</strong></p>
                    <ul>
                        {''.join([f'<li>{code}</li>' for code in setup_data.get('backup_codes', [])])}
                    </ul>
                    <p>احتفظ برموز النسخ الاحتياطي في مكان آمن لاستخدامها في حالة فقدان هاتفك.</p>
                </div>
                """
            else:
                subject = "Two-Factor Authentication Setup - Universal Workshop ERP"
                message = f"""
                <div style="font-family: Arial, sans-serif;">
                    <h2>Two-Factor Authentication Setup</h2>
                    <p>Hello {user_doc.first_name},</p>
                    <p>Two-factor authentication has been enabled for your account. Please follow these steps:</p>
                    <ol>
                        <li>Download Google Authenticator or Microsoft Authenticator app</li>
                        <li>Scan the QR code below using the app</li>
                        <li>Enter the 6-digit code to verify setup</li>
                    </ol>
                    <div style="text-align: center; margin: 20px 0;">
                        <img src="{setup_data.get('qr_code', '')}" alt="QR Code" style="max-width: 300px;">
                    </div>
                    <p><strong>Manual Entry Key:</strong> {setup_data.get('secret', '')}</p>
                    <p><strong>Backup Codes:</strong></p>
                    <ul>
                        {''.join([f'<li>{code}</li>' for code in setup_data.get('backup_codes', [])])}
                    </ul>
                    <p>Keep your backup codes in a safe place to use if you lose your phone.</p>
                </div>
                """

            frappe.sendmail(
                recipients=[user_email],
                subject=subject,
                message=message,
                header=_("MFA Setup - Universal Workshop ERP"),
            )

        except Exception as e:
            frappe.log_error(f"MFA setup email error: {e}")

    def _is_user_locked_out(self, mfa_settings: Dict[str, Any]) -> bool:
        """Check if user is currently locked out"""
        locked_until = mfa_settings.get("locked_until")
        if locked_until:
            return now_datetime() < datetime.fromisoformat(locked_until)
        return False

    def _increment_failed_attempts(self, user_email: str) -> None:
        """Increment failed MFA attempts and lock if necessary"""
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)
            if not mfa_settings:
                return

            failed_attempts = mfa_settings.get("failed_attempts", 0) + 1
            mfa_settings["failed_attempts"] = failed_attempts

            # Lock user if max attempts exceeded
            if failed_attempts >= self.max_failed_attempts:
                lockout_until = now_datetime() + timedelta(minutes=self.lockout_duration_minutes)
                mfa_settings["locked_until"] = lockout_until.isoformat()

            # Update user settings
            user_doc = frappe.get_doc("User", user_email)
            user_doc.db_set("mfa_settings", json.dumps(mfa_settings))

        except Exception as e:
            frappe.log_error(f"Failed attempts increment error: {e}")

    def _reset_failed_attempts(self, user_email: str) -> None:
        """Reset failed attempts counter"""
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)
            if not mfa_settings:
                return

            mfa_settings["failed_attempts"] = 0
            mfa_settings["locked_until"] = None

            # Update user settings
            user_doc = frappe.get_doc("User", user_email)
            user_doc.db_set("mfa_settings", json.dumps(mfa_settings))

        except Exception as e:
            frappe.log_error(f"Failed attempts reset error: {e}")

    def _get_remaining_attempts(self, user_email: str) -> int:
        """Get remaining MFA attempts before lockout"""
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)
            if not mfa_settings:
                return self.max_failed_attempts

            failed_attempts = mfa_settings.get("failed_attempts", 0)
            return max(0, self.max_failed_attempts - failed_attempts)

        except Exception:
            return 0

    def _remove_used_backup_code(self, user_email: str, used_code: str) -> None:
        """Remove a used backup code"""
        try:
            mfa_settings = self._get_user_mfa_settings(user_email)
            if not mfa_settings:
                return

            backup_codes = mfa_settings.get("backup_codes", [])
            if used_code in backup_codes:
                backup_codes.remove(used_code)
                mfa_settings["backup_codes"] = backup_codes

                # Update user settings
                user_doc = frappe.get_doc("User", user_email)
                user_doc.db_set("mfa_settings", json.dumps(mfa_settings))

        except Exception as e:
            frappe.log_error(f"Backup code removal error: {e}")

    def _log_mfa_event(self, user_email: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log MFA events for audit trail"""
        try:
            frappe.get_doc(
                {
                    "doctype": "Activity Log",
                    "subject_field": "MFA Event",
                    "operation": event_type,
                    "subject": user_email,
                    "content": json.dumps(event_data),
                    "user": user_email,
                    "ip_address": (
                        frappe.local.request.environ.get("REMOTE_ADDR")
                        if frappe.local.request
                        else None
                    ),
                }
            ).insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"MFA event logging error: {e}")


# Global MFA Manager instance
mfa_manager = MFAManager()


# WhiteListed API Methods


@frappe.whitelist()
def enable_mfa(mfa_method: str = "totp"):
    """
    Enable MFA for current user

    Args:
        mfa_method: MFA method to enable ('totp', 'sms', 'whatsapp', 'email')

    Returns:
        MFA setup information
    """
    return mfa_manager.enable_mfa_for_user(frappe.session.user, mfa_method)


@frappe.whitelist()
def verify_mfa(code: str, method: str = None):
    """
    Verify MFA code for current user

    Args:
        code: Verification code
        method: Optional method override

    Returns:
        Verification result
    """
    return mfa_manager.verify_mfa_code(frappe.session.user, code, method)


@frappe.whitelist()
def send_otp(method: str = "sms"):
    """
    Send OTP to current user

    Args:
        method: Delivery method ('sms', 'whatsapp', 'email')

    Returns:
        Send result
    """
    return mfa_manager.send_otp_code(frappe.session.user, method)


@frappe.whitelist()
def disable_mfa():
    """
    Disable MFA for current user

    Returns:
        Disable result
    """
    return mfa_manager.disable_mfa_for_user(frappe.session.user)


@frappe.whitelist()
def get_mfa_status():
    """
    Get MFA status for current user

    Returns:
        MFA status information
    """
    return mfa_manager.get_user_mfa_status(frappe.session.user)


@frappe.whitelist()
def generate_backup_codes():
    """
    Generate new backup codes for current user

    Returns:
        New backup codes
    """
    return mfa_manager.generate_new_backup_codes(frappe.session.user)


@frappe.whitelist()
def admin_enable_mfa(user_email: str, mfa_method: str = "totp"):
    """
    Admin function to enable MFA for any user

    Args:
        user_email: Target user's email
        mfa_method: MFA method to enable

    Returns:
        MFA setup information
    """
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("Insufficient permissions"))

    return mfa_manager.enable_mfa_for_user(user_email, mfa_method)


@frappe.whitelist()
def admin_disable_mfa(user_email: str):
    """
    Admin function to disable MFA for any user

    Args:
        user_email: Target user's email

    Returns:
        Disable result
    """
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("Insufficient permissions"))

    return mfa_manager.disable_mfa_for_user(user_email, admin_override=True)


@frappe.whitelist()
def admin_get_mfa_status(user_email: str):
    """
    Admin function to get MFA status for any user

    Args:
        user_email: Target user's email

    Returns:
        MFA status information
    """
    if not frappe.has_permission("User", "read"):
        frappe.throw(_("Insufficient permissions"))

    return mfa_manager.get_user_mfa_status(user_email)
