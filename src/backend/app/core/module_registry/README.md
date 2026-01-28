# Module Registry Framework - 快速参考

通用的模块注册框架，用于统一管理 SQL/MongoDB 模型和 Celery 任务。

---

## 🚀 快速开始

### 1. 注册 Models

```python
# app/modules/your_module/models/__init__.py
from app.core.module_registry import create_model_registry

model_registry = create_model_registry(
    module_name="your_module",
    sql_models=[
        {
            'name': 'YourModel',
            'class': YourModel,
            'version': '1.0.0',
            'validation_func': validate_your_model  # 可选
        }
    ],
    integrity_check_func=check_integrity  # 可选
)

def register_models() -> bool:
    try:
        logger.info("Starting model registration...")
        # 你的注册逻辑...
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False
```

### 2. 注册 Tasks

```python
# app/modules/your_module/tasks/__init__.py
from app.core.module_registry import (
    create_task_registry,
    TaskPriority,
    with_task_info,
    with_monitoring,
)

task_registry = create_task_registry(
    module_name="your_module",
    queue_configs={
        "your_queue": {
            'routing_key': 'your_queue',
            'priority': 7,
            'max_length': 500,
            'message_ttl': 3600
        }
    }
)

def register_tasks() -> bool:
    try:
        logger.info("Starting task registration...")
        # 导入任务文件...
        return True
    except Exception as e:
        logger.error(f"Failed: {e}")
        return False
```

### 3. 在主应用中注册

```python
# app/main.py
@app.on_event("startup")
async def startup():
    from app.modules.your_module.models import register_models
    from app.modules.your_module.tasks import register_tasks
    
    register_models()
    register_tasks()
```

---

## 📚 API 文档

### create_model_registry()

创建模型注册器

**参数**:
```python
create_model_registry(
    module_name: str,                        # 模块名称
    sql_models: List[Dict] = None,           # SQL模型列表
    mongodb_models: List[Dict] = None,       # MongoDB模型列表
    integrity_check_func: Callable = None    # 完整性检查函数
) -> ModelRegistry
```

**SQL/MongoDB Model Dict**:
```python
{
    'name': str,                    # 模型名称
    'class': Type,                  # 模型类
    'version': str,                 # 版本号（如 "1.0.0"）
    'validation_func': Callable,    # 可选：数据验证函数
    'integrity_check': Callable     # 可选：完整性检查函数
}
```

**示例**:
```python
model_registry = create_model_registry(
    module_name="product_selection",
    sql_models=[
        {
            'name': 'Attribute',
            'class': Attribute,
            'version': '1.0.0',
            'validation_func': validate_attribute
        }
    ]
)
```

---

### create_task_registry()

创建任务注册器

**参数**:
```python
create_task_registry(
    module_name: str,                           # 模块名称
    queue_configs: Dict[str, Dict] = None,      # 队列配置
    retry_policies: Dict[str, Dict] = None      # 重试策略
) -> TaskRegistry
```

**Queue Config Dict**:
```python
{
    "queue_name": {
        'routing_key': str,     # 路由键
        'priority': int,        # 优先级 (1-10)
        'max_length': int,      # 最大队列长度
        'message_ttl': int      # 消息TTL（秒）
    }
}
```

**Retry Policy Dict**:
```python
{
    "task_name": {
        'max_retries': int,      # 最大重试次数
        'countdown': int,        # 重试延迟（秒）
        'backoff': bool,         # 是否指数退避
        'backoff_max': int,      # 最大退避时间（秒）
        'jitter': bool           # 是否添加随机抖动
    }
}
```

**示例**:
```python
task_registry = create_task_registry(
    module_name="product_selection",
    queue_configs={
        "scoring_queue": {
            'routing_key': 'product_selection_scoring',
            'priority': 8,
            'max_length': 500,
            'message_ttl': 1800
        }
    },
    retry_policies={
        'calculate_score': {
            'max_retries': 3,
            'countdown': 60,
            'backoff': True
        }
    }
)
```

---

### 装饰器

#### @with_task_info

为任务添加元数据

```python
from app.modules.your_module.tasks import task_registry
from app.core.module_registry import with_task_info, TaskPriority

@celery_app.task
@with_task_info(
    task_registry,
    queue="your_queue",
    priority=TaskPriority.HIGH,
    description="计算评分"
)
def calculate_score(data):
    pass
```

#### @with_monitoring

添加任务监控

```python
from app.modules.your_module.tasks import task_registry
from app.core.module_registry import with_monitoring

@celery_app.task
@with_monitoring(task_registry)
def process_data(data):
    pass
```

#### @with_dependencies

声明任务依赖

```python
from app.modules.your_module.tasks import task_registry
from app.core.module_registry import with_dependencies

@celery_app.task
@with_dependencies(task_registry, "task_a", "task_b")
def task_c(data):
    # task_c 依赖 task_a 和 task_b
    pass
```

---

## 🔍 常用方法

### ModelRegistry

```python
# 获取注册状态
status = model_registry.get_registry_status()

# 验证模型数据
is_valid = model_registry.validate_model_data("ModelName", data)

# 检查模型完整性
integrity = model_registry.check_model_integrity("sql_models")

# 运行迁移
success = model_registry.run_migration("ModelName", "2.0.0")

# 验证所有模型
results = model_registry.validate_all_models()
```

### TaskRegistry

```python
# 获取注册状态
status = task_registry.get_registry_status()

# 获取任务指标
metrics = task_registry.get_task_metrics("task_name")

# 获取所有任务指标
all_metrics = task_registry.get_task_metrics()

# 验证任务依赖
is_valid = task_registry.validate_dependencies("task_name")

# 获取任务链
chain = task_registry.get_task_chain("task_name")
```

---

## 📊 枚举类

### TaskPriority

```python
from app.core.module_registry import TaskPriority

TaskPriority.LOW       # 1
TaskPriority.NORMAL    # 5
TaskPriority.HIGH      # 8
TaskPriority.URGENT    # 9
```

### ModelType

```python
from app.core.module_registry import ModelType

ModelType.SQL       # "sql"
ModelType.MONGODB   # "mongodb"
```

---

## ✨ 完整示例

查看以下实际应用：

- [Market Evaluation Models](../../modules/market_evaluation/models/__init__.py)
- [Market Evaluation Tasks](../../modules/market_evaluation/tasks/__init__.py)
- [Product Selection Models](../../modules/product_selection/models/__init__.py)
- [Product Selection Tasks](../../modules/product_selection/tasks/__init__.py)

---

## 🎯 最佳实践

1. **模块命名** - 使用小写加下划线（如 `product_selection`）
2. **版本号** - 使用语义化版本（如 `1.0.0`）
3. **验证函数** - 总是提供验证函数提高数据质量
4. **完整性检查** - 在生产环境启动时运行完整性检查
5. **监控** - 使用 `@with_monitoring` 装饰器跟踪任务执行
6. **日志** - 注册过程中添加详细日志

---

## 📖 相关文档

- [重构总结](../../../docs/06_product_selection/REFACTORING_SUMMARY.md)
- [重构示例](../../../docs/06_product_selection/REFACTORED_REGISTRATION_EXAMPLE.md)
- [模块注册文档](../../../docs/06_product_selection/MODULE_REGISTRATION.md)

---

**作者**: AI Assistant  
**版本**: 1.0.0  
**更新时间**: 2025-01


