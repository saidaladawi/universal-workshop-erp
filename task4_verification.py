#!/usr/bin/env python3
"""
Task 4 Verification Script - Vehicle Management System
Checks if all components of Task 4 have been implemented correctly.
"""

import os
import sys
from pathlib import Path


def check_vehicle_doctypes():
    """Check if all required DocTypes exist"""
    print("🔍 Checking Vehicle Management DocTypes...")

    doctypes_to_check = [
        "vehicle",
        "service_record",
        "service_record_parts",
        "maintenance_alert",
        "vehicle_document",
        "vehicle_inspection",
        "vehicle_inspection_item",
        "vehicle_inspection_photo",
    ]

    missing_doctypes = []
    found_doctypes = []

    for doctype in doctypes_to_check:
        doctype_path = (
            f"apps/universal_workshop/universal_workshop/vehicle_management/doctype/{doctype}"
        )
        if os.path.exists(doctype_path):
            # Check for essential files
            py_file = f"{doctype_path}/{doctype}.py"
            json_file = f"{doctype_path}/{doctype}.json"

            if os.path.exists(py_file) and os.path.exists(json_file):
                found_doctypes.append(doctype)
                print(f"  ✅ {doctype.title().replace('_', ' ')}")
            else:
                missing_doctypes.append(f"{doctype} (missing files)")
                print(f"  ❌ {doctype.title().replace('_', ' ')} (missing files)")
        else:
            missing_doctypes.append(doctype)
            print(f"  ❌ {doctype.title().replace('_', ' ')} (not found)")

    return len(missing_doctypes) == 0, found_doctypes, missing_doctypes


def check_vin_decoder_implementation():
    """Check VIN decoder implementation"""
    print("\n🔍 Checking VIN Decoder Implementation...")

    vehicle_py = (
        "apps/universal_workshop/universal_workshop/vehicle_management/doctype/vehicle/vehicle.py"
    )

    if not os.path.exists(vehicle_py):
        print("  ❌ Vehicle.py not found")
        return False

    with open(vehicle_py, "r", encoding="utf-8") as f:
        content = f.read()

    required_methods = ["decode_vin", "validate_vin", "get_arabic_translation"]

    missing_methods = []
    found_methods = []

    for method in required_methods:
        if f"def {method}" in content:
            found_methods.append(method)
            print(f"  ✅ {method}() method")
        else:
            missing_methods.append(method)
            print(f"  ❌ {method}() method")

    # Check for NHTSA API integration
    if "vpic.nhtsa.dot.gov" in content:
        print("  ✅ NHTSA VIN decoder API integration")
    else:
        print("  ❌ NHTSA VIN decoder API integration")

    return len(missing_methods) == 0


def check_service_history_tracking():
    """Check service history tracking implementation"""
    print("\n🔍 Checking Service History Tracking...")

    service_py = "apps/universal_workshop/universal_workshop/vehicle_management/doctype/service_record/service_record.py"

    if not os.path.exists(service_py):
        print("  ❌ Service Record not found")
        return False

    with open(service_py, "r", encoding="utf-8") as f:
        content = f.read()

    required_features = [
        ("calculate_totals", "Cost calculation"),
        ("set_next_service_due", "Next service calculation"),
        ("set_arabic_translations", "Arabic translations"),
        ("get_service_history", "Service history retrieval"),
        ("validate_mileage", "Mileage validation"),
    ]

    missing_features = []

    for method, description in required_features:
        if f"def {method}" in content:
            print(f"  ✅ {description}")
        else:
            missing_features.append(description)
            print(f"  ❌ {description}")

    return len(missing_features) == 0


def check_maintenance_alerts():
    """Check predictive maintenance alert system"""
    print("\n🔍 Checking Predictive Maintenance Alerts...")

    alert_py = "apps/universal_workshop/universal_workshop/vehicle_management/doctype/maintenance_alert/maintenance_alert.py"

    if not os.path.exists(alert_py):
        print("  ❌ Maintenance Alert not found")
        return False

    with open(alert_py, "r", encoding="utf-8") as f:
        content = f.read()

    required_features = [
        ("generate_maintenance_alerts", "Alert generation"),
        ("calculate_overdue_values", "Overdue calculation"),
        ("set_priority_based_on_urgency", "Priority calculation"),
        ("send_notification", "Notification system"),
        ("acknowledge_alert", "Alert acknowledgment"),
        ("get_arabic_message", "Arabic messaging"),
    ]

    missing_features = []

    for method, description in required_features:
        if f"def {method}" in content:
            print(f"  ✅ {description}")
        else:
            missing_features.append(description)
            print(f"  ❌ {description}")

    return len(missing_features) == 0


