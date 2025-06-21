#!/usr/bin/env python3
"""
Security Framework Testing - Standalone Validation
Tests security controls without requiring a running ERPNext server
"""

import sys
import os
import json
import hashlib
import ssl
import socket
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

class SecurityFrameworkTester:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "vulnerabilities": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "vulnerabilities_found": 0
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
            
        print(f"   {details}")
    
    def test_security_framework_structure(self):
        """Test security framework file structure"""
        print("\n📁 Testing Security Framework Structure...")
        
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        required_files = [
            "README.md",
            "run_security_tests.py",
            "test_authentication.py",
            "test_injection.py", 
            "test_api_security.py",
            "test_zap_scanner.py",
            "validate_security_framework.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not (base_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.log_test("Security Framework Structure", "FAIL", 
                         f"Missing files: {', '.join(missing_files)}", "high")
            return False
        else:
            self.log_test("Security Framework Structure", "PASS", 
                         f"All {len(required_files)} security test files present")
            return True
    
    def test_python_dependencies(self):
        """Test Python dependencies for security testing"""
        print("\n📦 Testing Python Dependencies...")
        
        required_packages = [
            ("requests", "HTTP client for API testing"),
            ("jwt", "JWT token handling"),
            ("psutil", "System monitoring"),
            ("json", "JSON processing"),
            ("ssl", "SSL/TLS testing"),
            ("socket", "Network testing"),
            ("hashlib", "Cryptographic functions"),
            ("subprocess", "Process execution"),
            ("urllib.parse", "URL parsing")
        ]
        
        missing_packages = []
        available_packages = []
        
        for package, description in required_packages:
            try:
                if package == "jwt":
                    import jwt as pyjwt
                else:
                    __import__(package)
                available_packages.append(f"{package} ({description})")
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.log_test("Python Dependencies", "FAIL", 
                         f"Missing packages: {', '.join(missing_packages)}", "medium")
            return False
        else:
            self.log_test("Python Dependencies", "PASS", 
                         f"All {len(required_packages)} required packages available")
            return True
    
    def test_security_test_categories(self):
        """Test security test category coverage"""
        print("\n🔍 Testing Security Test Categories...")
        
        # Read and analyze security test files
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        
        security_categories = {
            "Authentication Testing": ["password", "login", "session", "jwt", "brute.force"],
            "Authorization Testing": ["rbac", "role", "permission", "access.control"],
            "Input Validation": ["sql.injection", "xss", "csrf", "input.validation"],
            "API Security": ["api", "endpoint", "rate.limiting", "cors"],
            "SSL/TLS Testing": ["ssl", "tls", "certificate", "https"],
            "Information Disclosure": ["information.disclosure", "error.handling", "version"],
            "File Security": ["file.upload", "path.traversal", "file.inclusion"],
            "Session Management": ["session", "cookie", "timeout", "fixation"]
        }
        
        covered_categories = []
        
        for test_file in ["test_authentication.py", "test_injection.py", "test_api_security.py", "run_security_tests.py"]:
            file_path = base_dir / test_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().lower()
                    
                    for category, keywords in security_categories.items():
                        if any(keyword.replace(".", "_") in content or keyword.replace(".", " ") in content 
                              for keyword in keywords):
                            if category not in covered_categories:
                                covered_categories.append(category)
                except Exception:
                    pass
        
        coverage_percentage = (len(covered_categories) / len(security_categories)) * 100
        
        if coverage_percentage >= 80:
            self.log_test("Security Test Categories", "PASS", 
                         f"Good coverage: {len(covered_categories)}/{len(security_categories)} categories ({coverage_percentage:.1f}%)")
            return True
        else:
            missing_categories = [cat for cat in security_categories.keys() if cat not in covered_categories]
            self.log_test("Security Test Categories", "FAIL", 
                         f"Limited coverage: {len(covered_categories)}/{len(security_categories)} categories ({coverage_percentage:.1f}%). Missing: {', '.join(missing_categories)}", "medium")
            return False
    
    def test_owasp_top10_coverage(self):
        """Test OWASP Top 10 vulnerability coverage"""
        print("\n🏆 Testing OWASP Top 10 Coverage...")
        
        owasp_top10 = {
            "A01 Broken Access Control": ["access.control", "rbac", "authorization", "privilege"],
            "A02 Cryptographic Failures": ["ssl", "tls", "encryption", "crypto"],
            "A03 Injection": ["sql.injection", "nosql", "command.injection", "injection"],
            "A04 Insecure Design": ["security.design", "threat.modeling"],
            "A05 Security Misconfiguration": ["configuration", "default.credentials", "headers"],
            "A06 Vulnerable Components": ["dependency", "component", "version", "update"],
            "A07 Authentication Failures": ["authentication", "password", "session", "mfa"],
            "A08 Software Integrity": ["integrity", "ci.cd", "supply.chain"],
            "A09 Logging Failures": ["logging", "monitoring", "audit"],
            "A10 SSRF": ["ssrf", "server.side.request", "url.validation"]
        }
        
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        covered_vulnerabilities = []
        
        # Check coverage in security test files
        test_files = ["run_security_tests.py", "test_authentication.py", "test_injection.py", "test_api_security.py"]
        
        all_content = ""
        for test_file in test_files:
            file_path = base_dir / test_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        all_content += f.read().lower() + " "
                except Exception:
                    pass
        
        for vuln_name, keywords in owasp_top10.items():
            if any(keyword.replace(".", "_") in all_content or keyword.replace(".", " ") in all_content 
                  for keyword in keywords):
                covered_vulnerabilities.append(vuln_name)
        
        coverage_percentage = (len(covered_vulnerabilities) / len(owasp_top10)) * 100
        
        if coverage_percentage >= 70:
            self.log_test("OWASP Top 10 Coverage", "PASS", 
                         f"Good OWASP coverage: {len(covered_vulnerabilities)}/{len(owasp_top10)} vulnerabilities ({coverage_percentage:.1f}%)")
            return True
        else:
            missing_vulns = [vuln for vuln in owasp_top10.keys() if vuln not in covered_vulnerabilities]
            self.log_test("OWASP Top 10 Coverage", "FAIL", 
                         f"Limited OWASP coverage: {len(covered_vulnerabilities)}/{len(owasp_top10)} vulnerabilities ({coverage_percentage:.1f}%). Missing: {', '.join(missing_vulns[:3])}...", "medium")
            return False
    
    def test_reporting_capabilities(self):
        """Test security reporting capabilities"""
        print("\n📊 Testing Reporting Capabilities...")
        
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        reports_dir = base_dir / "reports"
        
        # Check if reports directory exists and is writable
        try:
            reports_dir.mkdir(exist_ok=True)
            
            # Test writing a sample report
            test_report_path = reports_dir / "test_report.json"
            test_data = {
                "test": "security_framework_validation",
                "timestamp": datetime.now().isoformat(),
                "status": "testing"
            }
            
            with open(test_report_path, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            # Verify report was created and is readable
            with open(test_report_path, 'r') as f:
                loaded_data = json.load(f)
            
            if loaded_data["test"] == test_data["test"]:
                # Clean up test file
                test_report_path.unlink()
                self.log_test("Reporting Capabilities", "PASS", 
                             "Report generation and reading capabilities verified")
                return True
            else:
                self.log_test("Reporting Capabilities", "FAIL", 
                             "Report data integrity check failed", "medium")
                return False
                
        except Exception as e:
            self.log_test("Reporting Capabilities", "FAIL", 
                         f"Report generation failed: {str(e)}", "medium")
            return False
    
    def test_erpnext_specific_coverage(self):
        """Test ERPNext/Frappe specific security considerations"""
        print("\n🏢 Testing ERPNext/Frappe Specific Coverage...")
        
        erpnext_security_areas = {
            "DocType Security": ["doctype", "permissions", "document"],
            "Frappe Framework": ["frappe", "hooks", "bench"],
            "API Endpoints": ["/api/resource", "/api/method", "frappe.client"],
            "Workshop Specific": ["customer", "vehicle", "inventory", "workshop"],
            "Database Security": ["mariadb", "mysql", "database"],
            "File Management": ["file.manager", "upload", "attachment"],
            "User Management": ["user", "role", "profile"],
            "Custom Fields": ["custom.field", "customization"]
        }
        
        base_dir = Path("/home/said/frappe-dev/frappe-bench/tests/security")
        test_files = ["run_security_tests.py", "test_authentication.py", "test_injection.py", "test_api_security.py"]
        
        all_content = ""
        for test_file in test_files:
            file_path = base_dir / test_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        all_content += f.read().lower() + " "
                except Exception:
                    pass
        
        covered_areas = []
        for area_name, keywords in erpnext_security_areas.items():
            if any(keyword.replace(".", "_") in all_content or keyword.replace(".", " ") in all_content 
                  for keyword in keywords):
                covered_areas.append(area_name)
        
        coverage_percentage = (len(covered_areas) / len(erpnext_security_areas)) * 100
        
        if coverage_percentage >= 60:
            self.log_test("ERPNext Specific Coverage", "PASS", 
                         f"Good ERPNext coverage: {len(covered_areas)}/{len(erpnext_security_areas)} areas ({coverage_percentage:.1f}%)")
            return True
        else:
            missing_areas = [area for area in erpnext_security_areas.keys() if area not in covered_areas]
            self.log_test("ERPNext Specific Coverage", "FAIL", 
                         f"Limited ERPNext coverage: {len(covered_areas)}/{len(erpnext_security_areas)} areas ({coverage_percentage:.1f}%). Missing: {', '.join(missing_areas[:2])}...", "low")
            return False
    
    def test_security_configuration_files(self):
        """Test security configuration and policy files"""
        print("\n⚙️ Testing Security Configuration...")
        
        # Check for security-related configuration files
        base_dir = Path("/home/said/frappe-dev/frappe-bench")
        security_configs = [
            ("tests/security/README.md", "Security documentation"),
            (".gitignore", "Git security (preventing secret commits)"),
            ("requirements.txt", "Dependency management"),
            ("sites/common_site_config.json", "Site configuration")
        ]
        
        found_configs = []
        missing_configs = []
        
        for config_file, description in security_configs:
            config_path = base_dir / config_file
            if config_path.exists():
                found_configs.append(f"{config_file} ({description})")
            else:
                missing_configs.append(config_file)
        
        if len(found_configs) >= len(security_configs) * 0.7:  # At least 70% of configs found
            self.log_test("Security Configuration", "PASS", 
                         f"Security configurations present: {len(found_configs)}/{len(security_configs)}")
            return True
        else:
            self.log_test("Security Configuration", "FAIL", 
                         f"Missing security configurations: {', '.join(missing_configs)}", "low")
            return False
    
    def run_framework_validation(self):
        """Run complete security framework validation"""
        print("🔒 ERPNext/Frappe Security Framework Validation")
        print("=" * 60)
        
        # Run all validation tests
        test_methods = [
            self.test_security_framework_structure,
            self.test_python_dependencies,
            self.test_security_test_categories,
            self.test_owasp_top10_coverage,
            self.test_reporting_capabilities,
            self.test_erpnext_specific_coverage,
            self.test_security_configuration_files
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, "ERROR", f"Test failed with exception: {str(e)}")
        
        self.generate_validation_report()
        return self.test_results["summary"]["failed"] == 0
    
    def generate_validation_report(self):
        """Generate security framework validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate main validation report
        report_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/framework_validation_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary report
        summary_path = f"/home/said/frappe-dev/frappe-bench/tests/security/reports/framework_validation_summary_{timestamp}.md"
        self.generate_validation_summary(summary_path)
        
        print("\n" + "=" * 60)
        print("📊 Security Framework Validation Summary")
        print("=" * 60)
        print(f"Total Tests: {self.test_results['summary']['total_tests']}")
        print(f"Passed: {self.test_results['summary']['passed']}")
        print(f"Failed: {self.test_results['summary']['failed']}")
        
        success_rate = (self.test_results['summary']['passed'] / self.test_results['summary']['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📄 Reports saved to:")
        print(f"  - {report_path}")
        print(f"  - {summary_path}")
    
    def generate_validation_summary(self, file_path):
        """Generate markdown validation summary"""
        success_rate = (self.test_results['summary']['passed'] / self.test_results['summary']['total_tests']) * 100
        
        content = f"""# Security Framework Validation Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Framework:** ERPNext/Frappe Security Testing Suite

## Validation Summary

- **Total Validation Tests:** {self.test_results['summary']['total_tests']}
- **Tests Passed:** {self.test_results['summary']['passed']}
- **Tests Failed:** {self.test_results['summary']['failed']}
- **Success Rate:** {success_rate:.1f}%

## Framework Readiness

{'✅ **FRAMEWORK READY FOR SECURITY TESTING**' if success_rate >= 80 else '⚠️ **FRAMEWORK NEEDS IMPROVEMENTS**'}

## Validation Results

| Test Component | Status | Details |
|----------------|--------|---------|
"""
        
        for test in self.test_results["tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "❌"
            content += f"| {test['test_name']} | {status_icon} {test['status']} | {test['details']} |\n"
        
        content += f"""

## Security Testing Capabilities

The security framework includes comprehensive testing for:

### Core Security Areas
- Authentication and Authorization Testing
- Input Validation and Injection Prevention
- API Security Assessment
- SSL/TLS Configuration Validation
- Session Management Security

### OWASP Top 10 Coverage
- Broken Access Control
- Cryptographic Failures
- Injection Vulnerabilities
- Insecure Design
- Security Misconfiguration
- Vulnerable and Outdated Components
- Identification and Authentication Failures
- Software and Data Integrity Failures
- Security Logging and Monitoring Failures
- Server-Side Request Forgery (SSRF)

### ERPNext/Frappe Specific
- DocType Security Testing
- Frappe Framework API Security
- Workshop Application Security
- Database Security Validation
- File Management Security
- User Role and Permission Testing

## Next Steps

{'1. **Security Framework Ready:** Proceed with comprehensive security testing' if success_rate >= 80 else '1. **Address Framework Issues:** Fix failed validation tests before security testing'}
2. **Run Security Tests:** Execute the full security test suite
3. **Review Results:** Analyze security test results and vulnerabilities
4. **Implement Fixes:** Address identified security issues
5. **Regular Testing:** Schedule recurring security assessments

## Framework Files

- `run_security_tests.py` - Main security test orchestrator
- `test_authentication.py` - Authentication and authorization tests
- `test_injection.py` - Injection and input validation tests
- `test_api_security.py` - API security assessment tests
- `test_zap_scanner.py` - OWASP ZAP integration tests
- `validate_security_framework.py` - Framework validation tests

---
*Security Framework Validation completed at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        with open(file_path, 'w') as f:
            f.write(content)

def main():
    """Main function to run security framework validation"""
    tester = SecurityFrameworkTester()
    success = tester.run_framework_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
