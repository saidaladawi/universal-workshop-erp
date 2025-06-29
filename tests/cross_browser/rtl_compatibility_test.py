#!/usr/bin/env python3
"""
Universal Workshop ERP - Cross-Browser RTL Compatibility Test System
Tests authentication flow and Arabic RTL interface across Chrome, Firefox, Edge, and Safari
"""

import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common.exceptions import TimeoutException, WebDriverException


class RTLCompatibilityTester:
    """Cross-browser RTL compatibility testing for Universal Workshop ERP"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "browsers": {},
            "rtl_issues": [],
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Test scenarios for different user roles
        self.test_scenarios = {
            "workshop_owner": {
                "username": "workshop.owner@test.com",
                "password": "test123",
                "expected_redirect": "/universal-workshop-dashboard",
                "role": "Workshop Owner"
            },
            "workshop_manager": {
                "username": "workshop.manager@test.com", 
                "password": "test123",
                "expected_redirect": "/app/workspace/Workshop%20Management",
                "role": "Workshop Manager"
            },
            "technician": {
                "username": "technician@test.com",
                "password": "test123", 
                "expected_redirect": "/technician",
                "role": "Workshop Technician"
            },
            "customer": {
                "username": "customer@test.com",
                "password": "test123",
                "expected_redirect": "/customer-portal",
                "role": "Customer"
            }
        }
        
        # RTL validation points
        self.rtl_validation_points = {
            "login_page": [
                ("body", "direction", "rtl"),
                (".login-form", "text-align", "right"),
                (".form-control", "text-align", "right"),
                (".btn-login", "font-family", "Tajawal"),
                (".login-header", "text-align", "center")
            ],
            "dashboard": [
                (".workshop-dashboard", "direction", "rtl"),
                (".workshop-card", "text-align", "right"),
                (".navbar", "direction", "rtl"),
                (".sidebar", "right", "0"),
                (".dropdown-menu", "text-align", "right")
            ],
            "forms": [
                (".form-control", "text-align", "right"),
                (".form-label", "text-align", "right"),
                (".input-group", "flex-direction", "row-reverse"),
                ("select.form-control", "background-position", "left"),
                (".form-check", "text-align", "right")
            ]
        }

    def setup_browser(self, browser_name):
        """Setup browser drivers with Arabic language preferences"""
        try:
            if browser_name == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--lang=ar")
                options.add_experimental_option("prefs", {
                    "intl.accept_languages": "ar,ar-SA,en",
                    "profile.default_content_setting_values.geolocation": 2
                })
                return webdriver.Chrome(options=options)
                
            elif browser_name == "firefox":
                options = FirefoxOptions()
                options.add_argument("--headless")
                options.set_preference("intl.locale.requested", "ar")
                options.set_preference("intl.accept_languages", "ar,ar-SA,en")
                return webdriver.Firefox(options=options)
                
            elif browser_name == "edge":
                options = EdgeOptions()
                options.add_argument("--headless")
                options.add_argument("--lang=ar")
                options.add_experimental_option("prefs", {
                    "intl.accept_languages": "ar,ar-SA,en"
                })
                return webdriver.Edge(options=options)
                
            elif browser_name == "safari":
                # Safari doesn't support headless mode in Selenium
                options = SafariOptions()
                return webdriver.Safari(options=options)
                
        except WebDriverException as e:
            print(f"Failed to setup {browser_name}: {e}")
            return None

    def validate_rtl_styling(self, driver, page_type):
        """Validate RTL styling for specific page type"""
        rtl_issues = []
        validation_points = self.rtl_validation_points.get(page_type, [])
        
        for selector, property_name, expected_value in validation_points:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                actual_value = driver.execute_script(
                    f"return window.getComputedStyle(arguments[0]).{property_name}",
                    element
                )
                
                if expected_value.lower() not in actual_value.lower():
                    rtl_issues.append({
                        "selector": selector,
                        "property": property_name,
                        "expected": expected_value,
                        "actual": actual_value,
                        "page": page_type
                    })
                    
            except Exception as e:
                rtl_issues.append({
                    "selector": selector,
                    "property": property_name,
                    "error": str(e),
                    "page": page_type
                })
                
        return rtl_issues

    def test_login_flow(self, driver, scenario_name, scenario_data):
        """Test login flow with RTL validation"""
        results = {
            "login_success": False,
            "redirect_success": False,
            "rtl_validation": True,
            "performance": {},
            "issues": []
        }
        
        try:
            # Navigate to login page with Arabic language
            start_time = time.time()
            driver.get(f"{self.base_url}/login?lang=ar")
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "login-form"))
            )
            load_time = time.time() - start_time
            results["performance"]["page_load_time"] = load_time
            
            # Validate RTL styling on login page
            rtl_issues = self.validate_rtl_styling(driver, "login_page")
            if rtl_issues:
                results["rtl_validation"] = False
                results["issues"].extend(rtl_issues)
            
            # Fill login form
            username_field = driver.find_element(By.NAME, "usr")
            password_field = driver.find_element(By.NAME, "pwd")
            login_button = driver.find_element(By.CSS_SELECTOR, ".btn-login")
            
            # Validate form field RTL alignment
            username_align = driver.execute_script(
                "return window.getComputedStyle(arguments[0]).textAlign", 
                username_field
            )
            if username_align != "right":
                results["issues"].append({
                    "type": "form_alignment",
                    "field": "username",
                    "expected": "right",
                    "actual": username_align
                })
            
            # Perform login
            username_field.send_keys(scenario_data["username"])
            password_field.send_keys(scenario_data["password"])
            
            start_time = time.time()
            login_button.click()
            
            # Wait for redirect
            try:
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.current_url != f"{self.base_url}/login"
                )
                login_time = time.time() - start_time
                results["performance"]["login_time"] = login_time
                results["login_success"] = True
                
                # Check if redirected to expected page
                current_url = driver.current_url
                expected_redirect = scenario_data["expected_redirect"]
                
                if expected_redirect in current_url:
                    results["redirect_success"] = True
                    
                    # Validate RTL styling on dashboard/destination page
                    if "dashboard" in expected_redirect or "app" in expected_redirect:
                        dashboard_rtl_issues = self.validate_rtl_styling(driver, "dashboard")
                        if dashboard_rtl_issues:
                            results["rtl_validation"] = False
                            results["issues"].extend(dashboard_rtl_issues)
                else:
                    results["issues"].append({
                        "type": "redirect_failure",
                        "expected": expected_redirect,
                        "actual": current_url
                    })
                    
            except TimeoutException:
                results["issues"].append({
                    "type": "login_timeout",
                    "message": "Login process timed out"
                })
                
        except Exception as e:
            results["issues"].append({
                "type": "general_error",
                "message": str(e)
            })
            
        return results

    def test_session_management_rtl(self, driver):
        """Test session management with RTL interface"""
        results = {
            "session_persistence": False,
            "rtl_consistency": True,
            "performance": {},
            "issues": []
        }
        
        try:
            # Navigate between pages to test session persistence
            test_pages = [
                "/universal-workshop-dashboard?lang=ar",
                "/app/Customer?lang=ar", 
                "/technician?lang=ar"
            ]
            
            for page in test_pages:
                try:
                    start_time = time.time()
                    driver.get(f"{self.base_url}{page}")
                    
                    # Wait for page load
                    WebDriverWait(driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    
                    load_time = time.time() - start_time
                    results["performance"][f"page_load_{page.split('/')[-1]}"] = load_time
                    
                    # Check if still authenticated (not redirected to login)
                    if "/login" not in driver.current_url:
                        results["session_persistence"] = True
                    
                    # Validate RTL consistency across pages
                    body_direction = driver.execute_script(
                        "return window.getComputedStyle(document.body).direction"
                    )
                    if body_direction != "rtl":
                        results["rtl_consistency"] = False
                        results["issues"].append({
                            "page": page,
                            "type": "rtl_inconsistency",
                            "expected": "rtl",
                            "actual": body_direction
                        })
                        
                except Exception as e:
                    results["issues"].append({
                        "page": page,
                        "type": "navigation_error",
                        "message": str(e)
                    })
                    
        except Exception as e:
            results["issues"].append({
                "type": "session_test_error",
                "message": str(e)
            })
            
        return results

    def test_responsive_rtl(self, driver):
        """Test RTL responsiveness across different screen sizes"""
        results = {
            "responsive_rtl": True,
            "breakpoint_tests": {},
            "issues": []
        }
        
        # Test common responsive breakpoints
        breakpoints = {
            "mobile": (375, 667),
            "tablet": (768, 1024), 
            "desktop": (1920, 1080)
        }
        
        for breakpoint_name, (width, height) in breakpoints.items():
            try:
                driver.set_window_size(width, height)
                time.sleep(1)  # Allow layout to adjust
                
                # Check RTL layout at this breakpoint
                body_direction = driver.execute_script(
                    "return window.getComputedStyle(document.body).direction"
                )
                
                # Check for horizontal scrolling (layout overflow)
                scroll_width = driver.execute_script("return document.body.scrollWidth")
                client_width = driver.execute_script("return document.body.clientWidth")
                
                breakpoint_result = {
                    "rtl_direction": body_direction == "rtl",
                    "no_horizontal_overflow": scroll_width <= client_width + 20,  # 20px tolerance
                    "viewport": f"{width}x{height}"
                }
                
                if not breakpoint_result["rtl_direction"]:
                    results["responsive_rtl"] = False
                    results["issues"].append({
                        "breakpoint": breakpoint_name,
                        "type": "rtl_direction_lost",
                        "viewport": f"{width}x{height}"
                    })
                
                if not breakpoint_result["no_horizontal_overflow"]:
                    results["responsive_rtl"] = False
                    results["issues"].append({
                        "breakpoint": breakpoint_name,
                        "type": "horizontal_overflow",
                        "scroll_width": scroll_width,
                        "client_width": client_width,
                        "viewport": f"{width}x{height}"
                    })
                
                results["breakpoint_tests"][breakpoint_name] = breakpoint_result
                
            except Exception as e:
                results["issues"].append({
                    "breakpoint": breakpoint_name,
                    "type": "responsive_test_error",
                    "message": str(e)
                })
        
        return results

    def test_browser_compatibility(self, browser_name):
        """Test complete RTL compatibility for a specific browser"""
        print(f"Testing {browser_name.upper()} browser compatibility...")
        
        browser_results = {
            "browser": browser_name,
            "overall_success": True,
            "test_scenarios": {},
            "session_management": {},
            "responsive_design": {},
            "performance": {},
            "total_issues": 0
        }
        
        driver = self.setup_browser(browser_name)
        if not driver:
            browser_results["overall_success"] = False
            browser_results["error"] = f"Failed to setup {browser_name} driver"
            return browser_results
        
        try:
            # Test each authentication scenario
            for scenario_name, scenario_data in self.test_scenarios.items():
                print(f"  Testing {scenario_name} login flow...")
                
                login_results = self.test_login_flow(driver, scenario_name, scenario_data)
                browser_results["test_scenarios"][scenario_name] = login_results
                
                if login_results["issues"]:
                    browser_results["total_issues"] += len(login_results["issues"])
                    browser_results["overall_success"] = False
                
                # Test session management for successful logins
                if login_results["login_success"]:
                    session_results = self.test_session_management_rtl(driver)
                    browser_results["session_management"][scenario_name] = session_results
                    
                    if session_results["issues"]:
                        browser_results["total_issues"] += len(session_results["issues"])
                        browser_results["overall_success"] = False
                
                # Logout before next test
                try:
                    driver.get(f"{self.base_url}/api/method/logout")
                    time.sleep(1)
                except:
                    pass
            
            # Test responsive RTL design
            print(f"  Testing responsive RTL design...")
            driver.get(f"{self.base_url}/login?lang=ar")
            responsive_results = self.test_responsive_rtl(driver)
            browser_results["responsive_design"] = responsive_results
            
            if responsive_results["issues"]:
                browser_results["total_issues"] += len(responsive_results["issues"])
                browser_results["overall_success"] = False
            
            # Calculate performance metrics
            total_tests = len(self.test_scenarios) * 3  # login, session, responsive
            success_rate = ((total_tests - browser_results["total_issues"]) / total_tests) * 100
            browser_results["performance"]["success_rate"] = success_rate
            
        except Exception as e:
            browser_results["overall_success"] = False
            browser_results["error"] = str(e)
            
        finally:
            driver.quit()
        
        return browser_results

    def run_cross_browser_tests(self):
        """Run RTL compatibility tests across all browsers"""
        print("Starting Cross-Browser RTL Compatibility Testing...")
        print("=" * 60)
        
        browsers = ["chrome", "firefox", "edge"]  # Safari excluded for CI/CD compatibility
        
        # Run tests in parallel for faster execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_browser = {
                executor.submit(self.test_browser_compatibility, browser): browser 
                for browser in browsers
            }
            
            for future in future_to_browser:
                browser = future_to_browser[future]
                try:
                    browser_results = future.result()
                    self.test_results["browsers"][browser] = browser_results
                    
                    if browser_results["overall_success"]:
                        self.test_results["passed_tests"] += 1
                        print(f"✅ {browser.upper()}: PASSED")
                    else:
                        self.test_results["failed_tests"] += 1
                        print(f"❌ {browser.upper()}: FAILED ({browser_results.get('total_issues', 0)} issues)")
                        
                except Exception as e:
                    self.test_results["failed_tests"] += 1
                    print(f"❌ {browser.upper()}: ERROR - {e}")
        
        self.test_results["total_tests"] = len(browsers)
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Save detailed report
        self.save_test_report()
        
        return self.test_results

    def generate_recommendations(self):
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Check for common RTL issues across browsers
        rtl_issues_by_type = {}
        
        for browser, results in self.test_results["browsers"].items():
            for scenario_name, scenario_results in results.get("test_scenarios", {}).items():
                for issue in scenario_results.get("issues", []):
                    issue_type = issue.get("type", "unknown")
                    if issue_type not in rtl_issues_by_type:
                        rtl_issues_by_type[issue_type] = []
                    rtl_issues_by_type[issue_type].append(browser)
        
        # Generate specific recommendations
        if "form_alignment" in rtl_issues_by_type:
            recommendations.append({
                "priority": "high",
                "type": "css_fix",
                "title": "Fix Form Field RTL Alignment",
                "description": "Form fields are not properly aligned for RTL layout",
                "affected_browsers": rtl_issues_by_type["form_alignment"],
                "solution": "Update CSS: .form-control { text-align: right; direction: rtl; }"
            })
        
        if "rtl_inconsistency" in rtl_issues_by_type:
            recommendations.append({
                "priority": "high", 
                "type": "css_fix",
                "title": "Ensure Consistent RTL Direction",
                "description": "RTL direction is not consistent across all pages",
                "affected_browsers": rtl_issues_by_type["rtl_inconsistency"],
                "solution": "Add [dir='rtl'] body { direction: rtl; } to arabic-rtl.css"
            })
        
        if "horizontal_overflow" in rtl_issues_by_type:
            recommendations.append({
                "priority": "medium",
                "type": "responsive_fix", 
                "title": "Fix Responsive RTL Layout Overflow",
                "description": "RTL layouts causing horizontal overflow on smaller screens",
                "solution": "Review flex-direction and margin properties in mobile breakpoints"
            })
        
        # Performance recommendations
        avg_load_time = 0
        load_time_count = 0
        
        for browser, results in self.test_results["browsers"].items():
            for scenario_name, scenario_results in results.get("test_scenarios", {}).items():
                if "performance" in scenario_results:
                    page_load = scenario_results["performance"].get("page_load_time", 0)
                    if page_load > 0:
                        avg_load_time += page_load
                        load_time_count += 1
        
        if load_time_count > 0:
            avg_load_time = avg_load_time / load_time_count
            if avg_load_time > 3:
                recommendations.append({
                    "priority": "medium",
                    "type": "performance",
                    "title": "Optimize Page Load Performance",
                    "description": f"Average page load time is {avg_load_time:.2f}s",
                    "solution": "Optimize CSS delivery, enable gzip compression, minify assets"
                })
        
        self.test_results["recommendations"] = recommendations

    def save_test_report(self):
        """Save comprehensive test report"""
        report_dir = "tests/cross_browser"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{report_dir}/rtl_compatibility_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Detailed report saved: {report_file}")
        
        # Generate summary report
        summary_file = f"{report_dir}/rtl_compatibility_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Universal Workshop ERP - Cross-Browser RTL Compatibility Test Summary\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Test Date: {self.test_results['test_timestamp']}\n")
            f.write(f"Total Tests: {self.test_results['total_tests']}\n")
            f.write(f"Passed: {self.test_results['passed_tests']}\n")
            f.write(f"Failed: {self.test_results['failed_tests']}\n")
            f.write(f"Success Rate: {(self.test_results['passed_tests']/self.test_results['total_tests']*100):.1f}%\n\n")
            
            f.write("Browser Results:\n")
            f.write("-" * 20 + "\n")
            for browser, results in self.test_results["browsers"].items():
                status = "✅ PASS" if results["overall_success"] else "❌ FAIL"
                f.write(f"{browser.upper()}: {status} ({results.get('total_issues', 0)} issues)\n")
            
            f.write(f"\nRecommendations ({len(self.test_results['recommendations'])}):\n")
            f.write("-" * 20 + "\n")
            for i, rec in enumerate(self.test_results["recommendations"], 1):
                f.write(f"{i}. [{rec['priority'].upper()}] {rec['title']}\n")
                f.write(f"   {rec['description']}\n")
                if 'solution' in rec:
                    f.write(f"   Solution: {rec['solution']}\n")
                f.write("\n")
        
        print(f"📋 Summary report saved: {summary_file}")


def main():
    """Main execution function"""
    print("Universal Workshop ERP - Cross-Browser RTL Compatibility Tester")
    print("Testing authentication flow and Arabic interface across browsers")
    print("=" * 70)
    
    # Initialize tester
    tester = RTLCompatibilityTester()
    
    # Run comprehensive tests
    results = tester.run_cross_browser_tests()
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    if results['total_tests'] > 0:
        success_rate = (results['passed_tests'] / results['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"Recommendations: {len(results['recommendations'])}")
    
    if results['failed_tests'] > 0:
        print("\n⚠️  Issues found! Check the detailed report for solutions.")
        return 1
    else:
        print("\n✅ All cross-browser RTL compatibility tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
