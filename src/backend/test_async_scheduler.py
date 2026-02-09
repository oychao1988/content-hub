"""
异步内容生成执行器测试脚本

测试 AsyncContentGenerationExecutor 的功能
"""
import sys
import asyncio
from datetime import datetime

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

    return True


async def test_executor_execution():
    """测试执行器执行"""
    print_section("测试 3: 执行器执行")

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
            'auto_approve': False,  # 不自动审核，方便测试
            'priority': 5
        }

        print(f"\n执行参数:")
        print(f"  账号: {params['account_ids']}")
        print(f"  每账号数量: {params['count_per_account']}")
        print(f"  板块: {params['category']}")
        print(f"  自动审核: {params['auto_approve']}")
        print(f"  优先级: {params['priority']}")

        # 执行
        print(f"\n开始执行...")
        result = await executor.execute(
            task_id=999,  # 测试用任务ID
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

            if data.get('errors'):
                print(f"\n错误信息:")
                for error in data['errors'][:5]:
                    print(f"  - {error}")

        # 验证数据库
        print(f"\n验证数据库...")
        if result.data and result.data.get('tasks'):
            task_ids = [t['task_id'] for t in result.data['tasks']]
            task_count = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.task_id.in_(task_ids)
            ).count()
            print(f"  数据库中的任务数: {task_count}")
            print(f"  提交的任务数: {len(task_ids)}")

            if task_count == len(task_ids):
                print(f"✓ 所有任务都已成功保存到数据库")
            else:
                print(f"✗ 部分任务未保存到数据库")

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

        # 生成选题
        topics = executor._generate_topics(account, count=3, category="技术")

        print(f"\n生成的选题 ({len(topics)} 个):")
        for idx, topic in enumerate(topics, 1):
            print(f"\n  选题 {idx}:")
            print(f"    主题: {topic['topic']}")
            print(f"    关键词: {topic['keywords']}")
            print(f"    要求: {topic['requirements']}")
            print(f"    语气: {topic['tone']}")

        if len(topics) == 3:
            print(f"\n✓ 选题生成成功")
            return True
        else:
            print(f"\n✗ 选题数量不符合预期")
            return False

    finally:
        db.close()


async def test_custom_topics():
    """测试自定义选题"""
    print_section("测试 5: 自定义选题")

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
            if custom_used:
                print(f"\n✓ 成功使用了自定义选题")
                return True
            else:
                print(f"\n✗ 未使用自定义选题")
                return False

        return False

    finally:
        db.close()


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  异步内容生成执行器测试套件")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    results = []

    # 测试 1: 执行器注册
    try:
        results.append(("执行器注册", test_executor_registration()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        results.append(("执行器注册", False))

    # 测试 2: 参数验证
    try:
        results.append(("参数验证", test_parameter_validation()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        results.append(("参数验证", False))

    # 测试 3: 执行器执行
    try:
        results.append(("执行器执行", await test_executor_execution()))
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
        results.append(("选题生成", False))

    # 测试 5: 自定义选题
    try:
        results.append(("自定义选题", await test_custom_topics()))
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("自定义选题", False))

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
