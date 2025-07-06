# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, date_diff, today
from typing import Dict, List, Optional, Tuple, Any
import json

def execute(filters=None):
    """Main execution function for Vehicle ROI Analysis Report"""
    if not filters:
        filters = {}
        
    # Validate filters
    validate_filters(filters)
    
    # Get columns
    columns = get_columns()
    
    # Get data
    data = get_data(filters)
    
    # Get chart data
    chart = get_chart_data(data)
    
    # Get summary
    summary = get_summary_data(data)
    
    return columns, data, None, chart, summary

def validate_filters(filters: Dict) -> None:
    """Validate report filters"""
    if not filters.get('from_date'):
        filters['from_date'] = frappe.utils.add_months(today(), -1)
        
    if not filters.get('to_date'):
        filters['to_date'] = today()
        
    # Validate date range
    if getdate(filters['from_date']) > getdate(filters['to_date']):
        frappe.throw(_("From Date cannot be greater than To Date"))

def get_columns() -> List[Dict]:
    """Define report columns with Arabic localization"""
    columns = [
        {
            "fieldname": "vehicle_name",
            "fieldtype": "Link",
            "label": _("Vehicle ID") + " | معرف المركبة",
            "options": "Scrap Vehicle",
            "width": 120
        },
        {
            "fieldname": "vehicle_vin",
            "fieldtype": "Data",
            "label": _("VIN") + " | رقم الهيكل",
            "width": 150
        },
        {
            "fieldname": "make",
            "fieldtype": "Data",
            "label": _("Make") + " | الصانع",
            "width": 100
        },
        {
            "fieldname": "model",
            "fieldtype": "Data",
            "label": _("Model") + " | الطراز",
            "width": 120
        },
        {
            "fieldname": "total_investment",
            "fieldtype": "Currency",
            "label": _("Total Investment") + " | إجمالي الاستثمار",
            "options": "currency",
            "width": 140
        },
        {
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "label": _("Total Revenue") + " | إجمالي الإيرادات",
            "options": "currency",
            "width": 130
        },
        {
            "fieldname": "net_profit",
            "fieldtype": "Currency",
            "label": _("Net Profit") + " | صافي الربح",
            "options": "currency",
            "width": 120
        },
        {
            "fieldname": "roi_percentage",
            "fieldtype": "Percent",
            "label": _("ROI %") + " | العائد على الاستثمار %",
            "width": 100
        }
    ]
    
    return columns

def get_data(filters: Dict) -> List[Dict]:
    """Get report data based on filters"""
    
    # Build base query
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            sv.name as vehicle_name,
            sv.vehicle_vin,
            sv.make,
            sv.model,
            sv.total_acquisition_cost as acquisition_cost,
            sv.total_processing_cost as processing_cost,
            sv.total_revenue,
            sv.status
        FROM `tabScrap Vehicle` sv
        WHERE sv.docstatus != 2 {conditions}
        ORDER BY sv.assessment_date DESC
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, filters, as_dict=True)
    
    # Calculate derived fields
    for row in data:
        calculate_derived_metrics(row)
        
    return data

def get_conditions(filters: Dict) -> str:
    """Build SQL conditions based on filters"""
    conditions = []
    
    if filters.get('from_date'):
        conditions.append("sv.assessment_date >= %(from_date)s")
        
    if filters.get('to_date'):
        conditions.append("sv.assessment_date <= %(to_date)s")
        
    return " AND " + " AND ".join(conditions) if conditions else ""

def calculate_derived_metrics(row: Dict) -> None:
    """Calculate derived financial metrics for each vehicle"""
    
    # Calculate total investment
    acquisition_cost = flt(row.get('acquisition_cost', 0))
    processing_cost = flt(row.get('processing_cost', 0))
    row['total_investment'] = acquisition_cost + processing_cost
    
    # Calculate net profit
    total_revenue = flt(row.get('total_revenue', 0))
    row['net_profit'] = total_revenue - row['total_investment']
    
    # Calculate ROI percentage
    if row['total_investment'] > 0:
        row['roi_percentage'] = (row['net_profit'] / row['total_investment']) * 100
    else:
        row['roi_percentage'] = 0

def get_chart_data(data: List[Dict]) -> Dict:
    """Generate chart data for the report"""
    if not data:
        return {}
        
    # ROI Distribution Chart
    roi_ranges = {
        'Profitable (>0%)': 0,
        'Break Even (0%)': 0,
        'Loss Making (<0%)': 0
    }
    
    for row in data:
        roi = flt(row.get('roi_percentage', 0))
        if roi > 0:
            roi_ranges['Profitable (>0%)'] += 1
        elif roi == 0:
            roi_ranges['Break Even (0%)'] += 1
        else:
            roi_ranges['Loss Making (<0%)'] += 1
    
    chart = {
        'data': {
            'labels': list(roi_ranges.keys()),
            'datasets': [
                {
                    'name': _('Vehicle Count'),
                    'values': list(roi_ranges.values())
                }
            ]
        },
        'type': 'donut',
        'height': 300,
        'colors': ['#28a745', '#ffc107', '#dc3545']
    }
    
    return chart

def get_summary_data(data: List[Dict]) -> List[Dict]:
    """Generate summary statistics for the report"""
    if not data:
        return []
        
    total_vehicles = len(data)
    total_investment = sum(flt(row.get('total_investment', 0)) for row in data)
    total_revenue = sum(flt(row.get('total_revenue', 0)) for row in data)
    total_profit = sum(flt(row.get('net_profit', 0)) for row in data)
    
    # Calculate averages
    avg_roi = sum(flt(row.get('roi_percentage', 0)) for row in data) / total_vehicles if total_vehicles > 0 else 0
    
    summary = [
        {
            'label': _('Total Vehicles') + ' | إجمالي المركبات',
            'value': total_vehicles,
            'indicator': 'blue'
        },
        {
            'label': _('Total Investment') + ' | إجمالي الاستثمار',
            'value': f"OMR {total_investment:,.3f}",
            'indicator': 'orange'
        },
        {
            'label': _('Total Revenue') + ' | إجمالي الإيرادات',
            'value': f"OMR {total_revenue:,.3f}",
            'indicator': 'green'
        },
        {
            'label': _('Average ROI') + ' | متوسط العائد',
            'value': f"{avg_roi:.2f}%",
            'indicator': 'green' if avg_roi >= 0 else 'red'
        }
    ]
    
    return summary
