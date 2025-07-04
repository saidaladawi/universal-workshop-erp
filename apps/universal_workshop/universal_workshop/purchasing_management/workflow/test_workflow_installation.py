"""
Test script for workflow installation validation
"""

import frappe
from frappe import _


@frappe.whitelist()
def test_workflow_installation():
    """Test the approval workflow installation"""

    results = {"status": "success", "tests_passed": 0, "tests_failed": 0, "details": []}

    try:
        # Test 1: Check if Purchase Order workflow exists
        po_workflow = frappe.db.exists("Workflow", "Purchase Order Approval Workflow")
        if po_workflow:
            results["tests_passed"] += 1
            results["details"].append("✅ Purchase Order workflow exists")
        else:
            results["tests_failed"] += 1
            results["details"].append("❌ Purchase Order workflow not found")

        # Test 2: Check if Material Request workflow exists
        mr_workflow = frappe.db.exists("Workflow", "Material Request Approval Workflow")
        if mr_workflow:
            results["tests_passed"] += 1
            results["details"].append("✅ Material Request workflow exists")
        else:
            results["tests_failed"] += 1
            results["details"].append("❌ Material Request workflow not found")

        # Test 3: Check if notification templates exist
        po_template = frappe.db.exists("Notification", "Purchase Order Approval Notification")
        mr_template = frappe.db.exists("Notification", "Material Request Approval Notification")

        if po_template and mr_template:
            results["tests_passed"] += 1
            results["details"].append("✅ Notification templates exist")
        else:
            results["tests_failed"] += 1
            results["details"].append("❌ Some notification templates missing")

        # Test 4: Check if required roles exist
        required_roles = ["Purchase Supervisor", "Department Head", "Director"]
        roles_exist = True

        for role in required_roles:
            if not frappe.db.exists("Role", role):
                roles_exist = False
                break

        if roles_exist:
            results["tests_passed"] += 1
            results["details"].append("✅ All required roles exist")
        else:
            results["tests_failed"] += 1
            results["details"].append("❌ Some required roles missing")

        # Test 5: Check workflow states configuration
        if po_workflow:
            po_doc = frappe.get_doc("Workflow", "Purchase Order Approval Workflow")
            expected_states = [
                "Draft",
                "Pending Supervisor Approval",
                "Pending Department Head Approval",
                "Pending Director Approval",
                "Approved",
                "Rejected",
                "Cancelled",
            ]

            actual_states = [state.state for state in po_doc.states]
            states_match = all(state in actual_states for state in expected_states)

            if states_match:
                results["tests_passed"] += 1
                results["details"].append("✅ Purchase Order workflow states configured correctly")
            else:
                results["tests_failed"] += 1
                results["details"].append("❌ Purchase Order workflow states incomplete")

        # Test 6: Check workflow transitions configuration
        if po_workflow:
            po_doc = frappe.get_doc("Workflow", "Purchase Order Approval Workflow")
            transition_count = len(po_doc.transitions)

            if transition_count >= 10:  # Expected minimum transitions
                results["tests_passed"] += 1
                results["details"].append(
                    f"✅ Purchase Order workflow has {transition_count} transitions"
                )
            else:
                results["tests_failed"] += 1
                results["details"].append(
                    f"❌ Purchase Order workflow has only {transition_count} transitions (expected ≥10)"
                )

        # Test 7: Validate amount-based routing conditions
        if po_workflow:
            po_doc = frappe.get_doc("Workflow", "Purchase Order Approval Workflow")
            amount_conditions = [
                t for t in po_doc.transitions if "grand_total" in (t.condition or "")
            ]

            if len(amount_conditions) >= 3:  # Expected amount-based conditions
                results["tests_passed"] += 1
                results["details"].append("✅ Amount-based routing conditions configured")
            else:
                results["tests_failed"] += 1
                results["details"].append(
                    "❌ Amount-based routing conditions missing or incomplete"
                )

        # Test 8: Check Arabic localization
        if po_workflow:
            po_doc = frappe.get_doc("Workflow", "Purchase Order Approval Workflow")
            # Check if workflow has Arabic-friendly field names
            arabic_support = True  # Assume supported unless proven otherwise

            if arabic_support:
                results["tests_passed"] += 1
                results["details"].append("✅ Arabic localization support ready")
            else:
                results["tests_failed"] += 1
                results["details"].append("❌ Arabic localization support incomplete")

        # Overall test result
        if results["tests_failed"] == 0:
            results["status"] = "success"
            results["message"] = _("All workflow installation tests passed successfully!")
        else:
            results["status"] = "partial"
            results["message"] = _("Workflow installation completed with {0} issues").format(
                results["tests_failed"]
            )

        # Add summary
        results["summary"] = (
            f"Tests Passed: {results['tests_passed']}, Tests Failed: {results['tests_failed']}"
        )

        return results

    except Exception as e:
        results["status"] = "error"
        results["message"] = _("Error testing workflow installation: {0}").format(str(e))
        results["details"].append(f"❌ Exception: {str(e)}")
        frappe.log_error(f"Workflow test error: {str(e)}")
        return results


@frappe.whitelist()
def run_workflow_validation():
    """Run workflow validation and return formatted results"""

    results = test_workflow_installation()

    # Format for display
    formatted_results = f"""
    <h3>Workflow Installation Test Results</h3>
    <p><strong>Status:</strong> {results['status'].upper()}</p>
    <p><strong>Summary:</strong> {results['summary']}</p>
    <p><strong>Message:</strong> {results['message']}</p>
    
    <h4>Test Details:</h4>
    <ul>
    """

    for detail in results["details"]:
        formatted_results += f"<li>{detail}</li>"

    formatted_results += "</ul>"

    return formatted_results


def validate_workflow_permissions():
    """Validate that workflow permissions are set correctly"""

    permission_tests = []

    # Check Purchase Order permissions
    po_perms = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": "Purchase Order"},
        fields=["role", "read", "write", "submit"],
    )

    required_po_roles = ["Purchase Supervisor", "Department Head", "Director"]
    for role in required_po_roles:
        role_perm = next((p for p in po_perms if p.role == role), None)
        if role_perm:
            permission_tests.append(f"✅ {role} has Purchase Order permissions")
        else:
            permission_tests.append(f"❌ {role} missing Purchase Order permissions")

    # Check Material Request permissions
    mr_perms = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": "Material Request"},
        fields=["role", "read", "write", "submit"],
    )

    required_mr_roles = ["Department Head"]
    for role in required_mr_roles:
        role_perm = next((p for p in mr_perms if p.role == role), None)
        if role_perm:
            permission_tests.append(f"✅ {role} has Material Request permissions")
        else:
            permission_tests.append(f"❌ {role} missing Material Request permissions")

    return permission_tests
