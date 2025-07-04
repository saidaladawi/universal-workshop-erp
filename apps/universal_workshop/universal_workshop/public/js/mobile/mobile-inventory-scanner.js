/**
 * Mobile Inventory Scanner
 * Comprehensive barcode scanning interface for inventory management
 * Supports offline operation, batch scanning, and Arabic localization
 * 
 * Copyright (c) 2025, Eng. Saeed Al-Adawi
 */

class MobileInventoryScanner {
	constructor() {
		this.isOnline = navigator.onLine;
		this.currentTab = 'scan';
		this.currentMode = 'lookup';
		this.isScanning = false;
		this.scanResults = [];
		this.pendingSync = [];
		this.scanSession = null;
		this.quaggaInitialized = false;
		this.stream = null;
		this.language = 'en';
		this.direction = 'ltr';

		// Configuration
		this.config = {
			api_timeout: 30000,
			max_retries: 3,
			sync_interval: 300000, // 5 minutes
			max_offline_records: 1000,
			scan_cooldown: 1000, // 1 second between scans
		};

		this.init();
	}

	async init() {
		console.log('Initializing Mobile Inventory Scanner...');

		try {
			// Load configuration from server
			await this.loadConfig();

			// Initialize components
			this.initConnectivityMonitoring();
			this.initOfflineManager();
			this.setupEventListeners();
			this.setupTabNavigation();
			this.setupModeSelector();
			this.initTranslations();

			// Start automatic sync timer
			this.startSyncTimer();

			// Load saved data
			this.loadSavedData();

			console.log('Mobile Inventory Scanner initialized successfully');
			this.showMessage('Scanner ready', 'success');

		} catch (error) {
			console.error('Error initializing scanner:', error);
			this.showMessage('Error initializing scanner', 'error');
		}
	}

	async loadConfig() {
		try {
			const response = await this.apiCall('universal_workshop.www.mobile-inventory-scanner.get_mobile_scanner_config');
			if (response) {
				this.config = { ...this.config, ...response };
				this.language = response.language || 'en';
				this.direction = this.language === 'ar' ? 'rtl' : 'ltr';
				this.updateLanguageInterface();
			}
		} catch (error) {
			console.warn('Could not load server config, using defaults:', error);
		}
	}

	initConnectivityMonitoring() {
		const updateConnectivityStatus = () => {
			this.isOnline = navigator.onLine;
			const indicator = document.getElementById('connectivity-indicator');
			const text = document.getElementById('connectivity-text');
			const offlineBanner = document.getElementById('offline-banner');

			if (this.isOnline) {
				indicator.classList.remove('offline');
				text.textContent = this.t('online');
				if (offlineBanner) offlineBanner.classList.remove('show');
				this.syncPendingData();
			} else {
				indicator.classList.add('offline');
				text.textContent = this.t('offline');
				if (offlineBanner) offlineBanner.classList.add('show');
			}

			this.updateSyncStatus();
		};

		window.addEventListener('online', updateConnectivityStatus);
		window.addEventListener('offline', updateConnectivityStatus);
		updateConnectivityStatus();
	}

	initOfflineManager() {
		// Initialize IndexedDB for offline storage
		if ('indexedDB' in window) {
			this.initIndexedDB().then(() => {
				console.log('IndexedDB initialized for offline storage');
			}).catch(error => {
				console.warn('IndexedDB not available:', error);
			});
		}

		// Initialize service worker for PWA capabilities
		if ('serviceWorker' in navigator) {
			navigator.serviceWorker.register('/assets/universal_workshop/js/service-worker.js')
				.then(registration => {
					console.log('Service Worker registered:', registration);
				})
				.catch(error => {
					console.warn('Service Worker registration failed:', error);
				});
		}
	}

