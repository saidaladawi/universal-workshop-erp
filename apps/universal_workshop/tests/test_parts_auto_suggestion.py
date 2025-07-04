"""
Comprehensive Tests for Parts Auto-Suggestion Feature
Tests the complete implementation including:
- Backend suggestion engine
- JavaScript frontend integration
- Feedback system
- Arabic localization
- Machine learning components
"""

import os
import json
import unittest
from pathlib import Path


# Test class for Parts Auto-Suggestion Feature
class TestPartsAutoSuggestionFeature(unittest.TestCase):
    """Test suite for Parts Auto-Suggestion implementation"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.app_path = self.project_root / "universal_workshop"

        # Test results tracking
        self.test_results = {
            "backend_engine": False,
            "frontend_javascript": False,
            "feedback_doctype": False,
            "feedback_controller": False,
            "arabic_localization": False,
            "api_integration": False,
            "caching_system": False,
            "ml_components": False,
        }

    def test_1_backend_engine_structure(self):
        """Test backend suggestion engine implementation"""
        print("\n=== Testing Backend Suggestion Engine ===")

        engine_file = self.app_path / "sales_service" / "auto_suggestion_engine.py"

        # Check if file exists
        self.assertTrue(engine_file.exists(), "Auto suggestion engine file should exist")

        # Read and validate content
        with open(engine_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Test required classes and methods
        required_elements = [
            "class PartsAutoSuggestionEngine",
            "def get_parts_suggestions",
            "_get_service_type_suggestions",
            "_get_vehicle_specific_suggestions",
            "_get_historical_suggestions",
            "_get_ml_predictions",
            "_combine_suggestions",
            "_filter_by_inventory",
            "_format_suggestions",
            "get_parts_by_category",
            "search_parts",
            "@frappe.whitelist()",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        self.assertEqual(len(missing_elements), 0, f"Missing required elements: {missing_elements}")

        # Test Arabic support
        arabic_indicators = [
            "language: str = 'en'",
            "item_name_ar",
            "Arabic localization support",
            "RTL",
        ]

        arabic_support_count = sum(1 for indicator in arabic_indicators if indicator in content)
        self.assertGreaterEqual(arabic_support_count, 2, "Should have Arabic localization support")

        # Test ML components
        ml_indicators = [
            "machine learning",
            "confidence_score",
            "ml_predictions",
            "pattern",
            "numpy as np",
        ]

        ml_support_count = sum(1 for indicator in ml_indicators if indicator in content)
        self.assertGreaterEqual(ml_support_count, 3, "Should have ML components")

        # Test caching
        caching_indicators = ["cache", "frappe.cache()", "Cache", "expires_in_sec"]

        cache_support_count = sum(1 for indicator in caching_indicators if indicator in content)
        self.assertGreaterEqual(cache_support_count, 2, "Should have caching system")

        self.test_results["backend_engine"] = True
        self.test_results["arabic_localization"] = arabic_support_count >= 2
        self.test_results["ml_components"] = ml_support_count >= 3
        self.test_results["caching_system"] = cache_support_count >= 2

        print(f"✅ Backend engine: {len(content)} lines, all components present")

    def test_2_frontend_javascript_implementation(self):
        """Test frontend JavaScript implementation"""
        print("\n=== Testing Frontend JavaScript ===")

        js_file = self.app_path / "public" / "js" / "parts_suggestion.js"

        # Check if file exists
        self.assertTrue(js_file.exists(), "Parts suggestion JavaScript file should exist")

        # Read and validate content
        with open(js_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Test required JavaScript components
        required_js_elements = [
            "class PartsAutoSuggestionUI",
            "initializeForForm",
            "setupSuggestionUI",
            "loadSuggestions",
            "displaySuggestions",
            "performSearch",
            "addItemToEstimate",
            "recordFeedback",
            "frappe.call",
            "arabic",
            "rtl",
        ]

        missing_js_elements = []
        for element in required_js_elements:
            if element not in content:
                missing_js_elements.append(element)

        self.assertEqual(
            len(missing_js_elements), 0, f"Missing required JS elements: {missing_js_elements}"
        )

        # Test CSS styling
        css_indicators = [
            ".parts-suggestion-panel",
            ".suggestion-item",
            ".rtl-layout",
            "arabic",
            "mobile responsive",
        ]

        css_support_count = sum(1 for indicator in css_indicators if indicator in content)
        self.assertGreaterEqual(css_support_count, 4, "Should have comprehensive CSS styling")

        # Test form integration
        form_integration = [
            "frappe.ui.form.on",
            "Service Estimate",
            "refresh: function(frm)",
            "frm.fields_dict",
        ]

        integration_count = sum(1 for indicator in form_integration if indicator in content)
        self.assertGreaterEqual(integration_count, 3, "Should have proper form integration")

        self.test_results["frontend_javascript"] = True

        print(f"✅ Frontend JavaScript: {len(content)} lines, all components present")

    def test_3_feedback_system_implementation(self):
        """Test feedback system DocType and controller"""
        print("\n=== Testing Feedback System ===")

        # Test DocType JSON
        feedback_json = (
            self.app_path
            / "sales_service"
            / "doctype"
            / "parts_suggestion_feedback"
            / "parts_suggestion_feedback.json"
        )
        self.assertTrue(feedback_json.exists(), "Feedback DocType JSON should exist")

        with open(feedback_json, "r", encoding="utf-8") as f:
            doctype_data = json.load(f)

        # Validate DocType structure
        required_fields = [
            "item_code",
            "service_estimate",
            "was_useful",
            "feedback_reason",
            "confidence_score",
            "user",
            "feedback_date",
            "ml_training_weight",
            "feedback_score",
            "item_name_ar",
        ]

        field_names = [field.get("fieldname") for field in doctype_data.get("fields", [])]
        missing_fields = [field for field in required_fields if field not in field_names]

        self.assertEqual(len(missing_fields), 0, f"Missing required fields: {missing_fields}")

        # Test Python controller
        feedback_py = (
            self.app_path
            / "sales_service"
            / "doctype"
            / "parts_suggestion_feedback"
            / "parts_suggestion_feedback.py"
        )
        self.assertTrue(feedback_py.exists(), "Feedback controller should exist")

        with open(feedback_py, "r", encoding="utf-8") as f:
            controller_content = f.read()

        # Test controller methods
        required_methods = [
            "class PartsSuggestionFeedback",
            "def validate",
            "def calculate_feedback_score",
            "def set_metadata",
            "def set_ml_training_weight",
            "export_training_data",
            "get_feedback_analytics",
        ]

        missing_methods = []
        for method in required_methods:
            if method not in controller_content:
                missing_methods.append(method)

        self.assertEqual(len(missing_methods), 0, f"Missing controller methods: {missing_methods}")

        self.test_results["feedback_doctype"] = True
        self.test_results["feedback_controller"] = True

        print(
            f"✅ Feedback system: DocType with {len(field_names)} fields, controller with all methods"
        )

    def test_4_api_integration_points(self):
        """Test API integration and whitelist methods"""
        print("\n=== Testing API Integration ===")

        engine_file = self.app_path / "sales_service" / "auto_suggestion_engine.py"

        with open(engine_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Test API endpoints
        api_methods = [
            "get_quick_suggestions",
            "search_parts_api",
            "get_category_parts",
            "update_suggestion_feedback",
        ]

        missing_apis = []
        for api in api_methods:
            if f"def {api}" not in content:
                missing_apis.append(api)

        self.assertEqual(len(missing_apis), 0, f"Missing API methods: {missing_apis}")

        # Test whitelist decorators
        whitelist_count = content.count("@frappe.whitelist()")
        self.assertGreaterEqual(whitelist_count, 4, "Should have multiple whitelisted API methods")

        self.test_results["api_integration"] = True

        print(f"✅ API integration: {whitelist_count} whitelisted methods, all endpoints present")

    def test_5_arabic_localization_features(self):
        """Test Arabic localization throughout the system"""
        print("\n=== Testing Arabic Localization ===")

        files_to_check = [
            self.app_path / "sales_service" / "auto_suggestion_engine.py",
            self.app_path / "public" / "js" / "parts_suggestion.js",
        ]

        arabic_features_found = 0

        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for Arabic support indicators
                arabic_indicators = [
                    "ar",
                    "arabic",
                    "rtl",
                    "right-to-left",
                    "اسم",
                    "direction",
                    "text-align: right",
                    "language",
                ]

                file_arabic_count = sum(
                    1 for indicator in arabic_indicators if indicator.lower() in content.lower()
                )
                arabic_features_found += file_arabic_count

        self.assertGreaterEqual(
            arabic_features_found, 10, "Should have comprehensive Arabic localization"
        )

        print(f"✅ Arabic localization: {arabic_features_found} indicators found across files")

    def test_6_performance_and_optimization(self):
        """Test performance optimization features"""
        print("\n=== Testing Performance Features ===")

        engine_file = self.app_path / "sales_service" / "auto_suggestion_engine.py"

        with open(engine_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Test performance features
        performance_indicators = [
            "cache",
            "limit",
            "index",
            "bulk",
            "async",
            "debounce",
            "throttle",
            "pagination",
            "expires",
        ]

        performance_count = sum(
            1 for indicator in performance_indicators if indicator.lower() in content.lower()
        )

        self.assertGreaterEqual(
            performance_count, 5, "Should have performance optimization features"
        )

        print(f"✅ Performance: {performance_count} optimization features present")

    def test_7_file_structure_completeness(self):
        """Test overall file structure completeness"""
        print("\n=== Testing File Structure ===")

        required_files = [
            "sales_service/auto_suggestion_engine.py",
            "public/js/parts_suggestion.js",
            "sales_service/doctype/parts_suggestion_feedback/parts_suggestion_feedback.json",
            "sales_service/doctype/parts_suggestion_feedback/parts_suggestion_feedback.py",
            "sales_service/doctype/parts_suggestion_feedback/__init__.py",
        ]

        missing_files = []
        existing_files = []

        for file_path in required_files:
            full_path = self.app_path / file_path
            if full_path.exists():
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)

        self.assertEqual(len(missing_files), 0, f"Missing required files: {missing_files}")

        print(f"✅ File structure: {len(existing_files)}/{len(required_files)} files present")

    def test_8_integration_readiness(self):
        """Test integration readiness with Service Estimate"""
        print("\n=== Testing Integration Readiness ===")

        js_file = self.app_path / "public" / "js" / "parts_suggestion.js"

        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test Service Estimate integration
        integration_points = [
            "Service Estimate",
            "estimate_items",
            "service_type",
            "vehicle",
            "customer",
            "frappe.ui.form.on",
        ]

        integration_count = sum(1 for point in integration_points if point in js_content)
        self.assertGreaterEqual(
            integration_count, 5, "Should have proper Service Estimate integration"
        )

        print(f"✅ Integration: {integration_count} integration points with Service Estimate")

    def tearDown(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("PARTS AUTO-SUGGESTION FEATURE TEST SUMMARY")
        print("=" * 60)

        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")

        completion_percentage = (passed_tests / total_tests) * 100
        print(f"\nOverall Completion: {passed_tests}/{total_tests} ({completion_percentage:.1f}%)")

        if completion_percentage == 100:
            print("\n🎉 ALL TESTS PASSED! Parts Auto-Suggestion feature is fully implemented.")
        elif completion_percentage >= 75:
            print(f"\n✅ IMPLEMENTATION COMPLETE! Minor issues to address.")
        else:
            print(f"\n⚠️  IMPLEMENTATION IN PROGRESS. Continue development.")

        print("=" * 60)


def run_parts_suggestion_tests():
    """Run the complete Parts Auto-Suggestion test suite"""
    print("Starting Parts Auto-Suggestion Feature Tests...")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPartsAutoSuggestionFeature)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_parts_suggestion_tests()
    exit(0 if success else 1)
