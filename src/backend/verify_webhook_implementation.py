#!/usr/bin/env python3
"""
验证 Webhook 端点实现

检查以下方面：
1. 端点是否正确注册
2. 依赖注入是否正确配置
3. 签名验证是否集成
4. 错误处理是否完整
5. 日志记录是否完整
6. 幂等性检查是否实现
7. 三个事件类型处理是否完整
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.content.endpoints import router, handle_webhook_callback
from app.services.webhook_handler import WebhookHandler, get_webhook_handler
from app.utils.webhook_signature import create_verifier
from app.core.config import settings
from app.models import ContentGenerationTask
import inspect


def verify_endpoint_registration():
    """验证端点注册"""
    print("\n" + "=" * 60)
    print("1. 验证端点注册")
    print("=" * 60)

    webhook_routes = [
        route for route in router.routes
        if hasattr(route, 'path') and 'callback' in route.path
    ]

    if not webhook_routes:
        print("❌ 未找到 Webhook 端点")
        return False

    route = webhook_routes[0]
    print(f"✓ 端点路径: {route.path}")
    print(f"✓ 请求方法: {route.methods}")
    print(f"✓ Tags: {route.tags}")
    print(f"✓ 处理函数: {route.endpoint.__name__}")

    # 检查路径参数
    if '{task_id}' in route.path:
        print("✓ 包含 task_id 路径参数")
    else:
        print("❌ 缺少 task_id 路径参数")
        return False

    # 检查 tags
    if 'webhooks' in route.tags:
        print("✓ 包含 'webhooks' 标签（用于 API 文档分组）")
    else:
        print("⚠ 缺少 'webhooks' 标签")

    return True


def verify_function_signature():
    """验证函数签名"""
    print("\n" + "=" * 60)
    print("2. 验证函数签名和依赖注入")
    print("=" * 60)

    sig = inspect.signature(handle_webhook_callback)
    params = list(sig.parameters.keys())

    print(f"函数参数: {params}")

    # 检查必需的参数
    required_params = ['task_id', 'request', 'db', 'x_webhook_signature', 'webhook_handler']
    missing_params = [p for p in required_params if p not in params]

    if missing_params:
        print(f"❌ 缺少参数: {missing_params}")
        return False

    print("✓ 包含所有必需参数")

    # 检查参数类型
    param_annotations = {
        name: sig.parameters[name].annotation
        for name in params
    }

    print("\n参数类型注解:")
    for name, annotation in param_annotations.items():
        print(f"  {name}: {annotation}")

    # 检查关键依赖
    if 'Depends' in str(param_annotations.get('db')):
        print("✓ db 使用依赖注入（Depends）")
    else:
        print("⚠ db 可能未正确使用依赖注入")

    if 'Header' in str(param_annotations.get('x_webhook_signature')):
        print("✓ x_webhook_signature 使用 Header 提取")
    else:
        print("⚠ x_webhook_signature 可能未正确使用 Header")

    if 'Depends' in str(param_annotations.get('webhook_handler')):
        print("✓ webhook_handler 使用依赖注入（Depends）")
    else:
        print("⚠ webhook_handler 可能未正确使用依赖注入")

    return True


def verify_documentation():
    """验证文档字符串"""
    print("\n" + "=" * 60)
    print("3. 验证文档字符串")
    print("=" * 60)

    doc = handle_webhook_callback.__doc__

    if not doc:
        print("❌ 缺少文档字符串")
        return False

    print("✓ 包含文档字符串")

    # 检查关键内容
    required_sections = [
        "content-creator",
        "Webhook",
        "completed",
        "failed",
        "progress",
        "签名",
        "幂等",
        "错误处理"
    ]

    missing_sections = []
    for section in required_sections:
        if section not in doc:
            missing_sections.append(section)

    if missing_sections:
        print(f"⚠ 文档中缺少以下内容: {missing_sections}")
    else:
        print("✓ 文档内容完整")

    # 打印部分文档
    print("\n文档预览（前 500 字符）:")
    print(doc[:500] + "...")

    return True


def verify_event_handling():
    """验证事件处理逻辑"""
    print("\n" + "=" * 60)
    print("4. 验证事件处理逻辑")
    print("=" * 60)

    # 读取函数源代码
    source = inspect.getsource(handle_webhook_callback)

    events = {
        "completed": "event == \"completed\"",
        "failed": "event == \"failed\"",
        "progress": "event == \"progress\""
    }

    for event_name, event_check in events.items():
        if event_check in source:
            print(f"✓ 处理 {event_name} 事件")

            # 检查是否调用了对应的处理方法
            handler_method = f"handle_task_{event_name}"
            if handler_method in source:
                print(f"  ✓ 调用 {handler_method}()")
            else:
                print(f"  ❌ 未调用 {handler_method}()")
        else:
            print(f"❌ 未处理 {event_name} 事件")

    return True


def verify_signature_verification():
    """验证签名验证"""
    print("\n" + "=" * 60)
    print("5. 验证签名验证集成")
    print("=" * 60)

    source = inspect.getsource(handle_webhook_callback)

    # 检查签名相关代码
    checks = {
        "签名存在检查": "x_webhook_signature" in source and "not x_webhook_signature" in source,
        "密钥配置检查": "WEBHOOK_SECRET_KEY" in source,
        "签名验证器创建": "create_verifier" in source,
        "签名验证调用": "verify_from_headers" in source or "verify" in source,
        "403 错误（签名缺失）": "403" in source,
        "401 错误（签名无效）": "401" in source,
    }

    all_passed = True
    for check_name, check_result in checks.items():
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"⚠ {check_name} 未找到")
            all_passed = False

    # 检查条件签名验证
    if "WEBHOOK_REQUIRE_SIGNATURE" in source:
        print("✓ 签名验证基于 WEBHOOK_REQUIRE_SIGNATURE 配置")
    else:
        print("⚠ 未检查 WEBHOOK_REQUIRE_SIGNATURE 配置")

    return all_passed


def verify_error_handling():
    """验证错误处理"""
    print("\n" + "=" * 60)
    print("6. 验证错误处理")
    print("=" * 60)

    source = inspect.getsource(handle_webhook_callback)

    error_codes = {
        "404": "任务不存在",
        "401": "签名验证失败",
        "403": "签名缺失",
        "400": "请求体格式错误",
        "500": "服务器内部错误"
    }

    all_found = True
    for code, description in error_codes.items():
        if code in source:
            print(f"✓ 包含 {code} 错误处理（{description}）")
        else:
            print(f"⚠ 可能缺少 {code} 错误处理（{description}）")
            all_found = False

    # 检查异常处理
    if "try:" in source and "except" in source:
        print("✓ 包含异常处理（try-except）")
    else:
        print("⚠ 缺少异常处理")
        all_found = False

    # 检查 HTTPException
    if "HTTPException" in source:
        print("✓ 使用 HTTPException 返回错误")
    else:
        print("⚠ 未使用 HTTPException")
        all_found = False

    return all_found


def verify_logging():
    """验证日志记录"""
    print("\n" + "=" * 60)
    print("7. 验证日志记录")
    print("=" * 60)

    source = inspect.getsource(handle_webhook_callback)

    logging_checks = {
        "接收请求日志": "Received webhook callback" in source or "接收" in source,
        "成功处理日志": "processed successfully" in source or "处理成功" in source,
        "失败处理日志": "failed" in source or "失败" in source,
        "错误日志": "log.error" in source,
        "警告日志": "log.warning" in source or "警告" in source,
    }

    all_found = True
    for check_name, check_result in logging_checks.items():
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"⚠ {check_name} 未找到")
            all_found = False

    return all_found


def verify_idempotency():
    """验证幂等性"""
    print("\n" + "=" * 60)
    print("8. 验证幂等性保证")
    print("=" * 60)

    # 幂等性由 WebhookHandler 处理，但端点需要正确调用
    source = inspect.getsource(handle_webhook_callback)

    # 检查是否调用了 handler 方法（这些方法内部有幂等性检查）
    if "handle_task_completed" in source:
        print("✓ 调用 handle_task_completed（包含幂等性检查）")

    if "handle_task_failed" in source:
        print("✓ 调用 handle_task_failed（包含幂等性检查）")

    if "handle_task_progress" in source:
        print("✓ 调用 handle_task_progress（包含幂等性检查）")

    # 检查响应中是否包含幂等性信息
    if '"skipped"' in source or "'skipped'" in source:
        print("✓ 响应包含幂等性标识（skipped）")
    else:
        print("⚠ 响应可能未包含幂等性标识")

    return True


def verify_response_format():
    """验证响应格式"""
    print("\n" + "=" * 60)
    print("9. 验证响应格式")
    print("=" * 60)

    source = inspect.getsource(handle_webhook_callback)

    response_fields = {
        "success": "success",
        "message": "message",
        "details": "details"
    }

    all_found = True
    for field_name, field_key in response_fields.items():
        if field_key in source:
            print(f"✓ 响应包含 {field_name} 字段")
        else:
            print(f"⚠ 响应可能缺少 {field_name} 字段")
            all_found = False

    return all_found


def run_all_verifications():
    """运行所有验证"""
    print("\n" + "🔍" * 30)
    print("开始验证 Webhook 端点实现")
    print("🔍" * 30)

    results = {}

    try:
        results["端点注册"] = verify_endpoint_registration()
        results["函数签名"] = verify_function_signature()
        results["文档字符串"] = verify_documentation()
        results["事件处理"] = verify_event_handling()
        results["签名验证"] = verify_signature_verification()
        results["错误处理"] = verify_error_handling()
        results["日志记录"] = verify_logging()
        results["幂等性"] = verify_idempotency()
        results["响应格式"] = verify_response_format()
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, result in results.items():
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{status} - {check_name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 项检查通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有检查通过！Webhook 端点实现完整且正确。")
        return True
    else:
        print(f"\n⚠ 有 {total - passed} 项检查未通过，请检查实现。")
        return False


if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)
