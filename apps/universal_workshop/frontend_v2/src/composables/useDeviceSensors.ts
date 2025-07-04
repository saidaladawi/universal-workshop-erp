/**
 * Advanced Device Sensors Composable for Universal Workshop PWA
 * Provides access to accelerometer, ambient light, proximity, and other device sensors
 * 
 * Features:
 * - Motion detection with Arabic cultural adaptations
 * - Automatic theme switching based on ambient light
 * - Gesture recognition for workshop operations
 * - Power management integration
 * - Arabic screen reader support
 */

import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import type { Ref } from 'vue'

// Types for device sensors
interface DeviceMotionData {
  acceleration: {
    x: number | null
    y: number | null
    z: number | null
  }
  accelerationIncludingGravity: {
    x: number | null
    y: number | null
    z: number | null
  }
  rotationRate: {
    alpha: number | null
    beta: number | null
    gamma: number | null
  }
  interval: number | null
}

interface DeviceOrientationData {
  alpha: number | null // Z axis rotation (0-360°)
  beta: number | null  // X axis rotation (-180° to 180°)
  gamma: number | null // Y axis rotation (-90° to 90°)
  absolute: boolean
}

interface AmbientLightData {
  illuminance: number // lux
  timestamp: number
}

interface ProximityData {
  distance: number | null
  max: number | null
  near: boolean
}

interface BatteryData {
  charging: boolean
  chargingTime: number
  dischargingTime: number
  level: number
}

interface NetworkData {
  type: string
  effectiveType: string
  downlink: number
  rtt: number
  saveData: boolean
}

