"""
测试 Webhook 回调 URL 功能

测试内容：
1. 任务提交时是否正确生成回调 URL
2. 回调 URL 是否正确保存到数据库
3. CLI 命令是否包含 --callback-url 参数
4. Webhook 禁用时是否不生成回调 URL
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.async_content_generation_service import AsyncContentGenerationService
from app.models.content_generation_task import ContentGenerationTask
from app.core.config import settings
from app.core.exceptions import CreatorException


class TestWebhookCallbackIntegration:
    """Webhook 回调集成测试"""

    def setup_method(self):
        """测试前准备"""
        self.db = Mock()
        self.service = AsyncContentGenerationService(db=self.db)

    @patch('app.services.async_content_generation_service.subprocess.run')
    @patch('app.services.async_content_generation_service.settings')
    def test_submit_task_with_webhook_enabled(
        self,
        mock_settings,
        mock_subprocess_run
    ):
        """测试：启用 Webhook 时提交任务"""
        # 配置 mock
        mock_settings.WEBHOOK_ENABLED = True
        mock_settings.WEBHOOK_CALLBACK_BASE_URL = "https://example.com"
        mock_settings.CREATOR_CLI_PATH = "/usr/bin/content-creator"
        mock_settings.HOST = "0.0.0.0"
        mock_settings.PORT = 18010

        mock_subprocess_run.return_value = MagicMock(
            stdout="Task submitted",
            stderr=""
        )

        # 创建测试任务
        task = ContentGenerationTask(
            id=1,
            task_id="test-task-123",
            account_id=1,
            topic="测试选题",
            status="pending",
            requirements="测试要求",
            tone="professional",
            keywords="测试,关键词"
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 执行提交
        self.service._submit_to_creator(task)

        # 验证回调 URL 已设置
        assert task.callback_url is not None
        assert task.callback_url == "https://example.com/api/v1/content/callback/test-task-123"

        # 验证 CLI 命令包含回调 URL
        call_args = mock_subprocess_run.call_args
        command = call_args[0][0]
        assert "--callback-url" in command
        callback_url_index = command.index("--callback-url")
        assert command[callback_url_index + 1] == task.callback_url

        print("✓ 测试通过：Webhook 启用时正确生成回调 URL")

    @patch('app.services.async_content_generation_service.subprocess.run')
    @patch('app.services.async_content_generation_service.settings')
    def test_submit_task_with_webhook_disabled(
        self,
        mock_settings,
        mock_subprocess_run
    ):
        """测试：禁用 Webhook 时提交任务"""
        # 配置 mock
        mock_settings.WEBHOOK_ENABLED = False
        mock_settings.CREATOR_CLI_PATH = "/usr/bin/content-creator"

        mock_subprocess_run.return_value = MagicMock(
            stdout="Task submitted",
            stderr=""
        )

        # 创建测试任务
        task = ContentGenerationTask(
            id=2,
            task_id="test-task-456",
            account_id=1,
            topic="测试选题",
            status="pending"
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 执行提交
        self.service._submit_to_creator(task)

        # 验证回调 URL 未设置
        assert task.callback_url is None

        # 验证 CLI 命令不包含回调 URL
        call_args = mock_subprocess_run.call_args
        command = call_args[0][0]
        assert "--callback-url" not in command

        print("✓ 测试通过：Webhook 禁用时不生成回调 URL")

    @patch('app.services.async_content_generation_service.subprocess.run')
    @patch('app.services.async_content_generation_service.settings')
    def test_submit_task_with_default_base_url(
        self,
        mock_settings,
        mock_subprocess_run
    ):
        """测试：未配置 WEBHOOK_CALLBACK_BASE_URL 时使用默认值"""
        # 配置 mock
        mock_settings.WEBHOOK_ENABLED = True
        mock_settings.WEBHOOK_CALLBACK_BASE_URL = None
        mock_settings.CREATOR_CLI_PATH = "/usr/bin/content-creator"
        mock_settings.HOST = "localhost"
        mock_settings.PORT = 18010

        mock_subprocess_run.return_value = MagicMock(
            stdout="Task submitted",
            stderr=""
        )

        # 创建测试任务
        task = ContentGenerationTask(
            id=3,
            task_id="test-task-789",
            account_id=1,
            topic="测试选题",
            status="pending"
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 执行提交
        self.service._submit_to_creator(task)

        # 验证使用默认值构造回调 URL
        assert task.callback_url is not None
        assert task.callback_url == "http://localhost:18010/api/v1/content/callback/test-task-789"

        print("✓ 测试通过：未配置 WEBHOOK_CALLBACK_BASE_URL 时使用默认值")

    def test_get_task_status_includes_callback_url(self):
        """测试：get_task_status 返回结果包含 callback_url"""
        # 创建测试任务
        task = ContentGenerationTask(
            id=4,
            task_id="test-task-status",
            account_id=1,
            topic="测试选题",
            status="pending",
            callback_url="https://example.com/api/v1/content/callback/test-task-status",
            created_at=datetime.utcnow(),
            submitted_at=datetime.utcnow()
        )

        self.db.query.return_value.filter_by.return_value.first.return_value = task

        # 执行查询
        status = self.service.get_task_status("test-task-status")

        # 验证返回结果包含 callback_url
        assert status is not None
        assert "callback_url" in status
        assert status["callback_url"] == "https://example.com/api/v1/content/callback/test-task-status"

        print("✓ 测试通过：get_task_status 正确返回 callback_url")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Webhook 回调 URL 功能测试")
    print("=" * 60)
    print()

    test_suite = TestWebhookCallbackIntegration()

    try:
        test_suite.setup_method()
        test_suite.test_submit_task_with_webhook_enabled()

        test_suite.setup_method()
        test_suite.test_submit_task_with_webhook_disabled()

        test_suite.setup_method()
        test_suite.test_submit_task_with_default_base_url()

        test_suite.setup_method()
        test_suite.test_get_task_status_includes_callback_url()

        print()
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ 测试失败: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
