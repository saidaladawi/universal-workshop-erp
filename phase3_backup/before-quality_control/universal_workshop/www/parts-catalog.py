"""
Parts Catalog Web Page Controller
Handles the backend logic for the parts catalog web interface
"""

import frappe
from frappe import _
import json


def get_context(context):
    """Get context for parts catalog page"""
    context.no_cache = 1
    context.show_sidebar = True
    
    # Set page metadata
    context.title = _("Parts Catalog - Universal Workshop")
    context.description = _("Browse our comprehensive automotive parts catalog with Arabic support")
    
    # Get initial data for filters
    context.categories = get_part_categories()
    context.vehicle_makes = get_vehicle_makes()
    context.brands = get_part_brands()
    
    # Get user preferences
    user = frappe.get_doc("User", frappe.session.user)
    context.preferred_language = getattr(user, 'language', 'en')
    
    # Add theme support
    context.theme_colors = get_theme_colors()
    
    return context


def get_part_categories():
    """Get list of part categories"""
    try:
        categories = frappe.get_all(
            "Item Group",
            filters={"is_group": 0, "disabled": 0},
            fields=["name", "item_group_name"],
            order_by="item_group_name"
        )
        
        # Add translations for common automotive categories
        automotive_categories = []
        for category in categories:
            if any(keyword in category.item_group_name.lower() for keyword in 
                   ['engine', 'brake', 'transmission', 'suspension', 'electrical', 
                    'filter', 'oil', 'body', 'tire', 'battery']):
                automotive_categories.append({
                    'name': category.name,
                    'label': category.item_group_name,
                    'label_ar': get_arabic_translation(category.item_group_name)
                })
        
        return automotive_categories
        
    except Exception as e:
        frappe.log_error(f"Error getting part categories: {str(e)}")
        return []


def get_vehicle_makes():
    """Get list of vehicle makes"""
    try:
        # Try to get from Vehicle doctype if it exists
        if frappe.db.exists("DocType", "Vehicle"):
            makes = frappe.get_all(
                "Vehicle",
                fields=["make"],
                group_by="make",
                order_by="make"
            )
            return [make.make for make in makes if make.make]
        else:
            # Return common vehicle makes
            return [
                "Toyota", "Nissan", "BMW", "Mercedes-Benz", "Audi", 
                "Lexus", "Hyundai", "KIA", "Honda", "Ford", "Chevrolet"
            ]
            
    except Exception as e:
        frappe.log_error(f"Error getting vehicle makes: {str(e)}")
        return []


def get_part_brands():
    """Get list of part brands"""
    try:
        brands = frappe.get_all(
            "Brand",
            filters={"disabled": 0},
            fields=["name", "brand"],
            order_by="brand"
        )
        return [brand.brand for brand in brands if brand.brand]
        
    except Exception as e:
        frappe.log_error(f"Error getting part brands: {str(e)}")
        return []


def get_theme_colors():
    """Get current theme colors"""
    try:
        from universal_workshop.themes.api import get_theme_colors
        return get_theme_colors()
    except Exception as e:
        frappe.log_error(f"Error getting theme colors: {str(e)}")
        return {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "success_color": "#28a745"
        }


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
        "Battery": "البطارية"
    }
    return translations.get(text, text)


