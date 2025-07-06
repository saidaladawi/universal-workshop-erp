# Security Framework API Reference

## Overview

This document provides a comprehensive reference for all API endpoints in the Universal Workshop ERP Security Framework.

## Authentication

All API endpoints require proper authentication and appropriate permissions. Include the following headers:

```http
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
Accept: application/json
```

## Security Alerts API

### Trigger Security Alert

**Endpoint:** `POST /api/method/universal_workshop.user_management.security_alerts.trigger_security_alert`

**Description:** Manually trigger a security alert.

**Parameters:**
- `alert_type` (string, required): Type of alert (failed_login, permission_change, etc.)
- `user_email` (string, required): Email of the user involved
- `source_ip` (string, optional): IP address of the source
- `details` (object, optional): Additional alert details

**Example Request:**
```json
{
    "alert_type": "suspicious_activity",
    "user_email": "user@workshop.com",
    "source_ip": "192.168.1.100",
    "details": {
        "activity_type": "unusual_access_pattern",
        "description": "Multiple failed attempts from different locations"
    }
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "alert_id": "SEC-2024-001234",
        "notifications_sent": ["email", "sms"],
        "escalation_level": "manager"
    }
}
```

### Get Security Alerts Summary

**Endpoint:** `GET /api/method/universal_workshop.user_management.security_alerts.get_security_alerts_summary`

**Description:** Get summary of security alerts for dashboard.

**Parameters:**
- `days` (integer, optional): Number of days to include (default: 7)
- `alert_types` (array, optional): Filter by specific alert types

**Example Request:**
```http
GET /api/method/universal_workshop.user_management.security_alerts.get_security_alerts_summary?days=30
```

**Example Response:**
```json
{
    "message": {
        "total_alerts": 45,
        "unresolved_alerts": 3,
        "critical_alerts": 1,
        "alert_breakdown": {
            "failed_login": 20,
            "permission_change": 15,
            "suspicious_activity": 10
        },
        "recent_critical": [
            {
                "alert_id": "SEC-2024-001234",
                "alert_type": "mfa_disabled",
                "user_email": "admin@workshop.com",
                "timestamp": "2024-06-23T10:30:00Z"
            }
        ]
    }
}
```

### Resolve Security Alert

**Endpoint:** `POST /api/method/universal_workshop.user_management.security_alerts.resolve_security_alert`

**Description:** Mark a security alert as resolved.

**Parameters:**
- `alert_id` (string, required): ID of the alert to resolve
- `resolution_notes` (string, required): Notes about the resolution

**Example Request:**
```json
{
    "alert_id": "SEC-2024-001234",
    "resolution_notes": "False positive - user was traveling and using VPN"
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "alert_id": "SEC-2024-001234",
        "resolved_by": "admin@workshop.com",
        "resolved_at": "2024-06-23T11:15:00Z"
    }
}
```

## Session Management API

### Get Session Status

**Endpoint:** `GET /api/method/universal_workshop.user_management.session_manager.get_session_status`

**Description:** Get current session information for a user.

**Parameters:**
- `user_email` (string, required): Email of the user

**Example Request:**
```http
GET /api/method/universal_workshop.user_management.session_manager.get_session_status?user_email=user@workshop.com
```

**Example Response:**
```json
{
    "message": {
        "active_sessions": 2,
        "max_allowed": 3,
        "sessions": [
            {
                "session_id": "sess_abc123",
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows 10",
                    "device_type": "desktop"
                },
                "ip_address": "192.168.1.100",
                "login_time": "2024-06-23T09:00:00Z",
                "last_activity": "2024-06-23T10:30:00Z",
                "is_current": true
            }
        ]
    }
}
```

### Revoke Session

**Endpoint:** `POST /api/method/universal_workshop.user_management.session_manager.revoke_session`

**Description:** Revoke a specific user session.

**Parameters:**
- `session_id` (string, required): ID of the session to revoke
- `reason` (string, optional): Reason for revocation

**Example Request:**
```json
{
    "session_id": "sess_abc123",
    "reason": "Security concern - unauthorized access"
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "session_id": "sess_abc123",
        "revoked_at": "2024-06-23T11:00:00Z",
        "reason": "Security concern - unauthorized access"
    }
}
```

### Revoke All User Sessions

**Endpoint:** `POST /api/method/universal_workshop.user_management.session_manager.revoke_user_sessions`

**Description:** Revoke all sessions for a specific user.

**Parameters:**
- `user_email` (string, required): Email of the user
- `exclude_current` (boolean, optional): Whether to exclude current session (default: true)
- `reason` (string, optional): Reason for revocation

