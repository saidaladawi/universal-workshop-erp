/**
 * Event Handlers - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Event System Enhancement
 * 
 * Comprehensive event processing system with Arabic support and
 * intelligent routing for workshop management operations.
 */

import { 
  WorkshopEvent, 
  WorkshopEventType, 
  EventHandler,
  ServiceOrderEvent,
  TechnicianEvent,
  InventoryEvent,
  CustomerEvent,
  QualityCheckEvent,
  SystemEvent,
  EventPriority,
  EventMetadata
} from './EventTypes'

// Event processing result
export interface ProcessingResult {
  success: boolean
  processedAt: Date
  processingTime: number
  errorMessage?: string
  retryCount: number
  nextRetryAt?: Date
}

// Event routing configuration
export interface RoutingConfig {
  eventType: WorkshopEventType
  priority: EventPriority
  handlers: string[]
  shouldPersist: boolean
  shouldBroadcast: boolean
  retryAttempts: number
  retryDelay: number
  deadLetterQueue: boolean
}

/**
 * Main Event Handler Registry
 * Manages registration and execution of event handlers
 */
export class EventHandlerRegistry {
  private handlers: Map<WorkshopEventType, Set<EventHandler>> = new Map()
  private routingConfig: Map<WorkshopEventType, RoutingConfig> = new Map()
  private processingMetrics: Map<string, ProcessingResult[]> = new Map()
  private isProcessing: boolean = false
  private processingQueue: WorkshopEvent[] = []
  private maxQueueSize: number = 1000
  private maxRetryAttempts: number = 3
  private retryDelay: number = 1000

  constructor() {
    this.initializeDefaultRouting()
  }

  /**
   * Register an event handler for specific event types
   */
  register<T extends WorkshopEvent>(
    eventTypes: WorkshopEventType | WorkshopEventType[],
    handler: EventHandler<T>,
    config?: Partial<RoutingConfig>
  ): () => void {
    const types = Array.isArray(eventTypes) ? eventTypes : [eventTypes]
    
    types.forEach(type => {
      if (!this.handlers.has(type)) {
        this.handlers.set(type, new Set())
      }
      
      this.handlers.get(type)!.add(handler as EventHandler)
      
      // Update routing config if provided
      if (config) {
        this.updateRoutingConfig(type, config)
      }
    })

    // Return unregister function
    return () => {
      types.forEach(type => {
        this.handlers.get(type)?.delete(handler as EventHandler)
      })
    }
  }

  /**
   * Process a single event through registered handlers
   */
  async processEvent(event: WorkshopEvent): Promise<ProcessingResult> {
    const startTime = performance.now()
    const result: ProcessingResult = {
      success: false,
      processedAt: new Date(),
      processingTime: 0,
      retryCount: event.metadata?.retryCount || 0
    }

    try {
      // Check if we have handlers for this event type
      const handlers = this.handlers.get(event.type)
      if (!handlers || handlers.size === 0) {
        console.warn(`⚠️ No handlers registered for event type: ${event.type}`)
        result.success = true // Not an error, just no handlers
        return result
      }

      // Route event to appropriate handlers
      await this.routeEvent(event, handlers)
      
      result.success = true
      console.log(`✅ Event processed successfully: ${event.type} (${event.id})`)
      
    } catch (error) {
      result.errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error(`❌ Error processing event ${event.type} (${event.id}):`, error)
      
      // Schedule retry if applicable
      if (result.retryCount < this.maxRetryAttempts) {
        result.nextRetryAt = new Date(Date.now() + this.retryDelay * Math.pow(2, result.retryCount))
        result.retryCount++
        
        // Add back to queue with updated retry count
        const retryEvent = {
          ...event,
          metadata: {
            ...event.metadata,
            retryCount: result.retryCount
          }
        }
        this.processingQueue.push(retryEvent)
      }
    } finally {
      result.processingTime = performance.now() - startTime
      this.recordProcessingMetrics(event.id, result)
    }

    return result
  }

