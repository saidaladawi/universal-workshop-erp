/**
 * Advanced Security Manager - Universal Workshop Frontend V2
 * Comprehensive security system with threat protection, data encryption,
 * multi-factor authentication, and Arabic security notifications.
 */

import { ref, computed, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import { useLocalizationStore } from '@/stores/localization'
import { useNotificationStore } from '@/stores/notification'

// Types
interface SecurityConfig {
  encryptionKey: string
  apiEndpoint: string
  maxLoginAttempts: number
  sessionTimeout: number
  requireMFA: boolean
  allowedDomains: string[]
  securityHeaders: Record<string, string>
}

interface SecurityThreat {
  id: string
  type: ThreatType
  severity: 'low' | 'medium' | 'high' | 'critical'
  source: string
  timestamp: Date
  description: string
  descriptionAr: string
  blocked: boolean
  details: Record<string, any>
}

type ThreatType = 
  | 'sql_injection'
  | 'xss_attempt'
  | 'csrf_attack'
  | 'brute_force'
  | 'suspicious_activity'
  | 'data_breach_attempt'
  | 'unauthorized_access'
  | 'malicious_upload'

interface SecurityEvent {
  id: string
  userId: string
  action: SecurityAction
  timestamp: Date
  ipAddress: string
  userAgent: string
  location?: GeoLocation
  success: boolean
  details: Record<string, any>
}

type SecurityAction = 
  | 'login'
  | 'logout'
  | 'password_change'
  | 'mfa_setup'
  | 'mfa_verify'
  | 'data_access'
  | 'data_export'
  | 'admin_action'
  | 'api_call'

interface GeoLocation {
  country: string
  city: string
  latitude: number
  longitude: number
}

interface MFAConfig {
  enabled: boolean
  methods: MFAMethod[]
  backupCodes: string[]
  trustedDevices: TrustedDevice[]
}

interface MFAMethod {
  type: 'totp' | 'sms' | 'email' | 'hardware_key'
  enabled: boolean
  verified: boolean
  setupDate: Date
  lastUsed?: Date
}

interface TrustedDevice {
  id: string
  name: string
  fingerprint: string
  addedDate: Date
  lastUsed: Date
  location: GeoLocation
}

interface SecurityAudit {
  id: string
  timestamp: Date
  type: 'vulnerability_scan' | 'penetration_test' | 'security_review'
  findings: SecurityFinding[]
  score: number
  recommendations: string[]
}

interface SecurityFinding {
  id: string
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  category: string
  description: string
  descriptionAr: string
  remediation: string
  remediationAr: string
  fixed: boolean
}

interface EncryptionResult {
  encrypted: string
  iv: string
  salt: string
}

export class AdvancedSecurityManager {
  private config: SecurityConfig
  private encryptionKey: CryptoKey | null = null
  private securityThreats = ref<SecurityThreat[]>([])
  private securityEvents = ref<SecurityEvent[]>([])
  private mfaConfig = ref<MFAConfig>({
    enabled: false,
    methods: [],
    backupCodes: [],
    trustedDevices: []
  })
  private isInitialized = ref(false)
  private securityScore = ref(0)
  private threatLevel = ref<'low' | 'medium' | 'high' | 'critical'>('low')

  // Stores
  private userStore = useUserStore()
  private localizationStore = useLocalizationStore()
  private notificationStore = useNotificationStore()

  // Security monitoring
  private securityMonitor = reactive({
    loginAttempts: new Map<string, number>(),
    suspiciousIPs: new Set<string>(),
    blockedRequests: 0,
    lastThreatDetection: null as Date | null,
    activeSessions: new Map<string, any>()
  })

  constructor(config: SecurityConfig) {
    this.config = config
    this.initializeEncryption()
    this.setupSecurityHeaders()
    this.startSecurityMonitoring()
  }

  // Initialize encryption
  private async initializeEncryption(): Promise<void> {
    try {
      // Import encryption key
      const keyData = new TextEncoder().encode(this.config.encryptionKey)
      const hashedKey = await crypto.subtle.digest('SHA-256', keyData)
      
      this.encryptionKey = await crypto.subtle.importKey(
        'raw',
        hashedKey,
        { name: 'AES-GCM' },
        false,
        ['encrypt', 'decrypt']
      )
    } catch (error) {
      console.error('Failed to initialize encryption:', error)
      throw new Error('Encryption initialization failed')
    }
  }

  // Setup security headers
  private setupSecurityHeaders(): void {
    // Add security headers to all requests
    const originalFetch = window.fetch
    window.fetch = async (input, init = {}) => {
      const headers = new Headers(init.headers)
      
      // Add security headers
      Object.entries(this.config.securityHeaders).forEach(([key, value]) => {
        headers.set(key, value)
      })

      // Add CSRF token
      const csrfToken = this.getCSRFToken()
      if (csrfToken) {
        headers.set('X-CSRF-Token', csrfToken)
      }

      // Add request fingerprint
      const fingerprint = await this.generateRequestFingerprint()
      headers.set('X-Request-Fingerprint', fingerprint)

      return originalFetch(input, {
        ...init,
        headers
      })
    }
  }

  // Start security monitoring
  private startSecurityMonitoring(): void {
    // Monitor failed login attempts
    this.monitorLoginAttempts()
    
    // Detect suspicious activity
    this.detectSuspiciousActivity()
    
    // Check for XSS attempts
    this.monitorXSSAttempts()
    
    // Monitor data access patterns
    this.monitorDataAccess()
    
    // Periodic security checks
    setInterval(() => {
      this.performSecurityCheck()
    }, 60000) // Every minute
  }

  // Encrypt sensitive data
  async encryptData(data: string): Promise<EncryptionResult> {
    if (!this.encryptionKey) {
      throw new Error('Encryption not initialized')
    }

    try {
      // Generate IV and salt
      const iv = crypto.getRandomValues(new Uint8Array(12))
      const salt = crypto.getRandomValues(new Uint8Array(16))
      
      // Encode data
      const encodedData = new TextEncoder().encode(data)
      
      // Encrypt
      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        this.encryptionKey,
        encodedData
      )

      return {
        encrypted: this.arrayBufferToBase64(encrypted),
        iv: this.arrayBufferToBase64(iv),
        salt: this.arrayBufferToBase64(salt)
      }
    } catch (error) {
      console.error('Encryption failed:', error)
      throw new Error('Data encryption failed')
    }
  }

  // Decrypt sensitive data
  async decryptData(encryptionResult: EncryptionResult): Promise<string> {
    if (!this.encryptionKey) {
      throw new Error('Encryption not initialized')
    }

    try {
      // Convert from base64
      const encrypted = this.base64ToArrayBuffer(encryptionResult.encrypted)
      const iv = this.base64ToArrayBuffer(encryptionResult.iv)
      
      // Decrypt
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        this.encryptionKey,
        encrypted
      )

      return new TextDecoder().decode(decrypted)
    } catch (error) {
      console.error('Decryption failed:', error)
      throw new Error('Data decryption failed')
    }
  }

  // Setup Multi-Factor Authentication
  async setupMFA(method: 'totp' | 'sms' | 'email'): Promise<{ secret?: string; qrCode?: string }> {
    try {
      const user = this.userStore.currentUser
      if (!user) throw new Error('User not authenticated')

      const response = await fetch(`${this.config.apiEndpoint}/security/mfa/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ method })
      })

      if (!response.ok) {
        throw new Error('MFA setup failed')
      }

      const result = await response.json()
      
      // Update MFA config
      const existingMethod = this.mfaConfig.value.methods.find(m => m.type === method)
      if (existingMethod) {
        existingMethod.enabled = true
        existingMethod.setupDate = new Date()
      } else {
        this.mfaConfig.value.methods.push({
          type: method,
          enabled: true,
          verified: false,
          setupDate: new Date()
        })
      }

      this.logSecurityEvent('mfa_setup', true, { method })
      
      return result
    } catch (error) {
      console.error('MFA setup failed:', error)
      this.logSecurityEvent('mfa_setup', false, { method, error: error.message })
      throw error
    }
  }

  // Verify MFA code
  async verifyMFA(method: 'totp' | 'sms' | 'email', code: string): Promise<boolean> {
    try {
      const user = this.userStore.currentUser
      if (!user) throw new Error('User not authenticated')

      const response = await fetch(`${this.config.apiEndpoint}/security/mfa/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ method, code })
      })

      const result = await response.json()
      const success = response.ok && result.verified

      if (success) {
        // Update method as verified
        const mfaMethod = this.mfaConfig.value.methods.find(m => m.type === method)
        if (mfaMethod) {
          mfaMethod.verified = true
          mfaMethod.lastUsed = new Date()
        }
      }

      this.logSecurityEvent('mfa_verify', success, { method })
      
      return success
    } catch (error) {
      console.error('MFA verification failed:', error)
      this.logSecurityEvent('mfa_verify', false, { method, error: error.message })
      return false
    }
  }

  // Detect and block threats
  private detectThreat(type: ThreatType, source: string, details: any): void {
    const threat: SecurityThreat = {
      id: this.generateSecurityId(),
      type,
      severity: this.calculateThreatSeverity(type, details),
      source,
      timestamp: new Date(),
      description: this.getThreatDescription(type, false),
      descriptionAr: this.getThreatDescription(type, true),
      blocked: this.shouldBlockThreat(type, details),
      details
    }

    this.securityThreats.value.unshift(threat)
    
    // Update threat level
    this.updateThreatLevel()
    
    // Take action if needed
    if (threat.blocked) {
      this.blockThreat(threat)
    }
    
    // Notify user if critical
    if (threat.severity === 'critical') {
      this.notifySecurityThreat(threat)
    }
    
    // Log threat
    console.warn('Security threat detected:', threat)
  }

  // Monitor login attempts
  private monitorLoginAttempts(): void {
    const originalLogin = this.userStore.login
    this.userStore.login = async (...args) => {
      const ip = await this.getCurrentIP()
      const attempts = this.securityMonitor.loginAttempts.get(ip) || 0
      
      try {
        const result = await originalLogin.apply(this.userStore, args)
        
        // Reset attempts on successful login
        this.securityMonitor.loginAttempts.delete(ip)
        this.logSecurityEvent('login', true, { ip })
        
        return result
      } catch (error) {
        // Increment failed attempts
        this.securityMonitor.loginAttempts.set(ip, attempts + 1)
        this.logSecurityEvent('login', false, { ip, attempts: attempts + 1 })
        
        // Detect brute force
        if (attempts + 1 >= this.config.maxLoginAttempts) {
          this.detectThreat('brute_force', ip, { attempts: attempts + 1 })
        }
        
        throw error
      }
    }
  }

  // Detect XSS attempts
  private monitorXSSAttempts(): void {
    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<iframe[^>]*>.*?<\/iframe>/gi,
      /eval\s*\(/gi,
      /document\.cookie/gi,
      /window\.location/gi
    ]

    // Monitor form inputs
    document.addEventListener('input', (event) => {
      const target = event.target as HTMLInputElement
      if (target && target.value) {
        for (const pattern of xssPatterns) {
          if (pattern.test(target.value)) {
            this.detectThreat('xss_attempt', 'user_input', {
              element: target.name || target.id,
              value: target.value,
              pattern: pattern.source
            })
            break
          }
        }
      }
    })
  }

  // Monitor data access
  private monitorDataAccess(): void {
    const sensitiveEndpoints = [
      '/api/customers',
      '/api/financial',
      '/api/reports',
      '/api/admin'
    ]

    const originalFetch = window.fetch
    window.fetch = async (input, init) => {
      const url = typeof input === 'string' ? input : input.url
      
      // Check if accessing sensitive data
      const isSensitive = sensitiveEndpoints.some(endpoint => url.includes(endpoint))
      
      if (isSensitive) {
        this.logSecurityEvent('data_access', true, { url, method: init?.method || 'GET' })
      }
      
      return originalFetch(input, init)
    }
  }

  // Perform periodic security check
  private async performSecurityCheck(): Promise<void> {
    try {
      // Check session validity
      await this.checkSessionSecurity()
      
      // Update security score
      this.updateSecurityScore()
      
      // Clean old threats
      this.cleanOldThreats()
      
      // Check for security updates
      await this.checkSecurityUpdates()
    } catch (error) {
      console.error('Security check failed:', error)
    }
  }

  // Check session security
  private async checkSessionSecurity(): Promise<void> {
    const user = this.userStore.currentUser
    if (!user) return

    const sessionAge = Date.now() - user.loginTime
    if (sessionAge > this.config.sessionTimeout) {
      // Session expired
      this.logSecurityEvent('logout', true, { reason: 'session_timeout' })
      await this.userStore.logout()
      
      this.notificationStore.showWarning(
        this.localizationStore.preferArabic
          ? 'انتهت صلاحية الجلسة، يرجى تسجيل الدخول مرة أخرى'
          : 'Session expired, please login again'
      )
    }
  }

  // Update security score
  private updateSecurityScore(): void {
    let score = 100

    // Deduct for recent threats
    const recentThreats = this.securityThreats.value.filter(
      threat => Date.now() - threat.timestamp.getTime() < 24 * 60 * 60 * 1000
    )
    score -= recentThreats.length * 5

    // Deduct for failed login attempts
    const totalFailedAttempts = Array.from(this.securityMonitor.loginAttempts.values())
      .reduce((sum, attempts) => sum + attempts, 0)
    score -= totalFailedAttempts * 2

    // Add for MFA enabled
    if (this.mfaConfig.value.enabled) {
      score += 20
    }

    // Add for recent security updates
    // ... additional scoring logic

    this.securityScore.value = Math.max(0, Math.min(100, score))
  }

  // Update threat level
  private updateThreatLevel(): void {
    const recentThreats = this.securityThreats.value.filter(
      threat => Date.now() - threat.timestamp.getTime() < 60 * 60 * 1000 // Last hour
    )

    const criticalThreats = recentThreats.filter(t => t.severity === 'critical').length
    const highThreats = recentThreats.filter(t => t.severity === 'high').length

    if (criticalThreats > 0) {
      this.threatLevel.value = 'critical'
    } else if (highThreats > 2) {
      this.threatLevel.value = 'high'
    } else if (recentThreats.length > 5) {
      this.threatLevel.value = 'medium'
    } else {
      this.threatLevel.value = 'low'
    }
  }

  // Calculate threat severity
  private calculateThreatSeverity(type: ThreatType, details: any): 'low' | 'medium' | 'high' | 'critical' {
    const severityMap: Record<ThreatType, 'low' | 'medium' | 'high' | 'critical'> = {
      sql_injection: 'critical',
      xss_attempt: 'high',
      csrf_attack: 'high',
      brute_force: 'medium',
      suspicious_activity: 'medium',
      data_breach_attempt: 'critical',
      unauthorized_access: 'high',
      malicious_upload: 'high'
    }

    let baseSeverity = severityMap[type] || 'low'

    // Adjust based on details
    if (details.attempts && details.attempts > 10) {
      baseSeverity = 'critical'
    }

    return baseSeverity
  }

  // Get threat description
  private getThreatDescription(type: ThreatType, arabic: boolean): string {
    const descriptions = {
      sql_injection: {
        en: 'SQL injection attempt detected',
        ar: 'تم اكتشاف محاولة حقن SQL'
      },
      xss_attempt: {
        en: 'Cross-site scripting attempt detected',
        ar: 'تم اكتشاف محاولة تنفيذ سكريبت ضار'
      },
      brute_force: {
        en: 'Brute force attack detected',
        ar: 'تم اكتشاف هجوم القوة الغاشمة'
      },
      // ... more descriptions
    }

    const desc = descriptions[type as keyof typeof descriptions]
    return arabic ? desc?.ar || desc?.en || 'Unknown threat' : desc?.en || 'Unknown threat'
  }

  // Block threat
  private blockThreat(threat: SecurityThreat): void {
    // Add IP to blocked list
    this.securityMonitor.suspiciousIPs.add(threat.source)
    
    // Increment blocked requests counter
    this.securityMonitor.blockedRequests++
    
    // Log blocking action
    console.warn(`Blocked security threat: ${threat.type} from ${threat.source}`)
  }

  // Notify security threat
  private notifySecurityThreat(threat: SecurityThreat): void {
    this.notificationStore.showError(
      this.localizationStore.preferArabic
        ? `تهديد أمني: ${threat.descriptionAr}`
        : `Security threat: ${threat.description}`
    )
  }

  // Log security event
  private logSecurityEvent(action: SecurityAction, success: boolean, details: any): void {
    const event: SecurityEvent = {
      id: this.generateSecurityId(),
      userId: this.userStore.currentUser?.id || 'anonymous',
      action,
      timestamp: new Date(),
      ipAddress: details.ip || 'unknown',
      userAgent: navigator.userAgent,
      success,
      details
    }

    this.securityEvents.value.unshift(event)
    
    // Keep only last 1000 events
    if (this.securityEvents.value.length > 1000) {
      this.securityEvents.value = this.securityEvents.value.slice(0, 1000)
    }
  }

  // Utility methods
  private async getCurrentIP(): Promise<string> {
    try {
      const response = await fetch('https://api.ipify.org?format=json')
      const data = await response.json()
      return data.ip
    } catch {
      return 'unknown'
    }
  }

  private async generateRequestFingerprint(): Promise<string> {
    const data = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timestamp: Date.now()
    }
    
    const encoder = new TextEncoder()
    const dataBuffer = encoder.encode(JSON.stringify(data))
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
    
    return this.arrayBufferToBase64(hashBuffer)
  }

  private getCSRFToken(): string | null {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || null
  }

  private generateSecurityId(): string {
    return `sec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
  }

  private cleanOldThreats(): void {
    const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000 // 7 days
    this.securityThreats.value = this.securityThreats.value.filter(
      threat => threat.timestamp.getTime() > cutoff
    )
  }

  private async checkSecurityUpdates(): Promise<void> {
    // Implementation for checking security updates
  }

  private shouldBlockThreat(type: ThreatType, details: any): boolean {
    const blockableThreats: ThreatType[] = [
      'sql_injection',
      'xss_attempt',
      'brute_force',
      'data_breach_attempt'
    ]
    
    return blockableThreats.includes(type)
  }

  // Public API
  async initialize(): Promise<boolean> {
    try {
      await this.initializeEncryption()
      this.isInitialized.value = true
      return true
    } catch (error) {
      console.error('Security manager initialization failed:', error)
      return false
    }
  }

  // Getters
  get threats() {
    return computed(() => this.securityThreats.value)
  }

  get events() {
    return computed(() => this.securityEvents.value)
  }

  get score() {
    return computed(() => this.securityScore.value)
  }

  get currentThreatLevel() {
    return computed(() => this.threatLevel.value)
  }

  get mfaSettings() {
    return computed(() => this.mfaConfig.value)
  }

  get isSecure() {
    return computed(() => this.securityScore.value >= 80 && this.threatLevel.value !== 'critical')
  }
}

// Export composable
export function useAdvancedSecurity(config?: SecurityConfig) {
  if (!config) {
    throw new Error('Security config is required')
  }

  const manager = new AdvancedSecurityManager(config)

  return {
    manager,
    initialize: () => manager.initialize(),
    encryptData: (data: string) => manager.encryptData(data),
    decryptData: (encrypted: EncryptionResult) => manager.decryptData(encrypted),
    setupMFA: (method: 'totp' | 'sms' | 'email') => manager.setupMFA(method),
    verifyMFA: (method: 'totp' | 'sms' | 'email', code: string) => manager.verifyMFA(method, code),
    
    // Reactive properties
    threats: manager.threats,
    events: manager.events,
    securityScore: manager.score,
    threatLevel: manager.currentThreatLevel,
    mfaSettings: manager.mfaSettings,
    isSecure: manager.isSecure
  }
} 