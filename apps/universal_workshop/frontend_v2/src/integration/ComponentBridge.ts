/**
 * Component Bridge - Universal Workshop Frontend V2
 * 
 * Safe integration layer for gradually replacing legacy Frappe components
 * with new Vue 3 components without breaking existing functionality.
 */

import { defineAsyncComponent, createApp, type App, type Component } from 'vue'
import { useFeatureFlags } from '@/composables/useFeatureFlags'

// Integration configuration
export interface ComponentReplacement {
  legacySelector: string
  newComponent: Component
  enabledFlag: string
  fallbackBehavior: 'legacy' | 'hybrid' | 'none'
  migrationPhase: 1 | 2 | 3 | 4
  testingEnabled: boolean
  rolloutPercentage: number
  dependencies?: string[]
  compatibility: {
    minFrappeVersion: string
    maxFrappeVersion?: string
    requiredFeatures: string[]
  }
}

// Legacy Frappe integration interface
interface FrappeUIForm {
  refresh: (...args: any[]) => void
}

interface FrappeUI {
  form?: {
    refresh: (...args: any[]) => void
  }
}

interface FrappeRoute {
  on: (event: string, callback: () => void) => void
}

interface FrappeCall {
  method: string
  args?: any
}

interface FrappeCore {
  ready: (callback: () => void) => void
  route?: FrappeRoute
  ui?: FrappeUI
  call: (options: FrappeCall) => Promise<any>
  msgprint: (message: string) => void
  show_alert: (message: string, type?: string) => void
  boot?: {
    version?: string
    user?: any
    lang?: string
  }
}

declare global {
  interface Window {
    frappe?: FrappeCore
    cur_frm?: any
    cur_list?: any
    cur_page?: any
  }
}

// Component replacement registry
const componentReplacements: ComponentReplacement[] = [
  {
    legacySelector: '.btn, button[data-fieldtype="Button"]',
    newComponent: defineAsyncComponent(() => import('@/components/base/Button.vue')),
    enabledFlag: 'vue3_buttons',
    fallbackBehavior: 'hybrid',
    migrationPhase: 1,
    testingEnabled: true,
    rolloutPercentage: 25,
    compatibility: {
      minFrappeVersion: '15.0.0',
      requiredFeatures: ['modern_ui']
    }
  },
  {
    legacySelector: 'input[type="text"], input[type="email"], textarea',
    newComponent: defineAsyncComponent(() => import('@/components/base/Input.vue')),
    enabledFlag: 'vue3_inputs',
    fallbackBehavior: 'hybrid',
    migrationPhase: 1,
    testingEnabled: true,
    rolloutPercentage: 15,
    compatibility: {
      minFrappeVersion: '15.0.0',
      requiredFeatures: ['modern_ui', 'form_validation']
    }
  },
  {
    legacySelector: '.frappe-card, .card',
    newComponent: defineAsyncComponent(() => import('@/components/base/Card.vue')),
    enabledFlag: 'vue3_cards',
    fallbackBehavior: 'legacy',
    migrationPhase: 2,
    testingEnabled: true,
    rolloutPercentage: 10,
    compatibility: {
      minFrappeVersion: '15.0.0',
      requiredFeatures: ['modern_ui']
    }
  },
  {
    legacySelector: 'form, .form-layout',
    newComponent: defineAsyncComponent(() => import('@/components/forms/Form.vue')),
    enabledFlag: 'vue3_forms',
    fallbackBehavior: 'legacy',
    migrationPhase: 3,
    testingEnabled: false,
    rolloutPercentage: 5,
    dependencies: ['vue3_inputs', 'vue3_buttons'],
    compatibility: {
      minFrappeVersion: '15.0.0',
      requiredFeatures: ['modern_ui', 'form_validation', 'arabic_support']
    }
  },
  {
    legacySelector: '.alert, .message',
    newComponent: defineAsyncComponent(() => import('@/components/feedback/Alert.vue')),
    enabledFlag: 'vue3_alerts',
    fallbackBehavior: 'hybrid',
    migrationPhase: 2,
    testingEnabled: true,
    rolloutPercentage: 20,
    compatibility: {
      minFrappeVersion: '15.0.0',
      requiredFeatures: ['modern_ui']
    }
  }
]

// Component Bridge Manager
export class ComponentBridge {
  private vueApps: Map<string, App> = new Map()
  private replacementStatus: Map<string, boolean> = new Map()
  private performanceMetrics: Map<string, number[]> = new Map()
  private errorLog: Array<{ component: string; error: Error; timestamp: Date }> = []
  private featureFlags: ReturnType<typeof useFeatureFlags>