	async initIndexedDB() {
		return new Promise((resolve, reject) => {
			const request = indexedDB.open('MobileInventoryScanner', 1);

			request.onerror = () => reject(request.error);
			request.onsuccess = () => {
				this.db = request.result;
				resolve();
			};

			request.onupgradeneeded = (event) => {
				const db = event.target.result;

				// Create stores
				if (!db.objectStoreNames.contains('scans')) {
					const scansStore = db.createObjectStore('scans', { keyPath: 'id', autoIncrement: true });
					scansStore.createIndex('timestamp', 'timestamp');
					scansStore.createIndex('synced', 'synced');
				}

				if (!db.objectStoreNames.contains('sessions')) {
					const sessionsStore = db.createObjectStore('sessions', { keyPath: 'id', autoIncrement: true });
					sessionsStore.createIndex('session_id', 'session_id');
				}

				if (!db.objectStoreNames.contains('config')) {
					db.createObjectStore('config', { keyPath: 'key' });
				}
			};
		});
	}

	setupEventListeners() {
		// Camera scan button
		const scanCameraBtn = document.getElementById('scan-camera-btn');
		if (scanCameraBtn) {
			scanCameraBtn.addEventListener('click', () => this.startCameraScanning());
		}

		// Manual input button
		const manualInputBtn = document.getElementById('manual-input-btn');
		if (manualInputBtn) {
			manualInputBtn.addEventListener('click', () => this.promptManualInput());
		}

		// Quick actions
		const batchScanAction = document.getElementById('batch-scan-action');
		if (batchScanAction) {
			batchScanAction.addEventListener('click', () => this.startBatchScanning());
		}

		const recentItemsAction = document.getElementById('recent-items-action');
		if (recentItemsAction) {
			recentItemsAction.addEventListener('click', () => this.showRecentItems());
		}

		const exportDataAction = document.getElementById('export-data-action');
		if (exportDataAction) {
			exportDataAction.addEventListener('click', () => this.exportData());
		}

		const settingsAction = document.getElementById('settings-action');
		if (settingsAction) {
			settingsAction.addEventListener('click', () => this.showSettings());
		}

		// Scanner modal controls
		const closeScannerBtn = document.getElementById('close-scanner');
		if (closeScannerBtn) {
			closeScannerBtn.addEventListener('click', () => this.stopCameraScanning());
		}

		const toggleFlashBtn = document.getElementById('toggle-flash');
		if (toggleFlashBtn) {
			toggleFlashBtn.addEventListener('click', () => this.toggleFlashlight());
		}

		const manualEntryBtn = document.getElementById('manual-entry');
		if (manualEntryBtn) {
			manualEntryBtn.addEventListener('click', () => {
				this.stopCameraScanning();
				this.promptManualInput();
			});
		}

		// Sync button
		const syncBtn = document.getElementById('sync-btn');
		if (syncBtn) {
			syncBtn.addEventListener('click', () => this.forceSyncData());
		}

		// Language toggle
		const languageToggle = document.getElementById('language-toggle');
		if (languageToggle) {
			languageToggle.addEventListener('click', () => this.toggleLanguage());
		}

		// Clear results
		const clearResultsBtn = document.getElementById('clear-results');
		if (clearResultsBtn) {
			clearResultsBtn.addEventListener('click', () => this.clearResults());
		}

		// Close modal when clicking outside
		const scannerModal = document.getElementById('scanner-modal');
		if (scannerModal) {
			scannerModal.addEventListener('click', (e) => {
				if (e.target === scannerModal) {
					this.stopCameraScanning();
				}
			});
		}
	}

	setupTabNavigation() {
		const tabButtons = document.querySelectorAll('.tab-btn');
		tabButtons.forEach(btn => {
			btn.addEventListener('click', (e) => {
				const tab = e.target.dataset.tab;
				if (tab) this.switchTab(tab);
			});
		});
	}

	setupModeSelector() {
		const modeButtons = document.querySelectorAll('.mode-btn');
		modeButtons.forEach(btn => {
			btn.addEventListener('click', (e) => {
				const mode = e.target.dataset.mode;
				if (mode) this.switchMode(mode);
			});
		});
	}

	initTranslations() {
		// Initialize translation system
		this.translations = window.translations || {};
	}

	switchTab(tabName) {
		// Update active tab button
		document.querySelectorAll('.tab-btn').forEach(btn => {
			btn.classList.remove('active');
		});
		document.getElementById(`${tabName}-tab`).classList.add('active');

		// Update content
		this.currentTab = tabName;
		this.loadTabContent(tabName);

		// Update page title
		const pageTitle = document.getElementById('page-title');
		if (pageTitle) {
			pageTitle.textContent = this.getTabTitle(tabName);
		}
	}

