# Week 16: Scheduler Functions for Load Testing & Production Deployment
# Universal Workshop ERP - Scheduled Job Implementations

import frappe
from frappe import _
from frappe.utils import now, add_days, cint, flt
from datetime import datetime, timedelta
import json

# Health Monitoring Scheduler Functions


def collect_realtime_health_metrics():
    """Collect real-time health metrics every 5 minutes"""
    try:
        from universal_workshop.utils.health_monitoring import HealthMonitoringSystem

        monitor = HealthMonitoringSystem()

        # Collect metrics
        metrics = monitor.collect_comprehensive_health_metrics()

        # Store key metrics in Redis for dashboard
        if monitor.redis_client:
            key_metrics = {
                "cpu_percent": metrics.get("system", {}).get("cpu_percent", 0),
                "memory_percent": metrics.get("system", {}).get("memory_percent", 0),
                "disk_percent": metrics.get("system", {}).get("disk_percent", 0),
                "health_score": metrics.get("overall_health", {}).get("score", 0),
                "timestamp": metrics.get("timestamp"),
            }

            monitor.redis_client.setex(
                "health:realtime:latest", 300, json.dumps(key_metrics)  # 5 minutes
            )

        return {"success": True, "metrics_collected": True}

    except Exception as e:
        frappe.log_error(f"Error collecting real-time health metrics: {e}")
        return {"success": False, "error": str(e)}


def check_critical_alerts():
    """Check for critical health alerts every 10 minutes"""
    try:
        from universal_workshop.utils.health_monitoring import HealthMonitoringSystem

        monitor = HealthMonitoringSystem()

        # Get current metrics
        metrics = monitor.collect_comprehensive_health_metrics()

        # Check for critical alerts
        alerts = monitor._check_alert_conditions(metrics)
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]

        if critical_alerts:
            # Send notifications for critical alerts
            for alert in critical_alerts:
                frappe.publish_realtime(
                    event="critical_alert",
                    message={
                        "type": "critical_health_alert",
                        "message": alert["message"],
                        "timestamp": now(),
                        "severity": "critical",
                    },
                    user="Administrator",  # Send to system admin
                )

                # Log critical alert
                frappe.log_error(f"Critical Health Alert: {alert['message']}", "Health Monitor")

        return {"success": True, "critical_alerts": len(critical_alerts)}

    except Exception as e:
        frappe.log_error(f"Error checking critical alerts: {e}")
        return {"success": False, "error": str(e)}


def comprehensive_health_check():
    """Comprehensive health check every hour"""
    try:
        from universal_workshop.utils.health_monitoring import HealthMonitoringSystem

        monitor = HealthMonitoringSystem()

        # Perform comprehensive health check
        health_report = monitor.collect_comprehensive_health_metrics()

        # Store hourly health report
        health_doc = frappe.new_doc("Health Monitor Report")
        health_doc.timestamp = now()
        health_doc.overall_health_score = health_report.get("overall_health", {}).get("score", 0)
        health_doc.health_status = health_report.get("overall_health", {}).get("status", "unknown")
        health_doc.system_metrics_json = json.dumps(health_report.get("system", {}))
        health_doc.database_metrics_json = json.dumps(health_report.get("database", {}))
        health_doc.application_metrics_json = json.dumps(health_report.get("application", {}))
        health_doc.arabic_metrics_json = json.dumps(health_report.get("arabic_specific", {}))
        health_doc.report_type = "hourly"
        health_doc.insert()
        frappe.db.commit()

        return {
            "success": True,
            "health_score": health_report.get("overall_health", {}).get("score", 0),
        }

    except Exception as e:
        frappe.log_error(f"Error in comprehensive health check: {e}")
        return {"success": False, "error": str(e)}


def cleanup_old_health_data():
    """Clean up old health data daily"""
    try:
        # Delete health reports older than 90 days
        cutoff_date = add_days(now(), -90)

        old_reports = frappe.get_list(
            "Health Monitor Report", filters={"timestamp": ["<", cutoff_date]}, fields=["name"]
        )

        deleted_count = 0
        for report in old_reports:
            frappe.delete_doc("Health Monitor Report", report.name, force=True)
            deleted_count += 1

        frappe.db.commit()

        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        frappe.log_error(f"Error cleaning up old health data: {e}")
        return {"success": False, "error": str(e)}


