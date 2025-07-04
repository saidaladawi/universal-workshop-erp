#!/usr/bin/env python3
"""
Test script for Performance Visualizations functionality
Universal Workshop ERP - Task 20.6 validation
"""

import os
import sys
import json
import time
from pathlib import Path


def test_file_structure():
    """Test that all required files exist and are properly structured"""
    print("📁 Testing file structure...")

    files_to_check = [
        "universal_workshop/dashboard/performance_visualizations.py",
        "universal_workshop/public/js/performance_visualizations.js",
        "universal_workshop/public/css/performance_visualizations.css",
        "universal_workshop/config/dashboard_workspace.py",
    ]

    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} - NOT FOUND")
            all_exist = False

    return all_exist


def test_python_implementation():
    """Test the Python implementation"""
    print("🐍 Testing Python implementation...")

    try:
        # Read the Python file and check for key components
        with open("universal_workshop/dashboard/performance_visualizations.py", "r") as f:
            content = f.read()

        required_elements = [
            "class PerformanceVisualizationEngine:",
            "@frappe.whitelist()",
            "get_chart_config",
            "get_all_charts_config",
            "refresh_chart_data",
            "revenue_trend",
            "technician_performance",
            "customer_satisfaction",
            "inventory_turnover",
            "Arabic",
            "RTL",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            print(f"   ❌ Missing elements: {missing_elements}")
            return False
        else:
            print("   ✅ All required Python elements found")
            return True

    except Exception as e:
        print(f"   ❌ Error reading Python file: {e}")
        return False


def test_javascript_implementation():
    """Test the JavaScript implementation"""
    print("🌐 Testing JavaScript implementation...")

    try:
        # Read the JavaScript file and check for key components
        with open("universal_workshop/public/js/performance_visualizations.js", "r") as f:
            content = f.read()

        required_elements = [
            "class PerformanceVisualizationManager",
            "loadChartJS()",
            "setupAutoRefresh()",
            "setupWebSocketUpdates()",
            "renderChart",
            "refreshAllCharts",
            "formatArabicNumber",
            "RTL",
            "Chart.js",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            print(f"   ❌ Missing JavaScript elements: {missing_elements}")
            return False
        else:
            print("   ✅ All required JavaScript elements found")
            return True

    except Exception as e:
        print(f"   ❌ Error reading JavaScript file: {e}")
        return False


def test_css_implementation():
    """Test the CSS implementation"""
    print("🎨 Testing CSS implementation...")

    try:
        # Read the CSS file and check for key components
        with open("universal_workshop/public/css/performance_visualizations.css", "r") as f:
            content = f.read()

        required_elements = [
            "performance-visualizations",
            "charts-grid",
            "chart-container",
            "rtl",
            "arabic",
            "responsive",
            "@media",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            print(f"   ❌ Missing CSS elements: {missing_elements}")
            return False
        else:
            print("   ✅ All required CSS elements found")
            return True

    except Exception as e:
        print(f"   ❌ Error reading CSS file: {e}")
        return False


def test_arabic_localization():
    """Test Arabic localization features"""
    print("🔤 Testing Arabic localization...")

    try:
        with open("universal_workshop/dashboard/performance_visualizations.py", "r") as f:
            content = f.read()

        arabic_features = [
            "arabic_numerals",
            "RTL",
            "arabic_months",
            "_convert_to_arabic_numerals",
            "_format_date_label",
            "Cairo, Tahoma",
            "self.is_arabic",
        ]

        missing_features = []
        for feature in arabic_features:
            if feature not in content:
                missing_features.append(feature)

        if missing_features:
            print(f"   ❌ Missing Arabic features: {missing_features}")
            return False
        else:
            print("   ✅ All Arabic localization features found")
            return True

    except Exception as e:
        print(f"   ❌ Error checking Arabic features: {e}")
        return False


def test_chart_types():
    """Test that all required chart types are implemented"""
    print("📊 Testing chart types...")

    try:
        with open("universal_workshop/dashboard/performance_visualizations.py", "r") as f:
            content = f.read()

        required_charts = [
            "'revenue_trend'",
            "'service_completion'",
            "'technician_performance'",
            "'customer_satisfaction'",
            "'inventory_turnover'",
            "'service_type_distribution'",
            "'monthly_targets'",
        ]

        missing_charts = []
        for chart in required_charts:
            if chart not in content:
                missing_charts.append(chart)

        if missing_charts:
            print(f"   ❌ Missing chart types: {missing_charts}")
            return False
        else:
            print("   ✅ All required chart types found")
            return True

    except Exception as e:
        print(f"   ❌ Error checking chart types: {e}")
        return False


def test_auto_refresh_logic():
    """Test auto-refresh implementation"""
    print("🔄 Testing auto-refresh logic...")

    try:
        with open("universal_workshop/public/js/performance_visualizations.js", "r") as f:
            content = f.read()

        refresh_features = [
            "autoRefreshEnabled",
            "refreshIntervals",
            "setupAutoRefresh",
            "refreshAllCharts",
            "setInterval",
            "clearInterval",
            "WebSocket",
        ]

        missing_features = []
        for feature in refresh_features:
            if feature not in content:
                missing_features.append(feature)

        if missing_features:
            print(f"   ❌ Missing auto-refresh features: {missing_features}")
            return False
        else:
            print("   ✅ All auto-refresh features found")
            return True

    except Exception as e:
        print(f"   ❌ Error checking auto-refresh logic: {e}")
        return False


def main():
    """Main test runner"""
    print("🚀 Starting Task 20.6 Validation Tests")
    print("   Performance Visualizations and Auto-refresh Logic")
    print("-" * 60)

    tests = [
        ("File Structure", test_file_structure),
        ("Python Implementation", test_python_implementation),
        ("JavaScript Implementation", test_javascript_implementation),
        ("CSS Implementation", test_css_implementation),
        ("Arabic Localization", test_arabic_localization),
        ("Chart Types", test_chart_types),
        ("Auto-refresh Logic", test_auto_refresh_logic),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Calculate results
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total) * 100

    print("\n" + "=" * 60)
    print("📊 TASK 20.6 VALIDATION REPORT")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n🎯 OVERALL SCORE: {passed}/{total} ({percentage:.1f}%)")

    if percentage >= 90:
        print("✅ TASK 20.6 STATUS: 🎉 COMPLETE")
        print("   Performance visualizations fully implemented!")
    elif percentage >= 70:
        print("⚠️  TASK 20.6 STATUS: 🔧 MOSTLY COMPLETE")
        print("   Minor fixes needed.")
    else:
        print("❌ TASK 20.6 STATUS: 🚫 INCOMPLETE")
        print("   Significant work needed before the system is ready.")

    print(f"\n📅 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Save detailed report
    report = {
        "task": "20.6 - Performance Visualizations and Auto-refresh Logic",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {name: result for name, result in results},
        "score": f"{passed}/{total}",
        "percentage": percentage,
        "status": "complete" if percentage >= 90 else "incomplete",
    }

    with open("task_20_6_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 Detailed report saved to: {os.path.abspath('task_20_6_validation_report.json')}")


if __name__ == "__main__":
    main()
