/**
 * Migration Utilities - Universal Workshop Frontend V2
 * 
 * Utilities for safe migration from legacy Frappe components to Vue 3 components
 * with rollback capabilities and compatibility checks.
 */

import { bridge } from './ComponentBridge'
import { useFeatureFlags } from '@/composables/useFeatureFlags'

// Migration phase definitions
export enum MigrationPhase {
  PREPARATION = 0,
  FOUNDATION = 1,
  CORE_COMPONENTS = 2,
  FORMS_AND_VALIDATION = 3,
  COMPLETE_INTEGRATION = 4
}

// Migration step interface
export interface MigrationStep {
  id: string
  name: string
  nameAr: string
  description: string
  descriptionAr: string
  phase: MigrationPhase
  dependencies: string[]
  estimatedTime: number // in minutes
  riskLevel: 'low' | 'medium' | 'high'
  rollbackAvailable: boolean
  testingRequired: boolean
  backupRequired: boolean
  execute: () => Promise<boolean>
  rollback?: () => Promise<boolean>
  verify: () => Promise<boolean>
}

// Migration status
export interface MigrationStatus {
  currentPhase: MigrationPhase
  completedSteps: string[]
  failedSteps: string[]
  totalSteps: number
  completedCount: number
  estimatedTimeRemaining: number
  lastError?: string
  canRollback: boolean
}

// Pre-migration system checks
export class SystemCompatibilityChecker {
  static async runFullCheck(): Promise<{
    compatible: boolean
    issues: Array<{ severity: 'error' | 'warning' | 'info'; message: string; messageAr: string }>
    recommendations: Array<{ action: string; actionAr: string; priority: 'high' | 'medium' | 'low' }>
  }> {
    const issues: Array<{ severity: 'error' | 'warning' | 'info'; message: string; messageAr: string }> = []
    const recommendations: Array<{ action: string; actionAr: string; priority: 'high' | 'medium' | 'low' }> = []

    // Check Frappe version
    const frappeVersion = window.frappe?.boot?.version || '0.0.0'
    if (!this.isVersionCompatible(frappeVersion, '15.0.0')) {
      issues.push({
        severity: 'error',
        message: `Frappe version ${frappeVersion} is not compatible. Minimum required: 15.0.0`,
        messageAr: `إصدار Frappe ${frappeVersion} غير متوافق. الحد الأدنى المطلوب: 15.0.0`
      })
      recommendations.push({
        action: 'Upgrade Frappe to version 15.0.0 or higher',
        actionAr: 'ترقية Frappe إلى الإصدار 15.0.0 أو أحدث',
        priority: 'high'
      })
    }

    // Check browser support
    if (!this.checkBrowserSupport()) {
      issues.push({
        severity: 'warning',
        message: 'Browser may not support all Vue 3 features',
        messageAr: 'المتصفح قد لا يدعم جميع ميزات Vue 3'
      })
      recommendations.push({
        action: 'Update to a modern browser (Chrome 90+, Firefox 88+, Safari 14+)',
        actionAr: 'التحديث إلى متصفح حديث (Chrome 90+, Firefox 88+, Safari 14+)',
        priority: 'medium'
      })
    }

    // Check JavaScript environment
    if (!this.checkJavaScriptEnvironment()) {
      issues.push({
        severity: 'error',
        message: 'JavaScript environment missing required features',
        messageAr: 'بيئة JavaScript تفتقر للميزات المطلوبة'
      })
    }

    // Check CSS custom properties support
    if (!this.checkCSSCustomProperties()) {
      issues.push({
        severity: 'warning',
        message: 'CSS custom properties not fully supported',
        messageAr: 'خصائص CSS المخصصة غير مدعومة بالكامل'
      })
    }

    // Check for conflicting libraries
    const conflicts = this.checkLibraryConflicts()
    if (conflicts.length > 0) {
      issues.push({
        severity: 'warning',
        message: `Potential library conflicts detected: ${conflicts.join(', ')}`,
        messageAr: `تم اكتشاف تضارب محتمل في المكتبات: ${conflicts.join(', ')}`
      })
    }

    // Check data integrity
    const dataIssues = await this.checkDataIntegrity()
    issues.push(...dataIssues)

    const compatible = !issues.some(issue => issue.severity === 'error')

    return { compatible, issues, recommendations }
  }

