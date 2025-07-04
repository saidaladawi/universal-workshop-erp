<!--
  RealTimeChatInterface Component - Universal Workshop Frontend V2
  Advanced real-time chat system with voice messages, image sharing,
  automatic translation, and offline message queuing.
-->
<template>
  <div :class="chatClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Chat Header -->
    <div class="chat-header">
      <div class="participant-info">
        <Button
          variant="ghost"
          size="sm"
          @click="$emit('close')"
          class="back-button"
        >
          <Icon :name="isRTL ? 'chevron-right' : 'chevron-left'" />
        </Button>
        
        <div class="avatar-container">
          <img 
            :src="otherParticipant.photoUrl || defaultAvatarUrl" 
            :alt="otherParticipant.name"
            class="participant-avatar"
          >
          <div 
            class="status-indicator" 
            :class="otherParticipant.isOnline ? 'online' : 'offline'"
          ></div>
        </div>
        
        <div class="participant-details">
          <h3>{{ preferArabic ? otherParticipant.nameAr : otherParticipant.name }}</h3>
          <p class="participant-role">
            {{ preferArabic ? otherParticipant.roleAr : otherParticipant.role }}
          </p>
          <div class="online-status">
            {{ otherParticipant.isOnline 
              ? (preferArabic ? 'متصل الآن' : 'Online now')
              : getLastSeenText(otherParticipant.lastSeen)
            }}
          </div>
        </div>
      </div>
      
      <div class="chat-actions">
        <Button
          variant="ghost"
          size="sm"
          @click="initiateVoiceCall"
          :disabled="!otherParticipant.isOnline"
        >
          <Icon name="phone" />
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          @click="initiateVideoCall"
          :disabled="!otherParticipant.isOnline"
        >
          <Icon name="video" />
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          @click="openChatSettings"
        >
          <Icon name="settings" />
        </Button>
      </div>
    </div>

    <!-- Service Context Banner -->
    <div class="service-context" v-if="serviceContext">
      <div class="context-info">
        <Icon name="wrench" />
        <div class="context-details">
          <span class="service-title">
            {{ preferArabic ? serviceContext.titleAr : serviceContext.title }}
          </span>
          <span class="vehicle-info">
            {{ serviceContext.vehicle.make }} {{ serviceContext.vehicle.model }}
            ({{ serviceContext.vehicle.plateNumber }})
          </span>
        </div>
      </div>
      
      <Button
        variant="outline"
        size="sm"
        @click="viewServiceDetails"
      >
        {{ preferArabic ? 'عرض التفاصيل' : 'View Details' }}
      </Button>
    </div>

    <!-- Messages Container -->
    <div class="messages-container" ref="messagesContainer">
      <div class="messages-list">
        <!-- Date Separator -->
        <div
          v-for="(group, date) in groupedMessages"
          :key="date"
          class="message-group"
        >
          <div class="date-separator">
            <span>{{ formatDateSeparator(date) }}</span>
          </div>
          
          <!-- Messages for this date -->
          <TransitionGroup name="message" tag="div">
            <div
              v-for="message in group"
              :key="message.id"
              :class="getMessageClass(message)"
            >
              <!-- System Message -->
              <div v-if="message.type === 'system'" class="system-message">
                <Icon :name="getSystemMessageIcon(message.systemType)" />
                <span>{{ preferArabic ? message.textAr : message.text }}</span>
              </div>

              <!-- Regular Message -->
              <div v-else class="message-bubble">
                <!-- Message Header (for other participant's messages) -->
                <div v-if="!message.isFromMe" class="message-header">
                  <img 
                    :src="message.sender.photoUrl || defaultAvatarUrl" 
                    :alt="message.sender.name"
                    class="sender-avatar"
                  >
                  <span class="sender-name">
                    {{ preferArabic ? message.sender.nameAr : message.sender.name }}
                  </span>
                </div>

                <!-- Message Content -->
                <div class="message-content">
                  <!-- Text Message -->
                  <div v-if="message.type === 'text'" class="text-content">
                    <p :dir="getTextDirection(message.text)">{{ message.text }}</p>
                    
                    <!-- Translation Toggle -->
                    <Button
                      v-if="message.hasTranslation && !message.isFromMe"
                      variant="ghost"
                      size="xs"
                      @click="toggleTranslation(message.id)"
                      class="translation-toggle"
                    >
                      <Icon name="languages" />
                      {{ message.showTranslation 
                        ? (preferArabic ? 'النص الأصلي' : 'Original')
                        : (preferArabic ? 'ترجمة' : 'Translate')
                      }}
                    </Button>
                    
                    <!-- Translated Text -->
                    <div v-if="message.showTranslation" class="translated-text">
                      <p :dir="getTextDirection(message.translatedText)">
                        {{ message.translatedText }}
                      </p>
                      <span class="translation-note">
                        {{ preferArabic ? 'مترجم تلقائياً' : 'Auto-translated' }}
                      </span>
                    </div>
                  </div>

                  <!-- Voice Message -->
                  <div v-else-if="message.type === 'voice'" class="voice-content">
                    <div class="voice-player">
                      <Button
                        :variant="message.isPlaying ? 'primary' : 'outline'"
                        size="sm"
                        @click="toggleVoicePlayback(message.id)"
                      >
                        <Icon :name="message.isPlaying ? 'pause' : 'play'" />
                      </Button>
                      
                      <div class="voice-waveform">
                        <div 
                          v-for="(bar, index) in message.waveform"
                          :key="index"
                          class="waveform-bar"
                          :style="{ height: `${bar * 100}%` }"
                          :class="{ 'active': message.isPlaying && index <= message.playbackPosition }"
                        ></div>
                      </div>
                      
                      <span class="voice-duration">{{ formatDuration(message.duration) }}</span>
                    </div>
                    
                    <!-- Voice Transcription -->
                    <div v-if="message.transcription" class="voice-transcription">
                      <Icon name="type" />
                      <p>{{ message.transcription }}</p>
                    </div>
                  </div>

                  <!-- Image Message -->
                  <div v-else-if="message.type === 'image'" class="image-content">
                    <div class="image-container" @click="openImageViewer(message.imageUrl)">
                      <img 
                        :src="message.thumbnailUrl || message.imageUrl" 
                        :alt="message.caption || 'Shared image'"
                        class="message-image"
                      >
                      <div class="image-overlay">
                        <Icon name="zoom-in" />
                      </div>
                    </div>
                    
                    <p v-if="message.caption" class="image-caption">
                      {{ message.caption }}
                    </p>
                  </div>

                  <!-- File Message -->
                  <div v-else-if="message.type === 'file'" class="file-content">
                    <div class="file-info">
                      <Icon :name="getFileIcon(message.fileType)" />
                      <div class="file-details">
                        <span class="file-name">{{ message.fileName }}</span>
                        <span class="file-size">{{ formatFileSize(message.fileSize) }}</span>
                      </div>
                    </div>
                    
                    <Button
                      variant="primary"
                      size="sm"
                      @click="downloadFile(message.fileUrl, message.fileName)"
                    >
                      <Icon name="download" />
                      {{ preferArabic ? 'تحميل' : 'Download' }}
                    </Button>
                  </div>

                  <!-- Location Message -->
                  <div v-else-if="message.type === 'location'" class="location-content">
                    <div class="location-map" @click="openLocationViewer(message.location)">
                      <img 
                        :src="getStaticMapUrl(message.location)" 
                        alt="Location map"
                        class="map-image"
                      >
                      <div class="location-overlay">
                        <Icon name="map-pin" />
                      </div>
                    </div>
                    
                    <div class="location-details">
                      <p class="location-address">{{ message.location.address }}</p>
                      <Button
                        variant="outline"
                        size="sm"
                        @click="openInMaps(message.location)"
                      >
                        <Icon name="external-link" />
                        {{ preferArabic ? 'فتح في الخرائط' : 'Open in Maps' }}
                      </Button>
                    </div>
                  </div>
                </div>

                <!-- Message Footer -->
                <div class="message-footer">
                  <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
                  
                  <!-- Delivery Status (for sent messages) -->
                  <div v-if="message.isFromMe" class="delivery-status">
                    <Icon 
                      :name="getDeliveryStatusIcon(message.deliveryStatus)" 
                      :class="getDeliveryStatusClass(message.deliveryStatus)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>

      <!-- Typing Indicator -->
      <div v-if="otherParticipantTyping" class="typing-indicator">
        <div class="typing-avatar">
          <img 
            :src="otherParticipant.photoUrl || defaultAvatarUrl" 
            :alt="otherParticipant.name"
          >
        </div>
        <div class="typing-animation">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <span class="typing-text">
          {{ preferArabic ? 'يكتب...' : 'typing...' }}
        </span>
      </div>
    </div>

    <!-- Message Input Area -->
    <div class="input-area">
      <!-- Attachment Preview -->
      <div v-if="attachmentPreview" class="attachment-preview">
        <div class="preview-container">
          <img 
            v-if="attachmentPreview.type === 'image'"
            :src="attachmentPreview.url" 
            alt="Preview"
            class="preview-image"
          >
          <div v-else class="preview-file">
            <Icon :name="getFileIcon(attachmentPreview.type)" />
            <span>{{ attachmentPreview.name }}</span>
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          @click="removeAttachment"
          class="remove-attachment"
        >
          <Icon name="x" />
        </Button>
      </div>

      <!-- Voice Recording Indicator -->
      <div v-if="isRecordingVoice" class="voice-recording">
        <div class="recording-indicator">
          <div class="pulse-dot"></div>
          <span>{{ preferArabic ? 'جاري التسجيل...' : 'Recording...' }}</span>
        </div>
        
        <div class="recording-timer">{{ formatRecordingTime(recordingDuration) }}</div>
        
        <div class="recording-actions">
          <Button
            variant="danger"
            size="sm"
            @click="cancelVoiceRecording"
          >
            <Icon name="x" />
          </Button>
          
          <Button
            variant="primary"
            size="sm"
            @click="stopVoiceRecording"
          >
            <Icon name="check" />
          </Button>
        </div>
      </div>

      <!-- Text Input -->
      <div v-if="!isRecordingVoice" class="text-input-container">
        <div class="input-actions">
          <Button
            variant="ghost"
            size="sm"
            @click="openAttachmentMenu"
            class="attachment-button"
          >
            <Icon name="paperclip" />
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            @click="openCamera"
            class="camera-button"
          >
            <Icon name="camera" />
          </Button>
        </div>
        
        <div class="text-input-wrapper">
          <textarea
            v-model="messageText"
            :placeholder="preferArabic ? 'اكتب رسالة...' : 'Type a message...'"
            :dir="getTextDirection(messageText)"
            class="message-input"
            rows="1"
            @input="handleInput"
            @keydown="handleKeyDown"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
            ref="messageInput"
          ></textarea>
          
          <!-- Emoji Button -->
          <Button
            variant="ghost"
            size="sm"
            @click="toggleEmojiPicker"
            class="emoji-button"
          >
            <Icon name="smile" />
          </Button>
        </div>
        
        <!-- Send/Voice Button -->
        <div class="send-actions">
          <Button
            v-if="messageText.trim() || attachmentPreview"
            variant="primary"
            size="sm"
            @click="sendMessage"
            :disabled="isSending"
            class="send-button"
          >
            <Icon name="send" />
          </Button>
          
          <Button
            v-else
            variant="primary"
            size="sm"
            @mousedown="startVoiceRecording"
            @mouseup="stopVoiceRecording"
            @mouseleave="cancelVoiceRecording"
            @touchstart="startVoiceRecording"
            @touchend="stopVoiceRecording"
            class="voice-button"
          >
            <Icon name="mic" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Emoji Picker -->
    <div v-if="showEmojiPicker" class="emoji-picker">
      <!-- Emoji picker implementation -->
    </div>

    <!-- Attachment Menu -->
    <div v-if="showAttachmentMenu" class="attachment-menu">
      <div class="attachment-options">
        <Button
          v-for="option in attachmentOptions"
          :key="option.id"
          variant="ghost"
          @click="handleAttachmentOption(option.id)"
          class="attachment-option"
        >
          <Icon :name="option.icon" />
          <span>{{ preferArabic ? option.labelAr : option.label }}</span>
        </Button>
      </div>
    </div>

    <!-- Offline Message Queue -->
    <div v-if="queuedMessages.length > 0" class="offline-queue">
      <div class="queue-header">
        <Icon name="wifi-off" />
        <span>
          {{ queuedMessages.length }} 
          {{ preferArabic ? 'رسائل في الانتظار' : 'messages queued' }}
        </span>
      </div>
      
      <Button
        variant="outline"
        size="sm"
        @click="retryQueuedMessages"
        :disabled="isRetrying"
      >
        <Icon name="refresh-cw" :class="{ 'animate-spin': isRetrying }" />
        {{ preferArabic ? 'إعادة المحاولة' : 'Retry' }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'

// Stores
import { useChatStore } from '@/stores/chat'
import { useLocalizationStore } from '@/stores/localization'
import { useConnectivityStore } from '@/stores/connectivity'
import { useNotificationStore } from '@/stores/notification'

// Composables
import { useRealTimeUpdates } from '@/composables/useRealTimeUpdates'
import { useVoiceRecording } from '@/composables/useVoiceRecording'
import { useMobileCamera } from '@/composables/useMobileCamera'
import { useFileUpload } from '@/composables/useFileUpload'
import { useTranslation } from '@/composables/useTranslation'

// Components
import { Button, Icon } from '@/components/ui'

// Types
interface RealTimeChatInterfaceProps {
  chatId: string
  participantId: string
  serviceContext?: ServiceContext
}

interface RealTimeChatInterfaceEmits {
  (e: 'close'): void
  (e: 'voice-call', participantId: string): void
  (e: 'video-call', participantId: string): void
}

// Props & Emits
const props = defineProps<RealTimeChatInterfaceProps>()
const emit = defineEmits<RealTimeChatInterfaceEmits>()

// Stores
const chatStore = useChatStore()
const localizationStore = useLocalizationStore()
const connectivityStore = useConnectivityStore()
const notificationStore = useNotificationStore()

// Store refs
const { messages, otherParticipant, queuedMessages } = storeToRefs(chatStore)
const { preferArabic, isRTL } = storeToRefs(localizationStore)
const { isOnline } = storeToRefs(connectivityStore)

// Composables
const router = useRouter()
const realTimeUpdates = useRealTimeUpdates()
const voiceRecording = useVoiceRecording()
const mobileCamera = useMobileCamera()
const fileUpload = useFileUpload()
const translation = useTranslation()

// Reactive state
const messageText = ref('')
const isSending = ref(false)
const isTyping = ref(false)
const otherParticipantTyping = ref(false)
const showEmojiPicker = ref(false)
const showAttachmentMenu = ref(false)
const attachmentPreview = ref<any>(null)
const isRecordingVoice = ref(false)
const recordingDuration = ref(0)
const isRetrying = ref(false)

// Refs
const messagesContainer = ref<HTMLElement>()
const messageInput = ref<HTMLTextAreaElement>()

// Computed properties
const chatClasses = computed(() => [
  'real-time-chat-interface',
  {
    'rtl': isRTL.value,
    'offline': !isOnline.value
  }
])

const groupedMessages = computed(() => {
  const groups: Record<string, any[]> = {}
  
  messages.value.forEach(message => {
    const date = new Date(message.timestamp).toDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(message)
  })
  
  return groups
})

const attachmentOptions = computed(() => [
  {
    id: 'camera',
    label: 'Camera',
    labelAr: 'كاميرا',
    icon: 'camera'
  },
  {
    id: 'gallery',
    label: 'Photo Gallery',
    labelAr: 'معرض الصور',
    icon: 'image'
  },
  {
    id: 'document',
    label: 'Document',
    labelAr: 'مستند',
    icon: 'file'
  },
  {
    id: 'location',
    label: 'Location',
    labelAr: 'الموقع',
    icon: 'map-pin'
  }
])

const defaultAvatarUrl = '/assets/universal_workshop/images/default-avatar.png'

// Methods
const getMessageClass = (message: any) => ({
  'message-item': true,
  'from-me': message.isFromMe,
  'from-other': !message.isFromMe,
  [`type-${message.type}`]: true
})

const getTextDirection = (text: string) => {
  // Simple Arabic text detection
  const arabicPattern = /[\u0600-\u06FF]/
  return arabicPattern.test(text) ? 'rtl' : 'ltr'
}

const formatDateSeparator = (dateString: string) => {
  const date = new Date(dateString)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  
  if (date.toDateString() === today.toDateString()) {
    return preferArabic.value ? 'اليوم' : 'Today'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return preferArabic.value ? 'أمس' : 'Yesterday'
  } else {
    return date.toLocaleDateString(preferArabic.value ? 'ar-SA' : 'en-US')
  }
}

const formatMessageTime = (timestamp: Date) => {
  return new Date(timestamp).toLocaleTimeString(
    preferArabic.value ? 'ar-SA' : 'en-US',
    { hour: '2-digit', minute: '2-digit' }
  )
}

const getLastSeenText = (lastSeen: Date) => {
  if (!lastSeen) return preferArabic.value ? 'غير متصل' : 'Offline'
  
  const now = new Date()
  const diff = now.getTime() - lastSeen.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) {
    return preferArabic.value ? 'منذ لحظات' : 'Just now'
  } else if (minutes < 60) {
    return preferArabic.value ? `منذ ${minutes} دقيقة` : `${minutes} minutes ago`
  } else {
    const hours = Math.floor(minutes / 60)
    return preferArabic.value ? `منذ ${hours} ساعة` : `${hours} hours ago`
  }
}

const sendMessage = async () => {
  if ((!messageText.value.trim() && !attachmentPreview.value) || isSending.value) {
    return
  }
  
  try {
    isSending.value = true
    
    const messageData = {
      text: messageText.value.trim(),
      type: attachmentPreview.value ? attachmentPreview.value.type : 'text',
      attachment: attachmentPreview.value
    }
    
    await chatStore.sendMessage(props.chatId, messageData)
    
    messageText.value = ''
    attachmentPreview.value = null
    
    // Auto-resize textarea
    if (messageInput.value) {
      messageInput.value.style.height = 'auto'
    }
    
    // Scroll to bottom
    await nextTick()
    scrollToBottom()
    
  } catch (error) {
    console.error('Failed to send message:', error)
    notificationStore.showError(
      preferArabic.value ? 'فشل في إرسال الرسالة' : 'Failed to send message'
    )
  } finally {
    isSending.value = false
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Event handlers
const handleInput = () => {
  // Auto-resize textarea
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = messageInput.value.scrollHeight + 'px'
  }
  
  // Send typing indicator
  if (!isTyping.value) {
    isTyping.value = true
    chatStore.sendTypingIndicator(props.chatId, true)
    
    // Clear typing indicator after 3 seconds
    setTimeout(() => {
      isTyping.value = false
      chatStore.sendTypingIndicator(props.chatId, false)
    }, 3000)
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Voice recording
const startVoiceRecording = async () => {
  try {
    await voiceRecording.startRecording()
    isRecordingVoice.value = true
    recordingDuration.value = 0
    
    // Update recording duration
    const interval = setInterval(() => {
      if (isRecordingVoice.value) {
        recordingDuration.value++
      } else {
        clearInterval(interval)
      }
    }, 1000)
  } catch (error) {
    console.error('Failed to start voice recording:', error)
  }
}

const stopVoiceRecording = async () => {
  try {
    const audioBlob = await voiceRecording.stopRecording()
    isRecordingVoice.value = false
    
    if (audioBlob && recordingDuration.value > 1) {
      await chatStore.sendVoiceMessage(props.chatId, audioBlob, recordingDuration.value)
    }
  } catch (error) {
    console.error('Failed to stop voice recording:', error)
  }
}

const cancelVoiceRecording = () => {
  voiceRecording.cancelRecording()
  isRecordingVoice.value = false
  recordingDuration.value = 0
}

// Lifecycle hooks
onMounted(async () => {
  await chatStore.loadChat(props.chatId)
  
  // Subscribe to real-time updates
  realTimeUpdates.subscribeToChatUpdates(props.chatId)
  
  // Scroll to bottom initially
  await nextTick()
  scrollToBottom()
})

onUnmounted(() => {
  realTimeUpdates.unsubscribeFromChatUpdates(props.chatId)
})

// Watch for new messages to scroll to bottom
watch(messages, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })
</script>

<style scoped>
.real-time-chat-interface {
  @apply flex flex-col h-full bg-gray-50;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.real-time-chat-interface.rtl {
  direction: rtl;
}

/* Chat Header */
.chat-header {
  @apply bg-white border-b border-gray-200 p-4 flex items-center justify-between;
}

.participant-info {
  @apply flex items-center space-x-3;
}

.participant-info.rtl {
  @apply space-x-reverse;
}

.back-button {
  @apply mr-2;
}

.back-button.rtl {
  @apply ml-2 mr-0;
}

.avatar-container {
  @apply relative;
}

.participant-avatar {
  @apply w-12 h-12 rounded-full object-cover;
}

.status-indicator {
  @apply absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white;
}

.status-indicator.online {
  @apply bg-green-500;
}

.status-indicator.offline {
  @apply bg-gray-400;
}

.participant-details h3 {
  @apply font-bold text-gray-900;
}

.participant-role {
  @apply text-sm text-gray-600;
}

.online-status {
  @apply text-xs text-gray-500;
}

.chat-actions {
  @apply flex space-x-2;
}

.chat-actions.rtl {
  @apply space-x-reverse;
}

/* Service Context */
.service-context {
  @apply bg-blue-50 border-b border-blue-200 p-3 flex items-center justify-between;
}

.context-info {
  @apply flex items-center space-x-3;
}

.context-info.rtl {
  @apply space-x-reverse;
}

.context-details {
  @apply flex flex-col;
}

.service-title {
  @apply font-medium text-blue-900;
}

.vehicle-info {
  @apply text-sm text-blue-700;
}

/* Messages Container */
.messages-container {
  @apply flex-1 overflow-y-auto p-4;
}

.date-separator {
  @apply text-center my-4;
}

.date-separator span {
  @apply bg-gray-200 text-gray-600 px-3 py-1 rounded-full text-sm;
}

/* Message Styles */
.message-item {
  @apply mb-4;
}

.message-item.from-me {
  @apply flex justify-end;
}

.message-item.from-other {
  @apply flex justify-start;
}

.system-message {
  @apply flex items-center justify-center space-x-2 text-gray-600 text-sm my-2;
}

.system-message.rtl {
  @apply space-x-reverse;
}

.message-bubble {
  @apply max-w-xs sm:max-w-sm lg:max-w-md;
}

.message-item.from-me .message-bubble {
  @apply bg-blue-500 text-white rounded-2xl rounded-br-sm p-3;
}

.message-item.from-other .message-bubble {
  @apply bg-white border border-gray-200 rounded-2xl rounded-bl-sm p-3;
}

.message-header {
  @apply flex items-center space-x-2 mb-2;
}

.message-header.rtl {
  @apply space-x-reverse;
}

.sender-avatar {
  @apply w-6 h-6 rounded-full object-cover;
}

.sender-name {
  @apply text-sm font-medium text-gray-700;
}

/* Message Content Types */
.text-content p {
  @apply break-words;
}

.translation-toggle {
  @apply mt-2;
}

.translated-text {
  @apply mt-2 pt-2 border-t border-gray-200;
}

.translation-note {
  @apply text-xs text-gray-500 italic;
}

.voice-content {
  @apply space-y-2;
}

.voice-player {
  @apply flex items-center space-x-3;
}

.voice-player.rtl {
  @apply space-x-reverse;
}

.voice-waveform {
  @apply flex items-end space-x-1 h-8;
}

.waveform-bar {
  @apply w-1 bg-gray-300 rounded-full transition-all duration-200;
}

.waveform-bar.active {
  @apply bg-blue-500;
}

.voice-duration {
  @apply text-sm text-gray-600;
}

.voice-transcription {
  @apply flex items-start space-x-2 text-sm text-gray-600;
}

.voice-transcription.rtl {
  @apply space-x-reverse;
}

.image-content .image-container {
  @apply relative cursor-pointer rounded-lg overflow-hidden;
}

.message-image {
  @apply max-w-full h-auto;
}

.image-overlay {
  @apply absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 flex items-center justify-center text-white transition-all duration-200;
}

.image-caption {
  @apply mt-2 text-sm;
}

.file-content {
  @apply space-y-3;
}

.file-info {
  @apply flex items-center space-x-3;
}

.file-info.rtl {
  @apply space-x-reverse;
}

.file-details {
  @apply flex flex-col;
}

.file-name {
  @apply font-medium;
}

.file-size {
  @apply text-sm text-gray-600;
}

.location-content {
  @apply space-y-3;
}

.location-map {
  @apply relative cursor-pointer rounded-lg overflow-hidden;
}

.map-image {
  @apply w-full h-32 object-cover;
}

.location-overlay {
  @apply absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 flex items-center justify-center text-white transition-all duration-200;
}

.location-details {
  @apply space-y-2;
}

.location-address {
  @apply text-sm;
}

/* Message Footer */
.message-footer {
  @apply flex items-center justify-between mt-2 text-xs;
}

.message-item.from-me .message-footer {
  @apply text-blue-200;
}

.message-item.from-other .message-footer {
  @apply text-gray-500;
}

.delivery-status {
  @apply flex items-center space-x-1;
}

.delivery-status.rtl {
  @apply space-x-reverse;
}

/* Typing Indicator */
.typing-indicator {
  @apply flex items-center space-x-3 p-4;
}

.typing-indicator.rtl {
  @apply space-x-reverse;
}

.typing-avatar img {
  @apply w-8 h-8 rounded-full object-cover;
}

.typing-animation {
  @apply flex space-x-1;
}

.typing-dot {
  @apply w-2 h-2 bg-gray-400 rounded-full animate-pulse;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

.typing-text {
  @apply text-sm text-gray-600;
}

/* Input Area */
.input-area {
  @apply bg-white border-t border-gray-200 p-4;
}

.attachment-preview {
  @apply flex items-center justify-between bg-gray-50 rounded-lg p-3 mb-3;
}

.preview-image {
  @apply w-16 h-16 rounded-lg object-cover;
}

.preview-file {
  @apply flex items-center space-x-2;
}

.preview-file.rtl {
  @apply space-x-reverse;
}

.voice-recording {
  @apply flex items-center justify-between bg-red-50 rounded-lg p-3;
}

.recording-indicator {
  @apply flex items-center space-x-2;
}

.recording-indicator.rtl {
  @apply space-x-reverse;
}

.pulse-dot {
  @apply w-3 h-3 bg-red-500 rounded-full animate-pulse;
}

.recording-timer {
  @apply font-mono text-lg font-bold text-red-600;
}

.recording-actions {
  @apply flex space-x-2;
}

.recording-actions.rtl {
  @apply space-x-reverse;
}

.text-input-container {
  @apply flex items-end space-x-3;
}

.text-input-container.rtl {
  @apply space-x-reverse;
}

.input-actions {
  @apply flex flex-col space-y-2;
}

.text-input-wrapper {
  @apply flex-1 flex items-end bg-gray-100 rounded-2xl px-4 py-2;
}

.message-input {
  @apply flex-1 bg-transparent border-none outline-none resize-none max-h-32;
}

.send-actions {
  @apply flex flex-col space-y-2;
}

/* Attachment Menu */
.attachment-menu {
  @apply absolute bottom-20 left-4 right-4 bg-white rounded-xl shadow-lg border border-gray-200 p-4;
}

.attachment-options {
  @apply grid grid-cols-2 gap-3;
}

.attachment-option {
  @apply flex flex-col items-center space-y-2 p-3 rounded-lg hover:bg-gray-50;
}

/* Offline Queue */
.offline-queue {
  @apply bg-yellow-50 border-t border-yellow-200 p-3 flex items-center justify-between;
}

.queue-header {
  @apply flex items-center space-x-2 text-yellow-800;
}

.queue-header.rtl {
  @apply space-x-reverse;
}

/* Transitions */
.message-enter-active,
.message-leave-active {
  @apply transition-all duration-300;
}

.message-enter-from,
.message-leave-to {
  @apply opacity-0 transform translate-y-4;
}
</style> 