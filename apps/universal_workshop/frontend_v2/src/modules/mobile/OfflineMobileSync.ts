/**
 * Offline Mobile Synchronization Manager
 * Phase 3: Sprint 3 Week 3 - Mobile Workflow Enhancement
 * 
 * Features:
 * - Intelligent offline data management
 * - Progressive sync with conflict resolution
 * - Arabic-aware sync status reporting
 * - Battery and network optimization
 * - Background sync with service workers
 */

import { WorkshopEventBus, WorkshopEventTypes } from '../../core/events';
import { SyncManager, ConflictResolver } from '../../core/sync';
import type { 
    SyncQueueItem, 
    SyncResult, 
    ConflictResolutionStrategy,
    OfflineCapabilities
} from '../../core/sync/types';

export interface MobileOfflineConfig {
    maxOfflineStorage: number; // MB
    syncInterval: number; // milliseconds
    batteryOptimization: boolean;
    networkAware: boolean;
    arabicStatusMessages: boolean;
    prioritizeLocalChanges: boolean;
    backgroundSync: boolean;
}

export interface OfflineDataCache {
    workOrders: Map<string, any>;
    inventory: Map<string, any>;
    customers: Map<string, any>;
    technicians: Map<string, any>;
    metadata: {
        lastSync: string;
        version: string;
        conflicts: number;
        pendingActions: number;
    };
}

export interface MobileSyncStatus {
    isOnline: boolean;
    isSyncing: boolean;
    pendingItems: number;
    lastSyncTime: string;
    batteryLevel?: number;
    networkType?: string;
    conflictsDetected: number;
    statusMessage: {
        english: string;
        arabic: string;
    };
}

export class OfflineMobileSync {
    private config: MobileOfflineConfig;
    private cache: OfflineDataCache;
    private syncManager: SyncManager;
    private conflictResolver: ConflictResolver;
    private eventBus: WorkshopEventBus;
    private syncWorker?: ServiceWorker;
    private networkInfo?: any;
    private batteryManager?: any;

    constructor(config: Partial<MobileOfflineConfig> = {}) {
        this.config = {
            maxOfflineStorage: 50, // 50MB default
            syncInterval: 30000, // 30 seconds
            batteryOptimization: true,
            networkAware: true,
            arabicStatusMessages: true,
            prioritizeLocalChanges: true,
            backgroundSync: true,
            ...config
        };

        this.cache = this.initializeCache();
        this.syncManager = new SyncManager();
        this.conflictResolver = new ConflictResolver();
        this.eventBus = WorkshopEventBus.getInstance();

        this.initialize();
    }

    /**
     * Initialize offline mobile sync capabilities
     */
    private async initialize(): Promise<void> {
        try {
            // Load cached data from IndexedDB
            await this.loadCachedData();

            // Setup network monitoring
            await this.setupNetworkMonitoring();

            // Setup battery optimization if supported
            if (this.config.batteryOptimization) {
                await this.setupBatteryOptimization();
            }

            // Register service worker for background sync
            if (this.config.backgroundSync) {
                await this.registerSyncWorker();
            }

            // Start periodic sync
            this.startPeriodicSync();

            // Listen for app lifecycle events
            this.setupAppLifecycleHandlers();

            this.eventBus.emit(WorkshopEventTypes.MOBILE_SYNC_INITIALIZED, {
                config: this.config,
                capabilities: await this.getOfflineCapabilities()
            });

            console.log('📱 OfflineMobileSync initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize OfflineMobileSync:', error);
            throw error;
        }
    }

    /**
     * Cache data for offline access
     */
    async cacheData(type: string, data: any[], metadata: any = {}): Promise<void> {
        try {
            const cacheKey = `mobile_cache_${type}`;
            const cacheData = {
                data,
                metadata: {
                    ...metadata,
                    cachedAt: new Date().toISOString(),
                    version: this.cache.metadata.version
                }
            };

            // Store in IndexedDB for persistence
            await this.storeInIndexedDB(cacheKey, cacheData);

            // Update in-memory cache
            switch (type) {
                case 'workOrders':
                    data.forEach(item => this.cache.workOrders.set(item.id, item));
                    break;
                case 'inventory':
                    data.forEach(item => this.cache.inventory.set(item.id, item));
                    break;
                case 'customers':
                    data.forEach(item => this.cache.customers.set(item.id, item));
                    break;
                case 'technicians':
                    data.forEach(item => this.cache.technicians.set(item.id, item));
                    break;
            }

            this.eventBus.emit(WorkshopEventTypes.MOBILE_DATA_CACHED, {
                type,
                count: data.length,
                size: this.calculateDataSize(cacheData)
            });

        } catch (error) {
            console.error(`❌ Failed to cache ${type} data:`, error);
            throw error;
        }
    }

