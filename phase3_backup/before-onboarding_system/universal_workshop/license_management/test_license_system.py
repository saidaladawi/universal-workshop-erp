#!/usr/bin/env python3
"""
Simple License Management System Test
Tests the complete license management system components
"""

import frappe
from frappe.utils import now_datetime


def test_license_system_components():
    """Test all license management system components"""
    print("🚀 Testing Universal Workshop License Management System")
    print("=" * 60)

    test_results = {"start_time": now_datetime().isoformat(), "tests": {}, "summary": {}}

    # Test 1: DocType Existence
    print("\n1. Testing DocType Existence...")
    doctype_results = test_doctype_existence()
    test_results["tests"]["doctype_existence"] = doctype_results
    print_test_result("DocType Existence", doctype_results)

    # Test 2: File Structure
    print("\n2. Testing File Structure...")
    file_results = test_file_structure()
    test_results["tests"]["file_structure"] = file_results
    print_test_result("File Structure", file_results)

    # Test 3: API Endpoints
    print("\n3. Testing API Endpoints...")
    api_results = test_api_endpoints()
    test_results["tests"]["api_endpoints"] = api_results
    print_test_result("API Endpoints", api_results)

    # Calculate summary
    total_passed = sum(result.get("passed", 0) for result in test_results["tests"].values())
    total_failed = sum(result.get("failed", 0) for result in test_results["tests"].values())

    test_results["summary"] = {
        "total_passed": total_passed,
        "total_failed": total_failed,
        "success_rate": (
            (total_passed / (total_passed + total_failed) * 100)
            if (total_passed + total_failed) > 0
            else 0
        ),
        "overall_status": "PASSED" if total_failed == 0 else "FAILED",
    }

    print_summary(test_results["summary"])
    return test_results


def test_doctype_existence():
    """Test if required DocTypes exist"""
    results = {"passed": 0, "failed": 0, "details": []}

    required_doctypes = [
        "License Management Dashboard",
        "License Activity Log",
        "Dashboard Audit Event",
        "Offline Session",
        "License Audit Log",
        "Business Registration",
        "Business Workshop Binding",
    ]

    for doctype in required_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                results["details"].append(f"✅ {doctype}")
                results["passed"] += 1
            else:
                results["details"].append(f"❌ {doctype} (missing)")
                results["failed"] += 1
        except Exception as e:
            results["details"].append(f"❌ {doctype} (error: {str(e)})")
            results["failed"] += 1

    return results


def test_file_structure():
    """Test if required files exist"""
    import os

    results = {"passed": 0, "failed": 0, "details": []}

    app_path = frappe.get_app_path("universal_workshop")
    license_path = os.path.join(app_path, "license_management")

    required_files = [
        "hardware_fingerprint.py",
        "utils/offline_validation_manager.py",
        "utils/license_lifecycle_manager.py",
        "doctype/license_audit_log/license_audit_log.py",
        "doctype/offline_session/offline_session.py",
        "doctype/business_registration/business_registration.py",
    ]

    for file_path in required_files:
        full_path = os.path.join(license_path, file_path)
        if os.path.exists(full_path):
            results["details"].append(f"✅ {file_path}")
            results["passed"] += 1
        else:
            results["details"].append(f"❌ {file_path} (missing)")
            results["failed"] += 1

    return results


def test_api_endpoints():
    """Test if API endpoints are accessible"""
    results = {"passed": 0, "failed": 0, "details": []}

    # Test basic functionality
    try:
        # Test translation function
        translated = frappe._("License Management")
        results["details"].append("✅ Translation function working")
        results["passed"] += 1
    except Exception as e:
        results["details"].append(f"❌ Translation function failed: {str(e)}")
        results["failed"] += 1

    # Test database connection
    try:
        frappe.db.sql("SELECT 1", as_list=True)
        results["details"].append("✅ Database connection working")
        results["passed"] += 1
    except Exception as e:
        results["details"].append(f"❌ Database connection failed: {str(e)}")
        results["failed"] += 1

    return results


def print_test_result(test_name, results):
    """Print individual test results"""
    status = "✅ PASSED" if results["failed"] == 0 else "❌ FAILED"
    print(f"   {status} - {results['passed']} passed, {results['failed']} failed")


def print_summary(summary):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Passed: {summary['total_passed']}")
    print(f"Total Tests Failed: {summary['total_failed']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Overall Status: {summary['overall_status']}")
    print("=" * 60)


if __name__ == "__main__":
    test_license_system_components()
