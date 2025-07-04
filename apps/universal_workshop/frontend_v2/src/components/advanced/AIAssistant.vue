<!--
  AI Assistant - Universal Workshop Frontend V2
  Intelligent assistant for automation, insights, and user support
-->

<template>
  <div class="ai-assistant" :class="{ 'rtl': isRTL, 'expanded': isExpanded }">
    <!-- Assistant Toggle Button -->
    <button 
      v-if="!isExpanded"
      @click="toggleAssistant"
      class="assistant-toggle"
      :title="isRTL ? 'المساعد الذكي' : 'AI Assistant'"
    >
      <Icon name="bot" class="assistant-icon" />
      <span v-if="hasUnreadSuggestions" class="notification-badge"></span>
    </button>

    <!-- Assistant Panel -->
    <div v-if="isExpanded" class="assistant-panel">
      <!-- Header -->
      <div class="assistant-header">
        <div class="header-content">
          <Icon name="bot" class="header-icon" />
          <div class="header-text">
            <h3>{{ isRTL ? 'المساعد الذكي' : 'AI Assistant' }}</h3>
            <p class="status">{{ isRTL ? statusTextAr : statusText }}</p>
          </div>
        </div>
        <div class="header-actions">
          <button @click="minimizeAssistant" class="minimize-btn">
            <Icon name="minimize" />
          </button>
          <button @click="closeAssistant" class="close-btn">
            <Icon name="x" />
          </button>
        </div>
      </div>

      <!-- Assistant Content -->
      <div class="assistant-content">
        <!-- Quick Actions -->
        <div class="quick-actions">
          <h4>{{ isRTL ? 'الإجراءات السريعة' : 'Quick Actions' }}</h4>
          <div class="action-grid">
            <button 
              v-for="action in quickActions"
              :key="action.id"
              @click="executeQuickAction(action)"
              class="action-btn"
              :disabled="action.disabled"
            >
              <Icon :name="action.icon" />
              <span>{{ isRTL ? action.titleAr : action.title }}</span>
            </button>
          </div>
        </div>

        <!-- Smart Suggestions -->
        <div class="suggestions-section" v-if="suggestions.length > 0">
          <h4>{{ isRTL ? 'اقتراحات ذكية' : 'Smart Suggestions' }}</h4>
          <div class="suggestions-list">
            <div 
              v-for="suggestion in suggestions"
              :key="suggestion.id"
              class="suggestion-item"
              :class="suggestion.priority"
            >
              <div class="suggestion-icon">
                <Icon :name="suggestion.icon" />
              </div>
              <div class="suggestion-content">
                <h5>{{ isRTL ? suggestion.titleAr : suggestion.title }}</h5>
                <p>{{ isRTL ? suggestion.descriptionAr : suggestion.description }}</p>
                <div class="suggestion-actions">
                  <button 
                    @click="applySuggestion(suggestion)"
                    class="apply-btn"
                  >
                    {{ isRTL ? 'تطبيق' : 'Apply' }}
                  </button>
                  <button 
                    @click="dismissSuggestion(suggestion.id)"
                    class="dismiss-btn"
                  >
                    {{ isRTL ? 'تجاهل' : 'Dismiss' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Interface -->
        <div class="chat-section">
          <h4>{{ isRTL ? 'اسأل المساعد' : 'Ask Assistant' }}</h4>
          
          <div class="chat-messages" ref="chatMessages">
            <div 
              v-for="message in chatHistory"
              :key="message.id"
              class="chat-message"
              :class="{ 'user': message.sender === 'user', 'assistant': message.sender === 'assistant' }"
            >
              <div class="message-content">
                <p>{{ message.content }}</p>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <input 
              v-model="currentMessage"
              @keyup.enter="sendMessage"
              :placeholder="isRTL ? 'اكتب رسالتك هنا...' : 'Type your message here...'"
              class="message-input"
              :disabled="isProcessing"
            />
            <button 
              @click="sendMessage"
              :disabled="!currentMessage.trim() || isProcessing"
              class="send-btn"
            >
              <Icon name="send" />
            </button>
          </div>
        </div>

        <!-- Analytics Insights -->
        <div class="insights-section">
          <h4>{{ isRTL ? 'رؤى تحليلية' : 'Analytics Insights' }}</h4>
          
          <div class="insights-grid">
            <div 
              v-for="insight in analyticsInsights"
              :key="insight.id"
              class="insight-card"
            >
              <div class="insight-header">
                <Icon :name="insight.icon" class="insight-icon" />
                <h5>{{ isRTL ? insight.titleAr : insight.title }}</h5>
              </div>
              <div class="insight-value">
                <span class="value">{{ insight.value }}</span>
                <span class="trend" :class="insight.trend">
                  <Icon :name="getTrendIcon(insight.trend)" />
                  {{ insight.change }}
                </span>
              </div>
              <p class="insight-description">
                {{ isRTL ? insight.descriptionAr : insight.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Automation Status -->
        <div class="automation-section">
          <h4>{{ isRTL ? 'حالة الأتمتة' : 'Automation Status' }}</h4>
          
          <div class="automation-list">
            <div 
              v-for="automation in automations"
              :key="automation.id"
              class="automation-item"
            >
              <div class="automation-info">
                <Icon :name="automation.icon" class="automation-icon" />
                <div class="automation-details">
                  <h5>{{ isRTL ? automation.nameAr : automation.name }}</h5>
                  <p>{{ isRTL ? automation.descriptionAr : automation.description }}</p>
                </div>
              </div>
              <div class="automation-controls">
                <div class="automation-status" :class="automation.status">
                  {{ isRTL ? getStatusTextAr(automation.status) : automation.status }}
                </div>
                <button 
                  @click="toggleAutomation(automation.id)"
                  class="toggle-btn"
                  :class="{ 'active': automation.enabled }"
                >
                  <Icon :name="automation.enabled ? 'toggle-right' : 'toggle-left'" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Floating Notifications -->
    <div class="floating-notifications" v-if="floatingNotifications.length > 0">
      <div 
        v-for="notification in floatingNotifications"
        :key="notification.id"
        class="floating-notification"
        :class="notification.type"
      >
        <Icon :name="notification.icon" />
        <span>{{ isRTL ? notification.messageAr : notification.message }}</span>
        <button @click="dismissNotification(notification.id)" class="dismiss-floating">
          <Icon name="x" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import Icon from '@/components/common/Icon.vue'

// Composables
const { locale } = useI18n()
const isRTL = computed(() => locale.value === 'ar')

// State
const isExpanded = ref(false)
const isProcessing = ref(false)
const currentMessage = ref('')
const chatMessages = ref<HTMLElement>()

// Assistant status
const statusText = ref('Ready to help')
const statusTextAr = ref('جاهز للمساعدة')

// Quick actions
const quickActions = ref([
  {
    id: 'new-customer',
    title: 'Add Customer',
    titleAr: 'إضافة عميل',
    icon: 'user-plus',
    disabled: false
  },
  {
    id: 'new-service',
    title: 'Create Service',
    titleAr: 'إنشاء خدمة',
    icon: 'wrench',
    disabled: false
  },
  {
    id: 'inventory-check',
    title: 'Check Inventory',
    titleAr: 'فحص المخزون',
    icon: 'package',
    disabled: false
  },
  {
    id: 'generate-report',
    title: 'Generate Report',
    titleAr: 'إنشاء تقرير',
    icon: 'file-text',
    disabled: false
  }
])

// Smart suggestions
const suggestions = ref([
  {
    id: 1,
    title: 'Low Stock Alert',
    titleAr: 'تنبيه مخزون منخفض',
    description: 'Several parts are running low. Consider reordering.',
    descriptionAr: 'عدة قطع تنخفض. فكر في إعادة الطلب.',
    icon: 'alert-triangle',
    priority: 'high',
    action: 'inventory-reorder'
  },
  {
    id: 2,
    title: 'Optimize Schedule',
    titleAr: 'تحسين الجدولة',
    description: 'Reschedule appointments for better efficiency.',
    descriptionAr: 'إعادة جدولة المواعيد لكفاءة أفضل.',
    icon: 'calendar',
    priority: 'medium',
    action: 'schedule-optimize'
  }
])

// Chat history
const chatHistory = ref([
  {
    id: 1,
    sender: 'assistant',
    content: isRTL.value ? 'مرحباً! كيف يمكنني مساعدتك اليوم؟' : 'Hello! How can I help you today?',
    timestamp: new Date()
  }
])

// Analytics insights
const analyticsInsights = ref([
  {
    id: 1,
    title: 'Revenue Growth',
    titleAr: 'نمو الإيرادات',
    description: 'Monthly revenue increased',
    descriptionAr: 'زادت الإيرادات الشهرية',
    icon: 'trending-up',
    value: 'OMR 15,240',
    change: '+12%',
    trend: 'up'
  },
  {
    id: 2,
    title: 'Customer Satisfaction',
    titleAr: 'رضا العملاء',
    description: 'Average satisfaction score',
    descriptionAr: 'متوسط نقاط الرضا',
    icon: 'heart',
    value: '4.8/5',
    change: '+0.3',
    trend: 'up'
  },
  {
    id: 3,
    title: 'Service Efficiency',
    titleAr: 'كفاءة الخدمة',
    description: 'Average completion time',
    descriptionAr: 'متوسط وقت الإنجاز',
    icon: 'clock',
    value: '2.3 hrs',
    change: '-15 min',
    trend: 'down'
  }
])

// Automations
const automations = ref([
  {
    id: 1,
    name: 'Inventory Alerts',
    nameAr: 'تنبيهات المخزون',
    description: 'Automatic low stock notifications',
    descriptionAr: 'إشعارات تلقائية للمخزون المنخفض',
    icon: 'bell',
    enabled: true,
    status: 'active'
  },
  {
    id: 2,
    name: 'Customer Reminders',
    nameAr: 'تذكيرات العملاء',
    description: 'Automated service reminders',
    descriptionAr: 'تذكيرات خدمة تلقائية',
    icon: 'message-circle',
    enabled: true,
    status: 'active'
  },
  {
    id: 3,
    name: 'Report Generation',
    nameAr: 'إنشاء التقارير',
    description: 'Weekly automated reports',
    descriptionAr: 'تقارير تلقائية أسبوعية',
    icon: 'file-text',
    enabled: false,
    status: 'inactive'
  }
])

// Floating notifications
const floatingNotifications = ref([])

// Computed
const hasUnreadSuggestions = computed(() => suggestions.value.length > 0)

// Methods
const toggleAssistant = () => {
  isExpanded.value = true
}

const minimizeAssistant = () => {
  isExpanded.value = false
}

const closeAssistant = () => {
  isExpanded.value = false
}

const executeQuickAction = async (action: any) => {
  console.log('Executing quick action:', action.id)
  
  // Simulate action execution
  action.disabled = true
  
  try {
    switch (action.id) {
      case 'new-customer':
        // Navigate to customer creation
        break
      case 'new-service':
        // Navigate to service creation
        break
      case 'inventory-check':
        // Open inventory dashboard
        break
      case 'generate-report':
        // Generate and download report
        break
    }
    
    // Add success message to chat
    addChatMessage('assistant', isRTL.value 
      ? `تم تنفيذ ${action.titleAr} بنجاح`
      : `${action.title} executed successfully`
    )
  } catch (error) {
    console.error('Action failed:', error)
    addChatMessage('assistant', isRTL.value 
      ? `فشل في تنفيذ ${action.titleAr}`
      : `Failed to execute ${action.title}`
    )
  } finally {
    action.disabled = false
  }
}

const applySuggestion = async (suggestion: any) => {
  console.log('Applying suggestion:', suggestion.id)
  
  try {
    // Simulate applying suggestion
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Remove suggestion from list
    suggestions.value = suggestions.value.filter(s => s.id !== suggestion.id)
    
    // Add confirmation to chat
    addChatMessage('assistant', isRTL.value 
      ? `تم تطبيق الاقتراح: ${suggestion.titleAr}`
      : `Applied suggestion: ${suggestion.title}`
    )
  } catch (error) {
    console.error('Failed to apply suggestion:', error)
  }
}

const dismissSuggestion = (suggestionId: number) => {
  suggestions.value = suggestions.value.filter(s => s.id !== suggestionId)
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isProcessing.value) return
  
  const message = currentMessage.value.trim()
  currentMessage.value = ''
  
  // Add user message
  addChatMessage('user', message)
  
  isProcessing.value = true
  
  try {
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Generate AI response
    const response = await generateAIResponse(message)
    addChatMessage('assistant', response)
  } catch (error) {
    console.error('Failed to process message:', error)
    addChatMessage('assistant', isRTL.value 
      ? 'عذراً، حدث خطأ في معالجة رسالتك'
      : 'Sorry, there was an error processing your message'
    )
  } finally {
    isProcessing.value = false
  }
}

const addChatMessage = (sender: 'user' | 'assistant', content: string) => {
  chatHistory.value.push({
    id: Date.now(),
    sender,
    content,
    timestamp: new Date()
  })
  
  // Scroll to bottom
  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

const generateAIResponse = async (message: string): Promise<string> => {
  // Simple AI response simulation
  const responses = {
    ar: [
      'أفهم استفسارك. دعني أساعدك في ذلك.',
      'هذا سؤال جيد. إليك ما يمكنني اقتراحه...',
      'بناءً على البيانات المتاحة، أنصح بـ...',
      'يمكنني مساعدتك في هذا الأمر.'
    ],
    en: [
      'I understand your query. Let me help you with that.',
      'That\'s a good question. Here\'s what I can suggest...',
      'Based on the available data, I recommend...',
      'I can help you with this matter.'
    ]
  }
  
  const responseList = isRTL.value ? responses.ar : responses.en
  return responseList[Math.floor(Math.random() * responseList.length)]
}

const toggleAutomation = (automationId: number) => {
  const automation = automations.value.find(a => a.id === automationId)
  if (automation) {
    automation.enabled = !automation.enabled
    automation.status = automation.enabled ? 'active' : 'inactive'
    
    // Add notification
    addFloatingNotification(
      automation.enabled ? 'success' : 'info',
      isRTL.value 
        ? `تم ${automation.enabled ? 'تفعيل' : 'إيقاف'} ${automation.nameAr}`
        : `${automation.name} ${automation.enabled ? 'enabled' : 'disabled'}`,
      'check'
    )
  }
}

const addFloatingNotification = (type: string, message: string, icon: string) => {
  const notification = {
    id: Date.now(),
    type,
    message,
    messageAr: message, // In real app, translate this
    icon
  }
  
  floatingNotifications.value.push(notification)
  
  // Auto dismiss after 3 seconds
  setTimeout(() => {
    dismissNotification(notification.id)
  }, 3000)
}

const dismissNotification = (notificationId: number) => {
  floatingNotifications.value = floatingNotifications.value.filter(n => n.id !== notificationId)
}

const formatTime = (timestamp: Date): string => {
  return timestamp.toLocaleTimeString(isRTL.value ? 'ar' : 'en', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getTrendIcon = (trend: string): string => {
  return trend === 'up' ? 'arrow-up' : 'arrow-down'
}

const getStatusTextAr = (status: string): string => {
  const statusMap = {
    active: 'نشط',
    inactive: 'غير نشط',
    pending: 'في الانتظار'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

// Lifecycle
onMounted(() => {
  // Initialize AI assistant
  console.log('AI Assistant initialized')
  
  // Simulate receiving suggestions
  setTimeout(() => {
    if (suggestions.value.length > 0) {
      addFloatingNotification(
        'info',
        isRTL.value ? 'لديك اقتراحات جديدة من المساعد الذكي' : 'You have new suggestions from AI Assistant',
        'lightbulb'
      )
    }
  }, 3000)
})
</script>

<style scoped>
.ai-assistant {
  @apply fixed bottom-6 right-6 z-50;
}

.ai-assistant.rtl {
  @apply left-6 right-auto;
}

.assistant-toggle {
  @apply w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all duration-300 flex items-center justify-center relative;
}

.assistant-icon {
  @apply w-6 h-6;
}

.notification-badge {
  @apply absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full;
}

.assistant-panel {
  @apply w-96 h-[600px] bg-white rounded-lg shadow-xl border overflow-hidden flex flex-col;
}

.assistant-header {
  @apply flex items-center justify-between p-4 bg-blue-600 text-white;
}

.header-content {
  @apply flex items-center gap-3;
}

.header-icon {
  @apply w-6 h-6;
}

.header-text h3 {
  @apply font-semibold;
}

.status {
  @apply text-blue-100 text-sm;
}

.header-actions {
  @apply flex gap-2;
}

.minimize-btn, .close-btn {
  @apply p-1 hover:bg-blue-700 rounded;
}

.assistant-content {
  @apply flex-1 overflow-y-auto p-4 space-y-6;
}

.quick-actions h4,
.suggestions-section h4,
.chat-section h4,
.insights-section h4,
.automation-section h4 {
  @apply font-semibold text-gray-900 mb-3;
}

.action-grid {
  @apply grid grid-cols-2 gap-2;
}

.action-btn {
  @apply p-3 border rounded-lg hover:bg-gray-50 flex flex-col items-center gap-2 text-sm transition-colors;
}

.action-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.suggestions-list {
  @apply space-y-3;
}

.suggestion-item {
  @apply flex gap-3 p-3 border rounded-lg;
}

.suggestion-item.high {
  @apply border-red-200 bg-red-50;
}

.suggestion-item.medium {
  @apply border-yellow-200 bg-yellow-50;
}

.suggestion-item.low {
  @apply border-blue-200 bg-blue-50;
}

.suggestion-icon {
  @apply flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-white;
}

.suggestion-content {
  @apply flex-1;
}

.suggestion-content h5 {
  @apply font-medium text-gray-900 mb-1;
}

.suggestion-content p {
  @apply text-gray-600 text-sm mb-2;
}

.suggestion-actions {
  @apply flex gap-2;
}

.apply-btn {
  @apply px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700;
}

.dismiss-btn {
  @apply px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300;
}

.chat-messages {
  @apply h-40 overflow-y-auto border rounded-lg p-3 space-y-3 mb-3;
}

.chat-message {
  @apply flex;
}

.chat-message.user {
  @apply justify-end;
}

.chat-message.assistant {
  @apply justify-start;
}

.message-content {
  @apply max-w-[80%] p-2 rounded-lg;
}

.chat-message.user .message-content {
  @apply bg-blue-600 text-white;
}

.chat-message.assistant .message-content {
  @apply bg-gray-100 text-gray-900;
}

.message-time {
  @apply text-xs opacity-70 block mt-1;
}

.chat-input {
  @apply flex gap-2;
}

.message-input {
  @apply flex-1 px-3 py-2 border rounded-lg;
}

.send-btn {
  @apply px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50;
}

.insights-grid {
  @apply space-y-3;
}

.insight-card {
  @apply p-3 border rounded-lg;
}

.insight-header {
  @apply flex items-center gap-2 mb-2;
}

.insight-icon {
  @apply w-4 h-4 text-blue-600;
}

.insight-header h5 {
  @apply font-medium text-gray-900;
}

.insight-value {
  @apply flex items-center gap-2 mb-2;
}

.value {
  @apply text-lg font-bold text-gray-900;
}

.trend {
  @apply text-sm flex items-center gap-1;
}

.trend.up {
  @apply text-green-600;
}

.trend.down {
  @apply text-red-600;
}

.insight-description {
  @apply text-gray-600 text-sm;
}

.automation-list {
  @apply space-y-3;
}

.automation-item {
  @apply flex items-center justify-between p-3 border rounded-lg;
}

.automation-info {
  @apply flex items-center gap-3;
}

.automation-icon {
  @apply w-5 h-5 text-gray-600;
}

.automation-details h5 {
  @apply font-medium text-gray-900;
}

.automation-details p {
  @apply text-gray-600 text-sm;
}

.automation-controls {
  @apply flex items-center gap-2;
}

.automation-status {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.automation-status.active {
  @apply bg-green-100 text-green-700;
}

.automation-status.inactive {
  @apply bg-gray-100 text-gray-700;
}

.toggle-btn {
  @apply p-1 text-gray-400 hover:text-gray-600;
}

.toggle-btn.active {
  @apply text-blue-600;
}

.floating-notifications {
  @apply fixed bottom-24 right-6 space-y-2 z-40;
}

.ai-assistant.rtl .floating-notifications {
  @apply left-6 right-auto;
}

.floating-notification {
  @apply flex items-center gap-2 px-4 py-2 rounded-lg shadow-lg text-white max-w-sm;
}

.floating-notification.success {
  @apply bg-green-600;
}

.floating-notification.info {
  @apply bg-blue-600;
}

.floating-notification.warning {
  @apply bg-yellow-600;
}

.floating-notification.error {
  @apply bg-red-600;
}

.dismiss-floating {
  @apply ml-auto p-1 hover:bg-black hover:bg-opacity-20 rounded;
}
</style> 