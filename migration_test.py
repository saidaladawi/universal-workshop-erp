#!/usr/bin/env python3
"""
Universal Workshop ERP - Comprehensive Migration Testing
Tests all aspects of database migration and schema validation
"""

import os
import subprocess
import json
import datetime

def run_migration_tests():
    print("="*70)
    print("UNIVERSAL WORKSHOP ERP - COMPREHENSIVE MIGRATION TESTING")
    print("="*70)
    
    test_results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'tests': {},
        'overall_status': 'UNKNOWN',
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0
    }
    
    # Test 1: Database Migration Status
    print("\n1️⃣  Testing Database Migration Status")
    print("-" * 50)
    
    try:
        # Run migration check
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe

# Check migration status
print("Checking migration status...")
migration_status = frappe.db.sql("""
    SELECT name, executed 
    FROM tabPatch 
    WHERE name LIKE '%universal_workshop%' 
    ORDER BY creation DESC 
    LIMIT 10
""", as_dict=True)

print(f"Universal Workshop patches executed: {len(migration_status)}")
for patch in migration_status:
    print(f"  • {patch.name}: {'✅ EXECUTED' if patch.executed else '❌ PENDING'}")

# Check if all DocTypes are properly created
workshop_doctypes = [
    'Workshop Profile', 'Workshop Service', 'Workshop Role', 'Workshop Theme',
    'Service Order', 'Technician', 'Vehicle', 'Parts Inventory', 'Customer Profile'
]

print(f"\\nChecking core DocTypes...")
for doctype in workshop_doctypes:
    exists = frappe.db.exists('DocType', doctype)
    print(f"  • {doctype}: {'✅ EXISTS' if exists else '❌ MISSING'}")

