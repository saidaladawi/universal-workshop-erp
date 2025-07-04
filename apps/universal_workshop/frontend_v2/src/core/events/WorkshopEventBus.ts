/**
 * Workshop Event Bus - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Event System Enhancement
 *
 * Enhanced event bus that integrates with the existing WorkshopEventBus
 * and provides comprehensive event management with Arabic support.
 */

import { ref, computed, reactive } from 'vue'
import {
    WorkshopEvent,
    WorkshopEventType,
    EventHandler,
    EventFilter,
    EventMetrics,
    SubscriptionConfig
} from './EventTypes'
import { eventHandlerRegistry } from './EventHandlers'
import {
    arabicEventTemplateRegistry,
    processArabicTemplate,
    ArabicEventTemplate,
    TemplateVariables
} from './ArabicEventTemplates'
// Import real-time WebSocket event bus for integration
import { WorkshopEventBus as RealTimeEventBus } from '../../features/realtime/WorkshopEventBus'

// Enhanced Event Bus Configuration
export interface EnhancedEventBusConfig {
    enableRealTime: boolean
    enablePersistence: boolean
    enableAnalytics: boolean
    enableArabicTemplates: boolean
    maxEventHistory: number
    batchSize: number
    retryAttempts: number
    retryDelay: number
    compressionEnabled: boolean
    encryptionEnabled: boolean
}

// Event subscription management
export interface EventSubscription {
    id: string
    eventTypes: WorkshopEventType[]
    handler: EventHandler
    filter?: EventFilter
    config?: SubscriptionConfig
    createdAt: Date
    lastTriggered?: Date
    triggerCount: number
    isActive: boolean
}

// Event statistics
export interface EventStatistics {
    totalEvents: number
    eventsByType: Map<WorkshopEventType, number>
    eventsByPriority: Map<string, number>
    processingTimes: number[]
    errorCount: number
    successCount: number
    averageProcessingTime: number
    peakEventsPerSecond: number
    lastEventTime?: Date
}

/**
 * Enhanced Workshop Event Bus
 * Provides comprehensive event management with Arabic support
 */
export class EnhancedWorkshopEventBus {
    private config: EnhancedEventBusConfig
    private subscriptions: Map<string, EventSubscription> = new Map()
    private eventHistory: WorkshopEvent[] = []
    private eventQueue: WorkshopEvent[] = []
    private statistics: EventStatistics = reactive({
        totalEvents: 0,
        eventsByType: new Map(),
        eventsByPriority: new Map(),
        processingTimes: [],
        errorCount: 0,
        successCount: 0,
        averageProcessingTime: 0,
        peakEventsPerSecond: 0
    })

    private isProcessing = ref(false)
    private isConnected = ref(false)
    private lastError = ref<string | null>(null)
    private processingMetrics = ref<EventMetrics>({
        totalEvents: 0,
        eventsPerSecond: 0,
        avgProcessingTime: 0,
        maxProcessingTime: 0,
        minProcessingTime: 0,
        errorRate: 0,
        successRate: 0,
        queueSize: 0,
        retryCount: 0,
        lastEventTime: new Date(),
        connectionStatus: 'disconnected' as const,
        latency: 0,
        bandwidth: 0
    })

    // Real-time integration
    private realTimeEventBus: RealTimeEventBus | null = null
    private connectionInfo = ref({
        connectionStatus: 'disconnected' as 'connected' | 'disconnected' | 'reconnecting',
        latency: 0,
        bandwidth: 0
    })

    constructor(config: Partial<EnhancedEventBusConfig> = {}) {
        this.config = {
            enableRealTime: true,
            enablePersistence: true,
            enableAnalytics: true,
            enableArabicTemplates: true,
            maxEventHistory: 1000,
            batchSize: 50,
            retryAttempts: 3,
            retryDelay: 1000,
            compressionEnabled: false,
            encryptionEnabled: false,
            ...config
        }

        this.initialize()
    }

