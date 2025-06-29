# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Profile Management
Handles customer profile updates, vehicle management, and service history
"""

import frappe
from frappe import _
from frappe.utils import cint, validate_email_address, get_datetime
from typing import Dict, List, Optional
from universal_workshop.customer_portal.auth import get_current_customer, require_customer_auth


@frappe.whitelist()
@require_customer_auth
def get_customer_profile() -> Dict:
    """
    Get current customer's profile information

    Returns:
        dict: Customer profile data
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Get comprehensive customer data
        customer_doc = frappe.get_doc("Customer", customer["customer_id"])

        # Get primary contact and address
        contact = _get_primary_contact(customer["customer_id"])
        address = _get_primary_address(customer["customer_id"])

        profile_data = {
            "customer_id": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "customer_name_ar": customer_doc.get("customer_name_ar", ""),
            "customer_type": customer_doc.customer_type,
            "customer_group": customer_doc.customer_group,
            "territory": customer_doc.territory,
            "default_currency": customer_doc.default_currency,
            "default_price_list": customer_doc.default_price_list,
            "language": customer_doc.get("language", "en"),
            "disabled": customer_doc.disabled,
            "contact": contact,
            "address": address,
            "communication_preferences": _get_communication_preferences(customer["customer_id"]),
        }

        return {"success": True, "profile": profile_data}

    except Exception as e:
        frappe.log_error(f"Error getting customer profile: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error retrieving profile information")}


@frappe.whitelist()
@require_customer_auth
def update_customer_profile(profile_data: Dict) -> Dict:
    """
    Update customer profile information

    Args:
        profile_data: Dictionary containing profile updates

    Returns:
        dict: Update operation result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        customer_doc = frappe.get_doc("Customer", customer["customer_id"])

        # Update allowed customer fields
        allowed_fields = [
            "customer_name",
            "customer_name_ar",
            "language",
            "default_currency",
            "default_price_list",
        ]

        updated_fields = []
        for field in allowed_fields:
            if field in profile_data and profile_data[field] != customer_doc.get(field):
                customer_doc.set(field, profile_data[field])
                updated_fields.append(field)

        if updated_fields:
            customer_doc.save(ignore_permissions=True)

            # Log profile update
            frappe.get_doc(
                {
                    "doctype": "Communication History",
                    "reference_doctype": "Customer",
                    "reference_name": customer["customer_id"],
                    "communication_type": "Profile Update",
                    "content": f"Profile updated: {', '.join(updated_fields)}",
                    "direction": "Outgoing",
                    "sent_at": get_datetime(),
                }
            ).insert(ignore_permissions=True)

        # Update contact information if provided
        if "contact" in profile_data:
            _update_customer_contact(customer["customer_id"], profile_data["contact"])

        # Update address information if provided
        if "address" in profile_data:
            _update_customer_address(customer["customer_id"], profile_data["address"])

        # Update communication preferences if provided
        if "communication_preferences" in profile_data:
            _update_communication_preferences(
                customer["customer_id"], profile_data["communication_preferences"]
            )

        return {
            "success": True,
            "message": _("Profile updated successfully"),
            "updated_fields": updated_fields,
        }

    except Exception as e:
        frappe.log_error(f"Error updating customer profile: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error updating profile")}


@frappe.whitelist()
@require_customer_auth
def get_customer_vehicles() -> Dict:
    """
    Get customer's vehicles list

    Returns:
        dict: Customer vehicles data
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        vehicles = frappe.get_list(
            "Vehicle Profile",
            filters={"customer": customer["customer_id"]},
            fields=[
                "name",
                "license_plate",
                "make",
                "model",
                "year",
                "vehicle_type",
                "vin_number",
                "engine_number",
                "color",
                "mileage",
                "fuel_type",
                "transmission_type",
                "insurance_company",
                "insurance_expiry",
                "registration_expiry",
                "last_service_date",
                "next_service_due",
                "creation",
            ],
            order_by="creation desc",
        )

        # Enhance vehicle data with service history summary
        for vehicle in vehicles:
            service_summary = _get_vehicle_service_summary(vehicle["name"])
            vehicle.update(service_summary)

        return {"success": True, "vehicles": vehicles, "total_vehicles": len(vehicles)}

    except Exception as e:
        frappe.log_error(f"Error getting customer vehicles: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error retrieving vehicles")}


