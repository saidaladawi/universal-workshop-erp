# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
import re
from difflib import SequenceMatcher
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


class SchemaAlignmentEngine:
    """Advanced schema alignment and field mapping engine"""

    def __init__(self):
        self.mapping_confidence_threshold = 60
        self.transformation_rules = {}
        self.field_similarity_cache = {}

    def analyze_schema_compatibility(self, legacy_schema: Dict, target_schema: Dict) -> Dict:
        """Analyze compatibility between legacy and target schemas"""

        legacy_fields = legacy_schema.get("fields", [])
        target_fields = target_schema.get("fields", [])

        # Generate field mappings
        mappings = self.generate_intelligent_mappings(legacy_fields, target_fields)

        # Calculate compatibility metrics
        metrics = self.calculate_compatibility_metrics(mappings, legacy_fields, target_fields)

        # Generate recommendations
        recommendations = self.generate_migration_recommendations(metrics, mappings)

        return {
            "mappings": mappings,
            "metrics": metrics,
            "recommendations": recommendations,
            "analysis_timestamp": frappe.utils.now(),
            "schema_versions": {
                "legacy": legacy_schema.get("version", "unknown"),
                "target": target_schema.get("version", "unknown"),
            },
        }

    def generate_intelligent_mappings(
        self, legacy_fields: List[Dict], target_fields: List[Dict]
    ) -> List[Dict]:
        """Generate intelligent field mappings using multiple algorithms"""

        mappings = []
        target_field_lookup = self._create_target_field_lookup(target_fields)

        for legacy_field in legacy_fields:
            mapping = self._find_best_field_mapping(
                legacy_field, target_field_lookup, target_fields
            )
            mappings.append(mapping)

        return mappings

    def _create_target_field_lookup(self, target_fields: List[Dict]) -> Dict:
        """Create optimized lookup structures for target fields"""

        lookup = {"by_name": {}, "by_label": {}, "by_type": {}, "by_semantic": {}}

        for field in target_fields:
            fieldname = field.get("fieldname", "").lower()
            label = field.get("label", "").lower()
            fieldtype = field.get("fieldtype", "").lower()

            lookup["by_name"][fieldname] = field
            if label:
                lookup["by_label"][label] = field

            if fieldtype not in lookup["by_type"]:
                lookup["by_type"][fieldtype] = []
            lookup["by_type"][fieldtype].append(field)

            # Semantic categorization
            semantic_category = self._categorize_field_semantically(field)
            if semantic_category not in lookup["by_semantic"]:
                lookup["by_semantic"][semantic_category] = []
            lookup["by_semantic"][semantic_category].append(field)

        return lookup

    def _find_best_field_mapping(
        self, legacy_field: Dict, target_lookup: Dict, all_target_fields: List[Dict]
    ) -> Dict:
        """Find the best mapping for a legacy field using multi-algorithm approach"""

        legacy_name = legacy_field.get("name", "").lower()

        # Stage 1: Exact name matching
        exact_match = self._try_exact_name_match(legacy_name, target_lookup)
        if exact_match:
            return self._create_mapping_result(
                legacy_field, exact_match, 100, "Direct", "Exact name match"
            )

        # Stage 2: Fuzzy name matching
        fuzzy_match = self._try_fuzzy_name_matching(legacy_name, all_target_fields)
        if fuzzy_match["confidence"] >= 85:
            return self._create_mapping_result(
                legacy_field,
                fuzzy_match["field"],
                fuzzy_match["confidence"],
                "Direct",
                fuzzy_match["reason"],
            )

        # Stage 3: Semantic matching
        semantic_match = self._try_semantic_matching(legacy_field, target_lookup)
        if semantic_match["confidence"] >= 70:
            return self._create_mapping_result(
                legacy_field,
                semantic_match["field"],
                semantic_match["confidence"],
                "Transform",
                semantic_match["reason"],
            )

        # Stage 4: Type-based matching
        type_match = self._try_type_based_matching(legacy_field, target_lookup)
        if type_match["confidence"] >= 60:
            return self._create_mapping_result(
                legacy_field,
                type_match["field"],
                type_match["confidence"],
                "Transform",
                type_match["reason"],
            )

        # Stage 5: Custom field suggestion
        return self._suggest_custom_field_creation(legacy_field)

    def _try_exact_name_match(self, legacy_name: str, target_lookup: Dict) -> Optional[Dict]:
        """Try exact name matching"""
        return target_lookup["by_name"].get(legacy_name)

    def _try_fuzzy_name_matching(self, legacy_name: str, target_fields: List[Dict]) -> Dict:
        """Try fuzzy name matching with advanced similarity algorithms"""

        best_match = None
        best_confidence = 0
        best_reason = ""

        for target_field in target_fields:
            target_name = target_field.get("fieldname", "").lower()

            # Calculate multiple similarity metrics
            similarities = self._calculate_field_similarities(legacy_name, target_name)

            # Weighted average of similarity scores
            confidence = (
                similarities["sequence_ratio"] * 0.4
                + similarities["jaro_winkler"] * 0.3
                + similarities["token_similarity"] * 0.2
                + similarities["semantic_similarity"] * 0.1
            ) * 100

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = target_field
                best_reason = f"Fuzzy name match ({confidence:.1f}% similarity)"

        return {"field": best_match, "confidence": best_confidence, "reason": best_reason}

    def _calculate_field_similarities(self, legacy_name: str, target_name: str) -> Dict[str, float]:
        """Calculate multiple similarity metrics between field names"""

        cache_key = f"{legacy_name}:{target_name}"
        if cache_key in self.field_similarity_cache:
            return self.field_similarity_cache[cache_key]

        similarities = {
            "sequence_ratio": SequenceMatcher(None, legacy_name, target_name).ratio(),
            "jaro_winkler": self._jaro_winkler_similarity(legacy_name, target_name),
            "token_similarity": self._token_based_similarity(legacy_name, target_name),
            "semantic_similarity": self._semantic_similarity(legacy_name, target_name),
        }

        self.field_similarity_cache[cache_key] = similarities
        return similarities

    def _jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity (simplified implementation)"""
        if not s1 or not s2:
            return 0.0

        # Find common prefix length (up to 4 characters)
        prefix_len = 0
        for i in range(min(len(s1), len(s2), 4)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break

        # Simplified Jaro similarity
        jaro = SequenceMatcher(None, s1, s2).ratio()

        # Apply Winkler modification
        return jaro + (0.1 * prefix_len * (1 - jaro))

    def _token_based_similarity(self, s1: str, s2: str) -> float:
        """Calculate token-based similarity"""
        tokens1 = set(re.split(r"[_\s]+", s1.lower()))
        tokens2 = set(re.split(r"[_\s]+", s2.lower()))

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union) if union else 0.0

    def _semantic_similarity(self, s1: str, s2: str) -> float:
        """Calculate semantic similarity using field name patterns"""

        semantic_groups = {
            "identifiers": ["id", "key", "code", "number", "ref"],
            "names": ["name", "title", "label", "caption"],
            "descriptions": ["desc", "description", "note", "comment"],
            "dates": ["date", "time", "created", "modified", "updated"],
            "contact": ["email", "phone", "mobile", "fax"],
            "location": ["address", "city", "country", "postal", "zip"],
            "financial": ["price", "cost", "amount", "total", "currency"],
            "status": ["status", "state", "active", "enabled", "disabled"],
        }

        def get_semantic_category(field_name):
            for category, keywords in semantic_groups.items():
                if any(keyword in field_name.lower() for keyword in keywords):
                    return category
            return "other"

        cat1 = get_semantic_category(s1)
        cat2 = get_semantic_category(s2)

        return 1.0 if cat1 == cat2 and cat1 != "other" else 0.0

    def _try_semantic_matching(self, legacy_field: Dict, target_lookup: Dict) -> Dict:
        """Try semantic field matching based on field purpose"""

        legacy_category = self._categorize_field_semantically(legacy_field)

        if legacy_category in target_lookup["by_semantic"]:
            candidate_fields = target_lookup["by_semantic"][legacy_category]

            # Find best match within semantic category
            best_match = None
            best_confidence = 0

            for candidate in candidate_fields:
                # Additional matching criteria within category
                confidence = self._calculate_semantic_confidence(legacy_field, candidate)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = candidate

            return {
                "field": best_match,
                "confidence": best_confidence,
                "reason": f"Semantic category match: {legacy_category}",
            }

        return {"field": None, "confidence": 0, "reason": "No semantic match found"}

    def _categorize_field_semantically(self, field: Dict) -> str:
        """Categorize field based on its semantic purpose"""

        field_name = field.get("name", "").lower()
        field_type = field.get("type", "").lower()

        # Primary key detection
        if field.get("primary_key") or "id" in field_name:
            return "identifier"

        # Name/title fields
        if any(keyword in field_name for keyword in ["name", "title", "label"]):
            return "name"

        # Contact information
        if any(keyword in field_name for keyword in ["email", "phone", "mobile", "fax"]):
            return "contact"

        # Address fields
        if any(keyword in field_name for keyword in ["address", "city", "country", "postal"]):
            return "location"

        # Date/time fields
        if "date" in field_type or any(
            keyword in field_name for keyword in ["date", "time", "created", "modified"]
        ):
            return "temporal"

        # Financial fields
        if any(keyword in field_name for keyword in ["price", "cost", "amount", "total"]):
            return "financial"

        # Status/boolean fields
        if "bool" in field_type or any(
            keyword in field_name for keyword in ["status", "active", "enabled"]
        ):
            return "status"

        # Description fields
        if "text" in field_type or any(
            keyword in field_name for keyword in ["desc", "note", "comment"]
        ):
            return "description"

        return "general"

    def _calculate_semantic_confidence(self, legacy_field: Dict, target_field: Dict) -> float:
        """Calculate confidence for semantic field matching"""

        confidence = 70  # Base confidence for semantic category match

        # Boost confidence for type compatibility
        legacy_type = self._normalize_field_type(legacy_field.get("type", ""))
        target_type = self._normalize_field_type(target_field.get("fieldtype", ""))

        if legacy_type == target_type:
            confidence += 20
        elif self._are_types_compatible(legacy_type, target_type):
            confidence += 10

        # Boost confidence for size compatibility
        if self._are_sizes_compatible(legacy_field, target_field):
            confidence += 5

        # Reduce confidence for required field mismatches
        if legacy_field.get("nullable", True) != (not target_field.get("reqd", False)):
            confidence -= 10

        return min(confidence, 100)

    def _try_type_based_matching(self, legacy_field: Dict, target_lookup: Dict) -> Dict:
        """Try type-based field matching"""

        legacy_type = self._normalize_field_type(legacy_field.get("type", ""))

        if legacy_type in target_lookup["by_type"]:
            candidate_fields = target_lookup["by_type"][legacy_type]

            # Simple heuristic: pick first available field of same type
            if candidate_fields:
                return {
                    "field": candidate_fields[0],
                    "confidence": 60,
                    "reason": f"Type-based match: {legacy_type}",
                }

        return {"field": None, "confidence": 0, "reason": "No type match found"}

    def _normalize_field_type(self, field_type: str) -> str:
        """Normalize field type for comparison"""

        type_mapping = {
            "varchar": "data",
            "char": "data",
            "text": "text",
            "longtext": "long_text",
            "int": "int",
            "integer": "int",
            "bigint": "int",
            "decimal": "float",
            "float": "float",
            "double": "float",
            "date": "date",
            "datetime": "datetime",
            "timestamp": "datetime",
            "time": "time",
            "boolean": "check",
            "bool": "check",
        }

        # Remove size specifications and normalize
        normalized = re.sub(r"\([^)]*\)", "", str(field_type)).lower().strip()
        return type_mapping.get(normalized, normalized)

    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two field types are compatible"""

        compatibility_groups = [
            {"data", "text", "long_text"},
            {"int", "float"},
            {"date", "datetime"},
            {"check", "boolean"},
        ]

        for group in compatibility_groups:
            if type1 in group and type2 in group:
                return True

        return False

    def _are_sizes_compatible(self, legacy_field: Dict, target_field: Dict) -> bool:
        """Check if field sizes are compatible"""

        legacy_size = self._extract_field_size(legacy_field.get("type", ""))
        target_size = self._extract_field_size(target_field.get("options", ""))

        if not legacy_size or not target_size:
            return True  # Can't determine, assume compatible

        try:
            legacy_num = int(legacy_size.split(",")[0])
            target_num = int(target_size.split(",")[0])
            return target_num >= legacy_num
        except (ValueError, IndexError):
            return True

    def _extract_field_size(self, type_definition: str) -> Optional[str]:
        """Extract size specification from field type"""
        match = re.search(r"\(([^)]+)\)", str(type_definition))
        return match.group(1) if match else None

    def _suggest_custom_field_creation(self, legacy_field: Dict) -> Dict:
        """Suggest creating a custom field for unmappable legacy field"""

        suggested_fieldname = self._generate_custom_fieldname(legacy_field["name"])
        suggested_fieldtype = self._map_legacy_type_to_erpnext(legacy_field.get("type", ""))

        return self._create_mapping_result(
            legacy_field,
            {
                "fieldname": suggested_fieldname,
                "label": legacy_field["name"].replace("_", " ").title(),
                "fieldtype": suggested_fieldtype,
            },
            50,
            "Custom Field",
            "No suitable existing field found - custom field creation required",
        )

    def _generate_custom_fieldname(self, legacy_name: str) -> str:
        """Generate ERPNext-compatible custom fieldname"""

        # Clean and normalize the name
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", legacy_name.lower())
        clean_name = re.sub(r"_+", "_", clean_name)
        clean_name = clean_name.strip("_")

        # Ensure it doesn't start with a number
        if clean_name[0].isdigit():
            clean_name = f"field_{clean_name}"

        # Add custom prefix
        return f"custom_{clean_name}"

    def _map_legacy_type_to_erpnext(self, legacy_type: str) -> str:
        """Map legacy field type to ERPNext field type"""

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

        base_type = re.sub(r"\([^)]*\)", "", str(legacy_type)).upper().strip()
        return type_mapping.get(base_type, "Data")

    def _create_mapping_result(
        self,
        legacy_field: Dict,
        target_field: Dict,
        confidence: float,
        mapping_type: str,
        reason: str,
    ) -> Dict:
        """Create standardized mapping result"""

        return {
            "legacy_field_name": legacy_field.get("name"),
            "legacy_field_type": legacy_field.get("type"),
            "legacy_field_size": self._extract_field_size(legacy_field.get("type", "")),
            "target_field_name": target_field.get("fieldname"),
            "target_field_type": target_field.get("fieldtype"),
            "mapping_type": mapping_type,
            "mapping_confidence": confidence,
            "mapping_reason": reason,
            "is_required": not legacy_field.get("nullable", True),
            "is_unique": legacy_field.get("primary_key", False),
            "transformation_needed": self._needs_transformation(legacy_field, target_field),
            "transformation_type": self._get_transformation_type(legacy_field, target_field),
            "suggested_custom_field": mapping_type == "Custom Field",
        }

    def _needs_transformation(self, legacy_field: Dict, target_field: Dict) -> bool:
        """Determine if field mapping requires data transformation"""

        legacy_type = self._normalize_field_type(legacy_field.get("type", ""))
        target_type = self._normalize_field_type(target_field.get("fieldtype", ""))

        return legacy_type != target_type

    def _get_transformation_type(self, legacy_field: Dict, target_field: Dict) -> Optional[str]:
        """Determine the type of transformation needed"""

        if not self._needs_transformation(legacy_field, target_field):
            return None

        legacy_type = self._normalize_field_type(legacy_field.get("type", ""))
        target_type = self._normalize_field_type(target_field.get("fieldtype", ""))

        transformations = {
            ("data", "date"): "Date Format",
            ("data", "datetime"): "Date Format",
            ("data", "float"): "Currency Format",
            ("text", "data"): "Text Case",
            ("int", "float"): "Type Conversion",
            ("data", "int"): "Type Conversion",
        }

        return transformations.get((legacy_type, target_type), "Custom Function")

    def calculate_compatibility_metrics(
        self, mappings: List[Dict], legacy_fields: List[Dict], target_fields: List[Dict]
    ) -> Dict:
        """Calculate comprehensive compatibility metrics"""

        total_fields = len(legacy_fields)
        if total_fields == 0:
            return {"error": "No legacy fields to analyze"}

        # Count mapping types
        mapping_counts = {
            "direct": len([m for m in mappings if m["mapping_type"] == "Direct"]),
            "transform": len([m for m in mappings if m["mapping_type"] == "Transform"]),
            "custom": len([m for m in mappings if m["mapping_type"] == "Custom Field"]),
            "skip": len([m for m in mappings if m["mapping_type"] == "Skip"]),
        }

        # Calculate scores
        compatibility_score = (mapping_counts["direct"] / total_fields) * 100
        transformation_complexity = (mapping_counts["transform"] / total_fields) * 100
        custom_fields_ratio = (mapping_counts["custom"] / total_fields) * 100

        # Calculate average confidence
        confidences = [m.get("mapping_confidence", 0) for m in mappings]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Determine overall readiness
        readiness = self._determine_migration_readiness(
            compatibility_score, transformation_complexity, custom_fields_ratio, average_confidence
        )

        return {
            "total_legacy_fields": total_fields,
            "total_target_fields": len(target_fields),
            "mapping_counts": mapping_counts,
            "compatibility_score": round(compatibility_score, 2),
            "transformation_complexity": round(transformation_complexity, 2),
            "custom_fields_ratio": round(custom_fields_ratio, 2),
            "average_confidence": round(average_confidence, 2),
            "migration_readiness": readiness,
            "estimated_effort": self._estimate_migration_effort(mappings),
        }

    def _determine_migration_readiness(
        self, compatibility: float, complexity: float, custom_ratio: float, confidence: float
    ) -> str:
        """Determine overall migration readiness"""

        if compatibility >= 80 and complexity <= 10 and custom_ratio <= 5:
            return "Ready"
        elif compatibility >= 60 and complexity <= 30 and custom_ratio <= 20:
            return "Good"
        elif compatibility >= 40 and complexity <= 50 and custom_ratio <= 40:
            return "Moderate"
        elif compatibility >= 20:
            return "Complex"
        else:
            return "High Risk"

    def _estimate_migration_effort(self, mappings: List[Dict]) -> Dict:
        """Estimate migration effort based on mapping complexity"""

        effort_weights = {"Direct": 1, "Transform": 3, "Custom Field": 5, "Skip": 0}

        total_effort = sum(effort_weights.get(m["mapping_type"], 0) for m in mappings)

        # Estimate in person-hours
        base_hours = total_effort * 0.5  # 30 minutes per effort point

        effort_category = "Low"
        if total_effort > 50:
            effort_category = "High"
        elif total_effort > 20:
            effort_category = "Medium"

        return {
            "effort_points": total_effort,
            "estimated_hours": round(base_hours, 1),
            "effort_category": effort_category,
            "confidence_level": "Medium",  # This would be more sophisticated in reality
        }

    def generate_migration_recommendations(self, metrics: Dict, mappings: List[Dict]) -> List[Dict]:
        """Generate actionable migration recommendations"""

        recommendations = []

        # Compatibility recommendations
        if metrics["compatibility_score"] < 50:
            recommendations.append(
                {
                    "type": "Warning",
                    "category": "Compatibility",
                    "title": "Low Compatibility Score",
                    "description": f"Only {metrics['compatibility_score']:.1f}% of fields have direct mappings",
                    "action": "Review field mappings and consider schema modifications",
                    "priority": "High",
                }
            )

        # Custom field recommendations
        if metrics["custom_fields_ratio"] > 30:
            recommendations.append(
                {
                    "type": "Action",
                    "category": "Custom Fields",
                    "title": "Many Custom Fields Required",
                    "description": f"{metrics['custom_fields_ratio']:.1f}% of fields need custom field creation",
                    "action": "Plan custom field creation and consider impact on performance",
                    "priority": "Medium",
                }
            )

        # Transformation recommendations
        high_complexity_mappings = [m for m in mappings if m.get("mapping_confidence", 0) < 60]
        if len(high_complexity_mappings) > len(mappings) * 0.3:
            recommendations.append(
                {
                    "type": "Review",
                    "category": "Data Quality",
                    "title": "Low Confidence Mappings",
                    "description": f"{len(high_complexity_mappings)} fields have low mapping confidence",
                    "action": "Manual review and validation of field mappings required",
                    "priority": "High",
                }
            )

        # Performance recommendations
        if metrics["total_legacy_fields"] > 100:
            recommendations.append(
                {
                    "type": "Performance",
                    "category": "Scale",
                    "title": "Large Schema Migration",
                    "description": f"Migration involves {metrics['total_legacy_fields']} fields",
                    "action": "Consider batch processing and performance optimization",
                    "priority": "Medium",
                }
            )

        return recommendations


