<!--
  Biometric Authentication Enrollment Flow
  Complete enrollment process for fingerprint, face recognition, and other biometric methods
  
  Features:
  - Multi-modal biometric support (fingerprint, face, voice)
  - Arabic-first interface with RTL support
  - Progressive enrollment with fallback options
  - Security validation and verification
  - Device compatibility checking
  - Cultural-appropriate messaging
-->

<template>
  <div class="biometric-enrollment" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Header -->
    <div class="enrollment-header">
      <h2 class="title">
        {{ currentStep.title }}
      </h2>
      <p class="subtitle">
        {{ currentStep.description }}
      </p>
      
      <!-- Progress indicator -->
      <div class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${enrollmentProgress}%` }"
          ></div>
        </div>
        <span class="progress-text">
          {{ formatProgress(currentStepIndex + 1, totalSteps) }}
        </span>
      </div>
    </div>

    <!-- Main content area -->
    <div class="enrollment-content">
      <!-- Step 1: Welcome & Setup -->
      <div v-if="currentStepIndex === 0" class="step-welcome">
        <div class="icon-container">
          <i class="icon-fingerprint"></i>
        </div>
        
        <div class="welcome-text">
          <h3>{{ $t('biometric.welcome.title') }}</h3>
          <p>{{ $t('biometric.welcome.description') }}</p>
        </div>

        <div class="benefits-list">
          <div class="benefit-item" v-for="benefit in benefits" :key="benefit.key">
            <i :class="benefit.icon"></i>
            <span>{{ $t(benefit.text) }}</span>
          </div>
        </div>

        <div class="security-notice">
          <i class="icon-shield"></i>
          <p>{{ $t('biometric.security.notice') }}</p>
        </div>
      </div>

      <!-- Step 2: Device Compatibility Check -->
      <div v-else-if="currentStepIndex === 1" class="step-compatibility">
        <div class="compatibility-checks">
          <div 
            v-for="check in compatibilityChecks" 
            :key="check.name"
            class="check-item"
            :class="{ 
              'check-success': check.status === 'passed',
              'check-warning': check.status === 'warning',
              'check-error': check.status === 'failed'
            }"
          >
            <div class="check-icon">
              <i v-if="check.status === 'checking'" class="icon-spinner spin"></i>
              <i v-else-if="check.status === 'passed'" class="icon-check-circle"></i>
              <i v-else-if="check.status === 'warning'" class="icon-warning"></i>
              <i v-else-if="check.status === 'failed'" class="icon-x-circle"></i>
            </div>
            
            <div class="check-content">
              <h4>{{ check.title }}</h4>
              <p>{{ check.description }}</p>
              <small v-if="check.details">{{ check.details }}</small>
            </div>
          </div>
        </div>

        <div v-if="compatibilityError" class="error-message">
          <i class="icon-alert-triangle"></i>
          <div>
            <h4>{{ $t('biometric.compatibility.error.title') }}</h4>
            <p>{{ compatibilityError }}</p>
          </div>
        </div>
      </div>

      <!-- Step 3: Method Selection -->
      <div v-else-if="currentStepIndex === 2" class="step-method-selection">
        <div class="methods-grid">
          <div 
            v-for="method in availableMethods" 
            :key="method.type"
            class="method-card"
            :class="{ 
              'method-selected': selectedMethods.includes(method.type),
              'method-disabled': !method.available
            }"
            @click="toggleMethod(method.type)"
          >
            <div class="method-icon">
              <i :class="method.icon"></i>
            </div>
            
            <div class="method-info">
              <h4>{{ method.title }}</h4>
              <p>{{ method.description }}</p>
              
              <div class="method-features">
                <span 
                  v-for="feature in method.features" 
                  :key="feature"
                  class="feature-tag"
                >
                  {{ $t(feature) }}
                </span>
              </div>
            </div>

            <div class="method-status">
              <i v-if="method.available" class="icon-check-circle"></i>
              <i v-else class="icon-x-circle"></i>
            </div>
          </div>
        </div>

        <div class="selection-notice">
          <i class="icon-info"></i>
          <p>{{ $t('biometric.selection.notice') }}</p>
        </div>
      </div>

      <!-- Step 4: Biometric Enrollment -->
      <div v-else-if="currentStepIndex === 3" class="step-enrollment">
        <div class="enrollment-container">
          <!-- Current method being enrolled -->
          <div class="current-method">
            <div class="method-header">
              <i :class="currentEnrollmentMethod.icon"></i>
              <h3>{{ currentEnrollmentMethod.title }}</h3>
            </div>

            <!-- Enrollment interface based on method -->
            <div class="enrollment-interface">
              <!-- Fingerprint enrollment -->
              <div v-if="currentEnrollmentMethod.type === 'fingerprint'" class="fingerprint-enrollment">
                <div class="fingerprint-scanner">
                  <div 
                    class="scanner-area"
                    :class="{ 
                      'scanning': isScanning,
                      'success': scanSuccess,
                      'error': scanError
                    }"
                  >
                    <i class="icon-fingerprint"></i>
                    <div class="scan-rings">
                      <div class="ring ring-1"></div>
                      <div class="ring ring-2"></div>
                      <div class="ring ring-3"></div>
                    </div>
                  </div>
                </div>

                <div class="enrollment-instructions">
                  <p>{{ currentEnrollmentInstruction }}</p>
                  
                  <div class="scan-progress">
                    <div class="progress-dots">
                      <div 
                        v-for="n in 5" 
                        :key="n"
                        class="progress-dot"
                        :class="{ 'completed': fingerprintScans >= n }"
                      ></div>
                    </div>
                    <span>{{ formatScanProgress(fingerprintScans, 5) }}</span>
                  </div>
                </div>
              </div>

              <!-- Face recognition enrollment -->
              <div v-else-if="currentEnrollmentMethod.type === 'face'" class="face-enrollment">
                <div class="camera-container">
                  <video 
                    ref="cameraVideo" 
                    class="camera-preview"
                    :class="{ 'face-detected': faceDetected }"
                    autoplay 
                    muted 
                    playsinline
                  ></video>
                  
                  <div class="face-outline">
                    <div class="outline-frame"></div>
                  </div>

                  <canvas ref="faceCanvas" class="face-canvas" style="display: none;"></canvas>
                </div>

                <div class="face-instructions">
                  <p>{{ currentFaceInstruction }}</p>
                  
                  <div class="capture-progress">
                    <div class="progress-steps">
                      <div 
                        v-for="step in faceSteps" 
                        :key="step.name"
                        class="step-item"
                        :class="{ 'completed': step.completed, 'active': step.active }"
                      >
                        <i :class="step.icon"></i>
                        <span>{{ step.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Voice recognition enrollment -->
              <div v-else-if="currentEnrollmentMethod.type === 'voice'" class="voice-enrollment">
                <div class="voice-recorder">
                  <div 
                    class="voice-visualizer"
                    :class="{ 'recording': isRecording }"
                  >
                    <div class="voice-waves">
                      <div 
                        v-for="n in 8" 
                        :key="n"
                        class="wave-bar"
                        :style="{ height: `${voiceLevel * (Math.sin(n) + 1) * 50}%` }"
                      ></div>
                    </div>
                  </div>

                  <button 
                    class="record-button"
                    :class="{ 'recording': isRecording }"
                    @click="toggleVoiceRecording"
                  >
                    <i :class="isRecording ? 'icon-square' : 'icon-mic'"></i>
                  </button>
                </div>

                <div class="voice-instructions">
                  <p>{{ currentVoiceInstruction }}</p>
                  
                  <div class="phrase-container">
                    <div class="phrase-text">
                      "{{ currentVoicePhrase }}"
                    </div>
                    
                    <div class="recording-progress">
                      <div class="progress-indicator">
                        <div 
                          class="progress-fill"
                          :style="{ width: `${voiceProgress}%` }"
                        ></div>
                      </div>
                      <span>{{ formatVoiceProgress(voiceAttempts, 3) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Method status -->
            <div class="method-status-bar">
              <div class="status-info">
                <i :class="enrollmentStatusIcon"></i>
                <span>{{ enrollmentStatusText }}</span>
              </div>
              
              <div class="status-actions">
                <button 
                  v-if="canRetryEnrollment"
                  class="btn-retry"
                  @click="retryEnrollment"
                >
                  <i class="icon-refresh"></i>
                  {{ $t('biometric.enrollment.retry') }}
                </button>
                
                <button 
                  v-if="canSkipMethod"
                  class="btn-skip"
                  @click="skipMethod"
                >
                  {{ $t('biometric.enrollment.skip') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Remaining methods queue -->
          <div v-if="remainingMethods.length > 0" class="remaining-methods">
            <h4>{{ $t('biometric.enrollment.remaining') }}</h4>
            <div class="method-queue">
              <div 
                v-for="method in remainingMethods" 
                :key="method.type"
                class="queue-item"
              >
                <i :class="method.icon"></i>
                <span>{{ method.title }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 5: Verification -->
      <div v-else-if="currentStepIndex === 4" class="step-verification">
        <div class="verification-container">
          <div class="verification-header">
            <i class="icon-shield-check"></i>
            <h3>{{ $t('biometric.verification.title') }}</h3>
            <p>{{ $t('biometric.verification.description') }}</p>
          </div>

          <div class="enrolled-methods">
            <h4>{{ $t('biometric.verification.enrolled_methods') }}</h4>
            <div class="methods-list">
              <div 
                v-for="method in enrolledMethods" 
                :key="method.type"
                class="enrolled-method"
              >
                <div class="method-info">
                  <i :class="method.icon"></i>
                  <span>{{ method.title }}</span>
                </div>
                
                <div class="verification-status">
                  <button 
                    class="btn-test"
                    :disabled="method.testing"
                    @click="testMethod(method)"
                  >
                    <i v-if="method.testing" class="icon-spinner spin"></i>
                    <i v-else-if="method.verified" class="icon-check"></i>
                    <i v-else class="icon-play"></i>
                    {{ method.testing ? $t('biometric.verification.testing') : 
                        method.verified ? $t('biometric.verification.verified') : 
                        $t('biometric.verification.test') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="verification-options">
            <div class="option-group">
              <h4>{{ $t('biometric.verification.options.title') }}</h4>
              
              <label class="option-item">
                <input 
                  type="checkbox" 
                  v-model="verificationOptions.requireMultiple"
                >
                <span>{{ $t('biometric.verification.options.require_multiple') }}</span>
              </label>
              
              <label class="option-item">
                <input 
                  type="checkbox" 
                  v-model="verificationOptions.allowFallback"
                >
                <span>{{ $t('biometric.verification.options.allow_fallback') }}</span>
              </label>
              
              <label class="option-item">
                <input 
                  type="checkbox" 
                  v-model="verificationOptions.requireStrongAuth"
                >
                <span>{{ $t('biometric.verification.options.require_strong') }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 6: Completion -->
      <div v-else-if="currentStepIndex === 5" class="step-completion">
        <div class="completion-container">
          <div class="success-animation">
            <div class="success-icon">
              <i class="icon-check-circle"></i>
            </div>
            <div class="celebration-particles">
              <div v-for="n in 12" :key="n" class="particle"></div>
            </div>
          </div>

          <div class="completion-content">
            <h3>{{ $t('biometric.completion.title') }}</h3>
            <p>{{ $t('biometric.completion.description') }}</p>
          </div>

          <div class="enrollment-summary">
            <h4>{{ $t('biometric.completion.summary') }}</h4>
            <div class="summary-stats">
              <div class="stat-item">
                <span class="stat-value">{{ enrolledMethods.length }}</span>
                <span class="stat-label">{{ $t('biometric.completion.methods_enrolled') }}</span>
              </div>
              
              <div class="stat-item">
                <span class="stat-value">{{ formatTime(enrollmentDuration) }}</span>
                <span class="stat-label">{{ $t('biometric.completion.time_taken') }}</span>
              </div>
              
              <div class="stat-item">
                <span class="stat-value">{{ securityLevel }}</span>
                <span class="stat-label">{{ $t('biometric.completion.security_level') }}</span>
              </div>
            </div>
          </div>

          <div class="next-steps">
            <h4>{{ $t('biometric.completion.next_steps') }}</h4>
            <ul>
              <li>{{ $t('biometric.completion.step1') }}</li>
              <li>{{ $t('biometric.completion.step2') }}</li>
              <li>{{ $t('biometric.completion.step3') }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation buttons -->
    <div class="enrollment-actions">
      <button 
        v-if="currentStepIndex > 0 && currentStepIndex < totalSteps - 1"
        class="btn-secondary"
        @click="previousStep"
      >
        <i class="icon-arrow-left"></i>
        {{ $t('biometric.navigation.previous') }}
      </button>

      <div class="actions-spacer"></div>

      <button 
        v-if="currentStepIndex < totalSteps - 1"
        class="btn-primary"
        :disabled="!canProceed"
        @click="nextStep"
      >
        {{ $t('biometric.navigation.next') }}
        <i class="icon-arrow-right"></i>
      </button>

      <button 
        v-else
        class="btn-primary"
        @click="completeEnrollment"
      >
        {{ $t('biometric.navigation.complete') }}
        <i class="icon-check"></i>
      </button>

      <button 
        class="btn-text"
        @click="cancelEnrollment"
      >
        {{ $t('biometric.navigation.cancel') }}
      </button>
    </div>

    <!-- Error dialog -->
    <div v-if="showErrorDialog" class="error-dialog-overlay" @click="closeErrorDialog">
      <div class="error-dialog" @click.stop>
        <div class="dialog-header">
          <h3>{{ errorDialog.title }}</h3>
          <button class="btn-close" @click="closeErrorDialog">
            <i class="icon-x"></i>
          </button>
        </div>
        
        <div class="dialog-content">
          <p>{{ errorDialog.message }}</p>
          
          <div v-if="errorDialog.suggestions" class="error-suggestions">
            <h4>{{ $t('biometric.error.suggestions') }}</h4>
            <ul>
              <li v-for="suggestion in errorDialog.suggestions" :key="suggestion">
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
        
        <div class="dialog-actions">
          <button class="btn-secondary" @click="closeErrorDialog">
            {{ $t('biometric.error.dismiss') }}
          </button>
          
          <button 
            v-if="errorDialog.canRetry"
            class="btn-primary" 
            @click="retryAfterError"
          >
            {{ $t('biometric.error.retry') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useBiometricAuth } from '@/composables/useBiometricAuth'
import { useHapticFeedback } from '@/composables/useHapticFeedback'

// Types
interface BiometricMethod {
  type: 'fingerprint' | 'face' | 'voice'
  title: string
  description: string
  icon: string
  available: boolean
  features: string[]
  enrolled?: boolean
  verified?: boolean
  testing?: boolean
}

interface EnrollmentStep {
  title: string
  description: string
  component: string
}

interface CompatibilityCheck {
  name: string
  title: string
  description: string
  status: 'checking' | 'passed' | 'warning' | 'failed'
  details?: string
}

// Composables
const { t } = useI18n()
const { 
  isSupported, 
  enroll, 
  verify, 
  getAvailableMethods,
  checkCompatibility 
} = useBiometricAuth()
const { workshopHaptics } = useHapticFeedback()

// Props
interface Props {
  isRTL?: boolean
  onComplete?: (methods: BiometricMethod[]) => void
  onCancel?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  isRTL: true,
  onComplete: () => {},
  onCancel: () => {}
})

// Reactive state
const currentStepIndex = ref(0)
const enrollmentStartTime = ref<Date | null>(null)
const selectedMethods = ref<string[]>([])
const enrolledMethods = ref<BiometricMethod[]>([])
const currentEnrollmentMethodIndex = ref(0)

// Enrollment state
const isScanning = ref(false)
const scanSuccess = ref(false)
const scanError = ref(false)
const fingerprintScans = ref(0)

const faceDetected = ref(false)
const faceSteps = ref([
  { name: 'front', label: t('biometric.face.front'), icon: 'icon-user', completed: false, active: true },
  { name: 'left', label: t('biometric.face.left'), icon: 'icon-rotate-ccw', completed: false, active: false },
  { name: 'right', label: t('biometric.face.right'), icon: 'icon-rotate-cw', completed: false, active: false }
])

const isRecording = ref(false)
const voiceLevel = ref(0)
const voiceProgress = ref(0)
const voiceAttempts = ref(0)

// Verification state
const verificationOptions = reactive({
  requireMultiple: false,
  allowFallback: true,
  requireStrongAuth: false
})

// Error handling
const showErrorDialog = ref(false)
const errorDialog = reactive({
  title: '',
  message: '',
  suggestions: [] as string[],
  canRetry: false
})

const compatibilityError = ref('')

// Steps configuration
const enrollmentSteps: EnrollmentStep[] = [
  {
    title: t('biometric.steps.welcome.title'),
    description: t('biometric.steps.welcome.description'),
    component: 'welcome'
  },
  {
    title: t('biometric.steps.compatibility.title'),
    description: t('biometric.steps.compatibility.description'),
    component: 'compatibility'
  },
  {
    title: t('biometric.steps.selection.title'),
    description: t('biometric.steps.selection.description'),
    component: 'selection'
  },
  {
    title: t('biometric.steps.enrollment.title'),
    description: t('biometric.steps.enrollment.description'),
    component: 'enrollment'
  },
  {
    title: t('biometric.steps.verification.title'),
    description: t('biometric.steps.verification.description'),
    component: 'verification'
  },
  {
    title: t('biometric.steps.completion.title'),
    description: t('biometric.steps.completion.description'),
    component: 'completion'
  }
]

const totalSteps = enrollmentSteps.length

// Available biometric methods
const availableMethods = ref<BiometricMethod[]>([
  {
    type: 'fingerprint',
    title: t('biometric.methods.fingerprint.title'),
    description: t('biometric.methods.fingerprint.description'),
    icon: 'icon-fingerprint',
    available: false,
    features: ['biometric.features.fast', 'biometric.features.secure', 'biometric.features.convenient']
  },
  {
    type: 'face',
    title: t('biometric.methods.face.title'),
    description: t('biometric.methods.face.description'),
    icon: 'icon-user-check',
    available: false,
    features: ['biometric.features.touchless', 'biometric.features.natural', 'biometric.features.modern']
  },
  {
    type: 'voice',
    title: t('biometric.methods.voice.title'),
    description: t('biometric.methods.voice.description'),
    icon: 'icon-mic',
    available: false,
    features: ['biometric.features.arabic', 'biometric.features.remote', 'biometric.features.accessible']
  }
])

// Compatibility checks
const compatibilityChecks = ref<CompatibilityCheck[]>([
  {
    name: 'webauthn',
    title: t('biometric.compatibility.webauthn.title'),
    description: t('biometric.compatibility.webauthn.description'),
    status: 'checking'
  },
  {
    name: 'biometric_hardware',
    title: t('biometric.compatibility.hardware.title'),
    description: t('biometric.compatibility.hardware.description'),
    status: 'checking'
  },
  {
    name: 'secure_context',
    title: t('biometric.compatibility.secure.title'),
    description: t('biometric.compatibility.secure.description'),
    status: 'checking'
  },
  {
    name: 'user_verification',
    title: t('biometric.compatibility.verification.title'),
    description: t('biometric.compatibility.verification.description'),
    status: 'checking'
  }
])

// Benefits list
const benefits = [
  {
    key: 'security',
    icon: 'icon-shield',
    text: 'biometric.benefits.security'
  },
  {
    key: 'convenience',
    icon: 'icon-zap',
    text: 'biometric.benefits.convenience'
  },
  {
    key: 'speed',
    icon: 'icon-clock',
    text: 'biometric.benefits.speed'
  },
  {
    key: 'accessibility',
    icon: 'icon-accessibility',
    text: 'biometric.benefits.accessibility'
  }
]

// Computed properties
const currentStep = computed(() => enrollmentSteps[currentStepIndex.value])

const enrollmentProgress = computed(() => 
  ((currentStepIndex.value + 1) / totalSteps) * 100
)

const currentEnrollmentMethod = computed(() => {
  const selectedMethodTypes = selectedMethods.value
  if (currentEnrollmentMethodIndex.value < selectedMethodTypes.length) {
    const methodType = selectedMethodTypes[currentEnrollmentMethodIndex.value]
    return availableMethods.value.find(m => m.type === methodType)!
  }
  return availableMethods.value[0]
})

const remainingMethods = computed(() => {
  const selectedMethodTypes = selectedMethods.value
  return selectedMethodTypes.slice(currentEnrollmentMethodIndex.value + 1)
    .map(type => availableMethods.value.find(m => m.type === type)!)
    .filter(Boolean)
})

const canProceed = computed(() => {
  switch (currentStepIndex.value) {
    case 0: return true // Welcome
    case 1: return !compatibilityError.value // Compatibility
    case 2: return selectedMethods.value.length > 0 // Selection
    case 3: return enrolledMethods.value.length > 0 // Enrollment
    case 4: return enrolledMethods.value.every(m => m.verified) // Verification
    default: return true
  }
})

const canRetryEnrollment = computed(() => 
  scanError.value || (fingerprintScans.value > 0 && fingerprintScans.value < 5)
)

const canSkipMethod = computed(() => 
  selectedMethods.value.length > 1 && currentEnrollmentMethodIndex.value < selectedMethods.value.length - 1
)

const enrollmentStatusIcon = computed(() => {
  if (scanSuccess.value) return 'icon-check-circle'
  if (scanError.value) return 'icon-x-circle'
  if (isScanning.value) return 'icon-spinner spin'
  return 'icon-circle'
})

const enrollmentStatusText = computed(() => {
  if (scanSuccess.value) return t('biometric.enrollment.status.success')
  if (scanError.value) return t('biometric.enrollment.status.error')
  if (isScanning.value) return t('biometric.enrollment.status.scanning')
  return t('biometric.enrollment.status.ready')
})

const currentEnrollmentInstruction = computed(() => {
  if (fingerprintScans.value === 0) {
    return t('biometric.fingerprint.instruction.initial')
  } else if (fingerprintScans.value < 5) {
    return t('biometric.fingerprint.instruction.continue', { count: fingerprintScans.value })
  } else {
    return t('biometric.fingerprint.instruction.complete')
  }
})

const currentFaceInstruction = computed(() => {
  const activeStep = faceSteps.value.find(step => step.active)
  return t(`biometric.face.instruction.${activeStep?.name || 'front'}`)
})

const currentVoiceInstruction = computed(() => {
  if (voiceAttempts.value === 0) {
    return t('biometric.voice.instruction.initial')
  } else if (voiceAttempts.value < 3) {
    return t('biometric.voice.instruction.repeat')
  } else {
    return t('biometric.voice.instruction.complete')
  }
})

const currentVoicePhrase = computed(() => {
  const phrases = [
    t('biometric.voice.phrase.1'),
    t('biometric.voice.phrase.2'),
    t('biometric.voice.phrase.3')
  ]
  return phrases[voiceAttempts.value % phrases.length]
})

const enrollmentDuration = computed(() => {
  if (!enrollmentStartTime.value) return 0
  return Date.now() - enrollmentStartTime.value.getTime()
})

const securityLevel = computed(() => {
  const methodCount = enrolledMethods.value.length
  if (methodCount >= 3) return t('biometric.security.level.maximum')
  if (methodCount >= 2) return t('biometric.security.level.high')
  if (methodCount >= 1) return t('biometric.security.level.medium')
  return t('biometric.security.level.low')
})

// Refs for camera and canvas
const cameraVideo = ref<HTMLVideoElement>()
const faceCanvas = ref<HTMLCanvasElement>()

// Methods
function formatProgress(current: number, total: number): string {
  if (props.isRTL) {
    const arabicCurrent = current.toString().replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
    const arabicTotal = total.toString().replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
    return `${arabicCurrent} من ${arabicTotal}`
  }
  return `${current} of ${total}`
}

function formatScanProgress(current: number, total: number): string {
  return formatProgress(current, total) + ' ' + t('biometric.fingerprint.scans')
}

function formatVoiceProgress(current: number, total: number): string {
  return formatProgress(current, total) + ' ' + t('biometric.voice.attempts')
}

function formatTime(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  
  if (props.isRTL) {
    const arabicMinutes = minutes.toString().replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
    const arabicSeconds = (seconds % 60).toString().replace(/[0-9]/g, (d) => '٠١٢٣٤٥٦٧٨٩'[parseInt(d)])
    return `${arabicMinutes}:${arabicSeconds.padStart(2, '٠')}`
  }
  
  return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`
}

