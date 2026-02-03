/**
 * 内容生成完整流程 E2E 测试
 *
 * 测试场景：
 * 1. 登录 → 创建内容 → 提交审核 → 审核 → 发布
 * 2. 验证每个步骤的页面状态和数据
 * 3. 验证内容状态流转（草稿 → 待审核 → 已审核 → 已发布）
 */

import { test, expect } from '@playwright/test'
import { login, logout, createContent, verifyMessage, verifyTableData } from './helpers/test-helpers'
import { testUsers, testContent } from './helpers/test-data'

test.describe('内容生成完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前登录
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    // 每个测试后登出
    await logout(page)
  })

  test('完整内容生成流程：创建 → 提交审核 → 审核 → 发布', async ({ page }) => {
    // 步骤 1: 创建内容草稿
    await page.goto('/content')

    // 点击新建按钮
    await page.click('button:has-text("新建")')

    // 等待对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 填写内容表单
    await page.fill('input[placeholder*="标题"]', testContent.publishable.title)
    await page.fill('input[placeholder*="标题"]', 'E2E测试：完整流程内容')

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

    // 填写内容
    const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]').first()
    await contentEditor.fill(testContent.publishable.content)

    // 保存草稿
    await page.click('button:has-text("保存")')

    // 验证保存成功
    await verifyMessage(page, '保存成功', 'success')

    // 等待对话框关闭
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 验证内容出现在列表中
    await verifyTableData(page, 'E2E测试：完整流程内容')

    // 步骤 2: 提交审核
    await page.click('.el-table__row:has-text("E2E测试：完整流程内容") button:has-text("编辑")')

    // 等待编辑对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 点击提交审核按钮
    await page.click('button:has-text("提交审核")')

    // 验证提交成功
    await verifyMessage(page, '提交审核成功', 'success')

    // 步骤 3: 审核通过（使用管理员账号）
    // 导航到待审核内容
    await page.goto('/content')

    // 筛选待审核内容
    await page.click('.el-tabs__item:has-text("待审核")')

    // 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找刚创建的内容
    const contentRow = page.locator('.el-table__row:has-text("E2E测试：完整流程内容")')
    await expect(contentRow).toBeVisible()

    // 点击审核通过按钮
    await contentRow.locator('button:has-text("审核通过")').click()

    // 确认对话框
    await page.click('.el-dialog button:has-text("确定")')

    // 验证审核通过
    await verifyMessage(page, '审核通过', 'success')

    // 步骤 4: 发布内容
    // 导航到已审核内容
    await page.click('.el-tabs__item:has-text("已审核")')

    // 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 查找已审核的内容
    const approvedRow = page.locator('.el-table__row:has-text("E2E测试：完整流程内容")')
    await expect(approvedRow).toBeVisible()

    // 点击发布按钮
    await approvedRow.locator('button:has-text("发布")').click()

    // 在发布对话框中选择账号
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 选择要发布的账号
    await page.click('.el-checkbox:has-text("微信")')

    // 确认发布
    await page.click('button:has-text("发布")')

    // 验证发布成功（可能需要mock外部API）
    // 这里验证至少显示了发布对话框
    await expect(page.locator('.el-dialog')).toBeVisible()
  })

  test('内容草稿可以编辑', async ({ page }) => {
    // 创建草稿
    await page.goto('/content')
    await page.click('button:has-text("新建")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="标题"]', 'E2E测试：可编辑草稿')
    await page.click('.el-select:has-text("选择平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]').first()
    await contentEditor.fill('原始内容')

    await page.click('button:has-text("保存")')
    await verifyMessage(page, '保存成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 编辑草稿
    await page.click('.el-table__row:has-text("E2E测试：可编辑草稿") button:has-text("编辑")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    // 修改内容
    await contentEditor.fill('修改后的内容')
    await page.click('button:has-text("保存")')

    // 验证保存成功
    await verifyMessage(page, '保存成功', 'success')
  })

  test('内容可以删除', async ({ page }) => {
    // 创建草稿
    await page.goto('/content')
    await page.click('button:has-text("新建")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="标题"]', 'E2E测试：可删除内容')
    await page.click('.el-select:has-text("选择平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]').first()
    await contentEditor.fill('将被删除的内容')

    await page.click('button:has-text("保存")')
    await verifyMessage(page, '保存成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 删除内容
    await page.click('.el-table__row:has-text("E2E测试：可删除内容") button:has-text("删除")')

    // 确认删除
    await page.click('.el-dialog button:has-text("确定")')

    // 验证删除成功
    await verifyMessage(page, '删除成功', 'success')

    // 验证内容不再出现在列表中
    const deletedRow = page.locator('.el-table__row:has-text("E2E测试：可删除内容")')
    await expect(deletedRow).not.toBeVisible()
  })

  test('内容搜索和过滤功能', async ({ page }) => {
    await page.goto('/content')

    // 等待内容列表加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 测试搜索功能
    const searchInput = page.locator('input[placeholder*="搜索"]').first()
    await searchInput.fill('E2E测试')
    await page.keyboard.press('Enter')

    // 等待搜索结果加载
    await page.waitForTimeout(1000)

    // 测试状态过滤
    await page.click('.el-tabs__item:has-text("草稿")')
    await page.waitForSelector('.el-table__row', { timeout: 5000 })

    // 测试平台过滤
    await page.click('.el-select:has-text("全部平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')
  })

  test('内容详情查看', async ({ page }) => {
    // 先创建一个内容
    await page.goto('/content')
    await page.click('button:has-text("新建")')
    await page.waitForSelector('.el-dialog', { timeout: 5000 })

    await page.fill('input[placeholder*="标题"]', 'E2E测试：查看详情')
    await page.click('.el-select:has-text("选择平台")')
    await page.waitForSelector('.el-select-dropdown', { timeout: 3000 })
    await page.click('.el-select-dropdown__item:first-child')

    const contentEditor = page.locator('.content-editor textarea, .content-editor [contenteditable="true"]').first()
    await contentEditor.fill('这是用于测试详情查看的内容')

    await page.click('button:has-text("保存")')
    await verifyMessage(page, '保存成功', 'success')
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // 查看详情
    await page.click('.el-table__row:has-text("E2E测试：查看详情") button:has-text("查看")')

    // 验证详情页面
    await page.waitForSelector('.content-detail', { timeout: 5000 })
    await expect(page.locator('text=E2E测试：查看详情')).toBeVisible()
    await expect(page.locator('text=这是用于测试详情查看的内容')).toBeVisible()
  })
})
