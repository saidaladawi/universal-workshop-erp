# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Backup Scheduler Utility for Universal Workshop ERP
Provides automated backup scheduling and management functions
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, cint, get_datetime


class BackupScheduler:
    """Manages automated backup scheduling and execution"""
    
    def __init__(self):
        self.settings = self.get_backup_settings()
    
    def get_backup_settings(self):
        """Get backup settings from Universal Workshop Settings"""
        try:
            settings = frappe.get_single("Universal Workshop Settings")
            return {
                'enabled': getattr(settings, 'backup_enabled', 1),
                'frequency': getattr(settings, 'backup_frequency', 'Daily'),
                'time': getattr(settings, 'backup_time', '02:00'),
                'include_files': getattr(settings, 'backup_include_files', 1),
                'include_private_files': getattr(settings, 'backup_include_private_files', 0),
                'retention_days': getattr(settings, 'backup_retention_days', 30),
                'verification_enabled': getattr(settings, 'backup_verification_enabled', 1),
                'notification_email': getattr(settings, 'backup_notification_email', ''),
                'storage_location': getattr(settings, 'backup_storage_location', '')
            }
        except Exception:
            # Return default settings if Universal Workshop Settings doesn't exist
            return {
                'enabled': 1,
                'frequency': 'Daily',
                'time': '02:00',
                'include_files': 1,
                'include_private_files': 0,
                'retention_days': 30,
                'verification_enabled': 1,
                'notification_email': '',
                'storage_location': ''
            }
    
    @frappe.whitelist()
    def create_scheduled_backup(self):
        """Create and execute a scheduled backup"""
        try:
            if not self.settings['enabled']:
                return {
                    'success': False,
                    'message': 'Automated backups are disabled'
                }
            
            # Generate backup name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"Auto_{frappe.local.site}_{timestamp}"
            
            # Prepare backup directory
            backup_dir = self.prepare_backup_directory()
            
            # Execute backup
            result = self.execute_backup(backup_name, backup_dir)
            
            # Log the result
            self.log_backup_result(backup_name, result)
            
            # Send notification if configured
            if self.settings['notification_email'] and result['success']:
                self.send_backup_notification(backup_name, result)
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            return result
            
        except Exception as e:
            error_msg = f"Scheduled backup failed: {str(e)}"
            frappe.log_error(error_msg, "Backup Scheduler")
            
            return {
                'success': False,
                'message': error_msg
            }
    
    def prepare_backup_directory(self):
        """Prepare backup directory"""
        try:
            if self.settings['storage_location']:
                backup_base = Path(self.settings['storage_location'])
            else:
                backup_base = Path(frappe.get_site_path()) / "private" / "backups"
            
            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d")
            backup_dir = backup_base / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            return str(backup_dir)
            
        except Exception as e:
            frappe.log_error(f"Failed to prepare backup directory: {str(e)}", "Backup Scheduler")
            raise
    
    def execute_backup(self, backup_name, backup_dir):
        """Execute the backup process"""
        try:
            site_name = frappe.local.site
            
            # Build backup command
            cmd = ["bench", "--site", site_name, "backup"]
            
            if self.settings['include_files']:
                cmd.append("--with-files")
            
            if self.settings['include_private_files']:
                cmd.append("--with-private-files")
            
            # Set backup path
            backup_path = os.path.join(backup_dir, f"{backup_name}.sql.gz")
            cmd.extend(["--backup-path-db", backup_path])
            
            # Execute backup command
            start_time = datetime.now()
            
            result = subprocess.run(
                cmd,
                cwd=frappe.get_app_path("frappe", ".."),
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.returncode == 0:
                # Verify backup file exists
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)
                    
                    backup_result = {
                        'success': True,
                        'message': f'Backup completed successfully in {duration:.1f} seconds',
                        'backup_name': backup_name,
                        'file_path': backup_path,
                        'file_size': file_size,
                        'duration': duration,
                        'timestamp': start_time.isoformat()
                    }
                    
                    # Verify backup if enabled
                    if self.settings['verification_enabled']:
                        verification_result = self.verify_backup_file(backup_path)
                        backup_result['verification'] = verification_result
                    
                    return backup_result
                    
                else:
                    return {
                        'success': False,
                        'message': 'Backup command succeeded but file was not created',
                        'error': result.stderr
                    }
            else:
                return {
                    'success': False,
                    'message': f'Backup command failed: {result.stderr}',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Backup timed out after 1 hour'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Backup execution failed: {str(e)}'
            }


