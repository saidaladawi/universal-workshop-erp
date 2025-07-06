<template>
  <div class="mobile-enhancements">
    <!-- Mobile Navigation Hints -->
    <div v-if="showHints" class="mobile-hints">
      <div class="hint-item" v-if="currentStep < totalSteps - 1">
        <span class="hint-icon">👆</span>
        <span class="hint-text">{{ $t('Tap Continue to proceed') }}</span>
      </div>
      <div class="hint-item" v-if="currentStep > 0">
        <span class="hint-icon">👈</span>
        <span class="hint-text">{{ $t('Swipe right or tap Previous') }}</span>
      </div>
    </div>

    <!-- Mobile Progress Indicator -->
    <div class="mobile-progress-simple">
      <div class="progress-dots">
        <div 
          v-for="(step, index) in totalSteps" 
          :key="index"
          class="progress-dot"
          :class="{ 
            'completed': index < currentStep,
            'current': index === currentStep,
            'upcoming': index > currentStep
          }"
          @click="$emit('navigate', index)"
        ></div>
      </div>
      <div class="progress-text">
        {{ $t('Step {current} of {total}', { current: currentStep + 1, total: totalSteps }) }}
      </div>
    </div>

    <!-- Touch Feedback Overlay -->
    <div v-if="showTouchFeedback" class="touch-feedback" :style="touchFeedbackStyle">
      <div class="ripple-effect"></div>
    </div>

    <!-- Mobile Keyboard Helper -->
    <div v-if="keyboardVisible" class="keyboard-helper">
      <div class="keyboard-toolbar">
        <button @click="focusPrevious" class="keyboard-nav-btn">
          <span>↑</span>
          <span class="btn-label">{{ $t('Previous') }}</span>
        </button>
        <button @click="focusNext" class="keyboard-nav-btn">
          <span>↓</span>
          <span class="btn-label">{{ $t('Next') }}</span>
        </button>
        <button @click="hideKeyboard" class="keyboard-nav-btn done-btn">
          <span>✓</span>
          <span class="btn-label">{{ $t('Done') }}</span>
        </button>
      </div>
    </div>

    <!-- Mobile Loading Overlay -->
    <div v-if="isLoading" class="mobile-loading-overlay">
      <div class="loading-content">
        <div class="loading-animation">
          <div class="loading-car">🚗</div>
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <p class="loading-message">{{ loadingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  currentStep: number
  totalSteps: number
  isLoading?: boolean
  loadingMessage?: string
  showHints?: boolean
}>()

const emit = defineEmits(['navigate'])

// State
const keyboardVisible = ref(false)
const showTouchFeedback = ref(false)
const touchFeedbackStyle = ref({})
const currentFocusedInput = ref<HTMLElement | null>(null)

// Computed
const isMobile = computed(() => {
  return window.innerWidth <= 768
})

// Methods
const detectKeyboard = () => {
  if (!isMobile.value) return
  
  const initialHeight = window.innerHeight
  
  const handleResize = () => {
    const currentHeight = window.innerHeight
    const heightDifference = initialHeight - currentHeight
    
    // If height decreased by more than 150px, keyboard is likely visible
    keyboardVisible.value = heightDifference > 150
  }
  
  window.addEventListener('resize', handleResize)
  
  return () => {
    window.removeEventListener('resize', handleResize)
  }
}

const setupTouchFeedback = () => {
  if (!isMobile.value) return
  
  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0]
    showTouchFeedback.value = true
    touchFeedbackStyle.value = {
      left: touch.clientX + 'px',
      top: touch.clientY + 'px'
    }
    
    setTimeout(() => {
      showTouchFeedback.value = false
    }, 300)
  }
  
  document.addEventListener('touchstart', handleTouchStart, { passive: true })
  
  return () => {
    document.removeEventListener('touchstart', handleTouchStart)
  }
}

const focusNext = () => {
  if (!currentFocusedInput.value) return
  
  const inputs = Array.from(document.querySelectorAll('input, select, textarea')) as HTMLElement[]
  const currentIndex = inputs.indexOf(currentFocusedInput.value)
  
  if (currentIndex < inputs.length - 1) {
    const nextInput = inputs[currentIndex + 1]
    nextInput.focus()
    currentFocusedInput.value = nextInput
  }
}

