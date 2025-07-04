/**
 * Sync Manager - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Synchronization
 *
 * Comprehensive data synchronization manager with offline capability,
 * conflict resolution, and Arabic-aware data handling for Omani workshops.
 */

import { ref, reactive, computed, watch } from 'vue'
import { useEnhancedEventBus } from '../events'

// Sync operation types
export type SyncOperationType = 'create' | 'update' | 'delete' | 'read'

// Sync strategy types
export type SyncStrategy = 'immediate' | 'batched' | 'scheduled' | 'manual'

// Sync status
export type SyncStatus = 'idle' | 'syncing' | 'conflict' | 'error' | 'offline'

// Data entity types for synchronization
export type EntityType =
    | 'service_order'
    | 'customer'
    | 'vehicle'
    | 'technician'
    | 'part'
    | 'inventory_item'
    | 'invoice'
    | 'payment'
    | 'quality_check'
    | 'user_preference'

// Sync configuration
export interface SyncConfig {
    strategy: SyncStrategy
    batchSize: number
    syncInterval: number // milliseconds
    maxRetries: number
    retryDelay: number
    conflictResolution: 'client_wins' | 'server_wins' | 'manual' | 'merge'
    enableOptimisticUpdates: boolean
    enableCompression: boolean
    enableEncryption: boolean
    syncPriority: 'high' | 'medium' | 'low'
}

// Sync operation interface
export interface SyncOperation {
    id: string
    type: SyncOperationType
    entityType: EntityType
    entityId: string
    data: any
    metadata: {
        timestamp: Date
        userId: string
        deviceId: string
        version: number
        checksum: string
        isArabicContent: boolean
        culturalContext?: string
    }
    status: 'pending' | 'syncing' | 'completed' | 'failed' | 'conflict'
    retryCount: number
    lastAttempt?: Date
    error?: string
    priority: 'high' | 'medium' | 'low'
}

// Sync state interface
export interface SyncState {
    isOnline: boolean
    isSyncing: boolean
    lastSyncTime?: Date
    pendingOperations: number
    conflictCount: number
    errorCount: number
    syncProgress: number // 0-100
    estimatedSyncTime?: number
    bandwidthEstimate?: number
}

// Sync conflict interface
export interface SyncConflict {
    id: string
    entityType: EntityType
    entityId: string
    localData: any
    serverData: any
    timestamp: Date
    conflictType: 'update_conflict' | 'delete_conflict' | 'version_conflict'
    isArabicContent: boolean
    culturalContext?: string
    resolutionOptions: ConflictResolutionOption[]
}

// Conflict resolution option
export interface ConflictResolutionOption {
    id: string
    label: string
    labelAr: string
    description: string
    descriptionAr: string
    action: 'use_local' | 'use_server' | 'merge' | 'manual'
    impact: 'low' | 'medium' | 'high'
}

// Sync metrics
export interface SyncMetrics {
    totalOperations: number
    successfulOperations: number
    failedOperations: number
    conflictOperations: number
    averageSyncTime: number
    dataTransferred: number // bytes
    lastSyncDuration: number
    syncEfficiency: number // percentage
    networkLatency: number
    serverResponseTime: number
}

/**
 * Main Sync Manager Class
 * Handles all data synchronization between client and server
 */
export class SyncManager {
    private config: SyncConfig
    private operationQueue: Map<string, SyncOperation> = new Map()
    private conflictQueue: Map<string, SyncConflict> = new Map()
    private syncState = reactive<SyncState>({
        isOnline: navigator.onLine,
        isSyncing: false,
        pendingOperations: 0,
        conflictCount: 0,
        errorCount: 0,
        syncProgress: 0
    })
    private metrics = reactive<SyncMetrics>({
        totalOperations: 0,
        successfulOperations: 0,
        failedOperations: 0,
        conflictOperations: 0,
        averageSyncTime: 0,
        dataTransferred: 0,
        lastSyncDuration: 0,
        syncEfficiency: 100,
        networkLatency: 0,
        serverResponseTime: 0
    })

    private syncInterval?: number
    private eventBus = useEnhancedEventBus()
    private isInitialized = false