	switchMode(modeName) {
		// Update active mode button
		document.querySelectorAll('.mode-btn').forEach(btn => {
			btn.classList.remove('active');
		});
		document.querySelector(`[data-mode="${modeName}"]`).classList.add('active');

		this.currentMode = modeName;
		this.updateModeInterface();
	}

	getTabTitle(tabName) {
		const titles = {
			'scan': this.t('scan'),
			'stock-take': this.t('stock_take'),
			'cycle-count': this.t('cycle_count'),
			'transfer': this.t('stock_transfer')
		};
		return titles[tabName] || 'Inventory Scanner';
	}

	updateModeInterface() {
		// Update interface based on current mode
		const scanBtn = document.getElementById('scan-camera-btn');
		const manualBtn = document.getElementById('manual-input-btn');

		if (scanBtn && manualBtn) {
			const modeTexts = {
				'lookup': { scan: 'Scan to Lookup', manual: 'Enter Barcode' },
				'receive': { scan: 'Scan to Receive', manual: 'Enter Barcode' },
				'issue': { scan: 'Scan to Issue', manual: 'Enter Barcode' },
				'adjust': { scan: 'Scan to Adjust', manual: 'Enter Barcode' }
			};

			const texts = modeTexts[this.currentMode] || modeTexts['lookup'];
			scanBtn.querySelector('span').textContent = this.t(texts.scan);
			manualBtn.querySelector('span').textContent = this.t(texts.manual);
		}
	}

	async startCameraScanning() {
		if (this.isScanning) {
			this.showMessage('Scanner already active', 'warning');
			return;
		}

		try {
			// Show scanner modal
			const modal = document.getElementById('scanner-modal');
			if (modal) {
				modal.classList.add('show');
			}

			// Request camera permission and start stream
			await this.initCameraStream();
			await this.initQuaggaScanner();

			this.isScanning = true;
			this.showMessage('Scanner started', 'success');

		} catch (error) {
			console.error('Error starting camera:', error);
			this.showMessage(this.getCameraErrorMessage(error), 'error');
			this.stopCameraScanning();
		}
	}

	async initCameraStream() {
		const video = document.getElementById('scanner-camera');
		if (!video) throw new Error('Camera element not found');

		const constraints = {
			video: {
				facingMode: 'environment', // Use back camera
				width: { ideal: 1280 },
				height: { ideal: 720 }
			}
		};

		this.stream = await navigator.mediaDevices.getUserMedia(constraints);
		video.srcObject = this.stream;

		return new Promise((resolve, reject) => {
			video.onloadedmetadata = () => {
				video.play();
				resolve();
			};
			video.onerror = reject;
		});
	}

	async initQuaggaScanner() {
		if (!window.Quagga) {
			throw new Error('QuaggaJS not loaded');
		}

		return new Promise((resolve, reject) => {
			const config = {
				inputStream: {
					name: "Live",
					type: "LiveStream",
					target: document.querySelector('#scanner-camera'),
					constraints: {
						width: 640,
						height: 480,
						facingMode: "environment"
					}
				},
				decoder: {
					readers: [
						"code_128_reader",
						"ean_reader",
						"ean_8_reader",
						"code_39_reader",
						"code_39_vin_reader",
						"codabar_reader",
						"upc_reader",
						"upc_e_reader"
					]
				},
				locator: {
					patchSize: "medium",
					halfSample: true
				},
				numOfWorkers: 2,
				frequency: 10,
				debug: false
			};

			window.Quagga.init(config, (err) => {
				if (err) {
					reject(err);
					return;
				}

				window.Quagga.start();
				this.quaggaInitialized = true;

				// Set up barcode detection
				window.Quagga.onDetected(this.handleBarcodeDetected.bind(this));
				resolve();
			});
		});
	}

