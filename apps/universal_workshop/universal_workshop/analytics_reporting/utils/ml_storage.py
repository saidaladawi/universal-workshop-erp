"""
Production ML Model Storage System
Advanced storage, versioning, and metadata management for Universal Workshop ML models
"""

import os
import json
import hashlib
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, add_days

# ML libraries with graceful imports
try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    frappe.log_error(
        "ML libraries not available. Install joblib, scikit-learn for model persistence.",
        "ML Storage Error",
    )


class MLModelStorage:
    """Production-ready ML model storage with versioning and metadata"""

    def __init__(self):
        self.model_dir = Path(frappe.get_site_path()) / "private" / "ml_models"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.model_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

        # Initialize Redis client for usage tracking
        try:
            self.redis_client = frappe.cache()
        except Exception:
            import redis

            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=1, decode_responses=True
            )

    def save_model(
        self, model, model_type: str, version: str = None, performance_metrics: Dict = None
    ) -> str:
        """Save model with versioning and comprehensive metadata"""
        if not ML_AVAILABLE:
            frappe.throw(_("ML libraries not available for model persistence"))

        try:
            if not version:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")

            model_path = self.model_dir / f"{model_type}_v{version}.pkl"

            # Save model using joblib for efficiency
            joblib.dump(model, model_path)

            # Generate comprehensive metadata
            metadata = {
                "model_type": model_type,
                "version": version,
                "created": now_datetime().isoformat(),
                "created_by": frappe.session.user,
                "file_path": str(model_path),
                "file_size": os.path.getsize(model_path),
                "file_hash": self._get_file_hash(model_path),
                "performance_metrics": performance_metrics or {},
                "model_attributes": self._extract_model_attributes(model),
                "dependencies": self._get_dependencies_info(),
            }

            # Save metadata
            metadata_path = self.metadata_dir / f"{model_type}_v{version}_meta.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

            # Update model registry
            self._update_model_registry(model_type, version, metadata)

            frappe.logger().info(f"Model {model_type} v{version} saved successfully")
            return str(model_path)

        except Exception as e:
            frappe.log_error(f"Model save error: {str(e)}", "ML Storage Error")
            frappe.throw(_("Failed to save model: {0}").format(str(e)))

    def load_model(self, model_type: str, version: str = "latest"):
        """Load model with version support and validation"""
        if not ML_AVAILABLE:
            frappe.throw(_("ML libraries not available for model loading"))

        try:
            if version == "latest":
                version = self._get_latest_version(model_type)

            model_path = self.model_dir / f"{model_type}_v{version}.pkl"

            if not model_path.exists():
                frappe.throw(_("Model {0} version {1} not found").format(model_type, version))

            # Validate model integrity
            if not self._validate_model_integrity(model_type, version):
                frappe.throw(_("Model {0} v{1} failed integrity check").format(model_type, version))

            model = joblib.load(model_path)

            # Log model access
            self._log_model_access(model_type, version)

            return model

        except Exception as e:
            frappe.log_error(f"Model load error: {str(e)}", "ML Storage Error")
            frappe.throw(_("Failed to load model: {0}").format(str(e)))

    def list_models(self, model_type: str = None) -> List[Dict]:
        """List available models with metadata"""
        try:
            registry = self._get_model_registry()

            if model_type:
                return registry.get(model_type, [])
            else:
                all_models = []
                for mt, models in registry.items():
                    all_models.extend(models)
                return sorted(all_models, key=lambda x: x["created"], reverse=True)

        except Exception as e:
            frappe.log_error(f"Model list error: {str(e)}", "ML Storage Error")
            return []

    def delete_model(self, model_type: str, version: str) -> bool:
        """Delete model and its metadata"""
        try:
            model_path = self.model_dir / f"{model_type}_v{version}.pkl"
            metadata_path = self.metadata_dir / f"{model_type}_v{version}_meta.json"

            # Remove files
            if model_path.exists():
                os.remove(model_path)
            if metadata_path.exists():
                os.remove(metadata_path)

            # Update registry
            self._remove_from_registry(model_type, version)

            frappe.logger().info(f"Model {model_type} v{version} deleted successfully")
            return True

        except Exception as e:
            frappe.log_error(f"Model delete error: {str(e)}", "ML Storage Error")
            return False

    def cleanup_old_models(self, model_type: str, keep_versions: int = 5) -> int:
        """Clean up old model versions, keeping specified number of recent versions"""
        try:
            models = self.list_models(model_type)
            if len(models) <= keep_versions:
                return 0

            # Sort by creation date and keep only the most recent
            models_sorted = sorted(models, key=lambda x: x["created"], reverse=True)
            models_to_delete = models_sorted[keep_versions:]

            deleted_count = 0
            for model in models_to_delete:
                if self.delete_model(model_type, model["version"]):
                    deleted_count += 1

            frappe.logger().info(f"Cleaned up {deleted_count} old models for {model_type}")
            return deleted_count

        except Exception as e:
            frappe.log_error(f"Model cleanup error: {str(e)}", "ML Storage Error")
            return 0

    def get_model_performance(self, model_type: str, version: str = "latest") -> Dict:
        """Get model performance metrics"""
        try:
            if version == "latest":
                version = self._get_latest_version(model_type)

            metadata_path = self.metadata_dir / f"{model_type}_v{version}_meta.json"

            if not metadata_path.exists():
                return {}

            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            return metadata.get("performance_metrics", {})

        except Exception as e:
            frappe.log_error(f"Performance retrieval error: {str(e)}", "ML Storage Error")
            return {}

    def track_model_usage(
        self, model_type: str, version: str, prediction_time: float, accuracy: float = None
    ) -> None:
        """Track model usage with Redis caching and database logging"""
        try:
            # Track in Redis for real-time monitoring
            usage_key = f"ml_usage:{model_type}:{version}"

            # Update usage statistics in Redis
            self.redis_client.hincrby(usage_key, "total_predictions", 1)
            self.redis_client.hset(usage_key, "last_used", now_datetime().isoformat())

            # Track prediction time statistics
            if prediction_time:
                current_avg = float(self.redis_client.hget(usage_key, "avg_prediction_time") or 0)
                current_count = int(self.redis_client.hget(usage_key, "total_predictions") or 1)

                # Calculate rolling average
                new_avg = ((current_avg * (current_count - 1)) + prediction_time) / current_count
                self.redis_client.hset(usage_key, "avg_prediction_time", new_avg)

                # Track min/max prediction times
                current_min = float(
                    self.redis_client.hget(usage_key, "min_prediction_time") or prediction_time
                )
                current_max = float(
                    self.redis_client.hget(usage_key, "max_prediction_time") or prediction_time
                )

                if prediction_time < current_min:
                    self.redis_client.hset(usage_key, "min_prediction_time", prediction_time)
                if prediction_time > current_max:
                    self.redis_client.hset(usage_key, "max_prediction_time", prediction_time)

            # Track accuracy if provided
            if accuracy is not None:
                self.redis_client.hset(usage_key, "last_accuracy", accuracy)

                # Update accuracy history
                accuracy_history_key = f"ml_accuracy_history:{model_type}:{version}"
                self.redis_client.lpush(accuracy_history_key, accuracy)
                self.redis_client.ltrim(
                    accuracy_history_key, 0, 99
                )  # Keep last 100 accuracy scores

            # Set expiry for Redis keys (24 hours)
            self.redis_client.expire(usage_key, 86400)

            # Log to database for persistent tracking
            usage_data = {
                "model_type": model_type,
                "model_version": version,
                "prediction_time": prediction_time,
                "accuracy": accuracy,
                "user": frappe.session.user,
                "session_id": (
                    frappe.local.session.sid if hasattr(frappe.local, "session") else None
                ),
                "timestamp": now_datetime(),
            }

            self._log_model_usage_to_db(model_type, version, usage_data)

        except Exception as e:
            frappe.log_error(f"Model usage tracking failed: {str(e)}", "ML Usage Tracking Error")

    def _log_model_usage_to_db(self, model_type: str, version: str, usage_data: Dict):
        """Log model usage to database via ML Model Usage Log DocType"""
        try:
            # Create ML Model Usage Log entry
            usage_log = frappe.new_doc("ML Model Usage Log")
            usage_log.model_type = model_type
            usage_log.model_version = version
            usage_log.prediction_time = usage_data.get("prediction_time", 0)
            usage_log.accuracy = usage_data.get("accuracy")
            usage_log.user = usage_data.get("user", frappe.session.user)
            usage_log.session_id = usage_data.get("session_id")
            usage_log.timestamp = usage_data.get("timestamp", now_datetime())

            # Insert without triggering user permission checks
            usage_log.flags.ignore_permissions = True
            usage_log.insert()

        except Exception as e:
            # Don't fail the main operation if logging fails
            frappe.log_error(f"ML usage DB logging failed: {str(e)}", "ML Usage DB Error")

    def auto_retrain_check(self, model_type: str) -> Dict[str, Any]:
        """Check if model needs retraining based on performance degradation"""
        try:
            # Get recent usage statistics
            recent_stats = self._get_recent_usage_stats(model_type, days=7)

            # Get model performance history
            performance_history = self._get_performance_history(model_type, days=30)

            # Calculate performance degradation
            performance_trend = self._analyze_performance_trend(performance_history)

            # Determine if retraining is needed
            needs_retraining = False
            reasons = []

            # Check accuracy degradation (>10% decline)
            if performance_trend.get("accuracy_decline", 0) > 0.1:
                needs_retraining = True
                reasons.append(
                    "Accuracy declined by {:.1%}".format(performance_trend["accuracy_decline"])
                )

            # Check prediction time increase (>50% slower)
            if performance_trend.get("time_increase", 0) > 0.5:
                needs_retraining = True
                reasons.append(
                    "Prediction time increased by {:.1%}".format(performance_trend["time_increase"])
                )

            # Check if model hasn't been retrained in 30 days
            last_retrain = self._get_last_retrain_date(model_type)
            days_since_retrain = (now_datetime() - last_retrain).days if last_retrain else 999

            if days_since_retrain > 30:
                needs_retraining = True
                reasons.append(f"Model not retrained in {days_since_retrain} days")

            # Check usage volume for statistical significance
            min_predictions_for_retrain = 100
            if recent_stats.get("total_predictions", 0) < min_predictions_for_retrain:
                if needs_retraining:
                    needs_retraining = False
                    reasons.append(
                        "Insufficient prediction volume for reliable retraining assessment"
                    )

            return {
                "model_type": model_type,
                "needs_retraining": needs_retraining,
                "reasons": reasons,
                "current_performance": recent_stats,
                "performance_trend": performance_trend,
                "last_retrain_date": last_retrain.isoformat() if last_retrain else None,
                "days_since_retrain": days_since_retrain,
                "recommendation": (
                    "Schedule retraining" if needs_retraining else "Continue monitoring"
                ),
                "checked_at": now_datetime().isoformat(),
            }

        except Exception as e:
            frappe.log_error(f"Auto retrain check failed: {str(e)}", "ML Auto Retrain Error")
            return {
                "model_type": model_type,
                "needs_retraining": False,
                "error": str(e),
                "checked_at": now_datetime().isoformat(),
            }

    def _get_recent_usage_stats(self, model_type: str, days: int = 7) -> Dict[str, float]:
        """Get recent usage statistics for model performance analysis"""
        try:
            # Query ML Model Usage Log for recent statistics
            recent_logs = frappe.db.sql(
                """
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(prediction_time) as avg_prediction_time,
                    MIN(prediction_time) as min_prediction_time,
                    MAX(prediction_time) as max_prediction_time,
                    AVG(accuracy) as avg_accuracy,
                    STDDEV(prediction_time) as prediction_time_std,
                    STDDEV(accuracy) as accuracy_std
                FROM `tabML Model Usage Log`
                WHERE model_type = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND accuracy IS NOT NULL
            """,
                [model_type, days],
                as_dict=True,
            )

            if recent_logs and recent_logs[0]["total_predictions"]:
                stats = recent_logs[0]

                # Calculate custom standard deviation if MySQL STDDEV not available
                if not stats.get("prediction_time_std"):
                    time_data = frappe.db.sql(
                        """
                        SELECT prediction_time 
                        FROM `tabML Model Usage Log`
                        WHERE model_type = %s 
                        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        AND prediction_time IS NOT NULL
                    """,
                        [model_type, days],
                        as_list=True,
                    )

                    if time_data:
                        times = [row[0] for row in time_data]
                        stats["prediction_time_std"] = self._calculate_std(times)

                return {
                    "total_predictions": int(stats["total_predictions"] or 0),
                    "avg_prediction_time": float(stats["avg_prediction_time"] or 0),
                    "min_prediction_time": float(stats["min_prediction_time"] or 0),
                    "max_prediction_time": float(stats["max_prediction_time"] or 0),
                    "avg_accuracy": float(stats["avg_accuracy"] or 0),
                    "prediction_time_std": float(stats["prediction_time_std"] or 0),
                    "accuracy_std": float(stats["accuracy_std"] or 0),
                }
            else:
                return {"total_predictions": 0}

        except Exception as e:
            frappe.log_error(f"Usage stats calculation failed: {str(e)}", "ML Usage Stats Error")
            return {"total_predictions": 0, "error": str(e)}

    def create_model_backup(self, model_type: str, version: str = "latest") -> str:
        """Create backup of model and metadata for disaster recovery"""
        try:
            if version == "latest":
                version = self._get_latest_version(model_type)

            backup_dir = self.model_dir / "backups" / f"{model_type}_v{version}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy model file
            model_path = self.model_dir / f"{model_type}_v{version}.pkl"
            backup_model_path = backup_dir / f"{model_type}_v{version}.pkl"

            if model_path.exists():
                import shutil

                shutil.copy2(model_path, backup_model_path)

            # Copy metadata
            metadata_path = self.metadata_dir / f"{model_type}_v{version}_meta.json"
            backup_metadata_path = backup_dir / f"{model_type}_v{version}_meta.json"

            if metadata_path.exists():
                import shutil

                shutil.copy2(metadata_path, backup_metadata_path)

            # Create backup manifest
            manifest = {
                "backup_date": now_datetime().isoformat(),
                "model_type": model_type,
                "model_version": version,
                "files": [str(backup_model_path), str(backup_metadata_path)],
                "created_by": frappe.session.user,
            }

            manifest_path = backup_dir / "backup_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, default=str)

            frappe.logger().info(f"Model backup created: {backup_dir}")
            return str(backup_dir)

        except Exception as e:
            frappe.log_error(f"Model backup error: {str(e)}", "ML Storage Error")
            frappe.throw(_("Failed to create model backup: {0}").format(str(e)))

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity checking"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_latest_version(self, model_type: str) -> str:
        """Get latest model version"""
        model_files = list(self.model_dir.glob(f"{model_type}_v*.pkl"))
        if not model_files:
            frappe.throw(_("No models found for type {0}").format(model_type))

        # Sort by creation time
        latest_file = max(model_files, key=lambda x: x.stat().st_mtime)
        return latest_file.stem.split("_v")[1]

    def _extract_model_attributes(self, model) -> Dict:
        """Extract model attributes and parameters"""
        try:
            attributes = {
                "model_class": model.__class__.__name__,
                "model_module": model.__class__.__module__,
            }

            # Extract sklearn model parameters
            if hasattr(model, "get_params"):
                attributes["parameters"] = model.get_params()

            # Extract feature information
            if hasattr(model, "feature_names_in_"):
                attributes["feature_names"] = model.feature_names_in_.tolist()
            if hasattr(model, "n_features_in_"):
                attributes["n_features"] = model.n_features_in_

            return attributes

        except Exception as e:
            frappe.logger().warning(f"Could not extract model attributes: {str(e)}")
            return {}

    def _get_dependencies_info(self) -> Dict:
        """Get information about ML dependencies"""
        try:
            import sklearn
            import numpy
            import pandas
            import joblib

            return {
                "sklearn_version": sklearn.__version__,
                "numpy_version": numpy.__version__,
                "pandas_version": pandas.__version__,
                "joblib_version": joblib.__version__,
                "python_version": frappe.local.conf.get("python_version", "unknown"),
            }
        except Exception:
            return {}

    def _update_model_registry(self, model_type: str, version: str, metadata: Dict):
        """Update the model registry"""
        try:
            registry_path = self.metadata_dir / "model_registry.json"

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
            else:
                registry = {}

            if model_type not in registry:
                registry[model_type] = []

            # Add new model info
            model_info = {
                "version": version,
                "created": metadata["created"],
                "created_by": metadata["created_by"],
                "file_size": metadata["file_size"],
                "performance": metadata.get("performance_metrics", {}),
            }

            registry[model_type].append(model_info)

            # Sort by creation date
            registry[model_type] = sorted(
                registry[model_type], key=lambda x: x["created"], reverse=True
            )

            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, default=str)

        except Exception as e:
            frappe.logger().warning(f"Could not update model registry: {str(e)}")

    def _get_model_registry(self) -> Dict:
        """Get the model registry"""
        try:
            registry_path = self.metadata_dir / "model_registry.json"

            if not registry_path.exists():
                return {}

            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            frappe.logger().warning(f"Could not read model registry: {str(e)}")
            return {}

    def _remove_from_registry(self, model_type: str, version: str):
        """Remove model from registry"""
        try:
            registry = self._get_model_registry()

            if model_type in registry:
                registry[model_type] = [m for m in registry[model_type] if m["version"] != version]

                registry_path = self.metadata_dir / "model_registry.json"
                with open(registry_path, "w", encoding="utf-8") as f:
                    json.dump(registry, f, indent=2, default=str)

        except Exception as e:
            frappe.logger().warning(f"Could not update registry after deletion: {str(e)}")

    def _validate_model_integrity(self, model_type: str, version: str) -> bool:
        """Validate model file integrity using stored hash"""
        try:
            model_path = self.model_dir / f"{model_type}_v{version}.pkl"
            metadata_path = self.metadata_dir / f"{model_type}_v{version}_meta.json"

            if not metadata_path.exists():
                return True  # No metadata to validate against

            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            stored_hash = metadata.get("file_hash")
            if not stored_hash:
                return True  # No hash to validate against

            current_hash = self._get_file_hash(model_path)
            return stored_hash == current_hash

        except Exception as e:
            frappe.logger().warning(f"Model integrity check failed: {str(e)}")
            return False

    def _log_model_access(self, model_type: str, version: str):
        """Log model access for monitoring"""
        try:
            access_log = {
                "model_type": model_type,
                "version": version,
                "accessed_by": frappe.session.user,
                "accessed_at": now_datetime().isoformat(),
                "ip_address": (
                    frappe.local.request.environ.get("REMOTE_ADDR")
                    if frappe.local.request
                    else None
                ),
            }

            log_path = self.metadata_dir / "access_log.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(access_log, default=str) + "\n")

        except Exception as e:
            frappe.logger().warning(f"Could not log model access: {str(e)}")

    def _calculate_std(self, data: List[float]) -> float:
        """Calculate standard deviation of a list of numbers"""
        if len(data) <= 1:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)

    def _get_performance_history(self, model_type: str, days: int = 30) -> List[Dict]:
        """Get model performance history for trend analysis"""
        try:
            history = frappe.db.sql(
                """
                SELECT 
                    DATE(timestamp) as date,
                    AVG(accuracy) as avg_accuracy,
                    AVG(prediction_time) as avg_prediction_time,
                    COUNT(*) as prediction_count
                FROM `tabML Model Usage Log`
                WHERE model_type = %s
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND accuracy IS NOT NULL
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                [model_type, days],
                as_dict=True,
            )

            return history

        except Exception as e:
            frappe.log_error(f"Performance history error: {str(e)}", "ML Storage Error")
            return []

    def _analyze_performance_trend(self, performance_history: List[Dict]) -> Dict[str, float]:
        """Analyze performance trends to detect degradation"""
        try:
            if len(performance_history) < 2:
                return {"accuracy_decline": 0, "time_increase": 0}

            # Split data into early and recent periods
            mid_point = len(performance_history) // 2
            early_period = performance_history[:mid_point]
            recent_period = performance_history[mid_point:]

            # Calculate average metrics for each period
            early_accuracy = sum(
                p["avg_accuracy"] for p in early_period if p["avg_accuracy"]
            ) / len(early_period)
            recent_accuracy = sum(
                p["avg_accuracy"] for p in recent_period if p["avg_accuracy"]
            ) / len(recent_period)

            early_time = sum(p["avg_prediction_time"] for p in early_period) / len(early_period)
            recent_time = sum(p["avg_prediction_time"] for p in recent_period) / len(recent_period)

            # Calculate degradation metrics
            accuracy_decline = (
                (early_accuracy - recent_accuracy) / early_accuracy if early_accuracy > 0 else 0
            )
            time_increase = (recent_time - early_time) / early_time if early_time > 0 else 0

            return {
                "accuracy_decline": max(0, accuracy_decline),  # Only count decline
                "time_increase": max(0, time_increase),  # Only count increase
                "early_accuracy": early_accuracy,
                "recent_accuracy": recent_accuracy,
                "early_time": early_time,
                "recent_time": recent_time,
            }

        except Exception as e:
            frappe.log_error(f"Performance trend analysis error: {str(e)}", "ML Storage Error")
            return {"accuracy_decline": 0, "time_increase": 0}

    def _get_last_retrain_date(self, model_type: str) -> Optional[datetime]:
        """Get the date when model was last retrained"""
        try:
            # Check model registry for latest model creation date
            registry = self._get_model_registry()

            if model_type in registry and registry[model_type]:
                # Get the most recent model version
                latest_model = max(registry[model_type], key=lambda x: x["created"])
                return get_datetime(latest_model["created"])

            return None

        except Exception as e:
            frappe.log_error(f"Last retrain date error: {str(e)}", "ML Storage Error")
            return None

    def schedule_auto_retrain(self, model_type: str) -> Dict[str, Any]:
        """Schedule automatic model retraining based on performance analysis"""
        try:
            retrain_check = self.auto_retrain_check(model_type)

            if not retrain_check.get("needs_retraining"):
                return {
                    "scheduled": False,
                    "reason": "Retraining not needed",
                    "check_results": retrain_check,
                }

            # Create background job for retraining
            job_name = f"retrain_model_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            frappe.enqueue(
                method="universal_workshop.analytics_reporting.utils.ml_engine.retrain_model_background",
                queue="long",
                timeout=3600,  # 1 hour timeout
                job_name=job_name,
                model_type=model_type,
                trigger_reason=retrain_check.get("reasons", []),
                scheduled_by=frappe.session.user,
            )

            # Log the scheduling
            frappe.logger().info(f"Scheduled retraining for model {model_type}: {job_name}")

            return {
                "scheduled": True,
                "job_name": job_name,
                "reasons": retrain_check.get("reasons", []),
                "check_results": retrain_check,
            }

        except Exception as e:
            frappe.log_error(f"Auto retrain scheduling error: {str(e)}", "ML Storage Error")
            return {"scheduled": False, "error": str(e)}

    def get_redis_usage_stats(self, model_type: str, version: str = None) -> Dict[str, Any]:
        """Get real-time usage statistics from Redis"""
        try:
            if version:
                usage_key = f"ml_usage:{model_type}:{version}"
                stats = self.redis_client.hgetall(usage_key)
            else:
                # Get stats for all versions of this model type
                pattern = f"ml_usage:{model_type}:*"
                keys = self.redis_client.keys(pattern)

                if not keys:
                    return {"error": "No usage data found in Redis"}

                # Aggregate stats from all versions
                total_predictions = 0
                total_avg_time = 0
                versions = []

                for key in keys:
                    version_stats = self.redis_client.hgetall(key)
                    if version_stats:
                        versions.append({"version": key.split(":")[-1], "stats": version_stats})
                        total_predictions += int(version_stats.get("total_predictions", 0))
                        total_avg_time += float(version_stats.get("avg_prediction_time", 0))

                return {
                    "model_type": model_type,
                    "total_predictions": total_predictions,
                    "avg_prediction_time": total_avg_time / len(versions) if versions else 0,
                    "active_versions": len(versions),
                    "version_breakdown": versions,
                }

            if stats:
                return {
                    "model_type": model_type,
                    "version": version,
                    "total_predictions": int(stats.get("total_predictions", 0)),
                    "avg_prediction_time": float(stats.get("avg_prediction_time", 0)),
                    "min_prediction_time": float(stats.get("min_prediction_time", 0)),
                    "max_prediction_time": float(stats.get("max_prediction_time", 0)),
                    "last_used": stats.get("last_used"),
                    "last_accuracy": (
                        float(stats.get("last_accuracy", 0)) if stats.get("last_accuracy") else None
                    ),
                }
            else:
                return {"error": "No Redis data found for this model"}

        except Exception as e:
            frappe.log_error(f"Redis usage stats error: {str(e)}", "ML Storage Error")
            return {"error": str(e)}


# Whitelisted API methods
@frappe.whitelist()
def list_available_models(model_type=None):
    """API endpoint to list available models"""
    storage = MLModelStorage()
    return storage.list_models(model_type)


@frappe.whitelist()
def get_model_info(model_type, version="latest"):
    """API endpoint to get model information"""
    storage = MLModelStorage()
    return storage.get_model_performance(model_type, version)


@frappe.whitelist()
def cleanup_models(model_type, keep_versions=5):
    """API endpoint to cleanup old models"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions"))

    storage = MLModelStorage()
    deleted_count = storage.cleanup_old_models(model_type, int(keep_versions))

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": _("Cleaned up {0} old model versions").format(deleted_count),
    }


