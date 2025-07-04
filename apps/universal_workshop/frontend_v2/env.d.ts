/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Frappe global declarations
declare global {
  interface Window {
    frappe: {
      boot: {
        feature_flags?: Record<string, boolean>
        user: {
          name: string
          full_name: string
          roles: string[]
        }
        lang: string
      }
      call: (args: {
        method: string
        args?: Record<string, any>
        callback?: (response: any) => void
        error?: (error: any) => void
      }) => Promise<any>
      msgprint: (message: string, title?: string) => void
      throw: (message: string) => void
      ui: {
        form: any
        toolbar: any
      }
      model: {
        get_doc: (doctype: string, name: string) => any
        set_value: (doctype: string, name: string, field: string, value: any) => void
      }
    }
  }
}

// Environment variables
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_ENABLE_DEVTOOLS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

export {}