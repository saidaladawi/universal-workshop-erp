import frappe

def validate_existing_tables():
    """Validate foreign key relationships for existing tables"""
    
    print("\n" + "="*70)
    print("EXISTING TABLE FOREIGN KEY VALIDATION")
    print("="*70)
    
    # Tables that actually exist
    existing_tables = [
        'Workshop Profile',
        'Customer',
        'Technician',
        'Workshop Role',
        'Workshop Theme',
        'Business Workshop Binding',
        'Customer Vehicle Ownership'
    ]
    
    validation_results = {
        'total_checks': 0,
        'passed_checks': 0,
        'failed_checks': 0,
        'table_status': []
    }
    
    for table_name in existing_tables:
        table_result = {
            'table': table_name,
            'exists': False,
            'record_count': 0,
            'checks': []
        }
        
        try:
            # Check if table exists
            if frappe.db.has_table(f"tab{table_name}"):
                table_result['exists'] = True
                
                # Get record count
                count_result = frappe.db.sql(f"SELECT COUNT(*) FROM `tab{table_name}`")
                table_result['record_count'] = count_result[0][0] if count_result else 0
                
                print(f"\n✅ {table_name}")
                print(f"   Records: {table_result['record_count']}")
                
                # Specific validations based on table
                if table_name == 'Workshop Profile':
                    # Check Workshop Profile integrity
                    check_workshop_profile_integrity(table_result, validation_results)
                
                elif table_name == 'Customer':
                    # Check Customer table integrity
                    check_customer_integrity(table_result, validation_results)
                
                elif table_name == 'Business Workshop Binding':
                    # Check Business Workshop Binding
                    check_business_binding_integrity(table_result, validation_results)
                
                elif table_name == 'Customer Vehicle Ownership':
                    # Check Customer Vehicle Ownership
                    check_vehicle_ownership_integrity(table_result, validation_results)
                
            else:
                table_result['exists'] = False
                print(f"\n❌ {table_name} - Table does not exist")
                
        except Exception as e:
            table_result['error'] = str(e)
            print(f"\n⚠️  {table_name} - Error: {str(e)}")
        
        validation_results['table_status'].append(table_result)
    
    # Print summary
    print(f"\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Checks: {validation_results['total_checks']}")
    print(f"Passed: {validation_results['passed_checks']}")
    print(f"Failed: {validation_results['failed_checks']}")
    
    if validation_results['total_checks'] > 0:
        success_rate = (validation_results['passed_checks'] / validation_results['total_checks']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print("="*70 + "\n")
    
    return validation_results

def check_workshop_profile_integrity(table_result, validation_results):
    """Check Workshop Profile table integrity"""
    
    validation_results['total_checks'] += 1
    
    try:
        # Check for required fields
        required_fields = ['workshop_code', 'workshop_name', 'status']
        missing_fields = []
        
        for field in required_fields:
            if not frappe.db.has_column('tabWorkshop Profile', field):
                missing_fields.append(field)
        
        if missing_fields:
            validation_results['failed_checks'] += 1
            table_result['checks'].append({
                'check': 'Required Fields',
                'status': 'FAILED',
                'details': f"Missing fields: {', '.join(missing_fields)}"
            })
            print(f"   ❌ Missing required fields: {', '.join(missing_fields)}")
        else:
            validation_results['passed_checks'] += 1
            table_result['checks'].append({
                'check': 'Required Fields',
                'status': 'PASSED',
                'details': 'All required fields present'
            })
            print(f"   ✅ All required fields present")
        
        # Check for duplicate workshop codes if there are records
        if table_result['record_count'] > 0:
            validation_results['total_checks'] += 1
            
            duplicates = frappe.db.sql("""
                SELECT workshop_code, COUNT(*) as count
                FROM `tabWorkshop Profile`
                WHERE workshop_code IS NOT NULL
                GROUP BY workshop_code
                HAVING COUNT(*) > 1
            """, as_dict=True)
            
            if duplicates:
                validation_results['failed_checks'] += 1
                table_result['checks'].append({
                    'check': 'Unique Workshop Codes',
                    'status': 'FAILED',
                    'details': f"Found {len(duplicates)} duplicate workshop codes"
                })
                print(f"   ❌ Found {len(duplicates)} duplicate workshop codes")
            else:
                validation_results['passed_checks'] += 1
                table_result['checks'].append({
                    'check': 'Unique Workshop Codes',
                    'status': 'PASSED',
                    'details': 'All workshop codes are unique'
                })
                print(f"   ✅ All workshop codes are unique")
                
    except Exception as e:
        validation_results['failed_checks'] += 1
        table_result['checks'].append({
            'check': 'Workshop Profile Integrity',
            'status': 'ERROR',
            'details': str(e)
        })
        print(f"   ⚠️  Error checking Workshop Profile: {str(e)}")

def check_customer_integrity(table_result, validation_results):
    """Check Customer table integrity"""
    
    validation_results['total_checks'] += 1
    
    try:
        # Check for required fields
        required_fields = ['customer_name']
        missing_fields = []
        
        for field in required_fields:
            if not frappe.db.has_column('tabCustomer', field):
                missing_fields.append(field)
        
        if missing_fields:
            validation_results['failed_checks'] += 1
            print(f"   ❌ Missing required fields: {', '.join(missing_fields)}")
        else:
            validation_results['passed_checks'] += 1
            print(f"   ✅ Customer table structure is valid")
            
    except Exception as e:
        validation_results['failed_checks'] += 1
        print(f"   ⚠️  Error checking Customer: {str(e)}")

def check_business_binding_integrity(table_result, validation_results):
    """Check Business Workshop Binding integrity"""
    
    validation_results['total_checks'] += 1
    
    try:
        if table_result['record_count'] > 0:
            # Check for orphaned bindings
            orphaned = frappe.db.sql("""
                SELECT bwb.name, bwb.business_name
                FROM `tabBusiness Workshop Binding` bwb
                LEFT JOIN `tabWorkshop Profile` wp ON bwb.business_name = wp.workshop_name
                WHERE wp.name IS NULL
                LIMIT 10
            """, as_dict=True)
            
            if orphaned:
                validation_results['failed_checks'] += 1
                print(f"   ❌ Found {len(orphaned)} orphaned business bindings")
            else:
                validation_results['passed_checks'] += 1
                print(f"   ✅ All business bindings are valid")
        else:
            validation_results['passed_checks'] += 1
            print(f"   ✅ No business bindings to validate")
            
    except Exception as e:
        validation_results['failed_checks'] += 1
        print(f"   ⚠️  Error checking Business Binding: {str(e)}")

def check_vehicle_ownership_integrity(table_result, validation_results):
    """Check Customer Vehicle Ownership integrity"""
    
    validation_results['total_checks'] += 1
    
    try:
        if table_result['record_count'] > 0:
            # Check for invalid customer references
            invalid_customers = frappe.db.sql("""
                SELECT cvo.name, cvo.customer
                FROM `tabCustomer Vehicle Ownership` cvo
                LEFT JOIN `tabCustomer` c ON cvo.customer = c.name
                WHERE cvo.customer IS NOT NULL AND c.name IS NULL
                LIMIT 10
            """, as_dict=True)
            
            if invalid_customers:
                validation_results['failed_checks'] += 1
                print(f"   ❌ Found {len(invalid_customers)} invalid customer references")
            else:
                validation_results['passed_checks'] += 1
                print(f"   ✅ All customer references are valid")
        else:
            validation_results['passed_checks'] += 1
            print(f"   ✅ No vehicle ownership records to validate")
            
    except Exception as e:
        validation_results['failed_checks'] += 1
        print(f"   ⚠️  Error checking Vehicle Ownership: {str(e)}")

if __name__ == "__main__":
    validate_existing_tables()