    /**
     * Initialize the enhanced event bus
     */
    private async initialize(): Promise<void> {
        try {
            // Initialize real-time connection if enabled
            if (this.config.enableRealTime) {
                await this.connectToRealTimeEventBus()
            }

            // Register default event handlers
            this.registerDefaultHandlers()

            // Start periodic statistics collection
            this.startStatisticsCollection()

            console.log('🚀 Enhanced Workshop Event Bus initialized')
        } catch (error) {
            console.error('❌ Failed to initialize Enhanced Workshop Event Bus:', error)
            this.lastError.value = error instanceof Error ? error.message : 'Initialization failed'
        }
    }

    /**
     * Connect to the real-time event bus
     */
    private async connectToRealTimeEventBus(): Promise<void> {
        try {
            // Subscribe to real-time events
            this.realTimeEventBus?.on('service_update', this.handleRealTimeEvent.bind(this))
            this.realTimeEventBus?.on('technician_status', this.handleRealTimeEvent.bind(this))
            this.realTimeEventBus?.on('inventory_change', this.handleRealTimeEvent.bind(this))
            this.realTimeEventBus?.on('customer_notification', this.handleRealTimeEvent.bind(this))
            this.realTimeEventBus?.on('system_alert', this.handleRealTimeEvent.bind(this))

            this.isConnected.value = true
            console.log('🔗 Connected to real-time event bus')
        } catch (error) {
            console.error('❌ Failed to connect to real-time event bus:', error)
            throw error
        }
    }

    /**
     * Subscribe to specific event types
     */
    subscribe(
        eventTypes: WorkshopEventType | WorkshopEventType[],
        handler: EventHandler,
        config?: SubscriptionConfig
    ): string {
        const subscriptionId = this.generateSubscriptionId()
        const types = Array.isArray(eventTypes) ? eventTypes : [eventTypes]

        const subscription: EventSubscription = {
            id: subscriptionId,
            eventTypes: types,
            handler,
            config,
            createdAt: new Date(),
            triggerCount: 0,
            isActive: true
        }

        this.subscriptions.set(subscriptionId, subscription)

        // Register with the event handler registry
        const unregister = eventHandlerRegistry.register(types, handler)

        console.log(`📝 Subscription created: ${subscriptionId} for events: ${types.join(', ')}`)

        return subscriptionId
    }

    /**
     * Unsubscribe from events
     */
    unsubscribe(subscriptionId: string): boolean {
        const subscription = this.subscriptions.get(subscriptionId)
        if (!subscription) {
            console.warn(`⚠️ Subscription not found: ${subscriptionId}`)
            return false
        }

        subscription.isActive = false
        this.subscriptions.delete(subscriptionId)

        console.log(`🗑️ Subscription removed: ${subscriptionId}`)
        return true
    }

    /**
     * Emit a new event
     */
    async emit(
        eventType: WorkshopEventType,
        data: any,
        options: {
            priority?: 'critical' | 'high' | 'medium' | 'low'
            target?: string | string[]
            requiresAck?: boolean
            ttl?: number
            metadata?: any
            useArabicTemplate?: boolean
            templateVariables?: TemplateVariables
        } = {}
    ): Promise<string> {
        const event: WorkshopEvent = {
            id: this.generateEventId(),
            type: eventType,
            timestamp: new Date(),
            source: 'desktop_app',
            priority: options.priority || 'medium',
            entityType: this.inferEntityType(eventType) as any,
            entityId: data.entityId || this.generateEntityId(),
            workshopId: data.workshopId || 'default',
            data,
            target: options.target,
            requiresAck: options.requiresAck,
            ttl: options.ttl,
            metadata: {
                ...options.metadata,
                sessionId: this.getSessionId(),
                platform: 'web'
            }
        }

        try {
            // Process Arabic template if requested
            if (options.useArabicTemplate && options.templateVariables) {
                await this.processArabicNotification(event, options.templateVariables)
            }

            // Add to event history
            this.addToHistory(event)

            // Update statistics
            this.updateStatistics(event)

            // Process through handlers
            await this.processEvent(event)

            // Send via real-time if connected
            if (this.isConnected.value && this.config.enableRealTime) {
                await this.realTimeEventBus?.send({
                    type: this.mapToRealTimeEventType(eventType) as 'service_update' | 'system_alert' | 'technician_status' | 'inventory_change' | 'customer_notification',
                    source: 'enhanced_event_bus',
                    data: event.data,
                    priority: event.priority
                })
            }

            console.log(`📤 Event emitted: ${eventType} (${event.id})`)
            return event.id

        } catch (error) {
            this.statistics.errorCount++
            this.lastError.value = error instanceof Error ? error.message : 'Event emission failed'
            console.error(`❌ Failed to emit event ${eventType}:`, error)
            throw error
        }
    }

