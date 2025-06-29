"""
Test suite for Predictive Model DocType
Tests model creation, training, prediction generation, and performance tracking
"""

import unittest
import json
from datetime import datetime, timedelta
import frappe
from universal_workshop.analytics_reporting.doctype.predictive_model.predictive_model import PredictiveModel

class TestPredictiveModel(unittest.TestCase):

    def setUp(self):
        """Setup test data"""
        self.test_model_data = {
            'model_name': 'Test Revenue Forecast',
            'model_name_ar': 'توقع الإيرادات التجريبي',
            'algorithm_type': 'Random Forest',
            'prediction_type': 'Time Series Forecast',
            'business_area': 'Financial',
            'target_metric': 'Revenue',
            'prediction_horizon_days': 30,
            'data_sources': json.dumps(['Sales Invoice', 'Service Order']),
            'model_parameters': json.dumps({
                "n_estimators": 50,
                "max_depth": 5,
                "random_state": 42
            }),
            'update_frequency': 'Daily',
            'confidence_threshold': 75.0,
            'is_active': 1
        }

    def test_predictive_model_creation(self):
        """Test basic predictive model creation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        self.assertEqual(model.model_name_ar, 'توقع الإيرادات التجريبي')
        self.assertEqual(model.algorithm_type, 'Random Forest')
        self.assertEqual(model.model_status, 'Draft')
        self.assertTrue(model.model_code.startswith('PM-'))

    def test_arabic_name_validation(self):
        """Test Arabic name requirement"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.model_name_ar = ''  # Remove Arabic name

        with self.assertRaises(frappe.ValidationError):
            model.insert()

    def test_data_sources_validation(self):
        """Test data sources validation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.data_sources = '[]'  # Empty data sources

        with self.assertRaises(frappe.ValidationError):
            model.insert()

    def test_model_parameters_validation(self):
        """Test model parameters JSON validation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.model_parameters = 'invalid json'  # Invalid JSON

        with self.assertRaises(frappe.ValidationError):
            model.insert()

    def test_prediction_horizon_validation(self):
        """Test prediction horizon validation for time series"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.prediction_horizon_days = 0  # Invalid horizon

        with self.assertRaises(frappe.ValidationError):
            model.insert()

    def test_confidence_threshold_validation(self):
        """Test confidence threshold range validation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.confidence_threshold = 150.0  # Invalid threshold

        with self.assertRaises(frappe.ValidationError):
            model.insert()

    def test_model_code_generation(self):
        """Test automatic model code generation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Test code format: PM-YYYY-#####
        import re
        self.assertTrue(re.match(r'^PM-\d{4}-\d{5}$', model.model_code))

    def test_unique_model_code(self):
        """Test that model codes are unique"""
        model1 = frappe.new_doc('Predictive Model')
        model1.update(self.test_model_data)
        model1.insert()

        model2 = frappe.new_doc('Predictive Model')
        model2.update(self.test_model_data)
        model2.model_name = 'Test Model 2'
        model2.model_name_ar = 'نموذج تجريبي 2'
        model2.insert()

        self.assertNotEqual(model1.model_code, model2.model_code)

    def test_model_training_status_update(self):
        """Test model training status updates"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Test start training
        model.start_training()
        self.assertEqual(model.model_status, 'Training')
        self.assertIsNotNone(model.training_start_time)

        # Test complete training
        model.complete_training(85.5)
        self.assertEqual(model.model_status, 'Trained')
        self.assertEqual(model.accuracy_score, 85.5)
        self.assertIsNotNone(model.last_training_date)

    def test_model_prediction_tracking(self):
        """Test prediction generation tracking"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()
        model.complete_training(80.0)

        # Test prediction generation
        initial_count = model.total_predictions_generated or 0
        model.track_prediction_generation()
        
        self.assertEqual(model.total_predictions_generated, initial_count + 1)
        self.assertIsNotNone(model.last_prediction_date)

    def test_model_performance_calculation(self):
        """Test model performance metrics calculation"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()
        model.complete_training(75.0)

        performance = model.get_performance_metrics()
        
        self.assertIn('accuracy', performance)
        self.assertIn('model_status', performance)
        self.assertIn('last_training', performance)
        self.assertEqual(performance['accuracy'], 75.0)

    def test_whitelisted_methods(self):
        """Test WhiteListed API methods"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Test get_model_performance method
        result = PredictiveModel.get_model_performance(model.name)
        self.assertIn('status', result)
        self.assertIn('performance', result)

        # Test check_ml_dependencies method
        deps = PredictiveModel.check_ml_dependencies()
        self.assertIn('scikit_learn', deps)
        self.assertIn('pandas', deps)

    def test_model_data_extraction(self):
        """Test data extraction for model training"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Test data extraction
        data = model.extract_training_data()
        self.assertIsInstance(data, dict)
        self.assertIn('features', data)
        self.assertIn('target', data)

    def test_model_status_transitions(self):
        """Test valid model status transitions"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Test Draft -> Training
        model.start_training()
        self.assertEqual(model.model_status, 'Training')

        # Test Training -> Trained
        model.complete_training(80.0)
        self.assertEqual(model.model_status, 'Trained')

        # Test Trained -> Deployed
        model.model_status = 'Deployed'
        model.save()
        self.assertEqual(model.model_status, 'Deployed')

    def test_model_accuracy_tracking(self):
        """Test accuracy tracking over time"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()

        # Complete training with different accuracies
        model.complete_training(75.0)
        first_accuracy = model.accuracy_score

        # Retrain with different accuracy
        model.start_training()
        model.complete_training(82.0)
        
        self.assertEqual(model.accuracy_score, 82.0)
        self.assertNotEqual(first_accuracy, model.accuracy_score)

    def test_model_deletion_cleanup(self):
        """Test proper cleanup when model is deleted"""
        model = frappe.new_doc('Predictive Model')
        model.update(self.test_model_data)
        model.insert()
        model_name = model.name

        # Delete model
        model.delete()

        # Verify model is deleted
        self.assertFalse(frappe.db.exists('Predictive Model', model_name))

    def tearDown(self):
        """Clean up test data"""
        # Clean up any test models
        test_models = frappe.get_all('Predictive Model', 
                                   filters={'model_name': ['like', 'Test%']})
        for model in test_models:
            frappe.delete_doc('Predictive Model', model.name, force=True)
        
        frappe.db.commit()

if __name__ == '__main__':
    unittest.main()
