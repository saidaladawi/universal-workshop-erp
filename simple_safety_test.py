#!/usr/bin/env python3

import frappe
import json
import sys
from datetime import datetime

def run_baseline_test():
    """Run simplified baseline safety test"""
    print("🧪 Refactoring Safety Baseline Test")
    print("=" * 40)
    
    results = []
    
    # Test 1: Database connectivity
    try:
        frappe.db.sql("SELECT 1")
        results.append(("Database Connectivity", True, "Connected successfully"))
        print("✅ PASS: Database Connectivity")
    except Exception as e:
        results.append(("Database Connectivity", False, str(e)))
        print(f"❌ FAIL: Database Connectivity - {e}")
    
    # Test 2: DocType accessibility
    try:
        meta = frappe.get_meta("User")
        if meta:
            results.append(("DocType Operations", True, "User DocType accessible"))
            print("✅ PASS: DocType Operations")
        else:
            results.append(("DocType Operations", False, "Cannot load User DocType"))
            print("❌ FAIL: DocType Operations - Cannot load User DocType")
    except Exception as e:
        results.append(("DocType Operations", False, str(e)))
        print(f"❌ FAIL: DocType Operations - {e}")
    
    # Test 3: Import integrity
    try:
        import universal_workshop
        results.append(("Import Integrity", True, "Universal Workshop module imported"))
        print("✅ PASS: Import Integrity")
    except Exception as e:
        results.append(("Import Integrity", False, str(e)))
        print(f"❌ FAIL: Import Integrity - {e}")
    
    # Test 4: System configuration
    try:
        site_config = frappe.get_site_config()
        db_name = site_config.get("db_name")
        if db_name:
            results.append(("System Configuration", True, f"Database: {db_name}"))
            print("✅ PASS: System Configuration")
        else:
            results.append(("System Configuration", False, "No database name in config"))
            print("❌ FAIL: System Configuration - No database name in config")
    except Exception as e:
        results.append(("System Configuration", False, str(e)))
        print(f"❌ FAIL: System Configuration - {e}")
    
    # Test 5: Universal Workshop specific test
    try:
        # Try to access universal workshop tables
        tables = frappe.db.sql("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name LIKE 'tab%Workshop%'
        """, (frappe.db.get_database_name(),), as_dict=True)
        
        if tables:
            results.append(("Universal Workshop Tables", True, f"Found {len(tables)} workshop tables"))
            print(f"✅ PASS: Universal Workshop Tables - Found {len(tables)} tables")
        else:
            results.append(("Universal Workshop Tables", False, "No workshop tables found"))
            print("❌ FAIL: Universal Workshop Tables - No workshop tables found")
    except Exception as e:
        results.append(("Universal Workshop Tables", False, str(e)))
        print(f"❌ FAIL: Universal Workshop Tables - {e}")
    
    # Summary
    print("=" * 40)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"📊 Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    print(f"⏱️ Time: {datetime.now()}")
    
    # Save detailed results
    results_data = {
        "summary": {
            "passed": passed,
            "total": total,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        },
        "tests": [
            {"name": name, "passed": p, "details": d} 
            for name, p, d in results
        ]
    }
    
    try:
        with open("refactoring_safety_baseline.json", "w") as f:
            json.dump(results_data, f, indent=2)
        print("📁 Results saved to: refactoring_safety_baseline.json")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    # Determine success
    if passed >= total * 0.8:  # 80% success threshold
        print("✅ BASELINE SAFETY TEST PASSED - Ready for refactoring")
        return True
    else:
        print("❌ BASELINE SAFETY TEST FAILED - NOT ready for refactoring")
        return False

if __name__ == "__main__":
    success = run_baseline_test()
    sys.exit(0 if success else 1)