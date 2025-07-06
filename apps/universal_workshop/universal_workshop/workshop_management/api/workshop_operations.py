# -*- coding: utf-8 -*-
"""
Workshop Operations API - Standardized Workshop Management Endpoints
====================================================================

This module provides standardized workshop operations API endpoints with comprehensive
Arabic support, cultural validation, and traditional workshop management patterns
for Universal Workshop ERP system.

Features:
- Standardized service order management with Arabic business context
- Workshop profile management with cultural validation
- Technician management with Islamic business principles
- Quality control management with traditional patterns
- Workshop analytics with Arabic business intelligence

Author: Universal Workshop Development Team
Version: 3.0 (Phase 3 - Backend Rebuild)
Arabic Support: Native RTL and cultural workshop patterns
Cultural Context: Traditional Arabic workshop excellence with Islamic principles
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, now, get_datetime
from typing import Dict, List, Any, Optional

# Import shared libraries for standardized patterns
from ...shared_libraries.api_standards.arabic_api_patterns import (
    traditional_service_pattern,
    arabic_business_intelligence_pattern
)
from ...shared_libraries.api_standards.response_utils import (
    success, error, validation_error
)
from ...shared_libraries.workshop_operations.service_order_management import (
    ServiceOrderManager
)
from ...shared_libraries.workshop_operations.technician_management import (
    TechnicianManager
)
from ...shared_libraries.workshop_operations.quality_control import (
    QualityControlManager
)

class WorkshopOperationsAPI:
    """
    Standardized workshop operations API with Arabic cultural excellence
    """
    
    def __init__(self):
        """Initialize workshop operations API with cultural context"""
        self.service_order_manager = ServiceOrderManager()
        self.technician_manager = TechnicianManager()
        self.quality_control_manager = QualityControlManager()
        self.arabic_support = True
        self.islamic_compliance = True

@frappe.whitelist()
def get_service_orders(
    filters: Dict = None,
    page_length: int = 20,
    page_start: int = 0,
    order_by: str = "modified desc",
    arabic_context: bool = True,
    cultural_validation: bool = True
) -> Dict:
    """
    Get service orders with Arabic cultural context and traditional workshop patterns
    
    Args:
        filters: Service order filters
        page_length: Number of records per page
        page_start: Starting record for pagination
        order_by: Sort order
        arabic_context: Include Arabic cultural context
        cultural_validation: Enable cultural validation
        
    Returns:
        Standardized API response with service orders and Arabic context
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Get service orders with cultural context
        service_orders = api.service_order_manager.get_service_orders_with_cultural_context(
            filters=filters or {},
            page_length=page_length,
            page_start=page_start,
            order_by=order_by,
            arabic_context=arabic_context
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "workshop_approach": "traditional_arabic_excellence",
            "service_quality_standard": "exceptional_arabic_hospitality",
            "customer_care_level": "premium_traditional_service"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=service_orders,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "service_excellence": "exceptional_standard_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Get Service Orders Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to retrieve service orders",
            arabic_message="فشل في استرداد أوامر الخدمة",
            error_code="WORKSHOP_SERVICE_ORDERS_ERROR"
        )

