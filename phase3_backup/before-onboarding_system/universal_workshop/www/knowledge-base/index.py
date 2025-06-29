# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import cstr
from universal_workshop.training_management.doctype.knowledge_base_category.knowledge_base_category import get_category_tree
from universal_workshop.training_management.doctype.knowledge_base_article.knowledge_base_article import search_knowledge_base

def get_context(context):
    """Get context for knowledge base index page"""
    
    # Get current language
    language = frappe.local.lang or 'en'
    
    # Set page metadata
    context.title = _("Knowledge Base")
    context.description = _("Comprehensive documentation and help articles for Universal Workshop ERP")
    
    # Get search query if provided
    search_query = frappe.form_dict.get('q', '').strip()
    category_filter = frappe.form_dict.get('category', '')
    
    # Get categories for navigation
    try:
        context.categories = get_category_tree(language=language, include_inactive=False)
    except Exception:
        context.categories = []
    
    # Get featured articles
    context.featured_articles = get_featured_articles(language)
    
    # Handle search
    if search_query:
        context.search_query = search_query
        context.search_results = search_knowledge_base(
            query=search_query,
            language=language,
            category=category_filter if category_filter else None,
            limit=20
        )
    
    # Get recent articles
    context.recent_articles = get_recent_articles(language, limit=10)
    
    # Get popular categories
    context.popular_categories = get_popular_categories(language, limit=6)
    
    # Set language and RTL support
    context.language = language
    context.is_rtl = language == 'ar'
    context.text_direction = 'rtl' if language == 'ar' else 'ltr'
    
    # Breadcrumb
    context.parents = [{"title": _("Home"), "route": "/"}]
    
    return context

def get_featured_articles(language, limit=6):
    """Get featured articles for the homepage"""
    
    filters = {
        'status': 'Published',
        'is_featured': 1,
        'is_public': 1
    }
    
    title_field = 'title_ar' if language == 'ar' else 'title_en'
    excerpt_field = 'excerpt_ar' if language == 'ar' else 'excerpt_en'
    
    articles = frappe.get_list(
        'Knowledge Base Article',
        filters=filters,
        fields=['name', 'title_en', 'title_ar', 'excerpt_en', 'excerpt_ar', 
               'category', 'published_date', 'view_count'],
        order_by='published_date desc',
        limit=limit
    )
    
    # Format articles for display
    for article in articles:
        article['title'] = article.get(title_field) or article.title_en
        article['excerpt'] = article.get(excerpt_field) or article.excerpt_en
        article['route'] = f"/knowledge-base/article/{article.name}"
    
    return articles

def get_recent_articles(language, limit=10):
    """Get recently published articles"""
    
    filters = {
        'status': 'Published',
        'is_public': 1
    }
    
    title_field = 'title_ar' if language == 'ar' else 'title_en'
    
    articles = frappe.get_list(
        'Knowledge Base Article',
        filters=filters,
        fields=['name', 'title_en', 'title_ar', 'category', 'published_date'],
        order_by='published_date desc',
        limit=limit
    )
    
    # Format articles for display
    for article in articles:
        article['title'] = article.get(title_field) or article.title_en
        article['route'] = f"/knowledge-base/article/{article.name}"
    
    return articles

def get_popular_categories(language, limit=6):
    """Get popular categories based on article count"""
    
    sql = """
        SELECT 
            c.name,
            c.category_name_en,
            c.category_name_ar,
            c.description_en,
            c.description_ar,
            c.icon_class,
            COUNT(a.name) as article_count
        FROM `tabKnowledge Base Category` c
        LEFT JOIN `tabKnowledge Base Article` a ON a.category = c.name 
            AND a.status = 'Published' AND a.is_public = 1
        WHERE c.status = 'Active' AND c.is_public = 1
        GROUP BY c.name
        ORDER BY article_count DESC, c.sort_order ASC
        LIMIT %s
    """
    
    categories = frappe.db.sql(sql, [limit], as_dict=True)
    
    # Format categories for display
    name_field = 'category_name_ar' if language == 'ar' else 'category_name_en'
    desc_field = 'description_ar' if language == 'ar' else 'description_en'
    
    for category in categories:
        category['title'] = category.get(name_field) or category.category_name_en
        category['description'] = category.get(desc_field) or category.description_en
        category['route'] = f"/knowledge-base/category/{category.name}"
        category['icon'] = category.icon_class or 'fa fa-folder-o'
    
    return categories
