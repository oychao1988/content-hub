"""
ContentHub 主入口文件
"""
import uvicorn
import argparse
from app.factory import create_app
from app.utils.custom_logger import logger

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContentHub 后端服务")
    parser.add_argument("--port", type=int, default=8010, help="服务端口（默认：8010）")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址（默认：0.0.0.0）")
    parser.add_argument("--reload", action="store_true", help="启用热重载（开发模式）")
    args = parser.parse_args()

    logger.info(f"🚀 启动 ContentHub 服务在端口 {args.port}...")
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
