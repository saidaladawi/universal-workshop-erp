"""
Session Management Enhancement
Universal Workshop ERP - User Management

Advanced session management features for controlling user sessions and mitigating
unauthorized access with timeout policies, concurrent session limits, and session
revocation capabilities.
"""

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import frappe
from frappe import _
from frappe.utils import now_datetime, format_datetime, cint, get_datetime, add_to_date
from frappe.model.document import Document
from frappe.core.doctype.user.user import User


@dataclass
class SessionPolicy:
    """Session policy configuration"""

    idle_timeout_minutes: int = 30  # 30 minutes idle timeout
    absolute_timeout_hours: int = 8  # 8 hours maximum session
    max_concurrent_sessions: int = 3  # Maximum concurrent sessions per user
    force_single_session: bool = False  # Force single session for high-security roles
    enable_device_tracking: bool = True  # Track device information
    enable_location_tracking: bool = False  # Track login location (optional)
    session_warning_minutes: int = 5  # Warning before timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionPolicy":
        """Create from dictionary"""
        return cls(**data)


class SessionManager:
    """
    Advanced Session Management System

    Provides comprehensive session control including:
    - Timeout policies (idle and absolute)
    - Concurrent session limits
    - Session revocation and monitoring
    - Device and location tracking
    - Integration with security dashboard
    """

    def __init__(self):
        self.default_policy = SessionPolicy()
        self.session_table = "tabSessions"
        self.custom_sessions_table = "tabWorkshop User Session"

        # Session monitoring settings
        self.cleanup_interval_hours = 24
        self.suspicious_activity_threshold = 5  # Multiple locations/devices

        # Create custom session tracking table if needed
        self._ensure_session_tracking_table()

    def _ensure_session_tracking_table(self):
        """Ensure custom session tracking table exists"""
        try:
            if not frappe.db.exists("DocType", "Workshop User Session"):
                self._create_session_tracking_doctype()
        except Exception as e:
            frappe.log_error(f"Error creating session tracking table: {e}")

    def _create_session_tracking_doctype(self):
        """Create custom DocType for enhanced session tracking"""
        session_doctype = frappe.new_doc("DocType")
        session_doctype.name = "Workshop User Session"
        session_doctype.module = "User Management"
        session_doctype.custom = 1
        session_doctype.is_submittable = 0
        session_doctype.track_changes = 1

        # Add fields for session tracking
        fields = [
            {
                "fieldname": "user_email",
                "fieldtype": "Link",
                "options": "User",
                "label": "User",
                "reqd": 1,
            },
            {
                "fieldname": "session_id",
                "fieldtype": "Data",
                "label": "Session ID",
                "unique": 1,
                "reqd": 1,
            },
            {"fieldname": "device_info", "fieldtype": "JSON", "label": "Device Information"},
            {"fieldname": "ip_address", "fieldtype": "Data", "label": "IP Address"},
            {"fieldname": "user_agent", "fieldtype": "Text", "label": "User Agent"},
            {"fieldname": "login_time", "fieldtype": "Datetime", "label": "Login Time", "reqd": 1},
            {"fieldname": "last_activity", "fieldtype": "Datetime", "label": "Last Activity"},
            {"fieldname": "expiry_time", "fieldtype": "Datetime", "label": "Expiry Time"},
            {"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": 1},
            {
                "fieldname": "revoked_by",
                "fieldtype": "Link",
                "options": "User",
                "label": "Revoked By",
            },
            {"fieldname": "revocation_reason", "fieldtype": "Text", "label": "Revocation Reason"},
            {"fieldname": "session_policy", "fieldtype": "JSON", "label": "Session Policy"},
        ]

        for field in fields:
            field["parent"] = "Workshop User Session"
            field["parenttype"] = "DocType"
            field["parentfield"] = "fields"
            session_doctype.append("fields", field)

        session_doctype.insert(ignore_permissions=True)
        frappe.db.commit()

    # =============================================================================
    # Session Policy Management
    # =============================================================================

    def get_session_policy(self, user_email: str) -> SessionPolicy:
        """
        Get session policy for user based on roles and settings

        Args:
            user_email: User email address

        Returns:
            SessionPolicy object with configured policies
        """
        try:
            user_doc = frappe.get_doc("User", user_email)

            # Get custom session settings from user
            custom_policy = getattr(user_doc, "session_policy", None)
            if custom_policy:
                try:
                    policy_data = json.loads(custom_policy)
                    return SessionPolicy.from_dict(policy_data)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Determine policy based on user roles
            user_roles = frappe.get_roles(user_email)

            # High-security roles get stricter policies
            high_security_roles = ["System Manager", "Workshop Manager", "Financial Manager"]
            if any(role in user_roles for role in high_security_roles):
                return SessionPolicy(
                    idle_timeout_minutes=15,
                    absolute_timeout_hours=4,
                    max_concurrent_sessions=2,
                    force_single_session=True,
                    enable_device_tracking=True,
                    session_warning_minutes=3,
                )

            # Regular workshop roles
            workshop_roles = ["Technician", "Service Advisor", "Parts Manager"]
            if any(role in user_roles for role in workshop_roles):
                return SessionPolicy(
                    idle_timeout_minutes=30,
                    absolute_timeout_hours=8,
                    max_concurrent_sessions=3,
                    force_single_session=False,
                    enable_device_tracking=True,
                    session_warning_minutes=5,
                )

            # Default policy for other users
            return self.default_policy

        except Exception as e:
            frappe.log_error(f"Error getting session policy for {user_email}: {e}")
            return self.default_policy

    def set_user_session_policy(self, user_email: str, policy: SessionPolicy) -> Dict[str, Any]:
        """
        Set custom session policy for specific user

        Args:
            user_email: User email address
            policy: SessionPolicy object

        Returns:
            Success status and message
        """
        try:
            user_doc = frappe.get_doc("User", user_email)

            # Store policy as JSON in custom field
            policy_json = json.dumps(policy.to_dict())
            user_doc.db_set("session_policy", policy_json)

            # Log the policy change
            self._log_session_event(
                user_email,
                "session_policy_updated",
                {"new_policy": policy.to_dict(), "updated_by": frappe.session.user},
            )

            return {"success": True, "message": _("Session policy updated successfully")}

        except Exception as e:
            error_msg = f"Error setting session policy: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg}

    # =============================================================================
    # Session Creation and Management
    # =============================================================================

    def create_session_record(
        self, user_email: str, session_id: str, request_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create session record with tracking information

        Args:
            user_email: User email address
            session_id: Session identifier
            request_info: Request information (IP, user agent, etc.)

        Returns:
            Success status and session info
        """
        try:
            policy = self.get_session_policy(user_email)

            # Check concurrent session limits before creating
            if not self._check_concurrent_session_limit(user_email, policy):
                return {
                    "success": False,
                    "error": _("Maximum concurrent sessions exceeded"),
                    "max_sessions": policy.max_concurrent_sessions,
                }

            # Calculate session expiry times
            now = now_datetime()
            idle_expiry = add_to_date(now, minutes=policy.idle_timeout_minutes)
            absolute_expiry = add_to_date(now, hours=policy.absolute_timeout_hours)
            expiry_time = min(idle_expiry, absolute_expiry)

            # Extract device and request information
            device_info = self._extract_device_info(request_info) if request_info else {}
            ip_address = request_info.get("REMOTE_ADDR", "") if request_info else ""
            user_agent = request_info.get("HTTP_USER_AGENT", "") if request_info else ""

            # Create session record
            session_doc = frappe.new_doc("Workshop User Session")
            session_doc.user_email = user_email
            session_doc.session_id = session_id
            session_doc.device_info = json.dumps(device_info)
            session_doc.ip_address = ip_address
            session_doc.user_agent = user_agent
            session_doc.login_time = now
            session_doc.last_activity = now
            session_doc.expiry_time = expiry_time
            session_doc.is_active = 1
            session_doc.session_policy = json.dumps(policy.to_dict())
            session_doc.insert(ignore_permissions=True)

            # Log session creation
            self._log_session_event(
                user_email,
                "session_created",
                {
                    "session_id": session_id,
                    "device_info": device_info,
                    "ip_address": ip_address,
                    "expiry_time": format_datetime(expiry_time),
                },
            )

            return {
                "success": True,
                "session_id": session_id,
                "expiry_time": format_datetime(expiry_time),
                "policy": policy.to_dict(),
            }

        except Exception as e:
            error_msg = f"Error creating session record: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg}

    def update_session_activity(self, session_id: str) -> Dict[str, Any]:
        """
        Update last activity time for session

        Args:
            session_id: Session identifier

        Returns:
            Success status and updated expiry time
        """
        try:
            session_doc = frappe.get_doc(
                "Workshop User Session", {"session_id": session_id, "is_active": 1}
            )

            policy_data = json.loads(session_doc.session_policy)
            policy = SessionPolicy.from_dict(policy_data)

            # Update last activity and calculate new idle expiry
            now = now_datetime()
            session_doc.last_activity = now

            # Calculate new expiry time (idle timeout from now)
            idle_expiry = add_to_date(now, minutes=policy.idle_timeout_minutes)

            # Don't extend beyond absolute timeout
            login_time = get_datetime(session_doc.login_time)
            absolute_expiry = add_to_date(login_time, hours=policy.absolute_timeout_hours)
            new_expiry = min(idle_expiry, absolute_expiry)

            session_doc.expiry_time = new_expiry
            session_doc.save(ignore_permissions=True)

            return {
                "success": True,
                "expiry_time": format_datetime(new_expiry),
                "session_valid": True,
            }

        except frappe.DoesNotExistError:
            return {
                "success": False,
                "error": _("Session not found or expired"),
                "session_valid": False,
            }
        except Exception as e:
            error_msg = f"Error updating session activity: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg, "session_valid": False}

    def _check_concurrent_session_limit(self, user_email: str, policy: SessionPolicy) -> bool:
        """Check if user can create new session based on concurrent limits"""
        try:
            # Count active sessions for user
            active_sessions = frappe.db.count(
                "Workshop User Session",
                {"user_email": user_email, "is_active": 1, "expiry_time": [">", now_datetime()]},
            )

            # For force single session, revoke all existing sessions
            if policy.force_single_session and active_sessions > 0:
                self._revoke_user_sessions(user_email, "force_single_session")
                return True

            # Check against concurrent session limit
            return active_sessions < policy.max_concurrent_sessions

        except Exception as e:
            frappe.log_error(f"Error checking concurrent session limit: {e}")
            return True  # Allow session creation on error

    # =============================================================================
    # Session Revocation and Cleanup
    # =============================================================================

    def revoke_session(
        self, session_id: str, reason: str = "", revoked_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revoke specific session

        Args:
            session_id: Session to revoke
            reason: Reason for revocation
            revoked_by: User who initiated revocation

        Returns:
            Success status and revocation details
        """
        try:
            session_doc = frappe.get_doc("Workshop User Session", {"session_id": session_id})

            # Mark session as inactive
            session_doc.is_active = 0
            session_doc.revoked_by = revoked_by or frappe.session.user
            session_doc.revocation_reason = reason
            session_doc.save(ignore_permissions=True)

            # Also remove from Frappe's session table
            frappe.db.delete("Sessions", {"sid": session_id})

            # Log revocation event
            self._log_session_event(
                session_doc.user_email,
                "session_revoked",
                {
                    "session_id": session_id,
                    "reason": reason,
                    "revoked_by": revoked_by or frappe.session.user,
                },
            )

            return {"success": True, "message": _("Session revoked successfully")}

        except Exception as e:
            error_msg = f"Error revoking session: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg}

    def revoke_user_sessions(
        self, user_email: str, reason: str = "", exclude_current: bool = True
    ) -> Dict[str, Any]:
        """
        Revoke all sessions for specific user

        Args:
            user_email: User whose sessions to revoke
            reason: Reason for revocation
            exclude_current: Whether to exclude current session

        Returns:
            Success status and count of revoked sessions
        """
        try:
            current_session = frappe.session.sid if exclude_current else None
            return self._revoke_user_sessions(user_email, reason, current_session)

        except Exception as e:
            error_msg = f"Error revoking user sessions: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg}

    def _revoke_user_sessions(
        self, user_email: str, reason: str = "", exclude_session: Optional[str] = None
    ) -> Dict[str, Any]:
        """Internal method to revoke user sessions"""
        try:
            # Get all active sessions for user
            filters = {"user_email": user_email, "is_active": 1}

            if exclude_session:
                filters["session_id"] = ["!=", exclude_session]

            sessions = frappe.get_all(
                "Workshop User Session", filters=filters, fields=["name", "session_id"]
            )

            revoked_count = 0
            for session in sessions:
                result = self.revoke_session(session.session_id, reason, frappe.session.user)
                if result.get("success"):
                    revoked_count += 1

            return {
                "success": True,
                "revoked_count": revoked_count,
                "message": _("Revoked {0} sessions").format(revoked_count),
            }

        except Exception as e:
            raise e

    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """
        Clean up expired sessions

        Returns:
            Cleanup statistics
        """
        try:
            now = now_datetime()

            # Find expired sessions
            expired_sessions = frappe.get_all(
                "Workshop User Session",
                filters={"is_active": 1, "expiry_time": ["<", now]},
                fields=["name", "session_id", "user_email"],
            )

            cleanup_count = 0
            for session in expired_sessions:
                try:
                    result = self.revoke_session(session.session_id, "session_expired")
                    if result.get("success"):
                        cleanup_count += 1
                except Exception as e:
                    frappe.log_error(f"Error cleaning up session {session.session_id}: {e}")
                    continue

            # Also clean up Frappe sessions table
            frappe.db.sql(
                """
                DELETE FROM `tabSessions` 
                WHERE lastupdate < %s
            """,
                [now],
            )

            return {
                "success": True,
                "cleaned_sessions": cleanup_count,
                "cleanup_time": format_datetime(now),
            }

        except Exception as e:
            error_msg = f"Error during session cleanup: {e}"
            frappe.log_error(error_msg)
            return {"success": False, "error": error_msg}

    # =============================================================================
    # Session Monitoring and Analytics
    # =============================================================================

    def get_user_sessions(self, user_email: str, include_inactive: bool = False) -> List[Dict]:
        """
        Get all sessions for specific user

        Args:
            user_email: User email address
            include_inactive: Include revoked/expired sessions

        Returns:
            List of session records
        """
        try:
            filters = {"user_email": user_email}
            if not include_inactive:
                filters["is_active"] = 1
                filters["expiry_time"] = [">", now_datetime()]

            sessions = frappe.get_all(
                "Workshop User Session",
                filters=filters,
                fields=[
                    "session_id",
                    "device_info",
                    "ip_address",
                    "login_time",
                    "last_activity",
                    "expiry_time",
                    "is_active",
                    "revoked_by",
                    "revocation_reason",
                ],
                order_by="login_time desc",
            )

            # Parse device info and format dates
            for session in sessions:
                try:
                    session["device_info"] = json.loads(session["device_info"] or "{}")
                except (json.JSONDecodeError, TypeError):
                    session["device_info"] = {}

                # Format datetime fields
                for field in ["login_time", "last_activity", "expiry_time"]:
                    if session.get(field):
                        session[field] = format_datetime(session[field])

            return sessions

        except Exception as e:
            frappe.log_error(f"Error getting user sessions: {e}")
            return []

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide session statistics

        Returns:
            Session analytics and statistics
        """
        try:
            now = now_datetime()

            # Active sessions count
            active_sessions = frappe.db.count(
                "Workshop User Session", {"is_active": 1, "expiry_time": [">", now]}
            )

            # Sessions by hour (last 24 hours)
            sessions_by_hour = frappe.db.sql(
                """
                SELECT 
                    HOUR(login_time) as hour,
                    COUNT(*) as session_count
                FROM `tabWorkshop User Session`
                WHERE login_time >= %s
                GROUP BY HOUR(login_time)
                ORDER BY hour
            """,
                [add_to_date(now, hours=-24)],
                as_dict=True,
            )

            # Concurrent sessions per user
            concurrent_sessions = frappe.db.sql(
                """
                SELECT 
                    user_email,
                    COUNT(*) as session_count
                FROM `tabWorkshop User Session`
                WHERE is_active = 1 AND expiry_time > %s
                GROUP BY user_email
                HAVING session_count > 1
                ORDER BY session_count DESC
            """,
                [now],
                as_dict=True,
            )

            # Suspicious activity (multiple IPs per user)
            suspicious_activity = frappe.db.sql(
                """
                SELECT 
                    user_email,
                    COUNT(DISTINCT ip_address) as ip_count,
                    GROUP_CONCAT(DISTINCT ip_address) as ip_addresses
                FROM `tabWorkshop User Session`
                WHERE login_time >= %s
                GROUP BY user_email
                HAVING ip_count > 2
                ORDER BY ip_count DESC
            """,
                [add_to_date(now, hours=-24)],
                as_dict=True,
            )

            return {
                "active_sessions": active_sessions,
                "sessions_by_hour": sessions_by_hour,
                "concurrent_sessions": concurrent_sessions,
                "suspicious_activity": suspicious_activity,
                "last_updated": format_datetime(now),
            }

        except Exception as e:
            frappe.log_error(f"Error getting session statistics: {e}")
            return {"error": str(e), "last_updated": format_datetime(now_datetime())}

    # =============================================================================
    # Device and Location Tracking
    # =============================================================================

    def _extract_device_info(self, request_info: Dict) -> Dict[str, Any]:
        """Extract device information from request"""
        try:
            user_agent = request_info.get("HTTP_USER_AGENT", "")

            # Basic device detection (can be enhanced with user-agents library)
            device_info = {
                "user_agent": user_agent,
                "is_mobile": "Mobile" in user_agent or "Android" in user_agent,
                "browser": self._detect_browser(user_agent),
                "os": self._detect_os(user_agent),
                "timestamp": format_datetime(now_datetime()),
            }

            return device_info

        except Exception as e:
            frappe.log_error(f"Error extracting device info: {e}")
            return {}

    def _detect_browser(self, user_agent: str) -> str:
        """Simple browser detection"""
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent:
            return "Safari"
        elif "Edge" in user_agent:
            return "Edge"
        else:
            return "Unknown"

    def _detect_os(self, user_agent: str) -> str:
        """Simple OS detection"""
        if "Windows" in user_agent:
            return "Windows"
        elif "Mac" in user_agent:
            return "macOS"
        elif "Linux" in user_agent:
            return "Linux"
        elif "Android" in user_agent:
            return "Android"
        elif "iOS" in user_agent:
            return "iOS"
        else:
            return "Unknown"

    # =============================================================================
    # Utility and Helper Methods
    # =============================================================================

    def _log_session_event(self, user_email: str, event_type: str, details: Dict):
        """Log session-related events for audit trail"""
        try:
            from universal_workshop.user_management.security_dashboard import SecurityDashboard

            security_dashboard = SecurityDashboard()
            security_dashboard.log_security_event(
                event_type=event_type,
                user_email=user_email,
                details=details,
                severity=(
                    "info" if event_type in ["session_created", "session_activity"] else "warning"
                ),
            )

        except Exception as e:
            frappe.log_error(f"Error logging session event: {e}")

    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Validate if session is still active and within policy limits

        Args:
            session_id: Session to validate

        Returns:
            Validation result with session status
        """
        try:
            session_doc = frappe.get_doc("Workshop User Session", {"session_id": session_id})

            now = now_datetime()
            expiry_time = get_datetime(session_doc.expiry_time)

            # Check if session is active and not expired
            if not session_doc.is_active:
                return {
                    "valid": False,
                    "reason": "session_revoked",
                    "message": _("Session has been revoked"),
                }

            if expiry_time <= now:
                # Auto-revoke expired session
                self.revoke_session(session_id, "session_expired")
                return {
                    "valid": False,
                    "reason": "session_expired",
                    "message": _("Session has expired"),
                }

            # Update activity time
            self.update_session_activity(session_id)

            return {
                "valid": True,
                "user_email": session_doc.user_email,
                "expiry_time": format_datetime(expiry_time),
                "last_activity": format_datetime(session_doc.last_activity),
            }

        except frappe.DoesNotExistError:
            return {
                "valid": False,
                "reason": "session_not_found",
                "message": _("Session not found"),
            }
        except Exception as e:
            frappe.log_error(f"Error validating session: {e}")
            return {"valid": False, "reason": "validation_error", "message": str(e)}


# =============================================================================
# WhiteListed API Methods
# =============================================================================


@frappe.whitelist()
def get_session_status():
    """Get current user's session status and policy"""
    session_manager = SessionManager()

    current_session = frappe.session.sid
    user_email = frappe.session.user

    # Validate current session
    validation = session_manager.validate_session(current_session)

    if validation.get("valid"):
        # Get user's session policy
        policy = session_manager.get_session_policy(user_email)

        # Get user's active sessions
        sessions = session_manager.get_user_sessions(user_email)

        return {
            "success": True,
            "session_valid": True,
            "expiry_time": validation.get("expiry_time"),
            "policy": policy.to_dict(),
            "active_sessions": len(sessions),
            "sessions": sessions,
        }
    else:
        return {
            "success": False,
            "session_valid": False,
            "reason": validation.get("reason"),
            "message": validation.get("message"),
        }


@frappe.whitelist()
def revoke_session(session_id, reason="Manual revocation"):
    """Revoke specific session (admin only)"""
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("Insufficient permissions"))

    session_manager = SessionManager()
    return session_manager.revoke_session(session_id, reason)


@frappe.whitelist()
def revoke_user_sessions(user_email, reason="Administrative action"):
    """Revoke all sessions for user (admin only)"""
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("Insufficient permissions"))

    session_manager = SessionManager()
    return session_manager.revoke_user_sessions(user_email, reason)


@frappe.whitelist()
def get_session_statistics():
    """Get session statistics (admin only)"""
    if not frappe.has_permission("User", "read"):
        frappe.throw(_("Insufficient permissions"))

    session_manager = SessionManager()
    return session_manager.get_session_statistics()


@frappe.whitelist()
def cleanup_expired_sessions():
    """Clean up expired sessions (system manager only)"""
    if not frappe.user.has_role("System Manager"):
        frappe.throw(_("Only System Managers can cleanup sessions"))

    session_manager = SessionManager()
    return session_manager.cleanup_expired_sessions()


@frappe.whitelist()
def update_session_policy(user_email, policy_data):
    """Update session policy for user (admin only)"""
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("Insufficient permissions"))

    try:
        policy = SessionPolicy.from_dict(policy_data)
        session_manager = SessionManager()
        return session_manager.set_user_session_policy(user_email, policy)
    except Exception as e:
        return {"success": False, "error": str(e)}
