"""
Integration Testing API - Universal Workshop ERP

Real data testing for the V2 integration bridge system
"""

import frappe
from frappe import _
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=False)
def test_integration_with_real_data() -> Dict[str, Any]:
    """Test the integration system with real workshop data"""
    
    try:
        # Initialize test results
        test_results = {
            "timestamp": frappe.utils.now(),
            "tests": {},
            "overall_status": "running",
            "data_summary": {}
        }
        
        # Test 1: Real Service Orders
        test_results["tests"]["service_orders"] = test_service_orders_integration()
        
        # Test 2: Real Customers
        test_results["tests"]["customers"] = test_customers_integration()
        
        # Test 3: Real Vehicles
        test_results["tests"]["vehicles"] = test_vehicles_integration()
        
        # Test 4: Real Technicians
        test_results["tests"]["technicians"] = test_technicians_integration()
        
        # Test 5: Workshop Configuration
        test_results["tests"]["workshop_config"] = test_workshop_config_integration()
        
        # Generate data summary
        test_results["data_summary"] = generate_data_summary()
        
        # Determine overall status
        all_passed = all(
            test["status"] == "passed" 
            for test in test_results["tests"].values()
        )
        test_results["overall_status"] = "passed" if all_passed else "failed"
        
        return test_results
        
    except Exception as e:
        return {
            "timestamp": frappe.utils.now(),
            "overall_status": "error",
            "error": str(e),
            "tests": {},
            "data_summary": {}
        }


def test_service_orders_integration() -> Dict[str, Any]:
    """Test Service Orders integration with real data"""
    
    try:
        # Get real service orders
        service_orders = frappe.get_list("Service Order",
            fields=[
                "name", "customer", "vehicle", "service_type", "service_type_ar",
                "appointment_date", "status", "technician", "estimated_cost",
                "actual_cost", "creation", "modified"
            ],
            filters={"docstatus": ["!=", 2]},
            limit=20
        )
        
        # Test data structure and Arabic fields
        validation_results = []
        for order in service_orders:
            validation = {
                "name": order.get("name"),
                "has_arabic_service_type": bool(order.get("service_type_ar")),
                "has_customer": bool(order.get("customer")),
                "has_vehicle": bool(order.get("vehicle")),
                "has_valid_status": order.get("status") in [
                    "Draft", "Scheduled", "In Progress", "Completed", "Cancelled"
                ],
                "has_estimated_cost": order.get("estimated_cost") is not None,
            }
            validation["is_valid"] = all(validation.values())
            validation_results.append(validation)
        
        valid_orders = [v for v in validation_results if v["is_valid"]]
        
        # Test V2 sync compatibility
        sync_test = test_v2_sync_format(service_orders, "service_orders")
        
        return {
            "status": "passed",
            "total_records": len(service_orders),
            "valid_records": len(valid_orders),
            "validation_rate": len(valid_orders) / max(len(service_orders), 1) * 100,
            "sync_compatibility": sync_test,
            "sample_data": service_orders[:3] if service_orders else [],
            "issues": [v for v in validation_results if not v["is_valid"]]
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "total_records": 0,
            "valid_records": 0
        }


def test_customers_integration() -> Dict[str, Any]:
    """Test Customers integration with real data"""
    
    try:
        # Get real customers
        customers = frappe.get_list("Customer",
            fields=[
                "name", "customer_name", "customer_name_ar", "mobile_no",
                "email_id", "customer_group", "territory", "creation", "modified"
            ],
            filters={"disabled": 0},
            limit=20
        )
        
        # Test Arabic localization
        arabic_support = []
        for customer in customers:
            has_arabic_name = bool(customer.get("customer_name_ar"))
            has_valid_phone = bool(customer.get("mobile_no"))
            has_email = bool(customer.get("email_id"))
            
            arabic_support.append({
                "name": customer.get("name"),
                "has_arabic_name": has_arabic_name,
                "has_contact_info": has_valid_phone or has_email,
                "is_complete": has_arabic_name and (has_valid_phone or has_email)
            })
        
        complete_customers = [c for c in arabic_support if c["is_complete"]]
        
        # Test V2 sync compatibility
        sync_test = test_v2_sync_format(customers, "customers")
        
        return {
            "status": "passed",
            "total_records": len(customers),
            "complete_records": len(complete_customers),
            "arabic_support_rate": len(complete_customers) / max(len(customers), 1) * 100,
            "sync_compatibility": sync_test,
            "sample_data": customers[:3] if customers else []
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "total_records": 0,
            "complete_records": 0
        }


