import frappe
from frappe import _
from frappe.utils import now, today, cint
import json
import os


class WorkflowManager:
    """Manager class for installing and managing Universal Workshop workflows"""

    def __init__(self):
        self.app_path = frappe.get_app_path("universal_workshop")
        self.workflows_path = os.path.join(self.app_path, "fixtures", "workflows")

    def install_all_workflows(self):
        """Install all Universal Workshop workflows"""
        workflows_installed = []

        try:
            # Install Return Request Workflow
            return_workflow = self.install_return_request_workflow()
            if return_workflow:
                workflows_installed.append("Return Request Workflow")

            # Install Exchange Request Workflow
            exchange_workflow = self.install_exchange_request_workflow()
            if exchange_workflow:
                workflows_installed.append("Exchange Request Workflow")

            # Create workflow email templates
            self.create_workflow_email_templates()

            # Setup workflow permissions
            self.setup_workflow_permissions()

            frappe.db.commit()

            return {
                "success": True,
                "message": _(
                    "تم تثبيت جميع سير العمل بنجاح / All workflows installed successfully"
                ),
                "workflows": workflows_installed,
            }

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error installing workflows: {str(e)}")
            return {
                "success": False,
                "message": _("خطأ في تثبيت سير العمل / Error installing workflows: {0}").format(
                    str(e)
                ),
                "workflows": workflows_installed,
            }

    def install_return_request_workflow(self):
        """Install Return Request Workflow"""
        workflow_file = os.path.join(self.workflows_path, "return_request_workflow.json")

        if not os.path.exists(workflow_file):
            frappe.throw(
                _("ملف سير عمل طلبات الاسترداد غير موجود / Return Request workflow file not found")
            )

        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)

        # Check if workflow already exists
        if frappe.db.exists("Workflow", workflow_data["name"]):
            existing_workflow = frappe.get_doc("Workflow", workflow_data["name"])
            existing_workflow.update(workflow_data)
            existing_workflow.save()
            workflow_doc = existing_workflow
        else:
            workflow_doc = frappe.new_doc("Workflow")
            workflow_doc.update(workflow_data)
            workflow_doc.insert()

        return workflow_doc

    def install_exchange_request_workflow(self):
        """Install Exchange Request Workflow"""
        workflow_file = os.path.join(self.workflows_path, "exchange_request_workflow.json")

        if not os.path.exists(workflow_file):
            frappe.throw(
                _("ملف سير عمل طلبات التبديل غير موجود / Exchange Request workflow file not found")
            )

        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)

        # Check if workflow already exists
        if frappe.db.exists("Workflow", workflow_data["name"]):
            existing_workflow = frappe.get_doc("Workflow", workflow_data["name"])
            existing_workflow.update(workflow_data)
            existing_workflow.save()
            workflow_doc = existing_workflow
        else:
            workflow_doc = frappe.new_doc("Workflow")
            workflow_doc.update(workflow_data)
            workflow_doc.insert()

        return workflow_doc

    def create_workflow_email_templates(self):
        """Create email templates for workflow notifications"""
        templates = [
            {
                "name": "Return Request Created",
                "subject": _("طلب استرداد جديد {0} / New Return Request {0}").format(
                    "{{ doc.name }}"
                ),
                "message": _(
                    """
<h3>طلب استرداد جديد / New Return Request</h3>
<p><strong>رقم الطلب / Request ID:</strong> {{ doc.name }}</p>
<p><strong>العميل / Customer:</strong> {{ doc.customer_name }}</p>
<p><strong>نوع الطلب / Request Type:</strong> {{ doc.request_type }}</p>
<p><strong>قيمة الاسترداد / Return Value:</strong> {{ doc.return_value }} OMR</p>
<p><strong>سبب الاسترداد / Return Reason:</strong> {{ doc.return_reason }}</p>

<p>يرجى مراجعة الطلب واتخاذ الإجراء المناسب.</p>
<p>Please review the request and take appropriate action.</p>
                """
                ),
                "doctype": "Email Template",
            },
            {
                "name": "Return Request Approved",
                "subject": _(
                    "تم الموافقة على طلب الاسترداد {0} / Return Request {0} Approved"
                ).format("{{ doc.name }}"),
                "message": _(
                    """
<h3>تم الموافقة على طلب الاسترداد / Return Request Approved</h3>
<p><strong>رقم الطلب / Request ID:</strong> {{ doc.name }}</p>
<p><strong>العميل / Customer:</strong> {{ doc.customer_name }}</p>
<p><strong>قيمة الاسترداد / Return Value:</strong> {{ doc.return_value }} OMR</p>
<p><strong>تاريخ الموافقة / Approval Date:</strong> {{ doc.approval_date }}</p>
<p><strong>الموافق / Approved By:</strong> {{ doc.approved_by }}</p>

<p>سيتم معالجة طلب الاسترداد خلال 3-5 أيام عمل.</p>
<p>The return request will be processed within 3-5 business days.</p>
                """
                ),
                "doctype": "Email Template",
            },
            {
                "name": "Exchange Request Created",
                "subject": _("طلب تبديل جديد {0} / New Exchange Request {0}").format(
                    "{{ doc.name }}"
                ),
                "message": _(
                    """
<h3>طلب تبديل جديد / New Exchange Request</h3>
<p><strong>رقم الطلب / Request ID:</strong> {{ doc.name }}</p>
<p><strong>العميل / Customer:</strong> {{ doc.customer_name }}</p>
<p><strong>المنتج الأصلي / Original Item:</strong> {{ doc.original_item_name }}</p>
<p><strong>المنتج الجديد / Exchange Item:</strong> {{ doc.exchange_item_name }}</p>
<p><strong>فرق السعر / Price Difference:</strong> {{ doc.price_difference }} OMR</p>
<p><strong>درجة التوافق / Compatibility Score:</strong> {{ doc.compatibility_score }}%</p>

<p>يرجى مراجعة الطلب واتخاذ الإجراء المناسب.</p>
<p>Please review the request and take appropriate action.</p>
                """
                ),
                "doctype": "Email Template",
            },
            {
                "name": "Exchange Request Approved",
                "subject": _(
                    "تم الموافقة على طلب التبديل {0} / Exchange Request {0} Approved"
                ).format("{{ doc.name }}"),
                "message": _(
                    """
<h3>تم الموافقة على طلب التبديل / Exchange Request Approved</h3>
<p><strong>رقم الطلب / Request ID:</strong> {{ doc.name }}</p>
<p><strong>العميل / Customer:</strong> {{ doc.customer_name }}</p>
<p><strong>المنتج الأصلي / Original Item:</strong> {{ doc.original_item_name }}</p>
<p><strong>المنتج الجديد / Exchange Item:</strong> {{ doc.exchange_item_name }}</p>
<p><strong>فرق السعر / Price Difference:</strong> {{ doc.price_difference }} OMR</p>
<p><strong>تاريخ الموافقة / Approval Date:</strong> {{ doc.approval_date }}</p>

<p>سيتم معالجة طلب التبديل خلال 3-5 أيام عمل.</p>
<p>The exchange request will be processed within 3-5 business days.</p>
                """
                ),
                "doctype": "Email Template",
            },
        ]

        for template_data in templates:
            if not frappe.db.exists("Email Template", template_data["name"]):
                template = frappe.new_doc("Email Template")
                template.update(template_data)
                template.insert()

    def setup_workflow_permissions(self):
        """Setup role-based permissions for workflows"""
        roles_to_create = [
            "Customer Service Representative",
            "Service Advisor",
            "Workshop Manager",
            "Technical Specialist",
            "Quality Inspector",
            "Inventory Manager",
            "Warehouse Keeper",
            "Accounts Manager",
            "General Manager",
        ]

        for role_name in roles_to_create:
            if not frappe.db.exists("Role", role_name):
                role = frappe.new_doc("Role")
                role.role_name = role_name
                role.desk_access = 1
                role.insert()

    def get_workflow_status(self, doctype_name):
        """Get status of workflow for a specific doctype"""
        workflow_name = f"{doctype_name} Workflow"

        if frappe.db.exists("Workflow", workflow_name):
            workflow = frappe.get_doc("Workflow", workflow_name)
            return {
                "exists": True,
                "name": workflow.name,
                "is_active": workflow.is_active,
                "document_type": workflow.document_type,
                "states_count": len(workflow.states),
                "transitions_count": len(workflow.transitions),
            }
        else:
            return {
                "exists": False,
                "name": workflow_name,
                "message": _("سير العمل غير مثبت / Workflow not installed"),
            }

    def test_workflow_functionality(self, doctype_name):
        """Test workflow functionality for a doctype"""
        try:
            workflow_status = self.get_workflow_status(doctype_name)

            if not workflow_status["exists"]:
                return {
                    "success": False,
                    "message": _("سير العمل غير موجود / Workflow does not exist"),
                }

            # Test workflow states and transitions
            workflow = frappe.get_doc("Workflow", f"{doctype_name} Workflow")

            # Validate workflow structure
            if not workflow.states:
                return {
                    "success": False,
                    "message": _("لا توجد حالات في سير العمل / No states found in workflow"),
                }

            if not workflow.transitions:
                return {
                    "success": False,
                    "message": _(
                        "لا توجد انتقالات في سير العمل / No transitions found in workflow"
                    ),
                }

            # Test email templates
            missing_templates = []
            for state in workflow.states:
                if state.get("next_action_email_template"):
                    if not frappe.db.exists("Email Template", state.next_action_email_template):
                        missing_templates.append(state.next_action_email_template)

            if missing_templates:
                return {
                    "success": False,
                    "message": _("قوالب الإيميل المفقودة / Missing email templates: {0}").format(
                        ", ".join(missing_templates)
                    ),
                }

            return {
                "success": True,
                "message": _("سير العمل يعمل بشكل صحيح / Workflow is functioning correctly"),
                "details": {
                    "states": len(workflow.states),
                    "transitions": len(workflow.transitions),
                    "email_templates": len(
                        [s for s in workflow.states if s.get("next_action_email_template")]
                    ),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "message": _("خطأ في اختبار سير العمل / Error testing workflow: {0}").format(
                    str(e)
                ),
            }

    def update_workflow_from_file(self, doctype_name):
        """Update existing workflow from file"""
        try:
            workflow_file = os.path.join(
                self.workflows_path, f"{doctype_name.lower().replace(' ', '_')}_workflow.json"
            )

            if not os.path.exists(workflow_file):
                return {
                    "success": False,
                    "message": _("ملف سير العمل غير موجود / Workflow file not found"),
                }

            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            workflow_name = f"{doctype_name} Workflow"

            if frappe.db.exists("Workflow", workflow_name):
                workflow = frappe.get_doc("Workflow", workflow_name)
                workflow.update(workflow_data)
                workflow.save()

                return {
                    "success": True,
                    "message": _("تم تحديث سير العمل بنجاح / Workflow updated successfully"),
                }
            else:
                return {
                    "success": False,
                    "message": _(
                        "سير العمل غير موجود للتحديث / Workflow does not exist for update"
                    ),
                }

        except Exception as e:
            return {
                "success": False,
                "message": _("خطأ في تحديث سير العمل / Error updating workflow: {0}").format(
                    str(e)
                ),
            }

    def remove_workflow(self, doctype_name):
        """Remove workflow for a doctype"""
        try:
            workflow_name = f"{doctype_name} Workflow"

            if frappe.db.exists("Workflow", workflow_name):
                frappe.delete_doc("Workflow", workflow_name)

                return {
                    "success": True,
                    "message": _("تم حذف سير العمل بنجاح / Workflow removed successfully"),
                }
            else:
                return {
                    "success": False,
                    "message": _("سير العمل غير موجود / Workflow does not exist"),
                }

        except Exception as e:
            return {
                "success": False,
                "message": _("خطأ في حذف سير العمل / Error removing workflow: {0}").format(str(e)),
            }


# Utility functions for workflow management
@frappe.whitelist()
def install_workflows():
    """Install all Universal Workshop workflows"""
    manager = WorkflowManager()
    return manager.install_all_workflows()


@frappe.whitelist()
def get_workflow_status(doctype_name):
    """Get workflow status for a doctype"""
    manager = WorkflowManager()
    return manager.get_workflow_status(doctype_name)


@frappe.whitelist()
def test_workflow(doctype_name):
    """Test workflow functionality"""
    manager = WorkflowManager()
    return manager.test_workflow_functionality(doctype_name)


@frappe.whitelist()
def update_workflow(doctype_name):
    """Update workflow from file"""
    manager = WorkflowManager()
    return manager.update_workflow_from_file(doctype_name)


@frappe.whitelist()
def remove_workflow(doctype_name):
    """Remove workflow"""
    manager = WorkflowManager()
    return manager.remove_workflow(doctype_name)


@frappe.whitelist()
def get_all_workflows_status():
    """Get status of all Universal Workshop workflows"""
    manager = WorkflowManager()

    doctypes = ["Return Request", "Exchange Request"]
    status_list = []

    for doctype in doctypes:
        status = manager.get_workflow_status(doctype)
        status_list.append({"doctype": doctype, "status": status})

    return status_list


def install_workflows_on_migrate():
    """Install workflows during app installation/migration"""
    try:
        manager = WorkflowManager()
        result = manager.install_all_workflows()

        if result["success"]:
            frappe.msgprint(_("تم تثبيت سير العمل بنجاح / Workflows installed successfully"))
        else:
            frappe.log_error(f"Workflow installation failed: {result['message']}")

    except Exception as e:
        frappe.log_error(f"Error in workflow installation during migration: {str(e)}")
