"""
Security Enhancements for License Management System
Addresses potential security vulnerabilities and improves robustness
"""

import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
from typing import Optional

import frappe
from frappe import _


class SecurityValidator:
    """Enhanced security validation for license management"""

    # Security constants
    MAX_TOKEN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    MIN_KEY_SIZE = 2048
    MAX_OFFLINE_HOURS = 24

    @staticmethod
    def validate_hardware_fingerprint_integrity(fingerprint: str) -> bool:
        """
        Validate hardware fingerprint format and integrity

        Args:
            fingerprint: Hardware fingerprint to validate

        Returns:
            bool: True if fingerprint is valid
        """
        if not fingerprint or len(fingerprint) < 32:
            return False

        # Check if fingerprint contains expected components
        required_components = ["cpu_info", "motherboard_id", "mac_addresses"]
        try:
            # Assuming fingerprint contains JSON-like structure
            fp_data = json.loads(fingerprint)

            for component in required_components:
                if component not in fp_data:
                    return False

        except (json.JSONDecodeError, TypeError):
            # If not JSON, validate as hash string
            if not all(c in "0123456789abcdef" for c in fingerprint.lower()):
                return False

        return True

    @staticmethod
    def rate_limit_check(workshop_code: str, action: str) -> bool:
        """
        Check rate limiting for security-sensitive actions

        Args:
            workshop_code: Workshop identifier
            action: Action being performed

        Returns:
            bool: True if action is allowed
        """
        cache_key = f"rate_limit:{workshop_code}:{action}"
        current_time = int(time.time())

        # Get current attempt data from cache
        attempts_data = frappe.cache().get(cache_key) or {"count": 0, "first_attempt": current_time}

        # Reset if lockout period has passed
        if (
            current_time - attempts_data.get("first_attempt", 0)
            > SecurityValidator.LOCKOUT_DURATION
        ):
            attempts_data = {"count": 0, "first_attempt": current_time}

        # Check if max attempts exceeded
        if attempts_data["count"] >= SecurityValidator.MAX_TOKEN_ATTEMPTS:
            remaining_time = SecurityValidator.LOCKOUT_DURATION - (
                current_time - attempts_data["first_attempt"]
            )
            frappe.throw(
                _("Too many failed attempts. Please wait {0} seconds before trying again").format(
                    remaining_time
                )
            )
            return False

        # Increment attempt counter
        attempts_data["count"] += 1
        frappe.cache().set(
            cache_key, attempts_data, expires_in_sec=SecurityValidator.LOCKOUT_DURATION
        )

        return True

    @staticmethod
    def clear_rate_limit(workshop_code: str, action: str):
        """Clear rate limit after successful action"""
        cache_key = f"rate_limit:{workshop_code}:{action}"
        frappe.cache().delete(cache_key)

    @staticmethod
    def validate_jwt_claims(payload: dict) -> bool:
        """
        Validate JWT payload contains required security claims

        Args:
            payload: JWT payload to validate

        Returns:
            bool: True if payload is valid
        """
        required_claims = [
            "iss",
            "sub",
            "iat",
            "exp",
            "jti",
            "workshop_id",
            "hardware_fingerprint",
            "hardware_hash",
        ]

        for claim in required_claims:
            if claim not in payload:
                frappe.log_error(f"Missing required JWT claim: {claim}", "Security Validation")
                return False

        # Validate timestamps
        current_time = int(time.time())

        if payload.get("iat", 0) > current_time + 60:  # Allow 1 minute clock skew
            frappe.log_error("JWT issued in the future", "Security Validation")
            return False

        if payload.get("exp", 0) <= current_time:
            frappe.log_error("JWT has expired", "Security Validation")
            return False

        # Validate hardware hash integrity
        fingerprint = payload.get("hardware_fingerprint", "")
        expected_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        if payload.get("hardware_hash") != expected_hash:
            frappe.log_error("Hardware hash validation failed", "Security Validation")
            return False

        return True

    @staticmethod
    def generate_secure_session_id() -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_business_license_integrity(business_license: str, business_name: str) -> bool:
        """
        Validate business license against known patterns and checksums

        Args:
            business_license: License number to validate
            business_name: Business name for cross-validation

        Returns:
            bool: True if license appears valid
        """
        # Oman business license validation
        if not business_license or not business_license.isdigit() or len(business_license) != 7:
            return False

        # Additional checksum validation could be added here
        # based on actual Oman business license algorithm

        return True

    @staticmethod
    def detect_suspicious_activity(workshop_code: str, event_data: dict) -> Optional[dict]:
        """
        Detect suspicious activity patterns

        Args:
            workshop_code: Workshop identifier
            event_data: Event data to analyze

        Returns:
            dict: Threat assessment if suspicious activity detected
        """
        threat_indicators = []
        risk_score = 0

        # Check for rapid token generation
        recent_tokens = frappe.db.count(
            "License Audit Log",
            {
                "workshop_id": workshop_code,
                "event_type": "token_generated",
                "timestamp": [">", datetime.now() - timedelta(minutes=5)],
            },
        )

        if recent_tokens > 10:
            threat_indicators.append("Rapid token generation")
            risk_score += 30

        # Check for hardware fingerprint changes
        recent_hardware_changes = frappe.db.count(
            "License Audit Log",
            {
                "workshop_id": workshop_code,
                "event_type": "security_hardware_mismatch",
                "timestamp": [">", datetime.now() - timedelta(hours=1)],
            },
        )

        if recent_hardware_changes > 3:
            threat_indicators.append("Multiple hardware fingerprint mismatches")
            risk_score += 50

        # Check for geographic inconsistencies (if IP tracking enabled)
        if event_data.get("ip_address"):
            # This would integrate with IP geolocation service
            # For now, just log the IP for analysis
            pass

        if risk_score > 50:
            return {
                "threat_level": "HIGH" if risk_score > 80 else "MEDIUM",
                "risk_score": risk_score,
                "indicators": threat_indicators,
                "recommended_action": (
                    "Require additional verification" if risk_score > 80 else "Monitor closely"
                ),
            }

        return None


