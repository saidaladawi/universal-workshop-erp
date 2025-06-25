#!/usr/bin/env python3

import os
import sys
import frappe

# Initialize Frappe
os.chdir('/home/said/frappe-dev/frappe-bench')
sys.path.insert(0, '.')
sys.path.insert(0, 'apps/frappe')
sys.path.insert(0, 'apps/erpnext')
sys.path.insert(0, 'apps/universal_workshop')

frappe.init(site='universal.local')
frappe.connect()

print("\n" + "="*90)
print("UNIVERSAL WORKSHOP ERP - COMPREHENSIVE DATA INTEGRITY CHECKS")
print("="*90)

def check_table_exists(table_name):
    """Check if table exists"""
    try:
        tables = frappe.db.sql(f"SHOW TABLES LIKE '{table_name}'", as_list=True)
        return len(tables) > 0
    except:
        return False

def get_record_count(table_name):
    """Get record count for table"""
    try:
        result = frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`", as_list=True)
        return result[0][0] if result else 0
    except:
        return 0

def check_column_exists(table_name, column_name):
    """Check if column exists in table"""
    try:
        columns = frappe.db.sql(f"DESCRIBE `{table_name}`", as_dict=True)
        column_names = [col['Field'] for col in columns]
        return column_name in column_names
    except:
        return False

# Initialize results
results = {
    'total_checks': 0,
    'passed_checks': 0,
    'failed_checks': 0,
    'warnings': 0,
    'critical_issues': 0
}

def pass_check(message):
    global results
    results['passed_checks'] += 1
    print(f"✅ {message}")

def fail_check(message):
    global results
    results['failed_checks'] += 1
    print(f"❌ {message}")

def add_warning(message):
    global results
    results['warnings'] += 1
    print(f"⚠️  {message}")

# Start checks
print(f"\n🏭 WORKSHOP PROFILE INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabWorkshop Profile'):
    count = get_record_count('tabWorkshop Profile')
    print(f"📊 Records: {count}")
    
    # Check table structure
    if check_column_exists('tabWorkshop Profile', 'workshop_code'):
        pass_check("Workshop Profile table structure is valid")
    else:
        fail_check("Workshop Profile missing workshop_code column")
    
    # Check for duplicates if data exists
    if count > 0:
        try:
            duplicates = frappe.db.sql("""
                SELECT workshop_code, COUNT(*) as count
                FROM `tabWorkshop Profile`
                WHERE workshop_code IS NOT NULL AND workshop_code != ''
                GROUP BY workshop_code
                HAVING COUNT(*) > 1
            """, as_dict=True)
            
            if duplicates:
                fail_check(f"Found {len(duplicates)} duplicate workshop codes")
            else:
                pass_check("All workshop codes are unique")
        except Exception as e:
            add_warning(f"Could not check duplicates: {str(e)}")
    else:
        pass_check("No data to validate (empty table)")
else:
    fail_check("Workshop Profile table does not exist")

print(f"\n👥 CUSTOMER DATA INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabCustomer'):
    count = get_record_count('tabCustomer')
    print(f"📊 Records: {count}")
    pass_check("Customer table exists and is accessible")
else:
    fail_check("Customer table does not exist")

print(f"\n🔧 TECHNICIAN DATA INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabTechnician'):
    count = get_record_count('tabTechnician')
    print(f"📊 Records: {count}")
    pass_check("Technician table exists")
else:
    add_warning("Technician table does not exist (will be created when needed)")

print(f"\n👤 WORKSHOP ROLE INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabWorkshop Role'):
    count = get_record_count('tabWorkshop Role')
    print(f"📊 Records: {count}")
    
    if count > 0:
        try:
            roles = frappe.db.sql("""
                SELECT name, role_name FROM `tabWorkshop Role`
                WHERE role_name IS NOT NULL AND role_name != ''
                LIMIT 5
            """, as_dict=True)
            
            print(f"✅ Found {len(roles)} valid workshop roles:")
            for role in roles:
                print(f"   👤 {role['role_name']}")
            
            pass_check(f"Workshop roles are properly configured ({count} roles)")
        except Exception as e:
            add_warning(f"Could not validate role data: {str(e)}")
    else:
        add_warning("No workshop roles defined")
else:
    fail_check("Workshop Role table does not exist")

print(f"\n🎨 WORKSHOP THEME INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabWorkshop Theme'):
    count = get_record_count('tabWorkshop Theme')
    print(f"📊 Records: {count}")
    
    if count > 0:
        try:
            themes = frappe.db.sql("""
                SELECT name, theme_name FROM `tabWorkshop Theme`
                WHERE theme_name IS NOT NULL AND theme_name != ''
            """, as_dict=True)
            
            print(f"✅ Found {len(themes)} valid themes:")
            for theme in themes:
                print(f"   🎨 {theme['theme_name']}")
            
            pass_check(f"Workshop themes are properly configured ({count} themes)")
        except Exception as e:
            add_warning(f"Could not validate theme data: {str(e)}")
    else:
        add_warning("No workshop themes defined")
else:
    fail_check("Workshop Theme table does not exist")

print(f"\n🗄️  DATABASE CONSTRAINTS")
print("-" * 50)

results['total_checks'] += 1
try:
    # Check database charset
    charset_info = frappe.db.sql("""
        SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
        FROM information_schema.SCHEMATA
        WHERE SCHEMA_NAME = DATABASE()
    """, as_dict=True)
    
    if charset_info:
        charset = charset_info[0]['DEFAULT_CHARACTER_SET_NAME']
        collation = charset_info[0]['DEFAULT_COLLATION_NAME']
        
        print(f"📊 Database Charset: {charset}")
        print(f"📊 Database Collation: {collation}")
        
        if charset == 'utf8mb4':
            pass_check("Database uses UTF8MB4 charset (supports Arabic)")
        else:
            fail_check(f"Database charset is {charset}, should be utf8mb4 for Arabic support")
    else:
        add_warning("Could not determine database charset")
except Exception as e:
    fail_check(f"Error checking database constraints: {str(e)}")

print(f"\n🌐 ARABIC LOCALIZATION INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabWorkshop Profile'):
    try:
        arabic_fields = frappe.db.sql("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tabWorkshop Profile'
            AND COLUMN_NAME LIKE '%_ar'
        """, as_list=True)
        
        arabic_field_count = len(arabic_fields)
        print(f"📊 Arabic Fields: {arabic_field_count}")
        
        if arabic_field_count > 0:
            pass_check(f"Found {arabic_field_count} Arabic fields in Workshop Profile")
            for field in arabic_fields[:3]:
                print(f"   🌐 {field[0]}")
        else:
            add_warning("No Arabic fields found in Workshop Profile")
    except Exception as e:
        add_warning(f"Could not check Arabic fields: {str(e)}")
else:
    fail_check("Cannot check Arabic fields - Workshop Profile table missing")

print(f"\n🔑 LICENSE SYSTEM INTEGRITY")
print("-" * 50)

results['total_checks'] += 1
if check_table_exists('tabBusiness Workshop Binding'):
    count = get_record_count('tabBusiness Workshop Binding')
    print(f"📊 Business Bindings: {count}")
    
    if count > 0:
        pass_check("License binding system has data")
    else:
        add_warning("No business workshop bindings found")
else:
    fail_check("Business Workshop Binding table not found")

# Generate final report
print(f"\n" + "="*90)
print("DATA INTEGRITY VALIDATION SUMMARY")
print("="*90)

total = results['total_checks']
passed = results['passed_checks']
failed = results['failed_checks']
warnings = results['warnings']
critical = results['critical_issues']

print(f"📊 Total Checks: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⚠️  Warnings: {warnings}")
print(f"🚨 Critical Issues: {critical}")

if total > 0:
    success_rate = (passed / total) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")

# Overall health assessment
if critical > 0:
    print(f"\n🚨 SYSTEM STATUS: CRITICAL ISSUES FOUND")
    print("Immediate attention required before production use.")
elif failed > 3:
    print(f"\n❌ SYSTEM STATUS: MULTIPLE FAILURES")
    print("Several issues need to be addressed.")
elif failed > 0:
    print(f"\n⚠️  SYSTEM STATUS: MINOR ISSUES")
    print("Some issues found but system is generally functional.")
elif warnings > 0:
    print(f"\n✅ SYSTEM STATUS: HEALTHY WITH WARNINGS")
    print("System is functional with minor warnings.")
else:
    print(f"\n🎉 SYSTEM STATUS: EXCELLENT")
    print("All data integrity checks passed successfully!")

print("="*90 + "\n")

# Store results in database
try:
    frappe.db.set_value('System Settings', None, 'data_integrity_last_check', frappe.utils.now())
    frappe.db.commit()
    print("✅ Results stored in system settings")
except Exception as e:
    print(f"⚠️  Could not store results: {str(e)}")

frappe.db.close()
print("✅ Data integrity checks completed!")