def generate_weekly_health_report():
    """Generate comprehensive weekly health report"""
    try:
        from universal_workshop.utils.health_monitoring import HealthMonitoringSystem

        monitor = HealthMonitoringSystem()

        # Get health data for the past week
        week_ago = add_days(now(), -7)

        weekly_reports = frappe.get_list(
            "Health Monitor Report",
            filters={"timestamp": [">=", week_ago], "report_type": "hourly"},
            fields=["overall_health_score", "health_status", "timestamp"],
            order_by="timestamp",
        )

        if weekly_reports:
            # Calculate weekly statistics
            scores = [r.overall_health_score for r in weekly_reports if r.overall_health_score]
            avg_score = sum(scores) / len(scores) if scores else 0
            min_score = min(scores) if scores else 0
            max_score = max(scores) if scores else 0

            # Count status distribution
            status_counts = {}
            for report in weekly_reports:
                status = report.health_status
                status_counts[status] = status_counts.get(status, 0) + 1

            # Create weekly summary report
            weekly_summary = frappe.new_doc("Health Monitor Report")
            weekly_summary.timestamp = now()
            weekly_summary.overall_health_score = avg_score
            weekly_summary.health_status = (
                "excellent" if avg_score >= 90 else "good" if avg_score >= 75 else "fair"
            )
            weekly_summary.report_type = "weekly"
            weekly_summary.summary_data_json = json.dumps(
                {
                    "average_score": avg_score,
                    "minimum_score": min_score,
                    "maximum_score": max_score,
                    "total_reports": len(weekly_reports),
                    "status_distribution": status_counts,
                    "trend": (
                        "improving"
                        if scores[-1] > scores[0]
                        else "declining" if scores[-1] < scores[0] else "stable"
                    ),
                }
            )
            weekly_summary.insert()
            frappe.db.commit()

        return {"success": True, "reports_analyzed": len(weekly_reports) if weekly_reports else 0}

    except Exception as e:
        frappe.log_error(f"Error generating weekly health report: {e}")
        return {"success": False, "error": str(e)}


# Production Deployment Scheduler Functions


def monitor_deployment_health():
    """Monitor production deployment health every 5 minutes"""
    try:
        from universal_workshop.utils.production_deployment import ProductionDeploymentManager

        manager = ProductionDeploymentManager()

        # Check deployment health
        health_check = manager._run_pre_deployment_checks()

        # Store deployment health status
        if manager.redis_client:
            manager.redis_client.setex(
                "deployment:health:latest",
                300,  # 5 minutes
                json.dumps(
                    {
                        "status": "healthy" if health_check["success"] else "unhealthy",
                        "failed_checks": health_check.get("failed_checks", []),
                        "timestamp": now(),
                    }
                ),
            )

        return {"success": True, "deployment_healthy": health_check["success"]}

    except Exception as e:
        frappe.log_error(f"Error monitoring deployment health: {e}")
        return {"success": False, "error": str(e)}


def system_health_assessment():
    """Comprehensive system health assessment hourly"""
    try:
        from universal_workshop.utils.production_deployment import ProductionDeploymentManager

        manager = ProductionDeploymentManager()

        # Perform comprehensive system assessment
        system_check = manager._check_system_resources()
        arabic_check = manager._check_arabic_locale_support()

        # Store assessment results
        assessment_doc = frappe.new_doc("System Health Assessment")
        assessment_doc.timestamp = now()
        assessment_doc.cpu_percent = system_check.get("cpu_percent", 0)
        assessment_doc.memory_percent = system_check.get("memory_percent", 0)
        assessment_doc.disk_percent = system_check.get("disk_percent", 0)
        assessment_doc.arabic_support_status = "working" if arabic_check["success"] else "issues"
        assessment_doc.overall_status = (
            "healthy" if system_check["success"] and arabic_check["success"] else "issues"
        )
        assessment_doc.warnings_json = json.dumps(system_check.get("warnings", []))
        assessment_doc.insert()
        frappe.db.commit()

        return {"success": True, "system_healthy": system_check["success"]}

    except Exception as e:
        frappe.log_error(f"Error in system health assessment: {e}")
        return {"success": False, "error": str(e)}


