"""
完整的异步内容生成工作流集成测试

注意：这些测试需要完整的数据库和 content-creator CLI 环境。
如果 CLI 不可用，部分测试会失败。
"""
import pytest
import time
import uuid
from datetime import datetime
from sqlalchemy import inspect
from unittest.mock import Mock, patch, MagicMock
from app.db.database import SessionLocal
from app.models import ContentGenerationTask, Content, Account
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.services.task_status_poller import TaskStatusPoller
from app.services.task_result_handler import TaskResultHandler


class TestAsyncContentDatabase:
    """数据库和模型测试"""

    def test_database_schema_exists(self):
        """测试数据库表是否正确创建"""
        db = SessionLocal()
        try:
            inspector = inspect(db.bind)

            # 检查主表存在
            assert 'content_generation_tasks' in inspector.get_table_names()
            assert 'contents' in inspector.get_table_names()
            assert 'accounts' in inspector.get_table_names()

            # 检查任务表结构
            columns = [col['name'] for col in inspector.get_columns('content_generation_tasks')]
            required_columns = [
                'id', 'task_id', 'account_id', 'topic', 'keywords',
                'status', 'priority', 'submitted_at', 'completed_at',
                'error_message', 'retry_count', 'content_id', 'auto_approve'
            ]
            for col in required_columns:
                assert col in columns, f"Missing column: {col}"

        finally:
            db.close()


class TestAsyncContentTaskModel:
    """任务模型测试（不涉及 CLI）"""

    def test_task_creation_in_db(self):
        """测试在数据库中创建任务"""
        db = SessionLocal()
        try:
            # 直接创建任务记录（不通过 service）
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-test-{test_id}",
                account_id=49,
                topic="直接创建测试",
                keywords="测试",
                status="pending",
                priority=5,
                auto_approve=False
            )
            db.add(task)
            db.commit()

            # 验证
            retrieved = db.query(ContentGenerationTask).filter_by(task_id=f"task-test-{test_id}").first()
            assert retrieved is not None
            assert retrieved.topic == "直接创建测试"
            assert retrieved.status == "pending"

            # 清理
            db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_task_status_update_in_db(self):
        """测试任务状态更新"""
        db = SessionLocal()
        try:
            test_id = uuid.uuid4().hex[:8]
            # 创建任务
            task = ContentGenerationTask(
                task_id=f"task-test-{test_id}",
                account_id=49,
                topic="状态更新测试",
                status="pending"
            )
            db.add(task)
            db.commit()

            # 更新状态
            task.status = "processing"
            db.commit()

            # 验证
            db.refresh(task)
            assert task.status == "processing"

            # 清理
            db.delete(task)
            db.commit()

        finally:
            db.close()


class TestAsyncContentService:
    """服务层测试（使用 mock 避免 CLI 调用）"""

    def test_submit_task_with_mock(self):
        """测试任务提交（使用 mock）"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # Mock subprocess 调用
            with patch('app.services.async_content_generation_service.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="Task submitted: task-mock-001",
                    returncode=0
                )

                task_id = service.submit_task(
                    account_id=49,
                    topic="Mock 测试选题",
                    keywords="测试",
                    auto_approve=False
                )

                assert task_id is not None
                assert isinstance(task_id, str)

                # 验证数据库记录
                task = db.query(ContentGenerationTask).filter_by(task_id=task_id).first()
                assert task is not None
                assert task.account_id == 49
                assert task.status in ['pending', 'submitted']

                # 清理
                db.delete(task)
                db.commit()

        finally:
            db.close()

    def test_get_task_status(self):
        """测试查询任务状态"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # 创建测试任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-status-{test_id}",
                account_id=49,
                topic="状态查询测试",
                status="pending"
            )
            db.add(task)
            db.commit()

            # 查询状态
            status = service.get_task_status(f"task-status-{test_id}")

            assert status is not None
            assert status['task_id'] == f"task-status-{test_id}"
            assert status['status'] == "pending"

            # 清理
            db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_list_tasks(self):
        """测试列出任务"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # 创建测试任务（使用唯一 ID）
            test_id = uuid.uuid4().hex[:8]
            tasks = []
            for i in range(3):
                task = ContentGenerationTask(
                    task_id=f"task-list-{test_id}-{i}",
                    account_id=49,
                    topic=f"列表测试 {i}",
                    status="pending"
                )
                db.add(task)
                tasks.append(task)
            db.commit()

            # 查询任务列表
            result = service.list_tasks(account_id=49, limit=10)

            assert len(result) >= 3

            # 清理
            for task in tasks:
                db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_update_task_status(self):
        """测试更新任务状态"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # 创建测试任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-update-{test_id}",
                account_id=49,
                topic="状态更新测试",
                status="pending"
            )
            db.add(task)
            db.commit()

            # 更新状态
            service.update_task_status(f"task-update-{test_id}", "processing")

            # 验证
            db.refresh(task)
            assert task.status == "processing"

            # 清理
            db.delete(task)
            db.commit()

        finally:
            db.close()


