# 任务执行器接口设计文档

## 概述

本文档描述了 ContentHub 调度系统的任务执行器接口设计。该接口提供了一个可扩展、类型安全的任务执行框架。

## 核心组件

### 1. TaskStatus 枚举

任务执行状态的三种状态：

- `RUNNING`: 任务正在执行
- `SUCCESS`: 任务执行成功
- `FAILED`: 任务执行失败

```python
from app.services.scheduler_service import TaskStatus

status = TaskStatus.SUCCESS
```

### 2. TaskExecutionResult 数据类

任务执行结果的统一数据结构。

#### 属性

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `success` | bool | 是 | 是否执行成功 |
| `message` | str | 是 | 执行结果消息 |
| `data` | Dict[str, Any] \| None | 否 | 业务数据 |
| `error` | str \| None | 否 | 错误信息 |
| `duration` | float \| None | 否 | 执行时长（秒） |
| `metadata` | Dict[str, Any] | 否 | 元数据信息 |

#### 类方法

**创建成功结果：**

```python
result = TaskExecutionResult.success_result(
    message="内容生成成功",
    data={"content_id": 123},
    duration=2.5,
    metadata={"word_count": 1500}
)
```

**创建失败结果：**

```python
result = TaskExecutionResult.failure_result(
    message="内容生成失败",
    error="Connection timeout",
    duration=5.0
)
```

**转换为字典：**

```python
result_dict = result.to_dict()
# 可用于存储到数据库 JSON 字段
```

### 3. TaskExecutor 抽象基类

所有任务执行器必须继承此类并实现抽象方法。

#### 抽象属性

```python
@property
@abstractmethod
def executor_type(self) -> str:
    """返回执行器类型标识（如 'content_generation', 'publishing'）"""
    pass
```

#### 抽象方法

```python
@abstractmethod
async def execute(
    self,
    task_id: int,
    task_params: Dict[str, Any],
    db: Session
) -> TaskExecutionResult:
    """执行任务的核心逻辑"""
    pass
```

#### 可选方法

```python
def validate_params(self, task_params: Dict[str, Any]) -> bool:
    """验证任务参数（默认返回 True）"""
    return True

def get_executor_info(self) -> Dict[str, Any]:
    """获取执行器元信息"""
    return {
        "type": self.executor_type,
        "class": self.__class__.__name__,
        "module": self.__class__.__module__
    }
```

#### 实现示例

```python
from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from typing import Dict, Any
from sqlalchemy.orm import Session

class ContentGenerationExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "content_generation"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        try:
            # 1. 提取参数
            account_id = task_params.get("account_id")
            topic = task_params.get("topic")

            # 2. 执行业务逻辑
            # ... 调用 CLI、保存到数据库等 ...

            # 3. 返回成功结果
            return TaskExecutionResult.success_result(
                message=f"成功生成内容: {topic}",
                data={"content_id": 123}
            )

        except Exception as e:
            # 4. 返回失败结果
            return TaskExecutionResult.failure_result(
                message="内容生成失败",
                error=str(e)
            )
```

### 4. SchedulerService 调度服务

管理任务执行器的注册和任务执行。

#### 主要方法

##### 注册执行器

```python
from app.services.scheduler_service import scheduler_service

executor = ContentGenerationExecutor()
scheduler_service.register_executor(executor)
```

##### 执行任务

```python
result = await scheduler_service.execute_task(
    task_id=1,
    task_type="content_generation",
    task_params={
        "account_id": 1,
        "topic": "人工智能的未来发展"
    },
    db=db_session
)

if result.success:
    print(f"成功: {result.message}")
    print(f"数据: {result.data}")
else:
    print(f"失败: {result.error}")
```

##### 获取执行器

```python
executor = scheduler_service.get_executor("content_generation")
if executor:
    print(f"找到执行器: {executor.executor_type}")
```

##### 获取所有已注册的执行器

