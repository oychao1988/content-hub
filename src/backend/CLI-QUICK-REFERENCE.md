# ContentHub CLI 快速参考指南

版本: v1.0.0
更新时间: 2026-02-03

## 快速开始

### 设置环境变量

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
export PYTHONPATH=/Users/Oychao/Documents/Projects/content-hub/src/backend
```

### 查看帮助

```bash
# 查看所有模块
python cli/main.py --help

# 查看模块帮助
python cli/main.py db --help
python cli/main.py users --help

# 查看命令帮助
python cli/main.py db info --help
python cli/main.py users create --help
```

## DB 模块 - 数据库管理

### 常用命令

```bash
# 查看数据库信息
python cli/main.py db info

# 查看数据库统计
python cli/main.py db stats

# 备份数据库（默认路径）
python cli/main.py db backup

# 备份数据库（指定路径）
python cli/main.py db backup /tmp/backup.db

# 恢复数据库（需要确认）
python cli/main.py db restore /tmp/backup.db

# 初始化数据库
python cli/main.py db init

# 重置数据库（危险操作，需要确认）
python cli/main.py db reset

# 进入 SQLite shell
python cli/main.py db shell
```

### 命令说明

| 命令 | 参数 | 说明 | 危险操作 |
|------|------|------|----------|
| `db info` | 无 | 显示数据库路径、大小、表数量 | 否 |
| `db stats` | 无 | 显示所有表的记录数 | 否 |
| `db backup` | [output_path] | 备份数据库到指定路径 | 否 |
| `db restore` | <backup_file> | 从备份文件恢复数据库 | 是 |
| `db init` | 无 | 初始化数据库（创建所有表） | 否 |
| `db reset` | 无 | 删除并重新创建数据库 | 是 |
| `db migrate` | 无 | 运行数据库迁移（占位） | 否 |
| `db rollback` | [--steps N] | 回滚 N 步迁移（占位） | 否 |
| `db shell` | 无 | 进入 SQLite 交互式 shell | 否 |

## Users 模块 - 用户管理

### 常用命令

```bash
# 列出所有用户
python cli/main.py users list

# 列出管理员
python cli/main.py users list --role admin

# 列出已激活用户
python cli/main.py users list --status active

# 分页查看
python cli/main.py users list --page 1 --page-size 10

# 创建用户（自动生成密码）
python cli/main.py users create \
  --username newuser \
  --email newuser@example.com \
  --role operator

# 创建用户（指定密码）
python cli/main.py users create \
  --username newuser \
  --email newuser@example.com \
  --role operator \
  --password MySecurePassword123

# 查看用户详情
python cli/main.py users info 1

# 更新用户
python cli/main.py users update 1 \
  --full-name "系统管理员" \
  --email admin@contenthub.com

# 设置用户角色
python cli/main.py users set-role 2 --role admin

# 修改密码（自动生成）
python cli/main.py users change-password 2

# 修改密码（指定新密码）
python cli/main.py users change-password 2 --new-password NewPass123!

# 重置密码（生成随机密码）
python cli/main.py users reset-password 2

# 激活用户
python cli/main.py users activate 2

# 停用用户（需要确认）
python cli/main.py users deactivate 2

# 删除用户（需要确认）
python cli/main.py users delete 2
```

### 命令说明

| 命令 | 参数 | 说明 | 危险操作 |
|------|------|------|----------|
| `users list` | [--role] [--status] [--page] [--page-size] | 列出用户 | 否 |
| `users create` | --username <u> --email <e> [--full-name] [--role] [--password] | 创建用户 | 否 |
| `users info` | <user_id> | 查看用户详情 | 否 |
| `users update` | <user_id> [--email] [--full-name] [--role] | 更新用户 | 否 |
| `users set-role` | <user_id> --role <r> | 设置角色 | 否 |
| `users activate` | <user_id> | 激活用户 | 否 |
| `users deactivate` | <user_id> | 停用用户 | 是 |
| `users change-password` | <user_id> [--new-password] | 修改密码 | 否 |
| `users reset-password` | <user_id> | 重置密码 | 否 |
| `users delete` | <user_id> | 删除用户 | 是 |

### 角色说明

- **admin** - 管理员，拥有所有权限
- **operator** - 操作员，拥有内容管理权限
- **customer** - 客户，拥有查看权限

### 状态说明

- **active** - 激活状态，用户可以登录
- **inactive** - 停用状态，用户无法登录

## 常见问题

### 1. 如何生成随机密码？

创建用户时不指定 `--password` 参数，系统会自动生成 12 位随机密码：

```bash
python cli/main.py users create \
  --username newuser \
  --email newuser@example.com \
  --role operator
