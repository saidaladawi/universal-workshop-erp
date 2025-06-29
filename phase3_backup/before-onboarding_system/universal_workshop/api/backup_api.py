import frappe
import os
import json
import datetime
import glob
from frappe import _

@frappe.whitelist()
def get_backup_status():
    """Get current backup status for dashboard"""
    
    backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
    
    if not os.path.exists(backup_dir):
        return {
            'status': 'error',
            'message': 'Backup directory not found',
            'backup_count': 0,
            'latest_backup': None
        }
    
    try:
        # Get all metadata files
        metadata_files = glob.glob(os.path.join(backup_dir, '*_metadata.json'))
        
        if not metadata_files:
            return {
                'status': 'warning',
                'message': 'No backups found',
                'backup_count': 0,
                'latest_backup': None
            }
        
        # Find latest backup
        latest_backup = None
        latest_time = None
        
        for metadata_file in sorted(metadata_files, reverse=True):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup_time = datetime.datetime.fromisoformat(metadata['created_at'])
                if latest_time is None or backup_time > latest_time:
                    latest_time = backup_time
                    latest_backup = {
                        'backup_id': metadata['backup_id'],
                        'created_at': metadata['created_at'],
                        'backup_type': metadata['backup_type'],
                        'file_count': len(metadata['backup_files']),
                        'age_hours': round((datetime.datetime.now() - backup_time).total_seconds() / 3600, 1)
                    }
                    
                    # Check file sizes
                    if 'file_sizes' in metadata:
                        total_size = sum(metadata['file_sizes'].values())
                        latest_backup['total_size_mb'] = round(total_size / (1024 * 1024), 2)
                
                break  # We only need the latest
                
            except Exception as e:
                continue
        
        # Determine status
        if latest_backup:
            if latest_backup['age_hours'] > 26:  # More than 26 hours old
                status = 'warning'
                message = f"Latest backup is {latest_backup['age_hours']} hours old"
            else:
                status = 'healthy'
                message = 'Backup system is healthy'
        else:
            status = 'error'
            message = 'Could not read backup metadata'
        
        return {
            'status': status,
            'message': message,
            'backup_count': len(metadata_files),
            'latest_backup': latest_backup
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking backups: {str(e)}',
            'backup_count': 0,
            'latest_backup': None
        }

@frappe.whitelist()
def get_backup_history(limit=10):
    """Get backup history for dashboard"""
    
    backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
    
    if not os.path.exists(backup_dir):
        return []
    
    try:
        backups = []
        metadata_files = glob.glob(os.path.join(backup_dir, '*_metadata.json'))
        
        for metadata_file in sorted(metadata_files, reverse=True)[:limit]:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup_info = {
                    'backup_id': metadata['backup_id'],
                    'created_at': metadata['created_at'],
                    'backup_type': metadata['backup_type'],
                    'file_count': len(metadata['backup_files']),
                    'files_exist': all(
                        os.path.exists(path) for path in metadata['backup_files'].values()
                    )
                }
                
                # Add file size info
                if 'file_sizes' in metadata:
                    total_size = sum(metadata['file_sizes'].values())
                    backup_info['total_size_mb'] = round(total_size / (1024 * 1024), 2)
                
                backups.append(backup_info)
                
            except Exception as e:
                continue
        
        return backups
        
    except Exception as e:
        frappe.log_error(f"Error getting backup history: {str(e)}", "Backup History Error")
        return []
