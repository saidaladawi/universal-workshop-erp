#!/usr/bin/env python3
"""
Universal Workshop ERP - Backup Automation Setup
Creates comprehensive backup scheduling and monitoring system
"""

import os
import json
import datetime

def create_backup_system():
    print("="*70)
    print("UNIVERSAL WORKSHOP ERP - COMPREHENSIVE BACKUP SYSTEM SETUP")
    print("="*70)
    
    bench_path = "/home/said/frappe-dev/frappe-bench"
    site_name = "universal.local"
    backup_dir = f"{bench_path}/sites/{site_name}/private/backups"
    
    # 1. Create cron setup script
    print("\n1️⃣  Creating automated backup scheduling...")
    
    cron_script_content = """#!/bin/bash
# Universal Workshop ERP Backup Cron Jobs
# Generated automatically - do not edit manually

echo "Setting up Universal Workshop ERP backup cron jobs..."

# Remove existing backup cron jobs
crontab -l | grep -v "universal_workshop.*backup" | crontab -

# Add new backup cron jobs
(
crontab -l 2>/dev/null
echo "0 2 * * * cd /home/said/frappe-dev/frappe-bench && bench --site universal.local execute universal_workshop.universal_workshop.utils.backup_automation.daily_backup # Daily database backup at 2 AM"
echo "0 3 * * 0 cd /home/said/frappe-dev/frappe-bench && bench --site universal.local execute universal_workshop.universal_workshop.utils.backup_automation.weekly_backup # Weekly full backup at 3 AM on Sundays"
echo "0 4 1 * * cd /home/said/frappe-dev/frappe-bench && bench --site universal.local execute universal_workshop.universal_workshop.utils.backup_automation.monthly_backup # Monthly full backup at 4 AM on 1st of month"
) | crontab -

echo "Backup cron jobs installed successfully"
echo "Current backup cron jobs:"
crontab -l | grep -E "(backup|universal_workshop)"
"""
    
    cron_script_path = f"{bench_path}/backup_cron_setup.sh"
    with open(cron_script_path, 'w') as f:
        f.write(cron_script_content)
    
    os.chmod(cron_script_path, 0o755)
    print(f"✅ Cron setup script created: {cron_script_path}")
    
    # 2. Create backup monitoring script
    print("\n2️⃣  Creating backup monitoring system...")
    
    monitor_script_content = f"""#!/usr/bin/env python3
'''
Universal Workshop ERP Backup Monitoring Script
Monitors backup health and sends alerts if needed
'''

import os
import json
import datetime
import glob

class BackupMonitor:
    def __init__(self):
        self.backup_dir = "{backup_dir}"
        self.site_name = "{site_name}"
        self.max_backup_age_hours = 26
        self.min_backup_count = 3
        
    def check_backup_health(self):
        print(f"🔍 Checking backup health for {{self.site_name}}")
        print("="*50)
        
        health_report = {{
            'timestamp': datetime.datetime.now().isoformat(),
            'backup_count': 0,
            'latest_backup_age_hours': None,
            'missing_files': [],
            'status': 'UNKNOWN',
            'alerts': []
        }}
        
        if not os.path.exists(self.backup_dir):
            health_report['status'] = 'CRITICAL'
            health_report['alerts'].append('Backup directory does not exist')
            return health_report
        
        # Get all metadata files
        metadata_files = glob.glob(os.path.join(self.backup_dir, '*_metadata.json'))
        health_report['backup_count'] = len(metadata_files)
        
        if health_report['backup_count'] == 0:
            health_report['status'] = 'CRITICAL'
            health_report['alerts'].append('No backups found')
            return health_report
        
        # Check latest backup age
        latest_backup_time = None
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup_time = datetime.datetime.fromisoformat(metadata['created_at'])
                if latest_backup_time is None or backup_time > latest_backup_time:
                    latest_backup_time = backup_time
                
                # Check if backup files exist
                for file_type, file_path in metadata['backup_files'].items():
                    if not os.path.exists(file_path):
                        health_report['missing_files'].append(f"{{metadata['backup_id']}}:{{file_type}}")
                        
            except Exception as e:
                health_report['alerts'].append(f"Could not read metadata {{os.path.basename(metadata_file)}}: {{str(e)}}")
        
        if latest_backup_time:
            age_hours = (datetime.datetime.now() - latest_backup_time).total_seconds() / 3600
            health_report['latest_backup_age_hours'] = round(age_hours, 2)
            
            if age_hours > self.max_backup_age_hours:
                health_report['alerts'].append(f'Latest backup is {{age_hours:.1f}} hours old (max: {{self.max_backup_age_hours}})')
        
        # Check backup count
        if health_report['backup_count'] < self.min_backup_count:
            health_report['alerts'].append(f'Only {{health_report["backup_count"]}} backups found (min: {{self.min_backup_count}})')
        
        # Check missing files
        if health_report['missing_files']:
            health_report['alerts'].append(f'{{len(health_report["missing_files"])}} backup files are missing')
        
        # Determine overall status
        if health_report['alerts']:
            if any('CRITICAL' in alert or 'No backups' in alert for alert in health_report['alerts']):
                health_report['status'] = 'CRITICAL'
            else:
                health_report['status'] = 'WARNING'
        else:
            health_report['status'] = 'HEALTHY'
        
        # Print report
        print(f"📊 Backup Count: {{health_report['backup_count']}}")
        if health_report['latest_backup_age_hours']:
            print(f"⏰ Latest Backup Age: {{health_report['latest_backup_age_hours']:.1f}} hours")
        print(f"🎯 Status: {{health_report['status']}}")
        
        if health_report['alerts']:
            print(f"⚠️  Alerts:")
            for alert in health_report['alerts']:
                print(f"   • {{alert}}")
        else:
            print(f"✅ No issues found")
        
        return health_report

if __name__ == "__main__":
    monitor = BackupMonitor()
    health_report = monitor.check_backup_health()
    
    # Save report
    report_file = os.path.join(monitor.backup_dir, 'health_report.json')
    try:
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(health_report, f, indent=2)
        print(f"\\n📄 Health report saved: {{report_file}}")
    except Exception as e:
        print(f"\\n❌ Could not save health report: {{str(e)}}")
"""
    
    monitor_script_path = f"{bench_path}/backup_monitor.py"
    with open(monitor_script_path, 'w') as f:
        f.write(monitor_script_content)
    
    os.chmod(monitor_script_path, 0o755)
    print(f"✅ Backup monitoring script created: {monitor_script_path}")
    
    # 3. Create backup dashboard API
    print("\n3️⃣  Creating backup dashboard API...")
    
    api_content = '''
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
'''
    
    # Ensure api directory exists
    api_dir = f"{bench_path}/apps/universal_workshop/universal_workshop/api"
    os.makedirs(api_dir, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = f"{api_dir}/__init__.py"
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Universal Workshop API Module\n")
    
    api_file_path = f"{api_dir}/backup_api.py"
    with open(api_file_path, 'w') as f:
        f.write(api_content)
    
    print(f"✅ Backup dashboard API created: {api_file_path}")
    
    # 4. Summary
    print("\n🎉 BACKUP SYSTEM SETUP COMPLETED!")
    print("="*70)
    print(f"📋 Components created:")
    print(f"   1. Cron setup script: {cron_script_path}")
    print(f"   2. Monitoring script: {monitor_script_path}")
    print(f"   3. Dashboard API: {api_file_path}")
    
    print(f"\n📋 Next steps:")
    print(f"   1. Install cron jobs: bash {cron_script_path}")
    print(f"   2. Test monitoring: python3 {monitor_script_path}")
    print(f"   3. Access backup status via API endpoints:")
    print(f"      • /api/method/universal_workshop.api.backup_api.get_backup_status")
    print(f"      • /api/method/universal_workshop.api.backup_api.get_backup_history")
    
    return True

if __name__ == "__main__":
    create_backup_system()
