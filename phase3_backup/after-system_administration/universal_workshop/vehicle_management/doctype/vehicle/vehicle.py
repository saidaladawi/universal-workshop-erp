import json
import re

import requests

import frappe
from frappe import _
from frappe.model.document import Document


class Vehicle(Document):
    def validate(self):
        """Validate vehicle data before saving"""
        self.validate_vin()
        self.validate_license_plate()
        self.validate_year()
        self.calculate_next_service()
        self.set_user_tracking()

    def validate_vin(self):
        """Validate VIN format (17 alphanumeric characters)"""
        if self.vin:
            # Remove spaces and convert to uppercase
            self.vin = self.vin.replace(" ", "").upper()

            # Check if VIN is exactly 17 characters
            if len(self.vin) != 17:
                frappe.throw(_("VIN must be exactly 17 characters long"))

            # Check if VIN contains only alphanumeric characters (excluding I, O, Q)
            if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", self.vin):
                frappe.throw(_("VIN contains invalid characters. VIN cannot contain I, O, or Q"))

    def validate_license_plate(self):
        """Validate license plate format"""
        if self.license_plate:
            # Remove extra spaces and normalize
            self.license_plate = " ".join(self.license_plate.split()).upper()

            # Basic validation - adjust for Oman license plate format if needed
            if len(self.license_plate) > 20:
                frappe.throw(_("License plate number is too long"))

    def validate_year(self):
        """Validate vehicle year"""
        if self.year:
            import datetime

            current_year = datetime.datetime.now().year

            if self.year < 1900:
                frappe.throw(_("Vehicle year cannot be before 1900"))

            if self.year > current_year + 1:
                frappe.throw(_("Vehicle year cannot be more than one year in the future"))

    def calculate_next_service(self):
        """Calculate next service due date based on mileage and interval"""
        if (
            self.last_service_date
            and self.service_interval_km
            and self.current_mileage
            and not self.next_service_due
        ):
            import datetime

            from dateutil.relativedelta import relativedelta

            # Estimate next service in 3 months or based on interval
            estimated_months = max(3, self.service_interval_km // 2000)
            self.next_service_due = self.last_service_date + relativedelta(months=estimated_months)

    def set_user_tracking(self):
        """Set user tracking fields"""
        if self.is_new():
            self.created_by_user = frappe.session.user
        self.last_updated_by = frappe.session.user

    def before_save(self):
        """Operations before saving"""
        self.set_title_field()

    def set_title_field(self):
        """Set the display title for the vehicle"""
        if self.make and self.model and self.year:
            title_parts = [str(self.year), self.make, self.model]
            if self.license_plate:
                title_parts.append(f"({self.license_plate})")
            # This will be used for display purposes
            self.vehicle_display_name = " ".join(title_parts)

    @frappe.whitelist()
    def decode_vin(self):
        """Decode VIN using NHTSA VIN decoder API to populate vehicle specifications"""
        if not self.vin:
            frappe.throw(_("VIN is required for decoding"))

        # Validate VIN format before making API call
        self.validate_vin()

        try:
            # Call NHTSA VIN decoder API
            api_url = (
                f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{self.vin}?format=json"
            )

            frappe.logger().info(f"Calling NHTSA VIN decoder API for VIN: {self.vin}")

            # Make API request with timeout
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            if data.get("Count", 0) == 0 or not data.get("Results"):
                frappe.throw(_("No vehicle data found for VIN: {0}").format(self.vin))

            # Extract vehicle data from first result
            vehicle_data = data["Results"][0]

            # Map NHTSA API fields to our DocType fields
            field_mapping = {
                "Make": "make",
                "Model": "model",
                "ModelYear": "year",
                "BodyClass": "body_class",
                "EngineCylinders": "engine_cylinders",
                "DisplacementL": "engine_displacement",
                "FuelTypePrimary": "fuel_type_primary",
                "TransmissionStyle": "transmission_type",
                "DriveType": "drive_type",
                "PlantCountry": "plant_country",
                "PlantState": "plant_state",
            }

            # Store original values to track what was updated
            updated_fields = []

            # Update fields with decoded data
            for api_field, doc_field in field_mapping.items():
                api_value = vehicle_data.get(api_field)
                if api_value and api_value.strip():
                    # Convert year to integer if it's the year field
                    if doc_field == "year":
                        try:
                            api_value = int(api_value)
                        except (ValueError, TypeError):
                            continue

                    # Only update if field is empty or user wants to override
                    current_value = getattr(self, doc_field, None)
                    if not current_value or current_value != api_value:
                        setattr(self, doc_field, api_value)
                        updated_fields.append(frappe.get_meta("Vehicle").get_label(doc_field))

                        # Generate Arabic translations for key fields
                        if doc_field == "make" and not self.make_ar:
                            self.make_ar = self.get_arabic_translation(api_value, "make")
                        elif doc_field == "model" and not self.model_ar:
                            self.model_ar = self.get_arabic_translation(api_value, "model")
                        elif doc_field == "body_class" and not self.body_class_ar:
                            self.body_class_ar = self.get_arabic_translation(
                                api_value, "body_class"
                            )

            # Additional engine type field combination
            if (
                vehicle_data.get("EngineModel")
                or vehicle_data.get("EngineCylinders")
                or vehicle_data.get("DisplacementL")
            ):
                engine_parts = []
                if vehicle_data.get("DisplacementL"):
                    engine_parts.append(f"{vehicle_data['DisplacementL']}L")
                if vehicle_data.get("EngineCylinders"):
                    engine_parts.append(
                        f"V{vehicle_data['EngineCylinders']}"
                        if int(vehicle_data.get("EngineCylinders", 0)) > 4
                        else f"I{vehicle_data['EngineCylinders']}"
                    )
                if vehicle_data.get("EngineModel"):
                    engine_parts.append(vehicle_data["EngineModel"])

                if engine_parts and not self.engine_type:
                    self.engine_type = " ".join(engine_parts)
                    updated_fields.append("Engine Type")

            # Cache the API response for future reference
            self.add_comment(
                "Comment",
                f"VIN decoded successfully via NHTSA API. Updated fields: {', '.join(updated_fields)}",
            )

            if updated_fields:
                frappe.msgprint(
                    _(
                        "VIN decoded successfully! Updated fields: {0}. Please review and save the vehicle."
                    ).format(", ".join(updated_fields))
                )
            else:
                frappe.msgprint(
                    _(
                        "VIN decoded successfully, but no new data was found or all fields were already populated."
                    )
                )

            return {"success": True, "updated_fields": updated_fields, "api_response": vehicle_data}

        except requests.exceptions.Timeout:
            frappe.throw(_("VIN decoder API request timed out. Please try again."))
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"VIN decoder API error: {e!s}", "VIN Decoder Error")
            frappe.throw(_("Error connecting to VIN decoder service. Please try again later."))
        except json.JSONDecodeError:
            frappe.throw(_("Invalid response from VIN decoder service. Please try again."))
        except Exception as e:
            frappe.log_error(f"VIN decoder unexpected error: {e!s}", "VIN Decoder Error")
            frappe.throw(
                _("An unexpected error occurred while decoding VIN. Please contact support.")
            )

    def get_arabic_translation(self, english_text, field_type):
        """Get Arabic translation for vehicle make/model/body type"""
        # This is a simplified translation mapping
        # In a real implementation, this could call a translation API or use a database
        translations = {
            "make": {
                "TOYOTA": "تويوتا",
                "HONDA": "هوندا",
                "NISSAN": "نيسان",
                "FORD": "فورد",
                "CHEVROLET": "شيفرولت",
                "BMW": "بي إم دبليو",
                "MERCEDES-BENZ": "مرسيدس بنز",
                "AUDI": "أودي",
                "VOLKSWAGEN": "فولكس فاغن",
                "HYUNDAI": "هيونداي",
                "KIA": "كيا",
                "MAZDA": "مازدا",
                "SUBARU": "سوبارو",
                "LEXUS": "لكزس",
            },
            "body_class": {
                "Sedan/Saloon": "سيدان",
                "SUV": "دفع رباعي",
                "Pickup": "بيك آب",
                "Coupe": "كوبيه",
                "Convertible": "قابل للتحويل",
                "Hatchback": "هاتشباك",
                "Wagon": "واغن",
                "Van": "فان",
                "Truck": "شاحنة",
            },
        }

        if field_type in translations and english_text.upper() in translations[field_type]:
            return translations[field_type][english_text.upper()]

        # Return empty string if no translation found - user can fill manually
        return ""

    def get_service_history(self):
        """Get service history for this vehicle"""
        # This would link to service records - placeholder for now
        return []

    def get_current_owner(self):
        """Get current owner information"""
        if self.customer:
            return frappe.get_doc("Customer", self.customer)
        return None

    def is_due_for_service(self):
        """Check if vehicle is due for service"""
        if not self.next_service_due:
            return False

        import datetime

        today = datetime.date.today()
        return self.next_service_due <= today

    def get_vehicle_age_months(self):
        """Calculate vehicle age in months"""
        if not self.year:
            return 0

        import datetime

        current_year = datetime.datetime.now().year
        datetime.datetime.now().month

        # Simple calculation - can be enhanced
        age_years = current_year - self.year
        return age_years * 12

    @frappe.whitelist()
    def get_maintenance_alerts(self):
        """Get maintenance alerts for this vehicle"""
        alerts = []

        # Check service due
        if self.is_due_for_service():
            alerts.append(
                {
                    "type": "service_due",
                    "message": _("Vehicle is due for service"),
                    "priority": "high",
                }
            )

        # Check insurance expiry
        if self.insurance_expiry_date:
            import datetime

            today = datetime.date.today()
            days_until_expiry = (self.insurance_expiry_date - today).days

            if days_until_expiry <= 30:
                alerts.append(
                    {
                        "type": "insurance_expiry",
                        "message": _("Insurance expires in {0} days").format(days_until_expiry),
                        "priority": "medium" if days_until_expiry > 7 else "high",
                    }
                )

        # Check warranty expiry
        if self.warranty_expiry_date:
            import datetime

            today = datetime.date.today()
            days_until_expiry = (self.warranty_expiry_date - today).days

            if days_until_expiry <= 90:
                alerts.append(
                    {
                        "type": "warranty_expiry",
                        "message": _("Warranty expires in {0} days").format(days_until_expiry),
                        "priority": "low",
                    }
                )

        return alerts
