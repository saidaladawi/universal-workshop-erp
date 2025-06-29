import unittest
import frappe
import json
from unittest.mock import patch, MagicMock
from universal_workshop.sales_service.quality_control import (
    QualityControlWorkflow,
    create_inspection_checklist,
    update_inspection_item,
    approve_inspection,
    reject_inspection,
    get_inspection_dashboard,
    generate_inspection_report,
)


class TestQualityControlWorkflow(unittest.TestCase):
    """Comprehensive test suite for Quality Control Workflow System"""

    def setUp(self):
        """Set up test environment"""
        self.test_service_order_data = {
            "name": "SO-TEST-QC-001",
            "customer": "Ahmed Al-Rashid",
            "vehicle_registration": "OMN-123-45",
            "total": 500.000,
        }

        self.test_checklist_data = {
            "checklist_type": "comprehensive",
            "vehicle_type": "passenger",
            "customer": "Ahmed Al-Rashid",
            "vehicle_registration": "OMN-123-45",
        }

        self.test_inspection_items = [
            {
                "item_code": "EXT001",
                "item_name": "Exterior Lights Check",
                "item_name_ar": "فحص الأضواء الخارجية",
                "category": "Exterior",
                "inspection_type": "Visual",
                "is_mandatory": True,
                "acceptance_criteria": "All lights working properly",
                "acceptance_criteria_ar": "جميع الأضواء تعمل بشكل صحيح",
            },
            {
                "item_code": "ENG001",
                "item_name": "Engine Oil Level",
                "item_name_ar": "مستوى زيت المحرك",
                "category": "Engine",
                "inspection_type": "Measurement",
                "is_mandatory": True,
                "acceptance_criteria": "Oil level between MIN and MAX marks",
                "acceptance_criteria_ar": "مستوى الزيت بين علامتي الحد الأدنى والأقصى",
            },
        ]

        # Setup test Quality Control Workflow
        self.qc_workflow = QualityControlWorkflow()

    def test_quality_control_workflow_initialization(self):
        """Test QualityControlWorkflow class initialization"""
        workflow = QualityControlWorkflow("SO-TEST-001")
        self.assertEqual(workflow.service_order, "SO-TEST-001")
        self.assertIsNone(workflow.service_order_doc)

    def test_create_inspection_checklist_comprehensive(self):
        """Test comprehensive inspection checklist creation"""
        result = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="passenger", service_order="SO-TEST-001"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("checklist_id", result)
        self.assertGreater(len(result["inspection_items"]), 10)

        # Check Arabic field presence
        arabic_items = [item for item in result["inspection_items"] if "item_name_ar" in item]
        self.assertGreater(len(arabic_items), 0)

    def test_create_inspection_checklist_basic(self):
        """Test basic inspection checklist creation"""
        result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("checklist_id", result)
        self.assertGreaterEqual(len(result["inspection_items"]), 5)
        self.assertLessEqual(len(result["inspection_items"]), 10)

    def test_create_inspection_checklist_safety_only(self):
        """Test safety-only inspection checklist creation"""
        result = self.qc_workflow.create_inspection_checklist(
            checklist_type="safety_only", vehicle_type="commercial"
        )

        self.assertEqual(result["status"], "success")
        safety_items = [item for item in result["inspection_items"] if item["category"] == "Safety"]
        self.assertGreater(len(safety_items), 0)

    def test_update_inspection_item_pass(self):
        """Test updating inspection item to pass status"""
        # Create test checklist first
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = self.qc_workflow.update_inspection_item(
            checklist_id=checklist_id,
            item_code="EXT001",
            status="pass",
            notes="All lights working correctly",
            measurements={"brightness": "100%", "alignment": "correct"},
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("updated item", result["message"].lower())

    def test_update_inspection_item_fail(self):
        """Test updating inspection item to fail status"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = self.qc_workflow.update_inspection_item(
            checklist_id=checklist_id,
            item_code="ENG001",
            status="fail",
            notes="Oil level below minimum mark",
            measurements={"oil_level": "Below MIN"},
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("updated item", result["message"].lower())

    def test_update_inspection_item_invalid_status(self):
        """Test updating inspection item with invalid status"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = self.qc_workflow.update_inspection_item(
            checklist_id=checklist_id,
            item_code="EXT001",
            status="invalid_status",
            notes="Test notes",
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("invalid status", result["message"].lower())

    def test_calculate_inspection_progress(self):
        """Test inspection progress calculation"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        # Update some items
        self.qc_workflow.update_inspection_item(checklist_id, "EXT001", "pass", "Good")
        self.qc_workflow.update_inspection_item(checklist_id, "ENG001", "fail", "Needs attention")

        progress = self.qc_workflow.calculate_inspection_progress(checklist_id)

        self.assertIn("completion_percentage", progress)
        self.assertIn("passed_items", progress)
        self.assertIn("failed_items", progress)
        self.assertIn("total_items", progress)

        self.assertGreater(progress["completion_percentage"], 0)
        self.assertEqual(progress["passed_items"], 1)
        self.assertEqual(progress["failed_items"], 1)

    def test_approve_inspection_checklist(self):
        """Test inspection checklist approval"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        # Mark all items as pass
        items = checklist_result["inspection_items"]
        for item in items:
            self.qc_workflow.update_inspection_item(
                checklist_id, item["item_code"], "pass", "Approved"
            )

        result = self.qc_workflow.approve_inspection(
            checklist_id, approval_notes="All items passed inspection"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("approved", result["message"].lower())

    def test_reject_inspection_checklist(self):
        """Test inspection checklist rejection"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        # Mark some items as fail
        self.qc_workflow.update_inspection_item(checklist_id, "EXT001", "fail", "Critical issue")

        result = self.qc_workflow.reject_inspection(
            checklist_id, rejection_reason="Critical safety issues found"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("rejected", result["message"].lower())

    def test_generate_inspection_recommendations(self):
        """Test inspection recommendations generation"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        # Add some failed items
        failed_items = [
            {"item_code": "EXT001", "status": "fail", "notes": "Headlight not working"},
            {"item_code": "ENG001", "status": "fail", "notes": "Oil level low"},
        ]

        for item in failed_items:
            self.qc_workflow.update_inspection_item(
                checklist_id, item["item_code"], item["status"], item["notes"]
            )

        recommendations = self.qc_workflow.generate_inspection_recommendations(checklist_id)

        self.assertEqual(recommendations["status"], "success")
        self.assertIn("recommendations", recommendations)
        self.assertGreater(len(recommendations["recommendations"]), 0)

        # Check recommendation structure
        rec = recommendations["recommendations"][0]
        self.assertIn("item_name", rec)
        self.assertIn("action", rec)
        self.assertIn("priority", rec)
        self.assertIn("estimated_cost", rec)

    def test_get_inspection_dashboard_data(self):
        """Test inspection dashboard data retrieval"""
        # Create multiple checklists
        checklist1 = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist2 = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="commercial"
        )

        dashboard_data = self.qc_workflow.get_inspection_dashboard()

        self.assertEqual(dashboard_data["status"], "success")
        self.assertIn("data", dashboard_data)
        self.assertGreaterEqual(len(dashboard_data["data"]), 2)

        # Check data structure
        checklist_data = dashboard_data["data"][0]
        self.assertIn("checklist_id", checklist_data)
        self.assertIn("checklist_type", checklist_data)
        self.assertIn("status", checklist_data)
        self.assertIn("progress", checklist_data)
        self.assertIn("items_by_category", checklist_data)

    def test_arabic_localization(self):
        """Test Arabic localization in quality control system"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="passenger"
        )

        items = checklist_result["inspection_items"]

        # Check Arabic field presence
        arabic_items = [item for item in items if "item_name_ar" in item and item["item_name_ar"]]
        self.assertGreater(len(arabic_items), 0)

        # Check Arabic criteria
        arabic_criteria = [
            item
            for item in items
            if "acceptance_criteria_ar" in item and item["acceptance_criteria_ar"]
        ]
        self.assertGreater(len(arabic_criteria), 0)

        # Verify Arabic text encoding
        arabic_item = arabic_items[0]
        arabic_text = arabic_item["item_name_ar"]

        # Check for Arabic characters
        has_arabic = any("\u0600" <= char <= "\u06ff" for char in arabic_text)
        self.assertTrue(has_arabic, f"No Arabic characters found in: {arabic_text}")

    def test_inspection_item_validation(self):
        """Test inspection item field validation"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )

        items = checklist_result["inspection_items"]

        for item in items:
            # Check required fields
            self.assertIn("item_code", item)
            self.assertIn("item_name", item)
            self.assertIn("category", item)
            self.assertIn("inspection_type", item)

            # Check field types
            self.assertIsInstance(item["item_code"], str)
            self.assertIsInstance(item["item_name"], str)
            self.assertIsInstance(item["is_mandatory"], bool)

            # Check valid categories
            valid_categories = [
                "Exterior",
                "Interior",
                "Engine",
                "Drivetrain",
                "Chassis",
                "Electrical",
                "Safety",
                "Lighting",
                "Comfort",
                "Commercial",
                "Documentation",
            ]
            self.assertIn(item["category"], valid_categories)

            # Check valid inspection types
            valid_types = ["Visual", "Functional", "Measurement", "Documentary"]
            self.assertIn(item["inspection_type"], valid_types)

    def test_performance_benchmarks(self):
        """Test performance benchmarks for quality control operations"""
        import time

        # Test checklist creation performance
        start_time = time.time()
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="passenger"
        )
        creation_time = time.time() - start_time

        self.assertLess(creation_time, 2.0, "Checklist creation should complete within 2 seconds")

        checklist_id = checklist_result["checklist_id"]
        items = checklist_result["inspection_items"]

        # Test bulk item updates performance
        start_time = time.time()
        for i, item in enumerate(items[:10]):  # Test first 10 items
            status = "pass" if i % 2 == 0 else "fail"
            self.qc_workflow.update_inspection_item(
                checklist_id, item["item_code"], status, f"Test note {i}"
            )
        bulk_update_time = time.time() - start_time

        self.assertLess(bulk_update_time, 5.0, "10 item updates should complete within 5 seconds")

        # Test dashboard data performance
        start_time = time.time()
        dashboard_data = self.qc_workflow.get_inspection_dashboard()
        dashboard_time = time.time() - start_time

        self.assertLess(
            dashboard_time, 1.0, "Dashboard data loading should complete within 1 second"
        )

    def test_error_handling(self):
        """Test error handling for various scenarios"""

        # Test invalid checklist type
        result = self.qc_workflow.create_inspection_checklist(
            checklist_type="invalid_type", vehicle_type="passenger"
        )
        self.assertEqual(result["status"], "error")

        # Test invalid vehicle type
        result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="invalid_vehicle"
        )
        self.assertEqual(result["status"], "error")

        # Test updating non-existent item
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = self.qc_workflow.update_inspection_item(
            checklist_id, "NON_EXISTENT", "pass", "Test"
        )
        self.assertEqual(result["status"], "error")

        # Test operations on non-existent checklist
        result = self.qc_workflow.approve_inspection("NON_EXISTENT", "Test notes")
        self.assertEqual(result["status"], "error")

    def test_workflow_state_transitions(self):
        """Test quality control workflow state transitions"""
        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        # Initial state should be 'draft'
        dashboard_data = self.qc_workflow.get_inspection_dashboard()
        checklist_data = next(
            (c for c in dashboard_data["data"] if c["checklist_id"] == checklist_id), None
        )
        self.assertIsNotNone(checklist_data)
        self.assertEqual(checklist_data["status"], "draft")

        # Update some items to change state to 'in_progress'
        items = checklist_result["inspection_items"]
        self.qc_workflow.update_inspection_item(checklist_id, items[0]["item_code"], "pass", "Good")

        # Check state progression
        progress = self.qc_workflow.calculate_inspection_progress(checklist_id)
        self.assertGreater(progress["completion_percentage"], 0)

        # Complete all items and approve
        for item in items:
            self.qc_workflow.update_inspection_item(
                checklist_id, item["item_code"], "pass", "Approved"
            )

        result = self.qc_workflow.approve_inspection(checklist_id, "All items passed")
        self.assertEqual(result["status"], "success")

    def test_integration_with_service_orders(self):
        """Test integration with service order workflow"""
        # This would test integration with actual Service Order DocType
        service_order = "SO-TEST-INTEGRATION-001"

        checklist_result = self.qc_workflow.create_inspection_checklist(
            checklist_type="comprehensive", vehicle_type="passenger", service_order=service_order
        )

        self.assertEqual(checklist_result["status"], "success")
        checklist_id = checklist_result["checklist_id"]

        # Test service order update after approval
        items = checklist_result["inspection_items"]
        for item in items:
            self.qc_workflow.update_inspection_item(
                checklist_id, item["item_code"], "pass", "Approved"
            )

        approval_result = self.qc_workflow.approve_inspection(checklist_id, "Quality approved")
        self.assertEqual(approval_result["status"], "success")

    def tearDown(self):
        """Clean up test data"""
        # Clean up any test records created during testing
        frappe.db.rollback()


