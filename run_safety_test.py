import frappe
import json

def main():
    frappe.init(site="universal.local")
    frappe.connect()
    
    print("🧪 Refactoring Safety Baseline Test")
    print("=" * 40)
    
    tests = []
    
    # Test 1: Database connectivity
    try:
        frappe.db.sql("SELECT 1")
        tests.append(("Database", True, "Connected successfully"))
        print("✅ Database: Connected successfully")
    except Exception as e:
        tests.append(("Database", False, str(e)))
        print(f"❌ Database: {e}")
    
    # Test 2: Universal Workshop import
    try:
        import universal_workshop
        tests.append(("Import", True, "Universal Workshop accessible"))
        print("✅ Import: Universal Workshop accessible")
    except Exception as e:
        tests.append(("Import", False, str(e)))
        print(f"❌ Import: {e}")
    
    # Test 3: DocType operations
    try:
        meta = frappe.get_meta("User")
        tests.append(("DocType", True, "User meta accessible"))
        print("✅ DocType: User meta accessible")
    except Exception as e:
        tests.append(("DocType", False, str(e)))
        print(f"❌ DocType: {e}")
    
    # Test 4: Workshop tables
    try:
        tables = frappe.db.sql("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name LIKE 'tab%Workshop%'
        """, (frappe.db.get_database_name(),), as_dict=True)
        
        count = tables[0]["count"] if tables else 0
        if count > 0:
            tests.append(("Workshop Tables", True, f"Found {count} tables"))
            print(f"✅ Workshop Tables: Found {count} tables")
        else:
            tests.append(("Workshop Tables", False, "No workshop tables found"))
            print("❌ Workshop Tables: No workshop tables found")
    except Exception as e:
        tests.append(("Workshop Tables", False, str(e)))
        print(f"❌ Workshop Tables: {e}")
    
    # Test 5: Configuration
    try:
        config = frappe.get_site_config()
        db_name = config.get("db_name")
        if db_name:
            tests.append(("Configuration", True, f"Database: {db_name}"))
            print(f"✅ Configuration: Database {db_name}")
        else:
            tests.append(("Configuration", False, "No database name"))
            print("❌ Configuration: No database name")
    except Exception as e:
        tests.append(("Configuration", False, str(e)))
        print(f"❌ Configuration: {e}")
    
    # Summary
    passed = sum(1 for _, success, _ in tests if success)
    total = len(tests)
    success_rate = (passed / total) * 100
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    # Save results
    results = {
        "summary": {
            "passed": passed,
            "total": total,
            "success_rate": success_rate,
            "timestamp": frappe.utils.now()
        },
        "tests": [{"name": name, "passed": p, "details": d} for name, p, d in tests]
    }
    
    try:
        with open("refactoring_safety_baseline.json", "w") as f:
            json.dump(results, f, indent=2)
        print("📁 Results saved to: refactoring_safety_baseline.json")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    # Determine overall success
    threshold = 0.8  # 80%
    if success_rate >= threshold * 100:
        print("✅ BASELINE SAFETY TEST PASSED - Ready for refactoring")
        return True
    else:
        print(f"❌ BASELINE SAFETY TEST FAILED - Success rate {success_rate:.1f}% below {threshold*100:.0f}%")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(2)
    finally:
        if frappe.local.db:
            frappe.destroy()