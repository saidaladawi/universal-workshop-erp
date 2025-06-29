# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""Help Content Analytics Report"""
	columns = get_columns()
	data = get_data(filters)
	chart_data = get_chart_data(data)
	
	return columns, data, None, chart_data


def get_columns():
	"""Get report columns"""
	return [
		{
			"label": _("Help Content"),
			"fieldname": "help_content",
			"fieldtype": "Link",
			"options": "Help Content",
			"width": 200
		},
		{
			"label": _("Title"),
			"fieldname": "title",
			"fieldtype": "Data",
			"width": 250
		},
		{
			"label": _("Help Type"),
			"fieldname": "help_type",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Priority"),
			"fieldname": "priority",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("View Count"),
			"fieldname": "view_count",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Avg Rating"),
			"fieldname": "helpfulness_rating",
			"fieldtype": "Float",
			"precision": 2,
			"width": 100
		},
		{
			"label": _("Total Feedback"),
			"fieldname": "feedback_count",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("Last Viewed"),
			"fieldname": "last_viewed",
			"fieldtype": "Datetime",
			"width": 150
		},
		{
			"label": _("Created By"),
			"fieldname": "created_by",
			"fieldtype": "Link",
			"options": "User",
			"width": 150
		},
		{
			"label": _("Created On"),
			"fieldname": "created_on",
			"fieldtype": "Datetime",
			"width": 150
		}
	]


def get_data(filters=None):
	"""Get report data"""
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			hc.name as help_content,
			hc.title,
			hc.help_type,
			hc.priority,
			hc.view_count,
			hc.helpfulness_rating,
			COUNT(DISTINCT hcf.name) as feedback_count,
			MAX(hul.timestamp) as last_viewed,
			hc.created_by,
			hc.created_on
		FROM `tabHelp Content` hc
		LEFT JOIN `tabHelp Content Feedback` hcf ON hc.name = hcf.help_content
		LEFT JOIN `tabHelp Usage Log` hul ON hc.name = hul.help_content
		WHERE hc.is_active = 1 {conditions}
		GROUP BY hc.name
		ORDER BY hc.view_count DESC, hc.helpfulness_rating DESC
	""", as_dict=True)
	
	return data


def get_conditions(filters):
	"""Get SQL conditions based on filters"""
	conditions = ""
	
	if filters.get("help_content"):
		conditions += f" AND hc.name = '{filters.get('help_content')}'"
	
	if filters.get("help_type"):
		conditions += f" AND hc.help_type = '{filters.get('help_type')}'"
	
	if filters.get("priority"):
		conditions += f" AND hc.priority = '{filters.get('priority')}'"
	
	if filters.get("from_date"):
		conditions += f" AND hc.created_on >= '{filters.get('from_date')}'"
	
	if filters.get("to_date"):
		conditions += f" AND hc.created_on <= '{filters.get('to_date')}'"
	
	return conditions


def get_chart_data(data):
	"""Get chart data for visualization"""
	if not data:
		return None
	
	# Chart by help type
	help_type_data = {}
	for row in data:
		help_type = row.get('help_type', 'Unknown')
		if help_type not in help_type_data:
			help_type_data[help_type] = {'count': 0, 'views': 0}
		help_type_data[help_type]['count'] += 1
		help_type_data[help_type]['views'] += row.get('view_count', 0)
	
	chart_data = {
		"data": {
			"labels": list(help_type_data.keys()),
			"datasets": [
				{
					"name": _("Content Count"),
					"values": [help_type_data[key]['count'] for key in help_type_data.keys()]
				},
				{
					"name": _("Total Views"),
					"values": [help_type_data[key]['views'] for key in help_type_data.keys()]
				}
			]
		},
		"type": "bar",
		"height": 300
	}
	
	return chart_data
