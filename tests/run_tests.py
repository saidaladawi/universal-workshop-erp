#!/usr/bin/env python3
"""
Universal Workshop ERP Test Runner
Comprehensive test execution script for integration testing
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime


class WorkshopTestRunner:
    """Main test runner for Universal Workshop ERP system."""
    
    def __init__(self, bench_path="/home/said/frappe-dev/frappe-bench"):
        self.bench_path = Path(bench_path)
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_python_tests(self, test_path=None, verbose=False):
        """Run Python-based integration tests."""
        print("🐍 Running Python Integration Tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        if test_path:
            cmd.append(str(test_path))
        else:
            cmd.extend([
                "tests/e2e/",
                "tests/integration/",
                "-v" if verbose else ""
            ])
        
        if verbose:
            cmd.extend(["-v", "-s", "--tb=short"])
        
        cmd.extend([
            "--json-report",
            "--json-report-file=test_results/python_tests.json"
        ])
        
        # Run tests
        result = subprocess.run(
            cmd,
            cwd=self.bench_path,
            capture_output=True,
            text=True
        )
        
        self.test_results["python_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        print(f"✅ Python tests completed with exit code: {result.returncode}")
        if result.returncode != 0:
            print(f"❌ Python test errors:\n{result.stderr}")
        
        return result.returncode == 0
    
    def run_cypress_tests(self, spec=None, headless=True):
        """Run Cypress E2E tests."""
        print("🌲 Running Cypress E2E Tests...")
        
        # Check if Cypress is available
        cypress_config = self.bench_path / "apps" / "frappe" / "cypress.config.js"
        if not cypress_config.exists():
            print("❌ Cypress configuration not found")
            return False
        
        cmd = ["npx", "cypress", "run"]
        
        if spec:
            cmd.extend(["--spec", spec])
        else:
            cmd.extend(["--spec", "tests/e2e/cypress_workshop_tests.js"])
        
        if headless:
            cmd.append("--headless")
        
        cmd.extend([
            "--reporter", "json",
            "--reporter-options", "outputFile=test_results/cypress_tests.json"
        ])
        
        # Set environment variables
        env = os.environ.copy()
        env["CYPRESS_baseUrl"] = "http://localhost:8000"
        env["CYPRESS_adminPassword"] = "admin"
        
        result = subprocess.run(
            cmd,
            cwd=self.bench_path / "apps" / "frappe",
            capture_output=True,
            text=True,
            env=env
        )
        
        self.test_results["cypress_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        print(f"✅ Cypress tests completed with exit code: {result.returncode}")
        if result.returncode != 0:
            print(f"❌ Cypress test errors:\n{result.stderr}")
        
        return result.returncode == 0
    
    def run_api_tests(self, host="localhost", port=8000):
        """Run API integration tests."""
        print("🔌 Running API Integration Tests...")
        
        # Check if server is running
        import requests
        try:
            response = requests.get(f"http://{host}:{port}/api/method/ping", timeout=5)
            if response.status_code != 200:
                print(f"❌ Server not responding at {host}:{port}")
                return False
        except requests.ConnectionError:
            print(f"❌ Cannot connect to server at {host}:{port}")
            return False
        
        # Run API tests
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/test_api_integration.py",
            "-v",
            "--json-report",
            "--json-report-file=test_results/api_tests.json"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.bench_path,
            capture_output=True,
            text=True
        )
        
        self.test_results["api_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        print(f"✅ API tests completed with exit code: {result.returncode}")
        return result.returncode == 0
    
    def run_load_tests(self, users=10, duration=60):
        """Run load tests using locust or similar."""
        print(f"⚡ Running Load Tests ({users} users, {duration}s)...")
        
        # Create a simple load test script
        load_test_script = """
import requests
import random
import time
from locust import HttpUser, task, between

class WorkshopUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/method/login", json={
            "usr": "Administrator",
            "pwd": "admin"
        })
        
    @task(3)
    def view_customers(self):
        self.client.get("/api/resource/Customer")
    
    @task(2)
    def view_vehicles(self):
        self.client.get("/api/resource/Vehicle")
    
    @task(1)
    def create_service_order(self):
        self.client.post("/api/resource/Service Order", json={
            "customer": "Test Customer",
            "service_type": "Oil Change",
            "status": "Open"
        })
