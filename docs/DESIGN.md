## ContentHub 设计文档

**版本**: v1.2
**更新日期**: 2026-01-28
**架构基础**: omni-cast 模块注册系统

---

## 一、项目概述

### 1.1 项目简介

ContentHub 是一个通用的内容运营管理系统，专注于**多用户、多平台账号管理**和**自动化内容发布流程**。系统采用现代化技术栈，提供友好的用户界面和完整的自动化流程，帮助企业高效管理内容创作和发布。

### 1.2 核心价值主张

- **多账号统一管理**: 集中管理多个用户在多个平台的账号信息
- **精细权限控制**: 员工分管理权限和操作权限，客户拥有独立管理权限
- **跨平台发布**: 支持多个平台的内容发布流程，统一管理
- **系统级配置**: 提供系统级别的写作风格和主题，供客户选择
- **自动化流程**: 从内容生成到发布的完整自动化，提升效率

### 1.3 技术选型

**后端**:
- 框架: FastAPI 0.109.0
- 数据库: SQLite + SQLAlchemy 2.0
- 任务调度: APScheduler 3.10
- 模块系统: 复用 omni-cast 的模块注册系统
- 配置管理: Pydantic Settings

**前端**:
- 框架: Vue 3 + Vite
- UI 组件: Element Plus
- 状态管理: Pinia
- HTTP 客户端: Axios
- 路由: Vue Router

**集成服务**:
- content-creator: CLI 调用 (内容生成)
- content-publisher: HTTP API (内容发布，支持多平台)
- Tavily API: 选题搜索

---

## 二、核心设计理念

### 2.1 多账号管理体系

ContentHub 采用三层账号管理体系：

```
┌─────────────────────────────────────────────────┐
│  用户层              │
│  ├─ 员工用户                                        │
│  │   ├─ 管理员: 拥有所有权限，可管理系统和客户            │
│  │   └─ 操作员: 拥有操作权限，可管理账号和内容            │
│  └─ 客户用户                                        │
│      └─ 客户: 拥有自己的账号和内容管理权限               │
├─────────────────────────────────────────────────┤
│  客户层                │
│  ├─ 一个客户可以拥有多个平台账号                        │
│  ├─ 客户可以选择系统级的写作风格和主题                    │
│  └─ 客户可以配置自己的内容发布策略                        │
├─────────────────────────────────────────────────┤
│  平台账号层            │
│  ├─ 一个平台账号属于一个客户                            │
│  ├─ 每个平台账号对应一个具体的平台（微信公众号、头条等）       │
│  └─ 账号包含平台的认证信息和发布配置                      │
└─────────────────────────────────────────────────┘
```

### 2.2 权限管理矩阵

| 功能模块 | 管理员 | 操作员 | 客户 |
|---------|--------|--------|------|
| 用户管理 | ✅ | ❌ | ❌ |
| 客户管理 | ✅ | ❌ | ❌ |
| 平台管理 | ✅ | ✅ | ❌ |
| 账号管理 | ✅ | ✅ | ✅ (仅自己的账号) |
| 系统级配置 | ✅ | ❌ | ❌ |
| 写作风格选择 | ✅ | ✅ | ✅ |
| 主题选择 | ✅ | ✅ | ✅ |
| 内容生成 | ✅ | ✅ | ✅ (仅自己的账号) |
| 内容审核 | ✅ | ✅ | ✅ (仅自己的内容) |
| 内容发布 | ✅ | ✅ | ✅ (仅自己的账号) |
| 发布管理 | ✅ | ✅ | ✅ (仅自己的账号) |
| 定时任务 | ✅ | ✅ | ✅ (仅自己的账号) |
| 数据统计 | ✅ | ✅ | ✅ (仅自己的数据) |

### 2.3 平台发布流程

系统支持多个平台的统一发布管理：

1. **平台配置**: 管理员预先配置支持的平台信息（微信公众号、头条、知乎等）
2. **账号绑定**: 客户可以绑定多个平台的账号
3. **统一发布**: 所有平台的发布请求统一交给 content-publisher 处理
4. **平台适配**: content-publisher 根据不同平台的特性自动适配发布格式

### 2.4 系统级配置管理

**系统级写作风格**：
- 管理员预先创建多个写作风格模板
- 写作风格包含：语气、人格设定、字数要求、表情使用等
- 客户在创建账号时可以从系统级写作风格中选择

**系统级内容主题**：
- 管理员预先创建多个内容主题分类
- 主题包含：行业领域、内容类型、目标受众等
- 客户在配置账号时可以选择适合的主题

### 2.5 安全设计

#### 2.5.1 认证机制

**JWT 认证**：
- 使用 JSON Web Token 进行无状态认证
- Token 存储在 HttpOnly Cookie 中（防止 XSS）
- Access Token 有效期：2 小时
- Refresh Token 有效期：7 天
- 支持Token 刷新机制

**密码策略**：
- 密码长度要求：最少 8 位
- 必须包含大小写字母、数字
- 使用 bcrypt 进行密码哈希（cost factor = 12）
- 禁止重复使用最近 5 次的密码
- 支持密码重置（通过邮箱链接）

#### 2.5.2 数据安全

**敏感信息加密**：
- 微信公众号 AppSecret 使用 AES-256 加密存储
- API 密钥使用环境变量管理，不写入数据库
- 数据库连接字符串使用加密配置

**数据脱敏**：
- 日志中自动脱敏敏感信息（手机号、邮箱、Token）
- API 响应中不返回完整敏感信息
- 支持数据导出时的选择性脱敏

#### 2.5.3 API 安全

**CORS 配置**：
```
允许的源: 配置化（支持多域名）
允许的方法: GET, POST, PUT, DELETE, PATCH
允许的头部: Content-Type, Authorization
凭证支持: 是
最大缓存时间: 3600 秒
```

**请求验证**：
- 使用 Pydantic 进行请求参数验证
- SQL 注入防护（ORM 参数化查询）
- XSS 防护（前端输入转义）
- CSRF 防护（SameSite Cookie）
- 文件上传验证（类型、大小限制）

#### 2.5.4 权限控制

**基于角色的访问控制（RBAC）**：
- 预定义角色：admin、operator、customer
- 支持自定义权限
- 权限检查在 API 层面统一处理
- 支持资源级别的权限控制（客户只能访问自己的资源）

**权限检查流程**：
```
请求 → 认证 → 权限验证 → 资源所有权验证 → 业务处理
```

#### 2.5.5 安全审计

**审计日志**：
- 记录所有敏感操作（登录、数据修改、删除）
- 包含操作人、操作时间、操作内容、IP 地址
- 日志不可删除，只可追加
- 支持日志导出和分析

---

## 三、系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────┐
│  ContentHub 内容运营管理系统                     │
├─────────────────────────────────────────────────┤
│  前端 (Vue 3 + Element Plus)                    │
│  ├─ 登录页面                                     │
│  ├─ 首页 (仪表盘)                                 │
│  ├─ 用户管理页面                                 │
│  ├─ 客户管理页面                                 │
│  ├─ 平台管理页面                                 │
│  ├─ 账号管理页面                                 │
│  ├─ 内容管理页面                                 │
│  ├─ 发布管理页面                                 │
│  ├─ 定时任务页面                                 │
│  ├─ 发布池管理页面                               │
│  └─ 系统配置页面                                 │
├─────────────────────────────────────────────────┤
│  后端 API (FastAPI)                              │
│  ├─ 认证模块 (auth)                              │
│  ├─ 系统模块 (system)                            │
│  ├─ 共享模块 (shared)                            │
│  ├─ 用户管理模块 (users)                         │
│  ├─ 客户管理模块 (customers)                     │
│  ├─ 平台管理模块 (platforms)                     │
│  ├─ 账号管理模块 (accounts)                      │
│  ├─ 内容管理模块 (content)                       │
│  ├─ 定时任务模块 (scheduler)                     │
│  ├─ 发布管理模块 (publisher)                     │
│  ├─ 仪表盘模块 (dashboard)                       │
│  ├─ 发布池模块 (publish-pool)                    │
│  └─ 系统配置模块 (config)                        │
├─────────────────────────────────────────────────┤
│  外部服务集成                                     │
│  ├─ content-creator (内容生成)                   │
│  ├─ content-publisher (多平台内容发布)               │
│  └─ Tavily API (选题搜索)                       │
├─────────────────────────────────────────────────┤
│  数据库 (SQLite)                                 │
│  ├─ 用户信息表 (users)                           │
│  ├─ 客户信息表 (customers)                        │
│  ├─ 平台信息表 (platforms)                        │
│  ├─ 账号信息表 (accounts)                        │
│  ├─ 系统级写作风格表 (writing_styles)            │
│  ├─ 系统级内容主题表 (content_themes)             │
│  ├─ 内容板块配置表 (content_sections)             │
│  ├─ 数据源配置表 (data_sources)                   │
│  ├─ 发布配置表 (publish_configs)                  │
│  ├─ 内容表 (contents)                             │
│  ├─ 发布记录表 (publish_logs)                     │
│  └─ 定时任务表 (scheduled_tasks)                  │
└─────────────────────────────────────────────────┘
```

### 3.2 核心设计原则

1. **可插拔模块化架构**: 完全复用 omni-cast 的模块系统设计
2. **API 优先**: 所有功能通过 Web API 提供
3. **数据库优先**: 所有配置和数据存储在数据库，Markdown 仅用于备份
4. **简化流程**: content-creator 已包含图片生成和质量检查
5. **轻量部署**: 单机部署，SQLite 数据库，无需复杂配置
6. **权限细分**: 支持员工和客户角色，员工分为管理权限和操作权限
7. **多平台支持**: 统一发布流程，支持多个平台的内容发布
8. **系统级配置**: 写作风格和主题由管理员预配置，客户可选择使用

### 3.3 缓存策略

#### 3.3.1 缓存场景

**系统配置缓存**：
- 写作风格列表（TTL: 1 小时）
- 内容主题列表（TTL: 1 小时）
- 平台配置（TTL: 30 分钟）
- 缓存键格式：`config:{type}:{id}`

**用户会话缓存**：
- 用户基本信息（TTL: 30 分钟）
- 用户权限列表（TTL: 30 分钟）
- 缓存键格式：`session:{user_id}`

**数据查询缓存**：
- 账号列表（TTL: 5 分钟）
- 内容列表（TTL: 2 分钟）
- 缓存键格式：`query:{model}:{filters_hash}`

**API 响应缓存**：
- 仪表盘统计数据（TTL: 10 分钟）
- 发布统计信息（TTL: 5 分钟）
- 缓存键格式：`api:{endpoint}:{params_hash}`

#### 3.3.2 缓存实现

**缓存后端**：
- 内存缓存（使用 Python `functools.lru_cache`）
- 可扩展支持 Redis（用于分布式部署）

**缓存失效策略**：
- **主动失效**: 数据更新时删除相关缓存
- **被动失效**: TTL 到期自动删除
- **标签失效**: 支持按标签批量删除缓存

**缓存更新机制**：
```
读取缓存 → 缓存命中 → 返回数据
     ↓
   缓存未命中 → 查询数据库 → 写入缓存 → 返回数据

