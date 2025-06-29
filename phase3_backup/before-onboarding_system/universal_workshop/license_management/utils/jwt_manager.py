# JWT Authentication Manager for Universal Workshop License System
# Copyright (c) 2024 Eng. Saeed Al-Adawi

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import frappe
from frappe import _


class JWTManager:
    """
    JWT-based Authentication System using RS256 algorithm
    Provides 24-hour token validation cycles with secure key management
    """

    def __init__(self):
        self.algorithm = "RS256"
        self.token_expiry_hours = 24
        self.issuer = "universal_workshop_license"
        self.key_size = 2048

    def get_or_create_key_pair(self):
        """
        Generate or retrieve RSA key pair for JWT signing
        Returns: License Key Pair document for better encapsulation
        """
        try:
            # Try to get existing active key pair
            existing_keys = frappe.get_doc(
                "License Key Pair", {"is_active": 1, "algorithm": self.algorithm}
            )

            # Verify key integrity
            self._deserialize_private_key(existing_keys.private_key)
            self._deserialize_public_key(existing_keys.public_key)

            return existing_keys

        except frappe.DoesNotExistError:
            # Generate new key pair
            return self._generate_new_key_pair()

    def _generate_new_key_pair(self):
        """
        Generate new RSA key pair and store securely
        """
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=self.key_size, backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        # Store keys in database
        key_doc = frappe.new_doc("License Key Pair")
        key_doc.name = "default"
        key_doc.private_key = private_pem
        key_doc.public_key = public_pem
        key_doc.created_at = frappe.utils.now()
        key_doc.key_size = self.key_size
        key_doc.algorithm = self.algorithm
        key_doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return private_pem, public_pem

    def _deserialize_private_key(self, private_key_pem):
        """Deserialize private key from PEM format"""
        return serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"), password=None, backend=default_backend()
        )

    def _deserialize_public_key(self, public_key_pem):
        """Deserialize public key from PEM format"""
        return serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"), backend=default_backend()
        )

    def generate_license_token(self, workshop_profile, hardware_fingerprint, business_data):
        """
        Generate JWT license token with workshop and hardware binding

        Args:
            workshop_profile (dict): Workshop profile information
            hardware_fingerprint (str): Hardware fingerprint hash
            business_data (dict): Business registration data

        Returns:
            str: Signed JWT token
        """
        private_key_pem, public_key_pem = self.get_or_create_key_pair()
        private_key = self._deserialize_private_key(private_key_pem)

        # Current time and expiration
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.token_expiry_hours)

        # Token payload with all required claims
        payload = {
            # Standard JWT claims
            "iss": self.issuer,  # Issuer
            "sub": workshop_profile.get("name"),  # Subject (workshop ID)
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiration time
            "jti": secrets.token_urlsafe(16),  # JWT ID
            # Workshop-specific claims
            "workshop_id": workshop_profile.get("name"),
            "workshop_name": workshop_profile.get("workshop_name"),
            "workshop_name_ar": workshop_profile.get("workshop_name_ar"),
            "business_license": workshop_profile.get("business_license"),
            "vat_number": workshop_profile.get("vat_number"),
            # Hardware binding
            "hardware_fingerprint": hardware_fingerprint,
            "hardware_hash": hashlib.sha256(hardware_fingerprint.encode()).hexdigest(),
            # Business binding
            "business_name": business_data.get("name"),
            "business_name_ar": business_data.get("name_ar"),
            "owner_name": business_data.get("owner_name"),
            "owner_verified": business_data.get("verified", False),
            # License constraints
            "max_users": workshop_profile.get("max_users", 10),
            "max_vehicles": workshop_profile.get("max_vehicles", 1000),
            "features_enabled": workshop_profile.get("features_enabled", []),
            # Security metadata
            "license_type": "production",
            "security_level": "high",
            "offline_grace_hours": 24,
            "requires_periodic_validation": True,
        }

        # Sign the token
        token = jwt.encode(
            payload=payload,
            key=private_key,
            algorithm=self.algorithm,
            headers={
                "typ": "JWT",
                "alg": self.algorithm,
                "kid": "default",  # Key ID for key rotation
            },
        )

        # Log token generation
        self._log_token_event("generated", payload, workshop_profile.get("name"))

        return token

    def validate_license_token(self, token, hardware_fingerprint=None):
        """
        Validate JWT license token and verify all claims

        Args:
            token (str): JWT token to validate
            hardware_fingerprint (str): Current hardware fingerprint

        Returns:
            dict: Decoded token payload if valid

        Raises:
            jwt.InvalidTokenError: If token is invalid
            ValueError: If hardware fingerprint doesn't match
        """
        try:
            private_key_pem, public_key_pem = self.get_or_create_key_pair()
            public_key = self._deserialize_public_key(public_key_pem)

            # Decode and verify token
            payload = jwt.decode(
                jwt=token,
                key=public_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "require": ["exp", "iat", "iss", "sub"],
                },
            )

            # Verify hardware fingerprint if provided
            if hardware_fingerprint:
                token_fingerprint = payload.get("hardware_fingerprint")
                if not token_fingerprint or token_fingerprint != hardware_fingerprint:
                    self._log_security_event(
                        "hardware_mismatch",
                        {
                            "expected": token_fingerprint,
                            "actual": hardware_fingerprint,
                            "workshop_id": payload.get("workshop_id"),
                        },
                    )
                    raise ValueError("Hardware fingerprint mismatch")

                # Verify hardware hash
                expected_hash = hashlib.sha256(hardware_fingerprint.encode()).hexdigest()
                if payload.get("hardware_hash") != expected_hash:
                    raise ValueError("Hardware hash verification failed")

            # Log successful validation
            self._log_token_event("validated", payload, payload.get("workshop_id"))

            return payload

        except jwt.ExpiredSignatureError:
            self._log_security_event("token_expired", {"token_preview": token[:20] + "..."})
            raise
        except jwt.InvalidSignatureError:
            self._log_security_event("invalid_signature", {"token_preview": token[:20] + "..."})
            raise
        except jwt.InvalidTokenError as e:
            self._log_security_event(
                "invalid_token", {"error": str(e), "token_preview": token[:20] + "..."}
            )
            raise

    def refresh_token(self, current_token, hardware_fingerprint):
        """
        Refresh JWT token if valid and within refresh window

        Args:
            current_token (str): Current JWT token
            hardware_fingerprint (str): Hardware fingerprint for validation

        Returns:
            str: New JWT token or None if refresh not allowed
        """
        try:
            # Validate current token
            payload = self.validate_license_token(current_token, hardware_fingerprint)

            # Check if token is within refresh window (last 6 hours of validity)
            exp_timestamp = payload.get("exp")
            current_timestamp = datetime.utcnow().timestamp()
            refresh_window = 6 * 3600  # 6 hours in seconds

            if (exp_timestamp - current_timestamp) > refresh_window:
                # Too early to refresh
                return None

            # Get workshop and business data for new token
            workshop_id = payload.get("workshop_id")
            workshop_profile = frappe.get_doc("Workshop Profile", workshop_id)

            business_data = {
                "name": payload.get("business_name"),
                "name_ar": payload.get("business_name_ar"),
                "owner_name": payload.get("owner_name"),
                "verified": payload.get("owner_verified"),
            }

            # Generate new token
            new_token = self.generate_license_token(
                workshop_profile.as_dict(), hardware_fingerprint, business_data
            )

            self._log_token_event("refreshed", payload, workshop_id)

            return new_token

        except Exception as e:
            self._log_security_event("refresh_failed", {"error": str(e)})
            return None

    def revoke_token(self, token, reason="manual_revocation"):
        """
        Revoke a JWT token by adding it to blacklist

        Args:
            token (str): Token to revoke
            reason (str): Reason for revocation
        """
        try:
            # Decode token to get JTI
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Add to revocation list
                revocation = frappe.new_doc("Revoked Token")
                revocation.jti = jti
                revocation.expires_at = datetime.fromtimestamp(exp)
                revocation.reason = reason
                revocation.revoked_at = frappe.utils.now()
                revocation.workshop_id = payload.get("workshop_id")
                revocation.insert(ignore_permissions=True)

                frappe.db.commit()

                self._log_security_event(
                    "token_revoked",
                    {"jti": jti, "reason": reason, "workshop_id": payload.get("workshop_id")},
                )

        except Exception as e:
            frappe.log_error(f"Token revocation failed: {e!s}")

    def is_token_revoked(self, token):
        """
        Check if token is in revocation list

        Args:
            token (str): Token to check

        Returns:
            bool: True if token is revoked
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")

            if jti:
                return frappe.db.exists("Revoked Token", {"jti": jti})

        except Exception:
            pass

        return False

    def cleanup_expired_tokens(self):
        """
        Clean up expired tokens from revocation list
        """
        current_time = frappe.utils.now()

        expired_tokens = frappe.get_all(
            "Revoked Token", filters={"expires_at": ["<", current_time]}, pluck="name"
        )

        for token_name in expired_tokens:
            frappe.delete_doc("Revoked Token", token_name, ignore_permissions=True)

        if expired_tokens:
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up {len(expired_tokens)} expired revoked tokens")

    def _log_token_event(self, event_type, payload, workshop_id):
        """Log token events for audit trail"""
        try:
            log_entry = frappe.new_doc("License Audit Log")
            log_entry.event_type = f"token_{event_type}"
            log_entry.workshop_id = workshop_id
            log_entry.event_data = json.dumps(
                {"jti": payload.get("jti"), "exp": payload.get("exp"), "iat": payload.get("iat")}
            )
            log_entry.timestamp = frappe.utils.now()
            log_entry.ip_address = (
                frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None
            )
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to log token event: {e!s}")

    def _log_security_event(self, event_type, event_data):
        """Log security events for monitoring"""
        try:
            log_entry = frappe.new_doc("License Audit Log")
            log_entry.event_type = f"security_{event_type}"
            log_entry.event_data = json.dumps(event_data)
            log_entry.timestamp = frappe.utils.now()
            log_entry.severity = (
                "high" if event_type in ["hardware_mismatch", "invalid_signature"] else "medium"
            )
            log_entry.ip_address = (
                frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None
            )
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to log security event: {e!s}")