def validate_deployment_integrity():
    """Validate deployment integrity daily"""
    try:
        from universal_workshop.utils.production_deployment import ProductionDeploymentManager

        manager = ProductionDeploymentManager()

        # Validate all deployment components
        validation_results = {
            "database": manager._check_database_connectivity(),
            "redis": manager._check_redis_connectivity(),
            "ssl": manager._check_ssl_certificates(),
            "backup": manager._check_backup_systems(),
            "arabic": manager._check_arabic_locale_support(),
        }

        # Count successful validations
        successful_checks = sum(
            1 for result in validation_results.values() if result.get("success", False)
        )
        total_checks = len(validation_results)

        # Store validation results
        validation_doc = frappe.new_doc("Deployment Validation")
        validation_doc.timestamp = now()
        validation_doc.successful_checks = successful_checks
        validation_doc.total_checks = total_checks
        validation_doc.success_rate = (successful_checks / total_checks) * 100
        validation_doc.validation_results_json = json.dumps(validation_results)
        validation_doc.overall_status = "passed" if successful_checks == total_checks else "failed"
        validation_doc.insert()
        frappe.db.commit()

        return {"success": True, "validation_passed": successful_checks == total_checks}

    except Exception as e:
        frappe.log_error(f"Error validating deployment integrity: {e}")
        return {"success": False, "error": str(e)}


# Load Testing Scheduler Functions


def cleanup_old_test_results():
    """Clean up old load test results daily"""
    try:
        from universal_workshop.utils.load_testing_framework import LoadTestingFramework

        framework = LoadTestingFramework()

        # Clean up results older than 90 days
        result = framework.cleanup_old_test_results(90)

        return result

    except Exception as e:
        frappe.log_error(f"Error cleaning up old test results: {e}")
        return {"success": False, "error": str(e)}


def run_daily_smoke_tests():
    """Run daily smoke tests for system validation"""
    try:
        from universal_workshop.utils.load_testing_framework import create_default_test_scenarios

        framework = create_default_test_scenarios()

        # Create a light smoke test scenario
        framework.create_load_test_scenario(
            "daily_smoke_test",
            {
                "concurrent_users": 10,
                "duration_minutes": 5,
                "ramp_up_time": 30,
                "arabic_percentage": 70,
                "think_time": 2,
                "description": "Daily smoke test for system validation",
                "endpoints": [
                    {
                        "path": "/api/method/frappe.auth.get_logged_user",
                        "method": "GET",
                        "type": "auth",
                    },
                    {
                        "path": "/api/resource/Workshop Profile",
                        "method": "GET",
                        "type": "workshop_profile",
                    },
                ],
                "max_response_time": 5000,
                "error_rate_threshold": 1,
                "min_throughput": 5,
            },
        )

        # Run the smoke test
        test_result = framework.execute_load_test("daily_smoke_test")

        # Send alert if smoke test fails
        if not test_result.get("success", False) or test_result.get("overall_grade") in ["D", "F"]:
            frappe.publish_realtime(
                event="smoke_test_failure",
                message={
                    "type": "smoke_test_alert",
                    "message": "Daily smoke test failed - system may have issues",
                    "test_result": test_result,
                    "timestamp": now(),
                },
                user="Administrator",
            )

        return test_result

    except Exception as e:
        frappe.log_error(f"Error running daily smoke tests: {e}")
        return {"success": False, "error": str(e)}