更新数据 → 删除相关缓存 → 下次读取时重建
```

#### 3.3.3 缓存配置

```python
# 缓存配置示例
CACHE_CONFIG = {
    "enabled": True,
    "default_ttl": 300,  # 默认 5 分钟
    "max_size": 1000,    # 最大缓存条目数
    "cache_backends": {
        "config": {"ttl": 3600},
        "session": {"ttl": 1800},
        "query": {"ttl": 120},
        "api": {"ttl": 600}
    }
}
```

---

## 四、功能需求

### 4.1 用户管理

#### 4.1.1 用户角色

**员工角色**:
- **管理员**: 拥有系统所有权限，包括用户管理、系统配置、内容审核等
- **操作员**: 拥有内容管理、账号管理、发布管理等操作权限，受管理员监督

**客户角色**:
- **客户**: 拥有自己的账号信息和内容管理权限，只能操作自己的内容

#### 4.1.2 用户功能

- 用户注册、登录
- 用户权限管理
- 密码重置
- 角色分配
- 用户状态管理
- 用户信息维护

### 4.2 客户管理

- 客户信息管理
- 客户与员工关联
- 客户状态管理
- 客户统计信息

### 4.3 平台管理

- 平台信息配置（支持微信公众号、头条、知乎等多个平台）
- 平台状态管理
- 平台类型管理
- 平台 API 配置
- 平台发布策略配置

### 4.4 账号管理

#### 4.4.1 核心功能

- 账号 CRUD 操作
- 配置同步 (Markdown ↔ 数据库)
- 账号切换和激活
- 账号配置管理 (写作风格、内容板块、数据源、发布配置)
- 客户与账号关联（一个客户可以拥有多个平台账号）
- 账号与平台关联关系管理

#### 4.4.2 配置管理

每个账号可以配置：
- **写作风格**: 从系统级写作风格中选择
- **内容板块**: 定义内容生成板块
- **数据源**: 配置选题数据源
- **发布配置**: 设置发布策略和审核模式

### 4.5 内容管理

- 内容生成 (调用 content-creator)
- 内容审核流程（自动/人工）
- 内容状态管理
- 内容编辑和删除
- 内容与账号关联

### 4.6 定时任务

- 任务调度器集成 (APScheduler)
- 任务管理和触发
- 执行历史记录
- 定时任务配置

### 4.7 发布管理

- 多平台内容发布（统一调用 content-publisher）
- 发布历史查询
- 发布状态跟踪
- 发布失败重试
- 平台适配（content-publisher 根据平台特性自动适配）

### 4.8 发布池

- 待发布内容管理
- 内容优先级调整
- 发布队列管理
- 批量发布功能

### 4.9 系统配置

#### 4.9.1 系统级写作风格管理

- 管理员创建和维护写作风格模板
- 写作风格包含：语气、人格设定、字数要求、表情使用、禁用词等
- 客户在创建账号时可以从系统级写作风格中选择

#### 4.9.2 系统级内容主题管理

- 管理员创建和维护内容主题分类
- 主题包含：行业领域、内容类型、目标受众等
- 客户在配置账号时可以选择适合的主题

#### 4.9.3 系统参数配置

- 系统级参数配置
- 外部服务配置
- 安全配置

### 4.10 数据分析

- 系统概览和关键指标
- 内容生成和发布趋势图
- 用户统计信息
- 客户统计信息
- 平台统计信息
- 快速操作入口

---

## 五、业务流程

### 5.1 内容生成流程

```
┌─────────────────────────────────────────────────┐
│  ContentHub 内容生成流程                          │
└─────────────────────────────────────────────────┘

1. 【选题阶段】（使用 Tavily API）
   ├─ 从数据库读取账号的 DataSource 配置
   ├─ 调用 Tavily API 检索最新内容
   ├─ 根据评分标准筛选选题
   └─ 保存选题到数据库

2. 【内容生成阶段】（使用 content-creator）
   ├─ 从数据库读取账号的 WritingStyle 和 ContentSection 配置
   ├─ 构建 requirements 参数（基于数据库配置）
   ├─ 调用 content-creator CLI
   │  ├─ 执行 pnpm run cli create
   │  └─ 解析 JSON 输出
   ├─ 输出: articleContent + imageUrl
   └─ 保存到数据库和文件系统

3. 【图片处理阶段】
   ├─ 从 imageUrl 下载图片到本地
   │  ├─ 保存到 accounts/{账号}/output/{日期}/images/
   │  └─ 验证文件大小和格式
   ├─ 创建 manifest.txt
   │  ├─ 记录图片信息（文件名、来源、用途）
   │  └─ 保存到同一 images/ 目录
   ├─ 更新文章图片引用
   │  └─ 将远程 URL 替换为 ./images/{文件名}
   └─ 保存最终文章到数据库和文件系统

4. 【内容审核阶段】
   ├─ 检查内容的 review_mode（审核模式）
   │
   ├─ 如果是 auto（自动通过，默认）：
   │   ├─ 自动标记为 review_status = "approved"
   │   ├─ 添加到发布池
   │   └─ 流程结束
   │
   └─ 如果是 manual（人工审核）：
   ├─ 标记为 review_status = "pending"
   ├─ 等待人工审核
   │  ├─ 审核通过：
   │  │  ├─ 标记为 review_status = "approved"
   │  │  ├─ 添加到发布池
   │  │  └─ 可选：发布到微信公众号草稿箱预览
   │  └─ 审核拒绝：
   │      ├─ 标记为 review_status = "rejected"
   │      ├─ 记录拒绝原因（review_comment）
   │      └─ 通知用户修改后重新提交
   └─ 返回待审核列表

5. 【发布池管理】
   ├─ 审核通过的内容进入发布池
   ├─ 支持调整发布优先级（priority 1-10）
   ├─ 支持设置计划发布时间（scheduled_at）
   ├─ 支持手动从发布池移除
   └─ 定时任务批量从发布池获取内容

6. 【批量发布阶段】（定时任务）
   ├─ 定时任务触发（如每 5 分钟执行一次）
   ├─ 从发布池按优先级获取待发布内容
   │  ├─ 优先级排序（priority 升序）
   │  ├─ 检查 scheduled_at（到达计划发布时间）
   │  └─ 限制单次批量数量（如 5 篇）
   ├─ 批量调用 content-publisher API 发布
   │  ├─ 更新状态为 publishing
   │  ├─ 发布成功：更新为 published，记录 media_id
   │  └─ 发布失败：更新为 failed，增加 retry_count
   └─ 失败内容进入重试队列

7. 【状态更新阶段】
   ├─ 更新数据库内容状态
   ├─ 创建发布记录（PublishLog）
   └─ 可选：更新 Markdown 文件作为备份
```

### 5.2 与外部服务的集成规范

#### 5.2.1 content-creator CLI 集成

**调用方式**：
- 使用 `subprocess` 模块调用 CLI
- 命令格式：`pnpm run cli create --requirements <json>`
- 工作目录：content-creator 项目根目录

**输入参数**：
```json
{
  "topic": "文章选题",
  "writingStyle": {
    "tone": "专业",
    "persona": "行业专家",
    "minWords": 800,
    "maxWords": 1500
  },
  "sections": [
    {
      "name": "引言",
      "modules": ["hook", "background"]
    }
  ],
  "dataSource": {
    "keywords": ["关键词1", "关键词2"],
    "url": "https://example.com"
  }
}
```

**输出格式**：
```json
{
  "success": true,
  "data": {
    "title": "文章标题",
    "content": "文章内容（Markdown）",
    "imageUrl": "https://example.com/image.jpg"
  }
}
```

**超时配置**：
- 默认超时：300 秒（5 分钟）
- 可配置超时时间

**错误处理**：
- 超时：终止进程，返回超时错误
- 非 0 退出码：记录错误日志，返回失败
- JSON 解析失败：记录原始输出，返回解析错误

#### 5.2.2 content-publisher API 集成

**API 端点**：
- 基础 URL：`{PUBLISHER_API_URL}/api/v1`
- 认证方式：API Key（Header: `X-API-Key`）

**发布接口**：
```
POST /publish/article
```

**请求参数**：
```json
{
  "platform": "wechat",
  "accountConfig": {
    "appId": "wx1234567890",
    "appSecret": "encrypted_secret"
  },
  "article": {
    "title": "文章标题",
    "content": "文章内容（HTML）",
    "coverImage": "base64_encoded_image",
    "author": "作者名称"
  },
  "publishMode": "draft"
}
```

**响应格式**：
```json
{
  "success": true,
  "data": {
    "mediaId": "media_id_xxxxx",
    "publishUrl": "https://mp.weixin.qq.com/...",
    "publishedAt": "2026-01-28T10:30:00Z"
  }
}
```

**超时配置**：
- 连接超时：10 秒
- 读取超时：60 秒

**重试机制**：
- 最大重试次数：3 次
- 重试间隔：指数退避（1s, 2s, 4s）
- 仅对网络错误和 5xx 错误重试

**降级策略**：
- 服务不可用：将内容标记为"待发布"，稍后重试
- 连续失败 5 次：暂停自动发布，发送告警通知

#### 5.2.3 Tavily API 集成

**API 端点**：
- 基础 URL：`https://api.tavily.com/search`
- 认证方式：API Key

