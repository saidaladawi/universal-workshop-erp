# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import json
import unittest

import frappe
from frappe.test_runner import make_test_records


class TestWorkshopIntegration(unittest.TestCase):
	"""Comprehensive integration tests for workshop onboarding system"""

	def setUp(self):
		"""Setup test data and environment"""
		self.test_workshop_data = {
			"workshop_name": "Al Khaleej Auto Service",
			"workshop_name_ar": "خدمة الخليج للسيارات",
			"business_license": "1234567",
			"vat_number": "OM123456789012345",
			"contact_person": "Ahmed Al-Rashid",
			"contact_person_ar": "أحمد الراشد",
			"email": "ahmed@alkhaleej-auto.om",
			"phone": "+968 24123456",
			"address_line_1": "Muscat Industrial Area",
			"address_line_1_ar": "المنطقة الصناعية مسقط",
			"city": "Muscat",
			"governorate": "Muscat",
			"working_hours_start": "08:00:00",
			"working_hours_end": "18:00:00",
			"weekend_days": "Friday-Saturday",
			"services_offered": "Engine repair, brake service, oil change",
			"bank_name": "Bank Muscat",
			"iban": "OM123456789012345678901234",
			"initial_capital": 50000.000,
			"currency": "OMR",
		}

		# Clear any existing test data
		self.cleanup_test_data()

	def tearDown(self):
		"""Cleanup after tests"""
		self.cleanup_test_data()

	def cleanup_test_data(self):
		"""Remove test data"""
		test_entities = [
			("Workshop Profile", "business_license", "1234567"),
			("Workshop Onboarding Form", "business_license", "1234567"),
			("Onboarding Progress", "user_email", "test@example.com"),
		]

		for doctype, field, value in test_entities:
			existing = frappe.get_list(doctype, filters={field: value})
			for item in existing:
				frappe.delete_doc(doctype, item.name, force=True)

		frappe.db.commit()

	def test_complete_onboarding_flow(self):
		"""Test the complete onboarding workflow from start to finish"""

		# Step 1: Start onboarding wizard
		result = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard"
		)

		self.assertTrue(result["success"])
		self.assertIn("progress_id", result)
		progress_id = result["progress_id"]

		# Step 2: Test each wizard step
		steps = ["basic_info", "business_info", "contact_info", "operational_details", "financial_info"]

		for _i, step in enumerate(steps):
			step_data = self.get_step_data(step)

			# Validate step data
			validation_result = frappe.call(
				"universal_workshop.workshop_management.api.onboarding_wizard.validate_step_data",
				step=step,
				data=step_data,
			)
			self.assertTrue(validation_result["success"])

			# Save step data
			save_result = frappe.call(
				"universal_workshop.workshop_management.api.onboarding_wizard.save_step_data",
				progress_id=progress_id,
				step=step,
				data=step_data,
			)
			self.assertTrue(save_result["success"])

		# Step 3: Complete onboarding
		completion_result = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.complete_onboarding",
			progress_id=progress_id,
		)

		self.assertTrue(completion_result["success"])
		self.assertIn("workshop_profile_id", completion_result)

		# Step 4: Verify Workshop Profile was created
		workshop_profile = frappe.get_doc("Workshop Profile", completion_result["workshop_profile_id"])
		self.assertEqual(workshop_profile.workshop_name, "Al Khaleej Auto Service")
		self.assertEqual(workshop_profile.workshop_name_ar, "خدمة الخليج للسيارات")
		self.assertEqual(workshop_profile.business_license, "1234567")

	def test_web_form_submission(self):
		"""Test web form submission and Workshop Profile creation"""

		# Create onboarding form
		form = frappe.new_doc("Workshop Onboarding Form")
		for field, value in self.test_workshop_data.items():
			setattr(form, field, value)

		# Test validation
		form.validate()

		# Insert form (should trigger Workshop Profile creation)
		form.insert()

		# Verify Workshop Profile was created
		workshop_profiles = frappe.get_list(
			"Workshop Profile",
			filters={"business_license": "1234567"},
			fields=["name", "workshop_name", "workshop_name_ar"],
		)

		self.assertEqual(len(workshop_profiles), 1)
		profile = workshop_profiles[0]
		self.assertEqual(profile.workshop_name, "Al Khaleej Auto Service")

	def test_arabic_validation(self):
		"""Test Arabic text validation"""

		# Test valid Arabic text
		form = frappe.new_doc("Workshop Onboarding Form")
		form.workshop_name_ar = "خدمة الخليج للسيارات"
		form.contact_person_ar = "أحمد الراشد"
		form.address_line_1_ar = "المنطقة الصناعية مسقط"

		# Should not raise exception
		form.validate_arabic_fields()

		# Test invalid Arabic text (English in Arabic field)
		form.workshop_name_ar = "Al Khaleej Auto Service"

		with self.assertRaises(frappe.ValidationError):
			form.validate_arabic_fields()

	def test_oman_specific_validation(self):
		"""Test Oman-specific validation rules"""

		form = frappe.new_doc("Workshop Onboarding Form")

		# Test business license validation
		form.business_license = "123"  # Too short
		with self.assertRaises(frappe.ValidationError):
			form.validate_business_license()

		form.business_license = "1234567"  # Correct format
		form.validate_business_license()  # Should not raise

		# Test VAT number validation
		form.vat_number = "OM123"  # Too short
		with self.assertRaises(frappe.ValidationError):
			form.validate_vat_number()

		form.vat_number = "OM123456789012345"  # Correct format
		form.validate_vat_number()  # Should not raise

		# Test phone number validation
		form.phone = "12345"  # Invalid format
		with self.assertRaises(frappe.ValidationError):
			form.validate_phone_number()

		form.phone = "+968 24123456"  # Correct format
		form.validate_phone_number()  # Should not raise

	def test_concurrent_onboarding_sessions(self):
		"""Test multiple concurrent onboarding sessions"""

		# Start multiple sessions
		session1 = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard"
		)
		session2 = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard"
		)

		self.assertTrue(session1["success"])
		self.assertTrue(session2["success"])
		self.assertNotEqual(session1["progress_id"], session2["progress_id"])

		# Test data isolation
		step_data1 = {"workshop_name": "Workshop One", "workshop_name_ar": "ورشة واحد"}
		step_data2 = {"workshop_name": "Workshop Two", "workshop_name_ar": "ورشة اثنين"}

		frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.save_step_data",
			progress_id=session1["progress_id"],
			step="basic_info",
			data=step_data1,
		)

		frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.save_step_data",
			progress_id=session2["progress_id"],
			step="basic_info",
			data=step_data2,
		)

		# Verify data isolation
		progress1 = frappe.get_doc("Onboarding Progress", session1["progress_id"])
		progress2 = frappe.get_doc("Onboarding Progress", session2["progress_id"])

		data1 = json.loads(progress1.data)
		data2 = json.loads(progress2.data)

		self.assertEqual(data1["basic_info"]["workshop_name"], "Workshop One")
		self.assertEqual(data2["basic_info"]["workshop_name"], "Workshop Two")

	def test_error_handling_and_rollback(self):
		"""Test error handling and rollback functionality"""

		# Start onboarding
		result = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard"
		)
		progress_id = result["progress_id"]

		# Save some data
		frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.save_step_data",
			progress_id=progress_id,
			step="basic_info",
			data={"workshop_name": "Test Workshop"},
		)

		# Test rollback
		rollback_result = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.rollback_onboarding",
			progress_id=progress_id,
		)

		self.assertTrue(rollback_result["success"])

		# Verify progress record is deleted
		self.assertFalse(frappe.db.exists("Onboarding Progress", progress_id))

	def test_performance(self):
		"""Test system performance under load"""
		import time

		start_time = time.time()

		# Complete onboarding process
		result = frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard"
		)
		progress_id = result["progress_id"]

		# Add all steps
		steps = ["basic_info", "business_info", "contact_info", "operational_details", "financial_info"]
		for step in steps:
			frappe.call(
				"universal_workshop.workshop_management.api.onboarding_wizard.save_step_data",
				progress_id=progress_id,
				step=step,
				data=self.get_step_data(step),
			)

		# Complete onboarding
		frappe.call(
			"universal_workshop.workshop_management.api.onboarding_wizard.complete_onboarding",
			progress_id=progress_id,
		)

		end_time = time.time()
		duration = end_time - start_time

		# Should complete within 30 seconds (test strategy requirement)
		self.assertLess(duration, 30, f"Onboarding took {duration:.2f} seconds, exceeding 30-second limit")

	def get_step_data(self, step):
		"""Get test data for a specific step"""

		step_mapping = {
			"basic_info": {
				"workshop_name": self.test_workshop_data["workshop_name"],
				"workshop_name_ar": self.test_workshop_data["workshop_name_ar"],
				"business_license": self.test_workshop_data["business_license"],
				"vat_number": self.test_workshop_data["vat_number"],
			},
			"business_info": {
				"contact_person": self.test_workshop_data["contact_person"],
				"contact_person_ar": self.test_workshop_data["contact_person_ar"],
			},
			"contact_info": {
				"email": self.test_workshop_data["email"],
				"phone": self.test_workshop_data["phone"],
				"address_line_1": self.test_workshop_data["address_line_1"],
				"address_line_1_ar": self.test_workshop_data["address_line_1_ar"],
				"city": self.test_workshop_data["city"],
				"governorate": self.test_workshop_data["governorate"],
			},
			"operational_details": {
				"working_hours_start": self.test_workshop_data["working_hours_start"],
				"working_hours_end": self.test_workshop_data["working_hours_end"],
				"weekend_days": self.test_workshop_data["weekend_days"],
				"services_offered": self.test_workshop_data["services_offered"],
			},
			"financial_info": {
				"bank_name": self.test_workshop_data["bank_name"],
				"iban": self.test_workshop_data["iban"],
				"initial_capital": self.test_workshop_data["initial_capital"],
				"currency": self.test_workshop_data["currency"],
			},
		}

		return step_mapping.get(step, {})


if __name__ == "__main__":
	unittest.main()
