# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import unittest

import frappe
from frappe.utils import cint, flt
from universal_workshop.scrap_management.doctype.storage_location.storage_location import (
	find_optimal_location,
	generate_location_report,
	get_location_hierarchy,
)


class TestStorageLocation(unittest.TestCase):
	"""Test cases for Storage Location functionality"""

	def setUp(self):
		"""Setup test data"""
		self.cleanup_test_data()
		self.create_test_warehouse()
		self.create_test_locations()

	def tearDown(self):
		"""Cleanup after tests"""
		self.cleanup_test_data()

	def cleanup_test_data(self):
		"""Remove test data"""
		# Delete test storage locations
		frappe.db.delete("Storage Location", {"location_code": ["like", "TEST-%"]})

		# Delete test warehouses
		frappe.db.delete("Warehouse", {"warehouse_name": ["like", "Test Warehouse%"]})

		frappe.db.commit()

	def create_test_warehouse(self):
		"""Create test warehouse"""
		if not frappe.db.exists("Warehouse", "Test Warehouse - UW"):
			warehouse = frappe.new_doc("Warehouse")
			warehouse.warehouse_name = "Test Warehouse"
			warehouse.company = frappe.defaults.get_user_default("Company") or "Universal Workshop"
			warehouse.insert(ignore_permissions=True)

	def create_test_locations(self):
		"""Create test storage locations"""
		locations_data = [
			{
				"location_code": "TEST-A01-001",
				"location_name": "Test Location A1",
				"location_name_ar": "موقع تجريبي أ1",
				"warehouse": "Test Warehouse - UW",
				"location_type": "Shelf",
				"max_weight_kg": 100.0,
				"max_volume_m3": 2.5,
				"max_items_count": 50,
				"accessibility_level": "Easy Access",
				"turnover_category": "Fast Moving",
			},
			{
				"location_code": "TEST-A01-002",
				"location_name": "Test Location A2",
				"location_name_ar": "موقع تجريبي أ2",
				"warehouse": "Test Warehouse - UW",
				"location_type": "Rack",
				"max_weight_kg": 200.0,
				"max_volume_m3": 5.0,
				"max_items_count": 100,
				"accessibility_level": "Standard Access",
				"turnover_category": "Medium Moving",
			},
			{
				"location_code": "TEST-B01-001",
				"location_name": "Test Location B1",
				"location_name_ar": "موقع تجريبي ب1",
				"warehouse": "Test Warehouse - UW",
				"location_type": "Bin",
				"max_weight_kg": 50.0,
				"max_volume_m3": 1.0,
				"max_items_count": 25,
				"accessibility_level": "Difficult Access",
				"turnover_category": "Slow Moving",
			},
		]

		for location_data in locations_data:
			if not frappe.db.exists("Storage Location", location_data["location_code"]):
				location = frappe.new_doc("Storage Location")
				location.update(location_data)
				location.insert(ignore_permissions=True)

	def test_location_creation(self):
		"""Test basic location creation"""
		location = frappe.new_doc("Storage Location")
		location.location_name = "Test New Location"
		location.location_name_ar = "موقع جديد تجريبي"
		location.warehouse = "Test Warehouse - UW"
		location.location_type = "Shelf"
		location.max_weight_kg = 75.0
		location.max_volume_m3 = 1.5

		# Should auto-generate location code
		location.insert(ignore_permissions=True)

		self.assertIsNotNone(location.location_code)
		self.assertTrue(location.location_code.startswith("TES-"))  # Warehouse abbreviation

		# Test barcode generation
		self.assertIsNotNone(location.location_barcode)
		self.assertTrue(location.location_barcode.startswith("LOC-"))

		# Test QR code generation
		self.assertIsNotNone(location.qr_code)

		# Cleanup
		frappe.delete_doc("Storage Location", location.name)

	def test_arabic_validation(self):
		"""Test Arabic name validation"""
		location = frappe.new_doc("Storage Location")
		location.location_name = "Test Location Without Arabic"
		location.warehouse = "Test Warehouse - UW"
		location.location_type = "Shelf"

		# Should fail without Arabic name
		with self.assertRaises(frappe.ValidationError):
			location.insert(ignore_permissions=True)

	def test_capacity_validation(self):
		"""Test capacity validation"""
		location = frappe.new_doc("Storage Location")
		location.location_name = "Test Capacity"
		location.location_name_ar = "اختبار السعة"
		location.warehouse = "Test Warehouse - UW"
		location.location_type = "Shelf"
		location.max_weight_kg = -10  # Invalid negative weight

		# Should fail with negative capacity
		with self.assertRaises(frappe.ValidationError):
			location.insert(ignore_permissions=True)

	def test_parent_location_validation(self):
		"""Test parent location relationship validation"""
		# Create parent location
		parent = frappe.new_doc("Storage Location")
		parent.location_name = "Parent Location"
		parent.location_name_ar = "الموقع الأب"
		parent.warehouse = "Test Warehouse - UW"
		parent.location_type = "Area"
		parent.insert(ignore_permissions=True)

		# Create child location
		child = frappe.new_doc("Storage Location")
		child.location_name = "Child Location"
		child.location_name_ar = "الموقع الفرعي"
		child.warehouse = "Test Warehouse - UW"
		child.location_type = "Shelf"
		child.parent_location = parent.name
		child.insert(ignore_permissions=True)

		# Test circular reference prevention
		parent.parent_location = child.name
		with self.assertRaises(frappe.ValidationError):
			parent.save()

		# Cleanup
		frappe.delete_doc("Storage Location", child.name)
		frappe.delete_doc("Storage Location", parent.name)

	def test_gps_coordinates_validation(self):
		"""Test GPS coordinates validation"""
		location = frappe.new_doc("Storage Location")
		location.location_name = "GPS Test Location"
		location.location_name_ar = "موقع اختبار GPS"
		location.warehouse = "Test Warehouse - UW"
		location.location_type = "Shelf"

		# Test invalid GPS format
		location.gps_coordinates = "invalid_format"
		with self.assertRaises(frappe.ValidationError):
			location.insert(ignore_permissions=True)

		# Test invalid GPS range
		location.gps_coordinates = "100.0,200.0"  # Out of valid range
		with self.assertRaises(frappe.ValidationError):
			location.insert(ignore_permissions=True)

		# Test valid GPS coordinates
		location.gps_coordinates = "23.5859,58.4059"  # Muscat coordinates
		location.insert(ignore_permissions=True)

		self.assertEqual(location.gps_coordinates, "23.5859,58.4059")

		# Cleanup
		frappe.delete_doc("Storage Location", location.name)

	def test_capacity_management(self):
		"""Test capacity calculation and management"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Test initial capacity
		capacity = location.get_available_capacity()
		self.assertEqual(capacity["weight_available_kg"], 100.0)
		self.assertEqual(capacity["volume_available_m3"], 2.5)
		self.assertEqual(capacity["items_available"], 50)

		# Test can_accommodate_part method
		can_accommodate, reason = location.can_accommodate_part(part_weight=50.0, part_volume=1.0)
		self.assertTrue(can_accommodate)

		# Test exceeding capacity
		can_accommodate, reason = location.can_accommodate_part(
			part_weight=150.0,
			part_volume=1.0,  # Exceeds max weight
		)
		self.assertFalse(can_accommodate)
		self.assertIn("weight", reason.lower())

	def test_efficiency_calculation(self):
		"""Test efficiency metrics calculation"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Set current usage
		location.current_weight_kg = 60.0
		location.current_volume_m3 = 1.5
		location.current_items_count = 30

		location.calculate_efficiency_metrics()

		# Check utilization percentages
		self.assertEqual(location.weight_utilization, 60.0)
		self.assertEqual(location.volume_utilization, 60.0)
		self.assertEqual(location.item_utilization, 60.0)
		self.assertEqual(location.efficiency_score, 60.0)

	def test_find_optimal_location(self):
		"""Test optimal location finding algorithm"""
		# Test finding location for a specific part
		optimal_locations = find_optimal_location(part_weight=25.0, part_volume=0.5, turnover_category="Fast")

		self.assertIsInstance(optimal_locations, list)

		if optimal_locations:
			# Should prioritize fast-moving locations for fast parts
			best_location = optimal_locations[0]
			self.assertIsInstance(best_location["score"], (int, float))
			self.assertGreater(best_location["score"], 0)

	def test_location_hierarchy(self):
		"""Test location hierarchy retrieval"""
		# Create hierarchical locations
		parent = frappe.new_doc("Storage Location")
		parent.location_name = "Zone A"
		parent.location_name_ar = "المنطقة أ"
		parent.warehouse = "Test Warehouse - UW"
		parent.location_type = "Area"
		parent.insert(ignore_permissions=True)

		child = frappe.new_doc("Storage Location")
		child.location_name = "Aisle A1"
		child.location_name_ar = "الممر أ1"
		child.warehouse = "Test Warehouse - UW"
		child.location_type = "Section"
		child.parent_location = parent.name
		child.insert(ignore_permissions=True)

		# Test hierarchy retrieval
		hierarchy = get_location_hierarchy("Test Warehouse - UW")

		self.assertIsInstance(hierarchy, list)

		# Cleanup
		frappe.delete_doc("Storage Location", child.name)
		frappe.delete_doc("Storage Location", parent.name)

	def test_location_report_generation(self):
		"""Test location utilization report generation"""
		report = generate_location_report("Test Warehouse - UW")

		self.assertIsInstance(report, dict)
		self.assertIn("locations", report)
		self.assertIn("summary", report)

		summary = report["summary"]
		self.assertIn("total_locations", summary)
		self.assertIn("high_utilization_count", summary)
		self.assertIn("low_utilization_count", summary)

		# Should have at least the test locations
		self.assertGreaterEqual(summary["total_locations"], 3)

	def test_barcode_generation(self):
		"""Test barcode and QR code generation"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Test barcode format
		self.assertIsNotNone(location.location_barcode)
		self.assertTrue(location.location_barcode.startswith("LOC-"))

		# Test QR code data
		self.assertIsNotNone(location.qr_code)

		# QR code should be valid JSON
		import json

		try:
			qr_data = json.loads(location.qr_code)
			self.assertEqual(qr_data["type"], "storage_location")
			self.assertEqual(qr_data["location_code"], location.location_code)
		except (json.JSONDecodeError, KeyError):
			self.fail("QR code data is not valid JSON or missing required fields")

	def test_location_update_usage(self):
		"""Test updating current usage from stored parts"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Mock extracted parts in this location
		# Note: This would require creating test Extracted Parts
		# For now, we'll test the method doesn't crash
		try:
			location.update_current_usage()
			# Should complete without error
			self.assertTrue(True)
		except Exception as e:
			self.fail(f"update_current_usage failed with error: {e!s}")

	def test_optimization_suggestions(self):
		"""Test storage optimization suggestions"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Test high utilization scenario
		location.efficiency_score = 95.0
		suggestions = location.suggest_optimization()

		self.assertIsInstance(suggestions, list)
		if suggestions:
			high_util_suggestion = next((s for s in suggestions if s["type"] == "warning"), None)
			self.assertIsNotNone(high_util_suggestion)

		# Test low utilization scenario
		location.efficiency_score = 20.0
		suggestions = location.suggest_optimization()

		if suggestions:
			low_util_suggestion = next((s for s in suggestions if s["type"] == "info"), None)
			self.assertIsNotNone(low_util_suggestion)

	def test_location_status_management(self):
		"""Test location status changes"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Test initial status
		self.assertEqual(location.location_status, "Available")

		# Test status change
		location.location_status = "Maintenance"
		location.save()

		# Reload and verify
		location.reload()
		self.assertEqual(location.location_status, "Maintenance")

		# Reset status
		location.location_status = "Available"
		location.save()

	def test_environmental_conditions(self):
		"""Test environmental condition validation"""
		location = frappe.new_doc("Storage Location")
		location.location_name = "Climate Test"
		location.location_name_ar = "اختبار المناخ"
		location.warehouse = "Test Warehouse - UW"
		location.location_type = "Shelf"
		location.temperature_controlled = 1
		location.temperature_range = "15-25"  # Valid range
		location.humidity_controlled = 1
		location.humidity_range = "40-60"  # Valid range

		location.insert(ignore_permissions=True)

		self.assertEqual(location.temperature_range, "15-25")
		self.assertEqual(location.humidity_range, "40-60")

		# Cleanup
		frappe.delete_doc("Storage Location", location.name)

	def test_security_levels(self):
		"""Test security level settings"""
		location = frappe.get_doc("Storage Location", {"location_code": "TEST-A01-001"})

		# Test security level assignment
		location.security_level = "High"
		location.restricted_access = 1
		location.access_permissions = "Manager and Senior Staff Only"

		location.save()

		location.reload()
		self.assertEqual(location.security_level, "High")
		self.assertTrue(location.restricted_access)

	def test_location_path_generation(self):
		"""Test location path generation for hierarchy"""
		# Create parent-child relationship
		parent = frappe.new_doc("Storage Location")
		parent.location_name = "Zone A"
		parent.location_name_ar = "المنطقة أ"
		parent.warehouse = "Test Warehouse - UW"
		parent.location_type = "Area"
		parent.insert(ignore_permissions=True)

		child = frappe.new_doc("Storage Location")
		child.location_name = "Aisle A1"
		child.location_name_ar = "الممر أ1"
		child.warehouse = "Test Warehouse - UW"
		child.location_type = "Section"
		child.parent_location = parent.name
		child.insert(ignore_permissions=True)

		# Check path generation
		child.reload()
		expected_path = "Zone A > Aisle A1"
		self.assertEqual(child.location_path, expected_path)

		# Cleanup
		frappe.delete_doc("Storage Location", child.name)
		frappe.delete_doc("Storage Location", parent.name)


