# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
    """Setup Universal Workshop after installation"""
    try:
        # Setup customer management extensions
        setup_customer_management()

        # Setup vehicle management (if module exists)
        setup_vehicle_management()

        # Setup workshop management
        setup_workshop_management()

        # Setup purchasing management workflows
        setup_purchasing_management()

        # Setup parts inventory system
        setup_parts_inventory()

        # Setup billing and VAT management
        setup_billing_management()

        # Setup communication management
        setup_communication_management()

        # Setup Arabic language and localization
        setup_arabic_localization()

        # Setup default workshop settings and sample data
        setup_default_workshop_data()

        frappe.msgprint(_("Universal Workshop setup completed successfully"))

    except Exception as e:
        frappe.log_error(f"Error in Universal Workshop after_install: {e!s}")
        frappe.throw(_("Failed to complete Universal Workshop setup: {0}").format(str(e)))


def setup_customer_management():
    """Setup customer management extensions"""
    try:
        from universal_workshop.customer_management.custom_fields import setup_customer_extensions

        setup_customer_extensions()
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up customer management: {e!s}")
        raise


def setup_vehicle_management():
    """Setup vehicle management (placeholder)"""
    try:
        # This will be implemented when vehicle management module is created
        pass

    except Exception as e:
        frappe.log_error(f"Error setting up vehicle management: {e!s}")
        raise


def setup_workshop_management():
    """Setup workshop management extensions"""
    try:
        # Check if workshop is already configured
        existing_profiles = frappe.get_all("Workshop Profile", limit=1)

        if not existing_profiles:
            # Set initial setup state - workshop needs configuration
            frappe.db.set_default("setup_complete", "0")

            # Don't set a fixed home page, let boot session handle redirection
            frappe.db.commit()

            frappe.msgprint(
                _(
                    "Welcome to Universal Workshop! The system will guide you through the initial setup process."
                ),
                title=_("Setup Required"),
                indicator="orange",
            )
        else:
            # Workshop already configured
            frappe.db.set_default("setup_complete", "1")
            frappe.db.commit()

            frappe.msgprint(
                _("Universal Workshop is already configured and ready to use."),
                title=_("System Ready"),
                indicator="green",
            )

    except Exception as e:
        frappe.log_error(f"Error setting up workshop management: {e!s}")
        raise


def before_uninstall():
    """Clean up before app uninstall"""
    try:
        # Remove custom fields and doctypes
        cleanup_customer_management()

        frappe.msgprint(_("Universal Workshop cleanup completed"))

    except Exception as e:
        frappe.log_error(f"Error in Universal Workshop before_uninstall: {e!s}")


def setup_purchasing_management():
    """Setup purchasing management workflows and configurations"""
    try:
        from universal_workshop.purchasing_management.workflow.workflow_installer import (
            install_approval_workflows,
        )
        from universal_workshop.purchasing_management.install_goods_receipt_integration import (
            install_goods_receipt_quality_inspection_integration,
        )

        # Install approval workflows
        install_approval_workflows()

        # Install goods receipt quality inspection integration
        install_goods_receipt_quality_inspection_integration()

        # Install cost analysis dashboard
        from universal_workshop.purchasing_management.cost_analysis_dashboard import (
            install_cost_analysis_dashboard,
        )

        dashboard_result = install_cost_analysis_dashboard()

        if dashboard_result["status"] == "success":
            frappe.msgprint(
                _("Purchasing management system configured successfully"),
                title=_("Purchasing Setup Complete"),
                indicator="green",
            )
        else:
            frappe.msgprint(
                _("Purchasing management configured with warnings: {0}").format(
                    dashboard_result["message"]
                ),
                title=_("Purchasing Setup Warning"),
                indicator="orange",
            )

    except Exception as e:
        frappe.log_error(f"Error setting up purchasing management: {e!s}")
        # Don't raise here to allow installation to continue
        frappe.msgprint(
            _(
                "Warning: Purchasing management setup failed. You can install components manually later."
            ),
            title=_("Setup Warning"),
            indicator="orange",
        )


