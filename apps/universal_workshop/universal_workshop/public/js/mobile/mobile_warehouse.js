// Mobile Warehouse Management Interface

class MobileWarehouseApp {
    constructor() {
        this.currentUser = frappe.session.user;
        this.isOnline = navigator.onLine;
        this.pendingSync = [];
        this.scanner = null;
        this.locationTracker = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeScanner();
        this.initializeLocationTracking();
        this.setupOfflineSupport();
        this.loadUserPreferences();
        this.setupArabicSupport();
    }

    setupEventListeners() {
        // Network status monitoring
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.syncPendingData();
            this.showConnectionStatus('online');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showConnectionStatus('offline');
        });

        // Touch and gesture handlers for mobile
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), false);
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), false);
    }

    setupArabicSupport() {
        // Apply RTL layout if Arabic is selected
        if (frappe.boot.lang === 'ar') {
            document.body.classList.add('rtl-mobile');
            document.dir = 'rtl';
        }

        // Setup Arabic number formatting
        this.setupArabicNumbers();
    }

    setupArabicNumbers() {
        const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

        window.formatArabicNumber = function (number) {
            if (frappe.boot.lang === 'ar') {
                return number.toString().replace(/[0-9]/g, (w) => arabicNumbers[+w]);
            }
            return number.toString();
        };
    }

    initializeScanner() {
        if ('BarcodeDetector' in window) {
            this.scanner = new BarcodeDetector({
                formats: ['qr_code', 'code_128', 'code_39', 'code_93']
            });
        } else {
            console.warn('BarcodeDetector not supported, using fallback');
            this.setupFallbackScanner();
        }
    }

    setupFallbackScanner() {
        // Fallback scanner using ZXing library
        this.scanner = {
            scan: async (video) => {
                // This would integrate with ZXing-js library
                return new Promise((resolve) => {
                    // Placeholder implementation
                    setTimeout(() => {
                        resolve([{ rawValue: 'UW-SAMPLE-001', format: 'code_128' }]);
                    }, 2000);
                });
            }
        };
    }

    initializeLocationTracking() {
        if ('geolocation' in navigator) {
            this.locationTracker = {
                getCurrentLocation: () => {
                    return new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(
                            position => resolve({
                                lat: position.coords.latitude,
                                lng: position.coords.longitude,
                                accuracy: position.coords.accuracy
                            }),
                            error => reject(error),
                            { enableHighAccuracy: true, timeout: 10000 }
                        );
                    });
                }
            };
        }
    }

    setupOfflineSupport() {
        // Register service worker for offline capability
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/assets/universal_workshop/js/warehouse-sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }

        // Setup local storage for offline data
        this.offlineStorage = {
            save: (key, data) => {
                localStorage.setItem(`warehouse_${key}`, JSON.stringify(data));
            },
            get: (key) => {
                const data = localStorage.getItem(`warehouse_${key}`);
                return data ? JSON.parse(data) : null;
            },
            remove: (key) => {
                localStorage.removeItem(`warehouse_${key}`);
            }
        };
    }

    // Main Scanner Interface
    async startScanning(mode = 'general') {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            this.showScannerInterface(stream, mode);

        } catch (error) {
            frappe.msgprint(__('Camera access denied or not available'));
            this.showManualEntryFallback(mode);
        }
    }

    showScannerInterface(stream, mode) {
        const scannerHTML = this.buildScannerHTML(mode);

        // Create full-screen scanner dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Scan Barcode/QR Code'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: scannerHTML
                }
            ],
            primary_action_label: __('Manual Entry'),
            primary_action: () => {
                this.stopScanning(stream);
                dialog.hide();
                this.showManualEntryFallback(mode);
            },
            secondary_action_label: __('Cancel'),
            secondary_action: () => {
                this.stopScanning(stream);
                dialog.hide();
            }
        });

        dialog.show();
        dialog.$wrapper.addClass('mobile-scanner-dialog');

        // Setup video stream
        const video = dialog.$wrapper.find('#scanner-video')[0];
        video.srcObject = stream;
        video.play();

        // Start scanning loop
        this.startScanningLoop(video, dialog, mode, stream);
    }

    buildScannerHTML(mode) {
        const title = this.getScannerTitle(mode);
        const instructions = this.getScannerInstructions(mode);

        return `
            <div class="mobile-scanner-container">
                <div class="scanner-header">
                    <h4>${title}</h4>
                    <p class="scanner-instructions">${instructions}</p>
                </div>
                
                <div class="scanner-viewport">
                    <video id="scanner-video" autoplay playsinline></video>
                    <div class="scanner-overlay">
                        <div class="scanner-frame"></div>
                        <div class="scanner-line"></div>
                    </div>
                </div>
                
                <div class="scanner-controls">
                    <button class="btn btn-secondary" onclick="toggleFlashlight()">
                        <i class="fa fa-flash"></i> ${__('Flash')}
                    </button>
                    <button class="btn btn-primary" onclick="captureImage()">
                        <i class="fa fa-camera"></i> ${__('Capture')}
                    </button>
                </div>
                
                <div class="scanner-status">
                    <div id="scan-status" class="text-muted">
                        ${__('Point camera at barcode or QR code')}
                    </div>
                </div>
            </div>
        `;
    }

    getScannerTitle(mode) {
        const titles = {
            'general': __('Scan Code'),
            'stock_in': __('Scan Part for Stock In'),
            'stock_out': __('Scan Part for Stock Out'),
            'transfer': __('Scan Part for Transfer'),
            'location': __('Scan Location Code')
        };
        return titles[mode] || titles['general'];
    }

    getScannerInstructions(mode) {
        const instructions = {
            'general': __('Scan any barcode or QR code'),
            'stock_in': __('Scan the part barcode to add to inventory'),
            'stock_out': __('Scan the part barcode to remove from inventory'),
            'transfer': __('Scan part barcode, then scan destination location'),
            'location': __('Scan location QR code or barcode')
        };
        return instructions[mode] || instructions['general'];
    }

    async startScanningLoop(video, dialog, mode, stream) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        const scanLoop = async () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                try {
                    const barcodes = await this.scanner.detect(canvas);

                    if (barcodes.length > 0) {
                        const result = barcodes[0];
                        this.handleScanResult(result, mode, dialog, stream);
                        return; // Stop scanning loop
                    }
                } catch (error) {
                    console.warn('Barcode detection error:', error);
                }
            }

            // Update scan status
            this.updateScanStatus(__('Scanning...'));

            // Continue scanning
            requestAnimationFrame(scanLoop);
        };

        scanLoop();
    }

    updateScanStatus(message) {
        const statusElement = document.getElementById('scan-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    async handleScanResult(result, mode, dialog, stream) {
        this.stopScanning(stream);
        dialog.hide();

        // Vibrate on successful scan (if supported)
        if ('vibrate' in navigator) {
            navigator.vibrate(200);
        }

        // Process the scanned code
        await this.processScanResult(result.rawValue, mode);
    }

    async processScanResult(scannedCode, mode) {
        this.showProcessingIndicator();

        try {
            // Determine code type
            if (scannedCode.startsWith('UW-')) {
                // Part barcode
                await this.handlePartScan(scannedCode, mode);
            } else if (scannedCode.startsWith('LOC-')) {
                // Location barcode
                await this.handleLocationScan(scannedCode, mode);
            } else if (this.isQRCodeData(scannedCode)) {
                // QR Code with JSON data
                await this.handleQRCodeScan(scannedCode, mode);
            } else {
                // Unknown format
                frappe.msgprint(__('Unknown barcode format: {0}', [scannedCode]));
            }

        } catch (error) {
            frappe.msgprint(__('Error processing scan: {0}', [error.message]));
        } finally {
            this.hideProcessingIndicator();
        }
    }

    isQRCodeData(data) {
        try {
            JSON.parse(data);
            return true;
        } catch {
            return false;
        }
    }

    async handlePartScan(partBarcode, mode) {
        // Get part information
        const partInfo = await this.getPartByBarcode(partBarcode);

        if (!partInfo) {
            frappe.msgprint(__('Part not found for barcode: {0}', [partBarcode]));
            return;
        }

        // Show part information and movement options
        this.showPartMovementDialog(partInfo, mode);
    }

    async handleLocationScan(locationBarcode, mode) {
        const locationCode = locationBarcode.replace('LOC-', '');

        // Get location information
        const locationInfo = await this.getLocationByCode(locationCode);

        if (!locationInfo) {
            frappe.msgprint(__('Location not found for code: {0}', [locationCode]));
            return;
        }

        // Show location information and available actions
        this.showLocationActionsDialog(locationInfo, mode);
    }

    async handleQRCodeScan(qrData, mode) {
        try {
            const data = JSON.parse(qrData);

            if (data.type === 'storage_location') {
                await this.handleLocationScan(`LOC-${data.location_code}`, mode);
            } else if (data.type === 'extracted_part') {
                await this.handlePartScan(`UW-${data.part_code}`, mode);
            } else {
                frappe.msgprint(__('Unknown QR code type: {0}', [data.type]));
            }

        } catch (error) {
            frappe.msgprint(__('Invalid QR code data'));
        }
    }

    showPartMovementDialog(partInfo, mode) {
        const dialog = new frappe.ui.Dialog({
            title: __('Part Movement: {0}', [partInfo.part_code]),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: this.buildPartInfoHTML(partInfo)
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Movement Options')
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'movement_type',
                    label: __('Movement Type'),
                    options: '\nStock In\nStock Out\nTransfer\nDamage\nLoss\nFound',
                    default: this.getDefaultMovementType(mode),
                    reqd: 1
                },
                {
                    fieldtype: 'Link',
                    fieldname: 'to_location',
                    label: __('To Location'),
                    options: 'Storage Location',
                    depends_on: 'eval:["Stock In", "Transfer", "Found"].includes(doc.movement_type)'
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'notes',
                    label: __('Notes')
                }
            ],
            primary_action_label: __('Create Movement'),
            primary_action: async (values) => {
                await this.createMovementRecord(partInfo, values);
                dialog.hide();
            }
        });

        dialog.show();
        dialog.$wrapper.addClass('mobile-movement-dialog');
    }

    buildPartInfoHTML(partInfo) {
        const nameDisplay = frappe.boot.lang === 'ar' ?
            (partInfo.part_name_ar || partInfo.part_name) :
            partInfo.part_name;

        return `
            <div class="part-info-card">
                <div class="part-header">
                    <h4>${partInfo.part_code}</h4>
                    <span class="part-name">${nameDisplay}</span>
                </div>
                
                <div class="part-details">
                    <div class="detail-row">
                        <label>${__('Current Location')}:</label>
                        <span>${partInfo.storage_location || __('Not Located')}</span>
                    </div>
                    <div class="detail-row">
                        <label>${__('Condition Grade')}:</label>
                        <span class="grade-badge grade-${partInfo.condition_grade?.toLowerCase()}">${partInfo.condition_grade}</span>
                    </div>
                    <div class="detail-row">
                        <label>${__('Weight')}:</label>
                        <span>${formatArabicNumber(partInfo.weight_kg || 0)} ${__('kg')}</span>
                    </div>
                    <div class="detail-row">
                        <label>${__('Estimated Value')}:</label>
                        <span>${formatArabicNumber(partInfo.estimated_price_omr || 0)} ${__('OMR')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    getDefaultMovementType(mode) {
        const defaults = {
            'stock_in': 'Stock In',
            'stock_out': 'Stock Out',
            'transfer': 'Transfer'
        };
        return defaults[mode] || '';
    }

    async createMovementRecord(partInfo, values) {
        this.showProcessingIndicator();

        try {
            // Get current location if needed
            const currentLocation = await this.getCurrentLocation();

            const movementData = {
                extracted_part: partInfo.name,
                movement_type: values.movement_type,
                to_location: values.to_location,
                notes: values.notes,
                scanned_by: this.currentUser,
                scan_method: 'Mobile Camera',
                gps_location: currentLocation ? `${currentLocation.lat},${currentLocation.lng}` : '',
                device_info: this.getDeviceInfo()
            };

            // Create movement record
            const result = await this.saveMovementRecord(movementData);

            if (result.success) {
                frappe.msgprint(__('Movement created successfully: {0}', [result.movement_id]));
                this.showSuccessAnimation();
            } else {
                frappe.msgprint(__('Error creating movement: {0}', [result.message]));
            }

        } catch (error) {
            frappe.msgprint(__('Error: {0}', [error.message]));
        } finally {
            this.hideProcessingIndicator();
        }
    }

    async getCurrentLocation() {
        if (this.locationTracker) {
            try {
                return await this.locationTracker.getCurrentLocation();
            } catch (error) {
                console.warn('Location access denied or unavailable');
                return null;
            }
        }
        return null;
    }

    getDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            screenSize: `${screen.width}x${screen.height}`,
            timestamp: new Date().toISOString()
        };
    }

    async saveMovementRecord(movementData) {
        if (this.isOnline) {
            // Save directly to server
            return await frappe.call({
                method: 'universal_workshop.scrap_management.doctype.inventory_movement.inventory_movement.create_movement_from_barcode',
                args: movementData
            });
        } else {
            // Save to local storage for later sync
            this.pendingSync.push({
                type: 'movement',
                data: movementData,
                timestamp: new Date().toISOString()
            });

            this.offlineStorage.save('pendingSync', this.pendingSync);

            return {
                success: true,
                movement_id: `OFFLINE-${Date.now()}`,
                message: __('Saved offline, will sync when connection is restored')
            };
        }
    }

    // API Helper Methods
    async getPartByBarcode(barcode) {
        if (this.isOnline) {
            const response = await frappe.call({
                method: 'universal_workshop.scrap_management.doctype.extracted_parts.extracted_parts.get_part_by_barcode',
                args: { barcode: barcode }
            });
            return response.message;
        } else {
            // Try to get from offline cache
            const cachedParts = this.offlineStorage.get('parts') || [];
            return cachedParts.find(part => part.barcode === barcode);
        }
    }

    async getLocationByCode(locationCode) {
        if (this.isOnline) {
            const response = await frappe.call({
                method: 'universal_workshop.scrap_management.doctype.storage_location.storage_location.get_location_by_code',
                args: { location_code: locationCode }
            });
            return response.message;
        } else {
            // Try to get from offline cache
            const cachedLocations = this.offlineStorage.get('locations') || [];
            return cachedLocations.find(loc => loc.location_code === locationCode);
        }
    }

    // UI Helper Methods
    showProcessingIndicator() {
        if (!document.getElementById('mobile-processing')) {
            const indicator = document.createElement('div');
            indicator.id = 'mobile-processing';
            indicator.className = 'mobile-processing-overlay';
            indicator.innerHTML = `
                <div class="processing-content">
                    <div class="spinner"></div>
                    <p>${__('Processing...')}</p>
                </div>
            `;
            document.body.appendChild(indicator);
        }
    }

    hideProcessingIndicator() {
        const indicator = document.getElementById('mobile-processing');
        if (indicator) {
            indicator.remove();
        }
    }

    showSuccessAnimation() {
        const success = document.createElement('div');
        success.className = 'mobile-success-animation';
        success.innerHTML = `
            <div class="success-content">
                <i class="fa fa-check-circle success-icon"></i>
                <p>${__('Success!')}</p>
            </div>
        `;
        document.body.appendChild(success);

        setTimeout(() => {
            success.remove();
        }, 2000);
    }

    showConnectionStatus(status) {
        const statusBar = document.getElementById('connection-status') || document.createElement('div');
        statusBar.id = 'connection-status';
        statusBar.className = `connection-status ${status}`;

        if (status === 'online') {
            statusBar.innerHTML = `<i class="fa fa-wifi"></i> ${__('Online')}`;
            statusBar.classList.remove('offline');
            statusBar.classList.add('online');
        } else {
            statusBar.innerHTML = `<i class="fa fa-exclamation-triangle"></i> ${__('Offline')}`;
            statusBar.classList.remove('online');
            statusBar.classList.add('offline');
        }

        if (!document.getElementById('connection-status')) {
            document.body.appendChild(statusBar);
        }

        // Auto-hide online status after 3 seconds
        if (status === 'online') {
            setTimeout(() => {
                statusBar.style.opacity = '0';
                setTimeout(() => statusBar.remove(), 500);
            }, 3000);
        }
    }

    // Offline Support Methods
    async syncPendingData() {
        if (!this.isOnline || this.pendingSync.length === 0) return;

        this.showProcessingIndicator();

        try {
            const results = await frappe.call({
                method: 'universal_workshop.scrap_management.doctype.inventory_movement.inventory_movement.bulk_movement_import',
                args: { movement_data: this.pendingSync.map(item => item.data) }
            });

            if (results.message) {
                const successful = results.message.filter(r => r.success).length;
                const failed = results.message.filter(r => !r.success).length;

                frappe.msgprint(__('Sync complete: {0} successful, {1} failed', [successful, failed]));

                // Clear successfully synced items
                this.pendingSync = [];
                this.offlineStorage.remove('pendingSync');
            }

        } catch (error) {
            frappe.msgprint(__('Sync failed: {0}', [error.message]));
        } finally {
            this.hideProcessingIndicator();
        }
    }

    // Touch and Gesture Handlers
    handleTouchStart(evt) {
        this.touchStartX = evt.touches[0].clientX;
        this.touchStartY = evt.touches[0].clientY;
    }

    handleTouchMove(evt) {
        if (!this.touchStartX || !this.touchStartY) return;

        const touchEndX = evt.touches[0].clientX;
        const touchEndY = evt.touches[0].clientY;

        const diffX = this.touchStartX - touchEndX;
        const diffY = this.touchStartY - touchEndY;

        // Swipe gestures for navigation
        if (Math.abs(diffX) > Math.abs(diffY)) {
            if (diffX > 50) {
                // Swipe left
                this.handleSwipeLeft();
            } else if (diffX < -50) {
                // Swipe right
                this.handleSwipeRight();
            }
        }

        this.touchStartX = null;
        this.touchStartY = null;
    }

    handleSwipeLeft() {
        // Navigate to next screen or close dialogs
        console.log('Swipe left detected');
    }

    handleSwipeRight() {
        // Navigate to previous screen or open menu
        console.log('Swipe right detected');
    }

    stopScanning(stream) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }

    showManualEntryFallback(mode) {
        const dialog = new frappe.ui.Dialog({
            title: __('Manual Entry'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'manual_code',
                    label: __('Enter Barcode/Code'),
                    reqd: 1
                }
            ],
            primary_action_label: __('Process'),
            primary_action: (values) => {
                if (values.manual_code) {
                    this.processScanResult(values.manual_code, mode);
                    dialog.hide();
                }
            }
        });

        dialog.show();
    }

    loadUserPreferences() {
        const prefs = this.offlineStorage.get('userPreferences') || {};

        // Apply saved preferences
        if (prefs.language) {
            frappe.boot.lang = prefs.language;
        }

        if (prefs.theme) {
            document.body.classList.add(`theme-${prefs.theme}`);
        }
    }
}

// Global functions for mobile interface
window.toggleFlashlight = function () {
    // Implementation depends on browser support
    console.log('Toggle flashlight');
};

window.captureImage = function () {
    // Capture current camera frame
    console.log('Capture image');
};

// Initialize mobile warehouse app when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Check if mobile device using standard method
    const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
        window.innerWidth <= 768;

    if (isMobile) {
        window.mobileWarehouse = new MobileWarehouseApp();

        // Add mobile-specific CSS
        const mobileCSS = document.createElement('link');
        mobileCSS.rel = 'stylesheet';
        mobileCSS.href = '/assets/universal_workshop/css/mobile-warehouse.css';
        document.head.appendChild(mobileCSS);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileWarehouseApp;
}
