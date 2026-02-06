"""
发布任务执行器单元测试

测试 PublishingExecutor 的各项功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.executors.publishing_executor import PublishingExecutor
from app.services.scheduler_service import TaskExecutionResult
from app.models.publisher import PublishPool
from app.models.content import Content
from app.models.account import Account


@pytest.fixture
def publishing_executor():
    """创建 PublishingExecutor 实例"""
    return PublishingExecutor()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_pool_entries():
    """创建示例发布池条目"""
    now = datetime.utcnow()

    entry1 = Mock(spec=PublishPool)
    entry1.id = 1
    entry1.content_id = 101
    entry1.priority = 1
    entry1.scheduled_at = now - timedelta(minutes=5)
    entry1.status = "pending"
    entry1.retry_count = 0
    entry1.max_retries = 3

    entry2 = Mock(spec=PublishPool)
    entry2.id = 2
    entry2.content_id = 102
    entry2.priority = 2
    entry2.scheduled_at = now - timedelta(minutes=3)
    entry2.status = "pending"
    entry2.retry_count = 0
    entry2.max_retries = 3

    return [entry1, entry2]


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


class TestPublishingExecutor:
    """PublishingExecutor 测试类"""

    def test_executor_type(self, publishing_executor):
        """测试执行器类型"""
        assert publishing_executor.executor_type == "publishing"

    def test_validate_params(self, publishing_executor):
        """测试参数验证"""
        # PublishingExecutor 不需要特定参数
        assert publishing_executor.validate_params({}) is True
        assert publishing_executor.validate_params({"any": "params"}) is True

    @pytest.mark.asyncio
    async def test_execute_empty_pool(self, publishing_executor, mock_db):
        """测试执行时发布池为空"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service:
            # 模拟没有待发布内容
            mock_pool_service.get_pending_entries.return_value = []

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["total_count"] == 0
            assert result.data["success_count"] == 0
            assert result.data["failed_count"] == 0
            assert "No pending entries" in result.message

    @pytest.mark.asyncio
    async def test_execute_success(self, publishing_executor, mock_db, sample_pool_entries, sample_content, sample_account):
        """测试成功发布"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
             patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

            # 模拟查询返回待发布内容
            mock_pool_service.get_pending_entries.return_value = sample_pool_entries

            # 模拟查询返回内容和账号（每个entry需要查询content和account）
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_content, sample_account,  # 第一个entry
                sample_content, sample_account   # 第二个entry
            ]

            # 模拟发布成功（调用两次）
            mock_publisher_service.manual_publish.side_effect = [
                {"success": True, "log_id": 100, "media_id": "test_media_id"},
                {"success": True, "log_id": 101, "media_id": "test_media_id_2"}
            ]

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["total_count"] == 2
            assert result.data["success_count"] == 2
            assert result.data["failed_count"] == 0
            assert len(result.data["results"]) == 2

            # 验证调用
            assert mock_pool_service.start_publishing.call_count == 2
            assert mock_publisher_service.manual_publish.call_count == 2
            assert mock_pool_service.complete_publishing.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_partial_failure(self, publishing_executor, mock_db, sample_pool_entries, sample_content, sample_account):
        """测试部分发布失败"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
             patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

            # 模拟查询返回待发布内容
            mock_pool_service.get_pending_entries.return_value = sample_pool_entries

            # 模拟查询返回内容和账号（每个entry需要查询content和account）
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_content, sample_account,  # 第一个entry
                sample_content, sample_account   # 第二个entry
            ]

            # 模拟第一次成功，第二次失败
            mock_publisher_service.manual_publish.side_effect = [
                {"success": True, "log_id": 100, "media_id": "test_media_id"},
                {"success": False, "error": "Publish failed"}
            ]

            # 模拟失败处理的重试逻辑
            mock_pool_entry = Mock()
            mock_pool_entry.retry_count = 1
            mock_pool_entry.max_retries = 3
            mock_pool_service.fail_publishing.return_value = mock_pool_entry

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True  # 整体任务成功（即使有部分失败）
            assert result.data["total_count"] == 2
            assert result.data["success_count"] == 1
            assert result.data["failed_count"] == 1
            assert len(result.data["results"]) == 2

            # 验证调用
            assert mock_pool_service.start_publishing.call_count == 2
            assert mock_publisher_service.manual_publish.call_count == 2
            assert mock_pool_service.complete_publishing.call_count == 1
            assert mock_pool_service.fail_publishing.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_content_not_found(self, publishing_executor, mock_db, sample_pool_entries):
        """测试内容不存在"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service:
            # 模拟查询返回待发布内容
            mock_pool_service.get_pending_entries.return_value = sample_pool_entries

            # 模拟查询不到内容（所有查询都返回None）
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # 模拟 fail_publishing 不抛出异常
            mock_pool_service.fail_publishing.return_value = None

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["total_count"] == 2
            assert result.data["success_count"] == 0
            assert result.data["failed_count"] == 2

            # 验证所有条目都标记为失败
            for item in result.data["results"]:
                assert item["status"] in ["failed", "error"]

            # 验证调用
            assert mock_pool_service.fail_publishing.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, publishing_executor, mock_db, sample_pool_entries, sample_content, sample_account):
        """测试重试机制"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
             patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

            # 模拟查询返回待发布内容
            mock_pool_service.get_pending_entries.return_value = sample_pool_entries

            # 模拟查询返回内容和账号（每个entry需要查询content和account）
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_content, sample_account,  # 第一个entry
                sample_content, sample_account   # 第二个entry
            ]

            # 模拟发布失败（调用两次）
            mock_publisher_service.manual_publish.side_effect = [
                {"success": False, "error": "Publish failed"},
                {"success": False, "error": "Publish failed"}
            ]

            # 创建模拟的 pool_entry 用于重试检查
            mock_pool_entry = Mock()
            mock_pool_entry.retry_count = 1
            mock_pool_entry.max_retries = 3
            mock_pool_service.fail_publishing.return_value = mock_pool_entry

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["failed_count"] == 2

            # 验证调用重试逻辑
            assert mock_pool_service.fail_publishing.call_count == 2
            assert mock_pool_service.retry_publishing.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_max_retries_exceeded(self, publishing_executor, mock_db, sample_pool_entries, sample_content, sample_account):
        """测试超过最大重试次数"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
             patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

            # 模拟查询返回待发布内容
            mock_pool_service.get_pending_entries.return_value = sample_pool_entries

            # 模拟查询返回内容和账号（每个entry需要查询content和account）
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_content, sample_account,  # 第一个entry
                sample_content, sample_account   # 第二个entry
            ]

            # 模拟发布失败（调用两次）
            mock_publisher_service.manual_publish.side_effect = [
                {"success": False, "error": "Publish failed"},
                {"success": False, "error": "Publish failed"}
            ]

            # 创建模拟的 pool_entry，已达到最大重试次数
            mock_pool_entry = Mock()
            mock_pool_entry.retry_count = 3
            mock_pool_entry.max_retries = 3
            mock_pool_service.fail_publishing.return_value = mock_pool_entry

            # 执行任务
            result = await publishing_executor.execute(
                task_id=1,
                task_params={},
                db=mock_db
            )

            # 验证结果
            assert result.success is True
            assert result.data["failed_count"] == 2

            # 验证不会调用重试
            assert mock_pool_service.fail_publishing.call_count == 2
            assert mock_pool_service.retry_publishing.call_count == 0

    def test_handle_publish_failure(self, publishing_executor, mock_db):
        """测试处理发布失败"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service:
            # 创建模拟的 pool_entry
            mock_pool_entry = Mock()
            mock_pool_entry.retry_count = 1
            mock_pool_entry.max_retries = 3
            mock_pool_service.fail_publishing.return_value = mock_pool_entry

            # 调用处理失败
            publishing_executor._handle_publish_failure(mock_db, 1, "Test error")

            # 验证调用
            mock_pool_service.fail_publishing.assert_called_once_with(mock_db, 1, "Test error")
            mock_pool_service.retry_publishing.assert_called_once_with(mock_db, 1)

    def test_handle_publish_failure_max_retries(self, publishing_executor, mock_db):
        """测试处理发布失败（达到最大重试次数）"""
        with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service:
            # 创建模拟的 pool_entry，已达到最大重试次数
            mock_pool_entry = Mock()
            mock_pool_entry.retry_count = 3
            mock_pool_entry.max_retries = 3
            mock_pool_service.fail_publishing.return_value = mock_pool_entry

            # 调用处理失败
            publishing_executor._handle_publish_failure(mock_db, 1, "Test error")

            # 验证调用
            mock_pool_service.fail_publishing.assert_called_once_with(mock_db, 1, "Test error")
            # 不会调用重试
            mock_pool_service.retry_publishing.assert_not_called()
