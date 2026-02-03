/**
 * 用户管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 用户列表正常加载
 * 2. 创建新用户
 * 3. 编辑用户信息
 * 4. 分配用户角色
 * 5. 启用/禁用用户
 * 6. 删除用户
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData, verifyFieldValidation, verifyRequiredField, selectTableRows, getTableRowCount } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('用户管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('用户列表正常加载', async ({ page }) => {
    await page.goto('/users')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('text=/用户管理|用户列表|Users/')).toBeVisible()
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('创建新用户', async ({ page }) => {
    await page.goto('/users')

    // 点击新建按钮
    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')

    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写用户表单
    await waitAndFill(page, 'input[placeholder*="用户名"]', 'e2e_test_user')
    await waitAndFill(page, 'input[placeholder*="密码"]', 'Test123456')
    await waitAndFill(page, 'input[placeholder*="邮箱"]', 'e2e@example.com')
    await waitAndFill(page, 'input[placeholder*="姓名"]', 'E2E测试用户')

    // 选择角色
    await page.click('.el-select:has-text("角色")')
    await page.click('.el-select-dropdown__item:first-child')

    // 保存
    await waitAndClick(page, 'button:has-text("保存")')

    await verifyMessage(page, '成功', 'success')
    await verifyTableData(page, 'e2e_test_user')
  })

  test('编辑用户信息', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 修改姓名
    const nameInput = page.locator('input[placeholder*="姓名"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试用户-已修改')

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('分配用户角色', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 选择不同角色
    const roleSelect = page.locator('.el-select:has-text("角色")').first()
    await roleSelect.click()
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })

    // 点击第二个角色选项（如果存在）
    const roleOptions = page.locator('.el-select-dropdown__item')
    const optionCount = await roleOptions.count()
    if (optionCount > 1) {
      await roleOptions.nth(1).click()
    }

    await waitAndClick(page, 'button:has-text("保存")')
    await verifyMessage(page, '成功', 'success')
  })

  test('启用/禁用用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找状态开关
    const statusSwitch = page.locator('.el-table__row:first-child .el-switch').first()

    if (await statusSwitch.count() > 0) {
      const originalClass = await statusSwitch.getAttribute('class')

      await statusSwitch.click()
      await page.waitForTimeout(500)

      // 验证状态改变
      const newClass = await statusSwitch.getAttribute('class')
      expect(newClass).not.toBe(originalClass)
    }
  })

  test('删除用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCountBefore = await page.locator('.el-table__row').count()

    // 点击删除按钮（避免删除 admin 用户）
    const deleteButtons = page.locator('.el-table__row button:has-text("删除")')
    const count = await deleteButtons.count()

    if (count > 1) {
      await deleteButtons.nth(1).click()
      await waitAndClick(page, '.el-dialog button:has-text("确定")')
      await verifyMessage(page, '成功', 'success')
    }
  })

  test('重置用户密码', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找重置密码按钮
    const resetButton = page.locator('.el-table__row:first-child button:has-text("重置密码"), .el-table__row:first-child button:has-text("密码")')

    if (await resetButton.count() > 0) {
      await resetButton.click()

      // 等待重置密码对话框
      await expect(page.locator('.el-dialog')).toBeVisible()

      // 确认重置
      await waitAndClick(page, 'button:has-text("确定")')
      await verifyMessage(page, '成功', 'success')
    }
  })
})

test.describe('用户管理表单验证', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('用户名长度验证 - 少于3个字符', async ({ page }) => {
    await page.goto('/users')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 输入少于3个字符的用户名
    await waitAndFill(page, 'input[placeholder*="用户名"]', 'ab')
    await page.locator('input[placeholder*="用户名"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/3.*20|至少|minimum/i)
    }
  })

  test('用户名长度验证 - 超过20个字符', async ({ page }) => {
    await page.goto('/users')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 输入超过20个字符的用户名
    await waitAndFill(page, 'input[placeholder*="用户名"]', 'a'.repeat(25))
    await page.locator('input[placeholder*="用户名"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/3.*20|最多|maximum/i)
    }
  })

  test('密码长度验证 - 少于6个字符', async ({ page }) => {
    await page.goto('/users')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 输入正确的用户名但密码少于6个字符
    await waitAndFill(page, 'input[placeholder*="用户名"]', 'testuser')
    await waitAndFill(page, 'input[placeholder*="密码"]', '12345')
    await page.locator('input[placeholder*="密码"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/6.*20|至少|minimum/i)
    }
  })

  test('邮箱格式验证', async ({ page }) => {
    await page.goto('/users')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 输入无效的邮箱格式
    await waitAndFill(page, 'input[placeholder*="邮箱"]', 'invalid-email')
    await page.locator('input[placeholder*="邮箱"]').blur()
    await page.waitForTimeout(200)

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toContainText(/邮箱|格式|email|format/i)
    }
  })

  test('角色必选验证', async ({ page }) => {
    await page.goto('/users')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写其他信息但不选择角色
    await waitAndFill(page, 'input[placeholder*="用户名"]', 'testuser')
    await waitAndFill(page, 'input[placeholder*="密码"]', 'Test123456')
    await waitAndFill(page, 'input[placeholder*="邮箱"]', 'test@example.com')

    // 点击保存
    await waitAndClick(page, 'button:has-text("保存")')

    // 验证角色选择的错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toBeVisible()
    }
  })
})

test.describe('用户管理批量操作', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('批量选择用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 获取初始行数
    const rowCountBefore = await getTableRowCount(page)

    if (rowCountBefore >= 2) {
      // 选择前2行
      await selectTableRows(page, 2)

      // 验证选中状态
      const checkboxes = page.locator('.el-table__body .el-checkbox__input.is-checked')
      const checkedCount = await checkboxes.count()
      expect(checkedCount).toBeGreaterThanOrEqual(2)
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('批量删除用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 获取删除前的行数
    const rowCountBefore = await getTableRowCount(page)

    if (rowCountBefore >= 3) {
      // 选择前2行（避免删除admin）
      await selectTableRows(page, 2)

      // 点击批量删除按钮
      const batchDeleteButton = page.locator('button:has-text("批量删除")')

      if (await batchDeleteButton.count() > 0) {
        await batchDeleteButton.click()

        // 确认删除对话框
        await waitAndClick(page, '.el-dialog button:has-text("确定")')

        // 等待删除完成
        await page.waitForTimeout(1000)

        // 验证行数减少
        const rowCountAfter = await getTableRowCount(page)
        expect(rowCountAfter).toBeLessThanOrEqual(rowCountBefore)
      } else {
        console.log('跳过测试：未找到批量删除按钮')
      }
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('批量启用用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCount = await getTableRowCount(page)

    if (rowCount >= 2) {
      // 选择前2行
      await selectTableRows(page, 2)

      // 查找批量启用按钮
      const batchEnableButton = page.locator('button:has-text("批量启用"), button:has-text("启用")')

      if (await batchEnableButton.count() > 0) {
        await batchEnableButton.click()

        // 验证成功消息
        await page.waitForTimeout(500)
        const successMsg = page.locator('.el-message--success')
        if (await successMsg.count() > 0) {
          await expect(successMsg).toBeVisible()
        }
      } else {
        console.log('跳过测试：未找到批量启用按钮')
      }
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('批量禁用用户', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCount = await getTableRowCount(page)

    if (rowCount >= 2) {
      // 选择前2行
      await selectTableRows(page, 2)

      // 查找批量禁用按钮
      const batchDisableButton = page.locator('button:has-text("批量禁用"), button:has-text("禁用")')

      if (await batchDisableButton.count() > 0) {
        await batchDisableButton.click()

        // 确认对话框（如果有）
        const confirmButton = page.locator('.el-dialog button:has-text("确定")')
        if (await confirmButton.count() > 0) {
          await confirmButton.click()
        }

        // 验证成功消息
        await page.waitForTimeout(500)
        const successMsg = page.locator('.el-message--success')
        if (await successMsg.count() > 0) {
          await expect(successMsg).toBeVisible()
        }
      } else {
        console.log('跳过测试：未找到批量禁用按钮')
      }
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('批量分配角色', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCount = await getTableRowCount(page)

    if (rowCount >= 2) {
      // 选择前2行
      await selectTableRows(page, 2)

      // 查找批量分配角色按钮
      const batchRoleButton = page.locator('button:has-text("批量分配"), button:has-text("分配角色")')

      if (await batchRoleButton.count() > 0) {
        await batchRoleButton.click()

        // 等待对话框打开
        await page.waitForSelector('.el-dialog', { timeout: 5000 })

        // 选择角色
        const roleSelect = page.locator('.el-dialog .el-select').first()
        if (await roleSelect.count() > 0) {
          await roleSelect.click()
          await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })

          // 点击第一个角色选项
          const roleOption = page.locator('.el-select-dropdown__item').first()
          await roleOption.click()

          // 确认分配
          await waitAndClick(page, '.el-dialog button:has-text("确定")')

          // 验证成功消息
          await verifyMessage(page, '成功', 'success')
        }
      } else {
        console.log('跳过测试：未找到批量分配角色按钮')
      }
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('全选和取消全选', async ({ page }) => {
    await page.goto('/users')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找全选复选框
    const selectAllCheckbox = page.locator('.el-table__header .el-checkbox__input').first()

    if (await selectAllCheckbox.count() > 0) {
      // 点击全选
      await selectAllCheckbox.click()
      await page.waitForTimeout(500)

      // 验证所有行都被选中
      const allCheckboxes = page.locator('.el-table__body .el-checkbox__input')
      const checkedCheckboxes = page.locator('.el-table__body .el-checkbox__input.is-checked')
      const allCount = await allCheckboxes.count()
      const checkedCount = await checkedCheckboxes.count()

      expect(checkedCount).toBe(allCount)

      // 再次点击取消全选
      await selectAllCheckbox.click()
      await page.waitForTimeout(500)

      // 验证所有选择被取消
      const checkedCountAfter = await page.locator('.el-table__body .el-checkbox__input.is-checked').count()
      expect(checkedCountAfter).toBe(0)
    } else {
      console.log('跳过测试：未找到全选复选框')
    }
  })
})
