# ContentHub CLI 阶段 5 命令参考

本文档提供阶段 5 实现的所有 CLI 命令的详细参考。

---

## 目录

- [platform - 平台管理](#platform---平台管理)
- [customer - 客户管理](#customer---客户管理)
- [config - 配置管理](#config---配置管理)
  - [writing-style - 写作风格](#writing-style---写作风格)
  - [content-theme - 内容主题](#content-theme---内容主题)
  - [system-params - 系统参数](#system-params---系统参数)
  - [platform-config - 平台配置](#platform-config---平台配置)
- [audit - 审计日志](#audit---审计日志)
- [dashboard - 仪表盘](#dashboard---仪表盘)
- [system - 系统管理](#system---系统管理)

---

## platform - 平台管理

管理内容发布平台（微信公众号、头条号等）。

### 命令列表

#### platform list

列出所有平台。

```bash
contenthub platform list [OPTIONS]
```

**选项**:
- `--status`, `-s`: 按状态筛选 (active/inactive)
- `--page`: 页码 (默认: 1)
- `--page-size`, `--size`: 每页数量 (默认: 20)

**示例**:
```bash
# 列出所有平台
contenthub platform list

# 只显示激活的平台
contenthub platform list --status active

# 显示第 2 页，每页 10 条
contenthub platform list --page 2 --page-size 10
```

#### platform create

创建新平台。

```bash
contenthub platform create [OPTIONS]
```

**选项**:
- `--name`, `-n`: 平台名称 (必需)
- `--code`, `-c`: 平台代码 (必需)
- `--type`, `-t`: 平台类型
- `--description`, `-d`: 平台描述
- `--api-url`: API 地址
- `--api-key`: API 密钥
- `--status`, `-s`: 平台状态 (active/inactive, 默认: active)

**示例**:
```bash
contenthub platform create \
  --name "微信公众号" \
  --code "wechat_mp" \
  --type "wechat" \
  --api-url "https://api.example.com" \
  --status active
```

#### platform update

更新平台信息。

```bash
contenthub platform update [PLATFORM_ID] [OPTIONS]
```

**参数**:
- `PLATFORM_ID`: 平台 ID (必需)

**选项**:
- `--name`, `-n`: 平台名称
- `--code`, `-c`: 平台代码
- `--type`, `-t`: 平台类型
- `--description`, `-d`: 平台描述
- `--api-url`: API 地址
- `--api-key`: API 密钥
- `--status`, `-s`: 平台状态 (active/inactive)

**示例**:
```bash
contenthub platform update 1 \
  --name "新名称" \
  --api-url "https://new-api.example.com"
```

#### platform delete

删除平台（需确认）。

```bash
contenthub platform delete [PLATFORM_ID]
```

**参数**:
- `PLATFORM_ID`: 平台 ID (必需)

**示例**:
```bash
contenthub platform delete 1
```

#### platform info

查看平台详情。

```bash
contenthub platform info [PLATFORM_ID]
```

**参数**:
- `PLATFORM_ID`: 平台 ID (必需)

**示例**:
```bash
contenthub platform info 1
```

#### platform test-api

测试平台 API 连接。

```bash
contenthub platform test-api [PLATFORM_ID] [OPTIONS]
```

**参数**:
- `PLATFORM_ID`: 平台 ID (必需)

**选项**:
- `--timeout`, `-t`: 超时时间（秒）(默认: 10)

**示例**:
```bash
contenthub platform test-api 1
contenthub platform test-api 1 --timeout 30
```

---

## customer - 客户管理

管理客户信息。

### 命令列表

#### customer list

列出所有客户。

```bash
contenthub customer list [OPTIONS]
```

**选项**:
- `--status`, `-s`: 按状态筛选 (active/inactive)
- `--page`: 页码 (默认: 1)
- `--page-size`, `--size`: 每页数量 (默认: 20)

**示例**:
```bash
contenthub customer list
contenthub customer list --status active
```

#### customer create

创建新客户。

```bash
contenthub customer create [OPTIONS]
```

**选项**:
- `--name`, `-n`: 客户名称 (必需)
- `--contact-name`, `-c`: 联系人姓名
- `--contact-email`, `-e`: 联系邮箱
- `--contact-phone`, `-p`: 联系电话
- `--description`, `-d`: 客户描述
- `--status`, `-s`: 客户状态 (active/inactive, 默认: active)

**示例**:
```bash
contenthub customer create \
  --name "示例公司" \
  --contact-name "张三" \
  --contact-email "contact@example.com" \
  --contact-phone "13800138000"
```

#### customer update

更新客户信息。

```bash
contenthub customer update [CUSTOMER_ID] [OPTIONS]
```

**参数**:
- `CUSTOMER_ID`: 客户 ID (必需)

**选项**: 与 create 相同

**示例**:
```bash
contenthub customer update 1 --name "新公司名称"
```

#### customer delete

删除客户（需确认）。

```bash
contenthub customer delete [CUSTOMER_ID]
```

**参数**:
- `CUSTOMER_ID`: 客户 ID (必需)

**示例**:
```bash
contenthub customer delete 1
```

#### customer info

查看客户详情。

```bash
contenthub customer info [CUSTOMER_ID]
```

**参数**:
- `CUSTOMER_ID`: 客户 ID (必需)

**示例**:
```bash
contenthub customer info 1
```

#### customer stats

查看客户统计信息（账号、内容、发布）。

```bash
contenthub customer stats [CUSTOMER_ID]
```

**参数**:
- `CUSTOMER_ID`: 客户 ID (必需)

**示例**:
```bash
contenthub customer stats 1
```

**输出示例**:
```
客户统计: 示例公司

┏━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 项目     ┃ 数量 ┃ 说明                            ┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 账号总数 │ 5    │ 该客户下的所有账号             │
│ 激活账号 │ 4    │ 当前激活的账号                 │
│ 内容总数 │ 120  │ 生成的所有内容                 │
│ 待审核   │ 10   │ 等待审核的内容                 │
│ 发布总数 │ 100  │ 尝试发布次数                   │
│ 发布成功 │ 95   │ 成功率 95.0%                   │
└──────────┴──────┴────────────────────────────────┘
```

#### customer accounts

列出客户的账号。

```bash
contenthub customer accounts [CUSTOMER_ID] [OPTIONS]
```

**参数**:
- `CUSTOMER_ID`: 客户 ID (必需)

**选项**:
- `--status`, `-s`: 按状态筛选 (active/inactive)

**示例**:
```bash
contenthub customer accounts 1
contenthub customer accounts 1 --status active
```

---

## config - 配置管理

管理系统配置，包括写作风格、内容主题、系统参数和平台配置。

### writing-style - 写作风格

#### writing-style list

列出写作风格。

```bash
contenthub config writing-style list [OPTIONS]
```

**选项**:
- `--system`: 仅显示系统级风格
- `--page`: 页码 (默认: 1)
- `--page-size`: 每页数量 (默认: 20)

**示例**:
```bash
contenthub config writing-style list
contenthub config writing-style list --system
```

#### writing-style create

创建写作风格。

```bash
contenthub config writing-style create [OPTIONS]
```

**选项**:
- `--name`, `-n`: 风格名称 (必需)
- `--code`, `-c`: 风格代码 (必需)
- `--tone`: 语气 (默认: 专业)
- `--persona`: 人设
- `--min-words`: 最小字数 (默认: 800)
- `--max-words`: 最大字数 (默认: 1500)
- `--emoji`: 表情使用（不使用/适度/频繁）(默认: 适度)
- `--forbidden`: 禁用词（逗号分隔）
- `--system`: 是否系统级 (默认: False)
- `--account-id`: 账号 ID（非系统级必需）

**示例**:
```bash
contenthub config writing-style create \
  --name "专业风格" \
  --code "professional" \
  --tone "专业" \
  --min-words 800 \
  --max-words 1500
```

#### writing-style update

更新写作风格。

```bash
contenthub config writing-style update [STYLE_ID] [OPTIONS]
```

**参数**:
- `STYLE_ID`: 风格 ID (必需)

**选项**: 与 create 相同（不需要 code 和 account-id）

#### writing-style delete

删除写作风格。

```bash
contenthub config writing-style delete [STYLE_ID]
```

**参数**:
- `STYLE_ID`: 风格 ID (必需)

#### writing-style info

查看写作风格详情。

```bash
contenthub config writing-style info [STYLE_ID]
```

**参数**:
- `STYLE_ID`: 风格 ID (必需)

---

### content-theme - 内容主题

#### content-theme list

列出内容主题。

```bash
contenthub config content-theme list [OPTIONS]
```

**选项**:
- `--system`: 仅显示系统级主题
- `--page`: 页码
- `--page-size`: 每页数量

#### content-theme create

创建内容主题。

```bash
contenthub config content-theme create [OPTIONS]
```

**选项**:
- `--name`, `-n`: 主题名称 (必需)
- `--code`, `-c`: 主题代码 (必需)
- `--type`, `-t`: 主题类型
- `--description`, `-d`: 主题描述
- `--system`: 是否系统级

**示例**:
```bash
contenthub config content-theme create \
  --name "技术分享" \
  --code "tech" \
  --type "技术"
```

#### content-theme update

更新内容主题。

```bash
contenthub config content-theme update [THEME_ID] [OPTIONS]
```

#### content-theme delete

删除内容主题。

```bash
contenthub config content-theme delete [THEME_ID]
```

#### content-theme info

查看内容主题详情。

```bash
contenthub config content-theme info [THEME_ID]
```

---

### system-params - 系统参数

#### system-params get

获取系统参数。

```bash
contenthub config system-params get [KEY]
```

**参数**:
- `KEY`: 参数键 (必需)

**示例**:
```bash
contenthub config system-params get DATABASE_URL
contenthub config system-params get APP_NAME
```

#### system-params set

设置系统参数（仅限当前会话）。

```bash
contenthub config system-params set [KEY] [VALUE]
```

**参数**:
- `KEY`: 参数键 (必需)
- `VALUE`: 参数值 (必需)

**注意**: 此设置仅在当前会话有效。如需永久设置，请修改 .env 文件。

**示例**:
```bash
contenthub config system-params set DEBUG true
```

#### system-params list

列出所有系统参数。

```bash
contenthub config system-params list [OPTIONS]
```

**选项**:
- `--filter`, `-f`: 过滤前缀

**示例**:
```bash
contenthub config system-params list
contenthub config system-params list --filter DATABASE
```

---

### platform-config - 平台配置

#### platform-config list

列出平台配置。

```bash
contenthub config platform-config list [OPTIONS]
```

**选项**:
- `--platform-id`, `-p`: 平台 ID

**注意**: 敏感信息（API 密钥）会被隐藏。

#### platform-config update

更新平台配置。

```bash
contenthub config platform-config update [PLATFORM_ID] [OPTIONS]
```

**参数**:
- `PLATFORM_ID`: 平台 ID (必需)

**选项**:
- `--api-url`: API 地址
- `--api-key`: API 密钥

**示例**:
```bash
contenthub config platform-config update 1 \
  --api-url "https://new-api.example.com" \
  --api-key "new-api-key"
```

---

## audit - 审计日志

查询和管理审计日志。

### 命令列表

#### audit logs

查询审计日志。

```bash
contenthub audit logs [OPTIONS]
```

**选项**:
- `--event-type`, `-e`: 事件类型
- `--user-id`, `-u`: 用户 ID
- `--result`, `-r`: 结果筛选 (success/failure)
- `--start`: 开始日期 (YYYY-MM-DD)
- `--end`: 结束日期 (YYYY-MM-DD)
- `--search`, `-s`: 搜索关键字
- `--page`: 页码 (默认: 1)
- `--page-size`: 每页数量 (默认: 20)

**示例**:
```bash
# 查看所有日志
contenthub audit logs

# 查看特定用户的日志
contenthub audit logs --user-id 1

# 查看特定日期范围的日志
contenthub audit logs --start 2026-01-01 --end 2026-01-31

# 查看失败的登录操作
contenthub audit logs --event-type user_login --result failure

# 搜索包含特定关键字的日志
contenthub audit logs --search "登录"
```

#### audit log-detail

查看审计日志详情。

```bash
contenthub audit log-detail [LOG_ID]
```

**参数**:
- `LOG_ID`: 日志 ID (必需)

**示例**:
```bash
contenthub audit log-detail 1
```

#### audit export

导出审计日志。

```bash
contenthub audit export [OPTIONS]
```

**选项**:
- `--start`, `-s`: 开始日期 (YYYY-MM-DD) (必需)
- `--end`, `-e`: 结束日期 (YYYY-MM-DD) (必需)
- `--event-type`: 事件类型筛选
- `--user-id`: 用户 ID 筛选
- `--result`: 结果筛选 (success/failure)
- `--output`, `-o`: 输出文件路径（可选，默认输出到控制台）

**示例**:
```bash
# 导出到控制台
contenthub audit export \
  --start 2026-01-01 \
  --end 2026-01-31

# 导出到文件
contenthub audit export \
  --start 2026-01-01 \
  --end 2026-01-31 \
  -o audit_2026_01.json

# 导出特定用户的日志
contenthub audit export \
  --start 2026-01-01 \
  --end 2026-01-31 \
  --user-id 1 \
  -o user1_audit.json
```

#### audit statistics

查看审计统计信息。

```bash
contenthub audit statistics [OPTIONS]
```

**选项**:
- `--start`, `-s`: 开始日期 (YYYY-MM-DD)
- `--end`, `-e`: 结束日期 (YYYY-MM-DD)

**示例**:
```bash
# 统计所有日志
contenthub audit statistics

# 统计特定时间段
contenthub audit statistics --start 2026-01-01 --end 2026-01-31
```

**输出示例**:
```
审计统计概览
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━┓
┃ 项目             ┃ 数量 ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━┩
│ 统计周期          │ (2026-01-01 至 2026-01-31) │
│ 日志总数          │ 1000 │
│ 成功操作          │ 950  │
│ 失败操作          │ 50   │
│ 成功率            │ 95.0%│
└───────────────────┴──────┘

事件类型统计:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┓
┃ 事件类型   ┃ 事件名称   ┃ 数量 ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━┩
│ user_login │ 用户登录   │ 500  │
│ content... │ 内容创建   │ 300  │
└────────────┴────────────┴──────┘

活跃用户 TOP 10:
┏━━━━━━━━━━┳━━━━━━━━━━┓
┃ 用户 ID  ┃ 操作次数 ┃
┡━━━━━━━━━━╇━━━━━━━━━━┩
│ 1        │ 150      │
│ 2        │ 120      │
└──────────┴──────────┘
```

#### audit user-activity

查看用户活动记录。

```bash
contenthub audit user-activity [USER_ID] [OPTIONS]
```

**参数**:
- `USER_ID`: 用户 ID (必需)

**选项**:
- `--days`, `-d`: 统计天数 (默认: 7)
- `--limit`, `-l`: 显示记录数 (默认: 50)

**示例**:
```bash
contenthub audit user-activity 1
contenthub audit user-activity 1 --days 30 --limit 100
```

---

## dashboard - 仪表盘

系统统计和数据分析。

### 命令列表

#### dashboard stats

显示仪表盘统计数据。

```bash
contenthub dashboard stats
```

**输出示例**:
```
仪表盘统计
┏━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 项目     ┃ 数量 ┃ 说明                            ┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 账号总数 │ 10   │ 系统中的所有账号               │
│ 激活账号 │ 8    │ 当前激活的账号                 │
│ 内容总数 │ 500  │ 生成的所有内容                 │
│ 待审核   │ 50   │ 等待审核的内容                 │
│ 已审核   │ 450  │ 通过审核的内容                 │
│ 发布成功 │ 400  │ 累计成功发布次数               │
│ 今日发布 │ 10   │ 今日成功发布次数               │
│ 本周发布 │ 50   │ 本周成功发布次数               │
┃ 定时任务 │ 5    │ 激活的定时任务                 │
│ 用户总数 │ 20   │ 系统用户数                     │
│ 客户总数 │ 10   │ 系统客户数                     │
└──────────┴──────┴────────────────────────────────┘
```

#### dashboard activities

显示最近的活动记录。

```bash
contenthub dashboard activities [OPTIONS]
```

**选项**:
- `--limit`, `-l`: 显示记录数 (默认: 20)

**示例**:
```bash
contenthub dashboard activities
contenthub dashboard activities --limit 50
```

#### dashboard content-trend

显示内容生成趋势。

```bash
contenthub dashboard content-trend [OPTIONS]
```

**选项**:
- `--days`, `-d`: 统计天数 (默认: 30)

**示例**:
```bash
contenthub dashboard content-trend
contenthub dashboard content-trend --days 90
```

**输出示例**:
```
内容生成趋势 (最近 30 天)
┏━━━━━━━━━━━━┳━━━━━━┳━━━━━━┓
┃ 日期       ┃ 数量 ┃ 占比 ┃
┡━━━━━━━━━━━━╇━━━━━━╇━━━━━━┩
│ 2026-01-01 │ 15   │ 5.0% │
│ 2026-01-02 │ 20   │ 6.7% │
│ 2026-01-03 │ 18   │ 6.0% │
└────────────┴──────┴──────┘

统计摘要:
  总计: 300 篇内容
  平均: 10.0 篇/天
  最高: 20 篇/天
  最低: 5 篇/天
```

#### dashboard publish-stats

显示发布统计信息。

```bash
contenthub dashboard publish-stats
```

**输出示例**:
```
发布统计概览
┏━━━━━━━━━━┳━━━━━━┳━━━━━━┓
┃ 项目     ┃ 数量 ┃ 占比 ┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━┩
│ 总发布数 │ 500  │ 100% │
│ 发布成功 │ 450  │ 90.0%│
│ 发布失败 │ 40   │ 8.0% │
│ 待发布   │ 10   │ 2.0% │
└──────────┴──────┴──────┘

按平台统计:
┏━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━┓
┃ 平台     ┃ 发布数 ┃ 成功数 ┃ 成功率 ┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━┩
│ 微信公众号 │ 300 │ 280 │ 93.3% │
│ 头条号   │ 200 │ 170 │ 85.0% │
└──────────┴──────┴──────┴────────┘
```

#### dashboard user-stats

显示用户统计信息。

```bash
contenthub dashboard user-stats [OPTIONS]
```

**选项**:
- `--limit`, `-l`: 显示用户数 (默认: 10)

**示例**:
```bash
contenthub dashboard user-stats
contenthub dashboard user-stats --limit 20
```

#### dashboard customer-stats

显示客户统计信息。

```bash
contenthub dashboard customer-stats [OPTIONS]
```

**选项**:
- `--limit`, `-l`: 显示客户数 (默认: 10)

**示例**:
```bash
contenthub dashboard customer-stats
contenthub dashboard customer-stats --limit 20
```

---

## system - 系统管理

系统监控和维护。

### 命令列表

#### system health

检查系统健康状态。

```bash
contenthub system health
```

**输出示例**:
```
系统健康状态
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ 组件             ┃ 状态            ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 整体状态          │ ✅ 健康         │
│ 数据库            │ ✅ 已连接       │
│ Redis             │ ✅ 可用         │
│ Content-Publisher │ ✅ 可用         │
│ Content-Creator   │ ⚠️  未找到       │
└───────────────────┴─────────────────┘
```

#### system info

显示系统信息。

```bash
contenthub system info
```

**输出示例**:
```
系统信息
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 项目     ┃ 值                             ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 应用名称 │ ContentHub                     │
│ 应用版本 │ v1.0.0                         │
│ Python 版本 │ 3.10.0                     │
│ 运行环境 │ 开发环境                       │
│ 操作系统 │ Linux-5.15.0-generic-x86_64   │
│ 架构     │ x86_64                         │
│ 调试模式 │ 开启                           │
└──────────┴────────────────────────────────┘
```

#### system version

显示版本信息。

```bash
contenthub system version
```

**输出**:
```
ContentHub v1.0.0
Python: 3.10.0
```

#### system metrics

显示系统指标。

```bash
contenthub system metrics
```

**输出示例**:
```
系统指标
┏━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 指标     ┃ 值           ┃ 说明                   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 运行时间 │ 2:15:30      │ 系统启动后的运行时间    │
│ 用户总数 │ 20           │ 系统注册用户数          │
│ 缓存命中 │ 1500         │ Redis 缓存命中次数      │
│ 缓存未命中 │ 300        │ Redis 缓存未命中次数    │
│ 命中率    │ 83.3%        │ 缓存命中率             │
│ 总请求数 │ 1800         │ 系统处理的总请求数      │
└──────────┴──────────────┴────────────────────────┘
```

#### system cache-stats

显示缓存统计信息。

```bash
contenthub system cache-stats
```

#### system cache-clear

清除缓存。

```bash
contenthub system cache-clear [OPTIONS]
```

**选项**:
- `--pattern`, `-p`: 清除模式（默认全部）

**示例**:
```bash
# 清除所有缓存
contenthub system cache-clear

# 按模式清除
contenthub system cache-clear --pattern "user:*"
contenthub system cache-clear --pattern "config:*"
```

#### system cache-cleanup

清理过期缓存。

```bash
contenthub system cache-cleanup [OPTIONS]
```

**选项**:
- `--max-age`, `-a`: 最大保留天数 (默认: 7)

**示例**:
```bash
contenthub system cache-cleanup
contenthub system cache-cleanup --max-age 30
```

#### system maintenance

维护模式管理。

```bash
contenthub system maintenance [OPTIONS]
```

**选项**:
- `--enable`, `-e`: 启用维护模式
- `--disable`, `-d`: 禁用维护模式

**示例**:
```bash
# 查看当前状态
contenthub system maintenance

# 启用维护模式
contenthub system maintenance --enable

# 禁用维护模式
contenthub system maintenance --disable
```

**注意**: 维护模式需要重启服务才能生效。请在 .env 文件中设置 `MAINTENANCE_MODE=true/false`。

#### system cleanup

清理系统资源。

```bash
contenthub system cleanup [OPTIONS]
```

**选项**:
- `--dry-run`: 仅显示将要清理的资源，不实际执行
- `--older-than`: 清理多少天前的资源 (默认: 30)

**示例**:
```bash
# 预览将要清理的资源
contenthub system cleanup --dry-run

# 清理 60 天前的资源
contenthub system cleanup --older-than 60

# 清理 30 天前的资源（实际执行）
contenthub system cleanup
```

**输出示例**:
```
可清理资源
┏━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 资源类型        ┃ 数量 ┃ 说明                    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 已拒绝内容      │ 50   │ 30 天前被拒绝的内容      │
│ 审计日志        │ 1000 │ 30 天前的日志            │
│ 失败发布记录    │ 20   │ 30 天前失败的发布        │
└─────────────────┴──────┴────────────────────────┘
```

#### system logs

查看系统日志。

```bash
contenthub system logs [OPTIONS]
```

**选项**:
- `--lines`, `-n`: 显示行数 (默认: 50)
- `--module`, `-m`: 模块筛选
- `--level`, `-l`: 日志级别筛选 (DEBUG/INFO/WARNING/ERROR)

**示例**:
```bash
# 查看最近 50 行日志
contenthub system logs

# 查看最近 100 行日志
contenthub system logs --lines 100

# 筛选特定模块
contenthub system logs --module content

# 筛选错误日志
contenthub system logs --level ERROR

# 组合筛选
contenthub system logs --lines 200 --level ERROR --module publisher
```

---

## 通用选项

所有命令都支持以下全局选项：

```bash
contenthub [global-options] <module> <command> [command-options]
```

**全局选项**:
- `--format`: 输出格式 (table/json/csv, 默认: table)
- `--debug`: 调试模式
- `--quiet`: 静默模式（仅输出错误）
- `--user`: 操作用户（用于审计，默认: cli-user）
- `--help`: 显示帮助信息

**示例**:
```bash
# 使用 JSON 格式输出
contenthub --format json platform list

# 调试模式
contenthub --debug customer list

# 指定操作用户
contenthub --user admin platform create --name "测试平台" --code "test"
```

---

## 常见用例

### 用例 1: 快速查看系统状态

```bash
# 检查系统健康
contenthub system health

# 查看仪表盘统计
contenthub dashboard stats

# 查看最近活动
contenthub dashboard activities --limit 30
```

### 用例 2: 客户管理

```bash
# 创建客户
contenthub customer create \
  --name "新客户" \
  --contact-name "联系人" \
  --contact-email "contact@example.com"

# 查看客户统计
contenthub customer stats 1

# 查看客户的账号
contenthub customer accounts 1
```

### 用例 3: 平台配置

```bash
# 创建平台
contenthub platform create \
  --name "微信公众号" \
  --code "wechat_mp" \
  --type "wechat" \
  --api-url "https://api.example.com"

# 测试 API 连接
contenthub platform test-api 1

# 更新配置
contenthub config platform-config update 1 \
  --api-key "new-key"
```

### 用例 4: 审计和监控

```bash
# 查看最近的审计日志
contenthub audit logs --page-size 50

# 查看特定用户的活动
contenthub audit user-activity 1 --days 7

# 导出月度审计报告
contenthub audit export \
  --start 2026-01-01 \
  --end 2026-01-31 \
  -o audit_2026_01.json

# 查看审计统计
contenthub audit statistics --start 2026-01-01
```

### 用例 5: 系统维护

```bash
# 检查系统健康
contenthub system health

# 查看系统指标
contenthub system metrics

# 清理缓存
contenthub system cache-clear

# 预览可清理的资源
contenthub system cleanup --dry-run

# 查看系统日志
contenthub system logs --lines 100 --level ERROR
```

---

## 获取帮助

每个命令和模块都支持 `--help` 选项查看详细帮助：

```bash
# 查看主帮助
contenthub --help

# 查看模块帮助
contenthub platform --help
contenthub customer --help

# 查看命令帮助
contenthub platform list --help
contenthub customer stats --help
```

---

**文档版本**: v1.0.0
**更新时间**: 2026-02-04
**ContentHub CLI**: 阶段 5 - 配置与查询模块
