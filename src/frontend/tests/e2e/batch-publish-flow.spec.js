/**
 * 批量发布完整流程 E2E 测试
 *
 * 测试场景：
 * 1. 选择多个内容 → 添加到发布池 → 批量发布
 * 2. 验证发布结果和日志
 * 3. 验证发布池管理功能
 */

import { test, expect } from '@playwright/test'
import { login, logout, verifyMessage, verifyTableData, selectTableRows } from './helpers/test-helpers'
import { testUsers, testContent } from './helpers/test-data'

test.describe('批量发布完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前登录
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    // 每个测试后登出
    await logout(page)
  })

  test('批量发布流程：选择内容 → 添加到发布池 → 发布', async ({ page }) => {
    // 步骤 1: 导航到内容管理页面
    await page.goto('/content')

    // 等待内容列表加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 步骤 2: 选择多个内容进行批量操作
    // 选择前3个内容
    const checkboxes = page.locator('.el-table__body .el-checkbox__input').first()
    const checkboxCount = await page.locator('.el-table__body .el-checkbox__input').count()

    if (checkboxCount >= 3) {
      for (let i = 0; i < Math.min(3, checkboxCount); i++) {
        await page.locator('.el-table__body .el-checkbox__input').nth(i).click()
      }

      // 步骤 3: 批量添加到发布池
      await page.click('button:has-text("批量操作")')
      await page.click('li:has-text("添加到发布池")')

      // 选择发布平台和账号
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // 选择平台
      await page.click('.el-select:has-text("选择平台")')
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await page.click('.el-select-dropdown__item:first-child')

      // 选择账号
      await page.click('.el-checkbox:has-text("微信")')

      // 确认添加
      await page.click('button:has-text("确定")')

      // 验证添加成功
      await verifyMessage(page, '添加成功', 'success')

      // 步骤 4: 导航到发布池
      await page.goto('/publish-pool')

      // 等待发布池列表加载
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 验证内容已添加到发布池
      await expect(page.locator('.el-table__row')).toHaveCount(3)

      // 步骤 5: 批量发布
      // 选择所有内容
      await page.click('.el-table__header .el-checkbox__input')

      // 点击批量发布按钮
      await page.click('button:has-text("批量发布")')

      // 确认发布对话框
      await page.waitForSelector('.el-dialog', { timeout: 5000 })
      await page.click('button:has-text("确定")')

      // 验证发布开始（可能需要mock外部API）
      await verifyMessage(page, '发布任务已创建', 'success')
    }
  })

  test('单个内容发布流程', async ({ page }) => {
    // 步骤 1: 导航到内容管理
    await page.goto('/content')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 步骤 2: 选择第一个内容
    const firstRow = page.locator('.el-table__row').first()
    await firstRow.locator('.el-checkbox__input').click()

    // 步骤 3: 添加到发布池
    await page.click('button:has-text("批量操作")')
    await page.click('li:has-text("添加到发布池")')

    // 配置发布参数
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.click('.el-select:has-text("选择平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    await page.click('.el-checkbox:has-text("微信")')
    await page.click('button:has-text("确定")')

    await verifyMessage(page, '添加成功', 'success')

    // 步骤 4: 导航到发布池并发布
    await page.goto('/publish-pool')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 点击发布按钮
    await page.locator('.el-table__row').first().locator('button:has-text("发布")').click()

    // 验证发布对话框
    await page.waitForSelector('.el-dialog', { timeout: 5000 })
    await expect(page.locator('text=/发布|确认/')).toBeVisible()
  })

  test('发布池优先级调整', async ({ page }) => {
    // 导航到发布池
    await page.goto('/publish-pool')

    // 等待发布池列表加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 如果有内容，测试优先级调整
    const rowCount = await page.locator('.el-table__row').count()

    if (rowCount > 0) {
      // 点击第一行的优先级调整按钮
      await page.locator('.el-table__row').first()
        .locator('button:has-text("优先级")')
        .click()

      // 等待对话框打开
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // 调整优先级
      await page.click('button:has-text("提高")')

      // 保存
      await page.click('button:has-text("确定")')

      // 验证调整成功
      await verifyMessage(page, '优先级调整成功', 'success')
    }
  })

  test('发布池内容移除', async ({ page }) => {
    // 先添加内容到发布池（如果发布池为空）
    await page.goto('/content')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    const checkboxCount = await page.locator('.el-table__body .el-checkbox__input').count()

    if (checkboxCount > 0) {
      // 选择第一个内容
      await page.locator('.el-table__body .el-checkbox__input').first().click()

      // 添加到发布池
      await page.click('button:has-text("批量操作")')
      await page.click('li:has-text("添加到发布池")')

      await page.waitForSelector('.el-dialog', { timeout: 5000 })
      await page.click('.el-select:has-text("选择平台")')
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await page.click('.el-select-dropdown__item:first-child')
      await page.click('.el-checkbox:has-text("微信")')
      await page.click('button:has-text("确定")')

      await verifyMessage(page, '添加成功', 'success')

      // 导航到发布池
      await page.goto('/publish-pool')
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 移除内容
      await page.locator('.el-table__row').first()
        .locator('button:has-text("移除")')
        .click()

      // 确认移除
      await page.click('.el-dialog button:has-text("确定")')

      // 验证移除成功
      await verifyMessage(page, '移除成功', 'success')
    }
  })

  test('发布历史查询', async ({ page }) => {
    // 导航到发布管理页面
    await page.goto('/publisher')

    // 等待发布历史加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 验证发布历史表格显示
    await expect(page.locator('.el-table')).toBeVisible()

    // 测试搜索功能
    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    await searchInput.fill('测试')
    await page.keyboard.press('Enter')

    // 等待搜索结果
    await page.waitForTimeout(1000)

    // 测试状态过滤
    await page.click('.el-tabs__item:has-text("已发布")')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 测试日期过滤
    await page.click('.el-date-editor')
    await page.waitForSelector('.el-picker-panel', { timeout: 3000 })
    await page.click('button:has-text("今天")')
  })

  test('发布状态流转', async ({ page }) => {
    // 导航到发布池
    await page.goto('/publish-pool')

    // 等待列表加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 查看不同状态的内容
    const statuses = ['待发布', '发布中', '已发布', '发布失败']

    for (const status of statuses) {
      // 点击状态标签
      const statusTab = page.locator(`.el-tabs__item:has-text("${status}")`)
      if (await statusTab.isVisible()) {
        await statusTab.click()
        await page.waitForTimeout(500)

        // 验证该状态的内容显示
        const rows = page.locator('.el-table__row')
        const count = await rows.count()

        if (count > 0) {
          await expect(rows.first()).toBeVisible()
        }
      }
    }
  })

  test('批量删除发布池内容', async ({ page }) => {
    // 导航到发布池
    await page.goto('/publish-pool')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    const rowCount = await page.locator('.el-table__row').count()

    if (rowCount >= 2) {
      // 选择多个内容
      await page.locator('.el-table__body .el-checkbox__input').nth(0).click()
      await page.locator('.el-table__body .el-checkbox__input').nth(1).click()

      // 批量删除
      await page.click('button:has-text("批量删除")')

      // 确认删除
      await page.click('.el-dialog button:has-text("确定")')

      // 验证删除成功
      await verifyMessage(page, '删除成功', 'success')
    }
  })
})
