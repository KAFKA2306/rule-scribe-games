import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build trigger: 2025-12-06-v2
export default defineConfig({
  envDir: '..',
  plugins: [react()],
  envPrefix: ['VITE_', 'NEXT_'],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