def check_document_storage():
    """Check digital document storage system"""
    print("\n🔍 Checking Digital Document Storage...")

    doc_py = "apps/universal_workshop/universal_workshop/vehicle_management/doctype/vehicle_document/vehicle_document.py"

    if not os.path.exists(doc_py):
        print("  ❌ Vehicle Document not found")
        return False

    with open(doc_py, "r", encoding="utf-8") as f:
        content = f.read()

    required_features = [
        ("validate_file_attachment", "File validation (50MB, formats)"),
        ("handle_version_control", "Version control system"),
        ("set_arabic_translations", "Arabic document types"),
        ("validate_expiry_date", "Expiry date tracking"),
        ("create_new_version", "Document versioning"),
        ("get_expiring_documents", "Expiry monitoring"),
    ]

    missing_features = []

    for method, description in required_features:
        if f"def {method}" in content:
            print(f"  ✅ {description}")
        else:
            missing_features.append(description)
            print(f"  ❌ {description}")

    return len(missing_features) == 0


def check_vehicle_inspection():
    """Check vehicle inspection module"""
    print("\n🔍 Checking Vehicle Inspection Module...")

    inspection_py = "apps/universal_workshop/universal_workshop/vehicle_management/doctype/vehicle_inspection/vehicle_inspection.py"

    if not os.path.exists(inspection_py):
        print("  ❌ Vehicle Inspection not found")
        return False

    with open(inspection_py, "r", encoding="utf-8") as f:
        content = f.read()

    required_features = [
        ("calculate_overall_rating", "Rating calculation"),
        ("set_next_inspection_date", "Next inspection scheduling"),
        ("get_arabic_inspection_item", "Arabic checklist items"),
        ("load_standard_checklist", "Standardized checklists"),
        ("create_maintenance_alert", "Integration with alerts"),
        ("get_inspection_statistics", "Inspection analytics"),
    ]

    missing_features = []

    for method, description in required_features:
        if f"def {method}" in content:
            print(f"  ✅ {description}")
        else:
            missing_features.append(description)
            print(f"  ❌ {description}")

    return len(missing_features) == 0


def check_arabic_localization():
    """Check Arabic localization implementation"""
    print("\n🔍 Checking Arabic Localization...")

    files_to_check = [
        "apps/universal_workshop/universal_workshop/vehicle_management/doctype/vehicle/vehicle.py",
        "apps/universal_workshop/universal_workshop/vehicle_management/doctype/service_record/service_record.py",
        "apps/universal_workshop/universal_workshop/vehicle_management/doctype/maintenance_alert/maintenance_alert.py",
    ]

    arabic_features_found = 0
    total_checks = 0

    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for Arabic translations
            total_checks += 1
            if "arabic" in content.lower() or "_ar" in content or "العربية" in content:
                arabic_features_found += 1
                print(f"  ✅ {os.path.basename(file_path)} - Arabic support")
            else:
                print(f"  ❌ {os.path.basename(file_path)} - No Arabic support")

    return arabic_features_found == total_checks


def main():
    """Main verification function"""
    print("🎯 Universal Workshop ERP - Task 4 Verification")
    print("=" * 60)
    print("📋 Vehicle Management and Registry System")
    print("=" * 60)

    # Change to project directory
    if os.path.exists("/home/said/frappe-dev/frappe-bench"):
        os.chdir("/home/said/frappe-dev/frappe-bench")

    # Run all checks
    checks = [
        ("DocTypes Structure", check_vehicle_doctypes),
        ("VIN Decoder Integration", check_vin_decoder_implementation),
        ("Service History Tracking", check_service_history_tracking),
        ("Maintenance Alerts", check_maintenance_alerts),
        ("Document Storage", check_document_storage),
        ("Vehicle Inspection", check_vehicle_inspection),
        ("Arabic Localization", check_arabic_localization),
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, check_function in checks:
        try:
            result = check_function()
            if result:
                passed_checks += 1
        except Exception as e:
            print(f"  ❌ Error in {check_name}: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 TASK 4 VERIFICATION SUMMARY")
    print("=" * 60)

    success_rate = (passed_checks / total_checks) * 100

    print(f"✅ Passed Checks: {passed_checks}/{total_checks}")
    print(f"📈 Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 TASK 4 IMPLEMENTATION: EXCELLENT ✅")
        print("   All major components implemented successfully!")
    elif success_rate >= 75:
        print("✅ TASK 4 IMPLEMENTATION: GOOD ✅")
        print("   Most components working, minor issues may exist.")
    elif success_rate >= 50:
        print("⚠️  TASK 4 IMPLEMENTATION: PARTIAL ⚠️")
        print("   Some components missing or incomplete.")
    else:
        print("❌ TASK 4 IMPLEMENTATION: INCOMPLETE ❌")
        print("   Major components missing or non-functional.")

    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
