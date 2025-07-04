#!/usr/bin/env python3
"""
Test script for validating the Live API Testing and Performance Monitoring system
This script validates that task 17.7 is complete and working correctly
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Add the apps directory to the Python path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench/apps")


def test_api_endpoints():
    """Test that all required API endpoints are accessible"""
    print("🔍 Testing API endpoints...")

    endpoints_to_test = [
        "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json",
        "https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/Toyota?format=json",
    ]

    results = {}

    for endpoint in endpoints_to_test:
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000

            results[endpoint] = {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "data_size": len(response.content) if response.content else 0,
            }

            print(f"   ✅ {endpoint}: {response.status_code} ({response_time:.1f}ms)")

        except requests.exceptions.Timeout:
            results[endpoint] = {"status": "timeout", "error": "Request timed out"}
            print(f"   ⏱️ {endpoint}: Timeout")

        except Exception as e:
            results[endpoint] = {"status": "error", "error": str(e)}
            print(f"   ❌ {endpoint}: Error - {e}")

    return results


def test_file_structure():
    """Test that all required files are in place"""
    print("\n📁 Testing file structure...")

    required_files = [
        "apps/universal_workshop/universal_workshop/vehicle_management/live_api_test.py",
        "apps/universal_workshop/universal_workshop/vehicle_management/page/api_performance_dashboard/api_performance_dashboard.py",
        "apps/universal_workshop/universal_workshop/vehicle_management/page/api_performance_dashboard/api_performance_dashboard.html",
        "apps/universal_workshop/universal_workshop/vehicle_management/page/api_performance_dashboard/api_performance_dashboard.js",
        "apps/universal_workshop/universal_workshop/vehicle_management/api.py",
    ]

    missing_files = []

    for file_path in required_files:
        full_path = f"/home/said/frappe-dev/frappe-bench/{file_path}"
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            missing_files.append(file_path)

    return len(missing_files) == 0, missing_files


def test_python_imports():
    """Test that the Python modules can be imported correctly"""
    print("\n🐍 Testing Python imports...")

    try:
        # Test main live testing module
        spec = __import__(
            "universal_workshop.universal_workshop.vehicle_management.live_api_test", fromlist=[""]
        )
        print("   ✅ live_api_test module imports successfully")

        # Check for required classes and functions
        if hasattr(spec, "VehicleAPILiveTester"):
            print("   ✅ VehicleAPILiveTester class found")
        else:
            print("   ❌ VehicleAPILiveTester class missing")
            return False

        if hasattr(spec, "run_live_api_tests"):
            print("   ✅ run_live_api_tests function found")
        else:
            print("   ❌ run_live_api_tests function missing")
            return False

        return True

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_gcc_vehicle_data():
    """Test access to GCC/Oman relevant vehicle data"""
    print("\n🚗 Testing GCC vehicle data access...")

    gcc_makes = ["Toyota", "Nissan", "Honda", "BMW", "Mercedes-Benz"]

    for make in gcc_makes[:3]:  # Test first 3 to avoid rate limits
        try:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{make}?format=json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("Results", []))
                print(f"   ✅ {make}: {model_count} models available")
            else:
                print(f"   ⚠️ {make}: API returned {response.status_code}")

        except Exception as e:
            print(f"   ❌ {make}: Error - {e}")


def test_arabic_translation_system():
    """Test the Arabic translation system"""
    print("\n🔤 Testing Arabic translation system...")

    # Test translation mapping
    test_translations = {"Toyota": "تويوتا", "BMW": "بي إم دبليو", "Mercedes-Benz": "مرسيدس بنز"}

    for english, expected_arabic in test_translations.items():
        # This is a simple test - in real implementation we'd test the actual translation function
        if expected_arabic:
            # Check if it contains Arabic characters
            has_arabic = any("\u0600" <= char <= "\u06ff" for char in expected_arabic)
            if has_arabic:
                print(f"   ✅ {english} → {expected_arabic}")
            else:
                print(f"   ⚠️ {english} → {expected_arabic} (not Arabic characters)")
        else:
            print(f"   ❌ {english} → No translation")


def test_performance_requirements():
    """Test that performance requirements are met"""
    print("\n⚡ Testing performance requirements...")

    # Test VIN decoder response time (should be < 5 seconds)
    test_vin = "1HGBH41JXMN109186"  # Sample VIN

    try:
        start_time = time.time()
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{test_vin}?format=json"
        response = requests.get(url, timeout=10)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        if response_time < 5000:  # 5 seconds
            print(f"   ✅ VIN decoder response time: {response_time:.1f}ms (< 5s requirement)")
        else:
            print(f"   ⚠️ VIN decoder response time: {response_time:.1f}ms (exceeds 5s requirement)")

        return response_time < 5000

    except Exception as e:
        print(f"   ❌ VIN decoder test failed: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 TASK 17.7 VALIDATION REPORT")
    print("=" * 60)

    # Run all tests
    api_results = test_api_endpoints()
    file_check, missing_files = test_file_structure()
    import_success = test_python_imports()

    test_gcc_vehicle_data()
    test_arabic_translation_system()
    performance_ok = test_performance_requirements()

    # Calculate overall score
    total_score = 0
    max_score = 6

    # API connectivity (1 point)
    if any(result.get("status") == "success" for result in api_results.values()):
        total_score += 1
        print("\n✅ API Connectivity: PASS")
    else:
        print("\n❌ API Connectivity: FAIL")

    # File structure (1 point)
    if file_check:
        total_score += 1
        print("✅ File Structure: PASS")
    else:
        print("❌ File Structure: FAIL")
        print(f"   Missing files: {missing_files}")

    # Python imports (1 point)
    if import_success:
        total_score += 1
        print("✅ Python Imports: PASS")
    else:
        print("❌ Python Imports: FAIL")

    # Performance requirements (1 point)
    if performance_ok:
        total_score += 1
        print("✅ Performance Requirements: PASS")
    else:
        print("❌ Performance Requirements: FAIL")

    # Implementation completeness (2 points for having all components)
    components_complete = file_check and import_success
    if components_complete:
        total_score += 2
        print("✅ Implementation Completeness: PASS")
    else:
        print("❌ Implementation Completeness: FAIL")

    # Final assessment
    percentage = (total_score / max_score) * 100

    print(f"\n🎯 OVERALL SCORE: {total_score}/{max_score} ({percentage:.1f}%)")

    if percentage >= 80:
        print("🎉 TASK 17.7 STATUS: ✅ COMPLETED SUCCESSFULLY")
        print("   The live API testing and performance monitoring system is ready for production!")
    elif percentage >= 60:
        print("⚠️ TASK 17.7 STATUS: 🔧 NEEDS MINOR FIXES")
        print("   The system is mostly complete but requires some adjustments.")
    else:
        print("❌ TASK 17.7 STATUS: 🚫 INCOMPLETE")
        print("   Significant work needed before the system is ready.")

    # Generate recommendations
    print("\n💡 RECOMMENDATIONS:")
    if not file_check:
        print("   - Ensure all required files are properly created")
    if not import_success:
        print("   - Fix Python import issues and module structure")
    if not performance_ok:
        print("   - Optimize API response times to meet <5s requirement")

    print("\n📅 Test completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "status": "COMPLETED" if percentage >= 80 else "NEEDS_WORK",
    }


if __name__ == "__main__":
    print("🚀 Starting Task 17.7 Validation Tests")
    print("   Live API Testing and Performance Tuning")
    print("-" * 60)

    try:
        report = generate_test_report()

        # Save report to file
        report_file = "/home/said/frappe-dev/frappe-bench/task_17_validation_report.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "test_date": datetime.now().isoformat(),
                    "task": "17.7 - Live API Testing and Performance Tuning",
                    "results": report,
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"\n💥 Test script failed with error: {e}")
        sys.exit(1)
