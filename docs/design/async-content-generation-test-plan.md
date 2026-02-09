# 异步内容生成系统 - 测试计划

## 📋 测试概述

本文档详细说明异步内容生成系统的测试策略、测试用例和验收标准。

**测试范围**：
- 数据库模型和迁移
- 核心异步服务
- 队列降级机制（Redis + 内存）
- CLI 命令改造
- 定时任务集成
- 端到端业务流程

**测试环境**：
- 开发环境：本地 Docker Compose
- 测试环境：独立测试服务器
- 数据库：SQLite（开发）/ PostgreSQL（生产）

---

## 🎯 测试策略

### 测试金字塔

```
        /\
       /E2E\          端到端测试 (10%)
      /------\
     /集成测试 \      集成测试 (30%)
    /----------\
   /  单元测试   \    单元测试 (60%)
  /--------------\
```

### 测试类型

| 类型 | 工具 | 覆盖率目标 | 执行频率 |
|------|------|-------------|----------|
| 单元测试 | pytest | > 80% | 每次提交 |
| 集成测试 | pytest | > 70% | 每日构建 |
| E2E 测试 | pytest + CLI | 核心流程 | 每次发布 |
| 性能测试 | locust | - | 每周 |
| 压力测试 | pytest | - | 每月 |

---

## 📊 阶段 1：数据库模型测试

### 测试文件
```
tests/unit/models/test_content_generation_task.py
tests/integration/test_db_migration.py
```

### 测试用例

#### 1.1 ContentGenerationTask 模型测试

**文件**：`tests/unit/models/test_content_generation_task.py`

```python
import pytest
from datetime import datetime, timedelta
from app.models.content_generation_task import ContentGenerationTask
from app.db.database import get_db

def test_create_task(db):
    """测试创建任务"""
    task = ContentGenerationTask(
        task_id="test-uuid-001",
        account_id=49,
        topic="测试选题",
        keywords="关键词1,关键词2",
        category="汽车",
        requirements="测试要求",
        tone="专业",
        status="pending",
        priority=5,
        auto_approve=True
    )
    db.add(task)
    db.commit()

    assert task.id is not None
    assert task.task_id == "test-uuid-001"
    assert task.status == "pending"
    assert task.auto_approve is True

def test_task_status_transitions(db):
    """测试任务状态流转"""
    task = ContentGenerationTask(
        task_id="test-uuid-002",
        account_id=49,
        status="pending"
    )
    db.add(task)
    db.commit()

    # pending → submitted
    task.status = "submitted"
    task.submitted_at = datetime.utcnow()
    db.commit()
    assert task.status == "submitted"

    # submitted → running
    task.status = "running"
    task.started_at = datetime.utcnow()
    db.commit()
    assert task.status == "running"

    # running → completed
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    task.result = {"content": "测试内容"}
    db.commit()
    assert task.status == "completed"
    assert task.result is not None

def test_task_retry_logic(db):
    """测试重试逻辑"""
    task = ContentGenerationTask(
        task_id="test-uuid-003",
        account_id=49,
        status="failed",
        retry_count=0,
        max_retries=3,
        error_message="API超时"
    )
    db.add(task)
    db.commit()

    # 可重试
    assert task.can_retry()
    assert task.retry_count < task.max_retries

    # 重试
    task.retry_count += 1
    task.status = "pending"
    db.commit()

    assert task.retry_count == 1
    assert task.status == "pending"

def test_task_timeout_detection(db):
    """测试超时检测"""
    task = ContentGenerationTask(
        task_id="test-uuid-004",
        account_id=49,
        status="running",
        submitted_at=datetime.utcnow() - timedelta(minutes=31),
        timeout_at=datetime.utcnow() - timedelta(minutes=1)
    )
    db.add(task)
    db.commit()

    # 检查超时
    assert task.is_timeout()
    assert task.status == "running"  # 需要手动标记为 timeout
```

#### 1.2 数据库迁移测试

**文件**：`tests/integration/test_db_migration.py`

