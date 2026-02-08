# 异步内容生成 CLI 快速参考

## 概述

ContentHub 异步内容生成系统允许您在后台生成内容，无需等待 AI 完成工作。本文档提供了常用命令的快速参考。

## 快速开始

### 1. 生成内容（异步模式）

```bash
# 基本用法
contenthub content generate -a <账号ID> -t "<选题>" --async

# 完整示例
contenthub content generate \
  -a 49 \
  -t "AI技术发展" \
  --keywords "人工智能,机器学习" \
  --category "技术" \
  --requirements "写一篇深度技术文章" \
  --tone "专业严谨" \
  --priority 8 \
  --async \
  --auto-approve
```

**参数说明**:
- `-a, --account-id`: 账号 ID（必需）
- `-t, --topic`: 选题（必需）
- `-k, --keywords`: 关键词（逗号分隔）
- `-c, --category`: 内容板块
- `-r, --requirements`: 创作要求
- `--tone`: 语气风格
- `-p, --priority`: 优先级（1-10，默认：5）
- `--async`: 启用异步模式
- `--auto-approve/--no-auto-approve`: 是否自动审核（默认：auto-approve）

**输出示例**:
```
ℹ️  异步模式：正在提交任务...
✅ 异步任务已提交
ℹ️  任务ID: task-abc123def456
ℹ️  状态: pending
ℹ️
ℹ️  使用以下命令查看状态:
ℹ️    contenthub task status task-abc123def456
```

### 2. 查询任务状态

```bash
contenthub task status <task_id>
```

**示例**:
```bash
contenthub task status task-abc123def456
```

**输出示例**:
```
ℹ️  ⏳ 任务信息
 任务ID    task-abc123def456
 状态      ⏳ pending
 账号ID    49
 选题      AI技术发展
 优先级    8
 自动审核  是
 创建时间  2026-02-08 20:30:15
```

**状态说明**:
- ⏳ `pending`: 等待处理
- 📤 `submitted`: 已提交到生成器
- ⚙️ `processing`: 正在生成
- ✅ `completed`: 已完成
- ❌ `failed`: 失败
- ⏰ `timeout`: 超时
- 🚫 `cancelled`: 已取消

### 3. 列出任务

```bash
# 列出所有任务
contenthub task list

# 列出指定账号的任务
contenthub task list -a 49

# 列出指定状态的任务
contenthub task list -s pending
contenthub task list -s failed

# 限制显示数量
contenthub task list -n 50
```

**筛选选项**:
- `-a, --account-id`: 按账号 ID 筛选
- `-s, --status`: 按状态筛选（pending/submitted/processing/completed/failed/timeout/cancelled）
- `-n, --limit`: 限制显示数量（默认：20）

### 4. 取消任务

```bash
contenthub task cancel <task_id>
```

**示例**:
```bash
contenthub task cancel task-abc123def456
```

**注意**:
- 只有 `pending` 或 `submitted` 状态的任务可以取消
- 命令会要求您确认操作

### 5. 重试失败的任务

```bash
contenthub task retry <task_id>
```

**示例**:
```bash
contenthub task retry task-abc123def456
```

**注意**:
- 只有 `failed`、`timeout` 或 `cancelled` 状态的任务可以重试
- 有最大重试次数限制（默认：3 次）
- 命令会要求您确认操作

### 6. 查看任务统计

```bash
contenthub task stats
```

**输出示例**:
```
          任务统计
┏━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┓
┃ 状态      ┃ 数量 ┃ 占比   ┃
┡━━━━━━━━━━━╇━━━━━━╇━━━━━━━━┩
│ ⏳ pending │ 5    │ 25.0%  │
│ 📤 submitted│ 3    │ 15.0%  │
│ ⚙️ processing│ 2   │ 10.0%  │
│ ✅ completed│ 8   │ 40.0%  │
│ ❌ failed  │ 2    │ 10.0%  │
└───────────┴──────┴────────┘
ℹ️  总计: 20 个任务
```