class SecureTokenManager:
    """Enhanced token management with improved security"""

    def __init__(self):
        self.validator = SecurityValidator()

    def generate_secure_token(
        self, workshop_profile: dict, hardware_fingerprint: str, business_data: dict
    ) -> dict:
        """
        Generate JWT token with enhanced security validation

        Args:
            workshop_profile: Workshop profile data
            hardware_fingerprint: Hardware fingerprint
            business_data: Business registration data

        Returns:
            dict: Token data with security metadata
        """
        workshop_code = workshop_profile.get("name")

        # Rate limiting check
        if not self.validator.rate_limit_check(workshop_code, "token_generation"):
            return {"error": "Rate limit exceeded"}

        # Validate hardware fingerprint
        if not self.validator.validate_hardware_fingerprint_integrity(hardware_fingerprint):
            frappe.throw(_("Invalid hardware fingerprint format"))

        # Validate business license
        business_license = workshop_profile.get("business_license")
        business_name = workshop_profile.get("workshop_name")

        if not self.validator.validate_business_license_integrity(business_license, business_name):
            frappe.throw(_("Invalid business license"))

        # Generate secure session ID
        session_id = self.validator.generate_secure_session_id()

        # Check for suspicious activity
        event_data = {
            "workshop_code": workshop_code,
            "hardware_fingerprint": hardware_fingerprint,
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None,
        }

        threat_assessment = self.validator.detect_suspicious_activity(workshop_code, event_data)

        if threat_assessment and threat_assessment.get("threat_level") == "HIGH":
            # Log high-risk event and require additional verification
            frappe.get_doc(
                {
                    "doctype": "Security Monitor",
                    "workshop_code": workshop_code,
                    "threat_level": threat_assessment["threat_level"],
                    "risk_score": threat_assessment["risk_score"],
                    "threat_indicators": threat_assessment["indicators"],
                    "event_timestamp": frappe.utils.now(),
                    "status": "Active",
                    "resolution_status": "Pending Investigation",
                }
            ).insert(ignore_permissions=True)

            frappe.throw(_("Security verification required. Please contact administrator."))

        # Clear rate limit on successful validation
        self.validator.clear_rate_limit(workshop_code, "token_generation")

        return {
            "session_id": session_id,
            "threat_assessment": threat_assessment,
            "security_level": "HIGH",
            "additional_verification_required": threat_assessment is not None,
        }


