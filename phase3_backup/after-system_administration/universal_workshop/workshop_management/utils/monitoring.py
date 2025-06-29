# Copyright (c) 2024, Said Al-Adawi and contributors
# For license information, please see license.txt

import json
import time
from datetime import datetime

import frappe
from frappe import _


class OnboardingMonitor:
	"""Monitor and log onboarding process performance and issues"""

	def __init__(self):
		self.log_entries = []
		self.start_time = None
		self.performance_metrics = {}

	def start_monitoring(self, progress_id):
		"""Start monitoring an onboarding session"""
		self.start_time = time.time()
		self.progress_id = progress_id

		self.log_event(
			"onboarding_started",
			{
				"progress_id": progress_id,
				"user": frappe.session.user,
				"timestamp": datetime.now().isoformat(),
			},
		)

	def log_step_completion(self, step, duration, data_size):
		"""Log completion of a wizard step"""
		self.log_event(
			"step_completed",
			{
				"step": step,
				"duration_seconds": duration,
				"data_size_bytes": data_size,
				"timestamp": datetime.now().isoformat(),
			},
		)

		# Track performance metrics
		if step not in self.performance_metrics:
			self.performance_metrics[step] = []
		self.performance_metrics[step].append(duration)

	def log_validation_error(self, step, field, error_message):
		"""Log validation errors for analysis"""
		self.log_event(
			"validation_error",
			{
				"step": step,
				"field": field,
				"error": error_message,
				"user": frappe.session.user,
				"timestamp": datetime.now().isoformat(),
			},
		)

	def log_completion(self, workshop_profile_id, total_duration):
		"""Log successful completion of onboarding"""
		self.log_event(
			"onboarding_completed",
			{
				"workshop_profile_id": workshop_profile_id,
				"total_duration_seconds": total_duration,
				"user": frappe.session.user,
				"timestamp": datetime.now().isoformat(),
				"performance_metrics": self.performance_metrics,
			},
		)

		# Save to database for analytics
		self.save_performance_data()

	def log_abandonment(self, step, duration):
		"""Log when a user abandons the onboarding process"""
		self.log_event(
			"onboarding_abandoned",
			{
				"abandoned_at_step": step,
				"duration_before_abandonment": duration,
				"user": frappe.session.user,
				"timestamp": datetime.now().isoformat(),
			},
		)

	def log_event(self, event_type, data):
		"""Generic event logging"""
		log_entry = {
			"event_type": event_type,
			"progress_id": getattr(self, "progress_id", None),
			"data": data,
			"session_id": frappe.session.sid,
			"user_agent": frappe.request.headers.get("User-Agent", ""),
			"ip_address": frappe.local.request_ip,
		}

		self.log_entries.append(log_entry)

		# Also log to Frappe's error log for critical events
		if event_type in ["validation_error", "onboarding_abandoned"]:
			frappe.log_error(title=f"Onboarding {event_type}", message=json.dumps(log_entry, indent=2))

	def save_performance_data(self):
		"""Save performance data to database for analytics"""
		try:
			performance_doc = frappe.new_doc("Onboarding Performance Log")
			performance_doc.progress_id = self.progress_id
			performance_doc.user = frappe.session.user
			performance_doc.total_duration = time.time() - self.start_time if self.start_time else 0
			performance_doc.log_data = json.dumps(self.log_entries)
			performance_doc.performance_metrics = json.dumps(self.performance_metrics)
			performance_doc.session_id = frappe.session.sid
			performance_doc.completion_date = datetime.now()
			performance_doc.insert()
			frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Error saving performance data: {e!s}")

	def get_performance_summary(self):
		"""Get performance summary for current session"""
		if not self.start_time:
			return None

		total_duration = time.time() - self.start_time

		summary = {
			"total_duration": total_duration,
			"steps_completed": len(self.performance_metrics),
			"average_step_duration": sum(
				[sum(durations) / len(durations) for durations in self.performance_metrics.values()]
			)
			/ len(self.performance_metrics)
			if self.performance_metrics
			else 0,
			"validation_errors": len(
				[entry for entry in self.log_entries if entry["event_type"] == "validation_error"]
			),
			"performance_grade": self.calculate_performance_grade(total_duration),
		}

		return summary

	def calculate_performance_grade(self, total_duration):
		"""Calculate performance grade based on duration"""
		if total_duration < 300:  # Less than 5 minutes
			return "A"
		elif total_duration < 600:  # Less than 10 minutes
			return "B"
		elif total_duration < 1200:  # Less than 20 minutes
			return "C"
		elif total_duration < 1800:  # Less than 30 minutes (requirement)
			return "D"
		else:
			return "F"  # Failed performance requirement


