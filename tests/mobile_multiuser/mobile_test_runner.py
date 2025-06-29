#!/usr/bin/env python3
"""
Universal Workshop ERP - Mobile Multi-User Test Runner
Orchestrates comprehensive mobile testing using both Selenium and Playwright
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class MobileMultiUserTestRunner:
    """
    Test runner for comprehensive mobile multi-user testing
    """
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results_dir = Path('test_results/mobile_multiuser')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Mobile Multi-User Test Runner Initialized")

    def check_dependencies(self):
        """
        Check if required testing dependencies are available
        """
        dependencies = {
            'selenium': False,
            'playwright': False,
            'chromedriver': False
        }
        
        # Check Python packages
        try:
            import selenium
            dependencies['selenium'] = True
        except ImportError:
            pass
        
        try:
            import playwright
            dependencies['playwright'] = True
        except ImportError:
            pass
        
        # Check ChromeDriver
        try:
            result = subprocess.run(['chromedriver', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                dependencies['chromedriver'] = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return dependencies

    def install_dependencies(self):
        """
        Install missing dependencies
        """
        print("\n📦 Installing missing dependencies...")
        
        dependencies = self.check_dependencies()
        
        # Install Python packages
        packages_to_install = []
        if not dependencies['selenium']:
            packages_to_install.append('selenium')
        if not dependencies['playwright']:
            packages_to_install.append('playwright')
        
        if packages_to_install:
            print(f"   Installing Python packages: {', '.join(packages_to_install)}")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + packages_to_install)
        
        # Install Playwright browsers if Playwright was installed
        if not dependencies['playwright']:
            print("   Installing Playwright browsers...")
            subprocess.run([sys.executable, '-m', 'playwright', 'install'])
        
        # ChromeDriver installation would depend on the system
        if not dependencies['chromedriver']:
            print("   ⚠️  ChromeDriver not found - Selenium tests may fail")
            print("   Please install ChromeDriver manually or use package manager")

    def run_selenium_tests(self, quick_mode=False):
        """
        Run Selenium-based mobile tests
        """
        print("\n🌐 Running Selenium Mobile Tests...")
        
        selenium_script = self.test_dir / 'mobile_multiuser_tester.py'
        
        cmd = [sys.executable, str(selenium_script)]
        if quick_mode:
            cmd.append('--quick')
        cmd.append('--verbose')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            selenium_results = {
                'framework': 'selenium',
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            print(f"   Selenium tests completed: {'✅' if result.returncode == 0 else '❌'}")
            if result.stdout:
                print("   Output preview:")
                print("   " + "\n   ".join(result.stdout.split('\n')[-10:]))  # Last 10 lines
            
            return selenium_results
            
        except subprocess.TimeoutExpired:
            print("   ❌ Selenium tests timed out")
            return {
                'framework': 'selenium',
                'success': False,
                'error': 'Test execution timed out',
                'return_code': -1
            }
        except Exception as e:
            print(f"   ❌ Error running Selenium tests: {e}")
            return {
                'framework': 'selenium',
                'success': False,
                'error': str(e),
                'return_code': -1
            }

    def run_playwright_tests(self, quick_mode=False):
        """
        Run Playwright-based mobile tests
        """
        print("\n🎭 Running Playwright Mobile Tests...")
        
        playwright_script = self.test_dir / 'playwright_mobile_tester.py'
        
        cmd = [sys.executable, str(playwright_script)]
        if quick_mode:
            cmd.append('--quick')
        cmd.append('--verbose')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            playwright_results = {
                'framework': 'playwright',
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            print(f"   Playwright tests completed: {'✅' if result.returncode == 0 else '❌'}")
            if result.stdout:
                print("   Output preview:")
                print("   " + "\n   ".join(result.stdout.split('\n')[-10:]))  # Last 10 lines
            
            return playwright_results
            
        except subprocess.TimeoutExpired:
            print("   ❌ Playwright tests timed out")
            return {
                'framework': 'playwright',
                'success': False,
                'error': 'Test execution timed out',
                'return_code': -1
            }
        except Exception as e:
            print(f"   ❌ Error running Playwright tests: {e}")
            return {
                'framework': 'playwright',
                'success': False,
                'error': str(e),
                'return_code': -1
            }

    def run_integration_validation(self):
        """
        Run integration validation tests
        """
        print("\n🔗 Running Integration Validation...")
        
        validation_results = {
            'server_availability': False,
            'login_page_accessible': False,
            'css_assets_loaded': False,
            'js_assets_loaded': False
        }
        
        try:
            import requests
            
            # Check server availability
            response = requests.get('http://localhost:8000', timeout=10)
            validation_results['server_availability'] = response.status_code in [200, 302]
            
            # Check login page
            login_response = requests.get('http://localhost:8000/login', timeout=10)
            validation_results['login_page_accessible'] = login_response.status_code == 200
            
            # Check CSS assets
            css_urls = [
                'http://localhost:8000/assets/universal_workshop/css/arabic-rtl.css',
                'http://localhost:8000/assets/universal_workshop/css/dynamic_branding.css'
            ]
            
            css_loaded = 0
            for url in css_urls:
                try:
                    css_response = requests.get(url, timeout=5)
                    if css_response.status_code == 200:
                        css_loaded += 1
                except:
                    pass
            
            validation_results['css_assets_loaded'] = css_loaded > 0
            
            # Check JS assets
            js_urls = [
                'http://localhost:8000/assets/universal_workshop/js/rtl_branding_manager.js'
            ]
            
            js_loaded = 0
            for url in js_urls:
                try:
                    js_response = requests.get(url, timeout=5)
                    if js_response.status_code == 200:
                        js_loaded += 1
                except:
                    pass
            
            validation_results['js_assets_loaded'] = js_loaded > 0
            
        except Exception as e:
            print(f"   ⚠️  Integration validation error: {e}")
        
        # Display results
        for check, status in validation_results.items():
            print(f"   {check}: {'✅' if status else '❌'}")
        
        return validation_results

    def generate_combined_report(self, selenium_results, playwright_results, validation_results):
        """
        Generate combined test report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        combined_report = {
            'test_execution': {
                'timestamp': datetime.now().isoformat(),
                'test_suite': 'mobile_multiuser_comprehensive',
                'frameworks_used': ['selenium', 'playwright']
            },
            'integration_validation': validation_results,
            'selenium_results': selenium_results,
            'playwright_results': playwright_results,
            'summary': {
                'selenium_success': selenium_results.get('success', False),
                'playwright_success': playwright_results.get('success', False),
                'integration_valid': all(validation_results.values()),
                'overall_success': (
                    selenium_results.get('success', False) and 
                    playwright_results.get('success', False) and 
                    all(validation_results.values())
                )
            }
        }
        
        report_file = self.results_dir / f"mobile_multiuser_combined_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(combined_report, f, indent=2, ensure_ascii=False)
        
        return report_file, combined_report

    def run_comprehensive_tests(self, quick_mode=False, install_deps=False):
        """
        Run comprehensive mobile multi-user testing
        """
        print("\n🌍 COMPREHENSIVE MOBILE MULTI-USER TESTING SUITE")
        print("=" * 60)
        
        # Check and optionally install dependencies
        dependencies = self.check_dependencies()
        print(f"\n📋 Dependency Status:")
        for dep, available in dependencies.items():
            print(f"   {dep}: {'✅' if available else '❌'}")
        
        if install_deps and not all(dependencies.values()):
            self.install_dependencies()
        
        # Run integration validation
        validation_results = self.run_integration_validation()
        
        # Run Selenium tests
        selenium_results = self.run_selenium_tests(quick_mode)
        
        # Run Playwright tests
        playwright_results = self.run_playwright_tests(quick_mode)
        
        # Generate combined report
        report_file, combined_report = self.generate_combined_report(
            selenium_results, playwright_results, validation_results
        )
        
        # Display summary
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"🔗 Integration Validation: {'✅' if all(validation_results.values()) else '❌'}")
        print(f"🌐 Selenium Tests: {'✅' if selenium_results.get('success', False) else '❌'}")
        print(f"🎭 Playwright Tests: {'✅' if playwright_results.get('success', False) else '❌'}")
        print(f"🎯 Overall Success: {'✅' if combined_report['summary']['overall_success'] else '❌'}")
        print(f"📄 Combined Report: {report_file}")
        
        return combined_report['summary']['overall_success']

def main():
    """
    Main execution function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Mobile Multi-User Testing Suite Runner')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--install-deps', action='store_true', help='Install missing dependencies')
    parser.add_argument('--selenium-only', action='store_true', help='Run only Selenium tests')
    parser.add_argument('--playwright-only', action='store_true', help='Run only Playwright tests')
    
    args = parser.parse_args()
    
    runner = MobileMultiUserTestRunner()
    
    if args.selenium_only:
        result = runner.run_selenium_tests(args.quick)
        return result.get('success', False)
    elif args.playwright_only:
        result = runner.run_playwright_tests(args.quick)
        return result.get('success', False)
    else:
        return runner.run_comprehensive_tests(args.quick, args.install_deps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