    /**
     * Process Arabic notification template
     */
    private async processArabicNotification(
        event: WorkshopEvent,
        variables: TemplateVariables
    ): Promise<void> {
        if (!this.config.enableArabicTemplates) return

        try {
            const template = arabicEventTemplateRegistry.getTemplate(event.type)
            if (template) {
                const notification = processArabicTemplate(event.type, variables, true)
                if (notification) {
                    event.data.arabicNotification = notification
                }
            }
        } catch (error) {
            console.warn('⚠️ Failed to process Arabic template:', error)
        }
    }

    /**
     * Process event through registered handlers
     */
    private async processEvent(event: WorkshopEvent): Promise<void> {
        const startTime = performance.now()
        this.isProcessing.value = true

        try {
            // Filter active subscriptions for this event type
            const relevantSubscriptions = Array.from(this.subscriptions.values())
                .filter(sub => sub.isActive && sub.eventTypes.includes(event.type))

            // Apply filters if specified
            const filteredSubscriptions = relevantSubscriptions.filter(sub =>
                this.applyEventFilter(event, sub.filter)
            )

            // Execute handlers
            for (const subscription of filteredSubscriptions) {
                try {
                    await subscription.handler(event)
                    subscription.triggerCount++
                    subscription.lastTriggered = new Date()
                } catch (error) {
                    console.error(`❌ Handler failed for subscription ${subscription.id}:`, error)
                }
            }

            // Process through event handler registry
            await eventHandlerRegistry.processEvent(event)

            this.statistics.successCount++

        } catch (error) {
            this.statistics.errorCount++
            throw error
        } finally {
            const processingTime = performance.now() - startTime
            this.statistics.processingTimes.push(processingTime)
            this.updateProcessingMetrics(processingTime)
            this.isProcessing.value = false
        }
    }

    /**
     * Handle real-time events from the base event bus
     */
    private async handleRealTimeEvent(realTimeEvent: any): Promise<void> {
        try {
            // Convert real-time event to workshop event format
            const event: WorkshopEvent = {
                id: this.generateEventId(),
                type: this.mapFromRealTimeEventType(realTimeEvent.type),
                timestamp: new Date(),
                source: 'external_api',
                priority: 'medium',
                entityType: 'service_order', // Default, should be inferred
                entityId: realTimeEvent.data?.entityId || this.generateEntityId(),
                workshopId: 'default',
                data: realTimeEvent.data || {},
                metadata: {
                    tags: ['real-time', 'external'],
                    retryCount: 0,
                    processingTime: 0,
                    sessionId: 'real-time-session',
                    deviceId: 'server',
                    platform: 'web' as const
                }
            }

            await this.processEvent(event)
            this.addToHistory(event)
            this.updateStatistics(event)

        } catch (error) {
            console.error('❌ Failed to handle real-time event:', error)
        }
    }

