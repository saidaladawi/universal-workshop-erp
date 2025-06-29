# pylint: disable=no-member
import frappe
from frappe import _
from frappe.model.document import Document


class VehicleModel(Document):
    """Vehicle Model DocType for managing car models with Arabic localization"""

    def validate(self):
        """Validate vehicle model data"""
        self.validate_model_name()
        self.validate_year_range()
        self.set_arabic_name_if_empty()
        self.validate_make_exists()

    def validate_model_name(self):
        """Ensure model name is properly formatted and unique within make"""
        if self.model_name:
            # Capitalize first letter of each word
            self.model_name = self.model_name.title()

            # Check for duplicate model names within the same make
            existing = frappe.db.sql(
                """
                SELECT name FROM `tabVehicle Model`
                WHERE vehicle_make = %s
                AND UPPER(model_name) = %s
                AND name != %s
            """,
                [self.vehicle_make, self.model_name.upper(), self.name or ""],
            )

            if existing:
                frappe.throw(_("Model '{0}' already exists for this make").format(self.model_name))

    def validate_year_range(self):
        """Validate model year range"""
        current_year = frappe.utils.now_datetime().year

        if self.model_year_start and (
            self.model_year_start < 1900 or self.model_year_start > current_year + 2
        ):
            frappe.throw(
                _("Model Year Start must be between 1900 and {0}").format(current_year + 2)
            )

        if self.model_year_end:
            if self.model_year_end < 1900 or self.model_year_end > current_year + 2:
                frappe.throw(
                    _("Model Year End must be between 1900 and {0}").format(current_year + 2)
                )

            if self.model_year_start and self.model_year_end < self.model_year_start:
                frappe.throw(_("Model Year End cannot be earlier than Model Year Start"))

    def set_arabic_name_if_empty(self):
        """Set Arabic name if not provided using common translations"""
        if self.model_name and not self.model_name_ar:
            arabic_translations = {
                # Toyota Models
                "Camry": "كامري",
                "Corolla": "كورولا",
                "Prius": "بريوس",
                "RAV4": "راف فور",
                "Highlander": "هايلاندر",
                "Land Cruiser": "لاند كروزر",
                "Hilux": "هايلكس",
                # Honda Models
                "Civic": "سيفيك",
                "Accord": "أكورد",
                "CR-V": "سي آر في",
                "Pilot": "بايلوت",
                "Odyssey": "أوديسي",
                # BMW Models
                "X5": "إكس فايف",
                "X3": "إكس ثري",
                "3 Series": "الفئة الثالثة",
                "5 Series": "الفئة الخامسة",
                "7 Series": "الفئة السابعة",
                # Mercedes Models
                "C-Class": "الفئة سي",
                "E-Class": "الفئة إي",
                "S-Class": "الفئة إس",
                "GLE": "جي إل إي",
                "GLS": "جي إل إس",
                # Nissan Models
                "Altima": "التيما",
                "Maxima": "ماكسيما",
                "Sentra": "سنترا",
                "Patrol": "باترول",
                "X-Trail": "إكس تريل",
                # Ford Models
                "F-150": "إف ١٥٠",
                "Explorer": "إكسبلورر",
                "Mustang": "موستانغ",
                "Focus": "فوكاس",
                "Fusion": "فيوجن",
                # Common Terms
                "Sedan": "سيدان",
                "Hatchback": "هاتشباك",
                "SUV": "دفع رباعي",
                "Pickup": "بيك أب",
                "Coupe": "كوبيه",
            }

            self.model_name_ar = arabic_translations.get(self.model_name, self.model_name)

    def validate_make_exists(self):
        """Validate that the vehicle make exists and is active"""
        if self.vehicle_make:
            make_doc = frappe.get_value(
                "Vehicle Make", self.vehicle_make, ["is_active"], as_dict=True
            )
            if not make_doc:
                frappe.throw(_("Vehicle Make '{0}' does not exist").format(self.vehicle_make))
            if not make_doc.is_active:
                frappe.throw(_("Vehicle Make '{0}' is not active").format(self.vehicle_make))

    def before_save(self):
        """Actions before saving the document"""
        # Set full model display name
        if self.vehicle_make and self.model_name:
            make_name = frappe.get_value("Vehicle Make", self.vehicle_make, "make_name")
            self.full_model_name = f"{make_name} {self.model_name}"

    def on_update(self):
        """Actions after updating the document"""
        # Update Vehicle DocType records if model name changed
        if self.has_value_changed("model_name"):
            self.update_linked_vehicles()

    def update_linked_vehicles(self):
        """Update linked vehicle records when model name changes"""
        vehicles = frappe.get_all("Vehicle", filters={"model": self.name}, fields=["name"])

        for vehicle in vehicles:
            vehicle_doc = frappe.get_doc("Vehicle", vehicle.name)
            vehicle_doc.model_display = f"{self.model_name} ({self.model_name_ar})"
            vehicle_doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_models_by_make(make):
    """Get all models for a specific vehicle make"""
    if not make:
        return []

    return frappe.get_list(
        "Vehicle Model",
        filters={"vehicle_make": make, "is_active": 1},
        fields=["name", "model_name", "model_name_ar", "model_year_start", "model_year_end"],
        order_by="model_name asc",
    )


@frappe.whitelist()
def search_models(query="", make=""):
    """Search vehicle models in both English and Arabic"""
    if not query:
        return []

    search_pattern = f"%{query}%"
    conditions = "is_active = 1 AND (model_name LIKE %s OR model_name_ar LIKE %s)"
    params = [search_pattern, search_pattern]

    if make:
        conditions += " AND vehicle_make = %s"
        params.append(make)

    models = frappe.db.sql(
        f"""
        SELECT name, model_name, model_name_ar, vehicle_make,
               model_year_start, model_year_end
        FROM `tabVehicle Model`
        WHERE {conditions}
        ORDER BY
            CASE WHEN model_name LIKE %s THEN 0 ELSE 1 END,
            model_name ASC
        LIMIT 10
    """,
        [*params, query],
        as_dict=True,
    )

    return models


@frappe.whitelist()
def get_model_specifications(model_name):
    """Get detailed specifications for a vehicle model"""
    return frappe.get_value(
        "Vehicle Model",
        model_name,
        [
            "body_type",
            "fuel_type",
            "transmission_type",
            "engine_displacement",
            "engine_cylinders",
            "drive_type",
        ],
        as_dict=True,
    )
