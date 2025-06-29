# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import re
from urllib.parse import urlparse, urljoin


@frappe.whitelist()
def get_marketplace_connectors(active_only=True):
    """Get list of available marketplace connectors"""
    filters = {}
    if active_only:
        filters.update({"is_active": 1, "status": "Connected"})

    connectors = frappe.get_list(
        "Marketplace Connector",
        filters=filters,
        fields=[
            "name",
            "connector_name",
            "connector_name_ar",
            "marketplace_platform",
            "platform_region",
            "status",
            "last_successful_sync",
            "sync_success_rate",
        ],
    )

    return connectors


@frappe.whitelist()
def get_marketplace_analytics(connector_name=None, date_range="30"):
    """Get marketplace analytics and performance data"""
    filters = {}
    if connector_name:
        filters["connector"] = connector_name

    # Get date range
    from_date = frappe.utils.add_days(frappe.utils.today(), -int(date_range))

    # Sync logs analytics
    sync_logs = frappe.db.sql(
        """
        SELECT 
            activity_type,
            status,
            COUNT(*) as count,
            AVG(duration_seconds) as avg_duration,
            SUM(successful_items) as total_successful,
            SUM(failed_items) as total_failed
        FROM `tabMarketplace Sync Log`
        WHERE timestamp >= %s
        {connector_filter}
        GROUP BY activity_type, status
    """.format(
            connector_filter=f"AND connector = '{connector_name}'" if connector_name else ""
        ),
        [from_date],
        as_dict=True,
    )

    # Product listings analytics
    listings_stats = frappe.db.sql(
        """
        SELECT 
            marketplace_connector,
            listing_status,
            COUNT(*) as count,
            AVG(views_count) as avg_views,
            AVG(conversion_rate) as avg_conversion,
            SUM(total_revenue) as total_revenue
        FROM `tabMarketplace Product Listing`
        WHERE created_date >= %s
        {connector_filter}
        GROUP BY marketplace_connector, listing_status
    """.format(
            connector_filter=(
                f"AND marketplace_connector = '{connector_name}'" if connector_name else ""
            )
        ),
        [from_date],
        as_dict=True,
    )

    return {
        "sync_analytics": sync_logs,
        "listings_analytics": listings_stats,
        "date_range": date_range,
        "from_date": from_date,
    }