    /**
     * Apply event filter to determine if subscription should be triggered
     */
    private applyEventFilter(event: WorkshopEvent, filter?: EventFilter): boolean {
        if (!filter) return true

        if (filter.types && !filter.types.includes(event.type)) return false
        if (filter.sources && !filter.sources.includes(event.source)) return false
        if (filter.priorities && !filter.priorities.includes(event.priority)) return false
        if (filter.entityTypes && !filter.entityTypes.includes(event.entityType)) return false
        if (filter.entityIds && !filter.entityIds.includes(event.entityId)) return false
        if (filter.userIds && event.userId && !filter.userIds.includes(event.userId)) return false
        if (filter.workshopIds && !filter.workshopIds.includes(event.workshopId)) return false
        if (filter.since && event.timestamp < filter.since) return false
        if (filter.until && event.timestamp > filter.until) return false

        return true
    }

    /**
     * Register default event handlers
     */
    private registerDefaultHandlers(): void {
        // Analytics handler
        this.subscribe(['service_order_updated', 'service_completed'], async (event) => {
            // Update analytics metrics
            console.log(`📊 Analytics: Processing ${event.type}`)
        })

        // Notification handler
        this.subscribe(['customer_arrived', 'service_completed'], async (event) => {
            // Send notifications
            console.log(`🔔 Notification: Processing ${event.type}`)
        })

        // System monitoring handler
        this.subscribe(['system_alert', 'backup_failed'], async (event) => {
            // Handle system events
            console.log(`⚙️ System: Processing ${event.type}`)
        })
    }

    /**
     * Start periodic statistics collection
     */
    private startStatisticsCollection(): void {
        setInterval(() => {
            this.updateAggregateStatistics()
        }, 60000) // Every minute

        setInterval(() => {
            this.cleanupOldData()
        }, 300000) // Every 5 minutes
    }

    /**
     * Update aggregate statistics
     */
    private updateAggregateStatistics(): void {
        if (this.statistics.processingTimes.length > 0) {
            const sum = this.statistics.processingTimes.reduce((a, b) => a + b, 0)
            this.statistics.averageProcessingTime = sum / this.statistics.processingTimes.length
        }

        // Update processing metrics
        this.processingMetrics.value = {
            ...this.processingMetrics.value,
            totalEvents: this.statistics.totalEvents,
            errorRate: this.statistics.totalEvents > 0 ?
                (this.statistics.errorCount / this.statistics.totalEvents) * 100 : 0,
            successRate: this.statistics.totalEvents > 0 ?
                (this.statistics.successCount / this.statistics.totalEvents) * 100 : 0,
            queueSize: this.eventQueue.length,
            avgProcessingTime: this.statistics.averageProcessingTime,
            connectionStatus: this.isConnected.value ? 'connected' : 'disconnected'
        }
    }

    /**
     * Update statistics for a processed event
     */
    private updateStatistics(event: WorkshopEvent): void {
        this.statistics.totalEvents++
        this.statistics.lastEventTime = event.timestamp

        // Update event type count
        const typeCount = this.statistics.eventsByType.get(event.type) || 0
        this.statistics.eventsByType.set(event.type, typeCount + 1)

        // Update priority count
        const priorityCount = this.statistics.eventsByPriority.get(event.priority) || 0
        this.statistics.eventsByPriority.set(event.priority, priorityCount + 1)
    }

    /**
     * Update processing metrics
     */
    private updateProcessingMetrics(processingTime: number): void {
        const current = this.processingMetrics.value

        this.processingMetrics.value = {
            ...current,
            maxProcessingTime: Math.max(current.maxProcessingTime, processingTime),
            minProcessingTime: current.minProcessingTime === 0 ?
                processingTime : Math.min(current.minProcessingTime, processingTime)
        }
    }

    /**
     * Add event to history
     */
    private addToHistory(event: WorkshopEvent): void {
        if (!this.config.enablePersistence) return

        this.eventHistory.push(event)

        // Keep only recent events
        if (this.eventHistory.length > this.config.maxEventHistory) {
            this.eventHistory.splice(0, this.eventHistory.length - this.config.maxEventHistory)
        }
    }

