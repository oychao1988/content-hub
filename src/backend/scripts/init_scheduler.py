#!/usr/bin/env python3
"""
ContentHub 调度器初始化脚本

在容器启动时自动注册执行器并启动调度器
"""
import sys
from app.services.scheduler_service import scheduler_service
from app.services.executors import (
    ContentGenerationExecutor,
    PublishingExecutor,
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor,
    AsyncContentGenerationExecutor,
    PublishPoolScannerExecutor
)
from app.db.database import SessionLocal
from app.utils.custom_logger import log


def init_scheduler():
    """初始化调度器"""

    log.info("=== 开始初始化调度器 ===")

    # 注册所有执行器
    executors = [
        ("content_generation", ContentGenerationExecutor()),
        ("publishing", PublishingExecutor()),
        ("workflow", WorkflowExecutor()),
        ("add_to_pool", AddToPoolExecutor()),
        ("approve", ApproveExecutor()),
        ("async_content_generation", AsyncContentGenerationExecutor()),
        ("publish_pool_scanner", PublishPoolScannerExecutor())
    ]

    registered_count = 0
    for name, executor in executors:
        try:
            scheduler_service.register_executor(executor)
            registered_count += 1
            log.info(f"✓ 已注册执行器: {name}")
        except Exception as e:
            log.error(f"✗ 注册执行器失败: {name}, 错误: {str(e)}")

    log.info(f"已注册的执行器总数: {registered_count}/{len(executors)}")

    # 启动调度器
    if not scheduler_service.is_running:
        try:
            scheduler_service.start()
            log.info("✓ 调度器已启动")
        except Exception as e:
            log.error(f"✗ 调度器启动失败: {str(e)}")
            return False
    else:
        log.info("调度器已在运行")

    # 从数据库加载定时任务
    try:
        db = SessionLocal()
        try:
            loaded_count = scheduler_service.load_tasks_from_db(db)
            log.info(f"✓ 成功加载 {loaded_count} 个定时任务")

            # 显示已加载的任务
            jobs = scheduler_service.get_scheduled_jobs()
            log.info(f"当前调度器中的任务: {len(jobs)} 个")
            for job in jobs:
                log.info(f"  - {job['name']} (下次运行: {job['next_run_time']})")
        finally:
            db.close()
    except Exception as e:
        log.error(f"✗ 加载定时任务失败: {str(e)}")
        return False

    log.info("=== 调度器初始化完成 ===")
    return True


if __name__ == "__main__":
    success = init_scheduler()
    sys.exit(0 if success else 1)
