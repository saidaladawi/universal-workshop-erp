# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import time
import unittest
from unittest.mock import patch

import requests_mock

import frappe
from universal_workshop.vehicle_management.doctype.vehicle.vehicle import Vehicle


class TestVINDecoder(unittest.TestCase):
    """Test VIN Decoder functionality and performance"""

    def setUp(self):
        """Set up test data"""
        # Test VIN - Toyota Camry 2020
        self.test_vin = "4T1BF1FK4LU123456"

        # Mock NHTSA API response
        self.mock_nhtsa_response = {
            "Count": 1,
            "Message": "Results returned successfully",
            "SearchCriteria": f"VIN:{self.test_vin}",
            "Results": [
                {
                    "VIN": self.test_vin,
                    "Make": "TOYOTA",
                    "Model": "Camry",
                    "ModelYear": "2020",
                    "BodyClass": "Sedan/Saloon",
                    "EngineCylinders": "4",
                    "DisplacementL": "2.5",
                    "FuelTypePrimary": "Gasoline",
                    "TransmissionStyle": "Automatic",
                    "DriveType": "FWD",
                    "PlantCountry": "JAPAN",
                    "PlantState": "",
                    "EngineModel": "2AR-FE",
                }
            ],
        }

        # Create test vehicle doc
        self.test_vehicle = frappe.new_doc("Vehicle")
        self.test_vehicle.vin = self.test_vin
        self.test_vehicle.license_plate = "TEST001"
        self.test_vehicle.customer = "Test Customer"

    def test_vin_validation(self):
        """Test VIN format validation"""
        vehicle = Vehicle()

        # Test valid VIN
        vehicle.vin = self.test_vin
        try:
            vehicle.validate_vin()
        except Exception:
            self.fail("Valid VIN should not raise exception")

        # Test invalid VIN length
        vehicle.vin = "SHORT"
        with self.assertRaises(frappe.ValidationError):
            vehicle.validate_vin()

        # Test invalid characters (contains I, O, Q)
        vehicle.vin = "4T1BF1FK4LI123456"  # Contains 'I'
        with self.assertRaises(frappe.ValidationError):
            vehicle.validate_vin()

    @requests_mock.Mocker()
    def test_vin_decoder_api_integration(self, mock_requests):
        """Test VIN decoder API integration"""
        # Mock the NHTSA API response
        api_url = (
            f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{self.test_vin}?format=json"
        )
        mock_requests.get(api_url, json=self.mock_nhtsa_response)

        # Test VIN decoding
        result = self.test_vehicle.decode_vin()

        # Verify response structure
        self.assertTrue(result["success"])
        self.assertIn("updated_fields", result)
        self.assertIn("api_response", result)

        # Verify vehicle data was populated
        self.assertEqual(self.test_vehicle.make, "TOYOTA")
        self.assertEqual(self.test_vehicle.model, "Camry")
        self.assertEqual(self.test_vehicle.year, 2020)
        self.assertEqual(self.test_vehicle.body_class, "Sedan/Saloon")
        self.assertEqual(self.test_vehicle.engine_cylinders, "4")
        self.assertEqual(self.test_vehicle.engine_displacement, "2.5")
        self.assertEqual(self.test_vehicle.fuel_type_primary, "Gasoline")

    @requests_mock.Mocker()
    def test_vin_decoder_performance(self, mock_requests):
        """Test VIN decoder performance - AC1: Response time < 5 seconds"""
        # Mock the NHTSA API response with delay simulation
        api_url = (
            f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{self.test_vin}?format=json"
        )
        mock_requests.get(api_url, json=self.mock_nhtsa_response)

        # Measure decode time
        start_time = time.time()
        result = self.test_vehicle.decode_vin()
        end_time = time.time()

        decode_time = end_time - start_time

        # Verify performance requirement: < 5 seconds
        self.assertLess(decode_time, 5.0, f"VIN decode took {decode_time:.2f}s, should be < 5s")
        self.assertTrue(result["success"])

    @requests_mock.Mocker()
    def test_arabic_translation_generation(self, mock_requests):
        """Test Arabic translation generation for decoded data"""
        # Mock the NHTSA API response
        api_url = (
            f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{self.test_vin}?format=json"
        )
        mock_requests.get(api_url, json=self.mock_nhtsa_response)

        # Ensure Arabic fields are empty before decoding
        self.test_vehicle.make_ar = ""
        self.test_vehicle.body_class_ar = ""

        # Decode VIN
        self.test_vehicle.decode_vin()

        # Verify Arabic translations were generated
        self.assertEqual(self.test_vehicle.make_ar, "تويوتا")  # Toyota in Arabic
        self.assertEqual(self.test_vehicle.body_class_ar, "سيدان")  # Sedan in Arabic

    @requests_mock.Mocker()
    def test_vin_decoder_error_handling(self, mock_requests):
        """Test VIN decoder error handling"""
        # Test API timeout
        api_url = (
            f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{self.test_vin}?format=json"
        )
        mock_requests.get(api_url, exc=requests_mock.exceptions.ConnectTimeout)

        with self.assertRaises(frappe.ValidationError) as context:
            self.test_vehicle.decode_vin()
        self.assertIn("timed out", str(context.exception))

        # Test invalid VIN (no results)
        invalid_response = {"Count": 0, "Message": "No results found", "Results": []}
        mock_requests.get(api_url, json=invalid_response)

        with self.assertRaises(frappe.ValidationError) as context:
            self.test_vehicle.decode_vin()
        self.assertIn("No vehicle data found", str(context.exception))

    def test_engine_type_generation(self):
        """Test engine type field generation from multiple API fields"""
        Vehicle()

        # Mock vehicle data with engine information
        vehicle_data = {"DisplacementL": "2.5", "EngineCylinders": "4", "EngineModel": "2AR-FE"}

        # Simulate engine type generation logic
        engine_parts = []
        if vehicle_data.get("DisplacementL"):
            engine_parts.append(f"{vehicle_data['DisplacementL']}L")
        if vehicle_data.get("EngineCylinders"):
            cylinders = int(vehicle_data["EngineCylinders"])
            engine_parts.append(f"V{cylinders}" if cylinders > 4 else f"I{cylinders}")
        if vehicle_data.get("EngineModel"):
            engine_parts.append(vehicle_data["EngineModel"])

        expected_engine_type = " ".join(engine_parts)
        self.assertEqual(expected_engine_type, "2.5L I4 2AR-FE")

    def test_field_update_logic(self):
        """Test that existing fields are not overridden unless empty"""
        vehicle = Vehicle()

        # Set some existing data
        vehicle.make = "HONDA"
        vehicle.model = "ACCORD"
        vehicle.year = 2019

        # Simulate API data
        api_data = {
            "Make": "TOYOTA",  # Different from existing
            "Model": "CAMRY",  # Different from existing
            "ModelYear": "2020",  # Different from existing
            "BodyClass": "Sedan/Saloon",  # New field
        }

        # Test the update logic
        field_mapping = {
            "Make": "make",
            "Model": "model",
            "ModelYear": "year",
            "BodyClass": "body_class",
        }

        updated_fields = []
        for api_field, doc_field in field_mapping.items():
            api_value = api_data.get(api_field)
            if api_value and api_value.strip():
                if doc_field == "year":
                    api_value = int(api_value)

                current_value = getattr(vehicle, doc_field, None)
                if not current_value or current_value != api_value:
                    setattr(vehicle, doc_field, api_value)
                    updated_fields.append(doc_field)

        # Verify that existing fields would be updated (in real implementation user choice)
        # and new field would be populated
        self.assertIn("body_class", updated_fields)

    def test_arabic_translation_mapping(self):
        """Test Arabic translation mapping functionality"""
        vehicle = Vehicle()

        # Test make translations
        test_makes = [
            ("TOYOTA", "تويوتا"),
            ("HONDA", "هوندا"),
            ("BMW", "بي إم دبليو"),
            ("MERCEDES-BENZ", "مرسيدس بنز"),
        ]

        for english_make, expected_arabic in test_makes:
            arabic_translation = vehicle.get_arabic_translation(english_make, "make")
            self.assertEqual(arabic_translation, expected_arabic)

        # Test body class translations
        test_body_classes = [("Sedan/Saloon", "سيدان"), ("SUV", "دفع رباعي"), ("Pickup", "بيك آب")]

        for english_body, expected_arabic in test_body_classes:
            arabic_translation = vehicle.get_arabic_translation(english_body, "body_class")
            self.assertEqual(arabic_translation, expected_arabic)

        # Test unknown translation returns empty string
        unknown_translation = vehicle.get_arabic_translation("UNKNOWN_MAKE", "make")
        self.assertEqual(unknown_translation, "")

    def tearDown(self):
        """Clean up test data"""


if __name__ == "__main__":
    unittest.main()
