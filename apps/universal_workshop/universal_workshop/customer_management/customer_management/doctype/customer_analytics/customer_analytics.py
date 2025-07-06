# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import json
import statistics
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, cstr, flt, get_datetime, getdate, now_datetime


class CustomerAnalytics(Document):
	def validate(self):
		"""Validate analytics data before saving"""
		self.validate_date_range()
		self.validate_customer_exists()

	def validate_date_range(self):
		"""Ensure data period dates are valid"""
		if (
			self.data_period_from
			and self.data_period_to
			and getdate(self.data_period_to) < getdate(self.data_period_from)
		):
			frappe.throw(_("Data Period To date cannot be before Data Period From date"))

	def validate_customer_exists(self):
		"""Verify customer exists and is active"""
		if self.customer:
			customer = frappe.get_doc("Customer", self.customer)
			if customer.disabled:
				frappe.throw(_("Cannot create analytics for disabled customer: {0}").format(self.customer))

	def before_save(self):
		"""Calculate analytics before saving"""
		if self.customer and self.data_period_from and self.data_period_to:
			self.calculate_all_analytics()

	def calculate_all_analytics(self):
		"""Calculate all analytics metrics for the customer"""
		try:
			# Calculate Customer Lifetime Value
			self.calculate_clv()

			# Calculate Retention Analytics
			self.calculate_retention_analytics()

			# Calculate Service Patterns
			self.calculate_service_patterns()

			# Calculate Loyalty Indicators
			self.calculate_loyalty_indicators()

			# Update customer segment
			self.update_customer_segment()

			# Mark calculation completion
			self.clv_calculation_date = now_datetime()
			self.needs_recalculation = 0

		except Exception as e:
			frappe.log_error(f"Error calculating analytics for customer {self.customer}: {e!s}")
			self.calculation_notes = f"Error during calculation: {e!s}"
			self.data_source_quality = "Poor"

	def calculate_clv(self):
		"""Calculate Customer Lifetime Value and related metrics"""
		try:
			# Get all invoices for the customer in the period
			invoices = frappe.db.sql(
				"""
                SELECT
                    posting_date,
                    grand_total,
                    status
                FROM `tabSales Invoice`
                WHERE customer = %s
                AND posting_date BETWEEN %s AND %s
                AND docstatus = 1
                ORDER BY posting_date
            """,
				(self.customer, self.data_period_from, self.data_period_to),
				as_dict=True,
			)

			if not invoices:
				self.total_revenue = 0
				self.total_orders = 0
				self.average_order_value = 0
				self.lifetime_value = 0
				self.data_source_quality = "Insufficient Data"
				return

			# Calculate basic metrics
			self.total_revenue = sum(flt(invoice.grand_total) for invoice in invoices)
			self.total_orders = len(invoices)
			self.average_order_value = self.total_revenue / self.total_orders if self.total_orders > 0 else 0

			# Calculate Customer Lifetime Value (simple model)
			# CLV = Average Order Value × Purchase Frequency × Customer Lifespan

			# Calculate purchase frequency (orders per month)
			period_months = self.get_period_months()
			purchase_frequency = self.total_orders / period_months if period_months > 0 else 0

			# Estimate customer lifespan based on first and last order
			if len(invoices) > 1:
				first_order = getdate(invoices[0].posting_date)
				last_order = getdate(invoices[-1].posting_date)
				lifespan_days = (last_order - first_order).days + 1
				lifespan_months = lifespan_days / 30.0
			else:
				lifespan_months = 1.0  # Assume at least 1 month for new customers

			# Calculate CLV
			self.lifetime_value = self.average_order_value * purchase_frequency * lifespan_months

			# Calculate CLV trend
			self.calculate_clv_trend(invoices)

			# Predict future value (simple linear projection)
			if len(invoices) >= 3:
				monthly_values = self.get_monthly_revenue_trend(invoices)
				if len(monthly_values) >= 2:
					# Simple linear regression for prediction
					avg_monthly_growth = (monthly_values[-1] - monthly_values[0]) / len(monthly_values)
					self.predicted_future_value = self.total_revenue + (
						avg_monthly_growth * 6
					)  # 6 months projection

			self.data_source_quality = "Good" if self.total_orders >= 3 else "Fair"

		except Exception as e:
			frappe.log_error(f"Error calculating CLV for customer {self.customer}: {e!s}")
			self.data_source_quality = "Poor"

	def calculate_clv_trend(self, invoices):
		"""Calculate CLV trend direction"""
		if len(invoices) < 2:
			self.clv_trend = "New Customer"
			return

		# Split invoices into first and second half
		mid_point = len(invoices) // 2
		first_half_total = sum(flt(inv.grand_total) for inv in invoices[:mid_point])
		second_half_total = sum(flt(inv.grand_total) for inv in invoices[mid_point:])

		# Calculate averages
		first_half_avg = first_half_total / mid_point if mid_point > 0 else 0
		second_half_avg = (
			second_half_total / (len(invoices) - mid_point) if (len(invoices) - mid_point) > 0 else 0
		)

		# Determine trend
		if second_half_avg > first_half_avg * 1.1:  # 10% increase threshold
			self.clv_trend = "Increasing"
		elif second_half_avg < first_half_avg * 0.9:  # 10% decrease threshold
			self.clv_trend = "Decreasing"
		else:
			self.clv_trend = "Stable"

	def get_monthly_revenue_trend(self, invoices):
		"""Get monthly revenue trend for prediction"""
		monthly_totals = {}

		for invoice in invoices:
			month_key = getdate(invoice.posting_date).strftime("%Y-%m")
			if month_key not in monthly_totals:
				monthly_totals[month_key] = 0
			monthly_totals[month_key] += flt(invoice.grand_total)

		return list(monthly_totals.values())

	def calculate_retention_analytics(self):
		"""Calculate customer retention metrics"""
		try:
			# Get customer creation date
			customer_doc = frappe.get_doc("Customer", self.customer)
			customer_creation = getdate(customer_doc.creation)
			today = getdate()

			# Calculate customer age
			self.customer_age_days = (today - customer_creation).days

			# Determine retention cohort
			if self.customer_age_days <= 90:
				self.retention_cohort = "New (0-3 months)"
			elif self.customer_age_days <= 365:
				self.retention_cohort = "Established (3-12 months)"
			elif self.customer_age_days <= 1095:  # 3 years
				self.retention_cohort = "Loyal (1-3 years)"
			else:
				self.retention_cohort = "Champion (3+ years)"

			# Calculate last service date and days since
			last_invoice = frappe.db.sql(
				"""
                SELECT MAX(posting_date) as last_date
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1
            """,
				(self.customer,),
				as_dict=True,
			)

			if last_invoice and last_invoice[0].last_date:
				self.last_service_date = last_invoice[0].last_date
				self.days_since_last_visit = (today - getdate(self.last_service_date)).days
			else:
				self.days_since_last_visit = self.customer_age_days

			# Calculate visit frequency (visits per month)
			period_months = self.get_period_months()
			self.visit_frequency = self.total_orders / period_months if period_months > 0 else 0

			# Calculate retention rate (simple model based on visit frequency)
			expected_frequency = 1.0  # Expected 1 visit per month
			if self.visit_frequency >= expected_frequency:
				self.retention_rate = 95.0
			elif self.visit_frequency >= 0.5:
				self.retention_rate = 75.0
			elif self.visit_frequency >= 0.25:
				self.retention_rate = 50.0
			else:
				self.retention_rate = 25.0

			# Calculate churn probability (inverse of retention)
			self.churn_probability = 100.0 - self.retention_rate

		except Exception as e:
			frappe.log_error(f"Error calculating retention analytics for customer {self.customer}: {e!s}")

	def calculate_service_patterns(self):
		"""Calculate service patterns and preferences"""
		try:
			# Get service data
			services = frappe.db.sql(
				"""
                SELECT
                    si.posting_date,
                    si.grand_total,
                    DAYNAME(si.posting_date) as day_name,
                    MONTH(si.posting_date) as month_num,
                    MONTHNAME(si.posting_date) as month_name,
                    sii.item_name,
                    sii.qty,
                    sii.amount
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
                WHERE si.customer = %s
                AND si.posting_date BETWEEN %s AND %s
                AND si.docstatus = 1
                ORDER BY si.posting_date
            """,
				(self.customer, self.data_period_from, self.data_period_to),
				as_dict=True,
			)

			if not services:
				return

			# Analyze preferred service day
			day_counts = {}
			for service in services:
				day = service.day_name
				day_counts[day] = day_counts.get(day, 0) + 1

			if day_counts:
				self.preferred_service_day = max(day_counts, key=day_counts.get)

			# Analyze peak service months
			month_counts = {}
			for service in services:
				month = service.month_name
				month_counts[month] = month_counts.get(month, 0) + 1

			if month_counts:
				peak_months = sorted(month_counts.items(), key=lambda x: x[1], reverse=True)[:3]
				self.peak_service_months = ", ".join([month[0] for month in peak_months])

			# Calculate average service interval
			service_dates = [getdate(service.posting_date) for service in services]
			service_dates = sorted(set(service_dates))  # Remove duplicates and sort

			if len(service_dates) > 1:
				intervals = []
				for i in range(1, len(service_dates)):
					interval = (service_dates[i] - service_dates[i - 1]).days
					intervals.append(interval)
				self.average_service_interval = sum(intervals) / len(intervals)

			# Analyze most frequent service
			service_counts = {}
			for service in services:
				item = service.item_name
				service_counts[item] = service_counts.get(item, 0) + service.qty

			if service_counts:
				self.most_frequent_service = max(service_counts, key=service_counts.get)

			# Calculate service complexity score (based on average invoice value)
			if self.average_order_value:
				if self.average_order_value > 500:  # High value services
					self.service_complexity_score = 9.0
				elif self.average_order_value > 200:
					self.service_complexity_score = 6.0
				elif self.average_order_value > 100:
					self.service_complexity_score = 4.0
				else:
					self.service_complexity_score = 2.0

			# Create service type preferences JSON
			service_preferences = {
				"preferred_day": self.preferred_service_day,
				"peak_months": self.peak_service_months,
				"most_frequent": self.most_frequent_service,
				"complexity_level": "High"
				if self.service_complexity_score >= 7
				else "Medium"
				if self.service_complexity_score >= 4
				else "Low",
			}
			self.service_type_preferences = json.dumps(service_preferences)

		except Exception as e:
			frappe.log_error(f"Error calculating service patterns for customer {self.customer}: {e!s}")

	def calculate_loyalty_indicators(self):
		"""Calculate loyalty and satisfaction indicators"""
		try:
			# Get loyalty points data
			loyalty_data = frappe.db.sql(
				"""
                SELECT
                    points_balance,
                    customer_tier,
                    total_points_earned,
                    total_amount_spent
                FROM `tabCustomer Loyalty Points`
                WHERE customer = %s
                ORDER BY creation DESC
                LIMIT 1
            """,
				(self.customer,),
				as_dict=True,
			)

			if loyalty_data:
				self.loyalty_points_balance = cint(loyalty_data[0].points_balance)
				self.loyalty_tier = loyalty_data[0].customer_tier

			# Check if repeat customer
			self.repeat_customer = 1 if self.total_orders > 1 else 0

			# Get satisfaction scores (if available)
			satisfaction_scores = frappe.db.sql(
				"""
                SELECT AVG(satisfaction_score) as avg_score
                FROM `tabCustomer Satisfaction Survey`
                WHERE customer = %s
                AND survey_date BETWEEN %s AND %s
            """,
				(self.customer, self.data_period_from, self.data_period_to),
				as_dict=True,
			)

			if satisfaction_scores and satisfaction_scores[0].avg_score:
				self.satisfaction_score = flt(satisfaction_scores[0].avg_score)

			# Calculate brand advocacy score (based on loyalty and satisfaction)
			if self.satisfaction_score and self.loyalty_points_balance:
				# Simple formula: (satisfaction_score/5 * 0.6) + (loyalty_tier_weight * 0.4)
				tier_weights = {"Bronze": 0.25, "Silver": 0.5, "Gold": 0.75, "Platinum": 1.0}
				tier_weight = tier_weights.get(self.loyalty_tier, 0.25)
				self.brand_advocacy_score = (self.satisfaction_score / 5.0 * 0.6) + (tier_weight * 0.4)

			# Get referrals made
			referrals = frappe.db.sql(
				"""
                SELECT COUNT(*) as count
                FROM `tabCustomer`
                WHERE referred_by = %s
            """,
				(self.customer,),
				as_dict=True,
			)

			if referrals:
				self.referrals_made = cint(referrals[0].count)

		except Exception as e:
			frappe.log_error(f"Error calculating loyalty indicators for customer {self.customer}: {e!s}")

	def update_customer_segment(self):
		"""Update customer segment based on calculated metrics"""
		try:
			# Segment based on CLV, retention, and loyalty
			if self.lifetime_value > 2000 and self.retention_rate > 80:
				self.segment = "VIP"
			elif self.lifetime_value > 1000 and self.retention_rate > 60:
				self.segment = "High Value"
			elif self.churn_probability > 70:
				self.segment = "At Risk"
			elif self.customer_age_days <= 90:
				self.segment = "New"
			elif self.days_since_last_visit > 180:
				self.segment = "Lost"
			else:
				self.segment = "Regular"

		except Exception as e:
			frappe.log_error(f"Error updating customer segment for {self.customer}: {e!s}")

	def get_period_months(self):
		"""Calculate number of months in the data period"""
		if not self.data_period_from or not self.data_period_to:
			return 1

		start = getdate(self.data_period_from)
		end = getdate(self.data_period_to)
		days = (end - start).days + 1
		return days / 30.0

	@staticmethod
	def create_analytics_for_customer(customer, from_date=None, to_date=None):
		"""Create or update analytics record for a customer"""
		try:
			if not from_date:
				from_date = add_days(getdate(), -365)  # Default to 1 year back
			if not to_date:
				to_date = getdate()

			# Check if analytics record exists for this period
			existing = frappe.db.exists(
				"Customer Analytics",
				{"customer": customer, "data_period_from": from_date, "data_period_to": to_date},
			)

			if existing:
				doc = frappe.get_doc("Customer Analytics", existing)
				doc.needs_recalculation = 1
				doc.save()
			else:
				doc = frappe.new_doc("Customer Analytics")
				doc.customer = customer
				doc.data_period_from = from_date
				doc.data_period_to = to_date
				doc.calculation_date = getdate()
				doc.insert()

			return doc

		except Exception as e:
			frappe.log_error(f"Error creating analytics for customer {customer}: {e!s}")
			return None


