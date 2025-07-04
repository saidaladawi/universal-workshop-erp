import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta

def execute(filters=None):
    """Execute Reorder Level Report"""
    
    if not filters:
        filters = {}
    
    # Get reorder level data
    reorder_data = get_reorder_level_data(filters)
    
    # Prepare columns
    columns = get_columns()
    
    # Prepare data
    data = prepare_data(reorder_data, filters)
    
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
            "fieldname": "item_group",
            "label": _("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 120
        },
        {
            "fieldname": "warehouse",
            "label": _("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 120
        },
        {
            "fieldname": "current_stock",
            "label": _("Current Stock"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "reorder_level",
            "label": _("Reorder Level"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "reorder_qty",
            "label": _("Reorder Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "stock_status",
            "label": _("Stock Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "days_to_stockout",
            "label": _("Days to Stockout"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "avg_daily_consumption",
            "label": _("Avg Daily Consumption"),
            "fieldtype": "Float",
            "width": 150
        },
        {
            "fieldname": "last_purchase_date",
            "label": _("Last Purchase Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "last_purchase_rate",
            "label": _("Last Purchase Rate"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        },
        {
            "fieldname": "stock_value",
            "label": _("Stock Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        }
    ]

def get_reorder_level_data(filters):
    """Get reorder level data from database"""
    
    # Get filters
    warehouse = filters.get('warehouse')
    item_group = filters.get('item_group')
    stock_status = filters.get('stock_status')
    
    # Build conditions
    conditions = ["i.disabled = 0", "i.is_stock_item = 1"]
    params = []
    
    if warehouse:
        conditions.append("sle.warehouse = %s")
        params.append(warehouse)
    
    if item_group:
        conditions.append("i.item_group = %s")
        params.append(item_group)
    
    # Get current stock levels
    stock_data = frappe.db.sql("""
        SELECT 
            i.item_code,
            i.item_name,
            i.item_name_ar,
            i.item_group,
            i.reorder_level,
            i.reorder_qty,
            sle.warehouse,
            SUM(sle.actual_qty) as current_stock,
            SUM(sle.actual_qty * sle.valuation_rate) as stock_value,
            AVG(sle.valuation_rate) as avg_valuation_rate
        FROM `tabItem` i
        LEFT JOIN `tabStock Ledger Entry` sle ON i.item_code = sle.item_code
        WHERE """ + " AND ".join(conditions) + """
        GROUP BY i.item_code, sle.warehouse
        HAVING current_stock IS NOT NULL
        ORDER BY i.item_code, sle.warehouse
    """, params, as_dict=1)
    
    # Get consumption data for last 30 days
    consumption_data = get_consumption_data(filters)
    
    # Get last purchase data
    purchase_data = get_last_purchase_data(filters)
    
    # Process data
    processed_data = []
    
    for stock in stock_data:
        # Get consumption for this item
        consumption = consumption_data.get(stock.item_code, {})
        avg_daily_consumption = consumption.get('avg_daily_consumption', 0)
        
        # Get last purchase for this item
        purchase = purchase_data.get(stock.item_code, {})
        last_purchase_date = purchase.get('last_purchase_date')
        last_purchase_rate = purchase.get('last_purchase_rate', 0)
        
        # Calculate stock status
        stock_status = calculate_stock_status(stock.current_stock, stock.reorder_level, avg_daily_consumption)
        
        # Calculate days to stockout
        days_to_stockout = calculate_days_to_stockout(stock.current_stock, avg_daily_consumption)
        
        processed_data.append({
            "item_code": stock.item_code,
            "item_name": stock.item_name or "",
            "item_name_ar": stock.item_name_ar or "",
            "item_group": stock.item_group,
            "warehouse": stock.warehouse,
            "current_stock": stock.current_stock,
            "reorder_level": stock.reorder_level or 0,
            "reorder_qty": stock.reorder_qty or 0,
            "stock_status": stock_status,
            "days_to_stockout": days_to_stockout,
            "avg_daily_consumption": avg_daily_consumption,
            "last_purchase_date": last_purchase_date,
            "last_purchase_rate": last_purchase_rate,
            "stock_value": stock.stock_value or 0
        })
    
    return processed_data

def get_consumption_data(filters):
    """Get consumption data for last 30 days"""
    
    warehouse = filters.get('warehouse')
    
    # Calculate date range (last 30 days)
    to_date = getdate()
    from_date = to_date - timedelta(days=30)
    
    conditions = ["docstatus = 1", "actual_qty < 0", "posting_date >= %s", "posting_date <= %s"]
    params = [from_date, to_date]
    
    if warehouse:
        conditions.append("warehouse = %s")
        params.append(warehouse)
    
    consumption = frappe.db.sql("""
        SELECT 
            item_code,
            SUM(ABS(actual_qty)) as total_consumption
        FROM `tabStock Ledger Entry`
        WHERE """ + " AND ".join(conditions) + """
        GROUP BY item_code
    """, params, as_dict=1)
    
    # Calculate average daily consumption
    consumption_lookup = {}
    for item in consumption:
        avg_daily = item.total_consumption / 30  # 30 days
        consumption_lookup[item.item_code] = {
            'avg_daily_consumption': avg_daily
        }
    
    return consumption_lookup

def get_last_purchase_data(filters):
    """Get last purchase data for items"""
    
    warehouse = filters.get('warehouse')
    
    conditions = ["docstatus = 1", "actual_qty > 0"]
    params = []
    
    if warehouse:
        conditions.append("warehouse = %s")
        params.append(warehouse)
    
    purchases = frappe.db.sql("""
        SELECT 
            item_code,
            MAX(posting_date) as last_purchase_date,
            AVG(valuation_rate) as last_purchase_rate
        FROM `tabStock Ledger Entry`
        WHERE """ + " AND ".join(conditions) + """
        GROUP BY item_code
    """, params, as_dict=1)
    
    purchase_lookup = {}
    for item in purchases:
        purchase_lookup[item.item_code] = {
            'last_purchase_date': item.last_purchase_date,
            'last_purchase_rate': item.last_purchase_rate
        }
    
    return purchase_lookup

def calculate_stock_status(current_stock, reorder_level, avg_daily_consumption):
    """Calculate stock status"""
    
    if current_stock <= 0:
        return "Out of Stock"
    elif current_stock <= reorder_level:
        return "Below Reorder Level"
    elif avg_daily_consumption > 0 and current_stock / avg_daily_consumption <= 7:
        return "Low Stock"
    else:
        return "Normal"

def calculate_days_to_stockout(current_stock, avg_daily_consumption):
    """Calculate days to stockout"""
    
    if avg_daily_consumption <= 0:
        return 999  # No consumption, won't stockout
    
    days = current_stock / avg_daily_consumption
    return int(days) if days > 0 else 0

def prepare_data(reorder_data, filters):
    """Prepare data for report"""
    
    # Apply stock status filter if specified
    stock_status_filter = filters.get('stock_status')
    if stock_status_filter:
        reorder_data = [item for item in reorder_data if item["stock_status"] == stock_status_filter]
    
    # Sort by stock status priority
    status_priority = {
        "Out of Stock": 1,
        "Below Reorder Level": 2,
        "Low Stock": 3,
        "Normal": 4
    }
    
    reorder_data.sort(key=lambda x: status_priority.get(x["stock_status"], 5))
    
    return reorder_data

def get_chart_data(data):
    """Generate chart data"""
    
    # Group by stock status
    status_data = {}
    for item in data:
        status = item["stock_status"]
        if status not in status_data:
            status_data[status] = {
                "count": 0,
                "total_value": 0
            }
        
        status_data[status]["count"] += 1
        status_data[status]["total_value"] += item["stock_value"]
    
    # Prepare chart data
    chart_data = {
        "data": {
            "labels": list(status_data.keys()),
            "datasets": [
                {
                    "name": "Item Count",
                    "values": [status_data[status]["count"] for status in status_data.keys()]
                },
                {
                    "name": "Stock Value (OMR)",
                    "values": [status_data[status]["total_value"] for status in status_data.keys()]
                }
            ]
        },
        "type": "pie",
        "colors": ["#dc3545", "#ffc107", "#fd7e14", "#28a745"],
        "height": 300
    }
    
    return chart_data 