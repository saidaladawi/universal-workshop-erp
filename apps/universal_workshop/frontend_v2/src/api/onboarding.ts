/**
 * Onboarding API Integration
 * Connects Vue.js frontend with Frappe backend APIs
 */

import frappe from './frappe-adapter'

export interface OnboardingProgress {
  exists: boolean
  current_step: number
  completed_steps: string[]
  data: Record<string, any>
  progress_id: string | null
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
}

export interface StepSaveResult {
  success: boolean
  message?: string
  errors?: string[]
  next_step?: string
  progress_percentage?: number
}

export interface OnboardingCompletionResult {
  success: boolean
  message?: string
  workshop_profile?: string
  workshop_code?: string
  license_mode?: boolean
  errors?: string[]
}

export interface StepField {
  fieldname: string
  label: string
  fieldtype: string
  reqd?: number
  options?: string
  description?: string
  default?: string
}

export class OnboardingAPI {
  /**
   * Check if user has existing onboarding progress
   */
  static async getUserProgress(): Promise<OnboardingProgress> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.get_user_onboarding_progress'
      )
      
      if (response.message) {
        return {
          exists: true,
          current_step: response.message.current_step || 0,
          completed_steps: response.message.completed_steps || [],
          data: response.message.data || {},
          progress_id: response.message.progress_id
        }
      }
      
      return {
        exists: false,
        current_step: 0,
        completed_steps: [],
        data: {},
        progress_id: null
      }
    } catch (error) {
      console.error('Failed to get user progress:', error)
      throw new Error('Failed to retrieve onboarding progress')
    }
  }

  /**
   * Start new onboarding wizard session
   */
  static async startWizard(): Promise<{ success: boolean; progress_id: string; message?: string }> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard'
      )
      
      if (response.message?.success) {
        return {
          success: true,
          progress_id: response.message.progress_id,
          message: response.message.message
        }
      }
      
      throw new Error(response.message?.message || 'Failed to start wizard')
    } catch (error) {
      console.error('Failed to start wizard:', error)
      throw error
    }
  }

  /**
   * Validate step data
   */
  static async validateStep(stepName: string, data: Record<string, any>): Promise<ValidationResult> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.validate_step_data',
        {
          step_name: stepName,
          data: JSON.stringify(data)
        }
      )
      
      return {
        valid: response.message?.valid || false,
        errors: response.message?.errors || []
      }
    } catch (error) {
      console.error('Validation failed:', error)
      return {
        valid: false,
        errors: ['Validation request failed']
      }
    }
  }

  /**
   * Save step data
   */
  static async saveStep(
    progressId: string, 
    stepName: string, 
    data: Record<string, any>
  ): Promise<StepSaveResult> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.save_step_data',
        {
          progress_id: progressId,
          step_name: stepName,
          data: JSON.stringify(data)
        }
      )
      
      return {
        success: response.message?.success || false,
        message: response.message?.message,
        errors: response.message?.errors,
        next_step: response.message?.next_step,
        progress_percentage: response.message?.progress_percentage
      }
    } catch (error) {
      console.error('Failed to save step:', error)
      return {
        success: false,
        errors: ['Failed to save step data']
      }
    }
  }

  /**
   * Complete onboarding process
   */
  static async completeOnboarding(progressId: string): Promise<OnboardingCompletionResult> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.complete_onboarding',
        {
          progress_id: progressId
        }
      )
      
      return {
        success: response.message?.success || false,
        message: response.message?.message,
        workshop_profile: response.message?.workshop_profile,
        workshop_code: response.message?.workshop_code,
        license_mode: response.message?.license_mode,
        errors: response.message?.errors
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error)
      return {
        success: false,
        errors: ['Failed to complete onboarding process']
      }
    }
  }

  /**
   * Get field configuration for a specific step
   */
  static async getStepFields(stepName: string): Promise<StepField[]> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.get_onboarding_step_fields',
        {
          step_name: stepName
        }
      )
      
      return response.message || []
    } catch (error) {
      console.error('Failed to get step fields:', error)
      return []
    }
  }

  /**
   * Cancel/rollback onboarding process
   */
  static async rollbackOnboarding(
    progressId: string, 
    reason: string = 'User cancelled'
  ): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await frappe.call(
        'universal_workshop.workshop_management.api.onboarding_wizard.rollback_onboarding',
        {
          progress_id: progressId,
          reason: reason
        }
      )
      
      return {
        success: response.message?.success || false,
        message: response.message?.message
      }
    } catch (error) {
      console.error('Failed to rollback onboarding:', error)
      return {
        success: false,
        message: 'Failed to cancel onboarding'
      }
    }
  }

  /**
   * Check if system is in license mode (admin-only setup)
   */
  static async isLicenseMode(): Promise<boolean> {
    try {
      const response = await frappe.call(
        'frappe.client.get_single_value',
        {
          doctype: 'System Settings',
          field: 'license_has_workshop_data'
        }
      )
      
      return response.message === '1'
    } catch (error) {
      console.error('Failed to check license mode:', error)
      return false
    }
  }

  /**
   * Get available workshop types
   */
  static getWorkshopTypes(): string[] {
    return [
      'General Repair',
      'Body Work',
      'Electrical',
      'Engine Specialist',
      'Tire Services',
      'Painting',
      'Air Conditioning'
    ]
  }

  /**
   * Get Oman governorates
   */
  static getOmanGovernorates(): string[] {
    return [
      'Muscat',
      'Dhofar',
      'Al Batinah North',
      'Al Batinah South',
      'Al Buraimi',
      'Al Dakhiliyah',
      'Al Dhahirah',
      'Al Sharqiyah North',
      'Al Sharqiyah South',
      'Al Wusta',
      'Musandam'
    ]
  }

  /**
   * Get weekend day options
   */
  static getWeekendOptions(): Array<{ value: string; label: string }> {
    return [
      { value: 'Friday-Saturday', label: 'Friday - Saturday' },
      { value: 'Saturday-Sunday', label: 'Saturday - Sunday' },
      { value: 'Sunday-Monday', label: 'Sunday - Monday' }
    ]
  }

  /**
   * Get certification levels
   */
  static getCertificationLevels(): string[] {
    return ['Basic', 'Intermediate', 'Advanced', 'Professional']
  }

  /**
   * Get supported currencies
   */
  static getCurrencies(): Array<{ value: string; label: string }> {
    return [
      { value: 'OMR', label: 'Omani Rial (OMR)' },
      { value: 'USD', label: 'US Dollar (USD)' },
      { value: 'EUR', label: 'Euro (EUR)' }
    ]
  }

  /**
   * Validate Oman phone number format
   */
  static validateOmanPhone(phone: string): boolean {
    const cleaned = phone.replace(/\s+/g, '')
    return /^\+968\d{8}$/.test(cleaned)
  }

  /**
   * Format Oman phone number
   */
  static formatOmanPhone(phone: string): string {
    let cleaned = phone.replace(/\D/g, '')
    
    if (cleaned.startsWith('968')) {
      cleaned = '+' + cleaned
    } else if (cleaned.length === 8) {
      cleaned = '+968' + cleaned
    } else if (!cleaned.startsWith('+968')) {
      cleaned = '+968' + cleaned.slice(-8)
    }
    
    return cleaned
  }

  /**
   * Validate Oman business license format (7 digits)
   */
  static validateBusinessLicense(license: string): boolean {
    return /^\d{7}$/.test(license)
  }

  /**
   * Validate Oman VAT number format
   */
  static validateVATNumber(vat: string): boolean {
    const cleaned = vat.replace(/\s+/g, '').toUpperCase()
    return /^OM\d{15}$/.test(cleaned)
  }

  /**
   * Validate Oman IBAN format
   */
  static validateIBAN(iban: string): boolean {
    const cleaned = iban.replace(/\s+/g, '').toUpperCase()
    return /^OM\d{21}$/.test(cleaned)
  }

  /**
   * Validate email address
   */
  static validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  /**
   * Validate URL format
   */
  static validateURL(url: string): boolean {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  /**
   * Validate password strength
   */
  static validatePassword(password: string): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long')
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter')
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter')
    }
    
    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one number')
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }

  /**
   * Check if Arabic text contains Arabic characters
   */
  static validateArabicText(text: string): boolean {
    return /[\u0600-\u06FF]/.test(text)
  }

  /**
   * Auto-detect text direction (RTL for Arabic)
   */
  static getTextDirection(text: string): 'ltr' | 'rtl' {
    return this.validateArabicText(text) ? 'rtl' : 'ltr'
  }
}

// Re-export for convenience
export default OnboardingAPI