**搜索接口**：
```
POST /search
```

**请求参数**：
```json
{
  "api_key": "{TAVILY_API_KEY}",
  "query": "搜索关键词",
  "search_depth": "basic",
  "max_results": 10,
  "include_images": false,
  "include_raw_content": false
}
```

**响应处理**：
- 提取标题、URL、摘要
- 计算相关性评分
- 按评分排序返回

**超时配置**：
- 连接超时：5 秒
- 读取超时：15 秒

**限流处理**：
- 遵守 API 速率限制
- 使用指数退避处理 429 错误

#### 5.2.4 通用集成规范

**配置管理**：
- 所有外部服务的 API 密钥存储在环境变量中
- 服务 URL 可配置，支持开发/测试/生产环境切换
- 提供服务健康检查接口

**日志记录**：
- 记录所有外部服务调用
- 包含请求参数、响应状态、耗时
- 敏感信息（API Key）脱敏记录

**监控告警**：
- 监控服务可用性
- 监控响应时间
- 监控错误率
- 异常情况发送告警

---

## 六、模块设计

### 6.1 模块系统架构

#### 6.1.1 模块接口定义

```python
# app/core/module_system/module.py
@dataclass(frozen=True)
class Module:
    name: str                    # 模块名称（如 "accounts"、"content"）
    router: APIRouter           # 模块的 API 路由
    startup: Optional[StartupFn] = None    # 启动时的钩子函数
    shutdown: Optional[ShutdownFn] = None  # 关闭时的钩子函数
```

#### 6.1.2 模块加载流程

```python
# app/core/module_system/loader.py
def load_modules(app: FastAPI, settings: Any) -> List[Module]:
    """动态加载所有启用的模块"""
    enabled = getattr(settings, "MODULES_ENABLED", []) or []
    modules: List[Module] = []

    for module_name in enabled:
        # 1. 动态导入模块的 module.py
        mod = importlib.import_module(f"app.modules.{module_name}.module")

        # 2. 获取 MODULE 对象
        module_obj = getattr(mod, "MODULE", None)

        # 3. 验证并注册模块
        if module_obj is not None and isinstance(module_obj, Module):
            app.include_router(module_obj.router, prefix=settings.API_STR)
            modules.append(module_obj)

    return modules
```

### 6.2 业务模块设计

#### 6.2.1 users 模块（用户管理）

**功能**:
- 用户 CRUD 操作
- 角色分配和权限管理
- 用户状态管理
- 密码重置

**结构**:
```
app/modules/users/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.2 customers 模块（客户管理）

**功能**:
- 客户 CRUD 操作
- 客户状态管理
- 客户与账号关联
- 客户统计信息

**结构**:
```
app/modules/customers/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.3 platforms 模块（平台管理）

**功能**:
- 平台 CRUD 操作
- 平台状态管理
- 平台 API 配置
- 平台发布策略配置

**结构**:
```
app/modules/platforms/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.4 accounts 模块（账号管理）

**功能**:
- 账号 CRUD 操作
- 配置同步（Markdown ↔ 数据库）
- 账号切换和激活
- 账号配置管理
- 客户与账号关联（一个客户可以拥有多个平台账号）
- 账号与平台关联关系管理

**结构**:
```
app/modules/accounts/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.5 content 模块（内容管理）

**功能**:
- 内容生成（调用 content-creator）
- 内容审核流程
- 内容状态管理

**结构**:
```
app/modules/content/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.6 scheduler 模块（定时任务）

**功能**:
- 任务调度器集成（APScheduler）
- 任务管理和触发
- 执行历史记录

**结构**:
```
app/modules/scheduler/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.7 publisher 模块（发布管理）

**功能**:
- 多平台内容发布（统一调用 content-publisher）
- 发布历史查询
- 发布状态跟踪
- 平台适配（content-publisher 根据平台特性自动适配）
- 发布失败重试

**结构**:
```
app/modules/publisher/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.8 dashboard 模块（仪表盘）

**功能**:
- 系统概览和关键指标
- 内容生成和发布趋势图
- 用户统计信息
- 客户统计信息
- 平台统计信息
- 快速操作入口

**结构**:
```
app/modules/dashboard/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.9 publish_pool 模块（发布池）

**功能**:
- 待发布内容管理
- 内容优先级调整
- 发布队列管理

**结构**:
```
app/modules/publish_pool/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

#### 6.2.10 config 模块（系统配置）

**功能**:
- 系统级写作风格管理（管理员创建，客户可选择）
- 系统级内容主题管理（管理员创建，客户可选择）
- 平台配置管理
- 系统参数配置

**结构**:
```
app/modules/config/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

---

## 七、数据设计

### 7.1 数据库设计原则

1. **单一真实数据源**: 所有配置和数据存储在 SQLite 数据库中
2. **混合配置**: Markdown 文件仅用于初始化导入和配置备份
3. **敏感信息加密**: 微信凭证和 API 密钥使用 AES 加密存储
4. **状态管理**: 内容状态通过数据库字段管理
5. **关系型数据**: 使用 SQLAlchemy ORM 管理数据关系

### 7.2 核心数据表

#### 7.2.1 users 表（用户信息表）

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="operator")  # admin, operator, customer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer = relationship("Customer", back_populates="users")
    roles = relationship("UserRole", back_populates="user")
    permissions = relationship("UserPermission", back_populates="user")
```

#### 7.2.2 customers 表（客户信息表）

```python
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    contact_name = Column(String(100), nullable=True)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    users = relationship("User", back_populates="customer")
    accounts = relationship("Account", back_populates="customer")
```

#### 7.2.3 platforms 表（平台信息表）

```python
class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    type = Column(String(50), nullable=True)
    description = Column(String(255), nullable=True)
    api_url = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    accounts = relationship("Account", back_populates="platform")
```

#### 7.2.4 accounts 表（账号信息表）

```python
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    name = Column(String(100), nullable=False)
    directory_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    wechat_app_id = Column(String(50), nullable=True)
    wechat_app_secret = Column(String(255), nullable=True)
    publisher_api_key = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    customer = relationship("Customer", back_populates="accounts")
    platform = relationship("Platform", back_populates="accounts")
    writing_style = relationship("WritingStyle", back_populates="account", uselist=False)
    content_sections = relationship("ContentSection", back_populates="account")
    data_sources = relationship("DataSource", back_populates="account")
    publish_config = relationship("PublishConfig", back_populates="account", uselist=False)
    contents = relationship("Content", back_populates="account")
```

#### 7.2.5 writing_styles 表（写作风格配置表）

```python
class WritingStyle(Base):
    __tablename__ = "writing_styles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    tone = Column(String(50), default="专业")
    persona = Column(Text, nullable=True)
    min_words = Column(Integer, default=800)
    max_words = Column(Integer, default=1500)
    emoji_usage = Column(String(20), default="适度")
    forbidden_words = Column(JSON, default=list)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account", back_populates="writing_style")
```

#### 7.2.6 content_themes 表（内容主题配置表）

```python
class ContentTheme(Base):
    __tablename__ = "content_themes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    publish_config = relationship("PublishConfig", back_populates="theme")
```

#### 7.2.7 content_sections 表（内容板块配置表）

```python
class ContentSection(Base):
    __tablename__ = "content_sections"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    word_count = Column(Integer, default=1000)
    update_frequency = Column(String(20), default="每日")
    publish_time = Column(String(50), nullable=True)
    modules = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="content_sections")
```

#### 7.2.8 data_sources 表（数据源配置表）

```python
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(50), default="rss")
    url = Column(String(255), nullable=True)
    strategy = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)
    scoring_criteria = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="data_sources")
```

#### 7.2.9 publish_configs 表（发布配置表）

```python
class PublishConfig(Base):
    __tablename__ = "publish_configs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True)
    theme_id = Column(Integer, ForeignKey("content_themes.id"), nullable=True)
    review_mode = Column(String(20), default="auto")
    publish_mode = Column(String(20), default="draft")
    auto_publish = Column(Boolean, default=False)
    publish_times = Column(JSON, default=list)
    section_theme_map = Column(JSON, default=dict)
    batch_settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="publish_config")
    theme = relationship("ContentTheme", back_populates="publish_config")
```

#### 7.2.10 contents 表（内容表）

```python
class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    image_path = Column(String(255), nullable=True)
    section_code = Column(String(50), nullable=True)
    review_mode = Column(String(20), default="auto")
    review_status = Column(String(20), default="pending")
    review_comment = Column(Text, nullable=True)
    publish_status = Column(String(20), default="draft")
    priority = Column(Integer, default=5)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="contents")
    publish_log = relationship("PublishLog", back_populates="content", uselist=False)
    pool_entry = relationship("PublishPool", back_populates="content", uselist=False)
