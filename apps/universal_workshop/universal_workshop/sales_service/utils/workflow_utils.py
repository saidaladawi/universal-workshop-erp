import frappe
from frappe import _
from frappe.utils import now, today, get_datetime
from frappe.workflow.doctype.workflow_action.workflow_action import get_workflow_name
import json


class WorkflowUtils:
    """Utility class for handling workflow operations in Return and Exchange systems"""

    @staticmethod
    def update_return_request_fields(doc, method=None):
        """Update Return Request fields based on workflow state"""
        if not hasattr(doc, "workflow_state") or not doc.workflow_state:
            return

        # Map workflow states to internal status
        state_mapping = {
            "Draft": "Draft",
            "Pending Review": "Pending Review",
            "Under Investigation": "Under Investigation",
            "Approved": "Approved",
            "Rejected": "Rejected",
            "Processing": "Processing",
            "Completed": "Completed",
            "Cancelled": "Cancelled",
        }

        if doc.workflow_state in state_mapping:
            doc.return_status = state_mapping[doc.workflow_state]

        # Update approval fields
        if doc.workflow_state == "Approved" and not doc.approved_by:
            doc.approved_by = frappe.session.user
            doc.approval_date = now()

        # Update processing fields
        if doc.workflow_state == "Processing" and not doc.processed_by:
            doc.processed_by = frappe.session.user
            doc.processing_date = now()

        # Handle auto-processing for simple returns
        if (
            doc.workflow_state == "Approved"
            and doc.auto_approved
            and doc.fraud_risk_level == "Low"
            and doc.return_value <= 50
        ):  # Auto-process small returns

            try:
                doc.process_return()
                doc.workflow_state = "Completed"
            except Exception as e:
                frappe.log_error(f"Auto-processing failed for return {doc.name}: {str(e)}")

    @staticmethod
    def update_exchange_request_fields(doc, method=None):
        """Update Exchange Request fields based on workflow state"""
        if not hasattr(doc, "workflow_state") or not doc.workflow_state:
            return

        # Map workflow states to internal status
        state_mapping = {
            "Draft": "Draft",
            "Pending Approval": "Pending Approval",
            "Compatibility Review": "Pending Approval",
            "Manager Approval": "Pending Approval",
            "Inventory Check": "Pending Approval",
            "Approved": "Approved",
            "Rejected": "Rejected",
            "Processing": "Processing",
            "Awaiting Payment": "Processing",
            "Completed": "Processed",
            "Cancelled": "Cancelled",
        }

        if doc.workflow_state in state_mapping:
            doc.exchange_status = state_mapping[doc.workflow_state]

        # Update approval fields
        if doc.workflow_state == "Approved" and not doc.approved_by:
            doc.approved_by = frappe.session.user
            doc.approval_date = now()

        # Update processing fields
        if doc.workflow_state == "Processing" and not doc.processed_by:
            doc.processed_by = frappe.session.user
            doc.processing_date = now()

        # Handle auto-processing for simple exchanges
        if (
            doc.workflow_state == "Approved"
            and doc.auto_approved
            and doc.risk_level == "Low"
            and doc.availability_status == "Available"
            and abs(doc.price_difference) <= 25
        ):  # Auto-process small exchanges

            try:
                doc.process_exchange()
                doc.workflow_state = "Completed"
            except Exception as e:
                frappe.log_error(f"Auto-processing failed for exchange {doc.name}: {str(e)}")

    @staticmethod
    def send_workflow_notification(doc, method=None):
        """Send notifications when workflow state changes"""
        if not hasattr(doc, "workflow_state"):
            return

        # Get previous state from database
        if doc.is_new():
            previous_state = None
        else:
            previous_state = frappe.db.get_value(doc.doctype, doc.name, "workflow_state")

        # Only send notification if state actually changed
        if previous_state == doc.workflow_state:
            return

        try:
            notification_data = WorkflowUtils.get_notification_data(
                doc, previous_state, doc.workflow_state
            )

            if notification_data:
                WorkflowUtils.send_email_notification(doc, notification_data)
                WorkflowUtils.create_system_notification(doc, notification_data)

        except Exception as e:
            frappe.log_error(
                f"Error sending workflow notification for {doc.doctype} {doc.name}: {str(e)}"
            )

    @staticmethod
    def get_notification_data(doc, previous_state, current_state):
        """Get notification data based on document type and state change"""
        notifications = {
            "Return Request": {
                "Pending Review": {
                    "subject": _("طلب استرداد في انتظار المراجعة / Return Request Pending Review"),
                    "message": _(
                        "طلب الاسترداد {0} في انتظار المراجعة / Return request {0} is pending review"
                    ).format(doc.name),
                    "recipients": ["Service Advisor", "Workshop Manager"],
                    "customer_message": _(
                        "تم استلام طلب الاسترداد الخاص بك وهو قيد المراجعة / Your return request has been received and is under review"
                    ),
                },
                "Approved": {
                    "subject": _("تم الموافقة على طلب الاسترداد / Return Request Approved"),
                    "message": _(
                        "تم الموافقة على طلب الاسترداد {0} / Return request {0} has been approved"
                    ).format(doc.name),
                    "recipients": ["Inventory Manager", "Accounts Manager"],
                    "customer_message": _(
                        "تم الموافقة على طلب الاسترداد الخاص بك / Your return request has been approved"
                    ),
                },
                "Rejected": {
                    "subject": _("تم رفض طلب الاسترداد / Return Request Rejected"),
                    "message": _(
                        "تم رفض طلب الاسترداد {0} / Return request {0} has been rejected"
                    ).format(doc.name),
                    "recipients": [],
                    "customer_message": _(
                        "عذراً، تم رفض طلب الاسترداد الخاص بك / Sorry, your return request has been rejected"
                    ),
                },
                "Completed": {
                    "subject": _("تم إنجاز طلب الاسترداد / Return Request Completed"),
                    "message": _(
                        "تم إنجاز طلب الاسترداد {0} بنجاح / Return request {0} has been completed successfully"
                    ).format(doc.name),
                    "recipients": [],
                    "customer_message": _(
                        "تم إنجاز طلب الاسترداد الخاص بك بنجاح / Your return request has been completed successfully"
                    ),
                },
            },
            "Exchange Request": {
                "Pending Approval": {
                    "subject": _(
                        "طلب تبديل في انتظار الموافقة / Exchange Request Pending Approval"
                    ),
                    "message": _(
                        "طلب التبديل {0} في انتظار الموافقة / Exchange request {0} is pending approval"
                    ).format(doc.name),
                    "recipients": ["Service Advisor", "Workshop Manager"],
                    "customer_message": _(
                        "تم استلام طلب التبديل الخاص بك وهو قيد المراجعة / Your exchange request has been received and is under review"
                    ),
                },
                "Manager Approval": {
                    "subject": _(
                        "طلب تبديل يتطلب موافقة المدير / Exchange Request Requires Manager Approval"
                    ),
                    "message": _(
                        "طلب التبديل {0} يتطلب موافقة المدير / Exchange request {0} requires manager approval"
                    ).format(doc.name),
                    "recipients": ["Workshop Manager", "General Manager"],
                    "customer_message": _(
                        "طلب التبديل الخاص بك قيد المراجعة من قبل الإدارة / Your exchange request is under management review"
                    ),
                },
                "Approved": {
                    "subject": _("تم الموافقة على طلب التبديل / Exchange Request Approved"),
                    "message": _(
                        "تم الموافقة على طلب التبديل {0} / Exchange request {0} has been approved"
                    ).format(doc.name),
                    "recipients": ["Inventory Manager", "Customer Service Representative"],
                    "customer_message": _(
                        "تم الموافقة على طلب التبديل الخاص بك / Your exchange request has been approved"
                    ),
                },
                "Awaiting Payment": {
                    "subject": _("طلب تبديل في انتظار الدفع / Exchange Request Awaiting Payment"),
                    "message": _(
                        "طلب التبديل {0} في انتظار دفع فرق السعر / Exchange request {0} is awaiting payment"
                    ).format(doc.name),
                    "recipients": ["Accounts Manager", "Customer Service Representative"],
                    "customer_message": _(
                        "يرجى دفع فرق السعر لإكمال التبديل / Please pay the price difference to complete the exchange"
                    ),
                },
                "Completed": {
                    "subject": _("تم إنجاز طلب التبديل / Exchange Request Completed"),
                    "message": _(
                        "تم إنجاز طلب التبديل {0} بنجاح / Exchange request {0} has been completed successfully"
                    ).format(doc.name),
                    "recipients": [],
                    "customer_message": _(
                        "تم إنجاز طلب التبديل الخاص بك بنجاح / Your exchange request has been completed successfully"
                    ),
                },
            },
        }

        return notifications.get(doc.doctype, {}).get(current_state)

    @staticmethod
    def send_email_notification(doc, notification_data):
        """Send email notification to relevant users"""
        try:
            # Send to customer
            if hasattr(doc, "customer") and doc.customer:
                customer_doc = frappe.get_doc("Customer", doc.customer)
                if customer_doc.email_id and notification_data.get("customer_message"):
                    frappe.sendmail(
                        recipients=[customer_doc.email_id],
                        subject=notification_data["subject"],
                        message=notification_data["customer_message"],
                        reference_doctype=doc.doctype,
                        reference_name=doc.name,
                    )

            # Send to internal users based on roles
            if notification_data.get("recipients"):
                internal_users = []
                for role in notification_data["recipients"]:
                    role_users = frappe.get_list(
                        "Has Role", filters={"role": role, "parenttype": "User"}, fields=["parent"]
                    )
                    for user in role_users:
                        user_email = frappe.db.get_value("User", user.parent, "email")
                        if user_email and user_email not in internal_users:
                            internal_users.append(user_email)

                if internal_users:
                    frappe.sendmail(
                        recipients=internal_users,
                        subject=notification_data["subject"],
                        message=notification_data["message"],
                        reference_doctype=doc.doctype,
                        reference_name=doc.name,
                    )

        except Exception as e:
            frappe.log_error(f"Error sending email notification: {str(e)}")

    @staticmethod
    def create_system_notification(doc, notification_data):
        """Create system notification for workflow state change"""
        try:
            # Create notification for assigned users
            if notification_data.get("recipients"):
                for role in notification_data["recipients"]:
                    role_users = frappe.get_list(
                        "Has Role", filters={"role": role, "parenttype": "User"}, fields=["parent"]
                    )

                    for user in role_users:
                        notification = frappe.new_doc("Notification Log")
                        notification.subject = notification_data["subject"]
                        notification.email_content = notification_data["message"]
                        notification.for_user = user.parent
                        notification.document_type = doc.doctype
                        notification.document_name = doc.name
                        notification.from_user = frappe.session.user
                        notification.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Error creating system notification: {str(e)}")

    @staticmethod
    def validate_workflow_conditions(doc, method=None):
        """Validate workflow conditions before state changes"""
        if not hasattr(doc, "workflow_state"):
            return

        # Return Request validations
        if doc.doctype == "Return Request":
            WorkflowUtils.validate_return_conditions(doc)

        # Exchange Request validations
        elif doc.doctype == "Exchange Request":
            WorkflowUtils.validate_exchange_conditions(doc)

    @staticmethod
    def validate_return_conditions(doc):
        """Validate conditions specific to Return Request"""
        if doc.workflow_state == "Approved":
            if not doc.eligible_for_return:
                frappe.throw(
                    _(
                        "لا يمكن الموافقة على طلب غير مؤهل للاسترداد / Cannot approve ineligible return request"
                    )
                )

            if doc.fraud_risk_level == "High" and not frappe.has_permission(
                "Return Request", "write", user=frappe.session.user
            ):
                frappe.throw(
                    _(
                        "طلبات الاسترداد عالية المخاطر تتطلب صلاحيات خاصة / High-risk returns require special permissions"
                    )
                )

        elif doc.workflow_state == "Processing":
            if doc.return_status != "Approved":
                frappe.throw(_("يجب الموافقة على الطلب أولاً / Request must be approved first"))

        elif doc.workflow_state == "Completed":
            if not doc.stock_entry or not doc.credit_note:
                frappe.throw(
                    _(
                        "يجب إنشاء قيد المخزون والإشعار الائتماني أولاً / Stock entry and credit note must be created first"
                    )
                )

    @staticmethod
    def validate_exchange_conditions(doc):
        """Validate conditions specific to Exchange Request"""
        if doc.workflow_state == "Approved":
            if not doc.eligible_for_exchange:
                frappe.throw(
                    _(
                        "لا يمكن الموافقة على طلب تبديل غير مؤهل / Cannot approve ineligible exchange request"
                    )
                )

            if doc.availability_status != "Available":
                frappe.throw(_("القطعة البديلة غير متوفرة / Exchange item is not available"))

            if doc.risk_level == "Critical" and not frappe.has_permission(
                "Exchange Request", "write", user=frappe.session.user
            ):
                frappe.throw(
                    _(
                        "طلبات التبديل عالية المخاطر تتطلب صلاحيات خاصة / Critical-risk exchanges require special permissions"
                    )
                )

        elif doc.workflow_state == "Processing":
            if doc.exchange_status != "Approved":
                frappe.throw(_("يجب الموافقة على الطلب أولاً / Request must be approved first"))

        elif doc.workflow_state == "Completed":
            if not doc.stock_entry or not doc.new_sales_invoice:
                frappe.throw(
                    _(
                        "يجب إنشاء قيد المخزون والفاتورة الجديدة أولاً / Stock entry and new invoice must be created first"
                    )
                )

            if doc.additional_payment > 0 and doc.workflow_state != "Awaiting Payment":
                frappe.throw(
                    _("يجب دفع المبلغ الإضافي أولاً / Additional payment must be made first")
                )


