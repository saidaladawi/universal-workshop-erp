"""
Comprehensive Offline Validation and Audit Logging Manager
Integrates offline grace period management, session tracking, and audit logging
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from ..offline_manager import OfflineGracePeriodManager
from ..doctype.license_audit_log.license_audit_log import LicenseAuditLog


class OfflineValidationManager:
    """
    Comprehensive offline validation manager that coordinates:
    - Grace period management
    - Offline session tracking
    - Security validation
    - Audit logging
    """

    def __init__(self, workshop_code: str):
        self.workshop_code = workshop_code
        self.grace_manager = OfflineGracePeriodManager()
        self.current_session = None
        self.security_threshold = 3  # Max failed validation attempts

    def start_offline_session(
        self, reason: str = "Connection lost", duration_hours: int = 24
    ) -> str:
        """
        Start a new offline validation session with comprehensive tracking

        Args:
            reason: Reason for starting offline session
            duration_hours: Duration of grace period in hours

        Returns:
            str: Session ID for tracking
        """
        try:
            # Check if there's already an active session
            existing_session = self._get_active_session()
            if existing_session:
                self._log_audit_event(
                    "offline_session_duplicate_start",
                    "medium",
                    f"Attempted to start offline session when one already exists: {existing_session.name}",
                    {"existing_session": existing_session.name, "reason": reason},
                )
                return existing_session.name

            # Create new offline session
            session = frappe.new_doc("Offline Session")
            session.workshop_code = self.workshop_code
            session.started_at = now_datetime()
            session.expires_at = add_to_date(session.started_at, hours=duration_hours)
            session.status = "active"

            # Generate security hash and hardware fingerprint
            session.secure_hash = self._generate_session_security_hash()
            session.hardware_fingerprint_partial = self._get_partial_hardware_fingerprint()

            # Initialize session data
            session_data = {
                "workshop_code": self.workshop_code,
                "start_reason": reason,
                "security_checks": [],
                "validation_attempts": [],
                "secure_hash": session.secure_hash,
            }
            session.session_data = json.dumps(session_data)

            session.insert(ignore_permissions=True)
            frappe.db.commit()

            # Start grace period monitoring
            self.grace_manager.enter_grace_period(reason)
            self.grace_manager.start_monitoring()

            # Log session start
            self._log_audit_event(
                "offline_session_started",
                "medium",
                f"Offline session started for workshop {self.workshop_code}",
                {
                    "session_id": session.name,
                    "duration_hours": duration_hours,
                    "reason": reason,
                    "expires_at": session.expires_at.isoformat(),
                },
            )

            self.current_session = session
            return session.name

        except Exception as e:
            self._log_audit_event(
                "offline_session_start_failed",
                "high",
                f"Failed to start offline session: {str(e)}",
                {"error": str(e), "reason": reason},
            )
            frappe.log_error(f"Failed to start offline session: {e}", "Offline Validation Manager")
            raise

    def validate_offline_session(self, session_id: str = None) -> Dict[str, Any]:
        """
        Validate current offline session with comprehensive security checks

        Args:
            session_id: Optional specific session ID to validate

        Returns:
            Dict containing validation results and session status
        """
        try:
            # Get session to validate
            if session_id:
                session = frappe.get_doc("Offline Session", session_id)
            else:
                session = self._get_active_session()

            if not session:
                return {
                    "valid": False,
                    "reason": "No active offline session found",
                    "status": "no_session",
                }

            # Perform comprehensive validation
            validation_results = {
                "session_id": session.name,
                "workshop_code": session.workshop_code,
                "validation_timestamp": now_datetime().isoformat(),
                "checks_performed": [],
            }

            # 1. Check session expiration
            if session.is_expired():
                validation_results["valid"] = False
                validation_results["reason"] = "Session expired"
                validation_results["status"] = "expired"

                self._log_audit_event(
                    "offline_session_expired",
                    "high",
                    f"Offline session {session.name} has expired",
                    validation_results,
                )

                # Mark session as expired
                session.status = "expired"
                session.ended_at = now_datetime()
                session.save(ignore_permissions=True)

                return validation_results

            validation_results["checks_performed"].append("expiration_check_passed")

            # 2. Validate hardware fingerprint consistency
            current_fingerprint = self._get_current_hardware_fingerprint()
            if not session.verify_hardware_fingerprint(current_fingerprint):
                validation_results["valid"] = False
                validation_results["reason"] = "Hardware fingerprint mismatch"
                validation_results["status"] = "hardware_mismatch"

                self._log_audit_event(
                    "security_hardware_mismatch",
                    "critical",
                    f"Hardware fingerprint mismatch in offline session {session.name}",
                    {
                        "session_id": session.name,
                        "expected_partial": session.hardware_fingerprint_partial,
                        "current_partial": (
                            current_fingerprint[:32] if current_fingerprint else None
                        ),
                    },
                )

                return validation_results

            validation_results["checks_performed"].append("hardware_fingerprint_verified")

            # 3. Validate session security hash
            if not self._validate_session_security(session):
                validation_results["valid"] = False
                validation_results["reason"] = "Session security validation failed"
                validation_results["status"] = "security_failed"

                self._log_audit_event(
                    "security_invalid_signature",
                    "critical",
                    f"Session security validation failed for {session.name}",
                    {"session_id": session.name},
                )

                return validation_results

            validation_results["checks_performed"].append("security_hash_verified")

            # 4. Update session activity
            session.update_activity()

            # 5. Check grace period status
            grace_remaining = self.grace_manager.get_grace_period_remaining()
            validation_results["grace_period_remaining_hours"] = grace_remaining

            # All validations passed
            validation_results["valid"] = True
            validation_results["status"] = "active"
            validation_results["remaining_time"] = session.get_remaining_time()

            # Log successful validation
            self._log_audit_event(
                "offline_session_validated",
                "low",
                f"Offline session {session.name} validated successfully",
                validation_results,
            )

            return validation_results

        except Exception as e:
            error_result = {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "status": "validation_error",
            }

            self._log_audit_event(
                "offline_validation_error",
                "high",
                f"Error during offline validation: {str(e)}",
                {"error": str(e), "session_id": session_id},
            )

            frappe.log_error(f"Offline validation error: {e}", "Offline Validation Manager")
            return error_result

    def end_offline_session(self, session_id: str = None, success: bool = True) -> bool:
        """
        End offline session with comprehensive cleanup and logging

        Args:
            session_id: Optional specific session ID to end
            success: Whether session ended successfully or due to failure

        Returns:
            bool: True if session ended successfully
        """
        try:
            # Get session to end
            if session_id:
                session = frappe.get_doc("Offline Session", session_id)
            else:
                session = self._get_active_session()

            if not session:
                return False

            # Calculate session metrics
            session_summary = session.get_session_summary()

            # Update session status
            session.status = "completed" if success else "cancelled"
            session.ended_at = now_datetime()
            session.online_validation_success = success

            # Calculate total offline hours
            if session.started_at:
                offline_duration = now_datetime() - get_datetime(session.started_at)
                session.total_offline_hours = offline_duration.total_seconds() / 3600

            session.save(ignore_permissions=True)

            # Stop grace period monitoring
            self.grace_manager.exit_grace_period(success)
            self.grace_manager.stop_monitoring()

            # Log session completion
            self._log_audit_event(
                "offline_session_ended",
                "medium" if success else "high",
                f"Offline session {session.name} ended {'successfully' if success else 'due to failure'}",
                {
                    "session_id": session.name,
                    "success": success,
                    "duration_hours": session.total_offline_hours,
                    "activity_count": session.activity_count,
                    "session_summary": session_summary,
                },
            )

            frappe.db.commit()
            return True

        except Exception as e:
            self._log_audit_event(
                "offline_session_end_failed",
                "high",
                f"Failed to end offline session: {str(e)}",
                {"error": str(e), "session_id": session_id},
            )
            frappe.log_error(f"Failed to end offline session: {e}", "Offline Validation Manager")
            return False

    def get_offline_status(self) -> Dict[str, Any]:
        """
        Get comprehensive offline validation status

        Returns:
            Dict containing complete offline status information
        """
        try:
            status = {"timestamp": now_datetime().isoformat(), "workshop_code": self.workshop_code}

            # Get active session info
            active_session = self._get_active_session()
            if active_session:
                status["active_session"] = active_session.get_session_summary()
                status["has_active_session"] = True
            else:
                status["has_active_session"] = False
                status["active_session"] = None

            # Get grace period status
            status["grace_period"] = {
                "active": self.grace_manager.is_grace_period_active(),
                "remaining_hours": self.grace_manager.get_grace_period_remaining(),
            }

            # Get recent audit events
            recent_events = frappe.get_all(
                "License Audit Log",
                filters={
                    "workshop_id": self.workshop_code,
                    "timestamp": [">=", add_to_date(now_datetime(), hours=-24)],
                },
                fields=["event_type", "severity", "timestamp", "description"],
                order_by="timestamp desc",
                limit=10,
            )
            status["recent_audit_events"] = recent_events

            return status

        except Exception as e:
            frappe.log_error(f"Failed to get offline status: {e}", "Offline Validation Manager")
            return {
                "error": str(e),
                "timestamp": now_datetime().isoformat(),
                "workshop_code": self.workshop_code,
            }

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired offline sessions and related data

        Returns:
            int: Number of sessions cleaned up
        """
        try:
            # Get expired sessions
            expired_sessions = frappe.get_all(
                "Offline Session",
                filters={
                    "status": ["in", ["active", "expired"]],
                    "expires_at": ["<", now_datetime()],
                },
                fields=["name", "workshop_code", "expires_at"],
            )

            cleanup_count = 0
            for session_data in expired_sessions:
                try:
                    session = frappe.get_doc("Offline Session", session_data.name)

                    # Mark as expired if still active
                    if session.status == "active":
                        session.status = "expired"
                        session.ended_at = now_datetime()
                        session.save(ignore_permissions=True)

                    # Log cleanup
                    self._log_audit_event(
                        "offline_session_cleanup",
                        "low",
                        f"Cleaned up expired offline session {session.name}",
                        {
                            "session_id": session.name,
                            "workshop_code": session.workshop_code,
                            "expired_at": session_data.expires_at.isoformat(),
                        },
                    )

                    cleanup_count += 1

                except Exception as e:
                    frappe.log_error(f"Failed to cleanup session {session_data.name}: {e}")

            if cleanup_count > 0:
                frappe.db.commit()

            return cleanup_count

        except Exception as e:
            frappe.log_error(
                f"Failed to cleanup expired sessions: {e}", "Offline Validation Manager"
            )
            return 0

    # Private helper methods

    def _get_active_session(self):
        """Get active offline session for current workshop"""
        try:
            filters = {"workshop_code": self.workshop_code, "status": "active"}
            if frappe.db.exists("Offline Session", filters):
                return frappe.get_doc("Offline Session", filters)
            return None
        except Exception:
            return None

    def _generate_session_security_hash(self) -> str:
        """Generate security hash for session validation"""
        try:
            # Use workshop code, timestamp, and hardware fingerprint for hash
            hash_data = f"{self.workshop_code}:{now_datetime().isoformat()}:{self._get_current_hardware_fingerprint()}"
            return hashlib.sha256(hash_data.encode()).hexdigest()
        except Exception:
            # Fallback hash
            return hashlib.sha256(
                f"{self.workshop_code}:{now_datetime().isoformat()}".encode()
            ).hexdigest()

    def _get_partial_hardware_fingerprint(self) -> str:
        """Get partial hardware fingerprint for session tracking"""
        try:
            full_fingerprint = self._get_current_hardware_fingerprint()
            return full_fingerprint[:32] if full_fingerprint else ""
        except Exception:
            return ""

    def _get_current_hardware_fingerprint(self) -> str:
        """Get current hardware fingerprint"""
        try:
            from ..hardware_fingerprint import HardwareFingerprintGenerator

            generator = HardwareFingerprintGenerator()
            return generator.get_primary_fingerprint()
        except Exception as e:
            frappe.log_error(f"Failed to get hardware fingerprint: {e}")
            return ""

    def _validate_session_security(self, session) -> bool:
        """Validate session security integrity"""
        try:
            if not session.secure_hash or not session.session_data:
                return False

            # Parse session data
            session_data = json.loads(session.session_data)
            stored_hash = session_data.get("secure_hash")

            # Verify hash matches
            return stored_hash == session.secure_hash

        except Exception:
            return False

    def _log_audit_event(
        self, event_type: str, severity: str, description: str, event_data: Dict = None
    ):
        """Log audit event for offline validation activities"""
        try:
            LicenseAuditLog.log_event(
                event_type=event_type,
                event_data=event_data,
                workshop_id=self.workshop_code,
                severity=severity,
                description=description,
            )
        except Exception as e:
            frappe.log_error(f"Failed to log audit event: {e}", "Offline Validation Manager")


