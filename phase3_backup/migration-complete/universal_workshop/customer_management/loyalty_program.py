import datetime
from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document


class LoyaltyProgramManager:
	"""Central class for managing loyalty program operations"""

	@staticmethod
	def get_customer_tier(customer):
		"""Determine customer tier based on transaction history and points"""
		if not customer:
			return "Bronze"

		# Get customer's total spent in last 12 months
		from dateutil.relativedelta import relativedelta

		start_date = datetime.date.today() - relativedelta(months=12)

		total_spent = (
			frappe.db.sql(
				"""
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE customer = %s
            AND posting_date >= %s
            AND docstatus = 1
        """,
				[customer, start_date],
			)[0][0]
			or 0
		)

		# Get customer's current points
		current_points = LoyaltyProgramManager.get_customer_points(customer)

		# Tier calculation logic
		if total_spent >= 5000 or current_points >= 10000:  # OMR 5,000 or 10,000 points
			return "Platinum"
		elif total_spent >= 2000 or current_points >= 5000:  # OMR 2,000 or 5,000 points
			return "Gold"
		elif total_spent >= 500 or current_points >= 1000:  # OMR 500 or 1,000 points
			return "Silver"
		else:
			return "Bronze"

	@staticmethod
	def get_customer_points(customer):
		"""Get customer's current loyalty points balance"""
		if not customer:
			return 0

		points_balance = (
			frappe.db.sql(
				"""
            SELECT COALESCE(SUM(points), 0) as total_points
            FROM `tabCustomer Loyalty Points`
            WHERE customer = %s
            AND status = 'Active'
        """,
				[customer],
			)[0][0]
			or 0
		)

		return points_balance

	@staticmethod
	def calculate_points_earned(transaction_amount, customer, transaction_type="service"):
		"""Calculate loyalty points based on transaction amount and customer tier"""
		if not transaction_amount or transaction_amount <= 0:
			return 0

		tier = LoyaltyProgramManager.get_customer_tier(customer)

		# Points calculation rules based on tier
		tier_multipliers = {
			"Bronze": 1.0,  # 1 point per OMR
			"Silver": 1.2,  # 1.2 points per OMR
			"Gold": 1.5,  # 1.5 points per OMR
			"Platinum": 2.0,  # 2 points per OMR
		}

		# Service type bonuses
		service_bonuses = {
			"service": 1.0,  # Regular service
			"major_repair": 1.5,  # Major repairs
			"parts_purchase": 0.8,  # Parts only
			"inspection": 0.5,  # Inspection only
		}

		base_points = float(transaction_amount)
		tier_multiplier = tier_multipliers.get(tier, 1.0)
		service_bonus = service_bonuses.get(transaction_type, 1.0)

		total_points = int(base_points * tier_multiplier * service_bonus)
		return total_points

	@staticmethod
	def add_loyalty_points(
		customer, points, transaction_reference=None, remarks=None, service_type="service", invoice_amount=0
	):
		"""Add loyalty points to customer's account"""
		if not customer or not points:
			return None

		loyalty_entry = frappe.new_doc("Customer Loyalty Points")
		loyalty_entry.customer = customer
		loyalty_entry.points = points
		loyalty_entry.transaction_type = "Earned"
		loyalty_entry.transaction_reference = transaction_reference
		loyalty_entry.service_type = service_type
		loyalty_entry.invoice_amount = invoice_amount
		loyalty_entry.remarks = remarks or f"Points earned: {points}"
		loyalty_entry.posting_date = datetime.date.today()
		loyalty_entry.insert()

		return loyalty_entry.name

	@staticmethod
	def redeem_loyalty_points(customer, points_to_redeem, transaction_reference=None, remarks=None):
		"""Redeem loyalty points from customer's account"""
		if not customer or not points_to_redeem:
			frappe.throw(_("Customer and points to redeem are required"))

		available_points = LoyaltyProgramManager.get_customer_points(customer)

		if points_to_redeem > available_points:
			frappe.throw(
				_("Insufficient loyalty points. Available: {0}, Requested: {1}").format(
					available_points, points_to_redeem
				)
			)

		# Create redemption entry
		loyalty_entry = frappe.new_doc("Customer Loyalty Points")
		loyalty_entry.customer = customer
		loyalty_entry.points = -points_to_redeem  # Negative for redemption
		loyalty_entry.transaction_type = "Redeemed"
		loyalty_entry.transaction_reference = transaction_reference
		loyalty_entry.remarks = remarks or f"Points redeemed: {points_to_redeem}"
		loyalty_entry.posting_date = datetime.date.today()
		loyalty_entry.insert()

		return loyalty_entry.name

	@staticmethod
	def get_available_rewards(customer_tier="Bronze", min_points=0):
		"""Get available rewards for customer tier and points"""
		rewards_catalog = {
			"Bronze": [
				{"name": "5% Service Discount", "points_required": 500, "value": "5% off next service"},
				{"name": "Free Car Wash", "points_required": 200, "value": "Complimentary car wash"},
				{"name": "Oil Change Discount", "points_required": 300, "value": "20% off oil change"},
			],
			"Silver": [
				{"name": "10% Service Discount", "points_required": 800, "value": "10% off next service"},
				{
					"name": "Free Basic Service",
					"points_required": 1000,
					"value": "Complimentary basic service",
				},
				{"name": "Priority Booking", "points_required": 600, "value": "Priority appointment booking"},
			],
			"Gold": [
				{"name": "15% Service Discount", "points_required": 1200, "value": "15% off next service"},
				{
					"name": "Free Tire Rotation",
					"points_required": 800,
					"value": "Complimentary tire rotation",
				},
				{"name": "Express Service", "points_required": 1000, "value": "Express service priority"},
			],
			"Platinum": [
				{"name": "20% Service Discount", "points_required": 1500, "value": "20% off next service"},
				{
					"name": "Free Annual Service",
					"points_required": 3000,
					"value": "Complimentary annual service",
				},
				{"name": "VIP Treatment", "points_required": 2000, "value": "VIP customer treatment"},
				{"name": "Extended Warranty", "points_required": 5000, "value": "6-month extended warranty"},
			],
		}

		# Get tier-specific rewards
		tier_rewards = rewards_catalog.get(customer_tier, [])

		# Filter by minimum points if specified
		if min_points > 0:
			available_rewards = [reward for reward in tier_rewards if reward["points_required"] <= min_points]
		else:
			available_rewards = tier_rewards

		return available_rewards

	@staticmethod
	def get_customer_loyalty_summary(customer):
		"""Get comprehensive loyalty program summary for customer"""
		if not customer:
			return {}

		current_points = LoyaltyProgramManager.get_customer_points(customer)
		tier = LoyaltyProgramManager.get_customer_tier(customer)
		available_rewards = LoyaltyProgramManager.get_available_rewards(tier, current_points)

		# Get recent transactions
		recent_transactions = frappe.get_list(
			"Customer Loyalty Points",
			filters={"customer": customer},
			fields=["posting_date", "points", "transaction_type", "remarks", "status"],
			order_by="posting_date desc",
			limit=10,
		)

		# Get next tier requirements
		tier_requirements = {
			"Bronze": {"points": 1000, "spending": 500},
			"Silver": {"points": 5000, "spending": 2000},
			"Gold": {"points": 10000, "spending": 5000},
			"Platinum": {"points": 10000, "spending": 5000},
		}

		next_tier = None
		if tier == "Bronze":
			next_tier = "Silver"
		elif tier == "Silver":
			next_tier = "Gold"
		elif tier == "Gold":
			next_tier = "Platinum"

		return {
			"customer": customer,
			"current_points": current_points,
			"current_tier": tier,
			"next_tier": next_tier,
			"tier_requirements": tier_requirements.get(next_tier, {}),
			"available_rewards": available_rewards,
			"recent_transactions": recent_transactions,
			"points_expiring_soon": LoyaltyProgramManager.get_expiring_points(customer),
		}

	@staticmethod
	def get_expiring_points(customer, days_ahead=30):
		"""Get points expiring within specified days"""
		if not customer:
			return 0

		expiry_date = datetime.date.today() + datetime.timedelta(days=days_ahead)

		expiring_points = (
			frappe.db.sql(
				"""
            SELECT COALESCE(SUM(points), 0) as expiring_points
            FROM `tabCustomer Loyalty Points`
            WHERE customer = %s
            AND expiry_date <= %s
            AND points > 0
            AND status = 'Active'
        """,
				[customer, expiry_date],
			)[0][0]
			or 0
		)

		return expiring_points


