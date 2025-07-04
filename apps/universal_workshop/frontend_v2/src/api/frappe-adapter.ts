/**
 * Enhanced Frappe API Adapter - Frontend V2
 * 
 * Comprehensive adapter for integrating Vue.js 3 with Frappe framework APIs
 * Provides type-safe, reactive data access with Arabic/RTL support
 */

import { ref, reactive, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'

// Type definitions
export interface FrappeResponse<T = any> {
  message: T
  docs?: T[]
  doc?: T
  exc?: string
  exc_type?: string
}

export interface FrappeCallOptions {
  method: string
  args?: Record<string, any>
  callback?: (response: any) => void
  error?: (error: any) => void
  freeze?: boolean
  freeze_message?: string
  no_spinner?: boolean
}

export interface DocListOptions {
  doctype: string
  fields?: string[]
  filters?: Record<string, any>
  order_by?: string
  limit_start?: number
  limit_page_length?: number
  parent?: string
}

export interface DocGetOptions {
  doctype: string
  name: string
  filters?: Record<string, any>
}

export interface DocSaveOptions {
  doc: Record<string, any>
  action?: 'Save' | 'Submit' | 'Update'
}

// Main Frappe Adapter Class
export class FrappeAdapter {
  private static instance: FrappeAdapter
  private sessionData: Ref<any> = ref(null)
  private isConnected: Ref<boolean> = ref(false)
  private lastError: Ref<string | null> = ref(null)
  
  constructor() {
    this.initializeSession()
  }
  
  public static getInstance(): FrappeAdapter {
    if (!FrappeAdapter.instance) {
      FrappeAdapter.instance = new FrappeAdapter()
    }
    return FrappeAdapter.instance
  }
  
  // Session Management
  async initializeSession(): Promise<void> {
    try {
      // Check if we're in Frappe context
      if (typeof window !== 'undefined' && (window as any).frappe) {
        this.isConnected.value = true
        
        // Get session data from existing bridge
        const sessionResponse = await this.call(
          'universal_workshop.api.frontend_bridge.create_v2_user_session'
        )
        
        if (sessionResponse) {
          this.sessionData.value = sessionResponse
          console.log('✅ Frappe session initialized for V2')
        }
      } else {
        // Fallback: load from localStorage (for standalone V2 mode)
        const storedSession = localStorage.getItem('v2_session')
        if (storedSession) {
          this.sessionData.value = JSON.parse(storedSession)
          this.isConnected.value = true
        }
      }
    } catch (error) {
      console.error('❌ Failed to initialize Frappe session:', error)
      this.lastError.value = error instanceof Error ? error.message : 'Session initialization failed'
    }
  }
  
  // Core API Methods
  async call<T = any>(method: string, args: Record<string, any> = {}): Promise<T> {
    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined' || !(window as any).frappe) {
        reject(new Error('Frappe not available'))
        return
      }
      
      const frappe = (window as any).frappe
      
      frappe.call({
        method,
        args,
        callback: (response: FrappeResponse<T>) => {
          if (response.exc) {
            reject(new Error(response.exc))
          } else {
            resolve(response.message)
          }
        },
        error: (error: any) => {
          this.lastError.value = error.message || 'API call failed'
          reject(error)
        }
      })
    })
  }
  
  // Document Operations
  async getDocList(options: DocListOptions): Promise<any[]> {
    const args = {
      doctype: options.doctype,
      fields: options.fields || ['name'],
      filters: options.filters || {},
      order_by: options.order_by || 'modified desc',
      limit_start: options.limit_start || 0,
      limit_page_length: options.limit_page_length || 20
    }
    
    if (options.parent) {
      args.parent = options.parent
    }
    
    try {
      const response = await this.call('frappe.client.get_list', args)
      return Array.isArray(response) ? response : []
    } catch (error) {
      console.error(`Failed to get ${options.doctype} list:`, error)
      throw error
    }
  }
  
  async getDoc(options: DocGetOptions): Promise<any> {
    try {
      const response = await this.call('frappe.client.get', {
        doctype: options.doctype,
        name: options.name,
        filters: options.filters
      })
      return response
    } catch (error) {
      console.error(`Failed to get ${options.doctype} document:`, error)
      throw error
    }
  }
  
  async saveDoc(options: DocSaveOptions): Promise<any> {
    try {
      const response = await this.call('frappe.client.save', {
        doc: options.doc
      })
      return response
    } catch (error) {
      console.error('Failed to save document:', error)
      throw error
    }
  }
  
  async submitDoc(doctype: string, name: string): Promise<any> {
    try {
      const response = await this.call('frappe.client.submit', {
        doctype,
        name
      })
      return response
    } catch (error) {
      console.error('Failed to submit document:', error)
      throw error
    }
  }
  
  async deleteDoc(doctype: string, name: string): Promise<void> {
    try {
      await this.call('frappe.client.delete', {
        doctype,
        name
      })
    } catch (error) {
      console.error('Failed to delete document:', error)
      throw error
    }
  }
  
  // Universal Workshop Specific Methods
  async syncWorkshopData(dataType: string, lastSync?: string): Promise<any> {
    try {
      const response = await this.call(
        'universal_workshop.api.frontend_bridge.sync_v2_data',
        { data_type: dataType, last_sync: lastSync }
      )
      return response
    } catch (error) {
      console.error(`Failed to sync ${dataType}:`, error)
      throw error
    }
  }
  
  async getWorkshopConfig(): Promise<any> {
    try {
      const response = await this.call(
        'universal_workshop.api.frontend_bridge.get_v2_config'
      )
      return response
    } catch (error) {
      console.error('Failed to get workshop config:', error)
      throw error
    }
  }
  
  async setFrontendPreference(frontend: 'traditional' | 'v2'): Promise<void> {
    try {
      await this.call(
        'universal_workshop.api.frontend_bridge.set_frontend_preference',
        { frontend }
      )
    } catch (error) {
      console.error('Failed to set frontend preference:', error)
      throw error
    }
  }
  
  // Search and Filters (with Arabic support)
  async searchDocuments(
    doctype: string, 
    searchText: string, 
    options: { 
      fields?: string[]
      filters?: Record<string, any>
      limit?: number
      searchFields?: string[]
    } = {}
  ): Promise<any[]> {
    const searchFields = options.searchFields || ['name']
    const filters = options.filters || {}
    
    // Add search conditions for both English and Arabic fields
    const searchConditions = []
    for (const field of searchFields) {
      searchConditions.push([field, 'like', `%${searchText}%`])
      
      // If field has Arabic variant, search that too
      const arabicField = `${field}_ar`
      if (arabicField !== field) {
        searchConditions.push([arabicField, 'like', `%${searchText}%`])
      }
    }
    
    // Combine with OR logic
    if (searchConditions.length > 1) {
      filters['or'] = searchConditions
    } else if (searchConditions.length === 1) {
      Object.assign(filters, { [searchConditions[0][0]]: searchConditions[0] })
    }
    
    return this.getDocList({
      doctype,
      fields: options.fields,
      filters,
      limit_page_length: options.limit || 20
    })
  }
  
  // File Operations
  async uploadFile(
    file: File, 
    options: {
      doctype?: string
      docname?: string
      is_private?: boolean
      folder?: string
    } = {}
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined' || !(window as any).frappe) {
        reject(new Error('Frappe not available'))
        return
      }
      
      const frappe = (window as any).frappe
      const formData = new FormData()
      
      formData.append('file', file)
      formData.append('is_private', options.is_private ? '1' : '0')
      
      if (options.doctype) formData.append('doctype', options.doctype)
      if (options.docname) formData.append('docname', options.docname)
      if (options.folder) formData.append('folder', options.folder)
      
      frappe.call({
        method: 'frappe.handler.upload_file',
        args: {},
        callback: (response: FrappeResponse) => {
          if (response.exc) {
            reject(new Error(response.exc))
          } else {
            resolve(response.message)
          }
        },
        error: reject
      })
    })
  }
  
  // Real-time Methods
  async subscribeToUpdates(
    doctype: string, 
    callback: (data: any) => void
  ): Promise<() => void> {
    if (typeof window === 'undefined' || !(window as any).frappe?.realtime) {
      throw new Error('Real-time updates not available')
    }
    
    const frappe = (window as any).frappe
    const eventName = `${doctype.toLowerCase()}_update`
    
    frappe.realtime.on(eventName, callback)
    
    // Return unsubscribe function
    return () => {
      frappe.realtime.off(eventName, callback)
    }
  }
  
  // Getters for reactive properties
  get session(): ComputedRef<any> {
    return computed(() => this.sessionData.value)
  }
  
  get connected(): ComputedRef<boolean> {
    return computed(() => this.isConnected.value)
  }
  
  get error(): ComputedRef<string | null> {
    return computed(() => this.lastError.value)
  }
  
  get user(): ComputedRef<any> {
    return computed(() => this.sessionData.value?.user || null)
  }
  
  get workshop(): ComputedRef<any> {
    return computed(() => this.sessionData.value?.workshop || null)
  }
  
  get settings(): ComputedRef<any> {
    return computed(() => this.sessionData.value?.settings || {})
  }
  
  // Utility Methods
  clearError(): void {
    this.lastError.value = null
  }
  
  async refresh(): Promise<void> {
    await this.initializeSession()
  }
  
  // Format helpers for Arabic/RTL
  formatCurrency(amount: number): string {
    const settings = this.sessionData.value?.settings
    const isArabic = settings?.language === 'ar'
    
    if (isArabic) {
      const arabicAmount = this.convertToArabicNumerals(amount.toFixed(3))
      return `ر.ع. ${arabicAmount}`
    } else {
      return `OMR ${amount.toFixed(3)}`
    }
  }
  
  formatDate(date: string | Date): string {
    const settings = this.sessionData.value?.settings
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    if (settings?.language === 'ar') {
      return new Intl.DateTimeFormat('ar-OM', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(dateObj)
    } else {
      return new Intl.DateTimeFormat('en-OM', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }).format(dateObj)
    }
  }
  
  private convertToArabicNumerals(input: string | number): string {
    const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
    return input.toString().replace(/[0-9]/g, (digit) => arabicNumerals[parseInt(digit)])
  }
}

