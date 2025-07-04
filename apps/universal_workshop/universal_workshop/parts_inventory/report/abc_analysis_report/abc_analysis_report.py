import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta

def execute(filters=None):
    """Execute ABC Analysis Report"""
    
    if not filters:
        filters = {}
    
    # Get ABC analysis data
    abc_data = get_abc_analysis_data(filters)
    
    # Prepare columns
    columns = get_columns()
    
    # Prepare data
    data = prepare_data(abc_data, filters)
    
    # Get chart data
    chart = get_chart_data(data)
    
    return columns, data, None, chart

def get_columns():
    """Define report columns"""
    return [
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "item_name_ar",
            "label": _("اسم الصنف"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "category",
            "label": _("ABC Category"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "annual_usage_value",
            "label": _("Annual Usage Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150
        },
        {
            "fieldname": "usage_percentage",
            "label": _("Usage %"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "cumulative_percentage",
            "label": _("Cumulative %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "current_stock",
            "label": _("Current Stock"),
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "stock_value",
            "label": _("Stock Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150
        },
        {
            "fieldname": "reorder_level",
            "label": _("Reorder Level"),
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "reorder_qty",
            "label": _("Reorder Qty"),
            "fieldtype": "Float",
            "width": 120
        }
    ]

def get_abc_analysis_data(filters):
    """Get ABC analysis data from database"""
    
    # Get date range
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    warehouse = filters.get('warehouse')
    
    # Build filters
    stock_filters = {"docstatus": 1}
    
    if warehouse:
        stock_filters["warehouse"] = warehouse
    
    if from_date:
        stock_filters["posting_date"] = [">=", from_date]
    
    if to_date:
        if from_date:
            stock_filters["posting_date"][1] = to_date
        else:
            stock_filters["posting_date"] = ["<=", to_date]
    
    # Get stock movement data
    stock_data = frappe.db.sql("""
        SELECT 
            item_code,
            SUM(CASE WHEN actual_qty > 0 THEN actual_qty ELSE 0 END) as usage_qty,
            SUM(CASE WHEN actual_qty > 0 THEN actual_qty * valuation_rate ELSE 0 END) as usage_value
        FROM `tabStock Ledger Entry`
        WHERE docstatus = 1
        AND posting_date BETWEEN %s AND %s
        """ + (" AND warehouse = %s" if warehouse else ""),
        [from_date or '2020-01-01', to_date or getdate(), warehouse] if warehouse else [from_date or '2020-01-01', to_date or getdate()],
        as_dict=1
    )
    
    # Get current stock data
    current_stock = frappe.db.sql("""
        SELECT 
            item_code,
            SUM(actual_qty) as current_qty,
            SUM(actual_qty * valuation_rate) as stock_value
        FROM `tabStock Ledger Entry`
        WHERE docstatus = 1
        GROUP BY item_code
        """, as_dict=1)
    
    # Create stock lookup
    stock_lookup = {item.item_code: item for item in current_stock}
    
    # Get item details
    items = frappe.get_list("Item", 
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["item_code", "item_name", "item_name_ar", "reorder_level", "reorder_qty"]
    )
    
    item_lookup = {item.item_code: item for item in items}
    
    # Process data
    processed_data = []
    total_usage_value = 0
    
    for stock in stock_data:
        if stock.usage_value > 0:
            item_details = item_lookup.get(stock.item_code, {})
            stock_details = stock_lookup.get(stock.item_code, {})
            
            processed_data.append({
                "item_code": stock.item_code,
                "item_name": item_details.get("item_name", ""),
                "item_name_ar": item_details.get("item_name_ar", ""),
                "annual_usage_value": stock.usage_value,
                "current_stock": stock_details.get("current_qty", 0),
                "stock_value": stock_details.get("stock_value", 0),
                "reorder_level": item_details.get("reorder_level", 0),
                "reorder_qty": item_details.get("reorder_qty", 0)
            })
            
            total_usage_value += stock.usage_value
    
    # Sort by usage value (descending)
    processed_data.sort(key=lambda x: x["annual_usage_value"], reverse=True)
    
    # Calculate percentages and categories
    cumulative_value = 0
    for item in processed_data:
        cumulative_value += item["annual_usage_value"]
        item["usage_percentage"] = (item["annual_usage_value"] / total_usage_value * 100) if total_usage_value > 0 else 0
        item["cumulative_percentage"] = (cumulative_value / total_usage_value * 100) if total_usage_value > 0 else 0
        
        # Assign ABC category
        if item["cumulative_percentage"] <= 80:
            item["category"] = "A"
        elif item["cumulative_percentage"] <= 95:
            item["category"] = "B"
        else:
            item["category"] = "C"
    
    return processed_data

def prepare_data(abc_data, filters):
    """Prepare data for report"""
    
    # Apply category filter if specified
    category_filter = filters.get('category')
    if category_filter:
        abc_data = [item for item in abc_data if item["category"] == category_filter]
    
    return abc_data

def get_chart_data(data):
    """Generate chart data"""
    
    # Group by category
    category_data = {}
    for item in data:
        category = item["category"]
        if category not in category_data:
            category_data[category] = {
                "count": 0,
                "total_value": 0
            }
        
        category_data[category]["count"] += 1
        category_data[category]["total_value"] += item["annual_usage_value"]
    
    # Prepare chart data
    chart_data = {
        "data": {
            "labels": list(category_data.keys()),
            "datasets": [
                {
                    "name": "Item Count",
                    "values": [category_data[cat]["count"] for cat in category_data.keys()]
                },
                {
                    "name": "Total Value (OMR)",
                    "values": [category_data[cat]["total_value"] for cat in category_data.keys()]
                }
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff", "#28a745"],
        "height": 300
    }
    
    return chart_data 