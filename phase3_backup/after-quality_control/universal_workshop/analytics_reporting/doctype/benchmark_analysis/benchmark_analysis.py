# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

class BenchmarkAnalysis(Document):
    """
    Benchmark Analysis DocType for comparing workshop performance metrics 
    against industry standards, internal targets, and peer benchmarks.
    Supports Arabic localization and comprehensive statistical analysis.
    """
    
    def validate(self):
        """Validate benchmark analysis configuration"""
        self.validate_basic_info()
        self.validate_targets()
        self.validate_kpi_reference()
        self.validate_calculation_config()
        self.calculate_derived_metrics()
        
    def before_save(self):
        """Set default values and perform calculations before saving"""
        self.set_metadata()
        self.update_performance_scores()
        self.generate_insights()
        
    def validate_basic_info(self):
        """Validate basic benchmark information"""
        if not self.benchmark_name:
            frappe.throw(_("Benchmark name is required"))
            
        if not self.business_area:
            frappe.throw(_("Business area must be specified"))
            
        if not self.benchmark_type:
            frappe.throw(_("Benchmark type must be selected"))
            
        # Validate Arabic name if RTL display is enabled
        if self.rtl_display and not self.benchmark_name_ar:
            frappe.msgprint(_("Arabic benchmark name is recommended for RTL display"))
            
    def validate_targets(self):
        """Validate comparison targets"""
        targets = [
            self.internal_target,
            self.industry_standard,
            self.peer_average,
            self.historical_baseline,
            self.best_in_class
        ]
        
        # At least one target should be specified
        if not any(target for target in targets):
            frappe.throw(_("At least one comparison target must be specified"))
            
        # Validate target values are positive for applicable metrics
        for target in targets:
            if target is not None and target < 0:
                frappe.msgprint(_("Warning: Negative target values detected"))
                
    def validate_kpi_reference(self):
        """Validate primary KPI reference"""
        if not self.primary_kpi:
            frappe.throw(_("Primary KPI reference is required"))
            
        # Check if KPI exists and is active
        if not frappe.db.exists('Analytics KPI', self.primary_kpi):
            frappe.throw(_("Referenced KPI does not exist"))
            
        kpi_doc = frappe.get_doc('Analytics KPI', self.primary_kpi)
        if not kpi_doc.is_active:
            frappe.throw(_("Referenced KPI is not active"))
            
        # Update current value from KPI if not manually set
        if not self.current_value:
            self.current_value = kpi_doc.current_value
            
    def validate_calculation_config(self):
        """Validate calculation and analysis configuration"""
        # Validate JSON fields
        if self.weights_json:
            try:
                json.loads(self.weights_json)
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in weights configuration"))
                
        if self.alert_thresholds:
            try:
                json.loads(self.alert_thresholds)
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON format in alert thresholds"))
                
        # Validate confidence level
        if self.confidence_level and (self.confidence_level < 0 or self.confidence_level > 100):
            frappe.throw(_("Confidence level must be between 0 and 100"))
            
    def calculate_derived_metrics(self):
        """Calculate derived metrics and scores"""
        if not self.current_value:
            return
            
        # Calculate variance from target
        if self.target_value:
            self.variance = ((self.current_value - self.target_value) / self.target_value) * 100
            
        # Calculate performance score (0-100)
        self.performance_score = self.calculate_performance_score()
        
        # Calculate improvement potential
        self.improvement_potential = self.calculate_improvement_potential()
        
        # Update trend direction
        self.trend_direction = self.determine_trend_direction()
        
        # Calculate stability and volatility scores
        self.stability_score = self.calculate_stability_score()
        self.volatility_index = self.calculate_volatility_index()
        
    def calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        if not self.current_value:
            return 0.0
            
        targets = []
        weights = []
        
        # Define default weights
        default_weights = {
            'internal_target': 0.3,
            'industry_standard': 0.25,
            'peer_average': 0.2,
            'best_in_class': 0.15,
            'historical_baseline': 0.1
        }
        
        # Load custom weights if configured
        if self.weights_json:
            try:
                custom_weights = json.loads(self.weights_json)
                default_weights.update(custom_weights)
            except:
                pass
                
        # Collect available targets with weights
        target_fields = [
            ('internal_target', self.internal_target),
            ('industry_standard', self.industry_standard),
            ('peer_average', self.peer_average),
            ('best_in_class', self.best_in_class),
            ('historical_baseline', self.historical_baseline)
        ]
        
        for field_name, target_value in target_fields:
            if target_value:
                targets.append(target_value)
                weights.append(default_weights.get(field_name, 0.2))
        
        if not targets:
            return 50.0  # Neutral score if no targets
            
        # Calculate weighted score
        total_score = 0.0
        total_weight = sum(weights)
        
        for target, weight in zip(targets, weights):
            if target > 0:
                # Higher is better for most metrics
                score = min((self.current_value / target) * 100, 150)  # Cap at 150%
                total_score += score * weight
                
        return min(total_score / total_weight, 100.0) if total_weight > 0 else 50.0
        
    def calculate_improvement_potential(self) -> float:
        """Calculate improvement potential percentage"""
        if not self.best_in_class or not self.current_value:
            return 0.0
            
        if self.current_value >= self.best_in_class:
            return 0.0  # Already at best in class
            
        return ((self.best_in_class - self.current_value) / self.current_value) * 100
        
    def determine_trend_direction(self) -> str:
        """Determine trend direction based on historical data"""
        if not self.primary_kpi:
            return "Stable"
            
        # Get historical KPI values
        history = frappe.get_list('Analytics KPI History',
                                filters={'kpi_code': self.primary_kpi},
                                fields=['current_value', 'recorded_date'],
                                order_by='recorded_date desc',
                                limit=10)
        
        if len(history) < 3:
            return "Stable"
            
        values = [h.current_value for h in history if h.current_value]
        if len(values) < 3:
            return "Stable"
            
        # Calculate trend using linear regression
        try:
            n = len(values)
            x_values = list(range(n))
            
            # Calculate slope
            x_mean = sum(x_values) / n
            y_mean = sum(values) / n
            
            numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return "Stable"
                
            slope = numerator / denominator
            
            # Determine trend direction
            if slope > 0.1:
                return "Improving"
            elif slope < -0.1:
                return "Declining"
            else:
                return "Stable"
                
        except:
            return "Stable"
            
    def calculate_stability_score(self) -> float:
        """Calculate performance stability score"""
        if not self.primary_kpi:
            return 50.0
            
        # Get recent historical values
        history = frappe.get_list('Analytics KPI History',
                                filters={'kpi_code': self.primary_kpi},
                                fields=['current_value'],
                                order_by='recorded_date desc',
                                limit=20)
        
        values = [h.current_value for h in history if h.current_value is not None]
        
        if len(values) < 5:
            return 50.0  # Insufficient data
            
        try:
            # Calculate coefficient of variation
            mean_val = statistics.mean(values)
            std_dev = statistics.stdev(values)
            
            if mean_val == 0:
                return 0.0
                
            cv = (std_dev / mean_val) * 100
            
            # Convert to stability score (lower CV = higher stability)
            stability = max(0, 100 - cv)
            return min(stability, 100.0)
            
        except:
            return 50.0
            
    def calculate_volatility_index(self) -> float:
        """Calculate volatility index"""
        if not self.stability_score:
            return 50.0
            
        # Volatility is inverse of stability
        return 100.0 - self.stability_score
        
    def set_metadata(self):
        """Set metadata fields"""
        if not self.created_by:
            self.created_by = frappe.session.user
            
        self.modified_by = frappe.session.user
        self.last_updated = frappe.utils.now()
        
        # Set regional standards based on location
        if not self.regional_standards:
            self.regional_standards = "Oman Standards"
            
    def update_performance_scores(self):
        """Update all performance-related scores"""
        # Data quality assessment
        self.data_quality_score = self.assess_data_quality()
        
        # Update growth rate
        self.growth_rate = self.calculate_growth_rate()
        
    def assess_data_quality(self) -> float:
        """Assess data quality score"""
        score = 100.0
        
        # Check data completeness
        required_fields = [self.current_value, self.target_value, self.primary_kpi]
        missing_fields = sum(1 for field in required_fields if not field)
        score -= (missing_fields * 15)  # 15 points per missing field
        
        # Check data recency
        if self.last_updated:
            days_old = (datetime.now() - self.last_updated).days
            if days_old > 7:
                score -= min(days_old * 2, 30)  # Max 30 points deduction
                
        # Check confidence level
        if self.confidence_level and self.confidence_level < 80:
            score -= (80 - self.confidence_level) / 2
            
        return max(score, 0.0)
        
    def calculate_growth_rate(self) -> float:
        """Calculate period-over-period growth rate"""
        if not self.current_value or not self.primary_kpi:
            return 0.0
            
        # Get previous period value
        period_mapping = {
            'Month over Month': 30,
            'Quarter over Quarter': 90,
            'Year over Year': 365,
            'Custom Period': 30
        }
        
        days_back = period_mapping.get(self.period_comparison, 30)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        previous_value = frappe.db.get_value('Analytics KPI History',
                                           filters={
                                               'kpi_code': self.primary_kpi,
                                               'recorded_date': ['<=', cutoff_date]
                                           },
                                           fieldname='current_value',
                                           order_by='recorded_date desc')
        
        if not previous_value or previous_value == 0:
            return 0.0
            
        return ((self.current_value - previous_value) / previous_value) * 100
        
    def generate_insights(self):
        """Generate automatic insights and recommendations"""
        insights = []
        recommendations = []
        actions = []
        
        # Performance analysis
        if self.performance_score:
            if self.performance_score >= 80:
                insights.append("Performance is excellent and exceeds most benchmarks.")
                recommendations.append("Maintain current practices and share best practices with other departments.")
            elif self.performance_score >= 60:
                insights.append("Performance is good but has room for improvement.")
                recommendations.append("Focus on closing gaps with industry leaders.")
            else:
                insights.append("Performance is below expectations and requires immediate attention.")
                recommendations.append("Implement urgent improvement initiatives.")
                actions.append("Schedule performance review meeting within 1 week")
                
        # Trend analysis
        if self.trend_direction:
            if self.trend_direction == "Improving":
                insights.append("Positive trend indicates effective improvement efforts.")
            elif self.trend_direction == "Declining":
                insights.append("Declining trend requires immediate investigation.")
                actions.append("Investigate root causes of performance decline")
            elif self.trend_direction == "Volatile":
                insights.append("High volatility suggests inconsistent processes.")
                recommendations.append("Standardize processes to reduce variability.")
                
        # Gap analysis
        gaps = []
        if self.industry_standard and self.current_value < self.industry_standard:
            gap = self.industry_standard - self.current_value
            gaps.append(f"Gap vs industry standard: {gap:.2f}")
            
        if self.best_in_class and self.current_value < self.best_in_class:
            gap = self.best_in_class - self.current_value
            gaps.append(f"Gap vs best in class: {gap:.2f}")
            
        # Update fields
        if insights:
            self.performance_summary = "<br>".join(insights)
            
        if gaps:
            self.gap_analysis = "<br>".join(gaps)
            
        if recommendations:
            self.recommendations = "<br>".join(recommendations)
            
        if actions:
            self.action_items = "<br>".join(actions)
            
    def get_comparison_data(self) -> Dict[str, Any]:
        """Get comprehensive comparison data for visualization"""
        comparison_data = {
            'current_value': self.current_value,
            'targets': {},
            'scores': {},
            'trends': {},
            'metadata': {}
        }
        
        # Target comparisons
        if self.internal_target:
            comparison_data['targets']['internal'] = self.internal_target
        if self.industry_standard:
            comparison_data['targets']['industry'] = self.industry_standard
        if self.peer_average:
            comparison_data['targets']['peer'] = self.peer_average
        if self.best_in_class:
            comparison_data['targets']['best_in_class'] = self.best_in_class
        if self.historical_baseline:
            comparison_data['targets']['historical'] = self.historical_baseline
            
        # Performance scores
        comparison_data['scores'] = {
            'performance': self.performance_score,
            'stability': self.stability_score,
            'data_quality': self.data_quality_score,
            'improvement_potential': self.improvement_potential
        }
        
        # Trend data
        comparison_data['trends'] = {
            'direction': self.trend_direction,
            'growth_rate': self.growth_rate,
            'volatility': self.volatility_index,
            'variance': self.variance
        }
        
        # Metadata
        comparison_data['metadata'] = {
            'benchmark_type': self.benchmark_type,
            'business_area': self.business_area,
            'analysis_period': self.analysis_period,
            'last_updated': self.last_updated,
            'confidence_level': self.confidence_level
        }
        
        return comparison_data