async function nextStep() {
  if (!canProceed.value) return

  // Perform step-specific actions
  switch (currentStepIndex.value) {
    case 0:
      enrollmentStartTime.value = new Date()
      break
    case 1:
      await checkDeviceCompatibility()
      break
    case 2:
      await startEnrollment()
      break
    case 3:
      await completeCurrentMethodEnrollment()
      break
  }

  if (currentStepIndex.value < totalSteps - 1) {
    currentStepIndex.value++
    workshopHaptics.pageChange()
  }
}

function previousStep() {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
    workshopHaptics.pageChange()
  }
}

async function checkDeviceCompatibility() {
  for (const check of compatibilityChecks.value) {
    check.status = 'checking'
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate check time
      
      switch (check.name) {
        case 'webauthn':
          if (window.PublicKeyCredential) {
            check.status = 'passed'
            check.details = t('biometric.compatibility.webauthn.supported')
          } else {
            check.status = 'failed'
            check.details = t('biometric.compatibility.webauthn.not_supported')
          }
          break
          
        case 'biometric_hardware':
          const available = await getAvailableMethods()
          availableMethods.value.forEach(method => {
            method.available = available.includes(method.type)
          })
          
          if (available.length > 0) {
            check.status = 'passed'
            check.details = t('biometric.compatibility.hardware.available', { count: available.length })
          } else {
            check.status = 'warning'
            check.details = t('biometric.compatibility.hardware.limited')
          }
          break
          
        case 'secure_context':
          if (window.isSecureContext) {
            check.status = 'passed'
            check.details = t('biometric.compatibility.secure.https')
          } else {
            check.status = 'failed'
            check.details = t('biometric.compatibility.secure.not_https')
          }
          break
          
        case 'user_verification':
          if (await checkCompatibility()) {
            check.status = 'passed'
            check.details = t('biometric.compatibility.verification.supported')
          } else {
            check.status = 'warning'
            check.details = t('biometric.compatibility.verification.limited')
          }
          break
      }
    } catch (error) {
      check.status = 'failed'
      check.details = error instanceof Error ? error.message : t('biometric.compatibility.unknown_error')
    }
  }

  // Check if any critical failures
  const criticalFailures = compatibilityChecks.value.filter(
    check => check.status === 'failed' && ['webauthn', 'secure_context'].includes(check.name)
  )

  if (criticalFailures.length > 0) {
    compatibilityError.value = t('biometric.compatibility.critical_error')
  }
}