@frappe.whitelist()
@require_customer_auth
def add_customer_vehicle(vehicle_data: Dict) -> Dict:
    """
    Add new vehicle to customer profile

    Args:
        vehicle_data: Vehicle information dictionary

    Returns:
        dict: Operation result with vehicle ID
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Validate required fields
        required_fields = ["license_plate", "make", "model", "year"]
        for field in required_fields:
            if not vehicle_data.get(field):
                return {
                    "success": False,
                    "message": _("Missing required field: {0}").format(
                        _(field.replace("_", " ").title())
                    ),
                }

        # Check for duplicate license plate
        existing_vehicle = frappe.db.exists(
            "Vehicle Profile", {"license_plate": vehicle_data["license_plate"]}
        )
        if existing_vehicle:
            return {
                "success": False,
                "message": _("Vehicle with this license plate already exists"),
            }

        # Create new vehicle
        vehicle_doc = frappe.new_doc("Vehicle Profile")
        vehicle_doc.customer = customer["customer_id"]

        # Set vehicle fields
        vehicle_fields = [
            "license_plate",
            "make",
            "model",
            "year",
            "vehicle_type",
            "vin_number",
            "engine_number",
            "color",
            "mileage",
            "fuel_type",
            "transmission_type",
            "insurance_company",
            "insurance_expiry",
            "registration_expiry",
        ]

        for field in vehicle_fields:
            if field in vehicle_data and vehicle_data[field]:
                vehicle_doc.set(field, vehicle_data[field])

        vehicle_doc.insert(ignore_permissions=True)

        # Log vehicle addition
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Vehicle Profile",
                "reference_name": vehicle_doc.name,
                "communication_type": "Vehicle Registration",
                "content": f"New vehicle added: {vehicle_data['make']} {vehicle_data['model']} ({vehicle_data['license_plate']})",
                "direction": "Outgoing",
                "sent_at": get_datetime(),
            }
        ).insert(ignore_permissions=True)

        return {
            "success": True,
            "message": _("Vehicle added successfully"),
            "vehicle_id": vehicle_doc.name,
        }

    except Exception as e:
        frappe.log_error(f"Error adding customer vehicle: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error adding vehicle")}


@frappe.whitelist()
@require_customer_auth
def update_customer_vehicle(vehicle_id: str, vehicle_data: Dict) -> Dict:
    """
    Update customer vehicle information

    Args:
        vehicle_id: Vehicle Profile ID
        vehicle_data: Updated vehicle information

    Returns:
        dict: Operation result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify vehicle ownership
        vehicle_doc = frappe.get_doc("Vehicle Profile", vehicle_id)
        if vehicle_doc.customer != customer["customer_id"]:
            return {"success": False, "message": _("Access denied")}

        # Update allowed fields
        updatable_fields = [
            "license_plate",
            "color",
            "mileage",
            "insurance_company",
            "insurance_expiry",
            "registration_expiry",
        ]

        updated_fields = []
        for field in updatable_fields:
            if field in vehicle_data and vehicle_data[field] != vehicle_doc.get(field):
                # Check for duplicate license plate if updating
                if field == "license_plate":
                    existing = frappe.db.exists(
                        "Vehicle Profile",
                        {"license_plate": vehicle_data[field], "name": ["!=", vehicle_id]},
                    )
                    if existing:
                        return {
                            "success": False,
                            "message": _("License plate already exists for another vehicle"),
                        }

                vehicle_doc.set(field, vehicle_data[field])
                updated_fields.append(field)

        if updated_fields:
            vehicle_doc.save(ignore_permissions=True)

            # Log vehicle update
            frappe.get_doc(
                {
                    "doctype": "Communication History",
                    "reference_doctype": "Vehicle Profile",
                    "reference_name": vehicle_id,
                    "communication_type": "Vehicle Update",
                    "content": f"Vehicle updated: {', '.join(updated_fields)}",
                    "direction": "Outgoing",
                    "sent_at": get_datetime(),
                }
            ).insert(ignore_permissions=True)

        return {
            "success": True,
            "message": _("Vehicle updated successfully"),
            "updated_fields": updated_fields,
        }

    except Exception as e:
        frappe.log_error(f"Error updating customer vehicle: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error updating vehicle")}


