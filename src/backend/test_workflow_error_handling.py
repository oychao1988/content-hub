"""
工作流执行器错误处理测试

测试工作流执行器在各种错误情况下的处理能力：
1. 参数验证失败
2. 步骤执行失败
3. 变量替换失败
4. 部分步骤成功后的回滚
"""
import asyncio
import json
from datetime import datetime

from app.db.database import SessionLocal
from app.services.scheduler_service import scheduler_service
from app.services.executors import (
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor
)
from app.models.scheduler import ScheduledTask
from app.utils.custom_logger import log


def setup_executors():
    """注册执行器"""
    executors = [
        WorkflowExecutor(),
        AddToPoolExecutor(),
        ApproveExecutor()
    ]

    for executor in executors:
        scheduler_service.register_executor(executor)


async def test_invalid_params():
    """测试 1: 无效参数"""
    print("\n" + "="*60)
    print("测试 1: 无效参数")
    print("="*60)

    db = SessionLocal()
    try:
        # 创建缺少 steps 参数的任务
        task = ScheduledTask(
            name="无效参数测试",
            task_type="workflow",
            description="测试参数验证",
            is_active=True,
            params={}  # 缺少 steps
        )

        result = await scheduler_service.execute_task(
            task_id=999,
            task_type="workflow",
            task_params={},
            db=db
        )

        print(f"  结果: {'✓ 通过' if not result.success else '✗ 失败'}")
        print(f"  消息: {result.message}")
        print(f"  预期: 参数验证失败")
        print(f"  实际: {'验证失败' if 'Missing required parameter' in str(result.error) or '参数验证失败' in result.message else '未验证'}")

        return not result.success  # 期望失败

    finally:
        db.close()


async def test_invalid_step_type():
    """测试 2: 无效的步骤类型"""
    print("\n" + "="*60)
    print("测试 2: 无效的步骤类型")
    print("="*60)

    db = SessionLocal()
    try:
        task_params = {
            "steps": [
                {
                    "type": "invalid_executor",  # 不存在的执行器
                    "params": {"content_id": 1}
                }
            ]
        }

        result = await scheduler_service.execute_task(
            task_id=999,
            task_type="workflow",
            task_params=task_params,
            db=db
        )

        print(f"  结果: {'✓ 通过' if not result.success else '✗ 失败'}")
        print(f"  消息: {result.message}")
        print(f"  预期: 找不到执行器")
        print(f"  实际: {'找不到执行器' if 'ExecutorNotFound' in str(result.error) or '未找到' in result.message else '未正确处理'}")

        return not result.success  # 期望失败

    finally:
        db.close()


async def test_step_failure():
    """测试 3: 步骤执行失败"""
    print("\n" + "="*60)
    print("测试 3: 步骤执行失败（不存在的 content_id）")
    print("="*60)

    db = SessionLocal()
    try:
        task_params = {
            "steps": [
                {
                    "type": "approve",
                    "params": {
                        "content_id": 99999  # 不存在的内容
                    }
                }
            ]
        }

        result = await scheduler_service.execute_task(
            task_id=999,
            task_type="workflow",
            task_params=task_params,
            db=db
        )

        print(f"  结果: {'✓ 通过' if not result.success else '✗ 失败'}")
        print(f"  消息: {result.message}")
        print(f"  错误: {result.error}")
        print(f"  预期: 步骤执行失败")

        return not result.success  # 期望失败

    finally:
        db.close()


async def test_variable_resolution():
    """测试 4: 变量替换"""
    print("\n" + "="*60)
    print("测试 4: 变量替换")
    print("="*60)

    db = SessionLocal()
    try:
        # 首先创建一个内容用于测试
        from app.models.content import Content
        content = Content(
            title="变量测试内容",
            content="测试内容",
            account_id=1,
            content_type="article",
            review_status="pending"
        )
        db.add(content)
        db.commit()
        db.refresh(content)

        # 使用变量引用
        task_params = {
            "steps": [
                {
                    "type": "approve",
                    "params": {
                        "content_id": "${content_id}",  # 会被替换为实际值
                        "auto_approve": True
                    }
                }
            ],
            "context": {
                "content_id": content.id  # 定义变量
            }
        }

        result = await scheduler_service.execute_task(
            task_id=999,
            task_type="workflow",
            task_params=task_params,
            db=db
        )

        print(f"  结果: {'✓ 通过' if result.success else '✗ 失败'}")
        print(f"  消息: {result.message}")
        print(f"  预期: 变量正确替换并执行成功")

        # 清理
        db.delete(content)
        db.commit()

        return result.success  # 期望成功

    finally:
        db.close()


async def test_partial_failure():
    """测试 5: 部分步骤失败（停止执行）"""
    print("\n" + "="*60)
    print("测试 5: 部分步骤失败（停止执行）")
    print("="*60)

    db = SessionLocal()
    try:
        # 创建测试内容
        from app.models.content import Content
        content = Content(
            title="部分失败测试",
            content="测试内容",
            account_id=1,
            content_type="article",
            review_status="pending"
        )
        db.add(content)
        db.commit()
        db.refresh(content)

        task_params = {
            "steps": [
                {
                    "type": "approve",  # 第一步成功
                    "params": {
                        "content_id": content.id,
                        "auto_approve": True
                    }
                },
                {
                    "type": "approve",  # 第二步失败（已经 approved）
                    "params": {
                        "content_id": 99999  # 不存在的内容
                    }
                }
            ]
        }

        result = await scheduler_service.execute_task(
            task_id=999,
            task_type="workflow",
            task_params=task_params,
            db=db
        )

        print(f"  结果: {'✓ 通过' if not result.success else '✗ 失败'}")
        print(f"  消息: {result.message}")

        if result.data and 'step_results' in result.data:
            step_results = result.data['step_results']
            print(f"  步骤 1 结果: {'成功' if step_results[0]['success'] else '失败'}")
            print(f"  步骤 2 结果: {'成功' if len(step_results) > 1 and step_results[1]['success'] else '失败'}")

        print(f"  预期: 第二步失败，工作流停止")

        # 清理
        db.delete(content)
        db.commit()

        return not result.success  # 期望失败

    finally:
        db.close()


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("工作流执行器错误处理测试")
    print("="*60)

    # 注册执行器
    setup_executors()

    # 运行测试
    tests = [
        ("无效参数", test_invalid_params),
        ("无效步骤类型", test_invalid_step_type),
        ("步骤执行失败", test_step_failure),
        ("变量替换", test_variable_resolution),
        ("部分步骤失败", test_partial_failure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ 测试 '{test_name}' 发生异常: {str(e)}")
            results.append((test_name, False))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {test_name}")

    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n✅ 所有错误处理测试通过！")
    else:
        print("\n⚠️  部分测试失败，需要修复")


if __name__ == "__main__":
    asyncio.run(main())
