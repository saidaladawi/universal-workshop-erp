<!--
  Avatar Component - Universal Workshop Frontend V2
  
  A flexible avatar component that supports images, initials, icons, and fallbacks.
  Includes Arabic name support and accessibility features.
-->

<template>
  <div
    :class="avatarClasses"
    :style="avatarStyles"
    :aria-label="ariaLabel || getDisplayName()"
    role="img"
  >
    <!-- Image avatar -->
    <img
      v-if="!imageError && (src || user?.avatar)"
      :src="src || user?.avatar"
      :alt="alt || getDisplayName()"
      class="avatar-image"
      @error="handleImageError"
      @load="handleImageLoad"
    />
    
    <!-- Initials fallback -->
    <span
      v-else-if="showInitials"
      class="avatar-initials"
      :style="initialsStyles"
    >
      {{ getInitials() }}
    </span>
    
    <!-- Icon fallback -->
    <UWIcon
      v-else-if="icon"
      :name="icon"
      :size="iconSize"
      class="avatar-icon"
    />
    
    <!-- Default user icon -->
    <UWIcon
      v-else
      name="user"
      :size="iconSize"
      class="avatar-icon avatar-icon--default"
    />
    
    <!-- Status indicator -->
    <div
      v-if="status"
      :class="statusClasses"
      :aria-label="`Status: ${status}`"
    />
    
    <!-- Badge overlay -->
    <div
      v-if="badge || $slots.badge"
      class="avatar-badge"
    >
      <slot name="badge">
        <UWBadge
          v-if="badge"
          v-bind="badge"
          size="xs"
          shape="pill"
        />
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import UWIcon from '../Icon/Icon.vue'
import UWBadge from '../Badge/Badge.vue'
import type { BadgeProps } from '../Badge/Badge.vue'

// User interface for convenience
export interface User {
  id?: string
  name?: string
  nameAr?: string
  email?: string
  avatar?: string
  initials?: string
}