@frappe.whitelist()
def create_product_listing(extracted_part_id, connector_name, marketplace_data=None):
    """Create a marketplace product listing from an extracted part"""
    try:
        # Get extracted part details
        extracted_part = frappe.get_doc("Scrap Vehicle Extracted Part", extracted_part_id)
        connector = frappe.get_doc("Marketplace Connector", connector_name)

        # Validate requirements
        if not extracted_part.final_grade:
            frappe.throw(_("Part must have a condition grade before listing"))

        if not extracted_part.final_sale_price:
            frappe.throw(_("Part must have a sale price before listing"))

        if extracted_part.status != "Available for Sale":
            frappe.throw(_("Part must be available for sale to create listing"))

        # Create marketplace listing
        listing = frappe.new_doc("Marketplace Product Listing")
        listing.update(
            {
                "marketplace_connector": connector_name,
                "source_extracted_part": extracted_part_id,
                "listing_title": extracted_part.marketplace_title
                or f"{extracted_part.part_name} - {extracted_part.final_grade}",
                "product_name": extracted_part.part_name,
                "product_name_ar": extracted_part.part_name_ar,
                "product_description": extracted_part.marketplace_description
                or extracted_part.part_description,
                "product_description_ar": extracted_part.part_description_ar,
                "part_category": extracted_part.part_category,
                "brand_manufacturer": extracted_part.original_manufacturer,
                "part_number": extracted_part.part_code,
                "condition_grade": extracted_part.final_grade,
                "listing_price": extracted_part.final_sale_price,
                "currency": connector.default_currency,
                "listing_status": "Draft",
                "auto_sync_enabled": 1,
                "sync_frequency": "Daily",
            }
        )

        # Add images
        for i in range(1, 11):
            image_field = f"image_{i}"
            if hasattr(extracted_part, image_field) and getattr(extracted_part, image_field):
                if i == 1:
                    listing.main_image = getattr(extracted_part, image_field)
                else:
                    setattr(listing, f"image_{i-1}", getattr(extracted_part, image_field))

        # Add marketplace-specific data
        if marketplace_data:
            listing.update(marketplace_data)

        # Apply marketplace mappings
        listing = apply_marketplace_mappings(listing, connector)

        listing.insert()

        # Update extracted part
        extracted_part.marketplace_listing = listing.name
        extracted_part.marketplace_listed = 1
        extracted_part.save()

        return {
            "status": "success",
            "listing_id": listing.name,
            "message": _("Product listing created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating marketplace listing: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def bulk_create_listings(extracted_part_ids, connector_name, marketplace_data=None):
    """Create multiple marketplace listings in bulk"""
    results = {"successful": [], "failed": [], "total": len(extracted_part_ids)}

    for part_id in extracted_part_ids:
        try:
            result = create_product_listing(part_id, connector_name, marketplace_data)
            if result["status"] == "success":
                results["successful"].append(
                    {"part_id": part_id, "listing_id": result["listing_id"]}
                )
            else:
                results["failed"].append({"part_id": part_id, "error": result["message"]})
        except Exception as e:
            results["failed"].append({"part_id": part_id, "error": str(e)})

    return results


def apply_marketplace_mappings(listing, connector):
    """Apply marketplace-specific field mappings"""
    try:
        # Category mapping
        if connector.category_mapping:
            category_map = json.loads(connector.category_mapping)
            marketplace_category = category_map.get(listing.part_category)
            if marketplace_category:
                listing.marketplace_category = marketplace_category

        # Condition grade mapping
        if connector.condition_grade_mapping:
            condition_map = json.loads(connector.condition_grade_mapping)
            marketplace_condition = condition_map.get(listing.condition_grade)
            if marketplace_condition:
                # Store as JSON for marketplace-specific condition
                listing.marketplace_attributes = json.dumps({"condition": marketplace_condition})

        # Platform-specific attributes
        platform_attributes = get_platform_specific_attributes(
            connector.marketplace_platform, listing
        )
        if platform_attributes:
            existing_attrs = json.loads(listing.marketplace_attributes or "{}")
            existing_attrs.update(platform_attributes)
            listing.marketplace_attributes = json.dumps(existing_attrs)

        return listing

    except Exception as e:
        frappe.log_error(f"Error applying marketplace mappings: {str(e)}")
        return listing


def get_platform_specific_attributes(platform, listing):
    """Get platform-specific attributes for listing"""
    attributes = {}

    if platform == "Dubizzle Motors":
        attributes.update({"item_type": "auto_part", "condition_type": "used", "negotiable": True})

    elif platform == "OpenSooq":
        attributes.update(
            {
                "category_id": get_opensooq_category_id(listing.part_category),
                "is_negotiable": "yes",
                "warranty_available": "no",
            }
        )

    elif platform == "YallaMotor":
        attributes.update(
            {"part_type": "aftermarket", "shipping_available": True, "installation_service": False}
        )

    return attributes


def get_opensooq_category_id(part_category):
    """Map part category to OpenSooq category ID"""
    category_map = {
        "Engine Parts": "automotive_engine",
        "Body Parts": "automotive_body",
        "Electrical": "automotive_electrical",
        "Interior": "automotive_interior",
        "Exterior": "automotive_exterior",
    }
    return category_map.get(part_category, "automotive_other")


@frappe.whitelist()
def sync_marketplace_orders(connector_name):
    """Sync orders from marketplace to ERPNext"""
    try:
        connector = frappe.get_doc("Marketplace Connector", connector_name)

        if connector.status != "Connected":
            return {"status": "error", "message": _("Connector is not connected")}

        # Get orders from marketplace API
        orders_data = fetch_marketplace_orders(connector)

        synced_orders = []
        for order_data in orders_data:
            try:
                # Create sales order in ERPNext
                sales_order = create_sales_order_from_marketplace(order_data, connector)
                synced_orders.append(sales_order.name)

                # Update listing status if item is sold
                if order_data.get("listing_id"):
                    update_listing_status(order_data["listing_id"], "Sold")

            except Exception as e:
                frappe.log_error(f"Error syncing order {order_data.get('order_id')}: {str(e)}")

        return {
            "status": "success",
            "synced_orders": synced_orders,
            "total_synced": len(synced_orders),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def fetch_marketplace_orders(connector):
    """Fetch orders from marketplace API"""
    try:
        headers = get_auth_headers(connector)
        endpoint = f"{connector.api_endpoint.rstrip('/')}/orders"

        # Get orders from last sync or last 7 days
        since_date = connector.last_successful_sync or frappe.utils.add_days(frappe.utils.now(), -7)

        params = {"since": since_date, "status": "paid", "limit": 100}

        response = requests.get(endpoint, headers=headers, params=params, timeout=60)

        if response.status_code == 200:
            return response.json().get("orders", [])
        else:
            frappe.throw(_("Failed to fetch orders: HTTP {0}").format(response.status_code))

    except Exception as e:
        frappe.log_error(f"Error fetching marketplace orders: {str(e)}")
        return []


def create_sales_order_from_marketplace(order_data, connector):
    """Create ERPNext Sales Order from marketplace order data"""
    # Create customer if not exists
    customer = get_or_create_customer(order_data["buyer"], connector)

    # Create sales order
    sales_order = frappe.new_doc("Sales Order")
    sales_order.update(
        {
            "customer": customer.name,
            "order_type": "Sales",
            "transaction_date": frappe.utils.getdate(order_data["order_date"]),
            "delivery_date": frappe.utils.getdate(
                order_data.get("delivery_date", frappe.utils.add_days(frappe.utils.today(), 7))
            ),
            "company": frappe.defaults.get_defaults().company,
            "currency": order_data.get("currency", connector.default_currency),
            "conversion_rate": 1,
            "selling_price_list": "Standard Selling",
        }
    )

    # Add items
    for item_data in order_data["items"]:
        sales_order.append(
            "items",
            {
                "item_code": item_data["sku"],
                "item_name": item_data["name"],
                "qty": item_data["quantity"],
                "rate": item_data["price"],
                "delivery_date": sales_order.delivery_date,
            },
        )

    # Add marketplace-specific fields
    sales_order.update(
        {
            "marketplace_order_id": order_data["order_id"],
            "marketplace_platform": connector.marketplace_platform,
            "custom_marketplace_connector": connector.name,
        }
    )

    sales_order.insert()
    sales_order.submit()

    return sales_order


def get_or_create_customer(buyer_data, connector):
    """Get existing customer or create new one from marketplace buyer data"""
    # Try to find existing customer by email or phone
    customer_name = None

    if buyer_data.get("email"):
        customer_name = frappe.db.get_value("Customer", {"email_id": buyer_data["email"]}, "name")

    if not customer_name and buyer_data.get("phone"):
        customer_name = frappe.db.get_value("Customer", {"mobile_no": buyer_data["phone"]}, "name")

    if customer_name:
        return frappe.get_doc("Customer", customer_name)

    # Create new customer
    customer = frappe.new_doc("Customer")
    customer.update(
        {
            "customer_name": buyer_data.get(
                "name", f"Marketplace Customer - {buyer_data.get('buyer_id')}"
            ),
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": connector.platform_region or "Oman",
            "email_id": buyer_data.get("email"),
            "mobile_no": buyer_data.get("phone"),
            "marketplace_buyer_id": buyer_data.get("buyer_id"),
            "marketplace_platform": connector.marketplace_platform,
        }
    )

    customer.insert()
    return customer


def update_listing_status(listing_id, status):
    """Update marketplace listing status"""
    frappe.db.set_value("Marketplace Product Listing", listing_id, "listing_status", status)


def get_auth_headers(connector):
    """Get authentication headers for marketplace API calls"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Universal Workshop ERP v2.0 ({connector.connector_name})",
    }

    if connector.auth_method == "API Key":
        headers["X-API-Key"] = connector.get_password("api_key")

    elif connector.auth_method == "Bearer Token":
        headers["Authorization"] = f"Bearer {connector.get_password('access_token')}"

    elif connector.auth_method == "Basic Auth":
        import base64

        credentials = f"{connector.get_password('api_key')}:{connector.get_password('api_secret')}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"

    return headers


@frappe.whitelist()
def get_marketplace_categories(connector_name):
    """Get available categories from marketplace"""
    try:
        connector = frappe.get_doc("Marketplace Connector", connector_name)

        if connector.status != "Connected":
            return {"status": "error", "message": _("Connector is not connected")}

        headers = get_auth_headers(connector)
        endpoint = f"{connector.api_endpoint.rstrip('/')}/categories"

        response = requests.get(endpoint, headers=headers, timeout=30)

        if response.status_code == 200:
            categories = response.json().get("categories", [])
            return {"status": "success", "categories": categories}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_marketplace_inventory(connector_name, product_listings=None):
    """Update inventory levels on marketplace"""
    try:
        connector = frappe.get_doc("Marketplace Connector", connector_name)

        if not product_listings:
            # Get all active listings for this connector
            product_listings = frappe.get_list(
                "Marketplace Product Listing",
                filters={"marketplace_connector": connector_name, "listing_status": "Active"},
                fields=["name", "external_listing_id", "source_extracted_part"],
            )

        updated_listings = []
        for listing in product_listings:
            try:
                # Get current inventory status
                part_doc = frappe.get_doc(
                    "Scrap Vehicle Extracted Part", listing.source_extracted_part
                )

                inventory_data = {
                    "listing_id": listing.external_listing_id,
                    "available": part_doc.status == "Available for Sale",
                    "quantity": 1 if part_doc.status == "Available for Sale" else 0,
                }

                # Update on marketplace
                result = update_marketplace_listing_inventory(connector, inventory_data)
                if result["status"] == "success":
                    updated_listings.append(listing.name)

            except Exception as e:
                frappe.log_error(f"Error updating inventory for listing {listing.name}: {str(e)}")

        return {
            "status": "success",
            "updated_listings": updated_listings,
            "total_updated": len(updated_listings),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_marketplace_listing_inventory(connector, inventory_data):
    """Update inventory for a specific listing on marketplace"""
    try:
        headers = get_auth_headers(connector)
        endpoint = f"{connector.api_endpoint.rstrip('/')}/listings/{inventory_data['listing_id']}/inventory"

        response = requests.put(endpoint, json=inventory_data, headers=headers, timeout=30)

        if response.status_code in [200, 204]:
            return {"status": "success"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def generate_marketplace_report(connector_name=None, report_type="summary", date_range="30"):
    """Generate marketplace performance report"""
    try:
        # Build filters
        filters = {}
        if connector_name:
            filters["marketplace_connector"] = connector_name

        from_date = frappe.utils.add_days(frappe.utils.today(), -int(date_range))
        filters["created_date"] = [">=", from_date]

        if report_type == "summary":
            return generate_summary_report(filters, date_range)
        elif report_type == "detailed":
            return generate_detailed_report(filters, date_range)
        elif report_type == "performance":
            return generate_performance_report(filters, date_range)
        else:
            return {"status": "error", "message": _("Invalid report type")}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_summary_report(filters, date_range):
    """Generate summary marketplace report"""
    # Get listing statistics
    listings = frappe.get_list(
        "Marketplace Product Listing",
        filters=filters,
        fields=["listing_status", "total_revenue", "views_count", "conversion_rate"],
    )

    # Calculate metrics
    total_listings = len(listings)
    active_listings = len([l for l in listings if l.listing_status == "Active"])
    sold_listings = len([l for l in listings if l.listing_status == "Sold"])
    total_revenue = sum([l.total_revenue or 0 for l in listings])
    avg_views = (
        sum([l.views_count or 0 for l in listings]) / total_listings if total_listings > 0 else 0
    )
    avg_conversion = (
        sum([l.conversion_rate or 0 for l in listings]) / total_listings
        if total_listings > 0
        else 0
    )

    return {
        "status": "success",
        "report_type": "summary",
        "date_range": date_range,
        "metrics": {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "sold_listings": sold_listings,
            "total_revenue": total_revenue,
            "average_views": round(avg_views, 1),
            "average_conversion_rate": round(avg_conversion, 2),
            "success_rate": round(
                (sold_listings / total_listings * 100) if total_listings > 0 else 0, 1
            ),
        },
    }


def generate_detailed_report(filters, date_range):
    """Generate detailed marketplace report"""
    listings = frappe.get_list("Marketplace Product Listing", filters=filters, fields="*")

    return {
        "status": "success",
        "report_type": "detailed",
        "date_range": date_range,
        "listings": listings,
    }


def generate_performance_report(filters, date_range):
    """Generate performance marketplace report"""
    # Get performance metrics by connector
    performance_data = frappe.db.sql(
        """
        SELECT 
            marketplace_connector,
            COUNT(*) as total_listings,
            AVG(views_count) as avg_views,
            AVG(conversion_rate) as avg_conversion,
            SUM(total_revenue) as total_revenue,
            AVG(average_response_time) as avg_response_time
        FROM `tabMarketplace Product Listing`
        WHERE created_date >= %s
        {filters}
        GROUP BY marketplace_connector
    """.format(
            filters=(
                " AND " + " AND ".join([f"{k} = '{v}'" for k, v in filters.items()])
                if filters
                else ""
            )
        ),
        [frappe.utils.add_days(frappe.utils.today(), -int(date_range))],
        as_dict=True,
    )

    return {
        "status": "success",
        "report_type": "performance",
        "date_range": date_range,
        "performance_data": performance_data,
    }
