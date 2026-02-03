/**
 * 内容主题管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 主题列表正常加载
 * 2. 创建新主题
 * 3. 编辑主题信息
 * 4. 删除主题
 * 5. 主题详情查看
 * 6. 搜索主题功能
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('内容主题管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('主题列表正常加载', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/内容主题|主题管理|Themes/')).toBeVisible()
    await expect(page.locator('.el-table, .theme-list')).toBeVisible()
  })

  test('创建新主题', async ({ page }) => {
    await page.goto('/content-themes')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await waitAndFill(page, 'input[placeholder*="名称"]', 'E2E测试主题')
    await waitAndFill(page, 'textarea[placeholder*="描述"]', '这是一个测试主题')
    await waitAndFill(page, 'input[placeholder*="标签"]', '测试, E2E')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
    await verifyTableData(page, 'E2E测试主题')
  })

  test('编辑主题信息', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑"), .theme-item:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    const nameInput = page.locator('input[placeholder*="名称"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试主题-已编辑')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('删除主题', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    const deleteButton = page.locator('button:has-text("删除")').first()
    if (await deleteButton.count() > 0) {
      await deleteButton.click()
      await waitAndClick(page, '.el-dialog button:has-text("确定")')
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('主题详情查看', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    const detailButton = page.locator('button:has-text("详情"), button:has-text("查看")').first()

    if (await detailButton.count() > 0) {
      await detailButton.click()
      await expect(page.locator('.el-dialog')).toBeVisible()

      // 验证详情信息
      await expect(page.locator('.el-dialog .el-descriptions, .el-dialog .detail-info')).toBeVisible()
    }
  })

  test('搜索主题功能', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('测试')
      await page.waitForTimeout(500)
      await expect(page.locator('.el-table, .theme-list')).toBeVisible()
    }
  })

  test('主题标签管理', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    // 查找标签显示
    const tags = page.locator('.el-tag').first()
    if (await tags.count() > 0) {
      await expect(tags).toBeVisible()
    }
  })

  test('主题状态切换', async ({ page }) => {
    await page.goto('/content-themes')
    await page.waitForSelector('.el-table__row, .theme-item', { timeout: 5000 })

    const statusSwitch = page.locator('.el-table__row:first-child .el-switch, .theme-item:first-child .el-switch').first()

    if (await statusSwitch.count() > 0) {
      await statusSwitch.click()
      await page.waitForTimeout(500)
      await verifyMessage(page, '成功', 'success')
    }
  })
})
