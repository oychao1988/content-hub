from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.dashboard import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/dashboard", tags=["dashboard"])

# 模块启动钩子
def startup(app):
    """仪表盘模块启动时执行的代码"""
    pass

# 模块关闭钩子
def shutdown(app):
    """仪表盘模块关闭时执行的代码"""
    pass

# 模块导出
MODULE = Module(
    name="dashboard",
    router=router,
    startup=startup,
    shutdown=shutdown
)