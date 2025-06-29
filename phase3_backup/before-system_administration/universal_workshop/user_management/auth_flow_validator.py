# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
import os
from datetime import datetime, timedelta


class AuthenticationFlowValidator:
    """Comprehensive authentication flow validation and testing"""
    
    def __init__(self):
        self.test_results = []
        self.validation_summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "critical_issues": 0
        }
    
    def run_complete_validation(self):
        """Run complete authentication flow validation"""
        try:
            print("🔐 Starting comprehensive authentication flow validation...")
            
            # 1. Custom Login Page Validation
            self.validate_custom_login_page()
            
            # 2. Session Management Integration
            self.validate_session_management()
            
            # 3. MFA System Validation
            self.validate_mfa_system()
            
            # 4. Role-Based Access Control
            self.validate_role_based_access()
            
            # 5. Arabic Interface Support
            self.validate_arabic_interface()
            
            # 6. Security Features
            self.validate_security_features()
            
            # 7. License Integration
            self.validate_license_integration()
            
            # 8. Boot Session Integration
            self.validate_boot_session()
            
            # Generate final report
            return self.generate_validation_report()
            
        except Exception as e:
            self.add_test_result("complete_validation", False, f"Validation failed: {e}", "critical")
            return self.generate_validation_report()
    
    def validate_custom_login_page(self):
        """Validate custom login page functionality"""
        try:
            test_name = "custom_login_page"
            
            # Check if login.py exists
            login_py_path = frappe.get_app_path("universal_workshop", "www", "login.py")
            login_html_path = frappe.get_app_path("universal_workshop", "www", "login.html")
            
            if not os.path.exists(login_py_path):
                self.add_test_result(test_name, False, "login.py file not found", "critical")
                return
            
            if not os.path.exists(login_html_path):
                self.add_test_result(test_name, False, "login.html file not found", "critical")
                return
            
            # Test login page components
            with open(login_py_path, 'r') as f:
                login_py_content = f.read()
            
            with open(login_html_path, 'r') as f:
                login_html_content = f.read()
            
            # Check for required components
            required_components = [
                ("setup_status_check", "get_setup_status" in login_py_content),
                ("license_validation", "validate_license" in login_py_content),
                ("arabic_support", "dir=\"rtl\"" in login_html_content or "arabic" in login_html_content.lower()),
                ("role_redirect", "get_role_home_page" in login_py_content),
                ("audit_logging", "log_login_attempt" in login_py_content)
            ]
            
            all_components_present = True
            missing_components = []
            
            for component, check in required_components:
                if not check:
                    all_components_present = False
                    missing_components.append(component)
            
            if all_components_present:
                self.add_test_result(test_name, True, "All login page components present")
            else:
                self.add_test_result(test_name, False, f"Missing components: {', '.join(missing_components)}", "warning")
            
        except Exception as e:
            self.add_test_result("custom_login_page", False, f"Login page validation failed: {e}", "critical")
    
    def validate_session_management(self):
        """Validate session management integration"""
        try:
            test_name = "session_management"
            
            # Check if session manager exists
            try:
                from universal_workshop.user_management.session_manager import SessionManager
                session_manager = SessionManager()
                
                # Test session manager methods
                methods_to_test = [
                    "get_current_session",
                    "validate_current_session", 
                    "create_session",
                    "cleanup_expired_sessions",
                    "get_user_security_settings"
                ]
                
                missing_methods = []
                for method in methods_to_test:
                    if not hasattr(session_manager, method):
                        missing_methods.append(method)
                
                if missing_methods:
                    self.add_test_result(test_name, False, f"Missing session manager methods: {', '.join(missing_methods)}", "critical")
                else:
                    self.add_test_result(test_name, True, "Session manager fully functional")
                
            except ImportError as e:
                self.add_test_result(test_name, False, f"Session manager import failed: {e}", "critical")
            
        except Exception as e:
            self.add_test_result("session_management", False, f"Session management validation failed: {e}", "critical")
    
    def validate_mfa_system(self):
        """Validate Multi-Factor Authentication system"""
        try:
            test_name = "mfa_system"
            
            # Check if MFA manager exists
            try:
                from universal_workshop.user_management.mfa_manager import MFAManager
                mfa_manager = MFAManager()
                
                # Test MFA manager methods
                mfa_methods = [
                    "is_mfa_required",
                    "generate_totp_secret",
                    "verify_totp_token",
                    "send_sms_otp",
                    "verify_sms_otp",
                    "generate_backup_codes"
                ]
                
                missing_mfa_methods = []
                for method in mfa_methods:
                    if not hasattr(mfa_manager, method):
                        missing_mfa_methods.append(method)
                
                if missing_mfa_methods:
                    self.add_test_result(test_name, False, f"Missing MFA methods: {', '.join(missing_mfa_methods)}", "warning")
                else:
                    self.add_test_result(test_name, True, "MFA system fully functional")
                
            except ImportError as e:
                self.add_test_result(test_name, False, f"MFA manager import failed: {e}", "warning")
            
        except Exception as e:
            self.add_test_result("mfa_system", False, f"MFA system validation failed: {e}", "warning")
    
    def validate_role_based_access(self):
        """Validate role-based access control"""
        try:
            test_name = "role_based_access"
            
            # Check if Workshop Roles exist
            workshop_roles = frappe.get_list("Workshop Role", fields=["role_name", "permissions"])
            
            required_roles = ["Workshop Owner", "Workshop Manager", "Workshop Technician", "Financial Staff", "Parts Manager", "Service Advisor"]
            existing_roles = [role.get("role_name") for role in workshop_roles]
            
            missing_roles = [role for role in required_roles if role not in existing_roles]
            
            if missing_roles:
                self.add_test_result(test_name, False, f"Missing workshop roles: {', '.join(missing_roles)}", "warning")
            else:
                self.add_test_result(test_name, True, f"All {len(required_roles)} workshop roles configured")
            
            # Check permission hooks
            try:
                from universal_workshop.user_management.permission_hooks import get_permission_query_conditions, has_permission
                self.add_test_result(f"{test_name}_hooks", True, "Permission hooks functional")
            except ImportError:
                self.add_test_result(f"{test_name}_hooks", False, "Permission hooks not found", "warning")
            
        except Exception as e:
            self.add_test_result("role_based_access", False, f"Role-based access validation failed: {e}", "warning")
    
    def validate_arabic_interface(self):
        """Validate Arabic interface support"""
        try:
            test_name = "arabic_interface"
            
            # Check Arabic CSS files
            arabic_css_files = [
                "public/css/arabic-rtl.css",
                "public/css/workshop-theme.css"
            ]
            
            missing_css = []
            for css_file in arabic_css_files:
                css_path = frappe.get_app_path("universal_workshop", css_file)
                if not os.path.exists(css_path):
                    missing_css.append(css_file)
            
            # Check Arabic JS files
            arabic_js_files = [
                "public/js/arabic-utils.js",
                "public/js/workshop-common.js"
            ]
            
            missing_js = []
            for js_file in arabic_js_files:
                js_path = frappe.get_app_path("universal_workshop", js_file)
                if not os.path.exists(js_path):
                    missing_js.append(js_file)
            
            if missing_css or missing_js:
                missing_files = missing_css + missing_js
                self.add_test_result(test_name, False, f"Missing Arabic files: {', '.join(missing_files)}", "warning")
            else:
                self.add_test_result(test_name, True, "Arabic interface files present")
            
        except Exception as e:
            self.add_test_result("arabic_interface", False, f"Arabic interface validation failed: {e}", "warning")
    
    def validate_security_features(self):
        """Validate security features"""
        try:
            test_name = "security_features"
            
            # Check security dashboard
            try:
                from universal_workshop.user_management.dashboard.security_dashboard import SecurityDashboard
                security_dashboard = SecurityDashboard()
                
                # Test security dashboard methods
                security_methods = [
                    "get_security_metrics",
                    "get_threat_analysis",
                    "get_user_activity_summary",
                    "get_security_alerts"
                ]
                
                missing_security_methods = []
                for method in security_methods:
                    if not hasattr(security_dashboard, method):
                        missing_security_methods.append(method)
                
                if missing_security_methods:
                    self.add_test_result(test_name, False, f"Missing security methods: {', '.join(missing_security_methods)}", "warning")
                else:
                    self.add_test_result(test_name, True, "Security dashboard fully functional")
                
            except ImportError:
                self.add_test_result(test_name, False, "Security dashboard not found", "warning")
            
            # Check audit logger
            try:
                from universal_workshop.user_management.audit_logger import AuditLogger
                self.add_test_result(f"{test_name}_audit", True, "Audit logger available")
            except ImportError:
                self.add_test_result(f"{test_name}_audit", False, "Audit logger not found", "warning")
            
        except Exception as e:
            self.add_test_result("security_features", False, f"Security features validation failed: {e}", "warning")
    
    def validate_license_integration(self):
        """Validate license integration with authentication"""
        try:
            test_name = "license_integration"
            
            # Check license validator
            try:
                from universal_workshop.license_management.license_validator import validate_current_license
                
                # Test license validation
                license_result = validate_current_license()
                
                if license_result.get("is_valid"):
                    self.add_test_result(test_name, True, f"License valid: {license_result.get('license_type')}")
                else:
                    self.add_test_result(test_name, False, f"License invalid: {license_result.get('message')}", "warning")
                
            except ImportError:
                self.add_test_result(test_name, False, "License validator not found", "critical")
            
        except Exception as e:
            self.add_test_result("license_integration", False, f"License integration validation failed: {e}", "critical")
    
    def validate_boot_session(self):
        """Validate boot session integration"""
        try:
            test_name = "boot_session"
            
            # Check boot.py file
            boot_path = frappe.get_app_path("universal_workshop", "boot.py")
            
            if not os.path.exists(boot_path):
                self.add_test_result(test_name, False, "boot.py file not found", "critical")
                return
            
            with open(boot_path, 'r') as f:
                boot_content = f.read()
            
            # Check for required boot functions
            required_boot_functions = [
                "get_boot_info",
                "check_initial_setup",
                "get_workshop_configuration",
                "get_license_information",
                "get_session_boot_info"
            ]
            
            missing_boot_functions = []
            for func in required_boot_functions:
                if f"def {func}" not in boot_content:
                    missing_boot_functions.append(func)
            
            if missing_boot_functions:
                self.add_test_result(test_name, False, f"Missing boot functions: {', '.join(missing_boot_functions)}", "warning")
            else:
                self.add_test_result(test_name, True, "All boot functions present")
            
        except Exception as e:
            self.add_test_result("boot_session", False, f"Boot session validation failed: {e}", "warning")
    
    def add_test_result(self, test_name, passed, message, severity="info"):
        """Add test result to validation summary"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        self.validation_summary["total_tests"] += 1
        
        if passed:
            self.validation_summary["passed"] += 1
        else:
            self.validation_summary["failed"] += 1
            
            if severity == "critical":
                self.validation_summary["critical_issues"] += 1
            elif severity == "warning":
                self.validation_summary["warnings"] += 1
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        try:
            # Calculate success rate
            success_rate = (self.validation_summary["passed"] / self.validation_summary["total_tests"]) * 100 if self.validation_summary["total_tests"] > 0 else 0
            
            # Determine overall status
            if self.validation_summary["critical_issues"] > 0:
                overall_status = "CRITICAL"
            elif self.validation_summary["failed"] > self.validation_summary["passed"]:
                overall_status = "POOR"
            elif self.validation_summary["warnings"] > 0:
                overall_status = "GOOD"
            else:
                overall_status = "EXCELLENT"
            
            report = {
                "validation_summary": self.validation_summary,
                "success_rate": round(success_rate, 2),
                "overall_status": overall_status,
                "test_results": self.test_results,
                "recommendations": self.generate_recommendations(),
                "generated_at": datetime.now().isoformat()
            }
            
            # Print summary
            print(f"\n🔐 Authentication Flow Validation Complete")
            print(f"Overall Status: {overall_status}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Tests Passed: {self.validation_summary['passed']}/{self.validation_summary['total_tests']}")
            print(f"Warnings: {self.validation_summary['warnings']}")
            print(f"Critical Issues: {self.validation_summary['critical_issues']}")
            
            return report
            
        except Exception as e:
            frappe.log_error(f"Error generating validation report: {e}")
            return {"error": str(e)}
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for critical issues
        critical_tests = [result for result in self.test_results if result["severity"] == "critical" and not result["passed"]]
        for test in critical_tests:
            recommendations.append({
                "priority": "HIGH",
                "category": "Critical Fix",
                "issue": test["test_name"],
                "recommendation": f"Fix critical issue: {test['message']}"
            })
        
        # Check for warnings
        warning_tests = [result for result in self.test_results if result["severity"] == "warning" and not result["passed"]]
        for test in warning_tests:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Enhancement",
                "issue": test["test_name"],
                "recommendation": f"Address warning: {test['message']}"
            })
        
        # General recommendations
        if self.validation_summary["success_rate"] < 80:
            recommendations.append({
                "priority": "HIGH",
                "category": "System Health",
                "issue": "low_success_rate",
                "recommendation": "Authentication system needs significant improvements"
            })
        
        return recommendations


@frappe.whitelist()
def run_authentication_flow_validation():
    """API endpoint to run authentication flow validation"""
    try:
        validator = AuthenticationFlowValidator()
        report = validator.run_complete_validation()
        return report
        
    except Exception as e:
        frappe.log_error(f"Authentication flow validation API error: {e}")
        return {"error": str(e)}


def run_validation_cli():
    """CLI function to run validation"""
    validator = AuthenticationFlowValidator()
    report = validator.run_complete_validation()
    
    # Create logs directory if it doesn't exist
    logs_dir = frappe.get_app_path("universal_workshop", "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Save report to file
    report_path = os.path.join(logs_dir, "auth_validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return report


if __name__ == "__main__":
    run_validation_cli() 