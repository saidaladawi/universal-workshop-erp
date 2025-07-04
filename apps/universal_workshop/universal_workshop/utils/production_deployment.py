# Week 16: Production Deployment Configuration System
# Universal Workshop ERP - Production Deployment Management

import os
import json
import subprocess
import time
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import frappe
from frappe import _
from frappe.utils import now, flt
import psutil
import docker
import yaml


class ProductionDeploymentManager:
    """
    Comprehensive production deployment management system
    Handles deployment configuration, health monitoring, and scaling
    """

    def __init__(self):
        self.deployment_config = self._load_deployment_config()
        self.docker_client = self._get_docker_client()
        self.deployment_history = []

    def _load_deployment_config(self) -> dict:
        """Load deployment configuration from config files"""
        config_path = frappe.get_app_path("universal_workshop", "config", "production.json")

        default_config = {
            "environment": "production",
            "arabic_support": True,
            "database": {
                "engine": "mariadb",
                "host": "localhost",
                "port": 3306,
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
            },
            "redis": {"host": "localhost", "port": 6379, "db": 0},
            "nginx": {"enabled": True, "ssl": True, "gzip": True, "arabic_fonts": True},
            "supervisor": {"enabled": True, "workers": 4, "auto_restart": True},
            "monitoring": {"prometheus": True, "grafana": True, "alerts": True},
            "backup": {"enabled": True, "frequency": "daily", "retention_days": 30},
            "scaling": {
                "auto_scale": True,
                "min_workers": 2,
                "max_workers": 10,
                "cpu_threshold": 80,
                "memory_threshold": 85,
            },
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            frappe.log_error(f"Error loading deployment config: {e}")

        return default_config

    def _get_docker_client(self):
        """Get Docker client for container management"""
        try:
            return docker.from_env()
        except Exception as e:
            frappe.log_error(f"Docker client initialization failed: {e}")
            return None

    def deploy_to_production(self, version: str = None) -> dict:
        """Deploy Universal Workshop ERP to production environment"""
        deployment_start = time.time()
        deployment_id = f"deploy-{int(deployment_start)}"

        try:
            print(f"\n🚀 Starting Production Deployment: {deployment_id}")

            # Pre-deployment checks
            pre_check_result = self._run_pre_deployment_checks()
            if not pre_check_result["success"]:
                return pre_check_result

            # Create deployment backup
            backup_result = self._create_deployment_backup()
            if not backup_result["success"]:
                return backup_result

            # Deploy components
            deployment_steps = [
                ("Database Migration", self._deploy_database_migration),
                ("Application Deployment", self._deploy_application),
                ("Static Assets", self._deploy_static_assets),
                ("Nginx Configuration", self._deploy_nginx_config),
                ("Supervisor Configuration", self._deploy_supervisor_config),
                ("Monitoring Setup", self._deploy_monitoring),
                ("Health Checks", self._run_post_deployment_health_checks),
            ]

            results = {}
            for step_name, step_function in deployment_steps:
                print(f"   📋 Executing: {step_name}")
                step_result = step_function()
                results[step_name] = step_result

                if not step_result.get("success", False):
                    return {
                        "success": False,
                        "deployment_id": deployment_id,
                        "error": f"Deployment failed at step: {step_name}",
                        "details": step_result,
                        "duration": time.time() - deployment_start,
                    }

            # Finalize deployment
            self._finalize_deployment(deployment_id, version)

            deployment_result = {
                "success": True,
                "deployment_id": deployment_id,
                "version": version,
                "duration": time.time() - deployment_start,
                "steps": results,
                "timestamp": datetime.now().isoformat(),
            }

            self.deployment_history.append(deployment_result)
            self._store_deployment_record(deployment_result)

            print(f"✅ Production Deployment Completed: {deployment_id}")
            return deployment_result

        except Exception as e:
            error_result = {
                "success": False,
                "deployment_id": deployment_id,
                "error": str(e),
                "duration": time.time() - deployment_start,
                "timestamp": datetime.now().isoformat(),
            }

            frappe.log_error(f"Production deployment failed: {e}")
            return error_result

    def _run_pre_deployment_checks(self) -> dict:
        """Run comprehensive pre-deployment checks"""
        checks = {
            "system_resources": self._check_system_resources(),
            "database_connectivity": self._check_database_connectivity(),
            "redis_connectivity": self._check_redis_connectivity(),
            "disk_space": self._check_disk_space(),
            "arabic_locale": self._check_arabic_locale_support(),
            "ssl_certificates": self._check_ssl_certificates(),
            "backup_systems": self._check_backup_systems(),
        }

        failed_checks = [
            check for check, result in checks.items() if not result.get("success", False)
        ]

        return {
            "success": len(failed_checks) == 0,
            "checks": checks,
            "failed_checks": failed_checks,
            "message": (
                "All pre-deployment checks passed"
                if len(failed_checks) == 0
                else f'Failed checks: {", ".join(failed_checks)}'
            ),
        }

    def _check_system_resources(self) -> dict:
        """Check system resource availability"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            warnings = []
            if cpu_percent > 80:
                warnings.append("High CPU usage")
            if memory.percent > 85:
                warnings.append("High memory usage")
            if disk.percent > 90:
                warnings.append("Low disk space")

            return {
                "success": len(warnings) == 0,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "warnings": warnings,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_arabic_locale_support(self) -> dict:
        """Check Arabic locale and font support"""
        try:
            # Check system locale
            locale_result = subprocess.run(["locale", "-a"], capture_output=True, text=True)
            arabic_locales = [l for l in locale_result.stdout.split("\n") if "ar_" in l.lower()]

            # Check Arabic fonts
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/",
                "/usr/share/fonts/truetype/noto/",
                "/usr/share/fonts/TTF/",
            ]

            arabic_fonts = []
            for path in font_paths:
                if os.path.exists(path):
                    fonts = [
                        f for f in os.listdir(path) if "arabic" in f.lower() or "noto" in f.lower()
                    ]
                    arabic_fonts.extend(fonts)

            return {
                "success": len(arabic_locales) > 0 and len(arabic_fonts) > 0,
                "arabic_locales": arabic_locales,
                "arabic_fonts": arabic_fonts[:5],  # First 5 fonts
                "font_count": len(arabic_fonts),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _deploy_monitoring(self) -> dict:
        """Deploy monitoring infrastructure (Prometheus/Grafana)"""
        try:
            if not self.deployment_config["monitoring"]["prometheus"]:
                return {"success": True, "message": "Monitoring disabled in config"}

            # Create monitoring configuration
            monitoring_config = self._generate_monitoring_config()

            # Deploy Prometheus configuration
            prometheus_result = self._deploy_prometheus(monitoring_config["prometheus"])

            # Deploy Grafana configuration
            grafana_result = self._deploy_grafana(monitoring_config["grafana"])

            # Deploy alerting rules
            alerts_result = self._deploy_alerting_rules(monitoring_config["alerts"])

            return {
                "success": all(
                    [
                        prometheus_result["success"],
                        grafana_result["success"],
                        alerts_result["success"],
                    ]
                ),
                "prometheus": prometheus_result,
                "grafana": grafana_result,
                "alerts": alerts_result,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_monitoring_config(self) -> dict:
        """Generate monitoring configuration for Prometheus and Grafana"""
        return {
            "prometheus": {
                "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
                "scrape_configs": [
                    {
                        "job_name": "universal-workshop",
                        "static_configs": [{"targets": ["localhost:8000"]}],
                        "metrics_path": "/api/method/universal_workshop.utils.apm_monitor.get_metrics",
                        "scrape_interval": "30s",
                    },
                    {
                        "job_name": "node-exporter",
                        "static_configs": [{"targets": ["localhost:9100"]}],
                    },
                    {
                        "job_name": "mysql-exporter",
                        "static_configs": [{"targets": ["localhost:9104"]}],
                    },
                    {
                        "job_name": "redis-exporter",
                        "static_configs": [{"targets": ["localhost:9121"]}],
                    },
                ],
                "rule_files": ["/etc/prometheus/rules/*.yml"],
                "alerting": {
                    "alertmanagers": [{"static_configs": [{"targets": ["localhost:9093"]}]}]
                },
            },
            "grafana": {
                "dashboards": [
                    "universal-workshop-overview",
                    "arabic-performance-metrics",
                    "load-testing-results",
                    "system-health-monitoring",
                ],
                "datasources": [
                    {
                        "name": "Prometheus",
                        "type": "prometheus",
                        "url": "http://localhost:9090",
                        "access": "proxy",
                    }
                ],
            },
            "alerts": {
                "groups": [
                    {
                        "name": "universal-workshop-alerts",
                        "rules": [
                            {
                                "alert": "HighResponseTime",
                                "expr": "avg_response_time > 5000",
                                "for": "5m",
                                "labels": {"severity": "warning"},
                                "annotations": {
                                    "summary": "High response time detected",
                                    "description": "Response time is above 5 seconds",
                                },
                            },
                            {
                                "alert": "HighErrorRate",
                                "expr": "error_rate > 5",
                                "for": "2m",
                                "labels": {"severity": "critical"},
                                "annotations": {
                                    "summary": "High error rate detected",
                                    "description": "Error rate is above 5%",
                                },
                            },
                        ],
                    }
                ]
            },
        }


# WhiteListed API methods for production deployment


@frappe.whitelist()
def get_deployment_status():
    """Get current deployment status and health"""
    manager = ProductionDeploymentManager()

    return {
        "environment": manager.deployment_config["environment"],
        "version": frappe.__version__,
        "uptime": _get_system_uptime(),
        "last_deployment": _get_last_deployment_info(),
        "health_status": _get_health_status(),
        "scaling_status": _get_scaling_status(manager),
    }


@frappe.whitelist()
def trigger_deployment(version=None):
    """Trigger production deployment"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Insufficient permissions for deployment"))

    manager = ProductionDeploymentManager()
    return manager.deploy_to_production(version)


@frappe.whitelist()
def get_deployment_history(limit=10):
    """Get deployment history"""
    return frappe.get_list(
        "Deployment Record",
        fields=["name", "deployment_id", "version", "status", "timestamp", "duration"],
        order_by="timestamp desc",
        limit=limit,
    )


def _get_system_uptime():
    """Get system uptime"""
    try:
        return time.time() - psutil.boot_time()
    except:
        return 0


def _get_health_status():
    """Get overall system health status"""
    try:
        from universal_workshop.utils.apm_monitor import APMMonitor

        monitor = APMMonitor()
        return monitor.get_system_health()
    except:
        return {"status": "unknown"}
