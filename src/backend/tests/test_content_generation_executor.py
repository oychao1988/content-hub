"""
内容生成任务执行器单元测试
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.executors.content_generation_executor import ContentGenerationExecutor
from app.services.scheduler_service import TaskExecutionResult


class TestContentGenerationExecutor:
    """内容生成执行器测试类"""

    def test_executor_type(self):
        """测试执行器类型"""
        executor = ContentGenerationExecutor()
        assert executor.executor_type == "content_generation"

    def test_validate_params_success(self):
        """测试参数验证成功"""
        executor = ContentGenerationExecutor()
        params = {
            "account_id": 1,
            "topic": "测试选题"
        }
        assert executor.validate_params(params) is True

    def test_validate_params_missing_account_id(self):
        """测试缺少 account_id"""
        executor = ContentGenerationExecutor()
        params = {
            "topic": "测试选题"
        }
        assert executor.validate_params(params) is False

    def test_validate_params_invalid_account_id(self):
        """测试无效的 account_id"""
        executor = ContentGenerationExecutor()

        # 负数
        params1 = {"account_id": -1, "topic": "测试"}
        assert executor.validate_params(params1) is False

        # 零
        params2 = {"account_id": 0, "topic": "测试"}
        assert executor.validate_params(params2) is False

        # 非整数
        params3 = {"account_id": "abc", "topic": "测试"}
        assert executor.validate_params(params3) is False

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试执行成功"""
        # Mock 数据库会话
        db = Mock(spec=Session)

        # Mock content_creator_service
        with patch('app.services.executors.content_generation_executor.content_creator_service') as mock_creator:
            # Mock 返回结果
            mock_creator.create_content.return_value = {
                "content": "# 测试标题\n\n这是测试内容。",
                "images": ["data/images/test.jpg"],
                "task_id": "test-task-123",
                "quality_score": 8.5,
                "quality_passed": True
            }

            # 创建执行器
            executor = ContentGenerationExecutor()

            # 执行任务
            result = await executor.execute(
                task_id=1,
                task_params={
                    "account_id": 1,
                    "topic": "测试选题",
                    "title": "测试标题"
                },
                db=db
            )

            # 验证结果
            assert result.success is True
            assert "content_id" in result.data
            assert result.data["title"] == "测试标题"
            assert result.data["word_count"] > 0
            assert result.data["images_count"] == 1

            # 验证数据库操作
            assert db.add.called
            assert db.commit.called

    @pytest.mark.asyncio
    async def test_execute_creator_cli_failure(self):
        """测试 content-creator CLI 调用失败"""
        db = Mock(spec=Session)

        # Mock content_creator_service 抛出异常
        with patch('app.services.executors.content_generation_executor.content_creator_service') as mock_creator:
            mock_creator.create_content.side_effect = Exception("CLI 调用失败")

            executor = ContentGenerationExecutor()

            result = await executor.execute(
                task_id=1,
                task_params={
                    "account_id": 1,
                    "topic": "测试选题"
                },
                db=db
            )

            assert result.success is False
            assert "CLI 调用失败" in result.error

    @pytest.mark.asyncio
    async def test_execute_empty_content(self):
        """测试生成的内容为空"""
        db = Mock(spec=Session)

        with patch('app.services.executors.content_generation_executor.content_creator_service') as mock_creator:
            # Mock 返回空内容
            mock_creator.create_content.return_value = {
                "content": "",
                "images": []
            }

            executor = ContentGenerationExecutor()

            result = await executor.execute(
                task_id=1,
                task_params={
                    "account_id": 1,
                    "topic": "测试选题"
                },
                db=db
            )

            assert result.success is False
            assert "EmptyContent" in result.error

    @pytest.mark.asyncio
    async def test_execute_database_failure(self):
        """测试数据库保存失败"""
        db = Mock(spec=Session)
        db.commit.side_effect = Exception("数据库错误")

        with patch('app.services.executors.content_generation_executor.content_creator_service') as mock_creator:
            mock_creator.create_content.return_value = {
                "content": "# 测试\n\n内容",
                "images": []
            }

            executor = ContentGenerationExecutor()

            result = await executor.execute(
                task_id=1,
                task_params={
                    "account_id": 1,
                    "topic": "测试"
                },
                db=db
            )

            assert result.success is False
            assert "数据库" in result.message

    def test_get_executor_info(self):
        """测试获取执行器信息"""
        executor = ContentGenerationExecutor()
        info = executor.get_executor_info()

        assert info["type"] == "content_generation"
        assert info["class"] == "ContentGenerationExecutor"
        assert "module" in info
