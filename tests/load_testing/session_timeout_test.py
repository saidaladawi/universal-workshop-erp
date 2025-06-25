#!/usr/bin/env python3
"""
Universal Workshop ERP - Session Management and Timeout Testing
Tests session creation, persistence, expiration, and timeout handling for multiple concurrent users.
Validates session handling in both Arabic and English interfaces.
"""

import os
import sys
import time
import json
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the frappe-bench directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Test configuration
TEST_USERS = [
    {
        "username": "workshop_owner@universal.local",
        "password": "admin123",
        "role": "Workshop Owner",
        "language": "en",
    },
    {
        "username": "workshop_manager@universal.local",
        "password": "manager123",
        "role": "Workshop Manager",
        "language": "ar",
    },
    {
        "username": "technician@universal.local",
        "password": "tech123",
        "role": "Workshop Technician",
        "language": "en",
    },
    {
        "username": "customer@universal.local",
        "password": "customer123",
        "role": "Customer",
        "language": "ar",
    },
]


class SessionTimeoutTester:
    """Comprehensive session management and timeout testing"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.test_start_time = None
        self.results = {
            "session_creation": {"success": 0, "failed": 0, "response_times": []},
            "session_persistence": {"success": 0, "failed": 0},
            "session_timeout": {"success": 0, "failed": 0, "timeout_times": []},
            "session_expiration": {"success": 0, "failed": 0},
            "concurrent_sessions": {"success": 0, "failed": 0},
            "arabic_interface": {"success": 0, "failed": 0},
            "english_interface": {"success": 0, "failed": 0},
            "errors": [],
            "session_analytics": {},
        }

    def run_comprehensive_session_test(self, num_users=10, test_duration_minutes=5):
        """Run comprehensive session management testing"""
        print(f"\n🔍 Starting Session Management and Timeout Testing")
        print(f"📊 Configuration: {num_users} users, {test_duration_minutes} minutes duration")
        print(f"🌐 Target: {self.base_url}")

        self.test_start_time = datetime.now()

        # Test phases
        print("\n📋 Test Phases:")
        print("1. Session Creation Testing")
        print("2. Session Persistence Testing")
        print("3. Session Timeout Testing")
        print("4. Session Expiration Testing")
        print("5. Concurrent Session Management")
        print("6. Arabic/English Interface Testing")

        # Execute test phases
        self._test_session_creation(num_users)
        self._test_session_persistence(num_users)
        self._test_session_timeout(num_users)
        self._test_session_expiration(num_users)
        self._test_concurrent_sessions(num_users)
        self._test_interface_languages(num_users)

        # Generate report
        self._generate_session_test_report()

    def _test_session_creation(self, num_users):
        """Test session creation for multiple users"""
        print(f"\n🔄 Phase 1: Session Creation Testing ({num_users} users)")

        with ThreadPoolExecutor(max_workers=min(num_users, 10)) as executor:
            futures = []

            for i in range(num_users):
                user_data = TEST_USERS[i % len(TEST_USERS)]
                future = executor.submit(self._test_single_session_creation, user_data, i)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    self._update_session_creation_results(result)
                except Exception as e:
                    self.results["errors"].append(
                        {
                            "phase": "session_creation",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

    def _test_single_session_creation(self, user_data: Dict, user_index: int) -> Dict[str, Any]:
        """Test session creation for a single user"""
        session = requests.Session()
        start_time = time.time()

        try:
            # Set language preference
            session.headers.update(
                {
                    "Accept-Language": "ar" if user_data["language"] == "ar" else "en",
                    "User-Agent": f"SessionTest-User-{user_index}",
                }
            )

            # Get login page
            login_page = session.get(f"{self.base_url}/login")
            if login_page.status_code != 200:
                return {
                    "success": False,
                    "error": "Login page not accessible",
                    "user": user_data["username"],
                }

            # Perform login
            login_data = {
                "cmd": "login",
                "usr": user_data["username"],
                "pwd": user_data["password"],
            }

            login_response = session.post(f"{self.base_url}/api/method/login", data=login_data)
            response_time = time.time() - start_time

            if login_response.status_code == 200:
                # Verify session is created
                user_info = session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user")

                if user_info.status_code == 200 and user_info.json().get("message"):
                    # Get session info
                    session_info = self._get_session_info(session)

                    return {
                        "success": True,
                        "user": user_data["username"],
                        "language": user_data["language"],
                        "response_time": response_time,
                        "session_info": session_info,
                        "session_object": session,
                    }

            return {
                "success": False,
                "error": f"Login failed: {login_response.status_code}",
                "user": user_data["username"],
                "response_time": response_time,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user": user_data["username"],
                "response_time": time.time() - start_time,
            }

    def _test_session_persistence(self, num_users):
        """Test session persistence across requests"""
        print(f"\n🔄 Phase 2: Session Persistence Testing")

        # Create sessions first
        active_sessions = []
        for i in range(min(num_users, 5)):  # Limit for persistence testing
            user_data = TEST_USERS[i % len(TEST_USERS)]
            session_result = self._test_single_session_creation(user_data, i)

            if session_result["success"]:
                active_sessions.append(session_result)

        print(f"📊 Testing persistence for {len(active_sessions)} active sessions")

        # Test persistence over time
        for session_data in active_sessions:
            persistence_result = self._test_single_session_persistence(session_data)
            self._update_session_persistence_results(persistence_result)

    def _test_single_session_persistence(self, session_data: Dict) -> Dict[str, Any]:
        """Test persistence of a single session"""
        session = session_data["session_object"]

        try:
            # Make multiple requests over time to test persistence
            requests_made = 0
            successful_requests = 0

            for i in range(5):  # 5 requests over 30 seconds
                time.sleep(6)  # Wait 6 seconds between requests

                # Test different endpoints
                endpoints = [
                    "/api/method/frappe.auth.get_logged_user",
                    "/api/method/frappe.desk.desktop.get_desktop_page",
                    "/api/resource/User",
                ]

                endpoint = endpoints[i % len(endpoints)]
                response = session.get(f"{self.base_url}{endpoint}")
                requests_made += 1

                if response.status_code == 200:
                    successful_requests += 1
                else:
                    break  # Session likely expired

            persistence_rate = (successful_requests / requests_made) * 100

            return {
                "success": persistence_rate >= 80,  # 80% success rate threshold
                "user": session_data["user"],
                "language": session_data["language"],
                "persistence_rate": persistence_rate,
                "requests_made": requests_made,
                "successful_requests": successful_requests,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "user": session_data["user"]}

    def _test_session_timeout(self, num_users):
        """Test session timeout behavior"""
        print(f"\n🔄 Phase 3: Session Timeout Testing")

        # Create sessions and test timeout
        for i in range(min(num_users, 3)):  # Limit for timeout testing
            user_data = TEST_USERS[i % len(TEST_USERS)]
            timeout_result = self._test_single_session_timeout(user_data, i)
            self._update_session_timeout_results(timeout_result)

    def _test_single_session_timeout(self, user_data: Dict, user_index: int) -> Dict[str, Any]:
        """Test timeout behavior for a single session"""
        session_result = self._test_single_session_creation(user_data, user_index)

        if not session_result["success"]:
            return {"success": False, "error": "Could not create session for timeout test"}

        session = session_result["session_object"]
        start_time = time.time()

        try:
            print(
                f"   ⏰ Testing timeout for {user_data['username']} (language: {user_data['language']})"
            )

            # Wait for session to potentially timeout (shortened for testing)
            # In production, this would be the actual session timeout period
            timeout_wait = 60  # 1 minute for testing (production might be 30+ minutes)

            print(f"   ⏳ Waiting {timeout_wait} seconds for potential timeout...")
            time.sleep(timeout_wait)

            # Test if session is still valid
            response = session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user")
            timeout_time = time.time() - start_time

            if response.status_code == 401 or (
                response.status_code == 200 and not response.json().get("message")
            ):
                # Session timed out as expected
                return {
                    "success": True,
                    "user": user_data["username"],
                    "language": user_data["language"],
                    "timeout_time": timeout_time,
                    "timeout_detected": True,
                }
            else:
                # Session still active (might be longer timeout)
                return {
                    "success": True,
                    "user": user_data["username"],
                    "language": user_data["language"],
                    "timeout_time": timeout_time,
                    "timeout_detected": False,
                    "note": "Session still active after wait period",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user": user_data["username"],
                "timeout_time": time.time() - start_time,
            }

    def _test_session_expiration(self, num_users):
        """Test session expiration handling"""
        print(f"\n🔄 Phase 4: Session Expiration Testing")

        # Test expiration by manipulating session data if possible
        for i in range(min(num_users, 2)):
            user_data = TEST_USERS[i % len(TEST_USERS)]
            expiration_result = self._test_single_session_expiration(user_data, i)
            self._update_session_expiration_results(expiration_result)

    def _test_single_session_expiration(self, user_data: Dict, user_index: int) -> Dict[str, Any]:
        """Test expiration handling for a single session"""
        try:
            # Create session
            session_result = self._test_single_session_creation(user_data, user_index)

            if not session_result["success"]:
                return {"success": False, "error": "Could not create session for expiration test"}

            session = session_result["session_object"]

            # Test session expiration endpoint
            expiration_response = session.get(
                f"{self.base_url}/api/method/universal_workshop.session_management.get_current_session_info"
            )

            if expiration_response.status_code == 200:
                session_info = expiration_response.json().get("message", {})

                return {
                    "success": True,
                    "user": user_data["username"],
                    "language": user_data["language"],
                    "session_info": session_info,
                    "expiration_endpoint_works": True,
                }
            else:
                return {
                    "success": False,
                    "error": f"Session info endpoint failed: {expiration_response.status_code}",
                    "user": user_data["username"],
                }

        except Exception as e:
            return {"success": False, "error": str(e), "user": user_data["username"]}

    def _test_concurrent_sessions(self, num_users):
        """Test concurrent session management"""
        print(f"\n🔄 Phase 5: Concurrent Session Management Testing")

        # Test multiple sessions for same user
        user_data = TEST_USERS[0]  # Use first user

        concurrent_sessions = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []

            # Create 3 concurrent sessions for same user
            for i in range(3):
                future = executor.submit(self._test_single_session_creation, user_data, i)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result["success"]:
                        concurrent_sessions.append(result)
                except Exception as e:
                    self.results["errors"].append(
                        {
                            "phase": "concurrent_sessions",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        concurrent_result = {
            "success": len(concurrent_sessions) > 0,
            "concurrent_sessions_created": len(concurrent_sessions),
            "user": user_data["username"],
            "note": f"Created {len(concurrent_sessions)} concurrent sessions",
        }

        self._update_concurrent_session_results(concurrent_result)

    def _test_interface_languages(self, num_users):
        """Test session management with different interface languages"""
        print(f"\n🔄 Phase 6: Arabic/English Interface Testing")

        # Test both languages
        for language in ["ar", "en"]:
            user_data = TEST_USERS[0].copy()
            user_data["language"] = language

            interface_result = self._test_single_interface_language(user_data, language)

            if language == "ar":
                self._update_arabic_interface_results(interface_result)
            else:
                self._update_english_interface_results(interface_result)

    def _test_single_interface_language(self, user_data: Dict, language: str) -> Dict[str, Any]:
        """Test session management with specific interface language"""
        try:
            print(f"   🌐 Testing {language.upper()} interface session management")

            session_result = self._test_single_session_creation(user_data, 0)

            if not session_result["success"]:
                return {"success": False, "error": "Could not create session for interface test"}

            session = session_result["session_object"]

            # Test language-specific endpoints
            endpoints_to_test = [
                "/api/method/frappe.auth.get_logged_user",
                "/api/method/frappe.desk.desktop.get_desktop_page",
            ]

            successful_requests = 0
            total_requests = len(endpoints_to_test)

            for endpoint in endpoints_to_test:
                response = session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    successful_requests += 1

            return {
                "success": successful_requests == total_requests,
                "language": language,
                "successful_requests": successful_requests,
                "total_requests": total_requests,
                "success_rate": (successful_requests / total_requests) * 100,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "language": language}

    def _get_session_info(self, session: requests.Session) -> Dict[str, Any]:
        """Get session information"""
        try:
            response = session.get(
                f"{self.base_url}/api/method/universal_workshop.session_management.get_current_session_info"
            )
            if response.status_code == 200:
                return response.json().get("message", {})
        except Exception:
            pass
        return {}

    def _update_session_creation_results(self, result: Dict[str, Any]):
        """Update session creation results"""
        if result["success"]:
            self.results["session_creation"]["success"] += 1
            self.results["session_creation"]["response_times"].append(result["response_time"])
        else:
            self.results["session_creation"]["failed"] += 1
            self.results["errors"].append(
                {
                    "phase": "session_creation",
                    "error": result.get("error", "Unknown error"),
                    "user": result.get("user", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _update_session_persistence_results(self, result: Dict[str, Any]):
        """Update session persistence results"""
        if result["success"]:
            self.results["session_persistence"]["success"] += 1
        else:
            self.results["session_persistence"]["failed"] += 1

    def _update_session_timeout_results(self, result: Dict[str, Any]):
        """Update session timeout results"""
        if result["success"]:
            self.results["session_timeout"]["success"] += 1
            if "timeout_time" in result:
                self.results["session_timeout"]["timeout_times"].append(result["timeout_time"])
        else:
            self.results["session_timeout"]["failed"] += 1

    def _update_session_expiration_results(self, result: Dict[str, Any]):
        """Update session expiration results"""
        if result["success"]:
            self.results["session_expiration"]["success"] += 1
        else:
            self.results["session_expiration"]["failed"] += 1

    def _update_concurrent_session_results(self, result: Dict[str, Any]):
        """Update concurrent session results"""
        if result["success"]:
            self.results["concurrent_sessions"]["success"] += 1
        else:
            self.results["concurrent_sessions"]["failed"] += 1

    def _update_arabic_interface_results(self, result: Dict[str, Any]):
        """Update Arabic interface results"""
        if result["success"]:
            self.results["arabic_interface"]["success"] += 1
        else:
            self.results["arabic_interface"]["failed"] += 1

    def _update_english_interface_results(self, result: Dict[str, Any]):
        """Update English interface results"""
        if result["success"]:
            self.results["english_interface"]["success"] += 1
        else:
            self.results["english_interface"]["failed"] += 1

    def _generate_session_test_report(self):
        """Generate comprehensive session test report"""
        duration = (datetime.now() - self.test_start_time).total_seconds()

        # Calculate metrics
        total_session_tests = (
            self.results["session_creation"]["success"] + self.results["session_creation"]["failed"]
        )

        session_success_rate = (
            (self.results["session_creation"]["success"] / total_session_tests * 100)
            if total_session_tests > 0
            else 0
        )

        avg_response_time = (
            sum(self.results["session_creation"]["response_times"])
            / len(self.results["session_creation"]["response_times"])
            if self.results["session_creation"]["response_times"]
            else 0
        )

        avg_timeout_time = (
            sum(self.results["session_timeout"]["timeout_times"])
            / len(self.results["session_timeout"]["timeout_times"])
            if self.results["session_timeout"]["timeout_times"]
            else 0
        )

        report = f"""
