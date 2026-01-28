from fastapi import APIRouter
from app.core.module_system.module import Module
from app.modules.accounts import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/accounts", tags=["accounts"])

# 模块启动钩子
def startup(app):
    """账号管理模块启动时执行的代码"""
    from app.services.account_config_service import account_config_service
    # 初始化默认配置
    pass

# 模块关闭钩子
def shutdown(app):
    """账号管理模块关闭时执行的代码"""
    pass

# 模块导出
MODULE = Module(
    name="accounts",
    router=router,
    startup=startup,
    shutdown=shutdown
)