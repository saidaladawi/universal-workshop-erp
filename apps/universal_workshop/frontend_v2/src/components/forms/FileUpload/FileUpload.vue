<template>
  <div class="file-upload" :class="uploadClasses" :dir="textDirection">
    <!-- Upload Area -->
    <div
      class="file-upload__dropzone"
      :class="dropzoneClasses"
      @click="openFileDialog"
      @dragover.prevent="handleDragOver"
      @dragenter.prevent="handleDragEnter"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <!-- Upload Icon and Text -->
      <div class="file-upload__content">
        <div class="file-upload__icon">
          <Icon :name="getUploadIcon()" />
        </div>
        
        <div class="file-upload__text">
          <h4>{{ getMainText() }}</h4>
          <p>{{ getSubText() }}</p>
          <p v-if="maxFileSize" class="file-upload__size-limit">
            {{ isRTL ? 'الحد الأقصى لحجم الملف:' : 'Max file size:' }} 
            {{ formatFileSize(maxFileSize) }}
          </p>
        </div>

        <!-- Browse Button -->
        <Button
          variant="primary"
          :disabled="disabled || uploading"
          @click.stop="openFileDialog"
        >
          {{ isRTL ? 'تصفح الملفات' : 'Browse Files' }}
        </Button>
      </div>

      <!-- Hidden File Input -->
      <input
        ref="fileInputRef"
        type="file"
        :multiple="multiple"
        :accept="accept"
        @change="handleFileSelect"
        class="file-upload__input"
        :disabled="disabled"
      />
    </div>

    <!-- Upload Progress -->
    <div v-if="uploading" class="file-upload__progress">
      <div class="file-upload__progress-bar">
        <div 
          class="file-upload__progress-fill"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
      <p class="file-upload__progress-text">
        {{ isRTL ? 'جاري الرفع...' : 'Uploading...' }} {{ uploadProgress }}%
      </p>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="file-upload__files">
      <h5 class="file-upload__files-title">
        {{ isRTL ? 'الملفات المحددة' : 'Selected Files' }} ({{ files.length }})
      </h5>
      
      <div class="file-upload__files-list">
        <div
          v-for="(file, index) in files"
          :key="file.id"
          class="file-upload__file-item"
          :class="getFileItemClasses(file)"
        >
          <!-- File Icon -->
          <div class="file-upload__file-icon">
            <Icon :name="getFileIcon(file)" />
          </div>

          <!-- File Info -->
          <div class="file-upload__file-info">
            <span class="file-upload__file-name">{{ file.name }}</span>
            <span class="file-upload__file-size">{{ formatFileSize(file.size) }}</span>
            
            <!-- File Status -->
            <div class="file-upload__file-status">
              <span v-if="file.status === 'uploading'" class="status status--uploading">
                {{ isRTL ? 'جاري الرفع...' : 'Uploading...' }}
              </span>
              <span v-else-if="file.status === 'uploaded'" class="status status--success">
                {{ isRTL ? 'تم الرفع' : 'Uploaded' }}
              </span>
              <span v-else-if="file.status === 'error'" class="status status--error">
                {{ file.error || (isRTL ? 'خطأ في الرفع' : 'Upload error') }}
              </span>
              <span v-else class="status status--pending">
                {{ isRTL ? 'في الانتظار' : 'Pending' }}
              </span>
            </div>
          </div>

          <!-- File Actions -->
          <div class="file-upload__file-actions">
            <button
              v-if="file.status === 'pending' || file.status === 'error'"
              @click="uploadFile(file)"
              class="file-upload__action-btn"
              :title="isRTL ? 'رفع الملف' : 'Upload file'"
              :disabled="uploading"
            >
              <Icon name="upload" />
            </button>
            
            <button
              v-if="file.status === 'uploaded' && file.url"
              @click="previewFile(file)"
              class="file-upload__action-btn"
              :title="isRTL ? 'معاينة الملف' : 'Preview file'"
            >
              <Icon name="eye" />
            </button>
            
            <button
              @click="removeFile(index)"
              class="file-upload__action-btn file-upload__action-btn--remove"
              :title="isRTL ? 'إزالة الملف' : 'Remove file'"
              :disabled="uploading && file.status === 'uploading'"
            >
              <Icon name="trash" />
            </button>
          </div>
        </div>
      </div>

      <!-- Upload All Button -->
      <div v-if="multiple && hasPendingFiles" class="file-upload__actions">
        <Button
          variant="primary"
          @click="uploadAllFiles"
          :disabled="uploading"
          :loading="uploading"
        >
          {{ isRTL ? 'رفع جميع الملفات' : 'Upload All Files' }}
        </Button>
        
        <Button
          variant="secondary"
          @click="clearAllFiles"
          :disabled="uploading"
        >
          {{ isRTL ? 'مسح الجميع' : 'Clear All' }}
        </Button>
      </div>
    </div>

    <!-- File Preview Modal -->
    <Modal
      v-if="previewFile"
      :show="showPreview"
      :title="previewFile?.name || ''"
      @close="closePreview"
      size="large"
    >
      <div class="file-upload__preview">
        <!-- Image Preview -->
        <img
          v-if="isImageFile(previewFile)"
          :src="previewFile.url"
          :alt="previewFile.name"
          class="file-upload__preview-image"
        />
        
        <!-- PDF Preview -->
        <iframe
          v-else-if="isPdfFile(previewFile)"
          :src="previewFile.url"
          class="file-upload__preview-pdf"
        ></iframe>
        
        <!-- Text Preview -->
        <pre
          v-else-if="isTextFile(previewFile)"
          class="file-upload__preview-text"
        >{{ previewFile.content }}</pre>
        
        <!-- Default Preview -->
        <div v-else class="file-upload__preview-default">
          <Icon name="file" class="file-upload__preview-icon" />
          <p>{{ isRTL ? 'معاينة غير متوفرة لهذا النوع من الملفات' : 'Preview not available for this file type' }}</p>
          <Button
            v-if="previewFile.url"
            @click="downloadFile(previewFile)"
          >
            {{ isRTL ? 'تحميل الملف' : 'Download File' }}
          </Button>
        </div>
      </div>
    </Modal>

    <!-- Error Messages -->
    <div v-if="errors.length > 0" class="file-upload__errors">
      <Alert
        v-for="(error, index) in errors"
        :key="index"
        type="error"
        :closable="true"
        @close="removeError(index)"
      >
        {{ error }}
      </Alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useArabicUtils } from '@/composables/useArabicUtils'
