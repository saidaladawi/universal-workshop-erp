# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

"""
Unit tests for BootManager
"""

import unittest
import frappe
from frappe.test_runner import make_test_records
from universal_workshop.core.boot.boot_manager import BootManager, get_boot_manager


class TestBootManager(unittest.TestCase):
    """Test BootManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.boot_manager = BootManager()
    
    def test_boot_manager_initialization(self):
        """Test BootManager initialization"""
        self.assertIsInstance(self.boot_manager, BootManager)
        self.assertIsNone(self.boot_manager.setup_status)
        self.assertIsNone(self.boot_manager.license_info)
        self.assertIsNone(self.boot_manager.workshop_config)
    
    def test_get_boot_manager_singleton(self):
        """Test get_boot_manager returns singleton"""
        manager1 = get_boot_manager()
        manager2 = get_boot_manager()
        self.assertIs(manager1, manager2)
    
    def test_check_initial_setup_status(self):
        """Test check_initial_setup_status method"""
        status = self.boot_manager.check_initial_setup_status()
        
        # Should return a dictionary with required keys
        self.assertIsInstance(status, dict)
        self.assertIn("setup_complete", status)
        self.assertIn("workshop_exists", status)
        self.assertIn("admin_users_count", status)
    
    def test_get_workshop_configuration(self):
        """Test get_workshop_configuration method"""
        config = self.boot_manager.get_workshop_configuration()
        
        # Should return configuration dict
        self.assertIsInstance(config, dict)
        self.assertIn("name", config)
        self.assertIn("name_ar", config)
        self.assertIn("has_branding", config)
        
        # Should have default values
        self.assertEqual(config["name"], "Universal Workshop")
        self.assertEqual(config["name_ar"], "الورشة الشاملة")
    
    def test_get_license_information(self):
        """Test get_license_information method"""
        license_info = self.boot_manager.get_license_information()
        
        # Should return license info dict
        self.assertIsInstance(license_info, dict)
        self.assertIn("is_valid", license_info)
        self.assertIn("license_type", license_info)
        self.assertIn("status_message", license_info)
    
    def test_get_session_boot_info(self):
        """Test get_session_boot_info method"""
        session_info = self.boot_manager.get_session_boot_info()
        
        # Should return session info dict
        self.assertIsInstance(session_info, dict)
        # Note: Session info may be empty if session manager is not available
    
    def test_get_boot_info(self):
        """Test get_boot_info method"""
        bootinfo = {}
        result = self.boot_manager.get_boot_info(bootinfo)
        
        # Should update and return bootinfo
        self.assertIsInstance(result, dict)
        self.assertIn("setup_complete", result)
        self.assertIn("setup_status", result)
    
    def test_get_onboarding_data(self):
        """Test get_onboarding_data method"""
        result = self.boot_manager.get_onboarding_data()
        
        # Should return response dict
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
    
    def test_check_setup_status(self):
        """Test check_setup_status method"""
        result = self.boot_manager.check_setup_status()
        
        # Should return status dict
        self.assertIsInstance(result, dict)
        self.assertIn("needs_onboarding", result)
        self.assertIn("setup_complete", result)
        self.assertIn("has_license", result)
    
    def test_get_user_home_page(self):
        """Test get_user_home_page method"""
        result = self.boot_manager.get_user_home_page("Administrator")
        
        # Should return either None or a route string
        self.assertTrue(result is None or isinstance(result, str))


class TestBootManagerIntegration(unittest.TestCase):
    """Integration tests for BootManager"""
    
    def test_boot_info_with_mock_data(self):
        """Test boot info with mock workshop data"""
        boot_manager = get_boot_manager()
        
        # Create mock bootinfo
        bootinfo = {"test": True}
        result = boot_manager.get_boot_info(bootinfo)
        
        # Should preserve original data and add new data
        self.assertTrue(result.get("test"))
        self.assertIn("setup_complete", result)
    
    def test_error_handling(self):
        """Test error handling in boot manager"""
        boot_manager = BootManager()
        
        # Test with empty bootinfo
        result = boot_manager.get_boot_info({})
        self.assertIsInstance(result, dict)
        
        # Should handle gracefully even if setup is incomplete
        self.assertIn("setup_complete", result)


if __name__ == "__main__":
    unittest.main()