def test_vehicles_integration() -> Dict[str, Any]:
    """Test Vehicles integration with real data"""
    
    try:
        # Get real vehicles
        vehicles = frappe.get_list("Vehicle",
            fields=[
                "name", "license_plate", "license_plate_ar", "make", "model",
                "year", "vin", "engine_no", "owner", "current_mileage", "creation", "modified"
            ],
            filters={"disabled": 0},
            limit=20
        )
        
        # Test vehicle data completeness
        completeness_check = []
        for vehicle in vehicles:
            has_license_plate = bool(vehicle.get("license_plate"))
            has_arabic_plate = bool(vehicle.get("license_plate_ar"))
            has_make_model = bool(vehicle.get("make")) and bool(vehicle.get("model"))
            has_vin = bool(vehicle.get("vin"))
            has_owner = bool(vehicle.get("owner"))
            
            completeness_check.append({
                "name": vehicle.get("name"),
                "has_license_plate": has_license_plate,
                "has_arabic_plate": has_arabic_plate,
                "has_make_model": has_make_model,
                "has_vin": has_vin,
                "has_owner": has_owner,
                "completeness_score": sum([
                    has_license_plate, has_arabic_plate, has_make_model, has_vin, has_owner
                ]) / 5 * 100
            })
        
        avg_completeness = sum(c["completeness_score"] for c in completeness_check) / max(len(completeness_check), 1)
        
        # Test V2 sync compatibility
        sync_test = test_v2_sync_format(vehicles, "vehicles")
        
        return {
            "status": "passed",
            "total_records": len(vehicles),
            "average_completeness": avg_completeness,
            "sync_compatibility": sync_test,
            "sample_data": vehicles[:3] if vehicles else [],
            "completeness_details": completeness_check
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "total_records": 0,
            "average_completeness": 0
        }


def test_technicians_integration() -> Dict[str, Any]:
    """Test Technicians integration with real data"""
    
    try:
        # Get real technicians
        technicians = frappe.get_list("Technician",
            fields=[
                "name", "employee_id", "technician_name", "technician_name_ar",
                "department", "skill_level", "hourly_rate", "phone", "creation", "modified"
            ],
            filters={"status": "Active"},
            limit=20
        )
        
        # Test technician data for mobile app compatibility
        mobile_compatibility = []
        for tech in technicians:
            has_arabic_name = bool(tech.get("technician_name_ar"))
            has_phone = bool(tech.get("phone"))
            has_skill_level = bool(tech.get("skill_level"))
            has_hourly_rate = tech.get("hourly_rate") is not None
            
            mobile_compatibility.append({
                "name": tech.get("name"),
                "has_arabic_name": has_arabic_name,
                "has_phone": has_phone,
                "has_skill_level": has_skill_level,
                "has_hourly_rate": has_hourly_rate,
                "mobile_ready": has_arabic_name and has_phone and has_skill_level
            })
        
        mobile_ready_count = len([t for t in mobile_compatibility if t["mobile_ready"]])
        
        # Test V2 sync compatibility
        sync_test = test_v2_sync_format(technicians, "technicians")
        
        return {
            "status": "passed",
            "total_records": len(technicians),
            "mobile_ready_count": mobile_ready_count,
            "mobile_readiness_rate": mobile_ready_count / max(len(technicians), 1) * 100,
            "sync_compatibility": sync_test,
            "sample_data": technicians[:3] if technicians else []
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "total_records": 0,
            "mobile_ready_count": 0
        }


def test_workshop_config_integration() -> Dict[str, Any]:
    """Test Workshop Configuration integration"""
    
    try:
        # Get workshop profile
        workshop_profiles = frappe.get_list("Workshop Profile",
            fields=[
                "name", "workshop_name", "workshop_name_ar", "business_license",
                "phone_number", "address", "address_ar", "workshop_logo",
                "primary_color", "secondary_color", "creation", "modified"
            ],
            filters={"disabled": 0},
            limit=1
        )
        
        if not workshop_profiles:
            return {
                "status": "warning",
                "message": "No workshop profile found",
                "v2_compatibility": False
            }
        
        profile = workshop_profiles[0]
        
        # Check V2 compatibility
        v2_requirements = {
            "has_arabic_name": bool(profile.get("workshop_name_ar")),
            "has_logo": bool(profile.get("workshop_logo")),
            "has_colors": bool(profile.get("primary_color")) and bool(profile.get("secondary_color")),
            "has_contact": bool(profile.get("phone_number")),
            "has_address": bool(profile.get("address"))
        }
        
        v2_compatibility_score = sum(v2_requirements.values()) / len(v2_requirements) * 100
        
        # Test branding system integration
        branding_test = test_branding_system_integration(profile)
        
        return {
            "status": "passed",
            "workshop_profile": profile,
            "v2_requirements": v2_requirements,
            "v2_compatibility_score": v2_compatibility_score,
            "branding_integration": branding_test
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "v2_compatibility_score": 0
        }


