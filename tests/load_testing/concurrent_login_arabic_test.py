"""
Concurrent Login Testing with Arabic Interface Support
====================================================

Specialized load testing for simultaneous user logins with Arabic interface validation.
Tests authentication flow, session management, and RTL layout rendering under load.

Usage:
    python concurrent_login_arabic_test.py
    # Or with Locust:
    locust -f concurrent_login_arabic_test.py --host=http://localhost:8000
"""

import json
import time
import threading
import requests
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any
from locust import HttpUser, TaskSet, task, between, events

# Test data for Arabic interface testing
ARABIC_TEST_USERS = [
    {
        "username": "workshop_owner@universal.local",
        "password": "admin",
        "role": "Workshop Owner",
        "expected_redirect": "/universal-workshop-dashboard",
        "arabic_name": "مالك الورشة",
        "language": "ar",
    },
    {
        "username": "manager@universal.local",
        "password": "admin",
        "role": "Workshop Manager",
        "expected_redirect": "/app/workspace/Workshop%20Management",
        "arabic_name": "مدير الورشة",
        "language": "ar",
    },
    {
        "username": "technician@universal.local",
        "password": "admin",
        "role": "Workshop Technician",
        "expected_redirect": "/technician",
        "arabic_name": "فني الورشة",
        "language": "ar",
    },
    {
        "username": "customer@universal.local",
        "password": "admin",
        "role": "Customer",
        "expected_redirect": "/customer-portal",
        "arabic_name": "العميل",
        "language": "ar",
    },
]

ARABIC_TEST_DATA = {
    "customer_names": [
        "أحمد محمد السعيدي",
        "فاطمة علي البلوشي",
        "محمد سالم الشامسي",
        "خديجة يوسف الهنائي",
        "سعيد أحمد المقبالي",
        "مريم سالم الريامي",
    ],
    "workshop_names": [
        "ورشة الخليج للسيارات",
        "مركز الشامسي للصيانة",
        "ورشة النجاح التقنية",
        "مركز البلوشي للإطارات",
        "ورشة الريامي للكهرباء",
        "مركز السعيدي الشامل",
    ],
    "service_types": [
        "تغيير زيت المحرك",
        "صيانة الفرامل",
        "إصلاح المكيف",
        "فحص شامل",
        "تبديل الإطارات",
        "إصلاح الكهرباء",
    ],
}


