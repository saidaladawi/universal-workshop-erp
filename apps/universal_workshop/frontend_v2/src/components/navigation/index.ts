/**
 * Navigation Components - Universal Workshop Frontend V2
 * 
 * Navigation components for app structure and user guidance including
 * breadcrumbs, tabs, and sidebar with Arabic/RTL support.
 */

// Import components
import Breadcrumb from './Breadcrumb.vue'
import Tabs from './Tabs.vue'
import Sidebar from './Sidebar.vue'
import SidebarMenu from './SidebarMenu.vue'
import SidebarMenuContent from './SidebarMenuContent.vue'
import SidebarMenuChevron from './SidebarMenuChevron.vue'

// Export components
export { 
  Breadcrumb, 
  Tabs, 
  Sidebar, 
  SidebarMenu, 
  SidebarMenuContent, 
  SidebarMenuChevron 
}

// Export component types
export type { BreadcrumbProps, BreadcrumbItem } from './Breadcrumb.vue'
export type { TabsProps, Tab } from './Tabs.vue'
export type { SidebarProps, SidebarUser, SidebarMenuItem } from './Sidebar.vue'
export type { SidebarMenuProps } from './SidebarMenu.vue'
export type { SidebarMenuContentProps } from './SidebarMenuContent.vue'
export type { SidebarMenuChevronProps } from './SidebarMenuChevron.vue'

// Component registry for global registration
export const navigationComponents = {
  UWBreadcrumb: Breadcrumb,
  UWTabs: Tabs,
  UWSidebar: Sidebar,
  UWSidebarMenu: SidebarMenu,
  UWSidebarMenuContent: SidebarMenuContent,
  UWSidebarMenuChevron: SidebarMenuChevron,
} as const

// Install function for Vue plugin
export function installNavigationComponents(app: any) {
  Object.entries(navigationComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  Breadcrumb,
  Tabs,
  Sidebar,
  SidebarMenu,
  SidebarMenuContent,
  SidebarMenuChevron,
  install: installNavigationComponents,
}