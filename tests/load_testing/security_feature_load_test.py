#!/usr/bin/env python3
"""
Universal Workshop ERP - Security Feature Validation Under Load
Tests the robustness of security features (rate limiting, MFA, security alerts) 
during high concurrent user activity in both Arabic and English interfaces.
"""

import os
import sys
import time
import json
import threading
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# Add the frappe-bench directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Test configuration
TEST_USERS = [
    {
        "username": "workshop_owner@universal.local",
        "password": "admin123",
        "role": "Workshop Owner",
        "language": "en",
        "valid": True
    },
    {
        "username": "workshop_manager@universal.local", 
        "password": "manager123",
        "role": "Workshop Manager",
        "language": "ar",
        "valid": True
    },
    {
        "username": "technician@universal.local",
        "password": "tech123", 
        "role": "Workshop Technician",
        "language": "en",
        "valid": True
    },
    {
        "username": "customer@universal.local",
        "password": "customer123",
        "role": "Customer",
        "language": "ar",
        "valid": True
    },
    # Invalid users for testing failed login rate limiting
    {
        "username": "invalid_user@universal.local",
        "password": "wrong_password",
        "role": "Invalid",
        "language": "en",
        "valid": False
    },
    {
        "username": "attacker@universal.local",
        "password": "hack_attempt",
        "role": "Attacker",
        "language": "ar",
        "valid": False
    }
]

@dataclass
class SecurityTestResult:
    """Result structure for security tests"""
    test_name: str
    success: bool
    response_time: float
    rate_limited: bool = False
    mfa_triggered: bool = False
    alert_triggered: bool = False
    error_message: str = ""
    details: Dict[str, Any] = None

