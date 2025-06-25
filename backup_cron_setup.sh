#!/bin/bash
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
