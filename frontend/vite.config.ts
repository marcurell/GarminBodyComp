import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Local dev: proxy API calls to FastAPI running locally
      '/api': {
        target: 'http://localhost:8001',
        rewrite: (path) => path.replace(/^\/api/, ''),
        changeOrigin: true,
      },
      // Local dev: mock SWA auth endpoint
      '/.auth': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
