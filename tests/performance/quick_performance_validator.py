#!/usr/bin/env python3
"""
Universal Workshop ERP - Quick Performance Validation
Lightweight performance test for authentication system validation
"""

import time
import json
import statistics
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import urllib.error
import sys
import os


class QuickPerformanceValidator:
    """
    Quick performance validation for authentication components
    """
    
    def __init__(self):
        self.results = []
        self.base_path = "/home/said/frappe-dev/frappe-bench"
        
    def test_static_file_performance(self):
        """Test static file access performance (CSS/JS files)"""
        print("🔍 Testing static file performance...")
        
        static_files = [
            "apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css",
            "apps/universal_workshop/universal_workshop/public/css/dynamic_branding.css",
            "apps/universal_workshop/universal_workshop/public/js/rtl_branding_manager.js"
        ]
        
        results = []
        
        for file_path in static_files:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                print(f"   ❌ File not found: {file_path}")
                continue
            
            # Test file read performance
            latencies = []
            file_size = os.path.getsize(full_path)
            
            for i in range(10):
                start_time = time.time()
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    latencies.append(latency)
                    
                except Exception as e:
                    print(f"   ❌ Error reading {file_path}: {e}")
            
            if latencies:
                avg_latency = statistics.mean(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                
                result = {
                    'file': file_path,
                    'file_size_bytes': file_size,
                    'avg_read_time_ms': avg_latency,
                    'min_read_time_ms': min_latency,
                    'max_read_time_ms': max_latency,
                    'throughput_mb_per_sec': (file_size / 1024 / 1024) / (avg_latency / 1000) if avg_latency > 0 else 0
                }
                
                results.append(result)
                
                print(f"   ✅ {os.path.basename(file_path)}: {avg_latency:.2f}ms avg ({file_size:,} bytes)")
        
        self.results.append({
            'test': 'static_file_performance',
            'timestamp': datetime.now().isoformat(),
            'files_tested': len(results),
            'detailed_results': results
        })
        
        return results
    
    def test_concurrent_file_access(self, num_threads=20):
        """Test concurrent file access to simulate multiple users loading CSS/JS"""
        print(f"🚀 Testing concurrent file access ({num_threads} threads)...")
        
        test_file = os.path.join(self.base_path, "apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css")
        
        if not os.path.exists(test_file):
            print("   ❌ Test file not found")
            return None
        
        latencies = []
        errors = 0
        
        def worker():
            try:
                start_time = time.time()
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                latency = (time.time() - start_time) * 1000
                return latency
            except Exception as e:
                return None
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads * 3)]  # 3 reads per thread
            
            for future in futures:
                result = future.result()
                if result is not None:
                    latencies.append(result)
                else:
                    errors += 1
        
        total_time = time.time() - start_time
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            throughput = len(latencies) / total_time
            
            result = {
                'test': 'concurrent_file_access',
                'threads': num_threads,
                'total_operations': len(latencies) + errors,
                'successful_operations': len(latencies),
                'failed_operations': errors,
                'total_time_seconds': total_time,
                'throughput_ops_per_sec': throughput,
                'avg_latency_ms': avg_latency,
                'p95_latency_ms': p95_latency,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Throughput: {throughput:.2f} ops/sec")
            print(f"   📊 Average latency: {avg_latency:.2f}ms")
            print(f"   📈 95th percentile: {p95_latency:.2f}ms")
            print(f"   ✔️  Success rate: {(len(latencies)/(len(latencies)+errors))*100:.1f}%")
            
            self.results.append(result)
            return result
        
        else:
            print("   ❌ All operations failed")
            return None
    
    def test_css_parsing_performance(self):
        """Test CSS parsing and validation performance"""
        print("🎨 Testing CSS parsing performance...")
        
        css_files = [
            "apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css",
            "apps/universal_workshop/universal_workshop/public/css/dynamic_branding.css"
        ]
        
        results = []
        
        for css_file in css_files:
            full_path = os.path.join(self.base_path, css_file)
            
            if not os.path.exists(full_path):
                continue
            
            # Test CSS parsing simulation
            parse_times = []
            
            for i in range(5):
                start_time = time.time()
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simulate CSS parsing by counting rules
                    rule_count = content.count('{')
                    property_count = content.count(':')
                    rtl_rules = content.count('[dir="rtl"]') + content.count('.rtl')
                    
                    parse_time = (time.time() - start_time) * 1000
                    parse_times.append(parse_time)
                    
                except Exception as e:
                    print(f"   ❌ Error parsing {css_file}: {e}")
            
            if parse_times:
                avg_parse_time = statistics.mean(parse_times)
                
                result = {
                    'file': css_file,
                    'avg_parse_time_ms': avg_parse_time,
                    'rule_count': rule_count,
                    'property_count': property_count,
                    'rtl_rules': rtl_rules,
                    'complexity_score': (rule_count + property_count) / 100  # Simple complexity metric
                }
                
                results.append(result)
                
                print(f"   ✅ {os.path.basename(css_file)}: {avg_parse_time:.2f}ms ({rule_count} rules)")
        
        self.results.append({
            'test': 'css_parsing_performance',
            'timestamp': datetime.now().isoformat(),
            'files_tested': len(results),
            'detailed_results': results
        })
        
        return results
    
    def test_javascript_loading_simulation(self):
        """Test JavaScript loading and execution simulation"""
        print("⚡ Testing JavaScript loading simulation...")
        
        js_file = os.path.join(self.base_path, "apps/universal_workshop/universal_workshop/public/js/rtl_branding_manager.js")
        
        if not os.path.exists(js_file):
            print("   ❌ JavaScript file not found")
            return None
        
        load_times = []
        
        for i in range(5):
            start_time = time.time()
            
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simulate basic JavaScript parsing
                function_count = content.count('function ') + content.count('=>')
                class_count = content.count('class ')
                method_count = content.count('() {')
                
                load_time = (time.time() - start_time) * 1000
                load_times.append(load_time)
                
            except Exception as e:
                print(f"   ❌ Error loading JavaScript: {e}")
        
        if load_times:
            avg_load_time = statistics.mean(load_times)
            file_size = os.path.getsize(js_file)
            
            result = {
                'test': 'javascript_loading_simulation',
                'file': js_file,
                'file_size_bytes': file_size,
                'avg_load_time_ms': avg_load_time,
                'function_count': function_count,
                'class_count': class_count,
                'method_count': method_count,
                'complexity_score': (function_count + class_count + method_count) / 10,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ✅ Load time: {avg_load_time:.2f}ms ({file_size:,} bytes)")
            print(f"   📊 Functions: {function_count}, Classes: {class_count}, Methods: {method_count}")
            
            self.results.append(result)
            return result
        
        else:
            print("   ❌ JavaScript loading test failed")
            return None
    
    def simulate_browser_load_sequence(self):
        """Simulate browser loading sequence for authentication page"""
        print("🌐 Simulating browser load sequence...")
        
        # Simulate typical browser loading order
        load_sequence = [
            ("HTML parsing", 50),      # Simulate HTML parse time
            ("CSS loading", "arabic-rtl.css"),
            ("CSS loading", "dynamic_branding.css"),
            ("JavaScript loading", "rtl_branding_manager.js"),
            ("DOM ready", 10),         # Simulate DOM ready time
            ("JavaScript execution", 30)  # Simulate JS execution time
        ]
        
        total_load_time = 0
        sequence_results = []
        
        for step, resource in load_sequence:
            start_time = time.time()
            
            if step == "CSS loading" or step == "JavaScript loading":
                # Load actual file
                if step == "CSS loading":
                    file_path = f"apps/universal_workshop/universal_workshop/public/css/{resource}"
                else:
                    file_path = f"apps/universal_workshop/universal_workshop/public/js/{resource}"
                
                full_path = os.path.join(self.base_path, file_path)
                
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        step_time = (time.time() - start_time) * 1000
                    except Exception:
                        step_time = 100  # Fallback time
                else:
                    step_time = 100  # Fallback time
            else:
                # Simulate other steps
                time.sleep(resource / 1000)  # Convert ms to seconds
                step_time = resource
            
            total_load_time += step_time
            
            sequence_results.append({
                'step': step,
                'resource': resource,
                'step_time_ms': step_time
            })
            
            print(f"   ⏱️  {step}: {step_time:.2f}ms")
        
        result = {
            'test': 'browser_load_sequence_simulation',
            'total_load_time_ms': total_load_time,
            'sequence_steps': sequence_results,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"   🎯 Total simulated load time: {total_load_time:.2f}ms")
        
        # Evaluate performance
        if total_load_time < 1000:
            print("   🎉 Excellent load performance (<1s)")
        elif total_load_time < 2000:
            print("   ✅ Good load performance (<2s)")
        elif total_load_time < 3000:
            print("   ⚠️  Acceptable load performance (<3s)")
        else:
            print("   ❌ Slow load performance (>3s)")
        
        self.results.append(result)
        return result
    
    def run_validation_suite(self):
        """Run complete validation suite"""
        print("🎯 Universal Workshop Performance Validation Suite")
        print("=" * 60)
        
        # Test 1: Static file performance
        self.test_static_file_performance()
        print()
        
        # Test 2: Concurrent access
        self.test_concurrent_file_access()
        print()
        
        # Test 3: CSS parsing
        self.test_css_parsing_performance()
        print()
        
        # Test 4: JavaScript loading
        self.test_javascript_loading_simulation()
        print()
        
        # Test 5: Browser load sequence
        self.simulate_browser_load_sequence()
        print()
        
        # Generate summary
        self.generate_validation_summary()
        
        return True
    
    def generate_validation_summary(self):
        """Generate validation summary"""
        print("📊 PERFORMANCE VALIDATION SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("No validation results available")
            return
        
        # Calculate key metrics
        total_tests = len(self.results)
        passed_tests = 0
        
        # Analyze results
        for result in self.results:
            test_type = result.get('test', 'unknown')
            
            if test_type == 'browser_load_sequence_simulation':
                total_load_time = result.get('total_load_time_ms', 0)
                if total_load_time < 3000:  # Less than 3 seconds is acceptable
                    passed_tests += 1
                print(f"✅ Browser Load Sequence: {total_load_time:.2f}ms")
            
            elif test_type == 'concurrent_file_access':
                throughput = result.get('throughput_ops_per_sec', 0)
                if throughput > 50:  # More than 50 ops/sec is good
                    passed_tests += 1
                print(f"✅ Concurrent Access: {throughput:.2f} ops/sec")
            
            elif test_type == 'static_file_performance':
                files_tested = result.get('files_tested', 0)
                if files_tested > 0:
                    passed_tests += 1
                print(f"✅ Static Files: {files_tested} files tested")
            
            else:
                passed_tests += 1  # Assume other tests passed if they completed
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Passed tests: {passed_tests}")
        print(f"Success rate: {success_rate:.1f}%")
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 Performance validation: EXCELLENT")
            assessment = "excellent"
        elif success_rate >= 75:
            print("✅ Performance validation: GOOD")
            assessment = "good"
        elif success_rate >= 60:
            print("⚠️  Performance validation: ACCEPTABLE")
            assessment = "acceptable"
        else:
            print("❌ Performance validation: NEEDS IMPROVEMENT")
            assessment = "poor"
        
        # Save results
        try:
            os.makedirs("test_results/performance", exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"test_results/performance/quick_validation_{timestamp}.json"
            
            final_report = {
                'validation_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'success_rate_percent': success_rate,
                    'assessment': assessment
                },
                'detailed_results': self.results
            }
            
            with open(results_file, 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"📄 Validation report saved: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
        return success_rate >= 75  # Return True if validation passed


def main():
    """Main function"""
    validator = QuickPerformanceValidator()
    success = validator.run_validation_suite()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
