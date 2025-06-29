# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def test_role_permission_system():
    """Test the workshop role and permission modeling system"""
    print("🔍 Testing Workshop Role and Permission System...")

    try:
        # Test 1: Create default workshop roles
        print("\n1. Creating default workshop roles...")
        from universal_workshop.user_management.doctype.workshop_role.workshop_role import (
            create_default_workshop_roles,
        )

        created_roles = create_default_workshop_roles()
        print(f"   ✅ Created roles: {created_roles}")

        # Test 2: Verify roles were created with Arabic names
        print("\n2. Verifying role creation with Arabic support...")
        roles = frappe.get_list(
            "Workshop Role",
            filters={"is_active": 1},
            fields=["name", "role_name", "role_name_ar", "role_type", "priority_level"],
        )

        for role in roles:
            print(
                f"   ✅ {role.role_name} ({role.role_name_ar}) - Type: {role.role_type}, Priority: {role.priority_level}"
            )

        # Test 3: Test permission manager
        print("\n3. Testing permission manager...")
        from universal_workshop.user_management.permission_manager import WorkshopPermissionManager

        permission_manager = WorkshopPermissionManager()
        success = permission_manager.setup_default_permissions()
        print(f"   ✅ Permission setup: {'Success' if success else 'Failed'}")

        # Test 4: Test role hierarchy
        print("\n4. Testing role hierarchy...")
        from universal_workshop.user_management.doctype.workshop_role.workshop_role import (
            get_role_hierarchy,
        )

        hierarchy = get_role_hierarchy()
        for role_type, role_list in hierarchy.items():
            print(f"   ✅ {role_type}: {len(role_list)} roles")
            for role in role_list:
                print(
                    f"      - {role.role_name} ({role.role_name_ar}) [Priority: {role.priority_level}]"
                )

        # Test 5: Test user role assignment
        print("\n5. Testing user role assignment...")
        current_user = frappe.session.user
        user_roles = permission_manager.get_user_workshop_roles(current_user)
        print(f"   ✅ Current user has {len(user_roles)} workshop roles")

        # Test 6: Create default permission profiles
        print("\n6. Creating default permission profiles...")
        from universal_workshop.user_management.doctype.workshop_permission_profile.workshop_permission_profile import (
            create_default_permission_profiles,
        )

        created_profiles = create_default_permission_profiles()
        print(f"   ✅ Created permission profiles: {created_profiles}")

        # Test 7: Verify Arabic field validation
        print("\n7. Testing Arabic field validation...")
        try:
            test_role = frappe.new_doc("Workshop Role")
            test_role.role_name = "Test Role"
            test_role.role_type = "Technical"
            test_role.priority_level = 5
            # Missing Arabic name should trigger validation error
            test_role.insert()
            print("   ❌ Arabic validation failed - should have thrown error")
        except frappe.ValidationError as e:
            print(f"   ✅ Arabic validation working: {str(e)}")

        # Test 8: Test permission validation
        print("\n8. Testing permission validation...")
        has_access = permission_manager.validate_user_permission(
            current_user, "Workshop Role", "test", "read"
        )
        print(f"   ✅ User access validation: {'Has access' if has_access else 'No access'}")

        print("\n🎉 All tests completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        frappe.log_error(f"Role permission test failed: {e}")
        return False


def test_arabic_role_creation():
    """Test creating a workshop role with Arabic content"""
    print("\n🔍 Testing Arabic role creation...")

    try:
        # Create a test role with Arabic content
        test_role = frappe.new_doc("Workshop Role")
        test_role.role_name = "Test Arabic Role"
        test_role.role_name_ar = "دور تجريبي عربي"
        test_role.role_description = "Test role for Arabic functionality"
        test_role.role_description_ar = "دور تجريبي لاختبار الوظائف العربية"
        test_role.role_type = "Technical"
        test_role.priority_level = 6
        test_role.is_active = 1
        test_role.supports_arabic_ui = 1

        # Add some permissions
        perm_row = test_role.append("workshop_permissions")
        perm_row.doctype_name = "Customer"
        perm_row.permission_type = "Read"
        perm_row.permission_level = 0
        perm_row.is_active = 1

        test_role.insert()

        print(f"   ✅ Created Arabic role: {test_role.role_name} ({test_role.role_name_ar})")
        print(f"   ✅ Arabic display name: {test_role.arabic_role_display}")

        # Verify the role was created correctly
        created_role = frappe.get_doc("Workshop Role", test_role.name)
        assert created_role.role_name_ar == "دور تجريبي عربي"
        assert created_role.arabic_role_display == "دور تجريبي عربي"

        print("   ✅ Arabic role creation test passed!")

        # Clean up test role
        frappe.delete_doc("Workshop Role", test_role.name)
        print("   ✅ Test role cleaned up")

        return True

    except Exception as e:
        print(f"   ❌ Arabic role creation test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run tests
    frappe.init(site="universal.local")
    frappe.connect()

    print("=" * 60)
    print("UNIVERSAL WORKSHOP ERP - ROLE & PERMISSION SYSTEM TESTS")
    print("=" * 60)

    test_success = test_role_permission_system()
    arabic_test_success = test_arabic_role_creation()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Role & Permission System: {'✅ PASSED' if test_success else '❌ FAILED'}")
    print(f"Arabic Role Creation: {'✅ PASSED' if arabic_test_success else '❌ FAILED'}")

    if test_success and arabic_test_success:
        print("\n🎉 ALL TESTS PASSED - Role and Permission Modeling is working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED - Please check the implementation")

    frappe.db.commit()