@frappe.whitelist()
def create_service_order(
    customer: str,
    vehicle: str,
    service_type: str,
    arabic_description: str = None,
    cultural_preferences: Dict = None,
    traditional_patterns: bool = True
) -> Dict:
    """
    Create service order with Arabic cultural validation and traditional patterns
    
    Args:
        customer: Customer ID
        vehicle: Vehicle ID  
        service_type: Type of service
        arabic_description: Service description in Arabic
        cultural_preferences: Customer cultural preferences
        traditional_patterns: Apply traditional workshop patterns
        
    Returns:
        Standardized API response with created service order
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Validate cultural context
        if not customer or not vehicle or not service_type:
            return validation_error(
                validation_errors={
                    "customer": "Customer is required",
                    "vehicle": "Vehicle is required", 
                    "service_type": "Service type is required"
                },
                arabic_validation_errors={
                    "customer": "العميل مطلوب",
                    "vehicle": "المركبة مطلوبة",
                    "service_type": "نوع الخدمة مطلوب"
                }
            )
        
        # Create service order with cultural context
        service_order_data = {
            "customer": customer,
            "vehicle": vehicle,
            "service_type": service_type,
            "arabic_description": arabic_description,
            "cultural_preferences": cultural_preferences or {},
            "traditional_patterns_applied": traditional_patterns,
            "islamic_business_compliance": True,
            "arabic_workflow_enabled": True
        }
        
        # Create service order through manager
        created_order = api.service_order_manager.create_service_order_with_cultural_validation(
            service_order_data=service_order_data,
            cultural_validation=True
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "service_creation_approach": "traditional_arabic_excellence",
            "customer_interaction_style": "respectful_arabic_hospitality",
            "quality_assurance_level": "exceptional_cultural_standards"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=created_order,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "service_excellence": "exceptional_standard_achieved"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Create Service Order Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to create service order",
            arabic_message="فشل في إنشاء أمر الخدمة",
            error_code="WORKSHOP_CREATE_SERVICE_ORDER_ERROR"
        )

@frappe.whitelist()
def update_service_order_status(
    service_order: str,
    new_status: str,
    arabic_notes: str = None,
    technician_comments: str = None,
    cultural_validation: bool = True
) -> Dict:
    """
    Update service order status with Arabic cultural context and traditional patterns
    
    Args:
        service_order: Service order ID
        new_status: New status for service order
        arabic_notes: Status update notes in Arabic
        technician_comments: Technician comments
        cultural_validation: Enable cultural validation
        
    Returns:
        Standardized API response with updated service order
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Validate inputs
        if not service_order or not new_status:
            return validation_error(
                validation_errors={
                    "service_order": "Service order ID is required",
                    "new_status": "New status is required"
                },
                arabic_validation_errors={
                    "service_order": "معرف أمر الخدمة مطلوب", 
                    "new_status": "الحالة الجديدة مطلوبة"
                }
            )
        
        # Update service order status with cultural context
        status_update_data = {
            "service_order": service_order,
            "new_status": new_status,
            "arabic_notes": arabic_notes,
            "technician_comments": technician_comments,
            "cultural_validation_applied": cultural_validation,
            "traditional_workflow_followed": True,
            "islamic_business_principles_maintained": True
        }
        
        # Update through manager
        updated_order = api.service_order_manager.update_service_order_status_with_cultural_context(
            status_update_data=status_update_data,
            cultural_validation=cultural_validation
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "status_update_approach": "traditional_arabic_transparency",
            "customer_communication_style": "respectful_arabic_updates",
            "quality_tracking_level": "meticulous_cultural_monitoring"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=updated_order,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "service_excellence": "exceptional_standard_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Update Service Order Status Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to update service order status",
            arabic_message="فشل في تحديث حالة أمر الخدمة",
            error_code="WORKSHOP_UPDATE_STATUS_ERROR"
        )

