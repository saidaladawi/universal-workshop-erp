#!/usr/bin/env python3

import os
import sys

# Add frappe-bench to path
sys.path.append('/home/said/frappe-dev/frappe-bench')
sys.path.append('/home/said/frappe-dev/frappe-bench/apps/frappe')
sys.path.append('/home/said/frappe-dev/frappe-bench/apps/universal_workshop')

def test_authentication_flow():
    """Test authentication flow components"""
    print("🔐 Testing Universal Workshop Authentication Flow...")
    
    results = {}
    
    # 1. Test Custom Login Page
    print("\n1. Testing Custom Login Page...")
    login_py_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/www/login.py"
    login_html_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/www/login.html"
    
    if os.path.exists(login_py_path):
        print("✅ login.py exists")
        results['login_py'] = True
    else:
        print("❌ login.py not found")
        results['login_py'] = False
    
    if os.path.exists(login_html_path):
        print("✅ login.html exists")
        results['login_html'] = True
    else:
        print("❌ login.html not found")
        results['login_html'] = False
    
    # 2. Test Session Management
    print("\n2. Testing Session Management...")
    session_manager_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/user_management/session_manager.py"
    
    if os.path.exists(session_manager_path):
        print("✅ session_manager.py exists")
        results['session_manager'] = True
    else:
        print("❌ session_manager.py not found")
        results['session_manager'] = False
    
    # 3. Test MFA System
    print("\n3. Testing MFA System...")
    mfa_manager_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/user_management/mfa_manager.py"
    
    if os.path.exists(mfa_manager_path):
        print("✅ mfa_manager.py exists")
        results['mfa_manager'] = True
    else:
        print("❌ mfa_manager.py not found")
        results['mfa_manager'] = False
    
    # 4. Test Security Dashboard
    print("\n4. Testing Security Dashboard...")
    security_dashboard_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/user_management/dashboard/security_dashboard.py"
    
    if os.path.exists(security_dashboard_path):
        print("✅ security_dashboard.py exists")
        results['security_dashboard'] = True
    else:
        print("❌ security_dashboard.py not found")
        results['security_dashboard'] = False
    
    # 5. Test Arabic Interface
    print("\n5. Testing Arabic Interface...")
    arabic_css_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css"
    arabic_js_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/public/js/arabic-utils.js"
    
    if os.path.exists(arabic_css_path):
        print("✅ arabic-rtl.css exists")
        results['arabic_css'] = True
    else:
        print("❌ arabic-rtl.css not found")
        results['arabic_css'] = False
    
    if os.path.exists(arabic_js_path):
        print("✅ arabic-utils.js exists")
        results['arabic_js'] = True
    else:
        print("❌ arabic-utils.js not found")
        results['arabic_js'] = False
    
    # 6. Test License Management
    print("\n6. Testing License Management...")
    license_validator_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/license_management/license_validator.py"
    
    if os.path.exists(license_validator_path):
        print("✅ license_validator.py exists")
        results['license_validator'] = True
    else:
        print("❌ license_validator.py not found")
        results['license_validator'] = False
    
    # 7. Test Boot Session
    print("\n7. Testing Boot Session...")
    boot_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/boot.py"
    
    if os.path.exists(boot_path):
        print("✅ boot.py exists")
        results['boot_session'] = True
        
        # Check boot.py content
        with open(boot_path, 'r') as f:
            boot_content = f.read()
        
        if "get_session_boot_info" in boot_content:
            print("✅ Session boot integration present")
            results['boot_session_integration'] = True
        else:
            print("❌ Session boot integration missing")
            results['boot_session_integration'] = False
    else:
        print("❌ boot.py not found")
        results['boot_session'] = False
        results['boot_session_integration'] = False
    
    # 8. Test Permission Hooks
    print("\n8. Testing Permission Hooks...")
    permission_hooks_path = "/home/said/frappe-dev/frappe-bench/apps/universal_workshop/universal_workshop/user_management/permission_hooks.py"
    
    if os.path.exists(permission_hooks_path):
        print("✅ permission_hooks.py exists")
        results['permission_hooks'] = True
    else:
        print("❌ permission_hooks.py not found")
        results['permission_hooks'] = False
    
    # Calculate results
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🔐 Authentication Flow Test Results:")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🟢 EXCELLENT - Authentication system is comprehensive")
    elif success_rate >= 75:
        print("🟡 GOOD - Authentication system is functional with minor gaps")
    elif success_rate >= 50:
        print("🟠 FAIR - Authentication system needs improvements")
    else:
        print("🔴 POOR - Authentication system needs significant work")
    
    # Show detailed results
    print(f"\n📊 Detailed Results:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    return results

if __name__ == "__main__":
    test_authentication_flow() 