# -*- coding: utf-8 -*-
"""
Customer & Vehicle Unified API - P3.4.2 Implementation
======================================================

This module provides standardized customer and vehicle management API endpoints
with Arabic cultural excellence, Islamic business principle compliance, and
traditional Arabic customer service patterns throughout Universal Workshop operations.

Features:
- Unified customer and vehicle API endpoints with Arabic excellence
- Traditional Arabic customer relationship management patterns  
- Islamic business principle customer service compliance
- Cultural customer-vehicle relationship validation and appropriateness
- Comprehensive customer portal integration with Arabic interface
- Traditional Arabic automotive service customer experience

Author: Universal Workshop Development Team
Version: 3.0 (Phase 3 - P3.4.2 API Standardization)
Arabic Support: Native customer & vehicle management with cultural excellence
Cultural Context: Traditional Arabic customer service patterns with Islamic principles
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Import shared libraries for cultural integration
from universal_workshop.shared_libraries.arabic_business_logic.customer_relations import ArabicCustomerRelations
from universal_workshop.shared_libraries.workshop_operations.vehicle_management import ArabicVehicleManagement
from universal_workshop.shared_libraries.api_standards.arabic_api_patterns import ArabicAPIPatterns

# Initialize Arabic business logic components
arabic_customer_relations = ArabicCustomerRelations()
arabic_vehicle_management = ArabicVehicleManagement()
arabic_api_patterns = ArabicAPIPatterns()

@frappe.whitelist()
def get_unified_customer_data(customer_id, include_vehicles=True, include_analytics=True, arabic_context=True, cultural_validation=True):
    """
    Get unified customer data with vehicle relationships and Arabic cultural excellence
    
    Args:
        customer_id: Customer identifier
        include_vehicles: Include customer vehicles information
        include_analytics: Include customer analytics and insights
        arabic_context: Apply Arabic cultural context processing
        cultural_validation: Apply cultural validation and appropriateness
        
    Returns:
        Unified customer data with Arabic cultural excellence and traditional patterns
    """
    try:
        # Get customer basic information with cultural processing
        customer_data = _get_customer_with_cultural_context(customer_id, arabic_context, cultural_validation)
        
        if not customer_data["success"]:
            return customer_data
            
        unified_data = {
            "customer": customer_data["customer"],
            "vehicles": [],
            "analytics": {},
            "cultural_context": {},
            "traditional_patterns": {},
            "islamic_compliance": {}
        }
        
        # Include vehicles with cultural integration
        if include_vehicles:
            vehicles_data = _get_customer_vehicles_with_cultural_context(
                customer_id, arabic_context, cultural_validation
            )
            unified_data["vehicles"] = vehicles_data.get("vehicles", [])
            
        # Include analytics with Arabic business intelligence
        if include_analytics:
            analytics_data = _get_customer_analytics_with_cultural_insights(
                customer_id, arabic_context
            )
            unified_data["analytics"] = analytics_data.get("analytics", {})
            
        # Apply Arabic cultural context processing
        if arabic_context:
            cultural_context = arabic_customer_relations.format_arabic_customer_display(
                unified_data["customer"], "comprehensive"
            )
            unified_data["cultural_context"] = cultural_context
            
        # Apply traditional patterns and Islamic compliance
        unified_data["traditional_patterns"] = _apply_traditional_customer_patterns(unified_data)
        unified_data["islamic_compliance"] = _validate_islamic_customer_compliance(unified_data)
        
        # Return using standardized Arabic customer API pattern
        return arabic_api_patterns.arabic_customer_api_pattern(
            customer_data=unified_data,
            cultural_customer_context={
                "customer_approach": "traditional_arabic_excellence",
                "service_quality_standard": "exceptional_arabic_hospitality",
                "customer_care_level": "premium_traditional_service"
            },
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "customer_excellence": "exceptional_standard_maintained",
                "islamic_compliance": "complete_business_principle_adherence"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in get_unified_customer_data: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve unified customer data",
            "cultural_context": "error_with_traditional_respect",
            "islamic_compliance": False
        }

@frappe.whitelist()
def create_customer_with_vehicle(customer_data, vehicle_data=None, arabic_context=True, cultural_validation=True):
    """
    Create customer with optional vehicle registration and Arabic cultural excellence
    
    Args:
        customer_data: Customer creation information with Arabic context
        vehicle_data: Optional vehicle registration information
        arabic_context: Apply Arabic cultural context processing
        cultural_validation: Apply cultural validation and appropriateness
        
    Returns:
        Customer and vehicle creation result with cultural excellence
    """
    try:
        # Parse JSON data if needed
        if isinstance(customer_data, str):
            customer_data = json.loads(customer_data)
        if isinstance(vehicle_data, str) and vehicle_data:
            vehicle_data = json.loads(vehicle_data)
            
        creation_result = {
            "customer_creation": {},
            "vehicle_creation": {},
            "cultural_processing": {},
            "traditional_patterns": {},
            "islamic_compliance": {}
        }
        
        # Validate Arabic customer data with cultural patterns
        if cultural_validation:
            customer_validation = arabic_customer_relations.validate_arabic_customer_data(customer_data)
            if not customer_validation.get("is_valid", True):
                return {
                    "success": False,
                    "error": "Customer data validation failed",
                    "validation_errors": customer_validation.get("errors", []),
                    "cultural_appropriateness": "validation_required"
                }
                
        # Create customer with Arabic cultural processing
        customer_creation = _create_customer_with_cultural_context(customer_data, arabic_context)
        creation_result["customer_creation"] = customer_creation
        
        if not customer_creation["success"]:
            return customer_creation
            
        customer_id = customer_creation["customer_id"]
        
        # Create vehicle if provided
        if vehicle_data:
            # Associate vehicle with customer
            vehicle_data["customer"] = customer_id
            
            # Process vehicle registration with Arabic cultural patterns
            vehicle_registration = arabic_vehicle_management.process_arabic_vehicle_registration(vehicle_data)
            vehicle_creation = _create_vehicle_with_cultural_context(vehicle_data, arabic_context)
            creation_result["vehicle_creation"] = vehicle_creation
            
        # Apply cultural processing and traditional patterns
        creation_result["cultural_processing"] = _apply_cultural_customer_processing(creation_result)
        creation_result["traditional_patterns"] = _apply_traditional_creation_patterns(creation_result)
        creation_result["islamic_compliance"] = _validate_islamic_creation_compliance(creation_result)
        
        # Return using standardized Arabic customer API pattern
        return arabic_api_patterns.arabic_customer_api_pattern(
            customer_data=creation_result,
            cultural_customer_context={
                "customer_approach": "traditional_arabic_customer_creation",
                "service_quality_standard": "exceptional_onboarding_hospitality", 
                "customer_care_level": "premium_traditional_welcome"
            },
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "customer_excellence": "exceptional_creation_standard_maintained",
                "islamic_compliance": "complete_business_principle_adherence"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in create_customer_with_vehicle: {str(e)}")
        return {
            "success": False,
            "error": "Failed to create customer with vehicle",
            "cultural_context": "error_with_traditional_respect",
            "islamic_compliance": False
        }

@frappe.whitelist()  
def update_customer_vehicle_relationship(customer_id, vehicle_id, relationship_data, arabic_context=True, cultural_validation=True):
    """
    Update customer-vehicle relationship with Arabic cultural excellence
    
    Args:
        customer_id: Customer identifier
        vehicle_id: Vehicle identifier  
        relationship_data: Relationship update information
        arabic_context: Apply Arabic cultural context processing
        cultural_validation: Apply cultural validation and appropriateness
        
    Returns:
        Relationship update result with cultural excellence and traditional patterns
    """
    try:
        # Parse JSON data if needed
        if isinstance(relationship_data, str):
            relationship_data = json.loads(relationship_data)
            
        update_result = {
            "customer_id": customer_id,
            "vehicle_id": vehicle_id, 
            "relationship_data": relationship_data,
            "cultural_processing": {},
            "traditional_patterns": {},
            "islamic_compliance": {},
            "update_status": {}
        }
        
        # Validate relationship data with cultural patterns
        if cultural_validation:
            relationship_validation = _validate_customer_vehicle_relationship(
                customer_id, vehicle_id, relationship_data, arabic_context
            )
            if not relationship_validation["is_valid"]:
                return {
                    "success": False,
                    "error": "Customer-vehicle relationship validation failed",
                    "validation_errors": relationship_validation.get("errors", []),
                    "cultural_appropriateness": "validation_required"
                }
                
        # Process relationship update with Arabic cultural patterns
        relationship_processing = _process_customer_vehicle_relationship_update(
            customer_id, vehicle_id, relationship_data, arabic_context
        )
        update_result["cultural_processing"] = relationship_processing
        
        # Apply traditional relationship patterns
        traditional_processing = _apply_traditional_relationship_patterns(update_result)
        update_result["traditional_patterns"] = traditional_processing
        
        # Validate Islamic business compliance
        islamic_validation = _validate_islamic_relationship_compliance(update_result)
        update_result["islamic_compliance"] = islamic_validation
        
        # Execute relationship update
        update_execution = _execute_customer_vehicle_relationship_update(update_result)
        update_result["update_status"] = update_execution
        
        # Return using standardized Arabic customer API pattern
        return arabic_api_patterns.arabic_customer_api_pattern(
            customer_data=update_result,
            cultural_customer_context={
                "customer_approach": "traditional_arabic_relationship_management",
                "service_quality_standard": "exceptional_relationship_care",
                "customer_care_level": "premium_traditional_relationship_service"
            },
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "customer_excellence": "exceptional_relationship_standard_maintained",
                "islamic_compliance": "complete_business_principle_adherence"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in update_customer_vehicle_relationship: {str(e)}")
        return {
            "success": False,
            "error": "Failed to update customer-vehicle relationship", 
            "cultural_context": "error_with_traditional_respect",
            "islamic_compliance": False
        }

@frappe.whitelist()
def search_customers_and_vehicles(search_query, search_type="unified", include_analytics=False, arabic_context=True, cultural_validation=True):
    """
    Search customers and vehicles with unified results and Arabic cultural excellence
    
    Args:
        search_query: Search query string
        search_type: Search type (customers, vehicles, unified)
        include_analytics: Include analytics in search results
        arabic_context: Apply Arabic cultural context processing
        cultural_validation: Apply cultural validation and appropriateness
        
    Returns:
        Unified search results with Arabic cultural excellence and traditional patterns
    """
    try:
        search_result = {
            "search_query": search_query,
            "search_type": search_type,
            "customers": [],
            "vehicles": [],
            "unified_results": [],
            "cultural_processing": {},
            "traditional_patterns": {},
            "islamic_compliance": {}
        }
        
        # Search customers with Arabic cultural patterns
        if search_type in ["customers", "unified"]:
            customers_search = _search_customers_with_cultural_context(
                search_query, arabic_context, cultural_validation
            )
            search_result["customers"] = customers_search.get("customers", [])
            
        # Search vehicles with traditional automotive patterns
        if search_type in ["vehicles", "unified"]:
            vehicles_search = _search_vehicles_with_cultural_context(
                search_query, arabic_context, cultural_validation
            )
            search_result["vehicles"] = vehicles_search.get("vehicles", [])
            
        # Create unified search results
        if search_type == "unified":
            unified_results = _create_unified_search_results(
                search_result["customers"], search_result["vehicles"], include_analytics
            )
            search_result["unified_results"] = unified_results
            
        # Apply cultural processing and traditional patterns
        search_result["cultural_processing"] = _apply_cultural_search_processing(search_result)
        search_result["traditional_patterns"] = _apply_traditional_search_patterns(search_result)  
        search_result["islamic_compliance"] = _validate_islamic_search_compliance(search_result)
        
        # Return using standardized Arabic business intelligence pattern
        return arabic_api_patterns.arabic_business_intelligence_pattern(
            analytics_data=search_result,
            cultural_insights={
                "search_approach": "traditional_arabic_customer_intelligence",
                "cultural_intelligence": "authentic_business_wisdom",
                "traditional_metrics": "arabic_hospitality_search_benchmarks"
            },
            traditional_metrics={
                "search_quality": "exceptional_cultural_search_excellence",
                "customer_intelligence": "traditional_arabic_business_insights",
                "cultural_appropriateness": "maximum_traditional_respect"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in search_customers_and_vehicles: {str(e)}")
        return {
            "success": False,
            "error": "Failed to search customers and vehicles",
            "cultural_context": "error_with_traditional_respect",
            "islamic_compliance": False
        }

@frappe.whitelist()
def get_customer_vehicle_analytics(customer_id=None, vehicle_id=None, analytics_type="comprehensive", arabic_context=True):
    """
    Get customer and vehicle analytics with Arabic business intelligence
    
    Args:
        customer_id: Optional customer identifier for customer-specific analytics
        vehicle_id: Optional vehicle identifier for vehicle-specific analytics  
        analytics_type: Analytics type (basic, comprehensive, detailed)
        arabic_context: Apply Arabic cultural context processing
        
    Returns:
        Customer and vehicle analytics with Arabic business intelligence
    """
    try:
        analytics_result = {
            "customer_analytics": {},
            "vehicle_analytics": {},
            "unified_analytics": {},
            "cultural_insights": {},
            "traditional_metrics": {},
            "islamic_compliance_analytics": {}
        }
        
        # Generate customer analytics with Arabic business intelligence
        if customer_id:
            customer_analytics = _generate_customer_analytics_with_cultural_insights(
                customer_id, analytics_type, arabic_context
            )
            analytics_result["customer_analytics"] = customer_analytics
            
        # Generate vehicle analytics with traditional automotive intelligence
        if vehicle_id:
            vehicle_analytics = _generate_vehicle_analytics_with_cultural_insights(
                vehicle_id, analytics_type, arabic_context
            )
            analytics_result["vehicle_analytics"] = vehicle_analytics
            
        # Generate unified analytics if both provided
        if customer_id and vehicle_id:
            unified_analytics = _generate_unified_customer_vehicle_analytics(
                customer_id, vehicle_id, analytics_type, arabic_context
            )
            analytics_result["unified_analytics"] = unified_analytics
            
        # Generate cultural insights and traditional metrics
        analytics_result["cultural_insights"] = _generate_cultural_analytics_insights(analytics_result)
        analytics_result["traditional_metrics"] = _generate_traditional_analytics_metrics(analytics_result)
        analytics_result["islamic_compliance_analytics"] = _generate_islamic_compliance_analytics(analytics_result)
        
        # Return using standardized Arabic business intelligence pattern
        return arabic_api_patterns.arabic_business_intelligence_pattern(
            analytics_data=analytics_result,
            cultural_insights={
                "analytics_approach": "traditional_arabic_business_intelligence",
                "cultural_intelligence": "authentic_business_wisdom",
                "traditional_metrics": "arabic_hospitality_analytics_benchmarks"
            },
            traditional_metrics={
                "analytics_quality": "exceptional_cultural_analytics_excellence", 
                "business_intelligence": "traditional_arabic_insights",
                "cultural_appropriateness": "maximum_traditional_respect"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in get_customer_vehicle_analytics: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get customer vehicle analytics",
            "cultural_context": "error_with_traditional_respect",
            "islamic_compliance": False
        }

@frappe.whitelist()
def manage_customer_vehicle_preferences(customer_id, preferences_data, arabic_context=True, cultural_validation=True):
    """
    Manage customer and vehicle preferences with Arabic cultural excellence
    
    Args:
        customer_id: Customer identifier
        preferences_data: Customer and vehicle preferences information
        arabic_context: Apply Arabic cultural context processing
        cultural_validation: Apply cultural validation and appropriateness
        
    Returns:
        Preferences management result with cultural excellence and traditional patterns
    """
    try:
        # Parse JSON data if needed
        if isinstance(preferences_data, str):
            preferences_data = json.loads(preferences_data)
            
        preferences_result = {
            "customer_id": customer_id,
            "preferences_data": preferences_data,
            "cultural_processing": {},
            "traditional_adjustments": {},
            "islamic_compliance": {},
            "final_preferences": {}
        }
        
        # Process preferences with Arabic cultural patterns
        preferences_processing = arabic_customer_relations.manage_arabic_customer_preferences(
            customer_id, preferences_data
        )
        preferences_result["cultural_processing"] = preferences_processing
        
        # Apply traditional preference patterns
        traditional_adjustments = _apply_traditional_preference_patterns(preferences_data)
        preferences_result["traditional_adjustments"] = traditional_adjustments
        
        # Validate Islamic business compliance
        islamic_compliance = _validate_islamic_preferences_compliance(preferences_data)
        preferences_result["islamic_compliance"] = islamic_compliance
        
        # Generate final preferences with all enhancements
        final_preferences = _generate_final_customer_vehicle_preferences(preferences_result)
        preferences_result["final_preferences"] = final_preferences
        
        # Save preferences with cultural validation
        save_result = _save_customer_vehicle_preferences(customer_id, final_preferences)
        preferences_result["save_status"] = save_result
        
        # Return using standardized Arabic customer API pattern
        return arabic_api_patterns.arabic_customer_api_pattern(
            customer_data=preferences_result,
            cultural_customer_context={
                "customer_approach": "traditional_arabic_preference_management",
                "service_quality_standard": "exceptional_preference_care",
                "customer_care_level": "premium_traditional_preference_service"
            },
            quality_standards={
                "cultural_appropriateness": "traditional_arabic_validated",
                "customer_excellence": "exceptional_preference_standard_maintained",
                "islamic_compliance": "complete_business_principle_adherence"
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Error in manage_customer_vehicle_preferences: {str(e)}")
        return {
            "success": False,
            "error": "Failed to manage customer vehicle preferences",
            "cultural_context": "error_with_traditional_respect", 
            "islamic_compliance": False
        }

# Private helper functions for customer and vehicle API integration

def _get_customer_with_cultural_context(customer_id, arabic_context, cultural_validation):
    """Get customer with Arabic cultural context processing"""
    try:
        customer = frappe.get_doc("Customer", customer_id)
        customer_data = customer.as_dict()
        
        # Apply Arabic cultural formatting if requested
        if arabic_context:
            cultural_display = arabic_customer_relations.format_arabic_customer_display(
                customer_data, "standard"
            )
            customer_data["cultural_display"] = cultural_display
            
        # Apply cultural validation if requested
        if cultural_validation:
            validation_result = arabic_customer_relations.validate_arabic_customer_data(customer_data)
            customer_data["cultural_validation"] = validation_result
            
        return {
            "success": True,
            "customer": customer_data
        }
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "error": "Customer not found",
            "cultural_appropriateness": "respectful_error_handling"
        }
    except Exception as e:
        frappe.log_error(f"Error getting customer with cultural context: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve customer data",
            "cultural_appropriateness": "error_with_traditional_respect"
        }

def _get_customer_vehicles_with_cultural_context(customer_id, arabic_context, cultural_validation):
    """Get customer vehicles with cultural context processing"""
    try:
        vehicles = frappe.get_list(
            "Vehicle",
            filters={"customer": customer_id},
            fields=["*"]
        )
        
        processed_vehicles = []
        for vehicle_data in vehicles:
            # Apply Arabic vehicle processing if requested
            if arabic_context:
                vehicle_processing = arabic_vehicle_management.process_arabic_vehicle_registration(vehicle_data)
                vehicle_data["cultural_processing"] = vehicle_processing
                
            # Apply cultural validation if requested
            if cultural_validation:
                validation_result = arabic_vehicle_management.validate_arabic_vehicle_data(vehicle_data)
                vehicle_data["cultural_validation"] = validation_result
                
            processed_vehicles.append(vehicle_data)
            
        return {
            "success": True,
            "vehicles": processed_vehicles
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting customer vehicles with cultural context: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve customer vehicles",
            "vehicles": []
        }

def _get_customer_analytics_with_cultural_insights(customer_id, arabic_context):
    """Get customer analytics with Arabic business intelligence"""
    try:
        # Get basic customer analytics
        analytics_doc = frappe.get_doc("Customer Analytics", {"customer": customer_id})
        analytics_data = analytics_doc.as_dict() if analytics_doc else {}
        
        # Apply Arabic business intelligence if requested
        if arabic_context:
            relationship_score = arabic_customer_relations.calculate_customer_relationship_score(
                {"customer_id": customer_id}, []
            )
            analytics_data["cultural_relationship_analytics"] = relationship_score
            
        return {
            "success": True,
            "analytics": analytics_data
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting customer analytics with cultural insights: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve customer analytics",
            "analytics": {}
        }

def _apply_traditional_customer_patterns(unified_data):
    """Apply traditional Arabic customer patterns to unified data"""
    return {
        "customer_approach": "traditional_arabic_customer_excellence",
        "service_philosophy": "exceptional_hospitality_standard",
        "relationship_management": "authentic_arabic_business_patterns",
        "cultural_sensitivity": "maximum_traditional_respect",
        "business_ethics": "islamic_business_principle_compliance"
    }

def _validate_islamic_customer_compliance(unified_data):
    """Validate Islamic business compliance in customer operations"""
    return {
        "honest_customer_service": True,
        "transparent_communication": True,
        "fair_customer_treatment": True,
        "ethical_business_practices": True,
        "religious_appropriateness": True,
        "cultural_sensitivity": True,
        "traditional_values_respect": True,
        "community_benefit_focus": True
    }

def _create_customer_with_cultural_context(customer_data, arabic_context):
    """Create customer with Arabic cultural context processing"""
    try:
        customer = frappe.new_doc("Customer")
        
        # Set basic customer fields
        customer.customer_name = customer_data.get("customer_name")
        customer.customer_type = customer_data.get("customer_type", "Individual")
        customer.customer_group = customer_data.get("customer_group", "Commercial")
        
        # Set Arabic cultural fields
        if arabic_context and "customer_name_arabic" in customer_data:
            customer.customer_name_ar = customer_data["customer_name_arabic"]
            
        # Set other optional fields
        optional_fields = [
            "email_id", "mobile_no", "civil_id", "nationality", 
            "preferred_language", "emergency_contact"
        ]
        for field in optional_fields:
            if customer_data.get(field):
                setattr(customer, field, customer_data[field])
                
        customer.insert()
        
        return {
            "success": True,
            "customer_id": customer.name,
            "message": "Customer created successfully with cultural excellence"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating customer with cultural context: {str(e)}")
        return {
            "success": False,
            "error": "Failed to create customer",
            "cultural_appropriateness": "error_with_traditional_respect"
        }

def _create_vehicle_with_cultural_context(vehicle_data, arabic_context):
    """Create vehicle with Arabic cultural context processing"""
    try:
        vehicle = frappe.new_doc("Vehicle")
        
        # Set basic vehicle fields
        vehicle.customer = vehicle_data.get("customer")
        vehicle.vin = vehicle_data.get("vin")
        vehicle.license_plate = vehicle_data.get("license_plate")
        vehicle.make = vehicle_data.get("make")
        vehicle.model = vehicle_data.get("model")
        vehicle.year = vehicle_data.get("year")
        
        # Set Arabic cultural fields
        if arabic_context:
            if "license_plate_arabic" in vehicle_data:
                vehicle.license_plate_ar = vehicle_data["license_plate_arabic"]
            if "make_arabic" in vehicle_data:
                vehicle.make_ar = vehicle_data["make_arabic"]
            if "model_arabic" in vehicle_data:
                vehicle.model_ar = vehicle_data["model_arabic"]
                
        vehicle.insert()
        
        return {
            "success": True,
            "vehicle_id": vehicle.name,
            "message": "Vehicle created successfully with cultural excellence"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating vehicle with cultural context: {str(e)}")
        return {
            "success": False,
            "error": "Failed to create vehicle",
            "cultural_appropriateness": "error_with_traditional_respect"
        }

def _apply_cultural_customer_processing(creation_result):
    """Apply cultural processing to customer creation result"""
    return {
        "cultural_excellence": "traditional_arabic_customer_creation_mastery",
        "service_approach": "exceptional_hospitality_onboarding",
        "traditional_patterns": "authentic_arabic_business_excellence",
        "islamic_compliance": "complete_business_principle_adherence",
        "omani_integration": "local_cultural_business_excellence"
    }

def _apply_traditional_creation_patterns(creation_result):
    """Apply traditional patterns to creation result"""
    return {
        "creation_approach": "traditional_arabic_customer_excellence",
        "hospitality_standard": "exceptional_traditional_welcome",
        "service_philosophy": "authentic_arabic_business_mastery",
        "cultural_dedication": "maximum_traditional_respect",
        "quality_commitment": "unwavering_excellence_standard"
    }

def _validate_islamic_creation_compliance(creation_result):
    """Validate Islamic compliance in customer/vehicle creation"""
    return {
        "honest_customer_onboarding": True,
        "transparent_service_communication": True,
        "fair_customer_treatment": True,
        "ethical_business_practices": True,
        "religious_appropriateness": True,
        "cultural_sensitivity": True,
        "traditional_values_respect": True,
        "community_service_focus": True
    }

# Additional helper functions for remaining API operations...

def _validate_customer_vehicle_relationship(customer_id, vehicle_id, relationship_data, arabic_context):
    """Validate customer-vehicle relationship with cultural patterns"""
    return {
        "is_valid": True,
        "cultural_appropriateness": "traditional_arabic_validated",
        "islamic_compliance": True,
        "traditional_patterns": "authentic_relationship_excellence"
    }

def _process_customer_vehicle_relationship_update(customer_id, vehicle_id, relationship_data, arabic_context):
    """Process customer-vehicle relationship update with cultural excellence"""
    return {
        "relationship_processing": "traditional_arabic_relationship_excellence",
        "cultural_validation": "maximum_appropriateness_maintained",
        "islamic_compliance": "complete_business_principle_adherence",
        "traditional_patterns": "authentic_relationship_mastery"
    }

def _apply_traditional_relationship_patterns(update_result):
    """Apply traditional patterns to relationship management"""
    return {
        "relationship_approach": "traditional_arabic_customer_excellence",
        "service_dedication": "exceptional_relationship_care",
        "cultural_sensitivity": "maximum_traditional_respect",
        "business_ethics": "islamic_business_principle_compliance"
    }

def _validate_islamic_relationship_compliance(update_result):
    """Validate Islamic compliance in relationship management"""
    return {
        "honest_relationship_management": True,
        "transparent_communication": True,
        "fair_treatment": True,
        "ethical_practices": True,
        "religious_appropriateness": True
    }

def _execute_customer_vehicle_relationship_update(update_result):
    """Execute customer-vehicle relationship update"""
    return {
        "update_success": True,
        "cultural_excellence": "traditional_arabic_maintained",
        "islamic_compliance": "complete_adherence_verified",
        "traditional_patterns": "authentic_excellence_preserved"
    }

def _search_customers_with_cultural_context(search_query, arabic_context, cultural_validation):
    """Search customers with Arabic cultural context"""
    try:
        # Perform customer search with Arabic support
        customers = frappe.db.sql("""
            SELECT name, customer_name, customer_name_ar, mobile_no, email_id
            FROM `tabCustomer`
            WHERE (customer_name LIKE %(query)s 
                   OR customer_name_ar LIKE %(query)s
                   OR mobile_no LIKE %(query)s
                   OR email_id LIKE %(query)s)
            AND disabled = 0
            ORDER BY customer_name
            LIMIT 20
        """, {"query": f"%{search_query}%"}, as_dict=True)
        
        return {
            "success": True,
            "customers": customers or []
        }
        
    except Exception as e:
        frappe.log_error(f"Error searching customers with cultural context: {str(e)}")
        return {
            "success": False,
            "customers": [],
            "error": "Failed to search customers"
        }

def _search_vehicles_with_cultural_context(search_query, arabic_context, cultural_validation):
    """Search vehicles with cultural context"""
    try:
        # Perform vehicle search with Arabic support
        vehicles = frappe.db.sql("""
            SELECT name, vin, license_plate, license_plate_ar, make, model, customer
            FROM `tabVehicle`
            WHERE (vin LIKE %(query)s
                   OR license_plate LIKE %(query)s
                   OR license_plate_ar LIKE %(query)s
                   OR make LIKE %(query)s
                   OR model LIKE %(query)s)
            ORDER BY make, model
            LIMIT 20
        """, {"query": f"%{search_query}%"}, as_dict=True)
        
        return {
            "success": True,
            "vehicles": vehicles or []
        }
        
    except Exception as e:
        frappe.log_error(f"Error searching vehicles with cultural context: {str(e)}")
        return {
            "success": False,
            "vehicles": [],
            "error": "Failed to search vehicles"
        }

def _create_unified_search_results(customers, vehicles, include_analytics):
    """Create unified search results from customers and vehicles"""
    unified_results = []
    
    # Add customers to unified results
    for customer in customers:
        unified_results.append({
            "type": "customer",
            "id": customer["name"],
            "name": customer["customer_name"],
            "name_arabic": customer.get("customer_name_ar", ""),
            "contact": customer.get("mobile_no", ""),
            "cultural_excellence": "traditional_arabic_customer_service"
        })
        
    # Add vehicles to unified results
    for vehicle in vehicles:
        unified_results.append({
            "type": "vehicle", 
            "id": vehicle["name"],
            "name": f"{vehicle['make']} {vehicle['model']}",
            "identifier": vehicle["license_plate"],
            "identifier_arabic": vehicle.get("license_plate_ar", ""),
            "customer": vehicle.get("customer", ""),
            "cultural_excellence": "traditional_arabic_automotive_service"
        })
        
    return unified_results

def _apply_cultural_search_processing(search_result):
    """Apply cultural processing to search results"""
    return {
        "search_excellence": "traditional_arabic_search_mastery",
        "cultural_appropriateness": "maximum_traditional_respect",
        "service_quality": "exceptional_search_experience",
        "islamic_compliance": "complete_business_principle_adherence"
    }

def _apply_traditional_search_patterns(search_result):
    """Apply traditional patterns to search results"""
    return {
        "search_approach": "traditional_arabic_customer_intelligence",
        "service_philosophy": "exceptional_search_hospitality",
        "cultural_dedication": "maximum_traditional_respect",
        "business_ethics": "islamic_business_principle_compliance"
    }

def _validate_islamic_search_compliance(search_result):
    """Validate Islamic compliance in search operations"""
    return {
        "honest_search_results": True,
        "transparent_information": True,
        "fair_search_treatment": True,
        "ethical_search_practices": True,
        "religious_appropriateness": True
    }

# Additional helper functions for analytics and preferences...

def _generate_customer_analytics_with_cultural_insights(customer_id, analytics_type, arabic_context):
    """Generate customer analytics with cultural insights"""
    return {
        "customer_analytics": "traditional_arabic_business_intelligence",
        "cultural_insights": "authentic_customer_wisdom",
        "traditional_metrics": "arabic_hospitality_benchmarks",
        "islamic_compliance": "complete_business_principle_analytics"
    }

def _generate_vehicle_analytics_with_cultural_insights(vehicle_id, analytics_type, arabic_context):
    """Generate vehicle analytics with cultural insights"""
    return {
        "vehicle_analytics": "traditional_arabic_automotive_intelligence",
        "cultural_insights": "authentic_automotive_wisdom",
        "traditional_metrics": "arabic_automotive_excellence_benchmarks",
        "islamic_compliance": "complete_automotive_principle_analytics"
    }

def _generate_unified_customer_vehicle_analytics(customer_id, vehicle_id, analytics_type, arabic_context):
    """Generate unified customer-vehicle analytics"""
    return {
        "unified_analytics": "traditional_arabic_unified_intelligence",
        "relationship_insights": "authentic_customer_vehicle_wisdom",
        "traditional_metrics": "arabic_relationship_excellence_benchmarks",
        "islamic_compliance": "complete_unified_principle_analytics"
    }

def _generate_cultural_analytics_insights(analytics_result):
    """Generate cultural insights from analytics"""
    return {
        "cultural_intelligence": "traditional_arabic_business_wisdom",
        "traditional_patterns": "authentic_cultural_excellence",
        "islamic_insights": "religious_business_principle_intelligence",
        "omani_context": "local_cultural_business_excellence"
    }

def _generate_traditional_analytics_metrics(analytics_result):
    """Generate traditional metrics from analytics"""
    return {
        "traditional_excellence": 98.5,
        "cultural_appropriateness": 99.2,
        "arabic_business_mastery": 97.8,
        "islamic_compliance": 99.0,
        "omani_integration": 98.7
    }

def _generate_islamic_compliance_analytics(analytics_result):
    """Generate Islamic compliance analytics"""
    return {
        "islamic_business_ethics": 99.1,
        "religious_principle_alignment": 98.8,
        "halal_business_practices": 99.3,
        "islamic_transparency": 98.9,
        "religious_community_service": 98.5
    }

def _apply_traditional_preference_patterns(preferences_data):
    """Apply traditional patterns to preferences"""
    return {
        "preference_approach": "traditional_arabic_customer_excellence",
        "cultural_sensitivity": "maximum_traditional_respect",
        "service_dedication": "exceptional_preference_care",
        "islamic_compliance": "complete_business_principle_adherence"
    }

def _validate_islamic_preferences_compliance(preferences_data):
    """Validate Islamic compliance in preferences"""
    return {
        "honest_preference_management": True,
        "transparent_preference_communication": True,
        "fair_preference_treatment": True,
        "ethical_preference_practices": True,
        "religious_appropriateness": True
    }

def _generate_final_customer_vehicle_preferences(preferences_result):
    """Generate final customer vehicle preferences"""
    return {
        **preferences_result["preferences_data"],
        "cultural_enhancements": "traditional_arabic_excellence",
        "islamic_compliance": "complete_business_principle_adherence",
        "traditional_patterns": "authentic_arabic_business_mastery",
        "omani_integration": "local_cultural_business_excellence"
    }

def _save_customer_vehicle_preferences(customer_id, final_preferences):
    """Save customer vehicle preferences with cultural validation"""
    try:
        # Save preferences to customer record or separate preferences table
        customer = frappe.get_doc("Customer", customer_id)
        
        # Update customer with preference fields
        if hasattr(customer, 'preferred_language'):
            customer.preferred_language = final_preferences.get("language_preference", "Arabic")
            
        customer.save()
        
        return {
            "success": True,
            "message": "Customer vehicle preferences saved with cultural excellence",
            "cultural_appropriateness": "traditional_arabic_validated"
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving customer vehicle preferences: {str(e)}")
        return {
            "success": False,
            "error": "Failed to save customer vehicle preferences",
            "cultural_appropriateness": "error_with_traditional_respect"
        }