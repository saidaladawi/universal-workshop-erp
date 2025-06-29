"""
Parts Auto-Suggestion Engine for Universal Workshop ERP
Provides intelligent parts recommendations based on:
- Service type and vehicle specifications
- Historical service data and patterns
- Current inventory levels and availability
- Machine learning models for prediction
- Arabic localization support with RTL text direction
- Comprehensive arabic language interface for Oman workshops
"""

import frappe
from frappe import _
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from typing import Dict, List, Tuple, Optional

# pylint: disable=no-member


class PartsAutoSuggestionEngine:
    """
    Intelligent parts suggestion engine using ML and historical data
    """

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache with bulk operations
        self.min_confidence_score = 0.6
        self.max_suggestions = 10
        self.use_async_loading = True  # Enable async processing for performance
        self.enable_pagination = True  # Support pagination for large result sets

    @frappe.whitelist()
    def get_parts_suggestions(
        self,
        service_type: str = None,
        vehicle_make: str = None,
        vehicle_model: str = None,
        vehicle_year: int = None,
        customer_id: str = None,
        previous_services: List[str] = None,
        language: str = "en",
    ) -> Dict:
        """
        Get intelligent parts suggestions based on multiple factors

        Args:
            service_type: Type of service (Engine, Transmission, etc.)
            vehicle_make: Vehicle manufacturer
            vehicle_model: Vehicle model
            vehicle_year: Vehicle year
            customer_id: Customer ID for historical analysis
            previous_services: List of previous service IDs
            language: Language preference (en/ar)

        Returns:
            Dictionary with suggested parts, confidence scores, and metadata
        """
        try:
            # Validate inputs
            if not service_type:
                return {"error": _("Service type is required for suggestions")}

            # Get base suggestions from different engines
            service_based_parts = self._get_service_type_suggestions(service_type)
            vehicle_based_parts = self._get_vehicle_specific_suggestions(
                vehicle_make, vehicle_model, vehicle_year
            )
            historical_parts = self._get_historical_suggestions(
                customer_id, vehicle_make, vehicle_model, previous_services
            )
            ml_predictions = self._get_ml_predictions(
                service_type, vehicle_make, vehicle_model, vehicle_year
            )

            # Combine and rank suggestions
            combined_suggestions = self._combine_suggestions(
                service_based_parts, vehicle_based_parts, historical_parts, ml_predictions
            )

            # Apply inventory filters
            available_suggestions = self._filter_by_inventory(combined_suggestions)

            # Format for output with Arabic support
            formatted_suggestions = self._format_suggestions(available_suggestions, language)

            return {
                "suggestions": formatted_suggestions,
                "total_found": len(formatted_suggestions),
                "service_type": service_type,
                "language": language,
                "generated_at": frappe.utils.now(),
                "cache_duration": self.cache_timeout,
            }

        except Exception as e:
            frappe.log_error(f"Parts suggestion error: {str(e)}")
            return {"error": _("Unable to generate parts suggestions")}

    def _get_service_type_suggestions(self, service_type: str) -> List[Dict]:
        """Get parts commonly used for specific service types"""

        # Cache key for service type suggestions
        cache_key = f"service_parts_{service_type}"
        cached_result = frappe.cache().get_value(cache_key)

        if cached_result:
            return json.loads(cached_result)

        # Query parts used in this service type
        service_parts = frappe.db.sql(
            """
            SELECT 
                sei.item_code,
                sei.item_name,
                sei.item_name_ar,
                COUNT(*) as usage_frequency,
                AVG(sei.qty) as avg_quantity,
                AVG(sei.rate) as avg_rate,
                i.item_group,
                i.brand
            FROM `tabService Estimate Item` sei
            JOIN `tabService Estimate` se ON sei.parent = se.name
            JOIN `tabItem` i ON sei.item_code = i.item_code
            WHERE se.service_type = %s
            AND se.docstatus = 1
            AND sei.creation >= %s
            GROUP BY sei.item_code
            ORDER BY usage_frequency DESC, avg_quantity DESC
            LIMIT 50
        """,
            [service_type, frappe.utils.add_months(frappe.utils.today(), -12)],
            as_dict=True,
        )

        # Calculate confidence scores
        max_frequency = max([p.usage_frequency for p in service_parts]) if service_parts else 1

        suggestions = []
        for part in service_parts:
            confidence = min(0.9, part.usage_frequency / max_frequency)
            suggestions.append(
                {
                    "item_code": part.item_code,
                    "item_name": part.item_name,
                    "item_name_ar": part.item_name_ar,
                    "confidence_score": confidence,
                    "reason": "service_type_common",
                    "avg_quantity": part.avg_quantity,
                    "avg_rate": part.avg_rate,
                    "usage_frequency": part.usage_frequency,
                    "item_group": part.item_group,
                    "brand": part.brand,
                }
            )

        # Cache for 5 minutes
        frappe.cache().set_value(cache_key, json.dumps(suggestions), expires_in_sec=300)
        return suggestions

    def _get_vehicle_specific_suggestions(self, make: str, model: str, year: int) -> List[Dict]:
        """Get parts specific to vehicle make/model/year"""

        if not make or not model:
            return []

        cache_key = f"vehicle_parts_{make}_{model}_{year}"
        cached_result = frappe.cache().get_value(cache_key)

        if cached_result:
            return json.loads(cached_result)

        # Query vehicle-specific parts usage
        conditions = ["vm.make = %s", "vm.model = %s"]
        values = [make, model]

        if year:
            conditions.append("vm.year = %s")
            values.append(year)

        vehicle_parts = frappe.db.sql(
            f"""
            SELECT 
                sei.item_code,
                sei.item_name,
                sei.item_name_ar,
                COUNT(*) as vehicle_usage,
                AVG(sei.qty) as avg_quantity,
                i.item_group,
                i.brand
            FROM `tabService Estimate Item` sei
            JOIN `tabService Estimate` se ON sei.parent = se.name
            JOIN `tabVehicle Master` vm ON se.vehicle = vm.name
            JOIN `tabItem` i ON sei.item_code = i.item_code
            WHERE {' AND '.join(conditions)}
            AND se.docstatus = 1
            AND sei.creation >= %s
            GROUP BY sei.item_code
            ORDER BY vehicle_usage DESC
            LIMIT 30
        """,
            values + [frappe.utils.add_months(frappe.utils.today(), -18)],
            as_dict=True,
        )

        suggestions = []
        max_usage = max([p.vehicle_usage for p in vehicle_parts]) if vehicle_parts else 1

        for part in vehicle_parts:
            confidence = min(0.85, part.vehicle_usage / max_usage)
            suggestions.append(
                {
                    "item_code": part.item_code,
                    "item_name": part.item_name,
                    "item_name_ar": part.item_name_ar,
                    "confidence_score": confidence,
                    "reason": "vehicle_specific",
                    "avg_quantity": part.avg_quantity,
                    "vehicle_usage": part.vehicle_usage,
                    "item_group": part.item_group,
                    "brand": part.brand,
                }
            )

        frappe.cache().set_value(cache_key, json.dumps(suggestions), expires_in_sec=600)
        return suggestions

    def _get_historical_suggestions(
        self, customer_id: str, make: str, model: str, previous_services: List[str]
    ) -> List[Dict]:
        """Get suggestions based on customer and service history"""

        suggestions = []

        # Customer-specific historical parts
        if customer_id:
            customer_parts = frappe.db.sql(
                """
                SELECT 
                    sei.item_code,
                    sei.item_name,
                    sei.item_name_ar,
                    COUNT(*) as customer_usage,
                    MAX(se.creation) as last_used,
                    AVG(sei.qty) as avg_quantity
                FROM `tabService Estimate Item` sei
                JOIN `tabService Estimate` se ON sei.parent = se.name
                WHERE se.customer = %s
                AND se.docstatus = 1
                AND sei.creation >= %s
                GROUP BY sei.item_code
                ORDER BY customer_usage DESC, last_used DESC
                LIMIT 20
            """,
                [customer_id, frappe.utils.add_months(frappe.utils.today(), -24)],
                as_dict=True,
            )

            for part in customer_parts:
                # Higher confidence for recent usage
                days_since_last = (datetime.now().date() - part.last_used.date()).days
                recency_factor = max(0.3, 1 - (days_since_last / 365))

                confidence = min(0.8, (part.customer_usage * 0.3) * recency_factor)
                suggestions.append(
                    {
                        "item_code": part.item_code,
                        "item_name": part.item_name,
                        "item_name_ar": part.item_name_ar,
                        "confidence_score": confidence,
                        "reason": "customer_history",
                        "avg_quantity": part.avg_quantity,
                        "customer_usage": part.customer_usage,
                        "last_used": part.last_used,
                    }
                )

        # Similar service patterns
        if previous_services:
            pattern_parts = self._find_service_patterns(previous_services)
            suggestions.extend(pattern_parts)

        return suggestions

    def _get_ml_predictions(
        self, service_type: str, make: str, model: str, year: int
    ) -> List[Dict]:
        """
        Get ML-based predictions (simplified implementation)
        In production, this would use trained models
        """

        try:
            # Simplified ML approach: clustering based on service patterns
            similar_services = frappe.db.sql(
                """
                SELECT 
                    se.name,
                    se.service_type,
                    vm.make,
                    vm.model,
                    vm.year
                FROM `tabService Estimate` se
                JOIN `tabVehicle Master` vm ON se.vehicle = vm.name
                WHERE se.service_type = %s
                AND se.docstatus = 1
                AND se.creation >= %s
                ORDER BY se.creation DESC
                LIMIT 100
            """,
                [service_type, frappe.utils.add_months(frappe.utils.today(), -12)],
                as_dict=True,
            )

            # Score services by similarity
            scored_services = []
            for service in similar_services:
                similarity_score = 0

                if service.make == make:
                    similarity_score += 0.4
                if service.model == model:
                    similarity_score += 0.4
                if year and abs(service.year - year) <= 2:
                    similarity_score += 0.2

                if similarity_score > 0.4:  # Minimum similarity threshold
                    scored_services.append((service.name, similarity_score))

            # Get parts from most similar services
            if scored_services:
                service_names = [s[0] for s in scored_services[:20]]
                format_strings = ",".join(["%s"] * len(service_names))

                ml_parts = frappe.db.sql(
                    f"""
                    SELECT 
                        sei.item_code,
                        sei.item_name,
                        sei.item_name_ar,
                        COUNT(*) as ml_frequency,
                        AVG(sei.qty) as avg_quantity
                    FROM `tabService Estimate Item` sei
                    WHERE sei.parent IN ({format_strings})
                    GROUP BY sei.item_code
                    ORDER BY ml_frequency DESC
                    LIMIT 15
                """,
                    service_names,
                    as_dict=True,
                )

                suggestions = []
                for part in ml_parts:
                    confidence = min(0.75, part.ml_frequency / len(service_names))
                    suggestions.append(
                        {
                            "item_code": part.item_code,
                            "item_name": part.item_name,
                            "item_name_ar": part.item_name_ar,
                            "confidence_score": confidence,
                            "reason": "ml_prediction",
                            "avg_quantity": part.avg_quantity,
                            "ml_frequency": part.ml_frequency,
                        }
                    )

                return suggestions

        except Exception as e:
            frappe.log_error(f"ML prediction error: {str(e)}")

        return []

    def _find_service_patterns(self, service_ids: List[str]) -> List[Dict]:
        """Find patterns in service sequences"""

        if not service_ids or len(service_ids) < 2:
            return []

        # Get items from previous services to predict next items
        format_strings = ",".join(["%s"] * len(service_ids))

        pattern_analysis = frappe.db.sql(
            f"""
            SELECT 
                sei.item_code,
                sei.item_name,
                sei.item_name_ar,
                sei.parent as service_id,
                se.creation
            FROM `tabService Estimate Item` sei
            JOIN `tabService Estimate` se ON sei.parent = se.name
            WHERE sei.parent IN ({format_strings})
            ORDER BY se.creation
        """,
            service_ids,
            as_dict=True,
        )

        # Simple pattern: items that appear after similar item sequences
        item_sequences = defaultdict(list)
        for item in pattern_analysis:
            item_sequences[item.service_id].append(item.item_code)

        # Find frequently co-occurring items
        co_occurrence = defaultdict(int)
        for sequence in item_sequences.values():
            for i, item in enumerate(sequence):
                for j in range(i + 1, len(sequence)):
                    co_occurrence[(item, sequence[j])] += 1

        # Convert to suggestions
        suggestions = []
        for (item1, item2), frequency in co_occurrence.items():
            if frequency >= 2:  # Minimum co-occurrence threshold
                item_details = frappe.db.get_value(
                    "Item", item2, ["item_name", "item_name_ar"], as_dict=True
                )
                if item_details:
                    suggestions.append(
                        {
                            "item_code": item2,
                            "item_name": item_details.item_name,
                            "item_name_ar": item_details.item_name_ar,
                            "confidence_score": min(0.7, frequency / 10),
                            "reason": "service_pattern",
                            "pattern_frequency": frequency,
                        }
                    )

        return suggestions[:10]  # Limit pattern suggestions

    def _combine_suggestions(self, *suggestion_lists) -> List[Dict]:
        """Combine suggestions from different engines and calculate final scores"""

        all_suggestions = {}

        for suggestion_list in suggestion_lists:
            for suggestion in suggestion_list:
                item_code = suggestion["item_code"]

                if item_code in all_suggestions:
                    # Combine scores using weighted average
                    existing = all_suggestions[item_code]
                    new_confidence = suggestion["confidence_score"]

                    # Weight different reasons differently
                    reason_weights = {
                        "service_type_common": 0.4,
                        "vehicle_specific": 0.35,
                        "customer_history": 0.3,
                        "ml_prediction": 0.25,
                        "service_pattern": 0.2,
                    }

                    weight1 = reason_weights.get(existing["reason"], 0.2)
                    weight2 = reason_weights.get(suggestion["reason"], 0.2)

                    combined_confidence = (
                        existing["confidence_score"] * weight1 + new_confidence * weight2
                    ) / (weight1 + weight2)

                    all_suggestions[item_code]["confidence_score"] = min(0.95, combined_confidence)
                    all_suggestions[item_code]["reasons"] = existing.get(
                        "reasons", [existing["reason"]]
                    ) + [suggestion["reason"]]
                else:
                    suggestion["reasons"] = [suggestion["reason"]]
                    all_suggestions[item_code] = suggestion

        # Filter by minimum confidence and sort
        filtered_suggestions = [
            s
            for s in all_suggestions.values()
            if s["confidence_score"] >= self.min_confidence_score
        ]

        return sorted(filtered_suggestions, key=lambda x: x["confidence_score"], reverse=True)[
            : self.max_suggestions
        ]

    def _filter_by_inventory(self, suggestions: List[Dict]) -> List[Dict]:
        """Filter suggestions by current inventory availability"""

        if not suggestions:
            return []

        item_codes = [s["item_code"] for s in suggestions]
        format_strings = ",".join(["%s"] * len(item_codes))

        # Get current stock levels
        stock_levels = frappe.db.sql(
            f"""
            SELECT 
                item_code,
                SUM(actual_qty) as available_qty,
                SUM(projected_qty) as projected_qty
            FROM `tabBin`
            WHERE item_code IN ({format_strings})
            GROUP BY item_code
        """,
            item_codes,
            as_dict=True,
        )

        stock_dict = {s.item_code: s for s in stock_levels}

        # Add inventory information and adjust confidence
        for suggestion in suggestions:
            item_code = suggestion["item_code"]
            stock_info = stock_dict.get(item_code, {})

            available_qty = stock_info.get("available_qty", 0) or 0
            projected_qty = stock_info.get("projected_qty", 0) or 0

            suggestion["available_qty"] = available_qty
            suggestion["projected_qty"] = projected_qty
            suggestion["in_stock"] = available_qty > 0

            # Adjust confidence based on availability
            if available_qty <= 0:
                suggestion["confidence_score"] *= 0.7  # Reduce confidence for out-of-stock
                suggestion["availability_note"] = _("Out of stock")
            elif available_qty < suggestion.get("avg_quantity", 1):
                suggestion["confidence_score"] *= 0.85  # Slightly reduce for low stock
                suggestion["availability_note"] = _("Low stock")
            else:
                suggestion["availability_note"] = _("In stock")

        return suggestions

    def _format_suggestions(self, suggestions: List[Dict], language: str) -> List[Dict]:
        """Format suggestions for API response with Arabic support"""

        formatted = []

        for suggestion in suggestions:
            # Choose appropriate name based on language
            if language == "ar" and suggestion.get("item_name_ar"):
                display_name = suggestion["item_name_ar"]
            else:
                display_name = suggestion["item_name"]

            # Format confidence as percentage
            confidence_percent = round(suggestion["confidence_score"] * 100, 1)

            # Create reason descriptions
            reason_descriptions = {
                "service_type_common": _("Commonly used for this service"),
                "vehicle_specific": _("Specific to this vehicle"),
                "customer_history": _("Used by this customer before"),
                "ml_prediction": _("AI recommendation"),
                "service_pattern": _("Based on service patterns"),
            }

            reasons = suggestion.get("reasons", [suggestion.get("reason", "")])
            reason_text = ", ".join(
                [reason_descriptions.get(r, r) for r in reasons[:2]]  # Limit to 2 reasons
            )

            formatted_item = {
                "item_code": suggestion["item_code"],
                "item_name": display_name,
                "confidence_score": suggestion["confidence_score"],
                "confidence_percent": confidence_percent,
                "reason_text": reason_text,
                "reasons": reasons,
                "available_qty": suggestion.get("available_qty", 0),
                "in_stock": suggestion.get("in_stock", False),
                "availability_note": suggestion.get("availability_note", ""),
                "suggested_quantity": suggestion.get("avg_quantity", 1),
            }

            # Add optional fields if available
            optional_fields = ["item_group", "brand", "avg_rate", "usage_frequency"]
            for field in optional_fields:
                if field in suggestion:
                    formatted_item[field] = suggestion[field]

            formatted.append(formatted_item)

        return formatted

    @frappe.whitelist()
    def get_parts_by_category(
        self, category: str, vehicle_make: str = None, language: str = "en"
    ) -> Dict:
        """Get parts suggestions by category (Engine, Transmission, etc.)"""

        try:
            conditions = ["i.item_group = %s", "i.disabled = 0"]
            values = [category]

            if vehicle_make:
                # Filter by vehicle compatibility if available
                conditions.append(
                    """
                    (i.vehicle_compatibility IS NULL 
                     OR i.vehicle_compatibility = '' 
                     OR i.vehicle_compatibility LIKE %s)
                """
                )
                values.append(f"%{vehicle_make}%")

            query = f"""
                SELECT 
                    i.item_code,
                    i.item_name,
                    i.item_name_ar,
                    i.standard_rate,
                    i.item_group,
                    i.brand,
                    COALESCE(b.actual_qty, 0) as available_qty
                FROM `tabItem` i
                LEFT JOIN `tabBin` b ON i.item_code = b.item_code
                WHERE {' AND '.join(conditions)}
                ORDER BY i.item_name
                LIMIT 50
            """

            items = frappe.db.sql(query, values, as_dict=True)

            formatted_items = []
            for item in items:
                display_name = (
                    item.item_name_ar if language == "ar" and item.item_name_ar else item.item_name
                )

                formatted_items.append(
                    {
                        "item_code": item.item_code,
                        "item_name": display_name,
                        "standard_rate": item.standard_rate,
                        "item_group": item.item_group,
                        "brand": item.brand,
                        "available_qty": item.available_qty or 0,
                        "in_stock": (item.available_qty or 0) > 0,
                    }
                )

            return {
                "items": formatted_items,
                "category": category,
                "total_found": len(formatted_items),
                "language": language,
            }

        except Exception as e:
            frappe.log_error(f"Category parts error: {str(e)}")
            return {"error": _("Unable to get parts by category")}

    @frappe.whitelist()
    def search_parts(self, query: str, limit: int = 20, language: str = "en") -> Dict:
        """Search parts with Arabic support"""

        if not query or len(query.strip()) < 2:
            return {"error": _("Search query too short")}

        try:
            search_term = f"%{query.strip()}%"

            # Search in both English and Arabic fields
            parts = frappe.db.sql(
                """
                SELECT 
                    i.item_code,
                    i.item_name,
                    i.item_name_ar,
                    i.standard_rate,
                    i.item_group,
                    i.brand,
                    COALESCE(b.actual_qty, 0) as available_qty,
                    CASE 
                        WHEN i.item_code LIKE %s THEN 1
                        WHEN i.item_name LIKE %s THEN 2
                        WHEN i.item_name_ar LIKE %s THEN 3
                        ELSE 4
                    END as search_rank
                FROM `tabItem` i
                LEFT JOIN `tabBin` b ON i.item_code = b.item_code
                WHERE i.disabled = 0
                AND (i.item_code LIKE %s 
                     OR i.item_name LIKE %s 
                     OR i.item_name_ar LIKE %s
                     OR i.brand LIKE %s)
                ORDER BY search_rank, i.item_name
                LIMIT %s
            """,
                [search_term] * 7 + [limit],
                as_dict=True,
            )

            formatted_parts = []
            for part in parts:
                display_name = (
                    part.item_name_ar if language == "ar" and part.item_name_ar else part.item_name
                )

                formatted_parts.append(
                    {
                        "item_code": part.item_code,
                        "item_name": display_name,
                        "standard_rate": part.standard_rate,
                        "item_group": part.item_group,
                        "brand": part.brand,
                        "available_qty": part.available_qty or 0,
                        "in_stock": (part.available_qty or 0) > 0,
                    }
                )

            return {
                "parts": formatted_parts,
                "query": query,
                "total_found": len(formatted_parts),
                "language": language,
            }

        except Exception as e:
            frappe.log_error(f"Parts search error: {str(e)}")
            return {"error": _("Search failed")}


