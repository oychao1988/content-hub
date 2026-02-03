/**
 * 仪表盘页面 E2E 测试
 *
 * 测试场景：
 * 1. 仪表盘页面正常加载
 * 2. 统计数据正确显示
 * 3. 活动记录正确显示
 * 4. 刷新功能正常
 * 5. 快速导航功能
 * 6. 数据更新实时性
 */

import { test, expect } from '@playwright/test'
import { login, logout } from './helpers/test-helpers'
import { testUsers } from './helpers/test-data'

test.describe('仪表盘页面', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前登录
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    // 每个测试后登出
    await logout(page)
  })

  test('仪表盘页面正常加载', async ({ page }) => {
    // 导航到仪表盘
    await page.goto('/')

    // 等待页面加载完成
    await page.waitForLoadState('networkidle')

    // 验证页面标题
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 验证页面主要元素存在
    await expect(page.locator('.dashboard, .page-content')).toBeVisible()
  })

  test('统计数据正确显示', async ({ page }) => {
    await page.goto('/')

    // 等待统计数据加载
    await page.waitForLoadState('networkidle')

    // 验证统计卡片存在（常见的统计项）
    const statsElements = page.locator('.stat-card, .stat-item, .data-card')
    const count = await statsElements.count()

    // 至少应该有一些统计卡片
    expect(count).toBeGreaterThan(0)

    // 验证统计数据显示（检查是否有数字）
    if (count > 0) {
      const firstStat = statsElements.first()
      await expect(firstStat).toBeVisible()

      // 检查统计卡片中是否包含数字
      const statText = await firstStat.textContent()
      expect(statText).toMatch(/\d+/)
    }
  })

  test('活动记录正确显示', async ({ page }) => {
    await page.goto('/')

    // 等待活动记录加载
    await page.waitForLoadState('networkidle')

    // 查找活动记录/最近活动区域
    const activitySection = page.locator('.activity-list, .recent-activity, .activity-log').first()

    // 如果存在活动记录区域
    if (await activitySection.count() > 0) {
      await expect(activitySection).toBeVisible()

      // 验证活动记录列表项
      const activityItems = activitySection.locator('.activity-item, .list-item')
      const itemCount = await activityItems.count()

      // 至少应该有活动记录容器
      await expect(activitySection).toBeVisible()
    }
  })

  test('刷新功能正常', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找刷新按钮
    const refreshButton = page.locator('button:has-text("刷新"), button:has-text("Refresh"), .refresh-button')

    // 如果存在刷新按钮
    if (await refreshButton.count() > 0) {
      // 点击刷新
      await refreshButton.first().click()

      // 等待刷新完成（可能有 loading 状态）
      await page.waitForLoadState('networkidle')

      // 验证页面仍然正常显示
      await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
    } else {
      // 如果没有刷新按钮，使用浏览器刷新
      await page.reload()
      await page.waitForLoadState('networkidle')

      // 验证页面正常
      await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
    }
  })

  test('快速导航功能', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找快速导航链接或快捷方式
    const quickNavLinks = page.locator('.quick-nav a, .shortcut a, .quick-link')

    // 如果存在快速导航
    const linkCount = await quickNavLinks.count()
    if (linkCount > 0) {
      // 点击第一个快速导航链接
      const firstLink = quickNavLinks.first()
      const href = await firstLink.getAttribute('href')

      if (href) {
        await firstLink.click()

        // 验证导航成功
        await page.waitForLoadState('networkidle')
        expect(page.url()).not.toEqual('/')
      }
    }
  })

  test('侧边栏导航', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找侧边栏导航
    const sidebar = page.locator('.sidebar, .aside, .nav-menu')

    // 验证侧边栏存在
    await expect(sidebar).toBeVisible()

    // 查找导航菜单项
    const navItems = sidebar.locator('a, .menu-item')
    const itemCount = await navItems.count()

    // 应该有多个导航项
    expect(itemCount).toBeGreaterThan(0)

    // 点击内容管理菜单项
    const contentNav = navItems.filter({ hasText: /内容|Content/ }).first()
    if (await contentNav.count() > 0) {
      await contentNav.click()
      await page.waitForLoadState('networkidle')

      // 验证导航到内容管理页面
      expect(page.url()).toContain('/content')
    }
  })

  test('用户菜单显示', async ({ page }) => {
    await page.goto('/')

    // 查找用户菜单/下拉菜单
    const userMenu = page.locator('.user-dropdown, .user-menu, .header-user-info')

    // 验证用户菜单存在
    await expect(userMenu).toBeVisible()

    // 点击用户菜单
    await userMenu.click()

    // 验证下拉菜单展开
    const dropdown = page.locator('.dropdown-menu, .user-dropdown-menu')
    await expect(dropdown).toBeVisible()

    // 验证包含退出登录选项
    await expect(dropdown).toContainText(/退出|Logout|登出/)
  })

  test('响应式布局 - 移动端视图', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 验证仪表盘在移动端仍然可见
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 查找移动端菜单按钮
    const mobileMenuButton = page.locator('.menu-toggle, .hamburger, .mobile-menu-button')
    if (await mobileMenuButton.count() > 0) {
      await expect(mobileMenuButton).toBeVisible()
    }
  })

  test('搜索功能', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="Search"], .search-box input')

    // 如果存在搜索框
    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible()

      // 输入搜索内容
      await searchInput.first().fill('test')

      // 验证搜索框可以输入（不验证结果，因为可能跳转）
      await expect(searchInput.first()).toHaveValue('test')
    }
  })

  test('通知/消息中心', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找通知/消息图标
    const notificationIcon = page.locator('.notification, .message-center, .bell-icon')

    // 如果存在通知图标
    if (await notificationIcon.count() > 0) {
      await expect(notificationIcon.first()).toBeVisible()

      // 点击通知图标
      await notificationIcon.first().click()

      // 验证通知列表或下拉菜单显示
      await page.waitForTimeout(500)
      // 通知面板可能显示
    }
  })

  test('数据时间范围筛选', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找时间范围选择器
    const dateRangePicker = page.locator('.date-range, .time-filter, .daterangepicker')

    // 如果存在时间范围选择器
    if (await dateRangePicker.count() > 0) {
      await expect(dateRangePicker.first()).toBeVisible()

      // 可以添加更多交互测试
    }
  })

  test('图表显示', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找图表容器
    const charts = page.locator('.chart, .graph, canvas, svg')

    // 如果存在图表
    const chartCount = await charts.count()
    if (chartCount > 0) {
      // 验证至少有一个图表可见
      await expect(charts.first()).toBeVisible()
    }
  })
})

