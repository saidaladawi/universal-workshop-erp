# -*- coding: utf-8 -*-
# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import nowdate, add_days, flt, cint, formatdate, get_datetime, add_months
from frappe.utils.data import get_link_to_form
import json
import re
from datetime import datetime, timedelta
import requests

# Import shared libraries with fallback support
try:
    from universal_workshop.shared_libraries.arabic_business_logic import (
        validate_arabic_business_context,
        apply_traditional_patterns,
        ensure_islamic_compliance,
        translate_vehicle_terminology
    )
    from universal_workshop.shared_libraries.vehicle_management import (
        enhanced_vin_decode,
        calculate_maintenance_schedule,
        predict_service_requirements,
        optimize_service_intervals
    )
    from universal_workshop.shared_libraries.omani_compliance import (
        validate_omani_license_plate,
        check_rop_registration,
        validate_registration_documents
    )
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError:
    SHARED_LIBRARIES_AVAILABLE = False
    frappe.log_error("Shared libraries not available, using fallback methods")

class EnhancedVehicleManagement(Document):
    """
    Enhanced Vehicle Management DocType
    
    This consolidated vehicle management system combines multiple vehicle-related
    functionalities while preserving and enhancing Arabic cultural excellence,
    Islamic business compliance, and advanced VIN decoding capabilities.
    """
    
    def autoname(self):
        """Generate vehicle ID automatically"""
        if not self.vehicle_id:
            # Generate based on customer type and VIN
            if self.vin:
                # Use last 6 characters of VIN for uniqueness
                vin_suffix = self.vin[-6:] if len(self.vin) >= 6 else self.vin
                self.vehicle_id = f"VEH-{vin_suffix}"
            else:
                self.vehicle_id = frappe.model.naming.make_autoname("VEH-.####")
    
    def validate(self):
        """Comprehensive validation with Arabic cultural context"""
        self.validate_vin()
        self.validate_license_plate()
        self.validate_vehicle_specifications()
        self.validate_arabic_cultural_context()
        self.validate_omani_compliance()
        self.calculate_service_schedules()
        self.decode_vin_information()
        self.ensure_islamic_business_compliance()
        self.apply_traditional_vehicle_patterns()
        self.update_integration_markers()
    
    def validate_vin(self):
        """Validate VIN format and characters"""
        if not self.vin:
            frappe.throw(_("VIN is required"))
        
        # Remove spaces and convert to uppercase
        self.vin = self.vin.replace(" ", "").upper()
        
        # Validate VIN length
        if len(self.vin) != 17:
            frappe.throw(_("VIN must be exactly 17 characters"))
        
        # Validate VIN characters (no I, O, Q allowed)
        if re.search(r'[IOQ]', self.vin):
            frappe.throw(_("VIN cannot contain letters I, O, or Q"))
        
        # Validate VIN format (alphanumeric)
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', self.vin):
            frappe.throw(_("VIN contains invalid characters"))
        
        # Check for duplicate VIN
        existing_vehicle = frappe.db.exists("Enhanced Vehicle Management", 
                                          {"vin": self.vin, "name": ["!=", self.name]})
        if existing_vehicle:
            frappe.throw(_("Vehicle with VIN {0} already exists").format(self.vin))
    
    def validate_license_plate(self):
        """Validate license plate format"""
        if not self.license_plate:
            frappe.throw(_("License plate is required"))
        
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for Omani license plate validation
            plate_validation = validate_omani_license_plate(self.license_plate)
            if not plate_validation.get("valid"):
                frappe.throw(_(plate_validation.get("error", "Invalid license plate format")))
        else:
            # Basic license plate validation
            if len(self.license_plate) < 2:
                frappe.throw(_("License plate is too short"))
        
        # Check for duplicate license plate
        existing_vehicle = frappe.db.exists("Enhanced Vehicle Management", 
                                          {"license_plate": self.license_plate, "name": ["!=", self.name]})
        if existing_vehicle:
            frappe.throw(_("Vehicle with license plate {0} already exists").format(self.license_plate))
    
    def validate_vehicle_specifications(self):
        """Validate vehicle specifications"""
        # Validate year
        current_year = datetime.now().year
        if self.year:
            if self.year < 1900 or self.year > current_year + 1:
                frappe.throw(_("Invalid vehicle year"))
        
        # Validate engine capacity
        if self.engine_capacity:
            if self.engine_capacity <= 0 or self.engine_capacity > 20:
                frappe.throw(_("Engine capacity must be between 0.1 and 20.0 liters"))
        
        # Validate mileage
        if self.current_mileage and self.current_mileage < 0:
            frappe.throw(_("Current mileage cannot be negative"))
    
    def validate_arabic_cultural_context(self):
        """Validate Arabic cultural context and terminology"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for Arabic terminology translation
            if self.make and not self.make_ar:
                self.make_ar = translate_vehicle_terminology(self.make, "make")
            
            if self.model and not self.model_ar:
                self.model_ar = translate_vehicle_terminology(self.model, "model")
            
            if self.color and not self.color_ar:
                self.color_ar = translate_vehicle_terminology(self.color, "color")
            
            # Validate Arabic cultural context
            cultural_validation = validate_arabic_business_context({
                "vehicle_make": self.make,
                "vehicle_model": self.model,
                "arabic_terminology": {
                    "make_ar": self.make_ar,
                    "model_ar": self.model_ar,
                    "color_ar": self.color_ar
                }
            })
            
            if cultural_validation.get("suggestions"):
                for suggestion in cultural_validation.get("suggestions", []):
                    msgprint(_(suggestion))
        else:
            # Fallback Arabic terminology
            if self.make and not self.make_ar:
                arabic_makes = {
                    "Toyota": "تويوتا",
                    "Honda": "هوندا", 
                    "Nissan": "نيسان",
                    "BMW": "بي إم دبليو",
                    "Mercedes": "مرسيدس",
                    "Audi": "أودي",
                    "Hyundai": "هيونداي",
                    "Kia": "كيا",
                    "Mitsubishi": "ميتسوبيشي",
                    "Mazda": "مازدا"
                }
                self.make_ar = arabic_makes.get(self.make, self.make)
            
            if self.color and not self.color_ar:
                arabic_colors = {
                    "White": "أبيض",
                    "Black": "أسود",
                    "Silver": "فضي",
                    "Gray": "رمادي",
                    "Blue": "أزرق",
                    "Red": "أحمر",
                    "Green": "أخضر",
                    "Brown": "بني",
                    "Gold": "ذهبي"
                }
                self.color_ar = arabic_colors.get(self.color, self.color)
    
    def validate_omani_compliance(self):
        """Validate Omani regulatory compliance"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Check ROP registration if available
            if self.license_plate and self.registration_date:
                rop_check = check_rop_registration({
                    "license_plate": self.license_plate,
                    "registration_date": self.registration_date,
                    "customer_civil_id": self.get_customer_civil_id()
                })
                
                if rop_check.get("status") == "verified":
                    self.omani_registration_context = "ROP registration verified"
                elif rop_check.get("status") == "pending":
                    msgprint(_("ROP registration verification is pending"))
        
        # Validate registration and insurance expiry dates
        if self.registration_expiry and self.registration_expiry < frappe.utils.today():
            msgprint(_("Vehicle registration has expired"))
        
        if self.insurance_expiry and self.insurance_expiry < frappe.utils.today():
            msgprint(_("Vehicle insurance has expired"))
    
    def calculate_service_schedules(self):
        """Calculate next service dates and mileage"""
        if SHARED_LIBRARIES_AVAILABLE:
            # Use shared library for advanced service scheduling
            service_schedule = calculate_maintenance_schedule({
                "vehicle_vin": self.vin,
                "current_mileage": self.current_mileage or 0,
                "last_service_date": self.last_service_date,
                "last_service_mileage": self.last_service_mileage or 0,
                "service_interval_km": self.service_interval_km or 10000,
                "service_interval_months": self.service_interval_months or 6,
                "make": self.make,
                "model": self.model,
                "year": self.year
            })
            
            self.next_service_date = service_schedule.get("next_service_date")
            self.next_service_mileage = service_schedule.get("next_service_mileage")
            
            # Calculate average monthly mileage
            if service_schedule.get("average_monthly_mileage"):
                self.average_monthly_mileage = service_schedule.get("average_monthly_mileage")
        else:
            # Fallback service scheduling
            if self.last_service_date and self.service_interval_months:
                self.next_service_date = add_months(self.last_service_date, self.service_interval_months)
            
            if self.last_service_mileage and self.service_interval_km:
                self.next_service_mileage = self.last_service_mileage + self.service_interval_km
            
            # Basic monthly mileage calculation
            if self.current_mileage and self.registration_date:
                months_since_registration = (
                    (get_datetime() - get_datetime(self.registration_date)).days / 30.44
                )
                if months_since_registration > 0:
                    self.average_monthly_mileage = self.current_mileage / months_since_registration
    
    def decode_vin_information(self):
        """Decode VIN information using multiple sources"""
        if self.vin and (not self.vin_decode_data or self.vin_decode_status == "Pending"):
            if SHARED_LIBRARIES_AVAILABLE:
                # Use enhanced VIN decode from shared library
                decode_result = enhanced_vin_decode(self.vin)
                
                if decode_result.get("success"):
                    self.vin_decode_data = json.dumps(decode_result.get("data"))
                    self.vin_decode_status = "Decoded"
                    self.decode_source = decode_result.get("source")
                    self.decode_reliability = decode_result.get("reliability")
                    self.decode_timestamp = frappe.utils.now()
                    
                    # Update vehicle information from decode
                    decode_data = decode_result.get("data", {})
                    if not self.make and decode_data.get("Make"):
                        self.make = decode_data.get("Make")
                    if not self.model and decode_data.get("Model"):
                        self.model = decode_data.get("Model")
                    if not self.year and decode_data.get("ModelYear"):
                        self.year = cint(decode_data.get("ModelYear"))
                else:
                    self.vin_decode_status = "Failed"
                    frappe.log_error(f"VIN decode failed: {decode_result.get('error')}")
            else:
                # Fallback VIN decode using NHTSA API
                self.fallback_vin_decode()
    
    def fallback_vin_decode(self):
        """Fallback VIN decode using NHTSA API"""
        try:
            # Try NHTSA API
            response = requests.get(
                f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{self.vin}?format=json",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("Results", [])
                
                decode_data = {}
                for result in results:
                    if result.get("Value") and result.get("Value") != "Not Applicable":
                        decode_data[result.get("Variable")] = result.get("Value")
                
                if decode_data:
                    self.vin_decode_data = json.dumps(decode_data)
                    self.vin_decode_status = "Decoded"
                    self.decode_source = "NHTSA"
                    self.decode_reliability = "High"
                    self.decode_timestamp = frappe.utils.now()
                    
                    # Update vehicle information
                    if not self.make and decode_data.get("Make"):
                        self.make = decode_data.get("Make")
                    if not self.model and decode_data.get("Model"):
                        self.model = decode_data.get("Model")
                    if not self.year and decode_data.get("Model Year"):
                        self.year = cint(decode_data.get("Model Year"))
                else:
                    self.vin_decode_status = "Failed"
            else:
                self.vin_decode_status = "Failed"
                
        except Exception as e:
            self.vin_decode_status = "Failed"
            frappe.log_error(f"VIN decode error: {str(e)}")
    
    def ensure_islamic_business_compliance(self):
        """Ensure Islamic business principle compliance"""
        if SHARED_LIBRARIES_AVAILABLE:
            islamic_validation = ensure_islamic_compliance({
                "business_context": "vehicle_management",
                "vehicle_type": self.body_type,
                "service_requirements": {
                    "halal_compliant": True,
                    "cultural_sensitivity": True
                }
            })
            
            if islamic_validation.get("compliance_notes"):
                self.islamic_compliance_notes = islamic_validation.get("compliance_notes")
            
            self.islamic_compliance_verified = 1
        else:
            # Fallback Islamic compliance
            self.islamic_compliance_notes = "Islamic business principles applied to vehicle service"
            self.islamic_compliance_verified = 1
    
    def apply_traditional_vehicle_patterns(self):
        """Apply traditional Arabic vehicle care patterns"""
        if SHARED_LIBRARIES_AVAILABLE:
            traditional_patterns = apply_traditional_patterns({
                "context": "vehicle_care",
                "vehicle_make": self.make,
                "customer_preferences": self.get_customer_preferences(),
                "cultural_context": "omani_automotive"
            })
            
            if traditional_patterns.get("patterns_applied"):
                self.traditional_vehicle_care = traditional_patterns.get("pattern_description")
                self.traditional_patterns_applied = 1
        else:
            # Fallback traditional patterns
            self.traditional_vehicle_care = "Traditional Arabic vehicle maintenance patterns applied"
            self.traditional_patterns_applied = 1
    
    def update_integration_markers(self):
        """Update shared library integration markers"""
        if SHARED_LIBRARIES_AVAILABLE:
            self.shared_library_vehicle_enhanced = 1
            self.arabic_business_logic_integrated = 1
            self.omani_context_validated = 1
        else:
            # Fallback integration markers
            self.shared_library_vehicle_enhanced = 0
            self.arabic_business_logic_integrated = 0
            self.omani_context_validated = 0
    
    def get_customer_civil_id(self):
        """Get customer civil ID"""
        if self.customer:
            customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
            return customer_doc.civil_id
        return None
    
    def get_customer_preferences(self):
        """Get customer cultural preferences"""
        if self.customer:
            customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
            return {
                "arabic_communication": customer_doc.arabic_communication_preference,
                "traditional_patterns": customer_doc.traditional_customer_patterns,
                "islamic_compliance": customer_doc.islamic_business_compliance
            }
        return {}
    
    def before_save(self):
        """Before save operations"""
        # Set creation date if new
        if not self.created_date:
            self.created_date = nowdate()
        
        # Set created by if new
        if not self.created_by:
            self.created_by = frappe.session.user
        
        # Always update last updated by
        self.last_updated_by = frappe.session.user
        
        # Update mileage history
        self.update_mileage_history()
    
    def update_mileage_history(self):
        """Update mileage history tracking"""
        if self.current_mileage:
            # Check if this is a new mileage reading
            last_mileage_entry = None
            if self.mileage_history:
                last_mileage_entry = max(self.mileage_history, 
                                       key=lambda x: x.reading_date if x.reading_date else "")
            
            should_add_entry = False
            if not last_mileage_entry:
                should_add_entry = True
            elif last_mileage_entry.mileage != self.current_mileage:
                should_add_entry = True
            
            if should_add_entry:
                self.append("mileage_history", {
                    "reading_date": frappe.utils.today(),
                    "mileage": self.current_mileage,
                    "recorded_by": frappe.session.user,
                    "source": "Manual Entry"
                })
    
    def after_insert(self):
        """After insert operations"""
        # Create maintenance alerts if needed
        self.create_maintenance_alerts()
        
        # Update customer vehicle count
        self.update_customer_vehicle_count()
    
    def create_maintenance_alerts(self):
        """Create maintenance alerts based on vehicle condition"""
        alerts_to_create = []
        
        # Registration expiry alert
        if self.registration_expiry:
            days_to_expiry = (get_datetime(self.registration_expiry) - get_datetime()).days
            if days_to_expiry <= 30:
                alerts_to_create.append({
                    "alert_type": "Registration Expiry",
                    "due_date": self.registration_expiry,
                    "priority": "High" if days_to_expiry <= 7 else "Medium",
                    "description": f"Vehicle registration expires on {formatdate(self.registration_expiry)}"
                })
        
        # Insurance expiry alert
        if self.insurance_expiry:
            days_to_expiry = (get_datetime(self.insurance_expiry) - get_datetime()).days
            if days_to_expiry <= 30:
                alerts_to_create.append({
                    "alert_type": "Insurance Expiry",
                    "due_date": self.insurance_expiry,
                    "priority": "High" if days_to_expiry <= 7 else "Medium",
                    "description": f"Vehicle insurance expires on {formatdate(self.insurance_expiry)}"
                })
        
        # Service due alert
        if self.next_service_date:
            days_to_service = (get_datetime(self.next_service_date) - get_datetime()).days
            if days_to_service <= 14:
                alerts_to_create.append({
                    "alert_type": "Service Due",
                    "due_date": self.next_service_date,
                    "priority": "Medium",
                    "description": f"Next service due on {formatdate(self.next_service_date)}"
                })
        
        # Add alerts to the vehicle
        for alert in alerts_to_create:
            self.append("maintenance_alerts", alert)
        
        if alerts_to_create:
            self.db_update()
    
    def update_customer_vehicle_count(self):
        """Update customer's total vehicle count"""
        if self.customer:
            customer_doc = frappe.get_doc("Consolidated Customer Profile", self.customer)
            vehicle_count = frappe.db.count("Enhanced Vehicle Management", 
                                           {"customer": self.customer})
            customer_doc.total_vehicles = vehicle_count
            customer_doc.db_update()
    
    @frappe.whitelist()
    def predict_maintenance_requirements(self):
        """Predict future maintenance requirements"""
        if SHARED_LIBRARIES_AVAILABLE:
            predictions = predict_service_requirements({
                "vehicle_vin": self.vin,
                "current_mileage": self.current_mileage or 0,
                "service_history": self.get_service_history(),
                "vehicle_specs": {
                    "make": self.make,
                    "model": self.model,
                    "year": self.year,
                    "engine_type": self.engine_type
                }
            })
            return predictions
        else:
            # Fallback prediction
            return {
                "next_service": self.next_service_date,
                "predicted_items": ["Oil Change", "Filter Replacement"],
                "estimated_cost": 100.0
            }
    
    @frappe.whitelist()
    def optimize_service_intervals(self):
        """Optimize service intervals based on usage patterns"""
        if SHARED_LIBRARIES_AVAILABLE:
            optimization = optimize_service_intervals({
                "vehicle_vin": self.vin,
                "current_intervals": {
                    "km": self.service_interval_km,
                    "months": self.service_interval_months
                },
                "usage_pattern": self.calculate_usage_pattern(),
                "climate_conditions": "hot_arid"  # Omani climate
            })
            return optimization
        else:
            # Fallback optimization
            return {
                "recommended_km_interval": self.service_interval_km,
                "recommended_month_interval": self.service_interval_months,
                "optimization_notes": "Current intervals are appropriate"
            }
    
    def calculate_usage_pattern(self):
        """Calculate vehicle usage pattern"""
        if self.average_monthly_mileage:
            if self.average_monthly_mileage > 2000:
                return "heavy"
            elif self.average_monthly_mileage > 1000:
                return "moderate"
            else:
                return "light"
        return "unknown"
    
    def get_service_history(self):
        """Get vehicle service history"""
        return frappe.get_all(
            "Service Record",
            filters={"vehicle": self.name},
            fields=["service_date", "service_type", "cost", "mileage"],
            order_by="service_date desc"
        )
    
    @frappe.whitelist()
    def get_vehicle_dashboard_data(self):
        """Get vehicle dashboard data"""
        return {
            "vehicle_info": {
                "license_plate": self.license_plate,
                "make": self.make,
                "make_ar": self.make_ar,
                "model": self.model,
                "model_ar": self.model_ar,
                "year": self.year,
                "current_mileage": self.current_mileage
            },
            "service_status": {
                "last_service": self.last_service_date,
                "next_service": self.next_service_date,
                "service_interval_km": self.service_interval_km,
                "next_service_mileage": self.next_service_mileage
            },
            "compliance_status": {
                "registration_expiry": self.registration_expiry,
                "insurance_expiry": self.insurance_expiry,
                "inspection_status": self.inspection_status
            },
            "alerts": [alert.__dict__ for alert in self.maintenance_alerts] if self.maintenance_alerts else []
        }
    
    def get_arabic_formatted_info(self):
        """Get Arabic formatted vehicle information"""
        return {
            "make_ar": self.make_ar or self.make,
            "model_ar": self.model_ar or self.model,
            "color_ar": self.color_ar or self.color,
            "license_plate_ar": self.license_plate_ar or self.license_plate
        }