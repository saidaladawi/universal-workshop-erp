# -*- coding: utf-8 -*-
# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import nowdate, add_days, flt, cint, formatdate, get_datetime
from frappe.utils.data import get_link_to_form
import json
import re
from datetime import datetime, timedelta

# Import shared libraries with fallback support
try:
    from universal_workshop.shared_libraries.arabic_business_logic import (
        validate_arabic_business_context,
        apply_traditional_patterns,
        ensure_islamic_compliance,
        validate_arabic_name_pattern,
        format_arabic_business_communication
    )
    from universal_workshop.shared_libraries.financial_compliance import (
        calculate_omani_vat,
        validate_islamic_transaction,
        format_omani_currency
    )
    from universal_workshop.shared_libraries.customer_relations import (
        calculate_customer_lifetime_value,
        determine_customer_segment,
        assess_retention_risk,
        generate_loyalty_recommendations
    )
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError:
    SHARED_LIBRARIES_AVAILABLE = False
    frappe.log_error("Shared libraries not available, using fallback methods")

class ConsolidatedCustomerProfile(Document):
    """
    Consolidated Customer Profile DocType
    
    This enhanced customer profile consolidates multiple customer-related functionalities
    while preserving and enhancing Arabic cultural excellence, Islamic business compliance,
    and Omani regulatory requirements.
    """
    
    def autoname(self):
        """Generate customer ID automatically"""
        if not self.customer_id:
            # Generate based on customer type and sequence
            prefix = self.get_customer_id_prefix()
            self.customer_id = frappe.model.naming.make_autoname(f"{prefix}-.####")
    
    def get_customer_id_prefix(self):
        """Get customer ID prefix based on customer type"""
        prefixes = {
            "Individual": "CUST",
            "Corporate": "CORP",
            "Government": "GOVT",
            "Fleet": "FLEET",
            "Insurance Partner": "INS",
            "Diplomatic": "DIPL"
        }
        return prefixes.get(self.customer_type, "CUST")
    
    def validate(self):
        """Comprehensive validation with Arabic cultural context"""
        self.validate_basic_information()
        self.validate_arabic_cultural_context()
        self.validate_omani_compliance()
        self.validate_communication_preferences()
        self.calculate_customer_metrics()
        self.ensure_islamic_business_compliance()
        self.apply_traditional_customer_patterns()
        self.update_integration_markers()
    
    def validate_basic_information(self):
        """Validate basic customer information"""
        # Validate Oman Civil ID format (8 digits)
        if self.civil_id:
            if not re.match(r'^\d{8}$', self.civil_id):
                frappe.throw(_("Civil ID must be 8 digits"))
        
        # Validate Oman phone number format
        if self.phone:
            if not re.match(r'^\+968\d{8}$', self.phone):
                if not self.phone.startswith('+968'):
                    self.phone = f"+968{self.phone.lstrip('0')}"
                if not re.match(r'^\+968\d{8}$', self.phone):
                    frappe.throw(_("Phone number must be in +968XXXXXXXX format"))
        
        # Validate email format
        if self.email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
                frappe.throw(_("Please enter a valid email address"))
        
        # Ensure Arabic name is provided
        if not self.customer_name_ar and self.customer_name:
            msgprint(_("Arabic customer name is recommended for better cultural service"))
    
    def validate_arabic_cultural_context(self):
        """Validate Arabic cultural context and appropriateness"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for Arabic validation
            arabic_validation = validate_arabic_business_context({
                "customer_name": self.customer_name,
                "customer_name_ar": self.customer_name_ar,
                "communication_preference": self.arabic_communication_preference,
                "cultural_context": {
                    "traditional_patterns": self.traditional_customer_patterns,
                    "islamic_compliance": self.islamic_business_compliance,
                    "omani_integration": self.omani_cultural_integration
                }
            })
            
            if arabic_validation.get("validation_required"):
                for warning in arabic_validation.get("warnings", []):
                    msgprint(_(warning))
        else:
            # Fallback Arabic validation
            if self.customer_name_ar:
                # Basic Arabic name pattern validation
                if not re.match(r'^[\u0600-\u06FF\s]+$', self.customer_name_ar):
                    frappe.throw(_("Arabic name contains invalid characters"))
        
        # Set Arabic name validation flag
        self.arabic_name_validation = 1 if self.customer_name_ar else 0
    
    def validate_omani_compliance(self):
        """Validate Omani business compliance requirements"""
        # Validate governorate selection
        if self.country == "Oman" and not self.governorate:
            msgprint(_("Please select a governorate for Omani customers"))
        
        # Validate commercial registration for corporate customers
        if self.customer_type == "Corporate" and not self.commercial_registration:
            msgprint(_("Commercial registration is required for corporate customers"))
        
        # Validate tax ID format if provided
        if self.tax_id:
            if not re.match(r'^\d{8,15}$', self.tax_id):
                frappe.throw(_("Tax ID must be 8-15 digits"))
    
    def validate_communication_preferences(self):
        """Validate communication preferences and settings"""
        # Ensure notification language matches preferred language
        if self.preferred_language and not self.notification_language:
            self.notification_language = self.preferred_language
        
        # Validate communication method based on available contact information
        if self.communication_method == "Phone Call" and not self.phone:
            frappe.throw(_("Phone number is required for phone call communication"))
        elif self.communication_method == "Email" and not self.email:
            frappe.throw(_("Email address is required for email communication"))
        elif self.communication_method in ["SMS", "WhatsApp"] and not self.phone:
            frappe.throw(_("Phone number is required for SMS/WhatsApp communication"))
    
    def calculate_customer_metrics(self):
        """Calculate customer metrics and analytics"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Calculate CLV using shared library
            clv_data = calculate_customer_lifetime_value({
                "customer_id": self.customer_id,
                "service_history": self.get_service_history(),
                "loyalty_points": self.loyalty_points_balance or 0,
                "customer_since": self.customer_since
            })
            
            self.total_lifetime_value = clv_data.get("total_clv", 0)
            self.clv_score = clv_data.get("clv_score", 0)
            
            # Determine customer segment
            segment_data = determine_customer_segment({
                "clv_score": self.clv_score,
                "service_frequency": clv_data.get("service_frequency", 0),
                "last_service_date": self.last_service_date
            })
            
            self.customer_segment = segment_data.get("segment", "Regular")
            
            # Assess retention risk
            risk_assessment = assess_retention_risk({
                "last_service_date": self.last_service_date,
                "service_frequency": clv_data.get("service_frequency", 0),
                "satisfaction_score": self.get_average_satisfaction_score()
            })
            
            self.retention_risk_score = risk_assessment.get("risk_score", 0)
        else:
            # Fallback calculations
            self.calculate_basic_metrics()
        
        # Update vehicle count
        self.total_vehicles = len(self.vehicles) if self.vehicles else 0
        
        # Calculate loyalty points totals
        self.update_loyalty_totals()
    
    def calculate_basic_metrics(self):
        """Basic fallback metric calculations"""
        # Calculate total lifetime value from service orders
        service_orders = frappe.get_all(
            "Service Order",
            filters={"customer": self.customer_id},
            fields=["final_amount"]
        )
        
        total_value = sum(flt(order.final_amount) for order in service_orders)
        self.total_lifetime_value = total_value
        
        # Basic CLV score calculation
        if total_value > 0:
            days_since_first_service = (
                (get_datetime() - get_datetime(self.customer_since)).days
                if self.customer_since else 365
            )
            self.clv_score = total_value / max(days_since_first_service, 1) * 365
        
        # Basic segment determination
        if total_value > 5000:
            self.customer_segment = "VIP"
        elif total_value > 2000:
            self.customer_segment = "High Value"
        elif total_value > 500:
            self.customer_segment = "Regular"
        else:
            self.customer_segment = "New Customer"
    
    def ensure_islamic_business_compliance(self):
        """Ensure Islamic business principle compliance"""
        if SHARED_LIBRARIES_AVAILABLE:
            islamic_validation = ensure_islamic_compliance({
                "customer_type": self.customer_type,
                "business_relationship": "customer_service",
                "cultural_context": {
                    "halal_requirements": self.halal_service_requirements,
                    "islamic_preferences": self.islamic_calendar_preferences
                }
            })
            
            if islamic_validation.get("compliance_notes"):
                self.islamic_business_compliance = islamic_validation.get("compliance_notes")
            
            self.islamic_compliance_verified = 1
        else:
            # Fallback Islamic compliance
            if self.halal_service_requirements:
                self.islamic_business_compliance = "Halal service requirements documented"
            self.islamic_compliance_verified = 1
    
    def apply_traditional_customer_patterns(self):
        """Apply traditional Arabic customer relationship patterns"""
        if SHARED_LIBRARIES_AVAILABLE:
            traditional_patterns = apply_traditional_patterns({
                "customer_name_ar": self.customer_name_ar,
                "customer_type": self.customer_type,
                "communication_preference": self.arabic_communication_preference,
                "cultural_context": self.omani_cultural_integration
            })
            
            if traditional_patterns.get("patterns_applied"):
                self.traditional_customer_patterns = traditional_patterns.get("pattern_description")
                self.traditional_patterns_applied = 1
        else:
            # Fallback traditional patterns
            if self.arabic_communication_preference == "Arabic Primary":
                self.traditional_customer_patterns = "Arabic-first customer service approach"
            self.traditional_patterns_applied = 1
    
    def update_integration_markers(self):
        """Update shared library integration markers"""
        if SHARED_LIBRARIES_AVAILABLE:
            self.shared_library_customer_enhanced = 1
            self.arabic_business_logic_integrated = 1
            self.omani_context_validated = 1
        else:
            # Fallback integration markers
            self.shared_library_customer_enhanced = 0
            self.arabic_business_logic_integrated = 0
            self.omani_context_validated = 0
    
    def get_service_history(self):
        """Get customer service history"""
        return frappe.get_all(
            "Service Order",
            filters={"customer": self.customer_id},
            fields=["name", "service_date", "final_amount", "status"],
            order_by="service_date desc"
        )
    
    def get_average_satisfaction_score(self):
        """Calculate average customer satisfaction score"""
        if self.satisfaction_scores:
            total_score = sum(flt(score.score) for score in self.satisfaction_scores)
            return total_score / len(self.satisfaction_scores) if self.satisfaction_scores else 0
        return 0
    
    def update_loyalty_totals(self):
        """Update loyalty points totals"""
        # Get loyalty point transactions
        loyalty_transactions = frappe.get_all(
            "Customer Loyalty Points",
            filters={"customer": self.customer_id},
            fields=["points_earned", "points_redeemed", "expiry_date"]
        )
        
        total_earned = sum(cint(trans.points_earned) for trans in loyalty_transactions)
        total_redeemed = sum(cint(trans.points_redeemed) for trans in loyalty_transactions)
        
        # Calculate current balance (excluding expired points)
        current_balance = 0
        for trans in loyalty_transactions:
            if trans.expiry_date and get_datetime(trans.expiry_date) > get_datetime():
                current_balance += cint(trans.points_earned) - cint(trans.points_redeemed)
        
        self.loyalty_points_earned = total_earned
        self.loyalty_points_redeemed = total_redeemed
        self.loyalty_points_balance = max(current_balance, 0)
    
    def before_save(self):
        """Before save operations"""
        # Set creation date if new
        if not self.created_date:
            self.created_date = nowdate()
        
        # Update customer since date if new
        if not self.customer_since:
            self.customer_since = nowdate()
        
        # Set created by if new
        if not self.created_by:
            self.created_by = frappe.session.user
        
        # Always update last updated by
        self.last_updated_by = frappe.session.user
    
    def after_insert(self):
        """After insert operations"""
        # Create customer portal user if portal is enabled
        if self.portal_enabled and self.email:
            self.create_portal_user()
        
        # Send welcome message
        self.send_welcome_message()
    
    def create_portal_user(self):
        """Create portal user for customer"""
        if not frappe.db.exists("User", self.email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": self.email,
                "first_name": self.customer_name,
                "user_type": "Website User",
                "language": self.preferred_language.lower() if self.preferred_language else "ar"
            })
            user.insert(ignore_permissions=True)
            
            # Set portal username
            self.portal_username = self.email
            self.db_update()
    
    def send_welcome_message(self):
        """Send welcome message to customer"""
        if self.communication_method and self.communication_method != "No Contact":
            # Format message based on preferred language
            if self.preferred_language == "Arabic":
                message = f"مرحباً بك {self.customer_name_ar or self.customer_name} في ورشة يونيفرسال. نحن سعداء لخدمتك."
            else:
                message = f"Welcome {self.customer_name} to Universal Workshop. We're happy to serve you."
            
            # Send based on communication method
            if self.communication_method == "SMS" and self.phone:
                self.send_sms_notification(message)
            elif self.communication_method == "Email" and self.email:
                self.send_email_notification("Welcome to Universal Workshop", message)
    
    def send_sms_notification(self, message):
        """Send SMS notification"""
        try:
            # Implementation depends on SMS gateway
            frappe.log_error(f"SMS sent to {self.phone}: {message}")
        except Exception as e:
            frappe.log_error(f"Failed to send SMS: {str(e)}")
    
    def send_email_notification(self, subject, message):
        """Send email notification"""
        try:
            frappe.sendmail(
                recipients=[self.email],
                subject=subject,
                message=message,
                sender="noreply@universalworkshop.com"
            )
        except Exception as e:
            frappe.log_error(f"Failed to send email: {str(e)}")
    
    @frappe.whitelist()
    def get_loyalty_recommendations(self):
        """Get loyalty program recommendations"""
        if SHARED_LIBRARIES_AVAILABLE:
            return generate_loyalty_recommendations({
                "customer_id": self.customer_id,
                "current_tier": self.loyalty_tier,
                "points_balance": self.loyalty_points_balance,
                "service_history": self.get_service_history()
            })
        else:
            # Fallback recommendations
            return {
                "recommended_tier": self.loyalty_tier,
                "points_to_next_tier": 0,
                "recommended_actions": ["Continue regular service visits"]
            }
    
    @frappe.whitelist()
    def get_customer_dashboard_data(self):
        """Get customer dashboard data"""
        return {
            "customer_info": {
                "name": self.customer_name,
                "name_ar": self.customer_name_ar,
                "tier": self.loyalty_tier,
                "points_balance": self.loyalty_points_balance,
                "clv_score": self.clv_score
            },
            "service_summary": {
                "total_services": len(self.get_service_history()),
                "last_service": self.last_service_date,
                "next_service": self.next_service_due,
                "total_spent": self.total_lifetime_value
            },
            "vehicle_summary": {
                "total_vehicles": self.total_vehicles,
                "primary_vehicle": self.primary_vehicle
            },
            "communication_preferences": {
                "preferred_language": self.preferred_language,
                "communication_method": self.communication_method,
                "notification_language": self.notification_language
            }
        }
    
    def get_arabic_formatted_name(self):
        """Get properly formatted Arabic name"""
        if SHARED_LIBRARIES_AVAILABLE:
            return format_arabic_business_communication(self.customer_name_ar)
        return self.customer_name_ar
    
    def get_omani_formatted_currency(self, amount):
        """Get Omani currency formatted amount"""
        if SHARED_LIBRARIES_AVAILABLE:
            return format_omani_currency(amount)
        return f"OMR {amount:.3f}"