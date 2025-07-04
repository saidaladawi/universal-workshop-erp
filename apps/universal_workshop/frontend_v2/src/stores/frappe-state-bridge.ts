/**
 * Frappe State Bridge - Frontend V2
 * 
 * Bidirectional state synchronization between traditional Frappe and Vue.js stores
 * Handles real-time data sync, conflict resolution, and state management
 */

import { defineStore } from 'pinia'
import { ref, computed, watch, reactive } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import { FrappeAdapter } from '../api/frappe-adapter'

// Types
export interface SyncState {
  lastSync: Record<string, string>
  syncInProgress: Record<string, boolean>
  syncErrors: Record<string, string>
  connectionStatus: 'connected' | 'disconnected' | 'syncing'
}

export interface ConflictResolution {
  strategy: 'server_wins' | 'client_wins' | 'manual' | 'merge'
  resolver?: (serverData: any, clientData: any) => any
}

export interface SyncOptions {
  immediate?: boolean
  interval?: number
  conflictResolution?: ConflictResolution
  fields?: string[]
  batchSize?: number
}

// Main State Bridge Store
export const useFrappeStateBridge = defineStore('frappeStateBridge', () => {
  // State
  const syncState: Ref<SyncState> = ref({
    lastSync: {},
    syncInProgress: {},
    syncErrors: {},
    connectionStatus: 'disconnected'
  })
  
  const bridgedData = reactive({
    serviceOrders: [],
    customers: [],
    vehicles: [],
    technicians: [],
    workshopProfile: null,
    notifications: [],
    realTimeUpdates: {}
  })
  
  const pendingChanges = reactive({
    serviceOrders: new Map(),
    customers: new Map(),
    vehicles: new Map(),
    technicians: new Map(),
    workshopProfile: new Map()
  })
  
  const subscriptions = new Map<string, () => void>()
  const adapter = FrappeAdapter.getInstance()
  
  // Computed
  const isConnected = computed(() => syncState.value.connectionStatus === 'connected')
  const hasErrors = computed(() => Object.keys(syncState.value.syncErrors).length > 0)
  const syncProgress = computed(() => {
    const inProgress = Object.values(syncState.value.syncInProgress)
    return inProgress.filter(Boolean).length / Math.max(inProgress.length, 1)
  })
  
  // Core Sync Methods
  async function initializeBridge(options: SyncOptions = {}): Promise<void> {
    try {
      syncState.value.connectionStatus = 'syncing'
      
      // Check Frappe connection
      if (!adapter.connected.value) {
        await adapter.refresh()
      }
      
      if (adapter.connected.value) {
        syncState.value.connectionStatus = 'connected'
        
        // Initial data sync
        if (options.immediate !== false) {
          await syncAllData(options)
        }
        
        // Setup real-time subscriptions
        await setupRealTimeSync()
        
        // Setup periodic sync if interval specified
        if (options.interval) {
          setupPeriodicSync(options.interval, options)
        }
        
        console.log('✅ Frappe State Bridge initialized')
      } else {
        throw new Error('Failed to connect to Frappe')
      }
    } catch (error) {
      syncState.value.connectionStatus = 'disconnected'
      console.error('❌ Failed to initialize Frappe State Bridge:', error)
      throw error
    }
  }
  
  async function syncAllData(options: SyncOptions = {}): Promise<void> {
    const dataTypes = ['serviceOrders', 'customers', 'vehicles', 'technicians', 'workshopProfile']
    
    try {
      // Sync all data types in parallel
      await Promise.all(
        dataTypes.map(dataType => syncDataType(dataType, options))
      )
      
      console.log('✅ Full data sync completed')
    } catch (error) {
      console.error('❌ Full data sync failed:', error)
      throw error
    }
  }
  
  async function syncDataType(
    dataType: string, 
    options: SyncOptions = {}
  ): Promise<void> {
    if (syncState.value.syncInProgress[dataType]) {
      console.log(`⏭️ Sync already in progress for ${dataType}`)
      return
    }
    
    try {
      syncState.value.syncInProgress[dataType] = true
      delete syncState.value.syncErrors[dataType]
      
      const lastSync = syncState.value.lastSync[dataType]
      const response = await adapter.syncWorkshopData(
        convertDataTypeName(dataType), 
        lastSync
      )
      
      if (response?.records) {
        // Apply data with conflict resolution
        await applyServerData(dataType, response.records, options.conflictResolution)
        
        // Update last sync time
        syncState.value.lastSync[dataType] = response.last_sync
        
        console.log(`✅ Synced ${response.count} ${dataType} records`)
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sync failed'
      syncState.value.syncErrors[dataType] = errorMessage
      console.error(`❌ Failed to sync ${dataType}:`, error)
      throw error
      
    } finally {
      syncState.value.syncInProgress[dataType] = false
    }
  }
  
  async function applyServerData(
    dataType: string,
    serverRecords: any[],
    conflictResolution: ConflictResolution = { strategy: 'server_wins' }
  ): Promise<void> {
    const clientData = bridgedData[dataType as keyof typeof bridgedData]
    const pendingData = pendingChanges[dataType as keyof typeof pendingChanges]
    
    if (Array.isArray(clientData)) {
      // Handle array data (most DocTypes)
      const mergedData = await mergeArrayData(
        clientData,
        serverRecords,
        pendingData as Map<string, any>,
        conflictResolution
      )
      
      // Update reactive data
      ;(bridgedData[dataType as keyof typeof bridgedData] as any[]).splice(
        0, 
        clientData.length, 
        ...mergedData
      )
      
    } else if (dataType === 'workshopProfile' && serverRecords.length > 0) {
      // Handle single object data (Workshop Profile)
      const serverProfile = serverRecords[0]
      const clientProfile = bridgedData.workshopProfile
      
      if (conflictResolution.strategy === 'server_wins' || !clientProfile) {
        bridgedData.workshopProfile = serverProfile
      } else if (conflictResolution.strategy === 'merge') {
        bridgedData.workshopProfile = { ...clientProfile, ...serverProfile }
      }
      // For 'client_wins', keep existing data
    }
  }
  
  async function mergeArrayData(
    clientData: any[],
    serverData: any[],
    pendingChanges: Map<string, any>,
    conflictResolution: ConflictResolution
  ): Promise<any[]> {
    const merged = new Map<string, any>()
    
    // Start with client data
    clientData.forEach(item => {
      merged.set(item.name, item)
    })
    
    // Apply server updates
    for (const serverItem of serverData) {
      const clientItem = merged.get(serverItem.name)
      const pendingItem = pendingChanges.get(serverItem.name)
      
      if (!clientItem) {
        // New item from server
        merged.set(serverItem.name, serverItem)
        
      } else if (pendingItem) {
        // Conflict resolution needed
        const resolvedItem = await resolveConflict(
          serverItem,
          clientItem,
          pendingItem,
          conflictResolution
        )
        merged.set(serverItem.name, resolvedItem)
        
        // Remove from pending changes
        pendingChanges.delete(serverItem.name)
        
      } else {
        // Simple server update
        merged.set(serverItem.name, serverItem)
      }
    }
    
    return Array.from(merged.values())
  }
  
  async function resolveConflict(
    serverData: any,
    clientData: any,
    pendingData: any,
    conflictResolution: ConflictResolution
  ): Promise<any> {
    switch (conflictResolution.strategy) {
      case 'server_wins':
        return serverData
        
      case 'client_wins':
        return pendingData || clientData
        
      case 'merge':
        return { ...serverData, ...pendingData }
        
      case 'manual':
        if (conflictResolution.resolver) {
          return await conflictResolution.resolver(serverData, pendingData || clientData)
        }
        // Fallback to server wins
        return serverData
        
      default:
        return serverData
    }
  }
  
  // Real-time Synchronization
  async function setupRealTimeSync(): Promise<void> {
    try {
      const dataTypes = ['Service Order', 'Customer', 'Vehicle', 'Technician']
      
      for (const doctype of dataTypes) {
        const unsubscribe = await adapter.subscribeToUpdates(doctype, (data) => {
          handleRealTimeUpdate(doctype, data)
        })
        
        subscriptions.set(doctype, unsubscribe)
      }
      
      console.log('✅ Real-time sync enabled')
    } catch (error) {
      console.warn('⚠️ Real-time sync not available:', error)
    }
  }
  
  function handleRealTimeUpdate(doctype: string, updateData: any): void {
    const dataType = convertDoctypeToDataType(doctype)
    const currentData = bridgedData[dataType as keyof typeof bridgedData] as any[]
    
    if (Array.isArray(currentData)) {
      const index = currentData.findIndex(item => item.name === updateData.name)
      
      if (updateData._action === 'delete') {
        if (index !== -1) {
          currentData.splice(index, 1)
        }
      } else if (index !== -1) {
        // Update existing
        currentData[index] = { ...currentData[index], ...updateData }
      } else {
        // Add new
        currentData.push(updateData)
      }
      
      // Store real-time update info
      bridgedData.realTimeUpdates[updateData.name] = {
        doctype,
        action: updateData._action || 'update',
        timestamp: Date.now()
      }
    }
  }
  
  // Data Modification Methods
  function markAsChanged(dataType: string, itemName: string, changes: any): void {
    const pendingMap = pendingChanges[dataType as keyof typeof pendingChanges] as Map<string, any>
    
    if (pendingMap) {
      const existing = pendingMap.get(itemName) || {}
      pendingMap.set(itemName, { ...existing, ...changes })
    }
  }
  
  async function pushChangesToServer(
    dataType: string, 
    itemName?: string
  ): Promise<void> {
    const pendingMap = pendingChanges[dataType as keyof typeof pendingChanges] as Map<string, any>
    
    if (!pendingMap || pendingMap.size === 0) {
      return
    }
    
    const itemsToPush = itemName 
      ? [[itemName, pendingMap.get(itemName)]]
      : Array.from(pendingMap.entries())
    
    for (const [name, changes] of itemsToPush) {
      if (changes) {
        try {
          await adapter.saveDoc({ doc: { ...changes, name } })
          pendingMap.delete(name)
          console.log(`✅ Pushed changes for ${dataType}:${name}`)
        } catch (error) {
          console.error(`❌ Failed to push changes for ${dataType}:${name}:`, error)
        }
      }
    }
  }
  
  // Search and Filter Methods
  function searchInBridgedData(
    dataType: string,
    searchText: string,
    searchFields: string[] = ['name']
  ): any[] {
    const data = bridgedData[dataType as keyof typeof bridgedData] as any[]
    
    if (!Array.isArray(data) || !searchText.trim()) {
      return data || []
    }
    
    const searchLower = searchText.toLowerCase()
    
    return data.filter(item => {
      return searchFields.some(field => {
        const value = item[field] || item[`${field}_ar`] || ''
        return value.toString().toLowerCase().includes(searchLower)
      })
    })
  }
  
  function filterBridgedData(
    dataType: string,
    filters: Record<string, any>
  ): any[] {
    const data = bridgedData[dataType as keyof typeof bridgedData] as any[]
    
    if (!Array.isArray(data) || Object.keys(filters).length === 0) {
      return data || []
    }
    
    return data.filter(item => {
      return Object.entries(filters).every(([field, value]) => {
        if (Array.isArray(value)) {
          return value.includes(item[field])
        } else if (typeof value === 'object' && value !== null) {
          // Range or operator filters
          if (value.$gte !== undefined && item[field] < value.$gte) return false
          if (value.$lte !== undefined && item[field] > value.$lte) return false
          if (value.$like !== undefined && !item[field]?.includes(value.$like)) return false
          return true
        } else {
          return item[field] === value
        }
      })
    })
  }
  
  // Utility Functions
  function convertDataTypeName(dataType: string): string {
    const mapping: Record<string, string> = {
      serviceOrders: 'service_orders',
      workshopProfile: 'workshop_profile'
    }
    return mapping[dataType] || dataType.toLowerCase()
  }
  
  function convertDoctypeToDataType(doctype: string): string {
    const mapping: Record<string, string> = {
      'Service Order': 'serviceOrders',
      'Customer': 'customers',
      'Vehicle': 'vehicles',
      'Technician': 'technicians',
      'Workshop Profile': 'workshopProfile'
    }
    return mapping[doctype] || doctype.toLowerCase()
  }
  
  function setupPeriodicSync(interval: number, options: SyncOptions): void {
    setInterval(async () => {
      if (syncState.value.connectionStatus === 'connected') {
        try {
          await syncAllData(options)
        } catch (error) {
          console.error('Periodic sync failed:', error)
        }
      }
    }, interval)
  }
  
  // Cleanup
  function cleanup(): void {
    // Unsubscribe from real-time updates
    for (const unsubscribe of subscriptions.values()) {
      unsubscribe()
    }
    subscriptions.clear()
    
    // Reset state
    syncState.value = {
      lastSync: {},
      syncInProgress: {},
      syncErrors: {},
      connectionStatus: 'disconnected'
    }
    
    console.log('🧹 Frappe State Bridge cleaned up')
  }
  
  // Return store interface
  return {
    // State
    syncState: readonly(syncState),
    bridgedData: readonly(bridgedData),
    pendingChanges: readonly(pendingChanges),
    
    // Computed
    isConnected,
    hasErrors,
    syncProgress,
    
    // Methods
    initializeBridge,
    syncAllData,
    syncDataType,
    markAsChanged,
    pushChangesToServer,
    searchInBridgedData,
    filterBridgedData,
    cleanup,
    
    // Direct data access helpers
    getServiceOrders: () => bridgedData.serviceOrders,
    getCustomers: () => bridgedData.customers,
    getVehicles: () => bridgedData.vehicles,
    getTechnicians: () => bridgedData.technicians,
    getWorkshopProfile: () => bridgedData.workshopProfile,
    
    // Change tracking
    hasPendingChanges: (dataType: string) => {
      const pendingMap = pendingChanges[dataType as keyof typeof pendingChanges] as Map<string, any>
      return pendingMap ? pendingMap.size > 0 : false
    },
    
    getPendingChanges: (dataType: string) => {
      const pendingMap = pendingChanges[dataType as keyof typeof pendingChanges] as Map<string, any>
      return pendingMap ? Array.from(pendingMap.entries()) : []
    }
  }
})

// Export types for external use
export type FrappeStateBridge = ReturnType<typeof useFrappeStateBridge>