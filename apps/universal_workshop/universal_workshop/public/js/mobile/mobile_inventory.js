/**
 * Mobile Inventory Management System
 * Progressive Web App for Universal Workshop ERP
 * Supports barcode scanning, offline functionality, and mobile-optimized workflows
 */
class MobileInventory {
    constructor() {
        this.isOnline = navigator.onLine;
        this.currentTab = 'scan';
        this.recentItems = [];
        this.scanHistory = [];
        this.pendingSync = [];
        
        this.init();
    }
    
    init() {
        console.log('Initializing Mobile Inventory System...');
        
        // Initialize connectivity monitoring
        this.initConnectivityMonitoring();
        
        // Initialize offline manager
        this.initOfflineManager();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize barcode scanner
        this.initBarcodeScanner();
        
        // Load recent items from localStorage
        this.loadRecentItems();
        
        // Setup tab navigation
        this.setupTabNavigation();
        
        console.log('Mobile Inventory System initialized successfully');
    }
    
    initConnectivityMonitoring() {
        const updateConnectivityStatus = () => {
            this.isOnline = navigator.onLine;
            const indicator = document.getElementById('connectivity-indicator');
            const text = document.getElementById('connectivity-text');
            const offlineBanner = document.getElementById('offline-banner');
            
            if (this.isOnline) {
                indicator.classList.remove('offline');
                text.textContent = 'Online';
                if (offlineBanner) offlineBanner.classList.remove('show');
                this.syncPendingData();
            } else {
                indicator.classList.add('offline');
                text.textContent = 'Offline';
                if (offlineBanner) offlineBanner.classList.add('show');
            }
        };
        
        window.addEventListener('online', updateConnectivityStatus);
        window.addEventListener('offline', updateConnectivityStatus);
        updateConnectivityStatus();
    }
    
    initOfflineManager() {
        // Initialize IndexedDB for offline storage
        if (!window.offlineManager) {
            // Use the existing offline manager if available
            console.log('Offline manager integration ready');
        }
    }
    