  /**
   * Process multiple events in batch
   */
  async processBatch(events: WorkshopEvent[]): Promise<ProcessingResult[]> {
    if (this.isProcessing) {
      console.warn('⚠️ Batch processing already in progress, queueing events')
      this.processingQueue.push(...events)
      return []
    }

    this.isProcessing = true
    const results: ProcessingResult[] = []

    try {
      // Process events by priority
      const sortedEvents = this.sortEventsByPriority(events)
      
      for (const event of sortedEvents) {
        const result = await this.processEvent(event)
        results.push(result)
        
        // Brief pause to prevent overwhelming the system
        if (event.priority === 'critical') {
          await this.sleep(10)
        } else if (event.priority === 'high') {
          await this.sleep(50)
        } else {
          await this.sleep(100)
        }
      }

      // Process any queued events
      if (this.processingQueue.length > 0) {
        const queuedEvents = this.processingQueue.splice(0, this.maxQueueSize)
        const queuedResults = await this.processBatch(queuedEvents)
        results.push(...queuedResults)
      }

    } finally {
      this.isProcessing = false
    }

    return results
  }

  /**
   * Route event to specific handlers based on configuration
   */
  private async routeEvent(event: WorkshopEvent, handlers: Set<EventHandler>): Promise<void> {
    const routingConfig = this.routingConfig.get(event.type)
    
    if (routingConfig?.shouldPersist) {
      await this.persistEvent(event)
    }

    // Execute handlers concurrently for better performance
    const handlerPromises = Array.from(handlers).map(async handler => {
      try {
        await handler(event)
      } catch (error) {
        console.error(`❌ Handler failed for event ${event.type}:`, error)
        throw error
      }
    })

    await Promise.all(handlerPromises)

    if (routingConfig?.shouldBroadcast) {
      await this.broadcastEvent(event)
    }
  }

  /**
   * Initialize default routing configuration
   */
  private initializeDefaultRouting(): void {
    const defaultConfigs: Array<[WorkshopEventType, RoutingConfig]> = [
      ['service_order_updated', {
        eventType: 'service_order_updated',
        priority: 'high',
        handlers: ['service_order_handler', 'notification_handler', 'analytics_handler'],
        shouldPersist: true,
        shouldBroadcast: true,
        retryAttempts: 3,
        retryDelay: 1000,
        deadLetterQueue: true
      }],
      ['technician_status_changed', {
        eventType: 'technician_status_changed',
        priority: 'medium',
        handlers: ['technician_handler', 'dashboard_handler'],
        shouldPersist: true,
        shouldBroadcast: true,
        retryAttempts: 2,
        retryDelay: 2000,
        deadLetterQueue: false
      }],
      ['parts_inventory_low', {
        eventType: 'parts_inventory_low',
        priority: 'high',
        handlers: ['inventory_handler', 'alert_handler', 'procurement_handler'],
        shouldPersist: true,
        shouldBroadcast: true,
        retryAttempts: 3,
        retryDelay: 1500,
        deadLetterQueue: true
      }],
      ['system_alert', {
        eventType: 'system_alert',
        priority: 'critical',
        handlers: ['system_handler', 'admin_notification_handler'],
        shouldPersist: true,
        shouldBroadcast: true,
        retryAttempts: 5,
        retryDelay: 500,
        deadLetterQueue: true
      }]
    ]

    defaultConfigs.forEach(([type, config]) => {
      this.routingConfig.set(type, config)
    })
  }

  /**
   * Update routing configuration for specific event type
   */
  private updateRoutingConfig(eventType: WorkshopEventType, config: Partial<RoutingConfig>): void {
    const existing = this.routingConfig.get(eventType) || {
      eventType,
      priority: 'medium',
      handlers: [],
      shouldPersist: false,
      shouldBroadcast: false,
      retryAttempts: 1,
      retryDelay: 1000,
      deadLetterQueue: false
    }

    this.routingConfig.set(eventType, { ...existing, ...config })
  }

  /**
   * Sort events by priority for processing order
   */
  private sortEventsByPriority(events: WorkshopEvent[]): WorkshopEvent[] {
    const priorityOrder: Record<EventPriority, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3
    }

