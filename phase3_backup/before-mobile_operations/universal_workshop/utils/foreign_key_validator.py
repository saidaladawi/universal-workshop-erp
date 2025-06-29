import frappe
from frappe import _

class ForeignKeyValidator:
    """Utility class for validating foreign key relationships in Universal Workshop ERP"""
    
    def __init__(self):
        self.validation_results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'errors': [],
            'warnings': []
        }
    
    def validate_all_relationships(self):
        """Validate all foreign key relationships"""
        
        frappe.log_error("Starting comprehensive foreign key validation", "Foreign Key Validation")
        
        try:
            # Define existing Link field relationships
            link_validations = [
                # Service Order validations
                {
                    'source_doctype': 'Service Order',
                    'source_field': 'customer',
                    'target_doctype': 'Customer',
                    'description': 'Service Order -> Customer'
                },
                {
                    'source_doctype': 'Service Order',
                    'source_field': 'vehicle',
                    'target_doctype': 'Vehicle',
                    'description': 'Service Order -> Vehicle'
                },
                {
                    'source_doctype': 'Service Order',
                    'source_field': 'technician_assigned',
                    'target_doctype': 'Technician',
                    'description': 'Service Order -> Technician'
                },
                
                # Vehicle validations
                {
                    'source_doctype': 'Vehicle',
                    'source_field': 'customer',
                    'target_doctype': 'Customer',
                    'description': 'Vehicle -> Customer'
                }
            ]
            
            # Validate each relationship
            for validation in link_validations:
                self.validate_link_field(
                    validation['source_doctype'],
                    validation['source_field'],
                    validation['target_doctype'],
                    validation['description']
                )
            
            # Additional consistency checks
            self.check_vehicle_customer_consistency()
            self.check_service_order_consistency()
            
            # Generate summary
            self.generate_summary()
            
            return self.validation_results
            
        except Exception as e:
            frappe.log_error(f"Critical error in foreign key validation: {str(e)}", "Foreign Key Validation Error")
            raise
    
    def validate_link_field(self, source_doctype, source_field, target_doctype, description):
        """Validate a specific Link field relationship"""
        
        self.validation_results['total_checks'] += 1
        
        try:
            # Check if DocTypes exist
            if not frappe.db.exists('DocType', source_doctype):
                self.add_error(description, f"Source DocType '{source_doctype}' does not exist")
                return
            
            if not frappe.db.exists('DocType', target_doctype):
                self.add_error(description, f"Target DocType '{target_doctype}' does not exist")
                return
            
            # Check if source table exists
            if not frappe.db.has_table(f"tab{source_doctype}"):
                self.add_error(description, f"Source table 'tab{source_doctype}' does not exist")
                return
            
            # Check if target table exists
            if not frappe.db.has_table(f"tab{target_doctype}"):
                self.add_error(description, f"Target table 'tab{target_doctype}' does not exist")
                return
            
            # Check if source field exists
            if not frappe.db.has_column(f"tab{source_doctype}", source_field):
                self.add_warning(description, f"Source field '{source_field}' does not exist in '{source_doctype}'")
                return
            
            # Get records with non-null link field values
            source_records = frappe.db.sql(f"""
                SELECT name, `{source_field}`
                FROM `tab{source_doctype}`
                WHERE `{source_field}` IS NOT NULL 
                AND `{source_field}` != ''
                LIMIT 1000
            """, as_dict=True)
            
            if not source_records:
                self.validation_results['passed_checks'] += 1
                frappe.log_error(f"✅ {description}: No records to validate", "Foreign Key Validation")
                return
            
            invalid_count = 0
            invalid_records = []
            
            # Check each link field value
            for record in source_records:
                link_value = record[source_field]
                if not frappe.db.exists(target_doctype, link_value):
                    invalid_count += 1
                    if len(invalid_records) < 10:  # Limit examples
                        invalid_records.append({
                            'source_record': record['name'],
                            'invalid_link': link_value
                        })
            
            if invalid_count > 0:
                self.add_error(description, f"Found {invalid_count} invalid link references", invalid_records)
            else:
                self.validation_results['passed_checks'] += 1
                frappe.log_error(f"✅ {description}: All {len(source_records)} references are valid", "Foreign Key Validation")
                
        except Exception as e:
            self.add_error(description, f"Error during validation: {str(e)}")
    
    def check_vehicle_customer_consistency(self):
        """Check vehicle-customer relationship consistency"""
        
        self.validation_results['total_checks'] += 1
        
        try:
            # Check if vehicles in service orders match customer vehicle ownership
            inconsistent_records = frappe.db.sql("""
                SELECT 
                    so.name as service_order,
                    so.customer as service_customer,
                    so.vehicle as service_vehicle,
                    v.customer as vehicle_customer
                FROM `tabService Order` so
                JOIN `tabVehicle` v ON so.vehicle = v.name
                WHERE so.customer != v.customer
                AND so.customer IS NOT NULL
                AND so.vehicle IS NOT NULL
                LIMIT 100
            """, as_dict=True)
            
            if inconsistent_records:
                self.add_error(
                    "Vehicle-Customer Consistency",
                    f"Found {len(inconsistent_records)} service orders with mismatched vehicle-customer relationships",
                    inconsistent_records[:10]
                )
            else:
                self.validation_results['passed_checks'] += 1
                frappe.log_error("✅ Vehicle-Customer Consistency: All relationships are consistent", "Foreign Key Validation")
                
        except Exception as e:
            self.add_error("Vehicle-Customer Consistency", f"Error checking consistency: {str(e)}")
    
    def check_service_order_consistency(self):
        """Check service order data consistency"""
        
        self.validation_results['total_checks'] += 1
        
        try:
            # Check for service orders with missing required references
            orphaned_orders = frappe.db.sql("""
                SELECT 
                    so.name,
                    so.customer,
                    so.vehicle,
                    CASE 
                        WHEN c.name IS NULL THEN 'Missing Customer'
                        WHEN v.name IS NULL THEN 'Missing Vehicle'
                        ELSE 'Unknown Issue'
                    END as issue
                FROM `tabService Order` so
                LEFT JOIN `tabCustomer` c ON so.customer = c.name
                LEFT JOIN `tabVehicle` v ON so.vehicle = v.name
                WHERE (so.customer IS NOT NULL AND c.name IS NULL)
                OR (so.vehicle IS NOT NULL AND v.name IS NULL)
                LIMIT 100
            """, as_dict=True)
            
            if orphaned_orders:
                self.add_error(
                    "Service Order Consistency",
                    f"Found {len(orphaned_orders)} service orders with missing references",
                    orphaned_orders[:10]
                )
            else:
                self.validation_results['passed_checks'] += 1
                frappe.log_error("✅ Service Order Consistency: All references are valid", "Foreign Key Validation")
                
        except Exception as e:
            self.add_error("Service Order Consistency", f"Error checking consistency: {str(e)}")
    
    def add_error(self, validation, message, invalid_records=None):
        """Add an error to the validation results"""
        self.validation_results['failed_checks'] += 1
        error_data = {
            'validation': validation,
            'error': message
        }
        if invalid_records:
            error_data['invalid_records'] = invalid_records
        
        self.validation_results['errors'].append(error_data)
        frappe.log_error(f"❌ {validation}: {message}", "Foreign Key Validation")
    
    def add_warning(self, validation, message):
        """Add a warning to the validation results"""
        self.validation_results['warnings'].append({
            'validation': validation,
            'warning': message
        })
        frappe.log_error(f"⚠️ {validation}: {message}", "Foreign Key Validation")
    
    def generate_summary(self):
        """Generate validation summary"""
        
        total = self.validation_results['total_checks']
        passed = self.validation_results['passed_checks']
        failed = self.validation_results['failed_checks']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        summary = f"""
Foreign Key Validation Summary:
- Total Checks: {total}
- Passed: {passed}
- Failed: {failed}
- Success Rate: {success_rate:.1f}%
- Warnings: {len(self.validation_results['warnings'])}
        """
        
        frappe.log_error(summary, "Foreign Key Validation Summary")
        
        if failed > 0:
            frappe.log_error("⚠️ Foreign Key Validation completed with errors", "Foreign Key Validation")
        else:
            frappe.log_error("✅ All Foreign Key Validations passed successfully!", "Foreign Key Validation")

@frappe.whitelist()
def validate_foreign_keys():
    """API method to validate foreign keys"""
    validator = ForeignKeyValidator()
    results = validator.validate_all_relationships()
    return {
        'summary': validator.validation_results,
        'timestamp': frappe.utils.now(),
        'status': 'PASSED' if validator.validation_results['failed_checks'] == 0 else 'FAILED'
    }
