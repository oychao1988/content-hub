# ContentGenerationTask 模型快速参考

## 模型概述

ContentGenerationTask 是异步内容生成系统的核心模型，用于追踪和管理内容生成任务的整个生命周期。

## 字段说明

### 标识字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PRIMARY KEY | 自增主键 |
| `task_id` | String(100) | UNIQUE, NOT NULL | 任务唯一标识（建议格式：`{prefix}-{uuid}`） |

### 关联字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `content_id` | Integer | FOREIGN KEY, NULLABLE | 关联的内容 ID（任务完成前可能为空） |
| `account_id` | Integer | FOREIGN KEY, NOT NULL | 关联的账号 ID |

### 任务参数

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `topic` | String(500) | NULL | 选题 |
| `keywords` | String(500) | NULL | 关键词（逗号分隔） |
| `category` | String(100) | NULL | 内容分类 |
| `requirements` | Text | NULL | 特殊要求 |
| `tone` | String(50) | NULL | 语气风格 |

### 状态管理

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `status` | String(50) | "pending" | 任务状态（见状态值说明） |
| `priority` | Integer | 5 | 优先级（1-10，数字越大优先级越高） |
| `retry_count` | Integer | 0 | 当前重试次数 |
| `max_retries` | Integer | 3 | 最大重试次数 |

### 时间戳

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `submitted_at` | DateTime | CURRENT_TIMESTAMP | 任务提交时间 |
| `started_at` | DateTime | NULL | 任务开始执行时间 |
| `completed_at` | DateTime | NULL | 任务完成时间 |
| `timeout_at` | DateTime | NULL | 任务超时时间 |

### 结果存储

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | JSON | NULL | 生成结果（JSON 格式） |
| `error_message` | Text | NULL | 错误信息 |

### 自动流程

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `auto_approve` | Boolean | True | 是否自动审核通过 |

### 审计字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `created_at` | DateTime | CURRENT_TIMESTAMP | 记录创建时间 |
| `updated_at` | DateTime | CURRENT_TIMESTAMP | 记录更新时间 |

## 状态值说明

| 状态 | 说明 | 使用场景 |
|------|------|----------|
| `pending` | 等待执行 | 任务已创建，等待调度器处理 |
| `processing` | 执行中 | 任务正在执行 |
| `completed` | 已完成 | 任务成功完成 |
| `failed` | 失败 | 任务执行失败（可重试） |
| `timeout` | 超时 | 任务执行超时 |

## 关系配置

### ContentGenerationTask → Content

```python
task.content  # 获取关联的内容对象（可为 None）
```

### ContentGenerationTask → Account

```python
task.account  # 获取关联的账号对象
```

### Account → ContentGenerationTask

```python
account.generation_tasks  # 获取账号的所有任务（列表）
```

### Content → ContentGenerationTask

```python
content.generation_tasks  # 获取内容的所有任务（列表）
```

## 常用操作

### 创建任务

```python
from app.db.database import SessionLocal
from app.models import ContentGenerationTask
import uuid

db = SessionLocal()

task = ContentGenerationTask(
    task_id=f"task-{uuid.uuid4().hex[:8]}",
    account_id=account_id,
    topic="AI 技术发展趋势",
    keywords="AI,人工智能,技术趋势",
    status="pending",
    priority=8
)

db.add(task)
db.commit()
db.refresh(task)
```

### 更新状态

```python
from datetime import datetime, timezone

# 开始执行
task.status = "processing"
task.started_at = datetime.now(timezone.utc)
db.commit()

# 完成执行
task.status = "completed"
task.completed_at = datetime.now(timezone.utc)
task.result = {
    "success": True,
    "content_id": 123,
    "word_count": 1500
}
db.commit()
```

### 错误处理

```python
task.status = "failed"
task.error_message = "Content generation failed: API timeout"
task.retry_count += 1

if task.retry_count >= task.max_retries:
    # 达到最大重试次数，不再重试
    pass
else:
    # 重新加入队列
    task.status = "pending"

db.commit()
```

### 查询任务

```python
from sqlalchemy import func

# 按状态查询
pending_tasks = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == "pending"
).order_by(
    ContentGenerationTask.priority.desc(),
    ContentGenerationTask.submitted_at.asc()
).all()

# 统计任务
total = db.query(func.count(ContentGenerationTask.id)).scalar()
completed = db.query(func.count(ContentGenerationTask.id)).filter(
    ContentGenerationTask.status == "completed"
).scalar()
```

## 索引说明

表已创建以下索引以优化查询性能：

1. **PRIMARY KEY**: `id`
2. **UNIQUE INDEX**: `task_id` - 快速查找特定任务
3. **INDEX**: `status` - 按状态筛选任务
4. **INDEX**: `account_id` - 查询特定账号的任务
5. **INDEX**: `content_id` - 查询特定内容的任务
6. **INDEX**: `submitted_at` - 按时间排序和查询

## 性能优化建议

### 1. 使用索引字段查询

```python
# ✓ 推荐：使用索引
tasks = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.account_id == account_id,
    ContentGenerationTask.status == "pending"
).all()

# ✗ 不推荐：全表扫描
all_tasks = db.query(ContentGenerationTask).all()
pending = [t for t in all_tasks if t.status == "pending"]
```

### 2. 分页查询

```python
from sqlalchemy.orm import defer

page = 1
per_page = 20

tasks = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == "pending"
).options(
    defer(ContentGenerationTask.result),  # 延迟加载大字段
).order_by(
    ContentGenerationTask.submitted_at
).limit(per_page).offset((page - 1) * per_page).all()
```

### 3. 批量更新

```python
# ✓ 推荐：批量更新
db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == "pending",
    ContentGenerationTask.timeout_at < datetime.now(timezone.utc)
).update({
    "status": "timeout"
}, synchronize_session=False)
db.commit()
```

## 错误处理最佳实践

### 1. 重试机制

```python
def execute_with_retry(task):
    max_attempts = task.max_retries + 1

    for attempt in range(max_attempts):
        try:
            # 执行任务
            result = generate_content(task)
            return result
        except TemporaryError as e:
            if attempt < max_attempts - 1:
                task.retry_count += 1
                task.status = "pending"
                db.commit()
                continue
            else:
                # 最后一次尝试也失败
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
                raise
        except PermanentError as e:
            # 永久性错误，不重试
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
            raise
```

### 2. 超时处理

```python
from datetime import datetime, timedelta, timezone

# 创建任务时设置超时时间
task = ContentGenerationTask(
    task_id=f"task-{uuid.uuid4().hex[:8]}",
    account_id=account_id,
    timeout_at=datetime.now(timezone.utc) + timedelta(minutes=10)
)

# 定期检查超时任务
timeout_tasks = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == "processing",
    ContentGenerationTask.timeout_at < datetime.now(timezone.utc)
).all()

for task in timeout_tasks:
    task.status = "timeout"
    task.error_message = "Task execution timeout"
    db.commit()
```

## 数据清理建议

```python
from datetime import datetime, timedelta, timezone

# 清理 30 天前的已完成任务
cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

old_tasks = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status == "completed",
    ContentGenerationTask.completed_at < cutoff_date
).all()

for task in old_tasks:
    db.delete(task)

db.commit()
```

## 相关文档

- [阶段 1 完成报告](/Users/Oychao/Documents/Projects/content-hub/src/backend/docs/development/ASYNC-CONTENT-GENERATION-PHASE1-COMPLETION.md)
- [数据库架构文档](/Users/Oychao/Documents/Projects/content-hub/docs/architecture/DATABASE-DESIGN.md)
- [测试脚本](/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/test_async_models.py)