def setup_parts_inventory():
    """Setup parts inventory system with custom fields and warehouses"""
    try:
        # Install item custom fields
        try:
            from universal_workshop.parts_inventory.fixtures.custom_fields import (
                install_item_custom_fields,
            )

            install_item_custom_fields()
        except ImportError:
            frappe.log_error("Parts inventory custom fields module not found")

        # Setup default warehouses
        try:
            from universal_workshop.parts_inventory.warehouse_management import (
                setup_default_warehouses,
            )

            setup_default_warehouses()
        except ImportError:
            frappe.log_error("Parts inventory warehouse management module not found")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up parts inventory: {e!s}")
        # Don't raise - allow installation to continue


def setup_billing_management():
    """Setup billing management with VAT compliance and custom fields"""
    try:
        # Install VAT custom fields
        try:
            from universal_workshop.billing_management.fixtures.vat_custom_fields import (
                install_vat_custom_fields,
            )

            install_vat_custom_fields()
        except ImportError:
            frappe.log_error("Billing VAT custom fields module not found")

        # Install invoice custom fields
        try:
            from universal_workshop.billing_management.fixtures.invoice_custom_fields import (
                install_invoice_custom_fields,
            )

            install_invoice_custom_fields()
        except ImportError:
            frappe.log_error("Billing invoice custom fields module not found")

        # Install QR code fields
        try:
            from universal_workshop.billing_management.fixtures.qr_code_fields import (
                install_qr_code_fields,
            )

            install_qr_code_fields()
        except ImportError:
            frappe.log_error("Billing QR code fields module not found")

        # Install bilingual invoice print format
        try:
            from universal_workshop.billing_management.print_formats.bilingual_invoice import (
                install_bilingual_invoice_print_format,
            )

            install_bilingual_invoice_print_format()
        except ImportError:
            frappe.log_error("Bilingual invoice print format module not found")

        # Setup Oman VAT configuration
        try:
            from universal_workshop.billing_management.oman_vat_config import setup_oman_vat

            setup_oman_vat()
        except ImportError:
            frappe.log_error("Oman VAT configuration module not found")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up billing management: {e!s}")
        # Don't raise - allow installation to continue


def setup_communication_management():
    """Setup communication management system"""
    try:
        # Install communication settings
        try:
            from universal_workshop.communication_management.setup import (
                install_communication_settings,
            )

            install_communication_settings()
        except ImportError:
            frappe.log_error("Communication management setup module not found")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up communication management: {e!s}")
        # Don't raise - allow installation to continue


def setup_arabic_localization():
    """Setup Arabic language and localization"""
    try:
        # Enable Arabic language
        if not frappe.db.exists("Language", "ar"):
            arabic_lang = frappe.new_doc("Language")
            arabic_lang.language_code = "ar"
            arabic_lang.language_name = "العربية"
            arabic_lang.enabled = 1
            arabic_lang.flag = "om"  # Oman flag
            arabic_lang.insert(ignore_permissions=True)

        # Update System Settings for Arabic and Oman
        system_settings = frappe.get_doc("System Settings")
        system_settings.language = "ar"
        system_settings.country = "Oman"
        system_settings.time_zone = "Asia/Muscat"
        system_settings.currency = "OMR"
        system_settings.save(ignore_permissions=True)

        # Setup default roles for workshop
        setup_default_workshop_roles()

        frappe.db.commit()
        frappe.msgprint(_("Arabic localization configured successfully"), indicator="green")

    except Exception as e:
        frappe.log_error(f"Error setting up Arabic localization: {e!s}")
        # Don't raise - allow installation to continue


