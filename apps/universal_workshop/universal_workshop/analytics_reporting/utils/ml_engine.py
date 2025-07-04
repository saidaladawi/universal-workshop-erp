"""
Machine Learning Engine
Core ML functionality for Universal Workshop predictive analytics
"""

import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_days, get_datetime, now_datetime

# Configure logging
logger = logging.getLogger(__name__)


class MLEngine:
    """Core machine learning engine for Universal Workshop"""

    def __init__(self):
        self.models = {}
        self.data_cache = {}

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if ML dependencies are installed"""
        deps = {"pandas": False, "scikit_learn": False, "numpy": False}

        try:
            import pandas

            deps["pandas"] = True
        except ImportError:
            pass

        try:
            import sklearn

            deps["scikit_learn"] = True
        except ImportError:
            pass

        try:
            import numpy

            deps["numpy"] = True
        except ImportError:
            pass

        return deps

    def extract_data_for_model(self, model_doc: Dict) -> Dict[str, Any]:
        """Extract training data based on model configuration"""
        try:
            data_sources = json.loads(model_doc.get("data_sources", "[]"))
            prediction_type = model_doc.get("prediction_type")
            target_metric = model_doc.get("target_metric")

            if prediction_type == "Time Series Forecast":
                return self._extract_time_series_data(data_sources, target_metric)
            elif prediction_type == "Regression":
                return self._extract_regression_data(data_sources, target_metric)
            else:
                return self._extract_classification_data(data_sources, target_metric)

        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return {"features": [], "target": [], "error": str(e)}

    def _extract_time_series_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract time series data for forecasting"""
        data = {"features": [], "target": [], "dates": []}

        try:
            # Extract revenue data from Sales Invoice
            if "Sales Invoice" in data_sources and target_metric == "Revenue":
                revenue_data = frappe.db.sql(
                    """
                    SELECT 
                        DATE(posting_date) as date,
                        SUM(grand_total) as revenue,
                        COUNT(*) as invoice_count
                    FROM `tabSales Invoice`
                    WHERE docstatus = 1
                    AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                    GROUP BY DATE(posting_date)
                    ORDER BY date
                """,
                    as_dict=True,
                )

                for row in revenue_data:
                    data["dates"].append(row["date"])
                    data["target"].append(flt(row["revenue"]))
                    data["features"].append(
                        [
                            flt(row["revenue"]),
                            cint(row["invoice_count"]),
                            row["date"].weekday(),  # Day of week
                            row["date"].day,  # Day of month
                            row["date"].month,  # Month
                        ]
                    )

            # Extract service order data
            if "Service Order" in data_sources:
                service_data = frappe.db.sql(
                    """
                    SELECT 
                        DATE(creation) as date,
                        COUNT(*) as order_count,
                        AVG(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completion_rate
                    FROM `tabService Order`
                    WHERE creation >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                    GROUP BY DATE(creation)
                    ORDER BY date
                """,
                    as_dict=True,
                )

                # Merge with existing data or create new if no revenue data
                if not data["features"]:
                    for row in service_data:
                        data["dates"].append(row["date"])
                        data["target"].append(flt(row["order_count"]))
                        data["features"].append(
                            [
                                flt(row["order_count"]),
                                flt(row["completion_rate"]),
                                row["date"].weekday(),
                                row["date"].day,
                                row["date"].month,
                            ]
                        )

        except Exception as e:
            logger.error(f"Time series extraction error: {str(e)}")
            data["error"] = str(e)

        return data

    def _extract_regression_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract regression data for continuous predictions"""
        data = {"features": [], "target": []}

        try:
            # Customer satisfaction regression
            if target_metric == "Customer Satisfaction":
                customer_data = frappe.db.sql(
                    """
                    SELECT 
                        c.name,
                        COUNT(DISTINCT so.name) as total_orders,
                        AVG(so.total_amount) as avg_order_value,
                        AVG(DATEDIFF(so.completion_date, so.creation)) as avg_service_time,
                        (SELECT COUNT(*) FROM `tabCustomer Feedback` 
                         WHERE customer = c.name AND rating >= 4) as positive_feedback
                    FROM `tabCustomer` c
                    LEFT JOIN `tabService Order` so ON so.customer = c.name
                    WHERE c.disabled = 0
                    GROUP BY c.name
                    HAVING total_orders > 0
                """,
                    as_dict=True,
                )

                for row in customer_data:
                    data["features"].append(
                        [
                            flt(row["total_orders"]),
                            flt(row["avg_order_value"]),
                            flt(row["avg_service_time"]),
                        ]
                    )
                    data["target"].append(flt(row["positive_feedback"]))

        except Exception as e:
            logger.error(f"Regression extraction error: {str(e)}")
            data["error"] = str(e)

        return data

    def _extract_classification_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract classification data for categorical predictions"""
        data = {"features": [], "target": []}

        try:
            # Vehicle maintenance classification
            if "Vehicle" in data_sources and target_metric == "Maintenance Risk":
                vehicle_data = frappe.db.sql(
                    """
                    SELECT 
                        v.name,
                        v.year,
                        v.mileage,
                        COUNT(so.name) as service_count,
                        DATEDIFF(CURDATE(), MAX(so.completion_date)) as days_since_service,
                        CASE 
                            WHEN DATEDIFF(CURDATE(), MAX(so.completion_date)) > 180 THEN 'High'
                            WHEN DATEDIFF(CURDATE(), MAX(so.completion_date)) > 90 THEN 'Medium'
                            ELSE 'Low'
                        END as risk_level
                    FROM `tabVehicle` v
                    LEFT JOIN `tabService Order` so ON so.vehicle = v.name
                    WHERE v.status = 'Active'
                    GROUP BY v.name
                """,
                    as_dict=True,
                )

                for row in vehicle_data:
                    current_year = datetime.now().year
                    vehicle_age = current_year - cint(row["year"])

                    data["features"].append(
                        [
                            vehicle_age,
                            flt(row["mileage"]),
                            cint(row["service_count"]),
                            cint(row["days_since_service"]),
                        ]
                    )
                    data["target"].append(row["risk_level"])

        except Exception as e:
            logger.error(f"Classification extraction error: {str(e)}")
            data["error"] = str(e)

        return data

    def train_model(self, model_doc: Dict) -> Dict[str, Any]:
        """Train ML model based on configuration"""
        deps = self.check_dependencies()
        if not all(deps.values()):
            return {
                "status": "error",
                "message": _("Missing ML dependencies: {0}").format(
                    ", ".join([k for k, v in deps.items() if not v])
                ),
            }

        try:
            # Import ML libraries
            import pandas as pd
            import numpy as np
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, mean_squared_error, r2_score

            # Extract training data
            training_data = self.extract_data_for_model(model_doc)

            if "error" in training_data:
                return {"status": "error", "message": training_data["error"]}

            if not training_data["features"] or not training_data["target"]:
                return {"status": "error", "message": _("No training data available")}

            # Prepare data
            X = np.array(training_data["features"])
            y = np.array(training_data["target"])

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Train model based on algorithm type
            model, score = self._train_algorithm(
                model_doc.get("algorithm_type"),
                model_doc.get("model_parameters"),
                X_train,
                X_test,
                y_train,
                y_test,
            )

            if model is None:
                return {"status": "error", "message": _("Model training failed")}

            # Store model (in production, save to file system)
            self.models[model_doc.get("name")] = {
                "model": model,
                "features_count": X.shape[1],
                "trained_date": datetime.now(),
                "accuracy": score,
            }

            return {
                "status": "success",
                "accuracy": score,
                "features_count": X.shape[1],
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            }

        except Exception as e:
            logger.error(f"Model training error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _train_algorithm(
        self, algorithm_type: str, parameters: str, X_train, X_test, y_train, y_test
    ) -> Tuple[Any, float]:
        """Train specific ML algorithm"""
        try:
            params = json.loads(parameters) if parameters else {}

            if algorithm_type == "Random Forest":
                from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

                # Determine if classification or regression
                if isinstance(y_train[0], str):
                    from sklearn.preprocessing import LabelEncoder

                    le = LabelEncoder()
                    y_train_encoded = le.fit_transform(y_train)
                    y_test_encoded = le.transform(y_test)

                    model = RandomForestClassifier(**params)
                    model.fit(X_train, y_train_encoded)
                    predictions = model.predict(X_test)
                    score = accuracy_score(y_test_encoded, predictions) * 100
                else:
                    model = RandomForestRegressor(**params)
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_test)
                    score = r2_score(y_test, predictions) * 100

            elif algorithm_type == "Gradient Boosting":
                from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier

                if isinstance(y_train[0], str):
                    le = LabelEncoder()
                    y_train_encoded = le.fit_transform(y_train)
                    y_test_encoded = le.transform(y_test)

                    model = GradientBoostingClassifier(**params)
                    model.fit(X_train, y_train_encoded)
                    predictions = model.predict(X_test)
                    score = accuracy_score(y_test_encoded, predictions) * 100
                else:
                    model = GradientBoostingRegressor(**params)
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_test)
                    score = r2_score(y_test, predictions) * 100

            else:
                return None, 0

            return model, score

        except Exception as e:
            logger.error(f"Algorithm training error: {str(e)}")
            return None, 0

    def generate_predictions(self, model_doc: Dict, horizon_days: int = None) -> Dict[str, Any]:
        """Generate predictions using trained model"""
        try:
            model_name = model_doc.get("name")

            if model_name not in self.models:
                return {"status": "error", "message": _("Model not trained")}

            model_info = self.models[model_name]
            model = model_info["model"]

            # Generate prediction data based on model type
            prediction_type = model_doc.get("prediction_type")

            if prediction_type == "Time Series Forecast":
                return self._generate_time_series_predictions(
                    model, model_doc, horizon_days or model_doc.get("prediction_horizon_days", 30)
                )
            else:
                return self._generate_standard_predictions(model, model_doc)

        except Exception as e:
            logger.error(f"Prediction generation error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _generate_time_series_predictions(self, model, model_doc: Dict, horizon_days: int) -> Dict:
        """Generate time series predictions"""
        predictions = []

        try:

            # Get recent data for prediction base
            base_date = datetime.now().date()

            for i in range(horizon_days):
                pred_date = base_date + timedelta(days=i + 1)

                # Create feature vector for prediction
                features = [
                    0,  # Placeholder values - in production, use actual features
                    0,
                    pred_date.weekday(),
                    pred_date.day,
                    pred_date.month,
                ]

                pred_value = model.predict([features])[0]

                predictions.append(
                    {
                        "date": pred_date.isoformat(),
                        "predicted_value": float(pred_value),
                        "confidence": 0.8,  # Placeholder confidence
                    }
                )

            return {"status": "success", "predictions": predictions, "horizon_days": horizon_days}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _generate_standard_predictions(self, model, model_doc: Dict) -> Dict:
        """Generate standard predictions for classification/regression"""
        try:
            # In production, this would use actual data to predict
            # For now, return sample predictions
            return {
                "status": "success",
                "predictions": [
                    {"item": "Sample Item 1", "predicted_value": "High Risk", "confidence": 0.85}
                ],
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global ML engine instance
ml_engine = MLEngine()


@frappe.whitelist()
def check_ml_dependencies():
    """Check ML dependencies via API"""
    return ml_engine.check_dependencies()


@frappe.whitelist()
def train_predictive_model(model_name):
    """Train a predictive model via API"""
    model_doc = frappe.get_doc("Predictive Model", model_name)
    return ml_engine.train_model(model_doc.as_dict())


@frappe.whitelist()
def generate_model_predictions(model_name, horizon_days=None):
    """Generate predictions via API"""
    model_doc = frappe.get_doc("Predictive Model", model_name)
    return ml_engine.generate_predictions(model_doc.as_dict(), horizon_days)


# ✅ ADD: Background retraining functionality
@frappe.whitelist()
def retrain_model_background(
    model_type: str, trigger_reason: List[str] = None, scheduled_by: str = None
):
    """
    Background job for automated model retraining
    Called by the scheduler when performance degradation is detected
    """
    try:
        from .ml_storage import storage

        # Log the start of retraining
        retraining_log = {
            "model_type": model_type,
            "trigger_reasons": trigger_reason or [],
            "scheduled_by": scheduled_by or frappe.session.user,
            "started_at": now_datetime().isoformat(),
            "status": "in_progress",
        }

        frappe.logger().info(f"Starting automated retraining for model {model_type}")

        # Get the existing model configuration
        model_doc = frappe.db.get_value(
            "Predictive Model", {"model_type": model_type, "is_active": 1}, "*", as_dict=True
        )

        if not model_doc:
            error_msg = f"No active predictive model found for type: {model_type}"
            frappe.log_error(error_msg, "Model Retraining Error")
            return {"success": False, "error": error_msg}

        # Initialize ML engine
        ml_engine = MLEngine()

        # Extract fresh training data
        training_data = ml_engine.extract_data_for_model(model_doc)

        if "error" in training_data:
            error_msg = f"Data extraction failed: {training_data['error']}"
            frappe.log_error(error_msg, "Model Retraining Error")
            return {"success": False, "error": error_msg}

        # Check if we have sufficient data for retraining
        if not training_data.get("features") or len(training_data["features"]) < 10:
            error_msg = f"Insufficient data for retraining model {model_type}"
            frappe.log_error(error_msg, "Model Retraining Error")
            return {"success": False, "error": error_msg}

        # Create backup of current model before retraining
        backup_path = storage.create_model_backup(model_type, "latest")
        retraining_log["backup_path"] = backup_path

        # Perform retraining
        training_result = ml_engine.train_model(model_doc)

        if training_result.get("success"):
            # Update model registry with new version
            new_version = datetime.now().strftime("%Y%m%d_%H%M%S_retrain")

            # Save retrained model
            model_path = storage.save_model(
                model=training_result["model"],
                model_type=model_type,
                version=new_version,
                performance_metrics=training_result.get("performance_metrics", {}),
            )

            # Update the Predictive Model DocType with new version
            model_doc_obj = frappe.get_doc("Predictive Model", model_doc["name"])
            model_doc_obj.current_version = new_version
            model_doc_obj.last_trained = now_datetime()
            model_doc_obj.training_accuracy = training_result.get("performance_metrics", {}).get(
                "accuracy", 0
            )
            model_doc_obj.model_file_path = model_path
            model_doc_obj.save()

            # Log successful retraining
            retraining_log.update(
                {
                    "status": "completed",
                    "completed_at": now_datetime().isoformat(),
                    "new_version": new_version,
                    "new_accuracy": training_result.get("performance_metrics", {}).get(
                        "accuracy", 0
                    ),
                    "training_samples": len(training_data["features"]),
                }
            )

            frappe.logger().info(
                f"Successfully retrained model {model_type} - new version: {new_version}"
            )

            # Send notification to relevant users
            _send_retraining_notification(model_type, retraining_log, success=True)

            return {
                "success": True,
                "new_version": new_version,
                "performance_metrics": training_result.get("performance_metrics", {}),
                "training_log": retraining_log,
            }

        else:
            # Retraining failed
            error_msg = training_result.get("error", "Unknown training error")
            retraining_log.update(
                {"status": "failed", "completed_at": now_datetime().isoformat(), "error": error_msg}
            )

            frappe.log_error(
                f"Model retraining failed for {model_type}: {error_msg}", "Model Retraining Error"
            )

            # Send failure notification
            _send_retraining_notification(model_type, retraining_log, success=False)

            return {"success": False, "error": error_msg, "training_log": retraining_log}

    except Exception as e:
        error_msg = f"Background retraining error for model {model_type}: {str(e)}"
        frappe.log_error(f"{error_msg}\n{traceback.format_exc()}", "Model Retraining Error")

        # Send failure notification
        _send_retraining_notification(model_type, {"error": error_msg}, success=False)

        return {"success": False, "error": error_msg}


def _send_retraining_notification(model_type: str, retraining_log: Dict, success: bool = True):
    """Send notification about retraining results to relevant users"""
    try:
        # Get users who should be notified (System Managers and Workshop Managers)
        notification_roles = ["System Manager", "Workshop Manager"]

        users_to_notify = frappe.db.sql(
            """
            SELECT DISTINCT u.name, u.email, u.full_name
            FROM `tabUser` u
            JOIN `tabHas Role` hr ON hr.parent = u.name
            WHERE hr.role IN %(roles)s
            AND u.enabled = 1
            AND u.email IS NOT NULL
        """,
            {"roles": notification_roles},
            as_dict=True,
        )

        if success:
            subject = f"✅ Model Retraining Completed: {model_type}"
            message = f"""
            <h3>Automated Model Retraining Completed Successfully</h3>
            <p><strong>Model Type:</strong> {model_type}</p>
            <p><strong>New Version:</strong> {retraining_log.get('new_version', 'N/A')}</p>
            <p><strong>New Accuracy:</strong> {retraining_log.get('new_accuracy', 'N/A'):.4f}</p>
            <p><strong>Training Samples:</strong> {retraining_log.get('training_samples', 'N/A')}</p>
            <p><strong>Trigger Reasons:</strong> {', '.join(retraining_log.get('trigger_reasons', []))}</p>
            <p><strong>Completed At:</strong> {retraining_log.get('completed_at', 'N/A')}</p>
            
            <p>The model has been automatically retrained and is now ready for use.</p>
            """
        else:
            subject = f"❌ Model Retraining Failed: {model_type}"
            message = f"""
            <h3>Automated Model Retraining Failed</h3>
            <p><strong>Model Type:</strong> {model_type}</p>
            <p><strong>Error:</strong> {retraining_log.get('error', 'Unknown error')}</p>
            <p><strong>Failed At:</strong> {retraining_log.get('completed_at', retraining_log.get('started_at', 'N/A'))}</p>
            
            <p>Please check the error logs and manually investigate the issue.</p>
            """

        # Send notifications
        for user in users_to_notify:
            try:
                frappe.sendmail(
                    recipients=[user["email"]], subject=subject, message=message, delayed=False
                )
            except Exception as e:
                frappe.log_error(
                    f"Failed to send retraining notification to {user['email']}: {str(e)}",
                    "Notification Error",
                )

        # Also create an in-app notification
        for user in users_to_notify:
            try:
                notification = frappe.new_doc("Notification Log")
                notification.subject = subject
                notification.email_content = message
                notification.for_user = user["name"]
                notification.type = "Alert"
                notification.document_type = "Predictive Model"
                notification.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(
                    f"Failed to create in-app notification for {user['name']}: {str(e)}",
                    "Notification Error",
                )

    except Exception as e:
        frappe.log_error(f"Notification sending error: {str(e)}", "Notification Error")


@frappe.whitelist()
def schedule_retrain_for_all_models():
    """Check all models and schedule retraining for those that need it"""
    try:
        from .ml_storage import storage

        # Get all unique model types that have usage logs
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

            # Check if retraining is needed
            retrain_check = storage.auto_retrain_check(model_type)

            if retrain_check.get("needs_retraining"):
                # Schedule retraining
                schedule_result = storage.schedule_auto_retrain(model_type)
                results.append(
                    {
                        "model_type": model_type,
                        "scheduled": schedule_result.get("scheduled", False),
                        "job_name": schedule_result.get("job_name"),
                        "reasons": schedule_result.get("reasons", []),
                    }
                )
            else:
                results.append(
                    {
                        "model_type": model_type,
                        "scheduled": False,
                        "reason": "Retraining not needed",
                        "check_results": retrain_check,
                    }
                )

        return {
            "success": True,
            "total_models_checked": len(results),
            "models_scheduled": len([r for r in results if r.get("scheduled")]),
            "results": results,
        }

    except Exception as e:
        frappe.log_error(f"Bulk retraining scheduling error: {str(e)}", "ML Engine Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_retraining_status():
    """Get status of current and recent retraining jobs"""
    try:
        # Get recent jobs from the queue
        jobs_status = []

        # Check Frappe queue for ML retraining jobs
        from frappe.utils.background_jobs import get_jobs

        active_jobs = get_jobs()
        ml_jobs = [job for job in active_jobs if "retrain_model" in job.get("method", "")]

        for job in ml_jobs:
            jobs_status.append(
                {
                    "job_id": job.get("job_id"),
                    "status": job.get("status"),
                    "method": job.get("method"),
                    "enqueued_at": job.get("enqueued_at"),
                    "started_at": job.get("started_at", ""),
                    "ended_at": job.get("ended_at", ""),
                }
            )

        # Also get recent model training history from the database
        recent_models = frappe.db.sql(
            """
            SELECT 
                name,
                model_type,
                current_version,
                last_trained,
                training_accuracy,
                modified
            FROM `tabPredictive Model`
            WHERE last_trained >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY last_trained DESC
        """,
            as_dict=True,
        )

        return {
            "active_jobs": jobs_status,
            "recent_retraining": recent_models,
            "checked_at": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Retraining status check error: {str(e)}", "ML Engine Error")
        return {"error": str(e)}
