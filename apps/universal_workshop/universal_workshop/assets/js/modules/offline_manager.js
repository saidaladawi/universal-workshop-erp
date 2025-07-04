/**
 * Universal Workshop ERP - Offline Capability Manager
 * Handles offline data storage, sync queue management, and connectivity state
 * Arabic/English localization support for Omani automotive workshops
 */

class UniversalOfflineManager {
    constructor() {
        this.dbName = 'UniversalWorkshopOfflineDB';
        this.dbVersion = 1;
        this.db = null;
        this.isOnline = navigator.onLine;
        this.syncQueue = [];
        this.conflictQueue = [];
        
        this.init();
    }

    async init() {
        try {
            // Register Service Worker
            if ('serviceWorker' in navigator) {
                await this.registerServiceWorker();
            }

            // Initialize IndexedDB
            await this.initIndexedDB();

            // Setup connectivity listeners
            this.setupConnectivityListeners();

            // Setup sync manager
            this.setupSyncManager();

            // Load pending sync queue
            await this.loadSyncQueue();

            console.log('Universal Workshop Offline Manager initialized successfully');
        } catch (error) {
            console.error('Error initializing offline manager:', error);
            frappe.msgprint(__('Failed to initialize offline capabilities'));
        }
    }

    async registerServiceWorker() {
        try {
            const registration = await navigator.serviceWorker.register('/assets/universal_workshop/js/service_worker.js');
            console.log('Service Worker registered successfully:', registration);
            
            // Listen for service worker messages
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event.data);
            });

            return registration;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            throw error;
        }
    }

    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Inventory transactions store
                if (!db.objectStoreNames.contains('inventory_transactions')) {
                    const inventoryStore = db.createObjectStore('inventory_transactions', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    inventoryStore.createIndex('item_code', 'item_code');
                    inventoryStore.createIndex('timestamp', 'timestamp');
                    inventoryStore.createIndex('sync_status', 'sync_status');
                    inventoryStore.createIndex('transaction_type', 'transaction_type');
                }

                // Sync queue store
                if (!db.objectStoreNames.contains('sync_queue')) {
                    const syncStore = db.createObjectStore('sync_queue', {
                        keyPath: 'queue_id',
                        autoIncrement: true
                    });
                    syncStore.createIndex('priority', 'priority');
                    syncStore.createIndex('created_at', 'created_at');
                    syncStore.createIndex('retry_count', 'retry_count');
                }

                // Conflict resolution store
                if (!db.objectStoreNames.contains('conflicts')) {
                    const conflictStore = db.createObjectStore('conflicts', {
                        keyPath: 'conflict_id',
                        autoIncrement: true
                    });
                    conflictStore.createIndex('item_code', 'item_code');
                    conflictStore.createIndex('resolution_status', 'resolution_status');
                }

                // Cached data store (for items, customers, etc.)
                if (!db.objectStoreNames.contains('cached_data')) {
                    const cacheStore = db.createObjectStore('cached_data', {
                        keyPath: 'cache_key'
                    });
                    cacheStore.createIndex('last_updated', 'last_updated');
                    cacheStore.createIndex('data_type', 'data_type');
                }

                // Audit logs store (for VAT compliance)
                if (!db.objectStoreNames.contains('audit_logs')) {
                    const auditStore = db.createObjectStore('audit_logs', {
                        keyPath: 'log_id',
                        autoIncrement: true
                    });
                    auditStore.createIndex('timestamp', 'timestamp');
                    auditStore.createIndex('user_id', 'user_id');
                    auditStore.createIndex('transaction_id', 'transaction_id');
                }
            };
        });
    }

    setupConnectivityListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.onConnectivityChange(true);
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.onConnectivityChange(false);
        });

        // Ping server to check actual connectivity
        setInterval(() => {
            this.checkRealConnectivity();
        }, 30000); // Check every 30 seconds
    }

    async checkRealConnectivity() {
        try {
            const response = await fetch('/api/method/ping', {
                method: 'GET',
                cache: 'no-cache'
            });
            
            const actuallyOnline = response.ok;
            if (actuallyOnline !== this.isOnline) {
                this.isOnline = actuallyOnline;
                this.onConnectivityChange(actuallyOnline);
            }
        } catch (error) {
            if (this.isOnline) {
                this.isOnline = false;
                this.onConnectivityChange(false);
            }
        }
    }

    onConnectivityChange(isOnline) {
        // Update UI status indicator
        this.updateConnectivityStatus(isOnline);

        if (isOnline) {
            // Start sync process when coming back online
            this.startBackgroundSync();
        } else {
            // Show offline mode indicator
            this.showOfflineNotification();
        }
    }

    updateConnectivityStatus(isOnline) {
        const statusIndicator = document.querySelector('.connectivity-status');
        if (statusIndicator) {
            statusIndicator.className = \`connectivity-status \${isOnline ? 'online' : 'offline'}\`;
            statusIndicator.textContent = isOnline ? __('Online') : __('Offline');
        }

        // Add to main toolbar if doesn't exist
        if (!statusIndicator) {
            this.createConnectivityIndicator(isOnline);
        }
    }

    createConnectivityIndicator(isOnline) {
        const indicator = document.createElement('div');
        indicator.className = \`connectivity-status \${isOnline ? 'online' : 'offline'}\`;
        indicator.innerHTML = \`
            <i class="fa \${isOnline ? 'fa-wifi' : 'fa-wifi-slash'}"></i>
            <span>\${isOnline ? __('Online') : __('Offline')}</span>
        \`;
        
        const toolbar = document.querySelector('.navbar-right') || document.querySelector('.toolbar');
        if (toolbar) {
            toolbar.appendChild(indicator);
        }
    }

    showOfflineNotification() {
        frappe.show_alert({
            message: __('You are now offline. Changes will be saved locally and synced when connection is restored.'),
            indicator: 'orange'
        }, 5);
    }

    // Inventory Transaction Management
    async storeInventoryTransaction(transactionData) {
        try {
            const transaction = {
                ...transactionData,
                id: this.generateOfflineId(),
                timestamp: new Date().toISOString(),
                sync_status: 'pending',
                created_offline: !this.isOnline,
                user_id: frappe.session.user,
                device_fingerprint: await this.getDeviceFingerprint()
            };

            await this.addToStore('inventory_transactions', transaction);
            
            // Add to sync queue
            await this.addToSyncQueue({
                action: 'inventory_transaction',
                data: transaction,
                priority: transactionData.priority || 'medium'
            });

            // Log for audit compliance
            await this.logAuditEntry({
                action: 'inventory_transaction_stored',
                transaction_id: transaction.id,
                data: transaction,
                offline_mode: !this.isOnline
            });

            return transaction;
        } catch (error) {
            console.error('Error storing inventory transaction:', error);
            throw error;
        }
    }

    async addToStore(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Utility Methods
    generateOfflineId() {
        return \`offline_\${Date.now()}_\${Math.random().toString(36).substr(2, 9)}\`;
    }

    async getDeviceFingerprint() {
        // Generate device fingerprint for security and audit
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Universal Workshop ERP', 2, 2);
        
        return btoa(JSON.stringify({
            canvas: canvas.toDataURL(),
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screen: \`\${screen.width}x\${screen.height}\`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }));
    }

    async logAuditEntry(auditData) {
        const logEntry = {
            ...auditData,
            log_id: this.generateOfflineId(),
            timestamp: new Date().toISOString(),
            user_id: frappe.session.user,
            session_id: frappe.session.sid
        };

        await this.addToStore('audit_logs', logEntry);
    }

    getStatus() {
        return {
            isOnline: this.isOnline,
            pendingSyncCount: this.syncQueue.length,
            conflictCount: this.conflictQueue.length,
            dbReady: !!this.db
        };
    }
}

// Initialize offline manager when document is ready
frappe.ready(() => {
    if (frappe.boot.user !== 'Guest') {
        window.universalOfflineManager = new UniversalOfflineManager();
    }
});

// Extend frappe namespace
frappe.universal_workshop = frappe.universal_workshop || {};
frappe.universal_workshop.offline_manager = UniversalOfflineManager;
