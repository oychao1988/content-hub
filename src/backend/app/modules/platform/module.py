"""
平台管理模块
提供平台的增删改查功能
"""
from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.platform import endpoints

router = APIRouter()
router.include_router(endpoints.router, tags=["platforms"])


# 模块启动钩子
def startup(app):
    """平台管理模块启动时执行的代码"""
    pass


# 模块关闭钩子
def shutdown(app):
    """平台管理模块关闭时执行的代码"""
    pass


# 模块导出
MODULE = Module(
    name="platform",
    router=router,
    startup=startup,
    shutdown=shutdown
)
