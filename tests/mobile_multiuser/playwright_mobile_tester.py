#!/usr/bin/env python3
"""
Universal Workshop ERP - Playwright Mobile Multi-User Testing Suite
Modern mobile testing with Playwright for Arabic RTL, authentication, and concurrent sessions
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add path for potential frappe/erpnext modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

class PlaywrightMobileMultiUserTester:
    """
    Modern mobile multi-user testing with Playwright
    """
    
    def __init__(self):
        self.test_results = []
        self.error_count = 0
        self.success_count = 0
        self.session_failures = 0
        
        # Playwright device configurations
        self.devices = [
            'iPhone 13',
            'iPhone 13 Pro',
            'iPhone 12',
            'Pixel 5',
            'Galaxy S8',
            'iPad Pro',
            'Desktop Chrome',
            'Desktop Firefox'
        ]
        
        # Test user configurations for concurrent testing
        self.test_users = [
            {'username': 'test_admin_pw', 'password': 'admin123', 'role': 'Workshop Admin'},
            {'username': 'test_tech_pw', 'password': 'tech123', 'role': 'Technician'},
            {'username': 'test_cs_pw', 'password': 'cs123', 'role': 'Customer Service'},
            {'username': 'test_inv_pw', 'password': 'inv123', 'role': 'Inventory Manager'},
            {'username': 'test_owner_pw', 'password': 'owner123', 'role': 'Workshop Owner'}
        ]
        
        # Base URL for testing
        self.base_url = 'http://localhost:8000'
        
        # Initialize report storage
        self.results_dir = Path('test_results/mobile_multiuser')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🎭 Playwright Mobile Multi-User Tester Initialized")
        print(f"🔧 Playwright available: {HAS_PLAYWRIGHT}")
        print(f"📱 Devices configured: {len(self.devices)}")
        print(f"👥 Test users configured: {len(self.test_users)}")

    async def test_mobile_device_rtl(self, browser, device_name):
        """
        Test RTL interface on specific mobile device
        """
        start_time = time.time()
        
        try:
            # Create context with device emulation and Arabic locale
            context = await browser.new_context(
                **browser.devices[device_name],
                locale='ar-EG',
                timezone_id='Asia/Dubai'
            )
            
            page = await context.new_page()
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check RTL layout
            body = page.locator('body')
            body_dir = await body.get_attribute('dir')
            body_class = await body.get_attribute('class')
            
            # Check language setting
            html_lang = await page.locator('html').get_attribute('lang')
            
            # Measure viewport and check responsiveness
            viewport_size = page.viewport_size
            
            # Check for touch-friendly elements
            buttons = page.locator('button')
            button_count = await buttons.count()
            
            # Take screenshot for visual validation
            screenshot_path = self.results_dir / f"rtl_{device_name.replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)
            
            # Check for Arabic content
            arabic_text_present = await page.locator('text=/[\u0600-\u06FF]/').count() > 0
            
            await context.close()
            
            processing_time = time.time() - start_time
            
            result = {
                'test_type': 'mobile_rtl',
                'device': device_name,
                'body_dir': body_dir,
                'body_class': body_class,
                'html_lang': html_lang,
                'viewport': viewport_size,
                'button_count': button_count,
                'arabic_text_present': arabic_text_present,
                'screenshot_saved': str(screenshot_path),
                'processing_time': processing_time,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            self.success_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            return {
                'test_type': 'mobile_rtl',
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    async def test_concurrent_login_session(self, browser, user, device_name, session_id):
        """
        Test individual user login in concurrent scenario using Playwright
        """
        start_time = time.time()
        
        try:
            # Create isolated context for this user session
            context = await browser.new_context(
                **browser.devices[device_name],
                locale='ar-EG'
            )
            
            page = await context.new_page()
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Fill login form
            await page.fill('input[name="usr"]', user['username'])
            await page.fill('input[name="pwd"]', user['password'])
            
            # Submit login
            await page.click('button[type="submit"]')
            
            # Wait for navigation or error
            try:
                await page.wait_for_url('**/app**', timeout=10000)
                login_successful = True
                current_url = page.url
            except:
                login_successful = False
                current_url = page.url
            
            # Test session persistence if login was successful
            session_valid = False
            if login_successful:
                # Navigate to different pages to test session
                await page.goto(f"{self.base_url}/app/desk")
                await page.wait_for_load_state('networkidle', timeout=5000)
                
                # Check if still authenticated
                session_valid = '/login' not in page.url
                
                # Test Arabic interface elements in authenticated state
                await page.goto(f"{self.base_url}/app")
                arabic_elements = await page.locator('text=/[\u0600-\u06FF]/').count()
                
                # Take screenshot of authenticated session
                screenshot_path = self.results_dir / f"session_{session_id}_{device_name.replace(' ', '_')}.png"
                await page.screenshot(path=screenshot_path)
            
            await context.close()
            
            processing_time = time.time() - start_time
            
            result = {
                'test_type': 'concurrent_session',
                'session_id': session_id,
                'username': user['username'],
                'role': user['role'],
                'device': device_name,
                'login_successful': login_successful,
                'session_valid': session_valid,
                'current_url': current_url,
                'processing_time': processing_time,
                'success': login_successful and session_valid,
                'timestamp': datetime.now().isoformat()
            }
            
            if login_successful and session_valid:
                self.success_count += 1
            else:
                self.error_count += 1
                self.session_failures += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.session_failures += 1
            return {
                'test_type': 'concurrent_session',
                'session_id': session_id,
                'username': user['username'],
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    async def test_responsive_design(self, browser, device_name):
        """
        Test responsive design characteristics
        """
        start_time = time.time()
        
        try:
            context = await browser.new_context(**browser.devices[device_name])
            page = await context.new_page()
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Get viewport information
            viewport = page.viewport_size
            
            # Check for horizontal scroll
            scroll_width = await page.evaluate('document.documentElement.scrollWidth')
            client_width = await page.evaluate('document.documentElement.clientWidth')
            has_horizontal_scroll = scroll_width > client_width
            
            # Check touch target sizes
            buttons = page.locator('button, a, input[type="button"], input[type="submit"]')
            button_count = await buttons.count()
            
            touch_friendly_count = 0
            for i in range(min(button_count, 10)):  # Check first 10 buttons
                button = buttons.nth(i)
                if await button.is_visible():
                    box = await button.bounding_box()
                    if box and box['height'] >= 44 and box['width'] >= 44:
                        touch_friendly_count += 1
            
            # Test navigation elements
            nav_elements = await page.locator('nav, .navbar, .navigation').count()
            
            await context.close()
            
            processing_time = time.time() - start_time
            
            result = {
                'test_type': 'responsive_design',
                'device': device_name,
                'viewport': viewport,
                'has_horizontal_scroll': has_horizontal_scroll,
                'total_buttons': button_count,
                'touch_friendly_buttons': touch_friendly_count,
                'touch_friendly_ratio': touch_friendly_count / max(button_count, 1),
                'nav_elements': nav_elements,
                'processing_time': processing_time,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            self.success_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            return {
                'test_type': 'responsive_design',
                'device': device_name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }

    async def run_mobile_device_tests(self, browser):
        """
        Run tests across multiple mobile devices
        """
        print("\n📱 Testing Mobile Devices...")
        device_results = []
        
        # Test subset of devices for responsiveness and RTL
        mobile_devices = [d for d in self.devices if 'iPhone' in d or 'Pixel' in d or 'Galaxy' in d]
        
        for device_name in mobile_devices[:4]:  # Test first 4 mobile devices
            print(f"   📱 Testing {device_name}...")
            
            # Test RTL interface
            rtl_result = await self.test_mobile_device_rtl(browser, device_name)
            device_results.append(rtl_result)
            
            # Test responsive design
            responsive_result = await self.test_responsive_design(browser, device_name)
            device_results.append(responsive_result)
        
        return device_results

    async def run_concurrent_session_tests(self, browser):
        """
        Run concurrent user session tests
        """
        print("\n👥 Testing Concurrent Sessions...")
        
        # Create tasks for concurrent execution
        tasks = []
        for i, user in enumerate(self.test_users):
            device_name = self.devices[i % len(self.devices)]
            if 'iPhone' in device_name or 'Pixel' in device_name:  # Use mobile devices
                task = self.test_concurrent_login_session(browser, user, device_name, i)
                tasks.append(task)
        
        # Execute concurrent sessions
        session_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(session_results):
            if isinstance(result, Exception):
                error_result = {
                    'test_type': 'concurrent_session',
                    'session_id': i,
                    'success': False,
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                }
                processed_results.append(error_result)
                self.error_count += 1
            else:
                processed_results.append(result)
        
        return processed_results

    async def run_all_tests(self, quick_mode=False):
        """
        Run comprehensive Playwright mobile testing suite
        """
        print("\n🎭 PLAYWRIGHT MOBILE MULTI-USER TESTING")
        print("=" * 60)
        
        if not HAS_PLAYWRIGHT:
            print("❌ Playwright not available - cannot run tests")
            return []
        
        start_time = time.time()
        all_results = []
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            # Run mobile device tests
            device_results = await self.run_mobile_device_tests(browser)
            all_results.extend(device_results)
            
            if not quick_mode:
                # Run concurrent session tests
                session_results = await self.run_concurrent_session_tests(browser)
                all_results.extend(session_results)
            else:
                print("\n⚡ Quick mode: Skipping concurrent session tests")
            
            await browser.close()
        
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
        
        print(f"\n📊 PLAYWRIGHT MOBILE TEST SUMMARY")
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
            success_rate_cat = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {test_type}: {success_rate_cat:.1f}% success, {stats['successful']}/{stats['total']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"🎉 EXCELLENT: Playwright mobile testing results")
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
                'framework': 'playwright',
                'start_time': datetime.now().isoformat(),
                'duration_seconds': total_time,
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r.get('success', False)]),
                'failed_tests': len([r for r in results if not r.get('success', False)]),
                'session_failures': self.session_failures
            },
            'devices_tested': self.devices,
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
        
        report_file = self.results_dir / f"playwright_mobile_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed report: {report_file}")

async def main():
    """
    Main execution function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Playwright Mobile Multi-User Interface Testing')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = PlaywrightMobileMultiUserTester()
    results = await tester.run_all_tests(quick_mode=args.quick)
    
    return len([r for r in results if not r.get('success', False)]) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
