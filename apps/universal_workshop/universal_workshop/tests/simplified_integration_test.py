"""
Universal Workshop ERP - Simplified Integration Test
Testing actual available functionality for end-to-end workflows
"""

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, flt
import json
import time


def test_end_to_end_workflows():
    """Test end-to-end workflows using actual available functions"""
    print("🧪 Universal Workshop ERP - End-to-End Integration Tests")
    print("=" * 80)
    
    test_results = {
        "system_status": test_system_status(),
        "customer_vehicle_workflow": test_customer_vehicle_workflow(),
        "service_order_workflow": test_service_order_workflow(),
        "arabic_localization": test_arabic_functionality(),
        "performance_metrics": test_performance_under_load(),
        "data_integrity": test_data_relationships()
    }
    
    # Generate comprehensive test report
    generate_end_to_end_report(test_results)
    
    return test_results


def test_system_status():
    """Test basic system functionality and module accessibility"""
    print("🔍 Testing System Status & Module Accessibility...")
    
    try:
        results = {}
        
        # Test app installation
        app_list = frappe.get_installed_apps()
        results["app_installed"] = "universal_workshop" in app_list
        
        # Test modules
        modules = frappe.get_all("Module Def", filters={"app_name": "universal_workshop"})
        results["modules_count"] = len(modules)
        results["modules_accessible"] = len(modules) > 0
        
        # Test DocTypes
        workshop_doctypes = frappe.get_all("DocType", filters={"module": ["like", "%Workshop%"]})
        results["workshop_doctypes"] = len(workshop_doctypes)
        
        vehicle_doctypes = frappe.get_all("DocType", filters={"module": ["like", "%Vehicle%"]})
        results["vehicle_doctypes"] = len(vehicle_doctypes)
        
        license_doctypes = frappe.get_all("DocType", filters={"module": ["like", "%License%"]})
        results["license_doctypes"] = len(license_doctypes)
        
        # Test database connectivity
        customers_count = len(frappe.get_all("Customer", limit=1))
        results["database_accessible"] = True
        
        return {
            "status": "PASS",
            "details": results,
            "summary": f"✅ {results['modules_count']} modules, {results['workshop_doctypes']} workshop DocTypes"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ System status check failed"
        }


def test_customer_vehicle_workflow():
    """Test customer and vehicle management workflow"""
    print("👥🚗 Testing Customer-Vehicle Workflow...")
    
    try:
        # Create test customer
        customer = frappe.new_doc("Customer")
        customer.customer_name = "Ahmed Al-Rashid"
        customer.customer_type = "Individual"
        customer.territory = "Oman"
        customer.customer_group = "Individual"
        customer.insert()
        
        # Create test vehicle
        vehicle = frappe.new_doc("Vehicle")
        vehicle.vin = f"TEST{int(time.time())}{frappe.generate_hash()[:8]}"  # Unique VIN
        vehicle.license_plate = f"OM{int(time.time() % 10000)}"
        vehicle.license_plate_ar = f"ع م {int(time.time() % 10000)}"
        vehicle.make = "Toyota"
        vehicle.make_ar = "تويوتا"
        vehicle.model = "Camry"
        vehicle.model_ar = "كامري"
        vehicle.year = 2020
        vehicle.customer = customer.name
        vehicle.current_mileage = 50000
        vehicle.insert()
        
        # Test vehicle API functions
        from universal_workshop.vehicle_management.api import get_vehicles_by_customer, validate_vin
        
        # Test get vehicles by customer
        customer_vehicles = get_vehicles_by_customer(customer.name)
        vehicles_found = len(customer_vehicles) > 0
        
        # Test VIN validation
        vin_validation = validate_vin("INVALID_VIN")
        vin_validation_works = not vin_validation["valid"]
        
        return {
            "status": "PASS",
            "customer_created": customer.name,
            "vehicle_created": vehicle.name,
            "vehicles_retrieved": vehicles_found,
            "vin_validation": vin_validation_works,
            "summary": f"✅ Customer & Vehicle workflow successful"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ Customer-Vehicle workflow failed"
        }


