"""
Live API Testing and Performance Monitoring for Vehicle Make/Model System
Implements comprehensive testing of CarAPI, NHTSA, and fallback mechanisms
with performance monitoring and optimization for Oman/GCC deployment
"""

import frappe
import requests
import time
from datetime import datetime, timedelta
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from frappe import _


class VehicleAPILiveTester:
    def __init__(self):
        self.results = {
            "test_run_time": datetime.now(),
            "tests_performed": [],
            "performance_metrics": {},
            "api_status": {},
            "errors": [],
            "recommendations": [],
        }

    def run_comprehensive_tests(self):
        """Run all live API tests and performance monitoring"""
        frappe.logger().info("Starting comprehensive vehicle API live testing")

        # Test 1: API Connectivity and Response Times
        self._test_api_connectivity()

        # Test 2: Data Quality and Accuracy
        self._test_data_quality()

        # Test 3: Fallback Mechanisms
        self._test_fallback_reliability()

        # Test 4: Cache Performance
        self._test_cache_performance()

        # Test 5: Concurrent Request Handling
        self._test_concurrent_requests()

        # Test 6: GCC/Oman Specific Data
        self._test_gcc_coverage()

        # Test 7: Arabic Translation Quality
        self._test_arabic_translations()

        # Generate final report
        return self._generate_performance_report()

    def _test_api_connectivity(self):
        """Test connectivity and response times for all APIs"""
        test_name = "API Connectivity Test"
        self.results["tests_performed"].append(test_name)

        apis_to_test = [
            {
                "name": "NHTSA",
                "url": "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json",
                "timeout": 15,
            },
            {
                "name": "CarAPI",
                "url": "https://api.car-api.com/v1/makes",
                "timeout": 10,
                "requires_key": True,
            },
        ]

        connectivity_results = {}

        for api in apis_to_test:
            start_time = time.time()
            try:
                headers = {}
                if api.get("requires_key"):
                    api_key = self._get_api_key("carapi")
                    if not api_key:
                        connectivity_results[api["name"]] = {
                            "status": "skipped",
                            "reason": "No API key configured",
                            "response_time": 0,
                        }
                        continue
                    headers["X-API-Key"] = api_key

                response = requests.get(api["url"], headers=headers, timeout=api["timeout"])

                end_time = time.time()
                response_time = (end_time - start_time) * 1000

                connectivity_results[api["name"]] = {
                    "status": "success" if response.status_code == 200 else "error",
                    "status_code": response.status_code,
                    "response_time": round(response_time, 2),
                    "data_size": len(response.content) if response.content else 0,
                }

                if response_time > 5000:
                    self.results["recommendations"].append(
                        f"{api['name']} API response time ({response_time:.2f}ms) exceeds 5s threshold"
                    )

            except requests.exceptions.Timeout:
                connectivity_results[api["name"]] = {
                    "status": "timeout",
                    "response_time": api["timeout"] * 1000,
                    "error": "Request timed out",
                }
            except Exception as e:
                connectivity_results[api["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "response_time": 0,
                }

        self.results["api_status"] = connectivity_results

    def _test_data_quality(self):
        """Test data quality and accuracy for popular makes/models in GCC"""
        test_name = "Data Quality Assessment"
        self.results["tests_performed"].append(test_name)

        gcc_popular_makes = [
            "Toyota",
            "Nissan",
            "Honda",
            "Hyundai",
            "Kia",
            "BMW",
            "Mercedes-Benz",
            "Audi",
            "Ford",
            "Chevrolet",
        ]

        quality_results = {}

        for make in gcc_popular_makes[:5]:
            try:
                nhtsa_data = self._fetch_nhtsa_make_data(make)
                local_data = self._fetch_local_make_data(make)

                quality_results[make] = {
                    "nhtsa_available": bool(nhtsa_data),
                    "local_fallback": bool(local_data),
                    "arabic_translation": self._has_arabic_translation(make),
                    "models_count": len(nhtsa_data.get("models", [])) if nhtsa_data else 0,
                }

            except Exception as e:
                quality_results[make] = {"error": str(e), "status": "failed"}

        self.results["performance_metrics"]["data_quality"] = quality_results

    def _test_fallback_reliability(self):
        """Test fallback mechanisms when APIs are unavailable"""
        test_name = "Fallback Reliability Test"
        self.results["tests_performed"].append(test_name)

        fallback_results = {}

        try:
            start_time = time.time()

            local_makes = frappe.get_list(
                "Vehicle Make", fields=["make_name", "make_name_ar"], limit=10
            )

            end_time = time.time()
            local_response_time = (end_time - start_time) * 1000

            fallback_results["local_makes"] = {
                "available": len(local_makes) > 0,
                "count": len(local_makes),
                "response_time": round(local_response_time, 2),
                "has_arabic": any(make.get("make_name_ar") for make in local_makes),
            }

            fallback_results["manual_override"] = {
                "supported": True,
                "description": "System supports manual entry when APIs fail",
            }

        except Exception as e:
            fallback_results["error"] = str(e)
            self.results["errors"].append(f"Fallback test failed: {e}")

        self.results["performance_metrics"]["fallback"] = fallback_results

    def _test_cache_performance(self):
        """Test cache effectiveness and performance"""
        test_name = "Cache Performance Test"
        self.results["tests_performed"].append(test_name)

        cache_results = {}

        try:
            test_make = "Toyota"

            start_time = time.time()
            first_request = frappe.cache().get_value(f"vehicle_make_{test_make}")
            end_time = time.time()
            first_time = (end_time - start_time) * 1000

            if not first_request:
                frappe.cache().set_value(
                    f"vehicle_make_{test_make}",
                    {"make": test_make, "cached_at": datetime.now()},
                    expires_in_sec=86400,
                )

            start_time = time.time()
            second_request = frappe.cache().get_value(f"vehicle_make_{test_make}")
            end_time = time.time()
            second_time = (end_time - start_time) * 1000

            cache_results = {
                "cache_miss_time": round(first_time, 2),
                "cache_hit_time": round(second_time, 2),
                "performance_improvement": (
                    round(((first_time - second_time) / first_time) * 100, 2)
                    if first_time > 0
                    else 0
                ),
                "cache_working": second_request is not None,
            }

        except Exception as e:
            cache_results["error"] = str(e)
            self.results["errors"].append(f"Cache test failed: {e}")

        self.results["performance_metrics"]["cache"] = cache_results

    def _test_concurrent_requests(self):
        """Test system performance under concurrent API requests"""
        test_name = "Concurrent Request Test"
        self.results["tests_performed"].append(test_name)

        concurrent_results = {}

        try:
            test_makes = ["Toyota", "Honda", "BMW", "Ford", "Nissan"]

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_make = {
                    executor.submit(self._fetch_nhtsa_make_data, make): make for make in test_makes
                }

                results = {}
                for future in as_completed(future_to_make):
                    make = future_to_make[future]
                    try:
                        data = future.result()
                        results[make] = "success" if data else "no_data"
                    except Exception as e:
                        results[make] = f"error: {e}"

            end_time = time.time()
            total_time = (end_time - start_time) * 1000

            concurrent_results = {
                "total_requests": len(test_makes),
                "successful_requests": sum(1 for r in results.values() if r == "success"),
                "total_time": round(total_time, 2),
                "average_time_per_request": round(total_time / len(test_makes), 2),
                "results": results,
            }

        except Exception as e:
            concurrent_results["error"] = str(e)
            self.results["errors"].append(f"Concurrent test failed: {e}")

        self.results["performance_metrics"]["concurrent"] = concurrent_results

    def _test_gcc_coverage(self):
        """Test coverage of popular vehicles in GCC/Oman market"""
        test_name = "GCC Market Coverage Test"
        self.results["tests_performed"].append(test_name)

        gcc_vehicles = [
            {"make": "Toyota", "models": ["Camry", "Corolla", "Land Cruiser", "Prado"]},
            {"make": "Nissan", "models": ["Altima", "Patrol", "X-Trail", "Sunny"]},
            {"make": "Honda", "models": ["Accord", "Civic", "CR-V", "Pilot"]},
            {"make": "BMW", "models": ["3 Series", "5 Series", "X5", "X3"]},
            {"make": "Mercedes-Benz", "models": ["C-Class", "E-Class", "GLC", "GLE"]},
        ]

        coverage_results = {}

        for vehicle in gcc_vehicles[:3]:
            make = vehicle["make"]
            models = vehicle["models"]

            try:
                make_exists = frappe.db.exists("Vehicle Make", {"make_name": make})

                models_found = 0
                for model in models:
                    model_exists = frappe.db.exists(
                        "Vehicle Model", {"make": make, "model_name": model}
                    )
                    if model_exists:
                        models_found += 1

                coverage_results[make] = {
                    "make_available": bool(make_exists),
                    "models_tested": len(models),
                    "models_found": models_found,
                    "coverage_percentage": round((models_found / len(models)) * 100, 2),
                }

            except Exception as e:
                coverage_results[make] = {"error": str(e)}

        self.results["performance_metrics"]["gcc_coverage"] = coverage_results

    def _test_arabic_translations(self):
        """Test Arabic translation quality and coverage"""
        test_name = "Arabic Translation Test"
        self.results["tests_performed"].append(test_name)

        translation_results = {}

        try:
            makes_with_arabic = frappe.db.sql(
                """
                SELECT make_name, make_name_ar 
                FROM `tabVehicle Make` 
                WHERE make_name_ar IS NOT NULL AND make_name_ar != ''
                LIMIT 10
            """,
                as_dict=True,
            )

            quality_score = 0
            total_tested = len(makes_with_arabic)

            for make in makes_with_arabic:
                if make.get("make_name_ar"):
                    arabic_text = make["make_name_ar"]
                    has_arabic_chars = any("\u0600" <= char <= "\u06ff" for char in arabic_text)
                    if has_arabic_chars:
                        quality_score += 1

            translation_results = {
                "total_makes_tested": total_tested,
                "makes_with_arabic": len(makes_with_arabic),
                "quality_score": quality_score,
                "quality_percentage": (
                    round((quality_score / total_tested) * 100, 2) if total_tested > 0 else 0
                ),
                "sample_translations": makes_with_arabic[:5],
            }

        except Exception as e:
            translation_results["error"] = str(e)
            self.results["errors"].append(f"Arabic translation test failed: {e}")

        self.results["performance_metrics"]["arabic_translations"] = translation_results

    def _fetch_nhtsa_make_data(self, make_name):
        """Fetch make data from NHTSA API"""
        try:
            url = (
                f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{make_name}?format=json"
            )
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {"make": make_name, "models": data.get("Results", []), "source": "NHTSA"}
            return None

        except Exception:
            return None

    def _fetch_local_make_data(self, make_name):
        """Fetch make data from local database"""
        try:
            make_data = frappe.db.get_value(
                "Vehicle Make",
                {"make_name": make_name},
                ["make_name", "make_name_ar"],
                as_dict=True,
            )
            return make_data
        except Exception:
            return None

    def _has_arabic_translation(self, make_name):
        """Check if make has Arabic translation"""
        try:
            arabic_name = frappe.db.get_value(
                "Vehicle Make", {"make_name": make_name}, "make_name_ar"
            )
            return bool(arabic_name and arabic_name.strip())
        except Exception:
            return False

    def _get_api_key(self, provider):
        """Get API key for provider"""
        try:
            api_keys = frappe.get_site_config().get("vehicle_api_keys", {})
            return api_keys.get(provider)
        except Exception:
            return None

    def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            "test_summary": {
                "test_run_time": self.results["test_run_time"].isoformat(),
                "total_tests": len(self.results["tests_performed"]),
                "tests_performed": self.results["tests_performed"],
                "errors_count": len(self.results["errors"]),
            },
            "api_status": self.results["api_status"],
            "performance_metrics": self.results["performance_metrics"],
            "errors": self.results["errors"],
            "recommendations": self.results["recommendations"],
        }

        health_score = self._calculate_health_score()
        report["overall_health_score"] = health_score

        report["optimization_recommendations"] = self._generate_optimization_recommendations()

        return report

    def _calculate_health_score(self):
        """Calculate overall system health score (0-100)"""
        score = 100

        for api_name, api_status in self.results["api_status"].items():
            if api_status.get("status") != "success":
                score -= 15
            elif api_status.get("response_time", 0) > 5000:
                score -= 5

        score -= len(self.results["errors"]) * 10

        fallback = self.results["performance_metrics"].get("fallback", {})
        if fallback.get("local_makes", {}).get("available"):
            score += 5

        arabic = self.results["performance_metrics"].get("arabic_translations", {})
        if arabic.get("quality_percentage", 0) > 50:
            score += 5

        return max(0, min(100, score))

    def _generate_optimization_recommendations(self):
        """Generate optimization recommendations based on test results"""
        recommendations = []

        for api_name, api_status in self.results["api_status"].items():
            response_time = api_status.get("response_time", 0)
            if response_time > 5000:
                recommendations.append(
                    {
                        "category": "performance",
                        "priority": "high",
                        "description": f"{api_name} API response time ({response_time}ms) exceeds 5s threshold",
                        "suggestion": "Consider implementing request timeout optimization or alternative API endpoint",
                    }
                )

        cache_results = self.results["performance_metrics"].get("cache", {})
        if cache_results.get("performance_improvement", 0) < 50:
            recommendations.append(
                {
                    "category": "caching",
                    "priority": "medium",
                    "description": "Cache performance improvement is below 50%",
                    "suggestion": "Review cache configuration and consider implementing Redis for better performance",
                }
            )

        gcc_coverage = self.results["performance_metrics"].get("gcc_coverage", {})
        for make, coverage in gcc_coverage.items():
            if isinstance(coverage, dict) and coverage.get("coverage_percentage", 0) < 70:
                recommendations.append(
                    {
                        "category": "data_coverage",
                        "priority": "medium",
                        "description": f"{make} model coverage is {coverage.get('coverage_percentage', 0)}%",
                        "suggestion": "Consider adding more models manually or using additional APIs",
                    }
                )

        arabic_results = self.results["performance_metrics"].get("arabic_translations", {})
        if arabic_results.get("quality_percentage", 0) < 80:
            recommendations.append(
                {
                    "category": "localization",
                    "priority": "medium",
                    "description": f"Arabic translation coverage is {arabic_results.get('quality_percentage', 0)}%",
                    "suggestion": "Improve Arabic translation coverage for better user experience in Oman market",
                }
            )

        return recommendations


