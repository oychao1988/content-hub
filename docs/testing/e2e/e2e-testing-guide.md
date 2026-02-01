# ContentHub E2E 测试总览

## 概述

ContentHub 项目的 E2E（端到端）测试使用 [Playwright](https://playwright.dev/) 框架，覆盖了所有核心业务流程。

## 测试架构

```
src/frontend/
├── playwright.config.js          # Playwright 配置文件
├── package.json                  # 包含 E2E 测试脚本
└── tests/
    └── e2e/                      # E2E 测试目录
        ├── helpers/              # 测试辅助函数
        │   ├── test-helpers.js   # 测试辅助函数库
        │   └── test-data.js      # 测试数据定义
        ├── global-setup.js       # 全局测试设置
        ├── setup.sh              # 环境设置脚本
        ├── README.md             # E2E 测试详细指南
        ├── RUN_TESTS.md          # 测试运行指南
        ├── example.spec.js       # 测试示例
        ├── content-generation-flow.spec.js    # 内容生成流程
        ├── scheduler-flow.spec.js             # 定时任务流程
        ├── batch-publish-flow.spec.js         # 批量发布流程
        ├── permission-control.spec.js         # 权限控制
        └── data-isolation.spec.js             # 数据隔离
```

## 快速开始

### 1. 安装依赖

```bash
cd src/frontend
npm install
npx playwright install
```

### 2. 启动服务

```bash
# 终端 1: 后端
cd src/backend
python main.py

# 终端 2: 前端
cd src/frontend
npm run dev
```

### 3. 运行测试

```bash
# 运行所有 E2E 测试
npm run test:e2e

# 使用 UI 模式
npm run test:e2e:ui

# 查看测试报告
npm run test:e2e:report
```

## 测试覆盖

### 1. 内容生成完整流程

**文件**: `content-generation-flow.spec.js`

**测试内容**:
- ✅ 创建内容草稿
- ✅ 提交审核
- ✅ 审核通过/拒绝
- ✅ 发布内容
- ✅ 内容编辑和删除
- ✅ 内容搜索和过滤
- ✅ 内容详情查看

**测试数量**: 6个测试用例

### 2. 定时任务完整流程

**文件**: `scheduler-flow.spec.js`

**测试内容**:
- ✅ 创建定时任务
- ✅ 配置任务参数
- ✅ 启用/禁用任务
- ✅ 手动触发任务
- ✅ 查看执行历史
- ✅ 任务编辑和删除
- ✅ 任务搜索和过滤
- ✅ 任务配置验证

**测试数量**: 6个测试用例

### 3. 批量发布完整流程

**文件**: `batch-publish-flow.spec.js`

**测试内容**:
- ✅ 批量发布流程
- ✅ 单个内容发布
- ✅ 发布池优先级调整
- ✅ 发布池内容移除
- ✅ 发布历史查询
- ✅ 发布状态流转
- ✅ 批量删除

**测试数量**: 7个测试用例

### 4. 权限控制完整流程

**文件**: `permission-control.spec.js`

**测试内容**:
- ✅ 管理员权限测试
- ✅ 运营员权限测试
- ✅ 查看员权限测试
- ✅ 路由权限控制
- ✅ 按钮级权限控制
- ✅ 数据隔离
- ✅ 权限边界测试

**测试数量**: ~20个测试用例

### 5. 跨用户数据隔离

**文件**: `data-isolation.spec.js`

**测试内容**:
- ✅ 内容数据隔离
- ✅ 定时任务数据隔离
- ✅ 发布池数据隔离
- ✅ 账号数据隔离
- ✅ 客户数据隔离
- ✅ API 数据隔离
- ✅ 会话隔离

**测试数量**: ~15个测试用例

## 测试统计

| 指标 | 数量 |
|------|------|
| 测试文件 | 6个 |
| 测试用例 | 54+个 |
| 辅助函数 | 14个 |
| 浏览器覆盖 | 5种 |
| 测试数据集 | 4组 |

## 浏览器覆盖

- ✅ Desktop Chrome (Chromium)
- ✅ Desktop Firefox
- ✅ Desktop Safari (WebKit)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)

