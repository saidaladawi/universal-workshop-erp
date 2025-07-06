"""
Universal Workshop ERP - Performance Visualizations Engine
Real-time data visualization with Chart.js integration and Arabic RTL support
"""

import json
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, add_months, add_days
from datetime import datetime, timedelta
from collections import defaultdict


class PerformanceVisualizationEngine:
    """
    Main engine for generating performance charts and visualizations
    with Arabic RTL support and real-time data updates
    """
    
    CHART_TYPES = {
        'revenue_trend': {
            'type': 'line',
            'title_en': 'Revenue Trend',
            'title_ar': 'اتجاه الإيرادات',
            'color': '#4e73df',
            'interval': 'daily'
        },
        'service_completion': {
            'type': 'doughnut',
            'title_en': 'Service Completion Rate',
            'title_ar': 'معدل إنجاز الخدمات',
            'color': '#1cc88a',
            'interval': 'daily'
        },
        'technician_performance': {
            'type': 'bar',
            'title_en': 'Technician Performance',
            'title_ar': 'أداء الفنيين',
            'color': '#36b9cc',
            'interval': 'weekly'
        },
        'customer_satisfaction': {
            'type': 'gauge',
            'title_en': 'Customer Satisfaction',
            'title_ar': 'رضا العملاء',
            'color': '#f6c23e',
            'interval': 'daily'
        },
        'inventory_turnover': {
            'type': 'area',
            'title_en': 'Inventory Turnover',
            'title_ar': 'دوران المخزون',
            'color': '#e74a3b',
            'interval': 'monthly'
        },
        'service_type_distribution': {
            'type': 'pie',
            'title_en': 'Service Type Distribution',
            'title_ar': 'توزيع أنواع الخدمات',
            'color': '#5a5c69',
            'interval': 'weekly'
        },
        'monthly_targets': {
            'type': 'mixed',
            'title_en': 'Monthly Targets vs Achievement',
            'title_ar': 'الأهداف الشهرية مقابل الإنجاز',
            'color': '#858796',
            'interval': 'monthly'
        }
    }
    
    def __init__(self):
        self.language = frappe.local.lang or 'en'
        self.is_arabic = self.language == 'ar'
        self.user_role = frappe.get_roles(frappe.session.user)
        
    def get_chart_config(self, chart_id, time_range='30days', filters=None):
        """Get complete chart configuration with data and options"""
        
        if chart_id not in self.CHART_TYPES:
            frappe.throw(_("Invalid chart type: {0}").format(chart_id))
            
        chart_info = self.CHART_TYPES[chart_id]
        
        # Get chart data
        data = self._get_chart_data(chart_id, time_range, filters or {})
        
        # Get chart options
        options = self._get_chart_options(chart_id, chart_info)
        
        return {
            'id': chart_id,
            'type': chart_info['type'],
            'title': chart_info['title_ar'] if self.is_arabic else chart_info['title_en'],
            'data': data,
            'options': options,
            'rtl': self.is_arabic,
            'language': self.language,
            'refresh_interval': self._get_refresh_interval(chart_info['interval']),
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_chart_data(self, chart_id, time_range, filters):
        """Get data for specific chart type"""
        
        data_methods = {
            'revenue_trend': self._get_revenue_trend_data,
            'service_completion': self._get_service_completion_data,
            'technician_performance': self._get_technician_performance_data,
            'customer_satisfaction': self._get_customer_satisfaction_data,
            'inventory_turnover': self._get_inventory_turnover_data,
            'service_type_distribution': self._get_service_type_distribution_data,
            'monthly_targets': self._get_monthly_targets_data
        }
        
        method = data_methods.get(chart_id)
        if not method:
            return {'labels': [], 'datasets': []}
            
        return method(time_range, filters)
    
    def _get_revenue_trend_data(self, time_range, filters):
        """Get revenue trend chart data"""
        
        end_date = getdate()
        if time_range == '7days':
            start_date = add_days(end_date, -7)
            date_format = '%Y-%m-%d'
        elif time_range == '30days':
            start_date = add_days(end_date, -30)
            date_format = '%Y-%m-%d'
        elif time_range == '6months':
            start_date = add_months(end_date, -6)
            date_format = '%Y-%m'
        else:
            start_date = add_days(end_date, -30)
            date_format = '%Y-%m-%d'
        
        # Query revenue data
        revenue_data = frappe.db.sql("""
            SELECT 
                DATE(posting_date) as date,
                SUM(grand_total) as revenue,
                COUNT(*) as order_count
            FROM `tabSales Invoice`
            WHERE 
                docstatus = 1
                AND posting_date BETWEEN %s AND %s
                AND company = %s
            GROUP BY DATE(posting_date)
            ORDER BY date
        """, [start_date, end_date, frappe.defaults.get_user_default("Company")], as_dict=True)
        
        # Format data for Chart.js
        labels = []
        revenue_values = []
        order_counts = []
        
        for row in revenue_data:
            label = self._format_date_label(row.date, date_format)
            labels.append(label)
            revenue_values.append(flt(row.revenue, 3))
            order_counts.append(cint(row.order_count))
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': _('Revenue (OMR)'),
                    'data': revenue_values,
                    'borderColor': '#4e73df',
                    'backgroundColor': 'rgba(78, 115, 223, 0.1)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4
                },
                {
                    'label': _('Order Count'),
                    'data': order_counts,
                    'borderColor': '#1cc88a',
                    'backgroundColor': 'rgba(28, 200, 138, 0.1)',
                    'borderWidth': 2,
                    'fill': False,
                    'yAxisID': 'y1'
                }
            ]
        }
    
    def _get_service_completion_data(self, time_range, filters):
        """Get service completion rate data"""
        
        # Get service order status counts
        status_counts = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count
            FROM `tabService Order`
            WHERE 
                creation >= %s
                AND company = %s
            GROUP BY status
        """, [add_days(getdate(), -30), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        status_mapping = {
            'Draft': {'label_en': 'Draft', 'label_ar': 'مسودة', 'color': '#6c757d'},
            'Scheduled': {'label_en': 'Scheduled', 'label_ar': 'مجدولة', 'color': '#ffc107'},
            'In Progress': {'label_en': 'In Progress', 'label_ar': 'قيد التنفيذ', 'color': '#17a2b8'},
            'Quality Check': {'label_en': 'Quality Check', 'label_ar': 'فحص الجودة', 'color': '#fd7e14'},
            'Completed': {'label_en': 'Completed', 'label_ar': 'مكتملة', 'color': '#28a745'},
            'Delivered': {'label_en': 'Delivered', 'label_ar': 'مسلمة', 'color': '#20c997'},
            'Cancelled': {'label_en': 'Cancelled', 'label_ar': 'ملغية', 'color': '#dc3545'}
        }
        
        labels = []
        data_values = []
        colors = []
        
        for row in status_counts:
            status_info = status_mapping.get(row.status, {})
            label = status_info.get('label_ar' if self.is_arabic else 'label_en', row.status)
            labels.append(label)
            data_values.append(row.count)
            colors.append(status_info.get('color', '#6c757d'))
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data_values,
                'backgroundColor': colors,
                'borderWidth': 1,
                'hoverBorderWidth': 2
            }]
        }
    
    def _get_technician_performance_data(self, time_range, filters):
        """Get technician performance chart data"""
        
        # Get technician performance metrics
        performance_data = frappe.db.sql("""
            SELECT 
                t.technician_name,
                t.technician_name_ar,
                COUNT(so.name) as total_orders,
                AVG(TIMESTAMPDIFF(HOUR, so.start_time, so.end_time)) as avg_hours,
                SUM(CASE WHEN so.status = 'Completed' THEN 1 ELSE 0 END) as completed_orders,
                AVG(so.customer_rating) as avg_rating
            FROM `tabTechnician` t
            LEFT JOIN `tabService Order` so ON t.name = so.assigned_technician
            WHERE 
                so.creation >= %s
                AND so.company = %s
            GROUP BY t.name
            HAVING total_orders > 0
            ORDER BY completed_orders DESC
            LIMIT 10
        """, [add_days(getdate(), -30), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        labels = []
        total_orders = []
        completed_orders = []
        avg_ratings = []
        
        for row in performance_data:
            name = row.technician_name_ar if self.is_arabic and row.technician_name_ar else row.technician_name
            labels.append(name)
            total_orders.append(row.total_orders)
            completed_orders.append(row.completed_orders)
            avg_ratings.append(flt(row.avg_rating or 0, 1))
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': _('Total Orders'),
                    'data': total_orders,
                    'backgroundColor': 'rgba(78, 115, 223, 0.8)',
                    'borderColor': '#4e73df',
                    'borderWidth': 1
                },
                {
                    'label': _('Completed Orders'),
                    'data': completed_orders,
                    'backgroundColor': 'rgba(28, 200, 138, 0.8)',
                    'borderColor': '#1cc88a',
                    'borderWidth': 1
                }
            ]
        }
    
    def _get_customer_satisfaction_data(self, time_range, filters):
        """Get customer satisfaction gauge data"""
        
        # Calculate average customer satisfaction
        satisfaction_data = frappe.db.sql("""
            SELECT 
                AVG(customer_rating) as avg_rating,
                COUNT(*) as total_ratings
            FROM `tabService Order`
            WHERE 
                customer_rating IS NOT NULL
                AND creation >= %s
                AND company = %s
        """, [add_days(getdate(), -30), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        avg_rating = flt(satisfaction_data[0].avg_rating or 0, 1) if satisfaction_data else 0
        total_ratings = satisfaction_data[0].total_ratings if satisfaction_data else 0
        
        # Convert to percentage (assuming 5-star rating)
        satisfaction_percentage = (avg_rating / 5.0) * 100
        
        return {
            'value': satisfaction_percentage,
            'max': 100,
            'avg_rating': avg_rating,
            'total_ratings': total_ratings,
            'color': self._get_satisfaction_color(satisfaction_percentage)
        }
    
    def _get_inventory_turnover_data(self, time_range, filters):
        """Get inventory turnover chart data"""
        
        # Get inventory turnover by month
        turnover_data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%Y-%m') as month,
                SUM(qty * rate) as total_cost
            FROM `tabStock Ledger Entry`
            WHERE 
                voucher_type = 'Sales Invoice'
                AND posting_date >= %s
                AND company = %s
            GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
            ORDER BY month
        """, [add_months(getdate(), -6), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        labels = []
        values = []
        
        for row in turnover_data:
            month_label = self._format_month_label(row.month)
            labels.append(month_label)
            values.append(flt(row.total_cost, 2))
        
        return {
            'labels': labels,
            'datasets': [{
                'label': _('Inventory Cost (OMR)'),
                'data': values,
                'backgroundColor': 'rgba(231, 74, 59, 0.1)',
                'borderColor': '#e74a3b',
                'borderWidth': 2,
                'fill': True,
                'tension': 0.4
            }]
        }
    
    def _get_service_type_distribution_data(self, time_range, filters):
        """Get service type distribution data"""
        
        # Get service type distribution
        service_data = frappe.db.sql("""
            SELECT 
                st.service_type,
                st.service_type_ar,
                COUNT(so.name) as count,
                SUM(so.grand_total) as revenue
            FROM `tabService Order` so
            JOIN `tabService Type` st ON so.service_type = st.name
            WHERE 
                so.creation >= %s
                AND so.company = %s
            GROUP BY st.name
            ORDER BY count DESC
        """, [add_days(getdate(), -30), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        labels = []
        data_values = []
        colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69']
        
        for i, row in enumerate(service_data):
            label = row.service_type_ar if self.is_arabic and row.service_type_ar else row.service_type
            labels.append(label)
            data_values.append(row.count)
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data_values,
                'backgroundColor': colors[:len(data_values)],
                'borderWidth': 1
            }]
        }
    
    def _get_monthly_targets_data(self, time_range, filters):
        """Get monthly targets vs achievement data"""
        
        # Get monthly targets and achievements
        current_month = datetime.now().strftime('%Y-%m')
        
        # This would typically come from a Monthly Targets DocType
        # For now, we'll use calculated data
        monthly_data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%Y-%m') as month,
                SUM(grand_total) as achieved_revenue,
                COUNT(*) as achieved_orders
            FROM `tabSales Invoice`
            WHERE 
                docstatus = 1
                AND posting_date >= %s
                AND company = %s
            GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
            ORDER BY month
        """, [add_months(getdate(), -6), frappe.defaults.get_user_default("Company")], as_dict=True)
        
        labels = []
        achieved_values = []
        target_values = []
        
        for row in monthly_data:
            month_label = self._format_month_label(row.month)
            labels.append(month_label)
            achieved_values.append(flt(row.achieved_revenue, 2))
            # For demo, set target as 120% of achieved
            target_values.append(flt(row.achieved_revenue * 1.2, 2))
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'type': 'bar',
                    'label': _('Achieved Revenue'),
                    'data': achieved_values,
                    'backgroundColor': 'rgba(28, 200, 138, 0.8)',
                    'borderColor': '#1cc88a',
                    'borderWidth': 1
                },
                {
                    'type': 'line',
                    'label': _('Target Revenue'),
                    'data': target_values,
                    'borderColor': '#e74a3b',
                    'backgroundColor': 'rgba(231, 74, 59, 0.1)',
                    'borderWidth': 2,
                    'fill': False
                }
            ]
        }
    
    def _get_chart_options(self, chart_id, chart_info):
        """Get Chart.js options for specific chart type"""
        
        base_options = {
            'responsive': True,
            'maintainAspectRatio': False,
            'locale': self.language,
            'plugins': {
                'legend': {
                    'display': True,
                    'position': 'top',
                    'rtl': self.is_arabic,
                    'labels': {
                        'font': {
                            'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif',
                            'size': 12
                        },
                        'usePointStyle': True
                    }
                },
                'tooltip': {
                    'rtl': self.is_arabic,
                    'callbacks': {
                        'label': "function(context) { return context.dataset.label + ': ' + formatArabicNumber(context.parsed.y); }"
                    }
                }
            },
            'layout': {
                'padding': {
                    'top': 10,
                    'bottom': 10,
                    'left': 10 if self.is_arabic else 0,
                    'right': 0 if self.is_arabic else 10
                }
            }
        }
        
        # Chart-specific options
        if chart_info['type'] in ['line', 'area']:
            base_options['scales'] = {
                'x': {
                    'grid': {'display': False},
                    'ticks': {
                        'font': {'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif'}
                    }
                },
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'callback': "function(value) { return formatArabicNumber(value); }",
                        'font': {'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif'}
                    }
                }
            }
            
            if chart_id == 'revenue_trend':
                base_options['scales']['y1'] = {
                    'type': 'linear',
                    'display': True,
                    'position': 'left' if self.is_arabic else 'right',
                    'grid': {'drawOnChartArea': False},
                    'ticks': {
                        'callback': "function(value) { return formatArabicNumber(value); }",
                        'font': {'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif'}
                    }
                }
        
        elif chart_info['type'] == 'bar':
            base_options['scales'] = {
                'x': {
                    'grid': {'display': False},
                    'ticks': {
                        'maxRotation': 45,
                        'font': {'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif'}
                    }
                },
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'callback': "function(value) { return formatArabicNumber(value); }",
                        'font': {'family': 'Cairo, Tahoma, Arial, sans-serif' if self.is_arabic else 'system-ui, sans-serif'}
                    }
                }
            }
        
        elif chart_info['type'] in ['pie', 'doughnut']:
            base_options['plugins']['tooltip']['callbacks'] = {
                'label': "function(context) { const total = context.dataset.data.reduce((a, b) => a + b, 0); const percentage = ((context.parsed * 100) / total).toFixed(1); return context.label + ': ' + formatArabicNumber(context.parsed) + ' (' + formatArabicNumber(percentage) + '%)'; }"
            }
        
        elif chart_info['type'] == 'gauge':
            # For gauge charts, we'll use a custom implementation
            base_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'circumference': 180,
                'rotation': 270,
                'cutout': '80%',
                'plugins': {
                    'legend': {'display': False},
                    'tooltip': {'enabled': False}
                }
            }
        
        return base_options
    
    def _get_refresh_interval(self, interval_type):
        """Get refresh interval in milliseconds"""
        intervals = {
            'daily': 300000,    # 5 minutes
            'weekly': 900000,   # 15 minutes
            'monthly': 1800000  # 30 minutes
        }
        return intervals.get(interval_type, 300000)
    
    def _format_date_label(self, date, format_type):
        """Format date label for charts"""
        if self.is_arabic:
            arabic_months = [
                'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
            ]
            
            if format_type == '%Y-%m':
                month_num = int(date.strftime('%m'))
                year = date.strftime('%Y')
                return f"{arabic_months[month_num - 1]} {self._convert_to_arabic_numerals(year)}"
            else:
                day = self._convert_to_arabic_numerals(date.strftime('%d'))
                month_num = int(date.strftime('%m'))
                return f"{day} {arabic_months[month_num - 1]}"
        else:
            if format_type == '%Y-%m':
                return date.strftime('%b %Y')
            else:
                return date.strftime('%m/%d')
    
    def _format_month_label(self, month_str):
        """Format month label for charts"""
        if self.is_arabic:
            arabic_months = [
                'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
            ]
            year, month = month_str.split('-')
            month_num = int(month)
            return f"{arabic_months[month_num - 1]} {self._convert_to_arabic_numerals(year)}"
        else:
            date_obj = datetime.strptime(month_str, '%Y-%m')
            return date_obj.strftime('%b %Y')
    
    def _convert_to_arabic_numerals(self, text):
        """Convert Western numerals to Arabic-Indic numerals"""
        if not self.is_arabic:
            return text
            
        arabic_numerals = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
        }
        
        result = str(text)
        for western, arabic in arabic_numerals.items():
            result = result.replace(western, arabic)
        return result
    
    def _get_satisfaction_color(self, percentage):
        """Get color based on satisfaction percentage"""
        if percentage >= 80:
            return '#28a745'  # Green
        elif percentage >= 60:
            return '#ffc107'  # Yellow
        else:
            return '#dc3545'  # Red


@frappe.whitelist()
def get_chart_config(chart_id, time_range='30days', filters=None):
    """API method to get chart configuration"""
    try:
        engine = PerformanceVisualizationEngine()
        
        if filters and isinstance(filters, str):
            filters = json.loads(filters)
        
        config = engine.get_chart_config(chart_id, time_range, filters)
        return config
    except Exception as e:
        frappe.log_error(f"Error getting chart config: {str(e)}")
        return {'error': str(e)}


@frappe.whitelist()
def get_all_charts_config(time_range='30days', chart_ids=None):
    """API method to get all charts configuration at once"""
    try:
        engine = PerformanceVisualizationEngine()
        
        if chart_ids:
            if isinstance(chart_ids, str):
                chart_ids = json.loads(chart_ids)
        else:
            chart_ids = list(engine.CHART_TYPES.keys())
        
        charts = {}
        for chart_id in chart_ids:
            if chart_id in engine.CHART_TYPES:
                charts[chart_id] = engine.get_chart_config(chart_id, time_range)
        
        return {
            'charts': charts,
            'last_updated': datetime.now().isoformat(),
            'language': engine.language,
            'rtl': engine.is_arabic
        }
    except Exception as e:
        frappe.log_error(f"Error getting all charts config: {str(e)}")
        return {'error': str(e)}


@frappe.whitelist()
def get_chart_export_data(chart_id, time_range='30days', export_format='pdf'):
    """API method to export chart data"""
    try:
        engine = PerformanceVisualizationEngine()
        config = engine.get_chart_config(chart_id, time_range)
        
        if export_format == 'pdf':
            # This would integrate with a PDF generation service
            return {'pdf_url': f'/api/method/generate_chart_pdf?chart_id={chart_id}'}
        elif export_format == 'excel':
            # This would generate Excel data
            return {'excel_data': config['data']}
        else:
            return config['data']
    except Exception as e:
        frappe.log_error(f"Error exporting chart data: {str(e)}")
        return {'error': str(e)}


@frappe.whitelist()
def refresh_chart_data(chart_id):
    """API method to refresh specific chart data"""
    try:
        engine = PerformanceVisualizationEngine()
        config = engine.get_chart_config(chart_id)
        
        return {
            'chart_id': chart_id,
            'data': config['data'],
            'last_updated': config['last_updated']
        }
    except Exception as e:
        frappe.log_error(f"Error refreshing chart data: {str(e)}")
        return {'error': str(e)} 