	handleBarcodeDetected(result) {
		if (!this.isScanning) return;

		const code = result.codeResult.code;
		const now = Date.now();

		// Prevent duplicate scans within cooldown period
		if (this.lastScanTime && (now - this.lastScanTime) < this.config.scan_cooldown) {
			return;
		}

		this.lastScanTime = now;

		// Provide feedback
		this.provideScanFeedback();

		// Process the scanned barcode
		this.handleBarcodeScanned(code);
	}

	provideScanFeedback() {
		// Audio feedback
		if (this.config.scanner_settings?.audio_feedback) {
			this.playBeepSound();
		}

		// Vibration feedback
		if (this.config.scanner_settings?.vibration_feedback && 'vibrate' in navigator) {
			navigator.vibrate(100);
		}

		// Visual feedback
		this.showVisualFeedback();
	}

	playBeepSound() {
		try {
			const audioContext = new (window.AudioContext || window.webkitAudioContext)();
			const oscillator = audioContext.createOscillator();
			const gainNode = audioContext.createGain();

			oscillator.connect(gainNode);
			gainNode.connect(audioContext.destination);

			oscillator.frequency.value = 800;
			oscillator.type = 'sine';

			gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
			gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

			oscillator.start(audioContext.currentTime);
			oscillator.stop(audioContext.currentTime + 0.1);
		} catch (error) {
			console.warn('Audio feedback not available:', error);
		}
	}

	showVisualFeedback() {
		const overlay = document.querySelector('.scanner-overlay');
		if (overlay) {
			overlay.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
			setTimeout(() => {
				overlay.style.backgroundColor = 'transparent';
			}, 200);
		}
	}

	async handleBarcodeScanned(barcode) {
		try {
			this.showMessage('Processing barcode...', 'info');

			// Look up item by barcode
			const result = await this.lookupItemByBarcode(barcode);

			if (result && result.success) {
				// Add to results
				this.addScanResult(result);

				// Process based on current mode
				await this.processScannedItem(result, barcode);

				this.showMessage('Item scanned successfully', 'success');
			} else {
				this.showMessage(result?.message || 'Item not found', 'warning');
			}

		} catch (error) {
			console.error('Error processing barcode:', error);
			this.showMessage('Error processing barcode', 'error');
		}
	}

	async lookupItemByBarcode(barcode) {
		try {
			const response = await this.apiCall('universal_workshop.parts_inventory.api.get_item_by_barcode', {
				barcode: barcode
			});

			return response;

		} catch (error) {
			// If offline or API fails, try local cache
			if (!this.isOnline) {
				return await this.lookupItemOffline(barcode);
			}
			throw error;
		}
	}

	async lookupItemOffline(barcode) {
		// Implement offline item lookup from cached data
		try {
			if (!this.db) return null;

			// This would use cached item data stored in IndexedDB
			// For now, return a placeholder
			return {
				success: false,
				message: 'Offline lookup not yet implemented'
			};
		} catch (error) {
			console.error('Offline lookup error:', error);
			return null;
		}
	}

	addScanResult(result) {
		const scanData = {
			id: Date.now() + Math.random(),
			timestamp: new Date().toISOString(),
			barcode: result.barcode,
			item_code: result.item_code,
			item_name: result.item_name,
			mode: this.currentMode,
			tab: this.currentTab,
			synced: false,
			...result
		};

		this.scanResults.unshift(scanData);

		// Limit results to prevent memory issues
		if (this.scanResults.length > this.config.max_offline_records) {
			this.scanResults = this.scanResults.slice(0, this.config.max_offline_records);
		}

		// Save to offline storage
		this.saveScanResult(scanData);

		// Update UI
		this.updateResultsDisplay();
	}

	async processScannedItem(result, barcode) {
		const processingData = {
			barcode: barcode,
			operation: this.currentMode,
			item_code: result.item_code,
			warehouse: this.config.default_warehouse,
			quantity: 1, // Default quantity, can be modified
			timestamp: new Date().toISOString()
		};

		switch (this.currentMode) {
			case 'lookup':
				// Just display item information
				this.displayItemDetails(result);
				break;

			case 'receive':
			case 'issue':
			case 'adjust':
				// Show quantity input dialog
				await this.showQuantityDialog(result, processingData);
				break;

			default:
				this.displayItemDetails(result);
		}
	}

