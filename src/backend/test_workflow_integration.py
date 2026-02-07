"""
工作流执行器集成测试脚本

测试工作流执行器的完整功能，包括：
1. 执行器注册
2. 工作流任务创建
3. 手动触发执行
4. 执行历史查看
5. 发布池验证
"""
import asyncio
import json
from datetime import datetime

from app.db.database import SessionLocal
from app.services.scheduler_service import scheduler_service
from app.services.executors import (
    ContentGenerationExecutor,
    PublishingExecutor,
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor
)
from app.models.scheduler import ScheduledTask, TaskExecution
from app.models.publisher import PublishPool
from app.utils.custom_logger import log


def setup_executors():
    """注册所有执行器"""
    print("\n" + "="*60)
    print("步骤 1: 注册执行器")
    print("="*60)

    executors = [
        ContentGenerationExecutor(),
        PublishingExecutor(),
        WorkflowExecutor(),
        AddToPoolExecutor(),
        ApproveExecutor()
    ]

    for executor in executors:
        scheduler_service.register_executor(executor)
        print(f"  ✓ 已注册: {executor.executor_type}")

    registered = scheduler_service.get_registered_executors()
    print(f"\n已注册的执行器: {list(registered.keys())}")


def create_workflow_task(db, content_id: int = None):
    """创建工作流测试任务"""
    print("\n" + "="*60)
    print("步骤 2: 创建工作流测试任务")
    print("="*60)

    # 如果没有指定 content_id，使用第一个内容
    if content_id is None:
        from app.models.content import Content
        content = db.query(Content).first()
        if not content:
            print("  ✗ 数据库中没有内容，无法创建测试任务")
            return None
        content_id = content.id
        print(f"  使用内容 ID: {content_id}, 标题: {content.title}")

    # 定义工作流参数
    workflow_params = {
        "steps": [
            {
                "type": "approve",
                "params": {
                    "content_id": content_id,
                    "auto_approve": True
                }
            },
            {
                "type": "add_to_pool",
                "params": {
                    "content_id": content_id,
                    "priority": 5,
                    "auto_approve": True
                }
            }
        ]
    }

    # 创建任务
    task = ScheduledTask(
        name=f"工作流集成测试-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        task_type="workflow",
        description="测试工作流执行器的完整功能",
        is_active=True,
        cron_expression=None,  # 手动触发
        interval=None,
        interval_unit=None,
        params=workflow_params
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    print(f"  ✓ 任务创建成功")
    print(f"    任务 ID: {task.id}")
    print(f"    任务名称: {task.name}")
    print(f"    任务类型: {task.task_type}")
    print(f"    工作流步骤数: {len(workflow_params['steps'])}")

    return task


async def test_workflow_execution(db, task_id: int):
    """测试工作流执行"""
    print("\n" + "="*60)
    print("步骤 3: 执行工作流任务")
    print("="*60)

    # 获取任务
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        print(f"  ✗ 任务不存在: {task_id}")
        return

    print(f"  任务名称: {task.name}")
    print(f"  任务类型: {task.task_type}")

    # 提取参数
    task_params = {}
    if task.params:
        if isinstance(task.params, dict):
            task_params = task.params
        elif isinstance(task.params, str):
            try:
                task_params = json.loads(task.params)
            except json.JSONDecodeError:
                print(f"  ✗ 参数 JSON 解析失败")
                return

    print(f"  工作流步骤:")
    for i, step in enumerate(task_params.get('steps', []), 1):
        print(f"    {i}. {step.get('type')} - {step.get('params', {})}")

    # 执行任务
    print(f"\n  开始执行...")
    result = await scheduler_service.execute_task(
        task_id=task.id,
        task_type=task.task_type,
        task_params=task_params,
        db=db
    )

    # 显示结果
    print(f"\n  执行结果:")
    print(f"    成功: {result.success}")
    print(f"    消息: {result.message}")
    if result.error:
        print(f"    错误: {result.error}")
    if result.duration:
        print(f"    耗时: {result.duration:.2f} 秒")
    if result.data:
        print(f"    数据: {json.dumps(result.data, indent=2, ensure_ascii=False)}")

    return result


def check_execution_history(db, task_id: int):
    """查看执行历史"""
    print("\n" + "="*60)
    print("步骤 4: 查看执行历史")
    print("="*60)

    executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id
    ).order_by(TaskExecution.start_time.desc()).limit(5).all()

    if not executions:
        print(f"  没有找到执行记录")
        return

    print(f"  执行历史（最近 5 次）:")
    for i, exec in enumerate(executions, 1):
        print(f"\n  执行 #{i}:")
        print(f"    ID: {exec.id}")
        print(f"    状态: {exec.status}")
        print(f"    开始时间: {exec.start_time}")
        if exec.end_time:
            print(f"    结束时间: {exec.end_time}")
        if exec.duration:
            print(f"    耗时: {exec.duration} 秒")
        if exec.error_message:
            print(f"    错误: {exec.error_message}")
        if exec.result:
            result_data = exec.result.get('data', {}) if isinstance(exec.result, dict) else {}
            if result_data:
                print(f"    结果数据: {json.dumps(result_data, indent=6, ensure_ascii=False)}")


