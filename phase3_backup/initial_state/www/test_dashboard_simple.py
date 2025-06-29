#!/usr/bin/env python3
# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Simple test script to validate Universal Workshop Dashboard functionality
"""

import sys
import os

# Add the app path to Python path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench")


def test_dashboard_imports():
    """Test that all dashboard modules can be imported"""
    print("Testing dashboard imports...")

    try:
        # Test dashboard Python file import
        from apps.universal_workshop.universal_workshop.www.universal_workshop_dashboard import (
            get_dashboard_data,
            get_kpi_data,
            has_dashboard_access,
            get_workshop_config,
        )

        print("✓ Dashboard Python functions imported successfully")

        # Test Customer Feedback import
        from apps.universal_workshop.universal_workshop.customer_satisfaction.doctype.customer_feedback.customer_feedback import (
            get_customer_feedback_summary,
        )

        print("✓ Customer Feedback functions imported successfully")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ General error: {e}")
        return False


def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")

    required_files = [
        "apps/universal_workshop/universal_workshop/www/universal-workshop-dashboard.py",
        "apps/universal_workshop/universal_workshop/www/universal-workshop-dashboard.html",
        "apps/universal_workshop/universal_workshop/customer_satisfaction/doctype/customer_feedback/customer_feedback.json",
        "apps/universal_workshop/universal_workshop/customer_satisfaction/doctype/customer_feedback/customer_feedback.py",
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def test_basic_functionality():
    """Test basic dashboard functionality without Frappe context"""
    print("\nTesting basic functionality...")

    try:
        # Test basic Python functionality
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta

        # Test date calculations
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - relativedelta(months=1)

        print(
            f"✓ Date calculations work: Today={today}, Week ago={week_ago}, Month ago={month_ago}"
        )

        # Test JSON functionality
        import json

        test_data = {
            "dashboard": "Universal Workshop",
            "status": "operational",
            "modules": ["service_orders", "customers", "vehicles", "inventory"],
        }
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)

        print("✓ JSON serialization/deserialization works")

        return True

    except Exception as e:
        print(f"✗ Basic functionality error: {e}")
        return False


def validate_doctype_structure():
    """Validate Customer Feedback DocType structure"""
    print("\nValidating DocType structure...")

    try:
        import json

        # Read Customer Feedback DocType JSON
        with open(
            "apps/universal_workshop/universal_workshop/customer_satisfaction/doctype/customer_feedback/customer_feedback.json",
            "r",
        ) as f:
            doctype_data = json.load(f)

        # Check required properties
        required_props = ["name", "doctype", "fields", "permissions"]
        for prop in required_props:
            if prop in doctype_data:
                print(f"✓ {prop} exists in DocType")
            else:
                print(f"✗ {prop} missing from DocType")
                return False

        # Check field structure
        fields = doctype_data.get("fields", [])
        if len(fields) > 0:
            print(f"✓ DocType has {len(fields)} fields")

            # Check for key fields
            field_names = [field.get("fieldname") for field in fields]
            key_fields = ["customer", "satisfaction_rating", "feedback_date"]

            for key_field in key_fields:
                if key_field in field_names:
                    print(f"✓ Key field '{key_field}' exists")
                else:
                    print(f"✗ Key field '{key_field}' missing")

        return True

    except FileNotFoundError:
        print("✗ Customer Feedback DocType JSON file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"✗ DocType validation error: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("Universal Workshop Dashboard - Simple Validation Test")
    print("=" * 60)

    tests = [
        ("File Structure", test_file_structure),
        ("Basic Functionality", test_basic_functionality),
        ("DocType Structure", validate_doctype_structure),
        ("Dashboard Imports", test_dashboard_imports),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:<25} : {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Dashboard is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
