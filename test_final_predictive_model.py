import frappe

def test_predictive_model():
    """اختبار نهائي للـ Predictive Model"""
    
    print("🔍 Testing Predictive Model Implementation...")
    
    # Test DocType exists
    if frappe.db.exists('DocType', 'Predictive Model'):
        print('✅ Predictive Model DocType exists')
        
        # Get DocType info
        doctype = frappe.get_meta('Predictive Model')
        print(f'✅ DocType has {len(doctype.fields)} fields')
        print(f'✅ Module: {doctype.module}')
        
        # Test creating a model
        try:
            model = frappe.new_doc('Predictive Model')
            model.model_name = 'Test Revenue Forecast'
            model.model_name_ar = 'توقع الإيرادات التجريبي'
            model.algorithm_type = 'Random Forest'
            model.prediction_type = 'Time Series Forecast'
            model.business_area = 'Financial'
            model.target_metric = 'Revenue'
            model.prediction_horizon_days = 30
            model.data_sources = '["Sales Invoice", "Service Order"]'
            model.model_parameters = '{"n_estimators": 50}'
            model.update_frequency = 'Daily'
            model.confidence_threshold = 75.0
            model.is_active = 1
            
            # Test validation
            model.validate()
            print('✅ Validation passed')
            
            # Insert without committing
            model.insert()
            print(f'✅ Can create Predictive Model: {model.model_code}')
            
            # Test ML dependencies
            try:
                from universal_workshop.analytics_reporting.utils.ml_engine import check_ml_dependencies
                deps = check_ml_dependencies()
                print(f'✅ ML dependencies: {deps}')
            except Exception as e:
                print(f'⚠️ ML dependencies: {e}')
            
            # Clean up
            frappe.db.rollback()
            print('🎉 Test completed successfully - Implementation working!')
            return True
            
        except Exception as e:
            print(f'❌ Error: {e}')
            frappe.db.rollback()
            return False
    else:
        print('❌ DocType not found')
        return False

if __name__ == '__main__':
    test_predictive_model()
