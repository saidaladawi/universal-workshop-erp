/**
 * Barcode Scanner Composable - Universal Workshop Frontend V2
 * Advanced barcode scanning with multiple format support,
 * offline capabilities, and integration with parts database.
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { usePartsStore } from '@/stores/parts'
import { useLocalizationStore } from '@/stores/localization'
import { useConnectivityStore } from '@/stores/connectivity'

// Types
interface ScanResult {
  code: string
  format: BarcodeFormat
  timestamp: Date
  confidence: number
  rawData?: string
}

interface ScanOptions {
  formats?: BarcodeFormat[]
  timeout?: number
  continuous?: boolean
  beep?: boolean
  vibrate?: boolean
  overlay?: boolean
}

interface PartLookupResult {
  found: boolean
  part?: Part
  alternatives?: Part[]
  suggestions?: string[]
}

interface Part {
  id: string
  partNumber: string
  name: string
  nameAr: string
  description: string
  descriptionAr: string
  manufacturer: string
  category: string
  price: number
  stockQuantity: number
  location: string
  imageUrl?: string
  specifications?: Record<string, any>
}

type BarcodeFormat = 
  | 'CODE_128' 
  | 'CODE_39' 
  | 'EAN_13' 
  | 'EAN_8' 
  | 'UPC_A' 
  | 'UPC_E' 
  | 'QR_CODE'
  | 'DATA_MATRIX'
  | 'PDF_417'

export function useBarcodeScanner() {
  // Stores
  const notificationStore = useNotificationStore()
  const partsStore = usePartsStore()
  const localizationStore = useLocalizationStore()
  const connectivityStore = useConnectivityStore()

  // Reactive state
  const isScanning = ref(false)
  const isInitialized = ref(false)
  const lastScanResult = ref<ScanResult | null>(null)
  const scanHistory = ref<ScanResult[]>([])
  const cameraPermission = ref<PermissionState>('prompt')
  
  // Scanner instance
  let scanner: any = null
  let videoElement: HTMLVideoElement | null = null
  let stream: MediaStream | null = null

  // Computed properties
  const { preferArabic } = localizationStore
  const { isOnline } = connectivityStore

  const supportedFormats = computed<BarcodeFormat[]>(() => [
    'CODE_128',  // Most common for parts
    'CODE_39',   // Industrial standard
    'EAN_13',    // Retail products
    'EAN_8',     // Small products
    'UPC_A',     // North American retail
    'UPC_E',     // Compact UPC
    'QR_CODE',   // Quick Response codes
    'DATA_MATRIX', // High density
    'PDF_417'    // 2D stacked
  ])

  const scannerCapabilities = computed(() => ({
    hasCamera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
    hasVibration: 'vibrate' in navigator,
    hasNotifications: 'Notification' in window,
    hasOfflineStorage: 'indexedDB' in window
  }))

  // Initialize scanner
  const initialize = async (): Promise<boolean> => {
    try {
      // Check camera permission
      if (scannerCapabilities.value.hasCamera) {
        const permission = await navigator.permissions.query({ name: 'camera' as PermissionName })
        cameraPermission.value = permission.state
        
        // Listen for permission changes
        permission.addEventListener('change', () => {
          cameraPermission.value = permission.state
        })
      }

      // Initialize QuaggaJS or ZXing scanner
      await initializeScannerEngine()
      
      isInitialized.value = true
      return true
    } catch (error) {
      console.error('Failed to initialize barcode scanner:', error)
      notificationStore.showError(
        preferArabic.value 
          ? 'فشل في تهيئة ماسح الباركود'
          : 'Failed to initialize barcode scanner'
      )
      return false
    }
  }

  // Initialize scanner engine (QuaggaJS)
  const initializeScannerEngine = async () => {
    // Dynamic import for QuaggaJS
    const Quagga = await import('quagga')
    scanner = Quagga.default || Quagga
  }

  // Start scanning
  const startScan = async (options: ScanOptions = {}): Promise<ScanResult | null> => {
    if (!isInitialized.value) {
      await initialize()
    }

    if (cameraPermission.value === 'denied') {
      notificationStore.showError(
        preferArabic.value
          ? 'يجب السماح بالوصول للكاميرا لمسح الباركود'
          : 'Camera permission required for barcode scanning'
      )
      return null
    }

    try {
      isScanning.value = true
      
      // Create video element if not exists
      if (!videoElement) {
        videoElement = document.createElement('video')
        videoElement.autoplay = true
        videoElement.playsInline = true
        videoElement.style.width = '100%'
        videoElement.style.height = '100%'
      }

      // Get camera stream
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      })

      videoElement.srcObject = stream

      // Configure scanner
      const scannerConfig = {
        inputStream: {
          name: "Live",
          type: "LiveStream",
          target: videoElement,
          constraints: {
            width: 1280,
            height: 720,
            facingMode: "environment"
          }
        },
        locator: {
          patchSize: "medium",
          halfSample: true
        },
        numOfWorkers: 2,
        frequency: 10,
        decoder: {
          readers: options.formats || supportedFormats.value
        },
        locate: true
      }

      return new Promise((resolve, reject) => {
        scanner.init(scannerConfig, (err: any) => {
          if (err) {
            reject(err)
            return
          }

          scanner.start()

          // Handle successful scan
          scanner.onDetected((result: any) => {
            const scanResult: ScanResult = {
              code: result.codeResult.code,
              format: result.codeResult.format as BarcodeFormat,
              timestamp: new Date(),
              confidence: result.codeResult.quality || 1,
              rawData: JSON.stringify(result)
            }

            // Stop scanning
            stopScan()

            // Add to history
            addToScanHistory(scanResult)

            // Provide feedback
            if (options.beep !== false) {
              playBeep()
            }
            if (options.vibrate !== false && scannerCapabilities.value.hasVibration) {
              navigator.vibrate(200)
            }

            lastScanResult.value = scanResult
            resolve(scanResult)
          })

          // Handle timeout
          if (options.timeout) {
            setTimeout(() => {
              stopScan()
              resolve(null)
            }, options.timeout)
          }
        })
      })
    } catch (error) {
      console.error('Barcode scanning failed:', error)
      isScanning.value = false
      throw error
    }
  }

  // Quick scan method
  const scan = async (options: ScanOptions = {}): Promise<ScanResult | null> => {
    return startScan({
      beep: true,
      vibrate: true,
      timeout: 30000, // 30 seconds
      ...options
    })
  }

  // Stop scanning
  const stopScan = () => {
    if (scanner && isScanning.value) {
      scanner.stop()
    }
    
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      stream = null
    }
    
    isScanning.value = false
  }

  // Lookup part by barcode
  const lookupPart = async (code: string): Promise<PartLookupResult> => {
    try {
      // Try online lookup first
      if (isOnline.value) {
        const part = await partsStore.findPartByBarcode(code)
        if (part) {
          return {
            found: true,
            part,
            alternatives: await partsStore.findAlternativeParts(part.id)
          }
        }
      }

      // Try offline lookup
      const offlinePart = await partsStore.findPartOffline(code)
      if (offlinePart) {
        return {
          found: true,
          part: offlinePart
        }
      }

      // No exact match - try fuzzy search
      const suggestions = await partsStore.searchPartsByCode(code)
      return {
        found: false,
        suggestions: suggestions.map(p => p.partNumber)
      }
    } catch (error) {
      console.error('Part lookup failed:', error)
      return { found: false }
    }
  }

  // Scan and lookup part
  const scanAndLookupPart = async (options: ScanOptions = {}): Promise<{
    scanResult: ScanResult | null
    partResult: PartLookupResult | null
  }> => {
    const scanResult = await scan(options)
    if (!scanResult) {
      return { scanResult: null, partResult: null }
    }

    const partResult = await lookupPart(scanResult.code)
    return { scanResult, partResult }
  }

  // Validate barcode format
  const validateBarcodeFormat = (code: string, expectedFormat?: BarcodeFormat): boolean => {
    if (!expectedFormat) return true

    const formatPatterns: Record<BarcodeFormat, RegExp> = {
      'CODE_128': /^[\x00-\x7F]+$/,
      'CODE_39': /^[0-9A-Z\-\.\$\/\+\%\s]+$/,
      'EAN_13': /^\d{13}$/,
      'EAN_8': /^\d{8}$/,
      'UPC_A': /^\d{12}$/,
      'UPC_E': /^\d{8}$/,
      'QR_CODE': /^.+$/,
      'DATA_MATRIX': /^.+$/,
      'PDF_417': /^.+$/
    }

    const pattern = formatPatterns[expectedFormat]
    return pattern ? pattern.test(code) : true
  }

  // Generate QR code for part
  const generatePartQRCode = async (partId: string): Promise<string> => {
    try {
      const part = await partsStore.getPart(partId)
      if (!part) throw new Error('Part not found')

      const qrData = {
        type: 'part',
        id: part.id,
        partNumber: part.partNumber,
        name: part.name,
        manufacturer: part.manufacturer,
        timestamp: Date.now()
      }

      // Use QR code library to generate
      const QRCode = await import('qrcode')
      return await QRCode.toDataURL(JSON.stringify(qrData))
    } catch (error) {
      console.error('QR code generation failed:', error)
      throw error
    }
  }

  // Add scan to history
  const addToScanHistory = (result: ScanResult) => {
    scanHistory.value.unshift(result)
    
    // Keep only last 50 scans
    if (scanHistory.value.length > 50) {
      scanHistory.value = scanHistory.value.slice(0, 50)
    }

    // Save to local storage
    saveHistoryToStorage()
  }

  // Save history to local storage
  const saveHistoryToStorage = () => {
    try {
      localStorage.setItem('barcode_scan_history', JSON.stringify(scanHistory.value))
    } catch (error) {
      console.error('Failed to save scan history:', error)
    }
  }

  // Load history from local storage
  const loadHistoryFromStorage = () => {
    try {
      const stored = localStorage.getItem('barcode_scan_history')
      if (stored) {
        scanHistory.value = JSON.parse(stored).map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }))
      }
    } catch (error) {
      console.error('Failed to load scan history:', error)
    }
  }

  // Clear scan history
  const clearHistory = () => {
    scanHistory.value = []
    localStorage.removeItem('barcode_scan_history')
  }

  // Play beep sound
  const playBeep = () => {
    try {
      const audioContext = new AudioContext()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.value = 800
      oscillator.type = 'square'

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.1)
    } catch (error) {
      // Fallback for browsers without Web Audio API
      console.warn('Could not play beep sound:', error)
    }
  }

  // Request camera permission
  const requestCameraPermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      stream.getTracks().forEach(track => track.stop())
      cameraPermission.value = 'granted'
      return true
    } catch (error) {
      cameraPermission.value = 'denied'
      return false
    }
  }

  // Get scan statistics
  const getScanStatistics = () => {
    const total = scanHistory.value.length
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const todayScans = scanHistory.value.filter(scan => 
      scan.timestamp >= today
    ).length

    const formatCounts = scanHistory.value.reduce((acc, scan) => {
      acc[scan.format] = (acc[scan.format] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return {
      total,
      todayScans,
      formatCounts,
      averageConfidence: scanHistory.value.reduce((sum, scan) => 
        sum + scan.confidence, 0) / total || 0
    }
  }

  // Lifecycle hooks
  onMounted(() => {
    loadHistoryFromStorage()
  })

  onUnmounted(() => {
    stopScan()
  })

  return {
    // State
    isScanning: readonly(isScanning),
    isInitialized: readonly(isInitialized),
    lastScanResult: readonly(lastScanResult),
    scanHistory: readonly(scanHistory),
    cameraPermission: readonly(cameraPermission),
    
    // Computed
    supportedFormats,
    scannerCapabilities,
    
    // Methods
    initialize,
    scan,
    startScan,
    stopScan,
    lookupPart,
    scanAndLookupPart,
    validateBarcodeFormat,
    generatePartQRCode,
    requestCameraPermission,
    clearHistory,
    getScanStatistics
  }
} 