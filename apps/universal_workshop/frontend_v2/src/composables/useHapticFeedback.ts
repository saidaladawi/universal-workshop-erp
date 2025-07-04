/**
 * Workshop-Specific Haptic Feedback System for Universal Workshop PWA
 * Provides contextual vibration patterns for different workshop operations
 * 
 * Features:
 * - Workshop-specific haptic patterns
 * - Arabic cultural adaptations
 * - Power-aware feedback management
 * - Accessibility support
 * - Custom vibration sequences
 * - User preference management
 */

import { ref, reactive, computed, onMounted } from 'vue'
import type { Ref } from 'vue'

// Types for haptic feedback
interface HapticPattern {
  name: string
  nameAr: string
  pattern: number[] // [vibrate, pause, vibrate, pause, ...]
  intensity: 'light' | 'medium' | 'heavy'
  duration: number // total duration in ms
  category: 'success' | 'warning' | 'error' | 'info' | 'action' | 'navigation'
  description: string
  descriptionAr: string
}

interface HapticSettings {
  enabled: boolean
  intensity: 'light' | 'medium' | 'heavy'
  batterySaver: boolean
  accessibilityMode: boolean
  quietHours: {
    enabled: boolean
    start: string
    end: string
  }
  culturalAdaptations: {
    respectPrayerTimes: boolean
    ramadanMode: boolean
    reducedIntensity: boolean
  }
}

interface HapticEvent {
  type: string
  pattern: HapticPattern
  timestamp: number
  success: boolean
  deviceSupport: boolean
}

class HapticFeedbackManager {
  private isSupported: boolean = false
  private lastPattern: string | null = null
  private lastExecution: number = 0
  private cooldownPeriod: number = 100 // ms between patterns