# WhiteListed API Methods

@frappe.whitelist()
def get_benchmark_dashboard_data(benchmark_name: str) -> Dict[str, Any]:
    """Get benchmark data for dashboard display"""
    
    if not benchmark_name:
        frappe.throw(_("Benchmark name is required"))
        
    benchmark = frappe.get_doc('Benchmark Analysis', benchmark_name)
    
    if not benchmark:
        frappe.throw(_("Benchmark analysis not found"))
        
    return benchmark.get_comparison_data()


@frappe.whitelist()
def create_benchmark_from_kpi(kpi_code: str, benchmark_type: str = "Internal Target") -> str:
    """Create a new benchmark analysis from existing KPI"""
    
    if not kpi_code:
        frappe.throw(_("KPI code is required"))
        
    # Get KPI details
    kpi = frappe.get_doc('Analytics KPI', kpi_code)
    if not kpi:
        frappe.throw(_("KPI not found"))
        
    # Create new benchmark
    benchmark = frappe.new_doc('Benchmark Analysis')
    benchmark.benchmark_name = f"Benchmark - {kpi.kpi_name}"
    benchmark.benchmark_name_ar = f"مقارنة معيارية - {kpi.kpi_name_ar or kpi.kpi_name}"
    benchmark.benchmark_type = benchmark_type
    benchmark.business_area = kpi.kpi_category
    benchmark.primary_kpi = kpi_code
    benchmark.current_value = kpi.current_value
    benchmark.target_value = kpi.target_value
    
    benchmark.insert()
    
    return benchmark.name


