/**
 * Vite configuration for GeoAvia front-end.
 *
 * - Tailwind CSS v4 via Vite plugin
 * - API proxy to backend to avoid CORS and prevent exposing backend URL to client
 * - Path aliases for clean imports
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: path.resolve(__dirname, '..'),  // Read .env from monorepo root
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
});
