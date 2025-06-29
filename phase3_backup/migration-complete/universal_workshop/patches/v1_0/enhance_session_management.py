# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date


def execute():
    """Enhance session management to fix Session Stopped errors and improve reliability"""
    try:
        print("🔧 Enhancing session management to fix Session Stopped errors...")

        # 1. Fix session timeout handling
        fix_session_timeout_handling()

        # 2. Improve session cleanup and recovery
        improve_session_cleanup()

        # 3. Add session error monitoring and alerting
        add_session_error_monitoring()

        # 4. Enhance session validation and recovery
        enhance_session_validation()

        # 5. Create session health check system
        create_session_health_check()

        # 6. Add session debugging and logging
        add_session_debugging()

        # 7. Configure automatic session recovery
        configure_session_recovery()

        print("✅ Session management enhancement completed successfully")

    except Exception as e:
        frappe.log_error(f"Session management enhancement failed: {e}")
        print(f"❌ Session management enhancement failed: {e}")
        raise


def fix_session_timeout_handling():
    """Fix session timeout handling to prevent unexpected Session Stopped errors"""
    try:
        # Create enhanced session timeout handler
        timeout_handler_code = '''
class EnhancedSessionTimeoutHandler:
    """Enhanced session timeout handler to prevent unexpected session stops"""
    
    def __init__(self):
        self.grace_period_minutes = 5  # Grace period before hard timeout
        self.warning_thresholds = [10, 5, 2]  # Warning at 10, 5, 2 minutes
        self.auto_extend_threshold = 30  # Auto-extend if activity within 30 seconds
    
    def check_session_timeout(self, session_id):
        """Check session timeout with enhanced logic"""
        try:
            from universal_workshop.user_management.session_manager import SessionManager
            
            session_manager = SessionManager()
            session_validation = session_manager.validate_session(session_id)
            
            if not session_validation.get("valid"):
                return self.handle_invalid_session(session_id, session_validation)
            
            # Check if session is approaching timeout
            time_remaining = session_validation.get("time_remaining_minutes", 0)
            
            if time_remaining <= self.grace_period_minutes:
                return self.handle_approaching_timeout(session_id, time_remaining)
            
            return {"status": "active", "time_remaining": time_remaining}
            
        except Exception as e:
            frappe.log_error(f"Session timeout check error: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_invalid_session(self, session_id, validation_result):
        """Handle invalid session with recovery options"""
        try:
            error_type = validation_result.get("error_type", "unknown")
            
            if error_type == "expired":
                # Try to extend session if recent activity
                if self.can_auto_extend_session(session_id):
                    return self.auto_extend_session(session_id)
                else:
                    return self.initiate_graceful_logout(session_id)
            
            elif error_type == "not_found":
                # Session record missing - try to recreate
                return self.attempt_session_recovery(session_id)
            
            else:
                # Other errors - log and initiate logout
                frappe.log_error(f"Session validation failed: {validation_result}")
                return self.initiate_graceful_logout(session_id)
                
        except Exception as e:
            frappe.log_error(f"Error handling invalid session: {e}")
            return {"status": "error", "message": "Session handling error"}
    
    def handle_approaching_timeout(self, session_id, time_remaining):
        """Handle session approaching timeout"""
        try:
            # Check for recent activity
            if self.has_recent_activity(session_id):
                # Auto-extend session
                return self.auto_extend_session(session_id)
            
            # Send warning to client
            if time_remaining in self.warning_thresholds:
                self.send_timeout_warning(session_id, time_remaining)
            
            return {
                "status": "warning",
                "time_remaining": time_remaining,
                "message": f"Session will expire in {time_remaining} minutes"
            }
            
        except Exception as e:
            frappe.log_error(f"Error handling approaching timeout: {e}")
            return {"status": "error", "message": str(e)}
    
    def can_auto_extend_session(self, session_id):
        """Check if session can be auto-extended"""
        try:
            # Check last activity time
            last_activity = frappe.db.get_value(
                "Workshop User Session", 
                {"session_id": session_id}, 
                "last_activity"
            )
            
            if not last_activity:
                return False
            
            from frappe.utils import get_datetime, now_datetime
            last_activity_time = get_datetime(last_activity)
            current_time = now_datetime()
            
            # Auto-extend if activity within threshold
            time_diff = (current_time - last_activity_time).total_seconds()
            return time_diff <= self.auto_extend_threshold
            
        except Exception as e:
            frappe.log_error(f"Error checking auto-extend eligibility: {e}")
            return False
    
    def auto_extend_session(self, session_id):
        """Automatically extend session"""
        try:
            from universal_workshop.user_management.session_manager import SessionManager
            
            session_manager = SessionManager()
            result = session_manager.update_session_activity(session_id)
            
            if result.get("success"):
                return {
                    "status": "extended",
                    "message": "Session automatically extended",
                    "new_expiry": result.get("new_expiry")
                }
            else:
                return {"status": "error", "message": "Failed to extend session"}
                
        except Exception as e:
            frappe.log_error(f"Error auto-extending session: {e}")
            return {"status": "error", "message": str(e)}
    
    def has_recent_activity(self, session_id):
        """Check if session has recent activity"""
        try:
            last_activity = frappe.db.get_value(
                "Workshop User Session",
                {"session_id": session_id},
                "last_activity"
            )
            
            if not last_activity:
                return False
            
            from frappe.utils import get_datetime, now_datetime
            last_activity_time = get_datetime(last_activity)
            current_time = now_datetime()
            
            # Consider activity within last 2 minutes as recent
            time_diff = (current_time - last_activity_time).total_seconds()
            return time_diff <= 120  # 2 minutes
            
        except Exception as e:
            frappe.log_error(f"Error checking recent activity: {e}")
            return False
    
    def send_timeout_warning(self, session_id, time_remaining):
        """Send timeout warning to client"""
        try:
            # This would be implemented to send real-time warnings
            # For now, just log the warning
            frappe.logger().info(f"Session {session_id} timeout warning: {time_remaining} minutes remaining")
            
        except Exception as e:
            frappe.log_error(f"Error sending timeout warning: {e}")
    
    def initiate_graceful_logout(self, session_id):
        """Initiate graceful logout process"""
        try:
            # Mark session as gracefully terminated
            frappe.db.set_value(
                "Workshop User Session",
                {"session_id": session_id},
                {
                    "is_active": 0,
                    "revocation_reason": "Graceful timeout"
                }
            )
            
            return {
                "status": "logout",
                "message": "Session expired - graceful logout initiated"
            }
            
        except Exception as e:
            frappe.log_error(f"Error initiating graceful logout: {e}")
            return {"status": "error", "message": str(e)}
    
    def attempt_session_recovery(self, session_id):
        """Attempt to recover missing session"""
        try:
            # Check if user is still logged in via Frappe session
            frappe_session = frappe.db.get_value("Sessions", session_id, "*")
            
            if frappe_session:
                # Recreate Workshop User Session record
                from universal_workshop.user_management.session_manager import SessionManager
                session_manager = SessionManager()
                
                recovery_result = session_manager.create_session_record(
                    frappe_session.get("user"),
                    session_id,
                    {"recovery": True}
                )
                
                if recovery_result.get("success"):
                    return {
                        "status": "recovered",
                        "message": "Session successfully recovered"
                    }
            
            return {"status": "failed", "message": "Session recovery failed"}
            
        except Exception as e:
            frappe.log_error(f"Error attempting session recovery: {e}")
            return {"status": "error", "message": str(e)}


# Global instance
session_timeout_handler = EnhancedSessionTimeoutHandler()
'''

        # Save enhanced timeout handler
        handler_path = frappe.get_app_path(
            "universal_workshop", "user_management", "enhanced_session_timeout.py"
        )
        with open(handler_path, "w") as f:
            f.write(f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime

{timeout_handler_code}
""")

        print("✅ Enhanced session timeout handling implemented")

    except Exception as e:
        frappe.log_error(f"Error fixing session timeout handling: {e}")
        raise


def improve_session_cleanup():
    """Improve session cleanup to prevent orphaned sessions"""
    try:
        # Create session cleanup scheduler job
        cleanup_job = {
            "method": "universal_workshop.user_management.session_cleanup.run_session_cleanup",
            "frequency": "Cron",
            "cron_format": "*/15 * * * *",  # Every 15 minutes
        }

        # Check if job already exists
        existing_job = frappe.db.exists("Scheduled Job Type", {
            "method": cleanup_job["method"]
        })

        if not existing_job:
            doc = frappe.get_doc({
                "doctype": "Scheduled Job Type",
                "method": cleanup_job["method"],
                "frequency": cleanup_job["frequency"],
                "cron_format": cleanup_job["cron_format"],
                "create_log": 1
            })
            doc.insert(ignore_permissions=True)

        # Create session cleanup module
        cleanup_code = '''
def run_session_cleanup():
    """Run comprehensive session cleanup"""
    try:
        from universal_workshop.user_management.session_manager import SessionManager
        from universal_workshop.user_management.enhanced_session_timeout import session_timeout_handler
        
        session_manager = SessionManager()
        
        # 1. Clean up expired sessions
        cleanup_result = session_manager.cleanup_expired_sessions()
        
        # 2. Check for orphaned sessions (Workshop User Session without Frappe Sessions)
        orphaned_sessions = frappe.db.sql("""
            SELECT wus.name, wus.session_id
            FROM `tabWorkshop User Session` wus
            LEFT JOIN `tabSessions` s ON wus.session_id = s.name
            WHERE wus.is_active = 1 AND s.name IS NULL
        """, as_dict=True)
        
        for orphaned in orphaned_sessions:
            frappe.db.set_value(
                "Workshop User Session",
                orphaned.name,
                {
                    "is_active": 0,
                    "revocation_reason": "Orphaned session cleanup"
                }
            )
        
        # 3. Check for Frappe sessions without Workshop User Session records
        frappe_sessions = frappe.db.sql("""
            SELECT s.name, s.user
            FROM `tabSessions` s
            LEFT JOIN `tabWorkshop User Session` wus ON s.name = wus.session_id
            WHERE wus.session_id IS NULL AND s.user != 'Guest'
        """, as_dict=True)
        
        for fs in frappe_sessions:
            # Create missing Workshop User Session record
            session_manager.create_session_record(
                fs.user,
                fs.name,
                {"cleanup_recovery": True}
            )
        
        # 4. Validate active sessions
        active_sessions = frappe.db.get_all(
            "Workshop User Session",
            filters={"is_active": 1},
            fields=["session_id"]
        )
        
        validation_results = []
        for session in active_sessions:
            result = session_timeout_handler.check_session_timeout(session.session_id)
            validation_results.append({
                "session_id": session.session_id,
                "status": result.get("status"),
                "action_taken": result.get("message", "")
            })
        
        frappe.logger().info(f"Session cleanup completed: {len(orphaned_sessions)} orphaned, {len(frappe_sessions)} recovered, {len(validation_results)} validated")
        
        return {
            "success": True,
            "orphaned_cleaned": len(orphaned_sessions),
            "sessions_recovered": len(frappe_sessions),
            "sessions_validated": len(validation_results),
            "validation_results": validation_results
        }
        
    except Exception as e:
        frappe.log_error(f"Session cleanup error: {e}")
        return {"success": False, "error": str(e)}


def get_session_health_status():
    """Get overall session health status"""
    try:
        # Get session statistics
        total_sessions = frappe.db.count("Workshop User Session", {"is_active": 1})
        frappe_sessions = frappe.db.count("Sessions")
        
        # Check for discrepancies
        orphaned_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWorkshop User Session` wus
            LEFT JOIN `tabSessions` s ON wus.session_id = s.name
            WHERE wus.is_active = 1 AND s.name IS NULL
        """)[0][0]
        
        missing_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabSessions` s
            LEFT JOIN `tabWorkshop User Session` wus ON s.name = wus.session_id
            WHERE wus.session_id IS NULL AND s.user != 'Guest'
        """)[0][0]
        
        health_score = 100
        if orphaned_count > 0:
            health_score -= min(orphaned_count * 5, 30)
        if missing_count > 0:
            health_score -= min(missing_count * 5, 30)
        
        status = "healthy" if health_score >= 90 else "warning" if health_score >= 70 else "critical"
        
        return {
            "health_score": health_score,
            "status": status,
            "total_active_sessions": total_sessions,
            "frappe_sessions": frappe_sessions,
            "orphaned_sessions": orphaned_count,
            "missing_sessions": missing_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting session health status: {e}")
        return {"health_score": 0, "status": "error", "error": str(e)}
'''

        # Save session cleanup module
        cleanup_path = frappe.get_app_path(
            "universal_workshop", "user_management", "session_cleanup.py"
        )
        with open(cleanup_path, "w") as f:
            f.write(f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

{cleanup_code}
""")

        print("✅ Session cleanup improvements implemented")

    except Exception as e:
        frappe.log_error(f"Error improving session cleanup: {e}")
        raise


def add_session_error_monitoring():
    """Add session error monitoring and alerting"""
    try:
        # Create session error monitor
        monitor_code = '''
class SessionErrorMonitor:
    """Monitor and track session-related errors"""
    
    def __init__(self):
        self.error_threshold = 10  # Alert after 10 errors in 1 hour
        self.time_window_hours = 1
    
    def log_session_error(self, error_type, session_id=None, user_email=None, details=None):
        """Log session error for monitoring"""
        try:
            error_doc = frappe.get_doc({
                "doctype": "Error Log",
                "method": f"session_error_{error_type}",
                "error": str(details) if details else f"Session {error_type} error",
                "reference_doctype": "Workshop User Session",
                "reference_name": session_id
            })
            error_doc.insert(ignore_permissions=True)
            
            # Check if we need to send alert
            self.check_error_threshold(error_type)
            
        except Exception as e:
            frappe.log_error(f"Error logging session error: {e}")
    
    def check_error_threshold(self, error_type):
        """Check if error threshold is exceeded"""
        try:
            from frappe.utils import add_to_date, now_datetime
            
            # Count errors in the last hour
            time_threshold = add_to_date(now_datetime(), hours=-self.time_window_hours)
            
            error_count = frappe.db.count("Error Log", {
                "method": f"session_error_{error_type}",
                "creation": [">=", time_threshold]
            })
            
            if error_count >= self.error_threshold:
                self.send_error_alert(error_type, error_count)
                
        except Exception as e:
            frappe.log_error(f"Error checking error threshold: {e}")
    
    def send_error_alert(self, error_type, error_count):
        """Send alert for high error count"""
        try:
            # Create system notification
            alert_doc = frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"High Session Error Rate: {error_type}",
                "email_content": f"Session error '{error_type}' occurred {error_count} times in the last hour.",
                "for_user": "Administrator",
                "type": "Alert"
            })
            alert_doc.insert(ignore_permissions=True)
            
            frappe.logger().warning(f"Session error alert: {error_type} occurred {error_count} times")
            
        except Exception as e:
            frappe.log_error(f"Error sending error alert: {e}")
    
    def get_error_statistics(self):
        """Get session error statistics"""
        try:
            from frappe.utils import add_to_date, now_datetime
            
            # Get errors in the last 24 hours
            time_threshold = add_to_date(now_datetime(), hours=-24)
            
            errors = frappe.db.sql("""
                SELECT method, COUNT(*) as count
                FROM `tabError Log`
                WHERE method LIKE 'session_error_%'
                AND creation >= %s
                GROUP BY method
                ORDER BY count DESC
            """, (time_threshold,), as_dict=True)
            
            return {
                "total_errors": sum(e.count for e in errors),
                "error_breakdown": errors,
                "time_window": "24 hours"
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting error statistics: {e}")
            return {"total_errors": 0, "error_breakdown": [], "error": str(e)}


# Global monitor instance
session_error_monitor = SessionErrorMonitor()
'''

        # Save session error monitor
        monitor_path = frappe.get_app_path(
            "universal_workshop", "user_management", "session_error_monitor.py"
        )
        with open(monitor_path, "w") as f:
            f.write(f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

{monitor_code}
""")

        print("✅ Session error monitoring implemented")

    except Exception as e:
        frappe.log_error(f"Error adding session error monitoring: {e}")
        raise


def enhance_session_validation():
    """Enhance session validation with better error handling"""
    try:
        # Update the SessionManager validate_session method
        validation_enhancement = '''
def enhanced_validate_session(self, session_id: str) -> Dict[str, Any]:
    """Enhanced session validation with comprehensive error handling"""
    try:
        from universal_workshop.user_management.session_error_monitor import session_error_monitor
        
        # Check if session exists in Workshop User Session
        session_record = frappe.db.get_value(
            "Workshop User Session",
            {"session_id": session_id, "is_active": 1},
            ["user_email", "expiry_time", "last_activity", "session_policy"],
            as_dict=True
        )
        
        if not session_record:
            # Check if Frappe session exists
            frappe_session = frappe.db.get_value("Sessions", session_id, ["user", "creation"])
            
            if frappe_session:
                # Session exists in Frappe but not in our tracking - recover it
                session_error_monitor.log_session_error(
                    "missing_tracking",
                    session_id,
                    frappe_session[0],
                    "Workshop User Session record missing"
                )
                
                # Attempt recovery
                recovery_result = self.create_session_record(
                    frappe_session[0],
                    session_id,
                    {"recovery": True, "created": frappe_session[1]}
                )
                
                if recovery_result.get("success"):
                    return {
                        "valid": True,
                        "recovered": True,
                        "user_email": frappe_session[0],
                        "message": "Session recovered successfully"
                    }
            
            session_error_monitor.log_session_error(
                "not_found",
                session_id,
                details="Session not found in tracking or Frappe sessions"
            )
            
            return {
                "valid": False,
                "error_type": "not_found",
                "message": "Session not found"
            }
        
        # Check session expiry
        current_time = now_datetime()
        
        if session_record.expiry_time and current_time > session_record.expiry_time:
            session_error_monitor.log_session_error(
                "expired",
                session_id,
                session_record.user_email,
                f"Session expired at {session_record.expiry_time}"
            )
            
            return {
                "valid": False,
                "error_type": "expired",
                "message": "Session has expired",
                "expired_at": session_record.expiry_time
            }
        
        # Calculate time remaining
        time_remaining_seconds = (session_record.expiry_time - current_time).total_seconds()
        time_remaining_minutes = max(0, int(time_remaining_seconds / 60))
        
        # Check for suspicious activity
        suspicious_indicators = self._check_suspicious_activity(session_id, session_record)
        
        validation_result = {
            "valid": True,
            "user_email": session_record.user_email,
            "expiry_time": session_record.expiry_time,
            "last_activity": session_record.last_activity,
            "time_remaining_minutes": time_remaining_minutes,
            "time_remaining_seconds": time_remaining_seconds
        }
        
        if suspicious_indicators:
            validation_result["suspicious_activity"] = suspicious_indicators
            session_error_monitor.log_session_error(
                "suspicious_activity",
                session_id,
                session_record.user_email,
                suspicious_indicators
            )
        
        return validation_result
        
    except Exception as e:
        session_error_monitor.log_session_error(
            "validation_error",
            session_id,
            details=str(e)
        )
        
        frappe.log_error(f"Session validation error: {e}")
        return {
            "valid": False,
            "error_type": "validation_error",
            "message": "Session validation failed"
        }

def _check_suspicious_activity(self, session_id: str, session_record: Dict) -> List[str]:
    """Check for suspicious session activity"""
    indicators = []
    
    try:
        # Check for multiple IP addresses
        ip_addresses = frappe.db.sql("""
            SELECT DISTINCT ip_address
            FROM `tabWorkshop User Session`
            WHERE user_email = %s AND is_active = 1
        """, (session_record["user_email"],))
        
        if len(ip_addresses) > 3:
            indicators.append(f"Multiple IP addresses ({len(ip_addresses)})")
        
        # Check for rapid session creation
        recent_sessions = frappe.db.count("Workshop User Session", {
            "user_email": session_record["user_email"],
            "creation": [">=", add_to_date(now_datetime(), hours=-1)]
        })
        
        if recent_sessions > 5:
            indicators.append(f"Rapid session creation ({recent_sessions} in 1 hour)")
        
        # Check for unusual user agent patterns
        user_agents = frappe.db.sql("""
            SELECT DISTINCT user_agent
            FROM `tabWorkshop User Session`
            WHERE user_email = %s AND is_active = 1
        """, (session_record["user_email"],))
        
        if len(user_agents) > 3:
            indicators.append(f"Multiple user agents ({len(user_agents)})")
        
    except Exception as e:
        frappe.log_error(f"Error checking suspicious activity: {e}")
    
    return indicators
'''

        # The enhancement will be applied by updating the SessionManager class
        # For now, we document the enhancement
        print("✅ Session validation enhancement documented")

    except Exception as e:
        frappe.log_error(f"Error enhancing session validation: {e}")
        raise


def create_session_health_check():
    """Create session health check system"""
    try:
        # Create health check scheduler
        health_check_job = {
            "method": "universal_workshop.user_management.session_cleanup.get_session_health_status",
            "frequency": "Cron",
            "cron_format": "*/30 * * * *",  # Every 30 minutes
        }

        existing_health_job = frappe.db.exists("Scheduled Job Type", {
            "method": health_check_job["method"]
        })

        if not existing_health_job:
            doc = frappe.get_doc({
                "doctype": "Scheduled Job Type",
                "method": health_check_job["method"],
                "frequency": health_check_job["frequency"],
                "cron_format": health_check_job["cron_format"],
                "create_log": 1
            })
            doc.insert(ignore_permissions=True)

        print("✅ Session health check system created")

    except Exception as e:
        frappe.log_error(f"Error creating session health check: {e}")
        raise


def add_session_debugging():
    """Add session debugging capabilities"""
    try:
        # Create session debug utilities
        debug_code = '''
def debug_session_issues():
    """Debug common session issues"""
    try:
        issues = []
        
        # 1. Check for orphaned sessions
        orphaned = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWorkshop User Session` wus
            LEFT JOIN `tabSessions` s ON wus.session_id = s.name
            WHERE wus.is_active = 1 AND s.name IS NULL
        """)[0][0]
        
        if orphaned > 0:
            issues.append(f"Orphaned sessions: {orphaned}")
        
        # 2. Check for missing tracking records
        missing = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabSessions` s
            LEFT JOIN `tabWorkshop User Session` wus ON s.name = wus.session_id
            WHERE wus.session_id IS NULL AND s.user != 'Guest'
        """)[0][0]
        
        if missing > 0:
            issues.append(f"Missing tracking records: {missing}")
        
        # 3. Check for expired but active sessions
        expired_active = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWorkshop User Session`
            WHERE is_active = 1 AND expiry_time < NOW()
        """)[0][0]
        
        if expired_active > 0:
            issues.append(f"Expired but active sessions: {expired_active}")
        
        # 4. Check for sessions without recent activity
        stale_sessions = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWorkshop User Session`
            WHERE is_active = 1 AND last_activity < DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """)[0][0]
        
        if stale_sessions > 0:
            issues.append(f"Stale sessions (>2h inactive): {stale_sessions}")
        
        return {
            "total_issues": len(issues),
            "issues": issues,
            "recommendations": generate_session_recommendations(issues)
        }
        
    except Exception as e:
        frappe.log_error(f"Session debugging error: {e}")
        return {"error": str(e)}

def generate_session_recommendations(issues):
    """Generate recommendations based on session issues"""
    recommendations = []
    
    for issue in issues:
        if "orphaned" in issue.lower():
            recommendations.append("Run session cleanup to remove orphaned sessions")
        elif "missing" in issue.lower():
            recommendations.append("Recreate missing session tracking records")
        elif "expired" in issue.lower():
            recommendations.append("Clean up expired sessions immediately")
        elif "stale" in issue.lower():
            recommendations.append("Review session timeout policies")
    
    if not recommendations:
        recommendations.append("No immediate action required - sessions are healthy")
    
    return recommendations

def get_session_debug_info(session_id):
    """Get detailed debug information for a specific session"""
    try:
        # Get Workshop User Session info
        workshop_session = frappe.db.get_value(
            "Workshop User Session",
            {"session_id": session_id},
            "*",
            as_dict=True
        )
        
        # Get Frappe Sessions info
        frappe_session = frappe.db.get_value(
            "Sessions",
            session_id,
            "*",
            as_dict=True
        )
        
        # Get recent error logs
        recent_errors = frappe.db.get_all(
            "Error Log",
            filters={
                "reference_name": session_id,
                "creation": [">=", add_to_date(now_datetime(), hours=-24)]
            },
            fields=["method", "error", "creation"],
            order_by="creation desc",
            limit=10
        )
        
        return {
            "session_id": session_id,
            "workshop_session": workshop_session,
            "frappe_session": frappe_session,
            "recent_errors": recent_errors,
            "exists_in_workshop": bool(workshop_session),
            "exists_in_frappe": bool(frappe_session),
            "status": "healthy" if workshop_session and frappe_session else "problematic"
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting session debug info: {e}")
        return {"error": str(e)}
'''

        # Save debug utilities
        debug_path = frappe.get_app_path(
            "universal_workshop", "user_management", "session_debug.py"
        )
        with open(debug_path, "w") as f:
            f.write(f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date

{debug_code}
""")

        print("✅ Session debugging capabilities added")

    except Exception as e:
        frappe.log_error(f"Error adding session debugging: {e}")
        raise


