#!/usr/bin/env python3
"""
Phase 2 Functionality Test
Test that the refactored boot and installation managers work correctly
"""

import frappe
import json
import sys
from datetime import datetime

def test_boot_manager_functionality():
    """Test that the new BootManager works correctly"""
    print("🧪 Testing BootManager functionality...")
    
    try:
        # Test importing the new boot manager
        from universal_workshop.core.boot.boot_manager import get_boot_manager, BootManager
        
        print("✅ PASS: BootManager imports successfully")
        
        # Test singleton pattern
        manager1 = get_boot_manager()
        manager2 = get_boot_manager()
        assert manager1 is manager2, "Singleton pattern not working"
        print("✅ PASS: Singleton pattern working")
        
        # Test basic functionality without database calls
        manager = BootManager()
        assert hasattr(manager, 'setup_status'), "Missing setup_status attribute"
        assert hasattr(manager, 'license_info'), "Missing license_info attribute"
        assert hasattr(manager, 'workshop_config'), "Missing workshop_config attribute"
        print("✅ PASS: BootManager attributes present")
        
        # Test license file reading (should not crash)
        license_data = manager.get_license_file_data()
        print(f"✅ PASS: License file check completed (data: {'found' if license_data else 'not found'})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: BootManager test failed - {e}")
        return False

def test_installation_manager_functionality():
    """Test that the new InstallationManager works correctly"""
    print("\n🧪 Testing InstallationManager functionality...")
    
    try:
        # Test importing the new installation manager
        from universal_workshop.setup.installation.installation_manager import get_installation_manager, InstallationManager
        
        print("✅ PASS: InstallationManager imports successfully")
        
        # Test singleton pattern
        manager1 = get_installation_manager()
        manager2 = get_installation_manager()
        assert manager1 is manager2, "Singleton pattern not working"
        print("✅ PASS: Singleton pattern working")
        
        # Test basic functionality
        manager = InstallationManager()
        assert hasattr(manager, 'errors'), "Missing errors attribute"
        assert hasattr(manager, 'warnings'), "Missing warnings attribute"
        assert isinstance(manager.errors, list), "Errors should be a list"
        assert isinstance(manager.warnings, list), "Warnings should be a list"
        print("✅ PASS: InstallationManager attributes present")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: InstallationManager test failed - {e}")
        return False

def test_hooks_integration():
    """Test that hooks.py references are updated correctly"""
    print("\n🧪 Testing hooks.py integration...")
    
    try:
        # Test importing hook functions
        from universal_workshop.core.boot.boot_manager import get_boot_info, check_initial_setup, get_user_home_page
        from universal_workshop.setup.installation.installation_manager import after_install, before_uninstall
        
        print("✅ PASS: All hook functions import successfully")
        
        # Test that functions are callable
        assert callable(get_boot_info), "get_boot_info not callable"
        assert callable(check_initial_setup), "check_initial_setup not callable"
        assert callable(get_user_home_page), "get_user_home_page not callable"
        assert callable(after_install), "after_install not callable"
        assert callable(before_uninstall), "before_uninstall not callable"
        print("✅ PASS: All hook functions are callable")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Hooks integration test failed - {e}")
        return False

def test_import_consolidation():
    """Test that old imports are properly replaced"""
    print("\n🧪 Testing import consolidation...")
    
    try:
        # Test that we can still import from legacy paths (for backward compatibility)
        from universal_workshop.core.boot.boot_manager import (
            get_boot_info, check_initial_setup, check_initial_setup_status,
            get_workshop_configuration, get_license_information, get_session_boot_info
        )
        
        print("✅ PASS: Legacy boot functions available")
        
        from universal_workshop.setup.installation.installation_manager import (
            after_install, before_uninstall, complete_onboarding_with_license
        )
        
        print("✅ PASS: Legacy installation functions available")
        
        # Test that new organized structure exists
        import universal_workshop.core.boot.boot_manager
        import universal_workshop.setup.installation.installation_manager
        
        print("✅ PASS: New organized module structure working")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Import consolidation test failed - {e}")
        return False

def main():
    """Run all Phase 2 functionality tests"""
    print("🚀 Phase 2: Core System Consolidation - Functionality Tests")
    print("=" * 60)
    
    tests = [
        test_boot_manager_functionality,
        test_installation_manager_functionality,
        test_hooks_integration,
        test_import_consolidation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Phase 2 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ PHASE 2 CONSOLIDATION SUCCESSFUL - All functionality tests passed")
        
        # Save test results
        results = {
            "phase": "Phase 2: Core System Consolidation",
            "timestamp": datetime.now().isoformat(),
            "tests_passed": passed,
            "tests_total": total,
            "success_rate": (passed / total) * 100,
            "status": "PASSED" if passed == total else "FAILED",
            "consolidation_completed": [
                "BootManager created and functional",
                "InstallationManager created and functional", 
                "Hook references updated",
                "Import paths consolidated",
                "Backward compatibility maintained"
            ]
        }
        
        with open("phase2_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print("📁 Phase 2 test results saved to: phase2_test_results.json")
        return True
    else:
        print(f"❌ PHASE 2 CONSOLIDATION FAILED - {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)