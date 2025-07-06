# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now


class KnowledgeBaseArticle(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    # Website configuration
    website = frappe._dict(
        {
            "route": "knowledge-base",
            "condition_field": "is_public",
            "template": "templates/knowledge_base_article.html",
            "page_title_field": "title_en",
        }
    )

    def validate(self):
        """Validate knowledge base article before saving"""
        self.validate_basic_info()
        self.validate_content()
        self.validate_translation_status()
        self.validate_arabic_content()
        self.set_metadata()

    def validate_basic_info(self):
        """Validate basic article information"""
        if not self.title_en:
            frappe.throw(_("English title is required"))

        if not self.title_ar:
            frappe.throw(_("Arabic title is required"))

        if not self.article_code:
            self.article_code = self.generate_article_code()

        # Validate article code format
        if not re.match(r"^KB-\d{5}$", self.article_code):
            frappe.throw(_("Article code must follow format: KB-00001"))

        # Validate category
        if not self.category:
            frappe.throw(_("Category is required"))

        # Set default author
        if not self.author:
            self.author = frappe.session.user

    def validate_content(self):
        """Validate content based on status"""
        if self.status in ["Approved", "Published"]:
            if not self.content_en and not self.content_ar:
                frappe.throw(_("Content is required for published articles"))

            if self.is_public and not self.excerpt_en and not self.excerpt_ar:
                frappe.throw(_("Excerpt is required for public articles"))

        # Validate parent article
        if self.parent_article and self.parent_article == self.name:
            frappe.throw(_("Article cannot be its own parent"))

    def validate_translation_status(self):
        """Validate and update translation status"""
        has_english = bool(self.content_en and self.title_en)
        has_arabic = bool(self.content_ar and self.title_ar)

        if has_english and has_arabic:
            self.translation_status = "Complete"
        elif has_english or has_arabic:
            self.translation_status = "Partial"
        else:
            self.translation_status = "Missing"

        # Update workflow status based on translation
        if self.status == "Pending Translation" and self.translation_status == "Complete":
            self.status = "In Review (AR)" if has_english else "In Review (EN)"

    def validate_arabic_content(self):
        """Validate Arabic content fields"""
        if self.title_ar and not self.contains_arabic_text(self.title_ar):
            frappe.msgprint(
                _("Warning: Arabic title appears to contain no Arabic characters"), alert=True
            )

        if self.content_ar and not self.contains_arabic_text(self.content_ar):
            frappe.msgprint(
                _("Warning: Arabic content appears to contain no Arabic characters"), alert=True
            )

    def set_metadata(self):
        """Set creation and modification metadata"""
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_date = now()

        self.modified_by = frappe.session.user
        self.last_modified_date = now()

        # Set review dates
        if not self.last_reviewed_date and self.status == "Published":
            self.last_reviewed_date = frappe.utils.today()

        if not self.next_review_date and self.review_frequency:
            self.next_review_date = self.calculate_next_review_date()

        # Set published date
        if self.status == "Published" and not self.published_date:
            self.published_date = now()

    def before_save(self):
        """Actions before saving the document"""
        # Auto-generate meta titles if not provided
        if not self.meta_title_en and self.title_en:
            self.meta_title_en = self.title_en

        if not self.meta_title_ar and self.title_ar:
            self.meta_title_ar = self.title_ar

        # Auto-generate excerpts if not provided
        if not self.excerpt_en and self.content_en:
            self.excerpt_en = self.generate_excerpt(self.content_en, "en")

        if not self.excerpt_ar and self.content_ar:
            self.excerpt_ar = self.generate_excerpt(self.content_ar, "ar")

    def after_insert(self):
        """Actions after inserting new article"""
        frappe.logger().info(
            f"Knowledge Base Article created: {self.article_code} - {self.title_en}"
        )

    def generate_article_code(self):
        """Generate unique article code"""
        # Get the next sequence number
        last_article = frappe.db.sql(
            """
            SELECT article_code FROM `tabKnowledge Base Article`
            WHERE article_code LIKE 'KB-%'
            ORDER BY article_code DESC LIMIT 1
        """
        )

        if last_article:
            last_num = int(last_article[0][0].split("-")[1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"KB-{new_num:05d}"

    def calculate_next_review_date(self):
        """Calculate next review date based on frequency"""
        if not self.review_frequency:
            return None

        base_date = (
            get_datetime(self.last_reviewed_date) if self.last_reviewed_date else get_datetime()
        )

        frequency_mapping = {
            "Monthly": 30,
            "Quarterly": 90,
            "Bi-annually": 180,
            "Annually": 365,
            "As Needed": None,
        }

        days = frequency_mapping.get(self.review_frequency)
        if days:
            return (base_date + timedelta(days=days)).date()

        return None

    def generate_excerpt(self, content, language="en"):
        """Generate excerpt from content"""
        if not content:
            return ""

        # Remove HTML tags

        clean_text = re.sub("<[^<]+?>", "", content)

        # Get first 150 characters
        excerpt = clean_text[:150].strip()

        if len(clean_text) > 150:
            # Try to break at word boundary
            last_space = excerpt.rfind(" ")
            if last_space > 100:  # Ensure minimum length
                excerpt = excerpt[:last_space]
            excerpt += "..."

        return excerpt

    def contains_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        if not text:
            return False
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return arabic_pattern.search(text) is not None

    @frappe.whitelist()
    def increment_view_count(self):
        """Increment view count for analytics"""
        frappe.db.sql(
            "UPDATE `tabKnowledge Base Article` SET view_count = view_count + 1 WHERE name = %s",
            [self.name],
        )
        frappe.db.commit()

    @frappe.whitelist()
    def publish_article(self):
        """Publish the article"""
        if self.translation_status == "Missing":
            frappe.throw(_("Cannot publish article without content"))

        if self.status != "Approved":
            frappe.throw(_("Article must be approved before publishing"))

        self.status = "Published"
        self.published_date = now()
        self.save()

        frappe.msgprint(_("Article published successfully"))
        return True

    @frappe.whitelist()
    def unpublish_article(self):
        """Unpublish the article"""
        if self.status == "Published":
            self.status = "Approved"
            self.save()
            frappe.msgprint(_("Article unpublished"))
        return True

    @frappe.whitelist()
    def add_feedback(self, rating, comment=""):
        """Add user feedback"""
        # Create feedback record
        feedback = frappe.new_doc("Knowledge Base Feedback")
        feedback.article = self.name
        feedback.user = frappe.session.user
        feedback.rating = rating
        feedback.comment = comment
        feedback.insert()

        # Update average rating
        self.update_feedback_rating()
        return True

    def update_feedback_rating(self):
        """Update average feedback rating"""
        avg_rating = frappe.db.sql(
            """
            SELECT AVG(rating) as avg_rating 
            FROM `tabKnowledge Base Feedback` 
            WHERE article = %s
        """,
            [self.name],
            as_dict=True,
        )

        if avg_rating and avg_rating[0].avg_rating:
            self.feedback_rating = flt(avg_rating[0].avg_rating, 2)
            frappe.db.sql(
                "UPDATE `tabKnowledge Base Article` SET feedback_rating = %s WHERE name = %s",
                [self.feedback_rating, self.name],
            )

    @frappe.whitelist()
    def get_article_content(self, language=None):
        """Get article content in specified language"""
        if not language:
            language = frappe.local.lang or "en"

        content_data = {
            "title": self.title_ar if language == "ar" else self.title_en,
            "content": self.content_ar if language == "ar" else self.content_en,
            "excerpt": self.excerpt_ar if language == "ar" else self.excerpt_en,
            "meta_title": self.meta_title_ar if language == "ar" else self.meta_title_en,
            "meta_description": (
                self.meta_description_ar if language == "ar" else self.meta_description_en
            ),
            "language": language,
            "translation_available": self.translation_status == "Complete",
        }

        # Increment view count
        self.increment_view_count()

        return content_data


@frappe.whitelist()
def search_articles(query, language="en", category=None, limit=20):
    """Search knowledge base articles with Arabic support"""
    if not query:
        return []

    # Build search conditions
    conditions = ["(status = 'Published' OR is_public = 1)"]

    if category:
        conditions.append(f"category = '{category}'")

    # Language-specific search fields
    if language == "ar":
        search_fields = ["title_ar", "content_ar", "excerpt_ar", "search_keywords_ar"]
    else:
        search_fields = ["title_en", "content_en", "excerpt_en", "search_keywords_en"]

    # Build search query
    search_conditions = []
    for field in search_fields:
        search_conditions.append(f"{field} LIKE '%{query}%'")

    if search_conditions:
        conditions.append(f"({' OR '.join(search_conditions)})")

    where_clause = " AND ".join(conditions)

    # Execute search
    articles = frappe.db.sql(
        f"""
        SELECT 
            name, article_code, 
            title_en, title_ar,
            excerpt_en, excerpt_ar,
            category, published_date,
            view_count, feedback_rating
        FROM `tabKnowledge Base Article`
        WHERE {where_clause}
        ORDER BY 
            CASE WHEN title_en LIKE '%{query}%' OR title_ar LIKE '%{query}%' THEN 1 ELSE 2 END,
            feedback_rating DESC,
            view_count DESC
        LIMIT {limit}
    """,
        as_dict=True,
    )

    return articles


@frappe.whitelist()
def get_featured_articles(language="en", limit=5):
    """Get featured articles"""
    articles = frappe.get_list(
        "Knowledge Base Article",
        filters={"is_featured": 1, "status": "Published"},
        fields=[
            "name",
            "article_code",
            "title_en",
            "title_ar",
            "excerpt_en",
            "excerpt_ar",
            "category",
            "published_date",
        ],
        order_by="published_date desc",
        limit=limit,
    )

    return articles


@frappe.whitelist()
def get_articles_by_category(category, language="en", limit=10):
    """Get articles by category"""
    articles = frappe.get_list(
        "Knowledge Base Article",
        filters={"category": category, "status": "Published"},
        fields=[
            "name",
            "article_code",
            "title_en",
            "title_ar",
            "excerpt_en",
            "excerpt_ar",
            "published_date",
            "view_count",
        ],
        order_by="view_count desc",
        limit=limit,
    )

    return articles