const focusPrevious = () => {
  if (!currentFocusedInput.value) return
  
  const inputs = Array.from(document.querySelectorAll('input, select, textarea')) as HTMLElement[]
  const currentIndex = inputs.indexOf(currentFocusedInput.value)
  
  if (currentIndex > 0) {
    const prevInput = inputs[currentIndex - 1]
    prevInput.focus()
    currentFocusedInput.value = prevInput
  }
}

const hideKeyboard = () => {
  if (currentFocusedInput.value) {
    currentFocusedInput.value.blur()
    currentFocusedInput.value = null
  }
  keyboardVisible.value = false
}

const setupInputTracking = () => {
  const handleFocus = (e: Event) => {
    const target = e.target as HTMLElement
    if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
      currentFocusedInput.value = target
    }
  }
  
  const handleBlur = () => {
    setTimeout(() => {
      if (!document.activeElement || 
          !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        currentFocusedInput.value = null
      }
    }, 100)
  }
  
  document.addEventListener('focus', handleFocus, true)
  document.addEventListener('blur', handleBlur, true)
  
  return () => {
    document.removeEventListener('focus', handleFocus, true)
    document.removeEventListener('blur', handleBlur, true)
  }
}

// Lifecycle
let cleanupFunctions: (() => void)[] = []

onMounted(() => {
  if (isMobile.value) {
    cleanupFunctions.push(
      detectKeyboard(),
      setupTouchFeedback(),
      setupInputTracking()
    )
  }
})

onUnmounted(() => {
  cleanupFunctions.forEach(cleanup => cleanup && cleanup())
})
</script>

<style scoped lang="scss">
.mobile-enhancements {
  position: relative;
  z-index: 1000;
}

.mobile-hints {
  position: fixed;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 1001;
  
  @media (min-width: 769px) {
    display: none;
  }
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  backdrop-filter: blur(10px);
  animation: hintPulse 2s ease-in-out infinite;
  
  .hint-icon {
    font-size: 1rem;
  }
  
  .hint-text {
    white-space: nowrap;
  }
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.mobile-progress-simple {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 0.75rem 1rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1001;
  
  @media (min-width: 769px) {
    display: none;
  }
}

.progress-dots {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
  transition: all 0.3s ease;
  cursor: pointer;
  
  &.completed {
    background: #10b981;
    transform: scale(1.2);
  }
  
  &.current {
    background: #667eea;
    transform: scale(1.4);
  }
  
  &.upcoming {
    background: #cbd5e0;
  }
}

.progress-text {
  font-size: 0.75rem;
  color: #6b7280;
  text-align: center;
  font-weight: 500;
}

.touch-feedback {
  position: fixed;
  width: 40px;
  height: 40px;
  pointer-events: none;
  z-index: 9999;
  transform: translate(-50%, -50%);
}

.ripple-effect {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.3);
  animation: ripple 0.3s ease-out;
}

@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

.keyboard-helper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1002;
  
  @media (min-width: 769px) {
    display: none;
  }
}

.keyboard-toolbar {
  display: flex;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  padding: 0.5rem;
  gap: 0.5rem;
}

.keyboard-nav-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
  
  span:first-child {
    font-size: 1.2rem;
  }
  
  .btn-label {
    font-size: 0.7rem;
    color: #6b7280;
    font-weight: 500;
  }
  
  &:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }
  
  &.done-btn {
    background: #667eea;
    color: white;
    border-color: #667eea;
    
    .btn-label {
      color: white;
    }
    
    &:hover {
      background: #5a67d8;
    }
  }
}

.mobile-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  
  @media (min-width: 769px) {
    display: none;
  }
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-animation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.loading-car {
  font-size: 2rem;
  animation: carBounce 1s ease-in-out infinite;
}

@keyframes carBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.loading-dots {
  display: flex;
  gap: 0.25rem;
  
  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: white;
    animation: dotPulse 1.4s ease-in-out infinite both;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes dotPulse {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.loading-message {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}
</style>