# Helper function to run all tests
def run_storage_location_tests():
	"""Run all storage location tests"""
	suite = unittest.TestLoader().loadTestsFromTestCase(TestStorageLocation)
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	return result.wasSuccessful()


# Performance test
class TestStorageLocationPerformance(unittest.TestCase):
	"""Performance tests for Storage Location operations"""

	def test_bulk_location_creation(self):
		"""Test performance of creating multiple locations"""
		import time

		start_time = time.time()

		# Create 100 test locations
		for i in range(100):
			location = frappe.new_doc("Storage Location")
			location.location_name = f"Perf Test Location {i}"
			location.location_name_ar = f"موقع اختبار الأداء {i}"
			location.warehouse = "Test Warehouse - UW"
			location.location_type = "Shelf"
			location.max_weight_kg = 100.0
			location.insert(ignore_permissions=True)

		end_time = time.time()
		duration = end_time - start_time

		# Should complete within reasonable time (adjust threshold as needed)
		self.assertLess(duration, 30.0, "Bulk location creation took too long")

		# Cleanup
		frappe.db.delete("Storage Location", {"location_name": ["like", "Perf Test Location%"]})
		frappe.db.commit()

	def test_location_search_performance(self):
		"""Test performance of location search operations"""
		import time

		start_time = time.time()

		# Perform multiple search operations
		for i in range(50):
			find_optimal_location(part_weight=25.0, part_volume=0.5, turnover_category="Fast")

		end_time = time.time()
		duration = end_time - start_time

		# Should complete within reasonable time
		self.assertLess(duration, 10.0, "Location search operations took too long")


if __name__ == "__main__":
	unittest.main()
