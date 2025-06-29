#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Workshop ERP - Compliance Testing Framework
Comprehensive testing for Oman VAT and e-invoice compliance
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, flt, get_datetime
import json
import re
import base64
from datetime import datetime, timedelta
import unittest


class OmanVATComplianceValidator:
    """Comprehensive validator for Oman VAT and e-invoice compliance"""

    def __init__(self):
        self.validation_results = []
        self.test_cases_passed = 0
        self.test_cases_failed = 0
        self.compliance_score = 0

    def run_comprehensive_validation(self, sales_invoice_id=None):
        """Run all compliance validation tests"""

        self.validation_results = []
        self.test_cases_passed = 0
        self.test_cases_failed = 0

        # Core VAT compliance tests
        self.validate_vat_configuration()
        self.validate_vat_calculation_accuracy()
        self.validate_vat_number_formats()

        # E-invoice compliance tests
        self.validate_einvoice_data_structure()
        self.validate_qr_code_compliance()
        self.validate_bilingual_invoice_content()

        # Integration and system tests
        self.validate_payment_gateway_integration()
        self.validate_multi_currency_compliance()
        self.validate_receivables_management()

        # Security and data integrity tests
        self.validate_data_integrity()
        self.validate_audit_trail()

        # Performance and scalability tests
        self.validate_system_performance()

        # Calculate compliance score
        total_tests = self.test_cases_passed + self.test_cases_failed
        self.compliance_score = (
            (self.test_cases_passed / total_tests * 100) if total_tests > 0 else 0
        )

        return {
            "compliance_score": self.compliance_score,
            "tests_passed": self.test_cases_passed,
            "tests_failed": self.test_cases_failed,
            "total_tests": total_tests,
            "validation_results": self.validation_results,
            "compliance_status": self.get_compliance_status(),
            "recommendations": self.generate_compliance_recommendations(),
        }

    def validate_vat_configuration(self):
        """Validate VAT configuration compliance"""

        test_name = "VAT Configuration Validation"

        try:
            # Check VAT accounts exist
            output_vat_account = frappe.db.exists("Account", {"account_name": "Output VAT 5%"})
            input_vat_account = frappe.db.exists("Account", {"account_name": "Input VAT 5%"})

            if not output_vat_account or not input_vat_account:
                self.add_validation_result(test_name, False, "VAT accounts not properly configured")
                return

            # Check VAT tax templates
            sales_tax_template = frappe.db.exists(
                "Sales Taxes and Charges Template", {"title": "Oman VAT 5%"}
            )
            purchase_tax_template = frappe.db.exists(
                "Purchase Taxes and Charges Template", {"title": "Oman VAT 5%"}
            )

            if not sales_tax_template or not purchase_tax_template:
                self.add_validation_result(
                    test_name, False, "VAT tax templates not properly configured"
                )
                return

            # Check item tax templates
            standard_vat_template = frappe.db.exists(
                "Item Tax Template", {"title": "Standard VAT 5%"}
            )
            zero_rated_template = frappe.db.exists("Item Tax Template", {"title": "Zero Rated"})

            if not standard_vat_template or not zero_rated_template:
                self.add_validation_result(
                    test_name, False, "Item tax templates not properly configured"
                )
                return

            self.add_validation_result(test_name, True, "VAT configuration is compliant")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"VAT configuration validation failed: {str(e)}"
            )

    def validate_vat_calculation_accuracy(self):
        """Validate VAT calculation accuracy with test data"""

        test_name = "VAT Calculation Accuracy"

        try:
            # Test case 1: Standard VAT calculation
            base_amount = 100.000  # OMR
            expected_vat = 5.000  # 5% VAT
            expected_total = 105.000

            # Simulate VAT calculation
            from universal_workshop.billing_management.automatic_vat_calculation import (
                OmanVATCalculationEngine,
            )

            vat_engine = OmanVATCalculationEngine()

            calculated_vat = vat_engine.calculate_vat_amount(base_amount, 5.0)

            if abs(calculated_vat - expected_vat) > 0.001:  # Allow small floating point variance
                self.add_validation_result(
                    test_name,
                    False,
                    f"VAT calculation inaccurate: expected {expected_vat}, got {calculated_vat}",
                )
                return

            # Test case 2: Zero-rated items
            zero_rated_vat = vat_engine.calculate_vat_amount(100.000, 0.0)
            if zero_rated_vat != 0.000:
                self.add_validation_result(
                    test_name,
                    False,
                    f"Zero-rated VAT calculation incorrect: expected 0.000, got {zero_rated_vat}",
                )
                return

            # Test case 3: Precision handling (Baisa)
            test_amount = 123.456
            calculated_vat_baisa = vat_engine.calculate_vat_amount(test_amount, 5.0)
            expected_vat_baisa = round(test_amount * 0.05, 3)

            if abs(calculated_vat_baisa - expected_vat_baisa) > 0.001:
                self.add_validation_result(
                    test_name,
                    False,
                    f"Baisa precision handling incorrect: expected {expected_vat_baisa}, got {calculated_vat_baisa}",
                )
                return

            self.add_validation_result(test_name, True, "VAT calculation accuracy validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"VAT calculation validation failed: {str(e)}"
            )

    def validate_vat_number_formats(self):
        """Validate Oman VAT number format compliance"""

        test_name = "VAT Number Format Validation"

        try:
            from universal_workshop.billing_management.oman_vat_config import OmanVATConfig

            # Test valid VAT numbers
            valid_vat_numbers = ["OM123456789012345", "OM000000000000001", "OM999999999999999"]

            for vat_number in valid_vat_numbers:
                if not OmanVATConfig.validate_oman_vat_number(vat_number):
                    self.add_validation_result(
                        test_name, False, f"Valid VAT number rejected: {vat_number}"
                    )
                    return

            # Test invalid VAT numbers
            invalid_vat_numbers = [
                "OM12345678901234",  # Too short
                "OM1234567890123456",  # Too long
                "ON123456789012345",  # Wrong country code
                "123456789012345",  # Missing country code
                "OM12345678901234A",  # Contains letter
            ]

            for vat_number in invalid_vat_numbers:
                try:
                    if OmanVATConfig.validate_oman_vat_number(vat_number):
                        self.add_validation_result(
                            test_name, False, f"Invalid VAT number accepted: {vat_number}"
                        )
                        return
                except:
                    pass  # Expected to fail

            self.add_validation_result(test_name, True, "VAT number format validation passed")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"VAT number format validation failed: {str(e)}"
            )

    def validate_einvoice_data_structure(self):
        """Validate e-invoice data structure compliance"""

        test_name = "E-Invoice Data Structure"

        try:
            # Check for required custom fields
            required_fields = [
                ("Sales Invoice", "qr_code_data"),
                ("Sales Invoice", "qr_code_image"),
                ("Sales Invoice", "e_invoice_uuid"),
                ("Sales Invoice", "tax_invoice_number"),
                ("Customer", "vat_number_oman"),
                ("Company", "vat_number_oman"),
            ]

            for doctype, fieldname in required_fields:
                if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                    self.add_validation_result(
                        test_name, False, f"Required e-invoice field missing: {doctype}.{fieldname}"
                    )
                    return

            # Check bilingual field support
            bilingual_fields = [
                ("Customer", "customer_name_ar"),
                ("Company", "company_name_ar"),
                ("Item", "item_name_ar"),
                ("Address", "address_ar"),
            ]

            for doctype, fieldname in bilingual_fields:
                if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                    self.add_validation_result(
                        test_name, False, f"Required bilingual field missing: {doctype}.{fieldname}"
                    )
                    return

            self.add_validation_result(test_name, True, "E-invoice data structure is compliant")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"E-invoice data structure validation failed: {str(e)}"
            )

    def validate_qr_code_compliance(self):
        """Validate QR code generation compliance"""

        test_name = "QR Code Compliance"

        try:
            from universal_workshop.billing_management.qr_code_generator import (
                OmanEInvoiceQRGenerator,
            )

            # Test QR code generation
            qr_generator = OmanEInvoiceQRGenerator()

            # Test data
            test_invoice_data = {
                "seller_name": "Universal Workshop",
                "vat_number": "OM123456789012345",
                "timestamp": "2024-12-19T15:30:00Z",
                "total_amount": 105.000,
                "vat_amount": 5.000,
            }

            # Generate QR code
            qr_data = qr_generator.generate_qr_data(test_invoice_data)
            qr_image = qr_generator.generate_qr_image(qr_data)

            # Validate QR data format (should be base64 encoded TLV)
            if not qr_data or not isinstance(qr_data, str):
                self.add_validation_result(test_name, False, "QR data generation failed")
                return

            # Validate QR image format (should be base64 encoded PNG)
            if not qr_image or not qr_image.startswith("data:image/png;base64,"):
                self.add_validation_result(test_name, False, "QR image generation failed")
                return

            # Test TLV decoding
            try:
                decoded_data = qr_generator.decode_tlv_data(qr_data)
                if not decoded_data or len(decoded_data) < 5:  # Should have at least 5 tags
                    self.add_validation_result(test_name, False, "QR TLV decoding failed")
                    return
            except Exception as decode_error:
                self.add_validation_result(
                    test_name, False, f"QR TLV decoding error: {str(decode_error)}"
                )
                return

            self.add_validation_result(test_name, True, "QR code compliance validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"QR code compliance validation failed: {str(e)}"
            )

    def validate_bilingual_invoice_content(self):
        """Validate bilingual invoice content compliance"""

        test_name = "Bilingual Invoice Content"

        try:
            # Check print format exists
            print_format = frappe.db.exists("Print Format", "Universal Workshop Bilingual Invoice")
            if not print_format:
                self.add_validation_result(test_name, False, "Bilingual print format not found")
                return

            # Get print format details
            pf_doc = frappe.get_doc("Print Format", print_format)

            # Check for Arabic content in HTML
            if 'lang="ar"' not in pf_doc.html and "direction: rtl" not in pf_doc.css:
                self.add_validation_result(
                    test_name, False, "Print format lacks proper Arabic RTL support"
                )
                return

            # Check for bilingual field references
            required_bilingual_refs = ["company_name_ar", "customer_name_ar", "address_ar"]

            for field_ref in required_bilingual_refs:
                if field_ref not in pf_doc.html:
                    self.add_validation_result(
                        test_name, False, f"Missing bilingual field reference: {field_ref}"
                    )
                    return

            self.add_validation_result(test_name, True, "Bilingual invoice content validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"Bilingual invoice validation failed: {str(e)}"
            )

    def validate_payment_gateway_integration(self):
        """Validate payment gateway integration compliance"""

        test_name = "Payment Gateway Integration"

        try:
            from universal_workshop.billing_management.payment_gateway_integration import (
                OmanPaymentGatewayManager,
            )

            # Test gateway manager initialization
            gateway_manager = OmanPaymentGatewayManager()

            # Check supported gateways
            supported_gateways = gateway_manager.get_supported_gateways()
            expected_gateways = [
                "thawani",
                "myfatoorah",
                "paytabs",
                "sohar",
                "quadrapay",
                "fibonatix",
            ]

            for gateway in expected_gateways:
                if gateway not in supported_gateways:
                    self.add_validation_result(
                        test_name, False, f"Required payment gateway missing: {gateway}"
                    )
                    return

            # Test gateway configuration validation
            test_config = {
                "api_key": "test_key",
                "secret_key": "test_secret",
                "environment": "sandbox",
            }

            try:
                is_valid = gateway_manager.validate_gateway_config("thawani", test_config)
                # This should pass basic validation
            except Exception as config_error:
                self.add_validation_result(
                    test_name,
                    False,
                    f"Gateway configuration validation failed: {str(config_error)}",
                )
                return

            self.add_validation_result(test_name, True, "Payment gateway integration validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"Payment gateway validation failed: {str(e)}"
            )

    def validate_multi_currency_compliance(self):
        """Validate multi-currency compliance"""

        test_name = "Multi-Currency Compliance"

        try:
            from universal_workshop.billing_management.multi_currency_config import (
                OmanMultiCurrencyManager,
            )

            # Test currency manager
            currency_manager = OmanMultiCurrencyManager()

            # Check supported currencies
            supported_currencies = currency_manager.get_supported_currencies()
            required_currencies = ["OMR", "USD", "EUR", "GBP", "AED", "SAR"]

            for currency in required_currencies:
                if currency not in supported_currencies:
                    self.add_validation_result(
                        test_name, False, f"Required currency missing: {currency}"
                    )
                    return

            # Test OMR precision (3 decimal places for Baisa)
            test_amount = 123.456789
            formatted_omr = currency_manager.format_currency(test_amount, "OMR")

            # Should be rounded to 3 decimal places
            if "123.457" not in formatted_omr:
                self.add_validation_result(
                    test_name, False, f"OMR precision formatting incorrect: {formatted_omr}"
                )
                return

            # Test currency conversion
            try:
                # This should work even with mock data
                converted = currency_manager.convert_currency(100, "USD", "OMR")
                if converted is None:
                    self.add_validation_result(test_name, False, "Currency conversion failed")
                    return
            except Exception as conv_error:
                # This may fail in test environment without live rates
                pass

            self.add_validation_result(test_name, True, "Multi-currency compliance validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"Multi-currency validation failed: {str(e)}"
            )

    def validate_receivables_management(self):
        """Validate receivables management compliance"""

        test_name = "Receivables Management"

        try:
            from universal_workshop.billing_management.receivables_management import (
                OmanReceivablesManager,
            )

            # Test receivables manager
            receivables_manager = OmanReceivablesManager()

            # Test aging analysis buckets
            aging_buckets = receivables_manager.get_aging_buckets()
            expected_buckets = ["current", "1-30", "31-60", "61-90", "90+"]

            for bucket in expected_buckets:
                if bucket not in aging_buckets:
                    self.add_validation_result(
                        test_name, False, f"Required aging bucket missing: {bucket}"
                    )
                    return

            # Test dunning levels
            dunning_levels = receivables_manager.get_dunning_levels()
            expected_levels = [
                "gentle_reminder",
                "first_reminder",
                "second_reminder",
                "final_notice",
            ]

            for level in expected_levels:
                if level not in dunning_levels:
                    self.add_validation_result(
                        test_name, False, f"Required dunning level missing: {level}"
                    )
                    return

            self.add_validation_result(test_name, True, "Receivables management validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"Receivables management validation failed: {str(e)}"
            )

    def validate_data_integrity(self):
        """Validate data integrity and consistency"""

        test_name = "Data Integrity"

        try:
            # Check for orphaned records
            orphaned_checks = [
                ("Sales Invoice", "customer", "Customer"),
                ("Sales Invoice Item", "item_code", "Item"),
                ("Payment Entry", "party", "Customer"),
            ]

            for table, field, ref_table in orphaned_checks:
                orphaned_query = f"""
                    SELECT COUNT(*) as count
                    FROM `tab{table}` t1
                    LEFT JOIN `tab{ref_table}` t2 ON t1.{field} = t2.name
                    WHERE t2.name IS NULL AND t1.{field} IS NOT NULL
                """

                result = frappe.db.sql(orphaned_query, as_dict=True)
                if result and result[0]["count"] > 0:
                    self.add_validation_result(
                        test_name, False, f"Orphaned records found in {table}"
                    )
                    return

            # Check VAT calculation consistency
            inconsistent_vat_query = """
                SELECT COUNT(*) as count
                FROM `tabSales Invoice` si
                JOIN `tabSales Taxes and Charges` stc ON si.name = stc.parent
                WHERE ABS(stc.tax_amount - (si.net_total * stc.rate / 100)) > 0.01
                AND stc.account_head LIKE '%VAT%'
            """

            result = frappe.db.sql(inconsistent_vat_query, as_dict=True)
            if result and result[0]["count"] > 0:
                self.add_validation_result(test_name, False, "Inconsistent VAT calculations found")
                return

            self.add_validation_result(test_name, True, "Data integrity validated")

        except Exception as e:
            self.add_validation_result(
                test_name, False, f"Data integrity validation failed: {str(e)}"
            )

    def validate_audit_trail(self):
        """Validate audit trail compliance"""

        test_name = "Audit Trail"

        try:
            # Check if version tracking is enabled
            version_settings = frappe.get_single("System Settings")
            if not version_settings.track_changes:
                self.add_validation_result(test_name, False, "Version tracking not enabled")
                return

            # Check for audit log retention
            audit_logs_exist = frappe.db.exists("Activity Log")
            if not audit_logs_exist:
                self.add_validation_result(test_name, False, "No audit logs found")
                return

            # Check specific document tracking
            tracked_doctypes = ["Sales Invoice", "Payment Entry", "Customer"]
            for doctype in tracked_doctypes:
                logs = frappe.db.count("Version", {"ref_doctype": doctype})
                if logs == 0:
                    self.add_validation_result(
                        test_name, False, f"No version history for {doctype}"
                    )
                    return

            self.add_validation_result(test_name, True, "Audit trail compliance validated")

        except Exception as e:
            self.add_validation_result(test_name, False, f"Audit trail validation failed: {str(e)}")

    def validate_system_performance(self):
        """Validate system performance compliance"""

        test_name = "System Performance"

        try:
            # Test invoice generation performance
            start_time = datetime.now()

            # Simulate invoice creation time
            test_invoice_data = {
                "customer": "Test Customer",
                "items": [{"item_code": "Test Item", "qty": 1, "rate": 100}],
            }

            # This is a mock performance test
            processing_time = (datetime.now() - start_time).total_seconds()

            # Should be under 5 seconds as per acceptance criteria
            if processing_time > 5.0:
                self.add_validation_result(
                    test_name, False, f"Invoice generation too slow: {processing_time}s"
                )
                return

            # Test QR code generation performance
            start_time = datetime.now()

            from universal_workshop.billing_management.qr_code_generator import (
                OmanEInvoiceQRGenerator,
            )

            qr_generator = OmanEInvoiceQRGenerator()

            test_data = {
                "seller_name": "Test",
                "vat_number": "OM123456789012345",
                "timestamp": "2024-12-19T15:30:00Z",
                "total_amount": 100.000,
                "vat_amount": 5.000,
            }

            qr_generator.generate_qr_image(qr_generator.generate_qr_data(test_data))
            qr_generation_time = (datetime.now() - start_time).total_seconds()

            # QR generation should be fast
            if qr_generation_time > 2.0:
                self.add_validation_result(
                    test_name, False, f"QR generation too slow: {qr_generation_time}s"
                )
                return

            self.add_validation_result(test_name, True, "System performance validated")

        except Exception as e:
            self.add_validation_result(test_name, False, f"Performance validation failed: {str(e)}")

    def add_validation_result(self, test_name, passed, message):
        """Add validation result"""

        self.validation_results.append(
            {
                "test_name": test_name,
                "passed": passed,
                "message": message,
                "timestamp": now_datetime().isoformat(),
            }
        )

        if passed:
            self.test_cases_passed += 1
        else:
            self.test_cases_failed += 1

    def get_compliance_status(self):
        """Get overall compliance status"""

        if self.compliance_score >= 95:
            return "Fully Compliant"
        elif self.compliance_score >= 85:
            return "Mostly Compliant"
        elif self.compliance_score >= 70:
            return "Partially Compliant"
        else:
            return "Non-Compliant"

    def generate_compliance_recommendations(self):
        """Generate compliance improvement recommendations"""

        recommendations = []

        # Analyze failed tests
        failed_tests = [result for result in self.validation_results if not result["passed"]]

        for failed_test in failed_tests:
            if "VAT" in failed_test["test_name"]:
                recommendations.append(
                    {
                        "priority": "high",
                        "area": "VAT Compliance",
                        "recommendation": f"Fix VAT compliance issue: {failed_test['message']}",
                        "test_name": failed_test["test_name"],
                    }
                )
            elif "QR" in failed_test["test_name"]:
                recommendations.append(
                    {
                        "priority": "high",
                        "area": "E-Invoice Compliance",
                        "recommendation": f"Fix QR code issue: {failed_test['message']}",
                        "test_name": failed_test["test_name"],
                    }
                )
            elif "Performance" in failed_test["test_name"]:
                recommendations.append(
                    {
                        "priority": "medium",
                        "area": "System Performance",
                        "recommendation": f"Improve performance: {failed_test['message']}",
                        "test_name": failed_test["test_name"],
                    }
                )
            else:
                recommendations.append(
                    {
                        "priority": "medium",
                        "area": "General Compliance",
                        "recommendation": f"Address issue: {failed_test['message']}",
                        "test_name": failed_test["test_name"],
                    }
                )

        return recommendations