```python
import pytest
from alembic import command
from app.db.database import init_db

def test_migration_create_table():
    """测试创建表"""
    # 运行迁移
    command.upgrade("head")

    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "content_generation_tasks" in tables

    # 检查列
    columns = [col['name'] for col in inspector.get_columns('content_generation_tasks')]
    assert "task_id" in columns
    assert "status" in columns
    assert "auto_approve" in columns
    assert "submitted_at" in columns
    assert "completed_at" in columns

def test_migration_indexes():
    """测试索引创建"""
    from sqlalchemy import inspect
    inspector = inspect(engine)

    indexes = inspector.get_indexes('content_generation_tasks')
    index_names = [idx['name'] for idx in indexes]

    # 验证关键索引存在
    assert "ix_content_generation_tasks_task_id" in index_names
    assert "ix_content_generation_tasks_status" in index_names
    assert "ix_content_generation_tasks_account_id" in index_names

def test_rollback_migration():
    """测试回滚"""
    command.downgrade("base")

    # 检查表是否已删除
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "content_generation_tasks" not in tables
```

---

## 🔧 阶段 2：核心服务测试

### 测试文件
```
tests/unit/services/test_task_queue_factory.py
tests/unit/services/test_async_content_generation_service.py
tests/unit/services/test_task_status_poller.py
tests/unit/services/test_task_result_handler.py
```

### 测试用例

#### 2.1 任务队列工厂测试

**文件**：`tests/unit/services/test_task_queue_factory.py`

```python
import pytest
from unittest.mock import Mock, patch
from app.services.task_queue_service import TaskQueueFactory, RedisTaskQueue, MemoryTaskQueue

def test_redis_queue_priority(redis_client):
    """测试 Redis 队列优先级"""
    queue = RedisTaskQueue("redis://localhost:6379/0")

    # 添加不同优先级的任务
    queue.enqueue("task-001", priority=5)
    queue.enqueue("task-002", priority=1)  # 高优先级
    queue.enqueue("task-003", priority=10) # 低优先级

    # 应该按优先级取出：task-002, task-001, task-003
    assert queue.dequeue() == "task-002"
    assert queue.dequeue() == "task-001"
    assert queue.dequeue() == "task-003"

def test_memory_queue_basic():
    """测试内存队列基本功能"""
    queue = MemoryTaskQueue(maxsize=10)

    queue.enqueue("task-001", priority=5)
    queue.enqueue("task-002", priority=1)

    assert queue.dequeue() == "task-002"  # 优先级高的先出
    assert queue.dequeue() == "task-001"

@patch('app.services.task_queue_service.redis')
def test_queue_fallback_to_memory(mock_redis):
    """测试队列降级到内存"""
    # 模拟 Redis 不可用
    mock_redis.from_url.side_effect = Exception("Redis 连接失败")

    queue = TaskQueueFactory.create_queue()

    # 应该降级到内存队列
    assert isinstance(queue, MemoryTaskQueue)
    assert not isinstance(queue, RedisTaskQueue)
```

#### 2.2 异步内容生成服务测试

**文件**：`tests/unit/services/test_async_content_generation_service.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.async_content_generation_service import AsyncContentGenerationService

def test_submit_task_success(db):
    """测试成功提交任务"""
    service = AsyncContentGenerationService()

    task_id = service.submit_task(
        account_id=49,
        topic="测试选题",
        keywords="关键词",
        auto_approve=True
    )

    # 验证任务已创建
    assert task_id is not None
    assert len(task_id) > 0  # UUID 格式

    task = service.get_task_by_id(task_id)
    assert task.status == "pending"
    assert task.auto_approve is True

@patch('subprocess.run')
def test_submit_to_creator_cli(mock_run):
    """测试调用 content-creator CLI"""
    # 模拟 CLI 返回
    mock_run.return_value = MagicMock(
        stdout="✅ 任务已提交\n任务ID: uuid-xxxx\n状态: pending",
        returncode=0
    )

    service = AsyncContentGenerationService()
    result = service._call_creator_cli(
        topic="测试选题",
        requirements="测试要求"
    )

    assert result["task_id"] == "uuid-xxxx"
    assert result["status"] == "pending"

    # 验证 CLI 调用参数
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert "--mode" in call_args[0][0]
    assert "async" in call_args[0][0]

def test_batch_submit_tasks(db):
    """测试批量提交任务"""
    service = AsyncContentGenerationService()

    tasks = [
        {"account_id": 49, "topic": "选题1", "keywords": "关键词1"},
        {"account_id": 49, "topic": "选题2", "keywords": "关键词2"},
        {"account_id": 49, "topic": "选题3", "keywords": "关键词3"},
    ]

    task_ids = service.submit_batch_tasks(tasks)

    assert len(task_ids) == 3
    assert all(tid is not None for tid in task_ids)
```