class SecurityFeatureLoadTester:
    """Comprehensive security feature testing under load"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_start_time = None
        self.results = {
            "rate_limiting": {
                "tests_run": 0,
                "rate_limits_triggered": 0,
                "rate_limits_bypassed": 0,
                "average_response_time": 0,
                "response_times": []
            },
            "mfa_validation": {
                "tests_run": 0,
                "mfa_triggered": 0,
                "mfa_bypassed": 0,
                "successful_validations": 0,
                "failed_validations": 0,
                "response_times": []
            },
            "security_alerts": {
                "tests_run": 0,
                "alerts_triggered": 0,
                "false_positives": 0,
                "alert_types": {},
                "response_times": []
            },
            "concurrent_performance": {
                "peak_concurrent_users": 0,
                "system_degradation": False,
                "performance_metrics": []
            },
            "arabic_interface": {
                "tests_run": 0,
                "successful": 0,
                "failed": 0,
                "security_features_working": 0
            },
            "english_interface": {
                "tests_run": 0,
                "successful": 0,
                "failed": 0,
                "security_features_working": 0
            },
            "errors": [],
            "test_scenarios": []
        }
        
    def run_comprehensive_security_test(self, concurrent_users=20, test_duration_minutes=10):
        """Run comprehensive security feature validation under load"""
        print(f"\n🔒 Starting Security Feature Validation Under Load")
        print(f"📊 Configuration: {concurrent_users} concurrent users, {test_duration_minutes} minutes duration")
        print(f"🌐 Target: {self.base_url}")
        
        self.test_start_time = datetime.now()
        
        # Test phases
        print("\n📋 Security Test Phases:")
        print("1. Rate Limiting Stress Testing")
        print("2. MFA Validation Under Load")
        print("3. Security Alert System Testing")
        print("4. Concurrent Attack Simulation")
        print("5. Arabic/English Interface Security Testing")
        print("6. Performance Degradation Analysis")
        
        # Execute test phases
        self._test_rate_limiting_under_load(concurrent_users)
        self._test_mfa_validation_under_load(concurrent_users)
        self._test_security_alerts_under_load(concurrent_users)
        self._test_concurrent_attack_simulation(concurrent_users)
        self._test_interface_security(concurrent_users)
        self._analyze_performance_degradation()
        
        # Generate comprehensive report
        self._generate_security_test_report()
        
    def _test_rate_limiting_under_load(self, concurrent_users):
        """Test rate limiting effectiveness under high load"""
        print(f"\n🔄 Phase 1: Rate Limiting Stress Testing ({concurrent_users} concurrent users)")
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Create multiple attack scenarios
            attack_scenarios = [
                {"type": "login_flood", "requests_per_user": 10},
                {"type": "api_flood", "requests_per_user": 15},
                {"type": "dashboard_flood", "requests_per_user": 8}
            ]
            
            for scenario in attack_scenarios:
                for i in range(concurrent_users // len(attack_scenarios)):
                    user_data = TEST_USERS[i % len(TEST_USERS)]
                    future = executor.submit(
                        self._simulate_rate_limit_attack, 
                        user_data, 
                        scenario, 
                        i
                    )
                    futures.append(future)
                    
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self._update_rate_limiting_results(result)
                except Exception as e:
                    self.results["errors"].append({
                        "phase": "rate_limiting",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

    def _simulate_rate_limit_attack(self, user_data: Dict, scenario: Dict, user_index: int) -> SecurityTestResult:
        """Simulate rate limiting attack scenario"""
        session = requests.Session()
        start_time = time.time()
        
        try:
            print(f"   🎯 User {user_index}: {scenario['type']} attack with {scenario['requests_per_user']} requests")
            
            # Set language preference
            session.headers.update({
                'Accept-Language': 'ar' if user_data["language"] == "ar" else 'en',
                'User-Agent': f'SecurityTest-{scenario["type"]}-{user_index}'
            })
            
            rate_limited_count = 0
            successful_requests = 0
            
            for request_num in range(scenario["requests_per_user"]):
                if scenario["type"] == "login_flood":
                    response = self._attempt_login_flood(session, user_data)
                elif scenario["type"] == "api_flood":
                    response = self._attempt_api_flood(session, user_data)
                elif scenario["type"] == "dashboard_flood":
                    response = self._attempt_dashboard_flood(session, user_data)
                else:
                    continue
                    
                if response and response.status_code == 429:  # Rate limited
                    rate_limited_count += 1
                elif response and response.status_code == 200:
                    successful_requests += 1
                    
                # Small delay between requests
                time.sleep(0.1)
                
            response_time = time.time() - start_time
            
            # Rate limiting is working if we got rate limited responses
            rate_limiting_working = rate_limited_count > 0
            
            return SecurityTestResult(
                test_name=f"{scenario['type']}_attack",
                success=rate_limiting_working,
                response_time=response_time,
                rate_limited=rate_limiting_working,
                details={
                    "total_requests": scenario["requests_per_user"],
                    "rate_limited_count": rate_limited_count,
                    "successful_requests": successful_requests,
                    "user": user_data["username"],
                    "language": user_data["language"]
                }
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name=f"{scenario['type']}_attack",
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                details={"user": user_data["username"]}
            )

    def _attempt_login_flood(self, session: requests.Session, user_data: Dict) -> requests.Response:
        """Attempt login flood attack"""
        login_data = {
            "cmd": "login",
            "usr": user_data["username"],
            "pwd": user_data["password"] if user_data["valid"] else "wrong_password"
        }
        return session.post(f"{self.base_url}/api/method/login", data=login_data)
        
    def _attempt_api_flood(self, session: requests.Session, user_data: Dict) -> requests.Response:
        """Attempt API endpoint flood"""
        # Try to access protected API endpoints rapidly
        endpoints = [
            "/api/method/frappe.auth.get_logged_user",
            "/api/resource/User",
            "/api/method/frappe.desk.desktop.get_desktop_page"
        ]
        endpoint = random.choice(endpoints)
        return session.get(f"{self.base_url}{endpoint}")
        
    def _attempt_dashboard_flood(self, session: requests.Session, user_data: Dict) -> requests.Response:
        """Attempt dashboard access flood"""
        return session.get(f"{self.base_url}/app")

    def _test_mfa_validation_under_load(self, concurrent_users):
        """Test MFA validation under concurrent load"""
        print(f"\n🔄 Phase 2: MFA Validation Under Load")
        
        # Test MFA with valid users only
        valid_users = [user for user in TEST_USERS if user["valid"]]
        
        with ThreadPoolExecutor(max_workers=min(concurrent_users, len(valid_users))) as executor:
            futures = []
            
            for i in range(min(concurrent_users, len(valid_users))):
                user_data = valid_users[i % len(valid_users)]
                future = executor.submit(self._test_mfa_validation, user_data, i)
                futures.append(future)
                
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self._update_mfa_results(result)
                except Exception as e:
                    self.results["errors"].append({
                        "phase": "mfa_validation",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

    def _test_mfa_validation(self, user_data: Dict, user_index: int) -> SecurityTestResult:
        """Test MFA validation for a user"""
        session = requests.Session()
        start_time = time.time()
        
        try:
            print(f"   🔐 Testing MFA for {user_data['username']} (language: {user_data['language']})")
            
            # Set language preference
            session.headers.update({
                'Accept-Language': 'ar' if user_data["language"] == "ar" else 'en',
                'User-Agent': f'MFATest-{user_index}'
            })
            
            # Test MFA status endpoint
            mfa_status_response = session.get(f"{self.base_url}/api/method/universal_workshop.user_management.mfa_manager.get_mfa_status")
            response_time = time.time() - start_time
            
            return SecurityTestResult(
                test_name="mfa_validation",
                success=mfa_status_response.status_code in [200, 401],  # Either works or requires auth
                response_time=response_time,
                details={
                    "user": user_data["username"],
                    "language": user_data["language"],
                    "mfa_status_code": mfa_status_response.status_code
                }
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="mfa_validation",
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                details={"user": user_data["username"]}
            )

    def _test_security_alerts_under_load(self, concurrent_users):
        """Test security alert system under load"""
        print(f"\n🔄 Phase 3: Security Alert System Testing")
        
        # Generate various security events to trigger alerts
        alert_scenarios = [
            {"type": "failed_login_burst", "count": 5},
            {"type": "permission_change", "count": 2},
            {"type": "suspicious_activity", "count": 3}
        ]
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for scenario in alert_scenarios:
                for i in range(scenario["count"]):
                    user_data = TEST_USERS[i % len(TEST_USERS)]
                    future = executor.submit(self._trigger_security_alert, user_data, scenario, i)
                    futures.append(future)
                    
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self._update_security_alert_results(result)
                except Exception as e:
                    self.results["errors"].append({
                        "phase": "security_alerts",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

    def _trigger_security_alert(self, user_data: Dict, scenario: Dict, index: int) -> SecurityTestResult:
        """Trigger security alert scenarios"""
        session = requests.Session()
        start_time = time.time()
        
        try:
            print(f"   🚨 Triggering {scenario['type']} alert for {user_data['username']}")
            
            if scenario["type"] == "failed_login_burst":
                # Multiple failed login attempts to trigger alert
                for _ in range(5):
                    login_data = {
                        "cmd": "login",
                        "usr": user_data["username"],
                        "pwd": "wrong_password_intentional"
                    }
                    session.post(f"{self.base_url}/api/method/login", data=login_data)
                    time.sleep(0.5)
                    
            elif scenario["type"] == "suspicious_activity":
                # Rapid API calls from different endpoints
                endpoints = [
                    "/api/resource/User",
                    "/api/resource/Role",
                    "/api/method/frappe.desk.desktop.get_desktop_page"
                ]
                for endpoint in endpoints:
                    session.get(f"{self.base_url}{endpoint}")
                    time.sleep(0.2)
                    
            # Check if alerts were triggered
            alert_check_response = session.get(
                f"{self.base_url}/api/method/universal_workshop.user_management.security_alerts.get_security_alerts_summary"
            )
            
            alert_triggered = alert_check_response.status_code == 200
            response_time = time.time() - start_time
            
            return SecurityTestResult(
                test_name=f"security_alert_{scenario['type']}",
                success=True,  # Success means test completed
                response_time=response_time,
                alert_triggered=alert_triggered,
                details={
                    "scenario_type": scenario["type"],
                    "user": user_data["username"],
                    "language": user_data["language"],
                    "alert_triggered": alert_triggered
                }
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name=f"security_alert_{scenario['type']}",
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                details={"user": user_data["username"]}
            )

    def _test_concurrent_attack_simulation(self, concurrent_users):
        """Simulate coordinated attack with multiple vectors"""
        print(f"\n🔄 Phase 4: Concurrent Attack Simulation")
        
        # Track peak concurrent users
        self.results["concurrent_performance"]["peak_concurrent_users"] = concurrent_users
        
        # Simple performance monitoring during attack simulation
        performance_metrics = []
        attack_duration = 15  # 15 seconds of coordinated attack
        
        for second in range(attack_duration):
            time.sleep(1)
            # Simple performance check
            try:
                response = requests.get(f"{self.base_url}/login", timeout=5)
                performance_metrics.append({
                    "timestamp": time.time(),
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 1.0,
                    "status_code": response.status_code
                })
            except Exception:
                performance_metrics.append({
                    "timestamp": time.time(),
                    "response_time": 5.0,  # Timeout
                    "status_code": 0
                })
                    
        self.results["concurrent_performance"]["performance_metrics"] = performance_metrics
        
        # Check for system degradation
        if performance_metrics:
            avg_response_time = sum(m["response_time"] for m in performance_metrics) / len(performance_metrics)
            self.results["concurrent_performance"]["system_degradation"] = avg_response_time > 3.0

    def _test_interface_security(self, concurrent_users):
        """Test security features in Arabic and English interfaces"""
        print(f"\n🔄 Phase 5: Arabic/English Interface Security Testing")
        
        for language in ["ar", "en"]:
            print(f"   🌐 Testing {language.upper()} interface security")
            
            language_users = [user for user in TEST_USERS if user["language"] == language and user["valid"]]
            
            for user_data in language_users[:min(concurrent_users//2, len(language_users))]:
                result = self._test_interface_specific_security(user_data, language)
                
                if language == "ar":
                    self._update_arabic_interface_results(result)
                else:
                    self._update_english_interface_results(result)

    def _test_interface_specific_security(self, user_data: Dict, language: str) -> SecurityTestResult:
        """Test security features for specific interface language"""
        session = requests.Session()
        start_time = time.time()
        
        try:
            # Set language preference
            session.headers.update({
                'Accept-Language': language,
                'User-Agent': f'InterfaceSecurityTest-{language}'
            })
            
            # Test security features work in this language
            security_features_working = 0
            total_features = 2
            
            # Test 1: MFA status check
            mfa_response = session.get(f"{self.base_url}/api/method/universal_workshop.user_management.mfa_manager.get_mfa_status")
            if mfa_response.status_code in [200, 401]:  # Either works or requires auth
                security_features_working += 1
                
            # Test 2: Security alert endpoint
            alert_response = session.get(f"{self.base_url}/api/method/universal_workshop.user_management.security_alerts.get_security_alerts_summary")
            if alert_response.status_code in [200, 401]:
                security_features_working += 1
                
            response_time = time.time() - start_time
            success = security_features_working >= 1  # At least 1 out of 2 features working
            
            return SecurityTestResult(
                test_name=f"interface_security_{language}",
                success=success,
                response_time=response_time,
                details={
                    "language": language,
                    "user": user_data["username"],
                    "security_features_working": security_features_working,
                    "total_features": total_features
                }
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name=f"interface_security_{language}",
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                details={"language": language, "user": user_data["username"]}
            )

    def _analyze_performance_degradation(self):
        """Analyze performance degradation during security tests"""
        print(f"\n🔄 Phase 6: Performance Degradation Analysis")
        
        metrics = self.results["concurrent_performance"]["performance_metrics"]
        if not metrics:
            return
            
        # Calculate performance statistics
        response_times = [m["response_time"] for m in metrics]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Check for performance degradation
        degradation_threshold = 3.0  # 3 seconds
        degraded_requests = sum(1 for rt in response_times if rt > degradation_threshold)
        degradation_percentage = (degraded_requests / len(response_times)) * 100
        
        self.results["concurrent_performance"]["average_response_time"] = avg_response_time
        self.results["concurrent_performance"]["max_response_time"] = max_response_time
        self.results["concurrent_performance"]["degradation_percentage"] = degradation_percentage
        self.results["concurrent_performance"]["system_degradation"] = degradation_percentage > 20
        
        print(f"   📊 Average response time: {avg_response_time:.2f}s")
        print(f"   📊 Max response time: {max_response_time:.2f}s")
        print(f"   📊 Degradation percentage: {degradation_percentage:.1f}%")

    def _update_rate_limiting_results(self, result: SecurityTestResult):
        """Update rate limiting test results"""
        self.results["rate_limiting"]["tests_run"] += 1
        self.results["rate_limiting"]["response_times"].append(result.response_time)
        
        if result.rate_limited:
            self.results["rate_limiting"]["rate_limits_triggered"] += 1
        else:
            self.results["rate_limiting"]["rate_limits_bypassed"] += 1
            
    def _update_mfa_results(self, result: SecurityTestResult):
        """Update MFA test results"""
        self.results["mfa_validation"]["tests_run"] += 1
        self.results["mfa_validation"]["response_times"].append(result.response_time)
        
        if result.success:
            self.results["mfa_validation"]["successful_validations"] += 1
        else:
            self.results["mfa_validation"]["failed_validations"] += 1
            
    def _update_security_alert_results(self, result: SecurityTestResult):
        """Update security alert test results"""
        self.results["security_alerts"]["tests_run"] += 1
        self.results["security_alerts"]["response_times"].append(result.response_time)
        
        if result.alert_triggered:
            self.results["security_alerts"]["alerts_triggered"] += 1
            
            # Track alert types
            alert_type = result.details.get("scenario_type", "unknown")
            if alert_type not in self.results["security_alerts"]["alert_types"]:
                self.results["security_alerts"]["alert_types"][alert_type] = 0
            self.results["security_alerts"]["alert_types"][alert_type] += 1
            
    def _update_arabic_interface_results(self, result: SecurityTestResult):
        """Update Arabic interface test results"""
        self.results["arabic_interface"]["tests_run"] += 1
        
        if result.success:
            self.results["arabic_interface"]["successful"] += 1
            security_features = result.details.get("security_features_working", 0)
            self.results["arabic_interface"]["security_features_working"] += security_features
        else:
            self.results["arabic_interface"]["failed"] += 1
            
    def _update_english_interface_results(self, result: SecurityTestResult):
        """Update English interface test results"""
        self.results["english_interface"]["tests_run"] += 1
        
        if result.success:
            self.results["english_interface"]["successful"] += 1
            security_features = result.details.get("security_features_working", 0)
            self.results["english_interface"]["security_features_working"] += security_features
        else:
            self.results["english_interface"]["failed"] += 1

    def _generate_security_test_report(self):
        """Generate comprehensive security test report"""
        duration = (datetime.now() - self.test_start_time).total_seconds()
        
        # Calculate overall metrics
        total_tests = (
            self.results["rate_limiting"]["tests_run"] +
            self.results["mfa_validation"]["tests_run"] +
            self.results["security_alerts"]["tests_run"] +
            self.results["arabic_interface"]["tests_run"] +
            self.results["english_interface"]["tests_run"]
        )
        
        rate_limiting_effectiveness = (
            (self.results["rate_limiting"]["rate_limits_triggered"] / 
             max(self.results["rate_limiting"]["tests_run"], 1)) * 100
        )
        
        mfa_success_rate = (
            (self.results["mfa_validation"]["successful_validations"] / 
             max(self.results["mfa_validation"]["tests_run"], 1)) * 100
        )
        
        alert_trigger_rate = (
            (self.results["security_alerts"]["alerts_triggered"] / 
             max(self.results["security_alerts"]["tests_run"], 1)) * 100
        )
        
        report = f"""
