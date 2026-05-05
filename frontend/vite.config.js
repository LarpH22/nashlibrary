import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/',
  plugins: [react()],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'esbuild',
    target: 'esnext'
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
      '/users': 'http://localhost:5000',
      '/books': 'http://localhost:5000',
      '/fines': 'http://localhost:5000',
      '/uploads': 'http://localhost:5000'
    }
  },
  css: {
    preprocessorOptions: {
      css: {
        charset: false
      }
    }
  }
})
