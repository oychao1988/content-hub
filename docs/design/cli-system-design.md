# ContentHub CLI 系统设计

> **版本**: 1.2.0
> **创建日期**: 2026-02-03
> **最后更新**: 2026-02-04
> **状态**: ✅ 已实施
> **作者**: ContentHub 开发团队
> **实施总结**: [CLI-IMPLEMENTATION-SUMMARY.md](../development/CLI-IMPLEMENTATION-SUMMARY.md)

---

## 概述

为 ContentHub 项目的所有功能模块添加 CLI（命令行界面）指令支持，使用独立的 shell 脚本和 Python CLI 结合的方式，提供类似 git/npm 的简洁使用体验。

### 设计目标

1. **简洁性**: 命令简短易记，`./contenthub <module> <action>`
2. **一致性**: 所有模块遵循相同的命令结构和参数约定
3. **安全性**: 危险操作需要确认，清晰的错误提示
4. **易用性**: 自动生成帮助文档，友好的表格输出
5. **可扩展性**: 模块化设计，易于添加新命令

---

## 技术选型

### 核心技术栈

| 技术 | 版本 | 用途 | 选择理由 |
|------|------|------|----------|
| **typer** | 0.12.0+ | CLI 框架 | 类型安全、自动文档生成、与 FastAPI 风格一致 |
| **rich** | 13.7.0+ | 终端美化 | 美观的表格输出、进度条、语法高亮 |
| **shell** | bash | 入口脚本 | 统一入口、跨平台兼容、简化调用 |

### 技术决策

#### 1. typer + 独立脚本架构

```bash
content-hub/
├── bin/
│   └── contenthub              # Shell 脚本入口（可执行）
└── src/backend/
    └── cli/                    # Python CLI 实现
        ├── __init__.py
        ├── main.py             # typer 主应用
        ├── config.py           # CLI 配置管理
        ├── utils.py            # CLI 工具函数
        └── modules/            # 各功能模块
            ├── db.py
            ├── users.py
            ├── accounts.py
            ├── content.py
            ├── scheduler.py
            ├── publisher.py
            ├── publish_pool.py  # 发布池管理
            ├── platform.py
            ├── customer.py
            ├── config.py
            ├── audit.py
            ├── system.py
            └── dashboard.py
```

**优势**:
- Shell 脚本提供统一的调用入口
- typer 处理命令解析和参数验证
- 自动生成完善的帮助文档
- 类型安全，减少运行时错误

#### 2. 输出格式化策略

使用 `rich` 库实现多级输出：

```python
# 表格输出（列表查询）
┌──────┬─────────┬────────┬──────────┐
│ ID   │ 用户名  │ 角色   │ 状态     │
├──────┼─────────┼────────┼──────────┤
│ 1    │ admin   │ admin  │ active   │
│ 2    │ editor  │ editor │ active   │
└──────┴─────────┴────────┴──────────┘

# 状态消息（操作结果）
✅ 用户创建成功
❌ 操作失败：用户名已存在
⚠️  警告：该操作不可逆

# 确认提示（危险操作）
⚠️  即将重置数据库，所有数据将丢失！
确认继续？[y/N]:
```

#### 3. 配置管理

- 从 `.env` 文件读取数据库连接、API 密钥等配置
- 支持命令行参数覆盖配置文件
- 敏感信息通过环境变量传递

---

## 系统架构

### 目录结构

```
content-hub/
├── bin/
│   └── contenthub                    # CLI 入口脚本（可执行）
├── src/backend/
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py                   # CLI 主入口（typer app）
│   │   ├── config.py                 # CLI 配置管理
│   │   ├── utils.py                  # CLI 工具函数
│   │   └── modules/
│   │       ├── db.py                 # 数据库管理
│   │       ├── users.py              # 用户管理
│   │       ├── accounts.py           # 账号管理
│   │       ├── content.py            # 内容管理
│   │       ├── scheduler.py          # 定时任务管理
│   │       ├── publisher.py          # 发布管理
│   │       ├── publish_pool.py       # 发布池管理
│   │       ├── platform.py           # 平台管理
│   │       ├── customer.py           # 客户管理
│   │       ├── config.py             # 系统配置管理
│   │       ├── audit.py              # 审计日志
│   │       ├── system.py             # 系统管理
│   │       └── dashboard.py          # 仪表盘数据
│   └── requirements.txt              # 添加 typer, rich
└── docs/
    └── references/
        └── CLI-REFERENCE.md          # CLI 命令参考手册
```

### 模块划分

