/**
 * E2E 测试辅助函数
 *
 * 提供常用的测试操作和断言
 */

import { expect } from '@playwright/test'

/**
 * 登录辅助函数
 * @param {Page} page - Playwright Page 对象
 * @param {string} username - 用户名
 * @param {string} password - 密码
 */
export async function login(page, username, password) {
  await page.goto('/login')

  // 等待登录表单加载
  await page.waitForSelector('input[placeholder*="用户名"]', { timeout: 5000 })

  // 填写登录表单
  await page.fill('input[placeholder*="用户名"]', username)
  await page.fill('input[type="password"]', password)

  // 点击登录按钮
  await page.click('button[type="submit"]')

  // 等待跳转到仪表板
  await page.waitForURL('/', { timeout: 10000 })

  // 验证登录成功
  await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
}

/**
 * 登出辅助函数
 * @param {Page} page - Playwright Page 对象
 */
export async function logout(page) {
  // 点击用户菜单
  await page.click('.user-dropdown')

  // 点击退出登录
  await page.click('text=/退出登录|Logout/')

  // 等待跳转到登录页
  await page.waitForURL('/login')
}

/**
 * 等待并点击元素
 * @param {Page} page - Playwright Page 对象
 * @param {string} selector - CSS 选择器
 * @param {number} timeout - 超时时间（毫秒）
 */
export async function waitAndClick(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { timeout })
  await page.click(selector)
}

/**
 * 等待并填写表单
 * @param {Page} page - Playwright Page 对象
 * @param {string} selector - CSS 选择器
 * @param {string} value - 填写的值
 * @param {number} timeout - 超时时间（毫秒）
 */
export async function waitAndFill(page, selector, value, timeout = 5000) {
  await page.waitForSelector(selector, { timeout })
  await page.fill(selector, value)
}

/**
 * 等待消息提示并验证内容
 * @param {Page} page - Playwright Page 对象
 * @param {string} message - 期望的消息内容
 * @param {string} type - 消息类型（success, error, warning, info）
 */
export async function verifyMessage(page, message, type = 'success') {
  const messageSelector = `.el-message--${type}`
  await expect(page.locator(messageSelector)).toBeVisible()
  await expect(page.locator(messageSelector)).toContainText(message)
}

/**
 * 创建内容辅助函数
 * @param {Page} page - Playwright Page 对象
 * @param {object} contentData - 内容数据
 */
export async function createContent(page, contentData) {
  // 导航到内容管理页面
  await page.goto('/content')

  // 点击新建按钮
  await waitAndClick(page, 'button:has-text("新建")')

  // 等待对话框打开
  await page.waitForSelector('.el-dialog', { timeout: 5000 })

  // 填写内容表单
  await waitAndFill(page, 'input[placeholder*="标题"]', contentData.title)

  // 选择平台
  if (contentData.platform_id) {
    await page.click('.el-select:has-text("选择平台")')
    await page.click(`.el-select-dropdown__item[data-value="${contentData.platform_id}"]`)
  }

  // 选择主题
  if (contentData.theme_id) {
    await page.click('.el-select:has-text("选择主题")')
    await page.click(`.el-select-dropdown__item[data-value="${contentData.theme_id}"]`)
  }

  // 填写内容
  const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]')
  await contentEditor.fill(contentData.content)

  // 保存
  await page.click('button:has-text("保存")')

  // 等待保存成功
  await verifyMessage(page, '保存成功', 'success')

  // 等待对话框关闭
  await page.waitForSelector('.el-dialog', { state: 'hidden' })
}

/**
 * 创建定时任务辅助函数
 * @param {Page} page - Playwright Page 对象
 * @param {object} taskData - 任务数据
 */
export async function createTask(page, taskData) {
  // 导航到定时任务页面
  await page.goto('/scheduler')

  // 点击新建任务按钮
  await waitAndClick(page, 'button:has-text("新建任务")')

  // 等待对话框打开
  await page.waitForSelector('.el-dialog', { timeout: 5000 })

  // 填写任务表单
  await waitAndFill(page, 'input[placeholder*="任务名称"]', taskData.name)
  await waitAndFill(page, 'textarea[placeholder*="描述"]', taskData.description)

  // 选择任务类型
  await page.click('.el-select:has-text("任务类型")')
  await page.click(`.el-select-dropdown__item:has-text("${taskData.task_type}")`)

  // 设置间隔
  await page.fill('input[placeholder*="间隔"]', taskData.interval.toString())
  await page.click('.el-select:has-text("时间单位")')
  await page.click(`.el-select-dropdown__item:has-text("${taskData.interval_unit}")`)

  // 保存
  await page.click('button:has-text("保存")')

  // 等待保存成功
  await verifyMessage(page, '创建成功', 'success')
}

/**
 * 验证表格数据
 * @param {Page} page - Playwright Page 对象
 * @param {string} text - 期望在表格中找到的文本
 */
export async function verifyTableData(page, text) {
  const tableRow = page.locator(`.el-table__row:has-text("${text}")`)
  await expect(tableRow).toBeVisible()
}

/**
 * 批量选择表格行
 * @param {Page} page - Playwright Page 对象
 * @param {number} count - 要选择的行数
 */
export async function selectTableRows(page, count) {
  const checkboxes = page.locator('.el-table__body .el-checkbox__input').first(count)
  for (let i = 0; i < count; i++) {
    await checkboxes.nth(i).click()
  }
}

/**
 * 截图辅助函数（用于调试）
 * @param {Page} page - Playwright Page 对象
 * @param {string} name - 截图名称
 */
export async function takeScreenshot(page, name) {
  await page.screenshot({ path: `screenshots/${name}.png`, fullPage: true })
}

/**
 * 等待加载完成
 * @param {Page} page - Playwright Page 对象
 */
export async function waitForLoading(page) {
  const loadingSelector = '.el-loading-mask'
  if (await page.locator(loadingSelector).count() > 0) {
    await page.waitForSelector(loadingSelector, { state: 'hidden', timeout: 10000 })
  }
}

/**
 * 获取表格行数
 * @param {Page} page - Playwright Page 对象
 * @returns {number} 表格行数
 */
export async function getTableRowCount(page) {
  return await page.locator('.el-table__body .el-table__row').count()
}

/**
 * 验证页面标题
 * @param {Page} page - Playwright Page 对象
 * @param {string} title - 期望的页面标题
 */
export async function verifyPageTitle(page, title) {
  await expect(page.locator('.page-header h1, .page-title').first()).toContainText(title)
}
