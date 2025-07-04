/**
 * File Upload Composable - Universal Workshop Frontend V2
 * 
 * Provides file upload functionality with progress tracking and error handling
 */

import { ref } from 'vue'

export interface UploadResult {
  success: boolean
  url?: string
  error?: string
  data?: any
}

export function useFileUpload() {
  const uploadProgress = ref(0)
  const isUploading = ref(false)

  const uploadFile = async (
    file: File, 
    uploadUrl: string = '/api/upload',
    additionalData?: Record<string, any>
  ): Promise<UploadResult> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData()
      formData.append('file', file)
      
      // Add additional data if provided
      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, value)
        })
      }

      const xhr = new XMLHttpRequest()

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          uploadProgress.value = Math.round((event.loaded / event.total) * 100)
        }
      })

      // Handle successful upload
      xhr.addEventListener('load', () => {
        isUploading.value = false
        uploadProgress.value = 0

        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText)
            resolve({
              success: true,
              url: response.url || response.file_url,
              data: response
            })
          } catch (error) {
            resolve({
              success: false,
              error: 'Invalid response format'
            })
          }
        } else {
          resolve({
            success: false,
            error: `Upload failed with status ${xhr.status}`
          })
        }
      })

      // Handle upload error
      xhr.addEventListener('error', () => {
        isUploading.value = false
        uploadProgress.value = 0
        resolve({
          success: false,
          error: 'Network error during upload'
        })
      })

      // Handle upload abort
      xhr.addEventListener('abort', () => {
        isUploading.value = false
        uploadProgress.value = 0
        resolve({
          success: false,
          error: 'Upload was aborted'
        })
      })

      // Start upload
      isUploading.value = true
      uploadProgress.value = 0

      // Add CSRF token if available (for Frappe)
      if (typeof window !== 'undefined' && window.frappe?.csrf_token) {
        xhr.setRequestHeader('X-Frappe-CSRF-Token', window.frappe.csrf_token)
      }

      xhr.open('POST', uploadUrl)
      xhr.send(formData)
    })
  }

  const uploadMultipleFiles = async (
    files: File[],
    uploadUrl: string = '/api/upload',
    additionalData?: Record<string, any>
  ): Promise<UploadResult[]> => {
    const results: UploadResult[] = []
    
    for (const file of files) {
      try {
        const result = await uploadFile(file, uploadUrl, additionalData)
        results.push(result)
      } catch (error) {
        results.push({
          success: false,
          error: error instanceof Error ? error.message : 'Upload failed'
        })
      }
    }
    
    return results
  }

  const uploadToFrappe = async (
    file: File,
    doctype?: string,
    docname?: string,
    fieldname?: string
  ): Promise<UploadResult> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_private', '0')
    
    if (doctype) formData.append('doctype', doctype)
    if (docname) formData.append('docname', docname)
    if (fieldname) formData.append('fieldname', fieldname)

    return uploadFile(file, '/api/method/upload_file', {
      doctype,
      docname,
      fieldname,
      is_private: 0
    })
  }

  const validateFile = (
    file: File,
    options: {
      maxSize?: number
      allowedTypes?: string[]
      allowedExtensions?: string[]
    } = {}
  ): { valid: boolean; error?: string } => {
    const { maxSize, allowedTypes, allowedExtensions } = options

    // Check file size
    if (maxSize && file.size > maxSize) {
      return {
        valid: false,
        error: `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(maxSize)})`
      }
    }

    // Check file type
    if (allowedTypes && allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type "${file.type}" is not allowed. Allowed types: ${allowedTypes.join(', ')}`
      }
    }

    // Check file extension
    if (allowedExtensions && allowedExtensions.length > 0) {
      const fileExtension = file.name.split('.').pop()?.toLowerCase()
      if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
        return {
          valid: false,
          error: `File extension ".${fileExtension}" is not allowed. Allowed extensions: ${allowedExtensions.join(', ')}`
        }
      }
    }

    return { valid: true }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const createImageThumbnail = (file: File, maxWidth: number = 150, maxHeight: number = 150): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!file.type.startsWith('image/')) {
        reject(new Error('File is not an image'))
        return
      }

      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img
        
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height
            height = maxHeight
          }
        }

        canvas.width = width
        canvas.height = height

        // Draw and export
        ctx?.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', 0.8))
      }

      img.onerror = () => reject(new Error('Failed to load image'))
      img.src = URL.createObjectURL(file)
    })
  }

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      
      reader.onload = (event) => {
        resolve(event.target?.result as string)
      }
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'))
      }
      
      reader.readAsText(file)
    })
  }

  const readFileAsDataURL = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      
      reader.onload = (event) => {
        resolve(event.target?.result as string)
      }
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'))
      }
      
      reader.readAsDataURL(file)
    })
  }

  return {
    uploadProgress,
    isUploading,
    uploadFile,
    uploadMultipleFiles,
    uploadToFrappe,
    validateFile,
    formatFileSize,
    createImageThumbnail,
    readFileAsText,
    readFileAsDataURL
  }
}