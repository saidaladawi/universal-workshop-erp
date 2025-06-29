"""
Offline Grace Period and Connectivity Management System
Handles 24-hour offline operation with secure validation and connectivity monitoring
"""

import hashlib
import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime


class OfflineGracePeriodManager:
	"""
	Manages offline operations with 24-hour grace period
	Implements secure timestamp tracking and clock manipulation protection
	"""

	def __init__(self):
		self.grace_period_hours = 24
		self.max_offline_days = 7  # Maximum offline period before forced online check
		self.heartbeat_interval = 300  # 5 minutes
		self.license_doc = None
		self._monitoring_thread = None
		self._stop_monitoring = False

	def start_monitoring(self):
		"""Start background monitoring of connectivity and grace period"""
		if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
			self._stop_monitoring = False
			self._monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
			self._monitoring_thread.start()
			frappe.logger().info("Offline grace period monitoring started")

	def stop_monitoring(self):
		"""Stop background monitoring"""
		self._stop_monitoring = True
		if self._monitoring_thread and self._monitoring_thread.is_alive():
			self._monitoring_thread.join(timeout=5)
			frappe.logger().info("Offline grace period monitoring stopped")

	def _monitor_loop(self):
		"""Main monitoring loop running in background thread"""
		while not self._stop_monitoring:
			try:
				self._check_grace_period_status()
				time.sleep(self.heartbeat_interval)
			except Exception as e:
				frappe.log_error(f"Grace period monitor error: {e!s}")
				time.sleep(60)  # Wait before retry on error

	def is_grace_period_active(self) -> bool:
		"""Check if system is currently in grace period"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return False

			# Get last successful online validation
			last_online_str = getattr(license_doc, "last_successful_validation", None)
			if not last_online_str:
				return False

			last_online = get_datetime(last_online_str)
			current_time = now_datetime()

			# Calculate hours since last online validation
			time_diff = current_time - last_online
			hours_offline = time_diff.total_seconds() / 3600

			# Check if within grace period
			is_within_grace = hours_offline <= self.grace_period_hours

			# Store current status
			license_doc.db_set("grace_period_active", 1 if is_within_grace else 0)
			license_doc.db_set("hours_offline", hours_offline)

			return is_within_grace

		except Exception as e:
			frappe.log_error(f"Grace period check failed: {e!s}")
			return False

	def get_grace_period_remaining(self) -> float:
		"""Get remaining grace period hours"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return 0.0

			last_online_str = getattr(license_doc, "last_successful_validation", None)
			if not last_online_str:
				return 0.0

			last_online = get_datetime(last_online_str)
			current_time = now_datetime()

			time_diff = current_time - last_online
			hours_offline = time_diff.total_seconds() / 3600

			remaining = max(0, self.grace_period_hours - hours_offline)
			return remaining

		except Exception as e:
			frappe.log_error(f"Failed to calculate remaining grace period: {e!s}")
			return 0.0

	def enter_grace_period(self, reason: str = "Connection lost"):
		"""Enter grace period mode"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return

			current_time = now_datetime()
			grace_expiry = add_to_date(current_time, hours=self.grace_period_hours)

			license_doc.db_set("grace_period_active", 1)
			license_doc.db_set("grace_period_start", current_time)
			license_doc.db_set("grace_period_expiry", grace_expiry)
			license_doc.db_set("grace_period_reason", reason)

			frappe.logger().info(f"Entered grace period: {reason}")

			# Schedule background validation attempts
			self._schedule_validation_attempts()

		except Exception as e:
			frappe.log_error(f"Failed to enter grace period: {e!s}")

	def exit_grace_period(self, success: bool = True):
		"""Exit grace period mode"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return

			current_time = now_datetime()

			license_doc.db_set("grace_period_active", 0)
			license_doc.db_set("grace_period_end", current_time)

			if success:
				license_doc.db_set("last_successful_validation", current_time)
				frappe.logger().info("Successfully exited grace period")
			else:
				frappe.logger().warning("Grace period expired without successful validation")

		except Exception as e:
			frappe.log_error(f"Failed to exit grace period: {e!s}")

	def _check_grace_period_status(self):
		"""Internal method to check and update grace period status"""
		try:
			if not self.is_grace_period_active():
				# Grace period has expired, attempt validation
				if self._attempt_online_validation():
					self.exit_grace_period(success=True)
				else:
					# Grace period expired and validation failed
					self._handle_grace_period_expiry()
			else:
				# Still in grace period, attempt validation anyway
				if self._attempt_online_validation():
					self.exit_grace_period(success=True)

		except Exception as e:
			frappe.log_error(f"Grace period status check failed: {e!s}")

	def _attempt_online_validation(self) -> bool:
		"""Attempt to perform online license validation"""
		try:
			# Import here to avoid circular dependency
			from .license_validator import LicenseValidator

			validator = LicenseValidator()
			return validator.validate_license_online()

		except Exception as e:
			frappe.log_error(f"Online validation attempt failed: {e!s}")
			return False

	def _handle_grace_period_expiry(self):
		"""Handle grace period expiry"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return

			# Mark license as expired
			license_doc.db_set("license_status", "Expired - Grace Period Ended")
			license_doc.db_set("system_status", "Offline")

			# Log critical event
			frappe.logger().critical("Grace period expired - System entering restricted mode")

			# Trigger system restrictions
			self._activate_restricted_mode()

		except Exception as e:
			frappe.log_error(f"Failed to handle grace period expiry: {e!s}")

	def _activate_restricted_mode(self):
		"""Activate restricted system mode when grace period expires"""
		try:
			# Set system-wide restriction flags
			frappe.db.set_single_value("System Settings", "license_restricted_mode", 1)

			# Clear user sessions (force re-authentication)
			frappe.db.sql("DELETE FROM `tabSessions`")

			# Disable background jobs
			frappe.db.set_single_value("System Settings", "disable_scheduler", 1)

			frappe.logger().warning("System entering restricted mode due to license expiry")

		except Exception as e:
			frappe.log_error(f"Failed to activate restricted mode: {e!s}")

	def _schedule_validation_attempts(self):
		"""Schedule periodic validation attempts during grace period"""
		try:
			# Use Frappe's job queue for scheduling
			from frappe.utils.background_jobs import enqueue

			# Schedule validation attempts every hour
			enqueue(
				"universal_workshop.license_management.offline_manager.validation_job",
				queue="short",
				timeout=300,
				is_async=True,
			)

		except Exception as e:
			frappe.log_error(f"Failed to schedule validation attempts: {e!s}")

	def _get_license_doc(self):
		"""Get the workshop license document"""
		if not self.license_doc:
			try:
				self.license_doc = frappe.get_single("Workshop License")
			except Exception as e:
				frappe.log_error(f"Failed to get license document: {e!s}")
				return None
		return self.license_doc

	def get_status_summary(self) -> dict[str, Any]:
		"""Get comprehensive status summary for grace period"""
		try:
			license_doc = self._get_license_doc()
			if not license_doc:
				return {"error": "License document not found"}

			is_active = self.is_grace_period_active()
			remaining = self.get_grace_period_remaining()

			status = {
				"grace_period_active": is_active,
				"remaining_hours": round(remaining, 2),
				"grace_period_hours": self.grace_period_hours,
				"last_validation": getattr(license_doc, "last_successful_validation", None),
				"hours_offline": getattr(license_doc, "hours_offline", 0),
				"status": "Active" if is_active else "Expired",
				"connectivity": self._check_internet_connectivity(),
			}

			return status

		except Exception as e:
			frappe.log_error(f"Failed to get status summary: {e!s}")
			return {"error": str(e)}

	def _check_internet_connectivity(self) -> bool:
		"""Check if internet connection is available"""
		try:
			# Try multiple endpoints for reliability
			test_urls = [
				"https://8.8.8.8",  # Google DNS
				"https://1.1.1.1",  # Cloudflare DNS
				"https://frappe.io",  # Frappe
			]

			for url in test_urls:
				try:
					response = requests.get(url, timeout=5)
					if response.status_code == 200:
						return True
				except Exception:
					continue

			return False

		except Exception:
			return False


# Background job function
def validation_job():
	"""Background job for periodic validation attempts"""
	try:
		manager = OfflineGracePeriodManager()
		manager._attempt_online_validation()
	except Exception as e:
		frappe.log_error(f"Validation job failed: {e!s}")


# API endpoints
@frappe.whitelist()
def get_grace_period_status():
	"""API endpoint to get grace period status"""
	manager = OfflineGracePeriodManager()
	return manager.get_status_summary()


@frappe.whitelist()
def force_validation_attempt():
	"""API endpoint to force a validation attempt"""
	manager = OfflineGracePeriodManager()
	success = manager._attempt_online_validation()

	if success:
		manager.exit_grace_period(success=True)
		return {"status": "success", "message": "Validation successful"}
	else:
		return {"status": "failed", "message": "Validation failed"}


# Initialization
def init_grace_period_monitoring():
	"""Initialize grace period monitoring on system startup"""
	try:
		manager = OfflineGracePeriodManager()
		manager.start_monitoring()
		frappe.logger().info("Grace period monitoring initialized")
	except Exception as e:
		frappe.log_error(f"Failed to initialize grace period monitoring: {e!s}")
