#!/usr/bin/env python3
"""
Universal Workshop ERP - Performance Test Runner
Orchestrates performance testing with different scenarios and generates reports
"""

import os
import sys
import json
import subprocess
import time
import argparse
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import signal
import threading


class PerformanceTestRunner:
    """
    Manages performance testing execution and monitoring
    """
    
    def __init__(self, config_file="performance_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.test_results = []
        self.monitoring_active = False
        self.system_metrics = []
        
    def load_config(self):
        """Load performance test configuration"""
        config_path = Path(__file__).parent / self.config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def check_prerequisites(self):
        """Check if required tools and dependencies are available"""
        print("🔍 Checking prerequisites...")
        
        prerequisites = {
            "locust": "pip install locust",
            "psutil": "pip install psutil",
            "frappe": "Frappe framework should be installed"
        }
        
        missing = []
        
        # Check locust
        try:
            import locust
            print(f"✅ Locust found: {locust.__version__}")
        except ImportError:
            missing.append("locust")
        
        # Check psutil
        try:
            import psutil
            print(f"✅ psutil found: {psutil.__version__}")
        except ImportError:
            missing.append("psutil")
        
        # Check if bench is running
        try:
            import requests
            response = requests.get("http://localhost:8000", timeout=5)
            print("✅ Frappe/ERPNext server is running")
        except Exception as e:
            print(f"⚠️  Frappe/ERPNext server check failed: {e}")
            print("   Make sure to run 'bench start' before testing")
        
        if missing:
            print("❌ Missing prerequisites:")
            for item in missing:
                print(f"   - {item}: {prerequisites[item]}")
            return False
        
        return True
    
    def start_system_monitoring(self):
        """Start background system monitoring"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_system)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        print("📊 System monitoring started")
    
    def stop_system_monitoring(self):
        """Stop background system monitoring"""
        self.monitoring_active = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=5)
        print("📊 System monitoring stopped")
    
    def _monitor_system(self):
        """Background system monitoring"""
        while self.monitoring_active:
            try:
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    'network_io': psutil.net_io_counters()._asdict(),
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                }
                
                self.system_metrics.append(metrics)
                
                # Keep only last 1000 metrics to prevent memory issues
                if len(self.system_metrics) > 1000:
                    self.system_metrics = self.system_metrics[-1000:]
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
            
            time.sleep(10)  # Collect metrics every 10 seconds
    
    def run_scenario(self, scenario_name):
        """Run a specific performance test scenario"""
        scenario = self.config['performance_test_config']['test_scenarios'].get(scenario_name)
        
        if not scenario:
            print(f"❌ Scenario '{scenario_name}' not found")
            return False
        
        print(f"\n🚀 Running scenario: {scenario_name}")
        print(f"📝 Description: {scenario['description']}")
        print(f"👥 Users: {scenario['users']}")
        print(f"⚡ Spawn rate: {scenario['spawn_rate']}/sec")
        print(f"⏱️  Duration: {scenario['duration']}")
        
        # Prepare locust command
        test_script = Path(__file__).parent / "performance_test_suite.py"
        
        locust_cmd = [
            "locust",
            "-f", str(test_script),
            "--host", scenario['host'],
            "--users", str(scenario['users']),
            "--spawn-rate", str(scenario['spawn_rate']),
            "--run-time", scenario['duration'],
            "--headless",
            "--csv", f"test_results/performance/{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ]
        
        print(f"🔧 Command: {' '.join(locust_cmd)}")
        
        # Start system monitoring
        self.start_system_monitoring()
        
        start_time = datetime.now()
        
        try:
            # Run locust test
            result = subprocess.run(
                locust_cmd,
                capture_output=True,
                text=True,
                timeout=self._parse_duration(scenario['duration']) + 300  # Add 5 minutes buffer
            )
            
            end_time = datetime.now()
            
            # Stop system monitoring
            self.stop_system_monitoring()
            
            # Analyze results
            test_result = {
                'scenario': scenario_name,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds(),
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'system_metrics': self.system_metrics.copy(),
                'performance_thresholds': self.config['performance_test_config']['performance_thresholds'],
                'expected_metrics': {
                    'failure_rate': scenario['expected_failure_rate'],
                    'avg_response_time': scenario['expected_avg_response_time']
                }
            }
            
            # Parse locust output for key metrics
            metrics = self.parse_locust_output(result.stdout)
            test_result['parsed_metrics'] = metrics
            
            # Evaluate test results
            evaluation = self.evaluate_test_results(test_result, scenario)
            test_result['evaluation'] = evaluation
            
            self.test_results.append(test_result)
            
            print(f"\n📊 Scenario '{scenario_name}' completed:")
            print(f"   ⏱️  Duration: {test_result['duration_seconds']:.1f}s")
            print(f"   🎯 Exit code: {result.returncode}")
            
            if metrics:
                print(f"   📈 Total requests: {metrics.get('total_requests', 'N/A')}")
                print(f"   ❌ Failures: {metrics.get('total_failures', 'N/A')}")
                print(f"   ⚡ Avg response time: {metrics.get('avg_response_time', 'N/A')}ms")
                
            print(f"   🏆 Result: {'✅ PASS' if evaluation['passed'] else '❌ FAIL'}")
            
            if result.returncode == 0:
                return True
            else:
                print(f"❌ Locust error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Test timed out after {scenario['duration']}")
            self.stop_system_monitoring()
            return False
        
        except Exception as e:
            print(f"💥 Test execution error: {e}")
            self.stop_system_monitoring()
            return False
    
    def _parse_duration(self, duration_str):
        """Parse duration string (e.g., '5m', '30s') to seconds"""
        if duration_str.endswith('m'):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith('s'):
            return int(duration_str[:-1])
        elif duration_str.endswith('h'):
            return int(duration_str[:-1]) * 3600
        else:
            return int(duration_str)  # Assume seconds
    
    def parse_locust_output(self, stdout):
        """Parse locust output to extract key metrics"""
        import re
        
        metrics = {}
        
        # Extract total requests
        requests_match = re.search(r'Total requests:\s+(\d+)', stdout)
        if requests_match:
            metrics['total_requests'] = int(requests_match.group(1))
        
        # Extract failures
        failures_match = re.search(r'Total failures:\s+(\d+)', stdout)
        if failures_match:
            metrics['total_failures'] = int(failures_match.group(1))
        
        # Extract average response time
        avg_time_match = re.search(r'Average response time:\s+([\d.]+)', stdout)
        if avg_time_match:
            metrics['avg_response_time'] = float(avg_time_match.group(1))
        
        # Extract percentiles
        percentile_matches = re.findall(r'(\d+)%\s+([\d.]+)', stdout)
        if percentile_matches:
            metrics['percentiles'] = {}
            for percentile, value in percentile_matches:
                metrics['percentiles'][f'{percentile}th'] = float(value)
        
        return metrics
    
    def evaluate_test_results(self, test_result, scenario):
        """Evaluate test results against thresholds"""
        evaluation = {
            'passed': True,
            'issues': [],
            'recommendations': []
        }
        
        parsed_metrics = test_result.get('parsed_metrics', {})
        expected = test_result['expected_metrics']
        
        # Check failure rate
        if parsed_metrics.get('total_requests', 0) > 0:
            actual_failure_rate = (parsed_metrics.get('total_failures', 0) / parsed_metrics['total_requests']) * 100
            
            if actual_failure_rate > expected['failure_rate']:
                evaluation['passed'] = False
                evaluation['issues'].append(
                    f"High failure rate: {actual_failure_rate:.2f}% > {expected['failure_rate']}%"
                )
        
        # Check response time
        actual_avg_time = parsed_metrics.get('avg_response_time', 0)
        if actual_avg_time > expected['avg_response_time']:
            evaluation['passed'] = False
            evaluation['issues'].append(
                f"Slow response time: {actual_avg_time:.2f}ms > {expected['avg_response_time']}ms"
            )
        
        # Check system metrics
        if test_result['system_metrics']:
            avg_cpu = sum(m['cpu_percent'] for m in test_result['system_metrics']) / len(test_result['system_metrics'])
            avg_memory = sum(m['memory_percent'] for m in test_result['system_metrics']) / len(test_result['system_metrics'])
            
            if avg_cpu > 90:
                evaluation['recommendations'].append(f"High CPU usage: {avg_cpu:.1f}%")
            
            if avg_memory > 85:
                evaluation['recommendations'].append(f"High memory usage: {avg_memory:.1f}%")
        
        return evaluation
    
    def run_all_scenarios(self):
        """Run all configured test scenarios"""
        scenarios = self.config['performance_test_config']['test_scenarios'].keys()
        
        print(f"🎯 Running {len(scenarios)} test scenarios...")
        
        results_summary = []
        
        for scenario_name in scenarios:
            success = self.run_scenario(scenario_name)
            results_summary.append({
                'scenario': scenario_name,
                'success': success
            })
            
            # Wait between scenarios
            if scenario_name != list(scenarios)[-1]:  # Not the last scenario
                print("⏳ Waiting 30 seconds before next scenario...")
                time.sleep(30)
        
        # Generate final report
        self.generate_final_report(results_summary)
        
        return results_summary
    
    def generate_final_report(self, results_summary):
        """Generate comprehensive final report"""
        report_dir = Path('test_results/performance')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f"performance_test_report_{timestamp}.json"
        
        final_report = {
            'test_execution': {
                'timestamp': datetime.now().isoformat(),
                'total_scenarios': len(results_summary),
                'successful_scenarios': sum(1 for r in results_summary if r['success']),
                'failed_scenarios': sum(1 for r in results_summary if not r['success'])
            },
            'scenarios_summary': results_summary,
            'detailed_results': self.test_results,
            'configuration': self.config,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'total_memory': psutil.virtual_memory().total
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n📊 Final performance report saved: {report_file}")
        
        # Print summary
        print("\n🎯 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Total scenarios: {final_report['test_execution']['total_scenarios']}")
        print(f"Successful: {final_report['test_execution']['successful_scenarios']}")
        print(f"Failed: {final_report['test_execution']['failed_scenarios']}")
        
        if final_report['test_execution']['failed_scenarios'] == 0:
            print("🎉 All performance tests PASSED!")
        else:
            print("⚠️  Some performance tests FAILED")
        
        return final_report


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Universal Workshop Performance Test Runner")
    parser.add_argument('--scenario', type=str, help='Run specific scenario')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--config', type=str, default='performance_config.json', 
                       help='Configuration file path')
    parser.add_argument('--check', action='store_true', help='Check prerequisites only')
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(args.config)
    
    if args.check:
        if runner.check_prerequisites():
            print("✅ All prerequisites are met")
            return 0
        else:
            print("❌ Prerequisites check failed")
            return 1
    
    if not runner.check_prerequisites():
        print("❌ Prerequisites not met. Run with --check for details")
        return 1
    
    # Create results directory
    Path('test_results/performance').mkdir(parents=True, exist_ok=True)
    
    if args.scenario:
        success = runner.run_scenario(args.scenario)
        return 0 if success else 1
    
    elif args.all:
        results = runner.run_all_scenarios()
        success = all(r['success'] for r in results)
        return 0 if success else 1
    
    else:
        print("Usage: python performance_test_runner.py --scenario <name> | --all | --check")
        print("\nAvailable scenarios:")
        scenarios = runner.config['performance_test_config']['test_scenarios'].keys()
        for scenario in scenarios:
            print(f"  - {scenario}")
        return 1


if __name__ == "__main__":
    exit(main())
