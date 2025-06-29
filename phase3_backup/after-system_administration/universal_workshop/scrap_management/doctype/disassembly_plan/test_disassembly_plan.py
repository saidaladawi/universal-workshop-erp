# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from universal_workshop.scrap_management.doctype.disassembly_plan.disassembly_plan import (
    DisassemblyPlan,
)


class TestDisassemblyPlan(FrappeTestCase):

    def setUp(self):
        """Setup test data"""
        self.cleanup_test_data()
        self.create_test_scrap_vehicle()

    def tearDown(self):
        """Clean up test data"""
        self.cleanup_test_data()

    def cleanup_test_data(self):
        """Clean up any existing test data"""
        # Delete test records
        frappe.db.delete("Disassembly Plan", {"scrap_vehicle": "TEST-SCRAP-001"})
        frappe.db.delete("Scrap Vehicle", {"name": "TEST-SCRAP-001"})
        frappe.db.commit()

    def create_test_scrap_vehicle(self):
        """Create a test scrap vehicle"""
        if not frappe.db.exists("Scrap Vehicle", "TEST-SCRAP-001"):
            scrap_vehicle = frappe.new_doc("Scrap Vehicle")
            scrap_vehicle.vin_number = "1HGBH41JXMN109186"
            scrap_vehicle.vehicle_brand = "Honda"
            scrap_vehicle.vehicle_model = "Civic"
            scrap_vehicle.vehicle_year = 2020
            scrap_vehicle.overall_condition = "Fair"
            scrap_vehicle.acquisition_price_omr = 2500.000
            scrap_vehicle.name = "TEST-SCRAP-001"
            scrap_vehicle.flags.ignore_validate = True
            scrap_vehicle.insert()

    def test_disassembly_plan_creation(self):
        """Test basic disassembly plan creation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        self.assertTrue(plan.name)
        self.assertEqual(plan.plan_status, "Draft")
        self.assertIsNotNone(plan.creation_date)

    def test_arabic_validation(self):
        """Test Arabic text validation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.special_instructions_ar = "تعليمات خاصة للتفكيك"
        plan.insert()

        self.assertTrue(plan.has_arabic_content())
        self.assertEqual(plan.special_instructions_ar, "تعليمات خاصة للتفكيك")

    def test_sequence_generation_value_first(self):
        """Test value-first sequence generation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Generate sequence
        sequence = plan.generate_optimal_sequence()

        self.assertIsInstance(sequence, list)
        self.assertGreater(len(sequence), 0)

        # Safety-critical parts should be first regardless of strategy
        safety_first_parts = ["Battery", "Airbag"]
        first_steps = [step["part_name"] for step in sequence[:2]]

        # At least one safety-critical part should be in first steps
        self.assertTrue(any(part in first_steps for part in safety_first_parts))

    def test_sequence_generation_safety_first(self):
        """Test safety-first sequence generation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Safety-First"
        plan.insert()

        sequence = plan.generate_optimal_sequence()

        # First step should be safety-critical
        first_step = sequence[0]
        safety_critical_parts = ["Battery", "Airbag", "Fuel Tank"]
        self.assertIn(first_step["part_name"], safety_critical_parts)

    def test_labor_time_calculation(self):
        """Test labor time calculation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Calculate total time
        total_time = plan.calculate_total_estimated_time()

        self.assertIsInstance(total_time, (int, float))
        self.assertGreater(total_time, 0)

    def test_profit_analysis(self):
        """Test profit analysis calculation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.labor_rate_per_hour = 15.000  # OMR per hour
        plan.insert()

        # Generate sequence to have steps
        plan.generate_optimal_sequence()

        # Calculate profit analysis
        analysis = plan.calculate_profit_analysis()

        self.assertIn("total_parts_value", analysis)
        self.assertIn("total_labor_cost", analysis)
        self.assertIn("estimated_profit", analysis)
        self.assertIn("profit_margin_percentage", analysis)

        # Values should be positive
        self.assertGreaterEqual(analysis["total_parts_value"], 0)
        self.assertGreaterEqual(analysis["total_labor_cost"], 0)

    def test_mobile_checklist_generation(self):
        """Test mobile checklist generation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Generate sequence
        plan.generate_optimal_sequence()

        # Get mobile checklist
        checklist = plan.get_mobile_checklist()

        self.assertIsInstance(checklist, list)

        if checklist:  # If steps were generated
            first_item = checklist[0]
            required_fields = [
                "step_number",
                "part_name",
                "part_name_ar",
                "extraction_method",
                "safety_level",
                "status",
            ]

            for field in required_fields:
                self.assertIn(field, first_item)

    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Generate sequence
        plan.generate_optimal_sequence()

        # Initial progress should be 0
        progress = plan.calculate_progress_percentage()
        self.assertEqual(progress, 0)

        # Mark first step as completed (if steps exist)
        if plan.disassembly_steps:
            plan.disassembly_steps[0].status = "Completed"
            progress = plan.calculate_progress_percentage()
            self.assertGreater(progress, 0)
            self.assertLessEqual(progress, 100)

    def test_workflow_transitions(self):
        """Test plan status workflow transitions"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Start disassembly
        plan.start_disassembly()
        self.assertEqual(plan.plan_status, "In Progress")
        self.assertIsNotNone(plan.start_date)

        # Complete disassembly
        plan.complete_disassembly()
        self.assertEqual(plan.plan_status, "Completed")
        self.assertIsNotNone(plan.completion_date)

    def test_arabic_part_translations(self):
        """Test Arabic part name translations"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Test some common translations
        test_parts = {
            "Engine Block": "كتلة المحرك",
            "Battery": "البطارية",
            "Transmission": "ناقل الحركة",
        }

        for english_name, expected_arabic in test_parts.items():
            arabic_name = plan.get_arabic_part_name(english_name)
            self.assertEqual(arabic_name, expected_arabic)

    def test_safety_warnings_generation(self):
        """Test safety warnings generation"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Safety-First"
        plan.insert()

        # Generate sequence
        sequence = plan.generate_optimal_sequence()

        # Check that hazardous parts have safety warnings
        for step in sequence:
            if step.get("safety_level") in ["High-Risk", "Hazardous"]:
                self.assertTrue(step.get("safety_warnings"))

    def test_tool_requirements(self):
        """Test tool requirements for different extraction methods"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Test tool requirements for different methods
        test_methods = {
            "Manual": ["Basic hand tools", "Safety gloves"],
            "Cutting": ["Cutting torch", "Safety goggles", "Fire extinguisher"],
            "Hydraulic": ["Hydraulic jack", "Jack stands", "Hydraulic pump"],
        }

        for method, expected_tools in test_methods.items():
            tools = plan.get_required_tools_for_method(method)

            # Check that expected tools are included
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tools)

    def test_vehicle_condition_impact(self):
        """Test how vehicle condition affects disassembly planning"""
        # Test with different conditions
        conditions = ["Excellent", "Good", "Fair", "Poor", "Damaged"]

        for condition in conditions:
            # Update test vehicle condition
            scrap_vehicle = frappe.get_doc("Scrap Vehicle", "TEST-SCRAP-001")
            scrap_vehicle.overall_condition = condition
            scrap_vehicle.save()

            plan = frappe.new_doc("Disassembly Plan")
            plan.scrap_vehicle = "TEST-SCRAP-001"
            plan.disassembly_strategy = "Value-First"
            plan.insert()

            total_time = plan.calculate_total_estimated_time()

            # Poor/Damaged condition should require more time
            if condition in ["Poor", "Damaged"]:
                self.assertGreater(total_time, 60)  # More than 1 hour

    def test_api_methods(self):
        """Test WhiteListed API methods"""
        plan = frappe.new_doc("Disassembly Plan")
        plan.scrap_vehicle = "TEST-SCRAP-001"
        plan.disassembly_strategy = "Value-First"
        plan.insert()

        # Test get_disassembly_plans API
        from universal_workshop.scrap_management.doctype.disassembly_plan.disassembly_plan import (
            get_disassembly_plans,
        )

        plans = get_disassembly_plans()
        self.assertIsInstance(plans, list)

        # Test create_disassembly_plan API
        from universal_workshop.scrap_management.doctype.disassembly_plan.disassembly_plan import (
            create_disassembly_plan,
        )

        new_plan_name = create_disassembly_plan(
            scrap_vehicle="TEST-SCRAP-001",
            strategy="Safety-First",
            special_instructions="Test instructions",
        )

        self.assertTrue(new_plan_name)

        # Verify plan was created
        new_plan = frappe.get_doc("Disassembly Plan", new_plan_name)
        self.assertEqual(new_plan.disassembly_strategy, "Safety-First")


if __name__ == "__main__":
    unittest.main()
