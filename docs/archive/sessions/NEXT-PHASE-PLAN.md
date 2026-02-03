# ContentHub 下一阶段开发计划

**计划版本**: v2.0
**制定日期**: 2026-01-29
**当前完成度**: 65%
**目标完成度**: 85%

---

## 📋 计划概述

基于当前项目进展（65% 完成度），本计划涵盖**优先级 2-4**的开发任务，旨在将项目完成度提升至 **85%**，重点关注用户体验优化、质量保证和生产部署准备。

---

## 🎯 总体目标

### 短期目标（1-2 周）
- 完成前端权限控制系统
- 实现内容预览组件
- 建立缓存策略机制

### 中期目标（2-3 周）
- 搭建完整的测试体系
- 实现单元测试和集成测试
- 覆盖率达到 70% 以上

### 长期目标（3-4 周）
- 完成 Docker 容器化部署
- 实现 Nginx 反向代理配置
- 建立数据库备份恢复机制
- 系统上线准备

---

## 📊 阶段划分

### 阶段 1: 用户体验优化 [优先级 2]

#### 阶段 1.1: 前端权限控制实现
- **目标**: 实现基于角色的 UI 显示控制
- **预计时间**: 2 天
- **详细描述**:

  **后端实现**:
  1. 创建权限装饰器 (`app/core/permissions.py`)
     - `require_role()` - 角色要求装饰器
     - `require_permission()` - 权限要求装饰器
     - `has_permission()` - 权限检查函数

  2. 完善用户权限模型
     - 扩展 User 模型（permissions 字段为 JSON）
     - 创建 Permission 枚举
     - 实现权限检查逻辑

  3. API 权限中间件
     - 集成到现有端点
     - 支持资源和操作级权限

  **前端实现**:
  1. 权限 Store (`stores/permissions.js`)
     - 用户权限缓存
     - 权限检查函数
     - 权限更新机制

  2. 权限指令 (`directives/permission.js`)
     - v-permission 指令
     - v-role 指令
     - 支持权限和角色判断

  3. 路由守卫 (`router/guards.js`)
     - 页面级权限检查
     - 自动跳转到无权限页面
     - 动态菜单过滤

  4. 权限控制组件
     - PermissionButton（有权限才显示）
     - PermissionView（有权限才渲染）
     - RoleSwitcher（角色切换，开发调试用）

- **完成标准**:
  - 不同角色看到不同的菜单
  - 无权限按钮自动隐藏或禁用
  - 访问受限页面自动跳转
  - 权限检查不影响性能

- **验证方式**:
  - 创建测试账号（admin, operator, customer）
  - 验证各角色权限
  - 测试权限继承和覆盖

#### 阶段 1.2: 内容预览组件开发
- **目标**: 实现 Markdown 内容和图片预览功能
- **预计时间**: 1.5 天
- **详细描述**:

  **组件开发**:
  1. MarkdownPreview 组件
     - 支持 Markdown 渲染
     - 代码高亮
     - 图片显示
     - 支持编辑模式切换

  2. ContentEditor 组件（增强版）
     - 集成 Markdown 预览
     - 实时预览（分屏或切换）
     - 工具栏（加粗、斜体、列表等）
     - 图片上传和预览

  3. ImagePreview 组件
     - 大图预览（点击放大）
     - 图片裁剪功能
     - 批量图片预览

  4. 集成到现有页面
     - ContentManage.vue
     - ContentDetail.vue（新建）

- **完成标准**:
  - Markdown 渲染正确显示
  - 实时预览流畅无卡顿
  - 图片预览支持缩放和裁剪
  - 编辑器和预览切换无缝

- **依赖库**:
  - `markdown-it` 或 `milkdown`（Markdown 解析）
  - `highlight.js`（代码高亮）
  - `vue-markdown` 或自定义实现

#### 阶段 1.3: 缓存策略实现
- **目标**: 实现配置缓存和查询缓存，提升系统性能
- **预计时间**: 2 天
- **详细描述**:

  **后端缓存**:
  1. 缓存管理器 (`app/core/cache.py` 扩展)
     - 内存缓存实现（使用 `functools.lru_cache`）
     - 缓存键生成
     - TTL 管理
     - 缓存失效

  2. 缓存装饰器
     - `@cache_query()` - 查询结果缓存
     - `@cache_config()` - 系统配置缓存
     - 支持自定义 TTL

  3. 缓存失效策略
     - 数据更新时主动失效
     - 定时自动失效
     - 标签化批量失效

  **前端缓存**:
  1. API 响应缓存
     - GET 请求缓存
     - 缓存键管理
     - 缓存更新

  2. 数据状态缓存
     - 列表数据缓存
     - 用户信息缓存
     - 配置数据缓存

  3. 缓存工具
     - Pinia 插件持久化（已有）
     - localStorage 封装
     - sessionStorage 封装

