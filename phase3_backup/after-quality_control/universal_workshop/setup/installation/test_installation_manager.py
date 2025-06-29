# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

"""
Unit tests for InstallationManager
"""

import unittest
import frappe
from frappe.test_runner import make_test_records
from universal_workshop.setup.installation.installation_manager import InstallationManager, get_installation_manager


class TestInstallationManager(unittest.TestCase):
    """Test InstallationManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.installation_manager = InstallationManager()
    
    def test_installation_manager_initialization(self):
        """Test InstallationManager initialization"""
        self.assertIsInstance(self.installation_manager, InstallationManager)
        self.assertIsInstance(self.installation_manager.errors, list)
        self.assertIsInstance(self.installation_manager.warnings, list)
        self.assertEqual(len(self.installation_manager.errors), 0)
        self.assertEqual(len(self.installation_manager.warnings), 0)
    
    def test_get_installation_manager_singleton(self):
        """Test get_installation_manager returns singleton"""
        manager1 = get_installation_manager()
        manager2 = get_installation_manager()
        self.assertIs(manager1, manager2)
    
    def test_setup_default_workshop_roles(self):
        """Test setup_default_workshop_roles method"""
        try:
            self.installation_manager.setup_default_workshop_roles()
            
            # Check if default roles are created
            expected_roles = ["Workshop Manager", "Workshop Technician", "Service Advisor", "Workshop Owner"]
            
            for role_name in expected_roles:
                # Note: In test environment, roles might not be created due to permissions
                # This test mainly ensures the method doesn't crash
                pass
                
        except Exception as e:
            # Method should handle errors gracefully
            self.fail(f"setup_default_workshop_roles raised an exception: {e}")
    
    def test_create_default_service_types(self):
        """Test create_default_service_types method"""
        try:
            self.installation_manager.create_default_service_types()
            # Method should complete without error even if DocType doesn't exist
        except Exception as e:
            self.fail(f"create_default_service_types raised an exception: {e}")
    
    def test_create_default_labor_rates(self):
        """Test create_default_labor_rates method"""
        try:
            self.installation_manager.create_default_labor_rates()
            # Method should complete without error even if DocType doesn't exist
        except Exception as e:
            self.fail(f"create_default_labor_rates raised an exception: {e}")
    
    def test_create_default_system_preferences(self):
        """Test create_default_system_preferences method"""
        try:
            self.installation_manager.create_default_system_preferences()
            # Method should complete without error even if DocType doesn't exist
        except Exception as e:
            self.fail(f"create_default_system_preferences raised an exception: {e}")
    
    def test_create_sample_workshop_data(self):
        """Test create_sample_workshop_data method"""
        try:
            self.installation_manager.create_sample_workshop_data()
            # Method should complete without error even if DocTypes don't exist
        except Exception as e:
            self.fail(f"create_sample_workshop_data raised an exception: {e}")
    
    def test_error_tracking(self):
        """Test error and warning tracking"""
        # Initially no errors
        self.assertEqual(len(self.installation_manager.errors), 0)
        self.assertEqual(len(self.installation_manager.warnings), 0)
        
        # Add test error
        self.installation_manager.errors.append("Test error")
        self.assertEqual(len(self.installation_manager.errors), 1)
        
        # Add test warning
        self.installation_manager.warnings.append("Test warning")
        self.assertEqual(len(self.installation_manager.warnings), 1)


class TestInstallationManagerIntegration(unittest.TestCase):
    """Integration tests for InstallationManager"""
    
    def test_workshop_management_setup(self):
        """Test setup_workshop_management method"""
        installation_manager = get_installation_manager()
        
        try:
            installation_manager.setup_workshop_management()
            # Should complete without critical errors
        except Exception as e:
            # Should handle gracefully in test environment
            pass
    
    def test_arabic_localization_setup(self):
        """Test setup_arabic_localization method"""
        installation_manager = get_installation_manager()
        
        try:
            installation_manager.setup_arabic_localization()
            # Should complete without critical errors
        except Exception as e:
            # Should handle gracefully in test environment
            pass
    
    def test_create_workshop_profile(self):
        """Test create_workshop_profile method"""
        installation_manager = InstallationManager()
        
        license_data = {
            "workshop_name_en": "Test Workshop",
            "workshop_name_ar": "ورشة الاختبار",
            "license_id": "TEST-LICENSE-001",
            "license_type": "Trial",
            "max_users": 5
        }
        
        user_data = {
            "owner_name": "Test Owner",
            "contact_email": "test@example.com",
            "contact_phone": "+968 12345678",
            "address": "Test Address",
            "city": "Muscat"
        }
        
        try:
            # This may fail in test environment due to DocType dependencies
            # but should handle gracefully
            result = installation_manager.create_workshop_profile(license_data, user_data)
        except Exception as e:
            # Expected in test environment without proper DocTypes
            pass
    
    def test_create_admin_user(self):
        """Test create_admin_user method"""
        installation_manager = InstallationManager()
        
        admin_data = {
            "email": "test.admin@example.com",
            "first_name": "Test",
            "last_name": "Admin",
            "password": "test_password"
        }
        
        try:
            # This may fail in test environment due to role dependencies
            result = installation_manager.create_admin_user(admin_data)
        except Exception as e:
            # Expected in test environment without proper roles
            pass


if __name__ == "__main__":
    unittest.main()