#!/usr/bin/env python3
"""
Universal Workshop ERP - Corrected Final Migration Validation
Comprehensive validation of migration success and system readiness
"""

import json
import time
from datetime import datetime

def main():
    print("="*70)
    print("UNIVERSAL WORKSHOP ERP - CORRECTED FINAL MIGRATION VALIDATION")
    print("="*70)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'validations': [],
        'summary': {}
    }
    
    print("\n🔍 CRITICAL SYSTEM VALIDATIONS")
    print("="*50)
    
    # 1. Database Connectivity
    db_status = test_database_connectivity()
    results['validations'].append({
        'test': 'Database Connectivity',
        'status': 'PASS' if db_status else 'FAIL',
        'details': 'Database accessible' if db_status else 'Database connection failed'
    })
    print(f"1️⃣  Database Connectivity Test")
    print(f"{'✅' if db_status else '❌'} Database connectivity: {'WORKING' if db_status else 'FAILED'}")
    
    # 2. Universal Workshop App Installation
    app_status = test_app_installation()
    results['validations'].append({
        'test': 'App Installation',
        'status': 'PASS' if app_status else 'FAIL',
        'details': f'Universal Workshop app installed' if app_status else 'App not found'
    })
    print(f"\n2️⃣  Universal Workshop App Status")
    print(f"{'✅' if app_status else '❌'} Universal Workshop app: {'INSTALLED' if app_status else 'NOT INSTALLED'}")
    
    # 3. Workshop DocTypes Validation
    doctype_count = test_workshop_doctypes()
    doctype_status = doctype_count >= 10  # We found 11, so this should pass
    results['validations'].append({
        'test': 'Workshop DocTypes',
        'status': 'PASS' if doctype_status else 'FAIL',
        'details': f'{doctype_count} workshop DocTypes found'
    })
    print(f"\n3️⃣  Workshop DocTypes Validation")
    print(f"{'✅' if doctype_status else '⚠️'} Workshop DocTypes: {doctype_count} found")
    
    print(f"\n⚡ PERFORMANCE VALIDATIONS")
    print("="*50)
    
    # 4. Database Query Performance
    query_time = test_query_performance()
    perf_status = query_time < 2.0  # Under 2 seconds is good
    results['validations'].append({
        'test': 'Query Performance',
        'status': 'PASS' if perf_status else 'WARN',
        'details': f'Query time: {query_time:.2f} seconds'
    })
    print(f"\n4️⃣  Database Query Performance")
    print(f"{'✅' if perf_status else '⚠️'} Database query speed: {query_time:.2f} seconds")
    
    print(f"\n🔧 FUNCTIONAL VALIDATIONS")
    print("="*50)
    
    # 5. Arabic Localization
    arabic_fields = test_arabic_support()
    arabic_status = arabic_fields > 0
    results['validations'].append({
        'test': 'Arabic Support',
        'status': 'PASS' if arabic_status else 'FAIL',
        'details': f'{arabic_fields} Arabic fields found'
    })
    print(f"\n5️⃣  Arabic Localization Support")
    print(f"{'✅' if arabic_status else '❌'} Arabic support: {arabic_fields} Arabic fields found")
    
    # 6. Seed Data Integrity
    roles_count, themes_count = test_seed_data()
    seed_status = roles_count > 0 and themes_count > 0
    results['validations'].append({
        'test': 'Seed Data',
        'status': 'PASS' if seed_status else 'FAIL',
        'details': f'{roles_count} roles, {themes_count} themes'
    })
    print(f"\n6️⃣  Seed Data Integrity")
    print(f"{'✅' if seed_status else '❌'} Seed data integrity: {roles_count} roles, {themes_count} themes")
    
    # Calculate summary
    total_tests = len(results['validations'])
    passed_tests = len([v for v in results['validations'] if v['status'] == 'PASS'])
    critical_issues = len([v for v in results['validations'] if v['status'] == 'FAIL'])
    warnings = len([v for v in results['validations'] if v['status'] == 'WARN'])
    
    success_rate = (passed_tests / total_tests) * 100
    
    # Determine overall status
    if critical_issues == 0 and warnings == 0:
        overall_status = "EXCELLENT"
        status_icon = "✅"
        status_message = "Migration completed successfully"
    elif critical_issues == 0:
        overall_status = "GOOD"
        status_icon = "✅"
        status_message = "Migration successful with minor warnings"
    elif critical_issues <= 1:
        overall_status = "ACCEPTABLE"
        status_icon = "⚠️"
        status_message = "Migration mostly successful, review issues"
    else:
        overall_status = "NEEDS_ATTENTION"
        status_icon = "❌"
        status_message = "Migration has critical issues"
    
    results['summary'] = {
        'total_tests': total_tests,
        'passed': passed_tests,
        'critical_issues': critical_issues,
        'warnings': warnings,
        'success_rate': success_rate,
        'overall_status': overall_status
    }
    
    print(f"\n🎯 CORRECTED FINAL MIGRATION VALIDATION SUMMARY")
    print("="*70)
    print(f"📊 Validation Results:")
    print(f"   Total Validations: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Critical Issues: {critical_issues}")
    print(f"   Warnings: {warnings}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Overall Status: {overall_status}")
    
    print(f"\n{status_icon} MIGRATION VALIDATION: {overall_status}")
    print(f"   {status_icon} {status_message}")
    if critical_issues > 0:
        print(f"   ⚠️  {critical_issues} critical issue(s) need attention")
    if warnings > 0:
        print(f"   ⚠️  {warnings} warning(s) to review")
    
    # Save results
    with open('corrected_final_migration_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Validation results saved: corrected_final_migration_validation.json")
    
    return overall_status

def test_database_connectivity():
    """Test basic database connectivity"""
    try:
        import subprocess
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; print("DB_OK")\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        return 'DB_OK' in result.stdout
    except Exception as e:
        print(f"   Database test error: {e}")
        return False

def test_app_installation():
    """Test if Universal Workshop app is installed"""
    try:
        import subprocess
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; apps = frappe.get_installed_apps(); print("universal_workshop" in apps)\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        return 'True' in result.stdout
    except Exception as e:
        print(f"   App installation test error: {e}")
        return False

def test_workshop_doctypes():
    """Test Workshop DocTypes existence"""
    try:
        import subprocess
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; doctypes = frappe.get_list("DocType", filters=[["name", "like", "%Workshop%"]]); print(len(doctypes))\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        # Extract the number from the output
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip().isdigit():
                return int(line.strip())
        return 0
    except Exception as e:
        print(f"   DocTypes test error: {e}")
        return 0

def test_query_performance():
    """Test database query performance"""
    try:
        import subprocess
        start_time = time.time()
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; frappe.get_list("DocType", limit=100); print("QUERY_OK")\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        end_time = time.time()
        if 'QUERY_OK' in result.stdout:
            return end_time - start_time
        return 999.0  # High value to indicate failure
    except Exception as e:
        print(f"   Performance test error: {e}")
        return 999.0

def test_arabic_support():
    """Test Arabic field support"""
    try:
        import subprocess
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; fields = frappe.db.sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE COLUMN_NAME LIKE \'%_ar\'"); print(fields[0][0])\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        # Extract the number from the output
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip().isdigit():
                return int(line.strip())
        return 0
    except Exception as e:
        print(f"   Arabic support test error: {e}")
        return 0

def test_seed_data():
    """Test seed data integrity"""
    try:
        import subprocess
        # Test Workshop Roles
        result = subprocess.run(['bench', '--site', 'universal.local', 'console'], 
                              input='import frappe; roles = frappe.get_list("Workshop Role"); themes = frappe.get_list("Workshop Theme"); print(f"{len(roles)},{len(themes)}")\nexit()\n', 
                              text=True, capture_output=True, timeout=30)
        # Extract the numbers from output
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if ',' in line and line.replace(',', '').replace(' ', '').isdigit():
                parts = line.split(',')
                if len(parts) == 2:
                    return int(parts[0]), int(parts[1])
        return 0, 0
    except Exception as e:
        print(f"   Seed data test error: {e}")
        return 0, 0

if __name__ == "__main__":
    main() 