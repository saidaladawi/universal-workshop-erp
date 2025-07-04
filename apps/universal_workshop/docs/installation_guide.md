# Universal Workshop ERP - Installation Guide

## Overview

Universal Workshop ERP is an Arabic-first automotive workshop management system built on ERPNext v15.65.2. This guide provides comprehensive instructions for installing and configuring the system for production use in Oman and other Arabic-speaking markets.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Process](#installation-process)
3. [Post-Installation Configuration](#post-installation-configuration)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)
6. [Recovery Procedures](#recovery-procedures)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 50GB free space
- **Database**: MariaDB 10.6+ or MySQL 8.0+
- **Python**: Python 3.8+
- **Node.js**: Node.js 18+

### Software Dependencies

- ERPNext v15.65.2
- Frappe Framework v15
- Redis Server
- Nginx (for production)
- Supervisor (for production)

### Network Requirements

- Internet connection for initial setup
- SMTP server access for email notifications
- SMS gateway access (optional, for Twilio integration)

## Installation Process

### Step 1: Prepare ERPNext Environment

```bash
# Install Frappe Bench
sudo pip3 install frappe-bench

# Initialize bench with ERPNext v15
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# Get ERPNext app
bench get-app --branch version-15 erpnext

# Create new site
bench new-site universal.local
bench --site universal.local install-app erpnext
```

### Step 2: Get Universal Workshop App

```bash
# Clone Universal Workshop app
bench get-app https://github.com/your-repo/universal_workshop.git

# Install Universal Workshop on site
bench --site universal.local install-app universal_workshop
```

### Step 3: Automatic Installation Process

The Universal Workshop app includes comprehensive installation hooks that automatically configure the system:

#### What Happens During Installation

1. **Customer Management Setup**
   - Custom fields installation
   - Customer extensions configuration

2. **Vehicle Management Setup**
   - Vehicle DocType initialization
   - VIN decoder setup
   - Vehicle specifications database

3. **Workshop Management Setup**
   - Workshop Profile configuration
   - Service Order workflows
   - Technician management

4. **Parts Inventory Setup**
   - Item custom fields installation
   - Default warehouse setup
   - Inventory management configuration

5. **Billing Management Setup**
   - VAT custom fields (Oman compliance)
   - Invoice custom fields
   - QR code generation setup
   - Bilingual print formats
   - Oman VAT configuration (5% rate)

6. **Communication Management Setup**
   - SMS/Email notification system
   - Twilio integration setup
   - Communication templates

7. **Arabic Localization Setup**
   - Arabic language creation and activation
   - System language set to Arabic
   - Oman country and timezone configuration
   - OMR currency setup
   - Default workshop roles with Arabic names

8. **Default Workshop Data Creation**
   - 8 service types with Arabic translations
   - 4 labor rate categories
   - Oman-specific system preferences
   - Sample customer and vehicle data

### Step 4: Verify Installation

```bash
# Check installation status
bench --site universal.local list-apps

# Verify Universal Workshop is installed
bench --site universal.local console
```

In the console, run:
```python
import frappe
frappe.get_installed_apps()
# Should include 'universal_workshop'

# Check Arabic language setup
frappe.db.exists("Language", "ar")
# Should return True

# Check system settings
system_settings = frappe.get_doc("System Settings")
print(f"Language: {system_settings.language}")
print(f"Country: {system_settings.country}")
print(f"Currency: {system_settings.currency}")
```

## Post-Installation Configuration

### Step 1: Initial System Setup

1. **Access the system**: Navigate to `http://your-domain:8000`
2. **Login**: Use Administrator credentials
3. **Language**: System should default to Arabic
4. **Complete setup wizard** if prompted

### Step 2: Workshop Profile Configuration

1. Navigate to **Workshop Profile**
2. Create your workshop profile with:
   - Workshop name (Arabic and English)
   - Address and contact information
   - License numbers and certifications
   - Operating hours
   - Service specializations

### Step 3: User Management

1. **Create workshop users** with appropriate roles:
   - **Workshop Owner** (مالك الورشة): Full system access
   - **Workshop Manager** (مدير الورشة): Management functions
   - **Service Advisor** (مستشار الخدمة): Customer interaction
   - **Workshop Technician** (فني الورشة): Service execution

2. **Assign permissions** based on roles
3. **Configure user preferences** (language, timezone)

### Step 4: Service Configuration

1. **Review default service types**:
   - Engine Service (خدمة المحرك)
   - Transmission Service (خدمة ناقل الحركة)
   - Brake Service (خدمة الفرامل)
   - Tire Service (خدمة الإطارات)
   - Oil Change (تغيير الزيت)
   - Air Conditioning (تكييف الهواء)
   - Electrical System (النظام الكهربائي)
   - General Inspection (فحص عام)

2. **Customize service rates** as needed
3. **Add additional services** specific to your workshop

### Step 5: Inventory Setup

1. **Configure warehouses** for parts storage
2. **Import parts catalog** or add items manually
3. **Set up suppliers** and purchasing workflows
4. **Configure reorder levels** and stock alerts

### Step 6: Financial Configuration

1. **Verify VAT settings** (5% for Oman)
2. **Configure payment methods**
3. **Set up bank accounts**
4. **Configure invoice numbering**

## Troubleshooting

### Common Installation Issues

#### Issue: Installation Hook Fails

**Symptoms**: Error during app installation
**Solution**:
```bash
# Check error logs
bench --site universal.local logs

# Manually run installation
bench --site universal.local console
```

In console:
```python
from universal_workshop.install import after_install
after_install()
```

#### Issue: Arabic Language Not Set

**Symptoms**: System still in English after installation
**Solution**:
```bash
bench --site universal.local console
```

In console:
```python
from universal_workshop.install import setup_arabic_localization
setup_arabic_localization()
```

#### Issue: Default Data Missing

**Symptoms**: No service types or roles created
**Solution**:
```bash
bench --site universal.local console
```

In console:
```python
from universal_workshop.install import setup_default_workshop_data
setup_default_workshop_data()
```

#### Issue: Permission Errors

**Symptoms**: Users cannot access workshop features
**Solution**:
1. Check role assignments in User master
2. Verify DocType permissions
3. Re-run role setup if needed:

```python
from universal_workshop.install import setup_default_workshop_roles
setup_default_workshop_roles()
```

### Database Issues

#### Issue: Database Connection Errors

**Solution**:
```bash
# Check database status
sudo systemctl status mariadb

# Restart database if needed
sudo systemctl restart mariadb

# Check site database
bench --site universal.local mariadb
```

#### Issue: Migration Errors

**Solution**:
```bash
# Run migrations manually
bench --site universal.local migrate

# Check for pending patches
bench --site universal.local console
```

In console:
```python
import frappe
frappe.db.sql("SELECT * FROM `tabPatch Log` ORDER BY creation DESC LIMIT 10")
```

### Performance Issues

#### Issue: Slow System Response

**Solutions**:
1. **Check system resources**:
   ```bash
   htop
   df -h
   ```

2. **Optimize database**:
   ```bash
   bench --site universal.local console
   ```
   
   In console:
   ```python
   frappe.db.sql("OPTIMIZE TABLE `tabCustomer`")
   frappe.db.sql("OPTIMIZE TABLE `tabVehicle`")
   frappe.db.sql("OPTIMIZE TABLE `tabService Order`")
   ```

3. **Clear cache**:
   ```bash
   bench --site universal.local clear-cache
   bench --site universal.local clear-website-cache
   ```

## Maintenance

### Daily Maintenance

1. **Monitor system logs**:
   ```bash
   bench --site universal.local logs
   ```

2. **Check disk space**:
   ```bash
   df -h
   ```

3. **Verify backup completion**:
   ```bash
   ls -la sites/universal.local/private/backups/
   ```

### Weekly Maintenance

1. **Database optimization**:
   ```bash
   bench --site universal.local console
   ```
   
   In console:
   ```python
   # Optimize frequently used tables
   tables = ['tabCustomer', 'tabVehicle', 'tabService Order', 'tabSales Invoice']
   for table in tables:
       frappe.db.sql(f"OPTIMIZE TABLE `{table}`")
   ```

2. **Clear old logs**:
   ```bash
   bench --site universal.local clear-cache
   ```

3. **Update system**:
   ```bash
   bench update --no-backup
   ```

### Monthly Maintenance

1. **Full system backup**:
   ```bash
   bench --site universal.local backup --with-files
   ```

2. **Security audit**:
   - Review user access logs
   - Check for unusual activity
   - Update passwords if needed

3. **Performance review**:
   - Analyze system performance metrics
   - Review and optimize slow queries
   - Clean up old data if needed

## Recovery Procedures

### Backup and Restore

#### Creating Backups

```bash
# Database only
bench --site universal.local backup

# Database with files
bench --site universal.local backup --with-files

# Automated daily backups
crontab -e
# Add: 0 2 * * * /path/to/bench --site universal.local backup --with-files
```

#### Restoring from Backup

```bash
# List available backups
ls sites/universal.local/private/backups/

# Restore database
bench --site universal.local restore /path/to/backup.sql.gz

# Restore files (if backed up with files)
bench --site universal.local restore /path/to/backup.tar --with-files
```

### Disaster Recovery

#### Complete System Failure

1. **Reinstall ERPNext environment**
2. **Restore from latest backup**
3. **Reinstall Universal Workshop app**
4. **Verify system functionality**

#### Data Corruption

1. **Stop all services**:
   ```bash
   bench --site universal.local stop
   ```

2. **Restore from backup**:
   ```bash
   bench --site universal.local restore /path/to/latest/backup.sql.gz
   ```

3. **Restart services**:
   ```bash
   bench --site universal.local start
   ```

4. **Verify data integrity**

### Emergency Contacts

- **Technical Support**: [Your support contact]
- **Database Administrator**: [DBA contact]
- **System Administrator**: [SysAdmin contact]

## Security Considerations

### Access Control

1. **Use strong passwords** for all accounts
2. **Enable two-factor authentication** for administrators
3. **Regular password rotation** policy
4. **Role-based access control** implementation

### Network Security

1. **Use HTTPS** in production
2. **Configure firewall** to restrict access
3. **Regular security updates**
4. **Monitor access logs**

### Data Protection

1. **Regular encrypted backups**
2. **Secure backup storage**
3. **Data retention policies**
4. **Compliance with local regulations**

## Support and Resources

### Documentation

- [ERPNext Documentation](https://docs.erpnext.com/)
- [Frappe Framework Documentation](https://frappeframework.com/docs)
- Universal Workshop User Guide (see `user_guide.md`)

### Community Support

- ERPNext Community Forum
- Frappe Discord Channel
- Universal Workshop GitHub Issues

### Professional Support

Contact your Universal Workshop implementation partner for:
- Custom development
- Advanced configuration
- Training and support
- System optimization

---

**Document Version**: 1.0  
**Last Updated**: 2025-06-25  
**Compatibility**: Universal Workshop ERP v1.0 / ERPNext v15.65.2 