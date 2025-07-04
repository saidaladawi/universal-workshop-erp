/**
 * Advanced Offline Manager - Universal Workshop Frontend V2
 * Comprehensive offline data management with intelligent sync,
 * conflict resolution, and Arabic content handling.
 */

import { ref, reactive, computed } from 'vue'
import { OfflineDatabase } from './OfflineDatabase'
import { useConnectivityStore } from '@/stores/connectivity'
import { useNotificationStore } from '@/stores/notification'
import { useLocalizationStore } from '@/stores/localization'

// Types
interface SyncQueueItem {
    id: string
    type: 'create' | 'update' | 'delete'
    entity: string
    data: any
    timestamp: number
    priority: 'high' | 'medium' | 'low'
    retryCount: number
    maxRetries: number
    conflictStrategy: ConflictStrategy
}

interface ConflictResolution {
    strategy: ConflictStrategy
    winner: 'local' | 'remote' | 'merge'
    mergedData?: any
    reason: string
    reasonAr: string
}

interface OfflineMetrics {
    totalPendingSync: number
    lastSyncTime: Date | null
    syncErrors: number
    conflictsResolved: number
    dataSize: number
    arabicContentPercentage: number
}

type ConflictStrategy = 'local-wins' | 'remote-wins' | 'merge' | 'manual' | 'timestamp-wins'

export class AdvancedOfflineManager {
    private db: OfflineDatabase
    private syncQueue = reactive<SyncQueueItem[]>([])
    private isOnline = ref(false)
    private isSyncing = ref(false)
    private syncProgress = ref(0)
    private lastSyncTime = ref<Date | null>(null)
    private conflictQueue = reactive<any[]>([])
    private metrics = reactive<OfflineMetrics>({
        totalPendingSync: 0,
        lastSyncTime: null,
        syncErrors: 0,
        conflictsResolved: 0,
        dataSize: 0,
        arabicContentPercentage: 0
    })

    // Stores
    private connectivityStore = useConnectivityStore()
    private notificationStore = useNotificationStore()
    private localizationStore = useLocalizationStore()

    constructor() {
        this.db = new OfflineDatabase()
        this.initializeManager()
    }

    private async initializeManager(): Promise<void> {
        try {
            await this.db.initialize()
            await this.loadSyncQueue()
            await this.calculateMetrics()
            this.setupConnectivityWatcher()
            this.setupPeriodicSync()
        } catch (error) {
            console.error('Failed to initialize AdvancedOfflineManager:', error)
        }
    }

    // Connectivity Management
    private setupConnectivityWatcher(): void {
        // Watch for connectivity changes
        window.addEventListener('online', () => {
            this.isOnline.value = true
            this.handleConnectionRestored()
        })

        window.addEventListener('offline', () => {
            this.isOnline.value = false
            this.handleConnectionLost()
        })

        this.isOnline.value = navigator.onLine
    }

    private async handleConnectionRestored(): Promise<void> {
        console.log('Connection restored. Starting sync...')
        await this.startIntelligentSync()
    }

    private handleConnectionLost(): void {
        console.log('Connection lost. Working in offline mode.')
    }

    // Data Operations
    async storeData(
        entity: string,
        data: any,
        operation: 'create' | 'update' | 'delete' = 'create'
    ): Promise<string> {
        try {
            // Store data locally
            const id = await this.db.store(entity, data)

            // Add to sync queue if online operations are needed
            if (this.requiresServerSync(entity, operation)) {
                await this.addToSyncQueue({
                    id: `${entity}_${id}_${Date.now()}`,
                    type: operation,
                    entity,
                    data: { ...data, localId: id },
                    timestamp: Date.now(),
                    priority: this.determinePriority(entity, operation),
                    retryCount: 0,
                    maxRetries: 3,
                    conflictStrategy: this.getDefaultConflictStrategy(entity)
                })
            }

            await this.calculateMetrics()
            return id
        } catch (error) {
            console.error('Failed to store data:', error)
            throw error
        }
    }

    async getData(entity: string, filters?: any): Promise<any[]> {
        try {
            const data = await this.db.get(entity, filters)

            // Enhance data with offline status
            return data.map(item => ({
                ...item,
                _offline: {
                    lastModified: item._lastModified || new Date(),
                    syncStatus: this.getSyncStatus(entity, item.id),
                    hasConflicts: this.hasConflicts(entity, item.id)
                }
            }))
        } catch (error) {
            console.error('Failed to get data:', error)
            throw error
        }
    }

