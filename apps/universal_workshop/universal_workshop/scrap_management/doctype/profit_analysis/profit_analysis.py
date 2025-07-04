# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, cint, date_diff, flt, getdate, today


class ProfitAnalysis(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields

	def validate(self):
		"""Validate profit analysis data before saving"""
		self.validate_dates()
		self.validate_arabic_name()
		self.validate_analysis_period()

	def before_save(self):
		"""Calculate all metrics before saving"""
		self.set_default_values()
		self.calculate_revenue_metrics()
		self.calculate_cost_metrics()
		self.calculate_profitability_metrics()
		self.calculate_financial_ratios()

	def after_insert(self):
		"""After creating new analysis"""
		self.generate_performance_data()
		self.schedule_next_analysis()

	def validate_dates(self):
		"""Validate analysis period dates"""
		if not self.analysis_period_from or not self.analysis_period_to:
			frappe.throw(_("Analysis period dates are required"))

		if getdate(self.analysis_period_from) >= getdate(self.analysis_period_to):
			frappe.throw(_("Analysis period 'From' date must be before 'To' date"))

		# Check if period is not too long (max 1 year)
		days_diff = date_diff(self.analysis_period_to, self.analysis_period_from)
		if days_diff > 365:
			frappe.throw(_("Analysis period cannot exceed 365 days"))

	def validate_arabic_name(self):
		"""Ensure Arabic analysis name is provided"""
		if not self.analysis_name_ar:
			frappe.throw(_("Arabic analysis name is required"))

	def validate_analysis_period(self):
		"""Validate that analysis period has sales data"""
		if self.sales_channel:
			# Check if there are any sales in the selected period for this channel
			sales_count = frappe.db.count(
				"Sales Invoice",
				{
					"docstatus": 1,
					"posting_date": [
						"between",
						[self.analysis_period_from, self.analysis_period_to],
					],
					"custom_sales_channel": self.sales_channel,
				},
			)
		else:
			# Check for any sales in the period
			sales_count = frappe.db.count(
				"Sales Invoice",
				{
					"docstatus": 1,
					"posting_date": [
						"between",
						[self.analysis_period_from, self.analysis_period_to],
					],
				},
			)

		if sales_count == 0:
			frappe.msgprint(
				_("No sales data found for the selected period and channel"),
				alert=True,
				indicator="orange",
			)

	def set_default_values(self):
		"""Set default values for required fields"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = today()
		if not self.last_updated_by:
			self.last_updated_by = frappe.session.user
		if not self.last_updated_date:
			self.last_updated_date = today()
		if not self.calculation_method:
			self.calculation_method = "Automated System Calculation"
		if not self.data_source:
			self.data_source = "ERPNext Sales and Purchase Data"

	def calculate_revenue_metrics(self):
		"""Calculate all revenue-related metrics"""
		try:
			# Base query conditions
			conditions = {
				"docstatus": 1,
				"posting_date": ["between", [self.analysis_period_from, self.analysis_period_to]],
			}

			# Add sales channel filter if specified
			if self.sales_channel:
				conditions["custom_sales_channel"] = self.sales_channel

			# Get all sales invoices for the period
			sales_invoices = frappe.get_list(
				"Sales Invoice",
				filters=conditions,
				fields=[
					"name",
					"grand_total",
					"customer_group",
					"custom_sales_channel",
					"posting_date",
				],
			)

			if not sales_invoices:
				self.total_revenue_omr = 0
				self.total_orders = 0
				return

			# Calculate totals
			self.total_revenue_omr = sum(flt(invoice.grand_total, 3) for invoice in sales_invoices)
			self.total_orders = len(sales_invoices)

			# Calculate average order value
			if self.total_orders > 0:
				self.average_order_value_omr = flt(self.total_revenue_omr / self.total_orders, 3)
				self.highest_order_value_omr = max(flt(invoice.grand_total, 3) for invoice in sales_invoices)

			# Calculate sales by channel type
			marketplace_sales = 0
			direct_sales = 0
			b2b_sales = 0

			for invoice in sales_invoices:
				invoice_total = flt(invoice.grand_total, 3)

				# Get sales channel info
				if invoice.custom_sales_channel:
					channel_doc = frappe.get_cached_doc("Sales Channel", invoice.custom_sales_channel)
					if channel_doc.platform_type in ["eBay", "Amazon", "OpenSooq", "Dubizzle"]:
						marketplace_sales += invoice_total
					elif channel_doc.platform_type == "Direct":
						direct_sales += invoice_total
					elif channel_doc.platform_type == "B2B":
						b2b_sales += invoice_total
				else:
					direct_sales += invoice_total

			self.marketplace_sales_omr = flt(marketplace_sales, 3)
			self.direct_sales_omr = flt(direct_sales, 3)
			self.b2b_sales_omr = flt(b2b_sales, 3)

			# Calculate revenue growth (compare with previous period)
			self.calculate_revenue_growth()

		except Exception as e:
			frappe.log_error(f"Error calculating revenue metrics: {e!s}")
			frappe.throw(_("Error calculating revenue metrics. Please check the data and try again."))

	def calculate_revenue_growth(self):
		"""Calculate revenue growth compared to previous period"""
		try:
			# Calculate previous period dates
			period_days = date_diff(self.analysis_period_to, self.analysis_period_from)
			prev_to_date = getdate(self.analysis_period_from) - timedelta(days=1)
			prev_from_date = prev_to_date - timedelta(days=period_days)

			# Get previous period revenue
			prev_conditions = {
				"docstatus": 1,
				"posting_date": ["between", [prev_from_date, prev_to_date]],
			}

			if self.sales_channel:
				prev_conditions["custom_sales_channel"] = self.sales_channel

			prev_invoices = frappe.get_list("Sales Invoice", filters=prev_conditions, fields=["grand_total"])

			prev_revenue = sum(flt(invoice.grand_total, 3) for invoice in prev_invoices)

			if prev_revenue > 0:
				growth = ((self.total_revenue_omr - prev_revenue) / prev_revenue) * 100
				self.revenue_growth_percentage = flt(growth, 2)
			else:
				self.revenue_growth_percentage = 100.0 if self.total_revenue_omr > 0 else 0.0

		except Exception as e:
			frappe.log_error(f"Error calculating revenue growth: {e!s}")
			self.revenue_growth_percentage = 0.0

	def calculate_cost_metrics(self):
		"""Calculate all cost-related metrics"""
		try:
			# Get purchase data for the period
			purchase_conditions = {
				"docstatus": 1,
				"posting_date": ["between", [self.analysis_period_from, self.analysis_period_to]],
			}

			purchase_invoices = frappe.get_list(
				"Purchase Invoice",
				filters=purchase_conditions,
				fields=["name", "grand_total", "supplier_group"],
			)

			# Calculate acquisition costs (purchase costs)
			self.acquisition_costs_omr = sum(flt(pi.grand_total, 3) for pi in purchase_invoices)

			# Get labor costs from timesheets/payroll
			self.calculate_labor_costs()

			# Calculate storage costs (warehouse expenses)
			self.calculate_storage_costs()

			# Calculate other cost components
			self.calculate_overhead_costs()
			self.calculate_shipping_costs()
			self.calculate_marketing_costs()
			self.calculate_platform_fees()

			# Calculate total costs
			self.total_costs_omr = flt(
				(self.acquisition_costs_omr or 0)
				+ (self.labor_costs_omr or 0)
				+ (self.storage_costs_omr or 0)
				+ (self.overhead_costs_omr or 0)
				+ (self.shipping_costs_omr or 0)
				+ (self.marketing_costs_omr or 0)
				+ (self.platform_fees_omr or 0),
				3,
			)

		except Exception as e:
			frappe.log_error(f"Error calculating cost metrics: {e!s}")
			frappe.throw(_("Error calculating cost metrics. Please check the data and try again."))

	def calculate_labor_costs(self):
		"""Calculate labor costs for the period"""
		try:
			# Get salary slips for the period (approximation)
			salary_slips = frappe.get_list(
				"Salary Slip",
				filters={
					"docstatus": 1,
					"start_date": [">=", self.analysis_period_from],
					"end_date": ["<=", self.analysis_period_to],
				},
				fields=["net_pay"],
			)

			total_payroll = sum(flt(slip.net_pay, 3) for slip in salary_slips)

			# Allocate percentage to parts processing (assume 30% for scrap management)
			self.labor_costs_omr = flt(total_payroll * 0.3, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating labor costs: {e!s}")
			self.labor_costs_omr = 0.0

	def calculate_storage_costs(self):
		"""Calculate storage and warehouse costs"""
		try:
			# Estimate storage costs based on warehouse size and duration
			# This is a simplified calculation - in practice, you'd have detailed warehouse cost tracking

			# Get number of items in storage
			storage_locations = frappe.get_list("Storage Location", fields=["COUNT(*) as location_count"])

			location_count = storage_locations[0].location_count if storage_locations else 0

			# Estimate monthly storage cost per location (example: 5 OMR per location per month)
			monthly_cost_per_location = 5.0
			period_months = date_diff(self.analysis_period_to, self.analysis_period_from) / 30

			self.storage_costs_omr = flt(location_count * monthly_cost_per_location * period_months, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating storage costs: {e!s}")
			self.storage_costs_omr = 0.0

	def calculate_overhead_costs(self):
		"""Calculate overhead costs"""
		try:
			# Estimate overhead as percentage of total revenue (typical 10-15%)
			overhead_percentage = 0.12  # 12%
			self.overhead_costs_omr = flt(self.total_revenue_omr * overhead_percentage, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating overhead costs: {e!s}")
			self.overhead_costs_omr = 0.0

	def calculate_shipping_costs(self):
		"""Calculate shipping and delivery costs"""
		try:
			# Get delivery notes for the period
			delivery_notes = frappe.get_list(
				"Delivery Note",
				filters={
					"docstatus": 1,
					"posting_date": [
						"between",
						[self.analysis_period_from, self.analysis_period_to],
					],
				},
				fields=["name"],
			)

			# Estimate shipping cost per delivery (example: 3 OMR per delivery)
			cost_per_delivery = 3.0
			self.shipping_costs_omr = flt(len(delivery_notes) * cost_per_delivery, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating shipping costs: {e!s}")
			self.shipping_costs_omr = 0.0

	def calculate_marketing_costs(self):
		"""Calculate marketing and advertising costs"""
		try:
			# Estimate marketing costs as percentage of revenue (typical 3-5%)
			marketing_percentage = 0.04  # 4%
			self.marketing_costs_omr = flt(self.total_revenue_omr * marketing_percentage, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating marketing costs: {e!s}")
			self.marketing_costs_omr = 0.0

	def calculate_platform_fees(self):
		"""Calculate marketplace platform fees"""
		try:
			platform_fees = 0.0

			if self.sales_channel:
				# Get commission rate for this channel
				channel_doc = frappe.get_cached_doc("Sales Channel", self.sales_channel)
				commission_rate = flt(channel_doc.commission_percentage, 2) / 100
				platform_fees = self.marketplace_sales_omr * commission_rate
			else:
				# Calculate for all marketplace sales with average commission (assume 8%)
				average_commission = 0.08
				platform_fees = self.marketplace_sales_omr * average_commission

			self.platform_fees_omr = flt(platform_fees, 3)

		except Exception as e:
			frappe.log_error(f"Error calculating platform fees: {e!s}")
			self.platform_fees_omr = 0.0

	def calculate_profitability_metrics(self):
		"""Calculate profitability metrics"""
		try:
			# Gross profit (Revenue - Cost of Goods Sold)
			# For simplicity, using acquisition costs as COGS
			cogs = self.acquisition_costs_omr or 0
			self.gross_profit_omr = flt(self.total_revenue_omr - cogs, 3)

			# Gross profit margin
			if self.total_revenue_omr > 0:
				self.gross_profit_margin_percentage = flt(
					(self.gross_profit_omr / self.total_revenue_omr) * 100, 2
				)
			else:
				self.gross_profit_margin_percentage = 0.0

			# Net profit (Revenue - Total Costs)
			self.net_profit_omr = flt(self.total_revenue_omr - self.total_costs_omr, 3)

			# Net profit margin
			if self.total_revenue_omr > 0:
				self.net_profit_margin_percentage = flt(
					(self.net_profit_omr / self.total_revenue_omr) * 100, 2
				)
			else:
				self.net_profit_margin_percentage = 0.0

			# ROI calculation
			if self.total_costs_omr > 0:
				self.roi_percentage = flt((self.net_profit_omr / self.total_costs_omr) * 100, 2)
			else:
				self.roi_percentage = 0.0

			# Breakeven point calculation
			self.calculate_breakeven_point()

			# Inventory turnover ratio
			self.calculate_inventory_turnover()

			# Profit per part
			if self.total_orders > 0:
				self.profit_per_part_omr = flt(self.net_profit_omr / self.total_orders, 3)
			else:
				self.profit_per_part_omr = 0.0

		except Exception as e:
			frappe.log_error(f"Error calculating profitability metrics: {e!s}")
			frappe.throw(_("Error calculating profitability metrics. Please check the data and try again."))

	def calculate_breakeven_point(self):
		"""Calculate breakeven point in days"""
		try:
			if self.net_profit_omr > 0:
				period_days = date_diff(self.analysis_period_to, self.analysis_period_from)
				daily_profit = self.net_profit_omr / period_days

				if daily_profit > 0:
					# Days to recover total costs
					self.breakeven_point_days = cint(self.total_costs_omr / daily_profit)
				else:
					self.breakeven_point_days = 0
			else:
				self.breakeven_point_days = 0

		except Exception as e:
			frappe.log_error(f"Error calculating breakeven point: {e!s}")
			self.breakeven_point_days = 0

	def calculate_inventory_turnover(self):
		"""Calculate inventory turnover ratio"""
		try:
			# Get average inventory value for the period
			# This is simplified - in practice you'd track inventory values over time

			# Get current stock value as approximation
			stock_value_query = """
                SELECT SUM(sle.stock_value)
                FROM `tabStock Ledger Entry` sle
                WHERE sle.posting_date <= %s
                AND sle.is_cancelled = 0
            """

			result = frappe.db.sql(stock_value_query, [self.analysis_period_to])
			avg_inventory_value = flt(result[0][0] if result and result[0][0] else 0, 3)

			if avg_inventory_value > 0:
				# Inventory turnover = COGS / Average Inventory
				cogs = self.acquisition_costs_omr or 0
				self.inventory_turnover_ratio = flt(cogs / avg_inventory_value, 2)
			else:
				self.inventory_turnover_ratio = 0.0

		except Exception as e:
			frappe.log_error(f"Error calculating inventory turnover: {e!s}")
			self.inventory_turnover_ratio = 0.0

	def calculate_financial_ratios(self):
		"""Calculate financial ratios"""
		try:
			# These are simplified calculations for demonstration
			# In practice, you'd need detailed balance sheet data

			# Current ratio (assume assets = revenue, liabilities = costs for simplification)
			if self.total_costs_omr > 0:
				self.current_ratio = flt(self.total_revenue_omr / self.total_costs_omr, 2)
			else:
				self.current_ratio = 0.0

			# Quick ratio (more conservative)
			self.quick_ratio = flt(self.current_ratio * 0.8, 2)  # Simplified

			# Debt to equity ratio (simplified)
			self.debt_to_equity_ratio = flt(0.3, 2)  # Placeholder

			# Return on assets
			estimated_assets = self.total_revenue_omr * 1.5  # Simplified estimate
			if estimated_assets > 0:
				self.return_on_assets_percentage = flt((self.net_profit_omr / estimated_assets) * 100, 2)
			else:
				self.return_on_assets_percentage = 0.0

			# Return on equity
			estimated_equity = estimated_assets * 0.7  # Simplified
			if estimated_equity > 0:
				self.return_on_equity_percentage = flt((self.net_profit_omr / estimated_equity) * 100, 2)
			else:
				self.return_on_equity_percentage = 0.0

			# Asset turnover ratio
			if estimated_assets > 0:
				self.asset_turnover_ratio = flt(self.total_revenue_omr / estimated_assets, 2)
			else:
				self.asset_turnover_ratio = 0.0

			# Profit margin ratio (same as net profit margin)
			self.profit_margin_ratio = self.net_profit_margin_percentage

			# Operating margin
			operating_income = self.total_revenue_omr - self.total_costs_omr + (self.overhead_costs_omr or 0)
			if self.total_revenue_omr > 0:
				self.operating_margin_percentage = flt((operating_income / self.total_revenue_omr) * 100, 2)
			else:
				self.operating_margin_percentage = 0.0

		except Exception as e:
			frappe.log_error(f"Error calculating financial ratios: {e!s}")
			# Set default values on error
			self.current_ratio = 0.0
			self.quick_ratio = 0.0
			self.debt_to_equity_ratio = 0.0
			self.return_on_assets_percentage = 0.0
			self.return_on_equity_percentage = 0.0
			self.asset_turnover_ratio = 0.0
			self.profit_margin_ratio = 0.0
			self.operating_margin_percentage = 0.0

	def generate_performance_data(self):
		"""Generate sales performance data"""
		try:
			# Generate best/worst performing parts data
			self.analyze_part_performance()

			# Generate customer segments data
			self.analyze_customer_segments()

			# Generate market analysis data
			self.analyze_market_trends()

		except Exception as e:
			frappe.log_error(f"Error generating performance data: {e!s}")

	def analyze_part_performance(self):
		"""Analyze best and worst performing parts"""
		try:
			# Get sales data for parts in the period
			conditions = {
				"docstatus": 1,
				"posting_date": ["between", [self.analysis_period_from, self.analysis_period_to]],
			}

			if self.sales_channel:
				conditions["custom_sales_channel"] = self.sales_channel

			# Get item-wise sales
			item_sales_query = """
                SELECT 
                    sii.item_code,
                    sii.item_name,
                    SUM(sii.qty) as total_qty,
                    SUM(sii.amount) as total_amount,
                    AVG(sii.rate) as avg_rate
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                WHERE si.docstatus = 1
                    AND si.posting_date BETWEEN %s AND %s
                    {channel_condition}
                GROUP BY sii.item_code, sii.item_name
                ORDER BY total_amount DESC
                LIMIT 10
            """.format(channel_condition="AND si.custom_sales_channel = %s" if self.sales_channel else "")

			params = [self.analysis_period_from, self.analysis_period_to]
			if self.sales_channel:
				params.append(self.sales_channel)

			top_items = frappe.db.sql(item_sales_query, params, as_dict=True)

			# Best performing parts
			best_parts = []
			for item in top_items[:5]:
				best_parts.append(
					{
						"item_code": item.item_code,
						"item_name": item.item_name,
						"total_sales": flt(item.total_amount, 3),
						"quantity_sold": cint(item.total_qty),
						"average_rate": flt(item.avg_rate, 3),
					}
				)

			self.best_performing_parts = json.dumps(best_parts, indent=2)

			# Worst performing parts (bottom 5)
			worst_parts = []
			for item in top_items[-5:]:
				worst_parts.append(
					{
						"item_code": item.item_code,
						"item_name": item.item_name,
						"total_sales": flt(item.total_amount, 3),
						"quantity_sold": cint(item.total_qty),
						"average_rate": flt(item.avg_rate, 3),
					}
				)

			self.worst_performing_parts = json.dumps(worst_parts, indent=2)

		except Exception as e:
			frappe.log_error(f"Error analyzing part performance: {e!s}")
			self.best_performing_parts = "[]"
			self.worst_performing_parts = "[]"

	def analyze_customer_segments(self):
		"""Analyze customer segments"""
		try:
			# Get customer group data
			customer_query = """
                SELECT 
                    c.customer_group,
                    COUNT(DISTINCT si.customer) as customer_count,
                    SUM(si.grand_total) as total_sales,
                    AVG(si.grand_total) as avg_order_value
                FROM `tabSales Invoice` si
                INNER JOIN `tabCustomer` c ON si.customer = c.name
                WHERE si.docstatus = 1
                    AND si.posting_date BETWEEN %s AND %s
                    {channel_condition}
                GROUP BY c.customer_group
                ORDER BY total_sales DESC
            """.format(channel_condition="AND si.custom_sales_channel = %s" if self.sales_channel else "")

			params = [self.analysis_period_from, self.analysis_period_to]
			if self.sales_channel:
				params.append(self.sales_channel)

			segments = frappe.db.sql(customer_query, params, as_dict=True)

			segment_data = []
			for segment in segments:
				segment_data.append(
					{
						"customer_group": segment.customer_group,
						"customer_count": cint(segment.customer_count),
						"total_sales": flt(segment.total_sales, 3),
						"avg_order_value": flt(segment.avg_order_value, 3),
					}
				)

			self.customer_segments = json.dumps(segment_data, indent=2)

		except Exception as e:
			frappe.log_error(f"Error analyzing customer segments: {e!s}")
			self.customer_segments = "[]"

	def analyze_market_trends(self):
		"""Analyze market trends and opportunities"""
		try:
			# Generate market analysis recommendations
			trends = []

			# Revenue growth trend
			if self.revenue_growth_percentage > 10:
				trends.append("Strong revenue growth indicates expanding market demand")
			elif self.revenue_growth_percentage < -5:
				trends.append("Revenue decline may indicate market saturation or increased competition")

			# Profit margin analysis
			if self.net_profit_margin_percentage > 15:
				trends.append("Healthy profit margins indicate strong pricing power")
			elif self.net_profit_margin_percentage < 5:
				trends.append("Low profit margins suggest need for cost optimization or pricing review")

			# Inventory turnover analysis
			if self.inventory_turnover_ratio > 6:
				trends.append("High inventory turnover indicates efficient operations")
			elif self.inventory_turnover_ratio < 2:
				trends.append("Low inventory turnover may indicate slow-moving stock")

			self.market_trends = json.dumps(trends, indent=2)

			# Generate recommendations
			recommendations = []

			if self.net_profit_margin_percentage < 10:
				recommendations.append("Consider reviewing pricing strategy to improve margins")

			if self.inventory_turnover_ratio < 3:
				recommendations.append("Focus on fast-moving parts to improve inventory efficiency")

			if self.marketplace_sales_omr > self.direct_sales_omr:
				recommendations.append("Marketplace channels are performing well - consider expansion")

			self.recommendations = json.dumps(recommendations, indent=2)

		except Exception as e:
			frappe.log_error(f"Error analyzing market trends: {e!s}")
			self.market_trends = "[]"
			self.recommendations = "[]"

	def schedule_next_analysis(self):
		"""Schedule next analysis date"""
		try:
			# Schedule next analysis in 30 days
			next_date = add_months(today(), 1)
			self.next_analysis_due = next_date

		except Exception as e:
			frappe.log_error(f"Error scheduling next analysis: {e!s}")


@frappe.whitelist()
def create_profit_analysis(
	analysis_name,
	analysis_name_ar,
	period_from,
	period_to,
	sales_channel=None,
	vehicle_category="All",
	part_category="All",
):
	"""Create new profit analysis with automatic calculations"""

	try:
		# Validate required fields
		if not analysis_name or not analysis_name_ar:
			frappe.throw(_("Analysis name in both English and Arabic is required"))

		if not period_from or not period_to:
			frappe.throw(_("Analysis period dates are required"))

		# Create new profit analysis
		doc = frappe.new_doc("Profit Analysis")
		doc.analysis_name = analysis_name
		doc.analysis_name_ar = analysis_name_ar
		doc.analysis_period_from = period_from
		doc.analysis_period_to = period_to
		doc.sales_channel = sales_channel
		doc.vehicle_category = vehicle_category
		doc.part_category = part_category
		doc.analysis_status = "In Progress"
		doc.auto_generated = 1

		doc.insert()
		frappe.db.commit()

		return {
			"success": True,
			"analysis_id": doc.name,
			"message": _("Profit analysis created successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Error creating profit analysis: {e!s}")
		return {
			"success": False,
			"message": _("Error creating profit analysis: {0}").format(str(e)),
		}


@frappe.whitelist()
def get_profit_analysis_dashboard(analysis_id):
	"""Get dashboard data for profit analysis"""

	try:
		doc = frappe.get_doc("Profit Analysis", analysis_id)

		dashboard_data = {
			"basic_info": {
				"analysis_name": doc.analysis_name,
				"analysis_name_ar": doc.analysis_name_ar,
				"period_from": doc.analysis_period_from,
				"period_to": doc.analysis_period_to,
				"status": doc.analysis_status,
			},
			"revenue_metrics": {
				"total_revenue": doc.total_revenue_omr,
				"marketplace_sales": doc.marketplace_sales_omr,
				"direct_sales": doc.direct_sales_omr,
				"total_orders": doc.total_orders,
				"average_order_value": doc.average_order_value_omr,
				"revenue_growth": doc.revenue_growth_percentage,
			},
			"profitability_metrics": {
				"gross_profit": doc.gross_profit_omr,
				"gross_margin": doc.gross_profit_margin_percentage,
				"net_profit": doc.net_profit_omr,
				"net_margin": doc.net_profit_margin_percentage,
				"roi": doc.roi_percentage,
				"profit_per_part": doc.profit_per_part_omr,
			},
			"cost_breakdown": {
				"acquisition_costs": doc.acquisition_costs_omr,
				"labor_costs": doc.labor_costs_omr,
				"storage_costs": doc.storage_costs_omr,
				"overhead_costs": doc.overhead_costs_omr,
				"shipping_costs": doc.shipping_costs_omr,
				"marketing_costs": doc.marketing_costs_omr,
				"platform_fees": doc.platform_fees_omr,
				"total_costs": doc.total_costs_omr,
			},
			"performance_data": {
				"best_parts": json.loads(doc.best_performing_parts or "[]"),
				"worst_parts": json.loads(doc.worst_performing_parts or "[]"),
				"customer_segments": json.loads(doc.customer_segments or "[]"),
				"market_trends": json.loads(doc.market_trends or "[]"),
				"recommendations": json.loads(doc.recommendations or "[]"),
			},
		}

		return dashboard_data

	except Exception as e:
		frappe.log_error(f"Error getting dashboard data: {e!s}")
		frappe.throw(_("Error loading dashboard data: {0}").format(str(e)))


@frappe.whitelist()
def generate_profit_report(filters=None):
	"""Generate comprehensive profit analysis report"""

	try:
		if isinstance(filters, str):
			filters = json.loads(filters)

		filters = filters or {}

		# Get all profit analyses based on filters
		conditions = {"docstatus": ["!=", 2]}  # Not cancelled

		if filters.get("from_date"):
			conditions["analysis_period_from"] = [">=", filters["from_date"]]
		if filters.get("to_date"):
			conditions["analysis_period_to"] = ["<=", filters["to_date"]]
		if filters.get("sales_channel"):
			conditions["sales_channel"] = filters["sales_channel"]
		if filters.get("status"):
			conditions["analysis_status"] = filters["status"]

		analyses = frappe.get_list(
			"Profit Analysis",
			filters=conditions,
			fields=[
				"name",
				"analysis_name",
				"analysis_name_ar",
				"analysis_period_from",
				"analysis_period_to",
				"total_revenue_omr",
				"net_profit_omr",
				"net_profit_margin_percentage",
				"roi_percentage",
				"total_orders",
				"analysis_status",
			],
			order_by="analysis_period_from desc",
		)

		# Calculate summary metrics
		total_revenue = sum(flt(a.total_revenue_omr, 3) for a in analyses)
		total_profit = sum(flt(a.net_profit_omr, 3) for a in analyses)
		total_orders = sum(cint(a.total_orders) for a in analyses)

		avg_margin = 0
		avg_roi = 0
		if analyses:
			avg_margin = sum(flt(a.net_profit_margin_percentage, 2) for a in analyses) / len(analyses)
			avg_roi = sum(flt(a.roi_percentage, 2) for a in analyses) / len(analyses)

		report_data = {
			"summary": {
				"total_revenue": total_revenue,
				"total_profit": total_profit,
				"total_orders": total_orders,
				"average_margin": avg_margin,
				"average_roi": avg_roi,
				"analysis_count": len(analyses),
			},
			"analyses": analyses,
			"generated_at": datetime.now().isoformat(),
			"filters_applied": filters,
		}

		return report_data

	except Exception as e:
		frappe.log_error(f"Error generating profit report: {e!s}")
		frappe.throw(_("Error generating report: {0}").format(str(e)))
