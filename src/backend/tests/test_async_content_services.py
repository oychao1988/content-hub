"""
测试异步内容生成核心服务

测试以下服务：
1. AsyncContentGenerationService - 任务管理服务
2. TaskStatusPoller - 状态轮询器
3. TaskResultHandler - 结果处理器
4. TaskQueueService - 任务队列和 Worker

运行方式：
    pytest tests/test_async_content_services.py -v
    pytest tests/test_async_content_services.py::test_async_service_submit -v
"""
import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.models import ContentGenerationTask, Account, Content, PublishPool
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.services.task_status_poller import TaskStatusPoller
from app.services.task_result_handler import TaskResultHandler
from app.services.task_queue_service import (
    MemoryTaskQueue,
    TaskQueueFactory,
    TaskWorker,
    TaskWorkerPool,
    get_task_worker_pool,
    stop_worker_pool
)


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db():
    """数据库会话 fixture"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_account(db: Session):
    """创建测试账号"""
    from app.models import Customer, Platform

    # 创建客户
    customer = Customer(
        name="测试客户",
        code="test_customer",
        contact="测试联系人",
        email="test@example.com",
        phone="13800138000"
    )
    db.add(customer)
    db.flush()

    # 创建平台
    platform = Platform(
        name="微信公众号",
        code="wechat_mp",
        description="测试平台"
    )
    db.add(platform)
    db.flush()

    # 创建账号
    account = Account(
        name="测试公众号",
        customer_id=customer.id,
        platform_id=platform.id,
        directory_name="test_account_001"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture(scope="function")
def async_service(db: Session):
    """异步内容生成服务 fixture"""
    return AsyncContentGenerationService(db)


@pytest.fixture(scope="function")
def result_handler():
    """结果处理器 fixture"""
    return TaskResultHandler()


@pytest.fixture(scope="function")
def status_poller():
    """状态轮询器 fixture"""
    return TaskStatusPoller(poll_interval=1)


# ==================== AsyncContentGenerationService 测试 ====================

class TestAsyncContentGenerationService:
    """测试异步内容生成服务"""

    def test_submit_task_success(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试成功提交任务"""
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题：人工智能的未来",
            keywords="AI,人工智能",
            category="科技",
            requirements="请详细论述",
            tone="专业",
            priority=8,
            auto_approve=True
        )

        assert task_id is not None
        assert task_id.startswith("task-")

        # 验证任务已创建
        task = async_service.get_task_by_id(task_id)
        assert task is not None
        assert task.topic == "测试选题：人工智能的未来"
        assert task.status == "pending"
        assert task.priority == 8
        assert task.auto_approve is True

    def test_submit_task_with_invalid_account(self, async_service: AsyncContentGenerationService):
        """测试使用无效账号提交任务"""
        with pytest.raises(Exception) as exc_info:
            async_service.submit_task(
                account_id=99999,
                topic="测试选题"
            )
        assert "账号" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_get_task_status(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试查询任务状态"""
        # 创建任务
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        # 查询状态
        status = async_service.get_task_status(task_id)

        assert status is not None
        assert status["task_id"] == task_id
        assert status["status"] == "pending"
        assert status["topic"] == "测试选题"
        assert status["account_id"] == test_account.id

    def test_get_task_status_not_found(self, async_service: AsyncContentGenerationService):
        """测试查询不存在的任务"""
        status = async_service.get_task_status("invalid-task-id")
        assert status is None

    def test_list_tasks(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试列出任务"""
        # 创建多个任务
        task_id_1 = async_service.submit_task(
            account_id=test_account.id,
            topic="选题1",
            priority=5
        )
        task_id_2 = async_service.submit_task(
            account_id=test_account.id,
            topic="选题2",
            priority=8
        )

        # 列出所有任务
        tasks = async_service.list_tasks(account_id=test_account.id)
        assert len(tasks) >= 2

        # 按状态筛选
        pending_tasks = async_service.list_tasks(
            account_id=test_account.id,
            status="pending"
        )
        assert len(pending_tasks) >= 2

    def test_cancel_task_success(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试取消任务"""
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        # 取消任务
        result = async_service.cancel_task(task_id)
        assert result is True

        # 验证状态
        task = async_service.get_task_by_id(task_id)
        assert task.status == "cancelled"
        assert task.completed_at is not None

    def test_cancel_task_invalid_state(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试取消已完成任务"""
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        # 手动设置为已完成
        task = async_service.get_task_by_id(task_id)
        task.status = "completed"
        async_service.db.commit()

        # 尝试取消
        with pytest.raises(Exception):
            async_service.cancel_task(task_id)

    def test_get_pending_tasks(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试获取待处理任务"""
        # 创建多个任务
        for i in range(3):
            async_service.submit_task(
                account_id=test_account.id,
                topic=f"选题{i}",
                priority=i + 1
            )

        # 获取待处理任务
        pending_tasks = async_service.get_pending_tasks()
        assert len(pending_tasks) >= 3

        # 验证排序（按优先级降序）
        priorities = [t.priority for t in pending_tasks[:3]]
        assert priorities == sorted(priorities, reverse=True)

    def test_get_running_tasks(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试获取运行中任务"""
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        # 手动设置为运行中
        task = async_service.get_task_by_id(task_id)
        task.status = "processing"
        async_service.db.commit()

        # 获取运行中任务
        running_tasks = async_service.get_running_tasks()
        assert len(running_tasks) >= 1
        assert any(t.task_id == task_id for t in running_tasks)

    def test_update_task_status(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试更新任务状态"""
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        # 更新为处理中
        result = async_service.update_task_status(task_id, "processing")
        assert result is True

        task = async_service.get_task_by_id(task_id)
        assert task.status == "processing"
        assert task.started_at is not None

        # 更新为已完成
        result = async_service.update_task_status(task_id, "completed")
        assert result is True

        task = async_service.get_task_by_id(task_id)
        assert task.status == "completed"
        assert task.completed_at is not None

    def test_cleanup_old_tasks(self, async_service: AsyncContentGenerationService, test_account: Account):
        """测试清理旧任务"""
        # 创建并完成一个任务
        task_id = async_service.submit_task(
            account_id=test_account.id,
            topic="测试选题"
        )

        task = async_service.get_task_by_id(task_id)
        task.status = "completed"
        task.completed_at = datetime.utcnow() - timedelta(days=10)
        async_service.db.commit()

        # 清理旧任务
        deleted_count = async_service.cleanup_old_tasks(days=7)
        assert deleted_count >= 1

        # 验证已删除
        task = async_service.get_task_by_id(task_id)
        assert task is None


# ==================== TaskResultHandler 测试 ====================

class TestTaskResultHandler:
    """测试任务结果处理器"""

    def test_handle_success(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试处理成功任务"""
        # 创建任务
        task = ContentGenerationTask(
            task_id="test-success-task",
            account_id=test_account.id,
            topic="测试选题",
            category="科技",
            priority=5,
            auto_approve=True,
            status="processing"
        )
        db.add(task)
        db.commit()

        # 模拟结果
        result = {
            "content": "这是生成的内容",
            "htmlContent": "<p>这是生成的内容</p>",
            "images": ["image1.jpg", "image2.jpg"],
            "qualityScore": 0.85
        }

        # 处理成功
        content = result_handler.handle_success(db, task, result)

        assert content is not None
        assert content.topic == "测试选题"
        assert content.content == "这是生成的内容"
        assert content.generation_task_id == "test-success-task"
        assert content.review_status == "approved"

        # 验证任务已更新
        db.refresh(task)
        assert task.status == "completed"
        assert task.content_id == content.id

        # 验证已添加到发布池
        pool_entry = db.query(PublishPool).filter_by(content_id=content.id).first()
        assert pool_entry is not None

    def test_handle_success_without_auto_approve(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试处理成功任务（不自动审核）"""
        task = ContentGenerationTask(
            task_id="test-manual-task",
            account_id=test_account.id,
            topic="测试选题",
            priority=5,
            auto_approve=False,
            status="processing"
        )
        db.add(task)
        db.commit()

        result = {
            "content": "这是生成的内容",
            "qualityScore": 0.85
        }

        content = result_handler.handle_success(db, task, result)

        assert content is not None
        assert content.review_status == "pending_review"

    def test_handle_failure(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试处理失败任务"""
        task = ContentGenerationTask(
            task_id="test-failed-task",
            account_id=test_account.id,
            topic="测试选题",
            status="processing"
        )
        db.add(task)
        db.commit()

        # 处理失败
        result_handler.handle_failure(db, task, "生成失败：网络错误")

        # 验证状态
        db.refresh(task)
        assert task.status == "failed"
        assert task.completed_at is not None
        assert "网络错误" in task.error_message

    def test_handle_timeout(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试处理超时任务"""
        task = ContentGenerationTask(
            task_id="test-timeout-task",
            account_id=test_account.id,
            topic="测试选题",
            status="processing"
        )
        db.add(task)
        db.commit()

        # 处理超时
        result_handler.handle_timeout(db, task)

        # 验证状态
        db.refresh(task)
        assert task.status == "timeout"
        assert task.completed_at is not None
        assert "timeout" in task.error_message.lower()

    def test_handle_cancelled(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试处理取消任务"""
        task = ContentGenerationTask(
            task_id="test-cancelled-task",
            account_id=test_account.id,
            topic="测试选题",
            status="processing"
        )
        db.add(task)
        db.commit()

        # 处理取消
        result_handler.handle_cancelled(db, task)

        # 验证状态
        db.refresh(task)
        assert task.status == "cancelled"
        assert task.completed_at is not None

    def test_retry_task(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试重试任务"""
        task = ContentGenerationTask(
            task_id="test-retry-task",
            account_id=test_account.id,
            topic="测试选题",
            status="failed",
            retry_count=0,
            max_retries=3
        )
        db.add(task)
        db.commit()

        # 重试任务
        result = result_handler.retry_task(db, task)
        assert result is True

        # 验证状态
        db.refresh(task)
        assert task.status == "pending"
        assert task.retry_count == 1

    def test_retry_task_max_retries(self, result_handler: TaskResultHandler, db: Session, test_account: Account):
        """测试重试任务达到最大次数"""
        task = ContentGenerationTask(
            task_id="test-max-retry-task",
            account_id=test_account.id,
            topic="测试选题",
            status="failed",
            retry_count=3,
            max_retries=3
        )
        db.add(task)
        db.commit()

        # 重试任务
        result = result_handler.retry_task(db, task)
        assert result is False


# ==================== TaskStatusPoller 测试 ====================

class TestTaskStatusPoller:
    """测试任务状态轮询器"""

    def test_poll_running_tasks_empty(self, status_poller: TaskStatusPoller):
        """测试轮询空任务列表"""
        stats = status_poller.poll_running_tasks()
        assert stats["total"] == 0
        assert stats["completed"] == 0

    def test_poll_single_task(self, status_poller: TaskStatusPoller, db: Session, test_account: Account):
        """测试轮询单个任务"""
        task = ContentGenerationTask(
            task_id="test-poll-task",
            account_id=test_account.id,
            topic="测试选题",
            status="submitted",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db.add(task)
        db.commit()

        # 轮询（由于 CLI 不可用，预期会有错误）
        stats = status_poller.poll_running_tasks()
        assert stats["total"] >= 1


# ==================== MemoryTaskQueue 测试 ====================

class TestMemoryTaskQueue:
    """测试内存任务队列"""

    def test_queue_put_and_get(self, db: Session, test_account: Account):
        """测试队列放入和获取"""
        queue = MemoryTaskQueue(maxsize=10)

        task = ContentGenerationTask(
            task_id="test-queue-task",
            account_id=test_account.id,
            topic="测试选题",
            status="pending"
        )

        # 放入任务
        result = queue.put(task)
        assert result is True
        assert queue.size() == 1

        # 获取任务
        retrieved_task = queue.get()
        assert retrieved_task is not None
        assert retrieved_task.task_id == "test-queue-task"
        assert queue.size() == 0

    def test_queue_full(self, db: Session, test_account: Account):
        """测试队列已满"""
        queue = MemoryTaskQueue(maxsize=2)

        # 放入两个任务
        for i in range(2):
            task = ContentGenerationTask(
                task_id=f"task-{i}",
                account_id=test_account.id,
                topic=f"选题{i}",
                status="pending"
            )
            queue.put(task)

        # 第三个任务应该失败
        task = ContentGenerationTask(
            task_id="task-full",
            account_id=test_account.id,
            topic="满载",
            status="pending"
        )
        result = queue.put(task)
        assert result is False

    def test_queue_empty(self):
        """测试队列为空"""
        queue = MemoryTaskQueue()
        assert queue.empty() is True

        task = queue.get()
        assert task is None

    def test_task_done_and_join(self, db: Session, test_account: Account):
        """测试任务完成和等待"""
        queue = MemoryTaskQueue()

        task = ContentGenerationTask(
            task_id="test-done-task",
            account_id=test_account.id,
            topic="测试选题",
            status="pending"
        )

        queue.put(task)
        queue.task_done()

        # 不应该阻塞
        queue.join(timeout=1)


# ==================== TaskWorker 测试 ====================

class TestTaskWorker:
    """测试任务 Worker"""

    def test_worker_start_and_stop(self):
        """测试 Worker 启动和停止"""
        worker = TaskWorker(worker_id=0, num_workers=1, poll_interval=1)

        # 启动
        worker.start()
        assert worker.running is True
        assert worker.thread is not None

        # 停止
        worker.stop()
        assert worker.running is False

    def test_worker_add_task(self, db: Session, test_account: Account):
        """测试 Worker 添加任务"""
        worker = TaskWorker(worker_id=0, num_workers=1)

        task = ContentGenerationTask(
            task_id="worker-test-task",
            account_id=test_account.id,
            topic="测试选题",
            status="pending"
        )

        result = worker.add_task(task)
        assert result is True
        assert worker.get_queue_size() == 1

        worker.stop()

    def test_worker_pool(self):
        """测试 Worker 池"""
        pool = TaskWorkerPool(num_workers=2)

        # 启动
        pool.start()
        assert len(pool.workers) == 2

        # 获取状态
        status = pool.get_status()
        assert status["num_workers"] == 2
        assert status["active_workers"] == 2

        # 停止
        pool.stop()
        assert len(pool.workers) == 0


# ==================== 集成测试 ====================

class TestAsyncContentIntegration:
    """集成测试"""

    def test_full_workflow_without_cli(self, async_service: AsyncContentGenerationService, result_handler: TaskResultHandler, test_account: Account):
        """测试完整工作流（不依赖 CLI）"""
        # 1. 提交任务
        with pytest.raises(Exception):
            # CLI 不可用，预期会失败
            task_id = async_service.submit_task(
                account_id=test_account.id,
                topic="完整测试选题"
            )

        # 手动创建任务
        task = ContentGenerationTask(
            task_id="integration-test-task",
            account_id=test_account.id,
            topic="完整测试选题",
            category="测试",
            priority=5,
            auto_approve=True,
            status="processing"
        )
        async_service.db.add(task)
        async_service.db.commit()

        # 2. 模拟成功结果
        result = {
            "content": "完整测试内容",
            "qualityScore": 0.9
        }

        # 3. 处理结果
        content = result_handler.handle_success(async_service.db, task, result)
        assert content is not None

        # 4. 验证完整流程
        async_service.db.refresh(task)
        assert task.status == "completed"
        assert task.content_id == content.id


# ==================== 运行测试辅助函数 ====================

def run_basic_tests():
    """运行基础测试"""
    pytest.main([__file__, "-v", "-k", "test_submit_task_success or test_queue_put_and_get or test_worker_start_and_stop"])


def run_all_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()
