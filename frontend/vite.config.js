import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  envDir: '..',
  plugins: [react()],
  envPrefix: ['VITE_', 'NEXT_'],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

