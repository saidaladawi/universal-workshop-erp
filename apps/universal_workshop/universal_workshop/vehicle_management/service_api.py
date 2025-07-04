# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import json
from datetime import datetime, timedelta

import frappe
from frappe import _


@frappe.whitelist()
def get_service_dashboard_data(vehicle=None, customer=None, date_range="30"):
	"""Get comprehensive service dashboard data"""
	try:
		days = int(date_range)
		from_date = datetime.now() - timedelta(days=days)

		filters = {}
		if vehicle:
			filters["vehicle"] = vehicle
		if customer:
			# Get customer's vehicles first
			customer_vehicles = frappe.get_all("Vehicle", filters={"customer": customer}, fields=["name"])
			if customer_vehicles:
				filters["vehicle"] = ["in", [v.name for v in customer_vehicles]]

		# Add date filter
		filters["service_date"] = [">=", from_date]

		# Get service records
		services = frappe.get_all(
			"Service Record",
			filters=filters,
			fields=[
				"name",
				"vehicle",
				"service_date",
				"service_type",
				"service_type_ar",
				"total_cost",
				"status",
				"mileage_at_service",
			],
		)

		# Calculate summary statistics
		total_services = len(services)
		completed_services = len([s for s in services if s.status == "Completed"])
		total_revenue = sum([s.total_cost or 0 for s in services if s.status == "Completed"])
		avg_service_cost = total_revenue / completed_services if completed_services > 0 else 0

		# Service type breakdown
		service_types = {}
		for service in services:
			service_type = service.service_type
			if service_type not in service_types:
				service_types[service_type] = {
					"count": 0,
					"revenue": 0,
					"arabic_name": service.service_type_ar or service_type,
				}
			service_types[service_type]["count"] += 1
			if service.status == "Completed":
				service_types[service_type]["revenue"] += service.total_cost or 0

		# Monthly trend data
		monthly_data = get_monthly_service_trends(filters)

		return {
			"summary": {
				"total_services": total_services,
				"completed_services": completed_services,
				"total_revenue": total_revenue,
				"avg_service_cost": avg_service_cost,
			},
			"service_types": service_types,
			"monthly_trends": monthly_data,
			"recent_services": services[:10],  # Latest 10 services
		}

	except Exception as e:
		frappe.log_error(f"Error in get_service_dashboard_data: {e!s}")
		return {"error": str(e)}


@frappe.whitelist()
def get_vehicle_service_timeline(vehicle):
	"""Get chronological service timeline for a vehicle"""
	try:
		services = frappe.get_all(
			"Service Record",
			filters={"vehicle": vehicle},
			fields=[
				"name",
				"service_date",
				"service_type",
				"service_type_ar",
				"mileage_at_service",
				"total_cost",
				"status",
				"description",
			],
			order_by="service_date desc",
		)

		# Format for timeline display
		timeline_data = []
		for service in services:
			timeline_data.append(
				{
					"date": service.service_date,
					"title": service.service_type_ar if frappe.local.lang == "ar" else service.service_type,
					"subtitle": f"{service.mileage_at_service} KM | OMR {service.total_cost or 0}",
					"status": service.status,
					"description": service.description,
					"link": f"/app/service-record/{service.name}",
				}
			)

		return timeline_data

	except Exception as e:
		frappe.log_error(f"Error in get_vehicle_service_timeline: {e!s}")
		return []


@frappe.whitelist()
def get_service_cost_analysis(vehicle=None, service_type=None, months=6):
	"""Get service cost analysis and trends"""
	try:
		filters = {
			"status": "Completed",
			"service_date": [">=", datetime.now() - timedelta(days=30 * int(months))],
		}

		if vehicle:
			filters["vehicle"] = vehicle
		if service_type:
			filters["service_type"] = service_type

		services = frappe.get_all(
			"Service Record",
			filters=filters,
			fields=["service_date", "total_cost", "labor_cost", "parts_total_cost", "service_type"],
		)

		# Calculate cost trends
		monthly_costs = {}
		for service in services:
			month_key = service.service_date.strftime("%Y-%m")
			if month_key not in monthly_costs:
				monthly_costs[month_key] = {"total": 0, "labor": 0, "parts": 0, "count": 0}
			monthly_costs[month_key]["total"] += service.total_cost or 0
			monthly_costs[month_key]["labor"] += service.labor_cost or 0
			monthly_costs[month_key]["parts"] += service.parts_total_cost or 0
			monthly_costs[month_key]["count"] += 1

		# Service type cost breakdown
		service_type_costs = {}
		for service in services:
			st = service.service_type
			if st not in service_type_costs:
				service_type_costs[st] = {"total": 0, "count": 0, "avg": 0}
			service_type_costs[st]["total"] += service.total_cost or 0
			service_type_costs[st]["count"] += 1
			service_type_costs[st]["avg"] = service_type_costs[st]["total"] / service_type_costs[st]["count"]

		return {
			"monthly_trends": monthly_costs,
			"service_type_breakdown": service_type_costs,
			"total_analyzed": len(services),
		}

	except Exception as e:
		frappe.log_error(f"Error in get_service_cost_analysis: {e!s}")
		return {}


