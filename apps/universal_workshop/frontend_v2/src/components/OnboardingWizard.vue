<template>
  <div class="onboarding-wizard" :class="{ 'rtl': isRTL }">
    <!-- Automotive Background Animation -->
    <div class="animated-background">
      <div class="automotive-scene">
        <div class="floating-cars">
          <div class="floating-car car-1">🚗</div>
          <div class="floating-car car-2">🚙</div>
          <div class="floating-car car-3">🚐</div>
        </div>
        <div class="floating-tools">
          <div class="floating-tool tool-1">🔧</div>
          <div class="floating-tool tool-2">⚙️</div>
          <div class="floating-tool tool-3">🛠️</div>
          <div class="floating-tool tool-4">🔩</div>
          <div class="floating-tool tool-5">🔨</div>
        </div>
        <div class="workshop-elements">
          <div class="workshop-building">🏢</div>
          <div class="garage-door">🚪</div>
          <div class="fuel-pump">⛽</div>
        </div>
      </div>
    </div>

    <!-- Main Container -->
    <div class="wizard-container">
      <!-- Header Section -->
      <header class="wizard-header">
        <div class="brand-section">
          <div class="brand-icon">
            <img 
              src="/assets/universal_workshop/images/logos/workshop_logo.svg" 
              alt="Universal Workshop" 
              class="workshop-logo"
            />
          </div>
          <div class="brand-text">
            <h1 class="brand-title">{{ $t('Universal Workshop') }}</h1>
            <p class="brand-subtitle">{{ $t('Professional Automotive Workshop Management System') }}</p>
            <div class="version-badge">
              <span class="badge-icon">⚡</span>
              {{ $t('Setup Wizard v2.0') }}
            </div>
          </div>
        </div>
        
        <div class="wizard-title-section">
          <h2 class="wizard-title">
            {{ isLicenseMode ? $t('Quick Setup') : $t('Workshop Setup Wizard') }}
          </h2>
          <p class="wizard-description">
            {{ isLicenseMode 
              ? $t('Complete your administrator setup to get started')
              : $t('Let\'s set up your workshop in just a few simple steps')
            }}
          </p>
        </div>
      </header>

      <!-- Automotive Progress Indicator -->
      <div class="progress-section">
        <div class="automotive-progress">
          <div class="road-line"></div>
          <div class="progress-car" :style="{ left: progressPercentage + '%' }">
            🚗
          </div>
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          <div 
            class="checkpoint" 
            v-for="(step, index) in steps" 
            :key="step.id"
            :style="{ left: ((index + 1) / steps.length * 100) + '%' }"
            :class="{ 'passed': index < currentStepIndex }"
          >
            🏁
          </div>
        </div>
        
        <div class="steps-indicator">
          <div
            v-for="(step, index) in steps"
            :key="step.id"
            class="step-indicator"
            :class="{
              'completed': index < currentStepIndex,
              'current': index === currentStepIndex,
              'upcoming': index > currentStepIndex
            }"
            @click="navigateToStep(index)"
          >
            <div class="step-icon-container">
              <img 
                :src="`/assets/universal_workshop/images/icons/${step.iconSvg}`"
                :alt="step.title"
                class="step-icon-img"
              />
              <div class="step-number">
                <div v-if="index < currentStepIndex" class="check-icon">✓</div>
                <span v-else>{{ index + 1 }}</span>
              </div>
            </div>
            <div class="step-label">{{ step.title }}</div>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <main class="wizard-content">
        <div class="content-container">
          <Transition name="slide" mode="out-in">
            <component
              :is="currentStepComponent"
              :key="currentStep.id"
              v-model="formData[currentStep.id]"
              :validation-errors="validationErrors"
              :is-loading="isLoading"
              @validate="updateStepData"
              @next="nextStep"
              @previous="previousStep"
              @complete="completeOnboarding"
            />
          </Transition>
        </div>
      </main>

      <!-- Navigation Footer -->
      <footer class="wizard-footer">
        <div class="footer-content">
          <button
            v-if="currentStepIndex > 0"
            @click="previousStep"
            class="btn btn-secondary"
            :disabled="isLoading"
          >
            <span class="btn-icon">←</span>
            {{ $t('Previous') }}
          </button>
          
          <div class="footer-spacer"></div>
          
          <button
            v-if="!isLastStep"
            @click="nextStep"
            class="btn btn-primary"
            :disabled="isLoading || !isCurrentStepValid"
            :class="{ 'loading': isLoading }"
          >
            {{ $t('Continue') }}
            <span class="btn-icon">→</span>
          </button>
          
          <button
            v-else
            @click="completeOnboarding"
            class="btn btn-success"
            :disabled="isLoading || !isCurrentStepValid"
            :class="{ 'loading': isLoading }"
          >
            <span class="btn-icon">🚀</span>
            {{ $t('Complete Setup') }}
          </button>
        </div>
      </footer>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner-ring"></div>
        <p class="loading-text">{{ loadingText }}</p>
      </div>
    </div>

    <!-- Mobile Enhancements -->
    <MobileEnhancements
      :current-step="currentStepIndex"
      :total-steps="steps.length"
      :is-loading="isLoading"
      :loading-message="loadingText"
      :show-hints="!isLoading && !showSuccessModal"
      @navigate="navigateToStep"
    />

    <!-- Automotive Success Modal -->
    <Teleport to="body">
      <div v-if="showSuccessModal" class="success-modal-overlay" @click="closeSuccessModal">
        <div class="success-modal" @click.stop>
          <div class="success-animation">
            <div class="celebration-car">🚗</div>
            <div class="celebration-tools">
              <span class="tool-1">🔧</span>
              <span class="tool-2">⚙️</span>
              <span class="tool-3">🛠️</span>
            </div>
            <div class="checkmark-circle">
              <div class="checkmark"></div>
            </div>
          </div>
          <h3 class="success-title">{{ $t('🎉 Workshop Setup Complete!') }}</h3>
          <p class="success-message">
            {{ isLicenseMode 
              ? $t('Your administrator account has been created successfully. You can now sign in to your automotive workshop management system.')
              : $t('Your Universal Workshop system is fully configured and ready to streamline your automotive business operations!')
            }}
          </p>
          <div class="success-features">
            <div class="feature-item">
              <i>🏢</i>
              <span>{{ $t('Workshop Configured') }}</span>
            </div>
            <div class="feature-item">
              <i>👥</i>
              <span>{{ $t('Admin Account Ready') }}</span>
            </div>
            <div class="feature-item">
              <i>📊</i>
              <span>{{ $t('Analytics Enabled') }}</span>
            </div>
          </div>
          <div class="success-details" v-if="workshopData || formData.admin_account">
            <div class="detail-item" v-if="workshopData?.workshop_code">
              <strong>{{ $t('Workshop Code') }}:</strong>
              <span class="workshop-code">{{ workshopData.workshop_code }}</span>
            </div>
            <div class="detail-item" v-if="formData.admin_account?.username">
              <strong>{{ $t('Admin Username') }}:</strong>
              <span class="admin-username">{{ formData.admin_account.username }}</span>
            </div>
            <div class="detail-item" v-if="formData.admin_account?.email">
              <strong>{{ $t('Admin Email') }}:</strong>
              <span class="admin-email">{{ formData.admin_account.email }}</span>
            </div>
          </div>
          <button @click="goToLogin" class="btn btn-primary">
            <i>🚀</i>
            {{ $t('Launch Dashboard') }}
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

