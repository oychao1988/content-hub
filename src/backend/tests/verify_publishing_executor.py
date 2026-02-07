#!/usr/bin/env python3
"""
发布执行器验证脚本

用于验证 PublishingExecutor 的功能
"""
import sys
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

# 添加项目路径
sys.path.insert(0, '/Users/Oychao/Documents/Projects/content-hub/src/backend')

from app.services.scheduler_service import scheduler_service
from app.services.executors.publishing_executor import PublishingExecutor
from app.utils.custom_logger import log


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def verify_executor_interface():
    """验证执行器接口"""
    print_section("1. 验证执行器接口")

    try:
        executor = PublishingExecutor()

        # 检查 executor_type
        print(f"\n执行器类型: {executor.executor_type}")
        if executor.executor_type == "publishing":
            print("✓ executor_type 正确")
        else:
            print("✗ executor_type 不正确")
            return False

        # 检查 validate_params
        print("\n测试 validate_params...")
        if executor.validate_params({}):
            print("✓ validate_params 正常工作")
        else:
            print("✗ validate_params 失败")
            return False

        # 检查 get_executor_info
        info = executor.get_executor_info()
        print(f"\n执行器信息: {info}")
        if "type" in info and "class" in info and "module" in info:
            print("✓ get_executor_info 正常工作")
        else:
            print("✗ get_executor_info 返回格式不正确")
            return False

        print("\n✓ 所有接口验证通过")
        return True

    except Exception as e:
        print(f"\n✗ 接口验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def verify_execute_empty_pool():
    """验证执行空发布池"""
    print_section("2. 验证执行空发布池")

    # 使用 mock 来确保返回空列表
    executor = PublishingExecutor()
    mock_db = Mock()

    with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service:
        # 模拟没有待发布内容
        mock_pool_service.get_pending_entries.return_value = []

        try:
            # 执行任务
            result = await executor.execute(
                task_id=999,
                task_params={},
                db=mock_db
            )

            print(f"\n执行结果:")
            print(f"  - success: {result.success}")
            print(f"  - message: {result.message}")
            print(f"  - total_count: {result.data['total_count']}")

            if result.success and result.data["total_count"] == 0:
                print("\n✓ 空发布池处理正确")
                return True
            else:
                print("\n✗ 空发布池处理不正确")
                return False

        except Exception as e:
            print(f"\n✗ 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def verify_execute_with_success():
    """验证成功发布"""
    print_section("3. 验证成功发布")

    executor = PublishingExecutor()
    mock_db = Mock()

    # 创建模拟数据
    mock_pool_entry = Mock()
    mock_pool_entry.id = 1
    mock_pool_entry.content_id = 101

    mock_content = Mock()
    mock_content.id = 101
    mock_content.account_id = 1

    mock_account = Mock()
    mock_account.id = 1
    mock_account.name = "Test Account"

    with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
         patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

        # 模拟查询返回待发布内容
        mock_pool_service.get_pending_entries.return_value = [mock_pool_entry]

        # 模拟查询返回内容和账号
        def mock_query_side_effect(model):
            query_mock = Mock()
            filter_mock = Mock()
            filter_mock.filter.return_value.first.return_value = mock_content if model.__name__ == 'Content' else mock_account
            query_mock.filter.return_value = filter_mock
            return query_mock

        mock_db.query.side_effect = mock_query_side_effect

        # 模拟发布成功
        mock_publisher_service.manual_publish.return_value = {
            "success": True,
            "log_id": 100,
            "media_id": "test_media_id"
        }

        try:
            # 执行任务
            result = await executor.execute(
                task_id=1000,
                task_params={},
                db=mock_db
            )

            print(f"\n执行结果:")
            print(f"  - success: {result.success}")
            print(f"  - message: {result.message}")
            print(f"  - 总数: {result.data['total_count']}")
            print(f"  - 成功: {result.data['success_count']}")
            print(f"  - 失败: {result.data['failed_count']}")

            if result.success and result.data["success_count"] == 1:
                print("\n✓ 成功发布处理正确")
                return True
            else:
                print("\n✗ 成功发布处理不正确")
                return False

        except Exception as e:
            print(f"\n✗ 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def verify_execute_with_failure():
    """验证发布失败处理"""
    print_section("4. 验证发布失败处理")

    executor = PublishingExecutor()
    mock_db = Mock()

    # 创建模拟数据
    mock_pool_entry = Mock()
    mock_pool_entry.id = 1
    mock_pool_entry.content_id = 101

    mock_content = Mock()
    mock_content.id = 101
    mock_content.account_id = 1

    mock_account = Mock()
    mock_account.id = 1
    mock_account.name = "Test Account"

    with patch('app.services.executors.publishing_executor.publish_pool_service') as mock_pool_service, \
         patch('app.services.executors.publishing_executor.publisher_service') as mock_publisher_service:

        # 模拟查询返回待发布内容
        mock_pool_service.get_pending_entries.return_value = [mock_pool_entry]

        # 模拟查询返回内容和账号
        def mock_query_side_effect(model):
            query_mock = Mock()
            filter_mock = Mock()
            filter_mock.filter.return_value.first.return_value = mock_content if model.__name__ == 'Content' else mock_account
            query_mock.filter.return_value = filter_mock
            return query_mock

        mock_db.query.side_effect = mock_query_side_effect

        # 模拟发布失败
        mock_publisher_service.manual_publish.return_value = {
            "success": False,
            "error": "Test publish error"
        }

        # 模拟重试逻辑
        mock_pool_entry_for_retry = Mock()
        mock_pool_entry_for_retry.retry_count = 1
        mock_pool_entry_for_retry.max_retries = 3
        mock_pool_service.fail_publishing.return_value = mock_pool_entry_for_retry

        try:
            # 执行任务
            result = await executor.execute(
                task_id=1001,
                task_params={},
                db=mock_db
            )

            print(f"\n执行结果:")
            print(f"  - success: {result.success}")
            print(f"  - message: {result.message}")
            print(f"  - 总数: {result.data['total_count']}")
            print(f"  - 成功: {result.data['success_count']}")
            print(f"  - 失败: {result.data['failed_count']}")

            if result.success and result.data["failed_count"] == 1:
                print("\n✓ 发布失败处理正确")
                # 验证调用了重试逻辑
                if mock_pool_service.retry_publishing.called:
                    print("✓ 重试逻辑正确调用")
                return True
            else:
                print("\n✗ 发布失败处理不正确")
                return False

        except Exception as e:
            print(f"\n✗ 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "发布执行器验证脚本" + " " * 38 + "║")
    print("║" + " " * 20 + "PublishingExecutor Verification" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")

    results = []

    # 1. 验证执行器接口
    results.append(await verify_executor_interface())

    # 2. 验证执行空发布池
    results.append(await verify_execute_empty_pool())

    # 3. 验证成功发布
    results.append(await verify_execute_with_success())

    # 4. 验证发布失败处理
    results.append(await verify_execute_with_failure())

    # 打印总结
    print_section("验证总结")
    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✓ 所有验证通过")
        return 0
    else:
        print(f"\n✗ {total - passed} 个验证失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