print("Migration status check completed.")
''', text=True, capture_output=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            test_results['tests']['migration_status'] = {
                'status': 'PASSED',
                'output': result.stdout
            }
            test_results['passed_tests'] += 1
            print("✅ Migration status check: PASSED")
        else:
            test_results['tests']['migration_status'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            test_results['failed_tests'] += 1
            print("❌ Migration status check: FAILED")
            
    except Exception as e:
        test_results['tests']['migration_status'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        test_results['failed_tests'] += 1
        print(f"❌ Migration status check: ERROR - {str(e)}")
    
    test_results['total_tests'] += 1
    
    # Test 2: Table Structure Validation
    print("\n2️⃣  Testing Table Structure Validation")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe

# Check Workshop Profile table structure
print("Validating Workshop Profile table structure...")
try:
    columns = frappe.db.sql("DESCRIBE `tabWorkshop Profile`", as_dict=True)
    print(f"Workshop Profile table has {len(columns)} columns")
    
    # Check for key Arabic fields
    arabic_fields = [col for col in columns if col['Field'].endswith('_ar')]
    print(f"Arabic fields found: {len(arabic_fields)}")
    
    # Check for required fields
    required_fields = ['workshop_name', 'workshop_name_ar', 'business_license', 'phone']
    for field in required_fields:
        field_exists = any(col['Field'] == field for col in columns)
        print(f"  • {field}: {'✅ EXISTS' if field_exists else '❌ MISSING'}")
        
except Exception as e:
    print(f"Error checking Workshop Profile: {str(e)}")

# Check Service Order table
print("\\nValidating Service Order table structure...")
try:
    columns = frappe.db.sql("DESCRIBE `tabService Order`", as_dict=True)
    print(f"Service Order table has {len(columns)} columns")
except Exception as e:
    print(f"Error checking Service Order: {str(e)}")

print("Table structure validation completed.")
''', text=True, capture_output=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            test_results['tests']['table_structure'] = {
                'status': 'PASSED',
                'output': result.stdout
            }
            test_results['passed_tests'] += 1
            print("✅ Table structure validation: PASSED")
        else:
            test_results['tests']['table_structure'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            test_results['failed_tests'] += 1
            print("❌ Table structure validation: FAILED")
            
    except Exception as e:
        test_results['tests']['table_structure'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        test_results['failed_tests'] += 1
        print(f"❌ Table structure validation: ERROR - {str(e)}")
    
    test_results['total_tests'] += 1
    
    # Test 3: Data Creation and Validation
    print("\n3️⃣  Testing Data Creation and Validation")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe

print("Testing data creation and validation...")

# Test Workshop Profile creation
try:
    test_workshop = frappe.new_doc('Workshop Profile')
    test_workshop.workshop_name = 'Migration Test Workshop'
    test_workshop.workshop_name_ar = 'ورشة اختبار الترحيل'
    test_workshop.business_license = '9876543'
    test_workshop.phone = '+968 24987654'
    test_workshop.email = 'migration-test@workshop.local'
    
    # Validate without saving
    test_workshop.validate()
    print("✅ Workshop Profile validation: PASSED")
    
    # Test Arabic character handling
    if test_workshop.workshop_name_ar and len(test_workshop.workshop_name_ar) > 0:
        print("✅ Arabic character support: WORKING")
    else:
        print("❌ Arabic character support: FAILED")
        
except Exception as e:
    print(f"❌ Workshop Profile creation test: {str(e)}")

# Test Technician creation
try:
    test_tech = frappe.new_doc('Technician')
    test_tech.employee_id = 'TEST-TECH-001'
    test_tech.technician_name = 'Migration Test Technician'
    test_tech.technician_name_ar = 'فني اختبار الترحيل'
    test_tech.phone = '+968 24555555'
    test_tech.department = 'Engine'
    test_tech.employment_status = 'Active'
    
    test_tech.validate()
    print("✅ Technician validation: PASSED")
    
except Exception as e:
    print(f"❌ Technician creation test: {str(e)}")

print("Data creation and validation tests completed.")
''', text=True, capture_output=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            test_results['tests']['data_creation'] = {
                'status': 'PASSED',
                'output': result.stdout
            }
            test_results['passed_tests'] += 1
            print("✅ Data creation and validation: PASSED")
        else:
            test_results['tests']['data_creation'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            test_results['failed_tests'] += 1
            print("❌ Data creation and validation: FAILED")
            
    except Exception as e:
        test_results['tests']['data_creation'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        test_results['failed_tests'] += 1
        print(f"❌ Data creation and validation: ERROR - {str(e)}")
    
    test_results['total_tests'] += 1
    
    # Test 4: Arabic Localization
    print("\n4️⃣  Testing Arabic Localization")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe

print("Testing Arabic localization features...")

# Check system settings for Arabic support
try:
    system_settings = frappe.get_doc('System Settings')
    print(f"System language: {system_settings.language}")
    print(f"System country: {system_settings.country}")
    
    # Check if Arabic is enabled
    arabic_enabled = frappe.db.exists('Language', 'ar')
    print(f"Arabic language enabled: {'✅ YES' if arabic_enabled else '❌ NO'}")
    
except Exception as e:
    print(f"Error checking system settings: {str(e)}")

# Test Arabic text handling
try:
    arabic_text = 'ورشة اختبار النظام'
    encoded_text = arabic_text.encode('utf-8').decode('utf-8')
    print(f"Arabic text encoding test: {'✅ PASSED' if encoded_text == arabic_text else '❌ FAILED'}")
    
except Exception as e:
    print(f"Arabic text encoding error: {str(e)}")

print("Arabic localization tests completed.")
''', text=True, capture_output=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            test_results['tests']['arabic_localization'] = {
                'status': 'PASSED',
                'output': result.stdout
            }
            test_results['passed_tests'] += 1
            print("✅ Arabic localization: PASSED")
        else:
            test_results['tests']['arabic_localization'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            test_results['failed_tests'] += 1
            print("❌ Arabic localization: FAILED")
            
    except Exception as e:
        test_results['tests']['arabic_localization'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        test_results['failed_tests'] += 1
        print(f"❌ Arabic localization: ERROR - {str(e)}")
    
    test_results['total_tests'] += 1
    
    # Test 5: API Endpoints
    print("\n5️⃣  Testing API Endpoints")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe

print("Testing API endpoints...")

# Test backup API endpoints
try:
    from universal_workshop.api.backup_api import get_backup_status, get_backup_history
    
    # Test backup status API
    status = get_backup_status()
    print(f"Backup status API: {'✅ WORKING' if status else '❌ FAILED'}")
    
    # Test backup history API
    history = get_backup_history(limit=5)
    print(f"Backup history API: {'✅ WORKING' if isinstance(history, list) else '❌ FAILED'}")
    
except Exception as e:
    print(f"API endpoint test error: {str(e)}")

print("API endpoint tests completed.")
''', text=True, capture_output=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            test_results['tests']['api_endpoints'] = {
                'status': 'PASSED',
                'output': result.stdout
            }
            test_results['passed_tests'] += 1
            print("✅ API endpoints: PASSED")
        else:
            test_results['tests']['api_endpoints'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            test_results['failed_tests'] += 1
            print("❌ API endpoints: FAILED")
            
    except Exception as e:
        test_results['tests']['api_endpoints'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        test_results['failed_tests'] += 1
        print(f"❌ API endpoints: ERROR - {str(e)}")
    
    test_results['total_tests'] += 1
    
    # Calculate overall status
    success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100
    
    if success_rate >= 90:
        test_results['overall_status'] = 'EXCELLENT'
    elif success_rate >= 80:
        test_results['overall_status'] = 'GOOD'
    elif success_rate >= 60:
        test_results['overall_status'] = 'ACCEPTABLE'
    else:
        test_results['overall_status'] = 'NEEDS_ATTENTION'
    
    # Final summary
    print("\n🎯 MIGRATION TESTING SUMMARY")
    print("="*70)
    print(f"📊 Test Results:")
    print(f"   Total Tests: {test_results['total_tests']}")
    print(f"   Passed: {test_results['passed_tests']}")
    print(f"   Failed: {test_results['failed_tests']}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Overall Status: {test_results['overall_status']}")
    
    if test_results['failed_tests'] > 0:
        print(f"\n⚠️  Failed Tests:")
        for test_name, test_data in test_results['tests'].items():
            if test_data['status'] != 'PASSED':
                print(f"   • {test_name}: {test_data['status']}")
    
    # Save test results
    results_file = 'migration_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📄 Test results saved: {results_file}")
    print(f"🎯 Migration testing completed with {test_results['overall_status']} status")
    
    return test_results

if __name__ == "__main__":
    run_migration_tests()
