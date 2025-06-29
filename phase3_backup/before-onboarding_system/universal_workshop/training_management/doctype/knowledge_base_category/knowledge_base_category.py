# -*- coding: utf-8 -*-
# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class KnowledgeBaseCategory(Document):
    def validate(self):
        """Validate category data before saving"""
        self.validate_basic_information()
        self.validate_hierarchy()
        self.validate_arabic_content()
        self.set_default_values()

    def validate_basic_information(self):
        """Validate basic category information"""
        # Validate category names
        if not self.category_name_en or not self.category_name_en.strip():
            frappe.throw(_("Category name (English) is required"))

        if not self.category_name_ar or not self.category_name_ar.strip():
            frappe.throw(_("Category name (Arabic) is required"))

        # Validate status
        if self.status not in ["Active", "Inactive", "Archived"]:
            frappe.throw(_("Invalid status. Must be Active, Inactive, or Archived"))

    def validate_hierarchy(self):
        """Validate category hierarchy to prevent circular references"""
        if self.parent_category:
            # Check if parent exists
            if not frappe.db.exists("Knowledge Base Category", self.parent_category):
                frappe.throw(_("Parent category {0} does not exist").format(self.parent_category))

            # Check for circular reference
            if self.name and self.parent_category == self.name:
                frappe.throw(_("Category cannot be its own parent"))

            # Check for deeper circular references
            current_parent = self.parent_category
            visited = set()
            while current_parent:
                if current_parent in visited:
                    frappe.throw(_("Circular reference detected in category hierarchy"))
                visited.add(current_parent)

                parent_doc = frappe.get_doc("Knowledge Base Category", current_parent)
                current_parent = parent_doc.parent_category

                # Additional check: prevent making this category a child of its own descendant
                if self.name and current_parent == self.name:
                    frappe.throw(_("Cannot create circular reference in category hierarchy"))

    def validate_arabic_content(self):
        """Validate Arabic text content"""
        # Check Arabic category name
        if self.category_name_ar and not self.is_arabic_text(self.category_name_ar):
            frappe.msgprint(_("Arabic category name should contain Arabic characters"), alert=True)

        # Check Arabic description
        if self.description_ar and not self.is_arabic_text(self.description_ar):
            frappe.msgprint(_("Arabic description should contain Arabic characters"), alert=True)

    def set_default_values(self):
        """Set default values before saving"""
        # Set created_by and creation_date for new records
        if not self.created_by:
            self.created_by = frappe.session.user

        if not self.creation_date:
            self.creation_date = now()

        # Set modified_by for all saves
        self.modified_by = frappe.session.user

        # Generate category code if not set
        if not self.category_code:
            self.category_code = self.generate_category_code()

        # Set default sort order
        if self.sort_order is None:
            self.sort_order = self.get_next_sort_order()

    def before_save(self):
        """Actions before saving the document"""
        # Update category code if names changed
        if self.has_value_changed("category_name_en") or self.has_value_changed("category_name_ar"):
            self.category_code = self.generate_category_code()

    def generate_category_code(self):
        """Generate unique category code based on name"""
        # Use English name as base, fallback to Arabic if English not available
        base_name = self.category_name_en if self.category_name_en else self.category_name_ar

        # Clean and format the name
        code_base = re.sub(r"[^a-zA-Z0-9\s]", "", base_name)
        code_base = re.sub(r"\s+", "_", code_base.strip())
        code_base = code_base.upper()

        # Add parent prefix if exists
        if self.parent_category:
            parent_doc = frappe.get_doc("Knowledge Base Category", self.parent_category)
            if parent_doc.category_code:
                code_base = f"{parent_doc.category_code}_{code_base}"

        # Ensure uniqueness
        base_code = code_base
        counter = 1
        while frappe.db.exists("Knowledge Base Category", {"category_code": code_base}):
            if (
                self.name
                and frappe.db.get_value("Knowledge Base Category", self.name, "category_code")
                == code_base
            ):
                break  # This is the current record
            code_base = f"{base_code}_{counter}"
            counter += 1

        return code_base

    def get_next_sort_order(self):
        """Get next sort order for the same level"""
        filters = {}
        if self.parent_category:
            filters["parent_category"] = self.parent_category
        else:
            filters["parent_category"] = ["is", "null"]

        last_order = frappe.db.get_value(
            "Knowledge Base Category", filters, "max(sort_order) as max_order"
        )

        return (last_order or 0) + 10

    @staticmethod
    def is_arabic_text(text):
        """Check if text contains Arabic characters"""
        if not text:
            return False
        # Arabic Unicode range
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return bool(arabic_pattern.search(text))

    def get_hierarchy_path(self):
        """Get full hierarchy path for this category"""
        path = []
        current = self

        while current:
            path.insert(
                0,
                {
                    "name": current.name,
                    "category_name_en": current.category_name_en,
                    "category_name_ar": current.category_name_ar,
                },
            )

            if current.parent_category:
                current = frappe.get_doc("Knowledge Base Category", current.parent_category)
            else:
                current = None

        return path

    def get_child_categories(self, include_inactive=False):
        """Get all child categories"""
        filters = {"parent_category": self.name}
        if not include_inactive:
            filters["status"] = "Active"

        return frappe.get_list(
            "Knowledge Base Category",
            filters=filters,
            fields=["name", "category_name_en", "category_name_ar", "status", "sort_order"],
            order_by="sort_order asc",
        )

    def get_article_count(self):
        """Get count of articles in this category"""
        return frappe.db.count("Knowledge Base Article", {"category": self.name})