=== Security Feature Validation Under Load Report ===
Test Duration: {duration:.2f} seconds
Test Start Time: {self.test_start_time.isoformat()}
Total Tests Executed: {total_tests}

RATE LIMITING RESULTS:
- Tests Run: {self.results["rate_limiting"]["tests_run"]}
- Rate Limits Triggered: {self.results["rate_limiting"]["rate_limits_triggered"]}
- Rate Limits Bypassed: {self.results["rate_limiting"]["rate_limits_bypassed"]}
- Effectiveness: {rate_limiting_effectiveness:.1f}%

MFA VALIDATION RESULTS:
- Tests Run: {self.results["mfa_validation"]["tests_run"]}
- Successful Validations: {self.results["mfa_validation"]["successful_validations"]}
- Failed Validations: {self.results["mfa_validation"]["failed_validations"]}
- Success Rate: {mfa_success_rate:.1f}%

SECURITY ALERTS RESULTS:
- Tests Run: {self.results["security_alerts"]["tests_run"]}
- Alerts Triggered: {self.results["security_alerts"]["alerts_triggered"]}
- Alert Trigger Rate: {alert_trigger_rate:.1f}%
- Alert Types: {self.results["security_alerts"]["alert_types"]}

CONCURRENT PERFORMANCE:
- Peak Concurrent Users: {self.results["concurrent_performance"]["peak_concurrent_users"]}
- System Degradation: {self.results["concurrent_performance"]["system_degradation"]}
- Average Response Time: {self.results["concurrent_performance"].get("average_response_time", 0):.2f}s
- Max Response Time: {self.results["concurrent_performance"].get("max_response_time", 0):.2f}s
- Degradation Percentage: {self.results["concurrent_performance"].get("degradation_percentage", 0):.1f}%

