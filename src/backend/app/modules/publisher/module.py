from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.publisher import endpoints

router = APIRouter()
router.include_router(endpoints.router, tags=["publisher"])

# 模块启动钩子
def startup(app):
    """发布管理模块启动时执行的代码"""
    from app.services.publish_pool_service import publish_pool_service
    publish_pool_service.init()

# 模块关闭钩子
def shutdown(app):
    """发布管理模块关闭时执行的代码"""
    pass

# 模块导出
MODULE = Module(
    name="publisher",
    router=router,
    startup=startup,
    shutdown=shutdown
)