```

#### 7.2.11 publish_logs 表（发布记录表）

```python
class PublishLog(Base):
    __tablename__ = "publish_logs"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False, unique=True)
    media_id = Column(String(255), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    content = relationship("Content", back_populates="publish_log")
```

#### 7.2.12 scheduled_tasks 表（定时任务表）

```python
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    task_type = Column(String(50), nullable=False)
    cron_expression = Column(String(50), nullable=True)
    interval = Column(Integer, nullable=True)
    interval_unit = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    last_run_time = Column(DateTime, nullable=True)
    next_run_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    executions = relationship("TaskExecution", back_populates="task")
```

#### 7.2.13 publish_pool 表（发布池表）

```python
class PublishPool(Base):
    __tablename__ = "publish_pool"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False, unique=True)
    priority = Column(Integer, default=5)
    scheduled_at = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    content = relationship("Content", back_populates="pool_entry")

    __table_args__ = (
        Index('idx_priority_scheduled', 'priority', 'scheduled_at'),
    )
```

---

## 八、API 设计

### 8.1 API 设计原则

1. **RESTful 风格**: 使用标准的 HTTP 方法
2. **统一前缀**: 所有 API 以 `/api/v1/` 为前缀
3. **模块化路由**: 每个业务模块有独立的路由前缀
4. **错误处理**: 统一的错误响应格式
5. **文档化**: 自动生成 Swagger 和 ReDoc 文档
6. **权限控制**: 基于角色和权限的访问控制

### 8.2 模块 API 前缀

| 模块名 | 路由前缀 | 说明 |
|--------|----------|------|
| auth | `/api/v1/auth` | 认证模块 |
| system | `/api/v1/system` | 系统模块 |
| users | `/api/v1/users` | 用户管理 |
| customers | `/api/v1/customers` | 客户管理 |
| platforms | `/api/v1/platforms` | 平台管理 |
| accounts | `/api/v1/accounts` | 账号管理 |
| content | `/api/v1/content` | 内容管理 |
| scheduler | `/api/v1/scheduler` | 定时任务 |
| publisher | `/api/v1/publisher` | 发布管理 |
| dashboard | `/api/v1/dashboard` | 仪表盘 |
| publish_pool | `/api/v1/publish-pool` | 发布池 |
| config | `/api/v1/config` | 系统配置 |

### 8.3 错误处理机制

#### 8.3.1 统一错误响应格式

**成功响应**：
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "email": "邮箱格式不正确"
    }
  },
  "requestId": "req_1234567890"
}
```

#### 8.3.2 HTTP 状态码规范

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 参数验证失败 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 外部服务错误 |
| 503 | Service Unavailable | 服务不可用 |

#### 8.3.3 业务错误码定义

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 用户名或密码错误 | 401 |
| `AUTH_TOKEN_EXPIRED` | Token 已过期 | 401 |
| `AUTH_INSUFFICIENT_PERMISSIONS` | 权限不足 | 403 |
| `VALIDATION_ERROR` | 参数验证失败 | 422 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 404 |
| `RESOURCE_CONFLICT` | 资源冲突 | 409 |
| `RESOURCE_ALREADY_EXISTS` | 资源已存在 | 409 |
| `RATE_LIMIT_EXCEEDED` | 请求过于频繁 | 429 |
| `EXTERNAL_SERVICE_ERROR` | 外部服务错误 | 502 |
| `INTERNAL_ERROR` | 内部错误 | 500 |

#### 8.3.4 错误日志记录

**日志级别**：
- ERROR: 系统错误、未捕获异常
- WARNING: 业务异常、外部服务错误
- INFO: 正常业务流程（如用户登录）

**日志内容**：
```
[ERROR] 2026-01-28 10:30:00 | req_1234567890 | GET /api/v1/users/999 | RESOURCE_NOT_FOUND | User 999 not found | IP: 192.168.1.100 | User: admin
```

### 8.4 API 限流

#### 8.4.1 限流策略

**基于用户的限流**：
- 管理员：1000 次/小时
- 操作员：500 次/小时
- 客户：200 次/小时

**基于 IP 的限流**：
- 单 IP：1000 次/小时

**基于端点的限流**：
- 登录接口：10 次/分钟
- 内容生成接口：20 次/小时
- 发布接口：100 次/小时

#### 8.4.2 限流算法

**令牌桶算法**：
- 桶容量：最大突发请求数
- 令牌生成速率：每秒补充的令牌数
- 请求处理：消耗 1 个令牌

**配置示例**：
```python
RATE_LIMIT_CONFIG = {
    "default": {
        "capacity": 100,      # 桶容量
        "refill_rate": 0.28   # 令牌/秒 (1000/小时)
    },
    "login": {
        "capacity": 10,
        "refill_rate": 0.17   # 10/分钟
    }
}
```

#### 8.4.3 限流响应

**响应头**：
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1706456400
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "retryAfter": 60
  }
}
```

#### 8.4.4 限流异常处理

**策略**：
- 返回 429 状态码
- 提供 Retry-After 响应头
- 记录限流事件日志

### 8.5 示例 API 接口

#### 8.5.1 用户管理接口

```
GET    /api/v1/users                    # 获取用户列表
GET    /api/v1/users/{id}               # 获取用户详情
POST   /api/v1/users                    # 创建用户
PUT    /api/v1/users/{id}               # 更新用户
DELETE /api/v1/users/{id}               # 删除用户
POST   /api/v1/users/{id}/reset-password # 重置密码
POST   /api/v1/users/{id}/assign-role   # 分配角色
POST   /api/v1/users/{id}/assign-permission # 分配权限
GET    /api/v1/users/me                 # 获取当前用户信息
```

#### 8.3.2 客户管理接口

```
GET    /api/v1/customers                # 获取客户列表
GET    /api/v1/customers/{id}           # 获取客户详情
POST   /api/v1/customers                # 创建客户
PUT    /api/v1/customers/{id}           # 更新客户
DELETE /api/v1/customers/{id}           # 删除客户
GET    /api/v1/customers/{id}/users     # 获取客户下的用户列表
GET    /api/v1/customers/{id}/accounts  # 获取客户下的账号列表
```

#### 8.3.3 平台管理接口

```
GET    /api/v1/platforms                # 获取平台列表
GET    /api/v1/platforms/{id}           # 获取平台详情
POST   /api/v1/platforms                # 创建平台
PUT    /api/v1/platforms/{id}           # 更新平台
DELETE /api/v1/platforms/{id}           # 删除平台
```

#### 8.3.4 账号管理接口

```
GET    /api/v1/accounts                 # 获取账号列表
GET    /api/v1/accounts/{id}            # 获取账号详情
POST   /api/v1/accounts                 # 创建账号
PUT    /api/v1/accounts/{id}            # 更新账号
DELETE /api/v1/accounts/{id}            # 删除账号
POST   /api/v1/accounts/{id}/import-md  # 从 Markdown 导入配置
POST   /api/v1/accounts/{id}/export-md  # 导出配置到 Markdown
POST   /api/v1/accounts/{id}/switch     # 切换活动账号
GET    /api/v1/accounts/{id}/writing-style # 获取写作风格配置
PUT    /api/v1/accounts/{id}/writing-style # 更新写作风格配置
```

#### 8.3.5 系统配置接口

```
GET    /api/v1/config/writing-styles    # 获取系统写作风格列表
POST   /api/v1/config/writing-styles    # 创建系统写作风格
PUT    /api/v1/config/writing-styles/{id} # 更新系统写作风格
DELETE /api/v1/config/writing-styles/{id} # 删除系统写作风格

GET    /api/v1/config/content-themes    # 获取系统内容主题列表
POST   /api/v1/config/content-themes    # 创建系统内容主题
PUT    /api/v1/config/content-themes/{id} # 更新系统内容主题
DELETE /api/v1/config/content-themes/{id} # 删除系统内容主题

GET    /api/v1/config/platforms         # 获取系统平台配置
POST   /api/v1/config/platforms         # 创建系统平台配置
PUT    /api/v1/config/platforms/{id}    # 更新系统平台配置
DELETE /api/v1/config/platforms/{id}    # 删除系统平台配置
```

---

## 九、部署方案

### 9.1 部署方式

**单机部署**:
- SQLite 数据库（无需额外安装）
- 前后端分离部署
- 建议使用 Nginx 反向代理整合

**Docker 部署**:
- 提供 Dockerfile 和 docker-compose.yml
- 支持环境变量配置
- 易于部署和维护

### 9.2 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `PUBLISHER_API_URL` | content-publisher 服务地址 | `http://150.158.88.23:3010` |
| `PUBLISHER_API_KEY` | content-publisher API 密钥 | - |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |
| `DEBUG` | 调试模式 | `false` |

### 9.3 服务器要求

- **CPU**: 2 核或以上
- **内存**: 4GB 或以上
- **存储**: 20GB 或以上（用于存储内容和图片）
- **网络**: 稳定的互联网连接

### 9.4 数据备份和恢复

#### 9.4.1 备份策略

**数据库备份**：
- **全量备份**：每天凌晨 2 点执行
- **增量备份**：每 4 小时执行一次
- **备份保留期**：30 天
- **备份存储**：本地存储 + 远程存储（可选）

**文件备份**：
- **内容文件**：每天备份
- **图片文件**：每周备份
- **配置文件**：每次修改后立即备份