import { useFileUpload } from '@/composables/useFileUpload'
import Icon from '@/components/primitives/Icon/Icon.vue'
import Button from '@/components/base/Button.vue'
import Modal from '@/components/feedback/Modal.vue'
import Alert from '@/components/feedback/Alert.vue'

// File interface
export interface UploadFile {
  id: string
  name: string
  size: number
  type: string
  file: File
  status: 'pending' | 'uploading' | 'uploaded' | 'error'
  progress?: number
  url?: string
  error?: string
  content?: string
}

// Component props
export interface FileUploadProps {
  accept?: string
  multiple?: boolean
  maxFileSize?: number // in bytes
  maxFiles?: number
  uploadUrl?: string
  disabled?: boolean
  dragAndDrop?: boolean
  autoUpload?: boolean
  showPreview?: boolean
  allowedTypes?: string[]
  customUploadHandler?: (file: File) => Promise<{ url: string; success: boolean; error?: string }>
}

const props = withDefaults(defineProps<FileUploadProps>(), {
  accept: '*/*',
  multiple: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 10,
  disabled: false,
  dragAndDrop: true,
  autoUpload: false,
  showPreview: true,
  allowedTypes: () => []
})

// Emits
const emit = defineEmits<{
  'files-selected': [files: UploadFile[]]
  'upload-progress': [progress: number, file: UploadFile]
  'upload-complete': [file: UploadFile]
  'upload-error': [error: string, file: UploadFile]
  'all-uploads-complete': [files: UploadFile[]]
}>()

// Composables
const { isArabicLocale, getTextDirection } = useArabicUtils()
const { uploadFile: uploadFileToServer, uploadProgress } = useFileUpload()