## 测试角色

测试使用3种不同角色的用户：

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部权限 |
| 运营员 | operator1 | operator123 | 内容、发布、定时任务 |
| 查看员 | viewer1 | viewer123 | 只读访问 |

## 测试命令

```bash
# 运行所有测试
npm run test:e2e

# UI 模式运行
npm run test:e2e:ui

# 调试模式
npm run test:e2e:debug

# 显示浏览器运行
npm run test:e2e:headed

# 查看报告
npm run test:e2e:report

# 运行特定文件
npx playwright test content-generation-flow.spec.js

# 运行特定测试用例
npx playwright test -g "测试名称"

# 特定浏览器
npx playwright test --project=chromium
```

## 测试辅助函数

位于 `tests/e2e/helpers/test-helpers.js`：

- `login(page, username, password)` - 用户登录
- `logout(page)` - 用户登出
- `waitAndClick(page, selector)` - 等待并点击元素
- `waitAndFill(page, selector, value)` - 等待并填写表单
- `verifyMessage(page, message, type)` - 验证消息提示
- `createContent(page, contentData)` - 创建内容
- `createTask(page, taskData)` - 创建任务
- `verifyTableData(page, text)` - 验证表格数据
- `selectTableRows(page, count)` - 批量选择行
- `takeScreenshot(page, name)` - 截图
- `waitForLoading(page)` - 等待加载
- `getTableRowCount(page)` - 获取表格行数
- `verifyPageTitle(page, title)` - 验证页面标题

## 测试数据

位于 `tests/e2e/helpers/test-data.js`：

- `testUsers` - 测试用户数据（3个用户）
- `testContent` - 测试内容数据（3个内容）
- `testTasks` - 测试任务数据（2个任务）
- `testAccounts` - 测试账号数据
- `apiUrls` - API URL 配置

## 文档

- **详细指南**: `src/frontend/tests/e2e/README.md`
- **运行指南**: `src/frontend/tests/e2e/RUN_TESTS.md`
- **检查清单**: `E2E_TEST_CHECKLIST.md`
- **示例测试**: `src/frontend/tests/e2e/example.spec.js`

## 配置

Playwright 配置文件：`playwright.config.js`

关键配置：
- 基础 URL: `http://localhost:3010`
- 测试目录: `./tests/e2e`
- 超时时间: 操作10s, 导航30s
- 失败截图: ✅
- 失败视频: ✅
- 失败追踪: ✅
- 自动启动开发服务器: ✅

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

## 最佳实践

1. **使用辅助函数**：复用 `test-helpers.js` 中的函数
2. **等待元素**：使用 `waitForSelector()` 等待元素加载
3. **验证状态**：使用 `expect()` 验证页面状态
4. **清理数据**：在测试后清理创建的测试数据
5. **独立测试**：每个测试应该独立运行
6. **描述性名称**：使用清晰的测试和变量名称
7. **使用 Page Object Model**：将页面元素和操作封装
8. **Mock 外部服务**：使用 MSW mock 外部API

## 故障排查

### 测试失败

1. 查看 HTML 报告：`npm run test:e2e:report`
2. 检查截图：`test-results/` 目录
3. 检查视频：`test-results/` 目录
4. 使用调试模式：`npm run test:e2e:debug`

### 服务未启动

确保前后端服务都在运行：
- 后端: `http://localhost:8010`
- 前端: `http://localhost:3010`

### 元素定位问题

使用 Playwright Codegen 查找选择器：
```bash
npx playwright codegen http://localhost:3010
```

## 下一步

- [ ] 添加视觉回归测试
- [ ] 添加性能测试
- [ ] 添加可访问性测试
- [ ] 集成到 CI/CD
- [ ] 添加测试覆盖率报告

## 相关资源

- [Playwright 官方文档](https://playwright.dev/)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [项目测试完成计划](./TEST_COMPLETION_PLAN.md)
- [前端测试指南](./src/frontend/FRONTEND_TESTING_GUIDE.md)