**备份命令**：
```bash
# 数据库全量备份
cp data/contenthub.db backups/contenthub_$(date +%Y%m%d).db

# 数据库增量备份（使用 SQLite 在线备份 API）
python scripts/backup_db.py --type incremental

# 文件备份
rsync -av accounts/ backups/accounts_$(date +%Y%m%d)/
```

#### 9.4.2 备份验证

**自动验证**：
- 备份完成后自动校验文件完整性
- 每周执行一次恢复测试
- 验证失败发送告警通知

**验证脚本**：
```bash
# 验证备份完整性
python scripts/verify_backup.py --file backups/contenthub_20260128.db

# 恢复测试
python scripts/test_restore.py --backup backups/contenthub_20260128.db
```

#### 9.4.3 恢复流程

**数据库恢复**：
```bash
# 1. 停止服务
systemctl stop contenthub

# 2. 备份当前数据库（以防万一）
cp data/contenthub.db data/contenthub.db.failed

# 3. 恢复备份
cp backups/contenthub_20260128.db data/contenthub.db

# 4. 启动服务
systemctl start contenthub

# 5. 验证服务状态
curl http://localhost:8000/api/v1/system/health
```

**文件恢复**：
```bash
# 恢复账号文件
rsync -av backups/accounts_20260128/ accounts/
```

#### 9.4.4 灾难恢复

**RTO（恢复时间目标）**：1 小时
**RPO（恢复点目标）**：4 小时

**灾难恢复步骤**：
1. 评估损坏程度
2. 准备新服务器
3. 安装依赖环境
4. 恢复最新备份
5. 验证数据完整性
6. 切换 DNS/负载均衡
7. 监控系统运行

#### 9.4.5 备份监控

**监控指标**：
- 备份执行状态（成功/失败）
- 备份文件大小
- 备份耗时
- 存储空间使用率

**告警规则**：
- 备份失败：立即告警
- 存储空间不足 20%：提前告警
- 备份文件损坏：立即告警

---

## 十、日志策略

### 10.1 日志级别定义

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发调试 |
| INFO | 一般信息 | 正常业务流程 |
| WARNING | 警告信息 | 可恢复的异常 |
| ERROR | 错误信息 | 需要关注的错误 |
| CRITICAL | 严重错误 | 系统级故障 |

### 10.2 日志格式

**标准格式**：
```
[级别] 时间戳 | 请求ID | 模块 | 函数 | 消息 | 额外信息
```

**示例**：
```
[INFO] 2026-01-28 10:30:00 | req_1234567890 | accounts | create_account | Account created | account_id=1
[ERROR] 2026-01-28 10:31:00 | req_1234567891 | content | generate_content | Content generation failed | error=timeout
```

### 10.3 敏感信息脱敏

**自动脱敏规则**：
- 手机号：`138****1234`
- 邮箱：`u***@example.com`
- 身份证：`110101********1234`
- Token：`eyJhbGciOi...（省略中间）`
- API Key：`ak_****XYZ`

**脱敏配置**：
```python
LOG_MASKING_PATTERNS = {
    "phone": r"(\d{3})\d{4}(\d{4})",
    "email": r"(\w{1})[^@]*(@.*)",
    "token": r"(eyJ\w+\.)[^.]*(\.\w+)",
    "api_key": r"(ak_\w{2})\w*(\w{2})"
}
```

### 10.4 日志文件管理

**日志文件分类**：
- `app.log` - 应用主日志
- `error.log` - 错误日志
- `access.log` - 访问日志
- `audit.log` - 审计日志
- `scheduler.log` - 定时任务日志

**日志轮转策略**：
- 按大小轮转：单文件最大 100MB
- 按时间轮转：每天生成新文件
- 保留期限：30 天
- 压缩归档：超过 7 天的日志自动压缩

**轮转配置**：
```python
LOG_ROTATION_CONFIG = {
    "max_size": "100MB",
    "max_age": 30,          # 天
    "backup_count": 100,
    "compression": "gzip"
}
```

### 10.5 审计日志

**审计事件**：
- 用户登录/登出
- 数据创建/修改/删除
- 权限变更
- 配置修改
- 发布操作

**审计日志格式**：
```json
{
  "timestamp": "2026-01-28T10:30:00Z",
  "event": "user_login",
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success",
  "details": {
    "username": "admin"
  }
}
```

**审计日志特性**：
- 只追加，不可修改
- 独立存储，防止删除
- 支持导出和查询
- 定期归档到远程存储

### 10.6 日志监控和告警

**监控指标**：
- 错误日志数量
- 错误率趋势
- 响应时间分布
- 异常堆栈频率

**告警规则**：
- 1 分钟内出现 10 个 ERROR：立即告警
- 出现 CRITICAL 级别：立即告警
- 单个接口错误率超过 5%：告警
- 数据库连接失败：立即告警

---

## 十一、项目计划

### 11.1 实施阶段

#### 阶段一: 架构基础搭建 (预计 1 周)
- 项目架构设计
- 基础项目结构创建
- omni-cast 核心模块集成
- 数据库配置
- 模块系统架构设计

#### 阶段二: 模块基础结构完善 (预计 2 周)
- 各业务模块的 module.py、endpoints.py、services.py、models.py、schemas.py 创建
- 数据库迁移脚本创建
- 基础 API 测试

#### 阶段三: 核心功能实现 (预计 3 周)
- 用户管理功能实现
- 客户管理功能实现
- 平台管理功能实现
- 账号管理功能实现
- 内容管理功能实现
- 定时任务功能实现
- 发布管理功能实现
- 发布池功能实现

#### 阶段四: 系统配置功能实现 (预计 1 周)
- 写作风格管理功能实现
- 内容主题管理功能实现
- 平台配置管理功能实现
- 系统参数配置功能实现

#### 阶段五: 前端开发 (预计 3 周)
- Vue 3 项目初始化
- 组件库集成
- 路由配置
- 状态管理
- 页面开发
- API 集成
- 响应式设计

#### 阶段六: 测试与优化 (预计 2 周)
- 单元测试
- 集成测试
- 系统测试
- 性能优化
- 安全优化
- 文档完善

#### 阶段七: 部署与上线 (预计 1 周)
- 服务器环境配置
- 数据库部署
- 后端服务部署
- 前端静态文件部署
- 反向代理配置 (Nginx)
- 域名配置
- SSL 证书配置
- 系统监控配置

### 10.2 项目里程碑

- **Week 1**: 架构基础搭建完成
- **Week 3**: 模块基础结构完善完成
- **Week 6**: 核心功能实现完成
- **Week 7**: 系统配置功能实现完成
- **Week 10**: 前端开发完成
- **Week 12**: 测试与优化完成
- **Week 13**: 项目部署与上线

---

## 十二、测试策略

### 12.1 测试类型

#### 12.1.1 单元测试

**覆盖范围**：
- 所有服务层方法
- 工具函数
- 数据模型方法

**测试框架**：pytest

**覆盖率要求**：
- 核心业务逻辑：≥ 80%
- 工具函数：≥ 90%
- 整体覆盖率：≥ 70%

**示例**：
```python
def test_create_account():
    # Arrange
    account_data = {
        "name": "测试账号",
        "customer_id": 1,
        "platform_id": 1
    }

    # Act
    account = AccountService.create_account(account_data)

    # Assert
    assert account.id is not None
    assert account.name == "测试账号"
```

#### 12.1.2 集成测试

**测试场景**：
- API 端点测试
- 数据库操作测试
- 外部服务集成测试
- 模块间交互测试

**测试工具**：
- pytest + httpx
- 测试数据库（SQLite 内存数据库）
- Mock 外部服务

**示例**：
```python
async def test_create_account_api(client, db):
    response = await client.post(
        "/api/v1/accounts",
        json={
            "name": "测试账号",
            "customer_id": 1,
            "platform_id": 1
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "测试账号"
```

#### 12.1.3 端到端测试

**测试场景**：
- 完整的内容生成流程
- 完整的发布流程
- 用户登录和权限验证

**测试工具**：
- Playwright（前端自动化）
- Testcontainers（Docker 集成测试）

#### 12.1.4 性能测试

**测试指标**：
- API 响应时间
- 并发请求处理能力
- 数据库查询性能

**测试工具**：
- Locust（负载测试）
- pytest-benchmark（基准测试）

**性能要求**：
- GET 请求：< 200ms (P95)
- POST 请求：< 500ms (P95)
- 并发 100 用户：无错误

### 12.2 测试环境

**开发环境**：
- 本地测试数据库
- Mock 外部服务

**测试环境**：
- 独立的测试数据库
- 真实外部服务（测试账号）

**预生产环境**：
- 接近生产配置
- 使用真实数据副本

### 12.3 CI/CD 集成

**自动化测试流程**：
1. 代码提交 → 触发 CI
2. 运行单元测试（必须通过）
3. 运行集成测试（必须通过）
4. 生成覆盖率报告
5. 代码质量检查（linting）

**测试失败处理**：
- 阻止合并到主分支
- 发送通知给开发人员
- 记录测试结果

---

## 十三、前端设计规范

### 13.1 前端模块架构设计

#### 13.1.1 项目目录结构

基于 omni-cast 的模块化思想，ContentHub 前端采用以下目录结构：

