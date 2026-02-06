# ContentGenerationExecutor 使用指南

## 快速开始

### 1. 基本概念

`ContentGenerationExecutor` 是一个任务执行器，负责自动调用 content-creator CLI 生成内容并保存到数据库。

**关键特性**：
- 继承自 `TaskExecutor` 抽象基类
- 支持账号配置（写作风格、内容主题）
- 完整的错误处理和日志记录
- 自动提取标题、计算字数、处理图片

### 2. 执行器类型

```python
executor_type = "content_generation"
```

## 使用场景

### 场景 1: 通过定时任务自动生成内容

#### 创建每日定时任务

```python
from app.modules.scheduler.services import create_task
from datetime import time

task_data = {
    "name": "每日科技文章生成",
    "task_type": "content_generation",
    "task_params": {
        "account_id": 1,
        "topic": "人工智能最新进展",
        "requirements": "写一篇关于 AI 技术发展趋势的文章，1000字左右",
        "target_audience": "技术爱好者",
        "tone": "专业"
    },
    "schedule_type": "cron",
    "cron_expression": "0 9 * * *",  # 每天早上9点
    "enabled": True
}

task = create_task(task_data, db)
```

#### 通过 API 创建

```bash
curl -X POST http://localhost:8000/api/v1/scheduler/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日内容生成",
    "task_type": "content_generation",
    "task_params": {
      "account_id": 1,
      "topic": "Python 编程技巧"
    },
    "schedule_type": "cron",
    "cron_expression": "0 9 * * *"
  }'
```

### 场景 2: 手动触发一次性生成

#### 直接使用执行器

```python
from app.services.executors import ContentGenerationExecutor
from app.db.database import get_db

# 获取数据库会话
db_gen = get_db()
db = next(db_gen)

# 创建执行器
executor = ContentGenerationExecutor()

# 执行任务
result = await executor.execute(
    task_id=123,
    task_params={
        "account_id": 1,
        "topic": "ContentHub 系统介绍",
        "requirements": "写一篇介绍 ContentHub 功能的文章",
        "target_audience": "开发者",
        "tone": "友好专业"
    },
    db=db
)

if result.success:
    print(f"生成成功！内容ID: {result.data['content_id']}")
    print(f"标题: {result.data['title']}")
    print(f"字数: {result.data['word_count']}")
else:
    print(f"生成失败: {result.message}")
```

#### 通过调度服务

```python
from app.services.scheduler_service import scheduler_service

result = await scheduler_service.execute_task(
    task_id=123,
    task_type="content_generation",
    task_params={
        "account_id": 1,
        "topic": "测试选题"
    },
    db=db
)
```

### 场景 3: 批量生成内容

```python
import asyncio
from app.services.executors import ContentGenerationExecutor

executor = ContentGenerationExecutor()

topics = [
    "Python 异步编程",
    "FastAPI 最佳实践",
    "SQLAlchemy 2.0 新特性",
    "Docker 容器化部署"
]

tasks = []
for topic in topics:
    task = executor.execute(
        task_id=len(tasks),
        task_params={
            "account_id": 1,
            "topic": topic
        },
        db=db
    )
    tasks.append(task)

# 并发执行
results = await asyncio.gather(*tasks)

for i, result in enumerate(results):
    if result.success:
        print(f"✅ {topics[i]}: {result.data['content_id']}")
    else:
        print(f"❌ {topics[i]}: {result.message}")
```

## 任务参数详解

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `account_id` | int | 账号ID | `1` |

### 可选参数

| 参数 | 类型 | 说明 | 默认值 | 示例 |
|------|------|------|--------|------|
| `topic` | str | 文章选题 | - | `"人工智能"` |
| `title` | str | 文章标题 | 自动提取 | `"AI技术发展"` |
| `requirements` | str | 创作要求 | `"写一篇关于{topic}的文章"` | `"1000字，结构清晰"` |
| `target_audience` | str | 目标受众 | `"普通读者"` | `"技术专家"` |
| `tone` | str | 语气风格 | `"友好专业"` | `"轻松幽默"` |

## 账号配置集成

执行器会自动读取账号的写作风格和内容主题配置。

### 写作风格配置

如果账号关联了写作风格，以下参数会被自动应用：

- `tone`: 语气风格（如果未明确指定）
- `persona`: 人设
- `min_words` / `max_words`: 字数限制
- `emoji_usage`: 表情使用规则
- `forbidden_words`: 禁用词列表

### 内容主题配置

如果账号关联了内容主题，主题信息会被整合到创作要求中：

- 主题名称和描述
- 内容类型
- 额外的主题相关要求

**示例**：

```python
# 假设账号 ID=1 关联了以下配置：
# - 写作风格: 技术博客风格（专业、2000-3000字、禁用流行词）
# - 内容主题: Python 编程

# 即使只指定基本参数，账号配置也会自动应用：
task_params = {
    "account_id": 1,
    "topic": "Python 类型提示"
}
# 实际调用时会自动整合账号配置
```

