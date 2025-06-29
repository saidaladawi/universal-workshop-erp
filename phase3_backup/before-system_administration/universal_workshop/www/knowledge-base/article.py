# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import cstr

def get_context(context):
    """Get context for knowledge base article page"""
    
    # Get article name from URL
    article_name = frappe.form_dict.get('name') or frappe.local.request.path.split('/')[-1]
    
    if not article_name:
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    
    # Get article
    try:
        article = frappe.get_doc('Knowledge Base Article', article_name)
    except frappe.DoesNotExistError:
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    
    # Check if article is published and public
    if article.status != 'Published' or not article.is_public:
        if not frappe.has_permission('Knowledge Base Article', 'read', article.name):
            frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    
    # Get current language
    language = frappe.local.lang or 'en'
    
    # Format article for display
    title_field = 'title_ar' if language == 'ar' else 'title_en'
    content_field = 'content_ar' if language == 'ar' else 'content_en'
    
    context.article = article
    context.title = article.get(title_field) or article.title_en
    context.content = article.get(content_field) or article.content_en
    context.language = language
    context.is_rtl = language == 'ar'
    context.text_direction = 'rtl' if language == 'ar' else 'ltr'
    
    # Get category information
    if article.category:
        try:
            category = frappe.get_doc('Knowledge Base Category', article.category)
            name_field = 'category_name_ar' if language == 'ar' else 'category_name_en'
            context.category_name = category.get(name_field) or category.category_name_en
            context.category_route = f"/knowledge-base/category/{category.name}"
        except frappe.DoesNotExistError:
            context.category_name = article.category
            context.category_route = "#"
    
    # Get related articles
    context.related_articles = get_related_articles(article, language, limit=5)
    
    # Increment view count
    try:
        frappe.db.sql("UPDATE `tabKnowledge Base Article` SET view_count = COALESCE(view_count, 0) + 1 WHERE name = %s", [article.name])
        frappe.db.commit()
    except Exception:
        pass  # Ignore errors in view count update
    
    # Breadcrumb
    context.parents = [
        {"title": _("Home"), "route": "/"},
        {"title": _("Knowledge Base"), "route": "/knowledge-base"},
        {"title": context.category_name, "route": context.category_route}
    ]
    
    return context

def get_related_articles(article, language, limit=5):
    """Get related articles based on category and tags"""
    
    filters = {
        'status': 'Published',
        'is_public': 1,
        'name': ['!=', article.name]
    }
    
    # Add category filter if available
    if article.category:
        filters['category'] = article.category
    
    title_field = 'title_ar' if language == 'ar' else 'title_en'
    excerpt_field = 'excerpt_ar' if language == 'ar' else 'excerpt_en'
    
    articles = frappe.get_list(
        'Knowledge Base Article',
        filters=filters,
        fields=['name', 'title_en', 'title_ar', 'excerpt_en', 'excerpt_ar', 
               'published_date', 'view_count'],
        order_by='published_date desc',
        limit=limit
    )
    
    # Format articles for display
    for art in articles:
        art['title'] = art.get(title_field) or art.title_en
        art['excerpt'] = art.get(excerpt_field) or art.excerpt_en
        art['route'] = f"/knowledge-base/article/{art.name}"
    
    return articles
