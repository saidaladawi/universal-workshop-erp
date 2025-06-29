import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, cint, flt, add_days
from datetime import datetime, timedelta
import json


class UserTrainingPath(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate user training path data before saving"""
        self.validate_user_and_path()
        self.set_user_details()
        self.set_path_details()
        self.calculate_progress_metrics()

    def before_save(self):
        """Set default values and computed fields before saving"""
        self.update_progress_status()
        self.set_metadata_fields()

    def after_save(self):
        """Trigger post-save actions"""
        if self.status == "Completed" and not self.completed_on:
            self.handle_path_completion()

    def validate_user_and_path(self):
        """Validate user and training path exist and are valid"""
        if not self.user:
            frappe.throw(_("User is required"))

        if not self.training_path:
            frappe.throw(_("Training Path is required"))

        # Check for duplicate enrollment
        existing = frappe.db.exists(
            "User Training Path",
            {
                "user": self.user,
                "training_path": self.training_path,
                "name": ["!=", self.name]
            }
        )
        if existing:
            frappe.throw(_("User is already enrolled in this training path"))

    def set_user_details(self):
        """Set user details from User DocType"""
        if self.user:
            user_doc = frappe.get_doc("User", self.user)
            self.full_name = user_doc.full_name or user_doc.first_name

            # Get primary role
            if user_doc.roles:
                self.role = user_doc.roles[0].role

            # Get department from Employee if linked
            employee = frappe.db.get_value("Employee", {"user_id": self.user}, "department")
            if employee:
                self.department = employee

    def set_path_details(self):
        """Set training path details"""
        if self.training_path:
            path_doc = frappe.get_doc("Training Path", self.training_path)
            self.path_name = path_doc.path_name
            self.total_modules = len(path_doc.training_modules)

    def calculate_progress_metrics(self):
        """Calculate progress metrics based on completed modules"""
        if not self.training_path:
            return

        # Get path modules
        path_doc = frappe.get_doc("Training Path", self.training_path)
        path_modules = [m.training_module for m in path_doc.training_modules]

        # Get user's completed modules in this path
        completed_progress = frappe.get_all(
            "Training Progress",
            filters={
                "user": self.user,
                "training_module": ["in", path_modules],
                "status": "Completed"
            },
            fields=["training_module", "quiz_score", "competency_level", "time_spent_minutes"]
        )

        self.modules_completed = len(completed_progress)
        self.modules_remaining = self.total_modules - self.modules_completed

        # Calculate progress percentage
        if self.total_modules > 0:
            self.progress_percentage = (self.modules_completed / self.total_modules) * 100
        else:
            self.progress_percentage = 0

        # Calculate average score
        scores = [p.quiz_score for p in completed_progress if p.quiz_score is not None]
        if scores:
            self.average_score = sum(scores) / len(scores)

        # Calculate total time spent
        total_minutes = sum([p.time_spent_minutes or 0 for p in completed_progress])
        self.total_time_spent_hours = total_minutes / 60 if total_minutes > 0 else 0

        # Determine overall competency level
        self.calculate_overall_competency(completed_progress)

        # Set current module (next module to take)
        self.set_current_module(path_doc, completed_progress)

    def calculate_overall_competency(self, completed_progress):
        """Calculate overall competency level based on completed modules"""
        if not completed_progress:
            self.overall_competency_level = "Not Assessed"
            return

        competency_levels = ["Not Assessed", "Beginner", "Intermediate", "Advanced", "Expert"]
        competency_scores = {
            "Not Assessed": 0,
            "Beginner": 1,
            "Intermediate": 2,
            "Advanced": 3,
            "Expert": 4
        }

        # Calculate weighted average competency
        total_score = 0
        total_modules = len(completed_progress)

        for progress in completed_progress:
            competency = progress.competency_level or "Not Assessed"
            total_score += competency_scores.get(competency, 0)

        if total_modules > 0:
            avg_score = total_score / total_modules

            # Map back to competency level
            if avg_score >= 3.5:
                self.overall_competency_level = "Expert"
            elif avg_score >= 2.5:
                self.overall_competency_level = "Advanced"
            elif avg_score >= 1.5:
                self.overall_competency_level = "Intermediate"
            elif avg_score >= 0.5:
                self.overall_competency_level = "Beginner"
            else:
                self.overall_competency_level = "Not Assessed"

    def set_current_module(self, path_doc, completed_progress):
        """Set the current module user should work on"""
        completed_modules = [p.training_module for p in completed_progress]

        # Find next module in sequence that's not completed
        for module in sorted(path_doc.training_modules, key=lambda x: x.sequence_order):
            if module.training_module not in completed_modules:
                self.current_module = module.training_module
                break
        else:
            # All modules completed
            self.current_module = None

    def update_progress_status(self):
        """Update status based on progress"""
        if self.progress_percentage >= 100:
            self.status = "Completed"
            if not self.completed_on:
                self.completed_on = now_datetime()
        elif self.progress_percentage > 0:
            self.status = "In Progress"
            if not self.started_on:
                self.started_on = now_datetime()
        else:
            self.status = "Not Started"

        # Update last activity date
        self.last_activity_date = now_datetime()

    def set_metadata_fields(self):
        """Set metadata fields"""
        if not self.created_by:
            self.created_by = frappe.session.user
            self.created_date = now_datetime()

        if not self.enrolled_on:
            self.enrolled_on = now_datetime()

    def handle_path_completion(self):
        """Handle path completion actions"""
        # Set next review date
        path_doc = frappe.get_doc("Training Path", self.training_path)
        if path_doc.review_frequency_months:
            self.next_review_date = add_days(getdate(), path_doc.review_frequency_months * 30)

        # Send completion notification
        self.send_completion_notification()

        # Check for automatic enrollment in advanced paths
        self.check_advanced_path_enrollment()

    def send_completion_notification(self):
        """Send path completion notification"""
        try:
            notification = frappe.new_doc("Notification Log")
            notification.subject = _("Training Path Completed: {0}").format(self.path_name)
            notification.email_content = self.get_completion_email_content()
            notification.document_type = "User Training Path"
            notification.document_name = self.name
            notification.for_user = self.user
            notification.type = "Alert"
            notification.insert(ignore_permissions=True)

            # Send email
            user_email = frappe.db.get_value("User", self.user, "email")
            if user_email:
                frappe.sendmail(
                    recipients=[user_email],
                    subject=notification.subject,
                    message=notification.email_content,
                    header=_("Training Path Completion")
                )

        except Exception as e:
            frappe.log_error(f"Failed to send completion notification: {str(e)}")

    def get_completion_email_content(self):
        """Generate email content for path completion"""
        return f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #28a745;">🎉 Training Path Completed!</h2>
            <p>Congratulations! You have successfully completed the training path:</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>Path:</strong> {self.path_name}<br>
                <strong>Modules Completed:</strong> {self.modules_completed}<br>
                <strong>Overall Competency:</strong> {_(self.overall_competency_level)}<br>
                <strong>Average Score:</strong> {self.average_score:.1f}%<br>
                <strong>Total Time:</strong> {self.total_time_spent_hours:.1f} hours<br>
                <strong>Completion Date:</strong> {self.completed_on}
            </div>
            <p>Access your training dashboard: <a href="/training-dashboard">Training Dashboard</a></p>
        </div>
        """

    def check_advanced_path_enrollment(self):
        """Check for automatic enrollment in advanced paths"""
        try:
            # Find paths that have this path as a prerequisite
            advanced_paths = frappe.get_all(
                "Training Path Prerequisite",
                filters={"prerequisite_path": self.training_path},
                fields=["parent"]
            )

            for path_data in advanced_paths:
                path_doc = frappe.get_doc("Training Path", path_data.parent)

                # Check if user meets criteria and auto-enrollment is enabled
                if path_doc.auto_enrollment and path_doc.meets_enrollment_criteria(self.user):
                    path_doc.create_user_enrollment(self.user)

        except Exception as e:
            frappe.log_error(f"Failed to check advanced path enrollment: {str(e)}")

    @frappe.whitelist()
    def apply_adaptive_adjustment(self, adjustment_type, notes=""):
        """Apply adaptive learning adjustment"""
        current_adjustments = self.adaptive_adjustments_made or ""
        timestamp = now_datetime().strftime("%Y-%m-%d %H:%M")

        new_adjustment = f"[{timestamp}] {adjustment_type}: {notes}"

        if current_adjustments:
            self.adaptive_adjustments_made = current_adjustments + "\n" + new_adjustment
        else:
            self.adaptive_adjustments_made = new_adjustment

        self.save()

        return {"status": "success", "message": _("Adaptive adjustment applied")}

    @frappe.whitelist()
    def record_remedial_action(self, action_type, details=""):
        """Record remedial action taken"""
        current_actions = self.remedial_actions_taken or ""
        timestamp = now_datetime().strftime("%Y-%m-%d %H:%M")

        new_action = f"[{timestamp}] {action_type}: {details}"

        if current_actions:
            self.remedial_actions_taken = current_actions + "\n" + new_action
        else:
            self.remedial_actions_taken = new_action

        self.save()

        return {"status": "success", "message": _("Remedial action recorded")}

    @frappe.whitelist()
    def get_learning_analytics(self):
        """Get learning analytics for this user's path"""
        # Get detailed module progress
        path_doc = frappe.get_doc("Training Path", self.training_path)
        path_modules = [m.training_module for m in path_doc.training_modules]

        module_progress = frappe.get_all(
            "Training Progress",
            filters={
                "user": self.user,
                "training_module": ["in", path_modules]
            },
            fields=[
                "training_module", "module_title", "status", "progress_percentage",
                "quiz_score", "competency_level", "time_spent_minutes",
                "started_on", "completed_on"
            ]
        )

        # Calculate time distribution
        time_per_module = {}
        for progress in module_progress:
            if progress.time_spent_minutes:
                time_per_module[progress.module_title] = progress.time_spent_minutes / 60

        # Calculate difficulty analysis
        difficulty_analysis = {}
        for progress in module_progress:
            if progress.quiz_score is not None:
                module_doc = frappe.get_doc("Training Module", progress.training_module)
                difficulty = module_doc.difficulty_level or "Beginner"

                if difficulty not in difficulty_analysis:
                    difficulty_analysis[difficulty] = []
                difficulty_analysis[difficulty].append(progress.quiz_score)

        # Average scores by difficulty
        avg_scores_by_difficulty = {}
        for difficulty, scores in difficulty_analysis.items():
            avg_scores_by_difficulty[difficulty] = sum(scores) / len(scores)

        return {
            "module_progress": module_progress,
            "time_per_module": time_per_module,
            "avg_scores_by_difficulty": avg_scores_by_difficulty,
            "total_time_hours": self.total_time_spent_hours,
            "completion_rate": self.progress_percentage,
            "overall_competency": self.overall_competency_level
        }


# API Methods for user training path management
@frappe.whitelist()
def get_user_path_dashboard(user):
    """Get dashboard data for user's training paths"""
    user_paths = frappe.get_all(
        "User Training Path",
        filters={"user": user},
        fields=[
            "name", "training_path", "path_name", "status", "progress_percentage",
            "modules_completed", "total_modules", "overall_competency_level",
            "enrolled_on", "started_on", "completed_on", "next_review_date"
        ]
    )

    # Get recommended paths
    recommended_paths = get_recommended_paths_for_user(user)

    # Get upcoming deadlines
    upcoming_deadlines = frappe.get_all(
        "User Training Path",
        filters={
            "user": user,
            "next_review_date": [">=", getdate()],
            "status": "Completed"
        },
        fields=["training_path", "path_name", "next_review_date"],
        order_by="next_review_date"
    )

    return {
        "enrolled_paths": user_paths,
        "recommended_paths": recommended_paths,
        "upcoming_deadlines": upcoming_deadlines[:5]  # Next 5 deadlines
    }


def get_recommended_paths_for_user(user):
    """Get recommended training paths for user"""
    # Get user's roles
    user_roles = frappe.get_all(
        "Has Role", filters={"parent": user}, fields=["role"]
    )
    roles = [r.role for r in user_roles]

    # Get available paths for user's roles
    available_paths = frappe.get_all(
        "Training Path",
        filters={
            "role": ["in", roles],
            "is_active": 1
        },
        fields=[
            "name", "path_name", "description", "difficulty_level",
            "estimated_duration_hours", "role"
        ]
    )

    # Filter out already enrolled paths
    enrolled_paths = frappe.get_all(
        "User Training Path",
        filters={"user": user},
        fields=["training_path"]
    )
    enrolled_path_names = [e.training_path for e in enrolled_paths]

    recommended = []
    for path in available_paths:
        if path.name not in enrolled_path_names:
            recommended.append(path)

    return recommended[:3]  # Top 3 recommendations
