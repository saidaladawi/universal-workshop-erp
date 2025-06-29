"""
Universal Workshop ERP - Core Dashboard Architecture
Provides comprehensive operational dashboard with real-time KPIs and Arabic localization
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, add_days, flt, cint
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

class WorkshopDashboard:
    """Main dashboard controller for Universal Workshop ERP"""
    
    def __init__(self):
        self.user = frappe.session.user
        self.user_roles = frappe.get_roles()
        self.language = frappe.local.lang or 'en'
        self.is_rtl = self.language in ['ar', 'he', 'fa', 'ur']
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data structure"""
        return {
            'layout': self.get_layout_config(),
            'kpis': self.get_kpi_metrics(),
            'widgets': self.get_widget_data(),
            'permissions': self.get_user_permissions(),
            'settings': self.get_dashboard_settings()
        }
    
    def get_layout_config(self) -> Dict[str, Any]:
        """Get responsive layout configuration with RTL support"""
        return {
            'direction': 'rtl' if self.is_rtl else 'ltr',
            'language': self.language,
            'grid_system': 'bootstrap5',
            'responsive_breakpoints': {
                'xs': 576,
                'sm': 768, 
                'md': 992,
                'lg': 1200,
                'xl': 1400
            },
            'layout_zones': {
                'header': {
                    'height': '60px',
                    'components': ['logo', 'navigation', 'user_menu', 'language_switcher']
                },
                'sidebar': {
                    'width': '280px',
                    'collapsible': True,
                    'components': ['quick_actions', 'alerts', 'notifications']
                },
                'main_content': {
                    'grid_columns': 12,
                    'components': ['kpi_cards', 'charts', 'status_board', 'recent_activities']
                },
                'footer': {
                    'height': '40px',
                    'components': ['last_update', 'system_status']
                }
            }
        }
    
    def get_kpi_metrics(self) -> List[Dict[str, Any]]:
        """Get KPI metrics with Arabic localization"""
        kpis = []
        
        # Today's Revenue
        today_revenue = self._get_today_revenue()
        kpis.append({
            'id': 'today_revenue',
            'title': _('Today\'s Revenue') if self.language == 'en' else 'إيرادات اليوم',
            'value': today_revenue,
            'format': 'currency',
            'currency': 'OMR',
            'trend': self._get_revenue_trend(),
            'icon': 'fa-money-bill-wave',
            'color': 'success' if today_revenue > 0 else 'warning',
            'grid_size': 'col-lg-3 col-md-6 col-sm-12'
        })
        
        # Active Service Orders
        active_orders = self._get_active_service_orders()
        kpis.append({
            'id': 'active_orders',
            'title': _('Active Service Orders') if self.language == 'en' else 'أوامر الخدمة النشطة',
            'value': active_orders['count'],
            'format': 'number',
            'subtitle': f"{active_orders['urgent']} " + (_('urgent') if self.language == 'en' else 'عاجل'),
            'trend': self._get_orders_trend(),
            'icon': 'fa-tools',
            'color': 'primary',
            'grid_size': 'col-lg-3 col-md-6 col-sm-12'
        })
        
        # Technician Utilization
        tech_util = self._get_technician_utilization()
        kpis.append({
            'id': 'technician_utilization',
            'title': _('Technician Utilization') if self.language == 'en' else 'استخدام الفنيين',
            'value': tech_util['percentage'],
            'format': 'percentage',
            'subtitle': f"{tech_util['active']}/{tech_util['total']} " + (_('active') if self.language == 'en' else 'نشط'),
            'trend': self._get_utilization_trend(),
            'icon': 'fa-users',
            'color': 'info',
            'grid_size': 'col-lg-3 col-md-6 col-sm-12'
        })
        
        # Inventory Alerts
        inventory_alerts = self._get_inventory_alerts()
        kpis.append({
            'id': 'inventory_alerts',
            'title': _('Inventory Alerts') if self.language == 'en' else 'تنبيهات المخزون',
            'value': inventory_alerts['total'],
            'format': 'number',
            'subtitle': f"{inventory_alerts['critical']} " + (_('critical') if self.language == 'en' else 'حرج'),
            'trend': None,
            'icon': 'fa-exclamation-triangle',
            'color': 'danger' if inventory_alerts['critical'] > 0 else 'success',
            'grid_size': 'col-lg-3 col-md-6 col-sm-12'
        })
        
        return kpis
    
    def get_widget_data(self) -> List[Dict[str, Any]]:
        """Get dashboard widgets configuration"""
        widgets = []
        
        # Service Status Board Widget
        widgets.append({
            'id': 'service_status_board',
            'type': 'kanban',
            'title': _('Service Status Board') if self.language == 'en' else 'لوحة حالة الخدمة',
            'data_source': 'service_orders',
            'columns': self._get_status_columns(),
            'grid_size': 'col-lg-8 col-md-12',
            'height': '400px',
            'refresh_interval': 30
        })
        
        # Quick Actions Widget
        widgets.append({
            'id': 'quick_actions',
            'type': 'action_grid',
            'title': _('Quick Actions') if self.language == 'en' else 'إجراءات سريعة',
            'actions': self._get_quick_actions(),
            'grid_size': 'col-lg-4 col-md-12',
            'height': '400px'
        })
        
        # Revenue Chart Widget
        widgets.append({
            'id': 'revenue_chart',
            'type': 'chart',
            'title': _('Revenue Trend') if self.language == 'en' else 'اتجاه الإيرادات',
            'chart_type': 'line',
            'data_source': 'revenue_data',
            'grid_size': 'col-lg-6 col-md-12',
            'height': '300px',
            'refresh_interval': 300
        })
        
        # Customer Satisfaction Widget
        widgets.append({
            'id': 'customer_satisfaction',
            'type': 'gauge',
            'title': _('Customer Satisfaction') if self.language == 'en' else 'رضا العملاء',
            'data_source': 'satisfaction_data',
            'grid_size': 'col-lg-6 col-md-12',
            'height': '300px',
            'refresh_interval': 600
        })
        
        # Recent Activities Widget
        widgets.append({
            'id': 'recent_activities',
            'type': 'timeline',
            'title': _('Recent Activities') if self.language == 'en' else 'الأنشطة الحديثة',
            'data_source': 'activity_log',
            'grid_size': 'col-lg-12',
            'height': '250px',
            'refresh_interval': 60
        })
        
        return widgets
    
    def get_user_permissions(self) -> Dict[str, bool]:
        """Get user permissions for dashboard components"""
        return {
            'can_view_revenue': 'System Manager' in self.user_roles or 'Workshop Manager' in self.user_roles,
            'can_create_orders': 'Service Advisor' in self.user_roles or 'Workshop Manager' in self.user_roles,
            'can_manage_inventory': 'Parts Manager' in self.user_roles or 'Workshop Manager' in self.user_roles,
            'can_assign_technicians': 'Workshop Supervisor' in self.user_roles or 'Workshop Manager' in self.user_roles,
            'can_view_analytics': 'System Manager' in self.user_roles or 'Workshop Manager' in self.user_roles,
            'can_manage_customers': 'Service Advisor' in self.user_roles or 'Workshop Manager' in self.user_roles
        }
    
    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Get dashboard configuration settings"""
        return {
            'auto_refresh': True,
            'refresh_interval': 30,  # seconds
            'theme': 'workshop_theme',
            'show_animations': True,
            'sound_notifications': False,
            'compact_mode': False,
            'rtl_support': self.is_rtl,
            'number_format': 'arabic' if self.language == 'ar' else 'western',
            'date_format': 'dd/mm/yyyy' if self.language == 'ar' else 'mm/dd/yyyy',
            'currency_symbol': 'ر.ع.' if self.language == 'ar' else 'OMR'
        }
    
    def _get_today_revenue(self) -> float:
        """Calculate today's revenue from completed service orders"""
        today = nowdate()
        revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """, (today,))[0][0]
        return flt(revenue, 2)
    
    def _get_revenue_trend(self) -> Dict[str, Any]:
        """Get revenue trend compared to yesterday"""
        yesterday = add_days(nowdate(), -1)
        yesterday_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """, (yesterday,))[0][0]
        
        today_revenue = self._get_today_revenue()
        if yesterday_revenue > 0:
            change = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
        else:
            change = 100 if today_revenue > 0 else 0
            
        return {
            'direction': 'up' if change >= 0 else 'down',
            'percentage': abs(change),
            'color': 'success' if change >= 0 else 'danger'
        }
    
    def _get_active_service_orders(self) -> Dict[str, int]:
        """Get active service orders count"""
        result = frappe.db.sql("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as urgent
            FROM `tabWork Order`
            WHERE status IN ('Open', 'In Progress', 'Material Transferred')
            AND docstatus = 1
        """, as_dict=True)[0]
        
        return {
            'count': cint(result.total),
            'urgent': cint(result.urgent)
        }
    
    def _get_orders_trend(self) -> Dict[str, Any]:
        """Get service orders trend"""
        # Compare with last week
        week_ago = add_days(nowdate(), -7)
        last_week_orders = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWork Order`
            WHERE creation >= %s AND creation < %s
            AND docstatus = 1
        """, (week_ago, nowdate()))[0][0]
        
        this_week_orders = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabWork Order`
            WHERE creation >= %s
            AND docstatus = 1
        """, (nowdate(),))[0][0]
        
        if last_week_orders > 0:
            change = ((this_week_orders - last_week_orders) / last_week_orders) * 100
        else:
            change = 100 if this_week_orders > 0 else 0
            
        return {
            'direction': 'up' if change >= 0 else 'down',
            'percentage': abs(change),
            'color': 'success' if change >= 0 else 'warning'
        }
    
    def _get_technician_utilization(self) -> Dict[str, Any]:
        """Get technician utilization statistics"""
        total_technicians = frappe.db.count('Employee', {
            'designation': 'Technician',
            'status': 'Active'
        })
        
        active_technicians = frappe.db.sql("""
            SELECT COUNT(DISTINCT employee) as active
            FROM `tabWork Order`
            WHERE status IN ('Open', 'In Progress', 'Material Transferred')
            AND employee IS NOT NULL
            AND docstatus = 1
        """)[0][0]
        
        percentage = (active_technicians / total_technicians * 100) if total_technicians > 0 else 0
        
        return {
            'total': total_technicians,
            'active': cint(active_technicians),
            'percentage': flt(percentage, 1)
        }
    
    def _get_utilization_trend(self) -> Dict[str, Any]:
        """Get utilization trend"""
        # Simplified trend calculation
        current_util = self._get_technician_utilization()['percentage']
        target_util = 85  # Target utilization percentage
        
        return {
            'direction': 'up' if current_util >= target_util else 'down',
            'percentage': abs(current_util - target_util),
            'color': 'success' if current_util >= target_util else 'warning'
        }
    
    def _get_inventory_alerts(self) -> Dict[str, int]:
        """Get inventory alert counts"""
        # Low stock items
        low_stock = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabItem`
            WHERE is_stock_item = 1
            AND (
                (reorder_level > 0 AND (
                    SELECT COALESCE(SUM(actual_qty), 0)
                    FROM `tabBin`
                    WHERE item_code = `tabItem`.item_code
                )) <= reorder_level
            )
        """)[0][0]
        
        # Critical stock (below minimum)
        critical_stock = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabItem`
            WHERE is_stock_item = 1
            AND (
                SELECT COALESCE(SUM(actual_qty), 0)
                FROM `tabBin`
                WHERE item_code = `tabItem`.item_code
            ) <= 0
        """)[0][0]
        
        return {
            'total': cint(low_stock),
            'critical': cint(critical_stock)
        }
    
    def _get_status_columns(self) -> List[Dict[str, Any]]:
        """Get Kanban status columns configuration"""
        return [
            {
                'id': 'pending',
                'title': _('Pending') if self.language == 'en' else 'معلق',
                'status_filter': ['Draft', 'Open'],
                'color': 'warning',
                'icon': 'fa-clock'
            },
            {
                'id': 'in_progress',
                'title': _('In Progress') if self.language == 'en' else 'قيد التنفيذ',
                'status_filter': ['In Progress', 'Material Transferred'],
                'color': 'primary',
                'icon': 'fa-cog'
            },
            {
                'id': 'quality_check',
                'title': _('Quality Check') if self.language == 'en' else 'فحص الجودة',
                'status_filter': ['Completed'],
                'color': 'info',
                'icon': 'fa-search'
            },
            {
                'id': 'completed',
                'title': _('Completed') if self.language == 'en' else 'مكتمل',
                'status_filter': ['Completed'],
                'color': 'success',
                'icon': 'fa-check'
            }
        ]
    
    def _get_quick_actions(self) -> List[Dict[str, Any]]:
        """Get quick action buttons configuration"""
        actions = []
        permissions = self.get_user_permissions()
        
        if permissions['can_create_orders']:
            actions.append({
                'id': 'new_service_order',
                'title': _('New Service Order') if self.language == 'en' else 'أمر خدمة جديد',
                'icon': 'fa-plus-circle',
                'color': 'primary',
                'action': 'create_service_order'
            })
        
        if permissions['can_manage_customers']:
            actions.append({
                'id': 'register_customer',
                'title': _('Register Customer') if self.language == 'en' else 'تسجيل عميل',
                'icon': 'fa-user-plus',
                'color': 'success',
                'action': 'register_customer'
            })
        
        if permissions['can_manage_inventory']:
            actions.append({
                'id': 'inventory_adjustment',
                'title': _('Inventory Adjustment') if self.language == 'en' else 'تعديل المخزون',
                'icon': 'fa-boxes',
                'color': 'warning',
                'action': 'inventory_adjustment'
            })
        
        actions.append({
            'id': 'process_payment',
            'title': _('Process Payment') if self.language == 'en' else 'معالجة الدفع',
            'icon': 'fa-credit-card',
            'color': 'info',
            'action': 'process_payment'
        })
        
        return actions


@frappe.whitelist()
def get_dashboard_data():
    """API endpoint to get dashboard data"""
    dashboard = WorkshopDashboard()
    return dashboard.get_dashboard_data()


@frappe.whitelist()
def get_kpi_metrics():
    """API endpoint to get KPI metrics only"""
    dashboard = WorkshopDashboard()
    return dashboard.get_kpi_metrics()


@frappe.whitelist()
def get_widget_data(widget_id=None):
    """API endpoint to get specific widget data"""
    dashboard = WorkshopDashboard()
    widgets = dashboard.get_widget_data()
    
    if widget_id:
        return next((w for w in widgets if w['id'] == widget_id), None)
    return widgets


@frappe.whitelist()
def refresh_dashboard():
    """API endpoint to refresh dashboard data"""
    return {
        'timestamp': frappe.utils.now(),
        'data': get_dashboard_data()
    } 