"""
Audit Trail Extension System
Universal Workshop ERP - User Management
"""

import json
import hashlib
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import frappe
from frappe import _
from frappe.utils import now_datetime


class EventType(Enum):
    """Audit event types"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    SESSION_CREATED = "session_created"
    SESSION_REVOKED = "session_revoked"
    ROLE_ASSIGNED = "role_assigned"
    PERMISSION_GRANTED = "permission_granted"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SeverityLevel(Enum):
    """Event severity levels"""

    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEventData:
    """Audit event data structure"""

    event_type: EventType
    severity: SeverityLevel
    user_email: str
    description: str = ""
    details: Dict[str, Any] = None
    timestamp: Optional[datetime.datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = now_datetime()
        if self.details is None:
            self.details: Dict[str, Any] = {}


class AuditTrailExtension:
    """Enhanced Audit Trail System"""

    def log_event(self, event_data: AuditEventData) -> Optional[str]:
        """Log security event"""
        try:
            event_id = self._generate_event_id(event_data)

            doc = frappe.get_doc(
                {
                    "doctype": "Security Audit Log",
                    "event_id": event_id,
                    "event_type": event_data.event_type.value,
                    "severity": event_data.severity.value,
                    "timestamp": event_data.timestamp,
                    "user_email": event_data.user_email,
                    "description": event_data.description,
                    "details": json.dumps(event_data.details),
                }
            )

            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return event_id

        except Exception as e:
            frappe.log_error(f"Audit logging error: {e}")
            return None

    def _generate_event_id(self, event_data: AuditEventData) -> str:
        """Generate unique event ID"""
        return (
            hashlib.sha256(
                f"{event_data.event_type.value}_{event_data.user_email}_{event_data.timestamp}".encode()
            )
            .hexdigest()[:16]
            .upper()
        )


# Global instance
_audit_trail = None


def get_audit_trail():
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrailExtension()
    return _audit_trail


@frappe.whitelist()
def log_audit_event(event_type, severity, description, details=None):
    """API to log audit event"""
    try:
        audit_trail = get_audit_trail()
        event_data = AuditEventData(
            event_type=EventType(event_type),
            severity=SeverityLevel(severity),
            user_email=frappe.session.user,
            description=description,
            details=json.loads(details) if isinstance(details, str) else details,
        )

        event_id = audit_trail.log_event(event_data)
        return {"success": True, "event_id": event_id}

    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_audit_summary(days=30):
    """Get audit trail summary for dashboard"""
    try:
        from frappe.utils import add_days, today

        start_date = add_days(today(), -int(days))

        # Get event counts by type and severity
        event_counts = frappe.db.sql(
            """
            SELECT 
                event_type,
                severity,
                COUNT(*) as count
            FROM `tabSecurity Audit Log`
            WHERE DATE(timestamp) >= %s
            GROUP BY event_type, severity
            ORDER BY count DESC
        """,
            [start_date],
            as_dict=True,
        )

        # Get total event count
        total_events = frappe.db.sql(
            """
            SELECT COUNT(*) as total
            FROM `tabSecurity Audit Log`
            WHERE DATE(timestamp) >= %s
        """,
            [start_date],
        )[0][0]

        # Get recent critical events
        critical_events = frappe.db.sql(
            """
            SELECT event_type, description, timestamp, user_email
            FROM `tabSecurity Audit Log`
            WHERE severity IN ('critical', 'high')
            AND DATE(timestamp) >= %s
            ORDER BY timestamp DESC
            LIMIT 10
        """,
            [start_date],
            as_dict=True,
        )

        return {
            "success": True,
            "event_counts": event_counts,
            "total_events": total_events,
            "critical_events": critical_events,
            "period_days": days,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