def setup_default_workshop_roles():
    """Create default workshop roles with Arabic names"""
    try:
        workshop_roles = [
            {
                "role_name": "Workshop Manager",
                "role_name_ar": "مدير الورشة",
                "description": "Full access to workshop management",
            },
            {
                "role_name": "Workshop Technician",
                "role_name_ar": "فني الورشة",
                "description": "Access to service orders and vehicle management",
            },
            {
                "role_name": "Service Advisor",
                "role_name_ar": "مستشار الخدمة",
                "description": "Customer interaction and service scheduling",
            },
            {
                "role_name": "Workshop Owner",
                "role_name_ar": "مالك الورشة",
                "description": "Full system access and business management",
            },
        ]

        for role_data in workshop_roles:
            if not frappe.db.exists("Role", role_data["role_name"]):
                role = frappe.new_doc("Role")
                role.role_name = role_data["role_name"]
                role.desk_access = 1
                role.insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up workshop roles: {e!s}")


def setup_default_workshop_data():
    """Create default workshop settings, service types, and sample data"""
    try:
        # Create default service types
        create_default_service_types()

        # Create default labor rates
        create_default_labor_rates()

        # Create default system preferences
        create_default_system_preferences()

        # Create sample workshop data for testing
        create_sample_workshop_data()

        frappe.db.commit()
        frappe.msgprint(_("Default workshop data created successfully"), indicator="green")

    except Exception as e:
        frappe.log_error(f"Error setting up default workshop data: {e!s}")
        # Don't raise - allow installation to continue


def create_default_service_types():
    """Create default automotive service types with Arabic names"""
    try:
        service_types = [
            {
                "service_name": "Engine Service",
                "service_name_ar": "خدمة المحرك",
                "description": "Engine maintenance and repair services",
                "description_ar": "خدمات صيانة وإصلاح المحرك",
                "standard_rate": 25.000,  # OMR per hour
                "is_active": 1,
            },
            {
                "service_name": "Transmission Service",
                "service_name_ar": "خدمة ناقل الحركة",
                "description": "Transmission maintenance and repair",
                "description_ar": "صيانة وإصلاح ناقل الحركة",
                "standard_rate": 30.000,
                "is_active": 1,
            },
            {
                "service_name": "Brake Service",
                "service_name_ar": "خدمة الفرامل",
                "description": "Brake system maintenance and repair",
                "description_ar": "صيانة وإصلاح نظام الفرامل",
                "standard_rate": 20.000,
                "is_active": 1,
            },
            {
                "service_name": "Tire Service",
                "service_name_ar": "خدمة الإطارات",
                "description": "Tire installation, rotation, and repair",
                "description_ar": "تركيب وتدوير وإصلاح الإطارات",
                "standard_rate": 15.000,
                "is_active": 1,
            },
            {
                "service_name": "Oil Change",
                "service_name_ar": "تغيير الزيت",
                "description": "Engine oil and filter change service",
                "description_ar": "خدمة تغيير زيت المحرك والفلتر",
                "standard_rate": 10.000,
                "is_active": 1,
            },
            {
                "service_name": "Air Conditioning",
                "service_name_ar": "تكييف الهواء",
                "description": "AC system maintenance and repair",
                "description_ar": "صيانة وإصلاح نظام التكييف",
                "standard_rate": 25.000,
                "is_active": 1,
            },
            {
                "service_name": "Electrical System",
                "service_name_ar": "النظام الكهربائي",
                "description": "Electrical system diagnosis and repair",
                "description_ar": "تشخيص وإصلاح النظام الكهربائي",
                "standard_rate": 35.000,
                "is_active": 1,
            },
            {
                "service_name": "General Inspection",
                "service_name_ar": "فحص عام",
                "description": "Comprehensive vehicle inspection",
                "description_ar": "فحص شامل للمركبة",
                "standard_rate": 20.000,
                "is_active": 1,
            },
        ]

        # Check if Service Type DocType exists
        if frappe.db.exists("DocType", "Service Type"):
            for service_data in service_types:
                if not frappe.db.exists(
                    "Service Type", {"service_name": service_data["service_name"]}
                ):
                    service_type = frappe.new_doc("Service Type")
                    service_type.update(service_data)
                    service_type.insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating default service types: {e!s}")