    /**
     * Get cached data for offline access
     */
    async getCachedData(type: string, filters: any = {}): Promise<any[]> {
        try {
            let dataMap: Map<string, any>;

            switch (type) {
                case 'workOrders':
                    dataMap = this.cache.workOrders;
                    break;
                case 'inventory':
                    dataMap = this.cache.inventory;
                    break;
                case 'customers':
                    dataMap = this.cache.customers;
                    break;
                case 'technicians':
                    dataMap = this.cache.technicians;
                    break;
                default:
                    throw new Error(`Unknown cache type: ${type}`);
            }

            let data = Array.from(dataMap.values());

            // Apply filters
            if (Object.keys(filters).length > 0) {
                data = data.filter(item => {
                    return Object.entries(filters).every(([key, value]) => {
                        return item[key] === value || 
                               (Array.isArray(value) && value.includes(item[key]));
                    });
                });
            }

            return data;

        } catch (error) {
            console.error(`❌ Failed to get cached ${type} data:`, error);
            return [];
        }
    }

    /**
     * Queue action for offline sync
     */
    async queueOfflineAction(action: {
        type: string;
        operation: 'create' | 'update' | 'delete';
        entityType: string;
        entityId: string;
        data: any;
        priority?: 'high' | 'medium' | 'low';
        requiresInternet?: boolean;
    }): Promise<string> {
        
        const queueItem: SyncQueueItem = {
            id: `mobile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            action: action.type,
            data: action.data,
            priority: action.priority || 'medium',
            retryCount: 0,
            maxRetries: 3,
            metadata: {
                operation: action.operation,
                entityType: action.entityType,
                entityId: action.entityId,
                requiresInternet: action.requiresInternet || true,
                isMobile: true
            }
        };

        await this.syncManager.queueItem(queueItem);

        // Update cache optimistically for immediate UI feedback
        if (action.operation === 'update' || action.operation === 'create') {
            await this.updateCacheOptimistically(action);
        }

        this.eventBus.emit(WorkshopEventTypes.MOBILE_ACTION_QUEUED, {
            actionId: queueItem.id,
            type: action.type,
            entityType: action.entityType
        });

        return queueItem.id;
    }

    /**
     * Perform intelligent sync based on network and battery conditions
     */
    async performIntelligentSync(): Promise<SyncResult> {
        try {
            const status = await this.getSyncStatus();

            // Check if sync should be performed
            if (!this.shouldPerformSync(status)) {
                return {
                    success: false,
                    processed: 0,
                    failed: 0,
                    conflicts: 0,
                    message: this.config.arabicStatusMessages ? 
                        'تم تأجيل المزامنة لتوفير البطارية' : 
                        'Sync delayed to conserve battery'
                };
            }

            // Notify sync start
            this.eventBus.emit(WorkshopEventTypes.MOBILE_SYNC_STARTED, {
                timestamp: new Date().toISOString(),
                pendingItems: status.pendingItems
            });

            // Perform the sync
            const result = await this.syncManager.processQueue();

            // Handle conflicts with Arabic-aware resolution
            if (result.conflicts > 0) {
                await this.handleMobileConflicts(result.conflictDetails || []);
            }

            // Update sync status
            this.cache.metadata.lastSync = new Date().toISOString();
            this.cache.metadata.conflicts = result.conflicts;
            await this.persistCacheMetadata();

            this.eventBus.emit(WorkshopEventTypes.MOBILE_SYNC_COMPLETED, {
                result,
                timestamp: new Date().toISOString()
            });

            return result;

        } catch (error) {
            console.error('❌ Intelligent sync failed:', error);
            
            this.eventBus.emit(WorkshopEventTypes.MOBILE_SYNC_FAILED, {
                error: error.message,
                timestamp: new Date().toISOString()
            });

            return {
                success: false,
                processed: 0,
                failed: 1,
                conflicts: 0,
                message: this.config.arabicStatusMessages ? 
                    'فشل في المزامنة' : 
                    'Sync failed'
            };
        }
    }

    /**
     * Get current sync status with Arabic support
     */
    async getSyncStatus(): Promise<MobileSyncStatus> {
        const isOnline = navigator.onLine;
        const pendingItems = await this.syncManager.getQueueSize();
        const lastSyncTime = this.cache.metadata.lastSync;
        const conflictsDetected = this.cache.metadata.conflicts;

        let statusMessage = {
            english: 'Ready to sync',
            arabic: 'جاهز للمزامنة'
        };

        if (!isOnline) {
            statusMessage = {
                english: 'Offline - changes will sync when online',
                arabic: 'غير متصل - ستتم المزامنة عند الاتصال'
            };
        } else if (pendingItems > 0) {
            statusMessage = {
                english: `${pendingItems} items pending sync`,
                arabic: `${pendingItems} عنصر في انتظار المزامنة`
            };
        } else if (conflictsDetected > 0) {
            statusMessage = {
                english: `${conflictsDetected} conflicts need resolution`,
                arabic: `${conflictsDetected} تضارب يحتاج حل`
            };
        }

        return {
            isOnline,
            isSyncing: this.syncManager.isSyncing(),
            pendingItems,
            lastSyncTime,
            batteryLevel: this.batteryManager?.level,
            networkType: this.networkInfo?.effectiveType,
            conflictsDetected,
            statusMessage
        };
    }

    /**
     * Handle mobile-specific conflicts with Arabic awareness
     */
    private async handleMobileConflicts(conflicts: any[]): Promise<void> {
        for (const conflict of conflicts) {
            try {
                const strategy: ConflictResolutionStrategy = this.config.prioritizeLocalChanges ? 
                    'local_wins' : 'server_wins';

                const resolution = await this.conflictResolver.resolveConflict(
                    conflict,
                    strategy,
                    {
                        isMobile: true,
                        arabicSupport: this.config.arabicStatusMessages,
                        userContext: {
                            deviceType: 'mobile',
                            lastSeen: new Date().toISOString()
                        }
                    }
                );

                // Update cache with resolved data
                if (resolution.resolvedData) {
                    await this.updateCacheWithResolvedData(conflict.entityType, resolution.resolvedData);
                }

                this.eventBus.emit(WorkshopEventTypes.MOBILE_CONFLICT_RESOLVED, {
                    conflictId: conflict.id,
                    strategy: strategy,
                    resolution: resolution
                });

            } catch (error) {
                console.error('❌ Failed to resolve mobile conflict:', conflict.id, error);
            }
        }
    }

    /**
     * Get offline capabilities of the device
     */
    private async getOfflineCapabilities(): Promise<OfflineCapabilities> {
        const storage = await this.getStorageQuota();
        
        return {
            storageQuota: storage.quota,
            storageUsed: storage.usage,
            indexedDBSupported: 'indexedDB' in window,
            serviceWorkerSupported: 'serviceWorker' in navigator,
            backgroundSyncSupported: 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype,
            networkInfoSupported: 'connection' in navigator,
            batterySupported: 'getBattery' in navigator,
            maxOfflineStorage: this.config.maxOfflineStorage * 1024 * 1024 // Convert MB to bytes
        };
    }

    // Private helper methods
    private initializeCache(): OfflineDataCache {
        return {
            workOrders: new Map(),
            inventory: new Map(),
            customers: new Map(),
            technicians: new Map(),
            metadata: {
                lastSync: new Date().toISOString(),
                version: '1.0.0',
                conflicts: 0,
                pendingActions: 0
            }
        };
    }

    private async loadCachedData(): Promise<void> {
        try {
            const cacheTypes = ['workOrders', 'inventory', 'customers', 'technicians'];
            
            for (const type of cacheTypes) {
                const cacheKey = `mobile_cache_${type}`;
                const cachedData = await this.getFromIndexedDB(cacheKey);
                
                if (cachedData?.data) {
                    await this.cacheData(type, cachedData.data, cachedData.metadata);
                }
            }
        } catch (error) {
            console.error('❌ Failed to load cached data:', error);
        }
    }

    private async setupNetworkMonitoring(): Promise<void> {
        if ('connection' in navigator) {
            this.networkInfo = (navigator as any).connection;
            
            this.networkInfo.addEventListener('change', () => {
                this.eventBus.emit(WorkshopEventTypes.MOBILE_NETWORK_CHANGED, {
                    effectiveType: this.networkInfo.effectiveType,
                    downlink: this.networkInfo.downlink,
                    rtt: this.networkInfo.rtt
                });
            });
        }

        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.eventBus.emit(WorkshopEventTypes.MOBILE_ONLINE, {
                timestamp: new Date().toISOString()
            });
            
            // Trigger sync when coming online
            setTimeout(() => this.performIntelligentSync(), 1000);
        });

        window.addEventListener('offline', () => {
            this.eventBus.emit(WorkshopEventTypes.MOBILE_OFFLINE, {
                timestamp: new Date().toISOString()
            });
        });
    }

    private async setupBatteryOptimization(): Promise<void> {
        if ('getBattery' in navigator) {
            try {
                this.batteryManager = await (navigator as any).getBattery();
                
                this.batteryManager.addEventListener('levelchange', () => {
                    this.eventBus.emit(WorkshopEventTypes.MOBILE_BATTERY_CHANGED, {
                        level: this.batteryManager.level,
                        charging: this.batteryManager.charging
                    });
                });
            } catch (error) {
                console.warn('⚠️ Battery API not available:', error);
            }
        }
    }

    private async registerSyncWorker(): Promise<void> {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw-mobile-sync.js');
                this.syncWorker = registration.active || registration.waiting || registration.installing;
                
                console.log('📱 Mobile sync service worker registered');
            } catch (error) {
                console.error('❌ Failed to register sync service worker:', error);
            }
        }
    }

    private startPeriodicSync(): void {
        setInterval(async () => {
            if (navigator.onLine && this.shouldPerformSync(await this.getSyncStatus())) {
                await this.performIntelligentSync();
            }
        }, this.config.syncInterval);
    }

    private setupAppLifecycleHandlers(): void {
        // Handle app focus/blur for sync optimization
        document.addEventListener('visibilitychange', async () => {
            if (document.visibilityState === 'visible') {
                // App became visible, perform sync
                await this.performIntelligentSync();
            }
        });

        // Handle page unload to save pending data
        window.addEventListener('beforeunload', () => {
            this.persistCacheMetadata();
        });
    }

    private shouldPerformSync(status: MobileSyncStatus): boolean {
        // Don't sync if offline
        if (!status.isOnline) return false;

        // Don't sync if already syncing
        if (status.isSyncing) return false;

        // Don't sync if battery is too low (unless charging)
        if (this.batteryManager && 
            this.batteryManager.level < 0.20 && 
            !this.batteryManager.charging) {
            return false;
        }

        // Don't sync on slow networks unless high priority items
        if (this.networkInfo && 
            this.networkInfo.effectiveType === 'slow-2g' && 
            status.pendingItems < 5) {
            return false;
        }

        return true;
    }

    private async updateCacheOptimistically(action: any): Promise<void> {
        // Update cache immediately for better UX
        try {
            let targetMap: Map<string, any>;

            switch (action.entityType) {
                case 'workOrder':
                    targetMap = this.cache.workOrders;
                    break;
                case 'inventory':
                    targetMap = this.cache.inventory;
                    break;
                case 'customer':
                    targetMap = this.cache.customers;
                    break;
                case 'technician':
                    targetMap = this.cache.technicians;
                    break;
                default:
                    return;
            }

            if (action.operation === 'create' || action.operation === 'update') {
                targetMap.set(action.entityId, {
                    ...action.data,
                    _pendingSync: true,
                    _lastModified: new Date().toISOString()
                });
            } else if (action.operation === 'delete') {
                targetMap.delete(action.entityId);
            }

        } catch (error) {
            console.error('❌ Failed to update cache optimistically:', error);
        }
    }

    private async updateCacheWithResolvedData(entityType: string, data: any): Promise<void> {
        let targetMap: Map<string, any>;

        switch (entityType) {
            case 'workOrder':
                targetMap = this.cache.workOrders;
                break;
            case 'inventory':
                targetMap = this.cache.inventory;
                break;
            case 'customer':
                targetMap = this.cache.customers;
                break;
            case 'technician':
                targetMap = this.cache.technicians;
                break;
            default:
                return;
        }

        targetMap.set(data.id, {
            ...data,
            _pendingSync: false,
            _lastSynced: new Date().toISOString()
        });
    }

    private calculateDataSize(data: any): number {
        return new Blob([JSON.stringify(data)]).size;
    }

    private async getStorageQuota(): Promise<{ quota: number, usage: number }> {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            return {
                quota: estimate.quota || 0,
                usage: estimate.usage || 0
            };
        }
        
        return { quota: 0, usage: 0 };
    }

    private async storeInIndexedDB(key: string, data: any): Promise<void> {
        // Implement IndexedDB storage
        const request = indexedDB.open('WorkshopMobileCache', 1);
        
        return new Promise((resolve, reject) => {
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['cache'], 'readwrite');
                const store = transaction.objectStore('cache');
                
                store.put({ key, data, timestamp: Date.now() });
                transaction.oncomplete = () => resolve();
                transaction.onerror = () => reject(transaction.error);
            };
            
            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains('cache')) {
                    db.createObjectStore('cache', { keyPath: 'key' });
                }
            };
        });
    }

    private async getFromIndexedDB(key: string): Promise<any> {
        const request = indexedDB.open('WorkshopMobileCache', 1);
        
        return new Promise((resolve, reject) => {
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['cache'], 'readonly');
                const store = transaction.objectStore('cache');
                const getRequest = store.get(key);
                
                getRequest.onsuccess = () => {
                    resolve(getRequest.result?.data);
                };
                getRequest.onerror = () => reject(getRequest.error);
            };
        });
    }

    private async persistCacheMetadata(): Promise<void> {
        await this.storeInIndexedDB('cache_metadata', this.cache.metadata);
    }
}

// Export singleton instance
export const offlineMobileSync = new OfflineMobileSync();