@frappe.whitelist()
def get_industry_benchmarks(business_area: str) -> List[Dict[str, Any]]:
    """Get industry benchmark data for specific business area"""
    
    # This would typically connect to external benchmark databases
    # For now, return mock data based on automotive workshop standards
    
    industry_standards = {
        'Service Operations': {
            'Service Bay Utilization': 75.0,
            'Average Repair Time': 120.0,  # minutes
            'First Time Fix Rate': 85.0,   # percentage
            'Customer Satisfaction': 4.2   # out of 5
        },
        'Financial Performance': {
            'Revenue per Service Order': 250.0,  # OMR
            'Gross Margin': 35.0,               # percentage
            'Parts Inventory Turnover': 8.0     # times per year
        },
        'Technician Productivity': {
            'Billable Hours Ratio': 80.0,       # percentage
            'Training Hours per Month': 8.0,    # hours
            'Certification Level': 3.5          # out of 5
        }
    }
    
    return industry_standards.get(business_area, {})


@frappe.whitelist()
def export_benchmark_report(benchmark_name: str, format_type: str = "PDF") -> str:
    """Export benchmark analysis report"""
    
    benchmark = frappe.get_doc('Benchmark Analysis', benchmark_name)
    if not benchmark:
        frappe.throw(_("Benchmark analysis not found"))
        
    # Generate report based on format
    if format_type.upper() == "PDF":
        return generate_pdf_report(benchmark)
    elif format_type.upper() == "EXCEL":
        return generate_excel_report(benchmark)
    else:
        frappe.throw(_("Unsupported export format"))


def generate_pdf_report(benchmark) -> str:
    """Generate PDF report for benchmark analysis"""
    # Implementation would use frappe.utils.pdf or external PDF generation
    # For now, return placeholder
    return "PDF report generated successfully"


def generate_excel_report(benchmark) -> str:
    """Generate Excel report for benchmark analysis"""
    # Implementation would use openpyxl or similar library
    # For now, return placeholder
    return "Excel report generated successfully"
