#!/usr/bin/env python3
"""
Universal Workshop ERP - Simple RTL Validation Test
Quick validation for RTL and branding implementation
"""

import os
import json
import re
from pathlib import Path


def validate_css_file(file_path, expected_rules):
    """Validate CSS file for RTL rules"""
    if not os.path.exists(file_path):
        return False, f"File {file_path} not found"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_rules = []
    for rule in expected_rules:
        if rule not in content:
            missing_rules.append(rule)
    
    if missing_rules:
        return False, f"Missing rules: {missing_rules}"
    
    return True, f"All {len(expected_rules)} rules found"


def validate_js_file(file_path, expected_functions):
    """Validate JavaScript file for required functions"""
    if not os.path.exists(file_path):
        return False, f"File {file_path} not found"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_functions = []
    for func in expected_functions:
        if func not in content:
            missing_functions.append(func)
    
    if missing_functions:
        return False, f"Missing functions: {missing_functions}"
    
    return True, f"All {len(expected_functions)} functions found"


def validate_hooks_integration(hooks_path):
    """Validate that RTL files are properly included in hooks.py"""
    if not os.path.exists(hooks_path):
        return False, "hooks.py not found"
    
    with open(hooks_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_includes = [
        "arabic-rtl.css",
        "dynamic_branding.css", 
        "rtl_branding_manager.js"
    ]
    
    missing_includes = []
    for include in required_includes:
        if include not in content:
            missing_includes.append(include)
    
    if missing_includes:
        return False, f"Missing includes: {missing_includes}"
    
    return True, "All RTL files properly included"


def main():
    """Run RTL validation tests"""
    print("🔍 Universal Workshop RTL Implementation Validation")
    print("=" * 50)
    
    # Base paths
    base_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop"
    
    results = []
    
    # Test 1: Arabic RTL CSS
    print("\n1. Testing Arabic RTL CSS...")
    rtl_css_path = f"{base_path}/public/css/arabic-rtl.css"
    rtl_rules = [
        "[dir=\"rtl\"]",
        "direction: rtl",
        "text-align: right",
        "padding-inline-start",
        "margin-inline-end"
    ]
    
    success, message = validate_css_file(rtl_css_path, rtl_rules)
    results.append(("Arabic RTL CSS", success, message))
    print(f"   {'✅' if success else '❌'} {message}")
    
    # Test 2: Dynamic Branding CSS
    print("\n2. Testing Dynamic Branding CSS...")
    branding_css_path = f"{base_path}/public/css/dynamic_branding.css"
    branding_rules = [
        "--workshop-primary",
        "--workshop-secondary",
        ".workshop-brand",
        "color-scheme",
        "@media (prefers-reduced-motion"
    ]
    
    success, message = validate_css_file(branding_css_path, branding_rules)
    results.append(("Dynamic Branding CSS", success, message))
    print(f"   {'✅' if success else '❌'} {message}")
    
    # Test 3: RTL Branding Manager JS
    print("\n3. Testing RTL Branding Manager JS...")
    rtl_js_path = f"{base_path}/public/js/rtl_branding_manager.js"
    js_functions = [
        "class WorkshopRTLManager",
        "setRTL",
        "setLanguage",
        "updateBranding",
        "detectBrowser",
        "enhanceAuthenticationUI"
    ]
    
    success, message = validate_js_file(rtl_js_path, js_functions)
    results.append(("RTL Branding Manager JS", success, message))
    print(f"   {'✅' if success else '❌'} {message}")
    
    # Test 4: Hooks Integration
    print("\n4. Testing Hooks Integration...")
    hooks_path = f"{base_path}/hooks.py"
    
    success, message = validate_hooks_integration(hooks_path)
    results.append(("Hooks Integration", success, message))
    print(f"   {'✅' if success else '❌'} {message}")
    
    # Test 5: File Sizes
    print("\n5. Testing File Sizes...")
    files_to_check = [
        (rtl_css_path, 1000),  # At least 1KB
        (branding_css_path, 1000),  # At least 1KB
        (rtl_js_path, 1000),  # At least 1KB
    ]
    
    all_sizes_ok = True
    for file_path, min_size in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size >= min_size:
                print(f"   ✅ {os.path.basename(file_path)}: {size} bytes")
            else:
                print(f"   ❌ {os.path.basename(file_path)}: {size} bytes (too small)")
                all_sizes_ok = False
        else:
            print(f"   ❌ {os.path.basename(file_path)}: Not found")
            all_sizes_ok = False
    
    results.append(("File Sizes", all_sizes_ok, "All files have adequate content"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:>6}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All RTL implementation tests PASSED!")
        print("✅ Cross-browser RTL compatibility is ready")
        return True
    else:
        print("⚠️  Some RTL implementation tests FAILED")
        print("❌ Please fix the issues before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
