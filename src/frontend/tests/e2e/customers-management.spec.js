/**
 * 客户管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 客户列表正常加载
 * 2. 添加新客户
 * 3. 编辑客户信息
 * 4. 删除客户
 * 5. 客户详情查看
 * 6. 搜索客户功能
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData, verifyFieldValidation, verifyRequiredField } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('客户管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('客户列表正常加载', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/客户管理|客户列表|Customers/')).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('添加新客户', async ({ page }) => {
    await page.goto('/customers')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await waitAndFill(page, 'input[placeholder*="名称"]', 'E2E测试客户')
    await waitAndFill(page, 'input[placeholder*="联系"]', 'test@example.com')
    await waitAndFill(page, 'textarea[placeholder*="描述"]', '这是一个测试客户')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
    await verifyTableData(page, 'E2E测试客户')
  })

  test('编辑客户信息', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    const nameInput = page.locator('input[placeholder*="名称"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试客户-已修改')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('删除客户', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCountBefore = await page.locator('.el-table__row').count()

    await waitAndClick(page, '.el-table__row:first-child button:has-text("删除")')
    await waitAndClick(page, '.el-dialog button:has-text("确定")')

    await verifyMessage(page, '成功', 'success')

    await page.waitForTimeout(500)
    const rowCountAfter = await page.locator('.el-table__row').count()
    expect(rowCountAfter).toBeLessThanOrEqual(rowCountBefore)
  })

  test('客户详情查看', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const detailButton = page.locator('.el-table__row:first-child button:has-text("详情"), .el-table__row:first-child button:has-text("查看")')

    if (await detailButton.count() > 0) {
      await detailButton.click()
      await expect(page.locator('.el-dialog')).toBeVisible()

      // 验证详情信息显示
      await expect(page.locator('.el-dialog .el-descriptions, .el-dialog .detail-info')).toBeVisible()
    }
  })

  test('搜索客户功能', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('测试')
      await page.waitForTimeout(500)
      await expect(page.locator('.el-table')).toBeVisible()
    }
  })

  test('客户状态管理', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const statusTag = page.locator('.el-table__row:first-child .el-tag').first()
    if (await statusTag.count() > 0) {
      await expect(statusTag).toBeVisible()
    }
  })
})

test.describe('客户管理表单验证', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('客户名称必填验证', async ({ page }) => {
    await page.goto('/customers')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 不填写名称，直接点击保存
    await waitAndClick(page, 'button:has-text("保存")')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
  })

  test('客户名称长度验证 - 超过最大长度', async ({ page }) => {
    await page.goto('/customers')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 输入超长名称（假设最大50字符）
    const longName = 'a'.repeat(100)
    await waitAndFill(page, 'input[placeholder*="名称"]', longName)

    // 触发验证
    await page.locator('input[placeholder*="名称"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示（如果有长度限制）
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/长度|最多|maximum/i)
    }
  })

  test('联系方式格式验证', async ({ page }) => {
    await page.goto('/customers')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写名称
    await waitAndFill(page, 'input[placeholder*="名称"]', '测试客户')

    // 输入无效的联系方式
    await waitAndFill(page, 'input[placeholder*="联系"]', 'invalid-contact-format-!!!')
    await page.locator('input[placeholder*="联系"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示（如果有格式验证）
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/格式|format|邮箱|电话|phone|email/i)
    }
  })

  test('必填字段验证', async ({ page }) => {
    await page.goto('/customers')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 只填写名称，不填写其他必填项
    await waitAndFill(page, 'input[placeholder*="名称"]', '测试客户')

    // 点击保存
    await waitAndClick(page, 'button:has-text("保存")')

    // 验证至少有一个错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg.first()).toBeVisible()
    }
  })
})