class ConcurrentLoginTest:
    """Main concurrent login testing class"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_attempts": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "session_errors": 0,
            "arabic_ui_errors": 0,
            "redirect_errors": 0,
            "response_times": [],
            "errors": [],
        }
        self.test_start_time = None

    def run_concurrent_login_test(self, num_users=20, duration_seconds=60):
        """Run concurrent login test with multiple users"""
        print(
            f"Starting concurrent login test with {num_users} users for {duration_seconds} seconds"
        )
        print("Testing Arabic interface support and session management...")

        self.test_start_time = datetime.now()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            # Submit login tasks for each user type
            futures = []

            for i in range(num_users):
                user_data = ARABIC_TEST_USERS[i % len(ARABIC_TEST_USERS)].copy()
                user_data["session_id"] = f"test_session_{i}_{int(time.time())}"

                future = executor.submit(
                    self._simulate_user_login_session, user_data, duration_seconds
                )
                futures.append(future)

            # Wait for all tasks to complete
            concurrent.futures.wait(futures, timeout=duration_seconds + 30)

        self._generate_test_report()
        return self.results

    def _simulate_user_login_session(self, user_data: Dict, duration_seconds: int):
        """Simulate a complete user login session with Arabic interface"""
        session = requests.Session()
        session_start = time.time()

        try:
            while time.time() - session_start < duration_seconds:
                # Perform login test cycle
                login_result = self._test_login_flow(session, user_data)

                if login_result["success"]:
                    # Test Arabic interface elements
                    arabic_result = self._test_arabic_interface(session, user_data)

                    # Test role-based redirect
                    redirect_result = self._test_role_redirect(session, user_data)

                    # Update results
                    self._update_results(login_result, arabic_result, redirect_result)

                    # Test session management
                    self._test_session_management(session, user_data)

                    # Logout
                    self._perform_logout(session)

                else:
                    self._update_results(login_result, {"success": False}, {"success": False})

                # Wait before next iteration
                time.sleep(1)

        except Exception as e:
            self.results["errors"].append(
                {
                    "user": user_data["username"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _test_login_flow(self, session: requests.Session, user_data: Dict) -> Dict[str, Any]:
        """Test complete login flow with timing"""
        start_time = time.time()

        try:
            # Get login page first
            login_page = session.get(f"{self.base_url}/login")

            if login_page.status_code != 200:
                return {
                    "success": False,
                    "error": f"Login page not accessible: {login_page.status_code}",
                    "response_time": time.time() - start_time,
                }

            # Perform login
            login_data = {
                "usr": user_data["username"],
                "pwd": user_data["password"],
                "language": user_data["language"],
            }

            response = session.post(f"{self.base_url}/api/method/login", data=login_data)
            response_time = time.time() - start_time

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("message") == "Logged In":
                        return {
                            "success": True,
                            "response_time": response_time,
                            "session_data": result,
                        }
                except json.JSONDecodeError:
                    pass

            return {
                "success": False,
                "error": f"Login failed: {response.status_code}",
                "response_time": response_time,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "response_time": time.time() - start_time}

    def _test_arabic_interface(self, session: requests.Session, user_data: Dict) -> Dict[str, Any]:
        """Test Arabic interface elements and RTL layout"""
        try:
            # Request page with Arabic language
            headers = {"Accept-Language": "ar", "X-Frappe-Language": "ar"}

            response = session.get(f"{self.base_url}/app", headers=headers)

            if response.status_code == 200:
                content = response.text

                # Check for Arabic text and RTL support
                arabic_indicators = [
                    'dir="rtl"',
                    'lang="ar"',
                    "العربية",
                    "direction: rtl",
                    "text-align: right",
                ]

                arabic_support_count = sum(
                    1 for indicator in arabic_indicators if indicator in content
                )

                return {
                    "success": arabic_support_count >= 2,
                    "arabic_indicators_found": arabic_support_count,
                    "content_length": len(content),
                }

            return {"success": False, "error": f"Page not accessible: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _test_role_redirect(self, session: requests.Session, user_data: Dict) -> Dict[str, Any]:
        """Test role-based redirect functionality"""
        try:
            # Follow redirects after login
            response = session.get(f"{self.base_url}/app", allow_redirects=True)

            final_url = response.url
            expected_path = user_data["expected_redirect"]

            # Check if redirect is correct
            redirect_correct = expected_path in final_url or final_url.endswith(expected_path)

            return {
                "success": redirect_correct,
                "expected_redirect": expected_path,
                "actual_url": final_url,
                "redirect_chain": [r.url for r in response.history],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _test_session_management(self, session: requests.Session, user_data: Dict):
        """Test session management features"""
        try:
            # Test session info endpoint
            response = session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user")

            if response.status_code == 200:
                user_info = response.json()
                if user_info.get("message"):
                    # Session is valid
                    return {"success": True, "user_info": user_info["message"]}

            return {"success": False, "error": "Session validation failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _perform_logout(self, session: requests.Session):
        """Perform logout to clean up session"""
        try:
            session.post(f"{self.base_url}/api/method/logout")
        except Exception:
            pass  # Ignore logout errors for this test

    def _update_results(self, login_result: Dict, arabic_result: Dict, redirect_result: Dict):
        """Update test results with thread safety"""
        with threading.Lock():
            self.results["total_attempts"] += 1

            if login_result["success"]:
                self.results["successful_logins"] += 1
                self.results["response_times"].append(login_result["response_time"])
            else:
                self.results["failed_logins"] += 1
                self.results["errors"].append(
                    {
                        "type": "login_failure",
                        "error": login_result.get("error", "Unknown error"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if not arabic_result["success"]:
                self.results["arabic_ui_errors"] += 1
                self.results["errors"].append(
                    {
                        "type": "arabic_ui_error",
                        "error": arabic_result.get("error", "Arabic UI validation failed"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if not redirect_result["success"]:
                self.results["redirect_errors"] += 1
                self.results["errors"].append(
                    {
                        "type": "redirect_error",
                        "error": redirect_result.get("error", "Role redirect validation failed"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    def _generate_test_report(self):
        """Generate comprehensive test report"""
        duration = (datetime.now() - self.test_start_time).total_seconds()
        avg_response_time = (
            sum(self.results["response_times"]) / len(self.results["response_times"])
            if self.results["response_times"]
            else 0
        )

        min_response_time = (
            min(self.results["response_times"]) if self.results["response_times"] else 0
        )
        max_response_time = (
            max(self.results["response_times"]) if self.results["response_times"] else 0
        )

        report = f"""
=== Concurrent Login Testing with Arabic Interface - Report ===
Test Duration: {duration:.2f} seconds
Test Start Time: {self.test_start_time.isoformat()}

AUTHENTICATION RESULTS:
- Total Login Attempts: {self.results['total_attempts']}
- Successful Logins: {self.results['successful_logins']}
- Failed Logins: {self.results['failed_logins']}
- Success Rate: {(self.results['successful_logins']/self.results['total_attempts']*100):.2f}%

