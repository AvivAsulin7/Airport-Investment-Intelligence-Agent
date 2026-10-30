import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Dev only: forward API calls to FastAPI so the browser sees one origin (D-034).
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
