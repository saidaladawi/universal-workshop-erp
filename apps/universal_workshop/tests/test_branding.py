#!/usr/bin/env python3
"""
Test script for Universal Workshop Branding Service
Tests dynamic logo injection and branding functionality
"""

import frappe
import json


def test_branding_service():
    """Test the branding service functionality"""

    print("🧪 Testing Universal Workshop Branding Service")
    print("=" * 50)

    # Test 1: Check if Workshop Profile DocType exists with branding fields
    print("\n1. Testing Workshop Profile DocType...")
    try:
        meta = frappe.get_meta("Workshop Profile")
        branding_fields = [
            "workshop_logo",
            "logo_preview",
            "primary_color",
            "secondary_color",
            "dark_mode_enabled",
            "theme_preference",
        ]

        existing_fields = [field.fieldname for field in meta.fields]
        missing_fields = [field for field in branding_fields if field not in existing_fields]

        if not missing_fields:
            print("✅ All branding fields exist in Workshop Profile")
        else:
            print(f"❌ Missing fields: {missing_fields}")

    except Exception as e:
        print(f"❌ Error checking Workshop Profile: {e}")

    # Test 2: Test branding API method
    print("\n2. Testing branding API method...")
    try:
        from universal_workshop.workshop_operations.workshop_profile.workshop_profile import (
            get_workshop_branding,
        )

        # Test with no workshop (should return default)
        default_branding = get_workshop_branding()
        print(f"✅ Default branding loaded: {json.dumps(default_branding, indent=2)}")

    except Exception as e:
        print(f"❌ Error testing branding API: {e}")

    # Test 3: Check if assets are properly linked
    print("\n3. Testing asset integration...")
    try:
        from universal_workshop import hooks

        # Check if branding service is in app includes
        branding_js_found = any("branding_service.js" in js for js in hooks.app_include_js)
        branding_css_found = any("dynamic_branding.css" in css for css in hooks.app_include_css)

        if branding_js_found:
            print("✅ Branding service JS found in app includes")
        else:
            print("❌ Branding service JS not found in app includes")

        if branding_css_found:
            print("✅ Dynamic branding CSS found in app includes")
        else:
            print("❌ Dynamic branding CSS not found in app includes")

    except Exception as e:
        print(f"❌ Error checking asset integration: {e}")

    # Test 4: Create test workshop profile with branding
    print("\n4. Testing workshop profile creation with branding...")
    try:
        # Check if any workshop profiles exist
        existing_workshops = frappe.get_list("Workshop Profile", limit=1)

        if existing_workshops:
            workshop = frappe.get_doc("Workshop Profile", existing_workshops[0].name)
            print(f"✅ Found existing workshop: {workshop.workshop_name}")

            # Test branding retrieval for specific workshop
            workshop_branding = get_workshop_branding(workshop.name)
            print(f"✅ Workshop branding: {json.dumps(workshop_branding, indent=2)}")

        else:
            print("ℹ️  No workshop profiles found - branding will use defaults")

    except Exception as e:
        print(f"❌ Error testing workshop profile branding: {e}")

    print("\n" + "=" * 50)
    print("🎯 Branding Service Test Complete!")

    return True


if __name__ == "__main__":
    # Initialize Frappe
    frappe.init(site="universal.local")
    frappe.connect()

    try:
        test_branding_service()
    finally:
        frappe.destroy()
