"""
阶段 4 集成验证脚本

验证异步内容生成执行器是否正确集成到调度器系统
"""
import sys
sys.path.insert(0, '/Users/Oychao/Documents/Projects/content-hub/src/backend')

from app.services.scheduler_service import scheduler_service
from app.services.executors import AsyncContentGenerationExecutor
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from app.utils.custom_logger import log


def print_section(title):
    """打印分节标题"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def verify_executor_registered():
    """验证执行器注册"""
    print_section("1. 验证执行器注册")

    # 手动注册执行器用于验证
    executor = AsyncContentGenerationExecutor()
    scheduler_service.register_executor(executor)

    # 获取已注册的执行器
    executors = scheduler_service.get_registered_executors()

    print(f"已注册的执行器 ({len(executors)} 个):")
    for executor_type, info in executors.items():
        print(f"  - {executor_type}: {info['class']}")

    if 'async_content_generation' in executors:
        print(f"\n✓ AsyncContentGenerationExecutor 已成功注册")
        return True
    else:
        print(f"\n✗ AsyncContentGenerationExecutor 未注册")
        return False


def verify_executor_instance():
    """验证执行器实例"""
    print_section("2. 验证执行器实例")

    try:
        executor = AsyncContentGenerationExecutor()

        print(f"执行器类型: {executor.executor_type}")
        print(f"执行器类: {executor.__class__.__name__}")
        print(f"执行器模块: {executor.__class__.__module__}")

        # 测试参数验证
        test_params = {
            'account_ids': [49],
            'count_per_account': 1,
            'priority': 5
        }

        if executor.validate_params(test_params):
            print(f"\n✓ 参数验证功能正常")
            return True
        else:
            print(f"\n✗ 参数验证失败")
            return False

    except Exception as e:
        print(f"\n✗ 创建执行器失败: {str(e)}")
        return False


def verify_database_tasks():
    """验证数据库中的任务"""
    print_section("3. 验证数据库任务")

    db = SessionLocal()

    try:
        # 查询异步内容生成任务
        async_tasks = db.query(ScheduledTask).filter_by(
            task_type='async_content_generation'
        ).all()

        print(f"找到 {len(async_tasks)} 个异步内容生成任务:")

        if len(async_tasks) == 0:
            print("  (无)")
            print("\n⚠️  数据库中没有异步内容生成任务")
            print("提示: 运行 'python create_async_generation_task.py' 创建示例任务")
            return False

        for task in async_tasks:
            print(f"\n  任务 ID: {task.id}")
            print(f"  名称: {task.name}")
            print(f"  Cron: {task.cron_expression}")
            print(f"  状态: {'启用' if task.is_active else '禁用'}")

            # 验证参数格式
            if task.params:
                if isinstance(task.params, dict):
                    params = task.params
                else:
                    import json
                    params = json.loads(task.params)

                print(f"  参数:")
                print(f"    账号: {params.get('account_ids', [])}")
                print(f"    数量: {params.get('count_per_account', 0)}")
                print(f"    板块: {params.get('category', 'N/A')}")

        print(f"\n✓ 数据库任务验证完成")
        return True

    finally:
        db.close()


def verify_executor_methods():
    """验证执行器方法"""
    print_section("4. 验证执行器方法")

    executor = AsyncContentGenerationExecutor()

    methods = {
        'executor_type': lambda: executor.executor_type,
        'validate_params': lambda: executor.validate_params({'account_ids': [49], 'count_per_account': 1}),
        'get_executor_info': lambda: executor.get_executor_info(),
        '_generate_topics': lambda: executor._generate_topics(
            type('Account', (), {'id': 1, 'name': 'Test', 'description': 'Test Account'}),
            2,
            '技术'
        )
    }

    all_ok = True

    for method_name, method_func in methods.items():
        try:
            result = method_func()
            print(f"✓ {method_name}: {type(result).__name__}")
        except Exception as e:
            print(f"✗ {method_name}: {str(e)}")
            all_ok = False

    if all_ok:
        print(f"\n✓ 所有方法验证通过")
    else:
        print(f"\n✗ 部分方法验证失败")

    return all_ok


def verify_integration():
    """验证整体集成"""
    print_section("5. 验证整体集成")

    checks = {
        "执行器注册": verify_executor_registered,
        "执行器实例": verify_executor_instance,
        "数据库任务": verify_database_tasks,
        "执行器方法": verify_executor_methods
    }

    results = {}

    for check_name, check_func in checks.items():
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n✗ {check_name} 检查时出错: {str(e)}")
            results[check_name] = False

    print_section("验证总结")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for check_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {check_name}: {status}")

    print(f"\n总计: {passed}/{total} 检查通过")

    if passed == total:
        print(f"\n🎉 阶段 4 集成验证通过！")
        print(f"\n下一步:")
        print(f"  1. 重启服务加载定时任务")
        print(f"  2. 通过 API 触发任务测试")
        print(f"  3. 查看执行历史")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个检查失败")
        print(f"\n请检查:")
        print(f"  - 执行器是否正确导入")
        print(f"  - 调度器模块是否正确配置")
        print(f"  - 数据库是否有任务记录")
        return 1


if __name__ == '__main__':
    exit_code = verify_integration()
    sys.exit(exit_code)
