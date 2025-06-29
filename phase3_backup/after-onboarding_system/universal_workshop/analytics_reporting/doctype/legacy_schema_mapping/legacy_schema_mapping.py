# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
import re
from difflib import SequenceMatcher
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, MetaData, inspect
import pandas as pd


class LegacySchemaMapping(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate schema mapping configuration"""
        self.validate_target_doctype()
        self.validate_database_connection()
        self.calculate_mapping_analytics()

    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.today()

    def validate_target_doctype(self):
        """Validate target DocType exists and is accessible"""
        if not frappe.db.exists("DocType", self.target_doctype):
            frappe.throw(_("Target DocType '{0}' does not exist").format(self.target_doctype))

    def validate_database_connection(self):
        """Test database connection if connection string provided"""
        if self.connection_string and self.legacy_database_type in [
            "MySQL",
            "PostgreSQL",
            "SQL Server",
            "Oracle",
        ]:
            try:
                engine = create_engine(self.connection_string)
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
            except Exception as e:
                frappe.throw(_("Database connection failed: {0}").format(str(e)))

    def calculate_mapping_analytics(self):
        """Calculate mapping analytics and scores"""
        total_fields = len(self.field_mappings or [])
        mapped_fields = len([m for m in (self.field_mappings or []) if m.mapping_type != "Skip"])
        custom_fields = len(
            [m for m in (self.field_mappings or []) if m.mapping_type == "Custom Field"]
        )
        transformations = len([m for m in (self.field_mappings or []) if m.transformation_needed])

        self.total_fields = total_fields
        self.mapped_fields = mapped_fields
        self.custom_fields_needed = custom_fields
        self.transformation_count = transformations

        # Calculate compatibility score
        if total_fields > 0:
            direct_mappings = len(
                [m for m in (self.field_mappings or []) if m.mapping_type == "Direct"]
            )
            self.compatibility_score = (direct_mappings / total_fields) * 100
        else:
            self.compatibility_score = 0

        # Calculate data quality score (based on confidence levels)
        if self.field_mappings:
            total_confidence = sum([float(m.mapping_confidence or 0) for m in self.field_mappings])
            self.data_quality_score = total_confidence / len(self.field_mappings)
        else:
            self.data_quality_score = 0

        # Determine migration readiness
        self.set_migration_readiness()

        # Generate mapping summary
        self.generate_mapping_summary()

    def set_migration_readiness(self):
        """Determine migration readiness based on various factors"""
        if self.compatibility_score >= 80 and self.transformation_count == 0:
            self.migration_readiness = "Ready"
        elif self.custom_fields_needed > 0:
            self.migration_readiness = "Needs Custom Fields"
        elif self.transformation_count > 0:
            self.migration_readiness = "Needs Transformations"
        elif self.compatibility_score < 50:
            self.migration_readiness = "Complex Migration"
        else:
            self.migration_readiness = "Not Ready"

    def generate_mapping_summary(self):
        """Generate human-readable mapping summary"""
        summary_parts = []

        if self.total_fields:
            summary_parts.append(f"Total Fields: {self.total_fields}")
            summary_parts.append(f"Successfully Mapped: {self.mapped_fields}")
            summary_parts.append(f"Compatibility Score: {self.compatibility_score:.1f}%")

        if self.custom_fields_needed:
            summary_parts.append(f"Custom Fields Required: {self.custom_fields_needed}")

        if self.transformation_count:
            summary_parts.append(f"Transformations Required: {self.transformation_count}")

        summary_parts.append(f"Migration Status: {self.migration_readiness}")

        self.mapping_summary = "\n".join(summary_parts)


@frappe.whitelist()
def analyze_legacy_schema(mapping_id):
    """Analyze legacy schema and suggest field mappings"""
    mapping_doc = frappe.get_doc("Legacy Schema Mapping", mapping_id)

    try:
        # Get legacy schema structure
        legacy_fields = get_legacy_schema_structure(mapping_doc)

        # Get target ERPNext DocType structure
        target_fields = get_erpnext_doctype_structure(mapping_doc.target_doctype)

        # Generate intelligent field mappings
        suggested_mappings = generate_field_mappings(legacy_fields, target_fields)

        # Clear existing mappings
        mapping_doc.field_mappings = []

        # Add suggested mappings
        for mapping in suggested_mappings:
            mapping_doc.append("field_mappings", mapping)

        # Save the document
        mapping_doc.save()

        return {
            "status": "success",
            "message": _("Schema analysis completed successfully"),
            "mappings_found": len(suggested_mappings),
            "legacy_fields": len(legacy_fields),
            "target_fields": len(target_fields),
        }

    except Exception as e:
        frappe.log_error(f"Schema analysis failed: {str(e)}")
        return {"status": "error", "message": _("Schema analysis failed: {0}").format(str(e))}


def get_legacy_schema_structure(mapping_doc):
    """Get schema structure from legacy system"""
    if mapping_doc.legacy_database_type in ["MySQL", "PostgreSQL", "SQL Server", "Oracle"]:
        return get_database_schema_structure(mapping_doc)
    elif mapping_doc.legacy_database_type in ["CSV", "Excel"]:
        return get_file_schema_structure(mapping_doc)
    elif mapping_doc.legacy_database_type == "JSON":
        return get_json_schema_structure(mapping_doc)
    else:
        frappe.throw(
            _("Unsupported legacy database type: {0}").format(mapping_doc.legacy_database_type)
        )


def get_database_schema_structure(mapping_doc):
    """Get schema structure from database connection"""
    try:
        engine = create_engine(mapping_doc.connection_string)
        inspector = inspect(engine)

        columns = inspector.get_columns(mapping_doc.legacy_table)

        fields = []
        for column in columns:
            fields.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "default": column.get("default"),
                    "primary_key": column.get("primary_key", False),
                    "autoincrement": column.get("autoincrement", False),
                }
            )

        return fields

    except Exception as e:
        frappe.throw(_("Failed to analyze database schema: {0}").format(str(e)))


def get_file_schema_structure(mapping_doc):
    """Get schema structure from file analysis"""
    # This would analyze file structure - simplified for demo
    return [
        {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
        {"name": "name", "type": "VARCHAR(255)", "nullable": False},
        {"name": "email", "type": "VARCHAR(255)", "nullable": True},
        {"name": "created_date", "type": "DATE", "nullable": True},
    ]


def get_json_schema_structure(mapping_doc):
    """Get schema structure from JSON analysis"""
    # This would analyze JSON structure - simplified for demo
    return [
        {"name": "id", "type": "NUMBER", "nullable": False},
        {"name": "name", "type": "STRING", "nullable": False},
        {"name": "metadata", "type": "OBJECT", "nullable": True},
    ]


def get_erpnext_doctype_structure(doctype_name):
    """Get ERPNext DocType field structure"""
    doctype = frappe.get_meta(doctype_name)
    fields = []

    for field in doctype.fields:
        if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "Heading"]:
            fields.append(
                {
                    "fieldname": field.fieldname,
                    "label": field.label,
                    "fieldtype": field.fieldtype,
                    "reqd": field.reqd,
                    "unique": field.unique,
                    "options": field.options,
                    "default": field.default,
                }
            )

    return fields


def generate_field_mappings(legacy_fields, target_fields):
    """Generate intelligent field mappings using similarity algorithms"""
    mappings = []

    # Create lookup dictionaries for faster matching
    target_by_name = {f["fieldname"].lower(): f for f in target_fields}
    target_by_label = {f["label"].lower(): f for f in target_fields if f["label"]}

    for legacy_field in legacy_fields:
        mapping = create_field_mapping(legacy_field, target_by_name, target_by_label, target_fields)
        mappings.append(mapping)

    return mappings


def create_field_mapping(legacy_field, target_by_name, target_by_label, all_target_fields):
    """Create a single field mapping with confidence scoring"""
    legacy_name = legacy_field["name"].lower()
    best_match = None
    best_confidence = 0
    mapping_type = "Skip"

    # Try direct name matching first
    if legacy_name in target_by_name:
        best_match = target_by_name[legacy_name]
        best_confidence = 100
        mapping_type = "Direct"

    # Try fuzzy name matching
    if not best_match or best_confidence < 80:
        for target_field in all_target_fields:
            similarity = SequenceMatcher(
                None, legacy_name, target_field["fieldname"].lower()
            ).ratio()
            confidence = similarity * 100

            if confidence > best_confidence and confidence > 60:
                best_match = target_field
                best_confidence = confidence
                mapping_type = "Transform" if confidence < 90 else "Direct"

    # Try label matching if available
    if not best_match or best_confidence < 60:
        for label, target_field in target_by_label.items():
            similarity = SequenceMatcher(None, legacy_name, label).ratio()
            confidence = similarity * 80  # Lower confidence for label matching

            if confidence > best_confidence and confidence > 50:
                best_match = target_field
                best_confidence = confidence
                mapping_type = "Transform"

    # Determine field type mapping
    target_fieldtype = map_legacy_type_to_erpnext(legacy_field.get("type", ""))
    transformation_needed = False
    transformation_type = None

    if best_match:
        if best_match["fieldtype"] != target_fieldtype:
            transformation_needed = True
            transformation_type = get_transformation_type(
                legacy_field.get("type", ""), best_match["fieldtype"]
            )
    else:
        # Suggest custom field creation
        mapping_type = "Custom Field"
        best_match = {
            "fieldname": suggest_fieldname(legacy_field["name"]),
            "label": legacy_field["name"].replace("_", " ").title(),
            "fieldtype": target_fieldtype,
        }
        best_confidence = 50

    return {
        "legacy_field_name": legacy_field["name"],
        "legacy_field_type": legacy_field.get("type", ""),
        "legacy_field_size": extract_field_size(legacy_field.get("type", "")),
        "target_field_name": best_match["fieldname"] if best_match else "",
        "target_field_type": best_match["fieldtype"] if best_match else target_fieldtype,
        "mapping_type": mapping_type,
        "is_required": not legacy_field.get("nullable", True),
        "is_unique": legacy_field.get("primary_key", False),
        "transformation_needed": transformation_needed,
        "transformation_type": transformation_type,
        "mapping_confidence": best_confidence,
        "mapping_notes": generate_mapping_notes(legacy_field, best_match, best_confidence),
    }


def map_legacy_type_to_erpnext(legacy_type):
    """Map legacy database types to ERPNext field types"""
    type_mapping = {
        "VARCHAR": "Data",
        "CHAR": "Data",
        "TEXT": "Text",
        "LONGTEXT": "Long Text",
        "INT": "Int",
        "INTEGER": "Int",
        "BIGINT": "Int",
        "DECIMAL": "Float",
        "FLOAT": "Float",
        "DOUBLE": "Float",
        "DATE": "Date",
        "DATETIME": "Datetime",
        "TIMESTAMP": "Datetime",
        "TIME": "Time",
        "BOOLEAN": "Check",
        "BOOL": "Check",
        "JSON": "JSON",
        "BLOB": "Attach",
        "BINARY": "Attach",
    }

    # Extract base type (remove size specifications)
    base_type = re.sub(r"\([^)]*\)", "", str(legacy_type)).upper().strip()

    return type_mapping.get(base_type, "Data")


def extract_field_size(legacy_type):
    """Extract field size from legacy type definition"""
    match = re.search(r"\((\d+(?:,\d+)?)\)", str(legacy_type))
    return match.group(1) if match else None


def get_transformation_type(legacy_type, target_type):
    """Determine transformation type needed between legacy and target types"""
    transformations = {
        ("VARCHAR", "Date"): "Date Format",
        ("VARCHAR", "Datetime"): "Date Format",
        ("VARCHAR", "Currency"): "Currency Format",
        ("TEXT", "Data"): "Text Case",
        ("INT", "Currency"): "Currency Format",
    }

    base_legacy = re.sub(r"\([^)]*\)", "", str(legacy_type)).upper().strip()
    return transformations.get((base_legacy, target_type), "Custom Function")


def suggest_fieldname(legacy_name):
    """Suggest ERPNext-compatible fieldname"""
    # Convert to snake_case
    fieldname = re.sub(r"[^a-zA-Z0-9_]", "_", legacy_name.lower())
    fieldname = re.sub(r"_+", "_", fieldname)  # Remove multiple underscores
    fieldname = fieldname.strip("_")  # Remove leading/trailing underscores

    # Add custom prefix to avoid conflicts
    return f"custom_{fieldname}"


def generate_mapping_notes(legacy_field, target_field, confidence):
    """Generate helpful notes for the field mapping"""
    notes = []

    if confidence == 100:
        notes.append("Exact field name match found")
    elif confidence >= 80:
        notes.append("High confidence match based on field name similarity")
    elif confidence >= 60:
        notes.append("Moderate confidence match - manual review recommended")
    elif confidence >= 50:
        notes.append("Low confidence match - requires custom field creation")
    else:
        notes.append("No suitable match found - manual mapping required")

    if legacy_field.get("primary_key"):
        notes.append("Source field is primary key")

    if not legacy_field.get("nullable", True):
        notes.append("Source field is required")

    return "; ".join(notes)


@frappe.whitelist()
def create_custom_fields(mapping_id):
    """Create custom fields based on mapping configuration"""
    mapping_doc = frappe.get_doc("Legacy Schema Mapping", mapping_id)

    created_fields = []
    failed_fields = []

    for custom_field_config in mapping_doc.custom_fields_config:
        try:
            # Check if custom field already exists
            existing_field = frappe.db.exists(
                "Custom Field",
                {
                    "dt": mapping_doc.target_doctype,
                    "fieldname": custom_field_config.custom_fieldname,
                },
            )

            if existing_field:
                custom_field_config.creation_status = "Skipped"
                custom_field_config.error_message = "Field already exists"
                continue

            # Create custom field
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = mapping_doc.target_doctype
            custom_field.fieldname = custom_field_config.custom_fieldname
            custom_field.label = custom_field_config.custom_label
            custom_field.fieldtype = custom_field_config.fieldtype
            custom_field.reqd = custom_field_config.reqd
            custom_field.unique = custom_field_config.unique
            custom_field.in_list_view = custom_field_config.in_list_view

            if custom_field_config.options:
                custom_field.options = custom_field_config.options
            if custom_field_config.default_value:
                custom_field.default = custom_field_config.default_value
            if custom_field_config.description:
                custom_field.description = custom_field_config.description
            if custom_field_config.depends_on:
                custom_field.depends_on = custom_field_config.depends_on
            if custom_field_config.width:
                custom_field.width = custom_field_config.width

            custom_field.read_only = custom_field_config.read_only

            custom_field.insert()

            # Update status
            custom_field_config.creation_status = "Created"
            custom_field_config.field_creation_date = frappe.utils.now()
            created_fields.append(custom_field_config.custom_fieldname)

        except Exception as e:
            custom_field_config.creation_status = "Failed"
            custom_field_config.error_message = str(e)
            failed_fields.append(
                {"fieldname": custom_field_config.custom_fieldname, "error": str(e)}
            )

    # Save the mapping document with updated statuses
    mapping_doc.save()

    return {
        "status": "completed",
        "created_fields": created_fields,
        "failed_fields": failed_fields,
        "total_created": len(created_fields),
        "total_failed": len(failed_fields),
    }


@frappe.whitelist()
def generate_mapping_template(target_doctype, legacy_system_name):
    """Generate a template mapping for common legacy systems"""
    templates = get_mapping_templates()

    if legacy_system_name.lower() in templates:
        template = templates[legacy_system_name.lower()]

        # Create new mapping document
        mapping_doc = frappe.new_doc("Legacy Schema Mapping")
        mapping_doc.mapping_name = f"{legacy_system_name} to {target_doctype} Mapping"
        mapping_doc.mapping_name_ar = f"تخطيط {legacy_system_name} إلى {target_doctype}"
        mapping_doc.legacy_system = legacy_system_name
        mapping_doc.target_doctype = target_doctype
        mapping_doc.legacy_table = template.get("default_table", "main_table")
        mapping_doc.legacy_database_type = template.get("database_type", "MySQL")

        # Add template field mappings
        for field_mapping in template.get("field_mappings", []):
            mapping_doc.append("field_mappings", field_mapping)

        # Add template transformation rules
        for transformation in template.get("transformations", []):
            mapping_doc.append("transformation_rules", transformation)

        mapping_doc.insert()

        return {
            "status": "success",
            "mapping_id": mapping_doc.name,
            "message": _("Template mapping created successfully"),
        }
    else:
        return {
            "status": "error",
            "message": _("No template available for {0}").format(legacy_system_name),
        }


def get_mapping_templates():
    """Get predefined mapping templates for common legacy systems"""
    return {
        "quickbooks": {
            "database_type": "Access",
            "default_table": "customers",
            "field_mappings": [
                {
                    "legacy_field_name": "customer_id",
                    "target_field_name": "name",
                    "mapping_type": "Direct",
                    "legacy_field_type": "INT",
                    "target_field_type": "Data",
                },
                {
                    "legacy_field_name": "company_name",
                    "target_field_name": "customer_name",
                    "mapping_type": "Direct",
                    "legacy_field_type": "VARCHAR",
                    "target_field_type": "Data",
                },
            ],
            "transformations": [],
        },
        "excel_workshop": {
            "database_type": "Excel",
            "default_table": "Sheet1",
            "field_mappings": [
                {
                    "legacy_field_name": "Customer Name",
                    "target_field_name": "customer_name",
                    "mapping_type": "Transform",
                    "legacy_field_type": "TEXT",
                    "target_field_type": "Data",
                    "transformation_needed": True,
                    "transformation_type": "Text Case",
                }
            ],
            "transformations": [
                {
                    "rule_name": "Normalize Customer Names",
                    "rule_type": "Text Case",
                    "source_field": "Customer Name",
                    "target_field": "customer_name",
                    "transformation_function": "title_case",
                }
            ],
        },
    }