function toggleMethod(methodType: string) {
  const method = availableMethods.value.find(m => m.type === methodType)
  if (!method?.available) return

  const index = selectedMethods.value.indexOf(methodType)
  if (index >= 0) {
    selectedMethods.value.splice(index, 1)
  } else {
    selectedMethods.value.push(methodType)
  }
  
  workshopHaptics.buttonPress()
}

async function startEnrollment() {
  if (selectedMethods.value.length === 0) return
  
  currentEnrollmentMethodIndex.value = 0
  enrolledMethods.value = []
  
  // Start with first method
  await enrollCurrentMethod()
}

async function enrollCurrentMethod() {
  const method = currentEnrollmentMethod.value
  if (!method) return

  try {
    switch (method.type) {
      case 'fingerprint':
        await enrollFingerprint()
        break
      case 'face':
        await enrollFace()
        break
      case 'voice':
        await enrollVoice()
        break
    }
  } catch (error) {
    showError(
      t('biometric.enrollment.error.title'),
      error instanceof Error ? error.message : t('biometric.enrollment.error.unknown'),
      [
        t('biometric.enrollment.error.suggestion1'),
        t('biometric.enrollment.error.suggestion2'),
        t('biometric.enrollment.error.suggestion3')
      ],
      true
    )
  }
}

