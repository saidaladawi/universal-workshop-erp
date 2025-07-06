import datetime

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerLoyaltyPoints(Document):
	def validate(self):
		"""Validate loyalty points entry"""
		self.validate_points_value()
		self.validate_customer()
		self.validate_expiry_date()
		self.set_processed_by()

	def validate_points_value(self):
		"""Validate points value based on transaction type"""
		if self.transaction_type == "Earned" and self.points <= 0:
			frappe.throw(_("Points must be positive for 'Earned' transactions"))

		if self.transaction_type in ["Redeemed", "Expired"] and self.points >= 0:
			frappe.throw(_("Points must be negative for 'Redeemed' or 'Expired' transactions"))

	def validate_customer(self):
		"""Validate customer exists and is active"""
		if not self.customer:
			frappe.throw(_("Customer is required"))

		customer_doc = frappe.get_doc("Customer", self.customer)
		if customer_doc.disabled:
			frappe.throw(_("Cannot process loyalty points for disabled customer"))

	def validate_expiry_date(self):
		"""Set expiry date for earned points"""
		if self.transaction_type == "Earned" and not self.expiry_date:
			# Set expiry to 1 year from posting date
			posting_date = self.posting_date or datetime.date.today()
			self.expiry_date = posting_date + datetime.timedelta(days=365)

	def set_processed_by(self):
		"""Set processed by current user"""
		if not self.processed_by:
			self.processed_by = frappe.session.user

	def before_save(self):
		"""Operations before saving"""
		self.validate_redemption_balance()

	def validate_redemption_balance(self):
		"""Validate customer has sufficient points for redemption"""
		if self.transaction_type == "Redeemed":
			# Get customer's available points (excluding this transaction)
			available_points = (
				frappe.db.sql(
					"""
                SELECT COALESCE(SUM(points), 0) as total_points
                FROM `tabCustomer Loyalty Points`
                WHERE customer = %s
                AND name != %s
                AND status = 'Active'
            """,
					[self.customer, self.name or ""],
				)[0][0]
				or 0
			)

			# Check if customer has enough points
			points_to_redeem = abs(self.points)
			if points_to_redeem > available_points:
				frappe.throw(
					_("Insufficient loyalty points. Available: {0}, Requested: {1}").format(
						available_points, points_to_redeem
					)
				)

	def after_insert(self):
		"""Operations after inserting"""
		self.update_customer_tier()

	def update_customer_tier(self):
		"""Update customer tier if points earned"""
		if self.transaction_type == "Earned":
			# Import here to avoid circular imports
			from universal_workshop.customer_management.loyalty_program import LoyaltyProgramManager

			# Get new tier
			new_tier = LoyaltyProgramManager.get_customer_tier(self.customer)

			# Update customer tier if it changed
			customer_doc = frappe.get_doc("Customer", self.customer)
			if hasattr(customer_doc, "loyalty_tier") and customer_doc.loyalty_tier != new_tier:
				customer_doc.loyalty_tier = new_tier
				customer_doc.save(ignore_permissions=True)

				# Create notification for tier upgrade
				if new_tier in ["Silver", "Gold", "Platinum"]:
					frappe.msgprint(
						_("Congratulations! Customer {0} has been upgraded to {1} tier!").format(
							customer_doc.customer_name, new_tier
						)
					)

	@frappe.whitelist()
	def expire_points(self):
		"""Mark points as expired"""
		if self.status == "Expired":
			frappe.throw(_("Points are already expired"))

		if self.transaction_type != "Earned":
			frappe.throw(_("Only earned points can be expired"))

		# Create expiry entry
		expiry_entry = frappe.new_doc("Customer Loyalty Points")
		expiry_entry.customer = self.customer
		expiry_entry.points = -self.points  # Negative to cancel out
		expiry_entry.transaction_type = "Expired"
		expiry_entry.transaction_reference = self.name
		expiry_entry.remarks = f"Points expired from {self.name}"
		expiry_entry.posting_date = datetime.date.today()
		expiry_entry.status = "Active"
		expiry_entry.insert()

		# Mark original entry as expired
		self.status = "Expired"
		self.save()

		return expiry_entry.name

	def get_formatted_points(self):
		"""Get formatted points with sign"""
		if self.points > 0:
			return f"+{self.points}"
		else:
			return str(self.points)

	def get_points_value_in_currency(self, conversion_rate=0.01):
		"""Get monetary value of points (1 point = 0.01 OMR by default)"""
		return abs(self.points) * conversion_rate