```python
executors = scheduler_service.get_registered_executors()
# 返回: {"content_generation": {...}, "publishing": {...}}
```

##### 调度器控制

```python
# 启动调度器
scheduler_service.start()

# 检查运行状态
is_running = scheduler_service.is_running

# 关闭调度器
scheduler_service.shutdown(wait=True)  # 等待任务完成
```

## 使用流程

### 1. 创建自定义执行器

继承 `TaskExecutor` 并实现抽象方法：

```python
class MyCustomExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "my_custom_type"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        # 实现你的业务逻辑
        return TaskExecutionResult.success_result(
            message="执行成功"
        )
```

### 2. 注册执行器

在应用启动时注册（例如在 `app/factory.py` 中）：

```python
from app.services.scheduler_service import scheduler_service

def register_executors():
    content_executor = ContentGenerationExecutor()
    publish_executor = PublishingExecutor()

    scheduler_service.register_executor(content_executor)
    scheduler_service.register_executor(publish_executor)
```

### 3. 执行任务

通过 APScheduler 或手动触发任务执行：

```python
from app.db.database import SessionLocal

db = SessionLocal()
try:
    result = await scheduler_service.execute_task(
        task_id=1,
        task_type="content_generation",
        task_params={"account_id": 1, "topic": "..."},
        db=db
    )
finally:
    db.close()
```

## 日志记录

`SchedulerService.execute_task()` 会自动记录以下日志：

- **INFO**: 任务开始执行、执行成功、执行失败
- **DEBUG**: 任务参数、执行结果详情
- **ERROR**: 任务失败原因、错误详情、异常堆栈

日志格式示例：

```
2024-02-06 10:00:00 | INFO     | 开始执行任务 1 (类型: content_generation)
2024-02-06 10:00:05 | INFO     | 任务 1 执行成功，耗时 5.23秒
2024-02-06 10:00:05 | DEBUG    | 执行结果: 成功生成内容: 人工智能的未来发展
```

## 错误处理

### 执行器未找到

```python
# 如果 task_type 没有对应的执行器
result = await scheduler_service.execute_task(
    task_id=1,
    task_type="unknown_type",  # 未注册的类型
    task_params={},
    db=db
)
# result.success == False
# result.error == "ExecutorNotFound: unknown_type"
```

### 参数验证失败

```python
# 如果 validate_params() 返回 False
result = await scheduler_service.execute_task(
    task_id=1,
    task_type="content_generation",
    task_params={"invalid": "params"},  # 缺少必填参数
    db=db
)
# result.success == False
# result.error == "InvalidParameters"
```

### 执行异常

```python
# 如果 execute() 方法抛出异常
# 会自动捕获并返回失败结果
# result.error 包含异常信息
```

## 扩展性

### 添加新的任务类型

1. 创建新的执行器类继承 `TaskExecutor`
2. 实现 `executor_type` 属性和 `execute()` 方法
3. 在应用启动时注册到 `scheduler_service`

### 参数验证

重写 `validate_params()` 方法实现自定义参数验证：

```python
def validate_params(self, task_params: Dict[str, Any]) -> bool:
    required_fields = ["account_id", "topic"]
    return all(field in task_params for field in required_fields)
```

### 执行器元信息

重写 `get_executor_info()` 方法添加自定义元信息：

```python
def get_executor_info(self) -> Dict[str, Any]:
    info = super().get_executor_info()
    info["version"] = "1.0.0"
    info["supported_params"] = ["account_id", "topic", "content_type"]
    return info
```

## 类型安全

所有接口都使用 Python 类型注解，支持静态类型检查：

```bash
# 运行类型检查
python -m mypy app/services/scheduler_service.py
```

## 测试

参考 `scheduler_service_examples.py` 查看完整的使用示例。

## 文件位置

- 核心实现: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/scheduler_service.py`
- 使用示例: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/scheduler_service_examples.py`
- 本文档: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/SCHEDULER_DESIGN.md`
