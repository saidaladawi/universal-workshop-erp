/**
 * Base Components - Universal Workshop Frontend V2
 * 
 * Core component primitives that form the foundation of the design system.
 * These components provide consistent styling and behavior patterns.
 */

// Import components
import Button from './Button.vue'
import Input from './Input.vue'
import Card from './Card.vue'

// Export components
export { Button, Input, Card }

// Export component types
export type { ButtonProps, ButtonEmits } from './Button.vue'
export type { InputProps, InputEmits } from './Input.vue'
export type { CardProps, CardEmits } from './Card.vue'

// Component registry for global registration
export const baseComponents = {
  UWButton: Button,
  UWInput: Input,
  UWCard: Card,
} as const

// Install function for Vue plugin
export function installBaseComponents(app: any) {
  Object.entries(baseComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  Button,
  Input,
  Card,
  install: installBaseComponents,
}