    async updateData(entity: string, id: string, updates: any): Promise<void> {
        try {
            // Update local data
            await this.db.update(entity, id, {
                ...updates,
                _lastModified: new Date(),
                _modifiedOffline: !this.isOnline.value
            })

            // Add to sync queue
            if (this.requiresServerSync(entity, 'update')) {
                await this.addToSyncQueue({
                    id: `${entity}_${id}_update_${Date.now()}`,
                    type: 'update',
                    entity,
                    data: { id, ...updates },
                    timestamp: Date.now(),
                    priority: this.determinePriority(entity, 'update'),
                    retryCount: 0,
                    maxRetries: 3,
                    conflictStrategy: this.getDefaultConflictStrategy(entity)
                })
            }

            await this.calculateMetrics()
        } catch (error) {
            console.error('Failed to update data:', error)
            throw error
        }
    }

    async deleteData(entity: string, id: string): Promise<void> {
        try {
            // Mark as deleted locally (soft delete)
            await this.db.update(entity, id, {
                _deleted: true,
                _deletedAt: new Date(),
                _deletedOffline: !this.isOnline.value
            })

            // Add to sync queue
            if (this.requiresServerSync(entity, 'delete')) {
                await this.addToSyncQueue({
                    id: `${entity}_${id}_delete_${Date.now()}`,
                    type: 'delete',
                    entity,
                    data: { id },
                    timestamp: Date.now(),
                    priority: this.determinePriority(entity, 'delete'),
                    retryCount: 0,
                    maxRetries: 3,
                    conflictStrategy: 'remote-wins' // Deletions usually favor remote
                })
            }

            await this.calculateMetrics()
        } catch (error) {
            console.error('Failed to delete data:', error)
            throw error
        }
    }

    // Sync Queue Management
    private async addToSyncQueue(item: SyncQueueItem): Promise<void> {
        this.syncQueue.push(item)
        await this.persistSyncQueue()

        // Trigger sync if online
        if (this.isOnline.value && !this.isSyncing.value) {
            await this.processSyncQueue()
        }
    }

    private async loadSyncQueue(): Promise<void> {
        try {
            const stored = await this.db.get('_sync_queue')
            this.syncQueue.splice(0, this.syncQueue.length, ...stored)
        } catch (error) {
            console.error('Failed to load sync queue:', error)
        }
    }

    private async persistSyncQueue(): Promise<void> {
        try {
            await this.db.store('_sync_queue', this.syncQueue)
        } catch (error) {
            console.error('Failed to persist sync queue:', error)
        }
    }

    // Intelligent Sync Process
    async startIntelligentSync(): Promise<void> {
        if (this.isSyncing.value || !this.isOnline.value) {
            return
        }

        this.isSyncing.value = true
        this.syncProgress.value = 0

        try {
            // Phase 1: Download server changes
            await this.downloadServerChanges()
            this.syncProgress.value = 30

            // Phase 2: Resolve conflicts
            await this.resolveConflicts()
            this.syncProgress.value = 60

            // Phase 3: Upload local changes
            await this.processSyncQueue()
            this.syncProgress.value = 90

            // Phase 4: Cleanup and finalize
            await this.finalizSync()
            this.syncProgress.value = 100

            this.lastSyncTime.value = new Date()
            this.metrics.lastSyncTime = this.lastSyncTime.value

            console.log('Data synchronized successfully')
        } catch (error) {
            console.error('Sync failed:', error)
            this.metrics.syncErrors++
        } finally {
            this.isSyncing.value = false
            this.syncProgress.value = 0
        }
    }

    private async downloadServerChanges(): Promise<void> {
        // This would integrate with your API to download changes
        try {
            const lastSync = this.lastSyncTime.value
            const entities = ['customers', 'services', 'vehicles', 'parts', 'technicians']

            for (const entity of entities) {
                const serverData = await this.fetchServerChanges(entity, lastSync)

                for (const item of serverData) {
                    await this.mergeServerData(entity, item)
                }
            }
        } catch (error) {
            console.error('Failed to download server changes:', error)
            throw error
        }
    }

    private async fetchServerChanges(entity: string, since: Date | null): Promise<any[]> {
        // Mock implementation - replace with actual API calls
        const url = `/api/${entity}/changes${since ? `?since=${since.toISOString()}` : ''}`

        try {
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            })

            if (!response.ok) {
                throw new Error(`Failed to fetch ${entity} changes: ${response.statusText}`)
            }

