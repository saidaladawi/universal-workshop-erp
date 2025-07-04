# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional

import frappe
from frappe import _

from .elasticsearch_client import get_elasticsearch_client


class CustomerIndexer:
    """
    Service for indexing Customer documents in Elasticsearch with Arabic support
    """

    def __init__(self):
        """Initialize the customer indexer"""
        self.es_client = get_elasticsearch_client()
        self.doctype = "Customer"

    def setup_customer_index(self) -> bool:
        """
        Setup the Customer index with proper field mappings for Arabic content

        Returns:
            bool: True if successful, False otherwise
        """
        fields_config = {
            # Customer identification
            "name": {"type": "keyword"},
            "customer_name": {"type": "text"},
            "customer_name_ar": {"type": "text"},
            "customer_code": {"type": "keyword"},
            "customer_type": {"type": "keyword"},
            "customer_group": {"type": "keyword"},
            # Contact information
            "email_id": {"type": "keyword"},
            "mobile_no": {"type": "keyword"},
            "phone_no": {"type": "keyword"},
            "website": {"type": "keyword"},
            # Arabic-specific fields
            "civil_id": {"type": "keyword"},
            "nationality": {"type": "keyword"},
            "preferred_language": {"type": "keyword"},
            "emergency_contact": {"type": "keyword"},
            # Address information
            "customer_primary_address": {"type": "text"},
            "address_ar": {"type": "text"},
            "city": {"type": "keyword"},
            "state": {"type": "keyword"},
            "country": {"type": "keyword"},
            "pincode": {"type": "keyword"},
            # Business information
            "territory": {"type": "keyword"},
            "tax_id": {"type": "keyword"},
            "customer_details": {"type": "text"},
            "customer_notes": {"type": "text"},
            # Analytics fields
            "customer_lifetime_value": {"type": "double"},
            "total_services_count": {"type": "integer"},
            "average_service_value": {"type": "double"},
            "customer_status": {"type": "keyword"},
            # Timestamps
            "creation": {"type": "date"},
            "modified": {"type": "date"},
            "disabled": {"type": "keyword"},
        }

        return self.es_client.create_index_mapping(self.doctype, fields_config)

    def index_customer(self, customer_name: str) -> bool:
        """
        Index a single customer document

        Args:
            customer_name: Name of the customer to index

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get customer document
            customer = frappe.get_doc("Customer", customer_name)

            # Build document for indexing
            doc_data = self._build_customer_document(customer)

            # Index the document
            doc_id = getattr(customer, "name", customer_name) or customer_name
            return self.es_client.index_document(doctype=self.doctype, doc_id=doc_id, document=doc_data)

        except Exception as e:
            frappe.log_error(f"Failed to index customer {customer_name}: {e!s}")
            return False

    def _build_customer_document(self, customer: Any) -> dict[str, Any]:
        """
        Build the document structure for Elasticsearch indexing

        Args:
            customer: Customer document from Frappe

        Returns:
            Dict containing the indexed document data
        """

        # Safe attribute access function
        def safe_get(obj: Any, attr: str, default: Any = "") -> Any:
            """Safely get attribute with default value"""
            try:
                value = getattr(obj, attr, default)
                return value if value is not None else default
            except Exception:
                return default

        doc_data = {
            # Basic customer information
            "name": safe_get(customer, "name", ""),
            "customer_name": safe_get(customer, "customer_name", ""),
            "customer_code": safe_get(customer, "customer_code", ""),
            "customer_type": safe_get(customer, "customer_type", ""),
            "customer_group": safe_get(customer, "customer_group", ""),
            # Contact information
            "email_id": safe_get(customer, "email_id", ""),
            "mobile_no": safe_get(customer, "mobile_no", ""),
            "phone_no": safe_get(customer, "phone_no", ""),
            "website": safe_get(customer, "website", ""),
            # Location information
            "territory": safe_get(customer, "territory", ""),
            "country": safe_get(customer, "country", ""),
            # Business information
            "tax_id": safe_get(customer, "tax_id", ""),
            "customer_details": safe_get(customer, "customer_details", ""),
            # Timestamps
            "creation": None,
            "modified": None,
            "disabled": "No",
        }

        # Handle timestamps safely
        try:
            creation_time = safe_get(customer, "creation", None)
            if creation_time and hasattr(creation_time, "isoformat"):
                doc_data["creation"] = creation_time.isoformat()
        except Exception:
            pass

        try:
            modified_time = safe_get(customer, "modified", None)
            if modified_time and hasattr(modified_time, "isoformat"):
                doc_data["modified"] = modified_time.isoformat()
        except Exception:
            pass

        # Handle disabled flag safely
        try:
            disabled_value = safe_get(customer, "disabled", 0)
            doc_data["disabled"] = "Yes" if disabled_value else "No"
        except Exception:
            doc_data["disabled"] = "No"

        # Add custom fields from Universal Workshop extension
        custom_fields = [
            "customer_name_ar",
            "civil_id",
            "nationality",
            "preferred_language",
            "emergency_contact",
            "customer_notes",
            "customer_lifetime_value",
            "total_services_count",
            "average_service_value",
            "customer_status",
        ]

        for field in custom_fields:
            try:
                value = safe_get(customer, field, None)
                if value is not None:
                    doc_data[field] = value
            except Exception:
                continue

        # Get primary address if available
        try:
            primary_address = safe_get(customer, "customer_primary_address", None)
            if primary_address:
                address = frappe.get_doc("Address", primary_address)
                doc_data.update(
                    {
                        "customer_primary_address": self._format_address(address),
                        "city": safe_get(address, "city", ""),
                        "state": safe_get(address, "state", ""),
                        "country": safe_get(address, "country", ""),
                        "pincode": safe_get(address, "pincode", ""),
                    }
                )

                # Add Arabic address if available
                arabic_address = safe_get(address, "address_line1_ar", "")
                if arabic_address:
                    doc_data["address_ar"] = arabic_address

        except Exception as e:
            frappe.log_error(
                f"Failed to get address for customer {safe_get(customer, 'name', 'Unknown')}: {e!s}"
            )

        # Add vehicle information summary
        customer_name = safe_get(customer, "name", "")
        if customer_name:
            doc_data["vehicle_summary"] = self._get_vehicle_summary(customer_name)
            doc_data["service_summary"] = self._get_service_summary(customer_name)

        return doc_data

    def _format_address(self, address: Any) -> str:
        """Format address for search indexing"""
        address_parts = []

        def safe_get_addr(attr: str) -> str:
            try:
                value = getattr(address, attr, "")
                return str(value) if value else ""
            except Exception:
                return ""

        address_line1 = safe_get_addr("address_line1")
        if address_line1:
            address_parts.append(address_line1)

        address_line2 = safe_get_addr("address_line2")
        if address_line2:
            address_parts.append(address_line2)

        city = safe_get_addr("city")
        if city:
            address_parts.append(city)

        state = safe_get_addr("state")
        if state:
            address_parts.append(state)

        return ", ".join(address_parts)

    def _get_vehicle_summary(self, customer_name: str) -> str:
        """Get summary of customer vehicles for search indexing"""
        try:
            vehicles = frappe.db.sql(
                """
                SELECT v.license_plate, v.make, v.model, v.year
                FROM `tabVehicle` v
                JOIN `tabCustomer Vehicle Ownership` vo ON v.name = vo.vehicle
                WHERE vo.parent = %s
                ORDER BY vo.primary_vehicle DESC, v.creation DESC
                LIMIT 5
            """,
                (customer_name,),
                as_dict=True,
            )

            vehicle_descriptions = []
            for vehicle in vehicles or []:
                make = str(vehicle.get("make") or "") if isinstance(vehicle, dict) else ""
                model = str(vehicle.get("model") or "") if isinstance(vehicle, dict) else ""
                year = str(vehicle.get("year") or "") if isinstance(vehicle, dict) else ""
                license_plate = str(vehicle.get("license_plate") or "") if isinstance(vehicle, dict) else ""

                parts = [part for part in [make, model, str(year), license_plate] if part]
                if parts:
                    vehicle_descriptions.append(" ".join(parts))

            return "; ".join(vehicle_descriptions) if vehicle_descriptions else ""

        except Exception as e:
            frappe.log_error(f"Failed to get vehicle summary for customer {customer_name}: {e!s}")
            return ""

    def _get_service_summary(self, customer_name: str) -> str:
        """Get summary of customer service history for search indexing"""
        try:
            services = frappe.db.sql(
                """
                SELECT si.posting_date, si.grand_total, si.remarks
                FROM `tabSales Invoice` si
                WHERE si.customer = %s AND si.docstatus = 1
                ORDER BY si.posting_date DESC
                LIMIT 3
            """,
                (customer_name,),
                as_dict=True,
            )

            service_descriptions = []
            for service in services or []:
                posting_date = service.get("posting_date", "")
                grand_total = service.get("grand_total", 0) or 0
                remarks = service.get("remarks", "") or ""

                desc_parts = []
                if posting_date:
                    desc_parts.append(str(posting_date))
                if grand_total:
                    desc_parts.append(f"OMR {grand_total:.2f}")
                if remarks:
                    desc_parts.append(remarks[:50])  # Truncate long remarks

                if desc_parts:
                    service_descriptions.append(" - ".join(desc_parts))

            return "; ".join(service_descriptions) if service_descriptions else ""

        except Exception as e:
            frappe.log_error(f"Failed to get service summary for customer {customer_name}: {e!s}")
            return ""

    def bulk_index_customers(self, batch_size: int = 100) -> dict[str, int]:
        """
        Index all customers in batches

        Args:
            batch_size: Number of customers to process in each batch

        Returns:
            Dict with success and failure counts
        """
        try:
            # Get all active customers
            customers = frappe.get_all(
                "Customer", filters={"disabled": 0}, fields=["name"], order_by="creation"
            )

            success_count = 0
            failure_count = 0

            # Process in batches
            for i in range(0, len(customers), batch_size):
                batch = customers[i : i + batch_size]

                for customer in batch:
                    customer_name = customer.get("name", "")
                    if customer_name and self.index_customer(customer_name):
                        success_count += 1
                    else:
                        failure_count += 1

                # Commit after each batch
                frappe.db.commit()

                # Log progress
                frappe.logger().info(f"Indexed batch {i // batch_size + 1}: {len(batch)} customers")

            return {"success": success_count, "failures": failure_count, "total": len(customers)}

        except Exception as e:
            frappe.log_error(f"Bulk customer indexing failed: {e!s}")
            return {"success": 0, "failures": 0, "total": 0}

    def remove_customer_from_index(self, customer_name: str) -> bool:
        """
        Remove customer from search index

        Args:
            customer_name: Name of the customer to remove

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.es_client.delete_document(doctype=self.doctype, doc_id=customer_name)
        except Exception as e:
            frappe.log_error(f"Failed to remove customer {customer_name} from index: {e!s}")
            return False

    def search_customers(
        self, query: str, filters: dict | None = None, size: int = 20, from_: int = 0
    ) -> dict[str, Any]:
        """
        Search customers using Elasticsearch

        Args:
            query: Search query string
            filters: Additional search filters
            size: Number of results to return
            from_: Starting position for pagination

        Returns:
            Dict containing search results
        """
        try:
            return self.es_client.search_documents(
                doctype=self.doctype, query=query, filters=filters, size=size, from_=from_
            )
        except Exception as e:
            frappe.log_error(f"Customer search failed for query '{query}': {e!s}")
            return {"hits": [], "total": 0, "max_score": 0}

    def get_customer_suggestions(self, field: str, text: str, size: int = 5) -> list[str]:
        """
        Get auto-completion suggestions for customer fields

        Args:
            field: Field name to get suggestions for
            text: Partial text to complete
            size: Number of suggestions to return

        Returns:
            List of completion suggestions
        """
        try:
            return self.es_client.suggest_completions(doctype=self.doctype, field=field, text=text, size=size)
        except Exception as e:
            frappe.log_error(f"Customer suggestion failed for field '{field}': {e!s}")
            return []


# API endpoints for customer search indexing


@frappe.whitelist()
def setup_customer_search_index():
    """Setup customer search index"""
    indexer = CustomerIndexer()
    return indexer.setup_customer_index()


def index_customer_on_save(doc, method=None):
    """Hook to index customer when saved"""
    indexer = CustomerIndexer()
    indexer.index_customer(doc.name)


def remove_customer_on_delete(doc, method=None):
    """Hook to remove customer from index when deleted"""
    indexer = CustomerIndexer()
    indexer.remove_customer_from_index(doc.name)
