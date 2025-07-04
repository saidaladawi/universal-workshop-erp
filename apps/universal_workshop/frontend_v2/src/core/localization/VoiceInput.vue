<!--
  Arabic Voice Input Component - Universal Workshop Frontend V2

  Advanced voice input system supporting Arabic dialects with
  real-time transcription and intelligent command processing.
-->
<template>
  <div class="arabic-voice-input" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Voice Control Interface -->
    <div class="voice-controls">
      <Button
        :variant="isRecording ? 'danger' : 'primary'"
        :disabled="!speechSupported || isProcessing"
        @click="toggleRecording"
        class="voice-button"
        size="lg"
      >
        <Icon
          :name="isRecording ? 'mic-off' : 'mic'"
          :class="{ 'animate-pulse': isRecording }"
        />
        <span class="voice-button-text">
          {{ getButtonText() }}
        </span>
      </Button>

      <!-- Language Toggle -->
      <div class="language-controls">
        <Button
          v-for="lang in supportedLanguages"
          :key="lang.code"
          :variant="selectedLanguage === lang.code ? 'primary' : 'outline'"
          size="sm"
          @click="setLanguage(lang.code)"
        >
          {{ lang.label }}
        </Button>
      </div>

      <!-- Dialect Selection -->
      <div class="dialect-controls" v-if="selectedLanguage === 'ar'">
        <Select
          v-model="selectedDialect"
          :options="arabicDialects"
          :placeholder="preferArabic ? 'اختر اللهجة' : 'Select Dialect'"
          size="sm"
        />
      </div>
    </div>

    <!-- Recording Feedback -->
    <div class="voice-feedback" v-if="isRecording">
      <div class="recording-indicator">
        <div class="pulse-animation">
          <div class="pulse-dot"></div>
          <div class="pulse-ring"></div>
        </div>
        <span class="recording-text">
          {{ preferArabic ? 'جاري الاستماع...' : 'Listening...' }}
        </span>
      </div>

      <!-- Live Transcript -->
      <div class="live-transcript" v-if="liveTranscript">
        <div class="transcript-header">
          {{ preferArabic ? 'النص المباشر:' : 'Live Transcript:' }}
        </div>
        <div class="transcript-text" :class="{ 'arabic-text': isArabicText(liveTranscript) }">
          {{ liveTranscript }}
        </div>
        <div class="confidence-indicator">
          <div class="confidence-bar">
            <div
              class="confidence-fill"
              :style="{ width: `${liveConfidence * 100}%` }"
            ></div>
          </div>
          <span class="confidence-text">
            {{ Math.round(liveConfidence * 100) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Processing State -->
    <div class="processing-state" v-if="isProcessing">
      <Icon name="loading" spin size="lg" />
      <span>{{ preferArabic ? 'جاري المعالجة...' : 'Processing...' }}</span>
    </div>

    <!-- Results Display -->
    <div class="voice-results" v-if="voiceResults.length > 0">
      <div class="results-header">
        <h3>{{ preferArabic ? 'نتائج التعرف على الصوت' : 'Voice Recognition Results' }}</h3>
        <Button
          variant="outline"
          size="sm"
          @click="clearResults"
        >
          {{ preferArabic ? 'مسح' : 'Clear' }}
        </Button>
      </div>

      <div class="results-list">
        <div
          v-for="(result, index) in voiceResults"
          :key="result.id"
          class="result-item"
          :class="{ 'selected': selectedResult === index }"
          @click="selectResult(index)"
        >
          <div class="result-header">
            <div class="result-confidence">
              <Icon name="volume-2" />
              <span>{{ Math.round(result.confidence * 100) }}%</span>
            </div>
            <div class="result-language">
              {{ getLanguageLabel(result.language) }}
            </div>
            <div class="result-timestamp">
              {{ formatTime(result.timestamp) }}
            </div>
          </div>

          <div class="result-text" :class="{ 'arabic-text': result.language === 'ar' }">
            {{ result.text }}
          </div>

          <!-- Commands Detection -->
          <div class="detected-commands" v-if="result.detectedCommands.length > 0">
            <div class="commands-label">
              {{ preferArabic ? 'الأوامر المكتشفة:' : 'Detected Commands:' }}
            </div>
            <div class="commands-list">
              <Badge
                v-for="command in result.detectedCommands"
                :key="command.type"
                :content="getCommandText(command)"
                variant="primary"
                size="sm"
              />
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="result-actions">
            <Button
              variant="outline"
              size="sm"
              @click="copyToClipboard(result.text)"
            >
              <Icon name="copy" />
              {{ preferArabic ? 'نسخ' : 'Copy' }}
            </Button>

            <Button
              variant="outline"
              size="sm"
              @click="insertText(result.text)"
            >
              <Icon name="edit" />
              {{ preferArabic ? 'إدراج' : 'Insert' }}
            </Button>

            <Button
              v-if="result.detectedCommands.length > 0"
              variant="primary"
              size="sm"
              @click="executeCommands(result.detectedCommands)"
            >
              <Icon name="play" />
              {{ preferArabic ? 'تنفيذ' : 'Execute' }}
            </Button>

            <Button
              variant="danger"
              size="sm"
              @click="removeResult(index)"
            >
              <Icon name="trash" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Voice Commands Help -->
    <div class="voice-commands-help" v-if="showHelp">
      <div class="help-header">
        <h4>{{ preferArabic ? 'الأوامر الصوتية المتاحة' : 'Available Voice Commands' }}</h4>
        <Button variant="ghost" size="sm" @click="showHelp = false">
          <Icon name="x" />
        </Button>
      </div>

      <div class="commands-categories">
        <div
          v-for="category in voiceCommands"
          :key="category.name"
          class="command-category"
        >
          <h5>{{ preferArabic ? category.nameAr : category.name }}</h5>
          <div class="command-list">
            <div
              v-for="command in category.commands"
              :key="command.trigger"
              class="command-item"
            >
              <span class="command-trigger">
                "{{ preferArabic ? command.triggerAr : command.trigger }}"
              </span>
              <span class="command-description">
                {{ preferArabic ? command.descriptionAr : command.description }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div class="voice-error" v-if="error">
      <Alert
        type="error"
        :title="preferArabic ? 'خطأ في التعرف على الصوت' : 'Voice Recognition Error'"
        :message="error"
        :dismissible="true"
        @dismiss="error = null"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useLocalizationStore } from '@/stores/localization'
import { useNotificationStore } from '@/stores/notification'

// Components
import { Button, Icon, Select, Badge, Alert } from '@/components/ui'

// Types
interface VoiceResult {
  id: string
  text: string
  confidence: number
  language: 'ar' | 'en'
  dialect?: string
  timestamp: Date
  detectedCommands: VoiceCommand[]
  alternatives?: string[]
}

interface VoiceCommand {
  type: string
  action: string
  parameters?: { [key: string]: any }
  confidence: number
}

interface ArabicVoiceInputProps {
  placeholder?: string
  autoStart?: boolean
  detectCommands?: boolean
  supportedLanguages?: string[]
  onResult?: (result: VoiceResult) => void
  onCommand?: (command: VoiceCommand) => void
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

// Props
const props = withDefaults(defineProps<ArabicVoiceInputProps>(), {
  placeholder: '',
  autoStart: false,
  detectCommands: true,
  supportedLanguages: () => ['ar', 'en']
})

// Emits
const emit = defineEmits<{
  'result': [result: VoiceResult]
  'command': [command: VoiceCommand]
  'error': [error: string]
}>()

// Stores
const localizationStore = useLocalizationStore()
const notificationStore = useNotificationStore()

// Reactive state
const isRecording = ref(false)
const isProcessing = ref(false)
const speechSupported = ref(false)
const selectedLanguage = ref('ar')
const selectedDialect = ref('gulf')
const liveTranscript = ref('')
const liveConfidence = ref(0)
const voiceResults = ref<VoiceResult[]>([])
const selectedResult = ref(-1)
const showHelp = ref(false)
const error = ref<string | null>(null)

// Speech Recognition
let recognition: SpeechRecognition | null = null
let recognitionTimeout: number | null = null

// Computed
const { preferArabic, isRTL } = localizationStore

const supportedLanguages = computed(() => [
  { code: 'ar', label: 'العربية', labelEn: 'Arabic' },
  { code: 'en', label: 'English', labelEn: 'English' }
])

const arabicDialects = computed(() => [
  { value: 'gulf', label: 'خليجي', labelEn: 'Gulf' },
  { value: 'levantine', label: 'شامي', labelEn: 'Levantine' },
  { value: 'egyptian', label: 'مصري', labelEn: 'Egyptian' },
  { value: 'maghrebi', label: 'مغربي', labelEn: 'Maghrebi' },
  { value: 'standard', label: 'فصحى', labelEn: 'Modern Standard' }
])

const voiceCommands = computed(() => [
  {
    name: 'Service Operations',
    nameAr: 'عمليات الخدمة',
    commands: [
      {
        trigger: 'create new service order',
        triggerAr: 'إنشاء طلب خدمة جديد',
        description: 'Creates a new service order',
        descriptionAr: 'ينشئ طلب خدمة جديد',
        action: 'create_service_order'
      },
      {
        trigger: 'start work on task',
        triggerAr: 'بدء العمل على المهمة',
        description: 'Starts work on selected task',
        descriptionAr: 'يبدأ العمل على المهمة المحددة',
        action: 'start_task'
      },
      {
        trigger: 'complete service',
        triggerAr: 'إكمال الخدمة',
        description: 'Marks service as completed',
        descriptionAr: 'يضع علامة على الخدمة كمكتملة',
        action: 'complete_service'
      }
    ]
  },
  {
    name: 'Inventory Management',
    nameAr: 'إدارة المخزون',
    commands: [
      {
        trigger: 'check parts availability',
        triggerAr: 'تحقق من توفر القطع',
        description: 'Checks parts in inventory',
        descriptionAr: 'يتحقق من القطع في المخزون',
        action: 'check_inventory'
      },
      {
        trigger: 'order parts',
        triggerAr: 'طلب قطع',
        description: 'Creates parts order',
        descriptionAr: 'ينشئ طلب قطع',
        action: 'order_parts'
      }
    ]
  },
  {
    name: 'Navigation',
    nameAr: 'التنقل',
    commands: [
      {
        trigger: 'go to dashboard',
        triggerAr: 'اذهب إلى لوحة التحكم',
        description: 'Navigate to dashboard',
        descriptionAr: 'انتقل إلى لوحة التحكم',
        action: 'navigate_dashboard'
      },
      {
        trigger: 'open customer portal',
        triggerAr: 'افتح بوابة العملاء',
        description: 'Opens customer portal',
        descriptionAr: 'يفتح بوابة العملاء',
        action: 'open_customer_portal'
      }
    ]
  }
])

// Methods
const initializeSpeechRecognition = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    speechSupported.value = false
    error.value = preferArabic ? 'التعرف على الصوت غير مدعوم في هذا المتصفح' : 'Speech recognition not supported'
    return
  }

  speechSupported.value = true
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

  recognition = new SpeechRecognition()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.maxAlternatives = 3

  recognition.onstart = () => {
    console.log('🎤 Voice recognition started')
    error.value = null
  }

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    handleSpeechResult(event)
  }

  recognition.onerror = (event: any) => {
    console.error('Speech recognition error:', event.error)
    handleSpeechError(event.error)
  }

  recognition.onend = () => {
    console.log('🛑 Voice recognition ended')
    if (isRecording.value) {
      // Restart if we're still supposed to be recording
      startRecognition()
    }
  }
}