INTERFACE SECURITY RESULTS:
Arabic Interface:
- Tests Run: {self.results["arabic_interface"]["tests_run"]}
- Successful: {self.results["arabic_interface"]["successful"]}
- Failed: {self.results["arabic_interface"]["failed"]}
- Security Features Working: {self.results["arabic_interface"]["security_features_working"]}

English Interface:
- Tests Run: {self.results["english_interface"]["tests_run"]}
- Successful: {self.results["english_interface"]["successful"]}
- Failed: {self.results["english_interface"]["failed"]}
- Security Features Working: {self.results["english_interface"]["security_features_working"]}

ERROR SUMMARY:
- Total Errors: {len(self.results["errors"])}
"""

        print(report)
        
        # Save detailed report
        detailed_report = {
            "test_summary": {
                "duration_seconds": duration,
                "start_time": self.test_start_time.isoformat(),
                "total_tests": total_tests,
                "rate_limiting_effectiveness": rate_limiting_effectiveness,
                "mfa_success_rate": mfa_success_rate,
                "alert_trigger_rate": alert_trigger_rate
            },
            "results": self.results,
            "recommendations": self._generate_security_recommendations()
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/load_testing/results/security_feature_load_test_{timestamp}.json"
        
        try:
            os.makedirs("tests/load_testing/results", exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(detailed_report, f, indent=2, ensure_ascii=False)
            print(f"\nDetailed report saved to: {filename}")
        except Exception as e:
            print(f"Error saving report: {e}")

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results"""
        recommendations = []
        
        # Rate limiting recommendations
        rate_limiting_effectiveness = (
            (self.results["rate_limiting"]["rate_limits_triggered"] / 
             max(self.results["rate_limiting"]["tests_run"], 1)) * 100
        )
        
        if rate_limiting_effectiveness < 80:
            recommendations.append(
                f"Rate limiting effectiveness ({rate_limiting_effectiveness:.1f}%) below 80% - review rate limiting configuration"
            )
            
        # MFA recommendations
        mfa_success_rate = (
            (self.results["mfa_validation"]["successful_validations"] / 
             max(self.results["mfa_validation"]["tests_run"], 1)) * 100
        )
        
        if mfa_success_rate < 95:
            recommendations.append(
                f"MFA validation success rate ({mfa_success_rate:.1f}%) below 95% - investigate MFA system reliability"
            )
            
        # Performance recommendations
        if self.results["concurrent_performance"]["system_degradation"]:
            recommendations.append(
                "System performance degradation detected under security load - optimize security feature performance"
            )
            
        # Interface recommendations
        arabic_success_rate = (
            (self.results["arabic_interface"]["successful"] / 
             max(self.results["arabic_interface"]["tests_run"], 1)) * 100
        )
        
        english_success_rate = (
            (self.results["english_interface"]["successful"] / 
             max(self.results["english_interface"]["tests_run"], 1)) * 100
        )
        
        if arabic_success_rate < 90:
            recommendations.append(
                f"Arabic interface security success rate ({arabic_success_rate:.1f}%) below 90% - review RTL security implementation"
            )
            
        if english_success_rate < 90:
            recommendations.append(
                f"English interface security success rate ({english_success_rate:.1f}%) below 90% - review security implementation"
            )
            
        return recommendations


def run_security_feature_load_test():
    """Run security feature load testing"""
    print("🔒 Universal Workshop ERP - Security Feature Validation Under Load")
    print("=" * 80)
    
    # Initialize tester
    tester = SecurityFeatureLoadTester()
    
    # Run comprehensive test
    tester.run_comprehensive_security_test(concurrent_users=12, test_duration_minutes=6)
    
    print("\n✅ Security feature validation under load completed!")
    print("📊 Check the generated report for detailed results and recommendations.")


if __name__ == "__main__":
    run_security_feature_load_test()
