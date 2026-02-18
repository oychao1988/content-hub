from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.scheduler import endpoints
from app.utils.custom_logger import log

router = APIRouter()
router.include_router(endpoints.router, tags=["scheduler"])

# 模块启动钩子
def startup(app):
    """定时任务模块启动时执行的代码"""
    try:
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

        log.info("=== 开始初始化调度器模块 ===")

        # 注册任务执行器
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

        log.info(f"已注册执行器总数: {registered_count}/{len(executors)}")

        # 启动调度器
        if not scheduler_service.is_running:
            scheduler_service.start()
            log.info("✓ 调度器已启动")
        else:
            log.info("调度器已在运行")

        # 从数据库加载定时任务
        db = SessionLocal()
        try:
            loaded_count = scheduler_service.load_tasks_from_db(db)
            log.info(f"✓ 成功加载 {loaded_count} 个定时任务")

            # 显示已加载的任务详情
            if loaded_count > 0:
                jobs = scheduler_service.get_scheduled_jobs()
                log.info(f"当前调度器中的任务: {len(jobs)} 个")
                for job in jobs:
                    log.info(f"  - {job['name']} (下次运行: {job['next_run_time']})")
        except Exception as e:
            log.error(f"✗ 加载定时任务时发生错误: {str(e)}")
            log.exception("Task loading failed")
        finally:
            db.close()

        log.info("=== 调度器模块初始化完成 ===")

    except Exception as e:
        log.error(f"✗ 调度器模块启动失败: {str(e)}")
        log.exception("Scheduler startup failed")
        raise

# 模块关闭钩子
def shutdown(app):
    """定时任务模块关闭时执行的代码"""
    from app.services.scheduler_service import scheduler_service
    scheduler_service.shutdown()

# 模块导出
MODULE = Module(
    name="scheduler",
    router=router,
    startup=startup,
    shutdown=shutdown
)