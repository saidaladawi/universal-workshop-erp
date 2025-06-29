import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now_datetime
import re
import math
import json


class StorageLocation(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate storage location data before saving"""
        self.validate_arabic_names()
        self.validate_capacity_limits()
        self.validate_parent_location()
        self.validate_coordinates()
        self.validate_environmental_conditions()

    def before_save(self):
        """Set default values and generate codes before saving"""
        self.generate_location_code()
        self.generate_barcode()
        self.generate_qr_code()
        self.update_path()
        self.calculate_efficiency_metrics()

    def after_insert(self):
        """Actions after location is created"""
        self.log_location_creation()

    def validate_arabic_names(self):
        """Ensure Arabic location names are provided"""
        if not self.location_name_ar:
            frappe.throw(_("Arabic location name is required"))
        if not self.description_ar:
            frappe.throw(_("Arabic description is required"))

    def validate_capacity_limits(self):
        """Validate capacity settings"""
        if self.max_weight_kg and self.max_weight_kg <= 0:
            frappe.throw(_("Maximum weight must be positive"))
        if self.max_volume_m3 and self.max_volume_m3 <= 0:
            frappe.throw(_("Maximum volume must be positive"))
        if self.max_items and self.max_items <= 0:
            frappe.throw(_("Maximum items must be positive"))

    def validate_parent_location(self):
        """Validate parent location relationship"""
        if self.parent_location:
            if self.parent_location == self.name:
                frappe.throw(_("Location cannot be its own parent"))
            # Check for circular references
            self.check_circular_reference(self.parent_location)

    def check_circular_reference(self, parent_name, visited=None):
        """Check for circular reference in parent hierarchy"""
        if visited is None:
            visited = set()

        if parent_name in visited:
            frappe.throw(_("Circular reference detected in location hierarchy"))

        visited.add(parent_name)
        parent_doc = frappe.get_value("Storage Location", parent_name, "parent_location")
        if parent_doc:
            self.check_circular_reference(parent_doc, visited)

    def validate_coordinates(self):
        """Validate GPS coordinates format"""
        if self.gps_coordinates:
            # Format: latitude,longitude
            coords = self.gps_coordinates.split(",")
            if len(coords) != 2:
                frappe.throw(_("GPS coordinates must be in format: latitude,longitude"))
            try:
                lat, lon = float(coords[0].strip()), float(coords[1].strip())
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    frappe.throw(_("Invalid GPS coordinates range"))
            except ValueError:
                frappe.throw(_("GPS coordinates must be numeric"))

    def validate_environmental_conditions(self):
        """Validate environmental condition ranges"""
        if self.temperature_min and self.temperature_max:
            if self.temperature_min >= self.temperature_max:
                frappe.throw(_("Minimum temperature must be less than maximum"))
        if self.humidity_min and self.humidity_max:
            if self.humidity_min >= self.humidity_max:
                frappe.throw(_("Minimum humidity must be less than maximum"))

    def generate_location_code(self):
        """Generate unique location code: WH-ZONE-ROW-BIN"""
        if not self.location_code:
            warehouse_abbr = self.warehouse[:3].upper() if self.warehouse else "WH"
            zone_abbr = self.zone[:2].upper() if self.zone else "Z1"

            # Get next sequence number for this zone
            last_location = frappe.db.sql(
                """
                SELECT location_code FROM `tabStorage Location`
                WHERE warehouse = %s AND zone = %s
                ORDER BY creation DESC LIMIT 1
            """,
                [self.warehouse, self.zone],
            )

            if last_location and last_location[0][0]:
                try:
                    last_num = int(last_location[0][0].split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.location_code = f"{warehouse_abbr}-{zone_abbr}-{new_num:03d}"

    def generate_barcode(self):
        """Generate barcode for location tracking"""
        if not self.barcode and self.location_code:
            self.barcode = f"LOC-{self.location_code}"

    def generate_qr_code(self):
        """Generate QR code with location information"""
        if not self.qr_code and self.location_code:
            qr_data = {
                "type": "storage_location",
                "location_code": self.location_code,
                "warehouse": self.warehouse,
                "zone": self.zone,
                "gps": self.gps_coordinates or "",
                "created": str(now_datetime()),
            }
            self.qr_code = json.dumps(qr_data)

    def update_path(self):
        """Update location path for hierarchical display"""
        path_parts = [self.location_name]
        current_parent = self.parent_location

        while current_parent:
            parent_name = frappe.get_value("Storage Location", current_parent, "location_name")
            if parent_name:
                path_parts.append(parent_name)
            current_parent = frappe.get_value("Storage Location", current_parent, "parent_location")

        self.location_path = " > ".join(reversed(path_parts))

    def calculate_efficiency_metrics(self):
        """Calculate storage efficiency metrics"""
        # Weight utilization percentage
        if self.max_weight_kg and self.current_weight_kg:
            self.weight_utilization = flt((self.current_weight_kg / self.max_weight_kg) * 100, 2)
        else:
            self.weight_utilization = 0

        # Volume utilization percentage
        if self.max_volume_m3 and self.current_volume_m3:
            self.volume_utilization = flt((self.current_volume_m3 / self.max_volume_m3) * 100, 2)
        else:
            self.volume_utilization = 0

        # Item count utilization percentage
        if self.max_items and self.current_item_count:
            self.item_utilization = flt((self.current_item_count / self.max_items) * 100, 2)
        else:
            self.item_utilization = 0

        # Overall efficiency score (weighted average)
        utilizations = [
            u
            for u in [self.weight_utilization, self.volume_utilization, self.item_utilization]
            if u > 0
        ]
        if utilizations:
            self.efficiency_score = flt(sum(utilizations) / len(utilizations), 2)
        else:
            self.efficiency_score = 0

    def log_location_creation(self):
        """Log location creation in system"""
        frappe.log_error(
            f"Storage Location created: {self.location_code} - {self.location_name}",
            "Storage Management",
        )

    def get_available_capacity(self):
        """Get available capacity in all dimensions"""
        return {
            "weight_available_kg": (
                flt(self.max_weight_kg - (self.current_weight_kg or 0), 2)
                if self.max_weight_kg
                else None
            ),
            "volume_available_m3": (
                flt(self.max_volume_m3 - (self.current_volume_m3 or 0), 3)
                if self.max_volume_m3
                else None
            ),
            "items_available": (
                cint(self.max_items - (self.current_item_count or 0)) if self.max_items else None
            ),
        }

    def can_accommodate_part(self, part_weight=0, part_volume=0):
        """Check if location can accommodate a new part"""
        available = self.get_available_capacity()

        # Check weight constraint
        if available.get("weight_available_kg") is not None:
            if part_weight > available["weight_available_kg"]:
                return False, _("Exceeds weight capacity")

        # Check volume constraint
        if available.get("volume_available_m3") is not None:
            if part_volume > available["volume_available_m3"]:
                return False, _("Exceeds volume capacity")

        # Check item count constraint
        if available.get("items_available") is not None:
            if available["items_available"] <= 0:
                return False, _("Maximum item count reached")

        return True, _("Location can accommodate part")

    def suggest_optimization(self):
        """Suggest storage optimization actions"""
        suggestions = []

        # High utilization warning
        if self.efficiency_score > 90:
            suggestions.append(
                {
                    "type": "warning",
                    "message": _("Location is near capacity - consider redistribution"),
                    "priority": "high",
                }
            )

        # Low utilization suggestion
        elif self.efficiency_score < 30:
            suggestions.append(
                {
                    "type": "info",
                    "message": _("Location is underutilized - consider consolidation"),
                    "priority": "low",
                }
            )

        # Environmental condition check
        if self.requires_climate_control and not self.climate_control_available:
            suggestions.append(
                {
                    "type": "error",
                    "message": _("Climate control required but not available"),
                    "priority": "high",
                }
            )

        return suggestions

    def update_current_usage(self):
        """Update current usage statistics from stored parts"""
        # Get all extracted parts in this location
        parts = frappe.get_list(
            "Extracted Parts",
            filters={"storage_location": self.name, "docstatus": 1},
            fields=["weight_kg", "volume_m3", "name"],
        )

        total_weight = sum(flt(part.get("weight_kg", 0)) for part in parts)
        total_volume = sum(flt(part.get("volume_m3", 0)) for part in parts)
        total_count = len(parts)

        # Update current usage
        self.current_weight_kg = flt(total_weight, 2)
        self.current_volume_m3 = flt(total_volume, 3)
        self.current_item_count = cint(total_count)

        # Recalculate efficiency
        self.calculate_efficiency_metrics()

        # Save without triggering validation again
        self.db_update()


# Utility functions for storage management
@frappe.whitelist()
def find_optimal_location(part_weight=0, part_volume=0, part_type=None, turnover_category=None):
    """Find optimal storage location for a part"""

    # Base filters
    filters = {"disabled": 0, "is_active": 1}

    # Add part type filter if specified
    if part_type:
        filters["preferred_part_types"] = ["like", f"%{part_type}%"]

    # Get all available locations
    locations = frappe.get_list(
        "Storage Location",
        filters=filters,
        fields=[
            "name",
            "location_code",
            "location_name",
            "warehouse",
            "zone",
            "max_weight_kg",
            "current_weight_kg",
            "max_volume_m3",
            "current_volume_m3",
            "max_items",
            "current_item_count",
            "accessibility_level",
            "turnover_category_preference",
            "priority_parts_only",
        ],
    )

    suitable_locations = []

    for location in locations:
        # Check capacity constraints
        can_accommodate, reason = check_location_capacity(location, part_weight, part_volume)

        if can_accommodate:
            # Calculate score based on multiple factors
            score = calculate_location_score(location, part_weight, part_volume, turnover_category)

            suitable_locations.append({"location": location, "score": score, "reason": reason})

    # Sort by score (highest first)
    suitable_locations.sort(key=lambda x: x["score"], reverse=True)

    return suitable_locations[:5]  # Return top 5 options


def check_location_capacity(location, part_weight, part_volume):
    """Check if location has capacity for the part"""

    # Weight check
    if location.get("max_weight_kg"):
        available_weight = flt(location["max_weight_kg"]) - flt(
            location.get("current_weight_kg", 0)
        )
        if part_weight > available_weight:
            return False, _("Exceeds weight capacity")

    # Volume check
    if location.get("max_volume_m3"):
        available_volume = flt(location["max_volume_m3"]) - flt(
            location.get("current_volume_m3", 0)
        )
        if part_volume > available_volume:
            return False, _("Exceeds volume capacity")

    # Item count check
    if location.get("max_items"):
        available_items = cint(location["max_items"]) - cint(location.get("current_item_count", 0))
        if available_items <= 0:
            return False, _("Maximum item count reached")

    return True, _("Capacity available")


def calculate_location_score(location, part_weight, part_volume, turnover_category):
    """Calculate suitability score for a location"""
    score = 100  # Base score

    # Efficiency preference (prefer locations with medium utilization)
    weight_util = 0
    if location.get("max_weight_kg") and location.get("current_weight_kg"):
        weight_util = (flt(location["current_weight_kg"]) / flt(location["max_weight_kg"])) * 100

    # Prefer 60-80% utilization
    if 60 <= weight_util <= 80:
        score += 20
    elif weight_util > 90:
        score -= 30  # Avoid nearly full locations
    elif weight_util < 20:
        score -= 10  # Slightly prefer over empty locations

    # Accessibility preference (higher is better for fast turnover)
    if turnover_category == "Fast" and location.get("accessibility_level"):
        if location["accessibility_level"] == "High":
            score += 15
        elif location["accessibility_level"] == "Medium":
            score += 5
    elif turnover_category == "Slow" and location.get("accessibility_level"):
        if location["accessibility_level"] == "Low":
            score += 10  # Slow items can go to less accessible locations

    # Turnover category preference match
    if turnover_category and location.get("turnover_category_preference"):
        if turnover_category.lower() in location["turnover_category_preference"].lower():
            score += 25

    return score


@frappe.whitelist()
def get_location_hierarchy(warehouse=None):
    """Get hierarchical view of storage locations"""

    filters = {"parent_location": ["is", "not set"]}
    if warehouse:
        filters["warehouse"] = warehouse

    root_locations = frappe.get_list(
        "Storage Location",
        filters=filters,
        fields=["name", "location_code", "location_name", "zone", "warehouse"],
        order_by="zone, location_name",
    )

    def build_tree(parent_name):
        children = frappe.get_list(
            "Storage Location",
            filters={"parent_location": parent_name},
            fields=["name", "location_code", "location_name", "zone"],
            order_by="location_name",
        )

        for child in children:
            child["children"] = build_tree(child["name"])

        return children

    # Build complete hierarchy
    for location in root_locations:
        location["children"] = build_tree(location["name"])

    return root_locations


@frappe.whitelist()
def generate_location_report(warehouse=None, zone=None):
    """Generate storage location utilization report"""

    filters = {"disabled": 0}
    if warehouse:
        filters["warehouse"] = warehouse
    if zone:
        filters["zone"] = zone

    locations = frappe.get_list(
        "Storage Location",
        filters=filters,
        fields=[
            "name",
            "location_code",
            "location_name",
            "warehouse",
            "zone",
            "max_weight_kg",
            "current_weight_kg",
            "max_volume_m3",
            "current_volume_m3",
            "max_items",
            "current_item_count",
            "efficiency_score",
            "accessibility_level",
        ],
    )

    # Calculate summary statistics
    total_locations = len(locations)
    high_utilization = len([l for l in locations if flt(l.get("efficiency_score", 0)) > 80])
    low_utilization = len([l for l in locations if flt(l.get("efficiency_score", 0)) < 30])

    return {
        "locations": locations,
        "summary": {
            "total_locations": total_locations,
            "high_utilization_count": high_utilization,
            "low_utilization_count": low_utilization,
            "optimal_utilization_count": total_locations - high_utilization - low_utilization,
            "high_utilization_percentage": (
                flt((high_utilization / total_locations) * 100, 1) if total_locations else 0
            ),
            "low_utilization_percentage": (
                flt((low_utilization / total_locations) * 100, 1) if total_locations else 0
            ),
        },
    }
