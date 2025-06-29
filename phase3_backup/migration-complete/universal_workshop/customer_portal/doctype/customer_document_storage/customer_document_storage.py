# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import hashlib
import mimetypes
import os
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, get_files_path, now, today
from frappe.utils.file_manager import get_file_path


class CustomerDocumentStorage(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate document before saving"""
        self.validate_required_fields()
        self.validate_arabic_content()
        self.validate_access_permissions()
        self.set_file_metadata()
        self.perform_virus_scan()

    def before_save(self):
        """Set default values before saving"""
        self.set_default_values()
        self.log_system_information()

    def after_insert(self):
        """Post-creation actions"""
        self.generate_file_hash()
        self.create_thumbnail()
        self.log_access("Document Created")

    def validate_required_fields(self):
        """Validate required fields for document"""
        if not self.document_title:
            frappe.throw(_("Document title is required"))

        if not self.customer:
            frappe.throw(_("Customer is required"))

        if not self.file_attachment:
            frappe.throw(_("File attachment is required"))

        if not self.document_type:
            frappe.throw(_("Document type is required"))

    def validate_arabic_content(self):
        """Validate Arabic content fields"""
        if self.document_title and not self.document_title_ar:
            # Auto-suggest Arabic translation if needed
            self.suggest_arabic_translation()

        # Check if document contains Arabic text
        if self.document_title_ar or self.description_ar or self.keywords_ar:
            self.arabic_content = 1
            self.rtl_support = 1

    def validate_access_permissions(self):
        """Validate access permission settings"""
        if self.access_permissions == "Restricted" and not self.approved_by:
            self.approval_required = 1

        if self.expiry_date and self.expiry_date < today():
            frappe.throw(_("Access expiry date cannot be in the past"))

    def set_file_metadata(self):
        """Set file metadata from attachment"""
        if self.file_attachment:
            try:
                file_path = get_file_path(self.file_attachment)
                if file_path and os.path.exists(file_path):
                    # Get file information
                    file_stats = os.stat(file_path)
                    self.file_size = self.format_file_size(file_stats.st_size)
                    self.file_name = os.path.basename(file_path)
                    self.original_filename = self.file_name

                    # Get MIME type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    self.mime_type = mime_type or "application/octet-stream"

                    # Get file extension
                    self.file_type = Path(file_path).suffix.lower()

                    # Set file URL
                    self.file_url = self.file_attachment

            except Exception as e:
                frappe.log_error(f"Error setting file metadata: {e}")

    def perform_virus_scan(self):
        """Perform basic virus scanning (placeholder for actual implementation)"""
        # In a real implementation, integrate with antivirus software
        # For now, set status based on file type validation
        if self.file_type in [".exe", ".bat", ".cmd", ".scr"]:
            self.virus_scan_status = "Infected"
            frappe.throw(_("Potentially dangerous file type detected"))
        else:
            self.virus_scan_status = "Clean"
            self.virus_scan_date = now()

    def set_default_values(self):
        """Set default values for document"""
        if not self.created_date:
            self.created_date = now()

        if not self.created_by:
            self.created_by = frappe.session.user

        if not self.status:
            self.status = "Draft"

        if not self.access_permissions:
            self.access_permissions = "Owner Only"

        if not self.upload_source:
            self.upload_source = "Customer Portal"

        if not self.version_number:
            self.version_number = 1

        # Set privacy based on document type
        if self.document_type in ["Contract", "Legal", "Financial"]:
            self.is_private = 1

    def log_system_information(self):
        """Log system information"""
        self.modified_by = frappe.session.user
        self.modified_date = now()

        # Get IP address from request
        if hasattr(frappe.local, "request") and frappe.local.request:
            self.ip_address = frappe.local.request.environ.get("REMOTE_ADDR", "Unknown")

    def generate_file_hash(self):
        """Generate SHA256 hash of file for integrity verification"""
        if self.file_attachment:
            try:
                file_path = get_file_path(self.file_attachment)
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        self.file_hash = file_hash
                        self.save()
            except Exception as e:
                frappe.log_error(f"Error generating file hash: {e}")

    def create_thumbnail(self):
        """Create thumbnail for supported file types"""
        if self.file_type in [".jpg", ".jpeg", ".png", ".gif", ".pdf"]:
            # Placeholder for thumbnail generation
            # In real implementation, use PIL for images, pdf2image for PDFs
            self.document_preview = 1
            self.preview_status = "Ready"
            self.thumbnail_url = (
                f"/api/method/universal_workshop.api.get_document_thumbnail?doc_id={self.name}"
            )
        else:
            self.preview_status = "Not Supported"

    def log_access(self, action):
        """Log document access for audit trail"""
        access_entry = {
            "timestamp": now(),
            "user": frappe.session.user,
            "action": action,
            "ip_address": self.ip_address or "Unknown",
        }

        current_log = self.access_log or "[]"
        try:
            import json

            log_entries = json.loads(current_log)
            log_entries.append(access_entry)
            # Keep only last 50 entries
            if len(log_entries) > 50:
                log_entries = log_entries[-50:]
            self.access_log = json.dumps(log_entries)
        except:
            self.access_log = json.dumps([access_entry])

    def suggest_arabic_translation(self):
        """Suggest Arabic translation for document title"""
        # Placeholder for translation service integration
        # In real implementation, integrate with translation API
        if self.document_title and not self.document_title_ar:
            # Common translations for workshop documents
            translations = {
                "Invoice": "فاتورة",
                "Service Report": "تقرير الخدمة",
                "Warranty Document": "وثيقة الضمان",
                "Receipt": "إيصال",
                "Quotation": "عرض أسعار",
                "Contract": "عقد",
                "Photo": "صورة",
                "Video": "فيديو",
            }

            self.document_title_ar = translations.get(
                self.document_title, f"ترجمة: {self.document_title}"
            )

    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def can_read(self, user=None):
        """Check if user can read document"""
        if not user:
            user = frappe.session.user

        # System managers can read all documents
        if "System Manager" in frappe.get_roles(user):
            return True

        # Workshop managers can read customer documents
        if "Workshop Manager" in frappe.get_roles(user):
            return True

        # Customer can read their own documents
        if self.customer:
            customer_user = frappe.db.get_value("Customer", self.customer, "email_id")
            if customer_user == user:
                return True

        # Check expiry date
        if self.expiry_date and self.expiry_date < today():
            return False

        return False

    def can_download(self, user=None):
        """Check if user can download document"""
        if not self.can_read(user):
            return False

        # Check approval status for restricted documents
        if self.access_permissions == "Restricted" and self.status != "Approved":
            return False

        return True

    def record_download(self, user=None):
        """Record document download"""
        if not user:
            user = frappe.session.user

        self.download_count = cint(self.download_count) + 1
        self.last_accessed = now()
        self.last_accessed_by = user
        self.log_access("Document Downloaded")
        self.save(ignore_permissions=True)

    def approve_document(self, approval_reason=""):
        """Approve document for access"""
        if not frappe.has_permission("Customer Document Storage", "write"):
            frappe.throw(_("Not permitted to approve documents"))

        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approval_date = now()
        self.log_access(f"Document Approved: {approval_reason}")
        self.save()

        # Send approval notification
        self.send_approval_notification()

    def reject_document(self, rejection_reason="", rejection_reason_ar=""):
        """Reject document access"""
        if not frappe.has_permission("Customer Document Storage", "write"):
            frappe.throw(_("Not permitted to reject documents"))

        self.status = "Rejected"
        self.rejection_reason = rejection_reason
        self.rejection_reason_ar = rejection_reason_ar
        self.log_access(f"Document Rejected: {rejection_reason}")
        self.save()

        # Send rejection notification
        self.send_rejection_notification()

    def send_approval_notification(self):
        """Send notification when document is approved"""
        if self.customer:
            customer_email = frappe.db.get_value("Customer", self.customer, "email_id")
            if customer_email:
                subject = _("Document Approved: {0}").format(self.document_title)
                message = _(
                    """
                Dear Customer,
                
                Your document "{0}" has been approved and is now available for download.
                
                Document Type: {1}
                Approved By: {2}
                Approval Date: {3}
                
                You can access your document from the customer portal.
                
                Best regards,
                Universal Workshop Team
                """
                ).format(
                    self.document_title, self.document_type, self.approved_by, self.approval_date
                )

                frappe.sendmail(recipients=[customer_email], subject=subject, message=message)

    def send_rejection_notification(self):
        """Send notification when document is rejected"""
        if self.customer:
            customer_email = frappe.db.get_value("Customer", self.customer, "email_id")
            if customer_email:
                subject = _("Document Rejected: {0}").format(self.document_title)
                message = _(
                    """
                Dear Customer,
                
                Your document "{0}" has been rejected.
                
                Document Type: {1}
                Rejection Reason: {2}
                
                Please contact us for more information or to resubmit the document.
                
                Best regards,
                Universal Workshop Team
                """
                ).format(
                    self.document_title,
                    self.document_type,
                    self.rejection_reason or "Not specified",
                )

                frappe.sendmail(recipients=[customer_email], subject=subject, message=message)


@frappe.whitelist()
def get_customer_documents(customer, document_type=None, status=None):
    """Get documents for a customer with Arabic support"""
    filters = {"customer": customer}

    if document_type:
        filters["document_type"] = document_type

    if status:
        filters["status"] = status

    fields = [
        "name",
        "document_title",
        "document_title_ar",
        "document_type",
        "status",
        "created_date",
        "file_size",
        "download_count",
        "approval_required",
        "preview_status",
    ]

    documents = frappe.get_list(
        "Customer Document Storage", filters=filters, fields=fields, order_by="created_date desc"
    )

    return documents


@frappe.whitelist()
def download_document(doc_id):
    """Download document with access control"""
    doc = frappe.get_doc("Customer Document Storage", doc_id)

    if not doc.can_download():
        frappe.throw(_("Access denied for this document"))

    doc.record_download()

    return {"file_url": doc.file_url, "file_name": doc.file_name, "mime_type": doc.mime_type}


@frappe.whitelist()
def get_document_preview(doc_id):
    """Get document preview/thumbnail"""
    doc = frappe.get_doc("Customer Document Storage", doc_id)

    if not doc.can_read():
        frappe.throw(_("Access denied for this document"))

    if not doc.document_preview:
        frappe.throw(_("Preview not available for this document"))

    return {"thumbnail_url": doc.thumbnail_url, "preview_status": doc.preview_status}


@frappe.whitelist()
def approve_document(doc_id, approval_reason=""):
    """Approve a document"""
    doc = frappe.get_doc("Customer Document Storage", doc_id)
    doc.approve_document(approval_reason)
    return {"message": _("Document approved successfully")}


@frappe.whitelist()
def reject_document(doc_id, rejection_reason="", rejection_reason_ar=""):
    """Reject a document"""
    doc = frappe.get_doc("Customer Document Storage", doc_id)
    doc.reject_document(rejection_reason, rejection_reason_ar)
    return {"message": _("Document rejected successfully")}


@frappe.whitelist()
def get_document_stats(customer=None):
    """Get document statistics for dashboard"""
    filters = {}
    if customer:
        filters["customer"] = customer

    stats = {
        "total_documents": frappe.db.count("Customer Document Storage", filters),
        "pending_approval": frappe.db.count(
            "Customer Document Storage", {**filters, "status": "Pending Approval"}
        ),
        "approved_documents": frappe.db.count(
            "Customer Document Storage", {**filters, "status": "Approved"}
        ),
        "rejected_documents": frappe.db.count(
            "Customer Document Storage", {**filters, "status": "Rejected"}
        ),
        "total_downloads": frappe.db.sql(
            """
            SELECT SUM(download_count) 
            FROM `tabCustomer Document Storage` 
            WHERE %s
        """
            % (" AND ".join([f"{k} = %({k})s" for k in filters.keys()]) if filters else "1=1"),
            filters,
        )[0][0]
        or 0,
    }

    return stats
