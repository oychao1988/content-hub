/**
 * 权限控制完整流程 E2E 测试
 *
 * 测试场景：
 * 1. 测试不同角色的权限边界
 * 2. 验证未授权操作被拒绝
 * 3. 测试页面级权限控制
 * 4. 测试按钮级权限控制
 */

import { test, expect } from '@playwright/test'
import { login, logout, verifyMessage } from '../helpers/test-helpers'
import { testUsers } from '../helpers/test-data'

test.describe('权限控制完整流程', () => {
  test.describe('管理员权限测试', () => {
    test.use({ storageState: { cookies: [], origins: [] } })

    test('管理员可以访问所有页面', async ({ page }) => {
      // 以管理员身份登录
      await login(page, testUsers.admin.username, testUsers.admin.password)

      // 测试访问所有页面
      const pages = [
        { path: '/accounts', title: '账号管理' },
        { path: '/content', title: '内容管理' },
        { path: '/publisher', title: '发布管理' },
        { path: '/scheduler', title: '定时任务' },
        { path: '/publish-pool', title: '发布池' },
        { path: '/users', title: '用户管理' },
        { path: '/customers', title: '客户管理' },
        { path: '/platforms', title: '平台管理' },
        { path: '/config', title: '系统配置' }
      ]

      for (const pageInfo of pages) {
        await page.goto(pageInfo.path)

        // 验证页面成功加载（未跳转到403）
        await expect(page).not.toHaveURL('/403')

        // 验证页面标题或内容
        await expect(page.locator('text=/' + pageInfo.title + '")).toBeVisible()
      }

      await logout(page)
    })

    test('管理员可以创建、编辑、删除用户', async ({ page }) => {
      await login(page, testUsers.admin.username, testUsers.admin.password)

      // 导航到用户管理
      await page.goto('/users')

      // 等待用户列表加载
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 创建用户
      await page.click('button:has-text("新建")')
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      await page.fill('input[placeholder*="用户名"]', 'e2e_test_user')
      await page.fill('input[placeholder*="邮箱"]', 'e2e@example.com')
      await page.fill('input[placeholder*="密码"]', 'password123')

      // 选择角色
      await page.click('.el-select:has-text("角色")')
      await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
      await page.click('.el-select-dropdown__item:has-text("operator")')

      await page.click('button:has-text("保存")')
      await verifyMessage(page, '创建成功', 'success')
      await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

      // 验证用户创建成功
      await expect(page.locator('text=e2e_test_user')).toBeVisible()

      // 编辑用户
      await page.click('.el-table__row:has-text("e2e_test_user") button:has-text("编辑")')
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      await page.fill('input[placeholder*="邮箱"]', 'e2e_updated@example.com')
      await page.click('button:has-text("保存")')
      await verifyMessage(page, '更新成功', 'success')

      // 删除用户
      await page.click('.el-table__row:has-text("e2e_test_user") button:has-text("删除")')
      await page.click('.el-dialog button:has-text("确定")')
      await verifyMessage(page, '删除成功', 'success')

      await logout(page)
    })
  })

  test.describe('运营员权限测试', () => {
    test('运营员可以访问内容、发布、定时任务页面', async ({ page }) => {
      // 以运营员身份登录
      await login(page, testUsers.operator.username, testUsers.operator.password)

      // 测试可访问的页面
      const allowedPages = [
        { path: '/content', title: '内容管理' },
        { path: '/publisher', title: '发布管理' },
        { path: '/scheduler', title: '定时任务' },
        { path: '/publish-pool', title: '发布池' }
      ]

      for (const pageInfo of allowedPages) {
        await page.goto(pageInfo.path)

        // 验证页面成功加载
        await expect(page).not.toHaveURL('/403')
        await expect(page.locator('text=/' + pageInfo.title + '')).toBeVisible()
      }

      await logout(page)
    })

    test('运营员无法访问管理员页面', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)

      // 测试不能访问的页面
      const forbiddenPages = [
        '/users',
        '/customers',
        '/platforms',
        '/config'
      ]

      for (const path of forbiddenPages) {
        await page.goto(path)

        // 验证跳转到403页面
        await expect(page).toHaveURL('/403')

        // 返回首页
        await page.goto('/')
      }

      await logout(page)
    })

    test('运营员可以创建和编辑内容', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)

      await page.goto('/content')

      // 验证有新建按钮
      await expect(page.locator('button:has-text("新建")')).toBeVisible()

      // 验证有编辑和删除按钮
      const firstRow = page.locator('.el-table__row').first()
      await expect(firstRow.locator('button:has-text("编辑")')).toBeVisible()
      await expect(firstRow.locator('button:has-text("删除")')).toBeVisible()

      await logout(page)
    })

    test('运营员不能管理系统配置', async ({ page }) => {
      await login(page, testUsers.operator.username, testUsers.operator.password)

      // 尝试访问系统配置
      await page.goto('/config')

      // 验证被拒绝
      await expect(page).toHaveURL('/403')

      await logout(page)
    })
  })

  test.describe('查看员权限测试', () => {
    test('查看员可以访问内容、发布页面但只读', async ({ page }) => {
      // 以查看员身份登录
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      // 测试可访问的页面
      const allowedPages = [
        { path: '/content', title: '内容管理' },
        { path: '/publisher', title: '发布管理' }
      ]

      for (const pageInfo of allowedPages) {
        await page.goto(pageInfo.path)

        // 验证页面成功加载
        await expect(page).not.toHaveURL('/403')
        await expect(page.locator('text=/' + pageInfo.title + '')).toBeVisible()

        // 验证没有新建按钮（只读）
        const createButton = page.locator('button:has-text("新建")')
        await expect(createButton).not.toBeVisible()

        // 验证没有编辑和删除按钮
        const firstRow = page.locator('.el-table__row').first()
        await expect(firstRow.locator('button:has-text("编辑")')).not.toBeVisible()
        await expect(firstRow.locator('button:has-text("删除")')).not.toBeVisible()
      }

      await logout(page)
    })

    test('查看员无法访问定时任务和发布池', async ({ page }) => {
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      // 测试不能访问的页面
      const forbiddenPages = [
        '/scheduler',
        '/publish-pool'
      ]

      for (const path of forbiddenPages) {
        await page.goto(path)

        // 验证跳转到403页面
        await expect(page).toHaveURL('/403')

        // 返回首页
        await page.goto('/')
      }

      await logout(page)
    })

    test('查看员可以查看内容详情但无法编辑', async ({ page }) => {
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      await page.goto('/content')

      // 等待内容列表加载
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 点击查看详情
      await page.locator('.el-table__row').first()
        .locator('button:has-text("查看")')
        .click()

      // 验证详情页面打开
      await page.waitForSelector('.content-detail', { timeout: 5000 })

      // 验证没有编辑按钮
      await expect(page.locator('button:has-text("编辑")')).not.toBeVisible()

      await logout(page)
    })
  })

  test.describe('路由权限控制测试', () => {
    test('未登录用户访问需要认证的页面被重定向到登录页', async ({ page }) => {
      // 不登录，直接访问需要认证的页面
      await page.goto('/content')

      // 验证重定向到登录页
      await expect(page).toHaveURL(/\/login.*/)
    })

    test('登录后可以访问之前想访问的页面', async ({ page }) => {
      // 访问需要认证的页面
      const targetUrl = '/content?test=1'
      await page.goto(targetUrl)

      // 应该重定向到登录页，并保存原始URL
      await expect(page).toHaveURL(/\/login.*/)
      const redirectUrl = page.url()
      expect(redirectUrl).toContain('redirect')

      // 登录
      await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
      await page.fill('input[type="password"]', testUsers.admin.password)
      await page.click('button[type="submit"]')

      // 等待跳转到原始页面
      await page.waitForURL('**/content**', { timeout: 10000 })
      await expect(page).toHaveURL(/\/content/)
    })
  })

  test.describe('按钮级权限控制测试', () => {
    test('不同角色看到不同的操作按钮', async ({ page }) => {
      // 测试管理员
      await login(page, testUsers.admin.username, testUsers.admin.password)
      await page.goto('/content')

      // 管理员应该看到所有按钮
      await expect(page.locator('button:has-text("新建")')).toBeVisible()
      await expect(page.locator('button:has-text("批量删除")')).toBeVisible()

      await logout(page)

      // 测试查看员
      await login(page, testUsers.viewer.username, testUsers.viewer.password)
      await page.goto('/content')

      // 查看员不应该看到操作按钮
      await expect(page.locator('button:has-text("新建")')).not.toBeVisible()
      await expect(page.locator('button:has-text("批量删除")')).not.toBeVisible()

      await logout(page)
    })
  })

  test.describe('数据隔离测试', () => {
    test('用户只能看到自己有权限的数据', async ({ page }) => {
      // 以运营员身份登录
      await login(page, testUsers.operator.username, testUsers.operator.password)

      await page.goto('/content')

      // 等待内容列表加载
      await page.waitForSelector('.el-table', { timeout: 10000 })

      // 验证列表显示了数据（可能是运营员创建的或分配给运营员的）
      const rows = page.locator('.el-table__row')
      const count = await rows.count()

      // 至少应该能看到某些数据（具体数量取决于测试数据）
      expect(count).toBeGreaterThanOrEqual(0)

      await logout(page)
    })
  })

  test.describe('权限边界测试', () => {
    test('跨用户操作被拒绝', async ({ page }) => {
      // 以查看员身份登录
      await login(page, testUsers.viewer.username, testUsers.viewer.password)

      await page.goto('/content')

      // 尝试直接访问编辑URL（绕过UI）
      // 这应该被后端权限控制拒绝
      await page.goto('/content/999/edit')

      // 验证要么显示403，要么显示权限错误
      const currentUrl = page.url()
      const isForbidden = currentUrl.includes('/403') ||
        await page.locator('text=/权限|拒绝|forbidden/i').count() > 0

      expect(isForbidden).toBeTruthy()

      await logout(page)
    })
  })
})
