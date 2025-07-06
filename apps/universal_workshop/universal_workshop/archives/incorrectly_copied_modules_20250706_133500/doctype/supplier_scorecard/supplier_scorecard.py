import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now, add_days


class SupplierScorecard(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate scorecard data"""
        self.validate_year()
        self.calculate_performance_metrics()
        self.calculate_overall_score()

    def before_save(self):
        """Set default values and fetch related data"""
        self.set_supplier_details()
        self.set_audit_trail()
        self.set_next_review_date()

    def validate_year(self):
        """Ensure evaluation year is valid"""
        current_year = getdate().year
        if self.year and (self.year > current_year + 1 or self.year < current_year - 5):
            frappe.throw(_("Evaluation year should be within last 5 years or next year"))

    def set_supplier_details(self):
        """Fetch and set supplier details"""
        if self.supplier:
            supplier = frappe.get_doc("Supplier", self.supplier)
            self.supplier_name = supplier.supplier_name
            # Set Arabic name if available
            if hasattr(supplier, "supplier_name_ar") and supplier.supplier_name_ar:
                self.supplier_name_ar = supplier.supplier_name_ar

    def set_audit_trail(self):
        """Set audit trail information"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = now()

        self.last_updated = now()

    def set_next_review_date(self):
        """Set next review date based on evaluation period"""
        if not self.next_review_date and self.evaluation_period:
            if self.evaluation_period == "Quarterly":
                self.next_review_date = add_days(getdate(), 90)
            elif self.evaluation_period == "Half-Yearly":
                self.next_review_date = add_days(getdate(), 180)
            else:  # Annually
                self.next_review_date = add_days(getdate(), 365)

    def calculate_performance_metrics(self):
        """Calculate delivery and other performance metrics"""
        # Calculate delivery performance
        if self.total_deliveries > 0:
            self.delivery_performance = (self.on_time_deliveries / self.total_deliveries) * 100
        else:
            self.delivery_performance = 0

        # Calculate average order value
        if self.total_deliveries > 0 and self.total_purchase_amount:
            self.average_order_value = self.total_purchase_amount / self.total_deliveries
        else:
            self.average_order_value = 0

    def calculate_overall_score(self):
        """Calculate overall supplier score (0-100)"""
        scores = []
        weights = []

        # Quality score (40% weight)
        if self.average_quality_score:
            scores.append(flt(self.average_quality_score))
            weights.append(40)

        # Delivery performance (30% weight)
        if self.delivery_performance:
            scores.append(flt(self.delivery_performance))
            weights.append(30)

        # Communication rating (15% weight)
        comm_score = self.get_rating_score(self.communication_rating)
        if comm_score:
            scores.append(comm_score)
            weights.append(15)

        # Technical support rating (15% weight)
        tech_score = self.get_rating_score(self.technical_support_rating)
        if tech_score:
            scores.append(tech_score)
            weights.append(15)

        # Calculate weighted average
        if scores and weights:
            self.overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            self.overall_score = 0

    def get_rating_score(self, rating):
        """Convert rating to numeric score"""
        rating_map = {"Excellent": 100, "Good": 80, "Average": 60, "Poor": 30}
        return rating_map.get(rating, 0)

    def update_quality_metrics(self, quality_score, passed):
        """Update quality metrics from quality inspection"""
        self.total_inspections += 1
        self.total_quality_score += flt(quality_score)

        if passed:
            self.passed_inspections += 1
        else:
            self.failed_inspections += 1

        # Recalculate averages
        self.average_quality_score = self.total_quality_score / self.total_inspections
        self.pass_rate = (self.passed_inspections / self.total_inspections) * 100

        # Update performance rating based on pass rate
        if self.pass_rate >= 95 and self.average_quality_score >= 90:
            self.performance_rating = "Excellent"
        elif self.pass_rate >= 85 and self.average_quality_score >= 80:
            self.performance_rating = "Good"
        elif self.pass_rate >= 70 and self.average_quality_score >= 70:
            self.performance_rating = "Satisfactory"
        else:
            self.performance_rating = "Needs Improvement"

        # Recalculate overall score
        self.calculate_overall_score()
        self.save()


@frappe.whitelist()
def get_supplier_scorecards(year=None, performance_rating=None):
    """Get supplier scorecards with filtering"""
    filters = {}

    if year:
        filters["year"] = year
    if performance_rating:
        filters["performance_rating"] = performance_rating

    scorecards = frappe.get_list(
        "Supplier Scorecard",
        filters=filters,
        fields=[
            "name",
            "supplier",
            "supplier_name",
            "supplier_name_ar",
            "year",
            "performance_rating",
            "overall_score",
            "pass_rate",
            "average_quality_score",
            "delivery_performance",
            "total_inspections",
            "total_deliveries",
            "risk_level",
            "next_review_date",
            "recommended_action",
        ],
        order_by="overall_score desc",
    )

    return scorecards


@frappe.whitelist()
def create_scorecard_from_supplier(supplier, year=None):
    """Create new scorecard for supplier"""
    if not year:
        year = getdate().year

    # Check if scorecard already exists
    existing = frappe.db.exists("Supplier Scorecard", f"{supplier}-{year}")
    if existing:
        return frappe.get_doc("Supplier Scorecard", existing)

    # Create new scorecard
    scorecard = frappe.new_doc("Supplier Scorecard")
    scorecard.supplier = supplier
    scorecard.year = year
    scorecard.evaluation_period = "Quarterly"
    scorecard.performance_rating = "Satisfactory"
    scorecard.risk_level = "Medium"

    # Initialize counters
    scorecard.total_inspections = 0
    scorecard.passed_inspections = 0
    scorecard.failed_inspections = 0
    scorecard.total_quality_score = 0
    scorecard.on_time_deliveries = 0
    scorecard.total_deliveries = 0
    scorecard.total_purchase_amount = 0

    scorecard.insert()
    return scorecard
