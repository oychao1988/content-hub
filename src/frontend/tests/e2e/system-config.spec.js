/**
 * 系统配置页面 E2E 测试
 *
 * 测试场景：
 * 1. 配置页面正常加载
 * 2. 查看系统配置
 * 3. 修改系统配置
 * 4. 保存配置
 * 5. 配置生效验证
 * 6. 配置重置功能
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('系统配置页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('配置页面正常加载', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/系统配置|配置|Config/')).toBeVisible()
    await expect(page.locator('.el-form, .config-panel')).toBeVisible()
  })

  test('查看系统配置', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    // 验证配置项存在
    const formItems = page.locator('.el-form-item')
    const count = await formItems.count()

    expect(count).toBeGreaterThan(0)
  })

  test('修改系统配置', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    // 查找可编辑的配置项
    const textInputs = page.locator('.el-form-item input[type="text"], .el-form-item textarea')
    const inputCount = await textInputs.count()

    if (inputCount > 0) {
      const firstInput = textInputs.first()
      const originalValue = await firstInput.inputValue()

      // 修改值
      await firstInput.fill('测试配置值')

      // 验证值已修改
      const newValue = await firstInput.inputValue()
      expect(newValue).toBe('测试配置值')
    }
  })

  test('保存配置', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    // 修改一个配置项
    const textInputs = page.locator('.el-form-item input[type="text"]').first()
    if (await textInputs.count() > 0) {
      await textInputs.fill('测试保存')
    }

    // 点击保存按钮
    const saveButton = page.locator('button:has-text("保存"), button:has-text("提交")')
    if (await saveButton.count() > 0) {
      await saveButton.click()
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('配置生效验证', async ({ page }) => {
    await page.goto('/config')

    // 修改配置
    const testInput = page.locator('.el-form-item input').first()
    if (await testInput.count() > 0) {
      await testInput.fill('配置生效测试')

      // 保存
      await waitAndClick(page, 'button:has-text("保存")')
      await page.waitForTimeout(1000)

      // 刷新页面
      await page.reload()
      await page.waitForLoadState('networkidle')

      // 验证配置已保存
      await expect(testInput).toHaveValue('配置生效测试')
    }
  })

  test('配置重置功能', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    const resetButton = page.locator('button:has-text("重置"), button:has-text("Reset")')

    if (await resetButton.count() > 0) {
      // 先修改一个值
      const testInput = page.locator('.el-form-item input').first()
      if (await testInput.count() > 0) {
        const originalValue = await testInput.inputValue()
        await testInput.fill('临时值')

        // 点击重置
        await resetButton.click()

        // 验证恢复原值
        const resetValue = await testInput.inputValue()
        expect(resetValue).toBe(originalValue)
      }
    }
  })

  test('配置分类标签切换', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    // 查找配置标签页
    const tabs = page.locator('.el-tabs__item')
    const tabCount = await tabs.count()

    if (tabCount > 1) {
      // 点击第二个标签
      await tabs.nth(1).click()
      await page.waitForTimeout(500)

      // 验证内容切换
      await expect(page.locator('.el-tab-pane')).toBeVisible()
    }
  })

  test('配置验证规则', async ({ page }) => {
    await page.goto('/config')
    await page.waitForLoadState('networkidle')

    // 查找必填项
    const requiredInputs = page.locator('.el-form-item.is-required input')

    if (await requiredInputs.count() > 0) {
      const firstRequired = requiredInputs.first()

      // 清空值
      await firstRequired.fill('')

      // 点击保存
      await waitAndClick(page, 'button:has-text("保存")')

      // 验证错误提示
      const errorMessage = page.locator('.el-form-item__error')
      expect(await errorMessage.count()).toBeGreaterThan(0)
    }
  })
})