- **缓存场景**:
  | 数据类型 | 缓存时长 | 失效策略 |
  |---------|---------|---------|
  | 系统配置 | 1 小时 | 配置更新时 |
  | 用户权限 | 30 分钟 | 权限变更时 |
  | 写作风格 | 1 小时 | 风格更新时 |
  | 内容主题 | 1 小时 | 主题更新时 |
  | 平台配置 | 30 分钟 | 平台更新时 |
  | 账号列表 | 5 分钟 | 数据变更时 |
  | 内容列表 | 2 分钟 | 数据变更时 |

- **完成标准**:
  - 缓存命中率达到 60% 以上
  - 缓存更新及时无延迟
  - 缓存失效逻辑正确
  - 性能提升可测量

---

### 阶段 2: 质量保证体系 [优先级 3]

#### 阶段 2.1: 单元测试
- **目标**: 搭建测试框架，编写单元测试，覆盖率达到 70%
- **预计时间**: 3-4 天
- **详细描述**:

  **测试框架搭建**:
  1. 配置 pytest（已有 pytest.ini）
  2. 安装测试依赖
     - pytest-asyncio（异步测试）
     - pytest-cov（覆盖率）
     - pytest-mock（Mock）
     - httpx（HTTP 客户端测试）
  3. 配置测试环境
     - 测试数据库（内存 SQLite）
     - 测试配置文件
     - Fixture 定义

  **服务层测试**:
  1. 核心服务测试
     - AccountService 测试
     - ContentService 测试
     - PublisherService 测试
     - SchedulerService 测试
     - PublishPoolService 测试

  2. 外部服务测试
     - ContentCreatorService Mock 测试
     - ContentPublisherService Mock 测试

  3. 工具函数测试
     - 验证函数测试
     - 工具类测试

  **API 测试**:
  1. 端点测试
     - 使用 TestClient 测试所有端点
     - 验证请求和响应
     - 测试权限控制

  2. 集成测试
     - 数据库操作测试
     - 事务测试
     - 并发测试

- **测试用例示例**:
  ```python
  def test_create_writing_style(db):
      style = WritingStyleCreate(
          name="测试风格",
          code="test_style",
          tone="专业"
      )
      result = writing_style_service.create_writing_style(db, style.dict())
      assert result.id is not None
      assert result.code == "test_style"
  ```

- **完成标准**:
  - 测试框架正常运行
  - 核心业务逻辑覆盖率 ≥ 80%
  - 整体覆盖率 ≥ 70%
  - 所有测试通过

#### 阶段 2.2: 集成测试和端到端测试
- **目标**: 测试完整业务流程和用户交互
- **预计时间**: 2-3 天
- **详细描述**:

  **集成测试**:
  1. API 集成测试
     - 测试完整的请求流程
     - Mock 外部服务
     - 测试数据持久化

  2. 业务流程测试
     - 内容生成完整流程
     - 内容发布流程
     - 定时任务调度

  **端到端测试**（可选，如时间允许）:
  1. 使用 Playwright 或 Cypress
  2. 测试关键用户场景
     - 登录和登出
     - 内容创建
     - 内容发布

- **完成标准**:
  - 所有主要业务流程有测试覆盖
  - 集成测试通过
  - 发现并修复至少 5 个 bug

---

### 阶段 3: 生产部署准备 [优先级 4]

