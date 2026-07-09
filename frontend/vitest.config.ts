import { defineConfig } from 'vitest/config';
import path from 'node:path';

// Unit tests run in a Node environment (pure logic: permissions, zod schemas).
// The '@' alias mirrors tsconfig/vite so imports resolve the same way.
export default defineConfig({
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
