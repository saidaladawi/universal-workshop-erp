#!/usr/bin/env python3
"""
Universal Workshop ERP - Parts Inventory Runtime Test
Tests implemented functions in ERPNext environment
"""

import sys
import os

# Ensure we can access the apps directory
sys.path.insert(0, os.path.join(os.getcwd(), 'apps'))

def main():
    print("🚀 Universal Workshop ERP - Parts Inventory Runtime Test")
    print("=" * 60)
    
    # Test 1: VIN Decoding
    print("\n🧪 Testing VIN Decoding...")
    try:
        from universal_workshop.parts_inventory.compatibility_matrix import decode_vin
        result = decode_vin("1HGBH41JXMN109186")
        print("✅ VIN Decode Success:", result.get('success', False))
        if result.get('success'):
            print("   Manufacturer:", result['data']['manufacturer'])
            print("   Year:", result['data']['model_year'])
            print("   Check Digit Valid:", result['data']['check_digit_valid'])
    except Exception as e:
        print("❌ VIN Decode Error:", str(e))
    
    # Test 2: Barcode Generation
    print("\n🧪 Testing Barcode Generation...")
    try:
        from universal_workshop.parts_inventory.barcode_utils import generate_automotive_item_code
        item_code = generate_automotive_item_code("Engine Parts", "TOYOTA")
        print("✅ Generated Item Code:", item_code)
    except Exception as e:
        print("❌ Barcode Generation Error:", str(e))
    
    # Test 3: Parts Catalog API
    print("\n🧪 Testing Parts Catalog API...")
    try:
        from universal_workshop.parts_inventory.api import get_parts_catalog
        result = get_parts_catalog(page=1, page_size=5)
        print("✅ Parts Catalog Success:", result.get('success', False))
        if result.get('success'):
            print("   Parts Found:", len(result['data']['parts']))
    except Exception as e:
        print("❌ Parts Catalog Error:", str(e))
    
    # Test 4: Supplier Integration
    print("\n🧪 Testing Supplier Performance...")
    try:
        from universal_workshop.parts_inventory.supplier_integration import get_supplier_performance_dashboard
        result = get_supplier_performance_dashboard()
        print("✅ Supplier Performance Success:", result.get('success', False))
        if result.get('success'):
            print("   Suppliers Analyzed:", len(result['data']['suppliers']))
    except Exception as e:
        print("❌ Supplier Performance Error:", str(e))
    
    print("\n" + "=" * 60)
    print("🎯 Runtime Test Complete!")
    print("Note: Some errors are expected if test data is not available")

if __name__ == "__main__":
    main()
            
            f.write("\n🎉 All tests passed!\n")
            
        except Exception as e:
            f.write(f"❌ Test failed: {str(e)}\n")
            f.write(f"Error type: {type(e).__name__}\n")

if __name__ == "__main__":
    main()