#### 2.3 状态轮询器测试

**文件**：`tests/unit/services/test_task_status_poller.py`

```python
import pytest
from unittest.mock import Mock, patch
from app.services.task_status_poller import TaskStatusPoller

@patch('subprocess.run')
def test_poll_task_status(mock_run):
    """测试轮询任务状态"""
    # 模拟 CLI 返回
    mock_run.return_value = MagicMock(
        stdout="任务ID: uuid-xxxx\n状态: running\n进度: 50%",
        returncode=0
    )

    poller = TaskStatusPoller()
    status = poller.check_task_status("uuid-xxxx")

    assert status["status"] == "running"
    assert status["progress"] == "50"

@patch('subprocess.run')
def test_poll_completed_task_and_fetch_result(mock_run):
    """测试轮询完成任务并获取结果"""
    # 第一次调用：running
    mock_run.side_effect = [
        MagicMock(stdout="状态: running", returncode=0),
        MagicMock(stdout="状态: completed", returncode=0),
        MagicMock(stdout='{"content": "文章内容", "images": []}', returncode=0)
    ]

    poller = TaskStatusPoller()

    # 第一次查询：running
    status1 = poller.check_task_status("uuid-xxxx")
    assert status1["status"] == "running"

    # 第二次查询：completed
    status2 = poller.check_task_status("uuid-xxxx")
    assert status2["status"] == "completed"

    # 获取结果
    result = poller.fetch_task_result("uuid-xxxx")
    assert result["content"] == "文章内容"

def test_poll_multiple_tasks():
    """测试批量轮询任务"""
    poller = TaskStatusPoller()

    # 模拟数据库返回3个进行中的任务
    pending_tasks = [
        Mock(task_id="uuid-001", status="running"),
        Mock(task_id="uuid-002", status="running"),
        Mock(task_id="uuid-003", status="pending"),
    ]

    with patch.object(poller, 'check_task_status') as mock_check:
        # 模拟状态返回
        mock_check.side_effect = [
            {"status": "completed"},
            {"status": "running"},
            {"status": "running"}
        ]

        results = poller.poll_pending_tasks(pending_tasks)

        assert results["uuid-001"]["status"] == "completed"
        assert results["uuid-002"]["status"] == "running"
        assert results["uuid-003"]["status"] == "running"
```

#### 2.4 结果处理器测试

**文件**：`tests/unit/services/test_task_result_handler.py`

```python
import pytest
from app.services.task_result_handler import TaskResultHandler
from app.models.content_generation_task import ContentGenerationTask

def test_handle_success_with_auto_approve(db):
    """测试处理成功结果（自动审核）"""
    handler = TaskResultHandler()

    task = ContentGenerationTask(
        task_id="uuid-001",
        account_id=49,
        status="running",
        auto_approve=True
    )
    db.add(task)
    db.commit()

    result = {
        "content": "# 测试文章\n\n这是内容",
        "images": ["image1.jpg"],
        "qualityScore": 8.5
    }

    handler.handle_success(task, result)

    # 验证内容已创建
    assert task.content_id is not None
    content = db.query(Content).filter_by(id=task.content_id).first()
    assert content is not None
    assert content.review_status == "approved"  # 自动审核通过

    # 验证已添加到发布池
    pool_entry = db.query(PublishPool).filter_by(content_id=task.content_id).first()
    assert pool_entry is not None

def test_handle_success_without_auto_approve(db):
    """测试处理成功结果（需要人工审核）"""
    handler = TaskResultHandler()

    task = ContentGenerationTask(
        task_id="uuid-002",
        account_id=49,
        status="running",
        auto_approve=False  # 不自动审核
    )
    db.add(task)
    db.commit()

    result = {"content": "文章内容", "images": []}

    handler.handle_success(task, result)

    # 验证内容已创建
    assert task.content_id is not None
    content = db.query(Content).filter_by(id=task.content_id).first()
    assert content is not None
    assert content.review_status == "pending"  # 待审核

def test_handle_failure_with_retry(db):
    """测试处理失败（可重试）"""
    handler = TaskResultHandler()

    task = ContentGenerationTask(
        task_id="uuid-003",
        account_id=49,
        status="running",
        retry_count=0,
        max_retries=3,
        error_message="API超时"
    )
    db.add(task)
    db.commit()

    error = Exception("API timeout")

    handler.handle_failure(task, error)

    # 验证任务已标记为可重试
    assert task.status == "pending"
    assert task.retry_count == 1

    # 验证已重新提交到队列
    # （需要 mock 队列服务）

def test_handle_failure_no_retry(db):
    """测试处理失败（不可重试）"""
    handler = TaskResultHandler()

    task = ContentGenerationTask(
        task_id="uuid-004",
        account_id=49,
        status="running",
        retry_count=3,
        max_retries=3,
        error_message="无效参数"
    )
    db.add(task)
    db.commit()

    error = Exception("Invalid parameters")

    handler.handle_failure(task, error)

    # 验证任务已标记为失败
    assert task.status == "failed"
    assert task.retry_count == 3  # 达到最大重试次数
```

