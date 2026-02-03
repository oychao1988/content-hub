# ContentHub CLI 命令参考手册

> **版本**: 1.0.0
> **创建日期**: 2026-02-03
> **状态**: ❌ 待实施
> **对应设计**: [cli-system-design.md](../design/cli-system-design.md)

---

## 目录

- [快速开始](#快速开始)
- [安装](#安装)
- [全局选项](#全局选项)
- [命令参考](#命令参考)
  - [数据库管理 (db)](#数据库管理-db)
  - [用户管理 (users)](#用户管理-users)
  - [账号管理 (accounts)](#账号管理-accounts)
  - [内容管理 (content)](#内容管理-content)
  - [定时任务 (scheduler)](#定时任务-scheduler)
  - [发布管理 (publisher)](#发布管理-publisher)
  - [发布池管理 (publish-pool)](#发布池管理-publish-pool)
  - [平台管理 (platform)](#平台管理-platform)
  - [客户管理 (customer)](#客户管理-customer)
  - [系统配置 (config)](#系统配置-config)
  - [审计日志 (audit)](#审计日志-audit)
  - [系统管理 (system)](#系统管理-system)
  - [仪表盘 (dashboard)](#仪表盘-dashboard)
- [常见使用场景](#常见使用场景)
- [常见问题](#常见问题)
- [错误代码](#错误代码)

---

## 快速开始

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/your-org/content-hub.git
cd content-hub

# 2. 安装依赖
cd src/backend
pip install -r requirements.txt

# 3. 安装 CLI（可选）
sudo bash scripts/install-cli.sh

# 4. 验证安装
./contenthub --version
# 或
contenthub --version
```

### 首次使用

```bash
# 1. 初始化数据库
./contenthub db init

# 2. 创建管理员用户
./contenthub users create \
  --username admin \
  --email admin@example.com \
  --role admin

# 3. 查看系统状态
./contenthub system health
```

### 获取帮助

```bash
# 查看所有命令
./contenthub --help

# 查看特定模块帮助
./contenthub users --help

# 查看特定命令帮助
./contenthub users create --help
```

---

## 安装

### 方式1：使用安装脚本（推荐）

```bash
sudo bash scripts/install-cli.sh
```

安装后可以直接使用 `contenthub` 命令：

```bash
contenthub --version
contenthub users list
```

### 方式2：手动安装

```bash
# 创建符号链接
sudo ln -s $(pwd)/bin/contenthub /usr/local/bin/contenthub

# 或添加到 PATH
export PATH="$PATH:$(pwd)/bin"
```

### 方式3：直接使用

```bash
# 从项目根目录
./bin/contenthub --version
```

---

## 全局选项

这些选项可以用于任何命令：

| 选项 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--format` | `-f` | 输出格式（table/json/csv） | `--format json` |
| `--debug` | `-d` | 启用调试模式 | `--debug` |
| `--quiet` | `-q` | 静默模式（仅输出错误） | `--quiet` |
| `--user` | `-u` | 指定操作用户（用于审计） | `--user operator-1` |
| `--help` | `-h` | 显示帮助信息 | `--help` |
| `--version` | `-v` | 显示版本信息 | `--version` |

### 示例

```bash
# JSON 格式输出
./contenthub users list --format json

# 调试模式
./contenthub content generate --account-id 1 --topic "AI" --debug

# 指定操作用户
./contenthub users create --username test --user admin
```

---

## 命令参考

## 数据库管理 (db)

数据库管理命令用于初始化、备份、恢复和维护数据库。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `db init` | 初始化数据库 | ❌ |
| `db reset` | 重置数据库（删除所有数据） | ⚠️ 是 |
| `db backup [output-path]` | 备份数据库 | ❌ |
| `db restore <backup-file>` | 恢复数据库 | ⚠️ 是 |
| `db migrate` | 运行数据库迁移 | ❌ |
| `db rollback [steps]` | 回滚迁移 | ⚠️ 是 |
| `db shell` | 进入数据库 shell（SQLite） | ❌ |
| `db info` | 显示数据库信息 | ❌ |
| `db stats` | 数据库统计信息 | ❌ |

### 详细说明

#### db init

初始化数据库，创建所有表和初始数据。

```bash
./contenthub db init
```

**输出示例**:
```
✅ 数据库初始化成功
路径：sqlite:///./data/contenthub.db
```

#### db reset

重置数据库，删除所有数据并重新初始化。⚠️ **危险操作，需要确认**

```bash
./contenthub db reset
```

**交互示例**:
```
⚠️  警告：即将重置数据库，所有数据将丢失！
此操作不可逆，请确认是否继续？[y/N]: y
✅ 数据库已重置
```

#### db backup

备份数据库到指定路径。

```bash
# 备份到默认位置（./backups/）
./contenthub db backup

# 备份到指定路径
./contenthub db backup /path/to/backup.db
```

**参数**:
- `output-path` (可选): 备份文件路径，默认为 `./backups/contenthub_YYYYMMDD.db`

**输出示例**:
```
✅ 数据库备份成功
文件：./backups/contenthub_20260203.db
大小：2.5 MB
```

#### db restore

从备份文件恢复数据库。⚠️ **会覆盖当前数据库**

```bash
./contenthub db restore ./backups/contenthub_20260203.db
```

**参数**:
- `backup-file` (必需): 备份文件路径

**交互示例**:
```
⚠️  警告：即将从备份恢复数据库，当前数据将被覆盖！
备份文件：./backups/contenthub_20260203.db
确认是否继续？[y/N]: y
✅ 数据库已恢复
```

#### db migrate

运行数据库迁移，更新数据库结构。

```bash
./contenthub db migrate
```

**输出示例**:
```
✅ 数据库迁移完成
迁移版本：001 → 002
```

#### db rollback

回滚数据库迁移。

```bash
# 回滚一步
./contenthub db rollback

# 回滚多步
./contenthub db rollback 3
```

**参数**:
- `steps` (可选): 回滚步数，默认为 1

#### db shell

进入 SQLite 数据库交互式 shell。

```bash
./contenthub db shell
```

**在 shell 中可以执行 SQL**:
```sql
.tables          # 查看所有表
.schema users     # 查看表结构
SELECT * FROM users LIMIT 10;
.quit            # 退出
```

#### db info

显示数据库信息。

```bash
./contenthub db info
```

**输出示例**:
```
┌────────────────────┬──────────────────┐
│ 数据库路径         │ ./data/contenthub.db │
├────────────────────┼──────────────────┤
│ 数据库大小         │ 2.5 MB           │
├────────────────────┼──────────────────┤
│ 数据库版本         │ 1                │
├────────────────────┼──────────────────┤
│ 表数量             │ 13               │
└────────────────────┴──────────────────┘
```

#### db stats

显示数据库统计信息。

```bash
./contenthub db stats
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 表名               │ 记录数   │
├────────────────────┼──────────┤
│ users              │ 5        │
│ customers          │ 3        │
│ platforms          │ 2        │
│ accounts           │ 12       │
│ contents           │ 156      │
│ publish_logs       │ 89       │
│ scheduled_tasks    │ 5        │
│ audit_logs         │ 234      │
└────────────────────┴──────────┘
```

---

## 用户管理 (users)

用户管理命令用于创建、管理和控制系统用户。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `users list` | 列出用户 | ❌ |
| `users create` | 创建新用户 | ❌ |
| `users update <id>` | 更新用户信息 | ❌ |
| `users delete <id>` | 删除用户 | ⚠️ 是 |
| `users info <id>` | 查看用户详情 | ❌ |
| `users activate <id>` | 激活用户 | ❌ |
| `users deactivate <id>` | 停用用户 | ❌ |
| `users change-password <id>` | 修改密码 | ❌ |
| `users set-role <id>` | 设置用户角色 | ❌ |
| `users reset-password <id>` | 重置密码（生成随机密码） | ❌ |

### 详细说明

#### users list

列出用户，支持筛选和分页。

```bash
# 列出所有用户
./contenthub users list

# 按角色筛选
./contenthub users list --role admin
./contenthub users list --role operator
./contenthub users list --role customer

# 按状态筛选
./contenthub users list --status active
./contenthub users list --status inactive

# 分页
./contenthub users list --page 1 --page-size 20
```

**参数**:
- `--role` (可选): 用户角色（admin/operator/customer）
- `--status` (可选): 用户状态（active/inactive）
- `--page` (可选): 页码，默认为 1
- `--page-size` (可选): 每页数量，默认为 20

**输出示例**:
```
┌────┬──────────┬─────────────────┬─────────┬──────────┐
│ ID │ 用户名   │ 邮箱            │ 角色    │ 状态     │
├────┼──────────┼─────────────────┼─────────┼──────────┤
│ 1  │ admin    │ admin@ex...     │ admin   │ active   │
│ 2  │ operator1│ op1@ex...       │ operator│ active   │
│ 3  │ customer1│ cust1@ex...     │ customer│ active   │
└────┴──────────┴─────────────────┴─────────┴──────────┘
共 3 条记录，第 1/1 页
```

#### users create

创建新用户。

```bash
./contenthub users create \
  --username admin \
  --email admin@example.com \
  --role admin
```

**必需参数**:
- `--username`: 用户名
- `--email`: 邮箱地址
- `--role`: 用户角色（admin/operator/customer）

**可选参数**:
- `--full-name`: 全名
- `--password`: 密码（不提供则自动生成）
- `--phone`: 手机号

**角色说明**:
- `admin`: 管理员，拥有所有权限
- `operator`: 操作员，拥有内容管理权限
- `customer`: 客户，只能操作自己的资源

**输出示例**:
```
✅ 用户创建成功
用户ID：1
用户名：admin
邮箱：admin@example.com
角色：admin
状态：active
```

#### users update

更新用户信息。

```bash
./contenthub users update 1 \
  --email newemail@example.com \
  --full-name "管理员"
```

**必需参数**:
- `id`: 用户ID

**可选参数**:
- `--email`: 新邮箱
- `--full-name`: 新全名
- `--phone`: 新手机号

#### users delete

删除用户。⚠️ **危险操作，需要确认**

```bash
./contenthub users delete 5
```

**交互示例**:
```
⚠️  警告：即将删除用户 "test-user"
此操作不可逆，请确认是否继续？[y/N]: y
✅ 用户已删除
```

#### users info

查看用户详情。

```bash
./contenthub users info 1
```

**输出示例**:
```
┌────────────────────┬──────────────────┐
│ 用户ID             │ 1                │
├────────────────────┼──────────────────┤
│ 用户名             │ admin            │
├────────────────────┼──────────────────┤
│ 邮箱               │ admin@ex...      │
├────────────────────┼──────────────────┤
│ 全名               │ 系统管理员       │
├────────────────────┼──────────────────┤
│ 角色               │ admin            │
├────────────────────┼──────────────────┤
│ 状态               │ active           │
├────────────────────┼──────────────────┤
│ 创建时间           │ 2026-02-03 10:00 │
├────────────────────┼──────────────────┤
│ 最后登录           │ 2026-02-03 15:30 │
└────────────────────┴──────────────────┘
```

#### users activate / users deactivate

激活或停用用户。

```bash
./contenthub users activate 5
./contenthub users deactivate 5
```

#### users change-password

修改用户密码。

```bash
# 交互式输入密码
./contenthub users change-password 1

# 或者直接指定（不安全，仅用于测试）
./contenthub users change-password 1 --new-password "newpass123"
```

#### users set-role

设置用户角色。

```bash
./contenthub users set-role 1 --role admin
```

**参数**:
- `--role`: 新角色（admin/operator/customer）

#### users reset-password

重置用户密码（生成随机密码）。

```bash
./contenthub users reset-password 5
```

**输出示例**:
```
✅ 密码已重置
用户ID：5
新密码：a7Bf9xK2
⚠️  请妥善保管此密码，并建议用户首次登录后修改
```

---

## 账号管理 (accounts)

账号管理命令用于管理运营账号，包括创建、配置和测试平台连接。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `accounts list` | 列出账号 | ❌ |
| `accounts create` | 创建账号 | ❌ |
| `accounts update <id>` | 更新账号 | ❌ |
| `accounts delete <id>` | 删除账号 | ⚠️ 是 |
| `accounts info <id>` | 查看账号详情 | ❌ |
| `accounts list-config <id>` | 查看完整配置 | ❌ |
| `accounts import-md <id> <file>` | 从 Markdown 导入配置 | ❌ |
| `accounts export-md <id> [path]` | 导出配置到 Markdown | ❌ |
| `accounts test-connection <id>` | 测试平台连接 | ❌ |
| `accounts writing-style <id>` | 管理写作风格 | ❌ |
| `accounts publish-config <id>` | 管理发布配置 | ❌ |

### 详细说明

#### accounts list

列出账号，支持筛选和分页。

```bash
# 列出所有账号
./contenthub accounts list

# 按客户筛选
./contenthub accounts list --customer-id 1

# 按平台筛选
./contenthub accounts list --platform-id 1

# 按状态筛选
./contenthub accounts list --status active
```

**参数**:
- `--customer-id` (可选): 客户ID
- `--platform-id` (可选): 平台ID
- `--status` (可选): 状态（active/inactive）

**输出示例**:
```
┌────┬──────────────────┬─────────┬──────────┬──────────┐
│ ID │ 账号名称         │ 客户    │ 平台     │ 状态     │
├────┼──────────────────┼─────────┼──────────┼──────────┤
│ 1  │ 客户A-公众号      │ 客户A   │ 微信公众号 │ active   │
│ 2  │ 客户B-头条号      │ 客户B   │ 今日头条 │ active   │
└────┴──────────────────┴─────────┴──────────┴──────────┘
```

#### accounts create

创建新账号。

```bash
./contenthub accounts create \
  --name "客户A-微信公众号" \
  --customer-id 1 \
  --platform-id 1
```

**必需参数**:
- `--name`: 账号名称
- `--customer-id`: 客户ID
- `--platform-id`: 平台ID

**可选参数**:
- `--description`: 描述
- `--wechat-app-id`: 微信 AppID
- `--wechat-app-secret`: 微信 AppSecret

**输出示例**:
```
✅ 账号创建成功
账号ID：1
名称：客户A-微信公众号
客户：客户A
平台：微信公众号
```

#### accounts update

更新账号信息。

```bash
./contenthub accounts update 1 \
  --name "新账号名" \
  --description "账号描述"
```

#### accounts test-connection

测试平台连接。

```bash
./contenthub accounts test-connection 1
```

**输出示例**:
```
✅ 连接成功
平台：微信公众号
AppID：wx1234567890
响应时间：235 ms
```

**失败示例**:
```
❌ 连接失败
平台：微信公众号
错误：AppSecret 验证失败
提示：请检查 AppSecret 配置是否正确
```

#### accounts export-md

导出账号配置到 Markdown 文件。

```bash
# 导出到默认路径
./contenthub accounts export-md 1

# 导出到指定路径
./contenthub accounts export-md 1 ./configs/
```

**输出示例**:
```
✅ 配置已导出
文件：./configs/account-1.md
```

---

## 内容管理 (content)

内容管理命令用于创建、生成、审核和管理内容。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `content list` | 列出内容 | ❌ |
| `content create` | 创建内容 | ❌ |
| `content generate` | 生成内容 | ❌ |
| `content batch-generate` | 批量生成内容 | ❌ |
| `content topic-search` | 选题搜索 | ❌ |
| `content update <id>` | 更新内容 | ❌ |
| `content delete <id>` | 删除内容 | ⚠️ 是 |
| `content info <id>` | 查看详情 | ❌ |
| `content submit-review <id>` | 提交审核 | ❌ |
| `content approve <id>` | 审核通过 | ❌ |
| `content reject <id>` | 审核拒绝 | ❌ |
| `content review-list` | 待审核列表 | ❌ |
| `content statistics` | 审核统计 | ❌ |

### 详细说明

#### content generate

使用 content-creator 生成内容。

```bash
./contenthub content generate \
  --account-id 1 \
  --topic "AI 技术在内容创作中的应用"
```

**必需参数**:
- `--account-id`: 账号ID
- `--topic`: 文章选题

**可选参数**:
- `--section-code`: 内容板块代码
- `--save-draft`: 保存为草稿（不提交审核）

**输出示例**:
```
⏳ 正在生成内容，请稍候...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✅ 内容生成成功
内容ID：123
标题：AI 技术在内容创作中的应用
字数：1,526
图片：已下载
```

#### content batch-generate

批量生成内容。

```bash
./contenthub content batch-generate \
  --account-id 1 \
  --count 5
```

**参数**:
- `--account-id`: 账号ID
- `--count`: 生成数量

**输出示例**:
```
⏳ 正在批量生成 5 篇内容...
[1/5] ✅ 完成
[2/5] ✅ 完成
[3/5] ✅ 完成
[4/5] ✅ 完成
[5/5] ✅ 完成

✅ 批量生成完成
成功：5 篇
失败：0 篇
内容ID：124, 125, 126, 127, 128
```

#### content topic-search

搜索选题。

```bash
./contenthub content topic-search \
  --account-id 1 \
  --keywords "AI,技术趋势,自动化"
```

**参数**:
- `--account-id`: 账号ID
- `--keywords`: 关键词（逗号分隔）

**输出示例**:
```
┌──────┬────────────────────────────┬──────────┐
│ 排名 │ 选题                       │ 相关度   │
├──────┼────────────────────────────┼──────────┤
│ 1    │ AI 代理：内容自动化的未来   │ 0.95     │
│ 2    │ 2026 年内容创作技术趋势     │ 0.89     │
│ 3    │ 如何用 AI 提升内容质量      │ 0.87     │
└──────┴────────────────────────────┴──────────┘
```

#### content approve

审核通过内容。

```bash
./contenthub content approve 123 --comment "内容质量优秀"
```

**参数**:
- `--comment`: 审核意见（可选）

#### content review-list

查看待审核列表。

```bash
./contenthub content review-list
```

**输出示例**:
```
┌──────┬────────────────────┬─────────┬──────────┐
│ ID   │ 标题               │ 账号    │ 提交时间 │
├──────┼────────────────────┼─────────┼──────────┤
│ 123  │ AI 技术应用         │ 客户A   │ 10:30    │
│ 124  │ 自动化工具推荐      │ 客户A   │ 10:35    │
│ 125  │ 内容创作指南        │ 客户B   │ 10:40    │
└──────┴────────────────────┴─────────┴──────────┘
共 3 篇待审核
```

---

## 定时任务 (scheduler)

定时任务管理命令用于创建、管理和控制定时任务。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `scheduler list` | 列出任务 | ❌ |
| `scheduler create` | 创建任务 | ❌ |
| `scheduler update <id>` | 更新任务 | ❌ |
| `scheduler delete <id>` | 删除任务 | ⚠️ 是 |
| `scheduler info <id>` | 任务详情 | ❌ |
| `scheduler trigger <id>` | 手动触发任务 | ❌ |
| `scheduler history` | 执行历史 | ❌ |
| `scheduler start` | 启动调度器 | ❌ |
| `scheduler stop` | 停止调度器 | ❌ |
| `scheduler status` | 调度器状态 | ❌ |
| `scheduler pause <id>` | 暂停任务 | ❌ |
| `scheduler resume <id>` | 恢复任务 | ❌ |

### 详细说明

#### scheduler create

创建定时任务。

```bash
./contenthub scheduler create \
  --name "每日内容生成" \
  --type content_generation \
  --cron "0 9 * * *" \
  --account-id 1
```

**必需参数**:
- `--name`: 任务名称
- `--type`: 任务类型（content_generation/batch_publish/system_cleanup）
- `--cron`: Cron 表达式

**可选参数**:
- `--account-id`: 账号ID（content_generation 需要）
- `--enabled`: 是否启用（默认 true）
- `--description`: 任务描述

**Cron 表达式示例**:
```
0 9 * * *     # 每天早上9点
0 */2 * * *   # 每2小时
0 0 * * 1     # 每周一凌晨
```

#### scheduler status

查看调度器状态。

```bash
./contenthub scheduler status
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 状态               │ running  │
├────────────────────┼──────────┤
│ 运行中任务数       │ 3        │
├────────────────────┼──────────┤
│ 暂停任务数         │ 1        │
├────────────────────┼──────────┤
│ 今日执行次数       │ 12       │
├────────────────────┼──────────┤
│ 下次执行时间       │ 09:00    │
└────────────────────┴──────────┘
```

#### scheduler start / scheduler stop

启动或停止调度器。

```bash
./contenthub scheduler start
./contenthub scheduler stop
```

---

## 发布管理 (publisher)

发布管理命令用于手动发布、重试和批量发布内容。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `publisher history` | 发布历史 | ❌ |
| `publisher publish <id>` | 手动发布 | ❌ |
| `publisher retry <id>` | 重试发布 | ❌ |
| `publisher batch-publish` | 批量发布 | ❌ |
| `publisher records` | 发布记录 | ❌ |
| `publisher stats` | 发布统计 | ❌ |

### 详细说明

#### publisher publish

手动发布内容。

```bash
./contenthub publisher publish 123
```

**输出示例**:
```
⏳ 正在发布...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✅ 发布成功
内容ID：123
平台：微信公众号
媒体ID：media_id_xxxxx
发布时间：2026-02-03 15:30:00
```

#### publisher batch-publish

批量发布内容。

```bash
./contenthub publisher batch-publish --limit 5
```

**参数**:
- `--limit`: 发布数量限制（默认为 5）

#### publisher stats

查看发布统计。

```bash
./contenthub publisher stats
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 总发布次数         │ 256      │
├────────────────────┼──────────┤
│ 成功次数           │ 245      │
├────────────────────┼──────────┤
│ 失败次数           │ 11       │
├────────────────────┼──────────┤
│ 成功率             │ 95.7%    │
├────────────────────┼──────────┤
│ 今日发布           │ 12       │
└────────────────────┴──────────┘
```

---

## 发布池管理 (publish-pool)

发布池管理命令用于管理待发布内容的优先级和计划发布时间。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `publish-pool list` | 列出待发布内容 | ❌ |
| `publish-pool add <id>` | 添加到发布池 | ❌ |
| `publish-pool remove <id>` | 从发布池移除 | ❌ |
| `publish-pool set-priority <id>` | 设置优先级 | ❌ |
| `publish-pool schedule <id>` | 设置计划发布时间 | ❌ |
| `publish-pool publish` | 从发布池发布 | ❌ |
| `publish-pool clear` | 清空发布池 | ⚠️ 是 |
| `publish-pool stats` | 发布池统计 | ❌ |

### 详细说明

#### publish-pool list

列出待发布内容。

```bash
./contenthub publish-pool list
```

**输出示例**:
```
┌──────┬────────────────────┬──────────┬──────────┬─────────────┐
│ ID   │ 标题               │ 优先级   │ 状态     │ 计划时间    │
├──────┼────────────────────┼──────────┼──────────┼─────────────┤
│ 123  │ AI 技术应用         │ 1        │ pending  │ 09:00       │
│ 124  │ 自动化工具          │ 2        │ pending  │ 10:00       │
│ 125  │ 内容创作指南        │ 5        │ pending  │ -           │
└──────┴────────────────────┴──────────┴──────────┴─────────────┘
共 3 篇待发布
```

#### publish-pool set-priority

设置内容优先级。

```bash
./contenthub publish-pool set-priority 123 --priority 1
```

**参数**:
- `--priority`: 优先级（1-10，数字越小优先级越高）

#### publish-pool schedule

设置计划发布时间。

```bash
./contenthub publish-pool schedule 123 --time "2026-02-04 09:00"
```

**参数**:
- `--time`: 发布时间（格式：YYYY-MM-DD HH:MM）

---

## 平台管理 (platform)

平台管理命令用于管理支持的平台。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `platform list` | 列出平台 | ❌ |
| `platform create` | 创建平台 | ❌ |
| `platform update <id>` | 更新平台 | ❌ |
| `platform delete <id>` | 删除平台 | ⚠️ 是 |
| `platform info <id>` | 平台详情 | ❌ |
| `platform test-api <id>` | 测试平台 API | ❌ |

### 详细说明

#### platform create

创建平台。

```bash
./contenthub platform create \
  --name "微信公众号" \
  --code wechat \
  --api-url "https://api.weixin.qq.com"
```

**必需参数**:
- `--name`: 平台名称
- `--code`: 平台代码（唯一标识）

**可选参数**:
- `--api-url`: API 地址
- `--description`: 平台描述
- `--type`: 平台类型

---

## 客户管理 (customer)

客户管理命令用于管理客户信息。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `customer list` | 列出客户 | ❌ |
| `customer create` | 创建客户 | ❌ |
| `customer update <id>` | 更新客户 | ❌ |
| `customer delete <id>` | 删除客户 | ⚠️ 是 |
| `customer info <id>` | 客户详情 | ❌ |
| `customer stats <id>` | 客户统计 | ❌ |
| `customer accounts <id>` | 查看客户的账号列表 | ❌ |

### 详细说明

#### customer create

创建客户。

```bash
./contenthub customer create \
  --name "客户A" \
  --contact-name "张三" \
  --contact-email "zhangsan@example.com"
```

**必需参数**:
- `--name`: 客户名称

**可选参数**:
- `--contact-name`: 联系人姓名
- `--contact-email`: 联系人邮箱
- `--contact-phone`: 联系人电话
- `--description`: 客户描述

#### customer stats

查看客户统计信息。

```bash
./contenthub customer stats 1
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 账号数量           │ 3        │
├────────────────────┼──────────┤
│ 内容总数           │ 156      │
├────────────────────┼──────────┤
│ 已发布内容         │ 142      │
├────────────────────┼──────────┤
│ 待发布内容         │ 14       │
├────────────────────┼──────────┤
│ 本月新增内容       │ 23       │
└────────────────────┴──────────┘
```

---

## 系统配置 (config)

系统配置命令用于管理写作风格、内容主题和系统参数。

### 命令列表

#### 写作风格管理

```bash
./contenthub config writing-style list
./contenthub config writing-style create --name <name>
./contenthub config writing-style update <id>
./contenthub config writing-style delete <id>
./contenthub config writing-style info <id>
```

#### 内容主题管理

```bash
./contenthub config content-theme list
./contenthub config content-theme create --name <name>
./contenthub config content-theme update <id>
./contenthub config content-theme delete <id>
./contenthub config content-theme info <id>
```

#### 系统参数管理

```bash
./contenthub config system-params get [--key]
./contenthub config system-params set --key <key> --value <value>
./contenthub config system-params list
```

### 详细说明

#### config writing-style create

创建写作风格。

```bash
./contenthub config writing-style create \
  --name "专业风格" \
  --tone "专业、严谨" \
  --min-words 1000 \
  --max-words 2000
```

**参数**:
- `--name`: 风格名称（必需）
- `--tone`: 语气风格
- `--min-words`: 最小字数
- `--max-words`: 最大字数
- `--description`: 描述
- `--persona`: 人格设定
- `--emoji-usage`: 表情使用（never/moderate/frequent）

#### config system-params set

设置系统参数。

```bash
./contenthub config system-params set \
  --key scheduler.enabled \
  --value true
```

**常用系统参数**:
- `scheduler.enabled`: 是否启用调度器
- `publisher.batch_size`: 批量发布数量
- `content.default_review_mode`: 默认审核模式

---

## 审计日志 (audit)

审计日志命令用于查询、导出和分析系统操作日志。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `audit logs` | 查询日志 | ❌ |
| `audit log-detail <id>` | 日志详情 | ❌ |
| `audit export` | 导出日志 | ❌ |
| `audit statistics` | 审计统计 | ❌ |
| `audit user-activity <id>` | 用户活动日志 | ❌ |

### 详细说明

#### audit logs

查询审计日志。

```bash
# 查询所有日志
./contenthub audit logs

# 按事件类型筛选
./contenthub audit logs --event-type user_login

# 按结果筛选
./contenthub audit logs --result failure

# 按日期范围筛选
./contenthub audit logs --start-date 2026-02-01 --end-date 2026-02-03

# 按用户筛选
./contenthub audit logs --user-id 1
```

**参数**:
- `--event-type`: 事件类型
- `--user-id`: 用户ID
- `--result`: 结果（success/failure）
- `--start-date`: 开始日期（YYYY-MM-DD）
- `--end-date`: 结束日期（YYYY-MM-DD）
- `--page`: 页码
- `--page-size`: 每页数量

**事件类型列表**:
- `user_login`: 用户登录
- `user_create`: 创建用户
- `account_create`: 创建账号
- `content_generate`: 生成内容
- `content_publish`: 发布内容
- `db_backup`: 数据库备份
- 系统所有敏感操作

#### audit export

导出审计日志。

```bash
./contenthub audit export \
  --start-date 2026-02-01 \
  --end-date 2026-02-03 \
  --output audit-logs.csv \
  --format csv
```

**参数**:
- `--start-date`: 开始日期
- `--end-date`: 结束日期
- `--output`: 输出文件路径
- `--format`: 输出格式（csv/json）

---

## 系统管理 (system)

系统管理命令用于健康检查、缓存管理和系统维护。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `system health` | 健康检查 | ❌ |
| `system info` | 系统信息 | ❌ |
| `system version` | 版本信息 | ❌ |
| `system metrics` | 系统指标 | ❌ |
| `system cache-stats` | 缓存统计 | ❌ |
| `system cache-clear` | 清空缓存 | ❌ |
| `system cache-cleanup` | 清理过期缓存 | ❌ |
| `system maintenance` | 维护模式控制 | ❌ |
| `system cleanup` | 清理临时文件 | ❌ |
| `system logs` | 查看系统日志 | ❌ |

### 详细说明

#### system health

系统健康检查。

```bash
./contenthub system health
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 数据库             │ ✅ OK    │
├────────────────────┼──────────┤
│ 调度器             │ ✅ 运行中│
├────────────────────┼──────────┤
│ 发布服务           │ ✅ 可用  │
├────────────────────┼──────────┤
│ 磁盘空间           │ ✅ 45%   │
├────────────────────┼──────────┤
│ 内存使用           │ ✅ 62%   │
└────────────────────┴──────────┘
```

#### system metrics

查看系统指标。

```bash
./contenthub system metrics
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ CPU 使用率         │ 23%      │
├────────────────────┼──────────┤
│ 内存使用           │ 62%      │
├────────────────────┼──────────┤
│ 磁盘使用           │ 45%      │
├────────────────────┼──────────┤
│ 数据库连接数       │ 5/10     │
├────────────────────┼──────────┤
│ 运行中任务数       │ 3        │
└────────────────────┴──────────┘
```

#### system maintenance

控制维护模式。

```bash
# 启用维护模式
./contenthub system maintenance --enable

# 禁用维护模式
./contenthub system maintenance --disable
```

**维护模式下**:
- 禁止所有内容生成和发布操作
- 显示维护提示给用户
- 管理员仍可访问系统

#### system cleanup

清理临时文件。

```bash
./contenthub system cleanup
```

**清理内容**:
- 临时缓存文件
- 过期日志文件
- 临时上传文件

---

## 仪表盘 (dashboard)

仪表盘命令用于查看统计数据和趋势分析。

### 命令列表

| 命令 | 说明 | 危险 |
|------|------|------|
| `dashboard stats` | 统计数据 | ❌ |
| `dashboard activities` | 最近活动 | ❌ |
| `dashboard content-trend` | 内容趋势 | ❌ |
| `dashboard publish-stats` | 发布统计 | ❌ |
| `dashboard user-stats` | 用户统计 | ❌ |
| `dashboard customer-stats` | 客户统计 | ❌ |

### 详细说明

#### dashboard stats

查看系统统计数据。

```bash
./contenthub dashboard stats
```

**输出示例**:
```
┌────────────────────┬──────────┐
│ 总用户数           │ 15       │
├────────────────────┼──────────┤
│ 总客户数           │ 8        │
├────────────────────┼──────────┤
│ 总账号数           │ 24       │
├────────────────────┼──────────┤
│ 总内容数           │ 1,567    │
├────────────────────┼──────────┤
│ 今日发布           │ 12       │
├────────────────────┼──────────┤
│ 待审核内容         │ 5        │
└────────────────────┴──────────┘
```

#### dashboard content-trend

查看内容趋势。

```bash
# 查看最近7天
./contenthub dashboard content-trend --days 7

# 查看最近30天
./contenthub dashboard content-trend --days 30
```

**输出示例**:
```
┌────────────┬─────────┬─────────┬─────────┐
│ 日期       │ 生成    │ 发布    │ 审核通过 │
├────────────┼─────────┼─────────┼─────────┤
│ 02-01      │ 23      │ 20      │ 22      │
├────────────┼─────────┼─────────┼─────────┤
│ 02-02      │ 25      │ 24      │ 23      │
├────────────┼─────────┼─────────┼─────────┤
│ 02-03      │ 18      │ 17      │ 18      │
└────────────┴─────────┴─────────┴─────────┘
```

---

## 常见使用场景

### 场景1：快速开始

```bash
# 1. 初始化数据库
./contenthub db init

# 2. 创建管理员
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
  --contact-name "张三"

# 2. 创建账号
./contenthub accounts create \
  --name "客户A-公众号" \
  --customer-id 1 \
  --platform-id 1

# 3. 测试连接
./contenthub accounts test-connection 1
```

### 场景3：内容生成与发布

```bash
# 1. 生成内容
./contenthub content generate \
  --account-id 1 \
  --topic "AI 技术应用"

# 2. 审核通过
./contenthub content approve 1

# 3. 发布
./contenthub publisher publish 1
```

### 场景4：批量操作

```bash
# 1. 批量生成
./contenthub content batch-generate \
  --account-id 1 \
  --count 5

# 2. 批量审核
./contenthub content review-list
# 使用审核ID批量通过

# 3. 批量发布
./contenthub publisher batch-publish --limit 5
```

### 场景5：定时任务

```bash
# 1. 创建定时任务
./contenthub scheduler create \
  --name "每日内容生成" \
  --type content_generation \
  --cron "0 9 * * *" \
  --account-id 1

# 2. 启动调度器
./contenthub scheduler start

# 3. 查看状态
./contenthub scheduler status
```

---

## 常见问题

### Q1: 如何查看完整命令列表？

```bash
./contenthub --help
```

### Q2: 如何查看特定模块的帮助？

```bash
./contenthub <module> --help

# 示例
./contenthub users --help
./contenthub content generate --help
```

### Q3: 如何导出数据？

```bash
# JSON 格式
./contenthub users list --format json > users.json

# CSV 格式
./contenthub accounts list --format csv > accounts.csv

# 导出审计日志
./contenthub audit export --output logs.csv
```

### Q4: 如何调试问题？

```bash
# 启用调试模式
./contenthub content generate --account-id 1 --topic "AI" --debug

# 查看系统日志
./contenthub system logs --tail 50 --level DEBUG
```

### Q5: 数据库连接失败怎么办？

```bash
# 1. 检查数据库文件是否存在
./contenthub db info

# 2. 初始化数据库（如果不存在）
./contenthub db init

# 3. 检查配置
cat src/backend/.env | grep DATABASE_URL
```

### Q6: 如何重置系统？

```bash
# ⚠️ 危险操作，会删除所有数据

# 1. 停止调度器
./contenthub scheduler stop

# 2. 备份当前数据
./contenthub db backup ./backups/before_reset.db

# 3. 重置数据库
./contenthub db reset

# 4. 重新初始化
./contenthub db init
```

### Q7: 忘记管理员密码怎么办？

```bash
# 重置密码
./contenthub users reset-password 1

# 或修改密码
./contenthub users change-password 1 --new-password "newpass123"
```

---

## 错误代码

| 代码 | 说明 | 解决方案 |
|------|------|----------|
| `0` | 成功 | - |
| `1` | 通用错误 | 查看错误信息 |
| `2` | 数据库错误 | 检查数据库连接，运行 `db init` |
| `3` | 配置错误 | 检查 `.env` 文件 |
| `4` | 权限错误 | 检查文件权限 |
| `5` | 资源不存在 | 检查ID是否正确 |
| `6` | 参数错误 | 使用 `--help` 查看正确参数 |
| `7` | 外部服务错误 | 检查外部服务配置 |
| `8` | 网络错误 | 检查网络连接 |

---

## 附录

### A. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `CREATOR_CLI_PATH` | content-creator 路径 | - |
| `PUBLISHER_API_URL` | 发布服务地址 | `http://localhost:3010` |
| `PUBLISHER_API_KEY` | 发布服务密钥 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CLI_FORMAT` | 输出格式 | `table` |

### B. 配置文件位置

```
1. ./contenthub.env              # 当前目录
2. ~/.contenthub.env             # 用户主目录
3. /etc/contenthub/env           # 系统配置目录
4. src/backend/.env              # 开发环境
```

### C. 退出代码

| 代码 | 说明 |
|------|------|
| `0` | 成功 |
| `1` | 通用错误 |
| `2` | 数据库错误 |
| `3` | 配置错误 |

### D. 相关文档

- [CLI 系统设计](../design/cli-system-design.md)
- [系统设计文档](../design/system-design.md)
- [API 文档](http://localhost:8010/docs)

---

**维护者**: ContentHub 开发团队
**最后更新**: 2026-02-03
**版本**: 1.0.0
