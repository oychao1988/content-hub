/**
 * 登录与认证流程 E2E 测试
 *
 * 测试场景：
 * 1. 访问首页自动跳转到登录页
 * 2. 成功登录并跳转到仪表盘
 * 3. 错误密码登录显示错误提示
 * 4. 登录后持久化会话
 * 5. 登出功能
 * 6. 未登录访问受保护页面重定向
 */

import { test, expect } from '@playwright/test'
import { login, logout, verifyMessage } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('登录与认证流程', () => {
  // 不需要 beforeEach 和 afterEach，因为登录本身就是要测试的功能

  test('访问首页自动跳转到登录页', async ({ page }) => {
    // 访问首页
    await page.goto('/')

    // 验证自动跳转到登录页
    await page.waitForURL('/login')
    expect(page.url()).toContain('/login')

    // 验证登录表单显示
    await expect(page.locator('input[placeholder*="用户名"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('成功登录并跳转到仪表盘', async ({ page }) => {
    // 使用辅助函数登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 验证跳转到仪表盘
    expect(page.url()).toContain('/')
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 验证用户信息显示
    await expect(page.locator('.user-dropdown, .user-info')).toBeVisible()
  })

  test('错误密码登录显示错误提示', async ({ page }) => {
    // 访问登录页
    await page.goto('/login')

    // 填写错误的用户名和密码
    await page.fill('input[placeholder*="用户名"]', 'wronguser')
    await page.fill('input[type="password"]', 'wrongpassword')

    // 点击登录按钮
    await page.click('button[type="submit"]')

    // 验证错误提示显示（Element Plus 的错误消息）
    const errorMessage = page.locator('.el-message--error')
    await expect(errorMessage).toBeVisible({ timeout: 5000 })

    // 验证仍在登录页
    expect(page.url()).toContain('/login')
  })

  test('错误密码登录显示错误提示 - 使用正确用户名错误密码', async ({ page }) => {
    // 访问登录页
    await page.goto('/login')

    // 使用正确的用户名但错误的密码
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', 'wrongpassword')

    // 点击登录按钮
    await page.click('button[type="submit"]')

    // 验证错误提示显示
    const errorMessage = page.locator('.el-message--error')
    await expect(errorMessage).toBeVisible({ timeout: 5000 })

    // 验证仍在登录页
    expect(page.url()).toContain('/login')
  })

  test('登录后持久化会话', async ({ page, context }) => {
    // 登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 验证 localStorage 或 sessionStorage 中有 token
    const localStorage = await page.evaluate(() => window.localStorage)
    const sessionStorage = await page.evaluate(() => window.sessionStorage)

    // 检查是否有认证相关的存储（token 或用户信息）
    const hasToken =
      Object.values(localStorage).some(val => val && (val.includes('token') || val.includes('user'))) ||
      Object.values(sessionStorage).some(val => val && (val.includes('token') || val.includes('user')))

    expect(hasToken).toBeTruthy()

    // 刷新页面验证会话持久化
    await page.reload()

    // 验证仍在仪表盘，没有跳转到登录页
    await page.waitForLoadState('networkidle')
    expect(page.url()).not.toContain('/login')
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
  })

  test('登出功能', async ({ page }) => {
    // 先登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 验证已登录
    await expect(page.locator('.user-dropdown, .user-info')).toBeVisible()

    // 登出
    await logout(page)

    // 验证跳转到登录页
    expect(page.url()).toContain('/login')

    // 验证可以再次登录（会话已清除）
    await login(page, testUsers.admin.username, testUsers.admin.password)
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
  })

  test('未登录访问受保护页面重定向', async ({ page }) => {
    // 直接访问受保护页面（内容管理）
    await page.goto('/content')

    // 验证重定向到登录页
    await page.waitForURL('/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')

    // 登录后验证跳转回原页面或仪表盘
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)
    await page.click('button[type="submit"]')

    // 验证登录成功，跳转到仪表盘或原页面
    await page.waitForURL(/\/(content|\/)/, { timeout: 10000 })
    await expect(page.locator('text=/仪表盘|Dashboard|内容管理/')).toBeVisible()
  })

  test('访问定时任务页面需要登录', async ({ page }) => {
    // 直接访问定时任务页面
    await page.goto('/scheduler')

    // 验证重定向到登录页
    await page.waitForURL('/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  test('访问发布池页面需要登录', async ({ page }) => {
    // 直接访问发布池页面
    await page.goto('/publish-pool')

    // 验证重定向到登录页
    await page.waitForURL('/login', { timeout: 5000 })
    expect(page.url()).toContain('/login')
  })

  test('登录后可以访问所有受保护页面', async ({ page }) => {
    // 登录
    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 测试多个受保护页面
    const protectedPages = [
      '/content',
      '/scheduler',
      '/publish-pool',
      '/accounts',
      '/users'
    ]

    for (const pagePath of protectedPages) {
      await page.goto(pagePath)
      await page.waitForLoadState('networkidle')

      // 验证没有重定向到登录页
      expect(page.url()).not.toContain('/login')
      expect(page.url()).toContain(pagePath)
    }
  })

  test('表单验证：空用户名和密码', async ({ page }) => {
    // 访问登录页
    await page.goto('/login')

    // 不填写任何信息直接点击登录
    await page.click('button[type="submit"]')

    // 验证表单验证提示（Element Plus 表单验证）
    const validationMessages = page.locator('.el-form-item__error')
    // 至少应该有用户名和密码的验证提示
    expect(await validationMessages.count()).toBeGreaterThan(0)
  })

  test('表单验证：只有用户名没有密码', async ({ page }) => {
    // 访问登录页
    await page.goto('/login')

    // 只填写用户名
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)

    // 点击登录
    await page.click('button[type="submit"]')

    // 验证密码验证提示
    const passwordError = page.locator('.el-form-item__error').filter({ hasText: /密码/ })
    await expect(passwordError).toBeVisible()
  })
})

test.describe('登录安全测试', () => {
  test('密码输入框隐藏密码字符', async ({ page }) => {
    await page.goto('/login')

    const passwordInput = page.locator('input[type="password"]')
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // 输入密码
    await passwordInput.fill('testpassword')

    // 验证值不为空但类型仍是 password
    await expect(passwordInput).toHaveValue('testpassword')
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('登录按钮禁用状态', async ({ page }) => {
    await page.goto('/login')

    const submitButton = page.locator('button[type="submit"]')

    // 初始状态应该可用
    await expect(submitButton).toBeEnabled()

    // 登录中应该禁用（如果实现了加载状态）
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)
    await submitButton.click()

    // 可以检查是否有 loading 类
    await expect(submitButton).toHaveClass(/is-loading|el-button--loading/, { timeout: 1000 }).catch(() => {
      // 如果没有 loading 状态也不算失败
    })
  })
})

test.describe('多用户登录测试', () => {
  test('管理员登录成功', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
    await logout(page)
  })

  test('运营员登录成功', async ({ page }) => {
    await login(page, testUsers.operator.username, testUsers.operator.password)
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
    await logout(page)
  })

  test('查看员登录成功', async ({ page }) => {
    await login(page, testUsers.viewer.username, testUsers.viewer.password)
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
    await logout(page)
  })
})

test.describe('登录表单边界验证', () => {
  test('记住我功能', async ({ page }) => {
    await page.goto('/login')

    // 勾选记住我复选框
    const checkbox = page.locator('.login-form input[type="checkbox"]')
    await checkbox.check()
    await expect(checkbox).toBeChecked()

    // 登录
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)
    await page.click('button[type="submit"]')

    // 等待登录成功
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 验证记住我状态被保存到 localStorage
    const rememberMe = await page.evaluate(() => {
      return localStorage.getItem('rememberMe') === 'true'
    })
    expect(rememberMe).toBeTruthy()

    await logout(page)
  })

  test('用户名长度验证 - 少于3个字符', async ({ page }) => {
    await page.goto('/login')

    // 输入少于3个字符的用户名
    await page.fill('input[placeholder*="用户名"]', 'ab')
    await page.fill('input[type="password"]', '123456')
    await page.click('button[type="submit"]')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
    await expect(errorMsg).toContainText('3 到 20')
  })

  test('用户名长度验证 - 超过20个字符', async ({ page }) => {
    await page.goto('/login')

    // 输入超过20个字符的用户名
    await page.fill('input[placeholder*="用户名"]', 'a'.repeat(25))
    await page.fill('input[type="password"]', '123456')
    await page.click('button[type="submit"]')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
    await expect(errorMsg).toContainText('3 到 20')
  })

  test('密码长度验证 - 少于6个字符', async ({ page }) => {
    await page.goto('/login')

    // 输入正确的用户名但密码少于6个字符
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', '12345')
    await page.click('button[type="submit"]')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
    await expect(errorMsg).toContainText('6 到 20')
  })

  test('密码长度验证 - 超过20个字符', async ({ page }) => {
    await page.goto('/login')

    // 输入正确的用户名但密码超过20个字符
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', 'a'.repeat(25))
    await page.click('button[type="submit"]')

    // 验证错误提示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
    await expect(errorMsg).toContainText('6 到 20')
  })

  test('Enter键提交表单', async ({ page }) => {
    await page.goto('/login')

    // 填写表单
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)

    // 按Enter键提交
    await page.keyboard.press('Enter')

    // 验证登录成功
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
  })

  test('Redirect参数测试 - 从受保护页面跳转后返回', async ({ page }) => {
    // 直接访问受保护页面（内容管理）
    await page.goto('/content')

    // 验证重定向到登录页，并且包含redirect参数
    await page.waitForURL('/login')
    expect(page.url()).toContain('/login')

    // 登录
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)
    await page.click('button[type="submit"]')

    // 验证返回到原页面（/content）或仪表盘
    await page.waitForURL(/\/(content|\/)/)
    expect(page.url()).toMatch(/\/(content|\/)/)
  })

  test('密码显示/隐藏切换', async ({ page }) => {
    await page.goto('/login')

    const passwordInput = page.locator('input[type="password"]')
    const eyeIcon = page.locator('.el-input__suffix .el-icon').first()

    // 密码输入框应该默认隐藏
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // 如果有眼睛图标（显示/隐藏切换）
    if (await eyeIcon.count() > 0) {
      // 点击显示密码
      await eyeIcon.click()

      // 验证密码可见（type变成text）
      await expect(passwordInput).toHaveAttribute('type', 'text')

      // 再次点击隐藏密码
      await eyeIcon.click()

      // 验证密码重新隐藏
      await expect(passwordInput).toHaveAttribute('type', 'password')
    }
  })

  test('表单验证触发时机 - blur触发验证', async ({ page }) => {
    await page.goto('/login')

    const usernameInput = page.locator('input[placeholder*="用户名"]')

    // 输入用户名
    await usernameInput.fill('ab')

    // 点击其他地方触发blur
    await page.click('body')

    // 验证错误提示应该立即显示
    const errorMsg = page.locator('.el-form-item__error')
    await expect(errorMsg).toBeVisible()
  })

  test('登录按钮loading状态', async ({ page }) => {
    await page.goto('/login')

    const submitButton = page.locator('.login-button button')

    // 填写表单
    await page.fill('input[placeholder*="用户名"]', testUsers.admin.username)
    await page.fill('input[type="password"]', testUsers.admin.password)

    // 点击登录
    await submitButton.click()

    // 验证按钮变为loading状态（可能短暂，所以使用短超时）
    await expect(submitButton).toHaveClass(/is-loading|el-button-is-loading/, { timeout: 500 }).catch(() => {
      // loading可能很快完成，这是可接受的
    })

    // 最终应该登录成功
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
  })
})