// Essential Step Components
import LicenseVerificationStep from './steps/LicenseVerificationStep.vue'
import AdminAccountStep from './steps/AdminAccountStep.vue'
import WorkshopConfigStep from './steps/WorkshopConfigStep.vue'
import MobileEnhancements from './MobileEnhancements.vue'

// API Integration
import { OnboardingAPI } from '@/api/onboarding'

// Composables
import { useArabicUtils } from '@/composables/useArabicUtils'

const { t } = useI18n()
const router = useRouter()
const { isRTL } = useArabicUtils()

// State
const currentStepIndex = ref(0)
const formData = ref({})
const validationErrors = ref({})
const isLoading = ref(false)
const loadingText = ref('')
const showSuccessModal = ref(false)
const workshopData = ref(null)
const progressId = ref(null)
const isLicenseMode = ref(false)

// Simplified 3-Step Configuration
const essentialSteps = [
  {
    id: 'license_verification',
    title: t('License Verification'),
    component: LicenseVerificationStep,
    icon: '🏪',
    iconSvg: 'step_license.svg'
  },
  {
    id: 'admin_account',
    title: t('Administrator Account'),
    component: AdminAccountStep,
    icon: '👤',
    iconSvg: 'step_admin.svg'
  },
  {
    id: 'workshop_config',
    title: t('Workshop Configuration'),
    component: WorkshopConfigStep,
    icon: '⚙️',
    iconSvg: 'step_config.svg'
  }
]

