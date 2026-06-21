import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE_URL || 'http://localhost:8001'

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        '/auth': { target: apiTarget, changeOrigin: true },
        '/users': { target: apiTarget, changeOrigin: true },
        '/employees': { target: apiTarget, changeOrigin: true },
        '/departments': { target: apiTarget, changeOrigin: true },
        '/attendance': { target: apiTarget, changeOrigin: true },
        '/payroll': { target: apiTarget, changeOrigin: true },
        '/dashboard': { target: apiTarget, changeOrigin: true },
        '/leaves': { target: apiTarget, changeOrigin: true },
        '/health': { target: apiTarget, changeOrigin: true },
      },
    },
  }
})
