# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.tests.utils import FrappeTestCase
from universal_workshop.user_management.custom_permission_engine import permission_engine


class TestCustomPermissionEngine(FrappeTestCase):
    """Test suite for the Custom Permission Engine"""

    def setUp(self):
        """Set up test data"""
        self.test_users = self.create_test_users()
        self.test_workshop_roles = self.create_test_workshop_roles()
        self.test_documents = self.create_test_documents()

    def create_test_users(self):
        """Create test users for different scenarios"""
        users = {}

        # Workshop Manager
        if not frappe.db.exists("User", "manager@workshop.test"):
            manager = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "manager@workshop.test",
                    "first_name": "Workshop",
                    "last_name": "Manager",
                    "username": "workshop_manager",
                    "workshop_location": "Main Branch",
                    "department": "Management",
                    "enabled": 1,
                }
            )
            manager.insert(ignore_permissions=True)
            users["manager"] = manager.name

        # Technician
        if not frappe.db.exists("User", "tech@workshop.test"):
            technician = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "tech@workshop.test",
                    "first_name": "Ahmed",
                    "last_name": "Technician",
                    "username": "technician_ahmed",
                    "workshop_location": "Main Branch",
                    "department": "Service",
                    "enabled": 1,
                }
            )
            technician.insert(ignore_permissions=True)
            users["technician"] = technician.name

        # Parts Manager
        if not frappe.db.exists("User", "parts@workshop.test"):
            parts_manager = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "parts@workshop.test",
                    "first_name": "Saeed",
                    "last_name": "Parts",
                    "username": "parts_manager",
                    "workshop_location": "Main Branch",
                    "department": "Parts",
                    "enabled": 1,
                }
            )
            parts_manager.insert(ignore_permissions=True)
            users["parts"] = parts_manager.name

        return users

    def create_test_workshop_roles(self):
        """Create test workshop roles"""
        roles = {}

        # Workshop Manager Role
        if not frappe.db.exists("Workshop Role", "Test Workshop Manager"):
            manager_role = frappe.get_doc(
                {
                    "doctype": "Workshop Role",
                    "role_name": "Test Workshop Manager",
                    "role_name_ar": "مدير الورشة",
                    "role_type": "Management",
                    "priority_level": 10,
                    "is_active": 1,
                    "description": "Full access workshop manager role for testing",
                }
            )
            manager_role.insert(ignore_permissions=True)
            roles["manager"] = manager_role.name

        # Technician Role
        if not frappe.db.exists("Workshop Role", "Test Technician"):
            tech_role = frappe.get_doc(
                {
                    "doctype": "Workshop Role",
                    "role_name": "Test Technician",
                    "role_name_ar": "فني",
                    "role_type": "Technical",
                    "priority_level": 5,
                    "is_active": 1,
                    "description": "Limited access technician role for testing",
                }
            )
            tech_role.insert(ignore_permissions=True)
            roles["technician"] = tech_role.name

        return roles

    def create_test_documents(self):
        """Create test documents for permission testing"""
        docs = {}

        # Test Customer
        if not frappe.db.exists("Customer", "TEST-CUSTOMER-001"):
            customer = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": "Test Customer",
                    "customer_type": "Individual",
                    "territory": "All Territories",
                    "customer_group": "All Customer Groups",
                }
            )
            customer.insert(ignore_permissions=True)
            docs["customer"] = customer.name

        return docs

    def test_permission_engine_initialization(self):
        """Test permission engine initialization"""
        self.assertIsNotNone(permission_engine)
        self.assertIsInstance(permission_engine.workshop_doctypes, list)
        self.assertIsInstance(permission_engine.sensitive_fields, dict)
        self.assertIn("Customer", permission_engine.workshop_doctypes)

    def test_user_workshop_roles(self):
        """Test getting user workshop roles"""
        # Test with manager user
        manager_roles = permission_engine.get_user_workshop_roles(self.test_users["manager"])
        self.assertIsInstance(manager_roles, list)

        # Test with non-existent user
        empty_roles = permission_engine.get_user_workshop_roles("nonexistent@test.com")
        self.assertEqual(empty_roles, [])

    def test_user_workshop_context(self):
        """Test getting user workshop context"""
        manager_context = permission_engine.get_user_workshop_context(self.test_users["manager"])

        self.assertIsInstance(manager_context, dict)
        self.assertIn("user", manager_context)
        self.assertIn("workshop_location", manager_context)
        self.assertEqual(manager_context["user"], self.test_users["manager"])

    def test_document_permission_check(self):
        """Test basic document permission checking"""
        # Get test customer document
        customer_doc = frappe.get_doc("Customer", self.test_documents["customer"])

        # Test with manager (should have access)
        manager_has_read = permission_engine.has_permission(
            customer_doc, self.test_users["manager"], "read"
        )
        self.assertTrue(manager_has_read)

        # Test with string doctype
        string_permission = permission_engine.has_permission(
            "Customer", self.test_users["manager"], "read"
        )
        self.assertTrue(string_permission)

    def test_row_level_permissions(self):
        """Test row-level permission restrictions"""
        customer_doc = frappe.get_doc("Customer", self.test_documents["customer"])

        # Test row-level access for different users
        manager_access = permission_engine.check_row_level_permission(
            customer_doc, self.test_users["manager"], "read"
        )
        self.assertTrue(manager_access)

        # Test with technician (might have limited access)
        tech_access = permission_engine.check_row_level_permission(
            customer_doc, self.test_users["technician"], "read"
        )
        # Should return True as base implementation allows access
        self.assertTrue(tech_access)

    def test_field_level_permissions(self):
        """Test field-level permission restrictions"""
        customer_doc = frappe.get_doc("Customer", self.test_documents["customer"])

        # Get user roles
        manager_roles = permission_engine.get_user_workshop_roles(self.test_users["manager"])
        tech_roles = permission_engine.get_user_workshop_roles(self.test_users["technician"])

        # Test field access for manager
        manager_field_access = permission_engine.check_field_level_permission(
            customer_doc, manager_roles
        )
        self.assertTrue(manager_field_access)

        # Test field access for technician
        tech_field_access = permission_engine.check_field_level_permission(customer_doc, tech_roles)
        self.assertTrue(tech_field_access)  # Should pass as no sensitive fields modified

    def test_business_context_permissions(self):
        """Test business context permission validation"""
        customer_doc = frappe.get_doc("Customer", self.test_documents["customer"])

        # Test business context access
        manager_business_access = permission_engine.check_business_context_permission(
            customer_doc, self.test_users["manager"]
        )
        self.assertTrue(manager_business_access)

        tech_business_access = permission_engine.check_business_context_permission(
            customer_doc, self.test_users["technician"]
        )
        self.assertTrue(tech_business_access)

    def test_query_conditions(self):
        """Test query condition generation for list views"""
        # Test conditions for different users and doctypes
        manager_conditions = permission_engine.apply_query_conditions(
            "Customer", self.test_users["manager"]
        )
        self.assertIsInstance(manager_conditions, str)

        tech_conditions = permission_engine.apply_query_conditions(
            "Service Order", self.test_users["technician"]
        )
        self.assertIsInstance(tech_conditions, str)

    def test_system_manager_bypass(self):
        """Test that System Manager bypasses all custom restrictions"""
        # Create system manager user for testing
        if not frappe.db.exists("User", "sysmanager@workshop.test"):
            sys_manager = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": "sysmanager@workshop.test",
                    "first_name": "System",
                    "last_name": "Manager",
                    "username": "system_manager",
                    "enabled": 1,
                }
            )
            sys_manager.insert(ignore_permissions=True)

            # Add System Manager role
            sys_manager.add_roles("System Manager")

        customer_doc = frappe.get_doc("Customer", self.test_documents["customer"])

        # System Manager should have full access
        sys_access = permission_engine.has_permission(
            customer_doc, "sysmanager@workshop.test", "write"
        )
        self.assertTrue(sys_access)

    def test_error_handling(self):
        """Test error handling in permission checks"""
        # Test with invalid document
        try:
            invalid_access = permission_engine.has_permission(
                None, self.test_users["manager"], "read"
            )
            # Should not raise exception
            self.assertIsNotNone(invalid_access)
        except Exception as e:
            self.fail(f"Permission check with invalid doc raised exception: {e}")

        # Test with invalid user
        try:
            invalid_user_access = permission_engine.has_permission(
                "Customer", "invalid@user.com", "read"
            )
            # Should not raise exception
            self.assertIsNotNone(invalid_user_access)
        except Exception as e:
            self.fail(f"Permission check with invalid user raised exception: {e}")

    def test_arabic_role_support(self):
        """Test Arabic role name support"""
        # Check if Arabic role names are properly handled
        if self.test_workshop_roles.get("manager"):
            role_doc = frappe.get_doc("Workshop Role", self.test_workshop_roles["manager"])
            self.assertIsNotNone(role_doc.role_name_ar)
            self.assertEqual(role_doc.role_name_ar, "مدير الورشة")

    def tearDown(self):
        """Clean up test data"""
        # Clean up test users
        for user_email in self.test_users.values():
            if frappe.db.exists("User", user_email):
                frappe.delete_doc("User", user_email, ignore_permissions=True)

        # Clean up test roles
        for role_name in self.test_workshop_roles.values():
            if frappe.db.exists("Workshop Role", role_name):
                frappe.delete_doc("Workshop Role", role_name, ignore_permissions=True)

        # Clean up test documents
        for doc_name in self.test_documents.values():
            if frappe.db.exists("Customer", doc_name):
                frappe.delete_doc("Customer", doc_name, ignore_permissions=True)

        # Clean up system manager test user
        if frappe.db.exists("User", "sysmanager@workshop.test"):
            frappe.delete_doc("User", "sysmanager@workshop.test", ignore_permissions=True)

        frappe.db.commit()