---

## 💻 阶段 3：CLI 命令测试

### 测试文件
```
tests/integration/test_cli_async_generate.py
tests/integration/test_cli_task_management.py
```

### 测试用例

#### 3.1 异步生成命令测试

**文件**：`tests/integration/test_cli_async_generate.py`

```python
import pytest
import subprocess
import time

def test_cli_generate_async_mode():
    """测试 CLI 异步生成命令"""
    # 提交异步任务
    result = subprocess.run(
        ["python", "-m", "cli.main", "content", "generate",
         "--account-id", "49",
         "--topic", "CLI测试选题",
         "--keywords", "测试关键词",
         "--async"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "任务已提交" in result.stdout
    assert "task_id:" in result.stdout.lower()

    # 提取 task_id
    task_id = result.stdout.split("task_id:")[1].strip().split()[0]

    return task_id

def test_cli_generate_with_wait():
    """测试 CLI 等待模式"""
    result = subprocess.run(
        ["python", "-m", "cli.main", "content", "generate",
         "--account-id", "49",
         "--topic", "等待测试",
         "--keywords", "关键词",
         "--async", "--wait"],  # 等待完成
        capture_output=True,
        text=True,
        timeout=300  # 5分钟超时
    )

    assert result.returncode == 0
    assert "完成" in result.stdout or "completed" in result.stdout.lower()

def test_cli_generate_sync_mode():
    """测试 CLI 同步模式（向后兼容）"""
    result = subprocess.run(
        ["python", "-m", "cli.main", "content", "generate",
         "--account-id", "49",
         "--topic", "同步测试",
         "--keywords", "关键词"],
        capture_output=True,
        text=True,
        timeout=300
    )

    assert result.returncode == 0
    # 同步模式应该返回内容
    assert "内容" in result.stdout or "content" in result.stdout.lower()
```

#### 3.2 任务管理命令测试

**文件**：`tests/integration/test_cli_task_management.py`

```python
import pytest
import subprocess

def test_cli_task_status():
    """测试查询任务状态"""
    # 先创建一个任务
    task_id = create_test_task()

    # 查询状态
    result = subprocess.run(
        ["python", "-m", "cli.main", "tasks", "status", task_id],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "任务ID" in result.stdout
    assert "状态" in result.stdout

def test_cli_task_list():
    """测试列出任务"""
    result = subprocess.run(
        ["python", "-m", "cli.main", "tasks", "list", "--status", "running"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    # 应该显示任务列表

def test_cli_task_list_with_filters():
    """测试带筛选条件的任务列表"""
    result = subprocess.run(
        ["python", "-m", "cli.main", "tasks", "list",
         "--account-id", "49",
         "--status", "pending",
         "--limit", "10"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    # 验证输出格式

def test_cli_task_cancel():
    """测试取消任务"""
    task_id = create_test_task()

    result = subprocess.run(
        ["python", "-m", "cli.main", "tasks", "cancel", task_id],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "取消" in result.stdout or "cancelled" in result.stdout.lower()

def test_cli_task_retry():
    """测试重试失败任务"""
    # 先创建一个失败的任务
    task_id = create_failed_task()

    result = subprocess.run(
        ["python", "-m", "cli.main", "tasks", "retry", task_id],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "重试" in result.stdout or "retry" in result.stdout.lower()
```

