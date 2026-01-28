"""
ContentHub 主入口文件
"""
import uvicorn
from app.factory import create_app
from app.utils.custom_logger import logger

app = create_app()

if __name__ == "__main__":
    logger.info("🚀 启动 ContentHub 服务...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
