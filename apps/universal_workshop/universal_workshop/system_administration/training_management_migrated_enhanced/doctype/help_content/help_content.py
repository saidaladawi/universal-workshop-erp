# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, cint, flt, get_url
import json
import re


class HelpContent(Document):
	"""Help Content DocType for contextual help system"""

	def validate(self):
		"""Validate help content data"""
		self.validate_content_key()
		self.validate_target_configuration()
		self.validate_trigger_conditions()
		self.auto_populate_fields()

	def before_save(self):
		"""Set default values before saving"""
		self.set_metadata_fields()

	def on_update(self):
		"""Clear help content cache when updated"""
		frappe.cache().delete_key("help_content_cache")

	def validate_content_key(self):
		"""Validate content key uniqueness and format"""
		if not self.content_key:
			# Auto-generate content key from title
			self.content_key = frappe.scrub(self.title).replace('_', '-')

		# Check for uniqueness
		existing = frappe.db.exists(
			"Help Content",
			{"content_key": self.content_key, "name": ["!=", self.name]}
		)
		if existing:
			frappe.throw(_("Content Key '{0}' already exists").format(self.content_key))

	def validate_target_configuration(self):
		"""Validate target configuration"""
		if self.target_doctype and not frappe.db.exists("DocType", self.target_doctype):
			frappe.throw(_("Target DocType '{0}' does not exist").format(self.target_doctype))

		if self.target_field and self.target_doctype:
			# Validate field exists in the DocType
			meta = frappe.get_meta(self.target_doctype)
			if not meta.get_field(self.target_field):
				frappe.throw(_("Field '{0}' does not exist in DocType '{1}'").format(
					self.target_field, self.target_doctype
				))

	def validate_trigger_conditions(self):
		"""Validate JSON format of trigger conditions"""
		if self.trigger_conditions:
			try:
				json.loads(self.trigger_conditions)
			except json.JSONDecodeError:
				frappe.throw(_("Trigger Conditions must be valid JSON"))

	def auto_populate_fields(self):
		"""Auto-populate related fields"""
		# Auto-populate article titles
		for doc_ref in self.related_documentation:
			if doc_ref.knowledge_base_article and not doc_ref.article_title:
				doc_ref.article_title = frappe.db.get_value(
					"Knowledge Base Article", doc_ref.knowledge_base_article, "title"
				)

		# Auto-populate module titles
		for training_ref in self.related_training_modules:
			if training_ref.training_module and not training_ref.module_title:
				training_ref.module_title = frappe.db.get_value(
					"Training Module", training_ref.training_module, "title"
				)

	def set_metadata_fields(self):
		"""Set metadata fields"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = now_datetime()

		self.last_updated_by = frappe.session.user
		self.last_updated_on = now_datetime()

	@frappe.whitelist()
	def record_view(self):
		"""Record a view of this help content"""
		self.view_count = cint(self.view_count) + 1
		self.save(ignore_permissions=True)

		# Log usage for analytics
		self.log_help_usage("view")

	@frappe.whitelist()
	def record_helpfulness_rating(self, rating, feedback=""):
		"""Record helpfulness rating"""
		rating = flt(rating)
		if rating < 1 or rating > 5:
			frappe.throw(_("Rating must be between 1 and 5"))

		# Update average rating
		current_rating = flt(self.helpfulness_rating)
		current_views = cint(self.view_count)

		if current_views > 0:
			new_rating = ((current_rating * current_views) + rating) / (current_views + 1)
		else:
			new_rating = rating

		self.helpfulness_rating = new_rating
		self.save(ignore_permissions=True)

		# Log feedback
		self.log_help_feedback(rating, feedback)

		return {"status": "success", "new_rating": new_rating}

	def log_help_usage(self, action_type):
		"""Log help content usage for analytics"""
		try:
			log_entry = frappe.new_doc("Help Usage Log")
			log_entry.help_content = self.name
			log_entry.user = frappe.session.user
			log_entry.action_type = action_type
			log_entry.timestamp = now_datetime()
			log_entry.route = frappe.request.path if frappe.request else ""
			log_entry.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Failed to log help usage: {str(e)}")

	def log_help_feedback(self, rating, feedback):
		"""Log help content feedback"""
		try:
			feedback_entry = frappe.new_doc("Help Content Feedback")
			feedback_entry.help_content = self.name
			feedback_entry.user = frappe.session.user
			feedback_entry.rating = rating
			feedback_entry.feedback = feedback
			feedback_entry.timestamp = now_datetime()
			feedback_entry.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Failed to log help feedback: {str(e)}")


# API Methods for contextual help system
@frappe.whitelist()
def get_contextual_help(route, doctype=None, field=None, user_roles=None):
	"""Get contextual help for current context"""
	if user_roles is None:
		user_roles = frappe.get_roles(frappe.session.user)

	# Build filters
	filters = {"is_active": 1}

	help_content = []

	# Get route-based help
	route_help = get_help_by_route(route, user_roles)
	help_content.extend(route_help)

	# Get doctype-based help
	if doctype:
		doctype_help = get_help_by_doctype(doctype, field, user_roles)
		help_content.extend(doctype_help)

	# Remove duplicates and sort by priority
	unique_help = {}
	for item in help_content:
		if item["name"] not in unique_help:
			unique_help[item["name"]] = item

	sorted_help = sorted(
		unique_help.values(),
		key=lambda x: {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}.get(x["priority"], 1),
		reverse=True
	)

	return sorted_help[:10]  # Limit to top 10 results


def get_help_by_route(route, user_roles):
	"""Get help content by route"""
	# Direct route match
	route_matches = frappe.db.sql("""
		SELECT DISTINCT hc.name, hc.title, hc.title_ar, hc.content_key, hc.help_type,
			   hc.priority, hc.content, hc.content_ar, hc.tooltip_text, hc.tooltip_text_ar
		FROM `tabHelp Content` hc
		JOIN `tabHelp Content Route` hcr ON hc.name = hcr.parent
		WHERE hc.is_active = 1
		AND (hcr.route = %s OR (hcr.is_regex = 1 AND %s REGEXP hcr.route_pattern))
	""", [route, route], as_dict=True)

	# Filter by user roles
	filtered_results = []
	for item in route_matches:
		if has_role_access(item["name"], user_roles):
			filtered_results.append(item)

	return filtered_results


def get_help_by_doctype(doctype, field, user_roles):
	"""Get help content by doctype and field"""
	filters = {
		"is_active": 1,
		"target_doctype": doctype
	}

	if field:
		filters["target_field"] = field

	help_items = frappe.get_all(
		"Help Content",
		filters=filters,
		fields=[
			"name", "title", "title_ar", "content_key", "help_type",
			"priority", "content", "content_ar", "tooltip_text", "tooltip_text_ar"
		]
	)

	# Filter by user roles
	filtered_results = []
	for item in help_items:
		if has_role_access(item["name"], user_roles):
			filtered_results.append(item)

	return filtered_results


def has_role_access(help_content_name, user_roles):
	"""Check if user has role access to help content"""
	help_roles = frappe.get_all(
		"Help Content Role",
		filters={"parent": help_content_name},
		fields=["role"]
	)

	# If no roles specified, allow access to all
	if not help_roles:
		return True

	help_role_names = [r.role for r in help_roles]
	return any(role in user_roles for role in help_role_names)


@frappe.whitelist()
def search_help_content(query, help_type=None, doctype=None):
	"""Search help content"""
	conditions = ["hc.is_active = 1"]
	values = []

	if help_type:
		conditions.append("hc.help_type = %s")
		values.append(help_type)

	if doctype:
		conditions.append("hc.target_doctype = %s")
		values.append(doctype)

	# Search in title and content
	search_condition = """
		(hc.title LIKE %s OR hc.title_ar LIKE %s
		 OR hc.content LIKE %s OR hc.content_ar LIKE %s
		 OR hc.tooltip_text LIKE %s OR hc.tooltip_text_ar LIKE %s)
	"""
	conditions.append(search_condition)
	search_term = f"%{query}%"
	values.extend([search_term] * 6)

	sql = f"""
		SELECT hc.name, hc.title, hc.title_ar, hc.content_key, hc.help_type,
			   hc.priority, hc.content, hc.content_ar, hc.tooltip_text, hc.tooltip_text_ar,
			   hc.view_count, hc.helpfulness_rating
		FROM `tabHelp Content` hc
		WHERE {' AND '.join(conditions)}
		ORDER BY hc.priority DESC, hc.helpfulness_rating DESC, hc.view_count DESC
		LIMIT 20
	"""

	results = frappe.db.sql(sql, values, as_dict=True)

	# Filter by user roles
	user_roles = frappe.get_roles(frappe.session.user)
	filtered_results = []
	for item in results:
		if has_role_access(item["name"], user_roles):
			filtered_results.append(item)

	return filtered_results


@frappe.whitelist()
def get_help_content_details(content_key):
	"""Get detailed help content by content key"""
	help_content = frappe.get_doc("Help Content", {"content_key": content_key})

	# Record view
	help_content.record_view()

	# Get related content
	related_docs = []
	for doc_ref in help_content.related_documentation:
		doc_details = frappe.get_doc("Knowledge Base Article", doc_ref.knowledge_base_article)
		related_docs.append({
			"name": doc_details.name,
			"title": doc_details.title,
			"title_ar": doc_details.title_ar,
			"is_primary": doc_ref.is_primary,
			"url": f"/knowledge-base/article/{doc_details.name}"
		})

	related_training = []
	for training_ref in help_content.related_training_modules:
		module_details = frappe.get_doc("Training Module", training_ref.training_module)
		related_training.append({
			"name": module_details.name,
			"title": module_details.title,
			"title_ar": module_details.title_ar,
			"is_prerequisite": training_ref.is_prerequisite,
			"estimated_duration": module_details.estimated_duration_hours
		})

	return {
		"content": help_content.as_dict(),
		"related_documentation": related_docs,
		"related_training": related_training
	}


@frappe.whitelist()
def get_help_widget_data():
	"""Get data for help widget"""
	user_roles = frappe.get_roles(frappe.session.user)

	# Get popular help content
	popular_help = frappe.db.sql("""
		SELECT name, title, title_ar, content_key, help_type, view_count
		FROM `tabHelp Content`
		WHERE is_active = 1
		ORDER BY view_count DESC, helpfulness_rating DESC
		LIMIT 5
	""", as_dict=True)

	# Get recent help content
	recent_help = frappe.db.sql("""
		SELECT name, title, title_ar, content_key, help_type, created_on
		FROM `tabHelp Content`
		WHERE is_active = 1
		ORDER BY created_on DESC
		LIMIT 5
	""", as_dict=True)

	# Filter by user roles
	popular_filtered = [item for item in popular_help if has_role_access(item["name"], user_roles)]
	recent_filtered = [item for item in recent_help if has_role_access(item["name"], user_roles)]

	return {
		"popular": popular_filtered,
		"recent": recent_filtered
	}
