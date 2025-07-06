import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, cint, flt
from datetime import datetime, timedelta
import json


class TrainingPath(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate training path data before saving"""
        self.validate_path_data()
        self.validate_modules_sequence()
        self.validate_prerequisites()
        self.calculate_total_duration()

    def before_save(self):
        """Set default values and computed fields before saving"""
        self.set_metadata_fields()
        self.validate_role_assignment()

    def after_save(self):
        """Trigger post-save actions"""
        if self.auto_enrollment:
            self.enroll_eligible_users()

    def validate_path_data(self):
        """Validate basic path data"""
        if not self.path_name:
            frappe.throw(_("Training Path Name is required"))

        if not self.role:
            frappe.throw(_("Target Role is required"))

        # Check for duplicate path names for the same role
        existing = frappe.db.exists(
            "Training Path",
            {
                "role": self.role,
                "path_name": self.path_name,
                "name": ["!=", self.name]
            }
        )
        if existing:
            frappe.throw(_("Training path with this name already exists for role {0}").format(self.role))

    def validate_modules_sequence(self):
        """Validate training modules sequence"""
        if not self.training_modules:
            frappe.throw(_("At least one training module is required"))

        # Check for duplicate sequence orders
        sequence_orders = [m.sequence_order for m in self.training_modules if m.sequence_order]
        if len(sequence_orders) != len(set(sequence_orders)):
            frappe.throw(_("Duplicate sequence orders found in training modules"))

        # Auto-populate module titles
        for module in self.training_modules:
            if module.training_module:
                module_doc = frappe.get_doc("Training Module", module.training_module)
                module.module_title = module_doc.title
                if not module.estimated_duration_hours:
                    module.estimated_duration_hours = module_doc.estimated_duration_hours or 1

    def validate_prerequisites(self):
        """Validate prerequisite paths"""
        if self.prerequisite_paths:
            for prereq in self.prerequisite_paths:
                if prereq.prerequisite_path == self.name:
                    frappe.throw(_("A training path cannot be a prerequisite of itself"))

                # Check for circular dependencies
                if self.has_circular_dependency(prereq.prerequisite_path):
                    frappe.throw(_("Circular dependency detected with prerequisite path {0}").format(
                        prereq.prerequisite_path
                    ))

    def has_circular_dependency(self, prereq_path, visited=None):
        """Check for circular dependencies in prerequisite paths"""
        if visited is None:
            visited = set()

        if prereq_path in visited:
            return True

        visited.add(prereq_path)

        # Get prerequisites of the prerequisite path
        prereq_doc = frappe.get_doc("Training Path", prereq_path)
        for prereq in prereq_doc.prerequisite_paths:
            if self.has_circular_dependency(prereq.prerequisite_path, visited.copy()):
                return True

        return False

    def calculate_total_duration(self):
        """Calculate total estimated duration"""
        total_hours = sum([m.estimated_duration_hours or 0 for m in self.training_modules])
        self.estimated_duration_hours = total_hours

    def set_metadata_fields(self):
        """Set metadata fields"""
        if not self.created_by:
            self.created_by = frappe.session.user
            self.created_date = now_datetime()

        self.last_modified_by = frappe.session.user
        self.last_modified_date = now_datetime()

    def validate_role_assignment(self):
        """Validate role assignment and check permissions"""
        # Ensure the role exists
        if not frappe.db.exists("Role", self.role):
            frappe.throw(_("Role {0} does not exist").format(self.role))

    def enroll_eligible_users(self):
        """Automatically enroll eligible users in this training path"""
        try:
            # Get users with the target role
            users_with_role = frappe.get_all(
                "Has Role",
                filters={"role": self.role},
                fields=["parent as user"]
            )

            for user_data in users_with_role:
                user = user_data.user

                # Skip system users
                if user in ["Administrator", "Guest"]:
                    continue

                # Check if user meets enrollment criteria
                if self.meets_enrollment_criteria(user):
                    self.create_user_enrollment(user)

        except Exception as e:
            frappe.log_error(f"Auto-enrollment failed for path {self.name}: {str(e)}")

    def meets_enrollment_criteria(self, user):
        """Check if user meets enrollment criteria"""
        # Check department filter
        if self.department_filter:
            user_department = frappe.db.get_value(
                "Employee", {"user_id": user}, "department"
            )
            if user_department not in [d.department for d in self.department_filter]:
                return False

        # Check prerequisites
        for prereq in self.prerequisite_paths:
            user_progress = frappe.db.get_value(
                "User Training Path",
                {"user": user, "training_path": prereq.prerequisite_path},
                ["status", "overall_competency_level"]
            )

            if not user_progress:
                return False

            status, competency = user_progress
            if status != "Completed":
                return False

            # Check minimum competency level
            competency_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
            required_level_index = competency_levels.index(prereq.minimum_competency_level)
            user_level_index = competency_levels.index(competency or "Beginner")

            if user_level_index < required_level_index:
                return False

        return True

    def create_user_enrollment(self, user):
        """Create user enrollment record"""
        # Check if already enrolled
        existing = frappe.db.exists(
            "User Training Path", {"user": user, "training_path": self.name}
        )

        if existing:
            return existing

        # Create new enrollment
        enrollment = frappe.new_doc("User Training Path")
        enrollment.user = user
        enrollment.training_path = self.name
        enrollment.status = "Not Started"
        enrollment.enrolled_on = now_datetime()
        enrollment.insert(ignore_permissions=True)

        return enrollment.name

    @frappe.whitelist()
    def get_next_module_for_user(self, user):
        """Get next module user should take in this path"""
        # Get user's progress in this path
        user_enrollments = frappe.get_all(
            "User Training Path",
            filters={"user": user, "training_path": self.name},
            fields=["name", "current_module", "status"]
        )

        if not user_enrollments:
            # User not enrolled, return first module
            first_module = min(self.training_modules, key=lambda x: x.sequence_order)
            return {
                "module": first_module.training_module,
                "module_title": first_module.module_title,
                "sequence": first_module.sequence_order,
                "is_mandatory": first_module.is_mandatory
            }

        enrollment = user_enrollments[0]

        # Get user's completed modules
        completed_modules = frappe.get_all(
            "Training Progress",
            filters={
                "user": user,
                "training_module": ["in", [m.training_module for m in self.training_modules]],
                "status": "Completed"
            },
            fields=["training_module", "competency_level", "quiz_score"]
        )

        completed_module_names = [c.training_module for c in completed_modules]

        # Find next module in sequence
        for module in sorted(self.training_modules, key=lambda x: x.sequence_order):
            if module.training_module not in completed_module_names:
                return {
                    "module": module.training_module,
                    "module_title": module.module_title,
                    "sequence": module.sequence_order,
                    "is_mandatory": module.is_mandatory,
                    "passing_score": module.passing_score_required
                }

        # All modules completed
        return {"completed": True, "message": _("All modules in this path completed")}

    @frappe.whitelist()
    def check_adaptive_progression(self, user, module_name, score):
        """Check if user can progress based on adaptive learning settings"""
        if not self.enable_adaptive_learning:
            return {"can_progress": True, "message": _("Manual progression")}

        score = flt(score)
        threshold = flt(self.performance_threshold)

        if score >= threshold:
            return {
                "can_progress": True,
                "message": _("Performance meets threshold. You can proceed to next module.")
            }
        else:
            return {
                "can_progress": False,
                "message": _("Performance below threshold. {0} required.").format(
                    _(self.remedial_action)
                ),
                "remedial_action": self.remedial_action,
                "required_score": threshold
            }

    @frappe.whitelist()
    def get_path_statistics(self):
        """Get statistics for this training path"""
        # Get total enrolled users
        total_enrolled = frappe.db.count(
            "User Training Path", {"training_path": self.name}
        )

        # Get completion statistics
        completed = frappe.db.count(
            "User Training Path", {"training_path": self.name, "status": "Completed"}
        )

        in_progress = frappe.db.count(
            "User Training Path", {"training_path": self.name, "status": "In Progress"}
        )

        # Average completion time
        avg_completion_sql = """
            SELECT AVG(DATEDIFF(completed_on, enrolled_on)) as avg_days
            FROM `tabUser Training Path`
            WHERE training_path = %s AND status = 'Completed'
            AND completed_on IS NOT NULL AND enrolled_on IS NOT NULL
        """
        avg_result = frappe.db.sql(avg_completion_sql, [self.name], as_dict=True)
        avg_completion_days = avg_result[0].avg_days if avg_result and avg_result[0].avg_days else 0

        return {
            "total_enrolled": total_enrolled,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_enrolled - completed - in_progress,
            "completion_rate": round((completed / total_enrolled * 100), 2) if total_enrolled > 0 else 0,
            "avg_completion_days": round(avg_completion_days, 1) if avg_completion_days else 0
        }


# API Methods for role-based training management
@frappe.whitelist()
def get_user_training_paths(user):
    """Get all training paths assigned to a user"""
    # Get user's roles
    user_roles = frappe.get_all(
        "Has Role", filters={"parent": user}, fields=["role"]
    )
    roles = [r.role for r in user_roles]

    # Get training paths for user's roles
    training_paths = frappe.get_all(
        "Training Path",
        filters={"role": ["in", roles], "is_active": 1},
        fields=[
            "name", "path_name", "path_name_ar", "role", "description",
            "difficulty_level", "estimated_duration_hours", "mandatory_completion"
        ]
    )

    # Get user's enrollment status for each path
    for path in training_paths:
        enrollment = frappe.db.get_value(
            "User Training Path",
            {"user": user, "training_path": path.name},
            ["status", "progress_percentage", "enrolled_on", "completed_on"],
            as_dict=True
        )

        if enrollment:
            path.update(enrollment)
        else:
            path.update({
                "status": "Not Enrolled",
                "progress_percentage": 0,
                "enrolled_on": None,
                "completed_on": None
            })

    return training_paths


@frappe.whitelist()
def enroll_user_in_path(user, training_path):
    """Manually enroll user in training path"""
    path_doc = frappe.get_doc("Training Path", training_path)

    # Check if user has required role
    user_roles = frappe.get_all(
        "Has Role", filters={"parent": user}, fields=["role"]
    )
    role_names = [r.role for r in user_roles]

    if path_doc.role not in role_names:
        frappe.throw(_("User does not have the required role: {0}").format(path_doc.role))

    # Check prerequisites
    if not path_doc.meets_enrollment_criteria(user):
        frappe.throw(_("User does not meet the enrollment criteria for this training path"))

    # Create enrollment
    enrollment_name = path_doc.create_user_enrollment(user)
    return {"status": "success", "enrollment": enrollment_name}


@frappe.whitelist()
def get_recommended_paths(user):
    """Get recommended training paths for user based on role and competency gaps"""
    # Get user's current competencies
    user_competencies = frappe.get_all(
        "Training Progress",
        filters={"user": user, "status": "Completed"},
        fields=["training_module", "competency_level"]
    )

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
            "name", "path_name", "role", "description", "difficulty_level",
            "estimated_duration_hours", "required_competencies"
        ]
    )

    # Filter out already completed or enrolled paths
    enrolled_paths = frappe.get_all(
        "User Training Path",
        filters={"user": user},
        fields=["training_path"]
    )
    enrolled_path_names = [e.training_path for e in enrolled_paths]

    recommended = []
    for path in available_paths:
        if path.name not in enrolled_path_names:
            # Score the recommendation based on various factors
            score = calculate_recommendation_score(path, user_competencies)
            path["recommendation_score"] = score
            recommended.append(path)

    # Sort by recommendation score
    recommended.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return recommended[:5]  # Top 5 recommendations


def calculate_recommendation_score(path, user_competencies):
    """Calculate recommendation score for a training path"""
    score = 0

    # Base score for difficulty level alignment
    difficulty_scores = {"Beginner": 10, "Intermediate": 8, "Advanced": 6, "Expert": 4}
    score += difficulty_scores.get(path.difficulty_level, 5)

    # Bonus for shorter duration (more likely to complete)
    if path.estimated_duration_hours <= 5:
        score += 5
    elif path.estimated_duration_hours <= 10:
        score += 3

    # Consider user's existing competencies
    competency_levels = {"Expert": 4, "Advanced": 3, "Intermediate": 2, "Beginner": 1}
    avg_competency = sum([competency_levels.get(c.competency_level, 0) for c in user_competencies])
    avg_competency = avg_competency / len(user_competencies) if user_competencies else 1

    # Align with user's current level
    path_difficulty_level = difficulty_scores.get(path.difficulty_level, 5) / 2
    if abs(avg_competency - path_difficulty_level) <= 1:
        score += 10  # Good match

    return score