# Hook functions to be called from DocType events
def on_update_return_request(doc, method=None):
    """Called when Return Request is updated"""
    WorkflowUtils.update_return_request_fields(doc, method)
    WorkflowUtils.send_workflow_notification(doc, method)


def on_update_exchange_request(doc, method=None):
    """Called when Exchange Request is updated"""
    WorkflowUtils.update_exchange_request_fields(doc, method)
    WorkflowUtils.send_workflow_notification(doc, method)


def validate_return_request(doc, method=None):
    """Called when Return Request is validated"""
    WorkflowUtils.validate_workflow_conditions(doc, method)


def validate_exchange_request(doc, method=None):
    """Called when Exchange Request is validated"""
    WorkflowUtils.validate_workflow_conditions(doc, method)


# WhiteListed methods for API access
@frappe.whitelist()
def get_available_actions(doctype, docname):
    """Get available workflow actions for a document"""
    if not frappe.has_permission(doctype, "read", doc=docname):
        frappe.throw(
            _("ليس لديك صلاحية لعرض هذا المستند / You don't have permission to view this document")
        )

    doc = frappe.get_doc(doctype, docname)

    # Get workflow
    workflow_name = get_workflow_name(doctype)
    if not workflow_name:
        return {"actions": [], "message": _("لا يوجد workflow محدد / No workflow defined")}

    workflow = frappe.get_doc("Workflow", workflow_name)
    current_state = getattr(doc, workflow.workflow_state_field, None)

    if not current_state:
        return {
            "actions": [],
            "message": _("لا توجد حالة workflow حالية / No current workflow state"),
        }

    # Get available transitions
    available_actions = []
    user_roles = frappe.get_roles(frappe.session.user)

    for transition in workflow.transitions:
        if transition.state == current_state:
            # Check if user has permission
            allowed_roles = [role.strip() for role in transition.allowed.split(",") if role.strip()]
            if not allowed_roles or any(role in user_roles for role in allowed_roles):
                # Check condition if any
                condition_met = True
                if transition.condition:
                    try:
                        condition_met = eval(transition.condition, {"doc": doc})
                    except:
                        condition_met = False

                if condition_met:
                    available_actions.append(
                        {
                            "action": transition.action,
                            "next_state": transition.next_state,
                            "allowed": True,
                        }
                    )

    return {"actions": available_actions, "current_state": current_state}


