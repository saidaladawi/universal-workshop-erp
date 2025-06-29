# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import unittest

import frappe
from frappe.utils import add_days, flt, now, nowdate


class TestServiceOrder(unittest.TestCase):
	def setUp(self):
		"""Setup test data"""
		# Use ignore_permissions for tests
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Cleanup test data"""
		# Delete test service orders if any
		try:
			service_orders = frappe.get_all("Service Order", filters={"service_type": "Test Service"})
			for so in service_orders:
				frappe.delete_doc("Service Order", so.name, force=1)
		except Exception:
			pass

	def test_service_order_creation(self):
		"""Test basic service order creation"""
		service_order = frappe.new_doc("Service Order")
		service_order.service_type = "Test Service"
		service_order.service_date = nowdate()
		service_order.current_mileage = 55000
		service_order.description = "Test service order"
		service_order.priority = "Medium"

		# Should not raise any exception
		service_order.insert()

		# Check if fields are set correctly
		self.assertEqual(service_order.status, "Draft")
		self.assertIsNotNone(service_order.created_on)

	def test_service_order_validation(self):
		"""Test service order validation"""
		service_order = frappe.new_doc("Service Order")
		service_order.service_type = "Test Service"
		service_order.service_date = nowdate()
		service_order.current_mileage = 55000
		service_order.description = "Test validation"
		service_order.priority = "Medium"

		# Should validate successfully
		service_order.insert()
		self.assertIsNotNone(service_order.name)

	def test_service_order_calculations(self):
		"""Test basic calculations work"""
		service_order = frappe.new_doc("Service Order")
		service_order.service_type = "Test Service"
		service_order.service_date = nowdate()
		service_order.current_mileage = 55000
		service_order.description = "Test calculations"
		service_order.priority = "Medium"
		service_order.insert()

		# Test that calculations don't throw errors
		service_order.calculate_totals()
		self.assertGreaterEqual(flt(service_order.total_amount, 3), 0)

	def test_naming_series(self):
		"""Test naming series functionality"""
		service_order = frappe.new_doc("Service Order")
		service_order.service_type = "Test Service"
		service_order.service_date = nowdate()
		service_order.insert()

		# Check naming pattern exists
		self.assertIsNotNone(service_order.name)
		self.assertTrue(len(service_order.name) > 0)
