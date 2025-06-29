# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
from typing import Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt

from universal_workshop.data_migration.migration_framework import MigrationFramework
from universal_workshop.data_migration.validation_engine import ValidationEngine, DuplicateDetection
from universal_workshop.data_migration.transaction_manager import TransactionManager


@frappe.whitelist()
def create_migration_job(
    job_title: str,
    job_title_ar: str = None,
    migration_type: str = "Import",
    source_type: str = "CSV",
    target_doctype: str = None,
    source_file: str = None,
    field_mapping: str = None,
    validation_rules: str = None,
    priority: str = "Medium",
) -> str:
    """Create a new migration job"""
    try:
        migration_job = frappe.new_doc("Migration Job")
        migration_job.job_title = job_title
        migration_job.job_title_ar = job_title_ar or ""
        migration_job.migration_type = migration_type
        migration_job.source_type = source_type
        migration_job.target_doctype = target_doctype
        migration_job.source_file = source_file
        migration_job.field_mapping = field_mapping
        migration_job.validation_rules = validation_rules
        migration_job.priority = priority
        migration_job.status = "Draft"
        migration_job.created_by = frappe.session.user
        migration_job.created_date = now_datetime()

        migration_job.insert()

        return migration_job.name

    except Exception as e:
        frappe.throw(_("Failed to create migration job: {0}").format(str(e)))


@frappe.whitelist()
def execute_migration_job(migration_job_id: str) -> Dict:
    """Execute a migration job"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)

        # Validate job can be executed
        if migration_job.status not in ["Draft", "Failed"]:
            frappe.throw(
                _("Migration job cannot be executed in current status: {0}").format(
                    migration_job.status
                )
            )

        # Update status to running
        migration_job.status = "Running"
        migration_job.started_at = now_datetime()
        migration_job.save()

        # Execute migration
        framework = MigrationFramework(migration_job)
        results = framework.execute()

        # Update job with results
        migration_job.status = "Completed" if results.get("success") else "Failed"
        migration_job.completed_at = now_datetime()
        migration_job.total_records = results.get("total_records", 0)
        migration_job.processed_records = results.get("processed_records", 0)
        migration_job.successful_records = results.get("successful_records", 0)
        migration_job.failed_records = results.get("failed_records", 0)
        migration_job.progress_percentage = 100 if results.get("success") else 0

        if results.get("error_log"):
            migration_job.error_log = json.dumps(results["error_log"])

        if results.get("transaction_log"):
            migration_job.transaction_log = json.dumps(results["transaction_log"])

        migration_job.save()

        return {
            "success": results.get("success", False),
            "migration_job_id": migration_job_id,
            "total_records": results.get("total_records", 0),
            "successful_records": results.get("successful_records", 0),
            "failed_records": results.get("failed_records", 0),
            "message": (
                _("Migration completed successfully")
                if results.get("success")
                else _("Migration completed with errors")
            ),
            "message_ar": (
                "تم الترحيل بنجاح" if results.get("success") else "تم الترحيل مع وجود أخطاء"
            ),
        }

    except Exception as e:
        # Update job status to failed
        try:
            migration_job = frappe.get_doc("Migration Job", migration_job_id)
            migration_job.status = "Failed"
            migration_job.completed_at = now_datetime()
            migration_job.save()
        except:
            pass

        frappe.throw(_("Failed to execute migration job: {0}").format(str(e)))


@frappe.whitelist()
def validate_migration_data(migration_job_id: str, sample_size: int = 100) -> Dict:
    """Validate migration data before execution"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)

        # Create validation engine
        validation_config = {}
        if migration_job.validation_rules:
            validation_config = json.loads(migration_job.validation_rules)

        validation_engine = ValidationEngine(validation_config)

        # Get sample data for validation
        framework = MigrationFramework(migration_job)
        adapter = framework._create_adapter()

        sample_data = []
        batch_count = 0
        for batch in adapter.read_data(batch_size=min(sample_size, 100)):
            sample_data.extend(batch)
            batch_count += 1
            if len(sample_data) >= sample_size:
                break

        # Validate sample data
        validation_results = validation_engine.validate_batch(
            sample_data[:sample_size], migration_job.target_doctype
        )

        return {
            "validation_summary": validation_results["summary"],
            "sample_size": len(sample_data),
            "validation_errors": validation_results.get("errors", [])[:10],  # Limit to 10 errors
            "duplicate_detection": validation_results.get("duplicates", {}),
            "recommendations": validation_results.get("recommendations", []),
            "estimated_success_rate": validation_results["summary"].get("success_rate", 0),
            "message": _("Validation completed"),
            "message_ar": "تم التحقق",
        }

    except Exception as e:
        frappe.throw(_("Failed to validate migration data: {0}").format(str(e)))