const startRecognition = () => {
  if (!recognition || !speechSupported.value) return

  try {
    // Set language based on selection
    const langCode = selectedLanguage.value === 'ar'
      ? getArabicLanguageCode()
      : 'en-US'

    recognition.lang = langCode
    recognition.start()

    // Set timeout for maximum recording time
    recognitionTimeout = window.setTimeout(() => {
      stopRecording()
    }, 60000) // 1 minute max

  } catch (error) {
    console.error('Failed to start recognition:', error)
    handleSpeechError('start_failed')
  }
}

const stopRecognition = () => {
  if (recognition) {
    recognition.stop()
  }

  if (recognitionTimeout) {
    clearTimeout(recognitionTimeout)
    recognitionTimeout = null
  }
}

const getArabicLanguageCode = (): string => {
  // Map Arabic dialects to language codes
  const dialectCodes: { [key: string]: string } = {
    'gulf': 'ar-SA', // Saudi Arabia for Gulf dialect
    'levantine': 'ar-LB', // Lebanon for Levantine
    'egyptian': 'ar-EG', // Egypt
    'maghrebi': 'ar-MA', // Morocco for Maghrebi
    'standard': 'ar-SA' // Default to Saudi for MSA
  }

  return dialectCodes[selectedDialect.value] || 'ar-SA'
}