const licenseSteps = [
  {
    id: 'admin_account',
    title: t('Administrator'),
    component: AdminAccountStep,
    icon: '👤',
    iconSvg: 'step_admin.svg'
  }
]

// Computed
const steps = computed(() => isLicenseMode.value ? licenseSteps : essentialSteps)
const currentStep = computed(() => steps.value[currentStepIndex.value])
const currentStepComponent = computed(() => currentStep.value?.component)
const isLastStep = computed(() => currentStepIndex.value === steps.value.length - 1)
const progressPercentage = computed(() => 
  ((currentStepIndex.value + 1) / steps.value.length) * 100
)
const isCurrentStepValid = computed(() => {
  const stepId = currentStep.value?.id
  const stepData = formData.value[stepId]
  const errors = validationErrors.value[stepId]
  return stepData && Object.keys(stepData).length > 0 && (!errors || errors.length === 0)
})

// Component Registration
const componentMap = {
  LicenseVerificationStep,
  AdminAccountStep,
  WorkshopConfigStep
}

// Methods
const initializeWizard = async () => {
  try {
    isLoading.value = true
    loadingText.value = t('Initializing setup wizard...')
    
    // Check for existing progress
    const progressResult = await OnboardingAPI.getUserProgress()
    
    if (progressResult.exists) {
      // Resume existing session
      progressId.value = progressResult.progress_id
      currentStepIndex.value = progressResult.current_step
      formData.value = progressResult.data
      
      // Ask user if they want to continue
      const shouldContinue = await showResumeDialog()
      if (!shouldContinue) {
        await startNewWizard()
      }
    } else {
      await startNewWizard()
    }
    
    // Check if license mode
    isLicenseMode.value = await OnboardingAPI.isLicenseMode()
    
  } catch (error) {
    console.error('Failed to initialize wizard:', error)
    showError(t('Failed to initialize setup wizard'))
  } finally {
    isLoading.value = false
  }
}

const startNewWizard = async () => {
  const result = await OnboardingAPI.startWizard()
  if (result.success) {
    progressId.value = result.progress_id
    currentStepIndex.value = 0
    formData.value = {}
  } else {
    throw new Error(result.message)
  }
}

const updateStepData = (data: any) => {
  const stepId = currentStep.value?.id
  if (stepId) {
    formData.value[stepId] = data
  }
}

const validateCurrentStep = async () => {
  if (!currentStep.value) return false
  
  try {
    const stepId = currentStep.value.id
    const stepData = formData.value[stepId] || {}
    
    const result = await OnboardingAPI.validateStep(stepId, stepData)
    
    if (result.valid) {
      validationErrors.value[stepId] = []
      return true
    } else {
      validationErrors.value[stepId] = result.errors
      return false
    }
  } catch (error) {
    console.error('Validation error:', error)
    return false
  }
}

const saveCurrentStep = async () => {
  if (!currentStep.value || !progressId.value) return false
  
  try {
    const stepId = currentStep.value.id
    const stepData = formData.value[stepId] || {}
    
    const result = await OnboardingAPI.saveStep(progressId.value, stepId, stepData)
    
    if (result.success) {
      return true
    } else {
      validationErrors.value[stepId] = result.errors
      return false
    }
  } catch (error) {
    console.error('Save error:', error)
    return false
  }
}

const nextStep = async () => {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    loadingText.value = t('Validating and saving...')
    
    // Validate current step
    const isValid = await validateCurrentStep()
    if (!isValid) return
    
    // Save current step
    const isSaved = await saveCurrentStep()
    if (!isSaved) return
    
    // Move to next step
    if (currentStepIndex.value < steps.value.length - 1) {
      currentStepIndex.value++
    }
    
  } catch (error) {
    console.error('Error in nextStep:', error)
    showError(t('Failed to proceed to next step'))
  } finally {
    isLoading.value = false
  }
}

const previousStep = () => {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
  }
}

const navigateToStep = (stepIndex: number) => {
  if (stepIndex <= currentStepIndex.value) {
    currentStepIndex.value = stepIndex
  }
}

