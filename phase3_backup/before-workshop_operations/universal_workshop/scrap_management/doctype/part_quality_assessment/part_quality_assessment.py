# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import re
from datetime import datetime, timedelta
import json


class PartQualityAssessment(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields
    
    def validate(self):
        """Validate part quality assessment before saving"""
        self.validate_inspector_qualification()
        self.validate_arabic_names()
        self.validate_pricing_logic()
        self.validate_grading_criteria()
        self.validate_required_photos()
        self.calculate_assessment_metrics()
        
    def before_save(self):
        """Set default values and auto-calculate fields before saving"""
        self.set_defaults()
        self.auto_generate_assessment_id()
        self.update_assessment_status()
        
    def after_insert(self):
        """After inserting new assessment"""
        self.log_assessment_activity("Assessment Created")
        
    def set_defaults(self):
        """Set default values for new assessments"""
        if not self.assessment_date:
            self.assessment_date = frappe.utils.today()
            
        if not self.inspector_employee:
            self.inspector_employee = frappe.session.user
            
        if not self.assessment_status:
            self.assessment_status = "Draft"
            
        if not self.created_by:
            self.created_by = frappe.session.user
            
        if not self.created_date:
            self.created_date = frappe.utils.now()
    
    def auto_generate_assessment_id(self):
        """Generate assessment ID with format: PQA-YYYY-####"""
        if not self.assessment_id:
            year = datetime.now().year
            
            # Get last assessment number for current year
            last_assessment = frappe.db.sql("""
                SELECT assessment_id FROM `tabPart Quality Assessment`
                WHERE assessment_id LIKE 'PQA-%s-%%'
                ORDER BY creation DESC LIMIT 1
            """.format(year))
            
            if last_assessment:
                last_num = int(last_assessment[0][0].split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            self.assessment_id = f"PQA-{year}-{new_num:04d}"
    
    def validate_inspector_qualification(self):
        """Validate inspector qualification against part category requirements"""
        if not self.inspector_qualification:
            frappe.throw(_("Inspector qualification is required"))
            
        # Safety critical parts require advanced qualification
        safety_critical_parts = ['Brakes', 'Suspension', 'Safety Systems', 'Electronics']
        
        if self.part_category in safety_critical_parts:
            required_qualifications = ['Advanced', 'Certified Expert']
            if self.inspector_qualification not in required_qualifications:
                frappe.throw(_(
                    "Part category '{0}' requires Advanced or Certified Expert inspector qualification"
                ).format(self.part_category))
    
    def validate_arabic_names(self):
        """Validate Arabic name fields"""
        if self.assessment_title_ar:
            if not self.is_arabic_text(self.assessment_title_ar):
                frappe.throw(_("Assessment title (Arabic) must contain Arabic characters"))
                
        if self.part_name_ar:
            if not self.is_arabic_text(self.part_name_ar):
                frappe.throw(_("Part name (Arabic) must contain Arabic characters"))
    
    def validate_pricing_logic(self):
        """Validate pricing and cost logic"""
        if self.suggested_selling_price and self.minimum_acceptable_price:
            if float(self.minimum_acceptable_price) > float(self.suggested_selling_price):
                frappe.throw(_("Minimum acceptable price cannot exceed suggested selling price"))
                
        if self.refurbishment_required and self.estimated_refurbishment_cost and self.suggested_selling_price:
            total_cost = float(self.estimated_refurbishment_cost or 0)
            selling_price = float(self.suggested_selling_price or 0)
            
            if total_cost > selling_price:
                frappe.msgprint(_(
                    "Warning: Refurbishment cost ({0} OMR) exceeds suggested selling price ({1} OMR)"
                ).format(total_cost, selling_price), indicator='orange')
    
    def validate_grading_criteria(self):
        """Validate grading against assessment criteria"""
        # Ensure grade matches assessment criteria
        if self.final_grade and self.overall_visual_condition:
            grade_condition_mapping = {
                'A': ['Excellent'],
                'B': ['Excellent', 'Very Good'],
                'C': ['Very Good', 'Good'],
                'D': ['Good', 'Fair'],
                'E': ['Fair', 'Poor'],
                'F': ['Poor', 'Very Poor']
            }
            
            valid_conditions = grade_condition_mapping.get(self.final_grade, [])
            if self.overall_visual_condition not in valid_conditions:
                frappe.msgprint(_(
                    "Warning: Final grade '{0}' may not match visual condition '{1}'"
                ).format(self.final_grade, self.overall_visual_condition), indicator='orange')
        
        # Second opinion requirements
        if self.inspector_confidence_level == 'Low' and not self.requires_second_opinion:
            frappe.msgprint(_(
                "Recommendation: Consider requiring second opinion for low confidence assessments"
            ), indicator='blue')
    
    def validate_required_photos(self):
        """Validate required photo documentation"""
        required_photos = ['overview_photo', 'detail_photo_1']
        
        for photo_field in required_photos:
            if not getattr(self, photo_field, None):
                frappe.msgprint(_(
                    "Warning: {0} is strongly recommended for complete assessment"
                ).format(photo_field.replace('_', ' ').title()), indicator='orange')
        
        # Additional requirements for certain grades
        if self.final_grade in ['A', 'B'] and not self.serial_number_photo:
            frappe.msgprint(_(
                "High-grade parts should include serial number photo for verification"
            ), indicator='blue')
    
    def calculate_assessment_metrics(self):
        """Calculate assessment score and confidence metrics"""
        score = 0
        weight_total = 0
        
        # Visual assessment score (30% weight)
        visual_scores = {
            'Excellent': 10, 'Very Good': 8, 'Good': 6,
            'Fair': 4, 'Poor': 2, 'Very Poor': 1
        }
        if self.overall_visual_condition:
            score += (visual_scores.get(self.overall_visual_condition, 0)) * 0.3
            weight_total += 0.3
        
        # Functional assessment score (40% weight)
        if self.functional_test_performed:
            functional_scores = {
                'Fully Functional': 10, 'Mostly Functional': 7,
                'Partially Functional': 4, 'Non-Functional': 1, 'Not Testable': 5
            }
            if self.operational_status:
                score += (functional_scores.get(self.operational_status, 0)) * 0.4
                weight_total += 0.4
        
        # Safety compliance score (20% weight)
        safety_scores = {
            'Compliant': 10, 'Minor Issues': 6,
            'Major Issues': 3, 'Non-Compliant': 1, 'Unknown': 5
        }
        if self.safety_compliance:
            score += (safety_scores.get(self.safety_compliance, 0)) * 0.2
            weight_total += 0.2
        
        # Market demand score (10% weight)
        demand_scores = {
            'Very High': 10, 'High': 8, 'Medium': 6,
            'Low': 4, 'Very Low': 2
        }
        if self.market_demand_assessment:
            score += (demand_scores.get(self.market_demand_assessment, 0)) * 0.1
            weight_total += 0.1
        
        # Calculate final score
        if weight_total > 0:
            self.assessment_score = round((score / weight_total), 2)
        else:
            self.assessment_score = 0
    
    def update_assessment_status(self):
        """Update assessment status based on completion criteria"""
        required_fields = [
            'part_name', 'part_category', 'overall_visual_condition',
            'preliminary_grade'
        ]
        
        all_required_complete = all(getattr(self, field, None) for field in required_fields)
        
        if all_required_complete and self.assessment_status == 'Draft':
            self.assessment_status = 'In Progress'
            
        if self.final_grade and self.grade_justification and all_required_complete:
            self.assessment_status = 'Completed'
    
    @frappe.whitelist()
    def approve_assessment(self, approver_notes=None):
        """Approve the assessment"""
        if self.assessment_status != 'Completed':
            frappe.throw(_("Only completed assessments can be approved"))
            
        self.assessment_approved = 1
        self.approved_by = frappe.session.user
        self.approval_date = frappe.utils.now()
        
        if approver_notes:
            self.approval_notes = approver_notes
            
        self.save()
        self.log_assessment_activity("Assessment Approved")
        
        frappe.msgprint(_("Assessment has been approved successfully"))
        return True
    
    @frappe.whitelist()
    def reject_assessment(self, rejection_notes):
        """Reject the assessment"""
        if not rejection_notes:
            frappe.throw(_("Rejection notes are required"))
            
        self.assessment_status = 'Rejected'
        self.approval_notes = rejection_notes
        self.approved_by = frappe.session.user
        self.approval_date = frappe.utils.now()
        
        self.save()
        self.log_assessment_activity(f"Assessment Rejected: {rejection_notes}")
        
        frappe.msgprint(_("Assessment has been rejected"))
        return True
    
    @frappe.whitelist()
    def generate_assessment_report(self):
        """Generate comprehensive assessment report"""
        report_data = {
            'assessment_id': self.assessment_id,
            'assessment_title': self.assessment_title,
            'generated_on': frappe.utils.now_datetime().strftime('%Y-%m-%d %H:%M:%S'),
            
            'part_information': {
                'name': self.part_name,
                'name_ar': self.part_name_ar or '',
                'category': self.part_category,
                'vehicle_make': self.vehicle_make or '',
                'vehicle_model': self.vehicle_model or '',
                'vehicle_year': self.vehicle_year or '',
                'vin': self.vin_number or ''
            },
            
            'assessment_details': {
                'inspector': self.inspector_employee,
                'qualification': self.inspector_qualification,
                'assessment_date': self.assessment_date,
                'confidence_level': self.inspector_confidence_level
            },
            
            'visual_assessment': {
                'overall_condition': self.overall_visual_condition,
                'wear_level': self.wear_level or '',
                'damage_level': self.damage_level or '',
                'surface_quality': self.surface_quality or '',
                'notes': self.visual_notes or ''
            },
            
            'functional_assessment': {
                'test_performed': self.functional_test_performed,
                'operational_status': self.operational_status or '',
                'performance_rating': self.performance_rating or '',
                'electrical_continuity': self.electrical_continuity or '',
                'notes': self.functional_notes or ''
            },
            
            'grading': {
                'preliminary_grade': self.preliminary_grade,
                'final_grade': self.final_grade,
                'confidence_level': self.inspector_confidence_level,
                'justification': self.grade_justification or '',
                'second_opinion_required': self.requires_second_opinion
            },
            
            'market_analysis': {
                'demand_assessment': self.market_demand_assessment,
                'suggested_price': self.suggested_selling_price or 0,
                'minimum_price': self.minimum_acceptable_price or 0,
                'time_to_sell': self.time_to_sell_estimate or '',
                'notes': self.market_notes or ''
            },
            
            'photos': {
                'overview': self.overview_photo or '',
                'detail_1': self.detail_photo_1 or '',
                'detail_2': self.detail_photo_2 or '',
                'detail_3': self.detail_photo_3 or '',
                'detail_4': self.detail_photo_4 or '',
                'serial_number': self.serial_number_photo or '',
                'damage_1': self.damage_photo_1 or '',
                'damage_2': self.damage_photo_2 or '',
                'test_result': self.test_result_photo or '',
                'packaging': self.packaging_photo or ''
            },
            
            'assessment_score': self.assessment_score or 0,
            'approval_status': {
                'approved': self.assessment_approved,
                'approved_by': self.approved_by or '',
                'approval_date': self.approval_date or '',
                'notes': self.approval_notes or ''
            }
        }
        
        return report_data
    
    def calculate_roi_projection(self):
        """Calculate ROI projection for the assessed part"""
        if not (self.suggested_selling_price and self.acquisition_cost):
            return None
            
        selling_price = float(self.suggested_selling_price)
        acquisition_cost = float(self.acquisition_cost or 0)
        refurbishment_cost = float(self.estimated_refurbishment_cost or 0)
        
        total_cost = acquisition_cost + refurbishment_cost
        gross_profit = selling_price - total_cost
        
        if total_cost > 0:
            roi_percentage = (gross_profit / total_cost) * 100
        else:
            roi_percentage = 0
            
        return {
            'selling_price': selling_price,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'roi_percentage': round(roi_percentage, 2)
        }
    
    def get_comparable_assessments(self):
        """Get similar part assessments for comparison"""
        filters = {
            'part_category': self.part_category,
            'vehicle_make': self.vehicle_make,
            'assessment_approved': 1,
            'name': ('!=', self.name)
        }
        
        similar_assessments = frappe.get_list(
            'Part Quality Assessment',
            filters=filters,
            fields=[
                'name', 'assessment_id', 'part_name', 'final_grade',
                'suggested_selling_price', 'assessment_score', 'assessment_date'
            ],
            order_by='assessment_date desc',
            limit=10
        )
        
        return similar_assessments
    
    def log_assessment_activity(self, activity_description):
        """Log assessment activity for audit trail"""
        try:
            activity_log = frappe.new_doc('Activity Log')
            activity_log.subject = f"Part Quality Assessment: {activity_description}"
            activity_log.content = json.dumps({
                'assessment_id': self.assessment_id,
                'part_name': self.part_name,
                'activity': activity_description,
                'user': frappe.session.user,
                'timestamp': frappe.utils.now()
            })
            activity_log.communication_date = frappe.utils.now()
            activity_log.reference_doctype = 'Part Quality Assessment'
            activity_log.reference_name = self.name
            activity_log.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log assessment activity: {e}")
    
    def is_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
        return bool(arabic_pattern.search(text))
    
    def get_dashboard_data(self):
        """Get data for assessment dashboard"""
        return {
            'assessment_id': self.assessment_id,
            'part_name': self.part_name,
            'final_grade': self.final_grade,
            'assessment_score': self.assessment_score,
            'market_value': self.suggested_selling_price,
            'status': self.assessment_status,
            'approved': self.assessment_approved
        }


@frappe.whitelist()
def get_inspector_qualifications():
    """Get list of available inspector qualifications"""
    return [
        'Basic',
        'Intermediate', 
        'Advanced',
        'Certified Expert'
    ]


@frappe.whitelist()
def get_part_categories():
    """Get list of available part categories"""
    return [
        'Engine',
        'Transmission',
        'Brakes',
        'Suspension',
        'Electrical',
        'Electronics',
        'Body',
        'Interior',
        'Safety Systems',
        'Exhaust',
        'Cooling',
        'Fuel System',
        'Steering',
        'Wheels & Tires',
        'Lighting',
        'Other'
    ]


@frappe.whitelist()
def get_grade_recommendations(part_category, visual_condition, functional_status):
    """Get grade recommendations based on assessment criteria"""
    
    # Base grade mapping from visual condition
    visual_grade_map = {
        'Excellent': 'A',
        'Very Good': 'B',
        'Good': 'C', 
        'Fair': 'D',
        'Poor': 'E',
        'Very Poor': 'F'
    }
    
    base_grade = visual_grade_map.get(visual_condition, 'F')
    
    # Adjust based on functional status
    if functional_status == 'Non-Functional':
        # Downgrade by 2 levels for non-functional parts
        grade_sequence = ['A', 'B', 'C', 'D', 'E', 'F']
        current_index = grade_sequence.index(base_grade)
        adjusted_index = min(current_index + 2, len(grade_sequence) - 1)
        recommended_grade = grade_sequence[adjusted_index]
    elif functional_status == 'Partially Functional':
        # Downgrade by 1 level
        grade_sequence = ['A', 'B', 'C', 'D', 'E', 'F']
        current_index = grade_sequence.index(base_grade)
        adjusted_index = min(current_index + 1, len(grade_sequence) - 1)
        recommended_grade = grade_sequence[adjusted_index]
    else:
        recommended_grade = base_grade
    
    # Safety-critical parts have stricter requirements
    safety_critical = part_category in ['Brakes', 'Suspension', 'Safety Systems']
    
    return {
        'recommended_grade': recommended_grade,
        'safety_critical': safety_critical,
        'reasoning': f"Based on {visual_condition} visual condition and {functional_status} functional status"
    }


@frappe.whitelist()
def bulk_approve_assessments(assessment_names, approver_notes=""):
    """Bulk approve multiple assessments"""
    approved_count = 0
    failed_assessments = []
    
    for assessment_name in assessment_names:
        try:
            assessment = frappe.get_doc('Part Quality Assessment', assessment_name)
            assessment.approve_assessment(approver_notes)
            approved_count += 1
        except Exception as e:
            failed_assessments.append({
                'name': assessment_name,
                'error': str(e)
            })
    
    return {
        'approved_count': approved_count,
        'failed_assessments': failed_assessments,
        'total_processed': len(assessment_names)
    }
