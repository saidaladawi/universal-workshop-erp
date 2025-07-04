/**
 * Event Bus Composable - Universal Workshop Frontend V2
 * 
 * Vue 3 composable for workshop events with Arabic support
 */

import { ref, onMounted, onUnmounted, computed, readonly } from 'vue'
import { eventBus } from '@/core/events/UnifiedEventBus'
import type { WorkshopEvent, WorkshopEventType } from '@/core/events/EventTypes'

interface UseEventBusOptions {
  autoConnect?: boolean
  preferArabic?: boolean
  debug?: boolean
}

export function useEventBus(options: UseEventBusOptions = {}) {
  const {
    autoConnect = true,
    preferArabic = false,
    debug = false
  } = options

  // Reactive state from unified event bus
  const isConnected = eventBus.isConnected
  const recentEvents = ref<WorkshopEvent[]>([])
  const notifications = ref<any[]>([])

  /**
   * Subscribe to events
   */
  const subscribe = (
    eventType: WorkshopEventType | WorkshopEventType[],
    handler: (event: WorkshopEvent) => void,
    options: {
      filter?: (event: WorkshopEvent) => boolean
      once?: boolean
    } = {}
  ) => {
    return eventBus.subscribe(eventType, handler, options)
  }

  /**
   * Emit/broadcast events
   */
  const emit = async (event: Partial<WorkshopEvent>) => {
    return await eventBus.emit(event)
  }

  /**
   * Send notification
   */
  const notify = async (event: Partial<WorkshopEvent>) => {
    // Add notification to local array
    const notification = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      ...event,
      read: false
    }
    
    notifications.value.unshift(notification)
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      removeNotification(notification.id)
    }, 10000)

    return await emit(event)
  }

  /**
   * Get recent events
   */
  const getRecentEvents = (eventType?: WorkshopEventType, limit: number = 10) => {
    return eventBus.getHistory(eventType, limit)
  }

  /**
   * Remove notification
   */
  const removeNotification = (notificationId: string) => {
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  /**
   * Clear all notifications
   */
  const clearNotifications = () => {
    notifications.value = []
  }

  /**
   * Mark notification as read
   */
  const markNotificationRead = (notificationId: string) => {
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.read = true
    }
  }

  /**
   * Check for unread notifications
   */
  const hasUnreadNotifications = computed(() => {
    return notifications.value.some(n => !n.read)
  })

  /**
   * Get connection statistics
   */
  const getConnectionStats = () => {
    return eventBus.getMetrics()
  }

  // Subscribe to general events to track recent events
  let generalSubscription: (() => void) | null = null

  onMounted(() => {
    if (autoConnect) {
      // Subscribe to all events to track recent events
      generalSubscription = eventBus.subscribe(
        ['service_order_updated', 'service_started', 'service_completed', 'technician_status_changed', 'parts_inventory_low'] as WorkshopEventType[],
        (event: WorkshopEvent) => {
          recentEvents.value.unshift(event)
          
          // Keep only last 50 events
          if (recentEvents.value.length > 50) {
            recentEvents.value = recentEvents.value.slice(0, 50)
          }
        }
      )
    }
  })

  onUnmounted(() => {
    // Clean up subscription
    if (generalSubscription) {
      generalSubscription()
    }
  })

  return {
    // Connection
    isConnected,

    // Event handling
    subscribe,
    emit,
    notify,

    // Recent events
    recentEvents: readonly(recentEvents),
    getRecentEvents,

    // Notifications  
    notifications: readonly(notifications),
    hasUnreadNotifications,
    removeNotification,
    markNotificationRead,
    clearNotifications,

    // Utilities
    getConnectionStats
  }
}

// Specialized composables for specific use cases

/**
 * Service Order Events
 */
export function useServiceOrderEvents() {
  const { subscribe, emit } = useEventBus()

  const updateServiceOrderStatus = (serviceOrderId: string, status: string, notes?: string) => {
    return emit({
      type: 'service_order_updated',
      entityType: 'service_order',
      entityId: serviceOrderId,
      data: { status, notes }
    })
  }

  const startService = (serviceOrderId: string, technicianId: string) => {
    return emit({
      type: 'service_started',
      entityType: 'service_order',
      entityId: serviceOrderId,
      data: { technicianId, startTime: new Date() }
    })
  }

  const completeService = (serviceOrderId: string, results: any) => {
    return emit({
      type: 'service_completed',
      entityType: 'service_order',
      entityId: serviceOrderId,
      data: { results, completedTime: new Date() }
    })
  }

  return {
    subscribe,
    updateServiceOrderStatus,
    startService,
    completeService
  }
}

/**
 * Technician Events
 */
export function useTechnicianEvents() {
  const { subscribe, emit } = useEventBus()

  const updateTechnicianStatus = (technicianId: string, status: string) => {
    return emit({
      type: 'technician_status_changed',
      entityType: 'technician',
      entityId: technicianId,
      data: { status, timestamp: new Date() }
    })
  }

  return {
    subscribe,
    updateTechnicianStatus
  }
}

/**
 * Inventory Events
 */
export function useInventoryEvents() {
  const { subscribe, emit } = useEventBus()

  const updateInventory = (itemId: string, quantity: number) => {
    return emit({
      type: 'parts_received',
      entityType: 'inventory_item',
      entityId: itemId,
      data: { quantity, timestamp: new Date() }
    })
  }

  const alertLowStock = (itemId: string, currentQuantity: number, minQuantity: number) => {
    return emit({
      type: 'parts_inventory_low',
      entityType: 'inventory_item',
      entityId: itemId,
      priority: 'high',
      data: { currentQuantity, minQuantity, timestamp: new Date() }
    })
  }

  return {
    subscribe,
    updateInventory,
    alertLowStock
  }
}

export default useEventBus