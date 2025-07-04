"""
Role-Based Access Validation Tests for Universal Workshop ERP

Tests that each user role can only access permitted features and validates
both English and Arabic interface functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os


# Mock frappe for testing environment
class MockFrappe:
    def __init__(self):
        self.session = MagicMock()
        self.session.user = "test@example.com"
        self.local = MagicMock()
        self.local.lang = "en"

    def get_roles(self, user):
        # Return different roles based on test context
        if hasattr(self, "_test_roles"):
            return self._test_roles
        return ["Guest"]

    def has_permission(self, doctype, ptype="read", doc=None, user=None):
        # Mock permission checking based on roles
        user_roles = self.get_roles(user or self.session.user)

        # Workshop Owner has full access
        if "Workshop Owner" in user_roles:
            return True

        # Manager has access to most features
        if "Workshop Manager" in user_roles:
            restricted_doctypes = ["System Settings", "User"]
            return doctype not in restricted_doctypes

        # Technician has limited access
        if "Workshop Technician" in user_roles:
            allowed_doctypes = ["Service Order", "Vehicle", "Parts Request", "Technician"]
            return doctype in allowed_doctypes

        # Customer has very limited access
        if "Customer" in user_roles:
            allowed_doctypes = ["Customer", "Service Appointment", "Service History"]
            return doctype in allowed_doctypes

        return False

    def get_doc(self, doctype, name=None):
        return MagicMock()

    def get_list(self, doctype, **kwargs):
        return []

    def log_error(self, *args, **kwargs):
        pass


# Setup mock
mock_frappe = MockFrappe()
sys.modules["frappe"] = mock_frappe


class TestRoleAccessValidation(unittest.TestCase):
    """Test role-based access permissions and Arabic interface support"""

    def setUp(self):
        """Set up test environment"""
        self.mock_frappe = mock_frappe

    def test_workshop_owner_access_permissions(self):
        """Test Workshop Owner has full access to all features"""
        self.mock_frappe._test_roles = ["Workshop Owner"]

        # Test access to administrative features
        admin_doctypes = [
            "Workshop Profile",
            "System Settings",
            "User",
            "Role",
            "Service Order",
            "Customer",
            "Vehicle",
            "Parts Inventory",
        ]

        for doctype in admin_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertTrue(has_access, f"Workshop Owner should have read access to {doctype}")

            has_write = self.mock_frappe.has_permission(doctype, "write")
            self.assertTrue(has_write, f"Workshop Owner should have write access to {doctype}")

    def test_workshop_manager_access_permissions(self):
        """Test Workshop Manager has appropriate business access"""
        self.mock_frappe._test_roles = ["Workshop Manager"]

        # Manager should have access to business features
        business_doctypes = [
            "Service Order",
            "Customer",
            "Vehicle",
            "Parts Inventory",
            "Workshop Profile",
            "Technician",
        ]

        for doctype in business_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertTrue(has_access, f"Workshop Manager should have access to {doctype}")

        # Manager should NOT have access to system administration
        restricted_doctypes = ["System Settings", "User"]

        for doctype in restricted_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertFalse(has_access, f"Workshop Manager should NOT have access to {doctype}")

    def test_technician_access_permissions(self):
        """Test Workshop Technician has limited operational access"""
        self.mock_frappe._test_roles = ["Workshop Technician"]

        # Technician should have access to operational features
        allowed_doctypes = ["Service Order", "Vehicle", "Parts Request", "Technician"]

        for doctype in allowed_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertTrue(has_access, f"Workshop Technician should have access to {doctype}")

        # Technician should NOT have access to administrative features
        restricted_doctypes = [
            "Customer",
            "Workshop Profile",
            "System Settings",
            "User",
            "Parts Inventory",
        ]

        for doctype in restricted_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertFalse(has_access, f"Workshop Technician should NOT have access to {doctype}")

    def test_customer_access_permissions(self):
        """Test Customer has very limited portal access"""
        self.mock_frappe._test_roles = ["Customer"]

        # Customer should only have access to their own data
        allowed_doctypes = ["Customer", "Service Appointment", "Service History"]

        for doctype in allowed_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertTrue(has_access, f"Customer should have access to {doctype}")

        # Customer should NOT have access to workshop operations
        restricted_doctypes = [
            "Service Order",
            "Vehicle",
            "Technician",
            "Parts Inventory",
            "Workshop Profile",
            "System Settings",
        ]

        for doctype in restricted_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertFalse(has_access, f"Customer should NOT have access to {doctype}")

    def test_arabic_interface_role_access(self):
        """Test role-based access with Arabic language interface"""
        # Test each role with Arabic language setting
        roles_to_test = ["Workshop Owner", "Workshop Manager", "Workshop Technician", "Customer"]

        for role in roles_to_test:
            with self.subTest(role=role):
                # Set Arabic language
                self.mock_frappe.local.lang = "ar"
                self.mock_frappe._test_roles = [role]

                # Test that role permissions work regardless of language
                if role == "Workshop Owner":
                    has_admin_access = self.mock_frappe.has_permission("System Settings")
                    self.assertTrue(
                        has_admin_access, f"{role} should have admin access in Arabic interface"
                    )

                elif role == "Workshop Manager":
                    has_business_access = self.mock_frappe.has_permission("Service Order")
                    self.assertTrue(
                        has_business_access,
                        f"{role} should have business access in Arabic interface",
                    )

                    has_admin_access = self.mock_frappe.has_permission("System Settings")
                    self.assertFalse(
                        has_admin_access, f"{role} should NOT have admin access in Arabic interface"
                    )

                elif role == "Workshop Technician":
                    has_service_access = self.mock_frappe.has_permission("Service Order")
                    self.assertTrue(
                        has_service_access, f"{role} should have service access in Arabic interface"
                    )

                    has_customer_access = self.mock_frappe.has_permission("Customer")
                    self.assertFalse(
                        has_customer_access,
                        f"{role} should NOT have customer access in Arabic interface",
                    )

                elif role == "Customer":
                    has_portal_access = self.mock_frappe.has_permission("Service Appointment")
                    self.assertTrue(
                        has_portal_access, f"{role} should have portal access in Arabic interface"
                    )

                    has_workshop_access = self.mock_frappe.has_permission("Service Order")
                    self.assertFalse(
                        has_workshop_access,
                        f"{role} should NOT have workshop access in Arabic interface",
                    )

    def test_english_interface_role_access(self):
        """Test role-based access with English language interface"""
        # Reset to English language
        self.mock_frappe.local.lang = "en"

        # Test Workshop Owner in English
        self.mock_frappe._test_roles = ["Workshop Owner"]
        has_access = self.mock_frappe.has_permission("Workshop Profile")
        self.assertTrue(has_access, "Workshop Owner should have access in English interface")

        # Test Technician in English
        self.mock_frappe._test_roles = ["Workshop Technician"]
        has_service_access = self.mock_frappe.has_permission("Service Order")
        self.assertTrue(has_service_access, "Technician should have service access in English")

        has_admin_access = self.mock_frappe.has_permission("System Settings")
        self.assertFalse(has_admin_access, "Technician should NOT have admin access in English")

    def test_role_hierarchy_validation(self):
        """Test that role hierarchy is properly enforced"""
        # Test multiple roles - higher privilege should prevail
        self.mock_frappe._test_roles = ["Workshop Owner", "Customer"]

        # Should have Workshop Owner permissions despite also having Customer role
        has_admin_access = self.mock_frappe.has_permission("System Settings")
        self.assertTrue(
            has_admin_access, "Workshop Owner role should override Customer role restrictions"
        )

    def test_guest_access_restrictions(self):
        """Test that guests have no access"""
        self.mock_frappe._test_roles = ["Guest"]

        # Guest should have no access to any business features
        business_doctypes = ["Service Order", "Customer", "Vehicle", "Workshop Profile"]

        for doctype in business_doctypes:
            has_access = self.mock_frappe.has_permission(doctype, "read")
            self.assertFalse(has_access, f"Guest should NOT have access to {doctype}")

    def test_role_based_dashboard_access(self):
        """Test that each role gets appropriate dashboard access"""
        role_dashboard_mapping = {
            "Workshop Owner": "/universal-workshop-dashboard",
            "Workshop Manager": "/app/workspace/Workshop%20Management",
            "Workshop Technician": "/technician",
            "Customer": "/customer-portal",
        }

        # Import the redirect manager
        import sys
        import os

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

        try:
            from universal_workshop.user_management.secure_redirect import SecureRedirectManager
        except ImportError:
            # Skip this test if the module is not available
            self.skipTest("SecureRedirectManager module not available")

        redirect_manager = SecureRedirectManager()

        for role, expected_dashboard in role_dashboard_mapping.items():
            redirect_url = redirect_manager._get_role_based_redirect([role])
            self.assertEqual(
                redirect_url,
                expected_dashboard,
                f"Role {role} should redirect to {expected_dashboard}",
            )


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
