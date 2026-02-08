# 异步内容生成系统 - 用户指南

## 概述

ContentHub 异步内容生成系统允许您在后台批量生成内容，无需等待 AI 完成。系统会自动管理任务队列、轮询状态、处理结果，并可选地自动审核和发布内容。

### 核心特性

- **异步任务提交**：快速提交多个生成任务，立即返回
- **自动状态轮询**：后台自动检查任务状态
- **智能结果处理**：自动创建内容记录并添加到发布池
- **任务监控**：实时查看任务状态和进度
- **自动审核**：可选的自动审核和发布流程
- **错误重试**：失败任务自动重试机制
- **调度器集成**：支持定时批量生成

## 快速开始

### 1. 提交异步任务

使用 CLI 命令提交异步任务：

```bash
# 基础用法
contenthub content generate \
  -a 49 \
  -t "AI技术发展" \
  --async

# 带自动审核
contenthub content generate \
  -a 49 \
  -t "AI技术发展" \
  --async \
  --auto-approve

# 完整参数
contenthub content generate \
  -a 49 \
  -t "智能客服系统" \
  -k "AI,客服,自动化" \
  --async \
  --auto-approve \
  --priority 8 \
  --requirements "详细介绍AI客服的优势"
```

**命令参数说明**：

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `-a, --account-id` | 账号 ID | 是 | - |
| `-t, --topic` | 内容选题 | 是 | - |
| `-k, --keywords` | 关键词（逗号分隔） | 否 | - |
| `--async` | 使用异步模式 | 是 | - |
| `--auto-approve` | 自动审核通过 | 否 | False |
| `--priority` | 任务优先级（0-10） | 否 | 5 |
| `--requirements` | 额外要求 | 否 | - |

**返回示例**：

```json
{
  "task_id": "task-abc123xyz",
  "status": "pending",
  "message": "任务已提交，正在处理中"
}
```

### 2. 监控任务状态

#### 查看单个任务状态

```bash
contenthub task status task-abc123xyz
```

**输出示例**：

```
任务 ID: task-abc123xyz
状态: processing
进度: 50%
提交时间: 2026-02-08 10:30:00
开始时间: 2026-02-08 10:30:30
完成时间: -
错误信息: -
```

#### 查看任务列表

```bash
# 查看所有待处理任务
contenthub monitor pending

# 查看特定账号的任务
contenthub task list --account-id 49 --status pending

# 查看失败的任务
contenthub monitor failed
```

#### 查看综合指标

```bash
contenthub monitor metrics
```

**输出示例**：

```
系统指标
========
总任务数: 150
待处理: 5
处理中: 3
已完成: 140
失败: 2

成功率: 98.6%
平均完成时间: 45.2秒
```

### 3. 设置定时任务

创建定时任务，自动批量生成内容：

```bash
contenthub scheduler create \
  --name "每日内容生成" \
  --type async_content_generation \
  --cron "0 8 * * *" \
  --params '{
    "account_ids": [49, 50, 51],
    "count_per_account": 3,
    "auto_approve": true,
    "priority": 7
  }'
```

**Cron 表达式说明**：

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6，0 = 周日)
│ │ │ │ │
* * * * *
```

**常用示例**：

- `"0 8 * * *"` - 每天早上 8 点
- `"0 */2 * * *"` - 每 2 小时
- `"0 0 * * 1"` - 每周一凌晨
- `"0 9,18 * * *"` - 每天早上 9 点和下午 6 点

#### 查看定时任务

```bash
# 列出所有定时任务
contenthub scheduler list

# 查看任务历史
contenthub scheduler history <job_id>

# 暂停任务
contenthub scheduler pause <job_id>

# 恢复任务
contenthub scheduler resume <job_id>
```

## 常见场景

### 场景 1: 批量生成

为多个账号批量生成内容：

```bash
#!/bin/bash
# batch-generate.sh

ACCOUNTS=(49 50 51 52 53)
TOPIC="AI技术发展趋势"

for account in "${ACCOUNTS[@]}"; do
  contenthub content generate \
    -a $account \
    -t "$TOPIC" \
    --async \
    --auto-approve
done

echo "批量任务提交完成"
```

### 场景 2: 自动化流程

设置完整的自动化流程：

```bash
# 1. 设置定时任务
contenthub scheduler create \
  --name "自动化内容生成" \
  --type async_content_generation \
  --cron "0 8,20 * * *" \
  --params '{
    "account_ids": [49, 50],
    "count_per_account": 5,
    "auto_approve": true
  }'

# 2. 监控执行情况
contenthub monitor stats --days 7

# 3. 查看失败任务并处理
contenthub monitor failed
```

### 场景 3: 高优先级任务

提交紧急任务：

```bash
contenthub content generate \
  -a 49 \
  -t "紧急：新产品发布" \
  --async \
  --auto-approve \
  --priority 10 \
  --requirements "突出产品核心优势，语气专业"
```

### 场景 4: 任务监控和告警

设置监控脚本：

```bash
#!/bin/bash
# monitor-tasks.sh

while true; do
  # 检查失败任务
  FAILED=$(contenthub monitor metrics --format json | jq '.failed_count')

  if [ "$FAILED" -gt 5 ]; then
    echo "警告：失败任务数量过多: $FAILED"
    # 发送告警通知
  fi

  # 等待 5 分钟
  sleep 300
done
```

## 配置说明

### 环境变量

在 `.env` 文件中配置：

```bash
# 启用异步生成
ASYNC_CONTENT_GENERATION_ENABLED=true

# 最大并发任务数
ASYNC_MAX_CONCURRENT_TASKS=5

# 任务超时时间（秒）
ASYNC_TASK_TIMEOUT=1800

# 状态轮询间隔（秒）
ASYNC_POLL_INTERVAL=30

