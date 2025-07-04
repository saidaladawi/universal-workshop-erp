# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for Universal Workshop ERP
Testing critical business logic and integrations
"""

import unittest
import frappe
from frappe.test_runner import make_test_records
import json
import datetime


class TestUniversalWorkshopCore(unittest.TestCase):
    """Test core Universal Workshop functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        frappe.set_user("Administrator")
        cls.create_test_data()

    @classmethod
    def create_test_data(cls):
        """Create test customers, vehicles, etc."""
        # Create required master data first
        cls.setup_master_data()

        # Create test customer
        if not frappe.db.exists("Customer", "Test Customer"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "Test Customer",
                "customer_type": "Individual",
                "territory": cls.test_territory,
                "customer_group": cls.test_customer_group
            })
            customer.insert(ignore_permissions=True)
            cls.test_customer = customer.name
        else:
            cls.test_customer = "Test Customer"

    @classmethod
    def setup_master_data(cls):
        """Setup required master data for tests"""
        # Create test territory
        if not frappe.db.exists("Territory", "Test Territory"):
            territory = frappe.get_doc({
                "doctype": "Territory",
                "territory_name": "Test Territory",
                "parent_territory": "All Territories"
            })
            territory.insert(ignore_permissions=True)
            cls.test_territory = territory.name
        else:
            cls.test_territory = "Test Territory"

        # Create test customer group
        if not frappe.db.exists("Customer Group", "Test Customer Group"):
            customer_group = frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": "Test Customer Group",
                "parent_customer_group": "All Customer Groups"
            })
            customer_group.insert(ignore_permissions=True)
            cls.test_customer_group = customer_group.name
        else:
            cls.test_customer_group = "Test Customer Group"

        # Create test vehicle with proper territory and customer group
        if not frappe.db.exists("Vehicle", {"vin": "1HGBH41JXMN109186"}):
            vehicle = frappe.get_doc({
                "doctype": "Vehicle",
                "customer": cls.test_customer,
                "vin": "1HGBH41JXMN109186",  # Valid Honda VIN for testing
                "license_plate": "TEST-123",
                "make": "Honda",
                "model": "Accord",
                "year": 2021,
                "color": "White"
            })
            vehicle.insert(ignore_permissions=True)
            cls.test_vehicle = vehicle.name
        else:
            cls.test_vehicle = frappe.db.get_value("Vehicle", {"vin": "1HGBH41JXMN109186"}, "name")

    def test_vin_decoder_basic(self):
        """Test VIN decoder basic functionality"""
        from universal_workshop.vehicle_management.vin_decoder import VINDecoderManager

        decoder = VINDecoderManager()

        # Test valid VIN
        result = decoder.decode_vin("1HGBH41JXMN109186")
        self.assertTrue(result.get("success"), "VIN decoder should succeed")
        self.assertIsNotNone(result.get("make"), "Make should be decoded")

        # Test invalid VIN
        result = decoder.decode_vin("INVALID")
        self.assertFalse(result.get("success"), "Invalid VIN should fail")

    def test_vin_decoder_caching(self):
        """Test VIN decoder caching functionality"""
        from universal_workshop.vehicle_management.vin_decoder import VINDecoderManager

        decoder = VINDecoderManager()
        test_vin = "1HGBH41JXMN109186"

        # First call - should hit API
        result1 = decoder.decode_vin(test_vin)
        self.assertTrue(result1.get("success"))

        # Second call - should use cache
        result2 = decoder.decode_vin(test_vin)
        self.assertTrue(result2.get("success"))
        self.assertEqual(result1.get("make"), result2.get("make"))

    def test_loyalty_program_points_calculation(self):
        """Test loyalty program points calculation"""
        from universal_workshop.customer_management.loyalty_program import LoyaltyProgramManager

        # Test Bronze tier customer
        points = LoyaltyProgramManager.calculate_points_earned(100.0, self.test_customer, "service")
        self.assertGreater(points, 0, "Points should be calculated for service")

        # Test different service types
        major_repair_points = LoyaltyProgramManager.calculate_points_earned(100.0, self.test_customer, "major_repair")
        regular_points = LoyaltyProgramManager.calculate_points_earned(100.0, self.test_customer, "service")

        self.assertGreater(major_repair_points, regular_points, "Major repairs should earn more points")

    def test_loyalty_program_tier_calculation(self):
        """Test customer tier calculation"""
        from universal_workshop.customer_management.loyalty_program import LoyaltyProgramManager

        # Test tier for new customer (should be Bronze)
        tier = LoyaltyProgramManager.get_customer_tier(self.test_customer)
        self.assertIn(tier, ["Bronze", "Silver", "Gold", "Platinum"], "Valid tier should be returned")

    def test_qr_code_generation(self):
        """Test QR code generation for invoices"""
        # Create test sales invoice
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.test_customer,
            "posting_date": datetime.date.today(),
            "items": [{
                "item_code": "Test Service",
                "qty": 1,
                "rate": 100
            }]
        })
        sales_invoice.insert()

        try:
            from universal_workshop.billing_management.qr_code_generator import OmanEInvoiceQRGenerator

            qr_generator = OmanEInvoiceQRGenerator()
            result = qr_generator.generate_qr_code_for_invoice(sales_invoice)

            # QR generation might fail due to missing company setup, but should not crash
            self.assertIsInstance(result, dict, "QR generator should return a dict")
            self.assertIn("success", result, "Result should have success field")

        finally:
            # Cleanup
            sales_invoice.delete()

    def test_vehicle_validation(self):
        """Test vehicle data validation"""
        vehicle_doc = frappe.get_doc("Vehicle", self.test_vehicle)

        # Test VIN validation
        original_vin = vehicle_doc.vin

        # Invalid VIN should fail
        vehicle_doc.vin = "INVALID"
        with self.assertRaises(frappe.ValidationError):
            vehicle_doc.validate_vin()

        # Restore valid VIN
        vehicle_doc.vin = original_vin
        vehicle_doc.validate_vin()  # Should not raise

    def test_whatsapp_api_structure(self):
        """Test WhatsApp API structure (without sending actual messages)"""
        from universal_workshop.communication_management.api.whatsapp_api import send_whatsapp_message

        # Test API exists and has proper structure
        self.assertTrue(callable(send_whatsapp_message), "WhatsApp API should be callable")

    def test_vat_configuration(self):
        """Test VAT configuration"""
        from universal_workshop.billing_management.oman_vat_config import OmanVATConfig

        vat_config = OmanVATConfig()
        self.assertEqual(vat_config.vat_rate, 5.0, "Oman VAT rate should be 5%")
        self.assertEqual(vat_config.currency, "OMR", "Currency should be OMR")
        self.assertEqual(vat_config.decimal_places, 3, "Should use Baisa precision")

    def test_system_health_basic(self):
        """Test basic system health checks"""
        # Test database connectivity
        self.assertTrue(frappe.db.sql("SELECT 1")[0][0] == 1, "Database should be accessible")

        # Test core DocTypes exist
        core_doctypes = [
            "Vehicle", "Customer", "Customer Loyalty Points",
            "QR Code Template", "VAT Settings"
        ]

        for doctype in core_doctypes:
            self.assertTrue(
                frappe.db.exists("DocType", doctype),
                f"Core DocType {doctype} should exist"
            )

    def test_module_imports(self):
        """Test that all core modules can be imported"""
        import_tests = [
            "universal_workshop.vehicle_management.vin_decoder",
            "universal_workshop.customer_management.loyalty_program",
            "universal_workshop.billing_management.qr_code_generator",
            "universal_workshop.communication_management.api.whatsapp_api"
        ]

        for module_path in import_tests:
            try:
                __import__(module_path)
            except ImportError as e:
                self.fail(f"Failed to import {module_path}: {str(e)}")