  private static isVersionCompatible(current: string, required: string): boolean {
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

  private static checkBrowserSupport(): boolean {
    return !!(
      window.CSS &&
      window.CSS.supports &&
      window.CSS.supports('display', 'grid') &&
      'IntersectionObserver' in window &&
      'customElements' in window
    )
  }

  private static checkJavaScriptEnvironment(): boolean {
    try {
      // Check for Proxy support
      new Proxy({}, {})
      
      // Check for WeakMap support
      new WeakMap()
      
      // Check for Symbol support
      Symbol()
      
      // Check for async/await support
      eval('(async () => {})')
      
      return true
    } catch {
      return false
    }
  }

  private static checkCSSCustomProperties(): boolean {
    return window.CSS && window.CSS.supports && window.CSS.supports('--test', 'value')
  }

  private static checkLibraryConflicts(): string[] {
    const conflicts: string[] = []
    
    // Check for jQuery conflicts
    if (window.$ && window.$.fn && window.$.fn.jquery) {
      const jqVersion = window.$.fn.jquery
      if (jqVersion.startsWith('1.') || jqVersion.startsWith('2.')) {
        conflicts.push('jQuery (old version)')
      }
    }
    
    // Check for Bootstrap conflicts
    if (window.bootstrap) {
      conflicts.push('Bootstrap JS')
    }
    
    // Check for other Vue instances
    if (window.Vue && window.Vue.version && !window.Vue.version.startsWith('3.')) {
      conflicts.push('Vue 2.x')
    }
    
    return conflicts
  }

  private static async checkDataIntegrity(): Promise<Array<{ severity: 'error' | 'warning' | 'info'; message: string; messageAr: string }>> {
    const issues: Array<{ severity: 'error' | 'warning' | 'info'; message: string; messageAr: string }> = []
    
    try {
      // Check if Frappe data is accessible
      if (!window.frappe?.boot) {
        issues.push({
          severity: 'error',
          message: 'Frappe boot data not accessible',
          messageAr: 'بيانات تمهيد Frappe غير متاحة'
        })
      }
      
      // Check for required permissions
      if (window.frappe?.boot && !window.frappe.boot.user?.can_read) {
        issues.push({
          severity: 'warning',
          message: 'User permissions may be limited',
          messageAr: 'صلاحيات المستخدم قد تكون محدودة'
        })
      }
      
      // Check database connectivity
      if (window.frappe?.call) {
        try {
          await window.frappe.call({
            method: 'frappe.ping',
            args: {}
          })
        } catch (error) {
          issues.push({
            severity: 'error',
            message: 'Cannot connect to Frappe backend',
            messageAr: 'لا يمكن الاتصال بخادم Frappe'
          })
        }
      }
    } catch (error) {
      issues.push({
        severity: 'error',
        message: 'Data integrity check failed',
        messageAr: 'فشل فحص سلامة البيانات'
      })
    }
    
    return issues
  }
}

// Migration orchestrator
export class MigrationOrchestrator {
  private steps: MigrationStep[] = []
  private status: MigrationStatus
  private backups: Map<string, any> = new Map()
  private featureFlags = useFeatureFlags()

  constructor() {
    this.initializeMigrationSteps()
    this.status = {
      currentPhase: MigrationPhase.PREPARATION,
      completedSteps: [],
      failedSteps: [],
      totalSteps: this.steps.length,
      completedCount: 0,
      estimatedTimeRemaining: this.calculateTotalTime(),
      canRollback: false
    }
  }