  constructor() {
    this.featureFlags = useFeatureFlags()
    this.initialize()
  }


  /**
   * Initialize the component bridge system
   */
  private async initialize(): Promise<void> {
    if (typeof window !== 'undefined' && window.frappe) {
      window.frappe.ready(() => {
        this.setupFrappeIntegration()
        this.startComponentReplacement()
        this.setupPerformanceMonitoring()
        this.setupErrorHandling()
      })
    }
  }

  /**
   * Set up integration with Frappe's existing systems
   */
  private setupFrappeIntegration(): void {
    // Hook into Frappe's route changes
    if (window.frappe.route) {
      const originalRoute = window.frappe.route
      window.frappe.route = {
        ...originalRoute,
        on: (event: string, callback: () => void) => {
          originalRoute.on(event, () => {
            callback()
            this.handleRouteChange()
          })
        }
      }
    }

    // Hook into form renders
    if (window.frappe.ui && window.frappe.ui.form) {
      const originalFormRefresh = window.frappe.ui.form.refresh
      const self = this
      window.frappe.ui.form.refresh = function(this: any) {
        originalFormRefresh.apply(this, arguments)
        setTimeout(() => self.handleFormRender(this), 100)
      }
    }

    console.log('🔗 Frappe integration initialized')
  }

  /**
   * Start the gradual component replacement process
   */
  private async startComponentReplacement(): Promise<void> {
    const enabledReplacements = componentReplacements.filter(replacement => {
      // Check feature flag
      if (!this.featureFlags.isEnabled(replacement.enabledFlag)) {
        return false
      }

      // Check rollout percentage
      if (!this.featureFlags.isInRollout(replacement.enabledFlag, replacement.rolloutPercentage)) {
        return false
      }

      // Check dependencies
      if (replacement.dependencies) {
        const dependenciesMet = replacement.dependencies.every(dep => 
          this.featureFlags.isEnabled(dep)
        )
        if (!dependenciesMet) {
          return false
        }
      }

      // Check compatibility
      if (!this.checkCompatibility(replacement.compatibility)) {
        return false
      }

      return true
    })

    console.log(`🚀 Starting component replacement for ${enabledReplacements.length} components`)

    for (const replacement of enabledReplacements) {
      try {
        await this.replaceComponent(replacement)
      } catch (error) {
        this.logError(replacement.legacySelector, error as Error)
        console.error(`❌ Failed to replace ${replacement.legacySelector}:`, error)
      }
    }
  }

  /**
   * Replace a legacy component with Vue 3 component
   */
  private async replaceComponent(replacement: ComponentReplacement): Promise<void> {
    const startTime = performance.now()
    const elements = document.querySelectorAll(replacement.legacySelector)

    console.log(`🔄 Replacing ${elements.length} instances of ${replacement.legacySelector}`)

    for (const element of elements) {
      try {
        await this.replaceElement(element as HTMLElement, replacement)
      } catch (error) {
        console.error(`Failed to replace element:`, error)
        
        if (replacement.fallbackBehavior === 'legacy') {
          // Keep legacy element as-is
          continue
        } else if (replacement.fallbackBehavior === 'hybrid') {
          // Apply Vue 3 styling to legacy element
          this.applyHybridStyling(element as HTMLElement, replacement)
        }
      }
    }

    const endTime = performance.now()
    this.recordPerformanceMetric(replacement.legacySelector, endTime - startTime)
    this.replacementStatus.set(replacement.legacySelector, true)
  }

  /**
   * Replace individual element with Vue component
   */
  private async replaceElement(element: HTMLElement, replacement: ComponentReplacement): Promise<void> {
    // Extract data from legacy element
    const elementData = this.extractElementData(element)
    
    // Create Vue app instance
    const appId = `vue-app-${Math.random().toString(36).substr(2, 9)}`
    const mountPoint = document.createElement('div')
    mountPoint.id = appId
    
    // Create Vue app
    const app = createApp({
      components: {
        ReplacementComponent: replacement.newComponent
      },
      data() {
        return {
          ...elementData,
          isRTL: document.documentElement.dir === 'rtl' || document.documentElement.getAttribute('data-dir') === 'rtl',
          preferArabic: this.detectArabicPreference()
        }
      },
      methods: {
        detectArabicPreference() {
          return document.documentElement.lang === 'ar' || 
                 localStorage.getItem('preferred_language') === 'ar' ||
                 window.frappe?.boot?.lang === 'ar'
        },
        handleLegacyEvent(eventName: string, data: any) {
          // Bridge Vue events back to Frappe
          const event = new CustomEvent(eventName, { detail: data })
          element.dispatchEvent(event)
        }
      },
      template: this.generateTemplate(replacement, elementData)
    })

    // Add error handling
    app.config.errorHandler = (err, instance, info) => {
      this.logError(replacement.legacySelector, err as Error)
      console.error('Vue component error:', err, info)
    }

    // Mount Vue component
    element.parentNode?.insertBefore(mountPoint, element)
    app.mount(`#${appId}`)
    
    // Store app instance for cleanup
    this.vueApps.set(appId, app)
    
    // Hide or remove legacy element
    if (replacement.testingEnabled) {
      element.style.display = 'none'
      element.setAttribute('data-vue-replaced', 'true')
    } else {
      element.remove()
    }
  }

