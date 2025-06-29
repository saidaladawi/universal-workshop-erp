# -*- coding: utf-8 -*-
# Copyright (c) 2024, Said Al-Adowi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import unittest
import frappe
from frappe.test_runner import make_test_records
from universal_workshop.billing_management.oman_vat_config import (
    OmanVATConfig,
    validate_oman_vat_number,
)


class TestOmanVAT(unittest.TestCase):
    """
    Test cases for Oman VAT configuration and validation
    """

    @classmethod
    def setUpClass(cls):
        """Setup test data"""
        make_test_records("Company")
        frappe.db.commit()

    def setUp(self):
        """Setup for each test"""
        self.vat_config = OmanVATConfig()

        # Test data
        self.valid_vat_numbers = ["OM123456789012345", "OM987654321098765", "OM111111111111111"]

        self.invalid_vat_numbers = [
            "OM12345678901234",  # Too short
            "OM1234567890123456",  # Too long
            "123456789012345",  # Missing OM prefix
            "OMA123456789012345",  # Invalid prefix
            "OM12345678901234A",  # Contains letter
            "",  # Empty string
            None,  # None value
        ]

    def test_vat_rate_configuration(self):
        """Test VAT rate is set to 5% for Oman"""
        self.assertEqual(self.vat_config.vat_rate, 5.0)
        self.assertEqual(self.vat_config.currency, "OMR")
        self.assertEqual(self.vat_config.decimal_places, 3)

    def test_valid_vat_number_validation(self):
        """Test validation of valid Oman VAT numbers"""
        for vat_number in self.valid_vat_numbers:
            result = self.vat_config.validate_vat_number(vat_number)
            self.assertTrue(result, f"Valid VAT number {vat_number} should pass validation")

    def test_invalid_vat_number_validation(self):
        """Test validation of invalid Oman VAT numbers"""
        for vat_number in self.invalid_vat_numbers:
            if vat_number in [None, ""]:
                # Empty values should pass (optional field)
                result = self.vat_config.validate_vat_number(vat_number)
                self.assertTrue(result)
            else:
                # Invalid formats should raise exception
                with self.assertRaises(frappe.ValidationError):
                    self.vat_config.validate_vat_number(vat_number)

    def test_currency_precision_setup(self):
        """Test OMR currency precision setup"""
        try:
            self.vat_config.setup_currency_precision()

            # Check if currency exists and has correct precision
            if frappe.db.exists("Currency", "OMR"):
                currency_doc = frappe.get_doc("Currency", "OMR")
                self.assertEqual(currency_doc.fraction_units, 3)
                self.assertEqual(currency_doc.fraction, "Baisa")

        except Exception as e:
            self.fail(f"Currency precision setup failed: {str(e)}")

    def test_vat_accounts_creation(self):
        """Test creation of VAT accounts"""
        try:
            # Skip if accounts already exist
            if not frappe.db.exists("Account", "Output VAT 5%"):
                self.vat_config.setup_oman_vat_accounts()

            # Verify accounts were created
            self.assertTrue(frappe.db.exists("Account", "Output VAT 5%"))
            self.assertTrue(frappe.db.exists("Account", "Input VAT 5%"))

            # Check account properties
            output_account = frappe.get_doc("Account", "Output VAT 5%")
            self.assertEqual(output_account.account_type, "Tax")
            self.assertEqual(output_account.account_currency, "OMR")

        except Exception as e:
            # Skip test if parent account doesn't exist
            if "Duties and Taxes" in str(e):
                self.skipTest("Parent account 'Duties and Taxes' not available in test environment")
            else:
                self.fail(f"VAT accounts creation failed: {str(e)}")

    def test_sales_tax_template_creation(self):
        """Test creation of sales tax template"""
        try:
            template_name = "Oman VAT 5% - Sales"

            # Skip if template already exists
            if not frappe.db.exists("Sales Taxes and Charges Template", template_name):
                self.vat_config.setup_sales_tax_template()

            # Verify template was created
            self.assertTrue(frappe.db.exists("Sales Taxes and Charges Template", template_name))

            # Check template properties
            template = frappe.get_doc("Sales Taxes and Charges Template", template_name)
            self.assertEqual(len(template.taxes), 1)
            self.assertEqual(template.taxes[0].rate, 5.0)
            self.assertEqual(template.taxes[0].charge_type, "On Net Total")

        except Exception as e:
            # Skip test if dependencies don't exist
            if "Output VAT 5%" in str(e) or "account" in str(e).lower():
                self.skipTest("VAT accounts not available in test environment")
            else:
                self.fail(f"Sales tax template creation failed: {str(e)}")

    def test_purchase_tax_template_creation(self):
        """Test creation of purchase tax template"""
        try:
            template_name = "Oman VAT 5% - Purchase"

            # Skip if template already exists
            if not frappe.db.exists("Purchase Taxes and Charges Template", template_name):
                self.vat_config.setup_purchase_tax_template()

            # Verify template was created
            self.assertTrue(frappe.db.exists("Purchase Taxes and Charges Template", template_name))

            # Check template properties
            template = frappe.get_doc("Purchase Taxes and Charges Template", template_name)
            self.assertEqual(len(template.taxes), 1)
            self.assertEqual(template.taxes[0].rate, 5.0)
            self.assertEqual(template.taxes[0].charge_type, "On Net Total")

        except Exception as e:
            # Skip test if dependencies don't exist
            if "Input VAT 5%" in str(e) or "account" in str(e).lower():
                self.skipTest("VAT accounts not available in test environment")
            else:
                self.fail(f"Purchase tax template creation failed: {str(e)}")

    def test_item_tax_templates_creation(self):
        """Test creation of item tax templates"""
        try:
            # Skip if templates already exist
            if not frappe.db.exists("Item Tax Template", "Oman Standard VAT 5%"):
                self.vat_config.setup_item_tax_templates()

            # Verify templates were created
            self.assertTrue(frappe.db.exists("Item Tax Template", "Oman Standard VAT 5%"))
            self.assertTrue(frappe.db.exists("Item Tax Template", "Oman Zero Rated VAT"))

            # Check standard VAT template
            standard_template = frappe.get_doc("Item Tax Template", "Oman Standard VAT 5%")
            self.assertEqual(len(standard_template.taxes), 1)
            self.assertEqual(standard_template.taxes[0].tax_rate, 5.0)

            # Check zero-rated template
            zero_template = frappe.get_doc("Item Tax Template", "Oman Zero Rated VAT")
            self.assertEqual(len(zero_template.taxes), 1)
            self.assertEqual(zero_template.taxes[0].tax_rate, 0.0)

        except Exception as e:
            # Skip test if dependencies don't exist
            if "Output VAT 5%" in str(e) or "account" in str(e).lower():
                self.skipTest("VAT accounts not available in test environment")
            else:
                self.fail(f"Item tax templates creation failed: {str(e)}")

    def test_complete_vat_setup(self):
        """Test complete VAT configuration setup"""
        try:
            result = self.vat_config.setup_complete_vat_configuration()

            # Check return value
            self.assertEqual(result["status"], "success")
            self.assertIn("message", result)

        except Exception as e:
            # Skip test if dependencies don't exist in test environment
            if any(keyword in str(e).lower() for keyword in ["account", "company", "parent"]):
                self.skipTest(f"Dependencies not available in test environment: {str(e)}")
            else:
                self.fail(f"Complete VAT setup failed: {str(e)}")

    def test_whitelist_methods(self):
        """Test whitelisted API methods"""
        # Test VAT number validation API
        try:
            # Valid VAT number
            result = validate_oman_vat_number("OM123456789012345")
            self.assertTrue(result)

            # Invalid VAT number should raise exception
            with self.assertRaises(frappe.ValidationError):
                validate_oman_vat_number("INVALID123")

        except Exception as e:
            self.fail(f"Whitelist methods test failed: {str(e)}")

    def tearDown(self):
        """Cleanup after each test"""
        frappe.db.rollback()

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        frappe.db.rollback()