"""
        
        # Write load test script
        load_test_file = self.bench_path / "tests" / "load_test.py"
        with open(load_test_file, 'w') as f:
            f.write(load_test_script)
        
        # Run locust
        cmd = [
            "locust",
            "-f", str(load_test_file),
            "--headless",
            "--users", str(users),
            "--spawn-rate", "1",
            "--run-time", f"{duration}s",
            "--host", "http://localhost:8000",
            "--html", "test_results/load_test_report.html"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.bench_path,
            capture_output=True,
            text=True
        )
        
        self.test_results["load_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        print(f"✅ Load tests completed with exit code: {result.returncode}")
        return result.returncode == 0
    
    def run_security_tests(self):
        """Run security tests using OWASP ZAP or similar."""
        print("🔒 Running Security Tests...")
        
        # Check if ZAP is available
        zap_cmd = "zap-baseline.py"
        
        try:
            result = subprocess.run(
                ["which", zap_cmd],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("⚠️ OWASP ZAP not found, skipping security tests")
                return True
            
            # Run ZAP baseline scan
            cmd = [
                zap_cmd,
                "-t", "http://localhost:8000",
                "-J", "test_results/zap_report.json",
                "-r", "test_results/zap_report.html"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.bench_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.test_results["security_tests"] = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode in [0, 1]  # ZAP returns 1 for warnings
            }
            
            print(f"✅ Security tests completed with exit code: {result.returncode}")
            return result.returncode in [0, 1]
            
        except subprocess.TimeoutExpired:
            print("⚠️ Security tests timed out")
            return False
        except Exception as e:
            print(f"⚠️ Security tests failed: {str(e)}")
            return False
    
    def setup_test_environment(self):
        """Setup test environment."""
        print("🔧 Setting up test environment...")
        
        # Create test results directory
        test_results_dir = self.bench_path / "test_results"
        test_results_dir.mkdir(exist_ok=True)
        
        # Setup test database
        cmd = ["bench", "set-config", "developer_mode", "1"]
        subprocess.run(cmd, cwd=self.bench_path)
        
        # Install test dependencies
        pip_packages = [
            "pytest",
            "pytest-json-report", 
            "requests",
            "locust"
        ]
        
        for package in pip_packages:
            cmd = ["pip", "install", package]
            subprocess.run(cmd, cwd=self.bench_path)
        
        print("✅ Test environment setup complete")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("📊 Generating test report...")
        
        report = {
            "test_run": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None
            },
            "results": self.test_results,
            "summary": {
                "total_test_suites": len(self.test_results),
                "passed_suites": sum(1 for result in self.test_results.values() if result.get("success", False)),
                "failed_suites": sum(1 for result in self.test_results.values() if not result.get("success", False))
            }
        }
        
        # Write report
        report_file = self.bench_path / "test_results" / "comprehensive_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_report = self.generate_html_report(report)
        html_file = self.bench_path / "test_results" / "test_report.html"
        with open(html_file, 'w') as f:
            f.write(html_report)
        
        print(f"📄 Test report generated: {report_file}")
        print(f"🌐 HTML report: {html_file}")
        
        return report
    
    def generate_html_report(self, report_data):
        """Generate HTML test report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Universal Workshop ERP - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .success {{ background-color: #d4edda; color: #155724; }}
        .failure {{ background-color: #f8d7da; color: #721c24; }}
        .test-suite {{ margin: 20px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Universal Workshop ERP - Integration Test Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Duration: {report_data['test_run'].get('duration', 'N/A')} seconds</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Suites</h3>
            <div>{report_data['summary']['total_test_suites']}</div>
        </div>
        <div class="metric success">
            <h3>Passed</h3>
            <div>{report_data['summary']['passed_suites']}</div>
        </div>
        <div class="metric failure">
            <h3>Failed</h3>
            <div>{report_data['summary']['failed_suites']}</div>
        </div>
    </div>
    
    <h2>Test Results</h2>
"""
        
        for suite_name, result in report_data['results'].items():
            status_class = "success" if result.get("success", False) else "failure"
            status_text = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            
            html += f"""
    <div class="test-suite {status_class}">
        <h3>{suite_name.replace('_', ' ').title()} {status_text}</h3>
        <p><strong>Exit Code:</strong> {result.get('exit_code', 'N/A')}</p>
        
        {f'<details><summary>Output</summary><pre>{result.get("stdout", "")}</pre></details>' if result.get("stdout") else ""}
        {f'<details><summary>Errors</summary><pre>{result.get("stderr", "")}</pre></details>' if result.get("stderr") else ""}
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def run_all_tests(self, include_load=False, include_security=False):
        """Run all test suites."""
        self.start_time = datetime.now()
        print("🚀 Starting comprehensive test suite...")
        
        # Setup environment
        self.setup_test_environment()
        
        results = {}
        
        # Run Python tests
        results["python"] = self.run_python_tests(verbose=True)
        
        # Run API tests
        results["api"] = self.run_api_tests()
        
        # Run Cypress tests
        results["cypress"] = self.run_cypress_tests()
        
        # Optional tests
        if include_load:
            results["load"] = self.run_load_tests()
        
        if include_security:
            results["security"] = self.run_security_tests()
        
        self.end_time = datetime.now()
        
        # Generate report
        report = self.generate_test_report()
        
        # Print summary
        print("\n" + "="*50)
        print("🏁 TEST SUITE COMPLETE")
        print("="*50)
        print(f"Total Duration: {report['test_run']['duration']:.2f} seconds")
        print(f"Passed Suites: {report['summary']['passed_suites']}/{report['summary']['total_test_suites']}")
        
        if report['summary']['failed_suites'] > 0:
            print(f"❌ {report['summary']['failed_suites']} test suite(s) failed")
            return False
        else:
            print("✅ All test suites passed!")
            return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Universal Workshop ERP Test Runner")
    parser.add_argument("--bench-path", default="/home/said/frappe-dev/frappe-bench", 
                       help="Path to Frappe bench")
    parser.add_argument("--python-only", action="store_true", 
                       help="Run only Python tests")
    parser.add_argument("--cypress-only", action="store_true", 
                       help="Run only Cypress tests")
    parser.add_argument("--api-only", action="store_true", 
                       help="Run only API tests")
    parser.add_argument("--include-load", action="store_true", 
                       help="Include load testing")
    parser.add_argument("--include-security", action="store_true", 
                       help="Include security testing")
    parser.add_argument("--test-path", 
                       help="Specific test path to run")
    
    args = parser.parse_args()
    
    runner = WorkshopTestRunner(args.bench_path)
    
    success = False
    
    if args.python_only:
        success = runner.run_python_tests(args.test_path, verbose=True)
    elif args.cypress_only:
        success = runner.run_cypress_tests()
    elif args.api_only:
        success = runner.run_api_tests()
    else:
        success = runner.run_all_tests(
            include_load=args.include_load,
            include_security=args.include_security
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