// Composable for Vue components
export function useFrappeAdapter() {
  const adapter = FrappeAdapter.getInstance()
  
  return {
    // Core methods
    call: adapter.call.bind(adapter),
    getDocList: adapter.getDocList.bind(adapter),
    getDoc: adapter.getDoc.bind(adapter),
    saveDoc: adapter.saveDoc.bind(adapter),
    submitDoc: adapter.submitDoc.bind(adapter),
    deleteDoc: adapter.deleteDoc.bind(adapter),
    
    // Universal Workshop methods
    syncWorkshopData: adapter.syncWorkshopData.bind(adapter),
    getWorkshopConfig: adapter.getWorkshopConfig.bind(adapter),
    setFrontendPreference: adapter.setFrontendPreference.bind(adapter),
    
    // Search and utilities
    searchDocuments: adapter.searchDocuments.bind(adapter),
    uploadFile: adapter.uploadFile.bind(adapter),
    subscribeToUpdates: adapter.subscribeToUpdates.bind(adapter),
    
    // Reactive properties
    session: adapter.session,
    connected: adapter.connected,
    error: adapter.error,
    user: adapter.user,
    workshop: adapter.workshop,
    settings: adapter.settings,
    
    // Utilities
    clearError: adapter.clearError.bind(adapter),
    refresh: adapter.refresh.bind(adapter),
    formatCurrency: adapter.formatCurrency.bind(adapter),
    formatDate: adapter.formatDate.bind(adapter)
  }
}

// Export default instance
export default FrappeAdapter.getInstance()