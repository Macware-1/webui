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
  base: './'
})