# Utility functions for external use


@frappe.whitelist()
def start_offline_validation(
    workshop_code: str, reason: str = "Manual offline mode", duration_hours: int = 24
) -> str:
    """
    Start offline validation session for a workshop

    Args:
        workshop_code: Workshop identifier
        reason: Reason for starting offline mode
        duration_hours: Duration of offline grace period

    Returns:
        str: Session ID
    """
    manager = OfflineValidationManager(workshop_code)
    return manager.start_offline_session(reason, duration_hours)


@frappe.whitelist()
def validate_offline_access(workshop_code: str, session_id: str = None) -> Dict[str, Any]:
    """
    Validate offline access for a workshop

    Args:
        workshop_code: Workshop identifier
        session_id: Optional session ID to validate

    Returns:
        Dict: Validation results
    """
    manager = OfflineValidationManager(workshop_code)
    return manager.validate_offline_session(session_id)


@frappe.whitelist()
def get_offline_validation_status(workshop_code: str) -> Dict[str, Any]:
    """
    Get comprehensive offline validation status

    Args:
        workshop_code: Workshop identifier

    Returns:
        Dict: Complete offline status
    """
    manager = OfflineValidationManager(workshop_code)
    return manager.get_offline_status()


@frappe.whitelist()
def end_offline_validation(
    workshop_code: str, session_id: str = None, success: bool = True
) -> bool:
    """
    End offline validation session

    Args:
        workshop_code: Workshop identifier
        session_id: Optional session ID to end
        success: Whether session ended successfully

    Returns:
        bool: True if ended successfully
    """
    manager = OfflineValidationManager(workshop_code)
    return manager.end_offline_session(session_id, success)


def scheduled_offline_cleanup():
    """Scheduled job to clean up expired offline sessions"""
    try:
        # Get all unique workshop codes with offline sessions
        workshop_codes = frappe.db.sql(
            """
            SELECT DISTINCT workshop_code 
            FROM `tabOffline Session` 
            WHERE status IN ('active', 'expired')
        """,
            as_list=True,
        )

        total_cleaned = 0
        for workshop_code_tuple in workshop_codes:
            workshop_code = workshop_code_tuple[0]
            manager = OfflineValidationManager(workshop_code)
            cleaned = manager.cleanup_expired_sessions()
            total_cleaned += cleaned

        frappe.logger().info(
            f"Offline session cleanup completed: {total_cleaned} sessions processed"
        )
        return total_cleaned

    except Exception as e:
        frappe.log_error(f"Scheduled offline cleanup failed: {e}", "Offline Validation Manager")
        return 0