@frappe.whitelist()
def get_onboarding_analytics():
	"""Get analytics data for onboarding performance"""

	# Get completion rates
	total_started = frappe.db.count("Onboarding Progress")
	total_completed = frappe.db.count("Workshop Profile")
	completion_rate = (total_completed / total_started * 100) if total_started > 0 else 0

	# Get average completion time
	performance_logs = frappe.get_list(
		"Onboarding Performance Log", fields=["total_duration"], filters={"total_duration": [">", 0]}
	)

	avg_duration = (
		sum([log.total_duration for log in performance_logs]) / len(performance_logs)
		if performance_logs
		else 0
	)

	# Get common validation errors
	error_logs = frappe.db.sql(
		"""
        SELECT log_data
        FROM `tabOnboarding Performance Log`
        WHERE log_data LIKE '%validation_error%'
        LIMIT 100
    """,
		as_dict=True,
	)

	error_analysis = analyze_common_errors(error_logs)

	# Get abandonment points
	abandonment_analysis = analyze_abandonment_points()

	return {
		"completion_rate": completion_rate,
		"average_duration_minutes": avg_duration / 60,
		"total_sessions": total_started,
		"completed_sessions": total_completed,
		"common_errors": error_analysis,
		"abandonment_points": abandonment_analysis,
		"performance_grade_distribution": get_performance_grade_distribution(),
	}


def analyze_common_errors(error_logs):
	"""Analyze common validation errors"""
	error_counts = {}

	for log in error_logs:
		try:
			log_data = json.loads(log.log_data)
			for entry in log_data:
				if entry["event_type"] == "validation_error":
					field = entry["data"].get("field", "unknown")
					error_counts[field] = error_counts.get(field, 0) + 1
		except Exception:
			continue

	return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]


def analyze_abandonment_points():
	"""Analyze where users commonly abandon the process"""
	abandonment_data = frappe.db.sql(
		"""
        SELECT log_data
        FROM `tabOnboarding Performance Log`
        WHERE log_data LIKE '%onboarding_abandoned%'
        LIMIT 100
    """,
		as_dict=True,
	)

	abandonment_points = {}

	for log in abandonment_data:
		try:
			log_data = json.loads(log.log_data)
			for entry in log_data:
				if entry["event_type"] == "onboarding_abandoned":
					step = entry["data"].get("abandoned_at_step", "unknown")
					abandonment_points[step] = abandonment_points.get(step, 0) + 1
		except Exception:
			continue

	return abandonment_points


def get_performance_grade_distribution():
	"""Get distribution of performance grades"""
	performance_logs = frappe.get_list("Onboarding Performance Log", fields=["total_duration"])

	grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

	monitor = OnboardingMonitor()
	for log in performance_logs:
		grade = monitor.calculate_performance_grade(log.total_duration)
		grade_distribution[grade] += 1

	return grade_distribution


@frappe.whitelist()
def create_performance_report():
	"""Create a comprehensive performance report"""
	analytics = get_onboarding_analytics()

	report = f"""
# Universal Workshop Onboarding Performance Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics
- **Completion Rate**: {analytics["completion_rate"]:.1f}%
- **Average Duration**: {analytics["average_duration_minutes"]:.1f} minutes
- **Total Sessions**: {analytics["total_sessions"]}
- **Completed Sessions**: {analytics["completed_sessions"]}

## Performance Grade Distribution
- Grade A (< 5 min): {analytics["performance_grade_distribution"]["A"]}
- Grade B (5-10 min): {analytics["performance_grade_distribution"]["B"]}
- Grade C (10-20 min): {analytics["performance_grade_distribution"]["C"]}
- Grade D (20-30 min): {analytics["performance_grade_distribution"]["D"]}
- Grade F (> 30 min): {analytics["performance_grade_distribution"]["F"]}

## Common Validation Errors
"""

	for field, count in analytics["common_errors"]:
		report += f"- {field}: {count} errors\n"

	report += "\n## Abandonment Analysis\n"
	for step, count in analytics["abandonment_points"].items():
		report += f"- {step}: {count} abandonments\n"

	return report


# Global monitor instance for session tracking
current_monitor = None


def get_or_create_monitor():
	"""Get or create monitor for current session"""
	global current_monitor
	if current_monitor is None:
		current_monitor = OnboardingMonitor()
	return current_monitor