@frappe.whitelist()
@require_customer_auth
def get_service_history(vehicle_id: str = None, limit: int = 20, offset: int = 0) -> Dict:
    """
    Get customer's service history

    Args:
        vehicle_id: Optional vehicle ID to filter by
        limit: Number of records to return
        offset: Number of records to skip

    Returns:
        dict: Service history data
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Build filters
        filters = {"customer": customer["customer_id"]}
        if vehicle_id:
            # Verify vehicle ownership
            vehicle_doc = frappe.get_doc("Vehicle Profile", vehicle_id)
            if vehicle_doc.customer != customer["customer_id"]:
                return {"success": False, "message": _("Access denied")}
            filters["vehicle"] = vehicle_id

        # Get service appointments
        appointments = frappe.get_list(
            "Service Appointment",
            filters=filters,
            fields=[
                "name",
                "appointment_date",
                "appointment_time",
                "vehicle",
                "service_type",
                "service_description",
                "technician_assigned",
                "status",
                "completion_date",
                "total_cost",
                "workshop",
                "creation",
                "owner",
            ],
            limit=limit,
            start=offset,
            order_by="appointment_date desc",
        )

        # Get sales invoices (completed services)
        invoice_filters = {"customer": customer["customer_id"], "docstatus": 1}
        if vehicle_id:
            invoice_filters["vehicle"] = vehicle_id

        invoices = frappe.get_list(
            "Sales Invoice",
            filters=invoice_filters,
            fields=[
                "name",
                "posting_date",
                "vehicle",
                "grand_total",
                "outstanding_amount",
                "status",
                "remarks",
                "creation",
                "owner",
            ],
            limit=limit,
            start=offset,
            order_by="posting_date desc",
        )

        # Combine and sort service history
        service_history = []

        for appointment in appointments:
            service_history.append(
                {
                    "type": "appointment",
                    "id": appointment.name,
                    "date": appointment.appointment_date,
                    "time": appointment.get("appointment_time"),
                    "vehicle": appointment.vehicle,
                    "service_type": appointment.service_type,
                    "description": appointment.get("service_description", ""),
                    "technician": appointment.get("technician_assigned", ""),
                    "status": appointment.status,
                    "completion_date": appointment.get("completion_date"),
                    "total_cost": appointment.get("total_cost", 0),
                    "workshop": appointment.get("workshop", ""),
                    "creation": appointment.creation,
                }
            )

        for invoice in invoices:
            service_history.append(
                {
                    "type": "invoice",
                    "id": invoice.name,
                    "date": invoice.posting_date,
                    "vehicle": invoice.get("vehicle"),
                    "total_amount": invoice.grand_total,
                    "outstanding_amount": invoice.outstanding_amount,
                    "status": invoice.status,
                    "remarks": invoice.get("remarks", ""),
                    "creation": invoice.creation,
                }
            )

        # Sort by date (newest first)
        service_history.sort(key=lambda x: x.get("date") or x.get("creation"), reverse=True)

        return {
            "success": True,
            "service_history": service_history[:limit],
            "total_records": len(service_history),
            "has_more": len(service_history) > limit,
        }

    except Exception as e:
        frappe.log_error(f"Error getting service history: {str(e)}", "Customer Portal Profile")
        return {"success": False, "message": _("Error retrieving service history")}


def _get_primary_contact(customer_id: str) -> Optional[Dict]:
    """Get customer's primary contact information"""
    try:
        contact_links = frappe.get_list(
            "Dynamic Link",
            filters={"link_doctype": "Customer", "link_name": customer_id, "parenttype": "Contact"},
            fields=["parent"],
            limit=1,
        )

        if contact_links:
            contact = frappe.get_doc("Contact", contact_links[0].parent)
            return {
                "name": contact.name,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email_id": contact.email_id,
                "mobile_no": contact.mobile_no,
                "phone": contact.phone,
                "designation": contact.designation,
                "department": contact.department,
            }
    except Exception:
        pass
    return None


