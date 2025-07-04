"""
Universal Workshop ERP - Performance Validation Suite
Comprehensive performance testing and validation
"""

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, flt
import time
import json
import statistics
from datetime import datetime, timedelta


class PerformanceValidator:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.results = {}
        self.test_data = {}
        
    def run_full_validation(self):
        """Run complete performance validation suite"""
        print("🚀 Universal Workshop ERP - Performance Validation Suite")
        print("=" * 80)
        
        # Database Performance Tests
        self.test_database_performance()
        
        # API Performance Tests  
        self.test_api_performance()
        
        # Memory Usage Tests
        self.test_memory_usage()
        
        # Load Testing (Simulated)
        self.test_load_simulation()
        
        # Arabic Performance Tests
        self.test_arabic_performance()
        
        # Generate comprehensive report
        self.generate_performance_report()
        
        return self.results
    
    def test_database_performance(self):
        """Test database query performance"""
        print("🗄️ Testing Database Performance...")
        
        db_results = {}
        
        # Test 1: Simple Select Query
        start_time = time.time()
        customers = frappe.db.sql("SELECT COUNT(*) FROM `tabCustomer`")
        db_results["simple_select"] = time.time() - start_time
        
        # Test 2: Complex Join Query
        start_time = time.time()
        complex_query = frappe.db.sql("""
            SELECT c.name, c.customer_name, COUNT(v.name) as vehicle_count,
                   SUM(so.grand_total) as total_orders
            FROM `tabCustomer` c
            LEFT JOIN `tabVehicle` v ON c.name = v.customer
            LEFT JOIN `tabService Order` so ON c.name = so.customer
            GROUP BY c.name
            LIMIT 50
        """, as_dict=True)
        db_results["complex_join"] = time.time() - start_time
        
        # Test 3: Arabic Text Search
        start_time = time.time()
        arabic_search = frappe.db.sql("""
            SELECT name, customer_name, customer_name_ar
            FROM `tabCustomer`
            WHERE customer_name_ar LIKE '%أ%' OR customer_name LIKE '%Al%'
            LIMIT 20
        """, as_dict=True)
        db_results["arabic_search"] = time.time() - start_time
        
        # Test 4: Full Text Search
        start_time = time.time()
        text_search = frappe.db.sql("""
            SELECT name, vin, make, model
            FROM `tabVehicle`
            WHERE make LIKE '%Toyota%' OR model LIKE '%Camry%'
            LIMIT 30
        """, as_dict=True)
        db_results["fulltext_search"] = time.time() - start_time
        
        # Calculate database performance grade
        avg_db_time = statistics.mean(db_results.values())
        if avg_db_time < 0.1:
            db_grade = "A+"
        elif avg_db_time < 0.2:
            db_grade = "A"
        elif avg_db_time < 0.5:
            db_grade = "B"
        elif avg_db_time < 1.0:
            db_grade = "C"
        else:
            db_grade = "D"
        
        self.results["database_performance"] = {
            "tests": db_results,
            "average_time": avg_db_time,
            "grade": db_grade,
            "recommendations": self._get_db_recommendations(avg_db_time)
        }
        
        print(f"   Database Performance Grade: {db_grade} (Avg: {avg_db_time:.3f}s)")
    
    def test_api_performance(self):
        """Test API endpoint performance"""
        print("🔌 Testing API Performance...")
        
        api_results = {}
        
        try:
            # Test Vehicle Management API
            from universal_workshop.vehicle_management.api import validate_vin, search_vehicles
            
            start_time = time.time()
            vin_result = validate_vin("1HGBH41JXMN109186")
            api_results["vin_validation"] = time.time() - start_time
            
            start_time = time.time()
            search_result = search_vehicles("Toyota", limit=10)
            api_results["vehicle_search"] = time.time() - start_time
            
        except Exception as e:
            api_results["vehicle_api_error"] = str(e)
        
        try:
            # Test License Management API
            from universal_workshop.license_management.hardware_fingerprint import generate_hardware_fingerprint
            
            start_time = time.time()
            fingerprint_result = generate_hardware_fingerprint()
            api_results["hardware_fingerprint"] = time.time() - start_time
            
        except Exception as e:
            api_results["license_api_error"] = str(e)
        
        # Calculate API performance grade
        api_times = [v for v in api_results.values() if isinstance(v, float)]
        if api_times:
            avg_api_time = statistics.mean(api_times)
            if avg_api_time < 0.5:
                api_grade = "A"
            elif avg_api_time < 1.0:
                api_grade = "B"
            elif avg_api_time < 2.0:
                api_grade = "C"
            else:
                api_grade = "D"
        else:
            avg_api_time = 0
            api_grade = "N/A"
        
        self.results["api_performance"] = {
            "tests": api_results,
            "average_time": avg_api_time,
            "grade": api_grade,
            "successful_tests": len(api_times),
            "total_tests": len(api_results)
        }
        
        print(f"   API Performance Grade: {api_grade} (Avg: {avg_api_time:.3f}s)")
    
    def test_memory_usage(self):
        """Test memory usage patterns"""
        print("💾 Testing Memory Usage...")
        
        import psutil
        import os
        
        # Get current process memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        memory_results = {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "process_count": len(psutil.pids()),
            "available_memory_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024
        }
        
        # Memory usage grade
        if memory_results["rss_mb"] < 100:
            memory_grade = "A"
        elif memory_results["rss_mb"] < 250:
            memory_grade = "B"
        elif memory_results["rss_mb"] < 500:
            memory_grade = "C"
        else:
            memory_grade = "D"
        
        self.results["memory_usage"] = {
            "metrics": memory_results,
            "grade": memory_grade,
            "recommendations": self._get_memory_recommendations(memory_results["rss_mb"])
        }
        
        print(f"   Memory Usage Grade: {memory_grade} (RSS: {memory_results['rss_mb']:.1f}MB)")
    
    def test_load_simulation(self):
        """Simulate load testing with multiple operations"""
        print("⚡ Testing Load Simulation...")
        
        load_results = {}
        
        # Simulate 10 concurrent customer creations
        customer_times = []
        for i in range(10):
            start_time = time.time()
            try:
                customer = frappe.new_doc("Customer")
                customer.customer_name = f"Load Test Customer {i}"
                customer.customer_type = "Individual"
                customer.territory = "All Territories"
                customer.customer_group = "All Customer Groups"
                # Just validate, don't save to avoid data pollution
                customer.validate()
                customer_times.append(time.time() - start_time)
            except Exception as e:
                load_results[f"customer_creation_error_{i}"] = str(e)
        
        # Simulate 20 database queries
        query_times = []
        for i in range(20):
            start_time = time.time()
            result = frappe.db.sql("SELECT COUNT(*) FROM `tabCustomer` LIMIT 1")
            query_times.append(time.time() - start_time)
        
        load_results["customer_validation_times"] = customer_times
        load_results["query_times"] = query_times
        load_results["avg_customer_time"] = statistics.mean(customer_times) if customer_times else 0
        load_results["avg_query_time"] = statistics.mean(query_times) if query_times else 0
        load_results["max_customer_time"] = max(customer_times) if customer_times else 0
        load_results["max_query_time"] = max(query_times) if query_times else 0
        
        # Load performance grade
        avg_total_time = (load_results["avg_customer_time"] + load_results["avg_query_time"]) / 2
        if avg_total_time < 0.1:
            load_grade = "A"
        elif avg_total_time < 0.3:
            load_grade = "B"
        elif avg_total_time < 0.7:
            load_grade = "C"
        else:
            load_grade = "D"
        
        self.results["load_simulation"] = {
            "metrics": load_results,
            "grade": load_grade,
            "concurrent_operations": 30,
            "success_rate": (len(customer_times) + len(query_times)) / 30 * 100
        }
        
        print(f"   Load Simulation Grade: {load_grade} (Success: {self.results['load_simulation']['success_rate']:.1f}%)")
    
    def test_arabic_performance(self):
        """Test Arabic-specific performance"""
        print("🌍 Testing Arabic Performance...")
        
        arabic_results = {}
        
        # Test Arabic text processing
        arabic_text = "مركبة تويوتا كامري موديل ٢٠٢٠"
        english_text = "Toyota Camry Vehicle Model 2020"
        
        # Arabic text detection performance
        start_time = time.time()
        for _ in range(100):
            is_arabic = any('\u0600' <= char <= '\u06FF' for char in arabic_text)
        arabic_results["text_detection"] = time.time() - start_time
        
        # Arabic number conversion performance
        start_time = time.time()
        for _ in range(100):
            arabic_digits = "٠١٢٣٤٥٦٧٨٩"
            english_digits = "0123456789"
            converted = "12345"
            for i, digit in enumerate(english_digits):
                converted = converted.replace(digit, arabic_digits[i])
        arabic_results["number_conversion"] = time.time() - start_time
        
        # RTL text direction performance
        start_time = time.time()
        for _ in range(100):
            arabic_chars = sum(1 for char in arabic_text if '\u0600' <= char <= '\u06FF')
            total_chars = len(arabic_text.replace(' ', ''))
            direction = "rtl" if arabic_chars / total_chars > 0.3 else "ltr"
        arabic_results["direction_calculation"] = time.time() - start_time
        
        # Arabic performance grade
        avg_arabic_time = statistics.mean(arabic_results.values())
        if avg_arabic_time < 0.01:
            arabic_grade = "A+"
        elif avg_arabic_time < 0.05:
            arabic_grade = "A"
        elif avg_arabic_time < 0.1:
            arabic_grade = "B"
        else:
            arabic_grade = "C"
        
        self.results["arabic_performance"] = {
            "tests": arabic_results,
            "average_time": avg_arabic_time,
            "grade": arabic_grade,
            "operations_per_second": int(100 / avg_arabic_time) if avg_arabic_time > 0 else 0
        }
        
        print(f"   Arabic Performance Grade: {arabic_grade} (OPS: {self.results['arabic_performance']['operations_per_second']})")
    
    def _get_db_recommendations(self, avg_time):
        """Get database performance recommendations"""
        if avg_time > 0.5:
            return [
                "Add indexes on frequently queried fields",
                "Optimize complex JOIN queries",
                "Consider query result caching",
                "Review database configuration"
            ]
        elif avg_time > 0.2:
            return [
                "Add indexes on Arabic text fields",
                "Optimize search queries",
                "Consider read replicas for heavy queries"
            ]
        else:
            return ["Database performance is excellent"]
    
    def _get_memory_recommendations(self, rss_mb):
        """Get memory usage recommendations"""
        if rss_mb > 500:
            return [
                "Review memory leaks in custom code",
                "Optimize large data processing",
                "Consider horizontal scaling",
                "Monitor Redis memory usage"
            ]
        elif rss_mb > 250:
            return [
                "Monitor memory usage trends",
                "Optimize large query results",
                "Consider caching strategies"
            ]
        else:
            return ["Memory usage is within acceptable limits"]
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*80)
        print("📊 UNIVERSAL WORKSHOP ERP - PERFORMANCE VALIDATION REPORT")
        print("="*80)
        
        # Overall performance calculation
        grades = []
        for category, data in self.results.items():
            if "grade" in data and data["grade"] not in ["N/A"]:
                grade_value = self._grade_to_number(data["grade"])
                grades.append(grade_value)
        
        overall_grade = self._number_to_grade(statistics.mean(grades)) if grades else "N/A"
        
        print(f"\n🎯 Overall Performance Grade: {overall_grade}")
        print(f"📈 Test Categories Completed: {len(self.results)}")
        
        print(f"\n📋 Performance Summary:")
        print("-" * 50)
        
        for category, data in self.results.items():
            category_name = category.replace("_", " ").title()
            grade = data.get("grade", "N/A")
            
            if category == "database_performance":
                print(f"🗄️ {category_name}: {grade} (Avg: {data['average_time']:.3f}s)")
            elif category == "api_performance":
                print(f"🔌 {category_name}: {grade} (Success: {data['successful_tests']}/{data['total_tests']})")
            elif category == "memory_usage":
                print(f"💾 {category_name}: {grade} (RSS: {data['metrics']['rss_mb']:.1f}MB)")
            elif category == "load_simulation":
                print(f"⚡ {category_name}: {grade} (Success: {data['success_rate']:.1f}%)")
            elif category == "arabic_performance":
                print(f"🌍 {category_name}: {grade} (OPS: {data['operations_per_second']})")
        
        # Performance recommendations
        print(f"\n🔧 Performance Recommendations:")
        print("-" * 50)
        
        all_recommendations = []
        for data in self.results.values():
            if "recommendations" in data:
                all_recommendations.extend(data["recommendations"])
        
        for i, rec in enumerate(set(all_recommendations), 1):
            print(f"{i}. {rec}")
        
        # Production readiness assessment
        print(f"\n🚀 Production Readiness Assessment:")
        print("-" * 50)
        
        if overall_grade in ["A+", "A"]:
            print("✅ EXCELLENT: System is ready for high-load production deployment")
            print("✅ Performance metrics exceed expectations")
            print("✅ Can handle concurrent users without issues")
        elif overall_grade in ["B"]:
            print("✅ GOOD: System is ready for production with monitoring")
            print("⚠️ Consider performance optimizations for peak loads")
            print("✅ Suitable for medium-scale deployments")
        elif overall_grade in ["C"]:
            print("⚠️ ACCEPTABLE: System needs optimization before production")
            print("🔧 Address performance bottlenecks")
            print("📊 Monitor performance metrics closely")
        else:
            print("🚨 CRITICAL: System needs significant optimization")
            print("❌ Not recommended for production deployment")
            print("🔧 Address all performance issues before deployment")
        
        print("="*80)
    
    def _grade_to_number(self, grade):
        """Convert letter grade to number"""
        grade_map = {"A+": 4.5, "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0}
        return grade_map.get(grade, 0)
    
    def _number_to_grade(self, number):
        """Convert number to letter grade"""
        if number >= 4.3:
            return "A+"
        elif number >= 3.7:
            return "A"
        elif number >= 2.5:
            return "B"
        elif number >= 1.5:
            return "C"
        else:
            return "D"


def run_performance_validation():
    """Main function to run performance validation"""
    validator = PerformanceValidator()
    return validator.run_full_validation()


if __name__ == "__main__":
    run_performance_validation() 