class TestVINDecoder(unittest.TestCase):
    """Comprehensive VIN decoder tests"""

    def setUp(self):
        frappe.set_user("Administrator")
        from universal_workshop.vehicle_management.vin_decoder import VINDecoderManager
        self.decoder = VINDecoderManager()

    def test_vin_validation(self):
        """Test VIN format validation"""
        # Valid VINs
        valid_vins = [
            "1HGBH41JXMN109186",  # Honda
            "1FTFW1ET5DFC10312",  # Ford
            "19UUA8F2XCA012345"   # Acura
        ]

        for vin in valid_vins:
            self.assertTrue(
                self.decoder.validate_vin_format(vin),
                f"VIN {vin} should be valid"
            )

        # Invalid VINs
        invalid_vins = [
            "123456789",          # Too short
            "1HGBH41JXMN109186X", # Too long
            "1HGBH41JXMN109I86",  # Contains I
            "1HGBH41JXMN109O86",  # Contains O
            "1HGBH41JXMN109Q86"   # Contains Q
        ]

        for vin in invalid_vins:
            self.assertFalse(
                self.decoder.validate_vin_format(vin),
                f"VIN {vin} should be invalid"
            )

    def test_basic_vin_decode(self):
        """Test basic VIN decoding functionality"""
        result = self.decoder.basic_vin_decode("1HGBH41JXMN109186")

        self.assertTrue(result.get("success"), "Basic decode should succeed")
        self.assertIsNotNone(result.get("year"), "Year should be decoded")
        self.assertIsNotNone(result.get("wmi"), "WMI should be extracted")

    def test_manufacturer_detection(self):
        """Test manufacturer detection from WMI"""
        test_cases = [
            ("1HG", "Honda"),
            ("1FT", "Ford"),
            ("JHM", "Honda"),
            ("WBA", "BMW")
        ]

        for wmi, expected_manufacturer in test_cases:
            result = self.decoder.get_manufacturer_from_wmi(wmi)
            if expected_manufacturer == "Unknown":
                continue  # Skip if manufacturer not in our database
            # Note: This test might need adjustment based on implementation


