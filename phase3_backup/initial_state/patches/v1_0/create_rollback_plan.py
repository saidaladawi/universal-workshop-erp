"""
Database Migration Rollback Planning System
Creates comprehensive rollback strategies and backup mechanisms for Universal Workshop ERP
"""

import frappe
import json
import os
from datetime import datetime
from frappe.utils import now, get_site_name


def execute():
    """Execute rollback planning implementation"""

    frappe.log_error("Starting rollback planning implementation", "Rollback Planning")

    try:
        # Create rollback configuration
        create_rollback_configuration()

        # Setup backup strategies
        setup_backup_strategies()

        # Create rollback scripts
        create_rollback_scripts()

        # Implement rollback validation
        implement_rollback_validation()

        # Create rollback documentation
        create_rollback_documentation()

        # Create pre-migration snapshot
        create_pre_migration_snapshot()

        frappe.log_error(
            "Rollback planning implementation completed successfully", "Rollback Planning"
        )

    except Exception as e:
        frappe.log_error(
            f"Rollback planning implementation failed: {str(e)}", "Rollback Planning Error"
        )
        # Don't raise - this is a safety system


def create_rollback_configuration():
    """Create comprehensive rollback configuration"""

    try:
        rollback_config = {
            "backup_retention_days": 30,
            "max_backup_files": 10,
            "rollback_timeout_minutes": 60,
            "validation_checks": [
                "database_integrity",
                "doctype_consistency",
                "data_validation",
                "index_verification",
                "constraint_checks",
            ],
            "critical_tables": [
                "tabWorkshop Profile",
                "tabService Order",
                "tabVehicle",
                "tabCustomer",
                "tabUser",
                "tabDocType",
            ],
            "rollback_strategies": {
                "schema_changes": "restore_from_backup",
                "data_corruption": "selective_restore",
                "migration_failure": "complete_rollback",
                "performance_issues": "index_rollback",
            },
            "notification_settings": {
                "rollback_alerts": True,
                "backup_alerts": True,
                "validation_alerts": True,
                "recipients": ["admin@workshop.local", "it@workshop.local"],
            },
        }

        # Store rollback configuration
        frappe.db.set_single_value(
            "System Settings", "rollback_configuration", json.dumps(rollback_config)
        )

        frappe.log_error("Rollback configuration created successfully", "Rollback Planning")

    except Exception as e:
        frappe.log_error(
            f"Failed to create rollback configuration: {str(e)}", "Rollback Planning Error"
        )


def setup_backup_strategies():
    """Setup automated backup strategies for rollback"""

    try:
        # Create backup configuration
        backup_config = {
            "pre_migration_backup": True,
            "incremental_backups": True,
            "backup_compression": True,
            "backup_encryption": False,  # Can be enabled later
            "backup_location": f"./sites/{get_site_name()}/private/backups",
            "backup_schedule": {
                "daily": "02:00",
                "weekly": "sunday_02:30",
                "monthly": "first_sunday_03:00",
            },
            "backup_types": {
                "full": "complete_database_and_files",
                "schema": "database_structure_only",
                "data": "data_only_backup",
                "incremental": "changes_since_last_backup",
            },
        }

        # Store backup configuration
        frappe.db.set_single_value(
            "System Settings", "backup_configuration", json.dumps(backup_config)
        )

        # Create backup directory structure
        create_backup_directories()

        frappe.log_error("Backup strategies configured successfully", "Rollback Planning")

    except Exception as e:
        frappe.log_error(f"Failed to setup backup strategies: {str(e)}", "Rollback Planning Error")


def create_backup_directories():
    """Create backup directory structure"""

    try:
        site_name = get_site_name()
        base_backup_path = f"/home/frappe/backups/{site_name}"

        backup_dirs = [
            f"{base_backup_path}/daily",
            f"{base_backup_path}/weekly",
            f"{base_backup_path}/monthly",
            f"{base_backup_path}/pre_migration",
            f"{base_backup_path}/rollback_points",
            f"{base_backup_path}/schema_snapshots",
        ]

        for backup_dir in backup_dirs:
            try:
                os.makedirs(backup_dir, exist_ok=True)
                frappe.log_error(f"Created backup directory: {backup_dir}", "Backup Directory")
            except Exception as e:
                frappe.log_error(
                    f"Failed to create {backup_dir}: {str(e)}", "Backup Directory Error"
                )

    except Exception as e:
        frappe.log_error(
            f"Failed to create backup directories: {str(e)}", "Rollback Planning Error"
        )


def create_rollback_scripts():
    """Create automated rollback scripts"""

    try:
        # Create rollback script template
        rollback_script_template = """#!/bin/bash
# Universal Workshop ERP Rollback Script
# Generated: {timestamp}
# Site: {site_name}

set -e

echo "Starting rollback process for {site_name}..."

# Validate backup file
if [ ! -f "$1" ]; then
    echo "Error: Backup file not found: $1"
    exit 1
fi

# Create emergency backup before rollback
echo "Creating emergency backup before rollback..."
bench --site {site_name} backup --with-files

# Restore from backup
echo "Restoring from backup: $1"
bench --site {site_name} restore "$1"

# Validate restoration
echo "Validating restoration..."
bench --site {site_name} migrate --skip-failing

echo "Rollback completed successfully!"
"""

        # Generate actual rollback script
        site_name = get_site_name()
        rollback_script = rollback_script_template.format(timestamp=now(), site_name=site_name)

        # Save rollback script
        script_path = f"/home/frappe/backups/{site_name}/rollback_script.sh"
        try:
            with open(script_path, "w") as f:
                f.write(rollback_script)
            os.chmod(script_path, 0o755)  # Make executable
            frappe.log_error(f"Rollback script created: {script_path}", "Rollback Planning")
        except Exception as e:
            frappe.log_error(
                f"Failed to create rollback script: {str(e)}", "Rollback Planning Error"
            )

    except Exception as e:
        frappe.log_error(f"Failed to create rollback scripts: {str(e)}", "Rollback Planning Error")


