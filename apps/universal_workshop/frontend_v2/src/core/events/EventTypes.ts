/**
 * Event Types - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Event System Enhancement
 *
 * Comprehensive event type definitions for the workshop management system
 * with Arabic support and Omani cultural considerations.
 */

// Base event types supported by the system
export type WorkshopEventType =
    | 'service_order_updated'
    | 'service_bay_assigned'
    | 'technician_clocked_in'
    | 'technician_clocked_out'
    | 'technician_status_changed'
    | 'parts_inventory_low'
    | 'parts_received'
    | 'parts_ordered'
    | 'customer_arrived'
    | 'customer_notification_sent'
    | 'service_started'
    | 'service_paused'
    | 'service_resumed'
    | 'service_completed'
    | 'quality_check_required'
    | 'quality_check_completed'
    | 'invoice_generated'
    | 'payment_received'
    | 'payment_failed'
    | 'vehicle_vin_decoded'
    | 'vehicle_inspection_completed'
    | 'system_maintenance'
    | 'system_alert'
    | 'backup_completed'
    | 'backup_failed'

// Event priority levels
export type EventPriority = 'critical' | 'high' | 'medium' | 'low'

// Event source types
export type EventSource =
    | 'mobile_app'
    | 'desktop_app'
    | 'system'
    | 'external_api'
    | 'webhook'
    | 'scheduled_task'
    | 'technician_device'
    | 'customer_portal'
    | 'admin_dashboard'

// Entity types that can trigger events
export type EntityType =
    | 'service_order'
    | 'vehicle'
    | 'customer'
    | 'technician'
    | 'part'
    | 'inventory_item'
    | 'service_bay'
    | 'invoice'
    | 'payment'
    | 'quality_check'
    | 'system'

// Base event interface
export interface WorkshopEvent {
    id: string
    type: WorkshopEventType
    timestamp: Date
    source: EventSource
    priority: EventPriority
    entityType: EntityType
    entityId: string
    userId?: string
    workshopId: string
    data: Record<string, any>
    target?: string | string[] // Specific recipients
    requiresAck?: boolean
    ttl?: number // Time to live in seconds
    metadata?: EventMetadata
}

// Event metadata for tracking and analytics
export interface EventMetadata {
    sessionId?: string
    deviceId?: string
    platform?: 'mobile' | 'desktop' | 'web'
    browserInfo?: string
    location?: {
        latitude: number
        longitude: number
        accuracy: number
    }
    networkType?: 'wifi' | 'cellular' | 'ethernet'
    retryCount?: number
    processingTime?: number
    tags?: string[]
}

// Service order specific events
export interface ServiceOrderEvent extends WorkshopEvent {
    type: 'service_order_updated' | 'service_started' | 'service_completed' | 'service_paused' | 'service_resumed'
    entityType: 'service_order'
    data: {
        orderId: string
        customerId: string
        vehicleId: string
        technicianId?: string
        bayId?: string
        status: ServiceOrderStatus
        statusAr: string
        previousStatus?: ServiceOrderStatus
        estimatedCompletion?: Date
        actualCompletion?: Date
        services: ServiceItem[]
        parts: PartItem[]
        totalAmount: number
        notes?: string
        notesAr?: string
    }
}

// Technician specific events
export interface TechnicianEvent extends WorkshopEvent {
    type: 'technician_clocked_in' | 'technician_clocked_out' | 'technician_status_changed'
    entityType: 'technician'
    data: {
        technicianId: string
        name: string
        nameAr: string
        status: TechnicianStatus
        statusAr: string
        previousStatus?: TechnicianStatus
        currentServiceOrders: string[]
        assignedBayId?: string
        shiftStart?: Date
        shiftEnd?: Date
        clockInTime?: Date
        clockOutTime?: Date
        totalHoursWorked?: number
        efficiency?: number
    }
}

// Inventory/Parts specific events
export interface InventoryEvent extends WorkshopEvent {
    type: 'parts_inventory_low' | 'parts_received' | 'parts_ordered'
    entityType: 'part' | 'inventory_item'
    data: {
        partId: string
        partNumber: string
        partName: string
        partNameAr: string
        currentStock: number
        minimumStock: number
        reorderLevel: number
        supplier: string
        supplierAr: string
        unitPrice: number
        currency: 'OMR' | 'USD'
        location: string
        locationAr: string
        lastUpdated: Date
        orderQuantity?: number
        orderId?: string
        deliveryDate?: Date
    }
}

// Customer specific events
export interface CustomerEvent extends WorkshopEvent {
    type: 'customer_arrived' | 'customer_notification_sent'
    entityType: 'customer'
    data: {
        customerId: string
        name: string
        nameAr?: string
        phone: string
        email?: string
        vehicleId: string
        serviceOrderId: string
        arrivalTime?: Date
        notificationType?: 'sms' | 'email' | 'push' | 'whatsapp'
        notificationContent?: string
        notificationContentAr?: string
        preferredLanguage: 'ar' | 'en'
        communicationHistory: CommunicationRecord[]
    }
}

// Quality check events
export interface QualityCheckEvent extends WorkshopEvent {
    type: 'quality_check_required' | 'quality_check_completed'
    entityType: 'quality_check'
    data: {
        checkId: string
        serviceOrderId: string
        vehicleId: string
        technicianId: string
        checklistItems: QualityCheckItem[]
        overallStatus: 'pending' | 'in_progress' | 'passed' | 'failed'
        inspector?: string
        inspectorAr?: string
        completedAt?: Date
        notes?: string
        notesAr?: string
        photos?: string[]
        requiresRework?: boolean
        reworkInstructions?: string
        reworkInstructionsAr?: string
    }
}

