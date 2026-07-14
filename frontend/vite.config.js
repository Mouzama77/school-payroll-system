import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE_URL || 'http://localhost:8000'

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: (() => {
        // Helper that proxies XHR/JSON requests but bypasses HTML navigation
        // so the dev server serves the SPA for direct browser navigation.
        const makeProxy = () => ({
          target: apiTarget,
          changeOrigin: true,
          // If the browser navigation requests HTML, serve the SPA instead of proxying.
          bypass: (req, res, opts) => {
            const accept = req.headers && req.headers.accept
            if (accept && accept.indexOf('text/html') !== -1) {
              return '/index.html'
            }
            return undefined
          },
          // Do NOT rewrite single-segment paths (e.g. '/designations') to add a
          // trailing slash. FastAPI registers these routes without a trailing
          // slash; a rewrite to '/designations/' triggers a 307 redirect to the
          // absolute cross-origin URL 'http://localhost:8000/designations', and
          // browsers drop the Authorization header on that cross-host redirect,
          // causing a 401 + forced logout. Proxying the path unchanged avoids
          // the redirect entirely.
        })

        return {
          '/auth': makeProxy(),
          '/users': makeProxy(),
          '/employees': makeProxy(),
          '/departments': makeProxy(),
          '/designations': makeProxy(),
          '/attendance': makeProxy(),
          '/payroll': makeProxy(),
          '/dashboard': makeProxy(),
          '/academic-calendar': makeProxy(),
          '/overtime': makeProxy(),
          '/leaves': makeProxy(),
          '/audit-logs': makeProxy(),
          '/health': makeProxy(),
        }
      })(),
    },
  }
})
