# User Management & Security Framework Guide - Universal Workshop ERP

## Overview

The User Management & Security Framework in Universal Workshop ERP provides an advanced security and access control system designed specifically for automotive workshop environments in Oman.

## Core Components

### 1. Role and Permission Model

#### Available Roles:
- **Workshop Manager**: Full access to all operations
- **Workshop Supervisor**: Daily operations and technician management
- **Service Advisor**: Customer interaction and service requests
- **Parts Manager**: Inventory and parts ordering management
- **Technician**: Maintenance and repair work execution
- **Financial Staff**: Invoice and payment management

#### Permission Levels:
- **Read**: View data only
- **Write**: Modify existing data
- **Create**: Create new records
- **Delete**: Delete records
- **Submit**: Confirm transactions
- **Cancel**: Cancel confirmed transactions

### 2. Custom Permission Engine

#### Advanced Features:
- **Dynamic Permissions**: Context and state-dependent access
- **Row-Level Permissions**: Granular data control
- **Field-Level Permissions**: Hide or protect specific fields
- **Custom Conditions**: Complex access rules

#### Usage Examples:
```python
# Example: Technician can only see work orders assigned to them
if user_role == "Technician":
    filters.update({"assigned_technician": user.email})

# Example: Hide cost information from technicians
if user_role == "Technician":
    hide_fields = ["cost_price", "profit_margin"]
```

### 3. Security Dashboard

#### Key Metrics:
- **Active Users**: Currently logged-in users count
- **Failed Login Attempts**: Last 24 hours
- **Permission Changes**: Recent modifications
- **Security Alerts**: Suspicious events
- **User Sessions**: Activity monitoring

#### Available Reports:
- Daily user activity report
- Monthly permission changes report
- Security events report
- System usage report

### 4. Multi-Factor Authentication (MFA)

#### Supported Authentication Methods:
- **Authenticator Apps**: Google Authenticator, Microsoft Authenticator
- **SMS Messages**: Verification code via phone
- **WhatsApp**: Verification code via WhatsApp
- **Email**: Verification code via email

#### Setting up MFA for Users:
1. Navigate to User settings page
2. Click "Enable Multi-Factor Authentication"
3. Choose preferred authentication method
4. Scan QR code with authenticator app
5. Enter verification code to confirm
6. Save backup codes

#### Backup Codes:
- 10 backup codes are generated
- Each code can only be used once
- Store them in a secure location
- New codes can be generated when needed

### 5. Advanced Session Management

#### Session Policies:
- **Idle Timeout**: 15-30 minutes of inactivity
- **Maximum Sessions**: 1-5 concurrent sessions
- **Single Session Only**: For sensitive roles
- **Device Monitoring**: Browser and OS tracking

#### Session Monitoring:
```javascript
// Display user's active sessions
frappe.call({
    method: 'universal_workshop.user_management.session_manager.get_session_status',
    args: { user_email: 'user@workshop.com' },
    callback: function(r) {
        console.log('Active Sessions:', r.message);
    }
});
```

#### Session Revocation:
- Revoke specific session
- Revoke all user sessions
- Automatically revoke expired sessions

### 6. Extended Audit Trail

#### Logged Events:
- **Login Events**: Success, failure, logout
- **MFA Events**: Enable, disable, verification failure
- **Session Events**: Create, expire, revoke
- **Role Changes**: Assign, unassign
- **Permission Grants**: Add, remove, modify
- **Suspicious Activities**: Unauthorized attempts

#### Audit Log Structure:
```json
{
    "event_id": "SEC-2024-001234",
    "event_type": "login_failed",
    "severity": "medium",
    "timestamp": "2024-06-23T10:30:00Z",
    "user_email": "user@workshop.com",
    "description": "Failed login attempt",
    "details": {
        "ip_address": "192.168.1.100",
        "user_agent": "Chrome/91.0",
        "failure_reason": "Invalid password"
    }
}
```

### 7. Security Alerts and Notifications

#### Alert Types:
- **Failed Login**: 3 attempts in 10 minutes
- **Multiple Failed Logins**: 5 attempts in 15 minutes
- **Permission Changes**: Any role modifications
- **MFA Disabled**: Immediate alert
- **Suspicious Activity**: 3 events in 60 minutes

#### Notification Channels:
- **Email**: For standard alerts
- **SMS**: For urgent alerts
- **WhatsApp**: For critical alerts
- **In-App**: For immediate information

#### Escalation Policies:
1. **Workshop Supervisor**: Standard alerts
2. **Workshop Manager**: Medium alerts
3. **System Manager**: Critical alerts
4. **Emergency**: All channels

## Administrator Usage Guide

### Initial System Setup

