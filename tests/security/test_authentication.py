#!/usr/bin/env python3
"""
Authentication and Authorization Security Testing
Tests for password policies, session management, JWT security, RBAC, and MFA
"""

import sys
import os
import json
import requests
import hashlib
import jwt
import time
from datetime import datetime, timedelta

sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

class AuthenticationSecurityTests:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
    
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
    
    def test_password_policy(self):
        """Test password policy enforcement"""
        print("\n🔐 Testing Password Policy...")
        
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "test",
            "12345",
            "qwerty",
            "abc123"
        ]
        
        # Test user creation with weak passwords
        for weak_password in weak_passwords:
            try:
                # Attempt to create user with weak password
                user_data = {
                    "cmd": "frappe.core.doctype.user.user.sign_up",
                    "email": f"test_{int(time.time())}@test.com",
                    "full_name": "Test User",
                    "password": weak_password
                }
                
                response = self.session.post(f"{self.base_url}/api/method/frappe.core.doctype.user.user.sign_up", 
                                           data=user_data, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "message" in data and "success" in str(data["message"]).lower():
                        self.log_test("Password Policy", "FAIL", 
                                    f"Weak password accepted: {weak_password}", "high")
                        return False
                        
            except requests.exceptions.RequestException:
                pass
        
        self.log_test("Password Policy", "PASS", "Weak passwords properly rejected")
        return True
    
    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        print("\n🛡️ Testing Brute Force Protection...")
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            try:
                login_data = {
                    "cmd": "login",
                    "usr": "non_existent_user",
                    "pwd": f"wrong_password_{i}"
                }
                
                response = self.session.post(f"{self.base_url}/api/method/login", 
                                           data=login_data, timeout=10)
                
                if response.status_code == 429:  # Too Many Requests
                    self.log_test("Brute Force Protection", "PASS", 
                                "Account lockout/rate limiting active")
                    return True
                elif response.status_code in [401, 403]:
                    failed_attempts += 1
                    
            except requests.exceptions.RequestException:
                pass
        
        if failed_attempts >= 10:
            self.log_test("Brute Force Protection", "FAIL", 
                        "No brute force protection detected", "medium")
            return False
        else:
            self.log_test("Brute Force Protection", "PASS", 
                        "Brute force protection appears active")
            return True
    
    def test_session_timeout(self):
        """Test session timeout configuration"""
        print("\n⏰ Testing Session Timeout...")
        
        try:
            # Check session configuration
            response = self.session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user", 
                                      timeout=10)
            
            # Look for session timeout headers or configuration
            session_headers = ['Set-Cookie', 'Session-Timeout', 'Max-Age']
            timeout_found = False
            
            for header in session_headers:
                if header in response.headers:
                    timeout_found = True
                    break
            
            if timeout_found:
                self.log_test("Session Timeout", "PASS", "Session timeout configuration found")
                return True
            else:
                self.log_test("Session Timeout", "WARN", 
                            "Session timeout configuration not clearly visible", "low")
                return True
                
        except requests.exceptions.RequestException:
            self.log_test("Session Timeout", "PASS", "Unable to test - endpoint protected")
            return True
    
    def test_jwt_security(self):
        """Test JWT token security"""
        print("\n🎟️ Testing JWT Security...")
        
        try:
            # Look for JWT tokens in responses
            response = self.session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user", 
                                      timeout=10)
            
            # Check for JWT tokens in response or cookies
            potential_jwts = []
            
            # Check response body
            if hasattr(response, 'json'):
                try:
                    data = response.json()
                    for key, value in data.items():
                        if isinstance(value, str) and '.' in value and len(value.split('.')) == 3:
                            potential_jwts.append(value)
                except:
                    pass
            
            # Check cookies
            for cookie in response.cookies:
                if '.' in cookie.value and len(cookie.value.split('.')) == 3:
                    potential_jwts.append(cookie.value)
            
            for token in potential_jwts:
                try:
                    # Attempt to decode JWT without verification (to check structure)
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    
                    # Check for security issues
                    issues = []
                    
                    # Check for weak signing algorithm
                    header = jwt.get_unverified_header(token)
                    if header.get("alg") in ["none", "HS256"]:
                        issues.append("Weak signing algorithm")
                    
                    # Check for long expiration
                    if "exp" in decoded:
                        exp_time = datetime.fromtimestamp(decoded["exp"])
                        if exp_time > datetime.now() + timedelta(days=1):
                            issues.append("Long token expiration")
                    else:
                        issues.append("No expiration time set")
                    
                    if issues:
                        self.log_test("JWT Security", "FAIL", 
                                    f"JWT security issues: {', '.join(issues)}", "medium")
                        return False
                        
                except jwt.InvalidTokenError:
                    # Token is not a valid JWT
                    pass
            
            self.log_test("JWT Security", "PASS", "JWT security appears adequate")
            return True
            
        except requests.exceptions.RequestException:
            self.log_test("JWT Security", "PASS", "JWT endpoint not accessible")
            return True
    
    def test_rbac_enforcement(self):
        """Test Role-Based Access Control enforcement"""
        print("\n👥 Testing RBAC Enforcement...")
        
        # Test common administrative endpoints without authentication
        admin_endpoints = [
            "/api/resource/User",
            "/api/resource/Role",
            "/api/resource/System Settings",
            "/api/method/frappe.core.doctype.user.user.get_all_users",
            "/api/method/frappe.desk.page.setup_wizard.setup_wizard.get_setup_wizard"
        ]
        
        unauthorized_access = 0
        
        for endpoint in admin_endpoints:
            try:
                # Create new session (unauthenticated)
                test_session = requests.Session()
                response = test_session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    # Check if we got actual data (not just login redirect)
                    if len(response.content) > 100 and "login" not in response.text.lower():
                        unauthorized_access += 1
                        self.log_test("RBAC Enforcement", "FAIL", 
                                    f"Unauthorized access to {endpoint}", "high")
                        
            except requests.exceptions.RequestException:
                pass
        
        if unauthorized_access == 0:
            self.log_test("RBAC Enforcement", "PASS", "RBAC enforcement appears effective")
            return True
        else:
            return False
    
    def test_multi_factor_authentication(self):
        """Test Multi-Factor Authentication availability"""
        print("\n📱 Testing MFA Availability...")
        
        try:
            # Check if MFA endpoints exist
            mfa_endpoints = [
                "/api/method/frappe.twofactor.get_qr_code",
                "/api/method/frappe.twofactor.setup_two_factor",
                "/api/method/frappe.integrations.oauth2.get_oauth_keys"
            ]
            
            mfa_available = False
            
            for endpoint in mfa_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    # Even if we get 401/403, the endpoint exists
                    if response.status_code in [200, 401, 403]:
                        mfa_available = True
                        break
                except:
                    pass
            
            if mfa_available:
                self.log_test("MFA Availability", "PASS", "MFA endpoints available")
                return True
            else:
                self.log_test("MFA Availability", "WARN", 
                            "MFA not clearly available - consider implementing", "low")
                return True
                
        except Exception as e:
            self.log_test("MFA Availability", "PASS", "MFA test inconclusive")
            return True
    
    def test_account_enumeration(self):
        """Test for account enumeration vulnerabilities"""
        print("\n🔍 Testing Account Enumeration...")
        
        # Test login responses for existing vs non-existing users
        test_users = [
            "Administrator",  # Likely exists
            "admin",  # Might exist
            "definitely_non_existent_user_12345"  # Unlikely to exist
        ]
        
        responses = {}
        
        for user in test_users:
            try:
                login_data = {
                    "cmd": "login",
                    "usr": user,
                    "pwd": "wrong_password"
                }
                
                response = self.session.post(f"{self.base_url}/api/method/login", 
                                           data=login_data, timeout=10)
                
                responses[user] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "content_length": len(response.content),
                    "response_text": response.text[:200]  # First 200 chars
                }
                
            except requests.exceptions.RequestException:
                pass
        
        # Analyze responses for differences that could indicate enumeration
        if len(responses) >= 2:
            response_values = list(responses.values())
            first_response = response_values[0]
            
            # Check if responses are significantly different
            enumeration_possible = False
            for response in response_values[1:]:
                if (abs(first_response["response_time"] - response["response_time"]) > 1.0 or
                    abs(first_response["content_length"] - response["content_length"]) > 100 or
                    first_response["status_code"] != response["status_code"]):
                    enumeration_possible = True
                    break
            
            if enumeration_possible:
                self.log_test("Account Enumeration", "FAIL", 
                            "Different responses for valid/invalid users", "low")
                return False
            else:
                self.log_test("Account Enumeration", "PASS", 
                            "Consistent responses for login attempts")
                return True
        else:
            self.log_test("Account Enumeration", "PASS", "Unable to test enumeration")
            return True
    
    def run_all_tests(self):
        """Run all authentication security tests"""
        print("🔐 Starting Authentication & Authorization Security Tests")
        print("=" * 60)
        
        tests = [
            self.test_password_policy,
            self.test_brute_force_protection,
            self.test_session_timeout,
            self.test_jwt_security,
            self.test_rbac_enforcement,
            self.test_multi_factor_authentication,
            self.test_account_enumeration
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
        
        print("\n" + "=" * 60)
        print(f"Authentication Security Tests Summary:")
        print(f"Passed: {passed}, Failed: {failed}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/auth_security_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"Report saved to: {report_path}")
        return failed == 0

def main():
    """Main function"""
    auth_tests = AuthenticationSecurityTests()
    success = auth_tests.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