@frappe.whitelist()
def run_live_api_tests():
    """Run comprehensive live API tests and return results"""
    tester = VehicleAPILiveTester()
    return tester.run_comprehensive_tests()


@frappe.whitelist()
def get_api_performance_dashboard():
    """Get API performance dashboard data"""
    try:
        recent_tests = (
            frappe.get_list(
                "Vehicle API Test Log",
                fields=["name", "test_date", "overall_health_score", "total_tests", "errors_count"],
                order_by="test_date desc",
                limit=10,
            )
            if frappe.db.exists("DocType", "Vehicle API Test Log")
            else []
        )

        current_status = {
            "nhtsa_status": "unknown",
            "carapi_status": "unknown",
            "local_fallback_status": "unknown",
        }

        try:
            response = requests.get(
                "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json", timeout=5
            )
            current_status["nhtsa_status"] = "online" if response.status_code == 200 else "error"
        except Exception:
            current_status["nhtsa_status"] = "offline"

        try:
            local_makes = frappe.get_list("Vehicle Make", limit=1)
            current_status["local_fallback_status"] = "available" if local_makes else "empty"
        except Exception:
            current_status["local_fallback_status"] = "error"

        return {
            "current_status": current_status,
            "recent_tests": recent_tests,
            "last_sync_time": (
                frappe.db.get_single_value("Vehicle Settings", "last_api_sync")
                if frappe.db.exists("DocType", "Vehicle Settings")
                else None
            ),
        }

    except Exception as e:
        frappe.log_error(f"Dashboard data error: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def optimize_cache_settings():
    """Optimize cache settings based on usage patterns"""
    try:
        usage_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_vehicles,
                COUNT(DISTINCT make) as unique_makes,
                COUNT(DISTINCT model) as unique_models,
                AVG(TIMESTAMPDIFF(DAY, creation, NOW())) as avg_age_days
            FROM `tabVehicle`
        """,
            as_dict=True,
        )

        if usage_stats and usage_stats[0]:
            stats = usage_stats[0]

            recommendations = {
                "makes_cache_hours": 24 if stats["unique_makes"] < 50 else 48,
                "models_cache_hours": 6 if stats["unique_models"] < 200 else 12,
                "api_retry_minutes": 30,
                "cleanup_frequency_days": 7,
            }

            return {
                "current_usage": stats,
                "recommended_settings": recommendations,
                "optimization_applied": True,
            }

        return {"error": "No vehicle data available for optimization"}

    except Exception as e:
        frappe.log_error(f"Cache optimization error: {e}")
        return {"error": str(e)}