class TestTaskResultHandler:
    """结果处理器测试"""

    def test_handle_success(self):
        """测试成功结果处理"""
        db = SessionLocal()
        try:
            # 创建任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-success-{test_id}",
                account_id=49,
                topic="结果处理测试",
                status="processing",
                auto_approve=False
            )
            db.add(task)
            db.commit()

            # 处理结果
            handler = TaskResultHandler()
            result = {
                'content': '这是测试生成的内容\n\nAI技术正在快速发展。',
                'htmlContent': '<p>这是测试生成的内容</p><p>AI技术正在快速发展。</p>',
                'images': [],
                'qualityScore': 8.5
            }

            content = handler.handle_success(db, task, result)

            # 验证内容已创建
            assert content is not None
            assert content.id is not None
            assert content.account_id == 49
            assert content.title == "结果处理测试"
            assert "AI技术正在快速发展" in content.content
            assert content.publish_status == 'draft'  # auto_approve=False

            # 验证任务已更新
            db.refresh(task)
            assert task.status == 'completed'
            assert task.content_id == content.id
            assert task.completed_at is not None

            # 清理
            db.delete(content)
            db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_handle_success_with_auto_approve(self):
        """测试自动审核场景"""
        db = SessionLocal()
        try:
            # 创建 auto_approve=True 的任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-auto-{test_id}",
                account_id=49,
                topic="自动审核测试",
                status="processing",
                auto_approve=True
            )
            db.add(task)
            db.commit()

            # 处理结果
            handler = TaskResultHandler()
            result = {
                'content': '自动审核的内容',
                'htmlContent': '<p>自动审核的内容</p>',
                'images': [],
                'qualityScore': 7.5
            }

            content = handler.handle_success(db, task, result)

            # 验证内容状态为 approved
            assert content is not None
            assert content.review_status == 'approved'

            # 清理
            db.delete(content)
            db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_handle_failure(self):
        """测试失败结果处理"""
        db = SessionLocal()
        try:
            # 创建任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-fail-{test_id}",
                account_id=49,
                topic="失败处理测试",
                status="processing"
            )
            db.add(task)
            db.commit()

            # 处理失败
            handler = TaskResultHandler()
            error_message = "内容生成失败：超时"

            handler.handle_failure(db, task, error_message)

            # 验证任务状态
            db.refresh(task)
            assert task.status == 'failed'
            assert error_message in task.error_message

            # 清理
            db.delete(task)
            db.commit()

        finally:
            db.close()


class TestAsyncContentPerformance:
    """性能测试"""

    def test_concurrent_task_creation(self):
        """测试并发任务创建"""
        db = SessionLocal()
        try:
            tasks = []
            start_time = time.time()

            for i in range(10):
                test_id = uuid.uuid4().hex[:8]
                task = ContentGenerationTask(
                    task_id=f"task-perf-{test_id}",
                    account_id=49,
                    topic=f"性能测试 {i+1}",
                    status="pending"
                )
                db.add(task)
                tasks.append(task)

            db.commit()
            elapsed_time = time.time() - start_time

            # 验证所有任务创建成功
            assert len(tasks) == 10

            # 验证响应时间（应该很快）
            assert elapsed_time < 1.0

            # 清理
            for task in tasks:
                db.delete(task)
            db.commit()

        finally:
            db.close()