### 7. 清理旧任务

```bash
# 清理 7 天前的旧任务（需要确认）
contenthub task cleanup --days 7

# 清理 30 天前的旧任务（跳过确认）
contenthub task cleanup -d 30 --yes
```

**注意**:
- 只清理已完成、失败、取消或超时的任务
- 不删除正在运行或等待的任务
- 操作不可恢复，请谨慎使用

## 常见使用场景

### 场景 1: 批量生成内容

```bash
# 提交多个异步任务
for topic in "AI技术" "机器学习" "深度学习" "自然语言处理" "计算机视觉"
do
  contenthub content generate -a 49 -t "$topic" --async --priority 7
done

# 查看所有任务
contenthub task list -s pending

# 查看统计
contenthub task stats
```

### 场景 2: 监控任务进度

```bash
# 提交任务
task_id=$(contenthub content generate -a 49 -t "AI技术" --async | grep "任务ID" | awk '{print $2}')

# 监控任务状态
while true
do
  clear
  contenthub task status $task_id
  sleep 5
done
```

### 场景 3: 处理失败任务

```bash
# 查看失败的任务
contenthub task list -s failed

# 重试所有失败的任务
for task_id in $(contenthub task list -s failed --format json | jq -r '.[].任务ID')
do
  contenthub task retry $task_id
done
```

### 场景 4: 定期清理

```bash
# 每周清理一次旧任务（添加到 crontab）
# 0 0 * * 0 cd /path/to/backend && python -m cli.main task cleanup -d 30 --yes
```

## 输出格式

所有命令支持多种输出格式：

```bash
# 默认表格格式
contenthub task list

# JSON 格式（便于脚本处理）
contenthub task list --format json

# CSV 格式（便于导入电子表格）
contenthub task list --format csv
```

## 获取帮助

```bash
# 查看主命令帮助
contenthub --help

# 查看 task 模块帮助
contenthub task --help

# 查看子命令帮助
contenthub task status --help
contenthub task list --help
contenthub task cancel --help
contenthub task retry --help
contenthub task cleanup --help
contenthub task stats --help
```

## 故障排查

### 问题 1: 任务一直处于 pending 状态

**原因**: 任务调度器可能未运行

**解决方案**:
```bash
# 检查调度器状态
contenthub scheduler status

# 启动调度器
contenthub scheduler start
```

### 问题 2: 任务失败

**原因**: 可能是 content-creator 配置问题或 API 错误

**解决方案**:
```bash
# 查看详细错误信息
contenthub task status <task_id>

# 检查配置
cat .env | grep CREATOR_CLI_PATH

# 重试任务
contenthub task retry <task_id>
```

### 问题 3: 找不到任务

**原因**: 任务 ID 可能输入错误

**解决方案**:
```bash
# 列出所有任务
contenthub task list

# 使用正确的任务 ID
contenthub task status <正确的任务ID>
```

## 最佳实践

1. **使用有意义的选题**: 选题清晰有助于生成更好的内容
2. **设置合适的优先级**: 重要任务设置更高的优先级（1-10）
3. **定期检查任务状态**: 使用 `task list` 和 `task stats` 监控任务
4. **及时处理失败任务**: 使用 `task retry` 重试失败的任务
5. **定期清理旧任务**: 使用 `task cleanup` 释放数据库空间
6. **使用 JSON 格式处理**: 脚本化操作时使用 `--format json`

## 相关文档

- [CLI 命令完整参考](/docs/references/CLI-REFERENCE.md)
- [Stage 3 实施总结](/docs/development/STAGE3-CLI-IMPLEMENTATION-SUMMARY.md)
- [异步内容生成架构](/docs/architecture/ASYNC-CONTENT-GENERATION.md)

---

**文档版本**: 1.0
**最后更新**: 2026-02-08
