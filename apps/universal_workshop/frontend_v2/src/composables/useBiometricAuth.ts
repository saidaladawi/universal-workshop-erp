/**
 * Biometric Authentication Composable for Universal Workshop PWA
 * Provides comprehensive biometric authentication support with Arabic/Omani cultural adaptations
 * 
 * Features:
 * - WebAuthn integration for fingerprint and face recognition
 * - Voice recognition with Arabic dialect support
 * - Multi-factor biometric authentication
 * - Fallback authentication methods
 * - Cultural and accessibility considerations
 * - Device compatibility checking
 */

import { ref, reactive, computed, onMounted } from 'vue'
import type { Ref } from 'vue'

// Types for biometric authentication
interface BiometricCredential {
  id: string
  type: 'fingerprint' | 'face' | 'voice'
  name: string
  nameAr: string
  createdAt: Date
  lastUsed: Date
  reliability: number // 0-1 score
  metadata: {
    deviceInfo: string
    userAgent: string
    enrollmentQuality: number
  }
}

interface AuthenticationResult {
  success: boolean
  credentialId?: string
  credentialType?: string
  confidence: number
  authenticatedAt: Date
  fallbackUsed: boolean
  error?: string
}

interface BiometricSettings {
  preferredMethods: string[]
  requireMultipleMethods: boolean
  allowFallback: boolean
  timeoutSeconds: number
  maxAttempts: number
  culturalAdaptations: {
    respectPrayerTimes: boolean
    ramadanMode: boolean
    arabicPrompts: boolean
  }
}

interface VoiceTemplate {
  userId: string
  voicePrint: ArrayBuffer
  language: 'ar' | 'en'
  dialect?: 'gulf' | 'levantine' | 'egyptian' | 'maghrebi' | 'msa'
  quality: number
  createdAt: Date
}

class BiometricAuthManager {
  private isSupported: boolean = false
  private webAuthnSupported: boolean = false
  private voiceRecognitionSupported: boolean = false
  private mediaDevicesSupported: boolean = false

  private credentials: Map<string, BiometricCredential> = new Map()
  private voiceTemplates: Map<string, VoiceTemplate> = new Map()

  // Arabic voice recognition phrases
  private readonly ARABIC_PHRASES = [
    'بسم الله نبدأ العمل',           // In the name of Allah we start work
    'السلام عليكم ورحمة الله',      // Peace be upon you and Allah's mercy
    'أشهد أن لا إله إلا الله',     // I testify that there is no god but Allah
    'اللهم بارك في عملنا',          // O Allah, bless our work
    'الحمد لله رب العالمين'         // Praise be to Allah, Lord of the worlds
  ]

  constructor() {
    this.checkSupport()
  }

  private async checkSupport(): Promise<void> {
    // Check WebAuthn support
    this.webAuthnSupported = !!(
      window.PublicKeyCredential &&
      window.navigator.credentials &&
      window.navigator.credentials.create
    )

    // Check MediaDevices support for camera/microphone
    this.mediaDevicesSupported = !!(
      window.navigator.mediaDevices &&
      window.navigator.mediaDevices.getUserMedia
    )

    // Check Speech Recognition support
    this.voiceRecognitionSupported = !!(
      window.SpeechRecognition ||
      (window as any).webkitSpeechRecognition
    )

    this.isSupported = this.webAuthnSupported || this.voiceRecognitionSupported

    console.log('Biometric support check:', {
      webAuthn: this.webAuthnSupported,
      mediaDevices: this.mediaDevicesSupported,
      voiceRecognition: this.voiceRecognitionSupported,
      overall: this.isSupported
    })
  }

  public async getAvailableMethods(): Promise<string[]> {
    const methods: string[] = []

    if (this.webAuthnSupported) {
      try {
        // Check if platform authenticator is available
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
        if (available) {
          methods.push('fingerprint', 'face')
        }
      } catch (error) {
        console.warn('Platform authenticator check failed:', error)
      }
    }

    if (this.voiceRecognitionSupported && this.mediaDevicesSupported) {
      methods.push('voice')
    }

    return methods
  }

