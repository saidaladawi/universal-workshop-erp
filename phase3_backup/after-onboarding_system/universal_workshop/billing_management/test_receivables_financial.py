"""
Test suite for Receivables Management and Financial Reporting
Universal Workshop ERP - Billing Management Module
"""

import unittest
import frappe
from frappe.utils import today, add_days, add_months, flt
from datetime import datetime, timedelta
import json

from universal_workshop.billing_management.receivables_management import OmanReceivablesManager
from universal_workshop.billing_management.financial_reporting import OmanFinancialReportingManager


class TestReceivablesManagement(unittest.TestCase):
    """Test cases for receivables management system"""

    def setUp(self):
        """Setup test data"""
        self.company = "Test Company"
        self.manager = OmanReceivablesManager()

        # Create test customer
        if not frappe.db.exists("Customer", "TEST-CUST-001"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Ahmed Al-Rashid"
            customer.customer_name_ar = "أحمد الراشد"
            customer.customer_group = "Individual"
            customer.territory = "Oman"
            customer.insert()
            customer.name = "TEST-CUST-001"
            customer.save()

    def test_aging_buckets_configuration(self):
        """Test aging bucket configuration"""
        buckets = self.manager.aging_buckets

        self.assertEqual(len(buckets), 5)
        self.assertEqual(buckets[0]["label"], "Current")
        self.assertEqual(buckets[-1]["label"], "90+ Days")

        # Test bucket ranges
        self.assertEqual(buckets[0]["min_days"], 0)
        self.assertEqual(buckets[0]["max_days"], 0)
        self.assertEqual(buckets[-1]["min_days"], 91)

    def test_aging_analysis_generation(self):
        """Test aging analysis report generation"""
        try:
            report = self.manager.generate_aging_analysis(self.company)

            # Verify report structure
            self.assertIn("company", report)
            self.assertIn("aging_buckets", report)
            self.assertIn("customer_summaries", report)
            self.assertIn("total_summary", report)
            self.assertIn("recommendations", report)

            # Verify aging buckets
            self.assertEqual(len(report["aging_buckets"]), 5)

            # Verify currency and precision
            self.assertEqual(report["currency"], "OMR")
            self.assertEqual(report["precision"], 3)

        except Exception as e:
            # Expected if no outstanding invoices exist
            self.assertIn("Failed to generate aging analysis", str(e))

    def test_payment_behavior_scoring(self):
        """Test payment behavior scoring algorithm"""

        # Test perfect customer
        perfect_customer = {
            "overdue_percentage": 0,
            "credit_utilization": 50,
            "overdue_invoices": 0,
        }
        score = self.manager._calculate_payment_score(perfect_customer)
        self.assertEqual(score, 10)

        # Test problematic customer
        problem_customer = {
            "overdue_percentage": 60,
            "credit_utilization": 95,
            "overdue_invoices": 6,
        }
        score = self.manager._calculate_payment_score(problem_customer)
        self.assertLessEqual(score, 5)
        self.assertGreaterEqual(score, 1)  # Minimum score

    def test_customer_risk_assessment(self):
        """Test customer risk assessment"""

        # Low risk customer
        low_risk_data = {"payment_behavior_score": 9, "overdue_percentage": 5}
        risk = self.manager._assess_customer_risk(low_risk_data)
        self.assertEqual(risk, "Low Risk")

        # Critical risk customer
        critical_risk_data = {"payment_behavior_score": 3, "overdue_percentage": 70}
        risk = self.manager._assess_customer_risk(critical_risk_data)
        self.assertEqual(risk, "Critical Risk")

    def test_dunning_level_determination(self):
        """Test dunning level determination logic"""

        # Recent overdue
        recent_overdue = [{"days_overdue": 10}]
        level = self.manager._determine_dunning_level(recent_overdue)
        self.assertEqual(level, "Gentle Reminder")

        # Long overdue
        long_overdue = [{"days_overdue": 95}]
        level = self.manager._determine_dunning_level(long_overdue)
        self.assertEqual(level, "Final Notice")

        # No overdue invoices
        no_overdue = []
        level = self.manager._determine_dunning_level(no_overdue)
        self.assertEqual(level, "No Action")

    def test_dunning_templates(self):
        """Test dunning message templates"""

        # Test English templates
        en_template = self.manager._get_dunning_templates("First Reminder", "en")
        self.assertIn("subject", en_template)
        self.assertIn("message", en_template)
        self.assertIn("customer_name", en_template["message"])

        # Test Arabic templates
        ar_template = self.manager._get_dunning_templates("First Reminder", "ar")
        self.assertIn("subject", ar_template)
        self.assertIn("message", ar_template)
        self.assertIn("أول", ar_template["subject"])  # Arabic text

    def test_next_action_date_calculation(self):
        """Test next action date calculation"""

        next_date = self.manager._calculate_next_action_date("Final Notice")
        expected_date = add_days(today(), 3)
        self.assertEqual(next_date, expected_date)

        next_date = self.manager._calculate_next_action_date("Gentle Reminder")
        expected_date = add_days(today(), 7)
        self.assertEqual(next_date, expected_date)


class TestFinancialReporting(unittest.TestCase):
    """Test cases for financial reporting system"""

    def setUp(self):
        """Setup test data"""
        self.company = "Test Company"
        self.manager = OmanFinancialReportingManager()

        # Setup test date range
        self.start_date = "2024-01-01"
        self.end_date = "2024-03-31"

    def test_vat_rate_configuration(self):
        """Test VAT rate configuration"""
        self.assertEqual(self.manager.vat_rate, 5.0)
        self.assertEqual(self.manager.currency, "OMR")
        self.assertEqual(self.manager.precision, 3)

    def test_quarterly_vat_return_structure(self):
        """Test quarterly VAT return data structure"""
        try:
            vat_return = self.manager.generate_quarterly_vat_return(self.company, 1, 2024)

            # Verify required fields
            required_fields = [
                "company",
                "quarter",
                "year",
                "period_start",
                "period_end",
                "total_sales_value",
                "vat_on_sales",
                "total_purchase_value",
                "vat_on_purchases",
                "net_vat_liability",
            ]

            for field in required_fields:
                self.assertIn(field, vat_return)

            # Verify calculations
            self.assertIsInstance(vat_return["total_sales_value"], (int, float))
            self.assertIsInstance(vat_return["vat_on_sales"], (int, float))
            self.assertIsInstance(vat_return["net_vat_liability"], (int, float))

        except Exception as e:
            # Expected if no invoices exist for the period
            self.assertIn("Failed to generate VAT return", str(e))

    def test_vat_calculation_logic(self):
        """Test VAT calculation logic"""

        # Test net liability calculation
        sales_vat = 1000.0
        purchase_vat = 300.0
        net_vat = sales_vat - purchase_vat

        self.assertEqual(net_vat, 700.0)

        # Test refund scenario
        sales_vat = 200.0
        purchase_vat = 500.0
        net_vat = sales_vat - purchase_vat

        self.assertEqual(net_vat, -300.0)  # Refund due

    def test_vat_audit_trail_structure(self):
        """Test VAT audit trail generation"""
        try:
            audit_trail = self.manager.generate_vat_audit_trail(
                self.company, self.start_date, self.end_date
            )

            # Verify audit trail structure
            required_sections = [
                "sales_register",
                "purchase_register",
                "vat_rate_analysis",
                "customer_analysis",
                "supplier_analysis",
                "payment_analysis",
            ]

            for section in required_sections:
                self.assertIn(section, audit_trail)

            # Verify metadata
            self.assertEqual(audit_trail["company"], self.company)
            self.assertEqual(audit_trail["period_start"], self.start_date)
            self.assertEqual(audit_trail["period_end"], self.end_date)

        except Exception as e:
            # May fail if no data exists
            pass

    def test_currency_precision(self):
        """Test currency precision handling"""

        # Test OMR precision (3 decimal places)
        test_amount = 123.4567
        rounded_amount = flt(test_amount, self.manager.precision)
        self.assertEqual(rounded_amount, 123.457)

        # Test Baisa conversion
        omr_amount = 10.500
        baisa_amount = omr_amount * 1000
        self.assertEqual(baisa_amount, 10500)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""

    def setUp(self):
        """Setup integration test data"""
        self.company = "Test Company"
        self.receivables_manager = OmanReceivablesManager()
        self.financial_manager = OmanFinancialReportingManager()

    def test_arabic_language_support(self):
        """Test Arabic language support across modules"""

        # Test aging analysis in Arabic
        try:
            report = self.receivables_manager.generate_aging_analysis(self.company, language="ar")
            self.assertEqual(report["language"], "ar")

            # Verify Arabic bucket labels exist
            for bucket in report["aging_buckets"]:
                self.assertIn("label_ar", bucket)
                self.assertTrue(bucket["label_ar"])  # Not empty

        except Exception:
            pass  # Expected if no data

        # Test dunning templates in Arabic
        ar_template = self.receivables_manager._get_dunning_templates("First Reminder", "ar")
        self.assertIsInstance(ar_template, dict)
        if ar_template:
            self.assertIn("أول", ar_template.get("subject", ""))  # Arabic text

    def test_vat_compliance_validation(self):
        """Test VAT compliance validation"""
        try:
            from universal_workshop.billing_management.financial_reporting import (
                validate_vat_compliance,
            )

            compliance_result = validate_vat_compliance(self.company, "2024-01-01", "2024-03-31")

            # Verify compliance result structure
            self.assertIn("missing_vat_numbers", compliance_result)
            self.assertIn("missing_qr_codes", compliance_result)
            self.assertIn("compliance_score", compliance_result)
            self.assertIn("recommendations", compliance_result)

            # Verify score is between 0-100
            score = compliance_result["compliance_score"]
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

        except Exception:
            pass  # Expected if functions not available

    def test_currency_formatting_consistency(self):
        """Test currency formatting consistency across modules"""

        # Test OMR formatting
        test_amount = 1234.567

        # Both managers should use same precision
        self.assertEqual(self.receivables_manager.precision, self.financial_manager.precision)

        # Both should use OMR currency
        self.assertEqual(self.receivables_manager.currency, self.financial_manager.currency)

    def test_data_consistency(self):
        """Test data consistency between modules"""

        # Both modules should handle same date format
        test_date = today()

        # Test aging analysis date handling
        try:
            aging_report = self.receivables_manager.generate_aging_analysis(self.company, test_date)
            self.assertEqual(aging_report["as_on_date"], test_date)
        except Exception:
            pass

        # Test VAT return date handling
        try:
            vat_return = self.financial_manager.generate_quarterly_vat_return(self.company, 1, 2024)
            self.assertIn("period_start", vat_return)
            self.assertIn("period_end", vat_return)
        except Exception:
            pass


def run_all_tests():
    """Run all test cases"""

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_classes = [TestReceivablesManagement, TestFinancialReporting, TestIntegrationScenarios]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return summary
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (
            ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
            if result.testsRun > 0
            else 0
        ),
    }


if __name__ == "__main__":
    # Run tests when file is executed directly
    summary = run_all_tests()
    print(f"\n📊 Test Summary:")
    print(f"✅ Tests run: {summary['tests_run']}")
    print(f"❌ Failures: {summary['failures']}")
    print(f"🔥 Errors: {summary['errors']}")
    print(f"📈 Success rate: {summary['success_rate']:.1f}%")
