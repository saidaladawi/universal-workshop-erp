"""
Test MFA Manager
Universal Workshop ERP - User Management

Test cases for Multi-Factor Authentication functionality
"""

import unittest
import json
import frappe
from universal_workshop.user_management.mfa_manager import MFAManager


class TestMFAManager(unittest.TestCase):
    """Test cases for MFA Manager functionality"""

    def setUp(self):
        """Setup test environment"""
        self.mfa_manager = MFAManager()
        self.test_user_email = "test_mfa@universal.local"

        # Create test user if it doesn't exist
        if not frappe.db.exists("User", self.test_user_email):
            test_user = frappe.new_doc("User")
            test_user.email = self.test_user_email
            test_user.first_name = "Test"
            test_user.last_name = "MFA User"
            test_user.user_type = "System User"
            test_user.insert(ignore_permissions=True)

    def test_mfa_manager_initialization(self):
        """Test MFA manager initialization"""
        self.assertIsInstance(self.mfa_manager, MFAManager)
        self.assertEqual(self.mfa_manager.otp_validity_minutes, 5)
        self.assertEqual(self.mfa_manager.backup_codes_count, 10)
        self.assertEqual(self.mfa_manager.max_failed_attempts, 3)

    def test_enable_mfa_totp(self):
        """Test enabling TOTP MFA for user"""
        result = self.mfa_manager.enable_mfa_for_user(self.test_user_email, mfa_method="totp")

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("method"), "totp")
        self.assertIn("qr_code", result)
        self.assertIn("secret", result)
        self.assertIn("backup_codes", result)
        self.assertEqual(len(result["backup_codes"]), 10)

    def test_get_mfa_status_enabled(self):
        """Test getting MFA status for enabled user"""
        # First enable MFA
        self.mfa_manager.enable_mfa_for_user(self.test_user_email, "totp")

        # Check status
        status = self.mfa_manager.get_user_mfa_status(self.test_user_email)

        self.assertTrue(status.get("success"))
        self.assertTrue(status.get("enabled"))
        self.assertEqual(status.get("method"), "totp")
        self.assertIn("setup_date", status)
        self.assertEqual(status.get("backup_codes_remaining"), 10)

    def test_get_mfa_status_disabled(self):
        """Test getting MFA status for user without MFA"""
        # Ensure MFA is disabled
        if frappe.db.exists("User", self.test_user_email):
            user_doc = frappe.get_doc("User", self.test_user_email)
            if hasattr(user_doc, "mfa_settings"):
                user_doc.db_set("mfa_settings", None)

        status = self.mfa_manager.get_user_mfa_status(self.test_user_email)

        self.assertTrue(status.get("success"))
        self.assertFalse(status.get("enabled"))
        self.assertNotIn("method", status)

    def test_disable_mfa(self):
        """Test disabling MFA for user"""
        # First enable MFA
        self.mfa_manager.enable_mfa_for_user(self.test_user_email, "totp")

        # Then disable it
        result = self.mfa_manager.disable_mfa_for_user(self.test_user_email)

        self.assertTrue(result.get("success"))

        # Verify it's disabled
        status = self.mfa_manager.get_user_mfa_status(self.test_user_email)
        self.assertFalse(status.get("enabled"))

    def test_generate_backup_codes(self):
        """Test generating new backup codes"""
        # First enable MFA
        self.mfa_manager.enable_mfa_for_user(self.test_user_email, "totp")

        # Generate new backup codes
        result = self.mfa_manager.generate_new_backup_codes(self.test_user_email)

        self.assertTrue(result.get("success"))
        self.assertIn("backup_codes", result)
        self.assertEqual(len(result["backup_codes"]), 10)

        # Each backup code should be 8 characters
        for code in result["backup_codes"]:
            self.assertEqual(len(code), 8)
            self.assertTrue(code.isalnum())

    def test_backup_codes_format(self):
        """Test backup codes are properly formatted"""
        backup_codes = self.mfa_manager._generate_backup_codes()

        self.assertEqual(len(backup_codes), 10)

        for code in backup_codes:
            self.assertEqual(len(code), 8)
            self.assertTrue(code.isalnum())
            self.assertTrue(code.isupper())

    def test_invalid_user_email(self):
        """Test MFA operations with invalid user email"""
        invalid_email = "nonexistent@example.com"

        result = self.mfa_manager.enable_mfa_for_user(invalid_email, "totp")
        self.assertFalse(result.get("success"))
        self.assertIn("error", result)

    def test_mfa_settings_storage(self):
        """Test MFA settings are properly stored in User document"""
        result = self.mfa_manager.enable_mfa_for_user(self.test_user_email, "sms")
        self.assertTrue(result.get("success"))

        # Check if settings are stored
        user_doc = frappe.get_doc("User", self.test_user_email)

        if hasattr(user_doc, "mfa_settings") and user_doc.mfa_settings:
            mfa_settings = json.loads(user_doc.mfa_settings)

            self.assertTrue(mfa_settings.get("enabled"))
            self.assertEqual(mfa_settings.get("method"), "sms")
            self.assertIn("secret", mfa_settings)
            self.assertIn("backup_codes", mfa_settings)

    def tearDown(self):
        """Clean up test data"""
        try:
            # Clean up test user
            if frappe.db.exists("User", self.test_user_email):
                frappe.delete_doc("User", self.test_user_email, ignore_permissions=True)

            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Test cleanup error: {e}")


if __name__ == "__main__":
    unittest.main()
