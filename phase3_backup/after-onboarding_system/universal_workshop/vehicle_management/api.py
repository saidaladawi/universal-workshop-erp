import re

import frappe
from frappe import _
import requests
import json
from datetime import datetime, timedelta


@frappe.whitelist()
def get_vehicles_by_customer(customer, language="en"):
    """Get all vehicles for a specific customer"""
    if not customer:
        frappe.throw(_("Customer is required"))

    # Fields to retrieve
    fields = [
        "name",
        "vin",
        "license_plate",
        "license_plate_ar",
        "make",
        "model",
        "year",
        "color",
        "color_ar",
        "current_mileage",
        "vehicle_status",
        "ownership_type",
    ]

    try:
        vehicles = frappe.get_list(
            "Vehicle",
            filters={"customer": customer},
            fields=fields,
            order_by="year desc, make, model",
        )

        # Format vehicles for display
        for vehicle in vehicles:
            # Create display name
            display_parts = []
            if vehicle.get("year"):
                display_parts.append(str(vehicle["year"]))
            if vehicle.get("make"):
                display_parts.append(vehicle["make"])
            if vehicle.get("model"):
                display_parts.append(vehicle["model"])
            if vehicle.get("license_plate"):
                display_parts.append(f"({vehicle['license_plate']})")

            vehicle["display_name"] = " ".join(display_parts)

            # Use Arabic names if language is Arabic and available
            if language == "ar" and vehicle.get("license_plate_ar"):
                vehicle["license_plate"] = vehicle["license_plate_ar"]
            if vehicle.get("color_ar"):
                vehicle["color"] = vehicle["color_ar"]

        return vehicles

    except Exception as e:
        frappe.log_error(f"Error fetching vehicles for customer {customer}: {e!s}")
        return []


@frappe.whitelist()
def search_vehicles(query, limit=20):
    """Search vehicles by VIN, license plate, or make/model with security"""
    if not query or len(query.strip()) < 2:
        return []

    # Sanitize inputs
    query = frappe.db.escape(query.strip())
    limit = int(limit) if str(limit).isdigit() else 20

    try:
        # Use parameterized query for security
        search_pattern = f"%{query}%"

        vehicles = frappe.db.sql(
            """
            SELECT
                name, vin, license_plate, make, model, year,
                customer, color, current_mileage
            FROM `tabVehicle`
            WHERE
                vin LIKE %s
                OR license_plate LIKE %s
                OR make LIKE %s
                OR model LIKE %s
                OR license_plate_ar LIKE %s
                OR make_ar LIKE %s
                OR model_ar LIKE %s
            ORDER BY
                CASE
                    WHEN vin = %s THEN 1
                    WHEN license_plate = %s THEN 2
                    WHEN make = %s THEN 3
                    ELSE 4
                END,
                make, model, year DESC
            LIMIT %s
        """,
            [
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                query,
                query,
                query,
                limit,
            ],
            as_dict=True,
        )

        return vehicles

    except Exception as e:
        frappe.log_error(f"Error in vehicle search: {e}")
        return []


@frappe.whitelist()
def validate_vin(vin):
    """Validate VIN format and check for duplicates"""
    if not vin:
        return {"valid": False, "message": _("VIN is required")}

    # Remove spaces and convert to uppercase
    vin = vin.replace(" ", "").upper()

    # Check length
    if len(vin) != 17:
        return {"valid": False, "message": _("VIN must be exactly 17 characters long")}

    # Check character validity (no I, O, Q)
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
        return {
            "valid": False,
            "message": _("VIN contains invalid characters. VIN cannot contain I, O, or Q"),
        }

    # Check for duplicates
    existing = frappe.db.exists("Vehicle", {"vin": vin})
    if existing:
        return {"valid": False, "message": _("VIN already exists in the system")}

    return {"valid": True, "formatted_vin": vin, "message": _("VIN is valid")}


@frappe.whitelist()
def get_vehicle_details(vehicle_name):
    """Get detailed information for a specific vehicle"""
    if not vehicle_name:
        frappe.throw(_("Vehicle name is required"))

    try:
        vehicle = frappe.get_doc("Vehicle", vehicle_name)

        # Get maintenance alerts
        alerts = vehicle.get_maintenance_alerts()

        # Get customer details
        customer_info = None
        if vehicle.customer:
            customer_info = frappe.get_doc("Customer", vehicle.customer)

        return {
            "vehicle": vehicle.as_dict(),
            "alerts": alerts,
            "customer": customer_info.as_dict() if customer_info else None,
            "service_history": vehicle.get_service_history(),
        }

    except frappe.DoesNotExistError:
        frappe.throw(_("Vehicle not found"))
    except Exception as e:
        frappe.log_error(f"Error getting vehicle details: {e!s}")
        frappe.throw(_("Error retrieving vehicle details"))


