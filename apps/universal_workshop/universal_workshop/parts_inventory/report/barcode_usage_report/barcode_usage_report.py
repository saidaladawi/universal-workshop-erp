import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta

def execute(filters=None):
    """Execute Barcode Usage Report"""
    
    if not filters:
        filters = {}
    
    # Get barcode usage data
    barcode_data = get_barcode_usage_data(filters)
    
    # Prepare columns
    columns = get_columns()
    
    # Prepare data
    data = prepare_data(barcode_data, filters)
    
    # Get chart data
    chart = get_chart_data(data)
    
    return columns, data, None, chart

def get_columns():
    """Define report columns"""
    return [
        {
            "fieldname": "barcode",
            "label": _("Barcode"),
            "fieldtype": "Data",
            "width": 150
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
            "fieldname": "barcode_type",
            "label": _("Barcode Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "scan_count",
            "label": _("Scan Count"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "last_scan_date",
            "label": _("Last Scan Date"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "first_scan_date",
            "label": _("First Scan Date"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "scanned_by",
            "label": _("Scanned By"),
            "fieldtype": "Link",
            "options": "User",
            "width": 120
        },
        {
            "fieldname": "scan_location",
            "label": _("Scan Location"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "scan_purpose",
            "label": _("Scan Purpose"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "success_rate",
            "label": _("Success Rate (%)"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "error_count",
            "label": _("Error Count"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "avg_scan_time",
            "label": _("Avg Scan Time (s)"),
            "fieldtype": "Float",
            "width": 120
        }
    ]

def get_barcode_usage_data(filters):
    """Get barcode usage data from database"""
    
    # Get filters
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    barcode_type = filters.get('barcode_type')
    scan_purpose = filters.get('scan_purpose')
    item_code = filters.get('item_code')
    
    # Build conditions
    conditions = ["docstatus = 1"]
    params = []
    
    if from_date:
        conditions.append("scan_timestamp >= %s")
        params.append(from_date)
    
    if to_date:
        conditions.append("scan_timestamp <= %s")
        params.append(to_date)
    
    if barcode_type:
        conditions.append("barcode_type = %s")
        params.append(barcode_type)
    
    if scan_purpose:
        conditions.append("scan_purpose = %s")
        params.append(scan_purpose)
    
    if item_code:
        conditions.append("item_code = %s")
        params.append(item_code)
    
    # Get barcode scan data
    scan_data = frappe.db.sql("""
        SELECT 
            bs.barcode,
            bs.item_code,
            bs.barcode_type,
            bs.scan_timestamp,
            bs.scanned_by,
            bs.scan_location,
            bs.scan_purpose,
            bs.scan_success,
            bs.scan_duration,
            bs.error_message,
            i.item_name,
            i.item_name_ar
        FROM `tabBarcode Scanner` bs
        LEFT JOIN `tabItem` i ON bs.item_code = i.item_code
        WHERE """ + " AND ".join(conditions) + """
        ORDER BY bs.scan_timestamp DESC
    """, params, as_dict=1)
    
    return scan_data

def prepare_data(barcode_data, filters):
    """Prepare data for report"""
    
    # Group by barcode
    barcode_groups = {}
    
    for scan in barcode_data:
        barcode = scan.barcode
        
        if barcode not in barcode_groups:
            barcode_groups[barcode] = {
                "barcode": barcode,
                "item_code": scan.item_code,
                "item_name": scan.item_name or "",
                "item_name_ar": scan.item_name_ar or "",
                "barcode_type": scan.barcode_type,
                "scan_count": 0,
                "success_count": 0,
                "error_count": 0,
                "scan_times": [],
                "first_scan_date": None,
                "last_scan_date": None,
                "scanned_by": scan.scanned_by,
                "scan_location": scan.scan_location,
                "scan_purpose": scan.scan_purpose
            }
        
        group = barcode_groups[barcode]
        group["scan_count"] += 1
        
        if scan.scan_success:
            group["success_count"] += 1
        else:
            group["error_count"] += 1
        
        if scan.scan_duration:
            group["scan_times"].append(scan.scan_duration)
        
        # Update first and last scan dates
        scan_date = scan.scan_timestamp
        if not group["first_scan_date"] or scan_date < group["first_scan_date"]:
            group["first_scan_date"] = scan_date
        
        if not group["last_scan_date"] or scan_date > group["last_scan_date"]:
            group["last_scan_date"] = scan_date
    
    # Calculate derived fields
    processed_data = []
    
    for barcode, group in barcode_groups.items():
        # Calculate success rate
        success_rate = (group["success_count"] / group["scan_count"] * 100) if group["scan_count"] > 0 else 0
        
        # Calculate average scan time
        avg_scan_time = sum(group["scan_times"]) / len(group["scan_times"]) if group["scan_times"] else 0
        
        processed_data.append({
            "barcode": group["barcode"],
            "item_code": group["item_code"],
            "item_name": group["item_name"],
            "item_name_ar": group["item_name_ar"],
            "barcode_type": group["barcode_type"],
            "scan_count": group["scan_count"],
            "last_scan_date": group["last_scan_date"],
            "first_scan_date": group["first_scan_date"],
            "scanned_by": group["scanned_by"],
            "scan_location": group["scan_location"],
            "scan_purpose": group["scan_purpose"],
            "success_rate": success_rate,
            "error_count": group["error_count"],
            "avg_scan_time": avg_scan_time
        })
    
    # Sort by scan count (descending)
    processed_data.sort(key=lambda x: x["scan_count"], reverse=True)
    
    return processed_data

def get_chart_data(data):
    """Generate chart data"""
    
    # Group by barcode type
    type_data = {}
    for item in data:
        barcode_type = item["barcode_type"] or "Unknown"
        
        if barcode_type not in type_data:
            type_data[barcode_type] = {
                "count": 0,
                "total_scans": 0,
                "avg_success_rate": 0
            }
        
        type_data[barcode_type]["count"] += 1
        type_data[barcode_type]["total_scans"] += item["scan_count"]
        type_data[barcode_type]["avg_success_rate"] += item["success_rate"]
    
    # Calculate averages
    for barcode_type in type_data:
        if type_data[barcode_type]["count"] > 0:
            type_data[barcode_type]["avg_success_rate"] /= type_data[barcode_type]["count"]
    
    # Prepare chart data
    chart_data = {
        "data": {
            "labels": list(type_data.keys()),
            "datasets": [
                {
                    "name": "Barcode Count",
                    "values": [type_data[bt]["count"] for bt in type_data.keys()]
                },
                {
                    "name": "Total Scans",
                    "values": [type_data[bt]["total_scans"] for bt in type_data.keys()]
                },
                {
                    "name": "Avg Success Rate (%)",
                    "values": [type_data[bt]["avg_success_rate"] for bt in type_data.keys()]
                }
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff", "#28a745", "#ffc107"],
        "height": 300
    }
    
    return chart_data 