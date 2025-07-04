/**
 * Layout Components - Universal Workshop Frontend V2
 * 
 * Layout components for organizing content with responsive design
 * and support for various layout patterns.
 */

// Import components
import Container from './Container.vue'
import Grid from './Grid.vue'
import Stack from './Stack.vue'

// Export components
export { Container, Grid, Stack }

// Export component types
export type { ContainerProps } from './Container.vue'
export type { GridProps } from './Grid.vue'
export type { StackProps } from './Stack.vue'

// Component registry for global registration
export const layoutComponents = {
  UWContainer: Container,
  UWGrid: Grid,
  UWStack: Stack,
} as const

// Install function for Vue plugin
export function installLayoutComponents(app: any) {
  Object.entries(layoutComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  Container,
  Grid,
  Stack,
  install: installLayoutComponents,
}