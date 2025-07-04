# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional

import frappe
from frappe import _


@frappe.whitelist()
def search_customers(query: str, filters: str | None = None, page: int = 1, page_size: int = 20):
	"""
	Search customers with Elasticsearch fuzzy matching

	Args:
	    query: Search query string
	    filters: JSON string of additional filters
	    page: Page number for pagination (1-based)
	    page_size: Number of results per page

	Returns:
	    Dict containing search results and pagination info
	"""
	try:
		from .customer_indexer import CustomerIndexer

		# Parse filters if provided
		search_filters = None
		if filters:
			import json

			search_filters = json.loads(filters)

		# Calculate offset for pagination
		from_offset = (page - 1) * page_size

		# Perform search
		indexer = CustomerIndexer()
		results = indexer.search_customers(
			query=query, filters=search_filters, size=page_size, from_=from_offset
		)

		# Calculate pagination info
		total_pages = (results["total"] + page_size - 1) // page_size

		return {
			"success": True,
			"data": {
				"customers": results["hits"],
				"pagination": {
					"current_page": page,
					"page_size": page_size,
					"total_results": results["total"],
					"total_pages": total_pages,
					"has_next": page < total_pages,
					"has_previous": page > 1,
				},
				"search_info": {"max_score": results["max_score"], "query": query, "filters": search_filters},
			},
		}

	except ImportError:
		return {
			"success": False,
			"message": _("Elasticsearch integration not available. Please install elasticsearch package."),
			"fallback": _fallback_customer_search(query, search_filters, page, page_size),
		}
	except Exception as e:
		frappe.log_error(f"Customer search failed: {e!s}")
		return {
			"success": False,
			"message": _("Search failed. Please try again."),
			"fallback": _fallback_customer_search(query, search_filters, page, page_size),
		}


def _fallback_customer_search(query: str, filters: dict | None, page: int, page_size: int):
	"""
	Fallback search using Frappe's built-in database search
	"""
	try:
		# Build SQL filters
		sql_filters = {"disabled": 0}
		if filters:
			sql_filters.update(filters)

		# Build search conditions for customer name and Arabic name
		search_conditions = []
		if query:
			search_conditions = [
				["customer_name", "like", f"%{query}%"],
				["customer_name_ar", "like", f"%{query}%"],
				["customer_code", "like", f"%{query}%"],
				["email_id", "like", f"%{query}%"],
			]

		# Get total count
		total_count = frappe.db.count("Customer", filters=sql_filters)

		# Get paginated results
		start = (page - 1) * page_size
		customers = frappe.get_list(
			"Customer",
			filters=sql_filters,
			or_filters=search_conditions if search_conditions else None,
			fields=[
				"name",
				"customer_name",
				"customer_name_ar",
				"customer_code",
				"customer_type",
				"customer_group",
				"territory",
				"email_id",
				"mobile_no",
				"disabled",
				"creation",
				"modified",
			],
			order_by="modified desc",
			start=start,
			page_length=page_size,
		)

		total_pages = (total_count + page_size - 1) // page_size

		return {
			"customers": customers,
			"pagination": {
				"current_page": page,
				"page_size": page_size,
				"total_results": total_count,
				"total_pages": total_pages,
				"has_next": page < total_pages,
				"has_previous": page > 1,
			},
			"search_info": {"query": query, "filters": filters, "search_type": "database_fallback"},
		}

	except Exception as e:
		frappe.log_error(f"Fallback customer search failed: {e!s}")
		return {"customers": [], "pagination": {}, "search_info": {}}


@frappe.whitelist()
def get_customer_suggestions(field: str, text: str, limit: int = 5):
	"""
	Get auto-completion suggestions for customer fields

	Args:
	    field: Field name to get suggestions for
	    text: Partial text to complete
	    limit: Maximum number of suggestions

	Returns:
	    List of suggestions
	"""
	try:

		indexer = CustomerIndexer()
		suggestions = indexer.get_customer_suggestions(field, text, limit)

		return {"success": True, "suggestions": suggestions}

	except ImportError:
		# Fallback to database suggestions
		return _fallback_customer_suggestions(field, text, limit)
	except Exception as e:
		frappe.log_error(f"Customer suggestions failed: {e!s}")
		return _fallback_customer_suggestions(field, text, limit)