## 执行结果

### 成功结果

```python
{
    "success": True,
    "message": "Successfully generated and saved content: 标题",
    "data": {
        "content_id": 123,           # 生成的内容ID
        "title": "文章标题",          # 内容标题
        "word_count": 2500,          # 字数
        "images_count": 3,           # 图片数量
        "creator_task_id": "task-123",  # content-creator 任务ID
        "quality_score": 8.5,        # 质量评分（如果有）
        "quality_passed": True       # 是否通过质检（如果有）
    },
    "duration": 45.2,                # 执行时长（秒）
    "metadata": {
        "account_id": 1,
        "topic": "选题",
        "creator_duration": 42       # content-creator 执行时长
    }
}
```

### 失败结果

```python
{
    "success": False,
    "message": "Failed to call content-creator CLI: ...",
    "error": "错误详情",
    "duration": 10.5,
    "metadata": {}
}
```

## 常见错误处理

### 错误 1: 缺少 account_id

```python
# 错误的参数
task_params = {
    "topic": "测试"
}
# 结果: validation failed
```

**解决**：确保提供有效的 `account_id`

### 错误 2: content-creator CLI 未配置

```python
{
    "success": False,
    "message": "Failed to call content-creator CLI",
    "error": "CREATOR_CLI_PATH 未配置"
}
```

**解决**：检查 `.env` 文件中的 `CREATOR_CLI_PATH` 配置

### 错误 3: 生成的内容为空

```python
{
    "success": False,
    "message": "No content generated by content-creator CLI",
    "error": "EmptyContent"
}
```

**解决**：检查 content-creator CLI 是否正常工作，查看日志

### 错误 4: 数据库保存失败

```python
{
    "success": False,
    "message": "Failed to save content to database",
    "error": "..."
}
```

**解决**：检查数据库连接、账号是否存在

## 监控和日志

### 查看执行日志

```bash
# 查看调度服务日志
tail -f logs/scheduler.log

# 查看内容生成日志
grep "ContentGenerationExecutor" logs/app.log
```

### 关键日志信息

执行器会在以下时机记录日志：

1. **参数验证**：记录验证结果
2. **CLI 调用**：记录调用开始和完成
3. **内容保存**：记录保存成功
4. **错误发生**：记录详细错误信息

示例日志：

```
2026-02-06 23:00:00 | INFO | Task params validation passed: account_id=1, topic=AI技术
2026-02-06 23:00:01 | INFO | Calling content-creator CLI for topic: AI技术
2026-02-06 23:00:45 | INFO | Content-creator CLI completed successfully
2026-02-06 23:00:45 | INFO | Content saved to database: id=123, title=AI技术发展
2026-02-06 23:00:45 | INFO | Task 123 executed successfully in 45.2s
```

## 测试和调试

### 单元测试

```bash
cd src/backend
pytest tests/test_content_generation_executor.py -v
```

### 集成测试

```bash
cd src/backend
python test_content_generation_executor.py
```

### 手动测试

```python
from app.services.executors import ContentGenerationExecutor
from app.db.database import get_db

db = next(get_db())
executor = ContentGenerationExecutor()

# 测试参数验证
print(executor.validate_params({"account_id": 1, "topic": "测试"}))  # True
print(executor.validate_params({"topic": "测试"}))  # False
```

## 最佳实践

### 1. 参数验证

在创建任务前验证参数：

```python
executor = ContentGenerationExecutor()

if not executor.validate_params(task_params):
    print("参数无效")
    return
```

### 2. 错误处理

始终检查执行结果：

```python
result = await executor.execute(task_id, task_params, db)

if result.success:
    # 处理成功情况
    content_id = result.data["content_id"]
else:
    # 处理失败情况
    log.error(f"任务失败: {result.message}")
    if result.error:
        log.error(f"错误详情: {result.error}")
```

### 3. 使用账号配置

充分利用账号配置功能，避免重复指定参数：

```python
# 推荐：利用账号配置
task_params = {
    "account_id": 1,  # 该账号已配置写作风格
    "topic": "新选题"
}

# 不推荐：每次都指定所有参数
task_params = {
    "account_id": 1,
    "topic": "新选题",
    "tone": "专业",
    "requirements": "..."  # 这些应该配置在账号级别
}
```

### 4. 批量操作

使用异步并发提高效率：

```python
import asyncio

tasks = [executor.execute(i, params, db) for i, params in task_params_list]
results = await asyncio.gather(*tasks)
```

## 相关文档

- [任务调度服务设计](./SCHEDULER_DESIGN.md)
- [快速参考](./QUICK_REFERENCE.md)
- [实现总结](./IMPLEMENTATION_SUMMARY.md)
- [阶段2实现报告](./IMPLEMENTATION_PHASE2.md)

## 支持

如有问题，请查看：

1. 应用日志：`logs/app.log`
2. 调度日志：`logs/scheduler.log`
3. 单元测试：`tests/test_content_generation_executor.py`
4. 集成测试：`test_content_generation_executor.py`
