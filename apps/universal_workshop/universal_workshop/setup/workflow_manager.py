import frappe
from frappe import _
import json
import os
from pathlib import Path


class WorkflowManager:
    """Manages workflow creation and updates for Universal Workshop ERP"""

    def __init__(self):
        self.app_path = frappe.get_app_path("universal_workshop")
        self.workflows_path = os.path.join(self.app_path, "fixtures", "workflows")

    def install_all_workflows(self):
        """Install all workflows from fixtures"""
        workflows_installed = []

        try:
            # Return Request Workflow
            return_workflow = self.install_return_request_workflow()
            if return_workflow:
                workflows_installed.append(return_workflow)

            # Exchange Request Workflow
            exchange_workflow = self.install_exchange_request_workflow()
            if exchange_workflow:
                workflows_installed.append(exchange_workflow)

            # Update hooks to include workflows
            self.update_hooks_for_workflows()

            frappe.db.commit()

            return {
                "status": "success",
                "message": _(
                    "تم تثبيت {0} workflows بنجاح / Successfully installed {0} workflows"
                ).format(len(workflows_installed)),
                "workflows": workflows_installed,
            }

        except Exception as e:
            frappe.log_error(f"Error installing workflows: {str(e)}")
            return {
                "status": "error",
                "message": _("خطأ في تثبيت workflows / Error installing workflows: {0}").format(
                    str(e)
                ),
            }

    def install_return_request_workflow(self):
        """Install Return Request workflow"""
        workflow_file = os.path.join(self.workflows_path, "return_request_workflow.json")

        if not os.path.exists(workflow_file):
            frappe.log_error(f"Return Request workflow file not found: {workflow_file}")
            return None

        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Check if workflow already exists
            if frappe.db.exists("Workflow", workflow_data["name"]):
                existing_workflow = frappe.get_doc("Workflow", workflow_data["name"])
                self.update_workflow_from_data(existing_workflow, workflow_data)
                frappe.msgprint(_("تم تحديث workflow الاسترداد / Updated Return Request workflow"))
                return workflow_data["name"]
            else:
                workflow_doc = self.create_workflow_from_data(workflow_data)
                frappe.msgprint(_("تم إنشاء workflow الاسترداد / Created Return Request workflow"))
                return workflow_doc.name

        except Exception as e:
            frappe.log_error(f"Error installing Return Request workflow: {str(e)}")
            return None

    def install_exchange_request_workflow(self):
        """Install Exchange Request workflow"""
        workflow_file = os.path.join(self.workflows_path, "exchange_request_workflow.json")

        if not os.path.exists(workflow_file):
            frappe.log_error(f"Exchange Request workflow file not found: {workflow_file}")
            return None

        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Check if workflow already exists
            if frappe.db.exists("Workflow", workflow_data["name"]):
                existing_workflow = frappe.get_doc("Workflow", workflow_data["name"])
                self.update_workflow_from_data(existing_workflow, workflow_data)
                frappe.msgprint(_("تم تحديث workflow التبديل / Updated Exchange Request workflow"))
                return workflow_data["name"]
            else:
                workflow_doc = self.create_workflow_from_data(workflow_data)
                frappe.msgprint(_("تم إنشاء workflow التبديل / Created Exchange Request workflow"))
                return workflow_doc.name

        except Exception as e:
            frappe.log_error(f"Error installing Exchange Request workflow: {str(e)}")
            return None

    def create_workflow_from_data(self, workflow_data):
        """Create a new workflow document from JSON data"""
        workflow_doc = frappe.new_doc("Workflow")

        # Set basic fields
        workflow_doc.workflow_name = workflow_data["workflow_name"]
        workflow_doc.document_type = workflow_data["document_type"]
        workflow_doc.is_active = workflow_data.get("is_active", 1)
        workflow_doc.send_email_alert = workflow_data.get("send_email_alert", 1)
        workflow_doc.workflow_state_field = workflow_data.get(
            "workflow_state_field", "workflow_state"
        )

        # Add states
        for state_data in workflow_data.get("states", []):
            workflow_doc.append(
                "states",
                {
                    "state": state_data["state"],
                    "doc_status": state_data["doc_status"],
                    "allow_edit": state_data.get("allow_edit", ""),
                    "is_optional_state": state_data.get("is_optional_state", 0),
                    "next_action_email_template": state_data.get("next_action_email_template", ""),
                    "message": state_data.get("message", ""),
                },
            )

        # Add transitions
        for transition_data in workflow_data.get("transitions", []):
            workflow_doc.append(
                "transitions",
                {
                    "state": transition_data["state"],
                    "action": transition_data["action"],
                    "next_state": transition_data["next_state"],
                    "allowed": transition_data.get("allowed", ""),
                    "condition": transition_data.get("condition", ""),
                },
            )

        workflow_doc.insert()
        return workflow_doc

    def update_workflow_from_data(self, workflow_doc, workflow_data):
        """Update existing workflow with new data"""
        # Update basic fields
        workflow_doc.workflow_name = workflow_data["workflow_name"]
        workflow_doc.document_type = workflow_data["document_type"]
        workflow_doc.is_active = workflow_data.get("is_active", 1)
        workflow_doc.send_email_alert = workflow_data.get("send_email_alert", 1)
        workflow_doc.workflow_state_field = workflow_data.get(
            "workflow_state_field", "workflow_state"
        )

        # Clear and re-add states
        workflow_doc.states = []
        for state_data in workflow_data.get("states", []):
            workflow_doc.append(
                "states",
                {
                    "state": state_data["state"],
                    "doc_status": state_data["doc_status"],
                    "allow_edit": state_data.get("allow_edit", ""),
                    "is_optional_state": state_data.get("is_optional_state", 0),
                    "next_action_email_template": state_data.get("next_action_email_template", ""),
                    "message": state_data.get("message", ""),
                },
            )

        # Clear and re-add transitions
        workflow_doc.transitions = []
        for transition_data in workflow_data.get("transitions", []):
            workflow_doc.append(
                "transitions",
                {
                    "state": transition_data["state"],
                    "action": transition_data["action"],
                    "next_state": transition_data["next_state"],
                    "allowed": transition_data.get("allowed", ""),
                    "condition": transition_data.get("condition", ""),
                },
            )

        workflow_doc.save()
        return workflow_doc

    def update_hooks_for_workflows(self):
        """Update hooks.py to include workflow fixtures"""
        hooks_file = os.path.join(self.app_path, "hooks.py")

        try:
            with open(hooks_file, "r", encoding="utf-8") as f:
                hooks_content = f.read()

            # Check if fixtures already includes workflows
            if '"Workflow"' not in hooks_content:
                # Add workflows to fixtures
                if "fixtures = [" in hooks_content:
                    # Find fixtures list and add workflows
                    import re

                    fixtures_pattern = r"fixtures = \[(.*?)\]"
                    match = re.search(fixtures_pattern, hooks_content, re.DOTALL)
                    if match:
                        current_fixtures = match.group(1).strip()
                        if current_fixtures and not current_fixtures.endswith(","):
                            current_fixtures += ","

                        new_fixtures = current_fixtures + '\n    "Workflow",'
                        new_hooks_content = hooks_content.replace(
                            f"fixtures = [{current_fixtures}]", f"fixtures = [{new_fixtures}\n]"
                        )

                        with open(hooks_file, "w", encoding="utf-8") as f:
                            f.write(new_hooks_content)

                        frappe.msgprint(
                            _(
                                "تم تحديث hooks.py لتشمل workflows / Updated hooks.py to include workflows"
                            )
                        )
                else:
                    # Add fixtures list if it doesn't exist
                    hooks_content += '\n\n# Workflow fixtures\nfixtures = [\n    "Workflow"\n]\n'
                    with open(hooks_file, "w", encoding="utf-8") as f:
                        f.write(hooks_content)

                    frappe.msgprint(
                        _(
                            "تم إضافة fixtures للـ workflows في hooks.py / Added workflow fixtures to hooks.py"
                        )
                    )

        except Exception as e:
            frappe.log_error(f"Error updating hooks for workflows: {str(e)}")

    def create_email_templates(self):
        """Create email templates for workflow notifications"""
        templates = [
            {
                "name": "Return Request Created",
                "subject": "طلب استرداد جديد / New Return Request - {doc.name}",
                "response": """
                <p>تم إنشاء طلب استرداد جديد / A new return request has been created.</p>
                <p><strong>رقم الطلب / Request Number:</strong> {doc.name}</p>
                <p><strong>العميل / Customer:</strong> {doc.customer_name}</p>
                <p><strong>نوع الطلب / Request Type:</strong> {doc.request_type}</p>
                <p><strong>قيمة الاسترداد / Return Value:</strong> {doc.return_value} OMR</p>
                <p><strong>الحالة / Status:</strong> {doc.workflow_state}</p>
                """,
            },
            {
                "name": "Return Request Approved",
                "subject": "تم الموافقة على طلب الاسترداد / Return Request Approved - {doc.name}",
                "response": """
                <p>تم الموافقة على طلب الاسترداد الخاص بك / Your return request has been approved.</p>
                <p><strong>رقم الطلب / Request Number:</strong> {doc.name}</p>
                <p><strong>قيمة الاسترداد / Return Value:</strong> {doc.return_value} OMR</p>
                <p>سيتم معالجة طلبك خلال 3-5 أيام عمل / Your request will be processed within 3-5 business days.</p>
                """,
            },
            {
                "name": "Exchange Request Created",
                "subject": "طلب تبديل جديد / New Exchange Request - {doc.name}",
                "response": """
                <p>تم إنشاء طلب تبديل جديد / A new exchange request has been created.</p>
                <p><strong>رقم الطلب / Request Number:</strong> {doc.name}</p>
                <p><strong>العميل / Customer:</strong> {doc.customer_name}</p>
                <p><strong>القطعة الأصلية / Original Item:</strong> {doc.original_item_name}</p>
                <p><strong>القطعة البديلة / Exchange Item:</strong> {doc.exchange_item_name}</p>
                <p><strong>فرق السعر / Price Difference:</strong> {doc.price_difference} OMR</p>
                """,
            },
            {
                "name": "Exchange Request Approved",
                "subject": "تم الموافقة على طلب التبديل / Exchange Request Approved - {doc.name}",
                "response": """
                <p>تم الموافقة على طلب التبديل الخاص بك / Your exchange request has been approved.</p>
                <p><strong>رقم الطلب / Request Number:</strong> {doc.name}</p>
                <p><strong>فرق السعر / Price Difference:</strong> {doc.price_difference} OMR</p>
                {% if doc.additional_payment > 0 %}
                <p>يرجى دفع المبلغ الإضافي {doc.additional_payment} OMR / Please pay the additional amount of {doc.additional_payment} OMR</p>
                {% endif %}
                """,
            },
        ]

        for template_data in templates:
            if not frappe.db.exists("Email Template", template_data["name"]):
                template = frappe.new_doc("Email Template")
                template.name = template_data["name"]
                template.subject = template_data["subject"]
                template.response = template_data["response"]
                template.insert()
                frappe.msgprint(
                    _("تم إنشاء قالب البريد الإلكتروني: {0} / Created email template: {0}").format(
                        template_data["name"]
                    )
                )