// Refs
const fileInputRef = ref<HTMLInputElement>()
const files = ref<UploadFile[]>([])
const isDragOver = ref(false)
const uploading = ref(false)
const errors = ref<string[]>([])
const previewFile = ref<UploadFile | null>(null)
const showPreview = ref(false)

// Computed
const isRTL = computed(() => isArabicLocale())
const textDirection = computed(() => getTextDirection())

const uploadClasses = computed(() => [
  'file-upload',
  {
    'file-upload--rtl': isRTL.value,
    'file-upload--disabled': props.disabled,
    'file-upload--uploading': uploading.value
  }
])

const dropzoneClasses = computed(() => [
  'file-upload__dropzone',
  {
    'file-upload__dropzone--drag-over': isDragOver.value,
    'file-upload__dropzone--disabled': props.disabled,
    'file-upload__dropzone--has-files': files.value.length > 0
  }
])

const hasPendingFiles = computed(() => 
  files.value.some(file => file.status === 'pending' || file.status === 'error')
)

// Methods
const openFileDialog = () => {
  if (props.disabled || uploading.value) return
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    processFiles(Array.from(input.files))
  }
  // Reset input value to allow selecting the same file again
  input.value = ''
}

const handleDragOver = (event: DragEvent) => {
  if (!props.dragAndDrop || props.disabled) return
  event.preventDefault()
  isDragOver.value = true
}

const handleDragEnter = (event: DragEvent) => {
  if (!props.dragAndDrop || props.disabled) return
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  if (!props.dragAndDrop || props.disabled) return
  event.preventDefault()
  // Check if we're actually leaving the dropzone
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    isDragOver.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  if (!props.dragAndDrop || props.disabled) return
  event.preventDefault()
  isDragOver.value = false
  
  const droppedFiles = Array.from(event.dataTransfer?.files || [])
  processFiles(droppedFiles)
}

const processFiles = (fileList: File[]) => {
  const newFiles: UploadFile[] = []
  
  for (const file of fileList) {
    // Check file count limit
    if (!props.multiple && files.value.length > 0) {
      addError(isRTL.value ? 'يمكن رفع ملف واحد فقط' : 'Only one file can be uploaded')
      break
    }
    
    if (files.value.length + newFiles.length >= props.maxFiles) {
      addError(isRTL.value ? 
        `الحد الأقصى للملفات هو ${props.maxFiles}` : 
        `Maximum ${props.maxFiles} files allowed`
      )
      break
    }
    
    // Check file size
    if (file.size > props.maxFileSize) {
      addError(isRTL.value ? 
        `حجم الملف ${file.name} كبير جداً` : 
        `File ${file.name} is too large`
      )
      continue
    }
    
    // Check file type
    if (props.allowedTypes.length > 0 && !props.allowedTypes.includes(file.type)) {
      addError(isRTL.value ? 
        `نوع الملف ${file.name} غير مدعوم` : 
        `File type of ${file.name} is not supported`
      )
      continue
    }
    
    const uploadFile: UploadFile = {
      id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
      status: 'pending'
    }
    
    newFiles.push(uploadFile)
  }
  
  files.value.push(...newFiles)
  emit('files-selected', [...files.value])
  
  // Auto upload if enabled
  if (props.autoUpload && newFiles.length > 0) {
    uploadAllFiles()
  }
}

const uploadFile = async (file: UploadFile) => {
  if (uploading.value) return
  
  file.status = 'uploading'
  uploading.value = true
  
  try {
    let result
    
    if (props.customUploadHandler) {
      result = await props.customUploadHandler(file.file)
    } else {
      result = await uploadFileToServer(file.file, props.uploadUrl)
    }
    
    if (result.success) {
      file.status = 'uploaded'
      file.url = result.url
      emit('upload-complete', file)
    } else {
      file.status = 'error'
      file.error = result.error || 'Upload failed'
      emit('upload-error', file.error, file)
    }
  } catch (error) {
    file.status = 'error'
    file.error = error instanceof Error ? error.message : 'Upload failed'
    emit('upload-error', file.error, file)
  } finally {
    uploading.value = false
  }
}

