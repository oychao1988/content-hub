# 发布池自动发布使用指南

## 概述

PublishPoolScannerExecutor 是 ContentHub 的发布池扫描执行器，用于自动扫描发布池并批量发布待发布内容。本文档提供了完整的使用说明、配置示例和最佳实践。

## 核心功能

### 1. 自动扫描

定期扫描发布池中状态为 `pending` 的待发布内容，无需人工干预。

### 2. 智能排序

按以下优先级顺序排序待发布内容：
1. **优先级**（priority）：数值越高越优先（1-10）
2. **计划时间**（scheduled_at）：时间越早越优先
3. **添加时间**（added_at）：时间越早越优先

### 3. 批量发布

单次可配置批量发布数量，避免一次性发布过多内容。

### 4. 容错机制

单个任务失败不影响其他任务，自动记录失败原因并更新重试次数。

## 快速开始

### 方式一：通过 CLI 创建定时任务

```bash
# 进入后端目录
cd src/backend

# 创建定时任务
python -m cli.main scheduler create \
  --name "发布池自动扫描" \
  --type "publish_pool_scanner" \
  --cron "*/5 * * * *" \
  --params '{"max_batch_size": 10, "check_future_tasks": true}' \
  --description "定期扫描发布池并批量发布待发布内容"
```

### 方式二：通过 API 创建定时任务

```bash
curl -X POST http://localhost:18010/api/v1/scheduler/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "发布池自动扫描",
    "description": "定期扫描发布池并批量发布待发布内容",
    "task_type": "publish_pool_scanner",
    "params": {
      "max_batch_size": 10,
      "check_future_tasks": true
    },
    "cron_expression": "*/5 * * * *",
    "is_active": true
  }'
```

### 方式三：通过数据库直接创建

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from datetime import datetime

