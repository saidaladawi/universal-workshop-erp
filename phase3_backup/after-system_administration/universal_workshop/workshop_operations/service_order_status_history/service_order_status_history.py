# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, time_diff_in_hours, time_diff_in_seconds


class ServiceOrderStatusHistory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		changed_by: DF.Link
		changed_by_name: DF.Data | None
		changed_on: DF.Datetime
		duration_in_status: DF.Data | None
		notes: DF.Text | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		status: DF.Data
		status_ar: DF.Data | None
	# end: auto-generated types

	def validate(self):
		"""Validate Status History entry"""
		self.validate_status()
		self.validate_changed_by()
		self.validate_changed_on()
		self.validate_arabic_fields()

	def validate_status(self):
		"""Validate status value"""
		if not self.status:
			frappe.throw(_("Status is required"))

		# Define valid statuses for service orders
		valid_statuses = [
			"Draft",
			"Scheduled",
			"In Progress",
			"Quality Check",
			"Completed",
			"Delivered",
			"Cancelled",
			"On Hold",
		]

		if self.status not in valid_statuses:
			frappe.msgprint(
				_("Status '{0}' is not in the standard list. Please verify.").format(self.status),
				indicator="orange",
			)

	def validate_changed_by(self):
		"""Validate user who changed the status"""
		if not self.changed_by:
			self.changed_by = frappe.session.user

		# Check if user is active
		user_active = frappe.db.get_value("User", self.changed_by, "enabled")
		if not user_active:
			frappe.throw(_("User {0} is not active").format(self.changed_by))

	def validate_changed_on(self):
		"""Validate change timestamp"""
		if not self.changed_on:
			self.changed_on = frappe.utils.now()

		# Check if timestamp is not in the future
		current_time = get_datetime(frappe.utils.now())
		change_time = get_datetime(self.changed_on)

		if change_time > current_time:
			frappe.throw(_("Change timestamp cannot be in the future"))

	def validate_arabic_fields(self):
		"""Validate Arabic field content"""
		if self.status_ar and not self.is_arabic_text(self.status_ar):
			frappe.msgprint(_("Status Arabic should contain Arabic characters"), indicator="orange")

	def is_arabic_text(self, text):
		"""Check if text contains Arabic characters"""
		if not text:
			return False
		arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
		return bool(arabic_pattern.search(text))

	def before_save(self):
		"""Actions before saving"""
		self.set_user_details()
		self.set_status_arabic()
		self.calculate_duration()

	def set_user_details(self):
		"""Auto-populate user details"""
		if self.changed_by and not self.changed_by_name:
			user_doc = frappe.get_doc("User", self.changed_by)
			self.changed_by_name = user_doc.full_name or user_doc.first_name

	def set_status_arabic(self):
		"""Auto-set Arabic status if available"""
		if self.status and not self.status_ar:
			# Common status translations
			status_translations = {
				"Draft": "مسودة",
				"Scheduled": "مجدول",
				"In Progress": "قيد التنفيذ",
				"Quality Check": "فحص الجودة",
				"Completed": "مكتمل",
				"Delivered": "تم التسليم",
				"Cancelled": "ملغى",
				"On Hold": "معلق",
				"Waiting for Parts": "في انتظار القطع",
				"Customer Approval": "موافقة العميل",
				"Ready for Pickup": "جاهز للاستلام",
				"Invoiced": "تم إصدار الفاتورة",
				"Paid": "تم الدفع",
			}

			if self.status in status_translations:
				self.status_ar = status_translations[self.status]

	def calculate_duration(self):
		"""Calculate duration in previous status"""
		if not self.changed_on:
			return

		# Get parent service order to find previous status change
		parent_doc = frappe.get_doc(self.parenttype, self.parent)

		# Find previous status history entry
		status_history = getattr(parent_doc, self.parentfield, [])
		current_index = None

		# Find current entry index
		for i, entry in enumerate(status_history):
			if (
				entry.status == self.status
				and entry.changed_on == self.changed_on
				and entry.changed_by == self.changed_by
			):
				current_index = i
				break

		if current_index is not None and current_index > 0:
			# Get previous entry
			previous_entry = status_history[current_index - 1]
			previous_time = get_datetime(previous_entry.changed_on)
			current_time = get_datetime(self.changed_on)

			# Calculate duration
			duration_seconds = time_diff_in_seconds(current_time, previous_time)
			duration_display = self.format_duration(duration_seconds)

			# Update previous entry's duration
			previous_entry.duration_in_status = duration_display

	def format_duration(self, seconds):
		"""Format duration in human-readable format"""
		if seconds < 60:
			return f"{int(seconds)} seconds"
		elif seconds < 3600:
			minutes = int(seconds / 60)
			return f"{minutes} minutes"
		elif seconds < 86400:
			hours = int(seconds / 3600)
			minutes = int((seconds % 3600) / 60)
			if minutes > 0:
				return f"{hours}h {minutes}m"
			return f"{hours} hours"
		else:
			days = int(seconds / 86400)
			hours = int((seconds % 86400) / 3600)
			if hours > 0:
				return f"{days}d {hours}h"
			return f"{days} days"

	def format_duration_arabic(self, seconds):
		"""Format duration in Arabic"""
		if seconds < 60:
			secs = self.convert_to_arabic_numerals(str(int(seconds)))
			return f"{secs} ثانية"
		elif seconds < 3600:
			minutes = int(seconds / 60)
			mins = self.convert_to_arabic_numerals(str(minutes))
			return f"{mins} دقيقة"
		elif seconds < 86400:
			hours = int(seconds / 3600)
			minutes = int((seconds % 3600) / 60)
			hrs = self.convert_to_arabic_numerals(str(hours))
			if minutes > 0:
				mins = self.convert_to_arabic_numerals(str(minutes))
				return f"{hrs} ساعة {mins} دقيقة"
			return f"{hrs} ساعة"
		else:
			days = int(seconds / 86400)
			hours = int((seconds % 86400) / 3600)
			d = self.convert_to_arabic_numerals(str(days))
			if hours > 0:
				h = self.convert_to_arabic_numerals(str(hours))
				return f"{d} يوم {h} ساعة"
			return f"{d} يوم"

	def convert_to_arabic_numerals(self, text):
		"""Convert Western numerals to Arabic-Indic numerals"""
		arabic_numerals = {
			"0": "٠",
			"1": "١",
			"2": "٢",
			"3": "٣",
			"4": "٤",
			"5": "٥",
			"6": "٦",
			"7": "٧",
			"8": "٨",
			"9": "٩",
		}

		for western, arabic in arabic_numerals.items():
			text = text.replace(western, arabic)
		return text

	@frappe.whitelist()
	def get_status_analytics(self):
		"""Get analytics for this status change"""
		if not self.changed_on:
			return {}

		# Get time of day information
		change_time = get_datetime(self.changed_on)
		hour = change_time.hour

		# Determine time period
		if 6 <= hour < 12:
			time_period = "Morning"
			time_period_ar = "صباح"
		elif 12 <= hour < 18:
			time_period = "Afternoon"
			time_period_ar = "بعد الظهر"
		elif 18 <= hour < 22:
			time_period = "Evening"
			time_period_ar = "مساء"
		else:
			time_period = "Night"
			time_period_ar = "ليل"

		# Get day of week
		day_of_week = change_time.strftime("%A")
		day_names_ar = {
			"Monday": "الاثنين",
			"Tuesday": "الثلاثاء",
			"Wednesday": "الأربعاء",
			"Thursday": "الخميس",
			"Friday": "الجمعة",
			"Saturday": "السبت",
			"Sunday": "الأحد",
		}

		return {
			"change_time": self.changed_on,
			"hour": hour,
			"time_period": time_period,
			"time_period_ar": time_period_ar,
			"day_of_week": day_of_week,
			"day_of_week_ar": day_names_ar.get(day_of_week, day_of_week),
			"is_weekend": day_of_week in ["Friday", "Saturday"],
			"is_business_hours": 8 <= hour <= 17,
			"changed_by": self.changed_by,
			"changed_by_name": self.changed_by_name,
		}

	def get_formatted_change_time(self, language="en"):
		"""Get formatted change time in specified language"""
		if not self.changed_on:
			return ""

		change_time = get_datetime(self.changed_on)

		if language == "ar":
			# Arabic date format
			day = self.convert_to_arabic_numerals(str(change_time.day))
			month = change_time.strftime("%B")
			year = self.convert_to_arabic_numerals(str(change_time.year))
			time = self.convert_to_arabic_numerals(change_time.strftime("%I:%M %p"))

			# Arabic month names
			months_ar = {
				"January": "يناير",
				"February": "فبراير",
				"March": "مارس",
				"April": "أبريل",
				"May": "مايو",
				"June": "يونيو",
				"July": "يوليو",
				"August": "أغسطس",
				"September": "سبتمبر",
				"October": "أكتوبر",
				"November": "نوفمبر",
				"December": "ديسمبر",
			}

			month_ar = months_ar.get(month, month)
			return f"{day} {month_ar} {year} - {time}"
		else:
			return change_time.strftime("%d %B %Y - %I:%M %p")

	@staticmethod
	def create_status_change(parent_doctype, parent_name, new_status, notes=None, user=None):
		"""Create a new status history entry"""
		if not user:
			user = frappe.session.user

		# Get the parent document
		parent_doc = frappe.get_doc(parent_doctype, parent_name)

		# Create new status history entry
		status_entry = {
			"status": new_status,
			"changed_by": user,
			"changed_on": frappe.utils.now(),
			"notes": notes or "",
		}

		# Add to parent document's status history
		parent_doc.append("status_history", status_entry)
		parent_doc.save()

		return status_entry