| 模块 | 文件 | 功能描述 | 对应后端模块 |
|------|------|----------|-------------|
| **db** | db.py | 数据库初始化、备份、恢复、迁移、shell | - |
| **users** | users.py | 用户 CRUD、角色管理、密码管理 | users |
| **accounts** | accounts.py | 运营账号管理、配置导入导出、连接测试 | accounts |
| **content** | content.py | 内容管理、生成、审核流程、批量生成 | content |
| **scheduler** | scheduler.py | 定时任务管理、执行历史、启停控制 | scheduler |
| **publisher** | publisher.py | 发布管理、手动发布、重试、批量发布 | publisher |
| **publish-pool** | publish_pool.py | 发布池管理、优先级调整、批量操作 | publish_pool |
| **platform** | platform.py | 平台管理、API 配置 | platform |
| **customer** | customer.py | 客户管理、统计信息 | customer |
| **config** | config.py | 写作风格、内容主题、系统参数、平台配置 | config |
| **audit** | audit.py | 审计日志查询、导出、统计 | audit |
| **system** | system.py | 系统信息、健康检查、缓存管理、维护模式 | system |
| **dashboard** | dashboard.py | 仪表盘统计数据、趋势分析 | dashboard |

---

## 配置管理

### 环境变量配置

CLI 通过环境变量和 `.env` 文件读取配置，优先级：**命令行参数 > 环境变量 > .env 文件**

| 变量名 | 说明 | 默认值 | CLI 使用 |
|--------|------|--------|----------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` | 所有数据库操作 |
| `CLI_DB_PATH` | CLI 专用数据库路径（覆盖 DATABASE_URL） | - | 所有数据库操作 |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - | content generate |
| `PUBLISHER_API_URL` | 发布服务地址 | `http://localhost:3010` | publisher publish |
| `PUBLISHER_API_KEY` | 发布服务 API 密钥 | - | publisher publish |
| `TAVILY_API_KEY` | Tavily API 密钥 | - | content topic-search |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` | scheduler start |
| `LOG_LEVEL` | 日志级别 | `INFO` | 全局 |
| `CLI_FORMAT` | 输出格式（table/json/csv） | `table` | 全局 |

### 配置文件位置

```bash
# 配置文件搜索顺序（优先级从高到低）
1. ./contenthub.env              # 当前目录
2. ~/.contenthub.env             # 用户主目录
3. /etc/contenthub/env           # 系统配置目录
4. src/backend/.env              # 开发环境
```

### 权限与认证

**CLI 权限模型**:
- CLI 假定以系统管理员身份运行，无需认证
- 所有 CLI 操作自动记录到审计日志（操作用户：`cli-user`）
- 可通过 `--user` 选项指定操作用户（用于审计）

```bash
# 默认：使用 cli-user
./contenthub users create --username admin

# 指定操作用户（用于审计）
./contenthub users create --username admin --user operator-1
```

**安全注意事项**:
- CLI 脚本应限制权限（仅限管理员可执行）
- 敏感操作（db reset, user delete）需要二次确认
- 所有操作记录审计日志，可追溯

---

## 命令设计

### 命令结构规范

```bash
./contenthub <module> <action> [arguments] [options]

# 示例：
./contenthub users list --role editor --page 1
./contenthub db init
./contenthub content generate --account-id 1 --topic "AI技术"
./contenthub accounts create --name "测试账号" --customer-id 1 --platform-id 1
```

### 全局选项

```bash
--format <table|json|csv>    # 输出格式（默认：table）
--debug                     # 启用调试模式
--quiet                     # 静默模式（仅输出错误）
--user <username>           # 指定操作用户（用于审计）
--help                      # 显示帮助信息
--version                   # 显示版本信息
```

---

## 完整命令清单

### 数据库管理 (db)

```bash
./contenthub db init                          # 初始化数据库
./contenthub db reset                         # 重置数据库（危险操作，需确认）
./contenthub db backup [output-path]          # 备份数据库
./contenthub db restore <backup-file>         # 恢复数据库
./contenthub db migrate                       # 运行数据库迁移
./contenthub db rollback [steps]              # 回滚迁移
./contenthub db shell                         # 进入数据库 shell（SQLite）
./contenthub db info                          # 显示数据库信息
./contenthub db stats                         # 数据库统计信息
```

**示例**:
```bash
# 初始化数据库
./contenthub db init

# 备份数据库到指定路径
./contenthub db backup /backups/contenthub_20260203.db