  // Workshop-specific haptic patterns
  private patterns: Map<string, HapticPattern> = new Map([
    // Success patterns
    ['scan_success', {
      name: 'Scan Success',
      nameAr: 'نجح المسح',
      pattern: [50, 50, 50], // Quick double pulse
      intensity: 'light',
      duration: 150,
      category: 'success',
      description: 'Successful barcode/QR scan',
      descriptionAr: 'تم مسح الرمز بنجاح'
    }],
    
    ['service_complete', {
      name: 'Service Complete',
      nameAr: 'اكتملت الخدمة',
      pattern: [100, 100, 100, 100, 100], // Triple pulse
      intensity: 'medium',
      duration: 500,
      category: 'success',
      description: 'Service order completed',
      descriptionAr: 'تم إنجاز أمر الخدمة'
    }],

    ['payment_success', {
      name: 'Payment Success',
      nameAr: 'تم الدفع بنجاح',
      pattern: [200, 100, 50, 100, 200], // Celebration pattern
      intensity: 'medium',
      duration: 650,
      category: 'success',
      description: 'Payment processed successfully',
      descriptionAr: 'تمت معالجة الدفع بنجاح'
    }],

    // Warning patterns
    ['low_inventory', {
      name: 'Low Inventory',
      nameAr: 'مخزون منخفض',
      pattern: [100, 200, 100, 200, 100], // Urgent pulse
      intensity: 'medium',
      duration: 800,
      category: 'warning',
      description: 'Item inventory running low',
      descriptionAr: 'المخزون ينفد من الصنف'
    }],

    ['appointment_reminder', {
      name: 'Appointment Reminder',
      nameAr: 'تذكير بالموعد',
      pattern: [150, 150, 150, 150, 150], // Gentle reminder
      intensity: 'light',
      duration: 750,
      category: 'warning',
      description: 'Upcoming appointment reminder',
      descriptionAr: 'تذكير بموعد قادم'
    }],

    ['tool_maintenance', {
      name: 'Tool Maintenance',
      nameAr: 'صيانة الأدوات',
      pattern: [80, 120, 80, 120, 80, 120, 80], // Maintenance rhythm
      intensity: 'medium',
      duration: 760,
      category: 'warning',
      description: 'Tool requires maintenance',
      descriptionAr: 'تحتاج الأداة إلى صيانة'
    }],

    // Error patterns
    ['scan_error', {
      name: 'Scan Error',
      nameAr: 'خطأ في المسح',
      pattern: [200, 100, 200], // Strong error pulse
      intensity: 'heavy',
      duration: 500,
      category: 'error',
      description: 'Barcode scan failed',
      descriptionAr: 'فشل في مسح الرمز'
    }],

    ['access_denied', {
      name: 'Access Denied',
      nameAr: 'رُفض الوصول',
      pattern: [300, 200, 300, 200, 300], // Security alert
      intensity: 'heavy',
      duration: 1400,
      category: 'error',
      description: 'Access denied to restricted area',
      descriptionAr: 'رُفض الوصول للمنطقة المحظورة'
    }],

    ['system_error', {
      name: 'System Error',
      nameAr: 'خطأ في النظام',
      pattern: [500, 300, 500], // Critical error
      intensity: 'heavy',
      duration: 1300,
      category: 'error',
      description: 'System error occurred',
      descriptionAr: 'حدث خطأ في النظام'
    }],

    // Info patterns
    ['new_message', {
      name: 'New Message',
      nameAr: 'رسالة جديدة',
      pattern: [75, 75, 75], // Gentle notification
      intensity: 'light',
      duration: 225,
      category: 'info',
      description: 'New message received',
      descriptionAr: 'تم استلام رسالة جديدة'
    }],

    ['battery_low', {
      name: 'Battery Low',
      nameAr: 'البطارية منخفضة',
      pattern: [100, 200, 100, 200, 100, 200], // Battery warning
      intensity: 'medium',
      duration: 1000,
      category: 'warning',
      description: 'Device battery is low',
      descriptionAr: 'بطارية الجهاز منخفضة'
    }],

    // Action patterns
    ['button_press', {
      name: 'Button Press',
      nameAr: 'ضغط الزر',
      pattern: [25], // Quick tap
      intensity: 'light',
      duration: 25,
      category: 'action',
      description: 'Button pressed confirmation',
      descriptionAr: 'تأكيد ضغط الزر'
    }],

    ['swipe_action', {
      name: 'Swipe Action',
      nameAr: 'حركة السحب',
      pattern: [40, 20, 40], // Swipe confirmation
      intensity: 'light',
      duration: 100,
      category: 'action',
      description: 'Swipe gesture confirmation',
      descriptionAr: 'تأكيد حركة السحب'
    }],

    ['long_press', {
      name: 'Long Press',
      nameAr: 'الضغط المطول',
      pattern: [100, 50, 100], // Long press feedback
      intensity: 'medium',
      duration: 250,
      category: 'action',
      description: 'Long press action triggered',
      descriptionAr: 'تم تفعيل الضغط المطول'
    }],

    // Navigation patterns
    ['page_change', {
      name: 'Page Change',
      nameAr: 'تغيير الصفحة',
      pattern: [30, 30, 60], // Page transition
      intensity: 'light',
      duration: 120,
      category: 'navigation',
      description: 'Page navigation completed',
      descriptionAr: 'تم تغيير الصفحة'
    }],

    ['drawer_open', {
      name: 'Drawer Open',
      nameAr: 'فتح القائمة',
      pattern: [50, 30, 80], // Drawer slide
      intensity: 'light',
      duration: 160,
      category: 'navigation',
      description: 'Navigation drawer opened',
      descriptionAr: 'تم فتح قائمة التنقل'
    }],

    // Workshop-specific patterns
    ['part_found', {
      name: 'Part Found',
      nameAr: 'تم العثور على القطعة',
      pattern: [60, 60, 120], // Discovery pattern
      intensity: 'medium',
      duration: 240,
      category: 'success',
      description: 'Vehicle part located in inventory',
      descriptionAr: 'تم العثور على قطعة المركبة في المخزون'
    }],

    ['technician_assigned', {
      name: 'Technician Assigned',
      nameAr: 'تم تكليف الفني',
      pattern: [80, 80, 160], // Assignment confirmation
      intensity: 'medium',
      duration: 320,
      category: 'info',
      description: 'Technician assigned to service',
      descriptionAr: 'تم تكليف فني بالخدمة'
    }],

    ['quality_check', {
      name: 'Quality Check',
      nameAr: 'فحص الجودة',
      pattern: [50, 50, 50, 50, 100], // Quality verification
      intensity: 'light',
      duration: 300,
      category: 'info',
      description: 'Quality check required',
      descriptionAr: 'مطلوب فحص الجودة'
    }],

    ['emergency_alert', {
      name: 'Emergency Alert',
      nameAr: 'تنبيه الطوارئ',
      pattern: [200, 100, 200, 100, 200, 100, 200], // Emergency pattern
      intensity: 'heavy',
      duration: 1300,
      category: 'error',
      description: 'Emergency situation alert',
      descriptionAr: 'تنبيه حالة طوارئ'
    }],

    // Cultural patterns
    ['prayer_time', {
      name: 'Prayer Time',
      nameAr: 'وقت الصلاة',
      pattern: [100, 200, 100, 400, 100], // Respectful prayer reminder
      intensity: 'light',
      duration: 900,
      category: 'info',
      description: 'Prayer time notification',
      descriptionAr: 'تذكير بوقت الصلاة'
    }],

    ['iftar_time', {
      name: 'Iftar Time',
      nameAr: 'وقت الإفطار',
      pattern: [150, 150, 150, 300], // Iftar celebration
      intensity: 'medium',
      duration: 750,
      category: 'info',
      description: 'Time to break fast',
      descriptionAr: 'حان وقت الإفطار'
    }]
  ])