class TestQualityControlAPI(unittest.TestCase):
    """Test Quality Control API methods"""

    def test_create_inspection_checklist_api(self):
        """Test create_inspection_checklist API method"""
        result = create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger", service_order="SO-API-TEST-001"
        )

        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")

    def test_update_inspection_item_api(self):
        """Test update_inspection_item API method"""
        # Create checklist first
        checklist_result = create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = update_inspection_item(
            checklist_id=checklist_id, item_code="EXT001", status="pass", notes="API test notes"
        )

        self.assertEqual(result["status"], "success")

    def test_approve_inspection_api(self):
        """Test approve_inspection API method"""
        checklist_result = create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = approve_inspection(checklist_id=checklist_id, approval_notes="API approval test")

        self.assertIn("status", result)

    def test_reject_inspection_api(self):
        """Test reject_inspection API method"""
        checklist_result = create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = reject_inspection(checklist_id=checklist_id, rejection_reason="API rejection test")

        self.assertIn("status", result)

    def test_get_inspection_dashboard_api(self):
        """Test get_inspection_dashboard API method"""
        result = get_inspection_dashboard()

        self.assertIn("status", result)
        self.assertIn("data", result)

    def test_generate_inspection_report_api(self):
        """Test generate_inspection_report API method"""
        checklist_result = create_inspection_checklist(
            checklist_type="basic", vehicle_type="passenger"
        )
        checklist_id = checklist_result["checklist_id"]

        result = generate_inspection_report(checklist_id=checklist_id)

        self.assertIn("status", result)


class TestQualityControlSecurity(unittest.TestCase):
    """Test security aspects of Quality Control system"""

    def test_user_permissions(self):
        """Test user permissions for quality control operations"""
        # This would test role-based access control
        # Implementation depends on ERPNext permission system
        pass

    def test_data_validation(self):
        """Test input data validation and sanitization"""
        qc_workflow = QualityControlWorkflow()

        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE tabCustomer; --"
        result = qc_workflow.create_inspection_checklist(
            checklist_type=malicious_input, vehicle_type="passenger"
        )
        self.assertEqual(result["status"], "error")

    def test_audit_trail(self):
        """Test audit trail for quality control operations"""
        # This would test logging and audit trail functionality
        pass


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