# 查看数据库统计
./contenthub db stats
# 输出：
# ┌────────────────────┬──────────┐
# │ 表名               │ 记录数   │
# ├────────────────────┼──────────┤
# │ users              │ 5        │
# │ accounts           │ 12       │
# │ contents           │ 156      │
# │ publish_logs       │ 89       │
# └────────────────────┴──────────┘
```

### 用户管理 (users)

```bash
./contenthub users list [--role] [--status] [--page] [--page-size]  # 列出用户
./contenthub users create --username <name> --email <email> --role <role>  # 创建用户
./contenthub users update <id> [--email] [--full-name] [--role]   # 更新用户信息
./contenthub users delete <id>                                      # 删除用户（需确认）
./contenthub users info <id>                                        # 查看用户详情
./contenthub users activate <id>                                    # 激活用户
./contenthub users deactivate <id>                                  # 停用用户
./contenthub users change-password <id> [--new-password]           # 修改密码
./contenthub users set-role <id> --role <role>                     # 设置用户角色
./contenthub users reset-password <id>                             # 重置密码（生成随机密码）
```

**角色选项**: `admin`, `operator`, `customer`

**示例**:
```bash
# 创建管理员用户
./contenthub users create \
  --username admin \
  --email admin@example.com \
  --role admin

# 列出所有操作员
./contenthub users list --role operator

# 停用某个用户
./contenthub users deactivate 5
```

### 账号管理 (accounts)

```bash
./contenthub accounts list [--customer-id] [--platform-id] [--status]  # 列出账号
./contenthub accounts create --name <name> --customer-id <id> --platform-id <id>  # 创建账号
./contenthub accounts update <id> [--name] [--description] [--status]  # 更新账号
./contenthub accounts delete <id>                                      # 删除账号（需确认）
./contenthub accounts info <id>                                        # 查看账号详情
./contenthub accounts list-config <id>                                 # 查看完整配置
./contenthub accounts import-md <id> <markdown-file>                   # 从 Markdown 导入配置
./contenthub accounts export-md <id> [output-path]                     # 导出配置到 Markdown
./contenthub accounts test-connection <id>                             # 测试平台连接
./contenthub accounts writing-style <id> [--list] [--get] [--update]   # 管理写作风格
./contenthub accounts publish-config <id> [--list] [--get] [--update]  # 管理发布配置
```

**示例**:
```bash
# 创建账号
./contenthub accounts create \
  --name "客户A-微信公众号" \
  --customer-id 1 \
  --platform-id 1

# 查看账号详情
./contenthub accounts info 1

# 测试平台连接
./contenthub accounts test-connection 1
# 输出：
# ✅ 连接成功
# 平台：微信公众号
# AppID：wx1234567890

# 导出配置
./contenthub accounts export-md 1 ./configs/account-1.md
```

### 内容管理 (content)

```bash
./contenthub content list [--account-id] [--status] [--page]       # 列出内容
./contenthub content create --account-id <id> --title <title>      # 创建内容
./contenthub content generate --account-id <id> --topic <topic>    # 生成内容
./contenthub content batch-generate --account-id <id> --count <n>  # 批量生成内容
./contenthub content topic-search --account-id <id> --keywords <k># 选题搜索
./contenthub content update <id> [--title] [--content]             # 更新内容
./contenthub content delete <id>                                   # 删除内容（需确认）
./contenthub content info <id>                                     # 查看详情
./contenthub content submit-review <id>                            # 提交审核
./contenthub content approve <id> [--comment]                      # 审核通过
./contenthub content reject <id> --reason <reason>                 # 审核拒绝
./contenthub content review-list                                  # 待审核列表
./contenthub content statistics                                   # 审核统计
```

**内容状态**: `draft`, `pending`, `approved`, `rejected`, `published`, `failed`

**示例**:
```bash
# 生成内容
./contenthub content generate \
  --account-id 1 \
  --topic "AI 技术在内容创作中的应用"

# 批量生成内容（5篇）
./contenthub content batch-generate \
  --account-id 1 \
  --count 5

# 查看待审核列表
./contenthub content review-list

# 审核通过
./contenthub content approve 123 --comment "内容质量优秀"
```

### 定时任务 (scheduler)

```bash
./contenthub scheduler list [--status]                      # 列出任务
./contenthub scheduler create --name <name> --type <type>   # 创建任务
./contenthub scheduler update <id> [--cron] [--enabled]     # 更新任务
./contenthub scheduler delete <id>                          # 删除任务（需确认）
./contenthub scheduler info <id>                            # 任务详情
./contenthub scheduler trigger <id>                         # 手动触发任务
./contenthub scheduler history [--task-id] [--limit]        # 执行历史
./contenthub scheduler start                                # 启动调度器
./contenthub scheduler stop                                 # 停止调度器
./contenthub scheduler status                               # 调度器状态
./contenthub scheduler pause <id>                           # 暂停任务
./contenthub scheduler resume <id>                          # 恢复任务
```

**任务类型**: `content_generation`, `batch_publish`, `system_cleanup`

**示例**:
```bash
# 创建定时生成任务
./contenthub scheduler create \
  --name "每日内容生成" \
  --type content_generation \
  --cron "0 9 * * *" \
  --account-id 1

