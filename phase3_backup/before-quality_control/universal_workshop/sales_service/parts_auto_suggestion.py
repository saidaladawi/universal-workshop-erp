# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class PartsAutoSuggestionEngine:
    """
    Intelligent parts auto-suggestion engine for automotive workshop
    Uses historical data, vehicle compatibility, and inventory awareness
    """

    def __init__(self):
        self.service_type_mapping = self.get_service_type_mapping()
        self.vehicle_parts_matrix = self.load_vehicle_parts_matrix()

    def get_service_type_mapping(self):
        """Map service types to common part categories"""
        return {
            "Engine Repair": [
                "Engine Oil",
                "Oil Filter",
                "Air Filter",
                "Spark Plugs",
                "Engine Gaskets",
            ],
            "Transmission": [
                "Transmission Fluid",
                "Transmission Filter",
                "Clutch Kit",
                "CV Joints",
            ],
            "Brakes": ["Brake Pads", "Brake Discs", "Brake Fluid", "Brake Lines", "Brake Calipers"],
            "Electrical": [
                "Battery",
                "Alternator",
                "Starter",
                "Spark Plugs",
                "Electrical Connectors",
            ],
            "Air Conditioning": ["AC Filter", "AC Compressor", "AC Refrigerant", "AC Belt"],
            "General Maintenance": ["Engine Oil", "Oil Filter", "Air Filter", "Fuel Filter"],
            "Body Work": ["Body Panels", "Paint", "Adhesives", "Fasteners"],
            "Tire Service": ["Tires", "Tire Valves", "Wheel Alignment", "Tire Balancing"],
            "Oil Change": ["Engine Oil", "Oil Filter", "Oil Drain Plug"],
            "Inspection": ["Light Bulbs", "Fuses", "Fluids", "Belts"],
        }

    def load_vehicle_parts_matrix(self):
        """Load vehicle-specific parts compatibility matrix"""
        # This would typically be loaded from a database or configuration file
        # For now, we'll create a basic structure
        return {
            "toyota": {
                "camry": ["Oil Filter OF-123", "Air Filter AF-456", "Brake Pads BP-789"],
                "corolla": ["Oil Filter OF-124", "Air Filter AF-457", "Brake Pads BP-790"],
                "prado": ["Oil Filter OF-125", "Air Filter AF-458", "Brake Pads BP-791"],
            },
            "nissan": {
                "altima": ["Oil Filter OF-126", "Air Filter AF-459", "Brake Pads BP-792"],
                "patrol": ["Oil Filter OF-127", "Air Filter AF-460", "Brake Pads BP-793"],
            },
            "honda": {
                "civic": ["Oil Filter OF-128", "Air Filter AF-461", "Brake Pads BP-794"],
                "accord": ["Oil Filter OF-129", "Air Filter AF-462", "Brake Pads BP-795"],
            },
        }

    @frappe.whitelist()
    def get_parts_suggestions(
        self, service_type=None, vehicle=None, customer=None, description=None, max_suggestions=10
    ):
        """
        Main method to get intelligent parts suggestions

        Args:
            service_type: Type of service being performed
            vehicle: Vehicle ID or details
            customer: Customer ID for historical analysis
            description: Service description for keyword analysis
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested parts with confidence scores and availability
        """
        try:
            suggestions = []

            # 1. Service type based suggestions
            if service_type:
                service_suggestions = self.get_service_type_suggestions(service_type)
                suggestions.extend(service_suggestions)

            # 2. Vehicle-specific suggestions
            if vehicle:
                vehicle_suggestions = self.get_vehicle_specific_suggestions(vehicle)
                suggestions.extend(vehicle_suggestions)

            # 3. Historical data suggestions
            if customer:
                historical_suggestions = self.get_historical_suggestions(customer, vehicle)
                suggestions.extend(historical_suggestions)

            # 4. Description keyword analysis
            if description:
                keyword_suggestions = self.analyze_description_keywords(description)
                suggestions.extend(keyword_suggestions)

            # 5. Combine and rank suggestions
            ranked_suggestions = self.rank_and_filter_suggestions(suggestions, max_suggestions)

            # 6. Add inventory information
            final_suggestions = self.add_inventory_information(ranked_suggestions)

            return final_suggestions

        except Exception as e:
            frappe.log_error(f"Parts suggestion error: {str(e)}")
            return []

    def get_service_type_suggestions(self, service_type):
        """Get parts suggestions based on service type"""
        suggestions = []

        if service_type in self.service_type_mapping:
            part_categories = self.service_type_mapping[service_type]

            for category in part_categories:
                # Find items in this category
                items = frappe.get_list(
                    "Item",
                    filters={
                        "item_group": ["like", f"%{category}%"],
                        "disabled": 0,
                        "is_stock_item": 1,
                    },
                    fields=["name", "item_name", "item_code", "standard_rate"],
                    limit=3,
                )

                for item in items:
                    suggestions.append(
                        {
                            "item_code": item.item_code,
                            "item_name": item.item_name,
                            "source": "service_type",
                            "confidence": 0.8,
                            "rate": item.standard_rate or 0,
                            "category": category,
                        }
                    )

        return suggestions

    def get_vehicle_specific_suggestions(self, vehicle):
        """Get parts suggestions specific to vehicle make/model"""
        suggestions = []

        try:
            vehicle_doc = frappe.get_doc("Vehicle", vehicle)
            make = vehicle_doc.make.lower() if vehicle_doc.make else ""
            model = vehicle_doc.model.lower() if vehicle_doc.model else ""

            # Check our compatibility matrix
            if make in self.vehicle_parts_matrix:
                if model in self.vehicle_parts_matrix[make]:
                    compatible_parts = self.vehicle_parts_matrix[make][model]

                    for part_code in compatible_parts:
                        # Find the actual item
                        item = frappe.db.get_value(
                            "Item",
                            {"item_code": ["like", f"%{part_code}%"]},
                            ["name", "item_name", "item_code", "standard_rate"],
                            as_dict=True,
                        )

                        if item:
                            suggestions.append(
                                {
                                    "item_code": item.item_code,
                                    "item_name": item.item_name,
                                    "source": "vehicle_specific",
                                    "confidence": 0.9,
                                    "rate": item.standard_rate or 0,
                                    "vehicle_compatibility": f"{make} {model}",
                                }
                            )

            # Also search for parts with vehicle make/model in name or description
            vehicle_parts = frappe.get_list(
                "Item",
                filters={"item_name": ["like", f"%{make}%"], "disabled": 0, "is_stock_item": 1},
                fields=["name", "item_name", "item_code", "standard_rate"],
                limit=5,
            )

            for item in vehicle_parts:
                suggestions.append(
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "source": "vehicle_search",
                        "confidence": 0.7,
                        "rate": item.standard_rate or 0,
                    }
                )

        except Exception as e:
            frappe.log_error(f"Vehicle suggestion error: {str(e)}")

        return suggestions

    def get_historical_suggestions(self, customer, vehicle=None):
        """Get suggestions based on customer's service history"""
        suggestions = []

        try:
            # Get customer's previous service estimates
            filters = {"customer": customer, "docstatus": 1}
            if vehicle:
                filters["vehicle"] = vehicle

            previous_estimates = frappe.get_list(
                "Service Estimate",
                filters=filters,
                fields=["name"],
                order_by="creation desc",
                limit=10,
            )

            part_frequency = Counter()

            for estimate in previous_estimates:
                # Get parts from previous estimates
                parts = frappe.get_list(
                    "Service Estimate Parts",
                    filters={"parent": estimate.name},
                    fields=["part_code", "part_name"],
                )

                for part in parts:
                    part_frequency[part.part_code] += 1

            # Convert to suggestions with frequency-based confidence
            for part_code, frequency in part_frequency.most_common(5):
                item = frappe.db.get_value(
                    "Item", part_code, ["item_name", "standard_rate"], as_dict=True
                )

                if item:
                    confidence = min(0.9, 0.5 + (frequency * 0.1))
                    suggestions.append(
                        {
                            "item_code": part_code,
                            "item_name": item.item_name,
                            "source": "historical",
                            "confidence": confidence,
                            "rate": item.standard_rate or 0,
                            "frequency": frequency,
                        }
                    )

        except Exception as e:
            frappe.log_error(f"Historical suggestion error: {str(e)}")

        return suggestions

    def analyze_description_keywords(self, description):
        """Analyze service description for relevant keywords"""
        suggestions = []

        try:
            # Define keyword mappings
            keyword_mappings = {
                "oil": ["Engine Oil", "Oil Filter"],
                "brake": ["Brake Pads", "Brake Discs", "Brake Fluid"],
                "battery": ["Battery", "Battery Terminal"],
                "tire": ["Tires", "Tire Valve"],
                "filter": ["Oil Filter", "Air Filter", "Fuel Filter"],
                "fluid": ["Brake Fluid", "Transmission Fluid", "Power Steering Fluid"],
                "belt": ["Timing Belt", "Serpentine Belt", "AC Belt"],
                "spark": ["Spark Plugs", "Ignition Coils"],
                "air": ["Air Filter", "Air Conditioning"],
            }

            description_lower = description.lower()

            for keyword, part_types in keyword_mappings.items():
                if keyword in description_lower:
                    for part_type in part_types:
                        # Search for items of this type
                        items = frappe.get_list(
                            "Item",
                            filters={
                                "item_name": ["like", f"%{part_type}%"],
                                "disabled": 0,
                                "is_stock_item": 1,
                            },
                            fields=["name", "item_name", "item_code", "standard_rate"],
                            limit=2,
                        )

                        for item in items:
                            suggestions.append(
                                {
                                    "item_code": item.item_code,
                                    "item_name": item.item_name,
                                    "source": "description_analysis",
                                    "confidence": 0.6,
                                    "rate": item.standard_rate or 0,
                                    "keyword": keyword,
                                }
                            )

        except Exception as e:
            frappe.log_error(f"Description analysis error: {str(e)}")

        return suggestions

    def rank_and_filter_suggestions(self, suggestions, max_suggestions):
        """Rank suggestions by confidence and remove duplicates"""
        # Remove duplicates while keeping highest confidence
        unique_suggestions = {}

        for suggestion in suggestions:
            item_code = suggestion["item_code"]

            if item_code not in unique_suggestions:
                unique_suggestions[item_code] = suggestion
            else:
                # Keep the one with higher confidence
                if suggestion["confidence"] > unique_suggestions[item_code]["confidence"]:
                    unique_suggestions[item_code] = suggestion

        # Sort by confidence score descending
        ranked = sorted(unique_suggestions.values(), key=lambda x: x["confidence"], reverse=True)

        return ranked[:max_suggestions]

    def add_inventory_information(self, suggestions):
        """Add real-time inventory information to suggestions"""
        final_suggestions = []

        for suggestion in suggestions:
            try:
                # Get current stock information
                stock_info = frappe.get_list(
                    "Stock Ledger Entry",
                    filters={"item_code": suggestion["item_code"]},
                    fields=["sum(actual_qty) as total_qty"],
                    group_by="item_code",
                )

                current_stock = 0
                if stock_info and stock_info[0].total_qty:
                    current_stock = stock_info[0].total_qty

                # Get supplier information
                suppliers = frappe.get_list(
                    "Item Supplier",
                    filters={"parent": suggestion["item_code"]},
                    fields=["supplier", "supplier_part_no"],
                    limit=1,
                )

                supplier_info = suppliers[0] if suppliers else None

                # Determine availability status
                if current_stock > 0:
                    availability = "In Stock"
                    availability_ar = "متوفر"
                elif current_stock == 0:
                    availability = "Out of Stock"
                    availability_ar = "غير متوفر"
                else:
                    availability = "Unknown"
                    availability_ar = "غير معروف"

                # Enhanced suggestion with inventory data
                enhanced_suggestion = {
                    **suggestion,
                    "current_stock": current_stock,
                    "availability": availability,
                    "availability_ar": availability_ar,
                    "supplier": supplier_info.supplier if supplier_info else None,
                    "supplier_part_no": supplier_info.supplier_part_no if supplier_info else None,
                    "stock_status_color": "green" if current_stock > 0 else "red",
                }

                final_suggestions.append(enhanced_suggestion)

            except Exception as e:
                frappe.log_error(f"Inventory info error for {suggestion['item_code']}: {str(e)}")
                # Add suggestion without inventory info
                final_suggestions.append(
                    {
                        **suggestion,
                        "current_stock": 0,
                        "availability": "Unknown",
                        "availability_ar": "غير معروف",
                    }
                )

        return final_suggestions

    def learn_from_selection(self, estimate_id, selected_parts, suggested_parts):
        """Learn from user selections to improve future suggestions"""
        try:
            # Log the learning data for future ML model training
            learning_data = {
                "estimate_id": estimate_id,
                "selected_parts": selected_parts,
                "suggested_parts": suggested_parts,
                "timestamp": datetime.now(),
                "user": frappe.session.user,
            }

            # This could be stored in a learning database or file for ML training
            frappe.log_error(json.dumps(learning_data), "Parts Suggestion Learning")

        except Exception as e:
            frappe.log_error(f"Learning error: {str(e)}")