@frappe.whitelist()
def create_vehicle_quick(customer, vin, license_plate, make, model, year):
    """Quick vehicle creation with minimal required fields"""
    try:
        # Validate required fields
        if not all([customer, vin, license_plate, make, model, year]):
            frappe.throw(_("All required fields must be provided"))

        # Validate VIN
        vin_validation = validate_vin(vin)
        if not vin_validation["valid"]:
            frappe.throw(vin_validation["message"])

        # Create vehicle
        vehicle = frappe.new_doc("Vehicle")
        vehicle.customer = customer
        vehicle.vin = vin_validation["formatted_vin"]
        vehicle.license_plate = license_plate.upper()
        vehicle.make = make
        vehicle.model = model
        vehicle.year = int(year)
        vehicle.vehicle_status = "Active"
        vehicle.ownership_type = "Owner"

        vehicle.insert()

        return {
            "success": True,
            "vehicle_name": vehicle.name,
            "message": _("Vehicle created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating vehicle: {e!s}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_vehicle_maintenance_summary(customer=None, status_filter=None):
    """Get maintenance summary for vehicles"""
    filters = {}
    if customer:
        filters["customer"] = customer
    if status_filter:
        filters["vehicle_status"] = status_filter

    try:
        vehicles = frappe.get_list(
            "Vehicle",
            filters=filters,
            fields=[
                "name",
                "vin",
                "license_plate",
                "make",
                "model",
                "year",
                "customer",
                "current_mileage",
                "last_service_date",
                "next_service_due",
                "insurance_expiry_date",
                "warranty_expiry_date",
            ],
        )

        summary = {
            "total_vehicles": len(vehicles),
            "service_due": 0,
            "insurance_expiring": 0,
            "warranty_expiring": 0,
            "vehicles": [],
        }

        import datetime

        today = datetime.date.today()
        thirty_days = today + datetime.timedelta(days=30)

        for vehicle_data in vehicles:
            vehicle_alerts = []

            # Check service due
            if vehicle_data.get("next_service_due") and vehicle_data["next_service_due"] <= today:
                summary["service_due"] += 1
                vehicle_alerts.append("service_due")

            # Check insurance expiry
            if (
                vehicle_data.get("insurance_expiry_date")
                and vehicle_data["insurance_expiry_date"] <= thirty_days
            ):
                summary["insurance_expiring"] += 1
                vehicle_alerts.append("insurance_expiring")

            # Check warranty expiry
            if (
                vehicle_data.get("warranty_expiry_date")
                and vehicle_data["warranty_expiry_date"] <= thirty_days
            ):
                summary["warranty_expiring"] += 1
                vehicle_alerts.append("warranty_expiring")

            vehicle_data["alerts"] = vehicle_alerts
            summary["vehicles"].append(vehicle_data)

        return summary

    except Exception as e:
        frappe.log_error(f"Error getting maintenance summary: {e!s}")
        return {
            "total_vehicles": 0,
            "service_due": 0,
            "insurance_expiring": 0,
            "warranty_expiring": 0,
            "vehicles": [],
        }


# =====================================
# External Vehicle API Integration
# =====================================


@frappe.whitelist()
def get_vehicle_makes_from_api(force_refresh=False):
    """Get vehicle makes from external API with caching and fallback to manual"""
    try:
        # Check cache first (unless forced refresh)
        if not force_refresh:
            cached_makes = frappe.cache().get_value("vehicle_makes_api")
            if cached_makes:
                return cached_makes

        # Try primary API - CarAPI (example)
        makes_data = fetch_from_carapi_makes()

        if not makes_data:
            # Fallback to NHTSA if CarAPI fails
            makes_data = fetch_from_nhtsa_makes()

        if makes_data:
            # Cache for 24 hours
            frappe.cache().set_value("vehicle_makes_api", makes_data, expires_in_sec=86400)
            return makes_data
        else:
            # Fallback to local manual data
            return get_local_vehicle_makes()

    except Exception as e:
        frappe.log_error(f"API Error in get_vehicle_makes: {str(e)}")
        return get_local_vehicle_makes()


def fetch_from_carapi_makes():
    """Fetch makes from CarAPI"""
    try:
        # Note: Replace with actual CarAPI endpoint and credentials
        # This is a conceptual example
        response = requests.get(
            "https://api.car-api.com/v1/makes",
            headers={"X-API-Key": get_api_key("carapi")},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            # Transform to our format
            makes = []
            for make in data.get("makes", []):
                makes.append(
                    {
                        "make_name": make.get("name"),
                        "make_name_ar": get_arabic_translation(make.get("name")),
                        "source": "CarAPI",
                        "last_updated": datetime.now(),
                    }
                )
            return makes

    except Exception as e:
        frappe.log_error(f"CarAPI Error: {str(e)}")
        return None


def fetch_from_nhtsa_makes():
    """Fetch makes from NHTSA API (free fallback)"""
    try:
        response = requests.get(
            "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json", timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            makes = []
            for make in data.get("Results", []):
                makes.append(
                    {
                        "make_name": make.get("Make_Name"),
                        "make_name_ar": get_arabic_translation(make.get("Make_Name")),
                        "source": "NHTSA",
                        "last_updated": datetime.now(),
                    }
                )
            return makes

    except Exception as e:
        frappe.log_error(f"NHTSA API Error: {str(e)}")
        return None


@frappe.whitelist()
def get_vehicle_models_from_api(make_name, year=None):
    """Get vehicle models from external API for specific make"""
    try:
        # Check cache first
        cache_key = f"vehicle_models_{make_name}_{year or 'all'}"
        cached_models = frappe.cache().get_value(cache_key)
        if cached_models:
            return cached_models

        # Try CarAPI first
        models_data = fetch_models_from_carapi(make_name, year)

        if not models_data:
            # Fallback to NHTSA
            models_data = fetch_models_from_nhtsa(make_name, year)

        if models_data:
            # Cache for 6 hours
            frappe.cache().set_value(cache_key, models_data, expires_in_sec=21600)
            return models_data
        else:
            return get_local_vehicle_models(make_name)

    except Exception as e:
        frappe.log_error(f"API Error in get_vehicle_models: {str(e)}")
        return get_local_vehicle_models(make_name)


def fetch_models_from_carapi(make_name, year):
    """Fetch models from CarAPI"""
    try:
        params = {"make": make_name}
        if year:
            params["year"] = year

        response = requests.get(
            "https://api.car-api.com/v1/models",
            headers={"X-API-Key": get_api_key("carapi")},
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append(
                    {
                        "model_name": model.get("name"),
                        "model_name_ar": get_arabic_translation(model.get("name")),
                        "year_start": model.get("year_start"),
                        "year_end": model.get("year_end"),
                        "source": "CarAPI",
                    }
                )
            return models

    except Exception as e:
        frappe.log_error(f"CarAPI Models Error: {str(e)}")
        return None


def fetch_models_from_nhtsa(make_name, year):
    """Fetch models from NHTSA API"""
    try:
        if year:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformakeyear/make/{make_name}/modelyear/{year}?format=json"
        else:
            url = (
                f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{make_name}?format=json"
            )

        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get("Results", []):
                models.append(
                    {
                        "model_name": model.get("Model_Name"),
                        "model_name_ar": get_arabic_translation(model.get("Model_Name")),
                        "source": "NHTSA",
                    }
                )
            return models

    except Exception as e:
        frappe.log_error(f"NHTSA Models Error: {str(e)}")
        return None


def get_local_vehicle_makes():
    """Get makes from local database as fallback"""
    makes = frappe.get_list(
        "Vehicle Make", fields=["make_name", "make_name_ar"], order_by="make_name"
    )
    for make in makes:
        make["source"] = "Local Database"
    return makes


def get_local_vehicle_models(make_name):
    """Get models from local database as fallback"""
    models = frappe.get_list(
        "Vehicle Model",
        filters={"make": make_name},
        fields=["model_name", "model_name_ar", "year_start", "year_end"],
        order_by="model_name",
    )
    for model in models:
        model["source"] = "Local Database"
    return models


def get_api_key(provider):
    """Get API key for provider from secure storage"""
    # Get from site config or environment variables
    api_keys = frappe.get_site_config().get("vehicle_api_keys", {})
    return api_keys.get(provider)


def get_arabic_translation(english_text):
    """Get Arabic translation for vehicle make/model names"""
    # This would connect to a translation service or local database
    # For now, return a placeholder
    translation_map = {
        "Toyota": "تويوتا",
        "Honda": "هوندا",
        "Ford": "فورد",
        "Chevrolet": "شيفروليه",
        "BMW": "بي إم دبليو",
        "Mercedes-Benz": "مرسيدس بنز",
        "Audi": "أودي",
        "Lexus": "لكزس",
        "Infiniti": "إنفينيتي",
        "Cadillac": "كاديلاك",
    }
    return translation_map.get(english_text, english_text)


@frappe.whitelist()
def sync_vehicle_data_from_apis():
    """Background job to sync vehicle data from APIs"""
    try:
        # Get fresh data from APIs
        makes = get_vehicle_makes_from_api(force_refresh=True)

        if not makes:
            return {"status": "error", "message": "Failed to fetch makes from APIs"}

        # Update local database
        updated_makes = 0
        for make_data in makes:
            if make_data.get("source") != "Local Database":
                # Check if make exists
                existing = frappe.db.exists("Vehicle Make", {"make_name": make_data["make_name"]})

                if not existing:
                    # Create new make
                    new_make = frappe.new_doc("Vehicle Make")
                    new_make.make_name = make_data["make_name"]
                    new_make.make_name_ar = make_data["make_name_ar"]
                    new_make.api_source = make_data["source"]
                    new_make.last_api_update = datetime.now()
                    new_make.insert()
                    updated_makes += 1
                else:
                    # Update existing make
                    make_doc = frappe.get_doc("Vehicle Make", existing)
                    if make_doc.make_name_ar != make_data["make_name_ar"]:
                        make_doc.make_name_ar = make_data["make_name_ar"]
                        make_doc.api_source = make_data["source"]
                        make_doc.last_api_update = datetime.now()
                        make_doc.save()
                        updated_makes += 1

        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Successfully updated {updated_makes} vehicle makes from APIs",
            "updated_count": updated_makes,
        }

    except Exception as e:
        frappe.log_error(f"Sync Error: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_api_sync_status():
    """Get status of last API synchronization"""
    try:
        # Get last sync info from cache or database
        last_sync = frappe.cache().get_value("last_vehicle_api_sync")

        if not last_sync:
            # Check database for last update
            last_updated = frappe.db.sql(
                """
                SELECT MAX(last_api_update) as last_update
                FROM `tabVehicle Make`
                WHERE api_source IS NOT NULL
            """,
                as_dict=True,
            )

            if last_updated and last_updated[0].get("last_update"):
                last_sync = {
                    "last_sync_time": last_updated[0]["last_update"],
                    "status": "completed",
                }
            else:
                last_sync = {"last_sync_time": None, "status": "never"}

        # Get counts
        api_makes_count = frappe.db.count("Vehicle Make", {"api_source": ["!=", ""]})
        manual_makes_count = frappe.db.count("Vehicle Make", {"api_source": ["in", ["", None]]})

        return {
            "last_sync": last_sync,
            "api_makes_count": api_makes_count,
            "manual_makes_count": manual_makes_count,
            "total_makes": api_makes_count + manual_makes_count,
        }

    except Exception as e:
        frappe.log_error(f"Status Error: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def cleanup_old_api_cache():
    """Clean up old API cache entries to maintain performance"""
    try:
        # Delete cache entries older than 30 days
        thirty_days_ago = frappe.utils.add_days(frappe.utils.nowdate(), -30)

        # Clean up vehicle make cache - check if table exists first
        if frappe.db.table_exists("Vehicle Make API Cache"):
            frappe.db.sql(
                """
                DELETE FROM `tabVehicle Make API Cache`
                WHERE last_synced < %s
            """,
                [thirty_days_ago],
            )

        # Clean up vehicle model cache - check if table exists first
        if frappe.db.table_exists("Vehicle Model API Cache"):
            frappe.db.sql(
                """
                DELETE FROM `tabVehicle Model API Cache`
                WHERE last_synced < %s
            """,
                [thirty_days_ago],
            )

        # Clean up old Vehicle Make entries that haven't been updated
        old_makes_count = frappe.db.sql(
            """
            DELETE FROM `tabVehicle Make`
            WHERE last_api_update < %s
            AND api_source IS NOT NULL
        """,
            [thirty_days_ago],
        )

        frappe.db.commit()

        return {
            "success": True,
            "message": _("API cache cleanup completed successfully"),
            "cleaned_entries": old_makes_count,
        }

    except Exception as e:
        frappe.log_error(f"Error during API cache cleanup: {e}")
        return {"success": False, "message": str(e)}