async function enrollFingerprint() {
  fingerprintScans.value = 0
  
  for (let scan = 0; scan < 5; scan++) {
    isScanning.value = true
    scanError.value = false
    scanSuccess.value = false
    
    try {
      // Simulate fingerprint scanning
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          const success = Math.random() > 0.2 // 80% success rate
          if (success) {
            scanSuccess.value = true
            fingerprintScans.value++
            workshopHaptics.scanSuccess()
            resolve(true)
          } else {
            scanError.value = true
            workshopHaptics.scanError()
            reject(new Error(t('biometric.fingerprint.scan_failed')))
          }
        }, 2000)

        // Allow manual trigger for testing
        const handleClick = () => {
          clearTimeout(timeout)
          scanSuccess.value = true
          fingerprintScans.value++
          workshopHaptics.scanSuccess()
          resolve(true)
          document.removeEventListener('click', handleClick)
        }
        document.addEventListener('click', handleClick, { once: true })
      })
      
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      if (scan < 4) continue // Retry
      throw error
    } finally {
      isScanning.value = false
    }
  }

  // Mark method as enrolled
  const enrolledMethod = { ...currentEnrollmentMethod.value, enrolled: true }
  enrolledMethods.value.push(enrolledMethod)
  workshopHaptics.serviceComplete()
}