@frappe.whitelist()
def get_migration_progress(migration_job_id: str) -> Dict:
    """Get real-time migration progress"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)

        progress_data = {
            "migration_job_id": migration_job_id,
            "status": migration_job.status,
            "total_records": migration_job.total_records or 0,
            "processed_records": migration_job.processed_records or 0,
            "successful_records": migration_job.successful_records or 0,
            "failed_records": migration_job.failed_records or 0,
            "progress_percentage": migration_job.progress_percentage or 0,
            "started_at": (
                migration_job.started_at.isoformat() if migration_job.started_at else None
            ),
            "estimated_completion": (
                migration_job.estimated_completion.isoformat()
                if migration_job.estimated_completion
                else None
            ),
            "duration_minutes": migration_job.duration_minutes or 0,
            "memory_usage_mb": migration_job.memory_usage_mb or 0,
            "cpu_usage_percent": migration_job.cpu_usage_percent or 0,
        }

        # Add Arabic status translation
        status_translations = {
            "Draft": "مسودة",
            "Queued": "في الطابور",
            "Running": "قيد التشغيل",
            "Completed": "مكتمل",
            "Failed": "فشل",
            "Cancelled": "ملغى",
            "Rolled Back": "تم التراجع",
        }

        progress_data["status_ar"] = status_translations.get(
            migration_job.status, migration_job.status
        )

        return progress_data

    except Exception as e:
        frappe.throw(_("Failed to get migration progress: {0}").format(str(e)))


@frappe.whitelist()
def cancel_migration_job(migration_job_id: str) -> Dict:
    """Cancel a running migration job"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)

        if migration_job.status not in ["Running", "Queued"]:
            frappe.throw(
                _("Cannot cancel migration job in status: {0}").format(migration_job.status)
            )

        # Update status
        migration_job.status = "Cancelled"
        migration_job.completed_at = now_datetime()
        migration_job.save()

        return {
            "success": True,
            "message": _("Migration job cancelled successfully"),
            "message_ar": "تم إلغاء مهمة الترحيل بنجاح",
        }

    except Exception as e:
        frappe.throw(_("Failed to cancel migration job: {0}").format(str(e)))


@frappe.whitelist()
def get_migration_error_log(migration_job_id: str) -> Dict:
    """Get detailed error log for a migration job"""
    try:
        migration_job = frappe.get_doc("Migration Job", migration_job_id)

        error_log = []
        if migration_job.error_log:
            error_log = json.loads(migration_job.error_log)

        return {
            "migration_job_id": migration_job_id,
            "total_errors": len(error_log),
            "errors": error_log,
            "error_categories": _categorize_errors(error_log),
            "suggestions": _generate_error_suggestions(error_log),
        }

    except Exception as e:
        frappe.throw(_("Failed to get migration error log: {0}").format(str(e)))