  /**
   * Extract relevant data from legacy element
   */
  private extractElementData(element: HTMLElement): Record<string, any> {
    const data: Record<string, any> = {}

    // Extract common attributes
    data.id = element.id
    data.className = element.className
    data.textContent = element.textContent?.trim()
    data.disabled = element.hasAttribute('disabled')
    data.required = element.hasAttribute('required')

    // Extract input-specific data
    if (element instanceof HTMLInputElement) {
      data.type = element.type
      data.value = element.value
      data.placeholder = element.placeholder
      data.name = element.name
    }

    // Extract button-specific data
    if (element instanceof HTMLButtonElement || element.classList.contains('btn')) {
      data.type = element.getAttribute('type') || 'button'
      data.variant = this.extractButtonVariant(element)
      data.size = this.extractButtonSize(element)
    }

    // Extract Frappe-specific data
    data.fieldname = element.getAttribute('data-fieldname')
    data.fieldtype = element.getAttribute('data-fieldtype')
    data.doctype = element.getAttribute('data-doctype')

    return data
  }

  /**
   * Extract button variant from legacy classes
   */
  private extractButtonVariant(element: HTMLElement): string {
    if (element.classList.contains('btn-primary')) return 'primary'
    if (element.classList.contains('btn-secondary')) return 'secondary'
    if (element.classList.contains('btn-success')) return 'primary'
    if (element.classList.contains('btn-danger')) return 'danger'
    if (element.classList.contains('btn-warning')) return 'warning'
    if (element.classList.contains('btn-outline')) return 'outline'
    return 'secondary'
  }

  /**
   * Extract button size from legacy classes
   */
  private extractButtonSize(element: HTMLElement): string {
    if (element.classList.contains('btn-sm')) return 'sm'
    if (element.classList.contains('btn-lg')) return 'lg'
    if (element.classList.contains('btn-xl')) return 'xl'
    return 'md'
  }

  /**
   * Generate Vue template based on component type
   */
  private generateTemplate(replacement: ComponentReplacement, data: Record<string, any>): string {
    const componentName = 'ReplacementComponent'
    
    if (replacement.legacySelector.includes('button') || replacement.legacySelector.includes('.btn')) {
      return `
        <${componentName}
          :variant="'${data.variant}'"
          :size="'${data.size}'"
          :disabled="${data.disabled}"
          @click="handleLegacyEvent('click', $event)"
        >
          ${data.textContent || 'Button'}
        </${componentName}>
      `
    }
    
    if (replacement.legacySelector.includes('input')) {
      return `
        <${componentName}
          :model-value="'${data.value || ''}'"
          :type="'${data.type}'"
          :placeholder="'${data.placeholder || ''}'"
          :disabled="${data.disabled}"
          :required="${data.required}"
          @update:model-value="handleLegacyEvent('input', $event)"
          @blur="handleLegacyEvent('blur', $event)"
        />
      `
    }
    
    // Default template
    return `<${componentName} v-bind="$data" />`
  }

  /**
   * Apply hybrid styling to keep legacy elements but with Vue 3 styles
   */
  private applyHybridStyling(element: HTMLElement, replacement: ComponentReplacement): void {
    element.classList.add('vue3-hybrid')
    
    // Apply design token styles
    const computedStyle = getComputedStyle(document.documentElement)
    
    if (replacement.legacySelector.includes('button') || replacement.legacySelector.includes('.btn')) {
      element.style.borderRadius = computedStyle.getPropertyValue('--radius-md')
      element.style.transition = computedStyle.getPropertyValue('--transition-colors')
      element.style.fontWeight = computedStyle.getPropertyValue('--font-weight-medium')
    }
    
    if (replacement.legacySelector.includes('input')) {
      element.style.borderRadius = computedStyle.getPropertyValue('--radius-md')
      element.style.borderColor = computedStyle.getPropertyValue('--color-border-primary')
      element.style.padding = computedStyle.getPropertyValue('--spacing-3')
    }
  }

