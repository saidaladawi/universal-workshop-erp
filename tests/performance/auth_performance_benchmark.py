#!/usr/bin/env python3
"""
Universal Workshop ERP - Authentication Performance Benchmark
Tests login/logout cycles and session management performance
"""

import os
import sys
import time
import json
import statistics
import threading
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


class AuthenticationBenchmark:
    """
    Benchmark authentication system performance
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'base_url': base_url,
            'tests': {}
        }
    
    def test_login_page_load(self, iterations=10):
        """Test login page loading performance"""
        print("🔍 Testing login page load performance...")
        
        times = []
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}/login", timeout=10)
                load_time = (time.time() - start_time) * 1000
                times.append(load_time)
                
                if response.status_code == 200:
                    success_count += 1
                    
            except Exception as e:
                print(f"   ❌ Login page request failed: {e}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max_time
            
            print(f"   ✅ Login page load: {avg_time:.2f}ms avg ({min_time:.2f}-{max_time:.2f}ms)")
            print(f"   📊 95th percentile: {p95_time:.2f}ms")
            print(f"   ✔️  Success rate: {success_count}/{iterations} ({success_count/iterations*100:.1f}%)")
            
            self.results['tests']['login_page_load'] = {
                'iterations': iterations,
                'avg_time_ms': avg_time,
                'min_time_ms': min_time,
                'max_time_ms': max_time,
                'p95_time_ms': p95_time,
                'success_rate': success_count / iterations
            }
            
            return avg_time < 1000  # Pass if under 1 second
        
        return False
    
    def test_authentication_flow(self, iterations=5):
        """Test complete authentication flow"""
        print("🔐 Testing authentication flow performance...")
        
        login_times = []
        logout_times = []
        total_times = []
        success_count = 0
        
        for i in range(iterations):
            session = requests.Session()
            
            try:
                # Test login flow
                start_time = time.time()
                
                # Get login page first
                login_page_response = session.get(f"{self.base_url}/login", timeout=10)
                
                if login_page_response.status_code == 200:
                    # Simulate login attempt (will fail but we measure timing)
                    login_data = {
                        'usr': f'test_user_{i}',
                        'pwd': 'test_password'
                    }
                    
                    login_response = session.post(
                        f"{self.base_url}/api/method/login",
                        data=login_data,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )
                    
                    login_time = (time.time() - start_time) * 1000
                    login_times.append(login_time)
                    
                    # Test logout (even if login failed)
                    logout_start = time.time()
                    logout_response = session.post(f"{self.base_url}/api/method/logout", timeout=10)
                    logout_time = (time.time() - logout_start) * 1000
                    logout_times.append(logout_time)
                    
                    total_time = login_time + logout_time
                    total_times.append(total_time)
                    
                    success_count += 1
                    
            except Exception as e:
                print(f"   ❌ Auth flow {i+1} failed: {e}")
        
        if login_times and logout_times:
            avg_login = statistics.mean(login_times)
            avg_logout = statistics.mean(logout_times)
            avg_total = statistics.mean(total_times)
            
            print(f"   ✅ Login attempts: {avg_login:.2f}ms avg")
            print(f"   ✅ Logout requests: {avg_logout:.2f}ms avg")
            print(f"   🎯 Total auth cycle: {avg_total:.2f}ms avg")
            print(f"   ✔️  Success rate: {success_count}/{iterations} ({success_count/iterations*100:.1f}%)")
            
            self.results['tests']['authentication_flow'] = {
                'iterations': iterations,
                'avg_login_ms': avg_login,
                'avg_logout_ms': avg_logout,
                'avg_total_ms': avg_total,
                'success_rate': success_count / iterations
            }
            
            return avg_total < 3000  # Pass if total cycle under 3 seconds
        
        return False
    
    def test_concurrent_requests(self, num_threads=10, requests_per_thread=5):
        """Test concurrent request handling"""
        print(f"🚀 Testing concurrent requests ({num_threads} threads, {requests_per_thread} requests each)...")
        
        def make_requests(thread_id):
            """Make requests from a single thread"""
            thread_results = []
            session = requests.Session()
            
            for i in range(requests_per_thread):
                start_time = time.time()
                try:
                    # Test different endpoints
                    endpoints = ['/login', '/api/method/ping', '/']
                    endpoint = endpoints[i % len(endpoints)]
                    
                    response = session.get(f"{self.base_url}{endpoint}", timeout=10)
                    request_time = (time.time() - start_time) * 1000
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': i,
                        'endpoint': endpoint,
                        'time_ms': request_time,
                        'status_code': response.status_code,
                        'success': response.status_code < 500
                    })
                    
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': i,
                        'endpoint': endpoint,
                        'time_ms': 0,
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            return thread_results
        
        # Execute concurrent requests
        start_time = time.time()
        all_results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_requests, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    thread_results = future.result()
                    all_results.extend(thread_results)
                except Exception as e:
                    print(f"   ❌ Thread execution error: {e}")
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        if successful_requests:
            response_times = [r['time_ms'] for r in successful_requests]
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            throughput = len(successful_requests) / total_time
            success_rate = len(successful_requests) / len(all_results)
            
            print(f"   ✅ Requests completed: {len(successful_requests)}/{len(all_results)}")
            print(f"   📊 Average response time: {avg_time:.2f}ms")
            print(f"   📈 Throughput: {throughput:.2f} req/sec")
            print(f"   ✔️  Success rate: {success_rate*100:.1f}%")
            print(f"   ⏱️  Total execution time: {total_time:.2f}s")
            
            self.results['tests']['concurrent_requests'] = {
                'num_threads': num_threads,
                'requests_per_thread': requests_per_thread,
                'total_requests': len(all_results),
                'successful_requests': len(successful_requests),
                'avg_response_time_ms': avg_time,
                'min_response_time_ms': min_time,
                'max_response_time_ms': max_time,
                'throughput_rps': throughput,
                'success_rate': success_rate,
                'total_time_seconds': total_time
            }
            
            return success_rate > 0.8  # Pass if 80%+ success rate
        
        return False
    
    def test_session_simulation(self, duration_seconds=30):
        """Simulate user session with multiple requests"""
        print(f"👤 Simulating user session ({duration_seconds}s)...")
        
        session = requests.Session()
        session_results = []
        start_time = time.time()
        request_count = 0
        
        # Simulate user behavior
        endpoints = [
            '/login',
            '/api/method/ping',
            '/',
            '/app',
            '/api/method/frappe.auth.get_logged_user'
        ]
        
        while (time.time() - start_time) < duration_seconds:
            endpoint = endpoints[request_count % len(endpoints)]
            
            request_start = time.time()
            try:
                response = session.get(f"{self.base_url}{endpoint}", timeout=5)
                request_time = (time.time() - request_start) * 1000
                
                session_results.append({
                    'timestamp': time.time(),
                    'endpoint': endpoint,
                    'time_ms': request_time,
                    'status_code': response.status_code,
                    'success': response.status_code < 500
                })
                
                request_count += 1
                
                # Simulate user think time
                time.sleep(0.5)
                
            except Exception as e:
                session_results.append({
                    'timestamp': time.time(),
                    'endpoint': endpoint,
                    'time_ms': 0,
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Analyze session
        successful_requests = [r for r in session_results if r['success']]
        
        if successful_requests:
            response_times = [r['time_ms'] for r in successful_requests]
            avg_time = statistics.mean(response_times)
            total_session_time = time.time() - start_time
            
            print(f"   ✅ Session requests: {len(successful_requests)}/{len(session_results)}")
            print(f"   📊 Average response time: {avg_time:.2f}ms")
            print(f"   ⏱️  Session duration: {total_session_time:.1f}s")
            print(f"   📈 Requests per minute: {(len(successful_requests) / total_session_time) * 60:.1f}")
            
            self.results['tests']['session_simulation'] = {
                'duration_seconds': duration_seconds,
                'total_requests': len(session_results),
                'successful_requests': len(successful_requests),
                'avg_response_time_ms': avg_time,
                'requests_per_minute': (len(successful_requests) / total_session_time) * 60
            }
            
            return len(successful_requests) > 0
        
        return False
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🎯 Universal Workshop Authentication Performance Benchmark")
        print("=" * 70)
        print(f"Target URL: {self.base_url}")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_results = []
        
        # Test 1: Login page load
        result1 = self.test_login_page_load()
        test_results.append(('Login Page Load', result1))
        print()
        
        # Test 2: Authentication flow
        result2 = self.test_authentication_flow()
        test_results.append(('Authentication Flow', result2))
        print()
        
        # Test 3: Concurrent requests
        result3 = self.test_concurrent_requests()
        test_results.append(('Concurrent Requests', result3))
        print()
        
        # Test 4: Session simulation
        result4 = self.test_session_simulation(15)  # 15 second session
        test_results.append(('Session Simulation', result4))
        print()
        
        # Generate summary
        self.generate_summary(test_results)
        
        return test_results
    
    def generate_summary(self, test_results):
        """Generate test summary and save results"""
        print("📊 AUTHENTICATION PERFORMANCE SUMMARY")
        print("=" * 70)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Overall assessment
        if passed_tests == total_tests:
            overall = "🎉 EXCELLENT"
        elif passed_tests >= total_tests * 0.75:
            overall = "✅ GOOD"
        elif passed_tests >= total_tests * 0.5:
            overall = "⚠️  FAIR"
        else:
            overall = "❌ POOR"
        
        print(f"Overall Performance: {overall}")
        
        # Save results
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests,
            'overall_assessment': overall,
            'test_results': test_results
        }
        
        # Save to file
        results_dir = Path('test_results/performance')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"auth_benchmark_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Detailed results saved: {results_file}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Workshop Authentication Performance Benchmark")
    parser.add_argument('--url', type=str, default='http://localhost:8000', 
                       help='Base URL for testing (default: http://localhost:8000)')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick tests with reduced iterations')
    
    args = parser.parse_args()
    
    benchmark = AuthenticationBenchmark(args.url)
    
    if args.quick:
        print("🚀 Running quick authentication benchmark...")
        # Reduce iterations for quick test
        benchmark.test_login_page_load(5)
        benchmark.test_authentication_flow(3)
        benchmark.test_concurrent_requests(5, 3)
    else:
        benchmark.run_all_tests()


if __name__ == "__main__":
    main()
