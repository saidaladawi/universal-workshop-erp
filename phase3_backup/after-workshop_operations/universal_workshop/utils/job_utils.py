"""
Universal Workshop ERP - Background Job Utilities
Provides background job functions for performance optimization
"""

import frappe
from frappe.utils.background_jobs import enqueue
import json

class WorkshopJobs:
    """Workshop-specific background job utilities"""
    
    @staticmethod
    def async_send_notification(customer_id, message, notification_type="info"):
        """Send customer notification asynchronously"""
        enqueue(
            'universal_workshop.utils.job_utils.WorkshopJobs._send_notification',
            customer_id=customer_id,
            message=message,
            notification_type=notification_type,
            queue='short'
        )
    
    @staticmethod
    def _send_notification(customer_id, message, notification_type):
        """Internal notification sending function"""
        try:
            # Get customer details
            customer = frappe.get_doc("Customer", customer_id)
            
            # Create communication record
            communication = frappe.get_doc({
                "doctype": "Communication",
                "communication_type": "Notification",
                "subject": f"Workshop Notification - {notification_type.title()}",
                "content": message,
                "reference_doctype": "Customer",
                "reference_name": customer_id,
                "status": "Open"
            })
            communication.insert(ignore_permissions=True)
            
            # Log successful notification
            frappe.log_error(f"Notification sent to {customer_id}: {message}", "Background Jobs")
            
        except Exception as e:
            frappe.log_error(f"Notification error: {str(e)}", "Background Jobs")
    
    @staticmethod
    def async_update_customer_analytics(customer_id):
        """Update customer analytics asynchronously"""
        enqueue(
            'universal_workshop.utils.job_utils.WorkshopJobs._update_customer_analytics',
            customer_id=customer_id,
            queue='long'
        )
    
    @staticmethod
    def _update_customer_analytics(customer_id):
        """Internal customer analytics update function"""
        try:
            # Calculate customer analytics
            analytics = frappe.db.sql("""
                SELECT 
                    COUNT(*) as total_services,
                    SUM(final_amount) as total_spent,
                    AVG(final_amount) as avg_service_cost,
                    MAX(service_date) as last_service_date,
                    MIN(service_date) as first_service_date,
                    COUNT(DISTINCT vehicle) as vehicles_serviced
                FROM `tabService Order`
                WHERE customer = %s AND docstatus = 1
            """, (customer_id,), as_dict=True)
            
            if analytics:
                analytics_data = analytics[0]
                
                # Update customer record with analytics
                customer = frappe.get_doc("Customer", customer_id)
                customer.db_set("total_services", analytics_data.get("total_services", 0))
                customer.db_set("total_spent", analytics_data.get("total_spent", 0))
                customer.db_set("last_service_date", analytics_data.get("last_service_date"))
                
                # Invalidate customer cache
                from universal_workshop.utils.cache_utils import WorkshopCache
                WorkshopCache.invalidate_customer_cache(customer_id)
                
                frappe.log_error(f"Customer analytics updated for {customer_id}", "Background Jobs")
                
        except Exception as e:
            frappe.log_error(f"Analytics update error: {str(e)}", "Background Jobs")
    
    @staticmethod
    def async_generate_report(report_type, filters, user):
        """Generate reports asynchronously"""
        enqueue(
            'universal_workshop.utils.job_utils.WorkshopJobs._generate_report',
            report_type=report_type,
            filters=filters,
            user=user,
            queue='long'
        )
    
    @staticmethod
    def _generate_report(report_type, filters, user):
        """Internal report generation function"""
        try:
            # Set user context
            frappe.set_user(user)
            
            # Generate report based on type
            if report_type == "service_summary":
                data = WorkshopJobs._generate_service_summary_report(filters)
            elif report_type == "customer_analytics":
                data = WorkshopJobs._generate_customer_analytics_report(filters)
            elif report_type == "technician_performance":
                data = WorkshopJobs._generate_technician_performance_report(filters)
            else:
                data = {"error": "Unknown report type"}
            
            # Save report to file
            report_filename = f"{report_type}_{frappe.utils.today()}.json"
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": report_filename,
                "content": json.dumps(data, indent=2, default=str),
                "is_private": 1
            })
            file_doc.insert(ignore_permissions=True)
            
            # Notify user that report is ready
            WorkshopJobs.async_send_notification(
                user, 
                f"Report '{report_type}' has been generated and is ready for download.",
                "info"
            )
            
        except Exception as e:
            frappe.log_error(f"Report generation error: {str(e)}", "Background Jobs")
    
    @staticmethod
    def _generate_service_summary_report(filters):
        """Generate service summary report"""
        try:
            start_date = filters.get("start_date", frappe.utils.add_days(frappe.utils.today(), -30))
            end_date = filters.get("end_date", frappe.utils.today())
            
            data = frappe.db.sql("""
                SELECT 
                    service_type,
                    COUNT(*) as service_count,
                    SUM(final_amount) as total_revenue,
                    AVG(final_amount) as avg_service_value,
                    COUNT(DISTINCT customer) as unique_customers
                FROM `tabService Order`
                WHERE service_date BETWEEN %s AND %s
                AND docstatus = 1
                GROUP BY service_type
                ORDER BY total_revenue DESC
            """, (start_date, end_date), as_dict=True)
            
            return {
                "report_type": "service_summary",
                "filters": filters,
                "data": data,
                "generated_at": frappe.utils.now()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def _generate_customer_analytics_report(filters):
        """Generate customer analytics report"""
        try:
            data = frappe.db.sql("""
                SELECT 
                    c.name as customer_id,
                    c.customer_name,
                    COUNT(so.name) as total_services,
                    SUM(so.final_amount) as total_spent,
                    AVG(so.final_amount) as avg_service_value,
                    MAX(so.service_date) as last_service_date,
                    COUNT(DISTINCT so.vehicle) as vehicles_count
                FROM `tabCustomer` c
                LEFT JOIN `tabService Order` so ON c.name = so.customer
                WHERE so.docstatus = 1
                GROUP BY c.name
                HAVING total_services > 0
                ORDER BY total_spent DESC
                LIMIT 100
            """, as_dict=True)
            
            return {
                "report_type": "customer_analytics",
                "filters": filters,
                "data": data,
                "generated_at": frappe.utils.now()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def _generate_technician_performance_report(filters):
        """Generate technician performance report"""
        try:
            start_date = filters.get("start_date", frappe.utils.add_days(frappe.utils.today(), -30))
            end_date = filters.get("end_date", frappe.utils.today())
            
            data = frappe.db.sql("""
                SELECT 
                    technician_assigned as technician,
                    COUNT(*) as services_completed,
                    AVG(DATEDIFF(completed_on, started_on)) as avg_completion_days,
                    SUM(final_amount) as total_revenue_generated,
                    COUNT(DISTINCT customer) as unique_customers_served
                FROM `tabService Order`
                WHERE service_date BETWEEN %s AND %s
                AND docstatus = 1
                AND technician_assigned IS NOT NULL
                AND completed_on IS NOT NULL
                GROUP BY technician_assigned
                ORDER BY services_completed DESC
            """, (start_date, end_date), as_dict=True)
            
            return {
                "report_type": "technician_performance",
                "filters": filters,
                "data": data,
                "generated_at": frappe.utils.now()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def async_cleanup_old_data():
        """Clean up old data asynchronously"""
        enqueue(
            'universal_workshop.utils.job_utils.WorkshopJobs._cleanup_old_data',
            queue='long'
        )
    
    @staticmethod
    def _cleanup_old_data():
        """Internal data cleanup function"""
        try:
            # Clean up old communication records (older than 1 year)
            old_communications = frappe.db.sql("""
                DELETE FROM `tabCommunication`
                WHERE creation < DATE_SUB(NOW(), INTERVAL 1 YEAR)
                AND communication_type = 'Notification'
            """)
            
            # Clean up old error logs (older than 6 months)
            old_errors = frappe.db.sql("""
                DELETE FROM `tabError Log`
                WHERE creation < DATE_SUB(NOW(), INTERVAL 6 MONTH)
            """)
            
            # Clean up old version records (older than 3 months)
            old_versions = frappe.db.sql("""
                DELETE FROM `tabVersion`
                WHERE creation < DATE_SUB(NOW(), INTERVAL 3 MONTH)
            """)
            
            frappe.log_error("Old data cleanup completed successfully", "Background Jobs")
            
        except Exception as e:
            frappe.log_error(f"Data cleanup error: {str(e)}", "Background Jobs")
    
    @staticmethod
    def async_warm_cache():
        """Warm up cache asynchronously"""
        enqueue(
            'universal_workshop.utils.job_utils.WorkshopJobs._warm_cache',
            queue='short'
        )
    
    @staticmethod
    def _warm_cache():
        """Internal cache warming function"""
        try:
            from universal_workshop.utils.cache_utils import WorkshopCache
            WorkshopCache.warm_cache()
            
        except Exception as e:
            frappe.log_error(f"Cache warming error: {str(e)}", "Background Jobs")
    
    @staticmethod
    def schedule_periodic_jobs():
        """Schedule periodic background jobs"""
        try:
            # Schedule daily cache warming
            enqueue(
                'universal_workshop.utils.job_utils.WorkshopJobs._warm_cache',
                queue='short'
            )
            
            # Schedule weekly data cleanup
            enqueue(
                'universal_workshop.utils.job_utils.WorkshopJobs._cleanup_old_data',
                queue='long'
            )
            
            frappe.log_error("Periodic jobs scheduled successfully", "Background Jobs")
            
        except Exception as e:
            frappe.log_error(f"Job scheduling error: {str(e)}", "Background Jobs")
