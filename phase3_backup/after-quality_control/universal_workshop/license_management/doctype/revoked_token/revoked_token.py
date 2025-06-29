import hashlib
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, now_datetime


class RevokedToken(Document):
	"""
	Revoked Token DocType for tracking blacklisted JWT tokens
	Supports Arabic localization and automatic cleanup
	"""

	def validate(self):
		"""Validate token data before saving"""
		self.validate_token_data()
		self.validate_arabic_reason()
		self.set_hash_if_missing()

	def validate_token_data(self):
		"""Validate token JTI and expiration data"""
		if not self.token_jti:
			frappe.throw(_("Token JTI is required"))

		if len(self.token_jti) < 10:
			frappe.throw(_("Token JTI must be at least 10 characters"))

		# Validate original expiration is in the future (or recent past for grace period)
		if self.original_exp:
			exp_date = datetime.fromisoformat(str(self.original_exp).replace("Z", "+00:00"))
			current_time = datetime.now()

			# Allow tokens that expired up to 24 hours ago (for cleanup)
			grace_period = add_days(current_time, -1)
			if exp_date < grace_period:
				frappe.msgprint(_("Warning: Token already expired over 24 hours ago"))

	def validate_arabic_reason(self):
		"""Ensure Arabic reason is provided if Arabic is enabled"""
		if frappe.local.lang == "ar" and self.reason and not self.reason_ar:
			# Auto-translate if possible or prompt for Arabic reason
			frappe.msgprint(_("Arabic revocation reason is recommended"))

	def set_hash_if_missing(self):
		"""Generate token hash if not provided"""
		if not self.token_hash and self.token_jti:
			# Create SHA256 hash of JTI for additional security
			self.token_hash = hashlib.sha256(self.token_jti.encode()).hexdigest()[:32]

	def before_insert(self):
		"""Set automatic fields before insertion"""
		if not self.revoked_at:
			self.revoked_at = now_datetime()

		if not self.revoked_by:
			self.revoked_by = frappe.session.user

		# Log security event
		self.log_revocation_event()

	def log_revocation_event(self):
		"""Log token revocation as security event"""
		try:
			from universal_workshop.license_management.doctype.license_audit_log.license_audit_log import (
				create_audit_log,
			)

			event_data = {
				"token_jti": self.token_jti,
				"workshop_code": self.workshop_code,
				"revocation_reason": self.reason,
				"hardware_fingerprint": self.hardware_fingerprint,
				"revoked_by": self.revoked_by,
			}

			create_audit_log(
				event_type="token_revoked",
				severity="medium",
				message=f"JWT token revoked: {self.reason}",
				event_data=event_data,
				workshop_code=self.workshop_code,
			)

		except Exception as e:
			frappe.log_error(f"Failed to log token revocation: {e!s}", "Revoked Token Audit")

	@staticmethod
	def is_token_revoked(token_jti):
		"""Check if a token JTI is in the revoked list"""
		if not token_jti:
			return False

		return frappe.db.exists("Revoked Token", {"token_jti": token_jti})

	@staticmethod
	def revoke_token(
		token_jti, reason, reason_ar=None, workshop_code=None, hardware_fingerprint=None, original_exp=None
	):
		"""
		Revoke a token by adding it to the blacklist

		Args:
		    token_jti (str): JWT ID to revoke
		    reason (str): Reason for revocation
		    reason_ar (str, optional): Arabic reason
		    workshop_code (str, optional): Associated workshop
		    hardware_fingerprint (str, optional): Hardware fingerprint
		    original_exp (datetime, optional): Original token expiration

		Returns:
		    RevokedToken: Created revoked token document
		"""
		if RevokedToken.is_token_revoked(token_jti):
			frappe.throw(_("Token is already revoked"))

		revoked_token = frappe.new_doc("Revoked Token")
		revoked_token.update(
			{
				"token_jti": token_jti,
				"reason": reason,
				"reason_ar": reason_ar,
				"workshop_code": workshop_code,
				"hardware_fingerprint": hardware_fingerprint,
				"original_exp": original_exp,
				"revoked_by": frappe.session.user,
				"revoked_at": now_datetime(),
			}
		)

		revoked_token.insert()
		frappe.db.commit()

		return revoked_token

	@staticmethod
	def cleanup_expired_tokens():
		"""
		Clean up revoked tokens that are past their expiration + grace period
		This should be run daily via scheduler
		"""
		try:
			# Delete revoked tokens that expired more than 7 days ago
			cutoff_date = add_days(now_datetime(), -7)

			expired_tokens = frappe.get_all(
				"Revoked Token", filters={"original_exp": ["<", cutoff_date]}, pluck="name"
			)

			deleted_count = 0
			for token_name in expired_tokens:
				try:
					frappe.delete_doc("Revoked Token", token_name, force=True)
					deleted_count += 1
				except Exception as e:
					frappe.log_error(f"Failed to delete expired revoked token {token_name}: {e!s}")

			if deleted_count > 0:
				frappe.db.commit()
				frappe.logger().info(f"Cleaned up {deleted_count} expired revoked tokens")

			return deleted_count

		except Exception as e:
			frappe.log_error(f"Failed to cleanup expired revoked tokens: {e!s}", "Revoked Token Cleanup")
			return 0

	@staticmethod
	def get_revocation_stats(workshop_code=None):
		"""
		Get statistics about token revocations

		Args:
		    workshop_code (str, optional): Filter by workshop

		Returns:
		    dict: Revocation statistics
		"""
		filters = {}
		if workshop_code:
			filters["workshop_code"] = workshop_code

		# Get total revocations
		total_revoked = frappe.db.count("Revoked Token", filters)

		# Get revocations in last 24 hours
		recent_cutoff = add_days(now_datetime(), -1)
		recent_filters = dict(filters)
		recent_filters["revoked_at"] = [">=", recent_cutoff]
		recent_revoked = frappe.db.count("Revoked Token", recent_filters)

		# Get top revocation reasons
		reason_stats = frappe.db.sql(
			"""
            SELECT reason, COUNT(*) as count
            FROM `tabRevoked Token`
            WHERE {workshop_filter}
            GROUP BY reason
            ORDER BY count DESC
            LIMIT 5
        """.format(workshop_filter="workshop_code = %(workshop_code)s" if workshop_code else "1=1"),
			{"workshop_code": workshop_code} if workshop_code else {},
			as_dict=True,
		)

		return {
			"total_revoked": total_revoked,
			"recent_revoked": recent_revoked,
			"top_reasons": reason_stats,
			"workshop_code": workshop_code,
		}


# Frappe hooks for scheduled cleanup
def cleanup_expired_revoked_tokens():
	"""Daily cleanup function called by scheduler"""
	return RevokedToken.cleanup_expired_tokens()
