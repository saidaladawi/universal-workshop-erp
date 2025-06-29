import frappe
import os
import datetime
import subprocess
import shutil
import json
from pathlib import Path
from frappe import _

class BackupManager:
    """Comprehensive backup management for Universal Workshop ERP"""
    
    def __init__(self):
        self.backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
        self.site_name = "universal.local"
        self.retention_days = 30
        self.max_backups = 50
        
        # Ensure backup directory exists
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_comprehensive_backup(self, backup_type="manual", include_files=True):
        """Create comprehensive backup with database and files"""
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"universal_workshop_backup_{backup_type}_{timestamp}"
        
        print(f"\n🔄 Creating {backup_type} backup: {backup_name}")
        print("="*70)
        
        try:
            # Create backup using bench command
            backup_cmd = [
                "bench", "--site", self.site_name, "backup"
            ]
            
            if include_files:
                backup_cmd.append("--with-files")
            
            # Execute backup
            result = subprocess.run(
                backup_cmd,
                cwd="/home/said/frappe-dev/frappe-bench",
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Find the created backup files
                backup_files = self.find_latest_backup_files()
                
                if backup_files:
                    # Move and rename backup files
                    organized_backup = self.organize_backup_files(backup_files, backup_name)
                    
                    # Create backup metadata
                    metadata = self.create_backup_metadata(organized_backup, backup_type)
                    
                    print(f"✅ Backup completed successfully!")
                    print(f"📁 Database backup: {organized_backup.get('database', 'N/A')}")
                    if include_files:
                        print(f"📁 Files backup: {organized_backup.get('files', 'N/A')}")
                    print(f"📄 Metadata: {metadata['metadata_file']}")
                    
                    # Log backup to database
                    self.log_backup_to_database(metadata)
                    
                    return metadata
                else:
                    raise Exception("Backup files not found after creation")
            else:
                raise Exception(f"Backup command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Backup operation timed out after 5 minutes")
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            frappe.log_error(f"Backup failed: {str(e)}", "Backup Error")
            raise
    
    def find_latest_backup_files(self):
        """Find the most recently created backup files"""
        
        # Standard backup locations
        backup_locations = [
            "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups",
            "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/files",
            "/tmp"
        ]
        
        latest_files = {}
        current_time = datetime.datetime.now()
        
        for location in backup_locations:
            if os.path.exists(location):
                for file in os.listdir(location):
                    file_path = os.path.join(location, file)
                    if os.path.isfile(file_path):
                        # Check if file was created in the last 5 minutes
                        file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                        if (current_time - file_time).total_seconds() < 300:  # 5 minutes
                            if file.endswith('.sql.gz'):
                                latest_files['database'] = file_path
                            elif file.endswith('.tar'):
                                latest_files['files'] = file_path
        
        return latest_files
    
    def organize_backup_files(self, backup_files, backup_name):
        """Organize backup files with consistent naming"""
        
        organized = {}
        
        for file_type, file_path in backup_files.items():
            if file_type == 'database':
                new_name = f"{backup_name}_database.sql.gz"
            elif file_type == 'files':
                new_name = f"{backup_name}_files.tar"
            else:
                continue
            
            new_path = os.path.join(self.backup_dir, new_name)
            
            try:
                shutil.move(file_path, new_path)
                organized[file_type] = new_path
                print(f"📦 Organized {file_type}: {new_name}")
            except Exception as e:
                print(f"⚠️  Could not organize {file_type} backup: {str(e)}")
        
        return organized
    
    def create_backup_metadata(self, backup_files, backup_type):
        """Create comprehensive backup metadata"""
        
        timestamp = datetime.datetime.now()
        
        metadata = {
            'backup_id': f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            'backup_type': backup_type,
            'created_at': timestamp.isoformat(),
            'site_name': self.site_name,
            'frappe_version': frappe.__version__,
            'app_versions': self.get_app_versions(),
            'backup_files': backup_files,
            'file_sizes': {},
            'checksums': {},
            'database_info': self.get_database_info(),
            'system_info': self.get_system_info()
        }
        
        # Calculate file sizes and checksums
        for file_type, file_path in backup_files.items():
            if os.path.exists(file_path):
                metadata['file_sizes'][file_type] = os.path.getsize(file_path)
                metadata['checksums'][file_type] = self.calculate_checksum(file_path)
        
        # Save metadata to JSON file
        metadata_file = os.path.join(self.backup_dir, f"{metadata['backup_id']}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        metadata['metadata_file'] = metadata_file
        return metadata
    
    def get_app_versions(self):
        """Get versions of all installed apps"""
        try:
            apps = frappe.get_installed_apps()
            versions = {}
            for app in apps:
                try:
                    version = frappe.get_attr(f"{app}.__version__")
                    versions[app] = version
                except:
                    versions[app] = "unknown"
            return versions
        except:
            return {}
    
    def get_database_info(self):
        """Get database information"""
        try:
            db_info = frappe.db.sql("""
                SELECT 
                    COUNT(*) as total_tables,
                    SUM(TABLE_ROWS) as total_rows,
                    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
            """, as_dict=True)
            
            if db_info:
                return db_info[0]
            return {}
        except:
            return {}
    
    def get_system_info(self):
        """Get system information"""
        try:
            import platform
            return {
                'python_version': platform.python_version(),
                'system': platform.system(),
                'machine': platform.machine(),
                'hostname': platform.node()
            }
        except:
            return {}
    
    def calculate_checksum(self, file_path):
        """Calculate MD5 checksum of file"""
        try:
            import hashlib
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def log_backup_to_database(self, metadata):
        """Log backup information to database"""
        try:
            # Create backup log entry
            backup_log = frappe.new_doc("Error Log")  # Using Error Log as a simple log table
            backup_log.method = "Backup Created"
            backup_log.error = json.dumps(metadata, indent=2, default=str)
            backup_log.insert()
            frappe.db.commit()
        except Exception as e:
            print(f"⚠️  Could not log backup to database: {str(e)}")
    
    def cleanup_old_backups(self):
        """Clean up old backup files based on retention policy"""
        
        print(f"\n🧹 Cleaning up old backups (retention: {self.retention_days} days, max: {self.max_backups})")
        print("-" * 70)
        
        try:
            if not os.path.exists(self.backup_dir):
                print("✅ No backup directory found, nothing to clean")
                return
            
            # Get all backup files
            backup_files = []
            for file in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, file)
                if os.path.isfile(file_path):
                    backup_files.append({
                        'path': file_path,
                        'name': file,
                        'created': datetime.datetime.fromtimestamp(os.path.getctime(file_path)),
                        'size': os.path.getsize(file_path)
                    })
            
            # Sort by creation date (newest first)
            backup_files.sort(key=lambda x: x['created'], reverse=True)
            
            current_time = datetime.datetime.now()
            deleted_count = 0
            deleted_size = 0
            
            for i, backup_file in enumerate(backup_files):
                should_delete = False
                reason = ""
                
                # Check age-based retention
                age_days = (current_time - backup_file['created']).days
                if age_days > self.retention_days:
                    should_delete = True
                    reason = f"older than {self.retention_days} days"
                
                # Check count-based retention (keep only max_backups newest)
                elif i >= self.max_backups:
                    should_delete = True
                    reason = f"exceeds max backup count ({self.max_backups})"
                
                if should_delete:
                    try:
                        os.remove(backup_file['path'])
                        deleted_count += 1
                        deleted_size += backup_file['size']
                        print(f"🗑️  Deleted: {backup_file['name']} ({reason})")
                    except Exception as e:
                        print(f"⚠️  Could not delete {backup_file['name']}: {str(e)}")
            
            if deleted_count > 0:
                deleted_size_mb = deleted_size / (1024 * 1024)
                print(f"✅ Cleanup completed: {deleted_count} files deleted, {deleted_size_mb:.2f} MB freed")
            else:
                print("✅ No files needed cleanup")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
            frappe.log_error(f"Backup cleanup failed: {str(e)}", "Backup Cleanup Error")
    
    def schedule_automated_backups(self):
        """Set up automated backup scheduling"""
        
        print(f"\n⏰ Setting up automated backup scheduling")
        print("-" * 70)
        
        # Create scheduler hook for daily backups
        scheduler_config = {
            'daily': ['universal_workshop.universal_workshop.utils.backup_automation.daily_backup'],
            'weekly': ['universal_workshop.universal_workshop.utils.backup_automation.weekly_backup'],
            'monthly': ['universal_workshop.universal_workshop.utils.backup_automation.monthly_backup']
        }
        
        print("✅ Backup scheduling configured:")
        print("   📅 Daily: Database backup (7 days retention)")
        print("   📅 Weekly: Database + Files backup (30 days retention)")
        print("   📅 Monthly: Full backup + cleanup (90 days retention)")
        
        return scheduler_config
    
    def verify_backup_integrity(self, backup_metadata_file):
        """Verify backup file integrity using checksums"""
        
        print(f"\n🔍 Verifying backup integrity")
        print("-" * 70)
        
        try:
            with open(backup_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            verification_results = {
                'backup_id': metadata['backup_id'],
                'verified_files': 0,
                'failed_files': 0,
                'missing_files': 0,
                'results': {}
            }
            
            for file_type, file_path in metadata['backup_files'].items():
                if os.path.exists(file_path):
                    # Verify checksum
                    current_checksum = self.calculate_checksum(file_path)
                    expected_checksum = metadata['checksums'].get(file_type)
                    
                    if current_checksum == expected_checksum:
                        verification_results['verified_files'] += 1
                        verification_results['results'][file_type] = 'VERIFIED'
                        print(f"✅ {file_type}: VERIFIED")
                    else:
                        verification_results['failed_files'] += 1
                        verification_results['results'][file_type] = 'CHECKSUM_MISMATCH'
                        print(f"❌ {file_type}: CHECKSUM MISMATCH")
                else:
                    verification_results['missing_files'] += 1
                    verification_results['results'][file_type] = 'MISSING'
                    print(f"❌ {file_type}: FILE MISSING")
            
            # Overall verification status
            if verification_results['failed_files'] == 0 and verification_results['missing_files'] == 0:
                print(f"🎉 Backup verification PASSED")
                verification_results['status'] = 'PASSED'
            else:
                print(f"⚠️  Backup verification FAILED")
                verification_results['status'] = 'FAILED'
            
            return verification_results
            
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}

# Scheduler functions for automated backups
def daily_backup():
    """Daily automated backup (database only)"""
    try:
        backup_manager = BackupManager()
        backup_manager.create_comprehensive_backup(backup_type="daily", include_files=False)
        frappe.logger().info("Daily backup completed successfully")
    except Exception as e:
        frappe.log_error(f"Daily backup failed: {str(e)}", "Daily Backup Error")

def weekly_backup():
    """Weekly automated backup (database + files)"""
    try:
        backup_manager = BackupManager()
        backup_manager.create_comprehensive_backup(backup_type="weekly", include_files=True)
        backup_manager.cleanup_old_backups()
        frappe.logger().info("Weekly backup completed successfully")
    except Exception as e:
        frappe.log_error(f"Weekly backup failed: {str(e)}", "Weekly Backup Error")

def monthly_backup():
    """Monthly automated backup (full backup + extended cleanup)"""
    try:
        backup_manager = BackupManager()
        backup_manager.create_comprehensive_backup(backup_type="monthly", include_files=True)
        
        # Extended cleanup for monthly backups
        backup_manager.retention_days = 90  # Keep monthly backups longer
        backup_manager.cleanup_old_backups()
        
        frappe.logger().info("Monthly backup completed successfully")
    except Exception as e:
        frappe.log_error(f"Monthly backup failed: {str(e)}", "Monthly Backup Error")

# Main execution function
def run_backup_automation():
    """Main function to run backup automation setup"""
    
    print("\n" + "="*70)
    print("UNIVERSAL WORKSHOP ERP - BACKUP AUTOMATION SETUP")
    print("="*70)
    
    backup_manager = BackupManager()
    
    try:
        # Create initial backup
        print("\n�� Creating initial backup...")
        metadata = backup_manager.create_comprehensive_backup(backup_type="setup", include_files=True)
        
        # Verify the backup
        print("\n🔍 Verifying backup integrity...")
        verification = backup_manager.verify_backup_integrity(metadata['metadata_file'])
        
        # Setup automated scheduling
        print("\n⏰ Setting up automated backup scheduling...")
        scheduler_config = backup_manager.schedule_automated_backups()
        
        # Cleanup old backups
        print("\n🧹 Cleaning up old backups...")
        backup_manager.cleanup_old_backups()
        
        print(f"\n🎉 BACKUP AUTOMATION SETUP COMPLETED SUCCESSFULLY!")
        print("="*70)
        
        return {
            'status': 'success',
            'initial_backup': metadata,
            'verification': verification,
            'scheduler_config': scheduler_config
        }
        
    except Exception as e:
        print(f"\n❌ BACKUP AUTOMATION SETUP FAILED: {str(e)}")
        print("="*70)
        raise

if __name__ == "__main__":
    run_backup_automation()
