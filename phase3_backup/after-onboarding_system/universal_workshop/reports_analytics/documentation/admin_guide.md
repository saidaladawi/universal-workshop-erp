# Administrator Guide - Reports & Analytics Engine

## Overview
This guide provides comprehensive instructions for system administrators to configure, manage, and maintain the Universal Workshop ERP Reports & Analytics Engine.

## System Configuration

### Initial Setup
1. **Enable Reports & Analytics Module**
   ```python
   # Enable in hooks.py
   app_include_js = [
       "/assets/universal_workshop/js/reports_analytics.js"
   ]
   
   # Install module
   bench --site universal.local install-app universal_workshop
   bench --site universal.local migrate
   ```

2. **Configure Regional Settings**
   - Navigate to **Setup → Regional Settings**
   - Set **Country**: Oman
   - Set **Currency**: Omani Rial (OMR)
   - Set **Time Zone**: Asia/Muscat
   - Set **Date Format**: DD/MM/YYYY
   - Set **Number Format**: 123,456.789

3. **Enable Arabic Language**
   ```python
   # System Settings configuration
   from frappe import _
   
   def setup_arabic_language():
       system_settings = frappe.get_doc("System Settings")
       system_settings.language = "ar"
       system_settings.save()
   ```

### Database Configuration

1. **Performance Indexes**
   ```sql
   -- Create indexes for Arabic search
   ALTER TABLE `tabCustomer` 
   ADD INDEX idx_customer_name_ar (customer_name_ar);
   
   ALTER TABLE `tabItem` 
   ADD INDEX idx_item_name_ar (item_name_ar);
   
   -- Full-text search for Arabic content
   ALTER TABLE `tabCustom Report Builder`
   ADD FULLTEXT INDEX ft_report_arabic (report_name_ar, description_ar);
   ```

2. **Database Cleanup Scheduler**
   ```python
   # Auto-cleanup old report files
   @frappe.whitelist()
   def cleanup_old_reports():
       """Clean up reports older than 30 days"""
       cutoff_date = frappe.utils.add_days(frappe.utils.today(), -30)
       
       old_files = frappe.get_list("File",
           filters={"creation": ["<", cutoff_date],
                   "file_url": ["like", "%reports%"]})
       
       for file_doc in old_files:
           frappe.delete_doc("File", file_doc.name)
   ```

## User Management and Permissions

### Role Configuration

1. **Create Report Roles**
   ```python
   # Reports & Analytics Roles
   roles = [
       {
           "role_name": "Reports Viewer",
           "permissions": ["read"],
           "description": "Can view reports and dashboards"
       },
       {
           "role_name": "Report Creator", 
           "permissions": ["read", "write", "create"],
           "description": "Can create and modify reports"
       },
       {
           "role_name": "Reports Administrator",
           "permissions": ["read", "write", "create", "delete", "export"],
           "description": "Full access to reports system"
       }
   ]
   ```

2. **Permission Matrix**
   | DocType | Reports Viewer | Report Creator | Reports Admin |
   |---------|----------------|----------------|---------------|
   | Custom Report Builder | Read | Read, Write, Create | All |
   | Interactive Dashboard | Read | Read, Write, Create | All |
   | Report Schedule | Read | Read, Write | All |
   | Report Export Utility | Read | Read, Write | All |

### User Onboarding

1. **New User Setup Checklist**
   - [ ] Create user account with appropriate roles
   - [ ] Set language preference (Arabic/English)
   - [ ] Configure regional settings
   - [ ] Assign to appropriate workshops
   - [ ] Set up email notifications
   - [ ] Provide training materials
   - [ ] Test report access

2. **Bulk User Import**
   ```python
   # Import users from Excel with Arabic names
   def import_workshop_users(file_path):
       data = frappe.utils.read_csv_content(file_path)
       
       for row in data:
           user = frappe.new_doc("User")
           user.email = row[0]
           user.first_name = row[1]
           user.first_name_ar = row[2]  # Arabic name
           user.last_name = row[3]
           user.last_name_ar = row[4]   # Arabic surname
           user.language = "ar"
           user.time_zone = "Asia/Muscat"
           user.insert()
   ```

## Arabic Localization Administration

### RTL Layout Configuration