```
src/frontend/src/
├── App.vue                    # 主应用组件
├── main.ts                    # 应用入口
├── assets/                    # 静态资源
│   ├── styles/
│   │   ├── global.css        # 全局样式
│   │   ├── variables.css     # CSS 变量
│   │   └── theme.css         # 主题配置
│   ├── images/               # 图片资源
│   └── icons/                # 图标资源
├── components/                # 组件目录
│   ├── common/               # 通用组件
│   │   ├── AppHeader.vue     # 应用头部
│   │   ├── AppSidebar.vue    # 应用侧边栏
│   │   ├── AppFooter.vue     # 应用底部
│   │   ├── Breadcrumb.vue    # 面包屑导航
│   │   └── LoadingSpinner.vue # 加载指示器
│   ├── business/             # 业务组件
│   │   ├── AccountSelector.vue     # 账号选择器
│   │   ├── ContentEditor.vue       # 内容编辑器
│   │   ├── PublishStatus.vue       # 发布状态
│   │   ├── SchedulePicker.vue      # 定时选择器
│   │   ├── WritingStyleEditor.vue  # 写作风格编辑器
│   │   └── ContentPreview.vue      # 内容预览
│   └── ui/                   # UI 基础组件
│       └── (基于 Element Plus 封装)
├── features/                 # 功能模块（参考 omni-cast）
│   ├── auth/                # 认证模块
│   │   ├── components/
│   │   │   ├── LoginForm.vue
│   │   │   └── RegisterForm.vue
│   │   ├── stores/
│   │   │   └── auth.ts
│   │   ├── api/
│   │   │   └── authApi.ts
│   │   └── types/
│   │       └── auth.ts
│   ├── dashboard/            # 仪表盘模块
│   │   ├── components/
│   │   │   ├── StatCard.vue
│   │   │   ├── TrendChart.vue
│   │   │   └── QuickActions.vue
│   │   ├── stores/
│   │   │   └── dashboard.ts
│   │   └── api/
│   │       └── dashboardApi.ts
│   ├── accounts/             # 账号管理模块
│   │   ├── components/
│   │   │   ├── AccountList.vue
│   │   │   ├── AccountForm.vue
│   │   │   ├── AccountConfig.vue
│   │   │   └── ConfigSync.vue
│   │   ├── stores/
│   │   │   └── accounts.ts
│   │   ├── api/
│   │   │   └── accountApi.ts
│   │   └── types/
│   │       └── account.ts
│   ├── content/              # 内容管理模块
│   │   ├── components/
│   │   │   ├── ContentList.vue
│   │   │   ├── ContentDetail.vue
│   │   │   ├── ContentGenerator.vue
│   │   │   ├── ContentReview.vue
│   │   │   └── ImageManager.vue
│   │   ├── stores/
│   │   │   └── content.ts
│   │   └── api/
│   │       └── contentApi.ts
│   ├── publisher/            # 发布管理模块
│   │   ├── components/
│   │   │   ├── PublishHistory.vue
│   │   │   ├── PublishStatus.vue
│   │   │   └── RetryQueue.vue
│   │   ├── stores/
│   │   │   └── publisher.ts
│   │   └── api/
│   │       └── publisherApi.ts
│   ├── scheduler/            # 定时任务模块
│   │   ├── components/
│   │   │   ├── TaskList.vue
│   │   │   ├── TaskForm.vue
│   │   │   └── TaskHistory.vue
│   │   └── stores/
│   │       └── scheduler.ts
│   ├── publish-pool/         # 发布池模块
│   │   ├── components/
│   │   │   ├── PoolList.vue
│   │   │   ├── PoolItem.vue
│   │   │   └── BatchPublish.vue
│   │   └── stores/
│   │       └── publishPool.ts
│   ├── users/                # 用户管理模块（管理员）
│   ├── customers/            # 客户管理模块（管理员）
│   ├── platforms/            # 平台管理模块（管理员）
│   └── config/               # 系统配置模块（管理员）
│       ├── components/
│       │   ├── WritingStyleList.vue
│       │   ├── WritingStyleForm.vue
│       │   ├── ContentThemeList.vue
│       │   └── SystemConfig.vue
│       └── stores/
│           └── config.ts
├── layouts/                  # 布局组件
│   ├── MainLayout.vue        # 主布局
│   ├── AuthLayout.vue        # 认证布局
│   └── BlankLayout.vue       # 空白布局
├── pages/                    # 页面组件
│   ├── Login.vue             # 登录页
│   ├── Dashboard.vue         # 仪表盘
│   ├── AccountManage.vue     # 账号管理
│   ├── ContentManage.vue     # 内容管理
│   ├── PublishManage.vue     # 发布管理
│   ├── SchedulerManage.vue   # 定时任务
│   ├── PublishPool.vue       # 发布池
│   ├── UserManage.vue        # 用户管理
│   ├── CustomerManage.vue    # 客户管理
│   ├── PlatformManage.vue    # 平台管理
│   └── SystemConfig.vue      # 系统配置
├── router/                   # 路由配置
│   ├── index.ts              # 路由主文件
│   ├── guards.ts             # 路由守卫
│   └── routes.ts             # 路由定义
├── stores/                   # Pinia 状态管理
│   ├── index.ts              # Store 入口
│   ├── modules/              # Store 模块
│   │   ├── user.ts
│   │   ├── app.ts
│   │   └── ...
│   └── plugins/              # Store 插件
│       └── persist.ts        # 持久化插件
├── api/                      # API 客户端
│   ├── index.ts              # Axios 实例配置
│   ├── interceptors.ts       # 请求/响应拦截器
│   ├── types.ts              # API 类型定义
│   └── modules/              # API 模块
│       ├── auth.ts
│       ├── account.ts
│       ├── content.ts
│       └── ...
├── composables/              # 组合式函数
│   ├── useAuth.ts            # 认证相关
│   ├── usePermission.ts      # 权限检查
│   ├── useTable.ts           # 表格操作
│   ├── useForm.ts            # 表单操作
│   └── usePagination.ts      # 分页操作
├── utils/                    # 工具函数
│   ├── request.ts            # 请求工具
│   ├── format.ts             # 格式化工具
│   ├── validate.ts           # 验证工具
│   ├── storage.ts            # 存储工具
│   └── constants.ts          # 常量定义
├── types/                    # TypeScript 类型定义
│   ├── common.ts             # 通用类型
│   ├── user.ts               # 用户类型
│   ├── account.ts            # 账号类型
│   ├── content.ts            # 内容类型
│   └── ...
├── directives/               # 自定义指令
│   ├── permission.ts         # 权限指令
│   └── loading.ts            # 加载指令
└── config/                   # 配置文件
    ├── app.ts                # 应用配置
    └── env.ts                # 环境配置
```

#### 13.1.2 模块注册系统（参考 omni-cast）

omni-cast 使用模块注册系统实现动态功能扩展。ContentHub 将使用类似的模式：

```typescript
// features/moduleTypes.ts
export interface FeatureModule {
  name: string                    // 模块名称
  routes: RouteRecordRaw[]         // 模块路由
  stores?: () => any               // 模块 Store
  components?: Record<string, any> // 模块组件
  apis?: Record<string, any>       // 模块 API
  permissions?: string[]           // 模块权限
  icon?: string                    // 模块图标
  order?: number                   // 菜单排序
}

// features/moduleRegistry.ts
import { FeatureModule } from './moduleTypes'
import { authModule } from './auth/module'
import { dashboardModule } from './dashboard/module'
import { accountsModule } from './accounts/module'
// ... 其他模块

// 模块注册表
const modules: FeatureModule[] = [
  authModule,
  dashboardModule,
  accountsModule,
  contentModule,
  publisherModule,
  schedulerModule,
  publishPoolModule,
  // 根据用户角色动态加载模块
]

// 获取所有启用的模块
export function getEnabledModules(userRole: string): FeatureModule[] {
  return modules.filter(m =>
    !m.permissions || m.permissions.some(p => hasPermission(p, userRole))
  )
}

// 获取模块路由
export function getModuleRoutes(userRole: string): RouteRecordRaw[] {
  return getEnabledModules(userRole).flatMap(m => m.routes || [])
}

// 获取模块菜单
export function getModuleMenus(userRole: string): MenuItem[] {
  return getEnabledModules(userRole)
    .filter(m => m.order !== undefined)
    .sort((a, b) => (a.order || 0) - (b.order || 0))
    .map(m => ({
      name: m.name,
      icon: m.icon,
      path: m.routes[0]?.path,
      order: m.order
    }))
}
```

#### 13.1.3 模块定义示例

```typescript
// features/accounts/module.ts
import { FeatureModule } from '../moduleTypes'
import { useAccountStore } from './stores/accounts'
import AccountList from './components/AccountList.vue'
import AccountForm from './components/AccountForm.vue'
import AccountConfig from './components/AccountConfig.vue'
import { accountApi } from './api/accountApi'

export const accountsModule: FeatureModule = {
  name: 'accounts',
  icon: 'User',
  order: 2,
  permissions: ['accounts:read', 'accounts:write'],
  routes: [
    {
      path: '/accounts',
      name: 'AccountManage',
      component: () => import('@/pages/AccountManage.vue'),
      meta: {
        title: '账号管理',
        requiresAuth: true,
        permissions: ['accounts:read']
      }
    },
    {
      path: '/accounts/:id',
      name: 'AccountDetail',
      component: () => import('@/pages/AccountDetail.vue'),
      meta: {
        title: '账号详情',
        requiresAuth: true,
        permissions: ['accounts:read']
      }
    }
  ],
  stores: () => ({
    useAccountStore
  }),
  components: {
    AccountList,
    AccountForm,
    AccountConfig
  },
  apis: {
    accountApi
  }
}
```

### 13.2 组件设计规范

#### 13.2.1 组件分类

**基础组件**：
- Button（按钮）
- Input（输入框）
- Select（选择器）
- Table（表格）
- Form（表单）
- Modal（弹窗）
- 等等（来自 Element Plus）

**业务组件**：
- AccountSelector（账号选择器）
- ContentEditor（内容编辑器）
- PublishStatus（发布状态）
- SchedulePicker（定时选择器）
- 等等