# Frappe API Functions for Loyalty Program


@frappe.whitelist()
def get_customer_loyalty_info(customer):
	"""API to get customer loyalty information"""
	return LoyaltyProgramManager.get_customer_loyalty_summary(customer)


@frappe.whitelist()
def calculate_invoice_points(customer, grand_total, service_type="service"):
	"""API to calculate points for invoice"""
	return LoyaltyProgramManager.calculate_points_earned(float(grand_total), customer, service_type)


@frappe.whitelist()
def apply_loyalty_points_to_invoice(sales_invoice, points_to_use):
	"""API to apply loyalty points discount to Sales Invoice"""
	try:
		# Get the sales invoice document
		invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice)

		# Validate invoice is in draft state
		if invoice_doc.docstatus != 0:
			return {"success": False, "message": _("Can only apply loyalty discount to draft invoices")}

		# Calculate discount amount (1 point = 0.01 OMR)
		points_to_use = int(points_to_use)
		discount_amount = points_to_use * 0.01

		# Ensure discount doesn't exceed invoice total
		if discount_amount > invoice_doc.grand_total:
			discount_amount = invoice_doc.grand_total
			points_to_use = int(discount_amount * 100)

		# Validate customer has enough points
		available_points = LoyaltyProgramManager.get_customer_points(invoice_doc.customer)
		if points_to_use > available_points:
			return {
				"success": False,
				"message": _("Insufficient points. Available: {0}, Requested: {1}").format(
					available_points, points_to_use
				),
			}

		# Apply discount to invoice
		invoice_doc.discount_amount = discount_amount
		invoice_doc.apply_discount_on = "Grand Total"

		# Save the invoice
		invoice_doc.save()

		# Create redemption entry
		redemption_entry = LoyaltyProgramManager.redeem_loyalty_points(
			invoice_doc.customer,
			points_to_use,
			invoice_doc.name,
			f"Loyalty discount applied to {invoice_doc.name}",
		)

		return {
			"success": True,
			"message": _("Loyalty discount applied successfully"),
			"discount_amount": discount_amount,
			"points_used": points_to_use,
			"redemption_entry": redemption_entry,
		}

	except Exception as e:
		frappe.log_error(f"Error applying loyalty discount: {e!s}")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def process_invoice_loyalty_points(sales_invoice):
	"""Process loyalty points when Sales Invoice is submitted"""
	try:
		invoice_doc = frappe.get_doc("Sales Invoice", sales_invoice)

		# Only process for submitted invoices
		if invoice_doc.docstatus != 1:
			return {"success": False, "message": _("Invoice must be submitted to earn points")}

		# Calculate points to be earned
		service_type = "service"  # Default, can be enhanced based on items
		points_earned = LoyaltyProgramManager.calculate_points_earned(
			invoice_doc.grand_total, invoice_doc.customer, service_type
		)

		if points_earned > 0:
			# Add loyalty points
			loyalty_entry = LoyaltyProgramManager.add_loyalty_points(
				invoice_doc.customer,
				points_earned,
				invoice_doc.name,
				f"Points earned from invoice {invoice_doc.name}",
				service_type,
				invoice_doc.grand_total,
			)

			return {
				"success": True,
				"message": _("Loyalty points added successfully"),
				"points_earned": points_earned,
				"loyalty_entry": loyalty_entry,
			}
		else:
			return {"success": False, "message": _("No points earned for this transaction")}

	except Exception as e:
		frappe.log_error(f"Error processing loyalty points: {e!s}")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_customer_rewards(customer):
	"""API to get available rewards for customer"""
	tier = LoyaltyProgramManager.get_customer_tier(customer)
	points = LoyaltyProgramManager.get_customer_points(customer)
	return LoyaltyProgramManager.get_available_rewards(tier, points)


@frappe.whitelist()
def redeem_reward(customer, reward_name, points_required):
	"""API to redeem a specific reward"""
	try:
		# Validate customer has enough points
		available_points = LoyaltyProgramManager.get_customer_points(customer)
		points_required = int(points_required)

		if points_required > available_points:
			return {
				"success": False,
				"message": _("Insufficient points. Available: {0}, Required: {1}").format(
					available_points, points_required
				),
			}

		# Create redemption entry
		redemption_entry = LoyaltyProgramManager.redeem_loyalty_points(
			customer, points_required, None, f"Reward redeemed: {reward_name}"
		)

		return {
			"success": True,
			"message": _("Reward redeemed successfully"),
			"redemption_entry": redemption_entry,
		}

	except Exception as e:
		frappe.log_error(f"Error redeeming reward: {e!s}")
		return {"success": False, "message": _("Error redeeming reward: {0}").format(str(e))}