const completeOnboarding = async () => {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    loadingText.value = t('Completing setup...')
    
    // Validate and save current step first
    const isValid = await validateCurrentStep()
    if (!isValid) return
    
    const isSaved = await saveCurrentStep()
    if (!isSaved) return
    
    // Complete onboarding
    const result = await OnboardingAPI.completeOnboarding(progressId.value)
    
    if (result.success) {
      workshopData.value = result
      showSuccessModal.value = true
    } else {
      showError(result.errors?.[0] || t('Failed to complete setup'))
    }
    
  } catch (error) {
    console.error('Error completing onboarding:', error)
    showError(t('Failed to complete setup'))
  } finally {
    isLoading.value = false
  }
}

const showResumeDialog = (): Promise<boolean> => {
  return new Promise((resolve) => {
    // Implementation would show a modern dialog
    // For now, just continue
    resolve(true)
  })
}

const showError = (message: string) => {
  // Implementation would show a toast notification
  console.error(message)
}

const closeSuccessModal = () => {
  showSuccessModal.value = false
}

const goToLogin = () => {
  // Navigate to login page with workshop info and first-login flag
  router.push({
    path: '/login',
    query: {
      firstLogin: 'true',
      workshop: workshopData.value?.workshop_name || '',
      adminUsername: formData.value.admin_account?.username || ''
    }
  })
}

// Lifecycle
onMounted(() => {
  initializeWizard()
})

// Watch for step changes to auto-save progress
watch(currentStepIndex, () => {
  // Auto-save progress when step changes
  if (progressId.value) {
    // Implementation for auto-save
  }
})
</script>

<style scoped lang="scss">
.onboarding-wizard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

  &.rtl {
    direction: rtl;
    
    .btn-icon {
      transform: scaleX(-1);
    }
  }
}

.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

// Automotive Scene Elements
.automotive-scene {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.floating-cars {
  position: absolute;
  width: 100%;
  height: 100%;
  
  .floating-car {
    position: absolute;
    font-size: 2.5rem;
    opacity: 0.08;
    animation: carFloat 12s ease-in-out infinite;
    color: white;
    
    &.car-1 {
      top: 20%;
      left: 15%;
      animation-delay: 0s;
    }
    
    &.car-2 {
      top: 60%;
      right: 20%;
      animation-delay: -4s;
    }
    
    &.car-3 {
      bottom: 30%;
      left: 25%;
      animation-delay: -8s;
    }
  }
}

.floating-tools {
  position: absolute;
  width: 100%;
  height: 100%;
  
  .floating-tool {
    position: absolute;
    font-size: 1.8rem;
    opacity: 0.06;
    animation: toolFloat 15s ease-in-out infinite;
    color: white;
    
    &.tool-1 {
      top: 25%;
      left: 30%;
      animation-delay: 0s;
    }
    
    &.tool-2 {
      top: 45%;
      right: 35%;
      animation-delay: -3s;
    }
    
    &.tool-3 {
      bottom: 40%;
      left: 60%;
      animation-delay: -6s;
    }
    
    &.tool-4 {
      top: 70%;
      right: 50%;
      animation-delay: -9s;
    }
    
    &.tool-5 {
      top: 35%;
      left: 80%;
      animation-delay: -12s;
    }
  }
}

.workshop-elements {
  position: absolute;
  width: 100%;
  height: 100%;
  
  .workshop-building {
    position: absolute;
    bottom: 20px;
    right: 50px;
    font-size: 4rem;
    opacity: 0.1;
    color: white;
  }
  
  .garage-door {
    position: absolute;
    bottom: 30px;
    left: 100px;
    font-size: 3rem;
    opacity: 0.08;
    color: white;
  }
  
  .fuel-pump {
    position: absolute;
    bottom: 40px;
    right: 150px;
    font-size: 2.5rem;
    opacity: 0.06;
    color: white;
  }
}

@keyframes carFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.08; }
  25% { transform: translateY(-15px) rotate(2deg); opacity: 0.12; }
  50% { transform: translateY(-5px) rotate(-1deg); opacity: 0.06; }
  75% { transform: translateY(-20px) rotate(1deg); opacity: 0.10; }
}

@keyframes toolFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.06; }
  25% { transform: translateY(-10px) rotate(5deg); opacity: 0.08; }
  50% { transform: translateY(-5px) rotate(-3deg); opacity: 0.04; }
  75% { transform: translateY(-15px) rotate(4deg); opacity: 0.07; }
}

