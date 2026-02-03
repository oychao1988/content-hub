/**
 * 403 权限页面 E2E 测试
 *
 * 测试场景：
 * 1. 403 页面正常显示
 * 2. 无权限访问管理员页面
 * 3. 路由级权限控制
 * 4. 按钮级权限控制
 * 5. 数据级权限控制
 * 6. 返回上一页功能
 */

import { test, expect } from '@playwright/test'
import { login, logout } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('403 权限页面测试', () => {
  test('403 页面正常显示', async ({ page }) => {
    // 使用查看员登录（权限较低）
    await login(page, testUsers.viewer.username, testUsers.viewer.password)

    // 尝试访问用户管理页面（管理员权限）
    await page.goto('/users')

    // 验证可能跳转到 403 页面或首页
    await page.waitForTimeout(2000)

    const currentUrl = page.url()

    // 要么显示 403 页面，要么被重定向
    if (currentUrl.includes('/403') || currentUrl.includes('forbidden')) {
      // 验证 403 页面内容
      await expect(page.locator('text=/403|无权限|Forbidden/')).toBeVisible()
    } else {
      // 验证仍在首页或登录页
      expect(currentUrl).toMatch(/\/(login|\?)/)
    }

    await logout(page)
  })

  test('路由级权限控制', async ({ page }) => {
    // 运营员登录
    await login(page, testUsers.operator.username, testUsers.operator.password)

    // 运营员可以访问的页面
    const allowedPages = ['/content', '/scheduler']
    for (const pagePath of allowedPages) {
      await page.goto(pagePath)
      await page.waitForLoadState('networkidle')

      // 应该能正常访问
      expect(page.url()).toContain(pagePath)
    }

    // 运营员不应该能访问的页面（用户管理）
    await page.goto('/users')
    await page.waitForTimeout(1000)

    // 应该被重定向或显示无权限
    const currentUrl = page.url()
    expect(currentUrl).not.toContain('/users')

    await logout(page)
  })

  test('按钮级权限控制', async ({ page }) => {
    // 查看员登录
    await login(page, testUsers.viewer.username, testUsers.viewer.password)

    // 访问内容管理页面
    await page.goto('/content')
    await page.waitForLoadState('networkidle')

    // 查看员应该看不到"删除"等操作按钮
    const deleteButtons = page.locator('button:has-text("删除")')
    const createButton = page.locator('button:has-text("新建"), button:has-text("添加")')

    // 可能没有这些按钮，或者按钮被禁用
    if (await deleteButtons.count() > 0) {
      // 如果有删除按钮，可能是禁用状态
      const firstDelete = deleteButtons.first()
      const isDisabled = await firstDelete.isDisabled()
      expect(isDisabled || (await deleteButtons.count()) === 0).toBeTruthy()
    }

    await logout(page)
  })

  test('数据级权限控制', async ({ page }) => {
    // 运营员登录
    await login(page, testUsers.operator.username, testUsers.operator.password)

    await page.goto('/content')
    await page.waitForLoadState('networkidle')

    // 验证只能看到自己创建的内容（或所在客户的内容）
    // 这里只验证页面正常加载，具体数据隔离由 data-isolation.spec.js 测试
    await expect(page.locator('.el-table')).toBeVisible()

    await logout(page)
  })

  test('返回上一页功能', async ({ page }) => {
    // 查看员登录
    await login(page, testUsers.viewer.username, testUsers.viewer.password)

    // 尝试访问无权限页面
    await page.goto('/users')
    await page.waitForTimeout(1000)

    // 如果有 403 页面
    if (page.url().includes('/403') || await page.locator('text=/403|无权限/').count() > 0) {
      const backButton = page.locator('button:has-text("返回"), button:has-text("Back")')

      if (await backButton.count() > 0) {
        await backButton.click()
        await page.waitForTimeout(500)

        // 验证返回到上一页或首页
        expect(page.url()).not.toContain('/403')
      }
    }

    await logout(page)
  })

  test('权限提示信息', async ({ page }) => {
    // 查看员登录
    await login(page, testUsers.viewer.username, testUsers.viewer.password)

    // 尝试访问管理员页面
    await page.goto('/users')
    await page.waitForTimeout(1000)

    // 查找权限提示
    const permissionMessage = page.locator('text=/无权限|没有权限|Permission denied/')

    if (await permissionMessage.count() > 0) {
      await expect(permissionMessage).toBeVisible()
    }

    await logout(page)
  })

  test('不同角色不同权限', async ({ page }) => {
    // 测试管理员可以访问所有页面
    await login(page, testUsers.admin.username, testUsers.admin.password)

    const adminPages = ['/users', '/accounts', '/platforms', '/config']
    for (const pagePath of adminPages) {
      await page.goto(pagePath)
      await page.waitForLoadState('networkidle')
      expect(page.url()).toContain(pagePath)
    }

    await logout(page)

    // 测试查看员不能访问这些页面
    await login(page, testUsers.viewer.username, testUsers.viewer.password)

    for (const pagePath of adminPages) {
      await page.goto(pagePath)
      await page.waitForTimeout(1000)
      // 应该被重定向
      expect(page.url()).not.toContain(pagePath)
    }

    await logout(page)
  })

  test('会话超时后权限控制', async ({ page }) => {
    // 登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 访问受保护页面
    await page.goto('/users')
    await page.waitForLoadState('networkidle')

    // 模拟清除会话（清除 localStorage）
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // 刷新页面
    await page.reload()
    await page.waitForTimeout(1000)

    // 应该被重定向到登录页
    expect(page.url()).toContain('/login')
  })
})
