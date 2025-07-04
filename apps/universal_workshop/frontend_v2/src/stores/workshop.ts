/**
 * Workshop Store - Universal Workshop Frontend V2
 * 
 * Pinia store for workshop state management with real-time synchronization,
 * offline support, and Arabic content handling.
 */

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useEventBus } from '@/composables/useEventBus'
import { getOfflineDatabase } from '@/core/offline/OfflineDatabase'
import type { WorkshopEvent } from '@/core/realtime/WorkshopEventBus'

export interface ServiceOrder {
  id: string
  customerName: string
  customerNameAr?: string
  vehicleMake: string
  vehicleModel: string
  vehicleYear: number
  plateNumber: string
  serviceType: string
  serviceTypeAr?: string
  status: 'draft' | 'open' | 'assigned' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'critical'
  estimatedDuration: number
  actualDuration?: number
  assignedTechnician?: string
  assignedBay?: string
  createdAt: number
  updatedAt: number
  progress: number
  notes: string
  notesAr?: string
  metadata: {
    userId: string
    arabicContent: boolean
    offline: boolean
    version: number
    lastSync?: number
  }
}

export interface ServiceBay {
  id: string
  name: string
  nameAr?: string
  status: 'available' | 'occupied' | 'maintenance' | 'reserved'
  capacity: number
  currentOrders: string[]
  equipment: string[]
  location: {
    zone: string
    position: string
  }
  lastUpdated: number
}

export interface Technician {
  id: string
  name: string
  nameAr?: string
  email: string
  phone: string
  skills: string[]
  currentAssignment?: string
  status: 'available' | 'busy' | 'break' | 'offline'
  workingHours: {
    start: string
    end: string
  }
  performance: {
    completedJobs: number
    averageTime: number
    customerRating: number
  }
  lastActivity: number
}

export interface WorkshopMetrics {
  activeOrders: number
  completedToday: number
  averageCompletionTime: number
  bayUtilization: number
  technicianUtilization: number
  customerSatisfaction: number
  revenue: {
    today: number
    thisWeek: number
    thisMonth: number
  }
}

export interface ConflictItem {
  id: string
  type: 'service_order' | 'bay' | 'technician'
  entityId: string
  clientVersion: any
  serverVersion: any
  timestamp: number
  autoResolvable: boolean
}