def check_publish_pool(db, content_id: int):
    """检查发布池"""
    print("\n" + "="*60)
    print("步骤 5: 检查发布池")
    print("="*60)

    pool_items = db.query(PublishPool).filter(
        PublishPool.content_id == content_id
    ).order_by(PublishPool.added_at.desc()).limit(5).all()

    if not pool_items:
        print(f"  内容 {content_id} 未在发布池中")
        return

    print(f"  内容 {content_id} 的发布池记录（最近 5 条）:")
    for item in pool_items:
        print(f"\n    记录 ID: {item.id}")
        print(f"    优先级: {item.priority}")
        print(f"    状态: {item.status}")
        print(f"    创建时间: {item.added_at}")
        if item.scheduled_at:
            print(f"    计划发布时间: {item.scheduled_at}")


def cleanup_test_data(db, task_id: int):
    """清理测试数据"""
    print("\n" + "="*60)
    print("步骤 6: 清理测试数据")
    print("="*60)

    # 删除执行历史
    deleted_executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id
    ).delete()
    print(f"  ✓ 删除 {deleted_executions} 条执行记录")

    # 删除任务
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if task:
        db.delete(task)
        print(f"  ✓ 删除任务: {task.name}")

    db.commit()


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("工作流执行器集成测试")
    print("="*60)

    db = SessionLocal()

    try:
        # 1. 注册执行器
        setup_executors()

        # 2. 创建测试任务
        task = create_workflow_task(db, content_id=4)  # 使用内容 ID 4
        if not task:
            print("\n✗ 测试失败: 无法创建测试任务")
            return

        # 3. 执行工作流
        result = await test_workflow_execution(db, task.id)

        # 4. 查看执行历史
        check_execution_history(db, task.id)

        # 5. 检查发布池（使用工作流中的 content_id）
        workflow_params = task.params
        if isinstance(workflow_params, dict):
            steps = workflow_params.get('steps', [])
            if steps:
                # 从第一个步骤获取 content_id
                content_id = steps[0].get('params', {}).get('content_id')
                if content_id:
                    check_publish_pool(db, content_id)

        # 6. 询问是否清理测试数据
        print("\n" + "="*60)
        cleanup = input("是否清理测试数据？(y/n): ").strip().lower()
        if cleanup == 'y':
            cleanup_test_data(db, task.id)

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"  任务 ID: {task.id}")
        print(f"  执行成功: {result.success if result else 'N/A'}")
        print(f"  执行消息: {result.message if result else 'N/A'}")
        print("\n" + "="*60)

        if result and result.success:
            print("✅ 所有测试通过！")
        else:
            print("❌ 测试失败")
            print("\n建议:")
            print("  1. 检查执行器注册是否正确")
            print("  2. 检查工作流参数是否有效")
            print("  3. 检查数据库连接")
            print("  4. 查看日志获取详细错误信息")

    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