# 查看调度器状态
./contenthub scheduler status
# 输出：
# ┌────────────────────┬──────────┐
# │ 状态               │ running  │
# ├────────────────────┼──────────┤
# │ 运行中任务数       │ 3        │
# │ 今日执行次数       │ 12       │
# │ 下次执行时间       │ 09:00    │
# └────────────────────┴──────────┘
```

### 发布管理 (publisher)

```bash
./contenthub publisher history [--account-id] [--status]     # 发布历史
./contenthub publisher publish <content-id>                   # 手动发布
./contenthub publisher retry <log-id>                        # 重试发布
./contenthub publisher batch-publish [--limit]               # 批量发布
./contenthub publisher records [--account-id] [--status]     # 发布记录
./contenthub publisher stats                                  # 发布统计
```

**发布状态**: `pending`, `publishing`, `published`, `failed`

**示例**:
```bash
# 发布单篇内容
./contenthub publisher publish 123

# 批量发布前5篇
./contenthub publisher batch-publish --limit 5

# 查看发布统计
./contenthub publisher stats
# 输出：
# ┌────────────────────┬──────────┐
# │ 总发布次数         │ 256      │
# ├────────────────────┼──────────┤
# │ 成功次数           │ 245      │
# │ 失败次数           │ 11       │
# │ 成功率             │ 95.7%    │
# └────────────────────┴──────────┘
```

### 发布池管理 (publish-pool)

```bash
./contenthub publish-pool list [--account-id] [--status]      # 列出待发布内容
./contenthub publish-pool add <content-id> [--priority]       # 添加到发布池
./contenthub publish-pool remove <content-id>                 # 从发布池移除
./contenthub publish-pool set-priority <id> --priority <n>    # 设置优先级（1-10）
./contenthub publish-pool schedule <id> --time <datetime>     # 设置计划发布时间
./contenthub publish-pool publish [--limit]                  # 从发布池发布
./contenthub publish-pool clear                               # 清空发布池（需确认）
./contenthub publish-pool stats                               # 发布池统计
```

**优先级**: 1-10（数字越小优先级越高）

**示例**:
```bash
# 查看待发布内容
./contenthub publish-pool list

# 设置优先级
./contenthub publish-pool set-priority 123 --priority 1

# 设置计划发布时间
./contenthub publish-pool schedule 123 --time "2026-02-04 09:00"

# 从发布池发布（最多10篇）
./contenthub publish-pool publish --limit 10
```

### 平台管理 (platform)

```bash
./contenthub platform list                                    # 列出平台
./contenthub platform create --name <name> --code <code>      # 创建平台
./contenthub platform update <id> [--name] [--api-url]       # 更新平台
./contenthub platform delete <id>                             # 删除平台（需确认）
./contenthub platform info <id>                               # 平台详情
./contenthub platform test-api <id>                           # 测试平台 API
```

**示例**:
```bash
# 创建平台
./contenthub platform create \
  --name "微信公众号" \
  --code wechat \
  --api-url "https://api.weixin.qq.com"

# 测试平台 API
./contenthub platform test-api 1
```

### 客户管理 (customer)

```bash
./contenthub customer list [--status]                         # 列出客户
./contenthub customer create --name <name> [--contact-name]  # 创建客户
./contenthub customer update <id> [--name] [--contact-email] # 更新客户
./contenthub customer delete <id>                             # 删除客户（需确认）
./contenthub customer info <id>                               # 客户详情
./contenthub customer stats <id>                              # 客户统计信息
./contenthub customer accounts <id>                           # 查看客户的账号列表
```

**示例**:
```bash
# 创建客户
./contenthub customer create \
  --name "客户A" \
  --contact-name "张三" \
  --contact-email "zhangsan@example.com"

# 查看客户统计
./contenthub customer stats 1
# 输出：
# ┌────────────────────┬──────────┐
# │ 账号数量           │ 3        │
# ├────────────────────┼──────────┤
# │ 内容总数           │ 156      │
# │ 已发布内容         │ 142      │
# │ 待发布内容         │ 14       │
# └────────────────────┴──────────┘
```

### 系统配置 (config)

```bash
# 写作风格管理
./contenthub config writing-style list                          # 列出写作风格
./contenthub config writing-style create --name <name>          # 创建写作风格
./contenthub config writing-style update <id> [--tone] [--words]# 更新写作风格
./contenthub config writing-style delete <id>                   # 删除写作风格（需确认）
./contenthub config writing-style info <id>                     # 写作风格详情

