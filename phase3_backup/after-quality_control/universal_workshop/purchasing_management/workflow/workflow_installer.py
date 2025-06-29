import frappe
import json
import os
from frappe import _
from frappe.utils import nowdate, add_days


def install_approval_workflows():
    """Install Purchase Order and Material Request approval workflows"""

    try:
        # Install Purchase Order workflow
        install_purchase_order_workflow()

        # Install Material Request workflow
        install_material_request_workflow()

        # Create notification templates
        create_notification_templates()

        # Set up roles and permissions
        setup_workflow_roles()

        frappe.db.commit()
        frappe.msgprint(_("Approval workflows installed successfully"))

    except Exception as e:
        frappe.log_error(f"Error installing workflows: {str(e)}")
        frappe.throw(_("Error installing workflows: {0}").format(str(e)))


def install_purchase_order_workflow():
    """Install Purchase Order approval workflow"""

    workflow_name = "Purchase Order Approval Workflow"

    # Check if workflow already exists
    if frappe.db.exists("Workflow", workflow_name):
        frappe.delete_doc("Workflow", workflow_name)

    # Create workflow document
    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = workflow_name
    workflow.document_type = "Purchase Order"
    workflow.is_active = 1
    workflow.send_email_alert = 1
    workflow.workflow_state_field = "workflow_state"
    workflow.override_status = 1

    # Add workflow states
    states = [
        {
            "state": "Draft",
            "allow_edit": "Purchase Manager,Purchase User",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Purchase Order is in draft state",
            "next_state": "Pending Supervisor Approval",
        },
        {
            "state": "Pending Supervisor Approval",
            "allow_edit": "Purchase Supervisor",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Waiting for supervisor approval",
            "next_state": "Pending Department Head Approval,Approved,Rejected",
        },
        {
            "state": "Pending Department Head Approval",
            "allow_edit": "Department Head",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Waiting for department head approval",
            "next_state": "Pending Director Approval,Approved,Rejected",
        },
        {
            "state": "Pending Director Approval",
            "allow_edit": "Director",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Waiting for director approval",
            "next_state": "Approved,Rejected",
        },
        {
            "state": "Approved",
            "allow_edit": "",
            "doc_status": "1",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Purchase Order has been approved",
            "next_state": "",
        },
        {
            "state": "Rejected",
            "allow_edit": "Purchase Manager",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Purchase Order has been rejected",
            "next_state": "Draft",
        },
        {
            "state": "Cancelled",
            "allow_edit": "",
            "doc_status": "2",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Purchase Order has been cancelled",
            "next_state": "",
        },
    ]

    for state in states:
        workflow.append("states", state)

    # Add workflow transitions
    transitions = [
        {
            "state": "Draft",
            "action": "Submit for Approval",
            "next_state": "Pending Supervisor Approval",
            "allowed": "Purchase Manager,Purchase User",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Supervisor Approval",
            "action": "Approve (Low Value)",
            "next_state": "Approved",
            "allowed": "Purchase Supervisor",
            "condition": "doc.grand_total <= 5000",
            "action_master": "",
        },
        {
            "state": "Pending Supervisor Approval",
            "action": "Forward to Department Head",
            "next_state": "Pending Department Head Approval",
            "allowed": "Purchase Supervisor",
            "condition": "doc.grand_total > 5000 and doc.grand_total <= 20000",
            "action_master": "",
        },
        {
            "state": "Pending Supervisor Approval",
            "action": "Forward to Director",
            "next_state": "Pending Director Approval",
            "allowed": "Purchase Supervisor",
            "condition": "doc.grand_total > 20000",
            "action_master": "",
        },
        {
            "state": "Pending Department Head Approval",
            "action": "Approve (Medium Value)",
            "next_state": "Approved",
            "allowed": "Department Head",
            "condition": "doc.grand_total <= 20000",
            "action_master": "",
        },
        {
            "state": "Pending Department Head Approval",
            "action": "Forward to Director",
            "next_state": "Pending Director Approval",
            "allowed": "Department Head",
            "condition": "doc.grand_total > 20000",
            "action_master": "",
        },
        {
            "state": "Pending Director Approval",
            "action": "Approve (High Value)",
            "next_state": "Approved",
            "allowed": "Director",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Supervisor Approval",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Purchase Supervisor,Department Head,Director",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Department Head Approval",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Department Head,Director",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Director Approval",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Director",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Rejected",
            "action": "Revise",
            "next_state": "Draft",
            "allowed": "Purchase Manager",
            "condition": "",
            "action_master": "",
        },
    ]

    for transition in transitions:
        workflow.append("transitions", transition)

    workflow.insert()
    workflow.save()