**Example Request:**
```json
{
    "user_email": "user@workshop.com",
    "exclude_current": false,
    "reason": "Password compromised"
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "revoked_sessions": 3,
        "user_email": "user@workshop.com",
        "revoked_at": "2024-06-23T11:05:00Z"
    }
}
```

### Get Session Statistics

**Endpoint:** `GET /api/method/universal_workshop.user_management.session_manager.get_session_statistics`

**Description:** Get session statistics for dashboard.

**Parameters:**
- `days` (integer, optional): Number of days to include (default: 7)

**Example Response:**
```json
{
    "message": {
        "active_sessions": 15,
        "total_logins_today": 45,
        "unique_users_today": 12,
        "average_session_duration": "2h 30m",
        "top_devices": [
            {"device": "Chrome/Windows", "count": 8},
            {"device": "Safari/macOS", "count": 4}
        ]
    }
}
```

## Multi-Factor Authentication API

### Enable MFA

**Endpoint:** `POST /api/method/universal_workshop.user_management.mfa_manager.enable_mfa`

**Description:** Enable MFA for a user.

**Parameters:**
- `user_email` (string, required): Email of the user
- `mfa_method` (string, required): MFA method (totp, sms, whatsapp, email)

**Example Request:**
```json
{
    "user_email": "user@workshop.com",
    "mfa_method": "totp"
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "secret_key": "JBSWY3DPEHPK3PXP",
        "backup_codes": [
            "12345678", "87654321", "11223344"
        ]
    }
}
```

### Verify MFA

**Endpoint:** `POST /api/method/universal_workshop.user_management.mfa_manager.verify_mfa`

**Description:** Verify MFA code.

**Parameters:**
- `user_email` (string, required): Email of the user
- `code` (string, required): MFA verification code
- `is_backup_code` (boolean, optional): Whether this is a backup code

**Example Request:**
```json
{
    "user_email": "user@workshop.com",
    "code": "123456",
    "is_backup_code": false
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "verified": true,
        "remaining_backup_codes": 9
    }
}
```

### Generate Backup Codes

**Endpoint:** `POST /api/method/universal_workshop.user_management.mfa_manager.generate_backup_codes`

**Description:** Generate new backup codes for a user.

**Parameters:**
- `user_email` (string, required): Email of the user

**Example Response:**
```json
{
    "message": {
        "success": true,
        "backup_codes": [
            "12345678", "87654321", "11223344",
            "55667788", "99887766", "44332211",
            "66778899", "33445566", "77889900",
            "22334455"
        ]
    }
}
```

## Audit Trail API

### Log Audit Event

**Endpoint:** `POST /api/method/universal_workshop.user_management.audit_trail_extension.log_audit_event`

**Description:** Log a security audit event.

**Parameters:**
- `event_type` (string, required): Type of event
- `severity` (string, required): Severity level (info, medium, high, critical)
- `user_email` (string, required): Email of the user involved
- `description` (string, required): Event description
- `details` (object, optional): Additional event details

**Example Request:**
```json
{
    "event_type": "permission_granted",
    "severity": "medium",
    "user_email": "user@workshop.com",
    "description": "Permission granted to access financial reports",
    "details": {
        "permission_type": "read",
        "doctype": "Financial Report",
        "granted_by": "admin@workshop.com"
    }
}
```

**Example Response:**
```json
{
    "message": {
        "success": true,
        "event_id": "AUD-2024-001234",
        "timestamp": "2024-06-23T11:10:00Z"
    }
}
```

### Get Audit Summary

**Endpoint:** `GET /api/method/universal_workshop.user_management.audit_trail_extension.get_audit_summary`

**Description:** Get audit trail summary for dashboard.

**Parameters:**
- `days` (integer, optional): Number of days to include (default: 30)
- `event_types` (array, optional): Filter by specific event types
- `severity_levels` (array, optional): Filter by severity levels

**Example Request:**
```http
GET /api/method/universal_workshop.user_management.audit_trail_extension.get_audit_summary?days=7&event_types=["login_failed","permission_change"]
```

**Example Response:**
```json
{
    "message": {
        "total_events": 156,
        "critical_events": 2,
        "event_breakdown": {
            "login_failed": 45,
            "permission_change": 12,
            "mfa_enabled": 8
        },
        "top_users": [
            {"user": "admin@workshop.com", "events": 25},
            {"user": "manager@workshop.com", "events": 18}
        ],
        "recent_critical": [
            {
                "event_id": "AUD-2024-001234",
                "event_type": "unauthorized_access_attempt",
                "user_email": "unknown@domain.com",
                "timestamp": "2024-06-23T10:45:00Z"
            }
        ]
    }
}
```

