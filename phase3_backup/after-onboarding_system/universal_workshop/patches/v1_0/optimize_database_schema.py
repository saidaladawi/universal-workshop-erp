"""
Database Schema Optimization Patch
Optimizes database indexes and constraints for Universal Workshop ERP
"""

import frappe
from frappe.utils import now


def execute():
    """Execute database optimization patch"""

    frappe.log_error("Starting database schema optimization patch", "Database Optimization")

    try:
        # Add indexes for better performance
        optimize_indexes()

        # Clean up any orphaned data
        cleanup_orphaned_data()

        # Update system settings
        update_system_settings()

        # Log successful completion
        frappe.log_error(
            "Database schema optimization completed successfully", "Database Optimization"
        )

    except Exception as e:
        frappe.log_error(
            f"Database optimization patch failed: {str(e)}", "Database Optimization Error"
        )
        raise


def optimize_indexes():
    """Add optimized indexes for better query performance"""

    indexes_to_add = [
        {
            "table": "tabWorkshop Profile",
            "index": "idx_workshop_status_type",
            "columns": ["status", "workshop_type"],
        },
        {
            "table": "tabService Order",
            "index": "idx_service_customer_status",
            "columns": ["customer", "status"],
        },
        {"table": "tabVehicle", "index": "idx_vehicle_make_model", "columns": ["make", "model"]},
    ]

    for index_info in indexes_to_add:
        try:
            # Check if index already exists
            existing_indexes = frappe.db.sql(
                f"""
				SHOW INDEX FROM `{index_info['table']}` 
				WHERE Key_name = '{index_info['index']}'
			"""
            )

            if not existing_indexes:
                columns_str = ", ".join([f"`{col}`" for col in index_info["columns"]])
                frappe.db.sql(
                    f"""
					ALTER TABLE `{index_info['table']}` 
					ADD INDEX `{index_info['index']}` ({columns_str})
				"""
                )
                frappe.log_error(
                    f"Added index {index_info['index']} to {index_info['table']}", "Index Creation"
                )

        except Exception as e:
            frappe.log_error(
                f"Failed to add index {index_info['index']}: {str(e)}", "Index Creation Error"
            )


def cleanup_orphaned_data():
    """Clean up any orphaned or inconsistent data"""

    # Remove any orphaned activity logs
    try:
        frappe.db.sql(
            """
			DELETE FROM `tabActivity Log` 
			WHERE reference_doctype = 'Workshop Profile' 
			AND reference_name NOT IN (
				SELECT name FROM `tabWorkshop Profile`
			)
		"""
        )

        # Remove orphaned communication records
        frappe.db.sql(
            """
			DELETE FROM `tabCommunication` 
			WHERE reference_doctype IN ('Workshop Profile', 'Service Order', 'Vehicle')
			AND reference_name NOT IN (
				SELECT name FROM `tabWorkshop Profile`
				UNION
				SELECT name FROM `tabService Order`
				UNION
				SELECT name FROM `tabVehicle`
			)
		"""
        )

        frappe.log_error("Cleaned up orphaned data successfully", "Data Cleanup")

    except Exception as e:
        frappe.log_error(f"Data cleanup failed: {str(e)}", "Data Cleanup Error")


def update_system_settings():
    """Update system settings for optimal performance"""

    try:
        # Enable scheduler if not already enabled
        if not frappe.db.get_single_value("System Settings", "enable_scheduler"):
            frappe.db.set_single_value("System Settings", "enable_scheduler", 1)

        # Set optimal backup settings
        frappe.db.set_single_value("System Settings", "backup_limit", 5)

        # Update session defaults for Universal Workshop
        session_defaults = frappe.get_single("Session Default Settings")
        session_defaults.append(
            "session_defaults", {"ref_doctype": "Workshop Profile", "default_value": "Active"}
        )
        session_defaults.save()

        frappe.log_error("Updated system settings successfully", "System Settings")

    except Exception as e:
        frappe.log_error(f"System settings update failed: {str(e)}", "System Settings Error")


def validate_schema_integrity():
    """Validate schema integrity after optimization"""

    try:
        # Check core tables exist
        core_tables = ["tabWorkshop Profile", "tabService Order", "tabVehicle"]

        for table in core_tables:
            result = frappe.db.sql(f"SHOW TABLES LIKE '{table}'")
            if not result:
                raise Exception(f"Core table {table} is missing")

        # Validate field consistency
        for table in core_tables:
            count = frappe.db.sql(
                f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = DATABASE()"
            )[0][0]
            if count < 10:  # Minimum expected fields
                raise Exception(f"Table {table} has insufficient fields: {count}")

        frappe.log_error("Schema integrity validation passed", "Schema Validation")

    except Exception as e:
        frappe.log_error(f"Schema validation failed: {str(e)}", "Schema Validation Error")
        raise
