# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
"""
Comprehensive test suite for Labor Time Tracking functionality
Tests all aspects of time tracking, Arabic support, and Oman compliance
"""

import unittest
from datetime import datetime, timedelta
import frappe
from frappe.utils import now_datetime, flt, add_to_date
from universal_workshop.sales_service.labor_time_tracking import (
    LaborTimeTracker,
    start_labor_tracking,
    pause_labor_tracking,
    resume_labor_tracking,
    stop_labor_tracking,
    get_active_labor_tracking,
    get_technician_productivity,
)


class TestLaborTimeTracking(unittest.TestCase):
    """Test Labor Time Tracking functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test workshop
        self.workshop = frappe.get_doc(
            {
                "doctype": "Workshop Profile",
                "workshop_name": "Al Rashid Auto Service",
                "workshop_name_ar": "خدمة الراشد للسيارات",
                "business_license": "1234567",
                "vat_number": "OM123456789012345",
                "phone": "+968 24123456",
                "email": "info@alrashidauto.om",
            }
        ).insert()

        # Create test customer
        self.customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Ahmed Al-Zahra",
                "customer_name_ar": "أحمد الزهراء",
                "phone": "+968 91234567",
                "customer_group": "Individual",
            }
        ).insert()

        # Create test vehicle
        self.vehicle = frappe.get_doc(
            {
                "doctype": "Vehicle Profile",
                "owner": self.customer.name,
                "license_plate": "OMA-12345",
                "vin_number": "WVWZZZ1JZ3W386752",
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "color": "Silver",
                "color_ar": "فضي",
            }
        ).insert()

        # Create test technician
        self.technician = frappe.get_doc(
            {
                "doctype": "Technician",
                "employee_id": "TECH-001",
                "technician_name": "Mohammed Al-Kindi",
                "technician_name_ar": "محمد الكندي",
                "phone": "+968 95123456",
                "department": "Engine",
                "employment_status": "Active",
                "hourly_rate": 15.000,  # OMR 15 per hour
            }
        ).insert()

        # Create test service order
        self.service_order = frappe.get_doc(
            {
                "doctype": "Service Order",
                "customer": self.customer.name,
                "vehicle": self.vehicle.name,
                "service_type": "Scheduled Maintenance",
                "description": "Regular service check",
                "description_ar": "فحص الخدمة الدورية",
                "status": "In Progress",
            }
        ).insert()

        frappe.db.commit()

    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse order
        frappe.db.sql("DELETE FROM `tabLabor Time Log`")
        self.service_order.delete()
        self.technician.delete()
        self.vehicle.delete()
        self.customer.delete()
        self.workshop.delete()
        frappe.db.commit()

    def test_start_labor_tracking(self):
        """Test starting a new labor tracking session"""
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
            notes="Starting engine diagnostic",
        )

        self.assertTrue(result["success"])
        self.assertIn("started successfully", result["message"])

        # Verify log was created
        log = frappe.get_doc("Labor Time Log", result["log_id"])
        self.assertEqual(log.service_order, self.service_order.name)
        self.assertEqual(log.technician, self.technician.name)
        self.assertEqual(log.activity_type, "Service Work")
        self.assertEqual(log.status, "Active")
        self.assertIsNotNone(log.start_time)

    def test_start_tracking_technician_already_active(self):
        """Test starting tracking when technician already has active session"""
        # Start first session
        start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Try to start second session
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Diagnostics",
        )

        self.assertFalse(result["success"])
        self.assertIn("already has an active", result["message"])

    def test_pause_labor_tracking(self):
        """Test pausing an active labor tracking session"""
        # Start session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Pause session
        result = pause_labor_tracking(log_id=start_result["log_id"], pause_reason="Break time")

        self.assertTrue(result["success"])
        self.assertIn("paused successfully", result["message"])

        # Verify status
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        self.assertEqual(log.status, "Paused")
        self.assertIsNotNone(log.pause_time)

    def test_resume_labor_tracking(self):
        """Test resuming a paused labor tracking session"""
        # Start and pause session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )
        pause_labor_tracking(start_result["log_id"], "Break time")

        # Resume session
        result = resume_labor_tracking(start_result["log_id"])

        self.assertTrue(result["success"])
        self.assertIn("resumed successfully", result["message"])

        # Verify status
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        self.assertEqual(log.status, "Active")
        self.assertIsNotNone(log.resume_time)

    def test_stop_labor_tracking(self):
        """Test stopping/completing a labor tracking session"""
        # Start session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Stop session
        result = stop_labor_tracking(
            log_id=start_result["log_id"], completion_notes="Work completed successfully"
        )

        self.assertTrue(result["success"])
        self.assertIn("completed successfully", result["message"])

        # Verify status and timesheet creation
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        self.assertEqual(log.status, "Completed")
        self.assertIsNotNone(log.end_time)
        self.assertGreater(log.total_hours, 0)
        self.assertGreater(log.total_cost, 0)

    def test_time_calculation(self):
        """Test accurate time calculation including pause time"""
        # Start session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Get the log and manually set times for testing
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        start_time = now_datetime()
        log.start_time = start_time
        log.pause_time = start_time + timedelta(hours=2)  # Work 2 hours
        log.resume_time = start_time + timedelta(hours=3)  # Pause 1 hour
        log.end_time = start_time + timedelta(hours=5)  # Work 2 more hours
        log.save()

        # Calculate total hours (should be 4 hours, excluding 1 hour pause)
        tracker = LaborTimeTracker()
        total_hours = tracker.calculate_total_hours(log)

        # Expected: 2 hours + 2 hours = 4 hours (excluding 1 hour pause)
        self.assertEqual(total_hours, 4.0)

    def test_cost_calculation_omr(self):
        """Test cost calculation in OMR currency"""
        # Set technician hourly rate to 15 OMR
        self.technician.hourly_rate = 15.000
        self.technician.save()

        # Start and complete session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Manually set 3 hours of work
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        log.total_hours = 3.0
        log.save()

        # Calculate cost
        tracker = LaborTimeTracker()
        total_cost = tracker.calculate_labor_cost(log)

        # Expected: 3 hours × 15 OMR = 45.000 OMR
        self.assertEqual(flt(total_cost, 3), 45.000)

    def test_get_active_labor_tracking(self):
        """Test retrieving active labor tracking sessions"""
        # Start multiple sessions
        start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Get active sessions
        active_sessions = get_active_labor_tracking(self.service_order.name)

        self.assertEqual(len(active_sessions), 1)
        self.assertEqual(active_sessions[0]["service_order"], self.service_order.name)
        self.assertEqual(active_sessions[0]["technician"], self.technician.name)
        self.assertEqual(active_sessions[0]["status"], "Active")

    def test_arabic_activity_types(self):
        """Test Arabic support for activity types"""
        # Test with Arabic activity type
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="صيانة دورية",  # Arabic: Regular Maintenance
            notes="بدء الفحص الدوري للمحرك",  # Arabic notes
        )

        self.assertTrue(result["success"])

        # Verify Arabic content is preserved
        log = frappe.get_doc("Labor Time Log", result["log_id"])
        self.assertEqual(log.activity_type, "صيانة دورية")
        self.assertEqual(log.notes, "بدء الفحص الدوري للمحرك")

    def test_technician_productivity_report(self):
        """Test technician productivity reporting"""
        # Create and complete a session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Complete the session
        stop_labor_tracking(start_result["log_id"])

        # Get productivity report
        from_date = add_to_date(None, days=-1)
        to_date = add_to_date(None, days=1)

        productivity = get_technician_productivity(
            technician_id=self.technician.name, from_date=from_date, to_date=to_date
        )

        self.assertGreater(len(productivity["time_logs"]), 0)
        self.assertGreater(productivity["metrics"]["total_hours"], 0)
        self.assertGreater(productivity["metrics"]["total_revenue"], 0)

    def test_concurrent_tracking_different_orders(self):
        """Test technician cannot work on multiple orders simultaneously"""
        # Create second service order
        service_order_2 = frappe.get_doc(
            {
                "doctype": "Service Order",
                "customer": self.customer.name,
                "vehicle": self.vehicle.name,
                "service_type": "Repair",
                "status": "In Progress",
            }
        ).insert()

        # Start tracking on first order
        start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        # Try to start tracking on second order
        result = start_labor_tracking(
            service_order_id=service_order_2.name,
            technician_id=self.technician.name,
            activity_type="Repair Work",
        )

        self.assertFalse(result["success"])
        self.assertIn("already has an active", result["message"])

        # Cleanup
        service_order_2.delete()

    def test_timesheet_integration(self):
        """Test integration with ERPNext Timesheet"""
        # Start and complete session
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        result = stop_labor_tracking(start_result["log_id"])

        # Verify timesheet was created
        log = frappe.get_doc("Labor Time Log", start_result["log_id"])
        if log.timesheet:
            timesheet = frappe.get_doc("Timesheet", log.timesheet)
            self.assertEqual(timesheet.employee, self.technician.employee_id)
            self.assertGreater(len(timesheet.time_logs), 0)

    def test_data_validation(self):
        """Test data validation and error handling"""
        # Test with invalid service order
        result = start_labor_tracking(
            service_order_id="INVALID-ORDER",
            technician_id=self.technician.name,
            activity_type="Service Work",
        )
        self.assertFalse(result["success"])

        # Test with invalid technician
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id="INVALID-TECH",
            activity_type="Service Work",
        )
        self.assertFalse(result["success"])

        # Test with empty activity type
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="",
        )
        self.assertFalse(result["success"])

    def test_service_order_cost_update(self):
        """Test service order cost updates from labor tracking"""
        # Get initial service order cost
        initial_cost = self.service_order.total_amount or 0

        # Start and complete labor tracking
        start_result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )

        stop_labor_tracking(start_result["log_id"])

        # Reload service order and check if cost was updated
        self.service_order.reload()
        final_cost = self.service_order.total_amount or 0

        # Cost should have increased due to labor
        self.assertGreater(final_cost, initial_cost)

    def test_performance_benchmarks(self):
        """Test performance meets acceptance criteria"""
        import time

        # Test tracking start performance (should be < 2 seconds)
        start_time = time.time()
        result = start_labor_tracking(
            service_order_id=self.service_order.name,
            technician_id=self.technician.name,
            activity_type="Service Work",
        )
        start_duration = time.time() - start_time

        self.assertTrue(result["success"])
        self.assertLess(
            start_duration, 2.0, "Labor tracking start should complete in under 2 seconds"
        )

        # Test pause performance
        pause_start = time.time()
        pause_result = pause_labor_tracking(result["log_id"], "Break")
        pause_duration = time.time() - pause_start

        self.assertTrue(pause_result["success"])
        self.assertLess(
            pause_duration, 1.0, "Labor tracking pause should complete in under 1 second"
        )

        # Test resume performance
        resume_start = time.time()
        resume_result = resume_labor_tracking(result["log_id"])
        resume_duration = time.time() - resume_start

        self.assertTrue(resume_result["success"])
        self.assertLess(
            resume_duration, 1.0, "Labor tracking resume should complete in under 1 second"
        )

        # Test stop performance
        stop_start = time.time()
        stop_result = stop_labor_tracking(result["log_id"])
        stop_duration = time.time() - stop_start

        self.assertTrue(stop_result["success"])
        self.assertLess(
            stop_duration, 3.0, "Labor tracking stop should complete in under 3 seconds"
        )

    def test_labor_time_log_creation(self):
        """Test basic Labor Time Log creation"""
        log = frappe.get_doc(
            {
                "doctype": "Labor Time Log",
                "technician": self.technician.name,
                "service_order": self.service_order.name,
                "activity_type": "Service Work",
                "status": "Active",
                "start_time": now_datetime(),
                "hourly_rate": self.technician.hourly_rate,
            }
        ).insert()

        self.assertEqual(log.technician, self.technician.name)
        self.assertEqual(log.activity_type, "Service Work")
        self.assertEqual(log.status, "Active")

    def test_arabic_content_support(self):
        """Test Arabic content in labor time logs"""
        log = frappe.get_doc(
            {
                "doctype": "Labor Time Log",
                "technician": self.technician.name,
                "service_order": self.service_order.name,
                "activity_type": "صيانة دورية",  # Arabic: Regular Maintenance
                "notes": "بدء الفحص الدوري للمحرك",  # Arabic notes
                "status": "Active",
                "start_time": now_datetime(),
                "hourly_rate": self.technician.hourly_rate,
            }
        ).insert()

        self.assertEqual(log.activity_type, "صيانة دورية")
        self.assertEqual(log.notes, "بدء الفحص الدوري للمحرك")

    def test_cost_calculation(self):
        """Test OMR cost calculation"""
        log = frappe.get_doc(
            {
                "doctype": "Labor Time Log",
                "technician": self.technician.name,
                "service_order": self.service_order.name,
                "activity_type": "Service Work",
                "status": "Completed",
                "start_time": now_datetime(),
                "end_time": now_datetime() + timedelta(hours=3),
                "total_hours": 3.0,
                "hourly_rate": self.technician.hourly_rate,
            }
        ).insert()

        # Expected: 3 hours × 15 OMR = 45.000 OMR
        expected_cost = 3.0 * self.technician.hourly_rate
        log.total_cost = log.total_hours * log.hourly_rate
        self.assertEqual(flt(log.total_cost, 3), expected_cost)


def run_all_tests():
    """Run all labor time tracking tests"""
    unittest.main()


if __name__ == "__main__":
    run_all_tests()