async function enrollFace() {
  try {
    // Start camera
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'user' } 
    })
    
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = stream
    }

    // Simulate face detection and capture process
    for (let stepIndex = 0; stepIndex < faceSteps.value.length; stepIndex++) {
      const step = faceSteps.value[stepIndex]
      step.active = true
      
      // Wait for face positioning
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      faceDetected.value = true
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      step.completed = true
      step.active = false
      workshopHaptics.scanSuccess()
    }

    // Stop camera
    const tracks = stream.getTracks()
    tracks.forEach(track => track.stop())

    // Mark method as enrolled
    const enrolledMethod = { ...currentEnrollmentMethod.value, enrolled: true }
    enrolledMethods.value.push(enrolledMethod)
    workshopHaptics.serviceComplete()
    
  } catch (error) {
    throw new Error(t('biometric.face.camera_error'))
  }
}

async function enrollVoice() {
  voiceAttempts.value = 0
  
  for (let attempt = 0; attempt < 3; attempt++) {
    isRecording.value = false
    voiceLevel.value = 0
    voiceProgress.value = 0
    
    // Wait for user to start recording
    await new Promise(resolve => {
      const startRecording = () => {
        isRecording.value = true
        workshopHaptics.buttonPress()
        resolve(true)
      }
      
      // This would be triggered by the record button
      window.addEventListener('voice-record-start', startRecording, { once: true })
      
      // Auto-start after 2 seconds for demo
      setTimeout(startRecording, 2000)
    })

    // Simulate recording
    await new Promise(resolve => {
      const duration = 3000
      const interval = setInterval(() => {
        voiceLevel.value = Math.random()
        voiceProgress.value = Math.min(voiceProgress.value + 2, 100)
      }, 50)

      setTimeout(() => {
        clearInterval(interval)
        isRecording.value = false
        voiceAttempts.value++
        workshopHaptics.scanSuccess()
        resolve(true)
      }, duration)
    })
  }

  // Mark method as enrolled
  const enrolledMethod = { ...currentEnrollmentMethod.value, enrolled: true }
  enrolledMethods.value.push(enrolledMethod)
  workshopHaptics.serviceComplete()
}

