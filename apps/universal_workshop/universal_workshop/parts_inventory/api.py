# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""API methods for automotive parts inventory management with Arabic support"""

import re

import frappe
from frappe import _
from universal_workshop.utils.arabic_utils import normalize_arabic_text


@frappe.whitelist()
def search_parts_by_vehicle(make, model=None, year=None, part_category=None, search_term=None):
    """Search automotive parts by vehicle compatibility with Arabic support"""

    # Build base query
    conditions = []
    values = []

    # Vehicle compatibility conditions
    if make:
        conditions.append("(vehicle_make = %s OR vehicle_make IS NULL)")
        values.append(make)

    if model:
        conditions.append("(vehicle_model = %s OR vehicle_model IS NULL)")
        values.append(model)

    if year:
        conditions.append("(year_from <= %s AND (year_to >= %s OR year_to IS NULL))")
        values.extend([year, year])

    if part_category:
        conditions.append("part_category = %s")
        values.append(part_category)

    # Text search in multiple fields (Arabic and English)
    if search_term:
        search_term = normalize_arabic_text(search_term) if search_term else ""
        search_conditions = [
            "item_name LIKE %s",
            "item_code LIKE %s",
            "oem_part_number LIKE %s",
            "aftermarket_part_number LIKE %s",
            "description LIKE %s",
        ]
        search_values = [f"%{search_term}%"] * 5

        conditions.append(f"({' OR '.join(search_conditions)})")
        values.extend(search_values)

    # Only show items in automotive parts groups
    conditions.append(
        """(
        item_group LIKE '%Auto Parts%' OR
        item_group LIKE '%قطع غيار%' OR
        part_category IS NOT NULL
    )"""
    )

    # Build final query
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            name, item_code, item_name,
            oem_part_number, aftermarket_part_number,
            part_category, vehicle_make, vehicle_model,
            year_from, year_to,
            standard_rate, stock_uom,
            min_stock_level, preferred_supplier,
            is_fast_moving
        FROM `tabItem`
        WHERE {where_clause}
        AND disabled = 0
        ORDER BY
            CASE WHEN is_fast_moving = 1 THEN 0 ELSE 1 END,
            item_name
        LIMIT 50
    """

    return frappe.db.sql(query, values, as_dict=True)


@frappe.whitelist()
def search_parts_by_cross_reference(cross_ref_number, manufacturer=None):
    """Search parts by cross reference numbers with Arabic support"""

    if not cross_ref_number:
        frappe.throw(_("Cross reference number is required"))

    # Normalize the search term
    cross_ref_number = cross_ref_number.strip().upper()

    # Search in cross reference table
    conditions = ["pcr.cross_ref_number LIKE %s"]
    values = [f"%{cross_ref_number}%"]

    if manufacturer:
        conditions.append("pcr.manufacturer = %s")
        values.append(manufacturer)

    query = f"""
        SELECT DISTINCT
            i.name, i.item_code, i.item_name,
            i.oem_part_number, i.aftermarket_part_number,
            i.part_category, i.vehicle_make, i.vehicle_model,
            i.standard_rate, i.stock_uom,
            pcr.cross_ref_number, pcr.manufacturer, pcr.reference_type,
            pcr.is_primary
        FROM `tabItem` i
        INNER JOIN `tabPart Cross Reference` pcr ON i.name = pcr.parent
        WHERE {" AND ".join(conditions)}
        AND i.disabled = 0
        ORDER BY
            pcr.is_primary DESC,
            CASE WHEN pcr.reference_type = 'OEM' THEN 0 ELSE 1 END,
            i.item_name
        LIMIT 30
    """

    return frappe.db.sql(query, values, as_dict=True)


@frappe.whitelist()
def get_part_compatibility_matrix(item_code):
    """Get complete compatibility matrix for a specific part"""

    if not item_code:
        frappe.throw(_("Item code is required"))

    # Get main item details
    item = frappe.get_doc("Item", item_code)

    # Get cross references
    cross_refs = frappe.get_all(
        "Part Cross Reference",
        filters={"parent": item_code},
        fields=["manufacturer", "cross_ref_number", "reference_type", "is_primary"],
    )

    # Get compatible vehicles (if specific compatibility is set)
    vehicle_compatibility = {}
    if item.vehicle_make:
        vehicle_compatibility = {
            "make": item.vehicle_make,
            "model": item.vehicle_model,
            "year_from": item.year_from,
            "year_to": item.year_to,
        }

    # Get stock levels across warehouses
    stock_levels = frappe.get_all(
        "Stock Ledger Entry",
        filters={"item_code": item_code, "is_cancelled": 0},
        fields=["warehouse", "sum(actual_qty) as actual_qty"],
        group_by="warehouse",
        having="sum(actual_qty) > 0",
    )

    return {
        "item_details": {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "oem_part_number": item.oem_part_number,
            "aftermarket_part_number": item.aftermarket_part_number,
            "part_category": item.part_category,
            "part_material": item.part_material,
            "dimensions": {
                "length": item.part_length,
                "width": item.part_width,
                "height": item.part_height,
            },
            "installation_notes": item.installation_notes,
        },
        "vehicle_compatibility": vehicle_compatibility,
        "cross_references": cross_refs,
        "stock_levels": stock_levels,
        "inventory_settings": {
            "min_stock_level": item.min_stock_level,
            "max_stock_level": item.max_stock_level,
            "reorder_quantity": item.reorder_quantity,
            "preferred_supplier": item.preferred_supplier,
            "is_fast_moving": item.is_fast_moving,
        },
    }


@frappe.whitelist()
def get_automotive_part_categories():
    """Get list of automotive part categories with Arabic translations"""

    categories = [
        {
            "value": "Engine Parts / قطع المحرك",
            "label": _("Engine Parts"),
            "label_ar": "قطع المحرك",
        },
        {
            "value": "Transmission / ناقل الحركة",
            "label": _("Transmission"),
            "label_ar": "ناقل الحركة",
        },
        {
            "value": "Brake System / نظام الفرامل",
            "label": _("Brake System"),
            "label_ar": "نظام الفرامل",
        },
        {
            "value": "Suspension / نظام التعليق",
            "label": _("Suspension"),
            "label_ar": "نظام التعليق",
        },
        {
            "value": "Electrical / النظام الكهربائي",
            "label": _("Electrical"),
            "label_ar": "النظام الكهربائي",
        },
        {
            "value": "Exhaust System / نظام العادم",
            "label": _("Exhaust System"),
            "label_ar": "نظام العادم",
        },
        {
            "value": "Cooling System / نظام التبريد",
            "label": _("Cooling System"),
            "label_ar": "نظام التبريد",
        },
        {
            "value": "Fuel System / نظام الوقود",
            "label": _("Fuel System"),
            "label_ar": "نظام الوقود",
        },
        {"value": "Steering / نظام التوجيه", "label": _("Steering"), "label_ar": "نظام التوجيه"},
        {"value": "Body Parts / قطع الهيكل", "label": _("Body Parts"), "label_ar": "قطع الهيكل"},
        {"value": "Interior / الداخلية", "label": _("Interior"), "label_ar": "الداخلية"},
        {"value": "Filters / المرشحات", "label": _("Filters"), "label_ar": "المرشحات"},
        {
            "value": "Belts & Hoses / الأحزمة والخراطيم",
            "label": _("Belts & Hoses"),
            "label_ar": "الأحزمة والخراطيم",
        },
        {
            "value": "Fluids & Oils / السوائل والزيوت",
            "label": _("Fluids & Oils"),
            "label_ar": "السوائل والزيوت",
        },
        {
            "value": "Tires & Wheels / الإطارات والعجلات",
            "label": _("Tires & Wheels"),
            "label_ar": "الإطارات والعجلات",
        },
        {
            "value": "Battery & Ignition / البطارية والإشعال",
            "label": _("Battery & Ignition"),
            "label_ar": "البطارية والإشعال",
        },
        {
            "value": "Lights & Signals / الأضواء والإشارات",
            "label": _("Lights & Signals"),
            "label_ar": "الأضواء والإشارات",
        },
        {"value": "Other / أخرى", "label": _("Other"), "label_ar": "أخرى"},
    ]

    return categories


@frappe.whitelist()
def get_parts_for_vehicle_service(vehicle, service_type=None):
    """Get recommended parts for vehicle service based on service type"""

    if not vehicle:
        frappe.throw(_("Vehicle is required"))

    # Get vehicle details
    vehicle_doc = frappe.get_doc("Vehicle", vehicle)

    # Get parts compatible with this vehicle
    parts = search_parts_by_vehicle(
        make=vehicle_doc.make, model=vehicle_doc.model, year=vehicle_doc.year
    )

    # Filter by service type if provided
    if service_type:
        service_parts_map = {
            "Oil Change": [
                "Engine Parts / قطع المحرك",
                "Filters / المرشحات",
                "Fluids & Oils / السوائل والزيوت",
            ],
            "Brake Service": ["Brake System / نظام الفرامل", "Fluids & Oils / السوائل والزيوت"],
            "Engine Repair": [
                "Engine Parts / قطع المحرك",
                "Filters / المرشحات",
                "Belts & Hoses / الأحزمة والخراطيم",
            ],
            "Transmission Service": [
                "Transmission / ناقل الحركة",
                "Fluids & Oils / السوائل والزيوت",
            ],
            "Tire Replacement": ["Tires & Wheels / الإطارات والعجلات"],
            "Battery Replacement": [
                "Battery & Ignition / البطارية والإشعال",
                "Electrical / النظام الكهربائي",
            ],
            "Air Filter Replacement": ["Filters / المرشحات"],
            "Cooling System Service": [
                "Cooling System / نظام التبريد",
                "Fluids & Oils / السوائل والزيوت",
            ],
            "Electrical Repair": [
                "Electrical / النظام الكهربائي",
                "Battery & Ignition / البطارية والإشعال",
            ],
        }

        relevant_categories = service_parts_map.get(service_type, [])
        if relevant_categories:
            parts = [p for p in parts if p.get("part_category") in relevant_categories]

    return {
        "vehicle_info": {
            "vehicle": vehicle,
            "make": vehicle_doc.make,
            "model": vehicle_doc.model,
            "year": vehicle_doc.year,
            "license_plate": vehicle_doc.license_plate,
        },
        "recommended_parts": parts,
        "service_type": service_type,
    }


@frappe.whitelist()
def update_part_stock_levels(item_code, min_stock=None, max_stock=None, reorder_qty=None):
    """Update stock level parameters for automotive parts"""

    if not item_code:
        frappe.throw(_("Item code is required"))

    item = frappe.get_doc("Item", item_code)

    if min_stock is not None:
        item.min_stock_level = min_stock

    if max_stock is not None:
        item.max_stock_level = max_stock

    if reorder_qty is not None:
        item.reorder_quantity = reorder_qty

    item.save()

    return {
        "message": _("Stock levels updated successfully"),
        "item_code": item_code,
        "min_stock_level": item.min_stock_level,
        "max_stock_level": item.max_stock_level,
        "reorder_quantity": item.reorder_quantity,
    }


@frappe.whitelist()
def get_item_by_barcode(barcode):
    """
    Get item details by barcode with Arabic support

    Args:
            barcode (str): Barcode to search for

    Returns:
            dict: Item details if found, None otherwise
    """
    if not barcode:
        frappe.throw(_("Barcode is required"))

    # Clean and normalize barcode
    barcode = barcode.strip()

    # Search for item by barcode
    item_code = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")

    if not item_code:
        # Try searching in item_code field directly
        if frappe.db.exists("Item", barcode):
            item_code = barcode
        else:
            # Try searching by OEM or aftermarket part numbers
            item_code = frappe.db.get_value(
                "Item", {"oem_part_number": barcode, "disabled": 0}, "item_code"
            )

            if not item_code:
                item_code = frappe.db.get_value(
                    "Item", {"aftermarket_part_number": barcode, "disabled": 0}, "item_code"
                )

    if not item_code:
        return None

    # Get item details
    item = frappe.get_doc("Item", item_code)

    # Get current stock levels
    stock_qty = (
        frappe.db.sql(
            """
		SELECT SUM(actual_qty) as qty
		FROM `tabStock Ledger Entry`
		WHERE item_code = %s AND is_cancelled = 0
	""",
            [item_code],
        )[0][0]
        or 0
    )

    # Get available stock by warehouse
    warehouse_stock = frappe.db.sql(
        """
		SELECT warehouse, SUM(actual_qty) as qty
		FROM `tabStock Ledger Entry`
		WHERE item_code = %s AND is_cancelled = 0
		GROUP BY warehouse
		HAVING SUM(actual_qty) > 0
		ORDER BY warehouse
	""",
        [item_code],
        as_dict=True,
    )

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_name_ar": getattr(item, "item_name_ar", ""),
        "barcode": barcode,
        "standard_rate": item.standard_rate,
        "stock_uom": item.stock_uom,
        "current_stock": stock_qty,
        "warehouse_stock": warehouse_stock,
        "part_category": getattr(item, "part_category", ""),
        "oem_part_number": getattr(item, "oem_part_number", ""),
        "aftermarket_part_number": getattr(item, "aftermarket_part_number", ""),
        "vehicle_make": getattr(item, "vehicle_make", ""),
        "vehicle_model": getattr(item, "vehicle_model", ""),
        "description": item.description,
        "is_stock_item": item.is_stock_item,
        "min_stock_level": getattr(item, "min_stock_level", 0),
        "is_fast_moving": getattr(item, "is_fast_moving", 0),
    }


@frappe.whitelist()
def get_parts_catalog(search="", category="", make="", price_range="",
                     stock_status="", page=1, lang="en", limit=20):
    """Get parts catalog data with filters for the web interface"""
    try:
        page = int(page)
        limit = int(limit)
        offset = (page - 1) * limit

        # Build filters
        filters = {"disabled": 0}
        conditions = []
        values = {}

        # Search filter
        if search:
            search = normalize_arabic_text(search) if search else ""
            conditions.append("""
                (item_name LIKE %(search)s
                OR item_code LIKE %(search)s
                OR description LIKE %(search)s
                OR oem_part_number LIKE %(search)s
                OR aftermarket_part_number LIKE %(search)s)
            """)
            values["search"] = f"%{search}%"

        # Category filter
        if category:
            conditions.append("item_group = %(category)s")
            values["category"] = category

        # Vehicle make filter
        if make:
            conditions.append("(vehicle_make = %(make)s OR vehicle_make IS NULL)")
            values["make"] = make

        # Stock status filter
        if stock_status == "in-stock":
            conditions.append("EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty > 0)")
        elif stock_status == "low-stock":
            conditions.append("EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty <= 5 AND actual_qty > 0)")
        elif stock_status == "out-stock":
            conditions.append("NOT EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty > 0)")

        # Price range filter
        if price_range:
            if price_range == "0-100":
                conditions.append("standard_rate BETWEEN 0 AND 100")
            elif price_range == "100-500":
                conditions.append("standard_rate BETWEEN 100 AND 500")
            elif price_range == "500-1000":
                conditions.append("standard_rate BETWEEN 500 AND 1000")
            elif price_range == "1000-5000":
                conditions.append("standard_rate BETWEEN 1000 AND 5000")
            elif price_range == "5000+":
                conditions.append("standard_rate > 5000")

        # Build WHERE clause
        where_clause = " AND ".join([f"{k} = %({k})s" for k in filters.keys() if k != "disabled"])
        if where_clause:
            where_clause = "disabled = 0 AND " + where_clause
        else:
            where_clause = "disabled = 0"

        if conditions:
            where_clause += " AND " + " AND ".join(conditions)

        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabItem`
            WHERE {where_clause}
        """

        count_result = frappe.db.sql(count_query, values, as_dict=True)
        total_results = count_result[0].total if count_result else 0
        total_pages = (total_results + limit - 1) // limit

        # Get parts data
        parts_query = f"""
            SELECT
                i.name,
                i.item_code,
                i.item_name,
                i.description,
                i.item_group,
                i.brand,
                i.image,
                i.stock_uom,
                i.standard_rate as price,
                i.vehicle_make,
                i.vehicle_model,
                i.year_from,
                i.year_to,
                i.oem_part_number,
                i.aftermarket_part_number,
                i.part_category,
                COALESCE(SUM(b.actual_qty), 0) as stock_qty,
                'SAR' as currency
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            WHERE {where_clause}
            GROUP BY i.name
            ORDER BY
                CASE WHEN i.is_fast_moving = 1 THEN 0 ELSE 1 END,
                i.item_name
            LIMIT {limit} OFFSET {offset}
        """

        parts = frappe.db.sql(parts_query, values, as_dict=True)

        # Process parts data
        processed_parts = []
        for part in parts:
            # Add Arabic translations if requested
            if lang == "ar":
                part["item_name_ar"] = get_arabic_translation(part.item_name)
                part["description_ar"] = get_arabic_translation(part.description or "")

            # Format price
            part["formatted_price"] = format_currency(part.price or 0, part.currency)

            # Add compatibility info
            part["compatible_vehicles"] = get_part_compatibility_string(part.name)

            # Add cross-reference info
            part["cross_references"] = get_part_cross_references(part.name)

            processed_parts.append(part)

        return {
            "success": True,
            "parts": processed_parts,
            "total_results": total_results,
            "total_pages": total_pages,
            "current_page": page
        }

    except Exception as e:
        frappe.log_error(f"Error getting parts catalog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "parts": [],
            "total_results": 0,
            "total_pages": 0
        }