  private initializeMigrationSteps(): void {
    this.steps = [
      {
        id: 'system_check',
        name: 'System Compatibility Check',
        nameAr: 'فحص توافق النظام',
        description: 'Verify system meets requirements for Vue 3 migration',
        descriptionAr: 'التحقق من أن النظام يلبي متطلبات ترحيل Vue 3',
        phase: MigrationPhase.PREPARATION,
        dependencies: [],
        estimatedTime: 5,
        riskLevel: 'low',
        rollbackAvailable: false,
        testingRequired: false,
        backupRequired: false,
        execute: async () => {
          const result = await SystemCompatibilityChecker.runFullCheck()
          return result.compatible
        },
        verify: async () => {
          const result = await SystemCompatibilityChecker.runFullCheck()
          return result.compatible
        }
      },
      {
        id: 'feature_flags_setup',
        name: 'Feature Flags Configuration',
        nameAr: 'تكوين علامات الميزات',
        description: 'Set up feature flags for controlled rollout',
        descriptionAr: 'إعداد علامات الميزات للنشر المتحكم به',
        phase: MigrationPhase.PREPARATION,
        dependencies: ['system_check'],
        estimatedTime: 10,
        riskLevel: 'low',
        rollbackAvailable: true,
        testingRequired: true,
        backupRequired: true,
        execute: async () => {
          try {
            // Enable foundation feature flags
            this.featureFlags.enable('vue3_buttons', { rolloutPercentage: 25 })
            this.featureFlags.enable('vue3_inputs', { rolloutPercentage: 15 })
            this.featureFlags.enable('modern_ui', { rolloutPercentage: 50 })
            return true
          } catch {
            return false
          }
        },
        rollback: async () => {
          this.featureFlags.disable('vue3_buttons')
          this.featureFlags.disable('vue3_inputs')
          this.featureFlags.disable('modern_ui')
          return true
        },
        verify: async () => {
          return this.featureFlags.isEnabled('modern_ui')
        }
      },
      {
        id: 'design_tokens_deployment',
        name: 'Deploy Design Token System',
        nameAr: 'نشر نظام رموز التصميم',
        description: 'Deploy CSS custom properties and design tokens',
        descriptionAr: 'نشر خصائص CSS المخصصة ورموز التصميم',
        phase: MigrationPhase.FOUNDATION,
        dependencies: ['feature_flags_setup'],
        estimatedTime: 15,
        riskLevel: 'medium',
        rollbackAvailable: true,
        testingRequired: true,
        backupRequired: true,
        execute: async () => {
          try {
            // Inject design tokens CSS
            const tokensCSS = await this.loadDesignTokens()
            this.injectCSS('design-tokens', tokensCSS)
            return true
          } catch {
            return false
          }
        },
        rollback: async () => {
          this.removeCSS('design-tokens')
          return true
        },
        verify: async () => {
          const style = getComputedStyle(document.documentElement)
          return style.getPropertyValue('--color-primary').trim() !== ''
        }
      },
      {
        id: 'button_component_migration',
        name: 'Migrate Button Components',
        nameAr: 'ترحيل مكونات الأزرار',
        description: 'Replace legacy buttons with Vue 3 Button components',
        descriptionAr: 'استبدال الأزرار التقليدية بمكونات Vue 3',
        phase: MigrationPhase.CORE_COMPONENTS,
        dependencies: ['design_tokens_deployment'],
        estimatedTime: 30,
        riskLevel: 'medium',
        rollbackAvailable: true,
        testingRequired: true,
        backupRequired: true,
        execute: async () => {
          try {
            this.featureFlags.enable('vue3_buttons', { rolloutPercentage: 50 })
            await new Promise(resolve => setTimeout(resolve, 1000)) // Allow bridge to process
            return bridge.getStats().successfulReplacements > 0
          } catch {
            return false
          }
        },
        rollback: async () => {
          this.featureFlags.disable('vue3_buttons')
          bridge.cleanup()
          return true
        },
        verify: async () => {
          return document.querySelectorAll('[data-vue-replaced="true"]').length > 0
        }
      },
      {
        id: 'input_component_migration',
        name: 'Migrate Input Components',
        nameAr: 'ترحيل مكونات الإدخال',
        description: 'Replace legacy inputs with Vue 3 Input components',
        descriptionAr: 'استبدال حقول الإدخال التقليدية بمكونات Vue 3',
        phase: MigrationPhase.CORE_COMPONENTS,
        dependencies: ['button_component_migration'],
        estimatedTime: 45,
        riskLevel: 'high',
        rollbackAvailable: true,
        testingRequired: true,
        backupRequired: true,
        execute: async () => {
          try {
            this.featureFlags.enable('vue3_inputs', { rolloutPercentage: 25 })
            await new Promise(resolve => setTimeout(resolve, 1000))
            return true
          } catch {
            return false
          }
        },
        rollback: async () => {
          this.featureFlags.disable('vue3_inputs')
          return true
        },
        verify: async () => {
          return this.featureFlags.isEnabled('vue3_inputs')
        }
      },
      {
        id: 'form_validation_migration',
        name: 'Deploy Form Validation System',
        nameAr: 'نشر نظام تحقق النماذج',
        description: 'Implement Vue 3 form validation with Arabic support',
        descriptionAr: 'تنفيذ نظام تحقق النماذج Vue 3 مع دعم العربية',
        phase: MigrationPhase.FORMS_AND_VALIDATION,
        dependencies: ['input_component_migration'],
        estimatedTime: 60,
        riskLevel: 'high',
        rollbackAvailable: true,
        testingRequired: true,
        backupRequired: true,
        execute: async () => {
          try {
            this.featureFlags.enable('form_validation', { rolloutPercentage: 10 })
            this.featureFlags.enable('arabic_support', { rolloutPercentage: 100 })
            return true
          } catch {
            return false
          }
        },
        rollback: async () => {
          this.featureFlags.disable('form_validation')
          return true
        },
        verify: async () => {
          return this.featureFlags.isEnabled('form_validation')
        }
      }
    ]
  }

  private calculateTotalTime(): number {
    return this.steps.reduce((total, step) => total + step.estimatedTime, 0)
  }

  private async loadDesignTokens(): Promise<string> {
    // In a real implementation, this would load the actual CSS file
    return `
      :root {
        --color-primary: #2563eb;
        --color-primary-50: #eff6ff;
        --color-primary-600: #2563eb;
        --color-primary-foreground: #ffffff;
        --spacing-1: 0.25rem;
        --spacing-2: 0.5rem;
        --spacing-3: 0.75rem;
        --spacing-4: 1rem;
        --radius-sm: 0.125rem;
        --radius-md: 0.375rem;
        --radius-lg: 0.5rem;
        --font-weight-medium: 500;
        --font-weight-semibold: 600;
        --transition-colors: all 0.2s ease;
      }
    `
  }

