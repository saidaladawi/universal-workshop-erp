#!/usr/bin/env python3
"""
Security Validation and Testing Framework
Validates security controls and generates comprehensive security report
"""

import sys
import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

def run_security_test(test_script, test_name):
    """Run individual security test script"""
    print(f"\n🔍 Running {test_name}...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, test_script
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {test_name} completed successfully")
            return True, result.stdout, result.stderr
        else:
            print(f"❌ {test_name} failed with return code {result.returncode}")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} timed out after 5 minutes")
        return False, "", "Test timed out"
    except Exception as e:
        print(f"💥 {test_name} failed with exception: {str(e)}")
        return False, "", str(e)

def validate_security_framework():
    """Validate security testing framework installation"""
    print("🔧 Validating Security Testing Framework...")
    
    # Check required Python packages
    required_packages = [
        "requests", "jwt", "psutil"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages, check=True)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install required packages")
            return False
    
    # Validate test framework structure
    security_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
    required_files = [
        "run_security_tests.py",
        "test_authentication.py", 
        "test_injection.py",
        "test_api_security.py",
        "test_zap_scanner.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not (security_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing security test files: {', '.join(missing_files)}")
        return False
    
    print("✅ Security testing framework validated")
    return True

def run_comprehensive_security_tests():
    """Run all security tests"""
    print("\n🛡️ Starting Comprehensive Security Testing Suite")
    print("=" * 70)
    
    security_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
    
    # Security test configuration
    security_tests = [
        (security_dir / "run_security_tests.py", "Core Security Tests"),
        (security_dir / "test_authentication.py", "Authentication & Authorization"),
        (security_dir / "test_injection.py", "Injection & Input Validation"),
        (security_dir / "test_api_security.py", "API Security Assessment")
    ]
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {
            "total_tests": len(security_tests),
            "passed": 0,
            "failed": 0
        }
    }
    
    # Run each security test
    for test_script, test_name in security_tests:
        if test_script.exists():
            success, stdout, stderr = run_security_test(str(test_script), test_name)
            
            test_result = {
                "name": test_name,
                "script": str(test_script),
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            test_results["tests"].append(test_result)
            
            if success:
                test_results["summary"]["passed"] += 1
            else:
                test_results["summary"]["failed"] += 1
        else:
            print(f"⚠️ Test script not found: {test_script}")
            test_results["summary"]["failed"] += 1
    
    # Save comprehensive test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = security_dir / "reports" / f"comprehensive_security_test_{timestamp}.json"
    
    with open(results_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    return test_results, results_path

def generate_security_summary_report(test_results, results_path):
    """Generate security summary report"""
    print("\n📊 Generating Security Summary Report...")
    
    security_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create summary report
    summary_content = f"""# ERPNext/Frappe Workshop Security Assessment Report

**Assessment Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Target Application:** ERPNext/Frappe Workshop Management System
**Assessment Type:** Comprehensive Security Testing

## Executive Summary

This report provides a comprehensive security assessment of the ERPNext/Frappe Workshop Management System, covering authentication, authorization, input validation, API security, and vulnerability scanning.

### Test Results Overview

- **Total Security Tests:** {test_results['summary']['total_tests']}
- **Tests Passed:** {test_results['summary']['passed']}
- **Tests Failed:** {test_results['summary']['failed']}
- **Success Rate:** {(test_results['summary']['passed'] / test_results['summary']['total_tests'] * 100):.1f}%

## Security Test Categories

### 1. Core Security Tests
**Purpose:** Basic security controls validation
- SSL/TLS configuration
- Default credentials testing
- Information disclosure
- Session management
- File upload security

### 2. Authentication & Authorization
**Purpose:** Identity and access management validation
- Password policy enforcement
- Brute force protection
- Session timeout configuration
- JWT security
- Role-based access control (RBAC)
- Multi-factor authentication availability

### 3. Injection & Input Validation
**Purpose:** Input validation and injection vulnerability testing
- SQL injection testing (basic, error-based, time-based)
- NoSQL injection testing
- Cross-site scripting (XSS) prevention
- File inclusion vulnerabilities
- Command injection testing

### 4. API Security Assessment
**Purpose:** REST API security validation
- API authentication requirements
- Authorization controls
- Rate limiting implementation
- Input validation for API endpoints
- Security headers configuration
- CORS policy validation

## Detailed Test Results

"""
    
    for test in test_results["tests"]:
        summary_content += f"""
### {test['name']}
**Status:** {'✅ PASSED' if test['success'] else '❌ FAILED'}
**Script:** {test['script']}
**Execution Time:** {test['timestamp']}

"""
        if not test['success'] and test['stderr']:
            summary_content += f"""
**Error Details:**
```
{test['stderr'][:500]}{'...' if len(test['stderr']) > 500 else ''}
```

"""
    
    # Add security recommendations
    summary_content += """
## Security Recommendations

### Immediate Actions (Critical Priority)
1. **Fix Critical Vulnerabilities:** Address any critical or high-severity vulnerabilities identified
2. **Enable HTTPS:** Ensure all production traffic uses HTTPS with valid certificates
3. **Change Default Credentials:** Verify no default passwords remain active
4. **Input Validation:** Implement comprehensive input validation for all user inputs

### Short-term Actions (High Priority)
1. **Implement Rate Limiting:** Add API rate limiting to prevent abuse
2. **Security Headers:** Configure security headers (CSP, HSTS, X-Frame-Options)
3. **Session Security:** Implement secure session management with proper timeouts
4. **Error Handling:** Ensure error messages don't leak sensitive information

### Long-term Actions (Medium Priority)
1. **Security Monitoring:** Implement security monitoring and alerting
2. **Regular Testing:** Schedule quarterly security assessments
3. **Security Training:** Provide security training for development team
4. **Penetration Testing:** Conduct annual professional penetration testing

### Compliance Considerations
1. **Data Protection:** Ensure compliance with GDPR/CCPA for customer data
2. **Audit Logging:** Maintain comprehensive audit logs for all sensitive operations
3. **Access Reviews:** Conduct regular access control reviews
4. **Backup Security:** Ensure backup data is encrypted and access-controlled

## Technical Security Controls

### Authentication Controls
- Multi-factor authentication support
- Strong password policy enforcement
- Account lockout mechanisms
- Session timeout configuration

### Authorization Controls
- Role-based access control (RBAC)
- Principle of least privilege
- Resource-level permissions
- API endpoint protection

### Data Protection
- Encryption at rest for sensitive data
- TLS encryption for data in transit
- Secure key management
- PII data handling procedures

### Infrastructure Security
- Web application firewall (WAF) configuration
- Network segmentation
- Regular security updates
- Vulnerability management

## Conclusion

The security assessment provides a comprehensive evaluation of the ERPNext/Frappe Workshop Management System's security posture. Immediate attention should be given to any critical or high-severity findings, with a focus on implementing defense-in-depth security controls.

Regular security testing and monitoring should be established to maintain security throughout the application lifecycle.

---
**Report Generated By:** ERPNext/Frappe Security Testing Framework
**Contact:** Security Team
**Next Assessment:** {(datetime.now().replace(month=datetime.now().month + 3) if datetime.now().month <= 9 else datetime.now().replace(year=datetime.now().year + 1, month=datetime.now().month - 9)).strftime("%Y-%m-%d")}
"""
    
    # Save summary report
    summary_path = security_dir / "reports" / f"security_assessment_report_{timestamp}.md"
    with open(summary_path, 'w') as f:
        f.write(summary_content)
    
    print(f"📄 Security assessment report saved: {summary_path}")
    
    return summary_path

def check_erpnext_server():
    """Check if ERPNext server is running"""
    print("🌐 Checking ERPNext Server Status...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=10)
        if response.status_code == 200:
            print("✅ ERPNext server is running")
            return True
        else:
            print(f"⚠️ ERPNext server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERPNext server not accessible: {str(e)}")
        print("   Start the server with: bench start")
        return False

def main():
    """Main security validation function"""
    print("🔒 ERPNext/Frappe Security Testing Framework Validation")
    print("=" * 60)
    
    # Validate framework
    if not validate_security_framework():
        print("❌ Security framework validation failed")
        return 1
    
    # Check if ERPNext server is running
    server_running = check_erpnext_server()
    if not server_running:
        print("⚠️ ERPNext server not running - some tests may be skipped")
    
    # Run comprehensive security tests
    test_results, results_path = run_comprehensive_security_tests()
    
    # Generate summary report
    summary_path = generate_security_summary_report(test_results, results_path)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🔒 Security Testing Framework Validation Complete")
    print("=" * 60)
    print(f"Tests Passed: {test_results['summary']['passed']}")
    print(f"Tests Failed: {test_results['summary']['failed']}")
    print(f"Success Rate: {(test_results['summary']['passed'] / test_results['summary']['total_tests'] * 100):.1f}%")
    print(f"\n📊 Detailed Results: {results_path}")
    print(f"📄 Summary Report: {summary_path}")
    
    if test_results['summary']['failed'] == 0:
        print("\n✅ All security tests completed successfully!")
        return 0
    else:
        print(f"\n⚠️ {test_results['summary']['failed']} security test(s) failed")
        print("   Review the detailed results and address any issues")
        return 1

if __name__ == "__main__":
    exit(main())
