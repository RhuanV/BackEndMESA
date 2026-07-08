/**
 * Vite configuration for GeoAvia front-end.
 *
 * - Tailwind CSS v4 via Vite plugin
 * - API proxy to backend to avoid CORS and prevent exposing backend URL to client
 * - Path aliases for clean imports
 */
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
  const apiPort = env.API_PORT || '8000';
  const frontendPort = parseInt(env.FRONTEND_PORT || '5173', 10);

  return {
    plugins: [react(), tailwindcss()],
    envDir: path.resolve(__dirname, '..'),  // Read .env from monorepo root
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: `http://localhost:${apiPort}`,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api/, ''),
        },
      },
    },
  };
});
