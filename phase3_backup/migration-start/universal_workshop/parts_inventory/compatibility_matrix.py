# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Parts Compatibility Matrix System for Universal Workshop ERP
Tracks and visualizes compatibility relationships between parts, vehicles, and assemblies
"""

import json
from typing import Any, Dict, List, Optional, Set, Tuple
import re
import datetime

import frappe
from frappe import _
from frappe.utils import cint, flt, cstr


@frappe.whitelist()
def get_part_compatibility(item_code: str, compatibility_type: str = "all"):
    """
    Get compatibility information for a specific part

    Args:
        item_code: Item code to get compatibility for
        compatibility_type: Type of compatibility (all, vehicle, parts, assembly)

    Returns:
        Dict with compatibility information
    """
    try:
        item = frappe.get_doc("Item", item_code)

        compatibility_data = {
            "item_info": {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "item_group": item.item_group,
                "brand": getattr(item, "brand", ""),
                "vehicle_make": getattr(item, "vehicle_make", ""),
                "vehicle_model": getattr(item, "vehicle_model", ""),
                "vehicle_year_from": getattr(item, "vehicle_year_from", ""),
                "vehicle_year_to": getattr(item, "vehicle_year_to", ""),
                "part_category": getattr(item, "part_category", ""),
                "oem_part_number": getattr(item, "oem_part_number", ""),
                "aftermarket_part_number": getattr(item, "aftermarket_part_number", ""),
            }
        }

        if compatibility_type in ["all", "vehicle"]:
            compatibility_data["vehicle_compatibility"] = get_vehicle_compatibility(item_code)

        if compatibility_type in ["all", "parts"]:
            compatibility_data["part_compatibility"] = get_parts_compatibility(item_code)

        if compatibility_type in ["all", "assembly"]:
            compatibility_data["assembly_compatibility"] = get_assembly_compatibility(item_code)

        return {"success": True, "data": compatibility_data}

    except Exception as e:
        frappe.log_error(f"Part compatibility lookup failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to get compatibility information"),
            "error": str(e),
        }


def get_vehicle_compatibility(item_code: str) -> Dict[str, Any]:
    """
    Get vehicle compatibility for a part based on various criteria
    """
    try:
        item = frappe.get_doc("Item", item_code)

        vehicle_compatibility = {
            "exact_matches": [],
            "make_model_matches": [],
            "make_matches": [],
            "category_matches": [],
            "universal_parts": [],
        }

        # Direct vehicle compatibility from item fields
        if hasattr(item, "vehicle_make") and item.vehicle_make:
            exact_criteria = {"vehicle_make": item.vehicle_make}

            if hasattr(item, "vehicle_model") and item.vehicle_model:
                exact_criteria["vehicle_model"] = item.vehicle_model

            if hasattr(item, "vehicle_year_from") and item.vehicle_year_from:
                exact_criteria["vehicle_year_from"] = (">=", item.vehicle_year_from)

            if hasattr(item, "vehicle_year_to") and item.vehicle_year_to:
                exact_criteria["vehicle_year_to"] = ("<=", item.vehicle_year_to)

            # Get vehicles matching exact criteria
            exact_vehicles = frappe.get_list(
                "Vehicle",
                filters=exact_criteria,
                fields=["name", "license_plate", "make", "model", "year", "vin"],
                limit=100,
            )
            vehicle_compatibility["exact_matches"] = exact_vehicles

        # Find other parts for same vehicle make/model
        if hasattr(item, "vehicle_make") and item.vehicle_make:
            same_make_parts = frappe.db.sql(
                """
                SELECT DISTINCT vehicle_model, COUNT(*) as part_count
                FROM `tabItem`
                WHERE vehicle_make = %s
                AND item_code != %s
                AND disabled = 0
                AND is_stock_item = 1
                GROUP BY vehicle_model
                ORDER BY part_count DESC
                LIMIT 20
            """,
                (item.vehicle_make, item_code),
                as_dict=True,
            )

            vehicle_compatibility["make_model_matches"] = same_make_parts

        # Universal/generic parts (no specific vehicle assignment)
        if not (hasattr(item, "vehicle_make") and item.vehicle_make):
            # This is likely a universal part
            similar_universal = frappe.get_list(
                "Item",
                filters={
                    "item_group": item.item_group,
                    "vehicle_make": ["is", "not set"],
                    "disabled": 0,
                    "is_stock_item": 1,
                    "name": ["!=", item_code],
                },
                fields=["item_code", "item_name", "brand"],
                limit=20,
            )
            vehicle_compatibility["universal_parts"] = similar_universal

        return vehicle_compatibility

    except Exception as e:
        frappe.log_error(f"Vehicle compatibility lookup failed: {str(e)}")
        return {}


def get_parts_compatibility(item_code: str) -> Dict[str, Any]:
    """
    Get compatibility with other parts (substitutes, alternatives, related parts)
    """
    try:
        item = frappe.get_doc("Item", item_code)

        parts_compatibility = {
            "direct_substitutes": [],
            "alternative_brands": [],
            "related_parts": [],
            "complementary_parts": [],
            "incompatible_parts": [],
        }

        # Direct substitutes (same OEM part number or aftermarket number)
        substitute_filters = []
        if hasattr(item, "oem_part_number") and item.oem_part_number:
            substitute_filters.append(["oem_part_number", "=", item.oem_part_number])
        if hasattr(item, "aftermarket_part_number") and item.aftermarket_part_number:
            substitute_filters.append(
                ["aftermarket_part_number", "=", item.aftermarket_part_number]
            )

        if substitute_filters:
            substitutes = frappe.get_list(
                "Item",
                or_filters=substitute_filters,
                filters={"name": ["!=", item_code], "disabled": 0},
                fields=[
                    "item_code",
                    "item_name",
                    "brand",
                    "standard_rate",
                    "oem_part_number",
                    "aftermarket_part_number",
                ],
                limit=10,
            )
            parts_compatibility["direct_substitutes"] = substitutes

        # Alternative brands for same part function
        if hasattr(item, "part_category") and item.part_category:
            alt_brand_filters = {
                "part_category": item.part_category,
                "name": ["!=", item_code],
                "disabled": 0,
                "is_stock_item": 1,
            }

            if hasattr(item, "vehicle_make") and item.vehicle_make:
                alt_brand_filters["vehicle_make"] = item.vehicle_make
            if hasattr(item, "vehicle_model") and item.vehicle_model:
                alt_brand_filters["vehicle_model"] = item.vehicle_model

            alternative_brands = frappe.get_list(
                "Item",
                filters=alt_brand_filters,
                fields=["item_code", "item_name", "brand", "standard_rate", "part_category"],
                order_by="brand, standard_rate",
                limit=15,
            )
            parts_compatibility["alternative_brands"] = alternative_brands

        # Related parts in same assembly/system
        related_parts = get_assembly_related_parts(item_code)
        parts_compatibility["related_parts"] = related_parts

        # Complementary parts (often bought together)
        complementary_parts = get_complementary_parts(item_code)
        parts_compatibility["complementary_parts"] = complementary_parts

        return parts_compatibility

    except Exception as e:
        frappe.log_error(f"Parts compatibility lookup failed: {str(e)}")
        return {}


def get_assembly_compatibility(item_code: str) -> Dict[str, Any]:
    """
    Get assembly/system compatibility information
    """
    try:
        item = frappe.get_doc("Item", item_code)

        assembly_compatibility = {
            "parent_assemblies": [],
            "child_components": [],
            "system_parts": [],
            "assembly_diagrams": [],
        }

        # Check if this item is part of any BOM (Bill of Materials)
        parent_boms = frappe.get_list(
            "BOM Item", filters={"item_code": item_code}, fields=["parent", "qty", "rate"], limit=10
        )

        for bom_item in parent_boms:
            bom = frappe.get_doc("BOM", bom_item.parent)
            assembly_compatibility["parent_assemblies"].append(
                {
                    "bom": bom.name,
                    "item": bom.item,
                    "item_name": bom.item_name,
                    "quantity_required": bom_item.qty,
                    "is_active": bom.is_active,
                    "is_default": bom.is_default,
                }
            )

        # Check if this item has its own BOM (is an assembly)
        child_boms = frappe.get_list(
            "BOM",
            filters={"item": item_code, "disabled": 0},
            fields=["name", "is_active", "is_default"],
            limit=5,
        )

        for bom in child_boms:
            bom_doc = frappe.get_doc("BOM", bom.name)
            components = []
            for item_row in bom_doc.items:
                components.append(
                    {
                        "item_code": item_row.item_code,
                        "item_name": item_row.item_name,
                        "qty": item_row.qty,
                        "rate": item_row.rate,
                        "amount": item_row.amount,
                    }
                )

            assembly_compatibility["child_components"].append(
                {"bom": bom.name, "components": components, "total_cost": bom_doc.total_cost}
            )

        # Get parts in the same system/category
        if hasattr(item, "part_category") and item.part_category:
            system_parts = frappe.get_list(
                "Item",
                filters={
                    "part_category": item.part_category,
                    "name": ["!=", item_code],
                    "disabled": 0,
                    "is_stock_item": 1,
                },
                fields=["item_code", "item_name", "brand", "standard_rate"],
                order_by="item_name",
                limit=20,
            )
            assembly_compatibility["system_parts"] = system_parts

        return assembly_compatibility

    except Exception as e:
        frappe.log_error(f"Assembly compatibility lookup failed: {str(e)}")
        return {}


def get_assembly_related_parts(item_code: str) -> List[Dict[str, Any]]:
    """
    Get parts that are related through assembly/system relationships
    """
    try:
        # Get parts that appear in the same BOMs
        related_sql = """
            SELECT DISTINCT bi2.item_code, i.item_name, i.brand, i.standard_rate
            FROM `tabBOM Item` bi1
            JOIN `tabBOM Item` bi2 ON bi1.parent = bi2.parent
            JOIN `tabItem` i ON bi2.item_code = i.item_code
            WHERE bi1.item_code = %s
            AND bi2.item_code != %s
            AND i.disabled = 0
            LIMIT 15
        """

        related_parts = frappe.db.sql(related_sql, (item_code, item_code), as_dict=True)
        return related_parts

    except Exception as e:
        frappe.log_error(f"Assembly related parts lookup failed: {str(e)}")
        return []


def get_complementary_parts(item_code: str) -> List[Dict[str, Any]]:
    """
    Get parts that are often bought/used together (based on transaction history)
    """
    try:
        # Find parts that appear together in sales transactions
        complementary_sql = """
            SELECT 
                sii2.item_code,
                i.item_name,
                i.brand,
                i.standard_rate,
                COUNT(*) as frequency
            FROM `tabSales Invoice Item` sii1
            JOIN `tabSales Invoice Item` sii2 ON sii1.parent = sii2.parent
            JOIN `tabItem` i ON sii2.item_code = i.item_code
            WHERE sii1.item_code = %s
            AND sii2.item_code != %s
            AND i.disabled = 0
            GROUP BY sii2.item_code
            ORDER BY frequency DESC
            LIMIT 10
        """

        complementary_parts = frappe.db.sql(complementary_sql, (item_code, item_code), as_dict=True)
        return complementary_parts

    except Exception as e:
        frappe.log_error(f"Complementary parts lookup failed: {str(e)}")
        return []


@frappe.whitelist()
def search_compatible_parts(
    search_query: str = "",
    vehicle_make: str = "",
    vehicle_model: str = "",
    vehicle_year: str = "",
    part_category: str = "",
    compatibility_type: str = "all",
    page: int = 1,
    page_size: int = 20,
):
    """
    Search for parts with compatibility information

    Args:
        search_query: Text search query
        vehicle_make: Vehicle manufacturer filter
        vehicle_model: Vehicle model filter
        vehicle_year: Vehicle year filter
        part_category: Part category filter
        compatibility_type: Type of compatibility to include
        page: Page number
        page_size: Results per page

    Returns:
        Dict with search results and compatibility data
    """
    try:
        # Build search filters
        filters = {"disabled": 0, "is_stock_item": 1}

        if vehicle_make:
            filters["vehicle_make"] = vehicle_make
        if vehicle_model:
            filters["vehicle_model"] = vehicle_model
        if vehicle_year:
            filters["vehicle_year_from"] = ("<=", cint(vehicle_year))
            filters["vehicle_year_to"] = (">=", cint(vehicle_year))
        if part_category:
            filters["part_category"] = part_category

        # Build search conditions
        search_conditions = []
        if search_query:
            search_conditions = [
                ["item_name", "like", f"%{search_query}%"],
                ["item_code", "like", f"%{search_query}%"],
                ["oem_part_number", "like", f"%{search_query}%"],
                ["aftermarket_part_number", "like", f"%{search_query}%"],
                ["description", "like", f"%{search_query}%"],
            ]

        # Calculate pagination
        start = (page - 1) * page_size

        # Get total count
        total_count = frappe.db.count(
            "Item", filters=filters, or_filters=search_conditions if search_conditions else None
        )

        # Get items
        items = frappe.get_list(
            "Item",
            filters=filters,
            or_filters=search_conditions if search_conditions else None,
            fields=[
                "name",
                "item_code",
                "item_name",
                "item_group",
                "brand",
                "standard_rate",
                "stock_uom",
                "vehicle_make",
                "vehicle_model",
                "vehicle_year_from",
                "vehicle_year_to",
                "part_category",
                "oem_part_number",
                "aftermarket_part_number",
            ],
            order_by="item_name",
            start=start,
            page_length=page_size,
        )

        # Enhance with compatibility data
        enhanced_items = []
        for item in items:
            item_data = item.copy()

            if compatibility_type != "none":
                compatibility = get_part_compatibility(item.item_code, compatibility_type)
                if compatibility["success"]:
                    item_data["compatibility"] = compatibility["data"]

            enhanced_items.append(item_data)

        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "items": enhanced_items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_results": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
                "search_info": {
                    "query": search_query,
                    "filters": {
                        "vehicle_make": vehicle_make,
                        "vehicle_model": vehicle_model,
                        "vehicle_year": vehicle_year,
                        "part_category": part_category,
                        "compatibility_type": compatibility_type,
                    },
                },
            },
        }

    except Exception as e:
        frappe.log_error(f"Compatible parts search failed: {str(e)}")
        return {"success": False, "message": _("Search failed. Please try again."), "error": str(e)}


@frappe.whitelist()
def get_compatibility_matrix(item_codes: str):
    """
    Generate a compatibility matrix for multiple parts

    Args:
        item_codes: Comma-separated list of item codes

    Returns:
        Dict with compatibility matrix data
    """
    try:
        if isinstance(item_codes, str):
            item_list = [code.strip() for code in item_codes.split(",") if code.strip()]
        else:
            item_list = item_codes

        if len(item_list) > 20:
            return {
                "success": False,
                "message": _("Maximum 20 items allowed for matrix comparison"),
            }

        matrix_data = {
            "items": [],
            "compatibility_matrix": {},
            "summary": {
                "total_items": len(item_list),
                "compatible_pairs": 0,
                "incompatible_pairs": 0,
                "unknown_pairs": 0,
            },
        }

        # Get item information
        for item_code in item_list:
            try:
                item = frappe.get_doc("Item", item_code)
                matrix_data["items"].append(
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "vehicle_make": getattr(item, "vehicle_make", ""),
                        "vehicle_model": getattr(item, "vehicle_model", ""),
                        "part_category": getattr(item, "part_category", ""),
                        "brand": getattr(item, "brand", ""),
                    }
                )
            except frappe.DoesNotExistError:
                continue

        # Build compatibility matrix
        for i, item1_code in enumerate(item_list):
            matrix_data["compatibility_matrix"][item1_code] = {}

            for j, item2_code in enumerate(item_list):
                if i == j:
                    # Same item
                    matrix_data["compatibility_matrix"][item1_code][item2_code] = {
                        "status": "self",
                        "compatibility_score": 100,
                        "reasons": ["Same item"],
                    }
                else:
                    # Check compatibility between different items
                    compatibility = check_item_compatibility(item1_code, item2_code)
                    matrix_data["compatibility_matrix"][item1_code][item2_code] = compatibility

                    # Update summary
                    if compatibility["status"] == "compatible":
                        matrix_data["summary"]["compatible_pairs"] += 1
                    elif compatibility["status"] == "incompatible":
                        matrix_data["summary"]["incompatible_pairs"] += 1
                    else:
                        matrix_data["summary"]["unknown_pairs"] += 1

        return {"success": True, "data": matrix_data}

    except Exception as e:
        frappe.log_error(f"Compatibility matrix generation failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to generate compatibility matrix"),
            "error": str(e),
        }


def check_item_compatibility(item1_code: str, item2_code: str) -> Dict[str, Any]:
    """
    Check compatibility between two specific items
    """
    try:
        item1 = frappe.get_doc("Item", item1_code)
        item2 = frappe.get_doc("Item", item2_code)

        compatibility_score = 0
        reasons = []
        status = "unknown"

        # Vehicle compatibility
        vehicle_compatible = True

        # Check vehicle make
        make1 = getattr(item1, "vehicle_make", "")
        make2 = getattr(item2, "vehicle_make", "")

        if make1 and make2:
            if make1 == make2:
                compatibility_score += 25
                reasons.append("Same vehicle make")
            else:
                vehicle_compatible = False
                reasons.append("Different vehicle makes")
        elif make1 or make2:
            # One is universal, one is specific
            compatibility_score += 10
            reasons.append("Universal/specific compatibility")
        else:
            # Both universal
            compatibility_score += 15
            reasons.append("Both universal parts")

        # Check vehicle model
        model1 = getattr(item1, "vehicle_model", "")
        model2 = getattr(item2, "vehicle_model", "")

        if model1 and model2 and make1 == make2:
            if model1 == model2:
                compatibility_score += 25
                reasons.append("Same vehicle model")
            else:
                vehicle_compatible = False
                reasons.append("Different vehicle models")

        # Check vehicle years
        year1_from = getattr(item1, "vehicle_year_from", 0)
        year1_to = getattr(item1, "vehicle_year_to", 0)
        year2_from = getattr(item2, "vehicle_year_from", 0)
        year2_to = getattr(item2, "vehicle_year_to", 0)

        if year1_from and year1_to and year2_from and year2_to:
            # Check for year overlap
            if year1_from <= year2_to and year1_to >= year2_from:
                compatibility_score += 20
                reasons.append("Compatible year ranges")
            else:
                vehicle_compatible = False
                reasons.append("Non-overlapping year ranges")

        # Part category compatibility
        cat1 = getattr(item1, "part_category", "")
        cat2 = getattr(item2, "part_category", "")

        if cat1 and cat2:
            if cat1 == cat2:
                compatibility_score += 15
                reasons.append("Same part category")
            else:
                # Check if categories are related
                related_categories = check_related_categories(cat1, cat2)
                if related_categories:
                    compatibility_score += 10
                    reasons.append("Related part categories")
                else:
                    compatibility_score -= 10
                    reasons.append("Unrelated part categories")

        # Brand compatibility (same brand often compatible)
        brand1 = getattr(item1, "brand", "")
        brand2 = getattr(item2, "brand", "")

        if brand1 and brand2 and brand1 == brand2:
            compatibility_score += 10
            reasons.append("Same brand")

        # OEM/Aftermarket part number matching
        oem1 = getattr(item1, "oem_part_number", "")
        oem2 = getattr(item2, "oem_part_number", "")
        am1 = getattr(item1, "aftermarket_part_number", "")
        am2 = getattr(item2, "aftermarket_part_number", "")

        if (oem1 and oem2 and oem1 == oem2) or (am1 and am2 and am1 == am2):
            compatibility_score += 30
            reasons.append("Matching part numbers (substitutes)")

        # Check if they appear together in BOMs
        bom_compatibility = check_bom_compatibility(item1_code, item2_code)
        if bom_compatibility:
            compatibility_score += 15
            reasons.append("Used together in assemblies")

        # Determine final status
        if compatibility_score >= 70:
            status = "compatible"
        elif compatibility_score >= 40:
            status = "possibly_compatible"
        elif compatibility_score <= 20:
            status = "incompatible"
        else:
            status = "unknown"

        return {
            "status": status,
            "compatibility_score": min(100, max(0, compatibility_score)),
            "reasons": reasons,
            "vehicle_compatible": vehicle_compatible,
        }

    except Exception as e:
        return {
            "status": "error",
            "compatibility_score": 0,
            "reasons": [f"Error checking compatibility: {str(e)}"],
            "vehicle_compatible": False,
        }


def check_related_categories(cat1: str, cat2: str) -> bool:
    """
    Check if two part categories are related (e.g., both engine parts)
    """
    try:
        # Define category relationships
        category_groups = {
            "engine": ["Engine Block", "Pistons", "Valves", "Gaskets", "Oil Filter"],
            "transmission": ["Transmission", "Clutch", "Gearbox", "Differential"],
            "brakes": ["Brake Pads", "Brake Discs", "Brake Lines", "Brake Fluid"],
            "suspension": ["Shock Absorbers", "Springs", "Struts", "Bushings"],
            "electrical": ["Battery", "Alternator", "Starter", "Lights", "Wiring"],
            "cooling": ["Radiator", "Water Pump", "Thermostat", "Coolant"],
            "fuel": ["Fuel Pump", "Fuel Filter", "Injectors", "Fuel Tank"],
        }

        for group, categories in category_groups.items():
            if cat1 in categories and cat2 in categories:
                return True

        return False

    except Exception:
        return False


def check_bom_compatibility(item1_code: str, item2_code: str) -> bool:
    """
    Check if two items appear together in any BOM
    """
    try:
        sql = """
            SELECT COUNT(*) as count
            FROM `tabBOM Item` bi1
            JOIN `tabBOM Item` bi2 ON bi1.parent = bi2.parent
            WHERE bi1.item_code = %s AND bi2.item_code = %s
        """

        result = frappe.db.sql(sql, (item1_code, item2_code), as_dict=True)
        return result[0]["count"] > 0

    except Exception:
        return False


@frappe.whitelist()
def get_compatibility_filters():
    """
    Get available filter options for compatibility search
    """
    try:
        filters = {}

        # Vehicle makes
        filters["vehicle_makes"] = frappe.db.sql(
            """
            SELECT DISTINCT vehicle_make as name
            FROM `tabItem`
            WHERE vehicle_make IS NOT NULL 
            AND vehicle_make != ''
            AND disabled = 0
            ORDER BY vehicle_make
        """,
            as_dict=True,
        )

        # Part categories
        filters["part_categories"] = frappe.db.sql(
            """
            SELECT DISTINCT part_category as name
            FROM `tabItem`
            WHERE part_category IS NOT NULL 
            AND part_category != ''
            AND disabled = 0
            ORDER BY part_category
        """,
            as_dict=True,
        )

        # Brands
        filters["brands"] = frappe.db.sql(
            """
            SELECT DISTINCT brand as name
            FROM `tabItem`
            WHERE brand IS NOT NULL 
            AND brand != ''
            AND disabled = 0
            ORDER BY brand
        """,
            as_dict=True,
        )

        # Compatibility types
        filters["compatibility_types"] = [
            {"name": "all", "label": _("All Compatibility")},
            {"name": "vehicle", "label": _("Vehicle Compatibility")},
            {"name": "parts", "label": _("Parts Compatibility")},
            {"name": "assembly", "label": _("Assembly Compatibility")},
            {"name": "none", "label": _("No Compatibility Data")},
        ]

        return {"success": True, "filters": filters}

    except Exception as e:
        frappe.log_error(f"Compatibility filters failed: {str(e)}")
        return {"success": False, "message": _("Failed to load filter options"), "error": str(e)}


# VIN DECODING SYSTEM
@frappe.whitelist()
def decode_vin(vin: str) -> Dict[str, Any]:
    """
    Decode VIN to extract vehicle information for compatibility matching
    
    Args:
        vin: 17-character Vehicle Identification Number
        
    Returns:
        Dict with decoded vehicle information
    """
    try:
        if not vin or len(vin) != 17:
            return {
                "success": False,
                "message": _("VIN must be exactly 17 characters"),
                "error": "Invalid VIN length"
            }
        
        # Clean and validate VIN
        vin = vin.upper().replace('O', '0').replace('I', '1').replace('Q', '9')
        
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
            return {
                "success": False,
                "message": _("Invalid VIN format"),
                "error": "VIN contains invalid characters"
            }
        
        # Extract VIN components
        wmi = vin[0:3]  # World Manufacturer Identifier
        vds = vin[3:9]  # Vehicle Descriptor Section
        vis = vin[9:17]  # Vehicle Identifier Section
        
        # Decode manufacturer from WMI
        manufacturer_map = {
            '1': 'United States', '4': 'United States', '5': 'United States',
            '2': 'Canada', '3': 'Mexico',
            'J': 'Japan', 'K': 'South Korea',
            'L': 'China', 'M': 'India', 'N': 'Turkey',
            'S': 'United Kingdom', 'T': 'Czechoslovakia', 'U': 'Romania',
            'V': 'France', 'W': 'Germany', 'X': 'Russia',
            'Y': 'Sweden', 'Z': 'Italy'
        }
        
        # Common manufacturer WMI codes
        manufacturer_codes = {
            '1HG': 'Honda', '1HT': 'Honda', '2HG': 'Honda', '19U': 'Honda',
            '1G1': 'Chevrolet', '1G6': 'Cadillac', '1GM': 'Pontiac',
            '1FA': 'Ford', '1FB': 'Ford', '1FC': 'Ford', '1FD': 'Ford',
            '1FT': 'Ford', '1FU': 'Ford', '1FV': 'Ford',
            '4T1': 'Toyota', '4T3': 'Toyota', '5TD': 'Toyota',
            'JHM': 'Honda', 'JH4': 'Acura',
            'JTD': 'Toyota', 'JT2': 'Toyota', 'JT3': 'Lexus',
            'KNA': 'Kia', 'KND': 'Kia',
            'KMH': 'Hyundai', 'KMJ': 'Hyundai',
            'WBA': 'BMW', 'WBS': 'BMW', 'WBY': 'BMW',
            'WDB': 'Mercedes-Benz', 'WDC': 'Mercedes-Benz', 'WDD': 'Mercedes-Benz',
            'WVW': 'Volkswagen', 'WV1': 'Volkswagen', 'WV2': 'Volkswagen',
            'WAU': 'Audi', 'WAG': 'Audi', 'WA1': 'Audi',
        }
        
        # Model year from position 10
        year_codes = {
            'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984,
            'F': 1985, 'G': 1986, 'H': 1987, 'J': 1988, 'K': 1989,
            'L': 1990, 'M': 1991, 'N': 1992, 'P': 1993, 'R': 1994,
            'S': 1995, 'T': 1996, 'V': 1997, 'W': 1998, 'X': 1999,
            'Y': 2000, '1': 2001, '2': 2002, '3': 2003, '4': 2004,
            '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
            'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
            'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
            'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024,
            'S': 2025, 'T': 2026, 'V': 2027, 'W': 2028, 'X': 2029,
            'Y': 2030
        }
        
        # Decode information
        decoded_info = {
            "vin": vin,
            "wmi": wmi,
            "vds": vds,
            "vis": vis,
            "country": manufacturer_map.get(vin[0], "Unknown"),
            "manufacturer": manufacturer_codes.get(wmi, "Unknown"),
            "model_year": year_codes.get(vin[9], None),
            "plant_code": vin[10],
            "serial_number": vin[11:17],
            "check_digit": vin[8],
            "body_style": vds[3:5] if len(vds) >= 5 else "",
            "engine_code": vds[4] if len(vds) >= 5 else "",
            "series": vds[2] if len(vds) >= 3 else ""
        }
        
        # Validate check digit
        if validate_vin_check_digit(vin):
            decoded_info["check_digit_valid"] = True
        else:
            decoded_info["check_digit_valid"] = False
            decoded_info["warning"] = _("VIN check digit validation failed")
        
        # Get compatible parts based on decoded VIN
        compatible_parts = get_parts_by_vin_data(decoded_info)
        
        return {
            "success": True,
            "data": decoded_info,
            "compatible_parts": compatible_parts,
            "message": _("VIN decoded successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"VIN decoding failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to decode VIN"),
            "error": str(e)
        }


def validate_vin_check_digit(vin: str) -> bool:
    """
    Validate VIN check digit using standard algorithm
    """
    try:
        # VIN character weights and values
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        values = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
            'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
        }
        
        total = 0
        for i, char in enumerate(vin):
            if i == 8:  # Skip check digit position
                continue
            total += values.get(char, 0) * weights[i]
        
        remainder = total % 11
        check_digit = 'X' if remainder == 10 else str(remainder)
        
        return vin[8] == check_digit
        
    except Exception:
        return False


def get_parts_by_vin_data(vin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get compatible parts based on decoded VIN information
    """
    try:
        parts = []
        
        # Search by manufacturer and model year
        if vin_data.get("manufacturer") and vin_data.get("model_year"):
            manufacturer_parts = frappe.db.sql("""
                SELECT 
                    item_code, item_name, brand, standard_rate,
                    vehicle_make, vehicle_model, vehicle_year_from, vehicle_year_to,
                    part_category, oem_part_number
                FROM `tabItem`
                WHERE vehicle_make LIKE %s
                AND (
                    (vehicle_year_from <= %s AND vehicle_year_to >= %s) OR
                    (vehicle_year_from IS NULL AND vehicle_year_to IS NULL)
                )
                AND disabled = 0
                AND is_stock_item = 1
                ORDER BY standard_rate ASC
                LIMIT 50
            """, (
                f"%{vin_data['manufacturer']}%",
                vin_data['model_year'],
                vin_data['model_year']
            ), as_dict=True)
            
            parts.extend(manufacturer_parts)
        
        # Add universal parts that might fit
        universal_parts = frappe.db.sql("""
            SELECT 
                item_code, item_name, brand, standard_rate,
                part_category, oem_part_number
            FROM `tabItem`
            WHERE (vehicle_make IS NULL OR vehicle_make = '')
            AND disabled = 0
            AND is_stock_item = 1
            AND part_category IN ('Filters / المرشحات', 'Fluids & Oils / السوائل والزيوت', 
                                'Battery & Ignition / البطارية والإشعال')
            ORDER BY standard_rate ASC
            LIMIT 20
        """, as_dict=True)
        
        parts.extend(universal_parts)
        
        return parts
        
    except Exception as e:
        frappe.log_error(f"VIN parts lookup failed: {str(e)}")
        return []


