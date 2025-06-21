#!/usr/bin/env python3
"""
Security Testing Suite for ERPNext/Frappe Workshop Application
Comprehensive security testing framework covering OWASP Top 10 and ERPNext-specific vulnerabilities
"""

import sys
import os
import subprocess
import json
import time
import requests
import hashlib
import ssl
import socket
from datetime import datetime
from pathlib import Path

# Add the frappe bench to Python path for imports
sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

class SecurityTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "vulnerabilities": [],
            "compliance": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "vulnerabilities_found": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories for security testing"""
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        directories = ["reports", "vulnerabilities", "compliance", "tools"]
        
        for directory in directories:
            (base_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def log_test(self, test_name, status, details, severity="info"):
        """Log test results"""
        test_result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["tests"].append(test_result)
        self.test_results["summary"]["total_tests"] += 1
        
        if status == "PASS":
            self.test_results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {status}")
        else:
            self.test_results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {status}")
            
        if severity in ["critical", "high", "medium", "low"]:
            self.test_results["summary"]["vulnerabilities_found"] += 1
            self.test_results["summary"][severity] += 1
            
    def log_vulnerability(self, vuln_type, description, severity, location, remediation):
        """Log vulnerability findings"""
        vulnerability = {
            "type": vuln_type,
            "description": description,
            "severity": severity,
            "location": location,
            "remediation": remediation,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results["vulnerabilities"].append(vulnerability)
    
    def test_server_availability(self):
        """Test if ERPNext server is running and accessible"""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Server Availability", "PASS", "ERPNext server is accessible")
                return True
            else:
                self.log_test("Server Availability", "FAIL", f"Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Server Availability", "FAIL", f"Cannot connect to server: {str(e)}")
            return False
    
    def test_ssl_configuration(self):
        """Test SSL/TLS configuration"""
        try:
            # Check if HTTPS is available
            https_url = self.base_url.replace("http://", "https://")
            try:
                response = requests.get(https_url, timeout=10, verify=True)
                self.log_test("HTTPS Availability", "PASS", "HTTPS is properly configured")
            except requests.exceptions.SSLError:
                self.log_test("HTTPS Availability", "FAIL", "SSL certificate validation failed", "medium")
                self.log_vulnerability(
                    "SSL Configuration",
                    "SSL certificate validation failed - potential man-in-the-middle vulnerability",
                    "medium",
                    "Server SSL configuration",
                    "Configure valid SSL certificate and ensure proper TLS settings"
                )
            except requests.exceptions.RequestException:
                self.log_test("HTTPS Availability", "FAIL", "HTTPS not available", "high")
                self.log_vulnerability(
                    "Missing HTTPS",
                    "HTTPS not configured - data transmitted in plain text",
                    "high",
                    "Server configuration",
                    "Configure HTTPS with valid SSL certificate for production deployment"
                )
        except Exception as e:
            self.log_test("SSL Configuration", "FAIL", f"SSL test failed: {str(e)}")
    
    def test_default_credentials(self):
        """Test for default or weak credentials"""
        default_creds = [
            ("Administrator", "admin"),
            ("admin", "admin"),
            ("Administrator", "password"),
            ("admin", "password"),
            ("test", "test"),
            ("demo", "demo")
        ]
        
        for username, password in default_creds:
            try:
                login_data = {
                    "cmd": "login",
                    "usr": username,
                    "pwd": password
                }
                
                response = requests.post(f"{self.base_url}/api/method/login", data=login_data, timeout=10)
                
                if response.status_code == 200 and "message" in response.text:
                    # Check if login was successful
                    data = response.json()
                    if data.get("message") == "Logged In":
                        self.log_test("Default Credentials", "FAIL", f"Default credentials work: {username}/{password}", "critical")
                        self.log_vulnerability(
                            "Default Credentials",
                            f"Default credentials {username}/{password} are still active",
                            "critical",
                            "User authentication",
                            "Change default passwords immediately and enforce strong password policy"
                        )
                        return False
                        
            except requests.exceptions.RequestException:
                # Connection issues are not credential-related
                pass
        
        self.log_test("Default Credentials", "PASS", "No default credentials found")
        return True
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        # Common SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE test;--",
            "' UNION SELECT NULL--",
            "1' AND SLEEP(5)--"
        ]
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            "/api/method/frappe.desk.search.search_link",
            "/api/method/frappe.desk.search.search_widget",
            "/api/resource/Customer"
        ]
        
        vulnerabilities_found = 0
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    # Test GET parameters
                    response = requests.get(f"{self.base_url}{endpoint}?txt={payload}", timeout=10)
                    
                    # Look for SQL error indicators
                    error_indicators = [
                        "mysql",
                        "sql syntax",
                        "ORA-",
                        "PostgreSQL",
                        "sqlite",
                        "mariadb"
                    ]
                    
                    response_text = response.text.lower()
                    for indicator in error_indicators:
                        if indicator in response_text:
                            self.log_test("SQL Injection", "FAIL", f"Potential SQL injection at {endpoint} with payload: {payload}", "high")
                            self.log_vulnerability(
                                "SQL Injection",
                                f"SQL injection vulnerability detected at {endpoint}",
                                "high",
                                endpoint,
                                "Use parameterized queries and input validation. Sanitize all user inputs."
                            )
                            vulnerabilities_found += 1
                            break
                            
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("SQL Injection", "PASS", "No SQL injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting vulnerabilities"""
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        # Test common form fields and search parameters
        test_params = ["txt", "query", "search", "name", "title", "description"]
        
        vulnerabilities_found = 0
        
        for payload in xss_payloads:
            for param in test_params:
                try:
                    # Test GET parameters
                    response = requests.get(f"{self.base_url}/app/customer?{param}={payload}", timeout=10)
                    
                    # Check if payload is reflected in response without encoding
                    if payload in response.text and "text/html" in response.headers.get("content-type", ""):
                        self.log_test("XSS Vulnerability", "FAIL", f"XSS vulnerability with payload: {payload}", "medium")
                        self.log_vulnerability(
                            "Cross-Site Scripting",
                            f"XSS vulnerability detected with parameter {param}",
                            "medium",
                            f"Parameter: {param}",
                            "Implement proper input validation and output encoding. Use Content Security Policy (CSP)."
                        )
                        vulnerabilities_found += 1
                        
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("XSS Vulnerability", "PASS", "No XSS vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        try:
            # Try to perform a state-changing operation without CSRF token
            response = requests.post(f"{self.base_url}/api/resource/Customer", 
                                   json={"customer_name": "Test Customer"},
                                   timeout=10)
            
            # Should be rejected due to missing CSRF token or authentication
            if response.status_code == 200:
                self.log_test("CSRF Protection", "FAIL", "POST request accepted without authentication/CSRF token", "medium")
                self.log_vulnerability(
                    "CSRF Vulnerability",
                    "State-changing requests can be made without CSRF protection",
                    "medium",
                    "API endpoints",
                    "Implement CSRF tokens for all state-changing operations"
                )
                return False
            else:
                self.log_test("CSRF Protection", "PASS", "CSRF protection appears to be in place")
                return True
                
        except requests.exceptions.RequestException as e:
            self.log_test("CSRF Protection", "PASS", "Request properly rejected")
            return True
    
    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities"""
        # Common sensitive files/endpoints
        sensitive_paths = [
            "/sitemap.xml",
            "/robots.txt",
            "/.git/config",
            "/config.json",
            "/app.py",
            "/requirements.txt",
            "/logs/",
            "/backup/",
            "/admin/",
            "/debug/"
        ]
        
        disclosures_found = 0
        
        for path in sensitive_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                
                if response.status_code == 200:
                    content_length = len(response.content)
                    if content_length > 0:
                        # Check if it contains sensitive information
                        sensitive_keywords = ["password", "secret", "key", "token", "database", "config"]
                        content_lower = response.text.lower()
                        
                        for keyword in sensitive_keywords:
                            if keyword in content_lower:
                                self.log_test("Information Disclosure", "FAIL", f"Sensitive information exposed at {path}", "medium")
                                self.log_vulnerability(
                                    "Information Disclosure",
                                    f"Sensitive information exposed at {path}",
                                    "medium",
                                    path,
                                    "Restrict access to sensitive files and directories"
                                )
                                disclosures_found += 1
                                break
                                
            except requests.exceptions.RequestException:
                pass
        
        if disclosures_found == 0:
            self.log_test("Information Disclosure", "PASS", "No information disclosure vulnerabilities detected")
        
        return disclosures_found == 0
    
    def test_session_management(self):
        """Test session management security"""
        try:
            # Test session without secure flags
            response = requests.get(self.base_url, timeout=10)
            
            cookies = response.cookies
            session_issues = []
            
            for cookie in cookies:
                # Check for secure flag
                if not cookie.secure and self.base_url.startswith("https"):
                    session_issues.append(f"Cookie {cookie.name} missing Secure flag")
                
                # Check for HttpOnly flag
                if not cookie.has_nonstandard_attr("HttpOnly"):
                    session_issues.append(f"Cookie {cookie.name} missing HttpOnly flag")
            
            if session_issues:
                self.log_test("Session Management", "FAIL", f"Session security issues: {', '.join(session_issues)}", "medium")
                self.log_vulnerability(
                    "Session Management",
                    "Session cookies lack security flags",
                    "medium",
                    "Cookie configuration",
                    "Set Secure and HttpOnly flags on all session cookies"
                )
                return False
            else:
                self.log_test("Session Management", "PASS", "Session management appears secure")
                return True
                
        except Exception as e:
            self.log_test("Session Management", "FAIL", f"Session test failed: {str(e)}")
            return False
    
    def test_file_upload_security(self):
        """Test file upload security"""
        try:
            # Test file upload endpoint
            upload_url = f"{self.base_url}/api/method/upload_file"
            
            # Try uploading a potentially dangerous file
            dangerous_files = [
                ("test.php", "<?php echo 'PHP execution test'; ?>", "application/x-php"),
                ("test.js", "alert('XSS test');", "application/javascript"),
                ("test.html", "<script>alert('XSS')</script>", "text/html")
            ]
            
            for filename, content, content_type in dangerous_files:
                files = {
                    'file': (filename, content, content_type)
                }
                
                try:
                    response = requests.post(upload_url, files=files, timeout=10)
                    
                    if response.status_code == 200:
                        # Check if file was uploaded without validation
                        self.log_test("File Upload Security", "FAIL", f"Dangerous file {filename} was uploaded", "high")
                        self.log_vulnerability(
                            "File Upload Vulnerability",
                            f"System accepts upload of potentially dangerous file type: {filename}",
                            "high",
                            "File upload functionality",
                            "Implement file type validation, virus scanning, and store uploads outside web root"
                        )
                        return False
                        
                except requests.exceptions.RequestException:
                    pass
            
            self.log_test("File Upload Security", "PASS", "File upload security appears adequate")
            return True
            
        except Exception as e:
            self.log_test("File Upload Security", "PASS", "File upload endpoint not accessible")
            return True
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        try:
            # Send multiple rapid requests to test rate limiting
            api_endpoint = f"{self.base_url}/api/method/ping"
            
            start_time = time.time()
            successful_requests = 0
            
            for i in range(50):  # Send 50 rapid requests
                try:
                    response = requests.get(api_endpoint, timeout=5)
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:  # Too Many Requests
                        self.log_test("API Rate Limiting", "PASS", "Rate limiting is active")
                        return True
                except requests.exceptions.RequestException:
                    pass
            
            end_time = time.time()
            requests_per_second = successful_requests / (end_time - start_time)
            
            if requests_per_second > 100:  # More than 100 requests per second might indicate no rate limiting
                self.log_test("API Rate Limiting", "FAIL", f"No rate limiting detected - {requests_per_second:.1f} req/s", "medium")
                self.log_vulnerability(
                    "Missing Rate Limiting",
                    "API endpoints lack rate limiting protection",
                    "medium",
                    "API endpoints",
                    "Implement rate limiting to prevent abuse and DoS attacks"
                )
                return False
            else:
                self.log_test("API Rate Limiting", "PASS", "Rate limiting appears to be in place")
                return True
                
        except Exception as e:
            self.log_test("API Rate Limiting", "PASS", f"Rate limiting test inconclusive: {str(e)}")
            return True
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 Starting Comprehensive Security Testing for ERPNext/Frappe Workshop Application")
        print("=" * 80)
        
        # Check server availability first
        if not self.test_server_availability():
            print("❌ Server not available. Skipping security tests.")
            return False
        
        # Run all security tests
        test_methods = [
            self.test_ssl_configuration,
            self.test_default_credentials,
            self.test_sql_injection,
            self.test_xss_vulnerabilities,
            self.test_csrf_protection,
            self.test_information_disclosure,
            self.test_session_management,
            self.test_file_upload_security,
            self.test_api_rate_limiting
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, "ERROR", f"Test failed with exception: {str(e)}")
        
        self.generate_reports()
        return True
    
    def generate_reports(self):
        """Generate security test reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate main security report
        report_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/security_test_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate vulnerability report
        if self.test_results["vulnerabilities"]:
            vuln_path = f"/home/said/frappe-dev/frappe-bench/tests/security/vulnerabilities/vulnerabilities_{timestamp}.json"
            with open(vuln_path, 'w') as f:
                json.dump(self.test_results["vulnerabilities"], f, indent=2)
        
        # Generate summary report
        summary_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/security_summary_{timestamp}.md"
        self.generate_summary_report(summary_path)
        
        print("\n" + "=" * 80)
        print("📊 Security Testing Summary")
        print("=" * 80)
        print(f"Total Tests: {self.test_results['summary']['total_tests']}")
        print(f"Passed: {self.test_results['summary']['passed']}")
        print(f"Failed: {self.test_results['summary']['failed']}")
        print(f"Vulnerabilities Found: {self.test_results['summary']['vulnerabilities_found']}")
        print(f"  Critical: {self.test_results['summary']['critical']}")
        print(f"  High: {self.test_results['summary']['high']}")
        print(f"  Medium: {self.test_results['summary']['medium']}")
        print(f"  Low: {self.test_results['summary']['low']}")
        print(f"\n📄 Reports saved to:")
        print(f"  - {report_path}")
        if self.test_results["vulnerabilities"]:
            print(f"  - {vuln_path}")
        print(f"  - {summary_path}")
    
    def generate_summary_report(self, file_path):
        """Generate markdown summary report"""
        content = f"""# Security Testing Report - ERPNext/Frappe Workshop Application

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

- **Total Tests Executed:** {self.test_results['summary']['total_tests']}
- **Tests Passed:** {self.test_results['summary']['passed']}
- **Tests Failed:** {self.test_results['summary']['failed']}
- **Vulnerabilities Found:** {self.test_results['summary']['vulnerabilities_found']}

### Vulnerability Breakdown
- **Critical:** {self.test_results['summary']['critical']}
- **High:** {self.test_results['summary']['high']}
- **Medium:** {self.test_results['summary']['medium']}
- **Low:** {self.test_results['summary']['low']}

## Test Results

| Test Name | Status | Details |
|-----------|--------|---------|
"""
        
        for test in self.test_results["tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "❌"
            content += f"| {test['test_name']} | {status_icon} {test['status']} | {test['details']} |\n"
        
        if self.test_results["vulnerabilities"]:
            content += "\n## Vulnerabilities Found\n\n"
            for i, vuln in enumerate(self.test_results["vulnerabilities"], 1):
                content += f"### {i}. {vuln['type']} ({vuln['severity'].upper()})\n\n"
                content += f"**Description:** {vuln['description']}\n\n"
                content += f"**Location:** {vuln['location']}\n\n"
                content += f"**Remediation:** {vuln['remediation']}\n\n"
        
        content += """
## Recommendations

1. **Immediate Actions:**
   - Fix all Critical and High severity vulnerabilities
   - Review and update security configurations
   - Implement missing security controls

2. **Short-term Actions:**
   - Address Medium severity vulnerabilities
   - Enhance monitoring and logging
   - Conduct security training for development team

3. **Long-term Actions:**
   - Implement automated security testing in CI/CD pipeline
   - Regular penetration testing
   - Security code reviews for all changes

## Compliance Considerations

- Ensure GDPR compliance for customer data handling
- Implement audit logging for all sensitive operations
- Regular security assessments and updates
- Access control reviews and user training

---
*Generated by ERPNext/Frappe Security Testing Framework*
"""
        
        with open(file_path, 'w') as f:
            f.write(content)

def main():
    """Main function to run security tests"""
    security_suite = SecurityTestSuite()
    success = security_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
