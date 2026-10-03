import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Forward Range, If-Range, and other headers needed for seekable
        // video streaming. Without this, Chrome's <video> element cannot
        // perform byte-range requests through the Vite dev proxy and
        // video playback / seeking will silently fail.
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            const rangeHeaders = ['range', 'if-range', 'if-none-match', 'if-modified-since'];
            rangeHeaders.forEach((header) => {
              const value = req.headers[header];
              if (value) {
                proxyReq.setHeader(header, value);
              }
            });
          });
        },
      },
    },
  },
})
