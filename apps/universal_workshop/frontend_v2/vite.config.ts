import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  
  // Vue configuration for template compilation
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version)
  },

  // Build configuration for integration with Frappe
  root: resolve(__dirname),
  base: '/',

  build: {
    outDir: resolve(__dirname, '../universal_workshop/public/v2'),
    emptyOutDir: false, // Don't delete existing files - safety first

    rollupOptions: {
      // Multiple entry points
      input: {
        main: resolve(__dirname, 'src/main.ts'),
        mobile: resolve(__dirname, 'src/mobile.ts'),
        branding: resolve(__dirname, 'src/branding.ts'),
        analytics: resolve(__dirname, 'src/analytics.ts')
      },

      // Externalize deps that shouldn't be bundled
      external: ['frappe'],

      output: {
        format: 'es',
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',

        // Manual chunk splitting for optimal loading
        manualChunks: {
          vendor: ['vue']
        },

        globals: {
          frappe: 'frappe'
        }
      }
    },

    // Source maps for development
    sourcemap: true,

    // Minimize in production
    minify: 'esbuild',

    // Target modern browsers
    target: 'es2020'
  },

  // CSS configuration
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
          @import "src/styles/base/variables.scss";
          @import "src/styles/base/mixins.scss";
        `
      }
    },

    // CSS modules for component isolation
    modules: {
      localsConvention: 'camelCase',
      generateScopedName: '[name]__[local]___[hash:base64:5]'
    }
  },

  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@modules': resolve(__dirname, 'src/modules'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@styles': resolve(__dirname, 'src/styles'),
      '@branding': resolve(__dirname, 'src/branding'),
      '@localization': resolve(__dirname, 'src/localization'),
      // Fix Vue template compilation
      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },

  // Development server
  server: {
    port: 5173,
    host: true,
    cors: true,

    // Proxy only API calls to Frappe development server
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
      // Removed /assets proxy to serve assets locally
    }
  }
})