# 内容主题管理
./contenthub config content-theme list                          # 列出内容主题
./contenthub config content-theme create --name <name>          # 创建内容主题
./contenthub config content-theme update <id> [--type]          # 更新内容主题
./contenthub config content-theme delete <id>                   # 删除内容主题（需确认）
./contenthub config content-theme info <id>                     # 内容主题详情

# 系统参数管理
./contenthub config system-params get [--key]                   # 获取系统参数
./contenthub config system-params set --key <key> --value <val> # 设置系统参数
./contenthub config system-params list                           # 列出所有系统参数

# 平台配置管理
./contenthub config platform-config list                         # 列出平台配置
./contenthub config platform-config update <platform-id>        # 更新平台配置
```

**示例**:
```bash
# 创建写作风格
./contenthub config writing-style create \
  --name "专业风格" \
  --tone "专业、严谨" \
  --min-words 1000 \
  --max-words 2000

# 设置系统参数
./contenthub config system-params set \
  --key scheduler.enabled \
  --value true
```

### 审计日志 (audit)

```bash
./contenthub audit logs [--event-type] [--user-id] [--result]   # 查询日志
./contenthub audit log-detail <id>                              # 日志详情
./contenthub audit export [--start-date] [--end-date]           # 导出日志
./contenthub audit statistics [--start-date] [--end-date]       # 审计统计
./contenthub audit user-activity <user-id>                       # 用户活动日志
```

**事件类型**: `user_login`, `user_create`, `account_create`, `content_generate`, `content_publish` 等

**结果**: `success`, `failure`

**示例**:
```bash
# 查询今天失败的发布操作
./contenthub audit logs \
  --event-type content_publish \
  --result failure \
  --start-date 2026-02-03

# 导出审计日志
./contenthub audit export \
  --start-date 2026-02-01 \
  --end-date 2026-02-03 \
  --output audit-logs.csv

# 查看用户活动
./contenthub audit user-activity 5
```

### 系统管理 (system)

```bash
./contenthub system health                                       # 健康检查
./contenthub system info                                         # 系统信息
./contenthub system version                                      # 版本信息
./contenthub system metrics                                      # 系统指标
./contenthub system cache-stats                                  # 缓存统计
./contenthub system cache-clear                                  # 清空缓存
./contenthub system cache-cleanup                                # 清理过期缓存
./contenthub system maintenance [--enable|--disable]            # 维护模式控制
./contenthub system cleanup                                      # 清理临时文件
./contenthub system logs [--tail] [--level]                     # 查看系统日志
```

**示例**:
```bash
# 健康检查
./contenthub system health
# 输出：
# ┌────────────────────┬──────────┐
# │ 数据库             │ ✅ OK    │
# ├────────────────────┼──────────┤
# │ 调度器             │ ✅ 运行中│
# ├────────────────────┼──────────┤
# │ 发布服务           │ ✅ 可用  │
# ├────────────────────┼──────────┤
# │ 磁盘空间           │ ✅ 45%   │
# └────────────────────┴──────────┘

# 启用维护模式
./contenthub system maintenance --enable

# 清理临时文件
./contenthub system cleanup
```

### 仪表盘 (dashboard)

```bash
./contenthub dashboard stats                                    # 统计数据
./contenthub dashboard activities [--limit]                     # 最近活动
./contenthub dashboard content-trend [--days]                   # 内容趋势
./contenthub dashboard publish-stats [--days]                   # 发布统计
./contenthub dashboard user-stats                                # 用户统计
./contenthub dashboard customer-stats                            # 客户统计
```

**示例**:
```bash
# 查看统计数据
./contenthub dashboard stats

# 查看最近20条活动
./contenthub dashboard activities --limit 20