#### 阶段 3.1: Docker 容器化
- **目标**: 将应用容器化，便于部署和管理
- **预计时间**: 2 天
- **详细描述**:

  **后端 Dockerfile**:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8000
  CMD ["python", "main.py"]
  ```

  **前端 Dockerfile**:
  ```dockerfile
  FROM node:18-alpine as build
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  RUN npm run build

  FROM nginx:alpine
  COPY --from=build /app/dist /usr/share/nginx/html
  EXPOSE 80
  ```

  **docker-compose.yml**:
  ```yaml
  version: '3.8'
  services:
    backend:
      build: ./src/backend
      ports:
        - "8000:8000"
      environment:
        - DATABASE_URL=sqlite:///data/contenthub.db
      volumes:
        - ./data:/app/data
      depends_on:
        - db

    frontend:
      build: ./src/frontend
      ports:
        - "80:80"
      depends_on:
        - backend

    db:
      image: postgres:15-alpine  # 可选：生产环境使用 PostgreSQL
      environment:
        - POSTGRES_DB=contenthub
        - POSTGRES_USER=contenthub
        - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      volumes:
        - postgres_data:/var/lib/postgresql/data
  ```

- **完成标准**:
  - Docker 镜像成功构建
  - docker-compose up 一键启动
  - 容器间网络通信正常
  - 数据持久化正常

#### 阶段 3.2: Nginx 反向代理配置
- **目标**: 配置 Nginx 作为反向代理，统一前后端访问
- **预计时间**: 1 天
- **详细描述**:

  **nginx.conf**:
  ```nginx
  server {
      listen 80;
      server_name localhost;

      # 前端静态文件
      location / {
          root /usr/share/nginx/html;
          try_files $uri $uri/ /index.html;
      }

      # API 反向代理
      location /api/ {
          proxy_pass http://backend:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;

          # WebSocket 支持（如果需要）
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
      }

      # API 文档
      location /docs {
          proxy_pass http://backend:8000;
      }
      location /redoc {
          proxy_pass http://backend:8000;
      }
  }
  ```

  **SSL 配置**（可选，使用 Let's Encrypt）:
  ```nginx
  server {
      listen 443 ssl http2;
      server_name your-domain.com;

      ssl_certificate /etc/nginx/ssl/cert.pem;
      ssl_certificate_key /etc/ssl/key.pem;

      # ... 其他配置同上
  }
  ```

- **完成标准**:
  - Nginx 配置文件正确
  - 前后端通过统一域名访问
  - 支持 WebSocket（如需要）
  - SSL 证书配置（可选）

#### 阶段 3.3: 数据库备份和恢复
- **目标**: 建立可靠的备份和恢复机制
- **预计时间**: 1 天
- **详细描述**:

  **备份脚本** (`scripts/backup.sh`):
  ```bash
  #!/bin/bash
  BACKUP_DIR="/backup"
  DATE=$(date +%Y%m%d_%H%M%S)

  # 数据库备份
  sqlite3 data/contenthub.db ".backup $BACKUP_DIR/contenthub_$DATE.db"

  # 文件备份
  rsync -av accounts/ "$BACKUP_DIR/accounts_$DATE/"

  # 压缩备份
  tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" "$BACKUP_DIR/*_$DATE/"

  # 清理 30 天前的备份
  find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete
  ```

  **恢复脚本** (`scripts/restore.sh`):
  ```bash
  #!/bin/bash
  BACKUP_FILE=$1

  # 解压备份
  tar -xzf $BACKUP_FILE -C /tmp

  # 恢复数据库
  cp /tmp/data/contenthub.db data/contenthub.db

  # 恢复文件
  rsync -av /tmp/accounts/ accounts/
  ```

  **定时备份**（Cron Job）:
  ```cron
  # 每天凌晨 2 点执行备份
  0 2 * * * /path/to/backup.sh
  ```

- **完成标准**:
  - 备份脚本可正常执行
  - 恢复脚本测试通过
  - 定时任务配置完成
  - 备份文件可正常恢复

#### 阶段 3.4: 环境配置和监控
- **目标**: 完善生产环境配置，添加监控
- **预计时间**: 1 天
- **详细描述**:

  **环境配置文件**:
  1. `.env.production` 模板
  2. `.env.example` 更新
  3. 环境变量文档

  **监控配置**:
  1. 日志轮转配置
  2. 性能监控（Prometheus + Grafana，可选）
  3. 错误告警（邮件或 Webhook）

  **健康检查**:
  1. `/health` 端点
  2. 数据库连接检查
  3. 外部服务可用性检查

- **完成标准**:
  - 环境配置清晰完整
  - 基础监控可用
  - 健康检查端点正常

---

## 📅 时间规划

### 第 1-2 周：用户体验优化
- 第 1-2 天：前端权限控制
- 第 3-4 天：内容预览组件
- 第 5-6 天：缓存策略实现
- 第 7 天：集成测试和优化

### 第 3-4 周：质量保证
- 第 1-2 天：测试框架搭建
- 第 3-6 天：单元测试编写
- 第 7-9 天：集成测试编写
- 第 10 天：测试修复和优化

### 第 5-6 周：生产部署
- 第 1-2 天：Docker 容器化
- 第 3 天：Nginx 配置
- 第 4 天：备份恢复脚本
- 第 5 天：环境配置和监控
- 第 6-10 天：测试和调优

---

## 🎯 里程碑

| 里程碑 | 目标 | 预计时间 | 验收标准 |
|--------|------|----------|----------|
| M1 | 权限控制完成 | 第 1 周末 | 不同角色看到不同界面 |
| M2 | 内容预览上线 | 第 2 周初 | 可以预览和编辑内容 |
| M3 | 缓存系统启用 | 第 2 周末 | 性能提升可测量 |
| M4 | 测试覆盖达标 | 第 4 周末 | 覆盖率 ≥ 70% |
| M5 | Docker 部署就绪 | 第 5 周末 | 可一键启动 |
| M6 | 生产环境就绪 | 第 6 周末 | 可正式上线 |

---

## 📋 阶段 1 详细任务清单

### 1.1 前端权限控制（2 天）

#### Day 1: 后端权限系统
- [ ] 创建 `app/core/permissions.py`
  - [ ] 实现 `require_role()` 装饰器
  - [ ] 实现 `require_permission()` 装饰器
  - [ ] 实现 `has_permission()` 函数
- [ ] 扩展 User 模型
  - [ ] 添加 permissions JSON 字段（如需要）
  - [ ] 定义 Permission 枚举
- [ ] 创建权限中间件
  - [ ] 集成到现有端点
  - [ ] 编写权限测试
- [ ] 更新 API 端点权限
  - [ ] 账号管理端点（admin/operator）
  - [ ] 系统配置端点（admin only）
  - [ ] 用户管理端点（admin only）

#### Day 2: 前端权限控制
- [ ] 创建 `stores/permissions.js`
  - [ ] 权限 Store 定义
  - [ ] 权限检查 actions
  - [ ] 权限更新机制
- [ ] 创建权限指令
  - [ ] `v-permission` 指令
  - [ ] `v-role` 指令
  - [ ] 适应动态权限
- [ ] 更新路由守卫
  - [ ] 页面级权限检查
  - [ ] 动态菜单过滤
  - [ ] 权限错误处理
- [ ] 更新现有页面
  - [ ] 应用权限指令
  - [ ] 调整菜单显示
  - [ ] 测试不同角色

### 1.2 内容预览组件（1.5 天）

#### Day 1: Markdown 预览
- [ ] 创建 MarkdownPreview 组件
  - [ ] 集成 markdown-it
  - [ ] 添加代码高亮
  - [ ] 支持图片显示
  - [ ] 实现编辑模式切换
- [ ] 创建 ContentEditor 组件
  - [ ] 集成 Markdown 预览
  - [ ] 实现实时预览（分屏）
  - [ ] 添加工具栏
  - [ ] 支持图片上传
- [ ] 创建 ImagePreview 组件
  - [ ] 大图预览（点击放大）
  - [ ] 缩放控制
  - [ ] 旋转功能
  - [ ] 下载功能

#### Day 2: 集成和优化
- [ ] 集成到 ContentManage.vue
  - [ ] 添加预览按钮
  - [ ] 实现预览对话框
- [ ] 创建 ContentDetail.vue（可选）
  - [ ] 完整的内容详情页
  - [ ] 编辑和预览模式
- [ ] 测试和优化
  - [ ] 性能优化（大文件）
  - [ ] 样式调整
  - [ ] 移动端适配

### 1.3 缓存策略实现（2 天）

#### Day 1: 后端缓存
- [ ] 扩展 `app/core/cache.py`
  - [ ] 实现内存缓存管理器
  - [ ] 缓存键生成函数
  - [ ] TTL 管理函数
  - [ ] 缓存失效函数
- [ ] 创建缓存装饰器
  - [ ] `@cache_query()` 装饰器
  - [ ] `@cache_config()` 装饰器
  - [ ] 支持自定义 TTL
- [ ] 应用到关键服务
  - [ ] WritingStyleService 缓存
  - [ ] ContentThemeService 缓存
  - [ ] PlatformService 缓存
- [ ] 测试缓存功能
  - [ ] 验证缓存命中
  - [ ] 测试缓存失效
  - [ ] 性能对比测试

#### Day 2: 前端缓存
- [ ] 扩展 `stores/cache.js`
  - [ ] API 响应缓存
  - [ ] 缓存键管理
  - [ ] 缓存更新机制
- [ ] 创建缓存工具
  - [ ] localStorage 封装
  - [ ] sessionStorage 封装
  - [ ] 统一缓存接口
- [ ] 应用到关键页面
  - [ ] 账号列表缓存
  - [ ] 写作风格列表缓存
  - [ ] 内容主题列表缓存
- [ ] 测试和优化
  - [ ] 缓存一致性测试
  - [ ] 性能测试

---

## 📋 阶段 2 详细任务清单

### 2.1 单元测试（3-4 天）

#### Day 1: 测试框架搭建
- [ ] 安装测试依赖
  ```bash
  pip install pytest-asyncio pytest-cov pytest-mock httpx
  ```
- [ ] 配置 pytest
  - [ ] 更新 pytest.ini
  - [ ] 配置测试覆盖率
  - [ ] 配置测试路径
- [ ] 创建测试 Fixtures
  - [ ] `conftest.py` - 全局 fixtures
  - [ ] `db.py` - 数据库 fixture
  - [ ] `client.py` - 测试客户端
  - [ ] `auth.py` - 认证 fixture
- [ ] 创建 Mock 工具
  - [ ] 外部服务 Mock
  - [ ] 测试数据生成器

#### Day 2-3: 服务层测试
- [ ] AccountService 测试
  - [ ] CRUD 操作测试
  - [ ] 关联查询测试
  - [ ] 边界条件测试
- [ ] ContentService 测试
  - [ ] 内容生成测试
  - [ ] 状态更新测试
  - [ ] 删除操作测试
- [ ] PublisherService 测试
  - [ ] 发布流程测试
  - [ ] 错误处理测试
  - [ ] 重试机制测试
- [ ] SchedulerService 测试
  - [ ] 任务调度测试
  - [ ] 执行历史测试
- [ ] PublishPoolService 测试
  - [ ] 发布池管理测试
  - [ ] 批量发布测试

#### Day 4: API 测试
- [ ] 端点测试
  - [ ] 认证端点测试
  - [ ] 账号管理端点测试
  - [ ] 内容管理端点测试
  - [ ] 发布管理端点测试
- [ ] 权限测试
  - [ ] 角色权限测试
  - [ ] 资源权限测试
  - [ ] 跨租户隔离测试

### 2.2 集成测试（2-3 天）

#### Day 1: API 集成测试
- [ ] 创建测试客户端
- [ ] 测试完整请求流程
- [ ] Mock 外部服务
- [ ] 测试数据库事务

#### Day 2: 业务流程测试
- [ ] 内容生成流程
  - [ ] 选题 → 生成 → 审核 → 发布
- [ ] 定时任务流程
  - [ ] 任务创建 → 调度 → 执行
- [ ] 发布流程
  - [ ] 手动发布
  - [ ] 批量发布
  - [ ] 失败重试

#### Day 3: Bug 修复和优化
- [ ] 记录发现的问题
- [ ] 修复关键 bug
- [ ] 优化性能
- [ ] 更新测试用例

---

## 📋 阶段 3 详细任务清单

### 3.1 Docker 容器化（2 天）

#### Day 1: 后端容器化
- [ ] 创建后端 Dockerfile
- [ ] 创建 .dockerignore
- [ ] 创建健康检查脚本
- [ ] 测试镜像构建
- [ ] 测试容器运行

#### Day 2: 前端和编排
- [ ] 创建前端 Dockerfile
- [ ] 创建 docker-compose.yml
- [ ] 配置服务依赖
- [ ] 配置数据卷
- [ ] 配置网络
- [ ] 测试完整部署

### 3.2 Nginx 配置（1 天）

- [ ] 创建 nginx.conf
- [ ] 配置反向代理
- [ ] 配置静态文件服务
- [ ] 配置 WebSocket 支持
- [ ] 配置 Gzip 压缩
- [ ] 测试配置
- [ ] SSL 配置（可选）

### 3.3 备份恢复（1 天）

- [ ] 创建备份脚本
  - [ ] 数据库备份
  - [ ] 文件备份
  - [ ] 压缩和归档
- [ ] 创建恢复脚本
  - [ ] 数据库恢复
  - [ ] 文件恢复
  - [ ] 验证脚本
- [ ] 配置定时任务
  - [ ] Cron 配置
  - [ ] 日志记录
  - [ ] 失败告警
- [ ] 测试备份恢复
  - [ ] 模拟数据丢失
  - [ ] 执行恢复
  - [ ] 验证数据完整性

### 3.4 环境配置（1 天）

- [ ] 创建 .env.production 模板
- [ ] 更新 .env.example
- [ ] 环境变量文档
- [ ] 创建健康检查端点
- [ ] 配置日志轮转
- [ ] 配置性能监控
- [ ] 配置错误告警
- [ ] 测试环境配置

---

## 🔧 技术要求

### 开发规范
1. **代码风格**
   - Python: PEP 8
   - JavaScript: Vue 3 风格指南
   - 使用 ESLint 和 Prettier

2. **Git 规范**
   - 分支策略: feature/xxx, fix/xxx
   - 提交信息规范: feat/fix/docs/refactor/test
   - Code Review 要求

3. **测试规范**
   - 测试文件命名: test_*.py
   - 测试函数命名: test_*
   - Mock 外部服务
   - 测试数据隔离

### 质量标准
- **单元测试覆盖率**: ≥ 70%
- **API 响应时间**: P95 < 500ms
- **系统可用性**: > 99%
- **代码复用率**: 提升 20%

---

## 📊 验收标准

### 阶段 1 验收
- [ ] 不同角色看到不同菜单
- [ ] 无权限按钮自动隐藏或禁用
- [ ] 访问受限页面自动跳转
- [ ] 内容预览功能正常
- [ ] Markdown 渲染正确
- [ ] 缓存命中率达到 60% 以上

### 阶段 2 验收
- [ ] 测试覆盖率 ≥ 70%
- [ ] 所有测试通过
- [ ] 主要业务流程有集成测试
- [ ] 发现并修复至少 5 个 bug

### 阶段 3 验收
- [ ] Docker 镜像可正常构建
- [ ] docker-compose 一键启动成功
- [ ] Nginx 正确代理前后端
- [ ] 备份恢复测试通过
- [ ] 健康检查端点正常

---

## 🎯 成功指标

### 性能指标
- API 响应时间 P95 < 500ms
- 页面加载时间 < 2s
- 缓存命中率 > 60%
- 系统可用性 > 99%

### 质量指标
- 单元测试覆盖率 ≥ 70%
- 集成测试覆盖主要流程
- 关键路径有端到端测试
- 代码重复率 < 5%

### 功能指标
- 所有计划功能正常工作
- 用户体验流畅
- 权限控制正确
- 备份恢复可靠

---

## 🚧 风险管理

### 技术风险
| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 缓存一致性 | 高 | 主动失效 + 版本控制 |
| 权限复杂性 | 中 | 简化权限模型 + 充分测试 |
| 测试覆盖不足 | 中 | 强制覆盖率要求 + Code Review |
| Docker 兼容性 | 低 | 使用标准镜像 + 充分测试 |

### 时间风险
| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 时间估算不足 | 中 | 预留 20% 缓冲时间 |
| 依赖延期 | 低 | 使用稳定版本 |
| 需求变更 | 中 | 锁定下一阶段范围 |

---

## 📝 文档要求

### 阶段 1 文档
- 权限系统设计文档
- 权限使用指南
- 缓存使用文档

### 阶段 2 文档
- 测试指南
- Mock 工具文档
- 覆盖率报告

### 阶段 3 文档
- 部署手册
- 运维手册
- 备份恢复手册

---

## 📞 沟通机制

### 日常沟通
- 每日站会（15 分钟）
- 进展更新到 Git
- 问题及时同步

### 里程碑评审
- 每个阶段完成后
- 演示和验收
- 问题记录和跟进

### 变更管理
- 需求变更需要评估
- 重大变更需要更新计划
- 保持计划文档同步

---

**计划制定时间**: 2026-01-29
**计划执行周期**: 约 6 周
**预计完成时间**: 2026-03-15
**项目目标完成度**: 65% → 85%

**下一步**: 开始阶段 1.1 - 前端权限控制实现
