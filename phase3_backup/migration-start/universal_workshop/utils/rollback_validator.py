"""
Rollback Validation Utility for Universal Workshop ERP
Provides validation and verification capabilities for database rollbacks
"""

import frappe
import json
from datetime import datetime
from frappe.utils import now, get_site_name


class RollbackValidator:
	"""Comprehensive rollback validation system"""
	
	def __init__(self):
		self.config = self.get_rollback_config()
		self.validation_results = []
	
	def get_rollback_config(self):
		"""Get rollback validation configuration"""
		try:
			config_str = frappe.db.get_single_value("System Settings", "rollback_validation_config")
			if config_str:
				return json.loads(config_str)
			else:
				return {
					"pre_rollback_checks": [
						"verify_backup_integrity",
						"check_disk_space",
						"validate_permissions"
					],
					"post_rollback_checks": [
						"database_connectivity",
						"table_existence",
						"data_integrity",
						"index_consistency"
					],
					"rollback_validation_timeout": 300
				}
		except Exception as e:
			frappe.log_error(f"Failed to get rollback config: {str(e)}", "Rollback Validator")
			return {}
	
	def validate_pre_rollback(self):
		"""Validate system state before rollback"""
		try:
			frappe.log_error("Starting pre-rollback validation", "Rollback Validator")
			
			results = {
				"timestamp": now(),
				"validation_type": "pre_rollback",
				"checks": [],
				"overall_status": "passed"
			}
			
			# Check disk space
			disk_check = self.check_disk_space()
			results["checks"].append(disk_check)
			
			# Check database connectivity
			db_check = self.check_database_connectivity()
			results["checks"].append(db_check)
			
			# Check critical tables
			table_check = self.check_critical_tables()
			results["checks"].append(table_check)
			
			# Determine overall status
			if any(check["status"] == "failed" for check in results["checks"]):
				results["overall_status"] = "failed"
			elif any(check["status"] == "warning" for check in results["checks"]):
				results["overall_status"] = "warning"
			
			self.validation_results.append(results)
			frappe.log_error(f"Pre-rollback validation completed: {results['overall_status']}", "Rollback Validator")
			
			return results
			
		except Exception as e:
			frappe.log_error(f"Pre-rollback validation failed: {str(e)}", "Rollback Validator")
			return {"overall_status": "error", "error": str(e)}
	
	def validate_post_rollback(self):
		"""Validate system state after rollback"""
		try:
			frappe.log_error("Starting post-rollback validation", "Rollback Validator")
			
			results = {
				"timestamp": now(),
				"validation_type": "post_rollback",
				"checks": [],
				"overall_status": "passed"
			}
			
			# Check database connectivity
			db_check = self.check_database_connectivity()
			results["checks"].append(db_check)
			
			# Check table existence
			table_check = self.check_critical_tables()
			results["checks"].append(table_check)
			
			# Check data integrity
			integrity_check = self.check_data_integrity()
			results["checks"].append(integrity_check)
			
			# Check application functionality
			app_check = self.check_application_functionality()
			results["checks"].append(app_check)
			
			# Check indexes
			index_check = self.check_index_consistency()
			results["checks"].append(index_check)
			
			# Determine overall status
			if any(check["status"] == "failed" for check in results["checks"]):
				results["overall_status"] = "failed"
			elif any(check["status"] == "warning" for check in results["checks"]):
				results["overall_status"] = "warning"
			
			self.validation_results.append(results)
			frappe.log_error(f"Post-rollback validation completed: {results['overall_status']}", "Rollback Validator")
			
			return results
			
		except Exception as e:
			frappe.log_error(f"Post-rollback validation failed: {str(e)}", "Rollback Validator")
			return {"overall_status": "error", "error": str(e)}
	
	def check_disk_space(self):
		"""Check available disk space"""
		try:
			import shutil
			
			# Check disk space (require at least 1GB free)
			total, used, free = shutil.disk_usage("/")
			free_gb = free // (1024**3)
			
			if free_gb >= 1:
				return {
					"check_name": "disk_space",
					"status": "passed",
					"message": f"Sufficient disk space: {free_gb}GB free",
					"details": {"free_gb": free_gb, "total_gb": total // (1024**3)}
				}
			else:
				return {
					"check_name": "disk_space",
					"status": "warning",
					"message": f"Low disk space: {free_gb}GB free",
					"details": {"free_gb": free_gb, "total_gb": total // (1024**3)}
				}
		
		except Exception as e:
			return {
				"check_name": "disk_space",
				"status": "failed",
				"message": f"Failed to check disk space: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def check_database_connectivity(self):
		"""Check database connectivity and basic operations"""
		try:
			# Test basic database query
			result = frappe.db.sql("SELECT 1 as test", as_dict=True)
			
			if result and result[0]["test"] == 1:
				return {
					"check_name": "database_connectivity",
					"status": "passed",
					"message": "Database connectivity verified",
					"details": {"connection": "active", "query_test": "passed"}
				}
			else:
				return {
					"check_name": "database_connectivity",
					"status": "failed",
					"message": "Database query test failed",
					"details": {"connection": "active", "query_test": "failed"}
				}
		
		except Exception as e:
			return {
				"check_name": "database_connectivity",
				"status": "failed",
				"message": f"Database connectivity failed: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def check_critical_tables(self):
		"""Check existence of critical tables"""
		try:
			critical_tables = self.config.get("critical_tables", [
				"tabWorkshop Profile",
				"tabService Order", 
				"tabVehicle",
				"tabCustomer",
				"tabUser",
				"tabDocType"
			])
			
			missing_tables = []
			existing_tables = []
			
			for table in critical_tables:
				try:
					result = frappe.db.sql(f"SHOW TABLES LIKE '{table}'")
					if result:
						existing_tables.append(table)
					else:
						missing_tables.append(table)
				except Exception as e:
					missing_tables.append(f"{table} (error: {str(e)})")
			
			if not missing_tables:
				return {
					"check_name": "critical_tables",
					"status": "passed",
					"message": f"All {len(existing_tables)} critical tables exist",
					"details": {"existing": existing_tables, "missing": missing_tables}
				}
			else:
				return {
					"check_name": "critical_tables",
					"status": "failed",
					"message": f"{len(missing_tables)} critical tables missing",
					"details": {"existing": existing_tables, "missing": missing_tables}
				}
		
		except Exception as e:
			return {
				"check_name": "critical_tables",
				"status": "failed",
				"message": f"Failed to check critical tables: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def check_data_integrity(self):
		"""Check basic data integrity"""
		try:
			integrity_checks = []
			
			# Check for null values in critical fields
			null_checks = [
				("tabUser", "name", "User names"),
				("tabDocType", "name", "DocType names"),
				("tabWorkshop Profile", "workshop_code", "Workshop codes")
			]
			
			for table, field, description in null_checks:
				try:
					result = frappe.db.sql(f"""
						SELECT COUNT(*) as null_count 
						FROM `{table}` 
						WHERE `{field}` IS NULL OR `{field}` = ''
					""", as_dict=True)
					
					null_count = result[0]["null_count"] if result else 0
					integrity_checks.append({
						"table": table,
						"field": field,
						"description": description,
						"null_count": null_count,
						"status": "passed" if null_count == 0 else "warning"
					})
				except Exception as e:
					integrity_checks.append({
						"table": table,
						"field": field,
						"description": description,
						"error": str(e),
						"status": "failed"
					})
			
			# Determine overall status
			failed_checks = [c for c in integrity_checks if c["status"] == "failed"]
			warning_checks = [c for c in integrity_checks if c["status"] == "warning"]
			
			if failed_checks:
				status = "failed"
				message = f"Data integrity issues: {len(failed_checks)} failed checks"
			elif warning_checks:
				status = "warning"
				message = f"Data integrity warnings: {len(warning_checks)} warnings"
			else:
				status = "passed"
				message = "Data integrity checks passed"
			
			return {
				"check_name": "data_integrity",
				"status": status,
				"message": message,
				"details": {"checks": integrity_checks}
			}
		
		except Exception as e:
			return {
				"check_name": "data_integrity",
				"status": "failed",
				"message": f"Failed to check data integrity: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def check_application_functionality(self):
		"""Check basic application functionality"""
		try:
			functionality_tests = []
			
			# Test DocType access
			try:
				doctype_count = frappe.db.count("DocType")
				functionality_tests.append({
					"test": "doctype_access",
					"status": "passed",
					"result": f"{doctype_count} DocTypes accessible"
				})
			except Exception as e:
				functionality_tests.append({
					"test": "doctype_access",
					"status": "failed",
					"result": f"DocType access failed: {str(e)}"
				})
			
			# Test user access
			try:
				user_count = frappe.db.count("User")
				functionality_tests.append({
					"test": "user_access",
					"status": "passed",
					"result": f"{user_count} users accessible"
				})
			except Exception as e:
				functionality_tests.append({
					"test": "user_access",
					"status": "failed",
					"result": f"User access failed: {str(e)}"
				})
			
			# Test Workshop Profile access
			try:
				workshop_count = frappe.db.count("Workshop Profile")
				functionality_tests.append({
					"test": "workshop_profile_access",
					"status": "passed",
					"result": f"{workshop_count} Workshop Profiles accessible"
				})
			except Exception as e:
				functionality_tests.append({
					"test": "workshop_profile_access",
					"status": "failed",
					"result": f"Workshop Profile access failed: {str(e)}"
				})
			
			# Determine overall status
			failed_tests = [t for t in functionality_tests if t["status"] == "failed"]
			
			if failed_tests:
				status = "failed"
				message = f"Application functionality issues: {len(failed_tests)} failed tests"
			else:
				status = "passed"
				message = "Application functionality tests passed"
			
			return {
				"check_name": "application_functionality",
				"status": status,
				"message": message,
				"details": {"tests": functionality_tests}
			}
		
		except Exception as e:
			return {
				"check_name": "application_functionality",
				"status": "failed",
				"message": f"Failed to check application functionality: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def check_index_consistency(self):
		"""Check database index consistency"""
		try:
			index_checks = []
			critical_tables = ["tabWorkshop Profile", "tabService Order", "tabVehicle"]
			
			for table in critical_tables:
				try:
					indexes = frappe.db.sql(f"SHOW INDEX FROM `{table}`", as_dict=True)
					index_checks.append({
						"table": table,
						"index_count": len(indexes),
						"status": "passed" if indexes else "warning"
					})
				except Exception as e:
					index_checks.append({
						"table": table,
						"error": str(e),
						"status": "failed"
					})
			
			# Determine overall status
			failed_checks = [c for c in index_checks if c["status"] == "failed"]
			
			if failed_checks:
				status = "failed"
				message = f"Index consistency issues: {len(failed_checks)} failed checks"
			else:
				status = "passed"
				message = "Index consistency checks passed"
			
			return {
				"check_name": "index_consistency",
				"status": status,
				"message": message,
				"details": {"checks": index_checks}
			}
		
		except Exception as e:
			return {
				"check_name": "index_consistency",
				"status": "failed",
				"message": f"Failed to check index consistency: {str(e)}",
				"details": {"error": str(e)}
			}
	
	def get_validation_report(self):
		"""Get comprehensive validation report"""
		return {
			"site": get_site_name(),
			"timestamp": now(),
			"validation_results": self.validation_results,
			"summary": {
				"total_validations": len(self.validation_results),
				"passed": len([r for r in self.validation_results if r["overall_status"] == "passed"]),
				"warnings": len([r for r in self.validation_results if r["overall_status"] == "warning"]),
				"failed": len([r for r in self.validation_results if r["overall_status"] == "failed"])
			}
		}


@frappe.whitelist()
def validate_rollback():
	"""API endpoint to validate rollback"""
	try:
		validator = RollbackValidator()
		result = validator.validate_post_rollback()
		
		frappe.log_error(f"Rollback validation API called: {result['overall_status']}", "Rollback Validator API")
		
		return result
	
	except Exception as e:
		frappe.log_error(f"Rollback validation API failed: {str(e)}", "Rollback Validator API")
		return {"overall_status": "error", "error": str(e)}


@frappe.whitelist()
def get_rollback_report():
	"""Get comprehensive rollback validation report"""
	try:
		validator = RollbackValidator()
		report = validator.get_validation_report()
		
		return report
	
	except Exception as e:
		frappe.log_error(f"Failed to get rollback report: {str(e)}", "Rollback Validator API")
		return {"error": str(e)}


def scheduled_rollback_validation():
	"""Scheduled function for regular rollback readiness validation"""
	try:
		validator = RollbackValidator()
		
		# Run pre-rollback validation to ensure system is ready for potential rollback
		result = validator.validate_pre_rollback()
		
		# Log results
		frappe.log_error(f"Scheduled rollback validation: {result['overall_status']}", "Rollback Validator")
		
		# Send alerts if there are issues
		if result["overall_status"] in ["failed", "warning"]:
			send_rollback_alert(result)
		
	except Exception as e:
		frappe.log_error(f"Scheduled rollback validation failed: {str(e)}", "Rollback Validator")


def send_rollback_alert(validation_result):
	"""Send alert about rollback validation issues"""
	try:
		# Get rollback configuration for alert recipients
		config_str = frappe.db.get_single_value("System Settings", "rollback_configuration")
		if config_str:
			config = json.loads(config_str)
			recipients = config.get("notification_settings", {}).get("recipients", [])
			
			if recipients:
				subject = f"Universal Workshop ERP Rollback Validation Alert - {validation_result['overall_status'].upper()}"
				message = f"""
				Rollback Validation Alert:
				
				Status: {validation_result['overall_status']}
				Timestamp: {validation_result['timestamp']}
				
				Issues detected during rollback readiness validation.
				Please check the system logs for detailed information.
				
				Site: {get_site_name()}
				"""
				
				for recipient in recipients:
					try:
						frappe.sendmail(
							recipients=[recipient],
							subject=subject,
							message=message
						)
					except Exception as e:
						frappe.log_error(f"Failed to send rollback alert to {recipient}: {str(e)}", "Rollback Alert")
	
	except Exception as e:
		frappe.log_error(f"Failed to send rollback alert: {str(e)}", "Rollback Alert") 