def install_material_request_workflow():
    """Install Material Request approval workflow"""

    workflow_name = "Material Request Approval Workflow"

    # Check if workflow already exists
    if frappe.db.exists("Workflow", workflow_name):
        frappe.delete_doc("Workflow", workflow_name)

    # Create workflow document
    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = workflow_name
    workflow.document_type = "Material Request"
    workflow.is_active = 1
    workflow.send_email_alert = 1
    workflow.workflow_state_field = "workflow_state"
    workflow.override_status = 1

    # Add workflow states
    states = [
        {
            "state": "Draft",
            "allow_edit": "Stock User,Purchase User",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Material Request is in draft state",
            "next_state": "Pending Department Approval",
        },
        {
            "state": "Pending Department Approval",
            "allow_edit": "Department Head",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Waiting for department approval",
            "next_state": "Pending Purchase Approval,Approved,Rejected",
        },
        {
            "state": "Pending Purchase Approval",
            "allow_edit": "Purchase Manager",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "",
            "update_value": "",
            "message": "Waiting for purchase manager approval",
            "next_state": "Approved,Rejected",
        },
        {
            "state": "Approved",
            "allow_edit": "",
            "doc_status": "1",
            "is_optional_state": 0,
            "update_field": "status",
            "update_value": "Approved",
            "message": "Material Request has been approved",
            "next_state": "Ordered,Partially Ordered",
        },
        {
            "state": "Rejected",
            "allow_edit": "Stock User",
            "doc_status": "0",
            "is_optional_state": 0,
            "update_field": "status",
            "update_value": "Rejected",
            "message": "Material Request has been rejected",
            "next_state": "Draft",
        },
        {
            "state": "Ordered",
            "allow_edit": "",
            "doc_status": "1",
            "is_optional_state": 0,
            "update_field": "status",
            "update_value": "Ordered",
            "message": "Material Request has been ordered",
            "next_state": "Received,Partially Received",
        },
        {
            "state": "Received",
            "allow_edit": "",
            "doc_status": "1",
            "is_optional_state": 0,
            "update_field": "status",
            "update_value": "Received",
            "message": "Material Request has been received",
            "next_state": "",
        },
    ]

    for state in states:
        workflow.append("states", state)

    # Add workflow transitions
    transitions = [
        {
            "state": "Draft",
            "action": "Submit for Approval",
            "next_state": "Pending Department Approval",
            "allowed": "Stock User,Purchase User",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Department Approval",
            "action": "Approve (Standard Items)",
            "next_state": "Approved",
            "allowed": "Department Head",
            "condition": "doc.priority != 'High' and (doc.estimated_cost or 0) <= 10000",
            "action_master": "",
        },
        {
            "state": "Pending Department Approval",
            "action": "Forward to Purchase Manager",
            "next_state": "Pending Purchase Approval",
            "allowed": "Department Head",
            "condition": "doc.priority == 'High' or (doc.estimated_cost or 0) > 10000",
            "action_master": "",
        },
        {
            "state": "Pending Purchase Approval",
            "action": "Approve (High Priority/Value)",
            "next_state": "Approved",
            "allowed": "Purchase Manager",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Department Approval",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Department Head,Purchase Manager",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Pending Purchase Approval",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Purchase Manager",
            "condition": "",
            "action_master": "",
        },
        {
            "state": "Rejected",
            "action": "Revise",
            "next_state": "Draft",
            "allowed": "Stock User",
            "condition": "",
            "action_master": "",
        },
    ]

    for transition in transitions:
        workflow.append("transitions", transition)

    workflow.insert()
    workflow.save()