@frappe.whitelist()
def get_part_details(part_id, lang="en"):
    """Get detailed information for a specific part"""
    try:
        # Get basic part info
        part = frappe.get_doc("Item", part_id)

        # Get stock information
        stock_info = frappe.db.sql("""
            SELECT
                warehouse,
                actual_qty,
                reserved_qty,
                projected_qty,
                valuation_rate
            FROM `tabBin`
            WHERE item_code = %s AND actual_qty > 0
            ORDER BY actual_qty DESC
        """, part_id, as_dict=True)

        # Get price information
        price_info = frappe.db.sql("""
            SELECT
                price_list,
                price_list_rate,
                currency,
                valid_from,
                valid_upto
            FROM `tabItem Price`
            WHERE item_code = %s
            ORDER BY price_list, valid_from DESC
        """, part_id, as_dict=True)

        # Get cross-reference information
        cross_refs = get_part_cross_references(part_id, detailed=True)

        # Get compatibility information
        compatibility = get_part_compatibility_details(part_id)

        # Get supplier information
        suppliers = frappe.get_all(
            "Item Supplier",
            filters={"parent": part_id},
            fields=["supplier", "supplier_part_no", "lead_time_days"]
        )

        # Build response
        part_details = {
            "name": part.name,
            "item_code": part.item_code,
            "item_name": part.item_name,
            "description": part.description,
            "item_group": part.item_group,
            "brand": part.brand,
            "image": part.image,
            "stock_uom": part.stock_uom,
            "standard_rate": part.standard_rate,
            "oem_part_number": getattr(part, 'oem_part_number', ''),
            "aftermarket_part_number": getattr(part, 'aftermarket_part_number', ''),
            "part_category": getattr(part, 'part_category', ''),
            "vehicle_make": getattr(part, 'vehicle_make', ''),
            "vehicle_model": getattr(part, 'vehicle_model', ''),
            "year_from": getattr(part, 'year_from', ''),
            "year_to": getattr(part, 'year_to', ''),
            "specifications": getattr(part, 'specifications', ''),
            "min_stock_level": getattr(part, 'min_stock_level', 0),
            "reorder_level": getattr(part, 'reorder_level', 0),
            "stock_info": stock_info,
            "price_info": price_info,
            "cross_references": cross_refs,
            "compatibility": compatibility,
            "suppliers": suppliers
        }

        # Add Arabic translations if requested
        if lang == "ar":
            part_details["item_name_ar"] = get_arabic_translation(part.item_name)
            part_details["description_ar"] = get_arabic_translation(part.description or "")

        # Calculate totals
        total_stock = sum([stock.actual_qty for stock in stock_info])
        primary_price = price_info[0] if price_info else {"price_list_rate": 0, "currency": "SAR"}

        part_details.update({
            "stock_qty": total_stock,
            "price": primary_price["price_list_rate"],
            "currency": primary_price.get("currency", "SAR"),
            "compatible_vehicles": get_part_compatibility_string(part_id)
        })

        return part_details

    except Exception as e:
        frappe.log_error(f"Error getting part details for {part_id}: {str(e)}")
        return {}