```

输出示例：
```
ℹ️  已生成随机密码: aB1$cD2%eF3&
✅ 用户创建成功 (ID: 3)
```

### 2. 如何批量创建用户？

目前不支持批量创建，需要逐个创建。建议使用脚本循环调用：

```bash
#!/bin/bash
while IFS=, read -r username email role; do
  python cli/main.py users create \
    --username "$username" \
    --email "$email" \
    --role "$role"
done < users.csv
```

### 3. 如何导出用户列表？

当前版本不支持直接导出，可以使用以下方法：

```bash
# 方法 1: 复制终端输出
python cli/main.py users list

# 方法 2: 使用 SQLite 查询
python cli/main.py db shell
sqlite> .mode csv
sqlite> .output users.csv
sqlite> SELECT id, username, email, role, is_active FROM users;
sqlite> .quit
```

### 4. 如何安全地删除用户？

删除前建议先停用用户并确认：

```bash
# 1. 查看用户详情
python cli/main.py users info 5

# 2. 停用用户
python cli/main.py users deactivate 5

# 3. 确认无误后删除
python cli/main.py users delete 5
```

### 5. 数据库备份保留在哪里？

默认备份位置：`./data/backups/`

文件名格式：`contenthub_YYYYMMDD_HHMMSS.db`

示例：
```
./data/backups/contenthub_20260203_224200.db
```

## 最佳实践

### 1. 定期备份数据库

```bash
# 添加到 crontab（每天凌晨 2 点备份）
0 2 * * * cd /path/to/backend && PYTHONPATH=/path/to/backend python cli/main.py db backup
```

### 2. 使用强密码

- 长度至少 12 位
- 包含大小写字母、数字、特殊字符
- 避免使用常见单词

### 3. 定期审查用户

```bash
# 查看所有用户
python cli/main.py users list

# 查看停用的用户
python cli/main.py users list --status inactive

# 删除不再需要的用户
python cli/main.py users delete <user_id>
```

### 4. 监控数据库大小

```bash
# 查看数据库信息
python cli/main.py db info

# 查看统计信息
python cli/main.py db stats
```

## 输出格式说明

### 表格输出

所有列表命令使用 Rich 表格输出，支持：
- 自动列宽
- 表头样式（bold magenta）
- 行线分隔
- 数据居中对齐

### 状态图标

- ✅ 成功操作
- ❌ 错误操作
- ⚠️  警告信息
- ℹ️  一般信息

### 时间格式

所有时间显示为：`YYYY-MM-DD HH:MM:SS`

示例：`2026-02-03 22:42:06`

## 错误处理

### 常见错误

#### 1. ModuleNotFoundError: No module named 'cli'

**解决**:
```bash
export PYTHONPATH=/Users/Oychao/Documents/Projects/content-hub/src/backend
```

#### 2. 数据库文件不存在

**解决**:
```bash
python cli/main.py db init
```

#### 3. 邮箱已被使用

**解决**:
```bash
# 检查邮箱是否已存在
python cli/main.py users list | grep email@example.com
```

#### 4. 用户不存在

**解决**:
```bash
# 列出所有用户查看 ID
python cli/main.py users list
```

## 调试技巧

### 启用详细输出

```bash
# 查看详细日志
python cli/main.py --debug db info
```

### 查看数据库内容

```bash
# 进入 SQLite shell
python cli/main.py db shell

# 查看所有表
sqlite> .tables

# 查看表结构
sqlite> .schema users

# 执行查询
sqlite> SELECT * FROM users;
```

### 导出查询结果

```bash
python cli/main.py db shell
sqlite> .mode csv
sqlite> .output output.csv
sqlite> SELECT * FROM users;
sqlite> .quit
```

## 相关文档

- [完整实现报告](./CLI-IMPLEMENTATION-REPORT.md)
- [项目 README](./README.md)
- [数据库设计](./docs/ARCHITECTURE.md)

## 技术支持

如有问题或建议，请联系开发团队或提交 Issue。