**页面组件**：
- LoginPage（登录页）
- DashboardPage（仪表盘）
- AccountManagePage（账号管理页）
- 等等

#### 13.1.2 组件命名规范

- 组件文件：PascalCase（如 `AccountSelector.vue`）
- 组件注册：PascalCase
- 组件引用：kebab-case（如 `<account-selector />`）

#### 13.1.3 组件结构

```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 1. 导入
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// 2. Props 定义
interface Props {
  modelValue: string
  disabled?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

// 3. Emits 定义
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}
const emit = defineEmits<Emits>()

// 4. 响应式数据
const localValue = ref(props.modelValue)

// 5. 计算属性
const isEmpty = computed(() => !localValue.value)

// 6. 方法
const handleChange = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 7. 生命周期
onMounted(() => {
  // 初始化逻辑
})
</script>

<style scoped>
/* 组件样式 */
</style>
```

### 13.2 状态管理设计

#### 13.2.1 Store 结构

**用户 Store**（stores/user.ts）：
```typescript
export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string>('')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(credentials: LoginCredentials) {
    const response = await authApi.login(credentials)
    user.value = response.data.user
    token.value = response.data.token
  }

  function logout() {
    user.value = null
    token.value = ''
  }

  return { user, token, isAuthenticated, isAdmin, login, logout }
})
```

**账号 Store**（stores/account.ts）：
```typescript
export const useAccountStore = defineStore('account', () => {
  const accounts = ref<Account[]>([])
  const currentAccount = ref<Account | null>(null)

  async function fetchAccounts() {
    const response = await accountApi.list()
    accounts.value = response.data
  }

  function setCurrentAccount(account: Account) {
    currentAccount.value = account
  }

  return { accounts, currentAccount, fetchAccounts, setCurrentAccount }
})
```

#### 13.2.2 Store 持久化

**使用插件**：`pinia-plugin-persistedstate`

**配置**：
```typescript
pinia.use(createPersistedState({
  storage: localStorage,
  key: id => `contenthub_${id}`
}))
```

### 13.3 路由设计

#### 13.3.1 路由结构

```typescript
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue')
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/DashboardPage.vue')
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/AccountManagePage.vue')
      },
      // ... 更多路由
    ]
  }
]
```

#### 13.3.2 路由守卫

```typescript
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})
```

### 13.4 API 调用封装

#### 13.4.1 HTTP 客户端配置

```typescript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
http.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.error?.message || '请求失败'
    ElMessage.error(message)

    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    }

    return Promise.reject(error)
  }
)
```

#### 13.4.2 API 模块

```typescript
// api/account.ts
export const accountApi = {
  list: (params?: AccountListParams) =>
    http.get<Account[]>('/accounts', { params }),

  get: (id: number) =>
    http.get<Account>(`/accounts/${id}`),

  create: (data: CreateAccountDto) =>
    http.post<Account>('/accounts', data),

  update: (id: number, data: UpdateAccountDto) =>
    http.put<Account>(`/accounts/${id}`, data),

  delete: (id: number) =>
    http.delete(`/accounts/${id}`)
}
```

### 13.5 响应式设计

**断点定义**：
```scss
$breakpoints: (
  'xs': 480px,
  'sm': 768px,
  'md': 1024px,
  'lg': 1280px,
  'xl': 1536px
);
```

**响应式布局**：
- 使用 Element Plus 的栅格系统
- 移动端优先设计
- 支持横屏和竖屏

### 13.6 交互逻辑设计

#### 13.6.1 登录和认证流程

**流程图**：
```
用户访问系统 → 检查登录状态 →
  ├─ 已登录 → 跳转到仪表盘
  └─ 未登录 → 显示登录页
       ├─ 输入用户名密码
       ├─ 点击登录按钮
       ├─ 调用登录 API
       ├─ 登录成功 → 保存 Token → 跳转仪表盘
       └─ 登录失败 → 显示错误提示
```

**状态管理**：
```typescript
// composables/useAuth.ts
export function useAuth() {
  const userStore = useUserStore()
  const router = useRouter()
  const route = useRoute()

  // 登录
  const login = async (credentials: LoginCredentials) => {
    try {
      // 显示加载状态
      const loading = ElLoading.service({ fullscreen: true })

      // 调用登录 API
      await userStore.login(credentials)

      // 关闭加载
      loading.close()

      // 成功提示
      ElMessage.success('登录成功')

      // 跳转到原始页面或仪表盘
      const redirect = (route.query.redirect as string) || '/dashboard'
      router.push(redirect)
    } catch (error: any) {
      ElMessage.error(error.message || '登录失败')
    }
  }

  // 登出
  const logout = async () => {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning'
      })

      await userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 用户取消
    }
  }

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    return userStore.user?.permissions?.includes(permission) || false
  }

  return {
    login,
    logout,
    hasPermission,
    isAuthenticated: computed(() => userStore.isAuthenticated),
    user: computed(() => userStore.user)
  }
}
```

#### 13.6.2 账号管理流程

**列表页交互**：
```
加载账号列表 → 显示表格 →
  ├─ 搜索/筛选 → 更新表格数据
  ├─ 分页 → 加载对应页数据
  ├─ 点击新建 → 打开新建表单弹窗
  ├─ 点击编辑 → 打开编辑表单弹窗
  ├─ 点击删除 → 确认后删除账号
  └─ 点击配置 → 跳转配置页面
```

**账号列表组件示例**：
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAccountStore } from '@/features/accounts/stores/accounts'
import { ElMessage, ElMessageBox } from 'element-plus'

const accountStore = useAccountStore()
const loading = ref(false)
const searchForm = ref({
  keyword: '',
  platformId: '',
  status: ''
})

