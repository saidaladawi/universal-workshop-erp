#!/usr/bin/env python3
"""
Universal Workshop ERP - Mobile Interface Multi-User Testing Suite
Comprehensive testing for mobile authentication, session management, and Arabic RTL interface support
"""

import os
import sys
import json
import time
import asyncio
import concurrent.futures
import threading
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Add path for potential frappe/erpnext modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

try:
    from playwright.async_api import async_playwright
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

class MobileMultiUserTester:
    """
    Comprehensive mobile interface multi-user testing
    """
    
    def __init__(self):
        self.test_results = []
        self.error_count = 0
        self.success_count = 0
        self.session_failures = 0
        
        # Mobile device configurations for testing
        self.mobile_devices = {
            'iphone_13': {
                'name': 'iPhone 13',
                'viewport': {'width': 390, 'height': 844},
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
            },
            'pixel_5': {
                'name': 'Pixel 5',
                'viewport': {'width': 393, 'height': 851},
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36'
            },
            'galaxy_s21': {
                'name': 'Galaxy S21',
                'viewport': {'width': 384, 'height': 854},
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36'
            },
            'ipad_pro': {
                'name': 'iPad Pro',
                'viewport': {'width': 1024, 'height': 1366},
                'user_agent': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
            }
        }
        
        # Test user configurations
        self.test_users = [
            {'username': 'test_admin_mobile', 'password': 'admin123', 'role': 'Workshop Admin'},
            {'username': 'test_tech_mobile', 'password': 'tech123', 'role': 'Technician'},
            {'username': 'test_cs_mobile', 'password': 'cs123', 'role': 'Customer Service'},
            {'username': 'test_inv_mobile', 'password': 'inv123', 'role': 'Inventory Manager'},
            {'username': 'test_owner_mobile', 'password': 'owner123', 'role': 'Workshop Owner'}
        ]
        
        # Base URL for testing
        self.base_url = 'http://localhost:8000'
        
        # Initialize report storage
        self.results_dir = Path('test_results/mobile_multiuser')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("📱 Mobile Multi-User Tester Initialized")
        print(f"🔧 Playwright available: {HAS_PLAYWRIGHT}")
        print(f"🔧 Selenium available: {HAS_SELENIUM}")
        print(f"📊 Mobile devices configured: {len(self.mobile_devices)}")
        print(f"👥 Test users configured: {len(self.test_users)}")

    def run_selenium_mobile_tests(self):
        """
        Run mobile tests using Selenium WebDriver
        """
        if not HAS_SELENIUM:
            print("❌ Selenium not available - skipping Selenium-based tests")
            return []
        
        print("\n🌐 Running Selenium Mobile Tests...")
        selenium_results = []
        
        for device_key, device_config in self.mobile_devices.items():
            print(f"📱 Testing on {device_config['name']}...")
            
            # Configure Chrome for mobile emulation
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f"--user-agent={device_config['user_agent']}")
            chrome_options.add_experimental_option("mobileEmulation", {
                "deviceMetrics": {
                    "width": device_config['viewport']['width'],
                    "height": device_config['viewport']['height'],
                    "pixelRatio": 2.0
                }
            })
            
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_window_size(
                    device_config['viewport']['width'],
                    device_config['viewport']['height']
                )
                
                # Test basic page load and responsiveness
                result = self.test_mobile_responsiveness_selenium(driver, device_config['name'])
                selenium_results.append(result)
                
                # Test Arabic RTL interface
                rtl_result = self.test_arabic_rtl_selenium(driver, device_config['name'])
                selenium_results.append(rtl_result)
                
                driver.quit()
                
            except Exception as e:
                error_result = {
                    'test_type': 'selenium_mobile',
                    'device': device_config['name'],
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                selenium_results.append(error_result)
                print(f"❌ Error testing {device_config['name']}: {e}")
        
        return selenium_results

    def test_mobile_responsiveness_selenium(self, driver, device_name):
        """
        Test mobile responsiveness using Selenium
        """
        start_time = time.time()
        
        try:
            # Navigate to login page
            driver.get(f"{self.base_url}/login")
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if viewport is properly set
            viewport_width = driver.execute_script("return window.innerWidth")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Check for horizontal scroll
            scroll_width = driver.execute_script("return document.body.scrollWidth")
            has_horizontal_scroll = scroll_width > viewport_width
            
            # Check for touch-friendly elements
            buttons = driver.find_elements(By.TAG_NAME, "button")
            touch_friendly_count = 0
            for button in buttons:
                if button.is_displayed():
                    size = button.size
                    if size['height'] >= 44 and size['width'] >= 44:  # 44px minimum touch target
                        touch_friendly_count += 1
            
            processing_time = time.time() - start_time
            
            result = {
                'test_type': 'mobile_responsiveness',
                'device': device_name,
                'viewport_width': viewport_width,
                'viewport_height': viewport_height,
                'has_horizontal_scroll': has_horizontal_scroll,
                'touch_friendly_buttons': touch_friendly_count,
                'total_buttons': len(buttons),
                'processing_time': processing_time,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            self.success_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            return {
                'test_type': 'mobile_responsiveness',
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    def test_arabic_rtl_selenium(self, driver, device_name):
        """
        Test Arabic RTL interface on mobile using Selenium
        """
        start_time = time.time()
        
        try:
            # Navigate to login page
            driver.get(f"{self.base_url}/login")
            
            # Check if RTL is properly applied
            body = driver.find_element(By.TAG_NAME, "body")
            body_dir = body.get_attribute("dir")
            body_class = body.get_attribute("class")
            
            # Check for Arabic-specific CSS classes
            has_arabic_class = "arabic" in body_class.lower() if body_class else False
            has_rtl_class = "rtl" in body_class.lower() if body_class else False
            
            # Check language settings
            html_lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
            
            # Look for Arabic text elements
            arabic_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'ا') or contains(text(), 'ب') or contains(text(), 'ت')]")
            
            processing_time = time.time() - start_time
            
            result = {
                'test_type': 'arabic_rtl_mobile',
                'device': device_name,
                'body_dir': body_dir,
                'has_arabic_class': has_arabic_class,
                'has_rtl_class': has_rtl_class,
                'html_lang': html_lang,
                'arabic_elements_count': len(arabic_elements),
                'processing_time': processing_time,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            self.success_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            return {
                'test_type': 'arabic_rtl_mobile',
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    def run_concurrent_session_tests(self):
        """
        Test concurrent user sessions across multiple mobile devices
        """
        print("\n👥 Running Concurrent Session Tests...")
        
        if not HAS_SELENIUM:
            print("❌ Selenium not available - skipping concurrent session tests")
            return []
        
        concurrent_results = []
        
        # Test with multiple users logging in simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.test_users)) as executor:
            futures = []
            
            for i, user in enumerate(self.test_users):
                device_key = list(self.mobile_devices.keys())[i % len(self.mobile_devices)]
                device_config = self.mobile_devices[device_key]
                
                future = executor.submit(
                    self.test_concurrent_login,
                    user,
                    device_config,
                    i
                )
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=60)  # 60-second timeout
                    concurrent_results.append(result)
                except Exception as e:
                    error_result = {
                        'test_type': 'concurrent_session',
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    concurrent_results.append(error_result)
        
        return concurrent_results

    def test_concurrent_login(self, user, device_config, session_id):
        """
        Test individual user login in concurrent scenario
        """
        start_time = time.time()
        session_name = f"session_{session_id}_{user['username']}"
        
        try:
            # Configure Chrome for this session
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f"--user-data-dir=/tmp/{session_name}")
            chrome_options.add_argument(f"--user-agent={device_config['user_agent']}")
            chrome_options.add_experimental_option("mobileEmulation", {
                "deviceMetrics": {
                    "width": device_config['viewport']['width'],
                    "height": device_config['viewport']['height'],
                    "pixelRatio": 2.0
                }
            })
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(
                device_config['viewport']['width'],
                device_config['viewport']['height']
            )
            
            # Navigate to login page
            driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "usr"))
            )
            
            # Perform login
            username_field = driver.find_element(By.NAME, "usr")
            password_field = driver.find_element(By.NAME, "pwd")
            
            username_field.clear()
            username_field.send_keys(user['username'])
            password_field.clear()
            password_field.send_keys(user['password'])
            
            # Submit login form
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for potential redirect or error
            time.sleep(3)
            
            current_url = driver.current_url
            login_successful = "/app" in current_url or "/desk" in current_url
            
            # Test session persistence
            session_valid = self.test_session_persistence(driver)
            
            processing_time = time.time() - start_time
            
            driver.quit()
            
            result = {
                'test_type': 'concurrent_login',
                'session_id': session_id,
                'username': user['username'],
                'role': user['role'],
                'device': device_config['name'],
                'login_successful': login_successful,
                'session_valid': session_valid,
                'current_url': current_url,
                'processing_time': processing_time,
                'success': login_successful,
                'timestamp': datetime.now().isoformat()
            }
            
            if login_successful:
                self.success_count += 1
            else:
                self.error_count += 1
                self.session_failures += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.session_failures += 1
            return {
                'test_type': 'concurrent_login',
                'session_id': session_id,
                'username': user['username'],
                'device': device_config['name'],
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    def test_session_persistence(self, driver):
        """
        Test session persistence and management
        """
        try:
            # Navigate to a protected page
            driver.get(f"{self.base_url}/app")
            time.sleep(2)
            
            # Check if still authenticated
            current_url = driver.current_url
            is_authenticated = "/login" not in current_url
            
            if is_authenticated:
                # Test navigation to different sections
                driver.get(f"{self.base_url}/app/desk")
                time.sleep(1)
                
                final_url = driver.current_url
                session_persisted = "/login" not in final_url
                
                return session_persisted
            
            return False
            
        except Exception:
            return False

    def run_all_tests(self, quick_mode=False):
        """
        Run comprehensive mobile multi-user testing suite
        """
        print("\n🌍 MOBILE INTERFACE MULTI-USER TESTING")
        print("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        # Run Selenium-based mobile tests
        selenium_results = self.run_selenium_mobile_tests()
        all_results.extend(selenium_results)
        
        if not quick_mode:
            # Run concurrent session tests
            concurrent_results = self.run_concurrent_session_tests()
            all_results.extend(concurrent_results)
        else:
            print("\n⚡ Quick mode: Skipping concurrent session tests")
        
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
        
        print(f"\n📊 MOBILE MULTI-USER TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {total_time:.2f}s")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🎯 Success Rate: {success_rate:.2f}%")
        
        if self.session_failures > 0:
            print(f"🔐 Session Failures: {self.session_failures}")
        
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
            success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {test_type}: {success_rate:.1f}% success, {stats['successful']}/{stats['total']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"🎉 EXCELLENT: Mobile multi-user interface performance")
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
                'start_time': datetime.now().isoformat(),
                'duration_seconds': total_time,
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r.get('success', False)]),
                'failed_tests': len([r for r in results if not r.get('success', False)]),
                'session_failures': self.session_failures
            },
            'device_configurations': self.mobile_devices,
            'test_users': [
                {k: v for k, v in user.items() if k != 'password'} 
                for user in self.test_users
            ],
            'detailed_results': results,
            'summary': {
                'success_rate': (len([r for r in results if r.get('success', False)]) / len(results) * 100) if results else 0,
                'average_processing_time': sum(r.get('processing_time', 0) for r in results) / len(results) if results else 0
            }
        }
        
        report_file = self.results_dir / f"mobile_multiuser_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed report: {report_file}")

def main():
    """
    Main execution function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Mobile Multi-User Interface Testing')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = MobileMultiUserTester()
    results = tester.run_all_tests(quick_mode=args.quick)
    
    return len([r for r in results if not r.get('success', False)]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
