"""
Hardware Fingerprinting System for Universal Workshop ERP
Provides cross-platform hardware identification with security and tolerance features
"""

import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _


class HardwareFingerprintGenerator:
	"""
	Generates unique hardware fingerprints for license binding
	Supports Windows, macOS, and Linux with tolerance for minor changes
	"""

	def __init__(self):
		self.os_type = platform.system().lower()
		self.supported_components = [
			"cpu_info",
			"motherboard_id",
			"mac_addresses",
			"disk_serial",
			"system_uuid",
			"bios_info",
		]

	def generate_fingerprint(self, include_volatile=False) -> dict:
		"""
		Generate comprehensive hardware fingerprint

		Args:
		    include_volatile (bool): Include components that may change (like USB devices)

		Returns:
		    Dict: Hardware fingerprint data with hash and components
		"""
		try:
			# Collect hardware components
			components = {}

			# Core stable components (required for fingerprint)
			components["cpu_info"] = self._get_cpu_info()
			components["motherboard_id"] = self._get_motherboard_id()
			components["mac_addresses"] = self._get_mac_addresses()
			components["system_uuid"] = self._get_system_uuid()
			components["bios_info"] = self._get_bios_info()

			# Optional stable components
			if include_volatile:
				components["disk_serial"] = self._get_disk_serial()

			# Remove None values and normalize
			components = {k: v for k, v in components.items() if v is not None}
			components = self._normalize_components(components)

			# Generate primary hash (stable components only)
			primary_hash = self._generate_primary_hash(components)

			# Generate secondary hash (with tolerance)
			secondary_hash = self._generate_tolerance_hash(components)

			# Create fingerprint record
			fingerprint_data = {
				"primary_hash": primary_hash,
				"secondary_hash": secondary_hash,
				"components": components,
				"os_type": self.os_type,
				"generated_at": datetime.utcnow().isoformat(),
				"version": "1.0",
			}

			# Log fingerprint generation
			self._log_fingerprint_event(fingerprint_data)

			return fingerprint_data

		except Exception as e:
			frappe.log_error(f"Hardware fingerprint generation failed: {e!s}", "Hardware Fingerprint")
			return self._generate_fallback_fingerprint()

	def _get_cpu_info(self) -> str | None:
		"""Get CPU information cross-platform"""
		try:
			if self.os_type == "windows":
				# Windows - use wmic
				result = subprocess.run(
					["wmic", "cpu", "get", "ProcessorId,Name", "/format:csv"],
					capture_output=True,
					text=True,
					timeout=10,
				)

				if result.returncode == 0:
					lines = result.stdout.strip().split("\n")
					for line in lines:
						if "ProcessorId" in line and "," in line:
							parts = line.split(",")
							if len(parts) >= 3:
								return f"{parts[1]}_{parts[2]}".strip()

			elif self.os_type == "darwin":
				# macOS - use system_profiler
				result = subprocess.run(
					["system_profiler", "SPHardwareDataType"], capture_output=True, text=True, timeout=10
				)

				if result.returncode == 0:
					# Extract CPU info from output
					cpu_name = ""
					cpu_speed = ""
					for line in result.stdout.split("\n"):
						if "Processor Name" in line:
							cpu_name = line.split(":")[1].strip()
						elif "Processor Speed" in line:
							cpu_speed = line.split(":")[1].strip()
					if cpu_name and cpu_speed:
						return f"{cpu_name}_{cpu_speed}".replace(" ", "_")

			elif self.os_type == "linux":
				# Linux - use /proc/cpuinfo
				with open("/proc/cpuinfo") as f:
					cpuinfo = f.read()

				# Extract model name
				model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)

				if model_match:
					cpu_model = model_match.group(1).strip()
					return cpu_model.replace(" ", "_")

		except Exception as e:
			frappe.log_error(f"CPU info detection failed: {e!s}", "Hardware Fingerprint")

		return None

	def _get_motherboard_id(self) -> str | None:
		"""Get motherboard/system board ID cross-platform"""
		try:
			if self.os_type == "windows":
				# Windows - motherboard serial
				result = subprocess.run(
					["wmic", "baseboard", "get", "SerialNumber", "/format:csv"],
					capture_output=True,
					text=True,
					timeout=10,
				)

				if result.returncode == 0:
					lines = result.stdout.strip().split("\n")
					for line in lines:
						if "SerialNumber" in line and "," in line:
							serial = line.split(",")[1].strip()
							if serial and serial != "SerialNumber":
								return serial

			elif self.os_type == "darwin":
				# macOS - hardware UUID
				result = subprocess.run(
					["system_profiler", "SPHardwareDataType"], capture_output=True, text=True, timeout=10
				)

				if result.returncode == 0:
					for line in result.stdout.split("\n"):
						if "Hardware UUID" in line:
							uuid = line.split(":")[1].strip()
							return uuid

			elif self.os_type == "linux":
				# Linux - DMI system UUID
				try:
					with open("/sys/class/dmi/id/board_serial") as f:
						board_serial = f.read().strip()
						if board_serial and board_serial != "None":
							return board_serial
				except Exception:
					# Fallback to product UUID
					try:
						with open("/sys/class/dmi/id/product_uuid") as f:
							return f.read().strip()
					except Exception:
						pass

		except Exception as e:
			frappe.log_error(f"Motherboard ID detection failed: {e!s}", "Hardware Fingerprint")

		return None

	def _get_mac_addresses(self) -> list[str]:
		"""Get MAC addresses of network interfaces"""
		try:
			import psutil

			mac_addresses = []
			for _interface, addrs in psutil.net_if_addrs().items():
				for addr in addrs:
					if addr.family == psutil.AF_LINK:  # MAC address
						mac = addr.address
						# Filter out virtual/temporary MACs
						if mac and mac != "00:00:00:00:00:00" and not mac.startswith("02:"):
							mac_addresses.append(mac.upper())

			return sorted(set(mac_addresses))  # Remove duplicates and sort

		except ImportError:
			# Fallback method without psutil
			try:
				if self.os_type == "windows":
					result = subprocess.run(
						["getmac", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=10
					)

					if result.returncode == 0:
						macs = []
						for line in result.stdout.strip().split("\n"):
							if line:
								mac = line.split(",")[0].strip('"')
								if mac and mac != "N/A":
									macs.append(mac.upper())
						return sorted(set(macs))

				elif self.os_type in ["darwin", "linux"]:
					result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=10)

					if result.returncode == 0:
						macs = re.findall(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})", result.stdout)
						return sorted({mac[0] + mac[1] for mac in macs})

			except Exception as e:
				frappe.log_error(f"MAC address fallback failed: {e!s}", "Hardware Fingerprint")

		return []

	def _get_system_uuid(self) -> str | None:
		"""Get system UUID/GUID"""
		try:
			if self.os_type == "windows":
				result = subprocess.run(
					["wmic", "csproduct", "get", "UUID", "/format:csv"],
					capture_output=True,
					text=True,
					timeout=10,
				)

				if result.returncode == 0:
					lines = result.stdout.strip().split("\n")
					for line in lines:
						if "UUID" in line and "," in line:
							uuid = line.split(",")[1].strip()
							if uuid and uuid != "UUID":
								return uuid

			elif self.os_type == "darwin":
				result = subprocess.run(
					["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
					capture_output=True,
					text=True,
					timeout=10,
				)

				if result.returncode == 0:
					uuid_match = re.search(r'"IOPlatformUUID" = "([^"]+)"', result.stdout)
					if uuid_match:
						return uuid_match.group(1)

			elif self.os_type == "linux":
				try:
					with open("/etc/machine-id") as f:
						return f.read().strip()
				except Exception:
					try:
						with open("/var/lib/dbus/machine-id") as f:
							return f.read().strip()
					except Exception:
						pass

		except Exception as e:
			frappe.log_error(f"System UUID detection failed: {e!s}", "Hardware Fingerprint")

		return None

	def _get_bios_info(self) -> str | None:
		"""Get BIOS/UEFI information"""
		try:
			if self.os_type == "windows":
				result = subprocess.run(
					["wmic", "bios", "get", "SerialNumber,Version", "/format:csv"],
					capture_output=True,
					text=True,
					timeout=10,
				)

				if result.returncode == 0:
					lines = result.stdout.strip().split("\n")
					for line in lines:
						if "SerialNumber" in line and "," in line:
							parts = line.split(",")
							if len(parts) >= 3:
								return f"{parts[1]}_{parts[2]}".strip()

			elif self.os_type == "linux":
				try:
					with open("/sys/class/dmi/id/bios_version") as f:
						bios_version = f.read().strip()
					with open("/sys/class/dmi/id/bios_vendor") as f:
						bios_vendor = f.read().strip()
					return f"{bios_vendor}_{bios_version}"
				except Exception:
					pass

		except Exception as e:
			frappe.log_error(f"BIOS info detection failed: {e!s}", "Hardware Fingerprint")

		return None

	def _get_disk_serial(self) -> list[str]:
		"""Get disk serial numbers (volatile component)"""
		try:
			import psutil

			serials = []
			for disk in psutil.disk_partitions():
				try:
					if self.os_type == "windows":
						drive_letter = disk.device[0]
						result = subprocess.run(
							[
								"wmic",
								"diskdrive",
								"where",
								f'DeviceID like "%{drive_letter}%"',
								"get",
								"SerialNumber",
								"/format:csv",
							],
							capture_output=True,
							text=True,
							timeout=10,
						)

						if result.returncode == 0:
							for line in result.stdout.strip().split("\n"):
								if "SerialNumber" in line and "," in line:
									serial = line.split(",")[1].strip()
									if serial and serial != "SerialNumber":
										serials.append(serial)
				except Exception:
					continue

			return sorted(set(serials))

		except Exception as e:
			frappe.log_error(f"Disk serial detection failed: {e!s}", "Hardware Fingerprint")

		return []

	def _normalize_components(self, components: dict) -> dict:
		"""Normalize component data for consistent hashing"""
		normalized = {}

		for key, value in components.items():
			if isinstance(value, str):
				# Normalize strings
				normalized[key] = re.sub(r"\s+", "_", value.strip().upper())
			elif isinstance(value, list):
				# Normalize and sort lists
				normalized[key] = sorted([re.sub(r"\s+", "_", str(item).strip().upper()) for item in value])
			else:
				normalized[key] = str(value).strip().upper()

		return normalized

	def _generate_primary_hash(self, components: dict) -> str:
		"""Generate primary hardware hash using stable components"""
		# Use only the most stable components for primary hash
		stable_components = ["cpu_info", "motherboard_id", "system_uuid"]

		hash_input = ""
		for component in stable_components:
			if components.get(component):
				hash_input += f"{component}:{components[component]}|"

		# Add first MAC address if available (usually most stable)
		if components.get("mac_addresses"):
			hash_input += f"primary_mac:{components['mac_addresses'][0]}|"

		if not hash_input:
			raise ValueError("Insufficient stable hardware components for fingerprinting")

		return hashlib.sha256(hash_input.encode()).hexdigest()

	def _generate_tolerance_hash(self, components: dict) -> str:
		"""Generate secondary hash with tolerance for hardware changes"""
		# Use broader set of components for tolerance matching
		hash_inputs = []

		# Create multiple hash combinations for tolerance
		for i in range(len(self.supported_components)):
			hash_input = ""
			component_count = 0

			for j, component in enumerate(self.supported_components):
				if j == i:  # Skip one component for tolerance
					continue

				if components.get(component):
					hash_input += f"{component}:{components[component]}|"
					component_count += 1

			if component_count >= 3:  # Minimum 3 components for valid hash
				hash_inputs.append(hashlib.sha256(hash_input.encode()).hexdigest())

		# Return combined tolerance hash
		combined_input = "|".join(sorted(hash_inputs))
		return hashlib.sha256(combined_input.encode()).hexdigest()

	def _generate_fallback_fingerprint(self) -> dict:
		"""Generate basic fallback fingerprint when detailed detection fails"""
		try:
			# Basic system information
			basic_info = {
				"platform": platform.platform(),
				"machine": platform.machine(),
				"processor": platform.processor(),
				"node": platform.node(),
			}

			hash_input = "|".join(f"{k}:{v}" for k, v in basic_info.items() if v)
			fallback_hash = hashlib.sha256(hash_input.encode()).hexdigest()

			return {
				"primary_hash": fallback_hash,
				"secondary_hash": fallback_hash,
				"components": basic_info,
				"os_type": self.os_type,
				"generated_at": datetime.utcnow().isoformat(),
				"version": "1.0-fallback",
				"is_fallback": True,
			}

		except Exception as e:
			frappe.log_error(f"Fallback fingerprint generation failed: {e!s}", "Hardware Fingerprint")
			# Ultimate fallback - random but deterministic
			import time

			emergency_hash = hashlib.sha256(f"emergency_{platform.node()}_{time.time()}".encode()).hexdigest()
			return {
				"primary_hash": emergency_hash,
				"secondary_hash": emergency_hash,
				"components": {"emergency": True},
				"os_type": self.os_type,
				"generated_at": datetime.utcnow().isoformat(),
				"version": "1.0-emergency",
				"is_emergency": True,
			}

	def _log_fingerprint_event(self, fingerprint_data: dict):
		"""Log fingerprint generation event for audit"""
		try:
			from universal_workshop.license_management.doctype.license_audit_log.license_audit_log import (
				create_audit_log,
			)

			event_data = {
				"os_type": fingerprint_data["os_type"],
				"components_detected": list(fingerprint_data["components"].keys()),
				"fingerprint_version": fingerprint_data["version"],
				"is_fallback": fingerprint_data.get("is_fallback", False),
				"is_emergency": fingerprint_data.get("is_emergency", False),
			}

			create_audit_log(
				event_type="hardware_fingerprint_generated",
				severity="low",
				message=f"Hardware fingerprint generated for {fingerprint_data['os_type']}",
				event_data=event_data,
			)

		except Exception as e:
			frappe.log_error(f"Failed to log fingerprint event: {e!s}", "Hardware Fingerprint Audit")


class HardwareFingerprintValidator:
	"""
	Validates hardware fingerprints with tolerance for changes
	Handles legitimate hardware changes vs license violations
	"""

	def __init__(self):
		self.generator = HardwareFingerprintGenerator()

	def validate_fingerprint(self, stored_fingerprint: str, tolerance_level: str = "medium") -> dict:
		"""
		Validate current hardware against stored fingerprint

		Args:
		    stored_fingerprint (str): Previously stored fingerprint hash
		    tolerance_level (str): "strict", "medium", or "loose"

		Returns:
		    Dict: Validation result with match status and details
		"""
		try:
			# Generate current fingerprint
			current_fp = self.generator.generate_fingerprint()

			# Parse stored fingerprint if it's JSON
			if stored_fingerprint.startswith("{"):
				stored_fp_data = json.loads(stored_fingerprint)
				stored_primary = stored_fp_data.get("primary_hash")
				stored_secondary = stored_fp_data.get("secondary_hash")
			else:
				# Legacy format - just a hash
				stored_primary = stored_fingerprint
				stored_secondary = stored_fingerprint

			# Primary hash match (exact)
			if current_fp["primary_hash"] == stored_primary:
				return {
					"valid": True,
					"match_type": "exact",
					"confidence": 100,
					"message": "Hardware fingerprint matches exactly",
				}

			# Secondary hash match (tolerance)
			if current_fp["secondary_hash"] == stored_secondary:
				return {
					"valid": True,
					"match_type": "tolerance",
					"confidence": 85,
					"message": "Hardware fingerprint matches with tolerance",
				}

			# Component-level analysis for partial matches
			if stored_fingerprint.startswith("{"):
				stored_components = stored_fp_data.get("components", {})
				current_components = current_fp["components"]

				component_matches = self._analyze_component_matches(
					stored_components, current_components, tolerance_level
				)

				if component_matches["match_percentage"] >= self._get_tolerance_threshold(tolerance_level):
					return {
						"valid": True,
						"match_type": "partial",
						"confidence": component_matches["match_percentage"],
						"message": f"Hardware partially matches ({component_matches['match_percentage']}%)",
						"component_analysis": component_matches,
					}

			# No match found
			return {
				"valid": False,
				"match_type": "none",
				"confidence": 0,
				"message": "Hardware fingerprint does not match",
				"current_fingerprint": current_fp["primary_hash"],
			}

		except Exception as e:
			frappe.log_error(f"Hardware fingerprint validation failed: {e!s}", "Hardware Fingerprint")
			return {
				"valid": False,
				"match_type": "error",
				"confidence": 0,
				"message": f"Validation error: {e!s}",
			}

	def _analyze_component_matches(
		self, stored_components: dict, current_components: dict, tolerance_level: str
	) -> dict:
		"""Analyze component-level matches between fingerprints"""
		matches = {}
		total_components = 0
		matched_components = 0

		# Check each component
		for component, stored_value in stored_components.items():
			total_components += 1
			current_value = current_components.get(component)

			if stored_value == current_value:
				matches[component] = "exact"
				matched_components += 1
			elif self._is_partial_match(stored_value, current_value, component, tolerance_level):
				matches[component] = "partial"
				matched_components += 0.5  # Partial match counts as half
			else:
				matches[component] = "no_match"

		match_percentage = int(matched_components / total_components * 100) if total_components > 0 else 0

		return {
			"matches": matches,
			"match_percentage": match_percentage,
			"total_components": total_components,
			"matched_components": matched_components,
		}

	def _is_partial_match(self, stored_value, current_value, component: str, tolerance_level: str) -> bool:
		"""Check if values represent a partial match based on component type and tolerance"""
		if not stored_value or not current_value:
			return False

		# MAC addresses - allow if at least one matches
		if (
			component == "mac_addresses"
			and isinstance(stored_value, list)
			and isinstance(current_value, list)
		):
			return bool(set(stored_value) & set(current_value))

		# String similarity for other components
		if isinstance(stored_value, str) and isinstance(current_value, str):
			# Simple Levenshtein-like comparison
			similarity = self._calculate_string_similarity(stored_value, current_value)

			thresholds = {"strict": 0.9, "medium": 0.7, "loose": 0.5}

			return similarity >= thresholds.get(tolerance_level, 0.7)

		return False

	def _calculate_string_similarity(self, str1: str, str2: str) -> float:
		"""Calculate similarity between two strings (0.0 to 1.0)"""
		if str1 == str2:
			return 1.0

		# Simple character overlap calculation
		set1 = set(str1.lower())
		set2 = set(str2.lower())

		intersection = len(set1 & set2)
		union = len(set1 | set2)

		return intersection / union if union > 0 else 0.0

	def _get_tolerance_threshold(self, tolerance_level: str) -> int:
		"""Get match percentage threshold for tolerance level"""
		thresholds = {"strict": 90, "medium": 70, "loose": 50}
		return thresholds.get(tolerance_level, 70)


# Frappe whitelist methods for API access
@frappe.whitelist()
def generate_hardware_fingerprint():
	"""API method to generate hardware fingerprint"""
	generator = HardwareFingerprintGenerator()
	return generator.generate_fingerprint()


@frappe.whitelist()
def validate_hardware_fingerprint(stored_fingerprint, tolerance_level="medium"):
	"""API method to validate hardware fingerprint"""
	validator = HardwareFingerprintValidator()
	return validator.validate_fingerprint(stored_fingerprint, tolerance_level)
