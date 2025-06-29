import frappe
import os
import json
import datetime
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from frappe import _

class BackupScheduler:
    """Advanced backup scheduling and monitoring system"""
    
    def __init__(self):
        self.site_name = "universal.local"
        self.bench_path = "/home/said/frappe-dev/frappe-bench"
        self.backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
        
    def setup_cron_jobs(self):
        """Setup cron jobs for automated backups"""
        
        print(f"\n⏰ Setting up cron jobs for automated backups")
        print("="*70)
        
        cron_jobs = [
            {
                'name': 'daily_backup',
                'schedule': '0 2 * * *',  # 2 AM daily
                'command': f'cd {self.bench_path} && bench --site {self.site_name} execute universal_workshop.universal_workshop.utils.backup_automation.daily_backup',
                'description': 'Daily database backup at 2 AM'
            },
            {
                'name': 'weekly_backup',
                'schedule': '0 3 * * 0',  # 3 AM on Sundays
                'command': f'cd {self.bench_path} && bench --site {self.site_name} execute universal_workshop.universal_workshop.utils.backup_automation.weekly_backup',
                'description': 'Weekly full backup at 3 AM on Sundays'
            },
            {
                'name': 'monthly_backup',
                'schedule': '0 4 1 * *',  # 4 AM on 1st of each month
                'command': f'cd {self.bench_path} && bench --site {self.site_name} execute universal_workshop.universal_workshop.utils.backup_automation.monthly_backup',
                'description': 'Monthly full backup at 4 AM on 1st of month'
            }
        ]
        
        # Create cron script
        cron_script_path = os.path.join(self.bench_path, 'backup_cron_setup.sh')
        
        with open(cron_script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Universal Workshop ERP Backup Cron Jobs\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            f.write("# Remove existing backup cron jobs\n")
            f.write("crontab -l | grep -v 'universal_workshop.*backup' | crontab -\n\n")
            
            f.write("# Add new backup cron jobs\n")
            f.write("(\n")
            f.write("crontab -l 2>/dev/null\n")
            
            for job in cron_jobs:
                f.write(f"echo '{job['schedule']} {job['command']} # {job['description']}'\n")
            
            f.write(") | crontab -\n")
            f.write("\necho 'Backup cron jobs installed successfully'\n")
        
        # Make script executable
        os.chmod(cron_script_path, 0o755)
        
        print(f"✅ Cron setup script created: {cron_script_path}")
        print(f"📋 Scheduled backup jobs:")
        
        for job in cron_jobs:
            print(f"   ⏰ {job['name']}: {job['description']}")
        
        print(f"\n💡 To install cron jobs, run: bash {cron_script_path}")
        
        return {
            'script_path': cron_script_path,
            'jobs': cron_jobs
        }
    
    def create_backup_monitoring_script(self):
        """Create monitoring script for backup health"""
        
        print(f"\n📊 Creating backup monitoring script")
        print("-" * 50)
        
        monitor_script_path = os.path.join(self.bench_path, 'backup_monitor.py')
        
        monitor_script_content = f'''#!/usr/bin/env python3
"""
Universal Workshop ERP Backup Monitoring Script
Monitors backup health and sends alerts if needed
"""

import os
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class BackupMonitor:
    def __init__(self):
        self.backup_dir = "{self.backup_dir}"
        self.site_name = "{self.site_name}"
        self.max_backup_age_hours = 26  # Alert if no backup in 26 hours
        self.min_backup_count = 3  # Alert if less than 3 backups
        
    def check_backup_health(self):
        """Check overall backup health"""
        
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
        metadata_files = [f for f in os.listdir(self.backup_dir) if f.endswith('_metadata.json')]
        health_report['backup_count'] = len(metadata_files)
        
        if health_report['backup_count'] == 0:
            health_report['status'] = 'CRITICAL'
            health_report['alerts'].append('No backups found')
            return health_report
        
        # Check latest backup age
        latest_backup_time = None
        for metadata_file in metadata_files:
            try:
                metadata_path = os.path.join(self.backup_dir, metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                backup_time = datetime.datetime.fromisoformat(metadata['created_at'])
                if latest_backup_time is None or backup_time > latest_backup_time:
                    latest_backup_time = backup_time
                
                # Check if backup files exist
                for file_type, file_path in metadata['backup_files'].items():
                    if not os.path.exists(file_path):
                        health_report['missing_files'].append(f"{{metadata['backup_id']}}:{{file_type}}")
                        
            except Exception as e:
                health_report['alerts'].append(f"Could not read metadata {{metadata_file}}: {{str(e)}}")
        
        if latest_backup_time:
            age_hours = (datetime.datetime.now() - latest_backup_time).total_seconds() / 3600
            health_report['latest_backup_age_hours'] = round(age_hours, 2)
            
            # Check backup age
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
    
    def send_alert_email(self, health_report):
        """Send email alert if backup issues are found"""
        
        if health_report['status'] == 'HEALTHY':
            return
        
        # Email configuration (customize as needed)
        smtp_server = "localhost"
        smtp_port = 587
        sender_email = "admin@workshop.local"
        recipient_email = "admin@workshop.local"
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Backup Alert - {health_report['status']} - {self.site_name}"
            
            # Email body
            body = "Universal Workshop ERP Backup Alert\n\n"
            body += f"Site: {self.site_name}\n"
            body += f"Status: {health_report['status']}\n"
            body += f"Timestamp: {health_report['timestamp']}\n\n"
            body += "Backup Statistics:\n"
            body += f"- Total Backups: {health_report['backup_count']}\n"
            body += f"- Latest Backup Age: {health_report['latest_backup_age_hours']} hours\n"
            body += f"- Missing Files: {len(health_report['missing_files'])}\n\n"
            body += "Alerts:\n"
            
            for alert in health_report['alerts']:
                body += f"• {alert}\n"
            
            body += "\nPlease check the backup system immediately.\n\n"
            body += f"Backup Directory: {self.backup_dir}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (uncomment when email is configured)
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.sendmail(sender_email, recipient_email, msg.as_string())
            # server.quit()
            
            print(f"📧 Alert email prepared (email sending disabled)")
            
        except Exception as e:
            print(f"❌ Could not send alert email: {{str(e)}}")

if __name__ == "__main__":
    monitor = BackupMonitor()
    health_report = monitor.check_backup_health()
    
    if health_report['status'] != 'HEALTHY':
        monitor.send_alert_email(health_report)
'''
        
        with open(monitor_script_path, 'w') as f:
            f.write(monitor_script_content)
        
        # Make script executable
        os.chmod(monitor_script_path, 0o755)
        
        print(f"✅ Backup monitoring script created: {monitor_script_path}")
        print(f"💡 Run monitoring: python3 {monitor_script_path}")
        
        return monitor_script_path
    
    def create_backup_dashboard_api(self):
        """Create API endpoints for backup dashboard"""
        
        print(f"\n📊 Creating backup dashboard API")
        print("-" * 50)
        
        api_content = '''
import frappe
import os
import json
import datetime
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
        metadata_files = [f for f in os.listdir(backup_dir) if f.endswith('_metadata.json')]
        
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
                metadata_path = os.path.join(backup_dir, metadata_file)
                with open(metadata_path, 'r') as f:
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
        metadata_files = [f for f in os.listdir(backup_dir) if f.endswith('_metadata.json')]
        
        for metadata_file in sorted(metadata_files, reverse=True)[:limit]:
            try:
                metadata_path = os.path.join(backup_dir, metadata_file)
                with open(metadata_path, 'r') as f:
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
        
        api_file_path = os.path.join(
            self.bench_path, 
            "apps/universal_workshop/universal_workshop/api/backup_api.py"
        )
        
        # Ensure api directory exists
        api_dir = os.path.dirname(api_file_path)
        os.makedirs(api_dir, exist_ok=True)
        
        with open(api_file_path, 'w') as f:
            f.write(api_content)
        
        print(f"✅ Backup dashboard API created: {api_file_path}")
        print(f"🔗 API endpoints:")
        print(f"   • /api/method/universal_workshop.api.backup_api.get_backup_status")
        print(f"   • /api/method/universal_workshop.api.backup_api.get_backup_history")
        
        return api_file_path

def setup_comprehensive_backup_system():
    """Setup complete backup automation system"""
    
    print(f"\n" + "="*70)
    print("UNIVERSAL WORKSHOP ERP - COMPREHENSIVE BACKUP SYSTEM SETUP")
    print("="*70)
    
    scheduler = BackupScheduler()
    
    try:
        # Setup cron jobs
        print(f"\n1️⃣  Setting up automated backup scheduling...")
        cron_setup = scheduler.setup_cron_jobs()
        
        # Create monitoring script
        print(f"\n2️⃣  Creating backup monitoring system...")
        monitor_script = scheduler.create_backup_monitoring_script()
        
        # Create dashboard API
        print(f"\n3️⃣  Creating backup dashboard API...")
        api_file = scheduler.create_backup_dashboard_api()
        
        print(f"\n🎉 BACKUP SYSTEM SETUP COMPLETED!")
        print("="*70)
        print(f"📋 Next steps:")
        print(f"   1. Install cron jobs: bash {cron_setup['script_path']}")
        print(f"   2. Test monitoring: python3 {monitor_script}")
        print(f"   3. Access backup status via API endpoints")
        print(f"   4. Configure email alerts in monitoring script")
        
        return {
            'status': 'success',
            'cron_setup': cron_setup,
            'monitor_script': monitor_script,
            'api_file': api_file
        }
        
    except Exception as e:
        print(f"\n❌ BACKUP SYSTEM SETUP FAILED: {str(e)}")
        raise

if __name__ == "__main__":
    setup_comprehensive_backup_system()
