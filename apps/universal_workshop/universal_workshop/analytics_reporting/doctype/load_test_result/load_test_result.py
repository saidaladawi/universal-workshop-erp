# Week 16: Load Testing Framework & Production Deployment
# Load Test Result DocType Controller

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, flt, cint, add_days
from typing import Dict, List, Any
import statistics


class LoadTestResult(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate load test result data"""
        self.validate_test_metrics()
        self.calculate_derived_metrics()
        self.validate_test_report_json()

    def before_save(self):
        """Process data before saving"""
        if not self.test_timestamp:
            self.test_timestamp = now()

        self.extract_summary_from_json()
        self.generate_recommendations_text()

    def validate_test_metrics(self):
        """Validate test metrics for consistency"""
        if self.total_requests and self.total_requests < 0:
            frappe.throw(_("Total requests cannot be negative"))

        if self.successful_requests and self.failed_requests:
            calculated_total = self.successful_requests + self.failed_requests
            if self.total_requests and abs(calculated_total - self.total_requests) > 0:
                frappe.throw(_("Total requests must equal successful + failed requests"))

        if self.pass_percentage and (self.pass_percentage < 0 or self.pass_percentage > 100):
            frappe.throw(_("Pass percentage must be between 0 and 100"))

        if self.error_rate and (self.error_rate < 0 or self.error_rate > 100):
            frappe.throw(_("Error rate must be between 0 and 100"))

    def calculate_derived_metrics(self):
        """Calculate derived metrics from basic data"""
        if self.successful_requests and self.failed_requests:
            self.total_requests = self.successful_requests + self.failed_requests

        if self.total_requests and self.total_requests > 0:
            self.error_rate = (self.failed_requests / self.total_requests) * 100

        if not self.concurrent_users and self.test_report_json:
            try:
                report_data = json.loads(self.test_report_json)
                config = report_data.get("configuration", {})
                self.concurrent_users = config.get("concurrent_users", 0)
            except (json.JSONDecodeError, KeyError):
                pass

    def validate_test_report_json(self):
        """Validate JSON structure of test report"""
        if self.test_report_json:
            try:
                report_data = json.loads(self.test_report_json)
                required_keys = ["scenario_name", "test_timestamp", "performance_metrics"]

                for key in required_keys:
                    if key not in report_data:
                        frappe.throw(_("Test report JSON missing required key: {0}").format(key))

            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in test report"))

    def extract_summary_from_json(self):
        """Extract summary data from detailed JSON report"""
        if not self.test_report_json:
            return

        try:
            report_data = json.loads(self.test_report_json)

            # Extract Arabic usage statistics
            arabic_stats = report_data.get("arabic_usage_stats", {})
            if arabic_stats.get("total_requests", 0) > 0:
                self.arabic_requests_percentage = arabic_stats.get("arabic_percentage", 0)

            # Extract system health score
            system_health = report_data.get("system_health", {})
            self.system_health_score = system_health.get("health_score", 0)

            # Extract performance metrics if not already set
            metrics = report_data.get("performance_metrics", {})
            if not self.avg_response_time:
                self.avg_response_time = metrics.get("avg_response_time", 0)
            if not self.max_response_time:
                self.max_response_time = metrics.get("max_response_time", 0)
            if not self.min_response_time:
                self.min_response_time = metrics.get("min_response_time", 0)
            if not self.throughput:
                self.throughput = metrics.get("throughput", 0)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            frappe.log_error(f"Error extracting summary from JSON: {e}")

    def generate_recommendations_text(self):
        """Generate human-readable recommendations from JSON data"""
        if not self.test_report_json:
            return

        try:
            report_data = json.loads(self.test_report_json)
            recommendations = report_data.get("recommendations", [])

            if recommendations:
                self.recommendations = "\n".join([f"• {rec}" for rec in recommendations])

            # Extract errors summary
            metrics = report_data.get("performance_metrics", {})
            errors = metrics.get("errors", [])

            if errors:
                # Group similar errors
                error_counts = {}
                for error in errors[:50]:  # Limit to first 50 errors
                    error_counts[error] = error_counts.get(error, 0) + 1

                error_summary = []
                for error, count in error_counts.items():
                    if count > 1:
                        error_summary.append(f"{error} ({count} times)")
                    else:
                        error_summary.append(error)

                self.errors_summary = "\n".join(error_summary[:20])  # Limit to 20 unique errors

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            frappe.log_error(f"Error generating recommendations text: {e}")


# WhiteListed API methods for Load Test Result management


@frappe.whitelist()
def get_test_performance_summary(days=30):
    """Get performance summary for load tests over specified days"""
    try:
        from_date = add_days(now(), -days)

        results = frappe.get_list(
            "Load Test Result",
            filters={"test_timestamp": [">=", from_date], "docstatus": 1},
            fields=[
                "name",
                "scenario_name",
                "test_timestamp",
                "overall_grade",
                "pass_percentage",
                "avg_response_time",
                "throughput",
                "error_rate",
                "concurrent_users",
                "total_requests",
            ],
            order_by="test_timestamp desc",
        )

        if not results:
            return {
                "summary": {
                    "total_tests": 0,
                    "avg_grade": "N/A",
                    "avg_pass_percentage": 0,
                    "avg_response_time": 0,
                    "avg_throughput": 0,
                    "trend": "stable",
                },
                "tests": [],
                "grade_distribution": {},
                "performance_trend": [],
            }

        # Calculate summary statistics
        grades = [r.overall_grade for r in results if r.overall_grade]
        pass_percentages = [r.pass_percentage for r in results if r.pass_percentage]
        response_times = [r.avg_response_time for r in results if r.avg_response_time]
        throughputs = [r.throughput for r in results if r.throughput]

        # Calculate grade distribution
        grade_distribution = {}
        for grade in grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        # Calculate performance trend (last 10 tests)
        recent_tests = results[:10]
        performance_trend = []

        for test in reversed(recent_tests):
            performance_trend.append(
                {
                    "date": test.test_timestamp.split()[0] if test.test_timestamp else "",
                    "pass_percentage": test.pass_percentage or 0,
                    "avg_response_time": test.avg_response_time or 0,
                    "throughput": test.throughput or 0,
                }
            )

        # Determine trend
        if len(pass_percentages) >= 2:
            recent_avg = (
                statistics.mean(pass_percentages[:5])
                if len(pass_percentages) >= 5
                else statistics.mean(pass_percentages[:2])
            )
            older_avg = (
                statistics.mean(pass_percentages[-5:])
                if len(pass_percentages) >= 10
                else statistics.mean(pass_percentages[-2:])
            )

            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "summary": {
                "total_tests": len(results),
                "avg_grade": statistics.mode(grades) if grades else "N/A",
                "avg_pass_percentage": statistics.mean(pass_percentages) if pass_percentages else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
                "trend": trend,
            },
            "tests": results,
            "grade_distribution": grade_distribution,
            "performance_trend": performance_trend,
        }

    except Exception as e:
        frappe.log_error(f"Error getting test performance summary: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def get_scenario_comparison(scenario_names=None):
    """Compare performance across different test scenarios"""
    try:
        if isinstance(scenario_names, str):
            scenario_names = json.loads(scenario_names)

        if not scenario_names:
            # Get all unique scenario names
            scenario_names = frappe.get_list(
                "Load Test Result",
                filters={"docstatus": 1},
                fields=["scenario_name"],
                group_by="scenario_name",
                pluck="scenario_name",
            )

        comparison_data = {}

        for scenario in scenario_names:
            results = frappe.get_list(
                "Load Test Result",
                filters={"scenario_name": scenario, "docstatus": 1},
                fields=[
                    "overall_grade",
                    "pass_percentage",
                    "avg_response_time",
                    "throughput",
                    "error_rate",
                    "concurrent_users",
                    "test_timestamp",
                    "total_requests",
                ],
                order_by="test_timestamp desc",
                limit=10,  # Last 10 tests for each scenario
            )

            if results:
                # Calculate statistics
                pass_percentages = [r.pass_percentage for r in results if r.pass_percentage]
                response_times = [r.avg_response_time for r in results if r.avg_response_time]
                throughputs = [r.throughput for r in results if r.throughput]
                error_rates = [r.error_rate for r in results if r.error_rate]

                comparison_data[scenario] = {
                    "test_count": len(results),
                    "latest_test": results[0].test_timestamp if results else None,
                    "avg_pass_percentage": (
                        statistics.mean(pass_percentages) if pass_percentages else 0
                    ),
                    "avg_response_time": statistics.mean(response_times) if response_times else 0,
                    "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
                    "avg_error_rate": statistics.mean(error_rates) if error_rates else 0,
                    "best_pass_percentage": max(pass_percentages) if pass_percentages else 0,
                    "worst_response_time": max(response_times) if response_times else 0,
                    "best_throughput": max(throughputs) if throughputs else 0,
                    "concurrent_users": results[0].concurrent_users if results else 0,
                    "grade_distribution": {},
                }

                # Calculate grade distribution
                for result in results:
                    grade = result.overall_grade
                    if grade:
                        comparison_data[scenario]["grade_distribution"][grade] = (
                            comparison_data[scenario]["grade_distribution"].get(grade, 0) + 1
                        )

        return comparison_data

    except Exception as e:
        frappe.log_error(f"Error getting scenario comparison: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def get_performance_alerts():
    """Get performance alerts based on recent test results"""
    try:
        # Get recent test results (last 7 days)
        from_date = add_days(now(), -7)

        recent_results = frappe.get_list(
            "Load Test Result",
            filters={"test_timestamp": [">=", from_date], "docstatus": 1},
            fields=[
                "name",
                "scenario_name",
                "test_timestamp",
                "overall_grade",
                "pass_percentage",
                "avg_response_time",
                "error_rate",
                "throughput",
            ],
            order_by="test_timestamp desc",
        )

        alerts = []

        for result in recent_results:
            # Critical alerts (Grade F or very low pass percentage)
            if result.overall_grade == "F" or (
                result.pass_percentage and result.pass_percentage < 50
            ):
                alerts.append(
                    {
                        "severity": "critical",
                        "message": f"Critical failure in {result.scenario_name} test",
                        "details": f"Grade: {result.overall_grade}, Pass Rate: {result.pass_percentage}%",
                        "test_name": result.name,
                        "timestamp": result.test_timestamp,
                    }
                )

            # High response time alerts (> 10 seconds)
            elif result.avg_response_time and result.avg_response_time > 10000:
                alerts.append(
                    {
                        "severity": "high",
                        "message": f"High response time in {result.scenario_name}",
                        "details": f"Average response time: {result.avg_response_time:.0f}ms",
                        "test_name": result.name,
                        "timestamp": result.test_timestamp,
                    }
                )

            # High error rate alerts (> 10%)
            elif result.error_rate and result.error_rate > 10:
                alerts.append(
                    {
                        "severity": "high",
                        "message": f"High error rate in {result.scenario_name}",
                        "details": f"Error rate: {result.error_rate:.1f}%",
                        "test_name": result.name,
                        "timestamp": result.test_timestamp,
                    }
                )

            # Low throughput alerts (< 10 req/sec)
            elif result.throughput and result.throughput < 10:
                alerts.append(
                    {
                        "severity": "medium",
                        "message": f"Low throughput in {result.scenario_name}",
                        "details": f"Throughput: {result.throughput:.1f} req/sec",
                        "test_name": result.name,
                        "timestamp": result.test_timestamp,
                    }
                )

        # Sort alerts by severity and timestamp
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(
            key=lambda x: (severity_order.get(x["severity"], 3), x["timestamp"]), reverse=True
        )

        return alerts[:20]  # Return top 20 alerts

    except Exception as e:
        frappe.log_error(f"Error getting performance alerts: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def generate_load_test_report(test_name):
    """Generate detailed report for a specific load test"""
    try:
        result = frappe.get_doc("Load Test Result", test_name)

        if not result.test_report_json:
            return {"error": "No detailed test data available"}

        report_data = json.loads(result.test_report_json)

        # Enhanced report with additional analysis
        enhanced_report = {
            "basic_info": {
                "scenario_name": result.scenario_name,
                "test_timestamp": result.test_timestamp,
                "duration_seconds": result.duration_seconds,
                "overall_grade": result.overall_grade,
                "pass_percentage": result.pass_percentage,
            },
            "performance_metrics": {
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "avg_response_time": result.avg_response_time,
                "max_response_time": result.max_response_time,
                "min_response_time": result.min_response_time,
                "throughput": result.throughput,
                "error_rate": result.error_rate,
            },
            "arabic_support": {
                "arabic_requests_percentage": result.arabic_requests_percentage,
                "arabic_usage_stats": report_data.get("arabic_usage_stats", {}),
            },
            "system_health": {
                "health_score": result.system_health_score,
                "system_health_details": report_data.get("system_health", {}),
            },
            "recommendations": result.recommendations.split("\n") if result.recommendations else [],
            "errors_summary": result.errors_summary.split("\n") if result.errors_summary else [],
            "configuration": report_data.get("configuration", {}),
            "detailed_metrics": report_data.get("performance_metrics", {}),
            "system_resources": report_data.get("performance_metrics", {}).get(
                "system_resources", []
            ),
        }

        return enhanced_report

    except Exception as e:
        frappe.log_error(f"Error generating load test report: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def cleanup_old_test_results(days=90):
    """Clean up old test results older than specified days"""
    try:
        cutoff_date = add_days(now(), -days)

        old_results = frappe.get_list(
            "Load Test Result", filters={"test_timestamp": ["<", cutoff_date]}, fields=["name"]
        )

        deleted_count = 0
        for result in old_results:
            try:
                frappe.delete_doc("Load Test Result", result.name, force=True)
                deleted_count += 1
            except Exception as e:
                frappe.log_error(f"Error deleting old test result {result.name}: {e}")

        frappe.db.commit()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} old test results older than {days} days",
        }

    except Exception as e:
        frappe.log_error(f"Error cleaning up old test results: {e}")
        return {"error": str(e)}
