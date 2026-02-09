"""
发布池扫描执行器单元测试

测试 PublishPoolScannerExecutor 的各项功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.executors.publish_pool_scanner_executor import PublishPoolScannerExecutor
from app.services.scheduler_service import TaskExecutionResult
from app.models.publisher import PublishPool
from app.models.content import Content
from app.models.account import Account


@pytest.fixture
def scanner_executor():
    """创建 PublishPoolScannerExecutor 实例"""
    return PublishPoolScannerExecutor()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_pending_tasks():
    """创建示例待发布任务"""
    now = datetime.now()

    task1 = Mock(spec=PublishPool)
    task1.id = 1
    task1.content_id = 101
    task1.priority = 10
    task1.scheduled_at = now - timedelta(minutes=10)
    task1.status = "pending"
    task1.retry_count = 0
    task1.max_retries = 3
    task1.added_at = now - timedelta(hours=1)
    task1.last_error = None

    task2 = Mock(spec=PublishPool)
    task2.id = 2
    task2.content_id = 102
    task2.priority = 8
    task2.scheduled_at = now - timedelta(minutes=5)
    task2.status = "pending"
    task2.retry_count = 0
    task2.max_retries = 3
    task2.added_at = now - timedelta(hours=2)
    task2.last_error = None

    task3 = Mock(spec=PublishPool)
    task3.id = 3
    task3.content_id = 103
    task3.priority = 5
    task3.scheduled_at = None  # 没有设定时间，立即发布
    task3.status = "pending"
    task3.retry_count = 0
    task3.max_retries = 3
    task3.added_at = now - timedelta(minutes=30)
    task3.last_error = None

    return [task1, task2, task3]


@pytest.fixture
def sample_content():
    """创建示例内容"""
    content = Mock(spec=Content)
    content.id = 101
    content.account_id = 1
    content.title = "Test Content"
    content.content = "Test content body"
    return content


@pytest.fixture
def sample_account():
    """创建示例账号"""
    account = Mock(spec=Account)
    account.id = 1
    account.name = "Test Account"
    account.wechat_app_id = "test_app_id"
    account.wechat_app_secret = "test_app_secret"
    return account


class TestPublishPoolScannerExecutor:
    """PublishPoolScannerExecutor 测试类"""

    def test_executor_type(self, scanner_executor):
        """测试执行器类型"""
        assert scanner_executor.executor_type == "publish_pool_scanner"

    def test_validate_params_default(self, scanner_executor):
        """测试默认参数验证"""
        # PublishPoolScannerExecutor 不需要特定参数
        # 任何参数都可以接受
        assert scanner_executor.validate_params({}) is True
        assert scanner_executor.validate_params({"max_batch_size": 5}) is True
        assert scanner_executor.validate_params({"check_future_tasks": True}) is True

    def test_get_pending_tasks_empty(self, scanner_executor, mock_db):
        """测试查询待发布任务（空结果）"""
        # 模拟查询返回空列表
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # 调用方法
        result = scanner_executor._get_pending_tasks(mock_db, max_batch_size=10)

        # 验证结果
        assert result == []
        mock_db.query.assert_called_once()

    def test_get_pending_tasks_with_results(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试查询待发布任务（有结果）"""
        # 模拟查询返回待发布任务
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_pending_tasks
        mock_db.query.return_value = mock_query

        # 调用方法
        result = scanner_executor._get_pending_tasks(mock_db, max_batch_size=10)

        # 验证结果
        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3

    def test_get_pending_tasks_priority_ordering(self, scanner_executor, mock_db):
        """测试优先级排序"""
        now = datetime.now()

        # 创建不同优先级的任务
        high_priority = Mock(spec=PublishPool)
        high_priority.id = 1
        high_priority.priority = 10
        high_priority.scheduled_at = now
        high_priority.added_at = now

        low_priority = Mock(spec=PublishPool)
        low_priority.id = 2
        low_priority.priority = 5
        low_priority.scheduled_at = now
        low_priority.added_at = now

        # 返回未排序的列表
        tasks = [low_priority, high_priority]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = tasks
        mock_db.query.return_value = mock_query

        # 调用方法
        result = scanner_executor._get_pending_tasks(mock_db, max_batch_size=10)

        # 验证调用了排序
        mock_query.order_by.assert_called_once()
        # order_by 应该接收多个排序条件
        order_by_call = mock_query.order_by.call_args
        assert len(order_by_call[0]) == 3  # 三个排序条件

    def test_get_pending_tasks_with_time_filter(self, scanner_executor, mock_db):
        """测试时间过滤（不检查未来任务）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # 调用方法，不检查未来任务
        scanner_executor._get_pending_tasks(mock_db, max_batch_size=10, check_future_tasks=False)

        # 验证调用了两次 filter（一次状态，一次时间）
        assert mock_query.filter.call_count == 2

    def test_get_pending_tasks_without_time_filter(self, scanner_executor, mock_db):
        """测试不进行时间过滤（检查未来任务）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # 调用方法，检查未来任务
        scanner_executor._get_pending_tasks(mock_db, max_batch_size=10, check_future_tasks=True)

        # 验证只调用了一次 filter（只有状态过滤）
        assert mock_query.filter.call_count == 1

    def test_get_pending_tasks_batch_size_limit(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试批量大小限制"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_pending_tasks
        mock_db.query.return_value = mock_query

        # 调用方法，限制批量大小为2
        scanner_executor._get_pending_tasks(mock_db, max_batch_size=2)

        # 验证调用了 limit
        mock_query.limit.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_execute_no_pending_tasks(self, scanner_executor, mock_db):
        """测试执行时没有待发布任务"""
        with patch.object(scanner_executor, '_get_pending_tasks', return_value=[]):
            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["scanned"] is True
            assert result.data["pending_count"] == 0
            assert result.data["published_count"] == 0
            assert result.data["failed_count"] == 0
            assert "没有待发布任务" in result.message

    @pytest.mark.asyncio
    async def test_execute_all_success(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试全部发布成功"""
        with patch.object(scanner_executor, '_get_pending_tasks', return_value=sample_pending_tasks), \
             patch('app.services.executors.publish_pool_scanner_executor.PublishingExecutor') as mock_executor_class:

            # Mock 发布执行器
            mock_executor = Mock()
            mock_executor.execute.return_value = TaskExecutionResult.success_result(
                message="发布成功",
                data={"log_id": 100}
            )
            mock_executor_class.return_value = mock_executor

            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["pending_count"] == 3
            assert result.data["published_count"] == 3
            assert result.data["failed_count"] == 0
            assert len(result.data["results"]) == 3

            # 验证所有任务都成功
            for item in result.data["results"]:
                assert item["success"] is True

    @pytest.mark.asyncio
    async def test_execute_partial_success(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试部分发布成功"""
        with patch.object(scanner_executor, '_get_pending_tasks', return_value=sample_pending_tasks), \
             patch('app.services.executors.publish_pool_scanner_executor.PublishingExecutor') as mock_executor_class:

            # Mock 发布执行器：第一个成功，第二个失败，第三个成功
            mock_executor = Mock()
            mock_executor.execute.side_effect = [
                TaskExecutionResult.success_result(message="发布成功"),
                TaskExecutionResult.failure_result(message="发布失败", error="API错误"),
                TaskExecutionResult.success_result(message="发布成功")
            ]
            mock_executor_class.return_value = mock_executor

            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["pending_count"] == 3
            assert result.data["published_count"] == 2
            assert result.data["failed_count"] == 1

            # 验证重试次数被更新
            assert sample_pending_tasks[1].retry_count == 1
            assert sample_pending_tasks[1].last_error == "发布失败"

    @pytest.mark.asyncio
    async def test_execute_all_failed(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试全部发布失败"""
        with patch.object(scanner_executor, '_get_pending_tasks', return_value=sample_pending_tasks), \
             patch('app.services.executors.publish_pool_scanner_executor.PublishingExecutor') as mock_executor_class:

            # Mock 发布执行器：所有都失败
            mock_executor = Mock()
            mock_executor.execute.return_value = TaskExecutionResult.failure_result(
                message="发布失败",
                error="网络错误"
            )
            mock_executor_class.return_value = mock_executor

            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True  # 扫描任务本身成功
            assert result.data["pending_count"] == 3
            assert result.data["published_count"] == 0
            assert result.data["failed_count"] == 3

            # 验证所有任务都失败
            for item in result.data["results"]:
                assert item["success"] is False

    @pytest.mark.asyncio
    async def test_execute_max_retries_exceeded(self, scanner_executor, mock_db):
        """测试超过最大重试次数的任务被跳过"""
        # 创建已达到最大重试次数的任务
        now = datetime.now()
        max_retries_task = Mock(spec=PublishPool)
        max_retries_task.id = 1
        max_retries_task.content_id = 101
        max_retries_task.priority = 10
        max_retries_task.scheduled_at = now
        max_retries_task.status = "pending"
        max_retries_task.retry_count = 3  # 已达到最大重试次数
        max_retries_task.max_retries = 3
        max_retries_task.last_error = "上次失败"

        with patch.object(scanner_executor, '_get_pending_tasks', return_value=[max_retries_task]):
            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["pending_count"] == 1
            assert result.data["published_count"] == 0
            assert result.data["failed_count"] == 1

            # 验证错误消息
            assert "超过最大重试次数" in result.data["results"][0]["error"]

    @pytest.mark.asyncio
    async def test_execute_with_exception(self, scanner_executor, mock_db, sample_pending_tasks):
        """测试执行过程中发生异常"""
        with patch.object(scanner_executor, '_get_pending_tasks', return_value=sample_pending_tasks), \
             patch('app.services.executors.publish_pool_scanner_executor.PublishingExecutor') as mock_executor_class:

            # Mock 发布执行器：抛出异常
            mock_executor = Mock()
            mock_executor.execute.side_effect = Exception("数据库连接断开")
            mock_executor_class.return_value = mock_executor

            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is True  # 扫描任务本身成功
            assert result.data["pending_count"] == 3
            assert result.data["published_count"] == 0
            assert result.data["failed_count"] == 3

            # 验证所有任务都标记为失败
            for item in result.data["results"]:
                assert item["success"] is False
                assert "数据库连接断开" in item["error"]

    @pytest.mark.asyncio
    async def test_execute_custom_batch_size(self, scanner_executor, mock_db):
        """测试自定义批量大小"""
        with patch.object(scanner_executor, '_get_pending_tasks') as mock_get_tasks:
            # 创建20个任务
            tasks = [Mock(id=i, content_id=i*100) for i in range(20)]
            for i, task in enumerate(tasks):
                task.retry_count = 0
                task.max_retries = 3
                task.priority = 5

            mock_get_tasks.return_value = tasks

            with patch('app.services.executors.publish_pool_scanner_executor.PublishingExecutor') as mock_executor_class:
                # Mock 所有发布都成功
                mock_executor = Mock()
                mock_executor.execute.return_value = TaskExecutionResult.success_result(
                    message="发布成功"
                )
                mock_executor_class.return_value = mock_executor

                # 执行任务，批量大小为5
                result = await scanner_executor.execute(
                    task_id=1,
                    task_params={"max_batch_size": 5},
                    db=mock_db
                )

                # 验证 _get_pending_tasks 被调用时使用了正确的批量大小
                mock_get_tasks.assert_called_once_with(mock_db, max_batch_size=5, check_future_tasks=False)

                # 验证只发布了5个任务
                assert result.data["pending_count"] == 5
                assert result.data["published_count"] == 5

    @pytest.mark.asyncio
    async def test_execute_check_future_tasks(self, scanner_executor, mock_db):
        """测试检查未来任务"""
        with patch.object(scanner_executor, '_get_pending_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = []

            # 执行任务，启用检查未来任务
            await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10, "check_future_tasks": True},
                db=mock_db
            )

            # 验证 _get_pending_tasks 被调用时使用了正确的参数
            mock_get_tasks.assert_called_once_with(
                mock_db,
                max_batch_size=10,
                check_future_tasks=True
            )

    @pytest.mark.asyncio
    async def test_execute_default_parameters(self, scanner_executor, mock_db):
        """测试使用默认参数"""
        with patch.object(scanner_executor, '_get_pending_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = []

            # 执行任务，不提供参数
            await scanner_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证使用了默认参数
            mock_get_tasks.assert_called_once_with(
                mock_db,
                max_batch_size=10,  # 默认批量大小
                check_future_tasks=False  # 默认不检查未来任务
            )

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, scanner_executor, mock_db):
        """测试数据库查询失败"""
        with patch.object(scanner_executor, '_get_pending_tasks', side_effect=Exception("数据库查询失败")):
            # 执行任务
            result = await scanner_executor.execute(
                task_id=1,
                task_params={"max_batch_size": 10},
                db=mock_db
            )

            # 验证结果
            assert result.success is False
            assert "数据库查询失败" in result.error
            assert "发布池扫描执行失败" in result.message

    def test_get_executor_info(self, scanner_executor):
        """测试获取执行器信息"""
        info = scanner_executor.get_executor_info()

        assert info["type"] == "publish_pool_scanner"
        assert info["class"] == "PublishPoolScannerExecutor"
        assert "module" in info