# WhiteListed methods for API access
@frappe.whitelist()
def install_workflows():
    """Install all workflows for Return and Exchange systems"""
    if not frappe.has_permission("Workflow", "create"):
        frappe.throw(
            _("ليس لديك صلاحية لإنشاء workflows / You don't have permission to create workflows")
        )

    workflow_manager = WorkflowManager()
    result = workflow_manager.install_all_workflows()

    # Also create email templates
    workflow_manager.create_email_templates()

    return result


@frappe.whitelist()
def update_workflow(workflow_name):
    """Update a specific workflow from fixtures"""
    if not frappe.has_permission("Workflow", "write"):
        frappe.throw(
            _("ليس لديك صلاحية لتحديث workflows / You don't have permission to update workflows")
        )

    workflow_manager = WorkflowManager()

    if workflow_name == "Return Request Workflow":
        result = workflow_manager.install_return_request_workflow()
    elif workflow_name == "Exchange Request Workflow":
        result = workflow_manager.install_exchange_request_workflow()
    else:
        frappe.throw(_("اسم workflow غير صحيح / Invalid workflow name"))

    return {"status": "success", "workflow": result}


@frappe.whitelist()
def get_workflow_status(doctype_name):
    """Get workflow status for a specific DocType"""
    workflow = frappe.db.get_value(
        "Workflow",
        {"document_type": doctype_name},
        ["name", "is_active", "workflow_state_field"],
        as_dict=True,
    )

    if workflow:
        # Get workflow states
        states = frappe.get_list(
            "Workflow Document State",
            filters={"parent": workflow.name},
            fields=["state", "doc_status", "allow_edit", "message"],
            order_by="idx",
        )

        # Get workflow transitions
        transitions = frappe.get_list(
            "Workflow Transition",
            filters={"parent": workflow.name},
            fields=["state", "action", "next_state", "allowed", "condition"],
            order_by="idx",
        )

        return {"workflow": workflow, "states": states, "transitions": transitions}
    else:
        return {
            "workflow": None,
            "message": _("لا يوجد workflow لهذا النوع / No workflow found for this DocType"),
        }


