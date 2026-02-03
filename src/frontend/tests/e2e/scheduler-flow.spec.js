/**
 * 定时任务完整流程 E2E 测试
 *
 * 测试场景：
 * 1. 创建定时任务 → 配置参数 → 启用任务 → 验证执行
 * 2. 验证任务执行历史
 * 3. 验证任务编辑和删除
 */

import { test, expect } from '@playwright/test'
import { login, logout, createTask, verifyMessage, verifyTableData } from './helpers/test-helpers'
import { testUsers, testTasks } from './helpers/test-data'

test.describe('定时任务完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前登录
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    // 每个测试后登出
    await logout(page)
  })

  test('完整定时任务流程：创建 → 配置 → 启用 → 手动触发', async ({ page }) => {
    // 步骤 1: 创建定时任务
    await page.goto('/scheduler')

    // 点击新建任务按钮
    await page.click('button:has-text("新建任务")')

    // 等待对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写任务基本信息
    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：定时内容生成任务')
    await page.fill('textarea[placeholder*="描述"]', 'E2E测试任务的描述')

    // 选择任务类型
    await page.click('.el-select:has-text("任务类型")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:has-text("content_generation")')

    // 设置执行间隔
    await page.fill('input[placeholder*="间隔"]', '30')
    await page.click('.el-select:has-text("时间单位")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:has-text("minutes")')

    // 配置任务参数
    // 选择平台
    await page.click('.el-select:has-text("选择平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    // 选择主题
    await page.click('.el-select:has-text("选择主题")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    // 选择写作风格
    await page.click('.el-select:has-text("写作风格")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    // 设置生成数量
    await page.fill('input[placeholder*="生成数量"]', '1')

    // 保存任务
    await page.click('button:has-text("保存")')

    // 验证创建成功
    await verifyMessage(page, '创建成功', 'success')

    // 等待对话框关闭
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 步骤 2: 验证任务出现在列表中
    await verifyTableData(page, 'E2E测试：定时内容生成任务')

    // 步骤 3: 启用任务
    const taskRow = page.locator('.el-table__row:has-text("E2E测试：定时内容生成任务")')
    await expect(taskRow).toBeVisible()

    // 查找启用/禁用开关
    const switchToggle = taskRow.locator('.el-switch').first()
    const isDisabled = await switchToggle.getAttribute('class')?.includes('is-disabled')

    if (!isDisabled) {
      await switchToggle.click()
      // 验证启用成功
      await verifyMessage(page, '启用成功', 'success')
    }

    // 步骤 4: 手动触发任务
    await taskRow.locator('button:has-text("立即执行")').click()

    // 确认对话框
    await page.click('.el-dialog button:has-text("确定")')

    // 验证触发成功
    await verifyMessage(page, '任务已触发', 'success')

    // 步骤 5: 查看执行历史
    await taskRow.locator('button:has-text("执行历史")').click()

    // 等待历史对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 验证历史记录显示
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('定时任务编辑和更新', async ({ page }) => {
    // 先创建一个任务
    await page.goto('/scheduler')
    await page.click('button:has-text("新建任务")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：可编辑任务')
    await page.click('.el-select:has-text("任务类型")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    await page.fill('input[placeholder*="间隔"]', '60')
    await page.click('button:has-text("保存")')
    await verifyMessage(page, '创建成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 编辑任务
    const taskRow = page.locator('.el-table__row:has-text("E2E测试：可编辑任务")')
    await taskRow.locator('button:has-text("编辑")').click()

    // 等待编辑对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 修改任务名称
    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：已编辑任务')

    // 修改间隔
    await page.fill('input[placeholder*="间隔"]', '120')

    // 保存修改
    await page.click('button:has-text("保存")')

    // 验证更新成功
    await verifyMessage(page, '更新成功', 'success')

    // 验证修改后的内容显示在列表中
    await verifyTableData(page, 'E2E测试：已编辑任务')
  })

  test('定时任务删除', async ({ page }) => {
    // 先创建一个任务
    await page.goto('/scheduler')
    await page.click('button:has-text("新建任务")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：可删除任务')
    await page.click('.el-select:has-text("任务类型")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    await page.fill('input[placeholder*="间隔"]', '30')
    await page.click('button:has-text("保存")')
    await verifyMessage(page, '创建成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 删除任务
    const taskRow = page.locator('.el-table__row:has-text("E2E测试：可删除任务")')
    await taskRow.locator('button:has-text("删除")').click()

    // 确认删除
    await page.click('.el-dialog button:has-text("确定")')

    // 验证删除成功
    await verifyMessage(page, '删除成功', 'success')

    // 验证任务不再出现在列表中
    const deletedRow = page.locator('.el-table__row:has-text("E2E测试：可删除任务")')
    await expect(deletedRow).not.toBeVisible()
  })

  test('定时任务禁用和启用', async ({ page }) => {
    // 创建任务
    await page.goto('/scheduler')
    await page.click('button:has-text("新建任务")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：开关任务')
    await page.click('.el-select:has-text("任务类型")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    await page.fill('input[placeholder*="间隔"]', '30')
    await page.click('button:has-text("保存")')
    await verifyMessage(page, '创建成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 测试启用/禁用切换
    const taskRow = page.locator('.el-table__row:has-text("E2E测试：开关任务")')
    const switchToggle = taskRow.locator('.el-switch').first()

    // 切换到禁用状态
    await switchToggle.click()

    // 等待状态更新
    await page.waitForTimeout(1000)

    // 再次切换到启用状态
    await switchToggle.click()

    // 验证状态切换成功
    await verifyMessage(page, '启用成功', 'success')
  })

  test('定时任务搜索和过滤', async ({ page }) => {
    await page.goto('/scheduler')

    // 等待任务列表加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 测试搜索功能
    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    await searchInput.fill('E2E测试')
    await page.keyboard.press('Enter')

    // 等待搜索结果加载
    await page.waitForTimeout(1000)

    // 测试状态过滤
    await page.click('.el-tabs__item:has-text("已启用")')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 测试任务类型过滤
    await page.click('.el-select:has-text("全部类型")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')
  })

  test('定时任务配置验证', async ({ page }) => {
    await page.goto('/scheduler')
    await page.click('button:has-text("新建任务")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 测试必填字段验证
    await page.click('button:has-text("保存")')

    // 验证显示错误提示
    await expect(page.locator('text=/必填|required/')).toBeVisible()

    // 测试间隔值验证
    await page.fill('input[placeholder*="任务名称"]', 'E2E测试：验证任务')
    await page.fill('input[placeholder*="间隔"]', '-1')
    await page.click('button:has-text("保存")')

    // 验证间隔错误提示
    await expect(page.locator('text=/间隔|interval/')).toBeVisible()
  })
})