async function completeCurrentMethodEnrollment() {
  if (currentEnrollmentMethodIndex.value < selectedMethods.value.length - 1) {
    currentEnrollmentMethodIndex.value++
    await enrollCurrentMethod()
  }
}

function retryEnrollment() {
  scanError.value = false
  scanSuccess.value = false
  fingerprintScans.value = Math.max(0, fingerprintScans.value - 1)
  enrollCurrentMethod()
}

function skipMethod() {
  if (canSkipMethod.value) {
    currentEnrollmentMethodIndex.value++
    if (currentEnrollmentMethodIndex.value < selectedMethods.value.length) {
      enrollCurrentMethod()
    }
  }
}

async function testMethod(method: BiometricMethod) {
  method.testing = true
  
  try {
    // Simulate verification test
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const success = Math.random() > 0.1 // 90% success rate
    if (success) {
      method.verified = true
      workshopHaptics.scanSuccess()
    } else {
      throw new Error(t('biometric.verification.test_failed'))
    }
  } catch (error) {
    workshopHaptics.scanError()
    showError(
      t('biometric.verification.error.title'),
      error instanceof Error ? error.message : t('biometric.verification.error.unknown'),
      [t('biometric.verification.error.suggestion')],
      true
    )
  } finally {
    method.testing = false
  }
}

