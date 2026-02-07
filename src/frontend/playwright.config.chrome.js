import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright 配置文件 - 使用系统 Chrome
 * 用于 E2E 测试的环境和浏览器配置
 */
export default defineConfig({
  testDir: './tests/e2e',

  /* 平行执行测试文件 */
  fullyParallel: false,

  /* 在 CI 环境下失败时不重试 */
  forbidOnly: !!process.env.CI,

  /* 在 CI 环境下重试失败的测试 */
  retries: process.env.CI ? 2 : 0,

  /* 在 CI 环境下使用并行工作线程 */
  workers: process.env.CI ? 1 : 1,

  /* 测试报告配置 */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  /* 全局设置 */
  use: {
    /* 基础 URL */
    baseURL: 'http://localhost:18030',

    /* 追踪设置（失败时保留追踪） */
    trace: 'on-first-retry',

    /* 截图设置（失败时截图） */
    screenshot: 'only-on-failure',

    /* 视频设置（失败时录制） */
    video: 'retain-on-failure',

    /* 操作超时时间 */
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,
  },

  /* 测试项目配置 - 使用系统 Chrome */
  projects: [
    {
      name: 'chrome-system',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome', // 使用系统安装的 Chrome
        launchOptions: {
          args: ['--start-maximized', '--disable-web-security'],
        },
      },
    },
  ],

  /* 测试开始前启动开发服务器 */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:18030',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
})
