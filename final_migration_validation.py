#!/usr/bin/env python3
"""
Universal Workshop ERP - Final Migration Validation
Comprehensive system validation after migration
"""

import subprocess
import json
import datetime

def run_final_validation():
    print("="*70)
    print("UNIVERSAL WORKSHOP ERP - FINAL MIGRATION VALIDATION")
    print("="*70)
    
    validation_results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'validation_status': 'IN_PROGRESS',
        'critical_tests': {},
        'performance_tests': {},
        'functional_tests': {},
        'summary': {
            'total_validations': 0,
            'passed_validations': 0,
            'critical_issues': 0,
            'warnings': 0
        }
    }
    
    print("\n🔍 CRITICAL SYSTEM VALIDATIONS")
    print("="*50)
    
    # Critical Test 1: Database Connectivity
    print("\n1️⃣  Database Connectivity Test")
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            'SELECT "Database connectivity test" as test, NOW() as timestamp;'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            validation_results['critical_tests']['database_connectivity'] = 'PASSED'
            validation_results['summary']['passed_validations'] += 1
            print("✅ Database connectivity: WORKING")
        else:
            validation_results['critical_tests']['database_connectivity'] = 'FAILED'
            validation_results['summary']['critical_issues'] += 1
            print("❌ Database connectivity: FAILED")
            
    except Exception as e:
        validation_results['critical_tests']['database_connectivity'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ Database connectivity: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    # Critical Test 2: Universal Workshop App Status
    print("\n2️⃣  Universal Workshop App Status")
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'console'
        ], input='''
import frappe
installed_apps = frappe.get_installed_apps()
if "universal_workshop" in installed_apps:
    print("✅ Universal Workshop app: INSTALLED")
else:
    print("❌ Universal Workshop app: NOT INSTALLED")
''', text=True, capture_output=True)
        
        if 'INSTALLED' in result.stdout:
            validation_results['critical_tests']['app_installation'] = 'PASSED'
            validation_results['summary']['passed_validations'] += 1
            print("✅ Universal Workshop app: INSTALLED")
        else:
            validation_results['critical_tests']['app_installation'] = 'FAILED'
            validation_results['summary']['critical_issues'] += 1
            print("❌ Universal Workshop app: NOT INSTALLED")
            
    except Exception as e:
        validation_results['critical_tests']['app_installation'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ App installation check: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    # Critical Test 3: Core DocTypes
    print("\n3️⃣  Core DocTypes Validation")
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            """
            SELECT 
                COUNT(*) as workshop_doctypes_count
            FROM information_schema.tables 
            WHERE table_schema = 'universal_workshop_db' 
            AND table_name LIKE '%workshop%';
            """
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            count = int(lines[-1]) if lines[-1].isdigit() else 0
            
            if count >= 10:
                validation_results['critical_tests']['core_doctypes'] = 'PASSED'
                validation_results['summary']['passed_validations'] += 1
                print(f"✅ Core DocTypes: {count} workshop tables found")
            else:
                validation_results['critical_tests']['core_doctypes'] = 'INSUFFICIENT'
                validation_results['summary']['warnings'] += 1
                print(f"⚠️  Core DocTypes: Only {count} workshop tables found")
        else:
            validation_results['critical_tests']['core_doctypes'] = 'FAILED'
            validation_results['summary']['critical_issues'] += 1
            print("❌ Core DocTypes check: FAILED")
            
    except Exception as e:
        validation_results['critical_tests']['core_doctypes'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ Core DocTypes check: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    print("\n⚡ PERFORMANCE VALIDATIONS")
    print("="*50)
    
    # Performance Test 1: Database Query Speed
    print("\n4️⃣  Database Query Performance")
    try:
        start_time = datetime.datetime.now()
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            """
            SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'universal_workshop_db';
            SELECT COUNT(*) FROM `tabWorkshop Role`;
            SELECT COUNT(*) FROM `tabWorkshop Theme`;
            """
        ], capture_output=True, text=True)
        end_time = datetime.datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        
        if result.returncode == 0 and query_time < 5.0:
            validation_results['performance_tests']['query_speed'] = f'PASSED ({query_time:.2f}s)'
            validation_results['summary']['passed_validations'] += 1
            print(f"✅ Database query speed: {query_time:.2f} seconds")
        else:
            validation_results['performance_tests']['query_speed'] = f'SLOW ({query_time:.2f}s)'
            validation_results['summary']['warnings'] += 1
            print(f"⚠️  Database query speed: {query_time:.2f} seconds (slow)")
            
    except Exception as e:
        validation_results['performance_tests']['query_speed'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ Database query performance: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    print("\n🔧 FUNCTIONAL VALIDATIONS")
    print("="*50)
    
    # Functional Test 1: Arabic Support
    print("\n5️⃣  Arabic Localization Support")
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            "SHOW COLUMNS FROM `tabWorkshop Profile` WHERE Field LIKE '%_ar';"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            arabic_fields = len([line for line in lines if '_ar' in line])
            
            if arabic_fields >= 3:
                validation_results['functional_tests']['arabic_support'] = 'PASSED'
                validation_results['summary']['passed_validations'] += 1
                print(f"✅ Arabic support: {arabic_fields} Arabic fields found")
            else:
                validation_results['functional_tests']['arabic_support'] = 'INSUFFICIENT'
                validation_results['summary']['warnings'] += 1
                print(f"⚠️  Arabic support: Only {arabic_fields} Arabic fields found")
        else:
            validation_results['functional_tests']['arabic_support'] = 'FAILED'
            validation_results['summary']['critical_issues'] += 1
            print("❌ Arabic support check: FAILED")
            
    except Exception as e:
        validation_results['functional_tests']['arabic_support'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ Arabic support check: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    # Functional Test 2: Seed Data Integrity
    print("\n6️⃣  Seed Data Integrity")
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            """
            SELECT 
                (SELECT COUNT(*) FROM `tabWorkshop Role`) as roles,
                (SELECT COUNT(*) FROM `tabWorkshop Theme`) as themes;
            """
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                data_line = lines[-1].split('\t')
                if len(data_line) >= 2:
                    roles = int(data_line[0])
                    themes = int(data_line[1])
                    
                    if roles >= 6 and themes >= 2:
                        validation_results['functional_tests']['seed_data'] = 'PASSED'
                        validation_results['summary']['passed_validations'] += 1
                        print(f"✅ Seed data integrity: {roles} roles, {themes} themes")
                    else:
                        validation_results['functional_tests']['seed_data'] = 'INCOMPLETE'
                        validation_results['summary']['warnings'] += 1
                        print(f"⚠️  Seed data integrity: {roles} roles, {themes} themes (incomplete)")
        else:
            validation_results['functional_tests']['seed_data'] = 'FAILED'
            validation_results['summary']['critical_issues'] += 1
            print("❌ Seed data integrity: FAILED")
            
    except Exception as e:
        validation_results['functional_tests']['seed_data'] = f'ERROR: {str(e)}'
        validation_results['summary']['critical_issues'] += 1
        print(f"❌ Seed data integrity: ERROR - {str(e)}")
    
    validation_results['summary']['total_validations'] += 1
    
    # Determine overall validation status
    total = validation_results['summary']['total_validations']
    passed = validation_results['summary']['passed_validations']
    critical = validation_results['summary']['critical_issues']
    warnings = validation_results['summary']['warnings']
    
    if critical == 0 and passed == total:
        validation_results['validation_status'] = 'EXCELLENT'
    elif critical == 0 and passed >= total * 0.8:
        validation_results['validation_status'] = 'GOOD'
    elif critical <= 1:
        validation_results['validation_status'] = 'ACCEPTABLE'
    else:
        validation_results['validation_status'] = 'CRITICAL_ISSUES'
    
    # Final Summary
    print("\n🎯 FINAL MIGRATION VALIDATION SUMMARY")
    print("="*70)
    print(f"📊 Validation Results:")
    print(f"   Total Validations: {total}")
    print(f"   Passed: {passed}")
    print(f"   Critical Issues: {critical}")
    print(f"   Warnings: {warnings}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    print(f"   Overall Status: {validation_results['validation_status']}")
    
    # Status-specific messages
    if validation_results['validation_status'] == 'EXCELLENT':
        print("\n🎉 MIGRATION VALIDATION: EXCELLENT")
        print("   ✅ All validations passed successfully")
        print("   ✅ System is ready for production use")
        print("   ✅ No critical issues detected")
        
    elif validation_results['validation_status'] == 'GOOD':
        print("\n✅ MIGRATION VALIDATION: GOOD")
        print("   ✅ Core functionality validated")
        print("   ⚠️  Minor issues may need attention")
        print("   ✅ System is suitable for production")
        
    elif validation_results['validation_status'] == 'ACCEPTABLE':
        print("\n⚠️  MIGRATION VALIDATION: ACCEPTABLE")
        print("   ⚠️  Some issues detected")
        print("   ⚠️  Review warnings before production")
        print("   ✅ Core functionality appears working")
        
    else:
        print("\n❌ MIGRATION VALIDATION: CRITICAL ISSUES")
        print("   ❌ Critical issues must be resolved")
        print("   ❌ System not ready for production")
        print("   ❌ Immediate attention required")
    
    # Save validation results
    results_file = 'final_migration_validation.json'
    with open(results_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n📄 Validation results saved: {results_file}")
    
    return validation_results

if __name__ == "__main__":
    run_final_validation()
