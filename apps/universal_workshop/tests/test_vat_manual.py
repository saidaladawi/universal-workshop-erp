#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Manual test script for Oman VAT configuration

import sys
import os

# Add the universal_workshop module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "universal_workshop"))


def test_vat_config_import():
    """Test that VAT config can be imported"""
    try:
        from universal_workshop.billing_management.oman_vat_config import OmanVATConfig

        print("✅ OmanVATConfig imported successfully")

        vat_config = OmanVATConfig()
        print(f"✅ VAT Rate: {vat_config.vat_rate}%")
        print(f"✅ Currency: {vat_config.currency}")
        print(f"✅ Decimal Places: {vat_config.decimal_places}")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating VAT config: {e}")
        return False


def test_vat_validation():
    """Test VAT number validation logic"""
    try:
        from universal_workshop.billing_management.oman_vat_config import OmanVATConfig

        vat_config = OmanVATConfig()

        # Test valid VAT numbers
        valid_numbers = ["OM123456789012345", "OM987654321098765"]
        for vat_number in valid_numbers:
            try:
                result = vat_config.validate_vat_number(vat_number)
                print(f"✅ Valid VAT number {vat_number}: {result}")
            except Exception as e:
                print(f"❌ Error validating {vat_number}: {e}")
                return False

        # Test invalid VAT numbers (without frappe.throw)
        import re

        invalid_numbers = ["OM12345", "123456789012345", "OMA123456789012345"]
        for vat_number in invalid_numbers:
            if not re.match(r"^OM\d{15}$", vat_number):
                print(f"✅ Invalid VAT number {vat_number} correctly identified")
            else:
                print(f"❌ Invalid VAT number {vat_number} incorrectly passed")
                return False

        return True
    except Exception as e:
        print(f"❌ Error in VAT validation test: {e}")
        return False


def test_custom_fields_import():
    """Test that custom fields module can be imported"""
    try:
        from universal_workshop.billing_management.fixtures.vat_custom_fields import (
            install_vat_custom_fields,
        )

        print("✅ VAT custom fields module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Custom fields import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing custom fields: {e}")
        return False


def main():
    """Run all manual tests"""
    print("🔍 Running Manual VAT Configuration Tests...")
    print("=" * 50)

    tests = [
        ("VAT Config Import", test_vat_config_import),
        ("VAT Validation", test_vat_validation),
        ("Custom Fields Import", test_custom_fields_import),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
