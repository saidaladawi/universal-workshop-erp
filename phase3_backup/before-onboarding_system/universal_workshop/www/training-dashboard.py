import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime
import json


def get_context(context):
    """Get context for training dashboard page"""
    context.no_cache = 1

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to access the training dashboard"))

    # Get user dashboard data
    try:
        dashboard_data = get_user_dashboard_data()
        context.update(dashboard_data)

        # Add page metadata
        context.title = _("Training Dashboard")
        context.show_sidebar = True
        context.hide_login = True

    except Exception as e:
        frappe.log_error(f"Training Dashboard Error: {str(e)}")
        context.error_message = _("Unable to load dashboard data. Please try again later.")


def get_user_dashboard_data():
    """Get comprehensive training dashboard data for current user"""
    user = frappe.session.user

    # Get user's training progress records
    progress_records = frappe.get_all(
        'Training Progress',
        filters={'user': user},
        fields=[
            'name', 'training_module', 'module_title', 'status',
            'progress_percentage', 'competency_level', 'quiz_score',
            'certification_issued', 'started_on', 'completed_on',
            'next_review_date', 'time_spent_minutes'
        ],
        order_by='completed_on desc, started_on desc'
    )

    # Get user's certifications
    certifications = frappe.get_all(
        'Training Certification',
        filters={'user': user},
        fields=[
            'name', 'certificate_number', 'training_module', 'module_title',
            'competency_level', 'quiz_score', 'issued_on', 'valid_until',
            'verification_code', 'certificate_file'
        ],
        order_by='issued_on desc'
    )

    # Calculate summary statistics
    total_modules = len(progress_records)
    completed_modules = len([r for r in progress_records if r.status == 'Completed'])
    in_progress_modules = len([r for r in progress_records if r.status == 'In Progress'])
    total_certifications = len(certifications)

    # Calculate competency distribution
    competency_stats = {}
    for record in progress_records:
        level = record.competency_level or 'Not Assessed'
        competency_stats[level] = competency_stats.get(level, 0) + 1

    # Get upcoming review dates
    upcoming_reviews = [
        r for r in progress_records
        if r.next_review_date and get_datetime(r.next_review_date) > get_datetime(nowdate())
    ]

    # Get overdue training (reviews past due)
    overdue_training = [
        r for r in progress_records
        if r.next_review_date and get_datetime(r.next_review_date) < get_datetime(nowdate())
    ]

    # Calculate total training time
    total_time_minutes = sum([r.time_spent_minutes or 0 for r in progress_records])
    total_time_hours = round(total_time_minutes / 60, 1) if total_time_minutes > 0 else 0

    # Get skill gaps and recommendations
    skill_gaps = get_skill_gap_recommendations(user)

    return {
        'user': user,
        'progress_records': progress_records,
        'certifications': certifications,
        'summary_stats': {
            'total_modules': total_modules,
            'completed_modules': completed_modules,
            'in_progress_modules': in_progress_modules,
            'completion_rate': round((completed_modules / total_modules * 100), 1) if total_modules > 0 else 0,
            'total_certifications': total_certifications,
            'total_training_hours': total_time_hours
        },
        'competency_stats': competency_stats,
        'upcoming_reviews': upcoming_reviews[:5],  # Next 5 reviews
        'overdue_training': overdue_training,
        'skill_gaps': skill_gaps,
        'dashboard_data_json': json.dumps({
            'competency_stats': competency_stats,
            'progress_records': progress_records,
            'summary_stats': {
                'total_modules': total_modules,
                'completed_modules': completed_modules,
                'in_progress_modules': in_progress_modules,
                'completion_rate': round((completed_modules / total_modules * 100), 1) if total_modules > 0 else 0
            }
        })
    }


def get_skill_gap_recommendations(user):
    """Get skill gap analysis and training recommendations"""
    try:
        # Get user's current competency levels
        user_competencies = frappe.get_all(
            'Training Progress',
            filters={'user': user, 'status': 'Completed'},
            fields=['training_module', 'competency_level'],
            group_by='training_module'
        )

        # Get all available training modules
        all_modules = frappe.get_all(
            'Training Module',
            filters={'is_active': 1},
            fields=['name', 'title', 'category', 'difficulty_level', 'prerequisites']
        )

        # Identify modules not yet taken
        completed_modules = [comp.training_module for comp in user_competencies]
        recommended_modules = [
            module for module in all_modules
            if module.name not in completed_modules
        ]

        # Sort by difficulty level (easier first)
        difficulty_order = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'Expert': 4}
        recommended_modules.sort(
            key=lambda x: difficulty_order.get(x.difficulty_level or 'Beginner', 1)
        )

        return recommended_modules[:6]  # Top 6 recommendations

    except Exception as e:
        frappe.log_error(f"Skill gap analysis error: {str(e)}")
        return []


@frappe.whitelist()
def get_progress_chart_data():
    """API endpoint for progress chart data"""
    user = frappe.session.user

    # Get monthly progress data for the last 12 months
    from frappe.utils import add_months

    chart_data = {
        'labels': [],
        'completed': [],
        'in_progress': []
    }

    current_date = nowdate()

    for i in range(12, 0, -1):
        month_date = add_months(current_date, -i)
        month_name = get_datetime(month_date).strftime('%b %Y')
        chart_data['labels'].append(month_name)

        # Count modules completed in this month
        completed_count = frappe.db.count(
            'Training Progress',
            filters={
                'user': user,
                'status': 'Completed',
                'completed_on': ['between', [month_date, add_months(month_date, 1)]]
            }
        )

        # Count modules started in this month
        started_count = frappe.db.count(
            'Training Progress',
            filters={
                'user': user,
                'started_on': ['between', [month_date, add_months(month_date, 1)]]
            }
        )

        chart_data['completed'].append(completed_count)
        chart_data['in_progress'].append(started_count)

    return chart_data


@frappe.whitelist()
def download_certificate(certification_name):
    """Download certificate PDF"""
    cert = frappe.get_doc('Training Certification', certification_name)

    # Verify user has access to this certificate
    if cert.user != frappe.session.user:
        frappe.throw(_("You don't have permission to download this certificate"))

    if cert.certificate_file:
        return {
            'file_url': cert.certificate_file,
            'file_name': f"Certificate_{cert.certificate_number}.pdf"
        }
    else:
        frappe.throw(_("Certificate file not found"))