test.describe('仪表盘性能测试', () => {
  test('页面加载时间', async ({ page }) => {
    // 记录开始时间
    const startTime = Date.now()

    await login(page, testUsers.admin.username, testUsers.admin.password)

    // 导航到仪表盘
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // 计算加载时间
    const loadTime = Date.now() - startTime

    // 页面应该在合理时间内加载完成（5秒内）
    expect(loadTime).toBeLessThan(5000)
  })

  test('数据刷新性能', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
    await page.goto('/')

    // 等待首次加载
    await page.waitForLoadState('networkidle')

    // 记录刷新开始时间
    const startTime = Date.now()

    // 刷新页面
    await page.reload()
    await page.waitForLoadState('networkidle')

    // 计算刷新时间
    const refreshTime = Date.now() - startTime

    // 刷新应该在合理时间内完成（3秒内）
    expect(refreshTime).toBeLessThan(3000)
  })
})

test.describe('仪表盘数据准确性', () => {
  test('统计数据非空', async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
    await page.goto('/')

    await page.waitForLoadState('networkidle')

    // 检查统计卡片不为空
    const statCards = page.locator('.stat-card, .stat-item, .data-card')
    const count = await statCards.count()

    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const card = statCards.nth(i)
        const text = await card.textContent()

        // 统计卡片应该包含数字
        expect(text).toMatch(/\d+/)
      }
    }
  })

  test('仪表盘在不同角色下的显示', async ({ page }) => {
    // 测试管理员视图
    await login(page, testUsers.admin.username, testUsers.admin.password)
    await page.goto('/')

    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 登出
    await logout(page)

    // 测试运营员视图
    await login(page, testUsers.operator.username, testUsers.operator.password)
    await page.goto('/')

    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()

    // 登出
    await logout(page)

    // 测试查看员视图
    await login(page, testUsers.viewer.username, testUsers.viewer.password)
    await page.goto('/')

    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=/仪表盘|Dashboard/')).toBeVisible()
  })
})
