#!/usr/bin/env python3
"""
Universal Workshop ERP Backup Monitoring Script
Monitors backup health and sends alerts if needed
"""

import os
import json
import datetime
import glob

class BackupMonitor:
    def __init__(self):
        self.backup_dir = "/home/said/frappe-dev/frappe-bench/sites/universal.local/private/backups"
        self.site_name = "universal.local"
        self.max_backup_age_hours = 26
        self.min_backup_count = 3
        
    def check_backup_health(self):
        print(f"🔍 Checking backup health for {self.site_name}")
        print("="*50)
        
        health_report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'backup_count': 0,
            'latest_backup_age_hours': None,
            'missing_files': [],
            'status': 'UNKNOWN',
            'alerts': []
        }
        
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
                        health_report['missing_files'].append(f"{metadata['backup_id']}:{file_type}")
                        
            except Exception as e:
                health_report['alerts'].append(f"Could not read metadata {os.path.basename(metadata_file)}: {str(e)}")
        
        if latest_backup_time:
            age_hours = (datetime.datetime.now() - latest_backup_time).total_seconds() / 3600
            health_report['latest_backup_age_hours'] = round(age_hours, 2)
            
            if age_hours > self.max_backup_age_hours:
                health_report['alerts'].append(f'Latest backup is {age_hours:.1f} hours old (max: {self.max_backup_age_hours})')
        
        # Check backup count
        if health_report['backup_count'] < self.min_backup_count:
            health_report['alerts'].append(f'Only {health_report["backup_count"]} backups found (min: {self.min_backup_count})')
        
        # Check missing files
        if health_report['missing_files']:
            health_report['alerts'].append(f'{len(health_report["missing_files"])} backup files are missing')
        
        # Determine overall status
        if health_report['alerts']:
            if any('CRITICAL' in alert or 'No backups' in alert for alert in health_report['alerts']):
                health_report['status'] = 'CRITICAL'
            else:
                health_report['status'] = 'WARNING'
        else:
            health_report['status'] = 'HEALTHY'
        
        # Print report
        print(f"📊 Backup Count: {health_report['backup_count']}")
        if health_report['latest_backup_age_hours']:
            print(f"⏰ Latest Backup Age: {health_report['latest_backup_age_hours']:.1f} hours")
        print(f"🎯 Status: {health_report['status']}")
        
        if health_report['alerts']:
            print(f"⚠️  Alerts:")
            for alert in health_report['alerts']:
                print(f"   • {alert}")
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
        print(f"\n📄 Health report saved: {report_file}")
    except Exception as e:
        print(f"\n❌ Could not save health report: {str(e)}")
