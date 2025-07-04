/**
 * Offline Database - Universal Workshop Frontend V2
 * 
 * IndexedDB wrapper for offline data storage with Arabic text support,
 * conflict resolution, and synchronization capabilities.
 */

export interface OfflineEntity {
  id: string
  type: string
  data: any
  created: number
  modified: number
  synced: boolean
  version: number
  checksum?: string
  metadata?: {
    userId?: string
    arabicContent?: boolean
    priority?: 'low' | 'medium' | 'high' | 'critical'
  }
}

export interface SyncOperation {
  id: string
  type: 'create' | 'update' | 'delete'
  entityType: string
  entityId: string
  operation: any
  timestamp: number
  retries: number
  maxRetries: number
  lastError?: string
}

export interface ConflictResolution {
  strategy: 'client_wins' | 'server_wins' | 'merge' | 'manual'
  resolver?: (clientData: any, serverData: any) => any
}

export interface DatabaseSchema {
  version: number
  stores: {
    [storeName: string]: {
      keyPath: string
      autoIncrement?: boolean
      indexes?: {
        [indexName: string]: {
          keyPath: string | string[]
          unique?: boolean
          multiEntry?: boolean
        }
      }
    }
  }
}

export class OfflineDatabase {
  private db: IDBDatabase | null = null
  private dbName: string
  private schema: DatabaseSchema
  private isReady = false
  private initPromise: Promise<void> | null = null

  constructor(dbName: string = 'UniversalWorkshopOffline') {
    this.dbName = dbName
    this.schema = this.getDefaultSchema()
  }

  /**
   * Get default database schema
   */
  private getDefaultSchema(): DatabaseSchema {
    return {
      version: 1,
      stores: {
        entities: {
          keyPath: 'id',
          indexes: {
            type: { keyPath: 'type' },
            modified: { keyPath: 'modified' },
            synced: { keyPath: 'synced' },
            userId: { keyPath: 'metadata.userId' }
          }
        },
        syncOperations: {
          keyPath: 'id',
          indexes: {
            timestamp: { keyPath: 'timestamp' },
            type: { keyPath: 'type' },
            entityType: { keyPath: 'entityType' },
            retries: { keyPath: 'retries' }
          }
        },
        cache: {
          keyPath: 'key',
          indexes: {
            timestamp: { keyPath: 'timestamp' },
            category: { keyPath: 'category' },
            expires: { keyPath: 'expires' }
          }
        },
        settings: {
          keyPath: 'key'
        }
      }
    }
  }

  /**
   * Initialize database
   */
  async initialize(): Promise<void> {
    if (this.initPromise) {
      return this.initPromise
    }

    this.initPromise = this.performInitialization()
    return this.initPromise
  }

  private async performInitialization(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.schema.version)

      request.onerror = () => {
        reject(new Error(`Failed to open database: ${request.error}`))
      }

      request.onsuccess = () => {
        this.db = request.result
        this.isReady = true
        
        // Setup error handling
        this.db.onerror = (event) => {
          console.error('Database error:', event)
        }

        resolve()
      }