@frappe.whitelist()
def get_parts_catalog(search="", category="", make="", price_range="", 
                     stock_status="", page=1, lang="en", limit=20):
    """Get parts catalog data with filters"""
    try:
        page = int(page)
        limit = int(limit)
        offset = (page - 1) * limit
        
        # Build filters
        filters = {"disabled": 0}
        conditions = []
        
        # Search filter
        if search:
            conditions.append("""
                (item_name LIKE %(search)s 
                OR item_code LIKE %(search)s 
                OR description LIKE %(search)s)
            """)
        
        # Category filter
        if category:
            filters["item_group"] = category
        
        # Stock status filter
        if stock_status == "in-stock":
            conditions.append("EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty > 0)")
        elif stock_status == "low-stock":
            conditions.append("EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty <= 5 AND actual_qty > 0)")
        elif stock_status == "out-stock":
            conditions.append("NOT EXISTS (SELECT 1 FROM `tabBin` WHERE item_code = `tabItem`.name AND actual_qty > 0)")
        
        # Build WHERE clause
        where_clause = " AND ".join([f"{k} = %({k})s" for k in filters.keys()])
        if conditions:
            if where_clause:
                where_clause += " AND " + " AND ".join(conditions)
            else:
                where_clause = " AND ".join(conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabItem`
            {"WHERE " + where_clause if where_clause else ""}
        """
        
        count_result = frappe.db.sql(count_query, {
            **filters,
            "search": f"%{search}%" if search else ""
        }, as_dict=True)
        
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
                COALESCE(SUM(b.actual_qty), 0) as stock_qty,
                COALESCE(ip.price_list_rate, 0) as price,
                'SAR' as currency
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            LEFT JOIN `tabItem Price` ip ON ip.item_code = i.name 
                AND ip.price_list = 'Standard Selling'
            {"WHERE " + where_clause if where_clause else ""}
            GROUP BY i.name
            ORDER BY i.item_name
            LIMIT {limit} OFFSET {offset}
        """
        
        parts = frappe.db.sql(parts_query, {
            **filters,
            "search": f"%{search}%" if search else ""
        }, as_dict=True)
        
        # Process parts data
        processed_parts = []
        for part in parts:
            # Add Arabic translations if requested
            if lang == "ar":
                part["item_name_ar"] = get_arabic_translation(part.item_name)
                part["description_ar"] = get_arabic_translation(part.description or "")
            
            # Format price
            part["formatted_price"] = format_currency(part.price or 0, part.currency)
            
            # Add compatibility info if available
            part["compatible_vehicles"] = get_part_compatibility(part.name)
            
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
                projected_qty
            FROM `tabBin`
            WHERE item_code = %s AND actual_qty > 0
        """, part_id, as_dict=True)
        
        # Get price information
        price_info = frappe.db.sql("""
            SELECT 
                price_list,
                price_list_rate,
                currency
            FROM `tabItem Price`
            WHERE item_code = %s
            ORDER BY price_list
        """, part_id, as_dict=True)
        
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
            "specifications": getattr(part, 'specifications', ''),
            "stock_info": stock_info,
            "price_info": price_info,
            "compatible_vehicles": get_part_compatibility(part_id)
        }
        
        # Add Arabic translations if requested
        if lang == "ar":
            part_details["item_name_ar"] = get_arabic_translation(part.item_name)
            part_details["description_ar"] = get_arabic_translation(part.description or "")
        
        # Get total stock and primary price
        total_stock = sum([stock.actual_qty for stock in stock_info])
        primary_price = price_info[0] if price_info else {"price_list_rate": 0, "currency": "SAR"}
        
        part_details.update({
            "stock_qty": total_stock,
            "price": primary_price["price_list_rate"],
            "currency": primary_price.get("currency", "SAR")
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
        
        # Get or create shopping cart
        cart = get_or_create_cart()
        
        # Add item to cart
        existing_item = None
        for item in cart.items:
            if item.item_code == part_id:
                existing_item = item
                break
        
        if existing_item:
            existing_item.qty += quantity
        else:
            part = frappe.get_doc("Item", part_id)
            price = get_item_price(part_id)
            
            cart.append("items", {
                "item_code": part_id,
                "item_name": part.item_name,
                "qty": quantity,
                "rate": price,
                "amount": price * quantity
            })
        
        cart.save()
        
        return {
            "success": True,
            "message": _("Part added to cart successfully"),
            "cart_items": len(cart.items)
        }
        
    except Exception as e:
        frappe.log_error(f"Error adding part to cart: {str(e)}")
        return {
            "success": False,
            "message": _("Error adding part to cart: {0}").format(str(e))
        }


def get_or_create_cart():
    """Get existing cart or create new one"""
    # Check if there's an existing cart for this session
    cart_name = frappe.session.get("shopping_cart")
    
    if cart_name and frappe.db.exists("Shopping Cart", cart_name):
        return frappe.get_doc("Shopping Cart", cart_name)
    else:
        # Create new cart
        cart = frappe.new_doc("Shopping Cart")
        cart.customer = frappe.session.user
        cart.insert()
        frappe.session["shopping_cart"] = cart.name
        return cart


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


def get_part_compatibility(part_id):
    """Get vehicle compatibility information for a part"""
    try:
        # Check if Part Cross Reference exists
        if frappe.db.exists("DocType", "Part Cross Reference"):
            compatibility = frappe.get_all(
                "Part Cross Reference",
                filters={"part_number": part_id},
                fields=["vehicle_make", "vehicle_model", "vehicle_year"],
                limit=10
            )
            
            if compatibility:
                vehicles = []
                for comp in compatibility:
                    vehicle_str = f"{comp.vehicle_make} {comp.vehicle_model}"
                    if comp.vehicle_year:
                        vehicle_str += f" ({comp.vehicle_year})"
                    vehicles.append(vehicle_str)
                return ", ".join(vehicles)
        
        return ""
        
    except Exception as e:
        frappe.log_error(f"Error getting part compatibility: {str(e)}")
        return ""


def format_currency(amount, currency="SAR"):
    """Format currency amount"""
    try:
        from frappe.utils import fmt_money
        return fmt_money(amount, currency=currency)
    except:
        return f"{currency} {amount:.2f}"
