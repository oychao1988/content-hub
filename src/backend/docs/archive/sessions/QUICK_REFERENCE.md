# 任务执行器接口 - 快速参考

## 快速开始

### 1. 创建任务执行器

```python
from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from typing import Dict, Any
from sqlalchemy.orm import Session

class MyExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "my_task_type"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        try:
            # 你的业务逻辑
            result = do_something(task_params)

            # 返回成功结果
            return TaskExecutionResult.success_result(
                message="任务执行成功",
                data={"result": result}
            )
        except Exception as e:
            # 返回失败结果
            return TaskExecutionResult.failure_result(
                message="任务执行失败",
                error=str(e)
            )
```

### 2. 注册执行器

```python
from app.services.scheduler_service import scheduler_service

executor = MyExecutor()
scheduler_service.register_executor(executor)
```

### 3. 执行任务

```python
from app.db.database import SessionLocal

db = SessionLocal()
try:
    result = await scheduler_service.execute_task(
        task_id=1,
        task_type="my_task_type",
        task_params={"key": "value"},
        db=db
    )

    if result.success:
        print(f"成功: {result.message}")
        print(f"数据: {result.data}")
    else:
        print(f"失败: {result.error}")
finally:
    db.close()
```

## 常用模式

### 参数验证

```python
class ValidatedExecutor(TaskExecutor):
    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """验证必填参数"""
        required = ["account_id", "topic"]
        return all(k in task_params for k in required)
```

### 带元数据的返回

```python
return TaskExecutionResult.success_result(
    message="内容生成完成",
    data={"content_id": 123},
    duration=2.5,
    metadata={
        "word_count": 1500,
        "model": "gpt-4",
        "timestamp": "2024-02-06T22:00:00"
    }
)
```

### 错误处理

```python
async def execute(self, task_id, task_params, db):
    try:
        # 业务逻辑
        result = risky_operation()
        return TaskExecutionResult.success_result(
            message="操作成功",
            data=result
        )
    except ValueError as e:
        return TaskExecutionResult.failure_result(
            message="参数错误",
            error=str(e)
        )
    except Exception as e:
        return TaskExecutionResult.failure_result(
            message="未知错误",
            error=str(e)
        )
```

## TaskExecutionResult 快捷方法

### 创建成功结果

```python
result = TaskExecutionResult.success_result(
    message="成功",              # 必填
    data={"key": "value"},      # 可选
    duration=1.5,               # 可选
    metadata={"info": "..."}    # 可选
)
```

### 创建失败结果

```python
result = TaskExecutionResult.failure_result(
    message="失败",              # 必填
    error="错误详情",           # 可选
    duration=2.0,               # 可选
    metadata={"context": "..."} # 可选
)
```

### 转换为字典

```python
result_dict = result.to_dict()
# 用于存储到数据库 JSON 字段
```

## 执行器信息

### 获取执行器信息

```python
executor.get_executor_info()
# 返回: {
#     "type": "my_task_type",
#     "class": "MyExecutor",
#     "module": "app.services.my_executor"
# }
```

### 查看所有已注册的执行器

```python
executors = scheduler_service.get_registered_executors()
# 返回: {
#     "content_generation": {...},
#     "publishing": {...}
# }
```

## 调试技巧

### 查看任务参数

```python
async def execute(self, task_id, task_params, db):
    from app.utils.custom_logger import log
    log.debug(f"任务参数: {task_params}")
    # ...
```

### 查看执行时间

```python
import time
start = time.time()
# ... 执行业务逻辑 ...
duration = time.time() - start

return TaskExecutionResult.success_result(
    message="完成",
    duration=duration  # 会自动记录执行时间
)
```

### 测试执行器

```python
# 创建模拟执行器
class TestExecutor(TaskExecutor):
    @property
    def executor_type(self):
        return "test"

    async def execute(self, task_id, task_params, db):
        return TaskExecutionResult.success_result(
            message="测试成功",
            data=task_params
        )

# 测试
scheduler_service.register_executor(TestExecutor())
result = await scheduler_service.execute_task(
    task_id=1,
    task_type="test",
    task_params={"test": True},
    db=db
)
```

## 常见错误

### 错误 1: 忘记实现 executor_type

```python
# ❌ 错误
class BadExecutor(TaskExecutor):
    async def execute(self, ...):
        pass

# ✅ 正确
class GoodExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "good_executor"

    async def execute(self, ...):
        pass
```

### 错误 2: execute 方法不是异步的

```python
# ❌ 错误
def execute(self, task_id, task_params, db):
    return TaskExecutionResult.success_result("OK")

# ✅ 正确
async def execute(self, task_id, task_params, db):
    return TaskExecutionResult.success_result("OK")
```

### 错误 3: 忘记返回 TaskExecutionResult

```python
# ❌ 错误
async def execute(self, ...):
    # 忘记返回

# ✅ 正确
async def execute(self, ...):
    return TaskExecutionResult.success_result("OK")
```

## 文件位置

- 核心实现: `app/services/scheduler_service.py`
- 使用示例: `app/services/scheduler_service_examples.py`
- 设计文档: `app/services/SCHEDULER_DESIGN.md`
- 实现总结: `app/services/IMPLEMENTATION_SUMMARY.md`
- 快速参考: `app/services/QUICK_REFERENCE.md`

## 相关模块

- 数据模型: `app/models/scheduler.py`
- API Schema: `app/modules/scheduler/schemas.py`
- 配置: `app/core/config.py`
- 日志: `app/utils/custom_logger.py`

## 下一步

1. 实现具体的执行器（ContentGenerationExecutor, PublishingExecutor）
2. 集成到数据库（记录执行历史）
3. 集成到 APScheduler（定时任务）
4. 添加单元测试

## 获取帮助

查看完整文档：
- 设计文档: `SCHEDULER_DESIGN.md`
- 实现总结: `IMPLEMENTATION_SUMMARY.md`
- 代码示例: `scheduler_service_examples.py`
