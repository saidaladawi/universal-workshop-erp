# -*- coding: utf-8 -*-
"""
Notification Template DocType Controller
Handles template management, rendering, validation, and preview functionality
"""

import json
import re
from typing import Dict, Any, Optional
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, cstr
import jinja2
from jinja2 import Environment, BaseLoader, TemplateError


class NotificationTemplate(Document):
    """
    Notification Template DocType for managing dynamic communication templates
    with support for SMS, WhatsApp, Email channels and Arabic/English languages
    """

    def validate(self):
        """Validate template configuration"""
        self.validate_template_syntax()
        self.validate_channel_specific_rules()
        self.calculate_estimated_segments()
        self.validate_whatsapp_config()
        self.set_created_by()

    def before_save(self):
        """Before save operations"""
        self.generate_preview()
        self.validate_character_limits()

    def on_update(self):
        """After save operations"""
        self.increment_version_if_content_changed()

    def validate_template_syntax(self):
        """Validate Jinja2 template syntax"""
        try:
            env = jinja2.Environment(loader=jinja2.BaseLoader())
            env.from_string(self.template_body)

            # Clear any previous syntax errors
            if hasattr(self, "_template_syntax_error"):
                delattr(self, "_template_syntax_error")

        except TemplateError as e:
            self._template_syntax_error = str(e)
            frappe.throw(_("Template syntax error: {0}").format(str(e)))
        except Exception as e:
            frappe.throw(_("Template validation error: {0}").format(str(e)))

    def validate_channel_specific_rules(self):
        """Validate channel-specific rules and constraints"""
        if self.channel_type == "SMS":
            # SMS specific validations
            if not self.max_length:
                self.max_length = 160  # Default SMS length

            if len(self.template_body) > 1000:  # Reasonable upper limit
                frappe.throw(_("SMS template body is too long. Consider using multiple templates."))

        elif self.channel_type == "WhatsApp":
            # WhatsApp specific validations
            if not self.max_length:
                self.max_length = 4096  # WhatsApp max length

            if len(self.template_body) > self.max_length:
                frappe.throw(
                    _("WhatsApp template exceeds maximum length of {0} characters").format(
                        self.max_length
                    )
                )

        elif self.channel_type == "Email":
            # Email specific validations
            if not self.template_subject:
                frappe.throw(_("Email templates must have a subject"))

    def calculate_estimated_segments(self):
        """Calculate estimated SMS segments for SMS templates"""
        if self.channel_type == "SMS":
            # Basic estimation - actual segments depend on rendered content
            text_length = len(self.template_body)

            # Check if contains Arabic characters (rough detection)
            contains_arabic = bool(re.search(r"[\u0600-\u06FF]", self.template_body))

            if contains_arabic:
                # Arabic SMS uses UCS-2 encoding (70 chars per segment)
                self.estimated_segments = max(
                    1, (text_length // 70) + (1 if text_length % 70 else 0)
                )
            else:
                # Standard GSM encoding (160 chars per segment)
                self.estimated_segments = max(
                    1, (text_length // 160) + (1 if text_length % 160 else 0)
                )

    def validate_whatsapp_config(self):
        """Validate WhatsApp specific configuration"""
        if self.channel_type == "WhatsApp":
            if self.approval_status == "Approved" and not self.whatsapp_template_id:
                frappe.msgprint(_("Warning: Approved WhatsApp templates should have a Template ID"))

    def validate_character_limits(self):
        """Validate rendered template against character limits"""
        if self.preview_context_json:
            try:
                rendered = self.render_template_with_context(json.loads(self.preview_context_json))

                if self.channel_type == "SMS":
                    # Check SMS length constraints
                    if len(rendered) > 1600:  # 10 SMS segments
                        frappe.msgprint(_("Warning: Rendered template may exceed 10 SMS segments"))

                elif self.channel_type == "WhatsApp" and len(rendered) > self.max_length:
                    frappe.throw(_("Rendered template exceeds WhatsApp character limit"))

            except Exception as e:
                # Don't fail save, just warn
                frappe.msgprint(_("Could not validate character limits: {0}").format(str(e)))

    def set_created_by(self):
        """Set created_by field on new templates"""
        if not self.created_by and self.is_new():
            self.created_by = frappe.session.user

    def increment_version_if_content_changed(self):
        """Increment version if template content has changed"""
        if not self.is_new():
            # Check if template body or subject changed
            old_doc = self.get_doc_before_save()
            if old_doc and (
                old_doc.template_body != self.template_body
                or old_doc.template_subject != self.template_subject
            ):
                self.version = (self.version or 1) + 1

    def generate_preview(self):
        """Generate template preview with sample data"""
        try:
            if self.preview_context_json:
                context = json.loads(self.preview_context_json)
            else:
                context = self.get_default_preview_context()

            self.rendered_preview = self.render_template_with_context(context)

        except Exception as e:
            self.rendered_preview = f"Preview Error: {str(e)}"

    def get_default_preview_context(self) -> Dict[str, Any]:
        """Get default preview context based on template category"""
        base_context = {
            "customer_name": "أحمد محمد" if self.language == "Arabic" else "Ahmed Mohammed",
            "customer_name_ar": "أحمد محمد",
            "workshop_name": (
                "ورشة الخليج العالمية" if self.language == "Arabic" else "Gulf Universal Workshop"
            ),
            "workshop_phone": "+968 24 123456",
            "current_date": frappe.utils.format_date(frappe.utils.today(), "dd/MM/yyyy"),
            "current_time": frappe.utils.format_time(frappe.utils.nowtime()),
        }

        # Add category-specific context
        category_contexts = {
            "Appointment Confirmation": {
                "appointment_date": "2025-01-15",
                "appointment_time": "10:00 AM",
                "service_type": (
                    "صيانة دورية" if self.language == "Arabic" else "Regular Maintenance"
                ),
                "vehicle_number": "AB-1234",
            },
            "Service Completion": {
                "vehicle_number": "AB-1234",
                "service_type": "تغيير الزيت" if self.language == "Arabic" else "Oil Change",
                "total_amount": "25.500",
                "invoice_number": "INV-2025-001",
            },
            "Invoice Notification": {
                "invoice_number": "INV-2025-001",
                "total_amount": "25.500",
                "due_date": "2025-01-30",
                "payment_link": "https://workshop.om/pay/INV-2025-001",
            },
            "Payment Reminder": {
                "invoice_number": "INV-2025-001",
                "total_amount": "25.500",
                "days_overdue": "5",
                "due_date": "2025-01-30",
            },
        }

        if self.template_category in category_contexts:
            base_context.update(category_contexts[self.template_category])

        return {"doc": base_context}

    def render_template_with_context(self, context: Dict[str, Any]) -> str:
        """
        Render template with provided context

        Args:
            context: Template context dictionary

        Returns:
            str: Rendered template content
        """
        try:
            # Create Jinja2 environment with RTL support
            env = jinja2.Environment(
                loader=jinja2.BaseLoader(),
                autoescape=False,  # Allow HTML for WhatsApp formatting
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Add custom filters for Arabic/RTL support
            env.filters["rtl_mark"] = self._add_rtl_mark
            env.filters["format_currency"] = self._format_currency_omr
            env.filters["format_date_ar"] = self._format_date_arabic

            # Render template
            template = env.from_string(self.template_body)
            rendered = template.render(**context)

            # Post-process for channel-specific formatting
            if self.channel_type == "WhatsApp":
                rendered = self._format_whatsapp_markup(rendered)
            elif self.channel_type == "SMS" and self.language == "Arabic":
                rendered = self._ensure_rtl_formatting(rendered)

            return rendered.strip()

        except Exception as e:
            frappe.log_error(f"Template rendering error: {str(e)}", "Template Rendering")
            raise

    def _add_rtl_mark(self, text):
        """Add RTL mark to Arabic text"""
        if text and self.language == "Arabic":
            return f"\u200f{text}"  # RTL mark
        return text

    def _format_currency_omr(self, amount):
        """Format currency in OMR"""
        try:
            if isinstance(amount, (int, float)):
                return f"{amount:.3f} ر.ع." if self.language == "Arabic" else f"{amount:.3f} OMR"
            return str(amount)
        except:
            return str(amount)

    def _format_date_arabic(self, date_str):
        """Format date in Arabic style"""
        try:
            if self.language == "Arabic":
                # Convert English numerals to Arabic numerals
                arabic_numerals = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
                return date_str.translate(arabic_numerals)
            return date_str
        except:
            return date_str

    def _format_whatsapp_markup(self, text):
        """Format WhatsApp markup (bold, italic, etc.)"""
        # Convert simple markdown-style formatting to WhatsApp formatting
        # *bold* -> *bold*
        # _italic_ -> _italic_
        # This preserves WhatsApp's native formatting
        return text

    def _ensure_rtl_formatting(self, text):
        """Ensure proper RTL formatting for Arabic SMS"""
        if self.language == "Arabic":
            # Add RTL mark at the beginning if not present
            if not text.startswith("\u200f"):
                text = f"\u200f{text}"
        return text

    @frappe.whitelist()
    def preview_template(self, context_json: str = None) -> Dict[str, Any]:
        """
        Preview template with provided or default context

        Args:
            context_json: JSON string of context data

        Returns:
            Dict: Preview result with rendered content and metadata
        """
        try:
            if context_json:
                context = json.loads(context_json)
            else:
                context = self.get_default_preview_context()

            rendered = self.render_template_with_context(context)

            # Calculate statistics
            char_count = len(rendered)

            if self.channel_type == "SMS":
                # Calculate SMS segments
                contains_arabic = bool(re.search(r"[\u0600-\u06FF]", rendered))
                segment_size = 70 if contains_arabic else 160
                segments = max(
                    1, (char_count // segment_size) + (1 if char_count % segment_size else 0)
                )
            else:
                segments = 1

            return {
                "success": True,
                "rendered_content": rendered,
                "character_count": char_count,
                "segments": segments,
                "channel_type": self.channel_type,
                "language": self.language,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @frappe.whitelist()
    def approve_template(self):
        """Approve template for use"""
        if self.approval_status in ["Approved"]:
            frappe.throw(_("Template is already approved"))

        self.approval_status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_on = now_datetime()
        self.save(ignore_permissions=True)

        frappe.msgprint(_("Template approved successfully"))

    @frappe.whitelist()
    def reject_template(self, reason: str = None):
        """Reject template with optional reason"""
        self.approval_status = "Rejected"
        if reason:
            self.add_comment("Comment", f"Rejection reason: {reason}")
        self.save(ignore_permissions=True)

        frappe.msgprint(_("Template rejected"))

    def increment_usage_count(self):
        """Increment usage statistics when template is used"""
        frappe.db.set_value(
            "Notification Template",
            self.name,
            {"usage_count": (self.usage_count or 0) + 1, "last_used": now_datetime()},
        )
        frappe.db.commit()

    def increment_error_count(self):
        """Increment error count when template fails"""
        frappe.db.set_value(
            "Notification Template", self.name, "error_count", (self.error_count or 0) + 1
        )
        frappe.db.commit()


# WhiteListed API methods
@frappe.whitelist()
def get_template_by_category(
    category: str, channel_type: str, language: str = "English"
) -> Dict[str, Any]:
    """
    Get active template by category, channel, and language

    Args:
        category: Template category
        channel_type: Communication channel (SMS, WhatsApp, Email)
        language: Template language (English, Arabic)

    Returns:
        Dict: Template data or None if not found
    """
    try:
        template = frappe.get_value(
            "Notification Template",
            {
                "template_category": category,
                "channel_type": channel_type,
                "language": language,
                "is_active": 1,
                "approval_status": "Approved",
            },
            ["name", "template_body", "template_subject", "whatsapp_template_id"],
            as_dict=True,
        )

        return template

    except Exception as e:
        frappe.log_error(f"Error getting template: {str(e)}", "Template API")
        return None


@frappe.whitelist()
def render_template(template_name: str, context_data: str) -> Dict[str, Any]:
    """
    Render template with provided context

    Args:
        template_name: Name of the template
        context_data: JSON string of context data

    Returns:
        Dict: Rendered template result
    """
    try:
        template_doc = frappe.get_doc("Notification Template", template_name)
        context = json.loads(context_data)

        rendered = template_doc.render_template_with_context(context)

        # Update usage statistics
        template_doc.increment_usage_count()

        return {
            "success": True,
            "rendered_content": rendered,
            "template_subject": template_doc.template_subject,
            "whatsapp_template_id": template_doc.whatsapp_template_id,
        }

    except Exception as e:
        frappe.log_error(f"Template rendering error: {str(e)}", "Template Rendering API")

        # Increment error count
        try:
            template_doc = frappe.get_doc("Notification Template", template_name)
            template_doc.increment_error_count()
        except:
            pass

        return {"success": False, "error": str(e)}
