#!/usr/bin/env python3
"""
测试 Webhook 端点

用于验证 Webhook 回调端点的功能，包括：
1. 端点是否正确注册
2. 签名验证是否正常工作
3. 三种事件类型是否都能正确处理
4. 错误处理是否完整
5. 幂等性是否得到保证
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.db.sql_db import Base
from app.models import ContentGenerationTask, Account, WritingStyle
from app.core.config import settings
from app.utils.webhook_signature import generate_signature


# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test_webhook.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 创建测试账号
    account = Account(
        name="测试账号",
        platform="weixin_mp",
        app_id="test_app_id",
        status="active"
    )
    db.add(account)
    db.flush()

    # 创建测试写作风格
    style = WritingStyle(
        name="测试风格",
        description="用于测试的写作风格",
        tone="professional",
        target_audience="developers"
    )
    db.add(style)
    db.flush()

    # 创建测试任务
    task = ContentGenerationTask(
        task_id="test-task-123",
        account_id=account.id,
        topic="测试选题",
        keywords="测试,关键词",
        status="processing",
        auto_approve=False
    )
    db.add(task)
    db.commit()

    return db, task.id


def teardown_test_db(db):
    """清理测试数据库"""
    db.close()
    Base.metadata.drop_all(bind=engine)


def generate_test_signature(payload: dict) -> str:
    """生成测试签名"""
    if settings.WEBHOOK_SECRET_KEY:
        return generate_signature(payload, settings.WEBHOOK_SECRET_KEY)
    return ""


async def test_webhook_endpoint():
    """测试 Webhook 端点"""
    print("=" * 60)
    print("开始测试 Webhook 端点")
    print("=" * 60)

    # 设置测试数据库
    db, _ = setup_test_db()

    try:
        # 创建异步客户端
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            task_id = "test-task-123"

            # 测试 1: 任务完成事件
            print("\n[测试 1] 任务完成事件")
            completed_payload = {
                "event": "completed",
                "taskId": task_id,
                "workflowType": "content-creator",
                "status": "completed",
                "timestamp": "2026-02-09T12:00:00Z",
                "metadata": {
                    "topic": "测试选题",
                    "requirements": "测试要求"
                },
                "result": {
                    "content": "# 测试文章内容\n\n这是一篇测试文章。",
                    "htmlContent": "<h1>测试文章内容</h1><p>这是一篇测试文章。</p>",
                    "images": [],
                    "qualityScore": 8.5,
                    "wordCount": 10
                }
            }

            # 生成签名（如果配置了密钥）
            signature = generate_test_signature(completed_payload)
            headers = {"Content-Type": "application/json"}
            if signature:
                headers["X-Webhook-Signature"] = signature

            response = await client.post(
                f"/api/v1/content/callback/{task_id}",
                json=completed_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.json()["success"] == True, "Expected success=True"
            print("✓ 测试通过")

            # 测试 2: 任务失败事件
            print("\n[测试 2] 任务失败事件")

            # 创建新任务用于测试失败场景
            task2 = ContentGenerationTask(
                task_id="test-task-456",
                account_id=1,
                topic="测试失败",
                keywords="失败",
                status="processing",
                auto_approve=False
            )
            db.add(task2)
            db.commit()

            failed_payload = {
                "event": "failed",
                "taskId": "test-task-456",
                "workflowType": "content-creator",
                "status": "failed",
                "timestamp": "2026-02-09T12:00:00Z",
                "error": {
                    "message": "生成失败：无法连接到 AI 服务",
                    "code": "AI_SERVICE_ERROR",
                    "type": "ServiceError"
                }
            }

            signature = generate_test_signature(failed_payload)
            headers = {"Content-Type": "application/json"}
            if signature:
                headers["X-Webhook-Signature"] = signature

            response = await client.post(
                "/api/v1/content/callback/test-task-456",
                json=failed_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.json()["success"] == True, "Expected success=True"
            print("✓ 测试通过")

            # 测试 3: 任务进度更新事件
            print("\n[测试 3] 任务进度更新事件")

            task3 = ContentGenerationTask(
                task_id="test-task-789",
                account_id=1,
                topic="测试进度",
                keywords="进度",
                status="submitted",
                auto_approve=False
            )
            db.add(task3)
            db.commit()

            progress_payload = {
                "event": "progress",
                "taskId": "test-task-789",
                "workflowType": "content-creator",
                "status": "processing",
                "timestamp": "2026-02-09T12:00:00Z",
                "progress": {
                    "percentage": 50,
                    "message": "正在生成内容",
                    "stage": "content_generation"
                }
            }

            signature = generate_test_signature(progress_payload)
            headers = {"Content-Type": "application/json"}
            if signature:
                headers["X-Webhook-Signature"] = signature

            response = await client.post(
                "/api/v1/content/callback/test-task-789",
                json=progress_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.json()["success"] == True, "Expected success=True"
            print("✓ 测试通过")

            # 测试 4: 任务不存在
            print("\n[测试 4] 任务不存在（404）")

            response = await client.post(
                "/api/v1/content/callback/non-existent-task",
                json=completed_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 404, f"Expected 404, got {response.status_code}"
            print("✓ 测试通过")

            # 测试 5: 幂等性检查
            print("\n[测试 5] 幂等性检查（重复处理已完成任务）")

            # 再次发送完成事件给 test-task-123（已经处理过了）
            response = await client.post(
                f"/api/v1/content/callback/{task_id}",
                json=completed_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.json()["success"] == True, "Expected success=True"
            # 检查是否跳过了处理
            assert "already" in response.json()["message"].lower() or "processed" in response.json()["message"].lower(), \
                "Expected idempotent response"
            print("✓ 测试通过（幂等性得到保证）")

            # 测试 6: 缺少事件类型
            print("\n[测试 6] 缺少事件类型（400）")

            invalid_payload = {
                "taskId": "test-task-123",
                "status": "completed"
            }

            response = await client.post(
                "/api/v1/content/callback/test-task-123",
                json=invalid_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print("✓ 测试通过")

            # 测试 7: 未知事件类型
            print("\n[测试 7] 未知事件类型（400）")

            unknown_event_payload = {
                "event": "unknown_event",
                "taskId": "test-task-123",
                "status": "unknown"
            }

            response = await client.post(
                "/api/v1/content/callback/test-task-123",
                json=unknown_event_payload,
                headers=headers
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print("✓ 测试通过")

        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)

    finally:
        # 清理测试数据库
        teardown_test_db(db)


if __name__ == "__main__":
    asyncio.run(test_webhook_endpoint())
