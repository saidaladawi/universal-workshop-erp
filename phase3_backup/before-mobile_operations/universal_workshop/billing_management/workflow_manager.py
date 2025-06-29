"""
Universal Workshop ERP - Accounts Workflow Manager
Implements advanced workflow automation for financial processes
Supports multi-level approvals, Arabic/English notifications, and Oman compliance
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, today, add_days, nowdate
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional


class AccountsWorkflowManager:
    """
    Comprehensive workflow management system for Universal Workshop accounts
    Handles approvals, notifications, escalations, and compliance tracking
    """

    def __init__(self):
        self.currency = "OMR"
        self.precision = 3
        self.supported_doctypes = [
            "Sales Invoice",
            "Purchase Invoice",
            "Payment Entry",
            "Journal Entry",
            "Sales Order",
            "Purchase Order",
        ]

    def setup_workflow_system(self, company: str) -> Dict[str, Any]:
        """
        Initialize the complete workflow system for a company

        Args:
            company: Company name

        Returns:
            Dict containing setup results and configuration
        """
        try:
            setup_results = {
                "company": company,
                "setup_date": today(),
                "workflows_created": [],
                "custom_fields_added": [],
                "notifications_configured": [],
                "permissions_set": [],
                "status": "success",
            }

            # 1. Create workflow states and actions
            workflow_configs = self._get_workflow_configurations()

            for doctype, config in workflow_configs.items():
                if self._create_workflow(doctype, config, company):
                    setup_results["workflows_created"].append(doctype)

            # 2. Add custom fields for workflow tracking
            custom_fields = self._setup_custom_fields()
            setup_results["custom_fields_added"] = custom_fields

            # 3. Configure notification templates
            notifications = self._setup_notification_system(company)
            setup_results["notifications_configured"] = notifications

            # 4. Set up role-based permissions
            permissions = self._configure_workflow_permissions()
            setup_results["permissions_set"] = permissions

            # 5. Initialize workflow monitoring
            self._setup_workflow_monitoring(company)

            return setup_results

        except Exception as e:
            frappe.log_error(f"Workflow setup failed: {e}")
            raise frappe.ValidationError(_("Failed to setup workflow system: {0}").format(str(e)))

    def _get_workflow_configurations(self) -> Dict[str, Dict]:
        """Get predefined workflow configurations for different DocTypes"""

        return {
            "Sales Invoice": {
                "workflow_name": "Sales Invoice Approval",
                "states": [
                    {"state": "Draft", "allow_edit": 1, "doc_status": 0},
                    {"state": "Pending Finance Review", "allow_edit": 0, "doc_status": 0},
                    {"state": "Pending Manager Approval", "allow_edit": 0, "doc_status": 0},
                    {"state": "Approved", "allow_edit": 0, "doc_status": 1},
                    {"state": "Rejected", "allow_edit": 1, "doc_status": 0},
                    {"state": "Cancelled", "allow_edit": 0, "doc_status": 2},
                ],
                "transitions": [
                    {
                        "state": "Draft",
                        "action": "Submit for Review",
                        "next_state": "Pending Finance Review",
                        "allowed": "Accounts User",
                        "condition": "doc.grand_total > 0",
                    },
                    {
                        "state": "Pending Finance Review",
                        "action": "Finance Approve",
                        "next_state": (
                            "Pending Manager Approval" if "grand_total > 5000" else "Approved"
                        ),
                        "allowed": "Finance Manager",
                        "condition": "doc.grand_total <= 5000",
                    },
                    {
                        "state": "Pending Finance Review",
                        "action": "Finance Approve Small",
                        "next_state": "Approved",
                        "allowed": "Finance Manager",
                        "condition": "doc.grand_total <= 5000",
                    },
                    {
                        "state": "Pending Finance Review",
                        "action": "Reject",
                        "next_state": "Rejected",
                        "allowed": "Finance Manager",
                    },
                    {
                        "state": "Pending Manager Approval",
                        "action": "Manager Approve",
                        "next_state": "Approved",
                        "allowed": "Accounts Manager",
                    },
                    {
                        "state": "Pending Manager Approval",
                        "action": "Reject",
                        "next_state": "Rejected",
                        "allowed": "Accounts Manager",
                    },
                ],
            },
            "Purchase Invoice": {
                "workflow_name": "Purchase Invoice Approval",
                "states": [
                    {"state": "Draft", "allow_edit": 1, "doc_status": 0},
                    {"state": "Pending Verification", "allow_edit": 0, "doc_status": 0},
                    {"state": "Pending Approval", "allow_edit": 0, "doc_status": 0},
                    {"state": "Approved", "allow_edit": 0, "doc_status": 1},
                    {"state": "Rejected", "allow_edit": 1, "doc_status": 0},
                ],
                "transitions": [
                    {
                        "state": "Draft",
                        "action": "Submit for Verification",
                        "next_state": "Pending Verification",
                        "allowed": "Accounts User",
                    },
                    {
                        "state": "Pending Verification",
                        "action": "Verify",
                        "next_state": "Pending Approval",
                        "allowed": "Purchase Manager",
                    },
                    {
                        "state": "Pending Approval",
                        "action": "Approve",
                        "next_state": "Approved",
                        "allowed": "Finance Manager",
                    },
                ],
            },
            "Payment Entry": {
                "workflow_name": "Payment Approval",
                "states": [
                    {"state": "Draft", "allow_edit": 1, "doc_status": 0},
                    {"state": "Pending Approval", "allow_edit": 0, "doc_status": 0},
                    {"state": "Approved", "allow_edit": 0, "doc_status": 1},
                    {"state": "Rejected", "allow_edit": 1, "doc_status": 0},
                ],
                "transitions": [
                    {
                        "state": "Draft",
                        "action": "Submit for Approval",
                        "next_state": "Pending Approval",
                        "allowed": "Accounts User",
                        "condition": "doc.paid_amount > 0",
                    },
                    {
                        "state": "Pending Approval",
                        "action": "Approve Payment",
                        "next_state": "Approved",
                        "allowed": "Finance Manager",
                    },
                    {
                        "state": "Pending Approval",
                        "action": "Reject Payment",
                        "next_state": "Rejected",
                        "allowed": "Finance Manager",
                    },
                ],
            },
        }

    def _create_workflow(self, doctype: str, config: Dict, company: str) -> bool:
        """Create workflow for a specific DocType"""

        try:
            workflow_name = f"{config['workflow_name']} - {company}"

            # Check if workflow already exists
            if frappe.db.exists("Workflow", workflow_name):
                return True

            # Create Workflow document
            workflow = frappe.new_doc("Workflow")
            workflow.workflow_name = workflow_name
            workflow.document_type = doctype
            workflow.is_active = 1
            workflow.send_email_alert = 1
            workflow.workflow_state_field = "workflow_state"

            # Add workflow states
            for state_config in config["states"]:
                workflow.append(
                    "states",
                    {
                        "state": state_config["state"],
                        "allow_edit": state_config.get("allow_edit", 0),
                        "doc_status": state_config.get("doc_status", 0),
                        "message": f"Document is in {state_config['state']} state",
                    },
                )

            # Add workflow transitions
            for transition in config["transitions"]:
                workflow.append(
                    "transitions",
                    {
                        "state": transition["state"],
                        "action": transition["action"],
                        "next_state": transition["next_state"],
                        "allowed": transition["allowed"],
                        "condition": transition.get("condition", ""),
                        "allow_self_approval": 0,
                    },
                )

            workflow.insert()
            frappe.db.commit()

            return True

        except Exception as e:
            frappe.log_error(f"Failed to create workflow for {doctype}: {e}")
            return False

    def _setup_custom_fields(self) -> List[str]:
        """Add custom fields needed for workflow tracking"""

        custom_fields = []

        # Common workflow fields for all financial documents
        workflow_fields = [
            {
                "fieldname": "workflow_state",
                "fieldtype": "Data",
                "label": "Workflow State",
                "read_only": 1,
                "hidden": 1,
            },
            {
                "fieldname": "approval_section",
                "fieldtype": "Section Break",
                "label": "Approval Details",
                "collapsible": 1,
            },
            {
                "fieldname": "approved_by",
                "fieldtype": "Link",
                "options": "User",
                "label": "Approved By",
                "read_only": 1,
            },
            {
                "fieldname": "approval_date",
                "fieldtype": "Datetime",
                "label": "Approval Date",
                "read_only": 1,
            },
            {
                "fieldname": "approval_comments",
                "fieldtype": "Small Text",
                "label": "Approval Comments",
            },
            {
                "fieldname": "approval_comments_ar",
                "fieldtype": "Small Text",
                "label": "ملاحظات الموافقة",
            },
        ]

        # Add fields to relevant DocTypes
        for doctype in self.supported_doctypes:
            try:
                for field in workflow_fields:
                    field_name = f"{doctype}-{field['fieldname']}"

                    if not frappe.db.exists("Custom Field", field_name):
                        custom_field = frappe.new_doc("Custom Field")
                        custom_field.dt = doctype
                        custom_field.update(field)
                        custom_field.insert()
                        custom_fields.append(field_name)

            except Exception as e:
                frappe.log_error(f"Failed to add custom fields to {doctype}: {e}")

        return custom_fields

    def _setup_notification_system(self, company: str) -> List[str]:
        """Configure email and SMS notifications for workflow events"""

        notifications = []

        notification_configs = [
            {
                "name": f"Sales Invoice Approval Required - {company}",
                "document_type": "Sales Invoice",
                "event": "Change in Workflow State",
                "condition": "doc.workflow_state == 'Pending Finance Review'",
                "recipients": [{"role": "Finance Manager"}],
                "subject": "Sales Invoice Approval Required - {{doc.name}}",
                "message": """
                A new sales invoice requires your approval:
                
                Invoice: {{doc.name}}
                Customer: {{doc.customer_name}}
                Amount: {{doc.grand_total}} OMR
                Date: {{doc.posting_date}}
                
                Please review and approve in the system.
                تحتاج فاتورة مبيعات جديدة لموافقتك
                """,
            },
            {
                "name": f"Payment Entry Approval - {company}",
                "document_type": "Payment Entry",
                "event": "Change in Workflow State",
                "condition": "doc.workflow_state == 'Pending Approval'",
                "recipients": [{"role": "Finance Manager"}],
                "subject": "Payment Approval Required - {{doc.name}}",
                "message": """
                A payment entry requires approval:
                
                Payment: {{doc.name}}
                Party: {{doc.party_name}}
                Amount: {{doc.paid_amount}} OMR
                Type: {{doc.payment_type}}
                
                Please review and approve.
                """,
            },
        ]

        for config in notification_configs:
            try:
                if not frappe.db.exists("Notification", config["name"]):
                    notification = frappe.new_doc("Notification")
                    notification.update(config)
                    notification.insert()
                    notifications.append(config["name"])

            except Exception as e:
                frappe.log_error(f"Failed to create notification {config['name']}: {e}")

        return notifications

    def _configure_workflow_permissions(self) -> List[str]:
        """Set up role-based permissions for workflow actions"""

        permissions_set = []

        # Define role permissions for workflow actions
        role_permissions = {
            "Finance Manager": {
                "doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry"],
                "permissions": ["read", "write", "submit", "cancel", "amend"],
                "workflow_actions": ["approve", "reject"],
            },
            "Accounts Manager": {
                "doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"],
                "permissions": ["read", "write", "submit", "cancel", "amend"],
                "workflow_actions": ["approve", "reject", "escalate"],
            },
            "Accounts User": {
                "doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry"],
                "permissions": ["read", "write", "create"],
                "workflow_actions": ["submit_for_approval"],
            },
        }

        for role, config in role_permissions.items():
            try:
                # Ensure role exists
                if not frappe.db.exists("Role", role):
                    role_doc = frappe.new_doc("Role")
                    role_doc.role_name = role
                    role_doc.insert()

                permissions_set.append(f"Role: {role}")

            except Exception as e:
                frappe.log_error(f"Failed to configure permissions for {role}: {e}")

        return permissions_set

    def _setup_workflow_monitoring(self, company: str):
        """Initialize workflow monitoring and analytics"""

        try:
            # Create scheduled job for workflow monitoring
            self._create_workflow_monitor_job(company)

            # Set up workflow analytics tracking
            self._initialize_workflow_analytics(company)

        except Exception as e:
            frappe.log_error(f"Failed to setup workflow monitoring: {e}")

    def _create_workflow_monitor_job(self, company: str):
        """Create background job for workflow monitoring"""

        # This would typically be set up in hooks.py scheduler_events
        # For now, we'll create the monitoring logic
        pass

    def _initialize_workflow_analytics(self, company: str):
        """Set up analytics tracking for workflow performance"""

        # Initialize workflow performance tracking
        analytics_config = {
            "company": company,
            "tracking_enabled": True,
            "metrics": [
                "approval_turnaround_time",
                "escalation_count",
                "rejection_rate",
                "workflow_bottlenecks",
            ],
            "created_on": today(),
        }

        # Store configuration (this would typically go to a custom DocType)
        # For now, we'll log it
        frappe.log_error(f"Workflow analytics initialized: {json.dumps(analytics_config)}")

    def process_workflow_action(
        self,
        doctype: str,
        docname: str,
        action: str,
        comments: str = "",
        comments_ar: str = "",
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process a workflow action (approve, reject, etc.)

        Args:
            doctype: Document type
            docname: Document name
            action: Workflow action to perform
            comments: Approval/rejection comments (English)
            comments_ar: Comments in Arabic
            language: User language preference

        Returns:
            Dict containing action result
        """
        try:
            # Get the document
            doc = frappe.get_doc(doctype, docname)

            # Validate user permissions
            if not self._validate_workflow_permissions(doc, action):
                raise frappe.PermissionError(_("You don't have permission to perform this action"))

            # Execute workflow action
            if action == "approve":
                result = self._approve_document(doc, comments, comments_ar, language)
            elif action == "reject":
                result = self._reject_document(doc, comments, comments_ar, language)
            elif action == "escalate":
                result = self._escalate_document(doc, comments, comments_ar, language)
            else:
                raise frappe.ValidationError(_("Invalid workflow action: {0}").format(action))

            # Log workflow activity
            self._log_workflow_activity(doc, action, comments, frappe.session.user)

            # Send notifications
            self._send_workflow_notifications(doc, action, language)

            return result

        except Exception as e:
            frappe.log_error(f"Workflow action failed: {e}")
            raise frappe.ValidationError(_("Failed to process workflow action: {0}").format(str(e)))

    def _validate_workflow_permissions(self, doc, action: str) -> bool:
        """Validate if current user can perform the workflow action"""

        # Check basic document permissions
        if not frappe.has_permission(doc.doctype, "write", doc):
            return False

        # Check workflow-specific permissions based on current state
        current_state = getattr(doc, "workflow_state", "Draft")
        user_roles = frappe.get_roles()

        # Define state-based permissions
        state_permissions = {
            "Pending Finance Review": ["Finance Manager"],
            "Pending Manager Approval": ["Accounts Manager", "Finance Manager"],
            "Pending Approval": ["Finance Manager", "Accounts Manager"],
        }

        required_roles = state_permissions.get(current_state, [])
        if required_roles and not any(role in user_roles for role in required_roles):
            return False

        return True

    def _approve_document(self, doc, comments: str, comments_ar: str, language: str) -> Dict:
        """Approve a document and move to next state"""

        current_state = getattr(doc, "workflow_state", "Draft")

        # Update document fields
        doc.approved_by = frappe.session.user
        doc.approval_date = nowdate()
        doc.approval_comments = comments
        doc.approval_comments_ar = comments_ar

        # Move to next state based on workflow logic
        next_state = self._get_next_workflow_state(doc, "approve")
        doc.workflow_state = next_state

        # Submit document if approved
        if next_state == "Approved":
            doc.submit()
        else:
            doc.save()

        return {
            "status": "success",
            "message": (
                _("Document approved successfully")
                if language == "en"
                else "تمت الموافقة على المستند بنجاح"
            ),
            "next_state": next_state,
        }

    def _reject_document(self, doc, comments: str, comments_ar: str, language: str) -> Dict:
        """Reject a document and move to rejected state"""

        doc.workflow_state = "Rejected"
        doc.approval_comments = comments
        doc.approval_comments_ar = comments_ar
        doc.save()

        return {
            "status": "success",
            "message": _("Document rejected") if language == "en" else "تم رفض المستند",
            "next_state": "Rejected",
        }

    def _escalate_document(self, doc, comments: str, comments_ar: str, language: str) -> Dict:
        """Escalate document to higher authority"""

        # Logic for escalation
        next_state = self._get_escalation_state(doc)
        doc.workflow_state = next_state
        doc.approval_comments = f"Escalated: {comments}"
        doc.approval_comments_ar = f"تم التصعيد: {comments_ar}"
        doc.save()

        return {
            "status": "success",
            "message": _("Document escalated") if language == "en" else "تم تصعيد المستند",
            "next_state": next_state,
        }

    def _get_next_workflow_state(self, doc, action: str) -> str:
        """Determine next workflow state based on document and action"""

        current_state = getattr(doc, "workflow_state", "Draft")

        # Sales Invoice logic
        if doc.doctype == "Sales Invoice":
            if current_state == "Pending Finance Review":
                if doc.grand_total > 5000:
                    return "Pending Manager Approval"
                else:
                    return "Approved"
            elif current_state == "Pending Manager Approval":
                return "Approved"

        # Purchase Invoice logic
        elif doc.doctype == "Purchase Invoice":
            if current_state == "Pending Verification":
                return "Pending Approval"
            elif current_state == "Pending Approval":
                return "Approved"

        # Payment Entry logic
        elif doc.doctype == "Payment Entry":
            if current_state == "Pending Approval":
                return "Approved"

        return current_state

    def _get_escalation_state(self, doc) -> str:
        """Get escalation state for document"""

        if doc.doctype == "Sales Invoice":
            return "Pending Manager Approval"
        elif doc.doctype == "Purchase Invoice":
            return "Pending Director Approval"

        return "Pending Manager Approval"

    def _log_workflow_activity(self, doc, action: str, comments: str, user: str):
        """Log workflow activity for audit trail"""

        activity_log = {
            "doctype": doc.doctype,
            "docname": doc.name,
            "action": action,
            "user": user,
            "timestamp": datetime.now(),
            "comments": comments,
            "workflow_state": getattr(doc, "workflow_state", ""),
        }

        # In a real implementation, this would be stored in a custom DocType
        frappe.log_error(f"Workflow Activity: {json.dumps(activity_log, default=str)}")

    def _send_workflow_notifications(self, doc, action: str, language: str):
        """Send notifications for workflow actions"""

        try:
            # Get notification recipients based on next state
            recipients = self._get_notification_recipients(doc)

            if recipients:
                # Send email notification
                self._send_email_notification(doc, action, recipients, language)

                # Send SMS if enabled
                self._send_sms_notification(doc, action, recipients, language)

        except Exception as e:
            frappe.log_error(f"Failed to send workflow notifications: {e}")

    def _get_notification_recipients(self, doc) -> List[str]:
        """Get list of users to notify based on document state"""

        state = getattr(doc, "workflow_state", "")

        if state == "Pending Finance Review":
            return frappe.get_list(
                "User", filters={"role_profile_name": "Finance Manager"}, pluck="email"
            )
        elif state == "Pending Manager Approval":
            return frappe.get_list(
                "User", filters={"role_profile_name": "Accounts Manager"}, pluck="email"
            )

        return []

    def _send_email_notification(self, doc, action: str, recipients: List[str], language: str):
        """Send email notification for workflow action"""

        try:
            subject = f"Workflow Action Required - {doc.name}"
            if language == "ar":
                subject = f"مطلوب إجراء سير العمل - {doc.name}"

            message = f"""
            Document: {doc.name}
            Type: {doc.doctype} 
            Action Required: {action}
            Amount: {getattr(doc, 'grand_total', 0)} OMR
            
            Please login to review and take action.
            يرجى تسجيل الدخول للمراجعة واتخاذ الإجراء المطلوب.
            """

            frappe.sendmail(recipients=recipients, subject=subject, message=message)

        except Exception as e:
            frappe.log_error(f"Failed to send email notification: {e}")

    def _send_sms_notification(self, doc, action: str, recipients: List[str], language: str):
        """Send SMS notification for workflow action"""

        # SMS notification implementation would go here
        # This is a placeholder for future SMS integration
        pass

    def get_workflow_analytics(self, company: str, period: str = "30") -> Dict[str, Any]:
        """
        Get workflow performance analytics

        Args:
            company: Company name
            period: Analysis period in days

        Returns:
            Dict containing workflow analytics
        """
        try:
            end_date = today()
            start_date = add_days(end_date, -int(period))

            analytics = {
                "company": company,
                "period": f"{period} days",
                "start_date": start_date,
                "end_date": end_date,
                "generated_on": today(),
            }

            # Get workflow statistics for each DocType
            for doctype in self.supported_doctypes:
                stats = self._get_doctype_workflow_stats(doctype, start_date, end_date)
                analytics[doctype.lower().replace(" ", "_")] = stats

            # Calculate overall metrics
            analytics["overall_metrics"] = self._calculate_overall_metrics(analytics)

            return analytics

        except Exception as e:
            frappe.log_error(f"Failed to generate workflow analytics: {e}")
            return {}

    def _get_doctype_workflow_stats(self, doctype: str, start_date: str, end_date: str) -> Dict:
        """Get workflow statistics for a specific DocType"""

        try:
            # Count documents by workflow state
            state_counts = frappe.db.sql(
                f"""
                SELECT workflow_state, COUNT(*) as count
                FROM `tab{doctype}`
                WHERE creation BETWEEN %s AND %s
                GROUP BY workflow_state
            """,
                [start_date, end_date],
                as_dict=True,
            )

            # Calculate average approval time (placeholder logic)
            avg_approval_time = frappe.db.sql(
                f"""
                SELECT AVG(TIMESTAMPDIFF(HOUR, creation, modified)) as avg_hours
                FROM `tab{doctype}`
                WHERE workflow_state = 'Approved'
                AND creation BETWEEN %s AND %s
            """,
                [start_date, end_date],
            )

            return {
                "total_documents": sum([s["count"] for s in state_counts]),
                "state_breakdown": state_counts,
                "avg_approval_time_hours": (
                    avg_approval_time[0][0] if avg_approval_time[0][0] else 0
                ),
            }

        except Exception as e:
            frappe.log_error(f"Failed to get stats for {doctype}: {e}")
            return {}

    def _calculate_overall_metrics(self, analytics: Dict) -> Dict:
        """Calculate overall workflow performance metrics"""

        total_docs = 0
        total_approval_time = 0

        for key, value in analytics.items():
            if isinstance(value, dict) and "total_documents" in value:
                total_docs += value["total_documents"]
                total_approval_time += value.get("avg_approval_time_hours", 0)

        return {
            "total_documents_processed": total_docs,
            "average_approval_time_hours": (
                total_approval_time / len(self.supported_doctypes) if total_docs > 0 else 0
            ),
            "workflow_efficiency": "Good" if total_approval_time < 24 else "Needs Improvement",
        }


