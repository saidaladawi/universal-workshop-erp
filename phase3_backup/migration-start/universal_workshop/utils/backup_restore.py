import frappe
import os
import json
import subprocess
import datetime
from pathlib import Path
from frappe import _

class BackupRestoreManager:
    """Backup restoration and recovery management"""
    
    def __init__(self):
        self.backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
        self.site_name = "universal.local"
        self.bench_path = "/home/said/frappe-dev/frappe-bench"
    
    def list_available_backups(self):
        """List all available backups with metadata"""
        
        print(f"\n📋 Available Backups for {self.site_name}")
        print("="*70)
        
        if not os.path.exists(self.backup_dir):
            print("❌ No backup directory found")
            return []
        
        backups = []
        metadata_files = [f for f in os.listdir(self.backup_dir) if f.endswith('_metadata.json')]
        
        for metadata_file in sorted(metadata_files, reverse=True):
            try:
                metadata_path = os.path.join(self.backup_dir, metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Check if backup files still exist
                files_exist = all(
                    os.path.exists(path) for path in metadata['backup_files'].values()
                )
                
                backup_info = {
                    'backup_id': metadata['backup_id'],
                    'created_at': metadata['created_at'],
                    'backup_type': metadata['backup_type'],
                    'files_exist': files_exist,
                    'metadata_file': metadata_path,
                    'metadata': metadata
                }
                
                backups.append(backup_info)
                
                # Display backup info
                created_date = datetime.datetime.fromisoformat(metadata['created_at'])
                status = "✅ AVAILABLE" if files_exist else "❌ MISSING FILES"
                
                print(f"📦 {metadata['backup_id']}")
                print(f"   📅 Created: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   🏷️  Type: {metadata['backup_type']}")
                print(f"   📁 Files: {', '.join(metadata['backup_files'].keys())}")
                print(f"   📊 Status: {status}")
                
                if metadata.get('database_info'):
                    db_info = metadata['database_info']
                    print(f"   🗄️  DB Size: {db_info.get('size_mb', 'N/A')} MB")
                
                print()
                
            except Exception as e:
                print(f"⚠️  Could not read metadata for {metadata_file}: {str(e)}")
        
        return backups
    
    def restore_from_backup(self, backup_id, restore_files=True, confirmation_required=True):
        """Restore from a specific backup"""
        
        print(f"\n🔄 Restoring from backup: {backup_id}")
        print("="*70)
        
        # Find backup metadata
        backup_metadata = None
        for backup in self.list_available_backups():
            if backup['backup_id'] == backup_id:
                backup_metadata = backup
                break
        
        if not backup_metadata:
            raise Exception(f"Backup {backup_id} not found")
        
        if not backup_metadata['files_exist']:
            raise Exception(f"Backup files for {backup_id} are missing")
        
        metadata = backup_metadata['metadata']
        
        # Safety confirmation
        if confirmation_required:
            print(f"⚠️  WARNING: This will restore the database to the state from:")
            print(f"   📅 {metadata['created_at']}")
            print(f"   🏷️  Type: {metadata['backup_type']}")
            print(f"   📁 Files included: {restore_files}")
            print(f"\n⚠️  Current data will be REPLACED. Continue? (This is automated, proceeding...)")
        
        try:
            # Stop any running processes
            print(f"\n🛑 Stopping bench processes...")
            subprocess.run(["bench", "stop"], cwd=self.bench_path, check=False)
            
            # Enable maintenance mode
            print(f"🔧 Enabling maintenance mode...")
            subprocess.run(
                ["bench", "--site", self.site_name, "set-maintenance-mode", "on"],
                cwd=self.bench_path,
                check=True
            )
            
            # Restore database
            if 'database' in metadata['backup_files']:
                print(f"🗄️  Restoring database...")
                db_backup_path = metadata['backup_files']['database']
                
                restore_cmd = [
                    "bench", "--site", self.site_name, "restore", db_backup_path
                ]
                
                result = subprocess.run(
                    restore_cmd,
                    cwd=self.bench_path,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"Database restore failed: {result.stderr}")
                
                print(f"✅ Database restored successfully")
            
            # Restore files if requested and available
            if restore_files and 'files' in metadata['backup_files']:
                print(f"📁 Restoring files...")
                files_backup_path = metadata['backup_files']['files']
                
                # Extract files backup (assuming it's a tar file)
                extract_cmd = [
                    "tar", "-xf", files_backup_path,
                    "-C", f"/home/said/frappe-dev/frappe-bench/sites/{self.site_name}"
                ]
                
                result = subprocess.run(
                    extract_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    print(f"⚠️  Files restore failed: {result.stderr}")
                else:
                    print(f"✅ Files restored successfully")
            
            # Run migration to ensure schema is up to date
            print(f"🔄 Running migration...")
            subprocess.run(
                ["bench", "--site", self.site_name, "migrate"],
                cwd=self.bench_path,
                check=True,
                timeout=300
            )
            
            # Clear cache
            print(f"🧹 Clearing cache...")
            subprocess.run(
                ["bench", "--site", self.site_name, "clear-cache"],
                cwd=self.bench_path,
                check=True
            )
            
            # Disable maintenance mode
            print(f"🔧 Disabling maintenance mode...")
            subprocess.run(
                ["bench", "--site", self.site_name, "set-maintenance-mode", "off"],
                cwd=self.bench_path,
                check=True
            )
            
            # Restart bench
            print(f"🚀 Restarting bench...")
            subprocess.run(["bench", "start"], cwd=self.bench_path, check=False)
            
            print(f"\n🎉 Restore completed successfully!")
            print(f"📅 Restored to state from: {metadata['created_at']}")
            print(f"🏷️  Backup type: {metadata['backup_type']}")
            
            # Log restore operation
            self.log_restore_operation(backup_id, metadata)
            
            return {
                'status': 'success',
                'backup_id': backup_id,
                'restored_at': datetime.datetime.now().isoformat(),
                'metadata': metadata
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Restore operation timed out")
        except Exception as e:
            # Try to recover by disabling maintenance mode
            try:
                subprocess.run(
                    ["bench", "--site", self.site_name, "set-maintenance-mode", "off"],
                    cwd=self.bench_path,
                    check=False
                )
            except:
                pass
            
            raise Exception(f"Restore failed: {str(e)}")
    
    def create_pre_migration_backup(self):
        """Create a backup before migration operations"""
        
        print(f"\n💾 Creating pre-migration backup...")
        print("-" * 50)
        
        try:
            from universal_workshop.universal_workshop.utils.backup_automation import BackupManager
            
            backup_manager = BackupManager()
            metadata = backup_manager.create_comprehensive_backup(
                backup_type="pre-migration", 
                include_files=True
            )
            
            print(f"✅ Pre-migration backup created: {metadata['backup_id']}")
            return metadata
            
        except Exception as e:
            print(f"❌ Pre-migration backup failed: {str(e)}")
            raise
    
    def create_post_migration_backup(self):
        """Create a backup after successful migration"""
        
        print(f"\n💾 Creating post-migration backup...")
        print("-" * 50)
        
        try:
            from universal_workshop.universal_workshop.utils.backup_automation import BackupManager
            
            backup_manager = BackupManager()
            metadata = backup_manager.create_comprehensive_backup(
                backup_type="post-migration", 
                include_files=True
            )
            
            print(f"✅ Post-migration backup created: {metadata['backup_id']}")
            return metadata
            
        except Exception as e:
            print(f"❌ Post-migration backup failed: {str(e)}")
            raise
    
    def validate_backup_before_restore(self, backup_id):
        """Validate backup integrity before restore"""
        
        print(f"\n🔍 Validating backup before restore: {backup_id}")
        print("-" * 50)
        
        # Find backup metadata
        backup_metadata = None
        for backup in self.list_available_backups():
            if backup['backup_id'] == backup_id:
                backup_metadata = backup
                break
        
        if not backup_metadata:
            raise Exception(f"Backup {backup_id} not found")
        
        metadata = backup_metadata['metadata']
        validation_results = {
            'backup_id': backup_id,
            'file_checks': {},
            'checksum_checks': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Check file existence
        for file_type, file_path in metadata['backup_files'].items():
            if os.path.exists(file_path):
                validation_results['file_checks'][file_type] = 'EXISTS'
                print(f"✅ {file_type} file exists")
                
                # Verify checksum if available
                if file_type in metadata.get('checksums', {}):
                    from universal_workshop.universal_workshop.utils.backup_automation import BackupManager
                    backup_manager = BackupManager()
                    
                    current_checksum = backup_manager.calculate_checksum(file_path)
                    expected_checksum = metadata['checksums'][file_type]
                    
                    if current_checksum == expected_checksum:
                        validation_results['checksum_checks'][file_type] = 'VALID'
                        print(f"✅ {file_type} checksum valid")
                    else:
                        validation_results['checksum_checks'][file_type] = 'INVALID'
                        print(f"❌ {file_type} checksum invalid")
            else:
                validation_results['file_checks'][file_type] = 'MISSING'
                print(f"❌ {file_type} file missing")
        
        # Determine overall status
        file_issues = [v for v in validation_results['file_checks'].values() if v != 'EXISTS']
        checksum_issues = [v for v in validation_results['checksum_checks'].values() if v != 'VALID']
        
        if not file_issues and not checksum_issues:
            validation_results['overall_status'] = 'VALID'
            print(f"🎉 Backup validation PASSED")
        elif file_issues:
            validation_results['overall_status'] = 'MISSING_FILES'
            print(f"❌ Backup validation FAILED: Missing files")
        elif checksum_issues:
            validation_results['overall_status'] = 'CHECKSUM_MISMATCH'
            print(f"⚠️  Backup validation WARNING: Checksum mismatch")
        
        return validation_results
    
    def log_restore_operation(self, backup_id, metadata):
        """Log restore operation to database"""
        try:
            restore_log = frappe.new_doc("Error Log")  # Using Error Log as a simple log table
            restore_log.method = "Backup Restored"
            restore_log.error = json.dumps({
                'backup_id': backup_id,
                'restored_at': datetime.datetime.now().isoformat(),
                'original_backup_date': metadata['created_at'],
                'backup_type': metadata['backup_type']
            }, indent=2)
            restore_log.insert()
            frappe.db.commit()
        except Exception as e:
            print(f"⚠️  Could not log restore operation: {str(e)}")

def emergency_restore_latest():
    """Emergency function to restore from the latest available backup"""
    
    print(f"\n🚨 EMERGENCY RESTORE - Restoring from latest backup")
    print("="*70)
    
    try:
        restore_manager = BackupRestoreManager()
        backups = restore_manager.list_available_backups()
        
        if not backups:
            raise Exception("No backups available for emergency restore")
        
        # Find the latest valid backup
        latest_backup = None
        for backup in backups:
            if backup['files_exist']:
                latest_backup = backup
                break
        
        if not latest_backup:
            raise Exception("No valid backups found for emergency restore")
        
        print(f"🔄 Using backup: {latest_backup['backup_id']}")
        print(f"📅 Created: {latest_backup['created_at']}")
        
        # Perform restore
        result = restore_manager.restore_from_backup(
            latest_backup['backup_id'],
            restore_files=True,
            confirmation_required=False
        )
        
        print(f"🎉 Emergency restore completed successfully!")
        return result
        
    except Exception as e:
        print(f"❌ Emergency restore failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    restore_manager = BackupRestoreManager()
    restore_manager.list_available_backups()