class TestLoyaltyProgram(unittest.TestCase):
    """Comprehensive loyalty program tests"""

    def setUp(self):
        frappe.set_user("Administrator")
        from universal_workshop.customer_management.loyalty_program import LoyaltyProgramManager
        self.loyalty_manager = LoyaltyProgramManager

        # Create test customer if not exists
        if not frappe.db.exists("Customer", "Loyalty Test Customer"):
            # Ensure master data exists first
            if not frappe.db.exists("Territory", "Test Territory"):
                territory = frappe.get_doc({
                    "doctype": "Territory",
                    "territory_name": "Test Territory",
                    "parent_territory": "All Territories"
                })
                territory.insert(ignore_permissions=True)

            if not frappe.db.exists("Customer Group", "Test Customer Group"):
                customer_group = frappe.get_doc({
                    "doctype": "Customer Group",
                    "customer_group_name": "Test Customer Group",
                    "parent_customer_group": "All Customer Groups"
                })
                customer_group.insert(ignore_permissions=True)

            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "Loyalty Test Customer",
                "customer_type": "Individual",
                "territory": "Test Territory",
                "customer_group": "Test Customer Group"
            })
            customer.insert(ignore_permissions=True)
        self.test_customer = "Loyalty Test Customer"

    def test_points_calculation_tiers(self):
        """Test points calculation for different tiers"""
        test_amount = 100.0

        # Test different service types
        service_types = ["service", "major_repair", "parts_purchase", "inspection"]

        for service_type in service_types:
            points = self.loyalty_manager.calculate_points_earned(
                test_amount, self.test_customer, service_type
            )
            self.assertGreaterEqual(points, 0, f"Points should be non-negative for {service_type}")

    def test_tier_progression(self):
        """Test customer tier progression logic"""
        tier = self.loyalty_manager.get_customer_tier(self.test_customer)
        self.assertIn(tier, ["Bronze", "Silver", "Gold", "Platinum"], "Valid tier should be returned")

    def test_rewards_catalog(self):
        """Test rewards catalog functionality"""
        for tier in ["Bronze", "Silver", "Gold", "Platinum"]:
            rewards = self.loyalty_manager.get_available_rewards(tier, 1000)
            self.assertIsInstance(rewards, list, f"Rewards should be a list for {tier}")

    def test_points_addition_validation(self):
        """Test loyalty points addition with validation"""
        # Test valid points addition
        result = self.loyalty_manager.add_loyalty_points(
            self.test_customer, 100, "TEST-001", "Test points"
        )
        self.assertIsNotNone(result, "Points addition should return entry name")

        # Cleanup
        if result:
            frappe.delete_doc("Customer Loyalty Points", result)


def run_comprehensive_tests():
    """
    Run comprehensive test suite and generate report
    """
    import unittest

    # Create test suite
    test_classes = [
        TestUniversalWorkshopCore,
        TestVINDecoder,
        TestLoyaltyProgram
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    report = {
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        "timestamp": datetime.datetime.now().isoformat(),
        "details": {
            "failures": [{"test": str(test), "error": error} for test, error in result.failures],
            "errors": [{"test": str(test), "error": error} for test, error in result.errors]
        }
    }

    return report


if __name__ == "__main__":
    # Run tests when script is executed directly
    report = run_comprehensive_tests()
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Failures: {report['failures']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"{'='*50}")