    /**
     * Cleanup old data
     */
    private cleanupOldData(): void {
        const cutoffTime = new Date(Date.now() - 24 * 60 * 60 * 1000) // 24 hours ago

        // Clean event history
        this.eventHistory = this.eventHistory.filter(event =>
            event.timestamp > cutoffTime
        )

        // Clean processing times (keep last 1000)
        if (this.statistics.processingTimes.length > 1000) {
            this.statistics.processingTimes.splice(0, this.statistics.processingTimes.length - 1000)
        }
    }

    // Utility methods
    private generateEventId(): string {
        return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private generateSubscriptionId(): string {
        return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }

    private generateEntityId(): string {
        return `entity_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
    }

    private getSessionId(): string {
        return `session_${Date.now()}` // Simplified session ID
    }

    private inferEntityType(eventType: WorkshopEventType): string {
        if (eventType.includes('service')) return 'service_order'
        if (eventType.includes('technician')) return 'technician'
        if (eventType.includes('customer')) return 'customer'
        if (eventType.includes('parts')) return 'part'
        if (eventType.includes('quality')) return 'quality_check'
        if (eventType.includes('system')) return 'system'
        return 'service_order' // Default
    }

    private mapToRealTimeEventType(eventType: WorkshopEventType): string {
        const mapping: Record<string, string> = {
            'service_order_updated': 'service_update',
            'technician_status_changed': 'technician_status',
            'parts_inventory_low': 'inventory_change',
            'customer_arrived': 'customer_notification',
            'system_alert': 'system_alert'
        }
        return mapping[eventType] || 'service_update'
    }

    private mapFromRealTimeEventType(realTimeType: string): WorkshopEventType {
        const mapping: Record<string, WorkshopEventType> = {
            'service_update': 'service_order_updated',
            'technician_status': 'technician_status_changed',
            'inventory_change': 'parts_inventory_low',
            'customer_notification': 'customer_arrived',
            'system_alert': 'system_alert'
        }
        return mapping[realTimeType] || 'service_order_updated'
    }

    // Public API methods
    getStatistics(): EventStatistics {
        return { ...this.statistics }
    }

    getProcessingMetrics() {
        return this.processingMetrics.value
    }

    getEventHistory(filter?: EventFilter): WorkshopEvent[] {
        if (!filter) return [...this.eventHistory]
        return this.eventHistory.filter(event => this.applyEventFilter(event, filter))
    }

    getActiveSubscriptions(): EventSubscription[] {
        return Array.from(this.subscriptions.values()).filter(sub => sub.isActive)
    }

    getConnectionStatus() {
        return this.isConnected.value
    }

    getLastError() {
        return this.lastError.value
    }

    isProcessingEvents() {
        return this.isProcessing.value
    }

    // Configuration methods
    updateConfig(newConfig: Partial<EnhancedEventBusConfig>): void {
        this.config = { ...this.config, ...newConfig }
    }

    getConfig(): EnhancedEventBusConfig {
        return { ...this.config }
    }
}

// Export singleton instance
export const enhancedWorkshopEventBus = new EnhancedWorkshopEventBus()

// Export for use in composables
export function useEnhancedEventBus() {
    return {
        eventBus: enhancedWorkshopEventBus,
        subscribe: enhancedWorkshopEventBus.subscribe.bind(enhancedWorkshopEventBus),
        unsubscribe: enhancedWorkshopEventBus.unsubscribe.bind(enhancedWorkshopEventBus),
        emit: enhancedWorkshopEventBus.emit.bind(enhancedWorkshopEventBus),
        getStatistics: enhancedWorkshopEventBus.getStatistics.bind(enhancedWorkshopEventBus),
        getProcessingMetrics: enhancedWorkshopEventBus.getProcessingMetrics.bind(enhancedWorkshopEventBus),
        getEventHistory: enhancedWorkshopEventBus.getEventHistory.bind(enhancedWorkshopEventBus),
        isConnected: enhancedWorkshopEventBus.getConnectionStatus.bind(enhancedWorkshopEventBus),
        isProcessing: enhancedWorkshopEventBus.isProcessingEvents.bind(enhancedWorkshopEventBus)
    }
}
