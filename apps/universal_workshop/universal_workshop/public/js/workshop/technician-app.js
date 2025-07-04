/**
 * Universal Workshop Technician PWA Application
 * Offline-first mobile interface for technician workflows
 * Arabic/English bilingual support
 */

class TechnicianApp {
    constructor() {
        this.isOnline = navigator.onLine;
        this.syncQueue = [];
        this.db = null;
        this.currentUser = null;
        this.currentJob = null;
        this.timeTracker = new TimeTracker();
        this.mediaCapture = new MediaCapture();
        this.barcodeScanner = new BarcodeScanner();
        this.pushNotifications = new PushNotificationManager();

        // Arabic/English UI strings
        this.strings = {
            ar: {
                offline: 'غير متصل',
                online: 'متصل',
                syncing: 'مزامنة...',
                syncComplete: 'تمت المزامنة',
                jobAssigned: 'تم تعيين مهمة جديدة',
                timeStarted: 'بدء توقيت العمل',
                timeStopped: 'توقف توقيت العمل',
                photoTaken: 'تم التقاط الصورة',
                partScanned: 'تم مسح القطعة',
                error: 'خطأ',
                loading: 'جاري التحميل...'
            },
            en: {
                offline: 'Offline',
                online: 'Online',
                syncing: 'Syncing...',
                syncComplete: 'Sync Complete',
                jobAssigned: 'New job assigned',
                timeStarted: 'Time tracking started',
                timeStopped: 'Time tracking stopped',
                photoTaken: 'Photo captured',
                partScanned: 'Part scanned',
                error: 'Error',
                loading: 'Loading...'
            }
        };

        this.lang = navigator.language.startsWith('ar') ? 'ar' : 'en';
        this.init();
    }

    async init() {
        try {
            // Initialize IndexedDB for offline storage
            await this.initDatabase();

            // Register service worker
            await this.registerServiceWorker();

            // Set up UI
            this.setupUI();

            // Set up event listeners
            this.setupEventListeners();

            // Load current user and jobs
            await this.loadUserData();

            // Set up offline/online detection
            this.setupConnectivityMonitoring();

            // Start periodic sync
            this.startPeriodicSync();

            // Initialize push notifications
            await this.pushNotifications.init();

            console.log('[TechnicianApp] Initialization complete');
        } catch (error) {
            console.error('[TechnicianApp] Initialization failed:', error);
            this.showError(this.getString('error'), error.message);
        }
    }