    constructor(config: Partial<SyncConfig> = {}) {
        this.config = {
            strategy: 'batched',
            batchSize: 50,
            syncInterval: 30000, // 30 seconds
            maxRetries: 3,
            retryDelay: 5000,
            conflictResolution: 'manual',
            enableOptimisticUpdates: true,
            enableCompression: false,
            enableEncryption: false,
            syncPriority: 'medium',
            ...config
        }

        this.initialize()
    }

    /**
     * Initialize the sync manager
     */
    private async initialize(): Promise<void> {
        try {
            // Setup network status monitoring
            this.setupNetworkMonitoring()

            // Setup event listeners
            this.setupEventListeners()

            // Start sync scheduler if configured
            if (this.config.strategy === 'scheduled') {
                this.startSyncScheduler()
            }

            // Load pending operations from storage
            await this.loadPendingOperations()

            // Initial sync if online
            if (this.syncState.isOnline) {
                await this.performInitialSync()
            }

            this.isInitialized = true
            console.log('🔄 Sync Manager initialized')

        } catch (error) {
            console.error('❌ Failed to initialize Sync Manager:', error)
            throw error
        }
    }

    /**
     * Queue a sync operation
     */
    async queueOperation(
        type: SyncOperationType,
        entityType: EntityType,
        entityId: string,
        data: any,
        options: {
            priority?: 'high' | 'medium' | 'low'
            immediate?: boolean
            optimistic?: boolean
        } = {}
    ): Promise<string> {
        const operationId = this.generateOperationId()

        const operation: SyncOperation = {
            id: operationId,
            type,
            entityType,
            entityId,
            data: this.processArabicContent(data),
            metadata: {
                timestamp: new Date(),
                userId: this.getCurrentUserId(),
                deviceId: this.getDeviceId(),
                version: await this.getEntityVersion(entityType, entityId),
                checksum: this.calculateChecksum(data),
                isArabicContent: this.containsArabicContent(data),
                culturalContext: this.extractCulturalContext(data)
            },
            status: 'pending',
            retryCount: 0,
            priority: options.priority || 'medium'
        }

        // Add to queue
        this.operationQueue.set(operationId, operation)
        this.syncState.pendingOperations = this.operationQueue.size

        // Emit event
        await this.eventBus.emit('sync_operation_queued', {
            operationId,
            entityType,
            type,
            priority: operation.priority
        })

        // Handle optimistic updates
        if (options.optimistic && this.config.enableOptimisticUpdates) {
            await this.applyOptimisticUpdate(operation)
        }

        // Immediate sync if requested and online
        if (options.immediate && this.syncState.isOnline) {
            await this.syncOperation(operation)
        } else if (this.config.strategy === 'immediate' && this.syncState.isOnline) {
            await this.syncOperation(operation)
        }

        console.log(`📤 Sync operation queued: ${type} ${entityType} (${operationId})`)
        return operationId
    }

    /**
     * Sync all pending operations
     */
    async syncAll(): Promise<{ success: number; failed: number; conflicts: number }> {
        if (!this.syncState.isOnline) {
            console.warn('⚠️ Cannot sync while offline')
            return { success: 0, failed: 0, conflicts: 0 }
        }

        if (this.syncState.isSyncing) {
            console.warn('⚠️ Sync already in progress')
            return { success: 0, failed: 0, conflicts: 0 }
        }

        this.syncState.isSyncing = true
        this.syncState.syncProgress = 0

        const startTime = performance.now()
        let successCount = 0
        let failedCount = 0
        let conflictCount = 0

        try {
            const operations = Array.from(this.operationQueue.values())
                .filter(op => op.status === 'pending')
                .sort(this.prioritizeOperations.bind(this))

            console.log(`🔄 Starting sync of ${operations.length} operations`)

            // Process operations in batches
            const batches = this.createBatches(operations, this.config.batchSize)

            for (let i = 0; i < batches.length; i++) {
                const batch = batches[i]
                const batchResults = await this.syncBatch(batch)

                successCount += batchResults.success
                failedCount += batchResults.failed
                conflictCount += batchResults.conflicts

                // Update progress
                this.syncState.syncProgress = Math.round(((i + 1) / batches.length) * 100)

                // Brief pause between batches to prevent overwhelming the server
                if (i < batches.length - 1) {
                    await this.sleep(500)
                }
            }

            // Update metrics
            const syncDuration = performance.now() - startTime
            this.updateSyncMetrics(successCount, failedCount, conflictCount, syncDuration)

            // Emit completion event
            await this.eventBus.emit('sync_completed', {
                totalOperations: operations.length,
                successCount,
                failedCount,
                conflictCount,
                duration: syncDuration
            })

            console.log(`✅ Sync completed: ${successCount} success, ${failedCount} failed, ${conflictCount} conflicts`)

        } catch (error) {
            console.error('❌ Sync failed:', error)
            this.syncState.errorCount++

            await this.eventBus.emit('sync_failed', {
                error: error instanceof Error ? error.message : 'Unknown error',
                operationsRemaining: this.operationQueue.size
            })

        } finally {
            this.syncState.isSyncing = false
            this.syncState.syncProgress = 100
            this.syncState.lastSyncTime = new Date()
        }

        return { success: successCount, failed: failedCount, conflicts: conflictCount }
    }