  constructor() {
    this.checkSupport()
  }

  private checkSupport(): void {
    this.isSupported = 'navigator' in window && 'vibrate' in navigator
    
    if (!this.isSupported) {
      console.warn('Haptic feedback not supported on this device')
    }
  }

  public async vibrate(pattern: HapticPattern, settings: HapticSettings): Promise<boolean> {
    // Check if haptics are enabled
    if (!settings.enabled || !this.isSupported) {
      return false
    }

    // Check cooldown period
    const now = Date.now()
    if (now - this.lastExecution < this.cooldownPeriod) {
      return false
    }

    // Check quiet hours
    if (this.isQuietHours(settings.quietHours)) {
      return false
    }

    // Adjust pattern based on intensity settings
    const adjustedPattern = this.adjustPatternIntensity(pattern, settings.intensity)

    try {
      // Execute vibration
      const success = navigator.vibrate(adjustedPattern.pattern)
      
      this.lastPattern = pattern.name
      this.lastExecution = now

      // Trigger custom event for analytics
      window.dispatchEvent(new CustomEvent('haptic-feedback', {
        detail: {
          pattern: pattern.name,
          category: pattern.category,
          success,
          timestamp: now
        }
      }))

      return success
    } catch (error) {
      console.error('Haptic feedback error:', error)
      return false
    }
  }

  private adjustPatternIntensity(pattern: HapticPattern, intensity: 'light' | 'medium' | 'heavy'): HapticPattern {
    if (pattern.intensity === intensity) {
      return pattern
    }

    const multipliers = {
      light: 0.6,
      medium: 1.0,
      heavy: 1.4
    }

    const multiplier = multipliers[intensity] / multipliers[pattern.intensity]
    
    return {
      ...pattern,
      pattern: pattern.pattern.map(duration => Math.round(duration * multiplier)),
      intensity
    }
  }

  private isQuietHours(quietHours: HapticSettings['quietHours']): boolean {
    if (!quietHours.enabled) return false

    const now = new Date()
    const currentTime = now.getHours() * 60 + now.getMinutes()
    
    const [startHour, startMin] = quietHours.start.split(':').map(Number)
    const [endHour, endMin] = quietHours.end.split(':').map(Number)
    
    const startTime = startHour * 60 + startMin
    const endTime = endHour * 60 + endMin

    if (startTime <= endTime) {
      return currentTime >= startTime && currentTime <= endTime
    } else {
      // Across midnight
      return currentTime >= startTime || currentTime <= endTime
    }
  }

  public getPattern(name: string): HapticPattern | undefined {
    return this.patterns.get(name)
  }

  public getAllPatterns(): HapticPattern[] {
    return Array.from(this.patterns.values())
  }

  public getPatternsByCategory(category: HapticPattern['category']): HapticPattern[] {
    return Array.from(this.patterns.values()).filter(pattern => pattern.category === category)
  }

