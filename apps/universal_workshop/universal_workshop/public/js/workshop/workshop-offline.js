/**
 * Universal Workshop Offline JavaScript
 * Handles PWA functionality, offline operations, and mobile features
 */

class UniversalWorkshopOffline {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineQueue = [];
        this.syncInProgress = false;
        this.geolocation = null;
        
        this.init();
    }
    
    init() {
        this.registerServiceWorker();
        this.setupEventListeners();
        this.setupOfflineIndicator();
        this.setupPWAInstaller();
        this.initializeGeolocation();
        this.loadOfflineQueue();
        
        console.log('[UW] Universal Workshop Offline initialized');
    }
    
    // Service Worker Registration
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register(
                    '/assets/universal_workshop/js/service-worker.js',
                    { scope: '/' }
                );
                
                console.log('[UW] Service Worker registered:', registration);
                
                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
                
                // Register for background sync
                if (registration.sync) {
                    await registration.sync.register('sync-offline-submissions');
                }
                
            } catch (error) {
                console.error('[UW] Service Worker registration failed:', error);
            }
        }
    }
    
    // Event Listeners Setup
    setupEventListeners() {
        // Online/Offline detection
        window.addEventListener('online', () => {
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.handleOffline();
        });
        
        // Form submission handling
        document.addEventListener('submit', (event) => {
            if (!this.isOnline) {
                this.handleOfflineSubmission(event);
            }
        });
        
        // PWA install prompt
        window.addEventListener('beforeinstallprompt', (event) => {
            event.preventDefault();
            this.deferredPrompt = event;
            this.showInstallBanner();
        });
        
        // Visibility change for sync
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                this.syncOfflineData();
            }
        });
    }
    
    // Offline Indicator
    setupOfflineIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        indicator.innerHTML = `
            <span class="offline-icon">📶</span>
            <span id="offline-text">غير متصل بالإنترنت - Offline Mode</span>
        `;
        document.body.appendChild(indicator);
        
        this.offlineIndicator = indicator;
        this.updateOfflineStatus();
    }
    
    // PWA Installer
    setupPWAInstaller() {
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('[UW] PWA already installed');
            return;
        }
        
        // Create install banner
        const banner = document.createElement('div');
        banner.className = 'pwa-install-banner hidden';
        banner.innerHTML = `
            <div class="pwa-banner-content">
                <span class="pwa-banner-text">تثبيت Universal Workshop</span>
                <button class="btn-mobile btn-primary pwa-install-btn">تثبيت</button>
                <button class="btn-mobile btn-secondary pwa-dismiss-btn">إغلاق</button>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        // Setup install button
        banner.querySelector('.pwa-install-btn').addEventListener('click', () => {
            this.installPWA();
        });
        
        banner.querySelector('.pwa-dismiss-btn').addEventListener('click', () => {
            banner.classList.add('hidden');
        });
        
        this.installBanner = banner;
    }
    
    // Online Event Handler
    handleOnline() {
        this.isOnline = true;
        this.updateOfflineStatus();
        this.syncOfflineData();
        this.showToast('اتصال الإنترنت متاح - Connection restored', 'success');
    }
    
    // Offline Event Handler
    handleOffline() {
        this.isOnline = false;
        this.updateOfflineStatus();
        this.showToast('تم فقدان الاتصال - Working offline', 'warning');
    }
    
    // Update Offline Status UI
    updateOfflineStatus() {
        if (this.offlineIndicator) {
            if (this.isOnline) {
                this.offlineIndicator.classList.remove('visible');
            } else {
                this.offlineIndicator.classList.add('visible');
            }
        }
        
        // Update page body class
        document.body.classList.toggle('offline-mode', !this.isOnline);
    }
    
    // Handle Offline Form Submissions
    handleOfflineSubmission(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Add to offline queue
        const submission = {
            id: this.generateOfflineId(),
            url: form.action || window.location.href,
            method: form.method || 'POST',
            data: data,
            timestamp: Date.now(),
            synced: false
        };
        
        this.offlineQueue.push(submission);
        this.saveOfflineQueue();
        
        this.showToast('تم حفظ البيانات محلياً - Data saved offline', 'info');
        
        // Show offline submission in UI
        this.showOfflineSubmissionCard(submission);
    }
    
    // Sync Offline Data
    async syncOfflineData() {
        if (this.syncInProgress || !this.isOnline) {
            return;
        }
        
        this.syncInProgress = true;
        this.showSyncStatus('syncing');
        
        try {
            const unsynced = this.offlineQueue.filter(item => !item.synced);
            
            for (const submission of unsynced) {
                try {
                    const response = await fetch(submission.url, {
                        method: submission.method,
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Frappe-CSRF-Token': frappe.csrf_token
                        },
                        body: JSON.stringify(submission.data)
                    });
                    
                    if (response.ok) {
                        submission.synced = true;
                        submission.syncedAt = Date.now();
                        console.log('[UW] Synced offline submission:', submission.id);
                    }
                } catch (error) {
                    console.error('[UW] Failed to sync submission:', submission.id, error);
                }
            }
            
            this.saveOfflineQueue();
            this.showSyncStatus('complete');
            
            const syncedCount = unsynced.filter(item => item.synced).length;
            if (syncedCount > 0) {
                this.showToast(`تم مزامنة ${syncedCount} عنصر - ${syncedCount} items synced`, 'success');
            }
            
        } catch (error) {
            console.error('[UW] Sync error:', error);
            this.showSyncStatus('error');
        } finally {
            this.syncInProgress = false;
        }
    }
    
    // Camera Integration
    async openCamera(callback) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });
            
            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;
            video.playsinline = true;
            
            // Create camera overlay
            const overlay = this.createCameraOverlay(video, stream, callback);
            document.body.appendChild(overlay);
            
            return stream;
        } catch (error) {
            console.error('[UW] Camera error:', error);
            this.showToast('خطأ في الوصول للكاميرا - Camera access error', 'error');
            throw error;
        }
    }
    
    // Create Camera Overlay
    createCameraOverlay(video, stream, callback) {
        const overlay = document.createElement('div');
        overlay.className = 'camera-overlay';
        overlay.innerHTML = `
            <div class="camera-container">
                <div class="camera-header">
                    <h3>التقاط صورة - Take Photo</h3>
                    <button class="camera-close-btn">×</button>
                </div>
                <div class="camera-view"></div>
                <div class="camera-controls">
                    <button class="btn-mobile btn-primary camera-capture-btn">📸 التقاط</button>
                    <button class="btn-mobile btn-secondary camera-cancel-btn">إلغاء</button>
                </div>
            </div>
        `;
        
        const cameraView = overlay.querySelector('.camera-view');
        cameraView.appendChild(video);
        
        // Camera controls
        overlay.querySelector('.camera-capture-btn').addEventListener('click', () => {
            const canvas = this.capturePhoto(video);
            this.closeCameraOverlay(overlay, stream);
            if (callback) callback(canvas.toDataURL('image/jpeg', 0.8));
        });
        
        overlay.querySelector('.camera-cancel-btn').addEventListener('click', () => {
            this.closeCameraOverlay(overlay, stream);
        });
        
        overlay.querySelector('.camera-close-btn').addEventListener('click', () => {
            this.closeCameraOverlay(overlay, stream);
        });
        
        return overlay;
    }
    
    // Capture Photo
    capturePhoto(video) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        context.drawImage(video, 0, 0);
        
        return canvas;
    }
    
    // Close Camera Overlay
    closeCameraOverlay(overlay, stream) {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(overlay);
    }
    
    // Barcode Scanner
    async startBarcodeScanner(callback) {
        try {
            // For demo purposes - in production use a library like QuaggaJS
            const result = await this.mockBarcodeScanner();
            if (callback) callback(result);
        } catch (error) {
            console.error('[UW] Barcode scanner error:', error);
            this.showToast('خطأ في ماسح الباركود - Barcode scanner error', 'error');
        }
    }
    
    // Mock Barcode Scanner (replace with real implementation)
    async mockBarcodeScanner() {
        return new Promise((resolve) => {
            // Simulate barcode scanning
            setTimeout(() => {
                resolve('1234567890123'); // Mock barcode
            }, 2000);
        });
    }
    
    // Geolocation
    initializeGeolocation() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.geolocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: Date.now()
                    };
                    console.log('[UW] Geolocation acquired:', this.geolocation);
                },
                (error) => {
                    console.warn('[UW] Geolocation error:', error);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
            );
        }
    }
    
    // Get Current Location
    async getCurrentLocation() {
        if (this.geolocation && (Date.now() - this.geolocation.timestamp) < 300000) {
            return this.geolocation;
        }
        
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const location = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: Date.now()
                    };
                    this.geolocation = location;
                    resolve(location);
                },
                reject,
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
            );
        });
    }
    
    // PWA Install
    async installPWA() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const result = await this.deferredPrompt.userChoice;
            
            if (result.outcome === 'accepted') {
                this.showToast('تم تثبيت التطبيق - App installed successfully', 'success');
            }
            
            this.deferredPrompt = null;
            this.installBanner.classList.add('hidden');
        }
    }
    
    // Show Install Banner
    showInstallBanner() {
        if (this.installBanner) {
            this.installBanner.classList.remove('hidden');
        }
    }
    
    // Utility Functions
    generateOfflineId() {
        return `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    saveOfflineQueue() {
        localStorage.setItem('universal_workshop_offline_queue', JSON.stringify(this.offlineQueue));
    }
    
    loadOfflineQueue() {
        const saved = localStorage.getItem('universal_workshop_offline_queue');
        if (saved) {
            this.offlineQueue = JSON.parse(saved);
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 4000);
    }
    
    showSyncStatus(status) {
        let existing = document.querySelector('.sync-status');
        if (existing) {
            existing.remove();
        }
        
        const statusEl = document.createElement('div');
        statusEl.className = `sync-status sync-${status}`;
        
        switch (status) {
            case 'syncing':
                statusEl.innerHTML = '🔄 مزامنة البيانات - Syncing data';
                break;
            case 'complete':
                statusEl.innerHTML = '✅ تمت المزامنة - Sync complete';
                break;
            case 'error':
                statusEl.innerHTML = '❌ خطأ في المزامنة - Sync error';
                break;
        }
        
        document.body.appendChild(statusEl);
        
        if (status !== 'syncing') {
            setTimeout(() => {
                if (document.body.contains(statusEl)) {
                    document.body.removeChild(statusEl);
                }
            }, 3000);
        }
    }
    
    showOfflineSubmissionCard(submission) {
        // Implementation for showing offline submission cards in UI
        console.log('[UW] Offline submission queued:', submission);
    }
    
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="update-content">
                <span>تحديث متاح - Update available</span>
                <button class="btn-mobile btn-primary update-btn">تحديث</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        notification.querySelector('.update-btn').addEventListener('click', () => {
            window.location.reload();
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.universalWorkshopOffline = new UniversalWorkshopOffline();
});

// Global utility functions for integration with Frappe
window.UW = {
    // Take photo and return base64
    takePhoto: async function(callback) {
        const offline = window.universalWorkshopOffline;
        if (offline) {
            await offline.openCamera(callback);
        }
    },
    
    // Scan barcode
    scanBarcode: async function(callback) {
        const offline = window.universalWorkshopOffline;
        if (offline) {
            await offline.startBarcodeScanner(callback);
        }
    },
    
    // Get current location
    getLocation: async function() {
        const offline = window.universalWorkshopOffline;
        if (offline) {
            return await offline.getCurrentLocation();
        }
        return null;
    },
    
    // Check if online
    isOnline: function() {
        const offline = window.universalWorkshopOffline;
        return offline ? offline.isOnline : navigator.onLine;
    },
    
    // Force sync
    syncNow: async function() {
        const offline = window.universalWorkshopOffline;
        if (offline) {
            await offline.syncOfflineData();
        }
    }
};

console.log('[UW] Universal Workshop Offline utilities loaded'); 