---

## 🔄 阶段 4：定时任务集成测试

### 测试文件
```
tests/integration/test_scheduler_async_tasks.py
tests/integration/test_end_to_end_workflow.py
```

### 测试用例

#### 4.1 异步生成任务执行器测试

**文件**：`tests/integration/test_scheduler_async_tasks.py`

```python
import pytest
from app.services.executors.async_content_generation_executor import AsyncContentGenerationExecutor

def test_executor_submit_multiple_tasks():
    """测试执行器提交多个任务"""
    executor = AsyncContentGenerationExecutor()

    job_config = {
        "account_id": 49,
        "count": 3,
        "topic_template": "测试选题 {}",
        "auto_approve": True
    }

    result = executor.execute(job_config)

    assert result["success"] is True
    assert result["submitted_tasks"] == 3
    assert len(result["task_ids"]) == 3

    # 验证任务已创建
    task_ids = result["task_ids"]
    for task_id in task_ids:
        task = db.query(ContentGenerationTask).filter_by(task_id=task_id).first()
        assert task is not None
        assert task.auto_approve is True

def test_executor_with_different_params():
    """测试执行器使用不同参数"""
    executor = AsyncContentGenerationExecutor()

    job_config = {
        "account_id": 49,
        "count": 2,
        "keywords": "关键词1,关键词2",
        "category": "汽车",
        "tone": "轻松",
        "auto_approve": False  # 不自动审核
    }

    result = executor.execute(job_config)

    assert result["submitted_tasks"] == 2

    # 验证任务的 auto_approve 设置
    task_ids = result["task_ids"]
    for task_id in task_ids:
        task = db.query(ContentGenerationTask).filter_by(task_id=task_id).first()
        assert task.auto_approve is False
```

#### 4.2 端到端工作流测试

**文件**：`tests/integration/test_end_to_end_workflow.py`

```python
import pytest
import subprocess
import time

def test_end_to_end_workflow_with_auto_approve():
    """测试完整工作流（自动审核）"""
    # 1. 定时任务触发
    scheduler_result = subprocess.run(
        ["python", "-m", "cli.main", "scheduler", "trigger", "test-daily-job"],
        capture_output=True,
        text=True
    )
    assert scheduler_result.returncode == 0

    # 2. 验证任务已提交
    time.sleep(2)

    # 3. 等待任务完成（最多5分钟）
    max_wait = 300  # 5分钟
    start_time = time.time()

    while time.time() - start_time < max_wait:
        # 检查任务状态
        tasks = get_running_tasks()
        if len(tasks) == 0:
            break
        time.sleep(10)

    # 4. 验证内容已创建
    contents = db.query(Content).filter_by(account_id=49).all()
    assert len(contents) > 0

    # 5. 验证自动审核通过
    approved_contents = [c for c in contents if c.review_status == "approved"]
    assert len(approved_contents) > 0

    # 6. 验证已添加到发布池
    pool_entries = db.query(PublishPool).filter_by(content_id=approved_contents[0].id).all()
    assert len(pool_entries) > 0

def test_end_to_end_workflow_without_auto_approve():
    """测试完整工作流（需人工审核）"""
    # 创建任务时设置 auto_approve=false
    task_id = submit_task_with_params(auto_approve=False)

    # 等待任务完成
    wait_for_task_completion(task_id, timeout=300)

    # 验证内容待审核
    content = get_content_by_task_id(task_id)
    assert content.review_status == "pending"

    # 手动审核通过
    approve_content(content.id)

    # 验证已添加到发布池
    pool_entry = db.query(PublishPool).filter_by(content_id=content.id).first()
    assert pool_entry is not None

def test_error_handling_and_retry():
    """测试错误处理和重试"""
    # 模拟 content-creator 返回错误
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            # 第一次：失败
            MagicMock(stdout="❌ 生成失败", returncode=1),
            # 第二次：重试
            MagicMock(stdout="❌ 生成失败", returncode=1),
            # 第三次：成功
            MagicMock(stdout="✅ 生成成功", returncode=0)
        ]

        task_id = submit_task()

        # 等待重试完成
        wait_for_task_completion(task_id, timeout=180)

        # 验证最终成功
        task = get_task_by_id(task_id)
        assert task.status == "completed"
        assert task.retry_count == 2  # 重试了2次
```