# 查看最近7天的内容趋势
./contenthub dashboard content-trend --days 7
```

---

## 错误处理

### 错误码规范

| 错误码 | 说明 | 示例场景 |
|--------|------|----------|
| `0` | 成功 | 命令执行成功 |
| `1` | 通用错误 | 未捕获的异常 |
| `2` | 数据库错误 | 数据库连接失败 |
| `3` | 配置错误 | .env 文件缺失 |
| `4` | 权限错误 | 文件无权限 |
| `5` | 资源不存在 | 用户 ID 999 不存在 |
| `6` | 参数错误 | 必需参数缺失 |
| `7` | 外部服务错误 | content-creator 调用失败 |
| `8` | 网络错误 | API 请求超时 |

### 错误输出示例

**数据库错误**:
```bash
$ ./contenthub users list
❌ 数据库错误：无法连接到数据库
路径：sqlite:///./data/contenthub.db
提示：请先运行 './contenthub db init' 初始化数据库
```

**资源不存在**:
```bash
$ ./contenthub users info 999
❌ 错误：用户 999 不存在
提示：使用 './contenthub users list' 查看可用用户
```

**参数错误**:
```bash
$ ./contenthub accounts create --name "测试"
❌ 参数错误：缺少必需参数 --customer-id
提示：运行 './contenthub accounts create --help' 查看帮助
```

**外部服务错误**:
```bash
$ ./contenthub content generate --account-id 1 --topic "AI"
❌ 内容生成失败：content-creator 服务不可用
路径：/path/to/content-creator
提示：请检查 CREATOR_CLI_PATH 配置
```

### 确认提示机制

**危险操作需要确认**:
```bash
$ ./contenthub db reset
⚠️  警告：即将重置数据库，所有数据将丢失！
此操作不可逆，请确认是否继续？[y/N]: y
✅ 数据库已重置

$ ./contenthub users delete 5
⚠️  警告：即将删除用户 "operator-1"
此操作不可逆，请确认是否继续？[y/N]: n
❌ 操作已取消
```

---

## 使用示例

### 场景1：快速开始

```bash
# 1. 初始化数据库
./contenthub db init

# 2. 创建管理员用户
./contenthub users create \
  --username admin \
  --email admin@example.com \
  --role admin

# 3. 创建平台
./contenthub platform create \
  --name "微信公众号" \
  --code wechat

# 4. 创建写作风格
./contenthub config writing-style create \
  --name "专业风格" \
  --tone "专业、严谨"
```

### 场景2：客户账号管理

```bash
# 1. 创建客户
./contenthub customer create \
  --name "客户A" \
  --contact-name "张三" \
  --contact-email "zhangsan@example.com"

# 2. 创建账号
./contenthub accounts create \
  --name "客户A-公众号" \
  --customer-id 1 \
  --platform-id 1

# 3. 配置写作风格
./contenthub accounts writing-style 1 --update \
  --tone "轻松、幽默"

# 4. 测试平台连接
./contenthub accounts test-connection 1
```

### 场景3：内容生成与发布

```bash
# 1. 搜索选题
./contenthub content topic-search \
  --account-id 1 \
  --keywords "AI,技术趋势"

# 2. 生成内容
./contenthub content generate \
  --account-id 1 \
  --topic "AI 技术在内容创作中的应用"

# 3. 查看生成的内容
./contenthub content info 1

# 4. 提交审核
./contenthub content submit-review 1

# 5. 审核通过
./contenthub content approve 1 --comment "内容质量优秀"

# 6. 发布到平台
./contenthub publisher publish 1
```

### 场景4：批量操作

```bash
# 1. 批量生成内容（5篇）
./contenthub content batch-generate \
  --account-id 1 \
  --count 5

# 2. 查看待审核列表
./contenthub content review-list

# 3. 批量审核通过
./contenthub content approve $(./contenthub content review-list --format json | jq -r '.[].id')

# 4. 批量发布
./contenthub publisher batch-publish --limit 5
```

### 场景5：定时任务

```bash
# 1. 创建定时生成任务（每天早上9点）
./contenthub scheduler create \
  --name "每日内容生成" \
  --type content_generation \
  --cron "0 9 * * *" \
  --account-id 1

# 2. 启动调度器
./contenthub scheduler start

# 3. 查看调度器状态
./contenthub scheduler status

# 4. 查看执行历史
./contenthub scheduler history --limit 10
```

### 场景6：数据导出

```bash
# 1. 导出账号配置
./contenthub accounts export-md 1 ./configs/

# 2. 导出审计日志（CSV格式）
./contenthub audit export \
  --start-date 2026-02-01 \
  --end-date 2026-02-03 \
  --output audit.csv \
  --format csv

# 3. 导出用户列表（JSON格式）
./contenthub users list --format json > users.json
```

### 场景7：系统维护

```bash
# 1. 健康检查
./contenthub system health

# 2. 备份数据库
./contenthub db backup ./backups/contenthub_$(date +%Y%m%d).db

# 3. 清理缓存
./contenthub system cache-clear

# 4. 查看系统指标
./contenthub system metrics

# 5. 启用维护模式
./contenthub system maintenance --enable
```

---

## Shell 脚本设计

### 入口脚本

**位置**: `bin/contenthub`

```bash
#!/usr/bin/env bash
# contenthub - ContentHub CLI 入口脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到后端目录
cd "$PROJECT_ROOT/src/backend"

# 设置 Python 路径
export PYTHONPATH="$PROJECT_ROOT/src/backend:$PYTHONPATH"