const uploadAllFiles = async () => {
  const pendingFiles = files.value.filter(file => 
    file.status === 'pending' || file.status === 'error'
  )
  
  for (const file of pendingFiles) {
    await uploadFile(file)
  }
  
  emit('all-uploads-complete', [...files.value])
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
  emit('files-selected', [...files.value])
}

const clearAllFiles = () => {
  files.value = []
  emit('files-selected', [])
}

const previewFileHandler = (file: UploadFile) => {
  previewFile.value = file
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
  previewFile.value = null
}

const downloadFile = (file: UploadFile) => {
  if (file.url) {
    const link = document.createElement('a')
    link.href = file.url
    link.download = file.name
    link.click()
  }
}

const addError = (message: string) => {
  errors.value.push(message)
}

const removeError = (index: number) => {
  errors.value.splice(index, 1)
}

// Helper functions
const getUploadIcon = (): string => {
  if (uploading.value) return 'upload'
  if (files.value.length > 0) return 'check-circle'
  return 'cloud-upload'
}

const getMainText = (): string => {
  if (uploading.value) {
    return isRTL.value ? 'جاري رفع الملفات...' : 'Uploading files...'
  }
  if (files.value.length > 0) {
    return isRTL.value ? 'تم تحديد الملفات' : 'Files selected'
  }
  return isRTL.value ? 'اسحب الملفات هنا أو انقر للتصفح' : 'Drag files here or click to browse'
}

const getSubText = (): string => {
  if (uploading.value) return ''
  if (files.value.length > 0) {
    return isRTL.value ? 'انقر لإضافة المزيد من الملفات' : 'Click to add more files'
  }
  
  const formats = props.allowedTypes.length > 0 ? 
    props.allowedTypes.join(', ') : 
    (isRTL.value ? 'جميع أنواع الملفات' : 'All file types')
  
  return isRTL.value ? `أنواع الملفات المدعومة: ${formats}` : `Supported formats: ${formats}`
}

const getFileIcon = (file: UploadFile): string => {
  const type = file.type.toLowerCase()
  
  if (type.startsWith('image/')) return 'image'
  if (type.includes('pdf')) return 'file-pdf'
  if (type.includes('word') || type.includes('document')) return 'file-word'
  if (type.includes('excel') || type.includes('spreadsheet')) return 'file-excel'
  if (type.includes('powerpoint') || type.includes('presentation')) return 'file-powerpoint'
  if (type.includes('zip') || type.includes('rar')) return 'file-zip'
  if (type.includes('video/')) return 'file-video'
  if (type.includes('audio/')) return 'file-audio'
  if (type.includes('text/')) return 'file-text'
  
  return 'file'
}

const getFileItemClasses = (file: UploadFile) => [
  'file-upload__file-item',
  `file-upload__file-item--${file.status}`
]

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = isRTL.value ? 
    ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت'] :
    ['Bytes', 'KB', 'MB', 'GB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(2))
  
  return `${size} ${sizes[i]}`
}

const isImageFile = (file: UploadFile): boolean => {
  return file.type.startsWith('image/')
}

const isPdfFile = (file: UploadFile): boolean => {
  return file.type === 'application/pdf'
}

const isTextFile = (file: UploadFile): boolean => {
  return file.type.startsWith('text/')
}

// Clear errors after 5 seconds
watch(errors, () => {
  setTimeout(() => {
    errors.value = []
  }, 5000)
})
</script>

<style lang="scss" scoped>
@import '@/styles/design-system/tokens.scss';

