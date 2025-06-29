# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, flt, cint


class MigrationJob(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def before_insert(self):
        """Set default values before insertion"""
        self.created_by = frappe.session.user
        self.created_date = now_datetime()
        self.status = "Draft"

        if not self.priority:
            self.priority = "Medium"

        if not self.batch_size:
            self.batch_size = 1000

    def validate(self):
        """Validate migration job configuration"""
        self.validate_arabic_title()
        self.validate_field_mapping()
        self.validate_source_file()
        self.validate_target_doctype()

    def validate_arabic_title(self):
        """Ensure Arabic title is provided if available"""
        if self.job_title and not self.job_title_ar:
            # Auto-suggest Arabic title based on migration type
            arabic_titles = {
                "Import": "استيراد البيانات",
                "Export": "تصدير البيانات",
                "Sync": "مزامنة البيانات",
                "Transform": "تحويل البيانات",
            }
            if self.migration_type in arabic_titles:
                self.job_title_ar = f"{arabic_titles[self.migration_type]} - {self.job_title}"

    def validate_field_mapping(self):
        """Validate field mapping configuration"""
        if self.field_mapping and isinstance(self.field_mapping, str):
            try:
                mapping = json.loads(self.field_mapping)
                if not isinstance(mapping, dict):
                    frappe.throw(_("Field mapping must be a valid JSON object"))
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in field mapping"))

    def validate_source_file(self):
        """Validate source file requirements"""
        if self.source_type in ["CSV", "Excel", "JSON", "XML"] and not self.source_file:
            frappe.throw(_("Source file is required for {0} migrations").format(self.source_type))

    def validate_target_doctype(self):
        """Validate target DocType exists and is accessible"""
        if self.target_doctype:
            if not frappe.db.exists("DocType", self.target_doctype):
                frappe.throw(_("Target DocType {0} does not exist").format(self.target_doctype))

    def before_save(self):
        """Update calculated fields before saving"""
        self.calculate_progress()
        self.calculate_duration()
        self.estimate_completion()

    def calculate_progress(self):
        """Calculate migration progress percentage"""
        if self.total_records and self.total_records > 0:
            self.progress_percentage = flt(
                (self.processed_records or 0) / self.total_records * 100, 2
            )
        else:
            self.progress_percentage = 0

    def calculate_duration(self):
        """Calculate migration duration in minutes"""
        if self.started_at and self.completed_at:
            start_time = get_datetime(self.started_at)
            end_time = get_datetime(self.completed_at)
            duration = end_time - start_time
            self.duration_minutes = int(duration.total_seconds() / 60)

    def estimate_completion(self):
        """Estimate completion time based on current progress"""
        if (
            self.started_at
            and self.processed_records
            and self.total_records
            and self.progress_percentage > 0
        ):

            start_time = get_datetime(self.started_at)
            current_time = now_datetime()
            elapsed = current_time - start_time

            if elapsed.total_seconds() > 0:
                remaining_percentage = 100 - self.progress_percentage
                estimated_remaining = elapsed * (remaining_percentage / self.progress_percentage)
                self.estimated_completion = current_time + estimated_remaining

    @frappe.whitelist()
    def start_migration(self):
        """Start the migration process"""
        if self.status != "Draft":
            frappe.throw(_("Only draft migrations can be started"))

        self.status = "Queued"
        self.started_at = now_datetime()
        self.save()

        # Queue background job for actual migration
        frappe.enqueue(
            "universal_workshop.data_migration.doctype.migration_job.migration_job.execute_migration",
            job_name=self.name,
            timeout=3600,  # 1 hour timeout
            migration_job_id=self.name,
        )

        frappe.msgprint(_("Migration job queued successfully"))
        return True

    @frappe.whitelist()
    def cancel_migration(self):
        """Cancel running migration"""
        if self.status not in ["Queued", "Running"]:
            frappe.throw(_("Only queued or running migrations can be cancelled"))

        self.status = "Cancelled"
        self.completed_at = now_datetime()
        self.save()

        frappe.msgprint(_("Migration job cancelled"))
        return True

    @frappe.whitelist()
    def rollback_migration(self):
        """Rollback completed migration"""
        if self.status != "Completed":
            frappe.throw(_("Only completed migrations can be rolled back"))

        if not self.rollback_data:
            frappe.throw(_("No rollback data available for this migration"))

        try:
            rollback_data = (
                json.loads(self.rollback_data)
                if isinstance(self.rollback_data, str)
                else self.rollback_data
            )

            # Execute rollback logic
            self._execute_rollback(rollback_data)

            self.status = "Rolled Back"
            self.completed_at = now_datetime()
            self.save()

            frappe.msgprint(_("Migration rolled back successfully"))
            return True

        except Exception as e:
            frappe.log_error(f"Rollback failed: {str(e)}", "Migration Rollback Error")
            frappe.throw(_("Rollback failed: {0}").format(str(e)))

    def _execute_rollback(self, rollback_data: Dict):
        """Execute the actual rollback process"""
        if "created_records" in rollback_data:
            # Delete created records
            for doctype, record_names in rollback_data["created_records"].items():
                for name in record_names:
                    try:
                        if frappe.db.exists(doctype, name):
                            frappe.delete_doc(doctype, name, force=1)
                    except Exception as e:
                        frappe.log_error(f"Failed to delete {doctype} {name}: {str(e)}")

        if "modified_records" in rollback_data:
            # Restore modified records
            for doctype, records in rollback_data["modified_records"].items():
                for record_name, original_data in records.items():
                    try:
                        if frappe.db.exists(doctype, record_name):
                            doc = frappe.get_doc(doctype, record_name)
                            doc.update(original_data)
                            doc.save()
                    except Exception as e:
                        frappe.log_error(f"Failed to restore {doctype} {record_name}: {str(e)}")

    @frappe.whitelist()
    def get_progress_summary(self):
        """Get migration progress summary"""
        return {
            "total_records": self.total_records or 0,
            "processed_records": self.processed_records or 0,
            "successful_records": self.successful_records or 0,
            "failed_records": self.failed_records or 0,
            "progress_percentage": self.progress_percentage or 0,
            "status": self.status,
            "estimated_completion": self.estimated_completion,
            "duration_minutes": self.duration_minutes or 0,
            "memory_usage_mb": self.memory_usage_mb or 0,
            "cpu_usage_percent": self.cpu_usage_percent or 0,
        }

    def log_error(
        self,
        error_message: str,
        record_data: Optional[Dict] = None,
        line_number: Optional[int] = None,
    ):
        """Log migration error"""
        error_log_data = json.loads(self.error_log) if self.error_log else []

        error_entry = {
            "timestamp": now_datetime().isoformat(),
            "message": error_message,
            "line_number": line_number,
            "record_data": record_data,
        }

        error_log_data.append(error_entry)
        self.error_log = json.dumps(error_log_data)
        self.failed_records = cint(self.failed_records or 0) + 1

    def log_transaction(
        self, action: str, doctype: str, record_name: str, data: Optional[Dict] = None
    ):
        """Log migration transaction for rollback purposes"""
        transaction_log_data = json.loads(self.transaction_log) if self.transaction_log else []

        transaction_entry = {
            "timestamp": now_datetime().isoformat(),
            "action": action,  # 'create', 'update', 'delete'
            "doctype": doctype,
            "record_name": record_name,
            "data": data,
        }

        transaction_log_data.append(transaction_entry)
        self.transaction_log = json.dumps(transaction_log_data)


@frappe.whitelist()
def execute_migration(migration_job_id: str):
    """Execute migration job in background"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)
        migration_job.status = "Running"
        migration_job.save()

        # Import migration framework and execute
        from universal_workshop.data_migration.migration_framework import MigrationFramework

        framework = MigrationFramework(migration_job)
        framework.execute()

        migration_job.status = "Completed"
        migration_job.completed_at = now_datetime()
        migration_job.save()

    except Exception as e:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)
        migration_job.status = "Failed"
        migration_job.completed_at = now_datetime()
        migration_job.log_error(f"Migration execution failed: {str(e)}")
        migration_job.save()

        frappe.log_error(
            f"Migration job {migration_job_id} failed: {str(e)}", "Migration Execution Error"
        )
        raise


@frappe.whitelist()
def get_migration_templates():
    """Get predefined migration templates"""
    return {
        "customer_import": {
            "name": _("Customer Import"),
            "name_ar": "استيراد العملاء",
            "target_doctype": "Customer",
            "field_mapping": {
                "customer_name": "name",
                "customer_name_ar": "arabic_name",
                "email_id": "email",
                "mobile_no": "phone",
                "customer_group": "group",
            },
            "validation_rules": {
                "required_fields": ["customer_name", "email_id"],
                "email_validation": True,
                "phone_format": "+968",
            },
        },
        "vehicle_import": {
            "name": _("Vehicle Import"),
            "name_ar": "استيراد المركبات",
            "target_doctype": "Vehicle Profile",
            "field_mapping": {
                "vin_number": "vin",
                "license_plate": "plate_number",
                "make": "make",
                "model": "model",
                "year": "year",
                "customer": "owner",
            },
            "validation_rules": {
                "required_fields": ["vin_number", "license_plate", "customer"],
                "vin_validation": True,
                "year_range": [1950, 2024],
            },
        },
        "parts_import": {
            "name": _("Parts Inventory Import"),
            "name_ar": "استيراد مخزون القطع",
            "target_doctype": "Item",
            "field_mapping": {
                "item_code": "item_code",
                "item_name": "item_name",
                "item_name_ar": "item_name_arabic",
                "standard_rate": "rate",
                "item_group": "item_group",
            },
            "validation_rules": {
                "required_fields": ["item_code", "item_name"],
                "rate_validation": True,
                "duplicate_check": "item_code",
            },
        },
    }


@frappe.whitelist()
def get_field_mapping_suggestions(source_fields: List[str], target_doctype: str):
    """Get intelligent field mapping suggestions"""
    if not target_doctype:
        return {}

    # Get target DocType meta
    meta = frappe.get_meta(target_doctype)
    target_fields = [
        df.fieldname
        for df in meta.fields
        if df.fieldtype not in ["Section Break", "Column Break", "Tab Break"]
    ]

    suggestions = {}

    # Smart mapping based on field names and patterns
    for source_field in source_fields:
        source_lower = source_field.lower().replace("_", "").replace(" ", "")

        # Direct name match
        if source_field in target_fields:
            suggestions[source_field] = source_field
            continue

        # Pattern matching
        best_match = None
        best_score = 0

        for target_field in target_fields:
            target_lower = target_field.lower().replace("_", "")

            # Calculate similarity score
            if source_lower in target_lower or target_lower in source_lower:
                score = len(set(source_lower) & set(target_lower)) / len(
                    set(source_lower) | set(target_lower)
                )
                if score > best_score:
                    best_score = score
                    best_match = target_field

        if best_match and best_score > 0.5:
            suggestions[source_field] = best_match

    return suggestions