.wizard-container {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 2rem;
  
  @media (max-width: 768px) {
    padding: 1rem 0.5rem;
    max-width: 100%;
  }
  
  @media (max-width: 480px) {
    padding: 0.5rem;
  }
}

.wizard-header {
  text-align: center;
  margin-bottom: 3rem;
  
  @media (max-width: 768px) {
    margin-bottom: 2rem;
  }
  
  .brand-section {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 2rem;
    
    @media (max-width: 768px) {
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }
  }
  
  .brand-icon {
    width: 100px;
    height: 100px;
    
    @media (max-width: 768px) {
      width: 80px;
      height: 80px;
    }
    
    @media (max-width: 480px) {
      width: 60px;
      height: 60px;
    }
    
    .workshop-logo {
      width: 100%;
      height: 100%;
      object-fit: contain;
      filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.2));
    }
  }
  
  .brand-text {
    text-align: left;
    
    @media (max-width: 768px) {
      text-align: center;
    }
    
    .rtl & {
      text-align: right;
      
      @media (max-width: 768px) {
        text-align: center;
      }
    }
  }
  
  .brand-title {
    color: white;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    
    @media (max-width: 768px) {
      font-size: 1.75rem;
    }
    
    @media (max-width: 480px) {
      font-size: 1.5rem;
    }
  }
  
  .brand-subtitle {
    color: rgba(255, 255, 255, 0.8);
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    
    @media (max-width: 768px) {
      font-size: 0.9rem;
      margin: 0 0 0.5rem 0;
    }
    
    @media (max-width: 480px) {
      font-size: 0.8rem;
      display: none; // Hide on very small screens
    }
  }
  
  .version-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, #f093fb, #f5576c);
    color: white;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
    
    .badge-icon {
      font-size: 1rem;
    }
  }
  
  .wizard-title-section {
    margin-top: 2rem;
  }
  
  .wizard-title {
    color: white;
    font-size: 2.5rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    
    @media (max-width: 768px) {
      font-size: 2rem;
    }
    
    @media (max-width: 480px) {
      font-size: 1.75rem;
    }
  }
  
  .wizard-description {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.1rem;
    margin: 0;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    
    @media (max-width: 768px) {
      font-size: 1rem;
      max-width: 90%;
    }
    
    @media (max-width: 480px) {
      font-size: 0.9rem;
    }
  }
}

// Automotive Progress Section
.progress-section {
  margin-bottom: 3rem;
}

.automotive-progress {
  position: relative;
  height: 60px;
  background: linear-gradient(to right, #e0e7ff 0%, #c7d2fe 100%);
  border-radius: 30px;
  margin-bottom: 3rem;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.3);
  
  @media (max-width: 768px) {
    height: 50px;
    margin-bottom: 2rem;
  }
  
  @media (max-width: 480px) {
    height: 40px;
    margin-bottom: 1.5rem;
  }
}

.road-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: repeating-linear-gradient(
    to right,
    rgba(255, 255, 255, 0.8) 0px,
    rgba(255, 255, 255, 0.8) 20px,
    transparent 20px,
    transparent 40px
  );
  transform: translateY(-1px);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 30px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.progress-car {
  position: absolute;
  top: 50%;
  transform: translateY(-50%) translateX(-50%);
  font-size: 2rem;
  z-index: 3;
  transition: left 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
  
  @media (max-width: 768px) {
    font-size: 1.75rem;
  }
  
  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
}

.checkpoint {
  position: absolute;
  top: 50%;
  transform: translateY(-50%) translateX(-50%);
  font-size: 1.2rem;
  z-index: 2;
  opacity: 0.3;
  transition: all 0.3s ease;
  
  &.passed {
    opacity: 1;
    transform: translateY(-50%) translateX(-50%) scale(1.2);
  }
}

.steps-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    gap: 0.75rem;
  }
}