def create_notification_templates():
    """Create notification templates for workflows"""

    # Purchase Order approval notifications
    po_notifications = [
        {
            "name": "Purchase Order Approval Required",
            "document_type": "Purchase Order",
            "subject": "Purchase Order Approval Required - {{ doc.name }}",
            "message": """
            <p>Dear {{ user.full_name }},</p>
            <p>Purchase Order {{ doc.name }} requires your approval.</p>
            <p><strong>Supplier:</strong> {{ doc.supplier }}</p>
            <p><strong>Amount:</strong> {{ doc.formatted_grand_total }}</p>
            <p><strong>Required Date:</strong> {{ doc.schedule_date }}</p>
            <p>Please review and approve at your earliest convenience.</p>
            <p>Best regards,<br>Universal Workshop ERP</p>
            """,
            "condition": "doc.workflow_state in ['Pending Supervisor Approval', 'Pending Department Head Approval', 'Pending Director Approval']",
            "event": "Change",
            "recipients": [
                {"receiver_by_document_field": "", "receiver_by_role": "Purchase Supervisor"}
            ],
        },
        {
            "name": "Purchase Order Approved Notification",
            "document_type": "Purchase Order",
            "subject": "Purchase Order Approved - {{ doc.name }}",
            "message": """
            <p>Dear {{ user.full_name }},</p>
            <p>Your Purchase Order {{ doc.name }} has been approved.</p>
            <p><strong>Supplier:</strong> {{ doc.supplier }}</p>
            <p><strong>Amount:</strong> {{ doc.formatted_grand_total }}</p>
            <p>You can now proceed with the order processing.</p>
            <p>Best regards,<br>Universal Workshop ERP</p>
            """,
            "condition": "doc.workflow_state == 'Approved'",
            "event": "Change",
            "recipients": [{"receiver_by_document_field": "owner", "receiver_by_role": ""}],
        },
    ]

    # Material Request approval notifications
    mr_notifications = [
        {
            "name": "Material Request Approval Required",
            "document_type": "Material Request",
            "subject": "Material Request Approval Required - {{ doc.name }}",
            "message": """
            <p>Dear {{ user.full_name }},</p>
            <p>Material Request {{ doc.name }} requires your approval.</p>
            <p><strong>Priority:</strong> {{ doc.priority }}</p>
            <p><strong>Estimated Cost:</strong> {{ doc.formatted_estimated_cost or 'Not specified' }}</p>
            <p><strong>Required Date:</strong> {{ doc.schedule_date }}</p>
            <p>Please review and approve at your earliest convenience.</p>
            <p>Best regards,<br>Universal Workshop ERP</p>
            """,
            "condition": "doc.workflow_state in ['Pending Department Approval', 'Pending Purchase Approval']",
            "event": "Change",
            "recipients": [
                {"receiver_by_document_field": "", "receiver_by_role": "Department Head"}
            ],
        }
    ]

    # Create notification documents
    all_notifications = po_notifications + mr_notifications

    for notification in all_notifications:
        if not frappe.db.exists("Notification", notification["name"]):
            doc = frappe.new_doc("Notification")
            doc.subject = notification["subject"]
            doc.document_type = notification["document_type"]
            doc.message = notification["message"]
            doc.condition = notification["condition"]
            doc.event = notification["event"]
            doc.enabled = 1

            for recipient in notification["recipients"]:
                doc.append("recipients", recipient)

            doc.insert()


def setup_workflow_roles():
    """Set up roles and permissions for workflow"""

    # Create custom roles if they don't exist
    roles = ["Purchase Supervisor", "Department Head", "Director"]

    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.insert()

    # Set up permissions for Purchase Order
    po_permissions = [
        {
            "role": "Purchase Supervisor",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "submit": 1,
            "cancel": 0,
            "delete": 0,
        },
        {
            "role": "Department Head",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "submit": 1,
            "cancel": 0,
            "delete": 0,
        },
        {
            "role": "Director",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "submit": 1,
            "cancel": 1,
            "delete": 1,
        },
    ]

    # Set up permissions for Material Request
    mr_permissions = [
        {
            "role": "Department Head",
            "permlevel": 0,
            "read": 1,
            "write": 1,
            "submit": 1,
            "cancel": 0,
            "delete": 0,
        }
    ]

    # Apply permissions
    for perm in po_permissions:
        if not frappe.db.exists(
            "Custom DocPerm", {"parent": "Purchase Order", "role": perm["role"]}
        ):
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "Purchase Order",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": perm["role"],
                    "permlevel": perm["permlevel"],
                    "read": perm["read"],
                    "write": perm["write"],
                    "submit": perm["submit"],
                    "cancel": perm["cancel"],
                    "delete": perm["delete"],
                }
            ).insert()

    for perm in mr_permissions:
        if not frappe.db.exists(
            "Custom DocPerm", {"parent": "Material Request", "role": perm["role"]}
        ):
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "Material Request",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": perm["role"],
                    "permlevel": perm["permlevel"],
                    "read": perm["read"],
                    "write": perm["write"],
                    "submit": perm["submit"],
                    "cancel": perm["cancel"],
                    "delete": perm["delete"],
                }
            ).insert()


