# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime


class CustomerAPI:
	"""Customer management API class"""

	def search_customers(self, query, language="both", limit=20):
		"""Advanced customer search supporting Arabic and English"""
		try:
			search_fields = ["name", "customer_name"]

			# Add Arabic search if available
			if language in ["arabic", "both"]:
				search_fields.append("customer_name_ar")

			# Build search conditions
			conditions = []
			for field in search_fields:
				conditions.append(f"`{field}` LIKE %(query)s")

			where_clause = " OR ".join(conditions)

			# Execute search query
			customers = frappe.db.sql(
				f"""
                SELECT name, customer_name, customer_name_ar, mobile_no, email_id
                FROM `tabCustomer`
                WHERE ({where_clause}) AND disabled = 0
                ORDER BY customer_name
                LIMIT %(limit)s
            """,
				{"query": f"%{query}%", "limit": limit},
				as_dict=True,
			)

			return {
				"success": True,
				"customers": customers or [],
				"total": len(customers) if customers else 0,
			}

		except Exception as e:
			frappe.log_error(f"Customer search failed: {e!s}")
			return {"success": False, "error": str(e), "customers": []}

	def get_customer_details(self, customer_id, include_vehicles=True, include_history=True):
		"""Get comprehensive customer details"""
		try:
			# Get customer basic info
			customer = frappe.get_doc("Customer", customer_id)

			customer_data = {
				"name": customer.name,
				"customer_name": getattr(customer, "customer_name", ""),
				"customer_name_ar": getattr(customer, "customer_name_ar", ""),
				"email_id": getattr(customer, "email_id", ""),
				"mobile_no": getattr(customer, "mobile_no", ""),
				"civil_id": getattr(customer, "civil_id", ""),
				"nationality": getattr(customer, "nationality", ""),
				"preferred_language": getattr(customer, "preferred_language", "English"),
				"customer_status": getattr(customer, "customer_status", "Active"),
				"creation": str(customer.creation) if customer.creation else None,
			}

			# Add vehicles if requested
			if include_vehicles:
				customer_data["vehicles"] = self._get_customer_vehicles(customer_id)

			# Add service history if requested
			if include_history:
				customer_data["service_history"] = self._get_customer_service_history(customer_id)
				customer_data["loyalty_points"] = self._get_customer_loyalty_points(customer_id)

			return {"success": True, "customer": customer_data}

		except Exception as e:
			frappe.log_error(f"Failed to get customer details for {customer_id}: {e!s}")
			return {"success": False, "error": str(e)}

	def _get_customer_vehicles(self, customer_id):
		"""Get customer's vehicles"""
		try:
			vehicles = frappe.db.sql(
				"""
                SELECT v.name, v.vin, v.license_plate, v.license_plate_ar,
                       v.make, v.model, v.year, v.color, v.color_ar
                FROM `tabVehicle` v
                WHERE v.customer = %(customer)s
                ORDER BY v.creation DESC
            """,
				{"customer": customer_id},
				as_dict=True,
			)

			return vehicles or []

		except Exception as e:
			frappe.log_error(f"Failed to get vehicles for customer {customer_id}: {e!s}")
			return []

	def _get_customer_service_history(self, customer_id, limit=10):
		"""Get customer's recent service history"""
		try:
			services = frappe.db.sql(
				"""
                SELECT si.name, si.posting_date, si.grand_total, si.status,
                       si.remarks, si.vehicle_vin
                FROM `tabSales Invoice` si
                WHERE si.customer = %(customer)s AND si.docstatus = 1
                ORDER BY si.posting_date DESC
                LIMIT %(limit)s
            """,
				{"customer": customer_id, "limit": limit},
				as_dict=True,
			)

			return services or []

		except Exception as e:
			frappe.log_error(f"Failed to get service history for customer {customer_id}: {e!s}")
			return []

	def _get_customer_loyalty_points(self, customer_id):
		"""Get customer's loyalty points summary"""
		try:
			# Get total active points
			total_points = frappe.db.sql(
				"""
                SELECT COALESCE(SUM(points_value), 0) as total
                FROM `tabCustomer Loyalty Points`
                WHERE customer = %(customer)s AND points_value > 0
                AND (expiry_date IS NULL OR expiry_date > CURDATE())
            """,
				{"customer": customer_id},
				as_dict=True,
			)

			total_value = 0
			if total_points and len(total_points) > 0:
				total_value = total_points[0].get("total", 0)

			# Get recent transactions
			recent_transactions = frappe.db.sql(
				"""
                SELECT transaction_type, points_value, posting_date, invoice_reference
                FROM `tabCustomer Loyalty Points`
                WHERE customer = %(customer)s
                ORDER BY posting_date DESC
                LIMIT 5
            """,
				{"customer": customer_id},
				as_dict=True,
			)

			return {"total_points": float(total_value), "recent_transactions": recent_transactions or []}

		except Exception as e:
			frappe.log_error(f"Failed to get loyalty points for customer {customer_id}: {e!s}")
			return {"total_points": 0, "recent_transactions": []}

	def create_customer(self, customer_data):
		"""Create a new customer with validation"""
		try:
			# Validate required fields
			if not customer_data.get("customer_name"):
				return {"success": False, "error": "Missing required field: customer_name"}

			# Create customer document
			customer = frappe.new_doc("Customer")

			# Set basic fields
			customer.customer_name = customer_data.get("customer_name")
			customer.customer_type = customer_data.get("customer_type", "Individual")
			customer.customer_group = customer_data.get("customer_group", "Commercial")

			# Set optional fields
			optional_fields = [
				"customer_name_ar",
				"email_id",
				"mobile_no",
				"civil_id",
				"nationality",
				"preferred_language",
				"emergency_contact",
			]

			for field in optional_fields:
				if customer_data.get(field):
					setattr(customer, field, customer_data[field])

			# Save customer
			customer.insert()

			return {
				"success": True,
				"customer_id": customer.name,
				"message": _("Customer created successfully"),
			}

		except Exception as e:
			frappe.log_error(f"Customer creation failed: {e!s}")
			return {"success": False, "error": str(e)}

	def update_customer(self, customer_id, update_data):
		"""Update existing customer"""
		try:
			customer = frappe.get_doc("Customer", customer_id)

			# Update allowed fields
			allowed_fields = [
				"customer_name",
				"customer_name_ar",
				"email_id",
				"mobile_no",
				"civil_id",
				"nationality",
				"preferred_language",
				"emergency_contact",
			]

			for field in allowed_fields:
				if field in update_data:
					setattr(customer, field, update_data[field])

			customer.save()

			return {"success": True, "message": _("Customer updated successfully")}

		except Exception as e:
			frappe.log_error(f"Customer update failed: {e!s}")
			return {"success": False, "error": str(e)}

	def get_customer_analytics(self, customer_id):
		"""Get comprehensive customer analytics data"""
		try:
			# Get latest analytics record
			latest_analytics = frappe.db.sql(
				"""
                SELECT *
                FROM `tabCustomer Analytics`
                WHERE customer = %s
                ORDER BY calculation_date DESC
                LIMIT 1
            """,
				(customer_id,),
				as_dict=True,
			)

			if not latest_analytics:
				# Create analytics if doesn't exist
				from universal_workshop.customer_management.doctype.customer_analytics.customer_analytics import (
					CustomerAnalytics,
				)

				analytics_doc = CustomerAnalytics.create_analytics_for_customer(customer_id)
				if analytics_doc:
					latest_analytics = [analytics_doc.as_dict()]
				else:
					return {"success": False, "error": "Failed to generate analytics"}

			analytics_data = latest_analytics[0]

			# Get customer service timeline
			service_timeline = frappe.db.sql(
				"""
                SELECT
                    posting_date,
                    grand_total,
                    status,
                    vehicle_vin
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1
                ORDER BY posting_date DESC
                LIMIT 12
            """,
				(customer_id,),
				as_dict=True,
			)

			# Calculate monthly revenue trend
			monthly_revenue = frappe.db.sql(
				"""
                SELECT
                    DATE_FORMAT(posting_date, '%%Y-%%m') as month,
                    SUM(grand_total) as revenue,
                    COUNT(*) as transaction_count
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
                ORDER BY month DESC
            """,
				(customer_id,),
				as_dict=True,
			)

			# Get customer vehicles with service counts
			vehicles_data = frappe.db.sql(
				"""
                SELECT
                    v.name,
                    v.vin,
                    v.license_plate,
                    v.make,
                    v.model,
                    v.year,
                    COUNT(si.name) as service_count,
                    MAX(si.posting_date) as last_service_date
                FROM `tabVehicle` v
                LEFT JOIN `tabSales Invoice` si ON si.vehicle_vin = v.vin AND si.docstatus = 1
                WHERE v.customer = %s
                GROUP BY v.name
                ORDER BY service_count DESC
            """,
				(customer_id,),
				as_dict=True,
			)

			return {
				"success": True,
				"analytics": analytics_data,
				"service_timeline": service_timeline or [],
				"monthly_revenue": monthly_revenue or [],
				"vehicles": vehicles_data or [],
				"last_updated": analytics_data.get("calculation_date"),
			}

		except Exception as e:
			frappe.log_error(f"Error getting customer analytics for {customer_id}: {e!s}")
			return {"success": False, "error": str(e)}