export function useDeviceSensors() {
  // Reactive sensor data
  const motion = ref<DeviceMotionData | null>(null)
  const orientation = ref<DeviceOrientationData | null>(null)
  const ambientLight = ref<AmbientLightData | null>(null)
  const proximity = ref<ProximityData | null>(null)
  const battery = ref<BatteryData | null>(null)
  const network = ref<NetworkData | null>(null)

  // Sensor availability
  const isMotionSupported = ref(false)
  const isOrientationSupported = ref(false)
  const isAmbientLightSupported = ref(false)
  const isProximitySupported = ref(false)
  const isBatterySupported = ref(false)
  const isNetworkSupported = ref(false)

  // Permission states
  const motionPermission = ref<'granted' | 'denied' | 'prompt' | null>(null)
  const orientationPermission = ref<'granted' | 'denied' | 'prompt' | null>(null)

  // Gesture detection
  const gestureData = reactive({
    isShaking: false,
    lastShake: 0,
    shakeThreshold: 15,
    shakeCooldown: 1000,
    
    isTilted: false,
    tiltAngle: 0,
    tiltThreshold: 45,
    
    isInMotion: false,
    motionIntensity: 0,
    
    lastGesture: null as string | null,
    gestureTimestamp: 0
  })

  // Arabic cultural adaptations
  const culturalSettings = reactive({
    rtlMotionAdjustment: true,
    arabicNumberDisplay: true,
    culturalGestures: {
      rightSwipe: 'التمرير يميناً', // Right swipe in Arabic
      leftSwipe: 'التمرير يساراً',   // Left swipe in Arabic
      shake: 'هز الجهاز',          // Shake in Arabic
      tilt: 'إمالة الجهاز'        // Tilt in Arabic
    }
  })

  // Auto theme switching based on ambient light
  const themeSettings = reactive({
    autoTheme: true,
    lightThreshold: 40, // lux - switch to light mode above this
    darkThreshold: 10,  // lux - switch to dark mode below this
    currentTheme: 'auto' as 'light' | 'dark' | 'auto'
  })

  // Performance optimization
  const performanceSettings = reactive({
    enablePowerSaving: true,
    reducedMotion: false,
    sampleRate: 60, // Hz
    bufferSize: 100
  })

  // Computed properties
  const deviceOrientation = computed(() => {
    if (!orientation.value) return 'unknown'
    
    const { beta, gamma } = orientation.value
    if (beta === null || gamma === null) return 'unknown'
    
    if (Math.abs(gamma) > Math.abs(beta)) {
      return gamma > 0 ? 'landscape-left' : 'landscape-right'
    } else {
      return beta > 0 ? 'portrait' : 'portrait-upside-down'
    }
  })

  const lightLevel = computed(() => {
    if (!ambientLight.value) return 'unknown'
    
    const lux = ambientLight.value.illuminance
    if (lux < 1) return 'dark'
    if (lux < 10) return 'dim'
    if (lux < 100) return 'normal'
    if (lux < 1000) return 'bright'
    return 'very-bright'
  })

  const batteryStatus = computed(() => {
    if (!battery.value) return 'unknown'
    
    const { level, charging } = battery.value
    if (charging) return 'charging'
    if (level > 0.5) return 'good'
    if (level > 0.2) return 'low'
    return 'critical'
  })

  const networkQuality = computed(() => {
    if (!network.value) return 'unknown'
    
    const { effectiveType, downlink } = network.value
    if (effectiveType === '4g' && downlink > 5) return 'excellent'
    if (effectiveType === '4g' || downlink > 2) return 'good'
    if (effectiveType === '3g' || downlink > 0.5) return 'fair'
    return 'poor'
  })

  // Request permissions for iOS devices
  async function requestMotionPermission(): Promise<boolean> {
    try {
      if (typeof DeviceMotionEvent !== 'undefined' && 
          typeof (DeviceMotionEvent as any).requestPermission === 'function') {
        const permission = await (DeviceMotionEvent as any).requestPermission()
        motionPermission.value = permission
        return permission === 'granted'
      }
      
      motionPermission.value = 'granted'
      return true
    } catch (error) {
      console.error('Error requesting motion permission:', error)
      motionPermission.value = 'denied'
      return false
    }
  }

  async function requestOrientationPermission(): Promise<boolean> {
    try {
      if (typeof DeviceOrientationEvent !== 'undefined' && 
          typeof (DeviceOrientationEvent as any).requestPermission === 'function') {
        const permission = await (DeviceOrientationEvent as any).requestPermission()
        orientationPermission.value = permission
        return permission === 'granted'
      }
      
      orientationPermission.value = 'granted'
      return true
    } catch (error) {
      console.error('Error requesting orientation permission:', error)
      orientationPermission.value = 'denied'
      return false
    }
  }

  // Motion detection and gesture recognition
  function detectShake(motionData: DeviceMotionData) {
    const now = Date.now()
    if (now - gestureData.lastShake < gestureData.shakeCooldown) return

    const { x, y, z } = motionData.accelerationIncludingGravity
    if (x === null || y === null || z === null) return

    const acceleration = Math.sqrt(x * x + y * y + z * z)
    
    if (acceleration > gestureData.shakeThreshold) {
      gestureData.isShaking = true
      gestureData.lastShake = now
      gestureData.lastGesture = culturalSettings.culturalGestures.shake
      gestureData.gestureTimestamp = now
      
      // Trigger shake event
      window.dispatchEvent(new CustomEvent('workshop-shake', {
        detail: { 
          intensity: acceleration, 
          timestamp: now,
          message_ar: 'تم اكتشاف هز الجهاز',
          message_en: 'Device shake detected'
        }
      }))
      
      setTimeout(() => {
        gestureData.isShaking = false
      }, 500)
    }
  }

  function detectTilt(orientationData: DeviceOrientationData) {
    const { beta, gamma } = orientationData
    if (beta === null || gamma === null) return

    const tiltAngle = Math.max(Math.abs(beta), Math.abs(gamma))
    gestureData.tiltAngle = tiltAngle
    
    const wasTilted = gestureData.isTilted
    gestureData.isTilted = tiltAngle > gestureData.tiltThreshold
    
    if (!wasTilted && gestureData.isTilted) {
      gestureData.lastGesture = culturalSettings.culturalGestures.tilt
      gestureData.gestureTimestamp = Date.now()
      
      window.dispatchEvent(new CustomEvent('workshop-tilt', {
        detail: { 
          angle: tiltAngle, 
          orientation: deviceOrientation.value,
          message_ar: 'تم اكتشاف إمالة الجهاز',
          message_en: 'Device tilt detected'
        }
      }))
    }
  }

  function calculateMotionIntensity(motionData: DeviceMotionData) {
    const { x, y, z } = motionData.acceleration
    if (x === null || y === null || z === null) return

    const intensity = Math.sqrt(x * x + y * y + z * z)
    gestureData.motionIntensity = intensity
    gestureData.isInMotion = intensity > 1.0
  }

  // Automatic theme switching based on ambient light
  function handleAmbientLightChange(lightData: AmbientLightData) {
    if (!themeSettings.autoTheme) return

    const { illuminance } = lightData
    
    if (illuminance < themeSettings.darkThreshold && themeSettings.currentTheme !== 'dark') {
      themeSettings.currentTheme = 'dark'
      document.documentElement.setAttribute('data-theme', 'dark')
      
      window.dispatchEvent(new CustomEvent('workshop-theme-change', {
        detail: { 
          theme: 'dark', 
          reason: 'ambient-light',
          illuminance,
          message_ar: 'تم التبديل إلى المظهر المظلم تلقائياً',
          message_en: 'Automatically switched to dark theme'
        }
      }))
    } else if (illuminance > themeSettings.lightThreshold && themeSettings.currentTheme !== 'light') {
      themeSettings.currentTheme = 'light'
      document.documentElement.setAttribute('data-theme', 'light')
      
      window.dispatchEvent(new CustomEvent('workshop-theme-change', {
        detail: { 
          theme: 'light', 
          reason: 'ambient-light',
          illuminance,
          message_ar: 'تم التبديل إلى المظهر الفاتح تلقائياً',
          message_en: 'Automatically switched to light theme'
        }
      }))
    }
  }

  // Power management based on battery status
  function handleBatteryChange(batteryData: BatteryData) {
    const { level, charging } = batteryData
    
    if (!charging && level < 0.2 && !performanceSettings.enablePowerSaving) {
      performanceSettings.enablePowerSaving = true
      performanceSettings.sampleRate = 30 // Reduce sample rate
      
      window.dispatchEvent(new CustomEvent('workshop-power-saving', {
        detail: { 
          enabled: true, 
          batteryLevel: level,
          message_ar: 'تم تفعيل وضع توفير الطاقة',
          message_en: 'Power saving mode enabled'
        }
      }))
    } else if ((charging || level > 0.5) && performanceSettings.enablePowerSaving) {
      performanceSettings.enablePowerSaving = false
      performanceSettings.sampleRate = 60 // Restore normal sample rate
      
      window.dispatchEvent(new CustomEvent('workshop-power-saving', {
        detail: { 
          enabled: false, 
          batteryLevel: level,
          message_ar: 'تم إلغاء وضع توفير الطاقة',
          message_en: 'Power saving mode disabled'
        }
      }))
    }
  }

  // Event handlers
  function handleDeviceMotion(event: DeviceMotionEvent) {
    const motionData: DeviceMotionData = {
      acceleration: {
        x: event.acceleration?.x || null,
        y: event.acceleration?.y || null,
        z: event.acceleration?.z || null
      },
      accelerationIncludingGravity: {
        x: event.accelerationIncludingGravity?.x || null,
        y: event.accelerationIncludingGravity?.y || null,
        z: event.accelerationIncludingGravity?.z || null
      },
      rotationRate: {
        alpha: event.rotationRate?.alpha || null,
        beta: event.rotationRate?.beta || null,
        gamma: event.rotationRate?.gamma || null
      },
      interval: event.interval || null
    }

    motion.value = motionData
    detectShake(motionData)
    calculateMotionIntensity(motionData)
  }

  function handleDeviceOrientation(event: DeviceOrientationEvent) {
    const orientationData: DeviceOrientationData = {
      alpha: event.alpha,
      beta: event.beta,
      gamma: event.gamma,
      absolute: event.absolute || false
    }

    orientation.value = orientationData
    detectTilt(orientationData)
  }

  function handleAmbientLight(event: any) {
    const lightData: AmbientLightData = {
      illuminance: event.value || 0,
      timestamp: Date.now()
    }

    ambientLight.value = lightData
    handleAmbientLightChange(lightData)
  }

  function handleProximity(event: any) {
    proximity.value = {
      distance: event.distance || null,
      max: event.max || null,
      near: event.near || false
    }
  }

  // Initialize sensors
  async function initializeSensors() {
    // Check sensor support
    isMotionSupported.value = 'DeviceMotionEvent' in window
    isOrientationSupported.value = 'DeviceOrientationEvent' in window
    isAmbientLightSupported.value = 'AmbientLightSensor' in window || 'ondevicelight' in window
    isProximitySupported.value = 'ProximitySensor' in window || 'onuserproximity' in window
    isBatterySupported.value = 'getBattery' in navigator
    isNetworkSupported.value = 'connection' in navigator

    // Request permissions for iOS
    if (isMotionSupported.value) {
      await requestMotionPermission()
    }
    
    if (isOrientationSupported.value) {
      await requestOrientationPermission()
    }

    // Initialize motion sensor
    if (isMotionSupported.value && motionPermission.value === 'granted') {
      window.addEventListener('devicemotion', handleDeviceMotion, { passive: true })
    }

    // Initialize orientation sensor
    if (isOrientationSupported.value && orientationPermission.value === 'granted') {
      window.addEventListener('deviceorientation', handleDeviceOrientation, { passive: true })
    }

    // Initialize ambient light sensor
    if (isAmbientLightSupported.value) {
      try {
        if ('AmbientLightSensor' in window) {
          const sensor = new (window as any).AmbientLightSensor()
          sensor.addEventListener('reading', () => {
            handleAmbientLight({ value: sensor.illuminance })
          })
          sensor.start()
        } else {
          window.addEventListener('devicelight', handleAmbientLight, { passive: true })
        }
      } catch (error) {
        console.warn('Ambient light sensor not available:', error)
      }
    }

    // Initialize proximity sensor
    if (isProximitySupported.value) {
      try {
        if ('ProximitySensor' in window) {
          const sensor = new (window as any).ProximitySensor()
          sensor.addEventListener('reading', () => {
            handleProximity({
              distance: sensor.distance,
              max: sensor.max,
              near: sensor.distance < 5
            })
          })
          sensor.start()
        } else {
          window.addEventListener('userproximity', handleProximity, { passive: true })
        }
      } catch (error) {
        console.warn('Proximity sensor not available:', error)
      }
    }

    // Initialize battery API
    if (isBatterySupported.value) {
      try {
        const batteryManager = await (navigator as any).getBattery()
        
        function updateBatteryInfo() {
          const batteryData: BatteryData = {
            charging: batteryManager.charging,
            chargingTime: batteryManager.chargingTime,
            dischargingTime: batteryManager.dischargingTime,
            level: batteryManager.level
          }
          battery.value = batteryData
          handleBatteryChange(batteryData)
        }

        updateBatteryInfo()
        batteryManager.addEventListener('chargingchange', updateBatteryInfo)
        batteryManager.addEventListener('levelchange', updateBatteryInfo)
      } catch (error) {
        console.warn('Battery API not available:', error)
      }
    }

    // Initialize network information
    if (isNetworkSupported.value) {
      const connection = (navigator as any).connection
      
      function updateNetworkInfo() {
        network.value = {
          type: connection.type || 'unknown',
          effectiveType: connection.effectiveType || 'unknown',
          downlink: connection.downlink || 0,
          rtt: connection.rtt || 0,
          saveData: connection.saveData || false
        }
      }

      updateNetworkInfo()
      connection.addEventListener('change', updateNetworkInfo)
    }
  }

  // Cleanup function
  function cleanup() {
    if (isMotionSupported.value) {
      window.removeEventListener('devicemotion', handleDeviceMotion)
    }
    
    if (isOrientationSupported.value) {
      window.removeEventListener('deviceorientation', handleDeviceOrientation)
    }
    
    if (isAmbientLightSupported.value) {
      window.removeEventListener('devicelight', handleAmbientLight)
    }
    
    if (isProximitySupported.value) {
      window.removeEventListener('userproximity', handleProximity)
    }
  }

  // Lifecycle management
  onMounted(() => {
    initializeSensors()
  })

  onUnmounted(() => {
    cleanup()
  })

  // Public API
  return {
    // Sensor data
    motion: readonly(motion),
    orientation: readonly(orientation),
    ambientLight: readonly(ambientLight),
    proximity: readonly(proximity),
    battery: readonly(battery),
    network: readonly(network),

    // Sensor availability
    isMotionSupported: readonly(isMotionSupported),
    isOrientationSupported: readonly(isOrientationSupported),
    isAmbientLightSupported: readonly(isAmbientLightSupported),
    isProximitySupported: readonly(isProximitySupported),
    isBatterySupported: readonly(isBatterySupported),
    isNetworkSupported: readonly(isNetworkSupported),

    // Permissions
    motionPermission: readonly(motionPermission),
    orientationPermission: readonly(orientationPermission),

    // Computed properties
    deviceOrientation: readonly(deviceOrientation),
    lightLevel: readonly(lightLevel),
    batteryStatus: readonly(batteryStatus),
    networkQuality: readonly(networkQuality),

    // Gesture data
    gestureData: readonly(gestureData),
    culturalSettings,
    themeSettings,
    performanceSettings,

    // Methods
    requestMotionPermission,
    requestOrientationPermission,
    initializeSensors,
    cleanup
  }
}

// Helper function for Arabic number formatting
export function formatArabicSensorValue(value: number, unit: string = ''): string {
  const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
  const formattedValue = value.toFixed(2).replace(/[0-9]/g, (digit) => arabicNumerals[parseInt(digit)])
  return unit ? `${formattedValue} ${unit}` : formattedValue
}

// Export readonly helper
function readonly<T>(ref: Ref<T>): Readonly<Ref<T>> {
  return ref as Readonly<Ref<T>>
}