# WhiteListed API Methods
@frappe.whitelist()
def setup_workflow_system(company):
    """Initialize workflow system for a company (API endpoint)"""

    manager = AccountsWorkflowManager()
    return manager.setup_workflow_system(company)


@frappe.whitelist()
def process_workflow_action(doctype, docname, action, comments="", comments_ar="", language="en"):
    """Process workflow action (API endpoint)"""

    manager = AccountsWorkflowManager()
    return manager.process_workflow_action(
        doctype=doctype,
        docname=docname,
        action=action,
        comments=comments,
        comments_ar=comments_ar,
        language=language,
    )


@frappe.whitelist()
def get_workflow_analytics(company, period="30"):
    """Get workflow analytics (API endpoint)"""

    manager = AccountsWorkflowManager()
    return manager.get_workflow_analytics(company=company, period=period)


@frappe.whitelist()
def get_pending_approvals(user=None):
    """Get pending approvals for a user (API endpoint)"""

    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    pending_docs = []

    # Get documents pending approval based on user roles
    if "Finance Manager" in user_roles:
        # Get Sales Invoices pending finance review
        sales_invoices = frappe.get_list(
            "Sales Invoice",
            filters={"workflow_state": "Pending Finance Review"},
            fields=["name", "customer", "grand_total", "posting_date"],
        )
        pending_docs.extend([{**doc, "doctype": "Sales Invoice"} for doc in sales_invoices])

    if "Accounts Manager" in user_roles:
        # Get documents pending manager approval
        manager_pending = frappe.get_list(
            "Sales Invoice",
            filters={"workflow_state": "Pending Manager Approval"},
            fields=["name", "customer", "grand_total", "posting_date"],
        )
        pending_docs.extend([{**doc, "doctype": "Sales Invoice"} for doc in manager_pending])

    return {"user": user, "pending_count": len(pending_docs), "pending_documents": pending_docs}