1. **CSS Configuration**
   ```css
   /* Arabic RTL styles for reports */
   .report-container[dir="rtl"] {
       text-align: right;
       direction: rtl;
   }
   
   .report-container[dir="rtl"] .table th,
   .report-container[dir="rtl"] .table td {
       text-align: right;
   }
   
   .report-container[dir="rtl"] .form-control {
       text-align: right;
   }
   ```

2. **Font Management**
   ```python
   # Configure Arabic fonts
   def setup_arabic_fonts():
       css_config = """
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       .arabic-text {
           font-family: 'Noto Sans Arabic', 'Tahoma', sans-serif;
           font-size: 14px;
           line-height: 1.6;
       }
       """
       
       frappe.db.set_value("Website Settings", None, "custom_css", css_config)
   ```

### Translation Management

1. **Translation Workflow**
   ```python
   def update_arabic_translations():
       """Update Arabic translations for reports"""
       translations = [
           {"en": "Report", "ar": "تقرير"},
           {"en": "Dashboard", "ar": "لوحة المعلومات"},
           {"en": "Export", "ar": "تصدير"},
           {"en": "Schedule", "ar": "جدولة"},
           {"en": "Filter", "ar": "فلتر"},
           {"en": "Chart", "ar": "مخطط"}
       ]
       
       for trans in translations:
           if not frappe.db.exists("Translation", 
               {"language": "ar", "source_text": trans["en"]}):
               doc = frappe.new_doc("Translation")
               doc.language = "ar"
               doc.source_text = trans["en"]
               doc.translated_text = trans["ar"]
               doc.insert()
   ```

## Troubleshooting Guide

### Common Issues

1. **Arabic Text Not Displaying**
   ```python
   # Check character encoding
   def fix_arabic_encoding():
       # Verify database charset
       charset = frappe.db.sql("SHOW VARIABLES LIKE 'character_set_database'")[0][1]
       if charset != 'utf8mb4':
           frappe.throw("Database must use utf8mb4 charset for Arabic support")
       
       # Check browser settings
       return {
           "database_charset": charset,
           "recommended_fonts": ["Noto Sans Arabic", "Tahoma", "Arial Unicode MS"],
           "browser_requirements": "Must support RTL and Arabic fonts"
       }
   ```

2. **Performance Issues**
   ```python
   # Diagnose slow reports
   def diagnose_slow_reports():
       slow_reports = frappe.db.sql("""
           SELECT r.name, r.report_name, AVG(e.execution_time) as avg_time
           FROM `tabCustom Report Builder` r
           JOIN `tabReport Schedule Execution` e ON r.name = e.report_id
           WHERE e.creation >= %s
           GROUP BY r.name
           HAVING avg_time > 30
           ORDER BY avg_time DESC
       """, [frappe.utils.add_days(frappe.utils.today(), -7)])
       
       return slow_reports
   ```

### Maintenance Scripts

1. **Daily Maintenance**
   ```bash
   #!/bin/bash
   # Daily maintenance script
   
   # Clean up old files
   bench --site universal.local execute universal_workshop.reports_analytics.cleanup_old_files
   
   # Update report statistics
   bench --site universal.local execute universal_workshop.reports_analytics.update_statistics
   
   # Check system health
   bench --site universal.local execute universal_workshop.reports_analytics.health_check
   ```

2. **Weekly Maintenance**
   ```bash
   #!/bin/bash
   # Weekly maintenance script
   
   # Backup report configurations
   bench --site universal.local execute universal_workshop.reports_analytics.backup_configurations
   
   # Optimize database
   bench --site universal.local execute universal_workshop.reports_analytics.optimize_database
   
   # Generate usage reports
   bench --site universal.local execute universal_workshop.reports_analytics.generate_usage_report
   ```

---

## Support and Resources

### Administrator Resources
- **Admin Forum**: https://admin.universal-workshop.om
- **API Documentation**: Available in system
- **Training Videos**: Available in documentation portal
- **24/7 Support**: +968 24 123 456

### Emergency Contacts
- **System Administrator**: admin@universal-workshop.om
- **Database Administrator**: dba@universal-workshop.om  
- **Arabic Support Specialist**: arabic@universal-workshop.om

For additional technical assistance, refer to the troubleshooting guides or contact our support team. 