# API Methods for Knowledge Base Category management


@frappe.whitelist()
def get_category_tree(language="en", include_inactive=False):
    """Get hierarchical category tree with Arabic/English support"""

    # Get all categories
    filters = {}
    if not include_inactive:
        filters["status"] = "Active"

    categories = frappe.get_list(
        "Knowledge Base Category",
        filters=filters,
        fields=[
            "name",
            "category_name_en",
            "category_name_ar",
            "parent_category",
            "icon_class",
            "sort_order",
        ],
        order_by="sort_order asc",
    )

    # Build tree structure
    tree = {}
    items = {}

    # First pass: create all items
    for cat in categories:
        name_field = "category_name_ar" if language == "ar" else "category_name_en"
        items[cat.name] = {
            "name": cat.name,
            "title": cat.get(name_field) or cat.category_name_en,
            "icon_class": cat.icon_class or "fa fa-folder",
            "children": [],
        }

    # Second pass: build hierarchy
    for cat in categories:
        if cat.parent_category and cat.parent_category in items:
            items[cat.parent_category]["children"].append(items[cat.name])
        else:
            tree[cat.name] = items[cat.name]

    return list(tree.values())


@frappe.whitelist()
def get_category_articles(category, language="en", status="Published"):
    """Get articles for a specific category"""

    filters = {"category": category}
    if status:
        filters["status"] = status

    name_field = "title_ar" if language == "ar" else "title_en"
    excerpt_field = "excerpt_ar" if language == "ar" else "excerpt_en"

    articles = frappe.get_list(
        "Knowledge Base Article",
        filters=filters,
        fields=[
            "name",
            "title_en",
            "title_ar",
            "excerpt_en",
            "excerpt_ar",
            "published_date",
            "view_count",
            "feedback_rating",
        ],
        order_by="published_date desc",
    )

    # Format for display
    for article in articles:
        article["title"] = article.get(name_field) or article.title_en
        article["excerpt"] = article.get(excerpt_field) or article.excerpt_en

    return articles


@frappe.whitelist()
def search_categories(query, language="en"):
    """Search categories with Arabic/English support"""

    if not query:
        return []

    # Search in both English and Arabic fields
    conditions = []
    query_like = f"%{query}%"

    conditions.append(f"category_name_en LIKE %(query)s")
    conditions.append(f"category_name_ar LIKE %(query)s")
    conditions.append(f"description_en LIKE %(query)s")
    conditions.append(f"description_ar LIKE %(query)s")
    conditions.append(f"meta_keywords LIKE %(query)s")

    sql = f"""
        SELECT name, category_name_en, category_name_ar, 
               description_en, description_ar, icon_class
        FROM `tabKnowledge Base Category`
        WHERE status = 'Active' 
        AND ({' OR '.join(conditions)})
        ORDER BY 
            CASE WHEN category_name_en LIKE %(query)s THEN 0 ELSE 1 END,
            CASE WHEN category_name_ar LIKE %(query)s THEN 0 ELSE 1 END,
            category_name_en
        LIMIT 20
    """

    results = frappe.db.sql(sql, {"query": query_like}, as_dict=True)

    # Format results based on language preference
    name_field = "category_name_ar" if language == "ar" else "category_name_en"
    desc_field = "description_ar" if language == "ar" else "description_en"

    for result in results:
        result["title"] = result.get(name_field) or result.category_name_en
        result["description"] = result.get(desc_field) or result.description_en

    return results


@frappe.whitelist()
def reorder_categories(category_orders):
    """Reorder categories by updating sort_order"""

    if not category_orders:
        return

    for order_info in category_orders:
        category_name = order_info.get("name")
        new_order = order_info.get("sort_order")

        if category_name and new_order is not None:
            frappe.db.set_value("Knowledge Base Category", category_name, "sort_order", new_order)

    frappe.db.commit()
    return _("Categories reordered successfully")
