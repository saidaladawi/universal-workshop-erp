# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import today, getdate, add_months
from datetime import timedelta
import json

# Import dashboard functions
from apps.universal_workshop.universal_workshop.www.universal_workshop_dashboard import (
    get_dashboard_data,
    get_kpi_data,
    get_recent_activities,
    get_dashboard_alerts,
    get_revenue_chart_data,
    get_service_orders_chart_data,
    get_satisfaction_chart_data,
    has_dashboard_access,
    get_workshop_config,
    refresh_dashboard_data,
)


class TestUniversalWorkshopDashboard(unittest.TestCase):
    """Comprehensive test suite for Universal Workshop Dashboard"""

    @classmethod
    def setUpClass(cls):
        """Set up test data for all tests"""
        cls.test_customer = cls.create_test_customer()
        cls.test_vehicle = cls.create_test_vehicle()
        cls.test_items = cls.create_test_items()
        cls.test_service_orders = cls.create_test_service_orders()
        cls.test_invoices = cls.create_test_invoices()
        cls.test_feedback = cls.create_test_feedback()

    @classmethod
    def create_test_customer(cls):
        """Create test customer"""
        try:
            customer = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": "Test Customer Dashboard",
                    "customer_name_ar": "عميل تجريبي للوحة",
                    "customer_type": "Individual",
                    "territory": "Oman",
                }
            )
            customer.insert(ignore_permissions=True)
            return customer.name
        except Exception as e:
            print(f"Error creating test customer: {e}")
            return None

    @classmethod
    def create_test_vehicle(cls):
        """Create test vehicle"""
        try:
            vehicle = frappe.get_doc(
                {
                    "doctype": "Vehicle",
                    "license_plate": "TEST-123",
                    "make": "Toyota",
                    "model": "Camry",
                    "year": 2020,
                    "customer": cls.test_customer,
                    "status": "Active",
                }
            )
            vehicle.insert(ignore_permissions=True)
            return vehicle.name
        except Exception as e:
            print(f"Error creating test vehicle: {e}")
            return None

    @classmethod
    def create_test_items(cls):
        """Create test items for inventory"""
        items = []
        try:
            for i in range(3):
                item = frappe.get_doc(
                    {
                        "doctype": "Item",
                        "item_code": f"TEST-ITEM-{i+1}",
                        "item_name": f"Test Item {i+1}",
                        "item_group": "Products",
                        "is_stock_item": 1,
                        "stock_uom": "Nos",
                    }
                )
                item.insert(ignore_permissions=True)

                # Create bin with low stock
                bin_doc = frappe.get_doc(
                    {
                        "doctype": "Bin",
                        "item_code": item.item_code,
                        "warehouse": "Stores - UW",
                        "actual_qty": 2,
                        "reorder_level": 10,
                    }
                )
                bin_doc.insert(ignore_permissions=True)

                items.append(item.name)
            return items
        except Exception as e:
            print(f"Error creating test items: {e}")
            return []

    @classmethod
    def create_test_service_orders(cls):
        """Create test service orders"""
        orders = []
        try:
            statuses = ["Pending", "In Progress", "Completed"]
            for i, status in enumerate(statuses):
                order = frappe.get_doc(
                    {
                        "doctype": "Service Order",
                        "customer": cls.test_customer,
                        "vehicle": cls.test_vehicle,
                        "service_date": today(),
                        "status": status,
                        "expected_completion_date": today() + timedelta(days=2),
                        "completion_date": today() if status == "Completed" else None,
                    }
                )
                order.insert(ignore_permissions=True)
                orders.append(order.name)
            return orders
        except Exception as e:
            print(f"Error creating test service orders: {e}")
            return []

    @classmethod
    def create_test_invoices(cls):
        """Create test sales invoices"""
        invoices = []
        try:
            for i in range(3):
                invoice = frappe.get_doc(
                    {
                        "doctype": "Sales Invoice",
                        "customer": cls.test_customer,
                        "posting_date": today(),
                        "due_date": today() + timedelta(days=30),
                        "grand_total": 100.0 * (i + 1),
                        "docstatus": 1,
                    }
                )
                invoice.insert(ignore_permissions=True)
                invoices.append(invoice.name)
            return invoices
        except Exception as e:
            print(f"Error creating test invoices: {e}")
            return []

    @classmethod
    def create_test_feedback(cls):
        """Create test customer feedback"""
        feedback_list = []
        try:
            ratings = [4, 5, 3, 5, 4]
            for rating in ratings:
                feedback = frappe.get_doc(
                    {
                        "doctype": "Customer Feedback",
                        "customer": cls.test_customer,
                        "feedback_date": today(),
                        "satisfaction_rating": rating,
                        "service_quality_rating": rating,
                        "would_recommend": 1 if rating >= 4 else 0,
                        "return_customer": 1 if rating >= 4 else 0,
                    }
                )
                feedback.insert(ignore_permissions=True)
                feedback_list.append(feedback.name)
            return feedback_list
        except Exception as e:
            print(f"Error creating test feedback: {e}")
            return []

    def test_dashboard_access_permissions(self):
        """Test dashboard access permissions"""
        # Test with administrator role
        frappe.set_user("Administrator")
        self.assertTrue(has_dashboard_access())

        # Test access function exists and returns boolean
        access = has_dashboard_access()
        self.assertIsInstance(access, bool)

    def test_workshop_config(self):
        """Test workshop configuration retrieval"""
        config = get_workshop_config()

        # Should return a dictionary
        self.assertIsInstance(config, dict)

        # Should have default values if no workshop profile exists
        if not config:
            # If no workshop profile, should return default config
            self.assertIn("workshop_name", config)

    def test_dashboard_data_structure(self):
        """Test dashboard data structure and content"""
        data = get_dashboard_data()

        # Should return a dictionary
        self.assertIsInstance(data, dict)

        # Check required sections
        expected_sections = ["service_orders", "customers", "vehicles", "financial", "inventory"]
        for section in expected_sections:
            self.assertIn(section, data)

        # Check service orders data
        if "service_orders" in data:
            service_data = data["service_orders"]
            self.assertIn("total", service_data)
            self.assertIn("pending", service_data)
            self.assertIn("in_progress", service_data)
            self.assertIn("completed_today", service_data)

    def test_kpi_data_calculation(self):
        """Test KPI data calculation"""
        kpi_data = get_kpi_data()

        # Should return a dictionary
        self.assertIsInstance(kpi_data, dict)

        # Check KPI sections
        expected_kpis = [
            "service_efficiency",
            "customer_satisfaction",
            "revenue_growth",
            "technician_utilization",
        ]
        for kpi in expected_kpis:
            if kpi in kpi_data:
                self.assertIsInstance(kpi_data[kpi], dict)

    def test_recent_activities(self):
        """Test recent activities retrieval"""
        activities = get_recent_activities()

        # Should return a list
        self.assertIsInstance(activities, list)

        # Check activity structure if activities exist
        if activities:
            activity = activities[0]
            required_fields = ["type", "title", "description", "timestamp", "icon"]
            for field in required_fields:
                self.assertIn(field, activity)

    def test_dashboard_alerts(self):
        """Test dashboard alerts generation"""
        alerts = get_dashboard_alerts()

        # Should return a list
        self.assertIsInstance(alerts, list)

        # Check alert structure if alerts exist
        if alerts:
            alert = alerts[0]
            required_fields = ["type", "title", "message", "priority"]
            for field in required_fields:
                self.assertIn(field, alert)

    def test_revenue_chart_data(self):
        """Test revenue chart data generation"""
        # Test weekly data
        weekly_data = get_revenue_chart_data("week")
        self.assertIsInstance(weekly_data, dict)

        # Test monthly data
        monthly_data = get_revenue_chart_data("month")
        self.assertIsInstance(monthly_data, dict)

        # Check chart structure
        if weekly_data:
            self.assertIn("labels", weekly_data)
            self.assertIn("datasets", weekly_data)

    def test_service_orders_chart_data(self):
        """Test service orders chart data generation"""
        chart_data = get_service_orders_chart_data("week")

        # Should return a dictionary
        self.assertIsInstance(chart_data, dict)

        # Check chart structure
        if chart_data:
            self.assertIn("labels", chart_data)
            self.assertIn("datasets", chart_data)

    def test_satisfaction_chart_data(self):
        """Test customer satisfaction chart data generation"""
        # Test weekly data
        weekly_data = get_satisfaction_chart_data("week")
        self.assertIsInstance(weekly_data, dict)

        # Test monthly data
        monthly_data = get_satisfaction_chart_data("month")
        self.assertIsInstance(monthly_data, dict)

    def test_refresh_dashboard_data(self):
        """Test dashboard data refresh functionality"""
        refreshed_data = refresh_dashboard_data()

        # Should return a dictionary
        self.assertIsInstance(refreshed_data, dict)

        # Check required sections
        if "dashboard_data" in refreshed_data:
            self.assertIsInstance(refreshed_data["dashboard_data"], dict)

        if "kpi_data" in refreshed_data:
            self.assertIsInstance(refreshed_data["kpi_data"], dict)

        if "alerts" in refreshed_data:
            self.assertIsInstance(refreshed_data["alerts"], list)

    def test_error_handling(self):
        """Test error handling in dashboard functions"""
        # Test functions handle missing data gracefully
        try:
            # These should not raise exceptions even with limited test data
            get_dashboard_data()
            get_kpi_data()
            get_recent_activities()
            get_dashboard_alerts()
            get_revenue_chart_data("week")
            get_service_orders_chart_data("week")
            get_satisfaction_chart_data("week")
        except Exception as e:
            self.fail(f"Dashboard functions should handle errors gracefully: {e}")

    def test_data_types_and_formats(self):
        """Test data types and formats returned by dashboard functions"""
        dashboard_data = get_dashboard_data()

        # Test numeric values are properly formatted
        if dashboard_data and "financial" in dashboard_data:
            financial = dashboard_data["financial"]
            if "today_revenue" in financial:
                self.assertIsInstance(financial["today_revenue"], (int, float))
            if "monthly_revenue" in financial:
                self.assertIsInstance(financial["monthly_revenue"], (int, float))

    def test_customer_feedback_integration(self):
        """Test customer feedback integration with dashboard"""
        # Test that customer feedback data is properly integrated
        kpi_data = get_kpi_data()

        if "customer_satisfaction" in kpi_data:
            satisfaction = kpi_data["customer_satisfaction"]
            if "avg_rating" in satisfaction:
                # Rating should be between 0 and 5
                rating = satisfaction["avg_rating"]
                self.assertTrue(0 <= rating <= 5)

    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        try:
            # Clean up in reverse order of creation
            if hasattr(cls, "test_feedback"):
                for feedback_id in cls.test_feedback:
                    if frappe.db.exists("Customer Feedback", feedback_id):
                        frappe.delete_doc("Customer Feedback", feedback_id, force=True)

            if hasattr(cls, "test_invoices"):
                for invoice_id in cls.test_invoices:
                    if frappe.db.exists("Sales Invoice", invoice_id):
                        frappe.delete_doc("Sales Invoice", invoice_id, force=True)

            if hasattr(cls, "test_service_orders"):
                for order_id in cls.test_service_orders:
                    if frappe.db.exists("Service Order", order_id):
                        frappe.delete_doc("Service Order", order_id, force=True)

            if hasattr(cls, "test_items"):
                for item_id in cls.test_items:
                    # Delete bins first
                    frappe.db.delete("Bin", {"item_code": item_id})
                    if frappe.db.exists("Item", item_id):
                        frappe.delete_doc("Item", item_id, force=True)

            if hasattr(cls, "test_vehicle") and cls.test_vehicle:
                if frappe.db.exists("Vehicle", cls.test_vehicle):
                    frappe.delete_doc("Vehicle", cls.test_vehicle, force=True)

            if hasattr(cls, "test_customer") and cls.test_customer:
                if frappe.db.exists("Customer", cls.test_customer):
                    frappe.delete_doc("Customer", cls.test_customer, force=True)

            frappe.db.commit()

        except Exception as e:
            print(f"Error in tearDown: {e}")


def run_dashboard_tests():
    """Run all dashboard tests"""
    print("Starting Universal Workshop Dashboard Tests...")

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestUniversalWorkshopDashboard)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'PASSED' if success else 'FAILED'}")

    return success


if __name__ == "__main__":
    run_dashboard_tests()