// Define component props
export interface AvatarProps {
  /** User object */
  user?: User
  /** Image source URL */
  src?: string
  /** Image alt text */
  alt?: string
  /** Avatar size */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | number | string
  /** Avatar shape */
  shape?: 'circle' | 'square' | 'rounded'
  /** Icon name for icon avatar */
  icon?: string
  /** Custom initials */
  initials?: string
  /** User status */
  status?: 'online' | 'offline' | 'away' | 'busy' | 'dnd'
  /** Badge configuration */
  badge?: BadgeProps
  /** Show initials fallback */
  showInitials?: boolean
  /** Custom background color */
  backgroundColor?: string
  /** Custom text color */
  textColor?: string
  /** ARIA label */
  ariaLabel?: string
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface AvatarEmits {
  imageLoad: [event: Event]
  imageError: [event: Event]
  click: [event: MouseEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<AvatarProps>(), {
  size: 'md',
  shape: 'circle',
  showInitials: true,
})

// Setup emits
const emit = defineEmits<AvatarEmits>()

// Reactive state
const imageError = ref(false)
const imageLoaded = ref(false)

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Size mappings
const sizeMap = {
  xs: { width: '1.5rem', height: '1.5rem', fontSize: '0.625rem', iconSize: 'xs' as const },
  sm: { width: '2rem', height: '2rem', fontSize: '0.75rem', iconSize: 'sm' as const },
  md: { width: '2.5rem', height: '2.5rem', fontSize: '0.875rem', iconSize: 'md' as const },
  lg: { width: '3rem', height: '3rem', fontSize: '1rem', iconSize: 'lg' as const },
  xl: { width: '4rem', height: '4rem', fontSize: '1.25rem', iconSize: 'xl' as const },
  '2xl': { width: '5rem', height: '5rem', fontSize: '1.5rem', iconSize: '2xl' as const },
}

// Computed properties
const currentSize = computed(() => {
  if (typeof props.size === 'string' && props.size in sizeMap) {
    return sizeMap[props.size as keyof typeof sizeMap]
  }
  
  // Custom size
  const customSize = typeof props.size === 'number' ? `${props.size}px` : props.size
  return {
    width: customSize,
    height: customSize,
    fontSize: '0.875rem',
    iconSize: 'md' as const
  }
})

const iconSize = computed(() => currentSize.value.iconSize)

// Get display name
const getDisplayName = (): string => {
  if (props.user) {
    if (isRTL.value && props.user.nameAr) {
      return props.user.nameAr
    }
    return props.user.name || props.user.email || 'User'
  }
  return props.alt || 'Avatar'
}

// Generate initials
const getInitials = (): string => {
  if (props.initials) {
    return props.initials.substring(0, 2).toUpperCase()
  }
  
  if (props.user?.initials) {
    return props.user.initials.substring(0, 2).toUpperCase()
  }
  
  const name = getDisplayName()
  
  // Handle Arabic names
  if (isRTL.value && props.user?.nameAr) {
    const arabicWords = props.user.nameAr.trim().split(/\s+/)
    if (arabicWords.length >= 2) {
      return arabicWords[0].charAt(0) + arabicWords[1].charAt(0)
    }
    return arabicWords[0].substring(0, 2)
  }
  
  // Handle English names
  const words = name.trim().split(/\s+/)
  if (words.length >= 2) {
    return words[0].charAt(0).toUpperCase() + words[1].charAt(0).toUpperCase()
  }
  
  return name.substring(0, 2).toUpperCase()
}

// Generate background color from name
const generateBackgroundColor = (): string => {
  if (props.backgroundColor) return props.backgroundColor
  
  const colors = [
    'var(--color-red-500)',
    'var(--color-orange-500)',
    'var(--color-yellow-500)',
    'var(--color-green-500)',
    'var(--color-blue-500)',
    'var(--color-indigo-500)',
    'var(--color-purple-500)',
    'var(--color-pink-500)',
  ]
  
  const name = getDisplayName()
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  return colors[Math.abs(hash) % colors.length]
}

// Computed classes
const avatarClasses = computed(() => [
  'uw-avatar',
  `uw-avatar--${typeof props.size === 'string' && props.size in sizeMap ? props.size : 'custom'}`,
  `uw-avatar--${props.shape}`,
  {
    'uw-avatar--has-image': !imageError.value && (props.src || props.user?.avatar),
    'uw-avatar--image-loaded': imageLoaded.value,
    'uw-avatar--has-status': props.status,
    'uw-avatar--has-badge': props.badge || this.$slots.badge,
    'uw-avatar--rtl': isRTL.value,
  },
  props.class,
])

const statusClasses = computed(() => [
  'avatar-status',
  `avatar-status--${props.status}`,
])

// Computed styles
const avatarStyles = computed(() => {
  const styles: Record<string, string> = {
    width: currentSize.value.width,
    height: currentSize.value.height,
  }
  
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})

const initialsStyles = computed(() => ({
  backgroundColor: generateBackgroundColor(),
  color: props.textColor || 'var(--color-neutral-white)',
  fontSize: currentSize.value.fontSize,
}))

// Event handlers
const handleImageError = (event: Event) => {
  imageError.value = true
  imageLoaded.value = false
  emit('imageError', event)
}

const handleImageLoad = (event: Event) => {
  imageError.value = false
  imageLoaded.value = true
  emit('imageLoad', event)
}

const handleClick = (event: MouseEvent) => {
  emit('click', event)
}
</script>

<script lang="ts">
export default {
  name: 'UWAvatar'
}
</script>

<style lang="scss" scoped>
.uw-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  background-color: var(--color-neutral-200);
  color: var(--color-neutral-600);
  font-weight: var(--font-weight-medium);
  text-align: center;
  user-select: none;
  overflow: hidden;
  
  // Smooth transitions
  transition: var(--transition-colors);
  
  // Shape variants
  &--circle {
    border-radius: 50%;
  }
  
  &--square {
    border-radius: 0;
  }
  
  &--rounded {
    border-radius: var(--radius-md);
  }
  
  // Image handling
  &--has-image {
    background-color: var(--color-neutral-100);
  }
  
  &--image-loaded {
    .avatar-image {
      opacity: 1;
    }
  }
  
  // Interactive states
  &:hover {
    transform: scale(1.05);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

// Avatar image
.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.2s ease;
}

// Avatar initials
.avatar-initials {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-weight: var(--font-weight-semibold);
  line-height: 1;
}

// Avatar icon
.avatar-icon {
  color: currentColor;
  
  &--default {
    color: var(--color-neutral-500);
  }
}

// Status indicator
.avatar-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 25%;
  height: 25%;
  min-width: 8px;
  min-height: 8px;
  border: 2px solid var(--color-background);
  border-radius: 50%;
  
  .uw-avatar--rtl & {
    right: auto;
    left: 0;
  }
  
  &--online {
    background-color: var(--color-success);
  }
  
  &--offline {
    background-color: var(--color-neutral-400);
  }
  
  &--away {
    background-color: var(--color-warning);
  }
  
  &--busy,
  &--dnd {
    background-color: var(--color-error);
  }
}

// Badge overlay
.avatar-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  z-index: 1;
  
  .uw-avatar--rtl & {
    right: auto;
    left: -4px;
  }
}

// Size variants
.uw-avatar--xs {
  .avatar-status {
    width: 6px;
    height: 6px;
    border-width: 1px;
  }
  
  .avatar-badge {
    top: -2px;
    right: -2px;
    
    .uw-avatar--rtl & {
      right: auto;
      left: -2px;
    }
  }
}

.uw-avatar--sm {
  .avatar-status {
    width: 8px;
    height: 8px;
    border-width: 1px;
  }
  
  .avatar-badge {
    top: -2px;
    right: -2px;
    
    .uw-avatar--rtl & {
      right: auto;
      left: -2px;
    }
  }
}

.uw-avatar--lg,
.uw-avatar--xl,
.uw-avatar--2xl {
  .avatar-status {
    border-width: 3px;
  }
  
  .avatar-badge {
    top: -6px;
    right: -6px;
    
    .uw-avatar--rtl & {
      right: auto;
      left: -6px;
    }
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-avatar {
    border: 2px solid var(--color-border);
  }
  
  .avatar-status {
    border-width: 3px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-avatar {
    transition: none;
    
    &:hover {
      transform: none;
    }
  }
  
  .avatar-image {
    transition: none;
    opacity: 1;
  }
}

// Print styles
@media print {
  .uw-avatar {
    background: white !important;
    border: 1px solid black !important;
  }
  
  .avatar-image {
    opacity: 1 !important;
  }
  
  .avatar-status,
  .avatar-badge {
    display: none !important;
  }
}
</style>