function toggleVoiceRecording() {
  if (isRecording.value) {
    window.dispatchEvent(new CustomEvent('voice-record-stop'))
  } else {
    window.dispatchEvent(new CustomEvent('voice-record-start'))
  }
}

function showError(title: string, message: string, suggestions: string[] = [], canRetry: boolean = false) {
  errorDialog.title = title
  errorDialog.message = message
  errorDialog.suggestions = suggestions
  errorDialog.canRetry = canRetry
  showErrorDialog.value = true
}

function closeErrorDialog() {
  showErrorDialog.value = false
}

function retryAfterError() {
  closeErrorDialog()
  enrollCurrentMethod()
}

function completeEnrollment() {
  props.onComplete(enrolledMethods.value)
  workshopHaptics.serviceComplete()
}

function cancelEnrollment() {
  props.onCancel()
}

// Lifecycle
onMounted(async () => {
  if (!isSupported.value) {
    showError(
      t('biometric.error.not_supported.title'),
      t('biometric.error.not_supported.message'),
      [t('biometric.error.not_supported.suggestion')]
    )
  }
})

onUnmounted(() => {
  // Clean up camera streams
  if (cameraVideo.value?.srcObject) {
    const stream = cameraVideo.value.srcObject as MediaStream
    stream.getTracks().forEach(track => track.stop())
  }
})
</script>

<style scoped>
/* Add comprehensive styling for the biometric enrollment flow */
.biometric-enrollment {
  @apply max-w-4xl mx-auto p-6 bg-white dark:bg-gray-900 rounded-lg shadow-lg;
}

.enrollment-header {
  @apply text-center mb-8;
}

.title {
  @apply text-3xl font-bold text-gray-900 dark:text-white mb-2;
}

.subtitle {
  @apply text-lg text-gray-600 dark:text-gray-300 mb-6;
}

.progress-container {
  @apply flex items-center gap-4;
}

.progress-bar {
  @apply flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden;
}

.progress-fill {
  @apply h-full bg-blue-600 transition-all duration-300 ease-out;
}

.progress-text {
  @apply text-sm font-medium text-gray-600 dark:text-gray-300 min-w-[80px];
}

/* Add more comprehensive styling for each step component */
.enrollment-actions {
  @apply flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700;
}

.btn-primary {
  @apply px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors;
}

.btn-text {
  @apply px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors;
}

/* Add styles for all the enrollment components */
</style>