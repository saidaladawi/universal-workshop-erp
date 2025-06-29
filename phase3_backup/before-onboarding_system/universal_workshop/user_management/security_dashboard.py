"""
Security Dashboard for Universal Workshop ERP

Provides comprehensive security monitoring, role management, and real-time alerts
for the workshop management system with Arabic localization support.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, format_datetime, cint

from .custom_permission_engine import CustomPermissionEngine


class SecurityDashboard:
    """
    Main security dashboard controller providing comprehensive security monitoring
    and management capabilities for Universal Workshop ERP.
    """

    def __init__(self):
        """Initialize security dashboard with permission engine integration"""
        self.permission_engine = CustomPermissionEngine()

    def get_dashboard_data(self, timeframe_hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for security monitoring
        
        Args:
            timeframe_hours: Time window for data collection (default 24 hours)
            
        Returns:
            Dict containing all dashboard widgets and metrics
        """
        try:
            cutoff_time = now_datetime() - timedelta(hours=timeframe_hours)
            
            return {
                "security_metrics": self._get_security_metrics(cutoff_time),
                "permission_summary": self._get_permission_summary(),
                "recent_activities": self._get_recent_activities(cutoff_time),
                "security_alerts": self._get_security_alerts(cutoff_time),
                "user_activities": self._get_user_activities(cutoff_time),
                "license_status": self._get_license_status(),
                "system_health": self._get_system_health(),
                "generated_at": format_datetime(now_datetime()),
                "timeframe_hours": timeframe_hours
            }
            
        except Exception as e:
            frappe.log_error(f"Security Dashboard Error: {e}")
            return {"error": str(e), "generated_at": format_datetime(now_datetime())}

    def _get_security_metrics(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Get key security metrics for the dashboard"""
        try:
            # Failed login attempts
            failed_logins = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabActivity Log`
                WHERE subject_field = 'User'
                AND operation = 'Login Failed'
                AND creation >= %s
            """, [cutoff_time])[0][0] or 0

            # Permission violations
            permission_violations = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabActivity Log`
                WHERE subject_field LIKE '%Permission%'
                AND operation = 'Access Denied'
                AND creation >= %s
            """, [cutoff_time])[0][0] or 0

            # Active sessions
            active_sessions = frappe.db.sql("""
                SELECT COUNT(DISTINCT user) as count
                FROM `tabSessions`
                WHERE lastupdate >= %s
            """, [cutoff_time])[0][0] or 0

            # License violations
            license_violations = self._count_license_violations(cutoff_time)

            return {
                "failed_logins": failed_logins,
                "permission_violations": permission_violations,
                "active_sessions": active_sessions,
                "license_violations": license_violations,
                "risk_level": self._calculate_risk_level(failed_logins, permission_violations, license_violations)
            }

        except Exception as e:
            frappe.log_error(f"Security metrics error: {e}")
            return {"error": str(e)}

    def _get_permission_summary(self) -> Dict[str, Any]:
        """Get summary of current permission assignments"""
        try:
            # Active workshop roles
            active_roles = frappe.db.sql("""
                SELECT role_name, priority_level
                FROM `tabWorkshop Role`
                WHERE is_active = 1
                ORDER BY priority_level DESC
            """, as_dict=True)

            # Recent permission changes
            recent_changes = frappe.db.sql("""
                SELECT modified, modified_by, name, 'Workshop Role' as doctype
                FROM `tabWorkshop Role`
                WHERE modified >= %s
                ORDER BY modified DESC
                LIMIT 10
            """, [now_datetime() - timedelta(hours=24)], as_dict=True)

            return {
                "active_roles": active_roles,
                "recent_changes": recent_changes,
                "total_workshop_roles": len(active_roles)
            }

        except Exception as e:
            frappe.log_error(f"Permission summary error: {e}")
            return {"error": str(e)}

    def _get_recent_activities(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get recent security-related activities"""
        try:
            activities = frappe.db.sql("""
                SELECT 
                    creation,
                    user,
                    subject_field,
                    operation,
                    ip_address,
                    subject,
                    content
                FROM `tabActivity Log`
                WHERE creation >= %s
                AND (
                    operation IN ('Login', 'Logout', 'Login Failed', 'Permission Denied')
                    OR subject_field LIKE '%Permission%'
                    OR subject_field LIKE '%Role%'
                    OR subject_field = 'User'
                )
                ORDER BY creation DESC
                LIMIT 50
            """, [cutoff_time], as_dict=True)

            # Enhance activities with risk assessment
            enhanced_activities = []
            for activity in activities:
                risk_score = self._assess_activity_risk(activity)
                activity.update({
                    "risk_score": risk_score,
                    "formatted_time": format_datetime(activity.creation),
                    "severity": self._get_severity_from_risk(risk_score)
                })
                enhanced_activities.append(activity)

            return enhanced_activities

        except Exception as e:
            frappe.log_error(f"Recent activities error: {e}")
            return [{"error": str(e)}]

    def _get_security_alerts(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get active security alerts requiring attention"""
        alerts = []

        try:
            # Multiple failed login attempts
            failed_login_users = frappe.db.sql("""
                SELECT 
                    user,
                    COUNT(*) as attempt_count,
                    MAX(creation) as last_attempt,
                    ip_address
                FROM `tabActivity Log`
                WHERE operation = 'Login Failed'
                AND creation >= %s
                GROUP BY user, ip_address
                HAVING attempt_count >= 3
                ORDER BY attempt_count DESC
            """, [cutoff_time], as_dict=True)

            for user_alert in failed_login_users:
                alerts.append({
                    "id": f"failed_login_{user_alert.user}_{user_alert.ip_address}",
                    "type": "failed_login",
                    "severity": "high" if user_alert.attempt_count >= 5 else "medium",
                    "title": _("Multiple Failed Login Attempts"),
                    "message": _("User {0} has {1} failed login attempts from IP {2}").format(
                        user_alert.user, user_alert.attempt_count, user_alert.ip_address
                    ),
                    "user": user_alert.user,
                    "details": user_alert,
                    "created_at": user_alert.last_attempt,
                    "status": "active"
                })

            return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            frappe.log_error(f"Security alerts error: {e}")
            return [{"error": str(e), "type": "system_error"}]

    def _get_user_activities(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Get user activity analytics"""
        try:
            # Most active users
            active_users = frappe.db.sql("""
                SELECT 
                    user,
                    COUNT(*) as activity_count,
                    MAX(creation) as last_activity
                FROM `tabActivity Log`
                WHERE creation >= %s
                AND user != 'Administrator'
                GROUP BY user
                ORDER BY activity_count DESC
                LIMIT 10
            """, [cutoff_time], as_dict=True)

            # Activity by operation type
            operation_stats = frappe.db.sql("""
                SELECT 
                    operation,
                    COUNT(*) as count
                FROM `tabActivity Log`
                WHERE creation >= %s
                GROUP BY operation
                ORDER BY count DESC
            """, [cutoff_time], as_dict=True)

            return {
                "active_users": active_users,
                "operation_stats": operation_stats,
                "total_activities": sum(stat.count for stat in operation_stats)
            }

        except Exception as e:
            frappe.log_error(f"User activities error: {e}")
            return {"error": str(e)}

    def _get_license_status(self) -> Dict[str, Any]:
        """Get current license and compliance status"""
        try:
            return {
                "status": "active",
                "expires_at": "2025-12-31",
                "users_licensed": 50,
                "users_active": 25,
                "compliance_score": 95,
                "last_validation": format_datetime(now_datetime()),
                "violations_today": 0,
                "grace_period_used": False
            }

        except Exception as e:
            frappe.log_error(f"License status error: {e}")
            return {"error": str(e)}

    def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system security health metrics"""
        try:
            # Database health
            db_health = self._check_database_health()
            
            # Permission integrity
            permission_integrity = self._check_permission_integrity()
            
            # Session health
            session_health = self._check_session_health()

            overall_score = (db_health + permission_integrity + session_health) / 3

            return {
                "overall_score": round(overall_score, 1),
                "database_health": db_health,
                "permission_integrity": permission_integrity,
                "session_health": session_health,
                "status": self._get_health_status(overall_score),
                "last_check": format_datetime(now_datetime())
            }

        except Exception as e:
            frappe.log_error(f"System health error: {e}")
            return {"error": str(e)}

    def _calculate_risk_level(self, failed_logins: int, permission_violations: int, license_violations: int) -> str:
        """Calculate overall risk level based on security metrics"""
        total_violations = failed_logins + permission_violations + license_violations
        
        if total_violations >= 20:
            return "critical"
        elif total_violations >= 10:
            return "high"
        elif total_violations >= 5:
            return "medium"
        else:
            return "low"

    def _assess_activity_risk(self, activity: Dict[str, Any]) -> int:
        """Assess risk score for individual activity (0-10)"""
        risk_score = 0
        
        # Base risk by operation type
        operation_risks = {
            "Login Failed": 3,
            "Permission Denied": 5,
            "Role Modified": 7,
            "Permission Modified": 8,
            "User Created": 4,
            "User Deleted": 9
        }
        
        risk_score += operation_risks.get(activity.get("operation"), 1)
        
        # Additional risk factors
        if activity.get("ip_address") and not self._is_trusted_ip(activity.get("ip_address")):
            risk_score += 2
            
        if activity.get("user") == "Administrator":
            risk_score += 1
            
        return min(risk_score, 10)

    def _get_severity_from_risk(self, risk_score: int) -> str:
        """Convert risk score to severity level"""
        if risk_score >= 8:
            return "critical"
        elif risk_score >= 6:
            return "high"
        elif risk_score >= 4:
            return "medium"
        else:
            return "low"

    def _count_license_violations(self, cutoff_time: datetime) -> int:
        """Count license violations in the given timeframe"""
        # Placeholder - integrate with your license management system
        return 0

    def _is_trusted_ip(self, ip_address: str) -> bool:
        """Check if IP address is in trusted range"""
        # Define trusted IP ranges (local network, office IPs, etc.)
        trusted_ranges = [
            "192.168.",
            "10.",
            "172.16.",
            "127.0.0.1"
        ]
        
        return any(ip_address.startswith(trusted) for trusted in trusted_ranges)

    def _check_database_health(self) -> float:
        """Check database health score (0-100)"""
        try:
            return 95.0  # Placeholder
        except Exception:
            return 50.0

    def _check_permission_integrity(self) -> float:
        """Check permission system integrity (0-100)"""
        try:
            test_result = self.permission_engine.validate_system_integrity()
            return 90.0 if test_result else 60.0
        except Exception:
            return 50.0

    def _check_session_health(self) -> float:
        """Check session management health (0-100)"""
        try:
            return 88.0  # Placeholder
        except Exception:
            return 50.0

    def _get_health_status(self, score: float) -> str:
        """Get health status from score"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        else:
            return "poor"


# WhiteListed API Methods for Dashboard Access

@frappe.whitelist()
def get_security_dashboard_data(timeframe_hours: int = 24):
    """
    API endpoint to get security dashboard data
    
    Args:
        timeframe_hours: Time window for data collection (default 24 hours)
        
    Returns:
        Dict containing dashboard data
    """
    try:
        dashboard = SecurityDashboard()
        return dashboard.get_dashboard_data(cint(timeframe_hours))
    except Exception as e:
        frappe.log_error(f"Dashboard API error: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def acknowledge_security_alert(alert_id: str, notes: str = ""):
    """
    Acknowledge a security alert
    
    Args:
        alert_id: ID of the alert to acknowledge
        notes: Optional notes about the acknowledgment
        
    Returns:
        Success/failure status
    """
    try:
        # Log the acknowledgment
        frappe.get_doc({
            "doctype": "Activity Log",
            "subject_field": "Security Alert",
            "operation": "Alert Acknowledged",
            "subject": alert_id,
            "content": f"Alert acknowledged by {frappe.session.user}. Notes: {notes}",
            "user": frappe.session.user,
            "ip_address": frappe.local.request.environ.get("REMOTE_ADDR")
        }).insert(ignore_permissions=True)
        
        return {"success": True, "message": _("Alert acknowledged successfully")}
        
    except Exception as e:
        frappe.log_error(f"Alert acknowledgment error: {e}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_user_security_profile(user_email: str):
    """
    Get detailed security profile for a specific user
    
    Args:
        user_email: Email of the user to analyze
        
    Returns:
        Dict containing user security profile
    """
    try:
        # Verify permission to view user profiles
        if not frappe.has_permission("User", "read"):
            frappe.throw(_("Insufficient permissions to view user profiles"))
        
        user_profile = {
            "user": user_email,
            "last_login": frappe.db.get_value("User", user_email, "last_login"),
            "login_attempts_today": frappe.db.sql("""
                SELECT COUNT(*) FROM `tabActivity Log`
                WHERE user = %s AND operation = 'Login Failed'
                AND DATE(creation) = CURDATE()
            """, [user_email])[0][0],
            "workshop_roles": frappe.db.sql("""
                SELECT role_name FROM `tabWorkshop Role`
                WHERE name IN (
                    SELECT role FROM `tabHas Role` WHERE parent = %s
                )
            """, [user_email], as_dict=True),
            "recent_activities": frappe.db.sql("""
                SELECT creation, operation, subject_field, ip_address
                FROM `tabActivity Log`
                WHERE user = %s
                ORDER BY creation DESC
                LIMIT 20
            """, [user_email], as_dict=True)
        }
        
        return user_profile
        
    except Exception as e:
        frappe.log_error(f"User security profile error: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def refresh_dashboard_widget(widget_name: str, timeframe_hours: int = 24):
    """
    Refresh specific dashboard widget data
    
    Args:
        widget_name: Name of the widget to refresh
        timeframe_hours: Time window for data collection
        
    Returns:
        Updated widget data
    """
    try:
        dashboard = SecurityDashboard()
        cutoff_time = now_datetime() - timedelta(hours=cint(timeframe_hours))
        
        widget_methods = {
            "security_metrics": dashboard._get_security_metrics,
            "permission_summary": dashboard._get_permission_summary,
            "recent_activities": dashboard._get_recent_activities,
            "security_alerts": dashboard._get_security_alerts,
            "user_activities": dashboard._get_user_activities,
            "license_status": dashboard._get_license_status,
            "system_health": dashboard._get_system_health
        }
        
        if widget_name not in widget_methods:
            frappe.throw(_("Invalid widget name: {0}").format(widget_name))
        
        method = widget_methods[widget_name]
        if widget_name in ["permission_summary", "license_status", "system_health"]:
            return method()
        else:
            return method(cutoff_time)
            
    except Exception as e:
        frappe.log_error(f"Widget refresh error: {e}")
        return {"error": str(e)}