db = SessionLocal()
try:
    task = ScheduledTask(
        name='发布池自动扫描',
        description='定期扫描发布池并批量发布待发布内容',
        task_type='publish_pool_scanner',
        params={
            'max_batch_size': 10,
            'check_future_tasks': True
        },
        cron_expression='*/5 * * * *',
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(task)
    db.commit()
    print(f'✅ 定时任务创建成功, ID: {task.id}')
finally:
    db.close()
```

## 参数配置

### max_batch_size（单次最大发布数量）

**类型**: 整数
**默认值**: 10
**范围**: 1-100

**说明**: 单次扫描最多发布的任务数量。

**推荐配置**:
- **测试环境**: 3-5
- **生产环境**: 10-20
- **大批量发布**: 30-50

**示例**:
```json
{
    "max_batch_size": 20
}
```

### check_future_tasks（是否检查未来任务）

**类型**: 布尔值
**默认值**: false

**说明**:
- `false`: 只扫描已到计划时间的任务（或没有设定时间的任务）
- `true`: 扫描所有待发布任务，包括计划在未来发布的任务

**使用场景**:

**场景 1**: 只发布到期的任务（推荐）
```json
{
    "check_future_tasks": false
}
```

**场景 2**: 预加载所有任务，手动控制发布时机
```json
{
    "check_future_tasks": true
}
```

## Cron 表达式配置

### 常用表达式

| 频率 | Cron 表达式 | 说明 |
|------|------------|------|
| 每5分钟 | `*/5 * * * *` | 推荐配置，平衡及时性和性能 |
| 每10分钟 | `*/10 * * * *` | 适用于低频发布场景 |
| 每小时 | `0 * * * *` | 适用于定时批量发布 |
| 每天上午9点 | `0 9 * * *` | 适用于固定时间发布 |
| 工作日每小时 | `0 9-18 * * 1-5` | 工作时间每小时发布 |

### Cron 表达式格式

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日期 (1 - 31)
│ │ │ ┌───────────── 月份 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6，0=周日)
│ │ │ │ │
* * * * *
```

### 特殊字符

| 字符 | 说明 | 示例 |
|------|------|------|
| `*` | 任意值 | `* * * * *`（每分钟） |
| `*/n` | 每n单位 | `*/5 * * * *`（每5分钟） |
| `,` | 多个值 | `0,15,30,45 * * * *`（每15分钟） |
| `-` | 范围 | `0 9-18 * * *`（9点到18点） |
| `?` | 不指定（日期和星期互斥） | `0 9 ? * MON-FRI`（工作日早上9点） |

## 发布池任务优先级

### 优先级级别

| 优先级 | 数值 | 使用场景 |
|--------|------|----------|
| 紧急 | 10 | 突发新闻、重要公告 |
| 高 | 8-9 | 优质内容、首发文章 |
| 中 | 5-7 | 常规内容、计划发布 |
| 低 | 1-4 | 备用内容、测试内容 |

### 设置优先级

```python
from app.db.database import SessionLocal
from app.models.publisher import PublishPool
from datetime import datetime

db = SessionLocal()
try:
    # 添加到发布池时设置优先级
    pool_entry = PublishPool(
        content_id=123,
        priority=10,  # 高优先级
        scheduled_at=None,  # 立即发布
        status='pending',
        added_at=datetime.now()
    )
    db.add(pool_entry)
    db.commit()
finally:
    db.close()
```

## 监控和日志

### 查看任务执行日志

```bash
# 查看最近的调度器日志
docker logs contenthub-backend --tail 100 | grep "发布池扫描"

# 查看特定任务的执行历史
python -m cli.main scheduler info <task_id>
```

### 日志关键字

搜索以下关键字了解执行情况：

- **开始扫描**: `开始扫描发布池`
- **找到任务**: `找到 X 个待发布任务`
- **正在发布**: `正在发布: pool_id=`
- **发布成功**: `发布池扫描完成: 扫描 X 个任务, 成功 X 个, 失败 X 个`
- **无任务**: `发布池中没有待发布的任务`
- **跳过任务**: `已达到最大重试次数`

### 查看任务执行结果

```python
from app.db.database import SessionLocal
from app.models.scheduler import TaskExecution

db = SessionLocal()
try:
    # 查询最近的执行记录
    executions = db.query(TaskExecution)\
        .order_by(TaskExecution.start_time.desc())\
        .limit(10)\
        .all()

    for execution in executions:
        print(f"任务ID: {execution.task_id}")
        print(f"状态: {execution.status}")
        print(f"耗时: {execution.duration}s")
        print(f"结果: {execution.result}")
        print("---")
finally:
    db.close()
```

## 常见问题

### Q1: 为什么任务没有执行？

**检查清单**:

1. **检查调度器状态**
   ```bash
   python -m cli.main scheduler status
   # 应显示 "running: true"
   ```

2. **检查任务是否启用**
   ```python
   from app.db.database import SessionLocal
   from app.models.scheduler import ScheduledTask

   db = SessionLocal()
   task = db.query(ScheduledTask).filter_by(name="发布池自动扫描").first()
   print(f"任务启用: {task.is_active}")
   print(f"下次运行: {task.next_run_time}")
   db.close()
   ```

3. **检查发布池是否有待发布内容**
   ```python
   from app.db.database import SessionLocal
   from app.models.publisher import PublishPool

   db = SessionLocal()
   pending_count = db.query(PublishPool).filter_by(status="pending").count()
   print(f"待发布数量: {pending_count}")
   db.close()
   ```

4. **检查 cron 表达式是否正确**
   ```bash
   # 验证 cron 表达式
   python -c "
   from croniter import croniter
   from datetime import datetime
   base = datetime.now()
   iter = croniter('*/5 * * * *', base)
   print(f'下次运行: {iter.get_next(datetime)}')
   "
   ```

### Q2: 如何控制发布频率？

**方法 1**: 调整 cron 表达式
```json
{
    "cron_expression": "*/15 * * * *"  // 改为每15分钟
}
```

**方法 2**: 设置任务的计划时间
```python
# 设置在特定时间发布
pool_entry = PublishPool(
    content_id=123,
    priority=5,
    scheduled_at=datetime(2026, 2, 10, 9, 0, 0),  # 早上9点
    status='pending'
)
```

### Q3: 如何处理发布失败的任务？

**自动重试机制**:

- 默认最大重试次数: 3次
- 每次失败后会自动增加 `retry_count`
- 超过最大重试次数后会被跳过

**手动重新发布**:
```bash
# 查看失败的任务
python -m cli.main publish-pool list --status pending

# 重试发布
python -m cli.main publish-pool retry <pool_id>
```

**查看失败原因**:
```python
from app.db.database import SessionLocal
from app.models.publisher import PublishPool

db = SessionLocal()
failed_tasks = db.query(PublishPool)\
    .filter_by(status="pending")\
    .filter(PublishPool.retry_count > 0)\
    .all()

for task in failed_tasks:
    print(f"Pool ID: {task.id}")
    print(f"重试次数: {task.retry_count}/{task.max_retries}")
    print(f"错误: {task.last_error}")
    print("---")
db.close()
```

### Q4: 如何避免高峰期发布？

**方法 1**: 使用 cron 表达式避开高峰期
```json
{
    "cron_expression": "0 1-6,20-23 * * *"  // 凌晨和晚上发布
}
```

**方法 2**: 设置任务的计划时间
```python
import pytz
from datetime import datetime, timedelta

# 设置在凌晨2点发布
tz = pytz.timezone('Asia/Shanghai')
scheduled_time = datetime.now(tz).replace(
    hour=2,
    minute=0,
    second=0,
    microsecond=0
) + timedelta(days=1)  # 明天凌晨2点

pool_entry = PublishPool(
    content_id=123,
    scheduled_at=scheduled_time,
    status='pending'
)
```

**方法 3**: 使用 `check_future_tasks: false`
```json
{
    "check_future_tasks": false  // 只扫描已到期的任务
}
```

## 最佳实践

### 1. 合理设置批量大小

```python
# 根据账号数量和发布频率调整
params = {
    "max_batch_size": len(accounts) * 2  # 账号数量的2倍
}
```

### 2. 分优先级管理内容

```python
# 优质内容设置高优先级
if content.quality_score > 8.0:
    priority = 10
elif content.quality_score > 6.0:
    priority = 7
else:
    priority = 5
```

### 3. 错峰发布

```python
# 避开工作时间（9:00-18:00）
current_hour = datetime.now().hour
if 9 <= current_hour < 18:
    # 设置在晚上发布
    scheduled_at = datetime.now().replace(hour=20)
```

### 4. 监控执行结果

```python
# 定期检查失败率
from datetime import datetime, timedelta
from app.models.scheduler import TaskExecution

db = SessionLocal()
recent_executions = db.query(TaskExecution)\
    .filter(TaskExecution.start_time > datetime.now() - timedelta(days=1))\
    .all()

failed_count = sum(1 for e in recent_executions if e.status == "failed")
total_count = len(recent_executions)
failure_rate = failed_count / total_count if total_count > 0 else 0

if failure_rate > 0.1:  # 失败率超过10%
    print("⚠️ 警告: 发布失败率过高!")
db.close()
```

### 5. 定期清理已发布的任务

```python
# 定期清理已成功发布的任务（保留30天）
from datetime import datetime, timedelta
from app.models.publisher import PublishPool

db = SessionLocal()
cutoff_date = datetime.now() - timedelta(days=30)

deleted = db.query(PublishPool)\
    .filter_by(status="published")\
    .filter(PublishPool.published_at < cutoff_date)\
    .delete()

db.commit()
print(f"✅ 清理了 {deleted} 条已发布的任务")
db.close()
```

## 完整示例

### 示例 1: 基础配置

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from datetime import datetime

db = SessionLocal()
try:
    # 每10分钟扫描一次，最多发布10条
    task = ScheduledTask(
        name='基础自动发布',
        description='每10分钟自动发布最多10条内容',
        task_type='publish_pool_scanner',
        params={
            'max_batch_size': 10,
            'check_future_tasks': False
        },
        cron_expression='*/10 * * * *',
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(task)
    db.commit()
    print(f'✅ 任务创建成功: {task.id}')
finally:
    db.close()
```

### 示例 2: 避开高峰期发布

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from datetime import datetime

db = SessionLocal()
try:
    # 只在凌晨1-6点和晚上20-23点发布
    task = ScheduledTask(
        name='非高峰期自动发布',
        description='避开工作时间，在非高峰期自动发布',
        task_type='publish_pool_scanner',
        params={
            'max_batch_size': 20,  # 非高峰期可以增加批量
            'check_future_tasks': False
        },
        cron_expression='0 1-6,20-23 * * *',
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(task)
    db.commit()
    print(f'✅ 任务创建成功: {task.id}')
finally:
    db.close()
```

### 示例 3: 高频扫描 + 批量发布

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from datetime import datetime

db = SessionLocal()
try:
    # 每5分钟扫描，预加载未来任务
    task = ScheduledTask(
        name='高频扫描+预加载',
        description='每5分钟扫描，包括未来计划的任务',
        task_type='publish_pool_scanner',
        params={
            'max_batch_size': 15,
            'check_future_tasks': True  # 预加载所有任务
        },
        cron_expression='*/5 * * * *',
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(task)
    db.commit()
    print(f'✅ 任务创建成功: {task.id}')
finally:
    db.close()
```

## 相关文档

- [调度器系统设计文档](../design/scheduler-system-design.md)
- [发布池管理指南](./publish-pool-management.md)
- [CLI 命令参考](../references/CLI-REFERENCE.md)
- [单元测试文档](/Users/cino.chen/.openclaw/workspace/content-hub/src/backend/tests/test_publish_pool_scanner_executor.py)

## 更新日志

- **2026-02-10**: 初始版本，添加 PublishPoolScannerExecutor 使用指南
- **待更新**: 添加更多实际使用案例和性能优化建议
