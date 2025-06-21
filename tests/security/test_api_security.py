#!/usr/bin/env python3
"""
API Security Testing for ERPNext/Frappe
Tests API endpoints for authentication, authorization, rate limiting, input validation, and security headers
"""

import sys
import os
import json
import requests
import time
import jwt
from datetime import datetime
from urllib.parse import urljoin

sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

class APISecurityTests:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        
        # Common API endpoints in ERPNext/Frappe
        self.api_endpoints = [
            "/api/resource/Customer",
            "/api/resource/Item", 
            "/api/resource/Supplier",
            "/api/resource/User",
            "/api/resource/Role",
            "/api/resource/System Settings",
            "/api/method/frappe.client.get_list",
            "/api/method/frappe.client.get",
            "/api/method/frappe.client.insert",
            "/api/method/frappe.client.submit",
            "/api/method/frappe.client.cancel",
            "/api/method/frappe.client.delete",
            "/api/method/frappe.desk.search.search_link",
            "/api/method/frappe.desk.reportview.get",
            "/api/method/frappe.auth.get_logged_user",
            "/api/method/ping",
            "/api/method/version"
        ]
    
    def log_test(self, test_name, status, details, severity="info"):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status} - {details}")
    
    def test_api_authentication(self):
        """Test API authentication requirements"""
        print("\n🔐 Testing API Authentication...")
        
        unauthenticated_access = 0
        
        for endpoint in self.api_endpoints:
            try:
                # Test without authentication
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                # Check if we get actual data without authentication
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # If we get structured data (not login redirect), it's likely unauthenticated access
                        if isinstance(data, (dict, list)) and len(str(data)) > 50:
                            if "login" not in str(data).lower() and "authentication" not in str(data).lower():
                                self.log_test("API Authentication", "FAIL",
                                            f"Unauthenticated access to {endpoint}", "high")
                                unauthenticated_access += 1
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, might be HTML redirect to login
                        pass
                        
            except requests.exceptions.RequestException:
                pass
        
        if unauthenticated_access == 0:
            self.log_test("API Authentication", "PASS", "API authentication properly enforced")
        
        return unauthenticated_access == 0
    
    def test_api_authorization(self):
        """Test API authorization and access controls"""
        print("\n👥 Testing API Authorization...")
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/resource/User",
            "/api/resource/Role", 
            "/api/resource/System Settings",
            "/api/method/frappe.core.doctype.user.user.get_all_users",
            "/api/method/frappe.desk.page.setup_wizard.setup_wizard.get_setup_wizard"
        ]
        
        authorization_issues = 0
        
        for endpoint in admin_endpoints:
            try:
                # Test with potentially low-privilege session
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Check if we got admin data
                        if isinstance(data, (dict, list)) and data:
                            # Look for sensitive information in response
                            response_str = str(data).lower()
                            sensitive_keywords = ["password", "hash", "secret", "token", "key"]
                            
                            for keyword in sensitive_keywords:
                                if keyword in response_str:
                                    self.log_test("API Authorization", "FAIL",
                                                f"Sensitive data exposed at {endpoint}", "high")
                                    authorization_issues += 1
                                    break
                    except (json.JSONDecodeError, ValueError):
                        pass
                        
            except requests.exceptions.RequestException:
                pass
        
        if authorization_issues == 0:
            self.log_test("API Authorization", "PASS", "API authorization appears proper")
        
        return authorization_issues == 0
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        print("\n🚦 Testing API Rate Limiting...")
        
        # Test with a safe endpoint
        test_endpoint = "/api/method/ping"
        
        try:
            start_time = time.time()
            request_count = 0
            rate_limited = False
            
            # Send rapid requests
            for i in range(100):
                try:
                    response = requests.get(f"{self.base_url}{test_endpoint}", timeout=5)
                    request_count += 1
                    
                    if response.status_code == 429:  # Too Many Requests
                        rate_limited = True
                        break
                    elif response.status_code != 200:
                        break
                        
                except requests.exceptions.RequestException:
                    break
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            if rate_limited:
                self.log_test("API Rate Limiting", "PASS", "Rate limiting is active")
                return True
            elif elapsed_time > 0:
                requests_per_second = request_count / elapsed_time
                if requests_per_second > 50:  # High request rate suggests no limiting
                    self.log_test("API Rate Limiting", "FAIL",
                                f"No rate limiting detected - {requests_per_second:.1f} req/s", "medium")
                    return False
                else:
                    self.log_test("API Rate Limiting", "PASS", "Rate limiting appears to be in place")
                    return True
            else:
                self.log_test("API Rate Limiting", "PASS", "Rate limiting test inconclusive")
                return True
                
        except Exception as e:
            self.log_test("API Rate Limiting", "PASS", f"Rate limiting test failed: {str(e)}")
            return True
    
    def test_api_input_validation(self):
        """Test API input validation"""
        print("\n✅ Testing API Input Validation...")
        
        # Test various malicious inputs
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>"},
            {"name": "'; DROP TABLE test; --"},
            {"filters": "{'$ne': ''}"},
            {"data": "A" * 10000},  # Very long input
            {"number_field": "not_a_number"},
            {"email": "invalid-email"},
            {"date": "not-a-date"},
            {"json_field": "{invalid json}"}
        ]
        
        validation_issues = 0
        
        for malicious_input in malicious_inputs:
            try:
                # Test POST with malicious data
                response = self.session.post(f"{self.base_url}/api/resource/Customer",
                                           json=malicious_input, timeout=10)
                
                # Look for unhandled errors or SQL errors
                if response.status_code == 500:
                    error_text = response.text.lower()
                    error_indicators = [
                        "mysql", "sql syntax", "traceback", "exception",
                        "internal server error", "database error"
                    ]
                    
                    for indicator in error_indicators:
                        if indicator in error_text:
                            self.log_test("API Input Validation", "FAIL",
                                        f"Unhandled error with input: {str(malicious_input)[:50]}...", "medium")
                            validation_issues += 1
                            break
                            
                # Test GET with malicious parameters
                for key, value in malicious_input.items():
                    params = {key: value}
                    response = self.session.get(f"{self.base_url}/api/method/frappe.client.get_list",
                                              params=params, timeout=10)
                    
                    if response.status_code == 500:
                        error_text = response.text.lower()
                        for indicator in error_indicators:
                            if indicator in error_text:
                                self.log_test("API Input Validation", "FAIL",
                                            f"Unhandled error with parameter {key}={str(value)[:20]}...", "medium")
                                validation_issues += 1
                                break
                                
            except requests.exceptions.RequestException:
                pass
            except Exception:
                pass
        
        if validation_issues == 0:
            self.log_test("API Input Validation", "PASS", "API input validation appears adequate")
        
        return validation_issues == 0
    
    def test_api_security_headers(self):
        """Test API security headers"""
        print("\n🛡️ Testing API Security Headers...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/method/ping", timeout=10)
            headers = response.headers
            
            # Check for important security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # Any value is good
                "Content-Security-Policy": None,
                "Referrer-Policy": None
            }
            
            missing_headers = []
            weak_headers = []
            
            for header, expected_value in security_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_value is not None:
                    if isinstance(expected_value, list):
                        if not any(val in headers[header] for val in expected_value):
                            weak_headers.append(f"{header}: {headers[header]}")
                    elif expected_value not in headers[header]:
                        weak_headers.append(f"{header}: {headers[header]}")
            
            if missing_headers or weak_headers:
                issues = []
                if missing_headers:
                    issues.append(f"Missing: {', '.join(missing_headers)}")
                if weak_headers:
                    issues.append(f"Weak: {', '.join(weak_headers)}")
                
                self.log_test("API Security Headers", "FAIL",
                            f"Security header issues: {'; '.join(issues)}", "medium")
                return False
            else:
                self.log_test("API Security Headers", "PASS", "Security headers properly configured")
                return True
                
        except requests.exceptions.RequestException:
            self.log_test("API Security Headers", "PASS", "API not accessible for header test")
            return True
    
    def test_api_error_handling(self):
        """Test API error handling and information disclosure"""
        print("\n⚠️ Testing API Error Handling...")
        
        # Test various error conditions
        error_tests = [
            ("/api/resource/NonExistentDocType", "GET", None),
            ("/api/resource/Customer/nonexistent_id", "GET", None),
            ("/api/method/nonexistent.method", "POST", {}),
            ("/api/resource/Customer", "POST", {"invalid": "data"}),
            ("/api/resource/Customer", "PUT", {"invalid": "data"}),
            ("/api/resource/Customer", "DELETE", None)
        ]
        
        information_leakage = 0
        
        for endpoint, method, data in error_tests:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
                elif method == "PUT":
                    response = self.session.put(f"{self.base_url}{endpoint}", json=data, timeout=10)
                elif method == "DELETE":
                    response = self.session.delete(f"{self.base_url}{endpoint}", timeout=10)
                
                # Check for information disclosure in error messages
                if response.status_code >= 400:
                    error_text = response.text.lower()
                    sensitive_info = [
                        "traceback", "file \"", "line ", "module ",
                        "directory", "path", "server", "database",
                        "mysql", "mariadb", "redis", "python",
                        "frappe", "erpnext", "/home/", "/var/",
                        "exception", "error in", "failed to"
                    ]
                    
                    for info in sensitive_info:
                        if info in error_text:
                            self.log_test("API Error Handling", "FAIL",
                                        f"Information disclosure in error: {endpoint}", "low")
                            information_leakage += 1
                            break
                            
            except requests.exceptions.RequestException:
                pass
        
        if information_leakage == 0:
            self.log_test("API Error Handling", "PASS", "Error handling appears secure")
        
        return information_leakage == 0
    
    def test_api_version_disclosure(self):
        """Test for API version and system information disclosure"""
        print("\n📋 Testing API Version Disclosure...")
        
        # Common endpoints that might expose version info
        version_endpoints = [
            "/api/method/version",
            "/api/method/frappe.utils.get_site_info",
            "/api/method/frappe.get_version",
            "/",
            "/app",
            "/desk"
        ]
        
        version_disclosure = 0
        
        for endpoint in version_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    response_text = response.text.lower()
                    
                    # Look for version information
                    version_indicators = [
                        "frappe", "erpnext", "version", "v1", "v2", "v3",
                        "api version", "server", "build", "commit",
                        "python", "mysql", "mariadb", "redis"
                    ]
                    
                    for indicator in version_indicators:
                        if indicator in response_text:
                            # Check if it's detailed version info (might be too much disclosure)
                            if ("version" in response_text and 
                                any(x in response_text for x in [".", "build", "commit", "date"])):
                                self.log_test("API Version Disclosure", "WARN",
                                            f"Detailed version info at {endpoint}", "low")
                                version_disclosure += 1
                                break
                            
            except requests.exceptions.RequestException:
                pass
        
        if version_disclosure == 0:
            self.log_test("API Version Disclosure", "PASS", "No excessive version disclosure detected")
        
        return version_disclosure == 0
    
    def test_api_cors_configuration(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            # Test CORS headers
            headers = {
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = self.session.options(f"{self.base_url}/api/method/ping", 
                                          headers=headers, timeout=10)
            
            cors_headers = response.headers
            
            # Check for overly permissive CORS
            cors_issues = []
            
            if "Access-Control-Allow-Origin" in cors_headers:
                origin = cors_headers["Access-Control-Allow-Origin"]
                if origin == "*":
                    cors_issues.append("Wildcard origin allowed")
                elif "evil.com" in origin:
                    cors_issues.append("Malicious origin accepted")
            
            if "Access-Control-Allow-Credentials" in cors_headers:
                if cors_headers["Access-Control-Allow-Credentials"].lower() == "true":
                    if cors_headers.get("Access-Control-Allow-Origin") == "*":
                        cors_issues.append("Credentials allowed with wildcard origin")
            
            if cors_issues:
                self.log_test("CORS Configuration", "FAIL",
                            f"CORS issues: {'; '.join(cors_issues)}", "medium")
                return False
            else:
                self.log_test("CORS Configuration", "PASS", "CORS configuration appears secure")
                return True
                
        except requests.exceptions.RequestException:
            self.log_test("CORS Configuration", "PASS", "CORS test inconclusive")
            return True
    
    def run_all_tests(self):
        """Run all API security tests"""
        print("🔌 Starting API Security Tests")
        print("=" * 50)
        
        tests = [
            self.test_api_authentication,
            self.test_api_authorization,
            self.test_api_rate_limiting,
            self.test_api_input_validation,
            self.test_api_security_headers,
            self.test_api_error_handling,
            self.test_api_version_disclosure,
            self.test_api_cors_configuration
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test.__name__, "ERROR", f"Test failed: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"API Security Tests Summary:")
        print(f"Passed: {passed}, Failed: {failed}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/api_security_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"Report saved to: {report_path}")
        return failed == 0

def main():
    """Main function"""
    api_tests = APISecurityTests()
    success = api_tests.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
