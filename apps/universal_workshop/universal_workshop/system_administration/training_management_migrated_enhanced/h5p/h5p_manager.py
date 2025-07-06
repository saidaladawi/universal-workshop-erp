# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional, Any

import frappe
from frappe import _
from frappe.utils.file_manager import get_file_path, save_file


class H5PManager:
    """
    H5P Content Manager for Universal Workshop Training System
    Handles H5P content upload, extraction, and integration with Frappe
    """

    def __init__(self):
        self.h5p_content_path = self.get_h5p_content_path()
        self.ensure_directories()

    def get_h5p_content_path(self) -> Path:
        """Get the base path for H5P content storage"""
        site_path = frappe.utils.get_site_path()
        return Path(site_path) / "private" / "files" / "h5p_content"

    def ensure_directories(self):
        """Ensure required directories exist"""
        self.h5p_content_path.mkdir(parents=True, exist_ok=True)
        (self.h5p_content_path / "libraries").mkdir(exist_ok=True)
        (self.h5p_content_path / "content").mkdir(exist_ok=True)
        (self.h5p_content_path / "temp").mkdir(exist_ok=True)

    def upload_h5p_file(self, file_path: str, training_module: str) -> Dict[str, Any]:
        """
        Upload and process H5P file

        Args:
            file_path: Path to the uploaded H5P file
            training_module: Training Module document name

        Returns:
            Dict with content_id, success status, and metadata
        """
        try:
            # Generate unique content ID
            content_id = f"h5p_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}_{frappe.utils.random_string(6)}"

            # Create content directory
            content_dir = self.h5p_content_path / "content" / content_id
            content_dir.mkdir(parents=True, exist_ok=True)

            # Extract H5P file
            metadata = self.extract_h5p_file(file_path, content_dir)

            # Store content metadata
            content_info = {
                "content_id": content_id,
                "training_module": training_module,
                "title": metadata.get("title", "Unknown"),
                "library": metadata.get("preloadedDependencies", []),
                "content_path": str(content_dir),
                "uploaded_by": frappe.session.user,
                "uploaded_on": frappe.utils.now(),
                "status": "active",
            }

            # Save content info to database
            self.save_h5p_content_info(content_info)

            return {
                "success": True,
                "content_id": content_id,
                "metadata": metadata,
                "message": _("H5P content uploaded successfully"),
            }

        except Exception as e:
            frappe.logger().error(f"H5P upload failed: {e}")
            return {"success": False, "error": str(e), "message": _("H5P content upload failed")}

    def extract_h5p_file(self, file_path: str, extract_to: Path) -> Dict[str, Any]:
        """
        Extract H5P file and return metadata

        Args:
            file_path: Path to H5P file
            extract_to: Directory to extract content

        Returns:
            H5P content metadata
        """
        actual_file_path = get_file_path(file_path)

        with zipfile.ZipFile(actual_file_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        # Read h5p.json metadata
        h5p_json_path = extract_to / "h5p.json"
        if h5p_json_path.exists():
            with open(h5p_json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            metadata = {"title": "Unknown H5P Content"}

        # Read content.json for additional metadata
        content_json_path = extract_to / "content" / "content.json"
        if content_json_path.exists():
            with open(content_json_path, "r", encoding="utf-8") as f:
                content_data = json.load(f)
                metadata["content"] = content_data

        return metadata

    def save_h5p_content_info(self, content_info: Dict[str, Any]):
        """Save H5P content information to database"""
        # Store in a custom table or use Frappe's database
        frappe.db.sql(
            """
            INSERT INTO `tabH5P Content` 
            (name, content_id, training_module, title, library_info, content_path, 
             uploaded_by, uploaded_on, status, creation, modified, owner, modified_by)
            VALUES (%(content_id)s, %(content_id)s, %(training_module)s, %(title)s, 
                    %(library)s, %(content_path)s, %(uploaded_by)s, %(uploaded_on)s, 
                    %(status)s, NOW(), NOW(), %(uploaded_by)s, %(uploaded_by)s)
            ON DUPLICATE KEY UPDATE
            modified = NOW(), modified_by = %(uploaded_by)s
        """,
            {
                "content_id": content_info["content_id"],
                "training_module": content_info["training_module"],
                "title": content_info["title"],
                "library": json.dumps(content_info["library"]),
                "content_path": content_info["content_path"],
                "uploaded_by": content_info["uploaded_by"],
                "uploaded_on": content_info["uploaded_on"],
                "status": content_info["status"],
            },
        )
        frappe.db.commit()

    def get_h5p_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve H5P content by ID

        Args:
            content_id: H5P content identifier

        Returns:
            Content data or None if not found
        """
        try:
            content_info = frappe.db.get_value(
                "H5P Content",
                content_id,
                ["content_id", "title", "library_info", "content_path", "status"],
                as_dict=True,
            )

            if not content_info or content_info.status != "active":
                return None

            content_path = Path(content_info.content_path)

            # Read content.json
            content_json_path = content_path / "content" / "content.json"
            if content_json_path.exists():
                with open(content_json_path, "r", encoding="utf-8") as f:
                    content_data = json.load(f)
            else:
                content_data = {}

            return {
                "content_id": content_id,
                "title": content_info.title,
                "library_info": json.loads(content_info.library_info or "[]"),
                "content_data": content_data,
                "base_url": f"/private/files/h5p_content/content/{content_id}",
            }

        except Exception as e:
            frappe.logger().error(f"Failed to retrieve H5P content {content_id}: {e}")
            return None

    def generate_h5p_player_config(self, content_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Generate H5P player configuration

        Args:
            content_id: H5P content identifier
            user_id: User ID for progress tracking

        Returns:
            H5P player configuration
        """
        content = self.get_h5p_content(content_id)
        if not content:
            return {}

        user_id = user_id or frappe.session.user

        config = {
            "baseUrl": "/assets/universal_workshop/h5p",
            "url": content["base_url"],
            "postUserStatistics": True,
            "ajax": {
                "setFinished": f"/api/method/universal_workshop.training_management.h5p.h5p_manager.set_finished",
                "contentUserData": f"/api/method/universal_workshop.training_management.h5p.h5p_manager.content_user_data",
            },
            "saveFreq": 30,  # Save progress every 30 seconds
            "user": {"name": frappe.get_value("User", user_id, "full_name"), "id": user_id},
            "content": {
                "id": content_id,
                "title": content["title"],
                "library": content["library_info"],
                "jsonContent": content["content_data"],
            },
            "l10n": self.get_localization_strings(),
        }

        return config

    def get_localization_strings(self) -> Dict[str, str]:
        """Get localized strings for H5P player"""
        if frappe.local.lang == "ar":
            return {
                "fullscreen": "ملء الشاشة",
                "disableFullscreen": "إلغاء ملء الشاشة",
                "download": "تحميل",
                "copyrights": "حقوق الطبع والنشر",
                "embed": "تضمين",
                "size": "الحجم",
                "showAdvanced": "إظهار خيارات متقدمة",
                "hideAdvanced": "إخفاء خيارات متقدمة",
                "advancedHelp": "قم بتضمين هذا المحتوى عن طريق نسخ ولصق الرمز أدناه",
                "copyrightInformation": "معلومات حقوق الطبع والنشر",
                "close": "إغلاق",
                "title": "العنوان",
                "author": "المؤلف",
                "year": "السنة",
                "source": "المصدر",
                "license": "الترخيص",
                "thumbnail": "الصورة المصغرة",
                "noCopyrights": "لا توجد معلومات حقوق طبع ونشر متاحة",
                "reuse": "إعادة استخدام المحتوى",
                "reuseContent": "إعادة استخدام المحتوى",
                "reuseDescription": "إعادة استخدام هذا المحتوى",
                "downloadDescription": "تحميل هذا المحتوى كملف H5P",
                "copyrightsDescription": "عرض معلومات حقوق الطبع والنشر",
            }
        else:
            return {
                "fullscreen": "Fullscreen",
                "disableFullscreen": "Disable fullscreen",
                "download": "Download",
                "copyrights": "Rights of use",
                "embed": "Embed",
                "size": "Size",
                "showAdvanced": "Show advanced",
                "hideAdvanced": "Hide advanced",
                "advancedHelp": "Include this content in your website by copying and pasting this code",
                "copyrightInformation": "Rights of use",
                "close": "Close",
                "title": "Title",
                "author": "Author",
                "year": "Year",
                "source": "Source",
                "license": "License",
                "thumbnail": "Thumbnail",
                "noCopyrights": "No copyright information available",
                "reuse": "Reuse",
                "reuseContent": "Reuse Content",
                "reuseDescription": "Reuse this content",
                "downloadDescription": "Download this content as a H5P file",
                "copyrightsDescription": "View copyright information",
            }

    def delete_h5p_content(self, content_id: str) -> bool:
        """
        Delete H5P content

        Args:
            content_id: H5P content identifier

        Returns:
            Success status
        """
        try:
            # Get content path
            content_path = self.h5p_content_path / "content" / content_id

            # Remove files
            if content_path.exists():
                import shutil

                shutil.rmtree(content_path)

            # Remove database record
            frappe.db.sql("DELETE FROM `tabH5P Content` WHERE content_id = %s", (content_id,))
            frappe.db.commit()

            return True

        except Exception as e:
            frappe.logger().error(f"Failed to delete H5P content {content_id}: {e}")
            return False


# Global instance
h5p_manager = H5PManager()


@frappe.whitelist()
def upload_h5p_content(training_module: str):
    """API endpoint for H5P content upload"""
    if not frappe.has_permission("Training Module", "write"):
        frappe.throw(_("Insufficient permissions"))

    if not frappe.form_dict.get("file"):
        frappe.throw(_("No file uploaded"))

    file_doc = frappe.get_doc("File", frappe.form_dict.file)
    result = h5p_manager.upload_h5p_file(file_doc.file_url, training_module)

    return result


@frappe.whitelist()
def get_h5p_player_config(content_id: str):
    """API endpoint to get H5P player configuration"""
    config = h5p_manager.generate_h5p_player_config(content_id)
    return config


@frappe.whitelist()
def set_finished(
    content_id: str,
    score: float = None,
    max_score: float = None,
    opened: int = None,
    finished: int = None,
    time: int = None,
):
    """API endpoint for H5P content completion tracking"""
    try:
        # Find related training progress record
        progress_record = frappe.db.get_value(
            "Training Progress",
            {"training_module": content_id, "user": frappe.session.user},
            "name",
        )

        if progress_record:
            progress_doc = frappe.get_doc("Training Progress", progress_record)

            if finished:
                progress_doc.status = "Completed"
                progress_doc.completed_on = frappe.utils.now()
                progress_doc.progress_percentage = 100

            if score is not None and max_score is not None and max_score > 0:
                progress_doc.quiz_score = (score / max_score) * 100
                progress_doc.quiz_attempts = (progress_doc.quiz_attempts or 0) + 1

            if time:
                progress_doc.time_spent_minutes = (progress_doc.time_spent_minutes or 0) + (
                    time / 60
                )

            progress_doc.last_accessed = frappe.utils.now()
            progress_doc.save()

        return {"success": True}

    except Exception as e:
        frappe.logger().error(f"Failed to update H5P progress: {e}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def content_user_data(
    content_id: str, data_id: str, data: str = None, preload: int = None, invalidate: int = None
):
    """API endpoint for H5P user data storage"""
    try:
        # This would implement user data storage for H5P content
        # For now, return success
        return {"success": True}

    except Exception as e:
        frappe.logger().error(f"Failed to handle H5P user data: {e}")
        return {"success": False, "error": str(e)}
