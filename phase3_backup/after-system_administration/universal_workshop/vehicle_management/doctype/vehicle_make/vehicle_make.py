# pylint: disable=no-member
import frappe
from frappe import _
from frappe.model.document import Document


class VehicleMake(Document):
    """Vehicle Make DocType for managing car manufacturers with Arabic localization"""

    def validate(self):
        """Validate vehicle make data"""
        self.validate_make_name()
        self.set_arabic_name_if_empty()
        self.validate_sort_order()

    def validate_make_name(self):
        """Ensure make name is properly formatted"""
        if self.make_name:
            # Capitalize first letter of each word
            self.make_name = self.make_name.title()

            # Check for duplicate make names (case-insensitive)
            existing = frappe.db.sql(
                """
                SELECT name FROM `tabVehicle Make`
                WHERE UPPER(make_name) = %s AND name != %s
            """,
                [self.make_name.upper(), self.name or ""],
            )

            if existing:
                frappe.throw(_("Vehicle Make '{0}' already exists").format(self.make_name))

    def set_arabic_name_if_empty(self):
        """Set Arabic name if not provided using common translations"""
        if self.make_name and not self.make_name_ar:
            arabic_translations = {
                "Toyota": "تويوتا",
                "Honda": "هوندا",
                "BMW": "بي إم دبليو",
                "Mercedes-Benz": "مرسيدس بنز",
                "Audi": "أودي",
                "Ford": "فورد",
                "Chevrolet": "شيفروليه",
                "Nissan": "نيسان",
                "Hyundai": "هيونداي",
                "Kia": "كيا",
                "Volkswagen": "فولكس فاغن",
                "Mazda": "مازدا",
                "Subaru": "سوبارو",
                "Mitsubishi": "ميتسوبيشي",
                "Lexus": "لكزس",
                "Infiniti": "إنفينيتي",
                "Acura": "أكورا",
                "Volvo": "فولفو",
                "Jaguar": "جاجوار",
                "Land Rover": "لاند روفر",
                "Porsche": "بورش",
                "Ferrari": "فيراري",
                "Lamborghini": "لامبورغيني",
            }

            self.make_name_ar = arabic_translations.get(self.make_name, self.make_name)

    def validate_sort_order(self):
        """Ensure sort order is positive"""
        if self.sort_order and self.sort_order < 0:
            frappe.throw(_("Sort Order must be a positive number"))

    def before_save(self):
        """Actions before saving the document"""
        if not self.sort_order:
            # Get next sort order
            max_sort = (
                frappe.db.sql(
                    """
                SELECT MAX(sort_order) FROM `tabVehicle Make`
            """
                )[0][0]
                or 0
            )
            self.sort_order = max_sort + 10

    def on_update(self):
        """Actions after updating the document"""
        # Update Vehicle DocType records if make name changed
        if self.has_value_changed("make_name"):
            self.update_linked_vehicles()

    def update_linked_vehicles(self):
        """Update linked vehicle records when make name changes"""
        vehicles = frappe.get_all("Vehicle", filters={"make": self.name}, fields=["name"])

        for vehicle in vehicles:
            vehicle_doc = frappe.get_doc("Vehicle", vehicle.name)
            vehicle_doc.make_display = f"{self.make_name} ({self.make_name_ar})"
            vehicle_doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_popular_makes():
    """Get list of popular vehicle makes for quick selection"""
    return frappe.get_list(
        "Vehicle Make",
        filters={"is_active": 1},
        fields=["name", "make_name", "make_name_ar", "logo_image"],
        order_by="sort_order asc",
        limit=20,
    )


@frappe.whitelist()
def search_makes(query=""):
    """Search vehicle makes in both English and Arabic"""
    if not query:
        return []

    search_pattern = f"%{query}%"

    makes = frappe.db.sql(
        """
        SELECT name, make_name, make_name_ar, logo_image
        FROM `tabVehicle Make`
        WHERE is_active = 1
        AND (make_name LIKE %s OR make_name_ar LIKE %s)
        ORDER BY
            CASE WHEN make_name LIKE %s THEN 0 ELSE 1 END,
            sort_order ASC
        LIMIT 10
    """,
        [search_pattern, search_pattern, query],
        as_dict=True,
    )

    return makes
