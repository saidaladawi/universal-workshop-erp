import frappe
from frappe import _


@frappe.whitelist()
def get_workflow_status_dashboard():
    """Get status dashboard for all workflows"""
    try:
        from universal_workshop.sales_service.utils.workflow_manager import WorkflowManager

        manager = WorkflowManager()
        doctypes = ["Return Request", "Exchange Request"]

        workflow_status = []

        for doctype in doctypes:
            status = manager.get_workflow_status(doctype)
            test_result = manager.test_workflow_functionality(doctype)

            workflow_status.append(
                {
                    "doctype": doctype,
                    "doctype_ar": (
                        _("طلب الاسترداد") if doctype == "Return Request" else _("طلب التبديل")
                    ),
                    "status": status,
                    "test_result": test_result,
                }
            )

        return {"success": True, "workflows": workflow_status}

    except Exception as e:
        frappe.log_error(f"Error getting workflow status: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def test_workflow_functionality(doctype):
    """Test specific workflow functionality"""
    try:
        from universal_workshop.sales_service.utils.workflow_manager import WorkflowManager

        manager = WorkflowManager()
        return manager.test_workflow_functionality(doctype)

    except Exception as e:
        frappe.log_error(f"Error testing workflow for {doctype}: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def install_workflow(doctype):
    """Install/reinstall specific workflow"""
    try:
        from universal_workshop.sales_service.utils.workflow_manager import WorkflowManager

        manager = WorkflowManager()

        if doctype == "Return Request":
            result = manager.install_return_request_workflow()
        elif doctype == "Exchange Request":
            result = manager.install_exchange_request_workflow()
        else:
            return {
                "success": False,
                "message": _("نوع المستند غير مدعوم / Unsupported document type"),
            }

        if result:
            return {
                "success": True,
                "message": _("تم تثبيت سير العمل بنجاح / Workflow installed successfully"),
            }
        else:
            return {
                "success": False,
                "message": _("فشل في تثبيت سير العمل / Failed to install workflow"),
            }

    except Exception as e:
        frappe.log_error(f"Error installing workflow for {doctype}: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_workflow_actions_demo():
    """Get demo workflow actions for testing"""
    return {
        "Return Request": [
            {
                "state": "Draft",
                "available_actions": ["Submit for Review", "Cancel"],
                "description": _("إرسال للمراجعة أو إلغاء / Submit for review or cancel"),
            },
            {
                "state": "Pending Review",
                "available_actions": ["Approve", "Reject", "Investigate"],
                "description": _("الموافقة أو الرفض أو التحقيق / Approve, reject or investigate"),
            },
            {
                "state": "Approved",
                "available_actions": ["Start Processing"],
                "description": _("بدء المعالجة / Start processing"),
            },
        ],
        "Exchange Request": [
            {
                "state": "Draft",
                "available_actions": ["Submit for Approval", "Cancel"],
                "description": _("إرسال للموافقة أو إلغاء / Submit for approval or cancel"),
            },
            {
                "state": "Pending Approval",
                "available_actions": [
                    "Review Compatibility",
                    "Manager Review",
                    "Auto Approve",
                    "Reject",
                ],
                "description": _(
                    "مراجعة التوافق أو المدير أو موافقة تلقائية / Review compatibility, manager review, auto approve"
                ),
            },
            {
                "state": "Approved",
                "available_actions": ["Start Processing"],
                "description": _("بدء المعالجة / Start processing"),
            },
        ],
    }