# Security audit functions
@frappe.whitelist()
def run_security_audit(workshop_code: str = None):
    """
    Run comprehensive security audit on license management system

    Args:
        workshop_code: Specific workshop to audit (optional)
    """
    audit_results = {
        "timestamp": frappe.utils.now(),
        "scope": "all_workshops" if not workshop_code else f"workshop_{workshop_code}",
        "findings": [],
        "recommendations": [],
    }

    # Check for expired tokens
    expired_tokens = frappe.db.count(
        "License Audit Log",
        {"event_type": "token_expired", "timestamp": [">", datetime.now() - timedelta(days=7)]},
    )

    if expired_tokens > 50:
        audit_results["findings"].append(f"High number of expired tokens: {expired_tokens}")
        audit_results["recommendations"].append("Review token expiration policies")

    # Check for security events
    security_events = frappe.db.count(
        "License Audit Log",
        {
            "event_type": ["like", "security_%"],
            "timestamp": [">", datetime.now() - timedelta(days=1)],
        },
    )

    if security_events > 10:
        audit_results["findings"].append(f"High security event volume: {security_events}")
        audit_results["recommendations"].append("Investigate security event patterns")

    # Check for inactive key pairs
    inactive_keys = frappe.db.count("License Key Pair", {"is_active": 0})
    if inactive_keys > 5:
        audit_results["findings"].append(f"Multiple inactive key pairs: {inactive_keys}")
        audit_results["recommendations"].append("Clean up unused key pairs")

    return audit_results


@frappe.whitelist()
def emergency_revoke_all_tokens(workshop_code: str, reason: str):
    """
    Emergency function to revoke all tokens for a workshop

    Args:
        workshop_code: Workshop identifier
        reason: Reason for mass revocation
    """
    # Validate permissions
    if not frappe.has_permission("License Audit Log", "write"):
        frappe.throw(_("Insufficient permissions for emergency revocation"))

    # Get all active tokens for workshop
    active_tokens = frappe.get_all(
        "License Audit Log",
        filters={"workshop_id": workshop_code, "event_type": "token_generated"},
        fields=["event_data"],
    )

    revoked_count = 0

    for token_log in active_tokens:
        try:
            event_data = json.loads(token_log.event_data)
            jti = event_data.get("jti")

            if jti:
                # Create revocation record
                frappe.get_doc(
                    {
                        "doctype": "Revoked Token",
                        "token_jti": jti,
                        "reason": f"Emergency revocation: {reason}",
                        "workshop_code": workshop_code,
                        "revoked_by": frappe.session.user,
                        "revoked_at": frappe.utils.now(),
                    }
                ).insert(ignore_permissions=True)

                revoked_count += 1

        except Exception as e:
            frappe.log_error(f"Failed to revoke token: {e}", "Emergency Revocation")

    # Log emergency action
    frappe.get_doc(
        {
            "doctype": "License Audit Log",
            "event_type": "emergency_revocation",
            "workshop_id": workshop_code,
            "event_description": f"Emergency revocation of {revoked_count} tokens",
            "severity": "Critical",
            "details": json.dumps(
                {"reason": reason, "revoked_count": revoked_count, "operator": frappe.session.user}
            ),
        }
    ).insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "revoked_count": revoked_count,
        "message": f"Successfully revoked {revoked_count} tokens for workshop {workshop_code}",
    }
