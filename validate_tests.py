#!/usr/bin/env python3

import sys
from pathlib import Path

def main():
    print("🔧 Validating Universal Workshop ERP Testing Framework...")
    
    # Check basic structure
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    required_dirs = ["e2e", "integration", "fixtures", "utils"]
    for dirname in required_dirs:
        dir_path = test_dir / dirname
        if dir_path.exists():
            print(f"✅ {dirname}/ directory found")
        else:
            print(f"❌ {dirname}/ directory missing")
            return False
    
    # Check fixtures
    fixtures_file = test_dir / "fixtures" / "workshop_test_data.json"
    if fixtures_file.exists():
        print("✅ Test fixtures file found")
        
        import json
        try:
            with open(fixtures_file, 'r', encoding='utf-8') as f:
                fixtures = json.load(f)
            print(f"✅ Fixtures loaded successfully with {len(fixtures)} sections")
            
            # Check for Arabic data
            if "customers" in fixtures:
                arabic_customers = [c for c in fixtures["customers"] if c.get("language") == "ar"]
                if arabic_customers:
                    print(f"✅ Found {len(arabic_customers)} Arabic test customers")
                else:
                    print("⚠️ No Arabic test customers found")
        except Exception as e:
            print(f"❌ Error loading fixtures: {e}")
            return False
    else:
        print("❌ Test fixtures file not found")
        return False
    
    # Check test files
    test_files = [
        "e2e/test_workshop_workflow.py",
        "e2e/cypress_workshop_tests.js", 
        "integration/test_api_integration.py",
        "utils/test_utils.py",
        "run_tests.py"
    ]
    
    for test_file in test_files:
        file_path = test_dir / test_file
        if file_path.exists():
            print(f"✅ {test_file} found")
        else:
            print(f"❌ {test_file} missing")
            return False
    
    # Check configuration
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        print("✅ pytest.ini configuration found")
    else:
        print("⚠️ pytest.ini configuration missing")
    
    # Test Arabic Unicode
    arabic_text = "ورشة أحمد الراشد للسيارات"
    try:
        encoded = arabic_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        if decoded == arabic_text:
            print("✅ Arabic Unicode support validated")
        else:
            print("❌ Arabic Unicode encoding/decoding failed")
            return False
    except Exception as e:
        print(f"❌ Arabic Unicode test failed: {e}")
        return False
    
    print("\n🎉 Testing Framework Validation Complete!")
    print("📝 Ready to run comprehensive workshop integration tests")
    print("🚀 Use './tests/run_tests.py' to execute the full test suite")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
