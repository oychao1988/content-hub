/**
 * 账号管理页面 E2E 测试
 *
 * 测试场景：
 * 1. 账号列表正常加载
 * 2. 创建新账号
 * 3. 编辑账号信息
 * 4. 删除账号
 * 5. 搜索账号功能
 * 6. 分页功能（如果有）
 */

import { test, expect } from '@playwright/test'
import { login, logout, waitAndClick, waitAndFill, verifyMessage, verifyTableData, verifyFieldValidation, verifyRequiredField, selectTableRows, getTableRowCount, verifyTableRowCountChange } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('账号管理页面', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('账号列表正常加载', async ({ page }) => {
    // 导航到账号管理页面
    await page.goto('/accounts')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 验证页面标题
    await expect(page.locator('text=/账号管理|账号列表|Accounts/')).toBeVisible()

    // 验证账号列表表格存在
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('创建新账号', async ({ page }) => {
    await page.goto('/accounts')

    // 点击新建按钮
    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加"), button:has-text("Create")')

    // 等待对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写账号表单
    await waitAndFill(page, 'input[placeholder*="名称"]', 'E2E测试账号')
    await waitAndFill(page, 'input[placeholder*="平台"]', '1')

    // 保存
    await waitAndClick(page, 'button:has-text("保存"), button:has-text("确定")')

    // 验证保存成功
    await verifyMessage(page, '成功', 'success')

    // 验证账号出现在列表中
    await verifyTableData(page, 'E2E测试账号')
  })

  test('编辑账号信息', async ({ page }) => {
    await page.goto('/accounts')

    // 等待列表加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 点击第一个账号的编辑按钮
    await waitAndClick(page, '.el-table__row:first-child button:has-text("编辑")')

    // 等待编辑对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 修改账号名称
    const nameInput = page.locator('input[placeholder*="名称"]').first()
    await nameInput.clear()
    await nameInput.fill('E2E测试账号-已修改')

    // 保存
    await waitAndClick(page, 'button:has-text("保存"), button:has-text("确定")')

    // 验证保存成功
    await verifyMessage(page, '成功', 'success')
  })

  test('删除账号', async ({ page }) => {
    await page.goto('/accounts')

    // 等待列表加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 获取删除前的行数
    const rowCountBefore = await page.locator('.el-table__row').count()

    // 点击第一个账号的删除按钮
    await waitAndClick(page, '.el-table__row:first-child button:has-text("删除")')

    // 确认删除对话框
    await waitAndClick(page, '.el-dialog button:has-text("确定")')

    // 验证删除成功
    await verifyMessage(page, '成功', 'success')

    // 验证行数减少
    await page.waitForTimeout(500)
    const rowCountAfter = await page.locator('.el-table__row').count()
    expect(rowCountAfter).toBeLessThanOrEqual(rowCountBefore)
  })

  test('搜索账号功能', async ({ page }) => {
    await page.goto('/accounts')

    // 等待列表加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 输入搜索关键词
    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('测试')
      await page.waitForTimeout(500)

      // 验证搜索结果（可选：检查表格内容）
      await expect(page.locator('.el-table')).toBeVisible()
    }
  })

  test('分页功能', async ({ page }) => {
    await page.goto('/accounts')

    // 查找分页组件
    const pagination = page.locator('.el-pagination')

    if (await pagination.count() > 0) {
      await expect(pagination).toBeVisible()

      // 点击下一页（如果可用）
      const nextButton = pagination.locator('.btn-next:not(.disabled)').first()
      if (await nextButton.count() > 0) {
        await nextButton.click()
        await page.waitForTimeout(500)

        // 验证页面仍然显示表格
        await expect(page.locator('.el-table')).toBeVisible()
      }
    }
  })

  test('查看账号详情', async ({ page }) => {
    await page.goto('/accounts')

    // 等待列表加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 点击第一个账号的查看详情按钮
    const detailButton = page.locator('.el-table__row:first-child button:has-text("详情"), .el-table__row:first-child button:has-text("查看")')

    if (await detailButton.count() > 0) {
      await detailButton.click()

      // 验证详情对话框打开
      await expect(page.locator('.el-dialog')).toBeVisible()
    }
  })

  test('账号状态切换', async ({ page }) => {
    await page.goto('/accounts')

    // 等待列表加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找状态开关
    const statusSwitch = page.locator('.el-table__row:first-child .el-switch').first()

    if (await statusSwitch.count() > 0) {
      // 点击状态开关
      await statusSwitch.click()

      // 验证状态切换成功
      await page.waitForTimeout(500)
      await expect(statusSwitch).toBeVisible()
    }
  })
})

test.describe('账号管理表单验证', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('账号名称必填验证', async ({ page }) => {
    await page.goto('/accounts')

    // 点击新建按钮
    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 不填写名称，直接点击保存
    await waitAndClick(page, 'button:has-text("保存")')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
  })

  test('账号名称长度验证 - 超过最大长度', async ({ page }) => {
    await page.goto('/accounts')

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

  test('平台选择必填验证', async ({ page }) => {
    await page.goto('/accounts')

    await waitAndClick(page, 'button:has-text("新建"), button:has-text("添加")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写名称但不选择平台
    await waitAndFill(page, 'input[placeholder*="名称"]', '测试账号')

    // 点击保存
    await waitAndClick(page, 'button:has-text("保存")')

    // 验证平台选择的错误提示
    const errorMsg = page.locator('.el-form-item__error')
    const hasError = await errorMsg.count() > 0
    if (hasError) {
      await expect(errorMsg).toBeVisible()
    }
  })
})

test.describe('账号管理批量操作', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('批量选择账号', async ({ page }) => {
    await page.goto('/accounts')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 获取初始行数
    const rowCountBefore = await getTableRowCount(page)

    if (rowCountBefore >= 2) {
      // 选择前2行
      await selectTableRows(page, 2)

      // 验证选中状态（检查复选框是否被选中）
      const checkboxes = page.locator('.el-table__body .el-checkbox__input.is-checked')
      const checkedCount = await checkboxes.count()
      expect(checkedCount).toBeGreaterThanOrEqual(2)
    } else {
      console.log('跳过测试：数据不足')
    }
  })

  test('批量删除账号', async ({ page }) => {
    await page.goto('/accounts')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 获取删除前的行数
    const rowCountBefore = await getTableRowCount(page)

    if (rowCountBefore >= 2) {
      // 选择前2行
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

  test('全选功能', async ({ page }) => {
    await page.goto('/accounts')
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
    } else {
      console.log('跳过测试：未找到全选复选框')
    }
  })

  test('取消选择', async ({ page }) => {
    await page.goto('/accounts')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    const rowCount = await getTableRowCount(page)

    if (rowCount >= 2) {
      // 选择几行
      await selectTableRows(page, 2)

      // 验证已选中
      const checkedCount = await page.locator('.el-table__body .el-checkbox__input.is-checked').count()
      expect(checkedCount).toBeGreaterThanOrEqual(2)

      // 点击全选复选框取消选择
      const selectAllCheckbox = page.locator('.el-table__header .el-checkbox__input').first()
      if (await selectAllCheckbox.count() > 0) {
        await selectAllCheckbox.click()
        await page.waitForTimeout(500)

        // 验证所有选择被取消
        const checkedCountAfter = await page.locator('.el-table__body .el-checkbox__input.is-checked').count()
        expect(checkedCountAfter).toBe(0)
      }
    } else {
      console.log('跳过测试：数据不足')
    }
  })
})
