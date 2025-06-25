import frappe

print("\n" + "="*70)
print("UNIVERSAL WORKSHOP ERP - DATA INTEGRITY CHECKS")
print("="*70)

# Initialize results
results = {'passed': 0, 'failed': 0, 'warnings': 0}

def check_table(table_name, description):
    try:
        tables = frappe.db.sql(f"SHOW TABLES LIKE '{table_name}'", as_list=True)
        if tables:
            count = frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`")[0][0]
            print(f"✅ {description}: EXISTS ({count} records)")
            results['passed'] += 1
            return True
        else:
            print(f"❌ {description}: NOT FOUND")
            results['failed'] += 1
            return False
    except Exception as e:
        print(f"⚠️  {description}: ERROR - {str(e)}")
        results['warnings'] += 1
        return False

# Core table checks
print(f"\n📋 CORE TABLES")
print("-" * 40)
check_table('tabWorkshop Profile', 'Workshop Profile')
check_table('tabCustomer', 'Customer')
check_table('tabTechnician', 'Technician')
check_table('tabWorkshop Role', 'Workshop Role')
check_table('tabWorkshop Theme', 'Workshop Theme')
check_table('tabBusiness Workshop Binding', 'Business Workshop Binding')

# Database charset check
print(f"\n🌐 DATABASE CONFIGURATION")
print("-" * 40)
try:
    charset_info = frappe.db.sql("""
        SELECT DEFAULT_CHARACTER_SET_NAME as charset, DEFAULT_COLLATION_NAME as collation
        FROM information_schema.SCHEMATA
        WHERE SCHEMA_NAME = DATABASE()
    """, as_dict=True)
    
    if charset_info:
        charset = charset_info[0]['charset']
        print(f"✅ Database Charset: {charset}")
        if charset == 'utf8mb4':
            print("✅ UTF8MB4 supports Arabic characters")
            results['passed'] += 1
        else:
            print("⚠️  Non-UTF8MB4 charset may not support Arabic")
            results['warnings'] += 1
    else:
        print("❌ Could not determine database charset")
        results['failed'] += 1
except Exception as e:
    print(f"❌ Database charset check failed: {str(e)}")
    results['failed'] += 1

# Workshop data validation
print(f"\n🏭 WORKSHOP DATA VALIDATION")
print("-" * 40)
try:
    if frappe.db.sql("SHOW TABLES LIKE 'tabWorkshop Profile'"):
        # Check for Arabic fields
        arabic_fields = frappe.db.sql("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tabWorkshop Profile'
            AND COLUMN_NAME LIKE '%_ar'
        """, as_list=True)
        
        if arabic_fields:
            print(f"✅ Found {len(arabic_fields)} Arabic fields")
            for field in arabic_fields[:3]:
                print(f"   🌐 {field[0]}")
            results['passed'] += 1
        else:
            print("⚠️  No Arabic fields found")
            results['warnings'] += 1
    else:
        print("❌ Workshop Profile table not found")
        results['failed'] += 1
except Exception as e:
    print(f"❌ Arabic field check failed: {str(e)}")
    results['failed'] += 1

# Summary
print(f"\n" + "="*70)
print("INTEGRITY CHECK SUMMARY")
print("="*70)
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"⚠️  Warnings: {results['warnings']}")

total = results['passed'] + results['failed'] + results['warnings']
if total > 0:
    success_rate = (results['passed'] / total) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")

if results['failed'] == 0 and results['warnings'] <= 2:
    print(f"\n🎉 SYSTEM STATUS: HEALTHY")
elif results['failed'] <= 2:
    print(f"\n⚠️  SYSTEM STATUS: MINOR ISSUES")
else:
    print(f"\n❌ SYSTEM STATUS: NEEDS ATTENTION")

print("="*70)
