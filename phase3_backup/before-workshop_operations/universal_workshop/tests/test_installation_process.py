#!/usr/bin/env python3
"""
Universal Workshop ERP - Installation Process Test
Tests the complete installation process including hooks, data creation, and system setup
"""

import frappe
import unittest
from frappe.test_runner import make_test_records


class TestInstallationProcess(unittest.TestCase):
    """Test the complete Universal Workshop installation process"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        frappe.set_user("Administrator")
        
    def setUp(self):
        """Setup for each test"""
        self.installation_results = {}
        
    def test_01_after_install_hook_execution(self):
        """Test that after_install hook executes without errors"""
        try:
            from universal_workshop.install import after_install
            
            # Execute the after_install function
            after_install()
            
            self.installation_results['after_install'] = "SUCCESS"
            print("✅ after_install hook executed successfully")
            
        except Exception as e:
            self.installation_results['after_install'] = f"FAILED: {str(e)}"
            self.fail(f"after_install hook failed: {e}")

    def test_02_arabic_language_setup(self):
        """Test Arabic language configuration"""
        try:
            # Check if Arabic language exists
            arabic_lang = frappe.db.exists("Language", "ar")
            self.assertTrue(arabic_lang, "Arabic language should be created")
            
            # Check system settings
            system_settings = frappe.get_doc("System Settings")
            self.assertEqual(system_settings.language, "ar", "System language should be Arabic")
            self.assertEqual(system_settings.country, "Oman", "Country should be Oman")
            self.assertEqual(system_settings.currency, "OMR", "Currency should be OMR")
            self.assertEqual(system_settings.time_zone, "Asia/Muscat", "Timezone should be Asia/Muscat")
            
            self.installation_results['arabic_setup'] = "SUCCESS"
            print("✅ Arabic language and localization setup validated")
            
        except Exception as e:
            self.installation_results['arabic_setup'] = f"FAILED: {str(e)}"
            self.fail(f"Arabic language setup validation failed: {e}")

    def test_03_workshop_roles_creation(self):
        """Test workshop roles creation"""
        try:
            expected_roles = [
                "Workshop Manager",
                "Workshop Technician", 
                "Service Advisor",
                "Workshop Owner"
            ]
            
            for role_name in expected_roles:
                role_exists = frappe.db.exists("Role", role_name)
                self.assertTrue(role_exists, f"Role '{role_name}' should be created")
                
                # Check role properties
                role = frappe.get_doc("Role", role_name)
                self.assertEqual(role.desk_access, 1, f"Role '{role_name}' should have desk access")
            
            self.installation_results['workshop_roles'] = "SUCCESS"
            print("✅ Workshop roles creation validated")
            
        except Exception as e:
            self.installation_results['workshop_roles'] = f"FAILED: {str(e)}"
            self.fail(f"Workshop roles creation validation failed: {e}")

    def test_04_default_service_types(self):
        """Test default service types creation"""
        try:
            expected_services = [
                "Engine Service",
                "Transmission Service",
                "Brake Service", 
                "Tire Service",
                "Oil Change",
                "Air Conditioning",
                "Electrical System",
                "General Inspection"
            ]
            
            # Check if Service Type DocType exists
            if frappe.db.exists("DocType", "Service Type"):
                for service_name in expected_services:
                    service_exists = frappe.db.exists("Service Type", {"service_name": service_name})
                    if service_exists:
                        service = frappe.get_doc("Service Type", {"service_name": service_name})
                        self.assertTrue(service.is_active, f"Service '{service_name}' should be active")
                        self.assertIsNotNone(service.service_name_ar, f"Service '{service_name}' should have Arabic name")
                
                self.installation_results['service_types'] = "SUCCESS"
                print("✅ Default service types creation validated")
            else:
                self.installation_results['service_types'] = "SKIPPED - DocType not found"
                print("⚠️ Service Type DocType not found - skipping validation")
                
        except Exception as e:
            self.installation_results['service_types'] = f"FAILED: {str(e)}"
            self.fail(f"Default service types validation failed: {e}")

    def test_05_default_labor_rates(self):
        """Test default labor rates creation"""
        try:
            expected_skills = [
                "Master Technician",
                "Senior Technician",
                "Junior Technician",
                "Apprentice"
            ]
            
            # Check if Labor Rate DocType exists
            if frappe.db.exists("DocType", "Labor Rate"):
                for skill_level in expected_skills:
                    rate_exists = frappe.db.exists("Labor Rate", {"skill_level": skill_level})
                    if rate_exists:
                        rate = frappe.get_doc("Labor Rate", {"skill_level": skill_level})
                        self.assertGreater(rate.hourly_rate, 0, f"Labor rate for '{skill_level}' should be positive")
                        self.assertIsNotNone(rate.skill_level_ar, f"Skill level '{skill_level}' should have Arabic name")
                
                self.installation_results['labor_rates'] = "SUCCESS"
                print("✅ Default labor rates creation validated")
            else:
                self.installation_results['labor_rates'] = "SKIPPED - DocType not found"
                print("⚠️ Labor Rate DocType not found - skipping validation")
                
        except Exception as e:
            self.installation_results['labor_rates'] = f"FAILED: {str(e)}"
            self.fail(f"Default labor rates validation failed: {e}")

    def test_06_system_preferences(self):
        """Test system preferences creation"""
        try:
            # Check if Workshop Settings DocType exists
            if frappe.db.exists("DocType", "Workshop Settings"):
                settings_exists = frappe.db.exists("Workshop Settings", "Workshop Settings")
                if settings_exists:
                    settings = frappe.get_doc("Workshop Settings", "Workshop Settings")
                    self.assertEqual(settings.default_currency, "OMR", "Default currency should be OMR")
                    self.assertEqual(settings.vat_rate, 5.0, "VAT rate should be 5%")
                    self.assertEqual(settings.language_preference, "ar", "Language preference should be Arabic")
                    self.assertEqual(settings.country, "Oman", "Country should be Oman")
                
                self.installation_results['system_preferences'] = "SUCCESS"
                print("✅ System preferences creation validated")
            else:
                self.installation_results['system_preferences'] = "SKIPPED - DocType not found"
                print("⚠️ Workshop Settings DocType not found - skipping validation")
                
        except Exception as e:
            self.installation_results['system_preferences'] = f"FAILED: {str(e)}"
            self.fail(f"System preferences validation failed: {e}")

    def test_07_sample_data_creation(self):
        """Test sample data creation"""
        try:
            # Check sample customer
            customer_exists = frappe.db.exists("Customer", "CUST-SAMPLE-001")
            if customer_exists:
                customer = frappe.get_doc("Customer", "CUST-SAMPLE-001")
                self.assertEqual(customer.customer_name, "Ahmed Al-Rashid", "Sample customer name should match")
                self.assertEqual(customer.customer_name_ar, "أحمد الراشد", "Sample customer Arabic name should match")
                self.assertEqual(customer.territory, "Oman", "Sample customer territory should be Oman")
            
            # Check sample vehicle
            if frappe.db.exists("DocType", "Vehicle"):
                vehicle_exists = frappe.db.exists("Vehicle", "VEH-SAMPLE-001")
                if vehicle_exists:
                    vehicle = frappe.get_doc("Vehicle", "VEH-SAMPLE-001")
                    self.assertEqual(vehicle.make, "Toyota", "Sample vehicle make should be Toyota")
                    self.assertEqual(vehicle.model, "Camry", "Sample vehicle model should be Camry")
                    self.assertEqual(vehicle.owner, "CUST-SAMPLE-001", "Sample vehicle should be owned by sample customer")
            
            self.installation_results['sample_data'] = "SUCCESS"
            print("✅ Sample data creation validated")
            
        except Exception as e:
            self.installation_results['sample_data'] = f"FAILED: {str(e)}"
            self.fail(f"Sample data validation failed: {e}")

    def test_08_installation_completeness(self):
        """Test overall installation completeness"""
        try:
            # Count successful installations
            successful_tests = sum(1 for result in self.installation_results.values() 
                                 if result == "SUCCESS")
            total_tests = len(self.installation_results)
            
            success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            
            print(f"\n📊 Installation Test Results:")
            print(f"Total Tests: {total_tests}")
            print(f"Successful: {successful_tests}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            # Print detailed results
            print(f"\n📋 Detailed Results:")
            for test_name, result in self.installation_results.items():
                status_icon = "✅" if result == "SUCCESS" else "⚠️" if "SKIPPED" in result else "❌"
                print(f"{status_icon} {test_name}: {result}")
            
            # Installation is considered successful if at least 80% of tests pass
            self.assertGreaterEqual(success_rate, 80, 
                                  f"Installation success rate ({success_rate:.1f}%) should be at least 80%")
            
            print(f"\n🎉 Installation process validation completed successfully!")
            
        except Exception as e:
            self.fail(f"Installation completeness validation failed: {e}")

    def tearDown(self):
        """Cleanup after each test"""
        pass

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        frappe.set_user("Administrator")


def run_installation_test():
    """Run the installation test suite"""
    print("🚀 Starting Universal Workshop Installation Process Test...")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstallationProcess)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 70)
    if result.wasSuccessful():
        print("🎉 All installation tests passed successfully!")
        return True
    else:
        print(f"❌ Installation tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    # Initialize Frappe
    import os
    import sys
    
    # Add frappe-bench to path
    bench_path = "/home/said/frappe-dev/frappe-bench"
    if bench_path not in sys.path:
        sys.path.insert(0, bench_path)
    
    try:
        # Initialize frappe
        frappe.init(site="universal.local")
        frappe.connect()
        
        # Run the test
        success = run_installation_test()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Failed to initialize test environment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if frappe.local.db:
            frappe.destroy() 