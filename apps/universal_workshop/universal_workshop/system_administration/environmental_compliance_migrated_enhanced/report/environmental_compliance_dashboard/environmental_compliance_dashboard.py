# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    charts = get_charts(data)
    summary = get_summary(data)
    
    return columns, data, None, charts, summary


def get_columns():
    """Define report columns with Arabic localization"""
    return [
        {
            "fieldname": "name",
            "label": _("Record ID | معرف السجل"),
            "fieldtype": "Link",
            "options": "Environmental Compliance Record",
            "width": 150
        },
        {
            "fieldname": "compliance_type",
            "label": _("Type | النوع"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status | الحالة"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "compliance_date",
            "label": _("Compliance Date | تاريخ الامتثال"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "due_date",
            "label": _("Due Date | تاريخ الاستحقاق"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "days_to_due",
            "label": _("Days to Due | أيام للاستحقاق"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "regulatory_authority",
            "label": _("Authority | السلطة"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "compliance_percentage",
            "label": _("Compliance % | نسبة الامتثال"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "total_compliance_cost",
            "label": _("Total Cost (OMR) | التكلفة الإجمالية"),
            "fieldtype": "Currency",
            "options": "OMR",
            "width": 130
        },
        {
            "fieldname": "priority",
            "label": _("Priority | الأولوية"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "next_monitoring_due",
            "label": _("Next Monitoring | المراقبة التالية"),
            "fieldtype": "Date",
            "width": 130
        },
        {
            "fieldname": "critical_issues",
            "label": _("Critical Issues | القضايا الحرجة"),
            "fieldtype": "Int",
            "width": 120
        }
    ]


def get_data(filters):
    """Get compliance data with calculated fields"""
    
    # Build conditions based on filters
    conditions = []
    if filters.get("from_date"):
        conditions.append(f"compliance_date >= '{filters.get('from_date')}'")
    if filters.get("to_date"):
        conditions.append(f"compliance_date <= '{filters.get('to_date')}'")
    if filters.get("compliance_type"):
        conditions.append(f"compliance_type = '{filters.get('compliance_type')}'")
    if filters.get("status"):
        conditions.append(f"status = '{filters.get('status')}'")
    if filters.get("priority"):
        conditions.append(f"priority = '{filters.get('priority')}'")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Get base compliance data
    query = f"""
        SELECT 
            name,
            compliance_type,
            status,
            compliance_date,
            due_date,
            regulatory_authority,
            total_compliance_cost,
            priority,
            next_monitoring_due,
            location_compliance,
            license_valid,
            documentation_complete,
            waste_properly_segregated,
            hazardous_materials_handled,
            spill_containment_in_place,
            pollution_prevention_active,
            staff_trained
        FROM `tabEnvironmental Compliance Record`
        {where_clause}
        ORDER BY compliance_date DESC
    """
    
    data = frappe.db.sql(query, as_dict=True)
    
    # Calculate additional fields
    today = datetime.now().date()
    
    for row in data:
        # Calculate days to due
        if row.due_date:
            due_date = row.due_date
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            row['days_to_due'] = (due_date - today).days
        else:
            row['days_to_due'] = None
            
        # Calculate compliance percentage
        checklist_fields = [
            'location_compliance', 'license_valid', 'documentation_complete',
            'waste_properly_segregated', 'hazardous_materials_handled',
            'spill_containment_in_place', 'pollution_prevention_active', 'staff_trained'
        ]
        
        total_checks = len(checklist_fields)
        passed_checks = sum(1 for field in checklist_fields if row.get(field))
        row['compliance_percentage'] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Count critical issues
        critical_checks = ['location_compliance', 'license_valid', 'documentation_complete']
        row['critical_issues'] = sum(1 for field in critical_checks if not row.get(field))
        
        # Clean up fields not needed in output
        for field in checklist_fields:
            if field in row:
                del row[field]
    
    return data


def get_charts(data):
    """Generate charts for the dashboard"""
    
    if not data:
        return []
    
    # Chart 1: Compliance Status Distribution
    status_data = {}
    for row in data:
        status = row.get('status', 'Unknown')
        status_data[status] = status_data.get(status, 0) + 1
    
    status_chart = {
        "data": {
            "labels": list(status_data.keys()),
            "datasets": [{
                "name": "Compliance Records",
                "values": list(status_data.values())
            }]
        },
        "type": "donut",
        "height": 300,
        "title": "Compliance Status Distribution | توزيع حالة الامتثال"
    }
    
    # Chart 2: Compliance Type Distribution
    type_data = {}
    for row in data:
        comp_type = row.get('compliance_type', 'Unknown')
        type_data[comp_type] = type_data.get(comp_type, 0) + 1
    
    type_chart = {
        "data": {
            "labels": list(type_data.keys()),
            "datasets": [{
                "name": "Records",
                "values": list(type_data.values())
            }]
        },
        "type": "bar",
        "height": 300,
        "title": "Compliance by Type | الامتثال حسب النوع"
    }
    
    # Chart 3: Compliance Percentage Trend
    compliance_trend = {}
    for row in data:
        if row.get('compliance_date'):
            date_key = row['compliance_date'].strftime('%Y-%m') if hasattr(row['compliance_date'], 'strftime') else str(row['compliance_date'])[:7]
            if date_key not in compliance_trend:
                compliance_trend[date_key] = []
            compliance_trend[date_key].append(row.get('compliance_percentage', 0))
    
    # Calculate average compliance percentage per month
    trend_labels = sorted(compliance_trend.keys())
    trend_values = [sum(compliance_trend[month]) / len(compliance_trend[month]) for month in trend_labels]
    
    trend_chart = {
        "data": {
            "labels": trend_labels,
            "datasets": [{
                "name": "Average Compliance %",
                "values": trend_values
            }]
        },
        "type": "line",
        "height": 300,
        "title": "Compliance Percentage Trend | اتجاه نسبة الامتثال"
    }
    
    # Chart 4: Cost Analysis
    cost_by_type = {}
    for row in data:
        comp_type = row.get('compliance_type', 'Unknown')
        cost = row.get('total_compliance_cost', 0) or 0
        cost_by_type[comp_type] = cost_by_type.get(comp_type, 0) + cost
    
    cost_chart = {
        "data": {
            "labels": list(cost_by_type.keys()),
            "datasets": [{
                "name": "Total Cost (OMR)",
                "values": list(cost_by_type.values())
            }]
        },
        "type": "bar",
        "height": 300,
        "title": "Compliance Cost by Type | تكلفة الامتثال حسب النوع"
    }
    
    return [status_chart, type_chart, trend_chart, cost_chart]


def get_summary(data):
    """Generate summary statistics"""
    
    if not data:
        return []
    
    total_records = len(data)
    compliant_records = len([r for r in data if r.get('status') == 'Compliant'])
    overdue_records = len([r for r in data if r.get('days_to_due', 0) < 0])
    critical_issues = sum(r.get('critical_issues', 0) for r in data)
    total_cost = sum(r.get('total_compliance_cost', 0) or 0 for r in data)
    avg_compliance = sum(r.get('compliance_percentage', 0) for r in data) / total_records if total_records > 0 else 0
    
    # Upcoming due in next 30 days
    upcoming_due = len([r for r in data if 0 <= r.get('days_to_due', -1) <= 30])
    
    return [
        {
            "value": total_records,
            "label": _("Total Records | إجمالي السجلات"),
            "datatype": "Int"
        },
        {
            "value": compliant_records,
            "label": _("Compliant Records | السجلات المطابقة"),
            "datatype": "Int"
        },
        {
            "value": f"{(compliant_records / total_records * 100):.1f}%" if total_records > 0 else "0%",
            "label": _("Compliance Rate | معدل الامتثال"),
            "datatype": "Data"
        },
        {
            "value": overdue_records,
            "label": _("Overdue Records | السجلات المتأخرة"),
            "datatype": "Int"
        },
        {
            "value": upcoming_due,
            "label": _("Due in 30 Days | مستحقة خلال 30 يوم"),
            "datatype": "Int"
        },
        {
            "value": critical_issues,
            "label": _("Critical Issues | القضايا الحرجة"),
            "datatype": "Int"
        },
        {
            "value": total_cost,
            "label": _("Total Cost (OMR) | إجمالي التكلفة"),
            "datatype": "Currency"
        },
        {
            "value": f"{avg_compliance:.1f}%",
            "label": _("Average Compliance | متوسط الامتثال"),
            "datatype": "Data"
        }
    ]


def get_filters():
    """Define report filters"""
    return [
        {
            "fieldname": "from_date",
            "label": _("From Date"),
            "fieldtype": "Date",
            "default": frappe.utils.add_months(frappe.utils.today(), -3)
        },
        {
            "fieldname": "to_date",
            "label": _("To Date"),
            "fieldtype": "Date",
            "default": frappe.utils.today()
        },
        {
            "fieldname": "compliance_type",
            "label": _("Compliance Type"),
            "fieldtype": "Select",
            "options": "\nVehicle Processing\nWaste Disposal\nHazardous Material\nEnvironmental Audit\nLicense Renewal\nRegulatory Submission\nInspection Report\nCertification"
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Select",
            "options": "\nDraft\nPending Review\nUnder Investigation\nCompliant\nNon-Compliant\nOverdue\nClosed"
        },
        {
            "fieldname": "priority",
            "label": _("Priority"),
            "fieldtype": "Select",
            "options": "\nLow\nMedium\nHigh\nCritical"
        }
    ]
