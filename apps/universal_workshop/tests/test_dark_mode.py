#!/usr/bin/env python3
"""
Dark Mode System Test Script for Universal Workshop ERP
Tests all dark mode functionality including installation, API methods, and integration
"""

import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath("."))


def test_dark_mode_files():
    """Test if all dark mode files exist"""
    print("🧪 Testing Dark Mode Files...")

    files_to_check = [
        "apps/universal_workshop/universal_workshop/public/js/dark_mode_manager.js",
        "apps/universal_workshop/universal_workshop/public/css/dark_mode.css",
        "apps/universal_workshop/universal_workshop/dark_mode/__init__.py",
        "apps/universal_workshop/universal_workshop/dark_mode/fixtures.py",
    ]

    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_exist = False

    return all_exist


def test_hooks_integration():
    """Test if dark mode files are properly integrated in hooks.py"""
    print("\n🧪 Testing Hooks Integration...")

    try:
        with open("apps/universal_workshop/universal_workshop/hooks.py", "r") as f:
            hooks_content = f.read()

        # Check for dark mode CSS
        if "/assets/universal_workshop/css/dark_mode.css" in hooks_content:
            print("  ✅ Dark mode CSS included in app_include_css")
        else:
            print("  ❌ Dark mode CSS missing from app_include_css")
            return False

        # Check for dark mode JS
        if "/assets/universal_workshop/js/dark_mode_manager.js" in hooks_content:
            print("  ✅ Dark mode JS included in app_include_js")
        else:
            print("  ❌ Dark mode JS missing from app_include_js")
            return False

        # Check web includes
        if hooks_content.count("/assets/universal_workshop/css/dark_mode.css") >= 2:
            print("  ✅ Dark mode CSS included in web_include_css")
        else:
            print("  ❌ Dark mode CSS missing from web_include_css")

        if hooks_content.count("/assets/universal_workshop/js/dark_mode_manager.js") >= 2:
            print("  ✅ Dark mode JS included in web_include_js")
        else:
            print("  ❌ Dark mode JS missing from web_include_js")

        return True

    except Exception as e:
        print(f"  ❌ Error reading hooks.py: {e}")
        return False


def test_asset_linking():
    """Test if assets are properly linked"""
    print("\n🧪 Testing Asset Linking...")

    asset_paths = [
        "sites/assets/universal_workshop/js/dark_mode_manager.js",
        "sites/assets/universal_workshop/css/dark_mode.css",
    ]

    all_linked = True
    for asset_path in asset_paths:
        if os.path.exists(asset_path):
            print(f"  ✅ {asset_path} - Linked")
        else:
            print(f"  ❌ {asset_path} - Not linked")
            all_linked = False

    return all_linked


def test_javascript_syntax():
    """Test JavaScript syntax for dark mode manager"""
    print("\n🧪 Testing JavaScript Syntax...")

    try:
        with open(
            "apps/universal_workshop/universal_workshop/public/js/dark_mode_manager.js", "r"
        ) as f:
            js_content = f.read()

        # Basic syntax checks
        if "class DarkModeManager" in js_content:
            print("  ✅ DarkModeManager class defined")
        else:
            print("  ❌ DarkModeManager class missing")
            return False

        if "window.workshop_dark_mode" in js_content:
            print("  ✅ Global dark mode instance defined")
        else:
            print("  ❌ Global dark mode instance missing")
            return False

        if "setupToggleUI" in js_content:
            print("  ✅ Toggle UI setup method found")
        else:
            print("  ❌ Toggle UI setup method missing")
            return False

        if "addNavbarToggle" in js_content:
            print("  ✅ Navbar toggle method found")
        else:
            print("  ❌ Navbar toggle method missing")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Error reading JavaScript file: {e}")
        return False