@frappe.whitelist()
def schedule_model_retrain(model_type: str):
    """API method to schedule model retraining"""
    storage = MLModelStorage()
    return storage.schedule_auto_retrain(model_type)


@frappe.whitelist()
def get_redis_model_stats(model_type: str, version: str = None):
    """Get real-time model usage stats from Redis"""
    storage = MLModelStorage()
    return storage.get_redis_usage_stats(model_type, version)


@frappe.whitelist()
def check_all_models_retrain_status():
    """Check retraining status for all models"""
    try:
        storage = MLModelStorage()

        # Get all unique model types
        model_types = frappe.db.sql(
            """
            SELECT DISTINCT model_type 
            FROM `tabML Model Usage Log`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """,
            as_list=True,
        )

        results = []
        for model_type_row in model_types:
            model_type = model_type_row[0]
            check_result = storage.auto_retrain_check(model_type)
            check_result["model_type"] = model_type
            results.append(check_result)

        return {
            "models_checked": len(results),
            "models_needing_retrain": len([r for r in results if r.get("needs_retraining")]),
            "results": results,
            "checked_at": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"All models retrain check error: {str(e)}", "ML Storage Error")
        return {"error": str(e)}


# ✅ ADD: Scheduled task for Redis usage stats update
def update_redis_usage_stats():
    """
    Scheduled task to update Redis usage stats and clean up expired keys
    Called hourly to maintain performance and consistency
    """
    try:
        storage = MLModelStorage()

        # Get all active model types from recent usage
        model_types = frappe.db.sql(
            """
            SELECT DISTINCT model_type 
            FROM `tabML Model Usage Log`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """,
            as_list=True,
        )

        updated_count = 0
        for model_type_row in model_types:
            model_type = model_type_row[0]

            try:
                # Get latest database stats for this model type
                db_stats = storage._get_recent_usage_stats(model_type, days=1)

                if db_stats and db_stats.get("total_predictions", 0) > 0:
                    # Update Redis with latest aggregated stats
                    redis_key = f"ml_usage_aggregated:{model_type}"

                    storage.redis_client.hset(
                        redis_key,
                        {
                            "total_predictions": db_stats.get("total_predictions", 0),
                            "avg_prediction_time": db_stats.get("avg_prediction_time", 0),
                            "min_prediction_time": db_stats.get("min_prediction_time", 0),
                            "max_prediction_time": db_stats.get("max_prediction_time", 0),
                            "avg_accuracy": db_stats.get("avg_accuracy", 0),
                            "last_updated": now_datetime().isoformat(),
                        },
                    )

                    # Set expiry for 48 hours
                    storage.redis_client.expire(redis_key, 48 * 3600)
                    updated_count += 1

            except Exception as e:
                frappe.log_error(
                    f"Redis update error for model {model_type}: {str(e)}", "Redis Update Error"
                )
                continue

        # Clean up expired prediction-level keys (older than 24 hours)
        try:
            pattern = "ml_usage:*"
            keys = storage.redis_client.keys(pattern)
            cleaned_count = 0

            for key in keys:
                # Check if key is older than 24 hours based on last_used timestamp
                last_used = storage.redis_client.hget(key, "last_used")
                if last_used:
                    try:
                        last_used_dt = get_datetime(last_used)
                        if (now_datetime() - last_used_dt).total_seconds() > 24 * 3600:
                            storage.redis_client.delete(key)
                            cleaned_count += 1
                    except Exception:
                        # If can't parse date, delete the key
                        storage.redis_client.delete(key)
                        cleaned_count += 1

            frappe.logger().info(
                f"Redis maintenance: Updated {updated_count} models, cleaned {cleaned_count} expired keys"
            )

        except Exception as e:
            frappe.log_error(f"Redis cleanup error: {str(e)}", "Redis Cleanup Error")

        return {
            "success": True,
            "models_updated": updated_count,
            "keys_cleaned": cleaned_count,
            "updated_at": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Redis usage stats update error: {str(e)}", "Redis Update Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_ml_system_status():
    """Get comprehensive ML system status for monitoring dashboard"""
    try:
        storage = MLModelStorage()

        # Get basic system stats
        total_models = len(storage.list_models())

        # Get usage stats from last 24 hours
        recent_usage = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(DISTINCT model_type) as active_models,
                COUNT(DISTINCT user) as active_users,
                AVG(prediction_time) as avg_response_time
            FROM `tabML Model Usage Log`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """,
            as_dict=True,
        )

        usage_stats = recent_usage[0] if recent_usage else {}

        # Check Redis health
        redis_health = True
        redis_keys_count = 0
        try:
            redis_keys_count = len(storage.redis_client.keys("ml_usage*"))
        except Exception:
            redis_health = False

        # Get retraining status
        models_needing_retrain = 0
        try:
            retrain_check = check_all_models_retrain_status()
            models_needing_retrain = retrain_check.get("models_needing_retrain", 0)
        except Exception:
            pass

        return {
            "system_status": "healthy" if redis_health else "degraded",
            "total_models": total_models,
            "redis_health": redis_health,
            "redis_keys": redis_keys_count,
            "models_needing_retrain": models_needing_retrain,
            "last_24h_stats": {
                "total_predictions": usage_stats.get("total_predictions", 0),
                "active_models": usage_stats.get("active_models", 0),
                "active_users": usage_stats.get("active_users", 0),
                "avg_response_time": round(usage_stats.get("avg_response_time", 0), 3),
            },
            "checked_at": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"ML system status error: {str(e)}", "ML System Status Error")
        return {"system_status": "error", "error": str(e)}


# Initialize storage instance for global access
storage = MLModelStorage()