PERFORMANCE METRICS:
- Average Response Time: {avg_response_time:.3f} seconds
- Min Response Time: {min_response_time:.3f}s
- Max Response Time: {max_response_time:.3f}s

ARABIC INTERFACE VALIDATION:
- Arabic UI Errors: {self.results['arabic_ui_errors']}
- Arabic UI Success Rate: {((self.results['total_attempts']-self.results['arabic_ui_errors'])/self.results['total_attempts']*100):.2f}%

ROLE-BASED REDIRECT VALIDATION:
- Redirect Errors: {self.results['redirect_errors']}
- Redirect Success Rate: {((self.results['total_attempts']-self.results['redirect_errors'])/self.results['total_attempts']*100):.2f}%

SESSION MANAGEMENT:
- Session Errors: {self.results['session_errors']}

ERROR SUMMARY:
- Total Errors: {len(self.results['errors'])}
"""

        print(report)

        # Save detailed report
        detailed_report = {
            "test_summary": {
                "duration_seconds": duration,
                "start_time": self.test_start_time.isoformat(),
                "total_attempts": self.results["total_attempts"],
                "success_rate": (
                    (self.results["successful_logins"] / self.results["total_attempts"] * 100)
                    if self.results["total_attempts"] > 0
                    else 0
                ),
                "average_response_time": avg_response_time,
            },
            "results": self.results,
            "recommendations": self._generate_recommendations(),
        }

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/load_testing/results/concurrent_login_arabic_test_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(detailed_report, f, indent=2, ensure_ascii=False)
            print(f"\nDetailed report saved to: {filename}")
        except Exception as e:
            print(f"Error saving report: {e}")

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        success_rate = (
            (self.results["successful_logins"] / self.results["total_attempts"] * 100)
            if self.results["total_attempts"] > 0
            else 0
        )

        if success_rate < 95:
            recommendations.append(
                "Login success rate below 95% - investigate authentication issues"
            )

        if self.results["arabic_ui_errors"] > 0:
            recommendations.append(
                "Arabic UI errors detected - validate RTL layout and translation loading"
            )

        if self.results["redirect_errors"] > 0:
            recommendations.append(
                "Role-based redirect errors detected - verify role mapping configuration"
            )

        avg_response_time = (
            sum(self.results["response_times"]) / len(self.results["response_times"])
            if self.results["response_times"]
            else 0
        )
        if avg_response_time > 3.0:
            recommendations.append(
                "Average response time exceeds 3 seconds - optimize authentication flow"
            )

        if len(self.results["errors"]) > self.results["total_attempts"] * 0.1:
            recommendations.append("Error rate exceeds 10% - investigate system stability issues")

        return recommendations


# Locust integration for web UI testing
class ArabicLoginUser(HttpUser):
    """Locust user class for Arabic interface login testing"""

    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session"""
        self.user_data = ARABIC_TEST_USERS[0]  # Default to workshop owner

    @task
    def test_arabic_login_flow(self):
        """Test complete Arabic login flow"""
        # Login
        response = self.client.post(
            "/api/method/login",
            {
                "usr": self.user_data["username"],
                "pwd": self.user_data["password"],
                "language": "ar",
            },
        )

        if response.status_code == 200:
            # Test Arabic interface
            self.client.get("/app", headers={"Accept-Language": "ar", "X-Frappe-Language": "ar"})

            # Test role redirect
            self.client.get("/app", allow_redirects=True)

            # Logout
            self.client.post("/api/method/logout")


def run_standalone_test():
    """Run standalone concurrent login test"""
    test = ConcurrentLoginTest()

    print("=== Universal Workshop ERP - Concurrent Login Test ===")
    print("Testing Arabic interface support with multiple concurrent users\n")

    # Run test with different load levels
    test_scenarios = [
        {"users": 5, "duration": 30, "description": "Light load test"},
        {"users": 10, "duration": 60, "description": "Medium load test"},
        {"users": 20, "duration": 120, "description": "Heavy load test"},
    ]

    for scenario in test_scenarios:
        print(f"\n--- Running {scenario['description']} ---")
        print(f"Users: {scenario['users']}, Duration: {scenario['duration']}s")

        results = test.run_concurrent_login_test(
            num_users=scenario["users"], duration_seconds=scenario["duration"]
        )

        print(
            f"Results: {results['successful_logins']}/{results['total_attempts']} successful logins"
        )
        print(
            f"Arabic UI Success: {results['total_attempts'] - results['arabic_ui_errors']}/{results['total_attempts']}"
        )

        # Brief pause between scenarios
        time.sleep(5)


if __name__ == "__main__":
    run_standalone_test()
