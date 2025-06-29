# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import re
from datetime import datetime
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class TrainingModule(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate training module before saving"""
        self.validate_basic_info()
        self.validate_content_configuration()
        self.validate_assessment_settings()
        self.validate_arabic_content()
        self.set_metadata()

    def validate_basic_info(self):
        """Validate basic module information"""
        if not self.title:
            frappe.throw(_("Module title (English) is required"))

        if not self.title_ar:
            frappe.throw(_("Module title (Arabic) is required"))

        if not self.module_code:
            self.module_code = self.generate_module_code()

        # Validate module code format
        if not re.match(r"^TM-\d{5}$", self.module_code):
            frappe.throw(_("Module code must follow format: TM-00001"))

        # Validate estimated duration
        if self.estimated_duration <= 0:
            frappe.throw(_("Estimated duration must be greater than 0 minutes"))

    def validate_content_configuration(self):
        """Validate content setup based on content type"""
        if self.content_type == "H5P Interactive" and not self.h5p_content_id:
            frappe.throw(_("H5P Content ID is required for H5P Interactive modules"))

        if self.content_type == "Video Tutorial" and not self.video_url:
            frappe.throw(_("Video URL is required for Video Tutorial modules"))

        if self.content_type in ["Document/PDF", "H5P Interactive"] and not self.content_file:
            frappe.throw(_("Content file is required for this content type"))

        # Validate video URL format
        if self.video_url and not self.is_valid_video_url(self.video_url):
            frappe.throw(_("Invalid video URL format. Use YouTube, Vimeo, or direct video links"))

    def validate_assessment_settings(self):
        """Validate quiz and assessment configuration"""
        if self.has_quiz:
            if not self.passing_score or self.passing_score <= 0:
                frappe.throw(_("Passing score is required for modules with quiz"))

            if self.passing_score > 100:
                frappe.throw(_("Passing score cannot exceed 100%"))

            if not self.max_attempts or self.max_attempts <= 0:
                frappe.throw(_("Maximum attempts must be greater than 0"))

            if self.quiz_questions:
                try:
                    quiz_data = json.loads(self.quiz_questions)
                    if not isinstance(quiz_data, list) or len(quiz_data) == 0:
                        frappe.throw(_("Quiz questions must be a non-empty JSON array"))
                except json.JSONDecodeError:
                    frappe.throw(_("Quiz questions must be valid JSON format"))

    def validate_arabic_content(self):
        """Validate Arabic content fields"""
        if self.title_ar and not self.contains_arabic_text(self.title_ar):
            frappe.msgprint(
                _("Warning: Arabic title appears to contain no Arabic characters"), alert=True
            )

        if self.description_ar and not self.contains_arabic_text(self.description_ar):
            frappe.msgprint(
                _("Warning: Arabic description appears to contain no Arabic characters"), alert=True
            )

    def set_metadata(self):
        """Set creation and modification metadata"""
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_date = datetime.now()

        self.last_modified_by = frappe.session.user
        self.last_modified_date = datetime.now()

        if not self.version:
            self.version = "1.0"

    def before_save(self):
        """Actions before saving the document"""
        if self.is_published and not self.thumbnail_image:
            frappe.msgprint(
                _("Consider adding a thumbnail image for published modules"), alert=True
            )

    def after_insert(self):
        """Actions after inserting new training module"""
        # Create default learning path entry if needed
        self.create_default_learning_path()

        # Log module creation
        frappe.logger().info(f"Training Module created: {self.module_code} - {self.title}")

    def generate_module_code(self):
        """Generate unique module code"""
        # Get the next sequence number
        last_module = frappe.db.sql(
            """
            SELECT module_code FROM `tabTraining Module`
            WHERE module_code LIKE 'TM-%'
            ORDER BY module_code DESC LIMIT 1
        """
        )

        if last_module:
            last_num = int(last_module[0][0].split("-")[1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"TM-{new_num:05d}"

    def is_valid_video_url(self, url):
        """Validate video URL format"""
        video_patterns = [
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/",
            r"(https?://)?(www\.)?vimeo\.com/",
            r"(https?://)?.*\.(mp4|avi|mov|wmv|flv|webm)$",
        ]

        for pattern in video_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False

    def contains_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        if not text:
            return False
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return arabic_pattern.search(text) is not None

    def create_default_learning_path(self):
        """Create default learning path entry for this module"""
        # This will be implemented when Learning Path DocType is created
        pass

    @frappe.whitelist()
    def get_h5p_content(self):
        """Retrieve H5P content for rendering"""
        if not self.h5p_content_id:
            return None

        # This will interface with H5P library
        return {
            "content_id": self.h5p_content_id,
            "content_type": self.content_type,
            "title": self.title,
            "title_ar": self.title_ar,
        }

    @frappe.whitelist()
    def publish_module(self):
        """Publish the training module"""
        if not self.content_file and not self.video_url and not self.h5p_content_id:
            frappe.throw(_("Cannot publish module without content"))

        self.is_published = 1
        self.save()

        frappe.msgprint(_("Training module published successfully"))
        return True

    @frappe.whitelist()
    def unpublish_module(self):
        """Unpublish the training module"""
        self.is_published = 0
        self.save()

        frappe.msgprint(_("Training module unpublished"))
        return True


@frappe.whitelist()
def get_modules_by_category(category=None, role=None):
    """Get training modules filtered by category and role"""
    filters = {"is_published": 1}

    if category:
        filters["category"] = category

    modules = frappe.get_list(
        "Training Module",
        filters=filters,
        fields=[
            "name",
            "title",
            "title_ar",
            "module_code",
            "category",
            "difficulty_level",
            "estimated_duration",
            "thumbnail_image",
            "requires_certification",
            "description",
            "description_ar",
        ],
        order_by="category, difficulty_level, title",
    )

    # Filter by role if specified
    if role and modules:
        role_filtered_modules = []
        for module in modules:
            module_doc = frappe.get_doc("Training Module", module.name)
            target_roles = (
                [d.role for d in module_doc.target_roles] if module_doc.target_roles else []
            )

            if not target_roles or role in target_roles:
                role_filtered_modules.append(module)

        return role_filtered_modules

    return modules


@frappe.whitelist()
def get_module_content(module_name):
    """Get module content for training delivery"""
    module = frappe.get_doc("Training Module", module_name)

    if not module.is_published:
        frappe.throw(_("Module is not published"))

    # Check user permissions
    if not frappe.has_permission("Training Module", "read", module_name):
        frappe.throw(_("Insufficient permissions to access this module"))

    content_data = {
        "module": module,
        "content_type": module.content_type,
        "content_url": None,
        "quiz_data": None,
    }

    # Prepare content based on type
    if module.content_type == "H5P Interactive" and module.h5p_content_id:
        content_data["h5p_content"] = module.get_h5p_content()
    elif module.content_type == "Video Tutorial" and module.video_url:
        content_data["content_url"] = module.video_url
    elif module.content_file:
        content_data["content_url"] = module.content_file

    # Include quiz data if available
    if module.has_quiz and module.quiz_questions:
        try:
            content_data["quiz_data"] = json.loads(module.quiz_questions)
        except json.JSONDecodeError:
            frappe.logger().error(f"Invalid quiz JSON in module {module_name}")

    return content_data
