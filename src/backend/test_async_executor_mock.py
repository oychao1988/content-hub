"""
异步内容生成执行器测试脚本（Mock 版本）

测试 AsyncContentGenerationExecutor 的核心功能，不依赖实际的 CLI
"""
import sys
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, '/Users/Oychao/Documents/Projects/content-hub/src/backend')

from app.services.executors.async_content_generation_executor import AsyncContentGenerationExecutor
from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal
from app.models.account import Account
from app.models import ContentGenerationTask


def print_section(title):
    """打印分节标题"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_executor_registration():
    """测试执行器注册"""
    print_section("测试 1: 执行器注册")

    # 注册执行器
    executor = AsyncContentGenerationExecutor()
    scheduler_service.register_executor(executor)

    # 验证注册
    registered = scheduler_service.get_registered_executors()
    print(f"✓ 已注册的执行器: {list(registered.keys())}")

    if "async_content_generation" in registered:
        print(f"✓ async_content_generation 执行器已成功注册")
        print(f"  信息: {registered['async_content_generation']}")
        return True
    else:
        print(f"✗ async_content_generation 执行器未找到")
        return False


def test_parameter_validation():
    """测试参数验证"""
    print_section("测试 2: 参数验证")

    executor = AsyncContentGenerationExecutor()

    # 测试有效参数
    valid_params = {
        'account_ids': [49],
        'count_per_account': 2,
        'category': '技术',
        'auto_approve': False,
        'priority': 5
    }

    print(f"测试有效参数: {valid_params}")
    if executor.validate_params(valid_params):
        print(f"✓ 参数验证通过")
    else:
        print(f"✗ 参数验证失败")
        return False

    # 测试无效参数（缺少 account_ids）
    invalid_params = {
        'count_per_account': 2
    }

    print(f"\n测试无效参数（缺少 account_ids）: {invalid_params}")
    if not executor.validate_params(invalid_params):
        print(f"✓ 正确拒绝了无效参数")
    else:
        print(f"✗ 应该拒绝无效参数")
        return False

    # 测试无效参数（无效的 priority）
    invalid_params2 = {
        'account_ids': [49],
        'count_per_account': 2,
        'priority': 15  # 超出范围
    }

    print(f"\n测试无效参数（priority 超出范围）: {invalid_params2}")
    if not executor.validate_params(invalid_params2):
        print(f"✓ 正确拒绝了无效的 priority")
    else:
        print(f"✗ 应该拒绝无效的 priority")
        return False

    # 测试有效参数（多个账号）
    multi_account_params = {
        'account_ids': [49, 50, 51],
        'count_per_account': 3,
        'category': '产品',
        'priority': 8
    }

    print(f"\n测试多账号参数: {multi_account_params}")
    if executor.validate_params(multi_account_params):
        print(f"✓ 多账号参数验证通过")
    else:
        print(f"✗ 多账号参数验证失败")
        return False

    return True


async def test_executor_execution_with_mock():
    """测试执行器执行（使用 Mock）"""
    print_section("测试 3: 执行器执行（Mock 版本）")

    # 创建执行器
    executor = AsyncContentGenerationExecutor()

    # 查询可用的账号
    db = SessionLocal()
    try:
        accounts = db.query(Account).limit(3).all()
        if not accounts:
            print("✗ 没有找到可用的账号")
            return False

        account_ids = [acc.id for acc in accounts]
        print(f"找到账号: {[(acc.id, acc.name) for acc in accounts]}")

        # 准备参数
        params = {
            'account_ids': account_ids,
            'count_per_account': 2,  # 每个账号生成 2 篇
            'category': '技术',
            'auto_approve': False,
            'priority': 5
        }

        print(f"\n执行参数:")
        print(f"  账号: {params['account_ids']}")
        print(f"  每账号数量: {params['count_per_account']}")
        print(f"  板块: {params['category']}")
        print(f"  自动审核: {params['auto_approve']}")
        print(f"  优先级: {params['priority']}")

        # Mock AsyncContentGenerationService.submit_task 方法
        with patch('app.services.executors.async_content_generation_executor.AsyncContentGenerationService') as MockService:
            # 创建 mock 实例
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance

            # Mock submit_task 方法返回模拟的任务ID
            mock_service_instance.submit_task.side_effect = [
                f"mock-task-{i}" for i in range(len(account_ids) * params['count_per_account'])
            ]

            print(f"\n开始执行（使用 Mock 服务）...")
            result = await executor.execute(
                task_id=999,
                task_params=params,
                db=db
            )

        # 显示结果
        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")
        print(f"  耗时: {result.duration:.2f}秒" if result.duration else "  耗时: N/A")

        if result.data:
            data = result.data
            print(f"\n数据统计:")
            print(f"  提交任务数: {data.get('total_submitted', 0)}")
            print(f"  失败任务数: {data.get('total_failed', 0)}")
            print(f"  错误数: {len(data.get('errors', []))}")

            if data.get('account_stats'):
                print(f"\n账号统计:")
                for acc_id, stats in data['account_stats'].items():
                    print(f"  账号 {acc_id} ({stats['account_name']}):")
                    print(f"    成功: {stats['success']}")
                    print(f"    失败: {stats['failed']}")
                    print(f"    总计: {stats['total']}")

            if data.get('tasks'):
                print(f"\n提交的任务列表（前 5 个）:")
                for task in data['tasks'][:5]:
                    print(f"  - {task['task_id']}:")
                    print(f"    账号: {task['account_name']} (ID: {task['account_id']})")
                    print(f"    选题: {task['topic']}")
                    print(f"    板块: {task.get('category', 'N/A')}")

        # 验证提交次数
        expected_count = len(account_ids) * params['count_per_account']
        actual_count = mock_service_instance.submit_task.call_count

        print(f"\n验证:")
        print(f"  预期提交次数: {expected_count}")
        print(f"  实际提交次数: {actual_count}")

        if actual_count == expected_count:
            print(f"✓ 提交次数正确")
        else:
            print(f"✗ 提交次数不匹配")
            return False

        # 验证每个账号的调用
        print(f"\n验证调用详情:")
        for idx, call in enumerate(mock_service_instance.submit_task.call_args_list[:5]):
            args, kwargs = call
            print(f"  调用 {idx + 1}:")
            print(f"    account_id: {kwargs.get('account_id')}")
            print(f"    topic: {kwargs.get('topic')}")
            print(f"    category: {kwargs.get('category')}")
            print(f"    priority: {kwargs.get('priority')}")

        return result.success

    finally:
        db.close()


def test_topic_generation():
    """测试选题生成"""
    print_section("测试 4: 选题生成")

    executor = AsyncContentGenerationExecutor()

    # 获取一个测试账号
    db = SessionLocal()
    try:
        account = db.query(Account).first()
        if not account:
            print("✗ 没有找到可用的账号")
            return False

        print(f"测试账号: {account.id} - {account.name}")

        # 测试不同板块的选题生成
        categories = ["技术", "产品", "运营", "营销"]

        for category in categories:
            print(f"\n测试板块: {category}")
            topics = executor._generate_topics(account, count=2, category=category)

            print(f"  生成选题 ({len(topics)} 个):")
            for idx, topic in enumerate(topics, 1):
                print(f"    {idx}. {topic['topic']}")

            if len(topics) != 2:
                print(f"  ✗ 选题数量不符合预期")
                return False

        print(f"\n✓ 所有板块的选题生成都成功")
        return True

    finally:
        db.close()


async def test_custom_topics_with_mock():
    """测试自定义选题（Mock 版本）"""
    print_section("测试 5: 自定义选题（Mock 版本）")

    # 创建执行器
    executor = AsyncContentGenerationExecutor()

    # 查询可用账号
    db = SessionLocal()
    try:
        account = db.query(Account).first()
        if not account:
            print("✗ 没有找到可用的账号")
            return False

        # 自定义选题
        custom_topics = [
            {
                'topic': '自定义选题1：人工智能未来',
                'keywords': 'AI,人工智能,未来',
                'requirements': '深度分析人工智能的发展趋势',
                'tone': '专业'
            },
            {
                'topic': '自定义选题2：云计算实践',
                'keywords': '云计算,实践,技术',
                'requirements': '分享云计算的实践经验',
                'tone': '实用'
            }
        ]

        params = {
            'account_ids': [account.id],
            'count_per_account': 2,
            'topics': custom_topics,  # 使用自定义选题
            'auto_approve': False,
            'priority': 5
        }

        print(f"使用自定义选题执行任务:")
        for topic in custom_topics:
            print(f"  - {topic['topic']}")

        # Mock AsyncContentGenerationService
        with patch('app.services.executors.async_content_generation_executor.AsyncContentGenerationService') as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance
            mock_service_instance.submit_task.side_effect = [
                f"mock-custom-{i}" for i in range(len(custom_topics))
            ]

            result = await executor.execute(
                task_id=998,
                task_params=params,
                db=db
            )

        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")

        if result.data and result.data.get('tasks'):
            submitted_topics = [t['topic'] for t in result.data['tasks']]
            print(f"\n提交的选题:")
            for topic in submitted_topics:
                print(f"  - {topic}")

            # 验证是否使用了自定义选题
            custom_used = any('自定义选题' in topic for topic in submitted_topics)
            if custom_used and len(submitted_topics) == len(custom_topics):
                print(f"\n✓ 成功使用了自定义选题")
                return True
            else:
                print(f"\n✗ 未正确使用自定义选题")
                return False

        return False

    finally:
        db.close()


async def test_error_handling():
    """测试错误处理"""
    print_section("测试 6: 错误处理")

    executor = AsyncContentGenerationExecutor()
    db = SessionLocal()

    try:
        # 测试不存在的账号
        params = {
            'account_ids': [99999],  # 不存在的账号
            'count_per_account': 1,
            'category': '技术'
        }

        print(f"测试不存在的账号: {params['account_ids']}")

        with patch('app.services.executors.async_content_generation_executor.AsyncContentGenerationService') as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance

            result = await executor.execute(
                task_id=997,
                task_params=params,
                db=db
            )

        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")

        if not result.success:
            print(f"✓ 正确处理了不存在的账号")
            return True
        else:
            print(f"✗ 应该返回失败结果")
            return False

    finally:
        db.close()


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  异步内容生成执行器测试套件（Mock 版本）")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    results = []

    # 测试 1: 执行器注册
    try:
        results.append(("执行器注册", test_executor_registration()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("执行器注册", False))

    # 测试 2: 参数验证
    try:
        results.append(("参数验证", test_parameter_validation()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("参数验证", False))

    # 测试 3: 执行器执行
    try:
        results.append(("执行器执行", await test_executor_execution_with_mock()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("执行器执行", False))

    # 测试 4: 选题生成
    try:
        results.append(("选题生成", test_topic_generation()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("选题生成", False))

    # 测试 5: 自定义选题
    try:
        results.append(("自定义选题", await test_custom_topics_with_mock()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("自定义选题", False))

    # 测试 6: 错误处理
    try:
        results.append(("错误处理", await test_error_handling()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("错误处理", False))

    # 显示测试总结
    print_section("测试总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print(f"\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
