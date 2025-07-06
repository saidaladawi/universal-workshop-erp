import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, cint, flt, add_days
from datetime import datetime, timedelta
import json


class TrainingProgress(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate training progress data before saving"""
        self.validate_user_data()
        self.validate_progress_percentage()
        self.validate_quiz_scores()
        self.calculate_competency_level()
        self.update_timestamps()

    def before_save(self):
        """Set default values and computed fields before saving"""
        self.set_user_details()
        self.set_training_module_details()
        self.calculate_progress_metrics()
        self.determine_certification_status()

    def after_save(self):
        """Trigger post-save actions"""
        if self.status == "Completed" and self.certification_issued:
            self.generate_certification()

        # Check for milestone notifications
        self.check_milestone_notifications()

        # Check for overdue training notifications
        self.check_overdue_notifications()

    def validate_user_data(self):
        """Validate user and training module data"""
        if not self.user:
            frappe.throw(_("User is required"))

        if not self.training_module:
            frappe.throw(_("Training Module is required"))

        # Check for duplicate progress records
        existing = frappe.db.exists(
            "Training Progress",
            {"user": self.user, "training_module": self.training_module, "name": ["!=", self.name]},
        )
        if existing:
            frappe.throw(_("Progress record already exists for this user and module"))

    def validate_progress_percentage(self):
        """Validate progress percentage is within valid range"""
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            frappe.throw(_("Progress percentage must be between 0 and 100"))

    def validate_quiz_scores(self):
        """Validate quiz scores and assessment data"""
        if self.has_assessment:
            if self.quiz_score is not None:
                if self.quiz_score < 0 or self.quiz_score > 100:
                    frappe.throw(_("Quiz score must be between 0 and 100"))

            if self.quiz_attempts < 0:
                frappe.throw(_("Quiz attempts cannot be negative"))

            # Auto-determine if assessment is passed
            if self.quiz_score is not None and self.passing_score_required:
                self.passed_assessment = 1 if self.quiz_score >= self.passing_score_required else 0

    def calculate_competency_level(self):
        """Calculate competency level based on progress and assessment"""
        if self.status == "Completed" and self.passed_assessment:
            if self.quiz_score >= 90:
                self.competency_level = "Expert"
            elif self.quiz_score >= 80:
                self.competency_level = "Advanced"
            elif self.quiz_score >= 70:
                self.competency_level = "Intermediate"
            else:
                self.competency_level = "Beginner"
        elif self.progress_percentage < 25:
            self.competency_level = "Not Assessed"
        else:
            self.competency_level = "Beginner"

    def update_timestamps(self):
        """Update relevant timestamps based on status"""
        current_time = now_datetime()

        if self.status == "In Progress" and not self.started_on:
            self.started_on = current_time

        if self.status == "Completed" and not self.completed_on:
            self.completed_on = current_time

        # Always update last accessed when record is modified
        self.last_accessed = current_time

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

    def set_training_module_details(self):
        """Set training module details"""
        if self.training_module:
            module_doc = frappe.get_doc("Training Module", self.training_module)
            self.module_title = module_doc.title
            self.has_assessment = module_doc.has_quiz
            self.passing_score_required = module_doc.passing_score or 70

    def calculate_progress_metrics(self):
        """Calculate various progress metrics"""
        # Calculate time spent if started and last accessed
        if self.started_on and self.last_accessed:
            time_diff = datetime.fromisoformat(str(self.last_accessed)) - datetime.fromisoformat(
                str(self.started_on)
            )
            self.time_spent_minutes = int(time_diff.total_seconds() / 60)

        # Set next review date for competency verification
        if self.completed_on and self.competency_level in ["Advanced", "Expert"]:
            completion_date = getdate(self.completed_on)
            self.next_review_date = completion_date + timedelta(days=365)  # Annual review
        elif self.completed_on:
            completion_date = getdate(self.completed_on)
            self.next_review_date = completion_date + timedelta(days=180)  # Semi-annual review

    def determine_certification_status(self):
        """Determine if certification should be issued"""
        if (
            self.status == "Completed"
            and self.passed_assessment
            and self.competency_level in ["Advanced", "Expert"]
        ):

            # Check if training module requires certification
            module_doc = frappe.get_doc("Training Module", self.training_module)
            if module_doc.requires_certification:
                self.certification_issued = 1

    def generate_certification(self):
        """Generate and save certification PDF"""
        try:
            # Create certification record
            certification = frappe.new_doc("Training Certification")
            certification.user = self.user
            certification.training_module = self.training_module
            certification.training_progress = self.name
            certification.competency_level = self.competency_level
            certification.quiz_score = self.quiz_score
            certification.completed_on = self.completed_on
            certification.valid_until = self.next_review_date
            certification.insert()

            frappe.msgprint(_("Training certification generated successfully"))

        except Exception as e:
            frappe.log_error(f"Failed to generate certification: {str(e)}")
            frappe.msgprint(_("Warning: Could not generate certification automatically"))

    @frappe.whitelist()
    def update_progress(self, progress_percentage, time_spent=None):
        """Update progress from external sources (H5P, etc.)"""
        self.progress_percentage = flt(progress_percentage)

        if time_spent:
            self.time_spent_minutes += cint(time_spent)

        # Update status based on progress
        if self.progress_percentage >= 100:
            self.status = "Completed"
        elif self.progress_percentage > 0:
            self.status = "In Progress"

        self.save()
        return {"status": "success", "message": _("Progress updated successfully")}

    @frappe.whitelist()
    def record_quiz_attempt(self, score, attempt_number=None):
        """Record quiz attempt and score"""
        self.quiz_score = flt(score)

        if attempt_number:
            self.quiz_attempts = cint(attempt_number)
        else:
            self.quiz_attempts += 1

        # Check if passed
        if self.passing_score_required:
            self.passed_assessment = 1 if self.quiz_score >= self.passing_score_required else 0

        self.save()
        return {
            "status": "success",
            "passed": self.passed_assessment,
            "message": _("Quiz attempt recorded successfully"),
        }

    @frappe.whitelist()
    def identify_skill_gaps(self):
        """Identify skill gaps and recommend remedial training"""
        gaps = []

        if self.quiz_score < self.passing_score_required:
            gaps.append(_("Overall assessment score below passing threshold"))

        if self.competency_level in ["Beginner", "Not Assessed"]:
            gaps.append(_("Basic competency not achieved"))

        if self.time_spent_minutes < 30:  # Minimum expected time
            gaps.append(_("Insufficient time spent on training content"))

        if gaps:
            self.skill_gaps_identified = "\n".join(gaps)
            self.requires_remedial_training = 1
        else:
            self.skill_gaps_identified = ""
            self.requires_remedial_training = 0

        self.save()
        return {"gaps": gaps, "requires_remedial": self.requires_remedial_training}

    def check_milestone_notifications(self):
        """Check and send milestone achievement notifications"""
        milestones = [25, 50, 75, 100]

        for milestone in milestones:
            if self.progress_percentage >= milestone:
                notification_key = f"milestone_{milestone}_{self.name}"

                # Check if notification already sent
                existing_notification = frappe.db.exists(
                    "Notification Log",
                    {
                        "document_type": "Training Progress",
                        "document_name": self.name,
                        "subject": ["like", f"%{milestone}%"]
                    }
                )

                if not existing_notification:
                    self.send_milestone_notification(milestone)

    def send_milestone_notification(self, milestone):
        """Send milestone achievement notification"""
        try:
            # Create notification
            notification = frappe.new_doc("Notification Log")
            notification.subject = _("Training Milestone Achieved: {0}% Complete").format(milestone)
            notification.email_content = self.get_milestone_email_content(milestone)
            notification.document_type = "Training Progress"
            notification.document_name = self.name
            notification.for_user = self.user
            notification.type = "Alert"
            notification.insert(ignore_permissions=True)

            # Send email if user has email
            user_email = frappe.db.get_value("User", self.user, "email")
            if user_email:
                frappe.sendmail(
                    recipients=[user_email],
                    subject=notification.subject,
                    message=notification.email_content,
                    header=_("Training Progress Update")
                )

            # Create in-app notification
            frappe.publish_realtime(
                "training_milestone",
                {
                    "user": self.user,
                    "milestone": milestone,
                    "module": self.module_title,
                    "message": _("Congratulations! You've completed {0}% of {1}").format(
                        milestone, self.module_title
                    )
                },
                user=self.user
            )

        except Exception as e:
            frappe.log_error(f"Failed to send milestone notification: {str(e)}")

    def get_milestone_email_content(self, milestone):
        """Generate email content for milestone notification"""
        if milestone == 100:
            content = _("Congratulations! You have successfully completed the training module '{0}'.").format(
                self.module_title
            )
            if self.certification_issued:
                content += _(" Your certificate is now available for download.")
        else:
            content = _("Great progress! You have completed {0}% of the training module '{1}'.").format(
                milestone, self.module_title
            )
            content += _(" Keep up the excellent work!")

        return f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #667eea;">Training Progress Update</h2>
            <p>{content}</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>Module:</strong> {self.module_title}<br>
                <strong>Progress:</strong> {self.progress_percentage}%<br>
                <strong>Status:</strong> {_(self.status)}<br>
                {f"<strong>Score:</strong> {self.quiz_score}%<br>" if self.quiz_score else ""}
                {f"<strong>Competency Level:</strong> {_(self.competency_level)}<br>" if self.competency_level else ""}
            </div>
            <p>Access your training dashboard: <a href="/training-dashboard">Training Dashboard</a></p>
        </div>
        """

    def check_overdue_notifications(self):
        """Check for overdue training and send reminders"""
        if not self.next_review_date:
            return

        days_overdue = (getdate() - getdate(self.next_review_date)).days

        # Send notifications at 7, 30, and 60 days overdue
        if days_overdue in [7, 30, 60]:
            self.send_overdue_notification(days_overdue)

    def send_overdue_notification(self, days_overdue):
        """Send overdue training notification"""
        try:
            subject = _("Training Review Overdue: {0}").format(self.module_title)

            notification = frappe.new_doc("Notification Log")
            notification.subject = subject
            notification.email_content = self.get_overdue_email_content(days_overdue)
            notification.document_type = "Training Progress"
            notification.document_name = self.name
            notification.for_user = self.user
            notification.type = "Alert"
            notification.insert(ignore_permissions=True)

            # Send email notification
            user_email = frappe.db.get_value("User", self.user, "email")
            if user_email:
                frappe.sendmail(
                    recipients=[user_email],
                    subject=subject,
                    message=notification.email_content,
                    header=_("Training Review Required")
                )

        except Exception as e:
            frappe.log_error(f"Failed to send overdue notification: {str(e)}")

    def get_overdue_email_content(self, days_overdue):
        """Generate email content for overdue notification"""
        return f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">Training Review Required</h2>
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>⚠️ Your training review is {days_overdue} days overdue</strong>
            </div>
            <p>The following training module requires review:</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>Module:</strong> {self.module_title}<br>
                <strong>Review Due Date:</strong> {self.next_review_date}<br>
                <strong>Current Competency:</strong> {_(self.competency_level or 'Not Assessed')}<br>
            </div>
            <p>Please complete the review to maintain your certification status.</p>
            <p>Access your training dashboard: <a href="/training-dashboard">Training Dashboard</a></p>
        </div>
        """


# API Methods for external integration
@frappe.whitelist()
def get_user_progress(user, training_module=None):
    """Get progress data for a specific user"""
    filters = {"user": user}
    if training_module:
        filters["training_module"] = training_module

    progress_records = frappe.get_list(
        "Training Progress",
        filters=filters,
        fields=[
            "name",
            "training_module",
            "module_title",
            "status",
            "progress_percentage",
            "quiz_score",
            "competency_level",
            "started_on",
            "completed_on",
            "certification_issued",
        ],
        order_by="last_accessed desc",
    )

    return progress_records


@frappe.whitelist()
def create_progress_record(user, training_module):
    """Create new progress record for user"""
    # Check if already exists
    existing = frappe.db.exists(
        "Training Progress", {"user": user, "training_module": training_module}
    )

    if existing:
        return {"status": "exists", "name": existing}

    # Create new record
    progress = frappe.new_doc("Training Progress")
    progress.user = user
    progress.training_module = training_module
    progress.status = "Not Started"
    progress.insert()

    return {"status": "created", "name": progress.name}


@frappe.whitelist()
def get_competency_dashboard(user):
    """Get competency dashboard data for user"""
    # Get all progress records for user
    progress_records = frappe.get_list(
        "Training Progress",
        filters={"user": user},
        fields=[
            "training_module",
            "module_title",
            "status",
            "progress_percentage",
            "competency_level",
            "certification_issued",
            "next_review_date",
        ],
    )

    # Get certifications
    certifications = frappe.get_list(
        "Training Certification",
        filters={"user": user},
        fields=["training_module", "competency_level", "valid_until", "file_url"],
    )

    # Calculate statistics
    total_modules = len(progress_records)
    completed_modules = len([p for p in progress_records if p.status == "Completed"])
    certified_modules = len([p for p in progress_records if p.certification_issued])

    return {
        "statistics": {
            "total_modules": total_modules,
            "completed_modules": completed_modules,
            "certified_modules": certified_modules,
            "completion_rate": (
                (completed_modules / total_modules * 100) if total_modules > 0 else 0
            ),
        },
        "progress_records": progress_records,
        "certifications": certifications,
    }