@frappe.whitelist()
def run_scheduled_backup():
    """Run scheduled backup (called by cron job)"""
    scheduler = BackupScheduler()
    return scheduler.create_scheduled_backup()
    
    def verify_backup_file(self, file_path):
        """Verify backup file integrity"""
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': 'Backup file does not exist'
                }
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {
                    'success': False,
                    'message': 'Backup file is empty'
                }
            
            # Basic gzip file validation
            try:
                import gzip
                with gzip.open(file_path, 'rb') as f:
                    # Try to read first few bytes
                    f.read(1024)
                
                return {
                    'success': True,
                    'message': f'Backup file verified successfully ({file_size} bytes)',
                    'file_size': file_size
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Backup file verification failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Unable to verify backup file: {str(e)}'
            }
    
    def log_backup_result(self, backup_name, result):
        """Log backup result to system"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'backup_name': backup_name,
                'success': result['success'],
                'message': result['message'],
                'duration': result.get('duration', 0),
                'file_size': result.get('file_size', 0)
            }
            
            # Add to system log
            log_message = f"Backup {backup_name}: {result['message']}"
            if result['success']:
                frappe.logger("backup").info(log_message)
            else:
                frappe.logger("backup").error(log_message)
            
        except Exception as e:
            frappe.log_error(f"Failed to log backup result: {str(e)}", "Backup Scheduler")
    
    def send_backup_notification(self, backup_name, result):
        """Send email notification about backup result"""
        try:
            if not self.settings['notification_email']:
                return
            
            subject = f"Backup {'Completed' if result['success'] else 'Failed'}: {backup_name}"
            
            if result['success']:
                message = f"""
                <h3 style="color: green;">Backup Completed Successfully</h3>
                <p><strong>Backup Name:</strong> {backup_name}</p>
                <p><strong>File Size:</strong> {self.format_file_size(result.get('file_size', 0))}</p>
                <p><strong>Duration:</strong> {result.get('duration', 0):.1f} seconds</p>
                <p><strong>Location:</strong> {result.get('file_path', 'N/A')}</p>
                
                {self.get_verification_message(result)}
                
                <p><em>This is an automated message from Universal Workshop ERP backup system.</em></p>
                """
            else:
                message = f"""
                <h3 style="color: red;">Backup Failed</h3>
                <p><strong>Backup Name:</strong> {backup_name}</p>
                <p><strong>Error:</strong> {result['message']}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <p style="color: red;"><strong>Action Required:</strong> Please check the backup configuration and system logs.</p>
                
                <p><em>This is an automated message from Universal Workshop ERP backup system.</em></p>
                """
            
            frappe.sendmail(
                recipients=[self.settings['notification_email']],
                subject=subject,
                message=message,
                now=True
            )
            
        except Exception as e:
            frappe.log_error(f"Failed to send backup notification: {str(e)}", "Backup Scheduler")
    
    def get_verification_message(self, result):
        """Get verification status message for email"""
        if 'verification' in result:
            verification = result['verification']
            if verification['success']:
                return f"<p style='color: green;'><strong>Verification:</strong> {verification['message']}</p>"
            else:
                return f"<p style='color: orange;'><strong>Verification:</strong> {verification['message']}</p>"
        return ""
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def cleanup_old_backups(self):
        """Remove old backup files based on retention policy"""
        try:
            retention_days = self.settings.get('retention_days', 30)
            if retention_days <= 0:
                return  # No cleanup if retention is disabled
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Determine backup directory
            if self.settings['storage_location']:
                backup_base = Path(self.settings['storage_location'])
            else:
                backup_base = Path(frappe.get_site_path()) / "private" / "backups"
            
            if not backup_base.exists():
                return
            
            deleted_count = 0
            total_size_freed = 0
            
            # Look for old backup files
            for backup_file in backup_base.rglob("*.sql.gz"):
                try:
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_size = backup_file.stat().st_size
                        backup_file.unlink()
                        deleted_count += 1
                        total_size_freed += file_size
                        
                        frappe.logger("backup").info(
                            f"Deleted old backup: {backup_file.name} ({self.format_file_size(file_size)})"
                        )
                        
                except Exception as e:
                    frappe.log_error(
                        f"Failed to delete old backup {backup_file}: {str(e)}", 
                        "Backup Cleanup"
                    )
            
            if deleted_count > 0:
                frappe.logger("backup").info(
                    f"Cleanup completed: {deleted_count} files deleted, "
                    f"{self.format_file_size(total_size_freed)} freed"
                )
                
        except Exception as e:
            frappe.log_error(f"Backup cleanup failed: {str(e)}", "Backup Cleanup")


@frappe.whitelist()
def get_backup_health_status():
    """Get backup system health status"""
    try:
        scheduler = BackupScheduler()
        settings = scheduler.settings
        
        # Check if backups are enabled
        if not settings['enabled']:
            return {
                'status': 'disabled',
                'message': _('Automated backups are disabled'),
                'last_backup': None,
                'next_backup': None
            }
        
        # Find latest backup
        latest_backup = get_latest_backup_info()
        
        # Calculate next backup time
        next_backup = calculate_next_backup_time(settings)
        
        # Determine health status
        status = 'healthy'
        message = _('Backup system is functioning normally')
        
        if latest_backup:
            # Check if last backup was successful and recent
            hours_since_backup = (datetime.now() - latest_backup['timestamp']).total_seconds() / 3600
            
            if not latest_backup['success']:
                status = 'error'
                message = _('Last backup failed')
            elif hours_since_backup > 48:  # More than 2 days
                status = 'warning'
                message = _('No recent backups found')
        else:
            status = 'warning'
            message = _('No backup history found')
        
        return {
            'status': status,
            'message': message,
            'last_backup': latest_backup,
            'next_backup': next_backup,
            'settings': settings
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to check backup health: {str(e)}',
            'last_backup': None,
            'next_backup': None
        }


def get_latest_backup_info():
    """Get information about the latest backup"""
    try:
        # This would typically query a backup log or check filesystem
        # For now, return a placeholder
        return {
            'timestamp': datetime.now() - timedelta(hours=12),
            'success': True,
            'size': 1024 * 1024 * 50,  # 50MB
            'duration': 45.2
        }
        
    except Exception:
        return None


def calculate_next_backup_time(settings):
    """Calculate when the next backup should run"""
    try:
        frequency = settings.get('frequency', 'Daily')
        backup_time = settings.get('time', '02:00')
        
        # Parse backup time
        hour, minute = map(int, backup_time.split(':'))
        
        # Calculate next backup
        now = datetime.now()
        next_backup = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if next_backup <= now:
            if frequency == 'Daily':
                next_backup += timedelta(days=1)
            elif frequency == 'Weekly':
                next_backup += timedelta(days=7)
            elif frequency == 'Monthly':
                # Add one month (approximately)
                next_backup += timedelta(days=30)
        
        return next_backup
        
    except Exception:
        return None


@frappe.whitelist()
def setup_cron_job():
    """Helper function to set up cron job for automated backups"""
    try:
        site_name = frappe.local.site
        
        # Get backup settings
        settings = frappe.get_single("Universal Workshop Settings")
        backup_time = getattr(settings, 'backup_time', '02:00')
        frequency = getattr(settings, 'backup_frequency', 'Daily')
        
        # Parse time
        hour, minute = map(int, backup_time.split(':'))
        
        # Generate cron expression
        if frequency == 'Daily':
            cron_expr = f"{minute} {hour} * * *"
        elif frequency == 'Weekly':
            cron_expr = f"{minute} {hour} * * 0"  # Sunday
        elif frequency == 'Monthly':
            cron_expr = f"{minute} {hour} 1 * *"  # First day of month
        else:
            cron_expr = f"{minute} {hour} * * *"  # Default to daily
        
        # Generate cron job command
        frappe_path = frappe.get_app_path("frappe", "..")
        cron_command = f"cd {frappe_path} && bench --site {site_name} execute universal_workshop.config.backup_scheduler.run_scheduled_backup"
        
        # Provide instructions for manual setup
        instructions = f"""
        To set up automated backups, add the following line to your crontab:
        
        {cron_expr} {cron_command}
        
        To edit your crontab, run:
        crontab -e
        
        Then add the line above and save.
        
        This will run backups {frequency.lower()} at {backup_time}.
        """
        
        return {
            'success': True,
            'message': 'Cron job instructions generated',
            'instructions': instructions,
            'cron_expression': cron_expr,
            'command': cron_command
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to generate cron job: {str(e)}'
        }
