import frappe
from frappe import _

class DataIntegrityChecker:
    """Comprehensive data integrity checker for Universal Workshop ERP"""
    
    def __init__(self):
        self.results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings': 0,
            'critical_issues': 0,
            'checks': []
        }
    
    def run_all_integrity_checks(self):
        """Run all data integrity checks"""
        
        print("\n" + "="*90)
        print("UNIVERSAL WORKSHOP ERP - COMPREHENSIVE DATA INTEGRITY CHECKS")
        print("="*90)
        
        try:
            # Core table integrity checks
            self.check_workshop_profile_integrity()
            self.check_customer_data_integrity()
            self.check_technician_data_integrity()
            self.check_workshop_role_integrity()
            self.check_workshop_theme_integrity()
            
            # System integrity checks
            self.check_doctype_consistency()
            self.check_user_permissions_integrity()
            self.check_database_constraints()
            
            # Arabic localization integrity
            self.check_arabic_data_integrity()
            
            # License system integrity
            self.check_license_system_integrity()
            
            # Generate comprehensive report
            self.generate_integrity_report()
            
            return self.results
            
        except Exception as e:
            self.add_critical_issue("System Error", f"Critical error during integrity checks: {str(e)}")
            raise
    
    def check_workshop_profile_integrity(self):
        """Check Workshop Profile data integrity"""
        
        print(f"\n🏭 WORKSHOP PROFILE INTEGRITY")
        print("-" * 50)
        
        self.add_check("Workshop Profile Table Structure")
        
        try:
            # Check table exists
            if not self.table_exists('tabWorkshop Profile'):
                self.fail_check("Workshop Profile table does not exist")
                return
            
            # Get record count
            count = self.get_record_count('tabWorkshop Profile')
            print(f"📊 Records: {count}")
            
            if count == 0:
                self.pass_check("No data to validate (empty table)")
                return
            
            # Check for required fields
            self.add_check("Workshop Profile Required Fields")
            required_fields = ['workshop_code', 'workshop_name', 'status']
            missing_fields = []
            
            for field in required_fields:
                if not self.column_exists('tabWorkshop Profile', field):
                    missing_fields.append(field)
            
            if missing_fields:
                self.fail_check(f"Missing required fields: {', '.join(missing_fields)}")
            else:
                self.pass_check("All required fields present")
            
            # Check for duplicate workshop codes
            self.add_check("Workshop Code Uniqueness")
            duplicates = frappe.db.sql("""
                SELECT workshop_code, COUNT(*) as count
                FROM `tabWorkshop Profile`
                WHERE workshop_code IS NOT NULL AND workshop_code != ''
                GROUP BY workshop_code
                HAVING COUNT(*) > 1
            """, as_dict=True)
            
            if duplicates:
                self.fail_check(f"Found {len(duplicates)} duplicate workshop codes")
                for dup in duplicates[:3]:
                    print(f"   ⚠️  Duplicate: {dup['workshop_code']} ({dup['count']} times)")
            else:
                self.pass_check("All workshop codes are unique")
            
            # Check for NULL values in critical fields
            self.add_check("Workshop Profile NULL Values")
            null_checks = [
                ('workshop_name', 'Workshop Name'),
                ('status', 'Status')
            ]
            
            null_issues = []
            for field, label in null_checks:
                null_count = frappe.db.sql(f"""
                    SELECT COUNT(*) FROM `tabWorkshop Profile`
                    WHERE `{field}` IS NULL OR `{field}` = ''
                """)[0][0]
                
                if null_count > 0:
                    null_issues.append(f"{label}: {null_count} records")
            
            if null_issues:
                self.add_warning("NULL values found", null_issues)
            else:
                self.pass_check("No NULL values in critical fields")
                
        except Exception as e:
            self.fail_check(f"Error checking Workshop Profile: {str(e)}")
    
    def check_customer_data_integrity(self):
        """Check Customer data integrity"""
        
        print(f"\n👥 CUSTOMER DATA INTEGRITY")
        print("-" * 50)
        
        self.add_check("Customer Table Structure")
        
        try:
            if not self.table_exists('tabCustomer'):
                self.fail_check("Customer table does not exist")
                return
            
            count = self.get_record_count('tabCustomer')
            print(f"📊 Records: {count}")
            
            if count == 0:
                self.pass_check("No customer data to validate")
                return
            
            # Check for duplicate customer names
            self.add_check("Customer Name Uniqueness")
            duplicates = frappe.db.sql("""
                SELECT customer_name, COUNT(*) as count
                FROM `tabCustomer`
                WHERE customer_name IS NOT NULL AND customer_name != ''
                GROUP BY customer_name
                HAVING COUNT(*) > 1
            """, as_dict=True)
            
            if duplicates:
                self.add_warning(f"Found {len(duplicates)} duplicate customer names")
                for dup in duplicates[:3]:
                    print(f"   ⚠️  Duplicate: {dup['customer_name']} ({dup['count']} times)")
            else:
                self.pass_check("All customer names are unique")
            
            # Check customer status consistency
            self.add_check("Customer Status Consistency")
            invalid_status = frappe.db.sql("""
                SELECT COUNT(*) FROM `tabCustomer`
                WHERE disabled NOT IN (0, 1)
            """)[0][0]
            
            if invalid_status > 0:
                self.fail_check(f"Found {invalid_status} customers with invalid status")
            else:
                self.pass_check("All customer statuses are valid")
                
        except Exception as e:
            self.fail_check(f"Error checking Customer data: {str(e)}")
    
    def check_technician_data_integrity(self):
        """Check Technician data integrity"""
        
        print(f"\n🔧 TECHNICIAN DATA INTEGRITY")
        print("-" * 50)
        
        self.add_check("Technician Table Structure")
        
        try:
            if not self.table_exists('tabTechnician'):
                self.add_warning("Technician table does not exist (will be created when needed)")
                return
            
            count = self.get_record_count('tabTechnician')
            print(f"📊 Records: {count}")
            
            if count == 0:
                self.pass_check("No technician data to validate")
                return
            
            # Check for required technician fields
            self.add_check("Technician Required Fields")
            if self.column_exists('tabTechnician', 'technician_name'):
                null_names = frappe.db.sql("""
                    SELECT COUNT(*) FROM `tabTechnician`
                    WHERE technician_name IS NULL OR technician_name = ''
                """)[0][0]
                
                if null_names > 0:
                    self.fail_check(f"Found {null_names} technicians without names")
                else:
                    self.pass_check("All technicians have names")
            else:
                self.add_warning("Technician name field not found")
                
        except Exception as e:
            self.fail_check(f"Error checking Technician data: {str(e)}")
    
    def check_workshop_role_integrity(self):
        """Check Workshop Role data integrity"""
        
        print(f"\n👤 WORKSHOP ROLE INTEGRITY")
        print("-" * 50)
        
        self.add_check("Workshop Role Data")
        
        try:
            if not self.table_exists('tabWorkshop Role'):
                self.fail_check("Workshop Role table does not exist")
                return
            
            count = self.get_record_count('tabWorkshop Role')
            print(f"📊 Records: {count}")
            
            if count == 0:
                self.add_warning("No workshop roles defined")
                return
            
            # Check role data integrity
            roles = frappe.db.sql("""
                SELECT name, role_name FROM `tabWorkshop Role`
                WHERE role_name IS NOT NULL AND role_name != ''
            """, as_dict=True)
            
            print(f"✅ Found {len(roles)} valid workshop roles:")
            for role in roles[:5]:
                print(f"   👤 {role['role_name']}")
            
            self.pass_check(f"Workshop roles are properly configured ({len(roles)} roles)")
            
            # Check for duplicate role names
            self.add_check("Workshop Role Uniqueness")
            duplicates = frappe.db.sql("""
                SELECT role_name, COUNT(*) as count
                FROM `tabWorkshop Role`
                WHERE role_name IS NOT NULL AND role_name != ''
                GROUP BY role_name
                HAVING COUNT(*) > 1
            """, as_dict=True)
            
            if duplicates:
                self.fail_check(f"Found {len(duplicates)} duplicate role names")
            else:
                self.pass_check("All workshop role names are unique")
                
        except Exception as e:
            self.fail_check(f"Error checking Workshop Role: {str(e)}")
    
    def check_workshop_theme_integrity(self):
        """Check Workshop Theme data integrity"""
        
        print(f"\n🎨 WORKSHOP THEME INTEGRITY")
        print("-" * 50)
        
        self.add_check("Workshop Theme Data")
        
        try:
            if not self.table_exists('tabWorkshop Theme'):
                self.fail_check("Workshop Theme table does not exist")
                return
            
            count = self.get_record_count('tabWorkshop Theme')
            print(f"📊 Records: {count}")
            
            if count == 0:
                self.add_warning("No workshop themes defined")
                return
            
            # Check theme data
            themes = frappe.db.sql("""
                SELECT name, theme_name FROM `tabWorkshop Theme`
                WHERE theme_name IS NOT NULL AND theme_name != ''
            """, as_dict=True)
            
            print(f"✅ Found {len(themes)} valid themes:")
            for theme in themes:
                print(f"   🎨 {theme['theme_name']}")
            
            self.pass_check(f"Workshop themes are properly configured ({len(themes)} themes)")
            
        except Exception as e:
            self.fail_check(f"Error checking Workshop Theme: {str(e)}")
    
    def check_doctype_consistency(self):
        """Check DocType consistency"""
        
        print(f"\n📋 DOCTYPE CONSISTENCY")
        print("-" * 50)
        
        self.add_check("DocType Registration")
        
        try:
            # Check if all Universal Workshop DocTypes are registered
            workshop_doctypes = [
                'Workshop Profile',
                'Technician',
                'Workshop Role',
                'Workshop Theme',
                'Business Workshop Binding'
            ]
            
            missing_doctypes = []
            existing_doctypes = []
            
            for doctype in workshop_doctypes:
                if frappe.db.exists('DocType', doctype):
                    existing_doctypes.append(doctype)
                else:
                    missing_doctypes.append(doctype)
            
            print(f"✅ Registered DocTypes: {len(existing_doctypes)}")
            for dt in existing_doctypes:
                print(f"   📋 {dt}")
            
            if missing_doctypes:
                self.add_warning(f"Missing DocTypes: {', '.join(missing_doctypes)}")
            else:
                self.pass_check("All DocTypes are properly registered")
                
        except Exception as e:
            self.fail_check(f"Error checking DocType consistency: {str(e)}")
    
    def check_user_permissions_integrity(self):
        """Check user permissions integrity"""
        
        print(f"\n🔐 USER PERMISSIONS INTEGRITY")
        print("-" * 50)
        
        self.add_check("Permission System")
        
        try:
            # Check if Workshop Permission Profile exists
            if self.table_exists('tabWorkshop Permission Profile'):
                profile_count = self.get_record_count('tabWorkshop Permission Profile')
                print(f"📊 Permission Profiles: {profile_count}")
                
                if profile_count > 0:
                    self.pass_check("Workshop permission profiles are configured")
                else:
                    self.add_warning("No workshop permission profiles found")
            else:
                self.add_warning("Workshop Permission Profile table not found")
            
            # Check Workshop Role Permissions
            if self.table_exists('tabWorkshop Role Permission'):
                role_perm_count = self.get_record_count('tabWorkshop Role Permission')
                print(f"📊 Role Permissions: {role_perm_count}")
                
                if role_perm_count > 0:
                    self.pass_check("Workshop role permissions are configured")
                else:
                    self.add_warning("No workshop role permissions found")
            else:
                self.add_warning("Workshop Role Permission table not found")
                
        except Exception as e:
            self.fail_check(f"Error checking user permissions: {str(e)}")
    
    def check_database_constraints(self):
        """Check database constraints and indexes"""
        
        print(f"\n🗄️  DATABASE CONSTRAINTS")
        print("-" * 50)
        
        self.add_check("Database Constraints")
        
        try:
            # Check for proper indexes on Workshop Profile
            if self.table_exists('tabWorkshop Profile'):
                indexes = frappe.db.sql("""
                    SHOW INDEX FROM `tabWorkshop Profile`
                    WHERE Key_name != 'PRIMARY'
                """, as_dict=True)
                
                index_count = len(indexes)
                print(f"📊 Workshop Profile Indexes: {index_count}")
                
                # Check for unique constraints
                unique_indexes = [idx for idx in indexes if idx['Non_unique'] == 0]
                print(f"📊 Unique Constraints: {len(unique_indexes)}")
                
                if len(unique_indexes) >= 2:  # workshop_code and business_license should be unique
                    self.pass_check("Proper unique constraints are in place")
                else:
                    self.add_warning("Some unique constraints may be missing")
            
            # Check table engine
            self.add_check("Table Engine Consistency")
            tables = frappe.db.sql("""
                SELECT TABLE_NAME, ENGINE
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME LIKE 'tabWorkshop%'
            """, as_dict=True)
            
            engines = set(table['ENGINE'] for table in tables)
            print(f"📊 Table Engines: {', '.join(engines)}")
            
            if len(engines) == 1 and 'InnoDB' in engines:
                self.pass_check("All tables use InnoDB engine")
            else:
                self.add_warning(f"Mixed table engines found: {', '.join(engines)}")
                
        except Exception as e:
            self.fail_check(f"Error checking database constraints: {str(e)}")
    
    def check_arabic_data_integrity(self):
        """Check Arabic localization data integrity"""
        
        print(f"\n🌐 ARABIC LOCALIZATION INTEGRITY")
        print("-" * 50)
        
        self.add_check("Arabic Data Encoding")
        
        try:
            # Check database charset
            charset_info = frappe.db.sql("""
                SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME = DATABASE()
            """, as_dict=True)
            
            if charset_info:
                charset = charset_info[0]['DEFAULT_CHARACTER_SET_NAME']
                collation = charset_info[0]['DEFAULT_COLLATION_NAME']
                
                print(f"📊 Database Charset: {charset}")
                print(f"📊 Database Collation: {collation}")
                
                if charset == 'utf8mb4':
                    self.pass_check("Database uses UTF8MB4 charset (supports Arabic)")
                else:
                    self.fail_check(f"Database charset is {charset}, should be utf8mb4 for Arabic support")
            
            # Check for Arabic field columns in Workshop Profile
            if self.table_exists('tabWorkshop Profile'):
                arabic_fields = frappe.db.sql("""
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'tabWorkshop Profile'
                    AND COLUMN_NAME LIKE '%_ar'
                """, as_list=True)
                
                arabic_field_count = len(arabic_fields)
                print(f"📊 Arabic Fields: {arabic_field_count}")
                
                if arabic_field_count > 0:
                    self.pass_check(f"Found {arabic_field_count} Arabic fields in Workshop Profile")
                    for field in arabic_fields[:3]:
                        print(f"   🌐 {field[0]}")
                else:
                    self.add_warning("No Arabic fields found in Workshop Profile")
                    
        except Exception as e:
            self.fail_check(f"Error checking Arabic data integrity: {str(e)}")
    
    def check_license_system_integrity(self):
        """Check license system integrity"""
        
        print(f"\n🔑 LICENSE SYSTEM INTEGRITY")
        print("-" * 50)
        
        self.add_check("License System Tables")
        
        try:
            # Check Business Workshop Binding
            if self.table_exists('tabBusiness Workshop Binding'):
                binding_count = self.get_record_count('tabBusiness Workshop Binding')
                print(f"📊 Business Bindings: {binding_count}")
                
                if binding_count > 0:
                    self.pass_check("License binding system has data")
                else:
                    self.add_warning("No business workshop bindings found")
            else:
                self.fail_check("Business Workshop Binding table not found")
            
            # Check for license-related fields in Workshop Profile
            if self.table_exists('tabWorkshop Profile'):
                license_fields = ['business_license', 'license_expiry_date']
                missing_license_fields = []
                
                for field in license_fields:
                    if not self.column_exists('tabWorkshop Profile', field):
                        missing_license_fields.append(field)
                
                if missing_license_fields:
                    self.fail_check(f"Missing license fields: {', '.join(missing_license_fields)}")
                else:
                    self.pass_check("All license-related fields are present")
                    
        except Exception as e:
            self.fail_check(f"Error checking license system: {str(e)}")
    
    # Helper methods
    def table_exists(self, table_name):
        """Check if table exists"""
        tables = frappe.db.sql(f"SHOW TABLES LIKE '{table_name}'", as_list=True)
        return len(tables) > 0
    
    def column_exists(self, table_name, column_name):
        """Check if column exists in table"""
        try:
            columns = frappe.db.sql(f"DESCRIBE `{table_name}`", as_dict=True)
            column_names = [col['Field'] for col in columns]
            return column_name in column_names
        except:
            return False
    
    def get_record_count(self, table_name):
        """Get record count for table"""
        try:
            result = frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`", as_list=True)
            return result[0][0] if result else 0
        except:
            return 0
    
    def add_check(self, check_name):
        """Add a new check"""
        self.results['total_checks'] += 1
        self.current_check = check_name
    
    def pass_check(self, message):
        """Mark current check as passed"""
        self.results['passed_checks'] += 1
        self.results['checks'].append({
            'check': self.current_check,
            'status': 'PASSED',
            'message': message
        })
        print(f"✅ {message}")
    
    def fail_check(self, message):
        """Mark current check as failed"""
        self.results['failed_checks'] += 1
        self.results['checks'].append({
            'check': self.current_check,
            'status': 'FAILED',
            'message': message
        })
        print(f"❌ {message}")
    
    def add_warning(self, message, details=None):
        """Add a warning"""
        self.results['warnings'] += 1
        warning_data = {
            'check': self.current_check,
            'status': 'WARNING',
            'message': message
        }
        if details:
            warning_data['details'] = details
        
        self.results['checks'].append(warning_data)
        print(f"⚠️  {message}")
        
        if details:
            for detail in details[:3]:
                print(f"     • {detail}")
    
    def add_critical_issue(self, issue_type, message):
        """Add a critical issue"""
        self.results['critical_issues'] += 1
        self.results['checks'].append({
            'check': issue_type,
            'status': 'CRITICAL',
            'message': message
        })
        print(f"🚨 CRITICAL: {message}")
    
    def generate_integrity_report(self):
        """Generate comprehensive integrity report"""
        
        print(f"\n" + "="*90)
        print("DATA INTEGRITY VALIDATION SUMMARY")
        print("="*90)
        
        total = self.results['total_checks']
        passed = self.results['passed_checks']
        failed = self.results['failed_checks']
        warnings = self.results['warnings']
        critical = self.results['critical_issues']
        
        print(f"📊 Total Checks: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"🚨 Critical Issues: {critical}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Overall health assessment
        if critical > 0:
            print(f"\n🚨 SYSTEM STATUS: CRITICAL ISSUES FOUND")
            print("Immediate attention required before production use.")
        elif failed > 3:
            print(f"\n❌ SYSTEM STATUS: MULTIPLE FAILURES")
            print("Several issues need to be addressed.")
        elif failed > 0:
            print(f"\n⚠️  SYSTEM STATUS: MINOR ISSUES")
            print("Some issues found but system is generally functional.")
        elif warnings > 0:
            print(f"\n✅ SYSTEM STATUS: HEALTHY WITH WARNINGS")
            print("System is functional with minor warnings.")
        else:
            print(f"\n🎉 SYSTEM STATUS: EXCELLENT")
            print("All data integrity checks passed successfully!")
        
        print("="*90 + "\n")

def run_data_integrity_checks():
    """Main function to run data integrity checks"""
    checker = DataIntegrityChecker()
    return checker.run_all_integrity_checks()

if __name__ == "__main__":
    run_data_integrity_checks()