# 自动审核
ASYNC_AUTO_APPROVE=true

# 最大重试次数
ASYNC_MAX_RETRIES=3
```

### 性能调优

根据服务器性能调整参数：

**低配置服务器**（2 核 4G）：

```bash
ASYNC_MAX_CONCURRENT_TASKS=2
ASYNC_POLL_INTERVAL=60
ASYNC_TASK_TIMEOUT=3600
```

**高配置服务器**（8 核 16G）：

```bash
ASYNC_MAX_CONCURRENT_TASKS=10
ASYNC_POLL_INTERVAL=15
ASYNC_TASK_TIMEOUT=1800
```

## 故障排查

### 任务卡住

**症状**：任务长时间处于 `processing` 状态

**排查步骤**：

```bash
# 1. 检查任务状态
contenthub task status task-id

# 2. 检查系统健康
contenthub monitor health

# 3. 查看日志
tail -f logs/app.log | grep "task-id"

# 4. 检查 content-creator 服务
./content-creator-cli.sh health
```

**解决方案**：

1. 检查 content-creator CLI 是否正常运行
2. 查看任务是否超时（默认 30 分钟）
3. 检查服务器资源使用情况
4. 重启服务（如果需要）

### 成功率低

**症状**：大量任务失败

**排查步骤**：

```bash
# 1. 查看失败任务
contenthub monitor failed

# 2. 统计失败原因
contenthub monitor stats --days 7 --format json | jq '.failure_reasons'

# 3. 查看错误日志
tail -f logs/app.log | grep "ERROR"
```

**常见原因**：

1. **账号配置错误**：检查账号 ID 和配置
2. **选题过于复杂**：简化选题或添加详细要求
3. **超时**：增加 `ASYNC_TASK_TIMEOUT` 值
4. **资源不足**：减少并发数或升级服务器

### 性能问题

**症状**：任务处理缓慢

**优化建议**：

```bash
# 1. 增加并发数
ASYNC_MAX_CONCURRENT_TASKS=10

# 2. 减少轮询间隔
ASYNC_POLL_INTERVAL=15

# 3. 使用定时任务避开高峰
contenthub scheduler create \
  --name "夜间生成" \
  --cron "0 2 * * *" \
  ...
```

### 数据库问题

**症状**：任务记录异常

**排查步骤**：

```bash
# 1. 检查数据库
sqlite3 data/contenthub.db "SELECT COUNT(*) FROM content_generation_tasks;"

# 2. 清理旧数据
python -c "
from app.db.database import SessionLocal
from app.models import ContentGenerationTask
from datetime import datetime, timedelta

db = SessionLocal()
cutoff = datetime.utcnow() - timedelta(days=30)
deleted = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == 'completed',
    ContentGenerationTask.completed_at < cutoff
).delete()
db.commit()
print(f'已清理 {deleted} 条旧记录')
"
```

## 高级用法

### 自定义任务参数

在 `requirements` 字段中使用 JSON 格式：

```bash
contenthub content generate \
  -a 49 \
  -t "AI 应用" \
  --async \
  --requirements '{
    "style": "专业",
    "length": "2000字",
    "sections": ["背景", "应用", "展望"],
    "tone": "客观"
  }'
```

### Webhook 回调（待实现）

配置 Webhook 接收任务完成通知：

```bash
# 设置环境变量
export WEBHOOK_URL="https://your-server.com/callback"

# 提交任务时会自动调用
```

### 批量导入任务

从 CSV 文件批量创建任务：

```bash
# tasks.csv
# account_id,topic,keywords,priority,auto_approve
# 49,"AI技术","AI,机器学习",8,true
# 50,"区块链应用","区块链,金融",7,false

python -m cli.main bulk-import --file tasks.csv --async
```

## 最佳实践

### 1. 任务分组

使用清晰的命名规范：

```bash
# 按日期分组
contenthub content generate -t "每日科技简报_20260208" --async

# 按系列分组
contenthub content generate -t "AI系列_第1期" --async
```

### 2. 优先级管理

合理设置优先级：

```bash
# 紧急新闻: 9-10
contenthub content generate -t "突发新闻" --async --priority 10

# 常规内容: 5-7
contenthub content generate -t "技术文章" --async --priority 6

# 备用内容: 0-4
contenthub content generate -t "存档内容" --async --priority 3
```

### 3. 错误处理

设置合理的重试策略：

```bash
# .env
ASYNC_MAX_RETRIES=3
ASYNC_RETRY_BACKOFF=60  # 重试间隔（秒）
```

### 4. 监控告警

建立监控机制：

```bash
# 定期检查
*/5 * * * * /path/to/monitor-tasks.sh

# 每日报告
0 9 * * * contenthub monitor stats --days 1 | mail -s "每日任务报告" admin@example.com
```

## API 参考

### REST API

除了 CLI，也可以使用 REST API：

```bash
# 提交任务
curl -X POST http://localhost:18010/api/v1/content/generate/async \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 49,
    "topic": "AI技术发展",
    "keywords": "AI,机器学习",
    "auto_approve": true,
    "priority": 8
  }'

# 查询状态
curl http://localhost:18010/api/v1/content/tasks/task-abc123

# 列出任务
curl http://localhost:18010/api/v1/content/tasks?account_id=49&status=pending
```

详细 API 文档：`/Users/Oychao/Documents/Projects/content-hub/src/backend/docs/api/async-content-api.md`

## 支持和反馈

如有问题或建议，请查看：

- **故障排查**：本文档的"故障排查"章节
- **日志文件**：`logs/app.log`
- **监控命令**：`contenthub monitor metrics`
- **API 文档**：http://localhost:18010/docs

---

**最后更新**：2026-02-08
**版本**：1.0.0
