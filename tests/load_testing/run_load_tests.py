#!/usr/bin/env python3
"""
Universal Workshop ERP - Comprehensive Load Testing Orchestrator
==============================================================

This script orchestrates comprehensive load testing using multiple tools:
- Locust for Python-based load testing
- Artillery for JavaScript/YAML-based API testing  
- Custom performance monitoring
- System resource monitoring

Usage:
    python run_load_tests.py --profile light
    python run_load_tests.py --profile heavy --duration 30m
    python run_load_tests.py --tools locust,artillery --monitoring
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to sys.path to import our modules
sys.path.append(str(Path(__file__).parent))

try:
    from performance_tests import SystemMonitor, DatabaseStressTest, BackgroundJobTest
    PERFORMANCE_TESTS_AVAILABLE = True
except ImportError:
    PERFORMANCE_TESTS_AVAILABLE = False
    print("⚠️ Performance tests module not available")


class LoadTestOrchestrator:
    """Orchestrates comprehensive load testing using multiple tools"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_profiles = {
            "light": {
                "description": "Light load testing - Development/Testing",
                "locust": {"users": 10, "spawn_rate": 2, "duration": "5m"},
                "artillery": {"phases": [{"duration": 60, "arrivalRate": 2}]},
                "monitoring_duration": 300  # 5 minutes
            },
            "medium": {
                "description": "Medium load testing - Staging validation",
                "locust": {"users": 50, "spawn_rate": 5, "duration": "15m"},
                "artillery": {"phases": [
                    {"duration": 60, "arrivalRate": 5},
                    {"duration": 300, "arrivalRate": 15}
                ]},
                "monitoring_duration": 900  # 15 minutes
            },
            "heavy": {
                "description": "Heavy load testing - Pre-production validation",
                "locust": {"users": 200, "spawn_rate": 10, "duration": "30m"},
                "artillery": {"phases": [
                    {"duration": 60, "arrivalRate": 10},
                    {"duration": 600, "arrivalRate": 30},
                    {"duration": 300, "arrivalRate": 50}
                ]},
                "monitoring_duration": 1800  # 30 minutes
            },
            "stress": {
                "description": "Stress testing - System limits exploration",
                "locust": {"users": 500, "spawn_rate": 20, "duration": "60m"},
                "artillery": {"phases": [
                    {"duration": 120, "arrivalRate": 20},
                    {"duration": 1800, "arrivalRate": 50},
                    {"duration": 600, "arrivalRate": 100}
                ]},
                "monitoring_duration": 3600  # 60 minutes
            }
        }
    
    def run_comprehensive_test(self, profile="medium", tools=None, target="http://localhost:8000", 
                             enable_monitoring=True, duration_override=None):
        """Run comprehensive load testing with specified profile"""
        
        if profile not in self.test_profiles:
            print(f"❌ Unknown profile: {profile}")
            print(f"Available profiles: {', '.join(self.test_profiles.keys())}")
            return False
        
        test_config = self.test_profiles[profile]
        tools = tools or ["locust", "artillery", "performance"]
        
        print("🚀 UNIVERSAL WORKSHOP ERP - COMPREHENSIVE LOAD TESTING")
        print("="*80)
        print(f"Profile: {profile.upper()} - {test_config['description']}")
        print(f"Target: {target}")
        print(f"Tools: {', '.join(tools)}")
        print(f"Monitoring: {'Enabled' if enable_monitoring else 'Disabled'}")
        print("="*80)
        
        # Create test session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.results_dir / f"load_test_{profile}_{timestamp}"
        session_dir.mkdir(exist_ok=True)
        
        # Start system monitoring if enabled
        monitor = None
        if enable_monitoring and PERFORMANCE_TESTS_AVAILABLE:
            monitor = SystemMonitor(str(session_dir / "system_metrics.json"))
            monitoring_duration = duration_override or test_config["monitoring_duration"]
            monitor_thread = monitor.start_monitoring(monitoring_duration)
            print(f"📊 System monitoring started for {monitoring_duration} seconds")
        
        test_results = {}
        
        try:
            # Run tests based on selected tools
            if "performance" in tools and PERFORMANCE_TESTS_AVAILABLE:
                print("\n1️⃣ Running Database & Performance Tests...")
                test_results["performance"] = self._run_performance_tests(session_dir)
            
            if "locust" in tools:
                print("\n2️⃣ Running Locust Load Tests...")
                test_results["locust"] = self._run_locust_test(
                    test_config["locust"], target, session_dir
                )
            
            if "artillery" in tools:
                print("\n3️⃣ Running Artillery API Tests...")
                test_results["artillery"] = self._run_artillery_test(
                    test_config["artillery"], target, session_dir
                )
            
            # Generate comprehensive report
            print(f"\n4️⃣ Generating comprehensive test report...")
            self._generate_report(test_results, session_dir, profile, test_config)
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
        finally:
            # Stop monitoring
            if monitor:
                monitor.stop_monitoring()
                if 'monitor_thread' in locals():
                    monitor_thread.join(timeout=10)
        
        print(f"\n✅ Comprehensive load testing completed!")
        print(f"📁 Results saved to: {session_dir}")
        print(f"📊 Open {session_dir / 'test_report.html'} for detailed analysis")
        
        return True
    
    def _run_performance_tests(self, session_dir):
        """Run database stress and background job tests"""
        print("  🔥 Database stress testing...")
        
        db_test = DatabaseStressTest()
        bg_test = BackgroundJobTest()
        
        try:
            # Run database stress test
            db_test.run_concurrent_operations(num_threads=15, operations_per_thread=50)
            
            # Brief pause
            time.sleep(10)
            
            # Run background job test
            bg_test.test_queue_performance(num_jobs=30)
            
            return {
                "status": "completed",
                "database_test": "completed",
                "background_jobs": "completed"
            }
        except Exception as e:
            print(f"  ❌ Performance tests failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _run_locust_test(self, config, target, session_dir):
        """Run Locust load test"""
        print(f"  🐝 Starting Locust with {config['users']} users...")
        
        locust_file = self.test_dir / "locust_workshop_tests.py"
        results_file = session_dir / "locust_results.html"
        stats_file = session_dir / "locust_stats.json"
        
        # Build Locust command
        cmd = [
            "locust",
            "-f", str(locust_file),
            "--host", target,
            "--users", str(config["users"]),
            "--spawn-rate", str(config["spawn_rate"]),
            "--run-time", config["duration"],
            "--headless",
            "--html", str(results_file),
            "--csv", str(session_dir / "locust"),
            "--logfile", str(session_dir / "locust.log")
        ]
        
        try:
            # Run Locust test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print("  ✅ Locust test completed successfully")
                return {
                    "status": "completed",
                    "users": config["users"],
                    "duration": config["duration"],
                    "results_file": str(results_file),
                    "output": result.stdout
                }
            else:
                print(f"  ❌ Locust test failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "output": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            print("  ⏰ Locust test timed out")
            return {"status": "timeout"}
        except FileNotFoundError:
            print("  ❌ Locust not found. Install with: pip install locust")
            return {"status": "not_installed"}
        except Exception as e:
            print(f"  ❌ Locust test error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _run_artillery_test(self, config, target, session_dir):
        """Run Artillery API test"""
        print("  🎯 Starting Artillery API load test...")
        
        artillery_file = self.test_dir / "artillery" / "api_load_test.yml"
        results_file = session_dir / "artillery_results.json"
        report_file = session_dir / "artillery_report.html"
        
        try:
            # Run Artillery test
            cmd = [
                "artillery", "run",
                str(artillery_file),
                "--target", target,
                "--output", str(results_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                # Generate HTML report
                report_cmd = [
                    "artillery", "report",
                    str(results_file),
                    "--output", str(report_file)
                ]
                subprocess.run(report_cmd, timeout=60)
                
                print("  ✅ Artillery test completed successfully")
                return {
                    "status": "completed",
                    "results_file": str(results_file),
                    "report_file": str(report_file),
                    "output": result.stdout
                }
            else:
                print(f"  ❌ Artillery test failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "output": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            print("  ⏰ Artillery test timed out")
            return {"status": "timeout"}
        except FileNotFoundError:
            print("  ❌ Artillery not found. Install with: npm install -g artillery")
            return {"status": "not_installed"}
        except Exception as e:
            print(f"  ❌ Artillery test error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_report(self, test_results, session_dir, profile, config):
        """Generate comprehensive HTML test report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "profile": profile,
            "config": config,
            "results": test_results,
            "session_dir": str(session_dir)
        }
        
        # Save JSON report
        with open(session_dir / "test_report.json", 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_content = self._create_html_report(report_data)
        with open(session_dir / "test_report.html", 'w') as f:
            f.write(html_content)
    
    def _create_html_report(self, data):
        """Create HTML report from test data"""
        timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Universal Workshop ERP - Load Test Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background: #d4edda; border-color: #c3e6cb; }}
        .warning {{ background: #fff3cd; border-color: #ffeaa7; }}
        .error {{ background: #f8d7da; border-color: #f5c6cb; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Universal Workshop ERP - Load Test Report</h1>
        <p>Profile: {data['profile'].upper()} | Generated: {timestamp}</p>
    </div>
    
    <div class="section">
        <h2>📊 Test Summary</h2>
        <div class="metric">
            <strong>Profile:</strong> {data['profile']} - {data['config']['description']}
        </div>
        <div class="metric">
            <strong>Duration:</strong> {data['config']['monitoring_duration']} seconds
        </div>
        <div class="metric">
            <strong>Tests Run:</strong> {', '.join(data['results'].keys())}
        </div>
    </div>
"""
        
        # Add individual test results
        for tool, result in data["results"].items():
            status_class = "success" if result.get("status") == "completed" else "error"
            html += f"""
    <div class="section {status_class}">
        <h2>🔧 {tool.title()} Results</h2>
        <p><strong>Status:</strong> {result.get('status', 'unknown')}</p>
"""
            
            if result.get("error"):
                html += f"<p><strong>Error:</strong> {result['error']}</p>"
            
            if result.get("output"):
                html += f"<h3>Output:</h3><pre>{result['output'][:2000]}...</pre>"
            
            html += "</div>"
        
        html += """
    <div class="section">
        <h2>📁 Generated Files</h2>
        <ul>
            <li>test_report.json - Machine-readable test results</li>
            <li>system_metrics.json - System resource monitoring data</li>
            <li>locust_results.html - Locust detailed report (if run)</li>
            <li>artillery_report.html - Artillery detailed report (if run)</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>📋 Next Steps</h2>
        <ol>
            <li>Review individual tool reports for detailed metrics</li>
            <li>Analyze system resource usage during peak load</li>
            <li>Identify performance bottlenecks and optimization opportunities</li>
            <li>Compare results with previous test runs for regression analysis</li>
            <li>Update performance baselines if improvements are confirmed</li>
        </ol>
    </div>
</body>
</html>
"""
        return html


def main():
    """Main entry point for load testing orchestrator"""
    parser = argparse.ArgumentParser(description="Universal Workshop ERP Load Testing Orchestrator")
    parser.add_argument("--profile", 
                       choices=["light", "medium", "heavy", "stress"],
                       default="medium",
                       help="Load testing profile")
    parser.add_argument("--tools",
                       default="locust,artillery,performance",
                       help="Comma-separated list of tools to run")
    parser.add_argument("--target",
                       default="http://localhost:8000",
                       help="Target server URL")
    parser.add_argument("--no-monitoring",
                       action="store_true",
                       help="Disable system monitoring")
    parser.add_argument("--duration",
                       help="Override monitoring duration (e.g., 30m, 1h)")
    parser.add_argument("--list-profiles",
                       action="store_true",
                       help="List available test profiles")
    
    args = parser.parse_args()
    
    orchestrator = LoadTestOrchestrator()
    
    if args.list_profiles:
        print("Available Load Testing Profiles:")
        print("="*50)
        for profile, config in orchestrator.test_profiles.items():
            print(f"{profile.upper()}: {config['description']}")
            print(f"  Locust: {config['locust']}")
            print(f"  Monitoring: {config['monitoring_duration']}s")
            print()
        return
    
    # Parse tools
    tools = [tool.strip() for tool in args.tools.split(",")]
    
    # Parse duration override
    duration_override = None
    if args.duration:
        duration_str = args.duration.lower()
        if duration_str.endswith('m'):
            duration_override = int(duration_str[:-1]) * 60
        elif duration_str.endswith('h'):
            duration_override = int(duration_str[:-1]) * 3600
        else:
            duration_override = int(duration_str)
    
    # Run comprehensive test
    success = orchestrator.run_comprehensive_test(
        profile=args.profile,
        tools=tools,
        target=args.target,
        enable_monitoring=not args.no_monitoring,
        duration_override=duration_override
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