@frappe.whitelist()
def add_to_cart(part_id, quantity=1):
    """Add part to shopping cart"""
    try:
        quantity = int(quantity)

        # Validate part exists
        if not frappe.db.exists("Item", part_id):
            return {
                "success": False,
                "message": _("Part not found")
            }

        # Check stock availability
        stock_qty = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_qty), 0) as total_stock
            FROM `tabBin`
            WHERE item_code = %s
        """, part_id)[0][0]

        if stock_qty < quantity:
            return {
                "success": False,
                "message": _("Insufficient stock. Available: {0}").format(stock_qty)
            }

        # Get part details
        part = frappe.get_doc("Item", part_id)
        price = get_item_price(part_id, "Standard Selling")

        # Add to session cart (simplified implementation)
        cart_items = frappe.session.get("cart_items", [])

        # Check if item already in cart
        existing_item = None
        for item in cart_items:
            if item["item_code"] == part_id:
                existing_item = item
                break

        if existing_item:
            existing_item["qty"] += quantity
            existing_item["amount"] = existing_item["qty"] * existing_item["rate"]
        else:
            cart_items.append({
                "item_code": part_id,
                "item_name": part.item_name,
                "qty": quantity,
                "rate": price,
                "amount": price * quantity,
                "stock_uom": part.stock_uom
            })

        frappe.session["cart_items"] = cart_items

        return {
            "success": True,
            "message": _("Part added to cart successfully"),
            "cart_items": len(cart_items),
            "cart_total": sum([item["amount"] for item in cart_items])
        }

    except Exception as e:
        frappe.log_error(f"Error adding part to cart: {str(e)}")
        return {
            "success": False,
            "message": _("Error adding part to cart: {0}").format(str(e))
        }


def get_part_cross_references(item_code, detailed=False):
    """Get cross-reference information for a part"""
    try:
        if not frappe.db.exists("DocType", "Part Cross Reference"):
            return []

        fields = ["manufacturer", "cross_ref_number", "reference_type", "is_primary"]
        if detailed:
            fields.extend(["notes", "verified_date", "created_by"])

        cross_refs = frappe.get_all(
            "Part Cross Reference",
            filters={"parent": item_code},
            fields=fields,
            order_by="is_primary DESC, reference_type, manufacturer"
        )

        return cross_refs

    except Exception as e:
        frappe.log_error(f"Error getting cross references: {str(e)}")
        return []


def get_part_compatibility_string(item_code):
    """Get formatted compatibility string for a part"""
    try:
        part = frappe.get_doc("Item", item_code)

        if not (hasattr(part, 'vehicle_make') and part.vehicle_make):
            return ""

        compatibility_parts = []

        # Build compatibility string
        vehicle_str = part.vehicle_make
        if hasattr(part, 'vehicle_model') and part.vehicle_model:
            vehicle_str += f" {part.vehicle_model}"

        if hasattr(part, 'year_from') and part.year_from:
            if hasattr(part, 'year_to') and part.year_to and part.year_to != part.year_from:
                vehicle_str += f" ({part.year_from}-{part.year_to})"
            else:
                vehicle_str += f" ({part.year_from})"

        compatibility_parts.append(vehicle_str)

        return ", ".join(compatibility_parts)

    except Exception as e:
        frappe.log_error(f"Error getting compatibility string: {str(e)}")
        return ""


def get_part_compatibility_details(item_code):
    """Get detailed compatibility information for a part"""
    try:
        part = frappe.get_doc("Item", item_code)

        compatibility = {
            "make": getattr(part, 'vehicle_make', ''),
            "model": getattr(part, 'vehicle_model', ''),
            "year_from": getattr(part, 'year_from', ''),
            "year_to": getattr(part, 'year_to', ''),
            "engine_type": getattr(part, 'engine_type', ''),
            "transmission": getattr(part, 'transmission_type', '')
        }

        return compatibility

    except Exception as e:
        frappe.log_error(f"Error getting compatibility details: {str(e)}")
        return {}


def get_item_price(item_code, price_list="Standard Selling"):
    """Get item price"""
    try:
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": price_list},
            "price_list_rate"
        )
        return price or 0
    except:
        return 0


def get_arabic_translation(text):
    """Get Arabic translation for common automotive terms"""
    translations = {
        "Engine Parts": "قطع المحرك",
        "Brake System": "نظام الفرامل",
        "Transmission": "ناقل الحركة",
        "Suspension": "نظام التعليق",
        "Electrical": "النظام الكهربائي",
        "Filters": "المرشحات",
        "Oils & Fluids": "الزيوت والسوائل",
        "Body Parts": "قطع الهيكل",
        "Tires": "الإطارات",
        "Battery": "البطارية",
        "Air Filter": "فلتر الهواء",
        "Oil Filter": "فلتر الزيت",
        "Brake Pad": "فحمة الفرامل",
        "Brake Disc": "قرص الفرامل",
        "Spark Plug": "شمعة الإشعال",
        "Engine Oil": "زيت المحرك"
    }
    return translations.get(text, text)


def format_currency(amount, currency="SAR"):
    """Format currency amount"""
    try:
        from frappe.utils import fmt_money
        return fmt_money(amount, currency=currency)
    except:
        return f"{currency} {amount:.2f}"


@frappe.whitelist()
def decode_vehicle_vin(vin):
    """API endpoint for VIN decoding"""
    from .compatibility_matrix import decode_vin
    return decode_vin(vin)


@frappe.whitelist()
def check_part_vehicle_fitment(item_code, vehicle_info, service_context=""):
    """API endpoint for advanced part fitment checking"""
    from .compatibility_matrix import check_part_fitment

    # Parse vehicle_info if it's a string
    if isinstance(vehicle_info, str):
        import json
        vehicle_info = json.loads(vehicle_info)

    return check_part_fitment(item_code, vehicle_info, service_context)


@frappe.whitelist()
def get_vehicle_specifications(make, model, year):
    """Get detailed vehicle specifications for compatibility checking"""
    try:
        # Get vehicle from database
        vehicle_filters = {
            "make": make,
            "model": model,
            "year": year,
            "disabled": 0
        }

        vehicles = frappe.get_list(
            "Vehicle",
            filters=vehicle_filters,
            fields=["*"],
            limit=1
        )

        if not vehicles:
            return {
                "success": False,
                "message": _("Vehicle not found in database"),
                "data": None
            }

        vehicle = vehicles[0]

        # Get compatible parts count by category
        compatible_parts_sql = """
            SELECT
                part_category,
                COUNT(*) as part_count,
                AVG(standard_rate) as avg_price
            FROM `tabItem`
            WHERE vehicle_make = %s
            AND (vehicle_model = %s OR vehicle_model IS NULL)
            AND (
                (vehicle_year_from <= %s AND vehicle_year_to >= %s) OR
                (vehicle_year_from IS NULL AND vehicle_year_to IS NULL)
            )
            AND disabled = 0
            AND is_stock_item = 1
            GROUP BY part_category
            ORDER BY part_count DESC
        """

        compatible_parts_stats = frappe.db.sql(
            compatible_parts_sql,
            (make, model, year, year),
            as_dict=True
        )

        # Get service history if available
        service_history = frappe.db.sql("""
            SELECT
                service_type,
                COUNT(*) as frequency,
                AVG(total_amount) as avg_cost
            FROM `tabService Order`
            WHERE vehicle = %s
            AND docstatus = 1
            GROUP BY service_type
            ORDER BY frequency DESC
            LIMIT 10
        """, (vehicle.get("name", "")), as_dict=True)

        vehicle_specs = {
            "vehicle_info": vehicle,
            "compatible_parts_stats": compatible_parts_stats,
            "service_history": service_history,
            "total_compatible_parts": sum(stat["part_count"] for stat in compatible_parts_stats)
        }

        return {
            "success": True,
            "data": vehicle_specs
        }

    except Exception as e:
        frappe.log_error(f"Vehicle specifications lookup failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to get vehicle specifications"),
            "error": str(e)
        }


@frappe.whitelist()
def get_fitment_recommendations(vehicle_make, vehicle_model, vehicle_year, service_type=""):
    """Get recommended parts with fitment scores for a specific vehicle and service"""
    try:

        # Build base filters for parts search
        base_filters = {
            "disabled": 0,
            "is_stock_item": 1
        }

        # Add vehicle-specific filters
        vehicle_filters = base_filters.copy()
        vehicle_filters.update({
            "vehicle_make": vehicle_make,
            "vehicle_year_from": ("<=", vehicle_year),
            "vehicle_year_to": (">=", vehicle_year)
        })

        # Add service-specific filters if provided
        if service_type:
            service_categories = {
                "oil_change": ["Engine Parts / قطع المحرك", "Filters / المرشحات", "Fluids & Oils / السوائل والزيوت"],
                "brake_service": ["Brake System / نظام الفرامل", "Fluids & Oils / السوائل والزيوت"],
                "engine_repair": ["Engine Parts / قطع المحرك", "Filters / المرشحات", "Belts & Hoses / الأحزمة والخراطيم"],
                "transmission_service": ["Transmission / ناقل الحركة", "Fluids & Oils / السوائل والزيوت"],
                "tire_replacement": ["Tires & Wheels / الإطارات والعجلات"],
                "battery_replacement": ["Battery & Ignition / البطارية والإشعال", "Electrical / النظام الكهربائي"],
                "cooling_service": ["Cooling System / نظام التبريد", "Fluids & Oils / السوائل والزيوت"]
            }

            relevant_categories = service_categories.get(service_type, [])
            if relevant_categories:
                vehicle_filters["part_category"] = ["in", relevant_categories]

        # Get vehicle-specific parts
        vehicle_parts = frappe.get_list(
            "Item",
            filters=vehicle_filters,
            fields=[
                "item_code", "item_name", "brand", "standard_rate",
                "vehicle_make", "vehicle_model", "vehicle_year_from", "vehicle_year_to",
                "part_category", "oem_part_number", "description"
            ],
            limit=50,
            order_by="standard_rate ASC"
        )

        # Get universal parts that might fit
        universal_filters = base_filters.copy()
        universal_filters.update({
            "vehicle_make": ["in", ["", None]],
        })

        if service_type and relevant_categories:
            universal_filters["part_category"] = ["in", relevant_categories]

        universal_parts = frappe.get_list(
            "Item",
            filters=universal_filters,
            fields=[
                "item_code", "item_name", "brand", "standard_rate",
                "part_category", "oem_part_number", "description"
            ],
            limit=20,
            order_by="standard_rate ASC"
        )

        # Combine and evaluate fitment for each part
        all_parts = vehicle_parts + universal_parts
        recommendations = []

        vehicle_info = {
            "make": vehicle_make,
            "model": vehicle_model,
            "year": vehicle_year
        }

        for part in all_parts:
            # Quick fitment check
            fitment_result = check_part_fitment(
                part["item_code"],
                vehicle_info,
                service_type
            )

            if fitment_result.get("success"):
                fitment_data = fitment_result["data"]
                part.update({
                    "fitment_score": fitment_data["confidence_score"],
                    "fitment_status": fitment_data["fitment_status"],
                    "fitment_details": fitment_data["fitment_details"][:2],  # Top 2 details
                    "warnings": fitment_data["warnings"][:1] if fitment_data["warnings"] else []
                })

                # Only include parts with reasonable fitment scores
                if fitment_data["confidence_score"] >= 30:
                    recommendations.append(part)

        # Sort by fitment score and price
        recommendations.sort(key=lambda x: (-x["fitment_score"], x["standard_rate"] or 0))

        # Group by category for better presentation
        categorized_recommendations = {}
        for part in recommendations[:30]:  # Top 30 recommendations
            category = part.get("part_category", "Other")
            if category not in categorized_recommendations:
                categorized_recommendations[category] = []
            categorized_recommendations[category].append(part)

        return {
            "success": True,
            "data": {
                "vehicle_info": vehicle_info,
                "service_type": service_type,
                "total_recommendations": len(recommendations),
                "categorized_parts": categorized_recommendations,
                "top_recommendations": recommendations[:10]
            }
        }

    except Exception as e:
        frappe.log_error(f"Fitment recommendations failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to get fitment recommendations"),
            "error": str(e)
        }