def run_weekly_capacity_test():
    """Run weekly capacity test for performance validation"""
    try:
        from universal_workshop.utils.load_testing_framework import create_default_test_scenarios

        framework = create_default_test_scenarios()

        # Run the peak hour stress test scenario
        test_result = framework.execute_load_test("peak_hour_stress")

        # Store weekly capacity test results
        capacity_doc = frappe.new_doc("Weekly Capacity Test")
        capacity_doc.test_timestamp = now()
        capacity_doc.test_result_json = json.dumps(test_result)
        capacity_doc.overall_grade = test_result.get("overall_grade", "F")
        capacity_doc.pass_percentage = test_result.get("pass_percentage", 0)
        capacity_doc.concurrent_users = test_result.get("configuration", {}).get(
            "concurrent_users", 0
        )
        capacity_doc.avg_response_time = test_result.get("performance_metrics", {}).get(
            "avg_response_time", 0
        )
        capacity_doc.throughput = test_result.get("performance_metrics", {}).get("throughput", 0)
        capacity_doc.insert()
        frappe.db.commit()

        return test_result

    except Exception as e:
        frappe.log_error(f"Error running weekly capacity test: {e}")
        return {"success": False, "error": str(e)}


# Archive and Optimization Functions


def archive_old_health_data():
    """Archive old health data monthly"""
    try:
        # Archive health reports older than 6 months to compressed format
        archive_date = add_days(now(), -180)

        old_reports = frappe.get_list(
            "Health Monitor Report",
            filters={"timestamp": ["<", archive_date]},
            fields=["name", "timestamp", "overall_health_score", "health_status"],
        )

        if old_reports:
            # Create monthly archive document
            archive_doc = frappe.new_doc("Health Data Archive")
            archive_doc.archive_date = now()
            archive_doc.archived_records_count = len(old_reports)
            archive_doc.date_range_start = min(r.timestamp for r in old_reports)
            archive_doc.date_range_end = max(r.timestamp for r in old_reports)
            archive_doc.archived_data_json = json.dumps(old_reports)
            archive_doc.insert()

            # Delete original records
            for report in old_reports:
                frappe.delete_doc("Health Monitor Report", report.name, force=True)

            frappe.db.commit()

        return {"success": True, "archived_records": len(old_reports)}

    except Exception as e:
        frappe.log_error(f"Error archiving old health data: {e}")
        return {"success": False, "error": str(e)}


def optimize_production_configuration():
    """Optimize production configuration monthly"""
    try:
        from universal_workshop.utils.production_deployment import ProductionDeploymentManager

        manager = ProductionDeploymentManager()

        # Analyze system performance over the past month
        month_ago = add_days(now(), -30)

        performance_data = frappe.get_list(
            "Health Monitor Report",
            filters={"timestamp": [">=", month_ago], "report_type": "hourly"},
            fields=["overall_health_score", "timestamp"],
        )

        optimization_recommendations = []

        if performance_data:
            scores = [r.overall_health_score for r in performance_data if r.overall_health_score]
            avg_score = sum(scores) / len(scores) if scores else 0

            # Generate optimization recommendations based on performance
            if avg_score < 75:
                optimization_recommendations.extend(
                    [
                        "Consider upgrading system resources",
                        "Optimize database queries and indexes",
                        "Review and optimize Arabic text processing",
                        "Implement additional caching strategies",
                    ]
                )
            elif avg_score < 85:
                optimization_recommendations.extend(
                    [
                        "Fine-tune system configuration",
                        "Optimize background job processing",
                        "Review Arabic localization performance",
                    ]
                )
            else:
                optimization_recommendations.append("System performance is optimal")

        # Store optimization report
        optimization_doc = frappe.new_doc("Production Optimization Report")
        optimization_doc.timestamp = now()
        optimization_doc.analysis_period_days = 30
        optimization_doc.avg_performance_score = avg_score if "avg_score" in locals() else 0
        optimization_doc.recommendations_json = json.dumps(optimization_recommendations)
        optimization_doc.records_analyzed = len(performance_data)
        optimization_doc.insert()
        frappe.db.commit()

        return {"success": True, "recommendations_count": len(optimization_recommendations)}

    except Exception as e:
        frappe.log_error(f"Error optimizing production configuration: {e}")
        return {"success": False, "error": str(e)}