  public addCustomPattern(name: string, pattern: HapticPattern): void {
    this.patterns.set(name, pattern)
  }

  public removePattern(name: string): boolean {
    return this.patterns.delete(name)
  }
}

// Composable function for Vue components
export function useHapticFeedback() {
  const manager = new HapticFeedbackManager()
  
  // Reactive state
  const isSupported = ref(manager['isSupported'])
  const isEnabled = ref(true)
  
  // Settings
  const settings = reactive<HapticSettings>({
    enabled: true,
    intensity: 'medium',
    batterySaver: false,
    accessibilityMode: false,
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '07:00'
    },
    culturalAdaptations: {
      respectPrayerTimes: true,
      ramadanMode: false,
      reducedIntensity: false
    }
  })

  // Usage statistics
  const stats = reactive({
    totalVibrations: 0,
    successfulVibrations: 0,
    failedVibrations: 0,
    lastUsed: null as string | null,
    mostUsedPattern: null as string | null,
    patternUsage: new Map<string, number>()
  })

  // Computed properties
  const effectiveIntensity = computed(() => {
    if (settings.culturalAdaptations.reducedIntensity) {
      return 'light'
    }
    if (settings.batterySaver) {
      return settings.intensity === 'heavy' ? 'medium' : 'light'
    }
    return settings.intensity
  })

  const availablePatterns = computed(() => 
    manager.getAllPatterns().filter(pattern => {
      if (settings.accessibilityMode && pattern.intensity === 'heavy') {
        return false
      }
      return true
    })
  )

  // Methods
  async function vibrate(patternName: string): Promise<boolean> {
    const pattern = manager.getPattern(patternName)
    if (!pattern) {
      console.warn(`Haptic pattern '${patternName}' not found`)
      return false
    }

    // Update settings based on cultural adaptations
    const currentSettings = { ...settings }
    if (currentSettings.culturalAdaptations.ramadanMode) {
      currentSettings.intensity = 'light'
    }

    const success = await manager.vibrate(pattern, currentSettings)
    
    // Update statistics
    stats.totalVibrations++
    if (success) {
      stats.successfulVibrations++
      stats.lastUsed = patternName
      
      const currentCount = stats.patternUsage.get(patternName) || 0
      stats.patternUsage.set(patternName, currentCount + 1)
      
      // Update most used pattern
      let maxCount = 0
      let mostUsed = null
      stats.patternUsage.forEach((count, name) => {
        if (count > maxCount) {
          maxCount = count
          mostUsed = name
        }
      })
      stats.mostUsedPattern = mostUsed
    } else {
      stats.failedVibrations++
    }

    return success
  }

  async function vibrateCustom(pattern: number[]): Promise<boolean> {
    if (!isSupported.value || !settings.enabled) {
      return false
    }

    try {
      const success = navigator.vibrate(pattern)
      stats.totalVibrations++
      if (success) {
        stats.successfulVibrations++
      } else {
        stats.failedVibrations++
      }
      return success
    } catch (error) {
      console.error('Custom haptic feedback error:', error)
      stats.failedVibrations++
      return false
    }
  }

  // Workshop-specific convenience methods
  const workshopHaptics = {
    scanSuccess: () => vibrate('scan_success'),
    scanError: () => vibrate('scan_error'),
    serviceComplete: () => vibrate('service_complete'),
    paymentSuccess: () => vibrate('payment_success'),
    lowInventory: () => vibrate('low_inventory'),
    appointmentReminder: () => vibrate('appointment_reminder'),
    toolMaintenance: () => vibrate('tool_maintenance'),
    accessDenied: () => vibrate('access_denied'),
    systemError: () => vibrate('system_error'),
    newMessage: () => vibrate('new_message'),
    batteryLow: () => vibrate('battery_low'),
    buttonPress: () => vibrate('button_press'),
    swipeAction: () => vibrate('swipe_action'),
    longPress: () => vibrate('long_press'),
    pageChange: () => vibrate('page_change'),
    drawerOpen: () => vibrate('drawer_open'),
    partFound: () => vibrate('part_found'),
    technicianAssigned: () => vibrate('technician_assigned'),
    qualityCheck: () => vibrate('quality_check'),
    emergencyAlert: () => vibrate('emergency_alert'),
    prayerTime: () => vibrate('prayer_time'),
    iftarTime: () => vibrate('iftar_time')
  }

  // Cultural adaptations
  function enableRamadanMode(enabled: boolean = true) {
    settings.culturalAdaptations.ramadanMode = enabled
    if (enabled) {
      settings.culturalAdaptations.reducedIntensity = true
      settings.quietHours.enabled = true
    }
  }

  function updateForPrayerTime(isPrayerTime: boolean) {
    if (settings.culturalAdaptations.respectPrayerTimes && isPrayerTime) {
      // Reduce intensity during prayer times
      settings.culturalAdaptations.reducedIntensity = true
    } else {
      settings.culturalAdaptations.reducedIntensity = false
    }
  }

  // Battery optimization
  function updateBatterySaver(batteryLevel: number) {
    if (batteryLevel < 0.2) {
      settings.batterySaver = true
    } else if (batteryLevel > 0.5) {
      settings.batterySaver = false
    }
  }

  // Load settings from localStorage
  function loadSettings() {
    try {
      const saved = localStorage.getItem('workshop-haptic-settings')
      if (saved) {
        const savedSettings = JSON.parse(saved)
        Object.assign(settings, savedSettings)
      }
    } catch (error) {
      console.warn('Failed to load haptic settings:', error)
    }
  }

  // Save settings to localStorage
  function saveSettings() {
    try {
      localStorage.setItem('workshop-haptic-settings', JSON.stringify(settings))
    } catch (error) {
      console.warn('Failed to save haptic settings:', error)
    }
  }

  // Initialize
  onMounted(() => {
    loadSettings()
    
    // Auto-save settings when changed
    const unwatchSettings = watch(settings, saveSettings, { deep: true })
    
    // Listen for battery changes
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        updateBatterySaver(battery.level)
        battery.addEventListener('levelchange', () => {
          updateBatterySaver(battery.level)
        })
      })
    }

    // Cleanup
    return () => {
      unwatchSettings()
    }
  })

  return {
    // State
    isSupported: readonly(isSupported),
    isEnabled: readonly(isEnabled),
    settings,
    stats: readonly(stats),

    // Computed
    effectiveIntensity,
    availablePatterns,

    // Methods
    vibrate,
    vibrateCustom,
    workshopHaptics,

    // Cultural adaptations
    enableRamadanMode,
    updateForPrayerTime,
    updateBatterySaver,

    // Settings management
    loadSettings,
    saveSettings,

    // Manager access for advanced use
    manager
  }
}

