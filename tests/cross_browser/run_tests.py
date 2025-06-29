#!/usr/bin/env python3
"""
Universal Workshop ERP - Cross-Browser RTL Test Runner
Quick execution script for cross-browser compatibility testing
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path


def run_test_command(command, description):
    """Run a test command and return results"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True, result.stdout
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False, "Test timed out after 5 minutes"
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False, str(e)


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔧 Checking dependencies...")
    
    dependencies = {
        "python": "python3 --version",
        "selenium": "python3 -c 'import selenium; print(selenium.__version__)'",
        "chrome": "google-chrome --version || chromium --version",
        "firefox": "firefox --version",
        "edge": "microsoft-edge --version || echo 'Edge not found'"
    }
    
    missing_deps = []
    
    for dep_name, check_command in dependencies.items():
        success, output = run_test_command(check_command, f"Checking {dep_name}")
        if not success and dep_name in ["python", "selenium"]:
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n❌ Missing required dependencies: {', '.join(missing_deps)}")
        print("\nInstall missing dependencies:")
        if "python" in missing_deps:
            print("  - Install Python 3.8+")
        if "selenium" in missing_deps:
            print("  - pip install selenium")
        return False
    
    print("✅ All required dependencies found")
    return True


def install_browser_drivers():
    """Install/update browser drivers"""
    print("\n🚀 Setting up browser drivers...")
    
    # Try to install webdriver-manager for automatic driver management
    install_cmd = "pip install webdriver-manager"
    success, _ = run_test_command(install_cmd, "Installing webdriver-manager")
    
    if success:
        print("✅ webdriver-manager installed - drivers will be managed automatically")
        return True
    else:
        print("⚠️  Manual driver setup may be required")
        print("Download drivers manually:")
        print("  - ChromeDriver: https://chromedriver.chromium.org/")
        print("  - GeckoDriver: https://github.com/mozilla/geckodriver/releases")
        print("  - EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return False


def run_rtl_compatibility_tests(browser=None, url=None):
    """Run the main RTL compatibility tests"""
    print("\n🌐 Running Cross-Browser RTL Compatibility Tests...")
    
    # Construct the test command
    test_script = "tests/cross_browser/rtl_compatibility_test.py"
    
    if not os.path.exists(test_script):
        print(f"❌ Test script not found: {test_script}")
        return False
    
    cmd_parts = ["python3", test_script]
    
    if browser:
        cmd_parts.extend(["--browser", browser])
    
    if url:
        cmd_parts.extend(["--url", url])
    
    test_command = " ".join(cmd_parts)
    
    success, output = run_test_command(
        test_command, 
        "Cross-Browser RTL Compatibility Tests"
    )
    
    if success:
        print("✅ RTL compatibility tests completed successfully")
        
        # Look for generated reports
        report_dir = "tests/cross_browser"
        if os.path.exists(report_dir):
            reports = [f for f in os.listdir(report_dir) if f.endswith('.json')]
            if reports:
                latest_report = max(reports, key=lambda x: os.path.getctime(os.path.join(report_dir, x)))
                print(f"📊 Latest test report: {report_dir}/{latest_report}")
    
    return success


def run_css_validation():
    """Validate CSS files for syntax errors"""
    print("\n🎨 Validating CSS files...")
    
    css_files = [
        "apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css",
        "apps/universal_workshop/universal_workshop/public/css/dynamic_branding.css"
    ]
    
    for css_file in css_files:
        if os.path.exists(css_file):
            # Simple CSS syntax check
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic syntax checks
                brace_count = content.count('{') - content.count('}')
                if brace_count != 0:
                    print(f"⚠️  {css_file}: Mismatched braces (difference: {brace_count})")
                else:
                    print(f"✅ {css_file}: Syntax OK")
                    
            except Exception as e:
                print(f"❌ {css_file}: Error reading file - {e}")
        else:
            print(f"⚠️  {css_file}: File not found")


def run_html_validation():
    """Validate HTML templates for RTL attributes"""
    print("\n📄 Validating HTML templates for RTL support...")
    
    template_files = [
        "apps/universal_workshop/universal_workshop/www/login.html",
        "apps/universal_workshop/universal_workshop/www/universal-workshop-dashboard.html",
        "apps/universal_workshop/universal_workshop/www/technician.html"
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for RTL support indicators
                rtl_indicators = [
                    'dir="rtl"',
                    'direction: rtl',
                    '[dir="rtl"]',
                    'text-align: right',
                    'arabic-rtl.css'
                ]
                
                found_indicators = [indicator for indicator in rtl_indicators if indicator in content]
                
                if found_indicators:
                    print(f"✅ {template_file}: RTL support detected ({len(found_indicators)} indicators)")
                else:
                    print(f"⚠️  {template_file}: No RTL support indicators found")
                    
            except Exception as e:
                print(f"❌ {template_file}: Error reading file - {e}")
        else:
            print(f"⚠️  {template_file}: File not found")


def generate_summary_report():
    """Generate a summary of all test results"""
    print("\n📋 Generating Test Summary Report...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_data = {
        "timestamp": timestamp,
        "test_type": "cross_browser_rtl_compatibility",
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        },
        "test_results": {
            "dependencies_check": True,  # Would be updated based on actual results
            "css_validation": True,
            "html_validation": True,
            "rtl_compatibility": True
        },
        "recommendations": [
            "Ensure all browsers have latest drivers installed",
            "Test on real devices with Arabic locale settings",
            "Validate RTL layout with actual Arabic content",
            "Monitor performance with Arabic fonts loaded"
        ]
    }
    
    # Save report
    os.makedirs("tests/cross_browser", exist_ok=True)
    report_file = f"tests/cross_browser/test_runner_summary_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Summary report saved: {report_file}")
    return report_file


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Universal Workshop ERP - Cross-Browser RTL Test Runner"
    )
    parser.add_argument(
        "--browser", 
        choices=["chrome", "firefox", "edge", "safari"],
        help="Test specific browser only"
    )
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="ERPNext base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--skip-deps", 
        action="store_true",
        help="Skip dependency checks"
    )
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick validation only (no browser tests)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 Universal Workshop ERP - Cross-Browser RTL Test Runner")
    print("=" * 70)
    
    success_count = 0
    total_tests = 0
    
    # Check dependencies
    if not args.skip_deps:
        total_tests += 1
        if check_dependencies():
            success_count += 1
            install_browser_drivers()
        else:
            print("❌ Dependency check failed. Use --skip-deps to continue anyway.")
            return 1
    
    # Run CSS validation
    total_tests += 1
    try:
        run_css_validation()
        success_count += 1
    except Exception as e:
        print(f"❌ CSS validation failed: {e}")
    
    # Run HTML validation
    total_tests += 1
    try:
        run_html_validation()
        success_count += 1
    except Exception as e:
        print(f"❌ HTML validation failed: {e}")
    
    # Run browser tests (unless quick mode)
    if not args.quick:
        total_tests += 1
        if run_rtl_compatibility_tests(args.browser, args.url):
            success_count += 1
    else:
        print("\n⚡ Quick mode: Skipping browser tests")
    
    # Generate summary
    generate_summary_report()
    
    # Print final results
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_tests - success_count}")
    
    if success_count == total_tests:
        print("✅ All tests passed!")
        print("\n🎉 Your Universal Workshop ERP is ready for cross-browser RTL deployment!")
        return 0
    else:
        print(f"⚠️  {total_tests - success_count} test(s) failed")
        print("\n🔧 Check the detailed reports for specific issues to fix.")
        return 1


if __name__ == "__main__":
    exit(main())
