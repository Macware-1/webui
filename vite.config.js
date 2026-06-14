import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'

export default defineConfig({
  plugins: [
    vue(),
    viteSingleFile()   // inlines ALL js+css into index.html — single file output
  ],
  build: {
    outDir: 'dist',
    cssCodeSplit: false,
  },
  base: './',
  server: {
    // Forward all /api/* requests to the mock backend (node mocks/server.js)
    proxy: {
      '/api': 'http://localhost:3001'
    }
  }
})
