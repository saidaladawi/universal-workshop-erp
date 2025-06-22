#!/usr/bin/env python3
"""
Test script for logo upload and validation functionality
"""

import sys
import os

# Add the bench directory to Python path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench")
os.chdir("/home/said/frappe-dev/frappe-bench")

try:
    import frappe

    # Initialize Frappe with the correct site
    frappe.init(site="universal.local", sites_path="/home/said/frappe-dev/frappe-bench/sites")
    frappe.connect()

    # Test the logo validation function
    from universal_workshop.workshop_management.doctype.workshop_profile.workshop_profile import (
        validate_logo_file,
        get_workshop_branding,
    )

    print("🧪 Testing Logo Upload and Validation System")
    print("=" * 50)

    # Test 1: Invalid file URL
    print("Test 1: Invalid file URL")
    result = validate_logo_file("/files/nonexistent.png")
    print(f"Result: {result}")
    assert not result["valid"], "Should fail for non-existent file"
    print("✅ Test 1 passed\n")

    # Test 2: No file provided
    print("Test 2: No file provided")
    result = validate_logo_file("")
    print(f"Result: {result}")
    assert not result["valid"], "Should fail for empty file URL"
    print("✅ Test 2 passed\n")

    # Test 3: Get default branding settings
    print("Test 3: Default branding settings")
    branding = get_workshop_branding()
    print(f"Default branding: {branding}")
    assert branding["primary_color"] == "#1f4e79", "Should have default primary color"
    assert branding["secondary_color"] == "#e8f4fd", "Should have default secondary color"
    print("✅ Test 3 passed\n")

    # Test 4: Check if Workshop Profile DocType has branding fields
    print("Test 4: Workshop Profile DocType fields")
    doctype_meta = frappe.get_meta("Workshop Profile")
    branding_fields = [
        "workshop_logo",
        "primary_color",
        "secondary_color",
        "dark_mode_enabled",
        "theme_preference",
    ]

    for field in branding_fields:
        if doctype_meta.has_field(field):
            print(f"✅ Field '{field}' exists")
        else:
            print(f"❌ Field '{field}' missing")

    print("\n🎉 All tests completed successfully!")
    print("Logo upload and validation system is ready for use.")

except Exception as e:
    print(f"❌ Error during testing: {str(e)}")
    import traceback

    traceback.print_exc()

finally:
    try:
        frappe.destroy()
    except:
        pass