# ADVANCED FITMENT SYSTEM
@frappe.whitelist()
def check_part_fitment(item_code: str, vehicle_info: Dict[str, Any], 
                      service_context: str = "") -> Dict[str, Any]:
    """
    Advanced fitment validation for parts to vehicles
    
    Args:
        item_code: Part to check fitment for
        vehicle_info: Vehicle details (make, model, year, engine, etc.)
        service_context: Service type context for relevance
        
    Returns:
        Dict with fitment validation results
    """
    try:
        item = frappe.get_doc("Item", item_code)
        
        fitment_result = {
            "item_code": item_code,
            "vehicle_info": vehicle_info,
            "fitment_status": "unknown",
            "confidence_score": 0,
            "fitment_details": [],
            "warnings": [],
            "alternatives": [],
            "installation_notes": []
        }
        
        # Basic vehicle compatibility check
        make_match = check_make_compatibility(item, vehicle_info.get("make", ""))
        model_match = check_model_compatibility(item, vehicle_info.get("model", ""))
        year_match = check_year_compatibility(item, vehicle_info)
        
        # Calculate confidence score
        confidence = 0
        
        if make_match["compatible"]:
            confidence += 40
            fitment_result["fitment_details"].append(make_match["message"])
        else:
            fitment_result["warnings"].append(make_match["message"])
        
        if model_match["compatible"]:
            confidence += 30
            fitment_result["fitment_details"].append(model_match["message"])
        elif make_match["compatible"]:
            confidence += 15  # Same make, different model might still fit
            fitment_result["fitment_details"].append("Same make, check model compatibility")
        
        if year_match["compatible"]:
            confidence += 25
            fitment_result["fitment_details"].append(year_match["message"])
        else:
            fitment_result["warnings"].append(year_match["message"])
        
        # Engine compatibility if available
        if vehicle_info.get("engine_code") or vehicle_info.get("engine_size"):
            engine_match = check_engine_compatibility(item, vehicle_info)
            if engine_match["compatible"]:
                confidence += 20
                fitment_result["fitment_details"].append(engine_match["message"])
            else:
                fitment_result["warnings"].append(engine_match["message"])
        
        # Service context relevance
        if service_context:
            relevance = check_service_relevance(item, service_context)
            if relevance["relevant"]:
                confidence += 10
                fitment_result["fitment_details"].append(relevance["message"])
            else:
                fitment_result["warnings"].append(relevance["message"])
        
        # Determine fitment status
        if confidence >= 85:
            fitment_result["fitment_status"] = "perfect_fit"
        elif confidence >= 65:
            fitment_result["fitment_status"] = "good_fit"
        elif confidence >= 40:
            fitment_result["fitment_status"] = "possible_fit"
        elif confidence >= 20:
            fitment_result["fitment_status"] = "check_required"
        else:
            fitment_result["fitment_status"] = "not_recommended"
        
        fitment_result["confidence_score"] = min(100, confidence)
        
        # Get alternative parts if fitment is not perfect
        if confidence < 85:
            alternatives = find_alternative_parts(item, vehicle_info, service_context)
            fitment_result["alternatives"] = alternatives[:5]  # Top 5 alternatives
        
        # Add installation notes
        installation_notes = get_installation_notes(item, vehicle_info)
        fitment_result["installation_notes"] = installation_notes
        
        return {
            "success": True,
            "data": fitment_result
        }
        
    except Exception as e:
        frappe.log_error(f"Fitment check failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to check part fitment"),
            "error": str(e)
        }