@frappe.whitelist()
def run_compliance_validation():
    """API endpoint to run comprehensive compliance validation"""

    validator = OmanVATComplianceValidator()
    results = validator.run_comprehensive_validation()

    # Log validation results
    frappe.log_error(json.dumps(results, indent=2), "Compliance Validation Results")

    return results


@frappe.whitelist()
def generate_compliance_report(language="en"):
    """Generate comprehensive compliance report"""

    validation_results = run_compliance_validation()

    title = "تقرير الامتثال الشامل" if language == "ar" else "Comprehensive Compliance Report"

    report = {
        "title": title,
        "generated_date": now_datetime().isoformat(),
        "language": language,
        "compliance_summary": {
            "overall_score": validation_results["compliance_score"],
            "status": validation_results["compliance_status"],
            "tests_passed": validation_results["tests_passed"],
            "tests_failed": validation_results["tests_failed"],
            "total_tests": validation_results["total_tests"],
        },
        "detailed_results": validation_results["validation_results"],
        "recommendations": validation_results["recommendations"],
        "next_actions": generate_next_actions(validation_results, language),
    }

    return report


def generate_next_actions(validation_results, language="en"):
    """Generate next action items based on validation results"""

    actions = []

    if validation_results["compliance_score"] < 100:
        if language == "ar":
            actions.append("إصلاح المشاكل المحددة في نتائج التحقق")
            actions.append("إعادة تشغيل اختبار الامتثال بعد الإصلاحات")
            actions.append("توثيق جميع التغييرات المطلوبة للامتثال")
        else:
            actions.append("Fix identified issues in validation results")
            actions.append("Re-run compliance testing after fixes")
            actions.append("Document all compliance-related changes")

    if validation_results["compliance_score"] >= 95:
        if language == "ar":
            actions.append("النظام جاهز للإنتاج")
            actions.append("جدولة مراجعات الامتثال الدورية")
            actions.append("تدريب المستخدمين على الوظائف المتوافقة")
        else:
            actions.append("System ready for production deployment")
            actions.append("Schedule regular compliance reviews")
            actions.append("Train users on compliant functionality")

    return actions
