/**
 * Feedback Components - Universal Workshop Frontend V2
 * 
 * User feedback and notification components for displaying status,
 * alerts, and interactive dialogs with Arabic/RTL support.
 */

// Import components
import Alert from './Alert.vue'
import Toast from './Toast.vue'
import Modal from './Modal.vue'
import Notification from './Notification.vue'

// Export components
export { Alert, Toast, Modal, Notification }

// Export component types
export type { AlertProps, AlertAction } from './Alert.vue'
export type { ToastProps, ToastAction } from './Toast.vue'
export type { ModalProps, ModalAction } from './Modal.vue'
export type { NotificationProps, NotificationAction } from './Notification.vue'

// Component registry for global registration
export const feedbackComponents = {
  UWAlert: Alert,
  UWToast: Toast,
  UWModal: Modal,
  UWNotification: Notification,
} as const

// Install function for Vue plugin
export function installFeedbackComponents(app: any) {
  Object.entries(feedbackComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  Alert,
  Toast,
  Modal,
  Notification,
  install: installFeedbackComponents,
}