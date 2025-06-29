# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""Enhanced search override for Arabic-aware parts and automotive components"""

import frappe
from frappe import _
from universal_workshop.utils.arabic_utils import clean_search_term, normalize_arabic_text


@frappe.whitelist()
def enhanced_search_link(
	doctype,
	txt,
	query=None,
	filters=None,
	page_length=20,
	searchfield=None,
	reference_doctype=None,
	ignore_user_permissions=False,
):
	"""Enhanced search for automotive parts with Arabic support"""

	# Use original search for non-automotive doctypes
	if doctype not in ["Item", "Customer", "Supplier", "Vehicle"]:
		return frappe.desk.search.search_link(
			doctype, txt, query, filters, page_length, searchfield, reference_doctype, ignore_user_permissions
		)

	# Enhanced Item search for automotive parts
	if doctype == "Item":
		return enhanced_item_search(txt, filters, page_length)

	# Enhanced Customer search with Arabic support
	elif doctype == "Customer":
		return enhanced_customer_search(txt, filters, page_length)

	# Enhanced Supplier search with Arabic support
	elif doctype == "Supplier":
		return enhanced_supplier_search(txt, filters, page_length)

	# Enhanced Vehicle search
	elif doctype == "Vehicle":
		return enhanced_vehicle_search(txt, filters, page_length)

	# Fallback to original search
	return frappe.desk.search.search_link(
		doctype, txt, query, filters, page_length, searchfield, reference_doctype, ignore_user_permissions
	)


def enhanced_item_search(txt, filters=None, page_length=20):
	"""Enhanced Item search with automotive parts support and Arabic text"""

	if not txt:
		txt = ""

	# Clean search term
	search_term = clean_search_term(txt)

	# Build conditions
	conditions = []
	values = []

	# Base filters
	conditions.append("disabled = 0")

	# Apply additional filters
	if filters:
		for key, value in filters.items():
			if key and value:
				conditions.append(f"{key} = %s")
				values.append(value)

	# Search conditions
	if search_term:
		search_conditions = [
			"item_code LIKE %s",
			"item_name LIKE %s",
			"oem_part_number LIKE %s",
			"aftermarket_part_number LIKE %s",
			"description LIKE %s",
		]

		search_values = [f"%{search_term}%"] * 5
		conditions.append(f"({' OR '.join(search_conditions)})")
		values.extend(search_values)

	# Cross-reference search
	cross_ref_query = ""
	if search_term:
		cross_ref_query = """
            UNION
            SELECT DISTINCT i.name, i.item_code, i.item_name,
                   CONCAT(i.item_name, ' (Cross-Ref: ', pcr.cross_ref_number, ')') as description,
                   i.standard_rate
            FROM `tabItem` i
            INNER JOIN `tabPart Cross Reference` pcr ON i.name = pcr.parent
            WHERE pcr.cross_ref_number LIKE %s
            AND i.disabled = 0
        """
		values.append(f"%{search_term}%")

	# Build final query
	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
        SELECT name, item_code, item_name, description, standard_rate
        FROM `tabItem`
        WHERE {where_clause}
        {cross_ref_query}
        ORDER BY
            CASE WHEN is_fast_moving = 1 THEN 0 ELSE 1 END,
            CASE WHEN item_code LIKE %s THEN 0 ELSE 1 END,
            item_name
        LIMIT {page_length}
    """

	# Add exact match parameter for sorting
	values.append(f"{search_term}%")

	return frappe.db.sql(query, values, as_dict=True)


def enhanced_customer_search(txt, filters=None, page_length=20):
	"""Enhanced Customer search with Arabic support"""

	if not txt:
		txt = ""

	search_term = clean_search_term(txt)

	conditions = []
	values = []

	# Base filters
	conditions.append("disabled = 0")

	# Apply additional filters
	if filters:
		for key, value in filters.items():
			if key and value:
				conditions.append(f"{key} = %s")
				values.append(value)

	# Search conditions (both English and Arabic fields)
	if search_term:
		search_conditions = [
			"customer_name LIKE %s",
			"customer_name_ar LIKE %s",
			"customer_code LIKE %s",
			"mobile_no LIKE %s",
			"email_id LIKE %s",
		]

		search_values = [f"%{search_term}%"] * 5
		conditions.append(f"({' OR '.join(search_conditions)})")
		values.extend(search_values)

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
        SELECT name, customer_name, customer_name_ar, customer_code,
               mobile_no, email_id
        FROM `tabCustomer`
        WHERE {where_clause}
        ORDER BY
            CASE WHEN customer_name LIKE %s THEN 0 ELSE 1 END,
            customer_name
        LIMIT {page_length}
    """

	values.append(f"{search_term}%")

	return frappe.db.sql(query, values, as_dict=True)


def enhanced_supplier_search(txt, filters=None, page_length=20):
	"""Enhanced Supplier search with Arabic support"""

	if not txt:
		txt = ""

	search_term = clean_search_term(txt)

	conditions = []
	values = []

	# Base filters
	conditions.append("disabled = 0")

	# Apply additional filters
	if filters:
		for key, value in filters.items():
			if key and value:
				conditions.append(f"{key} = %s")
				values.append(value)

	# Search conditions
	if search_term:
		search_conditions = ["supplier_name LIKE %s", "supplier_code LIKE %s"]

		search_values = [f"%{search_term}%"] * 2
		conditions.append(f"({' OR '.join(search_conditions)})")
		values.extend(search_values)

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
        SELECT name, supplier_name, supplier_code
        FROM `tabSupplier`
        WHERE {where_clause}
        ORDER BY
            CASE WHEN supplier_name LIKE %s THEN 0 ELSE 1 END,
            supplier_name
        LIMIT {page_length}
    """

	values.append(f"{search_term}%")

	return frappe.db.sql(query, values, as_dict=True)


def enhanced_vehicle_search(txt, filters=None, page_length=20):
	"""Enhanced Vehicle search"""

	if not txt:
		txt = ""

	search_term = clean_search_term(txt)

	conditions = []
	values = []

	# Apply additional filters
	if filters:
		for key, value in filters.items():
			if key and value:
				conditions.append(f"{key} = %s")
				values.append(value)

	# Search conditions
	if search_term:
		search_conditions = [
			"license_plate LIKE %s",
			"vin LIKE %s",
			"make LIKE %s",
			"model LIKE %s",
			"CONCAT(year, ' ', make, ' ', model) LIKE %s",
		]

		search_values = [f"%{search_term}%"] * 5
		conditions.append(f"({' OR '.join(search_conditions)})")
		values.extend(search_values)

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
        SELECT name, license_plate, vin, make, model, year,
               CONCAT(year, ' ', make, ' ', model, ' (', license_plate, ')') as display_name
        FROM `tabVehicle`
        WHERE {where_clause}
        ORDER BY
            CASE WHEN license_plate LIKE %s THEN 0 ELSE 1 END,
            make, model, year
        LIMIT {page_length}
    """

	values.append(f"{search_term}%")

	return frappe.db.sql(query, values, as_dict=True)
