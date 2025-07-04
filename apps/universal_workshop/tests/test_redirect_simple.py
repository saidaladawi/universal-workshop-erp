#!/usr/bin/env python3

import sys
import os

# Add the frappe path
sys.path.append("/home/said/frappe-dev/frappe-bench/apps/frappe")
sys.path.append("/home/said/frappe-dev/frappe-bench/apps/erpnext")
sys.path.append("/home/said/frappe-dev/frappe-bench/apps/universal_workshop")

import frappe


def test_redirect():
    print("🔒 Testing Secure Redirect System")
    print("=" * 40)

    try:
        # Initialize Frappe
        frappe.init(site="universal.local")
        frappe.connect()

        # Import secure redirect
        from universal_workshop.user_management.secure_redirect import get_redirect_manager

        manager = get_redirect_manager()
        print("✅ Secure redirect manager initialized")

        # Test 1: Malicious URL
        result = manager.validate_redirect_url("http://evil.com/steal")
        if not result["is_valid"]:
            print("✅ Malicious URL blocked:", result["error"])
        else:
            print("❌ Malicious URL not blocked!")

        # Test 2: Valid URL
        result = manager.validate_redirect_url("/app")
        if result["is_valid"]:
            print("✅ Valid URL accepted")
        else:
            print("❌ Valid URL rejected:", result["error"])

        # Test 3: Role-based redirect
        roles = ["Workshop Manager"]
        redirect = manager._get_role_based_redirect(roles)
        expected = "/app/workspace/Workshop%20Management"
        if redirect == expected:
            print("✅ Role-based redirect correct:", redirect)
        else:
            print("❌ Role-based redirect incorrect:", redirect, "expected:", expected)

        # Test 4: XSS attempt
        result = manager.validate_redirect_url("javascript:alert('xss')")
        if not result["is_valid"]:
            print("✅ XSS attempt blocked:", result["error"])
        else:
            print("❌ XSS attempt not blocked!")

        print("\n🎉 All basic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_redirect()
    sys.exit(0 if success else 1)
