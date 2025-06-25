#!/usr/bin/env python3
"""
Universal Workshop ERP - Migration Testing Report Generator
Creates comprehensive migration test report
"""

import json
import datetime
import subprocess
import os

def generate_migration_test_report():
    print("="*70)
    print("UNIVERSAL WORKSHOP ERP - MIGRATION TEST REPORT")
    print("="*70)
    
    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'test_summary': {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0
        },
        'test_results': {},
        'overall_status': 'UNKNOWN',
        'recommendations': []
    }
    
    print("\n1️⃣  Database Table Validation")
    print("-" * 50)
    
    # Test 1: Check Universal Workshop tables
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            """
            SELECT 
                table_name,
                table_rows,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'size_mb'
            FROM information_schema.tables 
            WHERE table_schema = 'universal_workshop_db' 
            AND table_name LIKE '%workshop%'
            ORDER BY table_name;
            """
        ], capture_output=True, text=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            workshop_tables = [line for line in lines if 'workshop' in line.lower()]
            
            report['test_results']['database_tables'] = {
                'status': 'PASSED',
                'workshop_tables_found': len(workshop_tables),
                'details': workshop_tables
            }
            report['test_summary']['passed_tests'] += 1
            print(f"✅ Workshop tables found: {len(workshop_tables)}")
            
            for table in workshop_tables[:5]:  # Show first 5
                print(f"   • {table}")
                
        else:
            report['test_results']['database_tables'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            report['test_summary']['failed_tests'] += 1
            print("❌ Database table check: FAILED")
            
    except Exception as e:
        report['test_results']['database_tables'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        report['test_summary']['failed_tests'] += 1
        print(f"❌ Database table check: ERROR - {str(e)}")
    
    report['test_summary']['total_tests'] += 1
    
    print("\n2️⃣  Workshop Profile Validation")
    print("-" * 50)
    
    # Test 2: Workshop Profile structure
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            "DESCRIBE `tabWorkshop Profile`;"
        ], capture_output=True, text=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            field_count = len([line for line in lines if line and not line.startswith('Field')])
            
            # Check for Arabic fields
            arabic_fields = [line for line in lines if '_ar' in line]
            
            report['test_results']['workshop_profile'] = {
                'status': 'PASSED',
                'field_count': field_count,
                'arabic_fields': len(arabic_fields)
            }
            report['test_summary']['passed_tests'] += 1
            print(f"✅ Workshop Profile fields: {field_count}")
            print(f"✅ Arabic fields: {len(arabic_fields)}")
            
        else:
            report['test_results']['workshop_profile'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            report['test_summary']['failed_tests'] += 1
            print("❌ Workshop Profile check: FAILED")
            
    except Exception as e:
        report['test_results']['workshop_profile'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        report['test_summary']['failed_tests'] += 1
        print(f"❌ Workshop Profile check: ERROR - {str(e)}")
    
    report['test_summary']['total_tests'] += 1
    
    print("\n3️⃣  Seed Data Validation")
    print("-" * 50)
    
    # Test 3: Check seed data
    try:
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'mariadb', '-e',
            """
            SELECT 'Workshop Roles' as data_type, COUNT(*) as count FROM `tabWorkshop Role`
            UNION ALL
            SELECT 'Workshop Themes' as data_type, COUNT(*) as count FROM `tabWorkshop Theme`
            UNION ALL
            SELECT 'Workshop Profiles' as data_type, COUNT(*) as count FROM `tabWorkshop Profile`;
            """
        ], capture_output=True, text=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            data_counts = {}
            
            for line in lines[1:]:  # Skip header
                if line and '\t' in line:
                    data_type, count = line.split('\t')
                    data_counts[data_type] = int(count)
            
            # Validate expected counts
            role_count = data_counts.get('Workshop Roles', 0)
            theme_count = data_counts.get('Workshop Themes', 0)
            profile_count = data_counts.get('Workshop Profiles', 0)
            
            if role_count >= 6 and theme_count >= 2:
                report['test_results']['seed_data'] = {
                    'status': 'PASSED',
                    'role_count': role_count,
                    'theme_count': theme_count,
                    'profile_count': profile_count
                }
                report['test_summary']['passed_tests'] += 1
                print(f"✅ Seed data validation: PASSED")
                print(f"   • Workshop Roles: {role_count}")
                print(f"   • Workshop Themes: {theme_count}")
                print(f"   • Workshop Profiles: {profile_count}")
            else:
                report['test_results']['seed_data'] = {
                    'status': 'WARNING',
                    'role_count': role_count,
                    'theme_count': theme_count,
                    'profile_count': profile_count,
                    'message': 'Incomplete seed data'
                }
                report['test_summary']['warnings'] += 1
                print(f"⚠️  Seed data validation: INCOMPLETE")
                
        else:
            report['test_results']['seed_data'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            report['test_summary']['failed_tests'] += 1
            print("❌ Seed data check: FAILED")
            
    except Exception as e:
        report['test_results']['seed_data'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        report['test_summary']['failed_tests'] += 1
        print(f"❌ Seed data check: ERROR - {str(e)}")
    
    report['test_summary']['total_tests'] += 1
    
    print("\n4️⃣  System Integration Test")
    print("-" * 50)
    
    # Test 4: Check system integration
    try:
        # Check if bench commands work
        result = subprocess.run([
            'bench', '--site', 'universal.local', 'version'
        ], capture_output=True, text=True, cwd='/home/said/frappe-dev/frappe-bench')
        
        if result.returncode == 0:
            version_info = result.stdout.strip()
            
            report['test_results']['system_integration'] = {
                'status': 'PASSED',
                'version_info': version_info
            }
            report['test_summary']['passed_tests'] += 1
            print(f"✅ System integration: WORKING")
            print(f"   Version info available: {len(version_info)} chars")
            
        else:
            report['test_results']['system_integration'] = {
                'status': 'FAILED',
                'error': result.stderr
            }
            report['test_summary']['failed_tests'] += 1
            print("❌ System integration: FAILED")
            
    except Exception as e:
        report['test_results']['system_integration'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        report['test_summary']['failed_tests'] += 1
        print(f"❌ System integration: ERROR - {str(e)}")
    
    report['test_summary']['total_tests'] += 1
    
    # Calculate overall status
    total = report['test_summary']['total_tests']
    passed = report['test_summary']['passed_tests']
    failed = report['test_summary']['failed_tests']
    warnings = report['test_summary']['warnings']
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    if success_rate >= 90 and failed == 0:
        report['overall_status'] = 'EXCELLENT'
    elif success_rate >= 80 and failed <= 1:
        report['overall_status'] = 'GOOD'
    elif success_rate >= 60:
        report['overall_status'] = 'ACCEPTABLE'
    else:
        report['overall_status'] = 'NEEDS_ATTENTION'
    
    # Generate recommendations
    if failed > 0:
        report['recommendations'].append('Review and fix failed tests before production deployment')
    if warnings > 0:
        report['recommendations'].append('Address warning conditions for optimal performance')
    if success_rate < 100:
        report['recommendations'].append('Consider running additional validation tests')
    
    # Final summary
    print("\n🎯 MIGRATION TEST SUMMARY")
    print("="*70)
    print(f"📊 Test Results:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Warnings: {warnings}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Overall Status: {report['overall_status']}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Save report
    report_file = 'migration_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved: {report_file}")
    
    return report

if __name__ == "__main__":
    generate_migration_test_report()