  private injectCSS(id: string, css: string): void {
    const existing = document.getElementById(id)
    if (existing) {
      existing.remove()
    }

    const style = document.createElement('style')
    style.id = id
    style.textContent = css
    document.head.appendChild(style)
  }

  private removeCSS(id: string): void {
    const element = document.getElementById(id)
    if (element) {
      element.remove()
    }
  }

  public async runMigration(): Promise<MigrationStatus> {
    console.log('🚀 Starting Universal Workshop Vue 3 migration...')

    for (const step of this.steps) {
      try {
        console.log(`⏳ Executing: ${step.name}`)
        
        // Create backup if required
        if (step.backupRequired) {
          await this.createBackup(step.id)
        }

        // Execute the migration step
        const success = await step.execute()
        
        if (success) {
          // Verify the step completed correctly
          const verified = await step.verify()
          
          if (verified) {
            this.status.completedSteps.push(step.id)
            this.status.completedCount++
            this.status.canRollback = step.rollbackAvailable
            console.log(`✅ Completed: ${step.name}`)
          } else {
            throw new Error(`Verification failed for step: ${step.name}`)
          }
        } else {
          throw new Error(`Execution failed for step: ${step.name}`)
        }
      } catch (error) {
        console.error(`❌ Failed: ${step.name}`, error)
        this.status.failedSteps.push(step.id)
        this.status.lastError = (error as Error).message

        // Attempt rollback if available
        if (step.rollback) {
          try {
            await step.rollback()
            console.log(`🔄 Rolled back: ${step.name}`)
          } catch (rollbackError) {
            console.error(`💥 Rollback failed: ${step.name}`, rollbackError)
          }
        }

        // Stop migration on critical failures
        if (step.riskLevel === 'high') {
          break
        }
      }

      // Update remaining time estimate
      const completedTime = this.status.completedSteps.reduce((total, stepId) => {
        const step = this.steps.find(s => s.id === stepId)
        return total + (step?.estimatedTime || 0)
      }, 0)
      this.status.estimatedTimeRemaining = this.calculateTotalTime() - completedTime
    }

    // Update current phase based on completed steps
    this.updateCurrentPhase()

    console.log('🏁 Migration completed!')
    console.log(`✅ Successful steps: ${this.status.completedSteps.length}`)
    console.log(`❌ Failed steps: ${this.status.failedSteps.length}`)

    return this.status
  }

  private async createBackup(stepId: string): Promise<void> {
    // Create backup of current state before executing step
    const backup = {
      timestamp: new Date().toISOString(),
      featureFlags: this.featureFlags.getAll(),
      domState: document.documentElement.outerHTML,
      localStorage: { ...localStorage },
      sessionStorage: { ...sessionStorage }
    }
    
    this.backups.set(stepId, backup)
  }

  private updateCurrentPhase(): void {
    const phases = [
      MigrationPhase.PREPARATION,
      MigrationPhase.FOUNDATION,
      MigrationPhase.CORE_COMPONENTS,
      MigrationPhase.FORMS_AND_VALIDATION,
      MigrationPhase.COMPLETE_INTEGRATION
    ]

    for (const phase of phases) {
      const phaseSteps = this.steps.filter(step => step.phase === phase)
      const completedPhaseSteps = phaseSteps.filter(step => 
        this.status.completedSteps.includes(step.id)
      )

      if (completedPhaseSteps.length === phaseSteps.length) {
        this.status.currentPhase = phase
      } else {
        break
      }
    }
  }

  public async rollbackToStep(stepId: string): Promise<boolean> {
    const stepIndex = this.steps.findIndex(step => step.id === stepId)
    if (stepIndex === -1) return false

    const stepsToRollback = this.steps.slice(stepIndex).reverse()
    
    for (const step of stepsToRollback) {
      if (step.rollback && this.status.completedSteps.includes(step.id)) {
        try {
          await step.rollback()
          this.status.completedSteps = this.status.completedSteps.filter(id => id !== step.id)
          console.log(`🔄 Rolled back: ${step.name}`)
        } catch (error) {
          console.error(`💥 Rollback failed: ${step.name}`, error)
          return false
        }
      }
    }

    this.updateCurrentPhase()
    return true
  }

  public getStatus(): MigrationStatus {
    return { ...this.status }
  }

  public getSteps(): MigrationStep[] {
    return [...this.steps]
  }
}

// Export singleton instance
export const migrationOrchestrator = new MigrationOrchestrator()

export default MigrationOrchestrator