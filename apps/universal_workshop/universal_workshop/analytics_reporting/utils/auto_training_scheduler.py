# pylint: disable=no-member
"""
Automated ML Model Retraining Scheduler
Production-ready automated training with drift detection and scheduling
Part of Phase 4: Advanced Analytics & Performance Optimization
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, add_days, getdate, format_datetime

from .ml_storage import MLModelStorage
from .ml_engine import MLEngine

# ML libraries with graceful imports
try:
    import numpy as np
    import pandas as pd
    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    frappe.log_error("ML libraries not available for auto-training.", "Auto Training Error")

class AutoTrainingScheduler:
    """Automated model training and retraining system"""
    
    def __init__(self):
        self.storage = MLModelStorage()
        self.ml_engine = MLEngine()
        self.performance_threshold = 0.8  # Minimum acceptable model performance
        self.drift_threshold = 0.15  # 15% performance degradation triggers retraining
        
    def schedule_retraining(self):
        """Main scheduler function - checks all models for retraining needs"""
        try:
            if not ML_AVAILABLE:
                frappe.log_error("ML libraries not available for scheduled retraining", "Auto Training")
                return
            
            models_to_retrain = []
            
            # Get all registered models
            model_registry = self.storage._get_model_registry()
            
            for model_type, model_versions in model_registry.items():
                if not model_versions:
                    continue
                    
                latest_model = model_versions[0]  # Registry is sorted by creation date desc
                
                # Check if model needs retraining
                needs_retraining, reason = self._evaluate_retraining_need(model_type, latest_model)
                
                if needs_retraining:
                    models_to_retrain.append({
                        'model_type': model_type,
                        'current_version': latest_model['version'],
                        'reason': reason,
                        'priority': self._calculate_retraining_priority(model_type, reason)
                    })
            
            # Sort by priority and retrain
            models_to_retrain.sort(key=lambda x: x['priority'], reverse=True)
            
            training_results = []
            for model_info in models_to_retrain:
                result = self._retrain_model(model_info['model_type'], model_info['reason'])
                training_results.append(result)
            
            # Log results
            self._log_retraining_session(training_results)
            
            # Send notifications for critical models
            self._send_retraining_notifications(training_results)
            
            return {
                "status": "completed",
                "models_evaluated": len(model_registry),
                "models_retrained": len([r for r in training_results if r['status'] == 'success']),
                "training_results": training_results
            }
            
        except Exception as e:
            frappe.log_error(f"Auto-training scheduler error: {str(e)}", "Auto Training Error")
            return {"status": "error", "message": str(e)}
    
    def _evaluate_retraining_need(self, model_type: str, latest_model: Dict) -> tuple:
        """Evaluate if a model needs retraining"""
        try:
            reasons = []
            
            # 1. Age-based retraining
            created_date = datetime.fromisoformat(latest_model['created'].replace('Z', '+00:00'))
            days_since_training = (datetime.now() - created_date.replace(tzinfo=None)).days
            
            max_age_days = self._get_max_model_age(model_type)
            if days_since_training > max_age_days:
                reasons.append(f"Model age ({days_since_training} days) exceeds maximum ({max_age_days} days)")
            
            # 2. Performance degradation
            current_performance = self._evaluate_current_performance(model_type)
            stored_performance = latest_model.get('performance', {})
            
            if current_performance and stored_performance:
                performance_metric = self._get_primary_metric(model_type)
                
                if performance_metric in current_performance and performance_metric in stored_performance:
                    current_score = current_performance[performance_metric]
                    original_score = stored_performance[performance_metric]
                    
                    performance_drop = (original_score - current_score) / original_score
                    
                    if performance_drop > self.drift_threshold:
                        reasons.append(f"Performance degradation: {performance_drop:.2%} drop in {performance_metric}")
            
            # 3. Data volume increase
            data_volume_increase = self._check_data_volume_increase(model_type, created_date)
            if data_volume_increase > 0.3:  # 30% more data
                reasons.append(f"Significant data increase: {data_volume_increase:.1%} more training data available")
            
            # 4. Feature drift detection
            feature_drift = self._detect_feature_drift(model_type)
            if feature_drift['has_drift']:
                reasons.append(f"Feature drift detected: {feature_drift['drift_score']:.3f}")
            
            # 5. Manual retraining flag
            if self._check_manual_retrain_flag(model_type):
                reasons.append("Manual retraining requested")
            
            return len(reasons) > 0, "; ".join(reasons)
            
        except Exception as e:
            frappe.log_error(f"Retraining evaluation error for {model_type}: {str(e)}", "Auto Training Error")
            return False, f"Evaluation error: {str(e)}"
    
    def _retrain_model(self, model_type: str, reason: str) -> Dict:
        """Retrain a specific model"""
        try:
            frappe.logger().info(f"Starting retraining for {model_type}. Reason: {reason}")
            
            # Get model configuration
            model_config = self._get_model_config(model_type)
            if not model_config:
                return {
                    "model_type": model_type,
                    "status": "error",
                    "message": "Model configuration not found"
                }
            
            # Train new model
            training_result = self.ml_engine.train_model(model_config)
            
            if training_result.get('status') == 'success':
                # Load the trained model and save with versioning
                model = self.ml_engine.models.get(model_config.get('name'))
                if model:
                    # Create new version
                    new_version = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save model with performance metrics
                    model_path = self.storage.save_model(
                        model['model'],
                        model_type,
                        new_version,
                        {
                            'accuracy': training_result.get('accuracy', 0),
                            'features_count': training_result.get('features_count', 0),
                            'training_samples': training_result.get('training_samples', 0),
                            'test_samples': training_result.get('test_samples', 0),
                            'retraining_reason': reason,
                            'retraining_date': now_datetime().isoformat()
                        }
                    )
                    
                    # Compare with previous model
                    comparison = self._compare_model_versions(model_type, new_version)
                    
                    result = {
                        "model_type": model_type,
                        "status": "success",
                        "new_version": new_version,
                        "model_path": model_path,
                        "performance": training_result,
                        "comparison": comparison,
                        "reason": reason
                    }
                    
                    # Auto-promote if better performance
                    if comparison.get('is_better', False):
                        self._promote_model(model_type, new_version)
                        result['promoted'] = True
                    else:
                        result['promoted'] = False
                        result['promotion_note'] = "New model not promoted - performance not improved"
                    
                    return result
                    
            return {
                "model_type": model_type,
                "status": "error",
                "message": "Model training failed",
                "training_result": training_result
            }
            
        except Exception as e:
            frappe.log_error(f"Model retraining error for {model_type}: {str(e)}", "Auto Training Error")
            return {
                "model_type": model_type,
                "status": "error",
                "message": str(e)
            }
    
    def _evaluate_current_performance(self, model_type: str) -> Dict:
        """Evaluate current model performance on recent data"""
        try:
            # Load current model
            model = self.storage.load_model(model_type)
            
            # Get recent test data
            model_config = self._get_model_config(model_type)
            if not model_config:
                return {}
            
            # Extract test data (last 30 days)
            test_data = self.ml_engine.extract_data_for_model(model_config)
            
            if not test_data or 'features' not in test_data or not test_data['features']:
                return {}
            
            X = np.array(test_data['features'])
            y = np.array(test_data['target'])
            
            if len(X) < 10:  # Not enough data for evaluation
                return {}
            
            # Split data for testing
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics based on model type
            prediction_type = model_config.get('prediction_type', 'Regression')
            
            if prediction_type == 'Classification':
                accuracy = accuracy_score(y_test, y_pred)
                return {
                    'accuracy': accuracy,
                    'test_samples': len(y_test),
                    'evaluation_date': now_datetime().isoformat()
                }
            else:
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                return {
                    'mse': mse,
                    'mae': mae,
                    'r2_score': r2,
                    'test_samples': len(y_test),
                    'evaluation_date': now_datetime().isoformat()
                }
                
        except Exception as e:
            frappe.log_error(f"Performance evaluation error for {model_type}: {str(e)}", "Auto Training Error")
            return {}
    
    def _detect_feature_drift(self, model_type: str) -> Dict:
        """Detect if feature distributions have drifted"""
        try:
            # Get model configuration
            model_config = self._get_model_config(model_type)
            if not model_config:
                return {'has_drift': False, 'drift_score': 0.0}
            
            # Extract recent data
            recent_data = self.ml_engine.extract_data_for_model(model_config)
            
            if not recent_data or 'features' not in recent_data:
                return {'has_drift': False, 'drift_score': 0.0}
            
            recent_features = np.array(recent_data['features'])
            
            if len(recent_features) < 50:  # Not enough data for drift detection
                return {'has_drift': False, 'drift_score': 0.0}
            
            # Split into old and new data (simple temporal split)
            split_point = len(recent_features) // 2
            old_features = recent_features[:split_point]
            new_features = recent_features[split_point:]
            
            # Calculate feature-wise drift using statistical distance
            drift_scores = []
            
            for feature_idx in range(recent_features.shape[1]):
                old_feature = old_features[:, feature_idx]
                new_feature = new_features[:, feature_idx]
                
                # Calculate Kolmogorov-Smirnov statistic as drift measure
                # (simplified implementation - in production, use scipy.stats.ks_2samp)
                old_mean, old_std = np.mean(old_feature), np.std(old_feature)
                new_mean, new_std = np.mean(new_feature), np.std(new_feature)
                
                if old_std > 0:
                    drift_score = abs(new_mean - old_mean) / old_std
                    drift_scores.append(drift_score)
            
            overall_drift = np.mean(drift_scores) if drift_scores else 0.0
            
            return {
                'has_drift': overall_drift > 0.5,  # Threshold for drift detection
                'drift_score': overall_drift,
                'feature_drifts': drift_scores
            }
            
        except Exception as e:
            frappe.log_error(f"Feature drift detection error for {model_type}: {str(e)}", "Auto Training Error")
            return {'has_drift': False, 'drift_score': 0.0}
    
    def _get_model_config(self, model_type: str) -> Optional[Dict]:
        """Get model configuration from Predictive Model DocType"""
        try:
            # Map model types to standard names
            model_name_mapping = {
                'revenue_forecast': 'Revenue Prediction Model',
                'maintenance_prediction': 'Maintenance Prediction Model',
                'satisfaction_prediction': 'Customer Satisfaction Model',
                'parts_demand_forecast': 'Parts Demand Model'
            }
            
            model_name = model_name_mapping.get(model_type)
            if not model_name:
                return None
            
            # Try to find existing model configuration
            existing_models = frappe.get_list(
                'Predictive Model',
                filters={'name': ['like', f'%{model_name}%']},
                limit=1
            )
            
            if existing_models:
                model_doc = frappe.get_doc('Predictive Model', existing_models[0].name)
                return model_doc.as_dict()
            
            # Return default configuration if not found
            return self._get_default_model_config(model_type)
            
        except Exception as e:
            frappe.log_error(f"Model config retrieval error for {model_type}: {str(e)}", "Auto Training Error")
            return None
    
    def _get_default_model_config(self, model_type: str) -> Dict:
        """Get default model configuration for auto-training"""
        default_configs = {
            'revenue_forecast': {
                'name': 'Auto Revenue Forecast Model',
                'prediction_type': 'Time Series Forecast',
                'target_metric': 'Revenue',
                'algorithm_type': 'Random Forest',
                'data_sources': '["Sales Invoice"]',
                'algorithm_parameters': '{"n_estimators": 100, "random_state": 42}'
            },
            'maintenance_prediction': {
                'name': 'Auto Maintenance Prediction Model',
                'prediction_type': 'Classification',
                'target_metric': 'Maintenance Risk',
                'algorithm_type': 'Random Forest',
                'data_sources': '["Vehicle", "Service Order"]',
                'algorithm_parameters': '{"n_estimators": 50, "random_state": 42}'
            },
            'satisfaction_prediction': {
                'name': 'Auto Satisfaction Model',
                'prediction_type': 'Regression',
                'target_metric': 'Customer Satisfaction',
                'algorithm_type': 'Random Forest',
                'data_sources': '["Customer", "Service Order"]',
                'algorithm_parameters': '{"n_estimators": 80, "random_state": 42}'
            },
            'parts_demand_forecast': {
                'name': 'Auto Parts Demand Model',
                'prediction_type': 'Time Series Forecast',
                'target_metric': 'Parts Usage',
                'algorithm_type': 'Random Forest',
                'data_sources': '["Parts Inventory", "Service Order"]',
                'algorithm_parameters': '{"n_estimators": 100, "random_state": 42}'
            }
        }
        
        return default_configs.get(model_type, {})
    
    def _log_retraining_session(self, training_results: List[Dict]):
        """Log retraining session results"""
        try:
            log_entry = {
                'session_id': frappe.generate_hash()[:8],
                'timestamp': now_datetime().isoformat(),
                'total_models': len(training_results),
                'successful_retrains': len([r for r in training_results if r['status'] == 'success']),
                'failed_retrains': len([r for r in training_results if r['status'] == 'error']),
                'results': training_results
            }
            
            # Save to file
            log_dir = Path(frappe.get_site_path()) / "private" / "ml_models" / "training_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"retraining_session_{log_entry['session_id']}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, default=str)
            
            frappe.logger().info(f"Retraining session logged: {log_entry['session_id']}")
            
        except Exception as e:
            frappe.log_error(f"Training log error: {str(e)}", "Auto Training Error")

# Scheduled tasks
def daily_model_retraining():
    """Daily scheduled task for model retraining"""
    scheduler = AutoTrainingScheduler()
    return scheduler.schedule_retraining()

def weekly_model_cleanup():
    """Weekly task to cleanup old model versions"""
    try:
        storage = MLModelStorage()
        model_types = ['revenue_forecast', 'maintenance_prediction', 'satisfaction_prediction', 'parts_demand_forecast']
        
        total_cleaned = 0
        for model_type in model_types:
            cleaned = storage.cleanup_old_models(model_type, keep_versions=3)
            total_cleaned += cleaned
        
        frappe.logger().info(f"Weekly cleanup: removed {total_cleaned} old model versions")
        return {"status": "success", "cleaned_models": total_cleaned}
        
    except Exception as e:
        frappe.log_error(f"Weekly cleanup error: {str(e)}", "Auto Training Error")
        return {"status": "error", "message": str(e)}

# API endpoints
@frappe.whitelist()
def trigger_manual_retraining(model_type):
    """Manually trigger model retraining"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions"))
    
    scheduler = AutoTrainingScheduler()
    result = scheduler._retrain_model(model_type, "Manual retraining requested")
    
    return result

@frappe.whitelist()
def get_retraining_status():
    """Get status of recent retraining activities"""
    try:
        log_dir = Path(frappe.get_site_path()) / "private" / "ml_models" / "training_logs"
        
        if not log_dir.exists():
            return {"status": "no_logs", "sessions": []}
        
        # Get recent log files
        log_files = sorted(log_dir.glob("retraining_session_*.json"))[-10:]  # Last 10 sessions
        
        sessions = []
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                sessions.append(log_data)
            except Exception as e:
                frappe.logger().warning(f"Could not read log file {log_file}: {str(e)}")
        
        return {
            "status": "success",
            "sessions": sorted(sessions, key=lambda x: x['timestamp'], reverse=True)
        }
        
    except Exception as e:
        frappe.log_error(f"Retraining status error: {str(e)}", "Auto Training Error")
        return {"status": "error", "message": str(e)} 