/**
 * E2E 测试全局设置
 *
 * 在所有测试运行前执行
 */

import { fullCoverage } from 'playwright-coveralls'

async function globalSetup(config) {
  console.log('🚀 Starting E2E tests global setup...')

  // 这里可以执行一些全局设置，例如：
  // 1. 初始化测试数据库
  // 2. 准备测试数据
  // 3. 启动mock服务器

  console.log('✅ E2E tests global setup completed')
}

export default globalSetup
