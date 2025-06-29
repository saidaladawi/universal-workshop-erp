import unittest

import frappe
from frappe.test_runner import make_test_records


class TestVehicle(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		# Create test customer first
		if not frappe.db.exists("Customer", "Test Customer"):
			customer = frappe.new_doc("Customer")
			customer.customer_name = "Test Customer"
			customer.customer_type = "Individual"
			customer.insert()

	def tearDown(self):
		"""Clean up test data"""
		# Clean up test vehicles
		frappe.db.sql("DELETE FROM `tabVehicle` WHERE vin LIKE 'TEST%'")
		frappe.db.commit()

	def test_vehicle_creation(self):
		"""Test basic vehicle creation"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567890"
		vehicle.license_plate = "TEST-123"
		vehicle.make = "Toyota"
		vehicle.model = "Camry"
		vehicle.year = 2022
		vehicle.customer = "Test Customer"

		# Should save successfully
		vehicle.insert()
		self.assertEqual(vehicle.vin, "TESTVIN1234567890")
		self.assertEqual(vehicle.make, "Toyota")

	def test_vin_validation(self):
		"""Test VIN validation"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.license_plate = "TEST-124"
		vehicle.make = "Toyota"
		vehicle.model = "Camry"
		vehicle.year = 2022
		vehicle.customer = "Test Customer"

		# Test invalid VIN length
		vehicle.vin = "SHORT"
		with self.assertRaises(frappe.ValidationError):
			vehicle.insert()

		# Test invalid VIN characters
		vehicle.vin = "1234567890ABCDEFG"  # Contains invalid characters
		with self.assertRaises(frappe.ValidationError):
			vehicle.insert()

	def test_year_validation(self):
		"""Test year validation"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567891"
		vehicle.license_plate = "TEST-125"
		vehicle.make = "Toyota"
		vehicle.model = "Camry"
		vehicle.customer = "Test Customer"

		# Test year too old
		vehicle.year = 1800
		with self.assertRaises(frappe.ValidationError):
			vehicle.insert()

		# Test year too new
		import datetime

		vehicle.year = datetime.datetime.now().year + 5
		with self.assertRaises(frappe.ValidationError):
			vehicle.insert()

	def test_license_plate_validation(self):
		"""Test license plate validation"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567892"
		vehicle.make = "Toyota"
		vehicle.model = "Camry"
		vehicle.year = 2022
		vehicle.customer = "Test Customer"

		# Test license plate too long
		vehicle.license_plate = "A" * 25  # Too long
		with self.assertRaises(frappe.ValidationError):
			vehicle.insert()

	def test_customer_relationship(self):
		"""Test customer-vehicle relationship"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567893"
		vehicle.license_plate = "TEST-126"
		vehicle.make = "Honda"
		vehicle.model = "Civic"
		vehicle.year = 2021
		vehicle.customer = "Test Customer"

		vehicle.insert()

		# Test getting current owner
		owner = vehicle.get_current_owner()
		self.assertEqual(owner.name, "Test Customer")

	def test_maintenance_alerts(self):
		"""Test maintenance alerts"""
		import datetime

		from dateutil.relativedelta import relativedelta

		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567894"
		vehicle.license_plate = "TEST-127"
		vehicle.make = "Honda"
		vehicle.model = "Civic"
		vehicle.year = 2021
		vehicle.customer = "Test Customer"

		# Set insurance expiry to soon
		vehicle.insurance_expiry_date = datetime.date.today() + relativedelta(days=15)
		vehicle.insert()

		alerts = vehicle.get_maintenance_alerts()
		self.assertTrue(len(alerts) > 0)
		self.assertEqual(alerts[0]["type"], "insurance_expiry")

	def test_vin_decode_placeholder(self):
		"""Test VIN decode functionality (placeholder)"""
		vehicle = frappe.new_doc("Vehicle")
		vehicle.vin = "TESTVIN1234567895"
		vehicle.license_plate = "TEST-128"
		vehicle.customer = "Test Customer"

		# Test decode function
		decoded_info = vehicle.decode_vin()
		self.assertTrue("make" in decoded_info)
		self.assertTrue("model" in decoded_info)