    return events.sort((a, b) => {
      const aPriority = priorityOrder[a.priority] || 3
      const bPriority = priorityOrder[b.priority] || 3
      return aPriority - bPriority
    })
  }

  /**
   * Persist event to storage
   */
  private async persistEvent(event: WorkshopEvent): Promise<void> {
    try {
      // In a real implementation, this would save to database
      console.log(`💾 Persisting event: ${event.type} (${event.id})`)
      
      // Simulate async persistence
      await this.sleep(50)
      
    } catch (error) {
      console.error('❌ Failed to persist event:', error)
      throw error
    }
  }

  /**
   * Broadcast event to connected clients
   */
  private async broadcastEvent(event: WorkshopEvent): Promise<void> {
    try {
      console.log(`📡 Broadcasting event: ${event.type} (${event.id})`)
      
      // In a real implementation, this would use WebSocket or Server-Sent Events
      // For now, we'll simulate the broadcast
      await this.sleep(25)
      
    } catch (error) {
      console.error('❌ Failed to broadcast event:', error)
      throw error
    }
  }

  /**
   * Record processing metrics for monitoring
   */
  private recordProcessingMetrics(eventId: string, result: ProcessingResult): void {
    if (!this.processingMetrics.has(eventId)) {
      this.processingMetrics.set(eventId, [])
    }
    
    const metrics = this.processingMetrics.get(eventId)!
    metrics.push(result)
    
    // Keep only last 10 results per event
    if (metrics.length > 10) {
      metrics.splice(0, metrics.length - 10)
    }
  }

  /**
   * Get processing metrics for analysis
   */
  getProcessingMetrics(eventId?: string): Map<string, ProcessingResult[]> | ProcessingResult[] {
    if (eventId) {
      return this.processingMetrics.get(eventId) || []
    }
    return this.processingMetrics
  }

  /**
   * Get handler registration status
   */
  getHandlerStatus(): Map<WorkshopEventType, number> {
    const status = new Map<WorkshopEventType, number>()
    
    this.handlers.forEach((handlers, eventType) => {
      status.set(eventType, handlers.size)
    })
    
    return status
  }

  /**
   * Clear all handlers (useful for testing)
   */
  clearAllHandlers(): void {
    this.handlers.clear()
    this.processingMetrics.clear()
    this.processingQueue = []
  }

  /**
   * Utility sleep function
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

/**
 * Specific Event Handlers for different event types
 */

// Service Order Event Handler
export const serviceOrderEventHandler: EventHandler<ServiceOrderEvent> = async (event) => {
  console.log(`🔧 Processing service order event: ${event.type}`)
  
  switch (event.type) {
    case 'service_order_updated':
      await handleServiceOrderUpdate(event)
      break
    case 'service_started':
      await handleServiceStarted(event)
      break
    case 'service_completed':
      await handleServiceCompleted(event)
      break
    case 'service_paused':
      await handleServicePaused(event)
      break
    case 'service_resumed':
      await handleServiceResumed(event)
      break
  }
}

// Technician Event Handler
export const technicianEventHandler: EventHandler<TechnicianEvent> = async (event) => {
  console.log(`👨‍🔧 Processing technician event: ${event.type}`)
  
  switch (event.type) {
    case 'technician_clocked_in':
      await handleTechnicianClockIn(event)
      break
    case 'technician_clocked_out':
      await handleTechnicianClockOut(event)
      break
    case 'technician_status_changed':
      await handleTechnicianStatusChange(event)
      break
  }
}

// Inventory Event Handler
export const inventoryEventHandler: EventHandler<InventoryEvent> = async (event) => {
  console.log(`📦 Processing inventory event: ${event.type}`)
  
  switch (event.type) {
    case 'parts_inventory_low':
      await handleLowInventoryAlert(event)
      break
    case 'parts_received':
      await handlePartsReceived(event)
      break
    case 'parts_ordered':
      await handlePartsOrdered(event)
      break
  }
}

// Customer Event Handler
export const customerEventHandler: EventHandler<CustomerEvent> = async (event) => {
  console.log(`🤝 Processing customer event: ${event.type}`)
  
  switch (event.type) {
    case 'customer_arrived':
      await handleCustomerArrival(event)
      break
    case 'customer_notification_sent':
      await handleCustomerNotificationSent(event)
      break
  }
}

// Quality Check Event Handler
export const qualityCheckEventHandler: EventHandler<QualityCheckEvent> = async (event) => {
  console.log(`✅ Processing quality check event: ${event.type}`)
  
  switch (event.type) {
    case 'quality_check_required':
      await handleQualityCheckRequired(event)
      break
    case 'quality_check_completed':
      await handleQualityCheckCompleted(event)
      break
  }
}

// System Event Handler
export const systemEventHandler: EventHandler<SystemEvent> = async (event) => {
  console.log(`⚙️ Processing system event: ${event.type}`)
  
  switch (event.type) {
    case 'system_maintenance':
      await handleSystemMaintenance(event)
      break
    case 'system_alert':
      await handleSystemAlert(event)
      break
    case 'backup_completed':
      await handleBackupCompleted(event)
      break
    case 'backup_failed':
      await handleBackupFailed(event)
      break
  }
}

