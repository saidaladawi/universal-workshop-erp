# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Advanced Search System for Parts Inventory Management
Supports real-time search, filters, keyword search, and attribute-based queries
"""

import json
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import cint, flt


@frappe.whitelist()
def advanced_item_search(
    query: str = "",
    part_category: str = "",
    vehicle_make: str = "",
    vehicle_model: str = "",
    vehicle_year_from: str = "",
    vehicle_year_to: str = "",
    part_condition: str = "",
    price_from: str = "",
    price_to: str = "",
    availability_status: str = "",
    stock_level: str = "",
    supplier: str = "",
    brand: str = "",
    location: str = "",
    language: str = "en",
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "modified",
    sort_order: str = "desc",
):
    """
    Advanced search for inventory items with comprehensive filtering

    Args:
        query: Text search query (item name, part number, description)
        part_category: Filter by part category
        vehicle_make: Filter by vehicle manufacturer
        vehicle_model: Filter by vehicle model
        vehicle_year_from: Filter by minimum vehicle year
        vehicle_year_to: Filter by maximum vehicle year
        part_condition: Filter by part condition (New, Used, Refurbished)
        price_from: Minimum price filter
        price_to: Maximum price filter
        availability_status: Filter by availability (In Stock, Low Stock, Out of Stock)
        stock_level: Filter by stock level category
        supplier: Filter by supplier
        brand: Filter by part brand
        location: Filter by warehouse location
        language: Language for results (en/ar)
        page: Page number for pagination
        page_size: Results per page
        sort_by: Field to sort by
        sort_order: Sort direction (asc/desc)

    Returns:
        Dict with search results and pagination info
    """
    try:
        # Build base filters
        filters = {"disabled": 0, "is_stock_item": 1}

        # Add specific filters
        if part_category:
            filters["item_group"] = part_category
        if supplier:
            filters["default_supplier"] = supplier
        if brand:
            filters["brand"] = brand

        # Build search conditions for text query
        search_conditions = []
        if query:
            search_conditions = [
                ["item_name", "like", f"%{query}%"],
                ["item_code", "like", f"%{query}%"],
                ["barcode", "like", f"%{query}%"],
                ["description", "like", f"%{query}%"],
            ]

            # Add Arabic search if available
            if hasattr(
                frappe.get_doc("Item", {"disabled": 0, "is_stock_item": 1}, "name"), "item_name_ar"
            ):
                search_conditions.extend(
                    [
                        ["item_name_ar", "like", f"%{query}%"],
                        ["description_ar", "like", f"%{query}%"],
                    ]
                )

        # Add custom field filters for automotive parts
        custom_filters = []

        if vehicle_make:
            custom_filters.append(["vehicle_make", "=", vehicle_make])
        if vehicle_model:
            custom_filters.append(["vehicle_model", "=", vehicle_model])
        if vehicle_year_from:
            custom_filters.append(["vehicle_year_from", ">=", cint(vehicle_year_from)])
        if vehicle_year_to:
            custom_filters.append(["vehicle_year_to", "<=", cint(vehicle_year_to)])
        if part_condition:
            custom_filters.append(["part_condition", "=", part_condition])

        # Price filters
        if price_from:
            custom_filters.append(["standard_rate", ">=", flt(price_from)])
        if price_to:
            custom_filters.append(["standard_rate", "<=", flt(price_to)])

        # Combine all filters
        all_filters = filters.copy()
        for cf in custom_filters:
            all_filters[cf[0]] = (cf[1], cf[2])

        # Calculate pagination
        start = (page - 1) * page_size

        # Get total count
        total_count = frappe.db.count(
            "Item", filters=all_filters, or_filters=search_conditions if search_conditions else None
        )

        # Define fields to return
        fields = [
            "name",
            "item_code",
            "item_name",
            "item_group",
            "description",
            "standard_rate",
            "stock_uom",
            "barcode",
            "image",
            "brand",
            "disabled",
            "is_stock_item",
            "creation",
            "modified",
        ]

        # Add Arabic fields if language is Arabic
        if language == "ar":
            fields.extend(["item_name_ar", "description_ar"])

        # Add custom automotive fields
        fields.extend(
            [
                "vehicle_make",
                "vehicle_model",
                "vehicle_year_from",
                "vehicle_year_to",
                "part_condition",
                "oem_part_number",
                "aftermarket_part_number",
                "part_category",
                "default_supplier",
            ]
        )

        # Execute search
        items = frappe.get_list(
            "Item",
            filters=all_filters,
            or_filters=search_conditions if search_conditions else None,
            fields=fields,
            order_by=f"{sort_by} {sort_order}",
            start=start,
            page_length=page_size,
        )

        # Enhance results with stock information
        enhanced_items = []
        for item in items:
            # Get current stock levels
            stock_info = get_item_stock_info(item.name, location)
            item.update(stock_info)

            # Apply availability status filter if specified
            if availability_status:
                if availability_status == "In Stock" and item.get("total_stock", 0) <= 0:
                    continue
                elif availability_status == "Low Stock" and item.get("total_stock", 0) > item.get(
                    "reorder_level", 10
                ):
                    continue
                elif availability_status == "Out of Stock" and item.get("total_stock", 0) > 0:
                    continue

            enhanced_items.append(item)

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
                    "query": query,
                    "filters_applied": len(
                        [
                            f
                            for f in [
                                part_category,
                                vehicle_make,
                                vehicle_model,
                                price_from,
                                price_to,
                                supplier,
                                brand,
                            ]
                            if f
                        ]
                    ),
                    "language": language,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                },
            },
        }

    except Exception as e:
        frappe.log_error(f"Advanced item search failed: {str(e)}", "Advanced Item Search")
        return {"success": False, "message": _("Search failed. Please try again."), "error": str(e)}


def get_item_stock_info(item_code: str, location: str = "") -> Dict[str, Any]:
    """
    Get comprehensive stock information for an item

    Args:
        item_code: Item code to get stock info for
        location: Optional warehouse location filter

    Returns:
        Dict with stock information
    """
    try:
        # Get current stock balance
        from erpnext.stock.utils import get_stock_balance

        if location:
            stock_balance = get_stock_balance(item_code, location)
            warehouses = [location]
        else:
            # Get total stock across all warehouses
            stock_balance = get_stock_balance(item_code)

            # Get stock by warehouse
            warehouses = frappe.get_list("Warehouse", filters={"disabled": 0}, fields=["name"])
            warehouses = [w.name for w in warehouses]

        # Get reorder level
        item = frappe.get_doc("Item", item_code)
        reorder_level = 0
        if hasattr(item, "reorder_level") and item.reorder_level:
            reorder_level = item.reorder_level

        # Determine availability status
        availability_status = "Out of Stock"
        if stock_balance > reorder_level:
            availability_status = "In Stock"
        elif stock_balance > 0:
            availability_status = "Low Stock"

        # Get recent transactions
        recent_transactions = frappe.get_list(
            "Stock Ledger Entry",
            filters={"item_code": item_code},
            fields=["posting_date", "voucher_type", "actual_qty", "qty_after_transaction"],
            order_by="posting_date desc",
            limit=5,
        )

        return {
            "total_stock": stock_balance,
            "reorder_level": reorder_level,
            "availability_status": availability_status,
            "warehouses": warehouses,
            "recent_transactions": recent_transactions,
            "stock_value": stock_balance * (item.standard_rate or 0),
        }

    except Exception as e:
        frappe.log_error(f"Stock info retrieval failed for {item_code}: {str(e)}")
        return {
            "total_stock": 0,
            "availability_status": "Unknown",
            "warehouses": [],
            "recent_transactions": [],
        }


@frappe.whitelist()
def get_search_filters():
    """
    Get available filter options for advanced search

    Returns:
        Dict with all available filter options
    """
    try:
        # Get unique values for filter dropdowns
        filters = {}

        # Part categories (Item Groups)
        filters["part_categories"] = frappe.get_list(
            "Item Group",
            filters={"disabled": 0},
            fields=["name", "parent_item_group"],
            order_by="name",
        )

        # Vehicle makes
        filters["vehicle_makes"] = frappe.db.sql(
            """
            SELECT DISTINCT vehicle_make 
            FROM `tabItem` 
            WHERE vehicle_make IS NOT NULL 
            AND vehicle_make != ''
            AND disabled = 0
            ORDER BY vehicle_make
        """,
            as_dict=True,
        )

        # Vehicle models (top 50 most common)
        filters["vehicle_models"] = frappe.db.sql(
            """
            SELECT DISTINCT vehicle_model, COUNT(*) as count
            FROM `tabItem` 
            WHERE vehicle_model IS NOT NULL 
            AND vehicle_model != ''
            AND disabled = 0
            GROUP BY vehicle_model
            ORDER BY count DESC, vehicle_model
            LIMIT 50
        """,
            as_dict=True,
        )

        # Part conditions
        filters["part_conditions"] = [
            {"name": "New", "value": "New"},
            {"name": "Used", "value": "Used"},
            {"name": "Refurbished", "value": "Refurbished"},
            {"name": "Damaged", "value": "Damaged"},
        ]

        # Suppliers
        filters["suppliers"] = frappe.get_list(
            "Supplier",
            filters={"disabled": 0},
            fields=["name", "supplier_name"],
            order_by="supplier_name",
        )

        # Brands
        filters["brands"] = frappe.db.sql(
            """
            SELECT DISTINCT brand 
            FROM `tabItem` 
            WHERE brand IS NOT NULL 
            AND brand != ''
            AND disabled = 0
            ORDER BY brand
        """,
            as_dict=True,
        )

        # Warehouses
        filters["warehouses"] = frappe.get_list(
            "Warehouse",
            filters={"disabled": 0},
            fields=["name", "warehouse_name"],
            order_by="warehouse_name",
        )

        return {"success": True, "filters": filters}

    except Exception as e:
        frappe.log_error(f"Filter options retrieval failed: {str(e)}")
        return {"success": False, "message": _("Failed to load filter options"), "error": str(e)}


@frappe.whitelist()
def get_item_suggestions(text: str, limit: int = 10):
    """
    Get auto-completion suggestions for search queries

    Args:
        text: Partial text to complete
        limit: Maximum number of suggestions

    Returns:
        List of suggestions
    """
    try:
        suggestions = []

        if len(text) >= 2:  # Minimum 2 characters for suggestions
            # Search in item names and codes
            items = frappe.db.sql(
                """
                SELECT DISTINCT item_name, item_code
                FROM `tabItem`
                WHERE (item_name LIKE %(text)s 
                       OR item_code LIKE %(text)s
                       OR barcode LIKE %(text)s)
                AND disabled = 0
                AND is_stock_item = 1
                ORDER BY 
                    CASE 
                        WHEN item_code LIKE %(exact_text)s THEN 1
                        WHEN item_name LIKE %(exact_text)s THEN 2
                        ELSE 3
                    END,
                    item_name
                LIMIT %(limit)s
            """,
                {"text": f"%{text}%", "exact_text": f"{text}%", "limit": limit},
                as_dict=True,
            )

            for item in items:
                suggestions.append(
                    {"value": item.item_name, "data": item.item_code, "type": "item"}
                )

        return {"success": True, "suggestions": suggestions}

    except Exception as e:
        frappe.log_error(f"Item suggestions failed: {str(e)}")
        return {"success": False, "suggestions": []}


@frappe.whitelist()
def quick_search(query: str, limit: int = 5):
    """
    Quick search for instant results as user types

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of quick results
    """
    try:
        if len(query) < 2:
            return {"success": True, "results": []}

        # Search with high relevance scoring
        results = frappe.db.sql(
            """
            SELECT 
                name, item_code, item_name, standard_rate, stock_uom,
                CASE 
                    WHEN item_code = %(query)s THEN 1
                    WHEN barcode = %(query)s THEN 1
                    WHEN item_code LIKE %(exact_query)s THEN 2
                    WHEN item_name LIKE %(exact_query)s THEN 2
                    WHEN item_name LIKE %(query_pattern)s THEN 3
                    ELSE 4
                END as relevance_score
            FROM `tabItem`
            WHERE (item_name LIKE %(query_pattern)s 
                   OR item_code LIKE %(query_pattern)s
                   OR barcode = %(query)s)
            AND disabled = 0
            AND is_stock_item = 1
            ORDER BY relevance_score, item_name
            LIMIT %(limit)s
        """,
            {
                "query": query,
                "exact_query": f"{query}%",
                "query_pattern": f"%{query}%",
                "limit": limit,
            },
            as_dict=True,
        )

        # Enhance with stock info
        for result in results:
            stock_info = get_item_stock_info(result.name)
            result.update(
                {
                    "stock_qty": stock_info.get("total_stock", 0),
                    "availability": stock_info.get("availability_status", "Unknown"),
                }
            )

        return {"success": True, "results": results, "query": query}

    except Exception as e:
        frappe.log_error(f"Quick search failed: {str(e)}")
        return {"success": False, "results": [], "error": str(e)}
