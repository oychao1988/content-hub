from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.config import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/config", tags=["config"])

# 模块启动钩子
def startup(app):
    """配置管理模块启动时执行的代码"""
    # 初始化默认写作风格和内容主题（可选）
    pass

# 模块关闭钩子
def shutdown(app):
    """配置管理模块关闭时执行的代码"""
    pass

# 模块导出
MODULE = Module(
    name="config",
    router=router,
    startup=startup,
    shutdown=shutdown
)