const handleSpeechResult = (event: SpeechRecognitionEvent) => {
  let interimTranscript = ''
  let finalTranscript = ''
  let confidence = 0

  for (let i = event.resultIndex; i < event.results.length; i++) {
    const result = event.results[i]
    const transcript = result[0].transcript
    confidence = result[0].confidence

    if (result.isFinal) {
      finalTranscript += transcript
    } else {
      interimTranscript += transcript
    }
  }

  // Update live transcript
  liveTranscript.value = finalTranscript + interimTranscript
  liveConfidence.value = confidence

  // Process final transcript
  if (finalTranscript) {
    processFinalTranscript(finalTranscript, confidence)
  }
}

const processFinalTranscript = (text: string, confidence: number) => {
  const processedText = cleanTranscript(text)
  const language = detectLanguage(processedText)
  const detectedCommands = props.detectCommands ? detectVoiceCommands(processedText) : []

  const result: VoiceResult = {
    id: generateId(),
    text: processedText,
    confidence,
    language,
    dialect: language === 'ar' ? selectedDialect.value : undefined,
    timestamp: new Date(),
    detectedCommands
  }

  // Add to results
  voiceResults.value.unshift(result)

  // Limit results to 10 items
  if (voiceResults.value.length > 10) {
    voiceResults.value = voiceResults.value.slice(0, 10)
  }

  // Emit events
  emit('result', result)
  if (props.onResult) {
    props.onResult(result)
  }

  // Execute commands if any
  if (detectedCommands.length > 0) {
    executeCommands(detectedCommands)
  }

  // Clear live transcript
  liveTranscript.value = ''
  liveConfidence.value = 0
}

