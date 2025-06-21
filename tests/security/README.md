# Security Testing Framework for ERPNext/Frappe Workshop Application

## Overview
Comprehensive security testing suite for ERPNext/Frappe applications focusing on OWASP Top 10 vulnerabilities, authentication, authorization, data protection, and compliance requirements.

## Test Categories

### 1. Automated Vulnerability Scanning
- OWASP ZAP integration for web application scanning
- SQLMap for SQL injection testing
- Custom security validators for ERPNext-specific vulnerabilities

### 2. Authentication & Authorization Testing
- Password policy validation
- Session management security
- JWT token security
- Role-based access control (RBAC) testing
- Multi-factor authentication validation

### 3. Input Validation & Injection Testing
- SQL injection testing across all DocTypes
- XSS (Cross-Site Scripting) prevention validation
- CSRF (Cross-Site Request Forgery) protection
- File upload security testing
- Barcode input validation

### 4. API Security Assessment
- REST API endpoint enumeration
- API authentication and rate limiting
- Input validation for API endpoints
- WebSocket security (for real-time features)

### 5. Data Protection & Encryption
- Encryption at rest validation
- TLS/SSL configuration testing
- Sensitive data exposure assessment
- PII (Personally Identifiable Information) protection

### 6. Business Logic Security
- Workshop-specific workflow security
- Inventory access controls
- Financial data protection
- License management security

### 7. Compliance Testing
- GDPR compliance validation
- Audit logging verification
- Data retention policy validation
- Access control compliance

## Tools Integration
- OWASP ZAP for automated scanning
- Custom Python scripts for ERPNext-specific tests
- SQLMap integration for injection testing
- SSL Labs integration for TLS assessment

## Execution
Run all security tests:
```bash
python tests/security/run_security_tests.py
```

Run specific test category:
```bash
python tests/security/test_authentication.py
python tests/security/test_injection.py
python tests/security/test_api_security.py
```

## Reporting
Security test results are saved to:
- `/tests/security/reports/` - Detailed test reports
- `/tests/security/vulnerabilities/` - Vulnerability assessment reports
- `/tests/security/compliance/` - Compliance validation reports

## Remediation
Each test includes:
- Vulnerability description
- Risk assessment (Critical/High/Medium/Low)
- Remediation steps
- Code examples for fixes
- Compliance requirements

## Continuous Security
- Integration with CI/CD pipeline
- Automated security regression testing
- Regular dependency vulnerability scanning
- Security monitoring and alerting