def check_make_compatibility(item, vehicle_make: str) -> Dict[str, Any]:
    """Check vehicle make compatibility"""
    item_make = getattr(item, "vehicle_make", "")
    
    if not item_make:
        return {
            "compatible": True,
            "message": _("Universal part - compatible with all makes"),
            "confidence": 50
        }
    
    if item_make.lower() == vehicle_make.lower():
        return {
            "compatible": True,
            "message": _("Exact make match"),
            "confidence": 100
        }
    
    # Check for make synonyms/variants
    make_synonyms = {
        "bmw": ["bmw", "mini"],
        "volkswagen": ["volkswagen", "vw", "audi", "seat", "skoda"],
        "general motors": ["chevrolet", "gmc", "cadillac", "buick"],
        "ford": ["ford", "lincoln", "mercury"],
        "toyota": ["toyota", "lexus", "scion"],
        "nissan": ["nissan", "infiniti", "datsun"],
        "honda": ["honda", "acura"],
        "hyundai": ["hyundai", "kia", "genesis"]
    }
    
    for group, makes in make_synonyms.items():
        if (item_make.lower() in makes and vehicle_make.lower() in makes):
            return {
                "compatible": True,
                "message": _(f"Compatible within {group} group"),
                "confidence": 80
            }
    
    return {
        "compatible": False,
        "message": _(f"Make mismatch: {item_make} vs {vehicle_make}"),
        "confidence": 0
    }


