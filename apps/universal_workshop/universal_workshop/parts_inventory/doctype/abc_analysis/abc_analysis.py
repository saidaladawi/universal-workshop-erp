# Copyright (c) 2025, Universal Workshop ERP
# For license information, see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta
import json

class ABCAnalysis(Document):
    def validate(self):
        """Validate ABC analysis configuration and run analysis"""
        self.validate_percentages()
        self.validate_analysis_period()
        
        if self.analysis_status == "Draft":
            self.run_abc_analysis()
    
    def validate_percentages(self):
        """Validate that category percentages sum to 100%"""
        total = (self.category_a_percentage or 0) + (self.category_b_percentage or 0) + (self.category_c_percentage or 0)
        if abs(total - 100.0) > 0.01:  # Allow small floating point differences
            frappe.throw(_("مجموع نسب الفئات يجب أن يساوي 100%. المجموع الحالي: {0}%").format(total))
    
    def validate_analysis_period(self):
        """Validate analysis period configuration"""
        valid_periods = ["Last 3 Months", "Last 6 Months", "Last 12 Months", "Custom Period"]
        if self.analysis_period and self.analysis_period not in valid_periods:
            frappe.throw(_("فترة التحليل غير صحيحة"))
    
    def run_abc_analysis(self):
        """Run ABC analysis based on configuration"""
        try:
            # Get analysis data
            analysis_data = self.get_analysis_data()
            
            if not analysis_data:
                frappe.msgprint(_("لا توجد بيانات للتحليل"), indicator="orange")
                return
            
            # Calculate ABC categories
            categorized_items = self.calculate_abc_categories(analysis_data)
            
            # Update results
            self.update_analysis_results(categorized_items)
            
            # Generate recommendations
            self.generate_recommendations(categorized_items)
            
            frappe.msgprint(_("تم إكمال تحليل ABC بنجاح"))
            
        except Exception as e:
            frappe.log_error(f"Error running ABC analysis: {e}")
            frappe.throw(_("خطأ في تشغيل تحليل ABC"))
    
    def get_analysis_data(self):
        """Get item data for analysis based on calculation method"""
        period_condition = self.get_period_condition()
        
        if self.calculation_method == "Value Based":
            return self.get_value_based_data(period_condition)
        elif self.calculation_method == "Usage Based":
            return self.get_usage_based_data(period_condition)
        else:  # Combined Value+Usage
            return self.get_combined_data(period_condition)
    
    def get_period_condition(self):
        """Get date condition based on analysis period"""
        today = datetime.now()
        
        if self.analysis_period == "Last 3 Months":
            start_date = today - timedelta(days=90)
        elif self.analysis_period == "Last 6 Months":
            start_date = today - timedelta(days=180)
        elif self.analysis_period == "Last 12 Months":
            start_date = today - timedelta(days=365)
        else:
            # Custom period - you can add custom date fields if needed
            start_date = today - timedelta(days=365)
        
        return f"'{start_date.strftime('%Y-%m-%d')}'"
    
    def get_value_based_data(self, period_condition):
        """Get value-based analysis data"""
        return frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.standard_rate,
                COALESCE(SUM(b.actual_qty), 0) as current_stock,
                (i.standard_rate * COALESCE(SUM(b.actual_qty), 0)) as total_value
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            GROUP BY i.name, i.item_name, i.standard_rate
            HAVING total_value > 0
            ORDER BY total_value DESC
        """, as_dict=True)
    
    def get_usage_based_data(self, period_condition):
        """Get usage-based analysis data"""
        return frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.standard_rate,
                COALESCE(SUM(b.actual_qty), 0) as current_stock,
                COALESCE(SUM(ABS(si.qty)), 0) as usage_qty,
                (i.standard_rate * COALESCE(SUM(ABS(si.qty)), 0)) as usage_value
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            LEFT JOIN `tabStock Ledger Entry` si ON i.name = si.item_code 
                AND si.posting_date >= %s
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            GROUP BY i.name, i.item_name, i.standard_rate
            HAVING usage_value > 0
            ORDER BY usage_value DESC
        """, (self.get_period_condition().strip("'"),), as_dict=True)
    
    def get_combined_data(self, period_condition):
        """Get combined value and usage analysis data"""
        return frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.standard_rate,
                COALESCE(SUM(b.actual_qty), 0) as current_stock,
                COALESCE(SUM(ABS(si.qty)), 0) as usage_qty,
                (i.standard_rate * COALESCE(SUM(b.actual_qty), 0)) as stock_value,
                (i.standard_rate * COALESCE(SUM(ABS(si.qty)), 0)) as usage_value,
                ((i.standard_rate * COALESCE(SUM(b.actual_qty), 0)) + 
                 (i.standard_rate * COALESCE(SUM(ABS(si.qty)), 0))) as combined_value
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            LEFT JOIN `tabStock Ledger Entry` si ON i.name = si.item_code 
                AND si.posting_date >= %s
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            GROUP BY i.name, i.item_name, i.standard_rate
            HAVING combined_value > 0
            ORDER BY combined_value DESC
        """, (self.get_period_condition().strip("'"),), as_dict=True)
    
    def calculate_abc_categories(self, analysis_data):
        """Calculate ABC categories based on data"""
        if not analysis_data:
            return {}
        
        # Calculate total value
        total_value = sum(item.get('total_value', item.get('usage_value', item.get('combined_value', 0))) 
                         for item in analysis_data)
        
        if total_value == 0:
            return {}
        
        # Calculate cumulative percentages
        cumulative_value = 0
        categorized_items = {
            'A': [],
            'B': [],
            'C': []
        }
        
        for item in analysis_data:
            item_value = item.get('total_value', item.get('usage_value', item.get('combined_value', 0)))
            cumulative_value += item_value
            cumulative_percentage = (cumulative_value / total_value) * 100
            
            # Categorize based on cumulative percentage
            if cumulative_percentage <= self.category_a_percentage:
                category = 'A'
            elif cumulative_percentage <= (self.category_a_percentage + self.category_b_percentage):
                category = 'B'
            else:
                category = 'C'
            
            item['category'] = category
            item['cumulative_percentage'] = cumulative_percentage
            categorized_items[category].append(item)
        
        return categorized_items
    
    def update_analysis_results(self, categorized_items):
        """Update analysis results with calculated data"""
        total_items = sum(len(items) for items in categorized_items.values())
        total_value = sum(
            sum(item.get('total_value', item.get('usage_value', item.get('combined_value', 0))) 
                for item in items)
            for items in categorized_items.values()
        )
        
        self.total_items_analyzed = total_items
        self.total_value_analyzed = total_value
        
        # Category A results
        category_a_items = categorized_items.get('A', [])
        self.category_a_items = len(category_a_items)
        self.category_a_value = sum(item.get('total_value', item.get('usage_value', item.get('combined_value', 0))) 
                                   for item in category_a_items)
        self.category_a_percentage_actual = (self.category_a_value / total_value * 100) if total_value > 0 else 0
        
        # Category B results
        category_b_items = categorized_items.get('B', [])
        self.category_b_items = len(category_b_items)
        self.category_b_value = sum(item.get('total_value', item.get('usage_value', item.get('combined_value', 0))) 
                                   for item in category_b_items)
        self.category_b_percentage_actual = (self.category_b_value / total_value * 100) if total_value > 0 else 0
        
        # Category C results
        category_c_items = categorized_items.get('C', [])
        self.category_c_items = len(category_c_items)
        self.category_c_value = sum(item.get('total_value', item.get('usage_value', item.get('combined_value', 0))) 
                                   for item in category_c_items)
        self.category_c_percentage_actual = (self.category_c_value / total_value * 100) if total_value > 0 else 0
    
    def generate_recommendations(self, categorized_items):
        """Generate recommendations for each category"""
        # Category A recommendations
        self.category_a_recommendation = _("""
        Category A Items (High Value):
        - Implement strict inventory control
        - Regular stock monitoring
        - Optimize reorder points
        - Consider vendor managed inventory
        - High priority for stock accuracy
        """)
        
        self.category_a_recommendation_ar = _("""
        فئة أ (عالي القيمة):
        - تطبيق رقابة صارمة على المخزون
        - مراقبة المخزون بانتظام
        - تحسين نقاط إعادة الطلب
        - النظر في إدارة المخزون من قبل المورد
        - أولوية عالية لدقة المخزون
        """)
        
        # Category B recommendations
        self.category_b_recommendation = _("""
        Category B Items (Medium Value):
        - Moderate inventory control
        - Periodic stock reviews
        - Standard reorder procedures
        - Monitor for category changes
        """)
        
        self.category_b_recommendation_ar = _("""
        فئة ب (متوسط القيمة):
        - رقابة معتدلة على المخزون
        - مراجعات دورية للمخزون
        - إجراءات إعادة طلب قياسية
        - مراقبة التغييرات في الفئة
        """)
        
        # Category C recommendations
        self.category_c_recommendation = _("""
        Category C Items (Low Value):
        - Simplified inventory control
        - Bulk ordering strategies
        - Consider consignment stock
        - Minimize handling costs
        """)
        
        self.category_c_recommendation_ar = _("""
        فئة ج (منخفض القيمة):
        - رقابة مبسطة على المخزون
        - استراتيجيات الطلب بالجملة
        - النظر في المخزون بالعمولة
        - تقليل تكاليف المعالجة
        """)
    
    @frappe.whitelist()
    def get_analysis_summary(self):
        """Get analysis summary for dashboard"""
        return {
            'total_items': self.total_items_analyzed or 0,
            'total_value': self.total_value_analyzed or 0,
            'category_a': {
                'items': self.category_a_items or 0,
                'value': self.category_a_value or 0,
                'percentage': self.category_a_percentage_actual or 0
            },
            'category_b': {
                'items': self.category_b_items or 0,
                'value': self.category_b_value or 0,
                'percentage': self.category_b_percentage_actual or 0
            },
            'category_c': {
                'items': self.category_c_items or 0,
                'value': self.category_c_value or 0,
                'percentage': self.category_c_percentage_actual or 0
            }
        } 