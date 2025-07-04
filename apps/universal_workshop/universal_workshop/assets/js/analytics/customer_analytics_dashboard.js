// Universal Workshop - Customer Analytics Dashboard JavaScript
// Arabic/RTL Support and Interactive Charts

class CustomerAnalyticsDashboard {
    constructor(options = {}) {
        this.options = {
            isArabic: options.isArabic || false,
            textDirection: options.textDirection || 'ltr',
            dateRange: 30,
            refreshInterval: 300000, // 5 minutes
            ...options
        };
        
        this.charts = {};
        this.data = {};
        this.refreshTimer = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.applyLocalization();
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-analytics')?.addEventListener('click', () => {
            this.loadDashboard();
        });
        
        // Date range filters
        document.querySelectorAll('.date-filter').forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                const days = parseInt(e.target.dataset.days);
                this.setDateRange(days);
            });
        });
        
        // Auto-refresh
        this.startAutoRefresh();
    }
    
    applyLocalization() {
        if (this.options.isArabic) {
            document.body.classList.add('arabic-layout');
            
            // Apply Arabic number formatting
            this.formatNumbers = this.formatArabicNumbers;
        } else {
            this.formatNumbers = this.formatEnglishNumbers;
        }
    }
    
    async loadDashboard() {
        try {
            this.showLoading();
            
            // Load analytics data
            const [summaryData, dashboardData] = await Promise.all([
                this.fetchAnalyticsSummary(),
                this.fetchDashboardData()
            ]);
            
            this.data.summary = summaryData;
            this.data.dashboard = dashboardData;
            
            // Update UI components
            this.updateSummaryCards();
            this.renderCharts();
            this.updateTables();
            
            this.showContent();
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showError(error.message);
        }
    }
    
    async fetchAnalyticsSummary() {
        const response = await frappe.call({
            method: 'universal_workshop.customer_management.doctype.customer_analytics.customer_analytics.get_customer_analytics_summary',
            args: {
                date_range: this.options.dateRange.toString()
            }
        });
        
        if (!response.message.success) {
            throw new Error(response.message.error || 'Failed to load analytics summary');
        }
        
        return response.message;
    }
    
    async fetchDashboardData() {
        const response = await frappe.call({
            method: 'universal_workshop.customer_management.customer_api.get_customer_dashboard_data',
            args: {
                date_range: this.options.dateRange.toString()
            }
        });
        
        if (!response.message.success) {
            throw new Error(response.message.error || 'Failed to load dashboard data');
        }
        
        return response.message;
    }
    
    updateSummaryCards() {
        const summary = this.data.summary?.summary || {};
        
        document.getElementById('total-customers').textContent = 
            this.formatNumbers(summary.total_customers || 0);
        
        document.getElementById('average-clv').textContent = 
            this.formatCurrency(summary.average_clv || 0);
        
        document.getElementById('average-retention').textContent = 
            this.formatPercentage(summary.average_retention || 0);
        
        document.getElementById('at-risk-count').textContent = 
            this.formatNumbers(summary.at_risk_count || 0);
    }
    
    renderCharts() {
        this.renderCLVTrendsChart();
        this.renderSegmentDistributionChart();
        this.renderRetentionCohortChart();
        this.renderServicePatternsChart();
    }
    
    renderCLVTrendsChart() {
        const container = document.getElementById('clv-trends-chart');
        if (!container) return;
        
        // Generate sample CLV trend data (replace with real data)
        const data = this.generateCLVTrendsData();
        
        this.charts.clvTrends = new frappe.Chart(container, {
            title: this.options.isArabic ? 'اتجاه قيمة العميل' : 'CLV Trends',
            data: data,
            type: 'line',
            height: 280,
            colors: ['#667eea', '#764ba2'],
            axisOptions: {
                xAxisMode: 'tick',
                xIsSeries: true
            },
            tooltipOptions: {
                formatTooltipX: d => this.formatDate(d),
                formatTooltipY: d => this.formatCurrency(d)
            }
        });
    }
    
    renderSegmentDistributionChart() {
        const container = document.getElementById('segments-distribution-chart');
        if (!container) return;
        
        const segmentData = this.data.summary?.segment_distribution || {};
        
        const data = {
            labels: Object.keys(segmentData).map(key => 
                this.translateSegment(key)
            ),
            datasets: [{
                values: Object.values(segmentData)
            }]
        };
        
        this.charts.segmentDistribution = new frappe.Chart(container, {
            title: this.options.isArabic ? 'توزيع شرائح العملاء' : 'Customer Segments',
            data: data,
            type: 'pie',
            height: 280,
            colors: ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#e67e22', '#95a5a6']
        });
    }
    
    renderRetentionCohortChart() {
        const container = document.getElementById('retention-cohort-chart');
        if (!container) return;
        
        // Generate retention cohort data
        const data = this.generateRetentionCohortData();
        
        this.charts.retentionCohort = new frappe.Chart(container, {
            title: this.options.isArabic ? 'تحليل مجموعات الاحتفاظ' : 'Retention Cohorts',
            data: data,
            type: 'bar',
            height: 280,
            colors: ['#2ecc71', '#3498db', '#f39c12', '#e74c3c'],
            isNavigable: false,
            axisOptions: {
                xAxisMode: 'tick'
            }
        });
    }
    
    renderServicePatternsChart() {
        const container = document.getElementById('service-patterns-chart');
        if (!container) return;
        
        // Generate service patterns heatmap data
        const data = this.generateServicePatternsData();
        
        this.charts.servicePatterns = new frappe.Chart(container, {
            title: this.options.isArabic ? 'أنماط الخدمة' : 'Service Patterns',
            data: data,
            type: 'heatmap',
            height: 280,
            discreteDomains: 1,
            colors: ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
        });
    }
    
    updateTables() {
        this.updateTopCustomersTable();
        this.updateAtRiskCustomersTable();
    }
    
    updateTopCustomersTable() {
        const tableBody = document.querySelector('#top-customers-table tbody');
        if (!tableBody) return;
        
        const topCustomers = this.data.summary?.top_customers || [];
        
        tableBody.innerHTML = topCustomers.map(customer => `
            <tr>
                <td>
                    <strong>${this.getCustomerName(customer)}</strong>
                </td>
                <td>${this.formatCurrency(customer.lifetime_value || 0)}</td>
                <td>
                    <span class="badge badge-${this.getSegmentClass(customer.segment)}">
                        ${this.translateSegment(customer.segment)}
                    </span>
                </td>
                <td>${this.formatNumbers(customer.total_orders || 0)}</td>
            </tr>
        `).join('');
    }
    
    updateAtRiskCustomersTable() {
        const tableBody = document.querySelector('#at-risk-customers-table tbody');
        if (!tableBody) return;
        
        const atRiskCustomers = this.data.summary?.at_risk_customers || [];
        
        tableBody.innerHTML = atRiskCustomers.map(customer => `
            <tr>
                <td>
                    <strong>${this.getCustomerName(customer)}</strong>
                </td>
                <td>
                    <span class="badge bg-warning">
                        ${this.formatPercentage(customer.churn_probability || 0)}
                    </span>
                </td>
                <td>${this.formatDate(customer.last_service_date)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="CustomerAnalyticsDashboard.contactCustomer('${customer.customer}')">
                        ${this.options.isArabic ? 'اتصال' : 'Contact'}
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    // Utility Methods
    getCustomerName(customer) {
        if (this.options.isArabic && customer.customer_name_ar) {
            return customer.customer_name_ar;
        }
        return customer.customer_name || customer.name;
    }
    
    translateSegment(segment) {
        if (!this.options.isArabic) return segment;
        
        const translations = {
            'VIP': 'عميل مميز',
            'High Value': 'عالي القيمة',
            'Regular': 'عادي',
            'New': 'جديد',
            'At Risk': 'معرض للخطر',
            'Lost': 'مفقود'
        };
        
        return translations[segment] || segment;
    }
    
    getSegmentClass(segment) {
        const classMap = {
            'VIP': 'vip',
            'High Value': 'high-value',
            'Regular': 'regular',
            'New': 'new',
            'At Risk': 'at-risk',
            'Lost': 'lost'
        };
        return classMap[segment] || 'regular';
    }
    
    formatCurrency(amount) {
        const formatted = Number(amount).toFixed(3);
        if (this.options.isArabic) {
            return `ر.ع. ${this.formatArabicNumbers(formatted)}`;
        }
        return `OMR ${formatted}`;
    }
    
    formatPercentage(value) {
        const formatted = Number(value).toFixed(1);
        if (this.options.isArabic) {
            return `${this.formatArabicNumbers(formatted)}٪`;
        }
        return `${formatted}%`;
    }
    
    formatDate(dateString) {
        if (!dateString) return '-';
        
        const date = new Date(dateString);
        if (this.options.isArabic) {
            return date.toLocaleDateString('ar-OM');
        }
        return date.toLocaleDateString('en-OM');
    }
    
    formatArabicNumbers(number) {
        const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        return number.toString().replace(/[0-9]/g, function(w) {
            return arabicNumerals[+w];
        });
    }
    
    formatEnglishNumbers(number) {
        return Number(number).toLocaleString();
    }
    
    // Data Generation Methods (Replace with real data)
    generateCLVTrendsData() {
        const months = this.getLast6Months();
        const datasets = [
            {
                name: this.options.isArabic ? 'متوسط قيمة العميل' : 'Average CLV',
                values: [850, 920, 1050, 1180, 1250, 1350]
            }
        ];
        
        return {
            labels: months,
            datasets: datasets
        };
    }
    
    generateRetentionCohortData() {
        const cohorts = this.options.isArabic 
            ? ['جديد', 'راسخ', 'مخلص', 'بطل']
            : ['New', 'Established', 'Loyal', 'Champion'];
        
        return {
            labels: cohorts,
            datasets: [{
                values: [25, 35, 30, 10]
            }]
        };
    }
    
    generateServicePatternsData() {
        const days = this.options.isArabic 
            ? ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
            : ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];
        
        const hours = ['8AM', '10AM', '12PM', '2PM', '4PM'];
        
        const dataPoints = [];
        days.forEach((day, dayIndex) => {
            hours.forEach((hour, hourIndex) => {
                dataPoints.push({
                    x: dayIndex,
                    y: hourIndex,
                    value: Math.floor(Math.random() * 20) + 1
                });
            });
        });
        
        return {
            dataPoints: dataPoints,
            start: new Date(2024, 0, 1),
            end: new Date(2024, 0, 5)
        };
    }
    
    getLast6Months() {
        const months = [];
        const now = new Date();
        
        for (let i = 5; i >= 0; i--) {
            const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
            if (this.options.isArabic) {
                const arabicMonths = [
                    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
                ];
                months.push(arabicMonths[date.getMonth()]);
            } else {
                months.push(date.toLocaleDateString('en-US', { month: 'short' }));
            }
        }
        
        return months;
    }
    
    formatNumbers(number) {
        if (this.options.isArabic) {
            return this.formatArabicNumbers(number);
        }
        return this.formatEnglishNumbers(number);
    }
        const months = [];
        const now = new Date();
        
        for (let i = 5; i >= 0; i--) {
            const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
            if (this.options.isArabic) {
                months.push(date.toLocaleDateString('ar-OM', { month: 'long' }));
            } else {
                months.push(date.toLocaleDateString('en-OM', { month: 'short' }));
            }
        }
        
        return months;
    }
    
    // UI State Management
    showLoading() {
        document.getElementById('loading-state').style.display = 'block';
        document.getElementById('dashboard-content').style.display = 'none';
        document.getElementById('error-state').style.display = 'none';
    }
    
    showContent() {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('dashboard-content').style.display = 'block';
        document.getElementById('error-state').style.display = 'none';
        
        // Add animations
        document.getElementById('dashboard-content').classList.add('fade-in');
    }
    
    showError(message) {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('dashboard-content').style.display = 'none';
        document.getElementById('error-state').style.display = 'block';
        document.getElementById('error-message').textContent = message;
    }
    
    setDateRange(days) {
        this.options.dateRange = days;
        this.loadDashboard();
    }
    
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadDashboard();
        }, this.options.refreshInterval);
    }
    
    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
    }
    
    // Static Methods for External Access
    static contactCustomer(customerId) {
        frappe.set_route('Form', 'Customer', customerId);
    }
    
    static exportData() {
        // Implement data export functionality
        console.log('Exporting analytics data...');
    }
}

// Make the class globally available
window.CustomerAnalyticsDashboard = CustomerAnalyticsDashboard; 