@frappe.whitelist()
def execute_workflow_action(doctype, docname, action):
    """Execute a workflow action on a document"""
    if not frappe.has_permission(doctype, "write", doc=docname):
        frappe.throw(
            _(
                "ليس لديك صلاحية لتعديل هذا المستند / You don't have permission to modify this document"
            )
        )

    doc = frappe.get_doc(doctype, docname)

    # Validate that action is available
    available_actions = get_available_actions(doctype, docname)
    action_found = False
    next_state = None

    for available_action in available_actions["actions"]:
        if available_action["action"] == action:
            action_found = True
            next_state = available_action["next_state"]
            break

    if not action_found:
        frappe.throw(_("الإجراء غير مسموح / Action not allowed"))

    try:
        # Get workflow
        workflow_name = get_workflow_name(doctype)
        workflow = frappe.get_doc("Workflow", workflow_name)

        # Update workflow state
        setattr(doc, workflow.workflow_state_field, next_state)
        doc.save()

        return {
            "status": "success",
            "message": _("تم تنفيذ الإجراء بنجاح / Action executed successfully"),
            "new_state": next_state,
        }

    except Exception as e:
        frappe.log_error(f"Error executing workflow action: {str(e)}")
        frappe.throw(_("خطأ في تنفيذ الإجراء / Error executing action: {0}").format(str(e)))


@frappe.whitelist()
def get_workflow_history(doctype, docname):
    """Get workflow history for a document"""
    if not frappe.has_permission(doctype, "read", doc=docname):
        frappe.throw(
            _("ليس لديك صلاحية لعرض هذا المستند / You don't have permission to view this document")
        )

    # Get workflow actions from version history
    versions = frappe.get_list(
        "Version",
        filters={"ref_doctype": doctype, "docname": docname},
        fields=["modified", "modified_by", "data"],
        order_by="modified desc",
    )

    workflow_history = []
    for version in versions:
        try:
            version_data = json.loads(version.data)
            if "changed" in version_data:
                for change in version_data["changed"]:
                    if change[0] == "workflow_state":
                        workflow_history.append(
                            {
                                "date": version.modified,
                                "user": version.modified_by,
                                "from_state": change[1],
                                "to_state": change[2],
                                "action": _("حالة متغيرة / State Changed"),
                            }
                        )
        except:
            continue

    return workflow_history