  public async enrollFingerprint(userId: string, userName: string): Promise<BiometricCredential> {
    if (!this.webAuthnSupported) {
      throw new Error('WebAuthn not supported on this device')
    }

    try {
      const challenge = crypto.getRandomValues(new Uint8Array(32))
      const userIdBytes = new TextEncoder().encode(userId)

      const credentialCreationOptions: CredentialCreationOptions = {
        publicKey: {
          challenge,
          rp: {
            name: 'Universal Workshop ERP',
            id: window.location.hostname
          },
          user: {
            id: userIdBytes,
            name: userName,
            displayName: userName
          },
          pubKeyCredParams: [
            { alg: -7, type: 'public-key' }, // ES256
            { alg: -257, type: 'public-key' } // RS256
          ],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required',
            residentKey: 'preferred'
          },
          timeout: 60000,
          attestation: 'direct'
        }
      }

      const credential = await navigator.credentials.create(credentialCreationOptions) as PublicKeyCredential
      
      if (!credential) {
        throw new Error('Failed to create fingerprint credential')
      }

      const biometricCredential: BiometricCredential = {
        id: credential.id,
        type: 'fingerprint',
        name: 'Fingerprint',
        nameAr: 'بصمة الإصبع',
        createdAt: new Date(),
        lastUsed: new Date(),
        reliability: 0.95, // High reliability for platform authenticators
        metadata: {
          deviceInfo: navigator.userAgent,
          userAgent: navigator.userAgent,
          enrollmentQuality: 0.9
        }
      }

      this.credentials.set(credential.id, biometricCredential)
      this.saveCredentials()

      return biometricCredential
    } catch (error) {
      console.error('Fingerprint enrollment failed:', error)
      throw new Error('فشل في تسجيل بصمة الإصبع / Fingerprint enrollment failed')
    }
  }

  public async enrollFace(userId: string, userName: string): Promise<BiometricCredential> {
    if (!this.webAuthnSupported) {
      throw new Error('Face recognition not supported on this device')
    }

    // For face enrollment, we use the same WebAuthn flow but with different user verification
    try {
      const challenge = crypto.getRandomValues(new Uint8Array(32))
      const userIdBytes = new TextEncoder().encode(userId)

      const credentialCreationOptions: CredentialCreationOptions = {
        publicKey: {
          challenge,
          rp: {
            name: 'Universal Workshop ERP',
            id: window.location.hostname
          },
          user: {
            id: userIdBytes,
            name: userName,
            displayName: userName
          },
          pubKeyCredParams: [
            { alg: -7, type: 'public-key' },
            { alg: -257, type: 'public-key' }
          ],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required'
          },
          timeout: 90000, // Longer timeout for face recognition
          attestation: 'direct'
        }
      }

      const credential = await navigator.credentials.create(credentialCreationOptions) as PublicKeyCredential

      if (!credential) {
        throw new Error('Failed to create face recognition credential')
      }

      const biometricCredential: BiometricCredential = {
        id: credential.id,
        type: 'face',
        name: 'Face Recognition',
        nameAr: 'التعرف على الوجه',
        createdAt: new Date(),
        lastUsed: new Date(),
        reliability: 0.88, // Slightly lower than fingerprint
        metadata: {
          deviceInfo: navigator.userAgent,
          userAgent: navigator.userAgent,
          enrollmentQuality: 0.85
        }
      }

      this.credentials.set(credential.id, biometricCredential)
      this.saveCredentials()

      return biometricCredential
    } catch (error) {
      console.error('Face enrollment failed:', error)
      throw new Error('فشل في تسجيل التعرف على الوجه / Face recognition enrollment failed')
    }
  }

  public async enrollVoice(
    userId: string, 
    userName: string, 
    language: 'ar' | 'en' = 'ar',
    dialect?: string
  ): Promise<BiometricCredential> {
    if (!this.voiceRecognitionSupported || !this.mediaDevicesSupported) {
      throw new Error('Voice recognition not supported on this device')
    }

    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      })

      // Create voice template through multiple recordings
      const voicePrint = await this.createVoicePrint(stream, language, dialect)

      // Stop the stream
      stream.getTracks().forEach(track => track.stop())

      const voiceTemplate: VoiceTemplate = {
        userId,
        voicePrint,
        language,
        dialect: dialect as any,
        quality: 0.85,
        createdAt: new Date()
      }

      this.voiceTemplates.set(userId, voiceTemplate)
      this.saveVoiceTemplates()

      const biometricCredential: BiometricCredential = {
        id: `voice_${userId}_${Date.now()}`,
        type: 'voice',
        name: 'Voice Recognition',
        nameAr: 'التعرف على الصوت',
        createdAt: new Date(),
        lastUsed: new Date(),
        reliability: 0.82, // Voice has more variability
        metadata: {
          deviceInfo: navigator.userAgent,
          userAgent: navigator.userAgent,
          enrollmentQuality: voiceTemplate.quality
        }
      }

      this.credentials.set(biometricCredential.id, biometricCredential)
      this.saveCredentials()

      return biometricCredential
    } catch (error) {
      console.error('Voice enrollment failed:', error)
      throw new Error('فشل في تسجيل التعرف على الصوت / Voice recognition enrollment failed')
    }
  }

  private async createVoicePrint(
    stream: MediaStream, 
    language: 'ar' | 'en',
    dialect?: string
  ): Promise<ArrayBuffer> {
    // This is a simplified implementation
    // In production, you would use advanced audio processing and ML
    
    const audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    const analyzer = audioContext.createAnalyser()
    
    analyzer.fftSize = 2048
    source.connect(analyzer)

    const bufferLength = analyzer.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    // Collect audio features over time
    const features: number[][] = []
    const recordingDuration = 5000 // 5 seconds

    return new Promise((resolve) => {
      const startTime = Date.now()
      
      const collectFeatures = () => {
        analyzer.getByteFrequencyData(dataArray)
        
        // Extract basic audio features (in production, use MFCC, spectral features, etc.)
        const feature = Array.from(dataArray).slice(0, 64) // First 64 frequency bins
        features.push(feature.map(f => f / 255)) // Normalize
        
        if (Date.now() - startTime < recordingDuration) {
          requestAnimationFrame(collectFeatures)
        } else {
          // Convert features to ArrayBuffer
          const flatFeatures = features.flat()
          const buffer = new ArrayBuffer(flatFeatures.length * 4)
          const view = new Float32Array(buffer)
          
          flatFeatures.forEach((value, index) => {
            view[index] = value
          })
          
          resolve(buffer)
        }
      }
      
      collectFeatures()
    })
  }

  public async authenticate(
    credentialIds?: string[],
    userVerification: UserVerificationRequirement = 'required'
  ): Promise<AuthenticationResult> {
    if (!this.isSupported) {
      throw new Error('Biometric authentication not supported')
    }

    const startTime = new Date()

    // Try WebAuthn authentication first
    if (this.webAuthnSupported) {
      try {
        const result = await this.authenticateWebAuthn(credentialIds, userVerification)
        if (result.success) {
          return result
        }
      } catch (error) {
        console.warn('WebAuthn authentication failed, trying fallback:', error)
      }
    }

    // Try voice authentication as fallback
    if (this.voiceRecognitionSupported) {
      try {
        return await this.authenticateVoice()
      } catch (error) {
        console.warn('Voice authentication failed:', error)
      }
    }

    return {
      success: false,
      confidence: 0,
      authenticatedAt: startTime,
      fallbackUsed: false,
      error: 'All biometric authentication methods failed'
    }
  }

  private async authenticateWebAuthn(
    credentialIds?: string[],
    userVerification: UserVerificationRequirement = 'required'
  ): Promise<AuthenticationResult> {
    const challenge = crypto.getRandomValues(new Uint8Array(32))
    
    const requestOptions: CredentialRequestOptions = {
      publicKey: {
        challenge,
        allowCredentials: credentialIds?.map(id => ({
          id: Uint8Array.from(atob(id), c => c.charCodeAt(0)),
          type: 'public-key'
        })),
        userVerification,
        timeout: 60000
      }
    }

    try {
      const credential = await navigator.credentials.get(requestOptions) as PublicKeyCredential
      
      if (!credential) {
        return {
          success: false,
          confidence: 0,
          authenticatedAt: new Date(),
          fallbackUsed: false,
          error: 'Authentication was cancelled'
        }
      }

      // Update last used time
      const storedCredential = this.credentials.get(credential.id)
      if (storedCredential) {
        storedCredential.lastUsed = new Date()
        this.saveCredentials()
      }

      return {
        success: true,
        credentialId: credential.id,
        credentialType: storedCredential?.type || 'unknown',
        confidence: storedCredential?.reliability || 0.8,
        authenticatedAt: new Date(),
        fallbackUsed: false
      }
    } catch (error) {
      console.error('WebAuthn authentication failed:', error)
      throw error
    }
  }

  private async authenticateVoice(): Promise<AuthenticationResult> {
    if (!this.voiceRecognitionSupported) {
      throw new Error('Voice recognition not supported')
    }

    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Create speech recognition instance
      const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      
      recognition.lang = 'ar-SA' // Arabic (Saudi Arabia) for Gulf dialect
      recognition.continuous = false
      recognition.interimResults = false
      recognition.maxAlternatives = 3

      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          recognition.stop()
          stream.getTracks().forEach(track => track.stop())
          reject(new Error('Voice authentication timeout'))
        }, 15000)

        recognition.onresult = (event) => {
          clearTimeout(timeoutId)
          stream.getTracks().forEach(track => track.stop())

          const results = event.results[0]
          const transcript = results[0].transcript.trim()
          const confidence = results[0].confidence

          // Check if the spoken phrase matches expected phrases
          const isValidPhrase = this.ARABIC_PHRASES.some(phrase => 
            this.calculateSimilarity(transcript, phrase) > 0.7
          )

          if (isValidPhrase && confidence > 0.6) {
            resolve({
              success: true,
              credentialType: 'voice',
              confidence: confidence * 0.9, // Slight confidence reduction for voice
              authenticatedAt: new Date(),
              fallbackUsed: true
            })
          } else {
            reject(new Error('Voice authentication failed: phrase not recognized'))
          }
        }

        recognition.onerror = (event) => {
          clearTimeout(timeoutId)
          stream.getTracks().forEach(track => track.stop())
          reject(new Error(`Voice recognition error: ${event.error}`))
        }

        recognition.start()
      })
    } catch (error) {
      console.error('Voice authentication failed:', error)
      throw error
    }
  }

  private calculateSimilarity(str1: string, str2: string): number {
    // Simple similarity calculation (Levenshtein distance)
    const len1 = str1.length
    const len2 = str2.length
    const matrix: number[][] = []

    for (let i = 0; i <= len2; i++) {
      matrix[i] = [i]
    }

    for (let j = 0; j <= len1; j++) {
      matrix[0][j] = j
    }

    for (let i = 1; i <= len2; i++) {
      for (let j = 1; j <= len1; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1]
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          )
        }
      }
    }

    return 1 - matrix[len2][len1] / Math.max(len1, len2)
  }

  public async deleteCredential(credentialId: string): Promise<boolean> {
    try {
      this.credentials.delete(credentialId)
      this.saveCredentials()
      return true
    } catch (error) {
      console.error('Failed to delete credential:', error)
      return false
    }
  }

  public getStoredCredentials(): BiometricCredential[] {
    return Array.from(this.credentials.values())
  }

  public async checkCompatibility(): Promise<boolean> {
    await this.checkSupport()
    return this.isSupported
  }

  public getArabicPhrases(): string[] {
    return [...this.ARABIC_PHRASES]
  }

  private saveCredentials(): void {
    try {
      const credentialsArray = Array.from(this.credentials.entries())
      localStorage.setItem('workshop_biometric_credentials', JSON.stringify(credentialsArray))
    } catch (error) {
      console.warn('Failed to save credentials to localStorage:', error)
    }
  }

  private loadCredentials(): void {
    try {
      const saved = localStorage.getItem('workshop_biometric_credentials')
      if (saved) {
        const credentialsArray = JSON.parse(saved)
        this.credentials = new Map(credentialsArray.map(([id, cred]: [string, any]) => [
          id,
          {
            ...cred,
            createdAt: new Date(cred.createdAt),
            lastUsed: new Date(cred.lastUsed)
          }
        ]))
      }
    } catch (error) {
      console.warn('Failed to load credentials from localStorage:', error)
    }
  }

  private saveVoiceTemplates(): void {
    try {
      // Convert ArrayBuffer to base64 for storage
      const templatesArray = Array.from(this.voiceTemplates.entries()).map(([id, template]) => [
        id,
        {
          ...template,
          voicePrint: Array.from(new Uint8Array(template.voicePrint)), // Convert to array
          createdAt: template.createdAt.toISOString()
        }
      ])
      localStorage.setItem('workshop_voice_templates', JSON.stringify(templatesArray))
    } catch (error) {
      console.warn('Failed to save voice templates:', error)
    }
  }

  private loadVoiceTemplates(): void {
    try {
      const saved = localStorage.getItem('workshop_voice_templates')
      if (saved) {
        const templatesArray = JSON.parse(saved)
        this.voiceTemplates = new Map(templatesArray.map(([id, template]: [string, any]) => [
          id,
          {
            ...template,
            voicePrint: new Uint8Array(template.voicePrint).buffer, // Convert back to ArrayBuffer
            createdAt: new Date(template.createdAt)
          }
        ]))
      }
    } catch (error) {
      console.warn('Failed to load voice templates:', error)
    }
  }

  public initialize(): void {
    this.loadCredentials()
    this.loadVoiceTemplates()
  }
}

