/**
 * Workshop Management Components - Universal Workshop Frontend V2
 * 
 * Specialized components for automotive workshop management system
 * with comprehensive Arabic/RTL support and workshop-specific functionality.
 */

// Import components
export { default as UWServiceOrderCard } from './ServiceOrderCard.vue'
export { default as UWVehicleDetailsCard } from './VehicleDetailsCard.vue'
export { default as UWTechnicianAssignment } from './TechnicianAssignment.vue'
export { default as UWWorkshopDashboard } from './WorkshopDashboard.vue'
export { default as UWServiceBayStatus } from './ServiceBayStatus.vue'
export { default as UWPartsInventoryWidget } from './PartsInventoryWidget.vue'

// Export component types
export type { ServiceOrderCardProps, ServiceOrderCardEmits } from './ServiceOrderCard.vue'
export type { VehicleDetailsCardProps, VehicleDetailsCardEmits } from './VehicleDetailsCard.vue'
export type { TechnicianAssignmentProps, TechnicianAssignmentEmits } from './TechnicianAssignment.vue'
export type { WorkshopDashboardProps, WorkshopDashboardEmits } from './WorkshopDashboard.vue'
export type { ServiceBayStatusProps, ServiceBayStatusEmits } from './ServiceBayStatus.vue'
export type { PartsInventoryWidgetProps, PartsInventoryWidgetEmits } from './PartsInventoryWidget.vue'

// Component registry for global registration
export const workshopComponents = {
  UWServiceOrderCard: () => import('./ServiceOrderCard.vue'),
  UWVehicleDetailsCard: () => import('./VehicleDetailsCard.vue'),
  UWTechnicianAssignment: () => import('./TechnicianAssignment.vue'),
  UWWorkshopDashboard: () => import('./WorkshopDashboard.vue'),
  UWServiceBayStatus: () => import('./ServiceBayStatus.vue'),
  UWPartsInventoryWidget: () => import('./PartsInventoryWidget.vue'),
} as const

// Install function for Vue plugin
export function installWorkshopComponents(app: any) {
  Object.entries(workshopComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  install: installWorkshopComponents,
}