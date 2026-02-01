# E2E 测试快速参考卡

## 快速启动

```bash
# 1. 安装（首次）
cd src/frontend
npm install
npx playwright install

# 2. 启动服务
# 终端1: 后端
cd src/backend && python main.py

# 终端2: 前端
cd src/frontend && npm run dev

# 3. 运行测试
# 终端3: 测试
cd src/frontend
npm run test:e2e
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run test:e2e` | 运行所有测试 |
| `npm run test:e2e:ui` | UI模式运行 |
| `npm run test:e2e:headed` | 显示浏览器 |
| `npm run test:e2e:debug` | 调试模式 |
| `npm run test:e2e:report` | 查看报告 |

## 测试文件

| 文件 | 测试内容 | 用例数 |
|------|---------|-------|
| `content-generation-flow.spec.js` | 内容生成 | 6 |
| `scheduler-flow.spec.js` | 定时任务 | 6 |
| `batch-publish-flow.spec.js` | 批量发布 | 7 |
| `permission-control.spec.js` | 权限控制 | 21+ |
| `data-isolation.spec.js` | 数据隔离 | 15+ |
| `example.spec.js` | 示例 | 10 |

## 辅助函数

```javascript
import { login, logout } from '../helpers/test-helpers'
import { testUsers } from '../helpers/test-data'

// 登录
await login(page, testUsers.admin.username, testUsers.admin.password)

// 登出
await logout(page)

// 验证消息
await verifyMessage(page, '保存成功', 'success')

// 创建内容
await createContent(page, contentData)

// 创建任务
await createTask(page, taskData)
```

## 测试数据

```javascript
testUsers.admin       // admin / admin123
testUsers.operator    // operator1 / operator123
testUsers.viewer      // viewer1 / viewer123

testContent.draft
testContent.publishable
testContent.scheduled

testTasks.basic
testTasks.complex
```

## 常见操作

### 页面导航
```javascript
await page.goto('/content')
await page.waitForURL('**/content')
```

### 元素交互
```javascript
await page.click('button:has-text("新建")')
await page.fill('input[placeholder*="标题"]', '测试')
await page.selectOption('select', 'value')
```

### 等待元素
```javascript
await page.waitForSelector('.el-dialog')
await page.waitForSelector('text=成功')
```

### 断言
```javascript
await expect(page).toHaveURL('/content')
await expect(locator).toBeVisible()
await expect(locator).toHaveText('内容')
```

## 选择器速查

| 类型 | 语法 | 示例 |
|------|------|------|
| 文本 | `text=文本` | `text=保存` |
| CSS | `css` | `button.primary` |
| 包含文本 | `:has-text()` | `button:has-text("保存")` |
| 属性 | `[attr=value]` | `[data-id="1"]` |
| 组合 | `>>` | `body >> .text` |

## 问题排查

| 问题 | 解决方案 |
|------|---------|
| 测试失败 | 查看报告: `npm run test:e2e:report` |
| 找不到元素 | 使用 `npx playwright codegen` |
| 服务未启动 | 检查 http://localhost:8010 和 3010 |
| 测试数据问题 | 重新初始化数据库 |

## 文档

- 详细指南: `tests/e2e/README.md`
- 运行指南: `tests/e2e/RUN_TESTS.md`
- 示例代码: `tests/e2e/example.spec.js`
- 项目总览: `E2E_TESTING_GUIDE.md`

## 测试覆盖

✅ 内容管理（创建、编辑、删除、审核、发布）
✅ 定时任务（创建、配置、启用、执行）
✅ 发布管理（单个、批量、发布池）
✅ 权限控制（管理员、运营员、查看员）
✅ 数据隔离（内容、任务、发布、会话）

## 浏览器

- ✅ Chromium (Desktop Chrome)
- ✅ Firefox
- ✅ WebKit (Safari)
- ✅ Mobile Chrome
- ✅ Mobile Safari

## 统计

- 测试文件: 6个
- 测试用例: 65+个
- 辅助函数: 14个
- 浏览器: 5种
