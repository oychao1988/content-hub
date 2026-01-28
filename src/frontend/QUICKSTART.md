# ContentHub 前端快速启动指南

## 一、安装依赖

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/frontend
npm install
```

## 二、配置环境

确保以下文件存在：
- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

默认配置：
- 开发环境 API: `http://localhost:8000`
- 前端端口: `5173`

## 三、启动项目

### 开发模式
```bash
npm run dev
```
访问: http://localhost:5173

### 生产构建
```bash
npm run build
```

### 预览构建
```bash
npm run preview
```

## 四、登录系统

默认账号：
- 用户名: `admin`
- 密码: `123456`

## 五、主要功能

### 仪表盘 (`/`)
- 查看统计数据
- 最近活动列表
- 趋势图表

### 账号管理 (`/accounts`)
- 创建发布账号
- 编辑账号信息
- 同步账号状态
- 删除账号

### 内容管理 (`/content`)
- 创建内容
- AI 生成内容
- 编辑内容
- 删除内容
- 管理内容状态

### 发布管理 (`/publisher`)
- 查看发布记录
- 重试失败发布
- 取消发布

### 定时任务 (`/scheduler`)
- 创建定时任务
- 启动/停止任务
- 立即执行任务

### 发布池 (`/publish-pool`)
- 添加到发布池
- 批量发布
- 清空已发布

### 管理功能（仅管理员）
- 用户管理 (`/users`)
- 客户管理 (`/customers`)
- 平台管理 (`/platforms`)
- 系统配置 (`/config`)

## 六、常见问题

### 1. 无法连接后端
- 检查后端是否运行在 `http://localhost:8000`
- 检查 `.env.development` 配置
- 查看浏览器控制台错误信息

### 2. 登录失败
- 确认后端已启动
- 确认用户名密码正确
- 检查网络请求状态

### 3. 权限不足
- 使用 admin 账号登录
- 检查用户角色配置

### 4. 页面空白
- 打开浏览器控制台查看错误
- 确认依赖已安装
- 尝试清除浏览器缓存

## 七、开发建议

### 1. 代码风格
- 使用 Vue 3 Composition API
- 使用 `<script setup>` 语法
- 遵循 ESLint 规则

### 2. 组件开发
- 优先使用 Element Plus 组件
- 复用通用组件
- 保持组件单一职责

### 3. API 调用
- 使用封装的 request 实例
- 统一错误处理
- 合理使用加载状态

### 4. 状态管理
- 复杂状态使用 Pinia
- 简单状态使用组件本地状态
- 合理使用持久化

## 八、目录结构

```
src/
├── api/              # API 接口
├── assets/           # 静态资源
├── components/       # 组件
│   ├── common/      # 通用组件
│   ├── business/    # 业务组件
│   └── ui/          # UI 组件
├── config/          # 配置
├── layouts/         # 布局
├── pages/           # 页面
├── router/          # 路由
├── stores/          # 状态管理
├── utils/           # 工具
├── App.vue          # 根组件
└── main.js          # 入口
```

## 九、更多文档

- 详细文档: `FRONTEND_README.md`
- 实现总结: `IMPLEMENTATION_SUMMARY.md`
- Element Plus: https://element-plus.org/
- Vue 3 文档: https://cn.vuejs.org/

## 十、技术支持

如有问题，请：
1. 查看浏览器控制台错误
2. 查后端日志
3. 参考官方文档
