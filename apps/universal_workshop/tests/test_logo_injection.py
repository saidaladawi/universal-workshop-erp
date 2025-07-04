#!/usr/bin/env python3
"""
Test script to demonstrate dynamic logo injection functionality
Creates a test workshop profile and tests branding system
"""

import frappe
import json
import os


def create_test_workshop_with_branding():
    """Create a test workshop profile with branding settings"""

    print("🏭 Creating Test Workshop Profile with Branding")
    print("=" * 50)

    try:
        # Check if test workshop already exists
        existing = frappe.db.exists("Workshop Profile", {"workshop_name": "Test Auto Workshop"})

        if existing:
            print("ℹ️  Test workshop already exists, updating branding...")
            workshop = frappe.get_doc("Workshop Profile", existing)
        else:
            print("➕ Creating new test workshop profile...")
            workshop = frappe.new_doc("Workshop Profile")
            workshop.workshop_name = "Test Auto Workshop"
            workshop.workshop_name_ar = "ورشة اختبار السيارات"
            workshop.business_license = "1234567"
            workshop.phone_oman = "+968 24123456"
            workshop.email = "test@workshop.om"
            workshop.address = "Muscat, Oman"
            workshop.address_ar = "مسقط، عمان"

        # Set branding properties
        workshop.primary_color = "#2c5f41"  # Green theme
        workshop.secondary_color = "#e8f5e8"  # Light green
        workshop.dark_mode_enabled = 0
        workshop.theme_preference = "Light"
        workshop.brand_description = "Modern automotive workshop specializing in luxury vehicles"
        workshop.brand_description_ar = "ورشة سيارات حديثة متخصصة في المركبات الفاخرة"

        # Note: In real scenario, workshop_logo would be set via file upload
        # For testing, we'll use a placeholder
        workshop.workshop_logo = "/assets/universal_workshop/images/test-logo.png"

        workshop.save()

        print(f"✅ Workshop Profile created/updated: {workshop.name}")
        print(f"   - Workshop Name: {workshop.workshop_name}")
        print(f"   - Arabic Name: {workshop.workshop_name_ar}")
        print(f"   - Primary Color: {workshop.primary_color}")
        print(f"   - Secondary Color: {workshop.secondary_color}")
        print(f"   - Logo: {workshop.workshop_logo}")

        return workshop

    except Exception as e:
        print(f"❌ Error creating workshop profile: {e}")
        return None


def test_branding_api():
    """Test the branding API with the created workshop"""

    print("\n🔧 Testing Branding API")
    print("=" * 30)

    try:
        from universal_workshop.workshop_operations.workshop_profile.workshop_profile import (
            get_workshop_branding,
        )

        # Test default branding
        default_branding = get_workshop_branding()
        print("📋 Default Branding:")
        print(json.dumps(default_branding, indent=2))

        # Test workshop-specific branding
        workshop = frappe.db.exists("Workshop Profile", {"workshop_name": "Test Auto Workshop"})
        if workshop:
            workshop_branding = get_workshop_branding(workshop)
            print(f"\n🏭 Workshop Branding for {workshop}:")
            print(json.dumps(workshop_branding, indent=2))

            return workshop_branding

    except Exception as e:
        print(f"❌ Error testing branding API: {e}")
        return None