---

## 🚀 阶段 5：性能测试

### 测试文件
```
tests/performance/test_queue_throughput.py
tests/performance/test_concurrent_tasks.py
tests/performance/test_poller_performance.py
```

### 测试用例

#### 5.1 队列吞吐量测试

**文件**：`tests/performance/test_queue_throughput.py`

```python
import pytest
import time

def test_queue_throughput_redis():
    """测试 Redis 队列吞吐量"""
    queue = RedisTaskQueue("redis://localhost:6379/0")

    # 批量添加任务
    start_time = time.time()
    for i in range(100):
        queue.enqueue(f"task-{i}", priority=5)
    elapsed = time.time() - start_time

    # 100个任务应该在1秒内完成
    assert elapsed < 1.0
    print(f"✅ 100个任务入队耗时: {elapsed:.3f}秒")

def test_queue_throughput_memory():
    """测试内存队列吞吐量"""
    queue = MemoryTaskQueue(maxsize=100)

    start_time = time.time()
    for i in range(100):
        queue.enqueue(f"task-{i}", priority=5)
    elapsed = time.time() - start_time

    # 内存队列应该更快
    assert elapsed < 0.5
    print(f"✅ 100个任务入队耗时: {elapsed:.3f}秒")

def test_worker_concurrent_processing():
    """测试 Worker 并发处理能力"""
    worker = TaskWorker(queue=queue, num_workers=5)

    # 添加10个任务
    for i in range(10):
        submit_task_to_queue(f"task-{i}")

    start_time = time.time()
    worker.start()

    # 等待所有任务完成
    wait_for_all_tasks_complete(timeout=300)
    elapsed = time.time() - start_time

    # 10个任务应该在合理时间内完成（考虑AI生成时间）
    # 每个任务约3-5分钟，5个Worker并发，预期约6-10分钟
    assert elapsed < 600  # 10分钟
    print(f"✅ 10个任务并发处理耗时: {elapsed/60:.1f}分钟")
```

#### 5.2 轮询器性能测试

**文件**：`tests/performance/test_poller_performance.py`

```python
import pytest
import time

def test_poller_performance_with_100_tasks():
    """测试轮询器处理100个任务"""
    poller = TaskStatusPoller()

    # 创建100个进行中的任务
    for i in range(100):
        create_pending_task(f"task-{i}")

    start_time = time.time()

    # 轮询所有任务
    results = poller.poll_all_pending_tasks()

    elapsed = time.time() - start_time

    # 100个任务轮询应该在合理时间内完成
    # 每个任务约需0.1秒（CLI调用）
    assert elapsed < 15  # 15秒
    assert len(results) == 100

    print(f"✅ 轮询100个任务耗时: {elapsed:.2f}秒")
    print(f"   平均每个任务: {elapsed/100*1000:.0f}毫秒")

def test_poller_efficiency():
    """测试轮询器效率（避免重复轮询）"""
    poller = TaskStatusPoller()

    # 创建10个任务
    for i in range(10):
        create_pending_task(f"task-{i}")

    # 轮询3次
    with patch.object(poller, 'check_task_status') as mock_check:
        mock_check.return_value = {"status": "running"}

        start_time = time.time()

        for _ in range(3):
            poller.poll_all_pending_tasks()

        elapsed = time.time() - start_time

        # 验证：每个任务应该被调用3次
        assert mock_check.call_count == 30  # 10个任务 × 3次
```

---

## ✅ 验收标准

### 功能验收

#### 1. 任务提交
- [ ] 可以通过 CLI 提交异步任务
- [ ] 立即返回 task_id
- [ ] 任务记录正确保存到数据库
- [ ] 支持 `auto_approve` 参数

#### 2. 状态监控
- [ ] 轮询器能正确查询任务状态
- [ ] 超时任务能被检测和标记
- [ ] 完成任务能自动获取结果

#### 3. 结果处理
- [ ] 成功任务能创建 Content 记录
- [ ] 自动审核能正确执行（`auto_approve=true`）
- [ ] 人工审核流程正常（`auto_approve=false`）
- [ ] 发布池自动添加正常

#### 4. 队列降级
- [ ] Redis 可用时使用 Redis 队列
- [ ] Redis 不可用时自动降级到内存队列
- [ ] 降级过程有日志记录

