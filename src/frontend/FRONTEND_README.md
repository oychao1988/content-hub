# ContentHub 前端项目

这是 ContentHub 内容运营管理系统的前端项目，基于 Vue 3 + Vite + Element Plus 构建。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **图标**: Element Plus Icons

## 项目结构

```
src/
├── api/                    # API 模块
│   └── modules/           # API 接口模块
│       ├── auth.js        # 认证相关
│       ├── accounts.js    # 账号管理
│       ├── content.js     # 内容管理
│       ├── publisher.js   # 发布管理
│       ├── publishPool.js # 发布池
│       ├── scheduler.js   # 定时任务
│       ├── dashboard.js   # 仪表盘
│       ├── users.js       # 用户管理
│       ├── customers.js   # 客户管理
│       └── platforms.js   # 平台管理
├── assets/                # 静态资源
│   └── styles/           # 样式文件
│       └── global.css    # 全局样式
├── components/            # 组件
│   ├── common/           # 通用组件
│   │   ├── PageHeader.vue    # 页面头部
│   │   ├── DataTable.vue     # 数据表格
│   │   ├── SearchForm.vue    # 搜索表单
│   │   └── ConfirmDialog.vue # 确认对话框
│   ├── business/         # 业务组件
│   └── ui/              # UI 组件
├── config/              # 配置文件
│   └── index.js        # 应用配置
├── layouts/            # 布局组件
│   └── MainLayout.vue # 主布局
├── pages/              # 页面组件
│   ├── Login.vue           # 登录页
│   ├── Dashboard.vue       # 仪表盘
│   ├── AccountManage.vue   # 账号管理
│   ├── ContentManage.vue   # 内容管理
│   ├── PublishManage.vue   # 发布管理
│   ├── SchedulerManage.vue # 定时任务
│   ├── PublishPool.vue     # 发布池
│   ├── UserManage.vue      # 用户管理
│   ├── CustomerManage.vue  # 客户管理
│   ├── PlatformManage.vue  # 平台管理
│   └── SystemConfig.vue    # 系统配置
├── router/             # 路由配置
│   └── index.js       # 路由定义
├── stores/            # 状态管理
│   └── modules/      # Store 模块
│       ├── user.js   # 用户 store
│       └── app.js    # 应用 store
├── utils/            # 工具函数
│   └── request.js   # HTTP 请求封装
├── App.vue          # 根组件
└── main.js          # 入口文件
```

## 功能特性

### 已实现功能

1. **用户认证**
   - 登录/登出
   - Token 管理
   - 权限验证

2. **仪表盘**
   - 统计数据展示
   - 最近活动列表
   - 趋势图表（占位）

3. **账号管理**
   - 账号列表（支持搜索、分页）
   - 创建/编辑/删除账号
   - 批量删除
   - 同步账号状态

4. **内容管理**
   - 内容列表（支持搜索、分页）
   - 创建/编辑/删除内容
   - AI 生成内容
   - 批量操作

5. **发布管理**
   - 发布记录列表
   - 重试发布
   - 取消发布
   - 发布统计

6. **定时任务**
   - 任务列表
   - 创建/编辑/删除任务
   - 启动/停止/暂停/恢复任务
   - 立即执行任务

7. **发布池**
   - 发布池列表
   - 添加到发布池
   - 批量发布
   - 清空已发布项

8. **系统管理**
   - 用户管理（管理员）
   - 客户管理（管理员）
   - 平台管理（管理员）
   - 系统配置（管理员）

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 环境配置

### 开发环境 (.env.development)

```
VITE_API_BASE_URL=http://localhost:8000
```

### 生产环境 (.env.production)

```
VITE_API_BASE_URL=https://api.your-domain.com
```

## 默认账号

```
用户名: admin
密码: 123456
```

## 主要组件说明

### PageHeader

页面头部组件，包含标题和操作按钮。

```vue
<page-header title="页面标题" icon="IconName">
  <el-button>操作按钮</el-button>
</page-header>
```

### DataTable

数据表格组件，支持分页、选择、排序等功能。

```vue
<data-table
  :data="tableData"
  :total="total"
  :loading="loading"
  @page-change="handlePageChange"
  @size-change="handleSizeChange"
>
  <el-table-column prop="name" label="名称" />
</data-table>
```

### SearchForm

搜索表单组件，支持自定义搜索字段。

```vue
<search-form v-model="searchForm" @search="handleSearch">
  <template #default>
    <el-col :span="6">
      <el-form-item label="关键词">
        <el-input v-model="searchForm.keyword" />
      </el-form-item>
    </el-col>
  </template>
</search-form>
```

## 路由说明

- `/login` - 登录页面
- `/` - 仪表盘（需要认证）
- `/accounts` - 账号管理
- `/content` - 内容管理
- `/publisher` - 发布管理
- `/scheduler` - 定时任务
- `/publish-pool` - 发布池
- `/users` - 用户管理（管理员）
- `/customers` - 客户管理（管理员）
- `/platforms` - 平台管理（管理员）
- `/config` - 系统配置（管理员）

## 权限说明

### 用户角色

- **admin**: 管理员，拥有所有权限
- **operator**: 运营人员，只能访问基本功能

### 权限控制

路由权限通过 `meta.permissions` 和 `meta.role` 配置：

```javascript
{
  path: 'users',
  meta: {
    title: '用户管理',
    permissions: ['users:read'],
    role: 'admin'
  }
}
```

## API 请求

所有 API 请求统一使用 `src/utils/request.js` 封装的 axios 实例。

### 请求拦截器

自动添加 Authorization header：

```javascript
headers.Authorization = `Bearer ${token}`
```

### 响应拦截器

统一处理错误响应：

- 401: 未授权，跳转登录
- 403: 无权限
- 404: 资源不存在
- 422: 表单验证错误
- 500: 服务器错误

## 状态管理

### User Store

用户相关状态和方法：

```javascript
import { useUserStore } from '@/stores/modules/user'

const userStore = useUserStore()

// 登录
await userStore.login({ username, password })

// 登出
await userStore.logout()

// 检查权限
userStore.hasPermission('users:read')
```

### App Store

应用全局状态：

```javascript
import { useAppStore } from '@/stores/modules/app'

const appStore = useAppStore()

// 切换侧边栏
appStore.toggleSidebar()

// 设置主题
appStore.setTheme('dark')
```

## 样式规范

### 全局样式变量

定义在 `src/assets/styles/global.css`：

```css
:root {
  --primary-color: #409eff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --info-color: #909399;
}
```

### 工具类

- `.text-center` - 居中对齐
- `.mt-10` / `.mt-20` - 上边距
- `.mb-10` / `.mb-20` - 下边距
- `.text-primary` / `.text-success` - 文字颜色

## 注意事项

1. **API 地址**: 确保后端服务运行在 `http://localhost:8000`
2. **CORS**: 开发环境已配置代理，生产环境需要后端配置 CORS
3. **Token 过期**: Token 过期后会自动跳转到登录页
4. **权限验证**: 部分页面需要特定权限才能访问

## 开发建议

1. 使用 Vue 3 Composition API 编写组件
2. 使用 `<script setup>` 语法糖
3. 组件命名使用 PascalCase
4. 文件夹命名使用 kebab-case
5. 合理使用 Element Plus 组件
6. 注意响应式设计，适配移动端

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## License

MIT
