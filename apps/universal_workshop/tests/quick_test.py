import frappe
import json

print("🧪 Testing Universal Workshop Branding Service")
print("=" * 50)

# Test 1: Check Workshop Profile DocType
print("\n1. Testing Workshop Profile DocType...")
try:
    meta = frappe.get_meta("Workshop Profile")
    branding_fields = [
        'workshop_logo', 'logo_preview', 'primary_color', 
        'secondary_color', 'dark_mode_enabled', 'theme_preference'
    ]
    
    existing_fields = [field.fieldname for field in meta.fields]
    missing_fields = [field for field in branding_fields if field not in existing_fields]
    
    if not missing_fields:
        print("✅ All branding fields exist in Workshop Profile")
    else:
        print(f"❌ Missing fields: {missing_fields}")
        
except Exception as e:
    print(f"❌ Error checking Workshop Profile: {e}")

# Test 2: Test branding API method
print("\n2. Testing branding API method...")
try:
    from universal_workshop.workshop_operations.workshop_profile.workshop_profile import get_workshop_branding
    
    default_branding = get_workshop_branding()
    print(f"✅ Default branding loaded: {json.dumps(default_branding, indent=2)}")
    
except Exception as e:
    print(f"❌ Error testing branding API: {e}")

# Test 3: Check assets integration
print("\n3. Testing asset integration...")
try:
    from universal_workshop import hooks
    
    branding_js_found = any('branding_service.js' in js for js in hooks.app_include_js)
    branding_css_found = any('dynamic_branding.css' in css for css in hooks.app_include_css)
    
    if branding_js_found:
        print("✅ Branding service JS found in app includes")
    else:
        print("❌ Branding service JS not found in app includes")
        
    if branding_css_found:
        print("✅ Dynamic branding CSS found in app includes")
    else:
        print("❌ Dynamic branding CSS not found in app includes")
        
except Exception as e:
    print(f"❌ Error checking asset integration: {e}")

print("\n" + "=" * 50)
print("🎯 Branding Service Test Complete!") 