  /**
   * Check if system meets compatibility requirements
   */
  private checkCompatibility(compatibility: ComponentReplacement['compatibility']): boolean {
    // Check Frappe version (simplified)
    const frappeVersion = window.frappe?.boot?.version || '15.0.0'
    if (!this.isVersionCompatible(frappeVersion, compatibility.minFrappeVersion)) {
      return false
    }

    // Check required features
    return compatibility.requiredFeatures.every(feature => {
      return this.featureFlags.isEnabled(feature)
    })
  }

  /**
   * Simple version comparison
   */
  private isVersionCompatible(current: string, required: string): boolean {
    const currentParts = current.split('.').map(Number)
    const requiredParts = required.split('.').map(Number)
    
    for (let i = 0; i < Math.max(currentParts.length, requiredParts.length); i++) {
      const currentPart = currentParts[i] || 0
      const requiredPart = requiredParts[i] || 0
      
      if (currentPart > requiredPart) return true
      if (currentPart < requiredPart) return false
    }
    
    return true
  }

  /**
   * Handle route changes to re-scan for components
   */
  private handleRouteChange(): void {
    setTimeout(() => {
      console.log('🔄 Route changed, re-scanning for components')
      this.startComponentReplacement()
    }, 500)
  }

  /**
   * Handle form render events
   */
  private handleFormRender(form: any): void {
    console.log('📋 Form rendered, scanning for components')
    this.startComponentReplacement()
  }

  /**
   * Set up performance monitoring
   */
  private setupPerformanceMonitoring(): void {
    // Monitor initial load performance
    if (typeof window !== 'undefined' && 'performance' in window) {
      window.addEventListener('load', () => {
        const loadTime = performance.now()
        console.log(`⚡ Component bridge loaded in ${loadTime.toFixed(2)}ms`)
      })
    }
  }

  /**
   * Record performance metric
   */
  private recordPerformanceMetric(component: string, time: number): void {
    if (!this.performanceMetrics.has(component)) {
      this.performanceMetrics.set(component, [])
    }
    this.performanceMetrics.get(component)!.push(time)
  }

  /**
   * Set up global error handling
   */
  private setupErrorHandling(): void {
    window.addEventListener('error', (event) => {
      if (event.error && event.error.stack?.includes('vue')) {
        this.logError('global', event.error)
      }
    })
    
    window.addEventListener('unhandledrejection', (event) => {
      if (event.reason?.stack?.includes('vue')) {
        this.logError('promise', event.reason)
      }
    })
  }

  /**
   * Log component errors
   */
  private logError(component: string, error: Error): void {
    this.errorLog.push({
      component,
      error,
      timestamp: new Date()
    })
    
    // Report to Frappe if available
    if (window.frappe?.call) {
      window.frappe.call({
        method: 'universal_workshop.api.log_frontend_error',
        args: {
          component,
          error: error.message,
          stack: error.stack,
          timestamp: new Date().toISOString()
        }
      }).catch(() => {
        // Silently fail if logging endpoint doesn't exist
      })
    }
  }

  /**
   * Get replacement statistics
   */
  public getStats(): {
    totalReplacements: number
    successfulReplacements: number
    failedReplacements: number
    performanceMetrics: Record<string, number>
    errorLog: Array<{ component: string; error: string; timestamp: Date }>
  } {
    const performanceAvg: Record<string, number> = {}
    
    for (const [component, times] of this.performanceMetrics) {
      performanceAvg[component] = times.reduce((a, b) => a + b, 0) / times.length
    }
    
    return {
      totalReplacements: componentReplacements.length,
      successfulReplacements: this.replacementStatus.size,
      failedReplacements: this.errorLog.length,
      performanceMetrics: performanceAvg,
      errorLog: this.errorLog.map(log => ({
        component: log.component,
        error: log.error.message,
        timestamp: log.timestamp
      }))
    }
  }

  /**
   * Cleanup all Vue instances
   */
  public cleanup(): void {
    for (const [appId, app] of this.vueApps) {
      try {
        app.unmount()
        const element = document.getElementById(appId)
        element?.remove()
      } catch (error) {
        console.error(`Failed to cleanup Vue app ${appId}:`, error)
      }
    }
    
    this.vueApps.clear()
    this.replacementStatus.clear()
    this.performanceMetrics.clear()
    this.errorLog.length = 0
  }
}

// Global bridge instance
export const bridge = new ComponentBridge()

// Export for external access
if (typeof window !== 'undefined') {
  (window as any).UniversalWorkshopBridge = bridge
}

export default ComponentBridge