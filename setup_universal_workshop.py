#!/usr/bin/env python3
import frappe
import sys
import os


def setup_universal_workshop():
    """Complete setup for Universal Workshop ERP"""

    try:
        # Initialize Frappe
        frappe.init("universal.local")
        frappe.connect()

        print("🔧 Starting Universal Workshop ERP Setup...")

        # Check if setup is already complete
        setup_complete = frappe.db.get_single_value("System Settings", "setup_complete")
        if setup_complete:
            print("✅ Setup already completed")
            return

        # Create main company if it doesn't exist
        if not frappe.db.exists("Company", "Universal Workshop"):
            print("📋 Creating Universal Workshop company...")

            company = frappe.new_doc("Company")
            company.company_name = "Universal Workshop"
            company.abbr = "UW"
            company.default_currency = "OMR"
            company.country = "Oman"
            company.enable_perpetual_inventory = 1
            company.domains = ["Manufacturing"]
            company.insert(ignore_permissions=True)

            print(f"✅ Company created: {company.name}")
        else:
            company_name = "Universal Workshop"
            print(f"✅ Company exists: {company_name}")

        # Set global defaults
        print("🌐 Setting global defaults...")

        # Update Global Defaults if exists, create if not
        if frappe.db.exists("Global Defaults", "Global Defaults"):
            global_defaults = frappe.get_doc("Global Defaults")
        else:
            global_defaults = frappe.new_doc("Global Defaults")

        global_defaults.default_company = "Universal Workshop"
        global_defaults.default_currency = "OMR"
        global_defaults.country = "Oman"
        global_defaults.save(ignore_permissions=True)

        # Set system settings
        print("⚙️ Configuring system settings...")
        system_settings = frappe.get_doc("System Settings")
        system_settings.country = "Oman"
        system_settings.language = "ar"
        system_settings.time_zone = "Asia/Muscat"
        system_settings.date_format = "dd/mm/yyyy"
        system_settings.time_format = "HH:mm:ss"
        system_settings.number_format = "#,###.###"
        system_settings.float_precision = 3  # For OMR currency (3 decimal places)
        system_settings.currency_precision = 3
        system_settings.setup_complete = 1
        system_settings.save(ignore_permissions=True)

        # Create Administrator user if needed
        print("👤 Setting up Administrator...")
        if not frappe.db.get_value("User", "Administrator", "full_name"):
            admin_user = frappe.get_doc("User", "Administrator")
            admin_user.first_name = "Saeed"
            admin_user.last_name = "Al-Adawi"
            admin_user.full_name = "Saeed Al-Adawi"
            admin_user.email = "admin@universal.local"
            admin_user.language = "ar"
            admin_user.time_zone = "Asia/Muscat"
            admin_user.save(ignore_permissions=True)

        # Create sample items for workshop
        print("🔧 Creating sample workshop items...")
        create_sample_workshop_items()

        # Commit all changes
        frappe.db.commit()

        print("🎉 Universal Workshop ERP setup completed successfully!")
        print("📍 Company: Universal Workshop (UW)")
        print("💰 Currency: OMR (Omani Rial)")
        print("🌍 Country: Oman")
        print("🗣️ Language: Arabic")

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        frappe.db.rollback()
        import traceback

        traceback.print_exc()
        return False

    finally:
        frappe.destroy()


def create_sample_workshop_items():
    """Create sample items for automotive workshop"""

    sample_items = [
        {
            "item_code": "ENG-OIL-5W30",
            "item_name": "Engine Oil 5W-30",
            "item_name_ar": "زيت محرك ٥دبليو-٣٠",
            "item_group": "Automotive Parts",
            "stock_uom": "Litre",
            "standard_rate": 8.500,  # OMR
            "is_stock_item": 1,
        },
        {
            "item_code": "AIR-FILTER",
            "item_name": "Air Filter",
            "item_name_ar": "فلتر الهواء",
            "item_group": "Automotive Parts",
            "stock_uom": "Nos",
            "standard_rate": 12.000,  # OMR
            "is_stock_item": 1,
        },
        {
            "item_code": "BRAKE-SERVICE",
            "item_name": "Brake System Service",
            "item_name_ar": "خدمة نظام الفرامل",
            "item_group": "Services",
            "stock_uom": "Nos",
            "standard_rate": 25.000,  # OMR
            "is_stock_item": 0,
            "is_service_item": 1,
        },
    ]

    for item_data in sample_items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            item = frappe.new_doc("Item")
            item.update(item_data)
            item.insert(ignore_permissions=True)
            print(f"  📦 Created item: {item.item_code}")


if __name__ == "__main__":
    success = setup_universal_workshop()
    sys.exit(0 if success else 1)