def create_default_labor_rates():
    """Create default labor rates for different skill levels"""
    try:
        labor_rates = [
            {
                "skill_level": "Master Technician",
                "skill_level_ar": "فني خبير",
                "hourly_rate": 40.000,  # OMR per hour
                "description": "Highly experienced technician for complex repairs",
            },
            {
                "skill_level": "Senior Technician",
                "skill_level_ar": "فني أول",
                "hourly_rate": 30.000,
                "description": "Experienced technician for standard repairs",
            },
            {
                "skill_level": "Junior Technician",
                "skill_level_ar": "فني مساعد",
                "hourly_rate": 20.000,
                "description": "Entry-level technician for basic maintenance",
            },
            {
                "skill_level": "Apprentice",
                "skill_level_ar": "متدرب",
                "hourly_rate": 15.000,
                "description": "Trainee technician under supervision",
            },
        ]

        # Check if Labor Rate DocType exists
        if frappe.db.exists("DocType", "Labor Rate"):
            for rate_data in labor_rates:
                if not frappe.db.exists("Labor Rate", {"skill_level": rate_data["skill_level"]}):
                    labor_rate = frappe.new_doc("Labor Rate")
                    labor_rate.update(rate_data)
                    labor_rate.insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating default labor rates: {e!s}")


def create_default_system_preferences():
    """Create default system preferences for workshop operations"""
    try:
        preferences = {
            "default_currency": "OMR",
            "vat_rate": 5.0,  # 5% VAT for Oman
            "working_hours_start": "08:00",
            "working_hours_end": "18:00",
            "working_days": "Sunday,Monday,Tuesday,Wednesday,Thursday",  # Oman working days
            "appointment_duration": 60,  # minutes
            "reminder_days": 7,  # days before service due
            "warranty_period": 90,  # days
            "language_preference": "ar",
            "country": "Oman",
            "timezone": "Asia/Muscat",
        }

        # Check if Workshop Settings DocType exists
        if frappe.db.exists("DocType", "Workshop Settings"):
            if not frappe.db.exists("Workshop Settings", "Workshop Settings"):
                workshop_settings = frappe.new_doc("Workshop Settings")
                workshop_settings.name = "Workshop Settings"
                workshop_settings.update(preferences)
                workshop_settings.insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating default system preferences: {e!s}")


def create_sample_workshop_data():
    """Create sample workshop data for testing and demonstration"""
    try:
        # Create sample customer
        if frappe.db.exists("DocType", "Customer") and not frappe.db.exists(
            "Customer", "CUST-SAMPLE-001"
        ):
            customer = frappe.new_doc("Customer")
            customer.customer_name = "Ahmed Al-Rashid"
            customer.customer_name_ar = "أحمد الراشد"
            customer.customer_type = "Individual"
            customer.customer_group = "Individual"
            customer.territory = "Oman"
            customer.mobile_no = "+968 91234567"
            customer.email_id = "ahmed.rashid@example.om"
            customer.insert(ignore_permissions=True)

        # Create sample vehicle
        if frappe.db.exists("DocType", "Vehicle") and not frappe.db.exists(
            "Vehicle", "VEH-SAMPLE-001"
        ):
            vehicle = frappe.new_doc("Vehicle")
            vehicle.license_plate = "12345 OM"
            vehicle.license_plate_ar = "١٢٣٤٥ عمان"
            vehicle.make = "Toyota"
            vehicle.model = "Camry"
            vehicle.year = 2022
            vehicle.vin = "JTDBF3FG4N0123456"
            vehicle.engine_number = "2GR-FE-123456"
            vehicle.color = "White"
            vehicle.color_ar = "أبيض"
            vehicle.owner = "CUST-SAMPLE-001"
            vehicle.insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating sample workshop data: {e!s}")


def cleanup_customer_management():
    """Remove customer management customizations"""
    try:
        # Remove child doctypes
        child_doctypes = [
            "Customer Vehicle Ownership",
            "Customer Communication Channel",
            "Customer Service Day",
            "Customer Communication History",
        ]

        for doctype_name in child_doctypes:
            if frappe.db.exists("DocType", doctype_name):
                frappe.delete_doc("DocType", doctype_name, force=True)

        # Remove custom fields (Frappe will handle this automatically)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error cleaning up customer management: {e!s}")
        raise