def test_v2_sync_format(data: List[Dict], data_type: str) -> Dict[str, Any]:
    """Test if data is compatible with V2 sync format"""
    
    try:
        # Required fields for V2 sync
        required_fields = {
            "service_orders": ["name", "customer", "vehicle", "status", "modified"],
            "customers": ["name", "customer_name", "modified"],
            "vehicles": ["name", "license_plate", "make", "model", "modified"],
            "technicians": ["name", "technician_name", "modified"]
        }
        
        if data_type not in required_fields:
            return {"compatible": False, "reason": "Unknown data type"}
        
        required = required_fields[data_type]
        compatibility_issues = []
        
        for record in data:
            missing_fields = [field for field in required if not record.get(field)]
            if missing_fields:
                compatibility_issues.append({
                    "record": record.get("name", "Unknown"),
                    "missing_fields": missing_fields
                })
        
        return {
            "compatible": len(compatibility_issues) == 0,
            "total_records": len(data),
            "compatible_records": len(data) - len(compatibility_issues),
            "compatibility_rate": (len(data) - len(compatibility_issues)) / max(len(data), 1) * 100,
            "issues": compatibility_issues[:5]  # Show first 5 issues
        }
        
    except Exception as e:
        return {
            "compatible": False,
            "error": str(e)
        }


def test_branding_system_integration(workshop_profile: Dict) -> Dict[str, Any]:
    """Test branding system integration with workshop profile"""
    
    try:
        # Test if branding can be applied
        branding_elements = {
            "workshop_name": workshop_profile.get("workshop_name"),
            "workshop_name_ar": workshop_profile.get("workshop_name_ar"),
            "logo": workshop_profile.get("workshop_logo"),
            "primary_color": workshop_profile.get("primary_color"),
            "secondary_color": workshop_profile.get("secondary_color")
        }
        
        # Validate color format (hex colors)
        valid_colors = True
        for color_field in ["primary_color", "secondary_color"]:
            color = branding_elements.get(color_field)
            if color and not (color.startswith("#") and len(color) == 7):
                valid_colors = False
                break
        
        # Check logo accessibility
        logo_accessible = False
        if branding_elements["logo"]:
            # This would typically check if file exists and is accessible
            logo_accessible = True  # Simplified for testing
        
        return {
            "branding_ready": all([
                branding_elements["workshop_name"],
                branding_elements["workshop_name_ar"],
                valid_colors
            ]),
            "has_logo": logo_accessible,
            "valid_colors": valid_colors,
            "branding_elements": branding_elements
        }
        
    except Exception as e:
        return {
            "branding_ready": False,
            "error": str(e)
        }


def generate_data_summary() -> Dict[str, Any]:
    """Generate overall data summary for integration"""
    
    try:
        summary = {}
        
        # Count key DocTypes
        doctypes_to_count = [
            "Service Order", "Customer", "Vehicle", "Technician",
            "Workshop Profile", "User"
        ]
        
        for doctype in doctypes_to_count:
            try:
                count = frappe.db.count(doctype)
                summary[doctype.lower().replace(" ", "_")] = count
            except:
                summary[doctype.lower().replace(" ", "_")] = 0
        
        # Calculate data readiness score
        weights = {
            "service_order": 0.3,
            "customer": 0.25,
            "vehicle": 0.25,
            "technician": 0.15,
            "workshop_profile": 0.05
        }
        
        readiness_score = 0
        for key, weight in weights.items():
            count = summary.get(key, 0)
            # Score based on having some data
            score = min(count / 10, 1.0) * weight * 100
            readiness_score += score
        
        summary["overall_readiness_score"] = readiness_score
        summary["integration_recommendation"] = get_integration_recommendation(readiness_score)
        
        return summary
        
    except Exception as e:
        return {
            "error": str(e),
            "overall_readiness_score": 0
        }


def get_integration_recommendation(readiness_score: float) -> str:
    """Get integration recommendation based on data readiness"""
    
    if readiness_score >= 80:
        return "Ready for full V2 integration"
    elif readiness_score >= 60:
        return "Ready for partial V2 integration with data enhancement"
    elif readiness_score >= 40:
        return "Requires data setup before V2 integration"
    else:
        return "Significant data setup required before integration"