def _get_primary_address(customer_id: str) -> Optional[Dict]:
    """Get customer's primary address information"""
    try:
        address_links = frappe.get_list(
            "Dynamic Link",
            filters={"link_doctype": "Customer", "link_name": customer_id, "parenttype": "Address"},
            fields=["parent"],
            limit=1,
        )

        if address_links:
            address = frappe.get_doc("Address", address_links[0].parent)
            return {
                "name": address.name,
                "address_title": address.address_title,
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "city": address.city,
                "state": address.state,
                "country": address.country,
                "pincode": address.pincode,
                "phone": address.phone,
                "email_id": address.email_id,
            }
    except Exception:
        pass
    return None


def _get_communication_preferences(customer_id: str) -> Dict:
    """Get customer's communication preferences"""
    try:
        consent = frappe.get_doc("Communication Consent", {"customer": customer_id})
        return {
            "sms_enabled": consent.sms_enabled,
            "whatsapp_enabled": consent.whatsapp_enabled,
            "email_enabled": consent.email_enabled,
            "preferred_language": consent.preferred_language,
            "marketing_consent": consent.marketing_consent,
        }
    except Exception:
        return {
            "sms_enabled": True,
            "whatsapp_enabled": True,
            "email_enabled": True,
            "preferred_language": "en",
            "marketing_consent": False,
        }


def _update_customer_contact(customer_id: str, contact_data: Dict):
    """Update customer contact information"""
    try:
        contact = _get_primary_contact(customer_id)
        if contact:
            contact_doc = frappe.get_doc("Contact", contact["name"])

            # Update allowed contact fields
            contact_fields = ["first_name", "last_name", "email_id", "mobile_no", "phone"]
            for field in contact_fields:
                if field in contact_data:
                    contact_doc.set(field, contact_data[field])

            contact_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error updating customer contact: {str(e)}", "Customer Portal Profile")


def _update_customer_address(customer_id: str, address_data: Dict):
    """Update customer address information"""
    try:
        address = _get_primary_address(customer_id)
        if address:
            address_doc = frappe.get_doc("Address", address["name"])

            # Update allowed address fields
            address_fields = [
                "address_line1",
                "address_line2",
                "city",
                "state",
                "country",
                "pincode",
                "phone",
                "email_id",
            ]
            for field in address_fields:
                if field in address_data:
                    address_doc.set(field, address_data[field])

            address_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error updating customer address: {str(e)}", "Customer Portal Profile")


def _update_communication_preferences(customer_id: str, preferences: Dict):
    """Update customer communication preferences"""
    try:
        consent_name = frappe.db.exists("Communication Consent", {"customer": customer_id})
        if consent_name:
            consent_doc = frappe.get_doc("Communication Consent", consent_name)
        else:
            consent_doc = frappe.new_doc("Communication Consent")
            consent_doc.customer = customer_id

        # Update preferences
        pref_fields = [
            "sms_enabled",
            "whatsapp_enabled",
            "email_enabled",
            "preferred_language",
            "marketing_consent",
        ]
        for field in pref_fields:
            if field in preferences:
                consent_doc.set(field, preferences[field])

        consent_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(
            f"Error updating communication preferences: {str(e)}", "Customer Portal Profile"
        )


def _get_vehicle_service_summary(vehicle_id: str) -> Dict:
    """Get vehicle service summary statistics"""
    try:
        # Count total services
        total_services = frappe.db.count(
            "Service Appointment", {"vehicle": vehicle_id, "status": "Completed"}
        )

        # Get last service date
        last_service = frappe.db.get_value(
            "Service Appointment",
            {"vehicle": vehicle_id, "status": "Completed"},
            "completion_date",
            order_by="completion_date desc",
        )

        # Calculate total spent
        total_spent = (
            frappe.db.sql(
                """
            SELECT SUM(grand_total)
            FROM `tabSales Invoice`
            WHERE vehicle = %s AND docstatus = 1
        """,
                [vehicle_id],
            )[0][0]
            or 0
        )

        return {
            "total_services": total_services,
            "last_service_date": last_service,
            "total_spent": total_spent,
        }
    except Exception:
        return {"total_services": 0, "last_service_date": None, "total_spent": 0}