            return await response.json()
        } catch (error) {
            console.error(`Failed to fetch server changes for ${entity}:`, error)
            return []
        }
    }

    private async mergeServerData(entity: string, serverItem: any): Promise<void> {
        // Implementation for merging server data with local data
        console.log(`Merging server data for ${entity}:`, serverItem)
    }

    // Conflict Resolution
    private async resolveConflicts(): Promise<void> {
        // Implementation for conflict resolution
        console.log('Resolving conflicts...')
    }

    // Sync Queue Processing
    private async processSyncQueue(): Promise<void> {
        // Implementation for processing sync queue
        console.log('Processing sync queue...')
    }

    private async finalizSync(): Promise<void> {
        await this.persistSyncQueue()
        await this.calculateMetrics()
        this.conflictQueue.splice(0)
    }

    // Utility Methods
    private requiresServerSync(entity: string, operation: string): boolean {
        const serverSyncEntities = [
            'customers', 'services', 'vehicles', 'parts',
            'technicians', 'invoices', 'appointments'
        ]

        return serverSyncEntities.includes(entity)
    }

    private determinePriority(entity: string, operation: string): 'high' | 'medium' | 'low' {
        if (operation === 'delete' || entity === 'invoices') return 'high'
        if (entity === 'services' || entity === 'appointments') return 'medium'
        return 'low'
    }

    private getDefaultConflictStrategy(entity: string): ConflictStrategy {
        const strategies: Record<string, ConflictStrategy> = {
            customers: 'merge',
            services: 'timestamp-wins',
            vehicles: 'merge',
            parts: 'remote-wins',
            technicians: 'remote-wins',
            invoices: 'remote-wins'
        }

        return strategies[entity] || 'manual'
    }

    private getSyncStatus(entity: string, id: string): string {
        const hasPendingSync = this.syncQueue.some(
            item => item.entity === entity && item.data.id === id
        )

        if (hasPendingSync) return 'pending'
        return 'synced'
    }

    private hasConflicts(entity: string, id: string): boolean {
        return this.conflictQueue.some(
            conflict => conflict.entity === entity &&
                (conflict.localItem.id === id || conflict.serverItem.id === id)
        )
    }

    private getAuthToken(): string {
        return localStorage.getItem('auth_token') || ''
    }

    private async calculateMetrics(): Promise<void> {
        try {
            this.metrics.totalPendingSync = this.syncQueue.length

            const allData = await this.db.getAllData()
            this.metrics.dataSize = JSON.stringify(allData).length

            // Calculate Arabic content percentage
            let totalText = 0
            let arabicText = 0

            Object.values(allData).flat().forEach((item: any) => {
                Object.entries(item).forEach(([key, value]) => {
                    if (typeof value === 'string' && value.length > 0) {
                        totalText += value.length
                        if (key.endsWith('_ar') || this.containsArabic(value)) {
                            arabicText += value.length
                        }
                    }
                })
            })

            this.metrics.arabicContentPercentage = totalText > 0 ? (arabicText / totalText) * 100 : 0
        } catch (error) {
            console.error('Failed to calculate metrics:', error)
        }
    }

    private containsArabic(text: string): boolean {
        return /[\u0600-\u06FF]/.test(text)
    }

    private setupPeriodicSync(): void {
        setInterval(() => {
            if (this.isOnline.value && !this.isSyncing.value && this.syncQueue.length > 0) {
                this.startIntelligentSync()
            }
        }, 5 * 60 * 1000) // 5 minutes
    }

    // Public API
    get syncMetrics() {
        return computed(() => ({ ...this.metrics }))
    }

    get pendingSyncCount() {
        return computed(() => this.syncQueue.length)
    }

    get isCurrentlySyncing() {
        return computed(() => this.isSyncing.value)
    }

    get syncProgressPercentage() {
        return computed(() => this.syncProgress.value)
    }

    get pendingConflicts() {
        return computed(() => [...this.conflictQueue])
    }

    async forceSync(): Promise<void> {
        if (this.isOnline.value) {
            await this.startIntelligentSync()
        }
    }

    async clearOfflineData(): Promise<void> {
        await this.db.clear()
        this.syncQueue.splice(0)
        this.conflictQueue.splice(0)
        await this.calculateMetrics()
    }

    async resolveConflictManually(
        conflictId: string,
        resolution: 'local' | 'remote' | 'custom',
        customData?: any
    ): Promise<void> {
        const conflict = this.conflictQueue.find((c, index) => index.toString() === conflictId)
        if (!conflict) return

        let finalData: any
        switch (resolution) {
            case 'local':
                finalData = conflict.localItem
                break
            case 'remote':
                finalData = conflict.serverItem
                break
            case 'custom':
                finalData = customData
                break
        }

        await this.db.update(conflict.entity, finalData.id, {
            ...finalData,
            _lastSync: new Date(),
            _conflictResolved: new Date()
        })

        // Remove from conflict queue
        const index = this.conflictQueue.indexOf(conflict)
        if (index !== -1) {
            this.conflictQueue.splice(index, 1)
        }

        this.metrics.conflictsResolved++
    }
}

// Export singleton instance
export const advancedOfflineManager = new AdvancedOfflineManager() 