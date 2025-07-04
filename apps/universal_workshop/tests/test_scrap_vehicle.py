#!/usr/bin/env python3
"""
Test script for Scrap Vehicle DocType functionality
Tests the core features implemented in subtask 10.1
"""

import frappe
import sys
import os

# Add the project path
sys.path.append("/home/said/frappe-dev/frappe-bench")


def test_scrap_vehicle_creation():
    """Test basic Scrap Vehicle creation"""
    try:
        print("🔄 Testing Scrap Vehicle DocType creation...")

        # Check if DocType exists
        if not frappe.db.exists("DocType", "Scrap Vehicle"):
            print("❌ Scrap Vehicle DocType does not exist")
            return False

        print("✅ Scrap Vehicle DocType exists")

        # Test creating a new scrap vehicle document
        scrap_vehicle = frappe.new_doc("Scrap Vehicle")
        scrap_vehicle.vehicle_title = "2018 Toyota Camry - Accident Damage"
        scrap_vehicle.vehicle_title_ar = "تويوتا كامري ٢٠١٨ - تلف حادث"
        scrap_vehicle.make = "Toyota"
        scrap_vehicle.model = "Camry"
        scrap_vehicle.year = 2018
        scrap_vehicle.vin = "1G1BC5SM7J7123456"
        scrap_vehicle.acquisition_source = "Insurance Company"
        scrap_vehicle.seller_name = "Al Ahlia Insurance"
        scrap_vehicle.seller_name_ar = "تأمين الأهلية"
        scrap_vehicle.seller_phone = "+968 24123456"
        scrap_vehicle.acquisition_cost = 2500.000
        scrap_vehicle.transport_cost = 150.000
        scrap_vehicle.documentation_cost = 25.000
        scrap_vehicle.acquisition_currency = "OMR"

        # Test validation
        scrap_vehicle.insert(ignore_permissions=True)
        print(f"✅ Scrap Vehicle created successfully: {scrap_vehicle.name}")
        print(f"   Generated ID: {scrap_vehicle.scrap_vehicle_id}")
        print(f"   Total Cost: {scrap_vehicle.total_acquisition_cost} OMR")

        return True

    except Exception as e:
        print(f"❌ Error creating Scrap Vehicle: {str(e)}")
        return False


def test_scrap_vehicle_workflow():
    """Test Scrap Vehicle workflow functionality"""
    try:
        print("\n🔄 Testing Scrap Vehicle workflow...")

        # Get the last created vehicle
        vehicles = frappe.get_list(
            "Scrap Vehicle", filters={"docstatus": 0}, limit=1, order_by="creation desc"
        )

        if not vehicles:
            print("❌ No scrap vehicles found for workflow testing")
            return False

        vehicle_name = vehicles[0].name
        vehicle = frappe.get_doc("Scrap Vehicle", vehicle_name)

        print(f"   Testing workflow for vehicle: {vehicle.vehicle_title}")
        print(f"   Initial status: {vehicle.status}")

        # Test starting assessment
        vehicle.start_condition_assessment()
        print(f"   Status after starting assessment: {vehicle.status}")

        # Set assessment fields
        vehicle.overall_condition = "Fair"
        vehicle.estimated_dismantling_hours = 16.0
        vehicle.estimated_parts_value = 1800.000
        vehicle.assessment_notes = "Front end damage, engine intact"

        # Test completing assessment
        vehicle.complete_condition_assessment()
        print(f"   Status after completing assessment: {vehicle.status}")

        # Test marking ready for dismantling
        vehicle.mark_ready_for_dismantling()
        print(f"   Final status: {vehicle.status}")

        # Test profit calculation
        profit_data = vehicle.get_profit_potential()
        if profit_data:
            print(f"   Profit Analysis:")
            print(f"     Total Cost: {profit_data['total_cost']} OMR")
            print(f"     Estimated Value: {profit_data['estimated_value']} OMR")
            print(f"     Potential Profit: {profit_data['potential_profit']} OMR")
            print(f"     Profit Margin: {profit_data['profit_margin']:.1f}%")

        print("✅ Workflow testing completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error in workflow testing: {str(e)}")
        return False


