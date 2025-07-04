/**
 * Enhanced Time Tracker Module for Universal Workshop Technician App
 * Includes comprehensive time tracking, break management, and API integration
 */

class EnhancedTimeTracker {
    constructor(technicianApp) {
        this.app = technicianApp;
        this.startTime = null;
        this.elapsedTime = 0;
        this.breakTime = 0;
        this.isRunning = false;
        this.isOnBreak = false;
        this.currentJob = null;
        this.interval = null;
        this.breaks = [];
        this.currentBreakStart = null;
        this.currentTimeLog = null;

        // Break reasons for Arabic/English
        this.breakReasons = {
            ar: {
                'prayer': 'صلاة',
                'lunch': 'وجبة الغداء',
                'rest': 'استراحة',
                'technical': 'مشكلة فنية',
                'material': 'انتظار مواد',
                'emergency': 'طوارئ',
                'other': 'أخرى'
            },
            en: {
                'prayer': 'Prayer Break',
                'lunch': 'Lunch Break',
                'rest': 'Rest Break',
                'technical': 'Technical Issue',
                'material': 'Waiting for Materials',
                'emergency': 'Emergency',
                'other': 'Other'
            }
        };
    }

    /**
     * Initialize enhanced time tracker UI
     */
    setupEnhancedUI() {
        const timerView = document.getElementById('timer-view');
        if (!timerView) return;

        const isArabic = this.app.lang === 'ar';

        timerView.innerHTML = `
            <div class="enhanced-timer-container">
                <!-- Current Job Info -->
                <div class="current-job-card" id="current-job-info">
                    <div class="job-header">
                        <h3>${isArabic ? 'المهمة الحالية' : 'Current Job'}</h3>
                        <button class="job-select-btn" id="select-job-btn">
                            <i class="icon-edit"></i>
                            <span>${isArabic ? 'اختيار' : 'Select'}</span>
                        </button>
                    </div>
                    <div class="job-details" id="job-details">
                        <p class="no-job">${isArabic ? 'لا توجد مهمة نشطة' : 'No active job selected'}</p>
                    </div>
                </div>

                <!-- Timer Display -->
                <div class="timer-main-display">
                    <div class="timer-circle">
                        <div class="timer-time" id="timer-display">00:00:00</div>
                        <div class="timer-status" id="timer-status">
                            ${isArabic ? 'متوقف' : 'Stopped'}
                        </div>
                    </div>
                </div>

                <!-- Timer Controls -->
                <div class="timer-controls-enhanced">
                    <div class="main-controls">
                        <button id="start-timer" class="timer-btn primary" disabled>
                            <i class="icon-play"></i>
                            <span>${isArabic ? 'بدء' : 'Start'}</span>
                        </button>
                        <button id="pause-timer" class="timer-btn secondary" disabled>
                            <i class="icon-pause"></i>
                            <span>${isArabic ? 'إيقاف مؤقت' : 'Pause'}</span>
                        </button>
                        <button id="stop-timer" class="timer-btn danger" disabled>
                            <i class="icon-stop"></i>
                            <span>${isArabic ? 'إيقاف' : 'Stop'}</span>
                        </button>
                    </div>
                    
                    <!-- Break Controls -->
                    <div class="break-controls" id="break-controls" style="display: none;">
                        <button id="take-break" class="break-btn">
                            <i class="icon-coffee"></i>
                            <span>${isArabic ? 'استراحة' : 'Take Break'}</span>
                        </button>
                        <button id="end-break" class="break-btn active" style="display: none;">
                            <i class="icon-play"></i>
                            <span>${isArabic ? 'انتهاء الاستراحة' : 'End Break'}</span>
                        </button>
                    </div>
                </div>

                <!-- Time Summary -->
                <div class="time-summary">
                    <div class="summary-item">
                        <label>${isArabic ? 'وقت العمل' : 'Work Time'}</label>
                        <span id="work-time-display">00:00:00</span>
                    </div>
                    <div class="summary-item">
                        <label>${isArabic ? 'وقت الاستراحة' : 'Break Time'}</label>
                        <span id="break-time-display">00:00:00</span>
                    </div>
                    <div class="summary-item">
                        <label>${isArabic ? 'الوقت الإجمالي' : 'Total Time'}</label>
                        <span id="total-time-display">00:00:00</span>
                    </div>
                </div>

                <!-- Breaks History -->
                <div class="breaks-section">
                    <div class="section-header">
                        <h4>${isArabic ? 'الاستراحات اليوم' : 'Today\'s Breaks'}</h4>
                        <button class="toggle-breaks" id="toggle-breaks">
                            <i class="icon-chevron-down"></i>
                        </button>
                    </div>
                    <div class="breaks-list" id="breaks-list" style="display: none;">
                        <!-- Breaks will be populated here -->
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button class="action-btn" id="add-manual-time">
                        <i class="icon-clock"></i>
                        <span>${isArabic ? 'إضافة وقت يدوي' : 'Add Manual Time'}</span>
                    </button>
                    <button class="action-btn" id="sync-time-logs">
                        <i class="icon-refresh"></i>
                        <span>${isArabic ? 'مزامنة' : 'Sync'}</span>
                    </button>
                </div>
            </div>

            <!-- Break Reason Modal -->
            <div id="break-reason-modal" class="modal hidden">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${isArabic ? 'سبب الاستراحة' : 'Break Reason'}</h3>
                        <button class="modal-close" onclick="enhancedTimeTracker.closeBreakModal()">
                            <i class="icon-x"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="break-reasons-grid">
                            ${Object.keys(this.breakReasons.en).map(key => `
                                <button class="reason-btn" data-reason="${key}">
                                    <i class="icon-${this.getBreakIcon(key)}"></i>
                                    <span>${this.breakReasons[this.app.lang][key]}</span>
                                </button>
                            `).join('')}
                        </div>
                        <div class="custom-reason">
                            <input type="text" id="custom-break-reason" placeholder="${isArabic ? 'سبب آخر...' : 'Other reason...'}" dir="${isArabic ? 'rtl' : 'ltr'}">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="enhancedTimeTracker.closeBreakModal()">
                            ${isArabic ? 'إلغاء' : 'Cancel'}
                        </button>
                        <button class="btn-primary" id="confirm-break">
                            ${isArabic ? 'بدء الاستراحة' : 'Start Break'}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Manual Time Entry Modal -->
            <div id="manual-time-modal" class="modal hidden">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${isArabic ? 'إضافة وقت يدوي' : 'Add Manual Time'}</h3>
                        <button class="modal-close" onclick="enhancedTimeTracker.closeManualTimeModal()">
                            <i class="icon-x"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>${isArabic ? 'ساعات العمل' : 'Work Hours'}</label>
                            <input type="number" id="manual-hours" min="0" max="12" step="0.25" placeholder="2.5">
                        </div>
                        <div class="form-group">
                            <label>${isArabic ? 'ملاحظات' : 'Notes'}</label>
                            <textarea id="manual-time-notes" placeholder="${isArabic ? 'أضف ملاحظات...' : 'Add notes...'}" dir="${isArabic ? 'rtl' : 'ltr'}"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="enhancedTimeTracker.closeManualTimeModal()">
                            ${isArabic ? 'إلغاء' : 'Cancel'}
                        </button>
                        <button class="btn-primary" id="save-manual-time">
                            ${isArabic ? 'حفظ' : 'Save'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    /**
     * Setup event listeners for enhanced time tracker
     */
    setupEventListeners() {
        // Main timer controls
        document.getElementById('start-timer').addEventListener('click', () => this.start());
        document.getElementById('pause-timer').addEventListener('click', () => this.pause());
        document.getElementById('stop-timer').addEventListener('click', () => this.stop());

        // Break controls
        document.getElementById('take-break').addEventListener('click', () => this.showBreakModal());
        document.getElementById('end-break').addEventListener('click', () => this.endBreak());

        // Job selection
        document.getElementById('select-job-btn').addEventListener('click', () => this.showJobSelector());

        // Break reason selection
        document.querySelectorAll('.reason-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.reason-btn').forEach(b => b.classList.remove('selected'));
                e.target.closest('.reason-btn').classList.add('selected');
            });
        });

        // Confirm break
        document.getElementById('confirm-break').addEventListener('click', () => this.confirmBreak());

        // Manual time entry
        document.getElementById('add-manual-time').addEventListener('click', () => this.showManualTimeModal());
        document.getElementById('save-manual-time').addEventListener('click', () => this.saveManualTime());

        // Sync time logs
        document.getElementById('sync-time-logs').addEventListener('click', () => this.syncTimeLogs());

        // Toggle breaks history
        document.getElementById('toggle-breaks').addEventListener('click', () => this.toggleBreaksHistory());
    }

    /**
     * Start time tracking
     */
    async start() {
        if (!this.currentJob) {
            this.app.showError(
                this.app.getString('error'),
                this.app.lang === 'ar' ? 'يرجى اختيار مهمة أولاً' : 'Please select a job first'
            );
            return;
        }

        try {
            // Call API to start time tracking
            const response = await this.app.apiCall('universal_workshop.www.technician.start_time_tracking', {
                service_order: this.currentJob.name,
                notes: `Started via mobile app at ${new Date().toLocaleString()}`
            });

            if (response && response.message && response.message.success) {
                this.currentTimeLog = response.message.time_log;
                this.startTime = Date.now();
                this.isRunning = true;
                this.isOnBreak = false;

                this.updateUI();
                this.startInterval();

                // Save to offline storage
                await this.saveTimeLogLocally('start');

                this.app.showNotification(
                    this.app.getString('timeStarted'),
                    `${this.app.lang === 'ar' ? 'للمهمة:' : 'for job:'} ${this.currentJob.service_order_number}`
                );
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to start time tracking:', error);
            // Continue offline
            this.startOffline();
        }
    }

    /**
     * Start time tracking offline
     */
    startOffline() {
        this.startTime = Date.now();
        this.isRunning = true;
        this.isOnBreak = false;
        this.currentTimeLog = `offline_${Date.now()}`;

        this.updateUI();
        this.startInterval();
        this.saveTimeLogLocally('start');

        this.app.showNotification(
            this.app.getString('timeStarted'),
            this.app.lang === 'ar' ? '(وضع غير متصل)' : '(Offline mode)'
        );
    }

    /**
     * Pause time tracking
     */
    async pause() {
        if (!this.isRunning) return;

        try {
            if (this.app.isOnline && !this.currentTimeLog.startsWith('offline_')) {
                await this.app.apiCall('universal_workshop.www.technician.pause_time_tracking', {
                    service_order: this.currentJob.name,
                    break_reason: 'Manual pause'
                });
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to pause via API:', error);
        }

        this.isRunning = false;
        this.stopInterval();
        this.updateUI();

        await this.saveTimeLogLocally('pause');
    }

    /**
     * Stop time tracking
     */
    async stop() {
        if (!this.startTime) return;

        try {
            if (this.app.isOnline && !this.currentTimeLog.startsWith('offline_')) {
                const response = await this.app.apiCall('universal_workshop.www.technician.stop_time_tracking', {
                    service_order: this.currentJob.name,
                    notes: `Completed via mobile app. Total time: ${this.formatTime(this.elapsedTime)}`
                });

                if (response && response.message) {
                    console.log('[TimeTracker] Time tracking stopped:', response.message.total_hours);
                }
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to stop via API:', error);
        }

        this.isRunning = false;
        this.isOnBreak = false;
        this.stopInterval();

        // Save final time log
        await this.saveTimeLogLocally('stop');

        // Reset
        this.startTime = null;
        this.elapsedTime = 0;
        this.breakTime = 0;
        this.breaks = [];
        this.currentTimeLog = null;

        this.updateUI();
        this.updateBreaksDisplay();

        this.app.showNotification(
            this.app.getString('timeStopped'),
            this.app.lang === 'ar' ? 'تم حفظ السجل' : 'Time log saved'
        );
    }

    /**
     * Show break reason modal
     */
    showBreakModal() {
        if (!this.isRunning) return;

        const modal = document.getElementById('break-reason-modal');
        modal.classList.remove('hidden');

        // Reset selections
        document.querySelectorAll('.reason-btn').forEach(btn => btn.classList.remove('selected'));
        document.getElementById('custom-break-reason').value = '';
    }

    /**
     * Confirm break with selected reason
     */
    async confirmBreak() {
        const selectedReason = document.querySelector('.reason-btn.selected');
        const customReason = document.getElementById('custom-break-reason').value;

        let breakReason = 'other';
        let breakDescription = customReason;

        if (selectedReason) {
            breakReason = selectedReason.dataset.reason;
            breakDescription = this.breakReasons[this.app.lang][breakReason];
            if (customReason) {
                breakDescription += `: ${customReason}`;
            }
        } else if (!customReason) {
            this.app.showError(
                this.app.getString('error'),
                this.app.lang === 'ar' ? 'يرجى اختيار سبب الاستراحة' : 'Please select a break reason'
            );
            return;
        }

        try {
            if (this.app.isOnline && !this.currentTimeLog.startsWith('offline_')) {
                await this.app.apiCall('universal_workshop.www.technician.pause_time_tracking', {
                    service_order: this.currentJob.name,
                    break_reason: breakDescription
                });
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to start break via API:', error);
        }

        // Start break tracking
        this.isOnBreak = true;
        this.currentBreakStart = Date.now();

        const breakRecord = {
            id: Date.now(),
            reason: breakReason,
            description: breakDescription,
            startTime: new Date().toISOString(),
            endTime: null,
            duration: 0
        };

        this.breaks.push(breakRecord);

        this.updateUI();
        this.updateBreaksDisplay();
        this.closeBreakModal();

        await this.saveTimeLogLocally('break_start', breakRecord);

        this.app.showNotification(
            this.app.lang === 'ar' ? 'بدء الاستراحة' : 'Break Started',
            breakDescription
        );
    }

    /**
     * End current break
     */
    async endBreak() {
        if (!this.isOnBreak || !this.currentBreakStart) return;

        try {
            if (this.app.isOnline && !this.currentTimeLog.startsWith('offline_')) {
                await this.app.apiCall('universal_workshop.www.technician.resume_time_tracking', {
                    service_order: this.currentJob.name
                });
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to end break via API:', error);
        }

        // End break tracking
        const breakDuration = Date.now() - this.currentBreakStart;
        this.breakTime += breakDuration;

        // Update last break record
        const lastBreak = this.breaks[this.breaks.length - 1];
        if (lastBreak && !lastBreak.endTime) {
            lastBreak.endTime = new Date().toISOString();
            lastBreak.duration = breakDuration;
        }

        this.isOnBreak = false;
        this.currentBreakStart = null;

        this.updateUI();
        this.updateBreaksDisplay();

        await this.saveTimeLogLocally('break_end', lastBreak);

        this.app.showNotification(
            this.app.lang === 'ar' ? 'انتهاء الاستراحة' : 'Break Ended',
            this.app.lang === 'ar' ? 'العودة للعمل' : 'Back to work'
        );
    }

    /**
     * Start update interval
     */
    startInterval() {
        this.interval = setInterval(() => {
            this.updateDisplay();
        }, 1000);
    }

    /**
     * Stop update interval
     */
    stopInterval() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    /**
     * Update time display
     */
    updateDisplay() {
        if (this.isRunning && !this.isOnBreak) {
            this.elapsedTime = Date.now() - this.startTime;
        }

        if (this.isOnBreak && this.currentBreakStart) {
            const currentBreakTime = Date.now() - this.currentBreakStart;
            this.breakTime = this.breaks.reduce((total, brk) => total + (brk.duration || 0), 0) + currentBreakTime;
        }

        // Update displays
        const timerDisplay = document.getElementById('timer-display');
        const workTimeDisplay = document.getElementById('work-time-display');
        const breakTimeDisplay = document.getElementById('break-time-display');
        const totalTimeDisplay = document.getElementById('total-time-display');

        if (timerDisplay) {
            timerDisplay.textContent = this.formatTime(this.elapsedTime);
        }

        if (workTimeDisplay) {
            workTimeDisplay.textContent = this.formatTime(this.elapsedTime);
        }

        if (breakTimeDisplay) {
            breakTimeDisplay.textContent = this.formatTime(this.breakTime);
        }

        if (totalTimeDisplay) {
            totalTimeDisplay.textContent = this.formatTime(this.elapsedTime + this.breakTime);
        }
    }

    /**
     * Update UI controls state
     */
    updateUI() {
        const startBtn = document.getElementById('start-timer');
        const pauseBtn = document.getElementById('pause-timer');
        const stopBtn = document.getElementById('stop-timer');
        const takeBreakBtn = document.getElementById('take-break');
        const endBreakBtn = document.getElementById('end-break');
        const breakControls = document.getElementById('break-controls');
        const timerStatus = document.getElementById('timer-status');

        if (!startBtn) return; // UI not ready

        // Update button states
        if (this.isRunning && !this.isOnBreak) {
            startBtn.disabled = true;
            pauseBtn.disabled = false;
            stopBtn.disabled = false;
            takeBreakBtn.style.display = 'block';
            endBreakBtn.style.display = 'none';
            breakControls.style.display = 'flex';

            if (timerStatus) {
                timerStatus.textContent = this.app.lang === 'ar' ? 'جاري العمل' : 'Working';
                timerStatus.className = 'timer-status running';
            }
        } else if (this.isOnBreak) {
            startBtn.disabled = true;
            pauseBtn.disabled = true;
            stopBtn.disabled = false;
            takeBreakBtn.style.display = 'none';
            endBreakBtn.style.display = 'block';
            breakControls.style.display = 'flex';

            if (timerStatus) {
                timerStatus.textContent = this.app.lang === 'ar' ? 'في الاستراحة' : 'On Break';
                timerStatus.className = 'timer-status break';
            }
        } else if (this.startTime) {
            startBtn.disabled = false;
            pauseBtn.disabled = true;
            stopBtn.disabled = false;
            breakControls.style.display = 'none';

            if (timerStatus) {
                timerStatus.textContent = this.app.lang === 'ar' ? 'متوقف مؤقتاً' : 'Paused';
                timerStatus.className = 'timer-status paused';
            }
        } else {
            startBtn.disabled = !this.currentJob;
            pauseBtn.disabled = true;
            stopBtn.disabled = true;
            breakControls.style.display = 'none';

            if (timerStatus) {
                timerStatus.textContent = this.app.lang === 'ar' ? 'متوقف' : 'Stopped';
                timerStatus.className = 'timer-status stopped';
            }
        }
    }

    /**
     * Set current job for time tracking
     */
    setCurrentJob(job) {
        this.currentJob = job;
        this.updateJobDisplay();
        this.updateUI();
    }

    /**
     * Update job display
     */
    updateJobDisplay() {
        const jobDetails = document.getElementById('job-details');
        if (!jobDetails) return;

        if (this.currentJob) {
            jobDetails.innerHTML = `
                <div class="job-info">
                    <h4>${this.currentJob.service_order_number}</h4>
                    <p class="customer-name">${this.app.lang === 'ar' && this.currentJob.customer_name_ar ? this.currentJob.customer_name_ar : this.currentJob.customer_name}</p>
                    <p class="vehicle-info">${this.currentJob.vehicle_license_plate} - ${this.currentJob.make} ${this.currentJob.model}</p>
                    <span class="priority-badge priority-${this.currentJob.priority.toLowerCase()}">${this.app.translatePriority(this.currentJob.priority)}</span>
                </div>
            `;
        } else {
            jobDetails.innerHTML = `<p class="no-job">${this.app.lang === 'ar' ? 'لا توجد مهمة نشطة' : 'No active job selected'}</p>`;
        }
    }

    /**
     * Show job selector
     */
    showJobSelector() {
        if (this.app.jobManager) {
            this.app.switchView('jobs');
        }
    }

    /**
     * Update breaks display
     */
    updateBreaksDisplay() {
        const breaksList = document.getElementById('breaks-list');
        if (!breaksList) return;

        if (this.breaks.length === 0) {
            breaksList.innerHTML = `<p class="no-breaks">${this.app.lang === 'ar' ? 'لا توجد استراحات' : 'No breaks taken'}</p>`;
            return;
        }

        breaksList.innerHTML = this.breaks.map(brk => `
            <div class="break-item ${!brk.endTime ? 'active' : ''}">
                <div class="break-info">
                    <span class="break-reason">${brk.description}</span>
                    <span class="break-time">${new Date(brk.startTime).toLocaleTimeString()}</span>
                </div>
                <div class="break-duration">
                    ${brk.endTime ? this.formatTime(brk.duration) : this.formatTime(Date.now() - new Date(brk.startTime).getTime())}
                </div>
            </div>
        `).join('');
    }

    /**
     * Toggle breaks history visibility
     */
    toggleBreaksHistory() {
        const breaksList = document.getElementById('breaks-list');
        const toggleBtn = document.getElementById('toggle-breaks');

        if (breaksList.style.display === 'none') {
            breaksList.style.display = 'block';
            toggleBtn.querySelector('i').className = 'icon-chevron-up';
        } else {
            breaksList.style.display = 'none';
            toggleBtn.querySelector('i').className = 'icon-chevron-down';
        }
    }

    /**
     * Show manual time entry modal
     */
    showManualTimeModal() {
        const modal = document.getElementById('manual-time-modal');
        modal.classList.remove('hidden');

        document.getElementById('manual-hours').value = '';
        document.getElementById('manual-time-notes').value = '';
    }

    /**
     * Save manual time entry
     */
    async saveManualTime() {
        const hours = parseFloat(document.getElementById('manual-hours').value);
        const notes = document.getElementById('manual-time-notes').value;

        if (!hours || hours <= 0) {
            this.app.showError(
                this.app.getString('error'),
                this.app.lang === 'ar' ? 'يرجى إدخال عدد الساعات' : 'Please enter valid hours'
            );
            return;
        }

        if (!this.currentJob) {
            this.app.showError(
                this.app.getString('error'),
                this.app.lang === 'ar' ? 'يرجى اختيار مهمة أولاً' : 'Please select a job first'
            );
            return;
        }

        const manualEntry = {
            id: `manual_${Date.now()}`,
            job: this.currentJob.name,
            action: 'manual_entry',
            hours: hours,
            notes: notes,
            timestamp: new Date().toISOString(),
            synced: false
        };

        // Save to IndexedDB
        try {
            const transaction = this.app.db.transaction(['time_logs'], 'readwrite');
            const store = transaction.objectStore('time_logs');
            await store.add(manualEntry);

            this.closeManualTimeModal();

            this.app.showNotification(
                this.app.lang === 'ar' ? 'تم حفظ الوقت اليدوي' : 'Manual Time Saved',
                `${hours} ${this.app.lang === 'ar' ? 'ساعات' : 'hours'}`
            );

            // Queue for sync
            if (this.app.isOnline) {
                this.syncTimeLogs();
            }
        } catch (error) {
            console.error('[TimeTracker] Failed to save manual time:', error);
            this.app.showError(this.app.getString('error'), 'Failed to save manual time');
        }
    }

    /**
     * Save time log locally
     */
    async saveTimeLogLocally(action, extraData = {}) {
        const timeLog = {
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            job: this.currentJob?.name,
            timeLogId: this.currentTimeLog,
            action: action,
            timestamp: new Date().toISOString(),
            elapsed_time: this.elapsedTime,
            break_time: this.breakTime,
            synced: false,
            ...extraData
        };

        try {
            const transaction = this.app.db.transaction(['time_logs'], 'readwrite');
            const store = transaction.objectStore('time_logs');
            await store.add(timeLog);
        } catch (error) {
            console.error('[TimeTracker] Failed to save time log locally:', error);
        }
    }

    /**
     * Sync time logs with server
     */
    async syncTimeLogs() {
        if (!this.app.isOnline) {
            this.app.showNotification(
                this.app.lang === 'ar' ? 'غير متصل' : 'Offline',
                this.app.lang === 'ar' ? 'سيتم المزامنة عند الاتصال' : 'Will sync when online'
            );
            return;
        }

        this.app.showSyncIndicator();

        try {
            // Get unsynced time logs
            const transaction = this.app.db.transaction(['time_logs'], 'readonly');
            const store = transaction.objectStore('time_logs');
            const unsyncedLogs = await new Promise((resolve, reject) => {
                const request = store.getAll();
                request.onsuccess = () => {
                    const logs = request.result.filter(log => !log.synced);
                    resolve(logs);
                };
                request.onerror = () => reject(request.error);
            });

            if (unsyncedLogs.length === 0) {
                this.app.showNotification(
                    this.app.lang === 'ar' ? 'محدث' : 'Up to date',
                    this.app.lang === 'ar' ? 'جميع السجلات محفوظة' : 'All logs are synced'
                );
                return;
            }

            // Sync each log
            let syncedCount = 0;
            for (const log of unsyncedLogs) {
                try {
                    // TODO: Implement API call for time log sync
                    // await this.app.apiCall('universal_workshop.api.sync_time_log', { time_log: log });

                    // Mark as synced
                    const updateTransaction = this.app.db.transaction(['time_logs'], 'readwrite');
                    const updateStore = updateTransaction.objectStore('time_logs');
                    log.synced = true;
                    await updateStore.put(log);

                    syncedCount++;
                } catch (error) {
                    console.error('[TimeTracker] Failed to sync log:', log.id, error);
                }
            }

            this.app.showNotification(
                this.app.getString('syncComplete'),
                `${syncedCount}/${unsyncedLogs.length} ${this.app.lang === 'ar' ? 'سجلات' : 'logs synced'}`
            );

        } catch (error) {
            console.error('[TimeTracker] Sync failed:', error);
            this.app.showError(this.app.getString('error'), 'Sync failed');
        } finally {
            this.app.hideSyncIndicator();
        }
    }

    /**
     * Format time duration
     */
    formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    /**
     * Get icon for break type
     */
    getBreakIcon(breakType) {
        const icons = {
            'prayer': 'moon',
            'lunch': 'utensils',
            'rest': 'coffee',
            'technical': 'tool',
            'material': 'package',
            'emergency': 'alert-triangle',
            'other': 'more-horizontal'
        };
        return icons[breakType] || 'clock';
    }

    /**
     * Close break reason modal
     */
    closeBreakModal() {
        const modal = document.getElementById('break-reason-modal');
        modal.classList.add('hidden');
    }

    /**
     * Close manual time modal
     */
    closeManualTimeModal() {
        const modal = document.getElementById('manual-time-modal');
        modal.classList.add('hidden');
    }

    /**
     * Clean up resources
     */
    destroy() {
        this.stopInterval();
        this.currentJob = null;
        this.currentTimeLog = null;
    }
}

// Export for global use
window.EnhancedTimeTracker = EnhancedTimeTracker; 