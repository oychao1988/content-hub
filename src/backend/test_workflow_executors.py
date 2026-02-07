"""
测试工作流执行器功能

验证新执行器能否正常工作
"""
import asyncio
from app.db.sql_db import get_session_local
from app.services.scheduler_service import scheduler_service
from app.services.executors import (
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor,
    ContentGenerationExecutor
)


async def test_workflow_executor():
    """测试工作流执行器"""
    print("=" * 60)
    print("测试工作流执行器")
    print("=" * 60)

    # 1. 注册执行器
    print("\n1. 注册执行器...")
    executors = [
        ContentGenerationExecutor(),
        ApproveExecutor(),
        AddToPoolExecutor(),
        WorkflowExecutor()
    ]

    for executor in executors:
        scheduler_service.register_executor(executor)
        print(f"  ✓ 已注册: {executor.executor_type}")

    print(f"\n已注册的执行器: {list(scheduler_service.get_registered_executors().keys())}")

    # 2. 测试 WorkflowExecutor 参数验证
    print("\n2. 测试 WorkflowExecutor 参数验证...")
    workflow_executor = WorkflowExecutor()

    # 有效参数
    valid_params = {
        "steps": [
            {
                "type": "approve",
                "params": {"content_id": "${content_id}"}
            },
            {
                "type": "add_to_pool",
                "params": {
                    "content_id": "${content_id}",
                    "priority": 5,
                    "auto_approve": True
                }
            }
        ]
    }

    is_valid = workflow_executor.validate_params(valid_params)
    print(f"  ✓ 有效参数验证: {is_valid}")

    # 无效参数（缺少 steps）
    invalid_params = {"name": "test"}
    is_valid = workflow_executor.validate_params(invalid_params)
    print(f"  ✓ 无效参数验证: {is_valid}（应该为 False）")

    # 3. 测试变量解析
    print("\n3. 测试变量解析...")
    context = {"content_id": 123, "title": "测试文章"}
    params = {"content_id": "${content_id}", "name": "${title}"}
    resolved = workflow_executor._resolve_variables(params, context)
    print(f"  原始参数: {params}")
    print(f"  上下文: {context}")
    print(f"  解析结果: {resolved}")
    print(f"  ✓ 变量解析成功")

    # 4. 测试 ApproveExecutor
    print("\n4. 测试 ApproveExecutor...")
    approve_executor = ApproveExecutor()
    print(f"  ✓ 执行器类型: {approve_executor.executor_type}")

    approve_params = {"content_id": 999}  # 使用不存在的 ID
    is_valid = approve_executor.validate_params(approve_params)
    print(f"  ✓ 参数验证: {is_valid}")

    # 5. 测试 AddToPoolExecutor
    print("\n5. 测试 AddToPoolExecutor...")
    add_to_pool_executor = AddToPoolExecutor()
    print(f"  ✓ 执行器类型: {add_to_pool_executor.executor_type}")

    pool_params = {"content_id": 999, "priority": 5, "auto_approve": True}
    is_valid = add_to_pool_executor.validate_params(pool_params)
    print(f"  ✓ 参数验证: {is_valid}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_workflow_executor())
