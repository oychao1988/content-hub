from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.scheduler import endpoints
from app.utils.custom_logger import log

router = APIRouter()
router.include_router(endpoints.router, tags=["scheduler"])

# 模块启动钩子
def startup(app):
    """定时任务模块启动时执行的代码"""
    from app.services.scheduler_service import scheduler_service
    from app.services.executors import (
        ContentGenerationExecutor,
        PublishingExecutor,
        WorkflowExecutor,
        AddToPoolExecutor,
        ApproveExecutor,
        AsyncContentGenerationExecutor
    )
    from app.db.database import SessionLocal

    # 注册任务执行器
    content_gen_executor = ContentGenerationExecutor()
    publishing_executor = PublishingExecutor()
    workflow_executor = WorkflowExecutor()
    add_to_pool_executor = AddToPoolExecutor()
    approve_executor = ApproveExecutor()
    async_content_gen_executor = AsyncContentGenerationExecutor()

    scheduler_service.register_executor(content_gen_executor)
    scheduler_service.register_executor(publishing_executor)
    scheduler_service.register_executor(workflow_executor)
    scheduler_service.register_executor(add_to_pool_executor)
    scheduler_service.register_executor(approve_executor)
    scheduler_service.register_executor(async_content_gen_executor)

    log.info(f"已注册执行器: {list(scheduler_service.get_registered_executors().keys())}")

    # 启动调度器
    scheduler_service.start()
    log.info("调度器已启动")

    # 从数据库加载定时任务
    try:
        db = SessionLocal()
        try:
            loaded_count = scheduler_service.load_tasks_from_db(db)
            log.info(f"成功加载 {loaded_count} 个定时任务")

            # 显示已加载的任务详情
            if loaded_count > 0:
                jobs = scheduler_service.get_scheduled_jobs()
                log.info(f"当前调度器中的任务: {len(jobs)} 个")
                for job in jobs:
                    log.info(f"  - {job['name']} (下次运行: {job['next_run_time']})")
        finally:
            db.close()
    except Exception as e:
        log.error(f"加载定时任务时发生错误: {str(e)}")
        log.exception("Task loading failed")

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