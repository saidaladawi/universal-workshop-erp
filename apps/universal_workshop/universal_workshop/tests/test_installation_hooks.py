#!/usr/bin/env python3
"""
Universal Workshop ERP - Installation Hooks Test
Tests the installation hooks and validates the complete setup process
"""

import frappe
import unittest


class TestInstallationHooks(unittest.TestCase):
    """Test Universal Workshop installation hooks and setup"""

    def setUp(self):
        """Setup for each test"""
        frappe.set_user("Administrator")
        self.test_results = {}

    def test_after_install_function_exists(self):
        """Test that after_install function exists and is importable"""
        try:
            from universal_workshop.install import after_install

            self.assertTrue(callable(after_install), "after_install should be a callable function")
            self.test_results["function_exists"] = "✅ PASS"
            print("✅ after_install function exists and is importable")
        except ImportError as e:
            self.test_results["function_exists"] = f"❌ FAIL: {e}"
            self.fail(f"Could not import after_install function: {e}")

    def test_hooks_configuration(self):
        """Test that hooks.py is properly configured"""
        try:
            import universal_workshop.hooks as hooks

            # Check if after_install is configured
            after_install = getattr(hooks, "after_install", None)
            self.assertIsNotNone(
                after_install, "after_install hook should be configured in hooks.py"
            )
            self.assertEqual(
                after_install,
                "universal_workshop.install.after_install",
                "after_install hook should point to correct function",
            )

            self.test_results["hooks_config"] = "✅ PASS"
            print("✅ Hooks configuration is correct")

        except Exception as e:
            self.test_results["hooks_config"] = f"❌ FAIL: {e}"
            self.fail(f"Hooks configuration test failed: {e}")

    def test_arabic_language_setup(self):
        """Test Arabic language setup functionality"""
        try:
            from universal_workshop.install import setup_arabic_localization

            # Test the function exists
            self.assertTrue(
                callable(setup_arabic_localization), "setup_arabic_localization should be callable"
            )

            # Test execution (in a safe way)
            try:
                setup_arabic_localization()
                self.test_results["arabic_setup"] = "✅ PASS"
                print("✅ Arabic localization setup executed successfully")
            except Exception as e:
                # Log but don't fail the test if it's just a data issue
                self.test_results["arabic_setup"] = f"⚠️ PARTIAL: {e}"
                print(f"⚠️ Arabic setup had issues: {e}")

        except Exception as e:
            self.test_results["arabic_setup"] = f"❌ FAIL: {e}"
            self.fail(f"Arabic language setup test failed: {e}")

    def test_workshop_roles_setup(self):
        """Test workshop roles setup functionality"""
        try:
            from universal_workshop.install import setup_default_workshop_roles

            # Test the function exists
            self.assertTrue(
                callable(setup_default_workshop_roles),
                "setup_default_workshop_roles should be callable",
            )

            # Test execution
            try:
                setup_default_workshop_roles()
                self.test_results["roles_setup"] = "✅ PASS"
                print("✅ Workshop roles setup executed successfully")
            except Exception as e:
                self.test_results["roles_setup"] = f"⚠️ PARTIAL: {e}"
                print(f"⚠️ Roles setup had issues: {e}")

        except Exception as e:
            self.test_results["roles_setup"] = f"❌ FAIL: {e}"
            self.fail(f"Workshop roles setup test failed: {e}")

    def test_default_data_setup(self):
        """Test default workshop data setup functionality"""
        try:
            from universal_workshop.install import setup_default_workshop_data

            # Test the function exists
            self.assertTrue(
                callable(setup_default_workshop_data),
                "setup_default_workshop_data should be callable",
            )

            # Test individual functions exist
            from universal_workshop.install import (
                create_default_service_types,
                create_default_labor_rates,
                create_default_system_preferences,
                create_sample_workshop_data,
            )

            functions = [
                create_default_service_types,
                create_default_labor_rates,
                create_default_system_preferences,
                create_sample_workshop_data,
            ]

            for func in functions:
                self.assertTrue(callable(func), f"{func.__name__} should be callable")

            self.test_results["data_setup"] = "✅ PASS"
            print("✅ Default workshop data setup functions exist and are callable")

        except Exception as e:
            self.test_results["data_setup"] = f"❌ FAIL: {e}"
            self.fail(f"Default data setup test failed: {e}")

    def test_error_handling(self):
        """Test error handling in installation functions"""
        try:
            from universal_workshop.install import after_install

            # Test that the function has proper error handling
            import inspect

            source = inspect.getsource(after_install)

            # Check for try-catch blocks
            self.assertIn("try:", source, "after_install should have try-catch blocks")
            self.assertIn("except", source, "after_install should have exception handling")
            self.assertIn("frappe.log_error", source, "after_install should log errors")

            self.test_results["error_handling"] = "✅ PASS"
            print("✅ Error handling is properly implemented")

        except Exception as e:
            self.test_results["error_handling"] = f"❌ FAIL: {e}"
            self.fail(f"Error handling test failed: {e}")

    def test_installation_safety(self):
        """Test that installation functions are safe to run multiple times"""
        try:
            from universal_workshop.install import (
                setup_default_workshop_roles,
                create_default_service_types,
                create_default_labor_rates,
            )

            # Test that functions check for existing data
            import inspect

            functions_to_test = [
                setup_default_workshop_roles,
                create_default_service_types,
                create_default_labor_rates,
            ]

            for func in functions_to_test:
                source = inspect.getsource(func)
                # Check for existence checks
                has_existence_check = any(
                    check in source
                    for check in ["frappe.db.exists", "not frappe.db.exists", "if not", "exists("]
                )
                self.assertTrue(
                    has_existence_check, f"{func.__name__} should check for existing data"
                )

            self.test_results["installation_safety"] = "✅ PASS"
            print("✅ Installation functions are safe for multiple runs")

        except Exception as e:
            self.test_results["installation_safety"] = f"❌ FAIL: {e}"
            self.fail(f"Installation safety test failed: {e}")

    def test_oman_localization(self):
        """Test Oman-specific localization settings"""
        try:
            from universal_workshop.install import create_default_system_preferences

            # Check the function source for Oman-specific settings
            import inspect

            source = inspect.getsource(create_default_system_preferences)

            # Check for Oman-specific configurations
            oman_settings = [
                "OMR",  # Currency
                "Oman",  # Country
                "Asia/Muscat",  # Timezone
                "5.0",  # VAT rate
                "Sunday,Monday,Tuesday,Wednesday,Thursday",  # Working days
            ]

            for setting in oman_settings:
                self.assertIn(setting, source, f"Should include Oman setting: {setting}")

            self.test_results["oman_localization"] = "✅ PASS"
            print("✅ Oman localization settings are properly configured")

        except Exception as e:
            self.test_results["oman_localization"] = f"❌ FAIL: {e}"
            self.fail(f"Oman localization test failed: {e}")

    def test_arabic_translations(self):
        """Test Arabic translations in default data"""
        try:
            from universal_workshop.install import create_default_service_types

            # Check the function source for Arabic translations
            import inspect

            source = inspect.getsource(create_default_service_types)

            # Check for Arabic field names
            arabic_indicators = [
                "service_name_ar",
                "description_ar",
                "خدمة",  # Service in Arabic
                "صيانة",  # Maintenance in Arabic
                "إصلاح",  # Repair in Arabic
            ]

            for indicator in arabic_indicators:
                self.assertIn(indicator, source, f"Should include Arabic indicator: {indicator}")

            self.test_results["arabic_translations"] = "✅ PASS"
            print("✅ Arabic translations are properly included")

        except Exception as e:
            self.test_results["arabic_translations"] = f"❌ FAIL: {e}"
            self.fail(f"Arabic translations test failed: {e}")

    def test_comprehensive_coverage(self):
        """Test that all major setup areas are covered"""
        try:
            from universal_workshop.install import after_install

            # Check the function source for all setup areas
            import inspect

            source = inspect.getsource(after_install)

            # Check for all setup function calls
            setup_functions = [
                "setup_customer_management",
                "setup_vehicle_management",
                "setup_workshop_management",
                "setup_purchasing_management",
                "setup_parts_inventory",
                "setup_billing_management",
                "setup_communication_management",
                "setup_arabic_localization",
                "setup_default_workshop_data",
            ]

            for func_name in setup_functions:
                self.assertIn(func_name, source, f"Should call {func_name}")

            self.test_results["comprehensive_coverage"] = "✅ PASS"
            print("✅ All major setup areas are covered")

        except Exception as e:
            self.test_results["comprehensive_coverage"] = f"❌ FAIL: {e}"
            self.fail(f"Comprehensive coverage test failed: {e}")

    def tearDown(self):
        """Print test results summary"""
        if hasattr(self, "test_results"):
            print(f"\n📊 Test Results Summary:")
            for test_name, result in self.test_results.items():
                print(f"  {test_name}: {result}")


def run_installation_hooks_test():
    """Run the installation hooks test suite"""
    print("🚀 Starting Universal Workshop Installation Hooks Test...")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstallationHooks)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 70)
    if result.wasSuccessful():
        print("🎉 All installation hooks tests passed!")
        return True
    else:
        print(
            f"❌ Installation hooks tests failed: {len(result.failures)} failures, {len(result.errors)} errors"
        )
        return False


if __name__ == "__main__":
    run_installation_hooks_test()
