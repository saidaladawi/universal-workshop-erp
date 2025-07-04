# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import today, getdate
from universal_workshop.customer_satisfaction.doctype.customer_feedback.customer_feedback import (
    get_customer_feedback_summary,
    create_feedback_from_service_order,
)


class TestCustomerFeedback(unittest.TestCase):
    """Test cases for Customer Feedback DocType"""

    def setUp(self):
        """Set up test data"""
        self.test_customer = self.create_test_customer()
        self.test_service_order = self.create_test_service_order()

    def create_test_customer(self):
        """Create a test customer"""
        customer_name = f"Test Customer {frappe.utils.random_string(5)}"

        customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": "Individual",
                "territory": "Oman",
            }
        )
        customer.insert(ignore_permissions=True)

        return customer.name

    def create_test_service_order(self):
        """Create a test service order"""
        service_order = frappe.get_doc(
            {
                "doctype": "Service Order",
                "customer": self.test_customer,
                "service_date": today(),
                "status": "Completed",
                "completion_date": today(),
            }
        )
        service_order.insert(ignore_permissions=True)

        return service_order.name

    def test_customer_feedback_creation(self):
        """Test creating customer feedback"""
        feedback = frappe.get_doc(
            {
                "doctype": "Customer Feedback",
                "customer": self.test_customer,
                "service_order": self.test_service_order,
                "feedback_date": today(),
                "satisfaction_rating": 5,
                "service_quality_rating": 4,
                "staff_behavior_rating": 5,
                "positive_feedback": "Excellent service!",
                "would_recommend": 1,
                "return_customer": 1,
            }
        )

        feedback.insert(ignore_permissions=True)

        # Verify feedback was created
        self.assertTrue(feedback.name)
        self.assertEqual(feedback.satisfaction_rating, 5)

        # Clean up
        feedback.delete()

    def test_rating_validation(self):
        """Test rating validation"""
        feedback = frappe.get_doc(
            {
                "doctype": "Customer Feedback",
                "customer": self.test_customer,
                "feedback_date": today(),
                "satisfaction_rating": 6,  # Invalid rating > 5
            }
        )

        with self.assertRaises(frappe.ValidationError):
            feedback.insert(ignore_permissions=True)

    def test_customer_name_setting(self):
        """Test automatic customer name setting"""
        feedback = frappe.get_doc(
            {
                "doctype": "Customer Feedback",
                "customer": self.test_customer,
                "feedback_date": today(),
                "satisfaction_rating": 4,
            }
        )

        feedback.insert(ignore_permissions=True)

        # Verify customer name was set
        customer_name = frappe.db.get_value("Customer", self.test_customer, "customer_name")
        self.assertEqual(feedback.customer_name, customer_name)

        # Clean up
        feedback.delete()

    def test_feedback_summary(self):
        """Test feedback summary function"""
        # Create multiple feedback records
        for rating in [4, 5, 3, 5, 4]:
            feedback = frappe.get_doc(
                {
                    "doctype": "Customer Feedback",
                    "customer": self.test_customer,
                    "feedback_date": today(),
                    "satisfaction_rating": rating,
                    "would_recommend": 1 if rating >= 4 else 0,
                    "return_customer": 1 if rating >= 4 else 0,
                }
            )
            feedback.insert(ignore_permissions=True)

        # Test summary
        summary = get_customer_feedback_summary(
            customer=self.test_customer, from_date=today(), to_date=today()
        )

        self.assertEqual(summary["total_feedback"], 5)
        self.assertEqual(summary["average_satisfaction"], 4.2)
        self.assertEqual(summary["recommendation_rate"], 80.0)

        # Clean up
        frappe.db.delete("Customer Feedback", {"customer": self.test_customer})

    def test_create_feedback_from_service_order(self):
        """Test creating feedback from service order"""
        feedback = create_feedback_from_service_order(self.test_service_order)

        self.assertEqual(feedback.customer, self.test_customer)
        self.assertEqual(feedback.service_order, self.test_service_order)
        self.assertEqual(feedback.feedback_source, "Service Completion")

    def tearDown(self):
        """Clean up test data"""
        try:
            # Clean up feedback records
            frappe.db.delete("Customer Feedback", {"customer": self.test_customer})

            # Clean up service order
            if frappe.db.exists("Service Order", self.test_service_order):
                frappe.delete_doc("Service Order", self.test_service_order, force=True)

            # Clean up customer
            if frappe.db.exists("Customer", self.test_customer):
                frappe.delete_doc("Customer", self.test_customer, force=True)

        except Exception as e:
            frappe.log_error(f"Error in tearDown: {e}")


if __name__ == "__main__":
    unittest.main()