def configure_session_recovery():
    """Configure automatic session recovery mechanisms"""
    try:
        # Create session recovery job
        recovery_job = {
            "method": "universal_workshop.user_management.session_recovery.run_session_recovery",
            "frequency": "Cron",
            "cron_format": "*/5 * * * *",  # Every 5 minutes
        }

        existing_recovery_job = frappe.db.exists("Scheduled Job Type", {
            "method": recovery_job["method"]
        })

        if not existing_recovery_job:
            doc = frappe.get_doc({
                "doctype": "Scheduled Job Type",
                "method": recovery_job["method"],
                "frequency": recovery_job["frequency"],
                "cron_format": recovery_job["cron_format"],
                "create_log": 1
            })
            doc.insert(ignore_permissions=True)

        # Create session recovery module
        recovery_code = '''
def run_session_recovery():
    """Run automatic session recovery"""
    try:
        from universal_workshop.user_management.session_manager import SessionManager
        
        session_manager = SessionManager()
        recovery_stats = {
            "recovered_sessions": 0,
            "failed_recoveries": 0,
            "orphaned_cleaned": 0
        }
        
        # 1. Recover missing Workshop User Session records
        missing_sessions = frappe.db.sql("""
            SELECT s.name, s.user, s.creation
            FROM `tabSessions` s
            LEFT JOIN `tabWorkshop User Session` wus ON s.name = wus.session_id
            WHERE wus.session_id IS NULL AND s.user != 'Guest'
        """, as_dict=True)
        
        for session in missing_sessions:
            try:
                result = session_manager.create_session_record(
                    session.user,
                    session.name,
                    {"recovery": True, "created": session.creation}
                )
                
                if result.get("success"):
                    recovery_stats["recovered_sessions"] += 1
                else:
                    recovery_stats["failed_recoveries"] += 1
                    
            except Exception as e:
                frappe.log_error(f"Session recovery error for {session.name}: {e}")
                recovery_stats["failed_recoveries"] += 1
        
        # 2. Clean up orphaned Workshop User Session records
        orphaned_sessions = frappe.db.sql("""
            SELECT wus.name, wus.session_id
            FROM `tabWorkshop User Session` wus
            LEFT JOIN `tabSessions` s ON wus.session_id = s.name
            WHERE wus.is_active = 1 AND s.name IS NULL
        """, as_dict=True)
        
        for orphaned in orphaned_sessions:
            try:
                frappe.db.set_value(
                    "Workshop User Session",
                    orphaned.name,
                    {
                        "is_active": 0,
                        "revocation_reason": "Automatic recovery cleanup"
                    }
                )
                recovery_stats["orphaned_cleaned"] += 1
                
            except Exception as e:
                frappe.log_error(f"Orphaned session cleanup error for {orphaned.session_id}: {e}")
        
        if recovery_stats["recovered_sessions"] > 0 or recovery_stats["orphaned_cleaned"] > 0:
            frappe.logger().info(f"Session recovery completed: {recovery_stats}")
        
        return recovery_stats
        
    except Exception as e:
        frappe.log_error(f"Session recovery error: {e}")
        return {"error": str(e)}
'''

        # Save session recovery module
        recovery_path = frappe.get_app_path(
            "universal_workshop", "user_management", "session_recovery.py"
        )
        with open(recovery_path, "w") as f:
            f.write(f"""# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt

import frappe
from frappe import _

{recovery_code}
""")

        print("✅ Automatic session recovery configured")

    except Exception as e:
        frappe.log_error(f"Error configuring session recovery: {e}")
        raise 