// 表格数据
const tableData = computed(() => accountStore.accounts)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    await accountStore.fetchAccounts({
      ...searchForm.value,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    pagination.total = accountStore.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 新建账号
const handleCreate = () => {
  // 打开表单弹窗
  formVisible.value = true
  formMode.value = 'create'
}

// 编辑账号
const handleEdit = (row: Account) => {
  formVisible.value = true
  formMode.value = 'edit'
  currentAccount.value = row
}

// 删除账号
const handleDelete = async (row: Account) => {
  try {
    await ElMessageBox.confirm(`确定要删除账号"${row.name}"吗？`, '警告', {
      type: 'warning'
    })

    await accountStore.deleteAccount(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="account-manage">
    <!-- 搜索栏 -->
    <el-form :model="searchForm" inline>
      <el-form-item label="关键词">
        <el-input v-model="searchForm.keyword" placeholder="搜索账号名称" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">新建账号</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading">
      <el-table-column prop="name" label="账号名称" />
      <el-table-column prop="platform" label="平台" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'danger'">
            {{ row.isActive ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link @click="handleEdit(row)">编辑</el-button>
          <el-button link @click="handleConfig(row)">配置</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      @change="loadData"
    />
  </div>
</template>
```

#### 13.6.3 内容生成流程

**交互流程**：
```
进入内容管理 → 选择账号 → 选择内容板块 →
  ├─ 自动选题
  │   ├─ 调用 Tavily API
  │   ├─ 显示选题列表
  │   └─ 选择选题
  ├─ 手动输入选题
  ├─ 生成内容
  │   ├─ 显示生成进度
  │   ├─ 生成成功 → 显示内容预览
  │   └─ 生成失败 → 显示错误信息
  └─ 内容预览
       ├─ 编辑内容
       ├─ 重新生成
       ├─ 提交审核
       └─ 保存草稿
```

**内容生成组件示例**：
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useContentStore } from '@/features/content/stores/content'
import { ElMessage } from 'element-plus'

const contentStore = useContentStore()

// 步骤
const currentStep = ref(1)

// 表单数据
const formData = reactive({
  accountId: '',
  sectionCode: '',
  topic: '',
  useAutoTopic: false
})

// 选题列表
const topics = ref<Topic[]>([])

// 生成进度
const generating = ref(false)
const progress = ref(0)

// 自动选题
const handleAutoTopic = async () => {
  try {
    const result = await contentService.fetchTopics({
      accountId: formData.accountId,
      sectionCode: formData.sectionCode
    })
    topics.value = result.data
    ElMessage.success('选题成功')
  } catch {
    ElMessage.error('选题失败')
  }
}

// 生成内容
const handleGenerate = async () => {
  generating.value = true
  progress.value = 0

  try {
    // 模拟进度
    const timer = setInterval(() => {
      if (progress.value < 90) {
        progress.value += 10
      }
    }, 500)

    const result = await contentService.generateContent({
      accountId: formData.accountId,
      sectionCode: formData.sectionCode,
      topic: formData.topic
    })

    clearInterval(timer)
    progress.value = 100

    currentStep.value = 3
    ElMessage.success('内容生成成功')

    // 保存到 store
    contentStore.setCurrentContent(result.data)
  } catch {
    ElMessage.error('内容生成失败')
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <el-steps :active="currentStep" align-center>
    <el-step title="选择账号和板块" />
    <el-step title="选择或输入选题" />
    <el-step title="生成内容" />
    <el-step title="预览和审核" />
  </el-steps>

  <!-- 步骤 1：选择账号和板块 -->
  <div v-if="currentStep === 1" class="step-content">
    <el-form :model="formData">
      <el-form-item label="账号">
        <account-selector v-model="formData.accountId" />
      </el-form-item>
      <el-form-item label="内容板块">
        <section-selector v-model="formData.sectionCode" :account-id="formData.accountId" />
      </el-form-item>
      <el-button type="primary" @click="currentStep = 2">下一步</el-button>
    </el-form>
  </div>

  <!-- 步骤 2：选题 -->
  <div v-if="currentStep === 2" class="step-content">
    <el-radio-group v-model="formData.useAutoTopic">
      <el-radio :label="false">手动输入</el-radio>
      <el-radio :label="true">自动选题</el-radio>
    </el-radio-group>

    <div v-if="!formData.useAutoTopic">
      <el-input v-model="formData.topic" type="textarea" placeholder="请输入选题" />
    </div>

    <div v-else>
      <el-button @click="handleAutoTopic">开始选题</el-button>
      <el-radio-group v-model="formData.topic">
        <el-radio v-for="t in topics" :key="t.id" :label="t.title">
          {{ t.title }}
        </el-radio>
      </el-radio-group>
    </div>

    <el-button @click="currentStep = 1">上一步</el-button>
    <el-button type="primary" @click="handleGenerate">生成内容</el-button>
  </div>

  <!-- 步骤 3：生成中 -->
  <div v-if="currentStep === 3 && generating" class="step-content">
    <el-progress :percentage="progress" status="success" />
    <p>正在生成内容，请稍候...</p>
  </div>

  <!-- 步骤 4：预览和审核 -->
  <div v-if="currentStep === 4 && !generating" class="step-content">
    <content-preview :content="contentStore.currentContent" />
    <el-button @click="handleGenerate">重新生成</el-button>
    <el-button @click="handleSubmit">提交审核</el-button>
  </div>
</template>
```

#### 13.6.4 发布流程

**交互流程**：
```
进入发布管理 → 查看待发布内容 →
  ├─ 单个发布
  │   ├─ 点击发布按钮
  │   ├─ 显示发布进度
  │   ├─ 发布成功 → 更新状态
  │   └─ 发布失败 → 显示错误，支持重试
  ├─ 批量发布
  │   ├─ 选择多个内容
  │   ├─ 点击批量发布
  │   └─ 依次发布，显示进度
  └─ 定时发布
       ├─ 设置发布时间
       └─ 添加到定时任务
```

#### 13.6.5 状态同步机制

**实时状态更新**：
```typescript
// composables/useRealtime.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useRealtime(channel: string) {
  const data = ref(null)
  let ws: WebSocket | null = null

  const connect = () => {
    ws = new WebSocket(`ws://localhost:8000/ws/${channel}`)

    ws.onmessage = (event) => {
      data.value = JSON.parse(event.data)
    }

    ws.onerror = () => {
      console.error('WebSocket error')
    }

    ws.onclose = () => {
      // 5秒后重连
      setTimeout(connect, 5000)
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    ws?.close()
  })

  return { data }
}

// 使用示例：实时更新发布状态
const { data: publishStatus } = useRealtime('publish-status')

watch(publishStatus, (newStatus) => {
  if (newStatus?.contentId === currentContent.value?.id) {
    currentContent.value.publishStatus = newStatus.status
  }
})
```

#### 13.6.6 错误处理和用户反馈

**统一错误处理**：
```typescript
// utils/errorHandler.ts
export function handleApiError(error: any) {
  console.error('API Error:', error)

  // 网络错误
  if (!error.response) {
    ElMessage.error('网络连接失败，请检查网络设置')
    return
  }

  // HTTP 状态码处理
  const status = error.response.status
  const data = error.response.data

  switch (status) {
    case 400:
      ElMessage.error(data.error?.message || '请求参数错误')
      break
    case 401:
      ElMessage.error('登录已过期，请重新登录')
      // 跳转登录页
      window.location.href = '/login'
      break
    case 403:
      ElMessage.error('没有权限执行此操作')
      break
    case 404:
      ElMessage.error('请求的资源不存在')
      break
    case 429:
      ElMessage.error('操作过于频繁，请稍后再试')
      break
    case 500:
      ElMessage.error('服务器内部错误，请稍后重试')
      break
    default:
      ElMessage.error(data.error?.message || '操作失败')
  }
}
```

**用户反馈机制**：
```typescript
// 乐观更新 + 回滚
const handleUpdate = async (id: number, data: any) => {
  // 保存旧数据
  const oldData = { ...tableData.value.find(item => item.id === id) }

  try {
    // 乐观更新
    const index = tableData.value.findIndex(item => item.id === id)
    tableData.value[index] = { ...tableData.value[index], ...data }

    // 调用 API
    await accountApi.update(id, data)

    ElMessage.success('更新成功')
  } catch (error) {
    // 回滚
    const index = tableData.value.findIndex(item => item.id === id)
    tableData.value[index] = oldData

    handleApiError(error)
  }
}
```

#### 13.6.7 性能优化交互

**虚拟滚动**：
```vue
<script setup>
import { useVirtualList } from '@vueuse/core'

const { list, containerProps, wrapperProps } = useVirtualList(
  largeDataSource,
  { itemHeight: 50 }
)
</script>

<template>
  <div v-bind="containerProps" style="height: 500px; overflow: auto;">
    <div v-bind="wrapperProps">
      <div
        v-for="{ data, index } in list"
        :key="index"
        style="height: 50px;"
      >
        {{ data }}
      </div>
    </div>
  </div>
</template>
```

**防抖和节流**：
```typescript
import { useDebounceFn, useThrottleFn } from '@vueuse/core'

// 防抖：搜索输入
const handleSearch = useDebounceFn((value: string) => {
  loadData(value)
}, 500)

// 节流：滚动加载
const handleScroll = useThrottleFn(() => {
  loadMoreData()
}, 200)
```

---

## 十四、性能优化策略

### 14.1 后端优化

#### 14.1.1 数据库优化

**索引优化**：
- 为常用查询字段添加索引
- 使用复合索引优化多条件查询
- 定期分析查询计划

**查询优化**：
- 使用 SQLAlchemy 的 `select_in` 加载策略
- 避免N+1 查询问题
- 使用分页减少数据传输

**连接池配置**：
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}
```

#### 14.1.2 API 优化

**响应优化**：
- 使用 Pydantic 的 `exclude` 字段排除不必要的数据
- 使用投影查询只返回需要的字段
- 启用 gzip 压缩

**异步处理**：
- 使用 FastAPI 的异步端点
- 长时间运行的任务使用后台任务
- 外部 API 调用使用异步 HTTP 客户端

**批量操作**：
- 支持批量创建、更新、删除
- 使用批量插入减少数据库操作

### 14.2 前端优化

#### 14.2.1 加载优化

**代码分割**：
- 路由懒加载
- 组件懒加载
- 第三方库按需加载

**资源优化**：
- 图片压缩和格式优化（WebP）
- 使用 CDN 加速静态资源
- 启用浏览器缓存

**预加载**：
- 预加载关键资源
- 使用 prefetch 预加载下一页资源

#### 14.2.2 渲染优化

**虚拟滚动**：
- 长列表使用虚拟滚动
- 减少 DOM 节点数量

**防抖和节流**：
- 搜索输入使用防抖
- 滚动事件使用节流

**计算属性缓存**：
- 使用 Vue 的 computed 缓存计算结果
- 避免在模板中使用复杂表达式

### 14.3 网络优化

#### 14.3.1 请求优化

**请求合并**：
- 批量请求合并为一个
- 使用 GraphQL 减少请求次数

**请求缓存**：
- GET 请求使用 HTTP 缓存
- 使用 ETag 和 Last-Modified

#### 14.3.2 CDN 配置

**静态资源 CDN**：
- 前端构建文件上传 CDN
- 图片文件上传 CDN

**API 缓存**：
- 使用 Redis 缓存 API 响应
- 配置合理的缓存时间

### 14.4 监控和调优

**性能监控**：
- API 响应时间监控
- 数据库查询时间监控
- 前端页面加载时间监控

**性能指标**：
- P50 响应时间 < 100ms
- P95 响应时间 < 500ms
- P99 响应时间 < 1000ms

**调优流程**：
1. 识别性能瓶颈
2. 分析性能数据
3. 制定优化方案
4. 实施优化
5. 验证优化效果

---

## 十五、风险评估

### 15.1 技术风险

1. **content-creator 集成**: 可能存在兼容性问题
2. **定时任务调度**: 可能影响系统性能
3. **配置同步**: 需要确保数据一致性
4. **外部 API 依赖**: 可能存在网络延迟或服务不可用

### 15.2 业务风险

1. **需求变更**: 可能需要调整功能和架构
2. **用户体验**: 需要不断优化界面和流程
3. **系统扩展性**: 可能需要支持更多平台和功能

### 15.3 风险缓解

1. **技术风险**: 提前进行技术验证和测试
2. **业务风险**: 与用户保持密切沟通，及时调整
3. **外部依赖**: 实现容错机制和备用方案

---

## 十六、成功指标

### 16.1 功能指标
- 所有核心功能正常运行
- 系统能够稳定处理内容生成和发布流程
- 前端界面提供良好的用户体验

### 16.2 性能指标
- 响应时间: < 2 秒
- 并发用户数: > 100
- 系统可用性: > 99%

### 16.3 业务指标
- 内容生成效率提升 80%
- 发布流程自动化程度 90%
- 用户满意度 > 4.5/5.0

---

## 十七、文档

- [后端开发文档](src/backend/README.md)
- [前端开发文档](src/frontend/README.md)
- [API 文档](http://localhost:8000/docs)

---

## 十八、附录

### 18.1 技术文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://www.sqlalchemy.org/)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)

### 18.2 相关项目
- [omni-cast](https://github.com/your-username/omni-cast)
- [content-creator](https://github.com/your-username/content-creator)
- [content-publisher](https://github.com/your-username/content-publisher)

---

这份设计文档为 ContentHub 项目提供了全面的指导，包括系统架构、功能需求、业务流程、模块设计、数据设计、API 设计、部署方案和项目计划。文档结构清晰，内容全面，是项目开发的重要参考依据。