.file-upload {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);

  &--rtl {
    direction: rtl;
  }

  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }

  // Dropzone
  &__dropzone {
    border: 2px dashed var(--color-border-subtle);
    border-radius: var(--border-radius-lg);
    padding: var(--spacing-xl);
    text-align: center;
    background: var(--color-surface-secondary);
    transition: all 0.3s ease;
    cursor: pointer;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover:not(&--disabled) {
      border-color: var(--color-primary-400);
      background: var(--color-primary-50);
    }

    &--drag-over {
      border-color: var(--color-primary-500);
      background: var(--color-primary-100);
      transform: scale(1.02);
    }

    &--has-files {
      min-height: 120px;
      background: var(--color-success-50);
      border-color: var(--color-success-300);
    }

    &--disabled {
      cursor: not-allowed;
      background: var(--color-surface-tertiary);
    }
  }

  &__content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
    max-width: 400px;
  }

  &__icon {
    width: 64px;
    height: 64px;
    color: var(--color-primary-500);

    .file-upload__dropzone--has-files & {
      color: var(--color-success-500);
    }
  }

  &__text {
    h4 {
      margin: 0 0 var(--spacing-xs) 0;
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
    }

    p {
      margin: 0 0 var(--spacing-xs) 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }
  }

  &__size-limit {
    font-style: italic;
    color: var(--color-text-tertiary);
  }

  &__input {
    display: none;
  }

  // Progress
  &__progress {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  &__progress-bar {
    width: 100%;
    height: 8px;
    background: var(--color-surface-tertiary);
    border-radius: var(--border-radius-full);
    overflow: hidden;
  }

  &__progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    transition: width 0.3s ease;
  }

  &__progress-text {
    text-align: center;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
  }

  // Files list
  &__files {
    background: var(--color-surface-primary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-md);
    padding: var(--spacing-lg);
  }

  &__files-title {
    margin: 0 0 var(--spacing-md) 0;
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
  }

  &__files-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  &__file-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--color-surface-secondary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-sm);
    transition: all 0.2s;

    &--uploading {
      border-color: var(--color-primary-300);
      background: var(--color-primary-50);
    }

    &--uploaded {
      border-color: var(--color-success-300);
      background: var(--color-success-50);
    }

    &--error {
      border-color: var(--color-error-300);
      background: var(--color-error-50);
    }
  }

  &__file-icon {
    width: 32px;
    height: 32px;
    color: var(--color-primary-500);
    flex-shrink: 0;
  }

  &__file-info {
    flex: 1;
    min-width: 0;
  }

  &__file-name {
    display: block;
    font-weight: var(--font-weight-medium);
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__file-size {
    display: block;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  &__file-status {
    margin-top: var(--spacing-xs);

    .status {
      font-size: var(--font-size-xs);
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--border-radius-sm);
      font-weight: var(--font-weight-medium);

      &--pending {
        background: var(--color-warning-100);
        color: var(--color-warning-700);
      }

      &--uploading {
        background: var(--color-primary-100);
        color: var(--color-primary-700);
      }

      &--success {
        background: var(--color-success-100);
        color: var(--color-success-700);
      }

      &--error {
        background: var(--color-error-100);
        color: var(--color-error-700);
      }
    }
  }

  &__file-actions {
    display: flex;
    gap: var(--spacing-xs);
    flex-shrink: 0;
  }

  &__action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--color-surface-primary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all 0.2s;
    color: var(--color-text-secondary);

    &:hover:not(:disabled) {
      background: var(--color-primary-50);
      border-color: var(--color-primary-300);
      color: var(--color-primary-600);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &--remove {
      &:hover:not(:disabled) {
        background: var(--color-error-50);
        border-color: var(--color-error-300);
        color: var(--color-error-600);
      }
    }
  }

  &__actions {
    display: flex;
    justify-content: center;
    gap: var(--spacing-md);
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--color-border-subtle);
  }

  // Preview
  &__preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
    max-height: 70vh;
    overflow: auto;
  }

  &__preview-image {
    max-width: 100%;
    max-height: 60vh;
    object-fit: contain;
    border-radius: var(--border-radius-md);
  }

  &__preview-pdf {
    width: 100%;
    height: 60vh;
    border: none;
    border-radius: var(--border-radius-md);
  }

  &__preview-text {
    width: 100%;
    max-height: 60vh;
    overflow: auto;
    background: var(--color-surface-secondary);
    padding: var(--spacing-md);
    border-radius: var(--border-radius-md);
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
    white-space: pre-wrap;
  }

  &__preview-default {
    text-align: center;
    padding: var(--spacing-xl);
  }

  &__preview-icon {
    width: 64px;
    height: 64px;
    color: var(--color-text-tertiary);
    margin-bottom: var(--spacing-md);
  }

  // Errors
  &__errors {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
</style>