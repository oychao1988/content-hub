import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', 'dist', 'build'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.js',
        '**/*.test.ts',
        '**/dist/',
        'src/main.js',
        '**/*.config.js',
        'src/stores/index.js'
      ],
      // 覆盖率阈值
      lines: 50,
      functions: 50,
      branches: 50,
      statements: 50
    },
    // 设置文件
    setupFiles: ['./tests/setup.js']
  }
})