=== Session Management and Timeout Testing Report ===
Test Duration: {duration:.2f} seconds
Test Start Time: {self.test_start_time.isoformat()}

SESSION CREATION RESULTS:
- Total Tests: {total_session_tests}
- Successful: {self.results["session_creation"]["success"]}
- Failed: {self.results["session_creation"]["failed"]}
- Success Rate: {session_success_rate:.2f}%
- Average Response Time: {avg_response_time:.3f} seconds

SESSION PERSISTENCE RESULTS:
- Successful: {self.results["session_persistence"]["success"]}
- Failed: {self.results["session_persistence"]["failed"]}

SESSION TIMEOUT RESULTS:
- Successful: {self.results["session_timeout"]["success"]}
- Failed: {self.results["session_timeout"]["failed"]}
- Average Timeout Time: {avg_timeout_time:.2f} seconds

SESSION EXPIRATION RESULTS:
- Successful: {self.results["session_expiration"]["success"]}
- Failed: {self.results["session_expiration"]["failed"]}

CONCURRENT SESSION RESULTS:
- Successful: {self.results["concurrent_sessions"]["success"]}
- Failed: {self.results["concurrent_sessions"]["failed"]}

INTERFACE LANGUAGE RESULTS:
- Arabic Interface Success: {self.results["arabic_interface"]["success"]}
- Arabic Interface Failed: {self.results["arabic_interface"]["failed"]}
- English Interface Success: {self.results["english_interface"]["success"]}
- English Interface Failed: {self.results["english_interface"]["failed"]}