    /**
     * Sync a batch of operations
     */
    private async syncBatch(operations: SyncOperation[]): Promise<{ success: number; failed: number; conflicts: number }> {
        let successCount = 0
        let failedCount = 0
        let conflictCount = 0

        const batchPromises = operations.map(async (operation) => {
            try {
                const result = await this.syncOperation(operation)

                if (result === 'success') {
                    successCount++
                } else if (result === 'conflict') {
                    conflictCount++
                } else {
                    failedCount++
                }
            } catch (error) {
                failedCount++
                console.error(`❌ Operation ${operation.id} failed:`, error)
            }
        })

        await Promise.allSettled(batchPromises)
        return { success: successCount, failed: failedCount, conflicts: conflictCount }
    }

    /**
     * Sync a single operation
     */
    private async syncOperation(operation: SyncOperation): Promise<'success' | 'failed' | 'conflict'> {
        operation.status = 'syncing'
        operation.lastAttempt = new Date()

        try {
            const apiEndpoint = this.getApiEndpoint(operation.entityType, operation.type)
            const requestData = this.prepareRequestData(operation)

            // Make API request
            const response = await fetch(apiEndpoint, {
                method: this.getHttpMethod(operation.type),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Workshop-Sync': 'true',
                    'X-Workshop-Version': operation.metadata.version.toString(),
                    'X-Workshop-Checksum': operation.metadata.checksum,
                    ...(operation.metadata.isArabicContent && {
                        'X-Workshop-Language': 'ar',
                        'X-Workshop-Culture': operation.metadata.culturalContext || 'omani'
                    })
                },
                body: JSON.stringify(requestData)
            })

            if (response.status === 409) {
                // Conflict detected
                const conflictData = await response.json()
                await this.handleConflict(operation, conflictData)
                return 'conflict'
            }

            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`)
            }

            const result = await response.json()

            // Update operation status
            operation.status = 'completed'
            this.operationQueue.delete(operation.id)
            this.syncState.pendingOperations = this.operationQueue.size

            // Update local data with server response
            await this.updateLocalData(operation.entityType, operation.entityId, result.data)

            // Emit success event
            await this.eventBus.emit('sync_operation_completed', {
                operationId: operation.id,
                entityType: operation.entityType,
                entityId: operation.entityId
            })

            this.metrics.successfulOperations++
            return 'success'

        } catch (error) {
            operation.retryCount++
            operation.error = error instanceof Error ? error.message : 'Unknown error'

            if (operation.retryCount >= this.config.maxRetries) {
                operation.status = 'failed'
                this.syncState.errorCount++

                await this.eventBus.emit('sync_operation_failed', {
                    operationId: operation.id,
                    entityType: operation.entityType,
                    entityId: operation.entityId,
                    error: operation.error,
                    retryCount: operation.retryCount
                })

                this.metrics.failedOperations++
                return 'failed'
            } else {
                // Schedule retry
                operation.status = 'pending'
                setTimeout(() => {
                    this.syncOperation(operation)
                }, this.config.retryDelay * Math.pow(2, operation.retryCount - 1))

                return 'failed'
            }
        }
    }

    /**
     * Handle sync conflicts
     */
    private async handleConflict(operation: SyncOperation, conflictData: any): Promise<void> {
        const conflict: SyncConflict = {
            id: this.generateConflictId(),
            entityType: operation.entityType,
            entityId: operation.entityId,
            localData: operation.data,
            serverData: conflictData.serverData,
            timestamp: new Date(),
            conflictType: conflictData.conflictType || 'update_conflict',
            isArabicContent: operation.metadata.isArabicContent,
            culturalContext: operation.metadata.culturalContext,
            resolutionOptions: this.generateResolutionOptions(operation, conflictData)
        }

        this.conflictQueue.set(conflict.id, conflict)
        this.syncState.conflictCount = this.conflictQueue.size
        this.metrics.conflictOperations++

        // Emit conflict event
        await this.eventBus.emit('sync_conflict_detected', {
            conflictId: conflict.id,
            entityType: conflict.entityType,
            entityId: conflict.entityId,
            isArabicContent: conflict.isArabicContent
        })

        // Auto-resolve if configured
        if (this.config.conflictResolution !== 'manual') {
            await this.autoResolveConflict(conflict)
        }

        console.log(`⚠️ Sync conflict detected: ${conflict.entityType} ${conflict.entityId}`)
    }

    /**
     * Resolve a sync conflict
     */
    async resolveConflict(
        conflictId: string,
        resolution: 'use_local' | 'use_server' | 'merge' | 'manual',
        mergedData?: any
    ): Promise<boolean> {
        const conflict = this.conflictQueue.get(conflictId)
        if (!conflict) {
            console.error(`❌ Conflict not found: ${conflictId}`)
            return false
        }

        try {
            let resolvedData: any

            switch (resolution) {
                case 'use_local':
                    resolvedData = conflict.localData
                    break
                case 'use_server':
                    resolvedData = conflict.serverData
                    break
                case 'merge':
                    resolvedData = this.mergeConflictData(conflict.localData, conflict.serverData)
                    break
                case 'manual':
                    if (!mergedData) {
                        throw new Error('Manual resolution requires merged data')
                    }
                    resolvedData = mergedData
                    break
            }

            // Apply resolution
            await this.updateLocalData(conflict.entityType, conflict.entityId, resolvedData)

            // Create new sync operation for the resolved data
            await this.queueOperation('update', conflict.entityType, conflict.entityId, resolvedData, {
                priority: 'high',
                immediate: true
            })

            // Remove from conflict queue
            this.conflictQueue.delete(conflictId)
            this.syncState.conflictCount = this.conflictQueue.size

            // Emit resolution event
            await this.eventBus.emit('sync_conflict_resolved', {
                conflictId,
                resolution,
                entityType: conflict.entityType,
                entityId: conflict.entityId
            })

            console.log(`✅ Conflict resolved: ${conflictId} using ${resolution}`)
            return true

        } catch (error) {
            console.error(`❌ Failed to resolve conflict ${conflictId}:`, error)
            return false
        }
    }

    /**
     * Get all pending conflicts
     */
    getConflicts(): SyncConflict[] {
        return Array.from(this.conflictQueue.values())
    }

    /**
     * Get sync state
     */
    getSyncState(): SyncState {
        return { ...this.syncState }
    }

    /**
     * Get sync metrics
     */
    getSyncMetrics(): SyncMetrics {
        return { ...this.metrics }
    }

    /**
     * Get pending operations count
     */
    getPendingOperationsCount(): number {
        return this.operationQueue.size
    }

    /**
     * Clear all pending operations (use with caution)
     */
    clearPendingOperations(): void {
        this.operationQueue.clear()
        this.syncState.pendingOperations = 0
        console.log('🗑️ All pending operations cleared')
    }

    /**
     * Pause sync operations
     */
    pauseSync(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval)
            this.syncInterval = undefined
        }
        console.log('⏸️ Sync paused')
    }

    /**
     * Resume sync operations
     */
    resumeSync(): void {
        if (this.config.strategy === 'scheduled') {
            this.startSyncScheduler()
        }
        console.log('▶️ Sync resumed')
    }

    // Private helper methods
    private setupNetworkMonitoring(): void {
        window.addEventListener('online', () => {
            this.syncState.isOnline = true
            console.log('🌐 Network connection restored')

            // Auto-sync when coming back online
            if (this.operationQueue.size > 0) {
                this.syncAll()
            }
        })

        window.addEventListener('offline', () => {
            this.syncState.isOnline = false
            console.log('📱 Network connection lost - entering offline mode')
        })
    }

    private setupEventListeners(): void {
        // Listen for data changes to trigger sync
        this.eventBus.subscribe(['service_order_updated', 'customer_arrived'], async (event) => {
            if (event.data.syncRequired !== false) {
                await this.queueOperation('update', 'service_order', event.entityId, event.data)
            }
        })
    }

    private startSyncScheduler(): void {
        this.syncInterval = window.setInterval(() => {
            if (this.syncState.isOnline && !this.syncState.isSyncing && this.operationQueue.size > 0) {
                this.syncAll()
            }
        }, this.config.syncInterval)
    }

    private async loadPendingOperations(): Promise<void> {
        // In a real implementation, this would load from IndexedDB or localStorage
        // For now, we'll simulate it
        console.log('📂 Loading pending operations from storage...')
    }

    private async performInitialSync(): Promise<void> {
        console.log('🔄 Performing initial sync...')
        // Implementation would fetch latest data from server
    }

    private processArabicContent(data: any): any {
        // Process Arabic content for proper encoding and cultural context
        if (typeof data === 'object' && data !== null) {
            const processed = { ...data }

            // Add cultural context markers for Arabic content
            if (this.containsArabicContent(data)) {
                processed._culturalContext = 'omani'
                processed._textDirection = 'rtl'
                processed._locale = 'ar-OM'
            }

            return processed
        }
        return data
    }

    private containsArabicContent(data: any): boolean {
        if (typeof data === 'string') {
            return /[\u0600-\u06FF]/.test(data)
        }

        if (typeof data === 'object' && data !== null) {
            return Object.values(data).some(value => this.containsArabicContent(value))
        }

        return false
    }

    private extractCulturalContext(data: any): string | undefined {
        // Extract cultural context from data for proper handling
        if (data.culturalContext) return data.culturalContext
        if (data.locale?.startsWith('ar')) return 'arabic'
        if (data.country === 'OM' || data.country === 'Oman') return 'omani'
        return undefined
    }

    private calculateChecksum(data: any): string {
        // Simple checksum calculation for data integrity
        const str = JSON.stringify(data)
        let hash = 0
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i)
            hash = ((hash << 5) - hash) + char
            hash = hash & hash // Convert to 32-bit integer
        }
        return hash.toString(16)
    }

    private async getEntityVersion(entityType: EntityType, entityId: string): Promise<number> {
        // Get current version of entity from local storage
        // In a real implementation, this would query the local database
        return 1 // Simplified
    }

    private async applyOptimisticUpdate(operation: SyncOperation): Promise<void> {
        // Apply update immediately to local data for responsive UI
        console.log(`⚡ Applying optimistic update: ${operation.entityType} ${operation.entityId}`)

        // Implementation would update local data store immediately
        await this.updateLocalData(operation.entityType, operation.entityId, operation.data)
    }

    private prioritizeOperations(a: SyncOperation, b: SyncOperation): number {
        const priorityOrder = { high: 0, medium: 1, low: 2 }
        return priorityOrder[a.priority] - priorityOrder[b.priority]
    }

    private createBatches<T>(items: T[], batchSize: number): T[][] {
        const batches: T[][] = []
        for (let i = 0; i < items.length; i += batchSize) {
            batches.push(items.slice(i, i + batchSize))
        }
        return batches
    }

    private updateSyncMetrics(
        successCount: number,
        failedCount: number,
        conflictCount: number,
        duration: number
    ): void {
        this.metrics.totalOperations += successCount + failedCount + conflictCount
        this.metrics.lastSyncDuration = duration
        this.metrics.syncEfficiency = this.metrics.totalOperations > 0 ?
            (this.metrics.successfulOperations / this.metrics.totalOperations) * 100 : 100
    }

    private getApiEndpoint(entityType: EntityType, operation: SyncOperationType): string {
        const baseUrl = '/api/workshop/sync'
        return `${baseUrl}/${entityType}/${operation}`
    }

    private getHttpMethod(operation: SyncOperationType): string {
        const methods = {
            create: 'POST',
            update: 'PUT',
            delete: 'DELETE',
            read: 'GET'
        }
        return methods[operation]
    }

    private prepareRequestData(operation: SyncOperation): any {
        return {
            id: operation.entityId,
            data: operation.data,
            metadata: operation.metadata
        }
    }

    private generateResolutionOptions(operation: SyncOperation, conflictData: any): ConflictResolutionOption[] {
        return [
            {
                id: 'use_local',
                label: 'Use Local Changes',
                labelAr: 'استخدم التغييرات المحلية',
                description: 'Keep your local changes and overwrite server data',
                descriptionAr: 'احتفظ بتغييراتك المحلية واستبدل بيانات الخادم',
                action: 'use_local',
                impact: 'medium'
            },
            {
                id: 'use_server',
                label: 'Use Server Changes',
                labelAr: 'استخدم تغييرات الخادم',
                description: 'Accept server changes and discard local modifications',
                descriptionAr: 'اقبل تغييرات الخادم واتجاهل التعديلات المحلية',
                action: 'use_server',
                impact: 'medium'
            },
            {
                id: 'merge',
                label: 'Merge Changes',
                labelAr: 'دمج التغييرات',
                description: 'Automatically merge compatible changes',
                descriptionAr: 'دمج التغييرات المتوافقة تلقائياً',
                action: 'merge',
                impact: 'low'
            }
        ]
    }

    private async autoResolveConflict(conflict: SyncConflict): Promise<void> {
        let resolution: 'use_local' | 'use_server' | 'merge'

        switch (this.config.conflictResolution) {
            case 'client_wins':
                resolution = 'use_local'
                break
            case 'server_wins':
                resolution = 'use_server'
                break
            case 'merge':
                resolution = 'merge'
                break
            default:
                return // Manual resolution required
        }

        await this.resolveConflict(conflict.id, resolution)
    }

    private mergeConflictData(localData: any, serverData: any): any {
        // Simple merge strategy - in a real implementation, this would be more sophisticated
        return {
            ...serverData,
            ...localData,
            _mergedAt: new Date().toISOString(),
            _mergeStrategy: 'automatic'
        }
    }

    private async updateLocalData(entityType: EntityType, entityId: string, data: any): Promise<void> {
        // Update local data store
        console.log(`💾 Updating local data: ${entityType} ${entityId}`)

        // In a real implementation, this would update IndexedDB or another local store
    }

    private getCurrentUserId(): string {
        // Get current user ID from authentication context
        return 'user_' + Math.random().toString(36).substr(2, 9)
    }

    private getDeviceId(): string {
        // Get unique device identifier
        return 'device_' + Math.random().toString(36).substr(2, 9)
    }

    private generateOperationId(): string {
        return `sync_op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private generateConflictId(): string {
        return `conflict_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms))
    }
}

// Export singleton instance
export const syncManager = new SyncManager()

// Export for use in composables
export function useSyncManager() {
    return {
        syncManager,
        queueOperation: syncManager.queueOperation.bind(syncManager),
        syncAll: syncManager.syncAll.bind(syncManager),
        resolveConflict: syncManager.resolveConflict.bind(syncManager),
        getConflicts: syncManager.getConflicts.bind(syncManager),
        getSyncState: syncManager.getSyncState.bind(syncManager),
        getSyncMetrics: syncManager.getSyncMetrics.bind(syncManager),
        getPendingOperationsCount: syncManager.getPendingOperationsCount.bind(syncManager),
        pauseSync: syncManager.pauseSync.bind(syncManager),
        resumeSync: syncManager.resumeSync.bind(syncManager)
    }
}
