/**
 * Sync Module Index - Universal Workshop Frontend V2
 * Phase 3: Sprint 3 Week 2 - Real-Time Synchronization
 * 
 * Centralized exports for the comprehensive synchronization system
 * with offline capability and Arabic-aware conflict resolution.
 */

// Main sync manager and conflict resolver
export * from './SyncManager'
export * from './ConflictResolver'

// Main exports for easy access
export { 
  syncManager,
  useSyncManager
} from './SyncManager'

export {
  conflictResolver,
  useConflictResolver
} from './ConflictResolver'

// Type exports for common usage
export type {
  SyncConfig,
  SyncOperation,
  SyncState,
  SyncMetrics,
  SyncOperationType,
  SyncStrategy,
  SyncStatus,
  EntityType
} from './SyncManager'

export type {
  SyncConflict,
  ConflictResolutionOption,
  ConflictComplexity,
  ConflictResolutionStrategy,
  ConflictResolutionResult,
  ArabicConflictContext,
  FieldConflict,
  MergeOperation
} from './ConflictResolver'

// Utility functions for common sync operations
import { syncManager } from './SyncManager'
import { conflictResolver } from './ConflictResolver'

/**
 * Quick helper to sync a service order
 */
export const syncServiceOrder = async (
  serviceOrderId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'service_order',
    serviceOrderId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'high'
    }
  )
}

/**
 * Quick helper to sync customer data
 */
export const syncCustomer = async (
  customerId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'customer',
    customerId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'medium'
    }
  )
}

/**
 * Quick helper to sync vehicle data
 */
export const syncVehicle = async (
  vehicleId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'vehicle',
    vehicleId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'medium'
    }
  )
}

/**
 * Quick helper to sync technician data
 */
export const syncTechnician = async (
  technicianId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'technician',
    technicianId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'medium'
    }
  )
}

/**
 * Quick helper to sync inventory data
 */
export const syncInventoryItem = async (
  itemId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'inventory_item',
    itemId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'high'
    }
  )
}

/**
 * Quick helper to sync part data
 */
export const syncPart = async (
  partId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'part',
    partId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'high'
    }
  )
}

/**
 * Quick helper to sync invoice data
 */
export const syncInvoice = async (
  invoiceId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'invoice',
    invoiceId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'high'
    }
  )
}

/**
 * Quick helper to sync payment data
 */
export const syncPayment = async (
  paymentId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'payment',
    paymentId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'high'
    }
  )
}

/**
 * Quick helper to sync quality check data
 */
export const syncQualityCheck = async (
  qualityCheckId: string,
  data: any,
  options: {
    immediate?: boolean
    optimistic?: boolean
    priority?: 'high' | 'medium' | 'low'
  } = {}
): Promise<string> => {
  return await syncManager.queueOperation(
    'update',
    'quality_check',
    qualityCheckId,
    data,
    {
      immediate: options.immediate || false,
      optimistic: options.optimistic || true,
      priority: options.priority || 'medium'
    }
  )
}

/**
 * Helper to get sync statistics for monitoring
 */
export const getSyncStatistics = () => {
  const state = syncManager.getSyncState()
  const metrics = syncManager.getSyncMetrics()
  const conflicts = syncManager.getConflicts()
  const resolutionStats = conflictResolver.getResolutionStatistics()

  return {
    state,
    metrics,
    conflicts: {
      count: conflicts.length,
      items: conflicts
    },
    resolutionStats,
    summary: {
      isOnline: state.isOnline,
      pendingOperations: state.pendingOperations,
      conflictCount: state.conflictCount,
      errorCount: state.errorCount,
      lastSyncTime: state.lastSyncTime,
      successRate: resolutionStats.successRate
    }
  }
}

/**
 * Helper to perform full system sync
 */