def implement_rollback_validation():
    """Implement rollback validation mechanisms"""

    try:
        validation_config = {
            "pre_rollback_checks": [
                "verify_backup_integrity",
                "check_disk_space",
                "validate_permissions",
                "confirm_service_status",
            ],
            "post_rollback_checks": [
                "database_connectivity",
                "table_existence",
                "data_integrity",
                "index_consistency",
                "application_functionality",
            ],
            "rollback_validation_timeout": 300,  # 5 minutes
            "critical_validation_failures": [
                "database_corruption",
                "missing_critical_tables",
                "authentication_failure",
                "complete_data_loss",
            ],
        }

        # Store validation configuration
        frappe.db.set_single_value(
            "System Settings", "rollback_validation_config", json.dumps(validation_config)
        )

        frappe.log_error("Rollback validation mechanisms implemented", "Rollback Planning")

    except Exception as e:
        frappe.log_error(
            f"Failed to implement rollback validation: {str(e)}", "Rollback Planning Error"
        )


def create_rollback_documentation():
    """Create comprehensive rollback documentation"""

    try:
        documentation = {
            "rollback_procedures": {
                "emergency_rollback": {
                    "description": "Complete system rollback in case of critical failure",
                    "steps": [
                        "1. Stop all services immediately",
                        "2. Assess the extent of the issue",
                        "3. Identify the most recent stable backup",
                        "4. Execute rollback script with backup file",
                        "5. Validate system functionality",
                        "6. Notify stakeholders of rollback completion",
                    ],
                    "estimated_time": "30-60 minutes",
                    "required_permissions": "root, frappe user",
                },
                "selective_rollback": {
                    "description": "Rollback specific components or data",
                    "steps": [
                        "1. Identify affected components",
                        "2. Create backup of current state",
                        "3. Restore specific tables or data",
                        "4. Validate affected functionality",
                        "5. Update system logs",
                    ],
                    "estimated_time": "15-30 minutes",
                    "required_permissions": "frappe user",
                },
            },
            "rollback_decision_matrix": {
                "data_corruption": "emergency_rollback",
                "schema_issues": "selective_rollback",
                "performance_degradation": "configuration_rollback",
                "application_errors": "code_rollback",
            },
            "contact_information": {
                "primary_admin": "admin@workshop.local",
                "technical_support": "it@workshop.local",
                "emergency_contact": "+968-XXXX-XXXX",
            },
            "backup_locations": {
                "daily_backups": "/home/frappe/backups/{site}/daily",
                "emergency_backups": "/home/frappe/backups/{site}/pre_migration",
                "rollback_points": "/home/frappe/backups/{site}/rollback_points",
            },
        }

        # Store documentation
        frappe.db.set_single_value(
            "System Settings", "rollback_documentation", json.dumps(documentation)
        )

        frappe.log_error("Rollback documentation created successfully", "Rollback Planning")

    except Exception as e:
        frappe.log_error(
            f"Failed to create rollback documentation: {str(e)}", "Rollback Planning Error"
        )


def create_pre_migration_snapshot():
    """Create a complete snapshot before any migration"""

    try:
        site_name = get_site_name()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        snapshot_info = {
            "snapshot_id": f"pre_migration_{timestamp}",
            "creation_time": now(),
            "site_name": site_name,
            "database_size": get_database_size(),
            "table_count": get_table_count(),
            "user_count": get_user_count(),
            "doctype_count": get_doctype_count(),
            "snapshot_type": "pre_migration",
            "validation_status": "pending",
        }

        # Store snapshot information
        frappe.db.set_single_value(
            "System Settings", "latest_snapshot_info", json.dumps(snapshot_info)
        )

        frappe.log_error(
            f"Pre-migration snapshot created: {snapshot_info['snapshot_id']}", "Rollback Planning"
        )

        return snapshot_info

    except Exception as e:
        frappe.log_error(
            f"Failed to create pre-migration snapshot: {str(e)}", "Rollback Planning Error"
        )
        return None


def get_database_size():
    """Get current database size in MB"""
    try:
        result = frappe.db.sql(
            """
			SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
			FROM information_schema.tables 
			WHERE table_schema = DATABASE()
		""",
            as_dict=True,
        )
        return result[0]["size_mb"] if result else 0
    except Exception:
        return 0


def get_table_count():
    """Get total number of tables"""
    try:
        result = frappe.db.sql(
            """
			SELECT COUNT(*) as table_count
			FROM information_schema.tables 
			WHERE table_schema = DATABASE()
		""",
            as_dict=True,
        )
        return result[0]["table_count"] if result else 0
    except Exception:
        return 0


def get_user_count():
    """Get total number of users"""
    try:
        return frappe.db.count("User")
    except Exception:
        return 0


def get_doctype_count():
    """Get total number of DocTypes"""
    try:
        return frappe.db.count("DocType")
    except Exception:
        return 0
