import frappe

def create_test_monitor():
    monitor = frappe.new_doc('Performance Monitor')
    monitor.monitor_name = 'System Performance Test'
    monitor.monitor_name_ar = 'اختبار أداء النظام'
    monitor.monitor_type = 'System Performance'
    monitor.monitoring_enabled = 1
    monitor.alert_enabled = 1
    monitor.cpu_threshold_warning = 70
    monitor.cpu_threshold_critical = 90
    monitor.memory_threshold_warning = 75
    monitor.memory_threshold_critical = 90
    monitor.disk_threshold_warning = 80
    monitor.disk_threshold_critical = 95
    monitor.insert()
    
    # Collect metrics
    result = monitor.collect_all_metrics()
    
    return {
        'monitor_id': monitor.name,
        'monitor_name': monitor.monitor_name,
        'metrics_result': result
    }

if __name__ == '__main__':
    frappe.init(site='universal.local')
    frappe.connect()
    result = create_test_monitor()
    print(f"Created monitor: {result}")
    frappe.db.commit()
