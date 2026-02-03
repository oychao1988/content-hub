/**
 * 写作风格管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 风格列表正常加载
 * 2. 创建新风格
 * 3. 编辑风格内容
 * 4. 删除风格
 * 5. 风格预览功能
 * 6. 设置默认风格
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('写作风格管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('风格列表正常加载', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/写作风格|风格管理|Styles/')).toBeVisible()
    await expect(page.locator('.el-table, .style-list')).toBeVisible()
  })

  test('创建新风格', async ({ page }) => {
    await page.goto('/writing-styles')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await waitAndFill(page, 'input[placeholder*="名称"]', 'E2E测试风格')
    await waitAndFill(page, 'textarea[placeholder*="描述"]', '这是一个测试风格')
    await waitAndFill(page, 'textarea[placeholder*="内容"]', '# E2E测试风格内容\n\n这是测试内容。')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
    await verifyTableData(page, 'E2E测试风格')
  })

  test('编辑风格内容', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForSelector('.el-table__row, .style-item', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑"), .style-item:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    const nameInput = page.locator('input[placeholder*="名称"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试风格-已编辑')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('删除风格', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForSelector('.el-table__row, .style-item', { timeout: 5000 })

    const deleteButton = page.locator('button:has-text("删除")').first()
    if (await deleteButton.count() > 0) {
      await deleteButton.click()
      await waitAndClick(page, '.el-dialog button:has-text("确定")')
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('风格预览功能', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForSelector('.el-table__row, .style-item', { timeout: 5000 })

    const previewButton = page.locator('button:has-text("预览"), button:has-text("查看")').first()

    if (await previewButton.count() > 0) {
      await previewButton.click()
      await expect(page.locator('.el-dialog')).toBeVisible()

      // 验证预览内容显示
      await expect(page.locator('.el-dialog .preview-content, .el-dialog .style-content')).toBeVisible()
    }
  })

  test('设置默认风格', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForSelector('.el-table__row, .style-item', { timeout: 5000 })

    const defaultButton = page.locator('button:has-text("设为默认"), button:has-text("默认")').first()

    if (await defaultButton.count() > 0) {
      await defaultButton.click()
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('风格搜索筛选', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForLoadState('networkidle')

    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('测试')
      await page.waitForTimeout(500)
      await expect(page.locator('.el-table, .style-list')).toBeVisible()
    }
  })

  test('风格分类管理', async ({ page }) => {
    await page.goto('/writing-styles')
    await page.waitForLoadState('networkidle')

    // 查找分类标签或筛选器
    const categoryTabs = page.locator('.el-tabs__item, .category-filter')
    if (await categoryTabs.count() > 1) {
      await categoryTabs.nth(1).click()
      await page.waitForTimeout(500)
      await expect(page.locator('.el-table, .style-list')).toBeVisible()
    }
  })
})