const cleanTranscript = (text: string): string => {
  return text
    .trim()
    .replace(/\s+/g, ' ') // Multiple spaces to single space
    .replace(/^\w/, c => c.toUpperCase()) // Capitalize first letter
}

const detectLanguage = (text: string): 'ar' | 'en' => {
  const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length
  const totalChars = text.length

  return arabicChars / totalChars > 0.3 ? 'ar' : 'en'
}

const detectVoiceCommands = (text: string): VoiceCommand[] => {
  const commands: VoiceCommand[] = []
  const lowerText = text.toLowerCase()

  for (const category of voiceCommands.value) {
    for (const command of category.commands) {
      const triggers = [command.trigger.toLowerCase()]
      if (command.triggerAr) {
        triggers.push(command.triggerAr.toLowerCase())
      }

      for (const trigger of triggers) {
        if (lowerText.includes(trigger)) {
          commands.push({
            type: command.action,
            action: command.action,
            confidence: 0.8,
            parameters: extractCommandParameters(text, trigger)
          })
          break
        }
      }
    }
  }

  return commands
}

const extractCommandParameters = (text: string, trigger: string): { [key: string]: any } => {
  // Extract parameters from text based on command type
  const parameters: { [key: string]: any } = {}

  // Simple parameter extraction - can be enhanced
  const numbers = text.match(/\d+/g)
  if (numbers) {
    parameters.numbers = numbers
  }

  return parameters
}

const handleSpeechError = (error: string) => {
  let errorMessage = ''

  switch (error) {
    case 'no-speech':
      errorMessage = preferArabic ? 'لم يتم اكتشاف صوت' : 'No speech detected'
      break
    case 'audio-capture':
      errorMessage = preferArabic ? 'خطأ في التقاط الصوت' : 'Audio capture error'
      break
    case 'not-allowed':
      errorMessage = preferArabic ? 'غير مسموح بالوصول للميكروفون' : 'Microphone access denied'
      break
    case 'network':
      errorMessage = preferArabic ? 'خطأ في الشبكة' : 'Network error'
      break
    default:
      errorMessage = preferArabic ? 'خطأ في التعرف على الصوت' : 'Speech recognition error'
  }

  this.error = errorMessage
  emit('error', errorMessage)
  isRecording.value = false
  isProcessing.value = false
}

