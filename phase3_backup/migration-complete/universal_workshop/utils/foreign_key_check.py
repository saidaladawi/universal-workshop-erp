import frappe

def check_foreign_key_constraints():
    """Check foreign key constraints and table relationships"""
    
    results = {
        'table_checks': [],
        'relationship_checks': [],
        'schema_validation': [],
        'summary': {}
    }
    
    # Define key tables and their expected Link fields
    key_tables = {
        'Service Order': {
            'link_fields': [
                ('customer', 'Customer'),
                ('vehicle', 'Vehicle'),
                ('technician_assigned', 'Technician')
            ]
        },
        'Vehicle': {
            'link_fields': [
                ('customer', 'Customer')
            ]
        },
        'Service Estimate': {
            'link_fields': [
                ('customer', 'Customer'),
                ('vehicle', 'Vehicle')
            ]
        },
        'Vehicle Inspection': {
            'link_fields': [
                ('vehicle', 'Vehicle'),
                ('technician', 'Technician')
            ]
        }
    }
    
    # Check table existence and structure
    for table_name, config in key_tables.items():
        table_check = {
            'table': table_name,
            'exists': False,
            'record_count': 0,
            'field_checks': []
        }
        
        try:
            # Check if table exists
            if frappe.db.has_table(f"tab{table_name}"):
                table_check['exists'] = True
                
                # Get record count
                count_result = frappe.db.sql(f"SELECT COUNT(*) FROM `tab{table_name}`")
                table_check['record_count'] = count_result[0][0] if count_result else 0
                
                # Check each link field
                for field_name, target_doctype in config['link_fields']:
                    field_check = {
                        'field': field_name,
                        'target_doctype': target_doctype,
                        'field_exists': False,
                        'target_table_exists': False,
                        'data_integrity': 'N/A'
                    }
                    
                    # Check if field exists in source table
                    if frappe.db.has_column(f"tab{table_name}", field_name):
                        field_check['field_exists'] = True
                    
                    # Check if target table exists
                    if frappe.db.has_table(f"tab{target_doctype}"):
                        field_check['target_table_exists'] = True
                    
                    # Check data integrity if both exist and there's data
                    if (field_check['field_exists'] and 
                        field_check['target_table_exists'] and 
                        table_check['record_count'] > 0):
                        
                        try:
                            # Count invalid references
                            invalid_count = frappe.db.sql(f"""
                                SELECT COUNT(*) 
                                FROM `tab{table_name}` s
                                LEFT JOIN `tab{target_doctype}` t ON s.`{field_name}` = t.name
                                WHERE s.`{field_name}` IS NOT NULL 
                                AND s.`{field_name}` != ''
                                AND t.name IS NULL
                            """)[0][0]
                            
                            # Count total references
                            total_refs = frappe.db.sql(f"""
                                SELECT COUNT(*) 
                                FROM `tab{table_name}`
                                WHERE `{field_name}` IS NOT NULL 
                                AND `{field_name}` != ''
                            """)[0][0]
                            
                            if total_refs == 0:
                                field_check['data_integrity'] = 'NO_DATA'
                            elif invalid_count == 0:
                                field_check['data_integrity'] = 'VALID'
                            else:
                                field_check['data_integrity'] = f'INVALID ({invalid_count}/{total_refs})'
                                
                        except Exception as e:
                            field_check['data_integrity'] = f'ERROR: {str(e)}'
                    
                    table_check['field_checks'].append(field_check)
                    
        except Exception as e:
            table_check['error'] = str(e)
        
        results['table_checks'].append(table_check)
    
    # Generate summary
    total_tables = len(key_tables)
    existing_tables = sum(1 for check in results['table_checks'] if check['exists'])
    total_fields = sum(len(check['field_checks']) for check in results['table_checks'])
    valid_fields = sum(1 for check in results['table_checks'] 
                      for field in check['field_checks'] 
                      if field['field_exists'] and field['target_table_exists'])
    
    results['summary'] = {
        'total_tables_checked': total_tables,
        'existing_tables': existing_tables,
        'total_link_fields': total_fields,
        'valid_link_fields': valid_fields,
        'schema_health': f"{valid_fields}/{total_fields} link fields valid",
        'table_health': f"{existing_tables}/{total_tables} tables exist"
    }
    
    return results

def print_foreign_key_report():
    """Print a formatted foreign key validation report"""
    
    print("\n" + "="*60)
    print("UNIVERSAL WORKSHOP ERP - FOREIGN KEY VALIDATION REPORT")
    print("="*60)
    
    results = check_foreign_key_constraints()
    
    # Print summary
    summary = results['summary']
    print(f"\nSUMMARY:")
    print(f"- Tables: {summary['table_health']}")
    print(f"- Link Fields: {summary['schema_health']}")
    
    # Print detailed results
    print(f"\nDETAILED RESULTS:")
    print("-" * 60)
    
    for table_check in results['table_checks']:
        status_icon = "✅" if table_check['exists'] else "❌"
        print(f"\n{status_icon} {table_check['table']}")
        print(f"   Records: {table_check['record_count']}")
        
        if table_check['exists']:
            for field in table_check['field_checks']:
                field_icon = "✅" if field['field_exists'] and field['target_table_exists'] else "❌"
                integrity_status = field['data_integrity']
                print(f"   {field_icon} {field['field']} -> {field['target_doctype']} [{integrity_status}]")
        
        if 'error' in table_check:
            print(f"   ⚠️  Error: {table_check['error']}")
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60 + "\n")
    
    return results

if __name__ == "__main__":
    print_foreign_key_report()
