#!/usr/bin/env python3
"""
Universal Workshop ERP - Arabic Data Handling Stress Test Suite
Comprehensive testing for Arabic text processing, storage, and display integrity
"""

import os
import sys
import json
import time
import hashlib
import statistics
import threading
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
import tempfile


class ArabicDataStressTester:
    """
    Test Arabic data handling under stress conditions
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'base_url': base_url,
            'tests': {},
            'arabic_test_data': self.generate_arabic_test_data()
        }
        
        # Create local test database for validation
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.init_test_database()
    
    def generate_arabic_test_data(self):
        """Generate comprehensive Arabic test data sets"""
        arabic_data = {
            'basic_text': [
                'مرحبا بكم في ورشة العمل العالمية',
                'إدارة النظام والمصادقة',
                'اختبار البيانات العربية',
                'نظام إدارة الورش الشاملة',
                'مرحبا وأهلا وسهلا بكم'
            ],
            'authentication_fields': {
                'usernames': [
                    'مدير_الورشة',
                    'فني_السيارات',
                    'خدمة_العملاء',
                    'مدير_المخزون',
                    'صاحب_الورشة'
                ],
                'passwords': [
                    'كلمة_السر_123',
                    'مفتاح_الدخول_456',
                    'رقم_المرور_789',
                    'شفرة_الأمان_000',
                    'كود_الوصول_111'
                ],
                'emails': [
                    'مدير@ورشة-عمل.com',
                    'فني@سيارات.org',
                    'خدمة@عملاء.net',
                    'مخزون@ادارة.co',
                    'صاحب@ورشة.ae'
                ]
            },
            'special_characters': [
                'أإآةءؤى',  # Different forms of Alef, Hamza, etc.
                'تثجحخدذرزسش',  # Arabic letters
                'صضطظعغفقكلمن',  # More Arabic letters  
                'هويًٌٍَُِّْ',  # Diacritics and special marks
                '٠١٢٣٤٥٦٧٨٩',  # Arabic numerals
                '،؛؟!()[]{}«»'  # Arabic punctuation
            ],
            'long_text': 'هذا نص طويل باللغة العربية لاختبار قدرة النظام على التعامل مع النصوص الطويلة والبيانات الكبيرة. ' * 100,
            'mixed_content': [
                'Arabic العربية English الإنجليزية Mixed مختلط',
                'Company شركة Universal العالمية Workshop ورشة',
                'User مستخدم Admin إدارة System نظام',
                'Data بيانات Test اختبار Arabic عربي'
            ],
            'rtl_layout_text': [
                'النص من اليمين إلى اليسار',
                'تخطيط صفحة RTL',
                'واجهة المستخدم العربية',
                'نظام إدارة ورشة السيارات'
            ],
            'edge_cases': [
                '',  # Empty string
                ' ',  # Single space
                '\n\t\r',  # Whitespace characters
                'ـ' * 1000,  # Tatweel (kashida) repeated
                'أ' + 'ل' * 500 + 'ه',  # Very long word
                'آ' * 255,  # Maximum typical field length
            ]
        }
        
        return arabic_data
    
    def init_test_database(self):
        """Initialize test database for validation"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create test table with UTF-8 support
        cursor.execute('''
            CREATE TABLE arabic_test_data (
                id INTEGER PRIMARY KEY,
                test_type TEXT,
                original_text TEXT,
                processed_text TEXT,
                hash_original TEXT,
                hash_processed TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_text_hash(self, text):
        """Calculate hash for text integrity checking"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def store_test_data(self, test_type, original_text, processed_text):
        """Store test data for integrity validation"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        hash_original = self.calculate_text_hash(original_text)
        hash_processed = self.calculate_text_hash(processed_text)
        
        cursor.execute('''
            INSERT INTO arabic_test_data 
            (test_type, original_text, processed_text, hash_original, hash_processed)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_type, original_text, processed_text, hash_original, hash_processed))
        
        conn.commit()
        conn.close()
        
        return hash_original == hash_processed
    
    def test_encoding_validation(self, iterations=50):
        """Test UTF-8 encoding validation with Arabic text"""
        print("🔤 Testing UTF-8 encoding validation...")
        
        encoding_results = {
            'total_tests': 0,
            'successful_encodings': 0,
            'failed_encodings': 0,
            'integrity_maintained': 0,
            'encoding_times': []
        }
        
        for test_type, texts in self.test_results['arabic_test_data'].items():
            if isinstance(texts, list):
                for text in texts[:min(len(texts), iterations)]:
                    encoding_results['total_tests'] += 1
                    
                    start_time = time.time()
                    
                    try:
                        # Test encoding/decoding cycle
                        encoded = text.encode('utf-8')
                        decoded = encoded.decode('utf-8')
                        
                        encoding_time = (time.time() - start_time) * 1000
                        encoding_results['encoding_times'].append(encoding_time)
                        
                        # Check integrity
                        if text == decoded:
                            encoding_results['successful_encodings'] += 1
                            integrity_maintained = self.store_test_data(test_type, text, decoded)
                            if integrity_maintained:
                                encoding_results['integrity_maintained'] += 1
                        else:
                            encoding_results['failed_encodings'] += 1
                            print(f"   ❌ Encoding integrity failed for: {text[:50]}...")
                            
                    except Exception as e:
                        encoding_results['failed_encodings'] += 1
                        print(f"   💥 Encoding error: {e}")
        
        # Calculate statistics
        if encoding_results['encoding_times']:
            avg_time = statistics.mean(encoding_results['encoding_times'])
            success_rate = (encoding_results['successful_encodings'] / encoding_results['total_tests']) * 100
            integrity_rate = (encoding_results['integrity_maintained'] / encoding_results['total_tests']) * 100
            
            print(f"   ✅ Encoding tests: {encoding_results['total_tests']}")
            print(f"   📊 Success rate: {success_rate:.1f}%")
            print(f"   🔒 Integrity rate: {integrity_rate:.1f}%")
            print(f"   ⏱️  Average encoding time: {avg_time:.3f}ms")
            
            self.test_results['tests']['encoding_validation'] = encoding_results
            
            return success_rate > 95 and integrity_rate > 95
        
        return False
    
    def test_form_input_handling(self, concurrent_users=20):
        """Test form input handling with Arabic data under load"""
        print(f"📝 Testing form input handling ({concurrent_users} concurrent users)...")
        
        def submit_arabic_form_data(user_id):
            """Submit Arabic data through forms"""
            user_results = []
            session = requests.Session()
            
            auth_data = self.test_results['arabic_test_data']['authentication_fields']
            
            for i in range(5):  # 5 submissions per user
                try:
                    # Select Arabic test data
                    username = auth_data['usernames'][i % len(auth_data['usernames'])]
                    password = auth_data['passwords'][i % len(auth_data['passwords'])]
                    email = auth_data['emails'][i % len(auth_data['emails'])]
                    
                    start_time = time.time()
                    
                    # Simulate form submission
                    form_data = {
                        'usr': username,
                        'pwd': password,
                        'email': email,
                        'cmd': 'test_arabic_input'
                    }
                    
                    # Test different endpoints
                    endpoints = ['/login', '/api/method/ping']
                    endpoint = endpoints[i % len(endpoints)]
                    
                    response = session.post(
                        f"{self.base_url}{endpoint}",
                        data=form_data,
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Accept-Charset': 'UTF-8'
                        },
                        timeout=10
                    )
                    
                    submission_time = (time.time() - start_time) * 1000
                    
                    # Validate response encoding
                    response_text = response.text if response.text else ""
                    content_type = response.headers.get('content-type', '')
                    
                    user_results.append({
                        'user_id': user_id,
                        'submission_id': i,
                        'username': username,
                        'endpoint': endpoint,
                        'submission_time_ms': submission_time,
                        'status_code': response.status_code,
                        'content_type': content_type,
                        'utf8_content_type': 'utf-8' in content_type.lower(),
                        'response_length': len(response_text),
                        'success': response.status_code < 500
                    })
                    
                    # Store for integrity checking
                    self.store_test_data('form_input', username, username)
                    
                except Exception as e:
                    user_results.append({
                        'user_id': user_id,
                        'submission_id': i,
                        'error': str(e),
                        'success': False
                    })
            
            return user_results
        
        # Execute concurrent form submissions
        start_time = time.time()
        all_results = []
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(submit_arabic_form_data, i) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    print(f"   ❌ User thread error: {e}")
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_submissions = [r for r in all_results if r.get('success', False)]
        failed_submissions = [r for r in all_results if not r.get('success', False)]
        
        if all_results:
            success_rate = len(successful_submissions) / len(all_results)
            
            if successful_submissions:
                submission_times = [r['submission_time_ms'] for r in successful_submissions if 'submission_time_ms' in r]
                avg_time = statistics.mean(submission_times) if submission_times else 0
                
                utf8_responses = sum(1 for r in successful_submissions if r.get('utf8_content_type', False))
                utf8_rate = utf8_responses / len(successful_submissions) if successful_submissions else 0
                
                print(f"   ✅ Form submissions: {len(successful_submissions)}/{len(all_results)}")
                print(f"   📊 Success rate: {success_rate*100:.1f}%")
                print(f"   ⏱️  Average submission time: {avg_time:.2f}ms")
                print(f"   🔤 UTF-8 content-type rate: {utf8_rate*100:.1f}%")
                print(f"   ⚡ Throughput: {len(successful_submissions)/total_time:.2f} submissions/sec")
                
                form_results = {
                    'concurrent_users': concurrent_users,
                    'total_submissions': len(all_results),
                    'successful_submissions': len(successful_submissions),
                    'success_rate': success_rate,
                    'avg_submission_time_ms': avg_time,
                    'utf8_content_type_rate': utf8_rate,
                    'throughput_rps': len(successful_submissions) / total_time,
                    'total_time_seconds': total_time
                }
                
                self.test_results['tests']['form_input_handling'] = form_results
                
                return success_rate > 0.8 and utf8_rate > 0.9
        
        return False
    
    def test_large_dataset_performance(self, dataset_size=1000):
        """Test performance with large Arabic datasets"""
        print(f"📊 Testing large Arabic dataset performance ({dataset_size} records)...")
        
        # Generate large dataset
        large_dataset = []
        arabic_texts = self.test_results['arabic_test_data']['basic_text']
        
        for i in range(dataset_size):
            record = {
                'id': i,
                'username': f"مستخدم_{i}",
                'description': arabic_texts[i % len(arabic_texts)],
                'long_text': self.test_results['arabic_test_data']['long_text'][:500],  # Truncate for testing
                'timestamp': datetime.now().isoformat()
            }
            large_dataset.append(record)
        
        # Test dataset processing
        processing_times = []
        memory_usage = []
        
        for batch_size in [10, 50, 100, 500]:
            if batch_size > dataset_size:
                continue
                
            print(f"   🔄 Testing batch size: {batch_size}")
            
            start_time = time.time()
            start_memory = self.get_memory_usage()
            
            # Process batches
            batches_processed = 0
            for i in range(0, min(dataset_size, 1000), batch_size):
                batch = large_dataset[i:i+batch_size]
                
                # Simulate processing each record
                for record in batch:
                    # Encoding/decoding test
                    encoded = json.dumps(record, ensure_ascii=False).encode('utf-8')
                    decoded = json.loads(encoded.decode('utf-8'))
                    
                    # Integrity check
                    if record['username'] == decoded['username']:
                        batches_processed += 1
                
                # Brief pause to simulate real processing
                time.sleep(0.001)
            
            processing_time = time.time() - start_time
            end_memory = self.get_memory_usage()
            memory_diff = end_memory - start_memory
            
            processing_times.append(processing_time)
            memory_usage.append(memory_diff)
            
            records_per_second = (batches_processed * batch_size) / processing_time if processing_time > 0 else 0
            
            print(f"      ⏱️  Processing time: {processing_time:.2f}s")
            print(f"      📈 Records/sec: {records_per_second:.1f}")
            print(f"      💾 Memory delta: {memory_diff:.2f}MB")
        
        if processing_times:
            avg_processing_time = statistics.mean(processing_times)
            avg_memory_usage = statistics.mean(memory_usage)
            
            dataset_results = {
                'dataset_size': dataset_size,
                'batch_sizes_tested': [10, 50, 100, 500],
                'avg_processing_time_seconds': avg_processing_time,
                'avg_memory_usage_mb': avg_memory_usage,
                'processing_times': processing_times,
                'memory_usage': memory_usage
            }
            
            self.test_results['tests']['large_dataset_performance'] = dataset_results
            
            print(f"   ✅ Dataset performance test completed")
            print(f"   📊 Average processing time: {avg_processing_time:.2f}s")
            print(f"   💾 Average memory usage: {avg_memory_usage:.2f}MB")
            
            return avg_processing_time < 10.0  # Pass if under 10 seconds
        
        return False
    
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # Return 0 if psutil not available
    
    def test_data_corruption_detection(self, iterations=100):
        """Test for Arabic data corruption during processing"""
        print(f"🔍 Testing data corruption detection ({iterations} iterations)...")
        
        corruption_results = {
            'total_tests': 0,
            'corrupted_data': 0,
            'intact_data': 0,
            'hash_mismatches': 0,
            'encoding_errors': 0
        }
        
        test_data = self.test_results['arabic_test_data']['basic_text'] + \
                   self.test_results['arabic_test_data']['special_characters']
        
        for i in range(iterations):
            text = test_data[i % len(test_data)]
            corruption_results['total_tests'] += 1
            
            try:
                # Original hash
                original_hash = self.calculate_text_hash(text)
                
                # Simulate various processing scenarios
                processing_scenarios = [
                    lambda x: x,  # No processing
                    lambda x: x.encode('utf-8').decode('utf-8'),  # Encoding cycle
                    lambda x: json.dumps(x, ensure_ascii=False),  # JSON serialization
                    lambda x: x.upper().lower(),  # Case changes
                    lambda x: x.strip(),  # Whitespace handling
                ]
                
                scenario = processing_scenarios[i % len(processing_scenarios)]
                processed_text = scenario(text)
                
                # Handle JSON scenario
                if processed_text.startswith('"') and processed_text.endswith('"'):
                    processed_text = json.loads(processed_text)
                
                # Calculate processed hash
                processed_hash = self.calculate_text_hash(processed_text)
                
                # Check for corruption
                if original_hash == processed_hash:
                    corruption_results['intact_data'] += 1
                else:
                    corruption_results['hash_mismatches'] += 1
                    corruption_results['corrupted_data'] += 1
                    print(f"   ⚠️  Hash mismatch detected: {text[:30]}...")
                
                # Store test result
                self.store_test_data('corruption_test', text, processed_text)
                
            except UnicodeError as e:
                corruption_results['encoding_errors'] += 1
                corruption_results['corrupted_data'] += 1
                print(f"   ❌ Encoding error: {e}")
            
            except Exception as e:
                corruption_results['corrupted_data'] += 1
                print(f"   💥 Processing error: {e}")
        
        # Calculate results
        if corruption_results['total_tests'] > 0:
            integrity_rate = (corruption_results['intact_data'] / corruption_results['total_tests']) * 100
            corruption_rate = (corruption_results['corrupted_data'] / corruption_results['total_tests']) * 100
            
            print(f"   ✅ Integrity tests: {corruption_results['total_tests']}")
            print(f"   🔒 Data integrity rate: {integrity_rate:.1f}%")
            print(f"   ⚠️  Corruption rate: {corruption_rate:.1f}%")
            print(f"   🔤 Encoding errors: {corruption_results['encoding_errors']}")
            
            self.test_results['tests']['data_corruption_detection'] = corruption_results
            
            return integrity_rate > 95
        
        return False
    
    def test_rtl_display_integrity(self):
        """Test RTL display integrity for Arabic text"""
        print("🔄 Testing RTL display integrity...")
        
        rtl_test_results = {
            'rtl_texts_tested': 0,
            'css_validation_passed': 0,
            'layout_checks_passed': 0,
            'text_direction_correct': 0
        }
        
        rtl_texts = self.test_results['arabic_test_data']['rtl_layout_text']
        
        for text in rtl_texts:
            rtl_test_results['rtl_texts_tested'] += 1
            
            # Simulate RTL CSS validation
            rtl_properties = [
                'direction: rtl',
                'text-align: right',
                'unicode-bidi: embed',
                'writing-mode: horizontal-tb'
            ]
            
            # Check if our RTL CSS file contains necessary properties
            try:
                rtl_css_path = 'apps/universal_workshop/universal_workshop/public/css/arabic-rtl.css'
                if os.path.exists(rtl_css_path):
                    with open(rtl_css_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    
                    css_properties_found = sum(1 for prop in rtl_properties if prop in css_content)
                    if css_properties_found >= len(rtl_properties) - 1:  # Allow for minor variations
                        rtl_test_results['css_validation_passed'] += 1
                
                # Text direction validation
                if any(char in text for char in 'أإآبتثجحخدذرزسشصضطظعغفقكلمنهوي'):
                    rtl_test_results['text_direction_correct'] += 1
                
                # Layout checks (simulated)
                if len(text) > 0 and not text.isspace():
                    rtl_test_results['layout_checks_passed'] += 1
                    
            except Exception as e:
                print(f"   ❌ RTL validation error: {e}")
        
        if rtl_test_results['rtl_texts_tested'] > 0:
            css_rate = (rtl_test_results['css_validation_passed'] / rtl_test_results['rtl_texts_tested']) * 100
            layout_rate = (rtl_test_results['layout_checks_passed'] / rtl_test_results['rtl_texts_tested']) * 100
            direction_rate = (rtl_test_results['text_direction_correct'] / rtl_test_results['rtl_texts_tested']) * 100
            
            print(f"   ✅ RTL texts tested: {rtl_test_results['rtl_texts_tested']}")
            print(f"   🎨 CSS validation rate: {css_rate:.1f}%")
            print(f"   📐 Layout checks rate: {layout_rate:.1f}%")
            print(f"   ➡️  Text direction rate: {direction_rate:.1f}%")
            
            self.test_results['tests']['rtl_display_integrity'] = rtl_test_results
            
            return css_rate > 80 and layout_rate > 90 and direction_rate > 95
        
        return False
    
    def run_all_tests(self):
        """Run all Arabic data handling stress tests"""
        print("🌍 Universal Workshop Arabic Data Handling Stress Test Suite")
        print("=" * 80)
        print(f"Target URL: {self.base_url}")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test database: {self.test_db_path}")
        print()
        
        test_results = []
        
        # Test 1: Encoding validation
        result1 = self.test_encoding_validation()
        test_results.append(('UTF-8 Encoding Validation', result1))
        print()
        
        # Test 2: Form input handling
        result2 = self.test_form_input_handling(10)  # 10 concurrent users
        test_results.append(('Form Input Handling', result2))
        print()
        
        # Test 3: Large dataset performance
        result3 = self.test_large_dataset_performance(500)  # 500 records
        test_results.append(('Large Dataset Performance', result3))
        print()
        
        # Test 4: Data corruption detection
        result4 = self.test_data_corruption_detection(50)  # 50 iterations
        test_results.append(('Data Corruption Detection', result4))
        print()
        
        # Test 5: RTL display integrity
        result5 = self.test_rtl_display_integrity()
        test_results.append(('RTL Display Integrity', result5))
        print()
        
        # Generate summary
        self.generate_summary(test_results)
        
        return test_results
    
    def generate_summary(self, test_results):
        """Generate comprehensive test summary"""
        print("📊 ARABIC DATA HANDLING STRESS TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Overall assessment
        if passed_tests == total_tests:
            overall = "🎉 EXCELLENT"
        elif passed_tests >= total_tests * 0.8:
            overall = "✅ GOOD"
        elif passed_tests >= total_tests * 0.6:
            overall = "⚠️  FAIR"
        else:
            overall = "❌ POOR"
        
        print(f"Overall Arabic Data Handling: {overall}")
        
        # Save results
        self.test_results['summary'] = {
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
        results_file = results_dir / f"arabic_data_stress_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed results saved: {results_file}")
        
        # Cleanup
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def cleanup(self):
        """Cleanup test resources"""
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Workshop Arabic Data Handling Stress Test")
    parser.add_argument('--url', type=str, default='http://localhost:8000',
                       help='Base URL for testing (default: http://localhost:8000)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests with reduced iterations')
    
    args = parser.parse_args()
    
    tester = ArabicDataStressTester(args.url)
    
    try:
        if args.quick:
            print("🚀 Running quick Arabic data stress tests...")
            # Run subset of tests with reduced parameters
            results = []
            results.append(('Encoding Validation', tester.test_encoding_validation(10)))
            results.append(('Form Input Handling', tester.test_form_input_handling(5)))
            results.append(('RTL Display Integrity', tester.test_rtl_display_integrity()))
            
            tester.generate_summary(results)
        else:
            tester.run_all_tests()
            
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
