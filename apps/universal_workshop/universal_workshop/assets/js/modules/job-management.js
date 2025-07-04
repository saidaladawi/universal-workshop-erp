/**
 * Job Management Module for Universal Workshop Technician App
 * Handles detailed work order views, customer info, and job operations
 */

class JobManager {
    constructor(technicianApp) {
        this.app = technicianApp;
        this.currentJob = null;
        this.jobCache = new Map();
        this.searchFilters = {
            status: 'all',
            priority: 'all',
            searchText: ''
        };
        this.sortBy = 'priority'; // priority, date, customer, vehicle
        this.sortOrder = 'asc';
    }

    /**
     * Initialize job management interface
     */
    async initialize() {
        await this.loadJobs();
        this.setupJobInterface();
        this.setupEventListeners();
        console.log('[JobManager] Initialized');
    }

    /**
     * Load jobs from API or cache
     */
    async loadJobs() {
        try {
            this.app.showLoading();

            // Try to load from API first
            if (this.app.isOnline) {
                const response = await this.app.apiCall('/api/method/universal_workshop.www.technician.get_technician_jobs');

                if (response && response.message) {
                    const jobs = response.message;
                    await this.cacheJobs(jobs);
                    this.renderJobsList(jobs);
                    return jobs;
                }
            }

            // Fallback to cached data
            const cachedJobs = await this.getCachedJobs();
            this.renderJobsList(cachedJobs);
            return cachedJobs;

        } catch (error) {
            console.error('[JobManager] Failed to load jobs:', error);
            // Load from cache as final fallback
            const cachedJobs = await this.getCachedJobs();
            this.renderJobsList(cachedJobs);
            return cachedJobs;
        } finally {
            this.app.hideLoading();
        }
    }

    /**
     * Cache jobs in IndexedDB
     */
    async cacheJobs(jobs) {
        try {
            const transaction = this.app.db.transaction(['jobs'], 'readwrite');
            const store = transaction.objectStore('jobs');

            // Clear existing jobs
            await store.clear();

            // Add new jobs
            for (const job of jobs) {
                await store.add(job);
                this.jobCache.set(job.name, job);
            }

            console.log(`[JobManager] Cached ${jobs.length} jobs`);
        } catch (error) {
            console.error('[JobManager] Failed to cache jobs:', error);
        }
    }

    /**
     * Get cached jobs from IndexedDB
     */
    async getCachedJobs() {
        try {
            const transaction = this.app.db.transaction(['jobs'], 'readonly');
            const store = transaction.objectStore('jobs');
            const request = store.getAll();

            return new Promise((resolve, reject) => {
                request.onsuccess = () => {
                    const jobs = request.result || [];
                    jobs.forEach(job => this.jobCache.set(job.name, job));
                    resolve(jobs);
                };
                request.onerror = () => reject(request.error);
            });
        } catch (error) {
            console.error('[JobManager] Failed to get cached jobs:', error);
            return [];
        }
    }

