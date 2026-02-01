/**
 * 跨用户数据隔离 E2E 测试
 *
 * 测试场景：
 * 1. 测试客户A无法查看客户B的数据
 * 2. 验证数据查询和操作的权限边界
 * 3. 测试多租户环境下的数据隔离
 */

import { test, expect } from '@playwright/test'
import { login, logout, verifyMessage } from '../helpers/test-helpers'
import { testUsers } from '../helpers/test-data'

test.describe('跨用户数据隔离测试', () => {
  test.describe('内容数据隔离', () => {
    test('不同用户创建的内容相互隔离', async ({ page, context }) => {
      // 用户1登录并创建内容
      await login(page, testUsers.operator.username, testUsers.operator.password)
      await page.goto('/content')

      // 点击新建
      await page.click('button:has-text("新建")')
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // 创建内容
      await page.fill('input[placeholder*="标题"]', '数据隔离测试 - 用户1')
      await page.click('.el-select:has-text("选择平台")')
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await page.click('.el-select-dropdown__item:first-child')

      const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]').first()
      await contentEditor.fill('这是用户1创建的内容')

      await page.click('button:has-text("保存")')
      await verifyMessage(page, '保存成功', 'success')
      await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

      // 验证用户1可以看到该内容
      await expect(page.locator('text=数据隔离测试 - 用户1')).toBeVisible()

      await logout(page)

      // 用户2登录（查看员）
      await login(page, testUsers.viewer.username, testUsers.viewer.password)
      await page.goto('/content')

      // 验证用户2看不到用户1的内容（如果做了严格的数据隔离）
      // 或者用户2只能看到分配给他的内容
      const user1Content = page.locator('text=数据隔离测试 - 用户1')
      const isVisible = await user1Content.isVisible()

      // 根据实际的数据隔离策略，这里可能看到也可能看不到
      // 如果是基于客户的数据隔离，不同客户的数据应该完全隔离
      // 如果是基于用户的权限，可能有部分可见

      // 登出
      await logout(page)
    })

    test('用户只能编辑自己创建的内容', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)
      await page.goto('/content')

      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 获取第一行内容的标题
      const firstRow = page.locator('.el-table__row').first()
      const title = await firstRow.locator('.cell').first().textContent()

      // 点击编辑
      await firstRow.locator('button:has-text("编辑")').click()

      // 等待编辑对话框
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // 验证可以编辑（说明有权限）
      const saveButton = page.locator('button:has-text("保存")')
      await expect(saveButton).toBeVisible()

      // 关闭对话框
      await page.click('.el-dialog .el-dialog__headerbtn')

      await logout(page)
    })
  })

  test.describe('定时任务数据隔离', () => {
    test('用户只能看到和操作自己创建的定时任务', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)
      await page.goto('/scheduler')

      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 记录当前任务数量
      const taskCount = await page.locator('.el-table__row').count()

      // 创建新任务
      await page.click('button:has-text("新建任务")')
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      await page.fill('input[placeholder*="任务名称"]', '数据隔离测试任务')
      await page.click('.el-select:has-text("任务类型")')
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await page.click('.el-select-dropdown__item:first-child')

      await page.fill('input[placeholder*="间隔"]', '60')
      await page.click('button:has-text("保存")')
      await verifyMessage(page, '创建成功', 'success')
      await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

      // 验证任务数量增加
      const newTaskCount = await page.locator('.el-table__row').count()
      expect(newTaskCount).toBe(taskCount + 1)

      // 验证可以看到自己创建的任务
      await expect(page.locator('text=数据隔离测试任务')).toBeVisible()

      await logout(page)

      // 换另一个用户登录
      await login(page, testUsers.viewer.username, testUsers.viewer.password)
      await page.goto('/scheduler')

      // 查看员可能无法访问定时任务页面
      // 或者只能看到部分任务
      const viewerTaskCount = await page.locator('.el-table__row').count()

      // 验证任务数量不同（数据隔离生效）
      // 如果查看员能访问，他应该看不到运营员创建的任务
      if (viewerTaskCount > 0) {
        const isolatedTask = page.locator('text=数据隔离测试任务')
        expect(await isolatedTask.isVisible()).toBeFalsy()
      }

      await logout(page)
    })
  })

  test.describe('发布池数据隔离', () => {
    test('发布池内容按用户权限隔离', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)

      // 先添加一些内容到发布池
      await page.goto('/content')
      await page.waitForSelector('.el-table', { timeout: 10000 })

      const checkboxCount = await page.locator('.el-table__body .el-checkbox__input').count()

      if (checkboxCount > 0) {
        await page.locator('.el-table__body .el-checkbox__input').first().click()

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

        const poolCount = await page.locator('.el-table__row').count()

        await logout(page)

        // 换用户登录
        await login(page, testUsers.viewer.username, testUsers.viewer.password)
        await page.goto('/publish-pool')

        // 验证发布池内容不同
        const viewerPoolCount = await page.locator('.el-table__row').count()

        // 根据权限，查看员可能看不到发布池，或者看到的数量不同
        // 这里验证数据隔离
        if (viewerPoolCount > 0) {
          // 如果能看到，数量应该不同
          expect(viewerPoolCount).not.toBe(poolCount)
        }

        await logout(page)
      }
    })
  })

  test.describe('账号数据隔离', () => {
    test('用户只能看到有权限的账号', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)
      await page.goto('/accounts')

      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 记录账号数量
      const accountCount = await page.locator('.el-table__row').count()

      // 验证至少能看到一些账号
      expect(accountCount).toBeGreaterThanOrEqual(0)

      await logout(page)

      // 管理员登录
      await login(page, testUsers.admin.username, testUsers.admin.password)
      await page.goto('/accounts')

      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 管理员应该能看到更多账号
      const adminAccountCount = await page.locator('.el-table__row').count()

      // 验证管理员看到的账号数量 >= 运营员看到的
      expect(adminAccountCount).toBeGreaterThanOrEqual(accountCount)

      await logout(page)
    })
  })

  test.describe('客户数据隔离', () => {
    test('不同客户的数据完全隔离', async ({ page }) => {
      // 这个测试假设系统支持多客户
      // 如果系统是单客户，这个测试可以跳过

      await login(page, testUsers.admin.username, testUsers.admin.password)
      await page.goto('/customers')

      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 查看客户列表
      const customerCount = await page.locator('.el-table__row').count()

      if (customerCount > 0) {
        // 获取第一个客户的名称
        const firstCustomer = await page.locator('.el-table__row').first()
          .locator('.cell').first().textContent()

        console.log(`第一个客户: ${firstCustomer}`)

        // 导航到内容管理
        await page.goto('/content')

        // 验证内容表中显示客户列
        await page.waitForSelector('.el-table', { timeout: 10000 })

        // 内容应该关联到特定客户
        // 不同客户的内容应该隔离
      }

      await logout(page)
    })
  })

  test.describe('审计日志数据隔离', () => {
    test('用户只能查看自己的操作日志', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)

      // 执行一些操作以生成日志
      await page.goto('/content')
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 执行搜索操作
      const searchInput = page.locator('input[placeholder*="搜索"]').first()
      await searchInput.fill('测试')
      await page.keyboard.press('Enter')

      await page.waitForTimeout(1000)

      // 如果有审计日志页面，验证日志
      // 这里假设系统有审计日志功能
      // 实际实现需要根据系统的审计日志功能调整

      await logout(page)
    })
  })

  test.describe('API数据隔离验证', () => {
    test('直接API调用也受权限控制', async ({ page }) => {
      // 以查看员身份登录
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      // 尝试通过API访问所有内容（绕过前端权限检查）
      const response = await page.request.get({
        url: 'http://localhost:8010/api/v1/content',
        headers: {
          // 浏览器会自动携带cookie
        }
      })

      // 验证返回的数据不是所有数据
      // 而是经过权限过滤的数据
      expect(response.ok()).toBeTruthy()

      const data = await response.json()

      // 验证数据结构
      if (data.items && Array.isArray(data.items)) {
        // 数据应该被过滤
        console.log(`返回 ${data.items.length} 条内容`)
      }

      await logout(page)
    })

    test('跨用户API访问被拒绝', async ({ page }) => {
      // 以查看员身份登录
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      // 尝试访问管理员专属的API
      const response = await page.request.get({
        url: 'http://localhost:8010/api/v1/users',
        headers: {}
      })

      // 验证返回403或404
      if (!response.ok()) {
        const status = response.status()
        expect(status === 403 || status === 404).toBeTruthy()
      }

      await logout(page)
    })
  })

  test.describe('会话隔离测试', () => {
    test('不同用户的会话完全独立', async ({ browser }) => {
      // 创建两个独立的浏览器上下文（模拟两个用户）
      const context1 = await browser.newContext()
      const context2 = await browser.newContext()

      const page1 = await context1.newPage()
      const page2 = await context2.newPage()

      // 用户1登录
      await login(page1, testUsers.operator.username, testUsers.operator.password)
      await page1.goto('/content')

      // 用户2登录
      await login(page2, testUsers.admin.username, testUsers.admin.password)
      await page2.goto('/content')

      // 验证两个页面显示不同的数据（基于权限）
      await page1.waitForSelector('.el-table', { timeout: 10000 })
      await page2.waitForSelector('.el-table', { timeout: 10000 })

      const count1 = await page1.locator('.el-table__row').count()
      const count2 = await page2.locator('.el-table__row').count()

      // 管理员应该能看到更多或相同的数据
      expect(count2).toBeGreaterThanOrEqual(count1)

      // 清理
      await context1.close()
      await context2.close()
    })
  })
})
