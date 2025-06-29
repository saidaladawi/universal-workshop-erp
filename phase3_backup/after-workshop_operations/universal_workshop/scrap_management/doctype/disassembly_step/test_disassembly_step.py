# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase


class TestDisassemblyStep(FrappeTestCase):

    def test_step_validation(self):
        """Test disassembly step validation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = frappe.new_doc("Disassembly Step")
        step.step_number = 1
        step.part_name = "Battery"
        step.extraction_method = "Manual"
        step.estimated_time_minutes = 15
        step.safety_level = "Elevated"

        # Should validate without errors
        step.validate()

        self.assertEqual(step.safety_level, "Elevated")
        self.assertEqual(step.skill_level, "Intermediate")  # Default value

    def test_required_fields_validation(self):
        """Test required fields validation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = frappe.new_doc("Disassembly Step")

        # Should fail without required fields
        with self.assertRaises(frappe.ValidationError):
            step.validate()

    def test_time_validation(self):
        """Test time validation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = frappe.new_doc("Disassembly Step")
        step.step_number = 1
        step.part_name = "Battery"
        step.extraction_method = "Manual"
        step.estimated_time_minutes = -5  # Invalid negative time

        with self.assertRaises(frappe.ValidationError):
            step.validate()

    def test_safety_level_validation(self):
        """Test safety level validation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = frappe.new_doc("Disassembly Step")
        step.step_number = 1
        step.part_name = "Airbag"
        step.extraction_method = "Manual"
        step.safety_level = "High-Risk"
        # Missing safety warnings for high-risk

        with self.assertRaises(frappe.ValidationError):
            step.validate()

    def test_arabic_translations(self):
        """Test Arabic part name translations"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = DisassemblyStep()

        # Test common translations
        test_cases = {
            "Battery": "البطارية",
            "Engine Block": "كتلة المحرك",
            "Transmission": "ناقل الحركة",
            "Unknown Part": "Unknown Part",  # Should return original
        }

        for english_name, expected_arabic in test_cases.items():
            step.part_name = english_name
            arabic_name = step.get_arabic_part_name()
            self.assertEqual(arabic_name, expected_arabic)

    def test_status_color_coding(self):
        """Test status color coding"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = DisassemblyStep()

        status_colors = {
            "Planned": "gray",
            "In Progress": "blue",
            "Completed": "green",
            "Skipped": "orange",
            "Failed": "red",
        }

        for status, expected_color in status_colors.items():
            step.status = status
            color = step.get_status_color()
            self.assertEqual(color, expected_color)

    def test_safety_color_coding(self):
        """Test safety level color coding"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = DisassemblyStep()

        safety_colors = {
            "Standard": "green",
            "Elevated": "yellow",
            "High-Risk": "orange",
            "Hazardous": "red",
        }

        for safety_level, expected_color in safety_colors.items():
            step.safety_level = safety_level
            color = step.get_safety_color()
            self.assertEqual(color, expected_color)

    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = DisassemblyStep()

        # Test different statuses
        status_percentages = {
            "Planned": 0,
            "In Progress": 50,
            "Completed": 100,
            "Skipped": 0,
            "Failed": 0,
        }

        for status, expected_percentage in status_percentages.items():
            step.status = status
            step.calculate_completion_percentage()
            self.assertEqual(step.completion_percentage, expected_percentage)

    def test_mobile_checklist_data(self):
        """Test mobile checklist data generation"""
        from universal_workshop.scrap_management.doctype.disassembly_step.disassembly_step import (
            DisassemblyStep,
        )

        step = DisassemblyStep()
        step.step_number = 1
        step.part_name = "Battery"
        step.extraction_method = "Manual"
        step.estimated_time_minutes = 15
        step.safety_level = "Elevated"
        step.required_tools = "Basic hand tools, Safety gloves"
        step.safety_warnings = "Disconnect negative terminal first"
        step.status = "Planned"

        checklist_data = step.get_mobile_checklist_data()

        required_fields = [
            "step_number",
            "part_name",
            "part_name_ar",
            "extraction_method",
            "estimated_time",
            "safety_level",
            "safety_color",
            "required_tools",
            "safety_warnings",
            "status",
            "status_color",
            "completion_percentage",
        ]

        for field in required_fields:
            self.assertIn(field, checklist_data)

        self.assertEqual(checklist_data["step_number"], 1)
        self.assertEqual(checklist_data["part_name"], "Battery")
        self.assertEqual(checklist_data["part_name_ar"], "البطارية")


if __name__ == "__main__":
    unittest.main()
