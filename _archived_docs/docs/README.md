# Universal Workshop ERP - Security Framework Documentation

## Overview

This documentation covers the comprehensive User Management & Security Framework implemented in Universal Workshop ERP v2.0. The framework provides enterprise-grade security features specifically designed for automotive workshop environments in Oman.

## Documentation Structure

### User Guides
- **[Arabic User Guide](ar/user-management-security-guide.md)** - Complete guide in Arabic for local users
- **[English User Guide](en/user-management-security-guide.md)** - Complete guide in English for international users

### Technical Documentation
- **[API Reference](api/security-api-reference.md)** - Comprehensive API documentation for developers
- **[Compliance Checklist](compliance/security-compliance-checklist.md)** - Security and regulatory compliance guidelines

## Quick Start Guide

### For Administrators
1. Review the [Administrator Usage Guide](en/user-management-security-guide.md#administrator-usage-guide)
2. Complete the [Initial System Setup](en/user-management-security-guide.md#initial-system-setup)
3. Configure security policies using the [Compliance Checklist](compliance/security-compliance-checklist.md)

### For Developers
1. Review the [Developer Guide](en/user-management-security-guide.md#developer-guide)
2. Explore the [API Reference](api/security-api-reference.md)
3. Implement custom security features following the provided examples

### For End Users
1. Read the appropriate user guide ([Arabic](ar/user-management-security-guide.md) or [English](en/user-management-security-guide.md))
2. Learn about [Multi-Factor Authentication setup](en/user-management-security-guide.md#multi-factor-authentication-mfa)
3. Understand [Security Best Practices](en/user-management-security-guide.md#security-best-practices)

## Security Framework Components

### 1. Role and Permission Model
- Granular role-based access control
- Workshop-specific role definitions
- Dynamic permission evaluation
- Field and row-level security

### 2. Multi-Factor Authentication (MFA)
- TOTP authenticator app support
- SMS and WhatsApp verification
- Backup codes for recovery
- Admin management interface

### 3. Advanced Session Management
- Configurable session policies
- Device and browser tracking
- Concurrent session limits
- Real-time session monitoring

### 4. Security Dashboard
- Real-time security metrics
- Alert management interface
- User activity monitoring
- Compliance reporting

### 5. Extended Audit Trail
- Comprehensive event logging
- Tamper-evident audit records
- Compliance-ready reports
- Real-time activity tracking

### 6. Security Alerts and Notifications
- Threshold-based alerting
- Multi-channel notifications
- Escalation policies
- Alert resolution workflow

## Key Features

### Arabic Localization
- Full RTL (Right-to-Left) interface support
- Bilingual documentation (Arabic/English)
- Cultural adaptation for Oman market
- Arabic text handling and validation

### Compliance Ready
- Oman Data Protection Law compliance
- ISO 27001 security standards
- Financial regulations compliance
- Automotive industry standards

### Enterprise Security
- Advanced threat detection
- Real-time monitoring
- Incident response automation
- Comprehensive audit trails

### Developer Friendly
- RESTful API endpoints
- Comprehensive SDK examples
- Webhook integrations
- Extensive documentation

## Installation and Setup

### Prerequisites
- ERPNext v15.65.2 or higher
- Universal Workshop ERP v2.0
- Python 3.8+ with required packages
- MariaDB/MySQL database
- Redis for caching

### Installation Steps
1. Install the Universal Workshop app
2. Run database migrations
3. Configure security settings
4. Setup user roles and permissions
5. Enable MFA for critical users
6. Configure monitoring and alerts

### Configuration
```bash
# Initialize security framework
bench --site universal.local execute universal_workshop.user_management.setup_roles

# Configure alert settings
bench --site universal.local execute universal_workshop.user_management.setup_alerts

# Enable audit logging
bench --site universal.local execute universal_workshop.user_management.setup_audit_trail
```

## API Usage Examples

### Python
```python
from universal_workshop_api import SecurityAPI

# Initialize API client
api = SecurityAPI('https://workshop.local', 'api_key', 'api_secret')

# Trigger security alert
alert = api.trigger_alert('suspicious_activity', 'user@workshop.com')

# Get user sessions
sessions = api.get_session_status('user@workshop.com')

# Log audit event
audit = api.log_audit_event('permission_granted', 'medium', 'user@workshop.com', 'Access granted to reports')
```

### JavaScript
```javascript
// Trigger security alert
frappe.call({
    method: 'universal_workshop.user_management.security_alerts.trigger_security_alert',
    args: {
        alert_type: 'failed_login',
        user_email: 'user@workshop.com',
        source_ip: '192.168.1.100'
    },
    callback: function(r) {
        console.log('Alert triggered:', r.message);
    }
});
```

## Security Best Practices

### Password Policy
- Minimum 8 characters with complexity requirements
- Regular password changes (90 days)
- No password reuse (last 12 passwords)
- Strong password enforcement

### MFA Implementation
- Enable for all administrative users
- Use authenticator apps over SMS when possible
- Regular backup code renewal
- Monitor MFA failure alerts

### Session Security
- Appropriate timeout settings (15-30 minutes idle)
- Device tracking and monitoring
- Concurrent session limits
- Regular session audits

### Access Control
- Principle of least privilege
- Regular permission reviews
- Role-based access control
- Separation of duties

## Monitoring and Alerting

### Key Metrics to Monitor
- Failed login attempts
- Permission changes
- Session anomalies
- MFA failures
- Suspicious activities

### Alert Thresholds
- Failed Login: 3 attempts in 10 minutes
- Multiple Failed Logins: 5 attempts in 15 minutes
- Permission Changes: Immediate alert
- MFA Disabled: Critical alert
- Suspicious Activity: 3 events in 60 minutes

### Escalation Policies
1. **Workshop Supervisor**: Standard alerts via email
2. **Workshop Manager**: Medium alerts via email + SMS
3. **System Manager**: Critical alerts via all channels
4. **Emergency**: Immediate notification via all channels

## Compliance and Auditing

### Regular Reviews
- **Daily**: Security dashboard and critical alerts
- **Weekly**: User permissions and access logs
- **Monthly**: Comprehensive security review
- **Quarterly**: Compliance audit and risk assessment
- **Annually**: Full security assessment and strategy review

### Audit Requirements
- Comprehensive event logging
- Tamper-evident audit trails
- Regular audit log reviews
- Compliance reporting
- Incident documentation

### Regulatory Compliance
- Oman Data Protection Law
- ISO 27001 Security Standards
- Financial Regulations
- Industry Standards

## Troubleshooting

### Common Issues
- **Login failures**: Check credentials, MFA settings, account status
- **Session timeouts**: Verify timeout settings, network connectivity
- **Permission errors**: Review role assignments, custom permissions
- **Alert fatigue**: Adjust thresholds, review escalation policies

### Support Channels
- **Documentation**: This comprehensive guide
- **Technical Support**: support@universal-workshop.om
- **Emergency**: +968 24 123456
- **Community**: GitHub issues and discussions

## Contributing

### Documentation Updates
- Follow markdown standards
- Include both Arabic and English versions
- Test all code examples
- Update API references

### Security Improvements
- Follow secure coding practices
- Include comprehensive tests
- Document security implications
- Review with security team

## License and Legal

### Software License
Universal Workshop ERP is licensed under the MIT License. See LICENSE file for details.

### Security Compliance
This framework is designed to meet:
- Oman Data Protection Law requirements
- ISO 27001 security standards
- International best practices
- Industry-specific regulations

### Disclaimer
While this framework implements comprehensive security measures, organizations are responsible for:
- Proper configuration and maintenance
- Regular security assessments
- Compliance with local regulations
- Incident response procedures

## Version History

### v2.0 (June 2024)
- Complete security framework implementation
- Multi-factor authentication
- Advanced session management
- Security alerts and notifications
- Comprehensive audit trail
- Arabic localization
- Compliance ready features

### v1.0 (Initial Release)
- Basic user management
- Role-based permissions
- Simple audit logging

## Contact Information

### Development Team
- **Lead Developer**: Eng. Saeed Al-Adawi
- **Security Architect**: Security Team
- **Documentation**: Technical Writers

### Support
- **Email**: support@universal-workshop.om
- **Phone**: +968 24 123456
- **Website**: https://universal-workshop.om
- **Documentation**: https://docs.universal-workshop.om

### Emergency Contacts
- **Security Incidents**: security@universal-workshop.om
- **System Outages**: operations@universal-workshop.om
- **Legal Issues**: legal@universal-workshop.om

---

*This documentation is maintained by the Universal Workshop ERP development team and is updated regularly to reflect the latest features and best practices.*

*Last Updated: June 2024*
*Version: 2.0*
*Language: English/العربية* 