"""
Test Suite for Business Name Binding and Owner Verification System
Tests business registration, government verification, and workshop binding functionality.
"""

import contextlib
import hashlib
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import frappe

# Import modules to test
from universal_workshop.license_management.doctype.business_registration.business_registration import (
    BusinessRegistration,
)
from universal_workshop.license_management.utils.business_binding import BusinessBindingManager
from universal_workshop.license_management.utils.government_api import GovernmentVerificationService


class TestBusinessRegistration(unittest.TestCase):
    """Test Business Registration DocType functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_business_data = {
            "business_name_en": "Al Khaleej Auto Service",
            "business_name_ar": "خدمة الخليج للسيارات",
            "business_license_number": "1234567",
            "registration_date": "2020-01-15",
            "business_type": "Individual Establishment",
            "owner_name_en": "Mohammed Al-Rashid",
            "owner_name_ar": "محمد الراشد",
            "owner_civil_id": "12345678",
            "primary_contact_name": "Mohammed Al-Rashid",
            "phone_number": "+968 24123456",
            "email": "mohammed@alkhaleej-auto.om",
        }

        # Clean up any existing test data
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up after tests"""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove test business registrations"""
        try:
            existing = frappe.db.get_list(
                "Business Registration",
                filters={
                    "business_license_number": self.test_business_data["business_license_number"]
                },
            )
            for record in existing:
                frappe.delete_doc("Business Registration", record.name, force=True)

            # Also clean audit logs
            frappe.db.sql(
                "DELETE FROM `tabLicense Audit Log` WHERE business_license = %s",
                (self.test_business_data["business_license_number"],),
            )

        except Exception:
            pass

    def test_business_registration_creation(self):
        """Test creating a new business registration"""
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.insert()

        # Verify business was created
        self.assertTrue(business.name)
        self.assertEqual(business.business_license_number, "1234567")
        self.assertEqual(business.business_name_ar, "خدمة الخليج للسيارات")
        self.assertTrue(business.verification_hash)

        # Verify naming series
        self.assertTrue(business.name.startswith("BR-"))

    def test_business_registration_without_license(self):
        """Test creating business registration without business license number (now optional)"""
        business_data_no_license = self.test_business_data.copy()
        del business_data_no_license["business_license_number"]  # Remove license number
        del business_data_no_license["email"]  # Remove email (also optional)

        business = frappe.new_doc("Business Registration")
        business.update(business_data_no_license)
        business.insert()

        # Verify business was created successfully
        self.assertTrue(business.name)
        self.assertEqual(business.business_name_ar, "خدمة الخليج للسيارات")
        self.assertTrue(business.verification_hash)
        self.assertIsNone(business.business_license_number)

        # Verify naming series
        self.assertTrue(business.name.startswith("BR-"))

    def test_business_license_validation(self):
        """Test business license number validation"""
        # Test invalid license format
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.business_license_number = "123"  # Too short

        with self.assertRaises(frappe.ValidationError):
            business.insert()

        # Test non-numeric license
        business.business_license_number = "ABC1234"
        with self.assertRaises(frappe.ValidationError):
            business.insert()

    def test_civil_id_validation(self):
        """Test civil ID validation"""
        # Test invalid civil ID format
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.owner_civil_id = "123"  # Too short

        with self.assertRaises(frappe.ValidationError):
            business.insert()

        # Test non-numeric civil ID
        business.owner_civil_id = "ABC12345"
        with self.assertRaises(frappe.ValidationError):
            business.insert()

    def test_arabic_text_validation(self):
        """Test Arabic text validation"""
        # Test missing Arabic text
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.business_name_ar = "English Text"  # Should be Arabic

        with self.assertRaises(frappe.ValidationError):
            business.insert()

    def test_phone_number_validation(self):
        """Test Oman phone number validation"""
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.phone_number = "+1234567890"  # Not Oman format

        with self.assertRaises(frappe.ValidationError):
            business.insert()

    def test_duplicate_license_prevention(self):
        """Test prevention of duplicate business licenses"""
        # Create first business
        business1 = frappe.new_doc("Business Registration")
        business1.update(self.test_business_data)
        business1.insert()

        # Try to create duplicate
        business2 = frappe.new_doc("Business Registration")
        business2.update(self.test_business_data)
        business2.owner_civil_id = "87654321"  # Different civil ID

        with self.assertRaises(frappe.ValidationError):
            business2.insert()

    def test_verification_hash_generation(self):
        """Test verification hash generation"""
        business = frappe.new_doc("Business Registration")
        business.update(self.test_business_data)
        business.insert()

        # Verify hash is generated
        self.assertTrue(business.verification_hash)
        self.assertEqual(len(business.verification_hash), 64)  # SHA256 hex

        # Verify hash is consistent
        expected_data = {
            "business_license": business.business_license_number,
            "owner_civil_id": business.owner_civil_id,
            "business_name_en": business.business_name_en,
            "business_name_ar": business.business_name_ar,
            "owner_name_en": business.owner_name_en,
            "owner_name_ar": business.owner_name_ar,
        }

        expected_hash = hashlib.sha256(
            json.dumps(expected_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        self.assertEqual(business.verification_hash, expected_hash)


class TestGovernmentVerification(unittest.TestCase):
    """Test Government API verification functionality"""

    def setUp(self):
        """Set up government verification service"""
        self.verification_service = GovernmentVerificationService()

    def test_business_license_verification_success(self):
        """Test successful business license verification"""
        result = self.verification_service.verify_business_license(
            "1234567", "Al Khaleej Auto Service", "خدمة الخليج للسيارات"
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["verified"])
        self.assertEqual(result["mci_number"], "MCI-1234567")
        self.assertEqual(result["business_name_official"], "Al Khaleej Auto Service")

    def test_business_license_verification_not_found(self):
        """Test business license not found scenario"""
        result = self.verification_service.verify_business_license(
            "1234000", "Test Business", "اختبار الأعمال"
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "LICENSE_NOT_FOUND")

    def test_business_license_verification_expired(self):
        """Test expired business license scenario"""
        result = self.verification_service.verify_business_license(
            "1234999", "Test Business", "اختبار الأعمال"
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "LICENSE_EXPIRED")

    def test_civil_id_verification_success(self):
        """Test successful civil ID verification"""
        result = self.verification_service.verify_civil_id(
            "12345678", "Mohammed Al-Rashid", "محمد الراشد"
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["verified"])
        self.assertTrue(result["name_match"])
        self.assertEqual(result["nationality"], "Omani")

    def test_civil_id_verification_not_found(self):
        """Test civil ID not found scenario"""
        result = self.verification_service.verify_civil_id("12340000", "Test Person", "اختبار شخص")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "CIVIL_ID_NOT_FOUND")

    def test_civil_id_verification_name_mismatch(self):
        """Test civil ID with name mismatch"""
        result = self.verification_service.verify_civil_id("12349999", "Wrong Name", "اسم خطأ")

        self.assertTrue(result["success"])
        self.assertFalse(result["verified"])
        self.assertFalse(result["name_match"])


class TestBusinessBinding(unittest.TestCase):
    """Test Business Binding functionality"""

    def setUp(self):
        """Set up test data for business binding"""
        self.binding_manager = BusinessBindingManager()

        # Create test business registration
        self.business_data = {
            "business_name_en": "Al Noor Auto Workshop",
            "business_name_ar": "ورشة النور للسيارات",
            "business_license_number": "9876543",
            "registration_date": "2020-01-15",
            "business_type": "Individual Establishment",
            "owner_name_en": "Ahmed Al-Noor",
            "owner_name_ar": "أحمد النور",
            "owner_civil_id": "87654321",
            "verification_status": "Verified",
            "government_verification_status": "Verified",
        }

        # Create test business
        self.business = frappe.new_doc("Business Registration")
        self.business.update(self.business_data)
        self.business.insert()

        # Test workshop and hardware data
        self.workshop_code = "WS-2024-0001"
        self.hardware_fingerprint = json.dumps(
            {
                "primary_hash": "abc123def456",
                "secondary_hash": "ghi789jkl012",
                "components": ["cpu", "motherboard", "mac"],
            }
        )
        self.license_key_hash = "license_key_hash_123"

        # Clean up any existing bindings
        self._cleanup_binding_data()

    def tearDown(self):
        """Clean up after binding tests"""
        self._cleanup_binding_data()

        # Remove test business
        with contextlib.suppress(Exception):
            frappe.delete_doc("Business Registration", self.business.name, force=True)

    def _cleanup_binding_data(self):
        """Clean up binding test data"""
        try:
            # Clean audit logs
            frappe.db.sql(
                "DELETE FROM `tabLicense Audit Log` WHERE workshop_code = %s", (self.workshop_code,)
            )
        except Exception:
            pass

    def test_successful_workshop_binding(self):
        """Test successful workshop-business binding"""
        result = self.binding_manager.bind_workshop_to_business(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
            self.license_key_hash,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["workshop_code"], self.workshop_code)
        self.assertEqual(result["business_name"], self.business_data["business_name_en"])
        self.assertTrue(result["binding_date"])

    def test_binding_with_unverified_business(self):
        """Test binding attempt with unverified business"""
        # Create unverified business
        unverified_business = frappe.new_doc("Business Registration")
        unverified_data = self.business_data.copy()
        unverified_data["business_license_number"] = "1111111"
        unverified_data["verification_status"] = "Pending"
        unverified_business.update(unverified_data)
        unverified_business.insert()

        try:
            result = self.binding_manager.bind_workshop_to_business(
                self.workshop_code, "1111111", self.hardware_fingerprint, self.license_key_hash
            )

            self.assertFalse(result["success"])
            self.assertIn("not verified", result["error"])

        finally:
            frappe.delete_doc("Business Registration", unverified_business.name, force=True)

    def test_workshop_binding_validation(self):
        """Test workshop binding validation"""
        # First bind the workshop
        bind_result = self.binding_manager.bind_workshop_to_business(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
            self.license_key_hash,
        )
        self.assertTrue(bind_result["success"])

        # Now validate the binding
        validation_result = self.binding_manager.validate_workshop_binding(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
        )

        self.assertTrue(validation_result["valid"])
        self.assertEqual(validation_result["workshop_code"], self.workshop_code)
        self.assertEqual(validation_result["business_name"], self.business_data["business_name_en"])

    def test_binding_validation_with_wrong_hardware(self):
        """Test binding validation with wrong hardware fingerprint"""
        # First bind the workshop
        bind_result = self.binding_manager.bind_workshop_to_business(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
            self.license_key_hash,
        )
        self.assertTrue(bind_result["success"])

        # Try to validate with wrong hardware
        wrong_hardware = json.dumps(
            {
                "primary_hash": "wrong_hash_123",
                "secondary_hash": "wrong_hash_456",
                "components": ["cpu", "motherboard", "mac"],
            }
        )

        validation_result = self.binding_manager.validate_workshop_binding(
            self.workshop_code, self.business_data["business_license_number"], wrong_hardware
        )

        self.assertFalse(validation_result["valid"])
        self.assertIn("fingerprint mismatch", validation_result["error"])

    def test_binding_conflict_detection(self):
        """Test detection of binding conflicts"""
        # Create another business
        other_business_data = self.business_data.copy()
        other_business_data["business_license_number"] = "5555555"
        other_business_data["owner_civil_id"] = "55555555"

        other_business = frappe.new_doc("Business Registration")
        other_business.update(other_business_data)
        other_business.insert()

        try:
            # Bind workshop to first business
            result1 = self.binding_manager.bind_workshop_to_business(
                self.workshop_code,
                self.business_data["business_license_number"],
                self.hardware_fingerprint,
                self.license_key_hash,
            )
            self.assertTrue(result1["success"])

            # Try to bind same workshop to different business
            result2 = self.binding_manager.bind_workshop_to_business(
                self.workshop_code,
                other_business_data["business_license_number"],
                self.hardware_fingerprint,
                self.license_key_hash,
            )

            self.assertFalse(result2["success"])
            self.assertIn("already bound", result2["error"])

        finally:
            frappe.delete_doc("Business Registration", other_business.name, force=True)


class TestIntegratedWorkflow(unittest.TestCase):
    """Test integrated workflow of business registration and binding"""

    def setUp(self):
        """Set up integrated test data"""
        self.business_data = {
            "business_name_en": "Integrated Test Workshop",
            "business_name_ar": "ورشة اختبار متكاملة",
            "business_license_number": "7777777",
            "registration_date": "2020-01-15",
            "business_type": "Individual Establishment",
            "owner_name_en": "Test Owner",
            "owner_name_ar": "مالك الاختبار",
            "owner_civil_id": "77777777",
        }

        self.workshop_code = "WS-INT-TEST-001"
        self.hardware_fingerprint = json.dumps(
            {
                "primary_hash": "integrated_test_hash",
                "secondary_hash": "integrated_secondary",
                "components": ["cpu", "motherboard", "mac"],
            }
        )

        # Clean up any existing data
        self._cleanup_integrated_data()

    def tearDown(self):
        """Clean up after integrated tests"""
        self._cleanup_integrated_data()

    def _cleanup_integrated_data(self):
        """Clean up integrated test data"""
        try:
            existing = frappe.db.get_list(
                "Business Registration",
                filters={"business_license_number": self.business_data["business_license_number"]},
            )
            for record in existing:
                frappe.delete_doc("Business Registration", record.name, force=True)

            frappe.db.sql(
                "DELETE FROM `tabLicense Audit Log` WHERE business_license = %s OR workshop_code = %s",
                (self.business_data["business_license_number"], self.workshop_code),
            )
        except Exception:
            pass

    @patch(
        "universal_workshop.license_management.utils.government_api.GovernmentVerificationService"
    )
    def test_complete_registration_and_binding_workflow(self, mock_verification_service):
        """Test complete workflow from registration to binding"""

        # Mock government verification
        mock_verification = MagicMock()
        mock_verification.verify_business_license.return_value = {
            "success": True,
            "verified": True,
            "mci_number": "MCI-7777777",
        }
        mock_verification.verify_civil_id.return_value = {
            "success": True,
            "verified": True,
            "name_match": True,
        }
        mock_verification_service.return_value = mock_verification

        # Step 1: Create business registration
        business = frappe.new_doc("Business Registration")
        business.update(self.business_data)
        business.insert()

        # Verify business was created
        self.assertTrue(business.name)
        self.assertEqual(business.verification_status, "Pending")

        # Step 2: Simulate government verification completion
        business.government_verification_status = "Verified"
        business.verification_status = "Verified"
        business.save()

        # Step 3: Bind workshop to business
        binding_manager = BusinessBindingManager()
        binding_result = binding_manager.bind_workshop_to_business(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
            "test_license_key_hash",
        )

        self.assertTrue(binding_result["success"])
        self.assertEqual(binding_result["workshop_code"], self.workshop_code)

        # Step 4: Validate the binding
        validation_result = binding_manager.validate_workshop_binding(
            self.workshop_code,
            self.business_data["business_license_number"],
            self.hardware_fingerprint,
        )

        self.assertTrue(validation_result["valid"])
        self.assertEqual(validation_result["business_name"], self.business_data["business_name_en"])

        # Step 5: Verify audit logs were created
        audit_logs = frappe.get_list(
            "License Audit Log",
            filters={"business_license": self.business_data["business_license_number"]},
        )
        self.assertGreater(len(audit_logs), 0)


if __name__ == "__main__":
    # Set up test environment
    frappe.init(site="test_site")
    frappe.connect()

    # Run tests
    unittest.main()
