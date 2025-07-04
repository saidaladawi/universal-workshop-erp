/**
 * Core Workshop Type Definitions
 * 
 * Fundamental types for the Universal Workshop ERP system,
 * providing type safety for workshop operations and data structures.
 */

// Workshop Profile and Configuration
export interface WorkshopProfile {
  id: string
  name: string
  nameAr: string
  branding: BrandingConfig
  settings: WorkshopSettings
  location: WorkshopLocation
  contact: ContactInfo
  features: FeatureConfig
}

export interface WorkshopSettings {
  timezone: string
  currency: string
  language: string
  dateFormat: string
  numberFormat: string
  vatRate: number
  vatEnabled: boolean
  multiLocation: boolean
  advancedFeatures: boolean
}

export interface WorkshopLocation {
  address: string
  addressAr: string
  city: string
  region: string
  postalCode: string
  country: string
  coordinates?: {
    lat: number
    lng: number
  }
}

export interface ContactInfo {
  phone: string
  email: string
  website?: string
  fax?: string
  emergencyContact?: string
}

export interface FeatureConfig {
  inventoryManagement: boolean
  customerPortal: boolean
  mobileApp: boolean
  analytics: boolean
  advancedReporting: boolean
  multiCurrency: boolean
  integrations: boolean
}

// Branding System Types
export interface BrandingConfig {
  colors: ColorPalette
  logos: LogoSet
  typography: TypographyConfig
  layout: LayoutConfig
  theme: ThemeConfig
}

export interface ColorPalette {
  primary: string
  secondary: string
  accent: string
  success: string
  warning: string
  error: string
  info: string
  background: string
  surface: string
  onPrimary: string
  onSecondary: string
  onBackground: string
  onSurface: string
  border: string
  divider: string
  shadow: string
}

export interface LogoSet {
  main: string
  light: string
  dark: string
  favicon: string
  mobile: string
  print: string
}

export interface TypographyConfig {
  fontFamily: {
    arabic: string[]
    latin: string[]
  }
  fontSize: {
    xs: string
    sm: string
    base: string
    lg: string
    xl: string
    '2xl': string
    '3xl': string
    '4xl': string
  }
  fontWeight: {
    light: number
    normal: number
    medium: number
    semibold: number
    bold: number
  }
  lineHeight: {
    tight: number
    normal: number
    relaxed: number
  }
}

export interface LayoutConfig {
  sidebar: {
    width: string
    collapsible: boolean
    position: 'left' | 'right'
  }
  header: {
    height: string
    fixed: boolean
    transparent: boolean
  }
  content: {
    maxWidth: string
    padding: string
    centered: boolean
  }
}

export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto'
  highContrast: boolean
  animations: boolean
  reducedMotion: boolean
  compactMode: boolean
}

// User and Session Types
export interface User {
  id: string
  email: string
  fullName: string
  fullNameAr?: string
  roles: string[]
  permissions: Permission[]
  preferences: UserPreferences
  avatar?: string
  lastLogin?: Date
  isActive: boolean
}

export interface Permission {
  doctype: string
  action: 'read' | 'write' | 'create' | 'delete' | 'submit' | 'cancel'
  allowed: boolean
  conditions?: Record<string, any>
}

export interface UserPreferences {
  language: string
  timezone: string
  dateFormat: string
  theme: 'light' | 'dark' | 'auto'
  notifications: NotificationPreferences
  dashboard: DashboardPreferences
}

export interface NotificationPreferences {
  email: boolean
  sms: boolean
  push: boolean
  inApp: boolean
  frequency: 'immediate' | 'hourly' | 'daily' | 'weekly'
}

export interface DashboardPreferences {
  widgets: string[]
  layout: 'grid' | 'list'
  refreshInterval: number
  defaultFilters: Record<string, any>
}

// Session Management Types
export interface SessionConfig {
  timeout: number
  warningTime: number
  extendable: boolean
  multiDevice: boolean
  securityLevel: 'basic' | 'enhanced' | 'strict'
}

export interface SessionInfo {
  id: string
  userId: string
  deviceInfo: DeviceInfo
  location?: GeolocationInfo
  startTime: Date
  lastActivity: Date
  expiresAt: Date
  isActive: boolean
}

export interface DeviceInfo {
  type: 'desktop' | 'mobile' | 'tablet'
  browser: string
  os: string
  screenResolution: string
  userAgent: string
}

export interface GeolocationInfo {
  lat: number
  lng: number
  accuracy: number
  city?: string
  country?: string
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errors?: ApiError[]
  meta?: ResponseMeta
}

export interface ApiError {
  code: string
  message: string
  field?: string
  details?: Record<string, any>
}

export interface ResponseMeta {
  total?: number
  page?: number
  pageSize?: number
  hasMore?: boolean
  executionTime?: number
}

// Utility Types
export type Direction = 'ltr' | 'rtl'
export type Language = 'en' | 'ar'
export type Currency = 'OMR' | 'USD' | 'EUR' | 'SAR' | 'AED'
export type Status = 'active' | 'inactive' | 'pending' | 'suspended'

// Form and Validation Types
export interface FormField {
  name: string
  label: string
  labelAr?: string
  type: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'textarea' | 'checkbox' | 'radio'
  required?: boolean
  placeholder?: string
  placeholderAr?: string
  validation?: ValidationRule[]
  options?: SelectOption[]
  defaultValue?: any
  disabled?: boolean
  readonly?: boolean
  direction?: Direction
  autoDetect?: boolean
}

export interface ValidationRule {
  type: 'required' | 'email' | 'minLength' | 'maxLength' | 'pattern' | 'custom'
  value?: any
  message: string
  messageAr?: string
}

export interface SelectOption {
  value: any
  label: string
  labelAr?: string
  disabled?: boolean
  group?: string
}

// Event Types
export interface WorkshopEvent {
  type: string
  data: any
  timestamp: Date
  source: string
  userId?: string
}

export interface EventHandler<T = any> {
  (event: WorkshopEvent & { data: T }): void | Promise<void>
}

// Feature Flag Types
export interface FeatureFlags {
  newBranding: boolean
  newArabicUtils: boolean
  newMobileInterface: boolean
  newAnalytics: boolean
  newCustomerPortal: boolean
  advancedSearch: boolean
  realTimeUpdates: boolean
  offlineMode: boolean
}

// Note: This file contains only type definitions, no runtime exports needed