import logging
import os
import sys
from datetime import datetime

from loguru import logger

from app.core.config import settings

# 移除默认处理器
logger.remove()

# 日志格式
SIMPLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>"
)

DETAILED_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<magenta>{process}</magenta>:<magenta>{thread}</magenta> | "
    "<level>{message}</level>"
)

# 选择日志格式
LOG_FORMAT = DETAILED_FORMAT if settings.LOG_FORMAT == "detailed" else SIMPLE_FORMAT


# 日志过滤器
def log_filter(record):
    """
    过滤掉不需要的日志
    1. 过滤掉SQL查询日志（除非启用）
    2. 过滤掉第三方库的DEBUG日志（除非启用）
    3. 过滤掉HTTP请求日志（除非启用）
    """
    # 过滤SQL查询日志
    if not settings.LOG_SQL_QUERIES and "sqlalchemy" in record["name"].lower():
        return False

    # 过滤HTTP请求日志
    if not settings.LOG_HTTP_REQUESTS and any(
        x in record["message"] for x in ["HTTP Request", "HTTP Response"]
    ):
        return False

    # 过滤第三方库日志
    if not settings.LOG_THIRD_PARTY and record["level"].name == "DEBUG":
        skip_paths = [
            "urllib3",
            "asyncio",
            "aiomysql",
            "aiohttp",
            "sqlalchemy",
            "celery",
            "kombu",
            "amqp",
        ]
        for path in skip_paths:
            if path in record["name"]:
                return False

    return True


# 配置日志文件
if settings.LOG_FILE:
    log_file = settings.LOG_FILE
else:
    # 在项目根目录的logs文件夹中创建日志文件
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 按日期分割日志文件
    log_file = os.path.join(log_dir, "{time:YYYY-MM-DD}.log")

# 添加控制台输出处理器
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level=settings.LOG_LEVEL,
    filter=log_filter,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# 添加文件输出处理器
logger.add(
    log_file,
    format=LOG_FORMAT,
    level=settings.LOG_LEVEL,
    filter=log_filter,
    rotation=settings.LOG_ROTATION_SIZE,  # 根据配置的大小轮转
    retention=f"{settings.LOG_RETENTION_DAYS} days",  # 根据配置保留天数
    compression="zip" if settings.LOG_COMPRESSION else None,  # 根据配置决定是否压缩
    encoding="utf-8",
    enqueue=settings.LOG_ASYNC,  # 根据配置决定是否异步写入
    backtrace=True,
    diagnose=True,
)

# 添加错误日志处理器
error_log_file = os.path.join("logs", "error_{time:YYYY-MM-DD}.log")
logger.add(
    error_log_file,
    format=LOG_FORMAT,
    level="ERROR",
    filter=log_filter,
    rotation="00:00",  # 每天午夜轮转
    retention=f"{settings.LOG_ERROR_RETENTION_DAYS} days",  # 根据配置保留天数
    compression="zip" if settings.LOG_COMPRESSION else None,
    encoding="utf-8",
    enqueue=settings.LOG_ASYNC,
    backtrace=True,
    diagnose=True,
)

# 性能日志处理器
if settings.LOG_PERFORMANCE:
    perf_log_file = os.path.join("logs", "performance_{time:YYYY-MM-DD}.log")
    logger.add(
        perf_log_file,
        format=LOG_FORMAT,
        filter=lambda record: "performance" in record["extra"],
        level="INFO",
        rotation="00:00",  # 每天午夜轮转
        retention="7 days",  # 保留7天的性能日志
        compression="zip" if settings.LOG_COMPRESSION else None,
        encoding="utf-8",
        enqueue=settings.LOG_ASYNC,
    )


# 创建一个处理器来拦截标准库的日志
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 Loguru 级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者的文件名和行号
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# 配置标准库日志处理
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# 配置第三方库的日志
# 在测试环境中，将数据库日志设置为WARNING级别以减少输出
import os

test_mode = os.getenv("PYTEST_CURRENT_TEST") is not None or "pytest" in os.getenv(
    "_", ""
)

if test_mode:
    # 测试环境下关闭详细的数据库日志
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
else:
    # 正常环境下使用配置的日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(settings.LOG_LEVEL)
    logging.getLogger("sqlalchemy.pool").setLevel(settings.LOG_LEVEL)
    logging.getLogger("sqlalchemy.dialects").setLevel(settings.LOG_LEVEL)
    logging.getLogger("sqlalchemy.orm").setLevel(settings.LOG_LEVEL)

logging.getLogger("aiohttp").setLevel(settings.LOG_LEVEL)
logging.getLogger("asyncio").setLevel(settings.LOG_LEVEL)
logging.getLogger("uvicorn").setLevel(settings.LOG_LEVEL)
logging.getLogger("fastapi").setLevel(settings.LOG_LEVEL)

# 在程序启动时记录基本信息
logger.info(f"应用启动 - {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"日志级别: {settings.LOG_LEVEL}")
logger.info(f"日志格式: {settings.LOG_FORMAT}")
logger.info(f"日志文件: {log_file}")
logger.info(f"错误日志: {error_log_file}")
logger.info(f"性能日志: {'启用' if settings.LOG_PERFORMANCE else '禁用'}")
logger.info(f"SQL查询日志: {'启用' if settings.LOG_SQL_QUERIES else '禁用'}")
logger.info(f"HTTP请求日志: {'启用' if settings.LOG_HTTP_REQUESTS else '禁用'}")
logger.info(f"第三方库日志: {'启用' if settings.LOG_THIRD_PARTY else '禁用'}")
logger.info(f"异步日志: {'启用' if settings.LOG_ASYNC else '禁用'}")
logger.info(f"调试模式: {'启用' if settings.DEBUG else '禁用'}")

# 导出处理过的logger实例，以便在其他模块中使用
log = logger