def _fallback_customer_suggestions(field: str, text: str, limit: int):
	"""
	Fallback suggestions using database LIKE queries
	"""
	try:
		# Map field names to actual Customer DocType fields
		field_mapping = {
			"customer_name": "customer_name",
			"customer_name_ar": "customer_name_ar",
			"customer_code": "customer_code",
			"email_id": "email_id",
			"mobile_no": "mobile_no",
		}

		db_field = field_mapping.get(field, "customer_name")

		# Get suggestions from database
		suggestions = frappe.db.sql(
			f"""
            SELECT DISTINCT {db_field}
            FROM `tabCustomer`
            WHERE {db_field} LIKE %(text)s
            AND disabled = 0
            AND {db_field} IS NOT NULL
            AND {db_field} != ''
            ORDER BY {db_field}
            LIMIT %(limit)s
        """,
			{"text": f"{text}%", "limit": limit},
			as_dict=False,
		)

		# Extract values from tuples
		suggestion_list = [s[0] for s in suggestions if s[0]]

		return {"success": True, "suggestions": suggestion_list, "search_type": "database_fallback"}

	except Exception as e:
		frappe.log_error(f"Fallback suggestions failed: {e!s}")
		return {"success": False, "suggestions": []}


@frappe.whitelist()
def reindex_customers():
	"""
	Reindex all customers - Admin only function

	Returns:
	    Status of reindexing operation
	"""
	# Check permissions
	if not frappe.has_permission("Customer", "write"):
		frappe.throw(_("Insufficient permissions to reindex customers"))

	try:

		indexer = CustomerIndexer()

		# Setup index first
		if not indexer.setup_customer_index():
			return {"success": False, "message": _("Failed to setup customer index")}

		# Bulk index customers
		results = indexer.bulk_index_customers()

		return {"success": True, "message": _("Customer reindexing completed"), "results": results}

	except ImportError:
		return {
			"success": False,
			"message": _("Elasticsearch not available. Please install elasticsearch package."),
		}
	except Exception as e:
		frappe.log_error(f"Customer reindexing failed: {e!s}")
		return {"success": False, "message": _("Reindexing failed. Check error logs for details.")}


@frappe.whitelist()
def search_status():
	"""
	Get the status of the search system

	Returns:
	    Dict with system status and configuration
	"""
	try:
		from .elasticsearch_client import get_elasticsearch_client

		es_client = get_elasticsearch_client()

		status = {
			"elasticsearch_available": es_client.is_available(),
			"search_type": "elasticsearch" if es_client.is_available() else "database_fallback",
		}

		if es_client.is_available():
			# Get index information
			index_name = es_client.get_index_name("Customer")
			try:
				index_stats = es_client.client.indices.stats(index=index_name)
				status["index_stats"] = {
					"document_count": index_stats["_all"]["primaries"]["docs"]["count"],
					"index_size": index_stats["_all"]["primaries"]["store"]["size_in_bytes"],
				}
			except Exception:
				status["index_stats"] = {"document_count": 0, "index_size": 0}

		return {"success": True, "status": status}

	except Exception as e:
		frappe.log_error(f"Search status check failed: {e!s}")
		return {"success": False, "message": _("Failed to get search status")}


@frappe.whitelist()
def advanced_customer_search(
	query: str = "",
	customer_type: str = "",
	customer_group: str = "",
	territory: str = "",
	language: str = "",
	date_from: str = "",
	date_to: str = "",
	page: int = 1,
	page_size: int = 20,
):
	"""
	Advanced customer search with multiple filters

	Args:
	    query: Text search query
	    customer_type: Filter by customer type
	    customer_group: Filter by customer group
	    territory: Filter by territory
	    language: Filter by preferred language
	    date_from: Filter by creation date from
	    date_to: Filter by creation date to
	    page: Page number
	    page_size: Results per page

	Returns:
	    Search results with applied filters
	"""
	filters = {}

	# Build filters
	if customer_type:
		filters["customer_type"] = customer_type
	if customer_group:
		filters["customer_group"] = customer_group
	if territory:
		filters["territory"] = territory
	if language:
		filters["preferred_language"] = language

	# Date range filter (for Elasticsearch this would need special handling)
	if date_from or date_to:
		filters["date_range"] = {"from": date_from, "to": date_to}

	# Use the main search function
	return search_customers(
		query=query, filters=frappe.as_json(filters) if filters else None, page=page, page_size=page_size
	)