@frappe.whitelist()
def run_permission_tests():
    """Run permission system tests via API"""
    try:
        import unittest

        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomPermissionEngine)

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return {
            "success": result.wasSuccessful(),
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "details": {
                "failures": [str(failure) for failure in result.failures],
                "errors": [str(error) for error in result.errors],
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def test_permission_integration():
    """Test permission integration with real ERPNext documents"""
    try:
        results = {
            "permission_engine_status": "active",
            "workshop_doctypes": permission_engine.workshop_doctypes,
            "sensitive_fields": permission_engine.sensitive_fields,
            "test_results": [],
        }

        # Test current user permissions
        current_user = frappe.session.user
        user_roles = permission_engine.get_user_workshop_roles(current_user)
        user_context = permission_engine.get_user_workshop_context(current_user)

        results["current_user"] = {
            "user": current_user,
            "workshop_roles": user_roles,
            "context": user_context,
        }

        # Test permission checks for each workshop doctype
        for doctype in permission_engine.workshop_doctypes:
            try:
                # Test basic permission check
                has_read = permission_engine.check_document_permission(doctype, user_roles, "read")
                has_write = permission_engine.check_document_permission(
                    doctype, user_roles, "write"
                )

                # Test query conditions
                conditions = permission_engine.apply_query_conditions(doctype, current_user)

                results["test_results"].append(
                    {
                        "doctype": doctype,
                        "read_permission": has_read,
                        "write_permission": has_write,
                        "query_conditions": conditions,
                        "status": "success",
                    }
                )

            except Exception as e:
                results["test_results"].append(
                    {"doctype": doctype, "status": "error", "error": str(e)}
                )

        return results

    except Exception as e:
        return {"success": False, "error": str(e)}