## Permission Management API

### Check Custom Permission

**Endpoint:** `POST /api/method/universal_workshop.user_management.custom_permission_engine.check_permission`

**Description:** Check if user has permission for specific action.

**Parameters:**
- `doctype` (string, required): Document type
- `docname` (string, required): Document name
- `permission_type` (string, required): Permission type (read, write, create, delete)
- `user_email` (string, optional): User email (defaults to current user)

**Example Request:**
```json
{
    "doctype": "Work Order",
    "docname": "WO-2024-001",
    "permission_type": "write",
    "user_email": "technician@workshop.com"
}
```

**Example Response:**
```json
{
    "message": {
        "has_permission": true,
        "reason": "User is assigned technician for this work order",
        "conditions_met": ["assigned_technician", "active_status"]
    }
}
```

## Error Handling

### Common Error Responses

#### Authentication Error (401):
```json
{
    "exc_type": "AuthenticationError",
    "exception": "Invalid API credentials"
}
```

#### Permission Error (403):
```json
{
    "exc_type": "PermissionError", 
    "exception": "Insufficient permissions for this operation"
}
```

#### Validation Error (400):
```json
{
    "exc_type": "ValidationError",
    "exception": "Invalid alert_type provided"
}
```

#### Not Found Error (404):
```json
{
    "exc_type": "DoesNotExistError",
    "exception": "Alert SEC-2024-001234 not found"
}
```

#### Rate Limit Error (429):
```json
{
    "exc_type": "RateLimitError",
    "exception": "Too many requests. Please try again later."
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Security Alerts**: 100 requests per hour per user
- **Session Management**: 200 requests per hour per user  
- **MFA Operations**: 50 requests per hour per user
- **Audit Logging**: 500 requests per hour per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1624456800
```

## Webhooks

### Security Alert Webhook

Configure webhooks to receive real-time security alerts:

**Endpoint Configuration:**
```json
{
    "url": "https://your-system.com/webhook/security-alert",
    "events": ["security_alert_triggered", "security_alert_resolved"],
    "secret": "your_webhook_secret"
}
```

**Webhook Payload:**
```json
{
    "event": "security_alert_triggered",
    "timestamp": "2024-06-23T11:15:00Z",
    "data": {
        "alert_id": "SEC-2024-001234",
        "alert_type": "failed_login",
        "severity": "medium",
        "user_email": "user@workshop.com",
        "source_ip": "192.168.1.100"
    },
    "signature": "sha256=abc123..."
}
```

## SDK Examples

### Python SDK Example:
```python
import requests

class WorkshopSecurityAPI:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'token {api_key}:{api_secret}',
            'Content-Type': 'application/json'
        }
    
    def trigger_alert(self, alert_type, user_email, **kwargs):
        data = {
            'alert_type': alert_type,
            'user_email': user_email,
            **kwargs
        }
        response = requests.post(
            f'{self.base_url}/api/method/universal_workshop.user_management.security_alerts.trigger_security_alert',
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def get_session_status(self, user_email):
        response = requests.get(
            f'{self.base_url}/api/method/universal_workshop.user_management.session_manager.get_session_status',
            params={'user_email': user_email},
            headers=self.headers
        )
        return response.json()

# Usage
api = WorkshopSecurityAPI('https://workshop.local', 'api_key', 'api_secret')
alert = api.trigger_alert('suspicious_activity', 'user@workshop.com')
sessions = api.get_session_status('user@workshop.com')
```

### JavaScript SDK Example:
```javascript
class WorkshopSecurityAPI {
    constructor(baseUrl, apiKey, apiSecret) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `token ${apiKey}:${apiSecret}`,
            'Content-Type': 'application/json'
        };
    }
    
    async triggerAlert(alertType, userEmail, options = {}) {
        const response = await fetch(
            `${this.baseUrl}/api/method/universal_workshop.user_management.security_alerts.trigger_security_alert`,
            {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({
                    alert_type: alertType,
                    user_email: userEmail,
                    ...options
                })
            }
        );
        return response.json();
    }
    
    async getSessionStatus(userEmail) {
        const response = await fetch(
            `${this.baseUrl}/api/method/universal_workshop.user_management.session_manager.get_session_status?user_email=${userEmail}`,
            { headers: this.headers }
        );
        return response.json();
    }
}

// Usage
const api = new WorkshopSecurityAPI('https://workshop.local', 'api_key', 'api_secret');
const alert = await api.triggerAlert('suspicious_activity', 'user@workshop.com');
const sessions = await api.getSessionStatus('user@workshop.com');
```

---

*Last Updated: June 2024*
*Version: 2.0*
*API Version: v1* 