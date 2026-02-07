"""
直接测试工作流执行器
"""
import asyncio
from app.db.database import get_db
from app.services.scheduler_service import scheduler_service
from app.utils.custom_logger import log


async def test_workflow():
    """测试工作流执行"""
    db = next(get_db())

    # 手动注册执行器（模拟模块启动）
    from app.services.executors import (
        ContentGenerationExecutor,
        PublishingExecutor,
        WorkflowExecutor,
        AddToPoolExecutor,
        ApproveExecutor
    )

    print("\n注册执行器...")
    content_gen_executor = ContentGenerationExecutor()
    publishing_executor = PublishingExecutor()
    workflow_executor = WorkflowExecutor()
    add_to_pool_executor = AddToPoolExecutor()
    approve_executor = ApproveExecutor()

    scheduler_service.register_executor(content_gen_executor)
    scheduler_service.register_executor(publishing_executor)
    scheduler_service.register_executor(workflow_executor)
    scheduler_service.register_executor(add_to_pool_executor)
    scheduler_service.register_executor(approve_executor)

    # 检查注册的执行器
    print("\n已注册的执行器:")
    executors = scheduler_service.get_registered_executors()
    for executor_type, executor_info in executors.items():
        if isinstance(executor_info, dict):
            print(f"  - {executor_type}: {executor_info.get('class_name', 'Unknown')}")
        else:
            print(f"  - {executor_type}: {executor_info.__class__.__name__}")

    # 准备测试参数（使用 content_id=5，避免冲突）
    task_params = {
        "steps": [
            {
                "type": "approve",
                "params": {
                    "content_id": 5,
                    "approve": True
                }
            },
            {
                "type": "add_to_pool",
                "params": {
                    "content_id": 5,
                    "priority": 5,
                    "auto_approve": True
                }
            }
        ]
    }

    print("\n开始执行工作流...")
    print(f"任务参数: {task_params}")

    # 获取工作流执行器
    workflow_executor = scheduler_service.get_executor("workflow")

    if not workflow_executor:
        print("❌ 错误: 找不到 workflow 执行器")
        return

    print(f"✅ 找到工作流执行器: {workflow_executor.__class__.__name__}")

    # 执行工作流
    result = await workflow_executor.execute(
        task_id=999,
        task_params=task_params,
        db=db
    )

    print("\n执行结果:")
    print(f"  成功: {result.success}")
    print(f"  消息: {result.message}")
    print(f"  耗时: {result.duration}")
    if result.error:
        print(f"  错误: {result.error}")
    if result.data:
        print(f"  数据: {result.data}")
    if result.metadata:
        print(f"  元数据: {result.metadata}")

    # 检查内容状态
    from app.models.content import Content
    content = db.query(Content).filter(Content.id == 5).first()
    if content:
        print(f"\n内容状态:")
        print(f"  审核状态: {content.review_status}")
        print(f"  发布状态: {content.publish_status}")

    # 检查发布池
    from app.models.publish import PublishPool
    pool_items = db.query(PublishPool).filter(PublishPool.content_id == 5).all()
    print(f"\n发布池记录数: {len(pool_items)}")
    for item in pool_items:
        print(f"  ID: {item.id}, 状态: {item.status}, 优先级: {item.priority}")


if __name__ == "__main__":
    asyncio.run(test_workflow())
