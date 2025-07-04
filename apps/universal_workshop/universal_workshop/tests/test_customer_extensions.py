# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest

import frappe
from frappe.test_runner import make_test_records
from universal_workshop.customer_management.custom_fields import setup_customer_extensions


class TestCustomerExtensions(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		"""Setup test environment"""
		# Ensure customer extensions are installed
		setup_customer_extensions()
		frappe.db.commit()

	def setUp(self):
		"""Setup test data for each test"""
		self.test_customer_data = {
			"customer_name": "Ahmed Al-Rashid Auto Services",
			"customer_name_ar": "أحمد الراشد لخدمات السيارات",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"territory": "Oman",
			"civil_id": "12345678",
			"nationality": "Oman",
			"preferred_language": "Arabic",
			"emergency_contact": "+968 95123456",
			"service_preferences": "Prefers morning appointments, needs Arabic-speaking technician",
			"preferred_service_time": "Morning (8AM-12PM)",
			"service_reminders_enabled": 1,
			"customer_notes": "VIP customer - priority handling required",
			"special_instructions": "Vehicle must be washed after service",
		}

	def test_customer_creation_with_arabic_fields(self):
		"""Test creating customer with Arabic fields"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		# Test insertion
		customer.insert()
		self.assertIsNotNone(customer.name)

		# Verify Arabic fields are saved correctly
		saved_customer = frappe.get_doc("Customer", customer.name)
		self.assertEqual(saved_customer.customer_name_ar, "أحمد الراشد لخدمات السيارات")
		self.assertEqual(saved_customer.preferred_language, "Arabic")

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_civil_id_validation(self):
		"""Test Oman Civil ID validation"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		# Test valid Civil ID (8 digits)
		customer.civil_id = "12345678"
		customer.insert()
		self.assertIsNotNone(customer.name)

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_emergency_contact_format(self):
		"""Test emergency contact phone number format"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		# Test valid Oman phone format
		customer.emergency_contact = "+968 95123456"
		customer.insert()
		self.assertIsNotNone(customer.name)

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_preferred_language_options(self):
		"""Test preferred language field options"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		# Test all valid language options
		language_options = ["Arabic", "English", "Both"]
		for lang in language_options:
			customer.preferred_language = lang
			customer.customer_name = f"Test Customer {lang}"
			customer.insert()

			saved_customer = frappe.get_doc("Customer", customer.name)
			self.assertEqual(saved_customer.preferred_language, lang)

			# Cleanup
			frappe.delete_doc("Customer", customer.name, force=True)

	def test_service_preferences_storage(self):
		"""Test service preferences field storage"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		service_prefs = "Prefers morning appointments, needs Arabic-speaking technician"
		customer.service_preferences = service_prefs
		customer.insert()

		saved_customer = frappe.get_doc("Customer", customer.name)
		self.assertEqual(saved_customer.service_preferences, service_prefs)

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_customer_notes_text_editor(self):
		"""Test customer notes text editor field"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)

		notes_html = "<p><strong>VIP Customer</strong></p><p>Special handling required</p>"
		customer.customer_notes = notes_html
		customer.insert()

		saved_customer = frappe.get_doc("Customer", customer.name)
		self.assertEqual(saved_customer.customer_notes, notes_html)

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_analytics_fields_defaults(self):
		"""Test customer analytics fields have correct defaults"""
		customer = frappe.new_doc("Customer")
		customer.update(self.test_customer_data)
		customer.insert()

		saved_customer = frappe.get_doc("Customer", customer.name)

		# Check default values
		self.assertEqual(saved_customer.total_services_count, 0)
		self.assertEqual(saved_customer.customer_lifetime_value, 0.0)
		self.assertEqual(saved_customer.average_service_value, 0.0)
		self.assertEqual(saved_customer.customer_status, "Active")

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)

	def test_child_doctypes_exist(self):
		"""Test that child DocTypes are created"""
		child_doctypes = [
			"Customer Vehicle Ownership",
			"Customer Communication Channel",
			"Customer Service Day",
			"Customer Communication History",
		]

		for doctype_name in child_doctypes:
			self.assertTrue(
				frappe.db.exists("DocType", doctype_name), f"Child DocType {doctype_name} should exist"
			)

	def test_custom_fields_exist(self):
		"""Test that custom fields are added to Customer DocType"""
		customer_meta = frappe.get_meta("Customer")

		required_fields = [
			"customer_name_ar",
			"civil_id",
			"nationality",
			"preferred_language",
			"communication_channels",
			"emergency_contact",
			"vehicle_ownership",
			"service_preferences",
			"communication_history",
			"customer_notes",
			"customer_lifetime_value",
			"total_services_count",
		]

		for field_name in required_fields:
			field = customer_meta.get_field(field_name)
			self.assertIsNotNone(field, f"Custom field {field_name} should exist in Customer DocType")


def run_customer_extension_tests():
	"""Run all customer extension tests"""
	frappe.init("universal.local")
	frappe.connect()

	# Run the test suite
	suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomerExtensions)
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	return result.wasSuccessful()


if __name__ == "__main__":
	unittest.main()
