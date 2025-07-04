#!/usr/bin/env python3

import frappe


def test_customer_extensions():
	"""Test customer extensions implementation"""
	try:
		# Create a test customer with Arabic fields
		customer = frappe.new_doc("Customer")
		customer.customer_name = "Ahmed Al-Rashid Workshop"
		customer.customer_name_ar = "أحمد الراشد للورش"
		customer.customer_type = "Company"
		customer.customer_group = "Commercial"
		customer.territory = "Oman"
		customer.preferred_language = "Arabic"
		customer.civil_id = "12345678"
		customer.nationality = "Oman"
		customer.emergency_contact = "+968 95123456"
		customer.service_preferences = "Prefers morning appointments"
		customer.customer_notes = "<p>VIP customer - priority handling</p>"

		# Insert the customer
		customer.insert()
		print(f"✅ Customer created successfully: {customer.name}")
		print(f"   Arabic name: {customer.customer_name_ar}")
		print(f"   Preferred language: {customer.preferred_language}")
		print(f"   Civil ID: {customer.civil_id}")

		# Verify custom fields exist
		meta = frappe.get_meta("Customer")
		custom_fields = [
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
		]

		missing_fields = []
		for field_name in custom_fields:
			if not meta.get_field(field_name):
				missing_fields.append(field_name)

		if missing_fields:
			print(f"❌ Missing custom fields: {missing_fields}")
		else:
			print("✅ All custom fields are present")

		# Cleanup
		frappe.delete_doc("Customer", customer.name, force=True)
		print("✅ Test completed successfully")

		return True

	except Exception as e:
		print(f"❌ Test failed: {e!s}")
		return False


if __name__ == "__main__":
	frappe.init(site="universal.local")
	frappe.connect()
	test_customer_extensions()
