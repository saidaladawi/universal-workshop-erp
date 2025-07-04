"""
Test Progress Tracking System
Tests for ServiceOrderProgressTracker and Service Progress Log DocType
"""

import unittest
import frappe
from frappe.utils import nowdate, get_datetime, add_days
from universal_workshop.sales_service.progress_tracking import ServiceOrderProgressTracker

class TestProgressTracking(unittest.TestCase):
    """Test Progress Tracking System"""

    def setUp(self):
        """Set up test data"""
        self.create_test_data()
        
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()

    def create_test_data(self):
        """Create test service order and related data"""
        # Create test customer
        if not frappe.db.exists("Customer", "Test Customer"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Test Customer"
            customer.customer_name_ar = "عميل تجريبي"
            customer.customer_type = "Individual"
            customer.customer_group = "Individual"
            customer.territory = "All Territories"
            customer.insert()
            
        # Create test sales order (service order)
        if not frappe.db.exists("Sales Order", "SO-TEST-001"):
            sales_order = frappe.new_doc("Sales Order")
            sales_order.name = "SO-TEST-001"
            sales_order.customer = "Test Customer"
            sales_order.delivery_date = add_days(nowdate(), 7)
            sales_order.service_estimate_reference = "EST-TEST-001"
            sales_order.insert()
            sales_order.submit()
            
        self.service_order_name = "SO-TEST-001"

    def test_progress_tracker_initialization(self):
        """Test ServiceOrderProgressTracker initialization"""
        tracker = ServiceOrderProgressTracker(self.service_order_name)
        
        self.assertIsNotNone(tracker.service_order)
        self.assertEqual(tracker.service_order.name, self.service_order_name)

    def test_update_progress_basic(self):
        """Test basic progress update functionality"""
        tracker = ServiceOrderProgressTracker(self.service_order_name)
        
        result = tracker.update_progress(
            operation_id="ENGINE_CHECK",
            status="in_progress",
            progress_percentage=25,
            technician="Administrator",
            notes="Engine inspection started",
            time_spent=0.5
        )
        
        self.assertEqual(result["status"], "success")

    def test_get_progress_dashboard(self):
        """Test getting progress dashboard data"""
        tracker = ServiceOrderProgressTracker(self.service_order_name)
        
        dashboard = tracker.get_progress_dashboard()
        
        self.assertEqual(dashboard["status"], "success")
        self.assertIn("data", dashboard)

def run_progress_tracking_tests():
    """Run progress tracking tests"""
    print("🧪 Running Progress Tracking System Tests...")
    
    test_categories = {
        "Basic Functionality": [
            "test_progress_tracker_initialization",
            "test_update_progress_basic", 
            "test_get_progress_dashboard"
        ]
    }
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in test_categories.items():
        print(f"\n📊 {category}:")
        
        for test_name in tests:
            total_tests += 1
            try:
                test_instance = TestProgressTracking()
                test_instance.setUp()
                
                test_method = getattr(test_instance, test_name)
                test_method()
                
                print(f"  ✅ {test_name}")
                passed_tests += 1
                
                test_instance.tearDown()
                
            except Exception as e:
                print(f"  ❌ {test_name}: {str(e)}")
    
    print(f"\n🎯 Progress Tracking Test Summary:")
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    run_progress_tracking_tests()
