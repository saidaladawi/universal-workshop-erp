/**
 * Advanced Offline Data Manager
 * Handles comprehensive offline data synchronization with conflict resolution
 * Supports Arabic data and intelligent sync strategies
 */

import { ref, reactive, computed, watch } from 'vue'
import type { Ref, ComputedRef } from 'vue'

// Types for offline data management
export interface OfflineDataEntry {
    id: string
    type: 'customer' | 'service' | 'inventory' | 'appointment' | 'billing'
    data: Record<string, any>
    timestamp: number
    operation: 'create' | 'update' | 'delete'
    syncStatus: 'pending' | 'syncing' | 'synced' | 'conflict' | 'failed'
    priority: 'high' | 'medium' | 'low'
    retryCount: number
    lastError?: string
    metadata?: {
        userId: string
        deviceId: string
        version: number
        checksum: string
    }
}

export interface SyncConflict {
    id: string
    localData: any
    serverData: any
    timestamp: number
    type: string
    resolution?: 'local' | 'server' | 'merge' | 'manual'
}

export interface SyncStrategy {
    name: string
    priority: number
    conditions: (entry: OfflineDataEntry) => boolean
    handler: (entry: OfflineDataEntry) => Promise<void>
}

export interface OfflineConfig {
    maxStorageSize: number // MB
    syncInterval: number // milliseconds
    retryAttempts: number
    priorityThresholds: {
        high: number // minutes
        medium: number // hours
        low: number // days
    }
    conflictResolution: 'auto' | 'manual' | 'timestamp'
    enableEncryption: boolean
    enableCompression: boolean
}

class AdvancedOfflineDataManager {
    private storage: IDBDatabase | null = null
    private isOnline: Ref<boolean> = ref(navigator.onLine)
    private syncQueue: Ref<OfflineDataEntry[]> = ref([])
    private conflicts: Ref<SyncConflict[]> = ref([])
    private syncStrategies: SyncStrategy[] = []
    private config: OfflineConfig
    private syncInProgress: Ref<boolean> = ref(false)
    private lastSyncTime: Ref<number> = ref(0)
    private storageUsage: Ref<number> = ref(0)

    constructor(config: Partial<OfflineConfig> = {}) {
        this.config = {
            maxStorageSize: 100, // 100MB
            syncInterval: 30000, // 30 seconds
            retryAttempts: 3,
            priorityThresholds: {
                high: 5, // 5 minutes
                medium: 60, // 1 hour
                low: 1440 // 24 hours
            },
            conflictResolution: 'timestamp',
            enableEncryption: true,
            enableCompression: true,
            ...config
        }

        this.initializeStorage()
        this.setupNetworkListeners()
        this.setupSyncStrategies()
        this.startPeriodicSync()
    }

