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
 * @param {string} selector - 选择器
 * @param {number} timeout - 超时时间（毫秒）
 */
export async function waitAndClick(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { timeout })
  await page.click(selector)
}

/**
 * 等待并填充输入框
 * @param {Page} page - Playwright Page 对象
 * @param {string} selector - 选择器
 * @param {string} value - 填充值
 * @param {number} timeout - 超时时间（毫秒）
 */
export async function waitAndFill(page, selector, value, timeout = 5000) {
  await page.waitForSelector(selector, { timeout })
  await page.fill(selector, value)
}

/**
 * 验证消息提示
 * @param {Page} page - Playwright Page 对象
 * @param {string} message - 期望的消息内容
 * @param {string} type - 消息类型（success/error/warning/info）
 */
export async function verifyMessage(page, message, type = 'success') {
  const messageSelector = `.el-message--${type}`
  await expect(page.locator(messageSelector)).toBeVisible()
  await expect(page.locator(messageSelector)).toContainText(message)
}

/**
 * 创建内容辅助函数
 * @param {Page} page - Playwright Page 对象
 * @param {Object} contentData - 内容数据
 */
export async function createContent(page, contentData) {
  // 点击新建按钮
  await waitAndClick(page, 'button:has-text("新建")')

  // 填写表单
  await waitAndFill(page, 'input[name="title"]', contentData.title)
  await waitAndFill(page, 'textarea[name="content"]', contentData.content)

  // 点击保存
  await waitAndClick(page, 'button:has-text("保存")')

  // 验证成功消息
  await verifyMessage(page, '创建成功')
}

/**
 * 创建定时任务辅助函数
 * @param {Page} page - Playwright Page 对象
 * @param {Object} taskData - 任务数据
 */
export async function createTask(page, taskData) {
  // 点击新建按钮
  await waitAndClick(page, 'button:has-text("新建任务")')

  // 填写表单
  await waitAndFill(page, 'input[name="name"]', taskData.name)
  await waitAndFill(page, 'textarea[name="description"]', taskData.description)

  // 选择执行时间
  await waitAndClick(page, 'input[name="execute_time"]')
  await page.click(`text=${taskData.execute_time}`)

  // 点击保存
  await waitAndClick(page, 'button:has-text("保存")')

  // 验证成功消息
  await verifyMessage(page, '创建成功')
}

/**
 * 验证表格数据
 * @param {Page} page - Playwright Page 对象
 * @param {string} text - 期望在表格中看到的文本
 */
export async function verifyTableData(page, text) {
  const table = page.locator('.el-table__body')
  await expect(table).toContainText(text)
}

/**
 * 选择表格行
 * @param {Page} page - Playwright Page 对象
 * @param {number} count - 要选择的行数
 */
export async function selectTableRows(page, count) {
  const checkboxes = page.locator('.el-table__body .el-checkbox__input').first()
  
  // 等待表格加载
  await page.waitForSelector('.el-table__body .el-checkbox__input', { timeout: 5000 })
  
  const allCheckboxes = page.locator('.el-table__body .el-checkbox__input')
  
  for (let i = 0; i < Math.min(count, await allCheckboxes.count()); i++) {
    await allCheckboxes.nth(i).check()
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
  const maxWait = 10000
  const startTime = Date.now()

  while (Date.now() - startTime < maxWait) {
    const isLoading = await page.locator(loadingSelector).count()
    if (isLoading === 0) {
      return
    }
    await page.waitForTimeout(100)
  }
}

/**
 * 验证页面标题
 * @param {Page} page - Playwright Page 对象
 * @param {string} title - 期望的页面标题
 */
export async function verifyPageTitle(page, title) {
  await expect(page.locator('.page-header h1, .page-title')).toContainText(title)
}

/**
 * 验证字段验证错误
 * @param {Page} page - Playwright Page 对象
 * @param {string} selector - 字段选择器
 * @param {string} value - 输入值
 * @param {Object} options - 选项
 */
export async function verifyFieldValidation(page, selector, value, options = {}) {
  const { shouldShowError = true, errorMessage } = options

  await page.fill(selector, value)
  await page.blur(selector)

  if (shouldShowError) {
    const errorElement = page.locator('.el-form-item__error')
    await expect(errorElement).toBeVisible()

    if (errorMessage) {
      await expect(errorElement).toContainText(errorMessage)
    }
  }
}

/**
 * 验证必填字段
 * @param {Page} page - Playwright Page 对象
 * @param {string} selector - 字段选择器
 */
export async function verifyRequiredField(page, selector) {
  await page.click(selector)
  await page.fill(selector, '')
  await page.blur(selector)

  const errorElement = page.locator('.el-form-item__error')
  await expect(errorElement).toBeVisible()
  await expect(errorElement).toContainText(/必填|不能为空|required/i)
}

/**
 * 验证权限按钮
 * @param {Page} page - Playwright Page 对象
 * @param {string} buttonText - 按钮文本
 * @param {boolean} shouldVisible - 是否应该可见
 */
export async function verifyPermissionButton(page, buttonText, shouldVisible = true) {
  const button = page.locator(`button:has-text("${buttonText}")`)

  if (shouldVisible) {
    await expect(button).toBeVisible()
    await expect(button).toBeEnabled()
  } else {
    await expect(button).not.toBeVisible()
  }
}

/**
 * 验证分页功能
 * @param {Page} page - Playwright Page 对象
 */
export async function verifyPagination(page) {
  const pagination = page.locator('.el-pagination')
  
  if (await pagination.count() > 0) {
    await expect(pagination).toBeVisible()
    
    // 验证分页信息
    const totalCount = page.locator('.el-pagination__total')
    expect(await totalCount.count()).toBeGreaterThan(0)
  }
}

/**
 * 等待消息消失
 * @param {Page} page - Playwright Page 对象
 */
export async function waitForMessageDisappear(page) {
  const messageSelector = '.el-message'
  await page.waitForSelector(messageSelector, { state: 'detached', timeout: 5000 })
}

/**
 * 获取表格行数
 * @param {Page} page - Playwright Page 对象
 * @returns {number} 表格行数
 */
export async function getTableRowCount(page) {
  await page.waitForSelector('.el-table__body tr', { timeout: 5000 })
  return await page.locator('.el-table__body tr').count()
}

/**
 * 验证表格行数变化
 * @param {Page} page - Playwright Page 对象
 * @param {number} expectedCount - 期望的行数
 * @param {string} operation - 操作类型（increase/decrease）
 */
export async function verifyTableRowCountChange(page, expectedCount, operation = 'decrease') {
  const currentCount = await getTableRowCount(page)

  if (operation === 'decrease') {
    expect(currentCount).toBeLessThan(expectedCount)
  } else if (operation === 'increase') {
    expect(currentCount).toBeGreaterThan(expectedCount)
  } else {
    expect(currentCount).toBe(expectedCount)
  }
}