#### 5. 错误处理
- [ ] 可重试错误能自动重试
- [ ] 重试次数符合配置
- [ ] 不可重试错误能正确标记失败
- [ ] 失败任务有告警通知

### 性能验收

#### 1. 响应时间
- [ ] 定时任务响应时间 < 5秒
- [ ] CLI 提交任务响应时间 < 1秒
- [ ] 队列入队操作 < 10ms（100个任务）

#### 2. 并发能力
- [ ] 支持 5 个并发任务
- [ ] 队列吞吐量 > 100 任务/小时
- [ ] Worker 利用率 > 80%

#### 3. 轮询效率
- [ ] 轮询间隔符合配置（30秒）
- [ ] 100个任务轮询完成时间 < 15秒
- [ ] 无重复轮询同一任务

### 稳定性验收

#### 1. 长时间运行
- [ ] 连续运行 24小时无崩溃
- [ ] 内存占用稳定（< 500MB）
- [ ] 无内存泄漏

#### 2. 异常恢复
- [ ] Redis 连接断开后能自动降级
- [ ] Worker 异常后能自动重启
- [ ] 任务数据不丢失

#### 3. 资源清理
- [ ] 完成的任务能及时清理
- [ ] 失败的任务有保留策略
- [ ] 数据库连接正常释放

---

## 📊 测试执行计划

### 第 1 周：单元测试

| 日期 | 测试内容 | 负责人 |
|------|----------|--------|
| Day 1 | 数据库模型测试 | 开发 |
| Day 2 | 任务队列服务测试 | 开发 |
| Day 3 | 异步服务测试 | 开发 |
| Day 4 | CLI 命令测试 | 开发 |
| Day 5 | 集成测试 | 开发 |

### 第 2 周：集成和性能测试

| 日期 | 测试内容 | 负责人 |
|------|----------|--------|
| Day 6 | 端到端工作流测试 | 测试 |
| Day 7 | 队列降级机制测试 | 测试 |
| Day 8 | 性能测试（吞吐量、并发） | 测试 |
| Day 9 | 压力测试（长时间运行） | 测试 |
| Day 10 | 回归测试（确保功能未破坏） | 测试 |

---

## 🐛 已知问题和风险

### 1. content-creator 集成风险

**风险**：CLI 命令可能失败或超时

**缓解措施**：
- 添加超时控制（subprocess timeout）
- 添加重试机制
- 记录详细的错误日志

### 2. Redis 依赖风险

**风险**：Redis 不可用时性能下降

**缓解措施**：
- 实现内存队列降级
- 监控 Redis 健康状态
- 提前告警 Redis 问题

### 3. 并发控制风险

**风险**：过多并发任务导致资源耗尽

**缓解措施**：
- 限制最大并发数（MAX_CONCURRENT_TASKS=5）
- 实现队列大小限制（QUEUE_SIZE=100）
- 监控系统资源使用

### 4. 数据一致性风险

**风险**：任务状态更新可能失败

**缓解措施**：
- 使用数据库事务
- 添加状态更新日志
- 实现状态校验机制

---

## 📝 测试数据准备

### 测试账号
- 账号 ID：49（车界显眼包）
- 客户 ID：50
- 平台 ID：1（微信公众号）

### 测试选题
- 正常选题："2025年汽车智能化技术发展"
- 长选题：2000字的深度分析文章
- 特殊字符：包含 emoji、中英文混合

### 测试关键词
- 单个关键词："汽车"
- 多个关键词："汽车,智能化,新能源"
- 特殊字符："关键词1,关键词2@#"

---

## ✅ 测试通过标准

### 单元测试
- [ ] 覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 无 skipped tests

### 集成测试
- [ ] 覆盖率 > 70%
- [ ] 所有测试通过
- [ ] 核心流程 100% 通过

### E2E 测试
- [ ] 主要业务流程 100% 通过
- [ ] 性能指标达标
- [ ] 无严重 Bug

### 性能测试
- [ ] 响应时间达标
- [ ] 并发能力达标
- [ ] 无资源泄漏

---

## 📅 下一步行动

1. ✅ 设计文档已完成
2. ✅ 执行计划已制定
3. ⏳ **测试计划已完成** ← 当前

**请审核测试计划，确认后即可开始实施！**

如有需要调整的测试用例或验收标准，请告知。