export const useWorkshopStore = defineStore('workshop', () => {
  // State
  const serviceOrders = ref<Map<string, ServiceOrder>>(new Map())
  const serviceBays = ref<Map<string, ServiceBay>>(new Map())
  const technicians = ref<Map<string, Technician>>(new Map())
  const metrics = ref<WorkshopMetrics>({
    activeOrders: 0,
    completedToday: 0,
    averageCompletionTime: 0,
    bayUtilization: 0,
    technicianUtilization: 0,
    customerSatisfaction: 0,
    revenue: { today: 0, thisWeek: 0, thisMonth: 0 }
  })

  const isLoading = ref(false)
  const lastSyncTime = ref<number | null>(null)
  const isOnline = ref(navigator.onLine)
  const conflicts = ref<ConflictItem[]>([])
  const pendingChanges = ref<Map<string, any>>(new Map())

  // Real-time event bus
  const eventBus = useEventBus({ autoConnect: true })
  const offlineDB = getOfflineDatabase()

  // Computed
  const activeServiceOrders = computed(() => 
    Array.from(serviceOrders.value.values()).filter(order => 
      ['open', 'assigned', 'in_progress'].includes(order.status)
    )
  )

  const availableBays = computed(() =>
    Array.from(serviceBays.value.values()).filter(bay => bay.status === 'available')
  )

  const availableTechnicians = computed(() =>
    Array.from(technicians.value.values()).filter(tech => tech.status === 'available')
  )

  const busyTechnicians = computed(() =>
    Array.from(technicians.value.values()).filter(tech => tech.status === 'busy')
  )

  const totalOrders = computed(() => serviceOrders.value.size)
  const totalBays = computed(() => serviceBays.value.size)
  const totalTechnicians = computed(() => technicians.value.size)

  const hasConflicts = computed(() => conflicts.value.length > 0)
  const hasPendingChanges = computed(() => pendingChanges.value.size > 0)

  // Actions

  /**
   * Initialize workshop store
   */
  async function initialize(): Promise<void> {
    isLoading.value = true

    try {
      // Initialize offline database
      await offlineDB.initialize()

      // Load cached data first
      await loadCachedData()

      // Setup real-time subscriptions
      setupRealTimeSync()

      // Load fresh data if online
      if (isOnline.value) {
        await syncWithServer()
      }

      console.log('✅ Workshop store initialized')
    } catch (error) {
      console.error('❌ Failed to initialize workshop store:', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load cached data from offline database
   */
  async function loadCachedData(): Promise<void> {
    try {
      // Load service orders
      const cachedOrders = await offlineDB.getEntitiesByType('service_order')
      cachedOrders.forEach(entity => {
        serviceOrders.value.set(entity.id, entity.data)
      })

      // Load service bays
      const cachedBays = await offlineDB.getEntitiesByType('service_bay')
      cachedBays.forEach(entity => {
        serviceBays.value.set(entity.id, entity.data)
      })

      // Load technicians
      const cachedTechnicians = await offlineDB.getEntitiesByType('technician')
      cachedTechnicians.forEach(entity => {
        technicians.value.set(entity.id, entity.data)
      })

      console.log('📦 Cached data loaded')
    } catch (error) {
      console.error('❌ Failed to load cached data:', error)
    }
  }

  /**
   * Setup real-time synchronization
   */
  function setupRealTimeSync(): void {
    // Service order events
    eventBus.subscribe('service_order_updated', handleServiceOrderUpdate)
    eventBus.subscribe('service_order_created', handleServiceOrderCreate)
    eventBus.subscribe('service_order_deleted', handleServiceOrderDelete)

    // Bay events
    eventBus.subscribe('service_bay_assigned', handleBayAssignment)
    eventBus.subscribe('service_bay_freed', handleBayFreed)

    // Technician events
    eventBus.subscribe('technician_assigned', handleTechnicianAssignment)
    eventBus.subscribe('technician_clocked_in', handleTechnicianClockIn)
    eventBus.subscribe('technician_clocked_out', handleTechnicianClockOut)

    // Connection events
    eventBus.subscribe('online', handleOnline)
    eventBus.subscribe('offline', handleOffline)

    console.log('🔄 Real-time sync setup complete')
  }

  /**
   * Sync with server
   */
  async function syncWithServer(): Promise<void> {
    if (!isOnline.value) return

    try {
      isLoading.value = true

      // Get fresh data from server
      const response = await fetch('/api/workshop/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lastSync: lastSyncTime.value,
          entities: ['service_orders', 'service_bays', 'technicians']
        })
      })

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`)
      }

      const syncData = await response.json()

      // Process updates
      await processSyncUpdates(syncData)

      // Update last sync time
      lastSyncTime.value = Date.now()
      await offlineDB.storeSetting('lastSyncTime', lastSyncTime.value)

      console.log('✅ Server sync completed')
    } catch (error) {
      console.error('❌ Server sync failed:', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Process sync updates from server
   */
  async function processSyncUpdates(syncData: any): Promise<void> {
    const { serviceOrders: serverOrders, serviceBays: serverBays, technicians: serverTechs, conflicts: serverConflicts } = syncData

    // Process service orders
    if (serverOrders) {
      for (const orderData of serverOrders) {
        await updateServiceOrderWithConflictCheck(orderData)
      }
    }

    // Process service bays
    if (serverBays) {
      for (const bayData of serverBays) {
        await updateServiceBayWithConflictCheck(bayData)
      }
    }

    // Process technicians
    if (serverTechs) {
      for (const techData of serverTechs) {
        await updateTechnicianWithConflictCheck(techData)
      }
    }

    // Handle conflicts
    if (serverConflicts && serverConflicts.length > 0) {
      conflicts.value.push(...serverConflicts)
    }
  }

  /**
   * Update service order with conflict detection
   */
  async function updateServiceOrderWithConflictCheck(serverData: ServiceOrder): Promise<void> {
    const localOrder = serviceOrders.value.get(serverData.id)

    if (localOrder && localOrder.metadata.version !== serverData.metadata.version) {
      // Version conflict detected
      const conflict: ConflictItem = {
        id: `conflict-${Date.now()}`,
        type: 'service_order',
        entityId: serverData.id,
        clientVersion: localOrder,
        serverVersion: serverData,
        timestamp: Date.now(),
        autoResolvable: canAutoResolveServiceOrder(localOrder, serverData)
      }

      if (conflict.autoResolvable) {
        const resolved = autoResolveServiceOrder(localOrder, serverData)
        await updateServiceOrder(resolved.id, resolved)
      } else {
        conflicts.value.push(conflict)
      }
    } else {
      // No conflict, update normally
      await updateServiceOrder(serverData.id, serverData)
    }
  }

  /**
   * Create new service order
   */
  async function createServiceOrder(orderData: Partial<ServiceOrder>): Promise<string> {
    const orderId = orderData.id || generateId()
    const now = Date.now()

    const order: ServiceOrder = {
      id: orderId,
      customerName: orderData.customerName || '',
      vehicleMake: orderData.vehicleMake || '',
      vehicleModel: orderData.vehicleModel || '',
      vehicleYear: orderData.vehicleYear || new Date().getFullYear(),
      plateNumber: orderData.plateNumber || '',
      serviceType: orderData.serviceType || '',
      status: 'draft',
      priority: orderData.priority || 'medium',
      estimatedDuration: orderData.estimatedDuration || 120,
      createdAt: now,
      updatedAt: now,
      progress: 0,
      notes: orderData.notes || '',
      metadata: {
        userId: getCurrentUserId(),
        arabicContent: detectArabicContent(orderData),
        offline: !isOnline.value,
        version: 1
      },
      ...orderData
    }

    // Store locally
    serviceOrders.value.set(orderId, order)

    // Cache offline
    await cacheEntity('service_order', orderId, order)

    // Sync to server if online
    if (isOnline.value) {
      await syncServiceOrderToServer(order)
    } else {
      // Queue for sync
      await queuePendingChange('create', 'service_order', orderId, order)
    }

    // Broadcast event
    eventBus.broadcast({
      type: 'service_order_created',
      data: {
        entityType: 'service_order',
        entityId: orderId,
        currentState: order,
        metadata: {
          title: `New Service Order ${orderId}`,
          titleAr: `أمر خدمة جديد ${orderId}`,
          priority: 'medium',
          requiresAction: false
        }
      }
    })

    return orderId
  }

  /**
   * Update service order
   */
  async function updateServiceOrder(orderId: string, updates: Partial<ServiceOrder>): Promise<void> {
    const existingOrder = serviceOrders.value.get(orderId)
    if (!existingOrder) {
      throw new Error(`Service order ${orderId} not found`)
    }

    const updatedOrder: ServiceOrder = {
      ...existingOrder,
      ...updates,
      updatedAt: Date.now(),
      metadata: {
        ...existingOrder.metadata,
        version: existingOrder.metadata.version + 1,
        arabicContent: detectArabicContent(updates) || existingOrder.metadata.arabicContent
      }
    }

    // Store locally
    serviceOrders.value.set(orderId, updatedOrder)

    // Cache offline
    await cacheEntity('service_order', orderId, updatedOrder)

    // Sync to server if online
    if (isOnline.value) {
      await syncServiceOrderToServer(updatedOrder)
    } else {
      // Queue for sync
      await queuePendingChange('update', 'service_order', orderId, updatedOrder)
    }

    // Broadcast event
    eventBus.broadcast({
      type: 'service_order_updated',
      data: {
        entityType: 'service_order',
        entityId: orderId,
        previousState: existingOrder,
        currentState: updatedOrder,
        metadata: {
          title: `Service Order ${orderId} Updated`,
          titleAr: `تم تحديث أمر الخدمة ${orderId}`,
          priority: updatedOrder.priority === 'critical' ? 'high' : 'medium',
          requiresAction: updatedOrder.status === 'completed'
        }
      }
    })
  }

  /**
   * Delete service order
   */
  async function deleteServiceOrder(orderId: string): Promise<void> {
    const order = serviceOrders.value.get(orderId)
    if (!order) return

    // Remove locally
    serviceOrders.value.delete(orderId)

    // Remove from offline cache
    await offlineDB.deleteEntity(orderId)

    // Sync deletion to server if online
    if (isOnline.value) {
      await syncServiceOrderDeletion(orderId)
    } else {
      // Queue for sync
      await queuePendingChange('delete', 'service_order', orderId, null)
    }

    // Broadcast event
    eventBus.broadcast({
      type: 'service_order_deleted',
      data: {
        entityType: 'service_order',
        entityId: orderId,
        previousState: order,
        metadata: {
          title: `Service Order ${orderId} Deleted`,
          titleAr: `تم حذف أمر الخدمة ${orderId}`,
          priority: 'medium',
          requiresAction: false
        }
      }
    })
  }

  /**
   * Assign technician to service order
   */
  async function assignTechnician(orderId: string, technicianId: string): Promise<void> {
    const order = serviceOrders.value.get(orderId)
    const technician = technicians.value.get(technicianId)

    if (!order || !technician) {
      throw new Error('Service order or technician not found')
    }

    // Update order
    await updateServiceOrder(orderId, {
      assignedTechnician: technicianId,
      status: 'assigned'
    })

    // Update technician
    await updateTechnician(technicianId, {
      currentAssignment: orderId,
      status: 'busy'
    })
  }

  /**
   * Assign bay to service order
   */
  async function assignBay(orderId: string, bayId: string): Promise<void> {
    const order = serviceOrders.value.get(orderId)
    const bay = serviceBays.value.get(bayId)

    if (!order || !bay) {
      throw new Error('Service order or bay not found')
    }

    // Update order
    await updateServiceOrder(orderId, {
      assignedBay: bayId
    })

    // Update bay
    await updateServiceBay(bayId, {
      status: 'occupied',
      currentOrders: [...bay.currentOrders, orderId]
    })
  }

  /**
   * Update service bay
   */
  async function updateServiceBay(bayId: string, updates: Partial<ServiceBay>): Promise<void> {
    const existingBay = serviceBays.value.get(bayId)
    if (!existingBay) return

    const updatedBay: ServiceBay = {
      ...existingBay,
      ...updates,
      lastUpdated: Date.now()
    }

    serviceBays.value.set(bayId, updatedBay)
    await cacheEntity('service_bay', bayId, updatedBay)

    if (isOnline.value) {
      await syncServiceBayToServer(updatedBay)
    }
  }

  /**
   * Update technician
   */
  async function updateTechnician(techId: string, updates: Partial<Technician>): Promise<void> {
    const existingTech = technicians.value.get(techId)
    if (!existingTech) return

    const updatedTech: Technician = {
      ...existingTech,
      ...updates,
      lastActivity: Date.now()
    }

    technicians.value.set(techId, updatedTech)
    await cacheEntity('technician', techId, updatedTech)

    if (isOnline.value) {
      await syncTechnicianToServer(updatedTech)
    }
  }

  /**
   * Resolve conflict manually
   */
  async function resolveConflict(conflictId: string, resolution: 'client' | 'server' | 'merge', mergedData?: any): Promise<void> {
    const conflict = conflicts.value.find(c => c.id === conflictId)
    if (!conflict) return

    let resolvedData: any

    switch (resolution) {
      case 'client':
        resolvedData = conflict.clientVersion
        break
      case 'server':
        resolvedData = conflict.serverVersion
        break
      case 'merge':
        resolvedData = mergedData || mergeConflictData(conflict.clientVersion, conflict.serverVersion)
        break
    }

    // Apply resolution
    switch (conflict.type) {
      case 'service_order':
        await updateServiceOrder(conflict.entityId, resolvedData)
        break
      case 'bay':
        await updateServiceBay(conflict.entityId, resolvedData)
        break
      case 'technician':
        await updateTechnician(conflict.entityId, resolvedData)
        break
    }

    // Remove conflict
    conflicts.value = conflicts.value.filter(c => c.id !== conflictId)
  }

  /**
   * Event handlers
   */
  function handleServiceOrderUpdate(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateServiceOrder(entityId, currentState)
  }

  function handleServiceOrderCreate(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    serviceOrders.value.set(entityId, currentState)
    cacheEntity('service_order', entityId, currentState)
  }

  function handleServiceOrderDelete(event: WorkshopEvent): void {
    const { entityId } = event.data
    serviceOrders.value.delete(entityId)
    offlineDB.deleteEntity(entityId)
  }

  function handleBayAssignment(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateServiceBay(entityId, currentState)
  }

  function handleBayFreed(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateServiceBay(entityId, currentState)
  }

  function handleTechnicianAssignment(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateTechnician(entityId, currentState)
  }

  function handleTechnicianClockIn(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateTechnician(entityId, { ...currentState, status: 'available' })
  }

  function handleTechnicianClockOut(event: WorkshopEvent): void {
    const { entityId, currentState } = event.data
    updateTechnician(entityId, { ...currentState, status: 'offline' })
  }

  function handleOnline(): void {
    isOnline.value = true
    syncWithServer()
    processPendingChanges()
  }

  function handleOffline(): void {
    isOnline.value = false
  }

  /**
   * Utility functions
   */
  function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
  }

  function getCurrentUserId(): string {
    return window.frappe?.boot?.user?.name || 'anonymous'
  }

  function detectArabicContent(data: any): boolean {
    const text = JSON.stringify(data)
    return /[\u0600-\u06FF]/.test(text)
  }

  async function cacheEntity(type: string, id: string, data: any): Promise<void> {
    await offlineDB.storeEntity({
      id,
      type,
      data,
      metadata: {
        userId: getCurrentUserId(),
        arabicContent: detectArabicContent(data)
      }
    })
  }

  async function queuePendingChange(operation: string, type: string, id: string, data: any): Promise<void> {
    const changeId = generateId()
    pendingChanges.value.set(changeId, { operation, type, id, data, timestamp: Date.now() })

    await offlineDB.queueSyncOperation({
      id: changeId,
      type: operation as any,
      entityType: type,
      entityId: id,
      operation: data
    })
  }

  async function processPendingChanges(): Promise<void> {
    const pendingOps = await offlineDB.getPendingSyncOperations()

    for (const op of pendingOps) {
      try {
        await syncOperationToServer(op)
        await offlineDB.removeSyncOperation(op.id)
        pendingChanges.value.delete(op.id)
      } catch (error) {
        console.error('Failed to sync operation:', error)
        await offlineDB.updateSyncOperation(op.id, {
          retries: op.retries + 1,
          lastError: (error as Error).message
        })
      }
    }
  }

  function canAutoResolveServiceOrder(client: ServiceOrder, server: ServiceOrder): boolean {
    // Simple auto-resolution rules
    return Math.abs(client.updatedAt - server.updatedAt) < 60000 // 1 minute
  }

  function autoResolveServiceOrder(client: ServiceOrder, server: ServiceOrder): ServiceOrder {
    // Use server version but keep client notes if newer
    return {
      ...server,
      notes: client.updatedAt > server.updatedAt ? client.notes : server.notes,
      metadata: {
        ...server.metadata,
        version: Math.max(client.metadata.version, server.metadata.version) + 1
      }
    }
  }

  function mergeConflictData(client: any, server: any): any {
    // Simple merge strategy - can be enhanced
    return {
      ...server,
      ...client,
      updatedAt: Date.now(),
      metadata: {
        ...server.metadata,
        ...client.metadata,
        version: Math.max(client.metadata?.version || 0, server.metadata?.version || 0) + 1
      }
    }
  }

  // API sync functions (simplified)
  async function syncServiceOrderToServer(order: ServiceOrder): Promise<void> {
    await fetch(`/api/service_orders/${order.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    })
  }

  async function syncServiceOrderDeletion(orderId: string): Promise<void> {
    await fetch(`/api/service_orders/${orderId}`, { method: 'DELETE' })
  }

  async function syncServiceBayToServer(bay: ServiceBay): Promise<void> {
    await fetch(`/api/service_bays/${bay.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bay)
    })
  }

  async function syncTechnicianToServer(tech: Technician): Promise<void> {
    await fetch(`/api/technicians/${tech.id}`, {
      method: 'PUT', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tech)
    })
  }

  async function syncOperationToServer(operation: any): Promise<void> {
    const endpoint = `/api/${operation.entityType}/${operation.entityId}`
    await fetch(endpoint, {
      method: operation.type === 'delete' ? 'DELETE' : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: operation.type !== 'delete' ? JSON.stringify(operation.operation) : undefined
    })
  }

  // Return store interface
  return {
    // State
    serviceOrders: readonly(serviceOrders),
    serviceBays: readonly(serviceBays),
    technicians: readonly(technicians),
    metrics: readonly(metrics),
    isLoading: readonly(isLoading),
    isOnline: readonly(isOnline),
    conflicts: readonly(conflicts),
    lastSyncTime: readonly(lastSyncTime),

    // Computed
    activeServiceOrders,
    availableBays,
    availableTechnicians,
    busyTechnicians,
    totalOrders,
    totalBays,
    totalTechnicians,
    hasConflicts,
    hasPendingChanges,

    // Actions
    initialize,
    syncWithServer,
    createServiceOrder,
    updateServiceOrder,
    deleteServiceOrder,
    assignTechnician,
    assignBay,
    updateServiceBay,
    updateTechnician,
    resolveConflict
  }
})

export default useWorkshopStore