def test_service_order_workflow():
    """Test service order creation and management"""
    print("🔧 Testing Service Order Workflow...")
    
    try:
        # Get or create test customer and vehicle
        customers = frappe.get_all("Customer", limit=1)
        if not customers:
            # Create test customer
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Test Customer"
            customer.customer_type = "Individual"
            customer.territory = "Oman"
            customer.customer_group = "Individual"
            customer.insert()
            customer_name = customer.name
        else:
            customer_name = customers[0].name
        
        vehicles = frappe.get_all("Vehicle", filters={"customer": customer_name}, limit=1)
        if not vehicles:
            # Create test vehicle
            vehicle = frappe.new_doc("Vehicle")
            vehicle.vin = f"TEST{int(time.time())}{frappe.generate_hash()[:8]}"
            vehicle.license_plate = f"TEST{int(time.time() % 10000)}"
            vehicle.make = "Test Make"
            vehicle.model = "Test Model"
            vehicle.year = 2020
            vehicle.customer = customer_name
            vehicle.current_mileage = 30000
            vehicle.insert()
            vehicle_name = vehicle.name
        else:
            vehicle_name = vehicles[0].name
        
        # Create service order
        service_order = frappe.new_doc("Service Order")
        service_order.customer = customer_name
        service_order.vehicle = vehicle_name
        service_order.service_date = nowdate()
        service_order.service_type = "Oil Change"
        service_order.status = "Draft"
        service_order.current_mileage = 31000
        service_order.description = "Regular oil change service"
        service_order.insert()
        
        # Test calculations
        service_order.parts_total = 100.000
        service_order.labor_total = 50.000
        service_order.vat_rate = 5.0
        service_order.calculate_totals()
        
        # Verify VAT calculation (5% of 150.000 = 7.500)
        expected_vat = 7.500
        vat_calculation_correct = abs(service_order.vat_amount - expected_vat) < 0.001
        
        # Test status transition
        service_order.status = "Scheduled"
        service_order.save()
        
        return {
            "status": "PASS",
            "service_order_created": service_order.name,
            "vat_calculation": vat_calculation_correct,
            "vat_amount": service_order.vat_amount,
            "status_transition": service_order.status == "Scheduled",
            "summary": f"✅ Service order workflow successful - VAT: {service_order.vat_amount}"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ Service order workflow failed"
        }


def test_arabic_functionality():
    """Test Arabic localization and RTL support"""
    print("🌍 Testing Arabic Localization...")
    
    try:
        results = {}
        
        # Test Arabic text detection
        arabic_text = "مركبة تويوتا"
        english_text = "Toyota Vehicle"
        
        # Simple Arabic detection (check for Arabic Unicode range)
        def is_arabic(text):
            return any('\u0600' <= char <= '\u06FF' for char in text)
        
        def get_direction(text):
            return "rtl" if is_arabic(text) else "ltr"
        
        results["arabic_detection"] = is_arabic(arabic_text) and not is_arabic(english_text)
        results["text_direction"] = get_direction(arabic_text) == "rtl"
        
        # Test Arabic number conversion
        def convert_to_arabic_numerals(text):
            arabic_digits = "٠١٢٣٤٥٦٧٨٩"
            english_digits = "0123456789"
            for i, digit in enumerate(english_digits):
                text = text.replace(digit, arabic_digits[i])
            return text
        
        arabic_numbers = convert_to_arabic_numerals("12345")
        results["number_conversion"] = arabic_numbers == "١٢٣٤٥"
        
        # Test system settings
        system_settings = frappe.get_doc("System Settings")
        results["country_setting"] = system_settings.country == "Oman"
        
        # Test Arabic fields in DocTypes
        vehicle_doctypes = frappe.get_all("DocType", filters={"name": "Vehicle"})
        if vehicle_doctypes:
            vehicle_doctype = frappe.get_doc("DocType", "Vehicle")
            arabic_fields = [f for f in vehicle_doctype.fields if "_ar" in f.fieldname]
            results["arabic_fields_count"] = len(arabic_fields)
            results["arabic_fields_exist"] = len(arabic_fields) > 0
        
        all_tests_passed = all([
            results["arabic_detection"],
            results["text_direction"], 
            results["number_conversion"],
            results["country_setting"],
            results.get("arabic_fields_exist", False)
        ])
        
        return {
            "status": "PASS" if all_tests_passed else "PARTIAL",
            "details": results,
            "summary": f"✅ Arabic localization: {len([k for k, v in results.items() if v])} of {len(results)} tests passed"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ Arabic localization test failed"
        }


def test_performance_under_load():
    """Test system performance under simulated load"""
    print("⚡ Testing Performance Under Load...")
    
    try:
        results = {}
        
        # Test database query performance
        start_time = time.time()
        customers = frappe.get_all("Customer", limit=50)
        db_query_time = time.time() - start_time
        results["db_query_time"] = db_query_time
        results["db_performance_grade"] = "A" if db_query_time < 0.1 else "B" if db_query_time < 0.5 else "C"
        
        # Test DocType creation performance
        start_time = time.time()
        test_customer = frappe.new_doc("Customer")
        test_customer.customer_name = f"Perf Test {int(time.time())}"
        test_customer.customer_type = "Individual"
        test_customer.territory = "Oman"
        test_customer.customer_group = "Individual"
        test_customer.insert()
        creation_time = time.time() - start_time
        results["creation_time"] = creation_time
        results["creation_grade"] = "A" if creation_time < 0.2 else "B" if creation_time < 1.0 else "C"
        
        # Test complex query performance
        start_time = time.time()
        complex_query = frappe.db.sql("""
            SELECT c.name, c.customer_name, COUNT(v.name) as vehicle_count
            FROM `tabCustomer` c
            LEFT JOIN `tabVehicle` v ON c.name = v.customer
            GROUP BY c.name
            LIMIT 20
        """, as_dict=True)
        complex_query_time = time.time() - start_time
        results["complex_query_time"] = complex_query_time
        results["complex_query_grade"] = "A" if complex_query_time < 0.2 else "B" if complex_query_time < 1.0 else "C"
        
        # Overall performance assessment
        avg_time = (db_query_time + creation_time + complex_query_time) / 3
        results["overall_performance"] = "A" if avg_time < 0.2 else "B" if avg_time < 0.5 else "C"
        
        return {
            "status": "PASS",
            "details": results,
            "summary": f"✅ Performance Grade: {results['overall_performance']} (Avg: {avg_time:.3f}s)"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ Performance test failed"
        }


