import datetime
import unittest

import frappe
from frappe.test_runner import make_test_records


class TestCustomerLoyaltyPoints(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		# Create test customer
		if not frappe.db.exists("Customer", "Test Loyalty Customer"):
			customer = frappe.new_doc("Customer")
			customer.customer_name = "Test Loyalty Customer"
			customer.customer_type = "Individual"
			customer.insert()

	def tearDown(self):
		"""Clean up test data"""
		# Clean up test loyalty points
		frappe.db.sql("DELETE FROM `tabCustomer Loyalty Points` WHERE customer = 'Test Loyalty Customer'")
		frappe.db.commit()

	def test_earned_points_creation(self):
		"""Test creating earned loyalty points"""
		loyalty_points = frappe.new_doc("Customer Loyalty Points")
		loyalty_points.customer = "Test Loyalty Customer"
		loyalty_points.transaction_type = "Earned"
		loyalty_points.points = 100
		loyalty_points.service_type = "service"
		loyalty_points.invoice_amount = 100.0
		loyalty_points.remarks = "Test earned points"
		loyalty_points.insert()

		self.assertEqual(loyalty_points.points, 100)
		self.assertEqual(loyalty_points.transaction_type, "Earned")
		self.assertEqual(loyalty_points.status, "Active")
		self.assertIsNotNone(loyalty_points.expiry_date)

	def test_points_validation(self):
		"""Test points value validation"""
		# Test negative points for earned transaction
		with self.assertRaises(frappe.ValidationError):
			loyalty_points = frappe.new_doc("Customer Loyalty Points")
			loyalty_points.customer = "Test Loyalty Customer"
			loyalty_points.transaction_type = "Earned"
			loyalty_points.points = -50  # Invalid: negative points for earned
			loyalty_points.insert()

		# Test positive points for redeemed transaction
		with self.assertRaises(frappe.ValidationError):
			loyalty_points = frappe.new_doc("Customer Loyalty Points")
			loyalty_points.customer = "Test Loyalty Customer"
			loyalty_points.transaction_type = "Redeemed"
			loyalty_points.points = 50  # Invalid: positive points for redeemed
			loyalty_points.insert()

	def test_redemption_validation(self):
		"""Test redemption balance validation"""
		# First, create some earned points
		earned_points = frappe.new_doc("Customer Loyalty Points")
		earned_points.customer = "Test Loyalty Customer"
		earned_points.transaction_type = "Earned"
		earned_points.points = 100
		earned_points.insert()

		# Try to redeem more points than available
		with self.assertRaises(frappe.ValidationError):
			redemption = frappe.new_doc("Customer Loyalty Points")
			redemption.customer = "Test Loyalty Customer"
			redemption.transaction_type = "Redeemed"
			redemption.points = -200  # More than available
			redemption.insert()

	def test_expiry_date_auto_set(self):
		"""Test automatic expiry date setting"""
		loyalty_points = frappe.new_doc("Customer Loyalty Points")
		loyalty_points.customer = "Test Loyalty Customer"
		loyalty_points.transaction_type = "Earned"
		loyalty_points.points = 50
		loyalty_points.posting_date = datetime.date.today()
		loyalty_points.insert()

		# Check expiry date is set to 1 year from today
		expected_expiry = datetime.date.today() + datetime.timedelta(days=365)
		self.assertEqual(loyalty_points.expiry_date, expected_expiry)

	def test_points_expiry(self):
		"""Test points expiry functionality"""
		# Create earned points
		earned_points = frappe.new_doc("Customer Loyalty Points")
		earned_points.customer = "Test Loyalty Customer"
		earned_points.transaction_type = "Earned"
		earned_points.points = 100
		earned_points.insert()

		# Expire the points
		expiry_entry_name = earned_points.expire_points()

		# Check original entry is marked as expired
		self.assertEqual(earned_points.status, "Expired")

		# Check expiry entry is created
		expiry_entry = frappe.get_doc("Customer Loyalty Points", expiry_entry_name)
		self.assertEqual(expiry_entry.transaction_type, "Expired")
		self.assertEqual(expiry_entry.points, -100)

	def test_formatted_points_display(self):
		"""Test formatted points display"""
		# Test positive points
		earned_points = frappe.new_doc("Customer Loyalty Points")
		earned_points.points = 100
		self.assertEqual(earned_points.get_formatted_points(), "+100")

		# Test negative points
		redeemed_points = frappe.new_doc("Customer Loyalty Points")
		redeemed_points.points = -50
		self.assertEqual(redeemed_points.get_formatted_points(), "-50")

	def test_points_currency_value(self):
		"""Test points to currency conversion"""
		loyalty_points = frappe.new_doc("Customer Loyalty Points")
		loyalty_points.points = 1000

		# Test default conversion (1 point = 0.01 OMR)
		self.assertEqual(loyalty_points.get_points_value_in_currency(), 10.0)

		# Test custom conversion rate
		self.assertEqual(loyalty_points.get_points_value_in_currency(0.02), 20.0)