@frappe.whitelist()
def get_technicians(
    filters: Dict = None,
    include_skills: bool = True,
    include_performance: bool = True,
    arabic_context: bool = True,
    islamic_compliance_check: bool = True
) -> Dict:
    """
    Get technicians with skills and performance data including Arabic cultural context
    
    Args:
        filters: Technician filters
        include_skills: Include technician skills
        include_performance: Include performance metrics
        arabic_context: Include Arabic cultural context
        islamic_compliance_check: Apply Islamic business compliance
        
    Returns:
        Standardized API response with technicians and Arabic context
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Get technicians with cultural context
        technicians = api.technician_manager.get_technicians_with_cultural_context(
            filters=filters or {},
            include_skills=include_skills,
            include_performance=include_performance,
            arabic_context=arabic_context,
            islamic_compliance_check=islamic_compliance_check
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "technician_management_approach": "traditional_arabic_respect",
            "skill_development_focus": "islamic_work_excellence",
            "performance_evaluation_style": "fair_traditional_assessment"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=technicians,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "islamic_work_principles": "islamic_excellence_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Get Technicians Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to retrieve technicians",
            arabic_message="فشل في استرداد الفنيين",
            error_code="WORKSHOP_TECHNICIANS_ERROR"
        )

@frappe.whitelist()
def assign_technician_to_service(
    service_order: str,
    technician: str,
    estimated_hours: float = None,
    arabic_instructions: str = None,
    cultural_considerations: Dict = None
) -> Dict:
    """
    Assign technician to service order with Arabic cultural validation
    
    Args:
        service_order: Service order ID
        technician: Technician ID
        estimated_hours: Estimated completion hours
        arabic_instructions: Instructions in Arabic
        cultural_considerations: Cultural considerations for assignment
        
    Returns:
        Standardized API response with assignment details
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Validate inputs
        if not service_order or not technician:
            return validation_error(
                validation_errors={
                    "service_order": "Service order ID is required",
                    "technician": "Technician ID is required"
                },
                arabic_validation_errors={
                    "service_order": "معرف أمر الخدمة مطلوب",
                    "technician": "معرف الفني مطلوب"
                }
            )
        
        # Create assignment with cultural context
        assignment_data = {
            "service_order": service_order,
            "technician": technician,
            "estimated_hours": estimated_hours,
            "arabic_instructions": arabic_instructions,
            "cultural_considerations": cultural_considerations or {},
            "traditional_assignment_patterns": True,
            "islamic_work_principles": True
        }
        
        # Assign through manager
        assignment = api.technician_manager.assign_technician_with_cultural_context(
            assignment_data=assignment_data,
            cultural_validation=True
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "assignment_approach": "traditional_arabic_skill_matching",
            "work_allocation_style": "islamic_fair_distribution",
            "performance_expectations": "excellence_with_cultural_respect"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=assignment,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "islamic_work_principles": "islamic_excellence_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Assign Technician Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to assign technician",
            arabic_message="فشل في تعيين الفني",
            error_code="WORKSHOP_ASSIGN_TECHNICIAN_ERROR"
        )

@frappe.whitelist()
def get_quality_control_checklist(
    service_order: str,
    checklist_type: str = "standard",
    arabic_context: bool = True,
    cultural_validation: bool = True
) -> Dict:
    """
    Get quality control checklist for service order with Arabic cultural patterns
    
    Args:
        service_order: Service order ID
        checklist_type: Type of quality checklist
        arabic_context: Include Arabic cultural context
        cultural_validation: Enable cultural validation
        
    Returns:
        Standardized API response with quality control checklist
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Validate inputs
        if not service_order:
            return validation_error(
                validation_errors={"service_order": "Service order ID is required"},
                arabic_validation_errors={"service_order": "معرف أمر الخدمة مطلوب"}
            )
        
        # Get quality control checklist with cultural context
        checklist = api.quality_control_manager.get_quality_checklist_with_cultural_context(
            service_order=service_order,
            checklist_type=checklist_type,
            arabic_context=arabic_context,
            cultural_validation=cultural_validation
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "quality_approach": "traditional_arabic_excellence",
            "inspection_standards": "meticulous_cultural_attention",
            "customer_satisfaction_focus": "exceptional_arabic_hospitality"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=checklist,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "quality_excellence": "exceptional_standard_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Get Quality Checklist Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to retrieve quality control checklist",
            arabic_message="فشل في استرداد قائمة مراقبة الجودة",
            error_code="WORKSHOP_QUALITY_CHECKLIST_ERROR"
        )

@frappe.whitelist()
def get_workshop_analytics(
    date_range: Dict = None,
    analytics_type: str = "overview",
    arabic_context: bool = True,
    traditional_metrics: bool = True,
    cultural_insights: bool = True
) -> Dict:
    """
    Get workshop analytics with Arabic business intelligence and cultural insights
    
    Args:
        date_range: Date range for analytics
        analytics_type: Type of analytics (overview, performance, quality)
        arabic_context: Include Arabic cultural context
        traditional_metrics: Include traditional business metrics
        cultural_insights: Include cultural business insights
        
    Returns:
        Arabic business intelligence response with workshop analytics
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Get workshop analytics with cultural context
        analytics_data = api.service_order_manager.get_workshop_analytics_with_cultural_context(
            date_range=date_range or {},
            analytics_type=analytics_type,
            arabic_context=arabic_context,
            traditional_metrics=traditional_metrics
        )
        
        # Prepare cultural insights
        cultural_insights_data = {
            "customer_satisfaction_cultural": "traditional_arabic_excellence_metrics",
            "service_quality_patterns": "arabic_hospitality_standards",
            "technician_performance_cultural": "islamic_work_excellence_indicators",
            "business_growth_traditional": "sustainable_halal_growth_patterns"
        }
        
        # Prepare traditional metrics
        traditional_metrics_data = {
            "service_excellence_metrics": "arabic_hospitality_benchmarks",
            "customer_relationship_indicators": "traditional_loyalty_patterns",
            "quality_assurance_measures": "cultural_excellence_standards"
        }
        
        # Apply Arabic business intelligence pattern
        return arabic_business_intelligence_pattern(
            analytics_data=analytics_data,
            cultural_insights=cultural_insights_data,
            traditional_metrics=traditional_metrics_data
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Get Analytics Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to retrieve workshop analytics",
            arabic_message="فشل في استرداد تحليلات الورشة",
            error_code="WORKSHOP_ANALYTICS_ERROR"
        )

