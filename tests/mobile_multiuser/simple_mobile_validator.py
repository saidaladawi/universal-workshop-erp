#!/usr/bin/env python3
"""
Universal Workshop ERP - Simple Mobile Interface Validator
Validates mobile interface without browser automation dependencies
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import subprocess
import re

class SimpleMobileValidator:
    """
    Simple mobile interface validation without browser automation
    """
    
    def __init__(self):
        self.test_results = []
        self.error_count = 0
        self.success_count = 0
        
        # Base URL for testing
        self.base_url = 'http://localhost:8000'
        
        # Mobile user agents for testing
        self.mobile_user_agents = {
            'iPhone_13': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Pixel_5': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Galaxy_S21': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'iPad_Pro': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        }
        
        # Initialize report storage
        self.results_dir = Path('test_results/mobile_multiuser')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("📱 Simple Mobile Validator Initialized")

    def test_server_availability(self):
        """
        Test basic server availability and response
        """
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}", timeout=10)
            
            result = {
                'test_type': 'server_availability',
                'url': self.base_url,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'success': response.status_code in [200, 302],
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            if result['success']:
                self.success_count += 1
                print(f"   ✅ Server available: {response.status_code}")
            else:
                self.error_count += 1
                print(f"   ❌ Server unavailable: {response.status_code}")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            result = {
                'test_type': 'server_availability',
                'url': self.base_url,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            print(f"   ❌ Server connection failed: {e}")
            return result

    def test_mobile_login_page(self, device_name, user_agent):
        """
        Test mobile login page accessibility and response
        """
        start_time = time.time()
        
        try:
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ar-EG,ar;q=0.9,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate'
            }
            
            response = requests.get(f"{self.base_url}/login", headers=headers, timeout=10)
            
            # Check response content
            content = response.text
            
            # Look for mobile-friendly elements
            has_viewport_meta = 'viewport' in content and 'width=device-width' in content
            has_mobile_css = 'mobile' in content.lower() or 'responsive' in content.lower()
            has_touch_friendly = 'touch' in content.lower()
            
            # Look for Arabic/RTL support
            has_rtl_support = 'dir="rtl"' in content or 'arabic' in content.lower()
            has_arabic_lang = 'lang="ar"' in content or 'ar-' in content
            
            # Check for essential form elements
            has_username_field = 'name="usr"' in content or 'id="login_email"' in content
            has_password_field = 'name="pwd"' in content or 'type="password"' in content
            has_submit_button = 'type="submit"' in content or 'login' in content.lower()
            
            result = {
                'test_type': 'mobile_login_page',
                'device': device_name,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(content),
                'has_viewport_meta': has_viewport_meta,
                'has_mobile_css': has_mobile_css,
                'has_touch_friendly': has_touch_friendly,
                'has_rtl_support': has_rtl_support,
                'has_arabic_lang': has_arabic_lang,
                'has_username_field': has_username_field,
                'has_password_field': has_password_field,
                'has_submit_button': has_submit_button,
                'success': response.status_code == 200 and has_username_field and has_password_field,
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            if result['success']:
                self.success_count += 1
                print(f"   ✅ {device_name} login page: accessible")
            else:
                self.error_count += 1
                print(f"   ❌ {device_name} login page: issues detected")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            result = {
                'test_type': 'mobile_login_page',
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            print(f"   ❌ {device_name} login page failed: {e}")
            return result

    def test_css_assets(self):
        """
        Test CSS asset availability and mobile responsiveness
        """
        start_time = time.time()
        
        css_assets = [
            '/assets/universal_workshop/css/arabic-rtl.css',
            '/assets/universal_workshop/css/dynamic_branding.css',
            '/assets/frappe/css/desk.min.css',
            '/assets/frappe/css/form.min.css'
        ]
        
        results = []
        
        for asset in css_assets:
            try:
                response = requests.get(f"{self.base_url}{asset}", timeout=5)
                
                asset_result = {
                    'test_type': 'css_asset',
                    'asset_url': asset,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'success': response.status_code == 200,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Check for mobile-specific CSS
                if response.status_code == 200:
                    content = response.text
                    asset_result['has_media_queries'] = '@media' in content
                    asset_result['has_mobile_styles'] = 'mobile' in content.lower() or 'max-width' in content
                    asset_result['has_rtl_styles'] = 'rtl' in content.lower() or 'dir=' in content
                
                results.append(asset_result)
                
                if asset_result['success']:
                    self.success_count += 1
                    print(f"   ✅ CSS asset loaded: {asset}")
                else:
                    self.error_count += 1
                    print(f"   ❌ CSS asset failed: {asset}")
                
            except Exception as e:
                self.error_count += 1
                asset_result = {
                    'test_type': 'css_asset',
                    'asset_url': asset,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(asset_result)
                print(f"   ❌ CSS asset error: {asset} - {e}")
        
        return results

    def test_js_assets(self):
        """
        Test JavaScript asset availability
        """
        start_time = time.time()
        
        js_assets = [
            '/assets/universal_workshop/js/rtl_branding_manager.js',
            '/assets/frappe/js/frappe-web.min.js',
            '/assets/frappe/js/control.min.js'
        ]
        
        results = []
        
        for asset in js_assets:
            try:
                response = requests.get(f"{self.base_url}{asset}", timeout=5)
                
                asset_result = {
                    'test_type': 'js_asset',
                    'asset_url': asset,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'success': response.status_code == 200,
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(asset_result)
                
                if asset_result['success']:
                    self.success_count += 1
                    print(f"   ✅ JS asset loaded: {asset}")
                else:
                    self.error_count += 1
                    print(f"   ❌ JS asset failed: {asset}")
                
            except Exception as e:
                self.error_count += 1
                asset_result = {
                    'test_type': 'js_asset',
                    'asset_url': asset,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(asset_result)
                print(f"   ❌ JS asset error: {asset} - {e}")
        
        return results

    def test_api_endpoints(self):
        """
        Test critical API endpoints that mobile interface would use
        """
        start_time = time.time()
        
        api_endpoints = [
            '/api/method/login',
            '/api/method/logout',
            '/api/method/frappe.auth.get_logged_user',
            '/api/resource/User'
        ]
        
        results = []
        
        for endpoint in api_endpoints:
            try:
                # Test with mobile user agent
                headers = {
                    'User-Agent': self.mobile_user_agents['iPhone_13'],
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
                
                endpoint_result = {
                    'test_type': 'api_endpoint',
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'success': response.status_code in [200, 401, 403],  # 401/403 are acceptable for protected endpoints
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(endpoint_result)
                
                if endpoint_result['success']:
                    self.success_count += 1
                    print(f"   ✅ API endpoint accessible: {endpoint}")
                else:
                    self.error_count += 1
                    print(f"   ❌ API endpoint failed: {endpoint}")
                
            except Exception as e:
                self.error_count += 1
                endpoint_result = {
                    'test_type': 'api_endpoint',
                    'endpoint': endpoint,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(endpoint_result)
                print(f"   ❌ API endpoint error: {endpoint} - {e}")
        
        return results

    def run_all_tests(self):
        """
        Run all simple mobile validation tests
        """
        print("\n🌍 SIMPLE MOBILE INTERFACE VALIDATION")
        print("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        # Test server availability
        print("\n🔌 Testing Server Availability...")
        server_result = self.test_server_availability()
        all_results.append(server_result)
        
        # Test mobile login pages
        print("\n📱 Testing Mobile Login Pages...")
        for device_name, user_agent in self.mobile_user_agents.items():
            login_result = self.test_mobile_login_page(device_name, user_agent)
            all_results.append(login_result)
        
        # Test CSS assets
        print("\n🎨 Testing CSS Assets...")
        css_results = self.test_css_assets()
        all_results.extend(css_results)
        
        # Test JS assets
        print("\n⚡ Testing JavaScript Assets...")
        js_results = self.test_js_assets()
        all_results.extend(js_results)
        
        # Test API endpoints
        print("\n🔌 Testing API Endpoints...")
        api_results = self.test_api_endpoints()
        all_results.extend(api_results)
        
        total_time = time.time() - start_time
        
        # Generate summary
        self.generate_summary_report(all_results, total_time)
        
        # Save detailed results
        self.save_detailed_results(all_results, total_time)
        
        return all_results

    def generate_summary_report(self, results, total_time):
        """
        Generate and display summary report
        """
        total_tests = len(results)
        successful_tests = len([r for r in results if r.get('success', False)])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 SIMPLE MOBILE VALIDATION SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {total_time:.2f}s")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🎯 Success Rate: {success_rate:.2f}%")
        
        # Categorize results
        test_categories = {}
        for result in results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_categories:
                test_categories[test_type] = {'total': 0, 'successful': 0}
            test_categories[test_type]['total'] += 1
            if result.get('success', False):
                test_categories[test_type]['successful'] += 1
        
        print(f"\n📈 Results by Test Type:")
        for test_type, stats in test_categories.items():
            cat_success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {test_type}: {cat_success_rate:.1f}% success, {stats['successful']}/{stats['total']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"🎉 EXCELLENT: Mobile interface validation passed")
        elif success_rate >= 75:
            print(f"✅ GOOD: Mobile interface mostly functional")
        elif success_rate >= 50:
            print(f"⚠️  WARNING: Mobile interface needs improvement")
        else:
            print(f"❌ CRITICAL: Mobile interface has serious issues")

    def save_detailed_results(self, results, total_time):
        """
        Save detailed test results to JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_data = {
            'test_execution': {
                'framework': 'simple_mobile_validator',
                'start_time': datetime.now().isoformat(),
                'duration_seconds': total_time,
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r.get('success', False)]),
                'failed_tests': len([r for r in results if not r.get('success', False)])
            },
            'mobile_user_agents': self.mobile_user_agents,
            'detailed_results': results,
            'summary': {
                'success_rate': (len([r for r in results if r.get('success', False)]) / len(results) * 100) if results else 0,
                'average_response_time': sum(r.get('response_time', 0) for r in results if 'response_time' in r) / len([r for r in results if 'response_time' in r]) if results else 0
            }
        }
        
        report_file = self.results_dir / f"simple_mobile_validation_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed report: {report_file}")

def main():
    """
    Main execution function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Mobile Interface Validation')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    validator = SimpleMobileValidator()
    results = validator.run_all_tests()
    
    return len([r for r in results if not r.get('success', False)]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