# Whitelisted API functions for dashboard


@frappe.whitelist()
def get_customer_analytics_summary(date_range="30"):
	"""Get summary analytics for customer dashboard"""
	try:
		days = cint(date_range)
		from_date = add_days(getdate(), -days)

		# Get latest analytics for all customers
		analytics = frappe.db.sql(
			"""
            SELECT
                customer,
                customer_name,
                customer_name_ar,
                lifetime_value,
                retention_rate,
                segment,
                loyalty_tier,
                churn_probability,
                last_service_date,
                total_orders
            FROM `tabCustomer Analytics`
            WHERE calculation_date >= %s
            AND customer IN (
                SELECT DISTINCT customer
                FROM `tabCustomer Analytics` ca2
                WHERE ca2.customer = `tabCustomer Analytics`.customer
                ORDER BY ca2.creation DESC
                LIMIT 1
            )
            ORDER BY lifetime_value DESC
        """,
			(from_date,),
			as_dict=True,
		)

		# Calculate summary statistics
		total_customers = len(analytics)
		avg_clv = (
			sum(flt(a.lifetime_value) for a in analytics) / total_customers if total_customers > 0 else 0
		)
		avg_retention = (
			sum(flt(a.retention_rate) for a in analytics) / total_customers if total_customers > 0 else 0
		)

		# Segment distribution
		segment_counts = {}
		for a in analytics:
			segment = a.segment or "Unknown"
			segment_counts[segment] = segment_counts.get(segment, 0) + 1

		# At-risk customers
		at_risk_customers = [a for a in analytics if flt(a.churn_probability) > 60]

		return {
			"success": True,
			"summary": {
				"total_customers": total_customers,
				"average_clv": avg_clv,
				"average_retention": avg_retention,
				"at_risk_count": len(at_risk_customers),
			},
			"segment_distribution": segment_counts,
			"top_customers": analytics[:10],
			"at_risk_customers": at_risk_customers[:5],
		}

	except Exception as e:
		frappe.log_error(f"Error getting customer analytics summary: {e!s}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def refresh_customer_analytics(customer=None):
	"""Refresh analytics for specific customer or all customers"""
	try:
		if customer:
			CustomerAnalytics.create_analytics_for_customer(customer)
			return {"success": True, "message": f"Analytics refreshed for customer {customer}"}
		else:
			# Refresh for all active customers
			customers = frappe.get_all("Customer", filters={"disabled": 0}, fields=["name"])

			count = 0
			for customer_doc in customers:
				CustomerAnalytics.create_analytics_for_customer(customer_doc.name)
				count += 1

			return {"success": True, "message": f"Analytics refreshed for {count} customers"}

	except Exception as e:
		frappe.log_error(f"Error refreshing customer analytics: {e!s}")
		return {"success": False, "error": str(e)}
