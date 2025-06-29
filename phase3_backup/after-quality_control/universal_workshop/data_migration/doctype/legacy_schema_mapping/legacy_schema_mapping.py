# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, flt, cint


class LegacySchemaMapping(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate legacy schema mapping configuration"""
        self.validate_mapping_configuration()
        self.validate_field_mappings()
        self.validate_transformation_rules()

    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = now_datetime()

    def validate_mapping_configuration(self):
        """Validate basic mapping configuration"""
        if not self.mapping_name:
            frappe.throw(_("Mapping name is required"))

        if not self.target_doctype:
            frappe.throw(_("Target DocType is required"))

        if not self.legacy_table_name:
            frappe.throw(_("Legacy table/source name is required"))

        # Validate target DocType exists
        if not frappe.db.exists("DocType", self.target_doctype):
            frappe.throw(_("Target DocType {0} does not exist").format(self.target_doctype))

    def validate_field_mappings(self):
        """Validate field mapping configuration"""
        if not self.field_mappings:
            return

        try:
            mappings = (
                json.loads(self.field_mappings)
                if isinstance(self.field_mappings, str)
                else self.field_mappings
            )

            # Get target DocType fields
            target_meta = frappe.get_meta(self.target_doctype)
            target_fields = [field.fieldname for field in target_meta.fields]

            # Validate each mapping
            for source_field, target_field in mappings.items():
                if target_field not in target_fields:
                    frappe.throw(
                        _("Target field {0} does not exist in {1}").format(
                            target_field, self.target_doctype
                        )
                    )

        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON format in field mappings"))

    def validate_transformation_rules(self):
        """Validate transformation rules configuration"""
        if not self.transformation_rules:
            return

        try:
            rules = (
                json.loads(self.transformation_rules)
                if isinstance(self.transformation_rules, str)
                else self.transformation_rules
            )

            # Validate rule structure
            for field_name, rule_config in rules.items():
                if not isinstance(rule_config, dict):
                    frappe.throw(_("Invalid transformation rule for field {0}").format(field_name))

                rule_type = rule_config.get("type")
                if rule_type not in [
                    "format_conversion",
                    "data_cleansing",
                    "value_mapping",
                    "calculation",
                ]:
                    frappe.throw(_("Invalid transformation rule type: {0}").format(rule_type))

        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON format in transformation rules"))

    @frappe.whitelist()
    def test_mapping(self):
        """Test the schema mapping with sample data"""
        try:
            # Get sample data
            sample_data = self.get_sample_data()

            # Apply field mappings
            mapped_data = self.apply_field_mappings(sample_data)

            # Apply transformations
            transformed_data = self.apply_transformations(mapped_data)

            # Validate against target schema
            validation_results = self.validate_against_target_schema(transformed_data)

            # Update test results
            test_results = {
                "test_timestamp": now_datetime().isoformat(),
                "sample_records": len(sample_data),
                "mapped_successfully": len(mapped_data),
                "transformation_success": len(transformed_data),
                "validation_results": validation_results,
                "status": "success" if validation_results["valid_records"] > 0 else "failed",
            }

            self.test_results = json.dumps(test_results)
            self.last_tested = now_datetime()
            self.save()

            return test_results

        except Exception as e:
            error_result = {
                "test_timestamp": now_datetime().isoformat(),
                "status": "error",
                "error_message": str(e),
            }
            self.test_results = json.dumps(error_result)
            self.save()
            frappe.throw(_("Mapping test failed: {0}").format(str(e)))

    def get_sample_data(self) -> List[Dict]:
        """Get sample data for testing"""
        if self.sample_data:
            try:
                return (
                    json.loads(self.sample_data)
                    if isinstance(self.sample_data, str)
                    else self.sample_data
                )
            except json.JSONDecodeError:
                pass

        # Generate sample data based on legacy system type
        if self.legacy_system_type in ["CSV", "Excel"]:
            return self._generate_file_sample_data()
        elif self.legacy_system_type in ["MySQL", "PostgreSQL", "SQL Server", "Oracle"]:
            return self._generate_database_sample_data()
        else:
            return []

    def _generate_file_sample_data(self) -> List[Dict]:
        """Generate sample data for file-based sources"""
        # Return mock data structure
        return [
            {
                "id": "1",
                "name": "Sample Customer",
                "email": "customer@example.com",
                "phone": "+968 24123456",
                "address": "Muscat, Oman",
            },
            {
                "id": "2",
                "name": "عميل تجريبي",
                "email": "arabic@example.com",
                "phone": "+968 24654321",
                "address": "صلالة، عمان",
            },
        ]

    def _generate_database_sample_data(self) -> List[Dict]:
        """Generate sample data for database sources"""
        if self.test_query:
            try:
                # Execute test query (limited to 10 records for safety)
                limited_query = f"SELECT * FROM ({self.test_query}) AS sample_query LIMIT 10"
                return frappe.db.sql(limited_query, as_dict=True)
            except Exception:
                pass

        return self._generate_file_sample_data()

    def apply_field_mappings(self, data: List[Dict]) -> List[Dict]:
        """Apply field mappings to data"""
        if not self.field_mappings or not data:
            return data

        mappings = (
            json.loads(self.field_mappings)
            if isinstance(self.field_mappings, str)
            else self.field_mappings
        )
        mapped_data = []

        for record in data:
            mapped_record = {}

            # Apply field mappings
            for source_field, target_field in mappings.items():
                if source_field in record:
                    mapped_record[target_field] = record[source_field]

            # Include unmapped fields
            for field, value in record.items():
                if field not in mappings and field not in mapped_record:
                    mapped_record[field] = value

            mapped_data.append(mapped_record)

        return mapped_data

    def apply_transformations(self, data: List[Dict]) -> List[Dict]:
        """Apply transformation rules to data"""
        if not self.transformation_rules or not data:
            return data

        rules = (
            json.loads(self.transformation_rules)
            if isinstance(self.transformation_rules, str)
            else self.transformation_rules
        )
        transformed_data = []

        for record in data:
            transformed_record = record.copy()

            for field_name, rule_config in rules.items():
                if field_name in transformed_record:
                    transformed_record[field_name] = self._apply_transformation_rule(
                        transformed_record[field_name], rule_config
                    )

            transformed_data.append(transformed_record)

        return transformed_data

    def _apply_transformation_rule(self, value: Any, rule_config: Dict) -> Any:
        """Apply a single transformation rule"""
        rule_type = rule_config.get("type")

        if rule_type == "format_conversion":
            return self._apply_format_conversion(value, rule_config)
        elif rule_type == "data_cleansing":
            return self._apply_data_cleansing(value, rule_config)
        elif rule_type == "value_mapping":
            return self._apply_value_mapping(value, rule_config)
        elif rule_type == "calculation":
            return self._apply_calculation(value, rule_config)
        else:
            return value

    def _apply_format_conversion(self, value: Any, rule_config: Dict) -> Any:
        """Apply format conversion transformation"""
        conversion_type = rule_config.get("conversion_type")

        if conversion_type == "date_format":
            from_format = rule_config.get("from_format", "%Y-%m-%d")
            to_format = rule_config.get("to_format", "%d/%m/%Y")
            try:
                date_obj = datetime.strptime(str(value), from_format)
                return date_obj.strftime(to_format)
            except (ValueError, TypeError):
                return value

        elif conversion_type == "phone_format":
            # Standardize phone format for Oman
            phone_str = str(value).strip()
            if not phone_str.startswith("+968"):
                if phone_str.startswith("968"):
                    return f"+{phone_str}"
                elif len(phone_str) == 8:
                    return f"+968 {phone_str}"
            return phone_str

        elif conversion_type == "currency_format":
            try:
                amount = flt(value)
                return f"OMR {amount:,.3f}"
            except (ValueError, TypeError):
                return value

        return value

    def _apply_data_cleansing(self, value: Any, rule_config: Dict) -> Any:
        """Apply data cleansing transformation"""
        cleansing_type = rule_config.get("cleansing_type")

        if cleansing_type == "trim_whitespace":
            return str(value).strip() if value else value

        elif cleansing_type == "standardize_case":
            case_type = rule_config.get("case_type", "title")
            if case_type == "upper":
                return str(value).upper() if value else value
            elif case_type == "lower":
                return str(value).lower() if value else value
            elif case_type == "title":
                return str(value).title() if value else value

        elif cleansing_type == "remove_special_chars":
            pattern = rule_config.get("pattern", r"[^\w\s]")
            return re.sub(pattern, "", str(value)) if value else value

        elif cleansing_type == "arabic_normalization":
            # Apply Arabic text normalization
            if value:
                text = str(value)
                # Remove diacritics
                text = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", text)
                # Normalize Alef variations
                text = re.sub(r"[آأإ]", "ا", text)
                # Normalize Teh Marbuta
                text = re.sub(r"ة", "ه", text)
                return text.strip()

        return value

    def _apply_value_mapping(self, value: Any, rule_config: Dict) -> Any:
        """Apply value mapping transformation"""
        mapping_table = rule_config.get("mapping_table", {})
        default_value = rule_config.get("default_value")

        mapped_value = mapping_table.get(str(value), default_value)
        return mapped_value if mapped_value is not None else value

    def _apply_calculation(self, value: Any, rule_config: Dict) -> Any:
        """Apply calculation transformation"""
        calculation_type = rule_config.get("calculation_type")

        if calculation_type == "multiply":
            factor = flt(rule_config.get("factor", 1))
            try:
                return flt(value) * factor
            except (ValueError, TypeError):
                return value

        elif calculation_type == "add":
            addend = flt(rule_config.get("addend", 0))
            try:
                return flt(value) + addend
            except (ValueError, TypeError):
                return value

        elif calculation_type == "percentage":
            try:
                return flt(value) / 100
            except (ValueError, TypeError):
                return value

        return value

    def validate_against_target_schema(self, data: List[Dict]) -> Dict:
        """Validate transformed data against target DocType schema"""
        target_meta = frappe.get_meta(self.target_doctype)
        required_fields = [field.fieldname for field in target_meta.fields if field.reqd]

        validation_results = {
            "total_records": len(data),
            "valid_records": 0,
            "invalid_records": 0,
            "validation_errors": [],
        }

        for i, record in enumerate(data):
            record_errors = []

            # Check required fields
            for field in required_fields:
                if field not in record or not record[field]:
                    record_errors.append(f"Missing required field: {field}")

            if record_errors:
                validation_results["invalid_records"] += 1
                validation_results["validation_errors"].append(
                    {"record_index": i, "errors": record_errors}
                )
            else:
                validation_results["valid_records"] += 1

        return validation_results

    @frappe.whitelist()
    def generate_mapping_template(self):
        """Generate field mapping template based on target DocType"""
        target_meta = frappe.get_meta(self.target_doctype)

        template = {
            "field_mappings": {},
            "transformation_rules": {},
            "validation_config": {"required_fields": [], "field_types": {}, "validation_rules": {}},
        }

        # Generate field mapping template
        for field in target_meta.fields:
            if field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]:
                template["field_mappings"][f"legacy_{field.fieldname}"] = field.fieldname
                template["validation_config"]["field_types"][field.fieldname] = field.fieldtype

                if field.reqd:
                    template["validation_config"]["required_fields"].append(field.fieldname)

        # Generate transformation rule templates
        common_transformations = {
            "phone": {"type": "format_conversion", "conversion_type": "phone_format"},
            "email": {"type": "data_cleansing", "cleansing_type": "trim_whitespace"},
            "name": {
                "type": "data_cleansing",
                "cleansing_type": "standardize_case",
                "case_type": "title",
            },
        }

        for field in target_meta.fields:
            if any(keyword in field.fieldname.lower() for keyword in common_transformations.keys()):
                for keyword, rule in common_transformations.items():
                    if keyword in field.fieldname.lower():
                        template["transformation_rules"][field.fieldname] = rule
                        break

        return template

    @frappe.whitelist()
    def export_mapping_config(self):
        """Export complete mapping configuration"""
        config = {
            "mapping_name": self.mapping_name,
            "mapping_name_ar": self.mapping_name_ar,
            "legacy_system_type": self.legacy_system_type,
            "target_doctype": self.target_doctype,
            "legacy_table_name": self.legacy_table_name,
            "field_mappings": json.loads(self.field_mappings) if self.field_mappings else {},
            "transformation_rules": (
                json.loads(self.transformation_rules) if self.transformation_rules else {}
            ),
            "validation_config": (
                json.loads(self.validation_config) if self.validation_config else {}
            ),
            "connection_config": (
                json.loads(self.connection_config) if self.connection_config else {}
            ),
            "test_query": self.test_query,
            "mapping_notes": self.mapping_notes,
            "mapping_notes_ar": self.mapping_notes_ar,
            "export_timestamp": now_datetime().isoformat(),
        }

        return config