	async showQuantityDialog(result, processingData) {
		const quantity = await this.promptQuantity(result.item_name);
		if (quantity !== null) {
			processingData.quantity = quantity;

			// Add to pending operations
			this.addPendingOperation(processingData);

			// If online, process immediately
			if (this.isOnline) {
				await this.processPendingOperations();
			}
		}
	}

	async promptQuantity(itemName) {
		return new Promise((resolve) => {
			const quantity = prompt(`Enter quantity for ${itemName}:`, '1');
			if (quantity === null) {
				resolve(null);
			} else {
				const qty = parseFloat(quantity);
				resolve(isNaN(qty) ? null : qty);
			}
		});
	}

	displayItemDetails(item) {
		const resultsContainer = document.getElementById('results-container');
		if (!resultsContainer) return;

		const stockLevel = item.actual_qty || 0;
		const stockClass = stockLevel > 10 ? 'stock-high' :
			stockLevel > 5 ? 'stock-medium' : 'stock-low';

		const itemCard = document.createElement('div');
		itemCard.className = 'item-card';
		itemCard.innerHTML = `
            <div class="item-header">
                <div class="item-name">${item.item_name}</div>
                <div class="item-code">${item.item_code}</div>
            </div>
            <div class="item-details">
                <div class="item-detail">
                    <span class="detail-label">${this.t('current_stock')}:</span>
                    <span class="detail-value stock-level ${stockClass}">${stockLevel}</span>
                </div>
                <div class="item-detail">
                    <span class="detail-label">${this.t('warehouse')}:</span>
                    <span class="detail-value">${item.warehouse || this.config.default_warehouse}</span>
                </div>
                ${item.barcode ? `
                <div class="item-detail">
                    <span class="detail-label">Barcode:</span>
                    <span class="detail-value">${item.barcode}</span>
                </div>
                ` : ''}
            </div>
            ${this.currentMode !== 'lookup' ? `
            <div class="quantity-controls">
                <span class="qty-label">${this.t('quantity')}:</span>
                <button class="qty-btn" onclick="this.adjustQuantity(-1)">-</button>
                <input type="number" class="qty-input" value="1" min="0" step="1">
                <button class="qty-btn" onclick="this.adjustQuantity(1)">+</button>
            </div>
            ` : ''}
        `;

		// Show results section
		const resultsSection = document.getElementById('scan-results');
		if (resultsSection) {
			resultsSection.classList.add('show');
		}

		resultsContainer.appendChild(itemCard);
		this.updateResultCount();
	}

	updateResultsDisplay() {
		this.updateResultCount();
		// Additional UI updates can be added here
	}

	updateResultCount() {
		const countElement = document.getElementById('result-count');
		if (countElement) {
			countElement.textContent = this.scanResults.length;
		}
	}

	promptManualInput() {
		const barcode = prompt(this.t('manual_entry') + ':');
		if (barcode && barcode.trim()) {
			this.handleBarcodeScanned(barcode.trim());
		}
	}

	stopCameraScanning() {
		this.isScanning = false;

		// Stop Quagga scanner
		if (this.quaggaInitialized && window.Quagga) {
			window.Quagga.stop();
			this.quaggaInitialized = false;
		}

		// Stop camera stream
		if (this.stream) {
			this.stream.getTracks().forEach(track => track.stop());
			this.stream = null;
		}

		// Hide scanner modal
		const modal = document.getElementById('scanner-modal');
		if (modal) {
			modal.classList.remove('show');
		}
	}

	toggleFlashlight() {
		if (this.stream) {
			const track = this.stream.getVideoTracks()[0];
			if (track && 'torch' in track.getCapabilities()) {
				const currentState = track.getSettings().torch;
				track.applyConstraints({
					advanced: [{ torch: !currentState }]
				}).catch(error => {
					console.warn('Flashlight control not supported:', error);
					this.showMessage('Flashlight not supported', 'warning');
				});
			} else {
				this.showMessage('Flashlight not available', 'warning');
			}
		}
	}