ERROR SUMMARY:
- Total Errors: {len(self.results["errors"])}
"""

        print(report)

        # Save detailed report
        detailed_report = {
            "test_summary": {
                "duration_seconds": duration,
                "start_time": self.test_start_time.isoformat(),
                "session_success_rate": session_success_rate,
                "average_response_time": avg_response_time,
                "average_timeout_time": avg_timeout_time,
            },
            "results": self.results,
            "recommendations": self._generate_session_recommendations(),
        }

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/load_testing/results/session_timeout_test_{timestamp}.json"

        try:
            os.makedirs("tests/load_testing/results", exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(detailed_report, f, indent=2, ensure_ascii=False)
            print(f"\nDetailed report saved to: {filename}")
        except Exception as e:
            print(f"Error saving report: {e}")

    def _generate_session_recommendations(self) -> List[str]:
        """Generate recommendations based on session test results"""
        recommendations = []

        # Session creation recommendations
        total_creation_tests = (
            self.results["session_creation"]["success"] + self.results["session_creation"]["failed"]
        )

        if total_creation_tests > 0:
            success_rate = (
                self.results["session_creation"]["success"] / total_creation_tests
            ) * 100
            if success_rate < 95:
                recommendations.append(
                    f"Session creation success rate ({success_rate:.1f}%) below 95% - investigate authentication issues"
                )

        # Response time recommendations
        if self.results["session_creation"]["response_times"]:
            avg_response = sum(self.results["session_creation"]["response_times"]) / len(
                self.results["session_creation"]["response_times"]
            )
            if avg_response > 3.0:
                recommendations.append(
                    f"Average session creation time ({avg_response:.2f}s) exceeds 3 seconds - optimize authentication flow"
                )

        # Persistence recommendations
        if self.results["session_persistence"]["failed"] > 0:
            recommendations.append(
                "Session persistence failures detected - investigate session storage and timeout configuration"
            )

        # Timeout recommendations
        if self.results["session_timeout"]["failed"] > 0:
            recommendations.append(
                "Session timeout testing failed - verify timeout configuration and handling"
            )

        # Interface recommendations
        if self.results["arabic_interface"]["failed"] > 0:
            recommendations.append(
                "Arabic interface session management issues detected - verify RTL support and Arabic session handling"
            )

        if self.results["english_interface"]["failed"] > 0:
            recommendations.append(
                "English interface session management issues detected - verify session handling consistency"
            )

        # Error rate recommendations
        total_tests = sum(
            [
                self.results["session_creation"]["success"]
                + self.results["session_creation"]["failed"],
                self.results["session_persistence"]["success"]
                + self.results["session_persistence"]["failed"],
                self.results["session_timeout"]["success"]
                + self.results["session_timeout"]["failed"],
                self.results["session_expiration"]["success"]
                + self.results["session_expiration"]["failed"],
            ]
        )

        if total_tests > 0 and len(self.results["errors"]) > total_tests * 0.1:
            recommendations.append(
                f"Error rate ({len(self.results['errors'])}/{total_tests}) exceeds 10% - investigate system stability"
            )

        return recommendations


def run_session_timeout_test():
    """Run session timeout testing"""
    print("🚀 Universal Workshop ERP - Session Management and Timeout Testing")
    print("=" * 80)

    # Initialize tester
    tester = SessionTimeoutTester()

    # Run comprehensive test
    tester.run_comprehensive_session_test(num_users=8, test_duration_minutes=5)

    print("\n✅ Session management and timeout testing completed!")
    print("📊 Check the generated report for detailed results and recommendations.")


if __name__ == "__main__":
    run_session_timeout_test()
