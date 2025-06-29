"""
Universal Workshop ERP - Enhanced Session Management System
Provides secure session handling with Arabic interface support, device binding, and audit trails.
"""

import json
import hashlib
import datetime
from typing import Dict, List, Optional, Any

import frappe
from frappe import _
from frappe.utils import now, add_to_date, get_datetime, cint, flt
from frappe.sessions import Session, delete_session, get_expiry_in_seconds
from frappe.core.doctype.activity_log.activity_log import add_authentication_log


class SessionInfo:
    """Session information structure"""

    def __init__(
        self,
        sid,
        user,
        device_fingerprint,
        ip_address,
        user_agent,
        location,
        created_at,
        last_activity,
        status,
        security_level,
        language="en",
    ):
        self.sid = sid
        self.user = user
        self.device_fingerprint = device_fingerprint
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.location = location
        self.created_at = created_at
        self.last_activity = last_activity
        self.status = status
        self.security_level = security_level
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sid": self.sid,
            "user": self.user,
            "device_fingerprint": self.device_fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "location": self.location,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "status": self.status,
            "security_level": self.security_level,
            "language": self.language,
        }


class UniversalWorkshopSessionManager:
    """Enhanced session management for Universal Workshop ERP"""

    def __init__(self):
        self.session_timeout_minutes = self._get_session_timeout()
        self.max_concurrent_sessions = self._get_max_concurrent_sessions()
        self.device_binding_enabled = self._get_device_binding_setting()

    def _get_session_timeout(self) -> int:
        """Get session timeout from system settings"""
        timeout = frappe.db.get_single_value("System Settings", "session_expiry") or "240:00:00"
        # Convert HH:MM:SS to minutes
        parts = timeout.split(":")
        return (int(parts[0]) * 60) + int(parts[1])

    def _get_max_concurrent_sessions(self) -> int:
        """Get maximum concurrent sessions allowed"""
        try:
            return cint(
                frappe.db.get_single_value("Workshop Settings", "max_concurrent_sessions") or 3
            )
        except Exception:
            return 3  # Default fallback

    def _get_device_binding_setting(self) -> bool:
        """Check if device binding is enabled"""
        try:
            return cint(
                frappe.db.get_single_value("Workshop Settings", "enable_device_binding") or 1
            )
        except Exception:
            return True  # Default to enabled

    def generate_device_fingerprint(self, request_data: Dict[str, str]) -> str:
        """Generate device fingerprint from request data"""
        fingerprint_data = {
            "user_agent": request_data.get("user_agent", ""),
            "accept_language": request_data.get("accept_language", ""),
            "screen_resolution": request_data.get("screen_resolution", ""),
            "timezone": request_data.get("timezone", ""),
            "platform": request_data.get("platform", ""),
        }

        # Create hash from fingerprint data
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]

    def create_enhanced_session(self, user: str, request_data: Dict[str, str]) -> SessionInfo:
        """Create enhanced session with security features"""

        # Generate device fingerprint
        device_fingerprint = self.generate_device_fingerprint(request_data)

        # Check concurrent sessions limit
        self._enforce_concurrent_sessions_limit(user)

        # Create session info
        session_info = SessionInfo(
            sid=frappe.generate_hash(),
            user=user,
            device_fingerprint=device_fingerprint,
            ip_address=frappe.local.request_ip or "",
            user_agent=request_data.get("user_agent", ""),
            location=self._get_location_from_ip(frappe.local.request_ip),
            created_at=now(),
            last_activity=now(),
            status="Active",
            security_level=self._determine_security_level(user),
            language=frappe.local.lang or "en",
        )

        # Store enhanced session data
        self._store_session_data(session_info)

        # Log authentication event
        self._log_authentication_event(
            user,
            "login",
            {
                "device_fingerprint": device_fingerprint,
                "ip_address": frappe.local.request_ip,
                "location": session_info.location,
            },
        )

        return session_info

    def validate_session_security(self, sid: str, current_request_data: Dict[str, str]) -> bool:
        """Validate session security including device binding"""

        session_data = self._get_session_data(sid)
        if not session_data:
            return False

        # Check session expiry
        if self._is_session_expired(session_data):
            self.revoke_session(sid, "Session expired")
            return False

        # Device binding validation
        if self.device_binding_enabled:
            current_fingerprint = self.generate_device_fingerprint(current_request_data)
            if current_fingerprint != session_data.get("device_fingerprint"):
                self.revoke_session(sid, "Device fingerprint mismatch")
                self._log_security_event(
                    session_data.get("user"),
                    "device_mismatch",
                    {
                        "expected_fingerprint": session_data.get("device_fingerprint"),
                        "actual_fingerprint": current_fingerprint,
                    },
                )
                return False

        # IP address validation (optional strict mode)
        if frappe.db.get_single_value("Workshop Settings", "strict_ip_validation"):
            if frappe.local.request_ip != session_data.get("ip_address"):
                self._log_security_event(
                    session_data.get("user"),
                    "ip_mismatch",
                    {
                        "expected_ip": session_data.get("ip_address"),
                        "actual_ip": frappe.local.request_ip,
                    },
                )

        # Update last activity
        self._update_session_activity(sid)

        return True

    def revoke_session(self, sid: str, reason: str = "Manual revocation") -> bool:
        """Revoke a specific session"""

        session_data = self._get_session_data(sid)
        if not session_data:
            return False

        # Delete from ERPNext sessions
        delete_session(sid, reason=reason)

        # Remove from enhanced session store
        frappe.cache.hdel("workshop_session", sid)

        # Log revocation event
        self._log_authentication_event(
            session_data.get("user"), "logout", {"reason": reason, "sid": sid}
        )

        return True

    def revoke_all_user_sessions(self, user: str, except_current: bool = True) -> int:
        """Revoke all sessions for a user"""

        user_sessions = self.get_user_sessions(user)
        revoked_count = 0

        current_sid = frappe.session.sid if except_current else None

        for session in user_sessions:
            if session["sid"] != current_sid:
                if self.revoke_session(session["sid"], "Admin revocation"):
                    revoked_count += 1

        return revoked_count

    def get_user_sessions(self, user: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""

        # Get sessions from ERPNext
        sessions = frappe.db.sql(
            """
            SELECT sid, lastupdate, sessiondata
            FROM tabSessions
            WHERE user = %s
            AND lastupdate > %s
            ORDER BY lastupdate DESC
        """,
            [user, self._get_expiry_threshold()],
            as_dict=True,
        )

        enhanced_sessions = []
        for session in sessions:
            enhanced_data = self._get_session_data(session.sid)
            if enhanced_data:
                enhanced_sessions.append(
                    {
                        "sid": session.sid,
                        "last_activity": session.lastupdate,
                        "device_fingerprint": enhanced_data.get("device_fingerprint", ""),
                        "ip_address": enhanced_data.get("ip_address", ""),
                        "location": enhanced_data.get("location", ""),
                        "user_agent": enhanced_data.get("user_agent", ""),
                        "security_level": enhanced_data.get("security_level", "standard"),
                        "language": enhanced_data.get("language", "en"),
                    }
                )

        return enhanced_sessions

    def get_session_analytics(self, user: str = None) -> Dict[str, Any]:
        """Get session analytics and statistics"""

        analytics = {
            "total_active_sessions": 0,
            "sessions_by_user": {},
            "sessions_by_location": {},
            "sessions_by_device": {},
            "security_events_last_24h": 0,
            "expired_sessions_cleaned": 0,
        }

        # Get active sessions
        where_clause = "WHERE lastupdate > %s"
        params = [self._get_expiry_threshold()]

        if user:
            where_clause += " AND user = %s"
            params.append(user)

        sessions = frappe.db.sql(
            f"""
            SELECT user, sid, lastupdate
            FROM tabSessions
            {where_clause}
        """,
            params,
            as_dict=True,
        )

        analytics["total_active_sessions"] = len(sessions)

        # Analyze sessions
        for session in sessions:
            # Count by user
            if session.user not in analytics["sessions_by_user"]:
                analytics["sessions_by_user"][session.user] = 0
            analytics["sessions_by_user"][session.user] += 1

            # Get enhanced data
            enhanced_data = self._get_session_data(session.sid)
            if enhanced_data:
                location = enhanced_data.get("location", "Unknown")
                device = enhanced_data.get("device_fingerprint", "Unknown")[:8]

                if location not in analytics["sessions_by_location"]:
                    analytics["sessions_by_location"][location] = 0
                analytics["sessions_by_location"][location] += 1

                if device not in analytics["sessions_by_device"]:
                    analytics["sessions_by_device"][device] = 0
                analytics["sessions_by_device"][device] += 1

        # Get security events count
        yesterday = add_to_date(now(), days=-1)
        security_events = frappe.db.count(
            "Activity Log", {"reference_doctype": "Session Security", "creation": [">=", yesterday]}
        )
        analytics["security_events_last_24h"] = security_events

        return analytics

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count"""

        expired_sessions = frappe.db.sql(
            """
            SELECT sid FROM tabSessions
            WHERE lastupdate < %s
        """,
            [self._get_expiry_threshold()],
            pluck=True,
        )

        cleaned_count = 0
        for sid in expired_sessions:
            if self.revoke_session(sid, "Session expired - cleanup"):
                cleaned_count += 1

        return cleaned_count

    def _enforce_concurrent_sessions_limit(self, user: str) -> None:
        """Enforce maximum concurrent sessions limit"""

        user_sessions = self.get_user_sessions(user)

        if len(user_sessions) >= self.max_concurrent_sessions:
            # Remove oldest sessions
            sessions_to_remove = len(user_sessions) - self.max_concurrent_sessions + 1
            oldest_sessions = sorted(user_sessions, key=lambda x: x["last_activity"])[
                :sessions_to_remove
            ]

            for session in oldest_sessions:
                self.revoke_session(session["sid"], "Concurrent session limit exceeded")

    def _store_session_data(self, session_info: SessionInfo) -> None:
        """Store enhanced session data in cache"""
        frappe.cache.hset("workshop_session", session_info.sid, session_info.to_dict())
        frappe.cache.expire("workshop_session", 3600 * 24)  # 24 hours

    def _get_session_data(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get enhanced session data from cache"""
        return frappe.cache.hget("workshop_session", sid)

    def _update_session_activity(self, sid: str) -> None:
        """Update session last activity timestamp"""
        session_data = self._get_session_data(sid)
        if session_data:
            session_data["last_activity"] = now()
            frappe.cache.hset("workshop_session", sid, session_data)

    def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """Check if session is expired"""
        last_activity = get_datetime(session_data.get("last_activity"))
        expiry_time = add_to_date(last_activity, minutes=self.session_timeout_minutes)
        return get_datetime(now()) > expiry_time

    def _get_expiry_threshold(self) -> str:
        """Get expiry threshold for database queries"""
        return add_to_date(now(), minutes=-self.session_timeout_minutes, as_string=True)

    def _determine_security_level(self, user: str) -> str:
        """Determine security level based on user roles"""
        user_roles = frappe.get_roles(user)

        if "System Manager" in user_roles or "Workshop Manager" in user_roles:
            return "high"
        elif "Workshop Technician" in user_roles:
            return "medium"
        else:
            return "standard"

    def _get_location_from_ip(self, ip_address: str) -> str:
        """Get approximate location from IP address"""
        # This is a placeholder - in production, integrate with IP geolocation service
        if not ip_address or ip_address.startswith("127.") or ip_address.startswith("192.168."):
            return "Local Network"
        return "External"

    def _log_authentication_event(
        self, user: str, event_type: str, details: Dict[str, Any]
    ) -> None:
        """Log authentication events for audit trail"""
        add_authentication_log(
            subject=f"Session {event_type}",
            user=user,
            operation=event_type,
            status="Success",
            details=json.dumps(details),
        )

    def _log_security_event(self, user: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log security events"""
        frappe.get_doc(
            {
                "doctype": "Activity Log",
                "subject": f"Security Event: {event_type}",
                "user": user,
                "reference_doctype": "Session Security",
                "operation": event_type,
                "status": "Warning",
                "details": json.dumps(details),
            }
        ).insert(ignore_permissions=True)


# API Methods for session management


@frappe.whitelist()
def get_current_session_info():
    """Get current session information"""
    session_manager = UniversalWorkshopSessionManager()

    if not frappe.session.sid or frappe.session.user == "Guest":
        return {"error": "No active session"}

    session_data = session_manager._get_session_data(frappe.session.sid)
    if not session_data:
        return {"error": "Session data not found"}

    return {
        "sid": frappe.session.sid,
        "user": frappe.session.user,
        "device_fingerprint": session_data.get("device_fingerprint", "")[:8] + "...",
        "location": session_data.get("location", "Unknown"),
        "created_at": session_data.get("created_at"),
        "last_activity": session_data.get("last_activity"),
        "security_level": session_data.get("security_level", "standard"),
        "language": session_data.get("language", "en"),
    }


@frappe.whitelist()
def get_user_sessions():
    """Get all sessions for current user"""
    session_manager = UniversalWorkshopSessionManager()
    return session_manager.get_user_sessions(frappe.session.user)


@frappe.whitelist()
def revoke_session(sid):
    """Revoke a specific session"""
    session_manager = UniversalWorkshopSessionManager()

    # Only allow users to revoke their own sessions, or admins to revoke any
    session_data = session_manager._get_session_data(sid)
    if not session_data:
        frappe.throw(_("Session not found"))

    if session_data.get("user") != frappe.session.user and not frappe.has_permission(
        "User", "write"
    ):
        frappe.throw(_("Not permitted to revoke this session"))

    success = session_manager.revoke_session(sid, "Manual revocation by user")
    return {"success": success}


@frappe.whitelist()
def revoke_all_sessions():
    """Revoke all sessions for current user except current"""
    session_manager = UniversalWorkshopSessionManager()
    count = session_manager.revoke_all_user_sessions(frappe.session.user, except_current=True)
    return {"revoked_count": count}


@frappe.whitelist()
def get_session_analytics():
    """Get session analytics (admin only)"""
    if not frappe.has_permission("User", "read"):
        frappe.throw(_("Not permitted"))

    session_manager = UniversalWorkshopSessionManager()
    return session_manager.get_session_analytics()


# Scheduled job for session cleanup
def cleanup_expired_sessions():
    """Scheduled job to clean up expired sessions"""
    session_manager = UniversalWorkshopSessionManager()
    cleaned_count = session_manager.cleanup_expired_sessions()

    if cleaned_count > 0:
        frappe.logger().info(f"Cleaned up {cleaned_count} expired sessions")

    return cleaned_count
