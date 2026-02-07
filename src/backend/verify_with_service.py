#!/usr/bin/env python3
"""
验证任务（包含服务启动）
"""
import sys
import time
from pathlib import Path

# 添加项目路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.scheduler_service import scheduler_service
from app.services.executors import (
    ContentGenerationExecutor,
    PublishingExecutor,
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor
)
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask


def verify_with_service():
    """验证任务（包含服务启动）"""

    print("=" * 70)
    print("验证工作流任务（包含服务启动）")
    print("=" * 70)
    print()

    # 1. 注册执行器
    print("🔧 注册执行器...")
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

    print(f"  ✅ 已注册执行器: {list(scheduler_service.get_registered_executors().keys())}")
    print()

    # 2. 启动调度器
    print("⏰ 启动调度器...")
    scheduler_service.start()
    print(f"  ✅ 调度器已启动 (运行状态: {scheduler_service.is_running})")
    print()

    # 3. 加载任务
    print("📋 从数据库加载任务...")
    db = SessionLocal()
    try:
        loaded_count = scheduler_service.load_tasks_from_db(db)
        print(f"  ✅ 成功加载 {loaded_count} 个任务")

        if loaded_count > 0:
            jobs = scheduler_service.get_scheduled_jobs()
            print(f"\n  当前调度器中的任务 ({len(jobs)} 个):")
            for job in jobs:
                print(f"    - {job['name']}")
                print(f"      下次运行: {job['next_run_time']}")

        print()
    finally:
        db.close()

    # 4. 查询任务详情
    print("🔍 查询任务详情...")
    db = SessionLocal()
    try:
        task = db.query(ScheduledTask).filter(
            ScheduledTask.name == "车界显眼包-每日7点自动发布"
        ).first()

        if task:
            print(f"  ✅ 找到任务:")
            print(f"     ID: {task.id}")
            print(f"     名称: {task.name}")
            print(f"     类型: {task.task_type}")
            print(f"     Cron: {task.cron_expression}")
            print(f"     状态: {'启用' if task.is_active else '禁用'}")
            print()

            # 5. 验证参数
            print("🔍 验证工作流参数...")
            workflow_executor = scheduler_service.get_executor("workflow")
            if workflow_executor:
                is_valid = workflow_executor.validate_params(task.params)
                if is_valid:
                    print(f"  ✅ 工作流参数验证通过")
                else:
                    print(f"  ❌ 工作流参数验证失败")

        print()
    finally:
        db.close()

    print("=" * 70)
    print("验证完成！")
    print("=" * 70)
    print()
    print("提示:")
    print("  - 调度器正在运行，任务已加载")
    print("  - 任务将在每天 07:00 自动执行")
    print("  - 使用 'make logs' 查看执行日志")
    print()
    print("如需手动触发任务测试，请使用:")
    print("  PYTHONPATH=. python -m cli.main scheduler trigger 1")
    print()


if __name__ == "__main__":
    try:
        verify_with_service()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭调度器
        if scheduler_service.is_running:
            print("\n关闭调度器...")
            scheduler_service.shutdown()
            print("✅ 调度器已关闭")