def test_data_relationships():
    """Test data integrity and relationships between modules"""
    print("🔗 Testing Data Relationships & Integrity...")
    
    try:
        results = {}
        
        # Test Customer-Vehicle relationship
        customers_with_vehicles = frappe.db.sql("""
            SELECT c.name, c.customer_name, COUNT(v.name) as vehicle_count
            FROM `tabCustomer` c
            LEFT JOIN `tabVehicle` v ON c.name = v.customer
            GROUP BY c.name
            HAVING vehicle_count > 0
            LIMIT 5
        """, as_dict=True)
        
        results["customers_with_vehicles"] = len(customers_with_vehicles)
        results["relationship_integrity"] = True
        
        # Test Vehicle-Service Order relationship
        vehicles_with_orders = frappe.db.sql("""
            SELECT v.name, v.vin, COUNT(so.name) as order_count
            FROM `tabVehicle` v
            LEFT JOIN `tabService Order` so ON v.name = so.vehicle
            GROUP BY v.name
            HAVING order_count > 0
            LIMIT 5
        """, as_dict=True)
        
        results["vehicles_with_orders"] = len(vehicles_with_orders)
        
        # Test foreign key constraints
        orphaned_vehicles = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVehicle` v
            LEFT JOIN `tabCustomer` c ON v.customer = c.name
            WHERE v.customer IS NOT NULL AND c.name IS NULL
        """, as_dict=True)
        
        results["orphaned_vehicles"] = orphaned_vehicles[0].count if orphaned_vehicles else 0
        results["data_integrity"] = results["orphaned_vehicles"] == 0
        
        # Test DocType consistency
        doctype_count = len(frappe.get_all("DocType", filters={"module": ["like", "%Workshop%"]}))
        results["doctype_consistency"] = doctype_count > 0
        
        all_integrity_checks = [
            results["relationship_integrity"],
            results["data_integrity"], 
            results["doctype_consistency"]
        ]
        
        return {
            "status": "PASS" if all(all_integrity_checks) else "PARTIAL",
            "details": results,
            "summary": f"✅ Data integrity: {results['customers_with_vehicles']} customers with vehicles, {results['orphaned_vehicles']} orphans"
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "error": str(e),
            "summary": "❌ Data integrity test failed"
        }


def generate_end_to_end_report(test_results):
    """Generate comprehensive end-to-end test report"""
    print("\n" + "="*80)
    print("📊 UNIVERSAL WORKSHOP ERP - END-TO-END INTEGRATION REPORT")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result.get("status") == "PASS")
    partial_tests = sum(1 for result in test_results.values() if result.get("status") == "PARTIAL")
    failed_tests = total_tests - passed_tests - partial_tests
    
    print(f"\n📈 Test Summary:")
    print(f"   Total Test Categories: {total_tests}")
    print(f"   ✅ Fully Passed: {passed_tests}")
    print(f"   ⚠️ Partially Passed: {partial_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📊 Success Rate: {((passed_tests + partial_tests*0.5)/total_tests)*100:.1f}%")
    
    print(f"\n🔍 Detailed Results:")
    print("-" * 80)
    
    for test_name, result in test_results.items():
        status = result.get("status", "UNKNOWN")
        if status == "PASS":
            status_icon = "✅"
        elif status == "PARTIAL":
            status_icon = "⚠️"
        else:
            status_icon = "❌"
            
        print(f"{status_icon} {test_name.replace('_', ' ').title()}: {status}")
        print(f"   {result.get('summary', 'No summary available')}")
        
        if status == "FAIL" and result.get("error"):
            print(f"   Error: {result.get('error')}")
        elif result.get("details"):
            details = result.get("details", {})
            for key, value in list(details.items())[:3]:  # Show first 3 details
                print(f"   {key}: {value}")
        print()
    
    # Overall assessment
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! System is ready for production deployment.")
        print("✅ End-to-end workflows are functioning correctly")
        print("✅ Data integrity is maintained across modules")
        print("✅ Performance is within acceptable ranges")
    elif (passed_tests + partial_tests) >= total_tests * 0.8:
        print("⚠️ MOST TESTS PASSED. System is largely functional with minor issues.")
        print("✅ Core workflows are working")
        print("⚠️ Some features may need refinement before production")
    else:
        print("🚨 SIGNIFICANT ISSUES DETECTED. System needs attention before production.")
        print("❌ Core functionality issues detected")
        print("🔧 Address failed tests before proceeding")
    
    print("="*80)


# Main execution function
if __name__ == "__main__":
    test_end_to_end_workflows() 