@frappe.whitelist()
def detect_duplicates(doctype: str, data: str, similarity_threshold: float = 0.8) -> Dict:
    """Detect potential duplicates in migration data"""
    try:
        # Parse data
        records = json.loads(data) if isinstance(data, str) else data

        # Detect duplicates based on doctype
        if doctype == "Customer":
            duplicates = DuplicateDetection.find_similar_customers(
                records[0] if records else {}, similarity_threshold
            )
        elif doctype == "Vehicle":
            duplicates = DuplicateDetection.find_similar_vehicles(
                records[0] if records else {}, similarity_threshold
            )
        else:
            # Generic duplicate detection
            duplicates = []

        return {
            "total_records": len(records),
            "potential_duplicates": len(duplicates),
            "duplicates": duplicates[:10],  # Limit to 10 results
            "similarity_threshold": similarity_threshold,
            "recommendations": _generate_duplicate_recommendations(duplicates),
        }

    except Exception as e:
        frappe.throw(_("Failed to detect duplicates: {0}").format(str(e)))


@frappe.whitelist()
def generate_field_mapping_suggestions(source_fields: str, target_doctype: str) -> Dict:
    """Generate intelligent field mapping suggestions"""
    try:
        # Parse source fields
        fields = json.loads(source_fields) if isinstance(source_fields, str) else source_fields

        # Get target DocType metadata
        target_meta = frappe.get_meta(target_doctype)
        target_fields = {field.fieldname: field for field in target_meta.fields}

        # Generate mapping suggestions
        suggestions = {}
        confidence_scores = {}

        for source_field in fields:
            best_match = _find_best_field_match(source_field, target_fields)
            if best_match:
                suggestions[source_field] = best_match["fieldname"]
                confidence_scores[source_field] = best_match["confidence"]

        return {
            "source_fields": fields,
            "target_doctype": target_doctype,
            "suggested_mappings": suggestions,
            "confidence_scores": confidence_scores,
            "unmapped_fields": [f for f in fields if f not in suggestions],
            "target_fields": list(target_fields.keys()),
        }

    except Exception as e:
        frappe.throw(_("Failed to generate field mapping suggestions: {0}").format(str(e)))


@frappe.whitelist()
def export_migration_template(target_doctype: str) -> Dict:
    """Export migration template for a DocType"""
    try:
        target_meta = frappe.get_meta(target_doctype)

        # Generate template structure
        template = {
            "doctype": target_doctype,
            "fields": [],
            "required_fields": [],
            "field_types": {},
            "sample_data": [],
            "validation_rules": {},
            "transformation_examples": {},
        }

        for field in target_meta.fields:
            if field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]:
                template["fields"].append(field.fieldname)
                template["field_types"][field.fieldname] = field.fieldtype

                if field.reqd:
                    template["required_fields"].append(field.fieldname)

                # Add validation rules
                if field.fieldtype == "Email":
                    template["validation_rules"][field.fieldname] = {"type": "email"}
                elif field.fieldtype == "Phone":
                    template["validation_rules"][field.fieldname] = {
                        "type": "phone",
                        "country_code": "+968",
                    }
                elif field.fieldtype == "Date":
                    template["validation_rules"][field.fieldname] = {"type": "date"}

        # Generate sample data
        sample_record = {}
        for field_name in template["fields"][:10]:  # Limit to 10 fields for sample
            field_type = template["field_types"][field_name]
            sample_record[field_name] = _generate_sample_value(field_name, field_type)

        template["sample_data"].append(sample_record)

        return template

    except Exception as e:
        frappe.throw(_("Failed to export migration template: {0}").format(str(e)))


