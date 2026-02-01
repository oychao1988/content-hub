# E2E 测试指南

## 概述

本目录包含 ContentHub 项目的端到端（E2E）测试，使用 [Playwright](https://playwright.dev/) 测试框架。

## 测试覆盖

### 1. 内容生成完整流程 (`content-generation-flow.spec.js`)

测试内容从创建到发布的完整生命周期：

- ✅ 创建内容草稿
- ✅ 提交审核
- ✅ 审核通过/拒绝
- ✅ 发布内容
- ✅ 内容编辑和删除
- ✅ 内容搜索和过滤
- ✅ 内容详情查看

### 2. 定时任务完整流程 (`scheduler-flow.spec.js`)

测试定时任务的创建和管理：

- ✅ 创建定时任务
- ✅ 配置任务参数
- ✅ 启用/禁用任务
- ✅ 手动触发任务
- ✅ 查看执行历史
- ✅ 编辑和删除任务
- ✅ 任务搜索和过滤
- ✅ 任务配置验证

### 3. 批量发布完整流程 (`batch-publish-flow.spec.js`)

测试批量发布功能：

- ✅ 选择多个内容
- ✅ 添加到发布池
- ✅ 批量发布
- ✅ 优先级调整
- ✅ 发布池内容移除
- ✅ 发布历史查询
- ✅ 发布状态流转

### 4. 权限控制完整流程 (`permission-control.spec.js`)

测试不同角色的权限边界：

- ✅ 管理员权限（全部权限）
- ✅ 运营员权限（内容、发布、定时任务）
- ✅ 查看员权限（只读访问）
- ✅ 路由权限控制
- ✅ 按钮级权限控制
- ✅ 数据隔离
- ✅ 权限边界测试

### 5. 跨用户数据隔离 (`data-isolation.spec.js`)

测试多用户环境下的数据隔离：

- ✅ 内容数据隔离
- ✅ 定时任务数据隔离
- ✅ 发布池数据隔离
- ✅ 账号数据隔离
- ✅ 客户数据隔离
- ✅ 审计日志数据隔离
- ✅ API数据隔离验证
- ✅ 会话隔离

## 前置条件

### 1. 安装依赖

```bash
cd src/frontend
npm install
```

### 2. 安装 Playwright 浏览器

```bash
npx playwright install
```

### 3. 启动服务

E2E测试需要前后端服务都运行：

**启动后端服务：**
```bash
cd src/backend
python main.py
# 后端运行在 http://localhost:8010
```

**启动前端服务（新终端）：**
```bash
cd src/frontend
npm run dev
# 前端运行在 http://localhost:3010
```

### 4. 准备测试数据

确保数据库中有测试用户：

```bash
cd src/backend
python -c "from app.db.database import init_db; init_db()"
```

默认测试用户：
- 管理员: `admin` / `admin123`
- 运营员: `operator1` / `operator123`
- 查看员: `viewer1` / `viewer123`

## 运行测试

### 运行所有 E2E 测试

```bash
npm run test:e2e
```

### 运行特定测试文件

```bash
npx playwright test content-generation-flow.spec.js
```

### 运行特定测试用例

```bash
npx playwright test -g "完整内容生成流程"
```

### 以 headed 模式运行（显示浏览器）

```bash
npm run test:e2e:headed
```

### 调试模式运行

```bash
npm run test:e2e:debug
```

### 使用 UI 模式运行

```bash
npm run test:e2e:ui
```

## 查看测试报告

### HTML 报告

```bash
npm run test:e2e:report
```

或在测试完成后运行：

```bash
npx playwright show-report
```

## 测试辅助函数

测试辅助函数位于 `helpers/test-helpers.js`：

- `login(page, username, password)` - 登录
- `logout(page)` - 登出
- `createContent(page, contentData)` - 创建内容
- `createTask(page, taskData)` - 创建任务
- `verifyMessage(page, message, type)` - 验证消息提示
- `verifyTableData(page, text)` - 验证表格数据
- `selectTableRows(page, count)` - 批量选择表格行

## 测试数据

测试数据位于 `helpers/test-data.js`：

- `testUsers` - 测试用户数据
- `testContent` - 测试内容数据
- `testTasks` - 测试任务数据
- `testAccounts` - 测试账号数据
- `apiUrls` - API URL 配置

## 配置

Playwright 配置文件：`playwright.config.js`

关键配置：
- 基础 URL: `http://localhost:3010`
- 测试目录: `./tests/e2e`
- 浏览器: Chromium, Firefox, WebKit
- 失败时截图: ✅
- 失败时录制视频: ✅
- 失败时保留追踪: ✅

## 编写新的 E2E 测试

1. 在 `tests/e2e/` 目录创建新的测试文件（`.spec.js`）
2. 导入必要的辅助函数和测试数据
3. 使用 `test.describe()` 组织测试套件
4. 使用 `test()` 定义测试用例
5. 使用 Playwright 的 API 进行页面操作和断言

示例：

```javascript
import { test, expect } from '@playwright/test'
import { login, logout } from '../helpers/test-helpers'
import { testUsers } from '../helpers/test-data'

test.describe('我的测试套件', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test.afterEach(async ({ page }) => {
    await logout(page)
  })

  test('我的测试用例', async ({ page }) => {
    await page.goto('/some-page')
    await expect(page.locator('h1')).toHaveText('页面标题')
  })
})
```

## 最佳实践

1. **使用辅助函数**：复用 `test-helpers.js` 中的函数
2. **等待元素**：使用 `waitForSelector()` 等待元素加载
3. **验证状态**：使用 `expect()` 验证页面状态
4. **清理数据**：在测试后清理创建的测试数据
5. **独立测试**：每个测试应该独立运行，不依赖其他测试
6. **描述性名称**：使用清晰的测试和变量名称

## 故障排查

### 测试失败

1. 查看 HTML 报告了解失败原因
2. 检查截图和视频（位于 `test-results/`）
3. 使用调试模式逐步运行测试

### 服务未启动

确保前后端服务都在运行：
- 后端: `http://localhost:8010`
- 前端: `http://localhost:3010`

### 测试数据问题

重新初始化测试数据：
```bash
cd src/backend
python -c "from app.db.database import init_db; init_db()"
```

### 元素定位问题

使用 Playwright Inspector 查找选择器：
```bash
npx playwright codegen http://localhost:3010
```

## CI/CD 集成

E2E 测试可以在 CI/CD 流程中自动运行：

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## 参考资源

- [Playwright 文档](https://playwright.dev/)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright API 参考](https://playwright.dev/docs/api/class-playwright)
