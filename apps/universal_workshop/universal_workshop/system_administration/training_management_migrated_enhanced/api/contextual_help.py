import frappe
from frappe import _


@frappe.whitelist()
def get_contextual_help(context=None, page=None):
    """Get contextual help content"""
    try:
        # Return empty help for now - can be expanded later
        return {"help_content": [], "context": context or "general", "page": page or "home"}
    except Exception as e:
        frappe.log_error(f"Error getting contextual help: {e}")
        return {"help_content": [], "error": "Failed to load help content"}


@frappe.whitelist()
def search_help_content(query=None, context=None):
    """Search help content"""
    try:
        # Return empty search results for now - can be expanded later
        return {"results": [], "query": query or "", "context": context or "general"}
    except Exception as e:
        frappe.log_error(f"Error searching help content: {e}")
        return {"results": [], "error": "Failed to search help content"}