      request.onupgradeneeded = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result
        this.upgradeDatabase(event.oldVersion, this.schema.version)
      }
    })
  }

  /**
   * Upgrade database schema
   */
  private upgradeDatabase(oldVersion: number, newVersion: number): void {
    if (!this.db) return

    console.log(`Upgrading database from version ${oldVersion} to ${newVersion}`)

    // Create stores and indexes
    Object.entries(this.schema.stores).forEach(([storeName, config]) => {
      let store: IDBObjectStore

      if (!this.db!.objectStoreNames.contains(storeName)) {
        store = this.db!.createObjectStore(storeName, {
          keyPath: config.keyPath,
          autoIncrement: config.autoIncrement || false
        })
      } else {
        // Store exists, might need index updates
        return
      }

      // Create indexes
      if (config.indexes) {
        Object.entries(config.indexes).forEach(([indexName, indexConfig]) => {
          if (!store.indexNames.contains(indexName)) {
            store.createIndex(indexName, indexConfig.keyPath, {
              unique: indexConfig.unique || false,
              multiEntry: indexConfig.multiEntry || false
            })
          }
        })
      }
    })
  }

  /**
   * Store entity offline
   */
  async storeEntity(entity: Partial<OfflineEntity>): Promise<string> {
    await this.ensureReady()

    const entityId = entity.id || this.generateId()
    const now = Date.now()

    const fullEntity: OfflineEntity = {
      id: entityId,
      type: entity.type || 'unknown',
      data: entity.data || {},
      created: entity.created || now,
      modified: now,
      synced: false,
      version: (entity.version || 0) + 1,
      checksum: this.calculateChecksum(entity.data),
      metadata: {
        userId: this.getCurrentUserId(),
        arabicContent: this.detectArabicContent(entity.data),
        priority: entity.metadata?.priority || 'medium',
        ...entity.metadata
      }
    }

    const transaction = this.db!.transaction(['entities'], 'readwrite')
    const store = transaction.objectStore('entities')

    return new Promise((resolve, reject) => {
      const request = store.put(fullEntity)
      
      request.onsuccess = () => resolve(entityId)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get entity by ID
   */
  async getEntity(id: string): Promise<OfflineEntity | null> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['entities'], 'readonly')
    const store = transaction.objectStore('entities')

    return new Promise((resolve, reject) => {
      const request = store.get(id)
      
      request.onsuccess = () => resolve(request.result || null)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get entities by type
   */
  async getEntitiesByType(type: string, limit?: number): Promise<OfflineEntity[]> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['entities'], 'readonly')
    const store = transaction.objectStore('entities')
    const index = store.index('type')

    return new Promise((resolve, reject) => {
      const request = limit ? index.getAll(type, limit) : index.getAll(type)
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get unsynced entities
   */
  async getUnsyncedEntities(limit?: number): Promise<OfflineEntity[]> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['entities'], 'readonly')
    const store = transaction.objectStore('entities')
    const index = store.index('synced')

    return new Promise((resolve, reject) => {
      const request = limit ? index.getAll(IDBKeyRange.only(false), limit) : index.getAll(IDBKeyRange.only(false))
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Mark entity as synced
   */
  async markEntitySynced(id: string): Promise<void> {
    await this.ensureReady()

    const entity = await this.getEntity(id)
    if (!entity) {
      throw new Error(`Entity ${id} not found`)
    }

    entity.synced = true
    entity.modified = Date.now()

    const transaction = this.db!.transaction(['entities'], 'readwrite')
    const store = transaction.objectStore('entities')

    return new Promise((resolve, reject) => {
      const request = store.put(entity)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Delete entity
   */
  async deleteEntity(id: string): Promise<void> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['entities'], 'readwrite')
    const store = transaction.objectStore('entities')

    return new Promise((resolve, reject) => {
      const request = store.delete(id)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Queue sync operation
   */
  async queueSyncOperation(operation: Partial<SyncOperation>): Promise<string> {
    await this.ensureReady()

    const opId = operation.id || this.generateId()
    const now = Date.now()

    const fullOperation: SyncOperation = {
      id: opId,
      type: operation.type || 'update',
      entityType: operation.entityType || 'unknown',
      entityId: operation.entityId || '',
      operation: operation.operation || {},
      timestamp: now,
      retries: 0,
      maxRetries: operation.maxRetries || 3,
      ...operation
    }

    const transaction = this.db!.transaction(['syncOperations'], 'readwrite')
    const store = transaction.objectStore('syncOperations')

    return new Promise((resolve, reject) => {
      const request = store.put(fullOperation)
      
      request.onsuccess = () => resolve(opId)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get pending sync operations
   */
  async getPendingSyncOperations(limit?: number): Promise<SyncOperation[]> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['syncOperations'], 'readonly')
    const store = transaction.objectStore('syncOperations')
    const index = store.index('timestamp')

    return new Promise((resolve, reject) => {
      const operations: SyncOperation[] = []
      const request = index.openCursor()

      request.onsuccess = () => {
        const cursor = request.result
        if (cursor && (!limit || operations.length < limit)) {
          const operation = cursor.value as SyncOperation
          if (operation.retries < operation.maxRetries) {
            operations.push(operation)
          }
          cursor.continue()
        } else {
          resolve(operations)
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Update sync operation
   */
  async updateSyncOperation(id: string, updates: Partial<SyncOperation>): Promise<void> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['syncOperations'], 'readwrite')
    const store = transaction.objectStore('syncOperations')

    // Get existing operation
    const getRequest = store.get(id)
    
    return new Promise((resolve, reject) => {
      getRequest.onsuccess = () => {
        const operation = getRequest.result
        if (!operation) {
          reject(new Error(`Sync operation ${id} not found`))
          return
        }

        // Apply updates
        const updatedOperation = { ...operation, ...updates }
        
        const putRequest = store.put(updatedOperation)
        putRequest.onsuccess = () => resolve()
        putRequest.onerror = () => reject(putRequest.error)
      }

      getRequest.onerror = () => reject(getRequest.error)
    })
  }

  /**
   * Remove sync operation
   */
  async removeSyncOperation(id: string): Promise<void> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['syncOperations'], 'readwrite')
    const store = transaction.objectStore('syncOperations')

    return new Promise((resolve, reject) => {
      const request = store.delete(id)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Cache data with expiration
   */
  async cacheData(key: string, data: any, category?: string, ttlMinutes?: number): Promise<void> {
    await this.ensureReady()

    const now = Date.now()
    const cacheItem = {
      key,
      data,
      category: category || 'general',
      timestamp: now,
      expires: ttlMinutes ? now + (ttlMinutes * 60 * 1000) : null
    }

    const transaction = this.db!.transaction(['cache'], 'readwrite')
    const store = transaction.objectStore('cache')

    return new Promise((resolve, reject) => {
      const request = store.put(cacheItem)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get cached data
   */
  async getCachedData(key: string): Promise<any | null> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['cache'], 'readonly')
    const store = transaction.objectStore('cache')

    return new Promise((resolve, reject) => {
      const request = store.get(key)
      
      request.onsuccess = () => {
        const item = request.result
        if (!item) {
          resolve(null)
          return
        }

        // Check expiration
        if (item.expires && Date.now() > item.expires) {
          // Expired, delete and return null
          this.deleteCachedData(key)
          resolve(null)
          return
        }

        resolve(item.data)
      }
      
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Delete cached data
   */
  async deleteCachedData(key: string): Promise<void> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['cache'], 'readwrite')
    const store = transaction.objectStore('cache')

    return new Promise((resolve, reject) => {
      const request = store.delete(key)
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Clear expired cache entries
   */
  async clearExpiredCache(): Promise<number> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['cache'], 'readwrite')
    const store = transaction.objectStore('cache')
    const index = store.index('expires')

    let deletedCount = 0
    const now = Date.now()

    return new Promise((resolve, reject) => {
      const request = index.openCursor()

      request.onsuccess = () => {
        const cursor = request.result
        if (cursor) {
          const item = cursor.value
          if (item.expires && now > item.expires) {
            cursor.delete()
            deletedCount++
          }
          cursor.continue()
        } else {
          resolve(deletedCount)
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Store settings
   */
  async storeSetting(key: string, value: any): Promise<void> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['settings'], 'readwrite')
    const store = transaction.objectStore('settings')

    return new Promise((resolve, reject) => {
      const request = store.put({ key, value, timestamp: Date.now() })
      
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get setting
   */
  async getSetting(key: string): Promise<any | null> {
    await this.ensureReady()

    const transaction = this.db!.transaction(['settings'], 'readonly')
    const store = transaction.objectStore('settings')

    return new Promise((resolve, reject) => {
      const request = store.get(key)
      
      request.onsuccess = () => {
        const item = request.result
        resolve(item ? item.value : null)
      }
      
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get database statistics
   */
  async getStatistics(): Promise<{
    entities: number
    unsyncedEntities: number
    pendingOperations: number
    cacheSize: number
    totalSize: number
  }> {
    await this.ensureReady()

    const stats = {
      entities: 0,
      unsyncedEntities: 0,
      pendingOperations: 0,
      cacheSize: 0,
      totalSize: 0
    }

    // Count entities
    const entitiesCount = await this.countStore('entities')
    stats.entities = entitiesCount

    // Count unsynced entities
    const unsyncedEntities = await this.getUnsyncedEntities()
    stats.unsyncedEntities = unsyncedEntities.length

    // Count pending operations
    const pendingOps = await this.getPendingSyncOperations()
    stats.pendingOperations = pendingOps.length

    // Count cache items
    const cacheCount = await this.countStore('cache')
    stats.cacheSize = cacheCount

    // Estimate total size (rough calculation)
    stats.totalSize = (stats.entities + stats.cacheSize) * 1024 // Rough estimate

    return stats
  }

  /**
   * Count items in store
   */
  private async countStore(storeName: string): Promise<number> {
    const transaction = this.db!.transaction([storeName], 'readonly')
    const store = transaction.objectStore('store')

    return new Promise((resolve, reject) => {
      const request = store.count()
      
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Utility methods
   */
  private async ensureReady(): Promise<void> {
    if (!this.isReady) {
      await this.initialize()
    }
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
  }

  private calculateChecksum(data: any): string {
    // Simple checksum calculation
    const str = JSON.stringify(data)
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash.toString(16)
  }

  private detectArabicContent(data: any): boolean {
    const str = JSON.stringify(data)
    const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/
    return arabicRegex.test(str)
  }

  private getCurrentUserId(): string {
    // This would come from the current user session
    return window.frappe?.boot?.user?.name || 'anonymous'
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close()
      this.db = null
      this.isReady = false
    }
  }

  /**
   * Delete entire database
   */
  static async deleteDatabase(dbName: string = 'UniversalWorkshopOffline'): Promise<void> {
    return new Promise((resolve, reject) => {
      const deleteRequest = indexedDB.deleteDatabase(dbName)
      
      deleteRequest.onsuccess = () => resolve()
      deleteRequest.onerror = () => reject(deleteRequest.error)
    })
  }
}

// Global instance
let globalOfflineDB: OfflineDatabase | null = null

export function getOfflineDatabase(): OfflineDatabase {
  if (!globalOfflineDB) {
    globalOfflineDB = new OfflineDatabase()
  }
  return globalOfflineDB
}

export default OfflineDatabase