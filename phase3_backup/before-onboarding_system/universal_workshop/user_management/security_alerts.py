"""
Security Alerts and Notifications System
Universal Workshop ERP - User Management
"""

import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date

from universal_workshop.user_management.audit_trail_extension import (
    get_audit_trail, AuditEventData, EventType, SeverityLevel
)


class AlertType(Enum):
    """Types of security alerts"""
    FAILED_LOGIN = "failed_login"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    PERMISSION_CHANGE = "permission_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MFA_DISABLED = "mfa_disabled"
    SESSION_ANOMALY = "session_anomaly"


class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"


class EscalationLevel(Enum):
    """Escalation levels for alerts"""
    NONE = "none"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"
    EMERGENCY = "emergency"


@dataclass
class AlertThreshold:
    """Configuration for alert thresholds"""
    alert_type: AlertType
    threshold_count: int
    time_window_minutes: int
    severity: SeverityLevel
    escalation_level: EscalationLevel
    notification_channels: List[NotificationChannel]
    cooldown_minutes: int = 60


class SecurityAlertsManager:
    """Main class for security alerts management"""
    
    def __init__(self):
        self.audit_trail = get_audit_trail()
        self.alert_thresholds = self._load_alert_thresholds()
        
    def _load_alert_thresholds(self) -> Dict[AlertType, AlertThreshold]:
        """Load alert threshold configurations"""
        
        default_thresholds = {
            AlertType.FAILED_LOGIN: AlertThreshold(
                alert_type=AlertType.FAILED_LOGIN,
                threshold_count=3,
                time_window_minutes=10,
                severity=SeverityLevel.MEDIUM,
                escalation_level=EscalationLevel.SUPERVISOR,
                notification_channels=[NotificationChannel.EMAIL],
                cooldown_minutes=30
            ),
            AlertType.MULTIPLE_FAILED_LOGINS: AlertThreshold(
                alert_type=AlertType.MULTIPLE_FAILED_LOGINS,
                threshold_count=5,
                time_window_minutes=15,
                severity=SeverityLevel.HIGH,
                escalation_level=EscalationLevel.MANAGER,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                cooldown_minutes=60
            ),
            AlertType.PERMISSION_CHANGE: AlertThreshold(
                alert_type=AlertType.PERMISSION_CHANGE,
                threshold_count=1,
                time_window_minutes=1,
                severity=SeverityLevel.HIGH,
                escalation_level=EscalationLevel.ADMINISTRATOR,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP],
                cooldown_minutes=0
            ),
            AlertType.MFA_DISABLED: AlertThreshold(
                alert_type=AlertType.MFA_DISABLED,
                threshold_count=1,
                time_window_minutes=1,
                severity=SeverityLevel.CRITICAL,
                escalation_level=EscalationLevel.EMERGENCY,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WHATSAPP],
                cooldown_minutes=0
            )
        }
        
        return default_thresholds
    
    def check_and_trigger_alerts(self, event_type: str, user_email: str, 
                                source_ip: str = None, details: Dict = None) -> List:
        """Check if event triggers any security alerts"""
        
        triggered_alerts = []
        
        try:
            event_to_alert_mapping = {
                'login_failed': AlertType.FAILED_LOGIN,
                'mfa_disabled': AlertType.MFA_DISABLED,
                'role_assigned': AlertType.PERMISSION_CHANGE,
                'permission_granted': AlertType.PERMISSION_CHANGE,
                'suspicious_activity': AlertType.SUSPICIOUS_ACTIVITY
            }
            
            alert_type = event_to_alert_mapping.get(event_type)
            if not alert_type or alert_type not in self.alert_thresholds:
                return triggered_alerts
                
            threshold_config = self.alert_thresholds[alert_type]
            
            if self._is_threshold_exceeded(alert_type, user_email, source_ip, threshold_config):
                alert = self._create_security_alert(
                    alert_type, user_email, source_ip, details or {}, threshold_config
                )
                
                self._send_alert_notifications(alert)
                self._log_alert_event(alert)
                
                triggered_alerts.append(alert)
                
        except Exception as e:
            frappe.log_error(f"Error checking security alerts: {e}")
            
        return triggered_alerts
    
    def _is_threshold_exceeded(self, alert_type: AlertType, user_email: str, 
                              source_ip: str, threshold_config: AlertThreshold) -> bool:
        """Check if alert threshold is exceeded"""
        
        try:
            if self._is_in_cooldown(alert_type, user_email, threshold_config.cooldown_minutes):
                return False
                
            cutoff_time = add_to_date(now_datetime(), minutes=-threshold_config.time_window_minutes)
            
            event_count = frappe.db.count("Security Audit Log", {
                "event_type": event_type.replace('_', '_'),
                "user_email": user_email,
                "timestamp": [">=", cutoff_time]
            })
            
            return event_count >= threshold_config.threshold_count
            
        except Exception as e:
            frappe.log_error(f"Error checking threshold for {alert_type}: {e}")
            return False
    
    def _is_in_cooldown(self, alert_type: AlertType, user_email: str, cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period"""
        
        if cooldown_minutes <= 0:
            return False
            
        try:
            cutoff_time = add_to_date(now_datetime(), minutes=-cooldown_minutes)
            
            recent_alert = frappe.db.exists("Security Alert Log", {
                "alert_type": alert_type.value,
                "user_email": user_email,
                "timestamp": [">=", cutoff_time]
            })
            
            return bool(recent_alert)
            
        except Exception as e:
            frappe.log_error(f"Error checking cooldown: {e}")
            return False
    
    def _create_security_alert(self, alert_type: AlertType, user_email: str, 
                              source_ip: str, details: Dict, threshold_config: AlertThreshold):
        """Create a security alert"""
        
        import hashlib
        
        alert_id = hashlib.sha256(
            f"{alert_type.value}_{user_email}_{now_datetime().isoformat()}".encode()
        ).hexdigest()[:16].upper()
        
        descriptions = {
            AlertType.FAILED_LOGIN: _("Multiple failed login attempts detected"),
            AlertType.MULTIPLE_FAILED_LOGINS: _("Excessive failed login attempts"),
            AlertType.PERMISSION_CHANGE: _("Critical permission change detected"),
            AlertType.MFA_DISABLED: _("Multi-factor authentication disabled"),
            AlertType.SUSPICIOUS_ACTIVITY: _("Suspicious activity pattern detected")
        }
        
        description = descriptions.get(alert_type, _("Security alert triggered"))
        
        alert_data = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": threshold_config.severity,
            "timestamp": now_datetime(),
            "user_email": user_email,
            "source_ip": source_ip or "unknown",
            "description": description,
            "details": details,
            "threshold_config": threshold_config,
            "escalation_level": threshold_config.escalation_level,
            "notifications_sent": []
        }
        
        self._save_alert_to_db(alert_data)
        
        return alert_data
    
    def _save_alert_to_db(self, alert):
        """Save security alert to database"""
        
        try:
            doc = frappe.get_doc({
                "doctype": "Security Alert Log",
                "alert_id": alert["alert_id"],
                "alert_type": alert["alert_type"].value,
                "severity": alert["severity"].value,
                "timestamp": alert["timestamp"],
                "user_email": alert["user_email"],
                "source_ip": alert["source_ip"],
                "description": alert["description"],
                "details": json.dumps(alert["details"]),
                "escalation_level": alert["escalation_level"].value,
                "notifications_sent": json.dumps(alert["notifications_sent"]),
                "is_resolved": 0
            })
            
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error saving security alert: {e}")
    
    def _send_alert_notifications(self, alert):
        """Send notifications for security alert"""
        
        try:
            for channel in alert["threshold_config"].notification_channels:
                success = False
                
                if channel == NotificationChannel.EMAIL:
                    success = self._send_email_alert(alert)
                elif channel == NotificationChannel.SMS:
                    success = self._send_sms_alert(alert)
                elif channel == NotificationChannel.WHATSAPP:
                    success = self._send_whatsapp_alert(alert)
                elif channel == NotificationChannel.IN_APP:
                    success = self._send_in_app_alert(alert)
                
                if success:
                    alert["notifications_sent"].append(channel.value)
                    
        except Exception as e:
            frappe.log_error(f"Error sending alert notifications: {e}")
    
    def _send_email_alert(self, alert) -> bool:
        """Send email alert notification"""
        
        try:
            recipients = self._get_alert_recipients(alert["escalation_level"])
            
            if not recipients:
                return False
            
            subject = f"🚨 Security Alert: {alert['description']}"
            
            language = frappe.db.get_value("User", frappe.session.user, "language") or "en"
            
            if language == "ar":
                subject = f"🚨 تنبيه أمني: {alert['description']}"
                template = self._get_arabic_email_template(alert)
            else:
                template = self._get_english_email_template(alert)
            
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=template,
                now=True
            )
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error sending email alert: {e}")
            return False
    
    def _send_sms_alert(self, alert) -> bool:
        """Send SMS alert notification"""
        
        try:
            recipients = self._get_sms_recipients(alert["escalation_level"])
            
            if not recipients:
                return False
            
            message = f"Security Alert: {alert['description']} for user {alert['user_email']}"
            
            for phone in recipients:
                frappe.call("universal_workshop.communication.sms_manager.send_sms", {
                    "phone": phone,
                    "message": message,
                    "priority": "high"
                })
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error sending SMS alert: {e}")
            return False
    
    def _send_whatsapp_alert(self, alert) -> bool:
        """Send WhatsApp alert notification"""
        
        try:
            recipients = self._get_whatsapp_recipients(alert["escalation_level"])
            
            if not recipients:
                return False
            
            message = f"🚨 *Security Alert*\n\n{alert['description']}\n\nUser: {alert['user_email']}\nTime: {alert['timestamp'].strftime('%Y-%m-%d %H:%M')}"
            
            for phone in recipients:
                frappe.call("universal_workshop.communication.whatsapp_manager.send_message", {
                    "phone": phone,
                    "message": message,
                    "priority": "high"
                })
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error sending WhatsApp alert: {e}")
            return False
    
    def _send_in_app_alert(self, alert) -> bool:
        """Send in-app notification"""
        
        try:
            users = self._get_alert_users(alert["escalation_level"])
            
            for user in users:
                notification = frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": f"Security Alert: {alert['description']}",
                    "for_user": user,
                    "type": "Alert",
                    "document_type": "Security Alert Log",
                    "document_name": alert["alert_id"],
                    "from_user": "Administrator"
                })
                notification.insert(ignore_permissions=True)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error sending in-app alert: {e}")
            return False
    
    def _get_alert_recipients(self, escalation_level):
        """Get email recipients based on escalation level"""
        
        try:
            recipients = []
            
            if escalation_level == EscalationLevel.SUPERVISOR:
                supervisors = frappe.get_all("User", 
                                           filters={"enabled": 1},
                                           fields=["email"])
                for user in supervisors:
                    user_roles = frappe.get_roles(user.email)
                    if "Workshop Supervisor" in user_roles:
                        recipients.append(user.email)
                        
            elif escalation_level == EscalationLevel.MANAGER:
                managers = frappe.get_all("User", 
                                        filters={"enabled": 1},
                                        fields=["email"])
                for user in managers:
                    user_roles = frappe.get_roles(user.email)
                    if "Workshop Manager" in user_roles:
                        recipients.append(user.email)
                        
            elif escalation_level in [EscalationLevel.ADMINISTRATOR, EscalationLevel.EMERGENCY]:
                admins = frappe.get_all("User", 
                                      filters={"enabled": 1},
                                      fields=["email"])
                for user in admins:
                    user_roles = frappe.get_roles(user.email)
                    if "System Manager" in user_roles:
                        recipients.append(user.email)
            
            return recipients
            
        except Exception as e:
            frappe.log_error(f"Error getting alert recipients: {e}")
            return []
    
    def _get_sms_recipients(self, escalation_level):
        """Get SMS recipients based on escalation level"""
        
        try:
            recipients = []
            users = self._get_alert_users(escalation_level)
            
            for user_email in users:
                phone = frappe.db.get_value("User", user_email, "mobile_no")
                if phone:
                    recipients.append(phone)
            
            return recipients
            
        except Exception as e:
            frappe.log_error(f"Error getting SMS recipients: {e}")
            return []
    
    def _get_whatsapp_recipients(self, escalation_level):
        """Get WhatsApp recipients based on escalation level"""
        
        return self._get_sms_recipients(escalation_level)
    
    def _get_alert_users(self, escalation_level):
        """Get user emails based on escalation level"""
        
        return self._get_alert_recipients(escalation_level)
    
    def _get_english_email_template(self, alert) -> str:
        """Get English email template for alert"""
        
        return f"""
        <h2>🚨 Security Alert</h2>
        
        <p><strong>Alert Type:</strong> {alert['alert_type'].value.replace('_', ' ').title()}</p>
        <p><strong>Severity:</strong> {alert['severity'].value.upper()}</p>
        <p><strong>User:</strong> {alert['user_email']}</p>
        <p><strong>Source IP:</strong> {alert['source_ip']}</p>
        <p><strong>Time:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Description:</strong> {alert['description']}</p>
        
        <h3>Event Details:</h3>
        <pre>{json.dumps(alert['details'], indent=2)}</pre>
        
        <p><strong>Escalation Level:</strong> {alert['escalation_level'].value.title()}</p>
        
        <hr>
        <p><em>This is an automated security alert from Universal Workshop ERP.</em></p>
        <p><em>Please investigate immediately and take appropriate action.</em></p>
        """
    
    def _get_arabic_email_template(self, alert) -> str:
        """Get Arabic email template for alert"""
        
        return f"""
        <div dir="rtl" style="text-align: right;">
        <h2>🚨 تنبيه أمني</h2>
        
        <p><strong>نوع التنبيه:</strong> {alert['alert_type'].value.replace('_', ' ')}</p>
        <p><strong>مستوى الخطورة:</strong> {alert['severity'].value.upper()}</p>
        <p><strong>المستخدم:</strong> {alert['user_email']}</p>
        <p><strong>عنوان IP:</strong> {alert['source_ip']}</p>
        <p><strong>الوقت:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>الوصف:</strong> {alert['description']}</p>
        
        <h3>تفاصيل الحدث:</h3>
        <pre>{json.dumps(alert['details'], indent=2)}</pre>
        
        <p><strong>مستوى التصعيد:</strong> {alert['escalation_level'].value}</p>
        
        <hr>
        <p><em>هذا تنبيه أمني تلقائي من نظام إدارة الورشة الشامل.</em></p>
        <p><em>يرجى التحقيق فوراً واتخاذ الإجراء المناسب.</em></p>
        </div>
        """
    
    def _log_alert_event(self, alert):
        """Log alert event in audit trail"""
        
        try:
            event_data = AuditEventData(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=alert["severity"],
                user_email=alert["user_email"],
                description=f"Security alert triggered: {alert['description']}",
                details={
                    "alert_id": alert["alert_id"],
                    "alert_type": alert["alert_type"].value,
                    "escalation_level": alert["escalation_level"].value,
                    "notifications_sent": alert["notifications_sent"]
                }
            )
            
            self.audit_trail.log_event(event_data)
            
        except Exception as e:
            frappe.log_error(f"Error logging alert event: {e}")


# Global instance
_security_alerts_manager = None


def get_security_alerts_manager():
    """Get global security alerts manager instance"""
    global _security_alerts_manager
    if _security_alerts_manager is None:
        _security_alerts_manager = SecurityAlertsManager()
    return _security_alerts_manager


@frappe.whitelist()
def trigger_security_alert(event_type, user_email, source_ip=None, details=None):
    """API method to trigger security alert check"""
    
    try:
        manager = get_security_alerts_manager()
        
        if isinstance(details, str):
            details = json.loads(details) if details else {}
        
        alerts = manager.check_and_trigger_alerts(
            event_type=event_type,
            user_email=user_email,
            source_ip=source_ip,
            details=details or {}
        )
        
        return {
            "success": True,
            "alerts_triggered": len(alerts),
            "alert_ids": [alert["alert_id"] for alert in alerts]
        }
        
    except Exception as e:
        frappe.log_error(f"Error triggering security alert: {e}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_security_alerts_summary(days=7):
    """Get summary of security alerts for dashboard"""
    
    try:
        from frappe.utils import add_days, today
        
        start_date = add_days(today(), -int(days))
        
        alert_stats = frappe.db.sql("""
            SELECT 
                alert_type,
                severity,
                COUNT(*) as count,
                SUM(CASE WHEN is_resolved = 0 THEN 1 ELSE 0 END) as unresolved
            FROM `tabSecurity Alert Log`
            WHERE DATE(timestamp) >= %s
            GROUP BY alert_type, severity
            ORDER BY count DESC
        """, [start_date], as_dict=True)
        
        total_alerts = frappe.db.count("Security Alert Log", {
            "timestamp": [">=", start_date]
        })
        
        unresolved_alerts = frappe.db.count("Security Alert Log", {
            "timestamp": [">=", start_date],
            "is_resolved": 0
        })
        
        critical_alerts = frappe.db.sql("""
            SELECT alert_type, user_email, description, timestamp
            FROM `tabSecurity Alert Log`
            WHERE severity = 'critical'
            AND timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT 10
        """, [start_date], as_dict=True)
        
        return {
            "success": True,
            "summary": {
                "total_alerts": total_alerts,
                "unresolved_alerts": unresolved_alerts,
                "alert_stats": alert_stats,
                "critical_alerts": critical_alerts,
                "period_days": days,
                "generated_at": now_datetime().isoformat()
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting alerts summary: {e}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def resolve_security_alert(alert_id, resolution_notes=""):
    """Mark security alert as resolved"""
    
    try:
        alert = frappe.get_doc("Security Alert Log", {"alert_id": alert_id})
        
        alert.is_resolved = 1
        alert.resolved_by = frappe.session.user
        alert.resolved_at = now_datetime()
        alert.resolution_notes = resolution_notes
        
        alert.save(ignore_permissions=True)
        
        audit_trail = get_audit_trail()
        event_data = AuditEventData(
            event_type=EventType.SUSPICIOUS_ACTIVITY,
            severity=SeverityLevel.INFO,
            user_email=frappe.session.user,
            description=f"Security alert {alert_id} resolved",
            details={
                "alert_id": alert_id,
                "resolution_notes": resolution_notes,
                "resolved_by": frappe.session.user
            }
        )
        audit_trail.log_event(event_data)
        
        return {"success": True, "message": "Alert resolved successfully"}
        
    except Exception as e:
        frappe.log_error(f"Error resolving security alert: {e}")
        return {"success": False, "error": str(e)}
