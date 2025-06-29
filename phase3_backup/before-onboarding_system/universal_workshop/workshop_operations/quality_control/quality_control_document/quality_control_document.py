# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member,access-member-before-definition
# Frappe framework dynamically adds DocType fields to Document class

import os
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_files_path


class QualityControlDocument(Document):
    def validate(self):
        """Validate quality control document data"""
        self.validate_arabic_title()
        self.validate_document_file()
        self.set_upload_details()

    def validate_arabic_title(self):
        """Ensure Arabic title is provided"""
        if not self.document_title_ar:
            # Auto-translate common document types
            translations = {
                "Inspection Report": "تقرير الفحص",
                "Certificate": "شهادة",
                "Warranty Document": "مستند الضمان",
                "Customer Authorization": "تصريح العميل",
                "Technical Specification": "المواصفات الفنية",
                "Compliance Document": "مستند الامتثال",
                "Other": "أخرى",
            }

            if self.document_title in translations:
                self.document_title_ar = translations[self.document_title]
            else:
                frappe.throw(_("Arabic document title is required"))

    def validate_document_file(self):
        """Validate document file attachment"""
        if not self.document_file:
            frappe.throw(_("Document file is required"))

        # Check file extension
        if self.document_file:
            allowed_extensions = [".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".txt"]
            file_ext = self.document_file.lower().split(".")[-1]
            if f".{file_ext}" not in allowed_extensions:
                frappe.throw(_("Only PDF, DOC, DOCX, JPG, PNG, and TXT files are allowed"))

    def set_upload_details(self):
        """Set default upload details"""
        if not self.uploaded_by:
            self.uploaded_by = frappe.session.user

        if not self.upload_date:
            self.upload_date = now_datetime()

    def before_save(self):
        """Set file size and other metadata"""
        if self.document_file and not self.file_size:
            self.file_size = self.get_file_size()

    def get_file_size(self):
        """Get file size in human readable format"""
        try:
            if self.document_file:
                file_path = frappe.get_doc("File", {"file_url": self.document_file})
                if file_path and file_path.file_size:
                    size_bytes = file_path.file_size
                    # Convert to human readable format
                    for unit in ["B", "KB", "MB", "GB"]:
                        if size_bytes < 1024.0:
                            return f"{size_bytes:.1f} {unit}"
                        size_bytes /= 1024.0
                    return f"{size_bytes:.1f} TB"
        except Exception:
            pass
        return "Unknown"

    @staticmethod
    def get_documents_by_type(checkpoint_id, document_type=None):
        """Get documents for a checkpoint, optionally filtered by type"""
        filters = {"parent": checkpoint_id}
        if document_type:
            filters["document_type"] = document_type

        return frappe.get_all(
            "Quality Control Document",
            filters=filters,
            fields=[
                "document_title",
                "document_title_ar",
                "document_type",
                "document_file",
                "upload_date",
                "uploaded_by",
                "file_size",
            ],
            order_by="upload_date desc",
        )

    @staticmethod
    def add_document_from_upload(checkpoint_id, document_data):
        """Add document from file upload with metadata"""
        document = frappe.new_doc("Quality Control Document")
        document.parent = checkpoint_id
        document.parenttype = "Quality Control Checkpoint"
        document.parentfield = "supporting_documents"

        document.document_title = document_data.get("title", "Uploaded Document")
        document.document_type = document_data.get("type", "Other")
        document.document_file = document_data.get("file_url")
        document.document_description = document_data.get("description", "")
        document.is_mandatory = document_data.get("is_mandatory", 0)

        document.insert()
        return document.name

    @staticmethod
    def get_mandatory_documents_status(checkpoint_id):
        """Check if all mandatory documents are uploaded"""
        mandatory_docs = frappe.get_all(
            "Quality Control Document",
            filters={"parent": checkpoint_id, "is_mandatory": 1},
            fields=["document_type", "document_file"],
        )

        missing_docs = [doc.document_type for doc in mandatory_docs if not doc.document_file]

        return {
            "all_uploaded": len(missing_docs) == 0,
            "missing_documents": missing_docs,
            "total_mandatory": len(mandatory_docs),
            "uploaded_count": len(mandatory_docs) - len(missing_docs),
        }
