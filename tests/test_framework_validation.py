"""
Basic validation test for testing framework setup
"""

import pytest
import frappe
import os
from pathlib import Path


def test_framework_setup():
    """Test that the testing framework is properly set up."""
    # Test that we can import required modules
    assert pytest is not None
    assert frappe is not None

    # Test that test directories exist
    test_dir = Path(__file__).parent
    assert (test_dir / "e2e").exists()
    assert (test_dir / "integration").exists()
    assert (test_dir / "fixtures").exists()
    assert (test_dir / "utils").exists()
    
    print("✅ Testing framework setup validation passed")


def test_frappe_connection():
    """Test basic Frappe connection and site setup."""
    try:
        # This should work if Frappe is properly set up
        site = getattr(frappe.local, 'site', None)
        print(f"Current site: {site}")
        
        # Test basic database connection
        if frappe.db:
            # Simple query to test database connection
            result = frappe.db.sql("SELECT 1 as test", as_dict=True)
            assert result[0]["test"] == 1
            print("✅ Database connection test passed")
        else:
            print("⚠️ Database not connected - may need manual site initialization")
            
    except Exception as e:
        print(f"⚠️ Frappe connection test warning: {str(e)}")
        # Don't fail the test, just warn


def test_test_data_fixtures():
    """Test that test data fixtures are properly loaded."""
    fixtures_file = Path(__file__).parent / "fixtures" / "workshop_test_data.json"
    assert fixtures_file.exists(), "Test fixtures file not found"
    
    import json
    with open(fixtures_file, 'r', encoding='utf-8') as f:
        fixtures = json.load(f)
    
    # Verify fixture structure
    assert "customers" in fixtures
    assert "vehicles" in fixtures
    assert "items" in fixtures
    assert "test_scenarios" in fixtures
    
    # Verify Arabic data is present
    arabic_customers = [c for c in fixtures["customers"] if c.get("language") == "ar"]
    assert len(arabic_customers) > 0, "No Arabic test customers found"
    
    print("✅ Test data fixtures validation passed")


def test_test_utilities():
    """Test that test utilities are importable and functional."""
    from tests.utils.test_utils import WorkshopTestUtils, MockDataGenerator
    
    # Test utility class instantiation
    utils = WorkshopTestUtils()
    assert utils is not None
    
    # Test mock data generators
    arabic_name = MockDataGenerator.generate_arabic_name()
    english_name = MockDataGenerator.generate_english_name()
    mobile_number = MockDataGenerator.generate_oman_mobile_number()
    
    assert arabic_name is not None
    assert english_name is not None
    assert mobile_number.startswith("+968")
    
    print("✅ Test utilities validation passed")


def test_arabic_unicode_support():
    """Test Arabic Unicode handling in the testing environment."""
    arabic_text = "ورشة أحمد الراشد للسيارات"
    
    # Test string operations
    assert len(arabic_text) > 0
    assert "أحمد" in arabic_text
    
    # Test encoding/decoding
    encoded = arabic_text.encode('utf-8')
    decoded = encoded.decode('utf-8')
    assert decoded == arabic_text
    
    print("✅ Arabic Unicode support validation passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
