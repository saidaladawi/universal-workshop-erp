#!/usr/bin/env python3
"""
Database Migration Script with Rollback Capabilities
Handles schema changes and data migrations for ERPNext/Frappe production deployments
"""

import os
import sys
import json
import logging
import subprocess
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/frappe_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, site_name, backup_dir="/opt/frappe/backups"):
        self.site_name = site_name
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.migration_log = self.backup_dir / "migration_log.json"
        self.load_migration_history()
    
    def load_migration_history(self):
        """Load previous migration history"""
        if self.migration_log.exists():
            with open(self.migration_log, 'r') as f:
                self.migration_history = json.load(f)
        else:
            self.migration_history = {"migrations": []}
    
    def save_migration_history(self):
        """Save migration history to log file"""
        with open(self.migration_log, 'w') as f:
            json.dump(self.migration_history, f, indent=2)
    
    def create_backup(self, backup_type="pre_migration"):
        """Create database backup before migration"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.site_name}_{backup_type}_{timestamp}"
        
        try:
            # Create database backup
            db_backup_cmd = [
                "bench", "--site", self.site_name, 
                "backup", "--backup-path", str(self.backup_dir)
            ]
            
            logger.info(f"Creating database backup: {backup_name}")
            result = subprocess.run(db_backup_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Backup failed: {result.stderr}")
            
            # Find the created backup file
            backup_files = list(self.backup_dir.glob(f"*{timestamp}*"))
            if backup_files:
                backup_file = backup_files[0]
                logger.info(f"Backup created successfully: {backup_file}")
                return str(backup_file)
            else:
                raise Exception("Backup file not found after creation")
                
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            raise
    
    def run_migration(self, version=None):
        """Run database migration"""
        try:
            migration_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create pre-migration backup
            backup_file = self.create_backup("pre_migration")
            
            # Run Frappe migrate command
            migrate_cmd = ["bench", "--site", self.site_name, "migrate"]
            
            logger.info(f"Starting migration for site: {self.site_name}")
            result = subprocess.run(migrate_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Migration failed: {result.stderr}")
                raise Exception(f"Migration failed: {result.stderr}")
            
            # Log successful migration
            migration_entry = {
                "id": migration_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "site": self.site_name,
                "version": version,
                "backup_file": backup_file,
                "status": "success",
                "output": result.stdout
            }
            
            self.migration_history["migrations"].append(migration_entry)
            self.save_migration_history()
            
            logger.info(f"Migration completed successfully: {migration_id}")
            return migration_id
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            # Log failed migration
            migration_entry = {
                "id": migration_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "site": self.site_name,
                "version": version,
                "backup_file": backup_file if 'backup_file' in locals() else None,
                "status": "failed",
                "error": str(e)
            }
            
            self.migration_history["migrations"].append(migration_entry)
            self.save_migration_history()
            raise
    
    def rollback_migration(self, migration_id=None):
        """Rollback to previous migration state"""
        try:
            if migration_id:
                # Find specific migration
                migration = None
                for m in self.migration_history["migrations"]:
                    if m["id"] == migration_id:
                        migration = m
                        break
                
                if not migration:
                    raise Exception(f"Migration {migration_id} not found")
            else:
                # Use latest successful migration
                successful_migrations = [
                    m for m in self.migration_history["migrations"] 
                    if m["status"] == "success"
                ]
                
                if not successful_migrations:
                    raise Exception("No successful migrations found for rollback")
                
                migration = successful_migrations[-1]
            
            backup_file = migration.get("backup_file")
            if not backup_file or not Path(backup_file).exists():
                raise Exception(f"Backup file not found: {backup_file}")
            
            logger.info(f"Rolling back to migration: {migration['id']}")
            
            # Restore from backup
            restore_cmd = [
                "bench", "--site", self.site_name,
                "restore", backup_file
            ]
            
            result = subprocess.run(restore_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Rollback failed: {result.stderr}")
            
            logger.info(f"Rollback completed successfully to migration: {migration['id']}")
            return migration['id']
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            raise
    
    def validate_migration(self):
        """Validate migration was successful"""
        try:
            # Run basic bench validation
            validate_cmd = ["bench", "--site", self.site_name, "doctor"]
            result = subprocess.run(validate_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Validation warnings: {result.stderr}")
            
            # Check if site is accessible
            ping_cmd = ["bench", "--site", self.site_name, "console"]
            test_script = "frappe.ping()"
            
            ping_result = subprocess.run(
                ping_cmd, 
                input=test_script, 
                capture_output=True, 
                text=True
            )
            
            if ping_result.returncode == 0:
                logger.info("Migration validation successful")
                return True
            else:
                logger.error(f"Migration validation failed: {ping_result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Migration validation error: {str(e)}")
            return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python migrate_database.py <site_name> <action> [migration_id]")
        print("Actions: migrate, rollback, validate")
        sys.exit(1)
    
    site_name = sys.argv[1]
    action = sys.argv[2]
    migration_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    migrator = DatabaseMigrator(site_name)
    
    try:
        if action == "migrate":
            result = migrator.run_migration()
            print(f"Migration completed: {result}")
            
            # Validate migration
            if migrator.validate_migration():
                print("Migration validation successful")
            else:
                print("Migration validation failed - consider rollback")
                
        elif action == "rollback":
            result = migrator.rollback_migration(migration_id)
            print(f"Rollback completed to: {result}")
            
        elif action == "validate":
            if migrator.validate_migration():
                print("Validation successful")
            else:
                print("Validation failed")
                sys.exit(1)
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