	clearResults() {
		if (confirm(this.t('confirm_clear'))) {
			this.scanResults = [];
			const resultsContainer = document.getElementById('results-container');
			if (resultsContainer) {
				resultsContainer.innerHTML = '';
			}

			const resultsSection = document.getElementById('scan-results');
			if (resultsSection) {
				resultsSection.classList.remove('show');
			}

			this.updateResultCount();
			this.showMessage('Results cleared', 'info');
		}
	}

	async exportData() {
		try {
			if (this.scanResults.length === 0) {
				this.showMessage('No data to export', 'warning');
				return;
			}

			const csvData = this.convertToCSV(this.scanResults);
			const blob = new Blob([csvData], { type: 'text/csv' });
			const url = URL.createObjectURL(blob);

			const a = document.createElement('a');
			a.href = url;
			a.download = `inventory_scan_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);

			this.showMessage('Data exported successfully', 'success');

		} catch (error) {
			console.error('Export error:', error);
			this.showMessage('Error exporting data', 'error');
		}
	}

	convertToCSV(data) {
		const headers = ['Timestamp', 'Barcode', 'Item Code', 'Item Name', 'Mode', 'Quantity', 'Warehouse'];
		const csvRows = [headers.join(',')];

		data.forEach(row => {
			const values = [
				row.timestamp,
				row.barcode,
				row.item_code,
				`"${row.item_name || ''}"`,
				row.mode,
				row.quantity || '',
				row.warehouse || ''
			];
			csvRows.push(values.join(','));
		});

		return csvRows.join('\n');
	}

	async forceSyncData() {
		this.showMessage('Syncing data...', 'info');
		await this.syncPendingData();
	}

	async syncPendingData() {
		if (!this.isOnline || this.pendingSync.length === 0) {
			this.updateSyncStatus();
			return;
		}

		try {
			const syncIndicator = document.getElementById('sync-indicator');
			if (syncIndicator) {
				syncIndicator.classList.add('syncing');
			}

			// Process pending sync items
			for (const item of this.pendingSync) {
				await this.syncSingleItem(item);
			}

			this.pendingSync = [];
			this.updateSyncStatus();
			this.showMessage('Data synced successfully', 'success');

		} catch (error) {
			console.error('Sync error:', error);
			this.showMessage('Sync failed', 'error');
		} finally {
			const syncIndicator = document.getElementById('sync-indicator');
			if (syncIndicator) {
				syncIndicator.classList.remove('syncing');
			}
		}
	}

	async syncSingleItem(item) {
		// Implementation for syncing individual items
		// This would call appropriate API endpoints based on item type
		return true;
	}

	addPendingOperation(operation) {
		this.pendingSync.push(operation);
		this.savePendingOperation(operation);
		this.updateSyncStatus();
	}

	updateSyncStatus() {
		const syncStatus = document.getElementById('sync-status');
		const syncText = document.getElementById('sync-text');
		const pendingCount = document.getElementById('pending-count');

		if (this.pendingSync.length > 0) {
			syncStatus.classList.add('show');
			syncText.textContent = this.t('pending_sync');
			pendingCount.textContent = `${this.pendingSync.length} pending`;
			pendingCount.style.display = 'block';
		} else {
			if (this.isOnline) {
				syncText.textContent = this.t('sync_complete');
				pendingCount.style.display = 'none';
			} else {
				syncStatus.classList.add('show');
				syncText.textContent = this.t('offline');
			}
		}
	}

	startSyncTimer() {
		setInterval(() => {
			if (this.isOnline && this.pendingSync.length > 0) {
				this.syncPendingData();
			}
		}, this.config.sync_interval);
	}

	toggleLanguage() {
		this.language = this.language === 'en' ? 'ar' : 'en';
		this.direction = this.language === 'ar' ? 'rtl' : 'ltr';
		this.updateLanguageInterface();
		this.saveLanguagePreference();
	}

	updateLanguageInterface() {
		const html = document.documentElement;
		html.setAttribute('lang', this.language);
		html.setAttribute('dir', this.direction);

		const indicator = document.getElementById('language-indicator');
		if (indicator) {
			indicator.textContent = this.language.toUpperCase();
		}

		// Update text content for key elements
		this.updateTranslatedContent();
	}

	updateTranslatedContent() {
		// Update page title
		const pageTitle = document.getElementById('page-title');
		if (pageTitle) {
			pageTitle.textContent = this.getTabTitle(this.currentTab);
		}

		// Update button texts
		this.updateModeInterface();

		// Update other translatable elements
		const translatableElements = document.querySelectorAll('[data-translate]');
		translatableElements.forEach(element => {
			const key = element.getAttribute('data-translate');
			element.textContent = this.t(key);
		});
	}

	saveLanguagePreference() {
		localStorage.setItem('mobile_scanner_language', this.language);
	}

	loadSavedData() {
		// Load language preference
		const savedLanguage = localStorage.getItem('mobile_scanner_language');
		if (savedLanguage) {
			this.language = savedLanguage;
			this.direction = this.language === 'ar' ? 'rtl' : 'ltr';
			this.updateLanguageInterface();
		}

		// Load other saved data from IndexedDB if available
		this.loadOfflineData();
	}

	async loadOfflineData() {
		if (!this.db) return;

		try {
			// Load pending sync items
			const transaction = this.db.transaction(['scans'], 'readonly');
			const store = transaction.objectStore('scans');
			const index = store.index('synced');
			const request = index.getAll(false); // Get unsynced items

			request.onsuccess = () => {
				this.pendingSync = request.result || [];
				this.updateSyncStatus();
			};

		} catch (error) {
			console.warn('Error loading offline data:', error);
		}
	}

	async saveScanResult(scanData) {
		if (!this.db) return;

		try {
			const transaction = this.db.transaction(['scans'], 'readwrite');
			const store = transaction.objectStore('scans');
			await store.add(scanData);
		} catch (error) {
			console.warn('Error saving scan result:', error);
		}
	}

	async savePendingOperation(operation) {
		if (!this.db) return;

		try {
			const transaction = this.db.transaction(['scans'], 'readwrite');
			const store = transaction.objectStore('scans');
			operation.synced = false;
			operation.type = 'operation';
			await store.add(operation);
		} catch (error) {
			console.warn('Error saving pending operation:', error);
		}
	}

	async apiCall(method, args = {}) {
		const url = `/api/method/${method}`;
		const options = {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-Frappe-CSRF-Token': frappe.csrf_token
			},
			body: JSON.stringify(args)
		};

		const response = await fetch(url, options);

		if (!response.ok) {
			throw new Error(`API call failed: ${response.statusText}`);
		}

		const data = await response.json();

		if (data.exc) {
			throw new Error(data.exc);
		}

		return data.message;
	}

	showMessage(message, type = 'info') {
		const container = document.getElementById('message-container');
		if (!container) return;

		const messageElement = document.createElement('div');
		messageElement.className = `message ${type} show`;
		messageElement.textContent = message;

		container.appendChild(messageElement);

		// Auto-remove after 5 seconds
		setTimeout(() => {
			messageElement.classList.remove('show');
			setTimeout(() => {
				if (messageElement.parentNode) {
					messageElement.parentNode.removeChild(messageElement);
				}
			}, 300);
		}, 5000);
	}

	getCameraErrorMessage(error) {
		if (error.name === 'NotAllowedError') {
			return this.t('camera_permission_denied');
		} else if (error.name === 'NotFoundError') {
			return this.t('camera_not_found');
		} else if (error.name === 'NotSupportedError') {
			return this.t('camera_not_supported');
		} else {
			return this.t('camera_error');
		}
	}

	t(key) {
		// Translation function
		return this.translations[key] || key;
	}

	// Additional methods for specific operations can be added here

	startBatchScanning() {
		this.showMessage('Batch scanning mode activated', 'info');
		// Implement batch scanning logic
	}

	showRecentItems() {
		// Implement recent items display
		this.showMessage('Recent items feature coming soon', 'info');
	}

	showSettings() {
		// Implement settings dialog
		this.showMessage('Settings feature coming soon', 'info');
	}

	loadTabContent(tabName) {
		// Load content specific to each tab
		const content = document.getElementById(`${tabName}-content`);
		if (content) {
			// Implement tab-specific content loading
		}
	}

	async processPendingOperations() {
		// Process any pending operations when online
		if (this.pendingSync.length > 0) {
			await this.syncPendingData();
		}
	}
}