# Initialize the global suggestion engine
suggestion_engine = PartsAutoSuggestionEngine()


@frappe.whitelist()
def get_parts_suggestions(
    service_type=None, vehicle=None, customer=None, description=None, max_suggestions=10
):
    """
    API endpoint for getting parts suggestions
    """
    return suggestion_engine.get_parts_suggestions(
        service_type=service_type,
        vehicle=vehicle,
        customer=customer,
        description=description,
        max_suggestions=cint(max_suggestions),
    )


@frappe.whitelist()
def add_suggested_part_to_estimate(estimate_id, part_code, quantity=1):
    """
    Add a suggested part to an existing service estimate
    """
    try:
        estimate = frappe.get_doc("Service Estimate", estimate_id)

        # Get item details
        item = frappe.get_doc("Item", part_code)

        # Add to parts table
        estimate.append(
            "parts_items",
            {
                "part_code": part_code,
                "part_name": item.item_name,
                "part_name_ar": getattr(item, "item_name_ar", ""),
                "description": item.description or "",
                "qty": quantity,
                "rate": item.standard_rate or 0,
                "amount": (item.standard_rate or 0) * quantity,
            },
        )

        estimate.save()

        return {"success": True, "message": _("Part added successfully")}

    except Exception as e:
        frappe.log_error(f"Add part error: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def log_suggestion_feedback(estimate_id, part_code, action, feedback=None):
    """
    Log user feedback on suggestions for learning
    """
    try:
        feedback_data = {
            "estimate_id": estimate_id,
            "part_code": part_code,
            "action": action,  # 'selected', 'rejected', 'modified'
            "feedback": feedback,
            "timestamp": datetime.now(),
            "user": frappe.session.user,
        }

        # Log for future ML training
        frappe.log_error(json.dumps(feedback_data), "Parts Suggestion Feedback")

        return {"success": True}

    except Exception as e:
        frappe.log_error(f"Feedback logging error: {str(e)}")
        return {"success": False, "message": str(e)}