// System events
export interface SystemEvent extends WorkshopEvent {
    type: 'system_maintenance' | 'system_alert' | 'backup_completed' | 'backup_failed'
    entityType: 'system'
    data: {
        alertType?: 'info' | 'warning' | 'error' | 'critical'
        title: string
        titleAr: string
        message: string
        messageAr: string
        affectedModules?: string[]
        scheduledDowntime?: {
            start: Date
            end: Date
            reason: string
            reasonAr: string
        }
        backupInfo?: {
            type: 'full' | 'incremental'
            size: number
            duration: number
            location: string
            success: boolean
            errorMessage?: string
        }
    }
}

// Supporting types
export type ServiceOrderStatus =
    | 'pending'
    | 'assigned'
    | 'in_progress'
    | 'quality_check'
    | 'completed'
    | 'delivered'
    | 'cancelled'
    | 'on_hold'

export type TechnicianStatus =
    | 'available'
    | 'busy'
    | 'break'
    | 'training'
    | 'offline'
    | 'sick_leave'
    | 'vacation'

export interface ServiceItem {
    id: string
    name: string
    nameAr: string
    description: string
    descriptionAr: string
    price: number
    currency: 'OMR' | 'USD'
    estimatedDuration: number // in minutes
    actualDuration?: number
    status: 'pending' | 'in_progress' | 'completed'
}

export interface PartItem {
    id: string
    partNumber: string
    name: string
    nameAr: string
    quantity: number
    unitPrice: number
    totalPrice: number
    currency: 'OMR' | 'USD'
    supplier: string
    supplierAr: string
    warrantyPeriod?: number // in months
    status: 'ordered' | 'received' | 'installed' | 'returned'
}

export interface QualityCheckItem {
    id: string
    category: string
    categoryAr: string
    description: string
    descriptionAr: string
    status: 'pending' | 'passed' | 'failed' | 'not_applicable'
    notes?: string
    notesAr?: string
    photos?: string[]
    checklistType: 'visual' | 'functional' | 'measurement' | 'test_drive'
}

export interface CommunicationRecord {
    id: string
    timestamp: Date
    type: 'sms' | 'email' | 'push' | 'whatsapp' | 'call'
    content: string
    contentAr?: string
    status: 'sent' | 'delivered' | 'read' | 'failed'
    recipientPhone?: string
    recipientEmail?: string
}

// Event handler types
export type EventHandler<T = WorkshopEvent> = (event: T) => void | Promise<void>

// Event filter types
export interface EventFilter {
    types?: WorkshopEventType[]
    sources?: EventSource[]
    priorities?: EventPriority[]
    entityTypes?: EntityType[]
    entityIds?: string[]
    userIds?: string[]
    workshopIds?: string[]
    since?: Date
    until?: Date
    tags?: string[]
}

// Event aggregation types
export interface EventAggregate {
    eventType: WorkshopEventType
    count: number
    firstOccurrence: Date
    lastOccurrence: Date
    averageProcessingTime: number
    sources: Record<EventSource, number>
    priorities: Record<EventPriority, number>
}

// Batch event processing
export interface EventBatch {
    id: string
    events: WorkshopEvent[]
    createdAt: Date
    processedAt?: Date
    status: 'pending' | 'processing' | 'completed' | 'failed'
    batchSize: number
    processingTime?: number
    errorCount?: number
    successCount?: number
}

// Real-time subscription configuration
export interface SubscriptionConfig {
    eventTypes: WorkshopEventType[]
    filter?: EventFilter
    batchSize?: number
    maxBatchTime?: number // ms
    retryAttempts?: number
    retryDelay?: number // ms
    deadLetterQueue?: boolean
    persistEvents?: boolean
    compressionEnabled?: boolean
}

// Event performance metrics
export interface EventMetrics {
    totalEvents: number
    eventsPerSecond: number
    avgProcessingTime: number
    maxProcessingTime: number
    minProcessingTime: number
    errorRate: number
    successRate: number
    queueSize: number
    retryCount: number
    lastEventTime: Date
    connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
    latency: number
    bandwidth: number
}

// Event store configuration
export interface EventStoreConfig {
    maxEvents: number
    maxAge: number // days
    compressionEnabled: boolean
    encryptionEnabled: boolean
    replicationEnabled: boolean
    backupEnabled: boolean
    retentionPolicy: {
        critical: number // days
        high: number
        medium: number
        low: number
    }
}

// Export utility types
export type EventTypeMap = {
    [K in WorkshopEventType]: K extends 'service_order_updated' | 'service_started' | 'service_completed' | 'service_paused' | 'service_resumed'
    ? ServiceOrderEvent
    : K extends 'technician_clocked_in' | 'technician_clocked_out' | 'technician_status_changed'
    ? TechnicianEvent
    : K extends 'parts_inventory_low' | 'parts_received' | 'parts_ordered'
    ? InventoryEvent
    : K extends 'customer_arrived' | 'customer_notification_sent'
    ? CustomerEvent
    : K extends 'quality_check_required' | 'quality_check_completed'
    ? QualityCheckEvent
    : K extends 'system_maintenance' | 'system_alert' | 'backup_completed' | 'backup_failed'
    ? SystemEvent
    : WorkshopEvent
}

export type EventByType<T extends WorkshopEventType> = EventTypeMap[T]
