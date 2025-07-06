# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
import unittest
import json
from frappe.utils import now, add_days
from universal_workshop.api.onboarding_wizard import (
    get_user_onboarding_progress,
    start_onboarding_wizard,
    validate_step_data,
    save_step_data,
    complete_onboarding
)

class TestOnboardingProgress(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create test user if not exists
        if not frappe.db.exists("User", "test_admin@workshop.com"):
            user = frappe.get_doc({
                "doctype": "User",
                "email": "test_admin@workshop.com",
                "first_name": "Test",
                "last_name": "Admin",
                "username": "testadmin",
                "send_welcome_email": 0,
                "user_type": "System User"
            })
            user.insert(ignore_permissions=True)
        
        # Clean up any existing test progress
        existing = frappe.db.exists("Onboarding Progress", {"user": "test_admin@workshop.com"})
        if existing:
            frappe.delete_doc("Onboarding Progress", existing, ignore_permissions=True)
        
        frappe.db.commit()
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up test progress records
        test_records = frappe.db.sql("""
            SELECT name FROM `tabOnboarding Progress` 
            WHERE user = 'test_admin@workshop.com'
        """, as_dict=True)
        
        for record in test_records:
            frappe.delete_doc("Onboarding Progress", record.name, ignore_permissions=True)
        
        frappe.db.commit()
    
    def test_start_onboarding_wizard(self):
        """Test starting new onboarding wizard"""
        frappe.set_user("test_admin@workshop.com")
        
        result = start_onboarding_wizard()
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["progress_id"])
        
        # Verify record was created
        progress_doc = frappe.get_doc("Onboarding Progress", result["progress_id"])
        self.assertEqual(progress_doc.user, "test_admin@workshop.com")
        self.assertEqual(progress_doc.status, "In Progress")
        self.assertEqual(progress_doc.current_step, 0)
    
    def test_get_user_progress(self):
        """Test getting user progress"""
        frappe.set_user("test_admin@workshop.com")
        
        # Start wizard first
        start_result = start_onboarding_wizard()
        self.assertTrue(start_result["success"])
        
        # Get progress
        progress = get_user_onboarding_progress()
        self.assertTrue(progress["exists"])
        self.assertEqual(progress["current_step"], 0)
        self.assertEqual(progress["progress_id"], start_result["progress_id"])
    
    def test_validate_license_step(self):
        """Test license verification step validation"""
        # Valid data
        valid_data = {
            "business_license": "1234567",
            "workshop_name": "Test Workshop",
            "workshop_name_ar": "ورشة تجريبية",
            "workshop_type": "General Repair",
            "governorate": "Muscat"
        }
        
        result = validate_step_data("license_verification", json.dumps(valid_data))
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Invalid data (missing fields)
        invalid_data = {
            "business_license": "123",  # Too short
            "workshop_name": "",  # Empty
        }
        
        result = validate_step_data("license_verification", json.dumps(invalid_data))
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
    
    def test_validate_admin_step(self):
        """Test admin account step validation"""
        # Valid data
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "mobile_number": "+96812345678",
            "username": "johndoe",
            "password": "Password123!"
        }
        
        result = validate_step_data("admin_account", json.dumps(valid_data))
        self.assertTrue(result["valid"])
        
        # Invalid data (weak password)
        invalid_data = valid_data.copy()
        invalid_data["password"] = "weak"
        
        result = validate_step_data("admin_account", json.dumps(invalid_data))
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
    
    def test_validate_workshop_step(self):
        """Test workshop configuration step validation"""
        # Valid data
        valid_data = {
            "working_hours_start": "08:00",
            "working_hours_end": "18:00",
            "weekend_days": "Friday-Saturday",
            "service_capacity_daily": 25,
            "currency": "OMR"
        }
        
        result = validate_step_data("workshop_config", json.dumps(valid_data))
        self.assertTrue(result["valid"])
        
        # Invalid data (end time before start time)
        invalid_data = valid_data.copy()
        invalid_data["working_hours_end"] = "07:00"
        
        result = validate_step_data("workshop_config", json.dumps(invalid_data))
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
    
    def test_save_step_data(self):
        """Test saving step data"""
        frappe.set_user("test_admin@workshop.com")
        
        # Start wizard
        start_result = start_onboarding_wizard()
        progress_id = start_result["progress_id"]
        
        # Save license step
        license_data = {
            "business_license": "1234567",
            "workshop_name": "Test Workshop",
            "workshop_name_ar": "ورشة تجريبية",
            "workshop_type": "General Repair",
            "governorate": "Muscat"
        }
        
        result = save_step_data(progress_id, "license_verification", json.dumps(license_data))
        self.assertTrue(result["success"])
        
        # Verify data was saved
        progress_doc = frappe.get_doc("Onboarding Progress", progress_id)
        form_data = json.loads(progress_doc.form_data)
        self.assertIn("license_verification", form_data)
        self.assertEqual(form_data["license_verification"]["business_license"], "1234567")
        
        completed_steps = json.loads(progress_doc.completed_steps)
        self.assertIn("license_verification", completed_steps)
    
    def test_complete_onboarding_flow(self):
        """Test complete onboarding flow"""
        frappe.set_user("test_admin@workshop.com")
        
        # Start wizard
        start_result = start_onboarding_wizard()
        progress_id = start_result["progress_id"]
        
        # Complete license step
        license_data = {
            "business_license": "7654321",
            "workshop_name": "Complete Test Workshop",
            "workshop_name_ar": "ورشة اختبار كاملة",
            "workshop_type": "General Repair",
            "governorate": "Muscat"
        }
        save_step_data(progress_id, "license_verification", json.dumps(license_data))
        
        # Complete admin step
        admin_data = {
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin.user@testworkshop.com",
            "mobile_number": "+96887654321",
            "username": "adminuser123",
            "password": "AdminPass123!",
            "default_language": "en",
            "timezone": "Asia/Muscat"
        }
        save_step_data(progress_id, "admin_account", json.dumps(admin_data))
        
        # Complete workshop config step
        config_data = {
            "working_hours_start": "08:00",
            "working_hours_end": "17:00",
            "weekend_days": "Friday-Saturday",
            "service_capacity_daily": 30,
            "currency": "OMR",
            "default_language": "en",
            "timezone": "Asia/Muscat",
            "selected_modules": ["parts_inventory", "user_management"]
        }
        save_step_data(progress_id, "workshop_config", json.dumps(config_data))
        
        # Complete onboarding
        completion_result = complete_onboarding(progress_id)
        self.assertTrue(completion_result["success"])
        self.assertIsNotNone(completion_result["workshop_code"])
        
        # Verify workshop profile was created
        workshop_profile = frappe.db.exists("Workshop Profile", {
            "workshop_code": completion_result["workshop_code"]
        })
        self.assertIsNotNone(workshop_profile)
        
        # Verify progress status
        progress_doc = frappe.get_doc("Onboarding Progress", progress_id)
        self.assertEqual(progress_doc.status, "Completed")
        self.assertIsNotNone(progress_doc.completed_at)
    
    def test_guest_onboarding(self):
        """Test guest user onboarding"""
        frappe.set_user("Guest")
        
        # Start guest wizard
        result = start_onboarding_wizard()
        self.assertTrue(result["success"])
        self.assertTrue(result["progress_id"].startswith("guest_"))
        
        # Save guest data
        guest_data = {
            "business_license": "9999999",
            "workshop_name": "Guest Workshop",
            "workshop_type": "General Repair"
        }
        
        save_result = save_step_data(result["progress_id"], "license_verification", json.dumps(guest_data))
        self.assertTrue(save_result["success"])
        
        # Complete guest onboarding
        completion_result = complete_onboarding(result["progress_id"])
        self.assertTrue(completion_result["success"])
        self.assertTrue(completion_result["workshop_code"].startswith("DEMO_"))
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation"""
        frappe.set_user("test_admin@workshop.com")
        
        # Create progress record
        progress = frappe.get_doc({
            "doctype": "Onboarding Progress",
            "user": "test_admin@workshop.com",
            "completed_steps": json.dumps(["license_verification", "admin_account"]),
            "status": "In Progress"
        })
        progress.insert(ignore_permissions=True)
        
        # Test percentage calculation
        percentage = progress.get_progress_percentage()
        expected = (2 / 3) * 100  # 2 out of 3 steps completed
        self.assertAlmostEqual(percentage, expected, places=2)
    
    def test_data_validation_edge_cases(self):
        """Test edge cases in data validation"""
        # Test empty JSON
        result = validate_step_data("license_verification", "{}")
        self.assertFalse(result["valid"])
        
        # Test invalid JSON
        result = validate_step_data("license_verification", "invalid json")
        self.assertFalse(result["valid"])
        
        # Test unknown step
        result = validate_step_data("unknown_step", "{}")
        self.assertTrue(result["valid"])  # Should pass if no specific validation exists
    
    def test_mobile_number_validation(self):
        """Test Oman mobile number validation"""
        from universal_workshop.api.onboarding_wizard import _validate_oman_mobile
        
        # Valid numbers
        valid_numbers = ["+96812345678", "+96887654321", "+96891234567"]
        for number in valid_numbers:
            self.assertTrue(_validate_oman_mobile(number))
        
        # Invalid numbers
        invalid_numbers = ["+9681234567", "96812345678", "+968123456789", "12345678"]
        for number in invalid_numbers:
            self.assertFalse(_validate_oman_mobile(number))
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        from universal_workshop.api.onboarding_wizard import _validate_password_strength
        
        # Strong password
        strong_password = "StrongPass123!"
        errors = _validate_password_strength(strong_password)
        self.assertEqual(len(errors), 0)
        
        # Weak passwords
        weak_passwords = ["weak", "12345678", "PASSWORD", "password123"]
        for password in weak_passwords:
            errors = _validate_password_strength(password)
            self.assertGreater(len(errors), 0)

def run_onboarding_tests():
    """Run all onboarding tests"""
    frappe.set_user("Administrator")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOnboardingProgress)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }

if __name__ == "__main__":
    unittest.main()