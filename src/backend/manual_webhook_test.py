#!/usr/bin/env python3
"""
手动测试 Webhook 端点

用于快速测试 Webhook 端点的功能，无需启动 content-creator 服务。

使用方法：
1. 确保 ContentHub 服务已启动（python main.py）
2. 运行此脚本：python manual_webhook_test.py
3. 查看测试结果
"""
import requests
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.webhook_signature import generate_signature
from app.core.config import settings

# 配置
BASE_URL = "http://localhost:18010"
WEBHOOK_URL = f"{BASE_URL}/api/v1/content/callback"


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_completed_event():
    """测试任务完成事件"""
    print_section("测试 1: 任务完成事件")

    # 首先创建一个测试任务
    task_id = "manual-test-completed-001"

    # 准备回调数据
    callback_data = {
        "event": "completed",
        "taskId": task_id,
        "workflowType": "content-creator",
        "status": "completed",
        "timestamp": "2026-02-09T12:00:00Z",
        "metadata": {
            "topic": "手动测试 - 任务完成",
            "requirements": "用于测试 Webhook 端点"
        },
        "result": {
            "content": "# 手动测试文章\n\n这是一篇用于测试 Webhook 端点的文章。\n\n## 功能验证\n\n- 任务完成事件\n- Content 创建\n- 数据库更新",
            "htmlContent": "<h1>手动测试文章</h1><p>这是一篇用于测试 Webhook 端点的文章。</p>",
            "images": [],
            "qualityScore": 9.0,
            "wordCount": 50
        }
    }

    # 生成签名
    headers = {"Content-Type": "application/json"}
    if settings.WEBHOOK_SECRET_KEY:
        signature = generate_signature(callback_data, settings.WEBHOOK_SECRET_KEY)
        headers["X-Webhook-Signature"] = signature
        print(f"✓ 生成签名: {signature[:30]}...")

    # 发送请求
    print(f"\n发送请求到: {WEBHOOK_URL}/{task_id}")
    print(f"事件类型: {callback_data['event']}")

    try:
        response = requests.post(
            f"{WEBHOOK_URL}/{task_id}",
            json=callback_data,
            headers=headers,
            timeout=10
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✓ 测试通过")
            return True
        else:
            print(f"\n❌ 测试失败: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败: 请确保 ContentHub 服务已启动")
        print("   启动命令: python main.py")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def test_failed_event():
    """测试任务失败事件"""
    print_section("测试 2: 任务失败事件")

    task_id = "manual-test-failed-002"

    callback_data = {
        "event": "failed",
        "taskId": task_id,
        "workflowType": "content-creator",
        "status": "failed",
        "timestamp": "2026-02-09T12:00:00Z",
        "error": {
            "message": "AI 服务暂时不可用",
            "code": "AI_SERVICE_UNAVAILABLE",
            "type": "ServiceError"
        }
    }

    headers = {"Content-Type": "application/json"}
    if settings.WEBHOOK_SECRET_KEY:
        signature = generate_signature(callback_data, settings.WEBHOOK_SECRET_KEY)
        headers["X-Webhook-Signature"] = signature

    print(f"\n发送请求到: {WEBHOOK_URL}/{task_id}")
    print(f"事件类型: {callback_data['event']}")

    try:
        response = requests.post(
            f"{WEBHOOK_URL}/{task_id}",
            json=callback_data,
            headers=headers,
            timeout=10
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✓ 测试通过")
            return True
        else:
            print(f"\n❌ 测试失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def test_progress_event():
    """测试进度更新事件"""
    print_section("测试 3: 进度更新事件")

    task_id = "manual-test-progress-003"

    callback_data = {
        "event": "progress",
        "taskId": task_id,
        "workflowType": "content-creator",
        "status": "processing",
        "timestamp": "2026-02-09T12:00:00Z",
        "progress": {
            "percentage": 75,
            "message": "正在生成文章内容",
            "stage": "content_generation"
        }
    }

    headers = {"Content-Type": "application/json"}
    if settings.WEBHOOK_SECRET_KEY:
        signature = generate_signature(callback_data, settings.WEBHOOK_SECRET_KEY)
        headers["X-Webhook-Signature"] = signature

    print(f"\n发送请求到: {WEBHOOK_URL}/{task_id}")
    print(f"事件类型: {callback_data['event']}")
    print(f"进度: {callback_data['progress']['percentage']}%")

    try:
        response = requests.post(
            f"{WEBHOOK_URL}/{task_id}",
            json=callback_data,
            headers=headers,
            timeout=10
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✓ 测试通过")
            return True
        else:
            print(f"\n❌ 测试失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def test_error_cases():
    """测试错误场景"""
    print_section("测试 4: 错误场景")

    results = []

    # 4.1 任务不存在
    print("\n[4.1] 测试任务不存在（404）")
    response = requests.post(
        f"{WEBHOOK_URL}/non-existent-task",
        json={"event": "completed", "taskId": "non-existent-task"},
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 404:
        print("✓ 正确返回 404")
        results.append(True)
    else:
        print(f"❌ 期望 404，实际 {response.status_code}")
        results.append(False)

    # 4.2 缺少事件类型
    print("\n[4.2] 测试缺少事件类型（400）")
    response = requests.post(
        f"{WEBHOOK_URL}/test-task",
        json={"taskId": "test-task"},
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 400:
        print("✓ 正确返回 400")
        results.append(True)
    else:
        print(f"❌ 期望 400，实际 {response.status_code}")
        results.append(False)

    # 4.3 未知事件类型
    print("\n[4.3] 测试未知事件类型（400）")
    response = requests.post(
        f"{WEBHOOK_URL}/test-task",
        json={"event": "unknown_event", "taskId": "test-task"},
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 400:
        print("✓ 正确返回 400")
        results.append(True)
    else:
        print(f"❌ 期望 400，实际 {response.status_code}")
        results.append(False)

    return all(results)


def main():
    """主函数"""
    print("\n" + "🧪" * 30)
    print("Webhook 端点手动测试")
    print("🧪" * 30)

    print(f"\n配置信息:")
    print(f"  服务地址: {BASE_URL}")
    print(f"  Webhook URL: {WEBHOOK_URL}")
    print(f"  签名验证: {'启用' if settings.WEBHOOK_REQUIRE_SIGNATURE else '禁用'}")
    print(f"  签名密钥: {'已配置' if settings.WEBHOOK_SECRET_KEY else '未配置'}")

    results = {}

    # 运行测试
    results["任务完成事件"] = test_completed_event()
    results["任务失败事件"] = test_failed_event()
    results["进度更新事件"] = test_progress_event()
    results["错误场景"] = test_error_cases()

    # 汇总结果
    print_section("测试结果汇总")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！Webhook 端点工作正常。")
        return 0
    else:
        print(f"\n⚠ 有 {total - passed} 项测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