@frappe.whitelist()
def get_workflow_status_dashboard():
    """Get workflow status dashboard data"""

    # Purchase Orders by workflow state
    po_data = frappe.db.sql(
        """
        SELECT workflow_state, COUNT(*) as count
        FROM `tabPurchase Order`
        WHERE workflow_state IS NOT NULL
        GROUP BY workflow_state
    """,
        as_dict=True,
    )

    # Material Requests by workflow state
    mr_data = frappe.db.sql(
        """
        SELECT workflow_state, COUNT(*) as count
        FROM `tabMaterial Request`
        WHERE workflow_state IS NOT NULL
        GROUP BY workflow_state
    """,
        as_dict=True,
    )

    # Pending approvals by role
    pending_approvals = frappe.db.sql(
        """
        SELECT 
            'Purchase Order' as doctype,
            workflow_state,
            COUNT(*) as count
        FROM `tabPurchase Order`
        WHERE workflow_state IN ('Pending Supervisor Approval', 'Pending Department Head Approval', 'Pending Director Approval')
        
        UNION ALL
        
        SELECT 
            'Material Request' as doctype,
            workflow_state,
            COUNT(*) as count
        FROM `tabMaterial Request`
        WHERE workflow_state IN ('Pending Department Approval', 'Pending Purchase Approval')
    """,
        as_dict=True,
    )

    return {
        "purchase_orders": po_data,
        "material_requests": mr_data,
        "pending_approvals": pending_approvals,
    }


@frappe.whitelist()
def bulk_approve_documents(doctype, names, action="approve"):
    """Bulk approve workflow documents"""

    if not isinstance(names, list):
        names = [names]

    results = {"success": [], "failed": []}

    for name in names:
        try:
            doc = frappe.get_doc(doctype, name)

            # Check if user has permission to approve
            if action == "approve":
                if doctype == "Purchase Order":
                    if (
                        doc.workflow_state == "Pending Supervisor Approval"
                        and frappe.has_permission(doctype, "write", doc)
                        and "Purchase Supervisor" in frappe.get_roles()
                    ):
                        doc.workflow_state = (
                            "Approved"
                            if doc.grand_total <= 5000
                            else "Pending Department Head Approval"
                        )
                    elif (
                        doc.workflow_state == "Pending Department Head Approval"
                        and "Department Head" in frappe.get_roles()
                    ):
                        doc.workflow_state = (
                            "Approved" if doc.grand_total <= 20000 else "Pending Director Approval"
                        )
                    elif (
                        doc.workflow_state == "Pending Director Approval"
                        and "Director" in frappe.get_roles()
                    ):
                        doc.workflow_state = "Approved"

                elif doctype == "Material Request":
                    if (
                        doc.workflow_state == "Pending Department Approval"
                        and "Department Head" in frappe.get_roles()
                    ):
                        doc.workflow_state = (
                            "Approved"
                            if doc.priority != "High" and (doc.estimated_cost or 0) <= 10000
                            else "Pending Purchase Approval"
                        )
                    elif (
                        doc.workflow_state == "Pending Purchase Approval"
                        and "Purchase Manager" in frappe.get_roles()
                    ):
                        doc.workflow_state = "Approved"

            doc.save()
            results["success"].append(name)

        except Exception as e:
            results["failed"].append({"name": name, "error": str(e)})

    return results