const toggleRecording = async () => {
  if (isRecording.value) {
    await stopRecording()
  } else {
    await startRecording()
  }
}

const startRecording = async () => {
  if (!speechSupported.value) return

  try {
    // Request microphone permission
    await navigator.mediaDevices.getUserMedia({ audio: true })

    isRecording.value = true
    isProcessing.value = false
    error.value = null

    startRecognition()

    notificationStore.showSuccess(
      preferArabic ? 'بدأ التسجيل' : 'Recording started'
    )
  } catch (err) {
    error.value = preferArabic ? 'فشل في الوصول للميكروفون' : 'Failed to access microphone'
  }
}

const stopRecording = async () => {
  isRecording.value = false
  isProcessing.value = true

  stopRecognition()

  // Processing delay simulation
  setTimeout(() => {
    isProcessing.value = false
  }, 1000)

  notificationStore.showSuccess(
    preferArabic ? 'توقف التسجيل' : 'Recording stopped'
  )
}

const setLanguage = (langCode: string) => {
  selectedLanguage.value = langCode

  if (isRecording.value) {
    // Restart recording with new language
    stopRecording()
    setTimeout(() => startRecording(), 500)
  }
}

const selectResult = (index: number) => {
  selectedResult.value = selectedResult.value === index ? -1 : index
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    notificationStore.showSuccess(
      preferArabic ? 'تم النسخ' : 'Copied to clipboard'
    )
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const insertText = (text: string) => {
  // Emit insert event for parent component to handle
  emit('result', {
    id: generateId(),
    text,
    confidence: 1,
    language: detectLanguage(text),
    timestamp: new Date(),
    detectedCommands: []
  })
}

const executeCommands = (commands: VoiceCommand[]) => {
  for (const command of commands) {
    emit('command', command)
    if (props.onCommand) {
      props.onCommand(command)
    }
  }
}

const removeResult = (index: number) => {
  voiceResults.value.splice(index, 1)
  if (selectedResult.value === index) {
    selectedResult.value = -1
  } else if (selectedResult.value > index) {
    selectedResult.value--
  }
}

const clearResults = () => {
  voiceResults.value = []
  selectedResult.value = -1
}

const getButtonText = (): string => {
  if (isProcessing.value) {
    return preferArabic ? 'جاري المعالجة...' : 'Processing...'
  }

  if (isRecording.value) {
    return preferArabic ? 'إيقاف التسجيل' : 'Stop Recording'
  }

  return preferArabic ? 'بدء التسجيل الصوتي' : 'Start Voice Input'
}

const getLanguageLabel = (langCode: string): string => {
  const lang = supportedLanguages.value.find(l => l.code === langCode)
  return preferArabic ? lang?.label || langCode : lang?.labelEn || langCode
}

const getCommandText = (command: VoiceCommand): string => {
  const commandDef = voiceCommands.value
    .flatMap(cat => cat.commands)
    .find(cmd => cmd.action === command.action)

  if (commandDef) {
    return preferArabic ? commandDef.triggerAr : commandDef.trigger
  }

  return command.action
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString(preferArabic ? 'ar-SA' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isArabicText = (text: string): boolean => {
  return /[\u0600-\u06FF]/.test(text)
}

const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9)
}

// Lifecycle
onMounted(() => {
  initializeSpeechRecognition()

  if (props.autoStart && speechSupported.value) {
    setTimeout(() => startRecording(), 1000)
  }
})

onUnmounted(() => {
  if (isRecording.value) {
    stopRecording()
  }

  if (recognitionTimeout) {
    clearTimeout(recognitionTimeout)
  }
})

// Watchers
watch(selectedDialect, () => {
  if (isRecording.value && selectedLanguage.value === 'ar') {
    // Restart with new dialect
    stopRecording()
    setTimeout(() => startRecording(), 500)
  }
})
</script>

<style scoped>
.arabic-voice-input {
  @apply max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.arabic-voice-input[dir="rtl"] {
  text-align: right;
}

/* Voice Controls */
.voice-controls {
  @apply mb-6 text-center;
}

.voice-button {
  @apply min-w-48 h-16 text-lg font-semibold;
}

.voice-button-text {
  @apply ml-3;
}

.voice-button[dir="rtl"] .voice-button-text {
  @apply mr-3 ml-0;
}

.language-controls {
  @apply flex justify-center gap-2 mt-4;
}

.dialect-controls {
  @apply mt-4 flex justify-center;
}

/* Recording Feedback */
.voice-feedback {
  @apply mb-6;
}

.recording-indicator {
  @apply flex items-center justify-center gap-4 p-4 bg-red-50 rounded-lg;
}

.pulse-animation {
  @apply relative;
}

.pulse-dot {
  @apply w-4 h-4 bg-red-500 rounded-full;
}

.pulse-ring {
  @apply absolute inset-0 w-4 h-4 bg-red-500 rounded-full animate-ping;
}

.recording-text {
  @apply text-red-700 font-medium;
}

/* Live Transcript */
.live-transcript {
  @apply mt-4 p-4 bg-blue-50 rounded-lg;
}

.transcript-header {
  @apply text-sm font-medium text-blue-700 mb-2;
}

.transcript-text {
  @apply text-lg text-blue-900 mb-3;
}

.transcript-text.arabic-text {
  @apply text-right leading-loose;
  font-family: 'Noto Sans Arabic', sans-serif;
}

.confidence-indicator {
  @apply flex items-center gap-2;
}

.confidence-bar {
  @apply flex-1 h-2 bg-blue-200 rounded-full overflow-hidden;
}

.confidence-fill {
  @apply h-full bg-blue-500 transition-all duration-300;
}

.confidence-text {
  @apply text-sm font-medium text-blue-700;
}

/* Processing State */
.processing-state {
  @apply flex items-center justify-center gap-3 p-4 bg-yellow-50 rounded-lg text-yellow-700;
}

/* Results Display */
.voice-results {
  @apply mb-6;
}

.results-header {
  @apply flex justify-between items-center mb-4;
}

.results-header h3 {
  @apply text-lg font-semibold text-gray-900;
}

.results-list {
  @apply space-y-3;
}

.result-item {
  @apply p-4 border border-gray-200 rounded-lg cursor-pointer transition-all hover:bg-gray-50;
}

.result-item.selected {
  @apply border-blue-300 bg-blue-50;
}

.result-header {
  @apply flex justify-between items-center mb-2 text-sm text-gray-600;
}

.result-confidence {
  @apply flex items-center gap-1;
}

.result-text {
  @apply text-lg text-gray-900 mb-3;
}

.result-text.arabic-text {
  @apply text-right leading-loose;
  font-family: 'Noto Sans Arabic', sans-serif;
}

/* Commands */
.detected-commands {
  @apply mb-3;
}

.commands-label {
  @apply text-sm font-medium text-gray-700 mb-2;
}

.commands-list {
  @apply flex flex-wrap gap-2;
}

.result-actions {
  @apply flex gap-2;
}

/* Voice Commands Help */
.voice-commands-help {
  @apply mb-6 p-4 bg-gray-50 rounded-lg;
}

.help-header {
  @apply flex justify-between items-center mb-4;
}

.help-header h4 {
  @apply text-lg font-semibold text-gray-900;
}

.commands-categories {
  @apply space-y-4;
}

.command-category h5 {
  @apply font-medium text-gray-800 mb-2;
}

.command-list {
  @apply space-y-2;
}

.command-item {
  @apply flex justify-between items-center p-2 bg-white rounded border;
}

.command-trigger {
  @apply font-mono text-sm text-blue-600;
}

.command-description {
  @apply text-sm text-gray-600;
}

/* Error Display */
.voice-error {
  @apply mt-4;
}

/* Animations */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s infinite;
}

/* Responsive */
@media (max-width: 768px) {
  .arabic-voice-input {
    @apply p-4;
  }

  .voice-button {
    @apply min-w-full h-14 text-base;
  }

  .language-controls {
    @apply flex-col gap-2;
  }

  .result-header {
    @apply flex-col gap-1 items-start;
  }

  .result-actions {
    @apply flex-wrap;
  }

  .command-item {
    @apply flex-col items-start gap-1;
  }
}
</style>
