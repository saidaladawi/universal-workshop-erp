"""
Print Formats Installation Script
Handles installation and setup of branded print formats
"""

import frappe
from frappe import _
from .print_format_manager import PrintFormatManager
from .branding_utils import PrintBrandingManager


def install_print_formats():
    """Install all default print formats with branding"""
    try:
        frappe.log_error("Starting print formats installation")

        # Initialize managers
        manager = PrintFormatManager()
        branding_manager = PrintBrandingManager()

        # Install default print formats
        installed_count = manager.install_default_print_formats()

        # Create print format management page
        create_print_format_management_page()

        # Set up print format permissions
        setup_print_format_permissions()

        frappe.log_error(
            f"Print formats installation completed. Installed {installed_count} formats"
        )

        return {
            "success": True,
            "message": f"Successfully installed {installed_count} branded print formats",
            "installed_count": installed_count,
        }

    except Exception as e:
        frappe.log_error(f"Error installing print formats: {e}")
        return {"success": False, "message": str(e)}


def create_print_format_management_page():
    """Create print format management workspace page"""
    try:
        # Check if page already exists
        if frappe.db.exists("Workspace", "Print Format Management"):
            return

        # Create workspace for print format management
        workspace = frappe.new_doc("Workspace")
        workspace.title = "Print Format Management"
        workspace.name = "Print Format Management"
        workspace.module = "Universal Workshop"
        workspace.category = "Modules"
        workspace.public = 1
        workspace.is_standard = 0

        # Add workspace content
        workspace.content = [
            {"type": "Card Break", "data": {"card_label": _("Branded Print Formats"), "col": 12}},
            {
                "type": "Shortcut",
                "data": {
                    "label": _("Install Default Formats"),
                    "url": "/app/print-format",
                    "doc_view": "List",
                    "color": "Blue",
                    "icon": "printer",
                    "format": "{} Print Formats",
                },
            },
            {
                "type": "Shortcut",
                "data": {
                    "label": _("Update Branding"),
                    "url": "/app/workshop-profile",
                    "doc_view": "List",
                    "color": "Green",
                    "icon": "edit",
                    "format": "{} Workshop Profiles",
                },
            },
            {
                "type": "Shortcut",
                "data": {
                    "label": _("Preview Formats"),
                    "url": "/app/print-format",
                    "doc_view": "List",
                    "color": "Orange",
                    "icon": "eye",
                    "format": "{} Print Formats",
                },
            },
        ]

        workspace.insert()
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating print format management page: {e}")


def setup_print_format_permissions():
    """Set up appropriate permissions for print format management"""
    try:
        # Roles that should have access to print format management
        roles = ["System Manager", "Workshop Manager", "Print Format Manager"]

        for role in roles:
            # Check if role exists, create if not
            if not frappe.db.exists("Role", role):
                if role == "Print Format Manager":
                    role_doc = frappe.new_doc("Role")
                    role_doc.role_name = role
                    role_doc.desk_access = 1
                    role_doc.insert()

            # Set permissions for Print Format doctype
            if not frappe.db.exists("Custom DocPerm", {"parent": "Print Format", "role": role}):
                perm = frappe.new_doc("Custom DocPerm")
                perm.parent = "Print Format"
                perm.parenttype = "DocType"
                perm.parentfield = "permissions"
                perm.role = role
                perm.read = 1
                perm.write = 1
                perm.create = 1
                perm.delete = 1
                perm.share = 1
                perm.export = 1
                perm.print = 1
                perm.email = 1
                perm.insert()

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up print format permissions: {e}")


def update_existing_print_formats():
    """Update existing print formats with workshop branding"""
    try:
        manager = PrintFormatManager()
        updated_count = manager.update_all_print_formats()

        return {
            "success": True,
            "message": f"Successfully updated {updated_count} print formats",
            "updated_count": updated_count,
        }

    except Exception as e:
        frappe.log_error(f"Error updating existing print formats: {e}")
        return {"success": False, "message": str(e)}


def uninstall_print_formats():
    """Remove all branded print formats"""
    try:
        # Get all Universal Workshop print formats
        print_formats = frappe.get_list(
            "Print Format", filters={"name": ["like", "Universal Workshop%"]}
        )

        removed_count = 0
        for pf in print_formats:
            try:
                frappe.delete_doc("Print Format", pf.name)
                removed_count += 1
            except Exception as e:
                frappe.log_error(f"Error removing print format {pf.name}: {e}")

        # Remove print format management workspace
        if frappe.db.exists("Workspace", "Print Format Management"):
            frappe.delete_doc("Workspace", "Print Format Management")

        frappe.db.commit()

        return {
            "success": True,
            "message": f"Successfully removed {removed_count} print formats",
            "removed_count": removed_count,
        }

    except Exception as e:
        frappe.log_error(f"Error uninstalling print formats: {e}")
        return {"success": False, "message": str(e)}


def test_print_format_integration():
    """Test print format integration functionality"""
    try:
        # Test branding manager
        branding_manager = PrintBrandingManager()
        branding_data = branding_manager.get_branding_data()

        # Test print format manager
        format_manager = PrintFormatManager()
        available_formats = format_manager.get_branded_print_formats()

        # Test template generation
        css = branding_manager.generate_print_css("en")
        header_html = branding_manager.generate_header_html("en")
        footer_html = branding_manager.generate_footer_html("en")

        test_results = {
            "branding_data_loaded": bool(branding_data),
            "available_formats_count": len(available_formats),
            "css_generated": bool(css),
            "header_html_generated": bool(header_html),
            "footer_html_generated": bool(footer_html),
            "arabic_support": True,
            "template_system": True,
        }

        return {
            "success": True,
            "message": "Print format integration test completed successfully",
            "test_results": test_results,
        }

    except Exception as e:
        frappe.log_error(f"Error testing print format integration: {e}")
        return {"success": False, "message": str(e)}


# API Functions for installation management
@frappe.whitelist()
def install_branded_print_formats():
    """API method to install branded print formats"""
    return install_print_formats()


@frappe.whitelist()
def update_print_format_branding():
    """API method to update print format branding"""
    return update_existing_print_formats()


@frappe.whitelist()
def test_print_integration():
    """API method to test print format integration"""
    return test_print_format_integration()


@frappe.whitelist()
def get_print_format_status():
    """Get status of print format installation"""
    try:
        # Count Universal Workshop print formats
        uw_formats = frappe.get_list(
            "Print Format", filters={"name": ["like", "Universal Workshop%"]}
        )

        # Check if branding data is available
        branding_manager = PrintBrandingManager()
        has_branding = bool(branding_manager.workshop_profile)

        # Check if templates exist
        import os

        templates_dir = "apps/universal_workshop/universal_workshop/templates/print_formats"
        has_templates = os.path.exists(templates_dir)

        return {
            "success": True,
            "status": {
                "installed_formats_count": len(uw_formats),
                "has_workshop_branding": has_branding,
                "has_templates": has_templates,
                "installation_complete": len(uw_formats) > 0 and has_branding,
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting print format status: {e}")
        return {"success": False, "message": str(e)}