// Enhanced Step Indicators with Automotive Icons
.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 1rem;
  border-radius: 12px;
  
  @media (max-width: 768px) {
    flex-direction: row;
    padding: 0.75rem 1rem;
    width: 100%;
    max-width: 300px;
    justify-content: flex-start;
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    padding: 0.5rem 0.75rem;
    max-width: 250px;
  }
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
  }
  
  &.completed {
    .step-icon-container {
      background: linear-gradient(135deg, #10b981, #059669);
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
      transform: scale(1.1);
    }
    
    .step-number {
      background: #10b981;
      border-color: white;
      color: white;
    }
  }
  
  &.current {
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.3);
    transform: translateY(-4px);
    
    .step-icon-container {
      background: linear-gradient(135deg, #667eea, #764ba2);
      box-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
      transform: scale(1.2);
    }
    
    .step-number {
      background: #667eea;
      border-color: white;
      color: white;
    }
  }
  
  &.upcoming {
    .step-icon-container {
      background: rgba(255, 255, 255, 0.2);
      border: 3px solid rgba(255, 255, 255, 0.3);
    }
    
    .step-number {
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.3);
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.step-icon-container {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 0.75rem;
  
  @media (max-width: 768px) {
    width: 50px;
    height: 50px;
    margin-bottom: 0;
    flex-shrink: 0;
  }
  
  @media (max-width: 480px) {
    width: 40px;
    height: 40px;
  }
  
  .step-icon-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
    transition: all 0.3s ease;
    filter: brightness(0) invert(1);
    
    @media (max-width: 768px) {
      width: 28px;
      height: 28px;
    }
    
    @media (max-width: 480px) {
      width: 24px;
      height: 24px;
    }
  }
  
  .step-number {
    position: absolute;
    bottom: -8px;
    right: -8px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.75rem;
    border: 2px solid white;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    
    @media (max-width: 768px) {
      width: 20px;
      height: 20px;
      font-size: 0.7rem;
      bottom: -6px;
      right: -6px;
    }
    
    @media (max-width: 480px) {
      width: 18px;
      height: 18px;
      font-size: 0.65rem;
    }
  }
}

.step-label {
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  opacity: 0.9;
  
  @media (max-width: 768px) {
    text-align: left;
    flex: 1;
  }
  
  @media (max-width: 480px) {
    font-size: 0.7rem;
  }
}

.check-icon {
  font-size: 1.2rem;
}

.wizard-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.content-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
  overflow: hidden;
  min-height: 400px;
  
  @media (max-width: 768px) {
    border-radius: 12px;
    margin: 0 0.5rem;
    min-height: 350px;
  }
  
  @media (max-width: 480px) {
    border-radius: 8px;
    margin: 0 0.25rem;
    min-height: 300px;
  }
}

.wizard-footer {
  margin-top: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    width: 100%;
  }
  
  @media (max-width: 480px) {
    gap: 0.75rem;
  }
}

.footer-spacer {
  flex: 1;
  
  @media (max-width: 768px) {
    display: none;
  }
}

.btn {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  position: relative;
  overflow: hidden;
  
  @media (max-width: 768px) {
    width: 100%;
    max-width: 300px;
    justify-content: center;
    padding: 1rem 2rem;
  }
  
  @media (max-width: 480px) {
    max-width: 250px;
    padding: 0.875rem 1.5rem;
    font-size: 0.9rem;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.loading::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shimmer 1.5s infinite;
  }
  
  &.btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(102, 126, 234, 0.6);
    }
  }
  
  &.btn-secondary {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    backdrop-filter: blur(10px);
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.3);
      transform: translateY(-2px);
    }
  }
  
  &.btn-success {
    background: linear-gradient(135deg, #00d4aa, #00b4db);
    color: white;
    box-shadow: 0 8px 24px rgba(0, 212, 170, 0.4);
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(0, 212, 170, 0.6);
    }
  }
}