    // Initialize IndexedDB storage
    private async initializeStorage(): Promise<void> {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('UniversalWorkshopOffline', 1)

            request.onerror = () => reject(request.error)
            request.onsuccess = () => {
                this.storage = request.result
                this.loadSyncQueue()
                resolve()
            }

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result

                // Create object stores
                const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id' })
                syncStore.createIndex('timestamp', 'timestamp')
                syncStore.createIndex('priority', 'priority')
                syncStore.createIndex('syncStatus', 'syncStatus')

                const conflictStore = db.createObjectStore('conflicts', { keyPath: 'id' })
                conflictStore.createIndex('timestamp', 'timestamp')

                const metadataStore = db.createObjectStore('metadata', { keyPath: 'key' })
            }
        })
    }

    // Setup network status listeners
    private setupNetworkListeners(): void {
        window.addEventListener('online', () => {
            this.isOnline.value = true
            this.triggerSync()
        })

        window.addEventListener('offline', () => {
            this.isOnline.value = false
        })
    }

    // Setup sync strategies
    private setupSyncStrategies(): void {
        // High priority strategy
        this.syncStrategies.push({
            name: 'high-priority',
            priority: 1,
            conditions: (entry) => entry.priority === 'high',
            handler: async (entry) => {
                await this.syncImmediately(entry)
            }
        })

        // Batch sync strategy
        this.syncStrategies.push({
            name: 'batch-sync',
            priority: 2,
            conditions: (entry) => entry.priority === 'medium',
            handler: async (entry) => {
                await this.batchSync([entry])
            }
        })

        // Background sync strategy
        this.syncStrategies.push({
            name: 'background-sync',
            priority: 3,
            conditions: (entry) => entry.priority === 'low',
            handler: async (entry) => {
                if (this.isOnline.value) {
                    await this.backgroundSync([entry])
                }
            }
        })
    }

    // Start periodic sync
    private startPeriodicSync(): void {
        setInterval(() => {
            if (this.isOnline.value && !this.syncInProgress.value) {
                this.triggerSync()
            }
        }, this.config.syncInterval)
    }

    // Add data to offline queue
    async addToQueue(
        type: OfflineDataEntry['type'],
        data: Record<string, any>,
        operation: OfflineDataEntry['operation'],
        priority: OfflineDataEntry['priority'] = 'medium'
    ): Promise<string> {
        const entry: OfflineDataEntry = {
            id: this.generateId(),
            type,
            data: this.processArabicData(data),
            timestamp: Date.now(),
            operation,
            syncStatus: 'pending',
            priority,
            retryCount: 0,
            metadata: {
                userId: this.getCurrentUserId(),
                deviceId: this.getDeviceId(),
                version: 1,
                checksum: await this.calculateChecksum(data)
            }
        }

        // Add to memory queue
        this.syncQueue.value.push(entry)

        // Persist to IndexedDB
        await this.persistEntry(entry)

        // Update storage usage
        await this.updateStorageUsage()

        // Trigger immediate sync for high priority items
        if (priority === 'high' && this.isOnline.value) {
            this.syncImmediately(entry)
        }

        return entry.id
    }

    // Process Arabic data for storage
    private processArabicData(data: Record<string, any>): Record<string, any> {
        const processed = { ...data }

        // Handle Arabic text fields
        Object.keys(processed).forEach(key => {
            if (typeof processed[key] === 'string' && this.isArabicText(processed[key])) {
                processed[key] = {
                    text: processed[key],
                    direction: 'rtl',
                    language: 'ar',
                    normalized: this.normalizeArabicText(processed[key])
                }
            }
        })

        return processed
    }

    // Check if text contains Arabic characters
    private isArabicText(text: string): boolean {
        return /[\u0600-\u06FF]/.test(text)
    }

    // Normalize Arabic text for search
    private normalizeArabicText(text: string): string {
        return text
            .replace(/[آأإ]/g, 'ا')
            .replace(/ة/g, 'ه')
            .replace(/ي/g, 'ى')
            .replace(/[\u064B-\u0652]/g, '') // Remove diacritics
    }

    // Trigger sync process
    async triggerSync(): Promise<void> {
        if (this.syncInProgress.value || !this.isOnline.value) {
            return
        }

        this.syncInProgress.value = true

        try {
            // Sort queue by priority and timestamp
            const sortedQueue = [...this.syncQueue.value]
                .filter(entry => entry.syncStatus === 'pending' || entry.syncStatus === 'failed')
                .sort((a, b) => {
                    const priorityOrder = { high: 0, medium: 1, low: 2 }
                    const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority]
                    return priorityDiff !== 0 ? priorityDiff : a.timestamp - b.timestamp
                })

            // Process entries with appropriate strategies
            for (const entry of sortedQueue) {
                const strategy = this.syncStrategies.find(s => s.conditions(entry))
                if (strategy) {
                    try {
                        await strategy.handler(entry)
                        entry.syncStatus = 'synced'
                        entry.retryCount = 0
                        await this.updateEntry(entry)
                    } catch (error) {
                        await this.handleSyncError(entry, error as Error)
                    }
                }
            }

            this.lastSyncTime.value = Date.now()
        } finally {
            this.syncInProgress.value = false
        }
    }

    // Immediate sync for high priority items
    private async syncImmediately(entry: OfflineDataEntry): Promise<void> {
        entry.syncStatus = 'syncing'
        await this.updateEntry(entry)

        try {
            const response = await this.sendToServer(entry)

            if (response.conflict) {
                await this.handleConflict(entry, response.serverData)
            } else {
                entry.syncStatus = 'synced'
                await this.removeFromQueue(entry.id)
            }
        } catch (error) {
            await this.handleSyncError(entry, error as Error)
        }
    }

    // Batch sync for medium priority items
    private async batchSync(entries: OfflineDataEntry[]): Promise<void> {
        const batchSize = 10
        const batches = this.chunkArray(entries, batchSize)

        for (const batch of batches) {
            try {
                const response = await this.sendBatchToServer(batch)

                for (let i = 0; i < batch.length; i++) {
                    const entry = batch[i]
                    const result = response.results[i]

                    if (result.conflict) {
                        await this.handleConflict(entry, result.serverData)
                    } else if (result.success) {
                        entry.syncStatus = 'synced'
                        await this.removeFromQueue(entry.id)
                    } else {
                        await this.handleSyncError(entry, new Error(result.error))
                    }
                }
            } catch (error) {
                for (const entry of batch) {
                    await this.handleSyncError(entry, error as Error)
                }
            }
        }
    }

    // Background sync for low priority items
    private async backgroundSync(entries: OfflineDataEntry[]): Promise<void> {
        // Use requestIdleCallback for non-blocking sync
        if ('requestIdleCallback' in window) {
            (window as any).requestIdleCallback(async () => {
                await this.batchSync(entries)
            })
        } else {
            setTimeout(async () => {
                await this.batchSync(entries)
            }, 100)
        }
    }

    // Handle sync conflicts
    private async handleConflict(localEntry: OfflineDataEntry, serverData: any): Promise<void> {
        const conflict: SyncConflict = {
            id: this.generateId(),
            localData: localEntry.data,
            serverData,
            timestamp: Date.now(),
            type: localEntry.type
        }

        // Auto-resolve based on configuration
        if (this.config.conflictResolution === 'timestamp') {
            conflict.resolution = localEntry.timestamp > serverData.timestamp ? 'local' : 'server'
        } else if (this.config.conflictResolution === 'auto') {
            conflict.resolution = await this.autoResolveConflict(conflict)
        } else {
            // Manual resolution required
            this.conflicts.value.push(conflict)
            localEntry.syncStatus = 'conflict'
            await this.updateEntry(localEntry)
            return
        }

        // Apply resolution
        await this.applyConflictResolution(localEntry, conflict)
    }

    // Auto-resolve conflicts using intelligent strategies
    private async autoResolveConflict(conflict: SyncConflict): Promise<'local' | 'server' | 'merge'> {
        // Simple strategy: prefer server for critical data, local for user preferences
        const criticalTypes = ['billing', 'inventory']

        if (criticalTypes.includes(conflict.type)) {
            return 'server'
        }

        // For customer data, try to merge
        if (conflict.type === 'customer') {
            return 'merge'
        }

        return 'local'
    }

    // Apply conflict resolution
    private async applyConflictResolution(entry: OfflineDataEntry, conflict: SyncConflict): Promise<void> {
        let resolvedData: any

        switch (conflict.resolution) {
            case 'local':
                resolvedData = conflict.localData
                break
            case 'server':
                resolvedData = conflict.serverData
                break
            case 'merge':
                resolvedData = await this.mergeData(conflict.localData, conflict.serverData)
                break
            default:
                return // Manual resolution pending
        }

        // Update entry with resolved data
        entry.data = resolvedData
        entry.syncStatus = 'pending'
        entry.retryCount = 0
        await this.updateEntry(entry)

        // Retry sync
        await this.syncImmediately(entry)
    }

    // Intelligent data merging
    private async mergeData(localData: any, serverData: any): Promise<any> {
        const merged = { ...serverData }

        // Merge strategy for different data types
        Object.keys(localData).forEach(key => {
            if (key.endsWith('_ar') || key.includes('arabic')) {
                // Prefer local Arabic data
                merged[key] = localData[key]
            } else if (key.includes('preference') || key.includes('setting')) {
                // Prefer local preferences
                merged[key] = localData[key]
            } else if (Array.isArray(localData[key]) && Array.isArray(serverData[key])) {
                // Merge arrays
                merged[key] = [...new Set([...serverData[key], ...localData[key]])]
            }
        })

        return merged
    }

    // Handle sync errors
    private async handleSyncError(entry: OfflineDataEntry, error: Error): Promise<void> {
        entry.retryCount++
        entry.lastError = error.message
        entry.syncStatus = entry.retryCount >= this.config.retryAttempts ? 'failed' : 'pending'

        await this.updateEntry(entry)

        // Log error for debugging
        console.error(`Sync error for entry ${entry.id}:`, error)
    }

    // Send single entry to server
    private async sendToServer(entry: OfflineDataEntry): Promise<any> {
        const response = await fetch('/api/sync/single', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify(entry)
        })

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`)
        }

        return await response.json()
    }

    // Send batch to server
    private async sendBatchToServer(entries: OfflineDataEntry[]): Promise<any> {
        const response = await fetch('/api/sync/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({ entries })
        })

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`)
        }

        return await response.json()
    }

    // Utility methods
    private generateId(): string {
        return `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private getCurrentUserId(): string {
        // Get from auth context
        return 'current_user_id'
    }

    private getDeviceId(): string {
        let deviceId = localStorage.getItem('deviceId')
        if (!deviceId) {
            deviceId = this.generateId()
            localStorage.setItem('deviceId', deviceId)
        }
        return deviceId
    }

    private getAuthToken(): string {
        return localStorage.getItem('authToken') || ''
    }

    private async calculateChecksum(data: any): Promise<string> {
        const text = JSON.stringify(data)
        const encoder = new TextEncoder()
        const dataBuffer = encoder.encode(text)
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    }

    private chunkArray<T>(array: T[], size: number): T[][] {
        const chunks: T[][] = []
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size))
        }
        return chunks
    }

    // IndexedDB operations
    private async persistEntry(entry: OfflineDataEntry): Promise<void> {
        if (!this.storage) return

        const transaction = this.storage.transaction(['syncQueue'], 'readwrite')
        const store = transaction.objectStore('syncQueue')
        await store.put(entry)
    }

    private async updateEntry(entry: OfflineDataEntry): Promise<void> {
        await this.persistEntry(entry)

        // Update in memory
        const index = this.syncQueue.value.findIndex(e => e.id === entry.id)
        if (index !== -1) {
            this.syncQueue.value[index] = entry
        }
    }

    private async removeFromQueue(entryId: string): Promise<void> {
        if (!this.storage) return

        const transaction = this.storage.transaction(['syncQueue'], 'readwrite')
        const store = transaction.objectStore('syncQueue')
        await store.delete(entryId)

        // Remove from memory
        const index = this.syncQueue.value.findIndex(e => e.id === entryId)
        if (index !== -1) {
            this.syncQueue.value.splice(index, 1)
        }
    }

    private async loadSyncQueue(): Promise<void> {
        if (!this.storage) return

        const transaction = this.storage.transaction(['syncQueue'], 'readonly')
        const store = transaction.objectStore('syncQueue')
        const request = store.getAll()

        request.onsuccess = () => {
            this.syncQueue.value = request.result || []
        }
    }

    private async updateStorageUsage(): Promise<void> {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate()
            this.storageUsage.value = (estimate.usage || 0) / (1024 * 1024) // MB
        }
    }

    // Public API
    get isOnlineStatus(): ComputedRef<boolean> {
        return computed(() => this.isOnline.value)
    }

    get pendingCount(): ComputedRef<number> {
        return computed(() =>
            this.syncQueue.value.filter(e => e.syncStatus === 'pending').length
        )
    }

    get conflictCount(): ComputedRef<number> {
        return computed(() => this.conflicts.value.length)
    }

    get isSyncing(): ComputedRef<boolean> {
        return computed(() => this.syncInProgress.value)
    }

    get lastSync(): ComputedRef<Date | null> {
        return computed(() =>
            this.lastSyncTime.value ? new Date(this.lastSyncTime.value) : null
        )
    }

    get storageUsagePercent(): ComputedRef<number> {
        return computed(() =>
            (this.storageUsage.value / this.config.maxStorageSize) * 100
        )
    }

    // Manual conflict resolution
    async resolveConflict(conflictId: string, resolution: 'local' | 'server' | 'merge'): Promise<void> {
        const conflict = this.conflicts.value.find(c => c.id === conflictId)
        if (!conflict) return

        conflict.resolution = resolution

        // Find the corresponding entry
        const entry = this.syncQueue.value.find(e =>
            e.data === conflict.localData && e.type === conflict.type
        )

        if (entry) {
            await this.applyConflictResolution(entry, conflict)
        }

        // Remove from conflicts
        const index = this.conflicts.value.findIndex(c => c.id === conflictId)
        if (index !== -1) {
            this.conflicts.value.splice(index, 1)
        }
    }

    // Clear all synced entries
    async clearSyncedEntries(): Promise<void> {
        const syncedEntries = this.syncQueue.value.filter(e => e.syncStatus === 'synced')

        for (const entry of syncedEntries) {
            await this.removeFromQueue(entry.id)
        }
    }

    // Force sync specific entry
    async forceSyncEntry(entryId: string): Promise<void> {
        const entry = this.syncQueue.value.find(e => e.id === entryId)
        if (entry && this.isOnline.value) {
            entry.retryCount = 0
            entry.syncStatus = 'pending'
            await this.syncImmediately(entry)
        }
    }

    // Get sync statistics
    getSyncStatistics() {
        const stats = {
            total: this.syncQueue.value.length,
            pending: this.syncQueue.value.filter(e => e.syncStatus === 'pending').length,
            syncing: this.syncQueue.value.filter(e => e.syncStatus === 'syncing').length,
            synced: this.syncQueue.value.filter(e => e.syncStatus === 'synced').length,
            conflicts: this.syncQueue.value.filter(e => e.syncStatus === 'conflict').length,
            failed: this.syncQueue.value.filter(e => e.syncStatus === 'failed').length,
            storageUsage: this.storageUsage.value,
            lastSync: this.lastSync.value
        }

        return stats
    }
}

// Composable for using offline data manager
export function useOfflineDataManager(config?: Partial<OfflineConfig>) {
    const manager = new AdvancedOfflineDataManager(config)

    return {
        // Manager instance
        manager,

        // Reactive states
        isOnline: manager.isOnlineStatus,
        pendingCount: manager.pendingCount,
        conflictCount: manager.conflictCount,
        isSyncing: manager.isSyncing,
        lastSync: manager.lastSync,
        storageUsage: manager.storageUsagePercent,

        // Methods
        addToQueue: manager.addToQueue.bind(manager),
        triggerSync: manager.triggerSync.bind(manager),
        resolveConflict: manager.resolveConflict.bind(manager),
        clearSyncedEntries: manager.clearSyncedEntries.bind(manager),
        forceSyncEntry: manager.forceSyncEntry.bind(manager),
        getSyncStatistics: manager.getSyncStatistics.bind(manager)
    }
}

export default AdvancedOfflineDataManager 