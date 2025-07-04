/**
 * File Upload Component - Universal Workshop Frontend V2
 * 
 * Advanced file upload with drag & drop, progress tracking, and preview
 */

export { default as FileUpload } from './FileUpload.vue'
export type { FileUploadProps, UploadFile } from './FileUpload.vue'

// Re-export composable for convenience
export { useFileUpload } from '@/composables/useFileUpload'
export type { UploadResult } from '@/composables/useFileUpload'