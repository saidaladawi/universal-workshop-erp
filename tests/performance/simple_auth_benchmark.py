#!/usr/bin/env python3
"""
Universal Workshop ERP - Simple Authentication Performance Benchmark
Quick benchmark for authentication and session management performance
"""

import time
import json
import requests
import threading
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import sys


class AuthenticationBenchmark:
    """
    Simple authentication performance benchmark
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results = []
        self.session = requests.Session()
        
    def check_server_availability(self):
        """Check if the server is running"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code < 500
        except Exception as e:
            print(f"❌ Server not available: {e}")
            return False
    
    def get_login_page(self):
        """Get login page and extract necessary tokens"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            return response.status_code == 200, response
        except Exception as e:
            return False, str(e)
    
    def test_login_latency(self, num_requests=10):
        """Test login page load latency"""
        print(f"🔍 Testing login page latency ({num_requests} requests)...")
        
        latencies = []
        errors = 0
        
        for i in range(num_requests):
            start_time = time.time()
            
            try:
                success, response = self.get_login_page()
                latency = time.time() - start_time
                
                if success:
                    latencies.append(latency * 1000)  # Convert to milliseconds
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                print(f"   Error {i+1}: {e}")
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            median_latency = statistics.median(latencies)
            
            result = {
                'test': 'login_page_latency',
                'requests': num_requests,
                'successful': len(latencies),
                'errors': errors,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'median_latency_ms': median_latency,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Average latency: {avg_latency:.2f}ms")
            print(f"   📊 Min/Max: {min_latency:.2f}ms / {max_latency:.2f}ms")
            print(f"   📈 Success rate: {(len(latencies)/num_requests)*100:.1f}%")
            
            self.results.append(result)
            return result
        
        else:
            print("   ❌ All requests failed")
            return None
    
    def test_concurrent_access(self, num_threads=50, requests_per_thread=5):
        """Test concurrent access to login page"""
        print(f"🚀 Testing concurrent access ({num_threads} threads, {requests_per_thread} requests each)...")
        
        all_latencies = []
        total_errors = 0
        results_queue = queue.Queue()
        
        def worker():
            worker_latencies = []
            worker_errors = 0
            
            for _ in range(requests_per_thread):
                start_time = time.time()
                
                try:
                    success, response = self.get_login_page()
                    latency = time.time() - start_time
                    
                    if success:
                        worker_latencies.append(latency * 1000)
                    else:
                        worker_errors += 1
                        
                except Exception as e:
                    worker_errors += 1
            
            results_queue.put({
                'latencies': worker_latencies,
                'errors': worker_errors
            })
        
        # Run concurrent tests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"   Thread error: {e}")
        
        total_time = time.time() - start_time
        
        # Collect results
        while not results_queue.empty():
            worker_result = results_queue.get()
            all_latencies.extend(worker_result['latencies'])
            total_errors += worker_result['errors']
        
        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            min_latency = min(all_latencies)
            max_latency = max(all_latencies)
            p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
            p99_latency = sorted(all_latencies)[int(len(all_latencies) * 0.99)]
            
            total_requests = num_threads * requests_per_thread
            throughput = len(all_latencies) / total_time
            
            result = {
                'test': 'concurrent_access',
                'threads': num_threads,
                'requests_per_thread': requests_per_thread,
                'total_requests': total_requests,
                'successful': len(all_latencies),
                'errors': total_errors,
                'total_time_seconds': total_time,
                'throughput_rps': throughput,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'p95_latency_ms': p95_latency,
                'p99_latency_ms': p99_latency,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Total time: {total_time:.2f}s")
            print(f"   🚀 Throughput: {throughput:.2f} requests/sec")
            print(f"   📊 Average latency: {avg_latency:.2f}ms")
            print(f"   📈 95th percentile: {p95_latency:.2f}ms")
            print(f"   📉 99th percentile: {p99_latency:.2f}ms")
            print(f"   ✔️  Success rate: {(len(all_latencies)/total_requests)*100:.1f}%")
            
            self.results.append(result)
            return result
        
        else:
            print("   ❌ All concurrent requests failed")
            return None
    
    def test_api_endpoint_performance(self, endpoint="/api/method/ping", num_requests=20):
        """Test API endpoint performance"""
        print(f"🔌 Testing API endpoint performance: {endpoint} ({num_requests} requests)...")
        
        latencies = []
        errors = 0
        
        for i in range(num_requests):
            start_time = time.time()
            
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                latency = time.time() - start_time
                
                if response.status_code < 500:
                    latencies.append(latency * 1000)
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            result = {
                'test': 'api_endpoint_performance',
                'endpoint': endpoint,
                'requests': num_requests,
                'successful': len(latencies),
                'errors': errors,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Average latency: {avg_latency:.2f}ms")
            print(f"   📊 Min/Max: {min_latency:.2f}ms / {max_latency:.2f}ms")
            print(f"   📈 Success rate: {(len(latencies)/num_requests)*100:.1f}%")
            
            self.results.append(result)
            return result
        
        else:
            print("   ❌ All API requests failed")
            return None
    
    def run_comprehensive_benchmark(self):
        """Run comprehensive performance benchmark"""
        print("🎯 Universal Workshop Authentication Performance Benchmark")
        print("=" * 60)
        
        if not self.check_server_availability():
            print("❌ Server is not available. Make sure Frappe/ERPNext is running.")
            return False
        
        print("✅ Server is available")
        
        # Test 1: Basic login page latency
        self.test_login_latency(10)
        
        print()
        
        # Test 2: Concurrent access
        self.test_concurrent_access(20, 3)
        
        print()
        
        # Test 3: API endpoints
        api_endpoints = [
            "/api/method/ping",
            "/api/method/frappe.auth.get_logged_user",
            "/api/resource/User?limit_page_length=5"
        ]
        
        for endpoint in api_endpoints:
            self.test_api_endpoint_performance(endpoint, 10)
            print()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate benchmark summary"""
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("No results to summarize")
            return
        
        # Calculate overall statistics
        all_avg_latencies = [r['avg_latency_ms'] for r in self.results if 'avg_latency_ms' in r]
        total_requests = sum(r.get('total_requests', r.get('requests', 0)) for r in self.results)
        total_successful = sum(r.get('successful', 0) for r in self.results)
        total_errors = sum(r.get('errors', 0) for r in self.results)
        
        if all_avg_latencies:
            overall_avg_latency = statistics.mean(all_avg_latencies)
            print(f"Overall average latency: {overall_avg_latency:.2f}ms")
        
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {total_successful}")
        print(f"Failed requests: {total_errors}")
        
        if total_requests > 0:
            success_rate = (total_successful / total_requests) * 100
            print(f"Overall success rate: {success_rate:.1f}%")
            
            # Performance evaluation
            if success_rate >= 95 and (not all_avg_latencies or overall_avg_latency < 2000):
                print("🎉 Performance: EXCELLENT")
            elif success_rate >= 90 and (not all_avg_latencies or overall_avg_latency < 3000):
                print("✅ Performance: GOOD")
            elif success_rate >= 80 and (not all_avg_latencies or overall_avg_latency < 5000):
                print("⚠️  Performance: ACCEPTABLE")
            else:
                print("❌ Performance: NEEDS IMPROVEMENT")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"test_results/performance/simple_benchmark_{timestamp}.json"
        
        try:
            import os
            os.makedirs("test_results/performance", exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    'benchmark_summary': {
                        'timestamp': datetime.now().isoformat(),
                        'total_requests': total_requests,
                        'successful_requests': total_successful,
                        'failed_requests': total_errors,
                        'overall_avg_latency_ms': overall_avg_latency if all_avg_latencies else None,
                        'success_rate_percent': success_rate if total_requests > 0 else 0
                    },
                    'detailed_results': self.results
                }, f, indent=2)
            
            print(f"📄 Results saved: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Workshop Authentication Performance Benchmark")
    parser.add_argument('--url', type=str, default='http://localhost:8000',
                       help='Base URL for the Frappe/ERPNext server')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick benchmark with fewer requests')
    
    args = parser.parse_args()
    
    benchmark = AuthenticationBenchmark(args.url)
    
    if args.quick:
        print("🏃 Running quick benchmark...")
        benchmark.test_login_latency(5)
        benchmark.test_concurrent_access(10, 2)
        benchmark.generate_summary()
    else:
        benchmark.run_comprehensive_benchmark()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