.btn-icon {
  font-size: 1.1rem;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

// Mobile-specific optimizations
@media (max-width: 768px) {
  // Improve touch targets
  .step-indicator {
    min-height: 44px; // iOS recommended touch target
    padding: 0.75rem;
  }
  
  .btn {
    min-height: 44px;
    touch-action: manipulation; // Disable double-tap zoom
  }
  
  .form-control {
    min-height: 44px;
    touch-action: manipulation;
  }
  
  .checkbox-custom,
  .module-checkbox {
    min-width: 32px;
    min-height: 32px;
  }
  
  // Prevent zoom on inputs
  input[type="text"],
  input[type="email"],
  input[type="tel"],
  input[type="password"],
  select,
  textarea {
    font-size: 16px !important; // Prevents zoom on iOS
  }
  
  // Improve scrolling performance
  .wizard-container {
    -webkit-overflow-scrolling: touch;
  }
  
  .content-container {
    -webkit-overflow-scrolling: touch;
  }
  
  // Add safe area padding for devices with notches
  .wizard-header {
    padding-top: env(safe-area-inset-top, 0);
  }
  
  .wizard-footer {
    padding-bottom: env(safe-area-inset-bottom, 0);
  }
}

@media (max-width: 480px) {
  // Extra small screens optimizations
  .floating-cars,
  .floating-tools,
  .workshop-elements {
    display: none; // Hide background animations on very small screens
  }
  
  .wizard-header {
    margin-bottom: 1.5rem;
  }
  
  .progress-section {
    margin-bottom: 1.5rem;
  }
  
  .automotive-progress {
    margin-bottom: 1rem;
  }
}

// High DPI displays
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .workshop-logo,
  .step-icon-img {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }
}

// Landscape orientation on mobile
@media (max-width: 768px) and (orientation: landscape) {
  .wizard-header {
    margin-bottom: 1rem;
  }
  
  .brand-section {
    flex-direction: row;
    gap: 1rem;
  }
  
  .brand-icon {
    width: 60px;
    height: 60px;
  }
  
  .wizard-title {
    font-size: 1.5rem;
  }
  
  .wizard-description {
    font-size: 0.9rem;
  }
  
  .progress-section {
    margin-bottom: 1.5rem;
  }
  
  .automotive-progress {
    height: 40px;
  }
}

// Dark mode support for mobile
@media (prefers-color-scheme: dark) and (max-width: 768px) {
  .content-container {
    background: #1f2937;
    color: white;
  }
  
  .form-control {
    background: #374151;
    border-color: #4b5563;
    color: white;
    
    &::placeholder {
      color: #9ca3af;
    }
  }
  
  .mobile-progress-simple {
    background: rgba(31, 41, 55, 0.95);
    color: white;
  }
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  text-align: center;
  color: white;
}

.spinner-ring {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.success-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  animation: fadeIn 0.3s ease-out;
}

.success-modal {
  background: white;
  border-radius: 20px;
  padding: 3rem;
  text-align: center;
  max-width: 500px;
  margin: 2rem;
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

// Automotive Success Animation
.success-animation {
  position: relative;
  margin-bottom: 2rem;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.celebration-car {
  font-size: 4rem;
  animation: celebrationBounce 2s ease-in-out infinite;
  z-index: 2;
}

.celebration-tools {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 1;
  
  span {
    font-size: 2rem;
    animation: toolSpin 3s ease-in-out infinite;
    opacity: 0.7;
    
    &.tool-1 {
      animation-delay: 0s;
    }
    
    &.tool-2 {
      animation-delay: 0.5s;
    }
    
    &.tool-3 {
      animation-delay: 1s;
    }
  }
}

.checkmark-circle {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: checkmarkPop 1s ease-out;
  z-index: 3;
}

.success-features {
  display: flex;
  justify-content: space-around;
  margin: 2rem 0;
  padding: 2rem;
  background: #f8fafc;
  border-radius: 16px;
  gap: 1rem;
  
  .feature-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    text-align: center;
    
    i {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }
    
    span {
      font-size: 0.9rem;
      font-weight: 600;
      color: #374151;
    }
  }
}

.checkmark {
  color: white;
  font-size: 2rem;
  font-weight: bold;
}

.checkmark::before {
  content: '✓';
}

.success-title {
  color: #2d3748;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
}

.success-message {
  color: #4a5568;
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 0 0 2rem 0;
}

.success-details {
  background: #f7fafc;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .workshop-code {
    font-family: 'Monaco', 'Menlo', monospace;
    background: #e2e8f0;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-weight: 600;
    color: #2d3748;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

// Automotive Success Animations
@keyframes celebrationBounce {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-20px) scale(1.1); }
}

@keyframes toolSpin {
  0%, 100% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(90deg) scale(1.2); }
  50% { transform: rotate(180deg) scale(0.8); }
  75% { transform: rotate(270deg) scale(1.1); }
}

@keyframes checkmarkPop {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

// Slide transitions for step changes
.slide-enter-active,
.slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// CSS Custom Properties for theming
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --success-gradient: linear-gradient(135deg, #00d4aa 0%, #00b4db 100%);
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
}
</style>