# 执行 Python CLI
exec python -m cli.main "$@"
```

### 安装脚本

**位置**: `scripts/install-cli.sh`

```bash
#!/usr/bin/env bash
# ContentHub CLI 安装脚本

set -e

INSTALL_DIR="/usr/local/bin"
SCRIPT_SOURCE="bin/contenthub"

echo "🚀 安装 ContentHub CLI..."

# 检查权限
if [ "$EUID" -ne 0 ]; then
  echo "❌ 请使用 sudo 运行此脚本"
  exit 1
fi

# 复制脚本
cp "$SCRIPT_SOURCE" "$INSTALL_DIR/contenthub"
chmod +x "$INSTALL_DIR/contenthub"

echo "✅ ContentHub CLI 已安装到 $INSTALL_DIR/contenthub"
echo "运行 'contenthub --version' 验证安装"
```

### 脚本特性

- **错误处理**: `set -e` 确保错误时退出
- **路径解析**: 自动定位到后端目录
- **参数传递**: 完整传递所有参数给 Python CLI
- **Python 路径**: 自动设置 PYTHONPATH

---

## 工具函数设计

### utils.py 功能模块

```python
from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
import rich.repr

console = Console()

# 输出格式化
def print_table(data: List[Dict], title: str = None):
    """打印表格"""
    if not data:
        console.print("[dim]无数据[/dim]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    # 添加列
    for key in data[0].keys():
        table.add_column(key)

    # 添加行
    for row in data:
        table.add_row(*[str(v) for v in row.values()])

    console.print(table)

def print_success(message: str):
    """打印成功消息"""
    console.print(f"✅ {message}")

def print_error(message: str):
    """打印错误消息"""
    console.print(f"❌ {message}", style="red")

def print_warning(message: str):
    """打印警告消息"""
    console.print(f"⚠️  {message}", style="yellow")

def print_info(message: str):
    """打印信息消息"""
    console.print(f"ℹ️  {message}", style="blue")

# 交互确认
def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作"""
    from rich.prompt import Confirm
    return Confirm.ask(message, default=default)

# 数据格式化
def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_bool(value: bool) -> str:
    """格式化布尔值"""
    return "✅" if value else "❌"

def format_json(data: Dict) -> str:
    """格式化 JSON"""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)

# 进度条
def show_progress(tasks: List[Dict]):
    """显示进度条"""
    with Progress() as progress:
        for task in tasks:
            task_id = progress.add_task(task["description"], total=task["total"])
            # 更新进度...
```

### config.py 配置管理

```python
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

class CLIConfig:
    """CLI 配置管理"""

    def __init__(self):
        self._load_env()

    def _load_env(self):
        """加载环境变量"""
        # 按优先级加载配置文件
        env_files = [
            Path("./contenthub.env"),
            Path.home() / ".contenthub.env",
            Path("/etc/contenthub/env"),
            Path("src/backend/.env")
        ]

        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                break

    @property
    def database_url(self) -> str:
        """数据库连接字符串"""
        return os.getenv("CLI_DB_PATH") or os.getenv(
            "DATABASE_URL",
            "sqlite:///./data/contenthub.db"
        )

    @property
    def creator_cli_path(self) -> Optional[str]:
        """content-creator 路径"""
        return os.getenv("CREATOR_CLI_PATH")

    @property
    def publisher_api_url(self) -> str:
        """发布服务 URL"""
        return os.getenv("PUBLISHER_API_URL", "http://localhost:3010")

    @property
    def publisher_api_key(self) -> Optional[str]:
        """发布服务 API 密钥"""
        return os.getenv("PUBLISHER_API_KEY")

    @property
    def tavily_api_key(self) -> Optional[str]:
        """Tavily API 密钥"""
        return os.getenv("TAVILY_API_KEY")

    @property
    def log_level(self) -> str:
        """日志级别"""
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def output_format(self) -> str:
        """输出格式"""
        return os.getenv("CLI_FORMAT", "table")

config = CLIConfig()
```

---

## 实施计划

### 阶段 1: 基础架构搭建（必须）

**优先级**: 🔴 高
**预计时间**: 2-3 天

- [ ] 添加依赖到 requirements.txt
  ```txt
  # CLI 框架
  typer[all]==0.12.0
  rich==13.7.0
  ```
- [ ] 创建 CLI 目录结构
  ```
  src/backend/cli/
  ├── __init__.py
  ├── main.py
  ├── config.py
  ├── utils.py
  └── modules/
  ```
- [ ] 实现主入口和工具函数
  - main.py: typer app 入口
  - utils.py: 输出格式化函数
  - config.py: 配置管理
- [ ] 创建 shell 脚本入口
  - bin/contenthub: 入口脚本
  - scripts/install-cli.sh: 安装脚本

### 阶段 2: 核心模块（高优先级）

**优先级**: 🔴 高
**预计时间**: 3-5 天

- [x] `db` 模块：数据库管理
  - init, reset, backup, restore, migrate, shell
- [x] `users` 模块：用户管理
  - CRUD, 角色管理, 密码管理
- [x] `accounts` 模块：账号管理
  - CRUD, 配置管理, 连接测试

### 阶段 3: 业务模块（中优先级）

**优先级**: 🟡 中
**预计时间**: 5-7 天

- [x] `content` 模块：内容管理
  - CRUD, 生成, 审核, 批量操作
- [x] `publisher` 模块：发布管理
  - 发布, 重试, 批量发布
- [x] `publish-pool` 模块：发布池
  - 列表, 添加, 移除, 优先级
- [x] `scheduler` 模块：定时任务
  - CRUD, 启停, 历史查询

### 阶段 4: 配置和查询（低优先级）

**优先级**: 🟢 低
**预计时间**: 3-4 天

- [x] `platform` 模块：平台管理
  - CRUD, API 测试
- [x] `customer` 模块：客户管理
  - CRUD, 统计信息
- [x] `config` 模块：系统配置
  - 写作风格, 内容主题, 系统参数
- [x] `audit` 模块：审计日志
  - 查询, 导出, 统计
- [x] `dashboard` 模块：仪表盘
  - 统计, 趋势, 活动
- [x] `system` 模块：系统管理
  - 健康检查, 缓存, 维护

### 阶段 5: 文档和测试（必须）

**优先级**: 🔴 高
**预计时间**: 2-3 天

- [ ] CLI 使用文档
  - 快速开始指南
  - 常见使用场景
  - 故障排除
- [ ] 命令参考手册
  - 完整命令列表
  - 参数说明
  - 示例代码
- [ ] 单元测试
  - 工具函数测试
  - 配置管理测试
- [ ] 集成测试
  - 端到端测试
  - 覆盖核心流程

---

## 设计原则

### 1. 简洁性

命令简短易记，类似 git/npm 的使用体验
```bash
./contenthub users list
./contenthub db init
```

### 2. 一致性

所有模块遵循相同的命名约定：
- 列表: `list`
- 创建: `create`
- 更新: `update <id>`
- 删除: `delete <id>`
- 详情: `info <id>`

### 3. 安全性

- 危险操作需要确认（如 `db reset`）
- 清晰的错误提示和警告信息
- 敏感操作记录审计日志
- CLI 假定管理员权限，无需认证

### 4. 易用性

- 自动生成完善的帮助文档
- 友好的表格化输出
- 清晰的进度反馈
- 支持多种输出格式

### 5. 可扩展性

- 模块化设计，易于添加新命令
- 统一的接口和工具函数
- 可复用的组件设计
- 复用现有 services 层

### 6. 架构一致性

- CLI 应该复用现有 services 层
- 保持业务逻辑一致性
- 自动处理权限验证
- 自动记录审计日志

---

## 依赖库

| 库 | 版本 | 用途 |
|---|------|------|
| typer[all] | 0.12.0+ | CLI 框架 |
| rich | 13.7.0+ | 终端美化 |
| python-dotenv | 1.0.0+ | 环境变量管理 |

**注意**: typer 和 rich 需要添加到 `src/backend/requirements.txt`

---

## 相关文档

- **CLI 参考手册**: [references/CLI-REFERENCE.md](../references/CLI-REFERENCE.md)（待创建）
- **系统设计文档**: [system-design.md](./system-design.md)
- **API 文档**: http://localhost:8010/docs

---

## 更新日志

### v1.2.0 (2026-02-04)
- ✅ 标记为已实施状态
- ✅ 添加实施总结链接
- ✅ 完成13个模块，123个命令
- ✅ 通过测试验证（95.7%通过率）

### v1.1.0 (2026-02-03)
- ✨ 新增 `publish-pool` 模块
- ✨ 补充环境变量配置章节
- ✨ 补充错误处理章节
- ✨ 补充使用示例章节
- ✨ 补充配置管理说明
- ✨ 补充权限控制说明
- ✨ 新增批量操作命令
- ✨ 新增系统维护命令
- 📝 更新目录结构（bin/ 目录）
- 📝 更新模块划分表
- 📝 更新实施计划

### v1.0.0 (2026-02-03)
- 🎉 初始版本
- ✨ 定义 CLI 架构和技术选型
- ✨ 设计命令结构和规范
- ✨ 规划 12 个功能模块

---

**维护者**: ContentHub 开发团队
**最后更新**: 2026-02-03
