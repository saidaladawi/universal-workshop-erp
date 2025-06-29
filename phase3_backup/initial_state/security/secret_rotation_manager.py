"""
Automated Secret Rotation Manager for Universal Workshop ERP

Provides automated rotation of secrets, API keys, and cryptographic material
to enhance security and reduce the risk of long-term credential compromise.
"""

import os
import re
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import frappe
from frappe import _
from frappe.utils import get_datetime, now, cint


class SecretRotationManager:
    """
    Automated secret rotation management system

    Handles rotation of:
    - JWT signing keys
    - Database encryption keys
    - API keys (Twilio, payment gateways, etc.)
    - Session secrets
    - File encryption keys
    """

    def __init__(self):
        """Initialize secret rotation manager"""
        self.rotation_config = self._load_rotation_config()
        self.secret_store = SecretStore()

    def _load_rotation_config(self) -> Dict[str, Any]:
        """Load rotation configuration from site config"""
        site_config = frappe.get_site_config()
        return site_config.get(
            "secret_rotation",
            {
                "jwt_key_rotation_days": 30,
                "api_key_rotation_days": 90,
                "session_secret_rotation_days": 7,
                "encryption_key_rotation_days": 365,
                "auto_rotation_enabled": True,
                "notification_before_days": 7,
                "backup_old_secrets": True,
                "max_backup_versions": 5,
            },
        )

    def rotate_all_secrets(self, force: bool = False) -> Dict[str, Any]:
        """
        Rotate all secrets that are due for rotation

        Args:
            force: Force rotation regardless of schedule

        Returns:
            Dict with rotation results
        """
        rotation_results = {
            "timestamp": now(),
            "rotated_secrets": [],
            "failed_rotations": [],
            "skipped_secrets": [],
            "total_processed": 0,
        }

        try:
            # Get all secrets due for rotation
            secrets_to_rotate = self._get_secrets_due_for_rotation(force)
            rotation_results["total_processed"] = len(secrets_to_rotate)

            for secret_info in secrets_to_rotate:
                try:
                    result = self._rotate_secret(secret_info)
                    if result["success"]:
                        rotation_results["rotated_secrets"].append(result)
                    else:
                        rotation_results["failed_rotations"].append(result)

                except Exception as e:
                    frappe.log_error(f"Secret rotation failed for {secret_info['name']}: {e}")
                    rotation_results["failed_rotations"].append(
                        {"secret_name": secret_info["name"], "error": str(e), "success": False}
                    )

            # Log rotation summary
            self._log_rotation_summary(rotation_results)

            # Send notifications if needed
            if rotation_results["failed_rotations"]:
                self._send_rotation_failure_alert(rotation_results)

            return rotation_results

        except Exception as e:
            frappe.log_error(f"Secret rotation manager error: {e}")
            raise

    def _get_secrets_due_for_rotation(self, force: bool = False) -> List[Dict[str, Any]]:
        """Get list of secrets that need rotation"""
        secrets_due = []

        # Define secret types and their rotation schedules
        secret_types = [
            {
                "name": "jwt_signing_key",
                "rotation_days": self.rotation_config["jwt_key_rotation_days"],
                "critical": True,
            },
            {
                "name": "session_secret",
                "rotation_days": self.rotation_config["session_secret_rotation_days"],
                "critical": True,
            },
            {
                "name": "api_keys",
                "rotation_days": self.rotation_config["api_key_rotation_days"],
                "critical": False,
            },
            {
                "name": "encryption_keys",
                "rotation_days": self.rotation_config["encryption_key_rotation_days"],
                "critical": True,
            },
        ]

        for secret_type in secret_types:
            if force or self._is_rotation_due(secret_type):
                secrets_due.append(secret_type)

        return secrets_due

    def _is_rotation_due(self, secret_info: Dict[str, Any]) -> bool:
        """Check if a secret is due for rotation"""
        try:
            # Get last rotation timestamp
            last_rotation = self.secret_store.get_secret_metadata(
                secret_info["name"], "last_rotation"
            )

            if not last_rotation:
                return True  # Never rotated, needs rotation

            last_rotation_date = get_datetime(last_rotation)
            rotation_interval = timedelta(days=secret_info["rotation_days"])
            next_rotation_due = last_rotation_date + rotation_interval

            return datetime.now() >= next_rotation_due

        except Exception as e:
            frappe.log_error(f"Error checking rotation due for {secret_info['name']}: {e}")
            return False

    def _rotate_secret(self, secret_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate a specific secret"""
        secret_name = secret_info["name"]

        try:
            # Backup current secret if enabled
            if self.rotation_config["backup_old_secrets"]:
                self._backup_current_secret(secret_name)

            # Generate new secret based on type
            new_secret = self._generate_new_secret(secret_info)

            # Store new secret
            self.secret_store.store_secret(secret_name, new_secret)

            # Update metadata
            self.secret_store.update_secret_metadata(
                secret_name,
                {
                    "last_rotation": now(),
                    "rotation_count": self.secret_store.get_secret_metadata(
                        secret_name, "rotation_count", 0
                    )
                    + 1,
                    "rotated_by": frappe.session.user,
                },
            )

            # Apply secret to system
            self._apply_secret_to_system(secret_name, new_secret)

            # Log successful rotation
            frappe.logger().info(f"Successfully rotated secret: {secret_name}")

            return {
                "secret_name": secret_name,
                "success": True,
                "timestamp": now(),
                "new_secret_id": hashlib.sha256(str(new_secret).encode()).hexdigest()[:16],
            }

        except Exception as e:
            frappe.log_error(f"Failed to rotate secret {secret_name}: {e}")
            return {
                "secret_name": secret_name,
                "success": False,
                "error": str(e),
                "timestamp": now(),
            }

    def _generate_new_secret(self, secret_info: Dict[str, Any]) -> Any:
        """Generate new secret based on type"""
        secret_name = secret_info["name"]

        if secret_name == "jwt_signing_key":
            return self._generate_jwt_key_pair()
        elif secret_name == "session_secret":
            return secrets.token_urlsafe(64)
        elif secret_name == "api_keys":
            return self._generate_api_keys()
        elif secret_name == "encryption_keys":
            return self._generate_encryption_key()
        else:
            # Default: secure random string
            return secrets.token_urlsafe(32)

    def _generate_jwt_key_pair(self) -> Dict[str, str]:
        """Generate new RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return {
            "private_key": private_pem,
            "public_key": public_pem,
            "key_id": secrets.token_urlsafe(16),
        }

    def _generate_api_keys(self) -> Dict[str, str]:
        """Generate new API keys for external services"""
        return {
            "internal_api_key": secrets.token_urlsafe(32),
            "webhook_secret": secrets.token_urlsafe(24),
            "file_access_token": secrets.token_urlsafe(28),
        }

    def _generate_encryption_key(self) -> str:
        """Generate new encryption key"""
        return Fernet.generate_key().decode("utf-8")

    def _backup_current_secret(self, secret_name: str) -> bool:
        """Backup current secret before rotation"""
        try:
            current_secret = self.secret_store.get_secret(secret_name)
            if not current_secret:
                return True  # No current secret to backup

            backup_timestamp = now().replace(" ", "_").replace(":", "-")
            backup_name = f"{secret_name}_backup_{backup_timestamp}"

            self.secret_store.store_secret(backup_name, current_secret, is_backup=True)

            # Clean up old backups
            self._cleanup_old_backups(secret_name)

            return True

        except Exception as e:
            frappe.log_error(f"Failed to backup secret {secret_name}: {e}")
            return False

    def _cleanup_old_backups(self, secret_name: str):
        """Clean up old backup versions"""
        try:
            max_backups = self.rotation_config["max_backup_versions"]
            backups = self.secret_store.get_secret_backups(secret_name)

            if len(backups) > max_backups:
                # Sort by timestamp and keep only the latest ones
                backups.sort(key=lambda x: x["timestamp"], reverse=True)
                backups_to_delete = backups[max_backups:]

                for backup in backups_to_delete:
                    self.secret_store.delete_secret(backup["name"])

        except Exception as e:
            frappe.log_error(f"Failed to cleanup old backups for {secret_name}: {e}")

    def _apply_secret_to_system(self, secret_name: str, new_secret: Any):
        """Apply rotated secret to system configuration"""
        try:
            if secret_name == "jwt_signing_key":
                self._update_jwt_configuration(new_secret)
            elif secret_name == "session_secret":
                self._update_session_configuration(new_secret)
            elif secret_name == "encryption_keys":
                self._update_encryption_configuration(new_secret)
            elif secret_name == "api_keys":
                self._update_api_key_configuration(new_secret)

        except Exception as e:
            frappe.log_error(f"Failed to apply secret {secret_name} to system: {e}")
            raise

    def _update_jwt_configuration(self, jwt_keys: Dict[str, str]):
        """Update JWT configuration with new keys"""
        # Update site config
        site_config = frappe.get_site_config()
        site_config["jwt_private_key"] = jwt_keys["private_key"]
        site_config["jwt_public_key"] = jwt_keys["public_key"]
        site_config["jwt_key_id"] = jwt_keys["key_id"]

        frappe.get_site().update_site_config(site_config)

    def _update_session_configuration(self, session_secret: str):
        """Update session configuration with new secret"""
        site_config = frappe.get_site_config()
        site_config["session_secret"] = session_secret
        frappe.get_site().update_site_config(site_config)

    def _update_encryption_configuration(self, encryption_key: str):
        """Update encryption configuration with new key"""
        site_config = frappe.get_site_config()
        site_config["encryption_key"] = encryption_key
        frappe.get_site().update_site_config(site_config)

    def _update_api_key_configuration(self, api_keys: Dict[str, str]):
        """Update API key configuration"""
        site_config = frappe.get_site_config()
        site_config.update(
            {
                "internal_api_key": api_keys["internal_api_key"],
                "webhook_secret": api_keys["webhook_secret"],
                "file_access_token": api_keys["file_access_token"],
            }
        )
        frappe.get_site().update_site_config(site_config)

    def _log_rotation_summary(self, results: Dict[str, Any]):
        """Log rotation summary for audit trail"""
        summary = {
            "timestamp": results["timestamp"],
            "total_processed": results["total_processed"],
            "successful_rotations": len(results["rotated_secrets"]),
            "failed_rotations": len(results["failed_rotations"]),
            "rotated_by": frappe.session.user,
            "details": results,
        }

        # Store in audit log
        frappe.logger().info(f"Secret rotation summary: {json.dumps(summary, indent=2)}")

    def _send_rotation_failure_alert(self, results: Dict[str, Any]):
        """Send alert for failed rotations"""
        try:
            from universal_workshop.communication.notification_manager import send_security_alert

            message = f"Secret rotation failures detected:\n"
            for failure in results["failed_rotations"]:
                message += f"- {failure['secret_name']}: {failure.get('error', 'Unknown error')}\n"

            send_security_alert(title="Secret Rotation Failures", message=message, severity="high")

        except Exception as e:
            frappe.log_error(f"Failed to send rotation failure alert: {e}")

    def get_rotation_status(self) -> Dict[str, Any]:
        """Get current rotation status for all secrets"""
        status = {"last_rotation_check": now(), "secrets": {}}

        secret_types = ["jwt_signing_key", "session_secret", "api_keys", "encryption_keys"]

        for secret_type in secret_types:
            try:
                metadata = self.secret_store.get_all_secret_metadata(secret_type)
                next_rotation = self._calculate_next_rotation_date(secret_type)

                status["secrets"][secret_type] = {
                    "last_rotation": metadata.get("last_rotation"),
                    "next_rotation": next_rotation,
                    "rotation_count": metadata.get("rotation_count", 0),
                    "days_until_rotation": self._days_until_next_rotation(next_rotation),
                    "status": "current" if next_rotation > datetime.now() else "overdue",
                }

            except Exception as e:
                status["secrets"][secret_type] = {"error": str(e), "status": "error"}

        return status

    def _calculate_next_rotation_date(self, secret_type: str) -> datetime:
        """Calculate next rotation date for a secret type"""
        last_rotation = self.secret_store.get_secret_metadata(secret_type, "last_rotation")
        if not last_rotation:
            return datetime.now()  # Immediate rotation needed

        rotation_days = self.rotation_config.get(f"{secret_type}_rotation_days", 30)
        return get_datetime(last_rotation) + timedelta(days=rotation_days)

    def _days_until_next_rotation(self, next_rotation: datetime) -> int:
        """Calculate days until next rotation"""
        delta = next_rotation - datetime.now()
        return max(0, delta.days)


class SecretStore:
    """Secure storage for secrets and metadata"""

    def __init__(self):
        """Initialize secret store"""
        self.store_path = frappe.get_site_path("private", "secrets")
        os.makedirs(self.store_path, exist_ok=True)

    def store_secret(self, name: str, secret: Any, is_backup: bool = False):
        """Store a secret securely"""
        try:
            secret_data = {
                "secret": secret,
                "created": now(),
                "is_backup": is_backup,
                "checksum": hashlib.sha256(str(secret).encode()).hexdigest(),
            }

            # Encrypt secret data
            encrypted_data = self._encrypt_data(json.dumps(secret_data))

            # Store to file
            secret_file = os.path.join(self.store_path, f"{name}.enc")
            with open(secret_file, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            os.chmod(secret_file, 0o600)

        except Exception as e:
            frappe.log_error(f"Failed to store secret {name}: {e}")
            raise

    def get_secret(self, name: str) -> Any:
        """Retrieve a secret"""
        try:
            secret_file = os.path.join(self.store_path, f"{name}.enc")
            if not os.path.exists(secret_file):
                return None

            with open(secret_file, "rb") as f:
                encrypted_data = f.read()

            # Decrypt secret data
            decrypted_data = self._decrypt_data(encrypted_data)
            secret_data = json.loads(decrypted_data)

            return secret_data["secret"]

        except Exception as e:
            frappe.log_error(f"Failed to retrieve secret {name}: {e}")
            return None

    def get_secret_metadata(self, name: str, key: str, default=None) -> Any:
        """Get specific metadata for a secret"""
        try:
            metadata_file = os.path.join(self.store_path, f"{name}.meta")
            if not os.path.exists(metadata_file):
                return default

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            return metadata.get(key, default)

        except Exception as e:
            frappe.log_error(f"Failed to get metadata for {name}: {e}")
            return default

    def update_secret_metadata(self, name: str, metadata: Dict[str, Any]):
        """Update metadata for a secret"""
        try:
            metadata_file = os.path.join(self.store_path, f"{name}.meta")

            # Load existing metadata
            existing_metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    existing_metadata = json.load(f)

            # Update with new metadata
            existing_metadata.update(metadata)
            existing_metadata["last_updated"] = now()

            # Save updated metadata
            with open(metadata_file, "w") as f:
                json.dump(existing_metadata, f, indent=2)

            os.chmod(metadata_file, 0o600)

        except Exception as e:
            frappe.log_error(f"Failed to update metadata for {name}: {e}")

    def get_all_secret_metadata(self, name: str) -> Dict[str, Any]:
        """Get all metadata for a secret"""
        try:
            metadata_file = os.path.join(self.store_path, f"{name}.meta")
            if not os.path.exists(metadata_file):
                return {}

            with open(metadata_file, "r") as f:
                return json.load(f)

        except Exception as e:
            frappe.log_error(f"Failed to get all metadata for {name}: {e}")
            return {}

    def get_secret_backups(self, name: str) -> List[Dict[str, Any]]:
        """Get list of secret backups"""
        backups = []
        try:
            for filename in os.listdir(self.store_path):
                if filename.startswith(f"{name}_backup_") and filename.endswith(".enc"):
                    backup_name = filename[:-4]  # Remove .enc extension
                    metadata = self.get_all_secret_metadata(backup_name)
                    backups.append(
                        {
                            "name": backup_name,
                            "timestamp": metadata.get("created"),
                            "file": filename,
                        }
                    )
        except Exception as e:
            frappe.log_error(f"Failed to get backups for {name}: {e}")

        return backups

    def delete_secret(self, name: str):
        """Delete a secret and its metadata"""
        try:
            secret_file = os.path.join(self.store_path, f"{name}.enc")
            metadata_file = os.path.join(self.store_path, f"{name}.meta")

            if os.path.exists(secret_file):
                os.remove(secret_file)
            if os.path.exists(metadata_file):
                os.remove(metadata_file)

        except Exception as e:
            frappe.log_error(f"Failed to delete secret {name}: {e}")

    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt data using site encryption key"""
        try:
            # Get site encryption key
            site_config = frappe.get_site_config()
            encryption_key = site_config.get("encryption_key")

            if not encryption_key:
                # Generate temporary key if none exists
                encryption_key = Fernet.generate_key().decode("utf-8")
                site_config["encryption_key"] = encryption_key
                frappe.get_site().update_site_config(site_config)

            # Encrypt data
            fernet = Fernet(encryption_key.encode())
            return fernet.encrypt(data.encode())

        except Exception as e:
            frappe.log_error(f"Failed to encrypt data: {e}")
            raise

    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data using site encryption key"""
        try:
            site_config = frappe.get_site_config()
            encryption_key = site_config.get("encryption_key")

            if not encryption_key:
                raise Exception("No encryption key found in site config")

            fernet = Fernet(encryption_key.encode())
            return fernet.decrypt(encrypted_data).decode()

        except Exception as e:
            frappe.log_error(f"Failed to decrypt data: {e}")
            raise


# Global instance
_rotation_manager = None


def get_rotation_manager() -> SecretRotationManager:
    """Get global rotation manager instance"""
    global _rotation_manager
    if _rotation_manager is None:
        _rotation_manager = SecretRotationManager()
    return _rotation_manager


# API endpoints
@frappe.whitelist()
def rotate_secrets(force: bool = False) -> Dict[str, Any]:
    """
    API endpoint to rotate secrets

    Args:
        force: Force rotation regardless of schedule

    Returns:
        Rotation results
    """
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Insufficient permissions for secret rotation"))

    manager = get_rotation_manager()
    return manager.rotate_all_secrets(force=force)


@frappe.whitelist()
def get_rotation_status() -> Dict[str, Any]:
    """Get current rotation status"""
    if not frappe.has_permission("System Settings", "read"):
        frappe.throw(_("Insufficient permissions to view rotation status"))

    manager = get_rotation_manager()
    return manager.get_rotation_status()


@frappe.whitelist()
def test_secret_rotation() -> Dict[str, Any]:
    """Test secret rotation in safe mode (for testing only)"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Insufficient permissions for secret rotation testing"))

    if frappe.conf.get("developer_mode"):
        # Safe test mode - only log what would be rotated
        manager = get_rotation_manager()
        secrets_due = manager._get_secrets_due_for_rotation(force=True)

        return {
            "test_mode": True,
            "secrets_that_would_be_rotated": [s["name"] for s in secrets_due],
            "message": "Test mode - no actual rotation performed",
        }
    else:
        frappe.throw(_("Secret rotation testing only available in developer mode"))
