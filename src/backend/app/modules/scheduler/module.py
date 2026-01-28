from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.scheduler import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/scheduler", tags=["scheduler"])

# 模块启动钩子
def startup(app):
    """定时任务模块启动时执行的代码"""
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()

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