# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import json
import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now, today, add_days


class CustomerFeedback(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate feedback before saving"""
        self.validate_required_fields()
        self.validate_rating_values()
        self.validate_arabic_content()
        self.process_sentiment_analysis()
        
    def before_save(self):
        """Set default values before saving"""
        self.set_default_values()
        self.extract_keywords()
        self.determine_priority()
        
    def after_insert(self):
        """Post-creation actions"""
        self.send_acknowledgment()
        self.trigger_workflow_actions()
        
    def validate_required_fields(self):
        """Validate required fields for feedback"""
        if not self.feedback_title:
            frappe.throw(_("Feedback title is required"))
            
        if not self.customer:
            frappe.throw(_("Customer is required"))
            
        if not self.overall_rating or self.overall_rating < 1:
            frappe.throw(_("Overall rating is required and must be at least 1 star"))
            
        if not self.feedback_date:
            self.feedback_date = now()
            
    def validate_rating_values(self):
        """Validate all rating fields are within acceptable range (1-5)"""
        rating_fields = [
            'overall_rating', 'service_quality_rating', 'technician_rating',
            'facility_rating', 'communication_rating', 'value_rating'
        ]
        
        for field in rating_fields:
            rating_value = getattr(self, field, None)
            if rating_value and (rating_value < 1 or rating_value > 5):
                frappe.throw(_("Rating for {0} must be between 1 and 5").format(field))
                
    def validate_arabic_content(self):
        """Validate and enhance Arabic content"""
        # Auto-suggest Arabic translation if needed
        if self.feedback_title and not self.feedback_title_ar:
            self.suggest_arabic_translation()
            
        # Validate Arabic text format
        if self.feedback_comments_ar:
            self.validate_arabic_text(self.feedback_comments_ar)
            
        if self.improvement_suggestions_ar:
            self.validate_arabic_text(self.improvement_suggestions_ar)
            
    def suggest_arabic_translation(self):
        """Suggest Arabic translation for feedback title"""
        # Common translations for feedback titles
        translations = {
            'Service Feedback': 'تقييم الخدمة',
            'Excellent Service': 'خدمة ممتازة',
            'Good Experience': 'تجربة جيدة',
            'Poor Service': 'خدمة ضعيفة',
            'Workshop Review': 'تقييم الورشة',
            'Service Review': 'مراجعة الخدمة',
            'Quality Feedback': 'تقييم الجودة',
            'Customer Satisfaction': 'رضا العميل',
            'Complaint': 'شكوى',
            'Suggestion': 'اقتراح',
            'Compliment': 'إطراء'
        }
        
        # Try exact match first
        if self.feedback_title in translations:
            self.feedback_title_ar = translations[self.feedback_title]
        else:
            # Generate based on rating
            if self.overall_rating >= 4:
                self.feedback_title_ar = "تقييم إيجابي للخدمة"
            elif self.overall_rating >= 3:
                self.feedback_title_ar = "تقييم متوسط للخدمة"
            else:
                self.feedback_title_ar = "تقييم سلبي للخدمة"
                
    def validate_arabic_text(self, text):
        """Validate Arabic text format"""
        if text:
            # Check for proper Arabic characters
            arabic_pattern = re.compile(r'[\u0600-\u06FF]')
            if not arabic_pattern.search(text):
                # If no Arabic characters found, might be transliterated
                pass  # Allow mixed content
                
    def process_sentiment_analysis(self):
        """Analyze sentiment of feedback comments"""
        try:
            # Simple sentiment analysis based on rating and keywords
            sentiment_score = self.calculate_sentiment_score()
            
            if sentiment_score >= 4:
                self.sentiment_analysis = "Very Positive"
                self.emotion_score = flt(sentiment_score * 2, 2)  # Scale to 0-10
            elif sentiment_score >= 3:
                self.sentiment_analysis = "Positive"
                self.emotion_score = flt(sentiment_score * 1.8, 2)
            elif sentiment_score >= 2.5:
                self.sentiment_analysis = "Neutral"
                self.emotion_score = flt(sentiment_score * 1.5, 2)
            elif sentiment_score >= 2:
                self.sentiment_analysis = "Negative"
                self.emotion_score = flt(sentiment_score * 1.2, 2)
            else:
                self.sentiment_analysis = "Very Negative"
                self.emotion_score = flt(sentiment_score, 2)
                
            self.analytics_processed = 1
            
        except Exception as e:
            frappe.log_error(f"Sentiment analysis error: {e}")
            self.sentiment_analysis = "Neutral"
            self.emotion_score = 5.0
            
    def calculate_sentiment_score(self):
        """Calculate sentiment score based on ratings and content"""
        # Base score from overall rating
        score = flt(self.overall_rating or 3)
        
        # Adjust based on other ratings
        ratings = [
            self.service_quality_rating,
            self.technician_rating,
            self.facility_rating,
            self.communication_rating,
            self.value_rating
        ]
        
        valid_ratings = [r for r in ratings if r]
        if valid_ratings:
            avg_rating = sum(valid_ratings) / len(valid_ratings)
            score = (score + avg_rating) / 2
            
        # Analyze text content for sentiment keywords
        text_content = f"{self.feedback_comments or ''} {self.improvement_suggestions or ''}"
        
        positive_keywords = [
            'excellent', 'great', 'amazing', 'outstanding', 'perfect',
            'professional', 'satisfied', 'recommend', 'impressed',
            'ممتاز', 'رائع', 'مذهل', 'متميز', 'مثالي', 'محترف', 'راضي', 'أنصح'
        ]
        
        negative_keywords = [
            'terrible', 'awful', 'poor', 'disappointed', 'worst',
            'unprofessional', 'dissatisfied', 'complaint', 'problem',
            'فظيع', 'سيء', 'ضعيف', 'محبط', 'الأسوأ', 'غير محترف', 'غير راضي', 'شكوى', 'مشكلة'
        ]
        
        if text_content:
            text_lower = text_content.lower()
            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            negative_count = sum(1 for word in negative_keywords if word in text_lower)
            
            # Adjust score based on keyword sentiment
            sentiment_adjustment = (positive_count - negative_count) * 0.2
            score += sentiment_adjustment
            
        return max(1, min(5, score))  # Ensure score is between 1-5
        
    def extract_keywords(self):
        """Extract keywords from feedback comments"""
        try:
            text_content = f"{self.feedback_comments or ''} {self.improvement_suggestions or ''}"
            arabic_content = f"{self.feedback_comments_ar or ''} {self.improvement_suggestions_ar or ''}"
            
            # Extract English keywords
            english_keywords = self.extract_keywords_from_text(text_content)
            self.keywords_extracted = ", ".join(english_keywords[:10])  # Limit to 10 keywords
            
            # Extract Arabic keywords
            arabic_keywords = self.extract_keywords_from_text(arabic_content, is_arabic=True)
            self.keywords_extracted_ar = "، ".join(arabic_keywords[:10])  # Arabic comma separator
            
        except Exception as e:
            frappe.log_error(f"Keyword extraction error: {e}")
            
    def extract_keywords_from_text(self, text, is_arabic=False):
        """Extract meaningful keywords from text"""
        if not text:
            return []
            
        # Common stop words to exclude
        stop_words_en = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
            'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
            'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
            'just', 'don', 'should', 'now', 'was', 'were', 'been', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        stop_words_ar = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'بعد', 'قبل', 'عند', 'لدى',
            'هذا', 'هذه', 'ذلك', 'تلك', 'التي', 'الذي', 'التي', 'اللذان', 'اللتان',
            'الذين', 'اللاتي', 'اللواتي', 'ما', 'من', 'كيف', 'متى', 'أين', 'لماذا',
            'كل', 'بعض', 'جميع', 'كان', 'كانت', 'يكون', 'تكون', 'أن', 'إن', 'لكن',
            'لكن', 'غير', 'سوى', 'إلا', 'بل', 'لا', 'ولا', 'أم', 'أو', 'كذلك'
        }
        
        stop_words = stop_words_ar if is_arabic else stop_words_en
        
        # Simple tokenization and filtering
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = []
        
        for word in words:
            if (len(word) > 2 and  # Minimum word length
                word not in stop_words and  # Not a stop word
                not word.isdigit()):  # Not a number
                keywords.append(word)
                
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
                
        return unique_keywords
        
    def determine_priority(self):
        """Determine priority level based on feedback content and ratings"""
        if not hasattr(self, 'priority_level') or not self.priority_level:
            # Auto-determine priority
            if self.overall_rating <= 2:
                self.priority_level = "High"
                self.response_required = 1
            elif self.overall_rating <= 3:
                self.priority_level = "Medium"
                if self.feedback_type in ["Complaint", "Suggestion"]:
                    self.response_required = 1
            else:
                self.priority_level = "Low"
                
        # Check for urgent keywords
        urgent_keywords = [
            'urgent', 'immediate', 'emergency', 'serious', 'critical',
            'عاجل', 'فوري', 'طارئ', 'خطير', 'حرج'
        ]
        
        text_content = f"{self.feedback_comments or ''} {self.feedback_comments_ar or ''}"
        if any(keyword in text_content.lower() for keyword in urgent_keywords):
            self.priority_level = "Urgent"
            self.response_required = 1
            
    def set_default_values(self):
        """Set default values for feedback"""
        if not self.created_by:
            self.created_by = frappe.session.user
            
        if not self.feedback_status:
            self.feedback_status = "Draft"
            
        if not self.feedback_channel:
            self.feedback_channel = "Customer Portal"
            
        if not self.preferred_language:
            # Determine based on Arabic content
            if self.feedback_comments_ar or self.feedback_title_ar:
                self.preferred_language = "Arabic"
            else:
                self.preferred_language = "English"
                
        # Set device and browser info if available
        if hasattr(frappe.local, 'request') and frappe.local.request:
            user_agent = frappe.local.request.headers.get('User-Agent', '')
            self.browser_info = user_agent[:100]  # Limit length
            
            # Simple device detection
            if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                self.device_type = "Mobile"
            elif 'Tablet' in user_agent or 'iPad' in user_agent:
                self.device_type = "Tablet"
            else:
                self.device_type = "Desktop"
                
        # Set session info
        self.session_id = frappe.session.sid[:20] if frappe.session.sid else "unknown"
        
    def send_acknowledgment(self):
        """Send acknowledgment to customer"""
        try:
            if self.customer and self.feedback_status == "Submitted":
                customer_email = frappe.db.get_value("Customer", self.customer, "email_id")
                
                if customer_email:
                    subject = _("Feedback Received - {0}").format(self.feedback_title)
                    
                    # Create bilingual message
                    message_en = f"""
                    Dear Valued Customer,
                    
                    Thank you for your feedback titled "{self.feedback_title}".
                    
                    Your feedback is important to us and helps us improve our services.
                    Reference Number: {self.name}
                    Submitted Date: {self.feedback_date}
                    
                    We will review your feedback and respond within 24-48 hours if a response is required.
                    
                    Best regards,
                    Universal Workshop Team
                    """
                    
                    message_ar = f"""
                    عزيزنا العميل،
                    
                    شكراً لك على تقييمك بعنوان "{self.feedback_title_ar or self.feedback_title}".
                    
                    رأيك مهم بالنسبة لنا ويساعدنا على تحسين خدماتنا.
                    رقم المرجع: {self.name}
                    تاريخ الإرسال: {self.feedback_date}
                    
                    سنقوم بمراجعة تقييمك والرد عليك خلال 24-48 ساعة إذا كان الرد مطلوباً.
                    
                    مع أطيب التحيات،
                    فريق الورشة الشاملة
                    """
                    
                    # Send email based on preferred language
                    if self.preferred_language == "Arabic":
                        message = message_ar + "\n\n" + "="*50 + "\n\n" + message_en
                    else:
                        message = message_en + "\n\n" + "="*50 + "\n\n" + message_ar
                        
                    frappe.sendmail(
                        recipients=[customer_email],
                        subject=subject,
                        message=message
                    )
                    
                    self.notification_sent = 1
                    self.email_sent = 1
                    
        except Exception as e:
            frappe.log_error(f"Acknowledgment email error: {e}")
            
    def trigger_workflow_actions(self):
        """Trigger workflow actions based on feedback"""
        try:
            # Auto-submit positive feedback
            if self.overall_rating >= 4 and self.feedback_status == "Draft":
                self.feedback_status = "Submitted"
                
            # Auto-assign for review if negative
            if self.overall_rating <= 2:
                self.feedback_status = "In Review"
                self.response_required = 1
                
                # Notify management for critical feedback
                self.notify_management()
                
            # Update satisfaction trend
            self.update_satisfaction_trend()
            
        except Exception as e:
            frappe.log_error(f"Workflow trigger error: {e}")
            
    def notify_management(self):
        """Notify management of critical feedback"""
        try:
            # Get management users
            managers = frappe.get_list("User", 
                                     filters={"role_profile_name": ["in", ["Workshop Manager", "System Manager"]]},
                                     fields=["email"])
            
            if managers:
                recipient_emails = [m.email for m in managers]
                
                subject = f"Critical Feedback Alert - {self.feedback_title}"
                message = f"""
                Critical customer feedback received:
                
                Customer: {self.customer}
                Rating: {self.overall_rating}/5 stars
                Feedback: {self.feedback_comments}
                
                Priority: {self.priority_level}
                
                Please review and respond promptly.
                
                Reference: {self.name}
                """
                
                frappe.sendmail(
                    recipients=recipient_emails,
                    subject=subject,
                    message=message
                )
                
        except Exception as e:
            frappe.log_error(f"Management notification error: {e}")
            
    def update_satisfaction_trend(self):
        """Update customer satisfaction trend"""
        try:
            # Get recent feedback for this customer
            recent_feedback = frappe.get_list("Customer Feedback",
                                            filters={
                                                "customer": self.customer,
                                                "feedback_date": [">", add_days(today(), -90)]
                                            },
                                            fields=["overall_rating"],
                                            order_by="feedback_date desc",
                                            limit=5)
            
            if len(recent_feedback) >= 2:
                ratings = [f.overall_rating for f in recent_feedback]
                current_avg = sum(ratings[:3]) / min(3, len(ratings))  # Last 3 ratings
                previous_avg = sum(ratings[1:4]) / min(3, len(ratings[1:]))  # Previous 3 ratings
                
                if current_avg > previous_avg + 0.5:
                    self.satisfaction_trend = "Improving"
                elif current_avg < previous_avg - 0.5:
                    self.satisfaction_trend = "Declining"
                else:
                    self.satisfaction_trend = "Stable"
            else:
                self.satisfaction_trend = "Stable"
                
        except Exception as e:
            frappe.log_error(f"Satisfaction trend update error: {e}")
            self.satisfaction_trend = "Stable"
            
    def acknowledge_feedback(self, acknowledged_by=None):
        """Acknowledge feedback receipt"""
        if not acknowledged_by:
            acknowledged_by = frappe.session.user
            
        self.feedback_status = "Acknowledged"
        self.acknowledged_by = acknowledged_by
        self.acknowledged_date = now()
        self.save()
        
    def resolve_feedback(self, resolution_comments="", resolution_comments_ar=""):
        """Mark feedback as resolved"""
        self.feedback_status = "Resolved"
        self.resolved_by = frappe.session.user
        self.resolution_date = now()
        self.response_comments = resolution_comments
        self.response_comments_ar = resolution_comments_ar
        self.save()
        
        # Send resolution notification
        self.send_resolution_notification()
        
    def send_resolution_notification(self):
        """Send notification when feedback is resolved"""
        try:
            if self.customer:
                customer_email = frappe.db.get_value("Customer", self.customer, "email_id")
                
                if customer_email:
                    subject = _("Feedback Resolved - {0}").format(self.feedback_title)
                    
                    message = f"""
                    Dear Customer,
                    
                    Your feedback "{self.feedback_title}" has been resolved.
                    
                    Resolution: {self.response_comments}
                    Resolved by: {self.resolved_by}
                    Resolution Date: {self.resolution_date}
                    
                    Thank you for helping us improve our services.
                    
                    Best regards,
                    Universal Workshop Team
                    """
                    
                    frappe.sendmail(
                        recipients=[customer_email],
                        subject=subject,
                        message=message
                    )
                    
        except Exception as e:
            frappe.log_error(f"Resolution notification error: {e}")


# API Methods for Customer Portal and Analytics

@frappe.whitelist()
def submit_customer_feedback(customer, service_order, overall_rating, feedback_title,
                           feedback_comments="", feedback_type="Service Review"):
    """Submit feedback from customer portal"""
    try:
        feedback = frappe.new_doc("Customer Feedback")
        feedback.customer = customer
        feedback.service_order = service_order
        feedback.overall_rating = cint(overall_rating)
        feedback.feedback_title = feedback_title
        feedback.feedback_comments = feedback_comments
        feedback.feedback_type = feedback_type
        feedback.feedback_status = "Submitted"
        feedback.feedback_channel = "Customer Portal"
        
        feedback.insert(ignore_permissions=True)
        
        return {
            "status": "success",
            "message": _("Thank you for your feedback!"),
            "feedback_id": feedback.name
        }
        
    except Exception as e:
        frappe.log_error(f"Feedback submission error: {e}")
        return {
            "status": "error",
            "message": _("Failed to submit feedback. Please try again.")
        }


@frappe.whitelist()
def get_customer_feedback_summary(customer):
    """Get feedback summary for customer dashboard"""
    try:
        # Get recent feedback
        feedback_list = frappe.get_list("Customer Feedback",
                                      filters={"customer": customer},
                                      fields=["name", "feedback_title", "overall_rating", 
                                             "feedback_date", "feedback_status"],
                                      order_by="feedback_date desc",
                                      limit=10)
        
        # Calculate statistics
        if feedback_list:
            ratings = [f.overall_rating for f in feedback_list]
            avg_rating = sum(ratings) / len(ratings)
            
            summary = {
                "total_feedback": len(feedback_list),
                "average_rating": round(avg_rating, 1),
                "recent_feedback": feedback_list,
                "satisfaction_level": "High" if avg_rating >= 4 else "Medium" if avg_rating >= 3 else "Low"
            }
        else:
            summary = {
                "total_feedback": 0,
                "average_rating": 0,
                "recent_feedback": [],
                "satisfaction_level": "No Data"
            }
            
        return summary
        
    except Exception as e:
        frappe.log_error(f"Feedback summary error: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def get_feedback_analytics(date_range="30"):
    """Get feedback analytics for management dashboard"""
    try:
        days = cint(date_range)
        from_date = add_days(today(), -days)
        
        # Get feedback data
        feedback_data = frappe.db.sql("""
            SELECT 
                overall_rating,
                feedback_type,
                sentiment_analysis,
                DATE(feedback_date) as feedback_date,
                customer
            FROM `tabCustomer Feedback`
            WHERE feedback_date >= %s
            AND docstatus != 2
        """, [from_date], as_dict=True)
        
        if not feedback_data:
            return {"message": "No feedback data available"}
            
        # Calculate analytics
        total_feedback = len(feedback_data)
        avg_rating = sum(f.overall_rating for f in feedback_data) / total_feedback
        
        # Rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[f"{i}_star"] = len([f for f in feedback_data if f.overall_rating == i])
            
        # Sentiment distribution
        sentiment_dist = {}
        sentiments = ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]
        for sentiment in sentiments:
            sentiment_dist[sentiment.lower().replace(" ", "_")] = len([f for f in feedback_data if f.sentiment_analysis == sentiment])
            
        # Feedback type distribution
        type_dist = {}
        for feedback in feedback_data:
            feedback_type = feedback.feedback_type or "Unknown"
            type_dist[feedback_type] = type_dist.get(feedback_type, 0) + 1
            
        # Daily trend
        daily_trend = {}
        for feedback in feedback_data:
            date_str = str(feedback.feedback_date)
            if date_str not in daily_trend:
                daily_trend[date_str] = {"count": 0, "total_rating": 0}
            daily_trend[date_str]["count"] += 1
            daily_trend[date_str]["total_rating"] += feedback.overall_rating
            
        # Calculate daily averages
        for date_str in daily_trend:
            daily_data = daily_trend[date_str]
            daily_data["avg_rating"] = daily_data["total_rating"] / daily_data["count"]
            
        analytics = {
            "summary": {
                "total_feedback": total_feedback,
                "average_rating": round(avg_rating, 2),
                "date_range": f"{from_date} to {today()}"
            },
            "rating_distribution": rating_dist,
            "sentiment_distribution": sentiment_dist,
            "feedback_type_distribution": type_dist,
            "daily_trend": daily_trend
        }
        
        return analytics
        
    except Exception as e:
        frappe.log_error(f"Feedback analytics error: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def acknowledge_feedback(feedback_id):
    """Acknowledge feedback (for management)"""
    try:
        feedback = frappe.get_doc("Customer Feedback", feedback_id)
        feedback.acknowledge_feedback()
        
        return {
            "status": "success",
            "message": _("Feedback acknowledged successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Feedback acknowledgment error: {e}")
        return {
            "status": "error",
            "message": _("Failed to acknowledge feedback")
        }


@frappe.whitelist()
def resolve_feedback(feedback_id, resolution_comments="", resolution_comments_ar=""):
    """Resolve feedback with comments"""
    try:
        feedback = frappe.get_doc("Customer Feedback", feedback_id)
        feedback.resolve_feedback(resolution_comments, resolution_comments_ar)
        
        return {
            "status": "success",
            "message": _("Feedback resolved successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Feedback resolution error: {e}")
        return {
            "status": "error",
            "message": _("Failed to resolve feedback")
        }