// Individual event processing functions
async function handleServiceOrderUpdate(event: ServiceOrderEvent): Promise<void> {
  // Update service order in data store
  // Send notifications to customer and technician
  // Update dashboard displays
  // Log for analytics
}

async function handleServiceStarted(event: ServiceOrderEvent): Promise<void> {
  // Update service order status
  // Start timer for service duration
  // Notify customer of service start
  // Update technician status
}

async function handleServiceCompleted(event: ServiceOrderEvent): Promise<void> {
  // Update service order status
  // Calculate final cost and duration
  // Generate invoice
  // Send completion notification to customer
  // Update technician availability
  // Trigger quality check if required
}

async function handleServicePaused(event: ServiceOrderEvent): Promise<void> {
  // Update service order status
  // Pause timer for service duration
  // Log pause reason
  // Update technician status if needed
}

async function handleServiceResumed(event: ServiceOrderEvent): Promise<void> {
  // Update service order status
  // Resume timer for service duration
  // Log resume time
  // Update technician status
}

async function handleTechnicianClockIn(event: TechnicianEvent): Promise<void> {
  // Update technician status
  // Start shift timer
  // Update dashboard displays
  // Check for assigned service orders
}

async function handleTechnicianClockOut(event: TechnicianEvent): Promise<void> {
  // Update technician status
  // Calculate shift duration
  // Update work reports
  // Handle active service orders
}

async function handleTechnicianStatusChange(event: TechnicianEvent): Promise<void> {
  // Update technician status
  // Update dashboard displays
  // Handle service order reassignments if needed
  // Send notifications if required
}

async function handleLowInventoryAlert(event: InventoryEvent): Promise<void> {
  // Send alert to inventory manager
  // Check for existing orders
  // Generate reorder suggestion
  // Update inventory status
}

async function handlePartsReceived(event: InventoryEvent): Promise<void> {
  // Update inventory levels
  // Process any pending service orders waiting for parts
  // Update supplier performance metrics
  // Send confirmation to ordering team
}

async function handlePartsOrdered(event: InventoryEvent): Promise<void> {
  // Update inventory status
  // Set expected delivery date
  // Schedule follow-up reminders
  // Update pending service orders
}

async function handleCustomerArrival(event: CustomerEvent): Promise<void> {
  // Update customer status
  // Notify assigned technician
  // Update service order priority
  // Update dashboard displays
}

async function handleCustomerNotificationSent(event: CustomerEvent): Promise<void> {
  // Log notification in customer communication history
  // Update notification status
  // Schedule follow-up if needed
  // Track delivery status
}

async function handleQualityCheckRequired(event: QualityCheckEvent): Promise<void> {
  // Assign quality inspector
  // Create quality check record
  // Send notification to inspector
  // Update service order status
}

async function handleQualityCheckCompleted(event: QualityCheckEvent): Promise<void> {
  // Update quality check results
  // Update service order status
  // Handle rework if needed
  // Send completion notification
}

async function handleSystemMaintenance(event: SystemEvent): Promise<void> {
  // Send maintenance notifications
  // Update system status
  // Prepare for downtime if scheduled
  // Log maintenance activity
}

async function handleSystemAlert(event: SystemEvent): Promise<void> {
  // Send alert to administrators
  // Log alert in system logs
  // Update system status if needed
  // Trigger automated responses if configured
}

async function handleBackupCompleted(event: SystemEvent): Promise<void> {
  // Log successful backup
  // Update backup status
  // Clean up old backups if needed
  // Send success notification
}

async function handleBackupFailed(event: SystemEvent): Promise<void> {
  // Log backup failure
  // Send failure alert to administrators
  // Schedule retry if appropriate
  // Update backup status
}

// Export singleton instance
export const eventHandlerRegistry = new EventHandlerRegistry()

// Auto-register default handlers
eventHandlerRegistry.register(['service_order_updated', 'service_started', 'service_completed', 'service_paused', 'service_resumed'], serviceOrderEventHandler)
eventHandlerRegistry.register(['technician_clocked_in', 'technician_clocked_out', 'technician_status_changed'], technicianEventHandler)
eventHandlerRegistry.register(['parts_inventory_low', 'parts_received', 'parts_ordered'], inventoryEventHandler)
eventHandlerRegistry.register(['customer_arrived', 'customer_notification_sent'], customerEventHandler)
eventHandlerRegistry.register(['quality_check_required', 'quality_check_completed'], qualityCheckEventHandler)
eventHandlerRegistry.register(['system_maintenance', 'system_alert', 'backup_completed', 'backup_failed'], systemEventHandler)