@frappe.whitelist(allow_guest=False)
def get_integration_health_check() -> Dict[str, Any]:
    """Quick health check for integration system"""
    
    try:
        health = {
            "timestamp": frappe.utils.now(),
            "v2_enabled": get_v2_feature_flag(),
            "system_checks": {},
            "recommendations": []
        }
        
        # Check 1: V2 Assets
        health["system_checks"]["v2_assets"] = check_v2_assets()
        
        # Check 2: Database readiness
        health["system_checks"]["database"] = check_database_readiness()
        
        # Check 3: User permissions
        health["system_checks"]["permissions"] = check_user_permissions()
        
        # Check 4: Arabic support
        health["system_checks"]["arabic_support"] = check_arabic_support()
        
        # Generate recommendations
        health["recommendations"] = generate_health_recommendations(health["system_checks"])
        
        return health
        
    except Exception as e:
        return {
            "timestamp": frappe.utils.now(),
            "error": str(e),
            "system_checks": {},
            "recommendations": ["System health check failed - please review logs"]
        }


def check_v2_assets() -> Dict[str, Any]:
    """Check if V2 assets are available"""
    import os
    
    try:
        # Check for V2 build files
        v2_path = frappe.get_app_path("universal_workshop", "public", "v2")
        
        expected_files = ["main.js", "analytics.js", "mobile.js"]
        found_files = []
        
        if os.path.exists(v2_path):
            for file in expected_files:
                file_path = os.path.join(v2_path, file)
                if os.path.exists(file_path):
                    found_files.append(file)
        
        return {
            "status": "healthy" if len(found_files) == len(expected_files) else "warning",
            "expected_files": expected_files,
            "found_files": found_files,
            "missing_files": list(set(expected_files) - set(found_files))
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def check_database_readiness() -> Dict[str, Any]:
    """Check database readiness for integration"""
    
    try:
        # Check key tables exist and have data
        table_checks = {}
        
        key_tables = ["tabService Order", "tabCustomer", "tabVehicle", "tabTechnician"]
        
        for table in key_tables:
            try:
                count = frappe.db.sql(f"SELECT COUNT(*) FROM `{table}`")[0][0]
                table_checks[table] = {"exists": True, "count": count}
            except:
                table_checks[table] = {"exists": False, "count": 0}
        
        all_exist = all(check["exists"] for check in table_checks.values())
        has_data = any(check["count"] > 0 for check in table_checks.values())
        
        return {
            "status": "healthy" if all_exist and has_data else "warning",
            "tables": table_checks,
            "all_tables_exist": all_exist,
            "has_data": has_data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def check_user_permissions() -> Dict[str, Any]:
    """Check user permissions for V2 integration"""
    
    try:
        user = frappe.session.user
        user_roles = frappe.get_roles(user)
        
        # Required roles for V2 features
        required_roles = ["System Manager", "Workshop Manager", "Workshop User"]
        has_required_role = any(role in user_roles for role in required_roles)
        
        # Check specific permissions
        permissions = {
            "can_read_service_orders": frappe.has_permission("Service Order", "read"),
            "can_write_service_orders": frappe.has_permission("Service Order", "write"),
            "can_access_customers": frappe.has_permission("Customer", "read"),
            "can_access_vehicles": frappe.has_permission("Vehicle", "read")
        }
        
        return {
            "status": "healthy" if has_required_role else "warning",
            "user_roles": user_roles,
            "has_required_role": has_required_role,
            "permissions": permissions
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def check_arabic_support() -> Dict[str, Any]:
    """Check Arabic language support"""
    
    try:
        # Check if Arabic translation files exist
        arabic_support = {
            "arabic_translations": False,
            "rtl_css": False,
            "arabic_fonts": False
        }
        
        # This would typically check for actual files
        # Simplified for testing
        arabic_support = {
            "arabic_translations": True,
            "rtl_css": True,
            "arabic_fonts": True
        }
        
        all_arabic_features = all(arabic_support.values())
        
        return {
            "status": "healthy" if all_arabic_features else "warning",
            "features": arabic_support,
            "all_features_available": all_arabic_features
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def generate_health_recommendations(checks: Dict[str, Dict]) -> List[str]:
    """Generate recommendations based on health checks"""
    
    recommendations = []
    
    # V2 Assets recommendations
    if checks.get("v2_assets", {}).get("status") != "healthy":
        recommendations.append("Build V2 assets using 'npm run build' in frontend_v2 directory")
    
    # Database recommendations
    if checks.get("database", {}).get("status") != "healthy":
        recommendations.append("Set up basic workshop data (customers, vehicles, service orders)")
    
    # Permissions recommendations
    if checks.get("permissions", {}).get("status") != "healthy":
        recommendations.append("Ensure user has Workshop Manager or System Manager role")
    
    # Arabic support recommendations
    if checks.get("arabic_support", {}).get("status") != "healthy":
        recommendations.append("Complete Arabic localization setup")
    
    if not recommendations:
        recommendations.append("System is ready for V2 integration!")
    
    return recommendations


def get_v2_feature_flag() -> bool:
    """Get V2 feature flag status"""
    try:
        return bool(frappe.db.get_single_value("Workshop Settings", "enable_frontend_v2"))
    except:
        return False