    async initDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('UWTechnicianDB', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Job data
                if (!db.objectStoreNames.contains('jobs')) {
                    const jobStore = db.createObjectStore('jobs', { keyPath: 'name' });
                    jobStore.createIndex('status', 'status', { unique: false });
                    jobStore.createIndex('assigned_to', 'assigned_to', { unique: false });
                }

                // Time logs
                if (!db.objectStoreNames.contains('time_logs')) {
                    const timeStore = db.createObjectStore('time_logs', { keyPath: 'id' });
                    timeStore.createIndex('job', 'job', { unique: false });
                }

                // Media files
                if (!db.objectStoreNames.contains('media')) {
                    const mediaStore = db.createObjectStore('media', { keyPath: 'id' });
                    mediaStore.createIndex('job', 'job', { unique: false });
                }

                // Parts usage
                if (!db.objectStoreNames.contains('parts_usage')) {
                    const partsStore = db.createObjectStore('parts_usage', { keyPath: 'id' });
                    partsStore.createIndex('job', 'job', { unique: false });
                }

                // Sync queue
                if (!db.objectStoreNames.contains('sync_queue')) {
                    db.createObjectStore('sync_queue', { keyPath: 'id' });
                }
            };
        });
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/assets/universal_workshop/js/technician-sw.js');
                console.log('[TechnicianApp] Service worker registered:', registration);

                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showNotification(this.getString('syncComplete'), 'App updated. Refresh for new features.');
                        }
                    });
                });

                return registration;
            } catch (error) {
                console.error('[TechnicianApp] Service worker registration failed:', error);
                throw error;
            }
        }
    }

    setupUI() {
        // Create main app container
        const appHTML = `
            <div id="technician-app" class="technician-app ${this.lang === 'ar' ? 'rtl' : 'ltr'}">
                <!-- Header -->
                <header class="app-header">
                    <div class="header-content">
                        <h1>${this.lang === 'ar' ? 'ورشة شاملة' : 'Universal Workshop'}</h1>
                        <div class="connection-status" id="connection-status">
                            <span class="status-indicator"></span>
                            <span class="status-text">${this.getString('online')}</span>
                        </div>
                    </div>
                </header>

                <!-- Navigation -->
                <nav class="app-nav">
                    <button class="nav-btn active" data-view="jobs">
                        <i class="icon-briefcase"></i>
                        <span>${this.lang === 'ar' ? 'المهام' : 'Jobs'}</span>
                    </button>
                    <button class="nav-btn" data-view="timer">
                        <i class="icon-clock"></i>
                        <span>${this.lang === 'ar' ? 'الموقت' : 'Timer'}</span>
                    </button>
                    <button class="nav-btn" data-view="media">
                        <i class="icon-camera"></i>
                        <span>${this.lang === 'ar' ? 'الوسائط' : 'Media'}</span>
                    </button>
                    <button class="nav-btn" data-view="parts">
                        <i class="icon-box"></i>
                        <span>${this.lang === 'ar' ? 'القطع' : 'Parts'}</span>
                    </button>
                </nav>

                <!-- Main Content -->
                <main class="app-main">
                    <!-- Jobs View -->
                    <div id="jobs-view" class="view active">
                        <div class="view-header">
                            <h2>${this.lang === 'ar' ? 'مهامي' : 'My Jobs'}</h2>
                            <button class="refresh-btn" id="refresh-jobs">
                                <i class="icon-refresh"></i>
                            </button>
                        </div>
                        <div class="jobs-list" id="jobs-list">
                            <!-- Jobs will be populated here -->
                        </div>
                    </div>

                    <!-- Timer View -->
                    <div id="timer-view" class="view">
                        <div class="timer-container">
                            <!-- Current Job Info -->
                            <div class="current-job" id="current-job-info">
                                <h3>${this.lang === 'ar' ? 'المهمة الحالية' : 'Current Job'}</h3>
                                <p id="job-title">${this.lang === 'ar' ? 'لا توجد مهمة نشطة' : 'No active job'}</p>
                            </div>

                            <!-- Timer Display Circle -->
                            <div class="timer-circle-container">
                                <div class="timer-circle">
                                    <div class="timer-circle-inner">
                                        <div class="timer-display" id="timer-display">00:00:00</div>
                                        <div class="timer-status" id="timer-status">${this.lang === 'ar' ? 'متوقف' : 'Stopped'}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Time Summary -->
                            <div class="time-summary">
                                <div class="time-summary-item">
                                    <span class="time-label">${this.lang === 'ar' ? 'وقت العمل' : 'Work Time'}</span>
                                    <span class="time-value" id="work-time">00:00:00</span>
                                </div>
                                <div class="time-summary-item">
                                    <span class="time-label">${this.lang === 'ar' ? 'وقت الاستراحة' : 'Break Time'}</span>
                                    <span class="time-value" id="break-time">00:00:00</span>
                                </div>
                                <div class="time-summary-item">
                                    <span class="time-label">${this.lang === 'ar' ? 'الوقت الإجمالي' : 'Total Time'}</span>
                                    <span class="time-value" id="total-time">00:00:00</span>
                                </div>
                            </div>

                            <!-- Timer Controls -->
                            <div class="timer-controls">
                                <button id="start-timer" class="timer-btn start-btn" disabled>
                                    <i class="icon-play"></i>
                                    <span>${this.lang === 'ar' ? 'بدء' : 'Start'}</span>
                                </button>
                                <button id="pause-timer" class="timer-btn pause-btn" disabled>
                                    <i class="icon-pause"></i>
                                    <span>${this.lang === 'ar' ? 'إيقاف مؤقت' : 'Pause'}</span>
                                </button>
                                <button id="resume-timer" class="timer-btn resume-btn" style="display: none;">
                                    <i class="icon-play"></i>
                                    <span>${this.lang === 'ar' ? 'استئناف' : 'Resume'}</span>
                                </button>
                                <button id="break-timer" class="timer-btn break-btn" disabled>
                                    <i class="icon-coffee"></i>
                                    <span>${this.lang === 'ar' ? 'استراحة' : 'Break'}</span>
                                </button>
                                <button id="end-break-timer" class="timer-btn end-break-btn" style="display: none;">
                                    <i class="icon-play"></i>
                                    <span>${this.lang === 'ar' ? 'انهاء الاستراحة' : 'End Break'}</span>
                                </button>
                                <button id="stop-timer" class="timer-btn stop-btn" disabled>
                                    <i class="icon-stop"></i>
                                    <span>${this.lang === 'ar' ? 'إيقاف' : 'Stop'}</span>
                                </button>
                            </div>

                            <!-- Additional Controls -->
                            <div class="timer-additional-controls">
                                <button id="manual-time-entry" class="additional-control-btn">
                                    <i class="icon-edit"></i>
                                    <span>${this.lang === 'ar' ? 'إدخال يدوي' : 'Manual Entry'}</span>
                                </button>
                            </div>

                            <!-- Break History -->
                            <div class="break-history-section">
                                <h4>${this.lang === 'ar' ? 'تاريخ الاستراحات' : 'Break History'}</h4>
                                <div class="break-history" id="break-history">
                                    <!-- Break history items will be populated here -->
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Media View -->
                    <div id="media-view" class="view">
                        <div class="media-controls">
                            <button id="take-photo" class="media-btn">
                                <i class="icon-camera"></i>
                                <span>${this.lang === 'ar' ? 'التقاط صورة' : 'Take Photo'}</span>
                            </button>
                            <button id="record-video" class="media-btn">
                                <i class="icon-video"></i>
                                <span>${this.lang === 'ar' ? 'تسجيل فيديو' : 'Record Video'}</span>
                            </button>
                        </div>
                        <div class="media-gallery" id="media-gallery">
                            <!-- Media items will be populated here -->
                        </div>
                    </div>

                    <!-- Parts View -->
                    <div id="parts-view" class="view">
                        <div class="parts-controls">
                            <button id="scan-barcode" class="parts-btn">
                                <i class="icon-barcode"></i>
                                <span>${this.lang === 'ar' ? 'مسح الباركود' : 'Scan Barcode'}</span>
                            </button>
                            <input type="text" id="manual-part-code" placeholder="${this.lang === 'ar' ? 'رمز القطعة يدوياً' : 'Enter part code manually'}">
                        </div>
                        <div class="parts-list" id="parts-list">
                            <!-- Used parts will be populated here -->
                        </div>
                    </div>
                </main>

                <!-- Sync Indicator -->
                <div class="sync-indicator" id="sync-indicator">
                    <div class="sync-progress"></div>
                    <span class="sync-text">${this.getString('syncing')}</span>
                </div>

                <!-- Notifications -->
                <div class="notifications" id="notifications"></div>
            </div>
        `;

        // Insert into page
        document.body.insertAdjacentHTML('beforeend', appHTML);
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.closest('.nav-btn').dataset.view;
                this.switchView(view);
            });
        });

        // Jobs refresh
        document.getElementById('refresh-jobs').addEventListener('click', () => {
            this.loadJobs();
        });

        // Timer controls
        document.getElementById('start-timer').addEventListener('click', () => {
            this.timeTracker.start(this.currentJob);
        });

        document.getElementById('pause-timer').addEventListener('click', () => {
            this.timeTracker.pause();
        });

        document.getElementById('resume-timer').addEventListener('click', () => {
            this.timeTracker.resume();
        });

        document.getElementById('break-timer').addEventListener('click', () => {
            this.timeTracker.showBreakModal();
        });

        document.getElementById('end-break-timer').addEventListener('click', () => {
            this.timeTracker.endBreak();
        });

        document.getElementById('stop-timer').addEventListener('click', () => {
            this.timeTracker.stop();
        });

        document.getElementById('manual-time-entry').addEventListener('click', () => {
            this.timeTracker.showManualTimeEntry();
        });

        // Media controls
        document.getElementById('take-photo').addEventListener('click', () => {
            this.mediaCapture.takePhoto(this.currentJob);
        });

        document.getElementById('record-video').addEventListener('click', () => {
            this.mediaCapture.recordVideo(this.currentJob);
        });

        // Parts controls
        document.getElementById('scan-barcode').addEventListener('click', () => {
            this.barcodeScanner.scan();
        });

        document.getElementById('manual-part-code').addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                this.addPartUsage(e.target.value);
                e.target.value = '';
            }
        });

        // Connectivity monitoring
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateConnectionStatus();
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateConnectionStatus();
        });
    }

    async loadUserData() {
        try {
            const response = await this.apiCall('universal_workshop.mobile_technician.api.get_technician_data');
            if (response && !response.offline) {
                this.currentUser = response.message.technician;
                await this.loadJobs();
            } else {
                // Load from cache
                await this.loadCachedData();
            }
        } catch (error) {
            console.error('[TechnicianApp] Failed to load user data:', error);
            await this.loadCachedData();
        }
    }

    async loadJobs() {
        try {
            this.showLoading();
            const response = await this.apiCall('universal_workshop.mobile_technician.api.get_assigned_jobs');

            if (response && !response.offline) {
                const jobs = response.message.jobs;
                await this.cacheJobs(jobs);
                this.renderJobs(jobs);
            } else {
                const cachedJobs = await this.getCachedJobs();
                this.renderJobs(cachedJobs);
            }
        } catch (error) {
            console.error('[TechnicianApp] Failed to load jobs:', error);
            const cachedJobs = await this.getCachedJobs();
            this.renderJobs(cachedJobs);
        } finally {
            this.hideLoading();
        }
    }

    renderJobs(jobs) {
        const jobsList = document.getElementById('jobs-list');
        jobsList.innerHTML = '';

        if (!jobs || jobs.length === 0) {
            jobsList.innerHTML = `
                <div class="empty-state">
                    <i class="icon-briefcase"></i>
                    <p>${this.lang === 'ar' ? 'لا توجد مهام مُعيّنة' : 'No assigned jobs'}</p>
                </div>
            `;
            return;
        }

        jobs.forEach(job => {
            const jobCard = this.createJobCard(job);
            jobsList.appendChild(jobCard);
        });
    }

    createJobCard(job) {
        const div = document.createElement('div');
        div.className = `job-card status-${job.status.toLowerCase()}`;
        div.innerHTML = `
            <div class="job-header">
                <h3>${job.title || job.name}</h3>
                <span class="job-status">${this.translateStatus(job.status)}</span>
            </div>
            <div class="job-details">
                <p class="customer">${this.lang === 'ar' ? 'العميل:' : 'Customer:'} ${job.customer}</p>
                <p class="vehicle">${this.lang === 'ar' ? 'المركبة:' : 'Vehicle:'} ${job.vehicle}</p>
                <p class="priority">${this.lang === 'ar' ? 'الأولوية:' : 'Priority:'} ${this.translatePriority(job.priority)}</p>
            </div>
            <div class="job-actions">
                <button class="btn-primary" onclick="technicianApp.selectJob('${job.name}')">
                    ${this.lang === 'ar' ? 'اختيار' : 'Select'}
                </button>
                <button class="btn-secondary" onclick="technicianApp.viewJobDetails('${job.name}')">
                    ${this.lang === 'ar' ? 'التفاصيل' : 'Details'}
                </button>
            </div>
        `;
        return div;
    }

    async selectJob(jobName) {
        try {
            const jobs = await this.getCachedJobs();
            this.currentJob = jobs.find(job => job.name === jobName);

            if (this.currentJob) {
                // Update UI
                document.getElementById('job-title').textContent = this.currentJob.title || this.currentJob.name;

                // Enable timer controls
                document.getElementById('start-timer').disabled = false;

                // Switch to timer view
                this.switchView('timer');

                this.showNotification(
                    this.getString('jobAssigned'),
                    `${this.lang === 'ar' ? 'تم اختيار مهمة:' : 'Selected job:'} ${this.currentJob.title}`
                );
            }
        } catch (error) {
            console.error('[TechnicianApp] Failed to select job:', error);
            this.showError(this.getString('error'), error.message);
        }
    }

    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        // Load data for specific views
        if (viewName === 'parts') {
            this.loadPartsList();
        } else if (viewName === 'media') {
            this.mediaCapture.renderMediaGallery();
        }
    }

    updateConnectionStatus() {
        const statusEl = document.getElementById('connection-status');
        const indicator = statusEl.querySelector('.status-indicator');
        const text = statusEl.querySelector('.status-text');

        if (this.isOnline) {
            indicator.className = 'status-indicator online';
            text.textContent = this.getString('online');
        } else {
            indicator.className = 'status-indicator offline';
            text.textContent = this.getString('offline');
        }
    }

    setupConnectivityMonitoring() {
        this.updateConnectionStatus();

        // Check connectivity every 30 seconds
        setInterval(() => {
            this.checkConnectivity();
        }, 30000);
    }

    async checkConnectivity() {
        try {
            const response = await fetch('/api/method/frappe.auth.get_csrf_token', {
                method: 'GET',
                cache: 'no-cache'
            });

            const wasOnline = this.isOnline;
            this.isOnline = response.ok;

            if (!wasOnline && this.isOnline) {
                // Just came online
                this.updateConnectionStatus();
                await this.syncPendingData();
            } else if (wasOnline && !this.isOnline) {
                // Just went offline
                this.updateConnectionStatus();
            }
        } catch (error) {
            const wasOnline = this.isOnline;
            this.isOnline = false;

            if (wasOnline) {
                this.updateConnectionStatus();
            }
        }
    }

    startPeriodicSync() {
        // Sync every 5 minutes when online
        setInterval(() => {
            if (this.isOnline) {
                this.syncPendingData();
            }
        }, 5 * 60 * 1000);
    }

    async syncPendingData() {
        if (!this.isOnline) return;

        try {
            this.showSyncIndicator();

            // Register background sync if available
            if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('technician-data-sync');
            } else {
                // Fallback sync
                await this.manualSync();
            }

            this.hideSyncIndicator();
            this.showNotification(this.getString('syncComplete'), '');
        } catch (error) {
            console.error('[TechnicianApp] Sync failed:', error);
            this.hideSyncIndicator();
        }
    }

    async manualSync() {
        // Sync pending time logs
        const pendingLogs = await this.getPendingData('time_logs');
        for (const log of pendingLogs) {
            await this.syncTimeLog(log);
        }

        // Sync pending media
        const pendingMedia = await this.getPendingData('media');
        for (const media of pendingMedia) {
            await this.syncMedia(media);
        }

        // Sync pending parts usage
        const pendingParts = await this.getPendingData('parts_usage');
        for (const part of pendingParts) {
            await this.syncPartUsage(part);
        }
    }

    // Utility methods
    async apiCall(method, args = {}) {
        try {
            const response = await fetch(`/api/method/${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': await this.getCSRFToken()
                },
                body: JSON.stringify(args)
            });

            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`[TechnicianApp] API call failed: ${method}`, error);
            throw error;
        }
    }

    async getCSRFToken() {
        try {
            const response = await fetch('/api/method/frappe.auth.get_csrf_token');
            const data = await response.json();
            return data.csrf_token;
        } catch (error) {
            return '';
        }
    }

    getString(key) {
        return this.strings[this.lang][key] || this.strings.en[key] || key;
    }

    translateStatus(status) {
        const statusTranslations = {
            ar: {
                'Draft': 'مسودة',
                'Confirmed': 'مؤكد',
                'In Progress': 'قيد التنفيذ',
                'Completed': 'مكتمل',
                'Cancelled': 'ملغى'
            },
            en: {
                'Draft': 'Draft',
                'Confirmed': 'Confirmed',
                'In Progress': 'In Progress',
                'Completed': 'Completed',
                'Cancelled': 'Cancelled'
            }
        };
        return statusTranslations[this.lang][status] || status;
    }

    translatePriority(priority) {
        const priorityTranslations = {
            ar: {
                'High': 'عالية',
                'Medium': 'متوسطة',
                'Low': 'منخفضة'
            },
            en: {
                'High': 'High',
                'Medium': 'Medium',
                'Low': 'Low'
            }
        };
        return priorityTranslations[this.lang][priority] || priority;
    }

    showLoading() {
        const loader = document.createElement('div');
        loader.id = 'loading-overlay';
        loader.className = 'loading-overlay';
        loader.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>${this.getString('loading')}</p>
            </div>
        `;
        document.body.appendChild(loader);
    }

    hideLoading() {
        const loader = document.getElementById('loading-overlay');
        if (loader) {
            loader.remove();
        }
    }

    showSyncIndicator() {
        document.getElementById('sync-indicator').classList.add('visible');
    }

    hideSyncIndicator() {
        document.getElementById('sync-indicator').classList.remove('visible');
    }

    showNotification(title, message) {
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close">&times;</button>
        `;

        document.getElementById('notifications').appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    showError(title, message) {
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close">&times;</button>
        `;

        document.getElementById('notifications').appendChild(notification);

        // Manual close only for errors
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    // Database helper methods
    async cacheJobs(jobs) {
        const transaction = this.db.transaction(['jobs'], 'readwrite');
        const store = transaction.objectStore('jobs');

        for (const job of jobs) {
            await store.put(job);
        }
    }

    async getCachedJobs() {
        const transaction = this.db.transaction(['jobs'], 'readonly');
        const store = transaction.objectStore('jobs');
        const request = store.getAll();

        return new Promise((resolve, reject) => {
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async loadCachedData() {
        try {
            const jobs = await this.getCachedJobs();
            this.renderJobs(jobs);
        } catch (error) {
            console.error('[TechnicianApp] Failed to load cached data:', error);
            this.renderJobs([]);
        }
    }

    async getPendingData(storeName) {
        try {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore('sync_queue');
            const pendingData = await store.getAll();
            return pendingData.filter(item => item.type === storeName);
        } catch (error) {
            console.error(`[TechnicianApp] Failed to get pending ${storeName}:`, error);
            return [];
        }
    }

    async syncPartUsage(partUsage) {
        try {
            const response = await this.apiCall('add_part_usage', {
                service_order: partUsage.job,
                barcode: partUsage.barcode,
                quantity: partUsage.quantity,
                notes: partUsage.notes || ''
            });

            if (response.success) {
                // Mark as synced in IndexedDB
                const transaction = this.db.transaction(['parts_usage'], 'readwrite');
                const store = transaction.objectStore('parts_usage');
                partUsage.synced = true;
                partUsage.syncedAt = new Date().toISOString();
                await store.put(partUsage);

                this.showNotification(
                    this.getString('syncComplete'),
                    `${this.lang === 'ar' ? 'تم مزامنة القطعة' : 'Part synced'}: ${partUsage.barcode}`
                );

                // Refresh parts list if visible
                this.updatePartsList();
            }
        } catch (error) {
            console.error('[TechnicianApp] Part sync failed:', error);
            partUsage.syncAttempts = (partUsage.syncAttempts || 0) + 1;

            // Retry up to 3 times
            if (partUsage.syncAttempts < 3) {
                setTimeout(() => this.syncPartUsage(partUsage), 5000 * partUsage.syncAttempts);
            }
        }
    }

    async loadPartsList(jobName = null) {
        const targetJob = jobName || this.currentJob?.name;
        if (!targetJob) return;

        try {
            // Load from server if online
            if (this.isOnline) {
                const response = await this.apiCall('get_parts_list', {
                    service_order: targetJob
                });

                if (response.success) {
                    await this.cachePartsList(targetJob, response.parts_usage);
                    this.renderPartsList(response.parts_usage, response.totals);
                    return;
                }
            }

            // Load from IndexedDB cache
            await this.loadCachedPartsList(targetJob);

        } catch (error) {
            console.error('[TechnicianApp] Failed to load parts list:', error);
            await this.loadCachedPartsList(targetJob);
        }
    }

    async cachePartsList(jobName, partsList) {
        try {
            const transaction = this.db.transaction(['parts_usage'], 'readwrite');
            const store = transaction.objectStore('parts_usage');

            // Clear existing cached parts for this job
            const existingParts = await store.index('job').getAll(jobName);
            for (const part of existingParts) {
                if (part.synced) {
                    await store.delete(part.id);
                }
            }

            // Cache new parts list
            for (const part of partsList) {
                const cachedPart = {
                    id: part.name,
                    job: jobName,
                    item_code: part.item_code,
                    item_name: part.item_name,
                    item_name_ar: part.item_name_ar,
                    quantity: part.quantity,
                    rate: part.rate,
                    amount: part.amount,
                    barcode: part.barcode,
                    timestamp: part.usage_time,
                    synced: true,
                    cached: true
                };
                await store.put(cachedPart);
            }
        } catch (error) {
            console.error('[TechnicianApp] Failed to cache parts list:', error);
        }
    }

    async loadCachedPartsList(jobName) {
        try {
            const transaction = this.db.transaction(['parts_usage'], 'readonly');
            const store = transaction.objectStore('parts_usage');
            const partsList = await store.index('job').getAll(jobName);

            // Calculate totals
            const totals = {
                total_parts: partsList.length,
                total_amount: partsList.reduce((sum, part) => sum + (part.amount || 0), 0)
            };

            this.renderPartsList(partsList, totals);
        } catch (error) {
            console.error('[TechnicianApp] Failed to load cached parts list:', error);
            this.renderPartsList([], { total_parts: 0, total_amount: 0 });
        }
    }

    renderPartsList(partsList, totals = null) {
        const partsListElement = document.getElementById('parts-list');
        if (!partsListElement) return;

        partsListElement.innerHTML = '';

        if (!partsList || partsList.length === 0) {
            partsListElement.innerHTML = `
                <div class="empty-state">
                    <i class="icon-package"></i>
                    <p>${this.lang === 'ar' ? 'لا توجد قطع مستخدمة' : 'No parts used'}</p>
                </div>
            `;
            return;
        }

        // Add parts summary
        if (totals) {
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'parts-summary';
            summaryDiv.innerHTML = `
                <div class="summary-header">
                    <h4>${this.lang === 'ar' ? 'ملخص القطع' : 'Parts Summary'}</h4>
                </div>
                <div class="summary-stats">
                    <div class="stat">
                        <span class="stat-label">${this.lang === 'ar' ? 'عدد القطع:' : 'Total Parts:'}</span>
                        <span class="stat-value">${totals.total_parts}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">${this.lang === 'ar' ? 'المجموع:' : 'Total Amount:'}</span>
                        <span class="stat-value">${totals.total_amount.toFixed(3)} OMR</span>
                    </div>
                </div>
            `;
            partsListElement.appendChild(summaryDiv);
        }

        // Add parts list
        const partsGrid = document.createElement('div');
        partsGrid.className = 'parts-grid';

        partsList.forEach(part => {
            const partItem = this.createPartItem(part);
            partsGrid.appendChild(partItem);
        });

        partsListElement.appendChild(partsGrid);
    }

    createPartItem(part) {
        const item = document.createElement('div');
        item.className = `part-item ${part.synced ? 'synced' : 'pending'}`;

        const syncStatus = part.synced ?
            '<i class="icon-check sync-status synced"></i>' :
            '<i class="icon-clock sync-status pending"></i>';

        const partName = this.lang === 'ar' && part.item_name_ar ?
            part.item_name_ar : part.item_name || part.item_code;

        item.innerHTML = `
            <div class="part-header">
                <div class="part-name">${partName}</div>
                ${syncStatus}
            </div>
            <div class="part-details">
                <div class="part-code">${this.lang === 'ar' ? 'الرمز:' : 'Code:'} ${part.item_code || part.barcode}</div>
                <div class="part-quantity">${this.lang === 'ar' ? 'الكمية:' : 'Qty:'} ${part.quantity}</div>
                <div class="part-rate">${this.lang === 'ar' ? 'السعر:' : 'Rate:'} ${(part.rate || 0).toFixed(3)} OMR</div>
                <div class="part-amount">${this.lang === 'ar' ? 'المجموع:' : 'Amount:'} ${(part.amount || 0).toFixed(3)} OMR</div>
            </div>
            <div class="part-meta">
                <span class="part-time">${this.formatTimestamp(part.timestamp || part.usage_time)}</span>
                ${!part.synced && !part.cached ? `
                    <button class="btn-small retry-sync" data-part-id="${part.id}">
                        <i class="icon-refresh"></i>
                        ${this.lang === 'ar' ? 'إعادة المحاولة' : 'Retry'}
                    </button>
                ` : ''}
            </div>
        `;

        // Add retry sync functionality
        const retryBtn = item.querySelector('.retry-sync');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.retryPartSync(part);
            });
        }

        return item;
    }

    async retryPartSync(part) {
        try {
            await this.syncPartUsage(part);
        } catch (error) {
            console.error('[TechnicianApp] Retry sync failed:', error);
            this.showError(this.getString('error'), 'Sync retry failed');
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString(this.lang === 'ar' ? 'ar-OM' : 'en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async updatePartsList() {
        const partsView = document.getElementById('parts-view');
        if (partsView && partsView.classList.contains('active')) {
            await this.loadPartsList();
        }
    }

    async addPartUsage(barcode, quantity = 1, notes = '') {
        try {
            if (!this.currentJob) {
                this.showError(this.getString('error'), 'Please select a job first');
                return;
            }

            // Create parts usage record
            const partUsage = {
                id: `part_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                job: this.currentJob.name,
                barcode: barcode,
                quantity: quantity,
                timestamp: new Date().toISOString(),
                technician: this.currentUser.technician?.name,
                notes: notes,
                synced: false
            };

            // Save to IndexedDB
            const transaction = this.db.transaction(['parts_usage'], 'readwrite');
            const store = transaction.objectStore('parts_usage');
            await store.add(partUsage);

            // Queue for sync if online
            if (this.isOnline) {
                await this.syncPartUsage(partUsage);
            }

            // Update parts list if visible
            this.updatePartsList();

            this.showNotification(
                this.getString('partScanned') || 'Part Scanned',
                `${this.lang === 'ar' ? 'الرمز:' : 'Code:'} ${barcode}`
            );

        } catch (error) {
            console.error('[TechnicianApp] Failed to add part usage:', error);
            this.showError(this.getString('error'), 'Failed to record part usage');
        }
    }
}

// Time Tracker Class
class TimeTracker {
    constructor() {
        this.startTime = null;
        this.elapsedTime = 0;
        this.workTime = 0; // Time actually working (excluding breaks)
        this.isRunning = false;
        this.isOnBreak = false;
        this.currentJob = null;
        this.interval = null;
        this.currentBreak = null;
        this.breaks = []; // History of breaks
        this.breakTypes = {
            ar: {
                prayer: 'صلاة',
                lunch: 'غداء',
                rest: 'استراحة',
                technical: 'مشكلة تقنية',
                material: 'انتظار قطع',
                emergency: 'طارئ',
                other: 'أخرى'
            },
            en: {
                prayer: 'Prayer',
                lunch: 'Lunch',
                rest: 'Rest Break',
                technical: 'Technical Issue',
                material: 'Waiting for Parts',
                emergency: 'Emergency',
                other: 'Other'
            }
        };
    }

    start(job) {
        if (!job) return;

        this.currentJob = job;
        this.startTime = Date.now() - this.elapsedTime;
        this.isRunning = true;
        this.isOnBreak = false;

        this.updateUI();
        this.startInterval();

        // Save to offline storage
        this.saveTimeLog('start');

        technicianApp.showNotification(
            technicianApp.getString('timeStarted'),
            `${technicianApp.lang === 'ar' ? 'للمهمة:' : 'for job:'} ${job.title}`
        );
    }

    pause() {
        if (!this.isRunning) return;

        this.isRunning = false;
        this.stopInterval();
        this.saveTimeLog('pause');
        this.updateUI();
    }

    resume() {
        if (this.isRunning || !this.startTime) return;

        this.startTime = Date.now() - this.elapsedTime;
        this.isRunning = true;
        this.isOnBreak = false;

        this.startInterval();
        this.saveTimeLog('resume');
        this.updateUI();
    }

    startBreak(breakType = 'rest', reason = '') {
        if (!this.isRunning) return;

        const now = Date.now();
        this.currentBreak = {
            id: `break_${now}_${Math.random().toString(36).substr(2, 9)}`,
            type: breakType,
            reason: reason,
            startTime: now,
            endTime: null,
            duration: 0
        };

        this.isOnBreak = true;
        this.isRunning = false;
        this.stopInterval();

        this.saveTimeLog('break_start', { breakType, reason });
        this.updateUI();
        this.updateBreakHistory();

        const breakText = this.breakTypes[technicianApp.lang][breakType];
        technicianApp.showNotification(
            technicianApp.lang === 'ar' ? 'بدء الاستراحة' : 'Break Started',
            breakText
        );
    }

    endBreak() {
        if (!this.isOnBreak || !this.currentBreak) return;

        const now = Date.now();
        this.currentBreak.endTime = now;
        this.currentBreak.duration = now - this.currentBreak.startTime;

        this.breaks.push({ ...this.currentBreak });
        this.currentBreak = null;
        this.isOnBreak = false;

        // Resume work timer
        this.startTime = now - this.elapsedTime;
        this.isRunning = true;
        this.startInterval();

        this.saveTimeLog('break_end');
        this.updateUI();
        this.updateBreakHistory();

        technicianApp.showNotification(
            technicianApp.lang === 'ar' ? 'انتهاء الاستراحة' : 'Break Ended',
            technicianApp.lang === 'ar' ? 'تم استئناف العمل' : 'Work resumed'
        );
    }

    stop() {
        if (!this.startTime) return;

        // End any active break
        if (this.isOnBreak && this.currentBreak) {
            this.endBreak();
        }

        this.isRunning = false;
        this.stopInterval();
        this.saveTimeLog('stop');

        // Calculate total work time (excluding breaks)
        this.calculateWorkTime();

        // Reset
        this.startTime = null;
        this.elapsedTime = 0;
        this.workTime = 0;
        this.currentJob = null;
        this.breaks = [];

        this.updateUI();

        technicianApp.showNotification(
            technicianApp.getString('timeStopped'),
            ''
        );
    }

    calculateWorkTime() {
        if (!this.startTime) return;

        const totalTime = this.elapsedTime;
        const totalBreakTime = this.breaks.reduce((sum, breakItem) => sum + breakItem.duration, 0);
        this.workTime = totalTime - totalBreakTime;
    }

    showBreakModal() {
        const modal = document.createElement('div');
        modal.className = 'break-modal-overlay';
        modal.innerHTML = `
            <div class="break-modal">
                <div class="break-modal-header">
                    <h3>${technicianApp.lang === 'ar' ? 'نوع الاستراحة' : 'Break Type'}</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="break-modal-body">
                    <div class="break-types-grid">
                        ${Object.entries(this.breakTypes[technicianApp.lang]).map(([type, label]) => `
                            <button class="break-type-btn" data-break-type="${type}">
                                <i class="break-icon break-icon-${type}"></i>
                                <span>${label}</span>
                            </button>
                        `).join('')}
                    </div>
                    <div class="break-reason-section">
                        <label>${technicianApp.lang === 'ar' ? 'ملاحظات (اختياري)' : 'Notes (Optional)'}</label>
                        <textarea id="break-reason" placeholder="${technicianApp.lang === 'ar' ? 'أدخل ملاحظات إضافية...' : 'Enter additional notes...'}" rows="3"></textarea>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('.close-modal').onclick = () => modal.remove();
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

        modal.querySelectorAll('.break-type-btn').forEach(btn => {
            btn.onclick = () => {
                const breakType = btn.dataset.breakType;
                const reason = modal.querySelector('#break-reason').value;
                this.startBreak(breakType, reason);
                modal.remove();
            };
        });
    }

    showManualTimeEntry() {
        const modal = document.createElement('div');
        modal.className = 'manual-time-modal-overlay';
        modal.innerHTML = `
            <div class="manual-time-modal">
                <div class="manual-time-header">
                    <h3>${technicianApp.lang === 'ar' ? 'إدخال الوقت يدوياً' : 'Manual Time Entry'}</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="manual-time-body">
                    <div class="time-inputs">
                        <div class="input-group">
                            <label>${technicianApp.lang === 'ar' ? 'الساعات' : 'Hours'}</label>
                            <input type="number" id="manual-hours" min="0" max="23" value="0">
                        </div>
                        <div class="input-group">
                            <label>${technicianApp.lang === 'ar' ? 'الدقائق' : 'Minutes'}</label>
                            <input type="number" id="manual-minutes" min="0" max="59" value="0">
                        </div>
                    </div>
                    <div class="manual-time-reason">
                        <label>${technicianApp.lang === 'ar' ? 'السبب' : 'Reason'}</label>
                        <textarea id="manual-reason" placeholder="${technicianApp.lang === 'ar' ? 'لماذا تم إدخال الوقت يدوياً؟' : 'Why was time entered manually?'}" rows="3" required></textarea>
                    </div>
                    <div class="manual-time-actions">
                        <button class="cancel-btn">${technicianApp.lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
                        <button class="save-btn">${technicianApp.lang === 'ar' ? 'حفظ' : 'Save'}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('.close-modal').onclick = () => modal.remove();
        modal.querySelector('.cancel-btn').onclick = () => modal.remove();
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

        modal.querySelector('.save-btn').onclick = () => {
            const hours = parseInt(modal.querySelector('#manual-hours').value) || 0;
            const minutes = parseInt(modal.querySelector('#manual-minutes').value) || 0;
            const reason = modal.querySelector('#manual-reason').value.trim();

            if (!reason) {
                alert(technicianApp.lang === 'ar' ? 'يرجى إدخال السبب' : 'Please enter a reason');
                return;
            }

            const totalMinutes = (hours * 60) + minutes;
            if (totalMinutes <= 0) {
                alert(technicianApp.lang === 'ar' ? 'يرجى إدخال وقت صحيح' : 'Please enter valid time');
                return;
            }

            this.addManualTime(totalMinutes, reason);
            modal.remove();
        };
    }

    addManualTime(minutes, reason) {
        const manualTime = minutes * 60 * 1000; // Convert to milliseconds
        this.elapsedTime += manualTime;
        this.workTime += manualTime;

        this.saveTimeLog('manual_entry', { minutes, reason });
        this.updateDisplay();

        technicianApp.showNotification(
            technicianApp.lang === 'ar' ? 'تم إضافة الوقت' : 'Time Added',
            `${minutes} ${technicianApp.lang === 'ar' ? 'دقيقة' : 'minutes'}`
        );
    }

    startInterval() {
        this.interval = setInterval(() => {
            this.updateDisplay();
        }, 1000);
    }

    stopInterval() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    updateDisplay() {
        if (this.isRunning) {
            this.elapsedTime = Date.now() - this.startTime;
        }

        // Update current break time if on break
        if (this.isOnBreak && this.currentBreak) {
            this.currentBreak.duration = Date.now() - this.currentBreak.startTime;
        }

        this.calculateWorkTime();

        // Update timer display
        const display = document.getElementById('timer-display');
        if (display) {
            display.textContent = this.formatTime(this.elapsedTime);
        }

        // Update time summary
        this.updateTimeSummary();
    }

    updateTimeSummary() {
        const workTimeEl = document.getElementById('work-time');
        const breakTimeEl = document.getElementById('break-time');
        const totalTimeEl = document.getElementById('total-time');

        if (workTimeEl) workTimeEl.textContent = this.formatTime(this.workTime);

        const totalBreakTime = this.breaks.reduce((sum, br) => sum + br.duration, 0) +
            (this.currentBreak ? this.currentBreak.duration : 0);
        if (breakTimeEl) breakTimeEl.textContent = this.formatTime(totalBreakTime);
        if (totalTimeEl) totalTimeEl.textContent = this.formatTime(this.elapsedTime);
    }

    updateBreakHistory() {
        const historyEl = document.getElementById('break-history');
        if (!historyEl) return;

        const allBreaks = [...this.breaks];
        if (this.currentBreak) {
            allBreaks.push({ ...this.currentBreak, duration: this.currentBreak.duration });
        }

        historyEl.innerHTML = allBreaks.map(br => `
            <div class="break-history-item ${br.endTime ? 'completed' : 'active'}">
                <div class="break-info">
                    <span class="break-type">${this.breakTypes[technicianApp.lang][br.type]}</span>
                    <span class="break-duration">${this.formatTime(br.duration)}</span>
                </div>
                <div class="break-time">
                    ${new Date(br.startTime).toLocaleTimeString()} 
                    ${br.endTime ? '- ' + new Date(br.endTime).toLocaleTimeString() : '- ' + (technicianApp.lang === 'ar' ? 'جاري' : 'ongoing')}
                </div>
                ${br.reason ? `<div class="break-reason">${br.reason}</div>` : ''}
            </div>
        `).join('');
    }

    formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    updateUI() {
        const startBtn = document.getElementById('start-timer');
        const pauseBtn = document.getElementById('pause-timer');
        const resumeBtn = document.getElementById('resume-timer');
        const stopBtn = document.getElementById('stop-timer');
        const breakBtn = document.getElementById('break-timer');
        const endBreakBtn = document.getElementById('end-break-timer');

        if (this.isOnBreak) {
            // On break state
            if (startBtn) startBtn.disabled = true;
            if (pauseBtn) pauseBtn.disabled = true;
            if (resumeBtn) resumeBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            if (breakBtn) breakBtn.style.display = 'none';
            if (endBreakBtn) endBreakBtn.style.display = 'block';
        } else if (this.isRunning) {
            // Running state
            if (startBtn) startBtn.disabled = true;
            if (pauseBtn) pauseBtn.disabled = false;
            if (resumeBtn) resumeBtn.style.display = 'none';
            if (stopBtn) stopBtn.disabled = false;
            if (breakBtn) breakBtn.disabled = false;
            if (endBreakBtn) endBreakBtn.style.display = 'none';
        } else if (this.startTime) {
            // Paused state
            if (startBtn) startBtn.disabled = true;
            if (pauseBtn) pauseBtn.disabled = true;
            if (resumeBtn) resumeBtn.style.display = 'block';
            if (stopBtn) stopBtn.disabled = false;
            if (breakBtn) breakBtn.disabled = true;
            if (endBreakBtn) endBreakBtn.style.display = 'none';
        } else {
            // Stopped state
            if (startBtn) startBtn.disabled = !this.currentJob;
            if (pauseBtn) pauseBtn.disabled = true;
            if (resumeBtn) resumeBtn.style.display = 'none';
            if (stopBtn) stopBtn.disabled = true;
            if (breakBtn) breakBtn.disabled = true;
            if (endBreakBtn) endBreakBtn.style.display = 'none';
        }

        // Update status display
        const statusEl = document.getElementById('timer-status');
        if (statusEl) {
            let status = '';
            if (this.isOnBreak) {
                const breakType = this.currentBreak ? this.breakTypes[technicianApp.lang][this.currentBreak.type] : '';
                status = `${technicianApp.lang === 'ar' ? 'استراحة' : 'On Break'}: ${breakType}`;
            } else if (this.isRunning) {
                status = technicianApp.lang === 'ar' ? 'يعمل' : 'Working';
            } else if (this.startTime) {
                status = technicianApp.lang === 'ar' ? 'متوقف مؤقتاً' : 'Paused';
            } else {
                status = technicianApp.lang === 'ar' ? 'متوقف' : 'Stopped';
            }
            statusEl.textContent = status;
        }
    }

    async saveTimeLog(action, additionalData = {}) {
        const timeLog = {
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            job: this.currentJob?.name,
            action: action,
            timestamp: new Date().toISOString(),
            elapsed_time: this.elapsedTime,
            work_time: this.workTime,
            breaks: this.breaks,
            current_break: this.currentBreak,
            additional_data: additionalData,
            synced: false
        };

        // Save to IndexedDB
        const transaction = technicianApp.db.transaction(['time_logs'], 'readwrite');
        const store = transaction.objectStore('time_logs');
        await store.add(timeLog);

        // Queue for sync
        if (technicianApp.isOnline) {
            technicianApp.syncTimeLog(timeLog);
        }
    }
}

// Media Capture Class
class MediaCapture {
    constructor() {
        this.stream = null;
        this.mediaRecorder = null;
        this.recordedChunks = [];
    }

    async takePhoto(job) {
        if (!job) {
            technicianApp.showError(technicianApp.getString('error'), 'Please select a job first');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            // Create video element for preview
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            // Create capture overlay
            const overlay = this.createCaptureOverlay(video, stream, 'photo', job);
            document.body.appendChild(overlay);

        } catch (error) {
            console.error('[MediaCapture] Camera access failed:', error);
            technicianApp.showError(technicianApp.getString('error'), 'Camera access denied');
        }
    }

    async recordVideo(job) {
        if (!job) {
            technicianApp.showError(technicianApp.getString('error'), 'Please select a job first');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: true
            });

            // Create video element for preview
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            // Create capture overlay
            const overlay = this.createCaptureOverlay(video, stream, 'video', job);
            document.body.appendChild(overlay);

        } catch (error) {
            console.error('[MediaCapture] Camera access failed:', error);
            technicianApp.showError(technicianApp.getString('error'), 'Camera/microphone access denied');
        }
    }

    createCaptureOverlay(video, stream, type, job) {
        const overlay = document.createElement('div');
        overlay.className = 'capture-overlay';
        overlay.innerHTML = `
            <div class="capture-container">
                <div class="capture-header">
                    <h3>${technicianApp.lang === 'ar' ? (type === 'photo' ? 'التقاط صورة' : 'تسجيل فيديو') : (type === 'photo' ? 'Take Photo' : 'Record Video')}</h3>
                    <button class="close-capture">&times;</button>
                </div>
                <div class="capture-preview"></div>
                <div class="capture-controls">
                    ${type === 'photo' ?
                `<button class="capture-btn photo-btn">
                            <i class="icon-camera"></i>
                        </button>` :
                `<button class="capture-btn record-btn">
                            <i class="icon-record"></i>
                        </button>
                        <button class="capture-btn stop-btn" style="display: none;">
                            <i class="icon-stop"></i>
                        </button>`
            }
                </div>
            </div>
        `;

        // Add video to preview
        overlay.querySelector('.capture-preview').appendChild(video);

        // Event listeners
        overlay.querySelector('.close-capture').addEventListener('click', () => {
            this.stopCapture(stream, overlay);
        });

        if (type === 'photo') {
            overlay.querySelector('.photo-btn').addEventListener('click', () => {
                this.capturePhoto(video, stream, overlay, job);
            });
        } else {
            const recordBtn = overlay.querySelector('.record-btn');
            const stopBtn = overlay.querySelector('.stop-btn');

            recordBtn.addEventListener('click', () => {
                this.startVideoRecording(stream, recordBtn, stopBtn);
            });

            stopBtn.addEventListener('click', () => {
                this.stopVideoRecording(stream, overlay, job);
            });
        }

        return overlay;
    }

    capturePhoto(video, stream, overlay, job) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        canvas.toBlob(async (blob) => {
            await this.saveMedia(blob, 'photo', job);
            this.stopCapture(stream, overlay);

            technicianApp.showNotification(
                technicianApp.getString('photoTaken'),
                `${technicianApp.lang === 'ar' ? 'للمهمة:' : 'for job:'} ${job.title}`
            );
        }, 'image/jpeg', 0.8);
    }

    startVideoRecording(stream, recordBtn, stopBtn) {
        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'video/webm;codecs=vp8,opus'
        });

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.start(1000); // Record in 1-second chunks
        recordBtn.style.display = 'none';
        stopBtn.style.display = 'block';

        // Add recording indicator
        this.addRecordingIndicator(stopBtn.parentElement);
    }

    addRecordingIndicator(container) {
        const indicator = document.createElement('div');
        indicator.className = 'recording-indicator';
        indicator.innerHTML = `
            <div class="recording-dot"></div>
            <span>${technicianApp.lang === 'ar' ? 'جاري التسجيل' : 'Recording'}</span>
        `;
        container.appendChild(indicator);
    }

    stopVideoRecording(stream, overlay, job) {
        this.mediaRecorder.stop();

        this.mediaRecorder.onstop = async () => {
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });

            // Compress video if too large (> 50MB)
            const compressedBlob = await this.compressVideo(blob);

            await this.saveMedia(compressedBlob, 'video', job);
            this.stopCapture(stream, overlay);

            technicianApp.showNotification(
                technicianApp.getString('videoRecorded') || technicianApp.getString('photoTaken'),
                `${technicianApp.lang === 'ar' ? 'للمهمة:' : 'for job:'} ${job.title}`
            );
        };
    }

    async compressVideo(blob) {
        // Basic video compression - in production, use a proper video compression library
        if (blob.size < 50 * 1024 * 1024) { // Less than 50MB
            return blob;
        }

        // For now, just return the original blob
        // In production, implement proper video compression
        return blob;
    }

    async compressImage(blob, quality = 0.8, maxWidth = 1920, maxHeight = 1080) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                // Calculate new dimensions
                let { width, height } = this.calculateNewDimensions(
                    img.width, img.height, maxWidth, maxHeight
                );

                canvas.width = width;
                canvas.height = height;

                // Draw and compress
                ctx.drawImage(img, 0, 0, width, height);
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };
            img.src = URL.createObjectURL(blob);
        });
    }

    calculateNewDimensions(width, height, maxWidth, maxHeight) {
        if (width <= maxWidth && height <= maxHeight) {
            return { width, height };
        }

        const ratio = Math.min(maxWidth / width, maxHeight / height);
        return {
            width: Math.round(width * ratio),
            height: Math.round(height * ratio)
        };
    }

    stopCapture(stream, overlay) {
        stream.getTracks().forEach(track => track.stop());
        overlay.remove();
    }

    async saveMedia(blob, type, job) {
        // Compress image if needed
        if (type === 'photo') {
            blob = await this.compressImage(blob);
        }

        const media = {
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            job: job.name,
            type: type,
            filename: `${type}_${job.name}_${Date.now()}.${type === 'photo' ? 'jpg' : 'webm'}`,
            blob: blob,
            size: blob.size,
            timestamp: new Date().toISOString(),
            synced: false,
            uploadAttempts: 0,
            metadata: {
                jobTitle: job.title,
                customerName: job.customer_name,
                vehicleLicense: job.vehicle_license_plate,
                timestamp: new Date().toISOString()
            }
        };

        // Save to IndexedDB
        try {
            const transaction = technicianApp.db.transaction(['media'], 'readwrite');
            const store = transaction.objectStore('media');
            await store.add(media);

            // Add to upload queue if online
            if (technicianApp.isOnline) {
                await this.queueForUpload(media);
            }

            // Update media gallery if visible
            this.updateMediaGallery();

            return media;
        } catch (error) {
            console.error('[MediaCapture] Failed to save media:', error);
            throw error;
        }
    }

    async queueForUpload(media) {
        // Add to sync queue
        const syncItem = {
            id: `media_${media.id}`,
            type: 'media_upload',
            data: media,
            attempts: 0,
            created: new Date().toISOString()
        };

        const transaction = technicianApp.db.transaction(['sync_queue'], 'readwrite');
        const store = transaction.objectStore('sync_queue');
        await store.add(syncItem);

        // Attempt immediate upload if online
        if (technicianApp.isOnline) {
            this.uploadMedia(media);
        }
    }

    async uploadMedia(media) {
        try {
            // Convert blob to base64
            const base64Data = await this.blobToBase64(media.blob);

            const response = await technicianApp.apiCall('save_media_file', {
                service_order: media.job,
                file_data: base64Data,
                file_name: media.filename,
                file_type: media.type,
                metadata: media.metadata
            });

            if (response.success) {
                // Mark as synced
                await this.markMediaAsSynced(media.id, response.file_url);

                technicianApp.showNotification(
                    technicianApp.getString('syncComplete'),
                    `${technicianApp.lang === 'ar' ? 'تم رفع' : 'Uploaded'} ${media.filename}`
                );
            }
        } catch (error) {
            console.error('[MediaCapture] Upload failed:', error);
            media.uploadAttempts = (media.uploadAttempts || 0) + 1;

            // Retry up to 3 times
            if (media.uploadAttempts < 3) {
                setTimeout(() => this.uploadMedia(media), 5000 * media.uploadAttempts);
            }
        }
    }

    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    async markMediaAsSynced(mediaId, fileUrl) {
        const transaction = technicianApp.db.transaction(['media'], 'readwrite');
        const store = transaction.objectStore('media');

        const media = await store.get(mediaId);
        if (media) {
            media.synced = true;
            media.fileUrl = fileUrl;
            media.syncedAt = new Date().toISOString();
            await store.put(media);
        }
    }

    async updateMediaGallery() {
        const mediaView = document.getElementById('media-view');
        if (mediaView && mediaView.classList.contains('active')) {
            // Refresh media gallery
            this.renderMediaGallery();
        }
    }

    async renderMediaGallery() {
        const gallery = document.getElementById('media-gallery');
        if (!gallery) return;

        try {
            const transaction = technicianApp.db.transaction(['media'], 'readonly');
            const store = transaction.objectStore('media');
            const mediaFiles = await store.getAll();

            gallery.innerHTML = '';

            if (mediaFiles.length === 0) {
                gallery.innerHTML = `
                    <div class="empty-state">
                        <i class="icon-camera"></i>
                        <p>${technicianApp.lang === 'ar' ? 'لا توجد ملفات وسائط' : 'No media files'}</p>
                    </div>
                `;
                return;
            }

            // Group by job
            const groupedMedia = {};
            mediaFiles.forEach(media => {
                if (!groupedMedia[media.job]) {
                    groupedMedia[media.job] = [];
                }
                groupedMedia[media.job].push(media);
            });

            // Render grouped media
            Object.entries(groupedMedia).forEach(([jobName, files]) => {
                const jobSection = document.createElement('div');
                jobSection.className = 'media-job-section';

                const job = files[0].metadata;
                jobSection.innerHTML = `
                    <div class="media-job-header">
                        <h4>${job.jobTitle || jobName}</h4>
                        <span class="media-count">${files.length} ${technicianApp.lang === 'ar' ? 'ملف' : 'files'}</span>
                    </div>
                    <div class="media-grid" data-job="${jobName}"></div>
                `;

                const grid = jobSection.querySelector('.media-grid');
                files.forEach(media => {
                    const mediaItem = this.createMediaItem(media);
                    grid.appendChild(mediaItem);
                });

                gallery.appendChild(jobSection);
            });

        } catch (error) {
            console.error('[MediaCapture] Failed to render gallery:', error);
        }
    }

    createMediaItem(media) {
        const item = document.createElement('div');
        item.className = `media-item ${media.type}`;

        const syncStatus = media.synced ?
            '<i class="icon-check sync-status synced"></i>' :
            '<i class="icon-clock sync-status pending"></i>';

        item.innerHTML = `
            <div class="media-preview">
                ${media.type === 'photo' ?
                '<i class="icon-image"></i>' :
                '<i class="icon-video"></i>'
            }
            </div>
            <div class="media-info">
                <div class="media-filename">${media.filename}</div>
                <div class="media-meta">
                    <span class="media-size">${this.formatFileSize(media.size)}</span>
                    <span class="media-time">${this.formatTimestamp(media.timestamp)}</span>
                    ${syncStatus}
                </div>
            </div>
        `;

        // Add click handler to view/download
        item.addEventListener('click', () => {
            this.viewMedia(media);
        });

        return item;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString(technicianApp.lang === 'ar' ? 'ar-OM' : 'en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async viewMedia(media) {
        // Create media viewer overlay
        const overlay = document.createElement('div');
        overlay.className = 'media-viewer-overlay';

        const blobUrl = URL.createObjectURL(media.blob);

        overlay.innerHTML = `
            <div class="media-viewer">
                <div class="media-viewer-header">
                    <h3>${media.filename}</h3>
                    <button class="close-viewer">&times;</button>
                </div>
                <div class="media-viewer-content">
                    ${media.type === 'photo' ?
                `<img src="${blobUrl}" alt="${media.filename}">` :
                `<video src="${blobUrl}" controls></video>`
            }
                </div>
                <div class="media-viewer-actions">
                    <button class="btn download-btn">
                        <i class="icon-download"></i>
                        ${technicianApp.lang === 'ar' ? 'تحميل' : 'Download'}
                    </button>
                    ${!media.synced ? `
                        <button class="btn upload-btn">
                            <i class="icon-upload"></i>
                            ${technicianApp.lang === 'ar' ? 'رفع' : 'Upload'}
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Event listeners
        overlay.querySelector('.close-viewer').addEventListener('click', () => {
            URL.revokeObjectURL(blobUrl);
            overlay.remove();
        });

        overlay.querySelector('.download-btn').addEventListener('click', () => {
            this.downloadMedia(media, blobUrl);
        });

        const uploadBtn = overlay.querySelector('.upload-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                this.uploadMedia(media);
                overlay.remove();
            });
        }

        document.body.appendChild(overlay);
    }

    downloadMedia(media, blobUrl) {
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = media.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
}

// Enhanced Barcode Scanner Class with QuaggaJS integration
class BarcodeScanner {
    constructor() {
        this.isScanning = false;
        this.quaggaLoaded = false;
        this.detectionActive = false;
    }

    async loadQuaggaJS() {
        if (this.quaggaLoaded) return true;

        try {
            // Load QuaggaJS library dynamically
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js';

            return new Promise((resolve, reject) => {
                script.onload = () => {
                    this.quaggaLoaded = true;
                    resolve(true);
                };
                script.onerror = () => reject(new Error('Failed to load QuaggaJS'));
                document.head.appendChild(script);
            });
        } catch (error) {
            console.warn('[BarcodeScanner] QuaggaJS not available, using fallback');
            return false;
        }
    }

    async scan() {
        if (this.isScanning) return;

        try {
            this.isScanning = true;

            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            const overlay = this.createScannerOverlay(stream);
            document.body.appendChild(overlay);

            // Try to load QuaggaJS for real barcode detection
            const quaggaAvailable = await this.loadQuaggaJS();

            if (quaggaAvailable) {
                this.startQuaggaDetection(overlay);
            } else {
                this.startFallbackDetection(overlay);
            }

        } catch (error) {
            console.error('[BarcodeScanner] Camera access failed:', error);
            technicianApp.showError(technicianApp.getString('error'), 'Camera access denied');
            this.isScanning = false;
        }
    }

    createScannerOverlay(stream) {
        const overlay = document.createElement('div');
        overlay.className = 'scanner-overlay';
        overlay.innerHTML = `
            <div class="scanner-container">
                <div class="scanner-header">
                    <h3>${technicianApp.lang === 'ar' ? 'مسح الباركود' : 'Scan Barcode'}</h3>
                    <div class="scanner-controls">
                        <button class="flashlight-btn" id="flashlight-btn">
                            <i class="icon-flashlight"></i>
                        </button>
                        <button class="close-scanner">&times;</button>
                    </div>
                </div>
                <div class="scanner-preview">
                    <video id="scanner-video" autoplay playsinline></video>
                    <div class="scanner-frame">
                        <div class="scanner-corners">
                            <div class="corner top-left"></div>
                            <div class="corner top-right"></div>
                            <div class="corner bottom-left"></div>
                            <div class="corner bottom-right"></div>
                        </div>
                    </div>
                    <div class="scanner-line"></div>
                </div>
                <div class="scanner-instructions">
                    <p>${technicianApp.lang === 'ar' ? 'ضع الباركود داخل الإطار' : 'Place barcode within the frame'}</p>
                    <div class="manual-entry">
                        <button class="btn manual-entry-btn">
                            <i class="icon-edit"></i>
                            ${technicianApp.lang === 'ar' ? 'إدخال يدوي' : 'Manual Entry'}
                        </button>
                    </div>
                </div>
                <div class="scanner-results" id="scanner-results"></div>
            </div>
        `;

        const video = overlay.querySelector('#scanner-video');
        video.srcObject = stream;

        // Event listeners
        overlay.querySelector('.close-scanner').addEventListener('click', () => {
            this.stopScanning(stream, overlay);
        });

        overlay.querySelector('.manual-entry-btn').addEventListener('click', () => {
            this.showManualEntry(stream, overlay);
        });

        const flashlightBtn = overlay.querySelector('#flashlight-btn');
        if (flashlightBtn) {
            flashlightBtn.addEventListener('click', () => {
                this.toggleFlashlight(stream, flashlightBtn);
            });
        }

        return overlay;
    }

    async startQuaggaDetection(overlay) {
        const video = overlay.querySelector('#scanner-video');

        try {
            await new Promise((resolve, reject) => {
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: video,
                        constraints: {
                            width: 1280,
                            height: 720,
                            facingMode: "environment"
                        }
                    },
                    decoder: {
                        readers: [
                            "code_128_reader",
                            "ean_reader",
                            "ean_8_reader",
                            "code_39_reader",
                            "code_93_reader",
                            "codabar_reader"
                        ]
                    },
                    locate: true,
                    locator: {
                        patchSize: "medium",
                        halfSample: true
                    }
                }, (err) => {
                    if (err) {
                        console.error('[BarcodeScanner] Quagga init failed:', err);
                        reject(err);
                        return;
                    }
                    resolve();
                });
            });

            Quagga.start();
            this.detectionActive = true;

            // Handle detection results
            Quagga.onDetected((result) => {
                const code = result.codeResult.code;
                this.onBarcodeDetected(code, overlay);
            });

            // Add visual feedback for detection attempts
            Quagga.onProcessed((result) => {
                const drawingCtx = Quagga.canvas.ctx.overlay;
                const drawingCanvas = Quagga.canvas.dom.overlay;

                if (result) {
                    if (result.boxes) {
                        drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                        result.boxes.filter(box => box !== result.box).forEach(box => {
                            Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { color: "green", lineWidth: 2 });
                        });
                    }

                    if (result.box) {
                        Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { color: "#00F", lineWidth: 2 });
                    }

                    if (result.codeResult && result.codeResult.code) {
                        Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { color: 'red', lineWidth: 3 });
                    }
                }
            });

        } catch (error) {
            console.error('[BarcodeScanner] Quagga detection failed:', error);
            this.startFallbackDetection(overlay);
        }
    }

    startFallbackDetection(overlay) {
        // Fallback: Manual detection simulation or pattern recognition
        const results = overlay.querySelector('#scanner-results');
        results.innerHTML = `
            <div class="fallback-message">
                <i class="icon-info"></i>
                <p>${technicianApp.lang === 'ar' ? 'استخدم الإدخال اليدوي للباركود' : 'Use manual entry for barcode'}</p>
            </div>
        `;

        // Simulate detection after delay (for demo purposes)
        setTimeout(() => {
            if (this.detectionActive) {
                // Show manual entry prompt
                this.showManualEntry(overlay.querySelector('#scanner-video').srcObject, overlay);
            }
        }, 5000);
    }

    showManualEntry(stream, overlay) {
        const manualEntryModal = document.createElement('div');
        manualEntryModal.className = 'manual-entry-modal';
        manualEntryModal.innerHTML = `
            <div class="manual-entry-content">
                <div class="manual-entry-header">
                    <h3>${technicianApp.lang === 'ar' ? 'إدخال الباركود يدوياً' : 'Manual Barcode Entry'}</h3>
                    <button class="close-manual-entry">&times;</button>
                </div>
                <div class="manual-entry-form">
                    <label>${technicianApp.lang === 'ar' ? 'رمز القطعة:' : 'Part Code:'}</label>
                    <input type="text" id="manual-barcode-input" placeholder="${technicianApp.lang === 'ar' ? 'أدخل رمز القطعة' : 'Enter part code'}" autocomplete="off">
                    <div class="manual-entry-actions">
                        <button class="btn btn-secondary cancel-manual">${technicianApp.lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
                        <button class="btn btn-primary confirm-manual">${technicianApp.lang === 'ar' ? 'تأكيد' : 'Confirm'}</button>
                    </div>
                </div>
            </div>
        `;

        const input = manualEntryModal.querySelector('#manual-barcode-input');
        const confirmBtn = manualEntryModal.querySelector('.confirm-manual');
        const cancelBtn = manualEntryModal.querySelector('.cancel-manual');
        const closeBtn = manualEntryModal.querySelector('.close-manual-entry');

        // Event listeners
        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                manualEntryModal.remove();
            });
        });

        confirmBtn.addEventListener('click', () => {
            const barcode = input.value.trim();
            if (barcode) {
                manualEntryModal.remove();
                this.onBarcodeDetected(barcode, overlay);
            }
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                confirmBtn.click();
            }
        });

        overlay.appendChild(manualEntryModal);

        // Focus input after a short delay
        setTimeout(() => input.focus(), 100);
    }

    async toggleFlashlight(stream, button) {
        try {
            const track = stream.getVideoTracks()[0];
            const capabilities = track.getCapabilities();

            if (capabilities.torch) {
                const settings = track.getSettings();
                const newTorchState = !settings.torch;

                await track.applyConstraints({
                    advanced: [{ torch: newTorchState }]
                });

                button.classList.toggle('active', newTorchState);
            }
        } catch (error) {
            console.warn('[BarcodeScanner] Flashlight not available:', error);
        }
    }

    async onBarcodeDetected(barcode, overlay) {
        // Stop detection
        if (this.quaggaLoaded && this.detectionActive) {
            Quagga.stop();
            this.detectionActive = false;
        }

        // Show detected barcode with part information
        const resultsDiv = overlay.querySelector('#scanner-results');
        resultsDiv.innerHTML = `
            <div class="barcode-result">
                <div class="barcode-detected">
                    <i class="icon-check"></i>
                    <span>${technicianApp.lang === 'ar' ? 'تم اكتشاف:' : 'Detected:'} ${barcode}</span>
                </div>
                <div class="barcode-actions">
                    <button class="btn use-part-btn">${technicianApp.lang === 'ar' ? 'استخدام القطعة' : 'Use Part'}</button>
                    <button class="btn scan-again-btn">${technicianApp.lang === 'ar' ? 'مسح آخر' : 'Scan Again'}</button>
                </div>
            </div>
        `;

        // Try to get part information
        try {
            const partInfo = await this.getPartInformation(barcode);
            if (partInfo) {
                this.showPartInformation(resultsDiv, partInfo);
            }
        } catch (error) {
            console.error('[BarcodeScanner] Failed to get part information:', error);
        }

        // Event listeners for actions
        resultsDiv.querySelector('.use-part-btn').addEventListener('click', () => {
            this.addPartUsage(barcode);
            this.stopScanning(overlay.querySelector('#scanner-video').srcObject, overlay);
        });

        resultsDiv.querySelector('.scan-again-btn').addEventListener('click', () => {
            this.startQuaggaDetection(overlay);
        });

        // Auto-close after 10 seconds
        setTimeout(() => {
            if (overlay.parentElement) {
                this.addPartUsage(barcode);
                this.stopScanning(overlay.querySelector('#scanner-video').srcObject, overlay);
            }
        }, 10000);
    }

    async getPartInformation(barcode) {
        try {
            const response = await technicianApp.apiCall('get_part_by_barcode', {
                barcode: barcode
            });
            return response.part;
        } catch (error) {
            console.error('[BarcodeScanner] Part lookup failed:', error);
            return null;
        }
    }

    showPartInformation(container, partInfo) {
        const partInfoDiv = document.createElement('div');
        partInfoDiv.className = 'part-information';
        partInfoDiv.innerHTML = `
            <div class="part-details">
                <h4>${partInfo.item_name || partInfo.item_name_ar || partInfo.item_code}</h4>
                <div class="part-meta">
                    <span class="part-code">${technicianApp.lang === 'ar' ? 'الرمز:' : 'Code:'} ${partInfo.item_code}</span>
                    <span class="part-price">${technicianApp.lang === 'ar' ? 'السعر:' : 'Price:'} ${partInfo.standard_rate || 0} OMR</span>
                    <span class="part-stock">${technicianApp.lang === 'ar' ? 'المخزون:' : 'Stock:'} ${partInfo.stock_qty || 0}</span>
                </div>
            </div>
        `;

        container.querySelector('.barcode-result').appendChild(partInfoDiv);
    }

    async addPartUsage(barcode) {
        try {
            if (!technicianApp.currentJob) {
                technicianApp.showError(technicianApp.getString('error'), 'Please select a job first');
                return;
            }

            // Create parts usage record
            const partUsage = {
                id: `part_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                job: technicianApp.currentJob.name,
                barcode: barcode,
                quantity: 1,
                timestamp: new Date().toISOString(),
                technician: technicianApp.currentUser.technician?.name,
                synced: false
            };

            // Save to IndexedDB
            const transaction = technicianApp.db.transaction(['parts_usage'], 'readwrite');
            const store = transaction.objectStore('parts_usage');
            await store.add(partUsage);

            // Queue for sync
            if (technicianApp.isOnline) {
                await technicianApp.syncPartUsage(partUsage);
            }

            technicianApp.showNotification(
                technicianApp.getString('partScanned') || 'Part Scanned',
                `${technicianApp.lang === 'ar' ? 'الرمز:' : 'Code:'} ${barcode}`
            );

        } catch (error) {
            console.error('[BarcodeScanner] Failed to add part usage:', error);
            technicianApp.showError(technicianApp.getString('error'), 'Failed to record part usage');
        }
    }

    stopScanning(stream, overlay) {
        this.isScanning = false;
        this.detectionActive = false;

        if (this.quaggaLoaded) {
            try {
                Quagga.stop();
            } catch (error) {
                console.warn('[BarcodeScanner] Error stopping Quagga:', error);
            }
        }

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        if (overlay && overlay.parentElement) {
            overlay.remove();
        }
    }
}

/**
 * Push Notification Manager
 * Handles push notification subscription and management
 */
class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.subscription = null;
        this.vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM90R-r-6eM7pF7QK_QrWkPzq6Kp-xCY1-qZKZZeU_LJkZyXKy7CJo'; // Configure in production
        this.permissionStatus = 'default';
        this.lang = navigator.language.startsWith('ar') ? 'ar' : 'en';

        this.strings = {
            ar: {
                permissionTitle: 'تفعيل الإشعارات',
                permissionMessage: 'هل تريد تلقي إشعارات للمهام الجديدة والتحديثات؟',
                subscribed: 'تم تفعيل الإشعارات',
                unsubscribed: 'تم إلغاء الإشعارات',
                error: 'خطأ في الإشعارات',
                allow: 'السماح',
                deny: 'رفض',
                testNotification: 'إشعار تجريبي'
            },
            en: {
                permissionTitle: 'Enable Notifications',
                permissionMessage: 'Would you like to receive notifications for new jobs and updates?',
                subscribed: 'Notifications enabled',
                unsubscribed: 'Notifications disabled',
                error: 'Notification error',
                allow: 'Allow',
                deny: 'Deny',
                testNotification: 'Test Notification'
            }
        };
    }

    async init() {
        if (!this.isSupported) {
            console.log('[PushNotifications] Push notifications not supported');
            return;
        }

        try {
            // Check current permission status
            this.permissionStatus = Notification.permission;

            // Get existing subscription
            const registration = await navigator.serviceWorker.ready;
            this.subscription = await registration.pushManager.getSubscription();

            // Auto-request permission if not set and no subscription exists
            if (this.permissionStatus === 'default') {
                setTimeout(() => this.requestPermission(), 3000); // Delay for better UX
            } else if (this.permissionStatus === 'granted' && !this.subscription) {
                // Permission granted but no subscription, create one
                await this.subscribe();
            }

            // Set up notification handlers
            this.setupNotificationHandlers();

            console.log('[PushNotifications] Initialized successfully');
        } catch (error) {
            console.error('[PushNotifications] Initialization failed:', error);
        }
    }

    async requestPermission() {
        try {
            // Show custom permission dialog first
            const result = await this.showPermissionDialog();

            if (result) {
                const permission = await Notification.requestPermission();
                this.permissionStatus = permission;

                if (permission === 'granted') {
                    await this.subscribe();
                    this.showMessage(this.getString('subscribed'));
                }
            }
        } catch (error) {
            console.error('[PushNotifications] Permission request failed:', error);
        }
    }

    async subscribe() {
        try {
            if (!this.isSupported || this.permissionStatus !== 'granted') {
                return false;
            }

            const registration = await navigator.serviceWorker.ready;

            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlB64ToUint8Array(this.vapidPublicKey)
            });

            this.subscription = subscription;

            // Send subscription to server
            const response = await this.apiCall('subscribe_to_notifications', {
                subscription_data: JSON.stringify(subscription.toJSON())
            });

            if (response.success) {
                console.log('[PushNotifications] Subscribed successfully');
                return true;
            } else {
                console.error('[PushNotifications] Server subscription failed:', response.message);
                return false;
            }

        } catch (error) {
            console.error('[PushNotifications] Subscription failed:', error);
            return false;
        }
    }

    async unsubscribe() {
        try {
            if (this.subscription) {
                await this.subscription.unsubscribe();
                this.subscription = null;
            }

            // Notify server
            await this.apiCall('unsubscribe_from_notifications');

            this.showMessage(this.getString('unsubscribed'));
            console.log('[PushNotifications] Unsubscribed successfully');

        } catch (error) {
            console.error('[PushNotifications] Unsubscribe failed:', error);
        }
    }

    async sendTestNotification() {
        try {
            const response = await this.apiCall('send_test_notification');

            if (response.success) {
                this.showMessage(this.getString('testNotification') + ' ✓');
            } else {
                this.showMessage(this.getString('error') + ': ' + response.message);
            }

        } catch (error) {
            console.error('[PushNotifications] Test notification failed:', error);
            this.showMessage(this.getString('error'));
        }
    }

    setupNotificationHandlers() {
        // Handle notification actions from service worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', event => {
                if (event.data && event.data.type === 'notification-click') {
                    this.handleNotificationClick(event.data);
                }
            });

            // Listen for push notifications received while app is visible
            navigator.serviceWorker.addEventListener('message', event => {
                if (event.data && event.data.type === 'push-received') {
                    this.handlePushReceived(event.data);
                }
            });
        }
    }

    handleNotificationClick(data) {
        console.log('[PushNotifications] Notification clicked:', data);

        // Navigate to appropriate view based on notification type
        if (data.type === 'job_assignment' && data.service_order) {
            // Switch to jobs view and highlight the specific job
            if (technicianApp) {
                technicianApp.switchView('jobs');
                technicianApp.selectJob(data.service_order);
            }
        } else if (data.type === 'priority_update' && data.service_order) {
            // Switch to jobs view and highlight the job
            if (technicianApp) {
                technicianApp.switchView('jobs');
                technicianApp.selectJob(data.service_order);
            }
        }
    }

    handlePushReceived(data) {
        console.log('[PushNotifications] Push received:', data);

        // Show in-app notification if app is visible
        if (document.visibilityState === 'visible') {
            this.showInAppNotification(data.title, data.body);
        }

        // Refresh jobs list if it's a job-related notification
        if (data.type === 'job_assignment' || data.type === 'priority_update') {
            if (technicianApp) {
                technicianApp.loadJobs();
            }
        }
    }

    showInAppNotification(title, message) {
        // Create in-app notification
        const notification = document.createElement('div');
        notification.className = 'in-app-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close" onclick="this.parentNode.remove()">×</button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    showPermissionDialog() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'permission-dialog-overlay';
            dialog.innerHTML = `
                <div class="permission-dialog">
                    <h3>${this.getString('permissionTitle')}</h3>
                    <p>${this.getString('permissionMessage')}</p>
                    <div class="dialog-buttons">
                        <button class="btn-allow">${this.getString('allow')}</button>
                        <button class="btn-deny">${this.getString('deny')}</button>
                    </div>
                </div>
            `;

            dialog.querySelector('.btn-allow').addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(true);
            });

            dialog.querySelector('.btn-deny').addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(false);
            });

            document.body.appendChild(dialog);
        });
    }

    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async apiCall(method, args = {}) {
        try {
            const response = await fetch(`/api/method/universal_workshop.www.technician.${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': await this.getCSRFToken()
                },
                body: JSON.stringify(args)
            });

            const data = await response.json();
            return data.message || data;

        } catch (error) {
            console.error('[PushNotifications] API call failed:', error);
            throw error;
        }
    }

    async getCSRFToken() {
        try {
            const response = await fetch('/api/method/frappe.auth.get_csrf_token');
            const data = await response.json();
            return data.csrf_token;
        } catch (error) {
            console.error('[PushNotifications] Failed to get CSRF token:', error);
            return '';
        }
    }

    getString(key) {
        return this.strings[this.lang][key] || this.strings.en[key];
    }

    showMessage(message) {
        // Use existing notification system from the main app
        if (technicianApp && technicianApp.showNotification) {
            technicianApp.showNotification('Notifications', message);
        } else {
            console.log('[PushNotifications] ' + message);
        }
    }

    getStatus() {
        return {
            supported: this.isSupported,
            permission: this.permissionStatus,
            subscribed: !!this.subscription
        };
    }
}

// Initialize app when DOM is ready
let technicianApp;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        technicianApp = new TechnicianApp();
    });
} else {
    technicianApp = new TechnicianApp();
}

// Global utility functions for external access
window.UW = window.UW || {};
window.UW.TechnicianApp = TechnicianApp;
window.UW.takePhoto = () => technicianApp?.mediaCapture.takePhoto(technicianApp.currentJob);
window.UW.scanBarcode = () => technicianApp?.barcodeScanner.scan();
window.UW.startTimer = () => technicianApp?.timeTracker.start(technicianApp.currentJob);
window.UW.stopTimer = () => technicianApp?.timeTracker.stop();
window.UW.testNotification = () => technicianApp?.pushNotifications.sendTestNotification(); 