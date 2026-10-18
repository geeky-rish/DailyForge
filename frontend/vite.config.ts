import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_URL || (process.env.NODE_ENV === 'production' ? '/DailyForge/' : '/'),
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/ready': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
  },
});