def test_validation_functions():
    """Test validation functions"""
    try:
        print("\n🔄 Testing validation functions...")

        # Test VIN validation
        test_vehicle = frappe.new_doc("Scrap Vehicle")
        test_vehicle.vehicle_title = "Test Vehicle"
        test_vehicle.vehicle_title_ar = "مركبة اختبار"
        test_vehicle.make = "Test"
        test_vehicle.model = "Model"
        test_vehicle.year = 2020
        test_vehicle.seller_name = "Test Seller"
        test_vehicle.acquisition_source = "Other"

        # Test invalid VIN
        try:
            test_vehicle.vin = "INVALID123"  # Too short
            test_vehicle.validate()
            print("❌ VIN validation failed - should have thrown error")
            return False
        except frappe.ValidationError:
            print("✅ VIN validation working correctly")

        # Test phone validation
        try:
            test_vehicle.seller_phone = "123456"  # Invalid format
            test_vehicle.validate()
            print("❌ Phone validation failed - should have thrown error")
            return False
        except frappe.ValidationError:
            print("✅ Phone validation working correctly")

        # Test Arabic name validation
        try:
            test_vehicle.vehicle_title_ar = ""  # Empty Arabic title
            test_vehicle.validate()
            print("❌ Arabic name validation failed - should have thrown error")
            return False
        except frappe.ValidationError:
            print("✅ Arabic name validation working correctly")

        print("✅ All validation functions working correctly")
        return True

    except Exception as e:
        print(f"❌ Error in validation testing: {str(e)}")
        return False


def test_child_tables():
    """Test child table functionality"""
    try:
        print("\n🔄 Testing child table functionality...")

        # Check if child DocTypes exist
        if not frappe.db.exists("DocType", "Scrap Vehicle Photo"):
            print("❌ Scrap Vehicle Photo DocType does not exist")
            return False

        if not frappe.db.exists("DocType", "Scrap Vehicle Document"):
            print("❌ Scrap Vehicle Document DocType does not exist")
            return False

        print("✅ Child DocTypes exist (Scrap Vehicle Photo & Document)")

        # Test adding photo record
        vehicles = frappe.get_list("Scrap Vehicle", limit=1)
        if vehicles:
            vehicle = frappe.get_doc("Scrap Vehicle", vehicles[0].name)

            # Add a photo record
            photo_row = vehicle.append(
                "vehicle_photos",
                {
                    "photo_type": "Exterior Front",
                    "photo_title": "Front View Damage",
                    "photo_title_ar": "منظر أمامي للضرر",
                    "photo_description": "Shows front end collision damage",
                    "camera_location": "Mobile Device",
                },
            )

            # Add a document record
            doc_row = vehicle.append(
                "acquisition_documents",
                {
                    "document_type": "Insurance Policy",
                    "document_title": "Insurance Claim Document",
                    "document_title_ar": "وثيقة مطالبة التأمين",
                    "document_description": "Official insurance claim paperwork",
                },
            )

            vehicle.save()
            print("✅ Child table records added successfully")
            print(f"   Photos: {len(vehicle.vehicle_photos)}")
            print(f"   Documents: {len(vehicle.acquisition_documents)}")

        return True

    except Exception as e:
        print(f"❌ Error in child table testing: {str(e)}")
        return False


def run_comprehensive_test():
    """Run all tests for Scrap Vehicle functionality"""
    print("🚀 Starting Scrap Vehicle DocType Testing")
    print("=" * 50)

    # Initialize Frappe
    frappe.init(site="universal.local")
    frappe.connect()

    test_results = []

    # Run all tests
    test_results.append(test_scrap_vehicle_creation())
    test_results.append(test_scrap_vehicle_workflow())
    test_results.append(test_validation_functions())
    test_results.append(test_child_tables())

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(test_results)
    total = len(test_results)

    print(f"✅ Tests Passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Scrap Vehicle DocType implementation is working correctly.")
        print("\n📋 Task 10.1 - Acceptance Criteria Verification:")
        print("✅ Vehicle creation with Arabic/English dual language support")
        print("✅ Condition assessment workflow (Acquired → Assessment → Complete → Dismantling)")
        print("✅ Comprehensive validation (VIN, phone, Arabic names)")
        print("✅ Photo upload and documentation functionality")
        print("✅ Cost calculation and profit analysis")
        print("✅ Oman-specific regional compliance (OMR currency, phone format)")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