#### 1. Create Roles:
```bash
# Run role setup script
bench --site universal.local execute universal_workshop.user_management.setup_roles
```

#### 2. Configure Security Policies:
1. Navigate to "Security Alert Settings"
2. Enable required notification channels
3. Adjust alert thresholds as needed
4. Save settings

#### 3. Setup Users:
1. Create user accounts
2. Assign appropriate roles
3. Enable MFA for sensitive roles
4. Configure session policies

### Daily User Management

#### Adding a New User:
1. Go to "User List"
2. Click "New"
3. Fill in basic information
4. Select appropriate roles
5. Enable MFA if required
6. Save user

#### Modifying User Permissions:
1. Open user page
2. Navigate to "Roles" section
3. Add or remove roles
4. Save changes
5. Check audit log

#### Monitoring Activity:
1. Open security dashboard
2. Review recent alerts
3. Check active sessions
4. Review audit log

## Developer Guide

### Adding Custom Permissions

#### Example: Conditional Permission
```python
# In permission_hooks.py file
def custom_permission_check(doc, user, permission_type):
    """Custom permission check"""
    if doc.doctype == "Work Order":
        # Technician can only see work orders assigned to them
        if frappe.get_roles(user) == ["Technician"]:
            return doc.assigned_technician == user
    return True
```

#### Logging Event to Audit Trail:
```python
from universal_workshop.user_management.audit_trail_extension import log_audit_event

# Log security event
log_audit_event(
    event_type="role_assigned",
    severity="medium",
    user_email=user.email,
    description=f"Role {role_name} assigned to user",
    details={
        "role_name": role_name,
        "assigned_by": frappe.session.user,
        "timestamp": frappe.utils.now()
    }
)
```

### Adding New Security Alert:
```python
from universal_workshop.user_management.security_alerts import get_security_alerts_manager

# Send security alert
manager = get_security_alerts_manager()
manager.check_and_trigger_alerts(
    event_type="suspicious_activity",
    user_email=user.email,
    source_ip=frappe.local.request_ip,
    details={
        "activity_type": "unusual_access_pattern",
        "description": "Unusual access from new location"
    }
)
```

## API Reference

### User Management APIs

#### Get User Sessions:
```javascript
frappe.call({
    method: 'universal_workshop.user_management.session_manager.get_session_status',
    args: {
        user_email: 'user@workshop.com'
    },
    callback: function(r) {
        if (r.message) {
            console.log('Sessions:', r.message);
        }
    }
});
```

#### Trigger Security Alert:
```javascript
frappe.call({
    method: 'universal_workshop.user_management.security_alerts.trigger_security_alert',
    args: {
        alert_type: 'suspicious_activity',
        user_email: 'user@workshop.com',
        source_ip: '192.168.1.100',
        details: JSON.stringify({
            activity: 'unusual_access',
            description: 'Access from new device'
        })
    },
    callback: function(r) {
        console.log('Alert triggered:', r.message);
    }
});
```

#### Log Audit Event:
```javascript
frappe.call({
    method: 'universal_workshop.user_management.audit_trail_extension.log_audit_event',
    args: {
        event_type: 'permission_granted',
        severity: 'medium',
        user_email: 'user@workshop.com',
        description: 'Permission granted to access reports',
        details: JSON.stringify({
            permission_type: 'read',
            doctype: 'Report',
            granted_by: frappe.session.user
        })
    }
});
```

### Security Dashboard APIs

#### Get Security Summary:
```javascript
frappe.call({
    method: 'universal_workshop.user_management.security_alerts.get_security_alerts_summary',
    args: {
        days: 7
    },
    callback: function(r) {
        if (r.message) {
            console.log('Security Summary:', r.message);
        }
    }
});
```

#### Get Audit Summary:
```javascript
frappe.call({
    method: 'universal_workshop.user_management.audit_trail_extension.get_audit_summary',
    args: {
        days: 30,
        event_types: ['login_failed', 'permission_change']
    },
    callback: function(r) {
        console.log('Audit Summary:', r.message);
    }
});
```

## Compliance and Auditing

### Compliance Requirements:
- **Oman Data Protection Law**: Encryption of sensitive data
- **International Security Standards**: ISO 27001
- **Audit Requirements**: Comprehensive audit logs
- **Data Retention**: 7 years for financial records

### Monthly Security Checklist:
- [ ] Review audit logs
- [ ] Check security alerts
- [ ] Update passwords
- [ ] Review user permissions
- [ ] Check active sessions
- [ ] Update security policies
- [ ] Test backup system
- [ ] Review MFA settings

### Compliance Reports:
- Monthly user activity report
- Quarterly security events report
- Annual permission review report
- Annual security testing report