    /**
     * Setup job management interface
     */
    setupJobInterface() {
        const jobsView = document.getElementById('jobs-view');
        if (!jobsView) return;

        jobsView.innerHTML = `
            <!-- Search and Filter Controls -->
            <div class="job-controls">
                <div class="search-container">
                    <input type="text" id="job-search" placeholder="${this.app.lang === 'ar' ? 'البحث في المهام...' : 'Search jobs...'}" 
                           class="search-input" dir="${this.app.lang === 'ar' ? 'rtl' : 'ltr'}">
                    <i class="search-icon icon-search"></i>
                </div>
                
                <div class="filter-controls">
                    <select id="status-filter" class="filter-select">
                        <option value="all">${this.app.lang === 'ar' ? 'جميع الحالات' : 'All Status'}</option>
                        <option value="assigned">${this.app.lang === 'ar' ? 'مُعيّن' : 'Assigned'}</option>
                        <option value="in-progress">${this.app.lang === 'ar' ? 'قيد التنفيذ' : 'In Progress'}</option>
                        <option value="on-hold">${this.app.lang === 'ar' ? 'معلق' : 'On Hold'}</option>
                    </select>
                    
                    <select id="priority-filter" class="filter-select">
                        <option value="all">${this.app.lang === 'ar' ? 'جميع الأولويات' : 'All Priority'}</option>
                        <option value="high">${this.app.lang === 'ar' ? 'عالية' : 'High'}</option>
                        <option value="medium">${this.app.lang === 'ar' ? 'متوسطة' : 'Medium'}</option>
                        <option value="low">${this.app.lang === 'ar' ? 'منخفضة' : 'Low'}</option>
                    </select>
                    
                    <button id="sort-toggle" class="sort-btn" title="${this.app.lang === 'ar' ? 'ترتيب' : 'Sort'}">
                        <i class="icon-sort"></i>
                    </button>
                </div>
            </div>

            <!-- Jobs List -->
            <div class="jobs-container">
                <div id="jobs-list" class="jobs-list">
                    <!-- Jobs will be populated here -->
                </div>
            </div>

            <!-- Job Details Modal -->
            <div id="job-details-modal" class="modal hidden">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-job-title">${this.app.lang === 'ar' ? 'تفاصيل المهمة' : 'Job Details'}</h3>
                        <button class="modal-close" onclick="jobManager.closeJobDetails()">
                            <i class="icon-x"></i>
                        </button>
                    </div>
                    <div class="modal-body" id="job-details-content">
                        <!-- Details will be populated here -->
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="jobManager.closeJobDetails()">
                            ${this.app.lang === 'ar' ? 'إغلاق' : 'Close'}
                        </button>
                        <button class="btn-primary" id="select-job-btn">
                            ${this.app.lang === 'ar' ? 'اختيار المهمة' : 'Select Job'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Setup event listeners for job management
     */
    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('job-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.searchFilters.searchText = e.target.value;
                this.applyFiltersAndSort();
            }, 300));
        }

        // Filter controls
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.searchFilters.status = e.target.value;
                this.applyFiltersAndSort();
            });
        }

        const priorityFilter = document.getElementById('priority-filter');
        if (priorityFilter) {
            priorityFilter.addEventListener('change', (e) => {
                this.searchFilters.priority = e.target.value;
                this.applyFiltersAndSort();
            });
        }

        // Sort toggle
        const sortToggle = document.getElementById('sort-toggle');
        if (sortToggle) {
            sortToggle.addEventListener('click', () => {
                this.toggleSort();
            });
        }

        // Refresh jobs
        const refreshBtn = document.getElementById('refresh-jobs');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadJobs();
            });
        }
    }

    /**
     * Render jobs list with current filters and sorting
     */
    async renderJobsList(jobs = null) {
        if (!jobs) {
            jobs = await this.getCachedJobs();
        }

        const jobsList = document.getElementById('jobs-list');
        if (!jobsList) return;

        // Apply filters and sorting
        const filteredJobs = this.filterAndSortJobs(jobs);

        jobsList.innerHTML = '';

        if (filteredJobs.length === 0) {
            jobsList.innerHTML = `
                <div class="empty-state">
                    <i class="icon-briefcase empty-icon"></i>
                    <h3>${this.app.lang === 'ar' ? 'لا توجد مهام' : 'No Jobs Found'}</h3>
                    <p>${this.app.lang === 'ar' ? 'لا توجد مهام مطابقة للفلاتر المحددة' : 'No jobs match your current filters'}</p>
                </div>
            `;
            return;
        }

        // Create job cards
        filteredJobs.forEach(job => {
            const jobCard = this.createJobCard(job);
            jobsList.appendChild(jobCard);
        });
    }

    /**
     * Create enhanced job card with detailed information
     */
    createJobCard(job) {
        const div = document.createElement('div');
        div.className = `job-card status-${job.status.toLowerCase().replace(' ', '-')}`;
        div.dataset.jobId = job.name;

        // Determine display names based on language
        const customerName = this.app.lang === 'ar' && job.customer_name_ar
            ? job.customer_name_ar
            : job.customer_name;

        const serviceName = this.app.lang === 'ar' && job.description_ar
            ? job.description_ar
            : job.description;

        // Format estimated time
        const estimatedTime = job.estimated_duration_hours
            ? `${job.estimated_duration_hours}${this.app.lang === 'ar' ? ' ساعة' : 'h'}`
            : this.app.lang === 'ar' ? 'غير محدد' : 'Not set';

        // Format dates
        const startTime = job.estimated_start_time
            ? new Date(job.estimated_start_time).toLocaleString(this.app.lang === 'ar' ? 'ar-AE' : 'en-US')
            : this.app.lang === 'ar' ? 'غير محدد' : 'Not scheduled';

        div.innerHTML = `
            <div class="job-header">
                <div class="job-title-section">
                    <h3 class="job-title">${job.service_order_number || job.name}</h3>
                    <span class="job-status status-${job.status.toLowerCase().replace(' ', '-')}">
                        ${this.app.translateStatus(job.status)}
                    </span>
                </div>
                <div class="job-priority priority-${job.priority.toLowerCase()}">
                    <i class="priority-icon icon-flag"></i>
                    <span>${this.app.translatePriority(job.priority)}</span>
                </div>
            </div>

            <div class="job-main-info">
                <div class="customer-info">
                    <i class="icon-user"></i>
                    <div>
                        <span class="label">${this.app.lang === 'ar' ? 'العميل:' : 'Customer:'}</span>
                        <span class="value">${customerName}</span>
                    </div>
                </div>

                <div class="vehicle-info">
                    <i class="icon-car"></i>
                    <div>
                        <span class="label">${this.app.lang === 'ar' ? 'المركبة:' : 'Vehicle:'}</span>
                        <span class="value">${job.vehicle_license_plate || job.vehicle || this.app.lang === 'ar' ? 'غير محدد' : 'Not specified'}</span>
                        ${job.make && job.model ? `<small>${job.year || ''} ${job.make} ${job.model}</small>` : ''}
                    </div>
                </div>

                <div class="service-info">
                    <i class="icon-tool"></i>
                    <div>
                        <span class="label">${this.app.lang === 'ar' ? 'الخدمة:' : 'Service:'}</span>
                        <span class="value">${serviceName || this.app.lang === 'ar' ? 'خدمة عامة' : 'General Service'}</span>
                    </div>
                </div>
            </div>

            <div class="job-meta">
                <div class="meta-item">
                    <i class="icon-clock"></i>
                    <span>${this.app.lang === 'ar' ? 'الوقت المقدر:' : 'Est. Time:'} ${estimatedTime}</span>
                </div>
                <div class="meta-item">
                    <i class="icon-calendar"></i>
                    <span>${this.app.lang === 'ar' ? 'موعد البدء:' : 'Start Time:'} ${startTime}</span>
                </div>
                ${job.total_estimated_cost ? `
                    <div class="meta-item">
                        <i class="icon-dollar-sign"></i>
                        <span>${this.app.lang === 'ar' ? 'التكلفة المقدرة:' : 'Est. Cost:'} ${job.total_estimated_cost} OMR</span>
                    </div>
                ` : ''}
            </div>

            <div class="job-actions">
                <button class="btn-outline" onclick="jobManager.viewJobDetails('${job.name}')">
                    <i class="icon-eye"></i>
                    <span>${this.app.lang === 'ar' ? 'التفاصيل' : 'Details'}</span>
                </button>
                <button class="btn-primary" onclick="jobManager.selectJob('${job.name}')">
                    <i class="icon-play"></i>
                    <span>${this.app.lang === 'ar' ? 'بدء العمل' : 'Start Work'}</span>
                </button>
            </div>

            ${job.current_time_log && job.current_time_log.length > 0 ? `
                <div class="job-active-indicator">
                    <i class="icon-clock pulse"></i>
                    <span>${this.app.lang === 'ar' ? 'جاري العمل' : 'Work in Progress'}</span>
                </div>
            ` : ''}
        `;

        return div;
    }

    /**
     * View detailed job information in modal
     */
    async viewJobDetails(jobName) {
        try {
            const job = this.jobCache.get(jobName) || await this.getJobDetails(jobName);
            if (!job) {
                this.app.showError(this.app.getString('error'), 'Job not found');
                return;
            }

            this.showJobDetailsModal(job);
        } catch (error) {
            console.error('[JobManager] Failed to view job details:', error);
            this.app.showError(this.app.getString('error'), error.message);
        }
    }

    /**
     * Show job details modal
     */
    showJobDetailsModal(job) {
        const modal = document.getElementById('job-details-modal');
        const content = document.getElementById('job-details-content');
        const selectBtn = document.getElementById('select-job-btn');

        if (!modal || !content) return;

        // Populate modal content
        content.innerHTML = this.createJobDetailsContent(job);

        // Setup select button
        selectBtn.onclick = () => {
            this.selectJob(job.name);
            this.closeJobDetails();
        };

        // Show modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Create detailed job content for modal
     */
    createJobDetailsContent(job) {
        const serviceItems = job.service_items || [];
        const timeLog = job.current_time_log && job.current_time_log.length > 0 ? job.current_time_log[0] : null;

        return `
            <div class="job-details-sections">
                <!-- Customer & Vehicle Section -->
                <div class="details-section">
                    <h4>${this.app.lang === 'ar' ? 'معلومات العميل والمركبة' : 'Customer & Vehicle Information'}</h4>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>${this.app.lang === 'ar' ? 'العميل:' : 'Customer:'}</label>
                            <span>${this.app.lang === 'ar' && job.customer_name_ar ? job.customer_name_ar : job.customer_name}</span>
                        </div>
                        <div class="info-item">
                            <label>${this.app.lang === 'ar' ? 'رقم اللوحة:' : 'License Plate:'}</label>
                            <span>${job.vehicle_license_plate || this.app.lang === 'ar' ? 'غير محدد' : 'Not specified'}</span>
                        </div>
                        ${job.make && job.model ? `
                            <div class="info-item">
                                <label>${this.app.lang === 'ar' ? 'المركبة:' : 'Vehicle:'}</label>
                                <span>${job.year || ''} ${job.make} ${job.model}</span>
                            </div>
                        ` : ''}
                        ${job.color ? `
                            <div class="info-item">
                                <label>${this.app.lang === 'ar' ? 'اللون:' : 'Color:'}</label>
                                <span>${job.color}</span>
                            </div>
                        ` : ''}
                        ${job.vin ? `
                            <div class="info-item">
                                <label>${this.app.lang === 'ar' ? 'رقم الهيكل:' : 'VIN:'}</label>
                                <span>${job.vin}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Service Items Section -->
                ${serviceItems.length > 0 ? `
                    <div class="details-section">
                        <h4>${this.app.lang === 'ar' ? 'عناصر الخدمة' : 'Service Items'}</h4>
                        <div class="service-items-list">
                            ${serviceItems.map(item => `
                                <div class="service-item">
                                    <div class="item-info">
                                        <span class="item-name">${this.app.lang === 'ar' && item.item_name_ar ? item.item_name_ar : item.item_name}</span>
                                        <span class="item-code">${item.item_code}</span>
                                    </div>
                                    <div class="item-details">
                                        <span class="quantity">${this.app.lang === 'ar' ? 'الكمية:' : 'Qty:'} ${item.qty}</span>
                                        ${item.estimated_time_hours ? `<span class="time">${item.estimated_time_hours}${this.app.lang === 'ar' ? ' ساعة' : 'h'}</span>` : ''}
                                        ${item.rate ? `<span class="rate">${item.rate} OMR</span>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Time Tracking Section -->
                ${timeLog ? `
                    <div class="details-section">
                        <h4>${this.app.lang === 'ar' ? 'تتبع الوقت' : 'Time Tracking'}</h4>
                        <div class="time-tracking-info">
                            <div class="info-item">
                                <label>${this.app.lang === 'ar' ? 'بدء العمل:' : 'Started:'}</label>
                                <span>${new Date(timeLog.start_time).toLocaleString()}</span>
                            </div>
                            <div class="info-item">
                                <label>${this.app.lang === 'ar' ? 'الحالة:' : 'Status:'}</label>
                                <span class="status-badge status-${timeLog.status.toLowerCase()}">${this.app.translateStatus(timeLog.status)}</span>
                            </div>
                            ${timeLog.total_hours ? `
                                <div class="info-item">
                                    <label>${this.app.lang === 'ar' ? 'إجمالي الساعات:' : 'Total Hours:'}</label>
                                    <span>${timeLog.total_hours}${this.app.lang === 'ar' ? ' ساعة' : 'h'}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}

                <!-- Job Notes Section -->
                <div class="details-section">
                    <h4>${this.app.lang === 'ar' ? 'ملاحظات المهمة' : 'Job Notes'}</h4>
                    <div class="job-notes">
                        <textarea id="job-notes" placeholder="${this.app.lang === 'ar' ? 'أضف ملاحظاتك هنا...' : 'Add your notes here...'}" 
                                  rows="4" dir="${this.app.lang === 'ar' ? 'rtl' : 'ltr'}"></textarea>
                        <button class="btn-secondary save-notes-btn" onclick="jobManager.saveJobNotes('${job.name}')">
                            ${this.app.lang === 'ar' ? 'حفظ الملاحظات' : 'Save Notes'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Close job details modal
     */
    closeJobDetails() {
        const modal = document.getElementById('job-details-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }

    /**
     * Select a job for work
     */
    async selectJob(jobName) {
        try {
            const job = this.jobCache.get(jobName);
            if (!job) {
                this.app.showError(this.app.getString('error'), 'Job not found');
                return;
            }

            this.currentJob = job;
            this.app.currentJob = job;

            // Update timer interface
            this.app.timeTracker.setCurrentJob(job);

            // Switch to timer view
            this.app.switchView('timer');

            // Show confirmation
            this.app.showNotification(
                this.app.getString('jobAssigned'),
                `${this.app.lang === 'ar' ? 'تم اختيار مهمة:' : 'Selected job:'} ${job.service_order_number || job.name}`
            );

            // Log job selection
            console.log('[JobManager] Job selected:', job.name);

        } catch (error) {
            console.error('[JobManager] Failed to select job:', error);
            this.app.showError(this.app.getString('error'), error.message);
        }
    }

    /**
     * Save job notes
     */
    async saveJobNotes(jobName, notes) {
        try {
            // Get notes from textarea if not provided
            if (!notes) {
                const notesTextarea = document.getElementById('job-notes');
                notes = notesTextarea ? notesTextarea.value : '';
            }

            if (!notes.trim()) return;

            // Save to server if online
            if (this.app.isOnline) {
                await this.app.apiCall('/api/method/universal_workshop.www.technician.add_job_comment', {
                    service_order: jobName,
                    comment: notes
                });
            }

            // Save to local storage for offline
            const job = this.jobCache.get(jobName);
            if (job) {
                if (!job.local_notes) job.local_notes = [];
                job.local_notes.push({
                    note: notes,
                    timestamp: new Date().toISOString(),
                    synced: this.app.isOnline
                });
                this.jobCache.set(jobName, job);
            }

            this.app.showNotification(
                this.app.lang === 'ar' ? 'تم الحفظ' : 'Saved',
                this.app.lang === 'ar' ? 'تم حفظ الملاحظات' : 'Notes saved successfully'
            );

        } catch (error) {
            console.error('[JobManager] Failed to save notes:', error);
            this.app.showError(this.app.getString('error'), error.message);
        }
    }

    /**
     * Filter and sort jobs based on current criteria
     */
    filterAndSortJobs(jobs) {
        let filtered = [...jobs];

        // Apply status filter
        if (this.searchFilters.status !== 'all') {
            filtered = filtered.filter(job =>
                job.status.toLowerCase().replace(' ', '-') === this.searchFilters.status
            );
        }

        // Apply priority filter
        if (this.searchFilters.priority !== 'all') {
            filtered = filtered.filter(job =>
                job.priority.toLowerCase() === this.searchFilters.priority
            );
        }

        // Apply search text filter
        if (this.searchFilters.searchText) {
            const searchLower = this.searchFilters.searchText.toLowerCase();
            filtered = filtered.filter(job => {
                return (
                    job.service_order_number?.toLowerCase().includes(searchLower) ||
                    job.customer_name?.toLowerCase().includes(searchLower) ||
                    job.customer_name_ar?.includes(this.searchFilters.searchText) ||
                    job.vehicle_license_plate?.toLowerCase().includes(searchLower) ||
                    job.description?.toLowerCase().includes(searchLower) ||
                    job.description_ar?.includes(this.searchFilters.searchText)
                );
            });
        }

        // Apply sorting
        filtered.sort((a, b) => {
            let comparison = 0;

            switch (this.sortBy) {
                case 'priority':
                    const priorityOrder = { 'high': 1, 'medium': 2, 'low': 3 };
                    comparison = priorityOrder[a.priority.toLowerCase()] - priorityOrder[b.priority.toLowerCase()];
                    break;
                case 'date':
                    comparison = new Date(a.estimated_start_time || a.creation) - new Date(b.estimated_start_time || b.creation);
                    break;
                case 'customer':
                    comparison = (a.customer_name || '').localeCompare(b.customer_name || '');
                    break;
                case 'vehicle':
                    comparison = (a.vehicle_license_plate || '').localeCompare(b.vehicle_license_plate || '');
                    break;
            }

            return this.sortOrder === 'asc' ? comparison : -comparison;
        });

        return filtered;
    }

    /**
     * Apply current filters and re-render list
     */
    async applyFiltersAndSort() {
        const jobs = await this.getCachedJobs();
        this.renderJobsList(jobs);
    }

    /**
     * Toggle sort order
     */
    toggleSort() {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        this.applyFiltersAndSort();

        // Update button indicator
        const sortBtn = document.getElementById('sort-toggle');
        if (sortBtn) {
            sortBtn.innerHTML = `<i class="icon-sort-${this.sortOrder}"></i>`;
        }
    }

    /**
     * Get detailed job information
     */
    async getJobDetails(jobName) {
        try {
            if (this.app.isOnline) {
                const response = await this.app.apiCall('/api/method/universal_workshop.www.technician.get_job_details', {
                    job_name: jobName
                });
                return response?.message;
            }

            return this.jobCache.get(jobName);
        } catch (error) {
            console.error('[JobManager] Failed to get job details:', error);
            return this.jobCache.get(jobName);
        }
    }

    /**
     * Debounce utility function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Refresh jobs data
     */
    async refreshJobs() {
        await this.loadJobs();
    }

    /**
     * Get current job
     */
    getCurrentJob() {
        return this.currentJob;
    }

    /**
     * Clear current job selection
     */
    clearCurrentJob() {
        this.currentJob = null;
        this.app.currentJob = null;
    }
}

// Export for use in technician app
window.JobManager = JobManager; 