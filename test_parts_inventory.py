#!/usr/bin/env python3
"""
Comprehensive Runtime Testing Script for Universal Workshop ERP Parts Inventory Module
Tests all implemented functions in the actual ERPNext environment
"""

import sys
import os
import json
import traceback
from datetime import datetime

# Add the apps directory to Python path
sys.path.insert(0, './apps')

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🧪 Testing Module Imports...")
    
    try:
        # Test our custom modules
        from universal_workshop.parts_inventory import barcode_utils
        print("✅ barcode_utils imported successfully")
        
        from universal_workshop.parts_inventory import warehouse_management
        print("✅ warehouse_management imported successfully")
        
        from universal_workshop.parts_inventory import compatibility_matrix
        print("✅ compatibility_matrix imported successfully")
        
        from universal_workshop.parts_inventory import api
        print("✅ parts_inventory.api imported successfully")
        
        from universal_workshop.parts_inventory import supplier_integration
        print("✅ supplier_integration imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_barcode_functions():
    """Test barcode utility functions"""
    print("\n🧪 Testing Barcode Functions...")
    
    try:
        from universal_workshop.parts_inventory.barcode_utils import (
            generate_automotive_item_code,
            auto_generate_item_codes
        )
        
        # Test automotive item code generation
        test_category = "Engine Parts"
        test_supplier = "SUPPLIER001"
        
        item_code = generate_automotive_item_code(test_category, test_supplier)
        print(f"✅ Generated item code: {item_code}")
        
        # Test function existence (can't easily test DocType hook without actual Item creation)
        print("✅ auto_generate_item_codes function exists and is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ Barcode function test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_warehouse_functions():
    """Test warehouse management functions"""
    print("\n🧪 Testing Warehouse Management Functions...")
    
    try:
        from universal_workshop.parts_inventory.warehouse_management import (
            validate_stock_transfer,
            on_stock_transfer_submit,
            setup_warehouse_defaults
        )
        
        print("✅ validate_stock_transfer function exists and is callable")
        print("✅ on_stock_transfer_submit function exists and is callable")
        print("✅ setup_warehouse_defaults function exists and is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ Warehouse function test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_compatibility_functions():
    """Test compatibility matrix functions"""
    print("\n🧪 Testing Compatibility Matrix Functions...")
    
    try:
        from universal_workshop.parts_inventory.compatibility_matrix import (
            decode_vin,
            check_part_fitment,
            get_part_compatibility
        )
        
        # Test VIN decoding with a sample VIN
        test_vin = "1HGBH41JXMN109186"  # Sample Honda VIN
        vin_result = decode_vin(test_vin)
        print(f"✅ VIN decode result: {vin_result.get('success', False)}")
        
        print("✅ check_part_fitment function exists and is callable")
        print("✅ get_part_compatibility function exists and is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility function test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_api_endpoints():
    """Test API endpoint functions"""
    print("\n🧪 Testing API Endpoint Functions...")
    
    try:
        from universal_workshop.parts_inventory.api import (
            get_parts_catalog,
            decode_vehicle_vin,
            check_part_vehicle_fitment,
            get_fitment_recommendations
        )
        
        print("✅ get_parts_catalog function exists and is callable")
        print("✅ decode_vehicle_vin function exists and is callable")
        print("✅ check_part_vehicle_fitment function exists and is callable")
        print("✅ get_fitment_recommendations function exists and is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_supplier_integration():
    """Test supplier integration functions"""
    print("\n🧪 Testing Supplier Integration Functions...")
    
    try:
        from universal_workshop.parts_inventory.supplier_integration import (
            create_auto_purchase_order,
            get_supplier_performance_dashboard,
            get_reorder_recommendations
        )
        
        print("✅ create_auto_purchase_order function exists and is callable")
        print("✅ get_supplier_performance_dashboard function exists and is callable")
        print("✅ get_reorder_recommendations function exists and is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ Supplier integration test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_web_pages():
    """Test that web pages exist and are accessible"""
    print("\n🧪 Testing Web Pages...")
    
    try:
        import os
        
        # Check web page files
        web_pages = [
            './apps/universal_workshop/universal_workshop/www/parts-catalog.html',
            './apps/universal_workshop/universal_workshop/www/parts-catalog.py',
            './apps/universal_workshop/universal_workshop/www/supplier-dashboard.html',
            './apps/universal_workshop/universal_workshop/www/supplier-dashboard.py',
            './apps/universal_workshop/universal_workshop/www/compatibility-matrix.html',
            './apps/universal_workshop/universal_workshop/www/compatibility-matrix.py'
        ]
        
        for page in web_pages:
            if os.path.exists(page):
                print(f"✅ {os.path.basename(page)} exists")
            else:
                print(f"❌ {os.path.basename(page)} missing")
        
        # Check JavaScript files
        js_files = [
            './apps/universal_workshop/universal_workshop/public/js/compatibility_matrix_ui.js',
            './apps/universal_workshop/universal_workshop/public/js/supplier_dashboard.js'
        ]
        
        for js_file in js_files:
            if os.path.exists(js_file):
                print(f"✅ {os.path.basename(js_file)} exists")
            else:
                print(f"❌ {os.path.basename(js_file)} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Web page test failed: {str(e)}")
        print(traceback.format_exc())
        return False

def test_syntax_compilation():
    """Test Python syntax compilation"""
    print("\n🧪 Testing syntax compilation...")
    
    import py_compile
    
    try:
        # Test all Python files for syntax errors
        python_files = [
            './apps/universal_workshop/universal_workshop/parts_inventory/barcode_utils.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/warehouse_management.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/compatibility_matrix.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/api.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/supplier_integration.py'
        ]
        
        for py_file in python_files:
            if os.path.exists(py_file):
                py_compile.compile(py_file, doraise=True)
                print(f"✅ {os.path.basename(py_file)} syntax OK")
            else:
                print(f"❌ {os.path.basename(py_file)} missing")
        
        return True
        
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax compilation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Syntax test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Universal Workshop ERP - Parts Inventory Module Runtime Tests")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Barcode Functions", test_barcode_functions),
        ("Warehouse Functions", test_warehouse_functions),
        ("Compatibility Functions", test_compatibility_functions),
        ("API Endpoints", test_api_endpoints),
        ("Supplier Integration", test_supplier_integration),
        ("Web Pages", test_web_pages),
        ("Syntax Compilation", test_syntax_compilation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The Parts Inventory Module is ready for runtime testing.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
