/**
 * Unified Event Bus - Universal Workshop Frontend V2
 * 
 * Single, simplified event bus that handles all workshop events
 * with Arabic support and optional WebSocket integration
 */

import { ref, reactive, computed } from 'vue'
import type { 
  WorkshopEvent, 
  WorkshopEventType
} from './EventTypes'

// WebSocket Manager interface (can be implemented separately)
export interface WebSocketManager {
  isConnected: boolean
  connect(url: string): Promise<void>
  disconnect(): void
  send(data: any): void
  onMessage(handler: (data: any) => void): void
  onConnect(handler: () => void): void
  onDisconnect(handler: () => void): void
}

// Event subscription type
export interface EventSubscription {
  id: string
  eventType: WorkshopEventType
  handler: (event: WorkshopEvent) => void
  filter?: (event: WorkshopEvent) => boolean
  once?: boolean
}

// Event bus configuration
export interface EventBusConfig {
  enableHistory: boolean
  maxHistorySize: number
  enableArabicTemplates: boolean
  enableRealTime: boolean
  debug: boolean
}

/**
 * Unified Workshop Event Bus
 */
export class UnifiedEventBus {
  private config: EventBusConfig
  private subscriptions = new Map<string, EventSubscription[]>()
  private history = ref<WorkshopEvent[]>([])
  private webSocketManager?: WebSocketManager
  private eventCounter = 0

  // Reactive state
  private connectionStatus = ref<'connected' | 'disconnected' | 'reconnecting'>('disconnected')
  private lastEvent = ref<WorkshopEvent | null>(null)
  private metrics = reactive({
    totalEvents: 0,
    eventsPerSecond: 0,
    successRate: 100,
    lastEventTime: null as Date | null
  })

  constructor(config: Partial<EventBusConfig> = {}) {
    this.config = {
      enableHistory: true,
      maxHistorySize: 1000,
      enableArabicTemplates: true,
      enableRealTime: false,
      debug: false,
      ...config
    }

    if (this.config.debug) {
      console.log('🚀 UnifiedEventBus initialized with config:', this.config)
    }
  }

  /**
   * Enable real-time functionality with WebSocket
   */
  enableRealTime(wsManager: WebSocketManager) {
    this.webSocketManager = wsManager
    this.config.enableRealTime = true

    // Set up WebSocket event handlers
    wsManager.onConnect(() => {
      this.connectionStatus.value = 'connected'
      if (this.config.debug) {
        console.log('🔗 WebSocket connected')
      }
    })

    wsManager.onDisconnect(() => {
      this.connectionStatus.value = 'disconnected'
      if (this.config.debug) {
        console.log('🔌 WebSocket disconnected')
      }
    })

    wsManager.onMessage((data) => {
      this.handleWebSocketMessage(data)
    })
  }

  /**
   * Emit an event
   */
  async emit(event: Partial<WorkshopEvent>): Promise<string> {
    const fullEvent: WorkshopEvent = {
      id: this.generateEventId(),
      type: event.type!,
      source: event.source || 'manual' as any,
      priority: event.priority || 'medium',
      entityType: event.entityType || 'service_order' as any,
      entityId: event.entityId || '',
      workshopId: event.workshopId || 'default',
      timestamp: new Date(),
      data: event.data || {},
      metadata: event.metadata || {}
    }

    try {
      // Add to history
      if (this.config.enableHistory) {
        this.addToHistory(fullEvent)
      }

      // Update metrics
      this.updateMetrics(fullEvent)

      // Process Arabic template if enabled
      if (this.config.enableArabicTemplates) {
        // Arabic template processing would go here
        // For now, just add basic Arabic properties
        fullEvent.data.titleEn = `Event: ${fullEvent.type}`
        fullEvent.data.titleAr = `حدث: ${fullEvent.type}`
      }

      // Emit to local subscribers
      await this.emitToSubscribers(fullEvent)

      // Send via WebSocket if enabled
      if (this.config.enableRealTime && this.webSocketManager?.isConnected) {
        this.webSocketManager.send(fullEvent)
      }

      this.lastEvent.value = fullEvent

      if (this.config.debug) {
        console.log('📤 Event emitted:', fullEvent.type, fullEvent.id)
      }

      return fullEvent.id

    } catch (error) {
      console.error('❌ Failed to emit event:', error)
      throw error
    }
  }

  /**
   * Subscribe to events
   */
  subscribe(
    eventType: WorkshopEventType | WorkshopEventType[],
    handler: (event: WorkshopEvent) => void,
    options: {
      filter?: (event: WorkshopEvent) => boolean
      once?: boolean
    } = {}
  ): () => void {
    const types = Array.isArray(eventType) ? eventType : [eventType]
    const subscriptionIds: string[] = []

    types.forEach(type => {
      const subscription: EventSubscription = {
        id: this.generateSubscriptionId(),
        eventType: type,
        handler,
        filter: options.filter,
        once: options.once
      }

      if (!this.subscriptions.has(type)) {
        this.subscriptions.set(type, [])
      }

      this.subscriptions.get(type)!.push(subscription)
      subscriptionIds.push(subscription.id)

      if (this.config.debug) {
        console.log('🔔 Subscribed to:', type, subscription.id)
      }
    })

    // Return unsubscribe function
    return () => {
      subscriptionIds.forEach(id => {
        types.forEach(type => {
          const subs = this.subscriptions.get(type) || []
          const index = subs.findIndex(s => s.id === id)
          if (index > -1) {
            subs.splice(index, 1)
            if (this.config.debug) {
              console.log('🔕 Unsubscribed from:', type, id)
            }
          }
        })
      })
    }
  }