@frappe.whitelist()
def validate_workflow_transition(doctype_name, docname, action):
    """Validate if a workflow transition is allowed"""
    doc = frappe.get_doc(doctype_name, docname)

    # Get current workflow state
    workflow = frappe.get_doc("Workflow", {"document_type": doctype_name})
    current_state = getattr(doc, workflow.workflow_state_field, None)

    if not current_state:
        return {
            "allowed": False,
            "message": _("لا توجد حالة workflow حالية / No current workflow state"),
        }

    # Find transition
    transition = None
    for t in workflow.transitions:
        if t.state == current_state and t.action == action:
            transition = t
            break

    if not transition:
        return {"allowed": False, "message": _("انتقال غير مسموح / Transition not allowed")}

    # Check user permission
    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = [role.strip() for role in transition.allowed.split(",") if role.strip()]

    if allowed_roles and not any(role in user_roles for role in allowed_roles):
        return {
            "allowed": False,
            "message": _(
                "ليس لديك صلاحية لهذا الإجراء / You don't have permission for this action"
            ),
        }

    # Check condition if any
    if transition.condition:
        try:
            if not eval(transition.condition, {"doc": doc}):
                return {
                    "allowed": False,
                    "message": _("شروط الانتقال غير محققة / Transition conditions not met"),
                }
        except Exception as e:
            frappe.log_error(f"Error evaluating workflow condition: {str(e)}")
            return {
                "allowed": False,
                "message": _("خطأ في تقييم شروط الانتقال / Error evaluating transition conditions"),
            }

    return {
        "allowed": True,
        "next_state": transition.next_state,
        "message": _("الانتقال مسموح / Transition allowed"),
    }
