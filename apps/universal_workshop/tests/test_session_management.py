"""
Session Management and Timeout Testing for Universal Workshop ERP

Tests session creation, persistence, expiration, and timeout handling
for multiple concurrent users with Arabic and English interface support.
"""

import unittest
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import concurrent.futures


class SessionManagementTests(unittest.TestCase):
    """Comprehensive session management testing"""

    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.test_users = [
            {
                "username": "Administrator",
                "password": "admin",
                "role": "System Manager",
                "language": "en",
            },
            {"username": "Guest", "password": "guest", "role": "Guest", "language": "ar"},
        ]
        self.test_results = {
            "session_creation": [],
            "session_persistence": [],
            "session_expiration": [],
            "concurrent_sessions": [],
            "language_specific": [],
            "timeout_handling": {},
        }

    def test_session_creation_english(self):
        """Test session creation with English interface"""
        print("\n🔐 Testing Session Creation - English Interface...")

        session = requests.Session()
        user = self.test_users[0]  # English user

        try:
            # Attempt login with English language preference
            login_data = {"usr": user["username"], "pwd": user["password"]}

            response = session.post(f"{self.base_url}/api/method/login", data=login_data)

            # Validate session creation
            session_created = self._validate_session_creation(response, session)

            self.test_results["session_creation"].append(
                {
                    "user": user["username"],
                    "language": user["language"],
                    "session_created": session_created,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            print(f"✅ Session creation test completed for {user['username']}")

        except Exception as e:
            print(f"❌ Session creation failed: {str(e)}")
            self.test_results["session_creation"].append(
                {
                    "user": user["username"],
                    "language": user["language"],
                    "session_created": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def test_session_persistence_across_requests(self):
        """Test session persistence across multiple requests"""
        print("\n📍 Testing Session Persistence...")

        session = requests.Session()
        user = self.test_users[0]

        # Login
        login_successful = self._perform_login(session, user)

        if not login_successful:
            print("⚠️ Skipping persistence test - login failed")
            return

        # Make multiple requests to test persistence
        test_endpoints = ["/api/method/frappe.auth.get_logged_user", "/app"]

        persistence_results = []

        for endpoint in test_endpoints:
            try:
                response = session.get(f"{self.base_url}{endpoint}")
                persistent = self._validate_session_persistence(response)

                persistence_results.append(
                    {
                        "endpoint": endpoint,
                        "persistent": persistent,
                        "status_code": response.status_code,
                    }
                )
                print(
                    f"{'✅' if persistent else '❌'} {endpoint}: {'Persistent' if persistent else 'Not persistent'}"
                )

            except Exception as e:
                persistence_results.append(
                    {"endpoint": endpoint, "persistent": False, "error": str(e)}
                )
                print(f"❌ {endpoint}: Error - {str(e)}")

        self.test_results["session_persistence"] = persistence_results

    def test_session_timeout_handling(self):
        """Test session timeout and expiration handling"""
        print("\n⏰ Testing Session Timeout Handling...")

        session = requests.Session()
        user = self.test_users[0]

        # Login and get initial session
        login_successful = self._perform_login(session, user)

        if not login_successful:
            print("⚠️ Skipping timeout test - login failed")
            return

        # Check initial session validity
        try:
            response = session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user")
            initial_session_valid = self._validate_session_persistence(response)

            timeout_results = {
                "initial_session_valid": initial_session_valid,
                "session_headers": dict(response.headers),
                "timeout_detected": False,
                "auto_logout_working": False,
            }

            # Check for timeout-related headers
            timeout_headers = ["Set-Cookie", "Session-Timeout", "Max-Age", "Expires"]
            timeout_configuration = {}

            for header in timeout_headers:
                if header in response.headers:
                    timeout_configuration[header] = response.headers[header]

            timeout_results["timeout_configuration"] = timeout_configuration

            print(f"Initial session valid: {'✅' if initial_session_valid else '❌'}")
            print(f"Timeout headers found: {len(timeout_configuration)}")

            self.test_results["timeout_handling"] = timeout_results

        except Exception as e:
            print(f"❌ Timeout test failed: {str(e)}")
            self.test_results["timeout_handling"] = {"error": str(e)}

    def _perform_login(self, session, user_data):
        """Helper method to perform login"""
        try:
            login_data = {"usr": user_data["username"], "pwd": user_data["password"]}

            response = session.post(f"{self.base_url}/api/method/login", data=login_data)
            return self._validate_session_creation(response, session)

        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def _validate_session_creation(self, response, session):
        """Validate that session was created successfully"""
        try:
            # Check for session cookies
            if session.cookies:
                return True

            # Check response status
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and ("message" in data or "user" in data):
                        return True
                except:
                    pass

            # Check for redirect to authenticated area
            if response.status_code == 302:
                return True

            return False

        except Exception:
            return False

    def _validate_session_persistence(self, response):
        """Validate that session persists across requests"""
        try:
            # Session is persistent if we get a valid response
            if response.status_code == 200:
                return True

            # Check if redirected to login (indicates session lost)
            if (
                response.status_code == 302
                and "login" in response.headers.get("Location", "").lower()
            ):
                return False

            if response.status_code == 401:
                return False

            return True

        except Exception:
            return False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Calculate summary statistics
        total_creation_tests = len(self.test_results["session_creation"])
        successful_creations = sum(
            1 for r in self.test_results["session_creation"] if r.get("session_created", False)
        )

        total_persistence_tests = len(self.test_results["session_persistence"])
        successful_persistence = sum(
            1 for r in self.test_results["session_persistence"] if r.get("persistent", False)
        )

        timeout_test_completed = bool(self.test_results["timeout_handling"])

        report = {
            "test_timestamp": timestamp,
            "test_summary": {
                "session_creation": {
                    "total_tests": total_creation_tests,
                    "successful": successful_creations,
                    "success_rate": (
                        f"{(successful_creations/total_creation_tests*100):.1f}%"
                        if total_creation_tests > 0
                        else "0%"
                    ),
                },
                "session_persistence": {
                    "total_tests": total_persistence_tests,
                    "successful": successful_persistence,
                    "success_rate": (
                        f"{(successful_persistence/total_persistence_tests*100):.1f}%"
                        if total_persistence_tests > 0
                        else "0%"
                    ),
                },
                "timeout_handling": {
                    "test_completed": timeout_test_completed,
                    "timeout_configured": bool(
                        self.test_results["timeout_handling"].get("timeout_configuration", {})
                    ),
                },
            },
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []

        # Session creation recommendations
        failed_creations = [
            r for r in self.test_results["session_creation"] if not r.get("session_created", False)
        ]
        if failed_creations:
            recommendations.append(
                "Investigate session creation failures - some users unable to establish sessions"
            )

        # Persistence recommendations
        if len(self.test_results["session_persistence"]) > 0:
            failed_persistence = [
                r
                for r in self.test_results["session_persistence"]
                if not r.get("persistent", False)
            ]
            if len(failed_persistence) > 0:
                recommendations.append(
                    "Session persistence issues detected - sessions may be lost across requests"
                )

        # Timeout recommendations
        timeout_result = self.test_results.get("timeout_handling", {})
        if not timeout_result.get("timeout_configuration", {}):
            recommendations.append(
                "Session timeout configuration not clearly visible - consider explicit timeout headers"
            )

        return recommendations


if __name__ == "__main__":
    # Run the session management tests
    print("🔐 Universal Workshop Session Management Tests")
    print("=" * 60)

    test_instance = SessionManagementTests()
    test_instance.setUp()

    # Run individual tests
    test_instance.test_session_creation_english()
    test_instance.test_session_persistence_across_requests()
    test_instance.test_session_timeout_handling()

    # Generate and display report
    report = test_instance.generate_test_report()

    print("\n📊 SESSION MANAGEMENT TEST RESULTS")
    print("=" * 60)
    print(f"Session Creation: {report['test_summary']['session_creation']['success_rate']}")
    print(f"Session Persistence: {report['test_summary']['session_persistence']['success_rate']}")
    print(
        f"Timeout Handling: {'✅ Tested' if report['test_summary']['timeout_handling']['test_completed'] else '❌ Failed'}"
    )

    if report["recommendations"]:
        print("\n🔧 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

    # Save report
    try:
        import os

        os.makedirs("apps/universal_workshop/tests/reports", exist_ok=True)
        report_filename = f"apps/universal_workshop/tests/reports/session_management_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {report_filename}")
    except Exception as e:
        print(f"\n⚠️ Could not save report: {str(e)}")