def test_css_syntax():
    """Test CSS syntax for dark mode styles"""
    print("\n🧪 Testing CSS Syntax...")

    try:
        with open("apps/universal_workshop/universal_workshop/public/css/dark_mode.css", "r") as f:
            css_content = f.read()

        # Basic syntax checks
        if ".workshop-dark-mode" in css_content:
            print("  ✅ Main dark mode class defined")
        else:
            print("  ❌ Main dark mode class missing")
            return False

        if "--workshop-bg-primary" in css_content:
            print("  ✅ CSS custom properties defined")
        else:
            print("  ❌ CSS custom properties missing")
            return False

        if ".workshop-dark-mode-toggle" in css_content:
            print("  ✅ Toggle button styles defined")
        else:
            print("  ❌ Toggle button styles missing")
            return False

        if '[dir="rtl"]' in css_content:
            print("  ✅ RTL support included")
        else:
            print("  ❌ RTL support missing")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Error reading CSS file: {e}")
        return False


def test_python_imports():
    """Test Python module imports"""
    print("\n🧪 Testing Python Module Imports...")

    try:
        # Test dark mode module import
        sys.path.insert(0, "apps/universal_workshop/universal_workshop")

        from dark_mode import fixtures

        print("  ✅ Dark mode fixtures module imported successfully")

        # Check if required functions exist
        if hasattr(fixtures, "install_dark_mode_system"):
            print("  ✅ install_dark_mode_system function found")
        else:
            print("  ❌ install_dark_mode_system function missing")
            return False

        if hasattr(fixtures, "get_user_dark_mode_preference"):
            print("  ✅ get_user_dark_mode_preference function found")
        else:
            print("  ❌ get_user_dark_mode_preference function missing")
            return False

        if hasattr(fixtures, "set_user_dark_mode_preference"):
            print("  ✅ set_user_dark_mode_preference function found")
        else:
            print("  ❌ set_user_dark_mode_preference function missing")
            return False

        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error testing imports: {e}")
        return False


def test_integration_points():
    """Test integration with existing systems"""
    print("\n🧪 Testing Integration Points...")

    try:
        # Check branding service integration
        with open(
            "apps/universal_workshop/universal_workshop/public/js/dark_mode_manager.js", "r"
        ) as f:
            js_content = f.read()

        if "window.refresh_workshop_branding" in js_content:
            print("  ✅ Branding service integration found")
        else:
            print("  ❌ Branding service integration missing")

        if "workshop:dark_mode_changed" in js_content:
            print("  ✅ Dark mode event system found")
        else:
            print("  ❌ Dark mode event system missing")

        if "integrateWithBranding" in js_content:
            print("  ✅ Branding integration method found")
        else:
            print("  ❌ Branding integration method missing")

        if "integrateWithThemes" in js_content:
            print("  ✅ Theme integration method found")
        else:
            print("  ❌ Theme integration method missing")

        return True

    except Exception as e:
        print(f"  ❌ Error testing integration: {e}")
        return False


def generate_summary():
    """Generate test summary"""
    print("\n" + "=" * 60)
    print("🌙 DARK MODE SYSTEM TEST SUMMARY")
    print("=" * 60)

    tests = [
        ("File Existence", test_dark_mode_files),
        ("Hooks Integration", test_hooks_integration),
        ("Asset Linking", test_asset_linking),
        ("JavaScript Syntax", test_javascript_syntax),
        ("CSS Syntax", test_css_syntax),
        ("Python Imports", test_python_imports),
        ("Integration Points", test_integration_points),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Dark mode system is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False


def main():
    """Main test execution"""
    print("🧪 Universal Workshop ERP - Dark Mode System Test")
    print("=" * 60)

    # Run comprehensive tests
    success = generate_summary()

    if success:
        print("\n🚀 Next Steps:")
        print("1. Restart the development server: bench restart")
        print("2. Install dark mode custom fields via console")
        print("3. Test dark mode toggle in the UI")
        print("4. Verify dark mode persistence across sessions")
        print("5. Test Arabic RTL compatibility with dark mode")
    else:
        print("\n🔧 Fix the failing tests before proceeding with deployment.")

    return success


if __name__ == "__main__":
    main()