# Global instance for use across the application
schema_alignment_engine = SchemaAlignmentEngine()


@frappe.whitelist()
def analyze_schema_alignment(legacy_schema_data, target_doctype):
    """API endpoint for schema alignment analysis"""

    try:
        # Parse legacy schema data
        if isinstance(legacy_schema_data, str):
            legacy_schema = json.loads(legacy_schema_data)
        else:
            legacy_schema = legacy_schema_data

        # Get target schema
        target_meta = frappe.get_meta(target_doctype)
        target_schema = {
            "fields": [
                {
                    "fieldname": field.fieldname,
                    "label": field.label,
                    "fieldtype": field.fieldtype,
                    "reqd": field.reqd,
                    "unique": field.unique,
                    "options": field.options,
                }
                for field in target_meta.fields
                if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "Heading"]
            ]
        }

        # Perform analysis
        analysis_result = schema_alignment_engine.analyze_schema_compatibility(
            legacy_schema, target_schema
        )

        return {"status": "success", "analysis": analysis_result}

    except Exception as e:
        frappe.log_error(f"Schema alignment analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def generate_transformation_rules(mapping_id):
    """Generate transformation rules for a schema mapping"""

    try:
        mapping_doc = frappe.get_doc("Legacy Schema Mapping", mapping_id)

        transformation_rules = []

        for field_mapping in mapping_doc.field_mappings:
            if field_mapping.transformation_needed:
                rule = {
                    "rule_name": f"Transform {field_mapping.legacy_field_name}",
                    "rule_type": field_mapping.transformation_type or "Custom Function",
                    "source_field": field_mapping.legacy_field_name,
                    "target_field": field_mapping.target_field_name,
                    "transformation_function": _get_transformation_function(field_mapping),
                    "function_parameters": _get_transformation_parameters(field_mapping),
                    "example_input": _generate_example_input(field_mapping),
                    "example_output": _generate_example_output(field_mapping),
                }
                transformation_rules.append(rule)

        # Clear existing transformation rules
        mapping_doc.transformation_rules = []

        # Add generated rules
        for rule in transformation_rules:
            mapping_doc.append("transformation_rules", rule)

        mapping_doc.save()

        return {"status": "success", "rules_generated": len(transformation_rules)}

    except Exception as e:
        frappe.log_error(f"Transformation rule generation failed: {str(e)}")
        return {"status": "error", "message": str(e)}


def _get_transformation_function(field_mapping):
    """Determine transformation function based on field mapping"""

    transformation_type = field_mapping.transformation_type

    function_mapping = {
        "Date Format": "convert_date_format",
        "Currency Format": "format_currency",
        "Text Case": "title_case",
        "Type Conversion": "convert_type",
        "Custom Function": "custom_transform",
    }

    return function_mapping.get(transformation_type, "custom_transform")


def _get_transformation_parameters(field_mapping):
    """Generate transformation parameters as JSON"""

    transformation_type = field_mapping.transformation_type

    if transformation_type == "Date Format":
        return json.dumps(
            {
                "source_format": "auto_detect",
                "target_format": "%Y-%m-%d",
                "handle_errors": "set_null",
            }
        )
    elif transformation_type == "Currency Format":
        return json.dumps(
            {"source_currency": "auto_detect", "target_currency": "OMR", "decimal_places": 3}
        )
    elif transformation_type == "Text Case":
        return json.dumps({"case_type": "title", "preserve_acronyms": True})
    else:
        return json.dumps({"custom_logic": "to_be_implemented"})


def _generate_example_input(field_mapping):
    """Generate example input for transformation"""

    field_type = field_mapping.legacy_field_type

    examples = {
        "VARCHAR": "Sample Text",
        "INT": "12345",
        "DATE": "2024-12-30",
        "DATETIME": "2024-12-30 10:30:00",
    }

    base_type = re.sub(r"\([^)]*\)", "", str(field_type)).upper()
    return examples.get(base_type, "sample_value")


def _generate_example_output(field_mapping):
    """Generate example output for transformation"""

    target_type = field_mapping.target_field_type

    examples = {
        "Data": "Sample Text",
        "Int": 12345,
        "Date": "2024-12-30",
        "Datetime": "2024-12-30 10:30:00",
    }

    return examples.get(target_type, "transformed_value")
