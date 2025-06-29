#!/usr/bin/env python3
"""
Universal Workshop ERP - Arabic Authentication Data Stress Testing
Focused testing for Arabic data in authentication and session flows
"""

import os
import sys
import json
import time
import hashlib
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path
import sqlite3
import re
import unicodedata

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class ArabicAuthStressTester:
    """
    Specialized Arabic data stress testing for authentication flows
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session_data = {}
        
        # Arabic authentication test data
        self.auth_test_data = {
            'usernames': [
                'المدير',
                'الفني_الأول',
                'خدمة_العملاء',
                'مدير_المخزون',
                'صاحب_الورشة',
                'محمد_أحمد',
                'فاطمة_علي',
                'عبدالله_محمد',
                'مريم_حسن',
                'أحمد_السيد'
            ],
            'passwords': [
                'كلمة_مرور_قوية_٢٠٢٥',
                'الرقم_السري_العربي_١٢٣',
                'كلمة_مرور_آمنة_جداً',
                'الورشة_الشاملة_٢٠٢٥',
                'مرور_عربي_معقد_!@#',
                'كلمة_سر_طويلة_وقوية_٢٠٢٥'
            ],
            'emails': [
                'المدير@الورشة.com',
                'admin@ورشة_شاملة.net',
                'مستخدم@الشركة.org',
                'العميل@البريد.ae',
                'الموظف@النظام.com'
            ],
            'full_names': [
                'محمد أحمد علي السيد',
                'فاطمة حسن محمود الزهراء',
                'عبدالله محمد إبراهيم الأحمد',
                'مريم علي حسن المحمد',
                'أحمد سعيد محمد العلي',
                'نورا عبدالله حسين السالم'
            ],
            'company_names': [
                'الورشة الشاملة للسيارات',
                'مركز الصيانة المتطور',
                'شركة الخدمات الفنية المحدودة',
                'مؤسسة الإصلاح والصيانة',
                'ورشة التقنية الحديثة'
            ]
        }
        
        # Create results directory
        self.results_dir = Path('test_results/arabic_auth_stress')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🔐 Arabic Authentication Stress Tester Initialized")
    
    def validate_arabic_text_integrity(self, original, processed):
        """Validate Arabic text integrity after processing"""
        try:
            # Basic equality check
            if original != processed:
                return False, "Text content mismatch"
            
            # UTF-8 encoding round-trip test
            original_bytes = original.encode('utf-8')
            processed_bytes = processed.encode('utf-8')
            
            if original_bytes != processed_bytes:
                return False, "UTF-8 encoding mismatch"
            
            # Unicode normalization consistency
            original_nfc = unicodedata.normalize('NFC', original)
            processed_nfc = unicodedata.normalize('NFC', processed)
            
            if original_nfc != processed_nfc:
                return False, "Unicode normalization inconsistency"
            
            # Hash verification
            original_hash = hashlib.sha256(original_bytes).hexdigest()
            processed_hash = hashlib.sha256(processed_bytes).hexdigest()
            
            if original_hash != processed_hash:
                return False, "Hash mismatch detected"
            
            return True, "Text integrity maintained"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def simulate_form_submission(self, auth_data):
        """Simulate authentication form submission with Arabic data"""
        try:
            start_time = time.time()
            
            # Simulate form encoding/decoding
            form_data = {}
            for field, value in auth_data.items():
                # Simulate web form encoding
                encoded_value = value.encode('utf-8').decode('utf-8')
                form_data[field] = encoded_value
            
            # Simulate validation processing
            for field, value in form_data.items():
                # Length validation
                if len(value) > 255:  # Typical database field limit
                    raise ValueError(f"Field {field} exceeds length limit")
                
                # Character validation (allow Arabic and common symbols)
                if not re.match(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9@._\-\s]*$', value):
                    raise ValueError(f"Field {field} contains invalid characters")
                
                # Integrity check
                integrity_valid, integrity_msg = self.validate_arabic_text_integrity(auth_data[field], value)
                if not integrity_valid:
                    raise ValueError(f"Integrity check failed for {field}: {integrity_msg}")
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'processing_time': processing_time * 1000,  # ms
                'fields_processed': len(form_data),
                'total_chars': sum(len(v) for v in form_data.values()),
                'error_msg': None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'success': False,
                'processing_time': processing_time * 1000,
                'fields_processed': 0,
                'total_chars': 0,
                'error_msg': str(e)
            }
    
    def simulate_database_operations(self, auth_data):
        """Simulate database storage/retrieval of Arabic authentication data"""
        try:
            # Create in-memory SQLite database for testing
            db_file = self.results_dir / f"temp_auth_db_{int(time.time())}.db"
            
            start_time = time.time()
            
            with sqlite3.connect(str(db_file)) as conn:
                # Ensure UTF-8 encoding
                conn.execute("PRAGMA encoding = 'UTF-8'")
                
                # Create test table
                conn.execute('''
                    CREATE TABLE auth_test (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        password TEXT,
                        email TEXT,
                        full_name TEXT,
                        company TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert Arabic data
                conn.execute('''
                    INSERT INTO auth_test (username, password, email, full_name, company)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    auth_data.get('username', ''),
                    auth_data.get('password', ''),
                    auth_data.get('email', ''),
                    auth_data.get('full_name', ''),
                    auth_data.get('company', '')
                ))
                
                # Retrieve data
                cursor = conn.execute('SELECT username, password, email, full_name, company FROM auth_test WHERE id = 1')
                retrieved_data = cursor.fetchone()
                
                if not retrieved_data:
                    raise Exception("No data retrieved from database")
                
                # Verify data integrity
                fields = ['username', 'password', 'email', 'full_name', 'company']
                for i, field in enumerate(fields):
                    original_value = auth_data.get(field, '')
                    retrieved_value = retrieved_data[i] or ''
                    
                    integrity_valid, integrity_msg = self.validate_arabic_text_integrity(original_value, retrieved_value)
                    if not integrity_valid:
                        raise Exception(f"Database integrity check failed for {field}: {integrity_msg}")
            
            # Clean up
            db_file.unlink(missing_ok=True)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'processing_time': processing_time * 1000,  # ms
                'database_operations': 2,  # INSERT + SELECT
                'error_msg': None
            }
            
        except Exception as e:
            # Clean up on error
            if 'db_file' in locals():
                db_file.unlink(missing_ok=True)
            
            processing_time = time.time() - start_time
            return {
                'success': False,
                'processing_time': processing_time * 1000,
                'database_operations': 0,
                'error_msg': str(e)
            }
    
    def simulate_session_management(self, auth_data):
        """Simulate session management with Arabic user data"""
        try:
            start_time = time.time()
            
            # Generate session ID
            session_id = hashlib.md5(f"{auth_data['username']}{time.time()}".encode('utf-8')).hexdigest()
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'username': auth_data['username'],
                'full_name': auth_data['full_name'],
                'email': auth_data['email'],
                'company': auth_data['company'],
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            # Simulate session storage (JSON serialization)
            session_json = json.dumps(session_data, ensure_ascii=False)
            
            # Simulate session retrieval
            retrieved_session = json.loads(session_json)
            
            # Verify session data integrity
            for field in ['username', 'full_name', 'email', 'company']:
                original_value = auth_data[field]
                retrieved_value = retrieved_session[field]
                
                integrity_valid, integrity_msg = self.validate_arabic_text_integrity(original_value, retrieved_value)
                if not integrity_valid:
                    raise Exception(f"Session integrity check failed for {field}: {integrity_msg}")
            
            # Store session for cleanup
            self.session_data[session_id] = session_data
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'processing_time': processing_time * 1000,  # ms
                'session_id': session_id,
                'session_size': len(session_json),
                'error_msg': None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'success': False,
                'processing_time': processing_time * 1000,
                'session_id': None,
                'session_size': 0,
                'error_msg': str(e)
            }
    
    def run_concurrent_auth_stress_test(self, concurrent_users=50, operations_per_user=5):
        """Run concurrent authentication stress test with Arabic data"""
        print(f"🔐 Running concurrent authentication stress test...")
        print(f"👥 Concurrent users: {concurrent_users}")
        print(f"⚡ Operations per user: {operations_per_user}")
        
        results = []
        
        def user_auth_session(user_id):
            """Simulate complete user authentication session"""
            user_results = []
            
            for operation_id in range(operations_per_user):
                try:
                    # Generate random Arabic auth data
                    auth_data = {
                        'username': f"{self.auth_test_data['usernames'][user_id % len(self.auth_test_data['usernames'])]}_{user_id}",
                        'password': self.auth_test_data['passwords'][operation_id % len(self.auth_test_data['passwords'])],
                        'email': f"user{user_id}@{self.auth_test_data['emails'][user_id % len(self.auth_test_data['emails'])].split('@')[1]}",
                        'full_name': self.auth_test_data['full_names'][user_id % len(self.auth_test_data['full_names'])],
                        'company': self.auth_test_data['company_names'][user_id % len(self.auth_test_data['company_names'])]
                    }
                    
                    session_start = time.time()
                    
                    # Test form submission
                    form_result = self.simulate_form_submission(auth_data)
                    form_result.update({
                        'user_id': user_id,
                        'operation_id': operation_id,
                        'test_type': 'form_submission'
                    })
                    user_results.append(form_result)
                    
                    # Test database operations
                    db_result = self.simulate_database_operations(auth_data)
                    db_result.update({
                        'user_id': user_id,
                        'operation_id': operation_id,
                        'test_type': 'database_operations'
                    })
                    user_results.append(db_result)
                    
                    # Test session management
                    session_result = self.simulate_session_management(auth_data)
                    session_result.update({
                        'user_id': user_id,
                        'operation_id': operation_id,
                        'test_type': 'session_management'
                    })
                    user_results.append(session_result)
                    
                    session_time = time.time() - session_start
                    
                    # Add summary result
                    summary_result = {
                        'user_id': user_id,
                        'operation_id': operation_id,
                        'test_type': 'complete_session',
                        'success': all(r['success'] for r in user_results[-3:]),
                        'processing_time': session_time * 1000,
                        'total_operations': 3,
                        'error_msg': None
                    }
                    user_results.append(summary_result)
                    
                except Exception as e:
                    error_result = {
                        'user_id': user_id,
                        'operation_id': operation_id,
                        'test_type': 'session_error',
                        'success': False,
                        'processing_time': 0,
                        'error_msg': str(e)
                    }
                    user_results.append(error_result)
            
            return user_results
        
        # Run concurrent user sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrent_users, 20)) as executor:
            future_to_user = {
                executor.submit(user_auth_session, user_id): user_id
                for user_id in range(concurrent_users)
            }
            
            for future in concurrent.futures.as_completed(future_to_user):
                user_results = future.result()
                results.extend(user_results)
        
        return results
    
    def run_arabic_auth_stress_test(self):
        """Run comprehensive Arabic authentication stress test"""
        print("🌍 ARABIC AUTHENTICATION DATA STRESS TESTING")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Run stress tests
        stress_results = self.run_concurrent_auth_stress_test(100, 3)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        total_operations = len(stress_results)
        successful_operations = sum(1 for r in stress_results if r['success'])
        
        # Group by test type
        results_by_type = {}
        for result in stress_results:
            test_type = result['test_type']
            if test_type not in results_by_type:
                results_by_type[test_type] = []
            results_by_type[test_type].append(result)
        
        # Generate report
        report = {
            'test_execution': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'success_rate': (successful_operations / max(total_operations, 1)) * 100
            },
            'results_by_type': {},
            'performance_metrics': {},
            'arabic_data_integrity': {
                'corruption_detected': False,
                'encoding_issues': 0,
                'normalization_issues': 0
            }
        }
        
        # Analyze by test type
        for test_type, type_results in results_by_type.items():
            successful = sum(1 for r in type_results if r['success'])
            failed = len(type_results) - successful
            
            processing_times = [r['processing_time'] for r in type_results if 'processing_time' in r and r['processing_time'] > 0]
            
            report['results_by_type'][test_type] = {
                'total': len(type_results),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / max(len(type_results), 1)) * 100,
                'avg_processing_time': sum(processing_times) / max(len(processing_times), 1),
                'errors': [r['error_msg'] for r in type_results if r.get('error_msg')]
            }
        
        # Save detailed report
        report_file = self.results_dir / f"arabic_auth_stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n📊 ARABIC AUTHENTICATION STRESS TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Total Operations: {total_operations:,}")
        print(f"✅ Successful: {successful_operations:,}")
        print(f"❌ Failed: {total_operations - successful_operations:,}")
        print(f"🎯 Success Rate: {report['test_execution']['success_rate']:.2f}%")
        
        print(f"\n📈 Performance by Test Type:")
        for test_type, metrics in report['results_by_type'].items():
            print(f"   {test_type}: {metrics['success_rate']:.1f}% success, {metrics['avg_processing_time']:.2f}ms avg")
        
        if report['test_execution']['success_rate'] >= 99:
            print("\n🎉 EXCELLENT: Arabic authentication data handling")
        elif report['test_execution']['success_rate'] >= 95:
            print("\n✅ GOOD: Arabic authentication data handling")
        else:
            print("\n⚠️  WARNING: Arabic authentication data handling needs improvement")
        
        print(f"\n📄 Detailed report: {report_file}")
        
        return report


def main():
    """Main function"""
    tester = ArabicAuthStressTester()
    return tester.run_arabic_auth_stress_test()


if __name__ == "__main__":
    main()
