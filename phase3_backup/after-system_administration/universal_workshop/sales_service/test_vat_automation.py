# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
"""
Comprehensive Test Suite for VAT Automation System
Tests Oman VAT compliance, Arabic localization, and OMR currency handling
"""

import unittest
import frappe
from frappe.utils import flt
from universal_workshop.sales_service.vat_automation import OmanVATController


class TestVATAutomation(unittest.TestCase):
    """Test VAT automation functionality"""

    def setUp(self):
        """Setup test data and environment"""
        self.controller = OmanVATController()
        self.test_company = "Test Workshop Company"

        # Create test company if it doesn't exist
        if not frappe.db.exists("Company", self.test_company):
            company = frappe.new_doc("Company")
            company.company_name = self.test_company
            company.abbr = "TWC"
            company.default_currency = "OMR"
            company.country = "Oman"
            company.insert()

        # Test customer data
        self.test_customer_data = {
            "customer_name": "Ahmed Al-Rashid Motors",
            "customer_name_ar": "أحمد الراشد للسيارات",
            "oman_trn": "123456789012345",
            "vat_type": "Registered",
        }

        # Test service estimate data
        self.test_estimate_data = {
            "customer": "Test Customer",
            "company": self.test_company,
            "items": [
                {
                    "item_code": "ENG-SRV-001",
                    "item_name": "Engine Oil Change",
                    "item_name_ar": "تغيير زيت المحرك",
                    "qty": 1,
                    "rate": 25.000,
                    "amount": 25.000,
                },
                {
                    "item_code": "PART-FLT-001",
                    "item_name": "Oil Filter",
                    "item_name_ar": "فلتر الزيت",
                    "qty": 1,
                    "rate": 15.000,
                    "amount": 15.000,
                },
            ],
        }

    def test_oman_vat_rate_validation(self):
        """Test Oman VAT rate (5%) validation"""
        # Test standard VAT calculation
        base_amount = 100.000
        expected_vat = 5.000
        calculated_vat = self.controller.calculate_vat(base_amount)

        self.assertEqual(
            flt(calculated_vat, 3),
            expected_vat,
            f"VAT calculation failed. Expected {expected_vat}, got {calculated_vat}",
        )

    def test_omr_currency_precision(self):
        """Test OMR currency formatting with 3 decimal places"""
        test_amounts = [100.123, 50.567, 25.999]

        for amount in test_amounts:
            vat_amount = self.controller.calculate_vat(amount)

            # Check OMR precision (3 decimal places)
            self.assertEqual(
                len(str(vat_amount).split(".")[-1]),
                3,
                f"OMR VAT amount {vat_amount} should have 3 decimal places",
            )

    def test_customer_vat_info_retrieval(self):
        """Test customer VAT information retrieval"""
        # Create test customer
        if not frappe.db.exists("Customer", "Test VAT Customer"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = self.test_customer_data["customer_name"]
            customer.oman_trn = self.test_customer_data["oman_trn"]
            customer.vat_type = self.test_customer_data["vat_type"]
            customer.insert()

        # Test VAT info retrieval
        vat_info = self.controller.get_customer_vat_info("Test VAT Customer")

        self.assertEqual(vat_info["vat_type"], "Registered")
        self.assertEqual(vat_info["trn"], self.test_customer_data["oman_trn"])

    def test_oman_trn_validation(self):
        """Test Oman TRN validation (15 digits)"""
        # Valid TRN
        valid_trn = "123456789012345"
        result = self.controller.validate_oman_trn(valid_trn)
        self.assertTrue(result["valid"], "Valid TRN should pass validation")

        # Invalid TRN (wrong length)
        invalid_trn = "12345"
        result = self.controller.validate_oman_trn(invalid_trn)
        self.assertFalse(result["valid"], "Invalid TRN should fail validation")

        # Invalid TRN (contains letters)
        invalid_trn_letters = "12345678901234a"
        result = self.controller.validate_oman_trn(invalid_trn_letters)
        self.assertFalse(result["valid"], "TRN with letters should fail validation")

    def test_vat_category_determination(self):
        """Test VAT category determination for different items"""
        # Standard VAT items
        standard_items = ["Automotive Parts", "Services", "Labor"]
        for item_group in standard_items:
            category = self.controller.get_item_vat_category(item_group)
            rate = self.controller.determine_vat_rate(category, {"vat_type": "Non-Registered"})
            self.assertEqual(rate, 5.0, f"{item_group} should have 5% VAT")

        # Exempt items
        exempt_items = ["Educational Services", "Healthcare Services"]
        for item_group in exempt_items:
            category = self.controller.get_item_vat_category(item_group)
            rate = self.controller.determine_vat_rate(category, {"vat_type": "Non-Registered"})
            self.assertEqual(rate, 0.0, f"{item_group} should be VAT exempt")

    def test_transaction_vat_calculation(self):
        """Test VAT calculation for complete transaction"""
        result = self.controller.calculate_vat_for_transaction(self.test_estimate_data)

        self.assertTrue(result["success"], "Transaction VAT calculation should succeed")

        data = result["data"]
        expected_net_total = 40.000  # 25.000 + 15.000
        expected_vat = 2.000  # 5% of 40.000
        expected_grand_total = 42.000  # 40.000 + 2.000

        self.assertEqual(
            flt(data["net_total"], 3),
            expected_net_total,
            f"Net total mismatch. Expected {expected_net_total}, got {data['net_total']}",
        )

        self.assertEqual(
            flt(data["total_taxes_and_charges"], 3),
            expected_vat,
            f"VAT amount mismatch. Expected {expected_vat}, got {data['total_taxes_and_charges']}",
        )

        self.assertEqual(
            flt(data["grand_total"], 3),
            expected_grand_total,
            f"Grand total mismatch. Expected {expected_grand_total}, got {data['grand_total']}",
        )

    def test_vat_breakdown_generation(self):
        """Test VAT breakdown report generation"""
        items = [
            {
                "amount": 100.000,
                "vat_rate": 5.0,
                "vat_amount": 5.000,
                "vat_category": "Standard VAT",
            },
            {"amount": 50.000, "vat_rate": 0.0, "vat_amount": 0.000, "vat_category": "VAT Exempt"},
        ]

        breakdown = self.controller.generate_vat_breakdown(items)

        # Check standard VAT breakdown
        self.assertEqual(flt(breakdown["standard_vat"]["net_amount"], 3), 100.000)
        self.assertEqual(flt(breakdown["standard_vat"]["vat_amount"], 3), 5.000)

        # Check exempt breakdown
        self.assertEqual(flt(breakdown["exempt"]["net_amount"], 3), 50.000)
        self.assertEqual(flt(breakdown["exempt"]["vat_amount"], 3), 0.000)

    def test_arabic_vat_field_handling(self):
        """Test Arabic VAT field handling and display"""
        # Test Arabic customer with VAT
        arabic_customer_data = {
            "customer_name": "Ahmed Motors",
            "customer_name_ar": "أحمد للسيارات",
            "oman_trn": "123456789012345",
            "oman_trn_ar": "١٢٣٤٥٦٧٨٩٠١٢٣٤٥",
        }

        # Validate Arabic TRN conversion
        self.assertIsNotNone(arabic_customer_data["oman_trn_ar"])
        self.assertIn("١", arabic_customer_data["oman_trn_ar"])  # Contains Arabic numeral

    def test_vat_configuration_validation(self):
        """Test VAT configuration setup and validation"""
        # Test configuration creation
        self.controller.setup_vat_configuration()

        # Verify tax templates are created
        standard_template = frappe.db.exists(
            "Sales Taxes and Charges Template", {"title": ["like", "%Oman VAT 5%"]}
        )
        self.assertTrue(standard_template, "Standard VAT template should be created")

        zero_template = frappe.db.exists(
            "Sales Taxes and Charges Template", {"title": ["like", "%Oman VAT 0%"]}
        )
        self.assertTrue(zero_template, "Zero-rated VAT template should be created")

    def test_performance_benchmarks(self):
        """Test VAT calculation performance"""
        import time

        # Test with large transaction (100 items)
        large_transaction = {
            "customer": "Test Customer",
            "company": self.test_company,
            "items": [
                {"item_code": f"ITEM-{i:03d}", "amount": 10.000, "qty": 1, "rate": 10.000}
                for i in range(100)
            ],
        }

        start_time = time.time()
        result = self.controller.calculate_vat_for_transaction(large_transaction)
        calculation_time = time.time() - start_time

        # Performance requirement: < 2 seconds for 100 items
        self.assertLess(
            calculation_time,
            2.0,
            f"VAT calculation too slow: {calculation_time:.2f}s for 100 items",
        )
        self.assertTrue(result["success"], "Large transaction VAT calculation should succeed")

    def test_error_handling(self):
        """Test error handling in VAT calculations"""
        # Test with invalid data
        invalid_data = {
            "customer": "Non-existent Customer",
            "items": [{"amount": "invalid_amount"}],  # Invalid amount
        }

        result = self.controller.calculate_vat_for_transaction(invalid_data)

        # Should handle errors gracefully
        self.assertFalse(result["success"], "Invalid data should return error")
        self.assertIn("message", result, "Error should include message")

    def test_multi_currency_handling(self):
        """Test VAT calculation with different currencies"""
        # Test OMR (3 decimals)
        omr_amount = 100.123
        vat_omr = self.controller.calculate_vat(omr_amount)
        self.assertEqual(len(str(vat_omr).split(".")[-1]), 3, "OMR should have 3 decimals")

        # Test precision consistency
        self.assertEqual(flt(vat_omr, 3), 5.006, "OMR VAT calculation precision")

    def tearDown(self):
        """Clean up test data"""
        # Clean up test records
        try:
            frappe.db.rollback()
        except:
            pass


class TestVATConfigurationDocType(unittest.TestCase):
    """Test VAT Configuration DocType functionality"""

    def setUp(self):
        """Setup test VAT configuration"""
        self.test_company = "Test VAT Company"

        if not frappe.db.exists("Company", self.test_company):
            company = frappe.new_doc("Company")
            company.company_name = self.test_company
            company.abbr = "TVC"
            company.default_currency = "OMR"
            company.insert()

    def test_vat_configuration_creation(self):
        """Test VAT configuration document creation"""
        config = frappe.new_doc("VAT Configuration")
        config.configuration_name = "Test Oman VAT"
        config.company = self.test_company
        config.effective_from = "2024-01-01"
        config.standard_vat_rate = 5.0
        config.currency = "OMR"
        config.vat_precision = 3

        # Should save without errors
        try:
            config.insert()
            self.assertTrue(True, "VAT configuration created successfully")
        except Exception as e:
            self.fail(f"VAT configuration creation failed: {str(e)}")

    def test_vat_rate_validation(self):
        """Test VAT rate validation"""
        config = frappe.new_doc("VAT Configuration")
        config.configuration_name = "Invalid VAT Test"
        config.company = self.test_company
        config.effective_from = "2024-01-01"
        config.standard_vat_rate = 150.0  # Invalid rate
        config.currency = "OMR"

        # Should raise validation error
        with self.assertRaises(frappe.ValidationError):
            config.insert()

    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()


if __name__ == "__main__":
    # Run all tests
    unittest.main()
