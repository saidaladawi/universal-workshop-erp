# Week 16: Load Testing Framework & Production Deployment
# Universal Workshop ERP - Comprehensive Load Testing System

import time
import threading
import queue
import random
import json
import requests
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import frappe
from frappe import _
from frappe.utils import now, add_days, flt, cint
import redis
import psutil


class LoadTestingFramework:
    """
    Comprehensive load testing framework for Universal Workshop ERP
    Supports 1000+ concurrent users with Arabic data scenarios
    """

    def __init__(self):
        self.base_url = frappe.utils.get_url()
        self.redis_client = self._get_redis_client()
        self.test_results = []
        self.active_threads = 0
        self.max_threads = 1000
        self.test_scenarios = {}
        self.arabic_test_data = self._load_arabic_test_data()
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float("inf"),
            "errors": [],
            "throughput": 0,
            "concurrent_users": 0,
        }

    def _get_redis_client(self):
        """Get Redis client for caching test results"""
        try:
            return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        except Exception as e:
            frappe.log_error(f"Redis connection failed: {e}")
            return None

    def _load_arabic_test_data(self) -> Dict:
        """Load Arabic test data for realistic testing scenarios"""
        return {
            "workshop_names": [
                "ورشة الخليج للسيارات",
                "مركز النجاح للصيانة",
                "ورشة الأمان للإطارات",
                "مركز التقنية المتقدمة",
                "ورشة البركة للسيارات",
            ],
            "customer_names": [
                "أحمد بن محمد الراشد",
                "سالم بن عبدالله المعمري",
                "فاطمة بنت سعيد البلوشي",
                "محمد بن حمود الشعيلي",
                "نورا بنت خالد الحارثي",
            ],
            "vehicle_makes": ["تويوتا", "نيسان", "هوندا", "مازدا", "ميتسوبيشي"],
            "services": [
                "تغيير الزيت والفلتر",
                "فحص الفرامل",
                "تبديل الإطارات",
                "صيانة المحرك",
                "فحص كهرباء السيارة",
            ],
        }

    def create_load_test_scenario(self, scenario_name: str, config: Dict) -> None:
        """Create a custom load test scenario"""
        self.test_scenarios[scenario_name] = {
            "concurrent_users": config.get("concurrent_users", 100),
            "duration_minutes": config.get("duration_minutes", 10),
            "ramp_up_time": config.get("ramp_up_time", 60),
            "endpoints": config.get("endpoints", []),
            "arabic_percentage": config.get("arabic_percentage", 50),
            "think_time": config.get("think_time", 2),
            "description": config.get("description", ""),
            "target_metrics": {
                "max_response_time": config.get("max_response_time", 5000),
                "error_rate_threshold": config.get("error_rate_threshold", 5),
                "min_throughput": config.get("min_throughput", 100),
            },
        }

    def get_system_resources(self) -> Dict:
        """Monitor system resources during load testing"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_percent": psutil.disk_usage("/").percent,
            "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
            "network_io": psutil.net_io_counters()._asdict(),
            "active_connections": len(psutil.net_connections()),
            "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
        }

    def simulate_user_session(self, user_id: int, scenario_config: Dict) -> Dict:
        """Simulate a single user session with realistic behavior"""
        session_start = time.time()
        session_results = {
            "user_id": user_id,
            "requests": [],
            "total_time": 0,
            "errors": [],
            "arabic_requests": 0,
            "english_requests": 0,
        }

        try:
            # Create session with authentication
            session = requests.Session()
            self._authenticate_session(session)

            # Execute test requests for specified duration
            end_time = session_start + (scenario_config["duration_minutes"] * 60)

            while time.time() < end_time:
                # Randomly select endpoint to test
                if scenario_config["endpoints"]:
                    endpoint = random.choice(scenario_config["endpoints"])

                    # Determine if Arabic or English data
                    use_arabic = random.randint(1, 100) <= scenario_config["arabic_percentage"]

                    # Execute request
                    request_result = self._execute_request(session, endpoint, use_arabic)
                    session_results["requests"].append(request_result)

                    if use_arabic:
                        session_results["arabic_requests"] += 1
                    else:
                        session_results["english_requests"] += 1

                # Simulate think time
                time.sleep(scenario_config["think_time"])

            session_results["total_time"] = time.time() - session_start

        except Exception as e:
            session_results["errors"].append(str(e))
            frappe.log_error(f"User session {user_id} failed: {e}")

        return session_results

    def _authenticate_session(self, session: requests.Session) -> bool:
        """Authenticate session for API testing"""
        try:
            # Get API key/secret for testing
            api_key = frappe.db.get_value("User", "Administrator", "api_key")
            api_secret = frappe.db.get_value("User", "Administrator", "api_secret")

            if api_key and api_secret:
                session.headers.update(
                    {
                        "Authorization": f"token {api_key}:{api_secret}",
                        "Content-Type": "application/json",
                    }
                )
                return True

            # Fallback: Use session-based authentication
            login_url = f"{self.base_url}/api/method/login"
            login_data = {"usr": "Administrator", "pwd": frappe.conf.get("admin_password", "admin")}

            response = session.post(login_url, data=login_data)
            return response.status_code == 200

        except Exception as e:
            frappe.log_error(f"Authentication failed: {e}")
            return False

    def _execute_request(
        self, session: requests.Session, endpoint_config: Dict, use_arabic: bool
    ) -> Dict:
        """Execute a single API request with timing and error tracking"""
        request_start = time.time()

        try:
            # Prepare request data
            url = f"{self.base_url}{endpoint_config['path']}"
            method = endpoint_config.get("method", "GET")

            # Generate test data
            if use_arabic:
                data = self._generate_arabic_test_data(endpoint_config["type"])
            else:
                data = self._generate_english_test_data(endpoint_config["type"])

            # Execute request
            if method == "GET":
                response = session.get(url, params=data, timeout=30)
            elif method == "POST":
                response = session.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = session.put(url, json=data, timeout=30)
            else:
                response = session.delete(url, timeout=30)

            response_time = (time.time() - request_start) * 1000  # milliseconds

            return {
                "endpoint": endpoint_config["path"],
                "method": method,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code < 400,
                "use_arabic": use_arabic,
                "timestamp": datetime.now().isoformat(),
                "response_size": len(response.content) if response.content else 0,
            }

        except Exception as e:
            response_time = (time.time() - request_start) * 1000

            return {
                "endpoint": endpoint_config["path"],
                "method": endpoint_config.get("method", "GET"),
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
                "use_arabic": use_arabic,
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_arabic_test_data(self, data_type: str) -> Dict:
        """Generate Arabic test data for different endpoint types"""
        if data_type == "workshop_profile":
            return {
                "workshop_name": random.choice(self.arabic_test_data["workshop_names"]),
                "workshop_name_ar": random.choice(self.arabic_test_data["workshop_names"]),
                "owner_name": random.choice(self.arabic_test_data["customer_names"]),
                "phone": f"+968 9{random.randint(1000000, 9999999)}",
                "governorate": random.choice(["مسقط", "صلالة", "نزوى", "صور", "صحار"]),
            }
        elif data_type == "customer":
            return {
                "customer_name": random.choice(self.arabic_test_data["customer_names"]),
                "customer_name_ar": random.choice(self.arabic_test_data["customer_names"]),
                "phone": f"+968 9{random.randint(1000000, 9999999)}",
                "email": f"test{random.randint(1000, 9999)}@example.com",
            }
        elif data_type == "service_order":
            return {
                "customer": random.choice(self.arabic_test_data["customer_names"]),
                "service_type": random.choice(self.arabic_test_data["services"]),
                "vehicle_make": random.choice(self.arabic_test_data["vehicle_makes"]),
                "description": f"وصف الخدمة {random.randint(1, 1000)}",
            }
        else:
            return {"test_field": f"بيانات اختبار {random.randint(1, 1000)}"}

    def _generate_english_test_data(self, data_type: str) -> Dict:
        """Generate English test data for different endpoint types"""
        if data_type == "workshop_profile":
            return {
                "workshop_name": f"Test Workshop {random.randint(1, 1000)}",
                "owner_name": f"Test Owner {random.randint(1, 1000)}",
                "phone": f"+968 9{random.randint(1000000, 9999999)}",
                "governorate": random.choice(["Muscat", "Salalah", "Nizwa", "Sur", "Sohar"]),
            }
        elif data_type == "customer":
            return {
                "customer_name": f"Test Customer {random.randint(1, 1000)}",
                "phone": f"+968 9{random.randint(1000000, 9999999)}",
                "email": f"test{random.randint(1000, 9999)}@example.com",
            }
        elif data_type == "service_order":
            return {
                "customer": f"Test Customer {random.randint(1, 1000)}",
                "service_type": random.choice(["Oil Change", "Brake Check", "Tire Service"]),
                "vehicle_make": random.choice(["Toyota", "Nissan", "Honda"]),
                "description": f"Service description {random.randint(1, 1000)}",
            }
        else:
            return {"test_field": f"Test data {random.randint(1, 1000)}"}

    def execute_load_test(self, scenario_name: str) -> Dict:
        """Execute a complete load test scenario"""
        if scenario_name not in self.test_scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        scenario = self.test_scenarios[scenario_name]
        test_start = time.time()

        print(f"\n🚀 Starting Load Test: {scenario_name}")
        print(f"   Concurrent Users: {scenario['concurrent_users']}")
        print(f"   Duration: {scenario['duration_minutes']} minutes")
        print(f"   Arabic Data: {scenario['arabic_percentage']}%")

        # Reset metrics
        self._reset_metrics()

        # Monitor system resources
        resource_monitor = threading.Thread(
            target=self._monitor_resources, args=(scenario["duration_minutes"],)
        )
        resource_monitor.start()

        # Execute concurrent user sessions
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=scenario["concurrent_users"]
        ) as executor:
            # Ramp up users gradually
            ramp_up_delay = scenario["ramp_up_time"] / scenario["concurrent_users"]

            futures = []
            for user_id in range(scenario["concurrent_users"]):
                future = executor.submit(self.simulate_user_session, user_id, scenario)
                futures.append(future)

                # Gradual ramp-up
                time.sleep(ramp_up_delay)

            # Collect results
            session_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    session_results.append(result)
                    self._update_metrics(result)
                except Exception as e:
                    frappe.log_error(f"Session execution failed: {e}")

        # Wait for resource monitor to finish
        resource_monitor.join()

        # Calculate final metrics
        test_duration = time.time() - test_start
        self._finalize_metrics(test_duration)

        # Generate comprehensive report
        test_report = self._generate_test_report(
            scenario_name, scenario, session_results, test_duration
        )

        # Store results in Redis for dashboard
        if self.redis_client:
            self.redis_client.setex(
                f"load_test:{scenario_name}:{int(test_start)}", 3600, json.dumps(test_report)
            )

        # Store in database
        self._store_test_results(test_report)

        return test_report

    def _reset_metrics(self):
        """Reset performance metrics for new test"""
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float("inf"),
            "errors": [],
            "throughput": 0,
            "concurrent_users": 0,
            "system_resources": [],
        }

    def _update_metrics(self, session_result: Dict):
        """Update performance metrics with session results"""
        for request in session_result["requests"]:
            self.performance_metrics["total_requests"] += 1

            if request["success"]:
                self.performance_metrics["successful_requests"] += 1
            else:
                self.performance_metrics["failed_requests"] += 1
                self.performance_metrics["errors"].append(request.get("error", "Unknown error"))

            # Update response time metrics
            response_time = request["response_time"]
            self.performance_metrics["max_response_time"] = max(
                self.performance_metrics["max_response_time"], response_time
            )
            self.performance_metrics["min_response_time"] = min(
                self.performance_metrics["min_response_time"], response_time
            )

    def _monitor_resources(self, duration_minutes: int):
        """Monitor system resources during test execution"""
        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            resources = self.get_system_resources()
            resources["timestamp"] = datetime.now().isoformat()
            self.performance_metrics["system_resources"].append(resources)
            time.sleep(10)  # Monitor every 10 seconds

    def _finalize_metrics(self, test_duration: float):
        """Calculate final performance metrics"""
        if self.performance_metrics["total_requests"] > 0:
            # Calculate average response time
            total_response_time = 0
            for metric in self.performance_metrics.get("response_times", []):
                total_response_time += metric

            if self.performance_metrics["total_requests"] > 0:
                self.performance_metrics["avg_response_time"] = (
                    total_response_time / self.performance_metrics["total_requests"]
                )

            # Calculate throughput (requests per second)
            self.performance_metrics["throughput"] = (
                self.performance_metrics["total_requests"] / test_duration
            )

            # Calculate error rate
            self.performance_metrics["error_rate"] = (
                self.performance_metrics["failed_requests"]
                / self.performance_metrics["total_requests"]
            ) * 100

    def _generate_test_report(
        self, scenario_name: str, scenario: Dict, session_results: List, test_duration: float
    ) -> Dict:
        """Generate comprehensive test report"""

        # Calculate pass/fail status
        target_metrics = scenario["target_metrics"]
        passed_tests = []
        failed_tests = []

        # Check response time
        if self.performance_metrics["max_response_time"] <= target_metrics["max_response_time"]:
            passed_tests.append("Response Time")
        else:
            failed_tests.append("Response Time")

        # Check error rate
        error_rate = (
            self.performance_metrics["failed_requests"]
            / max(self.performance_metrics["total_requests"], 1)
        ) * 100

        if error_rate <= target_metrics["error_rate_threshold"]:
            passed_tests.append("Error Rate")
        else:
            failed_tests.append("Error Rate")

        # Check throughput
        if self.performance_metrics["throughput"] >= target_metrics["min_throughput"]:
            passed_tests.append("Throughput")
        else:
            failed_tests.append("Throughput")

        # Overall grade
        pass_percentage = len(passed_tests) / (len(passed_tests) + len(failed_tests)) * 100
        if pass_percentage >= 90:
            grade = "A"
        elif pass_percentage >= 80:
            grade = "B"
        elif pass_percentage >= 70:
            grade = "C"
        elif pass_percentage >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "scenario_name": scenario_name,
            "test_timestamp": datetime.now().isoformat(),
            "duration_seconds": test_duration,
            "configuration": scenario,
            "performance_metrics": self.performance_metrics,
            "session_count": len(session_results),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "overall_grade": grade,
            "pass_percentage": pass_percentage,
            "recommendations": self._generate_recommendations(failed_tests),
            "arabic_usage_stats": self._calculate_arabic_usage(session_results),
            "system_health": self._assess_system_health(),
        }

    def _generate_recommendations(self, failed_tests: List) -> List:
        """Generate optimization recommendations based on failed tests"""
        recommendations = []

        if "Response Time" in failed_tests:
            recommendations.extend(
                [
                    "Optimize database queries and add proper indexing",
                    "Implement Redis caching for frequently accessed data",
                    "Consider upgrading server hardware (CPU/RAM)",
                    "Optimize Arabic text processing and RTL rendering",
                ]
            )

        if "Error Rate" in failed_tests:
            recommendations.extend(
                [
                    "Review error logs for common failure patterns",
                    "Implement better error handling and retry mechanisms",
                    "Check network connectivity and timeouts",
                    "Validate Arabic text encoding and processing",
                ]
            )

        if "Throughput" in failed_tests:
            recommendations.extend(
                [
                    "Scale horizontal with load balancers",
                    "Optimize database connection pooling",
                    "Implement async processing for heavy operations",
                    "Consider CDN for static assets",
                ]
            )

        return recommendations

    def _calculate_arabic_usage(self, session_results: List) -> Dict:
        """Calculate Arabic vs English usage statistics"""
        total_requests = sum(len(session["requests"]) for session in session_results)
        arabic_requests = sum(session["arabic_requests"] for session in session_results)
        english_requests = sum(session["english_requests"] for session in session_results)

        return {
            "total_requests": total_requests,
            "arabic_requests": arabic_requests,
            "english_requests": english_requests,
            "arabic_percentage": (arabic_requests / max(total_requests, 1)) * 100,
            "english_percentage": (english_requests / max(total_requests, 1)) * 100,
        }

    def _assess_system_health(self) -> Dict:
        """Assess overall system health during the test"""
        resources = self.performance_metrics.get("system_resources", [])
        if not resources:
            return {"status": "unknown", "details": "No resource data available"}

        # Calculate averages
        avg_cpu = sum(r["cpu_percent"] for r in resources) / len(resources)
        avg_memory = sum(r["memory_percent"] for r in resources) / len(resources)
        avg_disk = sum(r["disk_percent"] for r in resources) / len(resources)

        # Assess health
        health_score = 100
        warnings = []

        if avg_cpu > 80:
            health_score -= 20
            warnings.append("High CPU usage detected")

        if avg_memory > 85:
            health_score -= 25
            warnings.append("High memory usage detected")

        if avg_disk > 90:
            health_score -= 15
            warnings.append("Low disk space detected")

        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "fair"
        else:
            status = "poor"

        return {
            "status": status,
            "health_score": health_score,
            "avg_cpu_percent": avg_cpu,
            "avg_memory_percent": avg_memory,
            "avg_disk_percent": avg_disk,
            "warnings": warnings,
        }

    def _store_test_results(self, test_report: Dict):
        """Store test results in database for historical analysis"""
        try:
            # Store in a custom DocType for load test results
            doc = frappe.new_doc("Load Test Result")
            doc.scenario_name = test_report["scenario_name"]
            doc.test_timestamp = test_report["test_timestamp"]
            doc.duration_seconds = test_report["duration_seconds"]
            doc.total_requests = test_report["performance_metrics"]["total_requests"]
            doc.successful_requests = test_report["performance_metrics"]["successful_requests"]
            doc.failed_requests = test_report["performance_metrics"]["failed_requests"]
            doc.avg_response_time = test_report["performance_metrics"]["avg_response_time"]
            doc.max_response_time = test_report["performance_metrics"]["max_response_time"]
            doc.throughput = test_report["performance_metrics"]["throughput"]
            doc.error_rate = test_report["performance_metrics"].get("error_rate", 0)
            doc.overall_grade = test_report["overall_grade"]
            doc.pass_percentage = test_report["pass_percentage"]
            doc.test_report_json = json.dumps(test_report)
            doc.insert()
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"Failed to store load test results: {e}")


# Pre-defined test scenarios for Universal Workshop ERP
def create_default_test_scenarios():
    """Create default load test scenarios for workshop operations"""
    framework = LoadTestingFramework()

    # Scenario 1: Normal Workshop Operations
    framework.create_load_test_scenario(
        "normal_operations",
        {
            "concurrent_users": 100,
            "duration_minutes": 15,
            "ramp_up_time": 120,
            "arabic_percentage": 70,
            "think_time": 3,
            "description": "Normal daily workshop operations with mixed Arabic/English usage",
            "endpoints": [
                {
                    "path": "/api/method/frappe.desk.search.search_link",
                    "method": "GET",
                    "type": "customer",
                },
                {
                    "path": "/api/resource/Workshop Profile",
                    "method": "GET",
                    "type": "workshop_profile",
                },
                {"path": "/api/resource/Service Order", "method": "POST", "type": "service_order"},
                {"path": "/api/resource/Customer", "method": "GET", "type": "customer"},
            ],
            "max_response_time": 3000,
            "error_rate_threshold": 2,
            "min_throughput": 50,
        },
    )

    # Scenario 2: Peak Hour Stress Test
    framework.create_load_test_scenario(
        "peak_hour_stress",
        {
            "concurrent_users": 500,
            "duration_minutes": 30,
            "ramp_up_time": 300,
            "arabic_percentage": 80,
            "think_time": 1,
            "description": "Peak hour stress test with high Arabic usage",
            "endpoints": [
                {
                    "path": "/api/method/frappe.desk.search.search_link",
                    "method": "GET",
                    "type": "customer",
                },
                {
                    "path": "/api/resource/Workshop Profile",
                    "method": "GET",
                    "type": "workshop_profile",
                },
                {"path": "/api/resource/Service Order", "method": "POST", "type": "service_order"},
                {"path": "/api/resource/Vehicle", "method": "GET", "type": "vehicle"},
                {"path": "/api/resource/Customer", "method": "POST", "type": "customer"},
            ],
            "max_response_time": 5000,
            "error_rate_threshold": 5,
            "min_throughput": 100,
        },
    )

    # Scenario 3: Maximum Capacity Test
    framework.create_load_test_scenario(
        "maximum_capacity",
        {
            "concurrent_users": 1000,
            "duration_minutes": 60,
            "ramp_up_time": 600,
            "arabic_percentage": 75,
            "think_time": 2,
            "description": "1000+ concurrent users capacity test",
            "endpoints": [
                {
                    "path": "/api/method/frappe.desk.search.search_link",
                    "method": "GET",
                    "type": "customer",
                },
                {
                    "path": "/api/resource/Workshop Profile",
                    "method": "GET",
                    "type": "workshop_profile",
                },
                {"path": "/api/resource/Service Order", "method": "POST", "type": "service_order"},
                {"path": "/api/resource/Vehicle", "method": "GET", "type": "vehicle"},
                {"path": "/api/resource/Customer", "method": "POST", "type": "customer"},
                {"path": "/api/resource/Parts Inventory", "method": "GET", "type": "inventory"},
            ],
            "max_response_time": 8000,
            "error_rate_threshold": 10,
            "min_throughput": 150,
        },
    )

    return framework


# WhiteListed API methods for external access
@frappe.whitelist()
def run_load_test(scenario_name):
    """Execute a specific load test scenario"""
    framework = create_default_test_scenarios()
    return framework.execute_load_test(scenario_name)


@frappe.whitelist()
def get_load_test_scenarios():
    """Get list of available load test scenarios"""
    framework = create_default_test_scenarios()
    return list(framework.test_scenarios.keys())


@frappe.whitelist()
def get_load_test_results(limit=10):
    """Get recent load test results"""
    return frappe.get_list(
        "Load Test Result",
        fields=[
            "name",
            "scenario_name",
            "test_timestamp",
            "overall_grade",
            "pass_percentage",
            "total_requests",
            "avg_response_time",
        ],
        order_by="test_timestamp desc",
        limit=limit,
    )


@frappe.whitelist()
def get_system_resources():
    """Get current system resource usage"""
    framework = LoadTestingFramework()
    return framework.get_system_resources()
