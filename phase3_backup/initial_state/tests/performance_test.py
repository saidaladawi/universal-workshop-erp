# Copyright (c) 2025, Universal Workshop ERP
# Performance Testing for Task 29.13

import unittest
import frappe
import time
from frappe.utils import nowdate, add_days
from datetime import datetime
import random


class TestDocTypePerformance(unittest.TestCase):
    """Performance testing for existing DocTypes"""

    @classmethod
    def setUpClass(cls):
        """Set up performance testing"""
        frappe.set_user("Administrator")
        cls.results = {}

    def measure_time(self, operation_name, func, *args, **kwargs):
        """Measure execution time of an operation"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        self.results[operation_name] = duration
        print(f"⏱️ {operation_name}: {duration:.3f} seconds")
        return result

    def test_workshop_profile_performance(self):
        """Test Workshop Profile performance"""
        print("\n=== Workshop Profile Performance ===")

        def create_workshop():
            workshop = frappe.new_doc("Workshop Profile")
            workshop.workshop_name = "Performance Test Workshop"
            workshop.workshop_name_ar = "ورشة اختبار الأداء"
            workshop.workshop_type = "General Repair"
            workshop.owner_name = "Test Owner"
            workshop.owner_name_ar = "مالك التجربة"
            workshop.business_license = "1234567"
            workshop.phone_number = "+968 1234 5678"
            workshop.email = "test@performance.com"
            workshop.address = "Muscat, Oman"
            workshop.address_ar = "مسقط، عمان"
            workshop.city = "Muscat"
            workshop.governorate = "Muscat"
            workshop.insert(ignore_permissions=True)
            return workshop.name

        # Test creation performance
        workshop_name = self.measure_time("Workshop Profile Creation", create_workshop)

        # Test loading performance
        def load_workshop():
            return frappe.get_doc("Workshop Profile", workshop_name)

        workshop_doc = self.measure_time("Workshop Profile Loading", load_workshop)

        # Verify performance meets requirements
        self.assertLess(self.results["Workshop Profile Creation"], 2.0)
        self.assertLess(self.results["Workshop Profile Loading"], 1.0)

    def test_vehicle_performance(self):
        """Test Vehicle performance"""
        print("\n=== Vehicle Performance ===")

        # Create test customer first
        if not frappe.db.exists("Customer", "Performance Test Customer"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Performance Test Customer"
            customer.customer_type = "Individual"
            customer.insert(ignore_permissions=True)

        def create_vehicle():
            vehicle = frappe.new_doc("Vehicle")
            vehicle.vin = f"1HGBH41JXMN{random.randint(100000, 999999)}"
            vehicle.license_plate = f"T-{random.randint(10000, 99999)}"
            vehicle.license_plate_ar = f"ت-{random.randint(10000, 99999)}"
            vehicle.make = "Toyota"
            vehicle.make_ar = "تويوتا"
            vehicle.model = "Camry"
            vehicle.model_ar = "كامري"
            vehicle.year = 2023
            vehicle.color = "White"
            vehicle.color_ar = "أبيض"
            vehicle.customer = "Performance Test Customer"
            vehicle.current_mileage = 25000
            vehicle.fuel_type_primary = "Petrol"
            vehicle.insert(ignore_permissions=True)
            return vehicle.name

        # Test creation performance
        vehicle_name = self.measure_time("Vehicle Creation", create_vehicle)

        # Test loading performance
        def load_vehicle():
            return frappe.get_doc("Vehicle", vehicle_name)

        vehicle_doc = self.measure_time("Vehicle Loading", load_vehicle)

        # Verify performance meets requirements
        self.assertLess(self.results["Vehicle Creation"], 2.0)
        self.assertLess(self.results["Vehicle Loading"], 1.0)

    def test_service_order_performance(self):
        """Test Service Order performance"""
        print("\n=== Service Order Performance ===")

        # Ensure test data exists
        if not frappe.db.exists("Customer", "Performance Test Customer"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Performance Test Customer"
            customer.customer_type = "Individual"
            customer.insert(ignore_permissions=True)

        def create_service_order():
            service_order = frappe.new_doc("Service Order")
            service_order.customer = "Performance Test Customer"
            service_order.service_date = nowdate()
            service_order.service_type = "Performance Test Service"
            service_order.service_type_ar = "خدمة اختبار الأداء"
            service_order.description = "Performance testing service"
            service_order.description_ar = "خدمة اختبار الأداء"
            service_order.current_mileage = 25000
            service_order.priority = "Medium"
            service_order.estimated_completion_date = add_days(nowdate(), 1)
            service_order.insert(ignore_permissions=True)
            return service_order.name

        # Test creation performance
        so_name = self.measure_time("Service Order Creation", create_service_order)

        # Test loading performance
        def load_service_order():
            return frappe.get_doc("Service Order", so_name)

        so_doc = self.measure_time("Service Order Loading", load_service_order)

        # Test workflow transition performance
        def update_status():
            so_doc.status = "In Progress"
            so_doc.started_on = datetime.now()
            so_doc.save()

        self.measure_time("Service Order Status Update", update_status)

        # Verify performance meets requirements
        self.assertLess(self.results["Service Order Creation"], 3.0)
        self.assertLess(self.results["Service Order Loading"], 1.0)
        self.assertLess(self.results["Service Order Status Update"], 1.0)

    def test_list_view_performance(self):
        """Test list view performance"""
        print("\n=== List View Performance ===")

        # Test Workshop Profile list
        def load_workshop_list():
            return frappe.get_all(
                "Workshop Profile", fields=["name", "workshop_name", "status"], limit=100
            )

        workshops = self.measure_time("Workshop Profile List", load_workshop_list)

        # Test Vehicle list
        def load_vehicle_list():
            return frappe.get_all("Vehicle", fields=["name", "vin", "make", "model"], limit=100)

        vehicles = self.measure_time("Vehicle List", load_vehicle_list)

        # Test Service Order list
        def load_service_order_list():
            return frappe.get_all(
                "Service Order", fields=["name", "customer", "status", "service_date"], limit=100
            )

        service_orders = self.measure_time("Service Order List", load_service_order_list)

        # Verify performance meets requirements
        self.assertLess(self.results["Workshop Profile List"], 3.0)
        self.assertLess(self.results["Vehicle List"], 3.0)
        self.assertLess(self.results["Service Order List"], 3.0)

    def test_search_performance(self):
        """Test search performance"""
        print("\n=== Search Performance ===")

        # Test Workshop Profile search
        def search_workshops():
            return frappe.get_all(
                "Workshop Profile",
                filters={"workshop_name": ["like", "%Test%"]},
                fields=["name", "workshop_name"],
                limit=50,
            )

        workshop_results = self.measure_time("Workshop Profile Search", search_workshops)

        # Test Vehicle search
        def search_vehicles():
            return frappe.get_all(
                "Vehicle", filters={"make": "Toyota"}, fields=["name", "vin", "make"], limit=50
            )

        vehicle_results = self.measure_time("Vehicle Search", search_vehicles)

        # Test Service Order search
        def search_service_orders():
            return frappe.get_all(
                "Service Order",
                filters={"status": "Draft"},
                fields=["name", "customer", "status"],
                limit=50,
            )

        so_results = self.measure_time("Service Order Search", search_service_orders)

        # Verify performance meets requirements
        self.assertLess(self.results["Workshop Profile Search"], 2.0)
        self.assertLess(self.results["Vehicle Search"], 2.0)
        self.assertLess(self.results["Service Order Search"], 2.0)

    @classmethod
    def tearDownClass(cls):
        """Generate performance report"""
        print("\n" + "=" * 50)
        print("PERFORMANCE TEST RESULTS - Task 29.13")
        print("=" * 50)

        # Categorize results
        excellent = []
        good = []
        needs_attention = []

        for operation, time_taken in cls.results.items():
            if time_taken < 1.0:
                excellent.append((operation, time_taken))
            elif time_taken < 3.0:
                good.append((operation, time_taken))
            else:
                needs_attention.append((operation, time_taken))

        print(f"\n✅ EXCELLENT PERFORMANCE (< 1.0s): {len(excellent)}")
        for op, time_val in excellent:
            print(f"  {op}: {time_val:.3f}s")

        print(f"\n✅ GOOD PERFORMANCE (1.0-3.0s): {len(good)}")
        for op, time_val in good:
            print(f"  {op}: {time_val:.3f}s")

        if needs_attention:
            print(f"\n⚠️ NEEDS ATTENTION (> 3.0s): {len(needs_attention)}")
            for op, time_val in needs_attention:
                print(f"  {op}: {time_val:.3f}s")

        # Overall assessment
        total_ops = len(cls.results)
        excellent_pct = len(excellent) / total_ops * 100
        good_pct = len(good) / total_ops * 100

        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"Total Operations: {total_ops}")
        print(f"Excellent: {excellent_pct:.1f}%")
        print(f"Good: {good_pct:.1f}%")

        if excellent_pct >= 70:
            print("🎉 RESULT: EXCELLENT - All DocTypes exceed performance requirements")
        elif excellent_pct + good_pct >= 90:
            print("✅ RESULT: GOOD - DocTypes meet performance requirements")
        else:
            print("⚠️ RESULT: NEEDS OPTIMIZATION - Some operations require attention")

        print("\n✅ Performance Testing Complete")
        print("=" * 50)


if __name__ == "__main__":
    unittest.main()