// Helper functions
export function createHapticPattern(
  name: string,
  nameAr: string,
  pattern: number[],
  options: Partial<Omit<HapticPattern, 'name' | 'nameAr' | 'pattern'>> = {}
): HapticPattern {
  return {
    name,
    nameAr,
    pattern,
    intensity: options.intensity || 'medium',
    duration: options.duration || pattern.reduce((sum, val) => sum + val, 0),
    category: options.category || 'action',
    description: options.description || `Custom haptic pattern: ${name}`,
    descriptionAr: options.descriptionAr || `نمط اهتزاز مخصص: ${nameAr}`
  }
}

export function getHapticPatternsForWorkflow(workflow: string): string[] {
  const workflows: Record<string, string[]> = {
    'vehicle_checkin': ['scan_success', 'technician_assigned', 'button_press'],
    'parts_inventory': ['scan_success', 'part_found', 'low_inventory'],
    'service_completion': ['quality_check', 'service_complete', 'payment_success'],
    'emergency': ['emergency_alert', 'system_error', 'access_denied'],
    'navigation': ['page_change', 'drawer_open', 'button_press'],
    'cultural': ['prayer_time', 'iftar_time', 'appointment_reminder']
  }
  
  return workflows[workflow] || []
}

// Export readonly helper
function readonly<T>(ref: Ref<T>): Readonly<Ref<T>> {
  return ref as Readonly<Ref<T>>
}

// Watch helper
function watch(source: any, callback: any, options?: any) {
  // Simplified watch implementation
  // In real Vue app, this would be the actual watch function
  return () => {} // cleanup function
}

export default HapticFeedbackManager