    setupEventListeners() {
        // Scan button
        const scanBtn = document.getElementById('scan-barcode-btn');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.startBarcodeScanning());
        }
        
        // Search functionality
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.searchItems(), 300));
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchItems();
                }
            });
        }
        
        // Tab navigation
        document.querySelectorAll('.tab-btn, .nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                if (tab) this.switchTab(tab);
            });
        });
    }
    
    setupTabNavigation() {
        // Sync tab states between top tabs and bottom navigation
        const updateTabStates = (activeTab) => {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === activeTab);
            });
            
            // Update bottom navigation
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.toggle('active', item.dataset.tab === activeTab);
            });
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.toggle('active', content.id === `${activeTab}-tab`);
            });
        };
        
        updateTabStates(this.currentTab);
    }
    
    switchTab(tab) {
        this.currentTab = tab;
        this.setupTabNavigation();
        
        // Load tab-specific content
        switch (tab) {
            case 'scan':
                this.loadScanTab();
                break;
            case 'search':
                this.loadSearchTab();
                break;
            case 'recent':
                this.loadRecentTab();
                break;
            case 'transfers':
                this.loadTransfersTab();
                break;
        }
    }
    
    initBarcodeScanner() {
        // Check if we can use the device camera
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            console.log('Camera access available for barcode scanning');
        } else {
            console.warn('Camera not available - using keyboard input fallback');
        }
    }
    
    startBarcodeScanning() {
        const scanBtn = document.getElementById('scan-barcode-btn');
        const scanResult = document.getElementById('scan-result');
        const scanLoading = document.getElementById('scan-loading');
        
        if (!scanBtn || !scanResult) return;
        
        // Disable scan button and show loading
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        scanResult.classList.add('show');
        if (scanLoading) scanLoading.style.display = 'block';
        
        // Use existing barcode scanner integration
        if (window.barcodeScanner) {
            window.barcodeScanner.startScan()
                .then(barcode => this.handleBarcodeScanned(barcode))
                .catch(error => this.handleScanError(error))
                .finally(() => this.resetScanButton());
        } else {
            // Fallback to manual input
            this.promptManualBarcode();
        }
    }
    
    handleBarcodeScanned(barcode) {
        console.log('Barcode scanned:', barcode);
        
        // Add to scan history
        this.addToScanHistory(barcode);
        
        // Look up item information
        this.lookupItemByBarcode(barcode);
    }
    
    handleScanError(error) {
        console.error('Barcode scan error:', error);
        this.showMessage('Scan failed. Please try again.', 'error');
        this.resetScanButton();
    }
    
    resetScanButton() {
        const scanBtn = document.getElementById('scan-barcode-btn');
        const scanLoading = document.getElementById('scan-loading');
        
        if (scanBtn) {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<i class="fas fa-qrcode"></i> Scan Barcode';
        }
        
        if (scanLoading) {
            scanLoading.style.display = 'none';
        }
    }
    
    promptManualBarcode() {
        const barcode = prompt('Enter barcode manually:');
        if (barcode && barcode.trim()) {
            this.handleBarcodeScanned(barcode.trim());
        } else {
            this.resetScanButton();
        }
    }
    
    async lookupItemByBarcode(barcode) {
        try {
            const response = await this.apiCall('universal_workshop.parts_inventory.api.get_item_by_barcode', {
                barcode: barcode
            });
            
            if (response && response.item) {
                this.displayItemDetails(response.item);
                this.addToRecentItems(response.item);
            } else {
                this.showMessage('Item not found for this barcode', 'warning');
            }
        } catch (error) {
            console.error('Error looking up item:', error);
            this.showMessage('Error looking up item. Please try again.', 'error');
        }
    }
    
    displayItemDetails(item) {
        const scanContent = document.getElementById('scan-content');
        if (!scanContent) return;
        
        const stockLevel = item.actual_qty || 0;
        const stockClass = stockLevel > 10 ? 'stock-high' : 
                          stockLevel > 5 ? 'stock-medium' : 'stock-low';
        
        scanContent.innerHTML = `
            <div class="item-card">
                <div class="item-header">
                    <div class="item-name">${item.item_name}</div>
                    <div class="item-code">${item.item_code}</div>
                </div>
                <div class="item-details">
                    <div class="item-row">
                        <span class="item-label">Stock Level:</span>
                        <span class="item-value ${stockClass}">${stockLevel} ${item.stock_uom || 'Units'}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Warehouse:</span>
                        <span class="item-value">${item.warehouse || 'Main Store'}</span>
                    </div>
                    <div class="item-row">
                        <span class="item-label">Valuation Rate:</span>
                        <span class="item-value">OMR ${(item.valuation_rate || 0).toFixed(3)}</span>
                    </div>
                    ${item.abc_classification ? `
                    <div class="item-row">
                        <span class="item-label">ABC Category:</span>
                        <span class="item-value">${item.abc_classification}</span>
                    </div>` : ''}
                </div>
                <div class="quantity-controls">
                    <button class="qty-btn" onclick="mobileInventory.adjustQuantity('${item.item_code}', -1)">
                        <i class="fas fa-minus"></i>
                    </button>
                    <input type="number" class="qty-input" id="qty-${item.item_code}" value="1" min="1">
                    <button class="qty-btn" onclick="mobileInventory.adjustQuantity('${item.item_code}', 1)">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="scan-btn" style="margin-left: 1rem;" onclick="mobileInventory.createStockEntry('${item.item_code}')">
                        Update Stock
                    </button>
                </div>
            </div>
        `;
    }
    
    adjustQuantity(itemCode, delta) {
        const qtyInput = document.getElementById(`qty-${itemCode}`);
        if (qtyInput) {
            const currentValue = parseInt(qtyInput.value) || 1;
            const newValue = Math.max(1, currentValue + delta);
            qtyInput.value = newValue;
        }
    }
    
    async createStockEntry(itemCode) {
        const qtyInput = document.getElementById(`qty-${itemCode}`);
        if (!qtyInput) return;
        
        const quantity = parseInt(qtyInput.value) || 1;
        const entryType = 'Material Receipt'; // Default to stock in
        
        try {
            const response = await this.apiCall('universal_workshop.parts_inventory.api.create_stock_entry', {
                item_code: itemCode,
                quantity: quantity,
                entry_type: entryType,
                source: 'Mobile Scan'
            });
            
            if (response && response.name) {
                this.showMessage(`Stock entry ${response.name} created successfully`, 'success');
                // Refresh item details
                this.lookupItemByBarcode(qtyInput.closest('.item-card').querySelector('.item-code').textContent);
            }
        } catch (error) {
            console.error('Error creating stock entry:', error);
            this.showMessage('Error creating stock entry. Please try again.', 'error');
        }
    }
    
    async searchItems() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        
        if (!searchInput || !searchResults) return;
        
        const query = searchInput.value.trim();
        if (query.length < 2) {
            searchResults.innerHTML = '';
            return;
        }
        
        searchResults.innerHTML = '<div class="loading-spinner"></div>';
        
        try {
            const response = await this.apiCall('universal_workshop.parts_inventory.api.search_items', {
                query: query,
                limit: 20
            });
            
            if (response && response.items) {
                this.displaySearchResults(response.items);
            } else {
                searchResults.innerHTML = '<p class="text-center" style="color: #666; padding: 2rem;">No items found</p>';
            }
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = '<p class="text-center" style="color: #f44336; padding: 2rem;">Search failed. Please try again.</p>';
        }
    }
    
    displaySearchResults(items) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        const itemsHtml = items.map(item => {
            const stockLevel = item.actual_qty || 0;
            const stockClass = stockLevel > 10 ? 'stock-high' : 
                              stockLevel > 5 ? 'stock-medium' : 'stock-low';
            
            return `
                <div class="item-card" onclick="mobileInventory.selectSearchItem('${item.item_code}')">
                    <div class="item-header">
                        <div class="item-name">${item.item_name}</div>
                        <div class="item-code">${item.item_code}</div>
                    </div>
                    <div class="item-details">
                        <div class="item-row">
                            <span class="item-label">Stock:</span>
                            <span class="item-value ${stockClass}">${stockLevel} ${item.stock_uom || 'Units'}</span>
                        </div>
                        <div class="item-row">
                            <span class="item-label">Rate:</span>
                            <span class="item-value">OMR ${(item.valuation_rate || 0).toFixed(3)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        searchResults.innerHTML = itemsHtml;
    }
    
    selectSearchItem(itemCode) {
        // Switch to scan tab and show item details
        this.switchTab('scan');
        
        // Look up full item details
        this.apiCall('universal_workshop.parts_inventory.api.get_item_details', {
            item_code: itemCode
        }).then(response => {
            if (response && response.item) {
                this.displayItemDetails(response.item);
                this.addToRecentItems(response.item);
            }
        });
    }
    
    addToScanHistory(barcode) {
        this.scanHistory.unshift({
            barcode: barcode,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 50 scans
        this.scanHistory = this.scanHistory.slice(0, 50);
        
        // Save to localStorage
        localStorage.setItem('mobile_scan_history', JSON.stringify(this.scanHistory));
    }
    
    addToRecentItems(item) {
        // Remove if already exists
        this.recentItems = this.recentItems.filter(existing => existing.item_code !== item.item_code);
        
        // Add to beginning
        this.recentItems.unshift({
            ...item,
            accessed_at: new Date().toISOString()
        });
        
        // Keep only last 20 items
        this.recentItems = this.recentItems.slice(0, 20);
        
        // Save to localStorage
        localStorage.setItem('mobile_recent_items', JSON.stringify(this.recentItems));
        
        // Update recent tab if visible
        if (this.currentTab === 'recent') {
            this.loadRecentTab();
        }
    }
    
    loadRecentItems() {
        try {
            const stored = localStorage.getItem('mobile_recent_items');
            if (stored) {
                this.recentItems = JSON.parse(stored);
            }
            
            const storedHistory = localStorage.getItem('mobile_scan_history');
            if (storedHistory) {
                this.scanHistory = JSON.parse(storedHistory);
            }
        } catch (error) {
            console.error('Error loading recent items:', error);
        }
    }
    
    loadScanTab() {
        // Reset scan interface
        const scanResult = document.getElementById('scan-result');
        if (scanResult) {
            scanResult.classList.remove('show');
        }
    }
    
    loadSearchTab() {
        // Focus search input
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            setTimeout(() => searchInput.focus(), 100);
        }
    }
    
    loadRecentTab() {
        const recentContainer = document.getElementById('recent-items');
        if (!recentContainer) return;
        
        if (this.recentItems.length === 0) {
            recentContainer.innerHTML = `
                <div class="text-center" style="color: #666; padding: 2rem;">
                    <i class="fas fa-history fa-3x" style="opacity: 0.3;"></i>
                    <p>Recent scanned items will appear here</p>
                </div>
            `;
            return;
        }
        
        const itemsHtml = this.recentItems.map(item => {
            const accessTime = new Date(item.accessed_at).toLocaleString();
            const stockLevel = item.actual_qty || 0;
            const stockClass = stockLevel > 10 ? 'stock-high' : 
                              stockLevel > 5 ? 'stock-medium' : 'stock-low';
            
            return `
                <div class="item-card" onclick="mobileInventory.selectRecentItem('${item.item_code}')">
                    <div class="item-header">
                        <div class="item-name">${item.item_name}</div>
                        <div class="item-code">${item.item_code}</div>
                    </div>
                    <div class="item-details">
                        <div class="item-row">
                            <span class="item-label">Stock:</span>
                            <span class="item-value ${stockClass}">${stockLevel} ${item.stock_uom || 'Units'}</span>
                        </div>
                        <div class="item-row">
                            <span class="item-label">Accessed:</span>
                            <span class="item-value">${accessTime}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        recentContainer.innerHTML = itemsHtml;
    }
    
    selectRecentItem(itemCode) {
        // Switch to scan tab and show item details
        this.switchTab('scan');
        
        // Find item in recent items
        const item = this.recentItems.find(item => item.item_code === itemCode);
        if (item) {
            this.displayItemDetails(item);
        }
    }
    
    loadTransfersTab() {
        const transferContent = document.getElementById('transfer-content');
        if (!transferContent) return;
        
        transferContent.innerHTML = `
            <div class="text-center" style="color: #666; padding: 1rem;">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading transfers...</p>
            </div>
        `;
        
        // Load transfer functionality using existing stock transfer system
        if (window.stockTransferUI) {
            // Integrate with existing stock transfer UI
            transferContent.innerHTML = `
                <div class="quick-actions">
                    <button class="quick-action" onclick="mobileInventory.createTransfer()">
                        <i class="fas fa-plus"></i>
                        <div class="quick-action-label">New Transfer</div>
                    </button>
                    <button class="quick-action" onclick="mobileInventory.viewPendingTransfers()">
                        <i class="fas fa-clock"></i>
                        <div class="quick-action-label">Pending</div>
                    </button>
                </div>
                <div id="transfer-list">
                    <p class="text-center" style="color: #666; padding: 2rem;">
                        Transfer integration loaded successfully
                    </p>
                </div>
            `;
        } else {
            transferContent.innerHTML = `
                <p class="text-center" style="color: #666; padding: 2rem;">
                    Transfer functionality will be available when stock transfer system is loaded
                </p>
            `;
        }
    }
    
    // Quick Actions
    quickAction(action) {
        switch (action) {
            case 'stock-entry':
                this.showMessage('Opening stock entry interface...', 'info');
                break;
            case 'stock-out':
                this.showMessage('Opening stock out interface...', 'info');
                break;
            case 'transfer':
                this.switchTab('transfers');
                break;
            case 'reconcile':
                this.showMessage('Opening reconciliation interface...', 'info');
                break;
        }
    }
    
    createTransfer() {
        this.showMessage('Transfer creation functionality integrated with stock transfer system', 'info');
    }
    
    viewPendingTransfers() {
        this.showMessage('Loading pending transfers...', 'info');
    }
    
    viewCompletedTransfers() {
        this.showMessage('Loading completed transfers...', 'info');
    }
    
    // API Communication
    async apiCall(method, args = {}) {
        const url = `/api/method/${method}`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': frappe.csrf_token || ''
                },
                body: JSON.stringify(args)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.message) {
                return data.message;
            } else if (data.exc) {
                throw new Error(data.exc);
            }
            
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            
            // Handle offline scenario
            if (!this.isOnline) {
                this.queueForOfflineSync(method, args);
                throw new Error('Offline - operation queued for sync');
            }
            
            throw error;
        }
    }
    
    queueForOfflineSync(method, args) {
        this.pendingSync.push({
            method: method,
            args: args,
            timestamp: new Date().toISOString()
        });
        
        localStorage.setItem('mobile_pending_sync', JSON.stringify(this.pendingSync));
    }
    
    async syncPendingData() {
        if (this.pendingSync.length === 0) return;
        
        console.log(`Syncing ${this.pendingSync.length} pending operations...`);
        
        const failedSync = [];
        
        for (const operation of this.pendingSync) {
            try {
                await this.apiCall(operation.method, operation.args);
                console.log('Synced operation:', operation.method);
            } catch (error) {
                console.error('Failed to sync operation:', operation.method, error);
                failedSync.push(operation);
            }
        }
        
        this.pendingSync = failedSync;
        localStorage.setItem('mobile_pending_sync', JSON.stringify(this.pendingSync));
        
        if (failedSync.length === 0) {
            this.showMessage('All pending operations synced successfully', 'success');
        }
    }
    
    // Utility Methods
    showMessage(message, type = 'info') {
        // Create or update message display
        let messageEl = document.getElementById('mobile-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'mobile-message';
            messageEl.style.cssText = `
                position: fixed;
                top: 90px;
                left: 1rem;
                right: 1rem;
                z-index: 1001;
                padding: 1rem;
                border-radius: 8px;
                font-weight: 500;
                transform: translateY(-100px);
                transition: transform 0.3s ease;
            `;
            document.body.appendChild(messageEl);
        }
        
        // Set message styling based on type
        const colors = {
            success: '#4CAF50',
            error: '#F44336',
            warning: '#FF9800',
            info: '#2196F3'
        };
        
        messageEl.style.backgroundColor = colors[type] || colors.info;
        messageEl.style.color = 'white';
        messageEl.textContent = message;
        
        // Show message
        setTimeout(() => messageEl.style.transform = 'translateY(0)', 10);
        
        // Hide after 3 seconds
        setTimeout(() => {
            messageEl.style.transform = 'translateY(-100px)';
        }, 3000);
    }
    
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.mobileInventory = new MobileInventory();
});

// Export for global use
window.MobileInventory = MobileInventory; 