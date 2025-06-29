"""
ERPNext Runtime Test Script for Parts Inventory Module
This script should be run from bench console or within ERPNext context
"""

def test_parts_inventory_runtime():
    """Test Parts Inventory functions in ERPNext runtime"""
    
    print("🚀 Testing Parts Inventory Module in ERPNext Runtime")
    print("=" * 60)
    
    # Test 1: VIN Decoding
    print("\n🧪 Testing VIN Decoding...")
    try:
        from universal_workshop.parts_inventory.compatibility_matrix import decode_vin
        
        test_vin = "1HGBH41JXMN109186"  # Sample Honda VIN
        result = decode_vin(test_vin)
        
        if result.get('success'):
            print(f"✅ VIN Decoded: {result['data']['manufacturer']} {result['data']['model_year']}")
            print(f"   Country: {result['data']['country']}")
            print(f"   Check Digit Valid: {result['data']['check_digit_valid']}")
        else:
            print(f"❌ VIN Decode Failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ VIN Decode Error: {str(e)}")
    
    # Test 2: Parts Catalog API
    print("\n🧪 Testing Parts Catalog API...")
    try:
        from universal_workshop.parts_inventory.api import get_parts_catalog
        
        result = get_parts_catalog(page=1, page_size=5)
        
        if result.get('success'):
            parts_count = len(result['data']['parts'])
            print(f"✅ Parts Catalog: Retrieved {parts_count} parts")
            print(f"   Total Available: {result['data']['total_count']}")
        else:
            print(f"❌ Parts Catalog Failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Parts Catalog Error: {str(e)}")
    
    # Test 3: Barcode Generation
    print("\n🧪 Testing Barcode Generation...")
    try:
        from universal_workshop.parts_inventory.barcode_utils import generate_automotive_item_code
        
        item_code = generate_automotive_item_code("Engine Parts", "TOYOTA")
        print(f"✅ Generated Item Code: {item_code}")
        
    except Exception as e:
        print(f"❌ Barcode Generation Error: {str(e)}")
    
    # Test 4: Supplier Performance
    print("\n🧪 Testing Supplier Performance Dashboard...")
    try:
        from universal_workshop.parts_inventory.supplier_integration import get_supplier_performance_dashboard
        
        result = get_supplier_performance_dashboard()
        
        if result.get('success'):
            suppliers_count = len(result['data']['suppliers'])
            print(f"✅ Supplier Dashboard: {suppliers_count} suppliers analyzed")
        else:
            print(f"❌ Supplier Dashboard Failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Supplier Dashboard Error: {str(e)}")
    
    # Test 5: Compatibility Check
    print("\n🧪 Testing Part Compatibility...")
    try:
        from universal_workshop.parts_inventory.compatibility_matrix import get_part_compatibility
        
        # Get first available item
        items = frappe.get_list("Item", limit=1, filters={"disabled": 0})
        
        if items:
            item_code = items[0].name
            result = get_part_compatibility(item_code)
            
            if result.get('success'):
                print(f"✅ Compatibility Check: Item {item_code} analyzed successfully")
            else:
                print(f"❌ Compatibility Check Failed: {result.get('message', 'Unknown error')}")
        else:
            print("⚠️  No items available for compatibility testing")
            
    except Exception as e:
        print(f"❌ Compatibility Check Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Runtime Testing Complete")
    print("   Note: Some functions may show errors if test data is not available")
    print("   This is normal for a fresh ERPNext installation")


def test_web_page_access():
    """Test web page accessibility"""
    print("\n🌐 Testing Web Page Access...")
    
    try:
        import requests
        base_url = "http://127.0.0.1:8001"
        
        pages = [
            "/parts-catalog",
            "/supplier-dashboard", 
            "/compatibility-matrix"
        ]
        
        for page in pages:
            try:
                response = requests.get(f"{base_url}{page}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {page} accessible (200 OK)")
                else:
                    print(f"⚠️  {page} returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {page} not accessible: {str(e)}")
                
    except ImportError:
        print("⚠️  requests module not available for web testing")
    except Exception as e:
        print(f"❌ Web page testing error: {str(e)}")


if __name__ == "__main__":
    # This should be run in bench console context
    print("⚠️  This script should be run from 'bench console' for full functionality")
    print("   Run: bench console")
    print("   Then: exec(open('runtime_test.py').read())")
    
    # Basic function existence check only
    print("\n🔧 Basic Module Check (Outside ERPNext Context)...")
    
    try:
        import sys
        import os
        sys.path.insert(0, './apps')
        
        # Check if files exist
        files = [
            './apps/universal_workshop/universal_workshop/parts_inventory/barcode_utils.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/warehouse_management.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/compatibility_matrix.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/api.py',
            './apps/universal_workshop/universal_workshop/parts_inventory/supplier_integration.py'
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                print(f"✅ {os.path.basename(file_path)} exists")
            else:
                print(f"❌ {os.path.basename(file_path)} missing")
                
    except Exception as e:
        print(f"❌ Basic check error: {str(e)}")