# Create global instance
customer_api = CustomerAPI()


# Standalone API functions for whitelist
@frappe.whitelist()
def search_customers(query, language="both", limit=20):
	"""Search customers by name"""
	return customer_api.search_customers(query, language, limit)


@frappe.whitelist()
def get_customer_details(customer_id, include_vehicles=True, include_history=True):
	"""Get customer details"""
	return customer_api.get_customer_details(customer_id, include_vehicles, include_history)


@frappe.whitelist()
def create_customer(customer_data):
	"""Create a new customer"""
	try:
		data = json.loads(customer_data) if isinstance(customer_data, str) else customer_data
		return customer_api.create_customer(data)
	except json.JSONDecodeError:
		return {"success": False, "error": "Invalid JSON data"}


@frappe.whitelist()
def update_customer(customer_id, update_data):
	"""Update customer"""
	try:
		data = json.loads(update_data) if isinstance(update_data, str) else update_data
		return customer_api.update_customer(customer_id, data)
	except json.JSONDecodeError:
		return {"success": False, "error": "Invalid JSON data"}


@frappe.whitelist()
def get_customer_analytics(customer_id):
	"""Get customer analytics"""
	return customer_api.get_customer_analytics(customer_id)


@frappe.whitelist()
def create_customer_communication(customer_name, communication_type, subject, summary, direction="Outgoing"):
	"""Create customer communication entry"""
	try:
		customer = frappe.get_doc("Customer", customer_name)

		# Add to communication history
		if hasattr(customer, "communication_history"):
			customer.append(
				"communication_history",
				{
					"communication_date": now_datetime(),
					"communication_type": communication_type,
					"direction": direction,
					"subject": subject,
					"summary": summary,
					"user": frappe.session.user,
				},
			)

			customer.save(ignore_permissions=True)

		return {"success": True, "message": _("Communication entry created successfully")}

	except Exception as e:
		frappe.log_error(f"Error creating communication for {customer_name}: {e!s}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_customers_by_vehicle(license_plate=None, make=None, model=None):
	"""Find customers by vehicle information"""
	try:
		conditions = []
		values = {}

		if license_plate:
			conditions.append("v.license_plate LIKE %(license_plate)s")
			values["license_plate"] = f"%{license_plate}%"

		if make:
			conditions.append("v.make LIKE %(make)s")
			values["make"] = f"%{make}%"

		if model:
			conditions.append("v.model LIKE %(model)s")
			values["model"] = f"%{model}%"

		if not conditions:
			return {"success": False, "error": "At least one vehicle parameter required"}

		sql_query = f"""
            SELECT DISTINCT
                c.name,
                c.customer_name,
                c.customer_name_ar,
                c.preferred_language,
                c.mobile_no,
                v.license_plate,
                v.make,
                v.model,
                vo.ownership_type,
                vo.primary_vehicle
            FROM `tabCustomer` c
            JOIN `tabCustomer Vehicle Ownership` vo ON vo.parent = c.name
            JOIN `tabVehicle` v ON v.name = vo.vehicle
            WHERE c.disabled = 0
            AND {" AND ".join(conditions)}
            ORDER BY c.customer_name
        """

		results = frappe.db.sql(sql_query, values, as_dict=True)

		return {"success": True, "customers": results or [], "total_found": len(results) if results else 0}

	except Exception as e:
		frappe.log_error(f"Error searching customers by vehicle: {e!s}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_customer_dashboard_data(date_range="30"):
	"""Get customer dashboard analytics data"""
	try:
		days = int(date_range)
		from_date = datetime.now() - timedelta(days=days)

		# New customers in period
		new_customers_result = frappe.db.sql(
			"""
            SELECT COUNT(*) as count
            FROM `tabCustomer`
            WHERE creation >= %s AND disabled = 0
        """,
			(from_date,),
			as_dict=True,
		)

		new_customers = 0
		if new_customers_result and len(new_customers_result) > 0:
			new_customers = int(new_customers_result[0].get("count", 0))

		# Total active customers
		total_customers_result = frappe.db.sql(
			"""
            SELECT COUNT(*) as count
            FROM `tabCustomer`
            WHERE disabled = 0
        """,
			as_dict=True,
		)

		total_customers = 0
		if total_customers_result and len(total_customers_result) > 0:
			total_customers = int(total_customers_result[0].get("count", 0))

		# Customer status distribution
		status_distribution = frappe.db.sql(
			"""
            SELECT
                customer_status,
                COUNT(*) as count
            FROM `tabCustomer`
            WHERE disabled = 0
            GROUP BY customer_status
        """,
			as_dict=True,
		)

		# Top customers by lifetime value
		top_customers = frappe.db.sql(
			"""
            SELECT
                customer_name,
                customer_name_ar,
                customer_lifetime_value,
                total_services_count
            FROM `tabCustomer`
            WHERE disabled = 0 AND customer_lifetime_value > 0
            ORDER BY customer_lifetime_value DESC
            LIMIT 10
        """,
			as_dict=True,
		)

		# Recent service activity
		recent_activity = frappe.db.sql(
			"""
            SELECT
                c.customer_name,
                c.customer_name_ar,
                si.posting_date,
                si.grand_total
            FROM `tabSales Invoice` si
            JOIN `tabCustomer` c ON c.name = si.customer
            WHERE si.docstatus = 1 AND si.posting_date >= %s
            ORDER BY si.posting_date DESC
            LIMIT 20
        """,
			(from_date,),
			as_dict=True,
		)

		# Calculate growth rate safely
		growth_rate = 0.0
		if total_customers > new_customers and new_customers > 0:
			growth_rate = (new_customers / max(total_customers - new_customers, 1)) * 100

		return {
			"success": True,
			"summary": {
				"new_customers": new_customers,
				"total_customers": total_customers,
				"growth_rate": growth_rate,
			},
			"status_distribution": status_distribution or [],
			"top_customers": top_customers or [],
			"recent_activity": recent_activity or [],
		}

	except Exception as e:
		frappe.log_error(f"Error getting customer dashboard data: {e!s}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_analytics_summary(date_range="30"):
	"""Get comprehensive analytics summary for dashboard"""
	try:
		days = int(date_range)
		from_date = datetime.now() - timedelta(days=days)

		# Customer overview metrics
		total_customers = frappe.db.count("Customer", {"disabled": 0})
		new_customers = frappe.db.count("Customer", {"disabled": 0, "creation": (">=", from_date)})

		# Calculate analytics metrics
		analytics_summary = frappe.db.sql(
			"""
            SELECT
                AVG(lifetime_value) as avg_clv,
                AVG(retention_rate) as avg_retention,
                COUNT(CASE WHEN churn_probability > 70 THEN 1 END) as at_risk_count,
                COUNT(CASE WHEN segment = 'VIP' THEN 1 END) as vip_count,
                COUNT(CASE WHEN segment = 'High Value' THEN 1 END) as high_value_count
            FROM `tabCustomer Analytics`
            WHERE calculation_date >= %s
        """,
			(from_date,),
			as_dict=True,
		)

		# Top performing customers
		top_customers = frappe.db.sql(
			"""
            SELECT
                ca.customer,
                ca.customer_name,
                ca.customer_name_ar,
                ca.lifetime_value,
                ca.segment,
                ca.total_orders,
                ca.retention_rate
            FROM `tabCustomer Analytics` ca
            WHERE ca.calculation_date >= %s
            ORDER BY ca.lifetime_value DESC
            LIMIT 10
        """,
			(from_date,),
			as_dict=True,
		)

		# At-risk customers
		at_risk_customers = frappe.db.sql(
			"""
            SELECT
                ca.customer,
                ca.customer_name,
                ca.customer_name_ar,
                ca.churn_probability,
                ca.days_since_last_visit,
                ca.last_service_date
            FROM `tabCustomer Analytics` ca
            WHERE ca.churn_probability > 70
            AND ca.calculation_date >= %s
            ORDER BY ca.churn_probability DESC
            LIMIT 10
        """,
			(from_date,),
			as_dict=True,
		)

		# Segment distribution
		segment_distribution = frappe.db.sql(
			"""
            SELECT
                segment,
                COUNT(*) as count,
                AVG(lifetime_value) as avg_value
            FROM `tabCustomer Analytics`
            WHERE calculation_date >= %s
            GROUP BY segment
            ORDER BY count DESC
        """,
			(from_date,),
			as_dict=True,
		)

		# CLV trends (monthly)
		clv_trends = frappe.db.sql(
			"""
            SELECT
                DATE_FORMAT(calculation_date, '%%Y-%%m') as month,
                AVG(lifetime_value) as avg_clv,
                COUNT(*) as customer_count
            FROM `tabCustomer Analytics`
            WHERE calculation_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(calculation_date, '%%Y-%%m')
            ORDER BY month DESC
        """,
			as_dict=True,
		)

		# Service patterns by day of week
		service_patterns = frappe.db.sql(
			"""
            SELECT
                DAYOFWEEK(si.posting_date) as day_of_week,
                HOUR(si.posting_time) as hour_of_day,
                COUNT(*) as service_count
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1
            AND si.posting_date >= %s
            GROUP BY DAYOFWEEK(si.posting_date), HOUR(si.posting_time)
            ORDER BY day_of_week, hour_of_day
        """,
			(from_date,),
			as_dict=True,
		)

		# Calculate growth rate
		growth_rate = 0.0
		if total_customers > 0 and new_customers > 0:
			old_customer_count = total_customers - new_customers
			if old_customer_count > 0:
				growth_rate = (new_customers / old_customer_count) * 100

		# Build summary
		summary_data = {
			"overview": {
				"total_customers": total_customers,
				"new_customers": new_customers,
				"growth_rate": round(growth_rate, 2),
				"avg_clv": round(analytics_summary[0].get("avg_clv", 0), 3) if analytics_summary else 0,
				"avg_retention": round(analytics_summary[0].get("avg_retention", 0), 1)
				if analytics_summary
				else 0,
				"at_risk_count": analytics_summary[0].get("at_risk_count", 0) if analytics_summary else 0,
				"vip_count": analytics_summary[0].get("vip_count", 0) if analytics_summary else 0,
			},
			"top_customers": top_customers or [],
			"at_risk_customers": at_risk_customers or [],
			"segment_distribution": segment_distribution or [],
			"clv_trends": clv_trends or [],
			"service_patterns": service_patterns or [],
			"last_updated": datetime.now().isoformat(),
		}

		return {"success": True, "data": summary_data}

	except Exception as e:
		frappe.log_error(f"Error getting analytics summary: {e!s}")
		return {"success": False, "error": str(e)}
