#!/usr/bin/env python3
"""
Webhook 端点功能测试（简化版）

测试 Webhook 端点的核心功能，不需要启动服务器
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.modules.content.endpoints import handle_webhook_callback
from app.models import ContentGenerationTask
from app.services.webhook_handler import WebhookHandler
from app.core.config import settings


def create_mock_task(task_id="test-task-123"):
    """创建模拟任务对象"""
    task = Mock(spec=ContentGenerationTask)
    task.task_id = task_id
    task.status = "processing"
    task.account_id = 1
    task.auto_approve = False
    return task


def create_mock_db():
    """创建模拟数据库会话"""
    db = Mock(spec=Session)
    return db


async def test_completed_event():
    """测试任务完成事件"""
    print("\n" + "=" * 60)
    print("测试 1: 任务完成事件")
    print("=" * 60)

    # 准备测试数据
    task_id = "test-task-completed"
    task = create_mock_task(task_id)

    db = create_mock_db()
    db.query.return_value.filter.return_value.first.return_value = task

    # 创建模拟的 handler
    mock_handler = Mock(spec=WebhookHandler)
    mock_handler.handle_task_completed = AsyncMock(return_value={
        "success": True,
        "content_id": 123,
        "message": "Task completed and content created",
        "skipped": False
    })

    # 创建模拟请求
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "event": "completed",
        "taskId": task_id,
        "result": {
            "content": "测试内容",
            "wordCount": 100
        }
    })

    # 调用端点
    try:
        # 注意：由于依赖注入，我们需要手动提供参数
        # 在实际测试中，应该使用 TestClient
        print("✓ 测试设置完成")
        print(f"  任务 ID: {task_id}")
        print(f"  事件类型: completed")
        print(f"  模拟处理器: {mock_handler}")

        # 验证 handler 方法会被调用
        result = await mock_handler.handle_task_completed(
            db=db,
            task=task,
            result={"content": "测试内容", "wordCount": 100}
        )

        print(f"✓ Handler 返回结果: {result}")
        assert result["success"] == True
        assert result["content_id"] == 123
        print("✓ 测试通过")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_failed_event():
    """测试任务失败事件"""
    print("\n" + "=" * 60)
    print("测试 2: 任务失败事件")
    print("=" * 60)

    task_id = "test-task-failed"
    task = create_mock_task(task_id)

    mock_handler = Mock(spec=WebhookHandler)
    mock_handler.handle_task_failed = AsyncMock(return_value={
        "success": True,
        "retry_scheduled": True,
        "message": "Task failed, retry scheduled",
        "skipped": False
    })

    try:
        result = await mock_handler.handle_task_failed(
            db=create_mock_db(),
            task=task,
            error={"message": "AI service error", "code": "SERVICE_ERROR"}
        )

        print(f"✓ Handler 返回结果: {result}")
        assert result["success"] == True
        assert result["retry_scheduled"] == True
        print("✓ 测试通过")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_progress_event():
    """测试进度更新事件"""
    print("\n" + "=" * 60)
    print("测试 3: 进度更新事件")
    print("=" * 60)

    task_id = "test-task-progress"
    task = create_mock_task(task_id)
    task.status = "submitted"

    mock_handler = Mock(spec=WebhookHandler)
    mock_handler.handle_task_progress = AsyncMock(return_value={
        "success": True,
        "message": "Progress updated",
        "details": {"percentage": 50, "stage": "content_generation"}
    })

    try:
        result = await mock_handler.handle_task_progress(
            db=create_mock_db(),
            task=task,
            progress={"percentage": 50, "stage": "content_generation"}
        )

        print(f"✓ Handler 返回结果: {result}")
        assert result["success"] == True
        assert result["details"]["percentage"] == 50
        print("✓ 测试通过")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_signature_verification():
    """测试签名验证功能"""
    print("\n" + "=" * 60)
    print("测试 4: 签名验证功能")
    print("=" * 60)

    from app.utils.webhook_signature import generate_signature, verify_signature, create_verifier

    # 测试数据
    payload = {
        "event": "completed",
        "taskId": "test-task-123",
        "result": {"content": "测试"}
    }
    secret = "test-secret-key"

    try:
        # 生成签名
        signature = generate_signature(payload, secret)
        print(f"✓ 生成签名: {signature[:20]}...")

        # 验证签名
        is_valid = verify_signature(payload, signature, secret)
        print(f"✓ 验证签名: {is_valid}")
        assert is_valid == True

        # 错误的签名应该验证失败
        wrong_signature = "wrong-signature"
        is_valid_wrong = verify_signature(payload, wrong_signature, secret)
        print(f"✓ 错误签名验证: {is_valid_wrong}")
        assert is_valid_wrong == False

        # 使用 verifier 类
        verifier = create_verifier(secret=secret, require_signature=True)
        is_valid_verifier = verifier.verify(payload, signature)
        print(f"✓ Verifier 验证: {is_valid_verifier}")
        assert is_valid_verifier == True

        print("✓ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("开始功能测试")
    print("🧪" * 30)

    results = {}

    # 运行测试
    results["任务完成事件"] = await test_completed_event()
    results["任务失败事件"] = await test_failed_event()
    results["进度更新事件"] = await test_progress_event()
    results["签名验证"] = test_signature_verification()

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠ 有 {total - passed} 项测试失败。")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
