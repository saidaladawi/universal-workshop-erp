import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta

def execute(filters=None):
    """Execute Stock Movement Report"""
    
    if not filters:
        filters = {}
    
    # Get stock movement data
    movement_data = get_stock_movement_data(filters)
    
    # Prepare columns
    columns = get_columns()
    
    # Prepare data
    data = prepare_data(movement_data, filters)
    
    # Get chart data
    chart = get_chart_data(data)
    
    return columns, data, None, chart

def get_columns():
    """Define report columns"""
    return [
        {
            "fieldname": "posting_date",
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "width": 100
        },
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
            "fieldname": "warehouse",
            "label": _("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 120
        },
        {
            "fieldname": "voucher_type",
            "label": _("Voucher Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 120
        },
        {
            "fieldname": "in_qty",
            "label": _("In Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "out_qty",
            "label": _("Out Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "balance_qty",
            "label": _("Balance Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "in_value",
            "label": _("In Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        },
        {
            "fieldname": "out_value",
            "label": _("Out Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        },
        {
            "fieldname": "balance_value",
            "label": _("Balance Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        },
        {
            "fieldname": "valuation_rate",
            "label": _("Valuation Rate"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120
        }
    ]

def get_stock_movement_data(filters):
    """Get stock movement data from database"""
    
    # Get filters
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    warehouse = filters.get('warehouse')
    item_code = filters.get('item_code')
    item_group = filters.get('item_group')
    
    # Build conditions
    conditions = ["docstatus = 1"]
    params = []
    
    if from_date:
        conditions.append("posting_date >= %s")
        params.append(from_date)
    
    if to_date:
        conditions.append("posting_date <= %s")
        params.append(to_date)
    
    if warehouse:
        conditions.append("warehouse = %s")
        params.append(warehouse)
    
    if item_code:
        conditions.append("item_code = %s")
        params.append(item_code)
    
    # Get stock ledger entries
    stock_entries = frappe.db.sql("""
        SELECT 
            sle.posting_date,
            sle.item_code,
            sle.warehouse,
            sle.voucher_type,
            sle.voucher_no,
            sle.actual_qty,
            sle.valuation_rate,
            sle.qty_after_transaction,
            sle.stock_value_difference,
            i.item_name,
            i.item_name_ar,
            i.item_group
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` i ON sle.item_code = i.item_code
        WHERE """ + " AND ".join(conditions) + """
        ORDER BY sle.posting_date, sle.item_code, sle.warehouse
    """, params, as_dict=1)
    
    # Filter by item group if specified
    if item_group:
        stock_entries = [entry for entry in stock_entries if entry.item_group == item_group]
    
    return stock_entries

def prepare_data(movement_data, filters):
    """Prepare data for report"""
    
    processed_data = []
    
    for entry in movement_data:
        # Calculate in/out quantities
        in_qty = entry.actual_qty if entry.actual_qty > 0 else 0
        out_qty = abs(entry.actual_qty) if entry.actual_qty < 0 else 0
        
        # Calculate values
        in_value = in_qty * entry.valuation_rate if in_qty > 0 else 0
        out_value = out_qty * entry.valuation_rate if out_qty > 0 else 0
        
        processed_data.append({
            "posting_date": entry.posting_date,
            "item_code": entry.item_code,
            "item_name": entry.item_name or "",
            "item_name_ar": entry.item_name_ar or "",
            "warehouse": entry.warehouse,
            "voucher_type": entry.voucher_type,
            "voucher_no": entry.voucher_no,
            "in_qty": in_qty,
            "out_qty": out_qty,
            "balance_qty": entry.qty_after_transaction,
            "in_value": in_value,
            "out_value": out_value,
            "balance_value": entry.qty_after_transaction * entry.valuation_rate,
            "valuation_rate": entry.valuation_rate
        })
    
    return processed_data

def get_chart_data(data):
    """Generate chart data"""
    
    # Group by date
    date_data = {}
    for entry in data:
        date = entry["posting_date"].strftime("%Y-%m-%d") if isinstance(entry["posting_date"], datetime) else str(entry["posting_date"])
        
        if date not in date_data:
            date_data[date] = {
                "in_qty": 0,
                "out_qty": 0,
                "in_value": 0,
                "out_value": 0
            }
        
        date_data[date]["in_qty"] += entry["in_qty"]
        date_data[date]["out_qty"] += entry["out_qty"]
        date_data[date]["in_value"] += entry["in_value"]
        date_data[date]["out_value"] += entry["out_value"]
    
    # Sort by date
    sorted_dates = sorted(date_data.keys())
    
    # Prepare chart data
    chart_data = {
        "data": {
            "labels": sorted_dates,
            "datasets": [
                {
                    "name": "In Quantity",
                    "values": [date_data[date]["in_qty"] for date in sorted_dates]
                },
                {
                    "name": "Out Quantity", 
                    "values": [date_data[date]["out_qty"] for date in sorted_dates]
                }
            ]
        },
        "type": "line",
        "colors": ["#28a745", "#dc3545"],
        "height": 300
    }
    
    return chart_data 