  /**
   * Get event history
   */
  getHistory(eventType?: WorkshopEventType, limit?: number): WorkshopEvent[] {
    let events = this.history.value

    if (eventType) {
      events = events.filter(e => e.type === eventType)
    }

    if (limit) {
      events = events.slice(0, limit)
    }

    return events
  }

  /**
   * Get connection status
   */
  get isConnected() {
    return computed(() => this.connectionStatus.value === 'connected')
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      connectionStatus: this.connectionStatus.value,
      historySize: this.history.value.length,
      subscriptionCount: Array.from(this.subscriptions.values()).reduce((sum, subs) => sum + subs.length, 0)
    }
  }

  /**
   * Clear history
   */
  clearHistory() {
    this.history.value = []
    if (this.config.debug) {
      console.log('🗑️ Event history cleared')
    }
  }

  /**
   * Disconnect and cleanup
   */
  disconnect() {
    if (this.webSocketManager) {
      this.webSocketManager.disconnect()
    }
    
    this.subscriptions.clear()
    this.clearHistory()
    this.connectionStatus.value = 'disconnected'

    if (this.config.debug) {
      console.log('👋 EventBus disconnected and cleaned up')
    }
  }

  // Private methods
  private async emitToSubscribers(event: WorkshopEvent) {
    const subscribers = this.subscriptions.get(event.type) || []
    
    for (const subscription of subscribers) {
      try {
        // Apply filter if provided
        if (subscription.filter && !subscription.filter(event)) {
          continue
        }

        // Call handler
        await subscription.handler(event)

        // Remove if it's a one-time subscription
        if (subscription.once) {
          const subs = this.subscriptions.get(event.type) || []
          const index = subs.findIndex(s => s.id === subscription.id)
          if (index > -1) {
            subs.splice(index, 1)
          }
        }

      } catch (error) {
        console.error('❌ Error in event handler:', error)
      }
    }
  }

  private addToHistory(event: WorkshopEvent) {
    this.history.value.unshift(event)
    
    // Maintain max size
    if (this.history.value.length > this.config.maxHistorySize) {
      this.history.value = this.history.value.slice(0, this.config.maxHistorySize)
    }
  }

  private updateMetrics(event: WorkshopEvent) {
    this.metrics.totalEvents++
    this.metrics.lastEventTime = event.timestamp
    
    // Simple events per second calculation (last 60 seconds)
    const now = Date.now()
    const oneMinuteAgo = now - 60000
    const recentEvents = this.history.value.filter(e => e.timestamp.getTime() > oneMinuteAgo)
    this.metrics.eventsPerSecond = recentEvents.length / 60
  }

  private processArabicTemplate(event: WorkshopEvent) {
    // Basic Arabic template processing
    // This can be enhanced later with proper templates
    event.data.titleEn = event.data.titleEn || `Event: ${event.type}`
    event.data.titleAr = event.data.titleAr || `حدث: ${event.type}`
  }

  private interpolateTemplate(template: string, variables: any): string {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return variables[key] !== undefined ? String(variables[key]) : match
    })
  }

  private handleWebSocketMessage(data: any) {
    try {
      // Convert WebSocket message to WorkshopEvent
      const event: WorkshopEvent = {
        id: data.id || this.generateEventId(),
        type: data.type,
        source: 'external_api' as any,
        priority: data.priority || 'medium',
        entityType: data.entityType || 'unknown',
        entityId: data.entityId || '',
        workshopId: data.workshopId || 'default',
        timestamp: new Date(data.timestamp || Date.now()),
        data: data.data || {},
        metadata: data.metadata || {}
      }

      // Process like a local event
      this.addToHistory(event)
      this.updateMetrics(event)
      this.emitToSubscribers(event)

    } catch (error) {
      console.error('❌ Error processing WebSocket message:', error)
    }
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${++this.eventCounter}`
  }

  private generateSubscriptionId(): string {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}

// Global instance
export const eventBus = new UnifiedEventBus({
  enableHistory: true,
  enableArabicTemplates: true,
  debug: import.meta.env.DEV
})

// Helper functions
export const emitServiceOrderEvent = (
  type: 'service_order_updated' | 'service_started' | 'service_completed',
  data: any
) => eventBus.emit({ type, ...data })

export const emitTechnicianEvent = (
  type: 'technician_updated',
  data: any
) => eventBus.emit({ type, ...data })

export const emitInventoryEvent = (
  type: 'inventory_updated' | 'inventory_low_stock',
  data: any
) => eventBus.emit({ type, ...data })

export default eventBus
