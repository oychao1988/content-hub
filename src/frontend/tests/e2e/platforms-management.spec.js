/**
 * 平台管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 平台列表正常加载
 * 2. 添加新平台
 * 3. 编辑平台配置
 * 4. 启用/禁用平台
 * 5. 删除平台
 * 6. 平台配置验证
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('平台管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('平台列表正常加载', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/平台管理|平台列表|Platforms/')).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('添加新平台', async ({ page }) => {
    await page.goto('/platforms')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await waitAndFill(page, 'input[placeholder*="名称"]', 'E2E测试平台')
    await waitAndFill(page, 'input[placeholder*="标识"]', 'e2e_test_platform')
    await waitAndFill(page, 'textarea[placeholder*="描述"]', '测试平台描述')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
    await verifyTableData(page, 'E2E测试平台')
  })

  test('编辑平台配置', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    const nameInput = page.locator('input[placeholder*="名称"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试平台-已配置')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('启用/禁用平台', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const statusSwitch = page.locator('.el-table__row:first-child .el-switch').first()
    if (await statusSwitch.count() > 0) {
      await statusSwitch.click()
      await page.waitForTimeout(500)
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('删除平台', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const deleteButtons = page.locator('.el-table__row button:has-text("删除")')
    const count = await deleteButtons.count()

    if (count > 0) {
      await deleteButtons.first().click()
      await waitAndClick(page, '.el-dialog button:has-text("确定")')
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('平台配置验证', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const configButton = page.locator('.el-table__row:first-child button:has-text("配置"), .el-table__row:first-child button:has-text("设置")')

    if (await configButton.count() > 0) {
      await configButton.click()
      await expect(page.locator('.el-dialog')).toBeVisible()

      // 验证配置表单
      await expect(page.locator('.el-dialog input, .el-dialog textarea, .el-dialog .el-form')).toHaveCount(1)
    }
  })

  test('平台类型筛选', async ({ page }) => {
    await page.goto('/platforms')
    await page.waitForLoadState('networkidle')

    // 查找筛选器
    const filterSelect = page.locator('.el-select').first()
    if (await filterSelect.count() > 0) {
      await filterSelect.click()
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await expect(page.locator('.el-select-dropdown')).toBeVisible()
    }
  })
})
