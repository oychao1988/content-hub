# E2E 测试运行指南

## 快速开始

### 1. 环境准备

```bash
# 进入前端目录
cd /Users/Oychao/Documents/Projects/content-hub/src/frontend

# 安装依赖（如果还没安装）
npm install

# 安装 Playwright 浏览器
npx playwright install
```

### 2. 启动服务

E2E 测试需要前后端服务都运行：

**终端 1 - 启动后端：**
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python main.py
```

**终端 2 - 启动前端：**
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/frontend
npm run dev
```

**验证服务：**
- 后端: http://localhost:8010/docs
- 前端: http://localhost:3010

### 3. 运行测试

**终端 3 - 运行 E2E 测试：**

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/frontend

# 方式 1: 运行所有 E2E 测试
npm run test:e2e

# 方式 2: 使用 UI 模式（推荐）
npm run test:e2e:ui

# 方式 3: 显示浏览器窗口运行
npm run test:e2e:headed

# 方式 4: 调试模式
npm run test:e2e:debug

# 方式 5: 运行特定测试文件
npx playwright test content-generation-flow.spec.js

# 方式 6: 运行特定测试用例
npx playwright test -g "完整内容生成流程"
```

## 测试文件说明

| 测试文件 | 测试内容 | 测试数量 |
|---------|---------|---------|
| `content-generation-flow.spec.js` | 内容生成完整流程 | 6个 |
| `scheduler-flow.spec.js` | 定时任务完整流程 | 6个 |
| `batch-publish-flow.spec.js` | 批量发布完整流程 | 7个 |
| `permission-control.spec.js` | 权限控制完整流程 | 20+个 |
| `data-isolation.spec.js` | 跨用户数据隔离 | 15+个 |
| `example.spec.js` | 测试示例 | 10个 |

## 查看测试结果

### HTML 报告

测试运行完成后，查看 HTML 报告：

```bash
npm run test:e2e:report
```

或在浏览器中打开：
```bash
npx playwright show-report
```

### 控制台输出

测试运行时会显示详细的控制台输出：
- ✅ 通过的测试
- ❌ 失败的测试
- ⏱️  测试执行时间

### 失败测试的截图和视频

失败的测试会自动保存：
- 截图: `test-results/` 目录
- 视频: `test-results/` 目录
- 追踪: `test-results/` 目录

## 测试场景说明

### 1. 内容生成完整流程

测试内容从创建到发布的完整生命周期：
- 创建内容草稿
- 提交审核
- 审核通过/拒绝
- 发布内容
- 内容编辑和删除
- 内容搜索和过滤

### 2. 定时任务完整流程

测试定时任务的创建和管理：
- 创建定时任务
- 配置任务参数
- 启用/禁用任务
- 手动触发任务
- 查看执行历史

### 3. 批量发布完整流程

测试批量发布功能：
- 选择多个内容
- 添加到发布池
- 批量发布
- 发布池管理

### 4. 权限控制完整流程

测试不同角色的权限边界：
- 管理员权限（全部权限）
- 运营员权限（内容、发布、定时任务）
- 查看员权限（只读访问）
- 路由和按钮级权限控制

### 5. 跨用户数据隔离

测试多用户环境下的数据隔离：
- 内容数据隔离
- 定时任务数据隔离
- 发布池数据隔离
- 会话隔离

## 常见问题

### Q: 测试失败怎么办？

1. 查看 HTML 报告了解失败原因
2. 检查 `test-results/` 目录中的截图和视频
3. 使用调试模式逐步运行测试：`npm run test:e2e:debug`

### Q: 如何只运行一个测试？

```bash
# 运行特定测试文件
npx playwright test filename.spec.js

# 运行特定测试用例（使用grep）
npx playwright test -g "测试用例名称"
```

### Q: 如何跳过某个测试？

在测试代码中使用 `test.skip()`：

```javascript
test.skip('这个测试被跳过', async ({ page }) => {
  // 测试代码
})
```

### Q: 如何只在特定浏览器运行？

```bash
# 只在 Chromium 运行
npx playwright test --project=chromium

# 只在 Firefox 运行
npx playwright test --project=firefox

# 只在 WebKit 运行
npx playwright test --project=webkit
```

### Q: 测试需要多长时间？

- 单个测试: 通常 10-30 秒
- 所有测试: 约 5-15 分钟（取决于机器性能）

### Q: 如何并行运行测试？

Playwright 默认并行运行测试。控制并行度：

```javascript
// playwright.config.js
export default defineConfig({
  workers: 4, // 并行工作线程数
})
```

## 测试数据

测试使用的数据定义在 `helpers/test-data.js`：

```javascript
export const testUsers = {
  admin: {
    username: 'admin',
    password: 'admin123'
  },
  operator: {
    username: 'operator1',
    password: 'operator123'
  },
  viewer: {
    username: 'viewer1',
    password: 'viewer123'
  }
}
```

确保这些用户在数据库中存在。

## 编写新测试

1. 在 `tests/e2e/` 创建新的 `.spec.js` 文件
2. 导入辅助函数和测试数据：

```javascript
import { test, expect } from '@playwright/test'
import { login, logout } from '../helpers/test-helpers'
import { testUsers } from '../helpers/test-data'
```

3. 编写测试：

```javascript
test.describe('我的测试套件', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers.admin.username, testUsers.admin.password)
  })

  test('我的测试用例', async ({ page }) => {
    await page.goto('/some-page')
    await expect(page.locator('h1')).toHaveText('页面标题')
  })
})
```

4. 运行新测试：

```bash
npx playwright test my-new-test.spec.js
```

## 最佳实践

1. **使用辅助函数**：复用 `test-helpers.js` 中的函数
2. **等待元素**：使用 `waitForSelector()` 等待元素加载
3. **验证状态**：使用 `expect()` 验证页面状态
4. **清理数据**：在测试后清理创建的测试数据
5. **独立测试**：每个测试应该独立运行
6. **描述性名称**：使用清晰的测试和变量名称

## 相关资源

- [Playwright 文档](https://playwright.dev/)
- [测试指南](./README.md)
- [检查清单](./CHECKLIST.md)
- [示例测试](./example.spec.js)
