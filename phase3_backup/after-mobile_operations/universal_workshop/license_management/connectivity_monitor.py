"""
Connectivity Monitor System
Monitors network connectivity and manages automatic online validation when connection is restored
"""

import platform
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import requests

import frappe
from frappe import _
from frappe.utils import add_minutes, now_datetime


class ConnectivityMonitor:
	"""
	Monitors network connectivity and triggers online validation when connection is restored
	"""

	def __init__(self):
		self.check_interval = 300  # 5 minutes between checks
		self.quick_check_interval = 60  # 1 minute for quick checks
		self.connectivity_timeout = 10  # 10 seconds timeout for connectivity tests
		self.max_failures = 3  # Maximum consecutive failures before marking offline

		# Reliable endpoints for connectivity testing
		self.connectivity_endpoints = [
			"https://www.google.com",
			"https://www.cloudflare.com",
			"https://www.microsoft.com",
			"https://1.1.1.1",  # Cloudflare DNS
			"8.8.8.8",  # Google DNS
		]

		# Monitor state
		self.monitoring_active = {}  # workshop_code -> bool
		self.monitor_threads = {}  # workshop_code -> thread
		self.connectivity_state = {}  # workshop_code -> state data

	def start_monitoring(self, workshop_code: str) -> dict:
		"""
		Start connectivity monitoring for a workshop

		Args:
		    workshop_code (str): Workshop identifier

		Returns:
		    Dict: Monitoring start result
		"""
		try:
			if self.monitoring_active.get(workshop_code, False):
				return {
					"success": True,
					"message": "Monitoring already active",
					"workshop_code": workshop_code,
				}

			# Initialize state
			self.connectivity_state[workshop_code] = {
				"status": "unknown",
				"last_check": None,
				"consecutive_failures": 0,
				"total_checks": 0,
				"successful_checks": 0,
				"last_online": None,
				"check_history": [],
			}

			# Start monitoring thread
			self.monitoring_active[workshop_code] = True
			monitor_thread = threading.Thread(
				target=self._monitor_connectivity_loop, args=(workshop_code,), daemon=True
			)
			monitor_thread.start()
			self.monitor_threads[workshop_code] = monitor_thread

			# Log monitoring start
			self._log_connectivity_event(workshop_code, "monitoring_started", {})

			return {
				"success": True,
				"message": "Connectivity monitoring started",
				"workshop_code": workshop_code,
				"check_interval": self.check_interval,
			}

		except Exception as e:
			frappe.log_error(f"Failed to start connectivity monitoring: {e!s}", "Connectivity Monitor")
			return {"success": False, "error": f"Failed to start monitoring: {e!s}"}

	def stop_monitoring(self, workshop_code: str) -> dict:
		"""
		Stop connectivity monitoring for a workshop

		Args:
		    workshop_code (str): Workshop identifier

		Returns:
		    Dict: Monitoring stop result
		"""
		try:
			if not self.monitoring_active.get(workshop_code, False):
				return {
					"success": True,
					"message": "Monitoring was not active",
					"workshop_code": workshop_code,
				}

			# Stop monitoring
			self.monitoring_active[workshop_code] = False

			# Wait for thread to finish (with timeout)
			thread = self.monitor_threads.get(workshop_code)
			if thread and thread.is_alive():
				thread.join(timeout=5)

			# Clean up
			if workshop_code in self.monitor_threads:
				del self.monitor_threads[workshop_code]

			# Log final state
			final_state = self.connectivity_state.get(workshop_code, {})
			self._log_connectivity_event(workshop_code, "monitoring_stopped", final_state)

			return {
				"success": True,
				"message": "Connectivity monitoring stopped",
				"workshop_code": workshop_code,
				"final_state": final_state,
			}

		except Exception as e:
			frappe.log_error(f"Failed to stop connectivity monitoring: {e!s}", "Connectivity Monitor")
			return {"success": False, "error": f"Failed to stop monitoring: {e!s}"}

	def check_connectivity(self, quick_check: bool = False) -> dict:
		"""
		Perform immediate connectivity check

		Args:
		    quick_check (bool): Use quick check method

		Returns:
		    Dict: Connectivity status
		"""
		try:
			start_time = time.time()

			if quick_check:
				result = self._quick_connectivity_check()
			else:
				result = self._comprehensive_connectivity_check()

			check_duration = time.time() - start_time

			return {
				"connected": result["connected"],
				"method": "quick" if quick_check else "comprehensive",
				"response_time": round(check_duration, 2),
				"details": result.get("details", {}),
				"timestamp": now_datetime().isoformat(),
			}

		except Exception as e:
			frappe.log_error(f"Connectivity check failed: {e!s}", "Connectivity Monitor")
			return {"connected": False, "error": str(e), "timestamp": now_datetime().isoformat()}

	def get_connectivity_status(self, workshop_code: str) -> dict:
		"""Get current connectivity status for workshop"""
		state = self.connectivity_state.get(workshop_code, {})
		monitoring_active = self.monitoring_active.get(workshop_code, False)

		return {
			"workshop_code": workshop_code,
			"monitoring_active": monitoring_active,
			"current_status": state.get("status", "unknown"),
			"last_check": state.get("last_check"),
			"consecutive_failures": state.get("consecutive_failures", 0),
			"total_checks": state.get("total_checks", 0),
			"successful_checks": state.get("successful_checks", 0),
			"success_rate": round(
				(state.get("successful_checks", 0) / max(state.get("total_checks", 1), 1)) * 100, 2
			),
			"last_online": state.get("last_online"),
			"recent_history": state.get("check_history", [])[-10:],  # Last 10 checks
		}

	def _monitor_connectivity_loop(self, workshop_code: str):
		"""Main monitoring loop for a workshop"""
		try:
			while self.monitoring_active.get(workshop_code, False):
				# Perform connectivity check
				check_result = self._comprehensive_connectivity_check()

				# Update state
				self._update_connectivity_state(workshop_code, check_result)

				# Handle connectivity changes
				if check_result["connected"]:
					self._handle_connection_restored(workshop_code)
				else:
					self._handle_connection_lost(workshop_code)

				# Sleep until next check
				time.sleep(self.check_interval)

		except Exception as e:
			frappe.log_error(
				f"Connectivity monitoring loop failed for {workshop_code}: {e!s}", "Connectivity Monitor"
			)
		finally:
			# Clean up when loop exits
			if workshop_code in self.monitoring_active:
				self.monitoring_active[workshop_code] = False

	def _quick_connectivity_check(self) -> dict:
		"""Quick connectivity check using DNS resolution"""
		try:
			# Try to resolve Google's DNS
			socket.setdefaulttimeout(3)
			socket.gethostbyname("google.com")

			return {"connected": True, "method": "dns_resolution", "details": {"endpoint": "google.com"}}

		except OSError:
			return {
				"connected": False,
				"method": "dns_resolution",
				"details": {"error": "DNS resolution failed"},
			}

	def _comprehensive_connectivity_check(self) -> dict:
		"""Comprehensive connectivity check using multiple endpoints"""
		successful_endpoints = []
		failed_endpoints = []

		# Test multiple endpoints concurrently
		with ThreadPoolExecutor(max_workers=3) as executor:
			future_to_endpoint = {
				executor.submit(self._test_endpoint, endpoint): endpoint
				for endpoint in self.connectivity_endpoints[:3]  # Test first 3
			}

			for future in as_completed(future_to_endpoint, timeout=self.connectivity_timeout):
				endpoint = future_to_endpoint[future]
				try:
					result = future.result()
					if result["success"]:
						successful_endpoints.append(
							{"endpoint": endpoint, "response_time": result["response_time"]}
						)
					else:
						failed_endpoints.append(
							{"endpoint": endpoint, "error": result.get("error", "Unknown error")}
						)
				except Exception as e:
					failed_endpoints.append({"endpoint": endpoint, "error": str(e)})

		# Consider connected if at least one endpoint succeeded
		connected = len(successful_endpoints) > 0

		return {
			"connected": connected,
			"method": "multi_endpoint",
			"details": {
				"successful_endpoints": successful_endpoints,
				"failed_endpoints": failed_endpoints,
				"success_count": len(successful_endpoints),
				"total_tested": len(self.connectivity_endpoints[:3]),
			},
		}

	def _test_endpoint(self, endpoint: str) -> dict:
		"""Test connectivity to a specific endpoint"""
		start_time = time.time()

		try:
			if endpoint.startswith("http"):
				# HTTP endpoint test
				response = requests.get(endpoint, timeout=self.connectivity_timeout, stream=True)
				success = response.status_code == 200
			else:
				# IP address ping test
				success = self._ping_endpoint(endpoint)

			response_time = round((time.time() - start_time) * 1000, 2)  # milliseconds

			return {"success": success, "response_time": response_time, "endpoint": endpoint}

		except Exception as e:
			return {
				"success": False,
				"error": str(e),
				"endpoint": endpoint,
				"response_time": round((time.time() - start_time) * 1000, 2),
			}

	def _ping_endpoint(self, ip_address: str) -> bool:
		"""Ping an IP address to test connectivity"""
		try:
			# Platform-specific ping command
			if platform.system().lower() == "windows":
				cmd = ["ping", "-n", "1", "-w", "3000", ip_address]
			else:
				cmd = ["ping", "-c", "1", "-W", "3", ip_address]

			result = subprocess.run(cmd, capture_output=True, timeout=5)
			return result.returncode == 0

		except (subprocess.TimeoutExpired, subprocess.SubprocessError):
			return False

	def _update_connectivity_state(self, workshop_code: str, check_result: dict):
		"""Update connectivity state based on check result"""
		state = self.connectivity_state.get(workshop_code, {})

		# Update counters
		state["total_checks"] = state.get("total_checks", 0) + 1
		state["last_check"] = now_datetime()

		if check_result["connected"]:
			state["status"] = "online"
			state["consecutive_failures"] = 0
			state["successful_checks"] = state.get("successful_checks", 0) + 1
			state["last_online"] = now_datetime()
		else:
			state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
			if state["consecutive_failures"] >= self.max_failures:
				state["status"] = "offline"
			else:
				state["status"] = "unstable"

		# Update history (keep last 50 checks)
		history_entry = {
			"timestamp": now_datetime().isoformat(),
			"connected": check_result["connected"],
			"details": check_result.get("details", {}),
		}

		history = state.get("check_history", [])
		history.append(history_entry)
		state["check_history"] = history[-50:]  # Keep last 50

		self.connectivity_state[workshop_code] = state

	def _handle_connection_restored(self, workshop_code: str):
		"""Handle when connection is restored"""
		state = self.connectivity_state.get(workshop_code, {})

		# Check if this is a transition from offline to online
		if state.get("status") == "online" and state.get("consecutive_failures", 0) == 0:
			# Check if we previously had failures (restoration event)
			if state.get("total_checks", 0) > 0 and state.get("successful_checks", 0) < state.get(
				"total_checks", 0
			):
				self._trigger_online_validation(workshop_code)

	def _handle_connection_lost(self, workshop_code: str):
		"""Handle when connection is lost"""
		state = self.connectivity_state.get(workshop_code, {})

		# Log significant connectivity loss
		if state.get("consecutive_failures", 0) == self.max_failures:
			self._log_connectivity_event(
				workshop_code,
				"connection_lost",
				{
					"consecutive_failures": state["consecutive_failures"],
					"last_online": state.get("last_online"),
				},
			)

	def _trigger_online_validation(self, workshop_code: str):
		"""Trigger online license validation when connection is restored"""
		try:
			# Get active offline session
			from universal_workshop.license_management.doctype.offline_session.offline_session import (
				get_active_session,
			)

			offline_session = get_active_session(workshop_code)

			if offline_session:
				# Attempt online validation
				self._attempt_online_validation(workshop_code, offline_session)

		except Exception as e:
			frappe.log_error(f"Failed to trigger online validation: {e!s}", "Connectivity Monitor")

	def _attempt_online_validation(self, workshop_code: str, offline_session):
		"""Attempt online license validation"""
		try:
			from universal_workshop.license_management.offline_manager import OfflineGracePeriodManager

			# End offline session with online validation
			manager = OfflineGracePeriodManager()
			result = manager.end_offline_session(workshop_code, online_validation_success=True)

			if result.get("success"):
				self._log_connectivity_event(
					workshop_code,
					"online_validation_success",
					{
						"session_id": offline_session.name,
						"offline_duration_hours": result.get("session_duration_hours", 0),
					},
				)
			else:
				self._log_connectivity_event(
					workshop_code,
					"online_validation_failed",
					{"session_id": offline_session.name, "error": result.get("error", "Unknown error")},
				)

		except Exception as e:
			frappe.log_error(f"Online validation attempt failed: {e!s}", "Connectivity Monitor")

	def _log_connectivity_event(self, workshop_code: str, event_type: str, event_data: dict):
		"""Log connectivity events for audit"""
		try:
			from universal_workshop.license_management.doctype.license_audit_log.license_audit_log import (
				create_audit_log,
			)

			create_audit_log(
				event_type=event_type,
				severity="low" if "success" in event_type else "medium",
				message=f"Connectivity event: {event_type}",
				event_data=event_data,
				workshop_code=workshop_code,
			)

		except Exception as e:
			frappe.log_error(f"Failed to log connectivity event: {e!s}", "Connectivity Event Audit")


# Singleton instance for global access
_connectivity_monitor = None


def get_connectivity_monitor() -> ConnectivityMonitor:
	"""Get singleton connectivity monitor instance"""
	global _connectivity_monitor
	if _connectivity_monitor is None:
		_connectivity_monitor = ConnectivityMonitor()
	return _connectivity_monitor


# Frappe whitelist methods
@frappe.whitelist()
def start_connectivity_monitoring(workshop_code):
	"""API method to start connectivity monitoring"""
	monitor = get_connectivity_monitor()
	return monitor.start_monitoring(workshop_code)


@frappe.whitelist()
def stop_connectivity_monitoring(workshop_code):
	"""API method to stop connectivity monitoring"""
	monitor = get_connectivity_monitor()
	return monitor.stop_monitoring(workshop_code)


@frappe.whitelist()
def check_connectivity_status(workshop_code):
	"""API method to check connectivity status"""
	monitor = get_connectivity_monitor()
	return monitor.get_connectivity_status(workshop_code)


@frappe.whitelist()
def perform_connectivity_check(quick_check=False):
	"""API method to perform immediate connectivity check"""
	monitor = get_connectivity_monitor()
	return monitor.check_connectivity(quick_check=quick_check)
