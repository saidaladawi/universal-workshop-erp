"""
Machine Learning Engine
Core ML functionality for Universal Workshop predictive analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_days, get_datetime

# Configure logging
logger = logging.getLogger(__name__)

class MLEngine:
    """Core machine learning engine for Universal Workshop"""
    
    def __init__(self):
        self.models = {}
        self.data_cache = {}
        
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if ML dependencies are installed"""
        deps = {
            'pandas': False,
            'scikit_learn': False,
            'numpy': False
        }
        
        try:
            import pandas
            deps['pandas'] = True
        except ImportError:
            pass
            
        try:
            import sklearn
            deps['scikit_learn'] = True
        except ImportError:
            pass
            
        try:
            import numpy
            deps['numpy'] = True
        except ImportError:
            pass
            
        return deps
    
    def extract_data_for_model(self, model_doc: Dict) -> Dict[str, Any]:
        """Extract training data based on model configuration"""
        try:
            data_sources = json.loads(model_doc.get('data_sources', '[]'))
            prediction_type = model_doc.get('prediction_type')
            target_metric = model_doc.get('target_metric')
            
            if prediction_type == 'Time Series Forecast':
                return self._extract_time_series_data(data_sources, target_metric)
            elif prediction_type == 'Regression':
                return self._extract_regression_data(data_sources, target_metric)
            else:
                return self._extract_classification_data(data_sources, target_metric)
                
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return {'features': [], 'target': [], 'error': str(e)}
    
    def _extract_time_series_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract time series data for forecasting"""
        data = {'features': [], 'target': [], 'dates': []}
        
        try:
            # Extract revenue data from Sales Invoice
            if 'Sales Invoice' in data_sources and target_metric == 'Revenue':
                revenue_data = frappe.db.sql("""
                    SELECT 
                        DATE(posting_date) as date,
                        SUM(grand_total) as revenue,
                        COUNT(*) as invoice_count
                    FROM `tabSales Invoice`
                    WHERE docstatus = 1
                    AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                    GROUP BY DATE(posting_date)
                    ORDER BY date
                """, as_dict=True)
                
                for row in revenue_data:
                    data['dates'].append(row['date'])
                    data['target'].append(flt(row['revenue']))
                    data['features'].append([
                        flt(row['revenue']),
                        cint(row['invoice_count']),
                        row['date'].weekday(),  # Day of week
                        row['date'].day,        # Day of month
                        row['date'].month       # Month
                    ])
            
            # Extract service order data
            if 'Service Order' in data_sources:
                service_data = frappe.db.sql("""
                    SELECT 
                        DATE(creation) as date,
                        COUNT(*) as order_count,
                        AVG(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completion_rate
                    FROM `tabService Order`
                    WHERE creation >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                    GROUP BY DATE(creation)
                    ORDER BY date
                """, as_dict=True)
                
                # Merge with existing data or create new if no revenue data
                if not data['features']:
                    for row in service_data:
                        data['dates'].append(row['date'])
                        data['target'].append(flt(row['order_count']))
                        data['features'].append([
                            flt(row['order_count']),
                            flt(row['completion_rate']),
                            row['date'].weekday(),
                            row['date'].day,
                            row['date'].month
                        ])
                        
        except Exception as e:
            logger.error(f"Time series extraction error: {str(e)}")
            data['error'] = str(e)
            
        return data
    
    def _extract_regression_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract regression data for continuous predictions"""
        data = {'features': [], 'target': []}
        
        try:
            # Customer satisfaction regression
            if target_metric == 'Customer Satisfaction':
                customer_data = frappe.db.sql("""
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
                """, as_dict=True)
                
                for row in customer_data:
                    data['features'].append([
                        flt(row['total_orders']),
                        flt(row['avg_order_value']),
                        flt(row['avg_service_time']),
                    ])
                    data['target'].append(flt(row['positive_feedback']))
                    
        except Exception as e:
            logger.error(f"Regression extraction error: {str(e)}")
            data['error'] = str(e)
            
        return data
    
    def _extract_classification_data(self, data_sources: List[str], target_metric: str) -> Dict:
        """Extract classification data for categorical predictions"""
        data = {'features': [], 'target': []}
        
        try:
            # Vehicle maintenance classification
            if 'Vehicle' in data_sources and target_metric == 'Maintenance Risk':
                vehicle_data = frappe.db.sql("""
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
                """, as_dict=True)
                
                for row in vehicle_data:
                    current_year = datetime.now().year
                    vehicle_age = current_year - cint(row['year'])
                    
                    data['features'].append([
                        vehicle_age,
                        flt(row['mileage']),
                        cint(row['service_count']),
                        cint(row['days_since_service'])
                    ])
                    data['target'].append(row['risk_level'])
                    
        except Exception as e:
            logger.error(f"Classification extraction error: {str(e)}")
            data['error'] = str(e)
            
        return data
    
    def train_model(self, model_doc: Dict) -> Dict[str, Any]:
        """Train ML model based on configuration"""
        deps = self.check_dependencies()
        if not all(deps.values()):
            return {
                'status': 'error',
                'message': _('Missing ML dependencies: {0}').format(
                    ', '.join([k for k, v in deps.items() if not v])
                )
            }
        
        try:
            # Import ML libraries
            import pandas as pd
            import numpy as np
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
            
            # Extract training data
            training_data = self.extract_data_for_model(model_doc)
            
            if 'error' in training_data:
                return {
                    'status': 'error',
                    'message': training_data['error']
                }
            
            if not training_data['features'] or not training_data['target']:
                return {
                    'status': 'error',
                    'message': _('No training data available')
                }
            
            # Prepare data
            X = np.array(training_data['features'])
            y = np.array(training_data['target'])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model based on algorithm type
            model, score = self._train_algorithm(
                model_doc.get('algorithm_type'),
                model_doc.get('model_parameters'),
                X_train, X_test, y_train, y_test
            )
            
            if model is None:
                return {
                    'status': 'error',
                    'message': _('Model training failed')
                }
            
            # Store model (in production, save to file system)
            self.models[model_doc.get('name')] = {
                'model': model,
                'features_count': X.shape[1],
                'trained_date': datetime.now(),
                'accuracy': score
            }
            
            return {
                'status': 'success',
                'accuracy': score,
                'features_count': X.shape[1],
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Model training error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _train_algorithm(self, algorithm_type: str, parameters: str, 
                        X_train, X_test, y_train, y_test) -> Tuple[Any, float]:
        """Train specific ML algorithm"""
        try:
            params = json.loads(parameters) if parameters else {}
            
            if algorithm_type == 'Random Forest':
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
                    
            elif algorithm_type == 'Gradient Boosting':
                from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
                
                if isinstance(y_train[0], str):
                    from sklearn.preprocessing import LabelEncoder
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
            model_name = model_doc.get('name')
            
            if model_name not in self.models:
                return {
                    'status': 'error',
                    'message': _('Model not trained')
                }
            
            model_info = self.models[model_name]
            model = model_info['model']
            
            # Generate prediction data based on model type
            prediction_type = model_doc.get('prediction_type')
            
            if prediction_type == 'Time Series Forecast':
                return self._generate_time_series_predictions(
                    model, model_doc, horizon_days or model_doc.get('prediction_horizon_days', 30)
                )
            else:
                return self._generate_standard_predictions(model, model_doc)
                
        except Exception as e:
            logger.error(f"Prediction generation error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _generate_time_series_predictions(self, model, model_doc: Dict, horizon_days: int) -> Dict:
        """Generate time series predictions"""
        predictions = []
        
        try:
            import pandas as pd
            import numpy as np
            
            # Get recent data for prediction base
            base_date = datetime.now().date()
            
            for i in range(horizon_days):
                pred_date = base_date + timedelta(days=i+1)
                
                # Create feature vector for prediction
                features = [
                    0,  # Placeholder values - in production, use actual features
                    0,
                    pred_date.weekday(),
                    pred_date.day,
                    pred_date.month
                ]
                
                pred_value = model.predict([features])[0]
                
                predictions.append({
                    'date': pred_date.isoformat(),
                    'predicted_value': float(pred_value),
                    'confidence': 0.8  # Placeholder confidence
                })
                
            return {
                'status': 'success',
                'predictions': predictions,
                'horizon_days': horizon_days
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _generate_standard_predictions(self, model, model_doc: Dict) -> Dict:
        """Generate standard predictions for classification/regression"""
        try:
            # In production, this would use actual data to predict
            # For now, return sample predictions
            return {
                'status': 'success',
                'predictions': [
                    {
                        'item': 'Sample Item 1',
                        'predicted_value': 'High Risk',
                        'confidence': 0.85
                    }
                ]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

# Global ML engine instance
ml_engine = MLEngine()

@frappe.whitelist()
def check_ml_dependencies():
    """Check ML dependencies via API"""
    return ml_engine.check_dependencies()

@frappe.whitelist()
def train_predictive_model(model_name):
    """Train a predictive model via API"""
    model_doc = frappe.get_doc('Predictive Model', model_name)
    return ml_engine.train_model(model_doc.as_dict())

@frappe.whitelist()
def generate_model_predictions(model_name, horizon_days=None):
    """Generate predictions via API"""
    model_doc = frappe.get_doc('Predictive Model', model_name)
    return ml_engine.generate_predictions(model_doc.as_dict(), horizon_days)
