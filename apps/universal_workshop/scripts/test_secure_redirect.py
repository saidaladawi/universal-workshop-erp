#!/usr/bin/env python3
"""
Test script for Secure Redirect functionality in Universal Workshop ERP

This script validates that the secure redirect system properly handles
various types of URLs and prevents open redirect attacks.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import frappe
from universal_workshop.user_management.secure_redirect import get_redirect_manager


def test_secure_redirect():
    """Test secure redirect functionality"""
    print("🔒 Testing Secure Redirect Manager")
    print("=" * 50)

    # Initialize redirect manager
    manager = get_redirect_manager()

    # Test cases
    test_cases = [
        # Valid URLs
        {"url": "/app", "expected_valid": True, "description": "Valid relative path"},
        {
            "url": "/app/workspace/Workshop%20Management",
            "expected_valid": True,
            "description": "Valid workshop workspace URL",
        },
        {
            "url": "/technician",
            "expected_valid": True,
            "description": "Valid technician portal URL",
        },
        {
            "url": "/customer-portal",
            "expected_valid": True,
            "description": "Valid customer portal URL",
        },
        # Invalid/Dangerous URLs
        {
            "url": "http://evil.com/steal-data",
            "expected_valid": False,
            "description": "External malicious URL",
        },
        {
            "url": "javascript:alert('xss')",
            "expected_valid": False,
            "description": "JavaScript injection attempt",
        },
        {
            "url": "//evil.com/redirect",
            "expected_valid": False,
            "description": "Protocol-relative URL to external site",
        },
        {
            "url": "data:text/html,<script>alert('xss')</script>",
            "expected_valid": False,
            "description": "Data URL with script",
        },
        {
            "url": "/app/../../../etc/passwd",
            "expected_valid": False,
            "description": "Path traversal attempt",
        },
        {
            "url": "http://localhost:8000@evil.com/",
            "expected_valid": False,
            "description": "URL with @ character for host confusion",
        },
        # Edge cases
        {"url": "", "expected_valid": False, "description": "Empty URL"},
        {"url": None, "expected_valid": False, "description": "None URL"},
        {
            "url": "/app/some-new-feature",
            "expected_valid": True,
            "description": "Valid app sub-path",
        },
    ]

    # Run tests
    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        url = test_case["url"]
        expected_valid = test_case["expected_valid"]
        description = test_case["description"]

        try:
            # Test URL validation
            if url is None:
                result = manager.validate_redirect_url("")
            else:
                result = manager.validate_redirect_url(url)

            actual_valid = result["is_valid"]

            # Check if result matches expectation
            if actual_valid == expected_valid:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1

            print(f"{i:2d}. {status} - {description}")
            print(f"    URL: {url}")
            print(f"    Expected: {'Valid' if expected_valid else 'Invalid'}")
            print(f"    Actual: {'Valid' if actual_valid else 'Invalid'}")

            if not actual_valid:
                print(f"    Error: {result.get('error', 'N/A')}")
                print(f"    Safe URL: {result.get('safe_url', 'N/A')}")

            print()

        except Exception as e:
            print(f"{i:2d}. ❌ ERROR - {description}")
            print(f"    URL: {url}")
            print(f"    Exception: {e}")
            print()
            failed += 1

    # Test role-based redirects
    print("\n🎭 Testing Role-Based Redirects")
    print("=" * 40)

    role_test_cases = [
        {
            "roles": ["Workshop Owner"],
            "expected": "/app/workspace/Workshop%20Management",
            "description": "Workshop Owner role",
        },
        {
            "roles": ["Workshop Manager"],
            "expected": "/app/workspace/Workshop%20Management",
            "description": "Workshop Manager role",
        },
        {
            "roles": ["Workshop Technician"],
            "expected": "/technician",
            "description": "Workshop Technician role",
        },
        {"roles": ["Customer"], "expected": "/customer-portal", "description": "Customer role"},
        {
            "roles": ["System Manager"],
            "expected": "/app/workspace/Workshop%20Management",
            "description": "System Manager role",
        },
        {"roles": ["Unknown Role"], "expected": "/app", "description": "Unknown role fallback"},
    ]

    for i, test_case in enumerate(role_test_cases, 1):
        roles = test_case["roles"]
        expected = test_case["expected"]
        description = test_case["description"]

        try:
            actual = manager._get_role_based_redirect(roles)

            if actual == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1

            print(f"{i}. {status} - {description}")
            print(f"   Roles: {roles}")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
            print()

        except Exception as e:
            print(f"{i}. ❌ ERROR - {description}")
            print(f"   Roles: {roles}")
            print(f"   Exception: {e}")
            print()
            failed += 1

    # Test safe redirect with fallback
    print("\n🛡️ Testing Safe Redirect with Fallback")
    print("=" * 45)

    fallback_test_cases = [
        {
            "url": "http://evil.com/steal",
            "roles": ["Workshop Manager"],
            "expected": "/app/workspace/Workshop%20Management",
            "description": "Malicious URL with role fallback",
        },
        {
            "url": "/app/valid-path",
            "roles": ["Customer"],
            "expected": "/app/valid-path",
            "description": "Valid URL should be preserved",
        },
        {
            "url": "javascript:alert('xss')",
            "roles": ["Workshop Technician"],
            "expected": "/technician",
            "description": "XSS attempt with role fallback",
        },
    ]

    for i, test_case in enumerate(fallback_test_cases, 1):
        url = test_case["url"]
        roles = test_case["roles"]
        expected = test_case["expected"]
        description = test_case["description"]

        try:
            actual = manager.get_safe_redirect_url(url, roles)

            if actual == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1

            print(f"{i}. {status} - {description}")
            print(f"   URL: {url}")
            print(f"   Roles: {roles}")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
            print()

        except Exception as e:
            print(f"{i}. ❌ ERROR - {description}")
            print(f"   URL: {url}")
            print(f"   Roles: {roles}")
            print(f"   Exception: {e}")
            print()
            failed += 1

    # Summary
    total_tests = passed + failed
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total_tests*100):.1f}%")

    if failed == 0:
        print("\n🎉 All tests passed! Secure redirect system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the secure redirect implementation.")
        return False


def test_configuration():
    """Test redirect manager configuration"""
    print("\n⚙️ Testing Configuration")
    print("=" * 25)

    manager = get_redirect_manager()
    config = manager.get_configuration()

    print("Allowed Schemes:", config["allowed_schemes"])
    print("Allowed Hosts:", config["allowed_hosts"])
    print("Default Redirect:", config["default_redirect"])
    print("Safe Paths Count:", len(config["safe_paths"]))
    print("Blocked Patterns Count:", len(config["blocked_patterns"]))

    # Validate configuration
    checks = [
        len(config["allowed_schemes"]) > 0,
        len(config["allowed_hosts"]) > 0,
        config["default_redirect"] is not None,
        len(config["safe_paths"]) > 0,
        len(config["blocked_patterns"]) > 0,
    ]

    if all(checks):
        print("✅ Configuration is valid")
        return True
    else:
        print("❌ Configuration has issues")
        return False


if __name__ == "__main__":
    print("🚀 Starting Secure Redirect Tests")
    print("=" * 40)

    try:
        # Test configuration
        config_ok = test_configuration()

        # Test redirect functionality
        redirect_ok = test_secure_redirect()

        if config_ok and redirect_ok:
            print("\n🎯 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
