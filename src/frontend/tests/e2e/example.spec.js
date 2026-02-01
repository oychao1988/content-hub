/**
 * E2E 测试示例
 *
 * 这是一个简单的示例测试，帮助开发者快速上手 Playwright E2E 测试
 */

import { test, expect } from '@playwright/test'
import { login, logout } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('E2E 测试示例', () => {
  // 在每个测试前执行
  test.beforeEach(async ({ page }) => {
    console.log('开始测试...')
  })

  // 在每个测试后执行
  test.afterEach(async ({ page }) => {
    console.log('测试结束')
  })

  // 在所有测试前执行（仅在第一个测试前）
  test.beforeAll(async () => {
    console.log('准备测试环境...')
  })

  // 在所有测试后执行（仅在最后一个测试后）
  test.afterAll(async () => {
    console.log('清理测试环境...')
  })

  test('示例 1: 页面导航', async ({ page }) => {
    // 导航到登录页
    await page.goto('/login')

    // 验证页面标题
    await expect(page).toHaveTitle(/ContentHub/)

    // 验证某个元素存在
    await expect(page.locator('input[type="text"]')).toBeVisible()
  })

  test('示例 2: 表单填写和提交', async ({ page }) => {
    // 使用辅助函数登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 导航到某个页面
    await page.goto('/content')

    // 等待元素加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 验证当前URL
    await expect(page).toHaveURL('http://localhost:3010/content')

    // 登出
    await logout(page)
  })

  test('示例 3: 元素交互', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)

    await page.goto('/content')

    // 点击按钮
    await page.click('button:has-text("新建")')

    // 等待对话框出现
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写输入框
    await page.fill('input[placeholder*="标题"]', '测试内容')

    // 选择下拉选项
    await page.click('.el-select')
    await page.click('.el-select-dropdown__item:first-child')

    // 关闭对话框
    await page.click('.el-dialog__headerbtn')

    await logout(page)
  })

  test('示例 4: 列表和表格操作', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)

    await page.goto('/content')

    // 等待表格加载
    await page.waitForSelector('.el-table')

    // 获取行数
    const rowCount = await page.locator('.el-table__row').count()
    console.log(`表格有 ${rowCount} 行`)

    // 如果有数据，操作第一行
    if (rowCount > 0) {
      const firstRow = page.locator('.el-table__row').first()

      // 获取第一行的文本
      const rowText = await firstRow.textContent()
      console.log(`第一行内容: ${rowText}`)

      // 点击第一行的某个按钮
      await firstRow.locator('button').first().click()
    }

    await logout(page)
  })

  test('示例 5: 等待和重试', async ({ page }) => {
    await page.goto('/')

    // 等待元素出现
    await page.waitForSelector('text=仪表盘', { timeout: 5000 })

    // 等待导航完成
    await page.waitForURL('**/')

    // 等待特定条件
    await page.waitForFunction(() => {
      return document.title.includes('ContentHub')
    })

    // 等待网络请求完成
    // await page.waitForResponse('**/api/v1/**')
  })

  test('示例 6: 截图和调试', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)

    await page.goto('/content')

    // 截取整页截图
    await page.screenshot({
      path: 'test-results/content-page.png',
      fullPage: true
    })

    // 截取单个元素
    const table = page.locator('.el-table').first()
    await table.screenshot({
      path: 'test-results/table.png'
    })

    await logout(page)
  })

  test('示例 7: 断言和验证', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)

    await page.goto('/content')

    // 验证元素可见
    await expect(page.locator('.el-table')).toBeVisible()

    // 验证元素包含文本
    await expect(page.locator('h1')).toContainText('内容')

    // 验证元素数量
    await expect(page.locator('.el-table__row')).toHaveCount(await page.locator('.el-table__row').count())

    // 验证属性
    await expect(page.locator('button')).toHaveAttribute('type', 'submit')

    // 验证CSS类
    await expect(page.locator('.el-button')).toHaveClass(/el-button/)

    await logout(page)
  })

  test('示例 8: 处理对话框和弹窗', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)

    await page.goto('/content')

    // 点击打开对话框
    await page.click('button:has-text("新建")')

    // 等待对话框
    await page.waitForSelector('.el-dialog')

    // 在对话框中操作
    await page.fill('input[placeholder*="标题"]', '测试对话框')

    // 处理确认对话框
    await page.click('button:has-text("取消")')

    // 处理alert/confirm对话框
    page.on('dialog', dialog => {
      console.log(`对话框消息: ${dialog.message()}`)
      dialog.accept() // 或 dialog.dismiss()
    })

    await logout(page)
  })

  test('示例 9: API请求测试', async ({ page }) => {
    // 登录获取token
    const loginResponse = await page.request.post({
      url: 'http://localhost:8010/api/v1/auth/login',
      data: {
        username: testUsers.admin.username,
        password: testUsers.admin.password
      }
    })

    expect(loginResponse.ok()).toBeTruthy()

    const loginData = await loginResponse.json()
    console.log('登录响应:', loginData)

    // 使用token进行API调用
    const contentResponse = await page.request.get({
      url: 'http://localhost:8010/api/v1/content',
      headers: {
        'Authorization': `Bearer ${loginData.access_token}`
      }
    })

    expect(contentResponse.ok()).toBeTruthy()

    const contentData = await contentResponse.json()
    console.log('内容列表:', contentData)
  })

  test('示例 10: 多标签页和多窗口', async ({ context }) => {
    // 创建新的标签页
    const page1 = await context.newPage()
    await page1.goto('/content')

    const page2 = await context.newPage()
    await page2.goto('/scheduler')

    // 在两个标签页之间切换
    await page1.bringToFront()
    await expect(page1).toHaveURL('**/content')

    await page2.bringToFront()
    await expect(page2).toHaveURL('**/scheduler')

    // 关闭标签页
    await page1.close()
    await page2.close()
  })
})

/**
 * Playwright 常用API速查
 *
 * 导航:
 * - page.goto(url) - 导航到URL
 * - page.goBack() - 后退
 * page.goForward() - 前进
 * - page.reload() - 刷新
 *
 * 元素选择器:
 * - page.locator('css-selector') - CSS选择器
 * - page.locator('text=文本') - 文本选择器
 * - page.locator('xpath=//xpath') - XPath选择器
 *
 * 元素操作:
 * - click() - 点击
 * - fill(value) - 填写
 * - selectOption(value) - 选择
 * - check() / uncheck() - 勾选/取消勾选
 * - hover() - 悬停
 * - focus() - 聚焦
 *
 * 断言:
 * - expect(locator).toBeVisible() - 可见
 * - expect(locator).toContainText() - 包含文本
 * - expect(locator).toHaveAttribute() - 有属性
 * - expect(locator).toHaveCount() - 有特定数量
 * - expect(page).toHaveURL() - URL匹配
 *
 * 等待:
 * - waitForSelector() - 等待元素
 * - waitForURL() - 等待URL
 * - waitForTimeout() - 等待时间
 * - waitForFunction() - 等待函数返回true
 *
 * 获取信息:
 * -textContent() - 获取文本
 * - getAttribute() - 获取属性
 * - count() - 获取数量
 * - screenshot() - 截图
 */
