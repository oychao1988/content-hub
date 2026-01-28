from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.content import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/content", tags=["content"])

# 模块启动钩子
def startup(app):
    """内容管理模块启动时执行的代码"""
    from app.services.content_review_service import content_review_service
    content_review_service.init()

# 模块关闭钩子
def shutdown(app):
    """内容管理模块关闭时执行的代码"""
    pass

# 模块导出
MODULE = Module(
    name="content",
    router=router,
    startup=startup,
    shutdown=shutdown
)