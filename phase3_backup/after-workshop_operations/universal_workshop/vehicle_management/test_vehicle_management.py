#!/usr/bin/env python3
"""
Comprehensive Test Suite for Vehicle Management Module
Tests all core functionality including VIN decoding, service tracking, maintenance alerts
"""

import datetime
import unittest
from unittest.mock import Mock, patch
import contextlib

import frappe
from frappe.test_runner import make_test_records


class TestVehicleManagement(unittest.TestCase):
    """Test suite for Vehicle Management functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test data for all tests"""
        # Create test customer
        if not frappe.db.exists("Customer", "TEST-CUSTOMER-001"):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Ahmed Al-Rashid"
            customer.customer_name_ar = "أحمد الراشد"
            customer.customer_type = "Individual"
            customer.territory = "Oman"
            customer.insert(ignore_permissions=True)
            cls.test_customer = customer.name
        else:
            cls.test_customer = "TEST-CUSTOMER-001"

    def setUp(self):
        """Set up for each test"""
        self.test_vin = "1HGCM82633A123456"  # Valid Honda VIN format
        self.test_license_plate = "12345 A"

    def tearDown(self):
        """Clean up after each test"""
        # Clean up test vehicles
        test_vehicles = frappe.get_all("Vehicle", {"vin": self.test_vin})
        for vehicle in test_vehicles:
            frappe.delete_doc("Vehicle", vehicle.name, force=True)

    def test_vehicle_creation_basic(self):
        """Test basic vehicle creation with required fields"""
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022
        vehicle.customer = self.test_customer

        # Should save without errors
        vehicle.insert()
        self.assertTrue(vehicle.name)
        self.assertEqual(vehicle.vin, self.test_vin)

    def test_vin_validation(self):
        """Test VIN validation rules"""
        vehicle = frappe.new_doc("Vehicle")
        vehicle.customer = self.test_customer
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022

        # Test invalid VIN length
        vehicle.vin = "TOOLONG123456789012345"
        with self.assertRaises(frappe.ValidationError):
            vehicle.insert()

        # Test VIN with invalid characters (I, O, Q)
        vehicle.vin = "1HGCM82633A12345I"
        with self.assertRaises(frappe.ValidationError):
            vehicle.insert()

        # Test valid VIN
        vehicle.vin = self.test_vin
        vehicle.insert()  # Should not raise exception
        self.assertTrue(vehicle.name)

    def test_arabic_field_support(self):
        """Test Arabic field support and translations"""
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.license_plate_ar = "١٢٣٤٥ أ"
        vehicle.make = "Toyota"
        vehicle.make_ar = "تويوتا"
        vehicle.model = "Camry"
        vehicle.model_ar = "كامري"
        vehicle.year = 2023
        vehicle.customer = self.test_customer

        vehicle.insert()

        # Verify Arabic fields are preserved
        saved_vehicle = frappe.get_doc("Vehicle", vehicle.name)
        self.assertEqual(saved_vehicle.make_ar, "تويوتا")
        self.assertEqual(saved_vehicle.model_ar, "كامري")
        self.assertEqual(saved_vehicle.license_plate_ar, "١٢٣٤٥ أ")

    @patch("requests.get")
    def test_vin_decoder_api_integration(self, mock_get):
        """Test VIN decoder API integration with mock response"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "Count": 1,
            "Results": [
                {
                    "Make": "HONDA",
                    "Model": "Civic",
                    "ModelYear": "2023",
                    "BodyClass": "Sedan",
                    "EngineCylinders": "4",
                    "DisplacementL": "2.0",
                    "FuelTypePrimary": "Gasoline",
                    "TransmissionStyle": "Manual",
                    "DriveType": "FWD",
                }
            ],
        }
        mock_get.return_value = mock_response

        # Create vehicle and test VIN decoding
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Call decode_vin method
        vehicle.decode_vin()

        # Verify fields were populated
        self.assertEqual(vehicle.make, "HONDA")
        self.assertEqual(vehicle.model, "Civic")
        self.assertEqual(vehicle.year, 2023)
        self.assertEqual(vehicle.body_class, "Sedan")

    @patch("requests.get")
    def test_vin_decoder_api_timeout(self, mock_get):
        """Test VIN decoder API timeout handling"""
        # Mock timeout exception
        mock_get.side_effect = Exception("Timeout")

        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Should handle timeout gracefully
        with self.assertRaises(Exception):
            vehicle.decode_vin()

    def test_service_record_creation(self):
        """Test service record creation and calculations"""
        # Create vehicle first
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022
        vehicle.customer = self.test_customer
        vehicle.current_mileage = 15000
        vehicle.insert()

        # Create service record
        service_record = frappe.new_doc("Service Record")
        service_record.vehicle = vehicle.name
        service_record.service_date = datetime.date.today()
        service_record.service_type = "Oil Change"
        service_record.mileage_at_service = 15500
        service_record.labor_hours = 1.0
        service_record.labor_cost = 50.0
        service_record.status = "Completed"

        # Add parts
        parts_row = service_record.append("parts_used")
        parts_row.part_name = "Engine Oil"
        parts_row.part_number = "EO-5W30"
        parts_row.quantity = 4
        parts_row.unit_cost = 15.0

        service_record.insert()

        # Verify calculations
        self.assertEqual(service_record.parts_total_cost, 60.0)  # 4 * 15.0
        self.assertEqual(service_record.total_cost, 110.0)  # 50.0 + 60.0

    def test_maintenance_alert_creation(self):
        """Test maintenance alert creation and priority calculation"""
        # Create vehicle
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022
        vehicle.customer = self.test_customer
        vehicle.current_mileage = 25000
        vehicle.insert()

        # Create maintenance alert
        alert = frappe.new_doc("Maintenance Alert")
        alert.vehicle = vehicle.name
        alert.service_type = "Oil Change"
        alert.due_date = datetime.date.today() - datetime.timedelta(days=10)  # Overdue
        alert.service_due_mileage = 20000
        alert.current_mileage = 25000
        alert.alert_type = "Combined"
        alert.insert()

        # Verify priority calculation (should be high due to overdue)
        self.assertIn(alert.priority, ["High", "Critical"])
        self.assertEqual(alert.overdue_days, 10)
        self.assertEqual(alert.mileage_overdue, 5000)

    def test_vehicle_inspection_creation(self):
        """Test vehicle inspection with checklist items"""
        # Create vehicle
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Create inspection
        inspection = frappe.new_doc("Vehicle Inspection")
        inspection.vehicle = vehicle.name
        inspection.inspector = frappe.session.user
        inspection.inspection_type = "Periodic Maintenance"
        inspection.inspection_date = datetime.date.today()

        # Add checklist items
        item1 = inspection.append("checklist_items")
        item1.inspection_item = "Engine Oil Level"
        item1.result = "Pass"
        item1.priority = "High"

        item2 = inspection.append("checklist_items")
        item2.inspection_item = "Brake Pads"
        item2.result = "Fail"
        item2.priority = "Critical"

        inspection.insert()

        # Verify rating calculation
        self.assertEqual(inspection.overall_rating, "Critical")  # Due to critical failure
        self.assertTrue(inspection.immediate_action_required)

    def test_api_vehicle_search_security(self):
        """Test vehicle search API security against SQL injection"""
        from universal_workshop.vehicle_management.api import search_vehicles

        # Test with potential SQL injection
        malicious_query = "'; DROP TABLE tabVehicle; --"

        # Should handle safely without SQL injection
        try:
            results = search_vehicles(malicious_query)
            # Should return empty results, not cause SQL error
            self.assertIsInstance(results, list)
        except Exception as e:
            # Should not be a SQL-related error
            self.assertNotIn("SQL", str(e).upper())

    def test_vehicle_api_functions(self):
        """Test vehicle management API functions"""
        from universal_workshop.vehicle_management.api import get_vehicles_by_customer, validate_vin

        # Test VIN validation API
        result = validate_vin(self.test_vin)
        self.assertTrue(result["valid"])
        self.assertEqual(result["formatted_vin"], self.test_vin)

        # Test invalid VIN
        result = validate_vin("INVALID")
        self.assertFalse(result["valid"])

        # Create test vehicle for customer API test
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "Honda"
        vehicle.model = "Civic"
        vehicle.year = 2022
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Test get vehicles by customer
        vehicles = get_vehicles_by_customer(self.test_customer)
        self.assertGreater(len(vehicles), 0)
        self.assertEqual(vehicles[0]["make"], "Honda")

    def test_arabic_translation_system(self):
        """Test Arabic translation functionality"""
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.make = "BMW"
        vehicle.model = "X5"
        vehicle.year = 2023
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Test Arabic translation for common makes
        arabic_make = vehicle.get_arabic_translation("BMW", "make")
        self.assertEqual(arabic_make, "بي إم دبليو")

        arabic_make = vehicle.get_arabic_translation("Toyota", "make")
        self.assertEqual(arabic_make, "تويوتا")

    def test_performance_vin_decode_timing(self):
        """Test VIN decoder performance within 5-second requirement"""
        import time

        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = self.test_license_plate
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Mock the API call to test timeout behavior
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"Count": 0, "Results": []}
            mock_get.return_value = mock_response

            # Test VIN decode timing
            start_time = time.time()
            with contextlib.suppress(Exception):
                vehicle.decode_vin()  # Error is expected for empty results
            end_time = time.time()

            # Should complete within reasonable time (much less than 10s timeout)
            self.assertLess(end_time - start_time, 2.0)


class TestMaintenanceAlerts(unittest.TestCase):
    """Specific tests for maintenance alert functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_customer = "TEST-CUSTOMER-001"
        self.test_vin = "1HGCM82633A654321"

    def test_alert_priority_calculation(self):
        """Test maintenance alert priority calculation logic"""
        alert = frappe.new_doc("Maintenance Alert")

        # Test critical priority (overdue + high mileage)
        alert.overdue_days = 45
        alert.mileage_overdue = 8000
        alert.due_date = datetime.date.today() - datetime.timedelta(days=45)
        alert.set_priority_based_on_urgency()
        self.assertEqual(alert.priority, "Critical")

        # Test medium priority
        alert.overdue_days = 5
        alert.mileage_overdue = 500
        alert.due_date = datetime.date.today() - datetime.timedelta(days=5)
        alert.set_priority_based_on_urgency()
        self.assertEqual(alert.priority, "Medium")

    def test_arabic_alert_messages(self):
        """Test Arabic alert message generation"""
        # Create test vehicle
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = self.test_vin
        vehicle.license_plate = "67890 B"
        vehicle.make = "Toyota"
        vehicle.model = "Corolla"
        vehicle.year = 2021
        vehicle.customer = self.test_customer
        vehicle.insert()

        # Create alert
        alert = frappe.new_doc("Maintenance Alert")
        alert.vehicle = vehicle.name
        alert.service_type = "Oil Change"
        alert.service_type_ar = "تغيير الزيت"
        alert.due_date = datetime.date.today()
        alert.priority = "High"
        alert.insert()

        # Test Arabic message generation
        arabic_message = alert.get_arabic_message()
        self.assertIn("تغيير الزيت", arabic_message)
        self.assertIn("Toyota Corolla", arabic_message)
        self.assertIn("عالية", arabic_message)  # "High" in Arabic


if __name__ == "__main__":
    # Run tests
    unittest.main()