## Database Schema

### Security Alert Log Table:
```sql
CREATE TABLE `tabSecurity Alert Log` (
    `name` varchar(140) NOT NULL,
    `alert_id` varchar(140) NOT NULL,
    `alert_type` varchar(140) NOT NULL,
    `severity` varchar(140) NOT NULL,
    `timestamp` datetime NOT NULL,
    `user_email` varchar(140) NOT NULL,
    `source_ip` varchar(140),
    `description` text,
    `details` json,
    `escalation_level` varchar(140),
    `notifications_sent` json,
    `is_resolved` int(1) DEFAULT 0,
    `resolved_by` varchar(140),
    `resolved_at` datetime,
    `resolution_notes` text,
    PRIMARY KEY (`name`),
    UNIQUE KEY `alert_id` (`alert_id`),
    KEY `idx_user_email` (`user_email`),
    KEY `idx_timestamp` (`timestamp`),
    KEY `idx_alert_type` (`alert_type`)
);
```

### Security Audit Log Table:
```sql
CREATE TABLE `tabSecurity Audit Log` (
    `name` varchar(140) NOT NULL,
    `event_id` varchar(140) NOT NULL,
    `event_type` varchar(140) NOT NULL,
    `severity` varchar(140) NOT NULL,
    `timestamp` datetime NOT NULL,
    `user_email` varchar(140) NOT NULL,
    `description` text,
    `details` json,
    PRIMARY KEY (`name`),
    UNIQUE KEY `event_id` (`event_id`),
    KEY `idx_user_email` (`user_email`),
    KEY `idx_timestamp` (`timestamp`),
    KEY `idx_event_type` (`event_type`)
);
```

### Workshop User Session Table:
```sql
CREATE TABLE `tabWorkshop User Session` (
    `name` varchar(140) NOT NULL,
    `user_email` varchar(140) NOT NULL,
    `session_id` varchar(140) NOT NULL,
    `device_info` json,
    `ip_address` varchar(140),
    `login_time` datetime NOT NULL,
    `last_activity` datetime,
    `expiry_time` datetime,
    `is_active` int(1) DEFAULT 1,
    `revocation_reason` varchar(140),
    PRIMARY KEY (`name`),
    UNIQUE KEY `session_id` (`session_id`),
    KEY `idx_user_email` (`user_email`),
    KEY `idx_is_active` (`is_active`)
);
```

## Technical Support

### Common Errors and Solutions:

#### Error: "Login Failed"
**Solution:**
1. Check password
2. Verify account is enabled
3. Check MFA settings
4. Review audit log

#### Error: "Session Expired"
**Solution:**
1. Log in again
2. Check session timeout settings
3. Verify internet connection
4. Clear browser cache

#### Error: "Insufficient Permissions"
**Solution:**
1. Check assigned roles
2. Review role permissions
3. Contact system administrator
4. Check custom permissions

#### Error: "MFA Code Invalid"
**Solution:**
1. Check time synchronization
2. Generate new code
3. Use backup code
4. Contact administrator

### Performance Optimization:

#### Database Optimization:
```sql
-- Add indexes for better query performance
ALTER TABLE `tabSecurity Alert Log` ADD INDEX idx_severity_timestamp (severity, timestamp);
ALTER TABLE `tabSecurity Audit Log` ADD INDEX idx_event_type_timestamp (event_type, timestamp);
ALTER TABLE `tabWorkshop User Session` ADD INDEX idx_user_active (user_email, is_active);
```

#### Cache Configuration:
```python
# Redis cache configuration for session data
CACHE_CONFIG = {
    'session_cache_ttl': 3600,  # 1 hour
    'alert_cache_ttl': 300,     # 5 minutes
    'audit_cache_ttl': 1800     # 30 minutes
}
```

### Contact Information:
- **Technical Support**: support@universal-workshop.om
- **Emergency**: +968 24 123456
- **Documentation**: docs.universal-workshop.om
- **Training**: training@universal-workshop.om

## Security Best Practices

### Password Policy:
- Minimum 8 characters
- Include uppercase, lowercase, numbers, symbols
- No common dictionary words
- Change every 90 days
- No password reuse (last 12 passwords)

### MFA Recommendations:
- Enable for all administrative roles
- Use authenticator apps over SMS when possible
- Regularly review and update backup codes
- Monitor MFA failure alerts

### Session Security:
- Use HTTPS for all connections
- Set appropriate session timeouts
- Monitor concurrent sessions
- Log all session activities

### Network Security:
- Implement IP whitelisting for admin access
- Use VPN for remote access
- Monitor failed connection attempts
- Regular security assessments

---

*Last Updated: June 2024*
*Version: 2.0*
*Language: English* 