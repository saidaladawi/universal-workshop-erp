# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts import (
	ExtractedParts,
)


class TestExtractedParts(FrappeTestCase):
	def setUp(self):
		"""Setup test data"""
		self.cleanup_test_data()
		self.create_test_scrap_vehicle()
		self.create_test_disassembly_plan()

	def tearDown(self):
		"""Clean up test data"""
		self.cleanup_test_data()

	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Delete test records
		for doctype in ["Extracted Parts", "Disassembly Plan", "Scrap Vehicle"]:
			frappe.db.sql(f"DELETE FROM `tab{doctype}` WHERE name LIKE 'TEST-%'")
		frappe.db.commit()

	def create_test_scrap_vehicle(self):
		"""Create test scrap vehicle"""
		if not frappe.db.exists("Scrap Vehicle", "TEST-SCRAP-001"):
			scrap_vehicle = frappe.new_doc("Scrap Vehicle")
			scrap_vehicle.name = "TEST-SCRAP-001"
			scrap_vehicle.vin_number = "1HGBH41JXMN109186"
			scrap_vehicle.make = "Toyota"
			scrap_vehicle.model = "Camry"
			scrap_vehicle.year = 2018
			scrap_vehicle.vehicle_status = "Processing"
			scrap_vehicle.acquisition_source = "US Auction"
			scrap_vehicle.insert(ignore_permissions=True)
			frappe.db.commit()

	def create_test_disassembly_plan(self):
		"""Create test disassembly plan"""
		if not frappe.db.exists("Disassembly Plan", "TEST-PLAN-001"):
			plan = frappe.new_doc("Disassembly Plan")
			plan.name = "TEST-PLAN-001"
			plan.scrap_vehicle = "TEST-SCRAP-001"
			plan.plan_name = "Test Disassembly Plan"
			plan.plan_status = "Active"
			plan.insert(ignore_permissions=True)
			frappe.db.commit()

	def test_extracted_parts_creation(self):
		"""Test basic extracted parts creation with Arabic fields"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Engine"
		part.part_name_ar = "محرك"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade A - Excellent"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 1500.000
		part.insert()

		self.assertEqual(part.part_name_ar, "محرك")
		self.assertEqual(part.currency, "OMR")
		self.assertEqual(part.certification_status, "Pending Inspection")
		self.assertTrue(part.part_code.startswith("9186-"))  # Last 4 digits of VIN
		self.assertTrue(part.barcode.startswith("UW-"))

	def test_quality_grade_validation(self):
		"""Test quality grade validation"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Battery"
		part.part_name_ar = "بطارية"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Invalid Grade"  # Invalid grade
		part.extraction_date = frappe.utils.today()

		with self.assertRaises(frappe.ValidationError):
			part.insert()

	def test_pricing_calculation_grade_a(self):
		"""Test pricing calculation for Grade A parts"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Transmission"
		part.part_name_ar = "ناقل الحركة"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade A - Excellent"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 2000.000
		part.physical_condition = "Excellent"
		part.functional_status = "Fully Functional"
		part.insert()

		# Grade A should be 70% * 1.10 (excellent condition) = 77% of base price
		expected_price = 2000.000 * 0.70 * 1.10
		self.assertAlmostEqual(part.suggested_price, expected_price, places=2)
		self.assertEqual(part.final_price, part.suggested_price)

	def test_pricing_calculation_grade_c_with_repair_cost(self):
		"""Test pricing calculation for Grade C parts with repair costs"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Radiator"
		part.part_name_ar = "المبرد"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade C - Average"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 500.000
		part.physical_condition = "Fair"
		part.functional_status = "Partially Functional"
		part.estimated_repair_cost = 50.000
		part.insert()

		# Grade C: 30% * 0.85 (fair condition) * 0.75 (partially functional) - 50 repair cost
		expected_price = (500.000 * 0.30 * 0.85 * 0.75) - 50.000
		min_price = 500.000 * 0.05  # 5% minimum
		expected_price = max(expected_price, min_price)

		self.assertAlmostEqual(part.suggested_price, expected_price, places=2)

	def test_arabic_name_requirement(self):
		"""Test Arabic name requirement validation"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Alternator"
		# Missing Arabic name
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade B - Good"
		part.extraction_date = frappe.utils.today()

		with self.assertRaises(frappe.ValidationError):
			part.insert()

	def test_grade_description_auto_update(self):
		"""Test automatic grade description updates"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Starter"
		part.part_name_ar = "بادئ الحركة"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade B - Good"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 300.000
		part.insert()

		self.assertIn("Good condition", part.grade_description)
		self.assertIn("40-60%", part.grade_description)
		self.assertIn("حالة جيدة", part.grade_description_ar)

	def test_barcode_generation(self):
		"""Test barcode generation logic"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Brake Pad"
		part.part_name_ar = "قطعة الفرامل"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade C - Average"
		part.extraction_date = frappe.utils.today()
		part.insert()

		self.assertTrue(part.barcode.startswith("UW-"))
		self.assertIn("9186-", part.barcode)  # Should include VIN suffix

	def test_dimension_validation(self):
		"""Test physical dimension validation"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Door"
		part.part_name_ar = "الباب"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade B - Good"
		part.extraction_date = frappe.utils.today()
		part.length_mm = -100  # Invalid negative dimension

		with self.assertRaises(frappe.ValidationError):
			part.insert()

	def test_pricing_variance_warning(self):
		"""Test pricing variance warning system"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Mirror"
		part.part_name_ar = "المرآة"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade A - Excellent"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 200.000
		part.suggested_price = 140.000  # Should be auto-calculated
		part.final_price = 250.000  # More than 50% variance

		# Should not throw error, but would show warning in UI
		part.insert()
		self.assertEqual(part.final_price, 250.000)

	def test_omr_currency_precision(self):
		"""Test OMR currency precision (3 decimal places)"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Headlight"
		part.part_name_ar = "المصباح الأمامي"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade B - Good"
		part.extraction_date = frappe.utils.today()
		part.base_price_new = 157.123456  # Many decimal places
		part.insert()

		# Should round to 3 decimal places for OMR
		suggested_price_str = f"{part.suggested_price:.3f}"
		self.assertEqual(len(suggested_price_str.split(".")[-1]), 3)

	def test_photo_gallery_integration(self):
		"""Test photo gallery integration"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Seat"
		part.part_name_ar = "المقعد"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade A - Excellent"
		part.extraction_date = frappe.utils.today()

		# Add photo entries
		part.append(
			"photo_gallery",
			{
				"photo_type": "Front View",
				"photo_description": "Clean front view",
				"shows_defect": 0,
			},
		)

		part.append(
			"photo_gallery",
			{
				"photo_type": "Defect/Damage",
				"photo_description": "Small scratch on side",
				"shows_defect": 1,
				"defect_severity": "Minor",
				"defect_description": "Surface scratch",
			},
		)

		part.insert()

		self.assertEqual(len(part.photo_gallery), 2)
		self.assertEqual(part.photo_gallery[0].photo_type_ar, "المنظر الأمامي")
		self.assertEqual(part.photo_gallery[1].defect_severity, "Minor")

	def test_api_pricing_analysis(self):
		"""Test pricing analysis API method"""
		from universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts import (
			get_part_pricing_analysis,
		)

		analysis = get_part_pricing_analysis(
			part_name="Engine", quality_grade="Grade A - Excellent", base_price_new=1500.000
		)

		self.assertEqual(analysis["multiplier"], 0.70)
		self.assertEqual(analysis["suggested_price"], 1500.000 * 0.70)
		self.assertIn("price_range", analysis)
		self.assertIn("market_position", analysis)
		self.assertEqual(analysis["base_price_new"], 1500.000)

	def test_api_quality_checklist(self):
		"""Test quality inspection checklist API"""
		from universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts import (
			generate_quality_inspection_checklist,
		)

		checklist = generate_quality_inspection_checklist(
			part_name="Transmission", quality_grade="Grade A - Excellent"
		)

		self.assertEqual(checklist["part_name"], "Transmission")
		self.assertEqual(checklist["target_grade"], "Grade A - Excellent")
		self.assertGreater(len(checklist["checklist"]), 4)  # Should have base + grade-specific checks
		self.assertGreater(checklist["estimated_time_minutes"], 10)

		# Check for Arabic translations
		arabic_checks = [item for item in checklist["checklist"] if "point_ar" in item]
		self.assertGreater(len(arabic_checks), 0)

	def test_api_market_comparison(self):
		"""Test market price comparison API"""
		from universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts import (
			get_market_price_comparison,
		)

		comparison = get_market_price_comparison(
			part_name="Battery", quality_grade="Grade B - Good", region="Oman"
		)

		self.assertEqual(comparison["region"], "Oman")
		self.assertEqual(comparison["currency"], "OMR")
		self.assertIn("estimated_market_price", comparison)
		self.assertIn("price_range", comparison)
		self.assertIn("recommendation", comparison)

	def test_workflow_integration(self):
		"""Test workflow state updates"""
		part = frappe.new_doc("Extracted Parts")
		part.part_name = "Wheel"
		part.part_name_ar = "العجلة"
		part.scrap_vehicle = "TEST-SCRAP-001"
		part.quality_grade = "Grade B - Good"
		part.extraction_date = frappe.utils.today()
		part.workflow_state = "Extracted"
		part.insert()

		self.assertEqual(part.workflow_state, "Extracted")
		self.assertEqual(part.availability_status, "Available")

		# Test status update
		part.workflow_state = "Inspected"
		part.certification_status = "Certified"
		part.inspector = frappe.session.user
		part.save()

		self.assertEqual(part.certification_status, "Certified")
		self.assertIsNotNone(part.inspection_date)


if __name__ == "__main__":
	unittest.main()
