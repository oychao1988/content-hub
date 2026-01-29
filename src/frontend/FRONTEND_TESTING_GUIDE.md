# ContentHub 前端测试指南

本文档说明如何运行和管理 ContentHub 前端测试。

## 测试环境

### 已安装的依赖

```json
{
  "vitest": "^4.0.18",
  "@vue/test-utils": "^2.4.6",
  "@vitest/ui": "^4.0.18",
  "@pinia/testing": "^1.0.3",
  "jsdom": "^27.4.0",
  "happy-dom": "^20.4.0",
  "msw": "^2.12.7",
  "@vitest/coverage-v8": "^4.0.18"
}
```

## 运行测试

### 方法 1: 从 src/frontend 目录运行（推荐）

```bash
cd src/frontend
npx vitest run
```

### 方法 2: 使用 npm scripts

```bash
# 在 src/frontend 目录下
npm run test          # 运行测试
npm run test:ui       # 运行测试（带 UI）
npm run test:coverage # 运行测试并生成覆盖率报告
```

## 测试文件结构

```
tests/
├── unit/
│   ├── components/       # 组件测试
│   │   ├── PermissionButton.test.js
│   │   ├── DataTable.test.js
│   │   ├── MarkdownPreview.test.js
│   │   ├── ContentEditor.test.js
│   │   └── ImagePreview.test.js
│   ├── stores/          # Store 测试
│   │   ├── user.test.js
│   │   └── cache.test.js
│   └── utils/           # 工具函数测试
│       └── request.test.js
├── integration/         # 集成测试（待添加）
└── setup.js            # 测试设置文件
```

## 测试统计

- **总测试文件**: 9 个
- **总测试用例**: 134 个
- **组件测试**: 71 个（5 个组件）
- **Store 测试**: 46 个（2 个 store）
- **API 测试**: 14 个

## 编写新测试

### 组件测试示例

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('应该正确渲染', () => {
    const wrapper = mount(MyComponent, {
      props: {
        title: 'Test'
      }
    })

    expect(wrapper.text()).toContain('Test')
  })
})
```

### Store 测试示例

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMyStore } from '@/stores/modules/my'

describe('My Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('应该正确初始化状态', () => {
    const store = useMyStore()
    expect(store.someState).toBeDefined()
  })
})
```

### API 测试示例

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/test', (req, res, ctx) => {
    return res(ctx.json({ data: 'test' }))
  })
)

describe('API Tests', () => {
  beforeEach(() => {
    server.listen()
  })

  afterEach(() => {
    server.resetHandlers()
  })

  it('应该正确处理 API 请求', async () => {
    const response = await fetch('/api/test')
    const data = await response.json()
    expect(data).toEqual({ data: 'test' })
  })
})
```

## 覆盖率报告

运行覆盖率测试：

```bash
npm run test:coverage
```

报告将生成在 `coverage/` 目录下。

## 常见问题

### Q: 测试无法找到模块？

A: 确保从 `src/frontend` 目录运行测试，或检查 `vitest.config.js` 中的路径别名配置。

### Q: Mock 不生效？

A: 检查 `tests/setup.js` 中的全局 mock 配置，或使用 `vi.mock()` 在测试文件中 mock。

### Q: 组件测试报错？

A: 确保使用 `global.stubs` stub 掉 Element Plus 组件：

```javascript
mount(MyComponent, {
  global: {
    stubs: {
      'el-button': true
    }
  }
})
```

## 参考资料

- [Vitest 文档](https://vitest.dev/)
- [Vue Test Utils 文档](https://test-utils.vuejs.org/)
- [Pinia Testing 文档](https://pinia.vuejs.org/cookbook/testing.html)
- [MSW 文档](https://mswjs.io/)