def _categorize_errors(error_log: List[Dict]) -> Dict:
    """Categorize migration errors"""
    categories = {
        "validation_errors": 0,
        "permission_errors": 0,
        "duplicate_errors": 0,
        "format_errors": 0,
        "reference_errors": 0,
        "other_errors": 0,
    }

    for error in error_log:
        error_message = error.get("error", "").lower()

        if "validation" in error_message or "required" in error_message:
            categories["validation_errors"] += 1
        elif "permission" in error_message or "access" in error_message:
            categories["permission_errors"] += 1
        elif "duplicate" in error_message or "already exists" in error_message:
            categories["duplicate_errors"] += 1
        elif "format" in error_message or "invalid" in error_message:
            categories["format_errors"] += 1
        elif "reference" in error_message or "link" in error_message:
            categories["reference_errors"] += 1
        else:
            categories["other_errors"] += 1

    return categories


def _generate_error_suggestions(error_log: List[Dict]) -> List[str]:
    """Generate suggestions based on error patterns"""
    suggestions = []

    error_categories = _categorize_errors(error_log)

    if error_categories["validation_errors"] > 0:
        suggestions.append(_("Review validation rules and ensure required fields are mapped"))
        suggestions.append("راجع قواعد التحقق وتأكد من تطابق الحقول المطلوبة")

    if error_categories["duplicate_errors"] > 0:
        suggestions.append(_("Enable duplicate detection and merging"))
        suggestions.append("فعّل كشف التكرار والدمج")

    if error_categories["format_errors"] > 0:
        suggestions.append(_("Add data transformation rules for format conversion"))
        suggestions.append("أضف قواعد تحويل البيانات لتحويل التنسيق")

    return suggestions


def _generate_duplicate_recommendations(duplicates: List[Dict]) -> List[str]:
    """Generate recommendations for handling duplicates"""
    recommendations = []

    if len(duplicates) > 0:
        recommendations.extend(
            [
                _("Review potential duplicates before migration"),
                "راجع التكرارات المحتملة قبل الترحيل",
                _("Consider implementing automatic merge rules"),
                "فكر في تطبيق قواعد الدمج التلقائي",
                _("Use higher similarity threshold for stricter matching"),
                "استخدم عتبة تشابه أعلى لمطابقة أكثر صرامة",
            ]
        )

    return recommendations


def _find_best_field_match(source_field: str, target_fields: Dict) -> Optional[Dict]:
    """Find best matching target field for source field"""
    import difflib

    source_lower = source_field.lower()
    best_match = None
    best_score = 0

    for target_field, field_meta in target_fields.items():
        target_lower = target_field.lower()

        # Direct match
        if source_lower == target_lower:
            return {"fieldname": target_field, "confidence": 1.0}

        # Similarity matching
        similarity = difflib.SequenceMatcher(None, source_lower, target_lower).ratio()

        # Boost score for common patterns
        if any(keyword in source_lower for keyword in ["name", "title"]) and any(
            keyword in target_lower for keyword in ["name", "title"]
        ):
            similarity += 0.2

        if any(keyword in source_lower for keyword in ["email", "mail"]) and any(
            keyword in target_lower for keyword in ["email", "mail"]
        ):
            similarity += 0.3

        if any(keyword in source_lower for keyword in ["phone", "mobile", "tel"]) and any(
            keyword in target_lower for keyword in ["phone", "mobile", "tel"]
        ):
            similarity += 0.3

        if similarity > best_score and similarity > 0.6:
            best_score = similarity
            best_match = {"fieldname": target_field, "confidence": similarity}

    return best_match


def _generate_sample_value(field_name: str, field_type: str) -> str:
    """Generate sample value for field"""
    field_lower = field_name.lower()

    if "name" in field_lower:
        return "Sample Name" if "ar" not in field_lower else "اسم تجريبي"
    elif "email" in field_lower:
        return "sample@example.com"
    elif "phone" in field_lower:
        return "+968 24123456"
    elif "address" in field_lower:
        return "Muscat, Oman" if "ar" not in field_lower else "مسقط، عمان"
    elif field_type == "Date":
        return "2024-01-01"
    elif field_type == "Currency":
        return "100.000"
    elif field_type == "Int":
        return "1"
    elif field_type == "Float":
        return "1.0"
    else:
        return "Sample Value"
