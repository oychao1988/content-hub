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

## 已注册的执行器

ContentHub 系统当前已注册的执行器：

| 执行器类型 | 类名 | 功能描述 |
|-----------|------|----------|
| `content_generation` | ContentGenerationExecutor | 自动生成内容 |
| `publishing` | PublishingExecutor | 批量发布内容到发布池 |
| `workflow` | WorkflowExecutor | 编排多个执行步骤 |
| `add_to_pool` | AddToPoolExecutor | 将内容加入发布池 |
| `approve` | ApproveExecutor | 审核内容 |
| `async_content_generation` | AsyncContentGenerationExecutor | 异步内容生成（支持Webhook回调） |
| `publish_pool_scanner` | PublishPoolScannerExecutor | 扫描发布池并批量自动发布 |

**查看已注册的执行器**：

```python
from app.services.scheduler_service import scheduler_service

executors = scheduler_service.get_registered_executors()
for executor_type, executor_info in executors.items():
    print(f"{executor_type}: {executor_info}")
```

## 工作流执行器架构

### 设计概述

工作流执行器（WorkflowExecutor）是一个特殊的执行器，用于编排多个执行步骤。它提供了强大的流程编排能力。

### 核心特性

1. **顺序执行**: 步骤按定义顺序依次执行
2. **上下文传递**: 步骤间通过上下文共享数据
3. **变量引用**: 支持 `${variable_name}` 格式引用上下文变量
4. **错误中断**: 任何步骤失败则中断整个工作流
5. **结果汇总**: 返回所有步骤的执行结果

### 执行流程

```
┌─────────────────────────────────────────────────────────┐
│ WorkflowExecutor.execute()                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 验证参数（steps）                                    │
│     ├── 检查 steps 是否存在                             │
│     └── 验证每个步骤格式                                │
│                                                          │
│  2. 初始化上下文（context = {}）                        │
│                                                          │
│  3. 遍历执行步骤                                        │
│     └── 对每个 step:                                    │
│         a. 解析变量引用（${variable}）                  │
│         b. 调用对应执行器                               │
│         c. 检查执行结果                                 │
│         d. 合并 data 到上下文                           │
│         e. 失败则中断                                   │
│                                                          │
│  4. 返回汇总结果                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 变量解析机制

变量解析使用正则表达式匹配和替换：

```python
def _resolve_variables(self, params: Dict, context: Dict) -> Dict:
    """
    解析参数中的变量引用

    支持格式:
    - 简单引用: ${content_id}
    - 嵌套引用: ${user.name}
    - 组合引用: "内容 ${title} 已生成，ID: ${content_id}"
    """
    import re

    pattern = re.compile(r'\$\{([^}]+)\}')

    def resolve_value(value):
        if isinstance(value, str):
            # 替换字符串中的变量
            def replace_var(match):
                var_name = match.group(1)
                return str(context.get(var_name, match.group(0)))
            return pattern.sub(replace_var, value)
        elif isinstance(value, dict):
            # 递归处理字典
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            # 递归处理列表
            return [resolve_value(item) for item in value]
        return value

    return resolve_value(params)
```

### 上下文传递示例

```python
# 初始上下文
context = {}

# 步骤 1: content_generation
step1_result = {
    "success": True,
    "data": {
        "content_id": 123,
        "title": "测试文章",
        "word_count": 1500
    }
}
context.update(step1_result["data"])
# context = {"content_id": 123, "title": "测试文章", "word_count": 1500}

# 步骤 2: approve (使用变量引用)
step2_params = {"content_id": "${content_id}"}
resolved_params = {"content_id": 123}  # 解析后

step2_result = {
    "success": True,
    "data": {
        "content_id": 123,
        "review_status": "approved"
    }
}
context.update(step2_result["data"])
# context = {"content_id": 123, "title": "测试文章", "word_count": 1500, "review_status": "approved"}

# 步骤 3: add_to_pool (可以使用任何上下文变量)
step3_params = {
    "content_id": "${content_id}",
    "priority": 5,
    "note": "标题: ${title}, 字数: ${word_count}"
}
resolved_params = {
    "content_id": 123,
    "priority": 5,
    "note": "标题: 测试文章, 字数: 1500"
}
```

### 工作流参数结构

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "新能源汽车行业最新动态"
      }
    },
    {
      "type": "approve",
      "params": {
        "content_id": "${content_id}"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 5,
        "note": "审核通过，ID: ${content_id}"
      }
    }
  ]
}
```

### 新增执行器架构

#### AddToPoolExecutor

**功能**: 将内容加入发布池

**参数验证**:
- `content_id`: 必需，整数
- `priority`: 可选，整数（1-10），默认5
- `scheduled_at`: 可选，日期时间字符串
- `auto_approve`: 可选，布尔值，默认false

**返回数据**:
```json
{
  "pool_id": 456,
  "content_id": 123,
  "priority": 5,
  "scheduled_at": null,
  "auto_approved": true
}
```

#### ApproveExecutor

**功能**: 审核内容

**参数验证**:
- `content_id`: 必需，整数
- `review_status`: 可选，字符串，默认"approved"
- `review_note`: 可选，字符串

**返回数据**:
```json
{
  "content_id": 123,
  "content_title": "文章标题",
  "original_status": "pending",
  "new_status": "approved"
}
```

### 扩展性设计

#### 添加新执行器

创建自定义执行器：

```python
from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from typing import Dict, Any
from sqlalchemy.orm import Session

class CustomExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "custom_type"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        # 自定义参数验证逻辑
        required_fields = ["field1", "field2"]
        return all(field in task_params for field in required_fields)

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        try:
            # 执行业务逻辑
            result_data = {}
            return TaskExecutionResult.success_result(
                message="执行成功",
                data=result_data
            )
        except Exception as e:
            return TaskExecutionResult.failure_result(
                message="执行失败",
                error=str(e)
            )
```