def check_model_compatibility(item, vehicle_model: str) -> Dict[str, Any]:
    """Check vehicle model compatibility"""
    item_model = getattr(item, "vehicle_model", "")
    
    if not item_model:
        return {
            "compatible": True,
            "message": _("No specific model requirement"),
            "confidence": 70
        }
    
    if item_model.lower() == vehicle_model.lower():
        return {
            "compatible": True,
            "message": _("Exact model match"),
            "confidence": 100
        }
    
    # Check for model variants/generations
    if vehicle_model.lower() in item_model.lower() or item_model.lower() in vehicle_model.lower():
        return {
            "compatible": True,
            "message": _("Model variant compatibility"),
            "confidence": 85
        }
    
    return {
        "compatible": False,
        "message": _(f"Model mismatch: {item_model} vs {vehicle_model}"),
        "confidence": 0
    }


def check_year_compatibility(item, vehicle_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check vehicle year compatibility"""
    vehicle_year = vehicle_info.get("year")
    if not vehicle_year:
        return {
            "compatible": True,
            "message": _("No vehicle year specified"),
            "confidence": 50
        }
    
    year_from = getattr(item, "vehicle_year_from", None)
    year_to = getattr(item, "vehicle_year_to", None)
    
    if not year_from and not year_to:
        return {
            "compatible": True,
            "message": _("No year restrictions"),
            "confidence": 70
        }
    
    vehicle_year = int(vehicle_year)
    
    if year_from and year_to:
        if year_from <= vehicle_year <= year_to:
            return {
                "compatible": True,
                "message": _(f"Year {vehicle_year} within range {year_from}-{year_to}"),
                "confidence": 100
            }
        else:
            return {
                "compatible": False,
                "message": _(f"Year {vehicle_year} outside range {year_from}-{year_to}"),
                "confidence": 0
            }
    
    elif year_from:
        if vehicle_year >= year_from:
            return {
                "compatible": True,
                "message": _(f"Year {vehicle_year} after {year_from}"),
                "confidence": 90
            }
        else:
            return {
                "compatible": False,
                "message": _(f"Year {vehicle_year} before minimum {year_from}"),
                "confidence": 0
            }
    
    elif year_to:
        if vehicle_year <= year_to:
            return {
                "compatible": True,
                "message": _(f"Year {vehicle_year} before {year_to}"),
                "confidence": 90
            }
        else:
            return {
                "compatible": False,
                "message": _(f"Year {vehicle_year} after maximum {year_to}"),
                "confidence": 0
            }
    
    return {
        "compatible": True,
        "message": _("Year compatibility unknown"),
        "confidence": 50
    }


def check_engine_compatibility(item, vehicle_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check engine compatibility"""
    engine_code = vehicle_info.get("engine_code", "")
    engine_size = vehicle_info.get("engine_size", "")
    
    item_engine = getattr(item, "engine_type", "")
    
    if not item_engine:
        return {
            "compatible": True,
            "message": _("No engine restriction"),
            "confidence": 60
        }
    
    if engine_code and engine_code.lower() in item_engine.lower():
        return {
            "compatible": True,
            "message": _(f"Engine code {engine_code} matches"),
            "confidence": 95
        }
    
    if engine_size and engine_size in item_engine:
        return {
            "compatible": True,
            "message": _(f"Engine size {engine_size} matches"),
            "confidence": 90
        }
    
    return {
        "compatible": False,
        "message": _(f"Engine mismatch: {item_engine} vs {engine_code or engine_size}"),
        "confidence": 0
    }


def check_service_relevance(item, service_context: str) -> Dict[str, Any]:
    """Check if part is relevant for service context"""
    part_category = getattr(item, "part_category", "")
    
    service_categories = {
        "oil_change": ["Engine Parts", "Filters", "Fluids & Oils"],
        "brake_service": ["Brake System", "Fluids & Oils"],
        "engine_repair": ["Engine Parts", "Filters", "Belts & Hoses"],
        "transmission_service": ["Transmission", "Fluids & Oils"],
        "tire_replacement": ["Tires & Wheels"],
        "battery_replacement": ["Battery & Ignition", "Electrical"],
        "cooling_service": ["Cooling System", "Fluids & Oils"]
    }
    
    relevant_categories = service_categories.get(service_context.lower(), [])
    
    if any(cat in part_category for cat in relevant_categories):
        return {
            "relevant": True,
            "message": _(f"Part relevant for {service_context}"),
            "confidence": 90
        }
    
    return {
        "relevant": False,
        "message": _(f"Part not typically used for {service_context}"),
        "confidence": 0
    }


def find_alternative_parts(item, vehicle_info: Dict[str, Any], 
                         service_context: str = "") -> List[Dict[str, Any]]:
    """Find alternative parts with better fitment"""
    try:
        alternatives = []
        
        # Search for better fitting parts
        filters = {
            "disabled": 0,
            "is_stock_item": 1,
            "name": ["!=", item.name]
        }
        
        # Add vehicle filters if available
        if vehicle_info.get("make"):
            filters["vehicle_make"] = vehicle_info["make"]
        if vehicle_info.get("model"):
            filters["vehicle_model"] = vehicle_info["model"]
        
        # Same category parts
        if hasattr(item, "part_category") and item.part_category:
            filters["part_category"] = item.part_category
        
        alternative_items = frappe.get_list(
            "Item",
            filters=filters,
            fields=[
                "item_code", "item_name", "brand", "standard_rate",
                "vehicle_make", "vehicle_model", "vehicle_year_from", "vehicle_year_to",
                "part_category", "oem_part_number"
            ],
            limit=10,
            order_by="standard_rate ASC"
        )
        
        for alt_item in alternative_items:
            # Quick fitment check for each alternative
            alt_fitment = check_part_fitment(
                alt_item["item_code"], 
                vehicle_info, 
                service_context
            )
            
            if alt_fitment.get("success") and alt_fitment["data"]["confidence_score"] > 60:
                alternative = alt_item.copy()
                alternative["fitment_score"] = alt_fitment["data"]["confidence_score"]
                alternative["fitment_status"] = alt_fitment["data"]["fitment_status"]
                alternatives.append(alternative)
        
        # Sort by fitment score
        alternatives.sort(key=lambda x: x["fitment_score"], reverse=True)
        
        return alternatives
        
    except Exception as e:
        frappe.log_error(f"Alternative parts search failed: {str(e)}")
        return []


def get_installation_notes(item, vehicle_info: Dict[str, Any]) -> List[str]:
    """Get installation notes and warnings for the part"""
    notes = []
    
    part_category = getattr(item, "part_category", "")
    
    # Category-specific installation notes
    if "brake" in part_category.lower():
        notes.append(_("Always replace brake parts in pairs"))
        notes.append(_("Bleed brake system after installation"))
        notes.append(_("Check brake fluid level"))
    
    elif "filter" in part_category.lower():
        notes.append(_("Replace filter housing gasket"))
        notes.append(_("Pre-fill oil filters before installation"))
        notes.append(_("Check for proper seal"))
    
    elif "battery" in part_category.lower():
        notes.append(_("Disconnect negative terminal first"))
        notes.append(_("Check alternator charging system"))
        notes.append(_("Apply terminal protection"))
    
    elif "tire" in part_category.lower():
        notes.append(_("Check wheel alignment after installation"))
        notes.append(_("Balance wheels"))
        notes.append(_("Check tire pressure"))
    
    # Vehicle-specific notes
    vehicle_make = vehicle_info.get("make", "").lower()
    if vehicle_make in ["bmw", "mercedes", "audi"]:
        notes.append(_("May require specialized tools"))
        notes.append(_("Follow manufacturer torque specifications"))
    
    return notes