class TestAsyncContentEdgeCases:
    """边界情况测试"""

    def test_get_nonexistent_task(self):
        """测试查询不存在的任务"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            status = service.get_task_status("task-nonexistent-xyz")
            assert status is None

        finally:
            db.close()

    def test_update_nonexistent_task_status(self):
        """测试更新不存在的任务状态"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # 不应该抛出异常，应该静默失败
            service.update_task_status("task-nonexistent-xyz", "processing")

            # 验证：只是没有报错即可

        finally:
            db.close()


class TestAsyncContentEndToEnd:
    """端到端集成测试（模拟）"""

    def test_complete_workflow_simulation(self):
        """测试完整的生成工作流（模拟）"""
        db = SessionLocal()
        try:
            # 1. 创建任务（模拟提交）
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-e2e-{test_id}",
                account_id=49,
                topic="端到端测试 - 智能客服系统",
                keywords="AI,客服,自动化",
                status="pending",
                priority=7,
                auto_approve=True
            )
            db.add(task)
            db.commit()

            # 2. 查询初始状态
            service = AsyncContentGenerationService(db)
            status = service.get_task_status(f"task-e2e-{test_id}")
            assert status['status'] == 'pending'

            # 3. 模拟状态流转
            service.update_task_status(f"task-e2e-{test_id}", 'submitted')
            service.update_task_status(f"task-e2e-{test_id}", 'processing')

            # 4. 处理结果
            handler = TaskResultHandler()
            result = {
                'content': '# 智能客服系统\n\nAI技术正在改变客户服务。',
                'htmlContent': '<h1>智能客服系统</h1><p>AI技术正在改变客户服务。</p>',
                'images': [
                    {'url': 'https://example.com/ai-cs.jpg', 'alt': '智能客服'}
                ],
                'qualityScore': 9.0
            }

            task = db.query(ContentGenerationTask).filter_by(task_id=f"task-e2e-{test_id}").first()
            content = handler.handle_success(db, task, result)

            # 5. 验证最终状态
            db.refresh(task)
            assert task.status == 'completed'
            assert task.content_id == content.id
            assert task.completed_at is not None

            assert content is not None
            assert content.review_status == 'approved'  # auto_approve=True

            # 清理
            db.delete(content)
            db.delete(task)
            db.commit()

        finally:
            db.close()

    def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        db = SessionLocal()
        try:
            service = AsyncContentGenerationService(db)

            # 1. 创建任务
            test_id = uuid.uuid4().hex[:8]
            task = ContentGenerationTask(
                task_id=f"task-recovery-{test_id}",
                account_id=49,
                topic="错误恢复测试",
                status="processing"
            )
            db.add(task)
            db.commit()

            # 2. 模拟失败
            handler = TaskResultHandler()
            handler.handle_failure(db, task, "网络超时")

            # 3. 验证失败状态
            db.refresh(task)
            assert task.status == 'failed'
            assert "网络超时" in task.error_message

            # 4. 重试任务（创建新任务）
            new_test_id = uuid.uuid4().hex[:8]
            new_task = ContentGenerationTask(
                task_id=f"task-retry-{new_test_id}",
                account_id=task.account_id,
                topic=task.topic,
                keywords=task.keywords,
                status="pending",
                retry_count=task.retry_count + 1
            )
            db.add(new_task)
            db.commit()

            # 5. 验证新任务
            assert new_task is not None
            assert new_task.status == 'pending'
            assert new_task.retry_count == 1

            # 清理
            db.delete(task)
            db.delete(new_task)
            db.commit()

        finally:
            db.close()