def test_logo_injection_readiness():
    """Test if logo injection system is ready"""

    print("\n🖼️  Testing Logo Injection Readiness")
    print("=" * 40)

    try:
        # Check if branding service exists
        branding_service_path = (
            "apps/universal_workshop/universal_workshop/public/js/branding_service.js"
        )
        if os.path.exists(branding_service_path):
            print("✅ Branding service file exists")
        else:
            print("❌ Branding service file not found")

        # Check if dynamic CSS exists
        css_path = "apps/universal_workshop/universal_workshop/public/css/dynamic_branding.css"
        if os.path.exists(css_path):
            print("✅ Dynamic branding CSS exists")
        else:
            print("❌ Dynamic branding CSS not found")

        # Check hooks integration
        from universal_workshop import hooks

        js_includes = getattr(hooks, "app_include_js", [])
        css_includes = getattr(hooks, "app_include_css", [])

        branding_js_found = any("branding_service.js" in js for js in js_includes)
        branding_css_found = any("dynamic_branding.css" in css for css in css_includes)

        if branding_js_found:
            print("✅ Branding service JS included in hooks")
        else:
            print("❌ Branding service JS not in hooks")

        if branding_css_found:
            print("✅ Dynamic branding CSS included in hooks")
        else:
            print("❌ Dynamic branding CSS not in hooks")

        # Check if assets are built
        print("\n📦 Asset Build Status:")
        print("   Run 'bench build --apps universal_workshop' to ensure assets are built")

        return branding_js_found and branding_css_found

    except Exception as e:
        print(f"❌ Error checking logo injection readiness: {e}")
        return False


def generate_usage_instructions():
    """Generate instructions for using the dynamic logo injection"""

    print("\n📖 Dynamic Logo Injection Usage Instructions")
    print("=" * 50)

    instructions = """
🎯 How to Use Dynamic Logo Injection:

1. 📝 Workshop Profile Setup:
   - Navigate to Workshop Profile in ERPNext
   - Upload your workshop logo in the 'Workshop Logo' field
   - Set primary and secondary colors
   - Choose theme preference (Light/Dark/Auto)
   - Save the profile

2. 🔄 Automatic Logo Injection:
   - Logo automatically appears in header/navbar
   - Logo appears in sidebar (if applicable)
   - Logo appears on login page
   - Logo appears in print formats
   - Favicon is updated to workshop logo

3. 🎨 Theme Application:
   - Primary color applied to buttons, links, highlights
   - Secondary color applied to backgrounds, cards
   - Dark mode toggle affects entire interface
   - CSS custom properties updated in real-time

4. 🖥️ JavaScript API:
   - window.workshop_branding_service: Main service instance
   - window.refresh_workshop_branding(): Reload branding
   - window.update_workshop_branding(branding): Update branding
   - Event: 'workshop:branding_updated' fired on changes

5. 🔧 Developer Usage:
   - CSS variables: --workshop-primary-color, --workshop-secondary-color
   - Logo URL: --workshop-logo-url
   - RGB values: --workshop-primary-rgb, --workshop-secondary-rgb
   - Color variations: --workshop-primary-light, --workshop-primary-dark

6. 📱 Mobile & Responsive:
   - Logo scales appropriately on mobile devices
   - Touch-friendly branding controls
   - RTL support for Arabic interface
   - Accessibility features included
"""

    print(instructions)


def main():
    """Main test function"""

    print("🚀 Universal Workshop Dynamic Logo Injection Test")
    print("=" * 60)

    # Test 1: Create workshop with branding
    workshop = create_test_workshop_with_branding()

    # Test 2: Test branding API
    branding = test_branding_api()

    # Test 3: Check injection readiness
    ready = test_logo_injection_readiness()

    # Test 4: Generate usage instructions
    generate_usage_instructions()

    print("\n" + "=" * 60)
    print("🎯 Dynamic Logo Injection Test Summary:")
    print(f"   - Workshop Created: {'✅' if workshop else '❌'}")
    print(f"   - Branding API: {'✅' if branding else '❌'}")
    print(f"   - Injection Ready: {'✅' if ready else '❌'}")

    if workshop and branding and ready:
        print("\n🎉 Dynamic Logo Injection System is READY!")
        print("   Navigate to ERPNext interface to see logo injection in action")
    else:
        print("\n⚠️  Some components need attention before system is fully ready")

    return workshop and branding and ready


if __name__ == "__main__":
    # This script should be run in Frappe context
    # Example: bench --site universal.local console < test_logo_injection.py
    main()