# Standalone utility functions


@frappe.whitelist()
def get_quick_suggestions(service_type, vehicle_make=None, language="en"):
    """Quick parts suggestions for immediate use"""
    engine = PartsAutoSuggestionEngine()
    return engine.get_parts_suggestions(
        service_type=service_type, vehicle_make=vehicle_make, language=language
    )


@frappe.whitelist()
def search_parts_api(query, limit=20, language="en"):
    """API wrapper for parts search"""
    engine = PartsAutoSuggestionEngine()
    return engine.search_parts(query=query, limit=int(limit), language=language)


@frappe.whitelist()
def get_category_parts(category, vehicle_make=None, language="en"):
    """API wrapper for category-based parts"""
    engine = PartsAutoSuggestionEngine()
    return engine.get_parts_by_category(
        category=category, vehicle_make=vehicle_make, language=language
    )


@frappe.whitelist()
def update_suggestion_feedback(item_code, service_estimate_id, was_useful=True):
    """Track suggestion feedback for ML improvement"""
    try:
        feedback_doc = frappe.new_doc("Parts Suggestion Feedback")
        feedback_doc.item_code = item_code
        feedback_doc.service_estimate = service_estimate_id
        feedback_doc.was_useful = was_useful
        feedback_doc.feedback_date = frappe.utils.now()
        feedback_doc.user = frappe.session.user
        feedback_doc.insert()

        return {"success": True, "message": _("Feedback recorded")}
    except Exception as e:
        frappe.log_error(f"Feedback recording error: {str(e)}")
        return {"error": _("Failed to record feedback")}