注册执行器：

```python
from app.modules.scheduler.module import startup

def startup(app):
    from app.services.executors.custom_executor import CustomExecutor

    custom_executor = CustomExecutor()
    scheduler_service.register_executor(custom_executor)
```

在工作流中使用：

```json
{
  "steps": [
    {
      "type": "custom_type",
      "params": {
        "field1": "value1",
        "field2": "${context_var}"
      }
    }
  ]
}
```

#### PublishPoolScannerExecutor

**功能**: 扫描发布池并批量自动发布待发布内容

**核心特性**:
- **智能扫描**: 定期扫描发布池中待发布的内容
- **优先级排序**: 按优先级、计划时间和添加时间排序
- **时间过滤**: 支持检查未来计划发布的任务
- **批量处理**: 可配置单次批量发布数量
- **重试控制**: 自动跳过超过最大重试次数的任务
- **错误处理**: 单个任务失败不影响其他任务

**参数配置**:
```python
{
    "max_batch_size": 10,          # 单次最大发布数量（默认10）
    "check_future_tasks": False    # 是否检查未来任务（默认false）
}
```

**执行流程**:
```
┌─────────────────────────────────────────────────────────┐
│ PublishPoolScannerExecutor.execute()                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 获取待发布任务                                       │
│     ├── 查询状态为 pending 的任务                        │
│     ├── 按优先级降序、计划时间升序排序                   │
│     └── 限制数量为 max_batch_size                        │
│                                                          │
│  2. 遍历执行发布                                         │
│     └── 对每个任务:                                     │
│         a. 检查重试次数                                 │
│         b. 调用 PublishingExecutor                      │
│         c. 记录执行结果                                 │
│         d. 更新失败任务的重试次数                       │
│                                                          │
│  3. 返回汇总结果                                         │
│     ├── pending_count: 待发布总数                       │
│     ├── published_count: 成功发布数                     │
│     ├── failed_count: 失败数量                          │
│     └── results: 详细结果列表                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**查询逻辑**:
```python
# 基础查询
query = db.query(PublishPool).filter(PublishPool.status == "pending")

# 时间过滤（可选）
if not check_future_tasks:
    query = query.filter(
        (PublishPool.scheduled_at == None) |
        (PublishPool.scheduled_at <= datetime.now())
    )

# 排序规则
query = query.order_by(
    PublishPool.priority.desc(),      # 优先级高的优先
    PublishPool.scheduled_at.asc(),   # 计划时间早的优先
    PublishPool.added_at.asc()        # 添加时间早的优先
)

# 数量限制
query = query.limit(max_batch_size)
```

**返回数据示例**:
```json
{
    "success": true,
    "message": "发布池扫描完成: 扫描 3 个任务, 成功 2 个, 失败 1 个",
    "data": {
        "scanned": true,
        "pending_count": 3,
        "published_count": 2,
        "failed_count": 1,
        "results": [
            {
                "pool_id": 1,
                "content_id": 101,
                "success": true,
                "message": "发布成功"
            },
            {
                "pool_id": 2,
                "content_id": 102,
                "success": true,
                "message": "发布成功"
            },
            {
                "pool_id": 3,
                "content_id": 103,
                "success": false,
                "error": "API调用失败"
            }
        ]
    }
}
```

**定时任务配置示例**:
```python
# 通过数据库或API创建定时任务
task = ScheduledTask(
    name="发布池自动扫描",
    description="定期扫描发布池并批量发布待发布内容",
    task_type="publish_pool_scanner",
    params={
        "max_batch_size": 10,
        "check_future_tasks": True
    },
    cron_expression="*/5 * * * *",  # 每5分钟执行一次
    is_active=True
)
```

**使用场景**:
- **定时批量发布**: 每隔几分钟自动扫描发布池并批量发布
- **高峰期避开**: 设置 `scheduled_at` 在非高峰期自动发布
- **优先级控制**: 高优先级内容优先发布
- **容错机制**: 单个任务失败不影响其他任务

**单元测试**:
```bash
# 运行 PublishPoolScannerExecutor 测试
pytest tests/test_publish_pool_scanner_executor.py -v
```

测试覆盖：
- ✅ 执行器类型验证
- ✅ 参数验证（默认和自定义）
- ✅ 查询逻辑（空结果、有结果、优先级排序、时间过滤、批量限制）
- ✅ 执行逻辑（无任务、全部成功、部分成功、全部失败）
- ✅ 重试机制（超过最大重试次数）
- ✅ 异常处理
- ✅ 自定义批量大小
- ✅ 未来任务检查

## 文件位置

- 核心实现: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/scheduler_service.py`
- 使用示例: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/scheduler_service_examples.py`
- 工作流执行器: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/workflow_executor.py`
- 加入发布池执行器: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/add_to_pool_executor.py`
- 审核执行器: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/approve_executor.py`
- 发布池扫描执行器: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/publish_pool_scanner_executor.py`
- 单元测试: `/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/test_publish_pool_scanner_executor.py`
- 本文档: `/Users/Oychao/Documents/Projects/content-hub/src/backend/docs/design/scheduler-system-design.md`

## 相关文档

- [工作流执行器使用指南](../guides/workflow-executor-guide.md) - 工作流执行器详细使用文档
- [调度器快速参考](../guides/scheduler-quick-reference.md) - 调度器使用快速入门
- [工作流执行器使用文档](../../../WORKFLOW_EXECUTOR_USAGE.md) - 原始使用文档
- [工作流执行器测试报告](../../../WORKFLOW_EXECUTOR_TEST_REPORT.md) - 测试报告和验证结果