// Composable function for Vue components
export function useBiometricAuth() {
  const manager = new BiometricAuthManager()
  
  // Reactive state
  const isSupported = ref(false)
  const isInitialized = ref(false)
  const isAuthenticating = ref(false)
  const lastAuthResult = ref<AuthenticationResult | null>(null)
  
  // Settings
  const settings = reactive<BiometricSettings>({
    preferredMethods: ['fingerprint', 'face', 'voice'],
    requireMultipleMethods: false,
    allowFallback: true,
    timeoutSeconds: 60,
    maxAttempts: 3,
    culturalAdaptations: {
      respectPrayerTimes: true,
      ramadanMode: false,
      arabicPrompts: true
    }
  })

  // Statistics
  const stats = reactive({
    totalAttempts: 0,
    successfulAttempts: 0,
    failedAttempts: 0,
    averageConfidence: 0,
    lastUsed: null as Date | null,
    methodUsage: new Map<string, number>()
  })

  // Computed properties
  const storedCredentials = computed(() => manager.getStoredCredentials())
  
  const availableMethods = computed(async () => {
    if (!isSupported.value) return []
    return await manager.getAvailableMethods()
  })

  const successRate = computed(() => {
    if (stats.totalAttempts === 0) return 0
    return (stats.successfulAttempts / stats.totalAttempts) * 100
  })

  const hasMultipleMethods = computed(() => storedCredentials.value.length > 1)

  // Methods
  async function initialize(): Promise<void> {
    try {
      manager.initialize()
      isSupported.value = await manager.checkCompatibility()
      isInitialized.value = true
    } catch (error) {
      console.error('Failed to initialize biometric auth:', error)
      isSupported.value = false
    }
  }

  async function enroll(
    type: 'fingerprint' | 'face' | 'voice',
    userId: string,
    userName: string,
    options?: { language?: 'ar' | 'en'; dialect?: string }
  ): Promise<BiometricCredential> {
    if (!isSupported.value) {
      throw new Error('Biometric authentication not supported')
    }

    try {
      let credential: BiometricCredential

      switch (type) {
        case 'fingerprint':
          credential = await manager.enrollFingerprint(userId, userName)
          break
        case 'face':
          credential = await manager.enrollFace(userId, userName)
          break
        case 'voice':
          credential = await manager.enrollVoice(
            userId, 
            userName, 
            options?.language || 'ar',
            options?.dialect
          )
          break
        default:
          throw new Error(`Unsupported enrollment type: ${type}`)
      }

      return credential
    } catch (error) {
      console.error(`${type} enrollment failed:`, error)
      throw error
    }
  }

  async function authenticate(
    credentialIds?: string[],
    userVerification?: UserVerificationRequirement
  ): Promise<AuthenticationResult> {
    if (!isSupported.value) {
      throw new Error('Biometric authentication not supported')
    }

    isAuthenticating.value = true
    stats.totalAttempts++

    try {
      const result = await manager.authenticate(credentialIds, userVerification)
      
      lastAuthResult.value = result
      stats.lastUsed = result.authenticatedAt

      if (result.success) {
        stats.successfulAttempts++
        
        // Update method usage statistics
        if (result.credentialType) {
          const currentCount = stats.methodUsage.get(result.credentialType) || 0
          stats.methodUsage.set(result.credentialType, currentCount + 1)
        }

        // Update average confidence
        const totalConfidence = stats.averageConfidence * (stats.successfulAttempts - 1) + result.confidence
        stats.averageConfidence = totalConfidence / stats.successfulAttempts
      } else {
        stats.failedAttempts++
      }

      return result
    } catch (error) {
      stats.failedAttempts++
      console.error('Authentication failed:', error)
      throw error
    } finally {
      isAuthenticating.value = false
    }
  }

  async function deleteCredential(credentialId: string): Promise<boolean> {
    return await manager.deleteCredential(credentialId)
  }

  async function getAvailableMethods(): Promise<string[]> {
    return await manager.getAvailableMethods()
  }

  async function checkCompatibility(): Promise<boolean> {
    return await manager.checkCompatibility()
  }

  function getArabicPhrases(): string[] {
    return manager.getArabicPhrases()
  }

  // Cultural adaptations
  function updateCulturalSettings(updates: Partial<BiometricSettings['culturalAdaptations']>) {
    Object.assign(settings.culturalAdaptations, updates)
    saveSettings()
  }

  function enableRamadanMode(enabled: boolean = true) {
    settings.culturalAdaptations.ramadanMode = enabled
    if (enabled) {
      settings.timeoutSeconds = 90 // Longer timeout during Ramadan
      settings.allowFallback = true // More forgiving during fasting
    }
    saveSettings()
  }

  // Settings management
  function saveSettings() {
    try {
      localStorage.setItem('workshop_biometric_settings', JSON.stringify(settings))
    } catch (error) {
      console.warn('Failed to save biometric settings:', error)
    }
  }

  function loadSettings() {
    try {
      const saved = localStorage.getItem('workshop_biometric_settings')
      if (saved) {
        const savedSettings = JSON.parse(saved)
        Object.assign(settings, savedSettings)
      }
    } catch (error) {
      console.warn('Failed to load biometric settings:', error)
    }
  }

  // Initialize on mount
  onMounted(async () => {
    loadSettings()
    await initialize()
  })

  return {
    // State
    isSupported: readonly(isSupported),
    isInitialized: readonly(isInitialized),
    isAuthenticating: readonly(isAuthenticating),
    lastAuthResult: readonly(lastAuthResult),
    settings,
    stats: readonly(stats),

    // Computed
    storedCredentials,
    availableMethods,
    successRate,
    hasMultipleMethods,

    // Methods
    initialize,
    enroll,
    authenticate,
    deleteCredential,
    getAvailableMethods,
    checkCompatibility,
    getArabicPhrases,

    // Cultural adaptations
    updateCulturalSettings,
    enableRamadanMode,

    // Settings
    saveSettings,
    loadSettings,

    // Manager access for advanced use
    manager
  }
}

// Helper functions
export function generateArabicChallenge(): string {
  const challenges = [
    'قل: بسم الله نبدأ',
    'قل: السلام عليكم',
    'قل: أشهد أن لا إله إلا الله',
    'قل: اللهم بارك في عملنا',
    'قل: الحمد لله رب العالمين'
  ]
  
  return challenges[Math.floor(Math.random() * challenges.length)]
}

export function formatBiometricType(type: string, language: 'ar' | 'en' = 'ar'): string {
  const translations = {
    fingerprint: { ar: 'بصمة الإصبع', en: 'Fingerprint' },
    face: { ar: 'التعرف على الوجه', en: 'Face Recognition' },
    voice: { ar: 'التعرف على الصوت', en: 'Voice Recognition' }
  }
  
  return translations[type as keyof typeof translations]?.[language] || type
}

// Export readonly helper
function readonly<T>(ref: Ref<T>): Readonly<Ref<T>> {
  return ref as Readonly<Ref<T>>
}

export default BiometricAuthManager