export const performFullSync = async (): Promise<{
  success: boolean
  results: { success: number; failed: number; conflicts: number }
  message: string
  messageAr: string
}> => {
  try {
    console.log('🔄 Starting full system sync...')
    
    const results = await syncManager.syncAll()
    
    const message = `Sync completed: ${results.success} successful, ${results.failed} failed, ${results.conflicts} conflicts`
    const messageAr = `اكتمل التزامن: ${results.success} نجح، ${results.failed} فشل، ${results.conflicts} تعارض`
    
    return {
      success: results.failed === 0 && results.conflicts === 0,
      results,
      message,
      messageAr
    }
  } catch (error) {
    console.error('❌ Full sync failed:', error)
    
    return {
      success: false,
      results: { success: 0, failed: 1, conflicts: 0 },
      message: `Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      messageAr: `فشل التزامن: ${error instanceof Error ? error.message : 'خطأ غير معروف'}`
    }
  }
}

/**
 * Helper to auto-resolve conflicts based on strategy
 */
export const autoResolveConflicts = async (
  strategy: 'timestamp_based' | 'priority_based' | 'cultural_aware' = 'cultural_aware'
): Promise<{
  resolved: number
  failed: number
  remaining: number
}> => {
  const conflicts = syncManager.getConflicts()
  let resolved = 0
  let failed = 0

  for (const conflict of conflicts) {
    try {
      const result = await conflictResolver.resolveConflict(conflict, strategy)
      
      if (result.success) {
        await syncManager.resolveConflict(conflict.id, 'merge', result.resolvedData)
        resolved++
      } else {
        failed++
      }
    } catch (error) {
      console.error(`❌ Failed to resolve conflict ${conflict.id}:`, error)
      failed++
    }
  }

  const remaining = conflicts.length - resolved - failed

  console.log(`🔧 Auto-resolved ${resolved} conflicts, ${failed} failed, ${remaining} remaining`)

  return { resolved, failed, remaining }
}

/**
 * Helper to check sync health
 */
export const checkSyncHealth = () => {
  const state = syncManager.getSyncState()
  const metrics = syncManager.getSyncMetrics()
  const conflicts = syncManager.getConflicts()

  const health = {
    overall: 'healthy' as 'healthy' | 'warning' | 'critical',
    issues: [] as string[],
    issuesAr: [] as string[],
    recommendations: [] as string[],
    recommendationsAr: [] as string[]
  }

  // Check for critical issues
  if (!state.isOnline) {
    health.overall = 'critical'
    health.issues.push('System is offline')
    health.issuesAr.push('النظام غير متصل')
    health.recommendations.push('Check network connection')
    health.recommendationsAr.push('تحقق من اتصال الشبكة')
  }

  if (state.errorCount > 10) {
    health.overall = 'critical'
    health.issues.push(`High error count: ${state.errorCount}`)
    health.issuesAr.push(`عدد أخطاء مرتفع: ${state.errorCount}`)
    health.recommendations.push('Review error logs and resolve underlying issues')
    health.recommendationsAr.push('راجع سجلات الأخطاء وحل المشاكل الأساسية')
  }

  // Check for warnings
  if (state.pendingOperations > 100) {
    if (health.overall === 'healthy') health.overall = 'warning'
    health.issues.push(`Large sync queue: ${state.pendingOperations} operations`)
    health.issuesAr.push(`طابور تزامن كبير: ${state.pendingOperations} عملية`)
    health.recommendations.push('Consider manual sync or review sync strategy')
    health.recommendationsAr.push('فكر في التزامن اليدوي أو مراجعة استراتيجية التزامن')
  }

  if (conflicts.length > 5) {
    if (health.overall === 'healthy') health.overall = 'warning'
    health.issues.push(`Multiple conflicts: ${conflicts.length}`)
    health.issuesAr.push(`تعارضات متعددة: ${conflicts.length}`)
    health.recommendations.push('Resolve conflicts manually or use auto-resolution')
    health.recommendationsAr.push('حل التعارضات يدوياً أو استخدم الحل التلقائي')
  }

  if (metrics.successRate < 80) {
    if (health.overall === 'healthy') health.overall = 'warning'
    health.issues.push(`Low success rate: ${metrics.successRate.toFixed(1)}%`)
    health.issuesAr.push(`معدل نجاح منخفض: ${metrics.successRate.toFixed(1)}%`)
    health.recommendations.push('Review sync configuration and server connectivity')
    health.recommendationsAr.push('راجع إعدادات التزامن واتصال الخادم')
  }

  return health
}

// Default configuration presets
export const SYNC_CONFIGS = {
  REAL_TIME: {
    strategy: 'immediate',
    batchSize: 1,
    syncInterval: 5000,
    maxRetries: 3,
    retryDelay: 1000,
    conflictResolution: 'manual',
    enableOptimisticUpdates: true,
    enableCompression: false,
    enableEncryption: false,
    syncPriority: 'high'
  } as SyncConfig,
  
  BALANCED: {
    strategy: 'batched',
    batchSize: 10,
    syncInterval: 30000,
    maxRetries: 3,
    retryDelay: 2000,
    conflictResolution: 'cultural_aware',
    enableOptimisticUpdates: true,
    enableCompression: true,
    enableEncryption: false,
    syncPriority: 'medium'
  } as SyncConfig,
  
  OFFLINE_FIRST: {
    strategy: 'scheduled',
    batchSize: 50,
    syncInterval: 300000,
    maxRetries: 5,
    retryDelay: 5000,
    conflictResolution: 'merge',
    enableOptimisticUpdates: true,
    enableCompression: true,
    enableEncryption: true,
    syncPriority: 'low'
  } as SyncConfig
} as const

console.log('🔄 Sync Module Loaded - Phase 3 Week 2 Implementation Complete')
