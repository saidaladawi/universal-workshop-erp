"""
Test Role-Based Routing Implementation for Universal Workshop ERP

Tests the secure redirect manager and role-based routing functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the Universal Workshop app to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from universal_workshop.user_management.secure_redirect import (
        SecureRedirectManager,
        get_redirect_manager,
    )
except ImportError:
    # Mock frappe if not available in test environment
    class MockFrappe:
        def get_site_config(self):
            return {"host_name": "universal.local"}

        def log_error(self, *args, **kwargs):
            pass

        def get_roles(self, user):
            return []

    sys.modules["frappe"] = MockFrappe()
    sys.modules["frappe.utils"] = MockFrappe()

    from universal_workshop.user_management.secure_redirect import (
        SecureRedirectManager,
        get_redirect_manager,
    )


class TestRoleBasedRouting(unittest.TestCase):
    """Test role-based routing functionality"""

    def setUp(self):
        """Set up test environment"""
        self.redirect_manager = SecureRedirectManager()

    def test_workshop_owner_redirect(self):
        """Test Workshop Owner redirects to correct dashboard"""
        user_roles = ["Workshop Owner"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        # This should now redirect to the universal workshop dashboard
        expected_url = "/universal-workshop-dashboard"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Workshop Owner should redirect to {expected_url}, got {redirect_url}",
        )

    def test_system_manager_redirect(self):
        """Test System Manager redirects to workspace"""
        user_roles = ["System Manager"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/app/workspace/Workshop%20Management"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"System Manager should redirect to {expected_url}, got {redirect_url}",
        )

    def test_workshop_manager_redirect(self):
        """Test Workshop Manager redirects to workspace"""
        user_roles = ["Workshop Manager"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/app/workspace/Workshop%20Management"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Workshop Manager should redirect to {expected_url}, got {redirect_url}",
        )

    def test_technician_redirect(self):
        """Test Workshop Technician redirects to technician interface"""
        user_roles = ["Workshop Technician"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/technician"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Workshop Technician should redirect to {expected_url}, got {redirect_url}",
        )

    def test_customer_redirect(self):
        """Test Customer redirects to customer portal"""
        user_roles = ["Customer"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/customer-portal"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Customer should redirect to {expected_url}, got {redirect_url}",
        )

    def test_security_url_validation(self):
        """Test security validation blocks malicious URLs"""
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "//evil.com/steal-data",
            "http://malicious.com/phishing",
            "vbscript:msgbox('attack')",
            "file:///etc/passwd",
            "ftp://attacker.com/steal",
            "/redirect?url=http://evil.com",
            "/@attacker.com",
        ]

        for malicious_url in malicious_urls:
            validation_result = self.redirect_manager.validate_redirect_url(malicious_url)
            self.assertFalse(
                validation_result["is_valid"], f"Malicious URL should be blocked: {malicious_url}"
            )
            self.assertEqual(
                validation_result["safe_url"],
                "/app",
                f"Should fall back to default for: {malicious_url}",
            )

    def test_safe_url_validation(self):
        """Test that legitimate URLs are allowed"""
        safe_urls = [
            "/app",
            "/universal-workshop-dashboard",
            "/technician",
            "/customer-portal",
            "/app/service-order",
            "/app/customer",
        ]

        for safe_url in safe_urls:
            validation_result = self.redirect_manager.validate_redirect_url(safe_url)
            self.assertTrue(
                validation_result["is_valid"], f"Safe URL should be allowed: {safe_url}"
            )
            self.assertEqual(
                validation_result["safe_url"], safe_url, f"Safe URL should be preserved: {safe_url}"
            )

    def test_multiple_roles_priority(self):
        """Test role priority when user has multiple roles"""
        # Workshop Owner should take priority over other roles
        user_roles = ["Workshop Owner", "System Manager", "Customer"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/universal-workshop-dashboard"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Workshop Owner should take priority, expected {expected_url}, got {redirect_url}",
        )

    def test_default_redirect_fallback(self):
        """Test default redirect for unknown roles"""
        user_roles = ["Unknown Role", "Some Other Role"]
        redirect_url = self.redirect_manager._get_role_based_redirect(user_roles)

        expected_url = "/app"
        self.assertEqual(
            redirect_url,
            expected_url,
            f"Unknown roles should fall back to {expected_url}, got {redirect_url}",
        )


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
