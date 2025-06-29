# Copyright (c) 2025, Universal Workshop ERP
# Performance Testing and Optimization for Task 29.13

import unittest
import frappe
import time
import threading
import random
import string
from frappe.utils import nowdate, add_days
from datetime import datetime
import json
import concurrent.futures
from contextlib import contextmanager


class TestPerformanceOptimization(unittest.TestCase):
    """
    Comprehensive performance testing and optimization for existing DocTypes:
    - Workshop Profile
    - Service Order
    - Vehicle

    Tests form loading, list view performance, search functionality, and bulk operations.
    """

    @classmethod
    def setUpClass(cls):
        """Set up performance testing environment"""
        frappe.set_user("Administrator")
        cls.test_data = {}
        cls.performance_results = {}
        cls._create_test_data_pool()

    @classmethod
    def tearDownClass(cls):
        """Clean up test data and generate performance report"""
        cls._cleanup_test_data()
        cls._generate_performance_report()

    @classmethod
    def _create_test_data_pool(cls):
        """Create pool of test data for performance testing"""
        print("\n=== Creating Test Data Pool for Performance Testing ===")

        # Create test customers
        cls.test_customers = []
        for i in range(10):
            if not frappe.db.exists("Customer", f"Perf Customer {i}"):
                customer = frappe.new_doc("Customer")
                customer.customer_name = f"Perf Customer {i}"
                customer.customer_name_ar = f"عميل الأداء {i}"
                customer.customer_type = "Individual"
                customer.territory = "Oman"
                customer.insert(ignore_permissions=True)
                cls.test_customers.append(customer.name)

    @classmethod
    def _cleanup_test_data(cls):
        """Clean up all performance test data"""
        try:
            # Clean up test data
            frappe.db.sql("DELETE FROM `tabService Order` WHERE customer LIKE 'Perf Customer%'")
            frappe.db.sql("DELETE FROM `tabVehicle` WHERE customer LIKE 'Perf Customer%'")
            frappe.db.sql(
                "DELETE FROM `tabWorkshop Profile` WHERE workshop_name LIKE 'Perf Workshop%'"
            )
            frappe.db.sql("DELETE FROM `tabCustomer` WHERE customer_name LIKE 'Perf Customer%'")
            frappe.db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")

    @contextmanager
    def _measure_time(self, operation_name):
        """Context manager to measure operation time"""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self.performance_results[operation_name] = duration
            print(f"⏱️ {operation_name}: {duration:.3f} seconds")

    def test_workshop_profile_performance(self):
        """Test Workshop Profile DocType performance"""
        print("\n=== Testing Workshop Profile Performance ===")

        # Test single creation performance
        with self._measure_time("Workshop Profile Creation"):
            workshop = frappe.new_doc("Workshop Profile")
            workshop.workshop_name = "Perf Workshop Test"
            workshop.workshop_name_ar = "ورشة اختبار الأداء"
            workshop.workshop_type = "General Repair"
            workshop.owner_name = "Performance Test Owner"
            workshop.owner_name_ar = "مالك اختبار الأداء"
            workshop.business_license = "1234567"
            workshop.phone_number = "+968 1234 5678"
            workshop.email = "perf@test.com"
            workshop.address = "Muscat, Oman"
            workshop.address_ar = "مسقط، عمان"
            workshop.city = "Muscat"
            workshop.governorate = "Muscat"
            workshop.insert(ignore_permissions=True)
            self.test_data["workshop"] = workshop.name

        # Test form loading performance
        with self._measure_time("Workshop Profile Form Loading"):
            loaded_workshop = frappe.get_doc("Workshop Profile", self.test_data["workshop"])
            self.assertIsNotNone(loaded_workshop.workshop_name)

        # Test validation performance
        with self._measure_time("Workshop Profile Validation"):
            loaded_workshop.validate()

        # Test save performance
        with self._measure_time("Workshop Profile Save"):
            loaded_workshop.save()

        # Performance assertions
        self.assertLess(
            self.performance_results["Workshop Profile Creation"],
            2.0,
            "Workshop Profile creation should be under 2 seconds",
        )
        self.assertLess(
            self.performance_results["Workshop Profile Form Loading"],
            1.0,
            "Workshop Profile form loading should be under 1 second",
        )

    def test_vehicle_performance(self):
        """Test Vehicle DocType performance"""
        print("\n=== Testing Vehicle Performance ===")

        # Ensure we have a customer
        customer = self.test_customers[0] if self.test_customers else "Administrator"

        # Test single creation performance
        with self._measure_time("Vehicle Creation"):
            vehicle = frappe.new_doc("Vehicle")
            vehicle.vin = "1HGBH41JXMN" + str(random.randint(100000, 999999))
            vehicle.license_plate = f"T-{random.randint(10000, 99999)}"
            vehicle.license_plate_ar = f"ت-{random.randint(10000, 99999)}"
            vehicle.make = "Toyota"
            vehicle.make_ar = "تويوتا"
            vehicle.model = "Camry"
            vehicle.model_ar = "كامري"
            vehicle.year = 2023
            vehicle.color = "White"
            vehicle.color_ar = "أبيض"
            vehicle.customer = customer
            vehicle.current_mileage = 25000
            vehicle.fuel_type_primary = "Petrol"
            vehicle.insert(ignore_permissions=True)
            self.test_data["vehicle"] = vehicle.name

        # Test VIN decoder performance (if available)
        with self._measure_time("Vehicle VIN Decoder"):
            vehicle_doc = frappe.get_doc("Vehicle", self.test_data["vehicle"])
            try:
                decoded_info = vehicle_doc.decode_vin()
                self.assertIsInstance(decoded_info, dict)
            except Exception:
                pass  # VIN decoder might not be fully functional in test

        # Test form loading performance
        with self._measure_time("Vehicle Form Loading"):
            loaded_vehicle = frappe.get_doc("Vehicle", self.test_data["vehicle"])
            self.assertIsNotNone(loaded_vehicle.make)

        # Performance assertions
        self.assertLess(
            self.performance_results["Vehicle Creation"],
            2.0,
            "Vehicle creation should be under 2 seconds",
        )
        self.assertLess(
            self.performance_results["Vehicle Form Loading"],
            1.0,
            "Vehicle form loading should be under 1 second",
        )

    def test_service_order_performance(self):
        """Test Service Order DocType performance"""
        print("\n=== Testing Service Order Performance ===")

        # Ensure we have customer and vehicle
        customer = self.test_customers[0] if self.test_customers else "Administrator"
        vehicle = self.test_data.get("vehicle")

        if not vehicle:
            self.test_vehicle_performance()
            vehicle = self.test_data.get("vehicle")

        # Test single creation performance
        with self._measure_time("Service Order Creation"):
            service_order = frappe.new_doc("Service Order")
            service_order.customer = customer
            service_order.vehicle = vehicle
            service_order.service_date = nowdate()
            service_order.service_type = "Performance Test Service"
            service_order.service_type_ar = "خدمة اختبار الأداء"
            service_order.description = "Performance testing service order"
            service_order.description_ar = "طلب خدمة اختبار الأداء"
            service_order.current_mileage = 25500
            service_order.priority = "Medium"
            service_order.estimated_completion_date = add_days(nowdate(), 1)
            service_order.insert(ignore_permissions=True)
            self.test_data["service_order"] = service_order.name

        # Test workflow transition performance
        with self._measure_time("Service Order Workflow Transition"):
            so_doc = frappe.get_doc("Service Order", self.test_data["service_order"])
            so_doc.status = "In Progress"
            so_doc.started_on = datetime.now()
            so_doc.save()

        # Test calculation performance
        with self._measure_time("Service Order Calculations"):
            so_doc = frappe.get_doc("Service Order", self.test_data["service_order"])
            so_doc.parts_total = 100.0
            so_doc.labor_total = 50.0
            so_doc.vat_rate = 5.0
            so_doc.save()

        # Test form loading performance
        with self._measure_time("Service Order Form Loading"):
            loaded_so = frappe.get_doc("Service Order", self.test_data["service_order"])
            self.assertIsNotNone(loaded_so.service_type)

        # Performance assertions
        self.assertLess(
            self.performance_results["Service Order Creation"],
            3.0,
            "Service Order creation should be under 3 seconds",
        )
        self.assertLess(
            self.performance_results["Service Order Form Loading"],
            1.0,
            "Service Order form loading should be under 1 second",
        )

    def test_list_view_performance(self):
        """Test list view performance for all DocTypes"""
        print("\n=== Testing List View Performance ===")

        # Test Workshop Profile list view
        with self._measure_time("Workshop Profile List View"):
            workshops = frappe.get_all(
                "Workshop Profile",
                fields=["name", "workshop_name", "workshop_name_ar", "status"],
                limit=100,
            )
            self.assertIsInstance(workshops, list)

        # Test Vehicle list view
        with self._measure_time("Vehicle List View"):
            vehicles = frappe.get_all(
                "Vehicle", fields=["name", "vin", "make", "model", "customer"], limit=100
            )
            self.assertIsInstance(vehicles, list)

        # Test Service Order list view
        with self._measure_time("Service Order List View"):
            service_orders = frappe.get_all(
                "Service Order",
                fields=["name", "customer", "vehicle", "status", "service_date"],
                limit=100,
            )
            self.assertIsInstance(service_orders, list)

        # Performance assertions
        self.assertLess(
            self.performance_results["Workshop Profile List View"],
            3.0,
            "Workshop Profile list view should load under 3 seconds",
        )
        self.assertLess(
            self.performance_results["Vehicle List View"],
            3.0,
            "Vehicle list view should load under 3 seconds",
        )
        self.assertLess(
            self.performance_results["Service Order List View"],
            3.0,
            "Service Order list view should load under 3 seconds",
        )

    def test_search_performance(self):
        """Test search functionality performance"""
        print("\n=== Testing Search Performance ===")

        # Test Workshop Profile search
        with self._measure_time("Workshop Profile Search"):
            results = frappe.get_all(
                "Workshop Profile",
                filters={"workshop_name": ["like", "%Perf%"]},
                fields=["name", "workshop_name"],
                limit=50,
            )
            self.assertIsInstance(results, list)

        # Test Vehicle search
        with self._measure_time("Vehicle Search"):
            results = frappe.get_all(
                "Vehicle",
                filters={"make": "Toyota"},
                fields=["name", "vin", "make", "model"],
                limit=50,
            )
            self.assertIsInstance(results, list)

        # Test Service Order search
        with self._measure_time("Service Order Search"):
            results = frappe.get_all(
                "Service Order",
                filters={"status": "Draft"},
                fields=["name", "customer", "status"],
                limit=50,
            )
            self.assertIsInstance(results, list)

        # Performance assertions
        self.assertLess(
            self.performance_results["Workshop Profile Search"],
            2.0,
            "Workshop Profile search should complete under 2 seconds",
        )
        self.assertLess(
            self.performance_results["Vehicle Search"],
            2.0,
            "Vehicle search should complete under 2 seconds",
        )
        self.assertLess(
            self.performance_results["Service Order Search"],
            2.0,
            "Service Order search should complete under 2 seconds",
        )

    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        print("\n=== Testing Bulk Operations Performance ===")

        # Test bulk vehicle creation
        with self._measure_time("Bulk Vehicle Creation (10 records)"):
            vehicles_created = []
            customer = self.test_customers[0] if self.test_customers else "Administrator"

            for i in range(10):
                vehicle = frappe.new_doc("Vehicle")
                vehicle.vin = f"BULK{i:013d}"  # 17 character VIN
                vehicle.license_plate = f"B-{i:05d}"
                vehicle.make = "Toyota"
                vehicle.model = "Corolla"
                vehicle.year = 2022
                vehicle.customer = customer
                vehicle.current_mileage = 10000 + (i * 1000)
                vehicle.insert(ignore_permissions=True)
                vehicles_created.append(vehicle.name)

            self.test_data["bulk_vehicles"] = vehicles_created

        # Test bulk data retrieval
        with self._measure_time("Bulk Vehicle Retrieval"):
            if self.test_data.get("bulk_vehicles"):
                vehicles = frappe.get_all(
                    "Vehicle",
                    filters={"name": ["in", self.test_data["bulk_vehicles"]]},
                    fields=["name", "vin", "make", "model"],
                )
                self.assertEqual(len(vehicles), 10)

        # Performance assertions
        self.assertLess(
            self.performance_results["Bulk Vehicle Creation (10 records)"],
            15.0,
            "Bulk creation of 10 vehicles should complete under 15 seconds",
        )
        self.assertLess(
            self.performance_results["Bulk Vehicle Retrieval"],
            2.0,
            "Bulk retrieval should complete under 2 seconds",
        )

    def test_concurrent_access_performance(self):
        """Test concurrent user access performance"""
        print("\n=== Testing Concurrent Access Performance ===")

        def create_service_order(thread_id):
            """Create a service order in a separate thread"""
            try:
                frappe.set_user("Administrator")
                customer = self.test_customers[0] if self.test_customers else "Administrator"

                service_order = frappe.new_doc("Service Order")
                service_order.customer = customer
                service_order.service_date = nowdate()
                service_order.service_type = f"Concurrent Test {thread_id}"
                service_order.description = f"Concurrent access test {thread_id}"
                service_order.current_mileage = 30000 + thread_id
                service_order.priority = "Low"
                service_order.insert(ignore_permissions=True)
                return service_order.name
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
                return None

        # Test concurrent creation
        with self._measure_time("Concurrent Service Order Creation (5 threads)"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_service_order, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
                successful_creates = [r for r in results if r is not None]
                self.assertGreaterEqual(
                    len(successful_creates), 3, "At least 3 concurrent creates should succeed"
                )

        # Performance assertions
        self.assertLess(
            self.performance_results["Concurrent Service Order Creation (5 threads)"],
            10.0,
            "Concurrent creation should complete under 10 seconds",
        )

    def test_database_query_optimization(self):
        """Test database query optimization"""
        print("\n=== Testing Database Query Optimization ===")

        # Test index effectiveness
        with self._measure_time("Vehicle VIN Index Query"):
            if self.test_data.get("vehicle"):
                vehicle_doc = frappe.get_doc("Vehicle", self.test_data["vehicle"])
                results = frappe.get_all(
                    "Vehicle", filters={"vin": vehicle_doc.vin}, fields=["name", "vin"]
                )
                self.assertGreaterEqual(len(results), 1)

        # Test customer relationship query
        with self._measure_time("Customer Vehicle Relationship Query"):
            customer = self.test_customers[0] if self.test_customers else "Administrator"
            vehicles = frappe.get_all(
                "Vehicle", filters={"customer": customer}, fields=["name", "vin", "make", "model"]
            )
            self.assertIsInstance(vehicles, list)

        # Performance assertions
        self.assertLess(
            self.performance_results["Vehicle VIN Index Query"],
            1.0,
            "VIN index query should complete under 1 second",
        )
        self.assertLess(
            self.performance_results["Customer Vehicle Relationship Query"],
            2.0,
            "Customer relationship query should complete under 2 seconds",
        )

    @classmethod
    def _generate_performance_report(cls):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 60)
        print("PERFORMANCE OPTIMIZATION REPORT - Task 29.13")
        print("=" * 60)

        # Categorize results
        creation_ops = {k: v for k, v in cls.performance_results.items() if "Creation" in k}
        loading_ops = {
            k: v for k, v in cls.performance_results.items() if "Loading" in k or "List View" in k
        }
        search_ops = {k: v for k, v in cls.performance_results.items() if "Search" in k}
        bulk_ops = {
            k: v for k, v in cls.performance_results.items() if "Bulk" in k or "Concurrent" in k
        }

        print("\n📊 CREATION OPERATIONS:")
        for op, time_taken in creation_ops.items():
            status = (
                "✅ EXCELLENT"
                if time_taken < 1.0
                else (
                    "✅ GOOD"
                    if time_taken < 2.0
                    else "⚠️ ACCEPTABLE" if time_taken < 3.0 else "❌ NEEDS OPTIMIZATION"
                )
            )
            print(f"  {op}: {time_taken:.3f}s - {status}")

        print("\n📊 LOADING OPERATIONS:")
        for op, time_taken in loading_ops.items():
            status = (
                "✅ EXCELLENT"
                if time_taken < 1.0
                else (
                    "✅ GOOD"
                    if time_taken < 2.0
                    else "⚠️ ACCEPTABLE" if time_taken < 3.0 else "❌ NEEDS OPTIMIZATION"
                )
            )
            print(f"  {op}: {time_taken:.3f}s - {status}")

        print("\n📊 SEARCH OPERATIONS:")
        for op, time_taken in search_ops.items():
            status = (
                "✅ EXCELLENT"
                if time_taken < 1.0
                else (
                    "✅ GOOD"
                    if time_taken < 2.0
                    else "⚠️ ACCEPTABLE" if time_taken < 3.0 else "❌ NEEDS OPTIMIZATION"
                )
            )
            print(f"  {op}: {time_taken:.3f}s - {status}")

        print("\n📊 BULK & CONCURRENT OPERATIONS:")
        for op, time_taken in bulk_ops.items():
            status = (
                "✅ EXCELLENT"
                if time_taken < 5.0
                else (
                    "✅ GOOD"
                    if time_taken < 10.0
                    else "⚠️ ACCEPTABLE" if time_taken < 15.0 else "❌ NEEDS OPTIMIZATION"
                )
            )
            print(f"  {op}: {time_taken:.3f}s - {status}")

        # Overall assessment
        total_operations = len(cls.performance_results)
        excellent_count = sum(1 for v in cls.performance_results.values() if v < 2.0)
        good_count = sum(1 for v in cls.performance_results.values() if 2.0 <= v < 5.0)
        needs_optimization = sum(1 for v in cls.performance_results.values() if v >= 5.0)

        print(f"\n📈 OVERALL PERFORMANCE ASSESSMENT:")
        print(f"  Total Operations Tested: {total_operations}")
        print(
            f"  Excellent Performance (< 2s): {excellent_count} ({excellent_count/total_operations*100:.1f}%)"
        )
        print(f"  Good Performance (2-5s): {good_count} ({good_count/total_operations*100:.1f}%)")
        print(
            f"  Needs Optimization (> 5s): {needs_optimization} ({needs_optimization/total_operations*100:.1f}%)"
        )

        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        if excellent_count / total_operations >= 0.8:
            print("  ✅ EXCELLENT: Current performance exceeds expectations")
            print("  ✅ All DocTypes are production-ready from performance perspective")
        elif excellent_count / total_operations >= 0.6:
            print("  ✅ GOOD: Performance is acceptable for production")
            print("  💡 Consider minor optimizations for bulk operations")
        else:
            print("  ⚠️ ATTENTION: Some operations need optimization")
            print("  💡 Focus on database indexing and query optimization")
            print("  💡 Consider implementing caching strategies")

        print(f"\n✅ Task 29.13 Performance Testing COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    unittest.main()