@frappe.whitelist()
def get_upcoming_maintenance_alerts(days_ahead=30):
	"""Get vehicles due for maintenance in the next N days"""
	try:
		future_date = datetime.now() + timedelta(days=int(days_ahead))

		# Get vehicles with next service due date
		vehicles = frappe.get_all(
			"Vehicle",
			filters={"next_service_due": ["<=", future_date], "disabled": 0},
			fields=[
				"name",
				"vin",
				"make",
				"model",
				"year",
				"license_plate",
				"current_mileage",
				"next_service_due",
				"customer",
				"last_service_date",
			],
		)

		alerts = []
		for vehicle in vehicles:
			days_until_due = (vehicle.next_service_due - datetime.now().date()).days

			# Determine alert priority
			if days_until_due <= 0:
				priority = "critical"
				message = "Overdue"
			elif days_until_due <= 7:
				priority = "high"
				message = f"{days_until_due} days remaining"
			elif days_until_due <= 14:
				priority = "medium"
				message = f"{days_until_due} days remaining"
			else:
				priority = "low"
				message = f"{days_until_due} days remaining"

			alerts.append(
				{
					"vehicle_id": vehicle.name,
					"vehicle_display": f"{vehicle.year} {vehicle.make} {vehicle.model}",
					"license_plate": vehicle.license_plate,
					"customer": vehicle.customer,
					"due_date": vehicle.next_service_due,
					"days_until_due": days_until_due,
					"priority": priority,
					"message": message,
					"current_mileage": vehicle.current_mileage,
					"last_service": vehicle.last_service_date,
				}
			)

		# Sort by priority and due date
		priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
		alerts.sort(key=lambda x: (priority_order[x["priority"]], x["days_until_due"]))

		return alerts

	except Exception as e:
		frappe.log_error(f"Error in get_upcoming_maintenance_alerts: {e!s}")
		return []


def get_monthly_service_trends(filters=None):
	"""Get monthly service trends data"""
	try:
		# Get last 12 months of data
		end_date = datetime.now()
		start_date = end_date - timedelta(days=365)

		if filters is None:
			filters = {}
		filters["service_date"] = ["between", [start_date, end_date]]

		services = frappe.get_all(
			"Service Record", filters=filters, fields=["service_date", "total_cost", "status"]
		)

		monthly_data = {}
		for service in services:
			month_key = service.service_date.strftime("%Y-%m")
			if month_key not in monthly_data:
				monthly_data[month_key] = {
					"month": service.service_date.strftime("%b %Y"),
					"total_services": 0,
					"completed_services": 0,
					"revenue": 0,
				}
			monthly_data[month_key]["total_services"] += 1
			if service.status == "Completed":
				monthly_data[month_key]["completed_services"] += 1
				monthly_data[month_key]["revenue"] += service.total_cost or 0

		# Convert to list and sort by month
		return sorted(monthly_data.values(), key=lambda x: x["month"])

	except Exception as e:
		frappe.log_error(f"Error in get_monthly_service_trends: {e!s}")
		return []


@frappe.whitelist()
def create_service_from_template(vehicle, service_template):
	"""Create a new service record from a predefined template"""
	try:
		# This would integrate with a Service Template DocType (future enhancement)
		# For now, create a basic service record

		service_record = frappe.new_doc("Service Record")
		service_record.vehicle = vehicle
		service_record.service_date = datetime.now().date()
		service_record.service_type = service_template
		service_record.status = "Draft"

		# Get vehicle info for mileage
		vehicle_doc = frappe.get_doc("Vehicle", vehicle)
		if vehicle_doc.current_mileage:
			service_record.mileage_at_service = vehicle_doc.current_mileage

		service_record.insert()

		return {
			"success": True,
			"service_record": service_record.name,
			"message": f"Service record {service_record.name} created successfully",
		}

	except Exception as e:
		frappe.log_error(f"Error in create_service_from_template: {e!s}")
		return {"success": False, "error": str(e)}
