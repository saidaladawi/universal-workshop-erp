import frappe
from frappe import _


def execute():
    """Install Returns and Exchange workflows during app installation/migration"""
    try:
        frappe.log_info("Installing Returns and Exchange workflows...")
        
        # Import the workflow manager
        from universal_workshop.sales_service.utils.workflow_manager import WorkflowManager
        
        # Initialize the workflow manager
        manager = WorkflowManager()
        
        # Install all workflows
        result = manager.install_all_workflows()
        
        if result["success"]:
            frappe.log_info(f"Successfully installed workflows: {', '.join(result['workflows'])}")
            
            # Test the installed workflows
            for doctype in ["Return Request", "Exchange Request"]:
                test_result = manager.test_workflow_functionality(doctype)
                if test_result["success"]:
                    frappe.log_info(f"{doctype} workflow test passed")
                else:
                    frappe.log_error(f"{doctype} workflow test failed: {test_result['message']}")
        else:
            frappe.log_error(f"Failed to install workflows: {result['message']}")
            
    except ImportError as e:
        frappe.log_error(f"Import error installing workflows: {str(e)}")
        # Continue execution even if workflow installation fails
        
    except Exception as e:
        frappe.log_error(f"Error installing workflows: {str(e)}")
        # Don't fail the entire migration for workflow issues
        
    frappe.log_info("Returns and Exchange workflow installation patch completed") 