@frappe.whitelist()
def get_workshop_performance_summary(
    technician: str = None,
    service_bay: str = None,
    date_range: Dict = None,
    arabic_context: bool = True,
    cultural_validation: bool = True
) -> Dict:
    """
    Get workshop performance summary with Arabic cultural context and traditional patterns
    
    Args:
        technician: Specific technician ID (optional)
        service_bay: Specific service bay ID (optional)
        date_range: Date range for performance analysis
        arabic_context: Include Arabic cultural context
        cultural_validation: Enable cultural validation
        
    Returns:
        Standardized API response with performance summary and Arabic context
    """
    try:
        # Initialize API handler
        api = WorkshopOperationsAPI()
        
        # Get performance summary with cultural context
        performance_summary = api.service_order_manager.get_performance_summary_with_cultural_context(
            technician=technician,
            service_bay=service_bay,
            date_range=date_range or {},
            arabic_context=arabic_context,
            cultural_validation=cultural_validation
        )
        
        # Prepare cultural service context
        cultural_service_context = {
            "performance_evaluation_approach": "traditional_arabic_fairness",
            "excellence_measurement_style": "islamic_work_ethics_aligned",
            "improvement_guidance_method": "respectful_cultural_development"
        }
        
        # Apply traditional service pattern
        return traditional_service_pattern(
            service_data=performance_summary,
            cultural_service_context=cultural_service_context,
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "performance_excellence": "islamic_work_standards_maintained"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Workshop Operations API - Get Performance Summary Error: {str(e)}")
        return error(
            errors=[str(e)],
            message="Failed to retrieve workshop performance summary",
            arabic_message="فشل في استرداد ملخص أداء الورشة",
            error_code="WORKSHOP_PERFORMANCE_SUMMARY_ERROR"
        )

# API Endpoint Registration
workshop_operations_endpoints = {
    "get_service_orders": get_service_orders,
    "create_service_order": create_service_order,
    "update_service_order_status": update_service_order_status,
    "get_technicians": get_technicians,
    "assign_technician_to_service": assign_technician_to_service,
    "get_quality_control_checklist": get_quality_control_checklist,
    "get_workshop_analytics": get_workshop_analytics,
    "get_workshop_performance_summary": get_workshop_performance_summary
}